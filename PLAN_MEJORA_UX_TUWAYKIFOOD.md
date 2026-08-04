# PLAN DE MEJORA UX/VISUAL — TUWAYKIFOOD

> **Fecha:** 2026-08-04 · **Alcance:** Auditoría completa módulo por módulo (parte operativa + parte administrativa) enfocada en **claridad para el usuario**: que cada módulo se entienda solo — qué es, qué hace y qué se puede hacer en él — y mejora visual integral.
>
> **Relación con `AUDITORIA_FRONTEND_TUWAYKIFOOD.md` (2026-07-04):** aquel documento cubre arquitectura visual y features de producto; varios de sus ítems ya se implementaron (toasts, sonidos, banner de desconexión, modificadores, combos, reservas, delivery, tema oscuro operativo, español neutro parcial). **Este documento lo complementa** con foco en comprensibilidad y autoexplicación de cada módulo. Donde un ítem viejo siga pendiente y aplique, se referencia con su ID original (`UI-xx`).

---

## 0. CÓMO USAR ESTE DOCUMENTO

1. Trabajar por prioridad: **P0 → P1 → P2**. Cada ítem tiene ID (`T-xx` transversal, `M-xx` por módulo) para referenciar en commits.
2. Antes de escribir código Reflex, usar el skill **`reflex-docs`** (el proyecto usa Reflex 0.9.x; **no hay setters automáticos** — definir `set_*` explícitos).
3. Después de cada cambio: `reflex compile --dry`, verificación visual local (Docker :3003), y recién después commit.
4. **Todo texto de producto en español neutro latinoamericano** (tuteo neutro: "Elige", "Carga", "Agrega" — **nunca** voseo "Elegí" ni usted "Seleccione").
5. No romper multi-tenant (`_tenant_session()` / `company_id`) ni renombrar rutas existentes (hay QRs impresos).

---

## 1. MAPA ACTUAL DEL SISTEMA (quién ve qué)

### Parte OPERATIVA (shell staff oscuro — `app_shell` de `shared.py`)

| Ruta | Módulo | Descripción en nav | Rol |
|---|---|---|---|
| `/login` | Login PIN | — | Todos |
| `/mozos` | Mozos | "Mesas y comanda" | Mozo |
| `/caja` | Caja | "Cobro y tickets" | Caja |
| `/mostrador` | Mostrador | "Takeaway rápido" | Mozo/Caja |
| `/cocina` | Cocina (KDS) | "KDS / Producción" | Cocina |
| `/estacion-impresion` | Impresión | "Comandas a la térmica" | Caja |
| `/carta` | Carta | "Carta y precios" | Admin |
| `/reportes` | Reportes | "Ventas del día" | Admin/Caja |
| `/usuarios` | Usuarios | "Personal y PINs" | Admin |
| `/configuracion` | Configuración | "Impresoras y local" | Admin |

### Parte ADMINISTRATIVA (shell propio del dueño — `_dono_shell` de `dono.py`)

| Sección | Descripción en sidebar |
|---|---|
| Resumen | "Vista general del día" |
| Reportes | "Dashboard y ventas del día" |
| Clientes | "Fidelización y alertas" |
| Cuentas | "Fiado y créditos" |
| Promociones | "Descuentos y cupones" |
| Reservas | "Mesas reservadas" |
| Delivery | "Pedidos a domicilio" |
| Inventario | "Stock y alertas" |
| Usuarios | "Personal y PINs" |
| Configuración | "Ajustes del sistema" |

### Configuración (submódulos — `configuracion.py:_SECCIONES`)

| Submódulo | Descripción actual |
|---|---|
| Local | "Nombre del restaurante" |
| Carta digital | "Slug URL y código QR" |
| Mesas | "Salón y sectores" |
| Sucursales | "Multi-local" |
| Impresoras | "Cocina y caja" |
| Cuenta Admin | "Email y contraseña" |

### Público
- `/menu/[slug]` — carta digital QR + self-order.

---

## 2. HALLAZGOS TRANSVERSALES (afectan a todos los módulos)

### T-01 · Copy mezclado: "usted" vs tuteo neutro — **P0 (rápido, alto impacto)**

La regla del producto es tuteo neutro ("Elige", "Carga"), pero quedan **~20 textos en forma "usted"**:

