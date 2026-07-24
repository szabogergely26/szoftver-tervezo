from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QVBoxLayout, QWidget

from config import APP_VERSION, BUILD_CHANNEL, ICON_PATH
from settings.translations import tr


class AboutDialog(QDialog):
    """Névjegy ablak – programnév, verzió, kiadási csatorna."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("about.title"))
        self.setFixedSize(360, 260)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        if ICON_PATH.exists():
            icon_label = QLabel()
            pixmap = QPixmap(str(ICON_PATH)).scaled(
                64,
                64,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            icon_label.setPixmap(pixmap)
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(icon_label)

        name_label = QLabel(tr("main.window_title"))
        name_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(name_label)

        version_label = QLabel(tr("about.version", version=APP_VERSION))
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version_label)

        channel_label = QLabel(self._channel_text())
        channel_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        channel_label.setStyleSheet("color: #888;")
        layout.addWidget(channel_label)

        layout.addStretch()

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)

    def _channel_text(self) -> str:
        if BUILD_CHANNEL == "dev":
            return tr("about.channel_dev")
        if BUILD_CHANNEL == "preview":
            return tr("about.channel_preview")
        return tr("about.channel_stable")