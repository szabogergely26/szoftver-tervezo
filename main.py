import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from config import ICON_PATH
from tervezo.ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(str(ICON_PATH)))  # ez adja a tálca-/taskbar-ikont

    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
