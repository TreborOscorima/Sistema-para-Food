"""Pagina de mostrador — pedidos para llevar."""

from __future__ import annotations

import reflex as rx

from app.components.shared import app_shell, cumpleanos_banner
from app.states.food_state import (
    CarritoItem,
    FoodState,
    MostradorEntregadoView,
    MostradorPendienteView,
    ProductoView,
)


# ─── Producto card compacto ─────────────────────────────────────────────────

def _producto_card(producto: ProductoView) -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.text(producto.emoji, font_size="18px", line_height="1", flex_shrink="0"),
            rx.vstack(
                rx.text(
                    producto.nombre,
                    font_size="12px", font_weight="600", color="#F1F5F9",
                    no_of_lines=1,
                ),
                rx.text(
                    producto.precio_texto,
                    font_size="12px", font_weight="700", color="#EA580C",
                ),
                spacing="0", align="start", flex="1", min_width="0",
            ),
            rx.box(
                rx.icon(tag="plus", size=12, color="#FFFFFF"),
                width="22px", height="22px", border_radius="6px",
                background="#EA580C", display="flex",
                align_items="center", justify_content="center",
                flex_shrink="0",
            ),
            spacing="2", align="center", width="100%",
        ),
        on_click=FoodState.agregar_producto_mostrador(producto.id),
        background="#1E293B",
        border="1.5px solid #334155",
        border_radius="8px",
        padding="8px 10px",
        cursor="pointer",
        _hover={"border": "1.5px solid #EA580C"},
        transition="all 0.12s ease",
    )


# ─── Item de carrito ────────────────────────────────────────────────────────

def _carrito_item(item: CarritoItem) -> rx.Component:
    return rx.hstack(
        rx.text(
            item.nombre,
            font_size="12px", font_weight="600", color="#F1F5F9",
            flex="1", min_width="0", no_of_lines=1,
        ),
        rx.hstack(
            rx.button(
                "-",
                on_click=FoodState.restar_producto_mostrador(item.producto_id),
                width="40px", height="40px",
                background="#FEF2F2", color="#B91C1C",
                border="1px solid #FECACA", border_radius="8px",
                font_size="18px", cursor="pointer", padding="0",
                _hover={"opacity": "0.8"},
            ),
            rx.text(
                item.cantidad.to_string(),
                font_size="14px", font_weight="700", color="#EA580C",
                min_width="24px", text_align="center",
            ),
            rx.button(
                "+",
                on_click=FoodState.agregar_producto_mostrador(item.producto_id),
                width="40px", height="40px",
                background="#F0FDF4", color="#15803D",
                border="1px solid #BBF7D0", border_radius="8px",
                font_size="18px", cursor="pointer", padding="0",
                _hover={"opacity": "0.8"},
            ),
            spacing="2", align="center",
        ),
        rx.text(
            item.subtotal_texto,
            font_size="13px", font_weight="600", color="#94A3B8",
            min_width="56px", text_align="right",
        ),
        width="100%", align="center", spacing="2",
        padding="6px 0",
        border_bottom="1px solid #1E293B",
    )


# ─── Card de pedido pendiente ───────────────────────────────────────────────

def _pendiente_card(pedido: MostradorPendienteView) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.text(pedido.cliente_nombre, font_size="13px", font_weight="700", color="#FFFFFF"),
                rx.spacer(),
                rx.cond(
                    pedido.en_cocina,
                    rx.badge("En cocina", background="#0F172A", color="#FCD34D",
                             border="1px solid #FCD34D", border_radius="20px",
                             font_size="10px", font_weight="700", padding_x="8px"),
                    rx.badge("Listo", background="#052E16", color="#4ADE80",
                             border="1px solid #4ADE80", border_radius="20px",
                             font_size="10px", font_weight="700", padding_x="8px"),
                ),
                width="100%", align="center",
            ),
            rx.text(pedido.items_resumen, font_size="11px", color="#94A3B8", no_of_lines=2),
            rx.hstack(
                rx.text(pedido.total_texto, font_size="13px", font_weight="800", color="#EA580C"),
                rx.spacer(),
                rx.text(pedido.hora_texto, font_size="11px", color="#64748B"),
                width="100%", align="center",
            ),
            spacing="1", width="100%",
        ),
        background="#0F172A",
        border="1px solid #334155",
        border_radius="10px",
        padding="12px",
    )


# ─── Card de pedido entregado ───────────────────────────────────────────────

def _entregado_card(pedido: MostradorEntregadoView) -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.vstack(
                rx.text(pedido.cliente_nombre, font_size="13px", font_weight="600", color="#F1F5F9"),
                rx.text(pedido.items_resumen, font_size="11px", color="#64748B"),
                spacing="0", align="start",
            ),
            rx.spacer(),
            rx.vstack(
                rx.text(pedido.total_texto, font_size="13px", font_weight="700", color="#4ADE80"),
                rx.text(pedido.hora_texto, font_size="11px", color="#64748B"),
                align="end", spacing="0",
            ),
            width="100%", align="center",
        ),
        background="#1E293B",
        border="1px solid #334155",
        border_radius="8px",
        padding="10px 14px",
    )


