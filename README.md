# STEP-BY-STEP

Ein modulares Dashboard-Tool mit automatischer Startroutine. Das Projekt bündelt
die Bereiche Datenbank-Archiv, Audioplaylist und Aufgabenverwaltung in einer
barrierearmen Oberfläche. Die Startroutine erledigt nun komplett autonom die
Anlage einer virtuellen Umgebung, installiert Abhängigkeiten, führt
Selbsttests aus und liefert detailiertes Feedback über ein erweitertes
Logging.

## Schnellstart (Klick & Start)

```bash
python start_tool.py
```

Der Befehl erstellt bei Bedarf die virtuelle Umgebung `.venv`, installiert alle
Pakete aus `requirements.txt`, prüft den Code per Selbsttest (Syntax-Check
und Einstellungs-Validierung), protokolliert jeden Schritt unter `logs/` und
startet anschließend die barrierearme Oberfläche. Für einen Diagnoselauf ohne
Fenster:

```bash
python start_tool.py --headless
```

## Wesentliche Merkmale

- **Autonome Startroutine:** Erstellt fehlende Dateien, prüft Pakete, führt
  Selbsttests aus und startet sich bei Bedarf innerhalb der virtuellen
  Umgebung neu.
- **Detailiertes Logging:** Zentraler Logger mit drehenden Dateien (`logs/tool.log`)
  sowie einer separaten Startprotokollierung (`logs/startup.log`).
- **Automatische Selbsttests:** Beim Start wird der komplette Codebaum mit
  `compileall` (Syntaxprüfung) getestet und die `data/settings.json` wird auf
  Vollständigkeit und barrierefreie Standardeinstellungen geprüft.
- **Hoher Kontrast:** Die Oberfläche nutzt einen High-Contrast-Stil für beste
  Lesbarkeit (z.B. dunkler Hintergrund mit gelbem Akzent) und passt Buttons,
  Listen und Notizfelder automatisch an.
- **Zoom-Regler:** Ein gut sichtbarer Schriftgrößenregler mit Prozentanzeige
  erlaubt stufenloses Vergrößern (Zoom) zwischen 80 % und 160 % inklusive
  Reset-Knopf.
- **Standard-Schriftgröße 120 %:** Die Einstellungen setzen ab sofort dauerhaft
  eine 1,2er Skalierung, damit Texte auf Anhieb besser lesbar sind.
- **Audioplayer:** Playlistbereich mit Abspiel- und Stopp-Taste, Lautstärkeregler
  und Hinweisen für Screenreader. Unterstützt aktuell WAV-Dateien über
  `simpleaudio`.
- **Status-Feedback:** Fokussierte Elemente (z.B. Notizfeld, Listen, Regler)
  melden sich im Statusfeld und erhalten sichtbare Fokusrahmen für bessere
  Orientierung mit Tastatur oder Screenreader.
- **Farbprofile:** Umschaltbarer Modus im Header (High Contrast, Hell, Dunkel)
  inklusive direktem Feedback und automatischer Aktualisierung aller Bereiche.
- **Aufgabenverwaltung im Dashboard:** Aufgaben lassen sich per Enter, Leertaste
  oder Button direkt abhaken; die Liste zeigt offene und erledigte Punkte mit
  klaren Symbolen und aktualisiert den Statuszähler im Kopfbereich.
- **Selbsttest-Monitoring:** Ein Live-Hinweis im Header zeigt den letzten
  Selbsttest mit Datum und Ergebnis (Bestandene/Nicht bestandene Tests) an –
  die Startroutine schreibt die Daten in `data/selftest_report.json`.
- **Schnelllinks:** Info-Center mit Buttons zum Öffnen von `todo.txt`,
  `data/settings.json` und für den Headless-Selbsttest.
- **Autosave:** Notizen werden beim Fokusverlust und zusätzlich in Intervallen
  (Standard 10 Minuten) gespeichert.
