"""Pagina de configuracion con sub-modulos navegables."""

from __future__ import annotations

import reflex as rx

from app.components.shared import (
    app_shell,
    ACCENT, ACCENT_HOVER,
    DANGER_SOLID,
    DARK_700, DARK_800,
    PAGE_BACKGROUND,
    SUCCESS_SOLID,
    TEXT_MUTED, TEXT_PRIMARY, TEXT_WHITE,
    WARNING_SOLID,
)
from app.states.food_state import FoodState, MesaAdminView, SucursalView


# ─── Estado local para la sección activa ──────────────────────────────────────

class ConfigSeccionState(rx.State):
    seccion: str = "local"

    def ir_a(self, s: str) -> None:
        self.seccion = s


# ─── Sub-módulos disponibles ──────────────────────────────────────────────────

_SECCIONES = [
    ("local",       "Local",          "store",        "Nombre del restaurante"),
    ("carta",       "Carta digital",  "qr_code",      "Slug URL y código QR"),
    ("mesas",       "Mesas",          "layout_grid",  "Salón y sectores"),
    ("sucursales",  "Sucursales",     "map_pin",      "Multi-local"),
    ("impresoras",  "Impresoras",     "printer",      "Cocina y caja"),
    ("cuenta",      "Cuenta Admin",   "key_round",    "Email y contraseña"),
]


# ─── COMPONENTES INTERNOS (también exportados para dono.py) ───────────────────

def _toggle_btn(activo: bool, on_click) -> rx.Component:
    return rx.button(
        rx.hstack(
            rx.box(
                width="16px",
                height="16px",
                border_radius="full",
                background=rx.cond(activo, "#FFFFFF", "#475569"),
                transition="all 0.15s",
            ),
            rx.text(
                rx.cond(activo, "Activada", "Desactivada"),
                font_size="13px",
                font_weight="600",
                color=rx.cond(activo, "#FFFFFF", "#94A3B8"),
            ),
            spacing="2",
            align="center",
        ),
        on_click=on_click,
        background=rx.cond(activo, "#22C55E", "#1E293B"),
        border=rx.cond(activo, "1px solid #15803D", f"1px solid {DARK_700}"),
        border_radius="8px",
        padding="6px 14px",
        cursor="pointer",
        _hover={"opacity": "0.85"},
    )


def _section_header(title: str, icon: str, emoji: str = "") -> rx.Component:
    return rx.hstack(
        rx.box(
            rx.text(emoji, font_size="15px", line_height="1") if emoji
            else rx.icon(tag=icon, size=16, color=ACCENT),
            width="32px",
            height="32px",
            border_radius="8px",
            background="rgba(234,88,12,0.08)",
            border="1px solid rgba(234,88,12,0.40)",
            display="flex",
            align_items="center",
            justify_content="center",
        ),
        rx.text(title, font_size="16px", font_weight="700", color=TEXT_PRIMARY),
        spacing="3",
        align="center",
    )


def _field_row(label: str, value, on_change,
               placeholder: str = "", tipo: str = "text") -> rx.Component:
    return rx.hstack(
        rx.text(label, font_size="13px", color="#CBD5E1", font_weight="600",
                min_width="130px"),
        rx.input(
            placeholder=placeholder,
            value=value,
            on_change=on_change,
            type=tipo,
            background=DARK_800,
            border=f"1px solid {DARK_700}",
            color=TEXT_PRIMARY,
            border_radius="8px",
            padding_x="12px",
            padding_y="8px",
            font_size="13px",
            flex="1",
            _focus={"border": "1px solid #EA580C",
                    "box_shadow": "0 0 0 2px rgba(234,88,12,0.1)"},
        ),
        spacing="3",
        align="center",
        width="100%",
        class_name="twk-field-row",
    )




def _qr_section() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                _section_header("Carta digital (QR)", "qr_code"),
                rx.spacer(),
                rx.cond(
                    FoodState.config_menu_url != "",
                    rx.hstack(
                        rx.link(
                            rx.hstack(
                                rx.icon(tag="download", size=13, color=SUCCESS_SOLID),
                                rx.text("Descargar QR", font_size="12px", color=SUCCESS_SOLID,
                                        font_weight="600"),
                                spacing="1", align="center",
                            ),
                            href=FoodState.config_menu_qr_base64,
                            download="carta-qr.png",
                        ),
                        rx.link(
                            rx.hstack(
                                rx.icon(tag="external_link", size=13, color="#60A5FA"),
                                rx.text("Abrir", font_size="12px", color="#60A5FA",
                                        font_weight="600"),
                                spacing="1", align="center",
                            ),
                            href=FoodState.config_menu_url,
                            is_external=True,
                        ),
                        spacing="4", align="center",
                    ),
                    rx.fragment(),
                ),
                width="100%", align="center",
            ),
            _field_row("Slug URL", FoodState.config_slug,
                       FoodState.set_config_slug, "mi-restaurante"),
            rx.cond(
                FoodState.config_menu_url != "",
                rx.vstack(
                    rx.hstack(
                        rx.box(
                            rx.image(
                                src=FoodState.config_menu_qr_base64,
                                width="120px", height="120px",
                                border_radius="8px", border=f"1px solid {DARK_700}",
                            ),
                            padding="4px", background=DARK_800,
                            border=f"1px solid {DARK_700}", border_radius="10px",
                        ),
                        rx.vstack(
                            rx.text("URL de la carta:", font_size="11px",
                                    color=TEXT_MUTED, font_weight="600"),
                            rx.box(
                                rx.text(FoodState.config_menu_url, font_size="11px",
                                        color="#CBD5E1", word_break="break-all",
                                        font_family="monospace"),
                                background=PAGE_BACKGROUND, border=f"1px solid {DARK_700}",
                                border_radius="6px", padding="8px 10px",
                            ),
                            rx.text("Guarda para regenerar el QR con el slug actual.",
                                    font_size="11px", color=TEXT_MUTED,
                                    font_style="italic"),
                            spacing="2", align="start", flex="1",
                        ),
                        spacing="3", align="start", width="100%",
                    ),
                    width="100%",
                ),
                rx.text("Guarda la configuración para generar el QR.",
                        font_size="12px", color=TEXT_MUTED, font_style="italic"),
            ),
            rx.box(
                rx.hstack(
                    rx.icon(tag="smartphone", size=16, color="#7C3AED"),
                    rx.text("Self-Order QR", font_size="13px",
                            font_weight="700", color=TEXT_PRIMARY),
                    spacing="2", align="center",
                ),
                rx.text(
                    "Genera un token QR para cada mesa. Los clientes escanean y hacen "
                    "pedidos que van a la cola de aprobación del mozo.",
                    font_size="12px", color=TEXT_MUTED, margin_top="4px",
                ),
                rx.button(
                    rx.hstack(
                        rx.icon(tag="qr_code", size=14),
                        rx.text("Generar tokens QR para todas las mesas",
                                font_size="12px", font_weight="700"),
                        spacing="2", align="center",
                    ),
                    on_click=FoodState.generar_qr_tokens_mesas,
                    background="#7C3AED", color=TEXT_WHITE,
                    border_radius="8px", padding_x="14px", padding_y="8px",
                    cursor="pointer", margin_top="8px",
                    _hover={"background": "#6D28D9"},
                ),
                padding="14px", background="rgba(124,58,237,0.08)",
                border="1px solid rgba(124,58,237,0.20)",
                border_radius="10px", width="100%",
                margin_top="4px",
            ),
            spacing="4", width="100%",
        ),
        background=DARK_800,
        border=f"1px solid {DARK_700}",
        border_radius="12px",
        padding="20px",
        width="100%",
        box_shadow="0 1px 3px rgba(0,0,0,0.06)",
    )


