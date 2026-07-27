"""Compatibility patches for third-party conversion libraries."""

from __future__ import annotations


def ensure_pymupdf_compatibility() -> None:
    """Provide ``fitz.Rect.get_area`` for pdf2docx on newer PyMuPDF versions.

    Some pdf2docx releases expect ``Rect.get_area``. PyMuPDF 1.20+ removed that
    method in favor of properties, so the patch keeps conversion behavior stable
    without pinning the user's environment to an older PyMuPDF build.
    """
    import fitz

    if hasattr(fitz.Rect, "get_area"):
        return

    def get_area(self: object) -> float:
        return self.width * self.height

    fitz.Rect.get_area = get_area