| Archivo:línea | Texto actual | Corregir a |
|---|---|---|
| `app/pages/caja.py:229` | "Seleccione ítems en la lista y asigne un pago…" | "Selecciona ítems… y asigna…" |
| `app/pages/caja.py:889` | "Seleccione una mesa para cobrar" | "Selecciona una mesa para cobrar" |
| `app/pages/carta.py:908` | "Seleccione los grupos que aplican…" | "Selecciona los grupos…" |
| `app/pages/carta.py:1328` | "…Haga clic en «Nueva Categoría»…" | "…Toca «Nueva Categoría»…" |
| `app/pages/carta.py:1407` | "…Haga clic en «Nuevo Producto»…" | "…Toca «Nuevo Producto»…" |
| `app/pages/configuracion.py:485` | "Agregue mesas usando el formulario…" | "Agrega mesas con el formulario…" |
| `app/pages/dono.py:1627` | "Ingrese con su email y contraseña" | "Ingresa con tu email y contraseña" |
| `app/pages/inventario.py:860` | "Seleccione producto o combo…" | "Selecciona producto o combo…" |
| `app/pages/inventario.py:963` | "…Verifique que los productos tengan recetas…" | "…Verifica que los productos…" |
| `app/pages/login.py:265` | "Ingrese su PIN" | "Ingresa tu PIN" |
| `app/pages/mostrador.py:679` | "Seleccione las opciones…" | "Elige las opciones…" |
| `app/pages/mozos.py:798,914,1204` | "Seleccione…" (×3) | "Selecciona / Elige…" |
| `app/states/carta_mixin.py:790,943,990` | "Seleccione…" (×3) | "Selecciona…" |
| `app/states/clientes_cuentas_mixin.py:341,476` | "Ingrese… / Seleccione…" | "Ingresa… / Selecciona…" |
| `app/states/food_state.py:1763` | "…Ingrese nuevamente." | "…Ingresa nuevamente." |

**Tarea:** barrido único con verificación final `grep -rnE "Seleccione|Verifique|Ingrese|Haga clic|Agregue|Presione" app/` → 0 resultados.

### T-02 · Encabezado de módulo autoexplicativo + ayuda "¿Cómo funciona?" — **P0 (el corazón de este plan)**

Hoy cada página tiene título + subtítulo de una línea (bien), pero **ningún módulo explica su flujo de trabajo**. Un empleado nuevo no tiene dónde leer "qué se hace acá".

**Tarea:** crear en `shared.py` un componente reutilizable:

```
module_header(
    titulo="Salón",
    subtitulo="Mesas y comandas en curso",
    ayuda_titulo="¿Cómo funciona Mozos?",
    ayuda_pasos=[...],       # 3–6 pasos del flujo normal
    acciones=[...],          # botones existentes (sonido, etc.)
)
```

- Título + subtítulo como hoy, **más un botón de ícono `circle_help`** que abre un modal/panel con: qué es el módulo, el flujo paso a paso, y qué significa cada estado/color.
- El contenido de ayuda por módulo se define en un dict central (`app/components/ayuda.py`) para mantener consistencia y facilitar traducciones/ajustes.
- Aplicarlo a las 10 páginas staff + secciones dono. Contenidos concretos por módulo en la sección 3.

### T-03 · Estados vacíos accionables (con botón que lleva a la solución) — **P0**

Los estados vacíos existen pero son **pasivos** ("No hay mesas configuradas.", "Sin insumos registrados."). El usuario queda sin saber qué hacer.

**Patrón a aplicar** (componente `empty_state(icono, titulo, texto, cta_label, cta_href|on_click)`):

| Dónde | Hoy | Debe ofrecer |
|---|---|---|
| `mozos.py:354` | "No hay mesas configuradas." | Botón "Configurar mesas" → `/configuracion` (sección mesas) — solo si es Admin; si es mozo: "Pide al administrador que configure las mesas." |
| `caja.py:889` | "Seleccione una mesa para cobrar" (panel central) | Mini-explicación del flujo: "Elige una mesa de la izquierda. Ahí vas a ver su consumo y podrás cobrar." |
| `inventario.py:607` | "Sin insumos registrados. Agrega el primero." | CTA que abre el formulario de insumo directamente |
| `carta.py:1328/1407` | "Sin categorías/productos. Haga clic en…" | CTA que abre el form + neutro (T-01) |
| `clientes` | (sin estado vacío detectado) | Agregar: "Sin clientes aún. Se registran aquí para fiado, cumpleaños y fidelización." + CTA "Nuevo cliente" |
| `cuentas` | — | "Las cuentas se crean solas al registrar el primer fiado en Caja." + link "¿Cómo fiar? → ayuda de Caja" |
| `promociones/cupones` | — | CTA "Crear primera promoción / primer lote" + 1 línea de qué logra |

### T-04 · Checklist de puesta en marcha (onboarding del dueño) — **P1**

Un restaurante nuevo no sabe el orden de configuración. **Tarea:** tarjeta "Primeros pasos" en `/admin` (Resumen), visible mientras falten pasos, con checks calculados de la BD:

1. ✅ Nombre del local (Configuración → Local)
2. ⬜ Carga tu carta (categorías + productos)
3. ⬜ Configura tus mesas y sectores
4. ⬜ Crea los usuarios y PINs de tu equipo
5. ⬜ Configura la impresión (navegador o agente)
6. ⬜ (Opcional) Activa tu carta digital QR

Cada paso con link directo. Se puede descartar ("No mostrar más").

### T-05 · Nombres e íconos inconsistentes entre navegación, títulos y dono — **P1**

El mismo módulo se presenta con distintos nombres/íconos según dónde se mire, lo que rompe el modelo mental:

