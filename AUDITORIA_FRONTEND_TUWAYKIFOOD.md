# AUDITORÍA FRONTEND — TUWAYKIFOOD

> **Fecha:** 2026-07-04 · **Auditor:** Claude (Fable 5) · **Alcance:** Frontend/UI/UX completo + correcciones de backend que el frontend requiere + roadmap de mejoras para el rubro Gastronomía y Bebidas (restaurantes, restobares, bares).
>
> **Propósito de este documento:** que **cualquier IA (o desarrollador humano)** pueda retomar el trabajo sin contexto previo. Contiene: mapa del sistema, convenciones obligatorias, hallazgos con archivo:línea, tareas accionables con prioridad, y criterios de verificación.

---

## 0. CÓMO USAR ESTE DOCUMENTO (instrucciones para la IA implementadora)

1. **Leé primero la sección 1 (contexto) y la sección 2 (reglas)**. Son obligatorias antes de tocar código.
2. Trabajá por prioridad: **P0 → P1 → P2**. Cada ítem tiene un ID (`UI-xx`, `BE-xx`, `FEAT-xx`) para referenciarlo en commits y conversaciones.
3. Antes de escribir código Reflex, usá el skill **`reflex-docs`** (instrucciones en `CLAUDE.md` del repo). No confíes en memoria de APIs de Reflex: el proyecto usa **Reflex 0.9.4**.
4. Después de cada cambio: compilar (`reflex run` o el flujo del skill `reflex-process-management`), correr el **smoke test** (sección 9) y verificar visualmente la página tocada.
5. **Todo se prueba local antes de commitear. Push solo a `origin/main`.** No inventar ramas ni remotos nuevos salvo pedido explícito del usuario.
6. No romper el **aislamiento multi-tenant**: toda query pasa por `_tenant_session()` / `company_id`. Ver `app/utils/tenant.py`.

---

## 1. CONTEXTO DEL SISTEMA

### 1.1 Qué es

**TUWAYKIFOOD** es un POS SaaS multi-tenant para gastronomía (Perú — moneda S/, IGV) construido 100 % en Python con **Reflex 0.9.4** + **MySQL (food_db)** + SQLModel/Alembic. Corre en LAN del local (tablets para mozos, PC de caja, pantalla de cocina) y en Docker para producción. MVP + Fase 2 completos (inventario, clientes, cuenta corriente, promociones, cupones, turnos de caja con arqueo).

### 1.2 Mapa de archivos relevantes

| Archivo | Rol | Líneas |
|---|---|---|
| `app/app.py` | Entry point, registro de páginas, redirect raíz | 37 |
| `rxconfig.py` | Config Reflex: tema Radix `appearance="dark"` accent orange, TailwindV4, DB URL | 56 |
| `app/components/shared.py` | **Design system**: CSS global inyectado por `rx.script`, tokens `--twk-*`, clases `.twk-*`, constantes Python de paleta, `app_shell()` (sidebar + topbar + drawer), modal de anulación | 1041 |
| `app/states/food_state.py` | **God-state monolítico**: auth, mozos, caja, cocina, mostrador, carta, reportes, inventario, clientes, cuentas, promos, cupones, config, dono, menú público | **6457** |
| `app/states/caja_turno_mixin.py` | Mixin de turno de caja (único dominio ya separado) | 731 |
| `app/pages/*.py` | 17 páginas (ver 1.3) | 204–1171 c/u |
| `app/models/food.py` | Modelos SQLModel (Mesa, Categoria, Producto, Pedido, DetallePedido, PagoPedido, TurnoCaja, Insumo, Promocion, CuponLote, ConfigImpresora, etc.) | — |
| `app/services/receipt_service.py` | Tickets HTML (comanda + comprobante); impresión vía `window.print()` en el navegador del local | — |
| `app/api.py` | Health + rutas API (fix `/menu/[slug]` en Docker) | — |
| `_vendor/tuwayki-core/` | Librería compartida (formatting, validators, tax presets, countries) | — |

### 1.3 Páginas y su tema visual

| Ruta | Página | Tema | Público |
|---|---|---|---|
| `/login` | Login PIN (selector restaurante → rol → teclado iPhone) | Oscuro | Staff |
| `/mozos` | Mapa de salón + modal de comanda | Oscuro | Mozo |
| `/cocina` | KDS (columnas Pendiente / En preparación) | Oscuro | Cocina |
| `/mostrador` | Pedidos para llevar | Oscuro | Mozo/Caja |
| `/caja` | Cobro, turnos, arqueo, pagos divididos, fiado, cupones | Claro | Caja |
| `/carta` | Admin de categorías y productos | Claro | Admin |
| `/reportes` | KPIs, top platos, ventas por mozo/hora, margen, historial | Claro | Admin/Caja |
| `/usuarios`, `/configuracion`, `/inventario`, `/clientes`, `/cuentas`, `/promociones`, `/cupones` | Módulos admin | Claro | Admin |
| `/dono`, `/dono/login`, `/admin` | Panel Administrativo del dueño (shell propio) | Claro | Dueño |
| `/menu/[slug]` | Carta digital pública por QR, sin login | Claro | Cliente final |

