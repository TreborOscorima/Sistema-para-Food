"""Pagina de caja — turno con arqueo, cobro de mesas con método de pago y propina."""

from __future__ import annotations

import reflex as rx

from app.components.shared import anulacion_modal, app_shell, cumpleanos_banner
from app.states.caja_turno_mixin import (
    DenominacionRow,
    MovimientoCajaView,
    ResumenCierreRow,
    TurnoHistorialView,
)
from app.states.food_state import FoodState, MesaView, CajaItemView, PagoStagedView

_METODOS = [
    ("efectivo", "Efectivo", "💵"),
    ("tarjeta", "Tarjeta", "💳"),
    ("qr", "QR / Yape", "📱"),
    ("fiado", "Fiado / CC", "📒"),
]


def _metodo_btn(value: str, label: str, icon: str) -> rx.Component:
    activo = FoodState.caja_cobro_metodo == value
    return rx.box(
        rx.text(icon, font_size="18px", line_height="1"),
        rx.text(label, font_size="12px", font_weight="700",
                color=rx.cond(activo, "#FFFFFF", "#64748B")),
        on_click=FoodState.set_caja_cobro_metodo(value),
        background=rx.cond(activo, "#0F172A", "#FFFFFF"),
        border=rx.cond(activo, "2px solid #EA580C", "2px solid #E2E8F0"),
        border_radius="10px",
        padding="12px 4px",
        cursor="pointer",
        display="flex",
        flex_direction="column",
        align_items="center",
        gap="4px",
        transition="all 0.15s ease",
        _hover={"border": "2px solid #EA580C"},
    )


def _caja_item_row(item: CajaItemView) -> rx.Component:
    return rx.box(
        rx.grid(
            rx.vstack(
                rx.text(item.producto_nombre, font_size="13px", font_weight="600", color="#0F172A"),
                rx.cond(
                    item.notas != "",
                    rx.text(item.notas, font_size="11px", color="#64748B"),
                    rx.text(item.precio_unitario_texto + " c/u", font_size="11px", color="#64748B"),
                ),
                spacing="0", align="start",
            ),
            rx.text("×" + item.cantidad.to_string(), font_size="13px", font_weight="600",
                    color="#334155", text_align="center"),
            rx.text(item.subtotal_texto, font_size="13px", font_weight="700",
                    color="#0F172A", text_align="right"),
            columns="1fr 50px 80px",
            gap="8px", align_items="center", width="100%",
        ),
        padding="12px 16px",
        border_bottom="1px solid #F8FAFC",
        width="100%",
    )


def _pago_staged_chip(pago: PagoStagedView, idx) -> rx.Component:
    return rx.hstack(
        rx.text(pago.metodo_label, font_size="12px", font_weight="700", color="#334155"),
        rx.text(pago.monto_texto, font_size="12px", font_weight="800", color="#0F172A"),
        rx.icon(
            tag="x", size=13, color="#94A3B8", cursor="pointer",
            on_click=FoodState.quitar_pago_staged(idx),
        ),
        spacing="2", align="center",
        background="#F8FAFC", border="1px solid #E2E8F0",
        border_radius="20px", padding="6px 12px",
    )


def _pagos_divididos_panel() -> rx.Component:
    """Panel de pagos múltiples: cuenta dividida entre comensales o pago mixto."""
    return rx.box(
        rx.text("Pagos de la cuenta", font_size="12px", font_weight="700", color="#64748B",
                text_transform="uppercase", letter_spacing="0.05em", margin_bottom="12px"),
        rx.vstack(
            rx.hstack(
                rx.select(
                    ["efectivo", "tarjeta", "qr", "fiado"],
                    value=FoodState.caja_pago_staged_metodo,
                    on_change=FoodState.set_caja_pago_staged_metodo,
                    width="130px",
                ),
                rx.input(
                    placeholder="Monto (vacío = restante)",
                    value=FoodState.caja_pago_staged_monto,
                    on_change=FoodState.set_caja_pago_staged_monto,
                    type="number", min="0", step="0.50",
                    flex="1",
                    background="#F8FAFC", border="1px solid #E2E8F0",
                    border_radius="8px", font_size="13px",
                    padding_x="10px",
                    _focus={"border_color": "#EA580C"},
                ),
                rx.button(
                    "Agregar",
                    on_click=FoodState.agregar_pago_staged,
                    background="#EA580C", color="#FFFFFF",
                    border_radius="8px", font_size="13px", font_weight="700",
                    cursor="pointer", _hover={"background": "#C2410C"},
                ),
                spacing="2", width="100%", align="center",
            ),
            rx.cond(
                FoodState.caja_pagos_staged.length() > 0,
                rx.flex(
                    rx.foreach(FoodState.caja_pagos_staged, _pago_staged_chip),
                    gap="8px", width="100%", flex_wrap="wrap",
                ),
                rx.text("Agrega un pago por comensal o por método.",
                        font_size="12px", color="#94A3B8"),
            ),
            rx.hstack(
                rx.cond(
                    FoodState.caja_pagos_cubierto,
                    rx.badge(
                        "Cuenta cubierta ✓", background="#DCFCE7", color="#166534",
                        border_radius="8px", font_size="12px", font_weight="700",
                        padding_x="10px", padding_y="4px",
                    ),
                    rx.badge(
                        "Restante: " + FoodState.caja_pagos_restante_texto,
                        background="#FEF3C7", color="#92400E",
                        border_radius="8px", font_size="12px", font_weight="700",
                        padding_x="10px", padding_y="4px",
                    ),
                ),
                rx.spacer(),
                rx.cond(
                    FoodState.caja_pagos_vuelto_texto != "",
                    rx.text("Vuelto: " + FoodState.caja_pagos_vuelto_texto,
                            font_size="13px", font_weight="700", color="#15803D"),
                    rx.fragment(),
                ),
                width="100%", align="center",
            ),
            spacing="3", width="100%",
        ),
        background="#FFFFFF", border="1px solid #E2E8F0",
        border_radius="14px", padding="18px", width="100%",
    )


