"""Pagina de reportes — dashboard KPIs + historial filtrado."""

from __future__ import annotations

import reflex as rx

from app.components.shared import app_shell
from app.states.food_state import FoodState, TopPlatoView, VentaHistorialView

_METODOS_FILTRO = [
    ("", "Todos los métodos"),
    ("efectivo", "Efectivo"),
    ("tarjeta", "Tarjeta"),
    ("qr", "QR / Yape"),
    ("fiado", "Fiado / CC"),
]


# ─── KPI Card ────────────────────────────────────────────────────────────────

def _kpi_card(label: str, value, icon: str, accent: str, bg: str, border: str) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.box(
                    rx.icon(tag=icon, size=16, color=accent),
                    width="32px",
                    height="32px",
                    border_radius="8px",
                    background=bg,
                    border=f"1px solid {border}",
                    display="flex",
                    align_items="center",
                    justify_content="center",
                    flex_shrink="0",
                ),
                rx.spacer(),
            ),
            rx.text(value, font_size="22px", font_weight="800", color="#0F172A", line_height="1"),
            rx.text(label, font_size="11px", font_weight="600", color="#64748B",
                    text_transform="uppercase", letter_spacing="0.06em"),
            spacing="2",
            align="start",
            width="100%",
        ),
        background="#FFFFFF",
        border=f"1px solid {border}",
        border_radius="12px",
        padding="14px 16px",
        box_shadow="0 1px 3px rgba(0,0,0,0.06)",
    )


# ─── Top platos ───────────────────────────────────────────────────────────────

def _top_plato_row(plato: TopPlatoView, idx: int) -> rx.Component:
    return rx.hstack(
        rx.box(
            rx.text(
                (idx + 1).to_string(),
                font_size="11px", font_weight="700", color="#EA580C",
            ),
            width="22px",
            height="22px",
            border_radius="full",
            background="#FFF7ED",
            border="1px solid #FED7AA",
            display="flex",
            align_items="center",
            justify_content="center",
            flex_shrink="0",
        ),
        rx.text(plato.nombre, font_size="13px", color="#334155", flex="1",
                text_overflow="ellipsis", overflow="hidden", white_space="nowrap"),
        rx.badge(
            plato.cantidad.to_string() + " uds",
            background="#FFF7ED",
            color="#9A3412",
            border_radius="5px",
            font_size="10px",
            font_weight="700",
            padding="2px 6px",
            flex_shrink="0",
        ),
        rx.text(plato.total_texto, font_size="13px", font_weight="700",
                color="#15803D", min_width="72px", text_align="right", flex_shrink="0"),
        width="100%",
        align="center",
        padding="8px 10px",
        background="#FFFFFF",
        border_radius="8px",
        border="1px solid #F1F5F9",
        gap="8px",
        _hover={"background": "#F8FAFC"},
    )


# ─── Método badge ─────────────────────────────────────────────────────────────

def _metodo_badge(metodo: str) -> rx.Component:
    return rx.badge(
        metodo,
        background=rx.cond(
            metodo == "efectivo", "#DCFCE7",
            rx.cond(metodo == "tarjeta", "#DBEAFE",
            rx.cond(metodo == "qr", "#FEF3C7",
            rx.cond(metodo == "fiado", "#FFEDD5", "#F1F5F9"))),
        ),
        color=rx.cond(
            metodo == "efectivo", "#15803D",
            rx.cond(metodo == "tarjeta", "#1D4ED8",
            rx.cond(metodo == "qr", "#B45309",
            rx.cond(metodo == "fiado", "#C2410C", "#64748B"))),
        ),
        border_radius="5px",
        font_size="10px",
        font_weight="700",
        padding="2px 6px",
    )


# ─── Fila historial ───────────────────────────────────────────────────────────

