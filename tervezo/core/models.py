from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from settings.translations import tr


class ProjectStatus(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    DONE = "done"

    @property
    def icon(self) -> str:
        """Kártyán megjelenő státusz-jelzés."""
        return {
            ProjectStatus.NOT_STARTED: "🔴",
            ProjectStatus.IN_PROGRESS: "🟡",
            ProjectStatus.DONE: "🟢",
        }[self]

    @property
    def color(self) -> str:
        return {
            ProjectStatus.NOT_STARTED: "#e74c3c",
            ProjectStatus.IN_PROGRESS: "#f1c40f",
            ProjectStatus.DONE: "#2ecc71",
        }[self]

    @property
    def label(self) -> str:
        """A jelenlegi nyelven megjelenítendő státusz-felirat."""
        return {
            ProjectStatus.NOT_STARTED: tr("status.not_started"),
            ProjectStatus.IN_PROGRESS: tr("status.in_progress"),
            ProjectStatus.DONE: tr("status.done"),
        }[self]

    # Visszafelé kompatibilitás – régi hívások, amik még label_hu-t várnak.
    @property
    def label_hu(self) -> str:
        return self.label


@dataclass
class Milestone:
    """Nagyobb projekt-szintű megálló (pl. 'Alap CRUD működik')."""

    date: str  # ÉÉÉÉ.HH.NN
    title: str
    description: str = ""

    def to_dict(self) -> dict:
        return {"date": self.date, "title": self.title, "description": self.description}

    @staticmethod
    def from_dict(data: dict) -> Milestone:
        return Milestone(
            date=data.get("date", ""),
            title=data.get("title", ""),
            description=data.get("description", ""),
        )





class TaskStatus(Enum):
    PENDING = "pending"          # Következő feladatok
    IN_PROGRESS = "in_progress"  # Folyamatban lévő feladatok
    DONE = "done"                # Elkészült feladatok


@dataclass
class TaskItem:
    """Egy feladat-sor a 'Következő' / 'Folyamatban' / 'Elkészült' listákban.

    A `title` a listákban megjelenő rövid cím (sima szöveg).
    A `html` mező a részletes, gazdag-szöveges (rich-text) leírás,
    amit a "Részletek" dialógus mutat/szerkeszt.

    """

    id: int
    title: str
    html: str
    status: TaskStatus = TaskStatus.PENDING
    completed_at:  str | None = None

    def to_dict(self) -> dict:
        return {
            "id": self.id, 
            "title": self.title,
            "html": self.html, 
            "status": self.status.value,
            "completed_at": self.completed_at,
        }

    @staticmethod
    def from_dict(data: dict) -> TaskItem:
        # Visszafelé kompatibilitás: a régi mentések 'done': bool mezőt
        # tartalmaznak, státusz mező helyett.
        if "status" in data:
            status = TaskStatus(data["status"])
        else:
            status = TaskStatus.DONE if data.get("done") else TaskStatus.PENDING

        # Visszafelé kompatibilitás: a régi mentésekben nincs 'title', csak
        # 'html' — ilyenkor a html-ből nyerjük ki az egyszerű szöveget,
        # hogy a listákban legyen mit mutatni migráció után is.
        html = data.get("html", "")
        if "title" in data:
            title = data["title"]
        else:
            from PySide6.QtGui import QTextDocumentFragment
            title = QTextDocumentFragment.fromHtml(html).toPlainText().strip() or "…"

        return TaskItem(
            id=data["id"],
            title=title,
            html=html,
            status=status,
            completed_at=data.get("completed_at"),
        )

    @property
    def done(self) -> bool:
        """Visszafelé kompatibilitás régi hívásoknak, amik 'done'-t várnak."""
        return self.status == TaskStatus.DONE



@dataclass
class Project:
    """Egy projekt teljes metaadata (a project.json tartalma + a mappa útvonala)."""

    path: Path
    name: str
    description: str = ""  # rövid, kártyán is megjelenő leírás
    purpose: str = ""  # "Mire jó a program" -> Áttekintés tab tartalma
    photo: str | None = None  # relatív útvonal, pl. "assets/cover.png"
    status: ProjectStatus = ProjectStatus.NOT_STARTED
    start_date: str | None = None
    end_date: str | None = None
    milestones: list[Milestone] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "purpose": self.purpose,
            "photo": self.photo,
            "status": self.status.value,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "milestones": [m.to_dict() for m in self.milestones],
        }

    @staticmethod
    def from_dict(path: Path, data: dict) -> Project:
        return Project(
            path=path,
            name=data.get("name", path.name),
            description=data.get("description", ""),
            purpose=data.get("purpose", ""),
            photo=data.get("photo"),
            status=ProjectStatus(data.get("status", "not_started")),
            start_date=data.get("start_date"),
            end_date=data.get("end_date"),
            milestones=[Milestone.from_dict(m) for m in data.get("milestones", [])],
        )

    @property
    def photo_path(self) -> Path | None:
        """A fotó abszolút útvonala, ha van beállítva."""
        if not self.photo:
            return None
        return self.path / self.photo