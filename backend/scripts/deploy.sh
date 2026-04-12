#!/usr/bin/env bash
# Search Angel - Deploy / Redeploy
# Run from the project root: bash scripts/deploy.sh
set -euo pipefail

COMPOSE_FILE="docker-compose.prod.yml"
PROJECT="search_angel"

echo "=== Deploying Search Angel ==="

# ── Check .env exists ────────────────────────────────────────────
if [ ! -f .env ]; then
    echo "ERROR: .env file not found. Copy .env.example to .env and fill in values."
    exit 1
fi

# ── Mount SSL certs into nginx if they exist ─────────────────────
if [ -d /opt/search_angel/nginx/ssl ]; then
    echo "[1/6] SSL certs found"
else
    echo "[1/6] No SSL dir found, creating with self-signed..."
    mkdir -p nginx/ssl
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout nginx/ssl/self-signed.key \
        -out nginx/ssl/self-signed.crt \
        -subj "/CN=searchangel" 2>/dev/null
fi

# ── Build images ─────────────────────────────────────────────────
echo "[2/6] Building Docker images..."
docker compose -f "$COMPOSE_FILE" -p "$PROJECT" build

# ── Start infrastructure first ───────────────────────────────────
echo "[3/6] Starting PostgreSQL + OpenSearch..."
docker compose -f "$COMPOSE_FILE" -p "$PROJECT" up -d postgres opensearch

# Wait for health
echo "  Waiting for PostgreSQL..."
until docker compose -f "$COMPOSE_FILE" -p "$PROJECT" exec -T postgres pg_isready -U search_angel 2>/dev/null; do
    sleep 2
done
echo "  PostgreSQL ready"

echo "  Waiting for OpenSearch..."
for i in $(seq 1 30); do
    if docker compose -f "$COMPOSE_FILE" -p "$PROJECT" exec -T opensearch curl -s http://localhost:9200 2>/dev/null | grep -q cluster_name; then
        break
    fi
    sleep 3
done
echo "  OpenSearch ready"

# ── Run migrations ───────────────────────────────────────────────
echo "[4/6] Running database migrations..."
docker compose -f "$COMPOSE_FILE" -p "$PROJECT" run --rm app \
    alembic upgrade head

# ── Create OpenSearch index ──────────────────────────────────────
echo "[5/6] Initializing OpenSearch index..."
docker compose -f "$COMPOSE_FILE" -p "$PROJECT" run --rm app \
    python -m scripts.create_indexes 2>/dev/null || echo "  Index may already exist"

# ── Start all services ───────────────────────────────────────────
echo "[6/6] Starting all services..."
docker compose -f "$COMPOSE_FILE" -p "$PROJECT" up -d

# ── Health check ─────────────────────────────────────────────────
echo ""
echo "Waiting for services to start..."
sleep 5

HEALTH=$(docker compose -f "$COMPOSE_FILE" -p "$PROJECT" exec -T app \
    curl -sf http://localhost:8000/api/v1/health 2>/dev/null || echo '{"status":"starting"}')

echo ""
echo "=== Deploy Complete ==="
echo "Health: $HEALTH"
echo ""
echo "Services:"
docker compose -f "$COMPOSE_FILE" -p "$PROJECT" ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
echo ""
echo "Access:"
echo "  API:     https://YOUR_DOMAIN/api/v1/health"
echo "  Docs:    https://YOUR_DOMAIN/docs"
echo "  Frontend: https://YOUR_DOMAIN/"
