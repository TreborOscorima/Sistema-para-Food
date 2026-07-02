"""Pagina de configuracion con sub-modulos navegables."""

from __future__ import annotations

import reflex as rx

from app.components.shared import app_shell
from app.states.food_state import FoodState, MesaAdminView


# ─── Estado local para la sección activa ──────────────────────────────────────

class ConfigSeccionState(rx.State):
    seccion: str = "local"

    def ir_a(self, s: str) -> None:
        self.seccion = s


# ─── Sub-módulos disponibles ──────────────────────────────────────────────────

_SECCIONES = [
    ("local",       "Local",          "store",        "Nombre del restaurante"),
    ("carta",       "Carta digital",  "qr_code",      "Slug URL y código QR"),
    ("mesas",       "Mesas",          "layout_grid",  "Salon y sectores"),
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


def _section_header(title: str, icon: str, emoji: str = "") -> rx.Component:
    return rx.hstack(
        rx.box(
            rx.text(emoji, font_size="15px", line_height="1") if emoji
            else rx.icon(tag=icon, size=16, color="#EA580C"),
            width="32px",
            height="32px",
            border_radius="8px",
            background="#FFF7ED",
            border="1px solid #FED7AA",
            display="flex",
            align_items="center",
            justify_content="center",
        ),
        rx.text(title, font_size="16px", font_weight="700", color="#0F172A"),
        spacing="3",
        align="center",
    )


def _field_row(label: str, value, on_change,
               placeholder: str = "", tipo: str = "text") -> rx.Component:
    return rx.hstack(
        rx.text(label, font_size="13px", color="#334155", font_weight="600",
                min_width="130px"),
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
                                rx.icon(tag="download", size=13, color="#15803D"),
                                rx.text("Descargar QR", font_size="12px", color="#15803D",
                                        font_weight="600"),
                                spacing="1", align="center",
                            ),
                            href=FoodState.config_menu_qr_base64,
                            download="carta-qr.png",
                        ),
                        rx.link(
                            rx.hstack(
                                rx.icon(tag="external_link", size=13, color="#1D4ED8"),
                                rx.text("Abrir", font_size="12px", color="#1D4ED8",
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
                                border_radius="8px", border="1px solid #E2E8F0",
                            ),
                            padding="4px", background="#FFFFFF",
                            border="1px solid #E2E8F0", border_radius="10px",
                        ),
                        rx.vstack(
                            rx.text("URL de la carta:", font_size="11px",
                                    color="#64748B", font_weight="600"),
                            rx.box(
                                rx.text(FoodState.config_menu_url, font_size="11px",
                                        color="#334155", word_break="break-all",
                                        font_family="monospace"),
                                background="#F8FAFC", border="1px solid #E2E8F0",
                                border_radius="6px", padding="8px 10px",
                            ),
                            rx.text("Guarda para regenerar el QR con el slug actual.",
                                    font_size="11px", color="#94A3B8",
                                    font_style="italic"),
                            spacing="2", align="start", flex="1",
                        ),
                        spacing="3", align="start", width="100%",
                    ),
                    width="100%",
                ),
                rx.text("Guarda la configuracion para generar el QR.",
                        font_size="12px", color="#94A3B8", font_style="italic"),
            ),
            spacing="4", width="100%",
        ),
        background="#FFFFFF",
        border="1px solid #E2E8F0",
        border_radius="12px",
        padding="20px",
        width="100%",
        box_shadow="0 1px 3px rgba(0,0,0,0.06)",
    )


