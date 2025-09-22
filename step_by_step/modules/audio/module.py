"""Audio module for managing a persistent playlist and playback."""

from __future__ import annotations

from dataclasses import dataclass
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
CONVERTED_AUDIO_DIR = Path("data/converted_audio")
STANDARD_SAMPLE_WIDTH = 2  # 16 Bit PCM


@dataclass
class AudioFormatInfo:
    """Container for audio metadata."""

    channels: int
    sample_width: int
    frame_rate: int
    frame_count: int

    @property
    def duration_seconds(self) -> float:
        if not self.frame_rate:
            return 0.0
        return self.frame_count / float(self.frame_rate)


class AudioFormatInspector:
    """Analyse and normalise audio files for playback."""

    def __init__(self, *, logger: Optional[logging.Logger] = None) -> None:
        self.logger = logger or logging.getLogger("audio.format")
        CONVERTED_AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    def inspect(self, file_path: Path) -> Optional[AudioFormatInfo]:
        if not ensure_existing_path(file_path):
            self.logger.warning("Datei für Analyse nicht gefunden: %s", file_path)
            return None
        try:
            with wave.open(str(file_path), "rb") as handle:
                params = handle.getparams()
                return AudioFormatInfo(
                    channels=params.nchannels,
                    sample_width=params.sampwidth,
                    frame_rate=params.framerate,
                    frame_count=params.nframes,
                )
        except wave.Error as error:
            self.logger.error("Audioformat konnte nicht gelesen werden: %s", error)
            return None

    def needs_normalisation(self, info: AudioFormatInfo) -> bool:
        return info.sample_width != STANDARD_SAMPLE_WIDTH or info.channels not in (1, 2)

    def normalise(self, file_path: Path) -> Optional[Path]:
        info = self.inspect(file_path)
        if info is None:
            return None
        if not self.needs_normalisation(info):
            self.logger.debug("Keine Konvertierung nötig für %s", file_path)
            return file_path

        target_path = CONVERTED_AUDIO_DIR / f"{file_path.stem}_normalized.wav"
        try:
            with wave.open(str(file_path), "rb") as source:
                frames = source.readframes(info.frame_count)
                sample_width = info.sample_width
                channels = info.channels

            if sample_width != STANDARD_SAMPLE_WIDTH:
                frames = audioop.lin2lin(frames, sample_width, STANDARD_SAMPLE_WIDTH)
                sample_width = STANDARD_SAMPLE_WIDTH

            target_channels = 2 if channels >= 2 else 1
            if channels > target_channels:
                frames = audioop.tomono(frames, sample_width, 0.5, 0.5)
                channels = 1
            if target_channels == 2 and channels == 1:
                frames = audioop.tostereo(frames, sample_width, 1, 1)
                channels = 2

            with wave.open(str(target_path), "wb") as target:
                target.setnchannels(channels)
                target.setsampwidth(sample_width)
                target.setframerate(info.frame_rate)
                target.writeframes(frames)
        except wave.Error as error:
            self.logger.error("Konvertierung fehlgeschlagen: %s", error)
            return None
        except Exception as error:  # pragma: no cover - defensive guard
            self.logger.error("Unerwarteter Konvertierungsfehler: %s", error)
            return None

        self.logger.info("Audio normalisiert: %s -> %s", file_path, target_path)
        return target_path


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


__all__ = ["PlaylistManager", "AudioPlayer", "AudioFormatInspector", "AudioFormatInfo"]
