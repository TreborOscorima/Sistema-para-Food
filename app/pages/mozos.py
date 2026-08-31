"""Pagina de mozos — mapa de salon + menu + carrito."""

from __future__ import annotations

import reflex as rx

from app.components.shared import (
    SUCCESS_DARK,
    WARNING_TEXT, SUCCESS_TEXT,
    anulacion_modal, app_shell, cumpleanos_banner, loading_placeholder, preview_ticket_modal, section_card, surface_card,
    ACCENT, ACCENT_HOVER,
    DANGER_SOLID,
    DARK_600, DARK_700, DARK_800,
    PAGE_BACKGROUND, SURFACE_BASE,
    PURPLE, PURPLE_LIGHT,
    SUCCESS_SOLID,
    TEXT_MUTED, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_WHITE,
    WARNING_SOLID,
)
from app.components.ayuda import ayuda_modal, ayuda_trigger, empty_state
from app.states.food_state import CarritoItem, FoodState, HistorialItem, MesaView, ProductoView, SelfOrderPendienteView


def _mozos_ayuda() -> rx.Component:
    return ayuda_modal(
        titulo="¿Cómo funciona Mozos?",
        subtitulo="Toma y gestiona los pedidos de cada mesa del salón.",
        secciones=[{
            "titulo": None,
            "pasos": [
                "Toca una mesa del salón para abrir su comanda.",
                "Agrega productos —con sus opciones y notas— y envíalos a cocina.",
                "La mesa cambia de color según su estado (ver abajo).",
                "Cuando el cliente pida la cuenta, genera la precuenta desde la comanda.",
                "El cobro final se hace en el módulo Caja.",
            ],
        }],
        leyenda=[
            ("var(--twk-slate-500)", "Libre"),
            ("var(--twk-accent-text)", "Ocupada"),
            ("var(--twk-warning-text)", "Cuenta pedida"),
            (PURPLE_LIGHT, "Reservada"),
        ],
    )


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
                        background="rgba(245,158,11,0.15)",
                        border="1.5px solid rgba(245,158,11,0.30)",
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
                color=rx.cond(selected, TEXT_WHITE, TEXT_PRIMARY),
                line_height="1",
            ),
            # Reserva indicator
            rx.cond(
                mesa.reserva_texto != "",
                rx.badge(
                    "📅 " + mesa.reserva_texto,
                    background=PURPLE,
                    color="#E9D5FF",
                    border_radius="4px",
                    font_size="9px",
                    font_weight="700",
                    padding="1px 6px",
                    letter_spacing="0.02em",
                ),
                rx.fragment(),
            ),
            # Mozo que atiende
            rx.cond(
                mesa.mozo_nombre != "",
                rx.text(
                    "👤 " + mesa.mozo_nombre,
                    font_size="10px",
                    font_weight="600",
                    color=rx.cond(selected, "#FED7AA", TEXT_MUTED),
                    no_of_lines=1,
                ),
                rx.fragment(),
            ),
            # Total y tiempo si tiene consumo
            rx.cond(
                mesa.total_abierto > 0,
                rx.hstack(
                    rx.text(
                        mesa.total_abierto_texto,
                        font_size="13px",
                        font_weight="700",
                        color=rx.cond(selected, TEXT_WHITE, TEXT_MUTED),
                    ),
                    rx.text(
                        "⏱ " + mesa.tiempo_abierto_texto,
                        font_size="11px",
                        color=rx.cond(selected, "#FED7AA", TEXT_MUTED),
                    ),
                    spacing="2", align="center", wrap="wrap",
                ),
                rx.fragment(),
            ),
            # Nivel 3: Alerta de inactividad (> 4h)
            rx.cond(
                mesa.inactivo_minutos >= 240,
                rx.badge(
                    "⚠ Inactivo " + (mesa.inactivo_minutos / 60).to(int).to_string() + "h",
                    background="rgba(239,68,68,0.15)",
                    color="var(--twk-danger-text)",
                    border="1px solid rgba(239,68,68,0.3)",
                    border_radius="4px",
                    font_size="9px",
                    font_weight="700",
                    padding="1px 6px",
                ),
                rx.fragment(),
            ),
            # Items listos texto
            rx.cond(
                mesa.tiene_items_listos,
                rx.text(
                    mesa.items_listos_count.to_string() + " listos ↑",
                    font_size="10px",
                    color="var(--twk-warning-text)",
                    font_weight="700",
                ),
                rx.fragment(),
            ),
            spacing="2",
            align="start",
            width="100%",
        ),
        background=rx.cond(selected, ACCENT, mesa.card_bg),
        border=rx.cond(selected, f"2px solid {ACCENT}", mesa.card_border),
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


# ─── Grupo de mesas por sector ───────────────────────────────────────────────

def _sector_group(sector: str) -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.box(width="3px", height="14px", background=ACCENT, border_radius="2px"),
            rx.text(
                sector,
                font_size="14px",
                font_weight="700",
                color=TEXT_PRIMARY,
                letter_spacing="-0.3px",
            ),
            spacing="2",
            align="center",
        ),
        rx.flex(
            rx.foreach(
                FoodState.mesas,
                lambda m: rx.cond(m.sector == sector, _mesa_card(m), rx.fragment()),
            ),
            flex_wrap="wrap",
            gap="12px",
            width="100%",
        ),
        spacing="2",
        width="100%",
    )


# ─── Self-order pendientes ───────────────────────────────────────────────────

