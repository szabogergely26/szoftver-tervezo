"""Lebegő, mozgatható színmagyarázó ("legend") a projekt/feladat státusz-színekhez.

Vízszintes sáv: piros/sárga/zöld kör + felirat (Nem kezdett / Folyamatban / Kész).
Egérrel fogható és áthúzható a szülő widgeten (jellemzően a MainWindow
központi widgetje) belül. Van egy összecsukó gomb (kis "chip" nézetre húzza
össze magát), és egy X gomb, ami teljesen elrejti — ezt a szülő (MainWindow)
egy toolbar-gombbal tudja visszahozni a show_and_raise() hívással.

A pozíció és az összecsukott/kibontott állapot QSettings-be mentődik, hogy
induláskor emlékezzen rá.
"""

from __future__ import annotations

from PySide6.QtCore import QPoint, QSettings, Qt, QTimer, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QWidget

from settings.translations import tr

# Ugyanazok a hex-kódok, mint a ProjectStatus.color property-ben (models.py) –
# szándékosan nincs importálva onnan, hogy ez a widget ne kösse magát egyetlen
# konkrét modellhez (projekt-státusz vagy feladat-státusz is használhatja).
COLOR_NOT_STARTED = "#e74c3c"
COLOR_IN_PROGRESS = "#f1c40f"
COLOR_DONE = "#2ecc71"

_SETTINGS_POS_KEY = "status_legend/pos"
_SETTINGS_COLLAPSED_KEY = "status_legend/collapsed"


def _dot(color: str, size: int = 14) -> QLabel:
    dot = QLabel()
    dot.setFixedSize(size, size)
    dot.setStyleSheet(f"background-color: {color}; border-radius: {size // 2}px;")
    return dot