| Módulo | Nav staff | Título en página | Sidebar dono |
|---|---|---|---|
| Carta | "Carta" (book_open) | **"Carta / Admin"** (`carta.py:1266`) | — |
| Reportes | "Reportes" (**receipt_text**) | "Reportes" | "Reportes" (**trending_up**) |
| Usuarios | "Usuarios" (users) | **"Usuarios del sistema"** (`usuarios.py:513`) | "Usuarios" (users_round) |
| Mozos | "Mozos" (layout_grid) | **"Salón"** (`mozos.py:1478`) | quick-link "Mozos" |

**Tarea:** una sola fuente de verdad (`app/components/modulos.py`: dict con nombre, ícono, descripción corta, descripción de ayuda por módulo) consumida por nav staff, títulos, sidebar dono y quick-links. Decidir nombre canónico (recomendado: "Mozos · Salón" → título "Salón" está bien si la nav también dice "Salón"; lo importante es que coincidan).

### T-06 · Botones de solo ícono sin tooltip — **P1**

Sonido (`mozos.py:1487`, `cocina.py:315`), colapsar sidebar, refrescar, expandir KDS, editar/eliminar en listas: ninguno tiene `rx.tooltip`. En tablets el hover no existe, pero en desktop ayuda y no estorba.
**Tarea:** envolver icon-buttons en `rx.tooltip(content="...")` (verificar API con `reflex-docs`). Mínimo: sonido ("Activar/silenciar avisos sonoros"), expandir ("Pantalla completa"), refrescar ("Actualizar ahora"), colapsar sidebar.

### T-07 · Doble navegación (staff vs dono) sin explicación — **P1**

`Inventario`, `Clientes`, `Cuentas`, `Promociones`, `Cupones` viven en el shell del dono; `Carta`, `Reportes`, `Usuarios`, `Configuración` en el shell staff, pero el dono también los lista. El usuario ve dos "casas" distintas y módulos que cambian de lugar.

**Tarea (mínima, sin reestructurar):**
- En el sidebar staff, botón "Panel Administrativo" ya existe — agregarle subtítulo "Reportes del dueño, inventario y más".
- En el dono, agrupar el sidebar con encabezados: **"Análisis"** (Resumen, Reportes), **"Clientes"** (Clientes, Cuentas, Promociones), **"Operación extendida"** (Reservas, Delivery, Inventario), **"Sistema"** (Usuarios, Configuración).
- En cada quick-link del Resumen, mantener la descripción corta (ya está bien).

### T-08 · Nav "Impresión" no refleja el modo de impresión — **P2**

La entrada "Impresión — Comandas a la térmica" (`shared.py:281,384`) aparece siempre. En modo **agente**, la estación no imprime (la página ya lo explica, bien). **Tarea:** cambiar la descripción de la entrada según `config_modo_impresion`: navegador → "Comandas a la térmica"; agente → "Estado de impresión". (No ocultarla: sirve de monitoreo.)

### T-09 · `loading_placeholder` ignora su parámetro `dark` — **P2 (bug menor)**

`shared.py:735-748`: calcula `bg`/`accent`/`text_color` y no los usa (spinner y texto con valores fijos). Inofensivo hoy porque el texto gris funciona en ambos temas, pero es código muerto confuso. **Tarea:** usar las variables o eliminarlas.

### T-10 · Deuda visual heredada (auditoría 2026-07) — **P2**

Siguen aplicando: **UI-01** (paleta triplicada `shared.py` / `dono.py` / hex inline — migración oportunista a `theme.py`), **UI-02** (CSS global por `rx.script`), **UI-12** (z-index sin escala documentada). Mantener la política: cada vez que se toque un archivo por este plan, migrar sus hex crudos a constantes.

---

## 3. PLAN POR MÓDULO — PARTE OPERATIVA

### 3.1 `/login` — **M-01**

**Qué es hoy:** selector de restaurante → rol → PIN con teclado tipo iPhone. Sólido, con pasos rotulados ("ELIGE TU RESTAURANTE", "SELECCIONA TU ROL").

**Mejoras:**
- **M-01a (P0):** `login.py:265` "Ingrese su PIN" → "Ingresa tu PIN" (T-01).
- **M-01b (P1):** al elegir rol, mostrar 1 línea de qué verá ese rol: Mozo → "Mesas y toma de pedidos"; Cocina → "Pantalla de preparación"; Caja → "Cobros y turno"; Admin → "Todo el sistema". Reutilizar las descripciones de T-05.
- **M-01c (P2):** indicador de paso ("Paso 2 de 3") para reforzar dónde está el usuario.

### 3.2 `/mozos` (Salón) — **M-02**

**Qué es hoy:** mapa de mesas por sector con leyenda de 4 estados (Libre/Ocupada/Cuenta/Reservada, `mozos.py:291-315`), modal de comanda con carrito, historial, transferencia de mesa, modificadores, combos, self-orders pendientes.

**Hallazgos:**
- El flujo central (tocar mesa → agregar productos → **Enviar a cocina**) no se explica en ningún lado; un mozo nuevo depende de que alguien le muestre.
- Estado vacío pasivo (`mozos.py:354`, ver T-03).
- La tarjeta de mesa muestra estado por color; falta reforzar con texto corto en la tarjeta para daltonismo/aprendizaje (la leyenda existe pero está arriba, separada).
- Notas de producto con buen placeholder ("Ej: sin azúcar, extra picante...") ✔.

