"""Página de gestión de cupones por código de lote."""

from __future__ import annotations

import reflex as rx

from app.states.food_state import CuponLoteView, FoodState, AdminLocalState
from app.pages.dono import _dono_shell


def _tipo_badge(tipo: str) -> rx.Component:
    return rx.cond(
        tipo == "% Porcentaje",
        rx.badge("%", background="rgba(124,58,237,0.12)", color="#A78BFA",
                 border_radius="5px", font_size="10px", padding="2px 6px"),
        rx.badge("S/", background="rgba(34,197,94,0.12)", color="#22C55E",
                 border_radius="5px", font_size="10px", padding="2px 6px"),
    )


def _cupon_card(c: CuponLoteView) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.text(
                    rx.cond(c.activo, "🟢 ACTIVO", "⏸ PAUSADO"),
                    font_size="12px", font_weight="700", color="#FFFFFF",
                ),
                rx.cond(
                    c.vencido,
                    rx.text("VENCIDO", font_size="11px", color="#FCA5A5"),
                    rx.fragment(),
                ),
                width="100%", align="center",
                background=rx.cond(c.activo, "#EA580C", "#94A3B8"),
                padding="10px 14px",
            ),
            rx.vstack(
                rx.hstack(
                    rx.text(c.nombre, font_size="15px", font_weight="800", color="#F1F5F9"),
                    _tipo_badge(c.tipo),
                    spacing="2", align="center",
                ),
                rx.hstack(
                    rx.box(
                        rx.text(c.codigo, font_size="14px", font_weight="800",
                                color="#EA580C", letter_spacing="1px"),
                        background="rgba(234,88,12,0.08)", border="1px dashed rgba(234,88,12,0.40)",
                        border_radius="6px", padding="4px 10px",
                    ),
                    rx.text(c.valor_texto + " off", font_size="13px", color="#94A3B8"),
                    spacing="3", align="center",
                ),
                rx.hstack(
                    rx.icon(tag="calendar", size=12, color="#94A3B8"),
                    rx.text(c.fecha_inicio_texto + " → " + c.fecha_fin_texto,
                            font_size="11px", color="#94A3B8"),
                    spacing="1", align="center",
                ),
                rx.hstack(
                    rx.icon(tag="hash", size=12, color="#94A3B8"),
                    rx.text(c.usos_texto, font_size="11px", color="#94A3B8"),
                    spacing="1", align="center",
                ),
                rx.hstack(
                    rx.link(
                        "Editar",
                        on_click=FoodState.editar_cupon(c.id),
                        font_size="12px", font_weight="600", color="#94A3B8",
                        cursor="pointer", padding="5px 10px",
                        border="1px solid #334155", border_radius="6px",
                        _hover={"border_color": "#94A3B8"},
                    ),
                    rx.link(
                        rx.cond(c.activo, "Pausar", "Activar"),
                        on_click=FoodState.toggle_cupon_activo(c.id),
                        font_size="12px", font_weight="600",
                        color=rx.cond(c.activo, "#DC2626", "#EA580C"),
                        cursor="pointer", padding="5px 10px",
                        border=rx.cond(c.activo, "1px solid rgba(239,68,68,0.40)", "1px solid rgba(234,88,12,0.40)"),
                        border_radius="6px",
                        _hover={"opacity": "0.8"},
                    ),
                    spacing="2", justify="end", width="100%", margin_top="6px",
                ),
                spacing="2", align="start", width="100%", padding="14px",
            ),
        ),
        background="#1E293B",
        border=rx.cond(c.activo, "1px solid #334155", "1px solid #334155"),
        border_radius="16px", overflow="hidden",
        opacity=rx.cond(c.activo, "1", "0.65"),
        width="100%",
    )