def _self_order_card(order: SelfOrderPendienteView) -> rx.Component:
    return rx.hstack(
        rx.vstack(
            rx.hstack(
                rx.badge(order.mesa_label, background="rgba(59,130,246,0.12)",
                         color="#3B82F6", border_radius="5px",
                         font_size="10px", font_weight="700",
                         padding="2px 8px"),
                rx.text(order.nombre_cliente, font_size="13px",
                        font_weight="700", color="var(--twk-slate-200)",
                        no_of_lines=1),
                rx.text(order.hora_texto, font_size="11px",
                        color=TEXT_MUTED),
                spacing="2", align="center",
            ),
            rx.text(order.items_resumen, font_size="11px",
                    color=TEXT_MUTED, no_of_lines=1),
            rx.text(order.total_texto, font_size="13px",
                    font_weight="800", color="#FB923C"),
            spacing="1", align="start", flex="1", min_width="0",
        ),
        rx.hstack(
            rx.tooltip(
                rx.button(
                    rx.icon(tag="check", size=14),
                    on_click=FoodState.aprobar_self_order(order.pedido_id),
                    background="rgba(34,197,94,0.12)", color=SUCCESS_TEXT,
                    border="1px solid #BBF7D0", border_radius="7px",
                    padding="6px 10px", cursor="pointer", height="auto",
                    _hover={"background": "rgba(34,197,94,0.25)"},
                ),
                content="Aprobar pedido del cliente",
            ),
            rx.tooltip(
                rx.button(
                    rx.icon(tag="x", size=14),
                    on_click=FoodState.rechazar_self_order(order.pedido_id),
                    background="rgba(239,68,68,0.12)", color="var(--twk-danger-text)",
                    border="1px solid #FECACA", border_radius="7px",
                    padding="6px 10px", cursor="pointer", height="auto",
                    _hover={"background": "rgba(239,68,68,0.25)"},
                ),
                content="Rechazar pedido del cliente",
            ),
            spacing="1", align="center", flex_shrink="0",
        ),

        width="100%", align="center",
        padding="10px 12px",
        background=DARK_800,
        border="1px solid #7C3AED40",
        border_radius="8px",
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
                    color=WARNING_TEXT,
                ),
                background="rgba(245,158,11,0.10)",
                border="1px solid rgba(245,158,11,0.25)",
                border_radius="8px",
                padding="8px 14px",
                width="100%",
            ),
            rx.fragment(),
        ),
        rx.cond(
            FoodState.self_orders_pendientes.length() > 0,
            rx.vstack(
                rx.hstack(
                    rx.icon(tag="smartphone", size=16, color=PURPLE),
                    rx.text(
                        FoodState.self_orders_pendientes.length().to_string()
                        + " pedido(s) QR pendiente(s) de aprobación",
                        font_size="13px", font_weight="600", color=PURPLE_LIGHT,
                    ),
                    spacing="2", align="center", width="100%",
                    background="rgba(124,58,237,0.08)", border="1px solid rgba(124,58,237,0.20)",
                    border_radius="8px", padding="8px 14px",
                ),
                rx.foreach(FoodState.self_orders_pendientes, _self_order_card),
                spacing="2", width="100%",
            ),
            rx.fragment(),
        ),
        # Leyenda de estados
        rx.hstack(
            rx.hstack(
                rx.box(width="10px", height="10px", border_radius="3px",
                       border=f"2px solid {DARK_700}", background=DARK_800),
                rx.text("Libre", font_size="10px", color=TEXT_MUTED),
                spacing="1", align="center",
            ),
            rx.hstack(
                rx.box(width="10px", height="10px", border_radius="3px",
                       border=f"2px solid {ACCENT}", background=DARK_800),
                rx.text("Ocupada", font_size="10px", color="var(--twk-accent-text)"),
                spacing="1", align="center",
            ),
            rx.hstack(
                rx.box(width="10px", height="10px", border_radius="3px",
                       border="2px solid #F59E0B", background=DARK_800),
                rx.text("Cuenta", font_size="10px", color="var(--twk-warning-text)"),
                spacing="1", align="center",
            ),
            rx.hstack(
                rx.box(width="10px", height="10px", border_radius="3px",
                       border="3px solid #F59E0B", background="rgba(245,158,11,0.15)"),
                rx.text("Items listos", font_size="10px", color="var(--twk-warning-text)"),
                spacing="1", align="center",
            ),
            rx.hstack(
                rx.box(width="10px", height="10px", border_radius="3px",
                       border="2px solid #7C3AED", background=DARK_800),
                rx.text("Reservada", font_size="10px", color=PURPLE_LIGHT),
                spacing="1", align="center",
            ),
            spacing="3", align="center", flex_wrap="wrap",
        ),
        # Filtro por sector
        rx.cond(
            FoodState.sectores_unicos.length() > 1,
            rx.hstack(
                rx.button(
                    "Todos",
                    on_click=FoodState.set_mozos_filtro_sector(""),
                    background=rx.cond(FoodState.mozos_filtro_sector == "", ACCENT, DARK_800),
                    color=rx.cond(FoodState.mozos_filtro_sector == "", TEXT_WHITE, TEXT_MUTED),
                    border=rx.cond(FoodState.mozos_filtro_sector == "", f"1px solid {ACCENT}", f"1px solid {DARK_700}"),
                    border_radius="6px", font_size="12px", font_weight="600",
                    padding_x="10px", padding_y="5px", cursor="pointer",
                    _hover={"border_color": ACCENT},
                ),
                rx.foreach(
                    FoodState.sectores_unicos,
                    lambda s: rx.button(
                        s,
                        on_click=FoodState.set_mozos_filtro_sector(s),
                        background=rx.cond(FoodState.mozos_filtro_sector == s, ACCENT, DARK_800),
                        color=rx.cond(FoodState.mozos_filtro_sector == s, TEXT_WHITE, TEXT_MUTED),
                        border=rx.cond(FoodState.mozos_filtro_sector == s, f"1px solid {ACCENT}", f"1px solid {DARK_700}"),
                        border_radius="6px", font_size="12px", font_weight="600",
                        padding_x="10px", padding_y="5px", cursor="pointer",
                        _hover={"border_color": ACCENT},
                    ),
                ),
                spacing="1", align="center", flex_wrap="wrap",
            ),
            rx.fragment(),
        ),
        rx.cond(
            FoodState.mesas.length() == 0,
            rx.cond(
                FoodState.puede_ver_configuracion,
                empty_state(
                    icono="layout_grid",
                    titulo="No hay mesas configuradas",
                    texto="Agrega tus mesas y sectores para empezar a tomar pedidos.",
                    cta_label="Configurar mesas",
                    cta_href="/configuracion",
                ),
                empty_state(
                    icono="layout_grid",
                    titulo="No hay mesas configuradas",
                    texto="Pídele al administrador que configure las mesas en Configuración → Mesas.",
                ),
            ),
            rx.cond(
                (FoodState.sectores_unicos.length() > 1) & (FoodState.mozos_filtro_sector == ""),
                rx.vstack(
                    rx.foreach(FoodState.sectores_unicos, _sector_group),
                    spacing="4",
                    width="100%",
                ),
                rx.flex(
                    rx.foreach(FoodState.mesas_filtradas_por_sector, _mesa_card),
                    flex_wrap="wrap",
                    gap="12px",
                    width="100%",
                ),
            ),
        ),
        spacing="3",
        width="100%",
    )


