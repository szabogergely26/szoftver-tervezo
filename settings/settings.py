"""Beállítások ablak – kategória-fa bal oldalt, tartalom jobb oldalt."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from PySide6.QtCore import Property, QPropertyAnimation, Qt
from PySide6.QtGui import QColor, QIcon, QPainter
from PySide6.QtWidgets import (
    QAbstractButton,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from config import ICON_PATH, SETTINGS_FILE

from .translations import get_language, set_language, tr


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


def get_close_to_tray() -> bool:
    """Igaz, ha bezáráskor az app a tálcára kicsinyítve fusson tovább (alapból igen)."""
    data = load_settings()
    value = data.get("close_to_tray")
    return value if isinstance(value, bool) else True


# (név, logging szint, szín) - ez a sorrend jelenik meg a legördülőkben
LOG_LEVELS = [
    ("DEBUG", logging.DEBUG, "#8a8a8a"),
    ("INFO", logging.INFO, "#3fa7ff"),
    ("WARNING", logging.WARNING, "#e0a020"),
    ("ERROR", logging.ERROR, "#e05050"),
    ("CRITICAL", logging.CRITICAL, "#ff2020"),
]


def get_log_level_name() -> str:
    """Visszaadja a mentett naplózási szint NEVÉT (pl. 'INFO'), alapból 'INFO'."""
    data = load_settings()
    name = data.get("log_level")
    valid_names = {n for n, _v, _c in LOG_LEVELS}
    return name if name in valid_names else "INFO"


def get_log_level() -> int:
    """Visszaadja a mentett naplózási szintet numerikusan (logging.DEBUG stb.)."""
    return logging.getLevelName(get_log_level_name())


class ToggleSwitch(QAbstractButton):
    """Klasszikus csúszka-kapcsoló (iOS/Android-stílusú): balra=ki (szürke),
    jobbra=be (zöld), animált gomb-csúszással.

    Checkable QAbstractButton — a checked állapot Qt-szinten is lekérdezhető
    (isChecked()), és a toggled(bool) szignál a szokásos módon jelez.
    """

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(48, 26)

        self._knob_position = 3.0  # a gomb bal széle, pixelben (animált érték)
        self._animation = QPropertyAnimation(self, b"knob_position", self)
        self._animation.setDuration(150)

        self.toggled.connect(self._on_toggled)

    def _on_toggled(self, checked: bool) -> None:
        end_value = self.width() - self.height() + 3.0 if checked else 3.0
        self._animation.stop()
        self._animation.setStartValue(self._knob_position)
        self._animation.setEndValue(end_value)
        self._animation.start()

    def get_knob_position(self) -> float:
        return self._knob_position

    def set_knob_position(self, value: float) -> None:
        self._knob_position = value
        self.update()

    knob_position = Property(float, get_knob_position, set_knob_position)

    def setChecked(self, checked: bool) -> None:
        # Kezdeti / kódból történő állítás esetén (nem felhasználói
        # kattintás) a gomb pozíciója animáció nélkül, azonnal ugorjon a
        # helyére - az animáció csak a toggled-jelzésen keresztüli,
        # felhasználó általi váltáskor fusson (lásd _on_toggled).
        super().setChecked(checked)
        self._knob_position = self.width() - self.height() + 3.0 if checked else 3.0
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        track_color = QColor("#2ecc71") if self.isChecked() else QColor("#c0c3c9")
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(track_color)
        painter.drawRoundedRect(
            0, 0, self.width(), self.height(), self.height() / 2, self.height() / 2
        )

        knob_diameter = self.height() - 6
        painter.setBrush(QColor("#ffffff"))
        painter.drawEllipse(int(self._knob_position), 3, knob_diameter, knob_diameter)

        painter.end()


# Az első profil neve, amikor a "Több profil" kapcsolót bekapcsolják -
# a felhasználó ezt később átnevezheti a ProjectDialog profil-váltó sávján.
DEFAULT_FIRST_PROFILE_NAME = "Alap"


class SettingsDialog(QDialog):
    """Az alkalmazás beállítás ablaka."""

    def __init__(
        self, parent: QWidget | None = None, *, projects_dir: Path | None = None
    ) -> None:
        super().__init__(parent)

        self.setWindowTitle(tr("settings.title"))
        self.setMinimumSize(600, 400)

        if ICON_PATH.exists():
            self.setWindowIcon(QIcon(str(ICON_PATH)))

        self._projects_dir = projects_dir

        # Projektenkénti "Több profil" kapcsoló-állapotok: Path -> bool.
        # A kezdeti (dialógus-nyitáskori) állapotot is eltároljuk, hogy az
        # accept()-ben csak azokra a projektekre hívjunk enable/disable-t,
        # amiknél a felhasználó ténylegesen váltott - a kapcsoló maga csak
        # a "Rendben" gombra hat, nem azonnal (lásd _on_project_toggle_changed
        # docstringje).
        self._project_toggles: dict[Path, ToggleSwitch] = {}
        self._project_initial_state: dict[Path, bool] = {}

        self._build_ui()

    # ---------- UI felépítés ----------
    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)

        content_layout = QHBoxLayout()
        main_layout.addLayout(content_layout)

        # --- Bal oldal: kategória-fa (kinyitható/becsukható csoportokkal) ---
        self.category_tree = QTreeWidget()
        self.category_tree.setObjectName("SettingsCategoryTree")
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
        #   Projektek
        #       <projekt1>
        #       <projekt2>
        #       ...
        general_item = self._add_top_category(
            tr("settings.category.general"), self._build_general_page()
        )
        appearance_item = self._add_top_category(
            tr("settings.category.appearance"), self._build_appearance_page()
        )
        self._add_child_category(
            appearance_item,
            tr("settings.category.language"),
            self._build_language_page(),
        )
        self._add_child_category(
            appearance_item,
            tr("settings.category.sidebar_mode"),
            self._build_view_mode_page(),
        )
        self._add_top_category(tr("settings.category.tasks"), self._build_tasks_page())

        projects_item = self._add_top_category(
            tr("settings.category.projects"), self._build_projects_overview_page()
        )
        self._build_project_child_categories(projects_item)

        appearance_item.setExpanded(True)

        self.category_tree.currentItemChanged.connect(self._on_category_changed)
        self.category_tree.setCurrentItem(general_item)

        # --- Alsó gombsor ---
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
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

        self.close_to_tray_checkbox = QCheckBox(tr("general.close_to_tray"))
        self.close_to_tray_checkbox.setChecked(get_close_to_tray())
        layout.addWidget(self.close_to_tray_checkbox)

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
        self.view_mode_combo.addItem(
            tr("settings.general.view_mode.dialog"), userData="dialog"
        )
        self.view_mode_combo.addItem(
            tr("settings.general.view_mode.sidebar"), userData="sidebar"
        )

        current_idx = self.view_mode_combo.findData(get_project_view_mode())
        if current_idx >= 0:
            self.view_mode_combo.setCurrentIndex(current_idx)

        layout.addRow(tr("settings.general.view_mode.label"), self.view_mode_combo)
        return page

    def _build_tasks_page(self) -> QWidget:
        # Késleltetett (lazy) import: a tervezo.core.storage a settings
        # csomagot importálja (models.py -> settings.translations), így egy
        # modul-szintű "from tervezo.core.storage import Storage" itt fenn
        # körkörös importot okozna. Metóduson belül importolva a hívás
        # időpontjában mindkét modul már teljesen be van töltve.
        from tervezo.core.storage import Storage

        page = QWidget()
        outer_layout = QVBoxLayout(page)

        outer_layout.addWidget(QLabel(tr("settings.tasks.template_tasks_label")))

        # Lista + jobb oldali gombsor - ez a "keret" a sablon-tételek
        # szerkesztéséhez. A self._template_tasks a memóriabeli munkapéldány,
        # csak a dialógus OK gombjára íródik ki a JSON fájlba.
        row_layout = QHBoxLayout()
        outer_layout.addLayout(row_layout, 1)

        self._storage = Storage()
        self._template_tasks: list[dict] = self._storage.read_template_tasks()

        self.template_tasks_list = QListWidget()
        for item in self._template_tasks:
            self.template_tasks_list.addItem(QListWidgetItem(item["title"]))
        row_layout.addWidget(self.template_tasks_list, 1)

        button_col = QVBoxLayout()
        add_btn = QPushButton(tr("settings.tasks.add_btn"))
        edit_btn = QPushButton(tr("settings.tasks.edit_btn"))
        remove_btn = QPushButton(tr("settings.tasks.remove_btn"))
        add_btn.clicked.connect(self._on_template_task_add)
        edit_btn.clicked.connect(self._on_template_task_edit)
        remove_btn.clicked.connect(self._on_template_task_remove)
        button_col.addWidget(add_btn)
        button_col.addWidget(edit_btn)
        button_col.addWidget(remove_btn)
        button_col.addStretch(1)
        row_layout.addLayout(button_col)

        return page

    # ---------- Feladatok lap: sablon-tételek szerkesztése ----------
    def _next_template_task_id(self) -> str:
        """Új, egyedi 'custom_N' azonosító a kézzel felvett tételeknek."""
        existing_ids = {item["id"] for item in self._template_tasks}
        n = 1
        while f"custom_{n}" in existing_ids:
            n += 1
        return f"custom_{n}"

    def _on_template_task_add(self) -> None:
        title, ok = QInputDialog.getText(
            self, tr("settings.tasks.add_btn"), tr("settings.tasks.title_prompt")
        )
        title = title.strip()
        if not ok or not title:
            return

        self._template_tasks.append(
            {"id": self._next_template_task_id(), "title": title}
        )
        self.template_tasks_list.addItem(QListWidgetItem(title))

    def _on_template_task_edit(self) -> None:
        row = self.template_tasks_list.currentRow()
        if row < 0:
            return

        current_title = self._template_tasks[row]["title"]
        title, ok = QInputDialog.getText(
            self,
            tr("settings.tasks.edit_btn"),
            tr("settings.tasks.title_prompt"),
            text=current_title,
        )
        title = title.strip()
        if not ok or not title:
            return

        self._template_tasks[row]["title"] = title
        self.template_tasks_list.item(row).setText(title)

    def _on_template_task_remove(self) -> None:
        row = self.template_tasks_list.currentRow()
        if row < 0:
            return

        confirm = QMessageBox.question(
            self,
            tr("settings.tasks.remove_btn"),
            tr(
                "settings.tasks.remove_confirm",
                title=self._template_tasks[row]["title"],
            ),
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return

        del self._template_tasks[row]
        self.template_tasks_list.takeItem(row)

    # ---------- Projektek lap ----------
    def _build_projects_overview_page(self) -> QWidget:
        """A "Projektek" felső kategória saját lapja - egyelőre csak egy
        rövid tájékoztató szöveg; a tényleges beállítások projektenként,
        a gyerek-kategóriákon (lásd _build_project_child_categories)."""
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(QLabel(tr("settings.projects.overview_label")))
        layout.addStretch()
        return page

    def _build_project_child_categories(self, parent_item: QTreeWidgetItem) -> None:
        """Minden projekthez egy gyerek-kategória + saját beállítás-lap.

        Ha projects_dir nem lett átadva (pl. teszt-környezet), a fa üres
        marad ezen a ponton - ez nem hiba, csak semmi nem listázódik.
        """
        if self._projects_dir is None or not self._projects_dir.exists():
            return

        from tervezo.core.storage import Storage

        storage = Storage()
        for project_dir in storage.list_projects(self._projects_dir):
            project = storage.read_project(project_dir)
            self._add_child_category(
                parent_item,
                project.name,
                self._build_project_settings_page(project_dir),
            )

    def _build_project_settings_page(self, project_dir: Path) -> QWidget:
        """Egy adott projekt beállítás-lapja: jelenleg a "Több profil"
        kapcsoló. Később ide kerülhetnek további, projektenkénti
        beállítások is.
        """
        from tervezo.core.storage import Storage

        storage = Storage()
        project = storage.read_project(project_dir)

        page = QWidget()
        layout = QFormLayout(page)

        toggle = ToggleSwitch()
        toggle.setChecked(project.profiles_enabled)
        self._project_toggles[project_dir] = toggle
        self._project_initial_state[project_dir] = project.profiles_enabled

        layout.addRow(tr("settings.projects.multi_profile_label"), toggle)

        return page

    # ---------- Mentés ----------
    def _apply_project_toggle_changes(self) -> bool:
        """A projektenkénti "Több profil" kapcsolók végleges alkalmazása.

        Csak azokra a projektekre hívunk enable_profiles/disable_profiles-t,
        amiknél a dialógus megnyitása óta ténylegesen változott a kapcsoló
        állása - a kapcsoló maga csak vizuális, egészen a "Rendben" gombig.

        Kikapcsoláskor, ha a projektnek több aktív profilja is van, meg
        kell kérdezni, melyiket tartsa meg - ha a felhasználó ezt a
        kérdést Mégse-vel zárja le, az egész accept() megszakad (False-t
        adunk vissza), hogy a dialógus nyitva maradjon, és a kapcsoló ne
        vesszen el állapotában.
        """
        from tervezo.core.storage import Storage

        storage = Storage()

        for project_dir, toggle in self._project_toggles.items():
            was_enabled = self._project_initial_state[project_dir]
            is_enabled = toggle.isChecked()

            if was_enabled == is_enabled:
                continue

            if is_enabled:
                storage.enable_profiles(project_dir, DEFAULT_FIRST_PROFILE_NAME)
            else:
                active_names = storage.list_active_profile_names(project_dir)
                if len(active_names) <= 1:
                    keep_name = (
                        active_names[0]
                        if active_names
                        else (DEFAULT_FIRST_PROFILE_NAME)
                    )
                else:
                    confirm = QMessageBox.question(
                        self,
                        tr("settings.projects.disable_multi_warning_title"),
                        tr(
                            "settings.projects.disable_multi_warning_text",
                            name=project_dir.name,
                        ),
                    )
                    if confirm != QMessageBox.StandardButton.Yes:
                        return False

                    keep_name, ok = QInputDialog.getItem(
                        self,
                        tr("settings.projects.disable_pick_title"),
                        tr(
                            "settings.projects.disable_pick_label",
                            name=project_dir.name,
                        ),
                        active_names,
                        0,
                        editable=False,
                    )
                    if not ok:
                        return False

                storage.disable_profiles(project_dir, keep_profile_name=keep_name)

        return True

    def accept(self) -> None:
        if not self._apply_project_toggle_changes():
            return

        selected_language = self.language_combo.currentData()
        selected_view_mode = self.view_mode_combo.currentData()

        data = load_settings()

        if selected_language:
            set_language(selected_language)
            data["language"] = selected_language

        if selected_view_mode:
            data["project_view_mode"] = selected_view_mode

        data["close_to_tray"] = self.close_to_tray_checkbox.isChecked()

        self._storage.write_template_tasks(self._template_tasks)

        save_settings(data)

        super().accept()