def _cupon_form_modal() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.hstack(
                    rx.icon(
                        tag=rx.cond(FoodState.cupon_form_editando, "pencil", "circle_plus"),
                        size=14, color="#EA580C",
                    ),
                    rx.text(
                        rx.cond(FoodState.cupon_form_editando, "Editar cupón", "Nuevo cupón"),
                        font_size="14px", font_weight="700", color="#F1F5F9",
                    ),
                    spacing="2", align="center", margin_bottom="8px",
                ),
                # Nombre
                rx.vstack(
                    rx.text("Nombre del cupón *", font_size="11px", font_weight="600", color="#94A3B8"),
                    rx.input(
                        placeholder="Ej: Cupón de apertura enero",
                        value=FoodState.cupon_form_nombre,
                        on_change=FoodState.set_cupon_form_nombre,
                        background="#0F172A", border="1px solid #334155",
                        border_radius="7px", font_size="13px", width="100%",
                        _focus={"border": "1px solid #EA580C"},
                    ),
                    spacing="1", align="start", width="100%",
                ),
                # Código + Tipo
                rx.hstack(
                    rx.vstack(
                        rx.text("Código *", font_size="11px", font_weight="600", color="#94A3B8"),
                        rx.input(
                            placeholder="APERTURA2026",
                            value=FoodState.cupon_form_codigo,
                            on_change=FoodState.set_cupon_form_codigo,
                            background="#0F172A", border="1px solid #334155",
                            border_radius="7px", font_size="13px", width="100%",
                            _focus={"border": "1px solid #EA580C"},
                        ),
                        spacing="1", align="start", flex="2",
                    ),
                    rx.vstack(
                        rx.text("Tipo", font_size="11px", font_weight="600", color="#94A3B8"),
                        rx.select(
                            ["porcentaje", "monto_fijo"],
                            value=FoodState.cupon_form_tipo,
                            on_change=FoodState.set_cupon_form_tipo,
                            background="#0F172A", border="1px solid #334155",
                            border_radius="7px", font_size="13px", width="100%",
                        ),
                        spacing="1", align="start", flex="1",
                    ),
                    spacing="3", width="100%", class_name="twk-form-row",
                ),
                # Valor + Usos máximos
                rx.hstack(
                    rx.vstack(
                        rx.text(
                            rx.cond(FoodState.cupon_form_tipo == "porcentaje", "Valor (%)", "Valor (S/)"),
                            font_size="11px", font_weight="600", color="#94A3B8",
                        ),
                        rx.input(
                            placeholder="10",
                            value=FoodState.cupon_form_valor,
                            on_change=FoodState.set_cupon_form_valor,
                            type="number", min="0", step="0.01",
                            background="#0F172A", border="1px solid #334155",
                            border_radius="7px", font_size="13px", width="100%",
                            _focus={"border": "1px solid #EA580C"},
                        ),
                        spacing="1", align="start", flex="1",
                    ),
                    rx.vstack(
                        rx.text("Usos máximos", font_size="11px", font_weight="600", color="#94A3B8"),
                        rx.input(
                            placeholder="100 (vacío = ilimitado)",
                            value=FoodState.cupon_form_usos_max,
                            on_change=FoodState.set_cupon_form_usos_max,
                            type="number", min="1",
                            background="#0F172A", border="1px solid #334155",
                            border_radius="7px", font_size="13px", width="100%",
                            _focus={"border": "1px solid #EA580C"},
                        ),
                        spacing="1", align="start", flex="1",
                    ),
                    spacing="3", width="100%", class_name="twk-form-row",
                ),
                # Fechas
                rx.hstack(
                    rx.vstack(
                        rx.text("Válido desde", font_size="11px", font_weight="600", color="#94A3B8"),
                        rx.input(
                            value=FoodState.cupon_form_fecha_inicio,
                            on_change=FoodState.set_cupon_form_fecha_inicio,
                            type="date",
                            background="#0F172A", border="1px solid #334155",
                            border_radius="7px", font_size="13px", width="100%",
                            _focus={"border": "1px solid #EA580C"},
                        ),
                        spacing="1", align="start", flex="1",
                    ),
                    rx.vstack(
                        rx.text("Válido hasta", font_size="11px", font_weight="600", color="#94A3B8"),
                        rx.input(
                            value=FoodState.cupon_form_fecha_fin,
                            on_change=FoodState.set_cupon_form_fecha_fin,
                            type="date",
                            background="#0F172A", border="1px solid #334155",
                            border_radius="7px", font_size="13px", width="100%",
                            _focus={"border": "1px solid #EA580C"},
                        ),
                        spacing="1", align="start", flex="1",
                    ),
                    spacing="3", width="100%", class_name="twk-form-row",
                ),
                rx.hstack(
                    rx.button(
                        rx.cond(FoodState.cupon_form_editando, "Actualizar", "Crear cupón"),
                        on_click=FoodState.guardar_cupon,
                        background="#EA580C", color="#FFFFFF",
                        border_radius="7px", font_size="13px", font_weight="700",
                        padding_x="16px", padding_y="8px", cursor="pointer",
                        _hover={"background": "#C2410C"},
                    ),
                    rx.button(
                        "Cancelar",
                        on_click=FoodState.cancelar_cupon_form,
                        background="#1E293B", color="#94A3B8",
                        border="1px solid #334155", border_radius="7px",
                        font_size="13px", padding_x="16px", padding_y="8px",
                        cursor="pointer", _hover={"background": "#334155"},
                    ),
                    spacing="2", justify="end", width="100%",
                ),
                spacing="3", width="100%",
            ),
            background="#0F172A", border="1px solid #1E293B",
        ),
        open=FoodState.cupon_form_visible,
        on_open_change=FoodState.set_cupon_form_visible,
    )


