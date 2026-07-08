# PROYECTO TUWAYKIFOOD — Documento Maestro

> **Propósito de este documento:** handoff completo del proyecto para cualquier IA o desarrollador.
> Contiene visión, arquitectura, modelo de datos, módulos implementados, convenciones obligatorias,
> auditoría integral (2026-07-07) y roadmap priorizado. Leyendo solo este archivo se puede continuar
> el desarrollo sin contexto previo.
>
> **Última actualización:** 2026-07-07 · **Estado:** MVP completo + Auditoría Frontend P0/P1/P2 cerrada.

---

## 1. Visión y alcance

**TUWAYKIFOOD** es un sistema SaaS multi-tenant de gestión integral para el **rubro gastronómico y de bebidas**:
restaurantes, restobares, bares, cafeterías y comida rápida (Perú como mercado inicial — moneda S/, IGV 18%).

**Dos lados del sistema:**

| Lado | Usuarios | Módulos |
|---|---|---|
| **Operativo** | Mozos (5-7 tabletas simultáneas), Caja, Cocina/Barra, Mostrador | Mapa de mesas, toma de pedidos, KDS, cobros, turnos de caja |
| **Administrador** | Dueño del local (login email+contraseña) | Dashboard, carta, inventario/recetas, clientes, cuentas corrientes, promociones, cupones, reportes/analítica, usuarios, configuración |

**Contexto de carga esperado:** 5-7 tabletas de mozos enviando pedidos constantemente + caja + 1-2 pantallas
de cocina, todo en simultáneo por local. El sistema debe ser fluido bajo ese tráfico.

**Proyecto hermano:** Sistema-de-Ventas (retail) — comparte el paquete privado `tuwayki-core`
(rate limit, sanitización, validadores, timezone, logger) y el Owner Admin que gestiona la activación de
empresas de ambos sistemas. **Los repos son 100% independientes: cambios en uno jamás tocan al otro.**

---

## 2. Stack técnico

| Capa | Tecnología |
|---|---|
| Framework full-stack | **Reflex 0.9.4** (Python → React/Vite, websockets para estado) |
| Base de datos | **MySQL 8.0** (`food_db`), SQLModel + SQLAlchemy 2.0, PyMySQL |
| Migraciones | Alembic (39 migraciones aplicadas, head = `e8f1a2b3c4d5`) |
| Servidor | Granian, contenedor Docker único (frontend+backend, puerto interno 3000) |
| Auth | bcrypt 5.0 (PINs operativos + contraseña admin) |
| Exportación | openpyxl (Excel), reportlab (disponible, sin uso aún) |
| Compartido | `tuwayki-core` @ git (pinneado por commit — actualizar requirements.txt y Dockerfile juntos) |

**Puertos:** local dev 3003 (frontend) / 3004 (backend API). Prod: NPM proxy → `tuwayki_food:3000`, dominio `food.tuwayki.app`.

**Docker:** `docker build -t tuwayki_food:latest .` →
`docker compose -f docker-compose.yml -f docker-compose.local.yml up -d` (local, puerto 3003→3000).
Prod: `bash scripts/deploy-prod.sh`. Test: overlay `docker-compose.test.yml`.

**Ramas git:** `main` (desarrollo) y `docker-deploy-prod` (deploy) — siempre se pushean sincronizadas:
`git push origin HEAD:main HEAD:docker-deploy-prod`.

---

## 3. Arquitectura de código