def _mesa_qr_card(mesa: MesaAdminView) -> rx.Component:
    return rx.cond(
        mesa.qr_base64 != "",
        rx.vstack(
            rx.image(
                src=mesa.qr_base64,
                width="120px", height="120px",
                border_radius="6px",
            ),
            rx.text(mesa.nombre, font_size="12px", font_weight="700",
                    color=TEXT_PRIMARY, text_align="center"),
            rx.text(f"Mesa #{mesa.numero}", font_size="10px",
                    color=TEXT_MUTED, text_align="center"),
            rx.link(
                rx.hstack(
                    rx.icon(tag="download", size=11, color=SUCCESS_SOLID),
                    rx.text("Descargar", font_size="10px", color=SUCCESS_SOLID,
                            font_weight="600"),
                    spacing="1", align="center",
                ),
                href=mesa.qr_base64,
                download=f"qr-mesa-{mesa.numero}.png",
            ),
            spacing="1", align="center",
            padding="12px", background=DARK_800,
            border=f"1px solid {DARK_700}",
            border_radius="10px",
            width="160px",
        ),
        rx.fragment(),
    )


def _mesa_row(mesa: MesaAdminView) -> rx.Component:
    return rx.hstack(
        rx.text(f"#{mesa.numero}", font_size="13px", font_weight="700",
                color=TEXT_PRIMARY, min_width="36px"),
        rx.text(mesa.nombre, font_size="12px", color=TEXT_MUTED, flex="1"),
        rx.badge(mesa.sector, background=DARK_800, color=TEXT_MUTED,
                 border=f"1px solid {DARK_700}", border_radius="4px",
                 font_size="10px", padding="1px 6px"),
        rx.cond(
            mesa.qr_token != "",
            rx.badge("QR", background="rgba(124,58,237,0.12)", color="#A78BFA",
                     border="1px solid rgba(124,58,237,0.20)", border_radius="4px",
                     font_size="10px", padding="1px 6px"),
            rx.fragment(),
        ),
        rx.text(f"{mesa.capacidad} pers.", font_size="11px", color=TEXT_MUTED,
                min_width="54px"),
        rx.cond(
            mesa.activa,
            rx.badge("Activa", background="rgba(34,197,94,0.12)", color=SUCCESS_SOLID,
                     border_radius="5px", font_size="10px"),
            rx.badge("Inactiva", background="rgba(239,68,68,0.12)", color="#F87171",
                     border_radius="5px", font_size="10px"),
        ),
        rx.button("Editar", on_click=FoodState.editar_mesa_config(mesa.id),
                  background="rgba(234,88,12,0.08)", color=ACCENT, border="1px solid rgba(234,88,12,0.40)",
                  border_radius="6px", font_size="10px", cursor="pointer",
                  padding_x="7px", padding_y="3px", _hover={"opacity": "0.85"}),
        rx.button(
            rx.cond(mesa.activa, "Desactivar", "Activar"),
            on_click=FoodState.toggle_mesa_activa_config(mesa.id),
            background=rx.cond(mesa.activa, "rgba(239,68,68,0.08)", "rgba(34,197,94,0.08)"),
            color=rx.cond(mesa.activa, "#F87171", "#22C55E"),
            border=rx.cond(mesa.activa, "1px solid #FECACA", "1px solid #BBF7D0"),
            border_radius="6px", font_size="10px", cursor="pointer",
            padding_x="7px", padding_y="3px", _hover={"opacity": "0.85"},
        ),
        rx.alert_dialog.root(
            rx.alert_dialog.trigger(
                rx.button(
                    rx.icon(tag="trash_2", size=12, color="#F87171"),
                    background="rgba(239,68,68,0.08)", border="1px solid #FECACA",
                    border_radius="6px", cursor="pointer",
                    padding_x="7px", padding_y="3px", _hover={"opacity": "0.85"},
                ),
            ),
            rx.alert_dialog.content(
                rx.alert_dialog.title("¿Eliminar mesa?"),
                rx.alert_dialog.description(
                    "Se eliminará \"" + mesa.nombre + "\" permanentemente. "
                    "Esta acción no se puede deshacer. Si preferís conservarla "
                    "pero dejarla fuera de uso, usá \"Desactivar\" en su lugar.",
                    size="2",
                ),
                rx.hstack(
                    rx.alert_dialog.cancel(
                        rx.button(
                            "Cancelar",
                            background=DARK_800, color=TEXT_MUTED,
                            border=f"1px solid {DARK_700}", border_radius="8px",
                            font_size="13px", cursor="pointer",
                            padding_x="14px", padding_y="8px",
                        ),
                    ),
                    rx.alert_dialog.action(
                        rx.button(
                            "Eliminar mesa",
                            on_click=FoodState.eliminar_mesa_config(mesa.id),
                            background="#DC2626", color=TEXT_WHITE,
                            border_radius="8px", font_size="13px",
                            font_weight="700", cursor="pointer",
                            padding_x="14px", padding_y="8px",
                            _hover={"background": "#F87171"},
                        ),
                    ),
                    spacing="3", justify="end", width="100%", margin_top="16px",
                ),
            ),
        ),
        width="100%", align="center",
        padding="8px 10px", background=DARK_800,
        border_radius="8px", border=f"1px solid {DARK_700}",
        gap="8px", flex_wrap="wrap",
    )


