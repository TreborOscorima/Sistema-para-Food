"""Pagina admin — gestión de usuarios y PINs del local."""

from __future__ import annotations

import reflex as rx

from app.components.shared import (
    ACCENT,
    ACCENT_BG,
    ACCENT_HOVER,
    BORDER_ACCENT,
    BORDER_COLOR,
    BORDER_STRONG,
    DANGER_BG,
    DANGER_BORDER,
    DANGER_TEXT,
    INFO_BG,
    INFO_BORDER,
    INFO_TEXT,
    SUCCESS_BG,
    SUCCESS_BORDER,
    SUCCESS_TEXT,
    SURFACE_MUTED,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    WARNING_BG,
    WARNING_BORDER,
    WARNING_TEXT,
    app_shell,
    section_card,
    surface_card,
)
from app.states.food_state import FoodState, UsuarioAdminView


_USR_GRID_COLS = "2fr 1fr 1fr 90px"


def _usuarios_table_header() -> rx.Component:
    return rx.grid(
        rx.text("Usuario", font_size="11px", font_weight="600", color=TEXT_MUTED,
                text_transform="uppercase", letter_spacing="0.05em"),
        rx.text("Rol", font_size="11px", font_weight="600", color=TEXT_MUTED,
                text_transform="uppercase", letter_spacing="0.05em"),
        rx.text("Estado", font_size="11px", font_weight="600", color=TEXT_MUTED,
                text_transform="uppercase", letter_spacing="0.05em"),
        rx.text("", font_size="11px"),
        columns=_USR_GRID_COLS,
        gap="8px", width="100%",
        padding="0 14px 8px", border_bottom=f"1px solid {BORDER_COLOR}",
        display=rx.breakpoints(initial="none", md="grid"),
    )


def _usuario_row(u: UsuarioAdminView) -> rx.Component:
    return rx.grid(
        rx.hstack(
            rx.box(
                rx.text(u.nombre[:1].upper(), font_size="14px", font_weight="800",
                        color="#FFFFFF"),
                width="36px", height="36px", border_radius="full",
                background=u.badge_text, display="flex",
                align_items="center", justify_content="center", flex_shrink="0",
            ),
            rx.vstack(
                rx.hstack(
                    rx.text(u.nombre, font_size="13px", font_weight="700", color=TEXT_PRIMARY),
                    rx.cond(
                        u.es_yo,
                        rx.badge("Tú", background="#F3E8FF", color="#7C3AED",
                                 border_radius="5px", font_size="9px"),
                        rx.fragment(),
                    ),
                    spacing="1", align="center",
                ),
                rx.text(u.pin_masked, font_size="11px", color=TEXT_MUTED,
                        letter_spacing="0.06em"),
                spacing="0", align="start",
            ),
            spacing="2", align="center", min_width="0",
        ),
        rx.badge(
            u.rol_label, background=u.badge_bg, color=u.badge_text,
            border_radius="20px", font_size="11px", font_weight="700",
            padding="3px 10px", width="fit-content",
        ),
        rx.cond(
            u.activo,
            rx.badge("Activo", background=SUCCESS_BG, color=SUCCESS_TEXT,
                     border_radius="20px", font_size="11px", font_weight="700",
                     padding="3px 10px", width="fit-content"),
            rx.badge("Inactivo", background=DANGER_BG, color=DANGER_TEXT,
                     border_radius="20px", font_size="11px", font_weight="700",
                     padding="3px 10px", width="fit-content"),
        ),
        rx.hstack(
            rx.link(
                "✏️ Editar",
                on_click=FoodState.editar_usuario(u.id),
                font_size="12px", font_weight="600", color=ACCENT,
                cursor="pointer", _hover={"color": ACCENT_HOVER},
            ),
            rx.cond(
                u.es_yo,
                rx.fragment(),
                rx.button(
                    rx.cond(
                        u.activo,
                        rx.icon(tag="toggle_right", size=14),
                        rx.icon(tag="toggle_left", size=14),
                    ),
                    on_click=FoodState.toggle_usuario_activo(u.id),
                    background="transparent",
                    color=rx.cond(u.activo, SUCCESS_TEXT, TEXT_MUTED),
                    border="none", padding="0", cursor="pointer",
                    _hover={"opacity": "0.7"},
                ),
            ),
            spacing="2", align="center",
        ),
        columns=rx.breakpoints(initial="1fr auto", md=_USR_GRID_COLS),
        gap="8px", width="100%", align_items="center",
        padding="12px 14px",
        background="#FFFFFF",
        border_radius="10px",
        border=f"1px solid {BORDER_COLOR}",
        box_shadow="0 1px 2px rgba(0,0,0,0.04)",
    )