```
app/
├── app.py                  # Entry point Reflex, registra páginas + api_transformer
├── api.py                  # Starlette: /api/health, /api/ping, /api/registro,
│                           # /api/admin/companies/* (Owner Admin), /menu/{slug} SPA fallback
├── models/
│   ├── food.py             # TODOS los modelos SQLModel (706 líneas) — ver §4
│   └── company.py          # Company (tenant registry)
├── states/
│   ├── food_state.py       # Estado central (5.268 líneas) — login, mesas, pedidos,
│   │                       # cocina, caja/cobros, config, menú público, admin local
│   ├── carta_mixin.py      # CRUD carta: categorías, productos, modificadores, combos
│   ├── caja_turno_mixin.py # Turnos de caja, arqueo, movimientos ingreso/egreso
│   ├── inventario_mixin.py # Insumos, kardex, recetas por producto
│   ├── clientes_cuentas_mixin.py  # Clientes + cuentas corrientes (fiado)
│   ├── promos_cupones_mixin.py    # Promociones + lotes de cupones
│   └── reportes_mixin.py   # Dashboard, analítica, comparativa, export Excel
├── services/               # Lógica pura testeada (sin Reflex)
│   ├── pago_service.py     # validar_pagos, registrar_pagos_pedido (pagos mixtos/split)
│   ├── kardex_service.py   # registrar_entrada/merma/ajuste (stock insumos)
│   ├── anulacion_service.py# anular venta: repone stock, revierte fiado, audita
│   ├── analitica_service.py# ventas por mozo/hora, margen por plato
│   ├── promo_service.py    # promo_vigente (bitmask días + rango horario), ahora_local_pe
│   ├── cupon_service.py    # validar/redimir cupones
│   ├── suscripcion_service.py # evaluar_bloqueo (is_active + trial_ends_at)
│   └── receipt_service.py  # Tickets HTML térmicos 58/80mm (cocina, precuenta, caja)
├── pages/                  # Una página por módulo (mozos, caja, cocina, mostrador,
│                           # carta, inventario, clientes, cuentas, promociones, cupones,
│                           # reportes, usuarios, configuracion, dono=dashboard admin,
│                           # login, menu_publico)
├── components/
│   ├── shared.py           # Modales, navbar, kpi cards, confirmaciones
│   └── theme.py            # Constantes de color (migración incremental UI-01d)
└── utils/
    ├── db.py               # get_engine (pool_pre_ping, recycle 1800), get_session
    └── tenant.py           # set_tenant_context, tenant_bypass (listener tuwayki-core)
```

**Patrón de estado:** `FoodState` hereda de todos los mixins (`class XxxMixin(rx.State, mixin=True)`).
Los mixins organizan el código pero **no** particionan el estado en runtime — es un solo estado por cliente.

**Patrón multi-tenant:** filtro explícito `Model.company_id == self._company_id()` en **cada query**,
dentro de `self._tenant_session()`. Excepciones legítimas cross-tenant (usan `tenant_bypass()`):
resolución de slug en menú público, login admin por email global, API Owner Admin, selector de
restaurante en login. Tests de aislamiento en `tests/test_tenant_isolation.py`.

**Tiempo real:** polling por página con `@rx.event(background=True)` cada 3s
(`start_mozos/cocina/caja/mostrador_polling`). Cada `on_load_X` apaga los polls de las otras páginas.
Sonidos (chime mozos, campana cocina) y auto-impresión de tickets de cocina se disparan desde el poll.

---

## 4. Modelo de datos (MySQL, prefijo `food_`)

| Tabla | Rol | Claves |
|---|---|---|
| `food_companies` | Registro de tenants | slug único, `is_active`, `trial_ends_at` |
| `food_config_impresora` | Config por empresa (1 fila/company) | nombre local, impresoras IP, ancho papel 58/80mm, slug carta pública, admin_email+password_hash, RUC/dirección/teléfono, IGV configurable, KDS minutos alerta |
| `food_usuarios` | Usuarios operativos | PIN bcrypt (4-6 dígitos), rol (Mozo/Caja/Cocina/Admin), perms: descuento, anular, reportes |
| `food_mesas` | Mesas físicas | número único/company, estado (libre/ocupada/esperando_cuenta), sector, capacidad |
| `food_pedidos` | Pedido mesa o mostrador | estado (borrador→enviado→en_preparacion→listo→cobrado/cancelado), mozo/cajero, total/descuento/propina/recargo, turno_caja, cliente, auditoría de anulación |
| `food_detalle_pedidos` | Línea de pedido | estado_produccion (pendiente→en_preparacion→listo→entregado), modificadores_json, combo_items_json, impreso_cocina/caja, preparado_por |
| `food_productos` | Carta | precio Decimal, categoría, emoji, imagen_url, estación (cocina/barra), tags JSON (picante/veggie/…) |
| `food_categorias` | Categorías carta | orden, estación default |
| `food_grupo_modificadores` + `food_opcion_modificadores` + `food_producto_grupo_modificadores` | Modificadores (Tamaño, Extras…) | min/max selecciones, precio_extra |
| `food_combos` + `food_combo_items` | Combos precio fijo | items = producto+cantidad |
| `food_insumos` | Ingredientes con stock | stock_actual/mínimo Numeric(12,3), costo_unitario, vencimiento |
| `food_receta_items` | Receta por producto | (producto, insumo, cantidad) único — **base del cálculo de producción** |
| `food_movimientos_insumo` | Kardex | entrada/consumo/merma/ajuste/reposicion, stock_resultante |
| `food_turnos_caja` | Turnos con arqueo | snapshot al cierre: totales por método, esperado vs contado, descuadre, denominaciones JSON |
| `food_movimientos_caja` | Ingresos/egresos de efectivo | categoría, motivo obligatorio |
| `food_pagos_pedido` | Pagos 1..N por pedido | pago mixto, split por ítems (detalle_ids_json) |
| `food_clientes` | Clientes | teléfono único/company, cumpleaños, puntos |
| `food_cuentas_corrientes` + `food_movimientos_cuenta` | Fiado | saldo_deuda, límite crédito, cargo/pago |
| `food_promociones` | Promos | %/monto/happy_hour/2x1, bitmask días (lun=1…dom=64), rango horario, producto o categoría, auto_aplicar |
| `food_cupon_lotes` | Cupones por código | usos_max/actuales, vigencia |

