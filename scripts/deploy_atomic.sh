#!/usr/bin/env bash
set -Eeuo pipefail

# V11.12 lightweight atomic deployment script.
# Goal: keep atomic code switching, but avoid rebuilding venv on low-spec ECS.

APP_NAME="${APP_NAME:-ai-ecommerce-assistant}"
SERVICE_NAME="${SERVICE_NAME:-ai-operating-advisor}"
REPO_URL="${REPO_URL:-https://github.com/yu5-520/AI-e-commerce-assistant.git}"
BRANCH="${BRANCH:-main}"
DEPLOY_ROOT="${DEPLOY_ROOT:-/opt/ai-ecommerce-assistant-deploy}"
APP_HOST="${APP_HOST:-127.0.0.1}"
APP_PORT="${APP_PORT:-3000}"
KEEP_RELEASES="${KEEP_RELEASES:-5}"
RUN_USER="${RUN_USER:-$(id -un)}"
RUN_GROUP="${RUN_GROUP:-$(id -gn)}"
PYTHON_BIN="${PYTHON_BIN:-}"
EXPECTED_VERSION="${EXPECTED_VERSION:-}"
INSTALL_SYSTEMD_OVERRIDE="${INSTALL_SYSTEMD_OVERRIDE:-1}"
LIGHT_DEPLOY="${LIGHT_DEPLOY:-1}"
ROUTE_GUARD_MODE="${ROUTE_GUARD_MODE:-warn}"
RUNTIME_ROUTE_GUARD="${RUNTIME_ROUTE_GUARD:-warn}"
PIP_INDEX_URLS="${PIP_INDEX_URLS:-https://pypi.org/simple https://pypi.tuna.tsinghua.edu.cn/simple https://mirrors.aliyun.com/pypi/simple https://pypi.mirrors.ustc.edu.cn/simple}"
PIP_TIMEOUT="${PIP_TIMEOUT:-60}"
PIP_RETRIES="${PIP_RETRIES:-3}"
BOOTSTRAP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

RELEASES_DIR="$DEPLOY_ROOT/releases"
SHARED_DIR="$DEPLOY_ROOT/shared"
SHARED_VENV="$SHARED_DIR/.venv"
REQUIREMENTS_HASH_FILE="$SHARED_DIR/requirements.sha256"
CURRENT_LINK="$DEPLOY_ROOT/current"
NEXT_LINK="$DEPLOY_ROOT/.next"
LOG_FILE="$DEPLOY_ROOT/deploy.log"
PREVIOUS_RELEASE=""
NEW_RELEASE=""
SERVICE_VENV=""

log() {
  printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*" | tee -a "$LOG_FILE"
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
  if [ -n "$PYTHON_BIN" ]; then
    command -v "$PYTHON_BIN" >/dev/null 2>&1 || [ -x "$PYTHON_BIN" ] || fail "PYTHON_BIN not found: $PYTHON_BIN"
    python_version_ok "$PYTHON_BIN" || fail "PYTHON_BIN must be Python >= 3.10, got $(python_version_text "$PYTHON_BIN") at $PYTHON_BIN"
    return 0
  fi

  local candidate resolved
  for candidate in "$BOOTSTRAP_DIR/.venv/bin/python" "$SHARED_VENV/bin/python" python3.12 python3.11 python3.10 python3 python; do
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
  fail "No Python >= 3.10 found. Install python3.10+ or run with PYTHON_BIN=/opt/ai-ecommerce-assistant/.venv/bin/python bash scripts/deploy_atomic.sh"
}

file_hash() {
  local file="$1"
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$file" | awk '{print $1}'
  else
    python - "$file" <<'PY'
import hashlib, pathlib, sys
print(hashlib.sha256(pathlib.Path(sys.argv[1]).read_bytes()).hexdigest())
PY
  fi
}

retry() {
  local attempts="$1"; shift
  local delay="$1"; shift
  local n=1
  until "$@"; do
    if [ "$n" -ge "$attempts" ]; then
      return 1
    fi
    log "retry $n/$attempts failed: $*"
    n=$((n + 1))
    sleep "$delay"
  done
}

rollback() {
  if [ -n "${PREVIOUS_RELEASE:-}" ] && [ -d "$PREVIOUS_RELEASE" ]; then
    log "rollback: switching current back to $PREVIOUS_RELEASE"
    ln -sfn "$PREVIOUS_RELEASE" "$NEXT_LINK"
    mv -Tf "$NEXT_LINK" "$CURRENT_LINK"
    sudo systemctl restart "$SERVICE_NAME" || true
  else
    log "rollback skipped: no previous release"
  fi
}

