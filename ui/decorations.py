"""Integrated theme skin artwork for FileFlip."""

from __future__ import annotations

from PyQt6.QtCore import QPointF, QRectF, QSize, Qt
from PyQt6.QtGui import QColor, QLinearGradient, QPainter, QPainterPath
from PyQt6.QtWidgets import QSizePolicy, QWidget

from .themes import Theme, colors_for


class ThemeSurface(QWidget):
    """Central surface that paints subtle theme artwork behind the UI."""

    def __init__(self) -> None:
        super().__init__()
        self._theme = Theme.LIGHT
        self.setAutoFillBackground(False)

    def set_theme(self, theme: Theme) -> None:
        """Apply the active theme artwork."""
        self._theme = theme
        self.update()

    def paintEvent(self, event: object) -> None:
        painter = _make_painter(self)
        colors = colors_for(self._theme)
        painter.fillRect(self.rect(), QColor(colors["background"]))

        if self._theme is Theme.LIGHT:
            _paint_light_surface(painter, self.width(), self.height())
        elif self._theme is Theme.DARK:
            _paint_dark_surface(painter, self.width(), self.height())
        elif self._theme is Theme.COFFEE:
            _paint_coffee_surface(painter, self.width(), self.height())
        elif self._theme is Theme.VIBRANT:
            _paint_vibrant_surface(painter, self.width(), self.height())


class ThemeHeaderArt(QWidget):
    """Small top-right artwork, similar to a browser or mail-app theme skin."""

    def __init__(self) -> None:
        super().__init__()
        self._theme = Theme.LIGHT
        self.setFixedSize(QSize(168, 54))
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def set_theme(self, theme: Theme) -> None:
        """Update the header artwork."""
        self._theme = theme
        self.update()

    def paintEvent(self, event: object) -> None:
        painter = _make_painter(self)
        if self._theme is Theme.LIGHT:
            _paint_light_header(painter, self.width(), self.height())
        elif self._theme is Theme.DARK:
            _paint_dark_header(painter, self.width(), self.height())
        elif self._theme is Theme.COFFEE:
            _paint_coffee_header(painter, self.width(), self.height())
        elif self._theme is Theme.VIBRANT:
            _paint_vibrant_header(painter, self.width(), self.height())


class ThemeAccentRule(QWidget):
    """Thin app-wide accent rule that carries the theme without clutter."""

    def __init__(self) -> None:
        super().__init__()
        self._theme = Theme.LIGHT
        self.setFixedHeight(6)
        self.setMaximumWidth(16_777_215)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def set_theme(self, theme: Theme) -> None:
        """Update the accent rule."""
        self._theme = theme
        self.update()

    def paintEvent(self, event: object) -> None:
        painter = _make_painter(self)
        rect = QRectF(0, 2, self.width(), 2)
        colors = colors_for(self._theme)

        if self._theme is Theme.VIBRANT:
            gradient = QLinearGradient(rect.topLeft(), rect.topRight())
            gradient.setColorAt(0.0, _color(colors["decor_1"], 190))
            gradient.setColorAt(0.45, _color(colors["decor_3"], 180))
            gradient.setColorAt(1.0, _color(colors["decor_2"], 190))
            painter.fillRect(rect, gradient)
            return

        if self._theme is Theme.COFFEE:
            gradient = QLinearGradient(rect.topLeft(), rect.topRight())
            gradient.setColorAt(0.0, _color("#d8b085", 120))
            gradient.setColorAt(0.5, _color(colors["decor_2"], 190))
            gradient.setColorAt(1.0, _color("#d8b085", 120))
            painter.fillRect(rect, gradient)
            return

        painter.fillRect(rect, _color(colors["decor_line"], 180))


def _paint_light_surface(painter: QPainter, width: int, height: int) -> None:
    _paint_soft_corner(painter, width, "#dbeafe", "#bfdbfe", "#ffffff", alpha=82)
    _paint_bottom_panel(painter, width, height, "#dbeafe", alpha=38)


