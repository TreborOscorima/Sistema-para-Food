"""Página de gestión de clientes y alertas de cumpleaños."""

from __future__ import annotations

import reflex as rx

from app.states.food_state import FoodState, ClienteView, AdminLocalState
from app.pages.dono import _dono_shell


def _birthday_badge(c: ClienteView) -> rx.Component:
    return rx.cond(
        c.cumple_hoy,
        rx.badge("🎂 Hoy", background="#FEF9C3", color="#713F12",
                 border="1px solid #FDE047", border_radius="5px", font_size="10px", padding="2px 6px"),
        rx.cond(
            c.cumple_pronto,
            rx.badge(
                "en " + c.dias_para_cumple.to_string() + "d",
                background="#DBEAFE", color="#1D4ED8",
                border="1px solid #BFDBFE", border_radius="5px", font_size="10px", padding="2px 6px",
            ),
            rx.fragment(),
        ),
    )


def _cliente_row(c: ClienteView) -> rx.Component:
    return rx.hstack(
        rx.box(
            rx.text(c.nombre[:1].upper(), font_size="14px", font_weight="800", color="#FFFFFF"),
            width="34px",
            height="34px",
            border_radius="full",
            background=rx.cond(c.cumple_hoy, "#F59E0B", "#EA580C"),
            display="flex",
            align_items="center",
            justify_content="center",
            flex_shrink="0",
        ),
        rx.vstack(
            rx.hstack(
                rx.text(c.nombre, font_size="13px", font_weight="700", color="#0F172A"),
                _birthday_badge(c),
                spacing="2",
                align="center",
            ),
            rx.hstack(
                rx.cond(
                    c.telefono != "",
                    rx.hstack(
                        rx.icon(tag="phone", size=10, color="#94A3B8"),
                        rx.text(c.telefono, font_size="11px", color="#64748B"),
                        spacing="1", align="center",
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    c.fecha_nac_texto != "",
                    rx.hstack(
                        rx.icon(tag="cake", size=10, color="#94A3B8"),
                        rx.text(c.fecha_nac_texto, font_size="11px", color="#64748B"),
                        spacing="1", align="center",
                    ),
                    rx.fragment(),
                ),
                spacing="3",
                align="center",
            ),
            spacing="0",
            align="start",
            flex="1",
        ),
        rx.hstack(
            rx.button(
                rx.icon(tag="pencil", size=12),
                on_click=FoodState.editar_cliente(c.id),
                background="#F1F5F9", color="#475569",
                border="1px solid #E2E8F0", border_radius="6px",
                padding="4px 8px", cursor="pointer",
                _hover={"background": "#E2E8F0"},
            ),
            rx.button(
                rx.cond(c.activo, rx.icon(tag="toggle_right", size=14), rx.icon(tag="toggle_left", size=14)),
                on_click=FoodState.toggle_cliente_activo(c.id),
                background=rx.cond(c.activo, "#FEF2F2", "#F0FDF4"),
                color=rx.cond(c.activo, "#B91C1C", "#15803D"),
                border=rx.cond(c.activo, "1px solid #FECACA", "1px solid #BBF7D0"),
                border_radius="6px", padding="4px 8px", cursor="pointer",
                _hover={"opacity": "0.8"},
            ),
            spacing="2", flex_shrink="0",
        ),
        width="100%",
        align="center",
        padding="10px 12px",
        background=rx.cond(c.cumple_hoy, "#FFFBEB", "#FFFFFF"),
        border_radius="9px",
        border=rx.cond(c.cumple_hoy, "1px solid #FDE68A", "1px solid #F1F5F9"),
        gap="10px",
        _hover={"background": rx.cond(c.cumple_hoy, "#FEF9E7", "#F8FAFC")},
    )


def _cli_form() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.icon(
                    tag=rx.cond(FoodState.cli_form_editando, "pencil", "user_plus"),
                    size=13, color="#EA580C",
                ),
                rx.text(
                    rx.cond(FoodState.cli_form_editando, "Editar cliente", "Nuevo cliente"),
                    font_size="13px", font_weight="700", color="#0F172A",
                ),
                spacing="1", align="center",
            ),
            rx.hstack(
                rx.vstack(
                    rx.text("Nombre *", font_size="11px", font_weight="600", color="#64748B"),
                    rx.input(
                        placeholder="Nombre completo",
                        value=FoodState.cli_form_nombre,
                        on_change=FoodState.set_cli_form_nombre,
                        background="#F8FAFC", border="1px solid #E2E8F0",
                        border_radius="7px", font_size="13px",
                        padding_x="10px", padding_y="8px", width="100%",
                        _focus={"border": "1px solid #EA580C"},
                    ),
                    spacing="1", align="start", flex="2",
                ),
                rx.vstack(
                    rx.text("Teléfono", font_size="11px", font_weight="600", color="#64748B"),
                    rx.input(
                        placeholder="Ej: 987654321",
                        value=FoodState.cli_form_telefono,
                        on_change=FoodState.set_cli_form_telefono,
                        background="#F8FAFC", border="1px solid #E2E8F0",
                        border_radius="7px", font_size="13px",
                        padding_x="10px", padding_y="8px", width="100%",
                        _focus={"border": "1px solid #EA580C"},
                    ),
                    spacing="1", align="start", flex="1",
                ),
                spacing="3", width="100%",
            ),
            rx.hstack(
                rx.vstack(
                    rx.text("Email", font_size="11px", font_weight="600", color="#64748B"),
                    rx.input(
                        placeholder="cliente@email.com",
                        value=FoodState.cli_form_email,
                        on_change=FoodState.set_cli_form_email,
                        background="#F8FAFC", border="1px solid #E2E8F0",
                        border_radius="7px", font_size="13px",
                        padding_x="10px", padding_y="8px", width="100%",
                        _focus={"border": "1px solid #EA580C"},
                    ),
                    spacing="1", align="start", flex="2",
                ),
                rx.vstack(
                    rx.text("Fecha de nacimiento", font_size="11px", font_weight="600", color="#64748B"),
                    rx.input(
                        value=FoodState.cli_form_fecha_nac,
                        on_change=FoodState.set_cli_form_fecha_nac,
                        type="date",
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
                rx.text("Notas internas", font_size="11px", font_weight="600", color="#64748B"),
                rx.text_area(
                    placeholder="Preferencias, alergias, notas…",
                    value=FoodState.cli_form_notas,
                    on_change=FoodState.set_cli_form_notas,
                    background="#F8FAFC", border="1px solid #E2E8F0",
                    border_radius="7px", font_size="13px",
                    padding_x="10px", padding_y="8px", width="100%", rows="2",
                    _focus={"border": "1px solid #EA580C"},
                ),
                spacing="1", align="start", width="100%",
            ),
            rx.hstack(
                rx.button(
                    rx.cond(FoodState.cli_form_editando, "Actualizar", "Registrar"),
                    on_click=FoodState.guardar_cliente,
                    background="#EA580C", color="#FFFFFF",
                    border_radius="7px", font_size="13px", font_weight="700",
                    padding_x="16px", padding_y="8px", cursor="pointer",
                    _hover={"background": "#C2410C"},
                ),
                rx.cond(
                    FoodState.cli_form_editando,
                    rx.button(
                        "Cancelar",
                        on_click=FoodState.cancelar_cli_form,
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


def _cumpleanos_section() -> rx.Component:
    return rx.cond(
        (FoodState.clientes_cumpleanos_hoy.length() > 0) | (FoodState.clientes_cumpleanos_pronto.length() > 0),
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.icon(tag="cake", size=14, color="#B45309"),
                    rx.text("Cumpleaños", font_size="14px", font_weight="700", color="#0F172A"),
                    spacing="2", align="center",
                ),
                rx.cond(
                    FoodState.clientes_cumpleanos_hoy.length() > 0,
                    rx.vstack(
                        rx.text("Hoy", font_size="11px", font_weight="700", color="#B45309",
                                text_transform="uppercase", letter_spacing="0.05em"),
                        rx.foreach(
                            FoodState.clientes_cumpleanos_hoy,
                            lambda c: rx.hstack(
                                rx.text("🎂", font_size="16px"),
                                rx.vstack(
                                    rx.text(c.nombre, font_size="13px", font_weight="700", color="#0F172A"),
                                    rx.text(c.telefono, font_size="11px", color="#64748B"),
                                    spacing="0", align="start",
                                ),
                                spacing="2", align="center", width="100%",
                                padding="6px 8px", background="#FFFBEB",
                                border_radius="7px", border="1px solid #FDE68A",
                            ),
                        ),
                        spacing="2", width="100%",
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    FoodState.clientes_cumpleanos_pronto.length() > 0,
                    rx.vstack(
                        rx.text("Próximos 7 días", font_size="11px", font_weight="700", color="#64748B",
                                text_transform="uppercase", letter_spacing="0.05em"),
                        rx.foreach(
                            FoodState.clientes_cumpleanos_pronto,
                            lambda c: rx.hstack(
                                rx.text("🎁", font_size="14px"),
                                rx.text(c.nombre, font_size="12px", color="#334155", flex="1"),
                                rx.badge(
                                    "en " + c.dias_para_cumple.to_string() + " días",
                                    background="#DBEAFE", color="#1D4ED8",
                                    border_radius="5px", font_size="10px", padding="2px 6px",
                                ),
                                spacing="2", align="center", width="100%",
                                padding="5px 8px", background="#FFFFFF",
                                border_radius="6px", border="1px solid #F1F5F9",
                            ),
                        ),
                        spacing="1", width="100%",
                    ),
                    rx.fragment(),
                ),
                spacing="3", width="100%",
            ),
            background="#FFFBEB", border="1px solid #FDE68A",
            border_radius="10px", padding="14px 16px", width="100%",
        ),
        rx.fragment(),
    )


def _clientes_content() -> rx.Component:
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
        rx.text("Clientes", font_size="22px", font_weight="800", color="#0F172A"),
        rx.cond(
            FoodState.mensaje != "",
            rx.box(
                rx.text(FoodState.mensaje, font_size="13px", color="#15803D", font_weight="600"),
                background="#F0FDF4", border="1px solid #BBF7D0",
                border_radius="8px", padding="10px 14px", width="100%",
            ),
            rx.fragment(),
        ),
        _cumpleanos_section(),
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.icon(tag="user_plus", size=14, color="#EA580C"),
                    rx.text(
                        rx.cond(FoodState.cli_form_editando, "Editar cliente", "Registrar cliente"),
                        font_size="14px", font_weight="700", color="#0F172A",
                    ),
                    spacing="2", align="center",
                ),
                _cli_form(),
                spacing="3", width="100%",
            ),
            background="#FFFFFF", border="1px solid #E2E8F0",
            border_radius="12px", padding="16px 18px", width="100%",
            box_shadow="0 1px 3px rgba(0,0,0,0.06)",
        ),
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.icon(tag="users", size=14, color="#EA580C"),
                    rx.text("Lista de clientes", font_size="14px", font_weight="700", color="#0F172A"),
                    rx.spacer(),
                    rx.button(
                        rx.icon(tag="refresh_cw", size=12),
                        on_click=FoodState.cargar_clientes,
                        background="#F1F5F9", color="#64748B",
                        border="1px solid #E2E8F0", border_radius="6px",
                        padding="4px 8px", cursor="pointer",
                        _hover={"background": "#E2E8F0"},
                    ),
                    width="100%", align="center",
                ),
                rx.input(
                    placeholder="Buscar por nombre o teléfono…",
                    value=FoodState.cli_busqueda,
                    on_change=FoodState.set_cli_busqueda,
                    background="#F8FAFC", border="1px solid #E2E8F0",
                    border_radius="8px", font_size="13px",
                    padding_x="12px", padding_y="8px", width="100%",
                    _focus={"border": "1px solid #EA580C"},
                ),
                rx.cond(
                    FoodState.clientes_filtrados.length() > 0,
                    rx.vstack(
                        rx.foreach(FoodState.clientes_filtrados, _cliente_row),
                        spacing="1", width="100%",
                    ),
                    rx.center(
                        rx.text("Sin clientes registrados.", font_size="13px", color="#94A3B8"),
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
    route="/clientes",
    on_load=[AdminLocalState.on_load_dono, FoodState.on_load_clientes],
)
def clientes_page() -> rx.Component:
    return _dono_shell(_clientes_content())
