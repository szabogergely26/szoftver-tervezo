# Tervező App — Specifikáció v2 (2026-07-23)

> Ez a `szoftvertervezo.md` (2026-07-22) frissített, összesített változata. A korábbi dokumentum a koncepciót és a motivációt írta le; ez a verzió a beszélgetés során tisztázott konkrét adatmodellt, mappaszerkezetet és UI-részleteket rögzíti.

## Előzmény / motiváció

(Változatlan az eredeti dokumentumhoz képest — lásd `szoftvertervezo.md`.) Röviden: egy ODT-alapú "Fejlesztési-ütemterv" dokumentumban négy tartalomtípus keveredik (projekt-státusz, napi napló, technikai vizsgálat, ötletek/backlog), és ez megnehezíti a visszakeresést. A cél egy alkalmazás, ami ezt szétválasztja, a **Film-Adatbázis** app UI-mintáját követve.

## Meglévő kód állapota (`Szoftvertervezo.zip` átnézve)

- **`core/models.py`, `core/storage.py`, `core/workspace.py`** — jó absztrakciós szint, **megtartható**, bővítendő az alábbi adatmodell szerint.
- **`ui/main_window.py`** (562 sor) — **koncepcionálisan más irányba futott**: egy klasszikus fa-nézet + `QTextEdit` jegyzettömb-stílusú UI-t valósít meg (dirty-tracking, rename/delete, alap formázás — technikailag rendben), de nincs benne kártyanézet, nincs fül, nincs napló/jegyzet-szétválasztás. **Ezt a réteget gyakorlatilag újra kell építeni.**
- A `Projektek/projects/*.html` fájlokban nincs átmenthető struktúra-ötlet, ezek a jelenlegi (lecserélendő) note-modell termékei.
- `Projektek/inbox/` mappa létezik, de a UI nem használja — egyelőre nem kerül be a v1 tervbe.

## UI felépítés — pontosítva

### Főablak — kártyarács (kártya/lista váltás **nem** kell)

- Kártyák rácsban, görgethető terület
- Minden kártyán: **projekt neve**, **rövid leírás** ("Mire jó a program" rövidített változata vagy a `description` mező), és **státusz-jelzés**:
  - 🟢 zöld = kész
  - 🟡 sárga = folyamatban
  - 🔴 piros = el sincs kezdve
- Kártyára kattintva megnyílik a projekt **részletnézete egy `QDialog`-ban** ("Részletek – {projekt neve}" címsorral) — a Film-Adatbázis app screenshotja alapján ez a végleges referencia (nem az eredeti "ugyanabban az ablakban" ötlet).

### Új projekt felvétele — Varázsló

A Film-Adatbázis "Új bejegyzés" varázslójának mintájára:

| Mező | Kötelező? | Hova kerül |
|---|---|---|
| Fotó | Nem | `project.json` → `photo` (opcionális relatív útvonal, pl. `assets/cover.png`) |
| Név | **Igen** | mappa neve + `project.json` → `name` |
| Leírás | Nem, ajánlott | `project.json` → `description` (rövid, kártyán is megjelenhet) |
| Mire jó a program | **Igen** | → **Áttekintés tab** tartalma |
| Feladatlista (vesszővel elválasztva) | Nem | szétparszolva → `feladatok.json`, mind `done: false` → **Következő feladatok** tabra kerül |

### Projekt-részletnézet — Tabok (`QDialog`, Film-Adatbázis mintájára)

1. **Áttekintés** — "Mire jó a program" szöveg, kezdés/befejezés dátuma, mérföldkövek listája, státusz állítása
2. **Napló** — dátumozott bejegyzések (automatikus mai dátum új bejegyzésnél), alcímekkel és bullet listákkal, gazdag formázással
3. **Elkészült feladatok** — pipált tételek (szűrt nézet a feladatlistából)
4. **Következő feladatok** — checkbox-os backlog (szűrt nézet ugyanabból a listából)

## Adatmodell

### `project.json`

```json
{
  "name": "Pénzügyi Napló",
  "description": "Rövid kártya-alatti leírás",
  "purpose": "Mire jó a program — hosszabb szöveg, az Áttekintés tabra kerül",
  "photo": "assets/cover.png",
  "status": "in_progress",
  "start_date": "2026.03.15",
  "end_date": null,
  "milestones": [
    {"date": "2026.05.01", "title": "Alap CRUD működik", "description": "..."},
    {"date": "2026.06.10", "title": "Sync réteg kész", "description": "..."}
  ]
}
```

