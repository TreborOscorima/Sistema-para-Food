"""Página de gestión de cupones por código de lote."""

from __future__ import annotations

import reflex as rx

from app.states.food_state import CuponLoteView, FoodState, AdminLocalState
from app.pages.dono import _dono_shell
from app.components.ayuda import ayuda_modal, ayuda_trigger
from app.components.shared import (
    ACCENT, ACCENT_HOVER,
    DANGER_SOLID,
    DARK_700, DARK_800,
    PAGE_BACKGROUND,
    SUCCESS_SOLID,
    TEXT_MUTED, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_WHITE,
)


def _tipo_badge(tipo: str) -> rx.Component:
    return rx.cond(
        tipo == "% Porcentaje",
        rx.badge("%", background="rgba(124,58,237,0.12)", color="#A78BFA",
                 border_radius="5px", font_size="10px", padding="2px 6px"),
        rx.badge("S/", background="rgba(34,197,94,0.12)", color=SUCCESS_SOLID,
                 border_radius="5px", font_size="10px", padding="2px 6px"),
    )


def _cupon_card(c: CuponLoteView) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.text(
                    rx.cond(c.activo, "🟢 ACTIVO", "⏸ PAUSADO"),
                    font_size="12px", font_weight="700", color=TEXT_WHITE,
                ),
                rx.cond(
                    c.vencido,
                    rx.text("VENCIDO", font_size="11px", color="#FCA5A5"),
                    rx.fragment(),
                ),
                width="100%", align="center",
                background=rx.cond(c.activo, ACCENT, TEXT_MUTED),
                padding="10px 14px",
            ),
            rx.vstack(
                rx.hstack(
                    rx.text(c.nombre, font_size="15px", font_weight="800", color=TEXT_PRIMARY),
                    _tipo_badge(c.tipo),
                    spacing="2", align="center",
                ),
                rx.hstack(
                    rx.box(
                        rx.text(c.codigo, font_size="14px", font_weight="800",
                                color=ACCENT, letter_spacing="1px"),
                        background="rgba(234,88,12,0.08)", border="1px dashed rgba(234,88,12,0.40)",
                        border_radius="6px", padding="4px 10px",
                    ),
                    rx.text(c.valor_texto + " off", font_size="13px", color=TEXT_MUTED),
                    spacing="3", align="center",
                ),
                rx.hstack(
                    rx.icon(tag="calendar", size=12, color=TEXT_MUTED),
                    rx.text(c.fecha_inicio_texto + " → " + c.fecha_fin_texto,
                            font_size="11px", color=TEXT_MUTED),
                    spacing="1", align="center",
                ),
                rx.hstack(
                    rx.icon(tag="hash", size=12, color=TEXT_MUTED),
                    rx.text(c.usos_texto, font_size="11px", color=TEXT_MUTED),
                    spacing="1", align="center",
                ),
                rx.hstack(
                    rx.link(
                        "Editar",
                        on_click=FoodState.editar_cupon(c.id),
                        font_size="12px", font_weight="600", color=TEXT_MUTED,
                        cursor="pointer", padding="5px 10px",
                        border=f"1px solid {DARK_700}", border_radius="6px",
                        _hover={"border_color": TEXT_MUTED},
                    ),
                    rx.link(
                        rx.cond(c.activo, "Pausar", "Activar"),
                        on_click=FoodState.toggle_cupon_activo(c.id),
                        font_size="12px", font_weight="600",
                        color=rx.cond(c.activo, DANGER_SOLID, ACCENT),
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
        background=DARK_800,
        border=f"1px solid {DARK_700}",
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
                        size=14, color=ACCENT,
                    ),
                    rx.dialog.title(
                        rx.cond(FoodState.cupon_form_editando, "Editar cupón", "Nuevo cupón"),
                        font_size="14px", font_weight="700", color=TEXT_PRIMARY, margin="0",
                    ),
                    spacing="2", align="center", margin_bottom="8px",
                ),
                # Nombre
                rx.vstack(
                    rx.text("Nombre del cupón *", font_size="11px", font_weight="600", color=TEXT_MUTED),
                    rx.input(
                        placeholder="Ej: Cupón de apertura enero",
                        value=FoodState.cupon_form_nombre,
                        on_change=FoodState.set_cupon_form_nombre,
                        background=PAGE_BACKGROUND, border=f"1px solid {DARK_700}",
                        border_radius="7px", font_size="13px", width="100%",
                        _focus={"border": f"1px solid {ACCENT}"},
                    ),
                    spacing="1", align="start", width="100%",
                ),
                # Código + Tipo
                rx.hstack(
                    rx.vstack(
                        rx.text("Código *", font_size="11px", font_weight="600", color=TEXT_MUTED),
                        rx.input(
                            placeholder="APERTURA2026",
                            value=FoodState.cupon_form_codigo,
                            on_change=FoodState.set_cupon_form_codigo,
                            background=PAGE_BACKGROUND, border=f"1px solid {DARK_700}",
                            border_radius="7px", font_size="13px", width="100%",
                            _focus={"border": f"1px solid {ACCENT}"},
                        ),
                        spacing="1", align="start", flex="2",
                    ),
                    rx.vstack(
                        rx.text("Tipo", font_size="11px", font_weight="600", color=TEXT_MUTED),
                        rx.select(
                            ["porcentaje", "monto_fijo"],
                            value=FoodState.cupon_form_tipo,
                            on_change=FoodState.set_cupon_form_tipo,
                            background=PAGE_BACKGROUND, border=f"1px solid {DARK_700}",
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
                            font_size="11px", font_weight="600", color=TEXT_MUTED,
                        ),
                        rx.input(
                            placeholder="10",
                            value=FoodState.cupon_form_valor,
                            on_change=FoodState.set_cupon_form_valor,
                            type="number", min="0", step="0.01",
                            background=PAGE_BACKGROUND, border=f"1px solid {DARK_700}",
                            border_radius="7px", font_size="13px", width="100%",
                            _focus={"border": f"1px solid {ACCENT}"},
                        ),
                        spacing="1", align="start", flex="1",
                    ),
                    rx.vstack(
                        rx.text("Usos máximos", font_size="11px", font_weight="600", color=TEXT_MUTED),
                        rx.input(
                            placeholder="100 (vacío = ilimitado)",
                            value=FoodState.cupon_form_usos_max,
                            on_change=FoodState.set_cupon_form_usos_max,
                            type="number", min="1",
                            background=PAGE_BACKGROUND, border=f"1px solid {DARK_700}",
                            border_radius="7px", font_size="13px", width="100%",
                            _focus={"border": f"1px solid {ACCENT}"},
                        ),
                        spacing="1", align="start", flex="1",
                    ),
                    spacing="3", width="100%", class_name="twk-form-row",
                ),
                # Fechas
                rx.hstack(
                    rx.vstack(
                        rx.text("Válido desde", font_size="11px", font_weight="600", color=TEXT_MUTED),
                        rx.input(
                            value=FoodState.cupon_form_fecha_inicio,
                            on_change=FoodState.set_cupon_form_fecha_inicio,
                            type="date",
                            background=PAGE_BACKGROUND, border=f"1px solid {DARK_700}",
                            border_radius="7px", font_size="13px", width="100%",
                            _focus={"border": f"1px solid {ACCENT}"},
                        ),
                        spacing="1", align="start", flex="1",
                    ),
                    rx.vstack(
                        rx.text("Válido hasta", font_size="11px", font_weight="600", color=TEXT_MUTED),
                        rx.input(
                            value=FoodState.cupon_form_fecha_fin,
                            on_change=FoodState.set_cupon_form_fecha_fin,
                            type="date",
                            background=PAGE_BACKGROUND, border=f"1px solid {DARK_700}",
                            border_radius="7px", font_size="13px", width="100%",
                            _focus={"border": f"1px solid {ACCENT}"},
                        ),
                        spacing="1", align="start", flex="1",
                    ),
                    spacing="3", width="100%", class_name="twk-form-row",
                ),
                rx.hstack(
                    rx.button(
                        rx.cond(FoodState.cupon_form_editando, "Actualizar", "Crear cupón"),
                        on_click=FoodState.guardar_cupon,
                        background=ACCENT, color=TEXT_WHITE,
                        border_radius="7px", font_size="13px", font_weight="700",
                        padding_x="16px", padding_y="8px", cursor="pointer",
                        _hover={"background": ACCENT_HOVER},
                    ),
                    rx.button(
                        "Cancelar",
                        on_click=FoodState.cancelar_cupon_form,
                        background=DARK_800, color=TEXT_MUTED,
                        border=f"1px solid {DARK_700}", border_radius="7px",
                        font_size="13px", padding_x="16px", padding_y="8px",
                        cursor="pointer", _hover={"background": DARK_700},
                    ),
                    spacing="2", justify="end", width="100%",
                ),
                spacing="3", width="100%",
            ),
            max_width="560px",
            width="92vw",
            max_height="90vh",
            overflow_y="auto",
            background=PAGE_BACKGROUND, border=f"1px solid {DARK_800}",
        ),
        open=FoodState.cupon_form_visible,
        on_open_change=FoodState.set_cupon_form_visible,
    )


