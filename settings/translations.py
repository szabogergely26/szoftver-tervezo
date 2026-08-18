"""Egyszerű fordítási réteg – kulcs alapú szótár, HU/EN nyelvekkel.

Nyelvváltáskor a `language_changed` szignál jelez minden élő ablaknak,
hogy frissítse a saját szövegeit (retranslate_ui), így nem kell
újraindítani az alkalmazást ahhoz, hogy a nyelvváltás érvényre jusson.
"""

from __future__ import annotations

from PySide6.QtCore import QObject, Signal

# Az aktuálisan kiválasztott nyelv (alapértelmezetten magyar)
_current_language = "hu"


class _LanguageSignal(QObject):
    changed = Signal(str)


# Modulszintű, egyetlen példány – erre lehet feliratkozni bárhonnan:
#   from settings.translations import language_signal
#   language_signal.changed.connect(self.retranslate_ui)
language_signal = _LanguageSignal()


_TRANSLATIONS: dict[str, dict[str, str]] = {
    # --- Beállítások ablak ---
    "settings.title": {"hu": "Beállítások", "en": "Settings"},
    "settings.category.general": {"hu": "Általános", "en": "General"},
    "settings.category.appearance": {"hu": "Megjelenés", "en": "Appearance"},
    "settings.category.language": {"hu": "Nyelv", "en": "Language"},

    "settings.category.tasks": {"hu": "Feladatok", "en": "Tasks"},
        "settings.general.view_mode.label": {
            "hu": "Projekt megnyitás módja:",
            "en": "Project open mode:",
        },

    "settings.language.label": {"hu": "Nyelv:", "en": "Language:"},
    "settings.language.hungarian": {"hu": "Magyar", "en": "Hungarian"},
    "settings.language.english": {"hu": "English", "en": "English"},
    "settings.placeholder.general": {
        "hu": "Általános beállítások – hamarosan.",
        "en": "General settings – coming soon.",
    },
    "settings.placeholder.appearance": {
        "hu": "Megjelenés (téma, stb.) – hamarosan.",
        "en": "Appearance (theme, etc.) – coming soon.",
    },
    "settings.placeholder.tasks": {
        "hu": "Feladatok háttérszolgáltatás és értesítések – hamarosan.\n(pl. email értesítés :D)",
        "en": "Task background service and notifications – coming soon.\n(e.g. email notifications :D)",
    },


    "settings.category.sidebar_mode": {"hu": "Oldalsáv", "en": "Sidebar"},

    
    "settings.general.view_mode.dialog": {"hu": "Ablak", "en": "Window"},
    "settings.general.view_mode.sidebar": {"hu": "Oldalsáv", "en": "Sidebar"},



    # --- Általános ---
    "common.ok": {"hu": "OK", "en": "OK"},
    "common.cancel": {"hu": "Mégsem", "en": "Cancel"},
    "common.add": {"hu": "Hozzáadás", "en": "Add"},
    "common.add_ellipsis": {"hu": "Hozzáadás...", "en": "Add..."},
    "common.delete": {"hu": "Törlés", "en": "Delete"},
    "common.edit": {"hu": "Szerkesztés", "en": "Edit"},
    "common.save": {"hu": "Mentés", "en": "Save"},
    "common.close": {"hu": "Bezárás", "en": "Close"},
    "common.browse_ellipsis": {"hu": "Tallózás...", "en": "Browse..."},
    "common.custom_color_ellipsis": {"hu": "Egyéni szín...", "en": "Custom color..."},
    "common.date_placeholder": {"hu": "ÉÉÉÉ.HH.NN", "en": "YYYY.MM.DD"},
    "common.exists_title": {"hu": "Létezik", "en": "Already exists"},
    "project.close_discard_button": {"hu": "Elvetés", "en": "Discard"},
    "common.details": {"hu": "Részletek", "en": "Details"},
    "widgets.task_title_label": {"hu": "Cím:", "en": "Title:"},

    # ----------- Főablak ---------------
    "main.window_title": {"hu": "Szoftver-Tervező", "en": "Software-Designer"},
    "main.menu.file": {"hu": "Fájl", "en": "File"},
    "main.menu.help": {"hu": "Súgó", "en": "Help"},
    "main.action.new_project": {"hu": "Új projekt", "en": "New project"},
    "main.action.new_project_toolbar": {"hu": "+ Új projekt", "en": "+ New project"},
    "main.status_bar.next_task": {"hu": "Következő feladat", "en": "Next task"},

    # --- Megnyitás / Mentés / Beállítások
    "main.action.open": {"hu": "Megnyitás", "en": "Open"},
    "main.action.save": {"hu": "Mentés", "en": "Save"},


    # ------------ Munkaterület import/export
    "main.action.import_workspace": {"hu": "Importálás...", "en": "Import..."},
    "main.action.export_workspace": {"hu": "Exportálás...", "en": "Export..."},

    "main.export_error_title": {"hu": "Exportálási hiba", "en": "Export error"},
    "main.export_done_title": {"hu": "Exportálás kész", "en": "Export complete"},
    "main.export_done_text": {
        "hu": "A munkaterület mentése elkészült:\n{path}",
        "en": "Workspace export completed:\n{path}",
    },

    "main.import_error_title": {"hu": "Importálási hiba", "en": "Import error"},
    "main.import_conflict_title": {"hu": "Ütköző projektek", "en": "Conflicting projects"},
    "main.import_conflict_text": {
        "hu": "A következő projektek már léteznek, és felülíródnak:\n\n{names}\n\nFolytatod?",
        "en": "The following projects already exist and will be overwritten:\n\n{names}\n\nContinue?",
    },
    "main.import_done_title": {"hu": "Importálás kész", "en": "Import complete"},
    "main.import_done_text": {
        "hu": "A munkaterület visszaállítása megtörtént.",
        "en": "Workspace import completed.",
    },

    # Ütköző nevek:
    "main.import_extra_title": {"hu": "Nem importált, meglévő projektek", "en": "Existing projects not in the import"},
    "main.import_extra_text": {
        "hu": "A következő projektek megvannak nálad, de nem szerepelnek a most importált mentésben:\n\n{names}\n\nMegtartsuk őket (Igen), vagy töröljük (Nem)?",
        "en": "The following projects exist locally but are not part of this import:\n\n{names}\n\nKeep them (Yes) or delete them (No)?",
    },






    # --- Beállítások
    "main.action.settings": {"hu": "Beállítások", "en": "Settings"},

    # --- Kilépés
    "main.action.quit": {"hu": "Kilépés", "en": "Quit"},



    "main.toolbar.name": {"hu": "Eszköztár", "en": "Toolbar"},
    "main.project_exists": {
        "hu": "Már van ilyen nevű projekt.",
        "en": "A project with this name already exists.",
    },

    # -- Névjegy / About
    "main.action.about": {"hu": "Névjegy", "en": "About"},

    "main.sidebar.placeholder": {
        "hu": "Válassz egy projektet a bal oldali listából.",
        "en": "Select a project from the list on the left.",
    },



    # --- Eszközök , Napló ---
    "main.menu.tools": {"hu": "Eszközök", "en": "Tools"},
    "main.action.open_log": {"hu": "Napló megnyitása…", "en": "Open log…"},


    



    # --- Névjegy ---
    "about.title": {"hu": "Névjegy", "en": "About"},
    "about.version": {"hu": "Verzió: {version}", "en": "Version: {version}"},
    "about.channel_dev": {"hu": "Fejlesztői build (DEV)", "en": "Development build (DEV)"},
    "about.channel_preview": {"hu": "Előzetes build (Preview)", "en": "Preview build"},
    "about.channel_stable": {"hu": "Stabil kiadás", "en": "Stable release"},
    "about.developer": {"hu": "Fejlesztő: {name}", "en": "Developer: {name}"},
    "about.build_info": {
        "hu": "Build: {commit} ({date})",
        "en": "Build: {commit} ({date})",
    },
    "about.tech_info": {
        "hu": "Python {python_version} · PySide6 {pyside_version}",
        "en": "Python {python_version} · PySide6 {pyside_version}",
    },



    # --- Új projekt dialógus ---
    "new_project.title": {"hu": "Új projekt", "en": "New project"},
    "new_project.no_photo": {"hu": "Nincs kiválasztva", "en": "None selected"},
    "new_project.photo_label": {"hu": "Fotó (opcionális):", "en": "Photo (optional):"},
    "new_project.name_label": {"hu": "Név *:", "en": "Name *:"},
    "new_project.description_label": {
        "hu": "Rövid leírás (ajánlott):",
        "en": "Short description (recommended):",
    },
    "new_project.purpose_label": {
        "hu": "Mire jó a program *:",
        "en": "What is the program for *:",
    },
    "new_project.tasks_label": {"hu": "Kezdeti feladatok:", "en": "Initial tasks:"},
    "new_project.tasks_placeholder": {
        "hu": "Egy sor = egy feladat",
        "en": "One line = one task",
    },
    "new_project.error_required": {
        "hu": "A Név és a 'Mire jó a program' mező kitöltése kötelező.",
        "en": "The Name and 'What is the program for' fields are required.",
    },
    "new_project.choose_photo_title": {
        "hu": "Fotó kiválasztása",
        "en": "Choose photo",
    },
    "new_project.choose_photo_filter": {
        "hu": "Képek (*.png *.jpg *.jpeg *.webp)",
        "en": "Images (*.png *.jpg *.jpeg *.webp)",
    },

    # --- Projekt-részletek dialógus ---
    "project.tab.overview": {"hu": "Áttekintés", "en": "Overview"},
    "project.tab.journal": {"hu": "Napló", "en": "Journal"},
    "project.tab.next_tasks": {"hu": "Következő feladatok", "en": "Upcoming tasks"},
    "project.tab.in_progress_tasks": {"hu": "Folyamatban lévő feladatok", "en": "In-progress tasks"},
    "project.tab.done_tasks": {"hu": "Elkészült feladatok", "en": "Completed tasks"},

    "project.purpose_label": {"hu": "Mire jó a program:", "en": "What is the program for:"},
    "project.description_label": {
        "hu": "Rövid leírás (kártyán):",
        "en": "Short description (on card):",
    },
    "project.status_label": {"hu": "Státusz:", "en": "Status:"},
    "project.start_date_label": {"hu": "Kezdés dátuma:", "en": "Start date:"},
    "project.end_date_label": {"hu": "Befejezés dátuma:", "en": "End date:"},
    "project.milestones_label": {"hu": "Mérföldkövek:", "en": "Milestones:"},
    "project.new_journal_entry": {
        "hu": "Új bejegyzés (mai dátum)",
        "en": "New entry (today's date)",
    },
    "project.new_task_placeholder": {
        "hu": "Új feladat szövege...",
        "en": "New task text...",
    },
    "project.delete_confirm_title": {
        "hu": "Törlés megerősítése",
        "en": "Confirm deletion",
    },
    "project.delete_confirm_text": {
        "hu": "Biztosan törlöd a(z) „{name}” projektet és minden tartalmát?\n\nEz nem vonható vissza.",
        "en": "Are you sure you want to delete the project “{name}” and all its contents?\n\nThis cannot be undone.",
    },


    "project.close_confirm_title": {
        "hu": "Mentetlen módosítások",
        "en": "Unsaved changes",
    },
    "project.close_confirm_text": {
        "hu": "El szeretnéd menteni a módosításokat, mielőtt bezárod?",
        "en": "Do you want to save your changes before closing?",
    },



    # --- Lebegő szín-magyarázó eszköztár -----
    "status_legend.collapse": {"hu": "Összecsukás", "en": "Collapse"},
    "status_legend.expand": {"hu": "Kibontás", "en": "Expand"},
    "status_legend.close": {"hu": "Elrejtés", "en": "Hide"},
    "main.action.show_status_legend": {"hu": "Színmagyarázat mutatása", "en": "Show color legend"},










    "project.details_title": {"hu": "Részletek – {name}", "en": "Details – {name}"},

    # --- Projekt-státusz ---
    "status.not_started": {"hu": "El sincs kezdve", "en": "Not started"},
    "status.in_progress": {"hu": "Folyamatban", "en": "In progress"},
    "status.done": {"hu": "Kész", "en": "Done"},

    # --- Feladat-sor / mérföldkő / szerkesztés widgetek ---
    "widgets.milestone_title": {"hu": "Mérföldkő", "en": "Milestone"},
    "widgets.milestone_date_label": {"hu": "Dátum:", "en": "Date:"},
    "widgets.milestone_name_label": {"hu": "Cím:", "en": "Title:"},
    "widgets.milestone_description_label": {"hu": "Leírás:", "en": "Description:"},
    "widgets.task_edit_title": {"hu": "Feladat szerkesztése", "en": "Edit task"},

    "project.task.start": {"hu": "Elkezdés", "en": "Start"},



    # --- Formázó eszköztár ---
    "toolbar.bold": {"hu": "Félkövér", "en": "Bold"},
    "toolbar.italic": {"hu": "Dőlt", "en": "Italic"},
    "toolbar.underline": {"hu": "Aláhúzott", "en": "Underline"},
    "toolbar.highlight": {"hu": "Kiemelés", "en": "Highlight"},
    "toolbar.text_color": {"hu": "Betűszín", "en": "Text color"},
    "toolbar.font_size": {"hu": "Betűméret", "en": "Font size"},



    # --- Tálcaikon ---
    "main.tray.open": {"hu": "Megnyitás", "en" : "Open"},
    "main.tray.in_progress" : {"hu": "Folyamatban lévő feladatok", "en": "Tasks in progress"},
    "main.tray.next": {"hu": "Következő feladatok", "en": "Next Tasks"},
    "main.tray.empty": {"hu": "Nincs ilyen feladat", "en": "There is no such Task"},
    "main.tray.minimized_message": {"hu": "Kicsinyítve", "en": "Minimized"},
    "general.close_to_tray": {"hu": "Bezáráskor tálcára kicsinyítés (kilépés helyett)", "en": "Minimize to tray on close (instead of quitting)"},




    # --- Status bar ---
    "main.status_bar.popup_empty": {"hu": "Nincs hátralévő feladat.", "en": "No remaining tasks."},


    "main.status_bar.popup_title": {
    "hu": "Következő feladatok",
    "en": "Upcoming tasks",
    },

    "main.status_bar.in_progress": {"hu": "Folyamatban:", "en" : "In progress"},








}


    












