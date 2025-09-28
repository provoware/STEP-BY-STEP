"""Static resource declarations used during startup."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Callable, Dict, Iterable, Tuple

from .defaults import DEFAULT_SETTINGS

# Pfade (paths) für dauerhaft benötigte Ordner.
REQUIRED_FOLDERS: Tuple[Path, ...] = (
    Path("data"),
    Path("logs"),
    Path("data/exports"),
    Path("data/converted_audio"),
    Path("data/backups"),
)

# Gemeinsamer Pfad zur SQLite-Archivdatenbank.
ARCHIVE_DB_PATH = Path("data/archive.db")


def _dump(payload: object) -> str:
    """Hilfsfunktion zum schönen JSON-Format (indentiert)."""

    return json.dumps(payload, indent=2, ensure_ascii=False)


def _settings_template() -> str:
    return _dump(DEFAULT_SETTINGS)


def _empty_items_template() -> str:
    return _dump({"items": []})


def _empty_tracks_template() -> str:
    return _dump({"tracks": []})


def _empty_entries_template() -> str:
    return _dump({"entries": []})


def _notes_template() -> str:
    return ""


def _usage_stats_template() -> str:
    return _dump({})


def _selftest_template() -> str:
    return _dump(
        {
            "last_run": "",
            "all_passed": False,
            "self_tests": [],
            "created_virtualenv": False,
            "installed_dependencies": False,
            "messages": [],
            "repaired_paths": [],
            "dependency_messages": [],
            "security_summary": {
                "status": "unknown",
                "verified": 0,
                "issues": [],
                "backups": [],
                "size_alerts": [],
                "pruned_backups": [],
                "restore_points": [],
                "restore_issues": [],
                "updated_manifest": False,
                "timestamp": "",
            },
            "color_audit": {
                "generated_at": "",
                "overall_status": "unknown",
                "worst_ratio": 0.0,
                "themes": [],
                "issues": [],
                "recommendations": [],
            },
            "diagnostics": {
                "generated_at": "",
                "python": {},
                "virtualenv": {},
                "paths": [],
                "packages": [],
                "summary": {"status": "unknown", "issues": [], "recommendations": []},
                "startup": {},
            },
            "diagnostics_messages": [],
            "diagnostics_report_path": "",
            "diagnostics_report_html_path": "",
        }
    )


def _release_checklist_template() -> str:
    return _dump(
        {
            "items": [
                {
                    "title": "Automatischer Start inklusive Selbsttests",
                    "done": True,
                    "details": "Launcher führt Abhängigkeitsprüfung und Reparaturen durch.",
                },
                {
                    "title": "Audioformat-Prüfung und Normalisierung",
                    "done": True,
                    "details": "Playlist-Bereich bietet Prüfen und Konvertieren auf WAV-Basis.",
                },
                {
                    "title": "Archiv-Export als CSV und JSON",
                    "done": True,
                    "details": "Schnelllinks exportieren Datenbankeinträge in data/exports/.",
                },
                {
                    "title": "Startprotokoll durchsuchbar in der Oberfläche",
                    "done": True,
                    "details": "Eigenes Panel filtert logs/startup.log nach Begriffen.",
                },
                {
                    "title": "Abschließender Release-Review",
                    "done": True,
                    "details": "End-to-End-Prüfung dokumentiert, Release freigegeben.",
                },
            ],
            "updated_at": "",
        }
    )


def _color_audit_template() -> str:
    return _dump(
        {
            "generated_at": "",
            "overall_status": "unknown",
            "worst_ratio": 0.0,
            "themes": [],
            "issues": [],
            "recommendations": [],
        }
    )


def _diagnostics_template() -> str:
    return _dump(
        {
            "generated_at": "",
            "python": {},
            "virtualenv": {},
            "paths": [],
            "packages": [],
            "summary": {"status": "unknown", "issues": [], "recommendations": []},
            "startup": {},
        }
    )


def _security_manifest_template() -> str:
    return _dump({"files": {}, "created_at": "", "updated_at": ""})


FILE_TEMPLATES: Dict[Path, Callable[[], str]] = {
    Path("data/settings.json"): _settings_template,
    Path("data/todo_items.json"): _empty_items_template,
    Path("data/playlists.json"): _empty_tracks_template,
    Path("data/archive.json"): _empty_entries_template,
    Path("data/persistent_notes.txt"): _notes_template,
    Path("data/usage_stats.json"): _usage_stats_template,
    Path("data/selftest_report.json"): _selftest_template,
    Path("data/release_checklist.json"): _release_checklist_template,
    Path("data/color_audit.json"): _color_audit_template,
    Path("data/diagnostics_report.json"): _diagnostics_template,
    Path("data/security_manifest.json"): _security_manifest_template,
}


def iter_required_files() -> Iterable[Tuple[Path, str]]:
    """Erzeuge Tupel (Paare) aus Pfad und Inhalt für Pflichtdateien."""

    for path, factory in FILE_TEMPLATES.items():
        yield path, factory()


def required_file_content(path: Path) -> str:
    """Gib den Standardinhalt für einen Pfad zurück."""

    factory = FILE_TEMPLATES.get(path)
    if factory is None:
        raise KeyError(f"Keine Vorlage für {path} hinterlegt")
    return factory()


__all__ = [
    "ARCHIVE_DB_PATH",
    "REQUIRED_FOLDERS",
    "FILE_TEMPLATES",
    "iter_required_files",
    "required_file_content",
]

