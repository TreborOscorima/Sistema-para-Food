"""Página de cuentas corrientes (fiado) por cliente."""

from __future__ import annotations

import reflex as rx

from app.states.food_state import FoodState, CuentaView, MovimientoView, AdminLocalState
from app.pages.dono import _dono_shell
from app.components.ayuda import ayuda_modal, ayuda_trigger, empty_state
from app.components.shared import (
    ACCENT, ACCENT_HOVER, ACCENT_TEXT,
    DANGER_TEXT, DANGER_SOLID, SUCCESS_SOLID, SUCCESS_DARK, WARNING_SOLID,
    DARK_600, DARK_700, DARK_800,
    PAGE_BACKGROUND, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, TEXT_WHITE,
)


def _cc_kpi_card(label: str, value, icon: str, accent: str, bg: str) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.box(
                rx.icon(tag=icon, size=16, color=accent),
                width="32px", height="32px", border_radius="8px",
                background=bg, display="flex",
                align_items="center", justify_content="center",
            ),
            rx.text(value, font_size="22px", font_weight="800", color=TEXT_PRIMARY, line_height="1"),
            rx.text(label, font_size="11px", font_weight="600", color=TEXT_MUTED,
                    text_transform="uppercase", letter_spacing="0.06em"),
            spacing="2", align="start", width="100%",
        ),
        background=DARK_800, border=f"1px solid {DARK_700}",
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
                color=rx.cond(es_cargo, DANGER_TEXT, SUCCESS_SOLID),
            ),
            width="28px", height="28px", border_radius="full",
            background=rx.cond(es_cargo, "rgba(239,68,68,0.12)", "rgba(34,197,94,0.12)"),
            display="flex", align_items="center", justify_content="center",
            flex_shrink="0",
        ),
        rx.vstack(
            rx.text(
                m.descripcion,
                font_size="12px", color=TEXT_SECONDARY, font_weight="600",
            ),
            rx.text(m.fecha_texto, font_size="11px", color=TEXT_MUTED),
            spacing="0", align="start", flex="1",
        ),
        rx.text(
            rx.cond(es_cargo, "−", "+") + " S/ " + m.monto_texto,
            font_size="13px", font_weight="700",
            color=rx.cond(es_cargo, DANGER_TEXT, SUCCESS_SOLID),
            flex_shrink="0",
        ),
        width="100%", align="center", gap="10px",
        padding="8px 10px",
        background=DARK_800, border_radius="8px",
        border=f"1px solid {DARK_800}",
        _hover={"background": DARK_700},
    )


def _cuenta_row(c: CuentaView) -> rx.Component:
    return rx.hstack(
        rx.box(
            rx.text(c.cliente_nombre[:1].upper(),
                    font_size="13px", font_weight="800", color=TEXT_WHITE),
            width="32px", height="32px", border_radius="full",
            background=ACCENT,
            display="flex", align_items="center", justify_content="center",
            flex_shrink="0",
        ),
        rx.vstack(
            rx.text(c.cliente_nombre, font_size="13px", font_weight="700", color=TEXT_PRIMARY),
            rx.text(c.cliente_telefono, font_size="11px", color=TEXT_MUTED),
            spacing="0", align="start", flex="1",
        ),
        rx.vstack(
            rx.text("S/ " + c.saldo_texto,
                    font_size="14px", font_weight="800", color=DANGER_TEXT),
            rx.text("deuda", font_size="10px", color=TEXT_MUTED),
            spacing="0", align="end",
        ),
        rx.link(
            "Cobrar",
            on_click=FoodState.set_cc_cliente_sel_nombre(c.cliente_nombre),
            font_size="12px", font_weight="700", color=ACCENT,
            cursor="pointer", flex_shrink="0",
            _hover={"color": ACCENT_HOVER},
        ),
        width="100%", align="center", gap="10px",
        padding="10px 12px",
        background=DARK_800, border_radius="9px",
        border="1px solid #FECACA",
        cursor="pointer",
        on_click=FoodState.set_cc_cliente_sel_nombre(c.cliente_nombre),
        _hover={"background": "rgba(239,68,68,0.08)"},
    )


