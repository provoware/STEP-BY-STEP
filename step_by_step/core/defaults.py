"""Shared default values for STEP-BY-STEP configuration files."""

from __future__ import annotations

from typing import Dict, Any


# Central place for persistent default preferences so that startup checks,
# configuration loading, and validators rely on the same payload.
DEFAULT_SETTINGS: Dict[str, Any] = {
    "font_scale": 1.2,
    "theme": "light",
    "autosave_interval_minutes": 10,
    "accessibility_mode": True,
    "shortcuts_enabled": True,
    "contrast_theme": "accessible",
    "color_mode": "accessible",
    "audio_volume": 0.8,
}


__all__ = ["DEFAULT_SETTINGS"]
