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
- Neue Module liefern Docstrings am Kopf und exportieren ihre wichtigsten
  Klassen/Funktionen über `__all__`.
