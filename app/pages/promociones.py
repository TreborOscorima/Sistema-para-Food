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


def _promo_card(p: PromocionView) -> rx.Component:
    header_bg = rx.cond(p.activa, "#16A34A", "#94A3B8")
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.text(
                    rx.cond(p.activa, "🟢 ACTIVA", "⏸ PAUSADA"),
                    font_size="12px", font_weight="700", color="#FFFFFF",
                ),
                rx.spacer(),
                rx.cond(
                    p.aplica_ahora,
                    rx.text("Aplica ahora", font_size="11px", color="#FFFFFF", opacity="0.85"),
                    rx.fragment(),
                ),
                width="100%", align="center",
            ),
            background=header_bg, padding="12px 16px", width="100%",
        ),
        rx.vstack(
            rx.hstack(
                rx.text(p.nombre, font_size="16px", font_weight="800", color="#0F172A"),
                _tipo_label(p.tipo),
                spacing="2", align="center",
            ),
            rx.text(p.descuento_texto, font_size="13px", color="#64748B", line_height="1.4"),
            rx.cond(
                p.horario_texto != "",
                rx.text(p.horario_texto, font_size="11px", color="#94A3B8"),
                rx.fragment(),
            ),
            rx.hstack(
                rx.link(
                    "Editar",
                    on_click=FoodState.editar_promocion(p.id),
                    font_size="12px", font_weight="600", color="#64748B",
                    cursor="pointer", padding="5px 10px",
                    border="1px solid #E2E8F0", border_radius="6px",
                    _hover={"border_color": "#94A3B8"},
                ),
                rx.link(
                    rx.cond(p.activa, "Pausar", "Activar"),
                    on_click=FoodState.toggle_promo_activa(p.id),
                    font_size="12px", font_weight="600",
                    color=rx.cond(p.activa, "#DC2626", "#EA580C"),
                    cursor="pointer", padding="5px 10px",
                    border=rx.cond(p.activa, "1px solid #FCA5A5", "1px solid #FED7AA"),
                    border_radius="6px",
                    _hover={"opacity": "0.8"},
                ),
                spacing="2", justify="end", width="100%", margin_top="6px",
            ),
            spacing="2", align="start", width="100%", padding="16px",
        ),
        background="#FFFFFF",
        border=rx.cond(p.aplica_ahora, "2px solid #EA580C", "1px solid #E2E8F0"),
        border_radius="16px", overflow="hidden",
        opacity=rx.cond(p.activa, "1", "0.65"),
        width="100%",
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
                rx.button(
                    "Cancelar",
                    on_click=FoodState.cancelar_promo_form,
                    background="#F1F5F9", color="#64748B",
                    border="1px solid #E2E8F0", border_radius="7px",
                    font_size="13px", padding_x="16px", padding_y="8px",
                    cursor="pointer", _hover={"background": "#E2E8F0"},
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


def _promo_modal_content() -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.icon(
                tag=rx.cond(FoodState.promo_form_editando, "pencil", "circle_plus"),
                size=14, color="#EA580C",
            ),
            rx.text(
                rx.cond(FoodState.promo_form_editando, "Editar promoción", "Nueva promoción"),
                font_size="14px", font_weight="700", color="#0F172A",
            ),
            spacing="2", align="center", margin_bottom="12px",
        ),
        _promo_form(),
        width="100%",
    )


def _promo_nueva_placeholder() -> rx.Component:
    return rx.box(
        rx.text("🏷️", font_size="36px", line_height="1"),
        rx.text("Crear nueva promoción", font_size="14px", font_weight="700", color="#94A3B8",
                margin_top="8px"),
        rx.text("Descuento, combo, 2×1…", font_size="12px", color="#CBD5E1", margin_top="2px"),
        on_click=FoodState.abrir_nueva_promo,
        background="#FFFFFF", border="2px dashed #E2E8F0",
        border_radius="16px", padding="36px 16px",
        display="flex", flex_direction="column",
        align_items="center", justify_content="center",
        cursor="pointer", text_align="center", width="100%", height="100%",
        _hover={"border_color": "#FED7AA", "background": "#FFF7ED"},
    )


def _promociones_content() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.vstack(
                rx.text("Promociones", font_size="22px", font_weight="800", color="#0F172A"),
                rx.text("Descuentos, combos y ofertas activas", font_size="13px", color="#64748B"),
                spacing="0", align="start",
            ),
            rx.spacer(),
            rx.dialog.root(
                rx.button(
                    rx.hstack(
                        rx.icon(tag="plus", size=13),
                        rx.text("Nueva promo", font_size="13px", font_weight="700"),
                        spacing="1", align="center",
                    ),
                    on_click=FoodState.abrir_nueva_promo,
                    background="#EA580C", color="#FFFFFF", border_radius="9px",
                    padding_x="16px", padding_y="9px", cursor="pointer",
                    _hover={"background": "#C2410C"},
                ),
                rx.dialog.content(_promo_modal_content(), class_name="light"),
                open=FoodState.promo_form_visible,
                on_open_change=FoodState.set_promo_form_visible,
            ),
            width="100%", align="center",
        ),
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
        rx.grid(
            rx.foreach(FoodState.promociones_lista, _promo_card),
            _promo_nueva_placeholder(),
            columns=rx.breakpoints(initial="1", sm="2", lg="3"),
            gap="16px", width="100%",
        ),
        spacing="4", width="100%",
    )


@rx.page(
    route="/promociones",
    on_load=[AdminLocalState.on_load_dono, FoodState.on_load_promociones],
    title="TUWAYKIFOOD | Promociones",
)
def promociones_page() -> rx.Component:
    return _dono_shell(_promociones_content())
