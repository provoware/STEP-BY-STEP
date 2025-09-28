"""Terminal-Launcher für das STEP-BY-STEP-Dashboard."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tkinter as tk
from logging import Logger
from typing import Optional

from step_by_step.cli.reporting import StartupReportPresenter
from step_by_step.core import ConfigManager, get_logger, setup_logging
from step_by_step.core.startup import (
    RELAUNCH_ENV_FLAG,
    StartupManager,
    StartupReport,
)
from step_by_step.ui.main_window import MainWindow


def parse_args() -> argparse.Namespace:
    """Leserliche Argumente für den Schnellstart (Headless = ohne Fenster)."""

    parser = argparse.ArgumentParser(
        description=(
            "Startet das STEP-BY-STEP Tool und prüft vorher alle notwendigen "
            "Pakete (Abhängigkeiten)."
        )
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Nur Selbsttest ausführen, aber keine Oberfläche (GUI) öffnen.",
    )
    return parser.parse_args()

def relaunch_if_needed(report: StartupReport, logger: Logger) -> Optional[int]:
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
    """Entry-point für Kommandozeile und Konsolen-Shortcut."""

    args = parse_args()
    setup_logging()
    logger = get_logger("launcher")
    logger.info("Launcher gestartet (Argumente: %s)", args)

    startup = StartupManager()
    report = startup.run_startup_checks(argv=sys.argv)
    StartupReportPresenter(report).print()

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


__all__ = [
    "apply_font_scaling",
    "launch_gui",
    "main",
    "parse_args",
    "relaunch_if_needed",
]
