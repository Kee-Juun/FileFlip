"""Qt stylesheets and color themes for FileFlip."""

from __future__ import annotations

from collections.abc import Mapping
from enum import Enum

from .fonts import BODY_FONT_FAMILY


class Theme(Enum):
    """Available UI color themes."""

    LIGHT = "Light"
    DARK = "Dark"
    COFFEE = "Coffee"
    VIBRANT = "Vibrant"

    @classmethod
    def from_label(cls, label: str) -> "Theme":
        """Return the theme represented by a combo-box label."""
        for theme in cls:
            if theme.value == label:
                return theme
        raise ValueError(f"Unknown theme: {label}")


THEME_STYLESHEETS = {
    Theme.LIGHT: {
        "background": "#f5f7fb",
        "surface": "#ffffff",
        "surface_hover": "#f0f5ff",
        "text": "#111827",
        "muted": "#64748b",
        "border": "#dfe6f2",
        "button_border": "#d5deeb",
        "button_hover_border": "#b9c8dc",
        "primary": "#0a84ff",
        "primary_hover": "#006edc",
        "strong_button": "#111827",
        "strong_button_hover": "#253044",
        "strong_button_text": "#ffffff",
        "selection": "#e4f1ff",
        "row_border": "#edf1f6",
        "progress_track": "#e6ebf2",
        "success": "#12b981",
        "danger": "#ef4444",
        "disabled_bg": "#eef2f7",
        "disabled_text": "#9aa8ba",
        "log_text": "#1f2937",
        "checkbox": "#334155",
        "header_font": "Weghorst",
        "header_weight": "700",
        "decor_line": "#dfe6f2",
        "decor_1": "#d5deeb",
        "decor_2": "#dfe6f2",
        "decor_3": "#edf1f6",
    },
    Theme.DARK: {
        "background": "#0b1018",
        "surface": "#151b26",
        "surface_hover": "#1d2633",
        "text": "#f7f9fc",
        "muted": "#9da8b8",
        "border": "#293244",
        "button_border": "#354154",
        "button_hover_border": "#4b5c73",
        "primary": "#4da3ff",
        "primary_hover": "#6bb4ff",
        "strong_button": "#f4f6fb",
        "strong_button_hover": "#e2e8f0",
        "strong_button_text": "#0b1018",
        "selection": "#233a57",
        "row_border": "#222b3a",
        "progress_track": "#273244",
        "success": "#2fd18b",
        "danger": "#ff6b6b",
        "disabled_bg": "#202837",
        "disabled_text": "#657184",
        "log_text": "#dbe4f0",
        "checkbox": "#dbe4f0",
        "header_font": "Dicaten",
        "header_weight": "700",
        "decor_line": "#293244",
        "decor_1": "#354154",
        "decor_2": "#293244",
        "decor_3": "#222b3a",
    },
    Theme.COFFEE: {
        "background": "#f4ede4",
        "surface": "#fffaf2",
        "surface_hover": "#f2e1cc",
        "text": "#2b1f18",
        "muted": "#7a6655",
        "border": "#e3cfb8",
        "button_border": "#d5b99a",
        "button_hover_border": "#bd936a",
        "primary": "#b86b38",
        "primary_hover": "#985326",
        "strong_button": "#3a2417",
        "strong_button_hover": "#57351f",
        "strong_button_text": "#fff7ed",
        "selection": "#efd8be",
        "row_border": "#ead9c6",
        "progress_track": "#ead8c4",
        "success": "#5f9f6e",
        "danger": "#c2412d",
        "disabled_bg": "#eadfd4",
        "disabled_text": "#9f8974",
        "log_text": "#3a2a20",
        "checkbox": "#4b3628",
        "header_font": "Fraunces",
        "header_weight": "700",
        "decor_line": "#d0a077",
        "decor_1": "#7b4528",
        "decor_2": "#b86b38",
        "decor_3": "#d8b085",
    },
    Theme.VIBRANT: {
        "background": "#f5f2ff",
        "surface": "#ffffff",
        "surface_hover": "#fff1f8",
        "text": "#171124",
        "muted": "#665d7a",
        "border": "#ded6ff",
        "button_border": "#d3c7ff",
        "button_hover_border": "#b89dff",
        "primary": "#7c3aed",
        "primary_hover": "#6d28d9",
        "strong_button": "#ff4f8b",
        "strong_button_hover": "#e83e77",
        "strong_button_text": "#ffffff",
        "selection": "#efe7ff",
        "row_border": "#eee8ff",
        "progress_track": "#e5dcff",
        "success": "#00b884",
        "danger": "#f43f5e",
        "disabled_bg": "#eee9fb",
        "disabled_text": "#9a8eb4",
        "log_text": "#241a35",
        "checkbox": "#312244",
        "header_font": "Pacifico",
        "header_weight": "400",
        "decor_line": "#b89dff",
        "decor_1": "#ff4f8b",
        "decor_2": "#7c3aed",
        "decor_3": "#14b8a6",
    },
}


