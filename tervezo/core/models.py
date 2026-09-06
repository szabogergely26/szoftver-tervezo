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
    PENDING = "pending"  # Következő feladatok
    IN_PROGRESS = "in_progress"  # Folyamatban lévő feladatok
    DONE = "done"  # Elkészült feladatok


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
    completed_at: str | None = None
    # Ha a feladat egy "Sablon feladatok" tételből lett felvéve, itt az adott
    # sablon-tétel stabil azonosítója (l. sablon_feladatok.json). Kézzel felvett
    # feladatoknál és régi mentéseknél None.
    template_id: str | None = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "html": self.html,
            "status": self.status.value,
            "completed_at": self.completed_at,
            "template_id": self.template_id,
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
            template_id=data.get("template_id"),
        )

    @property
    def done(self) -> bool:
        """Visszafelé kompatibilitás régi hívásoknak, amik 'done'-t várnak."""
        return self.status == TaskStatus.DONE


# --- Project dataclass bővítése ---


@dataclass
class Project:
    """Egy projekt teljes metaadata (a project.json tartalma + a mappa útvonala)."""

    path: Path
    name: str
    description: str = ""
    purpose: str = ""
    photo: str | None = None
    status: ProjectStatus = ProjectStatus.NOT_STARTED
    start_date: str | None = None
    end_date: str | None = None
    milestones: list[Milestone] = field(default_factory=list)
    documents: list[str] = field(default_factory=list)
    # Projekt-profilok (pl. LOQ / ThinkPad) — külön feladatok.json/naplo.html
    # profilonként. Ha profiles_enabled=False, a régi gyökér-szintű fájlok
    # (feladatok.json, naplo.html) számítanak, ahogy eddig is.
    profiles_enabled: bool = False
    active_profile: str | None = None

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
            "documents": self.documents,
            "profiles_enabled": self.profiles_enabled,
            "active_profile": self.active_profile,
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
            documents=data.get("documents", []),
            profiles_enabled=data.get("profiles_enabled", False),
            active_profile=data.get("active_profile"),
        )

    @property
    def photo_path(self) -> Path | None:
        """A fotó abszolút útvonala, ha van beállítva."""
        if not self.photo:
            return None
        return self.path / self.photo


# --- Új dataclass: ProfileMeta ---


@dataclass
class ProfileMeta:
    """Egy inaktivált vagy kukába dobott profil kísérő meta-adata.

    `.inactive_meta.json`-ban csak `timestamp` (disabled_at) számít;
    `.trash_meta.json`-ban ugyanez a mező deleted_at szerepként szolgál.
    A mezőnév egységesen `timestamp`, hogy ugyanaz az osztály mindkét
    esetben újrahasználható legyen.
    """

    original_name: str
    timestamp: str  # ISO 8601, pl. "2026-09-06T14:30:00"

    def to_dict(self) -> dict:
        return {"original_name": self.original_name, "timestamp": self.timestamp}

    @staticmethod
    def from_dict(data: dict) -> ProfileMeta:
        return ProfileMeta(
            original_name=data.get("original_name", ""),
            timestamp=data.get("timestamp", ""),
        )


# --- Új dataclass: ProfileData ---


@dataclass
class ProfileData:
    """Egy aktív profil saját, profilonként külön tárolt adatai.

    A projekt-szintű mezők (borítókép, 'Mire jó a program', rövid leírás)
    NEM ide tartoznak — azok a Project dataclass-ban maradnak, közösek
    minden profil között. Ez a dataclass a profiles/<Name>/profile_meta.json
    tartalmát írja le: kezdés/befejezés dátum, mérföldkövek, és a profil
    saját (kézzel beállított) státusza a kártyán megjelenő pötty-höz.
    """

    status: ProjectStatus = ProjectStatus.NOT_STARTED
    start_date: str | None = None
    end_date: str | None = None
    milestones: list[Milestone] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "status": self.status.value,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "milestones": [m.to_dict() for m in self.milestones],
        }

    @staticmethod
    def from_dict(data: dict) -> ProfileData:
        return ProfileData(
            status=ProjectStatus(data.get("status", "not_started")),
            start_date=data.get("start_date"),
            end_date=data.get("end_date"),
            milestones=[Milestone.from_dict(m) for m in data.get("milestones", [])],
        )
