"""Regression tests for FileFlip's raster conversion routes."""

from __future__ import annotations

import shutil
import unittest
from pathlib import Path
from uuid import uuid4

import fitz
from PIL import Image

from core.converter import DocumentConverter
from core.models import ConversionMode, FileFormat, SUPPORTED_TARGETS


class ImageConversionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(__file__).parent / f".fileflip-test-{uuid4().hex}"
        self.root.mkdir()

    def tearDown(self) -> None:
        shutil.rmtree(self.root)

    def test_supported_target_matrix(self) -> None:
        self.assertEqual(
            SUPPORTED_TARGETS[FileFormat.PDF],
            (FileFormat.WORD, FileFormat.PNG, FileFormat.JPEG, FileFormat.TIFF),
        )
        self.assertEqual(SUPPORTED_TARGETS[FileFormat.WORD], (FileFormat.PDF,))
        self.assertIn(FileFormat.PDF, SUPPORTED_TARGETS[FileFormat.IMAGES])
        self.assertIn(FileFormat.WEBP, SUPPORTED_TARGETS[FileFormat.IMAGES])

    def test_multipage_pdf_to_png_directory(self) -> None:
        source = self.root / "two-pages.pdf"
        document = fitz.open()
        for label in ("Page one", "Page two"):
            page = document.new_page(width=144, height=144)
            page.insert_text((20, 72), label)
        document.save(source)
        document.close()

        with DocumentConverter() as converter:
            result = converter.convert(
                source,
                ConversionMode(FileFormat.PDF, FileFormat.PNG),
                self.root / "output",
                False,
                image_dpi=150,
            )

        self.assertTrue(result.succeeded, result.message)
        self.assertIsNotNone(result.output)
        self.assertTrue(result.output.is_dir())
        self.assertEqual([path.name for path in result.outputs], ["page_001.png", "page_002.png"])

    def test_transparent_png_to_jpeg_flattens_on_white(self) -> None:
        source = self.root / "transparent.png"
        Image.new("RGBA", (20, 20), (255, 0, 0, 0)).save(source)

        with DocumentConverter() as converter:
            result = converter.convert(
                source,
                ConversionMode(FileFormat.IMAGES, FileFormat.JPEG),
                self.root / "output",
                False,
                image_quality=95,
            )

        self.assertTrue(result.succeeded, result.message)
        with Image.open(result.output) as converted:
            red, green, blue = converted.convert("RGB").getpixel((10, 10))
        self.assertGreater(red, 245)
        self.assertGreater(green, 245)
        self.assertGreater(blue, 245)

    def test_animated_gif_to_multipage_pdf(self) -> None:
        source = self.root / "animated.gif"
        frames = [Image.new("RGB", (20, 20), color) for color in ("red", "blue")]
        frames[0].save(source, save_all=True, append_images=frames[1:], duration=100, loop=0)
        for frame in frames:
            frame.close()

        with DocumentConverter() as converter:
            result = converter.convert(
                source,
                ConversionMode(FileFormat.IMAGES, FileFormat.PDF),
                self.root / "output",
                False,
            )

        self.assertTrue(result.succeeded, result.message)
        with fitz.open(result.output) as converted:
            self.assertEqual(converted.page_count, 2)

    def test_static_gif_converts_to_every_supported_image_destination(self) -> None:
        source = self.root / "source.gif"
        Image.new("RGB", (20, 20), "green").save(source)
        targets = (
            FileFormat.PDF,
            FileFormat.PNG,
            FileFormat.JPEG,
            FileFormat.TIFF,
            FileFormat.WEBP,
            FileFormat.BMP,
        )

        with DocumentConverter() as converter:
            results = [
                converter.convert(
                    source,
                    ConversionMode(FileFormat.IMAGES, target),
                    self.root / "output",
                    False,
                )
                for target in targets
            ]

        for target, result in zip(targets, results, strict=True):
            self.assertTrue(result.succeeded, f"{target.label}: {result.message}")
            self.assertTrue(result.output.is_file())

    def test_pdf_converts_to_each_supported_image_destination(self) -> None:
        source = self.root / "one-page.pdf"
        document = fitz.open()
        document.new_page(width=72, height=72)
        document.save(source)
        document.close()

        with DocumentConverter() as converter:
            results = [
                converter.convert(
                    source,
                    ConversionMode(FileFormat.PDF, target),
                    self.root / "output",
                    False,
                    image_dpi=150,
                )
                for target in (FileFormat.PNG, FileFormat.JPEG, FileFormat.TIFF)
            ]

        for result in results:
            self.assertTrue(result.succeeded, result.message)
            self.assertTrue(result.output.is_file())

    def test_same_stem_sources_get_distinct_outputs_even_with_overwrite(self) -> None:
        first_folder = self.root / "first"
        second_folder = self.root / "second"
        output_folder = self.root / "output"
        first_folder.mkdir()
        second_folder.mkdir()
        first = first_folder / "sample.png"
        second = second_folder / "sample.jpg"
        Image.new("RGB", (10, 10), "red").save(first)
        Image.new("RGB", (10, 10), "blue").save(second)

        mode = ConversionMode(FileFormat.IMAGES, FileFormat.TIFF)
        with DocumentConverter() as converter:
            first_result = converter.convert(first, mode, output_folder, True)
            second_result = converter.convert(second, mode, output_folder, True)

        self.assertTrue(first_result.succeeded, first_result.message)
        self.assertTrue(second_result.succeeded, second_result.message)
        self.assertNotEqual(first_result.output, second_result.output)
        self.assertEqual(first_result.output.name, "sample.tiff")
        self.assertEqual(second_result.output.name, "sample (1).tiff")


if __name__ == "__main__":
    unittest.main()
