"""Pagina de reportes — dashboard KPIs + historial filtrado."""

from __future__ import annotations

import reflex as rx

from app.components.shared import anulacion_modal, app_shell, loading_placeholder
from app.states.food_state import (
    AnulacionView,
    DescuentoRankView,
    FoodState,
    MermaCategoriaView,
    MermaInsumoView,
    PylLineView,
    TopPlatoView,
    VentaDetalleItemView,
    VentaHistorialView,
)

_METODOS_FILTRO = [
    ("", "Todos los métodos"),
    ("efectivo", "Efectivo"),
    ("tarjeta", "Tarjeta"),
    ("qr", "QR / Yape"),
    ("fiado", "Fiado / CC"),
    ("mixto", "Mixto"),
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

def _mozo_row(m) -> rx.Component:
    return rx.hstack(
        rx.text(m.nombre, font_size="13px", font_weight="600", color="#0F172A", flex="1"),
        rx.text(m.pedidos.to_string() + " ped.", font_size="12px", color="#64748B",
                min_width="52px", text_align="right"),
        rx.vstack(
            rx.text(m.total_texto, font_size="13px", font_weight="800",
                    color="#15803D", text_align="right"),
            rx.cond(
                m.propinas_texto != "",
                rx.text("prop. " + m.propinas_texto, font_size="10px",
                        color="#B45309", text_align="right"),
                rx.fragment(),
            ),
            spacing="0", align="end", min_width="90px",
        ),
        width="100%", align="center", gap="8px",
        padding="8px 4px", border_bottom="1px solid #F1F5F9",
    )


def _ventas_hora_chart() -> rx.Component:
    return rx.recharts.responsive_container(
        rx.recharts.bar_chart(
            rx.recharts.cartesian_grid(stroke_dasharray="3 3", stroke="#E2E8F0"),
            rx.recharts.x_axis(
                data_key="hora_label", font_size=11, tick_line=False,
                axis_line=False, stroke="#94A3B8",
            ),
            rx.recharts.y_axis(
                font_size=11, tick_line=False, axis_line=False,
                stroke="#94A3B8", width=60,
            ),
            rx.recharts.graphing_tooltip(
                content_style={"fontSize": "12px", "borderRadius": "8px"},
            ),
            rx.recharts.bar(
                data_key="total", fill="#EA580C", radius=[4, 4, 0, 0],
                name="Total (S/)",
            ),
            rx.recharts.bar(
                data_key="pedidos", fill="#FB923C", radius=[4, 4, 0, 0],
                name="Pedidos",
            ),
            data=FoodState.reporte_horas_chart,
            margin={"top": 4, "right": 4, "left": 0, "bottom": 0},
        ),
        width="100%", height=220,
    )


def _ventas_mozo_chart() -> rx.Component:
    return rx.recharts.responsive_container(
        rx.recharts.bar_chart(
            rx.recharts.cartesian_grid(stroke_dasharray="3 3", stroke="#E2E8F0"),
            rx.recharts.x_axis(
                data_key="nombre", font_size=10, tick_line=False,
                axis_line=False, stroke="#94A3B8", interval=0,
                angle=-25, text_anchor="end", height=50,
            ),
            rx.recharts.y_axis(
                font_size=11, tick_line=False, axis_line=False,
                stroke="#94A3B8", width=60,
            ),
            rx.recharts.graphing_tooltip(
                content_style={"fontSize": "12px", "borderRadius": "8px"},
            ),
            rx.recharts.bar(
                data_key="total", fill="#EA580C", radius=[4, 4, 0, 0],
                name="Total (S/)",
            ),
            rx.recharts.bar(
                data_key="propinas", fill="#F59E0B", radius=[4, 4, 0, 0],
                name="Propinas (S/)",
            ),
            data=FoodState.reporte_mozos_chart,
            margin={"top": 4, "right": 4, "left": 0, "bottom": 0},
        ),
        width="100%", height=220,
    )


def _margen_row(p) -> rx.Component:
    return rx.hstack(
        rx.text(p.nombre, font_size="13px", font_weight="600", color="#0F172A", flex="1",
                min_width="0", overflow="hidden", text_overflow="ellipsis", white_space="nowrap"),
        rx.text("P " + p.precio_texto, font_size="12px", color="#64748B",
                min_width="86px", text_align="right",
                display=rx.breakpoints(initial="none", sm="block")),
        rx.text("C " + p.costo_texto, font_size="12px", color="#64748B",
                min_width="86px", text_align="right",
                display=rx.breakpoints(initial="none", sm="block")),
        rx.text(p.margen_texto, font_size="13px", font_weight="700", color="#334155",
                min_width="86px", text_align="right"),
        rx.hstack(
            rx.badge(
                p.margen_pct_texto,
                background="#FFFFFF", color=p.color,
                border="1.5px solid", border_color=p.color,
                border_radius="8px", font_size="11px", font_weight="800",
            ),
            rx.cond(
                p.costo_completo,
                rx.fragment(),
                rx.text("costos incompletos", font_size="10px", color="#94A3B8"),
            ),
            spacing="1", align="center", min_width="70px", justify="end",
        ),
        width="100%", align="center", gap="8px",
        padding="8px 4px", border_bottom="1px solid #F1F5F9",
    )


def _venta_row(venta: VentaHistorialView) -> rx.Component:
    return rx.hstack(
        rx.text(
            "#" + venta.pedido_id.to_string(),
            font_size="11px",
            color="#94A3B8",
            min_width="36px",
            flex_shrink="0",
        ),
        rx.vstack(
            rx.text(venta.mesa_label, font_size="13px", color="#334155", width="100%",
                    text_overflow="ellipsis", overflow="hidden", white_space="nowrap"),
            rx.cond(
                venta.anulada,
                rx.text(venta.anulacion_texto, font_size="10px", color="#B91C1C",
                        width="100%", text_overflow="ellipsis", overflow="hidden",
                        white_space="nowrap"),
                rx.fragment(),
            ),
            spacing="0", align="start", flex="1", min_width="0",
        ),
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
            rx.cond(
                venta.anulada,
                rx.badge(
                    "ANULADA", background="#FEE2E2", color="#B91C1C",
                    border_radius="6px", font_size="10px", font_weight="800",
                ),
                rx.text(venta.total_con_propina_texto, font_size="13px", font_weight="700",
                        color="#15803D", text_align="right"),
            ),
            rx.cond(
                venta.anulada,
                rx.text(venta.total_con_propina_texto, font_size="10px", color="#94A3B8",
                        text_decoration="line-through", text_align="right"),
                rx.cond(
                    venta.propina > 0,
                    rx.text("+ " + venta.propina_texto + " prop.",
                            font_size="10px", color="#B45309", text_align="right"),
                    rx.fragment(),
                ),
            ),
            spacing="0",
            align="end",
            min_width="80px",
            flex_shrink="0",
        ),
        rx.cond(
            venta.anulada,
            rx.fragment(),
            rx.button(
                rx.icon(tag="ban", size=15),
                on_click=FoodState.abrir_anulacion_venta(venta.pedido_id).stop_propagation,
                background="transparent", color="#CBD5E1",
                border="none", padding="2px", cursor="pointer",
                _hover={"color": "#DC2626"},
                flex_shrink="0",
                title="Anular venta",
            ),
        ),
        width="100%",
        align="center",
        padding="10px 12px",
        background="#FFFFFF",
        border_radius="8px",
        border="1px solid #E2E8F0",
        gap="8px",
        cursor="pointer",
        opacity=rx.cond(venta.anulada, "0.75", "1"),
        on_click=FoodState.abrir_detalle_venta(venta.pedido_id),
        _hover={"background": "#F8FAFC"},
    )