# ─── Modal de agregar productos a mesa ────────────────────────────────────────

def _producto_card_compact(producto: ProductoView) -> rx.Component:
    return rx.cond(
        producto.disponible,
        # ── Producto disponible ──
        rx.box(
            rx.hstack(
                rx.text(producto.emoji, font_size="18px", line_height="1", flex_shrink="0"),
                rx.vstack(
                    rx.text(
                        producto.nombre,
                        font_size="12px",
                        font_weight="600",
                        color=TEXT_PRIMARY,
                        no_of_lines=1,
                    ),
                    rx.hstack(
                        rx.text(
                            producto.precio_texto,
                            font_size="12px",
                            font_weight="700",
                            color=ACCENT,
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
                    spacing="0",
                    align="start",
                    flex="1",
                    min_width="0",
                ),
                rx.hstack(
                    rx.box(
                        rx.icon(tag="ban", size=15, color=TEXT_MUTED),
                        on_click=FoodState.toggle_producto_disponible(producto.id),
                        width=rx.breakpoints(initial="40px", md="30px"),
                        height=rx.breakpoints(initial="40px", md="30px"),
                        border_radius="6px",
                        background=PAGE_BACKGROUND,
                        border=f"1px solid {DARK_700}",
                        display="flex",
                        align_items="center",
                        justify_content="center",
                        flex_shrink="0",
                        cursor="pointer",
                        _hover={"border_color": "#EF4444", "background": "#1C1017"},
                        transition="all 0.12s ease",
                    ),
                    rx.box(
                        rx.icon(tag="plus", size=18, color=TEXT_WHITE),
                        on_click=FoodState.agregar_producto(producto.id),
                        width=rx.breakpoints(initial="40px", md="36px"),
                        height=rx.breakpoints(initial="40px", md="36px"),
                        border_radius="8px",
                        background=ACCENT,
                        display="flex",
                        align_items="center",
                        justify_content="center",
                        flex_shrink="0",
                        cursor="pointer",
                        _hover={"opacity": "0.85"},
                        transition="all 0.12s ease",
                    ),
                    spacing="1",
                    align="center",
                    flex_shrink="0",
                ),
                spacing="2",
                align="center",
                width="100%",
            ),
            background=DARK_800,
            border=f"1.5px solid {DARK_700}",
            border_radius="8px",
            padding="8px 10px",
            _hover={"border": f"1.5px solid {ACCENT}"},
            transition="all 0.12s ease",
        ),
        # ── Producto agotado (86) ──
        rx.box(
            rx.hstack(
                rx.text(producto.emoji, font_size="18px", line_height="1", flex_shrink="0", opacity="0.4"),
                rx.vstack(
                    rx.text(
                        producto.nombre,
                        font_size="12px",
                        font_weight="600",
                        color=TEXT_MUTED,
                        no_of_lines=1,
                        text_decoration="line-through",
                    ),
                    rx.badge(
                        "AGOTADO",
                        background="#7F1D1D",
                        color="var(--twk-danger-text)",
                        font_size="9px",
                        font_weight="700",
                        border_radius="4px",
                        padding="1px 6px",
                        letter_spacing="0.05em",
                    ),
                    spacing="1",
                    align="start",
                    flex="1",
                    min_width="0",
                ),
                rx.box(
                    rx.icon(tag="rotate_ccw", size=14, color=SUCCESS_TEXT),
                    on_click=FoodState.toggle_producto_disponible(producto.id),
                    width="36px",
                    height="36px",
                    border_radius="8px",
                    background="#0F2A1A",
                    border="1px solid #166534",
                    display="flex",
                    align_items="center",
                    justify_content="center",
                    flex_shrink="0",
                    cursor="pointer",
                    _hover={"border_color": "#22C55E", "background": "#14532D"},
                    transition="all 0.12s ease",
                ),
                spacing="2",
                align="center",
                width="100%",
            ),
            background=PAGE_BACKGROUND,
            border=f"1.5px solid {DARK_800}",
            border_radius="8px",
            padding="8px 10px",
            opacity="0.7",
            transition="all 0.12s ease",
        ),
    )


def _modal_carrito_item(item: CarritoItem) -> rx.Component:
    editing_nota = FoodState.nota_producto_activo_id == item.producto_id
    return rx.vstack(
        rx.hstack(
            rx.text(
                item.nombre,
                font_size="12px",
                font_weight="600",
                color=TEXT_PRIMARY,
                flex="1",
                min_width="0",
                no_of_lines=1,
            ),
            rx.hstack(
                rx.button(
                    "-",
                    on_click=FoodState.restar_producto(item.producto_id),
                    width="40px", height="40px",
                    background="rgba(239,68,68,0.08)", color="var(--twk-danger-text)",
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
                    on_click=FoodState.agregar_producto(item.producto_id),
                    width="40px", height="40px",
                    background="rgba(34,197,94,0.08)", color=SUCCESS_TEXT,
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
        # Combo badge
        rx.cond(
            item.es_combo,
            rx.badge("🍱 Combo", background=WARNING_SOLID, color="#78350F",
                     border_radius="4px", font_size="9px", padding="1px 5px"),
            rx.fragment(),
        ),
        # Modificadores
        rx.cond(
            item.modificadores_texto != "",
            rx.text(
                "⚙ " + item.modificadores_texto,
                font_size="10px", color=PURPLE_LIGHT, font_weight="500",
                padding_left="2px",
            ),
            rx.fragment(),
        ),
        # Nota inline
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
                    width="100%", height=rx.breakpoints(initial="40px", md="30px"),
                    _focus={"border": f"1px solid {ACCENT}"},
                    _placeholder={"color": TEXT_MUTED},
                ),
                rx.button(
                    rx.icon(tag="check", size=14),
                    on_click=FoodState.guardar_nota_carrito_item(item.producto_id),
                    width=rx.breakpoints(initial="40px", md="30px"),
                    height=rx.breakpoints(initial="40px", md="30px"),
                    flex_shrink="0",
                    background=DARK_800, color=SUCCESS_TEXT,
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
                    on_click=FoodState.abrir_nota_item(item.producto_id),
                ),
                width="100%", align="center", spacing="1",
            ),
        ),
        spacing="1", width="100%",
        padding="6px 0",
        border_bottom=f"1px solid {DARK_800}",
    )


def _modal_historial_item(item: HistorialItem, idx: int) -> rx.Component:
    return rx.hstack(
        rx.cond(
            FoodState.precuenta_parcial_modo,
            rx.box(
                rx.cond(
                    item.sel_precuenta,
                    rx.icon(tag="square_check", size=14, color=SUCCESS_TEXT),
                    rx.icon(tag="square", size=14, color=TEXT_MUTED),
                ),
                cursor="pointer",
                flex_shrink="0",
            ),
            rx.fragment(),
        ),
        rx.text(
            item.cantidad.to_string() + "x " + item.nombre,
            font_size="11px", font_weight="500",
            color=rx.cond(
                FoodState.precuenta_parcial_modo & item.sel_precuenta,
                SUCCESS_SOLID, "var(--twk-slate-300)",
            ),
            flex="1", min_width="0", no_of_lines=1,
        ),
        rx.cond(
            FoodState.precuenta_parcial_modo,
            rx.text(
                item.subtotal_texto,
                font_size="10px", font_weight="600",
                color=rx.cond(item.sel_precuenta, SUCCESS_SOLID, TEXT_MUTED),
                flex_shrink="0",
            ),
            rx.fragment(),
        ),
        rx.cond(
            item.nota != "",
            rx.cond(
                FoodState.precuenta_parcial_modo,
                rx.fragment(),
                rx.text(
                    item.nota,
                    font_size="10px", color=TEXT_MUTED,
                    no_of_lines=1, max_width="100px",
                ),
            ),
            rx.fragment(),
        ),
        rx.cond(
            FoodState.precuenta_parcial_modo,
            rx.fragment(),
            rx.cond(
                item.puede_entregar,
                rx.button(
                    rx.hstack(
                        rx.icon(tag="hand", size=10),
                        rx.text("Entregar", font_size="9px", font_weight="700"),
                        spacing="1", align="center",
                    ),
                    on_click=FoodState.entregar_item_historial(item.detalle_id),
                    background=SUCCESS_DARK,
                    color=TEXT_WHITE,
                    border_radius="4px",
                    padding="2px 8px",
                    cursor="pointer",
                    height="auto",
                    flex_shrink="0",
                    _hover={"background": "#16A34A"},
                ),
                rx.badge(
                    item.estado_label,
                    background=item.estado_bg,
                    color=item.estado_color,
                    font_size="9px",
                    padding_x="6px", padding_y="1px",
                    border_radius="4px",
                ),
            ),
        ),
        width="100%", align="center", spacing="2",
        padding="4px 0",
        border_bottom=f"1px solid {DARK_800}",
        cursor=rx.cond(FoodState.precuenta_parcial_modo, "pointer", "default"),
        on_click=rx.cond(
            FoodState.precuenta_parcial_modo,
            FoodState.toggle_precuenta_item(idx),
            None,
        ),
        _hover=rx.cond(
            FoodState.precuenta_parcial_modo,
            {"background": PAGE_BACKGROUND},
            {},
        ),
    )


def _transfer_mesa_card(mesa: MesaView) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.badge(
                mesa.estado_label,
                background=mesa.badge_bg,
                color=mesa.badge_text,
                border_radius="4px",
                font_size="9px",
                font_weight="700",
                padding="1px 5px",
            ),
            rx.text(
                mesa.nombre,
                font_size="13px", font_weight="700", color=TEXT_PRIMARY,
            ),
            rx.cond(
                mesa.total_abierto > 0,
                rx.text(mesa.total_abierto_texto, font_size="11px", color=TEXT_MUTED),
                rx.fragment(),
            ),
            spacing="1", align="start",
        ),
        background=SURFACE_BASE,
        border=rx.cond(
            mesa.estado == "libre",
            f"1px solid {DARK_700}",
            "1px solid #92400E",
        ),
        border_radius="10px",
        padding="10px 12px",
        cursor="pointer",
        on_click=FoodState.transferir_a_mesa(mesa.id),
        _hover={"border_color": ACCENT, "background": DARK_700},
        transition="all 0.15s ease",
        min_width="100px",
    )


