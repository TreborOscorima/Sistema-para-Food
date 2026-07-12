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
        background="#1E293B",
        border_radius="10px",
        border=f"1px solid {BORDER_COLOR}",
        box_shadow="0 1px 2px rgba(0,0,0,0.04)",
    )


def _perm_toggle(
    label: str,
    hint: str,
    value: rx.Var,
    on_click,
) -> rx.Component:
    return rx.hstack(
        rx.vstack(
            rx.text(label, font_size="12px", font_weight="600", color=TEXT_PRIMARY),
            rx.text(hint, font_size="11px", color=TEXT_MUTED),
            spacing="0",
            align="start",
            flex="1",
        ),
        rx.button(
            rx.hstack(
                rx.icon(tag=rx.cond(value, "check", "x"), size=11),
                rx.text(rx.cond(value, "Sí", "No"), font_size="11px", font_weight="700"),
                spacing="1",
                align="center",
            ),
            on_click=on_click,
            background=rx.cond(value, SUCCESS_BG, SURFACE_MUTED),
            color=rx.cond(value, SUCCESS_TEXT, TEXT_MUTED),
            border=rx.cond(
                value,
                f"1px solid {SUCCESS_BORDER}",
                f"1px solid {BORDER_COLOR}",
            ),
            border_radius="20px",
            padding="4px 12px",
            cursor="pointer",
            flex_shrink="0",
            _hover={"opacity": "0.8"},
        ),
        width="100%",
        align="center",
        padding_y="6px",
    )


def _permisos_section() -> rx.Component:
    return rx.cond(
        FoodState.usuario_form_rol == "Admin",
        rx.hstack(
            rx.icon(tag="shield_check", size=14, color=SUCCESS_TEXT),
            rx.text(
                "Acceso total — sin restricciones",
                font_size="12px",
                font_weight="600",
                color=SUCCESS_TEXT,
            ),
            spacing="2",
            align="center",
            background=SUCCESS_BG,
            border=f"1px solid {SUCCESS_BORDER}",
            border_radius="8px",
            padding="8px 12px",
            width="100%",
        ),
        rx.vstack(
            rx.hstack(
                rx.icon(tag="lock", size=13, color=TEXT_MUTED),
                rx.text(
                    "Permisos adicionales",
                    font_size="11px",
                    font_weight="700",
                    color=TEXT_MUTED,
                    text_transform="uppercase",
                    letter_spacing="0.05em",
                ),
                spacing="2",
                align="center",
            ),
            _perm_toggle(
                "Aplicar descuentos",
                "Puede ingresar descuentos al cobrar",
                FoodState.usuario_form_perm_descuento,
                FoodState.toggle_uf_perm_descuento,
            ),
            _perm_toggle(
                "Ver reportes",
                "Acceso al módulo de reportes",
                FoodState.usuario_form_perm_reportes,
                FoodState.toggle_uf_perm_reportes,
            ),
            _perm_toggle(
                "Abrir/cerrar turno",
                "Puede abrir y cerrar turnos de caja",
                FoodState.usuario_form_perm_turno,
                FoodState.toggle_uf_perm_turno,
            ),
            _perm_toggle(
                "Gestionar inventario",
                "Puede crear insumos, registrar entradas, mermas y ajustes",
                FoodState.usuario_form_perm_inventario,
                FoodState.toggle_uf_perm_inventario,
            ),
            _perm_toggle(
                "Ver costos y márgenes",
                "Acceso a costos de recetas y margen por plato",
                FoodState.usuario_form_perm_costos,
                FoodState.toggle_uf_perm_costos,
            ),
            _perm_toggle(
                "Reimprimir comprobantes",
                "Puede reimprimir tickets de cobro",
                FoodState.usuario_form_perm_reimprimir,
                FoodState.toggle_uf_perm_reimprimir,
            ),
            rx.cond(
                FoodState.usuario_form_rol == "Caja",
                _perm_toggle(
                    "Anular pedidos",
                    "Puede anular pedidos desde Caja",
                    FoodState.usuario_form_perm_anular,
                    FoodState.toggle_uf_perm_anular,
                ),
                rx.fragment(),
            ),
            spacing="0",
            align="start",
            width="100%",
            padding="10px 12px",
            background=SURFACE_MUTED,
            border=f"1px solid {BORDER_COLOR}",
            border_radius="10px",
        ),
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
            background="#1E293B",
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
            background="#1E293B",
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
                    "Nuevo PIN (dejar vacío para no cambiar)",
                    "PIN (4-6 dígitos) *",
                ),
                value=FoodState.usuario_form_pin,
                on_change=FoodState.on_change_uf_pin,
                type="password",
                max_length=6,
                background="#1E293B",
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
                background="#1E293B",
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
        _permisos_section(),
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
                    rx.text("Cocina — KDS y producción", font_size="11px", color=TEXT_MUTED),
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
                rx.dialog.content(
                    _usuario_modal_content(),
                    background="#0F172A", border="1px solid #1E293B",
                ),
                open=FoodState.usuario_form_visible,
                on_open_change=FoodState.set_usuario_form_visible,
            ),
            width="100%", align="center",
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