def _cobro_panel() -> rx.Component:
    return rx.vstack(
        # Header mesa
        rx.hstack(
            rx.vstack(
                rx.text(FoodState.caja_cobro_mesa_nombre, font_size="20px", font_weight="800", color="#0F172A"),
                rx.text("Consumo pendiente de cobro", font_size="13px", color="#64748B"),
                spacing="0",
            ),
            rx.spacer(),
            rx.badge(
                "Cuenta pedida", background="#FEE2E2", color="#DC2626",
                border_radius="20px", font_size="12px", font_weight="700",
                padding_x="14px", padding_y="6px",
            ),
            width="100%", align="center",
        ),
        # Banner de error de cobro
        rx.cond(
            FoodState.caja_cobro_error != "",
            rx.hstack(
                rx.icon(tag="circle_alert", size=14, color="#B91C1C"),
                rx.text(FoodState.caja_cobro_error, font_size="12px", color="#B91C1C", font_weight="600"),
                spacing="2", align="center",
                background="#FEF2F2", border="1px solid #FECACA",
                border_radius="8px", padding="10px 12px", width="100%",
            ),
            rx.fragment(),
        ),
        # Items
        rx.box(
            rx.hstack(
                rx.text("Producto", font_size="11px", font_weight="700", color="#94A3B8",
                        text_transform="uppercase", letter_spacing="0.05em", flex="1"),
                rx.text("Cant.", font_size="11px", font_weight="700", color="#94A3B8",
                        text_transform="uppercase", letter_spacing="0.05em", width="50px", text_align="center"),
                rx.text("Total", font_size="11px", font_weight="700", color="#94A3B8",
                        text_transform="uppercase", letter_spacing="0.05em", width="80px", text_align="right"),
                width="100%", padding="12px 16px",
                border_bottom="1px solid #F1F5F9",
            ),
            rx.cond(
                FoodState.caja_cobro_items.length() > 0,
                rx.vstack(
                    rx.foreach(FoodState.caja_cobro_items, _caja_item_row),
                    spacing="0", width="100%",
                ),
                rx.center(
                    rx.text("Sin items registrados.", font_size="13px", color="#94A3B8"),
                    padding_y="16px", width="100%",
                ),
            ),
            background="#FFFFFF", border="1px solid #E2E8F0",
            border_radius="14px", width="100%", overflow="hidden",
        ),
        # Subtotal + descuento + total
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.text("Consumo", font_size="14px", color="#64748B"),
                    rx.spacer(),
                    rx.text(FoodState.caja_cobro_total_base_texto, font_size="14px",
                            font_weight="600", color="#334155"),
                    width="100%", align="center",
                ),
                rx.hstack(
                    rx.text("Descuento S/", font_size="14px", color="#64748B"),
                    rx.spacer(),
                    rx.input(
                        placeholder="0.00",
                        value=FoodState.caja_cobro_descuento,
                        on_change=FoodState.set_caja_cobro_descuento,
                        type="number", min="0", step="0.50",
                        background="#F8FAFC", border="1px solid #E2E8F0",
                        border_radius="7px", font_size="13px",
                        padding_x="10px", padding_y="6px", width="110px",
                        text_align="right",
                        _focus={"border_color": "#EA580C"},
                    ),
                    width="100%", align="center",
                ),
                rx.hstack(
                    rx.text("Propina (opcional) S/", font_size="14px", color="#64748B"),
                    rx.spacer(),
                    rx.input(
                        placeholder="0.00",
                        value=FoodState.caja_cobro_propina,
                        on_change=FoodState.set_caja_cobro_propina,
                        type="number", min="0", step="0.50",
                        background="#F8FAFC", border="1px solid #E2E8F0",
                        border_radius="7px", font_size="13px",
                        padding_x="10px", padding_y="6px", width="110px",
                        text_align="right",
                        _focus={"border_color": "#EA580C"},
                    ),
                    width="100%", align="center",
                ),
                rx.box(border_top="2px solid #F1F5F9", width="100%", padding_top="4px"),
                rx.hstack(
                    rx.text("Total a pagar", font_size="16px", font_weight="700", color="#0F172A"),
                    rx.spacer(),
                    rx.text(FoodState.caja_cobro_total_final_texto, font_size="26px",
                            font_weight="900", color="#EA580C", letter_spacing="-0.5px"),
                    width="100%", align="center",
                ),
                spacing="3", width="100%",
            ),
            background="#FFFFFF", border="1px solid #E2E8F0",
            border_radius="14px", padding="18px", width="100%",
        ),
        # Toggle cuenta dividida / pago mixto
        rx.hstack(
            rx.switch(
                checked=FoodState.caja_cobro_dividido,
                on_change=FoodState.set_caja_cobro_dividido,
                color_scheme="orange",
            ),
            rx.text("Dividir cuenta / pago mixto", font_size="13px",
                    font_weight="700", color="#334155"),
            rx.text("(varios métodos o por comensal)", font_size="12px", color="#94A3B8"),
            spacing="2", align="center", width="100%",
        ),
        # Método de pago único (modo simple)
        rx.cond(
            FoodState.caja_cobro_dividido,
            _pagos_divididos_panel(),
            rx.box(
                rx.text("Método de pago", font_size="12px", font_weight="700", color="#64748B",
                        text_transform="uppercase", letter_spacing="0.05em", margin_bottom="12px"),
                rx.grid(
                    *[_metodo_btn(v, l, i) for v, l, i in _METODOS],
                    columns="4", gap="8px", width="100%",
                ),
                background="#FFFFFF", border="1px solid #E2E8F0",
                border_radius="14px", padding="18px", width="100%",
            ),
        ),
        # Selector de cliente (fiado simple o fiado dentro del pago dividido)
        rx.cond(
            FoodState.caja_cobro_es_fiado | FoodState.caja_pagos_tiene_fiado,
            rx.vstack(
                rx.hstack(
                    rx.text("Cliente", font_size="13px", font_weight="700", color="#334155"),
                    rx.text("*", font_size="13px", font_weight="700", color="#DC2626"),
                    rx.text("(requerido para fiado)", font_size="12px", color="#94A3B8"),
                    spacing="1", align="center",
                ),
                rx.select(
                    FoodState.clientes_activos_nombres,
                    value=FoodState.caja_cobro_cliente_nombre,
                    on_change=FoodState.set_caja_cobro_cliente_nombre,
                    placeholder="— Seleccionar cliente —",
                    background="#FFFFFF", color="#0F172A",
                    border="2px solid #EA580C", border_radius="8px",
                    font_size="14px", width="100%",
                ),
                spacing="2", width="100%",
                background="#FFFFFF", border="1px solid #E2E8F0",
                border_radius="14px", padding="18px",
            ),
            rx.fragment(),
        ),
        # Banner de promo aplicada automáticamente
        rx.cond(
            FoodState.caja_promo_aplicada_nombre != "",
            rx.box(
                rx.hstack(
                    rx.icon(tag="badge_percent", size=14, color="#16A34A"),
                    rx.vstack(
                        rx.text(
                            "Promo aplicada: " + FoodState.caja_promo_aplicada_nombre,
                            font_size="12px", font_weight="700", color="#0F172A",
                        ),
                        rx.text(
                            FoodState.caja_promo_aplicada_texto + " ya descontado del total",
                            font_size="11px", color="#166534",
                        ),
                        spacing="0", align="start",
                    ),
                    rx.spacer(),
                    rx.button(
                        "Quitar",
                        on_click=FoodState.quitar_promo_aplicada,
                        background="#FFFFFF", color="#64748B",
                        border="1px solid #E2E8F0", border_radius="6px",
                        font_size="12px", font_weight="600",
                        padding_x="12px", padding_y="6px", cursor="pointer",
                        _hover={"border_color": "#DC2626", "color": "#DC2626"},
                    ),
                    width="100%", align="center", gap="8px",
                ),
                background="#F0FDF4", border="1px solid #BBF7D0",
                border_radius="10px", padding="12px 14px", width="100%",
            ),
            rx.fragment(),
        ),
        # Banner de promo activa (sugerencia manual, si no hay auto aplicada)
        rx.cond(
            FoodState.hay_promo_activa & (FoodState.caja_promo_aplicada_nombre == ""),
            rx.box(
                rx.hstack(
                    rx.icon(tag="zap", size=13, color="#EA580C"),
                    rx.vstack(
                        rx.text(
                            "Promo activa: " + FoodState.promo_activa_nombre,
                            font_size="12px", font_weight="700", color="#0F172A",
                        ),
                        rx.text(FoodState.promo_activa_descuento_texto,
                                font_size="11px", color="#C2410C"),
                        spacing="0", align="start",
                    ),
                    rx.spacer(),
                    rx.button(
                        "Aplicar",
                        on_click=FoodState.aplicar_promo_al_cobro,
                        background="#EA580C", color="#FFFFFF",
                        border_radius="6px", font_size="12px", font_weight="700",
                        padding_x="12px", padding_y="6px", cursor="pointer",
                        _hover={"opacity": "0.9"},
                    ),
                    width="100%", align="center", gap="8px",
                ),
                background="#FFF7ED", border="1px solid #FED7AA",
                border_radius="10px", padding="12px 14px", width="100%",
            ),
            rx.fragment(),
        ),
        # Monto recibido (solo efectivo en modo simple)
        rx.cond(
            FoodState.caja_cobro_es_efectivo & ~FoodState.caja_cobro_dividido,
            rx.box(
                rx.vstack(
                    rx.text("Efectivo recibido S/", font_size="13px", font_weight="700", color="#64748B"),
                    rx.input(
                        placeholder="0.00",
                        value=FoodState.caja_cobro_efectivo_recibido,
                        on_change=FoodState.set_caja_cobro_efectivo_recibido,
                        type="number", min="0", step="0.50",
                        background="#F8FAFC", border="1px solid #E2E8F0",
                        border_radius="8px", padding_x="12px", padding_y="8px",
                        font_size="14px", width="100%",
                        _focus={"border_color": "#EA580C"},
                    ),
                    rx.cond(
                        FoodState.caja_cobro_efectivo_recibido != "",
                        rx.hstack(
                            rx.text("Vuelto:", font_size="13px", color="#64748B"),
                            rx.spacer(),
                            rx.text(FoodState.caja_cobro_vuelto_texto,
                                    font_size="16px", font_weight="700", color="#15803D"),
                            width="100%", align="center", padding="8px 12px",
                            background="#F0FDF4", border="1px solid #BBF7D0",
                            border_radius="8px",
                        ),
                        rx.fragment(),
                    ),
                    spacing="2", width="100%",
                ),
                background="#FFFFFF", border="1px solid #E2E8F0",
                border_radius="14px", padding="18px", width="100%",
            ),
            rx.fragment(),
        ),
        # Botones
        rx.hstack(
            rx.button(
                rx.hstack(rx.icon(tag="ban", size=14), rx.text("Anular"),
                          spacing="1", align="center"),
                on_click=FoodState.abrir_anulacion_pedido_abierto(FoodState.caja_cobro_mesa_id),
                background="#FFFFFF", color="#DC2626",
                border="1px solid #FECACA", border_radius="12px",
                font_size="14px", font_weight="600", padding_y="14px",
                cursor="pointer", _hover={"background": "#FEF2F2"}, flex="1",
            ),
            rx.button(
                "Cancelar",
                on_click=FoodState.cancelar_cobro,
                background="#FFFFFF", color="#64748B",
                border="1px solid #E2E8F0", border_radius="12px",
                font_size="14px", font_weight="600", padding_y="14px",
                cursor="pointer", _hover={"background": "#F8FAFC"}, flex="1",
            ),
            rx.button(
                "Confirmar cobro · " + FoodState.caja_cobro_total_final_texto,
                on_click=FoodState.confirmar_cobro,
                background="#EA580C", color="#FFFFFF",
                border_radius="12px", font_size="15px", font_weight="800",
                padding_y="14px", cursor="pointer",
                _hover={"background": "#C2410C"}, flex="2",
            ),
            spacing="3", width="100%",
        ),
        spacing="4", width="100%",
    )