**Mejoras:**
- **M-02a (P0):** ayuda de módulo (T-02) con el flujo: "1) Toca una mesa · 2) Agrega productos (con opciones y notas) · 3) Envía a cocina · 4) Cuando pidan la cuenta, genera la precuenta · 5) Caja cobra". Incluir el significado de los 4 colores.
- **M-02b (P0):** estado vacío accionable (T-03).
- **M-02c (P1):** micro-etiqueta de estado dentro de cada tarjeta de mesa ("Libre", "Ocupada 25 min", "Cuenta pedida") además del color.
- **M-02d (P2):** en el modal de comanda, dejar visible el subtotal acumulado y un hint "Los ítems no se envían hasta tocar Enviar a cocina" la primera vez.

### 3.3 `/cocina` (KDS) — **M-03**

**Qué es hoy:** el módulo más maduro visualmente: columnas Pendiente/En preparación/Listo, filtros Todo/Cocina/Barra, leyenda de colores (incl. "Demorado"), pantalla completa, sonidos, última actualización.

**Hallazgos:**
- Leyenda oculta en móvil/tablet chica (`display=lg`, `cocina.py:313`) — justo donde más se necesita.
- Filtros "Cocina"/"Barra" hardcodeados; si el local no usa estaciones, ocupan espacio y confunden.
- Sin ayuda del flujo (qué botón toca el cocinero para avanzar un ticket).

**Mejoras:**
- **M-03a (P1):** ayuda de módulo (T-02): "Cada tarjeta es una comanda. Tócala para pasarla a En preparación y luego a Listo. Roja = demorada (más de X min)."
- **M-03b (P1):** mostrar la leyenda también en pantallas chicas (colapsada en una fila compacta o dentro de la ayuda).
- **M-03c (P2):** ocultar filtros de estación si la carta no tiene productos con estación "barra" (consultar una vez en `on_load`).

### 3.4 `/caja` — **M-04**

**Qué es hoy:** el módulo más complejo: turno (apertura/cierre con arqueo por denominaciones), cobro con métodos/pagos divididos/fiado/cupones/promos, mesas por cobrar + para llevar, movimientos (ingresos/gastos), historial de turnos, últimos cobros, reversión, resumen del día.

**Hallazgos:**
- Densidad alta sin guía: la barra de turno tiene 4 botones ("Ingresos / Gastos", "Últimos cobros", "Historial", "Cerrar turno") sin explicación de qué hace cada uno.
- Panel central vacío dice solo "Seleccione una mesa para cobrar" (además en usted).
- El flujo de pago dividido es potente pero críptico: "Monto (vacío = restante)" (`caja.py:187`) es la única pista.
- El concepto "turno" (por qué no puedo cobrar sin abrirlo) no se explica; la card de apertura existe (`caja.py:901`) pero no dice el porqué.

**Mejoras:**
- **M-04a (P0):** T-01 + T-03 en el panel central: "Selecciona una mesa de la izquierda para ver su consumo y cobrar. Los pedidos para llevar aparecen abajo."
- **M-04b (P0):** ayuda de módulo (T-02) con dos flujos: **Cobro normal** (mesa → método → confirmar → ticket) y **Turno** (abrir con fondo → operar → cerrar con arqueo; el sistema compara lo contado vs lo esperado y registra el descuadre).
- **M-04c (P1):** en la card "Abrir turno", agregar 1 línea: "El turno agrupa todos los cobros del día para el arqueo. Nadie puede cobrar sin turno abierto."
- **M-04d (P1):** tooltips en los 4 botones de la barra de turno (T-06).
- **M-04e (P2):** en pagos divididos, texto guía arriba del panel: "Agrega pagos hasta cubrir el total. Si dejas el monto vacío, se usa lo que falta."

### 3.5 `/mostrador` — **M-05**

**Qué es hoy:** takeaway rápido: catálogo → carrito → pedido; columnas de pendientes/entregados.

**Mejoras:**
- **M-05a (P0):** `mostrador.py:679` "Seleccione…" → neutro (T-01).
- **M-05b (P1):** ayuda de módulo (T-02): "Para clientes sin mesa: armas el pedido, se envía a cocina, y cuando está listo lo entregas y se cobra en Caja." (aclarar dónde se cobra — hoy es ambiguo).
- **M-05c (P2):** estados vacíos de columnas con texto útil ("Los pedidos enviados aparecen aquí hasta que cocina los termine").

### 3.6 `/estacion-impresion` — **M-06**

**Qué es hoy:** recién trabajado — estado según modo (navegador/agente), métricas, prueba, pasos de configuración de la PC. **Referencia del patrón a seguir** (`_instruccion` numerada = lo que T-02/T-03 piden para el resto).

**Mejoras:**
- **M-06a (P2):** cuando el modo es agente, agregar link "Configurar agente →" hacia Configuración → Impresoras.

---

## 4. PLAN POR MÓDULO — PARTE ADMINISTRATIVA

### 4.1 `/carta` — **M-07**

