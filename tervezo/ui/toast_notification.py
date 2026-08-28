"""Nem-invazív "toast" értesítés a főablak tetején középen.

Használat (MainWindow-on):
    self.toast = ToastNotification(self)
    ...
    self.toast.show_message("Változtatások mentve")

A widget lebegő overlay-ként viselkedik: nem vesz részt a szülő
layout-jában, abszolút pozícióban jelenik meg (parent felett, vízszintesen
középen, felül), ezért a megjelenése/eltűnése nem tolja el a többi elem
helyét. A szülő resize eseményekor újra kell pozícionálni (lásd
reposition() hívása a MainWindow.resizeEvent()-jében).
"""

from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QPropertyAnimation, Qt, QTimer
from PySide6.QtWidgets import QGraphicsOpacityEffect, QLabel, QWidget

TOP_MARGIN = 16
DISPLAY_MS = 3000
FADE_OUT_MS = 400


class ToastNotification(QLabel):
    def __init__(self, parent: QWidget):
        super().__init__(parent)

        self.setStyleSheet(
            "background-color: #dff2e1;"
            "color: #1e4620;"
            "border: 1px solid #a8d5ab;"
            "padding: 8px 18px;"
            "border-radius: 6px;"
            "font-weight: bold;"
        )
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._opacity_effect = QGraphicsOpacityEffect(self)
        self._opacity_effect.setOpacity(1.0)
        self.setGraphicsEffect(self._opacity_effect)

        self._fade_animation = QPropertyAnimation(self._opacity_effect, b"opacity")
        self._fade_animation.setDuration(FADE_OUT_MS)
        self._fade_animation.setStartValue(1.0)
        self._fade_animation.setEndValue(0.0)
        self._fade_animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self._fade_animation.finished.connect(self._on_fade_finished)

        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self._start_fade_out)

        self.hide()

    def show_message(self, text: str, duration_ms: int = DISPLAY_MS) -> None:
        """Megjeleníti az üzenetet (megjelenés fade nélkül), majd a megadott
        idő után elhalványítja. Ha már fut egy toast, azt megszakítja és
        újraindítja az időzítést az új szöveggel."""
        self._hide_timer.stop()
        self._fade_animation.stop()

        self.setText(text)
        self._opacity_effect.setOpacity(1.0)
        self.adjustSize()
        self.reposition()
        self.show()
        self.raise_()

        self._hide_timer.start(duration_ms)

    def reposition(self) -> None:
        """A szülő felett vízszintesen középre, felülre igazítva."""
        parent = self.parentWidget()
        if parent is None:
            return
        x = (parent.width() - self.width()) // 2
        y = TOP_MARGIN
        self.move(x, y)

    def _start_fade_out(self) -> None:
        self._fade_animation.start()

    def _on_fade_finished(self) -> None:
        self.hide()
