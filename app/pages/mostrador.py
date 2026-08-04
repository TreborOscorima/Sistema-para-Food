"""Pagina de mostrador — pedidos para llevar."""

from __future__ import annotations

import reflex as rx

from app.components.shared import (
    app_shell, cumpleanos_banner, loading_placeholder,
    ACCENT, ACCENT_HOVER, ACCENT_TEXT,
    DANGER_SOLID, DANGER_TEXT,
    DARK_600, DARK_700, DARK_800,
    PAGE_BACKGROUND,
    PURPLE_LIGHT,
    SUCCESS_SOLID, SUCCESS_TEXT,
    TEXT_MUTED, TEXT_PRIMARY, TEXT_WHITE,
    WARNING_SOLID,
)
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
                    font_size="12px", font_weight="600", color=TEXT_PRIMARY,
                    no_of_lines=1,
                ),
                rx.hstack(
                    rx.text(
                        producto.precio_texto,
                        font_size="12px", font_weight="700", color=ACCENT,
                    ),
                    rx.cond(
                        producto.stock_diario >= 0,
                        rx.badge(
                            "Stock: " + producto.stock_diario.to_string(),
                            variant="surface",
                            size="1",
                            color_scheme=rx.cond(
                                producto.stock_diario > producto.stock_diario_alerta,
                                "blue",
                                rx.cond(producto.stock_diario > 0, "orange", "red"),
                            ),
                        ),
                    ),
                    spacing="2",
                    align="center",
                ),
                spacing="0", align="start", flex="1", min_width="0",
            ),
            rx.box(
                rx.icon(tag="plus", size=12, color=TEXT_WHITE),
                width="22px", height="22px", border_radius="6px",
                background=ACCENT, display="flex",
                align_items="center", justify_content="center",
                flex_shrink="0",
            ),
            spacing="2", align="center", width="100%",
        ),
        on_click=FoodState.agregar_producto_mostrador(producto.id),
        background=DARK_800,
        border=f"1.5px solid {DARK_700}",
        border_radius="8px",
        padding="8px 10px",
        cursor="pointer",
        _hover={"border": f"1.5px solid {ACCENT}"},
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
                    font_size="12px", font_weight="600", color=TEXT_PRIMARY,
                    no_of_lines=1,
                ),
                rx.cond(
                    item.es_combo,
                    rx.badge("🍱 Combo", background=WARNING_SOLID, color="#FDE68A",
                             border_radius="4px", font_size="9px", padding="1px 5px"),
                    rx.fragment(),
                ),
                rx.cond(
                    item.modificadores_texto != "",
                    rx.text(
                        "⚙ " + item.modificadores_texto,
                        font_size="10px", color=PURPLE_LIGHT,
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
                    background="rgba(239,68,68,0.08)", color=DANGER_TEXT,
                    border="1px solid #FECACA", border_radius="8px",
                    font_size="18px", cursor="pointer", padding="0",
                    _hover={"opacity": "0.8"},
                ),
                rx.text(
                    item.cantidad.to_string(),
                    font_size="14px", font_weight="700", color=ACCENT,
                    min_width="24px", text_align="center",
                ),
                rx.button(
                    "+",
                    on_click=FoodState.agregar_producto_mostrador(item.producto_id),
                    width="40px", height="40px",
                    background="rgba(34,197,94,0.08)", color=SUCCESS_SOLID,
                    border="1px solid #BBF7D0", border_radius="8px",
                    font_size="18px", cursor="pointer", padding="0",
                    _hover={"opacity": "0.8"},
                ),
                spacing="2", align="center",
            ),
            rx.text(
                item.subtotal_texto,
                font_size="13px", font_weight="600", color=TEXT_MUTED,
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
                    background=PAGE_BACKGROUND, border=f"1px solid {DARK_600}",
                    color=TEXT_PRIMARY, border_radius="6px",
                    font_size="11px", padding_x="8px", padding_y="4px",
                    width="100%", height="28px",
                    _focus={"border": f"1px solid {ACCENT}"},
                    _placeholder={"color": TEXT_MUTED},
                ),
                rx.button(
                    rx.icon(tag="check", size=11),
                    on_click=FoodState.guardar_nota_item_mostrador(item.producto_id),
                    width="28px", height="28px",
                    background=DARK_800, color=SUCCESS_SOLID,
                    border=f"1px solid {DARK_700}", border_radius="6px",
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
                        font_size="10px", color=TEXT_MUTED,
                        no_of_lines=1, flex="1", min_width="0",
                    ),
                    rx.fragment(),
                ),
                rx.text(
                    rx.cond(item.nota != "", "editar", "+ nota"),
                    font_size="10px", color=TEXT_MUTED, cursor="pointer",
                    _hover={"color": ACCENT},
                    on_click=FoodState.abrir_nota_item_mostrador(item.producto_id),
                ),
                width="100%", align="center", spacing="1",
            ),
        ),
        spacing="1", width="100%",
        padding="6px 0",
        border_bottom=f"1px solid {DARK_800}",
    )


