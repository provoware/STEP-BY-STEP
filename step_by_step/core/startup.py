"""Startup and self-repair routines for the STEP-BY-STEP tool."""

from __future__ import annotations

import compileall
import datetime as dt
import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from .color_audit import ColorAuditor
from .diagnostics import DiagnosticsManager
from .logging_manager import get_logger
from .resources import (
    ARCHIVE_DB_PATH,
    REQUIRED_FOLDERS,
    iter_required_files,
    required_file_content,
)
from .security import SecurityManager, SecuritySummary
from .validators import SettingsValidator

MAX_STARTUP_LOG_LINES = 2000

DEPENDENCY_COMMANDS: Dict[str, List[str]] = {
    "ttkbootstrap": ["-m", "pip", "install", "ttkbootstrap"],
    "simpleaudio": ["-m", "pip", "install", "simpleaudio"],
}

VENV_PATH = Path(".venv")
REQUIREMENTS_FILE = Path("requirements.txt")
RELAUNCH_ENV_FLAG = "STEP_BY_STEP_VENV_ACTIVE"


@dataclass
class SelfTestResult:
    """Represent the outcome of a single self-test."""

    name: str
    passed: bool
    details: str = ""


@dataclass
class StartupReport:
    """Collect details about performed startup actions."""

    created_virtualenv: bool = False
    installed_dependencies: bool = False
    repaired_paths: List[Path] = field(default_factory=list)
    dependency_messages: List[str] = field(default_factory=list)
    self_tests: List[SelfTestResult] = field(default_factory=list)
    relaunch_command: Optional[List[str]] = None
    messages: List[str] = field(default_factory=list)
    security_summary: Optional[SecuritySummary] = None
    color_audit: Optional[Dict[str, object]] = None
    diagnostics: Optional[Dict[str, object]] = None
    diagnostics_messages: List[str] = field(default_factory=list)
    diagnostics_path: Optional[Path] = None
    diagnostics_html_path: Optional[Path] = None

    def add_message(self, message: str) -> None:
        self.messages.append(message)

    def all_self_tests_passed(self) -> bool:
        if not self.self_tests:
            return True
        return all(result.passed for result in self.self_tests)


