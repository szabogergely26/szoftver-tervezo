"""Egyetlen közös forrás az alkalmazás verziójához és kiadási csatornájához.

Ezt a fájlt kell módosítani branch-váltáskor / kiadáskor - sem a
config.py-ban, sem a packaging/deb/control.in-ben, sem a
build_deb.sh-ban NE írd át kézzel a verziót/csatornát, azok innen olvasnak.

Build/branch-váltás után ELLENŐRIZD a config.py-t is: a BUILD_CHANNEL
értéke határozza meg, hova kerülnek a felhasználói adatok (dev: a repó
gyökere alatti Projektek/, egyébként: ~/.config/szoftvertervezo/).
"""

APP_VERSION = "0.2.0"
BUILD_CHANNEL = "dev"  # "dev" | "preview" | "main"