### 1.4 Patrones existentes (respetarlos)

- **Shell:** toda página staff usa `app_shell(content, page_key=..., dark=True/False)` de `shared.py`. Sidebar oscura `#0F172A` colapsable en desktop, drawer en mobile.
- **Paleta:** naranja `#EA580C` (accent), slate 50–900, semánticos success/error/warning/info. Definida 3 veces (ver hallazgo UI-01).
- **Polling:** mozos/cocina/mostrador cada 5 s, caja cada 10 s, vía `@rx.event(background=True)` + flag guard (`food_state.py:2469`). No hay `on_unload` en Reflex 0.9.4.
- **Feedback:** var `FoodState.mensaje` renderizada como caja gris en cada página; solo 4 usos de `rx.toast` en todo el sistema.
- **Vistas tipadas:** cada lista usa dataclasses `*View` (MesaView, ProductoView, etc.) calculadas en el state — buen patrón, mantenerlo.
- **Permisos:** computed vars `puede_ver_*` controlan la navegación por rol.

---

## 2. REGLAS INNEGOCIABLES PARA IMPLEMENTAR

1. **Reflex 0.9.4** — verificar API con el skill `reflex-docs` antes de usar cualquier componente/prop.
2. **Multi-tenant:** ninguna query sin scope de `company_id`. Los listeners se registran en `app/app.py` **antes** de cualquier query.
3. **Mobile/tablet first:** el sistema se opera en tablets. Targets táctiles ≥ 40 px en vistas operativas (mozos, cocina, caja, mostrador).
4. **No introducir JS/React custom** salvo imprescindible: resolver con Reflex (`rx.*`) y el CSS global `.twk-*`.
5. **Migraciones:** cualquier cambio de modelo → migración Alembic en `alembic/versions/` + probar upgrade local contra MySQL antes de commit.
6. **No renombrar rutas existentes** (hay QRs impresos apuntando a `/menu/[slug]`).
7. Textos de UI en **español** (voseo rioplatense ya usado en algunos textos: "Hacé clic", "Escaneá" — mantener consistencia, ver UI-14).
8. Commits atómicos por ID de tarea, mensaje en español estilo convencional (`feat(caja): ...`, `fix(ui): ...`).

---

## 3. LO QUE YA ESTÁ BIEN (no tocar sin motivo)

- Login PIN con selector de restaurante y teclado tipo iPhone: sólido, con `aria-label`, alturas fijas anti-salto.
- Caja: flujo de cobro completo (métodos, pago dividido/mixto, fiado con cliente obligatorio, cupones, promos, vuelto, arqueo con denominaciones, descuadre, historial de turnos). Es la página más madura.
- Anulaciones auditadas con motivo obligatorio (modal compartido `anulacion_modal`).
- Carta admin con buscador + paginación; carta pública liviana con anchors por categoría y estado de carga/404.
- Sistema de `*View` dataclasses (separación estado ↔ presentación).
- Responsive: `rx.breakpoints` usado consistentemente; sidebar colapsable + drawer móvil.
- Design tokens CSS (`--twk-*`) bien pensados, scrollbars finos, fix de autofill, fix de zoom iOS en inputs.

---

## 4. HALLAZGOS FRONTEND — ARQUITECTURA VISUAL (transversales)

### UI-01 · Tres fuentes de verdad para la paleta — **P0**
- `shared.py:13-210` define tokens CSS `--twk-*` y ~40 clases `.twk-*`.
- `shared.py:226-259` define ~35 constantes Python (`ACCENT`, `TEXT_MUTED`…).
- `dono.py:12-29` **redefine** su propia paleta (`_ORANGE`, `_SLATE_900`…).
- Y en la práctica, las 17 páginas usan **hex crudos inline** (`"#EA580C"`, `"#64748B"`) en el 90 % de los casos; las clases `.twk-btn`, `.twk-badge`, `.twk-card` casi no se usan.

**Tarea:** consolidar. (a) Mover la paleta a un único módulo `app/components/theme.py` que exporte constantes; (b) reexportar desde `shared.py` para compatibilidad; (c) eliminar la paleta duplicada de `dono.py`; (d) en cada página que se toque por otra tarea, reemplazar hex crudos por constantes (migración oportunista, no big-bang). Cambiar un color de marca hoy exige tocar ~17 archivos; después de esto, uno.

### UI-02 · CSS global inyectado por `rx.script` — **P1**
`shared.py:222` inyecta todo el CSS con un IIFE (`_CSS_SCRIPT`) que además carga la fuente Inter creando `<link>` por JS (`_FONT_JS`, línea 212). Problemas: FOUC en primera carga (la página pinta antes de que el JS agregue el `<style>`), fuente carga tarde, y el CSS no se cachea como asset.