def _usuario_form() -> rx.Component:
    return rx.vstack(
        rx.text(
            rx.cond(FoodState.usuario_form_es_edicion, "Editar usuario", "Nuevo usuario"),
            font_size="14px",
            font_weight="700",
            color=ACCENT,
        ),
        rx.input(
            placeholder="Nombre completo *",
            value=FoodState.usuario_form_nombre,
            on_change=FoodState.on_change_uf_nombre,
            background="#FFFFFF",
            border=f"1px solid {BORDER_COLOR}",
            color=TEXT_PRIMARY,
            border_radius="8px",
            padding_x="12px",
            padding_y="8px",
            font_size="13px",
            width="100%",
        ),
        rx.select(
            FoodState.roles_disponibles,
            value=FoodState.usuario_form_rol,
            on_change=FoodState.on_change_uf_rol,
            background="#FFFFFF",
            color=TEXT_PRIMARY,
            border=f"1px solid {BORDER_COLOR}",
            border_radius="8px",
            padding_x="12px",
            padding_y="8px",
            font_size="13px",
            width="100%",
        ),
        rx.hstack(
            rx.input(
                placeholder=rx.cond(
                    FoodState.usuario_form_es_edicion,
                    "Nuevo PIN (dejar vacio para no cambiar)",
                    "PIN (4-6 digitos) *",
                ),
                value=FoodState.usuario_form_pin,
                on_change=FoodState.on_change_uf_pin,
                type="password",
                max_length=6,
                background="#FFFFFF",
                border=f"1px solid {BORDER_COLOR}",
                color=TEXT_PRIMARY,
                border_radius="8px",
                padding_x="12px",
                padding_y="8px",
                font_size="13px",
                flex="1",
            ),
            rx.input(
                placeholder="Confirmar PIN",
                value=FoodState.usuario_form_pin_confirm,
                on_change=FoodState.on_change_uf_pin_confirm,
                type="password",
                max_length=6,
                background="#FFFFFF",
                border=f"1px solid {BORDER_COLOR}",
                color=TEXT_PRIMARY,
                border_radius="8px",
                padding_x="12px",
                padding_y="8px",
                font_size="13px",
                flex="1",
            ),
            spacing="2",
            width="100%",
        ),
        rx.cond(
            FoodState.usuario_form_es_edicion,
            rx.hstack(
                rx.button(
                    rx.cond(
                        FoodState.usuario_form_activo,
                        "Estado: Activo",
                        "Estado: Inactivo",
                    ),
                    on_click=FoodState.toggle_uf_activo,
                    background=rx.cond(
                        FoodState.usuario_form_activo,
                        SUCCESS_BG,
                        DANGER_BG,
                    ),
                    color=rx.cond(
                        FoodState.usuario_form_activo,
                        SUCCESS_TEXT,
                        DANGER_TEXT,
                    ),
                    border=rx.cond(
                        FoodState.usuario_form_activo,
                        f"1px solid {SUCCESS_BORDER}",
                        f"1px solid {DANGER_BORDER}",
                    ),
                    border_radius="8px",
                    font_size="12px",
                    cursor="pointer",
                    _hover={"opacity": "0.85"},
                ),
                rx.spacer(),
                rx.fragment(),
                spacing="2",
                width="100%",
            ),
            rx.fragment(),
        ),
        rx.hstack(
            rx.button(
                "Cancelar",
                on_click=FoodState.cancelar_usuario_form,
                background=SURFACE_MUTED,
                color=TEXT_SECONDARY,
                border=f"1px solid {BORDER_COLOR}",
                border_radius="8px",
                font_size="13px",
                cursor="pointer",
                _hover={"opacity": "0.85"},
            ),
            rx.button(
                rx.cond(FoodState.usuario_form_es_edicion, "Guardar cambios", "Crear usuario"),
                on_click=FoodState.guardar_usuario,
                background=ACCENT,
                color="#FFFFFF",
                border_radius="8px",
                font_size="13px",
                font_weight="700",
                cursor="pointer",
                flex="1",
                _hover={"background": ACCENT_HOVER},
            ),
            spacing="2",
            width="100%",
        ),
        spacing="3",
        padding="16px",
        background=ACCENT_BG,
        border=f"1px solid {BORDER_ACCENT}",
        border_radius="12px",
        width="100%",
    )


