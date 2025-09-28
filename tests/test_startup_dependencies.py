from __future__ import annotations

from step_by_step.core import startup
from step_by_step.core.dependency_manager import DependencyInstallOutcome


def test_startup_manager_handles_offline_dependencies(monkeypatch):
    """Offline-Installationen aktivieren den Schonmodus und liefern Hinweise."""

    monkeypatch.setenv(startup.INSTALL_DEV_ENV_FLAG, "1")

    def fake_requirements(description: str) -> DependencyInstallOutcome:
        if "dev" in description:
            return DependencyInstallOutcome(
                description=description,
                success=False,
                stderr="Network is unreachable",
                offline_detected=True,
                offline_hint="Keine Netzwerkverbindung erreichbar – Installation wurde übersprungen.",
            )
        return DependencyInstallOutcome(
            description=description,
            success=True,
            stdout="ok",
        )

    class FakeDependencyManager:
        def __init__(self, python_executable: str) -> None:
            self.python_executable = python_executable

        def install_requirements(self, requirements_file, description):
            return fake_requirements(description)

        def install_package(self, package, command_arguments, description=None):
            return DependencyInstallOutcome(
                description=description or f"{package} installieren",
                success=False,
                stderr="network is unreachable",
                offline_detected=True,
                offline_hint="Netzwerk-Zeitüberschreitung: Verbindung prüfen und später erneut versuchen.",
            )

    monkeypatch.setattr(startup, "DependencyManager", FakeDependencyManager)
    monkeypatch.setitem(
        startup.DEPENDENCY_COMMANDS,
        "simpleaudio",
        ["-m", "pip", "install", "simpleaudio"],
    )

    manager = startup.StartupManager()
    manager.ensure_dependencies()

    report = manager.report
    assert report.installed_dependencies is True
    assert report.offline_mode_enabled is True
    assert any("requirements-dev.txt" in message for message in report.dependency_messages)
    assert any("Audiowiedergabe" in feature for feature in report.degraded_features)
    assert any("Netz" in reason for reason in report.offline_reasons)