**Qué es hoy:** categorías, productos (con estación cocina/barra, orden, foto), combos, grupos de modificadores. Empty states de combos/modificadores ya explican qué son ✔ (`carta.py:1195,1240`).

**Mejoras:**
- **M-07a (P0):** título "Carta / Admin" → "Carta" (T-05); "Haga clic" ×2 → neutro (T-01).
- **M-07b (P1):** ayuda de módulo: qué es cada pestaña/sección (Categorías ordenan la carta; Productos con precio/foto/estación; Modificadores = opciones que elige el mozo, ej. término de cocción; Combos = paquete a precio fijo) y **dónde repercute** (mozos, mostrador, carta QR).
- **M-07c (P1):** en el form de producto, ayuda inline del campo "Estación": "Define a qué pantalla de cocina llega: Cocina o Barra."
- **M-07d (P2):** indicador visible de "este producto no tiene receta → no descuenta stock" con link a Inventario (conecta módulos).

### 4.2 `/reportes` — **M-08**

**Qué es hoy:** KPIs del día, top platos, ventas por mozo/hora, margen, descuentos/anulaciones/reversiones, historial con filtros. Empty states correctos ✔.

**Mejoras:**
- **M-08a (P1):** ayuda de módulo: qué responde cada bloque ("¿Cuánto vendí hoy?", "¿Qué platos salen más?", "¿Quién vendió más?") — el dueño no técnico agradece leer los reportes como preguntas.
- **M-08b (P1):** tooltips en KPIs con la definición exacta ("Ticket promedio = ventas cobradas ÷ número de cobros del período").
- **M-08c (P2):** unificar ícono con dono (T-05).

### 4.3 `/usuarios` — **M-09**

**Qué es hoy:** alta de personal con PIN y rol; descripciones de permisos por rol ya existen ✔ (`usuarios.py:243,290`).

**Mejoras:**
- **M-09a (P0):** título "Usuarios del sistema" → "Usuarios" (T-05).
- **M-09b (P1):** ayuda de módulo: "Cada empleado entra con su PIN de 4 dígitos desde la pantalla de login. El rol define qué módulos ve." + tabla rol→módulos (reutilizar T-05).
- **M-09c (P2):** al crear usuario, mostrar el PIN generado en grande con botón copiar (mismo patrón que el token de agente).

### 4.4 `/inventario` — **M-10**

**Qué es hoy:** insumos con stock/alertas/kardex, recetas por producto, planificador de producción. Subtítulo claro ✔.

**Mejoras:**
- **M-10a (P0):** "Seleccione"/"Verifique" → neutro (T-01).
- **M-10b (P1):** ayuda de módulo explicando la **cadena**: "Insumos (lo que compras) → Recetas (cuánto insumo lleva cada plato) → al cobrar, el stock se descuenta solo. El planificador calcula cuánto insumo necesitas para producir X platos."
- **M-10c (P1):** las 3 secciones (Insumos/Recetas/Producción) están apiladas en una página larga — convertir a tabs o anclas con navegación pegajosa para que se entienda que son 3 herramientas distintas.
- **M-10d (P2):** en Recetas, estado vacío que explique la consecuencia: "Sin receta, el producto se vende igual pero no descuenta stock."

### 4.5 `/clientes` — **M-11**

**Qué es hoy:** base de clientes + cumpleaños. Sin textos de ayuda ni estado vacío.

**Mejoras:**
- **M-11a (P1):** ayuda + estado vacío accionable (T-03): "Registra clientes para habilitar el fiado (cuenta corriente), recibir avisos de cumpleaños en Mozos/Caja y ver su historial."
- **M-11b (P2):** en la ficha, mostrar accesos: "Ver cuenta corriente →" (conecta con Cuentas).

### 4.6 `/cuentas` — **M-12**

**Qué es hoy:** cuentas corrientes (fiado). Ya explica "Se crea automáticamente al registrar el primer cargo fiado." ✔ (`cuentas.py:173`).

**Mejoras:**
- **M-12a (P1):** ayuda de módulo: el ciclo completo del fiado (Caja cobra "a cuenta" → se acumula aquí → se registran abonos → saldo). Con quién puede fiar (requiere cliente registrado).
- **M-12b (P2):** título "Cuentas Corrientes" → "Cuentas corrientes" (capitalización consistente con el resto).

### 4.7 `/promociones` y `/cupones` — **M-13**

**Qué es hoy:** dos módulos separados, pero el sidebar dono dice "Promociones — Descuentos y cupones" y el subtítulo de Promociones dice "Descuentos automáticos y cupones de código" — **el usuario no sabe cuál abrir**.

**Mejoras:**
- **M-13a (P1):** deslindar los conceptos en ambas páginas: Promociones = "Descuentos **automáticos** por horario o producto (ej. happy hour)"; Cupones = "Códigos que el cliente **presenta** y caja ingresa al cobrar". Ajustar subtítulos y descripciones de nav en consecuencia.
- **M-13b (P1):** ayuda de módulo en cada uno con 1 ejemplo concreto de punta a punta ("Creas el lote → imprimes/repartes códigos → caja lo aplica al cobrar → aquí ves cuántos se usaron").
- **M-13c (P2):** enlaces cruzados entre ambos ("¿Buscabas descuentos automáticos? → Promociones").

