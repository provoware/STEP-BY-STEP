"""Diagnostics helpers for the STEP-BY-STEP startup checks."""

from __future__ import annotations

import datetime as dt
import json
import os
import platform
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, TYPE_CHECKING

from .logging_manager import get_logger

try:  # Python 3.8 compatibility guard
    from importlib import metadata as importlib_metadata
except ImportError:  # pragma: no cover - fallback for very old runtimes
    import importlib_metadata  # type: ignore

if TYPE_CHECKING:  # pragma: no cover - for type checking only
    from .startup import StartupReport


@dataclass
class PackageStatus:
    """Status information for a required package."""

    name: str
    purpose: str
    installed: bool
    version: str = ""
    message: str = ""

    def to_dict(self) -> Dict[str, object]:
        return {
            "name": self.name,
            "purpose": self.purpose,
            "installed": self.installed,
            "version": self.version,
            "message": self.message,
        }


@dataclass
class PathStatus:
    """Represent a path check (Ordner oder Datei)."""

    path: Path
    exists: bool
    writable: bool
    kind: str = "folder"

    def to_dict(self) -> Dict[str, object]:
        return {
            "path": str(self.path),
            "exists": self.exists,
            "writable": self.writable,
            "kind": self.kind,
        }


@dataclass
class DiagnosticsReport:
    """Container for the collected diagnostics values."""

    generated_at: str
    python: Dict[str, object]
    virtualenv: Dict[str, object]
    paths: List[Dict[str, object]]
    packages: List[Dict[str, object]]
    summary: Dict[str, object]
    startup: Dict[str, object]

    def to_dict(self) -> Dict[str, object]:
        return {
            "generated_at": self.generated_at,
            "python": self.python,
            "virtualenv": self.virtualenv,
            "paths": self.paths,
            "packages": self.packages,
            "summary": self.summary,
            "startup": self.startup,
        }


