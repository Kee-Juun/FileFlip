"""Shared data models for conversion and UI state."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


IMAGE_SUFFIXES = (".png", ".jpg", ".jpeg", ".tif", ".tiff", ".webp", ".bmp", ".gif")


class FileFormat(Enum):
    """Source families and concrete output formats supported by FileFlip."""

    PDF = ("pdf", "PDF", (".pdf",), ".pdf")
    WORD = ("word", "Word", (".docx",), ".docx")
    IMAGES = ("images", "Images", IMAGE_SUFFIXES, None)
    PNG = ("png", "PNG", (".png",), ".png")
    JPEG = ("jpeg", "JPG", (".jpg", ".jpeg"), ".jpg")
    TIFF = ("tiff", "TIFF", (".tif", ".tiff"), ".tiff")
    WEBP = ("webp", "WebP", (".webp",), ".webp")
    BMP = ("bmp", "BMP", (".bmp",), ".bmp")

    def __init__(
        self,
        key: str,
        label: str,
        source_suffixes: tuple[str, ...],
        output_suffix: str | None,
    ) -> None:
        self.key = key
        self.label = label
        self.source_suffixes = source_suffixes
        self.output_suffix = output_suffix

    @property
    def is_image(self) -> bool:
        return self in {
            FileFormat.IMAGES,
            FileFormat.PNG,
            FileFormat.JPEG,
            FileFormat.TIFF,
            FileFormat.WEBP,
            FileFormat.BMP,
        }

    @property
    def file_dialog_filter(self) -> str:
        patterns = " ".join(f"*{suffix}" for suffix in self.source_suffixes)
        return f"{self.label} files ({patterns})"

    def accepts(self, path: Path) -> bool:
        return path.suffix.lower() in self.source_suffixes


SOURCE_FORMATS = (FileFormat.PDF, FileFormat.WORD, FileFormat.IMAGES)

SUPPORTED_TARGETS = {
    FileFormat.PDF: (FileFormat.WORD, FileFormat.PNG, FileFormat.JPEG, FileFormat.TIFF),
    FileFormat.WORD: (FileFormat.PDF,),
    FileFormat.IMAGES: (
        FileFormat.PDF,
        FileFormat.PNG,
        FileFormat.JPEG,
        FileFormat.TIFF,
        FileFormat.WEBP,
        FileFormat.BMP,
    ),
}


@dataclass(frozen=True)
class ConversionMode:
    """A validated source-to-target conversion route."""

    source_format: FileFormat
    target_format: FileFormat

    def __post_init__(self) -> None:
        if self.target_format not in SUPPORTED_TARGETS.get(self.source_format, ()):
            raise ValueError(
                f"Unsupported conversion: {self.source_format.label} to {self.target_format.label}"
            )

    @property
    def key(self) -> str:
        return f"{self.source_format.key}_to_{self.target_format.key}"

    @property
    def label(self) -> str:
        return f"{self.source_format.label} to {self.target_format.label}"

    @property
    def file_dialog_filter(self) -> str:
        return self.source_format.file_dialog_filter

    @classmethod
    def from_formats(
        cls,
        source_format: FileFormat,
        target_format: FileFormat,
    ) -> "ConversionMode":
        return cls(source_format=source_format, target_format=target_format)

    @classmethod
    def from_label(cls, label: str) -> "ConversionMode":
        """Return a supported route represented by its display label."""
        for source_format in SOURCE_FORMATS:
            for target_format in SUPPORTED_TARGETS[source_format]:
                mode = cls(source_format, target_format)
                if mode.label == label:
                    return mode
        raise ValueError(f"Unknown conversion mode: {label}")


@dataclass(frozen=True)
class ConversionOptions:
    """Options that apply to a batch conversion run."""

    mode: ConversionMode
    files: tuple[Path, ...]
    output_folder: Path | None = None
    overwrite_existing: bool = False
    delete_originals: bool = False
    save_log: bool = True
    image_dpi: int = 200
    image_quality: int = 90


@dataclass(frozen=True)
class ConversionResult:
    """Result for a single source document."""

    source: Path
    output: Path | None
    succeeded: bool
    message: str
    elapsed_seconds: float
    original_deleted: bool | None = None
    outputs: tuple[Path, ...] = ()


@dataclass(frozen=True)
class BatchSummary:
    """Final result for a conversion batch."""

    total: int
    succeeded: int
    failed: int
    cancelled: bool
    log_file: Path | None