def _paint_dark_surface(painter: QPainter, width: int, height: int) -> None:
    _paint_soft_corner(painter, width, "#1e293b", "#334155", "#0f172a", alpha=90)
    _paint_bottom_panel(painter, width, height, "#263244", alpha=60)


def _paint_coffee_surface(painter: QPainter, width: int, height: int) -> None:
    _paint_soft_corner(painter, width, "#ead5bd", "#c88b5a", "#fff7ed", alpha=86)
    _paint_bottom_panel(painter, width, height, "#d7a06f", alpha=52)


def _paint_vibrant_surface(painter: QPainter, width: int, height: int) -> None:
    _paint_soft_corner(painter, width, "#f0abfc", "#8b5cf6", "#2dd4bf", alpha=66)
    _paint_bottom_panel(painter, width, height, "#c4b5fd", alpha=44)


def _paint_light_header(painter: QPainter, width: int, height: int) -> None:
    _paint_header_tiles(painter, ("#60a5fa", "#93c5fd", "#e0f2fe"), alpha=150)


def _paint_dark_header(painter: QPainter, width: int, height: int) -> None:
    _paint_header_tiles(painter, ("#94a3b8", "#64748b", "#334155"), alpha=142)


def _paint_coffee_header(painter: QPainter, width: int, height: int) -> None:
    _paint_header_tiles(painter, ("#b86b38", "#d8b085", "#7b4528"), alpha=150)


def _paint_vibrant_header(painter: QPainter, width: int, height: int) -> None:
    _paint_header_tiles(painter, ("#ff4f8b", "#7c3aed", "#14b8a6"), alpha=185)


def _paint_soft_corner(
    painter: QPainter,
    width: int,
    first: str,
    second: str,
    third: str,
    alpha: int,
) -> None:
    corner = QRectF(width - 360, -92, 430, 170)
    gradient = QLinearGradient(corner.topLeft(), corner.bottomRight())
    gradient.setColorAt(0.0, _color(first, alpha))
    gradient.setColorAt(0.52, _color(second, max(alpha - 18, 20)))
    gradient.setColorAt(1.0, _color(third, 0))

    path = QPainterPath()
    path.addRoundedRect(corner, 54, 54)
    painter.fillPath(path, gradient)


def _paint_bottom_panel(painter: QPainter, width: int, height: int, color: str, alpha: int) -> None:
    panel = QPainterPath(QPointF(0, height - 42))
    panel.lineTo(width * 0.34, height - 34)
    panel.lineTo(width, height - 56)
    panel.lineTo(width, height)
    panel.lineTo(0, height)
    panel.closeSubpath()
    painter.fillPath(panel, _color(color, alpha))

    edge = QPainterPath(QPointF(width * 0.58, height))
    edge.lineTo(width, height - 28)
    edge.lineTo(width, height)
    edge.closeSubpath()
    painter.fillPath(edge, _color(color, max(alpha - 18, 16)))


def _paint_header_tiles(painter: QPainter, colors: tuple[str, str, str], alpha: int) -> None:
    specs = (
        (14, 9, 94, 18, 9, colors[0], alpha),
        (44, 24, 118, 16, 8, colors[1], max(alpha - 30, 48)),
        (92, 4, 54, 40, 18, colors[2], max(alpha - 52, 36)),
    )

    for x, y, width, height, radius, color, item_alpha in specs:
        rect = QRectF(x, y, width, height)
        gradient = QLinearGradient(rect.topLeft(), rect.topRight())
        gradient.setColorAt(0.0, _color(color, item_alpha))
        gradient.setColorAt(1.0, _color(color, max(item_alpha - 48, 24)))
        path = QPainterPath()
        path.addRoundedRect(rect, radius, radius)
        painter.fillPath(path, gradient)


def _make_painter(widget: QWidget) -> QPainter:
    painter = QPainter(widget)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    return painter


def _color(value: str, alpha: int = 220) -> QColor:
    color = QColor(value)
    color.setAlpha(alpha)
    return color

