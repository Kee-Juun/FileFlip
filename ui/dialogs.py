"""Theme-aware message dialogs for FileFlip."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QPalette
from PyQt6.QtWidgets import QMessageBox, QWidget

from .fonts import BODY_FONT_FAMILY
from .themes import Theme, colors_for


def ask_ok_cancel(
    parent: QWidget,
    theme: Theme,
    title: str,
    text: str,
    ok_text: str = "OK",
    cancel_text: str = "Cancel",
) -> bool:
    """Show a themed OK/Cancel question dialog and return whether OK was chosen."""
    response = show_message(
        parent=parent,
        theme=theme,
        icon=QMessageBox.Icon.Question,
        title=title,
        text=text,
        buttons=QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
        default_button=QMessageBox.StandardButton.Ok,
        ok_text=ok_text,
        cancel_text=cancel_text,
    )
    return response == QMessageBox.StandardButton.Ok


def show_warning(parent: QWidget, theme: Theme, title: str, text: str) -> QMessageBox.StandardButton:
    """Show a themed warning dialog."""
    return show_message(
        parent=parent,
        theme=theme,
        icon=QMessageBox.Icon.Warning,
        title=title,
        text=text,
    )


def show_information(parent: QWidget, theme: Theme, title: str, text: str) -> QMessageBox.StandardButton:
    """Show a themed information dialog."""
    return show_message(
        parent=parent,
        theme=theme,
        icon=QMessageBox.Icon.Information,
        title=title,
        text=text,
    )


def show_message(
    parent: QWidget,
    theme: Theme,
    icon: QMessageBox.Icon,
    title: str,
    text: str,
    buttons: QMessageBox.StandardButton = QMessageBox.StandardButton.Ok,
    default_button: QMessageBox.StandardButton = QMessageBox.StandardButton.Ok,
    ok_text: str = "Got it",
    cancel_text: str = "Cancel",
) -> QMessageBox.StandardButton:
    """Show a QMessageBox with explicit palette and stylesheet colors."""
    dialog = QMessageBox(parent)
    dialog.setIcon(icon)
    dialog.setWindowTitle(title)
    dialog.setText(text)
    dialog.setTextFormat(Qt.TextFormat.PlainText)
    dialog.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    dialog.setStandardButtons(buttons)
    dialog.setDefaultButton(default_button)
    dialog.setMinimumWidth(520)
    apply_dialog_theme(dialog, theme)
    if ok_button := dialog.button(QMessageBox.StandardButton.Ok):
        ok_button.setText(ok_text)
    if cancel_button := dialog.button(QMessageBox.StandardButton.Cancel):
        cancel_button.setText(cancel_text)
    return QMessageBox.StandardButton(dialog.exec())


def apply_dialog_theme(dialog: QMessageBox, theme: Theme) -> None:
    """Apply readable colors to dialog body, labels, icons, and buttons."""
    colors = colors_for(theme)
    body_font = QFont(BODY_FONT_FAMILY, 10)
    dialog.setFont(body_font)

    palette = dialog.palette()
    palette.setColor(QPalette.ColorRole.Window, QColor(colors["surface"]))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(colors["text"]))
    palette.setColor(QPalette.ColorRole.Base, QColor(colors["surface"]))
    palette.setColor(QPalette.ColorRole.Text, QColor(colors["text"]))
    palette.setColor(QPalette.ColorRole.Button, QColor(colors["surface_hover"]))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(colors["text"]))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(colors["selection"]))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(colors["text"]))
    dialog.setPalette(palette)

    dialog.setStyleSheet(
        f"""
        QMessageBox {{
            background-color: {colors["surface"]};
            color: {colors["text"]};
            font-family: "{BODY_FONT_FAMILY}";
        }}

        QMessageBox QWidget {{
            background-color: {colors["surface"]};
            color: {colors["text"]};
            font-family: "{BODY_FONT_FAMILY}";
        }}

        QMessageBox QLabel {{
            background: transparent;
            color: {colors["text"]};
            font-family: "{BODY_FONT_FAMILY}";
            font-size: 10.5pt;
        }}

        QMessageBox QLabel#qt_msgbox_label {{
            min-width: 420px;
        }}

        QMessageBox QPushButton {{
            background: {colors["surface"]};
            border: 1px solid {colors["button_border"]};
            border-radius: 14px;
            color: {colors["text"]};
            font-family: "{BODY_FONT_FAMILY}";
            min-height: 40px;
            min-width: 88px;
            padding: 6px 16px;
        }}

        QMessageBox QPushButton:hover {{
            background: {colors["surface_hover"]};
            border-color: {colors["button_hover_border"]};
        }}
        """
    )
