#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [ -f ".env" ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

APP_HOST="${APP_HOST:-127.0.0.1}"
APP_PORT="${APP_PORT:-3000}"
APP_WORKERS="${APP_WORKERS:-1}"
APP_RELOAD="${APP_RELOAD:-false}"

export PYTHONPATH="$ROOT_DIR:${PYTHONPATH:-}"

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

mkdir -p outputs data logs

if [ "$APP_RELOAD" = "true" ]; then
  exec uvicorn src.api.main:app --host "$APP_HOST" --port "$APP_PORT" --reload
fi

exec uvicorn src.api.main:app --host "$APP_HOST" --port "$APP_PORT" --workers "$APP_WORKERS"
