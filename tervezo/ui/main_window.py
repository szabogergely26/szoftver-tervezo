from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QKeySequence, QIcon
from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QScrollArea,
    QSplitter,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from ..core.storage import Storage
from ..core.workspace import Workspace
from .flow_layout import FlowLayout
from .new_project_dialog import NewProjectDialog
from .project_dialog import ProjectDialog, ProjectDetailsWidget
from .widgets import ProjectCard

from config import ICON_PATH

from settings.settings import (
    SettingsDialog, 
    get_project_view_mode,
    get_splitter_sizes,
    save_splitter_sizes,
    load_settings,
    save_settings,
)

from settings.translations import tr, language_signal


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon(str(ICON_PATH)))
        self.resize(1100, 720)

        self.storage = Storage()
        self.ws = Workspace()
        self.ws.ensure()
        self.ws.ensure_default_project()

        self._build_ui()
        self._build_menu()
        self._build_toolbar()
        self.retranslate_ui()

        self._apply_view_mode_visibility()

        self.reload_cards()



        self.reload_cards()

        language_signal.changed.connect(self._on_language_changed)

    # ---------- UI ----------
    def _build_ui(self) -> None:
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        self.cards_container = QWidget()
        self.flow_layout = FlowLayout(self.cards_container, margin=12, spacing=12)

        self.scroll_area.setWidget(self.cards_container)

        # --- Jobb oldali panel: ide kerül a ProjectDetailsWidget,
        # ha a Beállításokban "Oldalsáv" nézetmód van kiválasztva ---
        self.details_panel = QWidget()
        self.details_layout = QVBoxLayout(self.details_panel)
        self.details_layout.setContentsMargins(0, 0, 0, 0)
        self._reset_sidebar_placeholder()

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.addWidget(self.scroll_area)
        self.splitter.addWidget(self.details_panel)
        self.splitter.setStretchFactor(0, 3)
        self.splitter.setStretchFactor(1, 2)

        saved_sizes = get_splitter_sizes()
        if saved_sizes:
            self.splitter.setSizes(saved_sizes)
        else:
            # Alapból keskenyebb oldalsáv, mint korábban (650/450 helyett)
            self.splitter.setSizes([800, 300])

        self.splitter.splitterMoved.connect(self._on_splitter_moved)

        self.setCentralWidget(self.splitter)


    def _reset_sidebar_placeholder(self) -> None:
        while self.details_layout.count():
            item = self.details_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        placeholder = QLabel(tr("main.sidebar.placeholder"))
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        placeholder.setWordWrap(True)
        self.details_layout.addWidget(placeholder)


    def _apply_view_mode_visibility(self) -> None:
        """A jobb oldali panel csak 'sidebar' nézetmódban látszódjon."""
        is_sidebar_mode = get_project_view_mode() == "sidebar"
        self.details_panel.setVisible(is_sidebar_mode)



    def _on_splitter_moved(self, _pos: int, _index: int) -> None:
        # Csak akkor mentjük el, ha ténylegesen látszik az oldalsáv –
        # dialog módban a panel el van rejtve, nem akarjuk elmenteni
        # egy "összement" (0 széles) állapotot.
        if self.details_panel.isVisible():
            save_splitter_sizes(self.splitter.sizes())








    # ---------- Menü ----------
    def _build_menu(self):
        self.file_menu = self.menuBar().addMenu("")

        self.new_project_action = QAction(QIcon.fromTheme("document-new"), "", self)
        self.new_project_action.triggered.connect(self.new_project)
        self.file_menu.addAction(self.new_project_action)

        self.open_action = QAction(QIcon.fromTheme("document-open"), "", self)
        self.file_menu.addAction(self.open_action)

        self.save_action = QAction(QIcon.fromTheme("document-save"), "", self)
        self.file_menu.addAction(self.save_action)

        self.file_menu.addSeparator()

        self.settings_action = QAction(QIcon.fromTheme("preferences-system"), "", self)
        self.settings_action.triggered.connect(self.open_settings)
        self.file_menu.addAction(self.settings_action)

        self.quit_action = QAction(QIcon.fromTheme("application-exit"), "", self)
        self.quit_action.triggered.connect(self.close)
        self.file_menu.addAction(self.quit_action)

    def open_settings(self) -> None:
        dialog = SettingsDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Nézetmód-váltás után egyszerűbb, ha a sidebar visszaáll
            # placeholder állapotba, mint egy régi módban nyitott
            # tartalmat mutatni tovább.

            self._reset_sidebar_placeholder()
            self._apply_view_mode_visibility()

    def _build_toolbar(self) -> None:
        self.toolbar = QToolBar("", self)
        self.toolbar.setMovable(False)
        self.addToolBar(self.toolbar)

        self.toolbar.setToolButtonStyle(
            Qt.ToolButtonStyle.ToolButtonTextBesideIcon
        )

        self.act_new_project_toolbar = QAction(QIcon.fromTheme("document-new"), "", self)
        self.act_new_project_toolbar.triggered.connect(self.new_project)
        self.toolbar.addAction(self.act_new_project_toolbar)

    # ---------- Nyelv ----------
    def _on_language_changed(self, _lang_code: str) -> None:
        self.retranslate_ui()
        self.reload_cards()

    def retranslate_ui(self) -> None:
        self.setWindowTitle(tr("main.window_title"))

        self.file_menu.setTitle(tr("main.menu.file"))
        self.new_project_action.setText(tr("main.action.new_project"))
        self.open_action.setText(tr("main.action.open"))
        self.save_action.setText(tr("main.action.save"))
        self.settings_action.setText(tr("main.action.settings"))
        self.quit_action.setText(tr("main.action.quit"))

        self.toolbar.setWindowTitle(tr("main.toolbar.name"))
        self.act_new_project_toolbar.setText(tr("main.action.new_project_toolbar"))

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
        if get_project_view_mode() == "sidebar":
            self._open_project_in_sidebar(project_dir)
        else:
            self._open_project_in_dialog(project_dir)

    def _open_project_in_dialog(self, project_dir: Path) -> None:
        dlg = ProjectDialog(self.storage, project_dir, self)
        dlg.project_changed.connect(lambda: QTimer.singleShot(0, self.reload_cards))
        dlg.project_deleted.connect(lambda: QTimer.singleShot(0, self.reload_cards))
        dlg.exec()

    def _open_project_in_sidebar(self, project_dir: Path) -> None:
        while self.details_layout.count():
            item = self.details_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        details = ProjectDetailsWidget(
            self.storage, project_dir, self.details_panel, show_close_button=False
        )
        
        details.project_changed.connect(lambda: QTimer.singleShot(0, self.reload_cards))
        details.project_deleted.connect(lambda: QTimer.singleShot(0, self.reload_cards))
        details.project_deleted.connect(lambda: QTimer.singleShot(0, self._reset_sidebar_placeholder))
        details.close_requested.connect(self._reset_sidebar_placeholder)

        self.details_layout.addWidget(details)




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
            QMessageBox.warning(
                self, tr("common.exists_title"), tr("main.project_exists")
            )
            return

        self.reload_cards()