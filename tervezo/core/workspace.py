from __future__ import annotations

from pathlib import Path


class Workspace:
    def __init__(self):
        # Program gyökérkönyvtára
        self.root = Path(__file__).resolve().parents[2] / "Projektek"

        self.projects_dir = self.root / "projects"
        self.inbox_dir = self.root / "inbox"

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
