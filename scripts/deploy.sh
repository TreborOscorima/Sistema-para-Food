#!/usr/bin/env bash
# =============================================================================
# scripts/deploy.sh — Deploy Docker para TUWAYKIFOOD
#
# Uso:
#   bash scripts/deploy.sh              # Deploy completo (build + up -d)
#   bash scripts/deploy.sh --rollback   # Rollback al commit anterior
#
# Variables de entorno opcionales:
#   APP_DIR        Directorio de la app (default: directorio del script/../)
#   BRANCH         Branch de git a desplegar (default: docker-deploy-prod)
#   FOOD_PORT      Puerto del contenedor (default: 3003)
#   VENDOR_DIR     Directorio de tuwayki-core para copiar en _vendor/ (default: ../tuwayki-core)
# =============================================================================
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

info()  { echo -e "${CYAN}[INFO]${NC}  $*"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
fail()  { echo -e "${RED}[FAIL]${NC}  $*"; exit 1; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="${APP_DIR:-$(cd "$SCRIPT_DIR/.." && pwd)}"
BRANCH="${BRANCH:-docker-deploy-prod}"
FOOD_PORT="${FOOD_PORT:-3003}"
VENDOR_DIR="${VENDOR_DIR:-$(cd "$APP_DIR/../tuwayki-core" && pwd 2>/dev/null || echo '')}"
IS_ROLLBACK=false

for arg in "$@"; do
    case "$arg" in
        --rollback) IS_ROLLBACK=true ;;
    esac
done

cd "$APP_DIR"
info "Deploy TUWAYKIFOOD en: $APP_DIR"
info "Branch: $BRANCH | Puerto: $FOOD_PORT"

# ─── 0. Prerrequisitos ───────────────────────────────────────────────────────
command -v docker          >/dev/null 2>&1 || fail "docker no encontrado"
command -v docker-compose  >/dev/null 2>&1 || \
    (docker compose version >/dev/null 2>&1) || fail "docker-compose no encontrado"
command -v git             >/dev/null 2>&1 || fail "git no encontrado"

[[ -f ".env" ]] || fail "No existe .env — copiar .env.example y configurar"

COMPOSE_CMD="docker-compose"
docker compose version >/dev/null 2>&1 && COMPOSE_CMD="docker compose"

# ─── 1. Guardar commit actual (para rollback) ───────────────────────────────
PREV_COMMIT="$(git rev-parse HEAD)"
info "Commit actual: $PREV_COMMIT"

# ─── 2. Rollback? ────────────────────────────────────────────────────────────
if $IS_ROLLBACK; then
    [[ -f ".deploy_prev_commit" ]] || fail "No se encontró .deploy_prev_commit — rollback manual necesario"
    ROLLBACK_TO="$(cat .deploy_prev_commit)"
    warn "ROLLBACK a commit: $ROLLBACK_TO"
    git reset --hard "$ROLLBACK_TO"
else
    echo "$PREV_COMMIT" > .deploy_prev_commit
fi

# ─── 3. Actualizar código ────────────────────────────────────────────────────
if ! $IS_ROLLBACK; then
    info "Actualizando código desde origin/$BRANCH..."
    git fetch origin "$BRANCH"
    git reset --hard "origin/$BRANCH"
    NEW_COMMIT="$(git rev-parse HEAD)"
    ok "Código actualizado a: $NEW_COMMIT"
    [[ "$PREV_COMMIT" == "$NEW_COMMIT" ]] && warn "Sin cambios nuevos (mismo commit)"
fi

# ─── 4. Copiar vendor (tuwayki-core) ─────────────────────────────────────────
if [[ -n "$VENDOR_DIR" && -d "$VENDOR_DIR" ]]; then
    info "Copiando tuwayki-core desde $VENDOR_DIR..."
    mkdir -p "$APP_DIR/_vendor"
    cp -r "$VENDOR_DIR" "$APP_DIR/_vendor/tuwayki-core"
    ok "tuwayki-core copiado a _vendor/"
else
    # Si ya existe de un deploy anterior, OK; sino es un warning
    if [[ -d "$APP_DIR/_vendor/tuwayki-core" ]]; then
        warn "VENDOR_DIR no disponible — usando _vendor/ existente"
    else
        warn "tuwayki-core no encontrado en $VENDOR_DIR — el build puede fallar si no está en _vendor/"
    fi
fi

# ─── 5. Build de imagen Docker ───────────────────────────────────────────────
info "Construyendo imagen tuwayki_food:latest..."
docker build --no-cache -t tuwayki_food:latest .
ok "Imagen construida"

# ─── 6. Levantar contenedor ──────────────────────────────────────────────────
info "Levantando contenedor (docker compose up -d)..."
$COMPOSE_CMD up -d
ok "Contenedor iniciado"

# ─── 7. Esperar health check ─────────────────────────────────────────────────
MAX_WAIT=300
WAITED=0
info "Esperando /api/ping en puerto $FOOD_PORT (máx ${MAX_WAIT}s)..."
while [[ $WAITED -lt $MAX_WAIT ]]; do
    if curl -sf "http://127.0.0.1:${FOOD_PORT}/api/ping" >/dev/null 2>&1; then
        break
    fi
    sleep 3
    WAITED=$((WAITED + 3))
done

if [[ $WAITED -ge $MAX_WAIT ]]; then
    warn "App no respondió en ${MAX_WAIT}s — revisando logs..."
    docker logs tuwayki_food --tail 30 || true
    fail "Deploy falló — contenedor no respondió"
fi
ok "App respondiendo en puerto $FOOD_PORT (tardó ~${WAITED}s)"

# ─── 8. Smoke quick check ────────────────────────────────────────────────────
HEALTH="$(curl -sf "http://127.0.0.1:${FOOD_PORT}/api/health" || echo '{}')"
echo "  health: $HEALTH"

# ─── 9. Resumen ──────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  DEPLOY TUWAYKIFOOD COMPLETADO${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo "  Commit:   $(git rev-parse --short HEAD)"
echo "  Branch:   $BRANCH"
echo "  App:      http://127.0.0.1:${FOOD_PORT}"
echo "  Health:   http://127.0.0.1:${FOOD_PORT}/api/health"
echo "  Logs:     docker logs tuwayki_food -f"
echo "  Rollback: bash scripts/deploy.sh --rollback"
echo ""
