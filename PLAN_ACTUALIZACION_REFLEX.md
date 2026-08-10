# Plan de actualización de Reflex — Suite TUWAYKIAPP

> Documento vivo. Marcá cada casilla a medida que se completa. Objetivo: llevar toda la
> suite a **Reflex 0.9.8** de forma coordinada, sin romper producción, y dejar cada
> sistema completamente andando y verificado.
>
> **Fecha de inicio:** 2026-08-09 · **Responsable:** Trebor · **Versión objetivo:** Reflex 0.9.8
>
> **Estado de flota (act. 2026-08-10):**
> - 🟢 **Food — CERRADO Y DESPLEGADO.** Reflex 0.9.8 en local y prod (`food.tuwayki.app`), deploy Actions OK, E2E + cobro real verificados, emojis corregidos (local + prod CATBLACK). Solo restan ítems menores opcionales (sección 7).
> - 🟡 **Ventas** — 0.9.8 en rama `chore/reflex-0.9.8`; falta merge+deploy. *(otra sesión, va último)*
> - 🟡 **Life** — sigue en 0.9.4. *(otra sesión)*
> - ⏳ **Owner Panel** — cross-check de los 3 sistemas cuando Life y Ventas estén desplegados.

---

## 1. Contexto y objetivo

La suite comparte el paquete `tuwayki-core` (Food y Life lo usan; Ventas también) y se
administra desde el Owner Panel (vive en Sistema-de-Ventas). Queremos actualizar Reflex
de la línea 0.9.4/0.9.6 a **0.9.8** para ganar:

- **Parches de seguridad** (introducidos en 0.9.6): `starlette ≥1.3.1`, `python-multipart ≥0.0.32`,
  `granian ≥2.7.4`, `vite → 8.x` — tapan *path poisoning*, *DoS* y *header bypass*.
- **Fixes de Windows** (0.9.8): rutas de importación CSS, MIME de JS, corrupción de lockfile.
- **Calidad de vida**: `default_color_mode` sin flash, hashing de contenido en `rx.asset`,
  `frozen_lockfile`, lecturas de estado mutable 3-4× más rápidas.

### Hallazgos que reducen el riesgo (verificados 2026-08-09)

- ✅ **`tuwayki-core` es agnóstico a Reflex** — no lo importa ni lo pinnea. Actualizar Reflex
  en Food/Life **no obliga** a tocar el core. El orden de actualización queda desacoplado.
- ✅ **Cambios breaking oficiales 0.9.4→0.9.8**: solo se eliminó `REFLEX_USE_TURBOPACK`
  (env var muerta desde 0.8, **no se usa**). Cero impacto de API.
- ✅ **Única deprecación relevante**: `ArrayVar.foreach` → `.map`. Sigue funcionando (solo warning).
  En Food hay **1 sola** ocurrencia real (`app/pages/carta.py:1062`). Los 17 `rx.foreach(...)`
  restantes son el componente y **no** están deprecados.

### Riesgo por sistema

| Sistema | Riesgo | Motivo |
|---|---|---|
| **Ventas** | 🔴 Alto | +10 componentes extra (dataeditor, gridjs, markdown, moment, plotly, react-player, recharts, hosting-cli) + Owner Panel crítico |
| **Food** | 🟡 Medio | requirements/venv desincronizados; 1 deprecación; deploy a prod por rama |
| **Life** | 🟢 Bajo | Base 0.9.4 simple, menos superficie |
| **tuwayki-core** | 🟢 Nulo (por Reflex) | Agnóstico; solo re-validar que Food/Life/Ventas lo siguen importando bien |

---

## 2. Estado actual (verificado)

| Sistema | Pin en `requirements.txt` | Instalado en venv | Componentes extra |
|---|---|---|---|
| Food (`Sistema-para-Food`) | reflex==0.9.6.post1 | **0.9.4** ⚠️ desincronizado | code, core, lucide, radix, sonner |
| Ventas (`Sistema-de-Ventas`) | reflex==0.9.4 | (verificar) | +dataeditor, gridjs, markdown, moment, plotly, react-player, recharts, hosting-cli |
| Life (`Sistema-Gestion-Clinica`) | reflex==0.9.4 | (verificar) | (verificar) |
| tuwayki-core | — (sin reflex) | — | — |