**Flujo operativo núcleo:** Mozo toma pedido en mesa → envía a cocina (KDS por estación cocina/barra,
auto-print opcional) → cocina marca listo → mozo entrega → mesa pide cuenta → caja abre panel de cobro
(método/mixto/split, descuento, propina, recargo, cupón, fiado) → `confirmar_cobro()` marca COBRADO,
libera mesa, **descuenta stock por receta** (`_descontar_stock_por_pedido`), registra pagos al turno,
imprime ticket. Anulación posterior repone stock y revierte fiado con motivo auditado.

---

## 5. Convenciones obligatorias del proyecto

1. **Español neutro en toda la UI** — imperativo de usted ("Seleccione", "Ingrese", "Pruebe"). Prohibido voseo/tuteo.
2. **Aislamiento multi-tenant**: toda query filtra por `company_id` vía `_tenant_session()`. Nunca confiar en el listener; el filtro es explícito.
3. **Todo local primero**: probar en Docker local antes de commit. Push solo cuando el usuario lo pida, a `main` + `docker-deploy-prod` sincronizados.
4. **Decimal para dinero** (Numeric 10,2), **Numeric(12,3) para stock**. Nunca float en persistencia.
5. **Servicios puros testeados**: lógica de negocio en `app/services/` sin dependencia de Reflex; los mixins/states solo orquestan.
6. **ViewModels Pydantic** (`XxxView`) para todo lo que se renderiza — nunca pasar modelos SQLModel a componentes.
7. **Reflex 0.9.4 gotchas**: `rx.State` mixins con `mixin=True`; computed vars con `@rx.var`; `rx.cond`/`rx.foreach` para render condicional; es-toolkit patch en `docker-entrypoint.sh` (shims ESM para Vite/Rolldown).
8. **Migraciones Alembic siempre** — jamás `ALTER TABLE` manual. Correr dentro del contenedor con `alembic upgrade head` (el entrypoint lo hace solo).
9. **tuwayki-core pinneado por commit** en requirements.txt Y Dockerfile — actualizar ambos juntos.

---

## 6. AUDITORÍA INTEGRAL — 2026-07-07

> Alcance: operativo, administración/finanzas, seguridad/roles, performance bajo carga (5-7 tabletas),
> responsividad, multi-tenant. Prioridades: **P0** = antes de producción con clientes reales,
> **P1** = próximo sprint, **P2** = mejora planificada.

### 6.1 Seguridad y control de acceso

