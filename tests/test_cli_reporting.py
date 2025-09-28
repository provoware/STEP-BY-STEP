"""Tests for the console presentation of startup reports."""

from __future__ import annotations

from io import StringIO
from pathlib import Path

from step_by_step.cli.reporting import StartupReportPresenter
from step_by_step.core.security import SecuritySummary
from step_by_step.core.startup import SelfTestResult, StartupReport


def build_sample_report() -> StartupReport:
    report = StartupReport()
    report.messages.append("Ordner geprüft: data/")
    report.repaired_paths.append(Path("data/settings.json"))
    report.dependency_messages.extend(
        ["requirements.txt installieren (bereits aktuell)", "simpleaudio installieren"]
    )
    report.self_tests.extend(
        [
            SelfTestResult(name="Python-Codeprüfung", passed=True),
            SelfTestResult(name="Einstellungsprüfung", passed=False, details="Schriftgröße korrigiert"),
        ]
    )
    report.security_summary = SecuritySummary(
        status="attention",
        verified=5,
        issues=["data/settings.json: Prüfsumme neu erzeugt"],
        backups=["data/backups/settings.json.1"],
    )
    report.color_audit = {
        "overall_status": "attention",
        "worst_ratio": "2.5",
        "issues": ["Zu geringer Kontrast" for _ in range(6)],
        "recommendations": ["Dunklere Schrift testen"],
    }
    report.diagnostics_messages.append("Python 3.11 erkannt")
    report.diagnostics_path = Path("data/diagnostics_report.json")
    report.diagnostics_html_path = Path("data/diagnostics_report.html")
    report.offline_mode_enabled = True
    report.offline_reasons.append("Netzwerkkabel getrennt")
    report.degraded_features.append("Audio-Wiedergabe (simpleaudio)")
    return report


def test_presenter_lists_all_sections() -> None:
    report = build_sample_report()
    presenter = StartupReportPresenter(report)

    lines = list(presenter.iter_lines())

    assert any("Reparaturen" in line for line in lines)
    assert any("Paketinstallationen" in line for line in lines)
    assert any(line.startswith("[Selbsttest] Ergebnisse") for line in lines)
    assert any("[Datensicherheit]" in line for line in lines)
    assert any("[Farbaudit]" in line for line in lines)
    assert any("[Diagnose] Vollständiger Bericht" in line for line in lines)
    assert any("[Offline-Modus]" in line for line in lines)
    # Bullet list gets truncated with an ellipsis line for additional entries
    assert any(line.startswith("    … 1 weitere") for line in lines)


def test_presenter_print_writes_to_stream() -> None:
    report = build_sample_report()
    presenter = StartupReportPresenter(report)

    buffer = StringIO()
    presenter.print(stream=buffer)

    payload = buffer.getvalue()
    assert "Ordner geprüft" in payload
    assert "Sobald Internet verfügbar ist" in payload
    assert payload.count("Zu geringer Kontrast") == 5


def test_presenter_hides_offline_section_when_disabled() -> None:
    report = StartupReport()
    presenter = StartupReportPresenter(report)

    text = presenter.render()

    assert "Offline-Modus" not in text