def _pago_form() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.icon(tag="credit_card", size=13, color=ACCENT),
                rx.text("Registrar pago", font_size="13px", font_weight="700", color=TEXT_PRIMARY),
                spacing="1", align="center",
            ),
            rx.hstack(
                rx.vstack(
                    rx.text("Monto S/", font_size="11px", font_weight="600", color=TEXT_MUTED),
                    rx.input(
                        placeholder="0.00",
                        value=FoodState.cc_pago_monto,
                        on_change=FoodState.set_cc_pago_monto,
                        type="number", min="0.01", step="0.01",
                        background=PAGE_BACKGROUND, border=f"1px solid {DARK_700}",
                        border_radius="7px", font_size="13px",
                        padding_x="10px", padding_y="8px", width="100%",
                        _focus={"border": f"1px solid {ACCENT}"},
                    ),
                    spacing="1", align="start", flex="1",
                ),
                rx.vstack(
                    rx.text("Descripción", font_size="11px", font_weight="600", color=TEXT_MUTED),
                    rx.input(
                        placeholder="Ej: Pago en efectivo",
                        value=FoodState.cc_pago_descripcion,
                        on_change=FoodState.set_cc_pago_descripcion,
                        background=PAGE_BACKGROUND, border=f"1px solid {DARK_700}",
                        border_radius="7px", font_size="13px",
                        padding_x="10px", padding_y="8px", width="100%",
                        _focus={"border": f"1px solid {ACCENT}"},
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
                background=SUCCESS_SOLID, color=TEXT_WHITE,
                border_radius="7px", font_size="13px", font_weight="700",
                padding_x="16px", padding_y="8px", cursor="pointer",
                width="100%", justify="center",
                _hover={"background": SUCCESS_SOLID},
            ),
            spacing="3", width="100%",
        ),
        background="rgba(34,197,94,0.08)", border="1px solid #BBF7D0",
        border_radius="8px", padding="12px 14px", width="100%",
    )


def _cuenta_sin_cargos() -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.icon(tag="info", size=14, color=TEXT_MUTED),
            rx.text(
                "Este cliente no tiene cuenta corriente activa. "
                "Se crea automáticamente al registrar el primer cargo fiado.",
                font_size="13px", color=TEXT_MUTED,
            ),
            spacing="2", align="center",
        ),
        background=PAGE_BACKGROUND, border=f"1px solid {DARK_700}",
        border_radius="10px", padding="14px 16px", width="100%",
    )


def _cuenta_detalle() -> rx.Component:
    return rx.cond(
        FoodState.cuenta_sel_id > 0,
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.icon(tag="user", size=14, color=ACCENT),
                    rx.text(FoodState.cuenta_sel_nombre,
                            font_size="14px", font_weight="700", color=TEXT_PRIMARY),
                    rx.spacer(),
                    rx.vstack(
                        rx.text("S/ " + FoodState.cuenta_sel_saldo,
                                font_size="16px", font_weight="800", color=DANGER_TEXT),
                        rx.text("total deuda", font_size="10px", color=TEXT_MUTED),
                        spacing="0", align="end",
                    ),
                    width="100%", align="center",
                ),
                _pago_form(),
                rx.text("Movimientos",
                        font_size="12px", font_weight="700", color=TEXT_MUTED,
                        text_transform="uppercase", letter_spacing="0.05em"),
                rx.cond(
                    FoodState.cuenta_movimientos.length() > 0,
                    rx.vstack(
                        rx.foreach(FoodState.cuenta_movimientos, _movimiento_row),
                        spacing="1", width="100%",
                    ),
                    rx.center(
                        rx.text("Sin movimientos.", font_size="13px", color=TEXT_MUTED),
                        padding_y="16px", width="100%",
                    ),
                ),
                spacing="3", width="100%",
            ),
            background=DARK_800, border=f"1px solid {DARK_700}",
            border_radius="12px", padding="16px 18px", width="100%",
            box_shadow="0 1px 3px rgba(0,0,0,0.06)",
        ),
        rx.cond(
            FoodState.cc_cliente_sel_nombre != "",
            _cuenta_sin_cargos(),
            rx.fragment(),
        ),
    )


def _cuentas_ayuda() -> rx.Component:
    return ayuda_modal(
        titulo="¿Cómo funcionan las Cuentas Corrientes?",
        subtitulo="Fiado y créditos de clientes",
        secciones=[
            {"titulo": "Registrar deuda (fiado)", "pasos": [
                "La cuenta se crea sola cuando cobras un pedido como «fiado» a un cliente.",
                "El saldo pendiente aparece en «Clientes con deuda pendiente».",
            ]},
            {"titulo": "Cobrar un pago", "pasos": [
                "Selecciona el cliente o toca «Cobrar» en la lista.",
                "Ingresa el monto y una descripción, y toca «Registrar pago».",
                "El saldo baja solo y el movimiento queda registrado en el historial.",
            ]},
            {"titulo": "Exportar", "pasos": [
                "«Exportar Excel» descarga el detalle de deudas para tu contabilidad.",
            ]},
        ],
    )


