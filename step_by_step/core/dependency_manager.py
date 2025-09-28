"""Utility helpers for deterministic dependency installations."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence


@dataclass
class DependencyInstallOutcome:
    """Outcome information for a single dependency installation command."""

    description: str
    success: bool
    stdout: str = ""
    stderr: str = ""
    offline_detected: bool = False
    offline_hint: str = ""


class DependencyManager:
    """Run pip commands with enhanced diagnostics and offline detection."""

    OFFLINE_MARKERS = (
        "name or service not known",
        "temporary failure in name resolution",
        "failed to establish a new connection",
        "no such host is known",
        "nodename nor servname provided",
        "network is unreachable",
        "proxy connection failed",
    )

    def __init__(self, python_executable: str) -> None:
        self.python_executable = python_executable

    # ------------------------------------------------------------------
    def install_requirements(self, requirements_file: Path, description: str) -> Optional[DependencyInstallOutcome]:
        """Install dependencies from a requirements file when it exists."""

        if not requirements_file.exists():
            return None
        command = [
            self.python_executable,
            "-m",
            "pip",
            "install",
            "-r",
            str(requirements_file),
        ]
        return self._run(command, description)

    # ------------------------------------------------------------------
    def install_package(
        self,
        package: str,
        command_arguments: Sequence[str],
        *,
        description: Optional[str] = None,
    ) -> DependencyInstallOutcome:
        """Install a single package using pip arguments."""

        command = [self.python_executable, *command_arguments]
        final_description = description or f"{package} installieren"
        return self._run(command, final_description)

    # ------------------------------------------------------------------
    def _run(self, command: Sequence[str], description: str) -> DependencyInstallOutcome:
        """Execute ``pip`` and capture stdout/stderr with offline detection."""

        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True,
            )
        except subprocess.CalledProcessError as error:
            stderr = (error.stderr or "").strip()
            stdout = (error.stdout or "").strip()
            hint = self._detect_offline_hint(stderr or stdout)
            return DependencyInstallOutcome(
                description=description,
                success=False,
                stdout=stdout,
                stderr=stderr,
                offline_detected=hint is not None,
                offline_hint=hint or "",
            )
        except OSError as error:
            message = str(error)
            hint = self._detect_offline_hint(message)
            return DependencyInstallOutcome(
                description=description,
                success=False,
                stdout="",
                stderr=message,
                offline_detected=hint is not None,
                offline_hint=hint or "",
            )

        stdout = (result.stdout or "").strip()
        stderr = (result.stderr or "").strip()
        return DependencyInstallOutcome(
            description=description,
            success=True,
            stdout=stdout,
            stderr=stderr,
        )

    # ------------------------------------------------------------------
    def _detect_offline_hint(self, message: str) -> Optional[str]:
        """Return a human-readable hint when no network is available."""

        lowered = message.lower()
        for marker in self.OFFLINE_MARKERS:
            if marker in lowered:
                return "Keine Netzwerkverbindung erreichbar – Installation wurde übersprungen."
        if "connection timed out" in lowered or "timed out" in lowered:
            return "Netzwerk-Zeitüberschreitung: Verbindung prüfen und später erneut versuchen."
        return None


__all__ = ["DependencyManager", "DependencyInstallOutcome"]
