#!/usr/bin/env bash
# backup-mysql.sh — Backup MySQL de TUWAYKIFOOD con retención y compresión.
#
# Uso manual:
#   docker exec food_mysql bash -c 'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysqldump -u root food_db' \
#     | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz
#
# Uso automático (cron en el host):
#   0 3 * * * /ruta/al/proyecto/scripts/backup-mysql.sh >> /var/log/food_backup.log 2>&1
#
# Variables de entorno (o se leen del .env del proyecto):
#   BACKUP_DIR          — directorio destino (default: ./backups)
#   BACKUP_RETENTION    — días de retención (default: 30)
#   MYSQL_CONTAINER     — nombre del contenedor MySQL (default: food_mysql)
#   DB_NAME             — nombre de la base de datos (default: food_db)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Cargar .env si existe
if [ -f "$PROJECT_DIR/.env" ]; then
    set -a
    # shellcheck disable=SC1091
    source "$PROJECT_DIR/.env"
    set +a
fi

BACKUP_DIR="${BACKUP_DIR:-$PROJECT_DIR/backups}"
RETENTION_DAYS="${BACKUP_RETENTION:-30}"
CONTAINER="${MYSQL_CONTAINER:-food_mysql}"
DATABASE="${DB_NAME:-food_db}"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
FILENAME="food_backup_${TIMESTAMP}.sql.gz"

mkdir -p "$BACKUP_DIR"

echo "[$(date)] Iniciando backup de $DATABASE desde $CONTAINER..."

docker exec "$CONTAINER" bash -c \
    "MYSQL_PWD=\"\$MYSQL_ROOT_PASSWORD\" mysqldump -u root --single-transaction --routines --triggers --events \"$DATABASE\"" \
    | gzip > "$BACKUP_DIR/$FILENAME"

SIZE=$(du -h "$BACKUP_DIR/$FILENAME" | cut -f1)
echo "[$(date)] Backup completado: $FILENAME ($SIZE)"

# Retención: eliminar backups más viejos que RETENTION_DAYS
DELETED=$(find "$BACKUP_DIR" -name "food_backup_*.sql.gz" -mtime +"$RETENTION_DAYS" -print -delete | wc -l)
if [ "$DELETED" -gt 0 ]; then
    echo "[$(date)] Limpieza: $DELETED backup(s) eliminado(s) (>$RETENTION_DAYS días)"
fi

# Resumen
TOTAL=$(find "$BACKUP_DIR" -name "food_backup_*.sql.gz" | wc -l)
TOTAL_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
echo "[$(date)] Total backups: $TOTAL ($TOTAL_SIZE)"
