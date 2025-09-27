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
- Datensicherheits-Manifest mit automatischen Backups (`data/security_manifest.json`
  + `data/backups/`) sowie sichtbarem Status im Dashboard.
- Accessible-Farbpalette mit WCAG-konformen Kontrasten und zusätzlicher
  Paletten-Übersicht im Info-Center.
- Automatischer Farbaudit, der alle Themes beim Start prüft und einen Bericht in
  `data/color_audit.json` sowie im Info-Center bereitstellt.
- Abschlussprüfung dokumentiert: End-to-End-Testlauf, Freigabe des Bedienhandbuchs
  und aktualisierte Hinweise zu Wiederherstellung und Support.
- Wiederherstellungs-Check automatisiert – jeder Lauf prüft, ob die jüngsten
  Sicherungen aus `data/backups/` zu den Manifest-Prüfsummen passen und meldet
  verständliche Tipps bei Abweichungen.
- Farbaudit ergänzt nun konkrete Handlungsempfehlungen für Farben mit zu niedrigem
  Kontrast, die direkt im Info-Center angezeigt werden.
- Primärdatenfreie Auslieferung: Das Git-Repository enthält nur leere Datenordner;
  beim ersten Start erzeugt die Startroutine sämtliche JSON-/Datenbankdateien.

## Offen ⏳

- Optionale Kür: weitere Audioanalyse (z.B. Wellenform-Vorschau) und erweiterte
  Screenreader-Ausgabe.
- Erweiterte Monitoring-Ideen (z.B. wöchentlicher Sicherungsbericht per E-Mail)
  nach dem Release einplanen.

## Testempfehlungen

1. `python start_tool.py --headless` ausführen und prüfen, dass alle Tests
   „OK“ melden.
2. GUI starten und im Playlist-Bereich eine Datei markieren → „Format prüfen“
   sowie „Als WAV normalisieren“ testen.
3. Im Info-Center auf „Archiv als CSV/JSON“ klicken und die erzeugten Dateien in
   `data/exports/` kontrollieren.
4. Im Info-Center die Tabs „Palette“, „Farbaudit“ und „Sicherheit“ prüfen:
   Kontraste müssen mindestens 4,5:1 erreichen, das Manifest darf keine
   Auffälligkeiten melden und der Farbaudit sollte keine Warnungen enthalten.
5. Im Bereich „Startprotokoll“ nach Begriffen wie „installiert“ oder „Fehler"
   suchen, um die Filterung zu validieren.

Alle Schritte schreiben detaillierte Logs in `logs/tool.log` und
`logs/startup.log` und können somit jederzeit nachvollzogen werden.