class StatusLegendWidget(QFrame):
    """Lebegő státusz-színmagyarázó. A szülőjén belül szabadon mozgatható."""

    # Akkor emittálódik, ha a felhasználó X-szel bezárja – a szülő
    # ilyenkor pl. egy toolbar-gombot tehet láthatóvá a visszahozáshoz.
    closed = Signal()

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setObjectName("StatusLegendWidget")
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.setFrameShape(QFrame.Shape.NoFrame)

        self._drag_offset: QPoint | None = None
        self._collapsed = False
        self._settings = QSettings()
        # Amíg a felhasználó nem mozgatta el kézzel (és nincs mentett egyéni
        # pozíció sem), a widget minden átméretezéskor (pl. maximalizáláskor)
        # újraszámolja magát az alsó sarokba - nem csak "benntartja" magát.
        self._user_moved = False

        self._build_ui()
        self.retranslate_ui()
        self._apply_collapsed_style()

        # A _restore_state (és benne a _default_position) a szülő aktuális
        # méretét használja - ez a konstruktor lefutásakor még nem biztos,
        # hogy a végleges (pl. maximalizált) méret, ezért egy körrel később
        # futtatjuk, miután a szülő ablak elfoglalta a helyét.
        QTimer.singleShot(0, self._restore_state)

    # ---------- UI ----------
    def _build_ui(self) -> None:
        self.setStyleSheet(
            "#StatusLegendWidget {"
            "  background-color: #ffffff;"
            "  border: 1px solid #d0d3d9;"
            "  border-radius: 8px;"
            "}"
        )

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(16, 8, 10, 8)
        self._layout.setSpacing(8)

        # --- Kibontott tartalom (körök + feliratok) ---
        self._content = QWidget(self)
        content_layout = QHBoxLayout(self._content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(14)

        self._entry_not_started = self._build_entry(COLOR_NOT_STARTED)
        self._entry_in_progress = self._build_entry(COLOR_IN_PROGRESS)
        self._entry_done = self._build_entry(COLOR_DONE)

        content_layout.addLayout(self._entry_not_started[0])
        content_layout.addLayout(self._entry_in_progress[0])
        content_layout.addLayout(self._entry_done[0])

        self._layout.addWidget(self._content)
        self._layout.addStretch(0)

        # --- Kis "chip" nézet (csak 3 pötty, összecsukott állapotban) ---
        self._chip = QWidget(self)
        chip_layout = QHBoxLayout(self._chip)
        chip_layout.setContentsMargins(0, 0, 0, 0)
        chip_layout.setSpacing(4)
        chip_layout.addWidget(_dot(COLOR_NOT_STARTED, 10))
        chip_layout.addWidget(_dot(COLOR_IN_PROGRESS, 10))
        chip_layout.addWidget(_dot(COLOR_DONE, 10))
        self._layout.addWidget(self._chip)
        self._chip.setVisible(False)

        # --- Összecsukó / kibontó gomb ---
        self._collapse_btn = QPushButton("–")
        self._collapse_btn.setObjectName("StatusLegendIconButton")
        self._collapse_btn.setFixedSize(20, 20)
        self._collapse_btn.setFlat(True)
        self._collapse_btn.clicked.connect(self._toggle_collapsed)
        self._layout.addWidget(self._collapse_btn)

        # --- Bezáró (X) gomb ---
        self._close_btn = QPushButton("×")
        self._close_btn.setObjectName("StatusLegendIconButton")
        self._close_btn.setFixedSize(20, 20)
        self._close_btn.setFlat(True)
        self._close_btn.clicked.connect(self._on_close_clicked)
        self._layout.addWidget(self._close_btn)

        for btn in (self._collapse_btn, self._close_btn):
            btn.setCursor(Qt.CursorShape.PointingHandCursor)

        self.adjustSize()

    def _build_entry(self, color: str) -> tuple[QHBoxLayout, QLabel]:
        entry_layout = QHBoxLayout()
        entry_layout.setContentsMargins(0, 0, 0, 0)
        entry_layout.setSpacing(6)
        entry_layout.addWidget(_dot(color))
        label = QLabel()
        label.setStyleSheet("font-size: 11px;")
        entry_layout.addWidget(label)
        return entry_layout, label

    def retranslate_ui(self) -> None:
        self._entry_not_started[1].setText(tr("status.not_started"))
        self._entry_in_progress[1].setText(tr("status.in_progress"))
        self._entry_done[1].setText(tr("status.done"))
        self._collapse_btn.setToolTip(
            tr("status_legend.expand") if self._collapsed else tr("status_legend.collapse")
        )
        self._close_btn.setToolTip(tr("status_legend.close"))
        self.adjustSize()

    # ---------- Összecsukás ----------
    def _toggle_collapsed(self) -> None:
        self._collapsed = not self._collapsed
        self._apply_collapsed_style()
        self._save_state()

    def _apply_collapsed_style(self) -> None:
        self._content.setVisible(not self._collapsed)
        self._chip.setVisible(self._collapsed)
        self._collapse_btn.setText("+" if self._collapsed else "–")
        self._collapse_btn.setToolTip(
            tr("status_legend.expand") if self._collapsed else tr("status_legend.collapse")
        )
        self.adjustSize()

    # ---------- Bezárás / visszahozás ----------
    def _on_close_clicked(self) -> None:
        self.hide()
        self._save_state()
        self.closed.emit()

    def show_and_raise(self) -> None:
        self.show()
        self.raise_()
        self._clamp_into_parent()

    # ---------- Mozgatás ----------
    def mousePressEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = event.position().toPoint()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:
        if self._drag_offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
            new_pos = self.mapToParent(event.position().toPoint() - self._drag_offset)
            self.move(new_pos)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            if self._drag_offset is not None:
                # Csak akkor számít "kézzel mozgatottnak", ha ténylegesen
                # húzás történt - egy sima kattintás (pl. a gombokra) ne
                # kapcsolja ki az automatikus alsó-sarok-követést.
                self._user_moved = True
            self._drag_offset = None
            self.setCursor(Qt.CursorShape.OpenHandCursor)
            self._clamp_into_parent()
            self._save_state()
        super().mouseReleaseEvent(event)

    def _clamp_into_parent(self) -> None:
        """Átméretezéskor hívva: ha a felhasználó még nem mozgatta el kézzel
        (és nincs mentett egyéni pozíció), újraszámolja az alapértelmezett
        alsó sarok pozíciót; egyébként csak "benntartja" a jelenlegi helyén.
        """
        parent = self.parentWidget()
        if parent is None:
            return

        if not self._user_moved:
            self._default_position()
            return

        self.adjustSize()
        max_x = max(0, parent.width() - self.width())
        max_y = max(0, parent.height() - self.height())
        x = min(max(self.x(), 0), max_x)
        y = min(max(self.y(), 0), max_y)
        self.move(x, y)

    # ---------- Állapot mentése / visszaállítása ----------
    def _save_state(self) -> None:
        self._settings.setValue(_SETTINGS_POS_KEY, self.pos())
        self._settings.setValue(_SETTINGS_COLLAPSED_KEY, self._collapsed)

    def _restore_state(self) -> None:
        collapsed = self._settings.value(_SETTINGS_COLLAPSED_KEY, False, type=bool)
        if collapsed:
            self._collapsed = True
            self._apply_collapsed_style()

        pos = self._settings.value(_SETTINGS_POS_KEY, None)
        if isinstance(pos, QPoint):
            self._user_moved = True
            self.move(pos)
        else:
            self._default_position()

    def _default_position(self) -> None:
        parent = self.parentWidget()
        if parent is None:
            return
        self.adjustSize()

        # Vízszintesen a bal oldali (kártyás) terület közepére igazítjuk,
        # ha az elérhető - így oldalsáv nézetben sem csúszik a splitter
        # jobb oldali paneljére. Ha valamiért nem érhető el, essünk vissza
        # a teljes ablak közepére.
        main_window = self.window()
        left_area_width = getattr(main_window, "scroll_area", None)
        if left_area_width is not None:
            x = left_area_width.width() // 2 - self.width() // 2
        else:
            x = parent.width() // 2 - self.width() // 2

        y = parent.height() - self.height() - 50
        self.move(max(x, 0), max(y, 0))