def _usuario_modal_content() -> rx.Component:
    return rx.vstack(
        _usuario_form(),
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.icon(tag="info", size=14, color=INFO_TEXT),
                    rx.text("Roles disponibles", font_size="12px", font_weight="700", color=INFO_TEXT),
                    spacing="2",
                    align="center",
                ),
                rx.vstack(
                    rx.text("Admin — acceso completo al sistema", font_size="11px", color=TEXT_MUTED),
                    rx.text("Mozo — mesas y pedidos", font_size="11px", color=TEXT_MUTED),
                    rx.text("Caja — cobros y mostrador", font_size="11px", color=TEXT_MUTED),
                    rx.text("Cocina — KDS y produccion", font_size="11px", color=TEXT_MUTED),
                    spacing="1",
                    align="start",
                ),
                align="start",
                spacing="2",
                width="100%",
            ),
            padding="12px 14px",
            background=INFO_BG,
            border=f"1px solid {INFO_BORDER}",
            border_radius="10px",
            width="100%",
            margin_top="12px",
        ),
        width="100%",
    )


def _usuarios_content() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.vstack(
                rx.text("Usuarios del sistema", font_size="22px", font_weight="800", color=TEXT_PRIMARY),
                rx.text("Empleados y roles", font_size="13px", color=TEXT_MUTED),
                spacing="0", align="start",
            ),
            rx.spacer(),
            rx.dialog.root(
                rx.button(
                    rx.hstack(
                        rx.icon(tag="user_plus", size=14),
                        rx.text("Nuevo usuario", font_size="13px", font_weight="700"),
                        spacing="1", align="center",
                    ),
                    on_click=FoodState.nuevo_usuario_form,
                    background=ACCENT, color="#FFFFFF", border_radius="9px",
                    padding_x="16px", padding_y="9px", cursor="pointer",
                    _hover={"background": ACCENT_HOVER},
                ),
                rx.dialog.content(_usuario_modal_content(), class_name="light"),
                open=FoodState.usuario_form_visible,
                on_open_change=FoodState.set_usuario_form_visible,
            ),
            width="100%", align="center",
        ),
        rx.cond(
            FoodState.mensaje != "",
            rx.box(
                rx.text(FoodState.mensaje, font_size="12px", color=TEXT_SECONDARY),
                background=SURFACE_MUTED,
                border=f"1px solid {BORDER_COLOR}",
                border_radius="6px",
                padding="8px 12px",
                width="100%",
            ),
            rx.fragment(),
        ),
        _usuarios_table_header(),
        rx.cond(
            FoodState.usuarios_admin.length() == 0,
            rx.box(
                rx.text(
                    "No hay usuarios registrados.",
                    font_size="13px",
                    color=TEXT_MUTED,
                ),
                padding="16px",
                background=SURFACE_MUTED,
                border_radius="8px",
                border=f"1px solid {BORDER_COLOR}",
                width="100%",
            ),
            rx.vstack(
                rx.foreach(FoodState.usuarios_admin, _usuario_row),
                spacing="2",
                width="100%",
            ),
        ),
        spacing="4",
        width="100%",
    )


@rx.page(route="/usuarios", on_load=FoodState.on_load_usuarios, title="TUWAYKIFOOD | Usuarios")
def usuarios_page() -> rx.Component:
    return app_shell(_usuarios_content(), page_key="usuarios")
