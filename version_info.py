"""Egyetlen közös forrás az alkalmazás verziójához és kiadási csatornájához.

Ezt a fájlt kell módosítani branch-váltáskor / kiadáskor - sem a
config.py-ban, sem a packaging/deb/control.in-ben, sem a
build_deb.sh-ban NE írd át kézzel a verziót/csatornát, azok innen olvasnak.

Build/branch-váltás után ELLENŐRIZD a config.py-t is: a BUILD_CHANNEL
értéke határozza meg, hova kerülnek a felhasználói adatok (dev: a repó
gyökere alatti Projektek/, egyébként: ~/.config/szoftvertervezo/).



0.3.0 → 0.3.1 (patch) vagy 0.3.0 → 0.4.0 (minor, mert egy komplett alrendszer)

Megjegyzés: 0.4.0 a helyes választás — a verziószámozás logikája szerint az új funkciót (témarendszer) viszi a minor bump, 
a hozzá tartozó apró javítások (lint, set_task_done fix) pedig ugyanannak a release-nek a részei, nem külön patch-verziót érdemelnek. 
A 0.4.1 csak akkor jönne, ha a 0.4.0 kiadása UTÁN derülne ki egy hiba, amit gyorsan javítani kell.
"""

APP_VERSION = "0.5.0"
BUILD_CHANNEL = "dev"  # "dev" | "preview" | "main"
