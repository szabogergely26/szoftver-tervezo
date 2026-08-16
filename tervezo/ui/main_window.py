from __future__ import annotations

import tempfile
import zipfile
from datetime import date
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QIcon, QTextDocumentFragment
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QScrollArea,
    QSplitter,
    QStatusBar,
    QSystemTrayIcon,
    QToolBar,
    QVBoxLayout,
    QWidget,
    QWidgetAction,
)

from config import ICON_PATH
from settings.settings import (
    SettingsDialog,
    get_close_to_tray,
    get_project_view_mode,
    get_splitter_sizes,
    save_splitter_sizes,
)
from settings.translations import language_signal, tr

from ..core.models import TaskStatus
from ..core.storage import Storage
from ..core.workspace import Workspace
from .about_dialog import AboutDialog
from .flow_layout import FlowLayout
from .log_dialog import LogDialog
from .new_project_dialog import NewProjectDialog
from .project_dialog import ProjectDetailsWidget, ProjectDialog
from .task_overview_popup import TaskOverviewPopup
from .widgets import ProjectCard


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._log_dialog: LogDialog | None = None
        self.setWindowIcon(QIcon(str(ICON_PATH)))
        self.resize(1100, 720)

        self.storage = Storage()
        self.ws = Workspace()
        self.ws.ensure()
        self.ws.ensure_default_project()

        self._build_ui()
        self._build_menu()
        self._build_toolbar()
        self._build_status_bar()
        self.retranslate_ui()

        self._apply_view_mode_visibility()

        self.reload_cards()

        self.reload_cards()

        self._force_quit = False
        self._build_tray_icon()

        

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
            if item is None:
                continue
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
        # A menüben a szövegek a retranslate_ui() metódusban kerülnek beállításra.

        # --- Menüsáv és Fájl menü
        self.file_menu = self.menuBar().addMenu("")

        self.new_project_action = QAction(QIcon.fromTheme("document-new"), "", self)
        self.new_project_action.triggered.connect(self.new_project)
        self.file_menu.addAction(self.new_project_action)

        self.file_menu.addSeparator()


        # --- Megnyitás / Mentés / Beállítások
        self.open_action = QAction(QIcon.fromTheme("document-open"), "", self)
        self.open_action.triggered.connect(self.import_workspace)
        self.file_menu.addAction(self.open_action)

        self.save_action = QAction(QIcon.fromTheme("document-save"), "", self)
        self.save_action.triggered.connect(self.export_workspace)
        self.file_menu.addAction(self.save_action)

        self.file_menu.addSeparator()

        # --- Beállítások
        self.settings_action = QAction(QIcon.fromTheme("preferences-system"), "", self)
        self.settings_action.triggered.connect(self.open_settings)
        self.file_menu.addAction(self.settings_action)


        self.file_menu.addSeparator()

        # --- Kilépés
        self.quit_action = QAction(QIcon.fromTheme("application-exit"), "", self)
        self.quit_action.triggered.connect(self._quit_app)
        self.file_menu.addAction(self.quit_action)


         # --- Eszközök menü
        self.tools_menu = self.menuBar().addMenu("")

        self.log_action = QAction(QIcon.fromTheme("utilities-log-viewer"), "", self)
        self.log_action.triggered.connect(self.open_log_dialog)
        self.tools_menu.addAction(self.log_action)



        # --- Súgó menü
        self.help_menu = self.menuBar().addMenu(tr("main.menu.help"))

        self.about_action = QAction(QIcon.fromTheme("help-about"), tr("main.action.about"), self)
        self.about_action.triggered.connect(self.open_about)
        self.help_menu.addAction(self.about_action)




    # --- Tálcaikon
    def _build_tray_icon(self) -> None:
        self.tray_icon = QSystemTrayIcon(QIcon(str(ICON_PATH)), self)
        self.tray_icon.setToolTip(tr("main.window_title"))

        self.tray_menu = QMenu()
        self.tray_menu.aboutToShow.connect(self._rebuild_tray_menu)
        self.tray_icon.setContextMenu(self.tray_menu)

        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            self._show_main_window()

    def _show_main_window(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def _rebuild_tray_menu(self) -> None:
        self.tray_menu.clear()

        open_action = self.tray_menu.addAction(tr("main.tray.open"))
        open_action.triggered.connect(self._show_main_window)

        self.tray_menu.addSeparator()

        self._add_task_submenu(tr("main.tray.in_progress"), TaskStatus.IN_PROGRESS, tab_index=2)
        self._add_task_submenu(tr("main.tray.next"), TaskStatus.PENDING, tab_index=1)

        self.tray_menu.addSeparator()

        quit_action = self.tray_menu.addAction(tr("main.action.quit"))
        quit_action.triggered.connect(self._quit_app)


    def _add_task_submenu(
            self, 
            title: str, 
            status: TaskStatus,
            tab_index: int

        ) -> None:

        submenu = self.tray_menu.addMenu(title)
        found_any = False

        for project_dir in self.storage.list_projects(self.ws.projects_dir):
            project = self.storage.read_project(project_dir)
            tasks = [t for t in self.storage.read_tasks(project_dir) if t.status == status]
            if not tasks:
                continue

            found_any = True
            project_menu = submenu.addMenu(project.name)
            for task in tasks:
                plain_text = QTextDocumentFragment.fromHtml(task.html).toPlainText()
                action = project_menu.addAction(plain_text or "…")
                action.triggered.connect(
                    lambda checked=False, p=project_dir, i=tab_index: self._open_project_in_dialog(p, i)
                )

        if not found_any:
            empty_action = submenu.addAction(tr("main.tray.empty"))
            empty_action.setEnabled(False)




    
    def _add_readonly_menu_label(self, menu: QMenu, text: str) -> None:
        """Csak megjelenítő, nem kattintható menütétel – jól olvasható, egyedi színnel."""
        label = QLabel(text)
        label.setStyleSheet("padding: 4px 24px; color: palette(text);")
        label.setWordWrap(True)

        action = QWidgetAction(menu)
        action.setDefaultWidget(label)
        action.setEnabled(False)  # kattintásra reagáljon-e: nem
        menu.addAction(action)

    def _quit_app(self) -> None:
        self._force_quit = True
        self.tray_icon.hide()
        app = QApplication.instance()
        assert app is not None
        app.quit()

    def closeEvent(self, event) -> None:
        if self._force_quit or not get_close_to_tray():
            self.tray_icon.hide()
            event.accept()
            return

        event.ignore()
        self.hide()
        self.tray_icon.showMessage(
            tr("main.window_title"),
            tr("main.tray.minimized_message"),
            QSystemTrayIcon.MessageIcon.Information,
            2000,
        )

    # --- Tálcaikon: vége --------



    def open_log_dialog(self) -> None:
        if  self._log_dialog is None:
            self._log_dialog = LogDialog(self)
            self._log_dialog.destroyed.connect(self._on_log_dialog_destroyed)
        self._log_dialog.show()
        self._log_dialog.raise_()
        self._log_dialog.activateWindow()

    def _on_log_dialog_destroyed(self) -> None:
        self._log_dialog = None


    def open_about(self) -> None:
        dialog = AboutDialog(self)
        dialog.exec()


    






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



    def _build_status_bar(self) -> None:
        self.status_bar = QStatusBar()
        self.status_bar.setStyleSheet("QStatusBar { border-top: 1px solid palette(mid); }")
        self.setStatusBar(self.status_bar)

        self.next_task_label = QLabel()
        self.next_task_label.setStyleSheet("padding: 0 6px;")
        self.next_task_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.next_task_label.mousePressEvent = self._show_task_overview_popup


        self.status_bar.addPermanentWidget(self.next_task_label)


    def _show_task_overview_popup(self, event) -> None:
        popup = TaskOverviewPopup(self.storage, self.ws, self)
        popup.project_open_requested.connect(self._open_project_in_dialog)

        pos = self.next_task_label.mapToGlobal(self.next_task_label.rect().topRight())
        pos.setX(pos.x() - popup.sizeHint().width())
        pos.setY(pos.y() - popup.sizeHint().height())
        popup.move(pos)
        popup.show()



    # ---------- Nyelv ----------
    def _on_language_changed(self, _lang_code: str) -> None:
        self.retranslate_ui()
        self.reload_cards()

    def retranslate_ui(self) -> None:
        self.setWindowTitle(tr("main.window_title"))

        self.file_menu.setTitle(tr("main.menu.file"))
        self.new_project_action.setText(tr("main.action.new_project"))

        self.open_action.setText(tr("main.action.import_workspace"))
        self.save_action.setText(tr("main.action.export_workspace"))

        self.settings_action.setText(tr("main.action.settings"))
        self.quit_action.setText(tr("main.action.quit"))
        self.tools_menu.setTitle(tr("main.menu.tools"))
        self.log_action.setText(tr("main.action.open_log"))
        self.about_action.setText(tr("main.action.about"))

        self.toolbar.setWindowTitle(tr("main.toolbar.name"))
        self.act_new_project_toolbar.setText(tr("main.action.new_project_toolbar"))
        self.next_task_label.setText(tr("main.status_bar.next_task"))

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
            # A projektablak modális eseményciklust indít. Ha közvetlenül a
            # kártya egéreseményéből nyitnánk meg, a Mentés közben futó
            # reload_cards() deleteLater()-rel törölhetné azt a kártyát,
            # amelynek natív egéreseménye még nem ért véget. A sorba állított
            # kapcsolat csak az aktuális egéresemény teljes lefutása után
            # hívja meg az open_project metódust.
            card.clicked.connect(
                self.open_project,
                Qt.ConnectionType.QueuedConnection,
            )
            self.flow_layout.addWidget(card)

    def open_project(self, project_dir: Path) -> None:
        if get_project_view_mode() == "sidebar":
            self._open_project_in_sidebar(project_dir)
        else:
            self._open_project_in_dialog(project_dir)


    def export_workspace(self) -> None:
        default_name = f"Projektek_mentes_{date.today().strftime('%Y-%m-%d')}.zip"  # noqa: DTZ011 (helyi naptári dátum kell, nem UTC)
        path_str, _ = QFileDialog.getSaveFileName(
            self, tr("main.action.export_workspace"), default_name, "Zip fájlok (*.zip)"
        )
        if not path_str:
            return

        try:
            self.ws.export_to_zip(Path(path_str))
        except OSError as exc:
            QMessageBox.critical(self, tr("main.export_error_title"), str(exc))
            return

        QMessageBox.information(
            self,
            tr("main.export_done_title"),
            tr("main.export_done_text", path=path_str),
        )

    def import_workspace(self) -> None:
        path_str, _ = QFileDialog.getOpenFileName(
            self, tr("main.action.import_workspace"), "", "Zip fájlok (*.zip)"
        )
        if not path_str:
            return

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            try:
                conflicts = self.ws.preview_conflicts(Path(path_str), tmp_path)
            except (OSError, zipfile.BadZipFile) as exc:
                QMessageBox.critical(self, tr("main.import_error_title"), str(exc))
                return

            if conflicts:
                names = "\n".join(f"- {c}" for c in conflicts)
                reply = QMessageBox.question(
                    self,
                    tr("main.import_conflict_title"),
                    tr("main.import_conflict_text", names=names),
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return


            extra_local = self.ws.preview_extra_local(tmp_path)
            if extra_local:
                names = "\n".join(f"- {c}" for c in extra_local)
                reply = QMessageBox.question(
                    self,
                    tr("main.import_extra_title"),
                    tr("main.import_extra_text", names=names),
                    QMessageBox.StandardButton.Yes
                    | QMessageBox.StandardButton.No
                    | QMessageBox.StandardButton.Cancel,
                )
                if reply == QMessageBox.StandardButton.Cancel:
                    return
                if reply == QMessageBox.StandardButton.No:
                    self.ws.remove_projects(extra_local)


            self.ws.import_from_extracted(tmp_path)

        self.reload_cards()
        QMessageBox.information(
            self, tr("main.import_done_title"), tr("main.import_done_text")
        )








    def _open_project_in_dialog(
            self, 
            project_dir: Path,
            initial_tab_index: int | None = None

    )-> None:

        dlg = ProjectDialog(
            self.storage, project_dir, self, initial_tab_index=initial_tab_index
        )
        dlg.project_changed.connect(lambda: QTimer.singleShot(0, self.reload_cards))
        dlg.project_deleted.connect(lambda: QTimer.singleShot(0, self.reload_cards))
        dlg.exec()

    def _open_project_in_sidebar(self, project_dir: Path) -> None:
        while self.details_layout.count():
            item = self.details_layout.takeAt(0)
            if item is None:
                continue
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