def _mesa_sidebar_row(mesa: MesaView) -> rx.Component:
    seleccionada = FoodState.caja_cobro_mesa_id == mesa.id
    return rx.box(
        rx.hstack(
            rx.vstack(
                rx.text(
                    mesa.nombre, font_size="15px", font_weight="700",
                    color=rx.cond(seleccionada, "#EA580C", "#334155"),
                ),
                rx.text(
                    mesa.items_total_count.to_string() + " items · " + mesa.tiempo_abierto_texto,
                    font_size="12px", color="#64748B",
                ),
                spacing="0", align="start",
            ),
            rx.spacer(),
            rx.text(
                mesa.total_abierto_texto, font_size="17px", font_weight="800",
                color=rx.cond(seleccionada, "#0F172A", "#334155"),
            ),
            width="100%", align="center",
        ),
        on_click=FoodState.abrir_cobro_mesa(mesa.id),
        padding="14px 16px",
        background=rx.cond(seleccionada, "#FFF7ED", "#FFFFFF"),
        border_left=rx.cond(seleccionada, "3px solid #EA580C", "3px solid transparent"),
        border_bottom="1px solid #F1F5F9",
        cursor="pointer",
        width="100%",
        _hover={"background": rx.cond(seleccionada, "#FFF7ED", "#F8FAFC")},
    )


