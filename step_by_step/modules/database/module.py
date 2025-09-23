"""Database helper module for managing archive entries."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Dict, List, Optional

from ...core.validators import ensure_unique

ARCHIVE_FILE = Path("data/archive.json")
EXPORT_DIR = Path("data/exports")


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
        return sorted(
            data.get("entries", []),
            key=lambda entry: entry.get("title", "").casefold(),
        )

    def add_entry(self, title: str, description: str) -> bool:
        entries = self.list_entries()
        titles = [entry.get("title", "") for entry in entries] + [title]
        if not ensure_unique(titles):
            return False
        entries.append({"title": title, "description": description})
        self._write(entries)
        return True

    def search(self, term: str) -> List[Dict[str, str]]:
        term_cf = term.casefold()
        return [
            entry
            for entry in self.list_entries()
            if term_cf in entry.get("title", "").casefold()
            or term_cf in entry.get("description", "").casefold()
        ]

    def filter_by_prefix(self, prefix: str) -> List[Dict[str, str]]:
        prefix_cf = prefix.casefold()
        return [
            entry
            for entry in self.list_entries()
            if entry.get("title", "").casefold().startswith(prefix_cf)
        ]

    def remove(self, title: str) -> bool:
        entries = self.list_entries()
        filtered = [entry for entry in entries if entry.get("title") != title]
        if len(filtered) == len(entries):
            return False
        self._write(filtered)
        return True

    def get_entry(self, title: str) -> Optional[Dict[str, str]]:
        for entry in self.list_entries():
            if entry.get("title") == title:
                return entry
        return None

    def _write(self, entries: List[Dict[str, str]]) -> None:
        payload = {"entries": sorted(entries, key=lambda entry: entry.get("title", "").casefold())}
        self.storage_file.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def export_entries_to_csv(self, target: Optional[Path] = None) -> Path:
        entries = self.list_entries()
        EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        target_path = target or EXPORT_DIR / "archive_export.csv"
        with target_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=["title", "description"])
            writer.writeheader()
            for entry in entries:
                writer.writerow({
                    "title": entry.get("title", ""),
                    "description": entry.get("description", ""),
                })
        return target_path

    def export_entries_to_json(self, target: Optional[Path] = None) -> Path:
        entries = self.list_entries()
        EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        target_path = target or EXPORT_DIR / "archive_export.json"
        payload = {"entries": entries}
        target_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        return target_path


__all__ = ["DatabaseModule"]