| # | Prioridad | Hallazgo | Recomendación |
|---|---|---|---|
| SEC-01 | **P0** | **Login por PIN sin rate limiting ni lockout.** `_authenticate_with_pin` acepta intentos ilimitados vía websocket. Un PIN de 4 dígitos son 10.000 combinaciones — fuerza bruta trivial. Además itera TODOS los usuarios activos haciendo `bcrypt.checkpw` contra cada uno (O(N) costoso y ventana de DoS). | Contador de intentos fallidos por sesión/IP (reutilizar `tuwayki_core.utils.rate_limit` como en `/api/registro`), lockout progresivo (5 intentos → 1 min, 10 → 15 min). Incentivar PIN de 6 dígitos. |
| SEC-02 | **P0** | **Login admin local sin rate limiting.** `login_admin_local` (food_state.py ~5182) no usa `is_rate_limited` — solo el endpoint `/api/registro` lo tiene. | Aplicar el mismo rate limit por email+IP que ya existe en la API. |
| SEC-03 | P1 | `_require_admin_secret` compara con `!=` (no constant-time) y es un secreto compartido único en header. | `hmac.compare_digest`; evaluar allowlist de IP del Owner Admin. |
| SEC-04 | P1 | **Sin expiración de sesión operativa**: `usuario_actual` vive hasta logout explícito. Una tableta abandonada queda logueada indefinidamente. | Timestamp de última actividad + auto-logout configurable (ej. 8h operativo, 30 min admin). |
| SEC-05 | P1 | **Permisos insuficientemente granulares.** Solo existen `perm_descuento`, `perm_anular`, `perm_reportes`. No hay permiso para: abrir/cerrar turno, movimientos de caja, mermas/ajustes de inventario, ver costos y márgenes, reimprimir tickets, editar carta. | Ampliar flags por usuario (o matriz rol→permisos editable): `perm_turno`, `perm_inventario`, `perm_costos`, `perm_reimprimir`. |
| SEC-06 | P2 | **Sin bitácora de auditoría transversal.** Se auditan anulaciones y kardex, pero no: cambios de precio, descuentos aplicados (quién/cuánto), reimpresiones, cambios de permisos, cierres con descuadre. En gastronomía el fraude interno es el riesgo #1. | Tabla `food_auditoria` (company_id, usuario_id, acción, entidad, detalle JSON, timestamp) + vista en admin. |
| SEC-07 | P2 | `datetime.utcnow()` (deprecado en Python 3.12+) usado en todos los modelos y estados. | Migrar a `datetime.now(timezone.utc)` de forma incremental. |

### 6.2 Performance y escalabilidad (5-7 tabletas con tráfico constante)

| # | Prioridad | Hallazgo | Recomendación |
|---|---|---|---|
| PERF-01 | **P0** | **El polling reasigna las listas completas cada 3s aunque nada cambió.** `_refresh_mozos_slice` → `cargar_mesas()` reconstruye `self.mesas` en cada tick; Reflex marca la var como dirty y **reenvía la lista entera por websocket a cada cliente cada 3s**. Con 10 clientes y cartas grandes es tráfico y re-render constante. | Comparar antes de asignar: construir la lista nueva, si `nueva == self.mesas` no asignar. Aplica a mesas, tickets_cocina, pedidos_mostrador. Ganancia inmediata de fluidez percibida en tabletas. |
| PERF-02 | P1 | **Pool de conexiones default (5 + 10 overflow).** ~10 clientes × poll 3s × 3-6 queries/tick ≈ picos que pueden agotar el pool y encolar eventos (se siente como lag en la tableta). | `create_engine(..., pool_size=15, max_overflow=15)` en `app/utils/db.py`. MySQL ya permite 100 conexiones. |
| PERF-03 | P1 | **Faltan índices compuestos para las queries calientes del polling:** `Pedido(company_id, estado)`, `Pedido(company_id, cerrado_en)`, `DetallePedido(company_id, estado_produccion)`, `DetallePedido(pedido_id, estado_produccion)`. Hoy solo hay índices simples. | Migración Alembic con esos 4 índices compuestos. Costo cero, beneficio directo en cada tick de KDS/caja. |
| PERF-04 | P1 | **La analítica agrega en Python, no en SQL.** `_pedidos_cobrados` carga TODOS los pedidos del período como objetos y suma en bucles. Con 6-12 meses de historial (>20-50k pedidos) los reportes tardarán segundos y bloquearán el event loop. | Reescribir con `func.sum/count + group_by` en SQL. Misma salida, 10-100× menos memoria/tiempo. |
| PERF-05 | P1 | `confirmar_cobro`, `imprimir_precuenta` y `abrir_cobro_*` cargan **todos los productos del tenant** para mapear nombres (`select(Producto).where(company_id==...)`). | `Producto.id.in_([ids del pedido])` — trivial y reduce carga por cobro. |
| PERF-06 | P2 | `FoodState` monolítico (5.268 líneas + mixins ≈ 9.000): cada cliente serializa un estado grande; los mixins no lo particionan en runtime. | Migración gradual a substates reales (`rx.State` hijos) por página: el estado de inventario/reportes/config no necesita vivir en la sesión del mozo. |
| PERF-07 | P2 | **Sin resiliencia offline en tabletas.** Si el WiFi parpadea, el websocket se reconecta pero el mozo no tiene indicador claro ni cola de reintento del pedido que estaba enviando. | Indicador de conexión visible (verde/rojo) en navbar operativa + toast al reconectar + confirmar que el carrito local sobrevive la reconexión (es state del server: documentar comportamiento). |
| PERF-08 | P2 | MySQL con `innodb_buffer_pool_size=128M` y contenedor limitado a 512M. | Al crecer datos: 256-512M de buffer pool en prod y revisar límite del contenedor. |

