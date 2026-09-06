from __future__ import annotations

from datetime import date
from pathlib import Path

from PySide6.QtCore import QSize, Qt, QTimer, Signal
from PySide6.QtGui import (
    QAction,
    QBrush,
    QColor,
    QIcon,
    QPainter,
    QPixmap,
    QTextCharFormat,
)
from PySide6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMenu,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QToolBar,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from settings.translations import tr

from ..core.documents import get_document_icon
from ..core.models import Milestone, Project, ProjectStatus, TaskItem

CARD_WIDTH = 200
CARD_HEIGHT = 220
PHOTO_HEIGHT = 100


class ProjectCard(QFrame):
    """Egy projekt-kártya a főablak rácsában. Kattintásra jelzi a projekt útvonalát."""

    clicked = Signal(object)  # Path

    def __init__(self, project: Project, parent: QWidget | None = None):
        super().__init__(parent)
        self.project = project

        self.setFixedSize(CARD_WIDTH, CARD_HEIGHT)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setObjectName("ProjectCard")
        self.setStyleSheet(
            "#ProjectCard {"
            "  background-color: #ffffff;"
            "  border: 1px solid #d0d3d9;"
            "  border-radius: 8px;"
            "}"
            "#ProjectCard:hover {"
            "  border-color: #3b82f6;"
            "}"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        self.photo_label = QLabel()
        self.photo_label.setFixedHeight(PHOTO_HEIGHT)
        self.photo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.photo_label.setStyleSheet(
            "background-color: rgba(127,127,127,40); border-radius: 4px;"
        )
        self.photo_label.setText("📁")
        self.photo_label.setStyleSheet(
            self.photo_label.styleSheet() + "font-size: 32px;"
        )
        layout.addWidget(self.photo_label)

        # A borítókép betöltését (fájl-IO + dekódolás) a widget felépítése
        # UTÁN, a következő eseményhurok-ciklusban végezzük el
        # (singleShot(0, ...)): ha ez szinkron történik a kártya
        # létrehozásakor - még mielőtt a kártya a szülő elrendezésbe
        # kerülne és Qt lezárná a widget-hierarchia felépítését -, az
        # ugyanabba a natív dangling-widget hibaosztályba tartozhat, mint
        # amit a fájlválasztónál tapasztaltunk.
        QTimer.singleShot(0, self._load_cover_photo)

        header = QHBoxLayout()
        name_label = QLabel(project.name)
        name_label.setStyleSheet("font-weight: bold;")
        name_label.setWordWrap(True)

        status_dot = QLabel()
        status_dot.setFixedSize(14, 14)
        status_dot.setStyleSheet(
            f"background-color: {project.status.color}; border-radius: 7px;"
        )
        status_dot.setToolTip(project.status.label)

        header.addWidget(name_label, 1)
        header.addWidget(status_dot, 0, Qt.AlignmentFlag.AlignTop)
        layout.addLayout(header)

        desc_text = project.description or project.purpose
        desc_label = QLabel(desc_text)
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("font-size: 11px;")
        layout.addWidget(desc_label, 1)

    def _load_cover_photo(self) -> None:
        pixmap: QPixmap | None = None
        if self.project.photo_path and self.project.photo_path.exists():
            candidate = QPixmap(str(self.project.photo_path))
            if not candidate.isNull():
                pixmap = candidate

        if pixmap is not None:
            self.photo_label.setStyleSheet(
                "background-color: rgba(127,127,127,40); border-radius: 4px;"
            )
            self.photo_label.setText("")
            self.photo_label.setPixmap(
                pixmap.scaledToHeight(
                    PHOTO_HEIGHT, Qt.TransformationMode.SmoothTransformation
                )
            )

    def mousePressEvent(self, event) -> None:
        # FONTOS: a super() hívás előrébb van, mint az emit — ha a kattintás
        # egy modális dialógust nyit meg, ami közben (pl. Mentésre) törli ezt
        # a kártyát (reload_cards -> deleteLater), akkor a dialógus bezárása
        # után NEM szabad semmit hívni ezen a (már törölt) self-en. Az emit
        # ezért az utolsó dolog, amit a metódus csinál.
        super().mousePressEvent(event)
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.project.path)


