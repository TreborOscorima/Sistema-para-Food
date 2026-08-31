"""Pagina de reportes — dashboard KPIs + historial filtrado."""

from __future__ import annotations

import reflex as rx

from app.components.shared import (
    anulacion_modal, app_shell, loading_placeholder,
    ACCENT, ACCENT_HOVER,
    DANGER_SOLID, DANGER_TEXT,
    DARK_700, DARK_800,
    PAGE_BACKGROUND,
    SUCCESS_DARK, SUCCESS_SOLID, SUCCESS_TEXT,
    TEXT_MUTED, TEXT_PRIMARY, TEXT_WHITE,
    WARNING_SOLID, WARNING_TEXT,
)
from app.states.food_state import (
    AnulacionView,
    DescuentoRankView,
    FoodState,
    MatrizProductoView,
    MermaCategoriaView,
    MermaInsumoView,
    PylLineView,
    ReversionView,
    SucursalView,
    TopPlatoView,
    VentaDetalleItemView,
    VentaHistorialView,
)
from app.states.reportes_state import ReportesState
from app.components.ayuda import ayuda_modal, ayuda_trigger
from app.components.upgrade import upgrade_cta

_METODOS_FILTRO = [
    ("", "Todos los métodos"),
    ("efectivo", "Efectivo"),
    ("tarjeta", "Tarjeta"),
    ("qr", "QR / Yape"),
    ("fiado", "Fiado / CC"),
    ("mixto", "Mixto"),
]


# ─── KPI Card ────────────────────────────────────────────────────────────────

def _kpi_card(label: str, value, icon: str, accent: str, bg: str, border: str,
              hint: str = "") -> rx.Component:
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
                # Ícono de ayuda con la definición exacta del KPI (M-08b). Solo
                # se muestra si se pasó un hint.
                rx.cond(
                    hint != "",
                    rx.tooltip(
                        rx.icon(tag="info", size=14, color=TEXT_MUTED,
                                cursor="help", flex_shrink="0"),
                        content=hint,
                    ),
                ),
            ),
            rx.text(value, font_size="22px", font_weight="800", color=TEXT_PRIMARY, line_height="1"),
            rx.text(label, font_size="11px", font_weight="600", color=TEXT_MUTED,
                    text_transform="uppercase", letter_spacing="0.06em"),
            spacing="2",
            align="start",
            width="100%",
        ),
        background=DARK_800,
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
                font_size="11px", font_weight="700", color=ACCENT,
            ),
            width="22px",
            height="22px",
            border_radius="full",
            background="rgba(234,88,12,0.08)",
            border="1px solid rgba(234,88,12,0.40)",
            display="flex",
            align_items="center",
            justify_content="center",
            flex_shrink="0",
        ),
        rx.text(plato.nombre, font_size="13px", color="var(--twk-slate-300)", flex="1",
                text_overflow="ellipsis", overflow="hidden", white_space="nowrap"),
        rx.badge(
            plato.cantidad.to_string() + " uds",
            background="rgba(234,88,12,0.08)",
            color=ACCENT,
            border_radius="5px",
            font_size="10px",
            font_weight="700",
            padding="2px 6px",
            flex_shrink="0",
        ),
        rx.text(plato.total_texto, font_size="13px", font_weight="700",
                color=SUCCESS_TEXT, min_width="72px", text_align="right", flex_shrink="0"),
        width="100%",
        align="center",
        padding="8px 10px",
        background=DARK_800,
        border_radius="8px",
        border=f"1px solid {DARK_800}",
        gap="8px",
        _hover={"background": DARK_700},
    )


# ─── Método badge ─────────────────────────────────────────────────────────────

def _metodo_badge(metodo: str) -> rx.Component:
    return rx.badge(
        metodo,
        background=rx.cond(
            metodo == "efectivo", "rgba(34,197,94,0.12)",
            rx.cond(metodo == "tarjeta", "rgba(59,130,246,0.12)",
            rx.cond(metodo == "qr", "rgba(245,158,11,0.12)",
            rx.cond(metodo == "fiado", "rgba(234,88,12,0.12)", "var(--twk-d700)"))),
        ),
        color=rx.cond(
            metodo == "efectivo", "#22C55E",
            rx.cond(metodo == "tarjeta", "#3B82F6",
            rx.cond(metodo == "qr", "#F59E0B",
            rx.cond(metodo == "fiado", "#EA580C", "var(--twk-slate-400)"))),
        ),
        border_radius="5px",
        font_size="10px",
        font_weight="700",
        padding="2px 6px",
    )


# ─── Fila historial ───────────────────────────────────────────────────────────

def _mozo_row(m) -> rx.Component:
    return rx.hstack(
        rx.text(m.nombre, font_size="13px", font_weight="600", color=TEXT_PRIMARY, flex="1"),
        rx.text(m.pedidos.to_string() + " ped.", font_size="12px", color=TEXT_MUTED,
                min_width="52px", text_align="right"),
        rx.vstack(
            rx.text(m.total_texto, font_size="13px", font_weight="800",
                    color=SUCCESS_TEXT, text_align="right"),
            rx.cond(
                m.propinas_texto != "",
                rx.text("prop. " + m.propinas_texto, font_size="10px",
                        color=WARNING_TEXT, text_align="right"),
                rx.fragment(),
            ),
            spacing="0", align="end", min_width="90px",
        ),
        width="100%", align="center", gap="8px",
        padding="8px 4px", border_bottom=f"1px solid {DARK_800}",
    )


def _propina_row(m) -> rx.Component:
    return rx.cond(
        m.propinas > 0,
        rx.hstack(
            rx.text(m.nombre, font_size="13px", font_weight="600", color=TEXT_PRIMARY, flex="1"),
            rx.text(m.pedidos.to_string() + " ped.", font_size="12px", color=TEXT_MUTED,
                    min_width="52px", text_align="right"),
            rx.text(m.propinas_texto, font_size="14px", font_weight="800",
                    color=WARNING_TEXT, text_align="right", min_width="80px"),
            width="100%", align="center", gap="8px",
            padding="8px 4px", border_bottom=f"1px solid {DARK_700}",
        ),
        rx.fragment(),
    )


def _ventas_hora_chart() -> rx.Component:
    return rx.recharts.responsive_container(
        rx.recharts.bar_chart(
            rx.recharts.cartesian_grid(stroke_dasharray="3 3", stroke="var(--twk-d700)"),
            rx.recharts.x_axis(
                data_key="hora_label", font_size=11, tick_line=False,
                axis_line=False, stroke="var(--twk-slate-400)",
            ),
            rx.recharts.y_axis(
                font_size=11, tick_line=False, axis_line=False,
                stroke="var(--twk-slate-400)", width=60,
            ),
            rx.recharts.graphing_tooltip(
                content_style={"fontSize": "12px", "borderRadius": "8px"},
            ),
            rx.recharts.bar(
                data_key="total", fill=ACCENT, radius=[4, 4, 0, 0],
                name="Total (S/)",
            ),
            rx.recharts.bar(
                data_key="pedidos", fill="#FB923C", radius=[4, 4, 0, 0],
                name="Pedidos",
            ),
            data=ReportesState.reporte_horas_chart,
            margin={"top": 4, "right": 4, "left": 0, "bottom": 0},
        ),
        width="100%", height=220,
    )


def _ventas_mozo_chart() -> rx.Component:
    return rx.recharts.responsive_container(
        rx.recharts.bar_chart(
            rx.recharts.cartesian_grid(stroke_dasharray="3 3", stroke="var(--twk-d700)"),
            rx.recharts.x_axis(
                data_key="nombre", font_size=10, tick_line=False,
                axis_line=False, stroke="var(--twk-slate-400)", interval=0,
                angle=-25, text_anchor="end", height=50,
            ),
            rx.recharts.y_axis(
                font_size=11, tick_line=False, axis_line=False,
                stroke="var(--twk-slate-400)", width=60,
            ),
            rx.recharts.graphing_tooltip(
                content_style={"fontSize": "12px", "borderRadius": "8px"},
            ),
            rx.recharts.bar(
                data_key="total", fill=ACCENT, radius=[4, 4, 0, 0],
                name="Total (S/)",
            ),
            rx.recharts.bar(
                data_key="propinas", fill="#F59E0B", radius=[4, 4, 0, 0],
                name="Propinas (S/)",
            ),
            data=ReportesState.reporte_mozos_chart,
            margin={"top": 4, "right": 4, "left": 0, "bottom": 0},
        ),
        width="100%", height=220,
    )


