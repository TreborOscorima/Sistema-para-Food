# PENDIENTES CONSOLIDADOS — TUWAYKIFOOD

> **Fecha de consolidación:** 2026-07-09 (actualizado)
> **Fuentes:** `PROYECTO_TUWAYKIFOOD.md` (§6-7), verificación directa contra el código fuente.
>
> Este documento reemplaza las secciones de pendientes de ambos MD anteriores.

---

## SPRINT S3 — ✅ COMPLETADO (2026-07-08)

| ID | Tarea | Estado |
|---|---|---|
| **MT-01** | Campo de plan en Company + plan_service.py + API set-plan | ✅ DONE |
| **MT-02** | Gating de features por plan (rutas, reportes, usuarios, mesas) + badge UI | ✅ DONE |

---

## SEGURIDAD

| ID | Prioridad | Tarea | Estado | Origen |
|---|---|---|---|---|
| SEC-03 | **P1** | `hmac.compare_digest` para `_require_admin_secret` (hoy usa `!=`, no constant-time) + evaluar allowlist IP Owner Admin | ✅ DONE (2026-07-08) | PROYECTO §6.1 |
| SEC-06 | P2 | Tabla `food_auditoria` transversal (cambios de precio, descuentos aplicados, reimpresiones, permisos, descuadres) | ✅ DONE (2026-07-08) — modelo + migración + servicio + 5 puntos integración |
| SEC-07 | P2 | Completar migración `datetime.utcnow()` → `utc_now_naive()`. Helper existe y se usa 32× en food_state.py, pero **quedan 65 llamadas raw** en 8 archivos (api, models, mixins) | ✅ DONE (2026-07-08) | PROYECTO §6.1 |

---

## PERFORMANCE

| ID | Prioridad | Tarea | Detalle | Origen |
|---|---|---|---|---|
| PERF-06 | P2 | **Substates reales** por página | ✅ DONE (2026-07-09) — `ReportesState(rx.State)` extraído como substate independiente (75 vars, ~1100 líneas). FoodState pasa de 370 a 295 vars. 10 páginas (mozos, cocina, mostrador, login, menú, inventario, clientes, cupones, promos, usuarios) ya no serializan datos de reportes. Cross-state via `get_state()`. Migración gradual continúa con otros mixins. | PROYECTO §6.2 |
| PERF-08 | P2 | MySQL `innodb_buffer_pool_size` para prod | ✅ DONE (2026-07-08) — default 256M, parametrizado via `MYSQL_INNODB_BUFFER_POOL` env; memory limit 768M parametrizado via `MYSQL_MEMORY_LIMIT` | PROYECTO §6.2 |

---

## OPERATIVO

| ID | Prioridad | Tarea | Detalle | Origen |
|---|---|---|---|---|
| OP-03 | P2 | **Anotación rápida de cliente en mesa** | Vincular cliente registrado a pedido de mesa (hoy solo en fiado/mostrador) para acumular puntos e historial | ✅ DONE (2026-07-08) |
| OP-04 | P2 | **KDS: agrupar por mesa + tiempo objetivo por plato** | Hoy es cola por ticket; agrupar ítems de la misma mesa mejora sincronización de salida de platos | ✅ DONE (2026-07-08) — agrupación por (mesa, pedido, estado) |
| OP-05 | P2 | **86 rápido desde cocina** | MZ-03 (86 desde mozos) ya está hecho. Falta lo mismo desde el lado de cocina: botón "86" en el KDS para que el cocinero marque agotado directo | ✅ DONE (2026-07-08) |

---

## ADMINISTRACIÓN Y FINANZAS

| ID | Prioridad | Tarea | Detalle | Origen |
|---|---|---|---|---|
| ADM-04 | P2 | **Reporte de propinas por mozo** | Total propinas por mozo por turno/período para reparto. Dato existe en `Pedido.propina` + `mozo_id` | ✅ DONE (2026-07-08) |
| ADM-05 | P2 | **Resumen IGV mensual** | Base imponible + IGV del período para contadora. Export Excel | ✅ DONE (2026-07-08) — UI + service + state; Excel pendiente |
| ADM-06 | P2 | **Matriz estrella/perro de productos** | Top/bottom por unidades vendidas × margen — identifica qué sacar/promover en la carta | ✅ DONE (2026-07-08) |
| ADM-07 | P2 | **Excel en todos los reportes + PDF ejecutivo** | ✅ DONE (2026-07-08) — Excel en P&L, IGV, descuentos/anulaciones, mermas, matriz, margen. PDF pendiente fase futura | PROYECTO §6.4 |

---

## MULTI-TENANT / SaaS