class StartupManager:
    """Ensure the application can start safely and inform the user."""

    def __init__(self) -> None:
        self.logger = get_logger("core.startup")
        self.report = StartupReport()
        self.diagnostics_file = Path("logs/startup.log")
        self.diagnostics_file.parent.mkdir(parents=True, exist_ok=True)
        self._argv: List[str] = list(sys.argv)
        self.settings_validator = SettingsValidator()

    # ------------------------------------------------------------------
    def run_startup_checks(self, argv: Optional[List[str]] = None) -> StartupReport:
        self.logger.info("Startroutine beginnt")
        trimmed = self._trim_diagnostics_log()
        self.report = StartupReport()
        if argv is not None:
            self._argv = list(argv)
        self._write_diagnostic("Startroutine wird ausgeführt...")
        if trimmed:
            self._log_progress(
                (
                    "Startprotokoll bereinigt: Ältere Einträge wurden entfernt, "
                    f"es bleiben die letzten {MAX_STARTUP_LOG_LINES} Zeilen."
                )
            )

        steps: Sequence[Tuple[str, Callable[[], None]]] = (
            ("Strukturprüfung", self.ensure_structure),
            ("Virtuelle Umgebung prüfen", self.ensure_virtual_environment),
            ("Abhängigkeiten prüfen", self.ensure_dependencies),
            ("Datensicherheit prüfen", self.verify_data_security),
            ("Farbaudit ausführen", self.audit_color_contrast),
            ("Selbsttests ausführen", self.run_self_tests),
            ("Diagnose erfassen", self.capture_diagnostics),
        )

        for label, step in steps:
            self._run_step(label, step)

        self._persist_report()

        self.logger.info("Startroutine beendet")
        self._write_diagnostic("Startroutine beendet.")
        return self.report

    # ------------------------------------------------------------------
    def ensure_structure(self) -> None:
        for folder in REQUIRED_FOLDERS:
            folder.mkdir(parents=True, exist_ok=True)
            self._log_progress(f"Ordner geprüft: {folder}")
        for path, template in iter_required_files():
            if not path.exists():
                path.write_text(template, encoding="utf-8")
                self.report.repaired_paths.append(path)
                self._log_progress(f"Datei ergänzt: {path}")
            else:
                self._log_progress(f"Datei vorhanden: {path}")
            if path.name == "settings.json":
                self._ensure_settings_defaults(path)
        self._ensure_archive_database()

    # ------------------------------------------------------------------
    def _ensure_archive_database(self) -> None:
        """Create the SQLite archive database when it is missing."""

        if ARCHIVE_DB_PATH.exists():
            self._log_progress(f"Archiv-Datenbank vorhanden: {ARCHIVE_DB_PATH}")
            return

        try:
            from step_by_step.modules.database import DatabaseModule

            DatabaseModule(database_file=ARCHIVE_DB_PATH, logger=self.logger)
        except Exception as error:  # pragma: no cover - defensive bootstrap
            self._log_progress(
                f"Archiv-Datenbank konnte nicht erstellt werden: {error}",
                level="error",
            )
            return

        self.report.repaired_paths.append(ARCHIVE_DB_PATH)
        self._log_progress(f"Archiv-Datenbank initialisiert: {ARCHIVE_DB_PATH}")

    # ------------------------------------------------------------------
    def ensure_virtual_environment(self) -> None:
        python_in_venv = self._python_in_venv()
        if not python_in_venv.exists():
            self._create_virtualenv(python_in_venv)
        else:
            self._log_progress(f"Virtuelle Umgebung vorhanden: {python_in_venv}")

        if not self._running_inside_venv() and not os.environ.get(RELAUNCH_ENV_FLAG):
            command = [str(python_in_venv), str(self._launcher_path())]
            if len(self._argv) > 1:
                command.extend(self._argv[1:])
            self.report.relaunch_command = command
            self._log_progress("Neustart innerhalb der virtuellen Umgebung erforderlich.")

    # ------------------------------------------------------------------
    def ensure_dependencies(self) -> None:
        python_exec = self._python_for_dependencies()
        if REQUIREMENTS_FILE.exists():
            command = [python_exec, "-m", "pip", "install", "-r", str(REQUIREMENTS_FILE)]
            self._run_dependency_command(command, description="requirements.txt installieren")
        for package, command_args in DEPENDENCY_COMMANDS.items():
            if not self._is_package_installed(package):
                command = [python_exec, *command_args]
                self._run_dependency_command(command, description=f"{package} installieren")
            else:
                self._log_progress(f"Paket bereits verfügbar: {package}")

    # ------------------------------------------------------------------
    def run_self_tests(self) -> None:
        """Execute lightweight self-tests to ensure a safe launch."""

        self._log_progress("Selbsttests starten...")
        for name, test in (
            ("Python-Codeprüfung", self._self_test_compileall),
            ("Einstellungsprüfung", self._self_test_settings),
        ):
            passed, details = test()
            self.report.self_tests.append(SelfTestResult(name=name, passed=passed, details=details))
            status = "erfolgreich" if passed else "fehlgeschlagen"
            message = f"Selbsttest {name} {status}."
            if details:
                message = f"{message} {details}"
            self._log_progress(message, level="info" if passed else "error")
        self._log_progress("Selbsttests abgeschlossen.")

    # ------------------------------------------------------------------
    def verify_data_security(self) -> None:
        manager = SecurityManager()
        summary = manager.verify_files()
        self.report.security_summary = summary
        self._log_progress(
            (
                "Datensicherheit geprüft: "
                f"{summary.verified} Dateien kontrolliert, "
                f"{len(summary.issues)} Abweichungen"
            ),
            level="error" if summary.issues else "info",
        )
        for issue in summary.issues:
            self._log_progress(f"Sicherheitswarnung: {issue}", level="error")
        for backup in summary.backups:
            self._log_progress(f"Sicherung erstellt: {backup}")
        for removed in summary.pruned_backups:
            self._log_progress(f"Altes Backup entfernt: {removed}")
        for restore in summary.restore_points:
            filename = restore.get("file", "")
            status = restore.get("status")
            backup = restore.get("backup")
            message = restore.get("message")
            if status == "ok":
                detail = backup or "aktuelles Backup"
                self._log_progress(
                    f"Restore-Check erfolgreich: {filename} ← {detail}",
                )
            else:
                detail = message or f"Backup prüfen ({backup})"
                self._log_progress(
                    f"Restore-Hinweis: {filename} – {detail}",
                    level="error",
                )

    # ------------------------------------------------------------------
    def audit_color_contrast(self) -> None:
        auditor = ColorAuditor()
        try:
            report = auditor.generate_report()
        except Exception as error:  # pragma: no cover - defensive guard
            payload = {
                "generated_at": dt.datetime.now().isoformat(),
                "overall_status": "error",
                "worst_ratio": 0.0,
                "themes": [],
                "issues": [f"Farbaudit fehlgeschlagen: {error}"],
                "recommendations": [],
            }
            target = Path("data/color_audit.json")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(
                json.dumps(payload, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            self.report.color_audit = payload
            self._log_progress(f"Farbaudit fehlgeschlagen: {error}", level="error")
            return

        payload = report.to_dict()
        self.report.color_audit = payload
        target = Path("data/color_audit.json")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        status = report.overall_status
        self._log_progress(
            (
                "Farbaudit abgeschlossen: "
                f"{len(report.themes)} Themen geprüft, niedrigster Kontrast {report.worst_ratio:.2f}:1"
            ),
            level="error" if status != "ok" else "info",
        )
        for issue in report.issues:
            self._log_progress(f"Farbaudit-Hinweis: {issue}", level="error")
        for recommendation in getattr(report, "recommendations", []):
            self._log_progress(f"Farbaudit-Tipp: {recommendation}")
        refreshed_summary = SecurityManager().verify_files()
        self.report.security_summary = refreshed_summary
        self._log_progress(
            (
                "Datensicherheit nach Farbaudit aktualisiert: "
                f"{refreshed_summary.verified} Dateien geprüft, {len(refreshed_summary.issues)} Hinweise"
            ),
            level="error" if refreshed_summary.issues else "info",
        )
        for restore in refreshed_summary.restore_points:
            filename = restore.get("file", "")
            status = restore.get("status")
            backup = restore.get("backup")
            message = restore.get("message")
            if status == "ok":
                detail = backup or "aktuelles Backup"
                self._log_progress(
                    f"Restore-Check erfolgreich: {filename} ← {detail}",
                )
            else:
                detail = message or f"Backup prüfen ({backup})"
                self._log_progress(
                    f"Restore-Hinweis: {filename} – {detail}",
                    level="error",
                )

    # ------------------------------------------------------------------
    def capture_diagnostics(self) -> None:
        manager = DiagnosticsManager()
        try:
            diagnostics = manager.collect(self.report)
        except Exception as error:  # pragma: no cover - defensive guard
            payload = {
                "generated_at": dt.datetime.now().isoformat(),
                "python": {},
                "virtualenv": {},
                "paths": [],
                "packages": [],
                "summary": {
                    "status": "error",
                    "issues": [f"Diagnose konnte nicht erstellt werden: {error}"],
                    "recommendations": [],
                },
                "startup": {},
                "html_report_path": "",
            }
            target = Path("data/diagnostics_report.json")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(
                json.dumps(payload, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            self.report.diagnostics = payload
            self.report.diagnostics_path = target
            self.report.diagnostics_html_path = None
            message = f"Diagnose fehlgeschlagen: {error}"
            self.report.diagnostics_messages.append(message)
            self._log_progress(message, level="error")
            return

        html_path: Optional[Path] = None
        try:
            html_path = manager.export_html(diagnostics)
        except Exception as error:  # pragma: no cover - defensive guard
            self._log_progress(
                f"Diagnose-HTML konnte nicht erstellt werden: {error}",
                level="error",
            )

        diagnostics_path: Optional[Path] = None
        try:
            diagnostics_path = manager.save(diagnostics)
        except Exception as error:  # pragma: no cover - defensive guard
            self._log_progress(
                f"Diagnosebericht konnte nicht gespeichert werden: {error}",
                level="error",
            )

        diagnostics_dict = diagnostics.to_dict()
        if html_path:
            diagnostics.html_report_path = str(html_path)
            diagnostics_dict["html_report_path"] = str(html_path)
        self.report.diagnostics = diagnostics_dict
        self.report.diagnostics_path = diagnostics_path
        self.report.diagnostics_html_path = html_path
        try:
            summary_lines = manager.summary_lines(diagnostics)
        except Exception as error:  # pragma: no cover - defensive guard
            summary_lines = [f"Diagnose-Zusammenfassung nicht verfügbar: {error}"]
            self._log_progress(summary_lines[0], level="error")
        else:
            for line in summary_lines:
                self._log_progress(line)
        self.report.diagnostics_messages = summary_lines
        if html_path:
            self._log_progress(f"Diagnose als HTML gespeichert: {html_path}")

    # ------------------------------------------------------------------
    def _persist_report(self) -> None:
        """Store the latest startup report for display in the dashboard."""

        payload = {
            "last_run": dt.datetime.now().isoformat(),
            "all_passed": self.report.all_self_tests_passed(),
            "created_virtualenv": self.report.created_virtualenv,
            "installed_dependencies": self.report.installed_dependencies,
            "repaired_paths": [str(path) for path in self.report.repaired_paths],
            "dependency_messages": self.report.dependency_messages,
            "messages": self.report.messages,
            "self_tests": [
                {"name": result.name, "passed": result.passed, "details": result.details}
                for result in self.report.self_tests
            ],
        }
        if self.report.security_summary:
            payload["security_summary"] = self.report.security_summary.to_dict()
        if self.report.color_audit:
            payload["color_audit"] = self.report.color_audit
        if self.report.diagnostics:
            payload["diagnostics"] = self.report.diagnostics
        if self.report.diagnostics_messages:
            payload["diagnostics_messages"] = self.report.diagnostics_messages
        if self.report.diagnostics_path:
            payload["diagnostics_report_path"] = str(self.report.diagnostics_path)
        if self.report.diagnostics_html_path:
            payload["diagnostics_report_html_path"] = str(self.report.diagnostics_html_path)
        target = Path("data/selftest_report.json")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        self._log_progress("Selbsttest-Ergebnisse gespeichert.")

    # ------------------------------------------------------------------
    def _run_step(self, label: str, callback: Callable[[], None]) -> None:
        try:
            callback()
        except Exception as error:  # pragma: no cover - defensive umbrella
            message = f"{label} fehlgeschlagen: {error}"
            self._log_progress(message, level="error")
            self.logger.exception("%s", message, exc_info=error)

    # ------------------------------------------------------------------
    def _create_virtualenv(self, python_in_venv: Path) -> None:
        self._log_progress("Virtuelle Umgebung wird erstellt...")
        result = subprocess.run([sys.executable, "-m", "venv", str(VENV_PATH)], check=False)
        if result.returncode == 0 and python_in_venv.exists():
            self.report.created_virtualenv = True
            self._log_progress(f"Virtuelle Umgebung erstellt: {python_in_venv}")
        else:
            self._log_progress("Fehler beim Erstellen der virtuellen Umgebung", level="error")

    def _run_dependency_command(self, command: List[str], description: str) -> None:
        self._log_progress(f"{description} wird ausgeführt: {' '.join(command)}")
        result = subprocess.run(command, check=False)
        if result.returncode == 0:
            self.report.installed_dependencies = True
            self.report.dependency_messages.append(description)
            self._log_progress(f"{description} erfolgreich.")
        else:
            self._log_progress(f"{description} fehlgeschlagen (Code {result.returncode}).", level="error")

    def _self_test_compileall(self) -> Tuple[bool, str]:
        """Compile the code base to bytecode to spot syntax errors."""

        target = Path("step_by_step")
        try:
            success = compileall.compile_dir(
                str(target), quiet=1, legacy=False, workers=1
            )
        except Exception as exc:  # pragma: no cover - defensive guard
            return False, f"Fehler beim Kompilieren: {exc}"
        return success, "Alle Module wurden geprüft." if success else "Bitte Protokoll prüfen."

    def _self_test_settings(self) -> Tuple[bool, str]:
        """Validate settings and ensure recommended accessibility defaults."""

        settings_path = Path("data/settings.json")
        try:
            raw = json.loads(settings_path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            template = required_file_content(settings_path)
            settings_path.write_text(template, encoding="utf-8")
            if settings_path not in self.report.repaired_paths:
                self.report.repaired_paths.append(settings_path)
            return False, "Einstellungsdatei fehlte und wurde ersetzt."
        except json.JSONDecodeError:
            template = required_file_content(settings_path)
            settings_path.write_text(template, encoding="utf-8")
            if settings_path not in self.report.repaired_paths:
                self.report.repaired_paths.append(settings_path)
            return False, "Einstellungsdatei war defekt und wurde erneuert."

        sanitised, adjustments = self.settings_validator.normalise(raw)
        if sanitised != raw:
            settings_path.write_text(
                json.dumps(sanitised, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            if settings_path not in self.report.repaired_paths:
                self.report.repaired_paths.append(settings_path)
            detail = "Einstellungen wurden automatisch aktualisiert."
            if adjustments:
                detail = f"{detail} {' '.join(adjustments)}"
            return True, detail
        return True, "Einstellungen sind vollständig."

    def _ensure_settings_defaults(self, settings_path: Path) -> None:
        """Keep persisted settings aligned with recommended defaults."""

        try:
            content = json.loads(settings_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            sanitised, adjustments = self.settings_validator.normalise({})
            settings_path.write_text(
                json.dumps(sanitised, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            if settings_path not in self.report.repaired_paths:
                self.report.repaired_paths.append(settings_path)
            self._log_progress("Einstellungen zurückgesetzt (ungültiges Format).", level="error")
            for note in adjustments:
                self._log_progress(f"Einstellungs-Hinweis: {note}")
            return

        sanitised, adjustments = self.settings_validator.normalise(content)
        if sanitised != content:
            settings_path.write_text(
                json.dumps(sanitised, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            if settings_path not in self.report.repaired_paths:
                self.report.repaired_paths.append(settings_path)
            self._log_progress("Einstellungen automatisch aktualisiert.")
            for note in adjustments:
                self._log_progress(f"Einstellungs-Hinweis: {note}")

    def _python_in_venv(self) -> Path:
        if sys.platform == "win32":
            return VENV_PATH / "Scripts" / "python.exe"
        return VENV_PATH / "bin" / "python"

    def _python_for_dependencies(self) -> str:
        python_in_venv = self._python_in_venv()
        return str(python_in_venv if python_in_venv.exists() else sys.executable)

    def _running_inside_venv(self) -> bool:
        return sys.prefix != getattr(sys, "base_prefix", sys.prefix)

    def _is_package_installed(self, package: str) -> bool:
        try:
            __import__(package)
        except ImportError:
            return False
        return True

    def _log_progress(self, message: str, level: str = "info") -> None:
        self.report.add_message(message)
        if level == "error":
            self.logger.error(message)
        else:
            self.logger.info(message)
        self._write_diagnostic(message)

    def _write_diagnostic(self, message: str) -> None:
        with self.diagnostics_file.open("a", encoding="utf-8") as handle:
            handle.write(f"{message}\n")

    def _trim_diagnostics_log(self, max_lines: int = MAX_STARTUP_LOG_LINES) -> bool:
        """Kürzt das Startprotokoll auf eine sinnvolle Länge (Hauskeeping)."""

        if max_lines <= 0 or not self.diagnostics_file.exists():
            return False
        try:
            with self.diagnostics_file.open("r", encoding="utf-8") as handle:
                lines = handle.readlines()
        except OSError as error:
            self.logger.warning("Startprotokoll konnte nicht gelesen werden: %s", error)
            return False
        if len(lines) <= max_lines:
            return False
        trimmed = lines[-max_lines:]
        try:
            with self.diagnostics_file.open("w", encoding="utf-8") as handle:
                handle.writelines(trimmed)
        except OSError as error:
            self.logger.warning("Startprotokoll konnte nicht gekürzt werden: %s", error)
            return False
        self.logger.info(
            "Startprotokoll verkürzt: nur die letzten %s Zeilen bleiben erhalten.",
            max_lines,
        )
        return True

    def _launcher_path(self) -> Path:
        return Path(__file__).resolve().parents[2] / "start_tool.py"


__all__ = ["StartupManager", "StartupReport", "SelfTestResult", "RELAUNCH_ENV_FLAG"]