def _venta_detalle_item_row(item: VentaDetalleItemView) -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.text(item.cantidad.to_string() + "x", font_size="12px",
                     color="#94A3B8", min_width="26px", flex_shrink="0"),
            rx.text(item.nombre, font_size="13px", color="#0F172A", flex="1"),
            rx.text(item.subtotal_texto, font_size="13px", font_weight="700",
                     color="#0F172A", flex_shrink="0"),
            width="100%", align="center", gap="8px",
        ),
        rx.cond(
            item.notas != "",
            rx.text("Nota: " + item.notas, font_size="11px", color="#94A3B8",
                     padding_left="34px"),
            rx.fragment(),
        ),
        spacing="1", width="100%", padding="8px 0",
        border_bottom="1px solid #F1F5F9",
    )


def _venta_detalle_modal() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.hstack(
                    rx.vstack(
                        rx.text("Pedido #" + FoodState.venta_detalle_pedido_id.to_string(),
                                font_size="16px", font_weight="800", color="#0F172A"),
                        rx.text(FoodState.venta_detalle_mesa_label, font_size="13px", color="#64748B"),
                        spacing="0",
                    ),
                    rx.spacer(),
                    rx.dialog.close(
                        rx.icon(tag="x", size=16, color="#64748B", cursor="pointer"),
                    ),
                    width="100%", align="start",
                ),
                rx.hstack(
                    _metodo_badge(FoodState.venta_detalle_metodo),
                    rx.text("Mozo: " + FoodState.venta_detalle_mozo, font_size="12px", color="#64748B"),
                    rx.text("Cajero: " + FoodState.venta_detalle_cajero, font_size="12px", color="#64748B"),
                    spacing="3", align="center", wrap="wrap",
                ),
                rx.box(height="1px", width="100%", background="#E2E8F0"),
                rx.vstack(
                    rx.foreach(FoodState.venta_detalle_items, _venta_detalle_item_row),
                    spacing="0", width="100%", max_height="280px", overflow_y="auto",
                ),
                rx.box(height="1px", width="100%", background="#E2E8F0"),
                rx.hstack(
                    rx.vstack(
                        rx.text("Total", font_size="14px", font_weight="700", color="#0F172A"),
                        rx.cond(
                            FoodState.venta_detalle_propina_texto != "",
                            rx.text("Incluye propina " + FoodState.venta_detalle_propina_texto,
                                     font_size="11px", color="#B45309"),
                            rx.fragment(),
                        ),
                        spacing="0",
                    ),
                    rx.spacer(),
                    rx.text(FoodState.venta_detalle_total_texto, font_size="18px",
                             font_weight="800", color="#15803D"),
                    width="100%", align="center",
                ),
                spacing="3", width="100%",
            ),
            class_name="light",
            max_width="420px",
        ),
        open=FoodState.venta_detalle_visible,
        on_open_change=FoodState.set_venta_detalle_visible,
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
                                        rx.cond(
                                            FoodState.historial_filtro_metodo == "fiado", "Fiado / CC",
                                            "Mixto",
                                        ),
                                    ),
                                ),
                            ),
                        ),
                        on_change=lambda v: FoodState.set_historial_filtro_metodo(
                            rx.cond(v == "Todos los métodos", "",
                            rx.cond(v == "Efectivo", "efectivo",
                            rx.cond(v == "Tarjeta", "tarjeta",
                            rx.cond(v == "QR / Yape", "qr",
                            rx.cond(v == "Fiado / CC", "fiado", "mixto")))))
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
                    on_click=FoodState.buscar_historial_manual,
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


# ─── P&L mensual (ADM-01) ────────────────────────────────────────────────────

_MESES = [
    ("1", "Enero"), ("2", "Febrero"), ("3", "Marzo"), ("4", "Abril"),
    ("5", "Mayo"), ("6", "Junio"), ("7", "Julio"), ("8", "Agosto"),
    ("9", "Septiembre"), ("10", "Octubre"), ("11", "Noviembre"), ("12", "Diciembre"),
]


def _pyl_line_row(line: PylLineView) -> rx.Component:
    return rx.hstack(
        rx.text(
            line.concepto,
            font_size="13px",
            font_weight=rx.cond(line.es_total, "800", "500"),
            color=rx.cond(line.es_total, "#0F172A", "#475569"),
            flex="1",
        ),
        rx.hstack(
            rx.text(
                line.valor_texto,
                font_size=rx.cond(line.es_total, "15px", "13px"),
                font_weight=rx.cond(line.es_total, "800", "600"),
                color=rx.cond(
                    line.es_negativo, "#DC2626",
                    rx.cond(line.es_total, "#0F172A", "#334155"),
                ),
                min_width="100px",
                text_align="right",
            ),
            rx.cond(
                line.margen_pct_texto != "",
                rx.badge(
                    line.margen_pct_texto,
                    background=rx.cond(line.es_negativo, "#FEE2E2", "#DCFCE7"),
                    color=rx.cond(line.es_negativo, "#DC2626", "#15803D"),
                    border_radius="6px",
                    font_size="11px",
                    font_weight="800",
                    padding="2px 8px",
                ),
                rx.fragment(),
            ),
            spacing="2", align="center",
        ),
        width="100%",
        align="center",
        padding="8px 4px",
        border_top=rx.cond(line.es_total, "2px solid #E2E8F0", "1px solid #F1F5F9"),
    )


def _pyl_section() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.icon(tag="file_text", size=14, color="#EA580C"),
                rx.text("Estado de resultados (P&L)", font_size="13px",
                        font_weight="700", color="#334155"),
                rx.spacer(),
                rx.hstack(
                    rx.select(
                        [label for _, label in _MESES],
                        value=rx.cond(
                            FoodState.pyl_mes == 1, "Enero",
                            rx.cond(FoodState.pyl_mes == 2, "Febrero",
                            rx.cond(FoodState.pyl_mes == 3, "Marzo",
                            rx.cond(FoodState.pyl_mes == 4, "Abril",
                            rx.cond(FoodState.pyl_mes == 5, "Mayo",
                            rx.cond(FoodState.pyl_mes == 6, "Junio",
                            rx.cond(FoodState.pyl_mes == 7, "Julio",
                            rx.cond(FoodState.pyl_mes == 8, "Agosto",
                            rx.cond(FoodState.pyl_mes == 9, "Septiembre",
                            rx.cond(FoodState.pyl_mes == 10, "Octubre",
                            rx.cond(FoodState.pyl_mes == 11, "Noviembre",
                            "Diciembre",
                            ))))))))))),
                        on_change=lambda v: FoodState.set_pyl_mes(
                            rx.cond(v == "Enero", "1",
                            rx.cond(v == "Febrero", "2",
                            rx.cond(v == "Marzo", "3",
                            rx.cond(v == "Abril", "4",
                            rx.cond(v == "Mayo", "5",
                            rx.cond(v == "Junio", "6",
                            rx.cond(v == "Julio", "7",
                            rx.cond(v == "Agosto", "8",
                            rx.cond(v == "Septiembre", "9",
                            rx.cond(v == "Octubre", "10",
                            rx.cond(v == "Noviembre", "11",
                            "12",
                            )))))))))))
                        ),
                        background="#FFFFFF",
                        border="1px solid #E2E8F0",
                        border_radius="8px",
                        font_size="12px",
                        width="130px",
                    ),
                    rx.input(
                        value=FoodState.pyl_anio.to_string(),
                        on_change=FoodState.set_pyl_anio,
                        type="number",
                        background="#FFFFFF",
                        border="1px solid #E2E8F0",
                        border_radius="8px",
                        font_size="12px",
                        width="80px",
                        padding_x="8px",
                    ),
                    rx.button(
                        rx.icon(tag="refresh_cw", size=13),
                        on_click=FoodState.actualizar_pyl,
                        background="#FFF7ED",
                        color="#EA580C",
                        border="1px solid #FED7AA",
                        border_radius="8px",
                        padding="6px 10px",
                        cursor="pointer",
                        _hover={"opacity": "0.85"},
                    ),
                    spacing="2", align="center",
                ),
                spacing="2", align="center", width="100%", wrap="wrap",
            ),
            rx.cond(
                FoodState.pyl_lineas.length() > 0,
                rx.vstack(
                    rx.foreach(FoodState.pyl_lineas, _pyl_line_row),
                    spacing="0", width="100%",
                ),
                rx.text("Sin datos para el mes seleccionado.", font_size="12px", color="#94A3B8"),
            ),
            spacing="3", width="100%",
        ),
        background="#F8FAFC", border="1px solid #E2E8F0",
        border_radius="10px", padding="12px 14px", width="100%",
    )


