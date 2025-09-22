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
- **Schnelllinks:** Info-Center mit Buttons zum Öffnen von `todo.txt`,
  `data/settings.json` und für den Headless-Selbsttest.
- **Autosave:** Notizen werden beim Fokusverlust und zusätzlich in Intervallen
  (Standard 10 Minuten) gespeichert.
- **Info-Center:** Innerhalb des 3×3-Rasters zeigt ein Notebook eine Legende zum
  Toolumfang, ein textuelles Mockup (Entwurfsskizze) und den Ordner-/Dateibaum
  des Projekts an.

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
- Die Aufgabenliste zeigt Fälligkeitsdaten im Format `• Titel (bis YYYY-MM-DD)`
  und markiert erledigte Aufgaben mit einem Häkchen.
- Screenreader-Hinweise erklären Tastaturkürzel (Tab, Enter, Pfeiltasten) direkt
  an den jeweiligen Listen.
