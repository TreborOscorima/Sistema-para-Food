"""Página de cuentas corrientes (fiado) por cliente."""

from __future__ import annotations

import reflex as rx

from app.states.food_state import FoodState, CuentaView, MovimientoView, AdminLocalState
from app.pages.dono import _dono_shell


def _cc_kpi_card(label: str, value, icon: str, accent: str, bg: str) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.box(
                rx.icon(tag=icon, size=16, color=accent),
                width="32px", height="32px", border_radius="8px",
                background=bg, display="flex",
                align_items="center", justify_content="center",
            ),
            rx.text(value, font_size="22px", font_weight="800", color="#F1F5F9", line_height="1"),
            rx.text(label, font_size="11px", font_weight="600", color="#94A3B8",
                    text_transform="uppercase", letter_spacing="0.06em"),
            spacing="2", align="start", width="100%",
        ),
        background="#1E293B", border="1px solid #334155",
        border_radius="12px", padding="14px 16px",
        box_shadow="0 1px 3px rgba(0,0,0,0.06)", flex="1", min_width="0",
    )


def _movimiento_row(m: MovimientoView) -> rx.Component:
    es_cargo = m.tipo == "cargo"
    return rx.hstack(
        rx.box(
            rx.icon(
                tag=rx.cond(es_cargo, "arrow_up_right", "arrow_down_left"),
                size=12,
                color=rx.cond(es_cargo, "#F87171", "#22C55E"),
            ),
            width="28px", height="28px", border_radius="full",
            background=rx.cond(es_cargo, "rgba(239,68,68,0.12)", "rgba(34,197,94,0.12)"),
            display="flex", align_items="center", justify_content="center",
            flex_shrink="0",
        ),
        rx.vstack(
            rx.text(
                m.descripcion,
                font_size="12px", color="#CBD5E1", font_weight="600",
            ),
            rx.text(m.fecha_texto, font_size="11px", color="#94A3B8"),
            spacing="0", align="start", flex="1",
        ),
        rx.text(
            rx.cond(es_cargo, "−", "+") + " S/ " + m.monto_texto,
            font_size="13px", font_weight="700",
            color=rx.cond(es_cargo, "#F87171", "#22C55E"),
            flex_shrink="0",
        ),
        width="100%", align="center", gap="10px",
        padding="8px 10px",
        background="#1E293B", border_radius="8px",
        border="1px solid #1E293B",
        _hover={"background": "#334155"},
    )


def _cuenta_row(c: CuentaView) -> rx.Component:
    return rx.hstack(
        rx.box(
            rx.text(c.cliente_nombre[:1].upper(),
                    font_size="13px", font_weight="800", color="#FFFFFF"),
            width="32px", height="32px", border_radius="full",
            background="#EA580C",
            display="flex", align_items="center", justify_content="center",
            flex_shrink="0",
        ),
        rx.vstack(
            rx.text(c.cliente_nombre, font_size="13px", font_weight="700", color="#F1F5F9"),
            rx.text(c.cliente_telefono, font_size="11px", color="#94A3B8"),
            spacing="0", align="start", flex="1",
        ),
        rx.vstack(
            rx.text("S/ " + c.saldo_texto,
                    font_size="14px", font_weight="800", color="#F87171"),
            rx.text("deuda", font_size="10px", color="#94A3B8"),
            spacing="0", align="end",
        ),
        rx.link(
            "Cobrar",
            on_click=FoodState.set_cc_cliente_sel_nombre(c.cliente_nombre),
            font_size="12px", font_weight="700", color="#EA580C",
            cursor="pointer", flex_shrink="0",
            _hover={"color": "#C2410C"},
        ),
        width="100%", align="center", gap="10px",
        padding="10px 12px",
        background="#1E293B", border_radius="9px",
        border="1px solid #FECACA",
        cursor="pointer",
        on_click=FoodState.set_cc_cliente_sel_nombre(c.cliente_nombre),
        _hover={"background": "rgba(239,68,68,0.08)"},
    )