# ─── Descuentos y anulaciones (ADM-02) ──────────────────────────────────────


def _descuento_rank_row(d: DescuentoRankView) -> rx.Component:
    return rx.hstack(
        rx.text(d.cajero, font_size="13px", font_weight="600", color="#0F172A", flex="1"),
        rx.text(d.pedidos.to_string() + " ped.", font_size="12px", color="#64748B",
                min_width="52px", text_align="right"),
        rx.text(d.total_descuento_texto, font_size="13px", font_weight="700",
                color="#DC2626", min_width="86px", text_align="right"),
        rx.badge(
            d.pct_descuento_texto,
            background="#FEE2E2", color="#B91C1C",
            border_radius="6px", font_size="11px", font_weight="800",
            padding="2px 6px",
        ),
        width="100%", align="center", gap="8px",
        padding="8px 4px", border_bottom="1px solid #F1F5F9",
    )


def _anulacion_row(a: AnulacionView) -> rx.Component:
    return rx.hstack(
        rx.text("#" + a.pedido_id.to_string(), font_size="11px", color="#94A3B8",
                min_width="36px", flex_shrink="0"),
        rx.vstack(
            rx.text(a.motivo, font_size="13px", color="#334155", width="100%",
                    text_overflow="ellipsis", overflow="hidden", white_space="nowrap"),
            rx.text(
                a.cancelado_por + " — " + a.cancelado_en_texto,
                font_size="10px", color="#94A3B8",
            ),
            spacing="0", flex="1", min_width="0",
        ),
        rx.text(a.total_texto, font_size="13px", font_weight="700", color="#DC2626",
                min_width="80px", text_align="right", flex_shrink="0"),
        width="100%", align="center", gap="8px",
        padding="8px 4px", border_bottom="1px solid #F1F5F9",
    )