def _mesas_qr_grid() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.icon(tag="qr_code", size=16, color="#7C3AED"),
                rx.text("QR Self-Order por mesa", font_size="14px",
                        font_weight="700", color=TEXT_PRIMARY),
                rx.spacer(),
                rx.text("Imprimí cada QR y pegalo en la mesa correspondiente.",
                        font_size="11px", color=TEXT_MUTED, font_style="italic"),
                spacing="2", align="center", width="100%",
            ),
            rx.flex(
                rx.foreach(FoodState.mesas_config, _mesa_qr_card),
                flex_wrap="wrap", gap="12px", justify="start",
                width="100%",
            ),
            spacing="3", width="100%",
        ),
        background="rgba(124,58,237,0.08)",
        border="1px solid rgba(124,58,237,0.20)",
        border_radius="12px",
        padding="16px",
        width="100%",
    )


def _mesas_section() -> rx.Component:
    return rx.box(
        rx.vstack(
            _section_header("Gestión de Mesas", "layout_grid", "🍽️"),
            # Formulario compacto
            rx.hstack(
                rx.input(
                    placeholder="N°",
                    value=FoodState.mesa_config_form_numero,
                    on_change=FoodState.set_mesa_config_form_numero,
                    type="number", min="1", width="60px",
                    background=DARK_800, border=f"1px solid {DARK_700}",
                    color=TEXT_PRIMARY, border_radius="8px",
                    padding_x="8px", padding_y="7px", font_size="13px",
                    _focus={"border_color": ACCENT,
                            "box_shadow": "0 0 0 2px rgba(234,88,12,0.1)"},
                ),
                rx.input(
                    placeholder="Nombre (ej: Terraza 1)",
                    value=FoodState.mesa_config_form_nombre,
                    on_change=FoodState.set_mesa_config_form_nombre,
                    flex="1", min_width="120px",
                    background=DARK_800, border=f"1px solid {DARK_700}",
                    color=TEXT_PRIMARY, border_radius="8px",
                    padding_x="10px", padding_y="7px", font_size="13px",
                    _focus={"border_color": ACCENT,
                            "box_shadow": "0 0 0 2px rgba(234,88,12,0.1)"},
                ),
                rx.input(
                    placeholder="Sector (ej: Salón)",
                    value=FoodState.mesa_config_form_sector,
                    on_change=FoodState.set_mesa_config_form_sector,
                    width="120px",
                    background=DARK_800, border=f"1px solid {DARK_700}",
                    color=TEXT_PRIMARY, border_radius="8px",
                    padding_x="8px", padding_y="7px", font_size="13px",
                    _focus={"border_color": ACCENT,
                            "box_shadow": "0 0 0 2px rgba(234,88,12,0.1)"},
                ),
                rx.input(
                    placeholder="Cap.",
                    value=FoodState.mesa_config_form_capacidad,
                    on_change=FoodState.set_mesa_config_form_capacidad,
                    type="number", min="1", width="58px",
                    background=DARK_800, border=f"1px solid {DARK_700}",
                    color=TEXT_PRIMARY, border_radius="8px",
                    padding_x="8px", padding_y="7px", font_size="13px",
                    _focus={"border_color": ACCENT,
                            "box_shadow": "0 0 0 2px rgba(234,88,12,0.1)"},
                ),
                rx.button(
                    rx.hstack(
                        rx.icon(tag="plus", size=14, color=TEXT_WHITE),
                        rx.text(
                            rx.cond(FoodState.mesa_config_form_id > 0,
                                    "Actualizar", "Agregar"),
                            font_size="12px", font_weight="700", color=TEXT_WHITE,
                        ),
                        spacing="1", align="center",
                    ),
                    on_click=FoodState.guardar_mesa_config,
                    background=ACCENT, color=TEXT_WHITE,
                    border_radius="8px", cursor="pointer",
                    padding_x="12px", padding_y="7px",
                    _hover={"background": ACCENT_HOVER},
                    white_space="nowrap",
                ),
                rx.cond(
                    FoodState.mesa_config_form_id > 0,
                    rx.button(
                        rx.icon(tag="x", size=14, color=TEXT_MUTED),
                        on_click=FoodState.cancelar_mesa_config_form,
                        background=DARK_800, border=f"1px solid {DARK_700}",
                        border_radius="8px", cursor="pointer",
                        padding="7px",
                        _hover={"background": DARK_700},
                    ),
                    rx.fragment(),
                ),
                spacing="2", width="100%", align="center",
                flex_wrap="wrap",
            ),
            # Lista de mesas
            rx.cond(
                FoodState.mesas_config.length() == 0,
                rx.center(
                    rx.vstack(
                        rx.icon(tag="layout_grid", size=28, color="#CBD5E1"),
                        rx.text("Sin mesas configuradas", font_size="13px",
                                color=TEXT_MUTED),
                        rx.text("Agregue mesas usando el formulario de arriba.",
                                font_size="11px", color="#CBD5E1"),
                        spacing="1", align="center",
                    ),
                    padding_y="24px", width="100%",
                ),
                rx.vstack(
                    rx.foreach(FoodState.mesas_config, _mesa_row),
                    spacing="2", width="100%",
                ),
            ),
            spacing="4", width="100%",
        ),
        background=DARK_800,
        border=f"1px solid {DARK_700}",
        border_radius="12px",
        padding="20px",
        width="100%",
        box_shadow="0 1px 3px rgba(0,0,0,0.06)",
    )