# ─── Card de pedido pendiente ───────────────────────────────────────────────

def _pendiente_card(pedido: MostradorPendienteView) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.text(pedido.cliente_nombre, font_size="13px", font_weight="700", color=TEXT_WHITE),
                rx.spacer(),
                rx.cond(
                    pedido.en_cocina,
                    rx.badge("En cocina", background=PAGE_BACKGROUND, color="#FCD34D",
                             border="1px solid #FCD34D", border_radius="20px",
                             font_size="10px", font_weight="700", padding_x="8px"),
                    rx.badge("Listo", background="#052E16", color="#4ADE80",
                             border="1px solid #4ADE80", border_radius="20px",
                             font_size="10px", font_weight="700", padding_x="8px"),
                ),
                width="100%", align="center",
            ),
            rx.text("#" + pedido.pedido_id.to_string(),
                    font_size="20px", font_weight="900", color=ACCENT,
                    letter_spacing="-0.5px"),
            rx.text(pedido.items_resumen, font_size="11px", color=TEXT_MUTED, no_of_lines=2),
            rx.hstack(
                rx.text(pedido.total_texto, font_size="13px", font_weight="800", color=ACCENT),
                rx.spacer(),
                rx.text(pedido.hora_texto, font_size="11px", color=TEXT_MUTED),
                width="100%", align="center",
            ),
            spacing="1", width="100%",
        ),
        background=PAGE_BACKGROUND,
        border=f"1px solid {DARK_700}",
        border_radius="10px",
        padding="12px",
    )


# ─── Card de pedido entregado ───────────────────────────────────────────────

def _entregado_card(pedido: MostradorEntregadoView) -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.vstack(
                rx.text(pedido.cliente_nombre, font_size="13px", font_weight="600", color=TEXT_PRIMARY),
                rx.text(pedido.items_resumen, font_size="11px", color=TEXT_MUTED),
                spacing="0", align="start",
            ),
            rx.spacer(),
            rx.vstack(
                rx.text(pedido.total_texto, font_size="13px", font_weight="700", color="#4ADE80"),
                rx.text(pedido.hora_texto, font_size="11px", color=TEXT_MUTED),
                align="end", spacing="0",
            ),
            width="100%", align="center",
        ),
        background=DARK_800,
        border=f"1px solid {DARK_700}",
        border_radius="8px",
        padding="10px 14px",
    )


# ─── Layout principal ───────────────────────────────────────────────────────

