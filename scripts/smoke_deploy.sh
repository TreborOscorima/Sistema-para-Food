#!/usr/bin/env bash
# =============================================================================
# scripts/smoke_deploy.sh — Smoke test post-deploy TUWAYKIFOOD
#
# Uso:
#   bash scripts/smoke_deploy.sh                          # Local (port 3003)
#   bash scripts/smoke_deploy.sh http://IP:3003           # Test server
#   bash scripts/smoke_deploy.sh https://food.tuwayki.com # Producción
# =============================================================================
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

PASS=0
FAIL=0
WARN=0

for arg in "$@"; do
    case "$arg" in
        http*) BASE_URL="$arg" ;;
    esac
done

BASE_URL="${BASE_URL:-http://127.0.0.1:3003}"

info()   { echo -e "${CYAN}[TEST]${NC}  $*"; }
pass()   { echo -e "${GREEN}[PASS]${NC}  $*"; PASS=$((PASS + 1)); }
fail_t() { echo -e "${RED}[FAIL]${NC}  $*"; FAIL=$((FAIL + 1)); }
warn_t() { echo -e "${YELLOW}[WARN]${NC}  $*"; WARN=$((WARN + 1)); }

check_url() {
    local url="$1" expected="${2:-200}" desc="${3:-$1}"
    local code
    code="$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 "$url" 2>/dev/null)"
    if [[ "$code" == "$expected" ]]; then
        pass "$desc -> $code"
    elif [[ "$code" == "000" ]]; then
        fail_t "$desc -> TIMEOUT/CONNECTION_REFUSED"
    else
        fail_t "$desc -> $code (esperado: $expected)"
    fi
}

check_health() {
    local url="$1/api/health" desc="${2:-Health check}"
    local response status
    response="$(curl -sf --max-time 10 "$url" 2>/dev/null || echo '')"
    if [[ -z "$response" ]]; then
        fail_t "$desc -> sin respuesta"; return
    fi
    status="$(echo "$response" | python3 -c 'import sys,json; print(json.load(sys.stdin).get("status",""))' 2>/dev/null || echo '')"
    if [[ "$status" == "ok" ]]; then
        pass "$desc -> ok"
        echo "       $response"
    else
        fail_t "$desc -> status='$status' ($response)"
    fi
}

echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  TUWAYKIFOOD Smoke Test — $(date +%Y-%m-%d\ %H:%M:%S)${NC}"
echo -e "${CYAN}  Base URL: $BASE_URL${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo ""

info "=== API ==="
check_health "$BASE_URL" "Health check"
check_url "$BASE_URL/api/ping" 200 "Ping"

info "=== Frontend ==="
check_url "$BASE_URL/" 200 "Raíz /"
content_type="$(curl -s -o /dev/null -w '%{content_type}' --max-time 10 "$BASE_URL/" 2>/dev/null)"
if [[ "$content_type" == *"text/html"* ]]; then
    pass "Content-Type / es text/html"
else
    warn_t "Content-Type / es '$content_type' (esperado: text/html)"
fi

info "=== Páginas principales ==="
check_url "$BASE_URL/login"        200 "Login (PIN)"
check_url "$BASE_URL/dono/login"   200 "Login dueño"
check_url "$BASE_URL/mozos"        200 "Mozos"
check_url "$BASE_URL/cocina"       200 "Cocina"
check_url "$BASE_URL/caja"         200 "Caja"
check_url "$BASE_URL/configuracion" 200 "Configuracion"

echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
TOTAL=$((PASS + FAIL + WARN))
echo -e "  Total: $TOTAL | ${GREEN}Pass: $PASS${NC} | ${RED}Fail: $FAIL${NC} | ${YELLOW}Warn: $WARN${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo ""

if [[ $FAIL -gt 0 ]]; then
    echo -e "${RED}  HAY FALLOS — revisar antes de confirmar el deploy${NC}"
    exit 1
else
    echo -e "${GREEN}  TODAS LAS PRUEBAS PASARON${NC}"
    exit 0
fi
