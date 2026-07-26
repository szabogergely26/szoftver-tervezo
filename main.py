import faulthandler
import os
import sys

# A rendszer KDE platform-téma pluginja (pl. KDEPlasmaPlatformTheme6.so) a
# disztribúció Qt6 verziójához készült, ami eltérhet a PySide6 csomagba
# ágyazott Qt6 futtatókörnyezet verziójától. A kettő közötti ABI-eltérés
# natív szegmentálási hibát okoz induláskor, ezért letiltjuk a rendszer
# platform-téma integrációját, mielőtt a QApplication létrejönne.
os.environ.setdefault("QT_QPA_PLATFORMTHEME", "")

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from config import APP_VERSION, BUILD_CHANNEL, ICON_PATH
from settings import apply_saved_language
from tervezo.ui.main_window import MainWindow

from settings.settings import get_log_level
from tervezo.core.app_logging import (
    LOG_DIR,
    LOG_FILE,
    log_header,
    log_raw,
    logging,
    setup_logging,
    CRASH_LOG,
)

LOG_DIR.mkdir(parents=True, exist_ok=True)
faulthandler.enable(file=open(CRASH_LOG, "a"))

setup_logging(get_log_level())

SEPARATOR = "=" * 120


log_raw(SEPARATOR)
log_header("Tervező - alkalmazás indul")
log_raw(f"log file: {LOG_FILE}")
log_raw(SEPARATOR)
logging.info(f"Build channel: {BUILD_CHANNEL}")
logging.info(f"Verzió: {APP_VERSION}")

def main() -> int:
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    logging.info("QApplication létrejött")

    app.setWindowIcon(QIcon(str(ICON_PATH)))  # ez adja a tálca-/taskbar-ikont
    
    logging.info("Nyelv alkalmazva, MainWindow létrehozása előtt")
    
    apply_saved_language()

    

    win = MainWindow()
    logging.info("MainWindow létrejött, show() hívás előtt")
    win.show()
    logging.info("show() hívás megtörtént, eseményhurok indul")
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