class ProfileSwitcherBar(QWidget):
    """Profil-váltó sáv a ProjectDialog tab-sávja felett.

    Minden profilhoz egy sima (nem checkable) gomb: név + bal-szegély
    színnel jelzett státusz. Az "aktív" jelzést MI magunk rajzoljuk a
    stíluson keresztül (nem a Qt beépített checkable-mechanizmusán, ami
    kattintásonként automatikusan billegteti a checked-állapotot, és ez
    kiszámíthatatlan lett két gomb között váltogatva). Plusz egy "+" gomb
    a végén (jelenleg inaktív — új profil létrehozása egy későbbi
    lépésben kerül bele).
    """

    profile_selected = Signal(str)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._buttons: dict[str, QPushButton] = {}
        self._names: list[str] = []
        self._active: str | None = None

        self.layout_ = QHBoxLayout(self)
        self.layout_.setContentsMargins(0, 0, 0, 4)
        self.layout_.setSpacing(4)

        self.add_profile_btn = QPushButton("+")
        self.add_profile_btn.setFixedWidth(28)
        self.add_profile_btn.setEnabled(False)
        self.add_profile_btn.setToolTip(tr("project.profile.add_coming_soon"))

        self.layout_.addWidget(self.add_profile_btn)
        self.layout_.addStretch(1)

    def set_profiles(
        self,
        names: list[str],
        statuses: dict[str, ProjectStatus],
        active: str | None,
    ) -> None:
        """A sáv frissítése az aktuális profil-listából.

        Ha a névhalmaz nem változott az előző hívás óta, nem építjük
        újra a gombokat — csak az aktív-jelzést és a szín-jelzést
        frissítjük a meglévőkön.
        """
        if names == self._names:
            self._refresh_button_states(statuses, active)
            return

        while self.layout_.count():
            item = self.layout_.takeAt(0)
            widget = item.widget()
            if widget is not None and widget is not self.add_profile_btn:
                widget.deleteLater()

        self._buttons.clear()
        self._names = list(names)

        for name in names:
            btn = QPushButton(name)
            btn.clicked.connect(lambda _checked, n=name: self._on_button_clicked(n))
            self.layout_.addWidget(btn)
            self._buttons[name] = btn

        self.layout_.addWidget(self.add_profile_btn)
        self.layout_.addStretch(1)

        self._refresh_button_states(statuses, active)

    def _refresh_button_states(
        self, statuses: dict[str, ProjectStatus], active: str | None
    ) -> None:
        """A meglévő gombok aktív-jelzésének és szín-jelzésének frissítése."""

        self._active = active
        for name, btn in self._buttons.items():
            status = statuses.get(name)
            border_color = status.color if status is not None else "#d0d3d9"

            if name == active:
                btn.setStyleSheet(
                    f"QPushButton {{ border-left: 4px solid {border_color}; "
                    f"padding: 4px 10px; background-color: #3b82f6; "
                    f"color: white; font-weight: bold; }}"
                )
            else:
                btn.setStyleSheet(
                    f"QPushButton {{ border-left: 4px solid {border_color}; "
                    f"padding: 4px 10px; }}"
                )

    def _on_button_clicked(self, name: str) -> None:
        if name == self._active:
            return
        self.profile_selected.emit(name)


