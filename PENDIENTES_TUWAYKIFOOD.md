# PENDIENTES CONSOLIDADOS — TUWAYKIFOOD

> **Fecha de consolidación:** 2026-07-08
> **Fuentes:** `PROYECTO_TUWAYKIFOOD.md` (§6-7), `AUDITORIA_FRONTEND_TUWAYKIFOOD.md` (§4-8),
> verificación directa contra el código fuente.
>
> Este documento reemplaza las secciones de pendientes de ambos MD anteriores.
> Esos archivos quedan como referencia histórica.

---

## CAMBIOS SIN COMMITEAR (sesión 2026-07-08)

| Archivo | Cambio |
|---|---|
| `app/services/finanzas_service.py` | **NUEVO** — servicio puro SQL para P&L, descuentos/anulaciones, mermas |
| `app/states/food_state.py` | ViewModels financieros + handlers OP-02 (precuenta parcial) |
| `app/states/reportes_mixin.py` | Handlers + vars para ADM-01/02/03 |
| `app/pages/reportes.py` | 3 secciones UI: P&L, descuentos/anulaciones, mermas |
| `app/pages/mozos.py` | UI precuenta parcial (selección ítems + impresión) |
| `PROYECTO_TUWAYKIFOOD.md` | Marcas ✅ en ítems 8 y 9 del roadmap |

**Acción:** commitear todo antes de continuar.

---

## SPRINT S3 — PENDIENTE INMEDIATO (P1)

| ID | Tarea | Detalle | Origen |
|---|---|---|---|
| **MT-01** | **Campo de plan en Company** | `Company.plan: str` (`trial`/`standard`/`profesional`) + `plan_expires_at`. Servicio `plan_service.py` con matriz de features. Endpoint Owner Admin `set-plan`. | PROYECTO §6.6 |
| **MT-02** | **Gating de features por plan** | Decorador/guard en `on_load` de páginas premium + límites en creación (usuarios, mesas) con mensaje de upgrade. Reutilizar patrón `suscripcion_service`. | PROYECTO §6.6 |

---

## SEGURIDAD

| ID | Prioridad | Tarea | Estado | Origen |
|---|---|---|---|---|
| SEC-03 | **P1** | `hmac.compare_digest` para `_require_admin_secret` (hoy usa `!=`, no constant-time) + evaluar allowlist IP Owner Admin | No implementado | PROYECTO §6.1 |
| SEC-06 | P2 | Tabla `food_auditoria` transversal (cambios de precio, descuentos aplicados, reimpresiones, permisos, descuadres) | No implementado | PROYECTO §6.1 |
| SEC-07 | P2 | Completar migración `datetime.utcnow()` → `_utcnow()`. Helper existe y se usa 32× en food_state.py, pero **quedan 65 llamadas raw** en 8 archivos (api, models, mixins) | Parcial (~33%) | PROYECTO §6.1 |

---

## PERFORMANCE

| ID | Prioridad | Tarea | Detalle | Origen |
|---|---|---|---|---|
| PERF-06 | P2 | **Substates reales** por página | `FoodState` monolítico (~9.000 líneas con mixins): cada cliente serializa el estado entero. El estado de inventario/reportes/config no necesita vivir en la sesión del mozo. Migración gradual a `rx.State` hijos. | PROYECTO §6.2 |
| PERF-08 | P2 | MySQL `innodb_buffer_pool_size` para prod | Actualmente 128M, contenedor limitado a 512M. Subir a 256-512M al crecer datos. | PROYECTO §6.2 |

---

## OPERATIVO

| ID | Prioridad | Tarea | Detalle | Origen |
|---|---|---|---|---|
| OP-03 | P2 | **Anotación rápida de cliente en mesa** | Vincular cliente registrado a pedido de mesa (hoy solo en fiado/mostrador) para acumular puntos e historial | PROYECTO §6.3 |
| OP-04 | P2 | **KDS: agrupar por mesa + tiempo objetivo por plato** | Hoy es cola por ticket; agrupar ítems de la misma mesa mejora sincronización de salida de platos | PROYECTO §6.3 |
| OP-05 | P2 | **86 rápido desde cocina** | MZ-03 (86 desde mozos) ya está hecho. Falta lo mismo desde el lado de cocina: botón "86" en el KDS para que el cocinero marque agotado directo | PROYECTO §6.3 |

---

## ADMINISTRACIÓN Y FINANZAS

| ID | Prioridad | Tarea | Detalle | Origen |
|---|---|---|---|---|
| ADM-04 | P2 | **Reporte de propinas por mozo** | Total propinas por mozo por turno/período para reparto. Dato existe en `Pedido.propina` + `mozo_id` | PROYECTO §6.4 |
| ADM-05 | P2 | **Resumen IGV mensual** | Base imponible + IGV del período para contadora. Export Excel | PROYECTO §6.4 |
| ADM-06 | P2 | **Matriz estrella/perro de productos** | Top/bottom por unidades vendidas × margen — identifica qué sacar/promover en la carta | PROYECTO §6.4 |
| ADM-07 | P2 | **Excel en todos los reportes + PDF ejecutivo** | Hoy solo ventas y CC tienen export Excel. Falta en P&L, mermas, descuentos, margen, top platos. PDF mensual con reportlab | PROYECTO §6.4 |

---

## MULTI-TENANT / SaaS