**Pin de core en Food/Docker:** `git+...tuwayki-core.git@64850c8` (Dockerfile L26 y requirements.txt).

---

## 3. Set de versiones objetivo (Reflex 0.9.8)

Confirmadas del release 0.9.8:

```
reflex==0.9.8
reflex-base==0.9.8
reflex-components-core==0.9.8
reflex-components-code==0.9.3
reflex-components-lucide==1.0.3
reflex-components-radix==0.9.7
reflex-components-moment==0.9.3      # (Ventas)
reflex-components-plotly==0.9.4      # (Ventas)
reflex-components-recharts==0.9.2    # (Ventas)
reflex-docgen==0.9.4                 # (si se usa)
```

> ⚠️ **`sonner`, `dataeditor`, `gridjs`, `markdown`, `react-player`, `hosting-cli`**: versión
> compatible con 0.9.8 a resolver durante la ejecución. **Estrategia recomendada:** pinnear
> solo `reflex==0.9.8` + `reflex-base==0.9.8`, correr `pip install -U`, dejar que pip resuelva
> el resto, y luego re-pinnear con `pip freeze`. Evita el problema de sobre-fijar versiones.

---

## 4. Estrategia de orden

`tuwayki-core` es agnóstico a Reflex, así que **no es bloqueante**. Igual conviene este orden
para validar el eslabón compartido primero y dejar producción para el final:

1. **tuwayki-core** — smoke test contra Reflex 0.9.8 (no requiere cambios por Reflex).
2. **Food** — piloto (reconciliar venv, migrar deprecación, probar Docker).
3. **Life** — el más simple, valida el patrón en un segundo sistema.
4. **Ventas** — el más complejo, con toda la experiencia previa acumulada.
5. **Despliegue coordinado** de los tres.

> Trabajar cada sistema en su venv aislado. NO promover a `main`/`docker-deploy-prod` hasta
> tener tests + build Docker verdes localmente.

---

## FASE 0 — Preparación (transversal)

- [ ] Crear rama de trabajo en cada repo (o snapshot git) antes de tocar deps.
- [ ] Confirmar versión instalada real en cada venv: `pip show reflex` en Food, Ventas, Life.
- [ ] Leer changelog 0.9.5→0.9.8 una vez más para features que quieras adoptar (opcional).
- [ ] Definir ventana de despliegue (los push a prod los ejecuta Trebor manualmente).
- [ ] Backup de MySQL de cada entorno productivo antes de desplegar (el deploy-prod ya hace backup, pero confirmar).

---

## FASE 1 — tuwayki-core

`tuwayki-core` no depende de Reflex; el objetivo es solo **verificar que sigue importándose
y funcionando** bajo Reflex 0.9.8, y decidir si se re-pinnea a un commit nuevo.

- [ ] Revisar si hay commits nuevos en `tuwayki-core` que quieras incluir junto con esta actualización.
- [ ] Si NO hay cambios: mantener el pin `@64850c8` en Food/Life/Ventas (nada que hacer).
- [ ] Si SÍ hay cambios: actualizar el hash en los 3 `requirements.txt` y en el `Dockerfile` de cada sistema **de una sola vez**.
- [ ] Smoke test: en un venv con Reflex 0.9.8, `import tuwayki_core` y ejercitar `countries.py`, `utils/`, PDF (reportlab), DB (sqlmodel/aiomysql).

---

## FASE 2 — Food (piloto)

### 2.1 Reconciliar y actualizar deps
- [x] Actualizar `requirements.txt` al set 0.9.8 (sección 3). Reconcilia el desfase venv(0.9.4)/pin(0.9.6.post1). ✅
- [x] Recrear/actualizar el venv: `pip install -U -r requirements.txt` → reflex 0.9.8 instalado (venv estaba en 0.9.4). ✅
- [x] Verificar sin conflictos: `pip check` → "No broken requirements found". ✅
- [x] `sonner` confirmado en 0.9.1 (no se movió); resto del set 0.9.8 pinneado exacto. `import reflex` + `import tuwayki_core` OK. ✅

