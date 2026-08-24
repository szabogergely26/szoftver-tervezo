#!/usr/bin/env bash
# reset_done_tasks.sh
#
# Dev-eszköz: egy kiválasztott projekt "Elkészült feladatok" (DONE státuszú)
# tételeinek törlése, teszteléshez.
#
# Csak a dev-csatorna adatait célozza (a repó gyökere alatti Projektek/projects
# mappát) - a telepített (.deb) verzió ~/.config alatti adatait NEM érinti.
#
# Futtatás a repó gyökeréből:
#   ./reset_done_tasks.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PYTHON_BIN="python3"
if [ -x ".venv/bin/python" ]; then
    PYTHON_BIN=".venv/bin/python"
fi

"$PYTHON_BIN" -m dev_tools._reset_done_tasks