def set_language(lang_code: str) -> None:
    """Beállítja az aktuális nyelvet ('hu' vagy 'en').

    Ha ez ténylegesen megváltoztatja a nyelvet, kibocsátja a
    `language_signal.changed` szignált, hogy az élő ablakok
    frissíthessék a szövegeiket (retranslate_ui).
    """
    global _current_language
    if lang_code not in ("hu", "en"):
        raise ValueError(f"Ismeretlen nyelvkód: {lang_code}")
    if lang_code != _current_language:
        _current_language = lang_code
        language_signal.changed.emit(lang_code)


def get_language() -> str:
    """Visszaadja az aktuálisan beállított nyelvkódot."""
    return _current_language


def tr(key: str, **kwargs: str) -> str:
    """Visszaadja a kulcshoz tartozó szöveget az aktuális nyelven.

    Ha a kulcs nem található, magát a kulcsot adja vissza (így azonnal
    látszik a hiányzó fordítás, nem áll le a program).

    `kwargs`-al egyszerű `{placeholder}` behelyettesítés is végezhető,
    pl. tr("project.details_title", name="Valami") -> "Részletek – Valami".
    """

    entry = _TRANSLATIONS.get(key)
    if entry is None:
        return key
    text = entry.get(_current_language, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError):
            return text
    return text



    