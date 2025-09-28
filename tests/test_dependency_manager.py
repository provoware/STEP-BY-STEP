from __future__ import annotations

import subprocess
from pathlib import Path

from step_by_step.core.dependency_manager import DependencyManager


class DummyCompletedProcess:
    def __init__(self, stdout: str = "", stderr: str = "") -> None:
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = 0


def test_dependency_manager_success(monkeypatch):
    """A successful installation returns a positive outcome."""

    def fake_run(command, capture_output, text, check):  # noqa: D401 - matches subprocess API
        return DummyCompletedProcess(stdout="installed")

    monkeypatch.setattr(subprocess, "run", fake_run)
    manager = DependencyManager("python")

    outcome = manager.install_requirements(Path("requirements.txt"), "requirements installieren")
    assert outcome is not None
    assert outcome.success is True
    assert outcome.stdout == "installed"
    assert outcome.stderr == ""


def test_dependency_manager_offline_detection(monkeypatch):
    """Offline marker strings should be translated into readable hints."""

    error = subprocess.CalledProcessError(
        1,
        ["python", "-m", "pip"],
        output="",
        stderr="Name or service not known",
    )

    def fake_run(*args, **kwargs):
        raise error

    monkeypatch.setattr(subprocess, "run", fake_run)
    manager = DependencyManager("python")

    outcome = manager.install_package(
        "simpleaudio",
        ["-m", "pip", "install", "simpleaudio"],
    )
    assert outcome.success is False
    assert outcome.offline_detected is True
    assert "Keine Netzwerkverbindung" in outcome.offline_hint