def _venta_row(venta: VentaHistorialView) -> rx.Component:
    return rx.hstack(
        rx.text(
            "#" + venta.pedido_id.to_string(),
            font_size="11px",
            color="#94A3B8",
            min_width="36px",
            flex_shrink="0",
        ),
        rx.text(venta.mesa_label, font_size="13px", color="#334155", flex="1",
                min_width="0", text_overflow="ellipsis", overflow="hidden", white_space="nowrap"),
        _metodo_badge(venta.metodo_pago),
        rx.text(
            venta.mozo_nombre,
            font_size="12px", color="#64748B",
            min_width="72px", text_align="center", flex_shrink="0",
            display=rx.breakpoints(initial="none", sm="block"),
        ),
        rx.text(
            venta.cajero_nombre,
            font_size="12px", color="#64748B",
            min_width="72px", text_align="center", flex_shrink="0",
            display=rx.breakpoints(initial="none", lg="block"),
        ),
        rx.vstack(
            rx.text(venta.total_con_propina_texto, font_size="13px", font_weight="700",
                    color="#15803D", text_align="right"),
            rx.cond(
                venta.propina > 0,
                rx.text("+ " + venta.propina_texto + " prop.",
                        font_size="10px", color="#B45309", text_align="right"),
                rx.fragment(),
            ),
            spacing="0",
            align="end",
            min_width="80px",
            flex_shrink="0",
        ),
        width="100%",
        align="center",
        padding="10px 12px",
        background="#FFFFFF",
        border_radius="8px",
        border="1px solid #E2E8F0",
        gap="8px",
        _hover={"background": "#F8FAFC"},
    )


# ─── Filtros ──────────────────────────────────────────────────────────────────

def _filtros_bar() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.icon(tag="filter", size=14, color="#64748B"),
                rx.text("Filtros", font_size="13px", font_weight="700", color="#334155"),
                rx.cond(
                    FoodState.historial_filtro_activo,
                    rx.badge(
                        "Activo",
                        background="#FFF7ED",
                        color="#EA580C",
                        border_radius="5px",
                        font_size="10px",
                        font_weight="700",
                        padding="2px 6px",
                    ),
                    rx.fragment(),
                ),
                spacing="2",
                align="center",
            ),
            rx.grid(
                # Fecha desde
                rx.vstack(
                    rx.text("Desde", font_size="11px", font_weight="600", color="#64748B"),
                    rx.input(
                        value=FoodState.historial_filtro_fecha_desde,
                        on_change=FoodState.set_historial_filtro_fecha_desde,
                        type="date",
                        background="#FFFFFF",
                        border="1px solid #E2E8F0",
                        color="#0F172A",
                        border_radius="8px",
                        padding_x="10px",
                        padding_y="7px",
                        font_size="13px",
                        width="100%",
                        _focus={"border": "1px solid #EA580C"},
                    ),
                    spacing="1",
                    width="100%",
                ),
                # Fecha hasta
                rx.vstack(
                    rx.text("Hasta", font_size="11px", font_weight="600", color="#64748B"),
                    rx.input(
                        value=FoodState.historial_filtro_fecha_hasta,
                        on_change=FoodState.set_historial_filtro_fecha_hasta,
                        type="date",
                        background="#FFFFFF",
                        border="1px solid #E2E8F0",
                        color="#0F172A",
                        border_radius="8px",
                        padding_x="10px",
                        padding_y="7px",
                        font_size="13px",
                        width="100%",
                        _focus={"border": "1px solid #EA580C"},
                    ),
                    spacing="1",
                    width="100%",
                ),
                # Método de pago
                rx.vstack(
                    rx.text("Método", font_size="11px", font_weight="600", color="#64748B"),
                    rx.select(
                        [label for _, label in _METODOS_FILTRO],
                        value=rx.cond(
                            FoodState.historial_filtro_metodo == "", "Todos los métodos",
                            rx.cond(
                                FoodState.historial_filtro_metodo == "efectivo", "Efectivo",
                                rx.cond(
                                    FoodState.historial_filtro_metodo == "tarjeta", "Tarjeta",
                                    rx.cond(
                                        FoodState.historial_filtro_metodo == "qr", "QR / Yape",
                                        "Fiado / CC",
                                    ),
                                ),
                            ),
                        ),
                        on_change=lambda v: FoodState.set_historial_filtro_metodo(
                            rx.cond(v == "Todos los métodos", "",
                            rx.cond(v == "Efectivo", "efectivo",
                            rx.cond(v == "Tarjeta", "tarjeta",
                            rx.cond(v == "QR / Yape", "qr", "fiado"))))
                        ),
                        background="#FFFFFF",
                        border="1px solid #E2E8F0",
                        color="#0F172A",
                        border_radius="8px",
                        font_size="13px",
                        width="100%",
                    ),
                    spacing="1",
                    width="100%",
                ),
                columns=rx.breakpoints(initial="1", sm="3"),
                gap="10px",
                width="100%",
            ),
            # Botones acción
            rx.hstack(
                rx.button(
                    rx.hstack(
                        rx.icon(tag="search", size=13),
                        rx.text("Buscar", font_size="13px", font_weight="600"),
                        spacing="1", align="center",
                    ),
                    on_click=FoodState.aplicar_filtros_historial,
                    background="#EA580C",
                    color="#FFFFFF",
                    border_radius="8px",
                    padding_x="14px",
                    padding_y="8px",
                    cursor="pointer",
                    _hover={"background": "#C2410C"},
                ),
                rx.cond(
                    FoodState.historial_filtro_activo,
                    rx.button(
                        rx.hstack(
                            rx.icon(tag="x", size=13),
                            rx.text("Limpiar", font_size="13px", font_weight="600"),
                            spacing="1", align="center",
                        ),
                        on_click=FoodState.limpiar_filtros_historial,
                        background="#F1F5F9",
                        color="#64748B",
                        border="1px solid #E2E8F0",
                        border_radius="8px",
                        padding_x="14px",
                        padding_y="8px",
                        cursor="pointer",
                        _hover={"opacity": "0.85"},
                    ),
                    rx.fragment(),
                ),
                spacing="2",
            ),
            spacing="3",
            width="100%",
        ),
        background="#F8FAFC",
        border="1px solid #E2E8F0",
        border_radius="10px",
        padding="12px 14px",
        width="100%",
    )


