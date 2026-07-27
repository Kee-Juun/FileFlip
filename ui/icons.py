"""Generated application icons."""

from __future__ import annotations

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import (
    QColor,
    QFont,
    QIcon,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QRadialGradient,
)

from .fonts import load_theme_fonts


ICON_SIZES = (16, 24, 32, 48, 64, 128, 256)
ICON_FONT_FAMILY = "Pacifico"


def app_icon() -> QIcon:
    """Return FileFlip's premium jewel-tone application icon."""
    load_theme_fonts()
    icon = QIcon()
    for size in ICON_SIZES:
        icon.addPixmap(_app_icon_pixmap(size))
    return icon


def _app_icon_pixmap(size: int) -> QPixmap:
    """Render with supersampling so the mark stays crisp at taskbar sizes."""
    render_size = max(64, size * 4)
    rendered = _render_icon(render_size)
    return rendered.scaled(
        size,
        size,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )


def _render_icon(size: int) -> QPixmap:
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

    inset = size * 0.075
    body_rect = QRectF(inset, inset, size - inset * 2, size - inset * 2)
    radius = size * 0.245

    # A restrained floating shadow gives the tile depth without muddying its edges.
    shadow_rect = body_rect.translated(0, size * 0.025)
    shadow_path = QPainterPath()
    shadow_path.addRoundedRect(shadow_rect, radius, radius)
    shadow = QRadialGradient(shadow_rect.center(), size * 0.62)
    shadow.setColorAt(0.0, QColor(20, 10, 55, 150))
    shadow.setColorAt(0.72, QColor(20, 10, 55, 92))
    shadow.setColorAt(1.0, QColor(20, 10, 55, 0))
    painter.fillPath(shadow_path, shadow)

    body_path = QPainterPath()
    body_path.addRoundedRect(body_rect, radius, radius)

    # Sapphire, violet, and magenta create a richer jewel-tone identity.
    base = QLinearGradient(body_rect.topLeft(), body_rect.bottomRight())
    base.setColorAt(0.0, QColor("#22d3ee"))
    base.setColorAt(0.18, QColor("#3b82f6"))
    base.setColorAt(0.48, QColor("#7c3aed"))
    base.setColorAt(0.76, QColor("#a855f7"))
    base.setColorAt(1.0, QColor("#4c1d95"))
    painter.fillPath(body_path, base)

    painter.save()
    painter.setClipPath(body_path)

    # Glassy upper-left illumination and a deep lower-right vignette.
    glow = QRadialGradient(
        QPointF(body_rect.left() + body_rect.width() * 0.18,
                body_rect.top() + body_rect.height() * 0.12),
        body_rect.width() * 0.78,
    )
    glow.setColorAt(0.0, QColor(255, 255, 255, 112))
    glow.setColorAt(0.32, QColor(255, 255, 255, 36))
    glow.setColorAt(1.0, QColor(255, 255, 255, 0))
    painter.fillRect(body_rect, glow)

    vignette = QRadialGradient(
        QPointF(body_rect.right(), body_rect.bottom()),
        body_rect.width() * 0.82,
    )
    vignette.setColorAt(0.0, QColor(27, 8, 78, 110))
    vignette.setColorAt(0.64, QColor(27, 8, 78, 24))
    vignette.setColorAt(1.0, QColor(27, 8, 78, 0))
    painter.fillRect(body_rect, vignette)

    # A soft diagonal reflection reads as polished glass, not a flat gradient.
    sheen = QPainterPath()
    sheen.moveTo(body_rect.left() - size * 0.05, body_rect.top() + size * 0.16)
    sheen.lineTo(body_rect.right() - size * 0.08, body_rect.top() - size * 0.04)
    sheen.lineTo(body_rect.left() + size * 0.33, body_rect.bottom() + size * 0.04)
    sheen.closeSubpath()
    sheen_gradient = QLinearGradient(body_rect.topLeft(), body_rect.bottomRight())
    sheen_gradient.setColorAt(0.0, QColor(255, 255, 255, 44))
    sheen_gradient.setColorAt(0.55, QColor(255, 255, 255, 10))
    sheen_gradient.setColorAt(1.0, QColor(255, 255, 255, 0))
    painter.fillPath(sheen, sheen_gradient)
    painter.restore()

    # Fine outer and inner rims make the icon feel machined and premium.
    rim = QLinearGradient(body_rect.topLeft(), body_rect.bottomRight())
    rim.setColorAt(0.0, QColor(255, 255, 255, 205))
    rim.setColorAt(0.36, QColor(255, 255, 255, 66))
    rim.setColorAt(1.0, QColor(95, 42, 180, 170))
    painter.setPen(QPen(rim, max(1.0, size * 0.014)))
    painter.drawPath(body_path)

    inner_rect = body_rect.adjusted(size * 0.023, size * 0.023, -size * 0.023, -size * 0.023)
    inner_path = QPainterPath()
    inner_path.addRoundedRect(inner_rect, radius * 0.9, radius * 0.9)
    painter.setPen(QPen(QColor(255, 255, 255, 45), max(1.0, size * 0.007)))
    painter.drawPath(inner_path)

    font = QFont(ICON_FONT_FAMILY)
    font.setPixelSize(180)
    font.setWeight(QFont.Weight.Normal)

    text_path = QPainterPath()
    text_path.addText(0, 0, font, "F")
    text_bounds = text_path.boundingRect()
    target = body_rect.adjusted(size * 0.19, size * 0.155, -size * 0.19, -size * 0.155)
    scale = min(target.width() / text_bounds.width(), target.height() / text_bounds.height())
    target_center = target.center()
    text_center = text_bounds.center()

    painter.save()
    painter.translate(target_center)
    painter.scale(scale, scale)
    painter.translate(-text_center)

    # A subtle violet shadow and pearl-white face keep the F legible at 16 px.
    painter.save()
    painter.translate(size * 0.018 / scale, size * 0.026 / scale)
    painter.fillPath(text_path, QColor(35, 10, 90, 125))
    painter.restore()

    pearl = QLinearGradient(text_bounds.topLeft(), text_bounds.bottomLeft())
    pearl.setColorAt(0.0, QColor("#ffffff"))
    pearl.setColorAt(0.55, QColor("#f8f7ff"))
    pearl.setColorAt(1.0, QColor("#ded7ff"))
    painter.fillPath(text_path, pearl)
    painter.setPen(QPen(QColor(255, 255, 255, 128), max(0.7, 1.1 / scale)))
    painter.drawPath(text_path)
    painter.restore()

    painter.end()
    return pixmap
