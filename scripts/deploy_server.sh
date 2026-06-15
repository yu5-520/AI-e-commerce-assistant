#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/yu5-520/AI-e-commerce-assistant.git}"
APP_DIR="${APP_DIR:-/opt/ai-ecommerce-assistant}"
BRANCH="${BRANCH:-main}"
SERVICE_NAME="${SERVICE_NAME:-ai-operating-advisor}"
APP_PORT="${APP_PORT:-3000}"

if [ "${EUID}" -ne 0 ]; then
  echo "Please run as root: sudo bash scripts/deploy_server.sh"
  exit 1
fi

apt-get update
apt-get install -y git python3 python3-venv python3-pip curl

if [ ! -d "$APP_DIR/.git" ]; then
  mkdir -p "$APP_DIR"
  git clone "$REPO_URL" "$APP_DIR"
fi

cd "$APP_DIR"
git fetch origin "$BRANCH"
git checkout "$BRANCH"
git pull origin "$BRANCH"

if [ ! -f ".env" ]; then
  cp .env.example .env
fi

sed -i "s/^APP_PORT=.*/APP_PORT=${APP_PORT}/" .env
sed -i "s/^APP_HOST=.*/APP_HOST=0.0.0.0/" .env

chmod +x scripts/start_server.sh

cat > "/etc/systemd/system/${SERVICE_NAME}.service" <<SERVICE
[Unit]
Description=AI Operating Advisor FastAPI Service
After=network.target

[Service]
Type=simple
WorkingDirectory=${APP_DIR}
ExecStart=${APP_DIR}/scripts/start_server.sh
Restart=always
RestartSec=5
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload
systemctl enable "$SERVICE_NAME"
systemctl restart "$SERVICE_NAME"

sleep 2
systemctl --no-pager --full status "$SERVICE_NAME" || true

echo ""
echo "Service: ${SERVICE_NAME}"
echo "App dir: ${APP_DIR}"
echo "URL: http://$(curl -s ifconfig.me || echo SERVER_IP):${APP_PORT}"
echo "Health: curl http://127.0.0.1:${APP_PORT}/api/health"
