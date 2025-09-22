"""Startup and self-repair routines for the STEP-BY-STEP tool."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from .logging_manager import get_logger

REQUIRED_FOLDERS: Sequence[Path] = (
    Path("data"),
    Path("logs"),
)

REQUIRED_FILES: Dict[Path, str] = {
    Path("data/settings.json"): json.dumps(
        {
            "font_scale": 1.0,
            "theme": "light",
            "autosave_interval_minutes": 10,
            "accessibility_mode": True,
            "shortcuts_enabled": True,
            "contrast_theme": "high_contrast",
        },
        indent=2,
    ),
    Path("data/todo_items.json"): json.dumps({"items": []}, indent=2),
    Path("data/playlists.json"): json.dumps({"tracks": []}, indent=2),
    Path("data/archive.json"): json.dumps({"entries": []}, indent=2),
    Path("data/persistent_notes.txt"): "",
    Path("data/usage_stats.json"): json.dumps({}, indent=2),
}

DEPENDENCY_COMMANDS: Dict[str, List[str]] = {
    "ttkbootstrap": ["-m", "pip", "install", "ttkbootstrap"],
}

VENV_PATH = Path(".venv")
REQUIREMENTS_FILE = Path("requirements.txt")
RELAUNCH_ENV_FLAG = "STEP_BY_STEP_VENV_ACTIVE"


@dataclass
class StartupReport:
    """Collect details about performed startup actions."""

    created_virtualenv: bool = False
    installed_dependencies: bool = False
    repaired_paths: List[Path] = field(default_factory=list)
    dependency_messages: List[str] = field(default_factory=list)
    relaunch_command: Optional[List[str]] = None
    messages: List[str] = field(default_factory=list)

    def add_message(self, message: str) -> None:
        self.messages.append(message)


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


__all__ = ["StartupManager", "StartupReport", "RELAUNCH_ENV_FLAG"]
