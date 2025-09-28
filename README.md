# STEP-BY-STEP

Ein modulares Dashboard-Tool mit automatischer Startroutine. Das Projekt bündelt
die Bereiche Datenbank-Archiv, Audioplaylist und Aufgabenverwaltung in einer
barrierearmen Oberfläche. Die Startroutine erledigt nun komplett autonom die
Anlage einer virtuellen Umgebung, installiert Abhängigkeiten, führt
Selbsttests aus und liefert detailiertes Feedback über ein erweitertes
Logging.

## Schnellstart (Klick & Start)

```bash
./bootstrap.sh
```

Der Befehl erstellt bei Bedarf die virtuelle Umgebung `.venv`, aktualisiert
`pip`, installiert alle Pakete aus `requirements.txt` (Produktionsabhängigkeiten
für den täglichen Einsatz) und startet anschließend die barrierearme Oberfläche
über den neuen Konsolen-Einstiegspunkt `python -m step_by_step`. Die Konsole
zeigt danach eine zusammengefasste Auswertung (Security-Status, Farbaudit,
Selbsttests, Systemdiagnose) inklusive Offline-Hinweisen. Alternativ lässt sich
der Start jederzeit mit `python -m step_by_step` durchführen (zuvor manuell
`.venv` aktivieren).

**Entwicklungs-Werkzeuge nach Bedarf aktivieren:** Wer zusätzlich Prüf- und
Entwicklungs-Tools (Tests, Linter, Typchecker) benötigt, setzt vor dem Aufruf
eine Umgebungsvariable (Schalter für den Startprozess) und wiederholt den
Bootstrap-Befehl:

```bash
STEP_BY_STEP_INSTALL_DEV=1 ./bootstrap.sh
```

Dadurch installiert das Skript automatisch auch alle Pakete aus
`requirements-dev.txt`. Ohne den Schalter bleiben diese Werkzeuge außen vor,
sodass Endanwender*innen nur die wirklich benötigten Bibliotheken erhalten.
Beim allerersten Start legt die Routine sämtliche Primärdaten-Dateien neu an
(`data/settings.json`, `data/todo_items.json`, `data/archive.db` usw.), damit
das Git-Repository keine echten Nutzerdaten enthält.
Für einen Diagnoselauf ohne Fenster:

```bash
python -m step_by_step --headless
```

## Zusätzliche Installationshinweise für Neulinge

- **Nur Produktionspakete installieren:**

  ```bash
  python -m pip install -r requirements.txt
  ```

- **Entwicklungswerkzeuge (Tests, Linting, Typprüfung) nachrüsten:**

  ```bash
  python -m pip install -r requirements-dev.txt
  ```

- **Variable deaktivieren:** Um die Developer-Pakete wieder abzuschalten,
  genügt es, den Bootstrap-Befehl ohne gesetzte Umgebungsvariable aufzurufen.
  Die Programme bleiben installiert, können aber bei Bedarf mit `python -m pip`
  wieder entfernt werden (`python -m pip uninstall paketname`).

- **Offline starten:** Wenn kein Internet verfügbar ist, startet das Tool im
  Offline-Modus weiter. Eine spätere Nachinstallation gelingt mit:

  ```bash
  python -m pip install -r requirements.txt
  ```

  Optional kann für die Audiowiedergabe (simpleaudio) dieser Befehl ergänzt
  werden, sobald wieder Internet vorhanden ist:

  ```bash
  python -m pip install simpleaudio==1.0.4
  ```

Eine ausführliche Schritt-für-Schritt-Anleitung (Onboarding & Troubleshooting)
findet sich in `docs/onboarding.md`. Für Desktop-Umgebungen liegt eine
Starter-Verknüpfung unter `packaging/step-by-step.desktop` und das Icon in
`assets/step-by-step-icon.svg` bereit.

## Standardkonformes Packaging (PEP-517)

