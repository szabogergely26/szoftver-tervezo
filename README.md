# Tervező App (Szoftvertervező)

**Verzió:** 0.3.0 · **Státusz:** korai, aktívan fejlesztett, `.deb`-ből telepíthető

A Tervező App egy PySide6 alapú, KDE Plasma környezethez készült asztali alkalmazás saját szoftverfejlesztési projektek átlátható kezelésére: projekt-státuszok, napi napló, technikai jegyzetek és feladatlisták egy helyen, de vizuálisan és szerkezetileg elkülönítve egymástól.

> **Megjegyzés az AI-közreműködésről:** A kód nagy része AI (Claude) segítségével
> készült, emberi tervezés, irányítás és folyamatos ellenőrzés mellett. A
> funkcionalitásért és a projekt irányáért a szerző felel.

## Miért készült

A kiindulópont egy ODT-alapú "Fejlesztési-ütemterv" dokumentum volt, amiben négyféle tartalom keveredett egyetlen lineáris szövegben: projekt-státusz/ütemterv, napi napló, technikai mélyfúrás-jegyzetek és ötletek/backlog. Ez megnehezítette a visszakeresést. A Tervező App célja, hogy ezt a négy réteget szétválassza, miközben egy helyen, kényelmesen kezelhető marad.

## Fő funkciók

- **Kártyarács főnézet** — minden saját projekt egy kártya, névvel, rövid leírással és színes státuszjelzéssel (🔴 el sincs kezdve / 🟡 folyamatban / 🟢 kész)
- **Projekt-részletnézet** fülekkel:
  - Áttekintés — cél, kezdés/befejezés dátuma, mérföldkövek
  - Napló — dátumozott, gazdagon formázott bejegyzések
  - Következő feladatok / Folyamatban lévő / Elkészült feladatok — háromállapotú workflow, automatikus időbélyeggel elkészüléskor
- **Új projekt felvétele varázslóval**, a Filmek-Adatbázis app mintájára
- **Rendszertálca-integráció**: megnyitás, kilépés, bezáráskor tálcára kicsinyítés (kapcsolható), gyorsmenü projektenként csoportosított feladatokkal
- **Beállítások**: megjelenítés (sötét/világos/automatikus), nyelv (magyar/angol), naplózás, fejlesztői mód
- **Élő log-ablak** az alkalmazáson belül, szintenkénti színkódolással

## Adatmodell

Projektenként egy mappa, JSON + HTML vegyes tárolással:

```text
Projektek/projects/<ProjektNév>/
├── project.json      # leírás, cél, státusz, dátumok, mérföldkövek, fotó-útvonal
├── naplo.html         # dátumozott, gazdagon formázott napló
├── feladatok.json     # [{"id", "html", "status"}, ...]
└── assets/            # projekt-fotó, naplóba szúrt képek
```

A felhasználói adatok (`settings.json`, `Projektek/`) a `~/.config/szoftvertervezo/` alatt tárolódnak, nem a telepített programfájlok mellett — ez teszi lehetővé a `.deb`-ből történő telepítést.

## Telepítés

A projekt Debian-alapú rendszeren `.deb` csomagból telepíthető:

```bash
sudo dpkg -i tervezo_*.deb
```

## Fejlesztői futtatás

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

## Jelenlegi állapot

Az alkalmazás a fenti fő funkciókkal már használható, `.deb`-ből telepíthető, saját GitHub Action buildeli a csomagot.

Hátralévő / tervezett feladatok:

- `version_info.py` bevezetése egyetlen közös verzió-/csatornaforrásként
- A `completed_at` időbélyeg nélküli, korábbi "kész" feladatok migrációja
- Log-mappa átvezetése `~/.local/share/logs/Tervezo/`-ra
- Teljes APT szoftverforrás (GPG-aláírt repo, `gh-pages` publikálás)
- Windows build
- Későbbi fázis: egyszerű vektoros rajzoló-jegyzet (`QGraphicsView`-alapú mini-canvas)

## Licenc

GPL-3.0-or-later

## Mi hol van a projektbe?

MainWindow címe - a program neve: `settings\translations.py`