- **Info-Center:** Innerhalb des 3×3-Rasters liefert ein Notebook eine Legende,
  ein textuelles Mockup, den Ordner-/Dateibaum sowie neue Register für
  Schriftgrößen-Empfehlungen und einen Kontrast-Checker zur Prüfung eigener
  Farbprofile.

## Ressourcenüberblick

- `json-and-more.info.txt` dokumentiert alle Standarddateien und ersetzt die
  frühere ZIP-Datei.
- `data/` enthält alle persistenten Informationen (Notizen, Aufgaben, Playlists,
  Statistiken, Einstellungen).
- `logs/` speichert Start- und Laufzeitprotokolle für eine einfache Analyse.
- `docs/coding_guidelines.md` fasst Code-Standards zusammen.

## Audio & Playlist

- WAV-Dateien (unkomprimiertes Audio) werden per `simpleaudio` abgespielt.
- Die Lautstärke lässt sich per Regler (0–100 %) einstellen; das Tool merkt sich
  die letzte Einstellung. Der Regler kann komplett mit der Tastatur bedient
  werden und nutzt denselben Kontraststil wie der Schriftgrößenregler.
- Fehlende Abhängigkeiten meldet das Tool direkt und schlagen auch im Log auf.
- Die Playlist ist duplikatfrei und sortiert die Titel automatisch alphabetisch.

## Datenbank & Aufgaben

- Das Archiv-Modul (`step_by_step/modules/database/module.py`) bietet jetzt
  Such- und Präfixfilter sowie das Entfernen einzelner Einträge.
- Die Aufgabenliste zeigt Fälligkeitsdaten im Format `⏳/✔ Titel (bis DD.MM.YYYY)`
  und erlaubt das Umschalten per Tastatur (Enter/Leertaste) oder Button. Der
  aktuelle Status wird im Dashboard zusammen mit dem Sitzungszähler angezeigt.
- Screenreader-Hinweise erklären Tastaturkürzel (Tab, Enter, Pfeiltasten) direkt
  an den jeweiligen Listen.

## Design- und Barrierefreiheits-Hilfen

- **Schriftgrößen-Kompass:** Das Info-Center listet Empfehlungen für alle
  Module (Notizen, ToDo, Playlist, Info-Center, Audiosteuerung) und zeigt den
  aktuellen Zoom-Wert in Prozent an.
- **Kontrast-Checker:** Ein integriertes Werkzeug prüft zwei beliebige
  Farbwerte auf WCAG-Konformität (4,5:1 für Fließtext, 3,0:1 für große Schrift)
  und hilft beim Feintuning eigener Themes.
- **Live-Statusmeldungen:** Aktionen wie „Aufgabe erledigt“, „Notiz gespeichert“
  oder „Farbschema aktiviert“ werden im Kopfbereich angezeigt und kehren nach
  kurzer Zeit automatisch zur Übersicht (Sitzungen + offene Aufgaben) zurück.

## Qualitätssicherung & Releaseplanung

- `data/selftest_report.json` fasst jeden Startlauf zusammen (Ergebnisse der
  Selbsttests, reparierte Dateien, installierte Abhängigkeiten) und versorgt
  die Oberfläche mit einer Ampel-Anzeige.
- `Fortschritt.txt` dokumentiert den Ausbauzustand (aktuell 74 %) und zeigt die
  letzten Meilensteine sowie anstehende Aufgaben (z.B. Audio-Konvertierung,
  Datenbank-Export, Release-Checkliste).
- `todo.txt` wird direkt aus der Oberfläche gepflegt – erledigte Punkte werden
  automatisch markiert, neue Aufgaben lassen sich weiterhin per Textdatei
  ergänzen.
- Für den finalen Release fehlen noch: Audioformat-Prüfung/Konvertierung,
  erweiterter Datenbank-Export, durchsuchenbares Startprotokoll und der Abschluss
  der Release-Checkliste (siehe `todo.txt`).
