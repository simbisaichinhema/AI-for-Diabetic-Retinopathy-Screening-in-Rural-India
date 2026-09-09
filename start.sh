#!/usr/bin/env bash
set -Eeuo pipefail

PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(cd -- "$PROJECT_DIR/.." && pwd)"
PYTHON="$WORKSPACE_DIR/.venv/bin/python"
UVICORN="$WORKSPACE_DIR/.venv/bin/uvicorn"

if [[ ! -x "$UVICORN" ]]; then
  echo "Missing Python environment: $WORKSPACE_DIR/.venv"
  echo "Create it with: python3 -m venv $WORKSPACE_DIR/.venv"
  exit 1
fi

if [[ ! -d "$PROJECT_DIR/node_modules" ]]; then
  echo "Installing frontend dependencies..."
  npm --prefix "$PROJECT_DIR" ci
fi

backend_pid=""
cleanup() {
  if [[ -n "$backend_pid" ]] && kill -0 "$backend_pid" 2>/dev/null; then
    kill "$backend_pid" 2>/dev/null || true
    wait "$backend_pid" 2>/dev/null || true
  fi
}
trap cleanup EXIT INT TERM

echo "Starting FastAPI backend and loading the Hugging Face model..."
"$UVICORN" backend.app:app \
  --app-dir "$PROJECT_DIR" \
  --host 0.0.0.0 \
  --port 8000 &
backend_pid=$!

ready=false
for attempt in {1..120}; do
  if curl -fsS http://localhost:8000/api/models/status 2>/dev/null | grep -q '"classifier":true'; then
    ready=true
    break
  fi
  if ! kill -0 "$backend_pid" 2>/dev/null; then
    echo "Backend stopped during startup. Check the Python dependencies above."
    exit 1
  fi
  sleep 1
done

if [[ "$ready" != true ]]; then
  echo "Backend did not load the Hugging Face model within 120 seconds."
  echo "The model must be available before clinical screening can start."
  exit 1
fi

echo "Backend ready: http://localhost:8000"
echo "Frontend ready: http://localhost:5173"
echo "Press Ctrl+C to stop both services."
npm --prefix "$PROJECT_DIR" run dev -- --host 0.0.0.0