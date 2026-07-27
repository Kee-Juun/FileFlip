"""Background conversion worker."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal

from core.converter import DocumentConverter
from core.models import BatchSummary, ConversionOptions, ConversionResult
from utils.logger import SessionLog


def _file_count(count: int) -> str:
    """Return a natural file-count label for status text."""
    return "1 file" if count == 1 else f"{count} files"


class ConversionWorker(QThread):
    """Run a conversion batch outside the UI thread."""

    progress_changed = pyqtSignal(int, int, str)
    log_line = pyqtSignal(str)
    result_ready = pyqtSignal(object)
    batch_ready = pyqtSignal(object, object)

    def __init__(self, options: ConversionOptions) -> None:
        super().__init__()
        self.options = options
        self._cancel_requested = False

    def cancel(self) -> None:
        """Request cancellation after the current file completes."""
        self._cancel_requested = True

    def run(self) -> None:
        session_log = SessionLog()
        results: list[ConversionResult] = []

        def log(level: str, message: str) -> None:
            line = session_log.add(level, message)
            self.log_line.emit(line)

        total = len(self.options.files)
        log("INFO", f"Starting batch: {_file_count(total)}, mode {self.options.mode.label}.")

        with DocumentConverter(log=log) as converter:
            for index, source in enumerate(self.options.files, start=1):
                if self._cancel_requested:
                    log("WARNING", "Batch cancelled by user.")
                    break

                self.progress_changed.emit(index - 1, total, f"Converting {source.name}")
                result = converter.convert(
                    source=source,
                    mode=self.options.mode,
                    output_folder=self.options.output_folder,
                    overwrite_existing=self.options.overwrite_existing,
                    image_dpi=self.options.image_dpi,
                    image_quality=self.options.image_quality,
                )
                if result.succeeded and self.options.delete_originals:
                    try:
                        result.source.unlink()
                    except OSError as exc:
                        log("WARNING", f"Could not delete original {result.source}: {exc}")
                        result = replace(
                            result,
                            message=f"{result.message}; original was kept",
                            original_deleted=False,
                        )
                    else:
                        log("INFO", f"Deleted original: {result.source}")
                        result = replace(
                            result,
                            message=f"{result.message}; deleted original",
                            original_deleted=True,
                        )
                results.append(result)

                level = "INFO" if result.succeeded else "ERROR"
                log(level, f"{source.name}: {result.message} ({result.elapsed_seconds:.1f}s)")
                self.result_ready.emit(result)
                self.progress_changed.emit(index, total, result.message)

        log_path: Path | None = None
        if self.options.save_log:
            try:
                log_path = session_log.save(self._log_folder())
                self.log_line.emit(session_log.add("INFO", f"Log saved: {log_path}"))
            except Exception as exc:
                self.log_line.emit(session_log.add("ERROR", f"Could not save log: {exc}"))

        succeeded = sum(1 for result in results if result.succeeded)
        summary = BatchSummary(
            total=total,
            succeeded=succeeded,
            failed=len(results) - succeeded,
            cancelled=self._cancel_requested,
            log_file=log_path,
        )
        self.batch_ready.emit(summary, results)

    def _log_folder(self) -> Path:
        if self.options.output_folder is not None:
            return self.options.output_folder
        if self.options.files:
            return self.options.files[0].parent
        return Path.cwd()