def _mesas_sidebar() -> rx.Component:
    mesas_cobrables = FoodState.mesas_por_cobrar
    return rx.box(
        rx.box(
            rx.text("Mesas por cobrar", font_size="11px", font_weight="700", color="#94A3B8",
                    text_transform="uppercase", letter_spacing="0.05em"),
            padding="16px", border_bottom="1px solid #F1F5F9",
        ),
        rx.cond(
            mesas_cobrables.length() > 0,
            rx.vstack(
                rx.foreach(mesas_cobrables, _mesa_sidebar_row),
                spacing="0", width="100%",
            ),
            rx.center(
                rx.text("No hay mesas abiertas.", font_size="13px", color="#94A3B8"),
                padding_y="30px", width="100%",
            ),
        ),
        background="#FFFFFF",
        border="1px solid #E2E8F0",
        border_radius="14px",
        width=rx.breakpoints(initial="100%", lg="280px"),
        min_width=rx.breakpoints(initial="100%", lg="280px"),
        max_height=rx.breakpoints(initial="none", lg="calc(100vh - 180px)"),
        overflow_y="auto",
        flex_shrink="0",
    )


def _resumen_dia() -> rx.Component:
    return rx.box(
        rx.text("Resumen del día", font_size="12px", font_weight="700", color="#94A3B8",
                text_transform="uppercase", letter_spacing="0.05em", margin_bottom="16px"),
        rx.vstack(
            rx.box(
                rx.text("Ventas", font_size="11px", color="#94A3B8", font_weight="600"),
                rx.text(FoodState.dashboard_ventas_hoy_texto, font_size="22px", font_weight="800",
                        color="#0F172A", letter_spacing="-0.5px"),
                rx.text(
                    rx.cond(FoodState.dashboard_ventas_trend_pct >= 0, "↑ ", "↓ ")
                    + FoodState.dashboard_ventas_trend_pct.to_string() + "% vs ayer",
                    font_size="11px", font_weight="600",
                    color=rx.cond(FoodState.dashboard_ventas_trend_pct >= 0, "#16A34A", "#DC2626"),
                ),
                background="#F8FAFC", border_radius="10px", padding="14px", width="100%",
            ),
            rx.box(
                rx.text("Pedidos cobrados", font_size="11px", color="#94A3B8", font_weight="600"),
                rx.text(FoodState.dashboard_pedidos_hoy.to_string(), font_size="22px",
                        font_weight="800", color="#0F172A"),
                background="#F8FAFC", border_radius="10px", padding="14px", width="100%",
            ),
            rx.box(
                rx.text("Propinas", font_size="11px", color="#94A3B8", font_weight="600"),
                rx.text(FoodState.dashboard_propina_hoy_texto, font_size="22px",
                        font_weight="800", color="#0F172A"),
                background="#F8FAFC", border_radius="10px", padding="14px", width="100%",
            ),
            rx.link(
                rx.center(
                    rx.text("Ver reportes del día", font_size="13px", font_weight="600", color="#64748B"),
                    padding="12px", width="100%",
                ),
                href="/reportes",
                border="1px solid #E2E8F0", border_radius="10px", width="100%",
                _hover={"background": "#F8FAFC"},
            ),
            spacing="3", width="100%",
        ),
        background="#FFFFFF",
        border="1px solid #E2E8F0",
        border_radius="14px",
        padding="18px",
        width=rx.breakpoints(initial="100%", lg="260px"),
        min_width=rx.breakpoints(initial="100%", lg="260px"),
        flex_shrink="0",
    )