def _margen_row(p) -> rx.Component:
    return rx.hstack(
        rx.text(p.nombre, font_size="13px", font_weight="600", color=TEXT_PRIMARY, flex="1",
                min_width="0", overflow="hidden", text_overflow="ellipsis", white_space="nowrap"),
        rx.text("P " + p.precio_texto, font_size="12px", color=TEXT_MUTED,
                min_width="86px", text_align="right",
                display=rx.breakpoints(initial="none", sm="block")),
        rx.text("C " + p.costo_texto, font_size="12px", color=TEXT_MUTED,
                min_width="86px", text_align="right",
                display=rx.breakpoints(initial="none", sm="block")),
        rx.text(p.margen_texto, font_size="13px", font_weight="700", color="var(--twk-slate-300)",
                min_width="86px", text_align="right"),
        rx.hstack(
            rx.badge(
                p.margen_pct_texto,
                background=DARK_800, color=p.color,
                border="1.5px solid", border_color=p.color,
                border_radius="8px", font_size="11px", font_weight="800",
            ),
            rx.cond(
                p.costo_completo,
                rx.fragment(),
                rx.text("costos incompletos", font_size="10px", color=TEXT_MUTED),
            ),
            spacing="1", align="center", min_width="70px", justify="end",
        ),
        width="100%", align="center", gap="8px",
        padding="8px 4px", border_bottom=f"1px solid {DARK_800}",
    )


def _venta_row(venta: VentaHistorialView) -> rx.Component:
    return rx.hstack(
        rx.text(
            "#" + venta.pedido_id.to_string(),
            font_size="11px",
            color=TEXT_MUTED,
            min_width="36px",
            flex_shrink="0",
        ),
        rx.vstack(
            rx.text(venta.mesa_label, font_size="13px", color="var(--twk-slate-300)", width="100%",
                    text_overflow="ellipsis", overflow="hidden", white_space="nowrap"),
            rx.cond(
                venta.anulada,
                rx.text(venta.anulacion_texto, font_size="10px", color="var(--twk-danger-text)",
                        width="100%", text_overflow="ellipsis", overflow="hidden",
                        white_space="nowrap"),
                rx.fragment(),
            ),
            spacing="0", align="start", flex="1", min_width="0",
        ),
        _metodo_badge(venta.metodo_pago),
        rx.text(
            venta.mozo_nombre,
            font_size="12px", color=TEXT_MUTED,
            min_width="72px", text_align="center", flex_shrink="0",
            display=rx.breakpoints(initial="none", sm="block"),
        ),
        rx.text(
            venta.cajero_nombre,
            font_size="12px", color=TEXT_MUTED,
            min_width="72px", text_align="center", flex_shrink="0",
            display=rx.breakpoints(initial="none", lg="block"),
        ),
        rx.vstack(
            rx.cond(
                venta.anulada,
                rx.badge(
                    "ANULADA", background="rgba(239,68,68,0.12)", color="var(--twk-danger-text)",
                    border_radius="6px", font_size="10px", font_weight="800",
                ),
                rx.text(venta.total_con_propina_texto, font_size="13px", font_weight="700",
                        color=SUCCESS_TEXT, text_align="right"),
            ),
            rx.cond(
                venta.anulada,
                rx.text(venta.total_con_propina_texto, font_size="10px", color=TEXT_MUTED,
                        text_decoration="line-through", text_align="right"),
                rx.cond(
                    venta.propina > 0,
                    rx.text("+ " + venta.propina_texto + " prop.",
                            font_size="10px", color=WARNING_TEXT, text_align="right"),
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
            rx.tooltip(
                rx.button(
                    rx.icon(tag="trash_2", size=15),
                    on_click=FoodState.abrir_anulacion_venta(venta.pedido_id).stop_propagation,
                    background="transparent", color="var(--twk-slate-300)",
                    border="none", padding="2px", cursor="pointer",
                    _hover={"color": "#DC2626"},
                    flex_shrink="0",
                ),
                content="Anular venta",
            ),
        ),
        width="100%",
        align="center",
        padding="10px 12px",
        background=DARK_800,
        border_radius="8px",
        border=f"1px solid {DARK_700}",
        gap="8px",
        cursor="pointer",
        opacity=rx.cond(venta.anulada, "0.75", "1"),
        on_click=ReportesState.abrir_detalle_venta(venta.pedido_id),
        _hover={"background": DARK_700},
    )


def _venta_detalle_item_row(item: VentaDetalleItemView) -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.text(item.cantidad.to_string() + "x", font_size="12px",
                     color=TEXT_MUTED, min_width="26px", flex_shrink="0"),
            rx.text(item.nombre, font_size="13px", color=TEXT_PRIMARY, flex="1"),
            rx.text(item.subtotal_texto, font_size="13px", font_weight="700",
                     color=TEXT_PRIMARY, flex_shrink="0"),
            width="100%", align="center", gap="8px",
        ),
        rx.cond(
            item.notas != "",
            rx.text("Nota: " + item.notas, font_size="11px", color=TEXT_MUTED,
                     padding_left="34px"),
            rx.fragment(),
        ),
        spacing="1", width="100%", padding="8px 0",
        border_bottom=f"1px solid {DARK_800}",
    )


def _venta_detalle_modal() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.hstack(
                    rx.vstack(
                        rx.dialog.title("Pedido #" + ReportesState.venta_detalle_pedido_id.to_string(),
                                font_size="16px", font_weight="800", color=TEXT_PRIMARY, margin="0"),
                        rx.text(ReportesState.venta_detalle_mesa_label, font_size="13px", color=TEXT_MUTED),
                        spacing="0",
                    ),
                    rx.spacer(),
                    rx.dialog.close(
                        rx.icon(tag="x", size=16, color=TEXT_MUTED, cursor="pointer"),
                    ),
                    width="100%", align="start",
                ),
                rx.hstack(
                    _metodo_badge(ReportesState.venta_detalle_metodo),
                    rx.text("Mozo: " + ReportesState.venta_detalle_mozo, font_size="12px", color=TEXT_MUTED),
                    rx.text("Cajero: " + ReportesState.venta_detalle_cajero, font_size="12px", color=TEXT_MUTED),
                    spacing="3", align="center", wrap="wrap",
                ),
                rx.box(height="1px", width="100%", background=DARK_700),
                rx.vstack(
                    rx.foreach(ReportesState.venta_detalle_items, _venta_detalle_item_row),
                    spacing="0", width="100%", max_height="280px", overflow_y="auto",
                ),
                rx.box(height="1px", width="100%", background=DARK_700),
                rx.hstack(
                    rx.vstack(
                        rx.text("Total", font_size="14px", font_weight="700", color=TEXT_PRIMARY),
                        rx.cond(
                            ReportesState.venta_detalle_propina_texto != "",
                            rx.text("Incluye propina " + ReportesState.venta_detalle_propina_texto,
                                     font_size="11px", color=WARNING_TEXT),
                            rx.fragment(),
                        ),
                        spacing="0",
                    ),
                    rx.spacer(),
                    rx.text(ReportesState.venta_detalle_total_texto, font_size="18px",
                             font_weight="800", color=SUCCESS_TEXT),
                    width="100%", align="center",
                ),
                spacing="3", width="100%",
            ),
            max_width="420px",
            width="92vw",
            max_height="90vh",
            overflow_y="auto",
            background=PAGE_BACKGROUND,
            border=f"1px solid {DARK_800}",
        ),
        open=ReportesState.venta_detalle_visible,
        on_open_change=ReportesState.set_venta_detalle_visible,
    )


# ─── Filtros ──────────────────────────────────────────────────────────────────

