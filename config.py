"""Alkalmazás-szintű beállítások és útvonalak."""

from pathlib import Path

from build_info import (  # noqa: F401  (re-export a hívóknak)
    BUILD_COMMIT,
    BUILD_DATE,
)
from version_info import (  # noqa: F401  (re-export a hívóknak)
    APP_VERSION,
    BUILD_CHANNEL,
)

# ---------- Program (csak olvasható, telepített) útvonalak ----------

BASE_DIR = Path(__file__).resolve().parent

SETTINGS_DIR = BASE_DIR / "settings"

ASSETS_DIR = BASE_DIR / "assets"
ICON_PATH = ASSETS_DIR / "icons" / "app_icon.png"

TAB_ARROW_LEFT_LIGHT_PATH = ASSETS_DIR / "icons" / "left-arrow-light-theme.svg"
TAB_ARROW_RIGHT_LIGHT_PATH = ASSETS_DIR / "icons" / "right-arrow-light-theme.svg"
TAB_ARROW_LEFT_DARK_PATH = ASSETS_DIR / "icons" / "left-arrow-dark-theme.svg"
TAB_ARROW_RIGHT_DARK_PATH = ASSETS_DIR / "icons" / "right-arrow-dark-theme.svg"

# ---------- Felhasználói adatok (mindig írható, sose az app mellett) ----------
#
# dev csatornán (VSCode-ból futtatva, akármelyik git ágon) az adatok
# a repó gyökere alatti Projektek/ mappában élnek, hogy fejlesztés közben
# sose keveredjenek a telepített (.deb) verzió éles adataival.
# preview/main csatornán (a ténylegesen telepített csomag) az adatok
# a szokásos ~/.config alá kerülnek.

if BUILD_CHANNEL == "dev":
    USER_DATA_DIR = BASE_DIR
else:
    USER_DATA_DIR = Path.home() / ".config" / "szoftvertervezo"

USER_DATA_DIR.mkdir(parents=True, exist_ok=True)


SETTINGS_FILE = USER_DATA_DIR / "settings.json"


# A "Sablon feladatok" dialógus tételei: a program-melletti fájl csak
# kiinduló ("seed") adat, .deb-ből telepítve nem írható – az éles,
# szerkeszthető példány a USER_DATA_DIR alá kerül (l. Storage.read_template_tasks).
TEMPLATE_TASKS_SEED_FILE = BASE_DIR / "tervezo" / "core" / "sablon_feladatok.json"
TEMPLATE_TASKS_FILE = USER_DATA_DIR / "sablon_feladatok.json"