def _panel_central() -> rx.Component:
    return rx.box(
        rx.cond(
            FoodState.caja_cobro_activo,
            _cobro_panel(),
            rx.center(
                rx.vstack(
                    rx.icon(tag="credit_card", size=32, color="#CBD5E1"),
                    rx.text("Seleccioná una mesa para cobrar", font_size="14px", color="#94A3B8"),
                    spacing="2", align="center",
                ),
                padding_y="80px", width="100%",
            ),
        ),
        flex="1", min_width="0", width="100%",
    )


# ─── Turno de caja ────────────────────────────────────────────────────────────

def _turno_cerrado_card() -> rx.Component:
    """Card de apertura de turno cuando no hay ninguno abierto."""
    return rx.box(
        rx.hstack(
            rx.icon(tag="lock", size=18, color="#D97706"),
            rx.vstack(
                rx.text("Caja cerrada", font_size="15px", font_weight="800", color="#0F172A"),
                rx.text("Abre el turno con el fondo inicial para empezar a cobrar.",
                        font_size="12px", color="#64748B"),
                spacing="0", align="start",
            ),
            rx.spacer(),
            rx.hstack(
                rx.input(
                    placeholder="Fondo inicial S/",
                    value=FoodState.turno_apertura_monto,
                    on_change=FoodState.set_turno_apertura_monto,
                    type="number", min="0", step="0.50",
                    background="#FFFFFF", border="1px solid #E2E8F0",
                    border_radius="8px", padding_x="12px", padding_y="8px",
                    font_size="13px", width="150px",
                    _focus={"border_color": "#EA580C"},
                ),
                rx.button(
                    "Abrir turno",
                    on_click=FoodState.abrir_turno,
                    background="#EA580C", color="#FFFFFF",
                    border_radius="8px", font_size="13px", font_weight="700",
                    padding_x="16px", cursor="pointer",
                    _hover={"background": "#C2410C"},
                ),
                rx.button(
                    "Historial",
                    on_click=FoodState.toggle_historial_turnos,
                    background="#FFFFFF", color="#64748B",
                    border="1px solid #E2E8F0", border_radius="8px",
                    font_size="13px", font_weight="600", cursor="pointer",
                    _hover={"border_color": "#EA580C"},
                ),
                spacing="2", align="center",
            ),
            width="100%", align="center", gap="12px",
            flex_wrap="wrap",
        ),
        rx.cond(
            FoodState.turno_error != "",
            rx.text(FoodState.turno_error, font_size="12px", color="#B91C1C",
                    font_weight="600", margin_top="8px"),
            rx.fragment(),
        ),
        background="#FFFBEB", border="1px solid #FDE68A",
        border_radius="14px", padding="14px 18px", width="100%",
    )