**Tarea:** mover `_TWK_CSS` a `assets/twk.css` y cargarlo con `stylesheets=["/twk.css"]` en `rx.App` (verificar API exacta en reflex-docs); mover los `<link>` de Google Fonts a `head_components` en `app/app.py` (ya se usa para el favicon). Mantener `rx.script` solo si alguna página no comparte el App root (login/dono lo importan directo — dejarían de necesitarlo).

### UI-03 · Hack de tema claro anidado (`.light`) — **P1 (documentar) / P2 (resolver)**
El tema raíz es `appearance="dark"` (`rxconfig.py:51`) y las páginas claras fuerzan tokens Radix con la clase `.light` (`shared.py:61`). Funciona, pero cada componente Radix nuevo (select, checkbox, dialog) puede salir con colores oscuros dentro de páginas claras — ya pasó y por eso existe el hack.

**Tarea corta:** documentar en `shared.py` la lista de tokens ya forzados y agregar los que falten cuando aparezca un componente roto. **Tarea larga (P2):** evaluar `appearance="light"` como raíz + clase `.dark` para las 4 páginas oscuras (son menos), o tema por página si la versión de Reflex lo permite.

### UI-04 · Feedback de acciones: cajas `mensaje` en vez de toasts — **P0**
Solo hay 4 `rx.toast` en 6457 líneas de state. El resto del feedback es `FoodState.mensaje` renderizado como caja estática (ej. `mozos.py:1067-1078`, `caja.py:1139-1147`, `carta.py:559-570`): no desaparece sola, empuja el layout, y el usuario no la ve si está scrolleado.

**Tarea:** estandarizar `rx.toast.success/error/info` (posición `top-right` en claro, `bottom-right` en oscuro, duración 3.5 s) para resultados de acciones (pedido enviado, cobro confirmado, guardado, stock ajustado). Mantener errores de **formulario** inline junto al campo (patrón actual correcto, ej. `caja_cobro_error`). Eliminar las cajas `mensaje` a medida que se migran los handlers.

### UI-05 · Targets táctiles chicos en vistas operativas — **P0**
Botones `+`/`−` del carrito: 26 px en página (`mozos.py:169-181`) y **22 px** en modal (`mozos.py:685-708`, `mostrador.py:65-88`). Botón "Entregar" con `padding_y=3px` (`mozos.py:322-336`). Chips de categoría con `padding_y=4-5px`. En tablet con dedos, esto genera errores de tap en el momento de mayor presión operativa.

**Tarea:** mínimo 40×40 px de área táctil en mozos/mostrador/cocina/caja (puede ser hit-area con padding aunque el ícono sea chico). Subir tipografías operativas: nada de texto funcional < 12 px en esas 4 páginas (hoy hay 9–11 px, ej. footer de opcionales de caja `caja.py:263-326`).

### UI-06 · Sin skeletons ni estados de carga — **P1**
Solo `/menu/[slug]` tiene spinner. Las demás páginas quedan en blanco/vacías durante `on_load` (con MySQL remoto se nota). 

**Tarea:** agregar flag `cargando_<pagina>` + `rx.skeleton` (verificar en reflex-docs) o placeholder simple en: lista de mesas (mozos/caja), tickets KDS, historial de reportes, tablas de inventario/clientes. Patrón único reutilizable en `shared.py`.

### UI-07 · Sin aviso de desconexión (crítico en LAN) — **P1**
El POS corre en LAN con tablets: si se cae el WebSocket, el mozo sigue tocando y nada responde. Reflex trae overlay de conexión por defecto, pero conviene hacerlo explícito y en español.

**Tarea:** configurar el banner/overlay de conexión de Reflex (buscar `connection banner / connection_error` en reflex-docs para 0.9.4) con texto propio: "Sin conexión con el servidor — reintentando…". Verificar que el polling se recupere al reconectar.

### UI-08 · Sin notificaciones sonoras — **P1**
Cocina no suena cuando entra un ticket; mozos no suena cuando un plato está listo. En un restobar con ruido, la pantalla sola no alcanza. El polling ya detecta los cambios.

**Tarea:** en `_refresh_cocina_slice` / `_refresh_mozos_slice`, si aumenta el count de tickets nuevos / items listos, disparar `rx.call_script` que reproduzca un audio corto (`assets/kds-bell.mp3`, `assets/ready-chime.mp3`). Toggle on/off persistido (LocalStorage con `rx.LocalStorage` o campo en ConfigImpresora). Nota: los navegadores exigen interacción previa del usuario para audio — inicializar el `AudioContext` en el primer click de la sesión.

### UI-09 · Login sin soporte de teclado físico — **P1**
En la PC de caja, el cajero no puede tipear el PIN: solo funciona el teclado en pantalla (`login.py:119-146`).

**Tarea:** capturar teclas 0-9, Backspace y Enter en `/login` (evento global de teclado — verificar patrón recomendado en reflex-docs 0.9.4; alternativa: input oculto con foco). Enter = submit. Opcional: auto-submit al completar 6 dígitos si el PIN del rol es de longitud fija.

