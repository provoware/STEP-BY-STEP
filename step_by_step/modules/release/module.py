"""Release checklist helpers."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from ...core.file_utils import atomic_write_json


CHECKLIST_FILE = Path("data/release_checklist.json")


@dataclass
class ReleaseChecklistItem:
    """Represent a single release checklist entry."""

    title: str
    done: bool
    details: str

    @classmethod
    def from_dict(cls, raw: Dict[str, object]) -> "ReleaseChecklistItem":
        return cls(
            title=str(raw.get("title", "")),
            done=bool(raw.get("done", False)),
            details=str(raw.get("details", "")),
        )

    def to_dict(self) -> Dict[str, object]:
        return {"title": self.title, "done": self.done, "details": self.details}


class ReleaseChecklist:
    """Load and persist release checklist information."""

    def __init__(self, storage_file: Path = CHECKLIST_FILE) -> None:
        self.storage_file = storage_file
        self.storage_file.parent.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger("modules.release")

    def load_items(self) -> List[ReleaseChecklistItem]:
        if not self.storage_file.exists():
            return []
        try:
            data = json.loads(self.storage_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
        return [
            ReleaseChecklistItem.from_dict(item)
            for item in data.get("items", [])
            if isinstance(item, dict)
        ]

    def save_items(self, items: List[ReleaseChecklistItem]) -> None:
        payload = {
            "items": [item.to_dict() for item in items],
            "updated_at": datetime.now().isoformat(),
        }
        if not atomic_write_json(self.storage_file, payload, logger=self.logger):
            self.logger.error("Release-Checkliste konnte nicht gespeichert werden: %s", self.storage_file)

    def mark_done(self, title: str) -> bool:
        items = self.load_items()
        changed = False
        for item in items:
            if item.title == title and not item.done:
                item.done = True
                changed = True
        if changed:
            self.save_items(items)
        return changed

    def progress(self) -> Dict[str, int]:
        items = self.load_items()
        total = len(items)
        done = len([item for item in items if item.done])
        return {"done": done, "total": total}


__all__ = ["ReleaseChecklist", "ReleaseChecklistItem"]

