# TUWAYKIFOOD — Sesión de Pruebas y Desarrollo (2026-07-03)

## Contexto General

Se está realizando testing punto a punto del sistema TUWAYKIFOOD localmente via Docker.
- **Repo**: `C:\Users\Trebor Oscorima\Sistema-para-Food`
- **Docker**: `docker compose -f docker-compose.yml -f docker-compose.local.yml up -d --build tuwayki_food`
- **Container**: `tuwayki_food` en port `3003`, `food_mysql` en port `33307`
- **Framework**: Reflex 0.9.4, Python 3.13, MySQL 8
- **Login**: TUWAYKIFOOD (sin logo — la card "T") → "Ingresar como Administrador →" → `TreborOD523@gmail.com` / `TreborOD(523)`
- **Push dual**: siempre `git push origin HEAD:main HEAD:docker-deploy-prod`

## Cambios Realizados en esta Sesión

### 1. Mozos — Modal de productos al hacer clic en mesa (COMPLETADO + VERIFICADO)

**Archivos modificados:**
- `app/states/food_state.py` — nuevas variables, handlers, computed var
- `app/pages/mozos.py` — nuevo modal, componentes, eliminación de tabs

**Lo que se hizo:**

#### Round 1: Modal con productos
- Al hacer clic en cualquier mesa (libre u ocupada) se abre inmediatamente un **modal con 2 columnas**:
  - **Izquierda**: buscador de productos + filtros por categoría + grilla de productos compactos
  - **Derecha**: panel de carrito "Pedido" con total, items con +/-, y botón "Enviar a Cocina"
- Se eliminaron los botones/tabs "Agregar" e "Historial" de la vista de Mozos

#### Round 2: Carrito con notas inline
- Cada item del carrito tiene un enlace "+ nota" que abre un input inline
- Se puede escribir una nota (ej: "sin sal, extra aji") y guardarla con el botón check
- La nota se muestra como "📝 sin sal, extra aji" con opción "editar"
- Las notas se persisten en BD (`DetallePedido.notas`)

#### Round 3: Historial de pedidos enviados en el modal
- Para **mesas ocupadas** (con pedidos ya enviados a cocina), el modal muestra una sección extra **"Enviado a cocina"** con fondo azul oscuro que lista:
  - Cada item con cantidad, nombre, nota (si tiene) y badge de estado (Pendiente, En preparación, Listo)
- Debajo aparece la sección **"Nuevo pedido"** para agregar más items (que se enviarían como un nuevo pedido)
- Esto permite al mozo ver de un vistazo qué se pidió y en qué estado está

**Variables de estado agregadas (`food_state.py` ~línea 1019):**
```python
modal_agregar_abierto: bool = False
busqueda_producto_modal: str = ""
nota_producto_activo_id: int = 0
nota_input_temporal: str = ""
```

**Handlers agregados:**
- `set_modal_agregar_abierto(value)` — abre/cierra modal, limpia búsqueda al cerrar
- `cerrar_modal_agregar()` — cierra modal
- `set_busqueda_producto_modal(value)` — actualiza búsqueda
- `abrir_nota_item(producto_id)` — abre editor de nota inline
- `set_nota_input_temporal(value)` — cap 120 chars
- `guardar_nota_carrito_item(producto_id)` — persiste nota en BD

**Computed var agregado:**
- `productos_modal_filtrados` — filtra productos por categoría y texto de búsqueda

**`seleccionar_mesa` modificado** — ahora abre `modal_agregar_abierto = True` automáticamente

**Componentes nuevos en `mozos.py`:**
- `_producto_card_compact(producto)` — card compacto para la grilla del modal
- `_modal_carrito_item(item)` — item de carrito con nota inline
- `_modal_historial_item(item)` — item del historial con badge de estado
- `_modal_agregar_productos()` — el modal completo con 2 columnas

**Verificación:** Todo probado en vivo en el navegador. Búsqueda funciona, notas se guardan, historial muestra estados.

---

### 2. Mostrador — Rediseño visual completo (COMPLETADO + VERIFICADO)

**Archivos modificados:**
- `app/states/food_state.py` — nueva variable `busqueda_producto_mostrador`, setter, filtro actualizado
- `app/pages/mostrador.py` — reescritura completa del layout

**Lo que se hizo:**
- **Layout de 2 columnas** bien separadas (antes todo estaba apilado sin separación):
  - **Izquierda (flex=3)**: Campo de nombre del cliente (con ícono user) + buscador de productos (con botón X para limpiar) + filtros de categoría + grilla de productos compactos
  - **Derecha (flex=2)**: Panel de carrito "Pedido para llevar" con borde propio + Pendientes de cobro + Cobrados hoy
- **Buscador** integrado (no existía antes) — filtra productos por nombre en tiempo real
- **Cards de productos** rediseñados para ser consistentes con el estilo de Mozos
- **Carrito** con panel visual delimitado, botones +/- estilizados, total prominente
- **Responsive**: `direction=rx.breakpoints(initial="column", md="row")`

**Variables de estado agregadas:**
```python
busqueda_producto_mostrador: str = ""
```

**Handler agregado:**
- `set_busqueda_producto_mostrador(value)`

**Computed var actualizado:**
- `mostrador_productos_filtrados` — ahora también filtra por `busqueda_producto_mostrador`

