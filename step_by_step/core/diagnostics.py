"""Diagnostics helpers for the STEP-BY-STEP startup checks."""

from __future__ import annotations

import datetime as dt
import html
import json
import os
import platform
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple, TYPE_CHECKING

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
    required: str = ""
    meets_requirement: bool = True
    message: str = ""

    def to_dict(self) -> Dict[str, object]:
        return {
            "name": self.name,
            "purpose": self.purpose,
            "installed": self.installed,
            "version": self.version,
            "required": self.required,
            "meets_requirement": self.meets_requirement,
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
    html_report_path: str = ""

    def to_dict(self) -> Dict[str, object]:
        return {
            "generated_at": self.generated_at,
            "python": self.python,
            "virtualenv": self.virtualenv,
            "paths": self.paths,
            "packages": self.packages,
            "summary": self.summary,
            "startup": self.startup,
            "html_report_path": self.html_report_path,
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
    def export_html(self, diagnostics: DiagnosticsReport) -> Path:
        """Create an accessible HTML snapshot of the diagnostics."""

        target = Path("data/diagnostics_report.html")
        target.parent.mkdir(parents=True, exist_ok=True)
        summary = diagnostics.summary if isinstance(diagnostics.summary, dict) else {}
        issues = summary.get("issues", [])
        recommendations = summary.get("recommendations", [])

        def _render_rows(entries: Sequence[Dict[str, object]], keys: Sequence[str]) -> str:
            rows: List[str] = []
            for entry in entries:
                cells = []
                for key in keys:
                    value = entry.get(key, "") if isinstance(entry, dict) else ""
                    cells.append(f"<td>{html.escape(str(value))}</td>")
                rows.append("<tr>" + "".join(cells) + "</tr>")
            return "\n".join(rows)

        package_rows = _render_rows(
            diagnostics.packages,
            ["name", "version", "required", "installed", "meets_requirement", "message"],
        )
        path_rows = _render_rows(
            diagnostics.paths,
            ["path", "kind", "exists", "writable"],
        )

        html_payload = f"""
<!DOCTYPE html>
<html lang=\"de\">
  <head>
    <meta charset=\"utf-8\" />
    <title>STEP-BY-STEP – Systemdiagnose</title>
    <style>
      body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #0f0f0f; color: #f4f4f4; margin: 2rem; }}
      h1, h2 {{ color: #ffcc33; }}
      table {{ width: 100%; border-collapse: collapse; margin-bottom: 1.5rem; }}
      th, td {{ border: 1px solid #3a3a3a; padding: 0.5rem; text-align: left; }}
      th {{ background: #1d1d1d; }}
      tr:nth-child(even) {{ background: #191919; }}
      .ok {{ color: #6ad870; }}
      .warn {{ color: #ff9966; }}
      code {{ background: #1d1d1d; padding: 0.1rem 0.3rem; border-radius: 3px; }}
    </style>
  </head>
  <body>
    <h1>Systemdiagnose</h1>
    <p>Erstellt am <strong>{html.escape(diagnostics.generated_at)}</strong></p>

    <h2>Python</h2>
    <ul>
      <li>Version: <code>{html.escape(diagnostics.python.get('version', ''))}</code></li>
      <li>Interpreter: {html.escape(diagnostics.python.get('executable', ''))}</li>
      <li>Implementierung: {html.escape(diagnostics.python.get('implementation', ''))}</li>
      <li>Plattform: {html.escape(diagnostics.python.get('platform', ''))}</li>
    </ul>

    <h2>Virtuelle Umgebung</h2>
    <p>Status: <strong class=\"{'ok' if diagnostics.virtualenv.get('active') else 'warn'}\">{ 'aktiv' if diagnostics.virtualenv.get('active') else 'nicht aktiv' }</strong></p>
    <ul>
      <li>Erwarteter Pfad: {html.escape(diagnostics.virtualenv.get('expected_path', ''))}</li>
      <li>Aktueller Prefix: {html.escape(diagnostics.virtualenv.get('current_prefix', ''))}</li>
      <li>Umgebungsvariable: {html.escape(diagnostics.virtualenv.get('environment_path', ''))}</li>
    </ul>

    <h2>Pfadprüfung</h2>
    <table aria-label=\"Pfadstatus\">
      <thead><tr><th>Pfad</th><th>Typ</th><th>Vorhanden</th><th>Schreibbar</th></tr></thead>
      <tbody>
        {path_rows}
      </tbody>
    </table>

    <h2>Pakete</h2>
    <table aria-label=\"Paketstatus\">
      <thead><tr><th>Paket</th><th>Installierte Version</th><th>Vorgabe</th><th>Installiert</th><th>Version ok</th><th>Hinweis</th></tr></thead>
      <tbody>
        {package_rows}
      </tbody>
    </table>

    <h2>Zusammenfassung</h2>
    <p>Status: <strong class=\"{'ok' if summary.get('status') == 'ok' else 'warn'}\">{html.escape(summary.get('status', 'unbekannt'))}</strong></p>
    <h3>Hinweise</h3>
    <ul>
      {''.join(f'<li>{html.escape(item)}</li>' for item in issues) or '<li>Keine Hinweise</li>'}
    </ul>
    <h3>Empfehlungen</h3>
    <ul>
      {''.join(f'<li>{html.escape(item)}</li>' for item in recommendations) or '<li>Keine Empfehlungen</li>'}
    </ul>

    <h2>Startlauf</h2>
    <pre>{html.escape(json.dumps(diagnostics.startup, indent=2, ensure_ascii=False))}</pre>
  </body>
</html>
"""

        target.write_text(html_payload, encoding="utf-8")
        self.logger.info("Diagnosebericht (HTML) gespeichert: %s", target)
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
        outdated_packages = [
            pkg["name"]
            for pkg in packages
            if pkg.get("installed") and not pkg.get("meets_requirement", True)
        ]
        if outdated_packages:
            names = ", ".join(sorted(outdated_packages))
            lines.append(
                f"Versionsabweichung erkannt bei: {names} (Version kleiner als Vorgabe)."
            )
        if diagnostics.html_report_path:
            lines.append(
                f"HTML-Überblick gespeichert unter {diagnostics.html_report_path}."
            )
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
        purpose_map: Dict[str, str] = {
            "ttkbootstrap": "Theming (Oberflächen-Gestaltung)",
            "simpleaudio": "Audiowiedergabe",
        }
        requirements = self._parse_requirements()
        package_names = sorted({*purpose_map.keys(), *requirements.keys()})

        for package in package_names:
            purpose = purpose_map.get(package, "Abhängigkeit")
            required_spec = requirements.get(package, "")
            try:
                version = importlib_metadata.version(package)
                meets_requirement, hint = self._check_requirement(version, required_spec)
                message = hint or "Paket verfügbar."
                yield PackageStatus(
                    name=package,
                    purpose=purpose,
                    installed=True,
                    version=version,
                    required=required_spec,
                    meets_requirement=meets_requirement,
                    message=message,
                )
            except importlib_metadata.PackageNotFoundError:
                required_text = f" – benötigt {required_spec}" if required_spec else ""
                yield PackageStatus(
                    name=package,
                    purpose=purpose,
                    installed=False,
                    required=required_spec,
                    meets_requirement=False,
                    message=(
                        "Nicht installiert. Installation mit 'python -m pip install "
                        f"{package}' empfohlen{required_text}."
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
            elif not package.meets_requirement:
                issues.append(
                    f"Paket {package.name} erfüllt die Vorgabe {package.required} nicht (Version {package.version})."
                )
                recommendations.append(
                    f"'{package.name}' aktualisieren (z.B. python -m pip install --upgrade {package.name})."
                )

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

    # ------------------------------------------------------------------
    def _parse_requirements(self) -> Dict[str, str]:
        requirements: Dict[str, str] = {}
        requirements_file = Path("requirements.txt")
        if not requirements_file.exists():
            return requirements
        for line in requirements_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            match = re.match(r"^([A-Za-z0-9_.-]+)\s*([<>=!~]+\s*.+)?$", line)
            if not match:
                continue
            name = match.group(1)
            spec = (match.group(2) or "").strip()
            requirements[name] = spec
        return requirements

    # ------------------------------------------------------------------
    def _check_requirement(self, current: str, spec: str) -> Tuple[bool, str]:
        if not spec:
            return True, ""
        comparator_match = re.match(r"^(>=|<=|==|>|<|~=)?\s*(.+)$", spec)
        if not comparator_match:
            return True, ""
        comparator = comparator_match.group(1) or ">="
        required_version = comparator_match.group(2)
        current_version = self._parse_version(current)
        target_version = self._parse_version(required_version)
        comparison = self._compare_versions(current_version, target_version)

        operations = {
            ">": comparison > 0,
            ">=": comparison >= 0,
            "<": comparison < 0,
            "<=": comparison <= 0,
            "==": comparison == 0,
            "~=": comparison >= 0,
        }
        meets = operations.get(comparator, True)
        if meets:
            return True, ""
        return False, f"Version {current} erfüllt Vorgabe {spec} nicht."

    def _parse_version(self, value: str) -> Tuple[int, ...]:
        parts = re.findall(r"\d+", value)
        if not parts:
            return (0,)
        return tuple(int(part) for part in parts)

    def _compare_versions(self, current: Tuple[int, ...], target: Tuple[int, ...]) -> int:
        length = max(len(current), len(target))
        current_extended = current + (0,) * (length - len(current))
        target_extended = target + (0,) * (length - len(target))
        if current_extended > target_extended:
            return 1
        if current_extended < target_extended:
            return -1
        return 0


__all__ = ["DiagnosticsManager", "DiagnosticsReport", "PackageStatus", "PathStatus"]

