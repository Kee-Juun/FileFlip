"""Main PyQt window and application runner for FileFlip."""

from __future__ import annotations

import sys
from pathlib import Path

from PyQt6.QtCore import QSettings, QSize, Qt
from PyQt6.QtGui import QColor, QFont, QPalette
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QStyle,
    QTableWidget,
    QTableWidgetItem,
    QToolButton,
    QVBoxLayout,
)

from config import APP_NAME, DEFAULT_WINDOW_SIZE, MIN_WINDOW_SIZE, ORGANIZATION_NAME
from core.models import (
    SOURCE_FORMATS,
    SUPPORTED_TARGETS,
    BatchSummary,
    ConversionMode,
    ConversionOptions,
    ConversionResult,
    FileFormat,
)
from utils.platform import open_folder
from .decorations import ThemeAccentRule, ThemeHeaderArt, ThemeSurface
from .dialogs import ask_ok_cancel, show_information, show_warning
from .fonts import BODY_FONT_FAMILY, load_theme_fonts
from .icons import app_icon
from .themes import Theme, colors_for, combo_popup_stylesheet_for, stylesheet_for
from .titlebar import AppTitleBar, CornerResizeGrip
from .worker import ConversionWorker


def _file_count(count: int) -> str:
    """Return a natural file-count label."""
    return "1 file" if count == 1 else f"{count} files"


