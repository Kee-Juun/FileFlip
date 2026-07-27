"""Application font loading."""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtGui import QFontDatabase


BODY_FONT_FAMILY = "Segoe UI"


FONT_FILES = (
    "Weghorst-Italic.otf",
    "Dicaten Demo.otf",
    "Fraunces.ttf",
    "Pacifico-Regular.ttf",
)


def load_theme_fonts() -> None:
    """Register bundled theme fonts with Qt."""
    assets_dir = Path(__file__).resolve().parent.parent / "assets"
    for filename in FONT_FILES:
        path = assets_dir / filename
        if path.exists():
            QFontDatabase.addApplicationFont(str(path))
