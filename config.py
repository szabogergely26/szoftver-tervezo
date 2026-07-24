"""Alkalmazás-szintű beállítások és útvonalak."""

from pathlib import Path

# ---------- Alapértelmezett útvonalak ----------

# A projekt gyökérkönyvtára (Szoftvertervezo/)
BASE_DIR = Path(__file__).resolve().parent

# A settings/ csomag könyvtára (settings.py, translations.py, stb.)
SETTINGS_DIR = BASE_DIR / "settings"   # a beállítások könyvtára (pl. settings/settings.py, settings/translations.py, stb.)

# A ténylegesen elmentett beállítások fájlja (JSON)
# FIGYELEM: fejlesztés alatt a projekt gyökerében van; csomagolásnál majd
# a felhasználó user-config mappájába kerül (pl. platformdirs csomaggal),
# hogy ne kelljen írási jog a program telepítési helyére.
SETTINGS_FILE = BASE_DIR / "settings.json"


 # eszközök, ikonok, képek, stb. könyvtára
ASSETS_DIR = BASE_DIR / "assets"   

# az alkalmazás ikonja (tálca-/taskbar-ikon, ablakikon, stb.)
ICON_PATH = ASSETS_DIR / "icons" / "app_icon.png"   





# ---------- Verzió / kiadási csatorna ----------

APP_VERSION = "0.1.0"

# Lehetséges értékek: "dev", "preview", "stable"
# FIGYELEM: ez az érték ágfüggő! dev-en "dev", preview-n "preview",
# main-en "stable" legyen. Merge után kézzel vissza kell állítani az
# adott ágnak megfelelő értékre, és külön commitolni (lásd CHANGELOG).
BUILD_CHANNEL = "dev"