"""Session logging helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


@dataclass
class SessionLog:
    """Collect timestamped log lines and persist them at the end of a run."""

    lines: list[str] = field(default_factory=list)

    def add(self, level: str, message: str) -> str:
        """Append a formatted line and return it for UI display."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"{timestamp} [{level.upper()}] {message}"
        self.lines.append(line)
        return line

    def save(self, folder: Path) -> Path:
        """Write the session log into ``folder`` and return the created path."""
        folder.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_path = folder / f"fileflip-log_{timestamp}.txt"
        log_path.write_text("\n".join(self.lines) + "\n", encoding="utf-8")
        return log_path