Mit der neuen `pyproject.toml` lässt sich das Tool wie ein reguläres Paket
bauen und installieren. Alle Befehle sind vollständig aufgeführt:

```bash
python -m pip install --upgrade build
python -m build
```

Der Befehl erzeugt unter `dist/` ein Wheel-Paket. Dieses lässt sich lokal
installieren:

```bash
python -m pip install dist/step_by_step-0.2.0-py3-none-any.whl
```

Ein anschließender Start funktioniert über:

```bash
python -m step_by_step
```

Für Entwickler*innen steht zusätzlich die optionale Abhängigkeit
`step-by-step[dev]` bereit, welche dieselben Pakete wie `requirements-dev.txt`
enthält.

## Wesentliche Merkmale

- **Autonome Startroutine:** Erstellt fehlende Dateien, prüft Pakete, führt
  Selbsttests aus und startet sich bei Bedarf innerhalb der virtuellen
  Umgebung neu.
- **Primärdatenfreie Auslieferung:** Das Repository enthält nur leere
  Platzhalterordner (`data/`, `data/backups/`, `data/converted_audio/`,
  `data/exports/`). Alle JSON-/Datenbankdateien erzeugt die Startroutine beim
  ersten Start automatisch mit sauberen Standardeinträgen.
- **Detailiertes Logging:** Zentraler Logger mit drehenden Dateien (`logs/tool.log`)
  sowie einer separaten Startprotokollierung (`logs/startup.log`), die automatisch
  auf die letzten 2 000 Zeilen gekürzt wird.
- **Automatische Selbsttests:** Beim Start wird der komplette Codebaum mit
  `compileall` (Syntaxprüfung) getestet und die `data/settings.json` wird auf
  Vollständigkeit und barrierefreie Standardeinstellungen geprüft.
- **Robuste Einstellungs-Validierung:** Ein gemeinsamer Validator gleicht
  `data/settings.json` mit empfohlenen Grenzwerten ab, korrigiert ungültige
  Werte (z.B. Schriftgröße, Lautstärke, Autospeicher-Intervall) und protokolliert
  jede automatische Anpassung verständlich.
- **Systemdiagnose (Pro-Report):** Der Startlauf prüft Python-Version,
  virtuelle Umgebung, Pfad-Rechte und benötigte Pakete. Zusätzlich gleicht er
  installierte Paketversionen mit den Mindestanforderungen aus
  `requirements.txt` ab. Alle Details landen in `data/diagnostics_report.json`
  sowie in einer barrierefreundlichen HTML-Ansicht
  (`data/diagnostics_report.html`), während das Dashboard eine kurze,
  leicht verständliche Zusammenfassung anzeigt.
- **Barrierearme Oberfläche:** Umschaltbare High-Contrast-, helle und dunkle
  Themes, ein gut sichtbarer Zoom-Regler (80–160 %) samt Statusfeedback sowie
  tastaturfreundliche Aufgaben-, Notiz- und Playlist-Bereiche sorgen für
  sofort nutzbare Bedienung.
- **Datensicherheits-Manifest:** Beim Start wird ein Checksummen-Manifest für
  zentrale JSON/TXT-Dateien verifiziert. Abweichungen erzeugen automatische
  Backups unter `data/backups/`, Größenabweichungen werden hervorgehoben und
  alte Sicherungen nach fünf Generationen aufgeräumt. Zusätzlich prüft der
  Startlauf automatisch, ob die jüngsten Backups zu den Manifest-Prüfsummen
  passen und meldet konkrete Restore-Hinweise.
- **Automatischer Farbaudit:** Alle Farbschemata werden gegen die WCAG-Grenzwerte
  geprüft. Die Auswertung landet im Dashboard und in `data/color_audit.json` –
  inklusive konkreter Tipps, wie sich auffällige Farben nachschärfen lassen.
