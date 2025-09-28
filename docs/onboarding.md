# Schritt-für-Schritt-Onboarding

Dieses Dokument erklärt in einfacher Sprache (Fachbegriffe stehen in Klammern) den Einstieg.

## 1. Vorbereitung

1. Stelle sicher, dass Python 3.9 oder neuer installiert ist (`python --version`).
2. Klone das Repository oder lade es als ZIP.
3. Öffne ein Terminal (Eingabeaufforderung) im Projektordner.

## 2. Automatischer Start

Die Datei `bootstrap.sh` richtet alles ein und startet das Tool:

```bash
./bootstrap.sh
```

- Erstellt die virtuelle Umgebung (`.venv` = isolierte Python-Umgebung).
- Aktualisiert `pip` (Paketverwaltung) und installiert alle Pakete aus `requirements.txt`.
- Startet `python -m step_by_step`, das wiederum die Startroutine (Selbsttest + Diagnose) ausführt.

> Tipp: Unter Windows in Git Bash oder WSL ausführen. Alternativ:
>
> ```bash
> python -m venv .venv
> source .venv/bin/activate  # Windows: .venv\Scripts\activate
> python -m pip install -r requirements.txt
> python -m step_by_step
> ```

## 3. Desktop-Verknüpfung (Klick & Start)

Das Skript `packaging/install_desktop.sh` richtet Starter, Icon und Launcher automatisch ein:

```bash
bash packaging/install_desktop.sh
```

- Kopiert das Icon (`assets/step-by-step-icon.svg`) nach `~/.local/share/icons/hicolor/scalable/apps/`.
- Erstellt ein Starter-Skript unter `~/.local/bin/step-by-step-launcher`, das `bootstrap.sh` im Projekt aufruft (inkl. Abhängigkeitsprüfung).
- Schreibt einen personalisierten Desktop-Eintrag nach `~/.local/share/applications/step-by-step.desktop`.
- Aktualisiert nach Möglichkeit den Desktop- und Icon-Cache (`update-desktop-database`, `gtk-update-icon-cache`).

Danach erscheint "STEP-BY-STEP" im App-Menü und löst alle Abhängigkeiten beim Klick automatisch auf.

## 4. Erstes UI-Wochenende

Beim ersten Start erzeugt das Programm automatisch:

- `data/settings.json` (Einstellungen)
- `data/todo_items.json` (Aufgaben)
- `data/playlists.json` (Playlist)
- `data/archive.db` (Datenbank)
- `data/security_manifest.json` (Sicherheits-Manifest)
- `data/diagnostics_report.json` + `.html` (Systemdiagnose)

Das Dashboard zeigt oben Statusmeldungen:

- **Selbsttest:** Ergebnis der Startprüfung.
- **Datensicherheit:** Manifest-Status, Backup-Hinweise.
- **Farbaudit:** Prüft Kontrastwerte aller Themes (Designs).
- **Diagnose:** Kurzübersicht über Systemprüfung.

## 5. Bedienung in Kürze

- **Notizen:** Links oben, speichert automatisch bei Fokuswechsel und über `Strg+S`.
- **ToDo-Liste:** Rechts oben, Status per Enter/Leertaste toggeln (umschalten).
- **Playlist:** Spielt WAV-Dateien ab, Lautstärke-Regler nutzt `audioop.mul` (Sample-Skalierung).
  - Unter Linux fehlt oft das Zusatzpaket `simpleaudio` (Audiotreiber für Python). Die Diagnose meldet das als Hinweis.
  - Lösung: `python -m pip install --user simpleaudio==1.0.4` ausführen oder in der Paketverwaltung das gleichnamige Paket installieren.
  - Alternativ über den Systemplayer abspielen: Rechtsklick auf den Titel → "Datei im Ordner öffnen" → doppelklicken.
- **Info-Center:** Mittlere Spalte, jetzt mit Scroll-Container (überall scrollen möglich) und Tabs für Legende, Struktur, Schnelllinks, Schrift, Kontrast, Palette, Farbaudit, Release, Sicherheit, Diagnose.
- **Startprotokoll:** Zeigt `logs/startup.log`, Suche per Tastatur möglich.

## 6. Problemlösung

| Problem | Lösung (mit Befehl) |
| --- | --- |
| Virtuelle Umgebung defekt | `rm -rf .venv && ./bootstrap.sh` |
| Pakete fehlen | `.venv/bin/python -m pip install -r requirements.txt` |
| Audio ohne Ton | `python -m pip install --upgrade simpleaudio==1.0.4` |
| Beschädigte Einstellungen | `rm data/settings.json && python -m step_by_step --headless` |
| Diagnose frisch erzeugen | `python -m step_by_step --headless` |
| CI lokal prüfen | `ruff check . && pytest && mypy step_by_step --ignore-missing-imports` |

Weitere Details siehe `README.md` und `info.txt`.
