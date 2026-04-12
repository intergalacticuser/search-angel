#!/usr/bin/env bash
# Search Angel - PostgreSQL backup
# Add to crontab: 0 3 * * * /opt/search_angel/scripts/backup.sh
set -euo pipefail

BACKUP_DIR="/opt/search_angel/backups"
COMPOSE_FILE="/opt/search_angel/docker-compose.prod.yml"
RETENTION_DAYS=7
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/search_angel_$TIMESTAMP.sql.gz"

mkdir -p "$BACKUP_DIR"

# Dump database
docker compose -f "$COMPOSE_FILE" exec -T postgres \
    pg_dump -U search_angel search_angel | gzip > "$BACKUP_FILE"

# Check backup size
SIZE=$(ls -lh "$BACKUP_FILE" | awk '{print $5}')
echo "[$(date)] Backup created: $BACKUP_FILE ($SIZE)"

# Remove old backups
find "$BACKUP_DIR" -name "search_angel_*.sql.gz" -mtime +$RETENTION_DAYS -delete
echo "[$(date)] Cleaned backups older than $RETENTION_DAYS days"
