"""Alkalmazás vizuális témájának betöltése és alkalmazása.

Jelenleg csak a "light" témát tartalmazza; a "dark" később ugyanígy
felvehető egy dark.qss fájllal - a tab-scroller nyilak dark-témás SVG-i
és a load_theme() logikája már felkészítve rá.
"""

from __future__ import annotations

from pathlib import Path

from config import (
    TAB_ARROW_LEFT_DARK_PATH,
    TAB_ARROW_LEFT_LIGHT_PATH,
    TAB_ARROW_RIGHT_DARK_PATH,
    TAB_ARROW_RIGHT_LIGHT_PATH,
)
from tervezo.core.app_logging import logging

STYLES_DIR = Path(__file__).parent / "styles"


def _qss_url(path: Path) -> str:
    """Abszolút fájl-útvonalat alakít QSS url()-ben használható formára.

    A QSS mindig forward slash-t vár az útvonalban, Windows-on a Path
    backslash-eket ad vissza - erre készülünk fel, ha valaha oda is
    portolódna az app.
    """
    return str(path).replace("\\", "/")


def load_theme(name: str = "light") -> str:
    """Beolvassa a megadott nevű .qss fájlt, és visszaadja a tartalmát.

    A fájlban szereplő {{TAB_ARROW_LEFT}} / {{TAB_ARROW_RIGHT}}
    placeholdereket lecseréli a ténylegesen telepített/dev környezetben
    érvényes abszolút ikon-útvonalra (config.py-ból), a name paraméter
    (pl. "light" / "dark") alapján a megfelelő szín-variánsra - mert a
    QSS statikus szöveg, relatív útvonalat vagy feltételes logikát nem
    tudna megbízhatóan feloldani.

    Hiba esetén (pl. hiányzó fájl) üres stringet ad vissza, hogy az
    alkalmazás induláskor ne akadjon el egy hibás/hiányzó téma miatt.
    """
    qss_path = STYLES_DIR / f"{name}.qss"
    if name == "dark":
        arrow_left_path = TAB_ARROW_LEFT_DARK_PATH
        arrow_right_path = TAB_ARROW_RIGHT_DARK_PATH
    else:
        arrow_left_path = TAB_ARROW_LEFT_LIGHT_PATH
        arrow_right_path = TAB_ARROW_RIGHT_LIGHT_PATH

    try:
        stylesheet = qss_path.read_text(encoding="utf-8")
        stylesheet = stylesheet.replace("{{TAB_ARROW_LEFT}}", _qss_url(arrow_left_path))
        stylesheet = stylesheet.replace(
            "{{TAB_ARROW_RIGHT}}", _qss_url(arrow_right_path)
        )
        return stylesheet
    except OSError as e:
        logging.warning(f"Téma betöltése sikertelen ({qss_path}): {e}")
        return ""


def apply_theme(app, name: str = "light") -> None:
    """Alkalmazza a megadott témát a teljes QApplication-re."""
    stylesheet = load_theme(name)
    if stylesheet:
        app.setStyleSheet(stylesheet)
        logging.info(f"Téma alkalmazva: {name}")