def _admin_cuenta_section() -> rx.Component:
    return rx.box(
        rx.vstack(
            _section_header("Cuenta del Dueño", "key_round"),
            rx.text(
                "Configura email y contraseña para acceder al panel del dueño en /admin",
                font_size="12px", color=TEXT_MUTED, font_style="italic",
            ),
            _field_row("Email", FoodState.config_admin_email,
                       FoodState.set_config_admin_email,
                       "dueño@restaurante.com", "email"),
            rx.hstack(
                rx.text("Nueva clave", font_size="13px", color="#CBD5E1",
                        min_width="130px", font_weight="600"),
                rx.box(
                    rx.input(
                        placeholder="Nueva contraseña",
                        value=FoodState.config_admin_password_nueva,
                        on_change=FoodState.set_config_admin_password_nueva,
                        type=rx.cond(FoodState.config_admin_show_password, "text", "password"),
                        background=DARK_800, border=f"1px solid {DARK_700}",
                        color=TEXT_PRIMARY, border_radius="8px",
                        padding_x="12px", padding_y="8px", font_size="13px",
                        padding_right="40px", width="100%",
                    ),
                    rx.icon_button(
                        rx.icon(
                            tag=rx.cond(FoodState.config_admin_show_password, "eye_off", "eye"),
                            size=15,
                        ),
                        on_click=FoodState.toggle_config_admin_show_password,
                        type="button",
                        background="transparent", color=TEXT_MUTED, border="none",
                        width="26px", height="26px",
                        _hover={"background": DARK_700},
                        position="absolute", right="6px", top="50%",
                        transform="translateY(-50%)", cursor="pointer",
                    ),
                    position="relative", flex="1",
                ),
                spacing="3", align="center", width="100%",
                class_name="twk-field-row",
            ),
            rx.hstack(
                rx.text("Confirmar clave", font_size="13px", color="#CBD5E1",
                        min_width="130px", font_weight="600"),
                rx.box(
                    rx.input(
                        placeholder="Repite la contraseña",
                        value=FoodState.config_admin_password_confirm,
                        on_change=FoodState.set_config_admin_password_confirm,
                        type=rx.cond(FoodState.config_admin_show_password, "text", "password"),
                        background=DARK_800, border=f"1px solid {DARK_700}",
                        color=TEXT_PRIMARY, border_radius="8px",
                        padding_x="12px", padding_y="8px", font_size="13px",
                        padding_right="40px", width="100%",
                    ),
                    rx.icon_button(
                        rx.icon(
                            tag=rx.cond(FoodState.config_admin_show_password, "eye_off", "eye"),
                            size=15,
                        ),
                        on_click=FoodState.toggle_config_admin_show_password,
                        type="button",
                        background="transparent", color=TEXT_MUTED, border="none",
                        width="26px", height="26px",
                        _hover={"background": DARK_700},
                        position="absolute", right="6px", top="50%",
                        transform="translateY(-50%)", cursor="pointer",
                    ),
                    position="relative", flex="1",
                ),
                spacing="3", align="center", width="100%",
                class_name="twk-field-row",
            ),
            rx.button(
                rx.hstack(
                    rx.icon(tag="key_round", size=14, color=TEXT_WHITE),
                    rx.text("Guardar cuenta del dueño", font_size="13px",
                            font_weight="700", color=TEXT_WHITE),
                    spacing="2", align="center",
                ),
                on_click=FoodState.guardar_admin_cuenta,
                background=ACCENT, border_radius="8px",
                padding_x="16px", padding_y="8px", cursor="pointer",
                _hover={"background": ACCENT_HOVER},
                align_self="end",
            ),
            spacing="3", width="100%",
        ),
        background=DARK_800,
        border=f"1px solid {DARK_700}",
        border_radius="12px",
        padding="20px",
        width="100%",
        box_shadow="0 1px 3px rgba(0,0,0,0.06)",
    )


# ─── SIDEBAR DE SUB-MÓDULOS ───────────────────────────────────────────────────

def _seccion_item(key: str, label: str, icon: str, desc: str) -> rx.Component:
    active = ConfigSeccionState.seccion == key
    return rx.box(
        rx.hstack(
            # Icono
            rx.box(
                rx.icon(
                    tag=icon,
                    size=16,
                    color=rx.cond(active, ACCENT, TEXT_MUTED),
                ),
                width="34px",
                height="34px",
                border_radius="9px",
                background=rx.cond(active, "rgba(234,88,12,0.08)", "#0F172A"),
                border=rx.cond(active, "1px solid rgba(234,88,12,0.40)", f"1px solid {DARK_700}"),
                display="flex",
                align_items="center",
                justify_content="center",
                flex_shrink="0",
            ),
            # Texto
            rx.vstack(
                rx.text(
                    label,
                    font_size="13px",
                    font_weight=rx.cond(active, "700", "500"),
                    color=rx.cond(active, "#F1F5F9", "#CBD5E1"),
                    line_height="1",
                ),
                rx.text(
                    desc,
                    font_size="11px",
                    color=rx.cond(active, "#CBD5E1", "#94A3B8"),
                    line_height="1",
                ),
                spacing="1",
                align="start",
            ),
            spacing="3",
            align="center",
            width="100%",
        ),
        padding="10px 12px",
        border_radius="10px",
        background=rx.cond(active, "#1E293B", "transparent"),
        border=rx.cond(active, "1px solid rgba(234,88,12,0.40)", "1px solid transparent"),
        box_shadow=rx.cond(active, "0 1px 4px rgba(234,88,12,0.1)", "none"),
        cursor="pointer",
        on_click=ConfigSeccionState.ir_a(key),
        width="100%",
        transition="all 0.12s ease",
        _hover={
            "background": rx.cond(active, "#1E293B", "#334155"),
            "border": rx.cond(active, "1px solid rgba(234,88,12,0.40)", f"1px solid {DARK_700}"),
        },
    )


