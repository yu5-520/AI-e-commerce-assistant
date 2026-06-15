#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/yu5-520/AI-e-commerce-assistant.git}"
APP_DIR="${APP_DIR:-/opt/ai-ecommerce-assistant}"
BRANCH="${BRANCH:-main}"
SERVICE_NAME="${SERVICE_NAME:-ai-operating-advisor}"
APP_PORT="${APP_PORT:-3000}"
PUBLIC_HOST="${PUBLIC_HOST:-47.118.29.46}"
NGINX_SITE_NAME="${NGINX_SITE_NAME:-ai-operating-advisor}"

if [ "${EUID}" -ne 0 ]; then
  echo "Please run as root: sudo bash scripts/deploy_server.sh"
  exit 1
fi

install_packages() {
  if command -v apt-get >/dev/null 2>&1; then
    apt-get update
    apt-get install -y git python3 python3-venv python3-pip curl nginx
    return
  fi

  if command -v dnf >/dev/null 2>&1; then
    dnf install -y git python3 python3-pip curl nginx
    return
  fi

  if command -v yum >/dev/null 2>&1; then
    yum install -y git python3 python3-pip curl nginx
    return
  fi

  echo "No supported package manager found. Please install git python3 python3-pip curl nginx manually."
  exit 1
}

install_packages

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

# Security default: app only listens on localhost. Public access goes through Nginx 80/443.
sed -i "s/^APP_PORT=.*/APP_PORT=${APP_PORT}/" .env
sed -i "s/^APP_HOST=.*/APP_HOST=127.0.0.1/" .env
sed -i "s#^PUBLIC_BASE_URL=.*#PUBLIC_BASE_URL=http://${PUBLIC_HOST}#" .env

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

NGINX_AVAILABLE_DIR="/etc/nginx/sites-available"
NGINX_ENABLED_DIR="/etc/nginx/sites-enabled"
NGINX_CONF_PATH="${NGINX_AVAILABLE_DIR}/${NGINX_SITE_NAME}"

if [ ! -d "$NGINX_AVAILABLE_DIR" ] || [ ! -d "$NGINX_ENABLED_DIR" ]; then
  # RHEL / CentOS / Alibaba Cloud Linux usually uses /etc/nginx/conf.d/*.conf
  NGINX_CONF_PATH="/etc/nginx/conf.d/${NGINX_SITE_NAME}.conf"
else
  rm -f /etc/nginx/sites-enabled/default
fi

cat > "$NGINX_CONF_PATH" <<NGINX
server {
    listen 80;
    server_name ${PUBLIC_HOST};

    client_max_body_size 20m;

    location / {
        proxy_pass http://127.0.0.1:${APP_PORT};
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
NGINX

if [ -d "$NGINX_AVAILABLE_DIR" ] && [ -d "$NGINX_ENABLED_DIR" ]; then
  ln -sf "$NGINX_CONF_PATH" "${NGINX_ENABLED_DIR}/${NGINX_SITE_NAME}"
fi

nginx -t

systemctl daemon-reload
systemctl enable "$SERVICE_NAME"
systemctl restart "$SERVICE_NAME"
systemctl enable nginx
systemctl restart nginx

sleep 2
systemctl --no-pager --full status "$SERVICE_NAME" || true

echo ""
echo "Service: ${SERVICE_NAME}"
echo "App dir: ${APP_DIR}"
echo "Public URL: http://${PUBLIC_HOST}"
echo "Local app: http://127.0.0.1:${APP_PORT}"
echo "Health: curl http://127.0.0.1:${APP_PORT}/api/health"
echo "Security group: open 80/443 to public; do not open ${APP_PORT} to 0.0.0.0/0."