class TaskRowWidget(QWidget):
    """Egy feladat-sor: pipa/gomb + gazdag-szöveges (HTML) tartalom + szerkesztés/törlés."""

    start_requested = Signal(int)
    toggled = Signal(int, bool)
    edit_requested = Signal(int)
    details_requested = Signal(int)
    delete_requested = Signal(int)
    move_requested = Signal(int, int)  # (task_id, irány: -1 = fel, +1 = le)

    def __init__(
        self,
        task: TaskItem,
        mode: str = "pending",
        parent: QWidget | None = None,
        index: int | None = None,
        is_first: bool = False,
        is_last: bool = False,
    ):
        super().__init__(parent)
        self.task_id = task.id
        self._mode = mode

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)

        if mode == "pending":
            if index is not None:
                number_label = QLabel(f"{index}.")
                number_label.setFixedWidth(24)
                layout.addWidget(number_label)

            move_up_btn = QPushButton("▲")
            move_up_btn.setFixedWidth(28)
            move_up_btn.setEnabled(not is_first)
            move_up_btn.clicked.connect(
                lambda: self.move_requested.emit(self.task_id, -1)
            )
            layout.addWidget(move_up_btn)

            move_down_btn = QPushButton("▼")
            move_down_btn.setFixedWidth(28)
            move_down_btn.setEnabled(not is_last)
            move_down_btn.clicked.connect(
                lambda: self.move_requested.emit(self.task_id, 1)
            )
            layout.addWidget(move_down_btn)

            start_btn = QPushButton(tr("project.task.start"))
            start_btn.clicked.connect(lambda: self.start_requested.emit(self.task_id))
            layout.addWidget(start_btn)

        elif mode == "in_progress":
            self.checkbox = QCheckBox()
            self.checkbox.setChecked(False)
            self.checkbox.toggled.connect(
                lambda checked: self.toggled.emit(self.task_id, checked)
            )
            layout.addWidget(self.checkbox)

        else:
            # mode == "done"
            done_label = QLabel(f"✅ {task.completed_at or ''}")
            done_label.setStyleSheet("color: #2e7d32; font-weight: bold;")
            layout.addWidget(done_label)

        self.label = QLabel()
        self.label.setText(task.title)
        self.label.setWordWrap(True)
        layout.addWidget(self.label, 1)

        if mode != "done":
            details_btn = QPushButton(tr("common.details"))
            details_btn.clicked.connect(lambda: self.edit_requested.emit(self.task_id))
            layout.addWidget(details_btn)

            delete_btn = QPushButton(tr("common.delete"))
            delete_btn.clicked.connect(lambda: self.delete_requested.emit(self.task_id))
            layout.addWidget(delete_btn)
        else:
            details_btn = QPushButton(tr("common.details"))
            details_btn.clicked.connect(
                lambda: self.details_requested.emit(self.task_id)
            )
            layout.addWidget(details_btn)

    def set_html(self, html: str) -> None:
        self.label.setText(html)

    def mouseDoubleClickEvent(self, event) -> None:
        # A sorra (vagy a title-szövegre) duplán kattintva ugyanaz nyílik meg,
        # mint a Részletek gombra kattintva - kényelmi gyorsút a gomb mellett.
        if self._mode == "done":
            self.details_requested.emit(self.task_id)
        else:
            self.edit_requested.emit(self.task_id)
        super().mouseDoubleClickEvent(event)


class DocumentRowWidget(QWidget):
    """Egy dokumentum-sor a Dokumentumok tabon: típus-ikon + fájlnév + gombok.

    A show_extension paraméter/set_show_extension() csak a MEGJELENÍTETT
    szöveget érinti (pl. "readme.md" -> "readme") - a self.filename mindig
    a teljes, tényleges fájlnév marad, ezt küldik a jelzések is.
    """

    open_requested = Signal(str)
    rename_requested = Signal(str)
    delete_requested = Signal(str)

    def __init__(
        self, filename: str, parent: QWidget | None = None, show_extension: bool = True
    ):
        super().__init__(parent)
        self.filename = filename

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)

        icon_label = QLabel()
        icon_label.setPixmap(get_document_icon(filename).pixmap(20, 20))
        icon_label.setFixedWidth(28)
        layout.addWidget(icon_label)

        self.name_label = QLabel()
        self.name_label.setWordWrap(True)
        layout.addWidget(self.name_label, 1)
        self.set_show_extension(show_extension)

        open_btn = QPushButton(tr("widgets.document_open"))
        open_btn.clicked.connect(lambda: self.open_requested.emit(self.filename))
        layout.addWidget(open_btn)

        rename_btn = QPushButton(tr("widgets.document_rename"))
        rename_btn.clicked.connect(lambda: self.rename_requested.emit(self.filename))
        layout.addWidget(rename_btn)

        delete_btn = QPushButton(tr("common.delete"))
        delete_btn.clicked.connect(lambda: self.delete_requested.emit(self.filename))
        layout.addWidget(delete_btn)

    def set_show_extension(self, show_extension: bool) -> None:
        """A megjelenített szöveget frissíti - a self.filename nem változik."""
        if show_extension:
            self.name_label.setText(self.filename)
        else:
            self.name_label.setText(Path(self.filename).stem)


