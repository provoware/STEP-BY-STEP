"""Shared color theme definitions for STEP-BY-STEP."""

from __future__ import annotations

from typing import Dict

# Order in which the themes should be presented to the user.
THEME_ORDER = ("accessible", "high_contrast", "light", "dark")

# Central palette definitions used by GUI and audits alike.
COLOR_THEMES: Dict[str, Dict[str, str]] = {
    "accessible": {
        "background": "#0F1C2E",
        "on_background": "#F5F5F5",
        "surface": "#1B2B3C",
        "on_surface": "#F5F5F5",
        "accent": "#FF9500",
        "accent_hover": "#DB7C00",
        "success": "#1F9D6F",
        "warning": "#C07A00",
        "danger": "#FF6B6B",
    },
    "high_contrast": {
        "background": "#101820",
        "on_background": "#F2F2F2",
        "surface": "#1F2833",
        "on_surface": "#F2F2F2",
        "accent": "#FEE715",
        "accent_hover": "#FFC600",
        "success": "#008B5E",
        "warning": "#B17900",
        "danger": "#FF5C5C",
    },
    "dark": {
        "background": "#1E1E2E",
        "on_background": "#E0DEF4",
        "surface": "#2E2E3E",
        "on_surface": "#E0DEF4",
        "accent": "#89B4FA",
        "accent_hover": "#74A0F1",
        "success": "#0F8055",
        "warning": "#8B6000",
        "danger": "#F38BA8",
    },
    "light": {
        "background": "#f2f2f2",
        "on_background": "#0d0d0d",
        "surface": "#ffffff",
        "on_surface": "#0d0d0d",
        "accent": "#0d6efd",
        "accent_hover": "#0b5ed7",
        "success": "#4CC38A",
        "warning": "#FFB74D",
        "danger": "#dc3545",
    },
}


def get_theme_colors(mode: str) -> Dict[str, str]:
    """Return a copy of the palette for the requested mode."""

    palette = COLOR_THEMES.get(mode, COLOR_THEMES["light"])
    return dict(palette)


__all__ = ["COLOR_THEMES", "THEME_ORDER", "get_theme_colors"]
