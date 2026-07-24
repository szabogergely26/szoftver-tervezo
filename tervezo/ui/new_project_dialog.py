from __future__ import annotations

from pathlib import Path

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
        self.setWindowTitle("Új projekt")
        self.resize(440, 460)
        self._photo_path: Path | None = None

        layout = QFormLayout(self)

        photo_row = QHBoxLayout()
        self.photo_label = QLabel("Nincs kiválasztva")
        photo_btn = QPushButton("Tallózás...")
        photo_btn.clicked.connect(self._choose_photo)
        photo_row.addWidget(self.photo_label, 1)
        photo_row.addWidget(photo_btn)
        layout.addRow("Fotó (opcionális):", photo_row)

        self.name_edit = QLineEdit()
        layout.addRow("Név *:", self.name_edit)

        self.description_edit = QLineEdit()
        layout.addRow("Rövid leírás (ajánlott):", self.description_edit)

        self.purpose_edit = QPlainTextEdit()
        self.purpose_edit.setFixedHeight(90)
        layout.addRow("Mire jó a program *:", self.purpose_edit)

        self.tasks_edit = QPlainTextEdit()
        self.tasks_edit.setFixedHeight(90)
        self.tasks_edit.setPlaceholderText("Egy sor = egy feladat")
        layout.addRow("Kezdeti feladatok:", self.tasks_edit)

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
        path, _ = QFileDialog.getOpenFileName(
            self, "Fotó kiválasztása", "", "Képek (*.png *.jpg *.jpeg *.webp)"
        )
        if path:
            self._photo_path = Path(path)
            self.photo_label.setText(self._photo_path.name)

    def _on_accept(self) -> None:
        name = self.name_edit.text().strip()
        purpose = self.purpose_edit.toPlainText().strip()
        if not name or not purpose:
            self.error_label.setText(
                "A Név és a 'Mire jó a program' mező kitöltése kötelező."
            )
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
