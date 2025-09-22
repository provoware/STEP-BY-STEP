# STEP-BY-STEP Coding Guidelines

- Verwende sprechende Namen (aussagekräftige Bezeichner) und schreibe Docstrings.
- Trenne Logik strikt nach Verantwortlichkeiten: `core` für Infrastruktur,
  `ui` für Darstellung, `modules` für Fachlogik.
- Schreibe Funktionen klein mit Unterstrich (`snake_case`).
- Führe vor jedem Commit `python -m compileall step_by_step` aus, um Syntaxfehler
  zu vermeiden.
- Nutze Typhinweise (Type Hints) für klarere Schnittstellen.
