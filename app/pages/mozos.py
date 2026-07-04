"""Pagina de mozos — mapa de salon + menu + carrito."""

from __future__ import annotations

import reflex as rx

from app.components.shared import anulacion_modal, app_shell, cumpleanos_banner, section_card, surface_card
from app.states.food_state import CarritoItem, FoodState, HistorialItem, MesaView, ProductoView


# ─── Tarjeta de mesa ─────────────────────────────────────────────────────────

def _mesa_card(mesa: MesaView) -> rx.Component:
    selected = FoodState.mesa_seleccionada_id == mesa.id
    return rx.box(
        rx.vstack(
            # Estado badge superior
            rx.hstack(
                rx.badge(
                    mesa.estado_label,
                    background=mesa.badge_bg,
                    color=mesa.badge_text,
                    border_radius="5px",
                    font_size="9px",
                    font_weight="700",
                    padding="2px 7px",
                    letter_spacing="0.04em",
                    text_transform="uppercase",
                ),
                rx.spacer(),
                # Indicador de items listos
                rx.cond(
                    mesa.tiene_items_listos,
                    rx.box(
                        rx.icon(tag="bell", size=11, color="#D97706"),
                        width="20px",
                        height="20px",
                        border_radius="50%",
                        background="#FEF3C7",
                        border="1.5px solid #FDE68A",
                        display="flex",
                        align_items="center",
                        justify_content="center",
                    ),
                    rx.fragment(),
                ),
                width="100%",
                align="center",
            ),
            # Nombre grande
            rx.text(
                mesa.nombre,
                font_size=rx.breakpoints(initial="15px", md="16px"),
                font_weight="800",
                color="#FFFFFF",
                line_height="1",
            ),
            # Total y tiempo si tiene consumo
            rx.cond(
                mesa.total_abierto > 0,
                rx.hstack(
                    rx.text(
                        mesa.total_abierto_texto,
                        font_size="13px",
                        font_weight="700",
                        color=rx.cond(selected, "#FEF3C7", "#94A3B8"),
                    ),
                    rx.text(
                        "⏱ " + mesa.tiempo_abierto_texto,
                        font_size="11px",
                        color=rx.cond(selected, "#FED7AA", "#64748B"),
                    ),
                    spacing="2", align="center", wrap="wrap",
                ),
                rx.fragment(),
            ),
            # Items listos texto
            rx.cond(
                mesa.tiene_items_listos,
                rx.text(
                    mesa.items_listos_count.to_string() + " listos ↑",
                    font_size="10px",
                    color="#FCD34D",
                    font_weight="700",
                ),
                rx.fragment(),
            ),
            spacing="2",
            align="start",
            width="100%",
        ),
        background=rx.cond(selected, "#EA580C", mesa.card_bg),
        border=rx.cond(selected, "2px solid #EA580C", mesa.card_border),
        border_radius="14px",
        padding=rx.breakpoints(initial="12px", md="14px 16px"),
        cursor="pointer",
        on_click=FoodState.seleccionar_mesa(mesa.id),
        _hover={
            "border": "2px solid rgba(234,88,12,0.6)",
            "transform": "translateY(-2px)",
            "box_shadow": "0 6px 20px rgba(0,0,0,0.3)",
        },
        transition="all 0.15s ease",
        min_width=rx.breakpoints(initial="110px", md="130px", lg="150px"),
        box_shadow=rx.cond(
            selected,
            "0 0 0 3px rgba(234,88,12,0.25), 0 4px 16px rgba(0,0,0,0.3)",
            "0 1px 4px rgba(0,0,0,0.2)",
        ),
        position="relative",
    )


# ─── Salon (mapa de mesas) ────────────────────────────────────────────────────

def _salon_content() -> rx.Component:
    return rx.vstack(
        rx.cond(
            FoodState.mesas_con_alerta_entrega > 0,
            rx.box(
                rx.text(
                    FoodState.mesas_con_alerta_entrega.to_string() + " mesa(s) con items listos para entregar",
                    font_size="13px",
                    font_weight="600",
                    color="#B45309",
                ),
                background="#FFFBEB",
                border="1px solid #FDE68A",
                border_radius="8px",
                padding="8px 14px",
                width="100%",
            ),
            rx.fragment(),
        ),
        rx.cond(
            FoodState.mesas.length() == 0,
            rx.center(
                rx.text("No hay mesas configuradas.", font_size="14px", color="#94A3B8"),
                padding_y="40px",
            ),
            rx.flex(
                rx.foreach(FoodState.mesas, _mesa_card),
                flex_wrap="wrap",
                gap="12px",
                width="100%",
            ),
        ),
        spacing="3",
        width="100%",
    )