| ID | Prioridad | Tarea | Detalle | Origen |
|---|---|---|---|---|
| MT-03 | P2 | **Modelo de sucursal** | Tabla `food_sucursales` + `sucursal_id` en tablas operativas (mesas, pedidos, turnos, insumos, usuarios). Selector post-login. Reportes consolidados y por sucursal. Migración grande con default retrocompatible | PROYECTO §6.6 |
| MT-04 | P2 | **Auto tenant filter** | `with_loader_criteria` de SQLAlchemy para inyectar `company_id` automático como red de seguridad adicional (defensa en profundidad) | PROYECTO §6.6 |
| MT-05 | P2 | **Backups automatizados** | Cron `mysqldump` diario comprimido + retención 30 días + copia offsite (S3/BackBlaze). Crítico antes de crecer en clientes | PROYECTO §6.6 |

---

## FRONTEND / UX

| ID | Prioridad | Tarea | Estado | Origen |
|---|---|---|---|---|
| UI-01d | Continuo | **Migrar hex hardcodeados a `theme.py`** | Se hace incrementalmente al tocar cada página. No big-bang | AUDITORIA §4 |
| UI-03 | P2 | **Evaluar tema raíz `light`** | Hoy raíz=dark + hack `.light` en páginas claras. Evaluar invertir: raíz light + `.dark` solo para las 4 páginas oscuras (mozos, cocina, mostrador, login) | AUDITORIA §4 |
| MZ-06 | P3 | **Label "Enviar nueva ronda"** en CTA del modal cuando ya hay historial de pedido en la mesa | AUDITORIA §5.1 |
| — | P2 | **Responsive mostrador/usuarios en tablet 768px** | Breakpoints desiguales: mostrador (3), usuarios (2). Revisar en viewport tablet vertical | PROYECTO §6.7 |
| — | P2 | **Lazy-load imágenes menú público** | `loading="lazy"` en img de productos para cartas con fotos | PROYECTO §6.7 |

---

## TESTING

| ID | Prioridad | Tarea | Origen |
|---|---|---|---|
| TEST-01 | P1 | Test del flujo `confirmar_cobro` completo (con stock, fiado, split, combos) | PROYECTO §6.9 |
| TEST-02 | P1 | Test de `_descontar_stock_por_pedido` con combos | PROYECTO §6.9 |
| TEST-03 | P2 | Test de carga (locust/script) simulando 7 clientes con polling para validar PERF | PROYECTO §6.9 |

---

## DEUDA TÉCNICA (BE-10)

| Tarea | Riesgo | Detalle |
|---|---|---|
| **bcrypt de PINs** | Bajo (POS local, PINs 4-6 dígitos) | bcrypt instalado pero PINs se almacenan en texto plano. Requiere migración + UI cambio de PIN |
| **`cobrar_mesa()` no descuenta stock** | Medio | Función de cobro rápido sin recorrido por fiado/propina. Si se quiere stock tracking completo, agregar `_descontar_stock_por_pedido()` |
| **Polling sin `on_unload`** | Bajo (mitigado con flags) | Reflex 0.9.4 no tiene `on_unload`. Background tasks pueden acumularse si el usuario navega rápido. El flag guard mitiga |

---

## FASE 3 — FEATURES MAYORES (a acordar)

| ID | Tarea | Impacto | Complejidad |
|---|---|---|---|
| **FEAT-04** | **Reservas de mesa** — CRUD fecha/hora/pax/cliente + indicador "Reservada 21:00" en mapa de mozos | Alto para restobares | Media |
| **FEAT-07** | **Módulo Delivery** — `TipoPedido.DELIVERY`, dirección/teléfono, estado de reparto, repartidores | Alto (canal adicional) | Media-Alta |
| **FEAT-05** | **Self-order desde QR** — carrito en menú público + llamar mozo + cola de aprobación (nunca directo a cocina sin validar) | Diferenciador SaaS | Alta (seguridad mesa-token) |
| **MT-03** | **Multi-sucursal** (ver arriba) — prerequisito si hay clientes multi-local | Alto para escalar | Alta (migración grande) |
| **FEAT-06** | **Facturación electrónica SUNAT** — boleta/factura con IGV, integración PSE/OSE peruano. Campos RUC/IGV ya existen | Obligatorio para formalización | Muy Alta (regulatoria) |
| **FEAT-08** | **Dashboard del día para dueño (mobile)** — vista resumida: ventas en vivo, mesas abiertas, alertas stock. Panel dono ya existe | Uso real del dueño fuera del local | Media |

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
| Sprint S3 (inmediato) | **2** (MT-01/02) | — | — | — |
| Seguridad | 1 (SEC-03) | 2 | — | — |
| Performance | — | 2 | — | — |
| Operativo | — | 3 | — | — |
| Admin/Finanzas | — | 4 | — | — |
| Multi-tenant | — | 3 | — | — |
| Frontend/UX | — | 3 | 1 | — |
| Testing | 2 | 1 | — | — |
| Deuda técnica | — | 3 | — | — |
| Features mayores | — | — | — | **6** |
| **Total** | **5** | **21** | **1** | **6** |

Continuo: UI-01d (hex → theme.py, se hace al tocar cada página).

**Próximo paso sugerido:** commitear los cambios de la sesión actual (ADM-01/02/03 + OP-02), luego MT-01/MT-02 para cerrar Sprint S3.
