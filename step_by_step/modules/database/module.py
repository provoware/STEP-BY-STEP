"""Database helper module for managing archive entries."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from ...core.validators import ensure_unique

ARCHIVE_FILE = Path("data/archive.json")


class DatabaseModule:
    """Simple record store with duplicate checking."""

    def __init__(self, storage_file: Path = ARCHIVE_FILE) -> None:
        self.storage_file = storage_file
        self.storage_file.parent.mkdir(parents=True, exist_ok=True)

    def list_entries(self) -> List[Dict[str, str]]:
        if not self.storage_file.exists():
            return []
        try:
            data = json.loads(self.storage_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
        return data.get("entries", [])

    def add_entry(self, title: str, description: str) -> bool:
        entries = self.list_entries()
        titles = [entry.get("title", "") for entry in entries] + [title]
        if not ensure_unique(titles):
            return False
        entries.append({"title": title, "description": description})
        self.storage_file.write_text(
            json.dumps({"entries": entries}, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return True


__all__ = ["DatabaseModule"]