### 4.8 `/admin` (Resumen, Reservas, Delivery) — **M-14**

**Qué es hoy:** dashboard del dueño con KPIs, alertas (stock, cumpleaños), quick-links a módulos operativos, reservas y delivery con formularios propios, banner de upgrade para módulos no contratados.

**Mejoras:**
- **M-14a (P1):** checklist de puesta en marcha (T-04) en el Resumen.
- **M-14b (P1):** agrupar sidebar por secciones (T-07).
- **M-14c (P2):** ayuda en Reservas ("Anota reservas y la mesa aparece morada en el salón del mozo") y Delivery (estados del pedido y quién los avanza).

---

## 5. PLAN — CONFIGURACIÓN (cada submódulo autoexplicado)

> El patrón nuevo de **Impresoras** (selector de modo con tarjetas descriptivas + pasos numerados + descarga del agente) es la referencia. Llevar los otros 5 submódulos a ese nivel.

### M-15 · Submódulo **Local** — P1
Hoy: "Nombre del restaurante". Agregar intro: "Estos datos aparecen en los tickets impresos y en la carta digital." (conectar causa-efecto). Si hay más campos (moneda/IGV), explicar cada uno con 1 línea.

### M-16 · Submódulo **Carta digital** — P1
Hoy: "Slug URL y código QR". Agregar: qué es el slug con ejemplo en vivo ("tuwayki.app/menu/**tu-nombre**"), para qué sirve el QR (imprimirlo y pegarlo en mesas), y advertencia clara al cambiar el slug: "Los QR ya impresos dejarán de funcionar."

### M-17 · Submódulo **Mesas** — P0
Hoy: form + lista; estado vacío "Agregue mesas…" (usted, `configuracion.py:485`). Corregir a neutro + explicar el efecto: "Cada mesa que agregues aparece en el salón de los mozos. Usa sectores (Terraza, Barra) para agruparlas." Ítem del checklist T-04.

### M-18 · Submódulo **Sucursales** — P1
Hoy: "Multi-local". Explicar el modelo: "Si tienes más de un local, cada sucursal tiene sus propias mesas, impresoras y turnos. El personal elige sucursal al iniciar sesión." Y qué pasa si solo hay una (no afecta nada).

### M-19 · Submódulo **Impresoras** — P2 (ya es la referencia)
Pendientes menores: describir el efecto del ancho de papel ("58 mm = tickets angostos; 80 mm = estándar") y en modo navegador linkear a la Estación de impresión.

### M-20 · Submódulo **Cuenta Admin** — P1
Hoy: "Email y contraseña". Aclarar la diferencia clave que hoy nadie explica: "Esta cuenta (email + contraseña) es la del **dueño** y entra al Panel Administrativo. El personal entra con **PIN** desde la pantalla de inicio." (elimina la confusión de dos sistemas de login).

---

## 6. PLAN — CARTA PÚBLICA `/menu/[slug]` — **M-21 · P2**

Ya tiene carga/404 y confirmación de self-order ✔. Mejoras: (a) mensaje 404 con tono de marca; (b) en el flujo de self-order, indicar al cliente qué sigue ("El mozo confirmará tu pedido en breve") — ya existe en `menu_publico.py:361`, revisar visibilidad; (c) botón "Ver carta nuevamente" con estilo primario.

---

## 7. PLAN — MULTI-DISPOSITIVO Y PWA (escritorio · tablet · móvil)

> **Contexto:** el sistema se instala como **app nativa (PWA)** — los mozos toman pedidos desde el **celular**, cocina usa **tablet/pantalla**, caja usa **PC/tablet**, y el dueño revisa el panel desde **cualquier dispositivo**. Cada módulo debe funcionar perfecto en el dispositivo donde realmente se usa.

### Matriz módulo × dispositivo (dónde se usa de verdad)

| Módulo | Móvil (celu) | Tablet | Escritorio | Dispositivo primario |
|---|---|---|---|---|
| Mozos | ★★★ | ★★ | ★ | **Celular del mozo (PWA)** |
| Mostrador | ★★★ | ★★ | ★ | Celular/tablet |
| Cocina (KDS) | ★ | ★★★ | ★★ | **Tablet/pantalla fija** |
| Caja | ★ | ★★ | ★★★ | **PC de caja** |
| Carta / Reportes / Inventario / etc. | ★★ | ★★ | ★★★ | PC, pero el dueño consulta desde el celu |
| Carta pública QR | ★★★ | — | — | **Celular del cliente** |

### Estado actual (medido: usos de `rx.breakpoints` por página)

Bien cubiertas: `dono` (21), `mozos` (13), `reportes` (12), `caja` (10), `login` (9). **Flojas o nulas: `carta` (0), `cuentas` (0), `cocina` (1), `cupones` (1), `promociones` (1), `estacion_impresion` (1), `usuarios` (2), `clientes` (2).** (Varias compensan con `flex_wrap`, que ayuda pero no controla el orden ni el tamaño táctil.)

### D-01 · Páginas admin sin adaptación móvil real — **P0**

