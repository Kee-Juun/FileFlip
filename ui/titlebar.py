"""Custom frameless window title bar."""

from __future__ import annotations

from PyQt6.QtCore import QPoint, QPointF, Qt
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QSizeGrip, QSpacerItem, QSizePolicy, QToolButton, QWidget

from .icons import app_icon
from .themes import Theme, colors_for


class AppTitleBar(QWidget):
    """Small draggable title bar for the frameless app window."""

    def __init__(self, title: str) -> None:
        super().__init__()
        self._drag_start: QPoint | None = None
        self.setObjectName("TitleBar")
        self.setFixedHeight(34)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 0, 4, 0)
        layout.setSpacing(8)

        self.badge_label = QLabel()
        self.badge_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.badge_label.setFixedSize(22, 22)
        self.badge_label.setPixmap(app_icon().pixmap(22, 22))

        self.title_label = QLabel(title)
        self.title_label.setObjectName("WindowTitleText")

        self.minimize_button = self._make_button("−", "Minimize")
        self.maximize_button = self._make_button("□", "Maximize")
        self.close_button = self._make_button("×", "Close")
        self.close_button.setObjectName("TitleBarCloseButton")

        layout.addWidget(self.badge_label)
        layout.addWidget(self.title_label)
        layout.addItem(QSpacerItem(20, 1, QSizePolicy.Policy.Expanding))
        layout.addWidget(self.minimize_button)
        layout.addWidget(self.maximize_button)
        layout.addWidget(self.close_button)

        self.minimize_button.clicked.connect(lambda: self.window().showMinimized())
        self.maximize_button.clicked.connect(self._toggle_maximized)
        self.close_button.clicked.connect(lambda: self.window().close())

    def set_maximized(self, maximized: bool) -> None:
        """Refresh the maximize button for the current window state."""
        self.maximize_button.setText("❐" if maximized else "□")
        self.maximize_button.setToolTip("Restore" if maximized else "Maximize")

    def mouseDoubleClickEvent(self, event: object) -> None:
        """Toggle maximize on title-bar double click."""
        self._toggle_maximized()

    def mousePressEvent(self, event: object) -> None:
        """Begin dragging the frameless window."""
        if event.button() == Qt.MouseButton.LeftButton and not self.window().isMaximized():
            self._drag_start = event.globalPosition().toPoint() - self.window().frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: object) -> None:
        """Move the frameless window while dragging."""
        if self._drag_start is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.window().move(event.globalPosition().toPoint() - self._drag_start)
            event.accept()

    def mouseReleaseEvent(self, event: object) -> None:
        """End an active window drag."""
        self._drag_start = None
        event.accept()

    def _toggle_maximized(self) -> None:
        window = self.window()
        if window.isMaximized():
            window.showNormal()
        else:
            window.showMaximized()
        self.set_maximized(window.isMaximized())

    def _make_button(self, text: str, tooltip: str) -> QToolButton:
        button = QToolButton()
        button.setObjectName("TitleBarButton")
        button.setText(text)
        button.setToolTip(tooltip)
        button.setFixedSize(34, 28)
        return button


class CornerResizeGrip(QSizeGrip):
    """Subtle themed resize handle for the frameless window."""

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self._theme = Theme.LIGHT
        self.setFixedSize(16, 16)

    def set_theme(self, theme: Theme) -> None:
        """Refresh handle colors for the active theme."""
        self._theme = theme
        self.update()

    def paintEvent(self, event: object) -> None:
        colors = colors_for(self._theme)
        color = QColor(colors["muted"])
        color.setAlpha(125)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(color, 1.4)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)

        painter.drawLine(QPointF(12, 5), QPointF(5, 12))
        painter.drawLine(QPointF(14, 9), QPointF(9, 14))
