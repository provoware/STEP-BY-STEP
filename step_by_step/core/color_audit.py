"""Accessibility audit for color palettes."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Sequence

from .logging_manager import get_logger
from .themes import THEME_ORDER, get_theme_colors

# Which combinations should be tested for minimum contrast.
AUDIT_COMBINATIONS: Sequence[Dict[str, object]] = (
    {
        "label": "Basis-Text",
        "foreground": "on_background",
        "background": "background",
        "minimum": 4.5,
    },
    {
        "label": "Karten/Textfelder",
        "foreground": "on_surface",
        "background": "surface",
        "minimum": 4.5,
    },
    {
        "label": "Aktionsbutton",
        "foreground": "surface",
        "background": "accent",
        "minimum": 4.5,
    },
    {
        "label": "Warnhinweis",
        "foreground": "on_background",
        "background": "warning",
        "minimum": 3.0,
    },
    {
        "label": "Erfolgsnachricht",
        "foreground": "on_background",
        "background": "success",
        "minimum": 3.0,
    },
)


def _hex_to_rgb(color: str) -> Iterable[float]:
    color = color.strip().lstrip("#")
    if len(color) != 6:
        raise ValueError(f"Ungültige Farbe: {color}")
    return tuple(int(color[i : i + 2], 16) / 255.0 for i in range(0, 6, 2))


def _relative_luminance(rgb: Sequence[float]) -> float:
    def adjust(channel: float) -> float:
        return channel / 12.92 if channel <= 0.03928 else ((channel + 0.055) / 1.055) ** 2.4

    r, g, b = (adjust(channel) for channel in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _contrast_ratio(foreground: str, background: str) -> float:
    fg_lum = _relative_luminance(_hex_to_rgb(foreground))
    bg_lum = _relative_luminance(_hex_to_rgb(background))
    lighter = max(fg_lum, bg_lum)
    darker = min(fg_lum, bg_lum)
    return (lighter + 0.05) / (darker + 0.05)


@dataclass
class ThemeAudit:
    """Single theme evaluation result."""

    name: str
    entries: List[Dict[str, object]] = field(default_factory=list)
    worst_ratio: float = 21.0
    status: str = "ok"

    def to_dict(self) -> Dict[str, object]:
        return {
            "name": self.name,
            "entries": list(self.entries),
            "worst_ratio": self.worst_ratio,
            "status": self.status,
        }


@dataclass
class ColorAuditReport:
    """Collect results for all palettes."""

    generated_at: str
    themes: List[ThemeAudit] = field(default_factory=list)
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)

    @property
    def overall_status(self) -> str:
        return "ok" if not self.issues else "attention"

    @property
    def worst_ratio(self) -> float:
        if not self.themes:
            return 0.0
        return min(theme.worst_ratio for theme in self.themes)

    def to_dict(self) -> Dict[str, object]:
        return {
            "generated_at": self.generated_at,
            "overall_status": self.overall_status,
            "worst_ratio": self.worst_ratio,
            "issues": list(self.issues),
            "recommendations": list(self.recommendations),
            "themes": [theme.to_dict() for theme in self.themes],
        }


class ColorAuditor:
    """Audit all palettes and return a structured report."""

    def __init__(self) -> None:
        self.logger = get_logger("core.color_audit")

    def generate_report(self) -> ColorAuditReport:
        timestamp = dt.datetime.now().isoformat()
        report = ColorAuditReport(generated_at=timestamp)

        for name in THEME_ORDER:
            palette = get_theme_colors(name)
            entries: List[Dict[str, object]] = []
            worst_ratio = 21.0
            status = "ok"
            for rule in AUDIT_COMBINATIONS:
                fg_key = str(rule["foreground"])
                bg_key = str(rule["background"])
                minimum = float(rule["minimum"])
                fg = palette.get(fg_key, "#000000")
                bg = palette.get(bg_key, "#FFFFFF")
                ratio = _contrast_ratio(fg, bg)
                worst_ratio = min(worst_ratio, ratio)
                passes = ratio >= minimum
                suggestion = None
                if not passes:
                    status = "attention"
                    issue = (
                        f"Thema '{name}': {rule['label']} erreicht nur {ratio:.2f}:1 (benötigt {minimum}:1)"
                    )
                    suggestion = _suggest_adjustment(
                        theme=name,
                        element=str(rule["label"]),
                        foreground=fg,
                        background=bg,
                        minimum=minimum,
                        ratio=ratio,
                    )
                    report.issues.append(issue)
                    if suggestion and suggestion not in report.recommendations:
                        report.recommendations.append(suggestion)
                entries.append(
                    {
                        "element": rule["label"],
                        "foreground": fg,
                        "background": bg,
                        "ratio": round(ratio, 2),
                        "minimum": minimum,
                        "passes": passes,
                        "suggestion": suggestion,
                    }
                )
            report.themes.append(ThemeAudit(name=name, entries=entries, worst_ratio=worst_ratio, status=status))

        if report.issues:
            self.logger.warning("Farbaudit mit %s Hinweisen abgeschlossen", len(report.issues))
        else:
            self.logger.info("Farbaudit ohne Auffälligkeiten abgeschlossen")

        return report


def _suggest_adjustment(
    theme: str,
    element: str,
    foreground: str,
    background: str,
    minimum: float,
    ratio: float,
) -> str:
    """Return a human-readable hint on how to raise the contrast."""

    delta = max(0.0, minimum - ratio)
    fg_lum = _relative_luminance(_hex_to_rgb(foreground))
    bg_lum = _relative_luminance(_hex_to_rgb(background))
    if fg_lum > bg_lum:
        action = "Hintergrund dunkler wählen oder Textfarbe leicht aufhellen"
    else:
        action = "Textfarbe dunkler setzen oder Hintergrund aufhellen"
    return (
        f"{theme}: {element} erreicht {ratio:.2f}:1 – {action} (benötigt {minimum}:1, Differenz {delta:.2f})."
    )


__all__ = ["ColorAuditor", "ColorAuditReport", "ThemeAudit"]