def _descuentos_anulaciones_section() -> rx.Component:
    return rx.flex(
        # Descuentos por cajero
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.icon(tag="percent", size=14, color="#DC2626"),
                    rx.text("Descuentos por cajero", font_size="13px",
                            font_weight="700", color="#334155"),
                    rx.spacer(),
                    rx.badge(
                        FoodState.descuentos_total_texto,
                        background="#FEE2E2", color="#B91C1C",
                        border_radius="6px", font_size="11px", font_weight="800",
                        padding="2px 8px",
                    ),
                    spacing="2", align="center", width="100%",
                ),
                rx.cond(
                    FoodState.descuentos_rank.length() > 0,
                    rx.vstack(
                        rx.foreach(FoodState.descuentos_rank, _descuento_rank_row),
                        spacing="0", width="100%",
                    ),
                    rx.text("Sin descuentos en el período.", font_size="12px", color="#94A3B8"),
                ),
                spacing="3", width="100%",
            ),
            background="#F8FAFC", border="1px solid #E2E8F0",
            border_radius="10px", padding="12px 14px", flex="1", min_width="260px",
        ),
        # Anulaciones
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.icon(tag="ban", size=14, color="#DC2626"),
                    rx.text("Anulaciones", font_size="13px",
                            font_weight="700", color="#334155"),
                    rx.spacer(),
                    rx.badge(
                        FoodState.anulaciones_total_texto,
                        background="#FEE2E2", color="#B91C1C",
                        border_radius="6px", font_size="11px", font_weight="800",
                        padding="2px 8px",
                    ),
                    spacing="2", align="center", width="100%",
                ),
                rx.cond(
                    FoodState.anulaciones_lista.length() > 0,
                    rx.vstack(
                        rx.foreach(FoodState.anulaciones_lista, _anulacion_row),
                        spacing="0", width="100%", max_height="300px", overflow_y="auto",
                    ),
                    rx.text("Sin anulaciones en el período.", font_size="12px", color="#94A3B8"),
                ),
                spacing="3", width="100%",
            ),
            background="#F8FAFC", border="1px solid #E2E8F0",
            border_radius="10px", padding="12px 14px", flex="1", min_width="260px",
        ),
        gap="12px", width="100%",
        direction=rx.breakpoints(initial="column", md="row"),
    )


