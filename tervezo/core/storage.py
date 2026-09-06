from __future__ import annotations

import json
import re
import shutil
from datetime import date, datetime, timedelta
from pathlib import Path

from .models import (
    ProfileData,
    ProfileMeta,
    Project,
    ProjectStatus,
    TaskItem,
    TaskStatus,
)

PROJECT_FILE = "project.json"
TASKS_FILE = "feladatok.json"
JOURNAL_FILE = "naplo.html"
ASSETS_DIR = "assets"
DOCS_DIR = "docs"

PROFILES_DIR = "profiles"
INACTIVE_DIR = ".inactive"
TRASH_DIR = ".trash"
INACTIVE_META_FILE = ".inactive_meta.json"
TRASH_META_FILE = ".trash_meta.json"
TRASH_MAX_AGE_DAYS = 30

PROFILE_DATA_FILE = "profile_meta.json"

# A "Sablon feladatok" dialógus tételeit tartalmazó, kódtól független config.
# Új tétel felvételéhez elég ezt a JSON fájlt bővíteni, kódmódosítás nem kell.
TEMPLATE_TASKS_FILE = Path(__file__).parent / "sablon_feladatok.json"


class Storage:
    """
    A projektek és a hozzájuk tartozó fájlok (feladatok, napló, dokumentumok)
    olvasásáért/írásáért felelős osztály.
    A projektek a felhasználói adatok gyökérkönyvtárában
    (config.py: USER_DATA_DIR) találhatók, a projekt mappájában pedig
    a projekt.json, feladatok.json, naplo.html és a docs/ mappa
    található.
    """

    # ---------- Projektek listázása ----------
    def list_projects(self, projects_dir: Path) -> list[Path]:
        return sorted(p for p in projects_dir.iterdir() if p.is_dir())

    # ---------- project.json ----------
    def read_project(self, project_dir: Path) -> Project:
        f = project_dir / PROJECT_FILE
        if not f.exists():
            project = Project(path=project_dir, name=project_dir.name)
        else:
            data = json.loads(f.read_text(encoding="utf-8"))
            project = Project.from_dict(project_dir, data)

        if not project.photo:
            project.photo = self._detect_existing_cover(project_dir)

        return project

    def _detect_existing_cover(self, project_dir: Path) -> str | None:
        """Ha nincs project.photo beállítva, de van cover.* fájl az assets
        mappában (pl. kézzel odamásolt kép), azt automatikusan felismeri.
        """
        assets_dir = project_dir / ASSETS_DIR
        if not assets_dir.exists():
            return None
        matches = sorted(assets_dir.glob("cover.*"))
        if matches:
            return f"{ASSETS_DIR}/{matches[0].name}"
        return None

    def write_project(self, project: Project) -> None:
        f = project.path / PROJECT_FILE
        f.write_text(
            json.dumps(project.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def create_project(
        self,
        projects_dir: Path,
        name: str,
        *,
        description: str = "",
        purpose: str = "",
        photo_source: Path | None = None,
        initial_tasks_raw: str = "",
    ) -> Project:
        """Új projekt létrehozása a Varázsló adataiból.

        `initial_tasks_raw`: a Varázsló vesszővel elválasztott feladatlista mezőjének
        nyers szövege — ebből lesznek a kezdeti 'Következő feladatok' tételek.
        """
        project_dir = projects_dir / name
        project_dir.mkdir(parents=True, exist_ok=False)
        (project_dir / ASSETS_DIR).mkdir(exist_ok=True)

        photo_rel: str | None = None
        if photo_source is not None:
            photo_rel = self._copy_photo(project_dir, photo_source)

        project = Project(
            path=project_dir,
            name=name,
            description=description,
            purpose=purpose,
            photo=photo_rel,
            status=ProjectStatus.NOT_STARTED,
        )
        self.write_project(project)

        # naplo.html üres, de szerkeszthető váz (QTextEdit-nek)
        (project_dir / JOURNAL_FILE).write_text("<p><br></p>", encoding="utf-8")

        # feladatok.json a varázsló vesszővel elválasztott listájából
        tasks = [
            TaskItem(id=i, title=text, html=text)
            for i, text in enumerate(self.parse_task_list(initial_tasks_raw), start=1)
        ]
        self.write_tasks(project_dir, tasks)

        return project

    def _copy_photo(self, project_dir: Path, photo_source: Path) -> str:
        assets_dir = project_dir / ASSETS_DIR
        assets_dir.mkdir(exist_ok=True)
        target = assets_dir / f"cover{photo_source.suffix.lower()}"
        shutil.copy2(photo_source, target)
        return f"{ASSETS_DIR}/{target.name}"

    def set_project_cover(self, project_dir: Path, photo_source: Path) -> str:
        """Külső képfájl bemásolása a projekt assets mappájába (borítókép).

        Ha már létezik korábbi cover.* fájl, azt előtte eltávolítja.
        """
        assets_dir = project_dir / ASSETS_DIR
        assets_dir.mkdir(exist_ok=True)
        for old in assets_dir.glob("cover.*"):
            old.unlink()
        return self._copy_photo(project_dir, photo_source)

    def remove_project_cover(self, project_dir: Path) -> None:
        """Meglévő cover.* fájl törlése az assets mappából."""
        assets_dir = project_dir / ASSETS_DIR
        if assets_dir.exists():
            for old in assets_dir.glob("cover.*"):
                old.unlink()

    # ---------- Dokumentumok (docs/) ----------
    def add_document(
        self,
        project_dir: Path,
        source_file: Path,
        *,
        overwrite: bool = False,
        target_name: str | None = None,
    ) -> str:
        """Külső fájl bemásolása a projekt docs/ mappájába.

        A cél fájlnév alapesetben a forrás fájl neve, de target_name-mel
        felülírható (pl. névütközés esetén a felhasználó más nevet adott
        meg). Ha már létezik ilyen nevű dokumentum és overwrite=False,
        FileExistsError-t dob — a UI-nak ilyenkor meg kell kérdeznie a
        felhasználót (felülírás / új név).
        """
        docs_dir = project_dir / DOCS_DIR
        docs_dir.mkdir(exist_ok=True)
        target = docs_dir / (target_name or source_file.name)
        if target.exists() and not overwrite:
            raise FileExistsError(target)
        shutil.copy2(source_file, target)
        return target.name

    def remove_document(self, project_dir: Path, filename: str) -> None:
        """Egy dokumentum fájl törlése a docs/ mappából.

        Ha a fájl már nincs a lemezen (pl. kézzel törölték), nem hiba —
        a JSON-bejegyzés eltávolítását a hívónak (Project.documents
        frissítése + write_project) kell elvégeznie ezután.
        """
        target = project_dir / DOCS_DIR / filename
        if target.exists():
            target.unlink()

    def rename_document(
        self,
        project_dir: Path,
        old_filename: str,
        new_filename: str,
        *,
        overwrite: bool = False,
    ) -> str:
        """Dokumentum fájl átnevezése a docs/ mappán belül.

        Ha a cél név már foglalt (más dokumentum) és overwrite=False,
        FileExistsError-t dob. A JSON-bejegyzés frissítését a hívónak kell
        elvégeznie (Project.documents-ben a régi nevet a újra cserélve).
        """
        docs_dir = project_dir / DOCS_DIR
        old_path = docs_dir / old_filename
        new_path = docs_dir / new_filename
        if new_path.exists() and not overwrite:
            raise FileExistsError(new_path)
        old_path.rename(new_path)
        return new_filename

    def document_path(self, project_dir: Path, filename: str) -> Path:
        """Egy dokumentum abszolút útvonala (megnyitáshoz)."""
        return project_dir / DOCS_DIR / filename

    def delete_project(self, project_dir: Path) -> None:
        """Teljes projekt-mappa törlése. A megerősítést a UI-nak kell kérnie előtte."""
        shutil.rmtree(project_dir)

    def rename_project(self, project_dir: Path, new_name: str) -> Path:
        target = project_dir.with_name(new_name)
        if target.exists():
            raise FileExistsError(target)
        project_dir.rename(target)

        project = self.read_project(target)
        project = Project(
            path=target,
            name=new_name,
            description=project.description,
            purpose=project.purpose,
            photo=project.photo,
            status=project.status,
            start_date=project.start_date,
            end_date=project.end_date,
            milestones=project.milestones,
        )
        self.write_project(project)
        return target

    # ---------- Profilok: path-feloldás ----------

    def _tasks_path(self, project_dir: Path, profile: str | None) -> Path:
        if profile is None:
            return project_dir / TASKS_FILE
        return project_dir / PROFILES_DIR / profile / TASKS_FILE

    def _journal_path(self, project_dir: Path, profile: str | None) -> Path:
        if profile is None:
            return project_dir / JOURNAL_FILE
        return project_dir / PROFILES_DIR / profile / JOURNAL_FILE

    def _profile_data_path(self, project_dir: Path, profile: str) -> Path:
        return project_dir / PROFILES_DIR / profile / PROFILE_DATA_FILE

    def read_profile_data(self, project_dir: Path, profile: str) -> ProfileData:
        f = self._profile_data_path(project_dir, profile)
        if not f.exists():
            return ProfileData()
        data = json.loads(f.read_text(encoding="utf-8"))
        return ProfileData.from_dict(data)

    def write_profile_data(
        self, project_dir: Path, profile: str, profile_data: ProfileData
    ) -> None:
        f = self._profile_data_path(project_dir, profile)
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(
            json.dumps(profile_data.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    # ---------- feladatok.json ----------
    def read_tasks(
        self, project_dir: Path, profile: str | None = None
    ) -> list[TaskItem]:
        f = self._tasks_path(project_dir, profile)
        if not f.exists():
            return []
        data = json.loads(f.read_text(encoding="utf-8"))
        return [TaskItem.from_dict(d) for d in data]

    def write_tasks(
        self, project_dir: Path, tasks: list[TaskItem], profile: str | None = None
    ) -> None:
        f = self._tasks_path(project_dir, profile)
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(
            json.dumps([t.to_dict() for t in tasks], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def next_task_id(self, tasks: list[TaskItem]) -> int:
        return max((t.id for t in tasks), default=0) + 1

    def read_template_tasks(self) -> list[dict]:
        """A 'Sablon feladatok' dialógus tételei (sablon_feladatok.json-ból).

        Bővítés: a JSON fájlba felvett új {"id": ..., "title": ...} tétel
        automatikusan megjelenik a dialógusban, kódmódosítás nélkül.
        """
        if not TEMPLATE_TASKS_FILE.exists():
            return []
        return json.loads(TEMPLATE_TASKS_FILE.read_text(encoding="utf-8"))

    def write_template_tasks(self, items: list[dict]) -> None:
        """A sablon-tétel lista elmentése (Beállítások > Feladatok lapról)."""
        TEMPLATE_TASKS_FILE.write_text(
            json.dumps(items, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def parse_task_list(self, raw: str) -> list[str]:
        """A Varázsló vesszővel elválasztott feladatlista-mezőjének szétbontása."""
        return [part.strip() for part in raw.split(",") if part.strip()]

    def set_task_done(self, project_dir: Path, task_id: int, done: bool) -> None:
        tasks = self.read_tasks(project_dir)
        for t in tasks:
            if t.id == task_id:
                t.status = TaskStatus.DONE if done else TaskStatus.PENDING
                break
        self.write_tasks(project_dir, tasks)

    # ---------- naplo.html ----------
    def read_journal(self, project_dir: Path, profile: str | None = None) -> str:
        f = self._journal_path(project_dir, profile)
        if not f.exists():
            return "<p><br></p>"
        return f.read_text(encoding="utf-8")

    def write_journal(
        self, project_dir: Path, html: str, profile: str | None = None
    ) -> None:
        f = self._journal_path(project_dir, profile)
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(html, encoding="utf-8")

    def today_header_marker(self) -> str:
        """A mai dátum-fejléc szövege, ÉÉÉÉ.HH.NN formátumban (idő nélkül)."""
        return date.today().strftime("%Y.%m.%d")  # noqa: DTZ011 (helyi naptári dátum kell, nem UTC)

    def has_today_header(self, html: str) -> bool:
        """Van-e már mai dátumú fejléc a naplóban (duplikáció elkerülése)."""
        marker = re.escape(self.today_header_marker())
        return re.search(marker, html) is not None

    def build_today_header_html(self) -> str:
        """Új napi bejegyzés fejléce — félkövér dátum.

        A tényleges beszúrási pontot (kurzor-pozíció a meglévő HTML-ben)
        a UI réteg dönti el, mivel az a QTextEdit dokumentum-szerkezetétől függ.
        """
        return f"<p><b>{self.today_header_marker()}</b></p>"

    # ---------- Profilok engedélyezése / migráció ----------

    def enable_profiles(self, project_dir: Path, first_profile_name: str) -> None:
        """Profil-mód bekapcsolása egy eddig profil nélküli projekten.

        A jelenlegi gyökér-szintű feladatok.json/naplo.html átkerül a
        profiles/<first_profile_name>/ alá. Az assets/ (borítókép) marad
        projekt-szinten, nem duplázódik. Előtte biztonsági mentést készít
        a két fájlról (.bak kiterjesztéssel), hátha vissza kéne állítani.

        A projekt jelenlegi status/start_date/end_date/milestones értékei
        átmásolódnak az első profil profile_meta.json-jába (nem törlődnek
        a project.json-ból, de attól kezdve a UI a profilos mezőket
        használja, nem a project-szintűeket).

        """

        profiles_dir = project_dir / PROFILES_DIR
        target_dir = profiles_dir / first_profile_name
        target_dir.mkdir(parents=True, exist_ok=True)

        tasks_src = project_dir / TASKS_FILE
        journal_src = project_dir / JOURNAL_FILE

        if tasks_src.exists():
            shutil.copy2(tasks_src, tasks_src.with_suffix(tasks_src.suffix + ".bak"))
            shutil.move(str(tasks_src), str(target_dir / TASKS_FILE))
        if journal_src.exists():
            shutil.copy2(
                journal_src, journal_src.with_suffix(journal_src.suffix + ".bak")
            )
            shutil.move(str(journal_src), str(target_dir / JOURNAL_FILE))

        project = self.read_project(project_dir)

        profile_data = ProfileData(
            status=project.status,
            start_date=project.start_date,
            end_date=project.end_date,
            milestones=list(project.milestones),
        )
        self.write_profile_data(project_dir, first_profile_name, profile_data)

        project.profiles_enabled = True
        project.active_profile = first_profile_name
        self.write_project(project)

    def disable_profiles(self, project_dir: Path, keep_profile_name: str) -> None:
        """Profil-mód kikapcsolása.

        A megtartott profil (keep_profile_name) tartalma visszakerül a
        projekt gyökerébe (feladatok.json, naplo.html). A többi aktív
        profil a .inactive/ alá kerül (nem törlődik, később
        visszaállítható, ha újra bekapcsolod a profilokat).
        """
        profiles_dir = project_dir / PROFILES_DIR
        keep_dir = profiles_dir / keep_profile_name

        tasks_src = keep_dir / TASKS_FILE
        journal_src = keep_dir / JOURNAL_FILE
        if tasks_src.exists():
            shutil.move(str(tasks_src), str(project_dir / TASKS_FILE))
        if journal_src.exists():
            shutil.move(str(journal_src), str(project_dir / JOURNAL_FILE))
        if keep_dir.exists():
            shutil.rmtree(keep_dir)

        for other_dir in self._active_profile_dirs(project_dir):
            self._move_profile_to_inactive(project_dir, other_dir.name)

    def _active_profile_dirs(self, project_dir: Path) -> list[Path]:
        profiles_dir = project_dir / PROFILES_DIR
        if not profiles_dir.exists():
            return []
        return sorted(
            d
            for d in profiles_dir.iterdir()
            if d.is_dir() and not d.name.startswith(".")
        )

    def list_active_profile_names(self, project_dir: Path) -> list[str]:
        return [d.name for d in self._active_profile_dirs(project_dir)]

    # ---------- Inaktív profilok ----------

    def _move_profile_to_inactive(self, project_dir: Path, profile_name: str) -> None:
        src = project_dir / PROFILES_DIR / profile_name
        dst = project_dir / PROFILES_DIR / INACTIVE_DIR / profile_name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))

        meta = ProfileMeta(
            original_name=profile_name,
            timestamp=datetime.now().isoformat(timespec="seconds"),  # noqa: DTZ005 (helyi idő kell)
        )
        (dst / INACTIVE_META_FILE).write_text(
            json.dumps(meta.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def list_inactive_profiles(self, project_dir: Path) -> list[ProfileMeta]:
        """Lusta beolvasás — csak akkor hívjuk, amikor a felhasználó
        ténylegesen meg akarja nézni az inaktív profilokat (pl. a
        profil-bekapcsoló felületen)."""
        inactive_dir = project_dir / PROFILES_DIR / INACTIVE_DIR
        if not inactive_dir.exists():
            return []
        result = []
        for d in sorted(inactive_dir.iterdir()):
            if not d.is_dir():
                continue
            meta_file = d / INACTIVE_META_FILE
            if meta_file.exists():
                data = json.loads(meta_file.read_text(encoding="utf-8"))
                result.append(ProfileMeta.from_dict(data))
            else:
                # Nincs meta (pl. kézzel másolt mappa) — nevet a mappából vesszük.
                result.append(ProfileMeta(original_name=d.name, timestamp=""))
        return result

    def restore_from_inactive(self, project_dir: Path, profile_name: str) -> None:
        """Egy inaktív profil visszaállítása aktívvá (a meta fájl törlődik)."""
        src = project_dir / PROFILES_DIR / INACTIVE_DIR / profile_name
        dst = project_dir / PROFILES_DIR / profile_name
        meta_file = src / INACTIVE_META_FILE
        if meta_file.exists():
            meta_file.unlink()
        shutil.move(str(src), str(dst))

    # ---------- Kuka (trash) -------------

    def trash_profile(self, project_dir: Path, profile_name: str) -> None:
        """Egy aktív profil kukába dobása (nem törli azonnal, 30 napig
        visszaállítható). A célmappa nevéhez időbélyeget fűzünk, hogy
        névütközés ne legyen több egymást követő törlésnél."""
        src = project_dir / PROFILES_DIR / profile_name
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")  # noqa: DTZ005 (helyi idő kell)
        trash_folder_name = f"{profile_name}__{timestamp}"
        dst = project_dir / PROFILES_DIR / TRASH_DIR / trash_folder_name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))

        meta = ProfileMeta(
            original_name=profile_name,
            timestamp=datetime.now().isoformat(timespec="seconds"),  # noqa: DTZ005
        )
        (dst / TRASH_META_FILE).write_text(
            json.dumps(meta.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def list_trashed_profiles(self, project_dir: Path) -> list[tuple[str, ProfileMeta]]:
        """Lusta beolvasás — csak a Kuka nézet megnyitásakor hívjuk.

        Visszaadja a (trash_folder_name, meta) párok listáját —
        a mappanév kell a restore/purge műveletekhez.
        """
        trash_dir = project_dir / PROFILES_DIR / TRASH_DIR
        if not trash_dir.exists():
            return []
        result = []
        for d in sorted(trash_dir.iterdir()):
            if not d.is_dir():
                continue
            meta_file = d / TRASH_META_FILE
            if meta_file.exists():
                data = json.loads(meta_file.read_text(encoding="utf-8"))
                result.append((d.name, ProfileMeta.from_dict(data)))
            else:
                result.append((d.name, ProfileMeta(original_name=d.name, timestamp="")))
        return result

    def restore_from_trash(
        self, project_dir: Path, trash_folder_name: str, restore_as_name: str
    ) -> None:
        """Egy kukába dobott profil visszaállítása aktívvá.

        `restore_as_name`: a visszaállított profil neve — ha időközben
        létrejött egy aktív profil ugyanazzal a névvel, a hívónak (UI)
        előbb más nevet kell választania a felhasználóval, és azt kell
        ide átadnia.
        """
        src = project_dir / PROFILES_DIR / TRASH_DIR / trash_folder_name
        dst = project_dir / PROFILES_DIR / restore_as_name
        meta_file = src / TRASH_META_FILE
        if meta_file.exists():
            meta_file.unlink()
        shutil.move(str(src), str(dst))

    def purge_expired_trash(
        self, project_dir: Path, max_age_days: int = TRASH_MAX_AGE_DAYS
    ) -> list[str]:
        """A max_age_days-nél régebbi kukamappák végleges törlése.

        Visszaadja a törölt mappák neveit (logoláshoz/tájékoztatáshoz).
        A `deleted_at` a .trash_meta.json-ból számít, nem a fájlrendszer
        módosítási dátumából (export/import után is helyes marad).
        """
        trash_dir = project_dir / PROFILES_DIR / TRASH_DIR
        if not trash_dir.exists():
            return []

        cutoff = datetime.now() - timedelta(days=max_age_days)  # noqa: DTZ005
        purged: list[str] = []
        for d in sorted(trash_dir.iterdir()):
            if not d.is_dir():
                continue
            meta_file = d / TRASH_META_FILE
            if not meta_file.exists():
                continue
            data = json.loads(meta_file.read_text(encoding="utf-8"))
            meta = ProfileMeta.from_dict(data)
            if not meta.timestamp:
                continue
            deleted_at = datetime.fromisoformat(meta.timestamp)
            if deleted_at < cutoff:
                shutil.rmtree(d)
                purged.append(d.name)
        return purged
