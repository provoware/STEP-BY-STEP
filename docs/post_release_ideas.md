# Nach-Release-Ideen

Diese Sammlung hilft dabei, nach dem aktuellen Release strukturierte Verbesserungen zu planen. Die Punkte sind so formuliert, dass sie ohne technische Vorkenntnisse (Laien = Menschen ohne Fachwissen) nachvollzogen werden können. Fachbegriffe stehen in Klammern und werden kurz erklärt.

## Audio und Medien
- **Audio-Vorschau mit Zeitleiste**: Eine grafische Anzeige (Timeline = Zeitstrahl) zeigt Restlaufzeit und Position des Titels. Ergänzt ein Direkt-Springen über kleine Markierungen.
- **Streaming-Unterstützung**: Optionales Laden von Web-Radio-Streams, inklusive Zwischenspeicher (Buffer = Zwischenablage für Daten) für ruckelfreie Wiedergabe.
- **Intelligente Lautstärkeanpassung**: Normalisierung (Angleichen) von sehr leisen oder lauten Titeln durch automatisches Auswerten des Pegels.

## Barrierefreiheit & Sichtbarkeit
- **Erweiterte Screenreader-Ausgabe**: Vertonte Hinweise (Audio-Feedback) für Fokuswechsel und wichtige Aktionen, damit auch ohne Blick auf den Bildschirm gearbeitet werden kann.
- **Individuelle Farbpaletten**: Persönliche Themen, die Nutzer:innen abspeichern können. Der Farbaudit (automatische Kontrastprüfung) prüft sie sofort.
- **Kontrast-Monitor im Hintergrund**: Ein Wächter (Watcher = Überwachungsprogramm) misst dauerhaft neue Farbkombinationen und meldet sofort, falls Werte unter die WCAG-Grenzen (Barrierefreiheits-Standards) fallen.

## Daten & Interoperabilität
- **Direkte SQLite-Anbindung**: Option, die Datenbankeinträge zusätzlich in einer SQLite-Datei (leichte Datenbank) zu speichern, um externe Programme anzubinden.
- **API-Schnittstelle**: Ein kleines Web-Interface (Programmierschnittstelle) stellt ausgewählte Daten und Aktionen für andere Tools bereit.
- **Synchronisation zwischen Geräten**: Nutzung eines gemeinsamen Speicherorts (z.B. Netzwerkordner oder Cloud) inklusive Konfliktlösung, wenn Änderungen gleichzeitig erfolgen.

## Qualitätssicherung & Automatisierung
- **Erweiterte Selbsttests**: Zusätzliche Prüfungen für Exportfunktionen, Audio-Module und die Barrierefreiheit. Ergebnisse landen im Selbsttest-Bericht.
- **Update-Assistent**: Automatischer Vergleich (Diff = Vergleich zweier Zustände) der Konfigurationsdateien mit bekannten Versionen, inklusive Empfehlung zum Übernehmen.
- **Szenario-Tests**: Aufzeichnen einer kompletten Arbeitssitzung (Makro = Schritt-für-Schritt-Anleitung) und automatisches Nachspielen zur Fehlersuche.

## Dokumentation & Schulung
- **Interaktive Hilfe**: Schritt-für-Schritt-Assistent (Wizard) für neue Nutzer:innen, der alle Hauptfunktionen einmal durchführt und erklärt.
- **Video-Tutorials**: Direkt aus dem Tool abrufbar. Ein eingebetteter Player zeigt kurze Clips mit Untertiteln.
- **Wissensdatenbank**: Sammlung häufig gestellter Fragen (FAQ = Frequently Asked Questions) und Antworten, inklusive Suchfeld und Querverweisen.

## Organisation & Projektplanung
- **Erweiterte Fortschrittsanzeige**: Visualisierung (Burndown-Chart = Diagramm mit verbleibender Arbeit) für Sprint-Planung.
- **Team-Modus**: Aufgaben (Tasks) mehreren Personen zuweisen und synchronisieren; inklusive Benachrichtigungen bei Änderungen.
- **Release-Taktung**: Roadmap (Zeitplan) für künftige Versionen mit geschätzten Zeiträumen und Abhängigkeiten zwischen Modulen.

Diese Liste kann direkt in neue Aufgaben (Tasks) überführt und in `todo.txt` dokumentiert werden, sobald die Umsetzung gestartet wird.
