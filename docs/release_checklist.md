# Release-Checkliste

Diese Übersicht ergänzt die automatische `data/release_checklist.json` und
listet alle Schritte, die vor dem finalen Release erledigt wurden oder noch
ausstehen. Jeder Punkt ist zusätzlich direkt im Tool sichtbar (Info-Center →
Release-Register).

## Erledigt ✅

- Autonomer Start inklusive virtueller Umgebung, Paketinstallation und
  Selbsttests.
- Audioformat-Prüfung sowie Normalisierung auf 16-Bit-WAV für problematische
  Dateien (Ablage unter `data/converted_audio/`).
- Archiv-Export als CSV **und** JSON mit direktem Schnelllink in der
  Oberfläche (`data/exports/`).
- Suchbare Ansicht für `logs/startup.log` inklusive Kopierfunktion und
  Fokus-Hilfen.
- Dokumentation der Coding-Guidelines und des Release-Prozesses (README,
  info.txt, json-and-more.info.txt).

## Offen ⏳

- Abschlussprüfung (End-to-End-Test, Bedienhandbuch final freigeben).
- Optionale Kür: weitere Audioanalyse (z.B. Wellenform-Vorschau) und erweiterte
  Screenreader-Ausgabe.

## Testempfehlungen

1. `python start_tool.py --headless` ausführen und prüfen, dass alle Tests
   „OK“ melden.
2. GUI starten und im Playlist-Bereich eine Datei markieren → „Format prüfen“
   sowie „Als WAV normalisieren“ testen.
3. Im Info-Center auf „Archiv als CSV/JSON“ klicken und die erzeugten Dateien in
   `data/exports/` kontrollieren.
4. Im Bereich „Startprotokoll“ nach Begriffen wie „installiert“ oder „Fehler"
   suchen, um die Filterung zu validieren.

Alle Schritte schreiben detaillierte Logs in `logs/tool.log` und
`logs/startup.log` und können somit jederzeit nachvollzogen werden.