class DiagnosticsManager:
    """Collect and persist diagnostic information for professional support."""

    TARGET_FILE = Path("data/diagnostics_report.json")

    def __init__(self) -> None:
        self.logger = get_logger("core.diagnostics")

    # ------------------------------------------------------------------
    def collect(self, report: Optional["StartupReport"] = None) -> DiagnosticsReport:
        """Gather environment, dependency, and path status information."""

        generated_at = dt.datetime.now().isoformat()
        python_info = {
            "version": sys.version.split()[0],
            "executable": sys.executable,
            "implementation": platform.python_implementation(),
            "platform": platform.platform(),
            "cwd": str(Path.cwd()),
            "fs_encoding": sys.getfilesystemencoding(),
        }

        virtualenv_info = self._collect_virtualenv_info()
        path_checks = list(self._collect_paths())
        package_checks = list(self._collect_packages())

        summary = self._build_summary(virtualenv_info, path_checks, package_checks)
        startup_snapshot = self._build_startup_snapshot(report)

        diagnostics = DiagnosticsReport(
            generated_at=generated_at,
            python=python_info,
            virtualenv=virtualenv_info,
            paths=[status.to_dict() for status in path_checks],
            packages=[status.to_dict() for status in package_checks],
            summary=summary,
            startup=startup_snapshot,
        )
        return diagnostics

    # ------------------------------------------------------------------
    def save(self, diagnostics: DiagnosticsReport) -> Path:
        """Persist the diagnostics report to the default JSON file."""

        target = self.TARGET_FILE
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = diagnostics.to_dict()
        target.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        self.logger.info("Diagnosebericht gespeichert: %s", target)
        return target

    # ------------------------------------------------------------------
    def summary_lines(self, diagnostics: DiagnosticsReport) -> List[str]:
        """Create short, user-friendly summary sentences."""

        summary = diagnostics.summary
        generated = diagnostics.generated_at
        issues = summary.get("issues", [])
        packages = diagnostics.packages
        virtualenv = diagnostics.virtualenv

        lines = []
        if issues:
            lines.append(
                (
                    f"Systemdiagnose ({generated}): {len(issues)} Hinweis(e) gefunden. "
                    "Details stehen im Diagnosebericht (Systembericht)."
                )
            )
        else:
            lines.append(
                (
                    f"Systemdiagnose ({generated}): keine Auffälligkeiten. "
                    "Bericht liegt unter data/diagnostics_report.json."
                )
            )

        if virtualenv.get("active"):
            lines.append("Virtuelle Umgebung (eigene Programm-Umgebung) ist aktiv.")
        else:
            lines.append(
                "Hinweis: Tool läuft ohne virtuelle Umgebung (eigene Programm-Umgebung)."
            )

        missing_packages = [pkg["name"] for pkg in packages if not pkg.get("installed")]
        if missing_packages:
            names = ", ".join(sorted(missing_packages))
            lines.append(f"Fehlende Pakete: {names}.")
        return lines

    # ------------------------------------------------------------------
    def _collect_virtualenv_info(self) -> Dict[str, object]:
        expected_path = Path(".venv").resolve()
        env_path_raw = os.environ.get("VIRTUAL_ENV")
        env_path = Path(env_path_raw).resolve() if env_path_raw else None
        try:
            current_prefix = Path(sys.prefix).resolve()
        except Exception:  # pragma: no cover - defensive fallback
            current_prefix = Path(sys.prefix)

        active = expected_path.exists() and (
            current_prefix == expected_path or (env_path and env_path == expected_path)
        )
        return {
            "active": active,
            "expected_path": str(expected_path),
            "current_prefix": str(current_prefix),
            "environment_path": str(env_path) if env_path else "",
        }

    # ------------------------------------------------------------------
    def _collect_paths(self) -> Iterable[PathStatus]:
        for raw_path, kind in (
            (Path("data"), "folder"),
            (Path("logs"), "folder"),
            (Path("data/backups"), "folder"),
            (Path("data/exports"), "folder"),
            (Path("data/converted_audio"), "folder"),
            (Path("logs/startup.log"), "file"),
        ):
            exists = raw_path.exists()
            writable = os.access(raw_path if exists else raw_path.parent, os.W_OK)
            yield PathStatus(path=raw_path, exists=exists, writable=writable, kind=kind)

    # ------------------------------------------------------------------
    def _collect_packages(self) -> Iterable[PackageStatus]:
        requirements: Sequence[tuple[str, str]] = (
            ("ttkbootstrap", "Theming (Oberflächen-Gestaltung)"),
            ("simpleaudio", "Audiowiedergabe"),
        )
        for package, purpose in requirements:
            try:
                version = importlib_metadata.version(package)
                yield PackageStatus(
                    name=package,
                    purpose=purpose,
                    installed=True,
                    version=version,
                    message="Paket verfügbar.",
                )
            except importlib_metadata.PackageNotFoundError:
                yield PackageStatus(
                    name=package,
                    purpose=purpose,
                    installed=False,
                    message=(
                        "Nicht installiert. Installation mit 'python -m pip install "
                        f"{package}' empfohlen."
                    ),
                )

    # ------------------------------------------------------------------
    def _build_summary(
        self,
        virtualenv: Dict[str, object],
        paths: Sequence[PathStatus],
        packages: Sequence[PackageStatus],
    ) -> Dict[str, object]:
        issues: List[str] = []
        recommendations: List[str] = []

        if not virtualenv.get("active"):
            recommendations.append(
                "Virtuelle Umgebung (eigene Programm-Umgebung) aktivieren oder Startskript erneut ausführen."
            )

        for status in paths:
            if not status.exists:
                issues.append(f"Pfad {status.path} fehlt.")
                recommendations.append(
                    f"Ordner/Datei {status.path} neu anlegen lassen (Startskript erneut ausführen)."
                )
            elif not status.writable:
                issues.append(f"Pfad {status.path} ist schreibgeschützt.")
                recommendations.append(
                    f"Schreibrechte für {status.path} prüfen (z.B. chmod oder Eigentümerwechsel)."
                )

        for package in packages:
            if not package.installed:
                issues.append(f"Paket {package.name} ({package.purpose}) fehlt.")
                recommendations.append(package.message)

        status = "ok" if not issues else "attention"
        return {
            "status": status,
            "issues": issues,
            "recommendations": recommendations,
        }

    # ------------------------------------------------------------------
    def _build_startup_snapshot(self, report: Optional["StartupReport"]) -> Dict[str, object]:
        if report is None:
            return {}
        return {
            "created_virtualenv": report.created_virtualenv,
            "installed_dependencies": report.installed_dependencies,
            "repaired_paths": [str(path) for path in report.repaired_paths],
            "self_tests_total": len(report.self_tests),
            "self_tests_passed": report.all_self_tests_passed(),
            "headless_available": True,
        }


def VENV_FALLBACK() -> str:
    """Determine the fallback VENV path when no environment variable is set."""

    if sys.prefix and Path(sys.prefix).exists():
        return sys.prefix
    return str(Path(".venv").resolve())


__all__ = ["DiagnosticsManager", "DiagnosticsReport", "PackageStatus", "PathStatus"]
