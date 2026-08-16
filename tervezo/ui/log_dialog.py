from __future__ import annotations

import re

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QColor, QDesktopServices, QTextCharFormat, QTextCursor
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
)

from tervezo.core.app_logging import CRASH_LOG, LOG_FILE, qt_log_handler

# Csak a szint-címke színe változik, a sor többi része alapszínű marad.
LEVEL_COLORS = {
    "INFO": "#2e9e4f",       # zöld
    "WARNING": "#2e9e4f",    # zöld
    "ERROR": "#d13c3c",      # piros
    "CRITICAL": "#d13c3c",   # piros
    # DEBUG szándékosan nincs itt -> alapszínnel (fekete/téma) jelenik meg
}

# "[2026-07-25 07:28:36] INFO: DEV mode: False" formátumot bontja szét:
# 1. csoport: "[idő] " | 2. csoport: SZINT | 3. csoport: ": a többi szöveg"
_LEVEL_PATTERN = re.compile(r"^(\[.*?\]\s*)(DEBUG|INFO|WARNING|ERROR|CRITICAL)(:.*)$")


class LogDialog(QDialog):
    """Külön ablakban megnyitható napló nézet: a teljes log fájlt mutatja,
    élőben frissülve, a szint-címke szerint színezve."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Alkalmazásnapló")
        self.resize(900, 600)

        layout = QVBoxLayout(self)

        self.path_label = QLabel(f"Log fájl: {LOG_FILE}")
        self.path_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self.path_label)

        self.crash_path_label = QLabel(f"Súlyos hiba esetén itt: {CRASH_LOG}")
        self.crash_path_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self.crash_path_label)

        self.text_view = QPlainTextEdit()
        self.text_view.setReadOnly(True)
        layout.addWidget(self.text_view, 1)

        button_row = QHBoxLayout()

        refresh_btn = QPushButton("Frissítés")
        refresh_btn.clicked.connect(self.reload_log)
        button_row.addWidget(refresh_btn)

        open_file_btn = QPushButton("Log fájl megnyitása")
        open_file_btn.clicked.connect(self._on_open_log_file)
        button_row.addWidget(open_file_btn)

        copy_btn = QPushButton("Másolás")
        copy_btn.clicked.connect(self._on_copy)
        button_row.addWidget(copy_btn)

        button_row.addStretch(1)

        close_btn = QPushButton("Bezárás")
        close_btn.clicked.connect(self.close)
        button_row.addWidget(close_btn)

        layout.addLayout(button_row)

        self.reload_log()
        qt_log_handler.log_record.connect(self._on_live_record)

    # ---------- Betöltés / élő frissítés ----------
    def reload_log(self) -> None:
        self.text_view.clear()
        if not LOG_FILE.exists():
            self.text_view.setPlainText("(még nincs log fájl)")
            return
        try:
            content = LOG_FILE.read_text(encoding="utf-8")
        except OSError as exc:
            self.text_view.setPlainText(f"Nem sikerült beolvasni a log fájlt: {exc}")
            return

        for line in content.splitlines():
            self._append_colored_line(line)

    def _on_live_record(self, message: str, _levelno: int) -> None:
        self._append_colored_line(message)

    def _append_colored_line(self, line: str) -> None:
        cursor = self.text_view.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        default_fmt = QTextCharFormat()
        match = _LEVEL_PATTERN.match(line)

        if match:
            prefix, level, rest = match.groups()
            cursor.insertText(prefix, default_fmt)

            level_fmt = QTextCharFormat()
            color = LEVEL_COLORS.get(level)
            if color:
                level_fmt.setForeground(QColor(color))
            cursor.insertText(level, level_fmt)

            cursor.insertText(rest + "\n", default_fmt)
        else:
            # pl. az elválasztó "====" sorok vagy a "log file: ..." fejléc-sorok
            cursor.insertText(line + "\n", default_fmt)

        self.text_view.setTextCursor(cursor)
        self.text_view.ensureCursorVisible()

    # ---------- Gombok ----------
    def _on_open_log_file(self) -> None:
        target = LOG_FILE if LOG_FILE.exists() else LOG_FILE.parent
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(target)))

    def _on_copy(self) -> None:
        QApplication.clipboard().setText(self.text_view.toPlainText())

    def closeEvent(self, event) -> None:
        try:
            qt_log_handler.log_record.disconnect(self._on_live_record)
        except TypeError:
             # Már le volt iratkozva (pl. app-kilépéskor a MainWindow
            # újra bezárja ezt az ablakot) - ez nem hiba.
            pass
        super().closeEvent(event)