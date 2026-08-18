# Tervező — Beállítás-térkép

Ez a fájl azt gyűjti össze, hogy egy-egy gyakori módosításhoz **melyik fájlban,
melyik sort/kulcsot** kell átírni. Cél: ne kelljen mindig újra megkeresni.

Bővítsd nyugodtan, ahogy új beállítási pontok felmerülnek — egy blokk = egy
módosítási pont, mindig "Hol" + "Mit" + (ha van) "Kapcsolódó" felépítéssel.

---

## App név módosítása (UI-ban megjelenő cím)

**Hol:** `settings/translations.py`

**Mit:** a `main.window_title` kulcs értékét kell átírni a megfelelő nyelvi
szótár(ak)ban.

```python
"main.window_title": "Szoftvertervező",
```

**Kapcsolódó:** ez CSAK az ablak címsorában megjelenő szöveget változtatja.
A rendszerszintű alkalmazás-azonosítót (amit a `QSettings` a konfigurációs
fájl helyének meghatározásához használ) a `main.py`-ban lévő
`app.setApplicationName(...)` / `app.setOrganizationName(...)` hívások
adják meg — ez egy külön, ritkán módosítandó beállítás, nem ide tartozik.

---

## "Folyamatban" / "Következő feladatok" kattintás — melyik tab nyílik meg

**Hol:**

- `tervezo/ui/in_progress_task_label.py` → `mousePressEvent()` metódus,
  `self.project_open_requested.emit(project_dir, <TAB_INDEX>)` sor
- `tervezo/ui/task_overview_popup.py` → `_on_task_label_clicked()` metódus,
  `self.project_open_requested.emit(project_dir, <TAB_INDEX>)` sor

**Mit:** a `TAB_INDEX` egész szám dönti el, melyik tab nyílik meg a Részletek
(`ProjectDialog`) ablakban. Az index a `project_dialog.py`-ban lévő
`self.tabs.addTab(...)` hívások **sorrendjéből** adódik, 0-tól számozva:

| Index | Tab | Fordítási kulcs |

|---|---|---|
| 0 | Áttekintés | `project.tab.overview` |
| 1 | Napló | `project.tab.journal` |
| 2 | Következő feladatok | `project.tab.next_tasks` |
| 3 | Folyamatban lévő feladatok | `project.tab.in_progress_tasks` |
| 4 | Kész feladatok | `project.tab.done_tasks` |

**Kapcsolódó:** ha új tab kerül be a `ProjectDialog`-ba, ez a táblázat és
minden `emit(project_dir, <szám>)` hívás **eltolódhat** — mindig ellenőrizd
újra az `addTab` sorrendet a `project_dialog.py`-ban, mielőtt tab-indexre
hivatkozó kódot írsz vagy módosítasz.

---

## Új fordítási kulcs felvétele (`translations.py`)

**Hol:** `settings/translations.py`

**Mit:** a fordítási szótár(ak) a nyelvkód szerint vannak elkülönítve (pl.
`"hu"`, `"en"`). Új kulcsot **mindegyik** nyelvi szótárba fel kell venni,
ugyanazzal a kulcsnévvel, hogy nyelvváltáskor ne maradjon ki egyik nyelvből
sem.

Az elnevezési konvenció **pont-elválasztós, terület-alapú prefix**, pl.:

```
main.window_title
main.status_bar.next_task
main.status_bar.in_progress
main.action.new_project
project.tab.overview
project.tab.in_progress_tasks
common.exists_title
```

Formátum:

```python
"terület.alterület.kulcs_neve": "Megjelenő szöveg",
```

Új kulcs felvételekor:

1. Válassz a fenti mintához illeszkedő prefixet (pl. `main.status_bar.*`,
   `project.tab.*`, `common.*` — vagy ha egyik sem illik, új, beszédes
   prefixet).
2. Vedd fel **minden** nyelvi szótárba ugyanazzal a kulccsal.
3. A kódban `tr("terület.alterület.kulcs_neve")` hívással hivatkozz rá —
   soha ne írj be nyers, be nem ágyazott magyar/angol szöveget közvetlenül
   a UI-kódba.
4. Ha a kulcs hiányzik valamelyik nyelvből, a `tr()` jellemzően magát a
   kulcsot írja ki szöveg helyett (ahogy a `main.status_bar.in_progress`
   esetében is történt, amíg nem lett felvéve) — ez a jele annak, hogy
   valahol kimaradt a felvétel.

---

<!-- Új pontokat ide, alább vegyél fel, ugyanezzel a felépítéssel. -->