def _modal_transfer() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.hstack(
                    rx.icon(tag="move_right", size=16, color=WARNING_TEXT),
                    rx.dialog.title(
                        "Transferir " + FoodState.mesa_seleccionada_label,
                        font_size="15px", font_weight="700", color=TEXT_WHITE, margin="0",
                    ),
                    rx.spacer(),
                    rx.dialog.close(
                        rx.box(
                            rx.icon(tag="x", size=16, color=TEXT_MUTED),
                            cursor="pointer",
                            padding="4px",
                            border_radius="6px",
                            _hover={"background": DARK_700},
                        ),
                    ),
                    width="100%", align="center",
                ),
                rx.text(
                    "Selecciona la mesa destino. Si está ocupada, los pedidos se fusionarán.",
                    font_size="12px", color=TEXT_MUTED,
                ),
                rx.flex(
                    rx.foreach(FoodState.mesas_destino_transfer, _transfer_mesa_card),
                    flex_wrap="wrap",
                    gap="10px",
                    width="100%",
                    max_height="50vh",
                    overflow_y="auto",
                    padding_y="8px",
                ),
                spacing="3",
                width="100%",
            ),
            background=PAGE_BACKGROUND,
            border=f"1px solid {DARK_700}",
            border_radius="14px",
            padding="20px",
            max_width="500px",
            width="90vw",
        ),
        open=FoodState.transfer_modal_abierto,
        on_open_change=FoodState.set_transfer_modal_abierto,
    )