def _carrito_panel_inner(items_max_height: str) -> rx.Component:
    """Contenido del carrito (encabezado + total + ítems + acciones). Se reutiliza
    en la columna derecha (escritorio) y en el panel deslizable (móvil)."""
    return rx.vstack(
        rx.hstack(
            rx.icon(tag="shopping_cart", size=14, color=ACCENT),
            rx.text("Pedido para llevar", font_size="13px", font_weight="700", color=ACCENT),
            rx.spacer(),
            rx.hstack(
                rx.cond(
                    FoodState.mostrador_cupon_id_aplicado > 0,
                    rx.text(FoodState.total_mostrador_texto, font_size="11px",
                            color=TEXT_MUTED, text_decoration="line-through"),
                    rx.fragment(),
                ),
                rx.text(FoodState.total_mostrador_neto_texto, font_size="15px",
                        font_weight="800", color=TEXT_WHITE),
                spacing="2", align="center",
            ),
            width="100%", align="center",
        ),
        rx.box(
            rx.cond(
                FoodState.mostrador_carrito.length() == 0,
                rx.center(
                    rx.vstack(
                        rx.icon(tag="clipboard_list", size=24, color=TEXT_MUTED),
                        rx.text("Agrega productos", font_size="11px", color=TEXT_MUTED),
                        spacing="1", align="center",
                    ),
                    padding_y="20px",
                ),
                rx.vstack(
                    rx.foreach(FoodState.mostrador_carrito, _carrito_item),
                    width="100%", spacing="0",
                ),
            ),
            overflow_y="auto", max_height=items_max_height, width="100%", flex="1",
        ),
        rx.hstack(
            rx.button(
                "Limpiar",
                on_click=FoodState.limpiar_carrito_mostrador,
                background="transparent", color=TEXT_MUTED,
                border=f"1px solid {DARK_700}", border_radius="8px",
                font_size="12px", cursor="pointer", padding_x="14px", height="42px",
                _hover={"border_color": DANGER_SOLID, "color": "#FCA5A5"},
            ),
            rx.button(
                rx.hstack(rx.icon(tag="send", size=15), rx.text("Enviar a Cocina"),
                          spacing="2", align="center"),
                on_click=FoodState.enviar_pedido_mostrador,
                is_loading=FoodState.mostrador_enviando,
                background=ACCENT, color=TEXT_WHITE, border_radius="8px",
                font_size="14px", font_weight="700", cursor="pointer", height="42px",
                _hover={"background": ACCENT_HOVER}, flex="1",
                is_disabled=FoodState.mostrador_carrito.length() == 0,
            ),
            spacing="2", width="100%",
        ),
        spacing="2", width="100%",
    )


def _pendientes_panel() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.icon(tag="clock", size=13, color="#FCD34D"),
            rx.text("Pendientes de cobro", font_size="13px", font_weight="700", color="#FCD34D"),
            spacing="2", align="center",
        ),
        rx.cond(
            FoodState.pedidos_mostrador_pendientes.length() == 0,
            rx.center(rx.text("Sin pedidos en espera", font_size="12px", color=TEXT_MUTED),
                      padding_y="10px"),
            rx.vstack(rx.foreach(FoodState.pedidos_mostrador_pendientes, _pendiente_card),
                      spacing="2", width="100%"),
        ),
        spacing="2", width="100%",
    )


def _cobrados_panel() -> rx.Component:
    return rx.vstack(
        rx.text("Cobrados hoy", font_size="13px", font_weight="700", color=TEXT_MUTED),
        rx.cond(
            FoodState.pedidos_mostrador_entregados.length() == 0,
            rx.center(rx.text("Sin historial", font_size="12px", color=TEXT_MUTED),
                      padding_y="10px"),
            rx.vstack(rx.foreach(FoodState.pedidos_mostrador_entregados, _entregado_card),
                      spacing="2", width="100%"),
        ),
        spacing="2", width="100%",
    )