# ─── Modal de agregar productos a mesa ────────────────────────────────────────

def _producto_card_compact(producto: ProductoView) -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.text(producto.emoji, font_size="18px", line_height="1", flex_shrink="0"),
            rx.vstack(
                rx.text(
                    producto.nombre,
                    font_size="12px",
                    font_weight="600",
                    color="#F1F5F9",
                    no_of_lines=1,
                ),
                rx.text(
                    producto.precio_texto,
                    font_size="12px",
                    font_weight="700",
                    color="#EA580C",
                ),
                spacing="0",
                align="start",
                flex="1",
                min_width="0",
            ),
            rx.box(
                rx.icon(tag="plus", size=16, color="#FFFFFF"),
                width="36px",
                height="36px",
                border_radius="8px",
                background="#EA580C",
                display="flex",
                align_items="center",
                justify_content="center",
                flex_shrink="0",
            ),
            spacing="2",
            align="center",
            width="100%",
        ),
        on_click=FoodState.agregar_producto(producto.id),
        background="#1E293B",
        border="1.5px solid #334155",
        border_radius="8px",
        padding="8px 10px",
        cursor="pointer",
        _hover={"border": "1.5px solid #EA580C", "background": "#1E293B"},
        transition="all 0.12s ease",
    )


def _modal_carrito_item(item: CarritoItem) -> rx.Component:
    editing_nota = FoodState.nota_producto_activo_id == item.producto_id
    return rx.vstack(
        rx.hstack(
            rx.text(
                item.nombre,
                font_size="12px",
                font_weight="600",
                color="#F1F5F9",
                flex="1",
                min_width="0",
                no_of_lines=1,
            ),
            rx.hstack(
                rx.button(
                    "-",
                    on_click=FoodState.restar_producto(item.producto_id),
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
                    on_click=FoodState.agregar_producto(item.producto_id),
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
        # Nota inline
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
                    on_click=FoodState.guardar_nota_carrito_item(item.producto_id),
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
                    on_click=FoodState.abrir_nota_item(item.producto_id),
                ),
                width="100%", align="center", spacing="1",
            ),
        ),
        spacing="1", width="100%",
        padding="6px 0",
        border_bottom="1px solid #1E293B",
    )


def _modal_historial_item(item: HistorialItem) -> rx.Component:
    return rx.hstack(
        rx.text(
            item.cantidad.to_string() + "x " + item.nombre,
            font_size="11px", font_weight="500", color="#CBD5E1",
            flex="1", min_width="0", no_of_lines=1,
        ),
        rx.cond(
            item.nota != "",
            rx.text(
                "📝 " + item.nota,
                font_size="10px", color="#64748B",
                no_of_lines=1, max_width="100px",
            ),
            rx.fragment(),
        ),
        rx.badge(
            item.estado_label,
            background=item.estado_bg,
            color=item.estado_color,
            font_size="9px",
            padding_x="6px", padding_y="1px",
            border_radius="4px",
        ),
        width="100%", align="center", spacing="2",
        padding="4px 0",
        border_bottom="1px solid #1E293B",
    )