def _config_left_sidebar() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.text(
                "Ajustes",
                font_size="10px",
                font_weight="700",
                color=TEXT_MUTED,
                text_transform="uppercase",
                letter_spacing="0.08em",
                padding_x="4px",
                padding_bottom="4px",
            ),
            _seccion_item("local",      "Local",         "store",       "Nombre del restaurante"),
            _seccion_item("carta",      "Carta digital", "qr_code",     "Slug URL y código QR"),
            _seccion_item("mesas",      "Mesas",         "layout_grid", "Salón y sectores"),
            _seccion_item("impresoras", "Impresoras",    "printer",     "Cocina y caja"),
            _seccion_item("cuenta",     "Cuenta Admin",  "key_round",   "Email y contraseña"),
            spacing="1",
            width="100%",
            align="start",
        ),
        padding="12px",
        background=PAGE_BACKGROUND,
        border=f"1px solid {DARK_700}",
        border_radius="14px",
        width="210px",
        flex_shrink="0",
    )


def _tab_pill(key: str, label: str, icon: str) -> rx.Component:
    active = ConfigSeccionState.seccion == key
    return rx.box(
        rx.hstack(
            rx.icon(
                tag=icon, size=14,
                color=rx.cond(active, ACCENT, TEXT_MUTED),
            ),
            rx.text(
                label,
                font_size="12px",
                font_weight=rx.cond(active, "700", "500"),
                color=rx.cond(active, "#F1F5F9", "#94A3B8"),
                white_space="nowrap",
            ),
            spacing="2", align="center",
        ),
        on_click=ConfigSeccionState.ir_a(key),
        padding="8px 14px",
        border_radius="20px",
        background=rx.cond(active, "#1E293B", "transparent"),
        border=rx.cond(active, "1px solid rgba(234,88,12,0.40)", "1px solid transparent"),
        box_shadow=rx.cond(active, "0 1px 4px rgba(234,88,12,0.12)", "none"),
        cursor="pointer",
        flex_shrink="0",
        transition="all 0.12s ease",
        _hover={"background": rx.cond(active, "#1E293B", "#334155")},
    )


def _config_nav_tabs() -> rx.Component:
    """Barra horizontal de tabs para mobile/tablet — desplazable en X."""
    return rx.box(
        rx.hstack(
            _tab_pill("local",      "Local",      "store"),
            _tab_pill("carta",      "Carta",      "qr_code"),
            _tab_pill("mesas",      "Mesas",      "layout_grid"),
            _tab_pill("impresoras", "Impresoras", "printer"),
            _tab_pill("cuenta",     "Cuenta",     "key_round"),
            spacing="1",
            padding="4px",
        ),
        overflow_x="auto",
        background=PAGE_BACKGROUND,
        border=f"1px solid {DARK_700}",
        border_radius="12px",
        width="100%",
    )


# ─── CONTENIDO POR SECCIÓN ────────────────────────────────────────────────────

def _resumen_widget(icon: str, label: str, value, href: str) -> rx.Component:
    return rx.link(
        rx.vstack(
            rx.hstack(
                rx.icon(tag=icon, size=15, color=ACCENT),
                rx.text(label, font_size="12px", font_weight="700", color=TEXT_PRIMARY),
                spacing="2", align="center",
            ),
            rx.text(value, font_size="24px", font_weight="800", color=TEXT_PRIMARY),
            rx.hstack(
                rx.text("Gestionar", font_size="11px", font_weight="600", color=ACCENT),
                rx.icon(tag="arrow_right", size=11, color=ACCENT),
                spacing="1", align="center",
            ),
            spacing="1", align="start", width="100%",
        ),
        on_click=lambda: ConfigSeccionState.ir_a(href),
        background=DARK_800, border=f"1px solid {DARK_700}",
        border_radius="12px", padding="16px",
        width="100%", text_decoration="none", cursor="pointer",
        box_shadow="0 1px 3px rgba(0,0,0,0.06)",
        _hover={"border_color": "rgba(234,88,12,0.40)", "background": "rgba(234,88,12,0.08)"},
        transition="all 0.15s ease",
    )


