#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN=${PYTHON:-python3}

if [ ! -d ".venv" ]; then
  echo "[Bootstrap] Erstelle virtuelle Umgebung (.venv)" >&2
  "$PYTHON_BIN" -m venv .venv
fi

if [ -f ".venv/bin/activate" ]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
else
  echo "[Bootstrap] Aktivierungsskript nicht gefunden (.venv/bin/activate)" >&2
  exit 1
fi

python -m pip install --upgrade pip
python -m pip install --upgrade -r requirements.txt

if [ "${STEP_BY_STEP_INSTALL_DEV:-0}" != "0" ] && [ -f "requirements-dev.txt" ]; then
  echo "[Bootstrap] Installiere zusätzliche Entwickler-Werkzeuge" >&2
  python -m pip install --upgrade -r requirements-dev.txt
fi

python start_tool.py "$@"
