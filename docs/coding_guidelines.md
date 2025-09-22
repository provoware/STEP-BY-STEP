# STEP-BY-STEP Coding Guidelines

- Verwende sprechende Namen (aussagekräftige Bezeichner) und schreibe Docstrings.
- Trenne Logik strikt nach Verantwortlichkeiten: `core` für Infrastruktur,
  `ui` für Darstellung, `modules` für Fachlogik.
- Schreibe Funktionen klein mit Unterstrich (`snake_case`).
- Führe vor jedem Commit `python -m compileall step_by_step` aus, um Syntaxfehler
  zu vermeiden.
- Nutze Typhinweise (Type Hints) für klarere Schnittstellen.
- Prüfe Datenzugriffe zentral (z.B. über Manager-Klassen wie `PlaylistManager`,
  `DatabaseModule`, `ReleaseChecklist`), damit die GUI nur fertige Services
  anspricht.
- Nutze das Logging-Framework (`get_logger`) für jede Aktion, damit sich das
  Startprotokoll gezielt durchsuchen lässt.
- Barrierefreie Texte schreiben: Fachbegriffe kurz erläutern, Fokusmeldungen
  aktualisieren und sichtbare Kontraste verwenden.
- Dateien im Ordner `data/` behalten lesbare JSON-Struktur (UTF-8, `indent=2`).
- Bei Änderungen an Dateien aus `SENSITIVE_FILES` (siehe `core/security.py`)
  nach dem Speichern das Sicherheitsmanifest über die Startroutine oder den
  `SecurityManager` aktualisieren; so bleiben Prüfsummen und Backups stimmig.
- Für neue Farbschemata immer die Palette über `build_palette_panel` testen und
  sicherstellen, dass Hintergrund/Text mindestens den WCAG-Kontrast 4,5:1
  erfüllen.
- Palette-Definitionen zentral in `step_by_step/core/themes.py` pflegen und nach
  Änderungen den Farbaudit (Startroutine oder `ColorAuditor`) erneut laufen
  lassen.
- Neue Module liefern Docstrings am Kopf und exportieren ihre wichtigsten
  Klassen/Funktionen über `__all__`.