# ─── Layout principal ───────────────────────────────────────────────────────

def _mostrador_content() -> rx.Component:
    return rx.vstack(
        cumpleanos_banner(),
        # Header
        rx.vstack(
            rx.text("Mostrador", font_size="22px", font_weight="800", color="#FFFFFF"),
            rx.text("Pedidos para llevar", font_size="13px", color="#94A3B8"),
            spacing="0",
        ),
        # Contenido: 2 columnas principales
        rx.flex(
            # ─── Columna izquierda: catálogo de productos ───
            rx.vstack(
                # Nombre del cliente
                rx.hstack(
                    rx.icon(tag="user", size=14, color="#64748B", flex_shrink="0"),
                    rx.input(
                        value=FoodState.mostrador_cliente_nombre,
                        on_change=FoodState.set_mostrador_cliente_nombre,
                        placeholder="Nombre del cliente (opcional)",
                        background="transparent",
                        border="none",
                        color="#F1F5F9",
                        font_size="13px",
                        outline="none",
                        width="100%",
                        _focus={"outline": "none", "box_shadow": "none"},
                        _placeholder={"color": "#64748B"},
                    ),
                    spacing="2", align="center", width="100%",
                    background="#0F172A",
                    border="1px solid #334155",
                    border_radius="8px",
                    padding="6px 10px",
                ),
                # Buscador
                rx.box(
                    rx.hstack(
                        rx.icon(tag="search", size=14, color="#64748B", flex_shrink="0"),
                        rx.input(
                            value=FoodState.busqueda_producto_mostrador,
                            on_change=FoodState.set_busqueda_producto_mostrador,
                            placeholder="Buscar producto...",
                            background="transparent",
                            border="none",
                            color="#F1F5F9",
                            font_size="13px",
                            outline="none",
                            width="100%",
                            _focus={"outline": "none", "box_shadow": "none"},
                            _placeholder={"color": "#64748B"},
                        ),
                        rx.cond(
                            FoodState.busqueda_producto_mostrador != "",
                            rx.box(
                                rx.icon(tag="x", size=12, color="#94A3B8"),
                                cursor="pointer",
                                on_click=FoodState.set_busqueda_producto_mostrador(""),
                                _hover={"opacity": "0.7"},
                            ),
                            rx.fragment(),
                        ),
                        spacing="2", align="center", width="100%",
                    ),
                    background="#0F172A",
                    border="1px solid #334155",
                    border_radius="8px",
                    padding="6px 10px",
                    width="100%",
                ),
                # Filtros de categoría
                rx.hstack(
                    rx.button(
                        "Todos",
                        on_click=FoodState.seleccionar_mostrador_categoria(0),
                        background=rx.cond(FoodState.mostrador_categoria_activa_id == 0, "#EA580C", "transparent"),
                        color=rx.cond(FoodState.mostrador_categoria_activa_id == 0, "#FFFFFF", "#94A3B8"),
                        border=rx.cond(FoodState.mostrador_categoria_activa_id == 0, "1px solid #EA580C", "1px solid #334155"),
                        border_radius="6px",
                        font_size="11px",
                        font_weight=rx.cond(FoodState.mostrador_categoria_activa_id == 0, "700", "500"),
                        cursor="pointer",
                        padding_x="8px", padding_y="4px", height="auto",
                        _hover={"opacity": "0.85"},
                    ),
                    rx.foreach(
                        FoodState.categorias_activas,
                        lambda cat: rx.button(
                            cat.emoji + " " + cat.nombre,
                            on_click=FoodState.seleccionar_mostrador_categoria(cat.id),
                            background=rx.cond(FoodState.mostrador_categoria_activa_id == cat.id, "#EA580C", "transparent"),
                            color=rx.cond(FoodState.mostrador_categoria_activa_id == cat.id, "#FFFFFF", "#94A3B8"),
                            border=rx.cond(FoodState.mostrador_categoria_activa_id == cat.id, "1px solid #EA580C", "1px solid #334155"),
                            border_radius="6px",
                            font_size="11px",
                            cursor="pointer",
                            padding_x="8px", padding_y="4px", height="auto",
                            _hover={"opacity": "0.85"},
                        ),
                    ),
                    flex_wrap="wrap",
                    gap="4px",
                    width="100%",
                ),
                # Grid de productos
                rx.box(
                    rx.cond(
                        FoodState.mostrador_productos_filtrados.length() == 0,
                        rx.center(
                            rx.vstack(
                                rx.icon(tag="search_x", size=28, color="#475569"),
                                rx.text("Sin resultados", font_size="13px", color="#64748B"),
                                spacing="2", align="center",
                            ),
                            padding_y="24px",
                        ),
                        rx.grid(
                            rx.foreach(FoodState.mostrador_productos_filtrados, _producto_card),
                            columns=rx.breakpoints(initial="1", sm="2"),
                            gap="6px",
                            width="100%",
                        ),
                    ),
                    overflow_y="auto",
                    flex="1",
                    width="100%",
                ),
                spacing="2",
                flex="3",
                min_width="0",
                height="calc(100vh - 140px)",
            ),
            # ─── Columna derecha: carrito + pendientes + cobrados ───
            rx.vstack(
                # Panel de carrito
                rx.vstack(
                    rx.hstack(
                        rx.icon(tag="shopping_cart", size=14, color="#EA580C"),
                        rx.text("Pedido para llevar", font_size="13px", font_weight="700", color="#EA580C"),
                        rx.spacer(),
                        rx.hstack(
                            rx.cond(
                                FoodState.mostrador_cupon_id_aplicado > 0,
                                rx.text(
                                    FoodState.total_mostrador_texto,
                                    font_size="11px", color="#64748B",
                                    text_decoration="line-through",
                                ),
                                rx.fragment(),
                            ),
                            rx.text(
                                FoodState.total_mostrador_neto_texto,
                                font_size="14px", font_weight="700", color="#FFFFFF",
                            ),
                            spacing="2", align="center",
                        ),
                        width="100%", align="center",
                    ),
                    # Items del carrito
                    rx.box(
                        rx.cond(
                            FoodState.mostrador_carrito.length() == 0,
                            rx.center(
                                rx.vstack(
                                    rx.icon(tag="clipboard_list", size=24, color="#334155"),
                                    rx.text("Agrega productos", font_size="11px", color="#64748B"),
                                    spacing="1", align="center",
                                ),
                                padding_y="20px",
                            ),
                            rx.vstack(
                                rx.foreach(FoodState.mostrador_carrito, _carrito_item),
                                width="100%",
                                spacing="0",
                            ),
                        ),
                        overflow_y="auto",
                        max_height="22vh",
                        width="100%",
                        flex="1",
                    ),
                    # Botones de acción
                    rx.hstack(
                        rx.button(
                            "Limpiar",
                            on_click=FoodState.limpiar_carrito_mostrador,
                            background="transparent",
                            color="#64748B",
                            border="1px solid #334155",
                            border_radius="8px",
                            font_size="12px",
                            cursor="pointer",
                            padding_x="14px",
                            _hover={"border_color": "#DC2626", "color": "#FCA5A5"},
                        ),
                        rx.button(
                            rx.hstack(
                                rx.icon(tag="send", size=13),
                                rx.text("Enviar a Cocina"),
                                spacing="2", align="center",
                            ),
                            on_click=FoodState.enviar_pedido_mostrador,
                            background="#EA580C",
                            color="#FFFFFF",
                            border_radius="8px",
                            font_size="13px",
                            font_weight="700",
                            cursor="pointer",
                            _hover={"background": "#C2410C"},
                            flex="1",
                            is_disabled=FoodState.mostrador_carrito.length() == 0,
                        ),
                        spacing="2",
                        width="100%",
                    ),
                    spacing="2",
                    width="100%",
                    background="#1E293B",
                    border="1px solid #334155",
                    border_radius="10px",
                    padding="12px",
                ),
                # Separador
                rx.divider(border_color="#334155"),
                # Pendientes de cobro
                rx.vstack(
                    rx.hstack(
                        rx.icon(tag="clock", size=13, color="#FCD34D"),
                        rx.text("Pendientes de cobro", font_size="13px", font_weight="700", color="#FCD34D"),
                        spacing="2", align="center",
                    ),
                    rx.cond(
                        FoodState.pedidos_mostrador_pendientes.length() == 0,
                        rx.center(
                            rx.text("Sin pedidos en espera", font_size="12px", color="#64748B"),
                            padding_y="10px",
                        ),
                        rx.vstack(
                            rx.foreach(FoodState.pedidos_mostrador_pendientes, _pendiente_card),
                            spacing="2",
                            width="100%",
                        ),
                    ),
                    spacing="2", width="100%",
                ),
                # Cobrados hoy
                rx.vstack(
                    rx.text("Cobrados hoy", font_size="13px", font_weight="700", color="#94A3B8"),
                    rx.cond(
                        FoodState.pedidos_mostrador_entregados.length() == 0,
                        rx.center(
                            rx.text("Sin historial", font_size="12px", color="#64748B"),
                            padding_y="10px",
                        ),
                        rx.vstack(
                            rx.foreach(FoodState.pedidos_mostrador_entregados, _entregado_card),
                            spacing="2",
                            width="100%",
                        ),
                    ),
                    spacing="2", width="100%",
                ),
                spacing="3",
                flex="2",
                min_width="0",
                height="calc(100vh - 140px)",
                overflow_y="auto",
            ),
            direction=rx.breakpoints(initial="column", md="row"),
            gap="16px",
            width="100%",
            flex="1",
        ),
        spacing="4",
        width="100%",
    )


@rx.page(
    route="/mostrador",
    on_load=[FoodState.on_load_mostrador, FoodState.start_mostrador_polling,
             FoodState.cargar_clientes],
    title="TUWAYKIFOOD | Mostrador",
)
def mostrador_page() -> rx.Component:
    return app_shell(_mostrador_content(), page_key="mostrador", dark=True)
