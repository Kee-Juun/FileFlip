"""Regenerate the Windows ICO asset from FileFlip's code-native icon renderer."""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image
from PyQt6.QtWidgets import QApplication


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ui.fonts import load_theme_fonts  # noqa: E402
from ui.icons import ICON_SIZES, _render_icon  # noqa: E402


def main() -> int:
    app = QApplication.instance() or QApplication([])
    load_theme_fonts()

    source_path = PROJECT_ROOT / "assets" / "fileflip-icon.png"
    icon_path = PROJECT_ROOT / "assets" / "fileflip.ico"
    rendered = _render_icon(1024)
    if not rendered.save(str(source_path), "PNG"):
        raise RuntimeError(f"Could not save {source_path}")

    with Image.open(source_path) as source:
        source.save(icon_path, format="ICO", sizes=[(size, size) for size in ICON_SIZES])

    print(f"Saved {source_path}")
    print(f"Saved {icon_path}")
    del app
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
