"""Egyetlen közös forrás az alkalmazás verziójához és kiadási csatornájához.

Ezt a fájlt kell módosítani branch-váltáskor / kiadáskor - sem a
config.py-ban, sem a packaging/deb/control.in-ben, sem a
build_deb.sh-ban NE írd át kézzel a verziót/csatornát, azok innen olvasnak.

Build/branch-váltás után ELLENŐRIZD a config.py-t is: a BUILD_CHANNEL
értéke határozza meg, hova kerülnek a felhasználói adatok (dev: a repó
gyökere alatti Projektek/, egyébként: ~/.config/szoftvertervezo/).


Új build / nagy funkció / átalakítás: 0.3.0 --> 1.3.0  - major
Kis átalakítás / apróbb újítás: 0.3.0 --> 0.4.0 - minor
Patch / javítás: 0.3.0 --> 0.3.1 - patch

major (0.x.x → 1.0.0): nagy funkció vagy átalakítás — pl. egy komplett új alrendszer (témarendszer, checklist-feature, profil-architektúra), vagy olyan változás, ami érdemben átalakítja, hogyan használod az appot.
minor (0.3.0 → 0.4.0): kisebb újítás vagy bővítés a meglévő rendszeren belül — pl. a mai "Sablon feladatok" funkció, vagy az "Elkészült feladatok részletnézete + duplakatt" — új képesség, de nem alakítja át az egész appot.
patch (0.3.0 → 0.3.1): javítás, bugfix, apró finomítás — pl. a set_task_done bugfix, egy lint-tisztítás, vagy a mai kör-import hiba javítása, ha az önállóan menne ki.

"""

APP_VERSION = "0.7.2"
BUILD_CHANNEL = "main"  # "dev" | "preview" | "main"