def _mesa_row(mesa: MesaAdminView) -> rx.Component:
    return rx.hstack(
        rx.text(f"#{mesa.numero}", font_size="13px", font_weight="700",
                color="#0F172A", min_width="36px"),
        rx.text(mesa.nombre, font_size="12px", color="#64748B", flex="1"),
        rx.text(f"{mesa.capacidad} pers.", font_size="11px", color="#94A3B8",
                min_width="54px"),
        rx.cond(
            mesa.activa,
            rx.badge("Activa", background="#DCFCE7", color="#15803D",
                     border_radius="5px", font_size="10px"),
            rx.badge("Inactiva", background="#FEE2E2", color="#B91C1C",
                     border_radius="5px", font_size="10px"),
        ),
        rx.button("Editar", on_click=FoodState.editar_mesa_config(mesa.id),
                  background="#FFF7ED", color="#EA580C", border="1px solid #FED7AA",
                  border_radius="6px", font_size="10px", cursor="pointer",
                  padding_x="7px", padding_y="3px", _hover={"opacity": "0.85"}),
        rx.button(
            rx.cond(mesa.activa, "Desactivar", "Activar"),
            on_click=FoodState.toggle_mesa_activa_config(mesa.id),
            background=rx.cond(mesa.activa, "#FEF2F2", "#F0FDF4"),
            color=rx.cond(mesa.activa, "#B91C1C", "#15803D"),
            border=rx.cond(mesa.activa, "1px solid #FECACA", "1px solid #BBF7D0"),
            border_radius="6px", font_size="10px", cursor="pointer",
            padding_x="7px", padding_y="3px", _hover={"opacity": "0.85"},
        ),
        rx.alert_dialog.root(
            rx.alert_dialog.trigger(
                rx.button(
                    rx.icon(tag="trash_2", size=12, color="#B91C1C"),
                    background="#FEF2F2", border="1px solid #FECACA",
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
                            background="#F1F5F9", color="#64748B",
                            border="1px solid #E2E8F0", border_radius="8px",
                            font_size="13px", cursor="pointer",
                            padding_x="14px", padding_y="8px",
                        ),
                    ),
                    rx.alert_dialog.action(
                        rx.button(
                            "Eliminar mesa",
                            on_click=FoodState.eliminar_mesa_config(mesa.id),
                            background="#DC2626", color="#FFFFFF",
                            border_radius="8px", font_size="13px",
                            font_weight="700", cursor="pointer",
                            padding_x="14px", padding_y="8px",
                            _hover={"background": "#B91C1C"},
                        ),
                    ),
                    spacing="3", justify="end", width="100%", margin_top="16px",
                ),
            ),
        ),
        width="100%", align="center",
        padding="8px 10px", background="#FFFFFF",
        border_radius="8px", border="1px solid #E2E8F0",
        gap="8px", flex_wrap="wrap",
    )