def _cuentas_content() -> rx.Component:
    return rx.vstack(
        _cuentas_ayuda(),
        rx.cond(
            FoodState.es_pagina_standalone,
            rx.hstack(
                rx.link(
                    rx.hstack(
                        rx.icon(tag="arrow_left", size=13, color=TEXT_MUTED),
                        rx.text("Panel Administrativo", font_size="12px", color=TEXT_MUTED),
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
                rx.text("Cuentas Corrientes", font_size="22px", font_weight="800", color=TEXT_PRIMARY),
                rx.text("Fiado y créditos de clientes", font_size="13px", color=TEXT_MUTED),
                spacing="0",
            ),
            rx.spacer(),
            ayuda_trigger(),
            rx.button(
                rx.hstack(
                    rx.icon(tag="download", size=13, color=TEXT_WHITE),
                    rx.text("Exportar Excel", font_size="13px", font_weight="700",
                            color=TEXT_WHITE),
                    spacing="1", align="center",
                ),
                on_click=FoodState.exportar_cuentas_excel,
                background=SUCCESS_SOLID,
                border_radius="8px",
                padding_x="14px", padding_y="7px",
                cursor="pointer",
                _hover={"background": SUCCESS_SOLID},
            ),
            width="100%", align="center", flex_wrap="wrap", gap="10px",
        ),
        rx.hstack(
            _cc_kpi_card("Total a cobrar", FoodState.cuentas_total_deuda_texto,
                         "credit_card", DANGER_TEXT, "rgba(239,68,68,0.12)"),
            _cc_kpi_card("Cuentas con deuda", FoodState.cuentas_con_deuda.length().to_string(),
                         "users", ACCENT, "rgba(234,88,12,0.08)"),
            gap="12px", width="100%", flex_wrap="wrap",
        ),
        rx.hstack(
            rx.vstack(
                rx.text("Seleccionar cliente",
                        font_size="11px", font_weight="600", color=TEXT_MUTED),
                rx.select(
                    FoodState.clientes_activos_nombres,
                    value=FoodState.cc_cliente_sel_nombre,
                    on_change=FoodState.set_cc_cliente_sel_nombre,
                    placeholder="— Buscar cliente —",
                    background=PAGE_BACKGROUND, border=f"1px solid {DARK_700}",
                    border_radius="7px", font_size="13px", width="100%",
                ),
                spacing="1", align="start", flex="1",
            ),
            rx.tooltip(
                rx.button(
                    rx.icon(tag="refresh_cw", size=12),
                    on_click=FoodState.cargar_cuentas,
                    background=DARK_800, color=TEXT_MUTED,
                    border=f"1px solid {DARK_700}", border_radius="6px",
                    padding="4px 8px", cursor="pointer",
                    align_self="end", padding_y="9px",
                    _hover={"background": DARK_700},
                ),
                content="Actualizar",
            ),
            width="100%", align="end", spacing="3",
        ),
        _cuenta_detalle(),
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.icon(tag="clipboard_list", size=14, color=ACCENT),
                    rx.text("Clientes con deuda pendiente",
                            font_size="14px", font_weight="700", color=TEXT_PRIMARY),
                    spacing="2", align="center",
                ),
                rx.cond(
                    FoodState.cuentas_con_deuda.length() > 0,
                    rx.vstack(
                        rx.foreach(FoodState.cuentas_con_deuda, _cuenta_row),
                        spacing="1", width="100%",
                    ),
                    empty_state(
                        icono="wallet",
                        titulo="Sin deudas pendientes",
                        texto="Las cuentas se crean solas cuando cobras un pedido como «fiado» en Caja.",
                        cta_label="Ir a Caja",
                        cta_href="/caja",
                    ),
                ),
                spacing="3", width="100%",
            ),
            background=DARK_800, border=f"1px solid {DARK_700}",
            border_radius="12px", padding="16px 18px", width="100%",
            box_shadow="0 1px 3px rgba(0,0,0,0.06)",
        ),
        spacing="4", width="100%",
    )


@rx.page(
    route="/cuentas",
    on_load=[AdminLocalState.on_load_dono, FoodState.on_load_cuentas],
    title="TUWAYKIFOOD | Cuentas corrientes",
)
def cuentas_page() -> rx.Component:
    return _dono_shell(_cuentas_content())
