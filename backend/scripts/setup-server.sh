#!/usr/bin/env bash
# Search Angel - First-time server setup
# Run on a fresh Ubuntu 22.04+ VPS as root
set -euo pipefail

echo "=== Search Angel Server Setup ==="

# ── System updates ───────────────────────────────────────────────
echo "[1/6] Updating system..."
apt-get update && apt-get upgrade -y

# ── Install Docker ───────────────────────────────────────────────
echo "[2/6] Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
else
    echo "  Docker already installed"
fi

# ── Install Docker Compose plugin ────────────────────────────────
echo "[3/6] Checking Docker Compose..."
if ! docker compose version &> /dev/null; then
    apt-get install -y docker-compose-plugin
fi
docker compose version

# ── Firewall ─────────────────────────────────────────────────────
echo "[4/6] Configuring firewall..."
apt-get install -y ufw
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw allow 80/tcp
ufw allow 443/tcp
echo "y" | ufw enable
ufw status

# ── System tuning for OpenSearch ─────────────────────────────────
echo "[5/6] Tuning system for OpenSearch..."
sysctl -w vm.max_map_count=262144
echo "vm.max_map_count=262144" >> /etc/sysctl.conf

# ── Create app directory ─────────────────────────────────────────
echo "[6/6] Setting up directory structure..."
mkdir -p /opt/search_angel/backups
mkdir -p /opt/search_angel/nginx/ssl

# Generate self-signed cert for initial setup (replace with Let's Encrypt later)
if [ ! -f /opt/search_angel/nginx/ssl/self-signed.crt ]; then
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout /opt/search_angel/nginx/ssl/self-signed.key \
        -out /opt/search_angel/nginx/ssl/self-signed.crt \
        -subj "/CN=searchangel/O=SearchAngel/C=US"
    echo "  Self-signed SSL cert created"
fi

echo ""
echo "=== Setup complete! ==="
echo ""
echo "Next steps:"
echo "  1. Copy project files to /opt/search_angel/"
echo "  2. cp .env.example .env && nano .env  (set passwords)"
echo "  3. bash scripts/deploy.sh"
echo ""
echo "For Let's Encrypt SSL:"
echo "  certbot certonly --webroot -w /var/www/certbot -d YOUR_DOMAIN"
echo "  Then update nginx/conf.d/search_angel.conf with the cert paths"
