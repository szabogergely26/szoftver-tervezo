# Changelog

## [0.2.0] - 2026-07-26

### Hozzáadva
- Háromállapotú feladat-workflow: Következő → Folyamatban lévő → Elkészült
- Elkészült feladatoknál automatikus időbélyeg (`completed_at`), checkbox/Szerkesztés/Törlés nélkül
- Tálcaikon (`QSystemTrayIcon`): megnyitás, valódi kilépés, bezáráskor tálcára kicsinyítés (kapcsolható a Beállításokban)
- Tálcamenü gyorsáttekintés: Folyamatban lévő / Következő feladatok projektenként csoportosítva, feladatra kattintva egyenesen a megfelelő fülre nyíló projekt-ablak

### Javítva
- Napló tab hiányzó `addTab` hívás (véletlen copy-paste hiba a `project_dialog.py`-ban), ami `journal_editor` "already deleted" hibát és szegmentálási hibát okozott Mentéskor
- Sidebar `takeAt()` Optional-guard hiányzott (Pylance `reportOptionalMemberAccess`)