def _mesas_section() -> rx.Component:
    return rx.box(
        rx.vstack(
            _section_header("Gestion de Mesas", "layout_grid", "🍽️"),
            rx.vstack(
                rx.text(
                    rx.cond(FoodState.mesa_config_form_id > 0,
                            "Editar Mesa", "Nueva Mesa"),
                    font_size="12px", font_weight="700", color="#EA580C",
                ),
                rx.hstack(
                    rx.input(
                        placeholder="N° *",
                        value=FoodState.mesa_config_form_numero,
                        on_change=FoodState.set_mesa_config_form_numero,
                        type="number", min="1", width="70px",
                        background="#FFFFFF", border="1px solid #E2E8F0",
                        color="#0F172A", border_radius="8px",
                        padding_x="10px", padding_y="8px", font_size="13px",
                    ),
                    rx.input(
                        placeholder="Nombre (ej: Terraza 1)",
                        value=FoodState.mesa_config_form_nombre,
                        on_change=FoodState.set_mesa_config_form_nombre,
                        flex="1", background="#FFFFFF", border="1px solid #E2E8F0",
                        color="#0F172A", border_radius="8px",
                        padding_x="10px", padding_y="8px", font_size="13px",
                    ),
                    rx.input(
                        placeholder="Cap.",
                        value=FoodState.mesa_config_form_capacidad,
                        on_change=FoodState.set_mesa_config_form_capacidad,
                        type="number", min="1", width="62px",
                        background="#FFFFFF", border="1px solid #E2E8F0",
                        color="#0F172A", border_radius="8px",
                        padding_x="10px", padding_y="8px", font_size="13px",
                    ),
                    spacing="2", width="100%",
                ),
                rx.hstack(
                    rx.button(
                        "Cancelar",
                        on_click=FoodState.cancelar_mesa_config_form,
                        background="#F1F5F9", color="#64748B",
                        border="1px solid #E2E8F0", border_radius="7px",
                        font_size="12px", cursor="pointer",
                        _hover={"opacity": "0.85"},
                    ),
                    rx.button(
                        rx.cond(FoodState.mesa_config_form_id > 0,
                                "Actualizar Mesa", "Agregar Mesa"),
                        on_click=FoodState.guardar_mesa_config,
                        background="#EA580C", color="#FFFFFF",
                        border_radius="7px", font_size="12px",
                        font_weight="700", cursor="pointer", flex="1",
                        _hover={"background": "#C2410C"},
                    ),
                    spacing="2", width="100%",
                ),
                spacing="2", padding="12px",
                background="#FFF7ED", border="1px solid #FED7AA",
                border_radius="10px", width="100%",
            ),
            rx.cond(
                FoodState.mesas_config.length() == 0,
                rx.center(
                    rx.text("Sin mesas configuradas.", font_size="12px",
                            color="#94A3B8", font_style="italic"),
                    padding_y="12px", width="100%",
                ),
                rx.vstack(
                    rx.foreach(FoodState.mesas_config, _mesa_row),
                    spacing="2", width="100%",
                ),
            ),
            spacing="3", width="100%",
        ),
        background="#FFFFFF",
        border="1px solid #E2E8F0",
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
                font_size="12px", color="#64748B", font_style="italic",
            ),
            _field_row("Email", FoodState.config_admin_email,
                       FoodState.set_config_admin_email,
                       "dueño@restaurante.com", "email"),
            rx.hstack(
                rx.text("Nueva clave", font_size="13px", color="#334155",
                        min_width="130px", font_weight="600"),
                rx.box(
                    rx.input(
                        placeholder="Nueva contraseña",
                        value=FoodState.config_admin_password_nueva,
                        on_change=FoodState.set_config_admin_password_nueva,
                        type=rx.cond(FoodState.config_admin_show_password, "text", "password"),
                        background="#FFFFFF", border="1px solid #E2E8F0",
                        color="#0F172A", border_radius="8px",
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
                        background="transparent", color="#64748B", border="none",
                        width="26px", height="26px",
                        _hover={"background": "#F1F5F9"},
                        position="absolute", right="6px", top="50%",
                        transform="translateY(-50%)", cursor="pointer",
                    ),
                    position="relative", flex="1",
                ),
                spacing="3", align="center", width="100%",
                class_name="twk-field-row",
            ),
            rx.hstack(
                rx.text("Confirmar clave", font_size="13px", color="#334155",
                        min_width="130px", font_weight="600"),
                rx.box(
                    rx.input(
                        placeholder="Repite la contraseña",
                        value=FoodState.config_admin_password_confirm,
                        on_change=FoodState.set_config_admin_password_confirm,
                        type=rx.cond(FoodState.config_admin_show_password, "text", "password"),
                        background="#FFFFFF", border="1px solid #E2E8F0",
                        color="#0F172A", border_radius="8px",
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
                        background="transparent", color="#64748B", border="none",
                        width="26px", height="26px",
                        _hover={"background": "#F1F5F9"},
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
                    rx.icon(tag="key_round", size=14, color="#FFFFFF"),
                    rx.text("Guardar cuenta del dueño", font_size="13px",
                            font_weight="700", color="#FFFFFF"),
                    spacing="2", align="center",
                ),
                on_click=FoodState.guardar_admin_cuenta,
                background="#0F172A", border_radius="8px",
                padding_x="16px", padding_y="8px", cursor="pointer",
                _hover={"background": "#1E293B"},
                align_self="end",
            ),
            spacing="3", width="100%",
        ),
        background="#FFFFFF",
        border="1px solid #E2E8F0",
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
                    color=rx.cond(active, "#EA580C", "#64748B"),
                ),
                width="34px",
                height="34px",
                border_radius="9px",
                background=rx.cond(active, "#FFF7ED", "#F8FAFC"),
                border=rx.cond(active, "1px solid #FED7AA", "1px solid #F1F5F9"),
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
                    color=rx.cond(active, "#0F172A", "#334155"),
                    line_height="1",
                ),
                rx.text(
                    desc,
                    font_size="11px",
                    color=rx.cond(active, "#64748B", "#94A3B8"),
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
        background=rx.cond(active, "#FFFFFF", "transparent"),
        border=rx.cond(active, "1px solid #FED7AA", "1px solid transparent"),
        box_shadow=rx.cond(active, "0 1px 4px rgba(234,88,12,0.1)", "none"),
        cursor="pointer",
        on_click=ConfigSeccionState.ir_a(key),
        width="100%",
        transition="all 0.12s ease",
        _hover={
            "background": rx.cond(active, "#FFFFFF", "#F8FAFC"),
            "border": rx.cond(active, "1px solid #FED7AA", "1px solid #F1F5F9"),
        },
    )


def _config_left_sidebar() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.text(
                "Ajustes",
                font_size="10px",
                font_weight="700",
                color="#94A3B8",
                text_transform="uppercase",
                letter_spacing="0.08em",
                padding_x="4px",
                padding_bottom="4px",
            ),
            _seccion_item("local",      "Local",         "store",       "Nombre del restaurante"),
            _seccion_item("carta",      "Carta digital", "qr_code",     "Slug URL y código QR"),
            _seccion_item("mesas",      "Mesas",         "layout_grid", "Salon y sectores"),
            _seccion_item("impresoras", "Impresoras",    "printer",     "Cocina y caja"),
            _seccion_item("cuenta",     "Cuenta Admin",  "key_round",   "Email y contraseña"),
            spacing="1",
            width="100%",
            align="start",
        ),
        padding="12px",
        background="#F8FAFC",
        border="1px solid #E2E8F0",
        border_radius="14px",
        min_width=rx.breakpoints(initial="100%", md="210px"),
        width=rx.breakpoints(initial="100%", md="210px"),
        flex_shrink="0",
    )


