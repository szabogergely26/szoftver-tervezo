"""Dev-eszköz: egy kiválasztott projekt DONE státuszú feladatainak törlése.

Csak a dev-csatorna adatait célozza (a repó gyökere alatti Projektek/projects
mappát) - a telepített (.deb) verzió ~/.config alatti adatait NEM érinti.

Nem közvetlenül futtatandó - a reset_done_tasks.sh hívja, ami a repó
gyökerét teszi munkakönyvtárrá (import-útvonalak miatt szükséges).
"""

from __future__ import annotations

from config import USER_DATA_DIR
from tervezo.core.models import TaskStatus
from tervezo.core.storage import Storage


def main() -> None:
    projects_dir = USER_DATA_DIR / "Projektek" / "projects"

    if not projects_dir.exists():
        print(f"Nincs ilyen mappa: {projects_dir}")
        raise SystemExit(1)

    projects = sorted(p for p in projects_dir.iterdir() if p.is_dir())

    if not projects:
        print(f"Nincs egyetlen projekt sem itt: {projects_dir}")
        raise SystemExit(1)

    print("Elérhető projektek (dev):\n")
    for i, p in enumerate(projects, start=1):
        print(f"  {i}) {p.name}")

    print()
    choice = input(f"Válassz projektet (1-{len(projects)}, vagy üres = mégse): ").strip()

    if not choice:
        print("Mégse.")
        raise SystemExit(0)

    try:
        idx = int(choice)
        if not (1 <= idx <= len(projects)):
            raise ValueError
    except ValueError:
        print("Érvénytelen választás.")
        raise SystemExit(1)

    project_dir = projects[idx - 1]

    storage = Storage()
    tasks = storage.read_tasks(project_dir)
    done_tasks = [t for t in tasks if t.status == TaskStatus.DONE]

    print(f"\nProjekt: {project_dir.name}")

    if not done_tasks:
        print("Nincs egyetlen 'Elkészült' (done) státuszú feladat sem.")
        raise SystemExit(0)

    print(f"\nElkészült feladatok ({len(done_tasks)} db):\n")
    for t in done_tasks:
        template_note = f"  [sablon: {t.template_id}]" if t.template_id else ""
        print(f"  #{t.id}  {t.title}  (kész: {t.completed_at}){template_note}")

    print()
    confirm = (
        input(f"Biztosan törlöd mind a {len(done_tasks)} elkészült feladatot? [i/N]: ")
        .strip()
        .lower()
    )

    if confirm != "i":
        print("Mégse.")
        raise SystemExit(0)

    remaining = [t for t in tasks if t.status != TaskStatus.DONE]
    storage.write_tasks(project_dir, remaining)

    print(f"\nTörölve: {len(done_tasks)} elkészült feladat.")
    print(f"Megmaradt feladatok száma: {len(remaining)}")


if __name__ == "__main__":
    main()
