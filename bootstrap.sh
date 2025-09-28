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

python start_tool.py "$@"
