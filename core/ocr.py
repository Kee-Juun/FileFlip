"""OCR fallback helpers for image-heavy PDFs."""

from __future__ import annotations

import io
import os
import shutil
import sys
from collections.abc import Callable
from pathlib import Path


LogCallback = Callable[[str, str], None]


class OcrFallbackError(RuntimeError):
    """Raised when OCR fallback cannot complete."""


def ocr_pdf_to_docx(
    pdf_path: Path,
    docx_path: Path,
    log: LogCallback | None = None,
    language: str = "eng",
) -> None:
    """Create a text-only DOCX from PDF page images using Tesseract OCR."""
    tesseract_cmd = _require_tesseract()

    try:
        import fitz
        import pytesseract
        from docx import Document
        from docx.enum.text import WD_BREAK
        from PIL import Image
    except ImportError as exc:
        raise OcrFallbackError(
            "OCR fallback needs pytesseract, Pillow, and python-docx installed."
        ) from exc

    pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
    _configure_tessdata_prefix(tesseract_cmd)
    _emit(log, "INFO", f"OCR fallback: {pdf_path} -> {docx_path}")

    document = Document()
    pages_with_text = 0

    try:
        pdf = fitz.open(str(pdf_path))
    except Exception as exc:
        raise OcrFallbackError(f"Could not open the PDF for OCR: {exc}") from exc

    try:
        for page_index, page in enumerate(pdf, start=1):
            _emit(log, "INFO", f"OCR page {page_index} of {pdf.page_count}: {pdf_path.name}")
            pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            image = Image.open(io.BytesIO(pixmap.tobytes("png")))
            text = pytesseract.image_to_string(image, lang=language).strip()

            if text:
                pages_with_text += 1
                for block in text.split("\n\n"):
                    paragraph = block.strip()
                    if paragraph:
                        document.add_paragraph(paragraph)

            if page_index < pdf.page_count:
                document.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
    except pytesseract.TesseractNotFoundError as exc:
        raise OcrFallbackError(
            "Tesseract is not installed or is not on PATH. Install Tesseract OCR, then try again."
        ) from exc
    except Exception as exc:
        raise OcrFallbackError(f"OCR fallback stopped early: {exc}") from exc
    finally:
        pdf.close()

    if pages_with_text == 0:
        raise OcrFallbackError("OCR ran, but it could not find readable text in the PDF.")

    try:
        document.save(str(docx_path))
    except Exception as exc:
        raise OcrFallbackError(f"Could not save the OCR Word file: {exc}") from exc


def _require_tesseract() -> str:
    executable = _find_tesseract()
    if executable is None:
        raise OcrFallbackError(
            "Tesseract is not installed or is not on PATH. Install Tesseract OCR, then try again."
        )
    return executable


def _find_tesseract() -> str | None:
    for candidate in _tesseract_candidates():
        if candidate and Path(candidate).is_file():
            return str(Path(candidate))
    return None


def _tesseract_candidates() -> tuple[Path | str | None, ...]:
    """Return FileFlip, SADM, and MOADMN-style Tesseract probe locations."""
    project_root = Path(__file__).resolve().parents[1]
    exe_root = Path(sys.executable).resolve().parent
    bundle_root = _pyinstaller_bundle_root()
    local_app_data = os.environ.get("LOCALAPPDATA")

    return (
        os.environ.get("FILEFLIP_TESSERACT_PATH"),
        shutil.which("tesseract"),
        Path("C:/Program Files/Tesseract-OCR/tesseract.exe"),
        Path("C:/Program Files (x86)/Tesseract-OCR/tesseract.exe"),
        _local_app_path(local_app_data, "Programs", "Tesseract-OCR", "tesseract.exe"),
        _local_app_path(local_app_data, "Tesseract-OCR", "tesseract.exe"),
        project_root / "tesseract" / "tesseract.exe",
        project_root / "Tesseract-OCR" / "tesseract.exe",
        project_root / "assets" / "tesseract" / "tesseract.exe",
        project_root / "assets" / "Tesseract-OCR" / "tesseract.exe",
        exe_root / "tesseract" / "tesseract.exe",
        exe_root / "Tesseract-OCR" / "tesseract.exe",
        exe_root / "assets" / "tesseract" / "tesseract.exe",
        exe_root / "assets" / "Tesseract-OCR" / "tesseract.exe",
        bundle_root / "tesseract" / "tesseract.exe" if bundle_root else None,
        bundle_root / "Tesseract-OCR" / "tesseract.exe" if bundle_root else None,
        bundle_root / "assets" / "tesseract" / "tesseract.exe" if bundle_root else None,
        bundle_root / "assets" / "Tesseract-OCR" / "tesseract.exe" if bundle_root else None,
    )


def _local_app_path(root: str | None, *parts: str) -> Path | None:
    if not root:
        return None
    return Path(root, *parts)


def _pyinstaller_bundle_root() -> Path | None:
    root = getattr(sys, "_MEIPASS", None)
    if not root:
        return None
    return Path(root)


def _configure_tessdata_prefix(tesseract_cmd: str) -> None:
    tessdata_dir = Path(tesseract_cmd).resolve().parent / "tessdata"
    if tessdata_dir.is_dir():
        os.environ["TESSDATA_PREFIX"] = str(tessdata_dir)


def _emit(log: LogCallback | None, level: str, message: str) -> None:
    if log:
        log(level, message)