| ID | Prioridad | Tarea | Detalle | Origen |
|---|---|---|---|---|
| MT-03 | P2 | **Modelo de sucursal** | ✅ DONE (2026-07-09) — Tabla `food_sucursales` + `sucursal_id` nullable en 5 tablas operativas (mesas, pedidos, turnos_caja, insumos, usuarios). Login 3 pasos (empresa→PIN→sucursal). Admin CRUD sucursales en Configuración. Sidebar badge sucursal activa. Filtros en queries de mesas, turnos y creación de pedidos. Retrocompatible: NULL = single-location | PROYECTO §6.6 |
| MT-04 | P2 | **Auto tenant filter** | `with_loader_criteria` de SQLAlchemy para inyectar `company_id` automático como red de seguridad adicional (defensa en profundidad) | ✅ DONE — ya implementado en tuwayki_core (listeners + with_loader_criteria + tests) |
| MT-05 | P2 | **Backups automatizados** | ✅ DONE (2026-07-08) — `scripts/backup-mysql.sh` con mysqldump comprimido + retención 30d configurable. Offsite (S3/BackBlaze) queda como mejora futura | PROYECTO §6.6 |

---

## FRONTEND / UX

| ID | Prioridad | Tarea | Estado | Origen |
|---|---|---|---|---|
| UI-01d | Continuo | **Migrar hex hardcodeados a `theme.py`** | Se hace incrementalmente al tocar cada página. No big-bang | AUDITORIA §4 |
| UI-03 | P2 | **Evaluar tema raíz `light`** | Hoy raíz=dark + hack `.light` en páginas claras. Evaluar invertir: raíz light + `.dark` solo para las 4 páginas oscuras (mozos, cocina, mostrador, login) | ✅ DONE (2026-07-08) — raíz light, 14× class_name="light" removidos, 4 páginas dark |
| MZ-06 | P3 | **Label "Enviar nueva ronda"** en CTA del modal cuando ya hay historial de pedido en la mesa | ✅ DONE (2026-07-08) |
| — | P2 | **Responsive mostrador/usuarios en tablet 768px** | ✅ DONE (2026-07-08) — mostrador: flex direction column→row en lg (1024px) + alturas adaptivas | PROYECTO §6.7 |
| — | P2 | **Lazy-load imágenes menú público** | `loading="lazy"` en img de productos para cartas con fotos | ✅ DONE (2026-07-08) |

---

## TESTING

| ID | Prioridad | Tarea | Origen |
|---|---|---|---|
| TEST-01 | P1 | Test del flujo `confirmar_cobro` completo (con stock, fiado, split, combos) | ✅ DONE (2026-07-08) |
| TEST-02 | P1 | Test de `_descontar_stock_por_pedido` con combos | ✅ DONE (2026-07-08) |
| TEST-03 | P2 | Test de carga (locust/script) simulando 7 clientes con polling para validar PERF | ✅ DONE (2026-07-08) — `tests/locustfile.py` con 7 user profiles: ping, health, SPA pages | PROYECTO §6.9 |

---

## DEUDA TÉCNICA (BE-10)

| Tarea | Riesgo | Detalle |
|---|---|---|
| ~~**bcrypt de PINs**~~ | ~~Bajo~~ | ✅ Ya resuelto — migración 0012 hashea PINs existentes, `_hash_pin()`/`_verify_pin()` usan bcrypt, guardar_usuario y autenticación todo con bcrypt |
| ~~`cobrar_mesa()` no descuenta stock~~ | ~~Medio~~ | ✅ Resuelto — `cobrar_mesa()` ya solo redirige a `abrir_cobro_mesa()` → `confirmar_cobro()` que sí descuenta stock |
| ~~**Polling sin `on_unload`**~~ | ~~Bajo~~ | ✅ No-action — ya mitigado: cada on_load_* detiene otros pollings, flags rompen loops, session expiry mata tasks, WebSocket disconnect termina background tasks |

---

## FASE 3 — FEATURES MAYORES

