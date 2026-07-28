# Tervező App — Munkamenet összefoglaló (2026.07.26)

## 1. Feladat-workflow finomítás

- **Elkészült feladatok** tabon megszűnt a checkbox, a Szerkesztés és a Törlés gomb — csak egy zöld pipa (✅) és időbélyeg jelenik meg, hogy a lista mindig változatlan, megbízható napló maradjon.
- `TaskItem` modell bővítve `completed_at: str | None` mezővel (`models.py`), visszafelé kompatibilis `from_dict`/`to_dict`-tel.
- `TaskRowWidget` (`widgets.py`) három külön ágra bontva: `pending` / `in_progress` / `done`, mindegyik saját megjelenéssel.
- `_on_task_toggled` (`project_dialog.py`) mostantól beírja a `completed_at`-et `IN_PROGRESS → DONE` váltáskor (`datetime.now().astimezone()`, hogy a Ruff DTZ005 figyelmeztetés is elkerülve legyen).
- **Ismert korlát**: a `completed_at` mező bevezetése *előtt* `DONE`-ra állított régi tételeknek nincs és nem is lesz visszamenőleg dátumuk — ez nem hiba, hanem várt viselkedés. Lásd az 5. pontban a tervezett javítást.

## 2. Tálcaikon (rendszertálca)

- `QSystemTrayIcon` bevezetve (`main_window.py`): megnyitás, valódi kilépés, bezáráskor tálcára kicsinyítés.
- **Beállítások → Általános**: új checkbox (`general.close_to_tray`) — bezáráskor tálcára kicsinyítés be/ki kapcsolható.
- Kilépés implementációja `QApplication.instance().quit()`-tal (nem `self.close()`-zal), hogy tálcáról induló kilépés is ténylegesen leállítsa a folyamatot.
- `app.setQuitOnLastWindowClosed(False)` a `main.py`-ban, hogy rejtett főablak mellett megnyitott projekt-dialógus bezárása ne léptesse ki véletlenül az egész appot.
- Gyorsmenü: **Folyamatban lévő** és **Következő feladatok**, projektenként csoportosítva, feladatra kattintva a `ProjectDialog` egyenesen a megfelelő fülre nyitva jelenik meg (`initial_tab_index` paraméter végigvezetve `ProjectDetailsWidget` → `ProjectDialog` → `_open_project_in_dialog`-on).

## 3. Bugfixek

- **Segfault/`RuntimeError: already deleted`** a Napló fülön: egy korábbi copy-paste hiba miatt a `_build_journal_tab()` metódus közepébe bekerült egy oda nem illő `_add_task_submenu` (tálcaikon-kód), emiatt a `self.tabs.addTab(tab, ...)` hívás lemaradt a Napló tab hozzáadásáról → a `journal_editor` widget árván maradt és GC-vel megsemmisült. Javítva: az idegen metódus törölve, az `addTab` hívás visszakerült a helyére.
- Két `reportOptionalMemberAccess` Pylance-hiba (`main_window.py`, `takeAt()` Optional-guard hiánya) — `if item is None: continue` őrfeltétellel javítva mindkét helyen (`_reset_sidebar_placeholder`, `_open_project_in_sidebar`).
- `QtLogHandler` — PySide6 6.8.x alatt a `logging.Handler` + `QObject` közös örökítés miatt a `Signal.emit()` és a `Handler.emit()` metódusnév-ütközésbe került. Javítás: a Signal kiszervezve egy külön `_LogSignalEmitter(QObject)` segédosztályba, a `QtLogHandler` mostantól tiszta `logging.Handler`, `property`-n keresztül adja tovább a Signalt.

## 4. Verziózás és branch-workflow