def _cupones_nueva_placeholder() -> rx.Component:
    return rx.box(
        rx.text("🎫", font_size="36px", line_height="1"),
        rx.text("Crear nuevo cupón", font_size="14px", font_weight="700", color="#94A3B8",
                margin_top="8px"),
        rx.text("Apertura, fidelidad, marketing…", font_size="12px", color="#CBD5E1",
                margin_top="2px"),
        on_click=FoodState.abrir_nuevo_cupon,
        background="#1E293B", border="2px dashed #334155",
        border_radius="16px", padding="36px 16px",
        display="flex", flex_direction="column",
        align_items="center", justify_content="center",
        cursor="pointer", text_align="center", width="100%", height="100%",
        _hover={"border_color": "#EA580C", "background": "rgba(234,88,12,0.08)"},
    )


def _cupones_body() -> rx.Component:
    """Cuerpo reutilizable — sin header de título ni botón nuevo.
    Usado cuando cupones se embebe dentro de otro módulo (Promociones)."""
    return rx.vstack(
        rx.box(
            rx.hstack(
                rx.icon(tag="info", size=14, color="#60A5FA"),
                rx.text(
                    "Los cajeros ingresan el código al cobrar en Caja o Mostrador. "
                    "El sistema valida vigencia, usos y aplica el descuento automáticamente.",
                    font_size="12px", color="#60A5FA",
                ),
                spacing="2", align="center",
            ),
            background="rgba(59,130,246,0.08)", border="1px solid #BFDBFE",
            border_radius="10px", padding="10px 14px", width="100%",
        ),
        rx.grid(
            rx.foreach(FoodState.cupones_lista, _cupon_card),
            _cupones_nueva_placeholder(),
            columns=rx.breakpoints(initial="1", sm="2", lg="3"),
            gap="16px", width="100%",
        ),
        _cupon_form_modal(),
        spacing="4", width="100%",
    )


def _cupones_content() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.vstack(
                rx.text("Cupones", font_size="22px", font_weight="800", color="#F1F5F9"),
                rx.text("Códigos de descuento por lote", font_size="13px", color="#94A3B8"),
                spacing="0", align="start",
            ),
            rx.spacer(),
            rx.button(
                rx.hstack(
                    rx.icon(tag="plus", size=13),
                    rx.text("Nuevo cupón", font_size="13px", font_weight="700"),
                    spacing="1", align="center",
                ),
                on_click=FoodState.abrir_nuevo_cupon,
                background="#EA580C", color="#FFFFFF", border_radius="9px",
                padding_x="16px", padding_y="9px", cursor="pointer",
                _hover={"background": "#C2410C"},
            ),
            width="100%", align="center",
        ),
        _cupones_body(),
        spacing="4", width="100%",
    )


@rx.page(
    route="/cupones",
    on_load=[AdminLocalState.on_load_dono, FoodState.on_load_cupones],
    title="TUWAYKIFOOD | Cupones",
)
def cupones_page() -> rx.Component:
    return _dono_shell(_cupones_content())
