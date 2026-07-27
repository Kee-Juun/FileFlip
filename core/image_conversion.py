"""Reliable PDF and raster-image conversion helpers."""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from uuid import uuid4

import fitz
from PIL import Image, ImageOps, ImageSequence

from .models import FileFormat


class ImageConversionError(RuntimeError):
    """Raised when PDF rendering or raster conversion cannot finish."""


def pdf_page_count(pdf_path: Path) -> int:
    """Return the number of pages in a readable, unlocked PDF."""
    try:
        with fitz.open(str(pdf_path)) as document:
            if document.needs_pass:
                raise ImageConversionError("Password-protected PDFs are not supported yet.")
            if document.page_count < 1:
                raise ImageConversionError("The PDF does not contain any pages.")
            return document.page_count
    except ImageConversionError:
        raise
    except Exception as exc:
        raise ImageConversionError(f"Could not read the PDF: {exc}") from exc


def image_frame_count(image_path: Path) -> int:
    """Return the number of frames/pages in a supported raster image."""
    try:
        with Image.open(image_path) as image:
            return max(1, int(getattr(image, "n_frames", 1)))
    except Exception as exc:
        raise ImageConversionError(f"Could not read the image: {exc}") from exc


def convert_pdf_to_images(
    pdf_path: Path,
    destination: Path,
    target_format: FileFormat,
    *,
    dpi: int,
    quality: int,
) -> tuple[Path, ...]:
    """Render a PDF to one image, a multipage TIFF, or a page directory."""
    if target_format not in {FileFormat.PNG, FileFormat.JPEG, FileFormat.TIFF}:
        raise ImageConversionError(f"PDF rendering to {target_format.label} is not supported.")

    try:
        with fitz.open(str(pdf_path)) as document:
            if document.needs_pass:
                raise ImageConversionError("Password-protected PDFs are not supported yet.")
            if document.page_count < 1:
                raise ImageConversionError("The PDF does not contain any pages.")

            if destination.suffix:
                frames = [_render_pdf_page(page, dpi) for page in document]
                try:
                    _save_frames_atomic(frames, destination, target_format, dpi=dpi, quality=quality)
                finally:
                    _close_frames(frames)
                return (destination,)

            return _render_pdf_pages_to_directory(
                document,
                destination,
                target_format,
                dpi=dpi,
                quality=quality,
            )
    except ImageConversionError:
        raise
    except Exception as exc:
        raise ImageConversionError(f"Could not render the PDF: {exc}") from exc


def convert_image(
    image_path: Path,
    destination: Path,
    target_format: FileFormat,
    *,
    dpi: int,
    quality: int,
) -> tuple[Path, ...]:
    """Convert a raster image, preserving multiple frames where possible."""
    frames = _load_image_frames(image_path)
    try:
        if destination.suffix:
            _save_frames_atomic(frames, destination, target_format, dpi=dpi, quality=quality)
            return (destination,)
        return _save_frames_to_directory(
            frames,
            destination,
            target_format,
            dpi=dpi,
            quality=quality,
        )
    finally:
        _close_frames(frames)


def _render_pdf_page(page: fitz.Page, dpi: int) -> Image.Image:
    scale = max(72, dpi) / 72
    pixmap = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
    return Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)


def _render_pdf_pages_to_directory(
    document: fitz.Document,
    destination: Path,
    target_format: FileFormat,
    *,
    dpi: int,
    quality: int,
) -> tuple[Path, ...]:
    temp_dir = _create_staging_directory(destination.parent, ".fileflip-pages-")
    try:
        for page_number, page in enumerate(document, start=1):
            frame = _render_pdf_page(page, dpi)
            try:
                page_path = temp_dir / f"page_{page_number:03d}{target_format.output_suffix}"
                _save_single_frame(frame, page_path, target_format, dpi=dpi, quality=quality)
            finally:
                frame.close()
        temp_dir.replace(destination)
    except Exception:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise
    return tuple(sorted(destination.glob(f"*{target_format.output_suffix}")))


def _load_image_frames(image_path: Path) -> list[Image.Image]:
    try:
        with Image.open(image_path) as image:
            frames = [ImageOps.exif_transpose(frame.copy()) for frame in ImageSequence.Iterator(image)]
    except Exception as exc:
        raise ImageConversionError(f"Could not decode the image: {exc}") from exc
    if not frames:
        raise ImageConversionError("The image does not contain a readable frame.")
    return frames


def _save_frames_to_directory(
    frames: list[Image.Image],
    destination: Path,
    target_format: FileFormat,
    *,
    dpi: int,
    quality: int,
) -> tuple[Path, ...]:
    temp_dir = _create_staging_directory(destination.parent, ".fileflip-frames-")
    try:
        for frame_number, frame in enumerate(frames, start=1):
            frame_path = temp_dir / f"frame_{frame_number:03d}{target_format.output_suffix}"
            _save_single_frame(frame, frame_path, target_format, dpi=dpi, quality=quality)
        temp_dir.replace(destination)
    except Exception:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise
    return tuple(sorted(destination.glob(f"*{target_format.output_suffix}")))


