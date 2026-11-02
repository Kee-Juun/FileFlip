"""Restart-level tests for persisted FileFlip UI preferences."""

from __future__ import annotations

import os
import shutil
import unittest
from pathlib import Path
from uuid import uuid4

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import QApplication

from core.models import FileFormat
from ui import gui


class PreferencePersistenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self) -> None:
        self.root = Path(__file__).parent / f".fileflip-preferences-{uuid4().hex}"
        self.root.mkdir()
        self.settings_path = self.root / "settings.ini"
        self.original_qsettings = gui.QSettings
        gui.QSettings = lambda *_args: QSettings(
            str(self.settings_path),
            QSettings.Format.IniFormat,
        )

    def tearDown(self) -> None:
        gui.QSettings = self.original_qsettings
        shutil.rmtree(self.root)

    def test_route_checkboxes_and_image_options_survive_restart(self) -> None:
        first = gui.MainWindow()
        first.source_format_combo.setCurrentIndex(
            first.source_format_combo.findData(FileFormat.IMAGES)
        )
        first.target_format_combo.setCurrentIndex(
            first.target_format_combo.findData(FileFormat.WEBP)
        )
        first.source_folder_checkbox.setChecked(False)
        first.overwrite_checkbox.setChecked(True)
        first.delete_originals_checkbox.setChecked(True)
        first.save_log_checkbox.setChecked(False)
        first.open_when_done_checkbox.setChecked(False)
        first.dpi_combo.setCurrentIndex(first.dpi_combo.findData(300))
        first.quality_combo.setCurrentIndex(first.quality_combo.findData(100))
        first.settings.sync()
        first.close()
        first.deleteLater()
        self.app.processEvents()

        restored = gui.MainWindow()
        try:
            self.assertIs(restored.current_source_format, FileFormat.IMAGES)
            self.assertIs(restored.current_target_format, FileFormat.WEBP)
            self.assertFalse(restored.source_folder_checkbox.isChecked())
            self.assertTrue(restored.overwrite_checkbox.isChecked())
            self.assertTrue(restored.delete_originals_checkbox.isChecked())
            self.assertFalse(restored.save_log_checkbox.isChecked())
            self.assertFalse(restored.open_when_done_checkbox.isChecked())
            self.assertEqual(restored.dpi_combo.currentData(), 300)
            self.assertEqual(restored.quality_combo.currentData(), 100)
        finally:
            restored.close()
            restored.deleteLater()
            self.app.processEvents()


if __name__ == "__main__":
    unittest.main()
