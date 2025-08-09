#!/usr/bin/env bash
set -euo pipefail

# Smoke-test the EQUITR Coder TUI using Textual for ~20 seconds, then exit.
# - Ensures textual and rich are available
# - Launches equitrcoder TUI (default mode: single)
# - Captures logs to a temp file and prints a summary
# - Cleans up the process on exit

MODE="${1:-single}"
DURATION_SEC="${DURATION_SEC:-20}"
LOG_FILE="${LOG_FILE:-/tmp/equitrcoder_tui_$(date +%s).log}"

command -v python >/dev/null 2>&1 || {
  echo "Python not found on PATH" >&2
  exit 1
}

# Ensure textual and rich are installed
if ! python - <<'PY' >/dev/null 2>&1
import importlib.util as iu
ok = iu.find_spec('textual') is not None and iu.find_spec('rich') is not None
raise SystemExit(0 if ok else 1)
PY
then
  echo "Installing textual and rich (required for TUI)..."
  python -m pip install --quiet --upgrade pip
  python -m pip install --quiet textual rich || {
    echo "Failed to install textual/rich. Please install them manually: pip install textual rich" >&2
    exit 1
  }
fi

# Determine CLI entry
if command -v equitrcoder >/dev/null 2>&1; then
  CLI_CMD=(equitrcoder)
else
  CLI_CMD=(python -m equitrcoder.cli.unified_main)
fi

echo "Launching TUI in mode: ${MODE} for ${DURATION_SEC}s..."
echo "Log: ${LOG_FILE}"

# Launch in background and capture PID
set +e
"${CLI_CMD[@]}" tui --mode "${MODE}" >"${LOG_FILE}" 2>&1 &
PID=$!
set -e

# Ensure process started
sleep 2
if ! ps -p "$PID" >/dev/null 2>&1; then
  echo "TUI failed to start. Dumping log:"
  echo "----------------------------------------"
  cat "${LOG_FILE}" || true
  echo "----------------------------------------"
  exit 1
fi

echo "TUI started (PID=${PID}). Running for ${DURATION_SEC}s..."
sleep "${DURATION_SEC}"

# Graceful shutdown
if ps -p "$PID" >/dev/null 2>&1; then
  echo "Stopping TUI (PID=${PID})..."
  kill -TERM "$PID" 2>/dev/null || true
  sleep 2
fi

# Force kill if still running
if ps -p "$PID" >/dev/null 2>&1; then
  echo "Force killing TUI (PID=${PID})..."
  kill -KILL "$PID" 2>/dev/null || true
  sleep 1
fi

# Show a brief log summary
echo "----------------------------------------"
echo "TUI log (last 80 lines):"
if [ -f "${LOG_FILE}" ]; then
  tail -n 80 "${LOG_FILE}" || true
else
  echo "No log file at ${LOG_FILE}"
fi
echo "----------------------------------------"

echo "Done." 