def _cupones_nueva_placeholder() -> rx.Component:
    return rx.box(
        rx.text("🎫", font_size="36px", line_height="1"),
        rx.text("Crear nuevo cupón", font_size="14px", font_weight="700", color=TEXT_MUTED,
                margin_top="8px"),
        rx.text("Apertura, fidelidad, marketing…", font_size="12px", color=TEXT_SECONDARY,
                margin_top="2px"),
        on_click=FoodState.abrir_nuevo_cupon,
        background=DARK_800, border=f"2px dashed {DARK_700}",
        border_radius="16px", padding="36px 16px",
        display="flex", flex_direction="column",
        align_items="center", justify_content="center",
        cursor="pointer", text_align="center", width="100%", height="100%",
        _hover={"border_color": ACCENT, "background": "rgba(234,88,12,0.08)"},
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


def _cupones_ayuda() -> rx.Component:
    return ayuda_modal(
        titulo="¿Cómo funcionan los Cupones?",
        subtitulo="Códigos que el cliente presenta y caja ingresa al cobrar.",
        secciones=[
            {
                "titulo": None,
                "pasos": [
                    "Crea un lote con su código, descuento y vigencia.",
                    "Reparte o imprime los códigos para tus clientes.",
                    "Al cobrar, caja ingresa el código y se aplica el descuento.",
                    "Aquí ves cuántos se usaron de cada lote.",
                ],
            },
            {
                "titulo": "¿En qué se diferencian de las promociones?",
                "pasos": [
                    "Los cupones los presenta el cliente. Las promociones (happy hour, "
                    "por producto) se aplican solas — están en el módulo Promociones.",
                ],
            },
        ],
    )


def _cupones_content() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.vstack(
                rx.text("Cupones", font_size="22px", font_weight="800", color=TEXT_PRIMARY),
                rx.text("Códigos que el cliente presenta y caja ingresa al cobrar",
                        font_size="13px", color=TEXT_MUTED),
                spacing="0", align="start",
            ),
            rx.spacer(),
            ayuda_trigger(),
            rx.button(
                rx.hstack(
                    rx.icon(tag="plus", size=13),
                    rx.text("Nuevo cupón", font_size="13px", font_weight="700"),
                    spacing="1", align="center",
                ),
                on_click=FoodState.abrir_nuevo_cupon,
                background=ACCENT, color=TEXT_WHITE, border_radius="9px",
                padding_x="16px", padding_y="9px", cursor="pointer",
                _hover={"background": ACCENT_HOVER},
            ),
            width="100%", align="center", flex_wrap="wrap", gap="8px",
        ),
        _cupones_body(),
        _cupones_ayuda(),
        spacing="4", width="100%",
    )


@rx.page(
    route="/cupones",
    on_load=[AdminLocalState.on_load_dono, FoodState.on_load_cupones],
    title="TUWAYKIFOOD | Cupones",
)
def cupones_page() -> rx.Component:
    return _dono_shell(_cupones_content())
