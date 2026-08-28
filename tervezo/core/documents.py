from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

from PySide6.QtCore import QFileInfo
from PySide6.QtWidgets import QFileIconProvider

from .models import Project
from .storage import Storage

logger = logging.getLogger(__name__)


@dataclass
class PendingDocumentChanges:
    """A Dokumentumok tabon még el nem mentett módosítások.

    A UI ezt az objektumot bővíti (add/remove/rename hívásokkal), a
    tényleges fájlrendszeri műveletek és a Project.documents frissítése
    csak commit_pending_documents() hívásakor történik meg (Mentés gomb).

    additions: {cél_fájlnév: forrás_abszolút_útvonal} - még nem másolt fájlok
    removals: törlendő fájlnevek (meglévő, már mentett dokumentumok)
    renames: {régi_fájlnév: új_fájlnév} - meglévő dokumentumok átnevezése

    A UI-listában megjelenő állapot mindig
    effective_document_list()-ből számolható, a pending változások és a
    project.documents jelenlegi tartalma alapján - nem kell külön nyilván
    tartani.
    """

    additions: dict[str, Path] = field(default_factory=dict)
    removals: set[str] = field(default_factory=set)
    renames: dict[str, str] = field(default_factory=dict)

    def has_changes(self) -> bool:
        return bool(self.additions or self.removals or self.renames)

    def reset(self) -> None:
        self.additions.clear()
        self.removals.clear()
        self.renames.clear()


def effective_document_list(
    project: Project, pending: PendingDocumentChanges
) -> list[str]:
    """A Dokumentumok tab listájában megjelenítendő fájlnevek, a mentett
    project.documents és a még el nem mentett pending változások alapján.
    """
    names = list(project.documents)

    for old_name, new_name in pending.renames.items():
        if old_name in names:
            names[names.index(old_name)] = new_name

    names = [n for n in names if n not in pending.removals]

    for new_name in pending.additions:
        if new_name not in names:
            names.append(new_name)

    return names


def request_add_document(
    pending: PendingDocumentChanges,
    project: Project,
    source_file: Path,
    *,
    overwrite: bool = False,
    target_name: str | None = None,
) -> str:
    """Dokumentum hozzáadásának bejegyzése a pending listába (nincs azonnali fájlművelet).

    A cél fájlnév alapesetben a forrás fájl neve, de target_name-mel
    felülírható (pl. ütközés-feloldáskor a felhasználó más nevet adott meg).

    FileExistsError-t dob, ha a célnév már szerepel az effektív listában
    (meglévő vagy másik pending dokumentum) és overwrite=False.
    """
    target = target_name or source_file.name
    existing = effective_document_list(project, pending)
    if target in existing and not overwrite:
        raise FileExistsError(target)
    pending.additions[target] = source_file
    return target


def request_remove_document(
    pending: PendingDocumentChanges, project: Project, filename: str
) -> None:
    """Dokumentum törlésének bejegyzése a pending listába."""
    if filename in pending.additions:
        # Még nem mentett, csak pending hozzáadás volt -> egyszerűen elvetjük.
        del pending.additions[filename]
        return

    # Ha épp egy átnevezés célja volt, azt a bejegyzést is töröljük -
    # a régi nevet kell majd ténylegesen törölni mentéskor.
    original_name = next(
        (old for old, new in pending.renames.items() if new == filename), filename
    )
    pending.renames.pop(original_name, None)
    if original_name in project.documents:
        pending.removals.add(original_name)


def request_rename_document(
    pending: PendingDocumentChanges,
    project: Project,
    current_filename: str,
    new_filename: str,
    *,
    overwrite: bool = False,
) -> str:
    """Dokumentum átnevezésének bejegyzése a pending listába.

    FileExistsError-t dob, ha az új név már foglalt (és overwrite=False).
    current_filename az éppen a UI-listában látható (effektív) név lehet -
    ha az egy korábbi pending átnevezés eredménye, a láncot összevonjuk.
    """
    existing = [
        n for n in effective_document_list(project, pending) if n != current_filename
    ]
    if new_filename in existing and not overwrite:
        raise FileExistsError(new_filename)

    if current_filename in pending.additions:
        # Még nem mentett fájl -> csak a pending célnevet módosítjuk.
        source = pending.additions.pop(current_filename)
        pending.additions[new_filename] = source
        return new_filename

    original_name = next(
        (old for old, new in pending.renames.items() if new == current_filename),
        current_filename,
    )
    if original_name == new_filename:
        pending.renames.pop(original_name, None)
    else:
        pending.renames[original_name] = new_filename
    return new_filename


def commit_pending_documents(
    storage: Storage, project: Project, pending: PendingDocumentChanges
) -> None:
    """A pending add/remove/rename műveletek végrehajtása a lemezen,
    majd a Project.documents lista frissítése. A project.json mentését
    (write_project) a hívó (ProjectDetailsWidget._on_save) végzi el,
    ugyanabban a mentés-menetben, mint a többi tabot.
    """
    for old_name, new_name in pending.renames.items():
        try:
            storage.rename_document(project.path, old_name, new_name, overwrite=True)
        except FileNotFoundError:
            logger.warning(
                "Mentéskor átnevezendő dokumentum nem található: %s -> %s",
                old_name,
                new_name,
            )
            continue
        if old_name in project.documents:
            project.documents[project.documents.index(old_name)] = new_name

    for filename in pending.removals:
        storage.remove_document(project.path, filename)
        if filename in project.documents:
            project.documents.remove(filename)

    for target_name, source_path in pending.additions.items():
        storage.add_document(
            project.path, source_path, overwrite=True, target_name=target_name
        )
        if target_name not in project.documents:
            project.documents.append(target_name)

    pending.reset()


def get_document_icon(filename: str):
    """Típus-ikon egy dokumentumhoz, a rendszer natív ikonkészletéből.

    Jelenleg QFileIconProvider-t használ (kiterjesztés alapján natív ikon).
    Ha később saját SVG-/emoji-készletre váltanál, csak ezt a függvényt
    kell átírni - a UI-kód innentől nem tud a forrásról.
    """
    provider = QFileIconProvider()
    return provider.icon(QFileInfo(filename))