def _modal_agregar_productos() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                # Header
                rx.hstack(
                    rx.text(
                        FoodState.mesa_seleccionada_label,
                        font_size="16px",
                        font_weight="700",
                        color="#FFFFFF",
                    ),
                    rx.spacer(),
                    rx.dialog.close(
                        rx.box(
                            rx.icon(tag="x", size=16, color="#94A3B8"),
                            cursor="pointer",
                            padding="4px",
                            border_radius="6px",
                            _hover={"background": "#334155"},
                        ),
                    ),
                    width="100%",
                    align="center",
                ),
                # Contenido: 2 columnas en desktop, stacked en mobile
                rx.flex(
                    # ─── Columna izquierda: productos ───
                    rx.vstack(
                        # Buscador
                        rx.box(
                            rx.hstack(
                                rx.icon(tag="search", size=14, color="#64748B", flex_shrink="0"),
                                rx.input(
                                    value=FoodState.busqueda_producto_modal,
                                    on_change=FoodState.set_busqueda_producto_modal,
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
                                    FoodState.busqueda_producto_modal != "",
                                    rx.box(
                                        rx.icon(tag="x", size=12, color="#94A3B8"),
                                        cursor="pointer",
                                        on_click=FoodState.set_busqueda_producto_modal(""),
                                        _hover={"opacity": "0.7"},
                                    ),
                                    rx.fragment(),
                                ),
                                spacing="2",
                                align="center",
                                width="100%",
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
                                on_click=FoodState.seleccionar_categoria(0),
                                background=rx.cond(FoodState.categoria_activa_id == 0, "#EA580C", "transparent"),
                                color=rx.cond(FoodState.categoria_activa_id == 0, "#FFFFFF", "#94A3B8"),
                                border=rx.cond(FoodState.categoria_activa_id == 0, "1px solid #EA580C", "1px solid #334155"),
                                border_radius="6px",
                                font_size="11px",
                                font_weight=rx.cond(FoodState.categoria_activa_id == 0, "700", "500"),
                                cursor="pointer",
                                padding_x="8px", padding_y="4px", height="auto",
                                _hover={"opacity": "0.85"},
                            ),
                            rx.foreach(
                                FoodState.categorias_activas,
                                lambda cat: rx.button(
                                    cat.emoji + " " + cat.nombre,
                                    on_click=FoodState.seleccionar_categoria(cat.id),
                                    background=rx.cond(FoodState.categoria_activa_id == cat.id, "#EA580C", "transparent"),
                                    color=rx.cond(FoodState.categoria_activa_id == cat.id, "#FFFFFF", "#94A3B8"),
                                    border=rx.cond(FoodState.categoria_activa_id == cat.id, "1px solid #EA580C", "1px solid #334155"),
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
                                FoodState.productos_modal_filtrados.length() == 0,
                                rx.center(
                                    rx.vstack(
                                        rx.icon(tag="search_x", size=28, color="#475569"),
                                        rx.text("Sin resultados", font_size="13px", color="#64748B"),
                                        spacing="2", align="center",
                                    ),
                                    padding_y="24px",
                                ),
                                rx.grid(
                                    rx.foreach(FoodState.productos_modal_filtrados, _producto_card_compact),
                                    columns=rx.breakpoints(initial="1", sm="2"),
                                    gap="6px",
                                    width="100%",
                                ),
                            ),
                            overflow_y="auto",
                            max_height=rx.breakpoints(initial="28vh", md="45vh"),
                            width="100%",
                        ),
                        spacing="2",
                        flex="3",
                        min_width="0",
                        overflow="hidden",
                    ),
                    # ─── Columna derecha: historial + carrito ───
                    rx.vstack(
                        # Sección: Pedidos enviados a cocina
                        rx.cond(
                            FoodState.historial_pedido.length() > 0,
                            rx.vstack(
                                rx.hstack(
                                    rx.icon(tag="chef_hat", size=14, color="#38BDF8"),
                                    rx.text("Enviado a cocina", font_size="12px", font_weight="700", color="#38BDF8"),
                                    width="100%", align="center",
                                ),
                                rx.box(
                                    rx.vstack(
                                        rx.foreach(FoodState.historial_pedido, _modal_historial_item),
                                        width="100%", spacing="0",
                                    ),
                                    overflow_y="auto",
                                    max_height=rx.breakpoints(initial="12vh", md="20vh"),
                                    width="100%",
                                ),
                                spacing="2", width="100%",
                                background="#0F172A",
                                border="1px solid #1E3A5F",
                                border_radius="8px",
                                padding="8px 10px",
                            ),
                            rx.fragment(),
                        ),
                        # Sección: Nuevo pedido (carrito)
                        rx.hstack(
                            rx.icon(tag="shopping_cart", size=14, color="#EA580C"),
                            rx.text(
                                rx.cond(
                                    FoodState.historial_pedido.length() > 0,
                                    "Nuevo pedido",
                                    "Pedido",
                                ),
                                font_size="13px", font_weight="700", color="#EA580C",
                            ),
                            rx.spacer(),
                            rx.text(
                                FoodState.total_carrito_texto,
                                font_size="13px", font_weight="700", color="#FFFFFF",
                            ),
                            width="100%", align="center",
                        ),
                        rx.box(
                            rx.cond(
                                FoodState.carrito.length() == 0,
                                rx.center(
                                    rx.vstack(
                                        rx.icon(tag="clipboard_list", size=24, color="#334155"),
                                        rx.text("Agrega productos", font_size="11px", color="#64748B"),
                                        spacing="1", align="center",
                                    ),
                                    padding_y="20px",
                                ),
                                rx.vstack(
                                    rx.foreach(FoodState.carrito, _modal_carrito_item),
                                    width="100%",
                                    spacing="0",
                                ),
                            ),
                            overflow_y="auto",
                            max_height=rx.cond(
                                FoodState.historial_pedido.length() > 0,
                                "18vh",
                                "38vh",
                            ),
                            width="100%",
                            flex="1",
                        ),
                        # Botón Enviar a Cocina
                        rx.button(
                            rx.hstack(
                                rx.icon(tag="send", size=13),
                                rx.text("Enviar a Cocina"),
                                spacing="2", align="center",
                            ),
                            on_click=[FoodState.enviar_pedido, FoodState.cerrar_modal_agregar],
                            background="#EA580C",
                            color="#FFFFFF",
                            border_radius="8px",
                            font_size="13px",
                            font_weight="700",
                            width="100%",
                            cursor="pointer",
                            _hover={"background": "#C2410C"},
                            is_disabled=FoodState.cantidad_items_carrito == 0,
                        ),
                        # Botón Liberar mesa (solo si tiene pedido enviado y carrito vacío)
                        rx.cond(
                            (FoodState.historial_pedido.length() > 0) & (FoodState.cantidad_items_carrito == 0),
                            rx.button(
                                rx.hstack(
                                    rx.icon(tag="log_out", size=13),
                                    rx.text("Liberar mesa"),
                                    spacing="2", align="center",
                                ),
                                on_click=FoodState.liberar_mesa_sin_cobro,
                                background="transparent",
                                color="#EF4444",
                                border="1px solid #7F1D1D",
                                border_radius="8px",
                                font_size="12px",
                                font_weight="600",
                                width="100%",
                                cursor="pointer",
                                _hover={"background": "#1C1917", "border": "1px solid #EF4444"},
                            ),
                            rx.fragment(),
                        ),
                        spacing="2",
                        flex="2",
                        flex_shrink="0",
                        min_width="0",
                        background="#1E293B",
                        border="1px solid #334155",
                        border_radius="10px",
                        padding="12px",
                    ),
                    direction=rx.breakpoints(initial="column", md="row"),
                    gap="12px",
                    width="100%",
                    flex="1",
                    min_height="0",
                ),
                spacing="3",
                width="100%",
                height=rx.breakpoints(initial="88vh", md="75vh"),
                max_height=rx.breakpoints(initial="88vh", md="75vh"),
            ),
            background="#0F172A",
            border="1px solid #334155",
            border_radius="16px",
            padding="20px",
            max_width="900px",
            width="95vw",
        ),
        open=FoodState.modal_agregar_abierto,
        on_open_change=FoodState.set_modal_agregar_abierto,
    )