on_error() {
  local line="$1"
  log "deployment failed at line $line"
  rollback
}
trap 'on_error $LINENO' ERR

preflight() {
  require_cmd git
  require_cmd sudo
  require_cmd curl
  mkdir -p "$DEPLOY_ROOT"
  sudo mkdir -p "$RELEASES_DIR" "$SHARED_DIR/logs"
  sudo chown -R "$RUN_USER:$RUN_GROUP" "$DEPLOY_ROOT"
  touch "$LOG_FILE"
  resolve_python

  git config --global --add safe.directory "$DEPLOY_ROOT" >/dev/null 2>&1 || true
  git config --global http.version HTTP/1.1
  git config --global http.lowSpeedLimit 0
  git config --global http.lowSpeedTime 999999
  git config --global --unset http.proxy >/dev/null 2>&1 || true
  git config --global --unset https.proxy >/dev/null 2>&1 || true
}

remote_commit() {
  git ls-remote "$REPO_URL" "refs/heads/$BRANCH" | awk '{print $1}'
}

pip_install_with_fallback() {
  local pip_args=("$@")
  local index_url
  local success=0
  for index_url in $PIP_INDEX_URLS; do
    log "pip install via index: $index_url"
    if python -m pip install --no-cache-dir --timeout "$PIP_TIMEOUT" --retries "$PIP_RETRIES" --index-url "$index_url" "${pip_args[@]}"; then
      success=1
      break
    fi
    log "pip index failed: $index_url"
  done
  if [ "$success" != "1" ]; then
    return 1
  fi
}

ensure_shared_venv() {
  if [ ! -x "$SHARED_VENV/bin/python" ]; then
    log "create shared virtualenv with $PYTHON_BIN ($(python_version_text "$PYTHON_BIN"))"
    "$PYTHON_BIN" -m venv "$SHARED_VENV"
  else
    log "reuse shared virtualenv: $SHARED_VENV ($(python_version_text "$SHARED_VENV/bin/python"))"
  fi
  # shellcheck disable=SC1091
  source "$SHARED_VENV/bin/activate"
  log "upgrade shared pip with fallback indexes"
  pip_install_with_fallback --upgrade pip || log "pip upgrade failed, continue with existing pip"
}

install_requirements_if_needed() {
  if [ ! -f requirements.txt ]; then
    log "requirements.txt not found; skip dependency install"
    return 0
  fi
  local current_hash previous_hash
  current_hash="$(file_hash requirements.txt)"
  previous_hash="$(cat "$REQUIREMENTS_HASH_FILE" 2>/dev/null || true)"
  if [ "$LIGHT_DEPLOY" = "1" ] && [ "$current_hash" = "$previous_hash" ]; then
    log "requirements unchanged; skip pip install"
    return 0
  fi
  log "install requirements with fallback indexes"
  pip_install_with_fallback -r requirements.txt
  printf '%s\n' "$current_hash" > "$REQUIREMENTS_HASH_FILE"
}

prepare_release_venv() {
  if [ "$LIGHT_DEPLOY" = "1" ]; then
    ensure_shared_venv
    install_requirements_if_needed
    rm -rf .venv
    ln -sfn "$SHARED_VENV" .venv
    SERVICE_VENV="$SHARED_VENV"
    log "light deploy enabled: service uses shared venv $SERVICE_VENV"
  else
    log "create release virtualenv with $PYTHON_BIN ($(python_version_text "$PYTHON_BIN"))"
    "$PYTHON_BIN" -m venv .venv
    # shellcheck disable=SC1091
    source .venv/bin/activate
    log "upgrade pip with fallback indexes"
    pip_install_with_fallback --upgrade pip || log "pip upgrade failed, continue with bundled pip"
    install_requirements_if_needed
    SERVICE_VENV="$CURRENT_LINK/.venv"
  fi
}

create_release() {
  local commit="$1"
  local stamp
  stamp="$(date '+%Y%m%d%H%M%S')"
  NEW_RELEASE="$RELEASES_DIR/${stamp}_${commit:0:8}"
  log "clone release: $NEW_RELEASE"
  git clone --depth 1 --branch "$BRANCH" "$REPO_URL" "$NEW_RELEASE"
  cd "$NEW_RELEASE"
  local checked_commit
  checked_commit="$(git rev-parse HEAD)"
  [ "$checked_commit" = "$commit" ] || fail "cloned commit $checked_commit does not match remote $commit"

  rm -rf logs
  ln -s "$SHARED_DIR/logs" logs
  if [ -f "$SHARED_DIR/.env" ]; then
    ln -sfn "$SHARED_DIR/.env" .env
  fi

  prepare_release_venv

  log "verify release consistency"
  if [ -n "$EXPECTED_VERSION" ]; then
    python scripts/verify_release.py --expected-version "$EXPECTED_VERSION" --route-mode "$ROUTE_GUARD_MODE"
  else
    python scripts/verify_release.py --route-mode "$ROUTE_GUARD_MODE"
  fi
}

