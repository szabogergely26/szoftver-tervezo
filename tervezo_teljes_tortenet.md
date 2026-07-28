# Tervező App — Teljes fejlesztési történet (2026.07.22 – 07.26)

## Az ötlet és a motiváció (07.22)

A kiindulópont egy ODT-alapú "Fejlesztési-ütemterv" dokumentum volt, amiben négyféle tartalom keveredett egyetlen lineáris szövegben: projekt-státusz/ütemterv, napi napló, technikai mélyfúrás-jegyzetek és ötletek/backlog. Ez megnehezítette a visszakeresést. A cél egy alkalmazás, ami ezt a négy réteget szétválasztja — vizuális mintaként a már meglévő **Film-Adatbázis** app szolgált (kártyás nézet, fülek, egyszerű toolbar).

Volt egy korábbi próbálkozás is (`tervező_app.zip`) tiszta `core`/`ui` szétválasztással, de a `main_window.py` (562 sor) koncepcionálisan félrement — egy klasszikus fa-nézet + jegyzettömb-stílusú UI volt kártyák/fülek nélkül. Ezt a réteget teljesen újra kellett építeni, a `core/models.py`, `core/storage.py`, `core/workspace.py` viszont jó alapnak bizonyult.

## Specifikáció és adatmodell (07.22–07.23)

Az UI-koncepció lezárva: kártyarács a főablakban (🔴/🟡/🟢 státuszjelzés), kártyára kattintva `QDialog` nyílik meg fülekkel (Áttekintés / Napló / Következő feladatok / Elkészült feladatok). Adatmodell projektenként:

```
Projektek/projects/<ProjektNév>/
├── project.json      # leírás, cél, státusz, dátumok, mérföldkövek, fotó-útvonal
├── naplo.html         # dátumozott, gazdagon formázott napló
├── feladatok.json     # [{"id", "html", "status"}, ...]
└── assets/            # projekt-fotó, naplóba szúrt képek
```

Fontos döntések: a feladatoknál `html` mező (nem sima `text`), hogy soronkénti formázás (félkövér, szín) is elférjen; a napló automatikus dátumfejlécet kap új bejegyzésnél; mérföldkövek (dátum + cím + leírás) külön listaként az Áttekintés tabon.

## Alapok felépítése és korai hibavadászat (07.23)

A `models.py`/`storage.py`/`workspace.py` konkrét kódja elkészült, a UI felépült a specifikáció szerint. Több natív crash került elő és lett megoldva:
- **`RuntimeError: already deleted`** — egy Signal `ProjectCard.mousePressEvent`-ben a `super().mousePressEvent()` hívás *előtt* sült el; a sorrend cseréje + `QTimer.singleShot(0, ...)` a `reload_cards()` késleltetésére oldotta meg.
- **Szegmentálási hiba** — a `FlowLayout` (egyéni `QLayout`) egy `__del__` metódusa ütközött a Qt saját cleanup-mechanizmusával; törölve lett. Emellett `Qt.Orientations` nem létező típusnév volt (helyesen `Qt.Orientation(0)`), és a `getContentsMargins()` nem adott vissza iterálható tuple-t (`contentsMargins()`-re cserélve).
- Státuszjelzés emoji helyett CSS-stílusú színes pötty `QLabel`-lel (`#e74c3c`/`#f1c40f`/`#2ecc71`) — a rendszer emoji-fontjai megbízhatatlanul jelentek meg Qt alatt.

## Háromállapotú feladat-workflow, ikon, stílus (07.24)

- A kártyák 3D-s megjelenése (`QFrame.Shape.StyledPanel`) laposra cserélve (`NoFrame` + 1px border).
- Felismerve, hogy hiányzik egy harmadik állapot: `TaskStatus` enum (`PENDING` / `IN_PROGRESS` / `DONE`) bevezetve, visszafelé kompatibilis `from_dict`/`to_dict`-tel és `@property done` alias-szal. `TaskRowWidget` `mode` paramétert kapott, `pending` módban checkbox helyett "Elkezdés" gomb.
- Saját alkalmazásikon legyártva (256×256, indigó-türkiz gradiens, vágólap-motívum, zöld pipa), `config.py` létrehozva (`BASE_DIR`, `ASSETS_DIR`, `ICON_PATH`). Egy `QIcon`-t modulszinten (osztályon kívül) létrehozó sor `QPixmap: Must construct a QGuiApplication before a QPixmap` crash-t okozott — javítva, az ikon csak `__init__`-en belül jön létre.
- Menü- és toolbar-ikonok (`QIcon.fromTheme(...)`).
- **Oldalsáv nézetmód** bevezetve alternatívaként a `QDialog`-hoz: `ProjectDetailsWidget` kiszervezve `ProjectDialog`-ból, `QSplitter`-alapú elrendezés a főablakban, nézetmód-váltó a Beállításokban (`get_project_view_mode()`), splitter-méret mentése/visszatöltése.
- **Beállítások dialógus** flat listából `QTreeWidget`-alapú kategóriafává alakítva.
- **Verziózás bevezetve**: `APP_VERSION`/`BUILD_CHANNEL` (`dev`/`preview`/`stable`) a `config.py`-ban, ablakcím dinamikusan mutatja a csatornát dev/preview ágon. Névjegy-ablak (`about_dialog.py`) létrehozva.
- `requirements.txt` (`pipreqs`), első `venv`, `ruff` bevezetve és futtatva.
- **Fordítási réteg (i18n)**: kiderült, hogy a `tr()`/`set_language()` sehol nem volt ténylegesen meghívva — minden szöveg keményen magyarul volt beégetve. ~60 fordítási kulcs + `language_signal` (QObject-alapú) bevezetve, `retranslate_ui()` minden dialógusban és a főablakban.
- Git-történet logikus commitokra bontva, `main`/`preview`/`dev` háromágas workflow kialakítva, első GitHub-publikálás (`szoftver-tervezo` néven, VS Code GUI-val).
- Ötletek rögzítve (nem implementálva még ekkor): jobb oldali globális teendő-sidebar, pasztell háttérszínű kártyák a színes pötty helyett.

