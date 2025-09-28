"""Formatting helpers for presenting startup reports to end users."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence, TextIO

from step_by_step.core.startup import StartupReport


@dataclass
class StartupReportPresenter:
    """Convert a :class:`StartupReport` into readable console output."""

    report: StartupReport

    def iter_lines(self) -> Iterable[str]:
        """Yield all console lines for the stored report."""

        yield "[Startprüfung] Zusammenfassung der automatischen Kontrollen:"
        yield from self._iter_progress_messages()
        yield from self._iter_dependency_messages()
        yield from self._iter_self_test_messages()
        yield from self._iter_security_messages()
        yield from self._iter_color_audit_messages()
        yield from self._iter_diagnostics_messages()
        yield from self._iter_offline_messages()

    def render(self) -> str:
        """Return the console report as a single string."""

        return "\n".join(self.iter_lines())

    def print(self, stream: Optional[TextIO] = None) -> None:
        """Write all report lines to ``stream`` (defaults to ``sys.stdout``)."""

        if stream is None:
            import sys

            stream = sys.stdout
        for line in self.iter_lines():
            print(line, file=stream)

    # ------------------------------------------------------------------
    def _iter_progress_messages(self) -> Iterable[str]:
        for message in self.report.messages:
            yield f"  • {message}"
        if self.report.repaired_paths:
            repaired = ", ".join(str(path) for path in self.report.repaired_paths)
            yield f"  • Reparaturen: {repaired}"

    # ------------------------------------------------------------------
    def _iter_dependency_messages(self) -> Iterable[str]:
        if not self.report.dependency_messages:
            return
        yield "  • Paketinstallationen:"
        for description in self.report.dependency_messages:
            yield f"    - {description}"

    # ------------------------------------------------------------------
    def _iter_self_test_messages(self) -> Iterable[str]:
        if not self.report.self_tests:
            return
        yield "[Selbsttest] Ergebnisse:"
        for result in self.report.self_tests:
            status = "OK" if result.passed else "FEHLER"
            detail = f" – {result.details}" if result.details else ""
            yield f"  [{status}] {result.name}{detail}"
        if self.report.all_self_tests_passed():
            yield "[Selbsttest] Alle Prüfungen bestanden. Das Protokoll liegt unter logs/startup.log."
        else:
            yield "[Selbsttest] Mindestens eine Prüfung meldete Probleme. Details siehe logs/startup.log."

    # ------------------------------------------------------------------
    def _iter_security_messages(self) -> Iterable[str]:
        summary = self.report.security_summary
        if summary is None:
            return
        status_label = "OK" if summary.status == "ok" else "ACHTUNG"
        yield "[Datensicherheit] Manifest-Prüfung:"
        yield f"  [{status_label}] {summary.verified} Dateien kontrolliert, {len(summary.issues)} Abweichungen"
        for issue in summary.issues:
            yield f"    - Warnung: {issue}"
        for backup in summary.backups:
            yield f"    - Sicherung erstellt: {backup}"

    # ------------------------------------------------------------------
    def _iter_color_audit_messages(self) -> Iterable[str]:
        audit = self.report.color_audit
        if not audit:
            return
        overall = str(audit.get("overall_status", "unknown"))
        worst_ratio = self._parse_float(audit.get("worst_ratio", 0.0))
        label = "OK" if overall == "ok" else "ACHTUNG"
        yield "[Farbaudit] Zusammenfassung:"
        yield (
            "  "
            f"[{label}] Niedrigster Kontrast {worst_ratio:.2f}:1 – vollständiger Bericht: data/color_audit.json"
        )
        issues = list(audit.get("issues", []))
        recommendations = list(audit.get("recommendations", []))
        if issues:
            yield "  • Hinweise auf schwache Kontraste:"
            yield from self._iter_bullet_list(issues)
        if recommendations:
            yield "  • Tipps zur Verbesserung:"
            yield from self._iter_bullet_list(recommendations)

    # ------------------------------------------------------------------
    def _iter_diagnostics_messages(self) -> Iterable[str]:
        messages: List[str] = []
        if self.report.diagnostics_messages:
            messages.append("[Diagnose] Systemüberblick:")
            for line in self.report.diagnostics_messages:
                messages.append(f"  • {line}")
        if self.report.diagnostics_path:
            messages.append(f"[Diagnose] Vollständiger Bericht: {self.report.diagnostics_path}")
        if self.report.diagnostics_html_path:
            messages.append(f"[Diagnose] HTML-Überblick: {self.report.diagnostics_html_path}")
        return messages

    # ------------------------------------------------------------------
    def _iter_offline_messages(self) -> Iterable[str]:
        if not self.report.offline_mode_enabled:
            return
        yield "[Offline-Modus] Keine Paketnachinstallation möglich – Tool läuft mit Bordmitteln."
        for reason in self.report.offline_reasons:
            yield f"  • Hinweis: {reason}"
        if self.report.degraded_features:
            yield "  • Eingeschränkte Zusatzfunktionen:"
            for feature in self.report.degraded_features:
                yield f"    - {feature}"
        yield (
            "  • Sobald Internet verfügbar ist: 'python -m pip install -r requirements.txt' ausführen,"
            " um die Pakete nachzuladen."
        )

    # ------------------------------------------------------------------
    @staticmethod
    def _iter_bullet_list(entries: Sequence[str], prefix: str = "    - ") -> Iterable[str]:
        for entry in entries[:5]:
            yield f"{prefix}{entry}"
        remaining = len(entries) - 5
        if remaining > 0:
            yield f"    … {remaining} weitere Hinweise im Bericht"

    # ------------------------------------------------------------------
    @staticmethod
    def _parse_float(value) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0


__all__ = ["StartupReportPresenter"]
