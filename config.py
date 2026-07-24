"""Alkalmazás-szintű beállítások és útvonalak."""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent  # ez most a Szoftvertervezo/ gyökér lesz

ASSETS_DIR = BASE_DIR / "assets"
ICON_PATH = ASSETS_DIR / "icons" / "app_icon.png"