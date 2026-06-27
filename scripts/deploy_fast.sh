#!/usr/bin/env bash
set -Eeuo pipefail

# V11.13 demo fast deployment script.
# Goal: high-frequency Demo iteration. No release clone, no venv rebuild, no pip install by default.
# Use deploy_atomic.sh for milestone releases and production-like verification.

APP_NAME="${APP_NAME:-ai-ecommerce-assistant}"
SERVICE_NAME="${SERVICE_NAME:-ai-operating-advisor}"
BRANCH="${BRANCH:-main}"
APP_HOST="${APP_HOST:-127.0.0.1}"
APP_PORT="${APP_PORT:-3000}"
APP_DIR="${APP_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
RUN_USER="${RUN_USER:-$(id -un)}"
RUN_GROUP="${RUN_GROUP:-$(id -gn)}"
PYTHON_BIN="${PYTHON_BIN:-$APP_DIR/.venv/bin/python}"
INSTALL_SYSTEMD_OVERRIDE="${INSTALL_SYSTEMD_OVERRIDE:-1}"
FORCE_INSTALL_REQUIREMENTS="${FORCE_INSTALL_REQUIREMENTS:-0}"
FETCH_ATTEMPTS="${FETCH_ATTEMPTS:-5}"
FETCH_TIMEOUT="${FETCH_TIMEOUT:-300}"
FETCH_SLEEP="${FETCH_SLEEP:-10}"
ROUTE_GUARD_MODE="${ROUTE_GUARD_MODE:-warn}"
PIP_INDEX_URLS="${PIP_INDEX_URLS:-https://pypi.org/simple https://pypi.tuna.tsinghua.edu.cn/simple https://mirrors.aliyun.com/pypi/simple https://pypi.mirrors.ustc.edu.cn/simple}"
PIP_TIMEOUT="${PIP_TIMEOUT:-60}"
PIP_RETRIES="${PIP_RETRIES:-3}"