### 6.3 Lado operativo (mozos, cocina, caja, mostrador)

**Fortalezas verificadas:** flujo mesa→cocina→entrega→cobro completo y sólido; KDS por estación con
alerta de demora configurable; auto-print cocina; pagos mixtos y split por ítems; turnos con arqueo
ciego y descuadre; anulación auditada con reposición de stock; precuenta; recargo con concepto;
sonidos de notificación; leyenda de estados.

| # | Prioridad | Mejora | Detalle |
|---|---|---|---|
| OP-01 | P1 | **Transferir/unir mesas** | No existe mover un pedido de mesa 5 a mesa 8, ni unir dos mesas. Es operación diaria real en restobares. |
| OP-02 | P1 | **Dividir cuenta antes de cobrar (por comensal en el mozo)** | El split existe solo en caja al cobrar. Los mozos suelen necesitar precuentas parciales por comensal. |
| OP-03 | P2 | **Anotación rápida de cliente en mesa** | Vincular cliente registrado a pedido de mesa (hoy solo en fiado/mostrador) para acumular puntos e historial. |
| OP-04 | P2 | **KDS: agrupar por mesa + tiempo objetivo por plato** | Hoy es cola por ticket; agrupar ítems de la misma mesa mejora sincronización de salida de platos. |
| OP-05 | P2 | **Modo "producto agotado" rápido desde cocina** | Cocina detecta que se acabó un plato → hoy debe avisar al admin para desactivarlo en carta. Botón "86" (agotar) con permiso. |

### 6.4 Lado administrador (contabilidad, finanzas, reportes)

**Fortalezas verificadas:** dashboard con KPIs; ventas por mozo/hora/método de pago; margen por plato
(precio vs costo receta); comparativa entre períodos; export Excel de ventas y cuentas corrientes;
turnos históricos con descuadres; kardex valorizable; CC con límite de crédito.

| # | Prioridad | Mejora | Detalle |
|---|---|---|---|
| ADM-01 | P1 | **Estado de resultados simple (P&L mensual)** | Ventas netas − costo de insumos consumidos (kardex CONSUMO valorizado) − egresos de caja = utilidad bruta operativa. Todos los datos ya existen; falta el reporte. |
| ADM-02 | P1 | **Reporte de descuentos y anulaciones (anti-fraude)** | Quién aplicó cuánto descuento, quién anuló qué y por qué, ranking por usuario. Los datos están en Pedido; falta la vista. Complementa SEC-06. |
| ADM-03 | P1 | **Reporte de mermas valorizado** | Kardex ya registra mermas con categoría; falta el reporte S/ perdidos por categoría/mes — métrica clave del rubro. |
| ADM-04 | P2 | **Reporte de propinas por mozo para reparto** | Total propinas por mozo por turno/período (dato ya existe en Pedido.propina + mozo_id). |
| ADM-05 | P2 | **Resumen de impuesto (IGV) mensual** | Base imponible + IGV del período para la contadora. Export Excel. |
| ADM-06 | P2 | **Top/bottom productos por unidades y por margen combinados** | Matriz estrella/perro (vende mucho-margen bajo, etc.) para decisiones de carta. |
| ADM-07 | P2 | **Export Excel en todos los reportes** (hoy solo ventas y CC) + PDF ejecutivo mensual (reportlab ya está en requirements). | |

