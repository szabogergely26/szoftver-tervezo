# Tervező App — Specifikáció (2026-07-22)

## Előzmény

Van egy korábbi próbálkozás: `tervező_app.zip`, PySide6 alapú, tiszta `core`/`ui` szétválasztással:

```
tervező_app/
├── main.py                        (15 sor — belépési pont)
└── tervezo/
    ├── core/
    │   ├── models.py               (11 sor)
    │   ├── storage.py              (43 sor)
    │   └── workspace.py            (30 sor)
    └── ui/
        └── main_window.py          (562 sor — itt ment félre valami, ezt kell alaposan átnézni)
Projektek/projects/
├── Alap_projekt/ (Jegyzet.html, teszt2.html)
└── Pénzügyi Napló/ (Napló hub - Linux+Android sync.html)
```

A `core`/`ui` szétválasztás jó alap, nem a nulláról indulunk. A `main_window.py` 562 sora a gyanús rész.

Korábban HTML-alapú jegyzetelést próbált a felhasználó (a `Projektek/projects/` mappa HTML fájljai), mert abba szebb formázás fér, mint Markdownba — de a szerkesztése kényelmetlen volt.

## Motiváció / miért kell ez az app

Egy másik, ODT-alapú "Fejlesztési-ütemterv" dokumentum is létezik, amiben **négy különböző típusú tartalom keveredik egyetlen lineáris dokumentumban**:

1. Projekt-státusz / ütemterv (mi kész, mi van hátra projektenként: Film-Adatbázis, Pénzügyi Napló, Monitor-Config, Retro Game Launcher, Linux Disk Manager)
2. Napi napló (dátumozott bejegyzések, mit csináltunk aznap)
3. Technikai vizsgálat / mellékszál jegyzetek (pl. egy hosszabb soundbar/TV EDID-audio nyomozás)
4. Ötletek / backlog (CLI tervek, GUI mockupok)

Ez a keveredés megnehezíti a visszakeresést és az áttekintést. A cél egy alkalmazás, ami ezt a négy réteget vizuálisan és szerkezetileg szétválasztja, miközben egy helyen, kényelmesen kezelhető.

Vizuális inspiráció: Google SketchUp-szerű kényelem, de nem 3D — Projekttervekre alakítva, képekkel illusztrálható jegyzetekkel.

## A koncepció — UI felépítés

Mintaként a már meglévő **Film-Adatbázis** app szolgál (bal oldali fülek, kártyás nézet, egyszerű toolbar).

### Bal oldali két fül (mint a Film-Adatbázisban)

#### 1. fül — Projektek (kártya-nézet)

- Kártyák rácsban, görgethető terület
- Minden kártyán: **projekt neve** + **rövid leírás**
- Státusz-jelzés színnel:
  - 🟢 zöld pipa = kész
  - 🟡 sárga = folyamatban
  - 🔴 piros = el sincs kezdve
- Kártyára kattintva **ugyanabban az ablakban** nyílik meg a projekt részletes tartalma (nem külön popup/dialog — hasonlóan ahhoz, ahogy a Film-Adatbázisban egy film kártyájára kattintva megnyílik a részletnézet)
- Menüsor alatt egyszerű **toolbar** (nem ribbon, egyelőre nem szükséges)
  - Toolbaron: **vissza gomb (nyíl)** a kártyanézethez való visszatéréshez

#### Egy projekt megnyitása után, két önállóan görgethető terület

- **A) Napló-stílusú blokk**
  - Formátum: dátum + cím + rövid leírás (bullet pontokkal)
  - Példa tartalom: napi fejlesztési események, mit csináltunk aznap egy adott projekten
  - Cél: időrendi visszakereshetőség

- **B) Szabad szöveges / technikai jegyzet blokk**
  - Hosszabb, kötetlenebb szöveg, alcímekkel, felsorolásokkal
  - Példa: egy önálló technikai vizsgálat/probléma-megoldási szál (pl. hardveres diagnosztika, hosszabb elemzés)
  - Cél: mélyebb, egy adott altémához tartozó jegyzetek tárolása, elkülönítve a napi logtól

Ez a két terület **egymástól függetlenül görgethető**, és vizuálisan/stílusban is elkülönül egymástól (a napló inkább lista-szerű, a jegyzet inkább szabad szöveg/dokumentum-szerű).

## Nyitott kérdések (később tisztázandó)

- Adattárolás formátuma: mit használjon a `core/storage.py` — JSON, SQLite, vagy Markdown-fájlok a lemezen? (A meglévő `storage.py` csak 43 sor, érdemes megnézni, mit csinál most.)
- Képek beillesztése a jegyzetekbe: hogyan tárolódjanak (relatív útvonal egy `assets/` mappában, mint a Film-Adatbázis `cover/` mappája)?
- A projekt-kártyák és a hozzájuk tartozó napló/jegyzet hogyan kapcsolódik adatmodell szinten (`models.py` jelenleg csak 11 sor — valószínűleg ez bővül a legtöbbet)?
- Szükséges-e keresés/filter a kártyák vagy a naplóbejegyzések között?

## Következő lépés (amikor újra elővesszük)

1. Alaposan átnézni a meglévő `tervezo/ui/main_window.py`-t (562 sor) — megérteni mi van benne, mi ment félre
2. Átnézni a `core/models.py`, `core/storage.py`, `core/workspace.py` jelenlegi tartalmát
3. Megnézni a `Projektek/projects/*.html` fájlokat — van-e bennük hasznosítható tartalom/struktúra-ötlet, amit érdemes átmenteni az új rendszerbe
4. Ezek alapján eldönteni: érdemes-e a meglévő `core` réteget megtartani és csak a `ui`-t újraépíteni a fenti koncepció szerint, vagy jobb egy tiszta lappal kezdeni