def _mod_item_flat(item: dict) -> rx.Component:
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
                    background="#7F1D1D", color="var(--twk-danger-text)",
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


def _modal_seleccion_mods() -> rx.Component:
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
                    "Selecciona las opciones para este producto",
                    font_size="12px", color=TEXT_MUTED,
                ),
                rx.box(
                    rx.vstack(
                        rx.foreach(
                            FoodState.mod_seleccion_items_flat,
                            _mod_item_flat,
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
            border=f"1px solid {DARK_700}",
            border_radius="14px",
            padding="20px",
            max_width="420px",
            width="90vw",
        ),
        open=FoodState.mod_seleccion_modal,
        on_open_change=FoodState.set_mod_seleccion_modal,
    )


def _combo_card_mozos(combo: dict) -> rx.Component:
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
                on_click=FoodState.agregar_combo(combo["id"].to(int)),
                width="36px", height="36px", border_radius="8px",
                background=ACCENT, display="flex", align_items="center",
                justify_content="center", flex_shrink="0", cursor="pointer",
                _hover={"background": ACCENT_HOVER},
                transition="all 0.12s ease",
            ),
            spacing="2", align="center", width="100%",
        ),
        background=SURFACE_BASE, border=f"1px solid {DARK_700}", border_radius="10px",
        padding="8px 10px",
        _hover={"border_color": "#FDE68A"},
        transition="all 0.12s ease",
    )