- **Startprotokoll-Panel:** Ein eigener Bereich durchsucht `logs/startup.log`,
  kopiert Zeilen in die Zwischenablage und bietet Hilfetexte für Tastaturnutzung.

## Ressourcenüberblick

- `json-and-more.info.txt` dokumentiert alle Standarddateien und ersetzt die
  frühere ZIP-Datei.
- `data/` enthält alle persistenten Informationen (Notizen, Aufgaben,
  Playlists, Statistiken, Einstellungen). Im Git-Repository liegen hier nur
  `.gitkeep`-Platzhalter – die tatsächlichen Dateien entstehen beim ersten
  Programmstart.
- `data/archive.db` speichert das Archiv als SQLite-Datenbank (leichte
  Datenbank) und wird beim ersten Start automatisch angelegt oder aus der
  bisherigen `data/archive.json` befüllt.
- `logs/` speichert Start- und Laufzeitprotokolle für eine einfache Analyse.
- `data/security_manifest.json` dokumentiert nach dem ersten Start die letzten
  Checksummen-Prüfungen aller wichtigen Dateien und speichert
  Restore-Checks für jede Sicherung.
- `data/color_audit.json` hält die Ergebnisse der automatischen
  Farbkontrast-Prüfung inklusive Empfehlungen fest.
- `data/diagnostics_report.json` speichert die Systemdiagnose (Python,
  Pakete, Pfade) für Support und Fehlersuche.
- `data/diagnostics_report.html` stellt dieselben Informationen als
  kontraststarke HTML-Ansicht bereit (ideal für Support-Weitergabe).
- `docs/coding_guidelines.md` fasst Code-Standards zusammen.

## Weitere Laienfreundliche Tipps

- **Virtuelle Umgebung aufräumen:** (Entfernt den isolierten Python-Ordner)

  ```bash
  rm -rf .venv
  ```

  Danach kann mit `./bootstrap.sh` eine frische Umgebung erstellt werden.

- **Konfigurationsdateien sichern:** (Kopie der wichtigsten JSON-Dateien)

  ```bash
  mkdir -p backups-manual
  cp data/settings.json backups-manual/settings.json
  cp data/todo_items.json backups-manual/todo_items.json
  ```

- **Audiomodul testen:** (Kurzer Check ohne Oberfläche)

  ```bash
  python -m step_by_step --headless
  python - <<'PY'
from step_by_step.modules.audio import PlaylistManager
print("Playlist enthält", len(PlaylistManager().load_tracks()), "Einträge")
PY
  ```

- **Diagnose teilen:** (HTML-Bericht für Support speichern)

  ```bash
  python -m step_by_step --headless
  xdg-open data/diagnostics_report.html
  ```

## Audio & Playlist

- WAV-Dateien (unkomprimiertes Audio) werden per `simpleaudio` abgespielt.
- Die Lautstärke lässt sich per Regler (0–100 %) einstellen; das Tool merkt sich
  die letzte Einstellung. Der Regler kann komplett mit der Tastatur bedient
  werden und nutzt denselben Kontraststil wie der Schriftgrößenregler.
- Fehlende Abhängigkeiten meldet das Tool direkt und schlagen auch im Log auf.
- Die Playlist ist duplikatfrei und sortiert die Titel automatisch alphabetisch.
- Zusätzlich stehen Buttons zum Format-Check und zur Normalisierung bereit: das
  Tool liest Kanäle/Bitbreite und erzeugt bei Bedarf eine kompatible 16-Bit-WAV-
  Kopie unter `data/converted_audio/`.
- Hinweis: Auf Linux-Systemen wird `simpleaudio` nicht automatisch installiert,
  da systemweite ALSA-Header benötigt werden (`libasound2-dev`). Bei Bedarf
  manuell per `python -m pip install simpleaudio` nachinstallieren.

## Datenbank & Aufgaben