def _mobile_cart_bar() -> rx.Component:
    """Barra fija abajo (solo móvil) que muestra ítems + total y abre el carrito
    en un panel deslizable. Se muestra únicamente cuando hay ítems en el carrito."""
    return rx.box(
        rx.drawer.root(
            rx.drawer.trigger(
                rx.box(
                    rx.hstack(
                        rx.box(
                            rx.icon(tag="shopping_cart", size=20, color=TEXT_WHITE),
                            rx.box(
                                rx.text(FoodState.mostrador_carrito.length().to_string(),
                                        font_size="10px", font_weight="800", color=ACCENT),
                                background=TEXT_WHITE, border_radius="50%",
                                min_width="18px", height="18px", display="flex",
                                align_items="center", justify_content="center",
                                position="absolute", top="-6px", right="-8px",
                            ),
                            position="relative", flex_shrink="0", display="flex",
                        ),
                        rx.vstack(
                            rx.text("Ver pedido", font_size="14px", font_weight="800",
                                    color=TEXT_WHITE, line_height="1.15"),
                            rx.text(FoodState.mostrador_carrito.length().to_string() + " producto(s)",
                                    font_size="10px", color="rgba(255,255,255,0.85)", line_height="1.15"),
                            spacing="0", align="start",
                        ),
                        rx.spacer(),
                        rx.text(FoodState.total_mostrador_neto_texto, font_size="17px",
                                font_weight="800", color=TEXT_WHITE),
                        rx.icon(tag="chevron_up", size=20, color=TEXT_WHITE),
                        spacing="3", align="center", width="100%",
                    ),
                    background=ACCENT, border_radius="12px", padding="12px 16px",
                    box_shadow="0 6px 20px rgba(234,88,12,0.5)", cursor="pointer",
                    width="100%",
                )
            ),
            rx.drawer.portal(
                rx.drawer.overlay(background="rgba(15,23,42,0.6)", z_index="1000"),
                rx.drawer.content(
                    rx.vstack(
                        rx.drawer.close(
                            rx.box(width="44px", height="5px", background=DARK_600,
                                   border_radius="3px", margin="2px auto 4px", cursor="pointer"),
                        ),
                        _carrito_panel_inner("50vh"),
                        spacing="3", width="100%",
                    ),
                    background=DARK_800, border_top=f"1px solid {DARK_700}",
                    border_radius="16px 16px 0 0", padding="10px 16px 24px",
                    max_height="85vh", z_index="1001",
                ),
            ),
            open=FoodState.mostrador_cart_sheet_abierto,
            on_open_change=FoodState.set_mostrador_cart_sheet_abierto,
            direction="bottom",
        ),
        position="fixed", bottom="0", left="0", right="0", z_index="900",
        padding="10px 12px calc(12px + env(safe-area-inset-bottom))",
        background="linear-gradient(to top, rgba(15,23,42,0.98) 55%, rgba(15,23,42,0))",
        display=rx.breakpoints(initial="block", lg="none"),
    )