def _turno_abierto_bar() -> rx.Component:
    """Barra de estado cuando el turno está abierto."""
    return rx.box(
        rx.hstack(
            rx.icon(tag="badge_check", size=18, color="#16A34A"),
            rx.vstack(
                rx.text("Turno abierto", font_size="14px", font_weight="800", color="#0F172A"),
                rx.text(
                    "Desde " + FoodState.turno_abierto_desde_texto
                    + " · por " + FoodState.turno_abierto_por_nombre
                    + " · Fondo " + FoodState.turno_fondo_texto,
                    font_size="12px", color="#64748B",
                ),
                spacing="0", align="start",
            ),
            rx.spacer(),
            rx.hstack(
                rx.button(
                    rx.hstack(rx.icon(tag="arrow_down_up", size=14), rx.text("Ingresos / Gastos"),
                              spacing="1", align="center"),
                    on_click=FoodState.abrir_mov_modal,
                    background="#FFFFFF", color="#334155",
                    border="1px solid #E2E8F0", border_radius="8px",
                    font_size="13px", font_weight="600", cursor="pointer",
                    _hover={"border_color": "#EA580C"},
                ),
                rx.button(
                    "Historial",
                    on_click=FoodState.toggle_historial_turnos,
                    background="#FFFFFF", color="#64748B",
                    border="1px solid #E2E8F0", border_radius="8px",
                    font_size="13px", font_weight="600", cursor="pointer",
                    _hover={"border_color": "#EA580C"},
                ),
                rx.button(
                    rx.hstack(rx.icon(tag="lock", size=14), rx.text("Cerrar turno"),
                              spacing="1", align="center"),
                    on_click=FoodState.abrir_cierre_turno,
                    background="#0F172A", color="#FFFFFF",
                    border_radius="8px", font_size="13px", font_weight="700",
                    cursor="pointer", _hover={"opacity": "0.9"},
                ),
                spacing="2", align="center",
            ),
            width="100%", align="center", gap="12px",
            flex_wrap="wrap",
        ),
        background="#F0FDF4", border="1px solid #BBF7D0",
        border_radius="14px", padding="12px 18px", width="100%",
    )


def _turno_banner() -> rx.Component:
    return rx.cond(FoodState.turno_caja_abierto, _turno_abierto_bar(), _turno_cerrado_card())


def _mov_row(mov: MovimientoCajaView) -> rx.Component:
    es_ingreso = mov.tipo == "ingreso"
    return rx.hstack(
        rx.badge(
            mov.tipo_label,
            background=rx.cond(es_ingreso, "#DCFCE7", "#FEE2E2"),
            color=rx.cond(es_ingreso, "#166534", "#B91C1C"),
            border_radius="6px", font_size="11px", font_weight="700",
        ),
        rx.vstack(
            rx.text(mov.motivo, font_size="13px", font_weight="600", color="#0F172A"),
            rx.text(mov.categoria + " · " + mov.hora_texto + " · " + mov.usuario,
                    font_size="11px", color="#94A3B8"),
            spacing="0", align="start",
        ),
        rx.spacer(),
        rx.text(
            rx.cond(es_ingreso, "+", "-") + mov.monto_texto,
            font_size="14px", font_weight="800",
            color=rx.cond(es_ingreso, "#16A34A", "#DC2626"),
        ),
        width="100%", align="center", gap="10px",
        padding="10px 12px", border_bottom="1px solid #F1F5F9",
    )


def _mov_modal() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.hstack(
                    rx.text("Movimientos de caja", font_size="18px", font_weight="800", color="#0F172A"),
                    rx.spacer(),
                    rx.icon(tag="x", size=18, color="#64748B", cursor="pointer",
                            on_click=FoodState.cerrar_mov_modal),
                    width="100%", align="center",
                ),
                rx.hstack(
                    rx.text("Ingresos: " + FoodState.turno_ingresos_texto,
                            font_size="12px", font_weight="700", color="#16A34A"),
                    rx.text("Egresos: " + FoodState.turno_egresos_texto,
                            font_size="12px", font_weight="700", color="#DC2626"),
                    spacing="4",
                ),
                # Formulario
                rx.box(
                    rx.vstack(
                        rx.hstack(
                            rx.select(
                                ["egreso", "ingreso"],
                                value=FoodState.turno_mov_tipo,
                                on_change=FoodState.set_turno_mov_tipo,
                                width="120px",
                            ),
                            rx.select(
                                FoodState.turno_mov_categorias,
                                value=FoodState.turno_mov_categoria,
                                on_change=FoodState.set_turno_mov_categoria,
                                width="170px",
                            ),
                            rx.input(
                                placeholder="Monto S/",
                                value=FoodState.turno_mov_monto,
                                on_change=FoodState.set_turno_mov_monto,
                                type="number", min="0", step="0.50",
                                width="110px",
                                background="#FFFFFF", border="1px solid #E2E8F0",
                                border_radius="8px", font_size="13px",
                                _focus={"border_color": "#EA580C"},
                            ),
                            spacing="2", width="100%", flex_wrap="wrap",
                        ),
                        rx.hstack(
                            rx.input(
                                placeholder="Motivo (ej: compra de mercado)",
                                value=FoodState.turno_mov_motivo,
                                on_change=FoodState.set_turno_mov_motivo,
                                flex="1",
                                background="#FFFFFF", border="1px solid #E2E8F0",
                                border_radius="8px", font_size="13px",
                                _focus={"border_color": "#EA580C"},
                            ),
                            rx.button(
                                "Registrar",
                                on_click=FoodState.guardar_movimiento_caja,
                                background="#EA580C", color="#FFFFFF",
                                border_radius="8px", font_size="13px", font_weight="700",
                                cursor="pointer", _hover={"background": "#C2410C"},
                            ),
                            spacing="2", width="100%",
                        ),
                        rx.cond(
                            FoodState.turno_mov_error != "",
                            rx.text(FoodState.turno_mov_error, font_size="12px",
                                    color="#B91C1C", font_weight="600"),
                            rx.fragment(),
                        ),
                        spacing="2", width="100%",
                    ),
                    background="#F8FAFC", border="1px solid #E2E8F0",
                    border_radius="10px", padding="12px", width="100%",
                ),
                # Lista
                rx.box(
                    rx.cond(
                        FoodState.turno_movimientos.length() > 0,
                        rx.vstack(
                            rx.foreach(FoodState.turno_movimientos, _mov_row),
                            spacing="0", width="100%",
                        ),
                        rx.center(
                            rx.text("Sin movimientos en este turno.", font_size="13px", color="#94A3B8"),
                            padding_y="20px", width="100%",
                        ),
                    ),
                    max_height="260px", overflow_y="auto", width="100%",
                    border="1px solid #F1F5F9", border_radius="10px",
                ),
                spacing="3", width="100%",
            ),
            class_name="light", max_width="560px",
        ),
        open=FoodState.turno_mov_modal_visible,
        on_open_change=FoodState.set_turno_mov_modal_visible,
    )