def _pago_form() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.icon(tag="credit_card", size=13, color="#EA580C"),
                rx.text("Registrar pago", font_size="13px", font_weight="700", color="#F1F5F9"),
                spacing="1", align="center",
            ),
            rx.hstack(
                rx.vstack(
                    rx.text("Monto S/", font_size="11px", font_weight="600", color="#94A3B8"),
                    rx.input(
                        placeholder="0.00",
                        value=FoodState.cc_pago_monto,
                        on_change=FoodState.set_cc_pago_monto,
                        type="number", min="0.01", step="0.01",
                        background="#0F172A", border="1px solid #334155",
                        border_radius="7px", font_size="13px",
                        padding_x="10px", padding_y="8px", width="100%",
                        _focus={"border": "1px solid #EA580C"},
                    ),
                    spacing="1", align="start", flex="1",
                ),
                rx.vstack(
                    rx.text("Descripción", font_size="11px", font_weight="600", color="#94A3B8"),
                    rx.input(
                        placeholder="Ej: Pago en efectivo",
                        value=FoodState.cc_pago_descripcion,
                        on_change=FoodState.set_cc_pago_descripcion,
                        background="#0F172A", border="1px solid #334155",
                        border_radius="7px", font_size="13px",
                        padding_x="10px", padding_y="8px", width="100%",
                        _focus={"border": "1px solid #EA580C"},
                    ),
                    spacing="1", align="start", flex="2",
                ),
                spacing="3", width="100%",
                class_name="twk-form-row",
            ),
            rx.button(
                rx.icon(tag="check", size=13),
                "Registrar pago",
                on_click=FoodState.registrar_pago_cc,
                background="#22C55E", color="#FFFFFF",
                border_radius="7px", font_size="13px", font_weight="700",
                padding_x="16px", padding_y="8px", cursor="pointer",
                width="100%", justify="center",
                _hover={"background": "#22C55E"},
            ),
            spacing="3", width="100%",
        ),
        background="rgba(34,197,94,0.08)", border="1px solid #BBF7D0",
        border_radius="8px", padding="12px 14px", width="100%",
    )


def _cuenta_sin_cargos() -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.icon(tag="info", size=14, color="#94A3B8"),
            rx.text(
                "Este cliente no tiene cuenta corriente activa. "
                "Se crea automáticamente al registrar el primer cargo fiado.",
                font_size="13px", color="#94A3B8",
            ),
            spacing="2", align="center",
        ),
        background="#0F172A", border="1px solid #334155",
        border_radius="10px", padding="14px 16px", width="100%",
    )


def _cuenta_detalle() -> rx.Component:
    return rx.cond(
        FoodState.cuenta_sel_id > 0,
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.icon(tag="user", size=14, color="#EA580C"),
                    rx.text(FoodState.cuenta_sel_nombre,
                            font_size="14px", font_weight="700", color="#F1F5F9"),
                    rx.spacer(),
                    rx.vstack(
                        rx.text("S/ " + FoodState.cuenta_sel_saldo,
                                font_size="16px", font_weight="800", color="#F87171"),
                        rx.text("total deuda", font_size="10px", color="#94A3B8"),
                        spacing="0", align="end",
                    ),
                    width="100%", align="center",
                ),
                _pago_form(),
                rx.text("Movimientos",
                        font_size="12px", font_weight="700", color="#94A3B8",
                        text_transform="uppercase", letter_spacing="0.05em"),
                rx.cond(
                    FoodState.cuenta_movimientos.length() > 0,
                    rx.vstack(
                        rx.foreach(FoodState.cuenta_movimientos, _movimiento_row),
                        spacing="1", width="100%",
                    ),
                    rx.center(
                        rx.text("Sin movimientos.", font_size="13px", color="#94A3B8"),
                        padding_y="16px", width="100%",
                    ),
                ),
                spacing="3", width="100%",
            ),
            background="#1E293B", border="1px solid #334155",
            border_radius="12px", padding="16px 18px", width="100%",
            box_shadow="0 1px 3px rgba(0,0,0,0.06)",
        ),
        rx.cond(
            FoodState.cc_cliente_sel_nombre != "",
            _cuenta_sin_cargos(),
            rx.fragment(),
        ),
    )