def _save_frames_atomic(
    frames: list[Image.Image],
    destination: Path,
    target_format: FileFormat,
    *,
    dpi: int,
    quality: int,
) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(
        f".{destination.stem}.{uuid4().hex}.tmp{destination.suffix}"
    )
    try:
        if len(frames) == 1:
            _save_single_frame(frames[0], temporary, target_format, dpi=dpi, quality=quality)
        else:
            _save_multiple_frames(frames, temporary, target_format, dpi=dpi, quality=quality)
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)


def _save_multiple_frames(
    frames: list[Image.Image],
    destination: Path,
    target_format: FileFormat,
    *,
    dpi: int,
    quality: int,
) -> None:
    if target_format is FileFormat.PDF:
        prepared = [_flatten_to_rgb(frame) for frame in frames]
        try:
            prepared[0].save(
                destination,
                format="PDF",
                save_all=True,
                append_images=prepared[1:],
                resolution=dpi,
            )
        finally:
            _close_frames(prepared)
        return

    if target_format is FileFormat.TIFF:
        prepared = [_prepare_for_format(frame, target_format) for frame in frames]
        try:
            prepared[0].save(
                destination,
                format="TIFF",
                save_all=True,
                append_images=prepared[1:],
                compression="tiff_deflate",
                dpi=(dpi, dpi),
            )
        finally:
            _close_frames(prepared)
        return

    if target_format is FileFormat.WEBP:
        prepared = [_prepare_for_format(frame, target_format) for frame in frames]
        try:
            prepared[0].save(
                destination,
                format="WEBP",
                save_all=True,
                append_images=prepared[1:],
                quality=quality,
                method=6,
                duration=100,
                loop=0,
            )
        finally:
            _close_frames(prepared)
        return

    raise ImageConversionError(
        f"Multiple frames cannot be stored in one {target_format.label} file."
    )


def _save_single_frame(
    frame: Image.Image,
    destination: Path,
    target_format: FileFormat,
    *,
    dpi: int,
    quality: int,
) -> None:
    prepared = _prepare_for_format(frame, target_format)
    try:
        if target_format is FileFormat.PDF:
            prepared.save(destination, format="PDF", resolution=dpi)
        elif target_format is FileFormat.PNG:
            prepared.save(destination, format="PNG", optimize=True, dpi=(dpi, dpi))
        elif target_format is FileFormat.JPEG:
            prepared.save(
                destination,
                format="JPEG",
                quality=quality,
                optimize=True,
                dpi=(dpi, dpi),
            )
        elif target_format is FileFormat.TIFF:
            prepared.save(
                destination,
                format="TIFF",
                compression="tiff_deflate",
                dpi=(dpi, dpi),
            )
        elif target_format is FileFormat.WEBP:
            prepared.save(destination, format="WEBP", quality=quality, method=6)
        elif target_format is FileFormat.BMP:
            prepared.save(destination, format="BMP")
        else:
            raise ImageConversionError(f"Unsupported image output: {target_format.label}")
    finally:
        prepared.close()


def _prepare_for_format(frame: Image.Image, target_format: FileFormat) -> Image.Image:
    if target_format in {FileFormat.PDF, FileFormat.JPEG, FileFormat.BMP}:
        return _flatten_to_rgb(frame)
    if frame.mode in {"RGB", "RGBA", "L", "LA"}:
        return frame.copy()
    return frame.convert("RGBA" if "transparency" in frame.info else "RGB")


def _flatten_to_rgb(frame: Image.Image) -> Image.Image:
    if frame.mode == "RGB":
        return frame.copy()
    if frame.mode in {"RGBA", "LA"} or "transparency" in frame.info:
        rgba = frame.convert("RGBA")
        background = Image.new("RGBA", rgba.size, "white")
        background.alpha_composite(rgba)
        rgb = background.convert("RGB")
        rgba.close()
        background.close()
        return rgb
    return frame.convert("RGB")


def _close_frames(frames: list[Image.Image]) -> None:
    for frame in frames:
        frame.close()


def _create_staging_directory(parent: Path, prefix: str) -> Path:
    """Create a private staging folder without tempfile's restrictive Windows ACLs."""
    parent.mkdir(parents=True, exist_ok=True)
    for _ in range(100):
        candidate = parent / f"{prefix}{uuid4().hex}"
        try:
            candidate.mkdir()
        except FileExistsError:
            continue
        return candidate
    raise ImageConversionError("Could not create a temporary output folder.")
