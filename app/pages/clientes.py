"""Página de gestión de clientes y alertas de cumpleaños."""

from __future__ import annotations

import reflex as rx

from app.states.food_state import FoodState, ClienteView, AdminLocalState
from app.pages.dono import _dono_shell

_AVATAR_COLORS = ["#EA580C", "#3B82F6", "#8B5CF6", "#0D9488"]


def _avatar_color(c: ClienteView) -> rx.Var:
    idx = c.id % len(_AVATAR_COLORS)
    return rx.cond(
        c.cumple_hoy, "#F59E0B",
        rx.cond(
            idx == 0, _AVATAR_COLORS[0],
            rx.cond(
                idx == 1, _AVATAR_COLORS[1],
                rx.cond(idx == 2, _AVATAR_COLORS[2], _AVATAR_COLORS[3]),
            ),
        ),
    )


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


def _cliente_card(c: ClienteView) -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.hstack(
                rx.box(
                    rx.text(c.nombre[:1].upper(), font_size="18px", font_weight="800", color="#FFFFFF"),
                    width="44px", height="44px", border_radius="full",
                    background=_avatar_color(c),
                    display="flex", align_items="center", justify_content="center",
                    flex_shrink="0",
                ),
                rx.vstack(
                    rx.hstack(
                        rx.text(c.nombre, font_size="15px", font_weight="700", color="#0F172A"),
                        _birthday_badge(c),
                        spacing="1", align="center", flex_wrap="wrap",
                    ),
                    rx.text(
                        rx.cond(c.email != "", c.email + " · ", "") + c.telefono,
                        font_size="12px", color="#94A3B8",
                    ),
                    spacing="0", align="start", min_width="0",
                ),
                spacing="3", align="center", min_width="0", flex="1",
            ),
            rx.hstack(
                rx.icon(
                    tag="pencil", size=13, color="#94A3B8", cursor="pointer",
                    on_click=FoodState.editar_cliente(c.id),
                ),
                rx.icon(
                    tag=rx.cond(c.activo, "toggle_right", "toggle_left"),
                    size=15,
                    color=rx.cond(c.activo, "#16A34A", "#CBD5E1"),
                    cursor="pointer",
                    on_click=FoodState.toggle_cliente_activo(c.id),
                ),
                spacing="2", align="center", flex_shrink="0",
            ),
            width="100%", align="start", margin_bottom="14px",
        ),
        rx.grid(
            rx.box(
                rx.text("Visitas", font_size="11px", color="#94A3B8", font_weight="600",
                        text_transform="uppercase", letter_spacing="0.05em"),
                rx.text(c.visitas_count.to_string(), font_size="18px", font_weight="800",
                        color="#0F172A", margin_top="2px"),
                background="#F8FAFC", border_radius="8px", padding="10px", text_align="center",
            ),
            rx.box(
                rx.text("Gastado", font_size="11px", color="#94A3B8", font_weight="600",
                        text_transform="uppercase", letter_spacing="0.05em"),
                rx.text(c.gastado_texto, font_size="18px", font_weight="800",
                        color="#EA580C", margin_top="2px"),
                background="#F8FAFC", border_radius="8px", padding="10px", text_align="center",
            ),
            columns="2", gap="8px", width="100%",
        ),
        rx.hstack(
            rx.text("Última visita: " + c.ultima_visita_texto, font_size="12px", color="#64748B"),
            rx.cond(
                c.es_vip,
                rx.badge("VIP ⭐", background="#FEF9C3", color="#A16207",
                         border_radius="20px", font_size="11px", font_weight="700",
                         padding_x="8px", padding_y="2px"),
                rx.fragment(),
            ),
            spacing="2", align="center", margin_top="12px",
        ),
        background=rx.cond(c.cumple_hoy, "#FFFBEB", "#FFFFFF"),
        border=rx.cond(c.cumple_hoy, "1px solid #FDE68A", "1px solid #E2E8F0"),
        border_radius="14px", padding="18px", width="100%",
        opacity=rx.cond(c.activo, "1", "0.6"),
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
                class_name="twk-form-row",
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
                class_name="twk-form-row",
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
                    "Cancelar",
                    on_click=FoodState.cancelar_cli_form,
                    background="#F1F5F9", color="#64748B",
                    border="1px solid #E2E8F0", border_radius="7px",
                    font_size="13px", padding_x="16px", padding_y="8px",
                    cursor="pointer", _hover={"background": "#E2E8F0"},
                ),
                rx.button(
                    rx.cond(FoodState.cli_form_editando, "Actualizar", "Registrar"),
                    on_click=FoodState.guardar_cliente,
                    background="#EA580C", color="#FFFFFF",
                    border_radius="7px", font_size="13px", font_weight="700",
                    padding_x="16px", padding_y="8px", cursor="pointer",
                    _hover={"background": "#C2410C"},
                ),
                spacing="2", justify="end", width="100%",
            ),
            spacing="3", width="100%",
        ),
        background="#FFFFFF", padding="4px", width="100%",
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
        rx.cond(
            FoodState.es_pagina_standalone,
            rx.hstack(
                rx.link(
                    rx.hstack(
                        rx.icon(tag="arrow_left", size=13, color="#64748B"),
                        rx.text("Panel Administrativo", font_size="12px", color="#64748B"),
                        spacing="1", align="center",
                    ),
                    href="/admin", _hover={"opacity": "0.7"},
                ),
                rx.spacer(),
                width="100%",
            ),
            rx.fragment(),
        ),
        rx.hstack(
            rx.vstack(
                rx.text("Clientes", font_size="22px", font_weight="800", color="#0F172A"),
                rx.text("Base de clientes del local", font_size="13px", color="#64748B"),
                spacing="0",
            ),
            rx.spacer(),
            rx.input(
                placeholder="Buscar cliente...",
                value=FoodState.cli_busqueda,
                on_change=FoodState.set_cli_busqueda,
                background="#FFFFFF", border="1px solid #E2E8F0",
                border_radius="9px", font_size="13px",
                padding_x="14px", padding_y="8px",
                width=rx.breakpoints(initial="100%", sm="220px"),
                _focus={"border": "1px solid #EA580C"},
            ),
            rx.dialog.root(
                rx.dialog.trigger(
                    rx.button(
                        "+ Nuevo",
                        on_click=FoodState.abrir_nuevo_cliente,
                        background="#EA580C", color="#FFFFFF",
                        border_radius="9px", font_size="13px", font_weight="700",
                        padding_x="18px", padding_y="9px", cursor="pointer",
                        _hover={"background": "#C2410C"},
                        flex_shrink="0",
                    ),
                ),
                rx.dialog.content(
                    _cli_form(),
                    class_name="light",
                    max_width="560px",
                ),
                open=FoodState.cli_form_visible,
                on_open_change=FoodState.set_cli_form_visible,
            ),
            width="100%", align="center", gap="10px", flex_wrap="wrap",
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
        _cumpleanos_section(),
        rx.cond(
            FoodState.clientes_filtrados.length() > 0,
            rx.grid(
                rx.foreach(FoodState.clientes_filtrados, _cliente_card),
                columns=rx.breakpoints(initial="1", sm="2", lg="3"),
                gap="14px", width="100%",
            ),
            rx.center(
                rx.text("Sin clientes registrados.", font_size="13px", color="#94A3B8"),
                padding_y="40px", width="100%",
            ),
        ),
        spacing="4", width="100%",
    )


@rx.page(
    route="/clientes",
    on_load=[AdminLocalState.on_load_dono, FoodState.on_load_clientes],
    title="TUWAYKIFOOD | Clientes",
)
def clientes_page() -> rx.Component:
    return _dono_shell(_clientes_content())