# ─── CONTENIDO POR SECCIÓN ────────────────────────────────────────────────────

def _resumen_widget(icon: str, label: str, value, href: str) -> rx.Component:
    return rx.link(
        rx.vstack(
            rx.hstack(
                rx.icon(tag=icon, size=15, color="#EA580C"),
                rx.text(label, font_size="12px", font_weight="700", color="#0F172A"),
                spacing="2", align="center",
            ),
            rx.text(value, font_size="24px", font_weight="800", color="#0F172A"),
            rx.hstack(
                rx.text("Gestionar", font_size="11px", font_weight="600", color="#EA580C"),
                rx.icon(tag="arrow_right", size=11, color="#EA580C"),
                spacing="1", align="center",
            ),
            spacing="1", align="start", width="100%",
        ),
        on_click=lambda: ConfigSeccionState.ir_a(href),
        background="#FFFFFF", border="1px solid #E2E8F0",
        border_radius="12px", padding="16px",
        width="100%", text_decoration="none", cursor="pointer",
        box_shadow="0 1px 3px rgba(0,0,0,0.06)",
        _hover={"border_color": "#FED7AA", "background": "#FFF7ED"},
        transition="all 0.15s ease",
    )


def _content_local() -> rx.Component:
    return rx.grid(
        rx.box(
            rx.vstack(
                _section_header("Nombre del restaurante", "store", "🏪"),
                rx.text("Este nombre aparece en la carta digital y en los tickets.",
                        font_size="12px", color="#64748B"),
                _field_row("Nombre", FoodState.config_nombre_local,
                           FoodState.set_config_nombre_local, "Mi Restaurante"),
                rx.vstack(
                    rx.text("Logo de la empresa", font_size="12px", font_weight="600", color="#64748B"),
                    rx.text("Se muestra como tarjeta en la pantalla de inicio de sesión.",
                            font_size="11px", color="#94A3B8"),
                    rx.cond(
                        FoodState.config_logo_url != "",
                        rx.hstack(
                            rx.image(
                                src=FoodState.config_logo_url,
                                width="72px", height="72px",
                                object_fit="cover",
                                border_radius="10px",
                                border="1px solid #E2E8F0",
                            ),
                            rx.vstack(
                                rx.text("Logo cargado", font_size="11px", color="#15803D", font_weight="600"),
                                rx.button(
                                    "Quitar logo",
                                    on_click=FoodState.quitar_logo_empresa,
                                    background="#FEF2F2", color="#B91C1C",
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
                                rx.icon(tag="image_plus", size=20, color="#94A3B8"),
                                rx.text("Arrastra o haz click", font_size="11px", color="#64748B"),
                                rx.text("JPG, PNG, WEBP — max 5MB", font_size="10px", color="#94A3B8"),
                                spacing="1", align="center",
                            ),
                            id="upload_logo_empresa",
                            on_drop=FoodState.handle_upload_logo_empresa(
                                rx.upload_files(upload_id="upload_logo_empresa")
                            ),
                            accept={"image/jpeg": [".jpg", ".jpeg"], "image/png": [".png"], "image/webp": [".webp"]},
                            max_files=1,
                            border="2px dashed #E2E8F0",
                            border_radius="8px",
                            padding="16px",
                            width="100%",
                            background="#FAFAFA",
                            cursor="pointer",
                            _hover={"border_color": "#EA580C", "background": "#FFF7ED"},
                        ),
                    ),
                    spacing="2", width="100%",
                ),
                rx.button(
                    rx.hstack(
                        rx.icon(tag="save", size=14, color="#FFFFFF"),
                        rx.text("Guardar nombre", font_size="13px",
                                font_weight="700", color="#FFFFFF"),
                        spacing="2", align="center",
                    ),
                    on_click=FoodState.guardar_config_impresora,
                    background="#EA580C",
                    border_radius="8px",
                    padding_x="16px",
                    padding_y="9px",
                    cursor="pointer",
                    _hover={"background": "#C2410C"},
                    align_self="end",
                ),
                spacing="4", width="100%",
            ),
            background="#FFFFFF", border="1px solid #E2E8F0",
            border_radius="12px", padding="20px",
            width="100%", box_shadow="0 1px 3px rgba(0,0,0,0.06)",
        ),
        rx.vstack(
            _resumen_widget("layout_grid", "Mesas y salones",
                             FoodState.mesas.length(), "mesas"),
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
                rx.icon(tag="save", size=14, color="#FFFFFF"),
                rx.text("Guardar y regenerar QR", font_size="13px",
                        font_weight="700", color="#FFFFFF"),
                spacing="2", align="center",
            ),
            on_click=FoodState.guardar_config_impresora,
            background="#EA580C", border_radius="8px",
            padding_x="16px", padding_y="9px",
            cursor="pointer", _hover={"background": "#C2410C"},
            align_self="end",
        ),
        width="100%",
        spacing="4",
    )


