"""Alkalmazás-szintű beállítások és útvonalak."""

from pathlib import Path

# ---------- Program (csak olvasható, telepített) útvonalak ----------

BASE_DIR = Path(__file__).resolve().parent

SETTINGS_DIR = BASE_DIR / "settings"

ASSETS_DIR = BASE_DIR / "assets"
ICON_PATH = ASSETS_DIR / "icons" / "app_icon.png"

# ---------- Felhasználói adatok (mindig írható, sose az app mellett) ----------

USER_DATA_DIR = Path.home() / ".config" / "szoftvertervezo"
USER_DATA_DIR.mkdir(parents=True, exist_ok=True)

SETTINGS_FILE = USER_DATA_DIR / "settings.json"


# ---------- Verzió / kiadási csatorna ----------

APP_VERSION = "0.3.0"
BUILD_CHANNEL = "Stable"