class MainWindow(QMainWindow):
    """Compact batch-conversion interface."""

    STATUS_COLUMN = 2

    def __init__(self) -> None:
        super().__init__()
        load_theme_fonts()
        self.files: list[Path] = []
        self.output_folder: Path | None = None
        self.worker: ConversionWorker | None = None
        self.settings = QSettings(ORGANIZATION_NAME, APP_NAME)
        self.theme = self._saved_theme()

        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.setWindowTitle(APP_NAME)
        self.setWindowIcon(app_icon())
        self.setMinimumSize(*MIN_WINDOW_SIZE)
        self.resize(*DEFAULT_WINDOW_SIZE)

        self._build_ui()
        self._connect_signals()
        self._refresh_controls()
        self._set_output_display()
        self._apply_theme(self.theme)
        self.statusBar().hide()

    @property
    def current_mode(self) -> ConversionMode:
        return ConversionMode.from_formats(
            self.current_source_format,
            self.current_target_format,
        )

    @property
    def current_source_format(self) -> FileFormat:
        return self.source_format_combo.currentData()

    @property
    def current_target_format(self) -> FileFormat:
        return self.target_format_combo.currentData()

    def _build_ui(self) -> None:
        root = ThemeSurface()
        self.theme_surface = root
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(22, 20, 22, 18)
        root_layout.setSpacing(14)

        self.title_bar = AppTitleBar(APP_NAME)
        root_layout.addWidget(self.title_bar)

        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)
        title_block = QVBoxLayout()
        title_block.setSpacing(0)
        self.title_label = QLabel(APP_NAME)
        self.title_label.setObjectName("AppTitle")
        self.subtitle_label = QLabel("File Converter")
        self.subtitle_label.setObjectName("MutedText")
        title_block.addWidget(self.title_label)
        title_block.addWidget(self.subtitle_label)
        header_layout.addLayout(title_block)
        header_layout.addItem(QSpacerItem(20, 20, QSizePolicy.Policy.Expanding))

        self.theme_header_art = ThemeHeaderArt()
        header_layout.addWidget(self.theme_header_art)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems([theme.value for theme in Theme])
        self.theme_combo.setCurrentText(self.theme.value)
        # Leave room for the longest skin name plus the styled dropdown arrow.
        # The previous 100 px width clipped the final "t" in "Vibrant" at
        # common Windows display-scaling levels.
        self.theme_combo.setFixedWidth(124)
        self.skin_label = QLabel("Skin")
        self.skin_label.setObjectName("MutedText")
        self.source_format_combo = QComboBox()
        for source_format in SOURCE_FORMATS:
            self.source_format_combo.addItem(source_format.label, source_format)
        self.source_format_combo.setFixedWidth(104)
        self.from_format_label = QLabel("From")
        self.from_format_label.setObjectName("MutedText")
        self.to_format_label = QLabel("To")
        self.to_format_label.setObjectName("MutedText")
        self.target_format_combo = QComboBox()
        for target_format in SUPPORTED_TARGETS[FileFormat.PDF]:
            self.target_format_combo.addItem(target_format.label, target_format)
        self.target_format_combo.setFixedWidth(104)
        self._last_source_format = FileFormat.PDF
        self._last_target_format = FileFormat.WORD
        header_layout.addWidget(self.from_format_label)
        header_layout.addWidget(self.source_format_combo)
        header_layout.addWidget(self.to_format_label)
        header_layout.addWidget(self.target_format_combo)
        root_layout.addLayout(header_layout)

        toolbar = QFrame()
        toolbar.setObjectName("Toolbar")
        toolbar_layout = QVBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(14, 12, 14, 12)
        toolbar_layout.setSpacing(10)
        toolbar_top_layout = QHBoxLayout()
        toolbar_top_layout.setSpacing(10)
        toolbar_options_layout = QHBoxLayout()
        toolbar_options_layout.setSpacing(10)
        toolbar_image_options_layout = QHBoxLayout()
        toolbar_image_options_layout.setSpacing(8)

        self.add_files_button = QPushButton("Add")
        self.add_files_button.setObjectName("PrimaryLiteButton")
        self.remove_files_button = QToolButton()
        self.remove_files_button.setObjectName("IconButton")
        self.clear_files_button = QToolButton()
        self.clear_files_button.setObjectName("IconButton")

        self.output_line = QLineEdit()
        self.output_line.setReadOnly(True)
        self.output_line.setMinimumWidth(120)
        self.output_line.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.output_button = QToolButton()
        self.output_button.setObjectName("IconButton")

        self.source_folder_checkbox = QCheckBox("Original folders")
        self.source_folder_checkbox.setChecked(True)
        self.overwrite_checkbox = QCheckBox("Overwrite")
        self.delete_originals_checkbox = QCheckBox("Delete originals")
        self.save_log_checkbox = QCheckBox("Save log")
        self.save_log_checkbox.setChecked(True)
        self.open_when_done_checkbox = QCheckBox("Open after")
        self.open_when_done_checkbox.setChecked(True)

        self.dpi_label = QLabel("DPI")
        self.dpi_label.setObjectName("MutedText")
        self.dpi_combo = QComboBox()
        for dpi in (150, 200, 300):
            self.dpi_combo.addItem(str(dpi), dpi)
        self.dpi_combo.setCurrentText("200")
        self.dpi_combo.setFixedWidth(92)
        self.quality_label = QLabel("Quality")
        self.quality_label.setObjectName("MutedText")
        self.quality_combo = QComboBox()
        for quality in (80, 90, 95, 100):
            self.quality_combo.addItem(str(quality), quality)
        self.quality_combo.setCurrentText("90")
        self.quality_combo.setFixedWidth(92)

        toolbar_top_layout.addWidget(self.add_files_button)
        toolbar_top_layout.addWidget(self.remove_files_button)
        toolbar_top_layout.addWidget(self.clear_files_button)
        toolbar_top_layout.addWidget(self.output_line, 1)
        toolbar_top_layout.addWidget(self.output_button)
        toolbar_options_layout.addWidget(self.skin_label)
        toolbar_options_layout.addWidget(self.theme_combo)
        toolbar_options_layout.addItem(QSpacerItem(20, 1, QSizePolicy.Policy.Expanding))
        toolbar_options_layout.addWidget(self.source_folder_checkbox)
        toolbar_options_layout.addWidget(self.overwrite_checkbox)
        toolbar_options_layout.addWidget(self.delete_originals_checkbox)
        toolbar_options_layout.addWidget(self.save_log_checkbox)
        toolbar_options_layout.addWidget(self.open_when_done_checkbox)
        toolbar_image_options_layout.addItem(QSpacerItem(20, 1, QSizePolicy.Policy.Expanding))
        toolbar_image_options_layout.addWidget(self.dpi_label)
        toolbar_image_options_layout.addWidget(self.dpi_combo)
        toolbar_image_options_layout.addWidget(self.quality_label)
        toolbar_image_options_layout.addWidget(self.quality_combo)
        toolbar_layout.addLayout(toolbar_top_layout)
        toolbar_layout.addLayout(toolbar_options_layout)
        toolbar_layout.addLayout(toolbar_image_options_layout)
        root_layout.addWidget(toolbar)

        self.theme_accent_line = ThemeAccentRule()
        root_layout.addWidget(self.theme_accent_line)

        self.file_table = QTableWidget(0, 3)
        self.file_table.setObjectName("FileList")
        self.file_table.setHorizontalHeaderLabels(["File", "Type", "Status"])
        self.file_table.verticalHeader().setVisible(False)
        self.file_table.setAlternatingRowColors(False)
        self.file_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.file_table.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.file_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.file_table.setShowGrid(False)
        self.file_table.verticalHeader().setDefaultSectionSize(44)
        self.file_table.horizontalHeader().setStretchLastSection(False)
        self.file_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.file_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.file_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        root_layout.addWidget(self.file_table, 1)

        bottom_bar = QFrame()
        bottom_bar.setObjectName("BottomBar")
        bottom_layout = QHBoxLayout(bottom_bar)
        bottom_layout.setContentsMargins(14, 12, 14, 12)
        bottom_layout.setSpacing(12)

        status_block = QVBoxLayout()
        status_block.setSpacing(4)
        self.summary_label = QLabel("0 files")
        self.summary_label.setObjectName("CounterText")
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_label = QLabel("Ready")
        self.progress_label.setObjectName("MutedText")
        status_block.addWidget(self.summary_label)
        status_block.addWidget(self.progress_bar)
        status_block.addWidget(self.progress_label)
        bottom_layout.addLayout(status_block, 1)

        self.details_button = QToolButton()
        self.details_button.setText("Details")
        self.details_button.setCheckable(True)
        self.details_button.setObjectName("PillButton")
        self.cancel_button = QToolButton()
        self.cancel_button.setObjectName("IconButton")
        self.start_button = QPushButton("Convert")
        self.start_button.setObjectName("PrimaryButton")
        self.resize_grip = CornerResizeGrip(bottom_bar)

        bottom_layout.addWidget(self.details_button)
        bottom_layout.addWidget(self.cancel_button)
        bottom_layout.addWidget(self.start_button)
        bottom_layout.addWidget(self.resize_grip)
        root_layout.addWidget(bottom_bar)

        self.log_view = QPlainTextEdit()
        self.log_view.setObjectName("LogView")
        self.log_view.setReadOnly(True)
        self.log_view.setFixedHeight(112)
        self.log_view.hide()
        root_layout.addWidget(self.log_view)

        self.setCentralWidget(root)
        self._apply_button_icons()
        self._apply_tooltips()
        self._update_format_options()

    def _connect_signals(self) -> None:
        self.theme_combo.currentTextChanged.connect(self._theme_changed)
        self.source_format_combo.currentIndexChanged.connect(self._source_format_changed)
        self.target_format_combo.currentIndexChanged.connect(self._target_format_changed)
        self.add_files_button.clicked.connect(self.add_files)
        self.remove_files_button.clicked.connect(self.remove_selected_files)
        self.clear_files_button.clicked.connect(self.clear_files)
        self.output_button.clicked.connect(self.choose_output_folder)
        self.source_folder_checkbox.toggled.connect(self._source_folder_toggled)
        self.details_button.toggled.connect(self.log_view.setVisible)
        self.start_button.clicked.connect(self.start_conversion)
        self.cancel_button.clicked.connect(self.cancel_conversion)

    def _apply_button_icons(self) -> None:
        style = self.style()
        icon_size = QSize(18, 18)
        self.add_files_button.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_FileDialogNewFolder))
        self.remove_files_button.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_TrashIcon))
        self.clear_files_button.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_DialogResetButton))
        self.output_button.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_DirOpenIcon))
        self.cancel_button.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_DialogCancelButton))
        self.start_button.setIcon(style.standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        for button in (
            self.add_files_button,
            self.remove_files_button,
            self.clear_files_button,
            self.output_button,
            self.cancel_button,
            self.start_button,
        ):
            button.setIconSize(icon_size)

    def _apply_tooltips(self) -> None:
        self.theme_combo.setToolTip("Choose FileFlip's visual skin.")
        self.source_format_combo.setToolTip("Choose the type of files you want to convert.")
        self.target_format_combo.setToolTip("Choose a compatible output format.")
        self.add_files_button.setToolTip("Add source documents.")
        self.remove_files_button.setToolTip("Remove selected files.")
        self.clear_files_button.setToolTip("Clear the file list.")
        self.output_button.setToolTip("Choose an output folder.")
        self.source_folder_checkbox.setToolTip("Save each result next to its source file.")
        self.overwrite_checkbox.setToolTip("Replace matching output files.")
        self.delete_originals_checkbox.setToolTip(
            "Delete each original file only after it converts successfully."
        )
        self.save_log_checkbox.setToolTip("Save a timestamped text log for this batch.")
        self.open_when_done_checkbox.setToolTip("Open the output folder when finished.")
        self.dpi_combo.setToolTip("Rendering resolution. Higher DPI creates larger, sharper files.")
        self.quality_combo.setToolTip("Compression quality for JPG and WebP output.")
        self.details_button.setToolTip("Show or hide the conversion log.")
        self.start_button.setToolTip("Start conversion.")
        self.cancel_button.setToolTip("Cancel after the current file finishes.")

    def _theme_changed(self, label: str) -> None:
        theme = Theme.from_label(label)
        self._apply_theme(theme)
        self.settings.setValue("ui/theme", theme.value)
        self.settings.sync()

    def _saved_theme(self) -> Theme:
        """Return the last selected theme, falling back safely to Light."""
        label = self.settings.value("ui/theme", Theme.LIGHT.value, type=str)
        try:
            return Theme.from_label(label)
        except ValueError:
            return Theme.LIGHT

    def _apply_theme(self, theme: Theme) -> None:
        self.theme = theme
        self.setStyleSheet(stylesheet_for(theme))
        self._apply_theme_fonts(theme)
        self._apply_combo_popup_theme(theme)
        self._apply_theme_decorations(theme)
        self._refresh_status_colors()

    def _apply_theme_fonts(self, theme: Theme) -> None:
        colors = colors_for(theme)
        body_font = QFont(BODY_FONT_FAMILY, 10)
        header_font = QFont(colors["header_font"], 22)
        header_weight = QFont.Weight.Bold if colors["header_weight"] == "700" else QFont.Weight.Normal
        header_font.setWeight(header_weight)
        utility_font = QFont(BODY_FONT_FAMILY, 10)
        utility_font.setWeight(QFont.Weight.DemiBold)

        # Theme display fonts are intentionally scoped to title/status surfaces.
        # All working controls are reset here so fonts never leak between themes.
        body_widgets = (
            self.subtitle_label,
            self.skin_label,
            self.theme_combo,
            self.from_format_label,
            self.source_format_combo,
            self.to_format_label,
            self.target_format_combo,
            self.add_files_button,
            self.remove_files_button,
            self.clear_files_button,
            self.output_line,
            self.output_button,
            self.source_folder_checkbox,
            self.overwrite_checkbox,
            self.delete_originals_checkbox,
            self.save_log_checkbox,
            self.open_when_done_checkbox,
            self.dpi_label,
            self.dpi_combo,
            self.quality_label,
            self.quality_combo,
            self.file_table,
            self.progress_label,
            self.details_button,
            self.cancel_button,
            self.start_button,
            self.log_view,
        )
        for widget in body_widgets:
            widget.setFont(body_font)

        self.title_label.setFont(header_font)
        self.summary_label.setFont(utility_font)
        self.file_table.horizontalHeader().setFont(utility_font)

    def changeEvent(self, event: object) -> None:
        """Keep custom title-bar controls in sync with window state."""
        super().changeEvent(event)
        if hasattr(self, "title_bar"):
            self.title_bar.set_maximized(self.isMaximized())

    def _apply_theme_decorations(self, theme: Theme) -> None:
        self.theme_surface.set_theme(theme)
        self.theme_header_art.set_theme(theme)
        self.theme_accent_line.set_theme(theme)
        self.resize_grip.set_theme(theme)

    def _apply_combo_popup_theme(self, theme: Theme) -> None:
        colors = colors_for(theme)
        body_font = QFont(BODY_FONT_FAMILY, 10)
        for combo in (
            self.theme_combo,
            self.source_format_combo,
            self.target_format_combo,
            self.dpi_combo,
            self.quality_combo,
        ):
            view = combo.view()
            view.setFont(body_font)
            view.setStyleSheet(combo_popup_stylesheet_for(theme))

            palette = view.palette()
            palette.setColor(QPalette.ColorRole.Base, QColor(colors["surface"]))
            palette.setColor(QPalette.ColorRole.Window, QColor(colors["surface"]))
            palette.setColor(QPalette.ColorRole.Text, QColor(colors["text"]))
            palette.setColor(QPalette.ColorRole.WindowText, QColor(colors["text"]))
            palette.setColor(QPalette.ColorRole.Highlight, QColor(colors["selection"]))
            palette.setColor(QPalette.ColorRole.HighlightedText, QColor(colors["text"]))
            view.setPalette(palette)

    def _source_format_changed(self) -> None:
        source_format = self.current_source_format
        if self.files and not self._confirm_format_change():
            self.source_format_combo.blockSignals(True)
            self.source_format_combo.setCurrentIndex(
                self.source_format_combo.findData(self._last_source_format)
            )
            self.source_format_combo.blockSignals(False)
            return

        if self.files:
            self.clear_files()
        self._last_source_format = source_format
        self._populate_target_formats(source_format)
        self._last_target_format = self.current_target_format
        self._update_format_options()

    def _target_format_changed(self) -> None:
        target_format = self.current_target_format
        if self.files and not self._confirm_format_change():
            self.target_format_combo.blockSignals(True)
            self.target_format_combo.setCurrentIndex(
                self.target_format_combo.findData(self._last_target_format)
            )
            self.target_format_combo.blockSignals(False)
            return

        if self.files:
            self.clear_files()
        self._last_target_format = target_format
        self._update_format_options()

    def _confirm_format_change(self) -> bool:
        return ask_ok_cancel(
            self,
            self.theme,
            "Switch formats?",
            "Changing formats starts a fresh queue. Want me to clear the current files and switch?",
            ok_text="Clear and switch",
            cancel_text="Keep current queue",
        )

    def _populate_target_formats(self, source_format: FileFormat) -> None:
        self.target_format_combo.blockSignals(True)
        self.target_format_combo.clear()
        for target_format in SUPPORTED_TARGETS[source_format]:
            self.target_format_combo.addItem(target_format.label, target_format)
        self.target_format_combo.blockSignals(False)

    def _update_format_options(self) -> None:
        source_format = self.current_source_format
        target_format = self.current_target_format
        show_dpi = (
            source_format is FileFormat.PDF and target_format.is_image
        ) or (
            source_format is FileFormat.IMAGES and target_format is FileFormat.PDF
        )
        show_quality = target_format in {FileFormat.JPEG, FileFormat.WEBP}
        self.dpi_label.setVisible(show_dpi)
        self.dpi_combo.setVisible(show_dpi)
        self.quality_label.setVisible(show_quality)
        self.quality_combo.setVisible(show_quality)

    def add_files(self) -> None:
        mode = self.current_mode
        files, _ = QFileDialog.getOpenFileNames(
            self,
            f"Select {mode.source_format.label} files",
            "",
            mode.file_dialog_filter,
        )
        if not files:
            return

        existing = {path.resolve() for path in self.files}
        added = 0
        for file_name in files:
            path = Path(file_name).resolve()
            if path in existing:
                continue
            if not mode.source_format.accepts(path):
                continue
            if mode.source_format is FileFormat.IMAGES and mode.target_format.accepts(path):
                continue
            self.files.append(path)
            existing.add(path)
            added += 1

        if added:
            self._populate_file_table()
            self._append_log(f"Added {_file_count(added)}.")
        self._refresh_controls()

    def remove_selected_files(self) -> None:
        selected_rows = sorted({item.row() for item in self.file_table.selectedItems()}, reverse=True)
        if not selected_rows:
            return

        for row in selected_rows:
            del self.files[row]
        self._populate_file_table()
        self._append_log(f"Removed {_file_count(len(selected_rows))}.")
        self._refresh_controls()

    def clear_files(self) -> None:
        self.files.clear()
        self.file_table.setRowCount(0)
        self.summary_label.setText("0 files")
        self.progress_bar.setValue(0)
        self.progress_label.setText("Ready")
        self._append_log("Cleared selected files.")
        self._refresh_controls()

    def choose_output_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select output folder")
        if not folder:
            return
        self.output_folder = Path(folder).resolve()
        self.source_folder_checkbox.setChecked(False)
        self._set_output_display()
        self._append_log(f"Output folder set to {self.output_folder}.")
        self._refresh_controls()

    def _source_folder_toggled(self, checked: bool) -> None:
        if checked:
            self.output_folder = None
        self._set_output_display()
        self._refresh_controls()

    def _set_output_display(self) -> None:
        if self.source_folder_checkbox.isChecked():
            self.output_line.setText("Original folders")
            return
        if self.output_folder is None:
            self.output_line.setText("Choose output folder")
            return
        self.output_line.setText(str(self.output_folder))

    def start_conversion(self) -> None:
        if not self.files:
            show_warning(
                self,
                self.theme,
                "Nothing to convert yet",
                "Add a compatible source file first, then I'll take it from there.",
            )
            return

        output_folder = None if self.source_folder_checkbox.isChecked() else self.output_folder
        if output_folder is None and not self.source_folder_checkbox.isChecked():
            show_warning(
                self,
                self.theme,
                "Where should these go?",
                "Choose an output folder, or switch back to Original folders.",
            )
            return

        options = ConversionOptions(
            mode=self.current_mode,
            files=tuple(self.files),
            output_folder=output_folder,
            overwrite_existing=self.overwrite_checkbox.isChecked(),
            delete_originals=self.delete_originals_checkbox.isChecked(),
            save_log=self.save_log_checkbox.isChecked(),
            image_dpi=int(self.dpi_combo.currentData()),
            image_quality=int(self.quality_combo.currentData()),
        )

        self.worker = ConversionWorker(options)
        self.worker.progress_changed.connect(self._update_progress)
        self.worker.log_line.connect(self._append_log)
        self.worker.result_ready.connect(self._update_result)
        self.worker.batch_ready.connect(self._finish_batch)
        self.worker.finished.connect(self._worker_finished)

        self.log_view.clear()
        self._mark_all_files("Queued")
        self.summary_label.setText(f"{len(self.files)} queued")
        self.progress_label.setText("Starting...")
        self._set_busy(True)
        self.worker.start()

    def cancel_conversion(self) -> None:
        if self.worker is None:
            return
        self.worker.cancel()
        self.cancel_button.setEnabled(False)
        self.progress_label.setText("Cancelling after the current file...")

    def _update_progress(self, completed: int, total: int, message: str) -> None:
        value = int((completed / total) * 100) if total else 0
        self.progress_bar.setValue(value)
        self.progress_label.setText(f"{message} ({completed}/{total})")
        self.summary_label.setText(f"{completed}/{total} complete")

    def _update_result(self, result: ConversionResult) -> None:
        row = self._row_for_path(result.source)
        if row is None:
            return

        if result.original_deleted is False:
            status = "Done (source kept)"
        else:
            status = "Done" if result.succeeded else "Failed"
        self._set_row_status(row, status, result.succeeded)

    def _finish_batch(self, summary: BatchSummary, results: list[ConversionResult]) -> None:
        self.progress_bar.setValue(100 if summary.total else 0)
        originals_kept = sum(result.original_deleted is False for result in results)
        completed_successfully = (
            not summary.cancelled and not summary.failed and not originals_kept
        )
        if summary.cancelled:
            title = "Stopped for now"
            message = (
                f"I stopped after {_file_count(summary.succeeded)} out of {_file_count(summary.total)}. "
                "I left the queue in place so you can decide what to run next."
            )
            show_completion = show_warning
        elif summary.failed:
            title = "A few need a look"
            message = (
                f"I converted {_file_count(summary.succeeded)}, but {_file_count(summary.failed)} "
                "didn't make it through. I left the list open so you can review the details."
            )
            show_completion = show_warning
        else:
            title = "All set"
            message = f"Nice. I converted {_file_count(summary.succeeded)} and reset the queue for your next batch."
            show_completion = show_information

        if originals_kept:
            cleanup_message = (
                f"I couldn't delete {_file_count(originals_kept)}. The converted files "
                "are ready, and those originals are still on disk."
            )
            if not summary.cancelled and not summary.failed:
                title = "Converted, but kept originals"
                message = cleanup_message
            else:
                message = f"{message}\n\n{cleanup_message}"
            show_completion = show_warning

        if summary.log_file:
            message = f"{message}\n\nI saved the run log here:\n{summary.log_file}"

        self.summary_label.setText(title)
        self.progress_label.setText(message.split("\n", maxsplit=1)[0])

        show_completion(self, self.theme, title, message)

        if completed_successfully:
            self._reset_completed_queue()

        if (
            self.open_when_done_checkbox.isChecked()
            and not summary.failed
            and not summary.cancelled
        ):
            folder = self._folder_to_open(results, summary)
            if folder:
                try:
                    open_folder(folder)
                except Exception as exc:
                    show_warning(
                        self,
                        self.theme,
                        "Done, but I couldn't open the folder",
                        f"The files are converted. I just couldn't open the output folder automatically.\n\n{exc}",
                    )

    def _worker_finished(self) -> None:
        self.worker = None
        self._set_busy(False)
        self._refresh_controls()

    def _reset_completed_queue(self) -> None:
        """Clear successful queue state while keeping the run log available."""
        self.files.clear()
        self.file_table.setRowCount(0)
        self.summary_label.setText("0 files")
        self.progress_bar.setValue(0)
        self.progress_label.setText("Ready")
        self._refresh_controls()

    def _populate_file_table(self) -> None:
        self.file_table.setRowCount(len(self.files))
        for row, path in enumerate(self.files):
            file_item = QTableWidgetItem(path.name)
            file_item.setData(Qt.ItemDataRole.UserRole, str(path))
            file_item.setToolTip(str(path))
            type_item = QTableWidgetItem(path.suffix.lower())
            type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            status_item = QTableWidgetItem("Ready")
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            self.file_table.setItem(row, 0, file_item)
            self.file_table.setItem(row, 1, type_item)
            self.file_table.setItem(row, self.STATUS_COLUMN, status_item)

        self.summary_label.setText(_file_count(len(self.files)))

    def _mark_all_files(self, status: str) -> None:
        for row in range(self.file_table.rowCount()):
            self._set_row_status(row, status, None)

    def _set_row_status(self, row: int, status: str, succeeded: bool | None) -> None:
        item = self.file_table.item(row, self.STATUS_COLUMN)
        if item is None:
            item = QTableWidgetItem()
            self.file_table.setItem(row, self.STATUS_COLUMN, item)
        item.setText(status)
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

        colors = colors_for(self.theme)
        if succeeded is True:
            color = colors["success"]
        elif succeeded is False:
            color = colors["danger"]
        else:
            color = colors["muted"]
        item.setForeground(QColor(color))

    def _refresh_status_colors(self) -> None:
        for row in range(self.file_table.rowCount()):
            item = self.file_table.item(row, self.STATUS_COLUMN)
            if item is None:
                continue
            text = item.text()
            if text.startswith("Done"):
                self._set_row_status(row, text, True)
            elif text == "Failed":
                self._set_row_status(row, text, False)
            else:
                self._set_row_status(row, text, None)

    def _row_for_path(self, path: Path) -> int | None:
        target = str(path.resolve())
        for row in range(self.file_table.rowCount()):
            item = self.file_table.item(row, 0)
            if item and item.data(Qt.ItemDataRole.UserRole) == target:
                return row
        return None

    def _append_log(self, line: str) -> None:
        self.log_view.appendPlainText(line)

    def _set_busy(self, busy: bool) -> None:
        self.theme_combo.setEnabled(not busy)
        self.source_format_combo.setEnabled(not busy)
        self.target_format_combo.setEnabled(not busy)
        self.add_files_button.setEnabled(not busy)
        self.remove_files_button.setEnabled(not busy and bool(self.files))
        self.clear_files_button.setEnabled(not busy and bool(self.files))
        self.source_folder_checkbox.setEnabled(not busy)
        self.output_button.setEnabled(not busy)
        self.overwrite_checkbox.setEnabled(not busy)
        self.delete_originals_checkbox.setEnabled(not busy)
        self.save_log_checkbox.setEnabled(not busy)
        self.open_when_done_checkbox.setEnabled(not busy)
        self.dpi_combo.setEnabled(not busy)
        self.quality_combo.setEnabled(not busy)
        self.start_button.setEnabled(not busy and bool(self.files))
        self.cancel_button.setEnabled(busy)

    def _refresh_controls(self) -> None:
        busy = self.worker is not None
        self.remove_files_button.setEnabled(not busy and bool(self.files))
        self.clear_files_button.setEnabled(not busy and bool(self.files))
        self.start_button.setEnabled(not busy and bool(self.files))
        self.cancel_button.setEnabled(busy)
        self.output_button.setEnabled(not busy)

    def _folder_to_open(
        self,
        results: list[ConversionResult],
        summary: BatchSummary,
    ) -> Path | None:
        if summary.log_file:
            return summary.log_file.parent
        for result in results:
            if result.output:
                return result.output if result.output.is_dir() else result.output.parent
        return self.output_folder


def run_app(argv: list[str] | None = None) -> int:
    """Create and run the Qt application."""
    app = QApplication(argv if argv is not None else sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(ORGANIZATION_NAME)
    load_theme_fonts()
    app.setWindowIcon(app_icon())

    window = MainWindow()
    window.show()

    return app.exec()
