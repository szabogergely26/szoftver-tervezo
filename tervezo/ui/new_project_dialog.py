from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QWidget,
)

from settings.translations import tr


class NewProjectDialog(QDialog):
    """'Új projekt' varázsló — a Film-Adatbázis 'Új bejegyzés' mintájára.

    Mezők:
      - Fotó (opcionális)
      - Név (kötelező)
      - Rövid leírás (nem kötelező, ajánlott)
      - Mire jó a program (kötelező) -> Áttekintés tab tartalma lesz
      - Kezdeti feladatok (soronként egy tétel) -> Következő feladatok
    """

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle(tr("new_project.title"))
        self.resize(440, 460)
        self._photo_path: Path | None = None

        layout = QFormLayout(self)

        photo_row = QHBoxLayout()
        self.photo_label = QLabel(tr("new_project.no_photo"))
        photo_btn = QPushButton(tr("common.browse_ellipsis"))
        photo_btn.clicked.connect(self._choose_photo)
        photo_row.addWidget(self.photo_label, 1)
        photo_row.addWidget(photo_btn)
        layout.addRow(tr("new_project.photo_label"), photo_row)

        self.name_edit = QLineEdit()
        layout.addRow(tr("new_project.name_label"), self.name_edit)

        self.description_edit = QLineEdit()
        layout.addRow(tr("new_project.description_label"), self.description_edit)

        self.purpose_edit = QPlainTextEdit()
        self.purpose_edit.setFixedHeight(90)
        layout.addRow(tr("new_project.purpose_label"), self.purpose_edit)

        self.tasks_edit = QPlainTextEdit()
        self.tasks_edit.setFixedHeight(90)
        self.tasks_edit.setPlaceholderText(tr("new_project.tasks_placeholder"))
        layout.addRow(tr("new_project.tasks_label"), self.tasks_edit)

        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: #d9534f;")
        self.error_label.setVisible(False)
        layout.addRow(self.error_label)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _choose_photo(self) -> None:
        # A dialógust csak a kattintás eseményének teljes lezárása UTÁN
        # nyitjuk meg (singleShot(0, ...)): ha a modális fájlválasztót
        # közvetlenül a "clicked" jelzésből, szinkron módon nyitjuk meg,
        # a Qt belső "egér alatti widget" nyomkövetése inkonzisztens
        # állapotba kerülhet a dialógus bezárásakor, ami natív
        # szegmentálási hibát okoz (dangling widget-mutató).
        QTimer.singleShot(0, self._open_photo_dialog)

    def _open_photo_dialog(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            tr("new_project.choose_photo_title"),
            "",
            tr("new_project.choose_photo_filter"),
            options=QFileDialog.Option.DontUseNativeDialog,
        )
        if path:
            self._photo_path = Path(path)
            self.photo_label.setText(self._photo_path.name)

    def _on_accept(self) -> None:
        name = self.name_edit.text().strip()
        purpose = self.purpose_edit.toPlainText().strip()
        if not name or not purpose:
            self.error_label.setText(tr("new_project.error_required"))
            self.error_label.setVisible(True)
            return
        self.accept()

    def get_result(self) -> dict | None:
        name = self.name_edit.text().strip()
        purpose = self.purpose_edit.toPlainText().strip()
        if not name or not purpose:
            return None
        return {
            "name": name,
            "description": self.description_edit.text().strip(),
            "purpose": purpose,
            "photo_source": self._photo_path,
            "initial_tasks_raw": self.tasks_edit.toPlainText(),
        }