### UI-10 · Código muerto en mozos.py — **P0 (rápido)**
`_carrito_section()` (`mozos.py:222`), `_historial_section()` (`mozos.py:403`) y `_menu_section()` (`mozos.py:554`) se definen pero **nunca se llaman** (la página usa solo el salón + modal). Son ~400 líneas que confunden a cualquier IA/dev que edite la página.

**Tarea:** eliminarlas (verificar con grep que ningún otro módulo las importe).

### UI-11 · Redirect raíz por `window.location` — **P2**
`app/app.py:19-26` redirige con `rx.script("window.location.href=...")` → flash de página en blanco y doble carga.

**Tarea:** hacer el redirect en `FoodState.on_load_root` con `return rx.redirect("/mozos" | "/login")` y dejar `index()` como pantalla neutra (logo centrado).

### UI-12 · Escala de z-index sin documentar — **P2**
Header sticky z=50 (`shared.py:873`), topbar móvil z=200 (`shared.py:897`), sidebar admin z=30/29 (`shared.py:198-203`), menú público z=10. Funciona hoy, pero es frágil.

**Tarea:** definir escala en `theme.py` (`Z_STICKY=50, Z_DRAWER=200, Z_MODAL=300…`) y usarla.

### UI-13 · Botones "Actualizar" manuales redundantes — **P2**
Cocina/caja tienen botón "Actualizar" aunque hay polling. No molesta, pero desinforma.

**Tarea:** reemplazar por indicador pasivo "Actualizado hace Xs" + ícono refresh chico. Mantener el refresh manual como fallback.

### UI-14 · Consistencia de copy — **P2**
Convive "Selecciona una mesa" (tuteo, `mozos.py:559`) con "Hacé clic" (voseo, `carta.py:588`) y "Escaneá" (`menu_publico.py:179`). Unificar a **español neutro**: infinitivos o tercera persona impersonal ("Seleccionar una mesa", "Haga clic", "Escanear"). Sin voseo, sin tuteo regional.

---

## 5. HALLAZGOS FRONTEND — POR PÁGINA

### 5.1 `/mozos` (Salón)

| ID | Hallazgo | Prioridad |
|---|---|---|
| MZ-01 | **Sin agrupación por sector** (Salón/Terraza/Barra). Con 30+ mesas el mapa es una sopa de cards. Requiere `Mesa.sector` (ver BE-03). UI: tabs o headers por sector. | **P1** |
| MZ-02 | **Sin acciones de mesa**: transferir pedido a otra mesa, juntar mesas, mover ítems. Operación diaria real de un restobar. Requiere BE-04. UI: menú contextual (⋮) en la mesa seleccionada. | **P1** |
| MZ-03 | **Sin "86" rápido**: si cocina avisa que se acabó un plato, el mozo no puede marcarlo no disponible (el toggle existe solo en `/carta`, rol admin). UI: long-press o botón en producto del modal → "Marcar agotado" con permiso configurable. Backend ya existe (`toggle_producto_disponible`). | **P1** |
| MZ-04 | Card de mesa no muestra **quién la atiende** (solo en detalle). Agregar inicial/nombre corto del mozo en la card — evita que dos mozos pisen la misma mesa. | **P2** |
| MZ-05 | Leyenda de colores de estado de mesa ausente (verde=libre, naranja=ocupada, rojo=cuenta). Agregar mini-leyenda como en cocina (`cocina.py:177-195`). | **P2** |
| MZ-06 | En el modal de comanda, cambiar cantidad de ítems ya enviados no es posible (correcto), pero no hay affordance de "agregar ronda" — el flujo existe, solo renombrar CTA cuando ya hay historial ("Enviar nueva ronda"). Ya hay label "Nuevo pedido" (`mozos.py:956-961`) — extender al botón. | **P3** |

### 5.2 `/cocina` (KDS)

| ID | Hallazgo | Prioridad |
|---|---|---|
| KD-01 | **Sin columna "Listo / Por entregar" ni deshacer**: al tocar "Listo" el ticket desaparece del KDS. Un toque errado = ticket perdido de vista. Agregar tercera columna (últimos 10 listos no entregados) con botón "Volver a preparación". El estado por detalle ya existe (`estado_produccion`). | **P0** |
| KD-02 | **Sin routing por estación (cocina vs barra)** — crítico para restobares: los tragos no deben entrar a la cola de cocina. Requiere BE-02. UI: filtro/toggle "Cocina / Barra / Todo" en el header del KDS + comanda separada por estación. | **P1** |
| KD-03 | **Bump por ítem**: los tickets se marcan enteros (`detalle_ids_csv`), pero `DetallePedido` tiene estado individual. Permitir tocar un ítem para marcarlo listo (parcial) — útil cuando salen los platos por tandas. Solo UI + handler que reciba un `detalle_id`. | **P1** |
| KD-04 | **Modo pantalla completa** para la pantalla dedicada de cocina: ocultar sidebar/topbar (botón "expandir" que setee un flag y esconda el shell). Hoy la sidebar roba 236 px. | **P1** |
| KD-05 | Umbral de "Demorado" hardcodeado. Hacerlo configurable por local (campo en ConfigImpresora, ej. `kds_minutos_alerta`, default 15). | **P2** |
| KD-06 | Sonido al entrar ticket → cubierto por UI-08. | — |