# ─── Cabecera historial ───────────────────────────────────────────────────────

def _historial_header() -> rx.Component:
    return rx.hstack(
        rx.text("#", font_size="11px", color="#94A3B8", min_width="36px", flex_shrink="0"),
        rx.text("Mesa / Pedido", font_size="11px", color="#94A3B8", flex="1"),
        rx.text("Método", font_size="11px", color="#94A3B8", min_width="60px", flex_shrink="0"),
        rx.text(
            "Mozo", font_size="11px", color="#94A3B8",
            min_width="72px", text_align="center", flex_shrink="0",
            display=rx.breakpoints(initial="none", sm="block"),
        ),
        rx.text(
            "Cajero", font_size="11px", color="#94A3B8",
            min_width="72px", text_align="center", flex_shrink="0",
            display=rx.breakpoints(initial="none", lg="block"),
        ),
        rx.text("Total", font_size="11px", color="#94A3B8",
                min_width="80px", text_align="right", flex_shrink="0"),
        width="100%",
        padding_x="12px",
        gap="8px",
    )


# ─── Contenido principal ─────────────────────────────────────────────────────

def _reportes_content() -> rx.Component:
    return rx.vstack(
        # Header
        rx.hstack(
            rx.vstack(
                rx.text("Reportes", font_size="22px", font_weight="800", color="#0F172A"),
                rx.text("Dashboard y ventas del día", font_size="13px", color="#64748B"),
                spacing="0",
            ),
            rx.spacer(),
            rx.button(
                rx.hstack(
                    rx.icon(tag="refresh_cw", size=13),
                    rx.text("Actualizar", font_size="13px", font_weight="600"),
                    spacing="1", align="center",
                ),
                on_click=[FoodState.cargar_dashboard, FoodState.cargar_historial_ventas],
                background="#FFF7ED",
                color="#EA580C",
                border="1px solid #FED7AA",
                border_radius="8px",
                font_size="13px",
                cursor="pointer",
                _hover={"opacity": "0.85"},
            ),
            width="100%",
            align="center",
        ),

        # ── KPI cards ────────────────────────────────────────────────────────
        rx.grid(
            _kpi_card(
                "Ventas hoy",
                FoodState.dashboard_ventas_hoy_texto,
                "trending_up", "#15803D", "#F0FDF4", "#BBF7D0",
            ),
            _kpi_card(
                "Pedidos cobrados",
                FoodState.dashboard_pedidos_hoy.to_string(),
                "receipt_text", "#1D4ED8", "#EFF6FF", "#BFDBFE",
            ),
            _kpi_card(
                "Mesas ocupadas",
                FoodState.dashboard_mesas_ocupadas.to_string(),
                "layout_grid", "#B45309", "#FFFBEB", "#FDE68A",
            ),
            _kpi_card(
                "Propinas hoy",
                FoodState.dashboard_propina_hoy_texto,
                "heart", "#9A3412", "#FFF7ED", "#FED7AA",
            ),
            columns=rx.breakpoints(initial="2", md="4"),
            gap=rx.breakpoints(initial="10px", md="14px"),
            width="100%",
        ),

        # ── Top platos ────────────────────────────────────────────────────────
        rx.cond(
            FoodState.dashboard_top_platos.length() > 0,
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.icon(tag="star", size=14, color="#EA580C"),
                        rx.text("Top platos hoy", font_size="13px", font_weight="700", color="#334155"),
                        spacing="2", align="center",
                    ),
                    rx.foreach(FoodState.dashboard_top_platos, lambda plato, i: _top_plato_row(plato, i)),
                    spacing="2",
                    width="100%",
                ),
                background="#F8FAFC",
                border="1px solid #E2E8F0",
                border_radius="10px",
                padding="12px 14px",
                width="100%",
            ),
            rx.fragment(),
        ),

        # ── Historial con filtros ─────────────────────────────────────────────
        rx.vstack(
            rx.hstack(
                rx.text("Historial de ventas", font_size="15px", font_weight="700", color="#0F172A"),
                rx.cond(
                    FoodState.historial_ventas.length() > 0,
                    rx.badge(
                        FoodState.historial_ventas.length().to_string() + " registros",
                        background="#F1F5F9",
                        color="#64748B",
                        border_radius="5px",
                        font_size="10px",
                        font_weight="600",
                        padding="2px 6px",
                    ),
                    rx.fragment(),
                ),
                spacing="2",
                align="center",
            ),
            _filtros_bar(),
            rx.cond(
                FoodState.historial_ventas.length() == 0,
                rx.center(
                    rx.vstack(
                        rx.icon(tag="inbox", size=32, color="#CBD5E1"),
                        rx.text(
                            rx.cond(
                                FoodState.historial_filtro_activo,
                                "Sin resultados para los filtros aplicados.",
                                "Sin ventas registradas.",
                            ),
                            font_size="14px", color="#94A3B8", text_align="center",
                        ),
                        spacing="2",
                        align="center",
                    ),
                    padding_y="40px",
                    width="100%",
                ),
                rx.vstack(
                    rx.box(
                        _historial_header(),
                        position="sticky",
                        top="0",
                        z_index="10",
                        background="#F8FAFC",
                        border_bottom="1px solid #E2E8F0",
                        padding_y="4px",
                    ),
                    rx.foreach(FoodState.historial_ventas, _venta_row),
                    # Controles de paginación
                    rx.hstack(
                        rx.button(
                            rx.icon(tag="chevron_left", size=14),
                            on_click=FoodState.historial_pagina_anterior,
                            background="#F1F5F9",
                            color="#64748B",
                            border="1px solid #E2E8F0",
                            border_radius="7px",
                            padding_x="10px",
                            padding_y="6px",
                            cursor="pointer",
                            disabled=~FoodState.historial_tiene_anterior,
                            opacity=rx.cond(FoodState.historial_tiene_anterior, "1", "0.4"),
                            _hover={"background": "#E2E8F0"},
                        ),
                        rx.text(
                            FoodState.historial_pagina_label,
                            font_size="12px",
                            color="#64748B",
                            flex="1",
                            text_align="center",
                        ),
                        rx.button(
                            rx.icon(tag="chevron_right", size=14),
                            on_click=FoodState.historial_pagina_siguiente,
                            background="#F1F5F9",
                            color="#64748B",
                            border="1px solid #E2E8F0",
                            border_radius="7px",
                            padding_x="10px",
                            padding_y="6px",
                            cursor="pointer",
                            disabled=~FoodState.historial_tiene_siguiente,
                            opacity=rx.cond(FoodState.historial_tiene_siguiente, "1", "0.4"),
                            _hover={"background": "#E2E8F0"},
                        ),
                        width="100%",
                        align="center",
                        padding_y="12px",
                    ),
                    spacing="1",
                    width="100%",
                ),
            ),
            spacing="3",
            width="100%",
        ),

        spacing="5",
        width="100%",
    )


@rx.page(route="/reportes", on_load=FoodState.on_load_reportes, title="TUWAYKIFOOD | Reportes")
def reportes_page() -> rx.Component:
    return app_shell(_reportes_content(), page_key="reportes")
