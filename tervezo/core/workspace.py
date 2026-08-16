from __future__ import annotations

import logging
import shutil
import zipfile
from pathlib import Path

from config import USER_DATA_DIR

logger = logging.getLogger(__name__)

class Workspace:
    def __init__(self):
        # Program gyökérkönyvtára
        self.root = USER_DATA_DIR / "Projektek"

        self.projects_dir = self.root / "projects"
        self.inbox_dir = self.root / "inbox"

        logger.info("Projektek innen töltődnek: %s", self.projects_dir.resolve())

    def ensure(self) -> None:
        self.root.mkdir(exist_ok=True)
        self.projects_dir.mkdir(exist_ok=True)
        self.inbox_dir.mkdir(exist_ok=True)

    def ensure_default_project(self) -> None:
        # Ha nincs még projekt, hozzunk létre egyet
        if not any(self.projects_dir.iterdir()):
            default = self.projects_dir / "Alap_projekt"
            default.mkdir(exist_ok=True)

            note = default / "Jegyzet.html"
            if not note.exists():
                note.write_text(
                    "<h1>Alap jegyzet</h1><p>Kezdheted a tervezést.</p>",
                    encoding="utf-8",
                )



    # ---------- Export ----------
    def export_to_zip(self, zip_path: Path) -> None:
        """A teljes 'Projektek' munkaterület egyetlen zip fájlba csomagolása."""
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for file_path in self.root.rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(self.root.parent)
                    zf.write(file_path, arcname)

    # ---------- Import ----------
    def preview_conflicts(self, zip_path: Path, extract_dir: Path) -> list[str]:
        """Kicsomagol egy ideiglenes mappába, és visszaadja, mely projekt-mappák
        ütköznek a jelenleg meglévő tartalommal (ezek íródnának felül)."""
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(extract_dir)

        extracted_projects = extract_dir / self.root.name / "projects"
        conflicts: list[str] = []
        if extracted_projects.exists():
            for d in extracted_projects.iterdir():
                if d.is_dir() and (self.projects_dir / d.name).exists():
                    conflicts.append(d.name)
        return conflicts



    def import_from_extracted(self, extract_dir: Path) -> None:
        """A preview_conflicts által kicsomagolt tartalom tényleges bemásolása.
        Az ütköző projekt-mappák felülíródnak, a nem ütközők (meglévők és
        újak egyaránt) megmaradnak/bekerülnek."""
        self.ensure()

        extracted_root = extract_dir / self.root.name
        extracted_projects = extracted_root / "projects"
        extracted_inbox = extracted_root / "inbox"

        if extracted_projects.exists():
            for d in extracted_projects.iterdir():
                if not d.is_dir():
                    continue
                target = self.projects_dir / d.name
                if target.exists():
                    shutil.rmtree(target)
                shutil.copytree(d, target)

        if extracted_inbox.exists():
            for item in extracted_inbox.iterdir():
                target = self.inbox_dir / item.name
                if target.exists():
                    if target.is_dir():
                        shutil.rmtree(target)
                    else:
                        target.unlink()
                if item.is_dir():
                    shutil.copytree(item, target)
                else:
                    shutil.copy2(item, target)



    def preview_extra_local(self, extract_dir: Path) -> list[str]:
        """Azok a helyi projekt-mappák, amik megvannak nálad, de a
        zip-ben NEM szerepelnek - ezek importáláskor simán megmaradnának,
        hacsak a felhasználó nem kéri a törlésüket."""
        extracted_projects = extract_dir / self.root.name / "projects"
        extracted_names: set[str] = set()
        if extracted_projects.exists():
            extracted_names = {d.name for d in extracted_projects.iterdir() if d.is_dir()}

        extra: list[str] = []
        if self.projects_dir.exists():
            for d in self.projects_dir.iterdir():
                if d.is_dir() and d.name not in extracted_names:
                    extra.append(d.name)
        return extra

    def remove_projects(self, names: list[str]) -> None:
        """A megadott nevű projekt-mappák törlése (pl. felhasználói döntés
        alapján, ha nem akarja megtartani az importba nem tartozó projekteket)."""
        for name in names:
            target = self.projects_dir / name
            if target.exists():
                shutil.rmtree(target)