### 5.3 `/caja`

| ID | Hallazgo | Prioridad |
|---|---|---|
| CJ-01 | **Sin pre-cuenta imprimible** (proforma antes del pago). El mozo lleva "la cuenta" a la mesa en papel: hoy no se puede generar. Extender `receipt_service` con template pre-cuenta + botón "Imprimir pre-cuenta" en `_cobro_panel`. Ver BE-05. | **P0** |
| CJ-02 | **División por ítems**: hoy solo se divide por montos (`_pagos_divididos_panel`). Falta "cada comensal paga sus ítems" (seleccionar ítems → subtotal → cobrar). Requiere BE-06. | **P1** |
| CJ-03 | **Propina sugerida**: chips 5 % / 10 % / 15 % / otro junto al input libre (`caja.py:275-285`). Solo frontend (calcular sobre el total). Config del % por local opcional. | **P1** |
| CJ-04 | **Descuento por porcentaje**: hoy solo monto S/ (`caja.py:263-273`). Toggle `%` / `S/`. Solo frontend + cálculo en state. | **P1** |
| CJ-05 | Footer de opcionales (desc/propina/cupón) con fuentes 10-11 px y scroll horizontal (`caja.py:262-327`) — ilegible en caja. Rediseñar como fila de 3 campos con labels de 12 px+, sin overflow-x. | **P0** (junto con UI-05) |
| CJ-06 | **Confirmación post-cobro**: tras "Confirmar cobro" verificar que exista pantalla/toast de éxito con acciones "Imprimir comprobante / Siguiente". Si el panel simplemente se cierra, agregarla. | **P1** |
| CJ-07 | Botón "Cerrar turno e imprimir" — verificar que el ticket de cierre (arqueo) realmente se imprima vía `receipt_service`; si no, conectarlo. | **P1** |

### 5.4 `/mostrador`

| ID | Hallazgo | Prioridad |
|---|---|---|
| MS-01 | **Sin notas por ítem** en el carrito de mostrador (el modal de mozos sí tiene). Reusar el patrón `_modal_carrito_item` de mozos. | **P1** |
| MS-02 | **Número de pedido para el cliente** ("Pedido #47") visible grande al enviar, para llamarlo cuando esté listo. El `pedido_id` ya existe — mostrarlo en el card pendiente y en el toast de confirmación. | **P1** |
| MS-03 | Aviso sonoro/visual cuando un pedido pasa a "Listo" → cubierto por UI-08. | — |

### 5.5 `/carta` (admin)

| ID | Hallazgo | Prioridad |
|---|---|---|
| CT-01 | **No se puede editar la descripción del producto** desde el modal (`carta.py:280-504` no tiene input de descripción), pero la carta pública **la muestra** (`menu_publico.py:45-50`). Hoy la descripción solo se carga por seed/SQL. Agregar `rx.text_area` descripción al form + campo en el handler `guardar_producto`. | **P0** |
| CT-02 | Reordenar con campo numérico "Orden" es tosco. Mínimo: botones ↑/↓ por fila. Ideal: drag & drop si hay componente Reflex viable (verificar reflex-docs). | **P2** |
| CT-03 | **Duplicar producto** (copiar y editar) — ahorro real al cargar cartas grandes. Solo state + botón. | **P2** |
| CT-04 | Mostrar **margen** inline por producto (precio vs costo receta — el dato ya existe en reportes `_margen_row`). Badge de % en `_producto_row`. | **P2** |
| CT-05 | Modificadores/variantes/combos → ver FEAT-01 (backend primero). | **P1** |

### 5.6 `/menu/[slug]` (carta pública QR)

| ID | Hallazgo | Prioridad |
|---|---|---|
| MP-01 | **Buscador de productos** (la carta admin ya tiene; el comensal no). Input sticky bajo los chips. | **P1** |
| MP-02 | **Branding del local**: header muestra el favicon TUWAYKIFOOD; debería mostrar el **logo del restaurante** (`Company.logo_url` ya existe y se usa en login `login.py:151-183`). El QR es del local, no de la plataforma. | **P0** |
| MP-03 | Mostrar **promos activas** del local como banner arriba de la carta (datos ya existen en Promocion). | **P2** |
| MP-04 | Etiquetas de producto (🌶 picante, 🌱 veggie, alérgenos) → requiere BE-08 (tags). | **P2** |
| MP-05 | Self-order (pedir desde el QR) → FEAT-05, fase grande. | **P2** |

### 5.7 `/reportes`

| ID | Hallazgo | Prioridad |
|---|---|---|
| RP-01 | **Gráficos reales**: "Ventas por hora" es un bar de divs (`reportes.py:146-162`). Reflex trae **recharts** (`rx.recharts`) — agregar gráfico de líneas/barras para ventas por hora y evolución del período (verificar API en reflex-docs). | **P1** |
| RP-02 | Comparativa entre períodos (semana actual vs anterior) — el state ya calcula trends para "hoy vs ayer"; extender al rango filtrado. | **P2** |
| RP-03 | Desglose por método de pago del período (torta o barras apiladas) — dato ya existe en historial. | **P2** |