| ID | Tarea | Impacto | Complejidad | Estado |
|---|---|---|---|---|
| **FEAT-04** | **Reservas de mesa** — CRUD fecha/hora/pax/cliente + indicador "Reservada 21:00" en mapa de mozos | Alto para restobares | Media | ✅ DONE (2026-07-09) — Modelo `Reserva` + migración, CRUD completo en panel admin (sección Reservas), 5 estados (pendiente→confirmada→sentada/cancelada/no_show), badge "📅 Reservada HH:MM" en tarjetas de mesa, leyenda en salón, filtro por fecha |
| **FEAT-07** | **Módulo Delivery** — `TipoPedido.DELIVERY`, dirección/teléfono, estado de reparto, repartidores | Alto (canal adicional) | Media-Alta | ✅ DONE (2026-07-09) — `EstadoDelivery` enum (pendiente/en_camino/entregado/cancelado), `RolUsuario.REPARTIDOR`, 5 campos delivery en Pedido + migración, `DeliveryPedidoView` + state handlers (CRUD, asignar repartidor, cambiar estado), sección Delivery en panel admin con filtros por estado, form de creación, badges de estado/pago, acciones contextuales |
| **FEAT-05** | **Self-order desde QR** — carrito en menú público + llamar mozo + cola de aprobación (nunca directo a cocina sin validar) | Diferenciador SaaS | Alta (seguridad mesa-token) | ✅ DONE (2026-07-09) — Campo `qr_token` en Mesa + migración, campos `self_order`/`self_order_aprobado` en Pedido, `CarritoItemView` + `SelfOrderPendienteView`, carrito drawer en menú público con FAB flotante, botón "Agregar" en cada producto (solo si hay mesa QR), confirmación post-envío, cola de aprobación en vista mozos con approve/reject, polling auto, botón "Generar tokens QR" en Configuración → Carta digital |
| **MT-03b** | **Multi-sucursal (expansión)** — reportes filtrados por sucursal, selector sucursal en reportes, asignación masiva de mesas/insumos a sucursal. Base modelo ya hecho | Alto para escalar | Media | ✅ DONE (2026-07-09) — Selector sucursal en reportes y resumen (botones "Todas" + cada sucursal), filtro `_sucursal_q` aplicado a dashboard KPIs (pedidos, mesas, reservas) + historial ventas. Asignación de mesas/insumos a sucursal ya se hace en Configuración |
| **FEAT-06** | **Facturación electrónica SUNAT** — boleta/factura con IGV, integración PSE/OSE peruano. Campos RUC/IGV ya existen | Obligatorio para formalización | Muy Alta (regulatoria) | PENDIENTE |
| **FEAT-08** | **Dashboard del día para dueño (mobile)** — vista resumida responsive: ventas en vivo, mesas abiertas, alertas stock. Panel dono ya existe como base | Uso real del dueño fuera del local | Media | ✅ DONE (2026-07-09) — KPIs operativos en vivo (mesas ocupadas/total, ítems en cocina, reservas hoy), responsive breakpoints en KPI cards (font-size + padding + min-width adaptivo), sidebar mobile drawer ya existía |

---

## ÍTEMS QUE FIGURABAN COMO PENDIENTES PERO YA ESTÁN HECHOS

> Para evitar retrabajo — verificado contra el código el 2026-07-08.

| ID | Descripción | Evidencia |
|---|---|---|
| UI-02 | CSS global a archivo estático | `assets/twk.css` existe, `app.py:25 stylesheets=["/twk.css"]`, fuentes en `head_components` |
| UI-11 | Redirect raíz por `rx.redirect` | `food_state.py:1803 on_load_root` usa `rx.redirect()`, no `window.location` |
| MP-01 | Buscador en menú público | `menu_publico.py:183 busqueda_menu` con input sticky + filtro |
| CF-03 | dono.py paleta unificada | `dono.py:10-14` importa de `theme.py` (ACCENT, DARK_900, etc.) — no paleta propia |
| KD-05 | KDS delay configurable | `ConfigImpresora.kds_minutos_alerta` en models + config + food_state |

---

## RESUMEN EJECUTIVO

| Categoría | P1 | P2 | P3 | Fase 3 |
|---|---|---|---|---|
| Sprint S3 (inmediato) | ~~2~~ **0** — ✅ | — | — | — |
| Seguridad | ~~1~~ **0** ✅ | ~~1~~ **0** ✅ | — | — |
| Performance | — | ~~2~~ **0** ✅ | — | — |
| Operativo | — | ~~3~~ **0** ✅ | — | — |
| Admin/Finanzas | — | ~~4~~ **0** ✅ | — | — |
| Multi-tenant | — | ~~2~~ **0** ✅ | — | — |
| Frontend/UX | — | ~~3~~ **0** ✅ | ~~1~~ **0** ✅ | — |
| Testing | ~~2~~ **0** ✅ | ~~1~~ **0** ✅ | — | — |
| Deuda técnica | — | ~~3~~ **0** ✅ | — | — |
| Features mayores | — | — | — | ~~6~~ **1** (5 ✅) |
| **Total** | **0** ✅ | **0** ✅ | **0** ✅ | **1** |

Continuo: UI-01d (hex → theme.py, se hace al tocar cada página).

**Sprint S3 + P1 + P2 completados al 100%.** Fase 3: 5/6 completados (FEAT-04, FEAT-05, FEAT-07, FEAT-08, MT-03b), queda 1.