`carta.py` y `cuentas.py` no tienen **ningún** breakpoint; `usuarios`, `clientes`, `promociones`, `cupones` casi ninguno. El dueño abre estos módulos desde el celular (la PWA lo invita a hacerlo).

- **Tablas-grilla sin scroll controlado:** `inventario.py:268` (`_insumos_table_header`) y `usuarios.py:45` (`_usuarios_table_header`) arman filas tipo tabla de 5+ columnas **sin `overflow_x`** en ningún contenedor (grep = 0 resultados) → en móvil las columnas se aplastan o desbordan.
- **Tarea:** para cada tabla, elegir: (a) contenedor con `overflow_x="auto"` + `min_width` interna (scroll horizontal deliberado), o (b) colapsar a tarjetas apiladas en `initial` y tabla desde `md` (mejor para Insumos y Usuarios, que se consultan en el celu). Aplicar breakpoints a los forms de alta (hoy los inputs en fila se comprimen).

### D-02 · Targets táctiles chicos en vistas operadas con el dedo — **P0** (hereda UI-05)

Regla del proyecto: **≥ 40 px** en vistas operativas. Incumplen:

| Archivo:línea | Elemento | Tamaño actual |
|---|---|---|
| `mozos.py:608` | Botón ✓ guardar nota del ítem | 28×28 px |
| `mozos.py:601` | Input de nota | alto 28 px |
| `mostrador.py:64` | Indicador «+» de producto | 22×22 px |
| `mostrador.py:154,161` | Input de nota + botón ✓ | 28 px |
| `cocina.py:93,132` | Controles de ticket | alto 24 px |

**Tarea:** subir a ≥ 40 px en móvil/tablet (puede quedar más compacto en desktop vía breakpoints). En `mostrador.py:64`, si la tarjeta entera es la zona táctil, el «+» puede quedar chico como decoración — verificar y dejar comentario explícito en el código.

### D-03 · Modales en pantallas chicas — **P1**

Los modales usan `max_width` fijo (440–650 px: `caja.py:1142,1288,1353,1438`, `clientes.py:396`, `dono.py:1025`…) y **no todos** declaran ancho relativo de respaldo (`width="92vw"`). El modal de comanda de mozos ya se optimizó para móvil (commit `c81e670`) — usar ese patrón.
**Tarea:** barrido de todos los `rx.dialog.content`: garantizar `width="92vw"` (o `95vw`) + `max_height` con scroll interno + botones de acción alcanzables con el pulgar (columna en móvil si son 2+).

### D-04 · Cocina (KDS) en su dispositivo real — **P1**

La página asume pantalla ancha: columnas con `overflow_x="auto"` (`cocina.py:233`) y leyenda solo desde `lg` (`cocina.py:313`, ya en M-03b). En tablet vertical u operando desde un celu de apoyo, las 3 columnas quedan angostas o con scroll lateral sin indicio.
**Tarea:** en `initial/md`, apilar columnas verticalmente (Pendiente arriba) o tabs por estado; mantener el layout de 3 columnas desde `lg`. Indicador visual si hay scroll horizontal ("→ más columnas").

### D-05 · Protocolo de prueba por dispositivo — **P1 (proceso, no código)**

Definir 3 viewports canónicos y probar **cada módulo en el dispositivo del rol que lo usa** después de cada fase:

- **Móvil 360×800** (mozo con la PWA): Mozos, Mostrador, carta QR, y lectura de Reportes/admin.
- **Tablet 820×1180** (cocina/caja): KDS en horizontal y vertical, Caja.
- **Escritorio 1280+**: Caja, todos los admin, Configuración.

Con las herramientas del navegador embebido (`resize_window` mobile/tablet/desktop) esto se automatiza en la verificación de cada fase (ver sección 9).

### D-06 · Pulido PWA — **P2**

Lo hecho está bien: manifest completo (standalone, `orientation: any`, ícono maskable, `lang: es`) y SW passthrough puro (decisión correcta y documentada para un POS online).
Mejoras:
- **Página offline propia:** hoy sin red aparece el error del navegador. Como el SW ya intercepta `fetch`, servir un HTML mínimo embebido ("Sin conexión — revisa el WiFi del local y reintenta") con el estilo de la marca. (El banner rojo de reconexión ya cubre cortes breves con la app abierta ✔.)
- **`shortcuts` en el manifest:** mantener apretado el ícono → "Salón", "Caja", "Cocina" (cada rol salta directo a su módulo).
- **`screenshots` en el manifest:** el prompt de instalación de Chrome/Edge se ve mucho más profesional con capturas.

### D-07 · Safe areas iOS (notch/isla) — **P2**

En iPhone instalada como PWA (`display: standalone`), la topbar móvil (`shared.py:678`, `position="sticky"`, `top="0"`) puede quedar debajo del notch.
**Tarea:** agregar `padding-top: env(safe-area-inset-top)` al shell/topbar (vía CSS global `.twk-*`) y `viewport-fit=cover` en el meta viewport si no está.

---

## 8. ORDEN DE IMPLEMENTACIÓN SUGERIDO

