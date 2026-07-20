#!/usr/bin/env bash
# =============================================================================
# docker-entrypoint.sh — Pre-arranque del contenedor TUWAYKIFOOD
#
# 1. Espera a que MySQL esté disponible.
# 2. Ejecuta migraciones Alembic (upgrade head).
# 3. Pre-init Reflex (reflex init).
# 4. Arranca Reflex con los argumentos pasados por CMD.
# =============================================================================
set -euo pipefail

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info()  { echo -e "${CYAN}[ENTRYPOINT]${NC} $*"; }
ok()    { echo -e "${GREEN}[ENTRYPOINT]${NC} $*"; }
warn()  { echo -e "${YELLOW}[ENTRYPOINT]${NC} $*"; }
fail()  { echo -e "${RED}[ENTRYPOINT]${NC} $*"; exit 1; }

# ─── 1. Esperar MySQL ───────────────────────────────────────────────────────
DB_HOST="${DB_HOST:-mysql}"
DB_PORT="${DB_PORT:-3306}"
MAX_WAIT=120
SOCKET_TIMEOUT=5

sleep 3

info "Esperando MySQL en ${DB_HOST}:${DB_PORT}..."
WAITED=0
while [[ $WAITED -lt $MAX_WAIT ]]; do
    if python3 -c "
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(${SOCKET_TIMEOUT})
try:
    s.connect(('${DB_HOST}', ${DB_PORT}))
    s.close()
    exit(0)
except Exception as e:
    exit(1)
" 2>/dev/null; then
        break
    fi
    sleep 2
    WAITED=$((WAITED + 2))
done

if [[ $WAITED -ge $MAX_WAIT ]]; then
    fail "MySQL no disponible después de ${MAX_WAIT}s"
fi
ok "MySQL disponible"

# ─── 2. Migraciones Alembic ─────────────────────────────────────────────────
SKIP_MIGRATE="${SKIP_MIGRATE:-false}"
if [[ "$SKIP_MIGRATE" != "true" ]]; then
    info "Ejecutando migraciones Alembic..."
    if ! alembic upgrade head; then
        fail "Migraciones fallaron — abortando arranque"
    fi
    ok "Migraciones aplicadas correctamente"
else
    warn "Migraciones saltadas (SKIP_MIGRATE=true)"
fi

# ─── 3. Directorios de upload ──────────────────────────────────────────────
info "Preparando directorios de upload..."
mkdir -p /app/uploaded_files/food_productos /app/uploaded_files/food_empresas 2>/dev/null || true
if [ -w /app/uploaded_files ]; then
    ok "Directorio de uploads OK (writable)"
else
    warn "uploaded_files NO es escribible — las subidas de imágenes fallarán"
fi

# ─── 4. Pre-init Reflex ─────────────────────────────────────────────────────
info "Limpiando frontend para recompilación limpia..."
rm -rf /app/.web 2>/dev/null || true

info "Pre-inicializando frontend (reflex init)..."
reflex init 2>&1 | tail -3 && ok "reflex init OK" || warn "reflex init con error — continuando"

# ─── 5. Ejecutar CMD (reflex run ...) ───────────────────────────────────────
info "Iniciando Reflex: $*"
exec "$@"