class DocumentRenameDialog(QDialog):
    """Dokumentum átnevezése: külön mező a névnek és a kiterjesztésnek.

    A kiterjesztés így nem törölhető véletlenül (ami elrontaná a beépített
    .md/.txt előnézet felismerését) - a Kiterjesztés mező is szerkeszthető
    marad, de jól elkülönül a névtől, tehát szándékos döntés kell hozzá.

    A "Kiterjesztés megjelenítése" checkbox állapota megosztott a
    Dokumentumok tab listájával: a kezdőértékét a hívó adja át
    (show_extension), a dialógus lezárása után pedig new_show_extension()
    adja vissza a (esetleg módosított) állapotot - ezt a hívó elmenti, és
    a lista összes sorára alkalmazza. Mégse esetén a checkbox-módosítás
    is elvész, csak Elfogadáskor válik véglegessé.
    """

    def __init__(
        self,
        filename: str,
        parent: QWidget | None = None,
        *,
        show_extension: bool = True,
    ):
        super().__init__(parent)
        self.setWindowTitle(tr("project.document.rename_title"))

        path = Path(filename)
        stem = path.stem
        suffix = path.suffix  # a pontot is tartalmazza, pl. ".md"; lehet üres

        layout = QFormLayout(self)

        self.name_edit = QLineEdit(stem)
        self.name_edit.selectAll()
        layout.addRow(tr("project.document.rename_name_label"), self.name_edit)

        self.suffix_edit = QLineEdit(suffix)
        self.suffix_edit.setPlaceholderText(tr("project.document.rename_no_extension"))
        self._suffix_row_label = tr("project.document.rename_extension_label")
        layout.addRow(self._suffix_row_label, self.suffix_edit)

        self.show_suffix_checkbox = QCheckBox(
            tr("project.document.rename_show_extension")
        )
        self.show_suffix_checkbox.setChecked(show_extension)
        self.show_suffix_checkbox.toggled.connect(self._on_show_suffix_toggled)
        layout.addRow("", self.show_suffix_checkbox)
        self._on_show_suffix_toggled(show_extension)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        self._result_name = ""
        self._result_show_extension = show_extension

    def _on_show_suffix_toggled(self, checked: bool) -> None:
        form: QFormLayout = self.layout()
        form.setRowVisible(self.suffix_edit, checked)

    def _on_accept(self) -> None:
        name = self.name_edit.text().strip()
        if not name:
            self.name_edit.setFocus()
            return
        suffix = self.suffix_edit.text().strip()
        if suffix and not suffix.startswith("."):
            suffix = f".{suffix}"
        self._result_name = f"{name}{suffix}"
        self._result_show_extension = self.show_suffix_checkbox.isChecked()
        self.accept()

    def new_filename(self) -> str:
        return self._result_name

    def new_show_extension(self) -> bool:
        """A checkbox végállapota - csak Elfogadás után érvényes és végleges."""
        return self._result_show_extension