def colors_for(theme: Theme) -> Mapping[str, str]:
    """Return the color palette for ``theme``."""
    return THEME_STYLESHEETS[theme]


def combo_popup_stylesheet_for(theme: Theme) -> str:
    """Build a stylesheet for combo-box popup views.

    Qt creates combo popups as separate item views on some platforms. Styling
    those views directly keeps light-mode dropdown text readable even when the
    OS is using a dark application palette.
    """
    colors = colors_for(theme)
    return f"""
QAbstractItemView {{
    background: {colors["surface"]};
    border: 1px solid {colors["border"]};
    border-radius: 12px;
    color: {colors["text"]};
    font-family: "{BODY_FONT_FAMILY}";
    outline: 0;
    padding: 6px;
    selection-background-color: {colors["selection"]};
    selection-color: {colors["text"]};
}}

QAbstractItemView::item {{
    background: {colors["surface"]};
    color: {colors["text"]};
    min-height: 32px;
    padding: 6px 12px;
}}

QAbstractItemView::item:hover,
QAbstractItemView::item:selected {{
    background: {colors["selection"]};
    color: {colors["text"]};
}}
"""


def stylesheet_for(theme: Theme) -> str:
    """Build the Qt stylesheet for ``theme``."""
    colors = colors_for(theme)
    return f"""
QMainWindow {{
    background: {colors["background"]};
    color: {colors["text"]};
}}

QWidget {{
    font-family: "{BODY_FONT_FAMILY}";
    font-size: 10.5pt;
    color: {colors["text"]};
}}

QWidget#TitleBar {{
    background: transparent;
}}

QLabel#WindowBadge {{
    background: {colors["primary"]};
    border-radius: 7px;
    color: #ffffff;
    font-family: "{BODY_FONT_FAMILY}";
    font-size: 9pt;
    font-weight: 800;
}}

QLabel#WindowTitleText {{
    color: {colors["muted"]};
    font-family: "{BODY_FONT_FAMILY}";
    font-size: 9pt;
    font-weight: 700;
}}

QToolButton#TitleBarButton,
QToolButton#TitleBarCloseButton {{
    background: transparent;
    border: 0;
    border-radius: 9px;
    color: {colors["muted"]};
    font-family: "{BODY_FONT_FAMILY}";
    font-size: 12pt;
    min-height: 28px;
    min-width: 34px;
    max-width: 34px;
    padding: 0;
}}

QToolButton#TitleBarButton:hover {{
    background: {colors["surface_hover"]};
    color: {colors["text"]};
}}

QToolButton#TitleBarCloseButton:hover {{
    background: {colors["danger"]};
    color: #ffffff;
}}

QLabel#AppTitle {{
    color: {colors["text"]};
    font-family: "{colors["header_font"]}";
    font-size: 25pt;
    font-weight: {colors["header_weight"]};
}}

QLabel#MutedText {{
    font-family: "{BODY_FONT_FAMILY}";
    color: {colors["muted"]};
    font-size: 10pt;
}}

QFrame#ThemeAccentLine {{
    background: {colors["decor_line"]};
    border: 0;
    border-radius: 2px;
}}

QLabel#CounterText {{
    color: {colors["text"]};
    font-family: "{BODY_FONT_FAMILY}";
    font-size: 10pt;
    font-weight: 700;
}}

QFrame#Toolbar,
QFrame#BottomBar {{
    background: {colors["surface"]};
    border: 1px solid {colors["border"]};
    border-radius: 16px;
}}

QPushButton,
QToolButton {{
    font-family: "{BODY_FONT_FAMILY}";
    background: {colors["surface"]};
    border: 1px solid {colors["button_border"]};
    border-radius: 14px;
    color: {colors["text"]};
    min-height: 40px;
    padding: 6px 14px;
}}

QToolButton#IconButton {{
    min-width: 42px;
    max-width: 42px;
    padding: 6px;
}}

QToolButton#PillButton {{
    padding-left: 16px;
    padding-right: 16px;
}}

QPushButton:hover,
QToolButton:hover {{
    background: {colors["surface_hover"]};
    border-color: {colors["button_hover_border"]};
}}

QPushButton:disabled,
QToolButton:disabled {{
    background: {colors["disabled_bg"]};
    color: {colors["disabled_text"]};
}}

QPushButton#PrimaryButton {{
    background: {colors["primary"]};
    border-color: {colors["primary"]};
    color: #ffffff;
    font-weight: 700;
    min-width: 124px;
}}

QPushButton#PrimaryButton:hover {{
    background: {colors["primary_hover"]};
    border-color: {colors["primary_hover"]};
}}

QPushButton#PrimaryLiteButton {{
    background: {colors["strong_button"]};
    border-color: {colors["strong_button"]};
    color: {colors["strong_button_text"]};
    font-weight: 700;
    min-width: 92px;
}}

QPushButton#PrimaryLiteButton:hover {{
    background: {colors["strong_button_hover"]};
    border-color: {colors["strong_button_hover"]};
}}

QComboBox,
QLineEdit,
QPlainTextEdit,
QTableWidget {{
    font-family: "{BODY_FONT_FAMILY}";
    background: {colors["surface"]};
    border: 1px solid {colors["border"]};
    border-radius: 14px;
    color: {colors["text"]};
    selection-background-color: {colors["selection"]};
    selection-color: {colors["text"]};
}}

QComboBox,
QLineEdit {{
    min-height: 40px;
    padding: 5px 12px;
}}

QComboBox::drop-down {{
    border: 0;
    width: 34px;
}}

QComboBox QAbstractItemView {{
    background: {colors["surface"]};
    border: 1px solid {colors["border"]};
    border-radius: 12px;
    color: {colors["text"]};
    outline: 0;
    selection-background-color: {colors["selection"]};
    selection-color: {colors["text"]};
}}

QComboBox QAbstractItemView::item {{
    background: {colors["surface"]};
    color: {colors["text"]};
    min-height: 32px;
    padding: 6px 12px;
}}

QComboBox QAbstractItemView::item:hover,
QComboBox QAbstractItemView::item:selected {{
    background: {colors["selection"]};
    color: {colors["text"]};
}}

QCheckBox {{
    font-family: "{BODY_FONT_FAMILY}";
    color: {colors["checkbox"]};
    font-size: 10pt;
    spacing: 6px;
}}

QTableWidget#FileList {{
    border-radius: 16px;
    outline: 0;
}}

QTableWidget#FileList::item {{
    border-bottom: 1px solid {colors["row_border"]};
    padding: 8px 12px;
}}

QTableWidget#FileList::item:selected {{
    background: {colors["selection"]};
    color: {colors["text"]};
}}

QHeaderView {{
    font-family: "{BODY_FONT_FAMILY}";
    font-size: 9pt;
    font-weight: 600;
}}

QHeaderView::section {{
    background: {colors["surface"]};
    border: 0;
    border-bottom: 1px solid {colors["border"]};
    color: {colors["muted"]};
    font-family: "{BODY_FONT_FAMILY}";
    font-size: 9pt;
    font-weight: 600;
    padding: 10px 12px;
}}

QProgressBar {{
    background: {colors["progress_track"]};
    border: 0;
    border-radius: 5px;
    height: 10px;
}}

QProgressBar::chunk {{
    background: {colors["success"]};
    border-radius: 5px;
}}

QPlainTextEdit#LogView {{
    color: {colors["log_text"]};
    padding: 10px;
}}

QScrollBar:vertical {{
    background: transparent;
    border: 0;
    width: 10px;
    margin: 4px 2px 4px 2px;
}}

QScrollBar::handle:vertical {{
    background: {colors["button_border"]};
    border-radius: 5px;
    min-height: 32px;
}}

QScrollBar::handle:vertical:hover {{
    background: {colors["button_hover_border"]};
}}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical,
QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {{
    background: transparent;
    border: 0;
}}
"""
