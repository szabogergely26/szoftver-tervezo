from __future__ import annotations

import json
import re
import shutil
from datetime import date
from pathlib import Path

from .models import Project, ProjectStatus, TaskItem

PROJECT_FILE = "project.json"
TASKS_FILE = "feladatok.json"
JOURNAL_FILE = "naplo.html"
ASSETS_DIR = "assets"


class Storage:
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
            TaskItem(id=i, html=text, done=False)
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

    # ---------- feladatok.json ----------
    def read_tasks(self, project_dir: Path) -> list[TaskItem]:
        f = project_dir / TASKS_FILE
        if not f.exists():
            return []
        data = json.loads(f.read_text(encoding="utf-8"))
        return [TaskItem.from_dict(d) for d in data]

    def write_tasks(self, project_dir: Path, tasks: list[TaskItem]) -> None:
        f = project_dir / TASKS_FILE
        f.write_text(
            json.dumps([t.to_dict() for t in tasks], ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def next_task_id(self, tasks: list[TaskItem]) -> int:
        return max((t.id for t in tasks), default=0) + 1

    def parse_task_list(self, raw: str) -> list[str]:
        """A Varázsló vesszővel elválasztott feladatlista-mezőjének szétbontása."""
        return [part.strip() for part in raw.split(",") if part.strip()]

    def set_task_done(self, project_dir: Path, task_id: int, done: bool) -> None:
        tasks = self.read_tasks(project_dir)
        for t in tasks:
            if t.id == task_id:
                t.done = done
                break
        self.write_tasks(project_dir, tasks)

    # ---------- naplo.html ----------
    def read_journal(self, project_dir: Path) -> str:
        f = project_dir / JOURNAL_FILE
        if not f.exists():
            return "<p><br></p>"
        return f.read_text(encoding="utf-8")

    def write_journal(self, project_dir: Path, html: str) -> None:
        f = project_dir / JOURNAL_FILE
        f.write_text(html, encoding="utf-8")

    def today_header_marker(self) -> str:
        """A mai dátum-fejléc szövege, ÉÉÉÉ.HH.NN formátumban (idő nélkül)."""
        return date.today().strftime("%Y.%m.%d")

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