**Verificación:** Probado en vivo. Se crearon 3 pedidos para llevar:
1. **Juan Perez** — 2x Arroz con Pollo + 1x Chicha Morada + 1x Lomo Saltado = S/ 73.00
2. **Maria Lopez** — 1x Arroz con Pollo + 2x Chicha Morada = S/ 36.00
3. **Carlos Ramirez** — 3x Lomo Saltado + 1x Arroz con Pollo = S/ 95.00

Los 3 aparecen en "Pendientes de cobro" con badge "En cocina".

---

### 3. Otros cambios previos en esta sesión (ya commiteados o pendientes)

- **Migración 0027**: `nombre_impuesto` en `food_config_impresora` (columna String(20), default "IGV")
- **Receipt service**: Soporte para `nombre_impuesto` configurable en el ticket de caja
- **Configuración**: Campo para editar nombre del impuesto (IGV/IVA/VAT/etc.)
- **Toast duplicado fix**: Corregido toast duplicado en algún flujo anterior

---

## Datos de Prueba Actuales en la BD

### Mesas (Salón):
| Mesa | Estado | Detalle |
|------|--------|---------|
| Salón Principal | OCUPADA | S/ 53.00, pedidos previos de sesiones anteriores |
| Terraza | OCUPADA | S/ 78.00, pedidos previos |
| VIP | OCUPADA | S/ 28.00 — 1x Arroz con Pollo (nota: "sin sal, extra aji") + 1x Chicha Morada, enviado a cocina |
| Barra | LIBRE | — |
| Patio Exterior | LIBRE | — |

### Productos en Carta:
| Producto | Categoría | Precio |
|----------|-----------|--------|
| Arroz con Pollo | Platos Principales | S/ 20.00 |
| Chicha Morada | Bebidas | S/ 8.00 |
| Lomo Saltado | Platos Principales | S/ 25.00 |

### Pedidos Mostrador (Para llevar):
3 pedidos pendientes de cobro, todos "En cocina".

---

## Módulos YA Probados en esta Sesión

1. **Mozos** — Modal de productos, carrito con notas, historial de pedidos, búsqueda
2. **Cocina KDS** — Verificado que pedidos llegan correctamente con notas y estados
3. **Mostrador** — Rediseño completo, flujo de crear pedidos para llevar, pendientes de cobro

## Módulos PENDIENTES de Probar

4. **Caja** — Cobro y tickets. Hay 3 pedidos de mostrador + pedidos de mesas listos para cobrar. Probar:
   - Cobro de pedidos de mostrador (pendientes de cobro)
   - Cobro de pedidos de mesas
   - Métodos de pago (efectivo, tarjeta, etc.)
   - Impresión de tickets/comprobantes
   - Descuentos y cupones
   - Turnos de caja (apertura/cierre)

5. **Carta** — Gestión de categorías y productos. Ya se crearon categorías y productos en la sesión anterior. Probar:
   - Editar productos existentes
   - Cambiar disponibilidad
   - Precios y emojis
   - Ordenamiento

6. **Clientes** — Fidelización y alertas
   - Registro de clientes
   - Puntos de fidelidad
   - Alertas de cumpleaños

7. **Cuentas** — Fiado y créditos
   - Crear cuentas fiadas
   - Registrar pagos

8. **Promociones** — Descuentos y cupones
   - Crear cupones
   - Aplicar descuentos

9. **Inventario** — Stock y alertas
   - Gestión de stock
   - Alertas de bajo stock

10. **Usuarios** — Personal y PINs
    - Crear/editar usuarios (mozos, cocineros, cajeros)
    - PINs de acceso

11. **Configuración** — Impresoras y local
    - Nombre del negocio
    - Impuesto (IGV/IVA) — ya agregado campo `nombre_impuesto`
    - Logo

12. **Reportes** — Ventas del día
    - Dashboard de ventas
    - Reportes diarios

---

## Instrucciones para Continuar

1. **Levantar Docker**: 
   ```bash
   cd "C:\Users\Trebor Oscorima\Sistema-para-Food"
   docker compose -f docker-compose.yml -f docker-compose.local.yml up -d --build tuwayki_food
   ```

2. **Login**: Navegar a `http://localhost:3003/login` → card "T" (TUWAYKIFOOD sin logo) → "Ingresar como Administrador →" → `TreborOD523@gmail.com` / `TreborOD(523)`

3. **Siguiente módulo sugerido**: **Caja** — hay pedidos pendientes de cobro tanto de mesas como del mostrador listos para probar el flujo completo de cobro.

4. **Al hacer cambios de código**, rebuild con:
   ```bash
   docker compose -f docker-compose.yml -f docker-compose.local.yml up -d --build tuwayki_food
   ```

5. **Push siempre dual**:
   ```bash
   git push origin HEAD:main HEAD:docker-deploy-prod
   ```

6. **Archivos principales del sistema**:
   - Estado central: `app/states/food_state.py` (~6400 líneas)
   - Páginas: `app/pages/mozos.py`, `app/pages/mostrador.py`, `app/pages/caja.py`, `app/pages/cocina.py`, etc.
   - Componentes compartidos: `app/components/shared.py`
   - Modelos: `app/models/food_models.py`
   - Servicios: `app/services/receipt_service.py`

7. **Memoria del usuario**: El usuario es el Principal Software Architect, experto en Python/Reflex/SaaS multi-tenant. Respuestas deben ser en rol técnico senior, en español latinoamericano neutro (sin voseo argentino). Todo texto visible de la UI en español.
