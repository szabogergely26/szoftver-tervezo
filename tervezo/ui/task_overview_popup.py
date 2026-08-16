from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from settings.translations import tr

from ..core.models import TaskStatus
from ..core.storage import Storage
from ..core.workspace import Workspace


class TaskOverviewPopup(QFrame):
    """Projektfüggetlen, kattintható áttekintő popup a hátralévő
    (PENDING + IN_PROGRESS) feladatokról.

    Csak áttekintésre és "kész" jelölésre szolgál — nem hoz létre,
    nem indít el és nem szerkeszt feladatot. A cím sorra kattintva
    megnyílik a projekt ProjectDialog-ja (a UI ezt a project_open_requested
    szignálon keresztül kéri a MainWindow-tól).
    """

    project_open_requested = Signal(object, int)  # (project_dir, tab_index)

    # A shadow-nak "levegő" kell a top-level ablakon belül, különben a
    # blur/offset a window szélén levágódik (a QGraphicsDropShadowEffect
    # nem rajzolhat a widget saját bounding rect-jén túlra).
    SHADOW_MARGIN = 24
    SHADOW_Y_OFFSET = 4

    def __init__(
        self,
        storage: Storage,
        workspace: Workspace,
        parent: QWidget | None = None,
    ):
        super().__init__(parent, Qt.WindowType.Popup)
        self.storage = storage
        self.workspace = workspace

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setObjectName("TaskOverviewPopup")

        outer = QVBoxLayout(self)
        outer.setContentsMargins(
            self.SHADOW_MARGIN,
            self.SHADOW_MARGIN,
            self.SHADOW_MARGIN,
            self.SHADOW_MARGIN + self.SHADOW_Y_OFFSET,
        )

        # A tényleges lekerekített doboz egy belső kártya-widget: az
        # árnyék erre kerül, nem a (margó nélküli) top-level ablakra.
        self._card = QFrame(self)
        self._card.setObjectName("TaskOverviewCard")
        self._card.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._card.setMinimumWidth(280)
        self._card.setMaximumHeight(420)
        outer.addWidget(self._card)

        shadow = QGraphicsDropShadowEffect(self._card)
        shadow.setBlurRadius(self.SHADOW_MARGIN)
        shadow.setXOffset(0)
        shadow.setYOffset(self.SHADOW_Y_OFFSET)
        shadow.setColor(QColor(0, 0, 0, 60))
        self._card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(self._card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        # Saját, belső "címsor" a natív Popup ablak-típus miatt (annak
        # nincs OS-szintű díszítése/címsora).
        header = QLabel(tr("main.status_bar.popup_title"))
        header.setObjectName("TaskOverviewHeader")
        header.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        card_layout.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        card_layout.addWidget(scroll)

        self._content = QWidget()
        self._layout = QVBoxLayout(self._content)
        self._layout.setSpacing(2)
        self._layout.setContentsMargins(10, 10, 10, 10)
        scroll.setWidget(self._content)

        self._populate()

    # ---------- Felépítés ----------
    def _clear_layout(self) -> None:
        while self._layout.count():
            item = self._layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    def _populate(self) -> None:
        self._clear_layout()

        any_task = False
        for project_dir in self.storage.list_projects(self.workspace.projects_dir):
            project = self.storage.read_project(project_dir)
            tasks = [
                t for t in self.storage.read_tasks(project_dir)
                if t.status in (TaskStatus.PENDING, TaskStatus.IN_PROGRESS)
            ]
            if not tasks:
                continue

            any_task = True

            title_label = QLabel(project.name)
            title_label.setStyleSheet("font-weight: bold;")
            self._layout.addWidget(title_label)

            for task in tasks:
                self._layout.addWidget(self._build_task_row(project_dir, task))

            self._layout.addSpacing(6)

        if not any_task:
            empty_label = QLabel(tr("main.status_bar.popup_empty"))
            empty_label.setStyleSheet("color: palette(mid);")
            self._layout.addWidget(empty_label)

        self._layout.addStretch()

    def _build_task_row(self, project_dir: Path, task) -> QWidget:
        row = QWidget()
        row.setObjectName("TaskOverviewRow")
        row.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        row.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(6, 2, 6, 2)

        checkbox = QCheckBox()
        checkbox.setChecked(False)
        checkbox.toggled.connect(
            lambda checked, p=project_dir, t=task: self._on_task_checked(p, t, checked)
        )
        row_layout.addWidget(checkbox)

        label = QLabel(task.title)
        label.setWordWrap(True)
        label.setCursor(Qt.CursorShape.PointingHandCursor)
        label.mousePressEvent = (
            lambda event, p=project_dir: self._on_task_label_clicked(p)
        )
        row_layout.addWidget(label, 1)

        return row

    # ---------- Interakció ----------
    def _on_task_checked(self, project_dir: Path, task, checked: bool) -> None:
        if not checked:
            # A popup csak "kész"-re jelölésre szolgál — visszapipálást
            # itt nem kezelünk, az a projekt ProjectDialog-jában történhet.
            return

        tasks = self.storage.read_tasks(project_dir)
        for t in tasks:
            if t.id == task.id:
                t.status = TaskStatus.DONE
                t.completed_at = datetime.now().astimezone().strftime("%Y.%m.%d %H:%M")
                break
        self.storage.write_tasks(project_dir, tasks)

        self._populate()

    def _on_task_label_clicked(self, project_dir: Path) -> None:
        self.close()
        self.project_open_requested.emit(project_dir, 1)