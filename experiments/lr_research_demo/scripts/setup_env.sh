#!/usr/bin/env bash
set -euo pipefail

# POSIX-compatible environment setup for macOS/Linux
PY=${PY:-python3.11}
VENV=${VENV:-.venv}
PIP="$VENV/bin/pip"
PYBIN="$VENV/bin/python"

echo "Using python: ${PY}"

if ! command -v "$PY" >/dev/null 2>&1; then
  echo "Error: ${PY} not found. Please install Python 3.11." >&2
  echo "macOS: brew install python@3.11" >&2
  echo "Ubuntu/Debian: sudo apt install python3.11" >&2
  exit 1
fi

# Create venv
if [ ! -d "$VENV" ]; then
  echo "Creating virtual environment at $VENV"
  "$PY" -m venv "$VENV"
  "$PIP" install -U pip==24.2
else
  echo "Virtual environment $VENV already exists"
fi

# Install runtime requirements
echo "Installing runtime requirements"
"$PIP" install -r requirements.txt

# Install dev requirements if requested
if [ "${1:-}" = "--dev" ]; then
  echo "Installing dev requirements"
  "$PIP" install -r requirements-dev.txt
fi

echo "Setup complete. Activate with: source $VENV/bin/activate"