### 6.5 Módulo NUEVO solicitado: Planificador de producción (explosión de insumos)

**Requerimiento:** al planificar N unidades de un plato/producto terminado, calcular exactamente
cuánto de cada insumo se necesita. Ej.: 1 arroz con pollo = 150g arroz + 250g pollo + 30ml aceite →
¿cuánto necesito para 20 platos? Y sumado entre varios platos del día.

**La base ya existe** (`food_receta_items` + `food_insumos` + costos). Lo que falta es el módulo de cálculo y su UI:

- **Servicio `produccion_service.py`** (lógica pura, testeable):
  `explosionar_insumos(session, company_id, plan: list[(producto_id, cantidad)]) -> list[InsumoNecesidad]`
  donde cada fila = insumo, cantidad_necesaria (Σ receta.cantidad × cantidad_plan), unidad,
  stock_actual, **faltante** (max(0, necesario − stock)), costo_estimado (cantidad × costo_unitario).
  Debe expandir combos a sus productos componentes (mismo patrón que `_descontar_stock_por_pedido`).
- **UI en Inventario → pestaña "Producción"**: seleccionar múltiples productos con cantidades
  (plan del día), tabla resultado con semáforo (verde alcanza / rojo faltante), costo total del plan,
  y botón **"Exportar lista de compras"** (Excel) con solo los faltantes.
- **Extensión natural (P2):** botón "Registrar producción" que descuenta insumos por kardex tipo
  CONSUMO con motivo "Producción planificada" — para locales que preparan por lote (salsas, postres, hielo saborizado).
- **Prioridad: P1** — alto valor, bajo riesgo, reutiliza todo lo existente.

### 6.6 Multi-tenant: multi-empresa, multi-sucursal y planes

**Estado actual:** multi-empresa **funcional** (Company + aislamiento por company_id + registro público
+ API Owner Admin + trial). Lo que falta para el modelo SaaS completo tipo Sistema-de-Ventas:

| # | Prioridad | Brecha | Diseño propuesto |
|---|---|---|---|
| MT-01 | P1 | **Sin campo de plan** — solo `is_active` + `trial_ends_at`. | `Company.plan: str` (`trial`/`standard`/`profesional`) + `plan_expires_at`. Servicio `plan_service.py` con matriz de features: `plan_permite(company, feature)` — ej. standard: 1 sucursal, 5 usuarios, sin analítica avanzada ni API; profesional: todo. Owner Admin API: endpoint `set-plan`. |
| MT-02 | P1 | **Gating de features por plan inexistente.** | Decorador/guard en on_load de páginas premium + límites en creación (usuarios, mesas) con mensaje de upgrade. Los mensajes de bloqueo ya tienen patrón (`suscripcion_service`). |
| MT-03 | P2 | **Sin modelo de sucursal** — `sucursal` es un texto en ConfigImpresora. | Tabla `food_sucursales` (company_id, nombre, dirección, activa) + `sucursal_id` en tablas operativas: mesas, pedidos, turnos_caja, insumos/movimientos, usuarios (asignación). Selector de sucursal post-login. Reportes consolidados y por sucursal para el admin. **Migración grande: diseñarla con default sucursal_id=1 retrocompatible.** |
| MT-04 | P2 | El filtro tenant es manual por query (sólido pero repetitivo y propenso a olvido en código nuevo). | Evaluar `with_loader_criteria` de SQLAlchemy para inyectar `company_id` automático como red de seguridad adicional (defensa en profundidad; el filtro explícito se mantiene). |
| MT-05 | P2 | **Sin backups automatizados** de MySQL en scripts/. | Cron `mysqldump` diario comprimido + retención 30 días + copia offsite (S3/BackBlaze). Crítico antes de crecer en clientes. |

### 6.7 Frontend / Responsividad

- **Uso de breakpoints desigual:** dono (16), reportes/mozos/caja (10)… pero mostrador (3), usuarios (2),
  clientes (2), promociones (1), cocina (0 — pantalla fija aceptable). **P1:** revisar mostrador y
  usuarios en viewport tablet vertical (768px) que es el hardware real de los mozos.
