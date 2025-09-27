"""Utility helpers to inspect and search log files."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass
class LogEntry:
    """Represent a single line inside a log file."""

    line_number: int
    content: str


class LogReader:
    """Read and search textual log files in a safe way."""

    def __init__(self, file_path: Path) -> None:
        self.file_path = file_path
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    def ensure_exists(self) -> None:
        """Create the log file if it is currently missing."""

        if not self.file_path.exists():
            self.file_path.touch()

    # ------------------------------------------------------------------
    def read_tail(self, limit: int = 50) -> List[LogEntry]:
        """Return the ``limit`` latest lines from the log file."""

        self.ensure_exists()
        lines = self._read_lines()
        start_index = max(0, len(lines) - limit)
        return [
            LogEntry(line_number=index + 1, content=line.rstrip("\n"))
            for index, line in enumerate(lines[start_index:])
        ]

    # ------------------------------------------------------------------
    def search(self, term: str, limit: int = 50) -> List[LogEntry]:
        """Return log lines that contain ``term`` (case-insensitive)."""

        self.ensure_exists()
        term_cf = term.casefold()
        matches: List[LogEntry] = []
        if not term_cf:
            return self.read_tail(limit=limit)
        for index, line in enumerate(self._read_lines()):
            if term_cf in line.casefold():
                matches.append(LogEntry(line_number=index + 1, content=line.rstrip("\n")))
            if len(matches) >= limit:
                break
        return matches

    # ------------------------------------------------------------------
    def _read_lines(self) -> List[str]:
        try:
            return self.file_path.read_text(encoding="utf-8").splitlines()
        except UnicodeDecodeError:
            # Fallback: read as latin-1 to avoid crashes and still show lines
            return self.file_path.read_text(encoding="latin-1").splitlines()


__all__ = ["LogEntry", "LogReader"]

