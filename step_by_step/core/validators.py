"""Validation helpers that keep persisted data consistent."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from .defaults import DEFAULT_SETTINGS
from .themes import THEME_ORDER


def ensure_unique(values: Iterable[str]) -> bool:
    """Return ``True`` when all values are unique (einzigartig)."""

    lowered = [value.casefold() for value in values]
    return len(lowered) == len(set(lowered))


def ensure_existing_path(path: Path) -> bool:
    """Return ``True`` if the provided path exists on disk."""

    return path.exists()


@dataclass
class SettingsValidator:
    """Normalise values from ``settings.json`` and report adjustments."""

    min_scale: float = 0.8
    max_scale: float = 1.8

    def __post_init__(self) -> None:
        self.defaults = dict(DEFAULT_SETTINGS)
        self.allowed_themes = {name: name for name in THEME_ORDER}

    # ------------------------------------------------------------------
    def normalise(self, raw: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
        data = dict(raw)
        messages: List[str] = []

        for key, default in self.defaults.items():
            if key not in data:
                data[key] = default
                messages.append(f"'{key}' ergänzt (Standardwert übernommen).")

        data["font_scale"], notes = self._normalise_font_scale(data.get("font_scale"))
        messages.extend(notes)

        autosave, notes = self._normalise_autosave(data.get("autosave_interval_minutes"))
        data["autosave_interval_minutes"] = autosave
        messages.extend(notes)

        volume, notes = self._normalise_volume(data.get("audio_volume"))
        data["audio_volume"] = volume
        messages.extend(notes)

        for field in ("accessibility_mode", "shortcuts_enabled"):
            value, note = self._normalise_bool(field, data.get(field))
            data[field] = value
            if note:
                messages.append(note)

        for field in ("theme", "contrast_theme", "color_mode"):
            value, note = self._normalise_theme(field, data.get(field))
            data[field] = value
            if note:
                messages.append(note)

        return data, messages

    # ------------------------------------------------------------------
    def _normalise_font_scale(self, raw_value: Any) -> Tuple[float, List[str]]:
        messages: List[str] = []
        fallback = float(self.defaults.get("font_scale", 1.2))
        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            value = fallback
            messages.append("Schriftgröße war ungültig und wurde auf 120 % gesetzt.")

        clamped = max(self.min_scale, min(self.max_scale, value))
        if abs(clamped - value) > 1e-9:
            messages.append(
                (
                    "Schriftgröße automatisch in den empfohlenen Bereich "
                    f"({int(self.min_scale * 100)}–{int(self.max_scale * 100)} %) gebracht."
                )
            )

        return round(clamped, 2), messages

    # ------------------------------------------------------------------
    def _normalise_autosave(self, raw_value: Any) -> Tuple[int, List[str]]:
        messages: List[str] = []
        fallback = int(self.defaults.get("autosave_interval_minutes", 10))
        try:
            value = int(raw_value)
        except (TypeError, ValueError):
            value = fallback
            messages.append("Autospeicherintervall war ungültig und wurde auf 10 Minuten gesetzt.")

        clamped = max(1, min(120, value))
        if clamped != value:
            messages.append("Autospeicherintervall auf 1–120 Minuten begrenzt.")
        return clamped, messages

    # ------------------------------------------------------------------
    def _normalise_volume(self, raw_value: Any) -> Tuple[float, List[str]]:
        messages: List[str] = []
        fallback = float(self.defaults.get("audio_volume", 0.8))
        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            value = fallback
            messages.append("Audio-Lautstärke war ungültig und wurde auf 80 % gesetzt.")

        clamped = max(0.0, min(1.0, value))
        if abs(clamped - value) > 1e-9:
            messages.append("Audio-Lautstärke auf den Bereich 0–100 % eingegrenzt.")
        return round(clamped, 2), messages

    # ------------------------------------------------------------------
    def _normalise_bool(self, field: str, raw_value: Any) -> Tuple[bool, str]:
        default = bool(self.defaults.get(field, False))
        if isinstance(raw_value, bool):
            value = raw_value
        elif isinstance(raw_value, str):
            value = raw_value.strip().lower() in {"1", "true", "ja", "yes", "on", "an"}
        elif isinstance(raw_value, (int, float)):
            value = bool(raw_value)
        else:
            value = default

        if value != raw_value:
            label = "Barrierefreiheit" if field == "accessibility_mode" else "Tastenkürzel"
            return value, f"{label} wurde auf {'aktiv' if value else 'inaktiv'} gesetzt."
        return value, ""

    # ------------------------------------------------------------------
    def _normalise_theme(self, field: str, raw_value: Any) -> Tuple[str, str]:
        default = str(self.defaults.get(field, "light"))
        if isinstance(raw_value, str):
            candidate = raw_value.strip().lower()
        else:
            candidate = ""

        if candidate in self.allowed_themes:
            value = self.allowed_themes[candidate]
        else:
            value = default

        if value != raw_value:
            label_map = {
                "theme": "Standard-Design",
                "contrast_theme": "Kontrast-Design",
                "color_mode": "Farbschema",
            }
            label = label_map.get(field, field)
            return value, f"{label} wurde auf '{value}' gesetzt."
        return value, ""


__all__ = ["ensure_unique", "ensure_existing_path", "SettingsValidator"]