def _mostrador_content() -> rx.Component:
    return rx.vstack(
        _modal_seleccion_mods_m(),
        cumpleanos_banner(),
        # Header
        rx.vstack(
            rx.text("Mostrador", font_size="22px", font_weight="800", color=TEXT_WHITE),
            rx.text("Pedidos para llevar", font_size="13px", color=TEXT_MUTED),
            spacing="0",
        ),
        # Contenido: 2 columnas principales
        rx.flex(
            # ─── Columna izquierda: catálogo de productos ───
            rx.vstack(
                # Nombre del cliente
                rx.hstack(
                    rx.icon(tag="user", size=14, color=TEXT_MUTED, flex_shrink="0"),
                    rx.input(
                        value=FoodState.mostrador_cliente_nombre,
                        on_change=FoodState.set_mostrador_cliente_nombre,
                        placeholder="Nombre del cliente (opcional)",
                        background="transparent",
                        border="none",
                        color=TEXT_PRIMARY,
                        font_size="13px",
                        outline="none",
                        width="100%",
                        _focus={"outline": "none", "box_shadow": "none"},
                        _placeholder={"color": TEXT_MUTED},
                    ),
                    spacing="2", align="center", width="100%",
                    background=PAGE_BACKGROUND,
                    border=f"1px solid {DARK_700}",
                    border_radius="8px",
                    padding="6px 10px",
                ),
                # Buscador
                rx.box(
                    rx.hstack(
                        rx.icon(tag="search", size=14, color=TEXT_MUTED, flex_shrink="0"),
                        rx.input(
                            value=FoodState.busqueda_producto_mostrador,
                            on_change=FoodState.set_busqueda_producto_mostrador,
                            placeholder="Buscar producto...",
                            background="transparent",
                            border="none",
                            color=TEXT_PRIMARY,
                            font_size="13px",
                            outline="none",
                            width="100%",
                            _focus={"outline": "none", "box_shadow": "none"},
                            _placeholder={"color": TEXT_MUTED},
                        ),
                        rx.cond(
                            FoodState.busqueda_producto_mostrador != "",
                            rx.box(
                                rx.icon(tag="x", size=12, color=TEXT_MUTED),
                                cursor="pointer",
                                on_click=FoodState.set_busqueda_producto_mostrador(""),
                                _hover={"opacity": "0.7"},
                            ),
                            rx.fragment(),
                        ),
                        spacing="2", align="center", width="100%",
                    ),
                    background=PAGE_BACKGROUND,
                    border=f"1px solid {DARK_700}",
                    border_radius="8px",
                    padding="6px 10px",
                    width="100%",
                ),
                # Filtros de categoría
                rx.hstack(
                    rx.button(
                        "Todos",
                        on_click=FoodState.seleccionar_mostrador_categoria(0),
                        background=rx.cond(FoodState.mostrador_categoria_activa_id == 0, ACCENT, "transparent"),
                        color=rx.cond(FoodState.mostrador_categoria_activa_id == 0, TEXT_WHITE, TEXT_MUTED),
                        border=rx.cond(FoodState.mostrador_categoria_activa_id == 0, f"1px solid {ACCENT}", f"1px solid {DARK_700}"),
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
                            background=rx.cond(FoodState.mostrador_categoria_activa_id == cat.id, ACCENT, "transparent"),
                            color=rx.cond(FoodState.mostrador_categoria_activa_id == cat.id, TEXT_WHITE, TEXT_MUTED),
                            border=rx.cond(FoodState.mostrador_categoria_activa_id == cat.id, f"1px solid {ACCENT}", f"1px solid {DARK_700}"),
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
                                rx.icon(tag="search_x", size=28, color=TEXT_MUTED),
                                rx.text("Sin resultados", font_size="13px", color=TEXT_MUTED),
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
                # Combos
                rx.cond(
                    FoodState.combos_menu.length() > 0,
                    rx.vstack(
                        rx.hstack(
                            rx.text("🍱", font_size="14px"),
                            rx.text("Combos", font_size="12px", font_weight="700", color="#FDE68A"),
                            rx.badge(
                                FoodState.combos_menu.length().to_string(),
                                background=WARNING_SOLID, color="#FDE68A",
                                border_radius="8px", font_size="10px", padding_x="6px",
                            ),
                            spacing="2", align="center",
                        ),
                        rx.grid(
                            rx.foreach(FoodState.combos_menu, _combo_card_m),
                            columns=rx.breakpoints(initial="1", sm="2"),
                            gap="6px", width="100%",
                        ),
                        spacing="2", width="100%",
                    ),
                    rx.fragment(),
                ),
                spacing="2",
                flex="3",
                min_width="0",
                height=rx.breakpoints(initial="auto", lg="calc(100vh - 140px)"),
            ),
            # ─── Columna derecha (SOLO ESCRITORIO): carrito + pendientes + cobrados ───
            # En móvil el carrito vive en la barra fija + panel deslizable (abajo),
            # y pendientes/cobrados se muestran apilados debajo del catálogo.
            rx.vstack(
                rx.box(
                    _carrito_panel_inner("22vh"),
                    width="100%", background=DARK_800,
                    border=f"1px solid {DARK_700}", border_radius="10px", padding="12px",
                ),
                rx.divider(border_color=TEXT_MUTED),
                _pendientes_panel(),
                _cobrados_panel(),
                spacing="3",
                flex="2",
                min_width="0",
                height=rx.breakpoints(initial="auto", lg="calc(100vh - 140px)"),
                overflow_y="auto",
                display=rx.breakpoints(initial="none", lg="flex"),
            ),
            direction=rx.breakpoints(initial="column", lg="row"),
            gap="16px",
            width="100%",
            flex="1",
        ),
        # ─── Pendientes + cobrados (SOLO MÓVIL), debajo del catálogo ───
        rx.vstack(
            rx.divider(border_color=DARK_700),
            _pendientes_panel(),
            _cobrados_panel(),
            spacing="3", width="100%",
            display=rx.breakpoints(initial="flex", lg="none"),
        ),
        # Espacio para que la barra fija no tape el último contenido en móvil.
        rx.box(height="88px", width="100%", display=rx.breakpoints(initial="block", lg="none")),
        # ─── Barra fija del carrito (SOLO MÓVIL) ───
        rx.cond(
            FoodState.mostrador_carrito.length() > 0,
            _mobile_cart_bar(),
            rx.fragment(),
        ),
        spacing="4",
        width="100%",
    )


def _combo_card_m(combo: dict) -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.text(combo["emoji"].to(str), font_size="18px", line_height="1", flex_shrink="0"),
            rx.vstack(
                rx.text(combo["nombre"].to(str), font_size="12px", font_weight="600", color=TEXT_PRIMARY, no_of_lines=1),
                rx.text(combo["items_texto"].to(str), font_size="10px", color=TEXT_MUTED, no_of_lines=1),
                rx.text(combo["precio_texto"].to(str), font_size="12px", font_weight="700", color=ACCENT),
                spacing="0", align="start", flex="1", min_width="0",
            ),
            rx.box(
                rx.icon(tag="plus", size=16, color=TEXT_WHITE),
                on_click=FoodState.agregar_combo_mostrador(combo["id"].to(int)),
                width="36px", height="36px", border_radius="8px",
                background=ACCENT, display="flex", align_items="center",
                justify_content="center", flex_shrink="0", cursor="pointer",
                _hover={"background": ACCENT_HOVER},
                transition="all 0.12s ease",
            ),
            spacing="2", align="center", width="100%",
        ),
        background=DARK_800, border=f"1px solid {DARK_700}", border_radius="10px",
        padding="8px 10px",
        _hover={"border_color": "#FDE68A"},
        transition="all 0.12s ease",
    )


