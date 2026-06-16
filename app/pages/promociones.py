"""Página de gestión de promociones y happy hours."""

from __future__ import annotations

import reflex as rx

from app.states.food_state import FoodState, PromocionView, AdminLocalState
from app.pages.dono import _dono_shell


def _tipo_label(tipo: str) -> rx.Component:
    return rx.cond(
        tipo == "PORCENTAJE",
        rx.badge("%", background="#EDE9FE", color="#5B21B6",
                 border_radius="5px", font_size="10px", padding="2px 6px"),
        rx.cond(
            tipo == "MONTO_FIJO",
            rx.badge("S/", background="#DCFCE7", color="#166534",
                     border_radius="5px", font_size="10px", padding="2px 6px"),
            rx.badge("HH", background="#FEF9C3", color="#713F12",
                     border_radius="5px", font_size="10px", padding="2px 6px"),
        ),
    )


def _promo_row(p: PromocionView) -> rx.Component:
    return rx.hstack(
        rx.vstack(
            rx.hstack(
                rx.text(p.nombre, font_size="13px", font_weight="700", color="#0F172A"),
                _tipo_label(p.tipo),
                rx.cond(
                    p.aplica_ahora,
                    rx.badge("ACTIVA AHORA", background="#FEF9C3", color="#713F12",
                             border_radius="5px", font_size="9px", padding="2px 6px",
                             border="1px solid #FDE047"),
                    rx.fragment(),
                ),
                spacing="2", align="center",
            ),
            rx.hstack(
                rx.text(p.descuento_texto, font_size="12px", color="#334155", font_weight="600"),
                rx.cond(
                    p.horario_texto != "",
                    rx.text("·", font_size="12px", color="#CBD5E1"),
                    rx.fragment(),
                ),
                rx.cond(
                    p.horario_texto != "",
                    rx.text(p.horario_texto, font_size="11px", color="#64748B"),
                    rx.fragment(),
                ),
                spacing="1", align="center",
            ),
            spacing="1", align="start", flex="1",
        ),
        rx.hstack(
            rx.button(
                rx.icon(tag="pencil", size=12),
                on_click=FoodState.editar_promocion(p.id),
                background="#F1F5F9", color="#475569",
                border="1px solid #E2E8F0", border_radius="6px",
                padding="4px 8px", cursor="pointer",
                _hover={"background": "#E2E8F0"},
            ),
            rx.button(
                rx.cond(p.activa, rx.icon(tag="toggle_right", size=12), rx.icon(tag="toggle_left", size=12)),
                on_click=FoodState.toggle_promo_activa(p.id),
                background=rx.cond(p.activa, "#F0FDF4", "#F8FAFC"),
                color=rx.cond(p.activa, "#15803D", "#94A3B8"),
                border=rx.cond(p.activa, "1px solid #BBF7D0", "1px solid #E2E8F0"),
                border_radius="6px", padding="4px 8px", cursor="pointer",
                _hover={"opacity": "0.8"},
            ),
            spacing="2", flex_shrink="0",
        ),
        width="100%", align="center", gap="10px",
        padding="10px 12px",
        background=rx.cond(p.aplica_ahora, "#FFFBEB", "#FFFFFF"),
        border_radius="9px",
        border=rx.cond(p.aplica_ahora, "1px solid #FDE68A", "1px solid #F1F5F9"),
        _hover={"background": rx.cond(p.aplica_ahora, "#FEF9E7", "#F8FAFC")},
    )