install_systemd_override() {
  [ "$INSTALL_SYSTEMD_OVERRIDE" = "1" ] || return 0
  [ -n "$SERVICE_VENV" ] || SERVICE_VENV="$CURRENT_LINK/.venv"
  log "install systemd override for $SERVICE_NAME with venv $SERVICE_VENV"
  sudo mkdir -p "/etc/systemd/system/$SERVICE_NAME.service.d"
  sudo tee "/etc/systemd/system/$SERVICE_NAME.service.d/override.conf" >/dev/null <<EOF
[Service]
WorkingDirectory=$CURRENT_LINK
Environment=APP_HOST=$APP_HOST
Environment=APP_PORT=$APP_PORT
Environment=PYTHONUNBUFFERED=1
EnvironmentFile=-$SHARED_DIR/.env
ExecStart=
ExecStart=$SERVICE_VENV/bin/uvicorn src.api.main:app --host $APP_HOST --port $APP_PORT
Restart=always
RestartSec=3
User=$RUN_USER
Group=$RUN_GROUP
EOF
  sudo systemctl daemon-reload
}

switch_current() {
  PREVIOUS_RELEASE="$(readlink -f "$CURRENT_LINK" 2>/dev/null || true)"
  log "previous release: ${PREVIOUS_RELEASE:-none}"
  log "switch current -> $NEW_RELEASE"
  ln -sfn "$NEW_RELEASE" "$NEXT_LINK"
  mv -Tf "$NEXT_LINK" "$CURRENT_LINK"
}

health_check() {
  local expected_version
  expected_version="$(awk -F': ' '/Current Version:/ {print $2; exit}' "$CURRENT_LINK/versioning/VERSION.md")"
  log "restart service: $SERVICE_NAME"
  sudo systemctl restart "$SERVICE_NAME"

  log "wait for health $APP_HOST:$APP_PORT expected=$expected_version"
  for i in $(seq 1 30); do
    if curl -fsS "http://$APP_HOST:$APP_PORT/api/health" >/tmp/${APP_NAME}_health.json 2>/dev/null; then
      if python - "$expected_version" </tmp/${APP_NAME}_health.json <<'PY'
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

route_check() {
  log "runtime route check mode=$RUNTIME_ROUTE_GUARD"
  local failures=0
  curl -fsS -H 'X-Mock-User-Id: U004' "http://$APP_HOST:$APP_PORT/api/system/runtime-diagnostics" >/dev/null || failures=$((failures + 1))
  curl -fsS -H 'X-Mock-User-Id: U004' "http://$APP_HOST:$APP_PORT/api/modules/operating-unit" >/dev/null || failures=$((failures + 1))
  if [ "$failures" -gt 0 ]; then
    if [ "$RUNTIME_ROUTE_GUARD" = "strict" ]; then
      fail "runtime route check failed: $failures"
    fi
    log "WARN: runtime route check failed: $failures; continue because RUNTIME_ROUTE_GUARD=$RUNTIME_ROUTE_GUARD"
  fi
}

reload_nginx() {
  if command -v nginx >/dev/null 2>&1; then
    log "reload nginx"
    sudo nginx -t
    sudo systemctl reload nginx || true
  fi
}

cleanup_old_releases() {
  log "cleanup old releases, keep $KEEP_RELEASES"
  find "$RELEASES_DIR" -mindepth 1 -maxdepth 1 -type d | sort -r | tail -n +$((KEEP_RELEASES + 1)) | while read -r dir; do
    [ "$dir" = "$(readlink -f "$CURRENT_LINK" 2>/dev/null || true)" ] && continue
    rm -rf "$dir"
    log "removed old release: $dir"
  done
}

main() {
  preflight
  log "=== lightweight atomic deploy start ==="
  local commit
  commit="$(retry 5 3 remote_commit)"
  [ -n "$commit" ] || fail "cannot resolve remote commit for $REPO_URL $BRANCH"
  log "remote $BRANCH commit: $commit"
  create_release "$commit"
  switch_current
  install_systemd_override
  health_check
  route_check
  reload_nginx
  cleanup_old_releases
  log "=== lightweight atomic deploy success ==="
  log "current: $(readlink -f "$CURRENT_LINK")"
}

main "$@"
