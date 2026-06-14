"""Pagina de configuracion — impresoras ESC/POS."""

from __future__ import annotations

import reflex as rx

from app.components.shared import app_shell
from app.states.food_state import FoodState


def _toggle_btn(activo: bool, on_click) -> rx.Component:
    return rx.button(
        rx.hstack(
            rx.box(
                width="16px",
                height="16px",
                border_radius="full",
                background=rx.cond(activo, "#FFFFFF", "#CBD5E1"),
                transition="all 0.15s",
            ),
            rx.text(
                rx.cond(activo, "Activada", "Desactivada"),
                font_size="13px",
                font_weight="600",
                color=rx.cond(activo, "#FFFFFF", "#64748B"),
            ),
            spacing="2",
            align="center",
        ),
        on_click=on_click,
        background=rx.cond(activo, "#15803D", "#F1F5F9"),
        border=rx.cond(activo, "1px solid #15803D", "1px solid #E2E8F0"),
        border_radius="8px",
        padding="6px 14px",
        cursor="pointer",
        _hover={"opacity": "0.85"},
    )


def _section_header(title: str, icon: str) -> rx.Component:
    return rx.hstack(
        rx.box(
            rx.icon(tag=icon, size=16, color="#EA580C"),
            width="32px",
            height="32px",
            border_radius="8px",
            background="#FFF7ED",
            border="1px solid #FED7AA",
            display="flex",
            align_items="center",
            justify_content="center",
        ),
        rx.text(title, font_size="15px", font_weight="700", color="#0F172A"),
        spacing="2",
        align="center",
    )


def _field_row(label: str, value, on_change, placeholder: str = "", tipo: str = "text") -> rx.Component:
    return rx.hstack(
        rx.text(label, font_size="13px", color="#334155", min_width="140px", font_weight="600"),
        rx.input(
            placeholder=placeholder,
            value=value,
            on_change=on_change,
            type=tipo,
            background="#FFFFFF",
            border="1px solid #E2E8F0",
            color="#0F172A",
            border_radius="8px",
            padding_x="12px",
            padding_y="8px",
            font_size="13px",
            flex="1",
            _focus={"border": "1px solid #EA580C", "box_shadow": "0 0 0 2px rgba(234,88,12,0.1)"},
        ),
        spacing="3",
        align="center",
        width="100%",
    )


def _printer_section(
    title: str,
    icon: str,
    activo: bool,
    toggle_event,
    ip_value,
    ip_change,
    puerto_value,
    puerto_change,
) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                _section_header(title, icon),
                rx.spacer(),
                _toggle_btn(activo, toggle_event),
                width="100%",
                align="center",
            ),
            rx.cond(
                activo,
                rx.vstack(
                    _field_row("Dirección IP", ip_value, ip_change, "192.168.1.100"),
                    _field_row("Puerto", puerto_value, puerto_change, "9100", "number"),
                    spacing="3",
                    width="100%",
                ),
                rx.text(
                    "Activa la impresora para configurar la conexion.",
                    font_size="12px",
                    color="#94A3B8",
                    font_style="italic",
                ),
            ),
            spacing="4",
            width="100%",
        ),
        background="#FFFFFF",
        border="1px solid #E2E8F0",
        border_radius="12px",
        padding="16px 18px",
        width="100%",
        box_shadow="0 1px 3px rgba(0,0,0,0.06)",
    )


def _configuracion_content() -> rx.Component:
    return rx.vstack(
        # Header
        rx.hstack(
            rx.text("Configuracion", font_size="22px", font_weight="800", color="#0F172A"),
            rx.spacer(),
            rx.button(
                rx.hstack(
                    rx.icon(tag="save", size=15, color="#FFFFFF"),
                    rx.text("Guardar cambios", font_size="13px", font_weight="700", color="#FFFFFF"),
                    spacing="2",
                    align="center",
                ),
                on_click=FoodState.guardar_config_impresora,
                background="#EA580C",
                border_radius="8px",
                padding_x="16px",
                padding_y="8px",
                cursor="pointer",
                _hover={"background": "#C2410C"},
            ),
            width="100%",
            align="center",
        ),
        # Mensaje
        rx.cond(
            FoodState.mensaje != "",
            rx.box(
                rx.text(FoodState.mensaje, font_size="13px", color="#15803D", font_weight="600"),
                background="#F0FDF4",
                border="1px solid #BBF7D0",
                border_radius="8px",
                padding="10px 14px",
                width="100%",
            ),
            rx.fragment(),
        ),
        # Nombre del local
        rx.box(
            rx.vstack(
                _section_header("Nombre del local", "store"),
                _field_row(
                    "Nombre",
                    FoodState.config_nombre_local,
                    FoodState.set_config_nombre_local,
                    "Mi Restaurante",
                ),
                spacing="4",
                width="100%",
            ),
            background="#FFFFFF",
            border="1px solid #E2E8F0",
            border_radius="12px",
            padding="16px 18px",
            width="100%",
            box_shadow="0 1px 3px rgba(0,0,0,0.06)",
        ),
        # Impresora cocina
        _printer_section(
            title="Impresora Cocina (red)",
            icon="chef_hat",
            activo=FoodState.config_cocina_activa,
            toggle_event=FoodState.toggle_config_cocina_activa,
            ip_value=FoodState.config_cocina_ip,
            ip_change=FoodState.set_config_cocina_ip,
            puerto_value=FoodState.config_cocina_puerto,
            puerto_change=FoodState.set_config_cocina_puerto,
        ),
        # Impresora caja
        _printer_section(
            title="Impresora Caja (red)",
            icon="printer",
            activo=FoodState.config_caja_activa,
            toggle_event=FoodState.toggle_config_caja_activa,
            ip_value=FoodState.config_caja_ip,
            ip_change=FoodState.set_config_caja_ip,
            puerto_value=FoodState.config_caja_puerto,
            puerto_change=FoodState.set_config_caja_puerto,
        ),
        # Nota informativa
        rx.box(
            rx.hstack(
                rx.icon(tag="info", size=14, color="#1D4ED8"),
                rx.text(
                    "Las impresoras deben estar en la misma red local (LAN). "
                    "Protocolo ESC/POS por TCP puerto 9100 (estandar). "
                    "Si no hay impresora configurada, el sistema continua sin imprimir.",
                    font_size="12px",
                    color="#334155",
                ),
                spacing="2",
                align="start",
            ),
            background="#EFF6FF",
            border="1px solid #BFDBFE",
            border_radius="8px",
            padding="12px 14px",
            width="100%",
        ),
        spacing="4",
        width="100%",
        max_width="600px",
    )


@rx.page(route="/configuracion", on_load=FoodState.on_load_configuracion)
def configuracion_page() -> rx.Component:
    return app_shell(_configuracion_content(), page_key="configuracion")