### Fase 1 — Copy y quick wins (1 sesión) — todo P0 textual
1. **T-01** barrido usted→neutro completo (20 strings, incluye M-01a, M-04a-texto, M-05a, M-07a-texto, M-10a, M-17-texto).
2. **M-07a / M-09a** títulos canónicos ("Carta", "Usuarios").
3. **T-09** limpiar `loading_placeholder`.
4. Verificación: grep = 0 + compile + revisión visual.

### Fase 2 — Infraestructura de claridad (1–2 sesiones)
5. **T-05** dict central de módulos (nombre, ícono, descripciones).
6. **T-02** componente `module_header` + modal de ayuda; aplicar a Mozos, Caja, Cocina (los 3 críticos) con sus contenidos (M-02a, M-04b, M-03a).
7. **T-03** componente `empty_state` accionable; aplicar a Mozos, Caja, Carta, Inventario.

### Fase 3 — Multi-dispositivo (1–2 sesiones) — los P0 de la sección 7
8. **D-02** targets táctiles ≥ 40 px en Mozos, Mostrador, Cocina.
9. **D-01** responsive real en admin: tablas de Inventario/Usuarios (tarjetas u overflow controlado) + breakpoints en Carta, Cuentas, Clientes, Promos, Cupones.
10. **D-03** barrido de modales (ancho relativo + scroll interno + botones alcanzables).
11. **D-05** correr el protocolo de prueba en los 3 viewports.

### Fase 4 — Cobertura completa (2 sesiones)
12. T-02/T-03 al resto: Mostrador, Reportes, Usuarios, Inventario, Clientes, Cuentas, Promos/Cupones (M-13a deslinde), dono (M-14c).
13. **Configuración**: M-15 a M-20 (intros por submódulo; M-17 primero).
14. **T-06** tooltips en icon-buttons + **D-04** KDS apilado en pantallas chicas.

### Fase 5 — Onboarding y pulido (1–2 sesiones)
15. **T-04** checklist de puesta en marcha en /admin.
16. **T-07** agrupación del sidebar dono + subtítulo del link "Panel Administrativo".
17. **M-01b/M-01c** login con descripciones de rol y pasos.
18. **D-06/D-07** pulido PWA (offline propio, shortcuts, screenshots, safe areas iOS).
19. P2 restantes (M-03c, M-08b, M-10c tabs, T-08, M-21…).

---

## 9. VERIFICACIÓN (por fase)

1. `reflex compile --dry` limpio.
2. `grep -rnE "Seleccione|Verifique|Ingrese|Haga clic|Agregue |Presione|Cargá|Generá|Elegí|Ingresá" app/ agente/` → 0 resultados (neutro garantizado, sin usted ni voseo).
3. Revisión visual local (Docker :3003) de cada página tocada **en los 3 viewports canónicos** (D-05): móvil 360×800, tablet 820×1180, escritorio 1280+ — con el navegador embebido (`resize_window`). Verificar: sin scroll horizontal accidental, targets táctiles ≥ 40 px en operativas, modales completos y usables.
4. Prueba de comprensión: entrar con cada rol (mozo/cocina/caja/admin) y verificar que desde el login se puede llegar a entender el flujo de su módulo **solo con lo que está en pantalla** (título + ayuda + estados vacíos).
5. Prueba PWA (tras Fase 5): instalar la app, probar en el celular real de ser posible (mozo tomando un pedido completo de punta a punta).
6. Commit atómico por ID (`fix(ux): T-01 copy neutro`, `feat(ux): D-02 targets táctiles`…). Deploy solo con OK del usuario.

---

## 10. RESUMEN EJECUTIVO

| Eje | Problema | Solución | Ítems |
|---|---|---|---|
| **Copy** | 20 textos en "usted" mezclados con tuteo neutro | Barrido T-01 | P0 |
| **Comprensión** | Ningún módulo explica su flujo | `module_header` + ayuda "¿Cómo funciona?" por módulo (T-02) | P0 |
| **Estados vacíos** | Pasivos, sin salida | `empty_state` con CTA (T-03) | P0 |
| **Consistencia** | Nombres/íconos distintos por lugar | Dict central de módulos (T-05) | P1 |
| **Onboarding** | El dueño nuevo no sabe por dónde empezar | Checklist de puesta en marcha (T-04) | P1 |
| **Configuración** | Submódulos sin explicar su efecto | Intros causa-efecto por submódulo (M-15…M-20) | P0–P1 |
| **Módulos confusos entre sí** | Promociones vs Cupones; login dueño vs PIN | Deslindes M-13a y M-20 | P1 |
| **Multi-dispositivo** | Admin sin responsive (carta/cuentas = 0 breakpoints), tablas que rompen en móvil, targets < 40 px, modales fijos | D-01…D-05 (los mozos usan la PWA en el celu) | P0–P1 |
| **PWA** | Sin offline propio, sin shortcuts, notch iOS | D-06/D-07 | P2 |

**La vara de calidad ya existe dentro del propio sistema:** la sección de Impresoras (modo + pasos numerados + descarga) y la Estación de impresión son el patrón a replicar en todo lo demás.