# ─── Layout principal (tabs) ──────────────────────────────────────────────────

def _mozos_content() -> rx.Component:
    return rx.vstack(
        cumpleanos_banner(),
        rx.hstack(
            rx.vstack(
                rx.text(
                    "Salón",
                    font_size="22px",
                    font_weight="800",
                    color="#FFFFFF",
                ),
                rx.text("Mesas y comandas en curso", font_size="13px", color="#94A3B8"),
                spacing="0",
            ),
            width="100%",
            align="center",
            flex_wrap="wrap",
            gap="8px",
        ),
        rx.cond(
            FoodState.mensaje != "",
            rx.box(
                rx.text(FoodState.mensaje, font_size="12px", color="#CBD5E1"),
                background="#1E293B",
                border="1px solid #334155",
                border_radius="6px",
                padding="8px 12px",
                width="100%",
            ),
            rx.fragment(),
        ),
        _salon_content(),
        _modal_agregar_productos(),
        anulacion_modal(),
        spacing="4",
        width="100%",
    )


@rx.page(
    route="/mozos",
    on_load=[FoodState.on_load_mozos, FoodState.start_mozos_polling,
             FoodState.cargar_clientes],
    title="TUWAYKIFOOD | Salón",
)
def mozos_page() -> rx.Component:
    return app_shell(_mozos_content(), page_key="mozos", dark=True)