def _content_local() -> rx.Component:
    return rx.grid(
        rx.vstack(
            # ── Card 1: Identificación del local ─────────────────────────────
            rx.box(
                rx.vstack(
                    _section_header("Identificación del local", "store", "🏪"),
                    rx.text(
                        "Estos datos aparecen en el encabezado del comprobante de pago.",
                        font_size="12px", color=TEXT_MUTED,
                    ),
                    _field_row("Nombre del local", FoodState.config_nombre_local,
                               FoodState.set_config_nombre_local, "Mi Restaurante"),
                    _field_row("Sucursal", FoodState.config_sucursal,
                               FoodState.set_config_sucursal, "Casa Matriz"),
                    _field_row("RUC / CUIT", FoodState.config_ruc,
                               FoodState.set_config_ruc, "20XXXXXXXXX"),
                    _field_row("Dirección", FoodState.config_direccion,
                               FoodState.set_config_direccion, "Av. Principal 123"),
                    _field_row("Teléfono", FoodState.config_telefono,
                               FoodState.set_config_telefono, "999-999-999"),
                    rx.vstack(
                        rx.text("Logo de la empresa", font_size="12px",
                                font_weight="600", color=TEXT_MUTED),
                        rx.text("Se muestra como tarjeta en la pantalla de inicio de sesión.",
                                font_size="11px", color=TEXT_MUTED),
                        rx.cond(
                            FoodState.config_logo_url != "",
                            rx.hstack(
                                rx.image(
                                    src=FoodState.config_logo_url,
                                    width="72px", height="72px",
                                    object_fit="cover",
                                    border_radius="10px",
                                    border=f"1px solid {DARK_700}",
                                ),
                                rx.vstack(
                                    rx.text("Logo cargado", font_size="11px",
                                            color=SUCCESS_SOLID, font_weight="600"),
                                    rx.button(
                                        "Quitar logo",
                                        on_click=FoodState.quitar_logo_empresa,
                                        background="rgba(239,68,68,0.08)", color="#F87171",
                                        border="1px solid #FECACA", border_radius="6px",
                                        font_size="11px", cursor="pointer",
                                        padding_x="8px", padding_y="3px",
                                        _hover={"opacity": "0.85"},
                                    ),
                                    spacing="2", align="start",
                                ),
                                spacing="3", align="center",
                            ),
                            rx.upload(
                                rx.vstack(
                                    rx.icon(tag="image_plus", size=20, color=TEXT_MUTED),
                                    rx.text("Arrastre o haga clic", font_size="11px",
                                            color=TEXT_MUTED),
                                    rx.text("JPG, PNG, WEBP — max 5MB", font_size="10px",
                                            color=TEXT_MUTED),
                                    spacing="1", align="center",
                                ),
                                id="upload_logo_empresa",
                                on_drop=FoodState.handle_upload_logo_empresa(
                                    rx.upload_files(upload_id="upload_logo_empresa")
                                ),
                                accept={
                                    "image/jpeg": [".jpg", ".jpeg"],
                                    "image/png": [".png"],
                                    "image/webp": [".webp"],
                                },
                                max_files=1,
                                border="2px dashed #334155",
                                border_radius="8px",
                                padding="16px",
                                width="100%",
                                background=PAGE_BACKGROUND,
                                cursor="pointer",
                                _hover={"border_color": ACCENT, "background": "rgba(234,88,12,0.08)"},
                            ),
                        ),
                        spacing="2", width="100%",
                    ),
                    rx.button(
                        rx.hstack(
                            rx.icon(tag="save", size=14, color=TEXT_WHITE),
                            rx.text("Guardar información", font_size="13px",
                                    font_weight="700", color=TEXT_WHITE),
                            spacing="2", align="center",
                        ),
                        on_click=FoodState.guardar_config_impresora,
                        background=ACCENT, border_radius="8px",
                        padding_x="16px", padding_y="9px", cursor="pointer",
                        _hover={"background": ACCENT_HOVER}, align_self="end",
                    ),
                    spacing="4", width="100%",
                ),
                background=DARK_800, border=f"1px solid {DARK_700}",
                border_radius="12px", padding="20px",
                width="100%", box_shadow="0 1px 3px rgba(0,0,0,0.06)",
            ),
            # ── Card 2: Ticket y comprobante ─────────────────────────────────
            rx.box(
                rx.vstack(
                    _section_header("Ticket y comprobante", "receipt", "🧾"),
                    rx.text(
                        "Personaliza el pie del ticket y la configuración fiscal.",
                        font_size="12px", color=TEXT_MUTED,
                    ),
                    # Mensaje al pie
                    rx.vstack(
                        rx.text("Mensaje al pie del ticket", font_size="13px",
                                font_weight="600", color="#CBD5E1"),
                        rx.text_area(
                            placeholder="¡Gracias por su preferencia!",
                            value=FoodState.config_mensaje_ticket,
                            on_change=FoodState.set_config_mensaje_ticket,
                            background=DARK_800, border=f"1px solid {DARK_700}",
                            color=TEXT_PRIMARY, border_radius="8px",
                            padding_x="12px", padding_y="8px",
                            font_size="13px", width="100%", rows="2",
                            _focus={"border": "1px solid #EA580C",
                                    "box_shadow": "0 0 0 2px rgba(234,88,12,0.1)"},
                        ),
                        spacing="2", width="100%",
                    ),
                    # Impuesto toggle + nombre + porcentaje
                    rx.vstack(
                        rx.hstack(
                            rx.vstack(
                                rx.text("Mostrar impuesto en el ticket", font_size="13px",
                                        font_weight="600", color="#CBD5E1"),
                                rx.text("Muestra el desglose subtotal + impuesto + Total.",
                                        font_size="11px", color=TEXT_MUTED),
                                spacing="0", align="start",
                            ),
                            rx.spacer(),
                            _toggle_btn(
                                FoodState.config_mostrar_iva,
                                FoodState.toggle_config_mostrar_iva,
                            ),
                            width="100%", align="center",
                        ),
                        rx.cond(
                            FoodState.config_mostrar_iva,
                            rx.vstack(
                                _field_row(
                                    "Nombre del impuesto",
                                    FoodState.config_nombre_impuesto,
                                    FoodState.set_config_nombre_impuesto,
                                    "IGV, IVA, VAT...",
                                ),
                                _field_row(
                                    "Porcentaje (%)",
                                    FoodState.config_porcentaje_iva,
                                    FoodState.set_config_porcentaje_iva,
                                    "18",
                                    "number",
                                ),
                                spacing="3", width="100%",
                            ),
                            rx.fragment(),
                        ),
                        spacing="3", width="100%",
                    ),
                    # Preview del ticket
                    rx.box(
                        rx.hstack(
                            rx.icon(tag="eye", size=13, color=TEXT_MUTED),
                            rx.text("Vista previa del ticket", font_size="12px",
                                    font_weight="600", color=TEXT_MUTED),
                            spacing="1", align="center", margin_bottom="6px",
                        ),
                        rx.box(
                            rx.text(
                                FoodState.ticket_preview_text,
                                font_family="'Courier New', Courier, monospace",
                                font_size="10px",
                                line_height="1.35",
                                color="#1E293B",
                                white_space="pre",
                            ),
                            background="#FFFDF7",
                            border=f"1px solid {DARK_700}",
                            border_radius="6px",
                            padding="10px",
                            overflow_x="auto",
                            max_height="340px",
                            overflow_y="auto",
                        ),
                        width="100%",
                    ),
                    rx.button(
                        rx.hstack(
                            rx.icon(tag="save", size=14, color=TEXT_WHITE),
                            rx.text("Guardar ticket", font_size="13px",
                                    font_weight="700", color=TEXT_WHITE),
                            spacing="2", align="center",
                        ),
                        on_click=FoodState.guardar_config_impresora,
                        background=ACCENT, border_radius="8px",
                        padding_x="16px", padding_y="9px", cursor="pointer",
                        _hover={"background": ACCENT_HOVER}, align_self="end",
                    ),
                    spacing="4", width="100%",
                ),
                background=DARK_800, border=f"1px solid {DARK_700}",
                border_radius="12px", padding="20px",
                width="100%", box_shadow="0 1px 3px rgba(0,0,0,0.06)",
            ),
            spacing="4", width="100%",
        ),
        rx.vstack(
            _resumen_widget("layout_grid", "Mesas y salones",
                             FoodState.mesas_config.length(), "mesas"),
            _resumen_widget("printer", "Impresoras",
                             FoodState.config_ticket_paper_width_mm + "mm", "impresoras"),
            spacing="3", width="100%",
        ),
        columns=rx.breakpoints(initial="1", lg="2fr 1fr"),
        gap="16px",
        width="100%",
    )