def _mod_item_flat_m(item: dict) -> rx.Component:
    return rx.cond(
        item["type"] == "header",
        rx.hstack(
            rx.text(
                item["nombre"].to(str),
                font_size="13px", font_weight="700", color=TEXT_PRIMARY,
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
                font_size="10px", color=TEXT_MUTED,
            ),
            spacing="2", align="center", width="100%",
            padding_top="8px",
        ),
        rx.box(
            rx.hstack(
                rx.box(
                    width="16px", height="16px", border_radius="4px",
                    background=rx.cond(item["selected"].to(bool), ACCENT, "transparent"),
                    border=rx.cond(item["selected"].to(bool), f"2px solid {ACCENT}", f"2px solid {DARK_600}"),
                    flex_shrink="0",
                    display="flex", align_items="center", justify_content="center",
                ),
                rx.text(
                    item["nombre"].to(str),
                    font_size="13px", color=TEXT_PRIMARY, font_weight="500",
                    flex="1",
                ),
                rx.cond(
                    item["precio_extra"].to(float) > 0,
                    rx.text(
                        "+S/" + item["precio_extra"].to(float).to_string(),
                        font_size="12px", color=ACCENT, font_weight="600",
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
            background=rx.cond(item["selected"].to(bool), DARK_800, "transparent"),
            border=rx.cond(item["selected"].to(bool), f"1px solid {ACCENT}", f"1px solid {DARK_700}"),
            _hover={"background": DARK_800},
            transition="all 0.12s ease",
        ),
    )


def _modal_seleccion_mods_m() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.hstack(
                    rx.icon(tag="settings_2", size=16, color=PURPLE_LIGHT),
                    rx.dialog.title(
                        FoodState.mod_seleccion_producto_nombre,
                        font_size="15px", font_weight="700", color=TEXT_WHITE, margin="0",
                    ),
                    rx.spacer(),
                    rx.dialog.close(
                        rx.box(
                            rx.icon(tag="x", size=16, color=TEXT_MUTED),
                            cursor="pointer", padding="4px",
                            border_radius="6px",
                            _hover={"background": DARK_700},
                        ),
                    ),
                    width="100%", align="center",
                ),
                rx.text(
                    "Seleccione las opciones para este producto",
                    font_size="12px", color=TEXT_MUTED,
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
                        font_size="12px", font_weight="600", color=ACCENT,
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
                    background=ACCENT, color=TEXT_WHITE,
                    border_radius="8px", font_size="13px",
                    font_weight="700", width="100%",
                    cursor="pointer",
                    _hover={"background": ACCENT_HOVER},
                    is_disabled=~FoodState.mod_seleccion_valido,
                ),
                spacing="3", width="100%",
            ),
            background=PAGE_BACKGROUND,
            border=f"1px solid {DARK_800}",
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