class DocumentConflictDialog(QDialog):
    """Ütközés-feloldó dialógus: 'X már létezik, felülírjam vagy más néven mentsem?'

    Felülírás / Új név gombokkal (a Mégse a QDialog alap Escape-jén megy).
    """

    def __init__(self, filename: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle(tr("widgets.document_conflict_title"))

        layout = QVBoxLayout(self)

        message = QLabel(tr("widgets.document_conflict_text", name=filename))
        message.setWordWrap(True)
        layout.addWidget(message)

        button_row = QHBoxLayout()
        self.overwrite_btn = QPushButton(tr("widgets.document_overwrite"))
        self.overwrite_btn.clicked.connect(self._on_overwrite)
        button_row.addWidget(self.overwrite_btn)

        self.new_name_btn = QPushButton(tr("widgets.document_new_name"))
        self.new_name_btn.clicked.connect(self._on_new_name)
        button_row.addWidget(self.new_name_btn)

        cancel_btn = QPushButton(tr("common.cancel"))
        cancel_btn.clicked.connect(self.reject)
        button_row.addWidget(cancel_btn)

        layout.addLayout(button_row)

        self._choice: str | None = None

    def _on_overwrite(self) -> None:
        self._choice = "overwrite"
        self.accept()

    def _on_new_name(self) -> None:
        self._choice = "new_name"
        self.accept()

    def choice(self) -> str | None:
        """'overwrite', 'new_name', vagy None (Mégse/Escape esetén)."""
        return self._choice


class ProjectPickerDialog(QDialog):
    """Projekt-választó lista, pl. a Fájl menüből induló műveletekhez,
    amikor a felhasználó nem egy már nyitott projekt kontextusából indul.
    """

    def __init__(self, projects: list[Project], parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle(tr("widgets.project_picker_title"))
        self.resize(360, 420)

        layout = QVBoxLayout(self)

        self.list_widget = QListWidget()
        for project in projects:
            item = QListWidgetItem(project.name)
            item.setData(Qt.ItemDataRole.UserRole, project.path)
            self.list_widget.addItem(item)
        self.list_widget.itemDoubleClicked.connect(lambda _item: self.accept())
        layout.addWidget(self.list_widget, 1)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        if self.list_widget.count() > 0:
            self.list_widget.setCurrentRow(0)

    def _on_accept(self) -> None:
        if self.list_widget.currentItem() is None:
            return
        self.accept()

    def selected_project_path(self):
        item = self.list_widget.currentItem()
        if item is None:
            return None
        return item.data(Qt.ItemDataRole.UserRole)


class MilestoneDialog(QDialog):
    """Mérföldkő felvétele / szerkesztése (dátum, cím, rövid leírás)."""

    def __init__(
        self, parent: QWidget | None = None, milestone: Milestone | None = None
    ):
        super().__init__(parent)
        self.setWindowTitle(tr("widgets.milestone_title"))

        layout = QFormLayout(self)

        default_date = (
            milestone.date if milestone else date.today().strftime("%Y.%m.%d")  # noqa: DTZ011 (helyi naptári dátum kell, nem UTC)
        )
        self.date_edit = QLineEdit(default_date)
        self.date_edit.setPlaceholderText(tr("common.date_placeholder"))
        layout.addRow(tr("widgets.milestone_date_label"), self.date_edit)

        self.title_edit = QLineEdit(milestone.title if milestone else "")
        layout.addRow(tr("widgets.milestone_name_label"), self.title_edit)

        self.desc_edit = QPlainTextEdit(milestone.description if milestone else "")
        self.desc_edit.setFixedHeight(80)
        layout.addRow(tr("widgets.milestone_description_label"), self.desc_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_milestone(self) -> Milestone | None:
        title = self.title_edit.text().strip()
        if not title:
            return None
        return Milestone(
            date=self.date_edit.text().strip(),
            title=title,
            description=self.desc_edit.toPlainText().strip(),
        )


class TaskEditDialog(QDialog):
    """Egy feladat gazdag-szöveges (HTML) tartalmának szerkesztése."""

    def __init__(self, parent: QWidget | None = None, title: str = "", html: str = ""):
        super().__init__(parent)
        self.setWindowTitle(tr("widgets.task_edit_title"))
        self.resize(420, 320)

        layout = QVBoxLayout(self)

        form = QFormLayout()
        self.title_edit = QLineEdit(title)
        form.addRow(tr("widgets.task_title_label"), self.title_edit)
        layout.addLayout(form)

        self.editor = QTextEdit()
        self.editor.setHtml(html)

        toolbar = build_richtext_toolbar(self.editor, self)
        layout.addWidget(toolbar)
        layout.addWidget(self.editor, 1)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_accept(self) -> None:
        if not self.title_edit.text().strip():
            self.title_edit.setFocus()
            return
        self.accept()

    def get_title(self) -> str:
        return self.title_edit.text().strip()

    def get_html(self) -> str:
        return self.editor.toHtml()


class TaskDetailsDialog(QDialog):
    """Egy elkészült feladat tartalmának csak-olvasható megtekintése.

    A TaskEditDialog szerkeszthető változatával szemben ez a dialógus nem
    engedi módosítani a szöveget - elkészült feladatoknál a cél a részletek
    megtekintése, nem az utólagos átírás.
    """

    def __init__(self, parent: QWidget | None = None, title: str = "", html: str = ""):
        super().__init__(parent)
        self.setWindowTitle(title or tr("widgets.task_details_title"))
        self.resize(420, 320)

        layout = QVBoxLayout(self)

        viewer = QTextEdit()
        viewer.setHtml(html)
        viewer.setReadOnly(True)
        layout.addWidget(viewer, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)


def _text_icon(
    letter: str,
    *,
    bold: bool = False,
    italic: bool = False,
    underline: bool = False,
    size: int = 22,
) -> QIcon:
    """Egyszerű betű-ikon (B / I / U), hogy az akció ikon+felirat stílusban is jól nézzen ki."""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    font = painter.font()
    font.setPointSize(int(size * 1.0))  # ikonméret az eszköztáron
    font.setBold(bold)
    font.setItalic(italic)
    font.setUnderline(underline)
    painter.setFont(font)
    painter.setPen(QColor("#333333"))
    painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, letter)
    painter.end()
    return QIcon(pixmap)


def _color_swatch_icon(color: QColor, size: int = 14) -> QIcon:
    """Kis, kerekített négyzet ikon, ami az aktuális kiemelés-/betűszínt mutatja."""
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(color)
    painter.setPen(QColor("#555555"))
    painter.drawRoundedRect(1, 1, size - 2, size - 2, 3, 3)
    painter.end()
    return QIcon(pixmap)


def build_richtext_toolbar(target: QTextEdit, parent: QWidget) -> QToolBar:
    """Formázó eszköztár: félkövér, dőlt, aláhúzott, kiemelés, betűszín, betűméret.

    A Kiemelés és a Betűszín gomb:
      - színválasztóval bír (nem fix szín),
      - benyomott állapotban jelzi, ha a kurzor pozíciójánál aktív a formázás,
      - egy kis színes négyzettel mutatja, melyik szín van beállítva/aktív.
    """
    tb = QToolBar(parent)
    tb.setMovable(False)
    tb.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
    tb.setIconSize(QSize(18, 18))
    tb.setStyleSheet(
        "QToolBar { spacing: 2px; }QToolButton { padding: 1px 3px; font-size: 10px; }"
    )

    state = {
        "highlight_color": QColor("#ffff66"),
        "text_color": QColor("#e74c3c"),
    }

    def set_char_format(
        *,
        bold: bool | None = None,
        italic: bool | None = None,
        underline: bool | None = None,
        color: QColor | None = None,
        background: QColor | QBrush | None = None,
        point_size: int | None = None,
    ) -> None:
        fmt = QTextCharFormat()
        if bold is not None:
            fmt.setFontWeight(700 if bold else 400)
        if italic is not None:
            fmt.setFontItalic(italic)
        if underline is not None:
            fmt.setFontUnderline(underline)
        if color is not None:
            fmt.setForeground(color)
        if background is not None:
            fmt.setBackground(background)
        if point_size is not None:
            fmt.setFontPointSize(point_size)

        cursor = target.textCursor()
        if cursor.hasSelection():
            cursor.mergeCharFormat(fmt)
        target.mergeCurrentCharFormat(fmt)

    act_bold = QAction(_text_icon("B", bold=True), tr("toolbar.bold"), parent)
    act_bold.setCheckable(True)
    act_bold.triggered.connect(lambda checked: set_char_format(bold=checked))
    tb.addAction(act_bold)

    act_italic = QAction(_text_icon("I", italic=True), tr("toolbar.italic"), parent)
    act_italic.setCheckable(True)
    act_italic.triggered.connect(lambda checked: set_char_format(italic=checked))
    tb.addAction(act_italic)

    act_underline = QAction(
        _text_icon("U", underline=True), tr("toolbar.underline"), parent
    )
    act_underline.setCheckable(True)
    act_underline.triggered.connect(lambda checked: set_char_format(underline=checked))
    tb.addAction(act_underline)

    tb.addSeparator()

    # --- Kiemelés (klasszikus minta: szín-négyzet gomb + legördülő nyíl) ---
    highlight_btn = QToolButton(parent)
    highlight_btn.setCheckable(True)
    highlight_btn.setText(tr("toolbar.highlight"))
    highlight_btn.setToolTip(tr("toolbar.highlight"))
    highlight_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
    highlight_btn.setIconSize(QSize(20, 20))
    highlight_btn.setIcon(_color_swatch_icon(state["highlight_color"], size=20))
    highlight_btn.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)

    def pick_highlight_color() -> None:
        color = QColorDialog.getColor(state["highlight_color"], parent)
        if not color.isValid():
            return
        state["highlight_color"] = color
        highlight_btn.setIcon(_color_swatch_icon(color, size=20))
        highlight_btn.setChecked(True)
        set_char_format(background=color)

    highlight_menu = QMenu(highlight_btn)
    act_pick_highlight = QAction(tr("common.custom_color_ellipsis"), parent)
    act_pick_highlight.triggered.connect(pick_highlight_color)
    highlight_menu.addAction(act_pick_highlight)
    highlight_btn.setMenu(highlight_menu)

    def toggle_highlight(checked: bool) -> None:
        if checked:
            set_char_format(background=state["highlight_color"])
        else:
            set_char_format(background=QBrush(Qt.BrushStyle.NoBrush))

    highlight_btn.toggled.connect(toggle_highlight)
    tb.addWidget(highlight_btn)

    tb.addSeparator()

    # --- Betűszín (ugyanez a minta) ---
    color_btn = QToolButton(parent)
    color_btn.setCheckable(True)
    color_btn.setText(tr("toolbar.text_color"))
    color_btn.setToolTip(tr("toolbar.text_color"))
    color_btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
    color_btn.setIconSize(QSize(20, 20))
    color_btn.setIcon(_color_swatch_icon(state["text_color"], size=20))
    color_btn.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)

    def pick_text_color() -> None:
        color = QColorDialog.getColor(state["text_color"], parent)
        if not color.isValid():
            return
        state["text_color"] = color
        color_btn.setIcon(_color_swatch_icon(color, size=20))
        color_btn.setChecked(True)
        set_char_format(color=color)

    color_menu = QMenu(color_btn)
    act_pick_color = QAction(tr("common.custom_color_ellipsis"), parent)
    act_pick_color.triggered.connect(pick_text_color)
    color_menu.addAction(act_pick_color)
    color_btn.setMenu(color_menu)

    def apply_text_color(checked: bool) -> None:
        # a betűszínnek nincs "kikapcsolt" állapota — a gomb testére kattintva
        # mindig az utoljára használt/kiválasztott színt alkalmazzuk újra
        set_char_format(color=state["text_color"])

    color_btn.clicked.connect(apply_text_color)
    tb.addWidget(color_btn)

    tb.addSeparator()

    size_box = QSpinBox(parent)
    size_box.setRange(6, 48)
    size_box.setValue(11)
    size_box.setSuffix(" pt")
    size_box.setFixedHeight(40)  # Részletek ablak eszköztár magassága

    # méretek: padding
    # padding 2. érték - betüméret doboza, font-size: betümérete
    size_box.setStyleSheet("padding: 0px 10px; font-size: 13px;")
    size_box.setFixedWidth(70)  # ne nyúljon szét vízszintesen
    size_box.valueChanged.connect(lambda value: set_char_format(point_size=value))

    size_container = QWidget(parent)
    size_layout = QVBoxLayout(size_container)
    size_layout.setContentsMargins(8, 8, 8, 8)
    size_layout.setSpacing(2)
    size_layout.addWidget(size_box)
    size_caption = QLabel(tr("toolbar.font_size"))
    size_caption.setAlignment(Qt.AlignmentFlag.AlignCenter)
    size_caption.setStyleSheet("font-size: 10px;")
    size_layout.addWidget(size_caption)
    tb.addWidget(size_container)

    # --- Gombállapotok frissítése a kurzor pozíciója / formázás szerint ---
    def refresh_buttons(fmt: QTextCharFormat) -> None:
        for widget in (act_bold, act_italic, act_underline, highlight_btn, color_btn):
            widget.blockSignals(True)

        act_bold.setChecked(fmt.fontWeight() > 500)
        act_italic.setChecked(fmt.fontItalic())
        act_underline.setChecked(fmt.fontUnderline())

        bg = fmt.background()
        has_highlight = bg.style() != Qt.BrushStyle.NoBrush and bg.color().alpha() > 0
        highlight_btn.setChecked(has_highlight)
        if has_highlight:
            state["highlight_color"] = bg.color()
            highlight_btn.setIcon(_color_swatch_icon(bg.color(), size=20))
        else:
            highlight_btn.setIcon(_color_swatch_icon(state["highlight_color"], size=20))

        fg = fmt.foreground()
        default_color = target.palette().color(target.foregroundRole())
        has_custom_color = (
            fg.style() != Qt.BrushStyle.NoBrush and fg.color() != default_color
        )
        color_btn.setChecked(has_custom_color)
        if has_custom_color:
            state["text_color"] = fg.color()
            color_btn.setIcon(_color_swatch_icon(fg.color(), size=20))
        else:
            color_btn.setIcon(_color_swatch_icon(state["text_color"], size=20))

        for widget in (act_bold, act_italic, act_underline, highlight_btn, color_btn):
            widget.blockSignals(False)

    target.currentCharFormatChanged.connect(refresh_buttons)
    refresh_buttons(target.currentCharFormat())

    return tb
