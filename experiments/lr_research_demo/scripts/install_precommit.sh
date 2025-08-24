#!/usr/bin/env bash
set -euo pipefail

# Install pre-commit into the project's virtualenv (if present) or globally
PY=${PY:-python3.11}
VENV=${VENV:-.venv}

if [ -d "$VENV" ]; then
  echo "Using virtualenv in $VENV"
  PIP="$VENV/bin/pip"
  PYBIN="$VENV/bin/python"
else
  echo "Virtualenv not found at $VENV; using system $PY"
  PIP="$PY -m pip"
  PYBIN="$PY"
fi

echo "Installing pre-commit..."
$PIP install --upgrade pip==24.2
$PIP install pre-commit==3.4.0

echo "Installing git hooks via pre-commit..."
$PYBIN -m pre_commit install || true

echo "pre-commit installation complete. Run 'pre-commit run --all-files' to check the repository."