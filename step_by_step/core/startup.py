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
from typing import Dict, List, Optional, Sequence, Tuple

from .logging_manager import get_logger

REQUIRED_FOLDERS: Sequence[Path] = (
    Path("data"),
    Path("logs"),
    Path("data/exports"),
    Path("data/converted_audio"),
)

REQUIRED_FILES: Dict[Path, str] = {
    Path("data/settings.json"): json.dumps(
        {
            "font_scale": 1.2,
            "theme": "light",
            "autosave_interval_minutes": 10,
            "accessibility_mode": True,
            "shortcuts_enabled": True,
            "contrast_theme": "high_contrast",
            "color_mode": "high_contrast",
            "audio_volume": 0.8,
        },
        indent=2,
    ),
    Path("data/todo_items.json"): json.dumps({"items": []}, indent=2),
    Path("data/playlists.json"): json.dumps({"tracks": []}, indent=2),
    Path("data/archive.json"): json.dumps({"entries": []}, indent=2),
    Path("data/persistent_notes.txt"): "",
    Path("data/usage_stats.json"): json.dumps({}, indent=2),
    Path("data/selftest_report.json"): json.dumps(
        {
            "last_run": "",
            "all_passed": False,
            "self_tests": [],
            "messages": [],
            "repaired_paths": [],
            "dependency_messages": [],
        },
        indent=2,
        ensure_ascii=False,
    ),
    Path("data/release_checklist.json"): json.dumps(
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
                    "done": False,
                    "details": "Letzte End-to-End-Prüfung und Handbuch-Freigabe.",
                },
            ],
            "updated_at": "",
        },
        indent=2,
        ensure_ascii=False,
    ),
}


def _default_settings() -> Dict[str, object]:
    """Return a fresh copy of the default settings payload."""

    return json.loads(REQUIRED_FILES[Path("data/settings.json")])

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

    # ------------------------------------------------------------------
    def run_startup_checks(self, argv: Optional[List[str]] = None) -> StartupReport:
        self.logger.info("Startroutine beginnt")
        self.report = StartupReport()
        if argv is not None:
            self._argv = list(argv)
        self._write_diagnostic("Startroutine wird ausgeführt...")

        self.ensure_structure()
        self.ensure_virtual_environment()
        self.ensure_dependencies()
        self.run_self_tests()
        self._persist_report()

        self.logger.info("Startroutine beendet")
        self._write_diagnostic("Startroutine beendet.")
        return self.report

    # ------------------------------------------------------------------
    def ensure_structure(self) -> None:
        for folder in REQUIRED_FOLDERS:
            folder.mkdir(parents=True, exist_ok=True)
            self._log_progress(f"Ordner geprüft: {folder}")
        for path, template in REQUIRED_FILES.items():
            if not path.exists():
                path.write_text(template, encoding="utf-8")
                self.report.repaired_paths.append(path)
                self._log_progress(f"Datei ergänzt: {path}")
            else:
                self._log_progress(f"Datei vorhanden: {path}")
            if path.name == "settings.json":
                self._ensure_settings_defaults(path)

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
        target = Path("data/selftest_report.json")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        self._log_progress("Selbsttest-Ergebnisse gespeichert.")

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
        desired_scale = 1.2
        try:
            raw = json.loads(settings_path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            settings_path.write_text(REQUIRED_FILES[settings_path], encoding="utf-8")
            if settings_path not in self.report.repaired_paths:
                self.report.repaired_paths.append(settings_path)
            return False, "Einstellungsdatei fehlte und wurde ersetzt."
        except json.JSONDecodeError:
            settings_path.write_text(REQUIRED_FILES[settings_path], encoding="utf-8")
            if settings_path not in self.report.repaired_paths:
                self.report.repaired_paths.append(settings_path)
            return False, "Einstellungsdatei war defekt und wurde erneuert."

        changed = False
        default_settings = _default_settings()
        for key, value in default_settings.items():
            if key not in raw:
                raw[key] = value
                changed = True
        try:
            scale_value = float(raw.get("font_scale", desired_scale))
        except (TypeError, ValueError):
            scale_value = desired_scale
        if scale_value < desired_scale:
            raw["font_scale"] = desired_scale
            changed = True
        if changed:
            settings_path.write_text(json.dumps(raw, indent=2), encoding="utf-8")
            if settings_path not in self.report.repaired_paths:
                self.report.repaired_paths.append(settings_path)
            return True, "Einstellungen wurden automatisch aktualisiert."
        return True, "Einstellungen sind vollständig."

    def _ensure_settings_defaults(self, settings_path: Path) -> None:
        """Keep persisted settings aligned with recommended defaults."""

        desired_scale = 1.2
        try:
            content = json.loads(settings_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            settings_path.write_text(REQUIRED_FILES[settings_path], encoding="utf-8")
            if settings_path not in self.report.repaired_paths:
                self.report.repaired_paths.append(settings_path)
            self._log_progress("Einstellungen zurückgesetzt (ungültiges Format).", level="error")
            return

        try:
            current_scale = float(content.get("font_scale", desired_scale))
        except (TypeError, ValueError):
            current_scale = desired_scale
        if current_scale < desired_scale:
            content["font_scale"] = desired_scale
            settings_path.write_text(json.dumps(content, indent=2), encoding="utf-8")
            if settings_path not in self.report.repaired_paths:
                self.report.repaired_paths.append(settings_path)
            self._log_progress("Schriftgröße dauerhaft auf 1.2 angehoben.")

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

    def _launcher_path(self) -> Path:
        return Path(__file__).resolve().parents[2] / "start_tool.py"


__all__ = ["StartupManager", "StartupReport", "SelfTestResult", "RELAUNCH_ENV_FLAG"]
