"""ToDo module with date handling and completion tracking."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Dict, List

TODO_FILE = Path("data/todo_items.json")


@dataclass
class TodoItem:
    title: str
    due_date: date
    done: bool = False

    @classmethod
    def from_dict(cls, raw: Dict[str, str]) -> "TodoItem":
        return cls(
            title=raw.get("title", ""),
            due_date=date.fromisoformat(raw.get("due_date", date.today().isoformat())),
            done=raw.get("done", False),
        )

    def to_dict(self) -> Dict[str, str]:
        return {
            "title": self.title,
            "due_date": self.due_date.isoformat(),
            "done": self.done,
        }


class TodoModule:
    """Maintain a list of todos and provide dashboard summaries."""

    def __init__(self, storage_file: Path = TODO_FILE) -> None:
        self.storage_file = storage_file
        self.storage_file.parent.mkdir(parents=True, exist_ok=True)

    def load_items(self) -> List[TodoItem]:
        if not self.storage_file.exists():
            return []
        try:
            data = json.loads(self.storage_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
        return [TodoItem.from_dict(item) for item in data.get("items", [])]

    def add_item(self, item: TodoItem) -> None:
        items = self.load_items()
        items.append(item)
        payload = {"items": [entry.to_dict() for entry in items]}
        self.storage_file.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def mark_done(self, title: str) -> bool:
        items = self.load_items()
        updated = False
        for item in items:
            if item.title == title:
                item.done = True
                updated = True
        if updated:
            self.storage_file.write_text(
                json.dumps({"items": [entry.to_dict() for entry in items]}, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        return updated

    def next_due_items(self, limit: int = 3) -> List[TodoItem]:
        items = sorted(self.load_items(), key=lambda item: item.due_date)
        return [item for item in items if not item.done][:limit]


__all__ = ["TodoItem", "TodoModule"]