def _denominacion_row(row: DenominacionRow) -> rx.Component:
    return rx.hstack(
        rx.text(row.etiqueta, font_size="13px", color="#334155", width="140px"),
        rx.input(
            placeholder="0",
            value=row.cantidad,
            on_change=lambda v: FoodState.set_conteo_denominacion(row.key, v),
            type="number", min="0", step="1",
            width="70px", text_align="center",
            background="#FFFFFF", border="1px solid #E2E8F0",
            border_radius="7px", font_size="13px",
            _focus={"border_color": "#EA580C"},
        ),
        rx.spacer(),
        rx.text(row.subtotal_texto, font_size="13px", font_weight="700", color="#0F172A"),
        width="100%", align="center", gap="8px",
    )


def _resumen_cierre_row(row: ResumenCierreRow) -> rx.Component:
    return rx.hstack(
        rx.text(row.etiqueta, font_size="13px", color="#64748B"),
        rx.spacer(),
        rx.text(row.monto_texto, font_size="13px", font_weight="700", color="#334155"),
        width="100%", align="center",
    )


def _cierre_modal() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.text("Cierre de turno — Arqueo", font_size="18px", font_weight="800", color="#0F172A"),
                rx.flex(
                    # Columna resumen
                    rx.box(
                        rx.text("Resumen del turno", font_size="11px", font_weight="700",
                                color="#94A3B8", text_transform="uppercase",
                                letter_spacing="0.05em", margin_bottom="10px"),
                        rx.vstack(
                            rx.foreach(FoodState.turno_cierre_resumen, _resumen_cierre_row),
                            rx.box(border_top="2px solid #E2E8F0", width="100%", padding_top="4px"),
                            rx.hstack(
                                rx.text("Efectivo esperado en caja", font_size="14px",
                                        font_weight="800", color="#0F172A"),
                                rx.spacer(),
                                rx.text(FoodState.turno_cierre_esperado_texto, font_size="16px",
                                        font_weight="900", color="#EA580C"),
                                width="100%", align="center",
                            ),
                            spacing="2", width="100%",
                        ),
                        background="#F8FAFC", border="1px solid #E2E8F0",
                        border_radius="10px", padding="14px", flex="1", min_width="240px",
                    ),
                    # Columna arqueo
                    rx.box(
                        rx.text("Conteo de efectivo", font_size="11px", font_weight="700",
                                color="#94A3B8", text_transform="uppercase",
                                letter_spacing="0.05em", margin_bottom="10px"),
                        rx.vstack(
                            rx.foreach(FoodState.turno_cierre_denominaciones, _denominacion_row),
                            spacing="1", width="100%",
                        ),
                        border="1px solid #E2E8F0", border_radius="10px",
                        padding="14px", flex="1", min_width="260px",
                        max_height="320px", overflow_y="auto",
                    ),
                    gap="14px", width="100%",
                    direction=rx.breakpoints(initial="column", md="row"),
                ),
                # Contado + descuadre
                rx.box(
                    rx.hstack(
                        rx.vstack(
                            rx.text("Contado", font_size="11px", color="#94A3B8", font_weight="600"),
                            rx.text(FoodState.turno_cierre_contado_texto, font_size="18px",
                                    font_weight="800", color="#0F172A"),
                            spacing="0", align="start",
                        ),
                        rx.spacer(),
                        rx.vstack(
                            rx.text("Descuadre", font_size="11px", color="#94A3B8", font_weight="600"),
                            rx.text(FoodState.turno_cierre_descuadre_texto, font_size="18px",
                                    font_weight="900", color=FoodState.turno_cierre_descuadre_color),
                            spacing="0", align="end",
                        ),
                        width="100%", align="center",
                    ),
                    background="#FFFFFF", border="1px solid #E2E8F0",
                    border_radius="10px", padding="12px 16px", width="100%",
                ),
                rx.input(
                    placeholder="Notas del cierre (opcional)",
                    value=FoodState.turno_cierre_notas,
                    on_change=FoodState.set_turno_cierre_notas,
                    width="100%",
                    background="#FFFFFF", border="1px solid #E2E8F0",
                    border_radius="8px", font_size="13px",
                    _focus={"border_color": "#EA580C"},
                ),
                rx.cond(
                    FoodState.turno_cierre_error != "",
                    rx.text(FoodState.turno_cierre_error, font_size="12px",
                            color="#B91C1C", font_weight="600"),
                    rx.fragment(),
                ),
                rx.hstack(
                    rx.button(
                        "Cancelar",
                        on_click=FoodState.cancelar_cierre_turno,
                        background="#FFFFFF", color="#64748B",
                        border="1px solid #E2E8F0", border_radius="10px",
                        font_size="14px", font_weight="600", cursor="pointer",
                        _hover={"background": "#F8FAFC"}, flex="1",
                    ),
                    rx.button(
                        "Cerrar turno e imprimir",
                        on_click=FoodState.confirmar_cierre_turno,
                        background="#0F172A", color="#FFFFFF",
                        border_radius="10px", font_size="14px", font_weight="800",
                        cursor="pointer", _hover={"opacity": "0.9"}, flex="2",
                    ),
                    spacing="3", width="100%",
                ),
                spacing="3", width="100%",
            ),
            class_name="light", max_width="640px",
        ),
        open=FoodState.turno_cierre_visible,
        on_open_change=FoodState.set_turno_cierre_visible,
    )


