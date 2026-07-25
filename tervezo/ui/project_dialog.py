from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QPixmap

from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..core.models import ProjectStatus, TaskItem, TaskStatus
from ..core.storage import Storage
from .widgets import MilestoneDialog, TaskEditDialog, TaskRowWidget, build_richtext_toolbar
from settings.translations import tr
from config import ASSETS_DIR





class ProjectDetailsWidget(QWidget):
    """Projekt-részletnézet tartalma (tabok + gombsor).

    Ez a widget önmagában is beágyazható akár egy QDialog-ba
    (lásd ProjectDialog lentebb), akár a főablak egy jobb oldali
    panelébe (sidebar nézet) — a tényleges tartalom és logika egy helyen
    van, csak a "kereten" (dialógus vs. sidebar) múlik, hogyan jelenik meg.
    """

    project_changed = Signal()
    project_deleted = Signal()
    close_requested = Signal()

    def __init__(
        self,
        storage: Storage,
        project_dir: Path,
        parent: QWidget | None = None,
        show_close_button: bool = True,
    ):
        super().__init__(parent)
        self.storage = storage
        self.project = storage.read_project(project_dir)
        self.tasks: list[TaskItem] = storage.read_tasks(project_dir)

        self._deleted = False
        self._pending_cover_path: Path | None = None
        self._pending_cover_removed = False

        layout = QVBoxLayout(self)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs, 1)

        self._build_overview_tab()
        self._build_journal_tab()
        self._build_tasks_tabs()

        button_row = QHBoxLayout()
        self.delete_btn = QPushButton(tr("common.delete"))
        self.delete_btn.clicked.connect(self._on_delete)
        button_row.addWidget(self.delete_btn)
        button_row.addStretch(1)

        save_btn = QPushButton(tr("common.save"))
        save_btn.clicked.connect(self._on_save)
        button_row.addWidget(save_btn)

        if show_close_button:
            close_btn = QPushButton(tr("common.close"))
            close_btn.clicked.connect(self.close_requested.emit)
            button_row.addWidget(close_btn)

        layout.addLayout(button_row)

    # ---------- Áttekintés ----------
    def _build_overview_tab(self) -> None:
        tab = QWidget()
        form = QFormLayout(tab)

        # --- Borítókép ---
        cover_row = QHBoxLayout()
        self.cover_preview = QLabel()
        self.cover_preview.setFixedSize(120, 90)
        self.cover_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cover_preview.setStyleSheet("border: 1px solid #999; background: #222; color: #888;")
        cover_row.addWidget(self.cover_preview)

        cover_buttons = QVBoxLayout()
        choose_cover_btn = QPushButton("Borítókép választása…")
        choose_cover_btn.clicked.connect(self._on_choose_cover)
        cover_buttons.addWidget(choose_cover_btn)

        remove_cover_btn = QPushButton(tr("common.delete"))
        remove_cover_btn.clicked.connect(self._on_remove_cover)
        cover_buttons.addWidget(remove_cover_btn)
        cover_buttons.addStretch(1)

        cover_row.addLayout(cover_buttons)
        cover_row.addStretch(1)
        form.addRow("Borítókép", cover_row)

        self._reload_cover_preview()




        self.purpose_edit = QPlainTextEdit(self.project.purpose)
        self.purpose_edit.setFixedHeight(100)
        form.addRow(tr("project.purpose_label"), self.purpose_edit)

        self.description_edit = QLineEdit(self.project.description)
        form.addRow(tr("project.description_label"), self.description_edit)

        self.status_combo = QComboBox()
        for status in ProjectStatus:
            self.status_combo.addItem(f"{status.icon} {status.label}", status)
        idx = self.status_combo.findData(self.project.status)
        if idx >= 0:
            self.status_combo.setCurrentIndex(idx)
        form.addRow(tr("project.status_label"), self.status_combo)

        self.start_date_edit = QLineEdit(self.project.start_date or "")
        self.start_date_edit.setPlaceholderText(tr("common.date_placeholder"))
        form.addRow(tr("project.start_date_label"), self.start_date_edit)

        self.end_date_edit = QLineEdit(self.project.end_date or "")
        self.end_date_edit.setPlaceholderText(tr("common.date_placeholder"))
        form.addRow(tr("project.end_date_label"), self.end_date_edit)

        self.milestone_list = QListWidget()
        self._reload_milestones()
        form.addRow(tr("project.milestones_label"), self.milestone_list)

        ms_buttons = QHBoxLayout()
        add_ms_btn = QPushButton(tr("common.add_ellipsis"))
        add_ms_btn.clicked.connect(self._on_add_milestone)
        remove_ms_btn = QPushButton(tr("common.delete"))
        remove_ms_btn.clicked.connect(self._on_remove_milestone)
        ms_buttons.addWidget(add_ms_btn)
        ms_buttons.addWidget(remove_ms_btn)
        form.addRow("", ms_buttons)

        self.tabs.addTab(tab, tr("project.tab.overview"))



    def _reload_cover_preview(self, override_path: Path | str | None = None) -> None:
        path = override_path or self.project.photo_path
        if path and Path(path).exists():
            pixmap = QPixmap(str(path))
            if not pixmap.isNull():
                self.cover_preview.setPixmap(
                    pixmap.scaled(
                        self.cover_preview.width(),
                        self.cover_preview.height(),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
                return
        self.cover_preview.setPixmap(QPixmap())
        self.cover_preview.setText("Nincs borítókép")


    
   


    def _on_choose_cover(self) -> None:
        # A dialógust csak a kattintás eseményének teljes lezárása UTÁN
        # nyitjuk meg (singleShot(0, ...)): ha a modális fájlválasztót
        # közvetlenül a "clicked" jelzésből, szinkron módon nyitjuk meg,
        # a Qt belső "egér alatti widget" nyomkövetése inkonzisztens
        # állapotba kerülhet a dialógus bezárásakor, ami natív
        # szegmentálási hibát okoz (dangling widget-mutató).
        QTimer.singleShot(0, self._open_cover_dialog)

    def _open_cover_dialog(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Borítókép választása",
            "",
            "Képek (*.png *.jpg *.jpeg *.bmp *.webp)",
            options=QFileDialog.Option.DontUseNativeDialog,
        )
        if not file_path:
            return

        chosen = Path(file_path).resolve()
        assets_dir = (self.project.path / ASSETS_DIR).resolve()

        try:
            chosen.relative_to(assets_dir)
            already_in_assets = True
        except ValueError:
            already_in_assets = False

        if already_in_assets:
            # Már a projekt assets mappájában van -> nem másolunk, kérdés nélkül használjuk.
            self._pending_cover_path = None
            self._pending_cover_removed = False
            self.project.photo = f"{ASSETS_DIR}/{chosen.name}"
        else:
            # Külső fájl -> mentéskor bemásoljuk az assets mappába.
            self._pending_cover_path = chosen
            self._pending_cover_removed = False

        self._reload_cover_preview(override_path=chosen)

    def _on_remove_cover(self) -> None:
        self._pending_cover_path = None
        self._pending_cover_removed = True
        self.project.photo = None
        self._reload_cover_preview()


    def _reload_milestones(self) -> None:
        self.milestone_list.clear()
        for m in self.project.milestones:
            item = QListWidgetItem(f"{m.date} — {m.title}")
            item.setData(Qt.ItemDataRole.UserRole, m)
            self.milestone_list.addItem(item)

    def _on_add_milestone(self) -> None:
        dlg = MilestoneDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            milestone = dlg.get_milestone()
            if milestone:
                self.project.milestones.append(milestone)
                self._reload_milestones()

    def _on_remove_milestone(self) -> None:
        item = self.milestone_list.currentItem()
        if not item:
            return
        milestone = item.data(Qt.ItemDataRole.UserRole)
        self.project.milestones.remove(milestone)
        self._reload_milestones()

    # ---------- Napló ----------
    def _build_journal_tab(self) -> None:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        self.journal_editor = QTextEdit()
        self.journal_editor.setHtml(self.storage.read_journal(self.project.path))

        toolbar = build_richtext_toolbar(self.journal_editor, self)
        new_entry_btn = QPushButton(tr("project.new_journal_entry"))
        new_entry_btn.clicked.connect(self._on_new_journal_entry)
        toolbar.addSeparator()
        toolbar.addWidget(new_entry_btn)

        layout.addWidget(toolbar)
        layout.addWidget(self.journal_editor, 1)

        self.tabs.addTab(tab, tr("project.tab.journal"))

    def _on_new_journal_entry(self) -> None:
        html = self.journal_editor.toHtml()
        cursor = self.journal_editor.textCursor()
        cursor.movePosition(cursor.MoveOperation.Start)
        if not self.storage.has_today_header(html):
            cursor.insertHtml(self.storage.build_today_header_html())
        self.journal_editor.setTextCursor(cursor)
        self.journal_editor.setFocus()

    # ---------- Feladatok ----------
    def _build_tasks_tabs(self) -> None:
        next_tab = QWidget()
        next_layout = QVBoxLayout(next_tab)
        self.next_tasks_list = QListWidget()
        next_layout.addWidget(self.next_tasks_list, 1)

        add_row = QHBoxLayout()
        self.new_task_edit = QLineEdit()
        self.new_task_edit.setPlaceholderText(tr("project.new_task_placeholder"))
        add_task_btn = QPushButton(tr("common.add"))
        add_task_btn.clicked.connect(self._on_add_task)
        add_row.addWidget(self.new_task_edit, 1)
        add_row.addWidget(add_task_btn)
        next_layout.addLayout(add_row)

        self.tabs.addTab(next_tab, tr("project.tab.next_tasks"))

        in_progress_tab = QWidget()
        in_progress_layout = QVBoxLayout(in_progress_tab)
        self.in_progress_tasks_list = QListWidget()
        in_progress_layout.addWidget(self.in_progress_tasks_list, 1)
        self.tabs.addTab(in_progress_tab, tr("project.tab.in_progress_tasks"))

        done_tab = QWidget()
        done_layout = QVBoxLayout(done_tab)
        self.done_tasks_list = QListWidget()
        done_layout.addWidget(self.done_tasks_list, 1)
        self.tabs.addTab(done_tab, tr("project.tab.done_tasks"))

        self._reload_tasks()

    def _reload_tasks(self) -> None:
        self.next_tasks_list.clear()
        self.in_progress_tasks_list.clear()
        self.done_tasks_list.clear()

        list_by_status = {
            TaskStatus.PENDING: (self.next_tasks_list, "pending"),
            TaskStatus.IN_PROGRESS: (self.in_progress_tasks_list, "in_progress"),
            TaskStatus.DONE: (self.done_tasks_list, "done"),
        }

        for task in self.tasks:
            target_list, mode = list_by_status[task.status]

            row = TaskRowWidget(task, mode=mode)
            row.start_requested.connect(self._on_task_start)
            row.toggled.connect(self._on_task_toggled)
            row.edit_requested.connect(self._on_task_edit)
            row.delete_requested.connect(self._on_task_delete)

            item = QListWidgetItem()
            item.setSizeHint(row.sizeHint())
            target_list.addItem(item)
            target_list.setItemWidget(item, row)

    def _on_add_task(self) -> None:
        text = self.new_task_edit.text().strip()
        if not text:
            return
        new_id = self.storage.next_task_id(self.tasks)
        self.tasks.append(TaskItem(id=new_id, html=text, status=TaskStatus.PENDING))
        self.new_task_edit.clear()
        self._reload_tasks()

    def _on_task_start(self, task_id: int) -> None:
        for t in self.tasks:
            if t.id == task_id:
                t.status = TaskStatus.IN_PROGRESS
                break
        self._reload_tasks()

    def _on_task_toggled(self, task_id: int, checked: bool) -> None:
        # checked=True: folyamatban -> kész. checked=False: kész -> folyamatban.
        for t in self.tasks:
            if t.id == task_id:
                t.status = TaskStatus.DONE if checked else TaskStatus.IN_PROGRESS
                break
        self._reload_tasks()

    def _on_task_edit(self, task_id: int) -> None:
        task = next((t for t in self.tasks if t.id == task_id), None)
        if not task:
            return
        dlg = TaskEditDialog(self, html=task.html)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            task.html = dlg.get_html()
            self._reload_tasks()

    def _on_task_delete(self, task_id: int) -> None:
        self.tasks = [t for t in self.tasks if t.id != task_id]
        self._reload_tasks()

    # ---------- Mentés / Törlés ----------
    def _collect_project_from_form(self) -> None:
        self.project.purpose = self.purpose_edit.toPlainText().strip()
        self.project.description = self.description_edit.text().strip()
        self.project.status = self.status_combo.currentData()
        self.project.start_date = self.start_date_edit.text().strip() or None
        self.project.end_date = self.end_date_edit.text().strip() or None

    def _on_save(self) -> None:
        self._collect_project_from_form()

        if self._pending_cover_path is not None:
            rel_path = self.storage.set_project_cover(self.project.path, self._pending_cover_path)
            self.project.photo = rel_path
        elif self._pending_cover_removed:
            self.storage.remove_project_cover(self.project.path)
            self.project.photo = None

        self.storage.write_project(self.project)
        self.storage.write_journal(self.project.path, self.journal_editor.toHtml())
        self.storage.write_tasks(self.project.path, self.tasks)

        self._pending_cover_path = None
        self._pending_cover_removed = False
        self.project_changed.emit()

    def _on_delete(self) -> None:
        buttons = QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        res = QMessageBox.warning(
            self,
            tr("project.delete_confirm_title"),
            tr("project.delete_confirm_text", name=self.project.name),
            buttons,
        )
        if res != QMessageBox.StandardButton.Yes:
            return
        self.storage.delete_project(self.project.path)
        self._deleted = True
        self.project_deleted.emit()


class ProjectDialog(QDialog):
    """Vékony QDialog-héj a ProjectDetailsWidget köré ('Ablak' nézetmód)."""

    project_changed = Signal()
    project_deleted = Signal()

    def __init__(self, storage: Storage, project_dir: Path, parent: QWidget | None = None):
        super().__init__(parent)

        self.details = ProjectDetailsWidget(storage, project_dir, self)
        self.setWindowTitle(tr("project.details_title", name=self.details.project.name))
        self.resize(720, 580)

        layout = QVBoxLayout(self)
        layout.addWidget(self.details)

        self.details.project_changed.connect(self.project_changed)
        self.details.project_deleted.connect(self.project_deleted)
        self.details.project_deleted.connect(self.accept)
        self.details.close_requested.connect(self.accept)