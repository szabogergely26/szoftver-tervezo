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

    A `html` mező rich-text tartalmat hordoz (félkövér, szín, stb.),
    ezért nem sima `text: str`.
    """

    id: int
    html: str
    status: TaskStatus = TaskStatus.PENDING
    completed_at:  str | None = None

    def to_dict(self) -> dict:
        return {"id": self.id, "html": self.html, "status": self.status.value}

    @staticmethod
    def from_dict(data: dict) -> TaskItem:
        # Visszafelé kompatibilitás: a régi mentések 'done': bool mezőt
        # tartalmaznak, státusz mező helyett.
        if "status" in data:
            status = TaskStatus(data["status"])
        else:
            status = TaskStatus.DONE if data.get("done") else TaskStatus.PENDING

        return TaskItem(id=data["id"], html=data.get("html", ""), status=status)

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