def _turno_historial_row(t: TurnoHistorialView) -> rx.Component:
    return rx.hstack(
        rx.vstack(
            rx.text("Turno #" + t.id.to_string() + " · " + t.rango_texto,
                    font_size="13px", font_weight="600", color="#0F172A"),
            rx.text("Cerró: " + t.cajero + " · Ventas " + t.ventas_texto,
                    font_size="11px", color="#94A3B8"),
            spacing="0", align="start",
        ),
        rx.spacer(),
        rx.vstack(
            rx.text("Esperado " + t.esperado_texto + " · Contado " + t.contado_texto,
                    font_size="11px", color="#64748B"),
            rx.text(t.descuadre_texto, font_size="13px", font_weight="800",
                    color=t.descuadre_color, text_align="right"),
            spacing="0", align="end",
        ),
        width="100%", align="center", gap="10px",
        padding="10px 12px", border_bottom="1px solid #F1F5F9",
    )


def _historial_modal() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.hstack(
                    rx.text("Historial de turnos", font_size="18px", font_weight="800", color="#0F172A"),
                    rx.spacer(),
                    rx.icon(tag="x", size=18, color="#64748B", cursor="pointer",
                            on_click=FoodState.toggle_historial_turnos),
                    width="100%", align="center",
                ),
                rx.box(
                    rx.cond(
                        FoodState.turno_historial.length() > 0,
                        rx.vstack(
                            rx.foreach(FoodState.turno_historial, _turno_historial_row),
                            spacing="0", width="100%",
                        ),
                        rx.center(
                            rx.text("Todavía no hay turnos cerrados.", font_size="13px", color="#94A3B8"),
                            padding_y="20px", width="100%",
                        ),
                    ),
                    max_height="380px", overflow_y="auto", width="100%",
                    border="1px solid #F1F5F9", border_radius="10px",
                ),
                spacing="3", width="100%",
            ),
            class_name="light", max_width="600px",
        ),
        open=FoodState.turno_historial_visible,
        on_open_change=FoodState.set_turno_historial_visible,
    )


def _caja_content() -> rx.Component:
    return rx.vstack(
        cumpleanos_banner(),
        rx.hstack(
            rx.vstack(
                rx.text("Caja", font_size="22px", font_weight="800", color="#0F172A"),
                rx.text(
                    FoodState.cantidad_mesas_abiertas.to_string() + " mesa(s) abiertas",
                    font_size="13px", color="#64748B",
                ),
                spacing="0",
            ),
            rx.spacer(),
            rx.button(
                "Actualizar",
                on_click=FoodState.cargar_mesas,
                background="#FFFFFF", color="#EA580C",
                border="1px solid #E2E8F0", border_radius="8px",
                font_size="13px", font_weight="600", cursor="pointer",
                _hover={"border_color": "#EA580C"},
            ),
            width="100%", align="center",
        ),
        rx.cond(
            FoodState.mensaje != "",
            rx.box(
                rx.text(FoodState.mensaje, font_size="12px", color="#334155"),
                background="#F1F5F9", border="1px solid #E2E8F0",
                border_radius="6px", padding="8px 12px", width="100%",
            ),
            rx.fragment(),
        ),
        _turno_banner(),
        rx.flex(
            _mesas_sidebar(),
            _panel_central(),
            _resumen_dia(),
            direction=rx.breakpoints(initial="column", lg="row"),
            gap="16px", width="100%", align="start",
        ),
        _mov_modal(),
        _cierre_modal(),
        _historial_modal(),
        anulacion_modal(),
        spacing="4", width="100%",
    )


@rx.page(
    route="/caja",
    on_load=[FoodState.on_load_caja, FoodState.start_caja_polling,
             FoodState.cargar_clientes, FoodState.cargar_promociones,
             FoodState.cargar_dashboard],
    title="TUWAYKIFOOD | Caja",
)
def caja_page() -> rx.Component:
    return app_shell(_caja_content(), page_key="caja", dark=False)