# ─── Mermas valorizado (ADM-03) ─────────────────────────────────────────────


def _merma_cat_row(c: MermaCategoriaView) -> rx.Component:
    return rx.hstack(
        rx.text(c.categoria, font_size="13px", font_weight="600", color="#0F172A", flex="1"),
        rx.text(c.registros.to_string() + " reg.", font_size="12px", color="#64748B",
                min_width="52px", text_align="right"),
        rx.text(c.valor_texto, font_size="13px", font_weight="700", color="#DC2626",
                min_width="86px", text_align="right"),
        width="100%", align="center", gap="8px",
        padding="8px 4px", border_bottom="1px solid #F1F5F9",
    )


def _merma_insumo_row(i: MermaInsumoView) -> rx.Component:
    return rx.hstack(
        rx.text(i.nombre, font_size="13px", font_weight="600", color="#0F172A", flex="1",
                min_width="0", overflow="hidden", text_overflow="ellipsis", white_space="nowrap"),
        rx.text(i.cantidad_texto + " " + i.unidad, font_size="12px", color="#64748B",
                min_width="80px", text_align="right"),
        rx.text(i.valor_texto, font_size="13px", font_weight="700", color="#DC2626",
                min_width="86px", text_align="right"),
        width="100%", align="center", gap="8px",
        padding="8px 4px", border_bottom="1px solid #F1F5F9",
    )


