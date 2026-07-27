"""Document and image conversion services."""

from __future__ import annotations

import time
from collections.abc import Callable
from pathlib import Path

from pdf2docx import Converter

from .compat import ensure_pymupdf_compatibility
from .image_conversion import (
    convert_image,
    convert_pdf_to_images,
    image_frame_count,
    pdf_page_count,
)
from .models import ConversionMode, ConversionResult, FileFormat
from .ocr import OcrFallbackError, ocr_pdf_to_docx
from .word_pdf import WordToPdfSession


LogCallback = Callable[[str, str], None]


class ConversionError(RuntimeError):
    """Raised when a source file cannot be converted."""


class DocumentConverter:
    """Convert one file at a time while keeping path handling centralized."""

    def __init__(self, log: LogCallback | None = None) -> None:
        self._log = log
        self._word_pdf_session: WordToPdfSession | None = None
        self._reserved_outputs: set[Path] = set()
        ensure_pymupdf_compatibility()

    def __enter__(self) -> "DocumentConverter":
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()

    def close(self) -> None:
        """Release any converter resources opened during a batch."""
        if self._word_pdf_session is not None:
            self._word_pdf_session.close()
            self._word_pdf_session = None

    def convert(
        self,
        source: Path,
        mode: ConversionMode,
        output_folder: Path | None,
        overwrite_existing: bool,
        *,
        image_dpi: int = 200,
        image_quality: int = 90,
    ) -> ConversionResult:
        """Convert ``source`` according to ``mode`` and return a result object."""
        started = time.perf_counter()
        source = source.resolve()
        output: Path | None = None

        try:
            self._validate_source(source, mode)
            target = mode.target_format
            outputs: tuple[Path, ...]
            used_ocr_fallback = False

            if mode.source_format is FileFormat.PDF and target is FileFormat.WORD:
                output = self.output_path_for(source, mode, output_folder, overwrite_existing)
                output.parent.mkdir(parents=True, exist_ok=True)
                used_ocr_fallback = self._pdf_to_word(source, output)
                outputs = (output,)
            elif mode.source_format is FileFormat.WORD and target is FileFormat.PDF:
                output = self.output_path_for(source, mode, output_folder, overwrite_existing)
                output.parent.mkdir(parents=True, exist_ok=True)
                self._word_to_pdf(source, output)
                outputs = (output,)
            elif mode.source_format is FileFormat.PDF and target.is_image:
                page_count = pdf_page_count(source)
                output = self._image_destination(
                    source,
                    target,
                    output_folder,
                    overwrite_existing,
                    multiple_outputs=page_count > 1 and target is not FileFormat.TIFF,
                )
                outputs = convert_pdf_to_images(
                    source,
                    output,
                    target,
                    dpi=image_dpi,
                    quality=image_quality,
                )
            elif mode.source_format is FileFormat.IMAGES:
                if target.accepts(source):
                    raise ConversionError(f"{source.name} is already a {target.label} file.")
                frame_count = image_frame_count(source)
                output = self._image_destination(
                    source,
                    target,
                    output_folder,
                    overwrite_existing,
                    multiple_outputs=(
                        frame_count > 1
                        and target not in {FileFormat.PDF, FileFormat.TIFF, FileFormat.WEBP}
                    ),
                )
                outputs = convert_image(
                    source,
                    output,
                    target,
                    dpi=image_dpi,
                    quality=image_quality,
                )
            else:
                raise ConversionError(f"Unsupported conversion mode: {mode.label}")

            missing_outputs = [path for path in outputs if not path.exists()]
            if not outputs or missing_outputs:
                raise ConversionError("The converter finished without creating the expected output.")

            elapsed = time.perf_counter() - started
            message = self._success_message(output, outputs, target)
            if used_ocr_fallback:
                message = f"Created {output.name} with OCR fallback"

            return ConversionResult(
                source=source,
                output=output,
                succeeded=True,
                message=message,
                elapsed_seconds=elapsed,
                outputs=outputs,
            )
        except Exception as exc:
            elapsed = time.perf_counter() - started
            return ConversionResult(
                source=source,
                output=output,
                succeeded=False,
                message=str(exc),
                elapsed_seconds=elapsed,
            )

    def output_path_for(
        self,
        source: Path,
        mode: ConversionMode,
        output_folder: Path | None,
        overwrite_existing: bool,
    ) -> Path:
        """Build a single output path, avoiding collisions unless overwrite is enabled."""
        suffix = mode.target_format.output_suffix
        if not suffix:
            raise ConversionError(f"{mode.target_format.label} is not a concrete output format.")
        folder = output_folder or source.parent
        candidate = folder / f"{source.stem}{suffix}"

        return self._claim_output(candidate, allow_existing=overwrite_existing)

    def _image_destination(
        self,
        source: Path,
        target: FileFormat,
        output_folder: Path | None,
        overwrite_existing: bool,
        *,
        multiple_outputs: bool,
    ) -> Path:
        folder = output_folder or source.parent
        folder.mkdir(parents=True, exist_ok=True)
        if multiple_outputs:
            candidate = folder / f"{source.stem}_{target.key}_pages"
            return self._claim_output(candidate, allow_existing=False)

        mode = ConversionMode(FileFormat.IMAGES, target)
        if source.suffix.lower() == ".pdf":
            mode = ConversionMode(FileFormat.PDF, target)
        return self.output_path_for(source, mode, output_folder, overwrite_existing)

    def _claim_output(self, candidate: Path, *, allow_existing: bool) -> Path:
        """Reserve an output so files with the same stem cannot overwrite each other."""
        candidate = candidate.absolute()
        if candidate not in self._reserved_outputs and (allow_existing or not candidate.exists()):
            self._reserved_outputs.add(candidate)
            return candidate

        for index in range(1, 10_000):
            numbered = candidate.with_name(f"{candidate.stem} ({index}){candidate.suffix}")
            if numbered not in self._reserved_outputs and not numbered.exists():
                self._reserved_outputs.add(numbered)
                return numbered

        raise ConversionError(f"Could not create a unique output name for {candidate.name}.")

    def _validate_source(self, source: Path, mode: ConversionMode) -> None:
        if not source.is_file():
            raise ConversionError("Source file no longer exists or is not a regular file.")
        if not mode.source_format.accepts(source):
            expected = ", ".join(mode.source_format.source_suffixes)
            raise ConversionError(f"Expected one of these source types: {expected}.")

    @staticmethod
    def _success_message(
        output: Path,
        outputs: tuple[Path, ...],
        target: FileFormat,
    ) -> str:
        if output.is_dir():
            return f"Created {len(outputs)} {target.label} files in {output.name}"
        return f"Created {output.name}"

    def _pdf_to_word(self, pdf_path: Path, docx_path: Path) -> bool:
        self._emit("INFO", f"PDF to Word: {pdf_path} -> {docx_path}")
        try:
            self._pdf_to_word_standard(pdf_path, docx_path)
            return False
        except Exception as exc:
            self._emit("WARNING", f"Standard PDF conversion did not finish: {exc}")
            self._emit("INFO", "Trying Tesseract OCR fallback.")
            try:
                ocr_pdf_to_docx(pdf_path, docx_path, log=self._log)
            except OcrFallbackError as ocr_exc:
                raise ConversionError(
                    f"Standard conversion failed, and OCR fallback could not finish: {ocr_exc}"
                ) from ocr_exc
            return True

    def _pdf_to_word_standard(self, pdf_path: Path, docx_path: Path) -> None:
        converter = Converter(str(pdf_path))
        try:
            converter.convert(str(docx_path), start=0, end=None)
        finally:
            converter.close()

    def _word_to_pdf(self, docx_path: Path, pdf_path: Path) -> None:
        self._emit("INFO", f"Word to PDF: {docx_path} -> {pdf_path}")
        self._word_session().convert(docx_path, pdf_path)

    def _word_session(self) -> WordToPdfSession:
        if self._word_pdf_session is None:
            self._word_pdf_session = WordToPdfSession(log=self._log)
        return self._word_pdf_session

    def _emit(self, level: str, message: str) -> None:
        if self._log:
            self._log(level, message)


def _next_available_path(path: Path) -> Path:
    """Return a numbered sibling file or directory that does not exist."""
    for index in range(1, 10_000):
        candidate = path.with_name(f"{path.stem} ({index}){path.suffix}")
        if not candidate.exists():
            return candidate

    raise ConversionError(f"Could not create a unique output name for {path.name}.")
