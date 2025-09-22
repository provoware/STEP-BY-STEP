# STEP-BY-STEP

Ein modulares Dashboard-Tool mit automatischer Startroutine. Das Projekt bündelt
die Bereiche Datenbank-Archiv, Audioplaylist und Aufgabenverwaltung in einer
barrierearmen Oberfläche. Die Startroutine erledigt nun komplett autonom die
Anlage einer virtuellen Umgebung, installiert Abhängigkeiten und liefert
detailiertes Feedback über ein erweitertes Logging.

## Schnellstart (Klick & Start)

```bash
python start_tool.py
```

Der Befehl erstellt bei Bedarf die virtuelle Umgebung `.venv`, installiert alle
Pakete aus `requirements.txt`, protokolliert jeden Schritt unter `logs/` und
startet anschließend die barrierearme Oberfläche. Für einen Diagnoselauf ohne
Fenster:

```bash
python start_tool.py --headless
```

## Wesentliche Merkmale

- **Autonome Startroutine:** Erstellt fehlende Dateien, prüft Pakete und
  startet sich bei Bedarf innerhalb der virtuellen Umgebung neu.
- **Detailiertes Logging:** Zentraler Logger mit drehenden Dateien (`logs/tool.log`)
  sowie einer separaten Startprotokollierung (`logs/startup.log`).
- **Hoher Kontrast:** Die Oberfläche nutzt einen High-Contrast-Stil für beste
  Lesbarkeit (z.B. dunkler Hintergrund mit gelbem Akzent) und passt Buttons,
  Listen und Notizfelder automatisch an.
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
