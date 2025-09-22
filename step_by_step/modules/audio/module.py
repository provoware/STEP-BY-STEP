"""Audio module for managing a persistent playlist and playback."""

from __future__ import annotations

import audioop
import json
import logging
import threading
import wave
from pathlib import Path
from typing import Callable, Dict, List, Optional

try:  # pragma: no cover - optional dependency handled dynamically
    import simpleaudio as sa
except Exception:  # pragma: no cover - gracefully handle missing backend
    sa = None  # type: ignore

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
        return sorted(
            data.get("tracks", []),
            key=lambda entry: entry.get("title", "").casefold(),
        )

    def add_track(self, title: str, file_path: Path) -> bool:
        tracks = self.load_tracks()
        titles = [track.get("title", "") for track in tracks] + [title]
        if not ensure_unique(titles):
            return False
        if not ensure_existing_path(file_path):
            return False
        tracks.append({"title": title, "path": str(file_path)})
        self._write_tracks(tracks)
        return True

    def remove_track(self, title: str) -> bool:
        tracks = self.load_tracks()
        filtered = [track for track in tracks if track.get("title") != title]
        if len(filtered) == len(tracks):
            return False
        self._write_tracks(filtered)
        return True

    def find_track(self, title: str) -> Optional[Dict[str, str]]:
        for track in self.load_tracks():
            if track.get("title") == title:
                return track
        return None

    def _write_tracks(self, tracks: List[Dict[str, str]]) -> None:
        payload = {"tracks": sorted(tracks, key=lambda entry: entry.get("title", "").casefold())}
        self.storage_file.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )


class AudioPlayer:
    """Simple audio playback controller with volume handling."""

    def __init__(
        self,
        *,
        logger: Optional[logging.Logger] = None,
        on_error: Optional[Callable[[str], None]] = None,
    ) -> None:
        self.logger = logger or logging.getLogger("audio.player")
        self._on_error = on_error
        self._lock = threading.Lock()
        self._play_obj: Optional["sa.PlayObject"] = None  # type: ignore[name-defined]
        self._current_path: Optional[Path] = None
        self._volume: float = 0.8

    @property
    def backend_available(self) -> bool:
        """Return ``True`` if the playback backend is ready to use."""

        return sa is not None

    @property
    def volume(self) -> float:
        """Return the current playback volume (0.0–1.0)."""

        return self._volume

    def set_volume(self, value: float) -> None:
        self._volume = max(0.0, min(1.0, value))
        self.logger.debug("Audio-Lautstärke gesetzt: %s", self._volume)

    def stop(self) -> None:
        with self._lock:
            if self._play_obj is not None:
                self._play_obj.stop()
                self.logger.info("Audiowiedergabe gestoppt (%s)", self._current_path)
            self._play_obj = None
            self._current_path = None

    def play(self, file_path: Path) -> bool:
        if sa is None:
            self._notify_error(
                "Das Audiomodul 'simpleaudio' konnte nicht geladen werden."
                " Bitte die Abhängigkeiten neu installieren."
            )
            return False
        if not ensure_existing_path(file_path):
            self._notify_error(f"Datei nicht gefunden: {file_path}")
            return False

        try:
            with wave.open(str(file_path), "rb") as wave_file:
                raw_frames = wave_file.readframes(wave_file.getnframes())
                sample_width = wave_file.getsampwidth()
                if self._volume != 1.0:
                    raw_frames = audioop.mul(raw_frames, sample_width, self._volume)
                play_obj = sa.play_buffer(  # type: ignore[arg-type]
                    raw_frames,
                    wave_file.getnchannels(),
                    sample_width,
                    wave_file.getframerate(),
                )
        except wave.Error as exc:
            self._notify_error(f"Datei konnte nicht als WAV geöffnet werden: {exc}")
            return False
        except Exception as exc:  # pragma: no cover - failsafe for audio playback
            self._notify_error(f"Unbekannter Audiofehler: {exc}")
            return False

        with self._lock:
            if self._play_obj is not None:
                self._play_obj.stop()
            self._play_obj = play_obj
            self._current_path = file_path
        self.logger.info("Audiowiedergabe gestartet: %s", file_path)
        return True

    def _notify_error(self, message: str) -> None:
        self.logger.error(message)
        if self._on_error is not None:
            self._on_error(message)


__all__ = ["PlaylistManager", "AudioPlayer"]
