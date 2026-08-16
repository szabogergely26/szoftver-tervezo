"""Alkalmazás vizuális témájának betöltése és alkalmazása.

Jelenleg csak a "light" témát tartalmazza; a "dark" később ugyanígy
felvehető egy dark.qss fájllal, a load_theme() bővítésével.
"""

from __future__ import annotations

from pathlib import Path

from tervezo.core.app_logging import logging

STYLES_DIR = Path(__file__).parent / "styles"


def load_theme(name: str = "light") -> str:
    """Beolvassa a megadott nevű .qss fájlt, és visszaadja a tartalmát.

    Hiba esetén (pl. hiányzó fájl) üres stringet ad vissza, hogy az
    alkalmazás induláskor ne akadjon el egy hibás/hiányzó téma miatt.
    """
    qss_path = STYLES_DIR / f"{name}.qss"
    try:
        return qss_path.read_text(encoding="utf-8")
    except OSError as e:
        logging.warning(f"Téma betöltése sikertelen ({qss_path}): {e}")
        return ""


def apply_theme(app, name: str = "light") -> None:
    """Alkalmazza a megadott témát a teljes QApplication-re."""
    stylesheet = load_theme(name)
    if stylesheet:
        app.setStyleSheet(stylesheet)
        logging.info(f"Téma alkalmazva: {name}")