def _filtros_bar() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.icon(tag="filter", size=14, color=TEXT_MUTED),
                rx.text("Filtros", font_size="13px", font_weight="700", color="var(--twk-slate-300)"),
                rx.cond(
                    ReportesState.historial_filtro_activo,
                    rx.badge(
                        "Activo",
                        background="rgba(234,88,12,0.08)",
                        color=ACCENT,
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
                    rx.text("Desde", font_size="11px", font_weight="600", color=TEXT_MUTED),
                    rx.input(
                        value=ReportesState.historial_filtro_fecha_desde,
                        on_change=ReportesState.set_historial_filtro_fecha_desde,
                        type="date",
                        background=DARK_800,
                        border=f"1px solid {DARK_700}",
                        color=TEXT_PRIMARY,
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
                    rx.text("Hasta", font_size="11px", font_weight="600", color=TEXT_MUTED),
                    rx.input(
                        value=ReportesState.historial_filtro_fecha_hasta,
                        on_change=ReportesState.set_historial_filtro_fecha_hasta,
                        type="date",
                        background=DARK_800,
                        border=f"1px solid {DARK_700}",
                        color=TEXT_PRIMARY,
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
                    rx.text("Método", font_size="11px", font_weight="600", color=TEXT_MUTED),
                    rx.select(
                        [label for _, label in _METODOS_FILTRO],
                        value=rx.cond(
                            ReportesState.historial_filtro_metodo == "", "Todos los métodos",
                            rx.cond(
                                ReportesState.historial_filtro_metodo == "efectivo", "Efectivo",
                                rx.cond(
                                    ReportesState.historial_filtro_metodo == "tarjeta", "Tarjeta",
                                    rx.cond(
                                        ReportesState.historial_filtro_metodo == "qr", "QR / Yape",
                                        rx.cond(
                                            ReportesState.historial_filtro_metodo == "fiado", "Fiado / CC",
                                            "Mixto",
                                        ),
                                    ),
                                ),
                            ),
                        ),
                        on_change=lambda v: ReportesState.set_historial_filtro_metodo(
                            rx.cond(v == "Todos los métodos", "",
                            rx.cond(v == "Efectivo", "efectivo",
                            rx.cond(v == "Tarjeta", "tarjeta",
                            rx.cond(v == "QR / Yape", "qr",
                            rx.cond(v == "Fiado / CC", "fiado", "mixto")))))
                        ),
                        background=DARK_800,
                        border=f"1px solid {DARK_700}",
                        color=TEXT_PRIMARY,
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
                    on_click=ReportesState.buscar_historial_manual,
                    background=ACCENT,
                    color=TEXT_WHITE,
                    border_radius="8px",
                    padding_x="14px",
                    padding_y="8px",
                    cursor="pointer",
                    _hover={"background": ACCENT_HOVER},
                ),
                rx.cond(
                    ReportesState.historial_filtro_activo,
                    rx.button(
                        rx.hstack(
                            rx.icon(tag="x", size=13),
                            rx.text("Limpiar", font_size="13px", font_weight="600"),
                            spacing="1", align="center",
                        ),
                        on_click=ReportesState.limpiar_filtros_historial,
                        background=DARK_800,
                        color=TEXT_MUTED,
                        border=f"1px solid {DARK_700}",
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
        background=PAGE_BACKGROUND,
        border=f"1px solid {DARK_700}",
        border_radius="10px",
        padding="12px 14px",
        width="100%",
    )


# ─── Cabecera historial ───────────────────────────────────────────────────────

def _historial_header() -> rx.Component:
    return rx.hstack(
        rx.text("#", font_size="11px", color=TEXT_MUTED, min_width="36px", flex_shrink="0"),
        rx.text("Mesa / Pedido", font_size="11px", color=TEXT_MUTED, flex="1"),
        rx.text("Método", font_size="11px", color=TEXT_MUTED, min_width="60px", flex_shrink="0"),
        rx.text(
            "Mozo", font_size="11px", color=TEXT_MUTED,
            min_width="72px", text_align="center", flex_shrink="0",
            display=rx.breakpoints(initial="none", sm="block"),
        ),
        rx.text(
            "Cajero", font_size="11px", color=TEXT_MUTED,
            min_width="72px", text_align="center", flex_shrink="0",
            display=rx.breakpoints(initial="none", lg="block"),
        ),
        rx.text("Total", font_size="11px", color=TEXT_MUTED,
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
            color=rx.cond(line.es_total, "var(--twk-text-primary)", "var(--twk-slate-400)"),
            flex="1",
        ),
        rx.hstack(
            rx.text(
                line.valor_texto,
                font_size=rx.cond(line.es_total, "15px", "13px"),
                font_weight=rx.cond(line.es_total, "800", "600"),
                color=rx.cond(
                    line.es_negativo, "var(--twk-danger-text)",
                    rx.cond(line.es_total, "var(--twk-text-primary)", "var(--twk-text-secondary)"),
                ),
                min_width="100px",
                text_align="right",
            ),
            rx.cond(
                line.margen_pct_texto != "",
                rx.badge(
                    line.margen_pct_texto,
                    background=rx.cond(line.es_negativo, "rgba(239,68,68,0.12)", "rgba(34,197,94,0.12)"),
                    color=rx.cond(line.es_negativo, DANGER_TEXT, SUCCESS_TEXT),
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
        border_top=rx.cond(line.es_total, "2px solid var(--twk-d600)", f"1px solid {DARK_700}"),
    )


def _excel_btn(on_click) -> rx.Component:
    return rx.button(
        rx.icon(tag="download", size=12, color=SUCCESS_TEXT),
        rx.text("Excel", font_size="11px", font_weight="700", color=SUCCESS_TEXT),
        on_click=on_click,
        background="rgba(34,197,94,0.08)",
        border="1px solid #BBF7D0",
        border_radius="8px",
        padding="4px 10px",
        cursor="pointer",
        _hover={"background": "rgba(34,197,94,0.12)"},
        display="flex",
        align_items="center",
        gap="4px",
        height="auto",
    )


def _productos_stock_section() -> rx.Component:
    """Export de control de productos (stock actual + unidades vendidas).

    Disponible en TODOS los planes (Standard incluido): es control operativo, no
    análisis financiero. La matriz con margen/costo sigue siendo Profesional.
    """
    return rx.box(
        rx.hstack(
            rx.icon(tag="package_check", size=16, color=ACCENT),
            rx.vstack(
                rx.text("Productos — vendidos y stock", font_size="13px",
                        font_weight="700", color="var(--twk-slate-300)"),
                rx.text(
                    "Baja a Excel el stock actual y las unidades vendidas de cada "
                    "producto de la carta. Usa los filtros de fecha del Historial "
                    "(Desde/Hasta) para acotar el período.",
                    font_size="11px", color=TEXT_MUTED,
                ),
                spacing="1", align="start", flex="1", min_width="0",
            ),
            rx.spacer(),
            _excel_btn(ReportesState.exportar_productos_stock_excel),
            spacing="3", align="center", width="100%",
        ),
        background=DARK_800, border=f"1px solid {DARK_700}",
        border_radius="10px", padding="14px 16px", width="100%",
    )


def _pyl_section() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.icon(tag="file_text", size=14, color=ACCENT),
                rx.text("Estado de resultados (P&L)", font_size="13px",
                        font_weight="700", color="var(--twk-slate-300)"),
                rx.spacer(),
                rx.hstack(
                    rx.select(
                        [label for _, label in _MESES],
                        value=rx.cond(
                            ReportesState.pyl_mes == 1, "Enero",
                            rx.cond(ReportesState.pyl_mes == 2, "Febrero",
                            rx.cond(ReportesState.pyl_mes == 3, "Marzo",
                            rx.cond(ReportesState.pyl_mes == 4, "Abril",
                            rx.cond(ReportesState.pyl_mes == 5, "Mayo",
                            rx.cond(ReportesState.pyl_mes == 6, "Junio",
                            rx.cond(ReportesState.pyl_mes == 7, "Julio",
                            rx.cond(ReportesState.pyl_mes == 8, "Agosto",
                            rx.cond(ReportesState.pyl_mes == 9, "Septiembre",
                            rx.cond(ReportesState.pyl_mes == 10, "Octubre",
                            rx.cond(ReportesState.pyl_mes == 11, "Noviembre",
                            "Diciembre",
                            ))))))))))),
                        on_change=lambda v: ReportesState.set_pyl_mes(
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
                        background=DARK_800,
                        border=f"1px solid {DARK_700}",
                        border_radius="8px",
                        font_size="12px",
                        width="130px",
                    ),
                    rx.input(
                        value=ReportesState.pyl_anio.to_string(),
                        on_change=ReportesState.set_pyl_anio,
                        type="number",
                        background=DARK_800,
                        border=f"1px solid {DARK_700}",
                        border_radius="8px",
                        font_size="12px",
                        width="80px",
                        padding_x="8px",
                    ),
                    rx.tooltip(
                        rx.button(
                            rx.icon(tag="refresh_cw", size=13),
                            on_click=ReportesState.actualizar_pyl,
                            background="rgba(234,88,12,0.08)",
                            color=ACCENT,
                            border="1px solid rgba(234,88,12,0.40)",
                            border_radius="8px",
                            padding="6px 10px",
                            cursor="pointer",
                            _hover={"opacity": "0.85"},
                        ),
                        content="Actualizar",
                    ),
                    _excel_btn(ReportesState.exportar_pyl_excel),
                    spacing="2", align="center",
                ),
                spacing="2", align="center", width="100%", wrap="wrap",
            ),
            rx.cond(
                ReportesState.pyl_lineas.length() > 0,
                rx.vstack(
                    rx.foreach(ReportesState.pyl_lineas, _pyl_line_row),
                    spacing="0", width="100%",
                ),
                rx.text("Sin datos para el mes seleccionado.", font_size="12px", color=TEXT_MUTED),
            ),
            spacing="3", width="100%",
        ),
        background=PAGE_BACKGROUND, border=f"1px solid {DARK_700}",
        border_radius="10px", padding="12px 14px", width="100%",
    )


# ─── Resumen IGV mensual (ADM-05) ──────────────────────────────────────────


def _igv_kpi(label: str, value, icon: str) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.text(label, font_size="11px", font_weight="600", color=TEXT_MUTED),
            rx.text(value, font_size="18px", font_weight="800", color=TEXT_PRIMARY,
                    line_height="1"),
            spacing="1", align="start",
        ),
        flex="1", min_width="120px",
    )


def _igv_section() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.icon(tag="receipt", size=14, color=ACCENT),
                rx.text("Resumen IGV mensual", font_size="13px",
                        font_weight="700", color="var(--twk-slate-300)"),
                rx.spacer(),
                rx.hstack(
                    rx.select(
                        [label for _, label in _MESES],
                        value=rx.cond(
                            ReportesState.igv_mes == 1, "Enero",
                            rx.cond(ReportesState.igv_mes == 2, "Febrero",
                            rx.cond(ReportesState.igv_mes == 3, "Marzo",
                            rx.cond(ReportesState.igv_mes == 4, "Abril",
                            rx.cond(ReportesState.igv_mes == 5, "Mayo",
                            rx.cond(ReportesState.igv_mes == 6, "Junio",
                            rx.cond(ReportesState.igv_mes == 7, "Julio",
                            rx.cond(ReportesState.igv_mes == 8, "Agosto",
                            rx.cond(ReportesState.igv_mes == 9, "Septiembre",
                            rx.cond(ReportesState.igv_mes == 10, "Octubre",
                            rx.cond(ReportesState.igv_mes == 11, "Noviembre",
                            "Diciembre",
                            ))))))))))),
                        on_change=lambda v: ReportesState.set_igv_mes(
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
                        background=DARK_800,
                        border=f"1px solid {DARK_700}",
                        border_radius="8px",
                        font_size="12px",
                        width="130px",
                    ),
                    rx.input(
                        value=ReportesState.igv_anio.to_string(),
                        on_change=ReportesState.set_igv_anio,
                        type="number",
                        background=DARK_800,
                        border=f"1px solid {DARK_700}",
                        border_radius="8px",
                        font_size="12px",
                        width="80px",
                        padding_x="8px",
                    ),
                    rx.tooltip(
                        rx.button(
                            rx.icon(tag="refresh_cw", size=13),
                            on_click=ReportesState.actualizar_igv,
                            background="rgba(234,88,12,0.08)",
                            color=ACCENT,
                            border="1px solid rgba(234,88,12,0.40)",
                            border_radius="8px",
                            padding="6px 10px",
                            cursor="pointer",
                            _hover={"opacity": "0.85"},
                        ),
                        content="Actualizar",
                    ),
                    _excel_btn(ReportesState.exportar_igv_excel),
                    spacing="2", align="center",
                ),
                spacing="2", align="center", width="100%", wrap="wrap",
            ),
            rx.cond(
                ReportesState.igv_pedidos > 0,
                rx.vstack(
                    rx.flex(
                        _igv_kpi("Ventas netas (con IGV)", ReportesState.igv_ventas_netas_texto, "banknote"),
                        _igv_kpi("Base imponible", ReportesState.igv_base_imponible_texto, "calculator"),
                        _igv_kpi("IGV (" + ReportesState.igv_porcentaje.to_string() + "%)", ReportesState.igv_monto_texto, "percent"),
                        wrap="wrap", gap="12px", width="100%",
                    ),
                    rx.text(
                        ReportesState.igv_pedidos.to_string() + " pedidos cobrados en el mes.",
                        font_size="11px", color=TEXT_MUTED,
                    ),
                    spacing="3", width="100%",
                ),
                rx.text("Sin pedidos cobrados para el mes seleccionado.", font_size="12px", color=TEXT_MUTED),
            ),
            spacing="3", width="100%",
        ),
        background="rgba(34,197,94,0.08)", border="1px solid #BBF7D0",
        border_radius="10px", padding="12px 14px", width="100%",
    )


# ─── Matriz estrella/perro (ADM-06) ────────────────────────────────────────

_CAT_COLORS = {
    "estrella": ("rgba(245,158,11,0.12)", "#F59E0B"),
    "vaca": ("rgba(59,130,246,0.12)", "#3B82F6"),
    "puzzle": ("rgba(124,58,237,0.12)", "var(--twk-purple-text)"),
    "perro": ("rgba(239,68,68,0.12)", "var(--twk-danger-text)"),
}


def _matriz_row(p: MatrizProductoView) -> rx.Component:
    return rx.hstack(
        rx.text(p.categoria_emoji, font_size="16px", flex_shrink="0", width="22px"),
        rx.text(p.nombre, font_size="13px", font_weight="600", color=TEXT_PRIMARY,
                flex="1", min_width="0", text_overflow="ellipsis",
                overflow="hidden", white_space="nowrap"),
        rx.text(p.unidades.to_string() + " uds", font_size="12px", color=TEXT_MUTED,
                min_width="55px", text_align="right"),
        rx.text(p.ingreso_texto, font_size="12px", font_weight="600", color=TEXT_PRIMARY,
                min_width="75px", text_align="right"),
        rx.badge(
            p.margen_pct_texto,
            background=rx.cond(
                p.categoria == "estrella", "rgba(245,158,11,0.12)",
                rx.cond(p.categoria == "vaca", "rgba(59,130,246,0.12)",
                rx.cond(p.categoria == "puzzle", "rgba(124,58,237,0.12)", "rgba(239,68,68,0.12)")),
            ),
            color=rx.cond(
                p.categoria == "estrella", "#F59E0B",
                rx.cond(p.categoria == "vaca", "#3B82F6",
                rx.cond(p.categoria == "puzzle", "var(--twk-purple-text)", "var(--twk-danger-text)")),
            ),
            border_radius="6px", font_size="11px", font_weight="800",
            padding="2px 6px", min_width="55px", text_align="center",
        ),
        width="100%", align="center", gap="8px",
        padding="6px 4px", border_bottom=f"1px solid {DARK_800}",
    )


def _matriz_section() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.icon(tag="grid_2x2", size=14, color=ACCENT),
                rx.text("Matriz estrella / perro", font_size="13px",
                        font_weight="700", color="var(--twk-slate-300)"),
                rx.spacer(),
                rx.tooltip(
                    rx.button(
                        rx.icon(tag="refresh_cw", size=13),
                        on_click=ReportesState.cargar_matriz_productos,
                        background="rgba(234,88,12,0.08)",
                        color=ACCENT,
                        border="1px solid rgba(234,88,12,0.40)",
                        border_radius="8px",
                        padding="6px 10px",
                        cursor="pointer",
                        _hover={"opacity": "0.85"},
                    ),
                    content="Actualizar",
                ),
                _excel_btn(ReportesState.exportar_matriz_excel),
                spacing="2", align="center", width="100%",
            ),
            rx.cond(
                ReportesState.matriz_productos.length() > 0,
                rx.vstack(
                    rx.hstack(
                        rx.badge("⭐ " + ReportesState.matriz_estrellas.to_string(),
                                 background="rgba(245,158,11,0.12)", color=WARNING_TEXT,
                                 border_radius="6px", font_size="11px",
                                 font_weight="700", padding="3px 8px"),
                        rx.badge("\U0001F42E " + ReportesState.matriz_vacas.to_string(),
                                 background="rgba(59,130,246,0.12)", color="#3B82F6",
                                 border_radius="6px", font_size="11px",
                                 font_weight="700", padding="3px 8px"),
                        rx.badge("\U0001F9E9 " + ReportesState.matriz_puzzles.to_string(),
                                 background="rgba(124,58,237,0.12)", color="var(--twk-purple-text)",
                                 border_radius="6px", font_size="11px",
                                 font_weight="700", padding="3px 8px"),
                        rx.badge("\U0001F415 " + ReportesState.matriz_perros.to_string(),
                                 background="rgba(239,68,68,0.12)", color="var(--twk-danger-text)",
                                 border_radius="6px", font_size="11px",
                                 font_weight="700", padding="3px 8px"),
                        spacing="2", wrap="wrap",
                    ),
                    rx.box(
                        rx.foreach(ReportesState.matriz_productos, _matriz_row),
                        width="100%",
                        max_height="320px",
                        overflow_y="auto",
                    ),
                    spacing="3", width="100%",
                ),
                rx.text("Sin datos de ventas para el período.", font_size="12px", color=TEXT_MUTED),
            ),
            spacing="3", width="100%",
        ),
        background="rgba(245,158,11,0.10)", border="1px solid rgba(245,158,11,0.20)",
        border_radius="10px", padding="12px 14px", width="100%",
    )


