#!/usr/bin/env bash
# =============================================================================
# scripts/configure-npm-upload.sh
#
# Configura client_max_body_size en Nginx Proxy Manager para permitir uploads
# de imágenes > 1 MB (default de NPM). Usa la API REST de NPM.
#
# Variables de entorno requeridas:
#   NPM_EMAIL      Email del admin de NPM
#   NPM_PASSWORD   Password del admin de NPM
#
# Opcionales:
#   NPM_API_URL    URL base de la API NPM (default: http://localhost:81/api)
#   NPM_DOMAIN     Dominio del proxy host (default: food.tuwayki.app)
#   NPM_MAX_BODY   Valor de client_max_body_size (default: 10m)
#
# Uso:
#   NPM_EMAIL=admin@example.com NPM_PASSWORD=pass bash scripts/configure-npm-upload.sh
#   # o con las variables en .env:
#   source .env && bash scripts/configure-npm-upload.sh
# =============================================================================
set -euo pipefail

CYAN='\033[0;36m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
info()  { echo -e "${CYAN}[NPM-CFG]${NC} $*"; }
ok()    { echo -e "${GREEN}[NPM-CFG]${NC} $*"; }
warn()  { echo -e "${YELLOW}[NPM-CFG]${NC} $*"; }

NPM_API="${NPM_API_URL:-http://localhost:81/api}"
NPM_EMAIL="${NPM_EMAIL:-}"
NPM_PASSWORD="${NPM_PASSWORD:-}"
DOMAIN="${NPM_DOMAIN:-food.tuwayki.app}"
MAX_BODY="${NPM_MAX_BODY:-10m}"

# ── Pre-check ────────────────────────────────────────────────────────────────
if [[ -z "$NPM_EMAIL" || -z "$NPM_PASSWORD" ]]; then
    warn "NPM_EMAIL / NPM_PASSWORD no definidos — omitiendo config upload size"
    warn "Fix manual: NPM UI → Proxy Hosts → $DOMAIN → Advanced → client_max_body_size $MAX_BODY;"
    exit 0
fi

command -v curl >/dev/null 2>&1 || { warn "curl no encontrado — omitiendo"; exit 0; }

# ── 1. Auth ──────────────────────────────────────────────────────────────────
info "Autenticando en NPM ($NPM_API)..."
TOKEN_JSON=$(curl -sf -X POST "$NPM_API/tokens" \
    -H "Content-Type: application/json" \
    -d "{\"identity\":\"$NPM_EMAIL\",\"secret\":\"$NPM_PASSWORD\"}" 2>/dev/null || true)

if [[ -z "$TOKEN_JSON" ]]; then
    warn "No se pudo conectar a NPM API (¿puerto 81 accesible?) — omitiendo"
    exit 0
fi

TOKEN=$(python3 -c "import sys,json; print(json.loads(sys.argv[1])['token'])" "$TOKEN_JSON" 2>/dev/null || true)
if [[ -z "$TOKEN" ]]; then
    warn "Auth NPM falló — verificar NPM_EMAIL/NPM_PASSWORD"
    exit 0
fi
ok "Auth OK"

# ── 2. Buscar proxy host ────────────────────────────────────────────────────
info "Buscando proxy host: $DOMAIN..."
HOSTS_JSON=$(curl -sf "$NPM_API/nginx/proxy-hosts" \
    -H "Authorization: Bearer $TOKEN" 2>/dev/null || true)

if [[ -z "$HOSTS_JSON" ]]; then
    warn "No se pudieron listar proxy hosts — omitiendo"
    exit 0
fi

HOST_INFO=$(python3 -c "
import sys, json
hosts = json.loads(sys.argv[1])
domain = sys.argv[2]
for h in hosts:
    if domain in h.get('domain_names', []):
        print(json.dumps({
            'id': h['id'],
            'advanced_config': h.get('advanced_config') or '',
            'domain_names': h['domain_names'],
            'forward_scheme': h.get('forward_scheme', 'http'),
            'forward_host': h.get('forward_host', ''),
            'forward_port': h.get('forward_port', 80),
            'certificate_id': h.get('certificate_id', 0),
            'ssl_forced': h.get('ssl_forced', False),
            'hsts_enabled': h.get('hsts_enabled', False),
            'hsts_subdomains': h.get('hsts_subdomains', False),
            'http2_support': h.get('http2_support', False),
            'block_exploits': h.get('block_exploits', False),
            'caching_enabled': h.get('caching_enabled', False),
            'allow_websocket_upgrade': h.get('allow_websocket_upgrade', False),
            'access_list_id': h.get('access_list_id', '0'),
            'enabled': h.get('enabled', 1),
            'meta': h.get('meta', {}),
            'locations': h.get('locations', []),
        }))
        break
" "$HOSTS_JSON" "$DOMAIN" 2>/dev/null || true)

if [[ -z "$HOST_INFO" ]]; then
    warn "Proxy host '$DOMAIN' no encontrado en NPM — omitiendo"
    exit 0
fi

HOST_ID=$(python3 -c "import sys,json; print(json.loads(sys.argv[1])['id'])" "$HOST_INFO")
CURRENT_ADV=$(python3 -c "import sys,json; print(json.loads(sys.argv[1])['advanced_config'])" "$HOST_INFO")
ok "Proxy host encontrado (ID=$HOST_ID)"

# ── 3. Verificar si ya está configurado ─────────────────────────────────────
if echo "$CURRENT_ADV" | grep -q "client_max_body_size"; then
    ok "client_max_body_size ya configurado — sin cambios"
    exit 0
fi

# ── 4. Aplicar config ───────────────────────────────────────────────────────
info "Aplicando client_max_body_size $MAX_BODY..."

UPDATED_JSON=$(python3 -c "
import sys, json
h = json.loads(sys.argv[1])
directive = 'client_max_body_size ' + sys.argv[2] + ';'
prev = h.get('advanced_config', '')
h['advanced_config'] = directive + ('\n' + prev if prev else '')
del h['id']
print(json.dumps(h))
" "$HOST_INFO" "$MAX_BODY")

RESPONSE=$(curl -sf -X PUT "$NPM_API/nginx/proxy-hosts/$HOST_ID" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "$UPDATED_JSON" 2>/dev/null || true)

if echo "$RESPONSE" | grep -q "\"id\":"; then
    ok "client_max_body_size $MAX_BODY configurado en $DOMAIN"
else
    warn "Error actualizando proxy host — configurar manualmente"
    warn "NPM UI → Proxy Hosts → $DOMAIN → Advanced → client_max_body_size $MAX_BODY;"
    [[ -n "${RESPONSE:-}" ]] && echo "  Respuesta: $RESPONSE"
fi