def _content_carta() -> rx.Component:
    return rx.vstack(
        _qr_section(),
        rx.button(
            rx.hstack(
                rx.icon(tag="save", size=14, color=TEXT_WHITE),
                rx.text("Guardar y regenerar QR", font_size="13px",
                        font_weight="700", color=TEXT_WHITE),
                spacing="2", align="center",
            ),
            on_click=FoodState.guardar_config_impresora,
            background=ACCENT, border_radius="8px",
            padding_x="16px", padding_y="9px",
            cursor="pointer", _hover={"background": ACCENT_HOVER},
            align_self="end",
        ),
        width="100%",
        spacing="4",
    )


def _content_mesas() -> rx.Component:
    return rx.vstack(
        _mesas_section(),
        _mesas_qr_grid(),
        width="100%",
        spacing="4",
    )


def _paper_width_option(label: str, value: str) -> rx.Component:
    seleccionado = FoodState.config_ticket_paper_width_mm == value
    return rx.box(
        rx.text(label, font_size="13px", font_weight="700"),
        on_click=FoodState.set_config_ticket_paper_width_mm(value),
        background=rx.cond(seleccionado, ACCENT, DARK_800),
        color=rx.cond(seleccionado, "#FFFFFF", "#CBD5E1"),
        border=rx.cond(seleccionado, "1px solid #EA580C", f"1px solid {DARK_700}"),
        border_radius="8px", padding="10px 20px", cursor="pointer",
        _hover={"border_color": ACCENT},
    )


def _content_impresoras() -> rx.Component:
    return rx.vstack(
        rx.box(
            rx.vstack(
                _section_header("Impresión de tickets", "printer"),
                rx.text(
                    "Los tickets (comanda de cocina y comprobante de caja) se "
                    "imprimen desde el navegador de la tablet o PC donde estés "
                    "trabajando — se abre el diálogo de impresión del sistema "
                    "y usa la impresora ya instalada ahí, sea por USB o por red. "
                    "No hace falta configurar una IP.",
                    font_size="12px", color=TEXT_MUTED,
                ),
                rx.text("Ancho de papel", font_size="13px", color="#CBD5E1",
                        font_weight="600"),
                rx.hstack(
                    _paper_width_option("58mm", "58"),
                    _paper_width_option("80mm", "80"),
                    spacing="3",
                ),
                spacing="3", width="100%",
            ),
            background=DARK_800, border=f"1px solid {DARK_700}",
            border_radius="12px", padding="20px",
            width="100%", box_shadow="0 1px 3px rgba(0,0,0,0.06)",
        ),
        rx.box(
            rx.hstack(
                rx.icon(tag="info", size=14, color="#60A5FA"),
                rx.text(
                    "Para que la impresora quede configurada, instalala como "
                    "impresora normal en el sistema operativo de esa tablet/PC "
                    "(con el driver del fabricante si es USB) — el navegador se "
                    "encarga del resto.",
                    font_size="12px", color="#CBD5E1",
                ),
                spacing="2", align="start",
            ),
            background="rgba(59,130,246,0.08)", border="1px solid #BFDBFE",
            border_radius="8px", padding="12px 14px", width="100%",
        ),
        rx.box(
            rx.vstack(
                _section_header("Pantalla de cocina (KDS)", "chef_hat"),
                rx.hstack(
                    rx.vstack(
                        rx.text("Minutos para alerta de demorado", font_size="13px",
                                color="#CBD5E1", font_weight="600"),
                        rx.text("Un ticket se marca como demorado si supera este tiempo.",
                                font_size="12px", color=TEXT_MUTED),
                        spacing="0", align="start", flex="1",
                    ),
                    rx.input(
                        value=FoodState.config_kds_minutos_alerta,
                        on_change=FoodState.set_config_kds_minutos_alerta,
                        type="number", min="1", max="120",
                        width="80px",
                        background=PAGE_BACKGROUND, border=f"1px solid {DARK_700}",
                        border_radius="7px", font_size="14px", font_weight="700",
                        text_align="center",
                        padding_y="8px",
                        _focus={"border": f"1px solid {ACCENT}"},
                    ),
                    rx.text("min", font_size="13px", color=TEXT_MUTED, font_weight="600"),
                    spacing="3", align="center", width="100%",
                ),
                spacing="3", width="100%",
            ),
            background=DARK_800, border=f"1px solid {DARK_700}",
            border_radius="12px", padding="20px",
            width="100%", box_shadow="0 1px 3px rgba(0,0,0,0.06)",
        ),
        rx.hstack(
            rx.button(
                rx.hstack(
                    rx.icon(tag="printer", size=14, color=ACCENT),
                    rx.text("Imprimir ticket de prueba", font_size="13px",
                            font_weight="700", color=ACCENT),
                    spacing="2", align="center",
                ),
                on_click=FoodState.imprimir_ticket_prueba,
                background="rgba(234,88,12,0.08)", border="1px solid rgba(234,88,12,0.40)",
                border_radius="8px",
                padding_x="16px", padding_y="9px",
                cursor="pointer",
                _hover={"background": "rgba(234,88,12,0.12)", "border_color": ACCENT},
            ),
            rx.spacer(),
            rx.button(
                rx.hstack(
                    rx.icon(tag="save", size=14, color=TEXT_WHITE),
                    rx.text("Guardar configuración", font_size="13px",
                            font_weight="700", color=TEXT_WHITE),
                    spacing="2", align="center",
                ),
                on_click=FoodState.guardar_config_impresora,
                background=ACCENT, border_radius="8px",
                padding_x="16px", padding_y="9px",
                cursor="pointer", _hover={"background": ACCENT_HOVER},
            ),
            width="100%", align="center",
        ),
        width="100%",
        spacing="4",
    )


def _content_cuenta() -> rx.Component:
    return rx.vstack(
        _admin_cuenta_section(),
        width="100%",
        spacing="4",
    )


