from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from settings.translations import tr

from ..core.models import TaskItem
from ..core.storage import Storage

# Feladat-státuszokhoz tartozó fordítás-kulcs, a checkbox melletti
# állapot-feliratához (pl. "(folyamatban)").
_STATUS_LABEL_KEYS = {
    "pending": "template_tasks.status_pending",
    "in_progress": "template_tasks.status_in_progress",
    "done": "template_tasks.status_done",
}


class TemplateTasksDialog(QDialog):
    """Checkboxos dialógus előre megírt "sablon" feladatok felvételéhez.

    A tételek listája a `sablon_feladatok.json` fájlból jön (l. Storage.
    read_template_tasks) — bővítéshez elég azt a JSON fájlt szerkeszteni,
    ez az osztály kódmódosítás nélkül felveszi az új tételeket.

    Azok a tételek, amelyek `template_id`-ja már szerepel a projekt
    feladatai között (bármilyen státuszban), letiltott checkbox-ként
    jelennek meg, az aktuális állapotukat jelző felirattal.
    """

    def __init__(
        self,
        parent: QWidget | None,
        storage: Storage,
        existing_tasks: list[TaskItem],
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("template_tasks.title"))
        self.resize(420, 380)

        # template_id -> feladat, a már felvett tételek gyors kereséséhez.
        existing_by_template_id = {
            t.template_id: t for t in existing_tasks if t.template_id
        }

        layout = QVBoxLayout(self)

        description = QLabel(tr("template_tasks.description"))
        description.setWordWrap(True)
        layout.addWidget(description)

        # template_id -> {"id", "title"}, a checkbox-okhoz tartozó tételekhez.
        self._items_by_id: dict[str, dict] = {}
        self._checkboxes: dict[str, QCheckBox] = {}

        for item in storage.read_template_tasks():
            template_id = item["id"]
            title = item["title"]

            checkbox = QCheckBox(title)
            existing = existing_by_template_id.get(template_id)

            if existing is not None:
                status_key = _STATUS_LABEL_KEYS.get(existing.status.value)
                status_label = tr(status_key) if status_key else existing.status.value
                checkbox.setText(f"{title}  ({status_label})")
                checkbox.setEnabled(False)
            else:
                self._items_by_id[template_id] = item
                self._checkboxes[template_id] = checkbox

            layout.addWidget(checkbox)

        layout.addStretch(1)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def selected_template_items(self) -> list[dict]:
        """A bepipált, nem letiltott tételek, eredeti {"id", "title"} alakban."""
        return [
            self._items_by_id[template_id]
            for template_id, checkbox in self._checkboxes.items()
            if checkbox.isChecked()
        ]