### 5.8 `/configuracion` y `/dono`

| ID | Hallazgo | Prioridad |
|---|---|---|
| CF-01 | **Botón "Imprimir ticket de prueba"** en sección Impresoras (genera ticket dummy con `receipt_service` y dispara `window.print()`). Hoy se configura IP/puerto a ciegas. | **P1** |
| CF-02 | **Preview del ticket** (nombre local, RUC, dirección, mensaje) renderizado al lado del form — los campos ya están en `ConfigImpresora`. | **P2** |
| CF-03 | `dono.py` duplica paleta y shell propio → unificar con `theme.py` (UI-01) y evaluar compartir `app_shell`. | **P2** |
| CF-04 | Gestión de **sectores de mesas** cuando exista BE-03 (CRUD simple en sección Mesas). | **P1** (con MZ-01) |

---

## 6. CORRECCIONES DE BACKEND REQUERIDAS POR EL FRONTEND

> Ordenadas por lo que desbloquean. Toda migración con Alembic + backfill seguro.

| ID | Cambio | Desbloquea | Detalle |
|---|---|---|---|
| **BE-01** | **Partir `FoodState` (6457 líneas) en mixins por dominio** | Performance y mantenibilidad de TODO el frontend | Ya existe el patrón (`caja_turno_mixin.py`). Extraer: `inventario_mixin`, `clientes_cuentas_mixin`, `promos_cupones_mixin`, `reportes_mixin`, `carta_mixin`. En Reflex, un state gigante infla los deltas WebSocket y el cómputo de vars — con tablets en LAN se nota. Hacerlo incremental (un mixin por PR), sin cambiar nombres públicos de vars/handlers para no romper páginas. |
| **BE-02** | **Campo `estacion` en `Categoria`** (enum: `cocina` \| `barra`, default `cocina`) | KD-02 (KDS por estación), comandas separadas | Migración + selector en form de categoría + filtro en queries de cocina. Si un producto puntual difiere de su categoría, override opcional en `Producto.estacion` (nullable). |
| **BE-03** | **`Mesa.sector`** (string simple o tabla `Sector`) | MZ-01, CF-04 | Empezar con string + datalist de sectores existentes; tabla solo si piden orden/colores. |
| **BE-04** | **Transferir / juntar mesas** | MZ-02 | `transferir_pedido(pedido_id, mesa_destino_id)`: validar destino libre u ocupado (merge), actualizar `mesa_id`, registrar auditoría (motivo + usuario, mismo patrón que anulaciones). Merge: reasignar `DetallePedido` al pedido destino y cancelar el origen con motivo "fusión". |
| **BE-05** | **Pre-cuenta en `receipt_service`** | CJ-01 | Nuevo template (sin métodos de pago, con leyenda "PRE-CUENTA — NO ES COMPROBANTE"). Opcional: marcar `Pedido.precuenta_impresa_at` para métricas. |
| **BE-06** | **Pago por ítems** | CJ-02 | Tabla puente `pago_detalle` (pago_id, detalle_id, cantidad) o campo JSON en `PagoPedido.detalle_ids`. Validar que la suma de ítems asignados cubra el pedido al confirmar. |
| **BE-07** | **Modelo de modificadores** | FEAT-01, CT-05 | Ver FEAT-01. Es el cambio de modelo más grande: hacerlo en rama dedicada con seed de prueba. |
| **BE-08** | **`Producto.tags`** (JSON: picante, veggie, sin_gluten, alérgenos) | MP-04 | Campo JSON + chips en form de producto + render en carta pública. |
| **BE-09** | **Config extra en `ConfigImpresora`**: `kds_minutos_alerta`, `propina_sugerida_pcts`, `sonidos_activos` | KD-05, CJ-03, UI-08 | Una migración conjunta. |
| **BE-10** | Deudas ya conocidas (backlog previo, siguen vigentes): PINs en texto plano (bcrypt instalado sin usar), `cobrar_mesa()` no descuenta stock, polling sin `on_unload` (mitigado con flags — revisar si la versión actual de Reflex ya ofrece algo mejor antes de refactorizar). | Seguridad/consistencia | Ver `MEMORY` del proyecto (audit 2026-06-19). |

---

## 7. MEJORAS DE PRODUCTO — RUBRO GASTRONOMÍA Y BEBIDAS

> Para que TUWAYKIFOOD compita como sistema profesional de restaurantes/restobares/bares. Ordenadas por impacto en el rubro.