# ─── Descuentos y anulaciones (ADM-02) ──────────────────────────────────────


def _descuento_rank_row(d: DescuentoRankView) -> rx.Component:
    return rx.hstack(
        rx.text(d.cajero, font_size="13px", font_weight="600", color=TEXT_PRIMARY, flex="1"),
        rx.text(d.pedidos.to_string() + " ped.", font_size="12px", color=TEXT_MUTED,
                min_width="52px", text_align="right"),
        rx.text(d.total_descuento_texto, font_size="13px", font_weight="700",
                color=DANGER_TEXT, min_width="86px", text_align="right"),
        rx.badge(
            d.pct_descuento_texto,
            background="rgba(239,68,68,0.12)", color="var(--twk-danger-text)",
            border_radius="6px", font_size="11px", font_weight="800",
            padding="2px 6px",
        ),
        width="100%", align="center", gap="8px",
        padding="8px 4px", border_bottom=f"1px solid {DARK_800}",
    )


def _anulacion_row(a: AnulacionView) -> rx.Component:
    return rx.hstack(
        rx.text("#" + a.pedido_id.to_string(), font_size="11px", color=TEXT_MUTED,
                min_width="36px", flex_shrink="0"),
        rx.vstack(
            rx.text(a.motivo, font_size="13px", color="var(--twk-slate-300)", width="100%",
                    text_overflow="ellipsis", overflow="hidden", white_space="nowrap"),
            rx.text(
                a.cancelado_por + " — " + a.cancelado_en_texto,
                font_size="10px", color=TEXT_MUTED,
            ),
            spacing="0", flex="1", min_width="0",
        ),
        rx.text(a.total_texto, font_size="13px", font_weight="700", color=DANGER_TEXT,
                min_width="80px", text_align="right", flex_shrink="0"),
        width="100%", align="center", gap="8px",
        padding="8px 4px", border_bottom=f"1px solid {DARK_800}",
    )


