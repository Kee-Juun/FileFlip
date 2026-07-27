"""Small OS integration helpers."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def open_folder(path: Path) -> None:
    """Open ``path`` in the user's file manager."""
    if sys.platform == "win32":
        os.startfile(path)
        return

    command = "open" if sys.platform == "darwin" else "xdg-open"
    subprocess.Popen(
        [command, str(path)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