### FEAT-01 · Modificadores y variantes de producto — **P1, el gap más importante**
Hoy un producto es nombre+precio+nota libre. Un restobar real necesita: tamaño (pinta/media), término de cocción, extras con precio (+queso S/2), exclusiones (sin hielo, sin cebolla), sabor. La nota libre no descuenta stock ni suma al precio.
- **Modelo:** `GrupoModificador` (nombre, min/max selecciones, por producto o categoría) → `OpcionModificador` (nombre, precio_extra, insumo_id opcional para stock). `DetallePedido.modificadores` (JSON snapshot con nombre+precio al momento).
- **UI:** al tocar un producto con modificadores en mozos/mostrador, abrir bottom-sheet de opciones antes de agregar al carrito; el KDS y la comanda impresa muestran los modificadores en línea bajo el ítem.
- **Admin:** sección en `/carta` para definir grupos y asignarlos.

### FEAT-02 · Combos y promos de producto — **P1**
`Promocion` hoy es descuento sobre el total. Falta: combo a precio fijo (hamburguesa+papas+bebida S/25) y 2x1 por producto. Modelo `Combo` (items + precio) que en el pedido se expande a sus componentes para stock/cocina pero factura como uno.

### FEAT-03 · Happy hour / promos por horario — **P1 (verificar)**
Para bares es central. Revisar si `Promocion` ya soporta rango horario/días (página `/promociones` existe); si no, agregar `hora_desde/hora_hasta/dias_semana` y aplicar automáticamente en carta pública y sugerencia en caja.

### FEAT-04 · Reservas de mesa — **P2** (ya en roadmap Fase 3)
CRUD de reservas (fecha/hora/pax/cliente) + indicador en el mapa de mozos ("Reservada 21:00").

### FEAT-05 · Self-order desde el QR — **P2**
La carta pública ya existe; el paso natural es carrito + "llamar mozo" + envío del pedido a una cola de aprobación del mozo (nunca directo a cocina sin validación). Gran diferenciador SaaS, pero requiere diseño de seguridad (mesa token en QR).

### FEAT-06 · Facturación electrónica (SUNAT) — **P2** (Fase 3 acordada)
Boleta/factura con IGV — los campos RUC/IGV ya están en `ConfigImpresora`. Integración con PSE/OSE peruano.

### FEAT-07 · Módulo Delivery — **P3**
Canal "delivery" como `TipoPedido` adicional (hoy hay mesa/mostrador), con datos de dirección/teléfono y estado de reparto. Integraciones (Rappi/PedidosYa) recién después.

### FEAT-08 · Vista "Dashboard del día" para el dueño en el celular — **P3**
El panel dono ya existe; una vista resumida mobile-first (ventas en vivo, mesas abiertas, alertas de stock) es el uso real del dueño fuera del local.

---

## 8. PLAN DE IMPLEMENTACIÓN SUGERIDO

**Sprint A — Pulido operativo (P0, ~1 semana): ✅ COMPLETADO** (commit `c800019` + `e350b50`)
- ✅ UI-10 (código muerto mozos ~460 líneas eliminadas)
- ✅ UI-04 (toasts en enviar_pedido, confirmar_cobro, guardar_producto)
- ✅ UI-05 + CJ-05 (targets táctiles 40×40px, tipografías 12-13px en footer caja)
- ✅ KD-01 (columna "Listo" en cocina con botón "Volver a preparación")
- ✅ CJ-01 + BE-05 (pre-cuenta imprimible con receipt_service)
- ✅ CT-01 (campo descripción producto en /carta)
- ✅ MP-02 (logo dinámico del restaurante en carta pública)
- ✅ UI-01 fase a-c (theme.py centralizado, duplicados eliminados de shared.py y dono.py)

**Extras implementados (sesión 2026-07-04):** (commit `e350b50`)
- ✅ Auto-print tickets cocina desde polling caja/cocina (pedidos de mozos y mostrador)
- ✅ Editar pedido mostrador desde Caja (botón Editar → anula + carga carrito + redirige)
- ✅ Feed lines: 5 líneas en blanco en todos los tickets para corte manual
- ✅ Fix doble-print mostrador, fix init auto-print, fix pedidos cancelados en pendientes