def _descuentos_anulaciones_section() -> rx.Component:
    return rx.flex(
        # Descuentos por cajero
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.icon(tag="percent", size=14, color=DANGER_TEXT),
                    rx.text("Descuentos por cajero", font_size="13px",
                            font_weight="700", color="var(--twk-slate-300)"),
                    rx.spacer(),
                    rx.badge(
                        ReportesState.descuentos_total_texto,
                        background="rgba(239,68,68,0.12)", color="var(--twk-danger-text)",
                        border_radius="6px", font_size="11px", font_weight="800",
                        padding="2px 8px",
                    ),
                    spacing="2", align="center", width="100%",
                ),
                rx.cond(
                    ReportesState.descuentos_rank.length() > 0,
                    rx.vstack(
                        rx.foreach(ReportesState.descuentos_rank, _descuento_rank_row),
                        spacing="0", width="100%",
                    ),
                    rx.text("Sin descuentos en el período.", font_size="12px", color=TEXT_MUTED),
                ),
                spacing="3", width="100%",
            ),
            background=PAGE_BACKGROUND, border=f"1px solid {DARK_700}",
            border_radius="10px", padding="12px 14px", flex="1", min_width="260px",
        ),
        # Anulaciones
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.icon(tag="trash_2", size=14, color=DANGER_TEXT),
                    rx.text("Anulaciones", font_size="13px",
                            font_weight="700", color="var(--twk-slate-300)"),
                    rx.spacer(),
                    rx.badge(
                        ReportesState.anulaciones_total_texto,
                        background="rgba(239,68,68,0.12)", color="var(--twk-danger-text)",
                        border_radius="6px", font_size="11px", font_weight="800",
                        padding="2px 8px",
                    ),
                    spacing="2", align="center", width="100%",
                ),
                rx.cond(
                    ReportesState.anulaciones_lista.length() > 0,
                    rx.vstack(
                        rx.foreach(ReportesState.anulaciones_lista, _anulacion_row),
                        spacing="0", width="100%", max_height="300px", overflow_y="auto",
                    ),
                    rx.text("Sin anulaciones en el período.", font_size="12px", color=TEXT_MUTED),
                ),
                spacing="3", width="100%",
            ),
            background=PAGE_BACKGROUND, border=f"1px solid {DARK_700}",
            border_radius="10px", padding="12px 14px", flex="1", min_width="260px",
        ),
        # Reversiones de cobro
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.icon(tag="undo_2", size=14, color=WARNING_TEXT),
                    rx.text("Reversiones de cobro", font_size="13px",
                            font_weight="700", color="var(--twk-slate-300)"),
                    rx.spacer(),
                    rx.badge(
                        ReportesState.reversiones_total_texto,
                        background="rgba(245,158,11,0.12)", color="var(--twk-warning-text)",
                        border_radius="6px", font_size="11px", font_weight="800",
                        padding="2px 8px",
                    ),
                    spacing="2", align="center", width="100%",
                ),
                rx.cond(
                    ReportesState.reversiones_lista.length() > 0,
                    rx.vstack(
                        rx.foreach(ReportesState.reversiones_lista, _reversion_row),
                        spacing="0", width="100%", max_height="300px", overflow_y="auto",
                    ),
                    rx.text("Sin reversiones en el período.", font_size="12px", color=TEXT_MUTED),
                ),
                spacing="3", width="100%",
            ),
            background=PAGE_BACKGROUND, border=f"1px solid {DARK_700}",
            border_radius="10px", padding="12px 14px", flex="1", min_width="260px",
        ),
        _excel_btn(ReportesState.exportar_descuentos_excel),
        gap="12px", width="100%",
        direction=rx.breakpoints(initial="column", md="row"),
        flex_wrap="wrap",
    )


def _reversion_row(r: ReversionView) -> rx.Component:
    return rx.hstack(
        rx.text("#" + r.pedido_id.to_string(), font_size="11px", color=TEXT_MUTED,
                min_width="36px", flex_shrink="0"),
        rx.vstack(
            rx.text(r.motivo, font_size="13px", color="var(--twk-slate-300)", width="100%",
                    text_overflow="ellipsis", overflow="hidden", white_space="nowrap"),
            rx.text(
                r.revertido_por + " — " + r.revertido_en_texto,
                font_size="10px", color=TEXT_MUTED,
            ),
            spacing="0", flex="1", min_width="0",
        ),
        rx.text(r.total_texto, font_size="13px", font_weight="700", color=WARNING_TEXT,
                min_width="80px", text_align="right", flex_shrink="0"),
        width="100%", align="center", gap="8px",
        padding="8px 4px", border_bottom=f"1px solid {DARK_800}",
    )


# ─── Mermas valorizado (ADM-03) ─────────────────────────────────────────────


def _merma_cat_row(c: MermaCategoriaView) -> rx.Component:
    return rx.hstack(
        rx.text(c.categoria, font_size="13px", font_weight="600", color=TEXT_PRIMARY, flex="1"),
        rx.text(c.registros.to_string() + " reg.", font_size="12px", color=TEXT_MUTED,
                min_width="52px", text_align="right"),
        rx.text(c.valor_texto, font_size="13px", font_weight="700", color=DANGER_TEXT,
                min_width="86px", text_align="right"),
        width="100%", align="center", gap="8px",
        padding="8px 4px", border_bottom=f"1px solid {DARK_800}",
    )


def _merma_insumo_row(i: MermaInsumoView) -> rx.Component:
    return rx.hstack(
        rx.text(i.nombre, font_size="13px", font_weight="600", color=TEXT_PRIMARY, flex="1",
                min_width="0", overflow="hidden", text_overflow="ellipsis", white_space="nowrap"),
        rx.text(i.cantidad_texto + " " + i.unidad, font_size="12px", color=TEXT_MUTED,
                min_width="80px", text_align="right"),
        rx.text(i.valor_texto, font_size="13px", font_weight="700", color=DANGER_TEXT,
                min_width="86px", text_align="right"),
        width="100%", align="center", gap="8px",
        padding="8px 4px", border_bottom=f"1px solid {DARK_800}",
    )


