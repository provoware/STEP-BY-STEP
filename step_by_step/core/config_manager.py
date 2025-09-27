"""Configuration management utilities for the STEP-BY-STEP tool.

This module centralises loading and saving persistent configuration
values that are shared across the application.  The configuration is
stored as JSON (JavaScript Object Notation, ein textbasiertes Format für
strukturierte Daten) to keep it both human and machine readable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict

import json

from .defaults import DEFAULT_SETTINGS
from .logging_manager import get_logger
from .validators import SettingsValidator


CONFIG_FILE = Path("data/settings.json")


@dataclass
class UserPreferences:
    """Typed access (strukturierter Zugriff) to user preference values."""

    font_scale: float = 1.2
    theme: str = "light"
    autosave_interval_minutes: int = 10
    accessibility_mode: bool = True
    shortcuts_enabled: bool = True
    contrast_theme: str = "accessible"
    color_mode: str = "accessible"
    audio_volume: float = 0.8
    extra: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, raw: Dict[str, Any]) -> "UserPreferences":
        """Create a :class:`UserPreferences` from a dictionary."""

        known_fields = {field.name for field in cls.__dataclass_fields__.values()}  # type: ignore[attr-defined]
        data = {key: value for key, value in raw.items() if key in known_fields}
        extras = {key: value for key, value in raw.items() if key not in known_fields}
        preferences = cls(**data)
        preferences.extra = extras
        return preferences

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON serialisable (als JSON speicherbar) dictionary."""

        data = {field: getattr(self, field) for field in self.__dataclass_fields__}
        data.update(self.extra)
        return data


class ConfigManager:
    """Handle persistence (dauerhaftes Speichern) of configuration values."""

    def __init__(self, file_path: Path = CONFIG_FILE) -> None:
        self.file_path = file_path
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.logger = get_logger("core.config")
        self.validator = SettingsValidator()

    def load_preferences(self) -> UserPreferences:
        """Return stored user preferences or sensible defaults."""

        if not self.file_path.exists():
            self.logger.warning(
                "Einstellungsdatei fehlte – Standardwerte werden erzeugt."
            )
            defaults = dict(DEFAULT_SETTINGS)
            self._write_payload(defaults)
            return UserPreferences.from_dict(defaults)
        try:
            with self.file_path.open("r", encoding="utf-8") as handle:
                content = json.load(handle)
        except json.JSONDecodeError:
            self.logger.error(
                "Einstellungsdatei beschädigt – Standardwerte wiederhergestellt."
            )
            defaults = dict(DEFAULT_SETTINGS)
            self._write_payload(defaults)
            return UserPreferences.from_dict(defaults)
        except OSError as error:
            self.logger.error("Einstellungen konnten nicht gelesen werden: %s", error)
            return UserPreferences()

        sanitised, adjustments = self.validator.normalise(content)
        if sanitised != content:
            self._write_payload(sanitised)
            if adjustments:
                self.logger.info(
                    "Einstellungen korrigiert: %s", "; ".join(adjustments)
                )
            else:
                self.logger.info("Einstellungen auf Standardwerte aktualisiert.")
        return UserPreferences.from_dict(sanitised)

    def save_preferences(self, preferences: UserPreferences) -> None:
        """Persist the given preferences in JSON format."""

        self._write_payload(preferences.to_dict())

    def _write_payload(self, payload: Dict[str, Any]) -> None:
        with self.file_path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)


__all__ = ["ConfigManager", "UserPreferences"]
