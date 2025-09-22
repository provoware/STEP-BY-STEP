"""Klick & Start launcher for the STEP-BY-STEP tool."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tkinter as tk

from step_by_step.core import ConfigManager, get_logger, setup_logging
from step_by_step.core.startup import RELAUNCH_ENV_FLAG, StartupManager
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


def main() -> int:
    args = parse_args()
    setup_logging()
    logger = get_logger("launcher")
    logger.info("Launcher gestartet (Argumente: %s)", args)

    startup = StartupManager()
    report = startup.run_startup_checks(argv=sys.argv)
    for message in report.messages:
        print(f"[Startprüfung] {message}")
    if report.repaired_paths:
        repaired = ", ".join(str(path) for path in report.repaired_paths)
        print(f"[Startprüfung] Reparierte/erstellte Dateien: {repaired}")
    if report.dependency_messages:
        for description in report.dependency_messages:
            print(f"[Startprüfung] Paketinstallation: {description}")

    if report.relaunch_command:
        env = os.environ.copy()
        env[RELAUNCH_ENV_FLAG] = "1"
        logger.info("Starte Tool erneut innerhalb der virtuellen Umgebung: %s", report.relaunch_command)
        return subprocess.call(report.relaunch_command, env=env)

    config_manager = ConfigManager()
    preferences = config_manager.load_preferences()
    logger.info("Einstellungen geladen: %s", preferences.to_dict())

    if args.headless:
        print("Selbsttest abgeschlossen. Einstellungen:")
        print(preferences)
        return 0

    try:
        app = MainWindow(preferences=preferences, logger=get_logger("ui"))
        if preferences.font_scale != 1.0:
            try:
                app.tk.call("tk", "scaling", preferences.font_scale)
            except tk.TclError:
                logger.warning("Skalierung konnte nicht angepasst werden.")
        app.mainloop()
    except Exception as error:  # pragma: no cover - defensive logging for GUI
        logger.exception("Unerwarteter Fehler im Hauptfenster", exc_info=error)
        raise
    finally:
        config_manager.save_preferences(preferences)
        logger.info("Einstellungen gespeichert.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
