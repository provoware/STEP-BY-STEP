# Leitfaden zur Aktualisierung der Paketversionen

Dieser Ablauf beschreibt, wie wir geprüfte Paketstände erneuern und dabei die
Reproduzierbarkeit wahren. Die Befehle sind komplett ausgeschrieben, so dass
auch Einsteiger*innen sie Schritt für Schritt nachvollziehen können.

1. **Virtuelle Umgebung anlegen (isolierter Python-Arbeitsbereich):**

   ```bash
   python3 -m venv .venv
   . .venv/bin/activate
   ```

2. **Werkzeug `pip-tools` installieren (erleichtert das Einfrieren von Versionen):**

   ```bash
   python -m pip install pip-tools==7.4.1
   ```

3. **Aktuelle Anforderungen prüfen:**

   ```bash
   python -m pip install -r requirements.txt
   python -m pip install -r requirements-dev.txt
   ```

4. **Neue Pins erzeugen:**

   ```bash
   python -m piptools compile requirements.in --output-file requirements.txt
   python -m piptools compile requirements-dev.in --output-file requirements-dev.txt
   ```

   *Hinweis:* Die Dateien `requirements.in` können optional genutzt werden, um
   Grundpakete ohne feste Pins zu notieren. In diesem Repository sind die Pins
   bereits direkt in `requirements*.txt` hinterlegt. Wer keine `.in`-Dateien
   verwendet, passt die Versionsnummern direkt in den bestehenden Dateien an.

5. **Selbsttests erneut laufen lassen:**

   ```bash
   python -m pytest
   python -m step_by_step --headless
   ```

6. **Ergebnisse dokumentieren:**

   - Änderungen in `requirements*.txt` committen.
   - Changelog bzw. `README.md` ergänzen, wenn neue Pakete notwendig sind.

Wer kein Internet hat, kann Schritt 3 überspringen und die Pakete später mit
`python -m pip install -r requirements.txt` nachinstallieren. Die Startroutine
meldet den Offline-Modus automatisch und lässt das Tool in einem abgesicherten
Zustand weiterlaufen.