## Borítókép, naplózás, csapatmunka (07.25)

- **Borítókép-funkció** a projekt-részletekhez: base64-JSON és abszolút útvonal is elvetve (túl nehéz / nem hordozható) — végleges megoldás: a kiválasztott kép bemásolása a projekt saját `assets/` mappájába, relatív útvonal mentve. `storage.py`: `set_project_cover`, `remove_project_cover`, `_detect_existing_cover`. Egy duplikált metódusdefiníció-hiba (`_on_choose_cover`/`_on_remove_cover` kétszer, a régi verzió csendben felülírta az újat) megtalálva és javítva.
- **Teljes naplózási rendszer a semmiből**: `tervezo/core/app_logging.py` (rotáló fájl-handler + Qt-signal alapú `QtLogHandler` élő UI-frissítéshez), `tervezo/ui/log_dialog.py` (élő log-ablak, szintenkénti színkódolással), "Naplózás" kategória a Beállításokban, "Eszközök" menü.
- **Szegmentálási hiba vadászat**: időszakosan lefagyott az app induláskor — `faulthandler.enable()` bevezetve diagnosztikára. Kiderült, hogy a borítókép (`QPixmap`) betöltése/megjelenítése a kártyaépítés *közben*, szinkron módon történt; a megoldás `QTimer.singleShot(0, ...)`-ba kiszervezni a pixmap-betöltést, hogy a widget-építés már lezárult állapotban fusson le.
- **Csapatmunka**: egy fejlesztő ismerős (Gergő Fertetics) GitHub-collaboratorként bevonva; ő diagnosztizált és javított egy race condition-t (kártyára kattintás közben induló `reload_cards()` törölte a még feldolgozás alatt álló widgetet) — a megoldás `Qt.ConnectionType.QueuedConnection` az `open_project` meghívásához.
- Három-ágas branch-stratégia tisztázva: `main` a stabil история, `preview` egy adott javított commit-ponton külön ág a teszteléshez, `dev` a folyamatos fejlesztés.

## Mai nap: lezárás, tálcaikon, csomagolás (07.26)

- **Elkészült feladatok** tab lezárva: checkbox/Szerkesztés/Törlés eltávolítva, helyette zöld pipa + időbélyeg (`completed_at` mező a `TaskItem`-ben).
- **Tálcaikon** (`QSystemTrayIcon`) a semmiből felépítve: megnyitás, valódi kilépés (`QApplication.instance().quit()`), bezáráskor tálcára kicsinyítés (kapcsolható beállítás), gyorsmenü projektenként csoportosított Folyamatban lévő/Következő feladatokkal, feladatra kattintva a megfelelő fülre nyíló projekt-ablakkal.
- **Két komoly bugfix**: (1) egy copy-paste hiba miatt a Napló tab `addTab` hívása rossz helyre került, ami `journal_editor` "already deleted" hibát és szegmentálási hibát okozott Mentéskor; (2) `QtLogHandler` PySide6 6.8.x alatt `Signal`/`Handler.emit()` névütközésbe futott — a Signal külön `QObject`-segédosztályba szervezve.
- **Verziózás**: `0.2.0`, `CHANGELOG.md` létrehozva, `dev → preview` merge, majd Pull Request bevezető ismerkedés (GitHub felület).
- **Felhasználói adatok kiszervezése**: `settings.json` és a `Projektek/` mappa mostantól `~/.config/szoftvertervezo/` alatt, nem a telepített program mellett (ez lett volna a `.deb`-es telepítés blokkolója).
- **Linux `.deb` csomagolás + GitHub Action**: két saját korábbi projekt (Pénzügyi Napló, Filmek-Adatbázis) csomagolási mintája alapján `packaging/deb/` struktúra és `.github/workflows/build-deb.yml` létrehozva, sikeresen tesztelve (`sudo dpkg -i`, futó program, helyes adatútvonalak).
- **Nyitva maradt/tervezett**: `version_info.py` (egyetlen hely a verzió/csatorna infónak), log-mappa átvezetése `~/.local/share/logs/Tervezo/`-ra, a `completed_at` nélküli régi feladatok migrációja, teljes APT szoftverforrás (GPG-aláírt repo), Windows build.

## Állandó munkastílus-jellemzők

- A kód mindig chatbe másolva kerül a projektbe (fájlletöltés helyett), fájlonként.
- Egy funkció = egy commit, letesztelve előtte; az új, önálló funkcióba kezdés előtt érdemes jelezni, ha commitolni kellene előtte.
- Preferencia: explicit, olvasható kód az absztrakció helyett; minden új menüponthoz a teljes csomag (QAction, slot, `retranslate_ui`, fordítási kulcs) egyszerre.
- Saját, explicit QSS-stílus a cél, rendszertéma-függés nélkül, de túlstilizálás nélkül is.