def _sucursal_row(suc: SucursalView) -> rx.Component:
    return rx.hstack(
        rx.vstack(
            rx.hstack(
                rx.text(suc.nombre, font_size="14px", font_weight="600", color=TEXT_PRIMARY),
                rx.cond(
                    suc.es_principal,
                    rx.badge("Principal", color_scheme="orange", size="1"),
                    rx.fragment(),
                ),
                rx.cond(
                    suc.activa,
                    rx.fragment(),
                    rx.badge("Inactiva", color_scheme="gray", size="1"),
                ),
                spacing="2", align="center",
            ),
            rx.cond(
                suc.direccion != "",
                rx.text(suc.direccion, font_size="12px", color=TEXT_MUTED),
                rx.fragment(),
            ),
            spacing="1", align="start",
        ),
        rx.spacer(),
        rx.button(
            rx.icon(tag="pencil", size=14),
            on_click=FoodState.abrir_form_sucursal(suc.id),
            variant="ghost", size="1", cursor="pointer",
        ),
        width="100%", align="center",
        padding="10px 12px",
        background=DARK_800,
        border=f"1px solid {DARK_700}",
        border_radius="8px",
    )


def _content_sucursales() -> rx.Component:
    return rx.vstack(
        rx.box(
            rx.vstack(
                _section_header("Sucursales", "map_pin"),
                rx.text(
                    "Configura los locales de tu empresa. Los usuarios, mesas, "
                    "pedidos e inventario se filtran por sucursal activa.",
                    font_size="12px", color=TEXT_MUTED,
                ),
                rx.button(
                    rx.icon(tag="plus", size=14),
                    rx.text("Nueva sucursal", font_size="13px"),
                    on_click=FoodState.abrir_form_sucursal(0),
                    background=ACCENT, color=TEXT_WHITE,
                    border_radius="8px", cursor="pointer", size="2",
                    _hover={"background": ACCENT_HOVER},
                ),
                rx.foreach(FoodState.sucursales_empresa, _sucursal_row),
                spacing="3", width="100%",
            ),
            background=DARK_800, border=f"1px solid {DARK_700}",
            border_radius="12px", padding="20px", width="100%",
        ),
        # Modal form
        rx.dialog.root(
            rx.dialog.content(
                rx.dialog.title("Sucursal"),
                rx.vstack(
                    rx.text("Nombre *", font_size="12px", font_weight="600", color="#CBD5E1"),
                    rx.input(
                        value=FoodState.sucursal_admin_form_nombre,
                        on_change=FoodState.on_change_suc_nombre,
                        placeholder="Sede Central",
                    ),
                    rx.text("Dirección", font_size="12px", font_weight="600", color="#CBD5E1"),
                    rx.input(
                        value=FoodState.sucursal_admin_form_direccion,
                        on_change=FoodState.on_change_suc_direccion,
                        placeholder="Av. Principal 123",
                    ),
                    rx.text("Teléfono", font_size="12px", font_weight="600", color="#CBD5E1"),
                    rx.input(
                        value=FoodState.sucursal_admin_form_telefono,
                        on_change=FoodState.on_change_suc_telefono,
                        placeholder="01-2345678",
                    ),
                    rx.hstack(
                        rx.checkbox(
                            "Activa",
                            checked=FoodState.sucursal_admin_form_activa,
                            on_change=lambda _: FoodState.toggle_suc_activa(),
                        ),
                        rx.checkbox(
                            "Principal",
                            checked=FoodState.sucursal_admin_form_es_principal,
                            on_change=lambda _: FoodState.toggle_suc_principal(),
                        ),
                        spacing="4",
                    ),
                    spacing="2", width="100%",
                ),
                rx.hstack(
                    rx.dialog.close(
                        rx.button("Cancelar", variant="outline", size="2",
                                  on_click=FoodState.cerrar_form_sucursal),
                    ),
                    rx.button(
                        "Guardar", size="2",
                        on_click=FoodState.guardar_sucursal,
                        background=ACCENT, color=TEXT_WHITE,
                        _hover={"background": ACCENT_HOVER},
                    ),
                    spacing="3", justify="end", width="100%", margin_top="12px",
                ),
                background=PAGE_BACKGROUND, border=f"1px solid {DARK_800}",
            ),
            open=FoodState.sucursal_admin_form_visible,
            on_open_change=lambda v: rx.cond(v, rx.noop(), FoodState.cerrar_form_sucursal()),
        ),
        width="100%", spacing="4",
    )


def _content_area() -> rx.Component:
    return rx.cond(
        ConfigSeccionState.seccion == "local",
        _content_local(),
        rx.cond(
            ConfigSeccionState.seccion == "carta",
            _content_carta(),
            rx.cond(
                ConfigSeccionState.seccion == "mesas",
                _content_mesas(),
                rx.cond(
                    ConfigSeccionState.seccion == "sucursales",
                    _content_sucursales(),
                    rx.cond(
                        ConfigSeccionState.seccion == "impresoras",
                        _content_impresoras(),
                        _content_cuenta(),
                    ),
                ),
            ),
        ),
    )


# ─── LAYOUT PRINCIPAL ─────────────────────────────────────────────────────────

def _configuracion_content() -> rx.Component:
    return rx.vstack(
        # Header
        rx.hstack(
            rx.vstack(
                rx.text("Configuración", font_size=rx.breakpoints(initial="20px", md="24px"),
                        font_weight="800", color=TEXT_PRIMARY, line_height="1"),
                rx.text("Ajusta el funcionamiento del sistema",
                        font_size="13px", color=TEXT_MUTED),
                spacing="1", align="start",
            ),
            rx.spacer(),
            width="100%", align="center",
        ),
        # Mobile/tablet: tabs horizontales (hidden en desktop via CSS)
        rx.box(
            _config_nav_tabs(),
            display=rx.breakpoints(initial="block", md="none"),
            width="100%",
        ),
        # Cuerpo: sidebar (desktop) + contenido
        rx.flex(
            # Sidebar de sub-módulos — solo visible en desktop
            rx.box(
                _config_left_sidebar(),
                display=rx.breakpoints(initial="none", md="block"),
                flex_shrink="0",
            ),
            # Área de contenido dinámico
            rx.box(
                _content_area(),
                flex="1",
                min_width="0",
            ),
            direction="row",
            gap="16px",
            width="100%",
            align="start",
        ),
        spacing="4",
        width="100%",
    )


@rx.page(route="/configuracion", on_load=FoodState.on_load_configuracion,
         title="TUWAYKIFOOD | Configuración")
def configuracion_page() -> rx.Component:
    return app_shell(_configuracion_content(), page_key="configuracion")