log() {
  printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

fail() {
  log "ERROR: $*"
  exit 1
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || fail "missing command: $1"
}

python_version_ok() {
  local candidate="$1"
  [ -x "$candidate" ] || command -v "$candidate" >/dev/null 2>&1 || return 1
  "$candidate" - <<'PY' >/dev/null 2>&1
import sys
raise SystemExit(0 if sys.version_info >= (3, 10) else 1)
PY
}

python_version_text() {
  local candidate="$1"
  "$candidate" - <<'PY' 2>/dev/null || true
import sys
print(f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
PY
}

resolve_python() {
  local candidate resolved
  for candidate in "$PYTHON_BIN" "$APP_DIR/.venv/bin/python" python3.12 python3.11 python3.10 python3 python; do
    if [ -x "$candidate" ]; then
      resolved="$candidate"
    else
      resolved="$(command -v "$candidate" 2>/dev/null || true)"
    fi
    [ -n "$resolved" ] || continue
    if python_version_ok "$resolved"; then
      PYTHON_BIN="$resolved"
      log "selected python: $PYTHON_BIN ($(python_version_text "$PYTHON_BIN"))"
      return 0
    fi
    log "skip python candidate: $resolved ($(python_version_text "$resolved"))"
  done
  fail "No Python >= 3.10 found. Set PYTHON_BIN=/path/to/python3.10+"
}

pip_install_with_fallback() {
  local pip_args=("$@")
  local index_url
  for index_url in $PIP_INDEX_URLS; do
    log "pip install via index: $index_url"
    if "$PYTHON_BIN" -m pip install --no-cache-dir --timeout "$PIP_TIMEOUT" --retries "$PIP_RETRIES" --index-url "$index_url" "${pip_args[@]}"; then
      return 0
    fi
    log "pip index failed: $index_url"
  done
  return 1
}

fetch_latest() {
  cd "$APP_DIR"
  git config --global --add safe.directory "$APP_DIR" >/dev/null 2>&1 || true
  git config --global http.version HTTP/1.1
  git config --global http.lowSpeedLimit 0
  git config --global http.lowSpeedTime 999999
  git config --global --unset http.proxy >/dev/null 2>&1 || true
  git config --global --unset https.proxy >/dev/null 2>&1 || true

  local attempt=1
  while [ "$attempt" -le "$FETCH_ATTEMPTS" ]; do
    log "fetch attempt $attempt/$FETCH_ATTEMPTS"
    if timeout "$FETCH_TIMEOUT" git fetch --no-tags --depth=1 origin "+refs/heads/$BRANCH:refs/remotes/origin/$BRANCH"; then
      git rev-parse "origin/$BRANCH" >/dev/null
      return 0
    fi
    log "GitHub fetch failed; retry in ${FETCH_SLEEP}s"
    attempt=$((attempt + 1))
    sleep "$FETCH_SLEEP"
  done
  fail "GitHub fetch failed. Fast deploy stopped before reset."
}

reset_to_latest() {
  cd "$APP_DIR"
  log "reset bootstrap repo to origin/$BRANCH"
  git reset --hard "origin/$BRANCH"
  log "current commit: $(git log -1 --oneline)"
  cat versioning/VERSION.md
}

install_requirements_if_forced() {
  cd "$APP_DIR"
  if [ "$FORCE_INSTALL_REQUIREMENTS" != "1" ]; then
    log "skip pip install: FORCE_INSTALL_REQUIREMENTS=$FORCE_INSTALL_REQUIREMENTS"
    return 0
  fi
  [ -f requirements.txt ] || return 0
  log "FORCE_INSTALL_REQUIREMENTS=1, install requirements"
  pip_install_with_fallback -r requirements.txt
}

verify_release() {
  cd "$APP_DIR"
  log "verify version consistency"
  "$PYTHON_BIN" scripts/verify_release.py --route-mode "$ROUTE_GUARD_MODE"
}

install_systemd_override() {
  [ "$INSTALL_SYSTEMD_OVERRIDE" = "1" ] || return 0
  log "install systemd override for demo fast deploy"
  sudo mkdir -p "/etc/systemd/system/$SERVICE_NAME.service.d"
  sudo tee "/etc/systemd/system/$SERVICE_NAME.service.d/override.conf" >/dev/null <<EOF
[Service]
WorkingDirectory=$APP_DIR
Environment=APP_HOST=$APP_HOST
Environment=APP_PORT=$APP_PORT
Environment=APP_ENV=demo
Environment=STRICT_DATA_SCOPE=false
Environment=PYTHONUNBUFFERED=1
EnvironmentFile=-$APP_DIR/.env
ExecStart=
ExecStart=$APP_DIR/.venv/bin/uvicorn src.api.main:app --host $APP_HOST --port $APP_PORT
Restart=always
RestartSec=3
User=$RUN_USER
Group=$RUN_GROUP
EOF
  sudo systemctl daemon-reload
}

health_check() {
  local expected_version
  expected_version="$(awk -F': ' '/Current Version:/ {print $2; exit}' "$APP_DIR/versioning/VERSION.md")"
  log "restart service: $SERVICE_NAME"
  sudo systemctl restart "$SERVICE_NAME"

  log "wait for health $APP_HOST:$APP_PORT expected=$expected_version"
  for i in $(seq 1 30); do
    if curl -fsS "http://$APP_HOST:$APP_PORT/api/health" >/tmp/${APP_NAME}_fast_health.json 2>/dev/null; then
      if "$PYTHON_BIN" - "$expected_version" </tmp/${APP_NAME}_fast_health.json <<'PY'
import json, sys
expected = sys.argv[1]
payload = json.load(sys.stdin)
if payload.get("ok") and payload.get("version") == expected:
    raise SystemExit(0)
print(payload)
raise SystemExit(1)
PY
      then
        log "health ok"
        return 0
      fi
    fi
    sleep 1
  done
  sudo systemctl status "$SERVICE_NAME" --no-pager -l || true
  sudo journalctl -u "$SERVICE_NAME" -n 120 --no-pager || true
  fail "health check failed"
}

reload_nginx() {
  if command -v nginx >/dev/null 2>&1; then
    log "reload nginx"
    sudo nginx -t
    sudo systemctl reload nginx || true
  fi
}

final_check() {
  log "final version check"
  curl -sS "http://$APP_HOST:$APP_PORT/api/health" ; echo
  curl -sS -H 'X-Mock-User-Id: U004' "http://$APP_HOST:$APP_PORT/api/system/runtime-diagnostics" ; echo || true
}

main() {
  require_cmd git
  require_cmd sudo
  require_cmd curl
  cd "$APP_DIR"
  resolve_python
  log "=== demo fast deploy start ==="
  fetch_latest
  reset_to_latest
  install_requirements_if_forced
  verify_release
  install_systemd_override
  health_check
  reload_nginx
  final_check
  log "=== demo fast deploy success ==="
}

main "$@"