`status` értékek: `not_started` (🔴) / `in_progress` (🟡) / `done` (🟢).

### `naplo.html`

- Marad HTML, `QTextEdit`-tel szerkesztve (mint a jelenlegi note-fájlok)
- Új bejegyzésnél a program automatikusan beszúr egy **félkövér dátum-fejlécet** `ÉÉÉÉ.HH.NN` formátumban (idő nélkül) a mai nappal — ha aznapra már van fejléc, nem duplikálódik, az új tartalom alá kerül
- Formázási eszköztár: félkövér, dőlt, aláhúzott, kiemelés (highlight), betűszín, betűméret

### `feladatok.json`

```json
[
  {"id": 1, "html": "<b>2-3-4 CD-s játékok</b> kezelése", "done": false},
  {"id": 2, "html": "Lutris-szerű coveres UI", "done": false}
]
```

- `text` helyett `html` mező, hogy a soronkénti formázás (félkövér, szín stb.) megmaradjon
- Az "Elkészült" / "Következő" tab ugyanezt a listát mutatja, `done` szerint szűrve — nincs fizikai mozgatás, csak állapotváltás

### `assets/`

- Relatív útvonalú képmappa projektenként, a `naplo.html`-be szúrt (és később a canvas-jegyzetekbe kerülő) képekhez, valamint a projekt-fotóhoz

## Mappaszerkezet — összesítve

```
Projektek/projects/<ProjektNév>/
├── project.json      # leírás, cél, státusz, kezdés/befejezés, mérföldkövek, fotó-útvonal
├── naplo.html         # dátumozott napló, gazdag formázással
├── feladatok.json     # [{"id", "html", "done"}, ...]
└── assets/            # projekt-fotó, naplóba szúrt képek
```

## Alkalmazás-szintű beállítások (nem projekt-adat, `QSettings`)

- **Megjelenítés**: Sötét / Világos / Automatikus (rendszertéma követése)
- **Nyelv**: Magyar / Angol — UI-szövegek fordítási réteg mögé kerülnek a kezdetektől (egyszerű `tr()` + szótár)
- **Naplózás**: log fájlba írás (`_appdata/logs/`) + megnyitható log-ablak az alkalmazáson belül + log szintek (DEBUG/INFO/WARNING/ERROR), Python `logging` modullal + egyedi handlerrel
- **Fejlesztői mód**: kapcsoló, ami megjeleníti a még finomítás alatt álló / kísérleti funkciókat (pl. a jövőbeli rajzoló-jegyzet ez alatt debütálna)

## Jövőbeli fázis (v2, nem a mostani modellezés része)

- **Egyszerű vektoros rajzoló jegyzetekhez**: `QGraphicsView`/`QGraphicsScene` alapú mini-canvas (vonal, szövegdoboz, kép + felirat elrendezés) — nem Photoshop/Gimp szintű, Paint-szerű egyszerűség
- A mappaszerkezet ezt nem zárja ki: később egy `canvas_*.json` (alakzat-lista: típus, pozíció, méret, szöveg) kerülhet a projekt mappájába, függetlenül a `naplo.html`-től

## Nyitott kérdések (lezárva ebben a verzióban)

- ~~Adattárolás formátuma~~ → JSON (strukturált adat) + HTML (szabad szöveg) vegyesen, eldöntve
- ~~Képek tárolása~~ → `assets/` mappa projektenként, relatív útvonallal, eldöntve
- ~~Kártya ↔ napló/jegyzet kapcsolat~~ → `project.json` + `naplo.html` + `feladatok.json` hármas egy mappában, eldöntve
- ~~Kell-e kártya/lista nézet váltás~~ → Nem kell, csak kártyarács

## Következő lépés

1. `core/models.py` konkrét kódja: `Project`, `ProjectStatus`, `Milestone`, `TaskItem` dataclass-ok
2. `core/storage.py` bővítése: `read_project`/`write_project`, `read_tasks`/`write_tasks`, napló-bejegyzés beszúró logika
3. `ui/main_window.py` újraépítése: kártyarács + `QDialog`-alapú projekt-részletnézet (Tabok)
4. Beállítások-dialógus és `QSettings` integráció
