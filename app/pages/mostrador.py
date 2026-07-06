"""Pagina de mostrador — pedidos para llevar."""

from __future__ import annotations

import reflex as rx

from app.components.shared import app_shell, cumpleanos_banner, loading_placeholder
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
    editing_nota = FoodState.nota_producto_activo_id == item.producto_id
    return rx.vstack(
        rx.hstack(
            rx.vstack(
                rx.text(
                    item.nombre,
                    font_size="12px", font_weight="600", color="#F1F5F9",
                    no_of_lines=1,
                ),
                rx.cond(
                    item.modificadores_texto != "",
                    rx.text(
                        "⚙ " + item.modificadores_texto,
                        font_size="10px", color="#A78BFA",
                        no_of_lines=1,
                    ),
                    rx.fragment(),
                ),
                spacing="0", flex="1", min_width="0",
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
        ),
        rx.cond(
            editing_nota,
            rx.hstack(
                rx.input(
                    value=FoodState.nota_input_temporal,
                    on_change=FoodState.set_nota_input_temporal,
                    placeholder="Ej: sin azúcar, extra picante...",
                    background="#0F172A", border="1px solid #475569",
                    color="#F1F5F9", border_radius="6px",
                    font_size="11px", padding_x="8px", padding_y="4px",
                    width="100%", height="28px",
                    _focus={"border": "1px solid #EA580C"},
                    _placeholder={"color": "#64748B"},
                ),
                rx.button(
                    rx.icon(tag="check", size=11),
                    on_click=FoodState.guardar_nota_item_mostrador(item.producto_id),
                    width="28px", height="28px",
                    background="#1E293B", color="#22C55E",
                    border="1px solid #334155", border_radius="6px",
                    cursor="pointer", padding="0",
                    _hover={"opacity": "0.8"},
                ),
                spacing="1", width="100%",
            ),
            rx.hstack(
                rx.cond(
                    item.nota != "",
                    rx.text(
                        "📝 " + item.nota,
                        font_size="10px", color="#94A3B8",
                        no_of_lines=1, flex="1", min_width="0",
                    ),
                    rx.fragment(),
                ),
                rx.text(
                    rx.cond(item.nota != "", "editar", "+ nota"),
                    font_size="10px", color="#64748B", cursor="pointer",
                    _hover={"color": "#EA580C"},
                    on_click=FoodState.abrir_nota_item_mostrador(item.producto_id),
                ),
                width="100%", align="center", spacing="1",
            ),
        ),
        spacing="1", width="100%",
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
            rx.text("#" + pedido.pedido_id.to_string(),
                    font_size="20px", font_weight="900", color="#EA580C",
                    letter_spacing="-0.5px"),
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
        _modal_seleccion_mods_m(),
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


def _mod_item_flat_m(item: dict) -> rx.Component:
    return rx.cond(
        item["type"] == "header",
        rx.hstack(
            rx.text(
                item["nombre"].to(str),
                font_size="13px", font_weight="700", color="#F1F5F9",
            ),
            rx.cond(
                item["min"].to(int) > 0,
                rx.badge(
                    "Obligatorio",
                    background="#7F1D1D", color="#FCA5A5",
                    font_size="9px", border_radius="4px",
                    padding="1px 5px",
                ),
                rx.fragment(),
            ),
            rx.text(
                rx.cond(
                    item["max"].to(int) > 1,
                    "(máx " + item["max"].to(int).to_string() + ")",
                    "",
                ),
                font_size="10px", color="#64748B",
            ),
            spacing="2", align="center", width="100%",
            padding_top="8px",
        ),
        rx.box(
            rx.hstack(
                rx.box(
                    width="16px", height="16px", border_radius="4px",
                    background=rx.cond(item["selected"].to(bool), "#EA580C", "transparent"),
                    border=rx.cond(item["selected"].to(bool), "2px solid #EA580C", "2px solid #475569"),
                    flex_shrink="0",
                    display="flex", align_items="center", justify_content="center",
                ),
                rx.text(
                    item["nombre"].to(str),
                    font_size="13px", color="#F1F5F9", font_weight="500",
                    flex="1",
                ),
                rx.cond(
                    item["precio_extra"].to(float) > 0,
                    rx.text(
                        "+S/" + item["precio_extra"].to(float).to_string(),
                        font_size="12px", color="#EA580C", font_weight="600",
                    ),
                    rx.fragment(),
                ),
                spacing="2", align="center", width="100%",
            ),
            on_click=FoodState.toggle_mod_opcion(
                item["grupo_id"].to(str) + "_" + item["opcion_id"].to(int).to_string()
            ),
            cursor="pointer",
            padding="8px 10px",
            border_radius="8px",
            background=rx.cond(item["selected"].to(bool), "#1E293B", "transparent"),
            border=rx.cond(item["selected"].to(bool), "1px solid #EA580C", "1px solid #334155"),
            _hover={"background": "#1E293B"},
            transition="all 0.12s ease",
        ),
    )


def _modal_seleccion_mods_m() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.hstack(
                    rx.icon(tag="settings_2", size=16, color="#A78BFA"),
                    rx.text(
                        FoodState.mod_seleccion_producto_nombre,
                        font_size="15px", font_weight="700", color="#FFFFFF",
                    ),
                    rx.spacer(),
                    rx.dialog.close(
                        rx.box(
                            rx.icon(tag="x", size=16, color="#94A3B8"),
                            cursor="pointer", padding="4px",
                            border_radius="6px",
                            _hover={"background": "#334155"},
                        ),
                    ),
                    width="100%", align="center",
                ),
                rx.text(
                    "Elegí las opciones para este producto",
                    font_size="12px", color="#94A3B8",
                ),
                rx.box(
                    rx.vstack(
                        rx.foreach(
                            FoodState.mod_seleccion_items_flat,
                            _mod_item_flat_m,
                        ),
                        spacing="1", width="100%",
                    ),
                    max_height="50vh",
                    overflow_y="auto",
                    width="100%",
                    padding_y="4px",
                ),
                rx.cond(
                    FoodState.mod_seleccion_extra_total > 0,
                    rx.text(
                        "Extra: +S/" + FoodState.mod_seleccion_extra_total.to_string(),
                        font_size="12px", font_weight="600", color="#EA580C",
                    ),
                    rx.fragment(),
                ),
                rx.button(
                    rx.hstack(
                        rx.icon(tag="plus", size=14),
                        rx.text("Agregar al pedido"),
                        spacing="2", align="center",
                    ),
                    on_click=FoodState.confirmar_mod_seleccion,
                    background="#EA580C", color="#FFFFFF",
                    border_radius="8px", font_size="13px",
                    font_weight="700", width="100%",
                    cursor="pointer",
                    _hover={"background": "#C2410C"},
                    is_disabled=~FoodState.mod_seleccion_valido,
                ),
                spacing="3", width="100%",
            ),
            background="#0F172A",
            border="1px solid #334155",
            border_radius="14px",
            padding="20px",
            max_width="420px",
            width="90vw",
        ),
        open=FoodState.mod_seleccion_modal,
        on_open_change=FoodState.set_mod_seleccion_modal,
    )


@rx.page(
    route="/mostrador",
    on_load=[FoodState.on_load_mostrador, FoodState.start_mostrador_polling,
             FoodState.cargar_clientes],
    title="TUWAYKIFOOD | Mostrador",
)
def mostrador_page() -> rx.Component:
    return app_shell(
        rx.cond(FoodState.pagina_cargada, _mostrador_content(), loading_placeholder(dark=True)),
        page_key="mostrador", dark=True,
    )