def _promo_form() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.icon(
                    tag=rx.cond(FoodState.promo_form_editando, "pencil", "plus"),
                    size=13, color="#EA580C",
                ),
                rx.text(
                    rx.cond(FoodState.promo_form_editando, "Editar promoción", "Nueva promoción"),
                    font_size="13px", font_weight="700", color="#0F172A",
                ),
                spacing="1", align="center",
            ),
            rx.hstack(
                rx.vstack(
                    rx.text("Nombre *", font_size="11px", font_weight="600", color="#64748B"),
                    rx.input(
                        placeholder="Ej: 2x1 en cenas",
                        value=FoodState.promo_form_nombre,
                        on_change=FoodState.set_promo_form_nombre,
                        background="#F8FAFC", border="1px solid #E2E8F0",
                        border_radius="7px", font_size="13px",
                        padding_x="10px", padding_y="8px", width="100%",
                        _focus={"border": "1px solid #EA580C"},
                    ),
                    spacing="1", align="start", flex="2",
                ),
                rx.vstack(
                    rx.text("Tipo", font_size="11px", font_weight="600", color="#64748B"),
                    rx.select(
                        FoodState.tipos_promo_disponibles,
                        value=FoodState.promo_form_tipo,
                        on_change=FoodState.set_promo_form_tipo,
                        background="#F8FAFC", border="1px solid #E2E8F0",
                        border_radius="7px", font_size="13px", width="100%",
                    ),
                    spacing="1", align="start", flex="1",
                ),
                spacing="3", width="100%",
            ),
            rx.hstack(
                rx.vstack(
                    rx.text("Valor (% ó S/)", font_size="11px", font_weight="600", color="#64748B"),
                    rx.input(
                        placeholder="Ej: 10",
                        value=FoodState.promo_form_valor,
                        on_change=FoodState.set_promo_form_valor,
                        type="number", min="0", step="0.01",
                        background="#F8FAFC", border="1px solid #E2E8F0",
                        border_radius="7px", font_size="13px",
                        padding_x="10px", padding_y="8px", width="100%",
                        _focus={"border": "1px solid #EA580C"},
                    ),
                    spacing="1", align="start", flex="1",
                ),
                rx.vstack(
                    rx.text("Hora inicio", font_size="11px", font_weight="600", color="#64748B"),
                    rx.input(
                        placeholder="18:00",
                        value=FoodState.promo_form_hora_inicio,
                        on_change=FoodState.set_promo_form_hora_inicio,
                        type="time",
                        background="#F8FAFC", border="1px solid #E2E8F0",
                        border_radius="7px", font_size="13px",
                        padding_x="10px", padding_y="8px", width="100%",
                        _focus={"border": "1px solid #EA580C"},
                    ),
                    spacing="1", align="start", flex="1",
                ),
                rx.vstack(
                    rx.text("Hora fin", font_size="11px", font_weight="600", color="#64748B"),
                    rx.input(
                        placeholder="21:00",
                        value=FoodState.promo_form_hora_fin,
                        on_change=FoodState.set_promo_form_hora_fin,
                        type="time",
                        background="#F8FAFC", border="1px solid #E2E8F0",
                        border_radius="7px", font_size="13px",
                        padding_x="10px", padding_y="8px", width="100%",
                        _focus={"border": "1px solid #EA580C"},
                    ),
                    spacing="1", align="start", flex="1",
                ),
                spacing="3", width="100%",
            ),
            rx.vstack(
                rx.text("Descripción", font_size="11px", font_weight="600", color="#64748B"),
                rx.input(
                    placeholder="Descripción breve (opcional)",
                    value=FoodState.promo_form_descripcion,
                    on_change=FoodState.set_promo_form_descripcion,
                    background="#F8FAFC", border="1px solid #E2E8F0",
                    border_radius="7px", font_size="13px",
                    padding_x="10px", padding_y="8px", width="100%",
                    _focus={"border": "1px solid #EA580C"},
                ),
                spacing="1", align="start", width="100%",
            ),
            rx.hstack(
                rx.button(
                    rx.cond(FoodState.promo_form_editando, "Actualizar", "Crear promoción"),
                    on_click=FoodState.guardar_promocion,
                    background="#EA580C", color="#FFFFFF",
                    border_radius="7px", font_size="13px", font_weight="700",
                    padding_x="16px", padding_y="8px", cursor="pointer",
                    _hover={"background": "#C2410C"},
                ),
                rx.cond(
                    FoodState.promo_form_editando,
                    rx.button(
                        "Cancelar",
                        on_click=FoodState.cancelar_promo_form,
                        background="#F1F5F9", color="#64748B",
                        border="1px solid #E2E8F0", border_radius="7px",
                        font_size="13px", padding_x="16px", padding_y="8px",
                        cursor="pointer", _hover={"background": "#E2E8F0"},
                    ),
                    rx.fragment(),
                ),
                spacing="2", justify="end", width="100%",
            ),
            spacing="3", width="100%",
        ),
        background="#F8FAFC", border="1px solid #E2E8F0",
        border_radius="8px", padding="12px 14px", width="100%",
    )


