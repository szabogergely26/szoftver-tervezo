from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtWidgets import QLabel, QWidget

from settings.translations import tr

from ..core.models import TaskStatus
from ..core.storage import Storage
from ..core.workspace import Workspace


class InProgressTaskLabel(QLabel):
    """Statusbar-widget, ami a projektfüggetlenül összegyűjtött,
    IN_PROGRESS állapotú feladatok közül mindig egyet mutat, a
    "Folyamatban: <Projekt> - <Feladat>" formátumban.

    Ha egyszerre több feladat is IN_PROGRESS állapotban van, a widget
    időzítővel lapoz köztük (a "▸ index/összes" jelzéssel kiegészítve).
    Ha nincs egyetlen IN_PROGRESS feladat sem, a widget elrejti magát.
    """

    project_open_requested = Signal(object, int)  # (project_dir, tab_index)

    ROTATE_INTERVAL_MS = 5000

    def __init__(
        self,
        storage: Storage,
        workspace: Workspace,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.storage = storage
        self.workspace = workspace

        self.setObjectName("InProgressTaskLabel")
        self.setStyleSheet("padding: 2px 8px; border-radius: 4px;")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # (project_dir, project_name, task_title) hármasok
        self._entries: list[tuple[Path, str, str]] = []
        self._current_index = 0

        self._rotate_timer = QTimer(self)
        self._rotate_timer.setInterval(self.ROTATE_INTERVAL_MS)
        self._rotate_timer.timeout.connect(self._show_next)

        self.hide()

    # ---------- Adatfrissítés ----------
    def refresh(self) -> None:
        """Újraolvassa az összes projekt IN_PROGRESS feladatait, és
        ennek megfelelően mutatja/rejti, illetve frissíti a widgetet.
        """
        entries: list[tuple[Path, str, str]] = []

        for project_dir in self.storage.list_projects(self.workspace.projects_dir):
            project = self.storage.read_project(project_dir)
            for task in self.storage.read_tasks(project_dir):
                if task.status == TaskStatus.IN_PROGRESS:
                    entries.append((project_dir, project.name, task.title))

        self._entries = entries
        self._current_index = 0

        if not self._entries:
            self._rotate_timer.stop()
            self.hide()
            return

        if len(self._entries) > 1:
            self._rotate_timer.start()
        else:
            self._rotate_timer.stop()

        self._update_text()
        self.show()

    # ---------- Lapozás ----------
    def _show_next(self) -> None:
        if not self._entries:
            return
        self._current_index = (self._current_index + 1) % len(self._entries)
        self._update_text()

    def _update_text(self) -> None:
        if not self._entries:
            return

        _project_dir, project_name, task_title = self._entries[self._current_index]
        prefix = tr("main.status_bar.in_progress")
        text = f"{prefix} {project_name} - {task_title}"

        if len(self._entries) > 1:
            text += f"  ▸ {self._current_index + 1}/{len(self._entries)}"

        self.setText(text)

    # ---------- Interakció ----------
    def mousePressEvent(self, event) -> None:  # noqa: N802 (Qt override)
        if not self._entries:
            super().mousePressEvent(event)
            return

        project_dir, _project_name, _task_title = self._entries[self._current_index]
        self.project_open_requested.emit(project_dir, 3)
        super().mousePressEvent(event)