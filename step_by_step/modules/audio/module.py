"""Audio module for managing a persistent playlist."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from ...core.validators import ensure_existing_path, ensure_unique

PLAYLIST_FILE = Path("data/playlists.json")


class PlaylistManager:
    """Manage playlist entries with validation."""

    def __init__(self, storage_file: Path = PLAYLIST_FILE) -> None:
        self.storage_file = storage_file
        self.storage_file.parent.mkdir(parents=True, exist_ok=True)

    def load_tracks(self) -> List[Dict[str, str]]:
        if not self.storage_file.exists():
            return []
        try:
            data = json.loads(self.storage_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return []
        return data.get("tracks", [])

    def add_track(self, title: str, file_path: Path) -> bool:
        tracks = self.load_tracks()
        titles = [track.get("title", "") for track in tracks] + [title]
        if not ensure_unique(titles):
            return False
        if not ensure_existing_path(file_path):
            return False
        tracks.append({"title": title, "path": str(file_path)})
        self.storage_file.write_text(
            json.dumps({"tracks": tracks}, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return True


__all__ = ["PlaylistManager"]