def _promo_activa_banner() -> rx.Component:
    return rx.cond(
        FoodState.hay_promo_activa,
        rx.box(
            rx.hstack(
                rx.icon(tag="zap", size=14, color="#B45309"),
                rx.vstack(
                    rx.text(
                        "¡Promoción activa ahora: " + FoodState.promo_activa_nombre + "!",
                        font_size="13px", font_weight="700", color="#0F172A",
                    ),
                    rx.text(
                        FoodState.promo_activa_descuento_texto,
                        font_size="12px", color="#78350F",
                    ),
                    spacing="0", align="start",
                ),
                spacing="2", align="center", width="100%",
            ),
            background="#FFFBEB", border="1px solid #FDE68A",
            border_radius="10px", padding="12px 16px", width="100%",
        ),
        rx.fragment(),
    )


def _promociones_content() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.link(
                rx.hstack(
                    rx.icon(tag="arrow_left", size=13, color="#64748B"),
                    rx.text("Panel del Dueño", font_size="12px", color="#64748B"),
                    spacing="1", align="center",
                ),
                href="/dono", _hover={"opacity": "0.7"},
            ),
            rx.spacer(),
        ),
        rx.text("Promociones", font_size="22px", font_weight="800", color="#0F172A"),
        rx.cond(
            FoodState.mensaje != "",
            rx.box(
                rx.text(FoodState.mensaje, font_size="13px", color="#15803D", font_weight="600"),
                background="#F0FDF4", border="1px solid #BBF7D0",
                border_radius="8px", padding="10px 14px", width="100%",
            ),
            rx.fragment(),
        ),
        _promo_activa_banner(),
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.icon(tag="plus_circle", size=14, color="#EA580C"),
                    rx.text(
                        rx.cond(FoodState.promo_form_editando, "Editar promoción", "Crear promoción"),
                        font_size="14px", font_weight="700", color="#0F172A",
                    ),
                    spacing="2", align="center",
                ),
                _promo_form(),
                spacing="3", width="100%",
            ),
            background="#FFFFFF", border="1px solid #E2E8F0",
            border_radius="12px", padding="16px 18px", width="100%",
            box_shadow="0 1px 3px rgba(0,0,0,0.06)",
        ),
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.icon(tag="tag", size=14, color="#EA580C"),
                    rx.text("Mis promociones", font_size="14px", font_weight="700", color="#0F172A"),
                    rx.spacer(),
                    rx.button(
                        rx.icon(tag="refresh_cw", size=12),
                        on_click=FoodState.cargar_promociones,
                        background="#F1F5F9", color="#64748B",
                        border="1px solid #E2E8F0", border_radius="6px",
                        padding="4px 8px", cursor="pointer",
                        _hover={"background": "#E2E8F0"},
                    ),
                    width="100%", align="center",
                ),
                rx.cond(
                    FoodState.promociones_lista.length() > 0,
                    rx.vstack(
                        rx.foreach(FoodState.promociones_lista, _promo_row),
                        spacing="1", width="100%",
                    ),
                    rx.center(
                        rx.text("Sin promociones configuradas.", font_size="13px", color="#94A3B8"),
                        padding_y="20px", width="100%",
                    ),
                ),
                spacing="3", width="100%",
            ),
            background="#FFFFFF", border="1px solid #E2E8F0",
            border_radius="12px", padding="16px 18px", width="100%",
            box_shadow="0 1px 3px rgba(0,0,0,0.06)",
        ),
        spacing="4", width="100%",
    )


@rx.page(
    route="/promociones",
    on_load=[AdminLocalState.on_load_dono, FoodState.on_load_promociones],
)
def promociones_page() -> rx.Component:
    return _dono_shell(_promociones_content())
