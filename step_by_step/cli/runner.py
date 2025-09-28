"""Terminal-Launcher für das STEP-BY-STEP-Dashboard."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tkinter as tk
from typing import Optional

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


def _print_offline_section(report: StartupReport) -> None:
    if not report.offline_mode_enabled:
        return
    print("[Offline-Modus] Keine Paketnachinstallation möglich – Tool läuft mit Bordmitteln.")
    for reason in report.offline_reasons:
        print(f"  • Hinweis: {reason}")
    if report.degraded_features:
        print("  • Eingeschränkte Zusatzfunktionen:")
        for feature in report.degraded_features:
            print(f"    - {feature}")
    print(
        "  • Sobald Internet verfügbar ist: 'python -m pip install -r requirements.txt' "
        "ausführen, um die Pakete nachzuladen."
    )


def display_startup_report(report: StartupReport) -> None:
    """Print eine laienfreundliche Zusammenfassung aller Startprüfungen."""

    print("[Startprüfung] Zusammenfassung der automatischen Kontrollen:")
    for message in report.messages:
        print(f"  • {message}")
    if report.repaired_paths:
        repaired = ", ".join(str(path) for path in report.repaired_paths)
        print(f"  • Reparaturen: {repaired}")
    if report.dependency_messages:
        print("  • Paketinstallationen:")
        for description in report.dependency_messages:
            print(f"    - {description}")
    if report.self_tests:
        print("[Selbsttest] Ergebnisse:")
        for result in report.self_tests:
            status = "OK" if result.passed else "FEHLER"
            detail = f" – {result.details}" if result.details else ""
            print(f"  [{status}] {result.name}{detail}")
        if report.all_self_tests_passed():
            print("[Selbsttest] Alle Prüfungen bestanden. Das Protokoll liegt unter logs/startup.log.")
        else:
            print("[Selbsttest] Mindestens eine Prüfung meldete Probleme. Details siehe logs/startup.log.")
    if report.security_summary:
        summary = report.security_summary
        status = "OK" if summary.status == "ok" else "ACHTUNG"
        print("[Datensicherheit] Manifest-Prüfung:")
        summary_line = (
            f"  [{status}] {summary.verified} Dateien kontrolliert, {len(summary.issues)} Abweichungen"
        )
        print(summary_line)
        for issue in summary.issues:
            print(f"    - Warnung: {issue}")
        for backup in summary.backups:
            print(f"    - Sicherung erstellt: {backup}")
    if report.color_audit:
        audit = report.color_audit
        overall = str(audit.get("overall_status", "unknown"))
        worst_ratio = audit.get("worst_ratio", 0)
        try:
            numeric_ratio = float(worst_ratio)
        except (TypeError, ValueError):
            numeric_ratio = 0.0
        label = "OK" if overall == "ok" else "ACHTUNG"
        print("[Farbaudit] Zusammenfassung:")
        print(
            "  "
            f"[{label}] Niedrigster Kontrast {numeric_ratio:.2f}:1 – vollständiger Bericht: data/color_audit.json"
        )
        issues = list(audit.get("issues", []))
        recommendations = list(audit.get("recommendations", []))
        if issues:
            print("  • Hinweise auf schwache Kontraste:")
            for issue in issues[:5]:
                print(f"    - {issue}")
            if len(issues) > 5:
                print(f"    … {len(issues) - 5} weitere Hinweise im Bericht")
        if recommendations:
            print("  • Tipps zur Verbesserung:")
            for tip in recommendations[:5]:
                print(f"    - {tip}")
            if len(recommendations) > 5:
                print(f"    … {len(recommendations) - 5} weitere Tipps im Bericht")
    if report.diagnostics_messages:
        print("[Diagnose] Systemüberblick:")
        for line in report.diagnostics_messages:
            print(f"  • {line}")
    if report.diagnostics_path:
        print("[Diagnose] Vollständiger Bericht: %s" % report.diagnostics_path)
    if report.diagnostics_html_path:
        print("[Diagnose] HTML-Überblick: %s" % report.diagnostics_html_path)
    _print_offline_section(report)


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
    """Entry-point für Kommandozeile und Konsolen-Shortcut."""

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


__all__ = [
    "apply_font_scaling",
    "display_startup_report",
    "launch_gui",
    "main",
    "parse_args",
    "relaunch_if_needed",
]