def _content_mesas() -> rx.Component:
    return rx.vstack(
        _mesas_section(),
        width="100%",
        spacing="4",
    )


def _paper_width_option(label: str, value: str) -> rx.Component:
    seleccionado = FoodState.config_ticket_paper_width_mm == value
    return rx.box(
        rx.text(label, font_size="13px", font_weight="700"),
        on_click=FoodState.set_config_ticket_paper_width_mm(value),
        background=rx.cond(seleccionado, "#EA580C", "#FFFFFF"),
        color=rx.cond(seleccionado, "#FFFFFF", "#334155"),
        border=rx.cond(seleccionado, "1px solid #EA580C", "1px solid #E2E8F0"),
        border_radius="8px", padding="10px 20px", cursor="pointer",
        _hover={"border_color": "#EA580C"},
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
                    font_size="12px", color="#64748B",
                ),
                rx.text("Ancho de papel", font_size="13px", color="#334155",
                        font_weight="600"),
                rx.hstack(
                    _paper_width_option("58mm", "58"),
                    _paper_width_option("80mm", "80"),
                    spacing="3",
                ),
                spacing="3", width="100%",
            ),
            background="#FFFFFF", border="1px solid #E2E8F0",
            border_radius="12px", padding="20px",
            width="100%", box_shadow="0 1px 3px rgba(0,0,0,0.06)",
        ),
        rx.box(
            rx.hstack(
                rx.icon(tag="info", size=14, color="#1D4ED8"),
                rx.text(
                    "Para que la impresora quede configurada, instalala como "
                    "impresora normal en el sistema operativo de esa tablet/PC "
                    "(con el driver del fabricante si es USB) — el navegador se "
                    "encarga del resto.",
                    font_size="12px", color="#334155",
                ),
                spacing="2", align="start",
            ),
            background="#EFF6FF", border="1px solid #BFDBFE",
            border_radius="8px", padding="12px 14px", width="100%",
        ),
        rx.button(
            rx.hstack(
                rx.icon(tag="save", size=14, color="#FFFFFF"),
                rx.text("Guardar impresoras", font_size="13px",
                        font_weight="700", color="#FFFFFF"),
                spacing="2", align="center",
            ),
            on_click=FoodState.guardar_config_impresora,
            background="#EA580C", border_radius="8px",
            padding_x="16px", padding_y="9px",
            cursor="pointer", _hover={"background": "#C2410C"},
            align_self="end",
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
                    ConfigSeccionState.seccion == "impresoras",
                    _content_impresoras(),
                    _content_cuenta(),
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
                rx.text("Configuracion", font_size=rx.breakpoints(initial="20px", md="24px"),
                        font_weight="800", color="#0F172A", line_height="1"),
                rx.text("Ajusta el funcionamiento del sistema",
                        font_size="13px", color="#64748B"),
                spacing="1", align="start",
            ),
            rx.spacer(),
            width="100%", align="center",
        ),
        # Mensaje global
        rx.cond(
            FoodState.mensaje != "",
            rx.hstack(
                rx.icon(tag="circle_check", size=14, color="#15803D"),
                rx.text(FoodState.mensaje, font_size="13px", color="#15803D",
                        font_weight="600"),
                spacing="2", align="center",
                background="#F0FDF4", border="1px solid #BBF7D0",
                border_radius="8px", padding="10px 14px", width="100%",
            ),
            rx.fragment(),
        ),
        # Cuerpo: sidebar + contenido
        rx.flex(
            # Sidebar de sub-módulos
            _config_left_sidebar(),
            # Área de contenido dinámico
            rx.box(
                _content_area(),
                flex="1",
                min_width="0",
            ),
            direction=rx.breakpoints(initial="column", md="row"),
            gap="16px",
            width="100%",
            align="start",
        ),
        spacing="5",
        width="100%",
    )


@rx.page(route="/configuracion", on_load=FoodState.on_load_configuracion,
         title="TUWAYKIFOOD | Configuración")
def configuracion_page() -> rx.Component:
    return app_shell(_configuracion_content(), page_key="configuracion")
