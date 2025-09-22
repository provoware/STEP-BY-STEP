"""Klick & Start launcher for the STEP-BY-STEP tool."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tkinter as tk
from typing import Optional

from step_by_step.core import ConfigManager, get_logger, setup_logging
from step_by_step.core.startup import RELAUNCH_ENV_FLAG, StartupManager, StartupReport
from step_by_step.ui.main_window import MainWindow


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Startet das STEP-BY-STEP Tool und prüft vorab automatisch alle "
            "Abhängigkeiten (benötigte Pakete)."
        )
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Nur Selbsttest ausführen, aber keine Oberfläche öffnen.",
    )
    return parser.parse_args()


def display_startup_report(report: StartupReport) -> None:
    """Print a user-friendly summary of the startup checks."""

    print("[Startprüfung] Zusammenfassung der automatischen Kontrollen:")
    for message in report.messages:
        print(f"  • {message}")
    if report.repaired_paths:
        repaired = ", ".join(str(path) for path in report.repaired_paths)
        print(f"  • Reparaturen: {repaired}")
    if report.dependency_messages:
        print("  • Paketinstallationen wurden durchgeführt:")
        for description in report.dependency_messages:
            print(f"    - {description}")
    if report.self_tests:
        print("[Selbsttest] Ergebnisse:")
        for result in report.self_tests:
            status = "OK" if result.passed else "FEHLER"
            detail = f" – {result.details}" if result.details else ""
            print(f"  [{status}] {result.name}{detail}")
        if report.all_self_tests_passed():
            print("[Selbsttest] Alle Prüfungen bestanden. Das Startprotokoll liegt unter logs/startup.log.")
        else:
            print("[Selbsttest] Mindestens eine Prüfung meldete Probleme. Details stehen in logs/startup.log.")
    if report.security_summary:
        summary = report.security_summary
        status = "OK" if summary.status == "ok" else "ACHTUNG"
        print("[Datensicherheit] Manifest-Prüfung:")
        summary_line = (
            f"  [{status}] {summary.verified} Dateien kontrolliert, "
            f"{len(summary.issues)} Abweichungen"
        )
        print(summary_line)
        for issue in summary.issues:
            print(f"    - Warnung: {issue}")
        for backup in summary.backups:
            print(f"    - Sicherung erstellt: {backup}")


def relaunch_if_needed(report: StartupReport, logger) -> Optional[int]:
    """Restart the launcher inside the virtual environment when required."""

    if not report.relaunch_command:
        return None
    env = os.environ.copy()
    env[RELAUNCH_ENV_FLAG] = "1"
    logger.info("Starte Tool erneut innerhalb der virtuellen Umgebung: %s", report.relaunch_command)
    return subprocess.call(report.relaunch_command, env=env)


def apply_font_scaling(app: MainWindow, scale: float, logger) -> None:
    """Adjust the Tk (Toolkit für grafische Oberflächen) scaling factor."""

    if scale == 1.0:
        return
    try:
        app.tk.call("tk", "scaling", scale)
    except tk.TclError:
        logger.warning("Skalierung konnte nicht angepasst werden.")


def launch_gui(preferences) -> None:
    """Create and run the main application window."""

    ui_logger = get_logger("ui")
    app = MainWindow(preferences=preferences, logger=ui_logger)
    apply_font_scaling(app, preferences.font_scale, ui_logger)
    app.mainloop()


def main() -> int:
    args = parse_args()
    setup_logging()
    logger = get_logger("launcher")
    logger.info("Launcher gestartet (Argumente: %s)", args)

    startup = StartupManager()
    report = startup.run_startup_checks(argv=sys.argv)
    display_startup_report(report)

    relaunch_code = relaunch_if_needed(report, logger)
    if relaunch_code is not None:
        return relaunch_code

    config_manager = ConfigManager()
    preferences = config_manager.load_preferences()
    logger.info("Einstellungen geladen: %s", preferences.to_dict())

    if args.headless:
        print("[Headless] Der Selbsttest ist abgeschlossen. Aktive Einstellungen:")
        print(preferences)
        return 0

    try:
        launch_gui(preferences)
    except Exception as error:  # pragma: no cover - defensive logging for GUI
        logger.exception("Unerwarteter Fehler im Hauptfenster", exc_info=error)
        raise
    finally:
        config_manager.save_preferences(preferences)
        logger.info("Einstellungen gespeichert.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
