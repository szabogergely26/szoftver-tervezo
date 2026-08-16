from __future__ import annotations

import sys

from PySide6 import __version__ as PYSIDE_VERSION
from PySide6.QtCore import Qt
from PySide6.QtGui import QDesktopServices, QPixmap
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QVBoxLayout, QWidget

from config import APP_VERSION, BUILD_CHANNEL, BUILD_COMMIT, BUILD_DATE, ICON_PATH
from settings.translations import tr

DEVELOPER_NAME = "Szabó Gergely"
DEVELOPER_URL = "https://github.com/szabogergely26"


class AboutDialog(QDialog):
    """Névjegy ablak – programnév, verzió, kiadási csatorna."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("about.title"))
        self.setFixedSize(360, 340)

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

        developer_label = QLabel(
            f'<a href="{DEVELOPER_URL}">'
            f"{tr('about.developer', name=DEVELOPER_NAME)}</a>"
        )
        developer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        developer_label.setOpenExternalLinks(False)
        developer_label.linkActivated.connect(
            lambda url: QDesktopServices.openUrl(url)
        )
        layout.addWidget(developer_label)

        build_label = QLabel(
            tr("about.build_info", commit=BUILD_COMMIT, date=BUILD_DATE)
        )
        build_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        build_label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(build_label)

        tech_label = QLabel(
            tr(
                "about.tech_info",
                python_version=(
                    f"{sys.version_info.major}."
                    f"{sys.version_info.minor}."
                    f"{sys.version_info.micro}"
                ),
                pyside_version=PYSIDE_VERSION,
            )
        )
        tech_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tech_label.setStyleSheet("color: #888; font-size: 11px;")
        layout.addWidget(tech_label)

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