from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtGui import QAction, QKeySequence, QIcon, Qt
from PySide6.QtWidgets import (
    QDialog,
    QMainWindow,
    QMessageBox,
    QScrollArea,
    QToolBar,
    QWidget,
    QToolBar
)

from ..core.storage import Storage
from ..core.workspace import Workspace
from .flow_layout import FlowLayout
from .new_project_dialog import NewProjectDialog
from .project_dialog import ProjectDialog
from .widgets import ProjectCard

from config import ICON_PATH


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tervező")
        self.setWindowIcon(QIcon(str(ICON_PATH)))
        self.resize(1100, 720)

        self.storage = Storage()
        self.ws = Workspace()
        self.ws.ensure()
        self.ws.ensure_default_project()

        self._build_ui()
        self._build_menu()
        self._build_toolbar()

        self.reload_cards()

    # ---------- UI ----------
    def _build_ui(self) -> None:
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        self.cards_container = QWidget()
        self.flow_layout = FlowLayout(self.cards_container, margin=12, spacing=12)
        # A FlowLayout konstruktora (parent widget átadásával) automatikusan
        # be is állítja magát a cards_container elrendezéseként.

        self.scroll_area.setWidget(self.cards_container)
        self.setCentralWidget(self.scroll_area)

    # ---------- Menü ----------
    def _build_menu(self):
        file_menu = self.menuBar().addMenu("Fájl")

        new_action = QAction(
            QIcon.fromTheme("document-new"),
            "Új projekt",
            self,
        )
        new_action.triggered.connect(self.new_project)
        file_menu.addAction(new_action)

        open_action = QAction(
            QIcon.fromTheme("document-open"),
            "Megnyitás",
            self,
        )
        file_menu.addAction(open_action)

        save_action = QAction(
            QIcon.fromTheme("document-save"),
            "Mentés",
            self,
        )
        file_menu.addAction(save_action)

        file_menu.addSeparator()

        quit_action = QAction(
            QIcon.fromTheme("application-exit"),
            "Kilépés",
            self,
        )
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)


    def _build_toolbar(self) -> None:
        tb = QToolBar("Eszköztár", self)
        tb.setMovable(False)
        self.addToolBar(tb)

        tb.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonTextBesideIcon
    )
        
        act_new_project = QAction(QIcon.fromTheme("document-new"), "+ Új projekt", self)
        act_new_project.triggered.connect(self.new_project)
        tb.addAction(act_new_project)

    # ---------- Kártyák ----------
    def reload_cards(self) -> None:
        while self.flow_layout.count():
            item = self.flow_layout.takeAt(0)
            widget = item.widget() if item else None
            if widget:
                widget.deleteLater()

        for project_dir in self.storage.list_projects(self.ws.projects_dir):
            project = self.storage.read_project(project_dir)
            card = ProjectCard(project)
            card.clicked.connect(self.open_project)
            self.flow_layout.addWidget(card)

    def open_project(self, project_dir: Path) -> None:
        dlg = ProjectDialog(self.storage, project_dir, self)
        # Halasztott hívás (QTimer.singleShot 0 ms): a kártyák törlése így
        # csak azután történik, hogy a hívási verem (pl. az őket megnyitó
        # kattintás-kezelő) teljesen kiürült — elkerülve, hogy egy még
        # "élő" widget alól töröljünk C++ objektumot.
        dlg.project_changed.connect(lambda: QTimer.singleShot(0, self.reload_cards))
        dlg.project_deleted.connect(lambda: QTimer.singleShot(0, self.reload_cards))
        dlg.exec()

    def new_project(self) -> None:
        dlg = NewProjectDialog(self)
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        result = dlg.get_result()
        if result is None:
            return

        try:
            self.storage.create_project(
                self.ws.projects_dir,
                result["name"],
                description=result["description"],
                purpose=result["purpose"],
                photo_source=result["photo_source"],
                initial_tasks_raw=result["initial_tasks_raw"],
            )
        except FileExistsError:
            QMessageBox.warning(self, "Létezik", "Már van ilyen nevű projekt.")
            return

        self.reload_cards()
