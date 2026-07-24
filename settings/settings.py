"""Beállítások ablak – kategória-fa bal oldalt, tartalom jobb oldalt."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QTreeWidget,
    QTreeWidgetItem,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
    QComboBox,
    QFormLayout,
)
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt


import json
from config import ICON_PATH, SETTINGS_FILE
from .translations import tr, set_language, get_language


def load_settings() -> dict:
    """Betölti a settings.json tartalmát, vagy üres dict-et ad vissza, ha nincs."""
    if not SETTINGS_FILE.exists():
        return {}
    try:
        with SETTINGS_FILE.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def save_settings(data: dict) -> None:
    """Elmenti a data dict-et a settings.json-ba."""
    with SETTINGS_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def apply_saved_language() -> None:
    """Induláskor hívandó: beállítja a mentett nyelvet (ha van)."""
    data = load_settings()
    lang = data.get("language")
    if lang in ("hu", "en"):
        set_language(lang)


def get_project_view_mode() -> str:
    """Visszaadja a projekt-megnyitás nézetmódját: 'dialog' vagy 'sidebar'."""
    data = load_settings()
    mode = data.get("project_view_mode")
    return mode if mode in ("dialog", "sidebar") else "dialog"

def get_splitter_sizes() -> list[int] | None:
    """Visszaadja a mentett splitter-arányt (kártyák / oldalsáv), vagy None-t."""
    data = load_settings()
    sizes = data.get("splitter_sizes")
    if isinstance(sizes, list) and len(sizes) == 2:
        return sizes
    return None


def save_splitter_sizes(sizes: list[int]) -> None:
    """Elmenti a splitter jelenlegi méretarányát."""
    data = load_settings()
    data["splitter_sizes"] = list(sizes)
    save_settings(data)





class SettingsDialog(QDialog):
    """Az alkalmazás beállítás ablaka."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self.setWindowTitle(tr("settings.title"))
        self.setMinimumSize(600, 400)

        if ICON_PATH.exists():
            self.setWindowIcon(QIcon(str(ICON_PATH)))

        self._build_ui()

    # ---------- UI felépítés ----------
    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)

        content_layout = QHBoxLayout()
        main_layout.addLayout(content_layout)

        # --- Bal oldal: kategória-fa (kinyitható/becsukható csoportokkal) ---
        self.category_tree = QTreeWidget()
        self.category_tree.setHeaderHidden(True)
        self.category_tree.setFixedWidth(180)
        content_layout.addWidget(self.category_tree)

        # --- Jobb oldal: a kiválasztott kategóriának megfelelő tartalom ---
        self.pages = QStackedWidget()
        content_layout.addWidget(self.pages, stretch=1)

        # Kategóriák felépítése:
        #   Általános
        #   Megjelenés
        #       Nyelv
        #       Oldalsáv
        #   Feladatok
        general_item = self._add_top_category(
            tr("settings.category.general"), self._build_general_page()
        )
        appearance_item = self._add_top_category(
            tr("settings.category.appearance"), self._build_appearance_page()
        )
        self._add_child_category(
            appearance_item, tr("settings.category.language"), self._build_language_page()
        )
        self._add_child_category(
            appearance_item,
            tr("settings.category.sidebar_mode"),
            self._build_view_mode_page(),
        )
        self._add_top_category(tr("settings.category.tasks"), self._build_tasks_page())

        appearance_item.setExpanded(True)

        self.category_tree.currentItemChanged.connect(self._on_category_changed)
        self.category_tree.setCurrentItem(general_item)

        # --- Alsó gombsor ---
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

    def _add_top_category(self, name: str, page: QWidget) -> QTreeWidgetItem:
        item = QTreeWidgetItem([name])
        self.category_tree.addTopLevelItem(item)
        self.pages.addWidget(page)
        item.setData(0, Qt.ItemDataRole.UserRole, self.pages.count() - 1)
        return item

    def _add_child_category(
        self, parent_item: QTreeWidgetItem, name: str, page: QWidget
    ) -> QTreeWidgetItem:
        item = QTreeWidgetItem([name])
        parent_item.addChild(item)
        self.pages.addWidget(page)
        item.setData(0, Qt.ItemDataRole.UserRole, self.pages.count() - 1)
        return item

    def _on_category_changed(
        self, current: QTreeWidgetItem | None, _previous: QTreeWidgetItem | None
    ) -> None:
        if current is None:
            return
        idx = current.data(0, Qt.ItemDataRole.UserRole)
        if idx is not None:
            self.pages.setCurrentIndex(idx)

    # ---------- Egyes oldalak ----------
    def _build_general_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel(tr("settings.placeholder.general")))
        layout.addStretch()
        return page

    def _build_appearance_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel(tr("settings.placeholder.appearance")))
        layout.addStretch()
        return page

    def _build_language_page(self) -> QWidget:
        page = QWidget()
        layout = QFormLayout(page)

        self.language_combo = QComboBox()
        self.language_combo.addItem(tr("settings.language.hungarian"), userData="hu")
        self.language_combo.addItem(tr("settings.language.english"), userData="en")

        current_idx = self.language_combo.findData(get_language())
        if current_idx >= 0:
            self.language_combo.setCurrentIndex(current_idx)

        layout.addRow(tr("settings.language.label"), self.language_combo)
        return page

    def _build_view_mode_page(self) -> QWidget:
        page = QWidget()
        layout = QFormLayout(page)

        self.view_mode_combo = QComboBox()
        self.view_mode_combo.addItem(tr("settings.general.view_mode.dialog"), userData="dialog")
        self.view_mode_combo.addItem(tr("settings.general.view_mode.sidebar"), userData="sidebar")

        current_idx = self.view_mode_combo.findData(get_project_view_mode())
        if current_idx >= 0:
            self.view_mode_combo.setCurrentIndex(current_idx)

        layout.addRow(tr("settings.general.view_mode.label"), self.view_mode_combo)
        return page

    def _build_tasks_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel(tr("settings.placeholder.tasks")))
        layout.addStretch()
        return page

    # ---------- Mentés ----------
    def accept(self) -> None:
        selected_language = self.language_combo.currentData()
        selected_view_mode = self.view_mode_combo.currentData()

        data = load_settings()

        if selected_language:
            set_language(selected_language)
            data["language"] = selected_language

        if selected_view_mode:
            data["project_view_mode"] = selected_view_mode

        save_settings(data)

        super().accept()