"""Configuration helpers for persistent user preferences.

The STEP-BY-STEP launcher stores user specific values (z.B. Schriftgröße
und Thema) inside ``data/settings.json``.  This module takes care of reading
and writing that file while ensuring that invalid payloads are replaced with
safe defaults.  The concrete validation logic lives in
``step_by_step.core.validators.SettingsValidator`` which performs automatic
corrections and keeps a log of adjustments for the start report.
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
    """Typed access to the stored configuration values."""

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
        """Create an instance from an untyped dictionary."""

        known_fields = set(cls.__dataclass_fields__.keys())  # type: ignore[attr-defined]
        data = {key: value for key, value in raw.items() if key in known_fields}
        extras = {key: value for key, value in raw.items() if key not in known_fields}
        instance = cls(**data)
        instance.extra = extras
        return instance

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON serialisable representation including extras."""

        payload = {field: getattr(self, field) for field in self.__dataclass_fields__}
        payload.update(self.extra)
        return payload


class ConfigManager:
    """Load and persist configuration values with validation."""

    def __init__(self, file_path: Path = CONFIG_FILE) -> None:
        self.file_path = file_path
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.logger = get_logger("core.config")
        self.validator = SettingsValidator()

    # ------------------------------------------------------------------
    def load_preferences(self) -> UserPreferences:
        """Return stored preferences, sanitising invalid payloads."""

        if not self.file_path.exists():
            self.logger.warning("Einstellungsdatei fehlte – Standardwerte werden angelegt.")
            defaults = dict(DEFAULT_SETTINGS)
            self._write_payload(defaults)
            return UserPreferences.from_dict(defaults)

        try:
            with self.file_path.open("r", encoding="utf-8") as handle:
                raw_content: Dict[str, Any] = json.load(handle)
        except json.JSONDecodeError:
            self.logger.error(
                "Einstellungsdatei beschädigt – Standardwerte werden wiederhergestellt."
            )
            defaults = dict(DEFAULT_SETTINGS)
            self._write_payload(defaults)
            return UserPreferences.from_dict(defaults)
        except OSError as error:
            self.logger.error("Einstellungen konnten nicht gelesen werden: %s", error)
            return UserPreferences()

        sanitised, adjustments = self.validator.normalise(raw_content)
        if sanitised != raw_content:
            self._write_payload(sanitised)
            if adjustments:
                self.logger.info("Einstellungen korrigiert: %s", "; ".join(adjustments))
            else:
                self.logger.info("Einstellungen auf empfohlene Standardwerte gebracht.")

        return UserPreferences.from_dict(sanitised)

    # ------------------------------------------------------------------
    def save_preferences(self, preferences: UserPreferences) -> None:
        """Persist the provided preferences as JSON."""

        self._write_payload(preferences.to_dict())

    # ------------------------------------------------------------------
    def _write_payload(self, payload: Dict[str, Any]) -> None:
        try:
            with self.file_path.open("w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2, ensure_ascii=False)
        except OSError as error:
            self.logger.error("Einstellungen konnten nicht gespeichert werden: %s", error)


__all__ = ["ConfigManager", "UserPreferences"]