def _mermas_section() -> rx.Component:
    return rx.flex(
        # Por categoría
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.icon(tag="trash_2", size=14, color="#B45309"),
                    rx.text("Mermas por categoría", font_size="13px",
                            font_weight="700", color="#334155"),
                    rx.spacer(),
                    rx.badge(
                        FoodState.mermas_total_texto,
                        background="#FEF3C7", color="#92400E",
                        border_radius="6px", font_size="11px", font_weight="800",
                        padding="2px 8px",
                    ),
                    spacing="2", align="center", width="100%",
                ),
                rx.cond(
                    FoodState.mermas_por_categoria.length() > 0,
                    rx.vstack(
                        rx.foreach(FoodState.mermas_por_categoria, _merma_cat_row),
                        spacing="0", width="100%",
                    ),
                    rx.text("Sin mermas en el período.", font_size="12px", color="#94A3B8"),
                ),
                spacing="3", width="100%",
            ),
            background="#F8FAFC", border="1px solid #E2E8F0",
            border_radius="10px", padding="12px 14px", flex="1", min_width="260px",
        ),
        # Por insumo (top 20)
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.icon(tag="package_x", size=14, color="#B45309"),
                    rx.text("Mermas por insumo (top 20)", font_size="13px",
                            font_weight="700", color="#334155"),
                    spacing="2", align="center",
                ),
                rx.cond(
                    FoodState.mermas_por_insumo.length() > 0,
                    rx.vstack(
                        rx.foreach(FoodState.mermas_por_insumo, _merma_insumo_row),
                        spacing="0", width="100%", max_height="300px", overflow_y="auto",
                    ),
                    rx.text("Sin mermas en el período.", font_size="12px", color="#94A3B8"),
                ),
                spacing="3", width="100%",
            ),
            background="#F8FAFC", border="1px solid #E2E8F0",
            border_radius="10px", padding="12px 14px", flex="1", min_width="260px",
        ),
        gap="12px", width="100%",
        direction=rx.breakpoints(initial="column", md="row"),
    )


# ─── Contenido principal ─────────────────────────────────────────────────────

