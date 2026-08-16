"""Build-időben rögzített infó (commit hash, build dátum).

FONTOS: ezt a fájlt a build_deb.sh build közben FELÜLÍRJA egy statikus,
beégetett tartalommal (a build pillanatában érvényes commit hash + dátum).
Fejlesztői (dev) futtatásnál nincs ilyen felülírás, ezért ez a verzió
élőben, a helyi git repóból olvassa ki ugyanezt az infót - ha az sem
elérhető (pl. nincs .git mappa), "ismeretlen" jelenik meg a Névjegyben.

Ne szerkeszd kézzel telepített/csomagolt környezetben - a build_deb.sh
mindig felülírja.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


def _git_short_hash() -> str | None:
    try:
        repo_dir = Path(__file__).resolve().parent
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=repo_dir,
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass
    return None


def _git_commit_date() -> str | None:
    try:
        repo_dir = Path(__file__).resolve().parent
        result = subprocess.run(
            ["git", "log", "-1", "--format=%cd", "--date=short"],
            cwd=repo_dir,
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass
    return None


BUILD_COMMIT: str = _git_short_hash() or "ismeretlen"
BUILD_DATE: str = _git_commit_date() or "ismeretlen"