def _pedido_panel_inner(items_max_height: str) -> rx.Component:
    """Contenido del pedido de la mesa: lo enviado a cocina + el carrito nuevo +
    las acciones (enviar, directo a caja, transferir, liberar). Se reutiliza en
    la columna derecha (desktop) y en el bottom-sheet deslizable (móvil)."""
    return rx.vstack(
        # Sección: Pedidos enviados a cocina
        rx.cond(
            FoodState.historial_pedido.length() > 0,
            rx.vstack(
                rx.hstack(
                    rx.icon(tag="chef_hat", size=14, color="#38BDF8"),
                    rx.text(
                        rx.cond(
                            FoodState.precuenta_parcial_modo,
                            "Selecciona ítems para precuenta",
                            "Enviado a cocina",
                        ),
                        font_size="12px", font_weight="700",
                        color=rx.cond(FoodState.precuenta_parcial_modo, SUCCESS_SOLID, "#38BDF8"),
                    ),
                    rx.spacer(),
                    rx.cond(
                        FoodState.precuenta_parcial_modo,
                        rx.hstack(
                            rx.button(
                                "Todos",
                                on_click=FoodState.seleccionar_todos_precuenta,
                                background="transparent",
                                color=TEXT_MUTED,
                                border=f"1px solid {DARK_700}",
                                border_radius="6px",
                                font_size="10px",
                                padding="2px 8px",
                                cursor="pointer",
                                height="auto",
                                _hover={"color": TEXT_WHITE, "border_color": TEXT_MUTED},
                            ),
                            rx.button(
                                rx.icon(tag="x", size=12),
                                on_click=FoodState.cancelar_precuenta_parcial,
                                background="transparent",
                                color="#EF4444",
                                border="none",
                                padding="2px",
                                cursor="pointer",
                                _hover={"opacity": "0.8"},
                            ),
                            spacing="1", align="center",
                        ),
                        rx.button(
                            rx.hstack(
                                rx.icon(tag="receipt", size=11),
                                rx.text("Precuenta", font_size="10px", font_weight="600"),
                                spacing="1", align="center",
                            ),
                            on_click=FoodState.activar_precuenta_parcial,
                            background="transparent",
                            color=TEXT_MUTED,
                            border=f"1px solid {DARK_700}",
                            border_radius="6px",
                            padding="2px 8px",
                            cursor="pointer",
                            height="auto",
                            _hover={"color": SUCCESS_SOLID, "border_color": SUCCESS_SOLID},
                        ),
                    ),
                    width="100%", align="center",
                ),
                rx.box(
                    rx.vstack(
                        rx.foreach(FoodState.historial_pedido, lambda item, idx: _modal_historial_item(item, idx)),
                        width="100%", spacing="0",
                    ),
                    overflow_y="auto",
                    max_height=rx.breakpoints(initial="12vh", md="20vh"),
                    width="100%",
                ),
                # Botón "Entregar todo" si hay items listos
                rx.cond(
                    ~FoodState.precuenta_parcial_modo & FoodState.hay_items_para_entregar,
                    rx.button(
                        rx.hstack(
                            rx.icon(tag="hand", size=14),
                            rx.text("Entregar todo", font_size="11px", font_weight="700"),
                            spacing="1", align="center",
                        ),
                        on_click=FoodState.entregar_todos_items_listos,
                        background=SUCCESS_DARK,
                        color=TEXT_WHITE,
                        border_radius="6px",
                        padding="6px 12px",
                        cursor="pointer",
                        width="100%",
                        _hover={"background": "#16A34A"},
                    ),
                    rx.fragment(),
                ),
                # Barra de precuenta parcial
                rx.cond(
                    FoodState.precuenta_parcial_modo & FoodState.precuenta_parcial_hay_seleccion,
                    rx.hstack(
                        rx.text(
                            "Subtotal: " + FoodState.precuenta_parcial_subtotal_texto,
                            font_size="12px", font_weight="700", color=SUCCESS_TEXT,
                        ),
                        rx.spacer(),
                        rx.button(
                            rx.hstack(
                                rx.icon(tag="printer", size=12),
                                rx.text("Imprimir", font_size="11px", font_weight="700"),
                                spacing="1", align="center",
                            ),
                            on_click=FoodState.imprimir_precuenta_parcial,
                            background=SUCCESS_DARK,
                            color=TEXT_WHITE,
                            border_radius="6px",
                            padding="4px 12px",
                            cursor="pointer",
                            height="auto",
                            _hover={"background": "#16A34A"},
                        ),
                        width="100%", align="center",
                        padding_top="6px",
                        border_top="1px solid #1E3A5F",
                    ),
                    rx.fragment(),
                ),
                spacing="2", width="100%",
                background=PAGE_BACKGROUND,
                border=rx.cond(
                    FoodState.precuenta_parcial_modo,
                    f"1px solid {SUCCESS_SOLID}",
                    "1px solid #1E3A5F",
                ),
                border_radius="8px",
                padding="8px 10px",
            ),
            rx.fragment(),
        ),
        # Sección: Nuevo pedido (carrito)
        rx.hstack(
            rx.icon(tag="shopping_cart", size=14, color=ACCENT),
            rx.text(
                rx.cond(
                    FoodState.historial_pedido.length() > 0,
                    "Nuevo pedido",
                    "Pedido",
                ),
                font_size="13px", font_weight="700", color=ACCENT,
            ),
            rx.spacer(),
            rx.text(
                FoodState.total_carrito_texto,
                font_size="13px", font_weight="700", color=TEXT_WHITE,
            ),
            width="100%", align="center",
        ),
        rx.box(
            rx.cond(
                FoodState.carrito.length() == 0,
                rx.center(
                    rx.vstack(
                        rx.icon(tag="clipboard_list", size=24, color=TEXT_MUTED),
                        rx.text("Agrega productos", font_size="11px", color=TEXT_MUTED),
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
            width="100%",
            max_height=items_max_height,
        ),
        # Botón Enviar a Cocina
        rx.button(
            rx.hstack(
                rx.icon(tag="send", size=13),
                rx.text(rx.cond(
                    FoodState.historial_pedido.length() > 0,
                    "Enviar nueva ronda",
                    "Enviar pedido",
                )),
                spacing="2", align="center",
            ),
            on_click=[FoodState.enviar_pedido, FoodState.cerrar_modal_agregar],
            background=ACCENT,
            color=TEXT_WHITE,
            border_radius="8px",
            font_size="13px",
            font_weight="700",
            width="100%",
            cursor="pointer",
            _hover={"background": ACCENT_HOVER},
            is_disabled=FoodState.cantidad_items_carrito == 0,
        ),
        # Enviar y cobrar: dispara el pedido (los ítems de preparación igual van a
        # cocina, el ruteo es automático) y deja la mesa lista para cobrar en caja.
        rx.button(
            rx.hstack(
                rx.icon(tag="receipt", size=13),
                rx.text("Enviar y cobrar"),
                spacing="2", align="center",
            ),
            on_click=[FoodState.enviar_pedido_directo_caja, FoodState.cerrar_modal_agregar],
            background="transparent",
            color=TEXT_MUTED,
            border=f"1px solid {DARK_700}",
            border_radius="8px",
            font_size="12px",
            font_weight="600",
            width="100%",
            cursor="pointer",
            _hover={"background": DARK_800, "color": TEXT_PRIMARY},
            is_disabled=FoodState.cantidad_items_carrito == 0,
        ),
        # Botón Transferir mesa (solo si mesa ocupada)
        rx.cond(
            FoodState.mesa_seleccionada_ocupada,
            rx.button(
                rx.hstack(
                    rx.icon(tag="move_right", size=13),
                    rx.text("Transferir mesa"),
                    spacing="2", align="center",
                ),
                on_click=FoodState.abrir_transfer_modal,
                background="transparent",
                color=WARNING_TEXT,
                border="1px solid #92400E",
                border_radius="8px",
                font_size="12px",
                font_weight="600",
                width="100%",
                cursor="pointer",
                _hover={"background": "#1C1917", "border": "1px solid #F59E0B"},
            ),
            rx.fragment(),
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
        spacing="2", width="100%",
    )


def _pedido_sheet_bar() -> rx.Component:
    """Barra 'Ver pedido' (solo móvil) que abre el pedido en un bottom-sheet
    deslizable, al estilo Mostrador. Aparece si hay ítems nuevos o ya enviados."""
    return rx.cond(
        (FoodState.cantidad_items_carrito > 0) | (FoodState.historial_pedido.length() > 0),
        rx.box(
            rx.hstack(
                rx.box(
                    rx.icon(tag="shopping_cart", size=19, color=TEXT_WHITE),
                    rx.cond(
                        FoodState.cantidad_items_carrito > 0,
                        rx.box(
                            rx.text(FoodState.cantidad_items_carrito.to_string(),
                                    font_size="10px", font_weight="800", color=ACCENT),
                            background=TEXT_WHITE, border_radius="50%",
                            min_width="16px", height="16px", display="flex",
                            align_items="center", justify_content="center",
                            position="absolute", top="-7px", right="-8px",
                        ),
                        rx.fragment(),
                    ),
                    position="relative", flex_shrink="0", display="flex",
                ),
                rx.vstack(
                    rx.text("Ver pedido", font_size="13px", font_weight="800",
                            color=TEXT_WHITE, line_height="1.15"),
                    rx.text(
                        rx.cond(
                            FoodState.cantidad_items_carrito > 0,
                            FoodState.cantidad_items_carrito.to_string() + " ítem(s) nuevos",
                            "Pedido en curso",
                        ),
                        font_size="10px", color="rgba(255,255,255,0.85)", line_height="1.15"),
                    spacing="0", align="start",
                ),
                rx.spacer(),
                rx.cond(
                    FoodState.cantidad_items_carrito > 0,
                    rx.text(FoodState.total_carrito_texto, font_size="16px",
                            font_weight="800", color=TEXT_WHITE),
                    rx.fragment(),
                ),
                rx.icon(tag="chevron_up", size=19, color=TEXT_WHITE),
                spacing="3", align="center", width="100%",
            ),
            on_click=FoodState.set_mozos_pedido_sheet_abierto(True),
            background=ACCENT, border_radius="12px", padding="12px 16px",
            box_shadow="0 6px 20px rgba(234,88,12,0.5)", cursor="pointer",
            width="100%", flex_shrink="0",
            display=rx.breakpoints(initial="block", md="none"),
        ),
        rx.fragment(),
    )


def _pedido_sheet_panel() -> rx.Component:
    """Bottom-sheet del pedido (solo móvil), SIN portal: backdrop + panel
    posicionados en absoluto dentro del dialog, que suben con translateY. Evita
    el conflicto de portales (Radix Dialog + Vaul) que rompía la hidratación."""
    abierto = FoodState.mozos_pedido_sheet_abierto
    return rx.box(
        # Backdrop
        rx.box(
            position="absolute", top="0", left="0", right="0", bottom="0",
            background="rgba(0,0,0,0.55)",
            on_click=FoodState.set_mozos_pedido_sheet_abierto(False),
            opacity=rx.cond(abierto, "1", "0"),
            transition="opacity 0.25s ease",
        ),
        # Panel deslizable
        rx.vstack(
            rx.box(width="44px", height="5px", background=DARK_600,
                   border_radius="3px", margin="2px auto 6px", cursor="pointer",
                   on_click=FoodState.set_mozos_pedido_sheet_abierto(False)),
            rx.hstack(
                rx.text(FoodState.mesa_seleccionada_label, font_size="14px",
                        font_weight="800", color=TEXT_WHITE),
                rx.spacer(),
                rx.icon(tag="x", size=18, color=TEXT_MUTED, cursor="pointer",
                        on_click=FoodState.set_mozos_pedido_sheet_abierto(False)),
                width="100%", align="center", flex_shrink="0",
            ),
            _pedido_panel_inner("50vh"),
            spacing="2", width="100%",
            position="absolute", left="0", right="0", bottom="0",
            # Altura ADAPTATIVA al contenido, con tope 85vh — idéntico al sheet de
            # Mostrador: con pocos ítems queda corto y prolijo; con muchos crece
            # hasta 85vh y la lista interna (50vh) scrollea. Botones siempre
            # visibles abajo, sin espacio vacío.
            max_height="85vh", overflow_y="auto",
            background=DARK_800, border_top=f"1px solid {DARK_700}",
            border_radius="16px 16px 0 0", padding="10px 16px 20px",
            box_shadow="0 -8px 30px rgba(0,0,0,0.5)",
            transform=rx.cond(abierto, "translateY(0)", "translateY(105%)"),
            transition="transform 0.28s cubic-bezier(0.32,0.72,0,1)",
        ),
        position="absolute", top="0", left="0", right="0", bottom="0",
        z_index="50",
        pointer_events=rx.cond(abierto, "auto", "none"),
        display=rx.breakpoints(initial="block", md="none"),
        overflow="hidden",
    )


def _modal_agregar_productos() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                # Header
                rx.hstack(
                    rx.dialog.title(
                        FoodState.mesa_seleccionada_label,
                        font_size="16px",
                        font_weight="700",
                        color=TEXT_WHITE,
                        margin="0",
                    ),
                    rx.spacer(),
                    rx.dialog.close(
                        rx.box(
                            rx.icon(tag="x", size=16, color=TEXT_MUTED),
                            cursor="pointer",
                            padding="4px",
                            border_radius="6px",
                            _hover={"background": DARK_700},
                        ),
                    ),
                    width="100%",
                    align="center",
                ),
                # Cliente vinculado a la mesa
                rx.cond(
                    FoodState.mesa_cliente_id > 0,
                    rx.hstack(
                        rx.icon(tag="user", size=13, color=SUCCESS_TEXT, flex_shrink="0"),
                        rx.text(
                            FoodState.mesa_cliente_nombre,
                            font_size="12px", font_weight="600", color="#86EFAC",
                            flex="1", min_width="0",
                        ),
                        rx.icon(
                            tag="x", size=12, color=TEXT_MUTED,
                            cursor="pointer",
                            on_click=FoodState.desvincular_cliente_mesa,
                            _hover={"color": "#EF4444"},
                        ),
                        spacing="2", align="center", width="100%",
                        background="#052E16", border="1px solid #166534",
                        border_radius="8px", padding="6px 10px",
                    ),
                    rx.hstack(
                        rx.icon(tag="user_plus", size=13, color=TEXT_MUTED, flex_shrink="0"),
                        rx.select(
                            FoodState.clientes_activos_nombres,
                            placeholder="Vincular cliente...",
                            value=FoodState.mesa_cliente_busqueda,
                            on_change=FoodState.vincular_cliente_mesa,
                            background=DARK_800,
                            color="var(--twk-slate-300)",
                            border=f"1px solid {DARK_700}",
                            border_radius="8px",
                            font_size="12px",
                            flex="1",
                        ),
                        spacing="2", align="center", width="100%",
                    ),
                ),
                # Nota: en móvil ya no hay tabs Carta/Pedido. La carta se ve siempre
                # y el pedido se abre en un bottom-sheet deslizable (_pedido_sheet_bar,
                # patrón Mostrador). En desktop se ven las 2 columnas.
                # Contenido: 2 columnas en desktop; en móvil solo la carta
                rx.flex(
                    # ─── Columna izquierda: productos ───
                    rx.vstack(
                        # Buscador
                        rx.box(
                            rx.hstack(
                                rx.icon(tag="search", size=14, color=TEXT_MUTED, flex_shrink="0"),
                                rx.input(
                                    value=FoodState.busqueda_producto_modal,
                                    on_change=FoodState.set_busqueda_producto_modal,
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
                                    FoodState.busqueda_producto_modal != "",
                                    rx.box(
                                        rx.icon(tag="x", size=12, color=TEXT_MUTED),
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
                            background=PAGE_BACKGROUND,
                            border=f"1px solid {DARK_700}",
                            border_radius="8px",
                            padding="6px 10px",
                            width="100%",
                        ),
                        # Filtros de categoría
                        rx.box(
                            rx.hstack(
                                rx.button(
                                    "Todos",
                                    on_click=FoodState.seleccionar_categoria(0),
                                    background=rx.cond(FoodState.categoria_activa_id == 0, ACCENT, "transparent"),
                                    color=rx.cond(FoodState.categoria_activa_id == 0, TEXT_WHITE, TEXT_MUTED),
                                    border=rx.cond(FoodState.categoria_activa_id == 0, f"1px solid {ACCENT}", f"1px solid {DARK_700}"),
                                    border_radius="6px",
                                    font_size="11px",
                                    font_weight=rx.cond(FoodState.categoria_activa_id == 0, "700", "500"),
                                    cursor="pointer",
                                    padding_x="8px", padding_y="4px", height="auto",
                                    _hover={"opacity": "0.85"},
                                    flex_shrink="0",
                                ),
                                rx.foreach(
                                    FoodState.categorias_activas,
                                    lambda cat: rx.button(
                                        cat.emoji + " " + cat.nombre,
                                        on_click=FoodState.seleccionar_categoria(cat.id),
                                        background=rx.cond(FoodState.categoria_activa_id == cat.id, ACCENT, "transparent"),
                                        color=rx.cond(FoodState.categoria_activa_id == cat.id, TEXT_WHITE, TEXT_MUTED),
                                        border=rx.cond(FoodState.categoria_activa_id == cat.id, f"1px solid {ACCENT}", f"1px solid {DARK_700}"),
                                        border_radius="6px",
                                        font_size="11px",
                                        cursor="pointer",
                                        padding_x="8px", padding_y="4px", height="auto",
                                        _hover={"opacity": "0.85"},
                                        flex_shrink="0",
                                    ),
                                ),
                                flex_wrap="wrap",
                                gap="4px",
                                width="100%",
                            ),
                            overflow_y="auto",
                            max_height=rx.breakpoints(initial="72px", md="200px"),
                            width="100%",
                            flex_shrink="0",
                        ),
                        # Grid de productos
                        rx.box(
                            rx.cond(
                                FoodState.productos_modal_filtrados.length() == 0,
                                rx.center(
                                    rx.vstack(
                                        rx.icon(tag="search_x", size=28, color=TEXT_MUTED),
                                        rx.text("Sin resultados", font_size="13px", color=TEXT_MUTED),
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
                            min_height="0",
                            max_height=rx.breakpoints(initial="58vh", md="45vh"),
                            width="100%",
                        ),
                        # Sección combos
                        rx.cond(
                            FoodState.combos_menu.length() > 0,
                            rx.vstack(
                                rx.hstack(
                                    rx.text("🍱", font_size="14px"),
                                    rx.text("Combos", font_size="12px", font_weight="700", color="#FDE68A"),
                                    rx.badge(
                                        FoodState.combos_menu.length().to_string(),
                                        background=WARNING_SOLID, color="#78350F",
                                        border_radius="8px", font_size="10px", padding_x="6px",
                                    ),
                                    spacing="2", align="center",
                                ),
                                rx.grid(
                                    rx.foreach(FoodState.combos_menu, _combo_card_mozos),
                                    columns=rx.breakpoints(initial="1", sm="2"),
                                    gap="6px", width="100%",
                                ),
                                spacing="2", width="100%",
                            ),
                            rx.fragment(),
                        ),
                        spacing="2",
                        flex=rx.breakpoints(initial="1", md="3"),
                        min_width="0",
                        overflow_y="auto",
                        overflow_x="hidden",
                        # La carta se ve siempre (el pedido vive en el sheet en móvil).
                        display="flex",
                    ),
                    # ─── Columna derecha: pedido (solo desktop; en móvil va al sheet) ───
                    rx.box(
                        _pedido_panel_inner("40vh"),
                        flex=rx.breakpoints(initial="1", md="2"),
                        min_width="0",
                        min_height="0",
                        overflow_y="auto",
                        background=DARK_800,
                        border=f"1px solid {DARK_700}",
                        border_radius="10px",
                        padding="12px",
                        # En móvil el pedido vive en el bottom-sheet (_pedido_sheet_bar),
                        # no en columna: aquí solo se muestra en desktop.
                        display=rx.breakpoints(initial="none", md="flex"),
                    ),
                    direction=rx.breakpoints(initial="column", md="row"),
                    gap="12px",
                    width="100%",
                    flex="1",
                    min_height="0",
                    overflow="hidden",
                ),
                # Barra "Ver pedido" → bottom-sheet — SOLO MÓVIL (patrón Mostrador)
                _pedido_sheet_bar(),
                # Bottom-sheet del pedido: overlay absoluto dentro del dialog (móvil).
                _pedido_sheet_panel(),
                spacing="3",
                width="100%",
                height=rx.breakpoints(initial="88vh", md="75vh"),
                max_height=rx.breakpoints(initial="88vh", md="75vh"),
                overflow="hidden",
                position="relative",
                padding="20px",
            ),
            background=PAGE_BACKGROUND,
            border=f"1px solid {DARK_700}",
            border_radius="16px",
            padding="0",
            max_width="900px",
            width="95vw",
            overflow="hidden",
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
                    "Mozos",
                    font_size="22px",
                    font_weight="800",
                    color=TEXT_PRIMARY,
                ),
                rx.text("Mesas y comandas en curso", font_size="13px", color=TEXT_MUTED),
                spacing="0",
            ),
            rx.spacer(),
            ayuda_trigger(),
            rx.tooltip(
                rx.button(
                    rx.icon(
                        tag=rx.cond(FoodState.sonidos_activos, "volume_2", "volume_off"),
                        size=16,
                    ),
                    on_click=FoodState.toggle_sonidos,
                    background=rx.cond(FoodState.sonidos_activos, DARK_800, PAGE_BACKGROUND),
                    color=rx.cond(FoodState.sonidos_activos, ACCENT, DARK_600),
                    border=rx.cond(FoodState.sonidos_activos, f"1px solid {DARK_700}", f"1px solid {DARK_800}"),
                    border_radius="8px",
                    cursor="pointer",
                    padding="8px",
                    _hover={"border_color": ACCENT},
                ),
                content=rx.cond(FoodState.sonidos_activos, "Silenciar avisos sonoros", "Activar avisos sonoros"),
            ),
            width="100%",
            align="center",
            flex_wrap="wrap",
            gap="8px",
        ),
        _salon_content(),
        _modal_agregar_productos(),
        _modal_transfer(),
        _modal_seleccion_mods(),
        anulacion_modal(),
        preview_ticket_modal(),
        _mozos_ayuda(),
        spacing="4",
        width="100%",
    )


@rx.page(
    route="/mozos",
    on_load=[FoodState.on_load_mozos, FoodState.start_mozos_polling,
             FoodState.cargar_clientes],
    title="TUWAYKIFOOD | Mozos",
)
def mozos_page() -> rx.Component:
    return app_shell(
        rx.cond(FoodState.pagina_cargada, _mozos_content(), loading_placeholder(dark=True)),
        page_key="mozos", dark=True,
    )