def _reportes_content() -> rx.Component:
    return rx.vstack(
        _venta_detalle_modal(),
        anulacion_modal(),
        # Header
        rx.hstack(
            rx.vstack(
                rx.text("Reportes", font_size="22px", font_weight="800", color="#0F172A"),
                rx.text("Dashboard y ventas del día", font_size="13px", color="#64748B"),
                spacing="0",
            ),
            rx.spacer(),
            rx.hstack(
                rx.button(
                    "Hoy", on_click=FoodState.filtro_rapido_hoy,
                    background=rx.cond(FoodState.historial_filtro_rapido == "hoy", "#EA580C", "#FFFFFF"),
                    color=rx.cond(FoodState.historial_filtro_rapido == "hoy", "#FFFFFF", "#64748B"),
                    border=rx.cond(FoodState.historial_filtro_rapido == "hoy", "1px solid #EA580C", "1px solid #E2E8F0"),
                    border_radius="8px", font_size="12px", font_weight="700",
                    padding_x="14px", padding_y="7px", cursor="pointer",
                    _hover={"border_color": "#EA580C", "color": "#EA580C"},
                ),
                rx.button(
                    "Semana", on_click=FoodState.filtro_rapido_semana,
                    background=rx.cond(FoodState.historial_filtro_rapido == "semana", "#EA580C", "#FFFFFF"),
                    color=rx.cond(FoodState.historial_filtro_rapido == "semana", "#FFFFFF", "#64748B"),
                    border=rx.cond(FoodState.historial_filtro_rapido == "semana", "1px solid #EA580C", "1px solid #E2E8F0"),
                    border_radius="8px", font_size="12px", font_weight="600",
                    padding_x="14px", padding_y="7px", cursor="pointer",
                    _hover={"border_color": "#EA580C", "color": "#EA580C"},
                ),
                rx.button(
                    "Mes", on_click=FoodState.filtro_rapido_mes,
                    background=rx.cond(FoodState.historial_filtro_rapido == "mes", "#EA580C", "#FFFFFF"),
                    color=rx.cond(FoodState.historial_filtro_rapido == "mes", "#FFFFFF", "#64748B"),
                    border=rx.cond(FoodState.historial_filtro_rapido == "mes", "1px solid #EA580C", "1px solid #E2E8F0"),
                    border_radius="8px", font_size="12px", font_weight="600",
                    padding_x="14px", padding_y="7px", cursor="pointer",
                    _hover={"border_color": "#EA580C", "color": "#EA580C"},
                ),
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
                rx.button(
                    rx.hstack(
                        rx.icon(tag="download", size=13, color="#FFFFFF"),
                        rx.text("Exportar Excel", font_size="13px", font_weight="700",
                                color="#FFFFFF"),
                        spacing="1", align="center",
                    ),
                    on_click=FoodState.exportar_ventas_excel,
                    background="#15803D",
                    border_radius="8px",
                    padding_x="14px", padding_y="7px",
                    cursor="pointer",
                    _hover={"background": "#166534"},
                ),
                spacing="2", wrap="wrap",
            ),
            width="100%",
            align="center",
            wrap="wrap", gap="8px",
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
                "Ticket promedio",
                FoodState.dashboard_ticket_promedio_texto,
                "calculator", "#7C3AED", "#F5F3FF", "#DDD6FE",
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

        # ── Analítica: por mozo / por hora / margen por plato ─────────────────
        rx.flex(
            # Ranking por mozo
            rx.box(
                rx.hstack(
                    rx.icon(tag="users", size=14, color="#EA580C"),
                    rx.text("Ventas por mozo", font_size="13px", font_weight="700", color="#334155"),
                    spacing="2", align="center", margin_bottom="10px",
                ),
                rx.cond(
                    FoodState.reporte_mozos.length() > 0,
                    _ventas_mozo_chart(),
                    rx.text("Sin ventas en el período.", font_size="12px", color="#94A3B8"),
                ),
                background="#F8FAFC", border="1px solid #E2E8F0",
                border_radius="10px", padding="12px 14px", flex="1", min_width="260px",
            ),
            # Ventas por hora
            rx.box(
                rx.hstack(
                    rx.icon(tag="clock", size=14, color="#EA580C"),
                    rx.text("Ventas por hora", font_size="13px", font_weight="700", color="#334155"),
                    spacing="2", align="center", margin_bottom="10px",
                ),
                rx.cond(
                    FoodState.reporte_horas.length() > 0,
                    _ventas_hora_chart(),
                    rx.text("Sin ventas en el período.", font_size="12px", color="#94A3B8"),
                ),
                background="#F8FAFC", border="1px solid #E2E8F0",
                border_radius="10px", padding="12px 14px", flex="1", min_width="260px",
            ),
            gap="12px", width="100%",
            direction=rx.breakpoints(initial="column", md="row"),
        ),
        # Desglose por método de pago
        rx.box(
            rx.hstack(
                rx.icon(tag="credit_card", size=14, color="#EA580C"),
                rx.text("Desglose por método de pago", font_size="13px", font_weight="700", color="#334155"),
                spacing="2", align="center", margin_bottom="10px",
            ),
            rx.cond(
                FoodState.reporte_metodos.length() > 0,
                rx.recharts.responsive_container(
                    rx.recharts.bar_chart(
                        rx.recharts.cartesian_grid(stroke_dasharray="3 3", stroke="#E2E8F0"),
                        rx.recharts.x_axis(
                            data_key="metodo", font_size=11, tick_line=False,
                            axis_line=False, stroke="#94A3B8",
                        ),
                        rx.recharts.y_axis(
                            font_size=11, tick_line=False, axis_line=False,
                            stroke="#94A3B8", width=70,
                        ),
                        rx.recharts.graphing_tooltip(
                            content_style={"fontSize": "12px", "borderRadius": "8px"},
                        ),
                        rx.recharts.bar(
                            data_key="total", fill="#EA580C", radius=[4, 4, 0, 0],
                            name="Total (S/)",
                        ),
                        rx.recharts.bar(
                            data_key="count", fill="#FB923C", radius=[4, 4, 0, 0],
                            name="Pagos",
                        ),
                        data=FoodState.reporte_metodos,
                        margin={"top": 4, "right": 4, "left": 0, "bottom": 0},
                    ),
                    width="100%", height=220,
                ),
                rx.text("Sin pagos en el período.", font_size="12px", color="#94A3B8"),
            ),
            background="#F8FAFC", border="1px solid #E2E8F0",
            border_radius="10px", padding="12px 14px", width="100%",
        ),
        # Comparativa entre períodos
        rx.box(
            rx.hstack(
                rx.icon(tag="git_compare_arrows", size=14, color="#EA580C"),
                rx.text("Comparativa con período anterior", font_size="13px",
                        font_weight="700", color="#334155"),
                spacing="2", align="center", margin_bottom="10px",
            ),
            rx.grid(
                # Ventas
                rx.box(
                    rx.text("Ventas", font_size="11px", color="#94A3B8", margin_bottom="2px"),
                    rx.text(FoodState.comp_ventas_actual, font_size="18px",
                            font_weight="800", color="#0F172A"),
                    rx.hstack(
                        rx.text(
                            "vs " + FoodState.comp_ventas_anterior,
                            font_size="11px", color="#64748B",
                        ),
                        rx.text(
                            rx.cond(FoodState.comp_ventas_pct >= 0, "+", "") + FoodState.comp_ventas_pct.to_string() + "%",
                            font_size="11px", font_weight="700",
                            color=rx.cond(FoodState.comp_ventas_pct >= 0, "#16A34A", "#DC2626"),
                        ),
                        spacing="1", align="center",
                    ),
                    rx.text(FoodState.comp_label_anterior, font_size="10px", color="#CBD5E1"),
                    padding="10px", background="#FFFFFF", border_radius="8px",
                    border="1px solid #E2E8F0",
                ),
                # Pedidos
                rx.box(
                    rx.text("Pedidos", font_size="11px", color="#94A3B8", margin_bottom="2px"),
                    rx.text(FoodState.comp_pedidos_actual.to_string(), font_size="18px",
                            font_weight="800", color="#0F172A"),
                    rx.hstack(
                        rx.text(
                            "vs " + FoodState.comp_pedidos_anterior.to_string(),
                            font_size="11px", color="#64748B",
                        ),
                        rx.text(
                            rx.cond(FoodState.comp_pedidos_diff >= 0, "+", "") + FoodState.comp_pedidos_diff.to_string(),
                            font_size="11px", font_weight="700",
                            color=rx.cond(FoodState.comp_pedidos_diff >= 0, "#16A34A", "#DC2626"),
                        ),
                        spacing="1", align="center",
                    ),
                    rx.text(FoodState.comp_label_anterior, font_size="10px", color="#CBD5E1"),
                    padding="10px", background="#FFFFFF", border_radius="8px",
                    border="1px solid #E2E8F0",
                ),
                # Ticket promedio
                rx.box(
                    rx.text("Ticket promedio", font_size="11px", color="#94A3B8", margin_bottom="2px"),
                    rx.text(FoodState.comp_ticket_actual, font_size="18px",
                            font_weight="800", color="#0F172A"),
                    rx.hstack(
                        rx.text(
                            "vs " + FoodState.comp_ticket_anterior,
                            font_size="11px", color="#64748B",
                        ),
                        rx.text(
                            rx.cond(FoodState.comp_ticket_pct >= 0, "+", "") + FoodState.comp_ticket_pct.to_string() + "%",
                            font_size="11px", font_weight="700",
                            color=rx.cond(FoodState.comp_ticket_pct >= 0, "#16A34A", "#DC2626"),
                        ),
                        spacing="1", align="center",
                    ),
                    rx.text(FoodState.comp_label_anterior, font_size="10px", color="#CBD5E1"),
                    padding="10px", background="#FFFFFF", border_radius="8px",
                    border="1px solid #E2E8F0",
                ),
                columns="3", spacing="3", width="100%",
            ),
            background="#F8FAFC", border="1px solid #E2E8F0",
            border_radius="10px", padding="12px 14px", width="100%",
        ),
        # ── P&L mensual (ADM-01) ─────────────────────────────────────────────
        _pyl_section(),

        # ── Descuentos y anulaciones (ADM-02) ────────────────────────────────
        _descuentos_anulaciones_section(),

        # ── Mermas valorizado (ADM-03) ───────────────────────────────────────
        _mermas_section(),

        # Margen por plato
        rx.box(
            rx.hstack(
                rx.icon(tag="chef_hat", size=14, color="#EA580C"),
                rx.text("Margen por plato (precio vs costo de receta)",
                        font_size="13px", font_weight="700", color="#334155"),
                spacing="2", align="center", margin_bottom="10px",
            ),
            rx.cond(
                FoodState.reporte_margen.length() > 0,
                rx.vstack(
                    rx.foreach(FoodState.reporte_margen, _margen_row),
                    spacing="0", width="100%",
                ),
                rx.text(
                    "Carga recetas y costos de insumos en Inventario para ver el margen de cada plato.",
                    font_size="12px", color="#94A3B8",
                ),
            ),
            background="#F8FAFC", border="1px solid #E2E8F0",
            border_radius="10px", padding="12px 14px", width="100%",
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
    return rx.cond(
        FoodState.pagina_cargada,
        app_shell(_reportes_content(), page_key="reportes"),
        app_shell(loading_placeholder(), page_key="reportes"),
    )