- `config.py`: `APP_VERSION = "0.2.0"`, `BUILD_CHANNEL` ágfüggő (`dev` / `preview` / `stable`).
- `CHANGELOG.md` (`changelog.md`) létrehozva a `0.2.0` kiadáshoz.
- Git-workflow tisztázva: `dev` → `preview` → (később) `main`, mindig sima `merge`-dzsel, `BUILD_CHANNEL` kézzel átírva és külön commitolva minden ágváltás után.
- **Tervezett egyszerűsítés** (még nincs megcsinálva): `version_info.py` bevezetése, hogy `APP_VERSION`/`BUILD_CHANNEL` egyetlen helyről olvasson mindent (`config.py`, `build_deb.sh`, `control.in`), branch-váltáskor csak egy fájlt kelljen módosítani.

## 5. Adatútvonalak — felhasználói adatok kiszervezése

- **Probléma**: eredetileg a `settings.json` és a `Projektek/` mappa a telepített program mellett (`BASE_DIR`-hez relatívan) jött volna létre — ez `.deb`-ből telepítve `/usr/share/tervezo/` alá esett volna, ahova sima felhasználó nem tud írni.
- **Megoldás**: `config.py`-ban új `USER_DATA_DIR = Path.home() / ".config" / "szoftvertervezo"`, ide kerül a `settings.json`; `workspace.py` a `Projektek/` mappát is innen származtatja.
- **Hátralévő finomítás**: a log mappa jelenleg `~/.local/share/logs/Tervezo/` (RustDesk mintájára), ezt még nem vezettük át `app_logging.py`-ban (jelenleg `/tmp/tervezo/logs`-on áll) — **legközelebbi feladat**.

## 6. Linux `.deb` csomagolás + GitHub Action

- Minta átvéve két saját projektből (Pénzügyi Napló, Filmek-Adatbázis) — a Filmek-Adatbázis egyszerűbb, `root/` overlay-alapú felépítését követtük.
- Létrehozva:
  - `packaging/deb/control` — csomag-metaadatok, függőségek (`python3-pyside6.qtcore/qtgui/qtwidgets`)
  - `packaging/deb/build_deb.sh` — a build script (fájlmásolás, ikon, jogosultságok egységesítése, `dpkg-deb --build`)
  - `packaging/deb/root/usr/bin/tervezo` — launcher script
  - `packaging/deb/root/usr/share/applications/tervezo.desktop` — desktop-fájl
  - `.github/workflows/build-deb.yml` — GitHub Action, ami `dev` push-ra buildeli a `.deb`-et és letölthető Actions-artifactként feltölti
- **Tesztelve, sikeresen fut** telepítve (`sudo dpkg -i --force-all dist/tervezo_0.2.0_all.deb`), a helyes `~/.config/szoftvertervezo/` adatútvonallal.
- **Következő fázis** (még nincs elkezdve): teljes APT szoftverforrás (GPG-aláírt repo, `gh-pages`-re publikálva) — ehhez is megvan már a minta mindkét korábbi projektből.
- **Végcél**: Windows build — még nincs elkezdve, de a `windows-dev/preview/stable` branch-elnevezési konvenció már megvan az egyik korábbi projektben mintaként.

## 7. Nyitott / következő feladatok (Tervező app saját listájából)

1. **Verzió-egységesítés**: `version_info.py` bevezetése.
2. Projektre kattintva ne a részletek-ablak nyíljon meg, hanem egy általános áttekintő nézet az adott projektről.
3. Oldalsáv-nézetben tüntesse fel az aktuális projekt nevét.
4. **Elkészült feladatok dátuma**: a `completed_at` mező bevezetése előtt kész státuszba állított régi tételeknek nincs dátumuk — tervezett javítás: egyszeri migráció/backfill a `storage.py`-ban (Pénzügyi Napló adatbázis-migrációs mintájára), vagy "ismeretlen dátum" jelölés a hiányzó esetekre.
5. Log-mappa átvezetése `~/.local/share/logs/Tervezo/`-ra (`app_logging.py`).
6. APT szoftverforrás (GPG-aláírt repo, `gh-pages` publikálás).
7. Windows build.