def _cuentas_content() -> rx.Component:
    return rx.vstack(
        rx.cond(
            FoodState.es_pagina_standalone,
            rx.hstack(
                rx.link(
                    rx.hstack(
                        rx.icon(tag="arrow_left", size=13, color="#94A3B8"),
                        rx.text("Panel Administrativo", font_size="12px", color="#94A3B8"),
                        spacing="1", align="center",
                    ),
                    href="/admin", _hover={"opacity": "0.7"},
                ),
                rx.spacer(),
            ),
            rx.fragment(),
        ),
        rx.hstack(
            rx.vstack(
                rx.text("Cuentas Corrientes", font_size="22px", font_weight="800", color="#F1F5F9"),
                rx.text("Fiado y créditos de clientes", font_size="13px", color="#94A3B8"),
                spacing="0",
            ),
            rx.spacer(),
            rx.button(
                rx.hstack(
                    rx.icon(tag="download", size=13, color="#FFFFFF"),
                    rx.text("Exportar Excel", font_size="13px", font_weight="700",
                            color="#FFFFFF"),
                    spacing="1", align="center",
                ),
                on_click=FoodState.exportar_cuentas_excel,
                background="#22C55E",
                border_radius="8px",
                padding_x="14px", padding_y="7px",
                cursor="pointer",
                _hover={"background": "#22C55E"},
            ),
            width="100%", align="center",
        ),
        rx.hstack(
            _cc_kpi_card("Total a cobrar", FoodState.cuentas_total_deuda_texto,
                         "credit_card", "#F87171", "rgba(239,68,68,0.12)"),
            _cc_kpi_card("Cuentas con deuda", FoodState.cuentas_con_deuda.length().to_string(),
                         "users", "#EA580C", "rgba(234,88,12,0.08)"),
            gap="12px", width="100%", flex_wrap="wrap",
        ),
        rx.hstack(
            rx.vstack(
                rx.text("Seleccionar cliente",
                        font_size="11px", font_weight="600", color="#94A3B8"),
                rx.select(
                    FoodState.clientes_activos_nombres,
                    value=FoodState.cc_cliente_sel_nombre,
                    on_change=FoodState.set_cc_cliente_sel_nombre,
                    placeholder="— Buscar cliente —",
                    background="#0F172A", border="1px solid #334155",
                    border_radius="7px", font_size="13px", width="100%",
                ),
                spacing="1", align="start", flex="1",
            ),
            rx.button(
                rx.icon(tag="refresh_cw", size=12),
                on_click=FoodState.cargar_cuentas,
                background="#1E293B", color="#94A3B8",
                border="1px solid #334155", border_radius="6px",
                padding="4px 8px", cursor="pointer",
                align_self="end", padding_y="9px",
                _hover={"background": "#334155"},
            ),
            width="100%", align="end", spacing="3",
        ),
        _cuenta_detalle(),
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.icon(tag="clipboard_list", size=14, color="#EA580C"),
                    rx.text("Clientes con deuda pendiente",
                            font_size="14px", font_weight="700", color="#F1F5F9"),
                    spacing="2", align="center",
                ),
                rx.cond(
                    FoodState.cuentas_con_deuda.length() > 0,
                    rx.vstack(
                        rx.foreach(FoodState.cuentas_con_deuda, _cuenta_row),
                        spacing="1", width="100%",
                    ),
                    rx.center(
                        rx.text("Sin deudas pendientes.", font_size="13px", color="#94A3B8"),
                        padding_y="20px", width="100%",
                    ),
                ),
                spacing="3", width="100%",
            ),
            background="#1E293B", border="1px solid #334155",
            border_radius="12px", padding="16px 18px", width="100%",
            box_shadow="0 1px 3px rgba(0,0,0,0.06)",
        ),
        spacing="4", width="100%",
    )


@rx.page(
    route="/cuentas",
    on_load=[AdminLocalState.on_load_dono, FoodState.on_load_cuentas],
    title="TUWAYKIFOOD | Cuentas Corrientes",
)
def cuentas_page() -> rx.Component:
    return _dono_shell(_cuentas_content())
