"""Alkalmazás-szintű logolás beállítása.

Egyetlen helyen konfiguráljuk a Python logging rendszert:
- fájlba írás (rotálva, hogy ne nőjön a végtelenségig)
- egy Qt-signal alapú handler, amivel a LogDialog valós időben
  megjelenítheti az üzeneteket, anélkül hogy közvetlenül a
  logging modulhoz kellene nyúlnia
"""

from __future__ import annotations

import logging
import logging.handlers
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QObject, Signal

from config import USER_DATA_DIR, BUILD_CHANNEL

LOG_DIR = USER_DATA_DIR / "logs"
LOG_FILE = LOG_DIR / "tervezo.log"
CRASH_LOG = LOG_DIR / "crash.log"

# main ágon (éles, telepített kiadás) nem írunk konzolra - ott nincs
# aki nézze, és csak szemetelne egy esetleges terminálba. dev/preview
# ágon viszont kényelmesebb, ha a log a konzolon is megjelenik, nem
# csak a fájlban / LogDialog-ban.
_LOG_TO_CONSOLE = BUILD_CHANNEL != "main"


class _LogSignalEmitter(QObject):
    """Kizárólag a Signal hordozója — külön a logging.Handler-től,
    hogy a Qt Signal-gépezet és a Handler.emit() metódusa
    ne ütközzön névben (lásd PySide6 6.8.x ismert kvirk)."""

    log_record = Signal(str, int)  # (formázott szöveg, levelno)


class QtLogHandler(logging.Handler):
    """Logging handler, ami minden rekordot Qt signal-ként is kibocsát,
    hogy a UI valós időben megjeleníthesse."""

    def __init__(self) -> None:
        super().__init__()
        self._emitter = _LogSignalEmitter()

    @property
    def log_record(self) -> Signal:
        return self._emitter.log_record

    def emit(self, record: logging.LogRecord) -> None:
        msg = self.format(record)
        self._emitter.log_record.emit(msg, record.levelno)

# Modul-szintű, egyetlen példány - a LogDialog erre csatlakozik rá,
# bárhányszor nyitja/zárja meg a felhasználó az ablakot.
qt_log_handler = QtLogHandler()

_file_handler: logging.handlers.RotatingFileHandler | None = None
_console_handler: logging.StreamHandler | None = None


def setup_logging(level: int = logging.INFO) -> None:
    """Egyszer, induláskor hívandó (main.py-ból)."""
    global _file_handler, _console_handler

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        fmt="[%(asctime)s] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    _file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILE, maxBytes=1_000_000, backupCount=5, encoding="utf-8"
    )
    _file_handler.setFormatter(formatter)
    _file_handler.setLevel(level)

    qt_log_handler.setFormatter(formatter)
    qt_log_handler.setLevel(level)

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)  # a tényleges szűrés a handlereken történik
    root.addHandler(_file_handler)
    root.addHandler(qt_log_handler)

    if _LOG_TO_CONSOLE:
        _console_handler = logging.StreamHandler()
        _console_handler.setFormatter(formatter)
        _console_handler.setLevel(level)
        root.addHandler(_console_handler)


def set_log_level(level: int) -> None:
    """UI-ból hívva állítja a minimum szintet - ettől kezdve ez a szint
    kerül a fájlba ÉS a log ablakba is."""
    qt_log_handler.setLevel(level)
    if _file_handler is not None:
        _file_handler.setLevel(level)
    if _console_handler is not None:
        _console_handler.setLevel(level)


def _write_raw(text: str) -> None:
    """Közvetlenül a fájlba ír, a logging Formatter megkerülésével,
    ÉS az élő log ablaknak is jelzi, hogy azonnal lássa."""
    if _file_handler is not None and _file_handler.stream is not None:
        _file_handler.stream.write(text + "\n")
        _file_handler.flush()
    qt_log_handler.log_record.emit(text, logging.INFO)
    if _LOG_TO_CONSOLE:
        print(text)


def log_raw(text: str) -> None:
    """Nyers sor - se időbélyeg, se szint. (pl. elválasztó vonal, fájlút)"""
    _write_raw(text)


def log_header(text: str) -> None:
    """Időbélyeggel ellátott sor, de szint NÉLKÜL. (pl. 'app indul' fejléc)"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # noqa: DTZ005
    _write_raw(f"[{timestamp}] {text}")