- **UI-01d (continuo):** seguir migrando hex hardcodeados a `theme.py` al tocar cada página.
- **P2:** estados de carga skeleton en reportes (hoy spinner global `pagina_cargada`).
- **P2:** menú público — lazy-load de imágenes de productos (`loading="lazy"`) para cartas con fotos.

### 6.8 Gotchas y warnings conocidos

- **"Page X is being redefined"** — warning cosmético de Reflex 0.9.4 al importar páginas en `dono.py` con import diferido. Inofensivo, no afecta runtime ni funcionalidad.
- **es-toolkit CJS/ESM** — fix en `docker-entrypoint.sh` con shims manuales + patch watcher background. Puede necesitar actualización si Reflex/Vite cambian su bundling.

### 6.9 Testing

Cobertura actual: servicios core (pagos, kardex, anulación, promos, analítica, turnos, aislamiento tenant) ✓.
**Brechas (P1):** falta test del flujo `confirmar_cobro` completo (con stock, fiado, split),
`_descontar_stock_por_pedido` con combos, y `explosionar_insumos` cuando exista.
**P2:** test de carga simple (locust/script) simulando 7 clientes con polling para validar PERF-01/02.

---

## 7. ROADMAP CONSOLIDADO (prioridad de ejecución)

### Sprint S1 — Seguridad y fluidez (P0, antes de clientes reales)
1. SEC-01 rate limit + lockout en login PIN
2. SEC-02 rate limit en login admin
3. PERF-01 comparar-antes-de-asignar en los 4 slices de polling

### Sprint S2 — Performance y producción (P1)
4. PERF-02 pool 15/15 · PERF-03 índices compuestos · PERF-05 queries de productos acotadas
5. PERF-04 analítica en SQL
6. **Planificador de producción** (§6.5) — servicio + UI + export lista de compras
7. SEC-04 expiración de sesión · SEC-05 permisos granulares

### Sprint S3 — Admin financiero (P1)
8. ADM-01 P&L mensual · ADM-02 reporte descuentos/anulaciones · ADM-03 mermas valorizado
9. OP-01 transferir/unir mesas · OP-02 split desde mozos
10. MT-01/MT-02 planes standard/profesional + gating

### Fase 3 — Features mayores (acordados previamente, orden sugerido)
11. **FEAT-04 Reservas de mesa** — CRUD fecha/hora/pax/cliente + indicador en mapa
12. **FEAT-07 Módulo Delivery** — TipoPedido.DELIVERY, dirección/teléfono, estado reparto, repartidores
13. **FEAT-05 Self-order QR** — carrito en menú público + llamar mozo + cola de aprobación
14. **MT-03 Multi-sucursal** (antes de FEAT-06 si hay clientes multi-local)
15. **FEAT-06 Facturación electrónica SUNAT** — boleta/factura, integración PSE/OSE (mayor complejidad regulatoria)

### Continuo
- UI-01d theme.py · SEC-07 utcnow · PERF-06 substates · MT-05 backups (no postergar demasiado)

---

## 8. Cómo continuar (para cualquier IA/desarrollador)

1. **Leer este documento completo** + `CLAUDE.md` (skills Reflex obligatorios) + memoria del proyecto si existe.
2. Entorno: seguir skill `setup-python-env`; para correr/testear usar skill `reflex-process-management`
   (`reflex compile --dry` valida sin levantar servidor).
3. **Verificación local**: `docker build -t tuwayki_food:latest .` + compose local, comprobar rutas 200
   (`/login`, `/admin/login`, `/menu/{slug}`, `/api/health`).
4. Tests: `pytest tests/ -x -q` (usa SQLite en memoria vía conftest).
5. Antes de escribir código Reflex consultar el skill `reflex-docs` — no confiar en memoria de APIs.
6. Commits: convencional en español (`feat(scope): …`), push a `main` + `docker-deploy-prod` juntos
   **solo cuando el usuario lo pida**.
7. Documento de auditoría frontend histórico: `AUDITORIA_FRONTEND_TUWAYKIFOOD.md` (Sprints A-D cerrados).
   Este documento (`PROYECTO_TUWAYKIFOOD.md`) es la fuente de verdad del roadmap vigente.