- Das Archiv-Modul (`step_by_step/modules/database/module.py`) arbeitet mit
  SQLite (leichte Datenbank) und bietet Such-/Präfixfilter sowie das Entfernen
  einzelner Einträge ohne Duplikate.
- Über Schnelllinks können CSV- und JSON-Exporte erstellt werden (`data/exports/`).
- Der neue Daten-Tab im Info-Center fasst die letzten Einträge, die Gesamtzahl
  der Datensätze und die häufigsten Anfangsbuchstaben zusammen und erklärt
  dabei zentrale Begriffe (Eintrag = Datensatz, SQLite = leichte Datenbank).
- Die Aufgabenliste zeigt Fälligkeitsdaten im Format `⏳/✔ Titel (bis DD.MM.YYYY)`
  und erlaubt das Umschalten per Tastatur (Enter/Leertaste) oder Button. Der
  aktuelle Status wird im Dashboard zusammen mit dem Sitzungszähler angezeigt.
- Screenreader-Hinweise erklären Tastaturkürzel (Tab, Enter, Pfeiltasten) direkt
  an den jeweiligen Listen.

## Design- und Barrierefreiheits-Hilfen

- **Schriftgrößen-Kompass:** Das Info-Center listet Empfehlungen für alle
  Module (Notizen, ToDo, Playlist, Info-Center, Audiosteuerung) und zeigt den
  aktuellen Zoom-Wert in Prozent an.
- **Kontrast-Checker, Palette & Farbaudit:** Ein integriertes Werkzeug prüft zwei
  beliebige Farbwerte auf WCAG-Konformität (4,5:1 für Fließtext, 3,0:1 für große
  Schrift) und hilft beim Feintuning eigener Themes. Zusätzlich sorgt ein
  automatischer Farbaudit dafür, dass alle vordefinierten Paletten beim Start
  geprüft werden – inklusive Tabelle der niedrigsten Kontraste und Hinweisliste.
- **Live-Statusmeldungen:** Aktionen wie „Aufgabe erledigt“, „Notiz gespeichert“
  oder „Farbschema aktiviert“ werden im Kopfbereich angezeigt und kehren nach
  kurzer Zeit automatisch zur Übersicht (Sitzungen + offene Aufgaben) zurück.

## Qualitätssicherung & Releaseplanung

- `data/selftest_report.json` fasst jeden Startlauf zusammen (Ergebnisse der
  Selbsttests, reparierte Dateien, installierte Abhängigkeiten) und versorgt
  die Oberfläche mit einer Ampel-Anzeige.
- `data/release_checklist.json` dokumentiert erledigte und offene
  Release-Schritte; die Inhalte erscheinen auch im Info-Center. Neue Punkte
  decken die Manifest-Prüfung und die finale Freigabe der Accessible-Farbprofile
  ab.
- `data/security_manifest.json` plus Sicherungsordner `data/backups/` zeigen den
  Verlauf der Datensicherheitsprüfungen samt angelegter Backups und den
  automatischen Restore-Abgleich.
- `data/color_audit.json` listet die geprüften Farbschemata mit niedrigsten
  Kontrasten, Hinweisen und ergänzenden Empfehlungen.
- `data/diagnostics_report.json` dokumentiert die zuletzt gesammelten
  Diagnosewerte und wird automatisch beim Start aktualisiert.
- `Fortschritt.txt` dokumentiert den Ausbauzustand (aktuell 100 %) und zeigt die
  letzten Meilensteine inklusive finaler Abschlussprüfung.
- `todo.txt` wird direkt aus der Oberfläche gepflegt – erledigte Punkte werden
  automatisch markiert, neue Aufgaben lassen sich weiterhin per Textdatei
  ergänzen. Nach dem Release bleiben nur noch optionale Ideen erhalten.
- `docs/post_release_ideas.md` sammelt strukturierte Vorschläge für den
  Folgeausbau. Die Stichpunkte verwenden einfache Sprache und erklären
  Fachbegriffe direkt in Klammern.