**Sprint B — Dominio gastro core (P1, ~2-3 semanas): EN PROGRESO**
- ✅ CJ-03 (propina sugerida con chips 5%/10%/15%)
- ✅ CJ-04 (descuento por porcentaje con toggle S/%)
- ✅ BE-02 + KD-02 (estaciones cocina/barra — enum EstacionCocina, campo estacion en Categoria y Producto, filtro Todo/Cocina/Barra en KDS, select en form categoría, migración 8fe5fb3c54f1)
- ✅ BE-03 + MZ-01 + CF-04 (sectores de mesas — Mesa.sector string, filtro/agrupación por sector en mozos, campo sector en form config mesas, migración c6c6d83f95dd)
- ✅ KD-03 (bump por ítem individual — ícono ✓ clickeable en items de tickets en_preparacion, handler bump_item_cocina)
- ✅ KD-04 (modo fullscreen cocina — botón Expandir/Salir oculta sidebar+topbar)
- ✅ UI-08 + BE-09 (sonidos: bell en cocina al entrar ticket pendiente, chime en mozos al haber items listos; toggle volume on/off en header de ambas páginas; detección por delta en polling)
- ✅ MZ-02 + BE-04 (transferir/juntar mesas: botón "Transferir mesa" en modal → sub-dialog con grid de mesas destino; libre=mover pedido, ocupada=fusionar detalles y cancelar origen)
- ✅ MZ-03 (86 rápido — marcar agotado desde mozos: botón 🚫 en card + card agotado con badge AGOTADO + botón reponer ↩)
- ✅ MS-01 (notas por ítem en mostrador: mismo patrón mozos + nota persiste en DetallePedido)
- ✅ MS-02 (número de pedido #ID visible en tarjetas mostrador+caja + toast al enviar)
- ✅ UI-06 (loading placeholder con spinner en mozos/cocina/caja/mostrador via flag pagina_cargada)
- ✅ UI-07 (aviso de desconexión en español — overlay_component con banner+modal custom)
- ✅ UI-09 (login con teclado físico — input oculto auto-focus + handler login_keydown 0-9/Enter/Backspace/Escape)
- ✅ CF-01 (ticket de prueba en config — botón en sección Impresoras genera ticket demo con datos del local)
- ✅ RP-01 (gráficos reales con rx.recharts — bar_chart para ventas por hora y por mozo con tooltip, responsive_container, loading_placeholder en reportes)

**Sprint C — Modelo de producto profesional (P1 grande): EN PROGRESO**
- ✅ FEAT-01 + BE-07 (modificadores de producto — 3 tablas: GrupoModificador, OpcionModificador, ProductoGrupoModificador + DetallePedido.modificadores_json; admin CRUD en /carta con modal grupo+opciones y asignación a productos; modal selección en mozos y mostrador con validación min/max; display en carrito, KDS y tickets; migración 72325b029491)
- ✅ FEAT-02 (combos a precio fijo — 2 tablas: Combo, ComboItem + DetallePedido.combo_items_json; admin CRUD en /carta con modal nombre/precio/emoji/items; catálogo en mozos y mostrador con cards; display combo badge en carrito; KDS muestra componentes; stock se descuenta por componentes; ticket cobro muestra detalles combo; migración 211cb3440c87)
- ✅ CJ-06 (confirmación post-cobro — ya implementado: toast success + auto-print ticket al confirmar cobro)
- ✅ CJ-07 (ticket cierre turno — ya implementado: generate_cash_close_ticket_html + build_print_script al cerrar turno)
- FEAT-03 (happy hour) → CJ-02 + BE-06 (split por ítems).

**Continuo:** BE-01 (un mixin extraído por sprint), UI-01 fase d (migración de hex a constantes en cada página tocada), UI-14 (copy).

**Fase 3 (a acordar con el usuario):** FEAT-04, FEAT-05, FEAT-06, FEAT-07, bcrypt de PINs.

---

## 9. VERIFICACIÓN (obligatoria tras cada cambio)

```bash
# Smoke test — usar 127.0.0.1 (NO localhost, en Windows resuelven distinto)
routes=("/api/ping" "/api/health" "/" "/login" "/mozos" "/cocina" "/caja" "/mostrador" "/carta" "/reportes" "/usuarios" "/configuracion" "/dono/login" "/dono" "/inventario" "/clientes" "/cuentas" "/promociones" "/menu/mi-restaurante")
for r in "${routes[@]}"; do
    code=$(curl -o /dev/null -sw "%{http_code}" -L "http://127.0.0.1:3003$r")
    [ "$code" = "200" ] && echo "OK  $r" || echo "FAIL $code $r"
done
```

Checklist por cambio de UI:
- [ ] Compila sin errores (`reflex run` según skill `reflex-process-management`).
- [ ] Smoke test 19/19.
- [ ] Verificado en viewport móvil (375px), tablet (768px) y desktop (1280px).
- [ ] Página oscura sigue oscura / clara sigue clara (hack `.light`, ver UI-03).
- [ ] Sin hex nuevos: colores desde `theme.py`/constantes (UI-01).
- [ ] Si tocó modelos: migración Alembic aplicada y reversible en local.
- [ ] Targets táctiles ≥ 40px en páginas operativas (UI-05).

---

## 10. RESUMEN EJECUTIVO

El sistema está **funcionalmente maduro** (flujo mesa→comanda→cocina→cobro→arqueo completo, multi-tenant, auditoría de anulaciones) y **visualmente consistente en intención** (identidad naranja/slate, dark para operación, light para admin). Los problemas no son de rediseño sino de **consolidación y profundidad de dominio**:

1. **Deuda de sistema de diseño:** paleta triplicada + estilos inline masivos + CSS por script → consolidar (UI-01/02).
2. **Ergonomía POS:** targets y tipografías chicas, feedback sin toasts, sin sonido, sin estados de carga → Sprint A/B.
3. **Gaps del rubro:** modificadores de producto, estaciones cocina/barra, pre-cuenta, split por ítems, sectores de salón, transferencia de mesas → es lo que separa un MVP de un sistema profesional de gastronomía; ninguno requiere rediseñar lo existente, todos extienden patrones ya presentes.
4. **Riesgo técnico principal:** `food_state.py` de 6457 líneas — partirlo en mixins es la inversión que abarata todo lo demás.
