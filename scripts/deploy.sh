#!/usr/bin/env bash
# ==============================================================================
# Telecom NMS Automated Deployment Script
# Target: RHEL 9 / Ubuntu 22.04 LTS on Azure VM
# Author: Osama Khalil (Senior DevOps Engineer)
# ==============================================================================

set -euo pipefail

APP_ROOT="/opt/telecom-nms"
WWW_ROOT="/var/www/telecom-nms"
SERVICE_NAME="nms-api"
USER="nmsadmin"

echo "[INFO] Starting Telecom NMS deployment..."

# 1. Ensure system user exists
if ! id -u "${USER}" >/dev/null 2>&1; then
    echo "[INFO] Creating service user ${USER}..."
    sudo useradd -r -s /sbin/nologin "${USER}"
fi

# 2. Directory structure setup
echo "[INFO] Setting up directory hierarchy..."
sudo mkdir -p "${APP_ROOT}/backend" "${APP_ROOT}/venv" "${WWW_ROOT}/frontend" "/etc/telecom-nms"
sudo chown -R "${USER}:${USER}" "${APP_ROOT}"

# 3. Synchronize application files
echo "[INFO] Syncing application code..."
sudo cp -r backend/* "${APP_ROOT}/backend/"
sudo cp -r frontend/* "${WWW_ROOT}/frontend/"
sudo chown -R "${USER}:${USER}" "${APP_ROOT}/backend"
sudo chown -R nginx:nginx "${WWW_ROOT}/frontend" 2>/dev/null || sudo chown -R www-data:www-data "${WWW_ROOT}/frontend" 2>/dev/null || true

# 4. Setup Python Virtualenv
echo "[INFO] Provisioning Python virtual environment..."
if [ ! -f "${APP_ROOT}/venv/bin/activate" ]; then
    sudo -u "${USER}" python3 -m venv "${APP_ROOT}/venv"
fi

sudo -u "${USER}" "${APP_ROOT}/venv/bin/pip" install --upgrade pip
sudo -u "${USER}" "${APP_ROOT}/venv/bin/pip" install -r "${APP_ROOT}/backend/requirements.txt"

# 5. Environment configuration template
if [ ! -f "/etc/telecom-nms/nms-backend.env" ]; then
    echo "[INFO] Generating default environment template..."
    sudo tee /etc/telecom-nms/nms-backend.env > /dev/null <<EOF
DATABASE_URL=sqlite:////opt/telecom-nms/telecom_nms_prod.db
PG_SSLMODE=require
APP_ENV=production
EOF
    sudo chmod 600 /etc/telecom-nms/nms-backend.env
    sudo chown "${USER}:${USER}" /etc/telecom-nms/nms-backend.env
fi

# 6. Install & reload systemd unit
echo "[INFO] Registering systemd unit..."
sudo cp backend/nms-api.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable "${SERVICE_NAME}"
sudo systemctl restart "${SERVICE_NAME}"

# 7. Configure Nginx
if [ -f "nginx/nginx.conf" ]; then
    echo "[INFO] Updating Nginx reverse proxy configuration..."
    sudo cp nginx/nginx.conf /etc/nginx/nginx.conf
    sudo nginx -t && sudo systemctl reload nginx
fi

# 8. Post-deploy smoke test
echo "[INFO] Running deployment verification probe..."
sleep 3
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/healthz || echo "000")

if [ "$RESPONSE" -eq 200 ]; then
    echo "=========================================================="
    echo "[SUCCESS] Telecom NMS Platform deployed and healthy (HTTP 200)!"
    echo "=========================================================="
else
    echo "[ERROR] Deployment health check failed with status code ${RESPONSE}"
    sudo journalctl -u "${SERVICE_NAME}" --no-pager -n 25
    exit 1
fi
