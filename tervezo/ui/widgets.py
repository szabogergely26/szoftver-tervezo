from __future__ import annotations

from datetime import date

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QAction, QBrush, QColor, QIcon, QPainter, QPixmap, QTextCharFormat
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

from ..core.models import Milestone, Project, TaskItem
from settings.translations import tr

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
        self.setStyleSheet("#ProjectCard { border: 1px solid #ccc; }")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        photo_label = QLabel()
        photo_label.setFixedHeight(PHOTO_HEIGHT)
        photo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        photo_label.setStyleSheet(
            "background-color: rgba(127,127,127,40); border-radius: 4px;"
        )

        pixmap: QPixmap | None = None
        if project.photo_path and project.photo_path.exists():
            candidate = QPixmap(str(project.photo_path))
            if not candidate.isNull():
                pixmap = candidate

        if pixmap is not None:
            photo_label.setPixmap(
                pixmap.scaledToHeight(
                    PHOTO_HEIGHT, Qt.TransformationMode.SmoothTransformation
                )
            )
        else:
            photo_label.setText("📁")
            photo_label.setStyleSheet(
                photo_label.styleSheet() + "font-size: 32px;"
            )
        layout.addWidget(photo_label)

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

    def mousePressEvent(self, event) -> None:  # noqa: N802 (Qt override)
        # FONTOS: a super() hívás előrébb van, mint az emit — ha a kattintás
        # egy modális dialógust nyit meg, ami közben (pl. Mentésre) törli ezt
        # a kártyát (reload_cards -> deleteLater), akkor a dialógus bezárása
        # után NEM szabad semmit hívni ezen a (már törölt) self-en. Az emit
        # ezért az utolsó dolog, amit a metódus csinál.
        super().mousePressEvent(event)
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.project.path)


class TaskRowWidget(QWidget):
    """Egy feladat-sor: pipa/gomb + gazdag-szöveges (HTML) tartalom + szerkesztés/törlés."""

    start_requested = Signal(int)
    toggled = Signal(int, bool)
    edit_requested = Signal(int)
    delete_requested = Signal(int)

    def __init__(self, task: TaskItem, mode: str = "pending", parent: QWidget | None = None):
        super().__init__(parent)
        self.task_id = task.id

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)

        if mode == "pending":
            start_btn = QPushButton(tr("project.task.start"))
            start_btn.clicked.connect(lambda: self.start_requested.emit(self.task_id))
            layout.addWidget(start_btn)
        else:
            self.checkbox = QCheckBox()
            self.checkbox.setChecked(mode == "done")
            self.checkbox.toggled.connect(
                lambda checked: self.toggled.emit(self.task_id, checked)
            )
            layout.addWidget(self.checkbox)

        self.label = QLabel()
        self.label.setTextFormat(Qt.TextFormat.RichText)
        self.label.setText(task.html)
        self.label.setWordWrap(True)
        layout.addWidget(self.label, 1)

        edit_btn = QPushButton(tr("common.edit"))
        edit_btn.clicked.connect(lambda: self.edit_requested.emit(self.task_id))
        layout.addWidget(edit_btn)

        delete_btn = QPushButton(tr("common.delete"))
        delete_btn.clicked.connect(lambda: self.delete_requested.emit(self.task_id))
        layout.addWidget(delete_btn)

    def set_html(self, html: str) -> None:
        self.label.setText(html)



        
class MilestoneDialog(QDialog):
    """Mérföldkő felvétele / szerkesztése (dátum, cím, rövid leírás)."""

    def __init__(
        self, parent: QWidget | None = None, milestone: Milestone | None = None
    ):
        super().__init__(parent)
        self.setWindowTitle(tr("widgets.milestone_title"))

        layout = QFormLayout(self)

        default_date = (
            milestone.date if milestone else date.today().strftime("%Y.%m.%d")
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

    def __init__(self, parent: QWidget | None = None, html: str = ""):
        super().__init__(parent)
        self.setWindowTitle(tr("widgets.task_edit_title"))
        self.resize(420, 220)

        layout = QVBoxLayout(self)

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

    def get_html(self) -> str:
        return self.editor.toHtml()


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
    "QToolBar { spacing: 2px; }"
    "QToolButton { padding: 1px 3px; font-size: 10px; }"
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

    act_underline = QAction(_text_icon("U", underline=True), tr("toolbar.underline"), parent)
    act_underline.setCheckable(True)
    act_underline.triggered.connect(
        lambda checked: set_char_format(underline=checked)
    )
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

    def apply_text_color(checked: bool) -> None:  # noqa: ARG001 (Qt signal aláírás)
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
    size_box.setFixedHeight(40) # Részletek ablak eszköztár magassága

    # méretek: padding
    # padding 2. érték - betüméret doboza, font-size: betümérete
    size_box.setStyleSheet("padding: 0px 10px; font-size: 13px;")
    size_box.setFixedWidth(70)   # ne nyúljon szét vízszintesen
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