def _mermas_section() -> rx.Component:
    return rx.flex(
        # Por categoría
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.icon(tag="trash_2", size=14, color=WARNING_TEXT),
                    rx.text("Mermas por categoría", font_size="13px",
                            font_weight="700", color="var(--twk-slate-300)"),
                    rx.spacer(),
                    rx.badge(
                        ReportesState.mermas_total_texto,
                        background="rgba(245,158,11,0.12)", color=WARNING_TEXT,
                        border_radius="6px", font_size="11px", font_weight="800",
                        padding="2px 8px",
                    ),
                    spacing="2", align="center", width="100%",
                ),
                rx.cond(
                    ReportesState.mermas_por_categoria.length() > 0,
                    rx.vstack(
                        rx.foreach(ReportesState.mermas_por_categoria, _merma_cat_row),
                        spacing="0", width="100%",
                    ),
                    rx.text("Sin mermas en el período.", font_size="12px", color=TEXT_MUTED),
                ),
                spacing="3", width="100%",
            ),
            background=PAGE_BACKGROUND, border=f"1px solid {DARK_700}",
            border_radius="10px", padding="12px 14px", flex="1", min_width="260px",
        ),
        # Por insumo (top 20)
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.icon(tag="package_x", size=14, color=WARNING_TEXT),
                    rx.text("Mermas por insumo (top 20)", font_size="13px",
                            font_weight="700", color="var(--twk-slate-300)"),
                    spacing="2", align="center",
                ),
                rx.cond(
                    ReportesState.mermas_por_insumo.length() > 0,
                    rx.vstack(
                        rx.foreach(ReportesState.mermas_por_insumo, _merma_insumo_row),
                        spacing="0", width="100%", max_height="300px", overflow_y="auto",
                    ),
                    rx.text("Sin mermas en el período.", font_size="12px", color=TEXT_MUTED),
                ),
                spacing="3", width="100%",
            ),
            background=PAGE_BACKGROUND, border=f"1px solid {DARK_700}",
            border_radius="10px", padding="12px 14px", flex="1", min_width="260px",
        ),
        _excel_btn(ReportesState.exportar_mermas_excel),
        gap="12px", width="100%",
        direction=rx.breakpoints(initial="column", md="row"),
        flex_wrap="wrap",
    )


# ─── Contenido principal ─────────────────────────────────────────────────────

def _reportes_ayuda() -> rx.Component:
    return ayuda_modal(
        titulo="¿Cómo funciona Reportes?",
        subtitulo="Dashboard y ventas del local",
        secciones=[
            {"titulo": "Panel del período", "pasos": [
                "Arriba ves los indicadores: ventas, tickets, ticket promedio y más.",
                "Cambia el rango con «Hoy», «Semana» o eligiendo fechas propias.",
                "Si tienes más de una sucursal, filtra por sucursal desde el header.",
            ]},
            {"titulo": "Historial de ventas", "pasos": [
                "Abre cualquier venta para ver el detalle de productos y pagos.",
                "Desde el detalle puedes anular una venta, si tienes el permiso.",
            ]},
            {"titulo": "Exportar", "pasos": [
                "Cada tabla tiene un botón «Excel» para descargar los datos.",
            ]},
        ],
    )


