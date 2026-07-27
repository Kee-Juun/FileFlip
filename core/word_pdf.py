"""Microsoft Word backed DOCX to PDF conversion."""

from __future__ import annotations

import sys
import time
from collections.abc import Callable
from pathlib import Path


LogCallback = Callable[[str, str], None]


class WordPdfError(RuntimeError):
    """Raised when Microsoft Word cannot export a document to PDF."""


class WordToPdfSession:
    """Reuse one Microsoft Word COM session for a whole conversion batch.

    The upstream ``docx2pdf`` single-file path starts Word and quits Word for
    every file. On a cold Windows launch that final ``Word.Application.Quit``
    call can raise after the PDF has already been written, causing a false
    failure and destabilizing the rest of the first batch. This session keeps
    Word open for the batch, closes each document, and treats final app teardown
    as cleanup rather than as part of an individual file result.
    """

    WD_FORMAT_PDF = 17
    WD_DO_NOT_SAVE_CHANGES = 0

    def __init__(self, log: LogCallback | None = None) -> None:
        self._log = log
        self._word = None
        self._pythoncom = None
        self._com_initialized = False

    def convert(self, docx_path: Path, pdf_path: Path) -> None:
        """Export ``docx_path`` to ``pdf_path``."""
        if sys.platform != "win32":
            self._convert_with_docx2pdf(docx_path, pdf_path)
            return

        word = self._ensure_word()
        doc = None
        save_error: Exception | None = None

        try:
            if pdf_path.exists():
                pdf_path.unlink()

            doc = word.Documents.Open(
                str(docx_path),
                ConfirmConversions=False,
                ReadOnly=True,
                AddToRecentFiles=False,
            )
            doc.SaveAs(str(pdf_path), FileFormat=self.WD_FORMAT_PDF)
        except Exception as exc:
            save_error = exc
        finally:
            if doc is not None:
                self._close_document(doc, docx_path)

        if save_error is not None:
            raise WordPdfError(f"Word PDF export failed: {save_error}") from save_error

        if not pdf_path.exists() or pdf_path.stat().st_size == 0:
            raise WordPdfError("Word did not create a readable PDF output file.")

    def close(self) -> None:
        """Quit Word and release COM for the worker thread."""
        if self._word is not None:
            try:
                self._word.Quit(SaveChanges=self.WD_DO_NOT_SAVE_CHANGES)
            except Exception as exc:
                self._emit("WARNING", f"Word cleanup warning: {exc}")
            finally:
                self._word = None

        if self._com_initialized and self._pythoncom is not None:
            try:
                self._pythoncom.CoUninitialize()
            finally:
                self._com_initialized = False
                self._pythoncom = None

    def _ensure_word(self):
        if self._word is not None:
            return self._word

        self._initialize_com()
        self._word = self._create_word_application()
        self._word.Visible = False
        self._word.DisplayAlerts = 0
        try:
            self._word.ScreenUpdating = False
        except Exception:
            pass
        self._emit("INFO", "Microsoft Word session started for this batch.")
        return self._word

    def _initialize_com(self) -> None:
        if self._com_initialized:
            return

        import pythoncom

        pythoncom.CoInitialize()
        self._pythoncom = pythoncom
        self._com_initialized = True

    def _create_word_application(self):
        import win32com.client

        last_error: Exception | None = None
        for attempt in range(1, 4):
            try:
                return win32com.client.DispatchEx("Word.Application")
            except Exception as exc:
                last_error = exc
                self._emit("WARNING", f"Word startup attempt {attempt} failed: {exc}")
                time.sleep(1.5 * attempt)

        try:
            return win32com.client.Dispatch("Word.Application")
        except Exception as exc:
            raise WordPdfError(f"Could not start Microsoft Word: {exc}") from last_error or exc

    def _close_document(self, doc: object, docx_path: Path) -> None:
        try:
            doc.Close(SaveChanges=self.WD_DO_NOT_SAVE_CHANGES)
        except Exception as exc:
            self._emit("WARNING", f"Document cleanup warning for {docx_path.name}: {exc}")

    def _convert_with_docx2pdf(self, docx_path: Path, pdf_path: Path) -> None:
        from docx2pdf import convert as docx2pdf_convert

        docx2pdf_convert(str(docx_path), str(pdf_path))

    def _emit(self, level: str, message: str) -> None:
        if self._log:
            self._log(level, message)
