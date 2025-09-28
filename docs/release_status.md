# Release-Status (Stand: aktueller Arbeitslauf)

## Testüberblick
- `ruff check .` – bestanden.
- `pytest` – bestanden (5 Tests).
- `mypy step_by_step --ignore-missing-imports` – fehlgeschlagen (114 Fehler, v. a. in UI-/Diagnose-Modulen und Hilfsklassen).

## Automatischer Start (Headless)
- Startroutine läuft durch, richtet virtuelle Umgebung ein und erstellt Backups.
- Mehrere Sicherheitswarnungen wegen fehlender Basissicherungen (settings.json, todo_items.json, playlists.json, archive.json, usage_stats.json, persistent_notes.txt, archive.db).
- Diagnose meldet weiterhin optionales Paket `simpleaudio` als fehlend auf Linux.

## Offene Punkte für den Release-Abschluss
1. Typfehler (`mypy`) in UI-, Diagnose- und Sicherheitsmodulen beheben oder begründet ignorieren.
2. Basissicherungen für Kern-Dateien vorbereiten, damit die Sicherheitsprüfung ohne Warnungen verläuft.
3. Umgang mit fehlendem `simpleaudio` (Audio-Wiedergabe) dokumentieren oder Abhängigkeit anpassen.
4. Release-Hinweise/Changelog für Anwender*innen fertigstellen.

## Empfohlene nächste Schritte
- Typdefekte schrittweise korrigieren (Start bei `step_by_step/ui/main_window.py` und `step_by_step/core/diagnostics.py`).
- Dummy-Backups initialisieren oder Manifest-Logik anpassen, damit produktive Erstdurchläufe keine Fehlalarme auslösen.
- Audio-Dokumentation ergänzen: Hinweis auf OS-Einschränkungen oder alternativen Wiedergabeweg.
- Abschließende Anwender-Dokumentation aktualisieren und Tests erneut laufen lassen.
