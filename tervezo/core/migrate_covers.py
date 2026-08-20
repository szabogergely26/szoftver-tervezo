from __future__ import annotations

import logging
from pathlib import Path

from .storage import Storage

logger = logging.getLogger(__name__)


def migrate_absolute_covers(projects_dir: Path) -> list[str]:
    """Végigmegy az összes projekten, és ha a project.json 'photo' mezője
    abszolút útvonalra mutat (régi, nem-portábilis állapot), bemásolja a
    képet a projekt saját assets/ mappájába, és relatívra cseréli az útvonalat.

    Ha az abszolút útvonal már nem létezik (pl. törölt fájl, más gép),
    a photo mező üresre kerül, figyelmeztetés kíséretében.

    Visszaadja az érintett (migrált) projektek neveinek listáját.
    """
    storage = Storage()
    migrated: list[str] = []

    for project_dir in storage.list_projects(projects_dir):
        project = storage.read_project(project_dir)

        if not project.photo:
            continue

        photo_path = Path(project.photo)
        if not photo_path.is_absolute():
            continue  # már relatív, rendben van

        if not photo_path.exists():
            logger.warning(
                "Migráció: '%s' projekt cover fájlja nem található (%s) — photo mező ürítve.",
                project.name,
                photo_path,
            )
            project.photo = None
            storage.write_project(project)
            migrated.append(project.name)
            continue

        new_photo = storage.set_project_cover(project_dir, photo_path)
        project.photo = new_photo
        storage.write_project(project)
        logger.info(
            "Migráció: '%s' projekt cover-je bemásolva assets/-be (%s).",
            project.name,
            new_photo,
        )
        migrated.append(project.name)

    return migrated