def _reportes_content() -> rx.Component:
    return rx.vstack(
        _venta_detalle_modal(),
        anulacion_modal(),
        _reportes_ayuda(),
        # Header
        rx.hstack(
            rx.vstack(
                rx.text("Reportes", font_size="22px", font_weight="800", color=TEXT_PRIMARY),
                rx.text("Dashboard y ventas del día", font_size="13px", color=TEXT_MUTED),
                spacing="0",
            ),
            rx.cond(
                FoodState.tiene_sucursales,
                rx.hstack(
                    rx.icon(tag="map_pin", size=14, color=TEXT_MUTED),
                    rx.button(
                        "Todas",
                        on_click=ReportesState.cambiar_sucursal_reportes("0"),
                        background=rx.cond(
                            ReportesState.reportes_sucursal_id == 0,
                            "#EA580C", "var(--twk-d800)",
                        ),
                        color=rx.cond(
                            ReportesState.reportes_sucursal_id == 0,
                            "#FFFFFF", "var(--twk-slate-400)",
                        ),
                        border=rx.cond(
                            ReportesState.reportes_sucursal_id == 0,
                            "1px solid #EA580C", f"1px solid {DARK_700}",
                        ),
                        border_radius="7px", font_size="11px", font_weight="600",
                        padding_x="10px", padding_y="5px", cursor="pointer",
                        _hover={"border_color": ACCENT},
                    ),
                    rx.foreach(
                        FoodState.sucursales_empresa,
                        lambda s: rx.button(
                            s.nombre,
                            on_click=ReportesState.cambiar_sucursal_reportes(
                                s.id.to_string()
                            ),
                            background=rx.cond(
                                ReportesState.reportes_sucursal_id == s.id,
                                "#EA580C", "var(--twk-d800)",
                            ),
                            color=rx.cond(
                                ReportesState.reportes_sucursal_id == s.id,
                                "#FFFFFF", "var(--twk-slate-400)",
                            ),
                            border=rx.cond(
                                ReportesState.reportes_sucursal_id == s.id,
                                "1px solid #EA580C", f"1px solid {DARK_700}",
                            ),
                            border_radius="7px", font_size="11px", font_weight="600",
                            padding_x="10px", padding_y="5px", cursor="pointer",
                            _hover={"border_color": ACCENT},
                        ),
                    ),
                    spacing="1", align="center", flex_wrap="wrap",
                ),
                rx.fragment(),
            ),
            rx.spacer(),
            ayuda_trigger(),
            rx.hstack(
                rx.button(
                    "Hoy", on_click=ReportesState.filtro_rapido_hoy,
                    background=rx.cond(ReportesState.historial_filtro_rapido == "hoy", ACCENT, DARK_800),
                    color=rx.cond(ReportesState.historial_filtro_rapido == "hoy", "#FFFFFF", "var(--twk-slate-400)"),
                    border=rx.cond(ReportesState.historial_filtro_rapido == "hoy", "1px solid #EA580C", f"1px solid {DARK_700}"),
                    border_radius="8px", font_size="12px", font_weight="700",
                    padding_x="14px", padding_y="7px", cursor="pointer",
                    _hover={"border_color": ACCENT, "color": ACCENT},
                ),
                rx.button(
                    "Semana", on_click=ReportesState.filtro_rapido_semana,
                    background=rx.cond(ReportesState.historial_filtro_rapido == "semana", ACCENT, DARK_800),
                    color=rx.cond(ReportesState.historial_filtro_rapido == "semana", "#FFFFFF", "var(--twk-slate-400)"),
                    border=rx.cond(ReportesState.historial_filtro_rapido == "semana", "1px solid #EA580C", f"1px solid {DARK_700}"),
                    border_radius="8px", font_size="12px", font_weight="600",
                    padding_x="14px", padding_y="7px", cursor="pointer",
                    _hover={"border_color": ACCENT, "color": ACCENT},
                ),
                rx.button(
                    "Mes", on_click=ReportesState.filtro_rapido_mes,
                    background=rx.cond(ReportesState.historial_filtro_rapido == "mes", ACCENT, DARK_800),
                    color=rx.cond(ReportesState.historial_filtro_rapido == "mes", "#FFFFFF", "var(--twk-slate-400)"),
                    border=rx.cond(ReportesState.historial_filtro_rapido == "mes", "1px solid #EA580C", f"1px solid {DARK_700}"),
                    border_radius="8px", font_size="12px", font_weight="600",
                    padding_x="14px", padding_y="7px", cursor="pointer",
                    _hover={"border_color": ACCENT, "color": ACCENT},
                ),
                rx.button(
                    rx.hstack(
                        rx.icon(tag="refresh_cw", size=13),
                        rx.text("Actualizar", font_size="13px", font_weight="600"),
                        spacing="1", align="center",
                    ),
                    on_click=[ReportesState.cargar_dashboard, ReportesState.cargar_historial_ventas],
                    background="rgba(234,88,12,0.08)",
                    color=ACCENT,
                    border="1px solid rgba(234,88,12,0.40)",
                    border_radius="8px",
                    font_size="13px",
                    cursor="pointer",
                    _hover={"opacity": "0.85"},
                ),
                rx.button(
                    rx.hstack(
                        rx.icon(tag="download", size=13, color=TEXT_WHITE),
                        rx.text("Exportar Excel", font_size="13px", font_weight="700",
                                color=TEXT_WHITE),
                        spacing="1", align="center",
                    ),
                    on_click=ReportesState.exportar_ventas_excel,
                    background=SUCCESS_DARK,
                    border_radius="8px",
                    padding_x="14px", padding_y="7px",
                    cursor="pointer",
                    _hover={"background": SUCCESS_DARK},
                ),
                rx.button(
                    rx.hstack(
                        rx.icon(tag="file_text", size=13, color=TEXT_WHITE),
                        rx.text("PDF Ejecutivo", font_size="13px", font_weight="700",
                                color=TEXT_WHITE),
                        spacing="1", align="center",
                    ),
                    on_click=ReportesState.exportar_pdf_ejecutivo,
                    background="#7C3AED",
                    border_radius="8px",
                    padding_x="14px", padding_y="7px",
                    cursor="pointer",
                    _hover={"background": "#6D28D9"},
                ),
                spacing="2", wrap="wrap",
            ),
            width="100%",
            align="center",
            wrap="wrap", gap="8px",
        ),

        # ── Período activo de los KPIs ────────────────────────────────────────
        # Los indicadores de abajo siguen el filtro Hoy/Semana/Mes; esta línea
        # deja explícito el período para que no se lea "Ventas hoy" con datos
        # del mes.
        rx.hstack(
            rx.icon(tag="calendar_range", size=13, color=TEXT_MUTED),
            rx.text("Indicadores del período:", font_size="12px", color=TEXT_MUTED),
            rx.badge(
                ReportesState.dashboard_periodo_label,
                background="rgba(234,88,12,0.08)", color=ACCENT,
                border_radius="6px", font_size="11px", font_weight="700",
                padding="2px 8px",
            ),
            spacing="2", align="center",
        ),

        # ── KPI cards ────────────────────────────────────────────────────────
        rx.grid(
            _kpi_card(
                "Ventas",
                ReportesState.dashboard_ventas_hoy_texto,
                "trending_up", "#22C55E", "rgba(34,197,94,0.12)", "rgba(34,197,94,0.25)",
                hint="Total cobrado en el período, sin contar propinas.",
            ),
            _kpi_card(
                "Pedidos cobrados",
                ReportesState.dashboard_pedidos_hoy.to_string(),
                "receipt_text", "var(--twk-info-text)", "rgba(59,130,246,0.12)", "rgba(59,130,246,0.25)",
                hint="Cantidad de cobros cerrados en el período (no incluye anulados).",
            ),
            _kpi_card(
                "Ticket promedio",
                ReportesState.dashboard_ticket_promedio_texto,
                "calculator", "#7C3AED", "rgba(124,58,237,0.12)", "rgba(124,58,237,0.25)",
                hint="Ventas cobradas ÷ número de cobros del período.",
            ),
            _kpi_card(
                "Propinas",
                ReportesState.dashboard_propina_hoy_texto,
                "heart", "#EA580C", "rgba(234,88,12,0.12)", "rgba(234,88,12,0.25)",
                hint="Suma de propinas registradas en los cobros del período.",
            ),
            columns=rx.breakpoints(initial="2", md="4"),
            gap=rx.breakpoints(initial="10px", md="14px"),
            width="100%",
        ),

        # ── Top platos ────────────────────────────────────────────────────────
        rx.cond(
            ReportesState.dashboard_top_platos.length() > 0,
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.icon(tag="star", size=14, color=ACCENT),
                        rx.text("Top platos · " + ReportesState.dashboard_periodo_label,
                                font_size="13px", font_weight="700", color="var(--twk-slate-300)"),
                        spacing="2", align="center",
                    ),
                    rx.foreach(ReportesState.dashboard_top_platos, lambda plato, i: _top_plato_row(plato, i)),
                    spacing="2",
                    width="100%",
                ),
                background=PAGE_BACKGROUND,
                border=f"1px solid {DARK_700}",
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
                    rx.icon(tag="users", size=14, color=ACCENT),
                    rx.text("Ventas por mozo", font_size="13px", font_weight="700", color="var(--twk-slate-300)"),
                    spacing="2", align="center", margin_bottom="10px",
                ),
                rx.cond(
                    ReportesState.reporte_mozos.length() > 0,
                    _ventas_mozo_chart(),
                    rx.text("Sin ventas en el período.", font_size="12px", color=TEXT_MUTED),
                ),
                background=PAGE_BACKGROUND, border=f"1px solid {DARK_700}",
                border_radius="10px", padding="12px 14px", flex="1", min_width="260px",
            ),
            # Ventas por hora
            rx.box(
                rx.hstack(
                    rx.icon(tag="clock", size=14, color=ACCENT),
                    rx.text("Ventas por hora", font_size="13px", font_weight="700", color="var(--twk-slate-300)"),
                    spacing="2", align="center", margin_bottom="10px",
                ),
                rx.cond(
                    ReportesState.reporte_horas.length() > 0,
                    _ventas_hora_chart(),
                    rx.text("Sin ventas en el período.", font_size="12px", color=TEXT_MUTED),
                ),
                background=PAGE_BACKGROUND, border=f"1px solid {DARK_700}",
                border_radius="10px", padding="12px 14px", flex="1", min_width="260px",
            ),
            gap="12px", width="100%",
            direction=rx.breakpoints(initial="column", md="row"),
        ),
        # ── Propinas por mozo (ADM-04) ───────────────────────────────────────
        rx.box(
            rx.hstack(
                rx.hstack(
                    rx.icon(tag="hand_coins", size=14, color=WARNING_TEXT),
                    rx.text("Propinas por mozo", font_size="13px",
                            font_weight="700", color="var(--twk-slate-300)"),
                    spacing="2", align="center",
                ),
                rx.text(
                    "Total: " + ReportesState.reporte_propinas_total_texto,
                    font_size="13px", font_weight="800", color=WARNING_TEXT,
                ),
                width="100%", justify="between", align="center",
                margin_bottom="10px",
            ),
            rx.cond(
                ReportesState.reporte_propinas_total_texto != "S/ 0.00",
                rx.vstack(
                    rx.foreach(ReportesState.reporte_mozos, _propina_row),
                    spacing="0", width="100%",
                ),
                rx.text("Sin propinas registradas en el período.", font_size="12px",
                        color=TEXT_MUTED),
            ),
            background="rgba(245,158,11,0.10)", border="1px solid rgba(245,158,11,0.20)",
            border_radius="10px", padding="12px 14px", width="100%",
        ),
        # Desglose por método de pago
        rx.box(
            rx.hstack(
                rx.icon(tag="credit_card", size=14, color=ACCENT),
                rx.text("Desglose por método de pago", font_size="13px", font_weight="700", color="var(--twk-slate-300)"),
                spacing="2", align="center", margin_bottom="10px",
            ),
            rx.cond(
                ReportesState.reporte_metodos.length() > 0,
                rx.recharts.responsive_container(
                    rx.recharts.bar_chart(
                        rx.recharts.cartesian_grid(stroke_dasharray="3 3", stroke="var(--twk-d700)"),
                        rx.recharts.x_axis(
                            data_key="metodo", font_size=11, tick_line=False,
                            axis_line=False, stroke="var(--twk-slate-400)",
                        ),
                        rx.recharts.y_axis(
                            font_size=11, tick_line=False, axis_line=False,
                            stroke="var(--twk-slate-400)", width=70,
                        ),
                        rx.recharts.graphing_tooltip(
                            content_style={"fontSize": "12px", "borderRadius": "8px"},
                        ),
                        rx.recharts.bar(
                            data_key="total", fill=ACCENT, radius=[4, 4, 0, 0],
                            name="Total (S/)",
                        ),
                        rx.recharts.bar(
                            data_key="count", fill="#FB923C", radius=[4, 4, 0, 0],
                            name="Pagos",
                        ),
                        data=ReportesState.reporte_metodos,
                        margin={"top": 4, "right": 4, "left": 0, "bottom": 0},
                    ),
                    width="100%", height=220,
                ),
                rx.text("Sin pagos en el período.", font_size="12px", color=TEXT_MUTED),
            ),
            background=PAGE_BACKGROUND, border=f"1px solid {DARK_700}",
            border_radius="10px", padding="12px 14px", width="100%",
        ),
        # Comparativa entre períodos
        rx.box(
            rx.hstack(
                rx.icon(tag="git_compare_arrows", size=14, color=ACCENT),
                rx.text("Comparativa con período anterior", font_size="13px",
                        font_weight="700", color="var(--twk-slate-300)"),
                spacing="2", align="center", margin_bottom="10px",
            ),
            rx.grid(
                # Ventas
                rx.box(
                    rx.text("Ventas", font_size="11px", color=TEXT_MUTED, margin_bottom="2px"),
                    rx.text(ReportesState.comp_ventas_actual, font_size="18px",
                            font_weight="800", color=TEXT_PRIMARY),
                    rx.hstack(
                        rx.text(
                            "vs " + ReportesState.comp_ventas_anterior,
                            font_size="11px", color=TEXT_MUTED,
                        ),
                        rx.text(
                            rx.cond(ReportesState.comp_ventas_pct >= 0, "+", "") + ReportesState.comp_ventas_pct.to_string() + "%",
                            font_size="11px", font_weight="700",
                            color=rx.cond(ReportesState.comp_ventas_pct >= 0, "#16A34A", "#DC2626"),
                        ),
                        spacing="1", align="center",
                    ),
                    rx.text(ReportesState.comp_label_anterior, font_size="10px", color="var(--twk-slate-300)"),
                    padding="10px", background=DARK_800, border_radius="8px",
                    border=f"1px solid {DARK_700}",
                ),
                # Pedidos
                rx.box(
                    rx.text("Pedidos", font_size="11px", color=TEXT_MUTED, margin_bottom="2px"),
                    rx.text(ReportesState.comp_pedidos_actual.to_string(), font_size="18px",
                            font_weight="800", color=TEXT_PRIMARY),
                    rx.hstack(
                        rx.text(
                            "vs " + ReportesState.comp_pedidos_anterior.to_string(),
                            font_size="11px", color=TEXT_MUTED,
                        ),
                        rx.text(
                            rx.cond(ReportesState.comp_pedidos_diff >= 0, "+", "") + ReportesState.comp_pedidos_diff.to_string(),
                            font_size="11px", font_weight="700",
                            color=rx.cond(ReportesState.comp_pedidos_diff >= 0, "#16A34A", "#DC2626"),
                        ),
                        spacing="1", align="center",
                    ),
                    rx.text(ReportesState.comp_label_anterior, font_size="10px", color="var(--twk-slate-300)"),
                    padding="10px", background=DARK_800, border_radius="8px",
                    border=f"1px solid {DARK_700}",
                ),
                # Ticket promedio
                rx.box(
                    rx.text("Ticket promedio", font_size="11px", color=TEXT_MUTED, margin_bottom="2px"),
                    rx.text(ReportesState.comp_ticket_actual, font_size="18px",
                            font_weight="800", color=TEXT_PRIMARY),
                    rx.hstack(
                        rx.text(
                            "vs " + ReportesState.comp_ticket_anterior,
                            font_size="11px", color=TEXT_MUTED,
                        ),
                        rx.text(
                            rx.cond(ReportesState.comp_ticket_pct >= 0, "+", "") + ReportesState.comp_ticket_pct.to_string() + "%",
                            font_size="11px", font_weight="700",
                            color=rx.cond(ReportesState.comp_ticket_pct >= 0, "#16A34A", "#DC2626"),
                        ),
                        spacing="1", align="center",
                    ),
                    rx.text(ReportesState.comp_label_anterior, font_size="10px", color="var(--twk-slate-300)"),
                    padding="10px", background=DARK_800, border_radius="8px",
                    border=f"1px solid {DARK_700}",
                ),
                columns="3", spacing="3", width="100%",
            ),
            background=PAGE_BACKGROUND, border=f"1px solid {DARK_700}",
            border_radius="10px", padding="12px 14px", width="100%",
        ),
        # ── Control de productos (Standard) — stock + unidades vendidas ──────
        _productos_stock_section(),
        # ── Secciones avanzadas (requieren plan profesional) ────────────────
        rx.cond(
            FoodState.reportes_avanzados_habilitados,
            rx.fragment(
                _pyl_section(),
                _igv_section(),
                _matriz_section(),
                _descuentos_anulaciones_section(),
                _mermas_section(),
            ),
            upgrade_cta(
                titulo="Reportes avanzados — Plan Profesional",
                mensaje=(
                    "P&L, IGV, matriz de productos, descuentos/anulaciones y mermas "
                    "requieren el plan Profesional."
                ),
            ),
        ),

        # Margen por plato
        rx.box(
            rx.hstack(
                rx.icon(tag="chef_hat", size=14, color=ACCENT),
                rx.text("Margen por plato (precio vs costo de receta)",
                        font_size="13px", font_weight="700", color="var(--twk-slate-300)"),
                rx.spacer(),
                _excel_btn(ReportesState.exportar_margen_excel),
                spacing="2", align="center", margin_bottom="10px", width="100%",
            ),
            rx.cond(
                ReportesState.reporte_margen.length() > 0,
                rx.vstack(
                    rx.foreach(ReportesState.reporte_margen, _margen_row),
                    spacing="0", width="100%",
                ),
                rx.text(
                    "Carga recetas y costos de insumos en Inventario para ver el margen de cada plato.",
                    font_size="12px", color=TEXT_MUTED,
                ),
            ),
            background=PAGE_BACKGROUND, border=f"1px solid {DARK_700}",
            border_radius="10px", padding="12px 14px", width="100%",
        ),

        # ── Historial con filtros ─────────────────────────────────────────────
        rx.vstack(
            rx.hstack(
                rx.text("Historial de ventas", font_size="15px", font_weight="700", color=TEXT_PRIMARY),
                rx.cond(
                    ReportesState.historial_ventas.length() > 0,
                    rx.badge(
                        ReportesState.historial_ventas.length().to_string() + " registros",
                        background=DARK_800,
                        color=TEXT_MUTED,
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
                ReportesState.historial_ventas.length() == 0,
                rx.center(
                    rx.vstack(
                        rx.icon(tag="inbox", size=32, color="var(--twk-slate-300)"),
                        rx.text(
                            rx.cond(
                                ReportesState.historial_filtro_activo,
                                "Sin resultados para los filtros aplicados.",
                                "Sin ventas registradas.",
                            ),
                            font_size="14px", color=TEXT_MUTED, text_align="center",
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
                        background=PAGE_BACKGROUND,
                        border_bottom=f"1px solid {DARK_700}",
                        padding_y="4px",
                    ),
                    rx.foreach(ReportesState.historial_ventas, _venta_row),
                    # Controles de paginación
                    rx.hstack(
                        rx.tooltip(
                            rx.button(
                                rx.icon(tag="chevron_left", size=14),
                                on_click=ReportesState.historial_pagina_anterior,
                                background=DARK_800,
                                color=TEXT_MUTED,
                                border=f"1px solid {DARK_700}",
                                border_radius="7px",
                                padding_x="10px",
                                padding_y="6px",
                                cursor="pointer",
                                disabled=~ReportesState.historial_tiene_anterior,
                                opacity=rx.cond(ReportesState.historial_tiene_anterior, "1", "0.4"),
                                _hover={"background": DARK_700},
                            ),
                            content="Página anterior",
                        ),
                        rx.text(
                            ReportesState.historial_pagina_label,
                            font_size="12px",
                            color=TEXT_MUTED,
                            flex="1",
                            text_align="center",
                        ),
                        rx.tooltip(
                            rx.button(
                                rx.icon(tag="chevron_right", size=14),
                                on_click=ReportesState.historial_pagina_siguiente,
                                background=DARK_800,
                                color=TEXT_MUTED,
                                border=f"1px solid {DARK_700}",
                                border_radius="7px",
                                padding_x="10px",
                                padding_y="6px",
                                cursor="pointer",
                                disabled=~ReportesState.historial_tiene_siguiente,
                                opacity=rx.cond(ReportesState.historial_tiene_siguiente, "1", "0.4"),
                                _hover={"background": DARK_700},
                            ),
                            content="Página siguiente",
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


@rx.page(route="/reportes", on_load=ReportesState.on_load_reportes, title="TUWAYKIFOOD | Reportes")
def reportes_page() -> rx.Component:
    return rx.cond(
        FoodState.pagina_cargada,
        app_shell(_reportes_content(), page_key="reportes"),
        app_shell(loading_placeholder(), page_key="reportes"),
    )