### 2.2 Migrar deprecación
- [x] `app/pages/carta.py:1062` — migrado `.to(list).foreach(...)` → `.to(list).map(...)`. ✅
- [x] Confirmado que NO quedan otros `.foreach(` de método (los 17 `rx.foreach(...)` quedan igual). ✅
- [x] Compilación con `-W` revisada: no aparecen DeprecationWarnings NUEVOS por la actualización. ✅

### 2.3 Compilar y probar en local
- [x] `reflex export --frontend-only` compila 100% sin errores (exit 0). ✅
- [x] Runtime interactivo verificado vía Docker (localhost:3003) + navegador — ver sección 7. ✅
- [ ] Regenerar lockfile si `frozen_lockfile` se queja (nuevo default en 0.9.7).
- [x] `pytest tests/` → **64 passed, 1 failed**. El único fallo es PREEXISTENTE y ajeno a Reflex (ver Incidencias #1). ✅
- [x] Smoke funcional navegador (parcial, sin credenciales) — ver sección 7. ✅

### 2.4 Build de producción (Docker) — OBLIGATORIO
- [x] `docker build` completo → imagen OK (558MB/161MB), exit 0. ✅
- [x] `docker compose up` (mysql + app) → app **healthy**, `GET /api/ping` → `{"pong":true}`. ✅
- [x] Frontend recompilado dentro del contenedor: Compiling 100% (54/53) + Production Build 100% (4/4). `.web/reflex.json` → `"version": "0.9.8"`. ✅
- [x] Backend confirmado en 0.9.8 dentro del contenedor. ✅
- [x] Sin errores nuevos en logs (los "Page X is being redefined" son preexistentes). ✅
- [ ] ⚠️ **Nota deploy** (ver Incidencia #3): el volumen persistente `food_web` cachea el frontend entre deploys.

---

## FASE 3 — Life (`Sistema-Gestion-Clinica`) — **DELEGADA a sesión paralela** 🔀

> ⚠️ **Life lo gestiona OTRA sesión.** No ejecutar desde esta sesión. Estado observado: sigue
> en **Reflex 0.9.4** (2026-08-09). Esta fila queda solo como referencia de estado de flota;
> el runbook/verificación de Life lo lleva su propia sesión.

---

## FASE 4 — Ventas (`Sistema-de-Ventas`) — **DELEGADA a sesión paralela** 🔀

> ⚠️ **Ventas lo gestiona OTRA sesión** con su propio runbook detallado:
> [`Sistema-de-Ventas/docs/REFLEX_098_UPGRADE_PLAN.md`](../Sistema-de-Ventas/docs/REFLEX_098_UPGRADE_PLAN.md).
> **No ejecutar Ventas desde esta sesión** para evitar pisar el trabajo. Esta fila queda solo
> como referencia de estado de flota.

Estado observado (2026-08-09, verificado desde afuera):
- [x] Ya en **Reflex 0.9.8** commiteado en rama `chore/reflex-0.9.8` (commit `3f286a4`). ✅
- [x] `pip check` limpio, `import reflex`+`tuwayki_core` OK. ✅
- [x] **0** usos del método `.foreach` deprecado (nada que migrar en Ventas). ✅
- [~] Su plan: FASE 1-5 hechas (pytest 1274 passed / 4 e2e fail preexistentes). Pendiente FASE 6 (verificación funcional), 7 (merge+push), 9/10 (deploy). SHOP va **último** en el orden de flota.
- Nota: Ventas instala el core desde `_vendor` local (editable) / CI desde SHA git; Food lo instala desde SHA git. Mecanismos distintos (ver Incidencia #4).

---

## FASE 5 — Despliegue coordinado

> Flujo git preferido (trunk-based, sin PR). Los push a prod los ejecuta Trebor manualmente
> (el auto-mode bloquea pushes a prod).

Orden de despliegue (de menor a mayor criticidad, o el que definas):

- [x] **Food**: `git push origin HEAD:main HEAD:docker-deploy-prod` (2026-08-10, FF limpio, ambas ramas en `f9bb1be`). GitHub Actions `deploy-prod.yml` → EC2: run `31406304383` **success (2m56s)**. Backup MySQL OK (88K), pip instaló reflex 0.9.8 + set completo, `food_mysql` y `tuwayki_food` healthy, health público `{"status":"ok","app":"tuwaykifood","db":{"ok":true}}`. ✅
- [x] ⚠️ Volumen `food_web`: el `deploy-prod.sh` NO lo recrea, PERO el entrypoint hace `rm -rf /app/.web` + `reflex init` en cada arranque → frontend recompila fresco igual. Resultado prod OK sin recrear el volumen a mano. (Para un deploy "de manual" se puede recrear igual; ver Incidencia #3.) ✅
- [x] Verificar `food.tuwayki.app` post-deploy: `/api/health` + `/api/ping` OK en vivo; **login dueño CATBLACK (lo hizo Trebor) → /admin + /carta renderizan con datos reales (123 productos) y emojis correctos, 0 mojibake**. Confirma que la migración de emojis (Incidencia #5) corrió y corrigió el dato en prod. ✅
- [ ] **Life**: mismo flujo → verificar post-deploy. *(otra sesión)*
- [ ] **Ventas**: mismo flujo → verificar POS + Owner Panel post-deploy. *(otra sesión)*
- [ ] Confirmar que el Owner Panel ve a los 3 sistemas correctamente tras el despliegue. *(cross-sistema, cuando Life y Ventas estén desplegados)*

> **FOOD: CERRADO Y DESPLEGADO (2026-08-10).** Local y producción corriendo al 100% sobre Reflex 0.9.8. Solo restan ítems menores opcionales (sección 7) y la flota (Life/Ventas, sus sesiones).

---

## 6. Rollback (por sistema)

- [ ] Tener a mano el commit previo (deps + código) para revertir.
- [ ] Si el deploy falla el healthcheck, el script de prod no promueve (verificar comportamiento).
- [ ] Revertir = `git revert`/reset del commit de deps + re-deploy de la imagen anterior.
- [ ] Restaurar backup MySQL solo si hubo migración de datos (esta actualización NO trae migraciones de schema).

---

## 7. Checklist de pruebas funcionales por sistema

### Food
**Verificado en navegador vs. contenedor 0.9.8 (localhost:3003), 2026-08-09:**
- [x] Página de login empleado (PASO 1) renderiza: logo, selección de restaurante, iconos lucide, tema radix. Assets 200, sin errores de consola reales. ✅
- [x] **Round-trip de estado (websocket) OK**: clic en restaurante → avanza a PASO 2 (rol Mozo/Cocina/Caja + teclado PIN). Confirma que el pipeline de eventos 0.9.8 funciona. ✅
- [x] Resolución de query params OK: el slug `empresa=pizzeria-don-luigi` se propaga en links (`/admin/login?empresa=…`). Cubre el code path de `RouterData.page` (Incidencia #2). ✅
- [x] Página admin/owner login (por email) renderiza: campos email/contraseña, "Ingresar al Panel", link a PIN. ✅
- [x] Handshake socket.io verificado a mano: `0{"sid":…,"pingTimeout":120000}`. El banner "Connection Error" es cosmético (panel oculto estrangula el socket); los eventos fluyen igual. ✅

**E2E adicional verificado (2026-08-09):**
- [x] Ruta pública `/menu/[slug]` (autopedido) ejecuta `on_load` end-to-end (websocket → backend → DB → estado → render). Manejo correcto del caso "carta no encontrada" para empresa sin productos (pizzeria-don-luigi = 0 productos). ✅
- [x] **App ↔ MySQL E2E (lectura)**: la página de login lista restaurantes reales desde `food_db.food_companies`; el menú consulta productos y decide render vs. not-found. DB round-trip vivo OK. ✅
- [x] Suite de integración `pytest` (pago, confirmar_cobro, turno_caja, descontar_stock, kardex, tenant_isolation, anulacion, promo, produccion) = **65/65 verdes** (el fallo preexistente quedó resuelto, Incidencia #1). Es el E2E de las rutas de dinero/stock contra DB. ✅
- Nota: mostrar un menú digital poblado requeriría habilitar el módulo de carta digital en una empresa (mutación de datos) — no se hizo por ser fuera de alcance de un test.

**E2E logueado + transacción real (2026-08-09, empresa TUWAYKIFOOD `admin@tuwaykifood.com`):**
- [x] **Login dueño (por email) OK** → redirect a `/admin`, panel Profesional con KPIs y datos reales. ✅
- [x] **Barrido de las 18 rutas autenticadas** (`/admin`, `/carta` 92 productos, `/caja` turno abierto, `/cocina`, `/mostrador`, `/mozos`, `/inventario`, `/reportes`, `/clientes`, `/cuentas`, `/cupones`, `/promociones`, `/usuarios`, `/configuracion`, `/estacion-impresion`) — todas renderizan con datos reales, **0 errores de consola**. ✅
- [x] **Transacción de escritura real contra MySQL vivo** (CRUD de producto): CREATE (id=199, S/9.99, cat Alitas) → READ en sesión nueva (92→93) → DELETE (→92). Ejercita SQLModel→SQLAlchemy→PyMySQL→MySQL 8 (Decimal, JSON, unique, utf8mb4). Base limpia, 0 residuo. ✅

**E2E completo + cobro real verificado (2026-08-10, empresa TUWAYKIFOOD `admin@tuwaykifood.com`):**
- [x] **Barrido completo re-verificado como humano**: login dueño → 18 pantallas (Panel del Dueño: Resumen/Reportes/Inventario+subtabs/Promociones/Clientes/Cuentas/Reservas/Delivery/Usuarios/Configuración+subtabs; operativo: Carta/Mozos+toma de comanda/Cocina/Caja/Mostrador/Estación impresión/Cupones; público: carta QR con slug de ruta). 0 errores de consola. ✅
- [x] **Alta de producto por UI real** (modal Carta → MySQL id=200 → borrado → 92). ✅
- [x] **Cobro REAL de punta a punta contra MySQL vivo** vía los MISMOS servicios que `confirmar_cobro` (`pago_service.validar_pagos/registrar_pagos_pedido/metodo_pago_resumen` + `_descontar_stock_por_pedido`): pedido #86, 2× Burger S/24 + propina S/5, efectivo S/29 → turno 9, mesa liberada, pago registrado. Verificado desde sesión nueva y **revertido** (DB en baseline). Respalda los 7 escenarios de `test_confirmar_cobro.py` (65/65). ✅
- [x] **Logout OK** (redirect a `/admin/login`). ✅
- Nota entorno: el panel del navegador headless dropea el websocket a mitad de flujos multi-paso, por eso el cobro se cerró a nivel servicios (determinístico) en vez de clic-a-clic — misma lógica de negocio.

**Pendiente (opcional, no bloquea — para después):**
- [ ] Impresión/PDF (reportlab) y subida de imágenes (uploaded_files).
- [ ] Tema claro/oscuro sin flash (`default_color_mode` nuevo, opcional).
- [ ] Cobro completo clic-a-clic por UI (nice-to-have; la lógica ya está verificada a nivel servicios + tests).

### Life
- [ ] Flujos core de clínica (agenda/pacientes) sin regresiones.
- [ ] Reportes/PDF.

### Ventas
- [ ] POS: venta completa.
- [ ] Owner Panel: alta/gestión de empresas contra los 3 productos.
- [ ] Componentes de datos (grid/dataeditor) y gráficos (plotly/recharts).

---

## 8. Registro de incidencias

| # | Fecha | Sistema | Problema | Estado / Solución |
|---|---|---|---|---|
| 1 | 2026-08-09 | Food | `pytest`: `test_bloqueo_empresa_suspendida_o_inexistente` falla. `evaluar_bloqueo(None,...)` devuelve `"Empresa no encontrada — contacte soporte."` pero el test espera `MSG_SUSPENDIDA`. **PREEXISTENTE, ajeno a Reflex** (archivo `suscripcion_service.py` no se tocó). | ✅ **RESUELTO** (2026-08-09): la conducta del código es la correcta (None = no encontrada ≠ suspendida). Se promovió el string a constante `MSG_NO_ENCONTRADA` y se alineó el test. Suite: **65 passed, 0 failed**. |
| 2 | 2026-08-09 | Food | `DeprecationWarning: RouterData.page` (deprecado desde 0.8.1, remoción en 1.0). 7 usos en `food_state.py` y `self_order_state.py`. **PREEXISTENTE.** Trampa detectada: `.url.query_parameters` = solo query params (`parse_qsl`), NO los params de RUTA dinámica (`slug` en `/menu/[slug]`). | ✅ **RESUELTO** (2026-08-09): el reemplazo correcto es `self.router.page` → `self.router._page` (el campo que la property deprecada devuelve internamente, y que Reflex mismo usa para dynamic route args en `state.py:1379`). Conducta **1:1** (incluye params de ruta Y query), sin warning. 7 sitios migrados. **Verificado en vivo:** menú QR `/menu/tuwaykifoodsac2305?mesa=1` renderiza 92 productos + promo (slug de ruta ✅ + mesa query ✅); `/clientes` logueado usa el computed var `_page.path` ✅; compile OK; warning 0 en runtime; 65/65 tests. |
| 3 | 2026-08-09 | Food (deploy) | El servicio monta un volumen persistente `food_web:/app/.web` (docker-compose.yml:74). Tras un bump de versión, en el primer arranque el contenedor puede servir brevemente el frontend viejo cacheado a clientes ya conectados → warning `Frontend version X does not match backend`. Reflex **recompila solo** al detectar el cambio (verificado: `.web` quedó en 0.9.8), así se auto-cura; el warning solo afecta pestañas ya abiertas con caché vieja. | **Benigno.** Recomendación para deploy limpio: al desplegar 0.9.8 en prod, **recrear el volumen** (`docker volume rm <proj>_food_web` con el stack abajo, o `docker compose down` sin `-v` NO alcanza) para forzar build fresco. Clientes con pestaña abierta: hard-refresh (Ctrl+Shift+R). Añadir a checklist Fase 5. |
| 4 | 2026-08-09 | Suite (higiene) | **Drift del pin de `tuwayki-core` entre sistemas:** Food fija `@64850c8` (requirements.txt + Dockerfile), Ventas/SHOP fija `@ef852f2` en CI. Commits distintos → los sistemas pueden correr contra versiones diferentes del core. **PREEXISTENTE, ajeno a Reflex.** | Fuera de alcance del upgrade de Reflex (regla de oro: el core no se toca en este rollout). Cleanup futuro coordinado: unificar el SHA del core en los 3 sistemas y re-testear. |
| 5 | 2026-08-10 | Food (datos) | **Emojis de producto doble-codificados (mojibake).** `food_productos.emoji` (y `food_combos.emoji`) tenían el emoji UTF-8 re-codificado como windows-1252 (ej: 🍔 `F0 9F 8D 94` guardado como `C3B0C5B8C28DE2809D`, se veía "ðŸ”" en Carta/Mozos/Mostrador/menú QR). **PREEXISTENTE, ajeno a Reflex**: origen import/restore histórico; el alta nueva por el modal guarda bien. `fix_encoding.sql` NO aplica (usa latin1; la corrupción es cp1252 con `Ÿ`/`”`). | ✅ **RESUELTO** (2026-08-10): migración Alembic `r8m9n0o1p2q3` que revierte en Python (windows-1252 WHATWG con fallback C1), **idempotente** y autocontenida, con guardarraíl `assert` contra el caso 🍔. Auto-aplica a prod vía `alembic upgrade head` del entrypoint. Verificado local (184/184 filas, 0 mojibake, re-run = 0 cambios, /carta y /menu OK) **y en PROD** (CATBLACK: 123 productos, 0 mojibake). Commiteada y desplegada. |
| 6 | 2026-08-10 | Food (Tailwind) | **Clases CSS de componentes compartidos no se generaban.** Reflex 0.9.x compila páginas/componentes compartidos a `.web/app_components/**`, dir que NO entra en el content-glob por defecto de Tailwind v4 (`./app/**`, `./utils/**`); con `@config`, Tailwind v4 usa content explícito y NO auto-detecta. Riesgo: estilos faltantes en clases usadas solo en `app_components`. | ✅ **RESUELTO** por Trebor (commit `f9bb1be`): `TailwindV4Plugin(config={content:[app, app_components, components, utils], plugins:[typography]})` en `rxconfig.py`, coherente con SHOP. Incluido en el deploy 0.9.8; prod verificado (login + carta renderizan con estilos). |

---

## 9. Notas / decisiones

- `tuwayki-core` desacoplado de Reflex → no bloquea la actualización.
- Sobre-fijar `reflex-components-*` es la principal fuente de fricción: preferir resolver con pip y re-pinnear con `freeze`.
- Esta actualización **no incluye migraciones de base de datos**.
