"""Pagina de configuracion con sub-modulos navegables."""

from __future__ import annotations

import reflex as rx

from app.components.shared import (
    WARNING_TEXT, SUCCESS_TEXT,
    app_shell,
    ACCENT, ACCENT_HOVER,
    DANGER_SOLID,
    DARK_600, DARK_700, DARK_800,
    PAGE_BACKGROUND, SURFACE_BASE,
    SUCCESS_SOLID,
    TEXT_MUTED, TEXT_PRIMARY, TEXT_WHITE,
    WARNING_SOLID,
    switch_toggle,
)
from app.states.food_state import (
    FoodState,
    MesaAdminView,
    SucursalView,
    ImpresoraView,
    AgenteView,
)
from app.states.metodos_pago_mixin import MetodoPagoAdminView, TIPOS_METODO

# País de operación (código ISO-2 → nombre). Define la zona horaria con la que
# se agrupan los reportes por día local. Debe ser subconjunto de los países
# soportados por tuwayki_core.
_PAISES = [
    ("PE", "🇵🇪 Perú"),
    ("AR", "🇦🇷 Argentina"),
    ("CL", "🇨🇱 Chile"),
    ("CO", "🇨🇴 Colombia"),
    ("EC", "🇪🇨 Ecuador"),
    ("MX", "🇲🇽 México"),
    ("BO", "🇧🇴 Bolivia"),
    ("UY", "🇺🇾 Uruguay"),
    ("PY", "🇵🇾 Paraguay"),
    ("VE", "🇻🇪 Venezuela"),
]


# URL de descarga del agente (GitHub Release, repo público). "latest" apunta
# siempre a la última versión publicada del agente.
AGENTE_DOWNLOAD_URL = (
    "https://github.com/TreborOscorima/Sistema-para-Food/"
    "releases/latest/download/TuwaykifoodAgente.exe"
)


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
    ("metodos",     "Métodos de pago", "wallet",      "Efectivo, Yape, Plin…"),
    ("impresoras",  "Impresoras",     "printer",      "Cocina y caja"),
    ("cuenta",      "Cuenta Admin",   "key_round",    "Email y contraseña"),
]


# ─── COMPONENTES INTERNOS (también exportados para dono.py) ───────────────────

def _toggle_btn(activo: bool, on_click) -> rx.Component:
    """Switch estilo iOS (mismo look que ``styled_switch``).

    Mantiene la firma ``(activo, on_click)`` para no tocar los llamadores:
    el ``on_click`` ya viene armado (toggle o setter con valor).
    """
    return rx.box(
        rx.box(
            position="absolute", top="2px", left="2px",
            width="20px", height="20px", border_radius="9999px",
            background="#FFFFFF", box_shadow="0 1px 3px rgba(0,0,0,0.45)",
            transform=rx.cond(activo, "translateX(18px)", "translateX(0)"),
            transition="transform 0.22s cubic-bezier(0.4,0,0.2,1)",
        ),
        on_click=on_click,
        position="relative", width="42px", height="24px", border_radius="9999px",
        background=rx.cond(activo, ACCENT, DARK_600),
        border=rx.cond(activo, f"1px solid {ACCENT}", f"1px solid {DARK_700}"),
        cursor="pointer", flex_shrink="0",
        transition="background 0.22s ease, border-color 0.22s ease",
        _hover={"opacity": "0.88"},
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
        rx.text(label, font_size="13px", color="var(--twk-slate-300)", font_weight="600",
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
                                rx.icon(tag="download", size=13, color=SUCCESS_TEXT),
                                rx.text("Descargar QR", font_size="12px", color=SUCCESS_TEXT,
                                        font_weight="600"),
                                spacing="1", align="center",
                            ),
                            href=FoodState.config_menu_qr_base64,
                            download="carta-qr.png",
                        ),
                        rx.link(
                            rx.hstack(
                                rx.icon(tag="external_link", size=13, color="var(--twk-info-text)"),
                                rx.text("Abrir", font_size="12px", color="var(--twk-info-text)",
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
            rx.text(
                "El slug es el final de la dirección de tu carta "
                "(tuwayki.app/menu/tu-nombre). Imprime el QR y pégalo en las mesas.",
                font_size="11px", color=TEXT_MUTED, margin_top="-4px",
            ),
            rx.hstack(
                rx.icon(tag="triangle_alert", size=13, color="#F59E0B"),
                rx.text(
                    "Si cambias el slug, los QR ya impresos dejarán de funcionar.",
                    font_size="11px", color="var(--twk-warning-text)", font_weight="600",
                ),
                spacing="2", align="center",
            ),
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
                                        color="var(--twk-slate-300)", word_break="break-all",
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
                    rx.icon(tag="download", size=11, color=SUCCESS_TEXT),
                    rx.text("Descargar", font_size="10px", color=SUCCESS_TEXT,
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
            rx.badge("QR", background="rgba(124,58,237,0.12)", color="var(--twk-purple-text)",
                     border="1px solid rgba(124,58,237,0.20)", border_radius="4px",
                     font_size="10px", padding="1px 6px"),
            rx.fragment(),
        ),
        rx.text(f"{mesa.capacidad} pers.", font_size="11px", color=TEXT_MUTED,
                min_width="54px"),
        rx.cond(
            mesa.activa,
            rx.badge("Activa", background="rgba(34,197,94,0.12)", color=SUCCESS_TEXT,
                     border_radius="5px", font_size="10px"),
            rx.badge("Inactiva", background="rgba(239,68,68,0.12)", color="var(--twk-danger-text)",
                     border_radius="5px", font_size="10px"),
        ),
        rx.tooltip(
            rx.button(
                rx.icon(tag="pencil", size=13),
                on_click=FoodState.editar_mesa_config(mesa.id),
                background="rgba(234,88,12,0.08)", color=ACCENT, border="1px solid rgba(234,88,12,0.40)",
                border_radius="6px", cursor="pointer",
                padding="5px", min_width="0", height="auto", _hover={"opacity": "0.85"},
            ),
            content="Editar mesa",
        ),
        rx.tooltip(
            switch_toggle(mesa.activa, FoodState.toggle_mesa_activa_config(mesa.id)),
            content=rx.cond(mesa.activa, "Desactivar mesa", "Activar mesa"),
        ),
        rx.alert_dialog.root(
            rx.alert_dialog.trigger(
                rx.tooltip(
                    rx.button(
                        rx.icon(tag="trash_2", size=12, color="var(--twk-danger-text)"),
                        background="rgba(239,68,68,0.08)", border="1px solid #FECACA",
                        border_radius="6px", cursor="pointer",
                        padding_x="7px", padding_y="3px", _hover={"opacity": "0.85"},
                    ),
                    content="Eliminar mesa",
                ),
            ),
            rx.alert_dialog.content(
                rx.alert_dialog.title("¿Eliminar mesa?"),
                rx.alert_dialog.description(
                    "Se eliminará \"" + mesa.nombre + "\" permanentemente. "
                    "Esta acción no se puede deshacer. Si preferís conservarla "
                    "pero dejarla fuera de uso, usa \"Desactivar\" en su lugar.",
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
                            _hover={"background": "var(--twk-danger-text)"},
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
                rx.text("Imprime cada QR y pégalo en la mesa correspondiente.",
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
            rx.text(
                "Cada mesa que agregues aparece en el salón de los mozos. "
                "Usa sectores (Terraza, Barra) para agruparlas.",
                font_size="12px", color=TEXT_MUTED,
            ),
            # Formulario compacto
            rx.hstack(
                rx.input(
                    placeholder="N°",
                    value=FoodState.mesa_config_form_numero,
                    on_change=FoodState.set_mesa_config_form_numero,
                    type="number", min="1", width="60px",
                    background=SURFACE_BASE, border=f"1px solid {DARK_700}",
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
                    background=SURFACE_BASE, border=f"1px solid {DARK_700}",
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
                    background=SURFACE_BASE, border=f"1px solid {DARK_700}",
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
                    background=SURFACE_BASE, border=f"1px solid {DARK_700}",
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
                        background=SURFACE_BASE, border=f"1px solid {DARK_700}",
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
                        rx.icon(tag="layout_grid", size=28, color="var(--twk-slate-300)"),
                        rx.text("Sin mesas configuradas", font_size="13px",
                                color=TEXT_MUTED),
                        rx.text("Agrega mesas usando el formulario de arriba.",
                                font_size="11px", color="var(--twk-slate-300)"),
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
                "Esta cuenta (email + contraseña) es la del dueño y entra al Panel "
                "Administrativo. El personal, en cambio, entra con su PIN desde la "
                "pantalla de inicio.",
                font_size="12px", color=TEXT_MUTED, font_style="italic",
            ),
            _field_row("Email", FoodState.config_admin_email,
                       FoodState.set_config_admin_email,
                       "dueño@restaurante.com", "email"),
            rx.hstack(
                rx.text("Nueva clave", font_size="13px", color="var(--twk-slate-300)",
                        min_width="130px", font_weight="600"),
                rx.box(
                    rx.input(
                        placeholder="Nueva contraseña",
                        value=FoodState.config_admin_password_nueva,
                        on_change=FoodState.set_config_admin_password_nueva,
                        type=rx.cond(FoodState.config_admin_show_password, "text", "password"),
                        background=SURFACE_BASE, border=f"1px solid {DARK_700}",
                        color=TEXT_PRIMARY, border_radius="8px",
                        padding_x="12px", padding_y="8px", font_size="13px",
                        padding_right="40px", width="100%",
                    ),
                    rx.tooltip(
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
                        content="Mostrar u ocultar contraseña",
                    ),
                    position="relative", flex="1",
                ),
                spacing="3", align="center", width="100%",
                class_name="twk-field-row",
            ),
            rx.hstack(
                rx.text("Confirmar clave", font_size="13px", color="var(--twk-slate-300)",
                        min_width="130px", font_weight="600"),
                rx.box(
                    rx.input(
                        placeholder="Repite la contraseña",
                        value=FoodState.config_admin_password_confirm,
                        on_change=FoodState.set_config_admin_password_confirm,
                        type=rx.cond(FoodState.config_admin_show_password, "text", "password"),
                        background=SURFACE_BASE, border=f"1px solid {DARK_700}",
                        color=TEXT_PRIMARY, border_radius="8px",
                        padding_x="12px", padding_y="8px", font_size="13px",
                        padding_right="40px", width="100%",
                    ),
                    rx.tooltip(
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
                        content="Mostrar u ocultar contraseña",
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
                background=rx.cond(active, "rgba(234,88,12,0.08)", "var(--twk-d900)"),
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
                    color=rx.cond(active, "var(--twk-text-primary)", "var(--twk-slate-300)"),
                    line_height="1",
                ),
                rx.text(
                    desc,
                    font_size="11px",
                    color=rx.cond(active, "var(--twk-slate-300)", "var(--twk-slate-400)"),
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
        background=rx.cond(active, "var(--twk-d800)", "transparent"),
        border=rx.cond(active, "1px solid rgba(234,88,12,0.40)", "1px solid transparent"),
        box_shadow=rx.cond(active, "0 1px 4px rgba(234,88,12,0.1)", "none"),
        cursor="pointer",
        on_click=ConfigSeccionState.ir_a(key),
        width="100%",
        transition="all 0.12s ease",
        _hover={
            "background": rx.cond(active, "var(--twk-d800)", "var(--twk-d700)"),
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
            _seccion_item("metodos",    "Métodos de pago", "wallet",    "Efectivo, Yape, Plin…"),
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
                color=rx.cond(active, "var(--twk-text-primary)", "var(--twk-slate-400)"),
                white_space="nowrap",
            ),
            spacing="2", align="center",
        ),
        on_click=ConfigSeccionState.ir_a(key),
        padding="8px 14px",
        border_radius="20px",
        background=rx.cond(active, "var(--twk-d800)", "transparent"),
        border=rx.cond(active, "1px solid rgba(234,88,12,0.40)", "1px solid transparent"),
        box_shadow=rx.cond(active, "0 1px 4px rgba(234,88,12,0.12)", "none"),
        cursor="pointer",
        flex_shrink="0",
        transition="all 0.12s ease",
        _hover={"background": rx.cond(active, "var(--twk-d800)", "var(--twk-d700)")},
    )


def _config_nav_tabs() -> rx.Component:
    """Barra horizontal de tabs para mobile/tablet — desplazable en X."""
    return rx.box(
        rx.hstack(
            _tab_pill("local",      "Local",      "store"),
            _tab_pill("carta",      "Carta",      "qr_code"),
            _tab_pill("mesas",      "Mesas",      "layout_grid"),
            _tab_pill("metodos",    "Métodos",    "wallet"),
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
        background=SURFACE_BASE, border=f"1px solid {DARK_700}",
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
                        "Estos datos aparecen en el encabezado del comprobante de pago "
                        "y en tu carta digital. Complétalos antes de imprimir tickets.",
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
                        rx.text("País (zona horaria)", font_size="12px",
                                font_weight="600", color=TEXT_MUTED),
                        rx.text(
                            "Define la hora local con la que se agrupan reportes y "
                            "cierres de caja por día. Cámbialo según dónde opera el local.",
                            font_size="11px", color=TEXT_MUTED,
                        ),
                        rx.select.root(
                            rx.select.trigger(width="100%"),
                            rx.select.content(
                                *[rx.select.item(nombre, value=code)
                                  for code, nombre in _PAISES]
                            ),
                            value=FoodState.config_pais,
                            on_change=FoodState.set_config_pais,
                        ),
                        spacing="1", width="100%", align="start",
                    ),
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
                                            color=SUCCESS_TEXT, font_weight="600"),
                                    rx.button(
                                        "Quitar logo",
                                        on_click=FoodState.quitar_logo_empresa,
                                        background="rgba(239,68,68,0.08)", color="var(--twk-danger-text)",
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
                                    rx.text("Arrastra o toca aquí", font_size="11px",
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
                                border="2px dashed var(--twk-d700)",
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
                background=SURFACE_BASE, border=f"1px solid {DARK_700}",
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
                                font_weight="600", color="var(--twk-slate-300)"),
                        rx.text_area(
                            placeholder="¡Gracias por su preferencia!",
                            value=FoodState.config_mensaje_ticket,
                            on_change=FoodState.set_config_mensaje_ticket,
                            background=SURFACE_BASE, border=f"1px solid {DARK_700}",
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
                                        font_weight="600", color="var(--twk-slate-300)"),
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
                    # Nota: los interruptores de "qué se imprime solo" (comprobante
                    # y comanda de cocina) viven ahora en la pestaña Impresoras,
                    # junto al resto de la configuración de impresión.
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
                background=SURFACE_BASE, border=f"1px solid {DARK_700}",
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


# ─── Métodos de pago ─────────────────────────────────────────────────────────

def _metodo_pago_row(metodo: MetodoPagoAdminView) -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.text(metodo.icono, font_size="20px", line_height="1", width="26px"),
            rx.vstack(
                rx.hstack(
                    rx.text(metodo.nombre, font_size="14px", font_weight="700",
                            color=TEXT_PRIMARY),
                    rx.badge(metodo.tipo_label, color_scheme="gray",
                             variant="soft", font_size="10px"),
                    rx.cond(
                        metodo.es_sistema,
                        rx.badge("Sistema", color_scheme="blue", variant="soft",
                                 font_size="10px"),
                        rx.fragment(),
                    ),
                    spacing="2", align="center",
                ),
                rx.text("código: " + metodo.codigo, font_size="11px", color=TEXT_MUTED),
                spacing="0", align="start",
            ),
            rx.spacer(),
            switch_toggle(metodo.activo, FoodState.toggle_metodo_activo(metodo.id)),
            rx.button(
                rx.icon(tag="pencil", size=14, color=TEXT_MUTED),
                on_click=FoodState.editar_metodo(metodo.id),
                background=SURFACE_BASE, border=f"1px solid {DARK_700}",
                border_radius="8px", cursor="pointer", padding="7px",
                _hover={"background": DARK_700},
            ),
            rx.cond(
                metodo.es_sistema,
                rx.fragment(),
                rx.button(
                    rx.icon(tag="trash_2", size=14, color=TEXT_MUTED),
                    on_click=FoodState.eliminar_metodo(metodo.id),
                    background=SURFACE_BASE, border=f"1px solid {DARK_700}",
                    border_radius="8px", cursor="pointer", padding="7px",
                    _hover={"background": "rgba(239,68,68,0.15)"},
                ),
            ),
            spacing="3", width="100%", align="center",
        ),
        padding="12px 14px",
        border=f"1px solid {DARK_700}",
        border_radius="10px",
        background=rx.cond(metodo.activo, PAGE_BACKGROUND, "rgba(148,163,184,0.05)"),
        opacity=rx.cond(metodo.activo, "1", "0.6"),
        width="100%",
    )


def _tipo_metodo_option(value: str, label: str) -> rx.Component:
    seleccionado = FoodState.metodo_form_tipo == value
    return rx.box(
        rx.text(label, font_size="12px", font_weight="600"),
        on_click=FoodState.set_metodo_form_tipo(value),
        background=rx.cond(seleccionado, ACCENT, DARK_800),
        color=rx.cond(seleccionado, "#FFFFFF", "var(--twk-slate-300)"),
        border=rx.cond(seleccionado, "1px solid #EA580C", f"1px solid {DARK_700}"),
        border_radius="8px", padding="7px 12px", cursor="pointer",
        white_space="nowrap",
        opacity=rx.cond(FoodState.metodo_form_es_sistema, "0.5", "1"),
        pointer_events=rx.cond(FoodState.metodo_form_es_sistema, "none", "auto"),
    )


def _metodos_section() -> rx.Component:
    return rx.box(
        rx.vstack(
            _section_header("Métodos de pago", "wallet", "💳"),
            rx.text(
                "Define cómo cobras: Efectivo, Yape, Plin, Tarjeta, Transferencia… "
                "Cada cobro en Caja se registra con el método real que usó el cliente. "
                "Solo el tipo «Efectivo» suma al arqueo del cajón.",
                font_size="12px", color=TEXT_MUTED,
            ),
            # Formulario
            rx.vstack(
                rx.hstack(
                    rx.input(
                        placeholder="Nombre (ej: Yape, Plin, Transferencia)",
                        value=FoodState.metodo_form_nombre,
                        on_change=FoodState.set_metodo_form_nombre,
                        flex="1", min_width="140px",
                        background=SURFACE_BASE, border=f"1px solid {DARK_700}",
                        color=TEXT_PRIMARY, border_radius="8px",
                        padding_x="10px", padding_y="7px", font_size="13px",
                        _focus={"border_color": ACCENT,
                                "box_shadow": "0 0 0 2px rgba(234,88,12,0.1)"},
                    ),
                    rx.input(
                        placeholder="Ícono 📱",
                        value=FoodState.metodo_form_icono,
                        on_change=FoodState.set_metodo_form_icono,
                        width="90px",
                        background=SURFACE_BASE, border=f"1px solid {DARK_700}",
                        color=TEXT_PRIMARY, border_radius="8px",
                        padding_x="10px", padding_y="7px", font_size="13px",
                        _focus={"border_color": ACCENT,
                                "box_shadow": "0 0 0 2px rgba(234,88,12,0.1)"},
                    ),
                    spacing="2", width="100%", align="center", flex_wrap="wrap",
                ),
                rx.hstack(
                    rx.text("Tipo:", font_size="12px", font_weight="600",
                            color=TEXT_MUTED),
                    *[_tipo_metodo_option(v, l) for v, l in TIPOS_METODO],
                    spacing="2", align="center", flex_wrap="wrap",
                ),
                rx.cond(
                    FoodState.metodo_form_error != "",
                    rx.text(FoodState.metodo_form_error, font_size="12px",
                            color="#EF4444"),
                    rx.fragment(),
                ),
                rx.hstack(
                    rx.button(
                        rx.hstack(
                            rx.icon(tag="plus", size=14, color=TEXT_WHITE),
                            rx.text(
                                rx.cond(FoodState.metodo_form_es_edicion,
                                        "Actualizar", "Agregar método"),
                                font_size="12px", font_weight="700", color=TEXT_WHITE,
                            ),
                            spacing="1", align="center",
                        ),
                        on_click=FoodState.guardar_metodo,
                        background=ACCENT, color=TEXT_WHITE,
                        border_radius="8px", cursor="pointer",
                        padding_x="14px", padding_y="8px",
                        _hover={"background": ACCENT_HOVER},
                        white_space="nowrap",
                    ),
                    rx.cond(
                        FoodState.metodo_form_es_edicion,
                        rx.button(
                            rx.text("Cancelar", font_size="12px", color=TEXT_MUTED),
                            on_click=FoodState.cancelar_metodo_form,
                            background=SURFACE_BASE, border=f"1px solid {DARK_700}",
                            border_radius="8px", cursor="pointer",
                            padding_x="14px", padding_y="8px",
                            _hover={"background": DARK_700},
                        ),
                        rx.fragment(),
                    ),
                    spacing="2", align="center",
                ),
                spacing="3", width="100%",
                padding="14px",
                background=DARK_800,
                border=f"1px solid {DARK_700}",
                border_radius="10px",
            ),
            # Lista
            rx.vstack(
                rx.foreach(FoodState.metodos_admin, _metodo_pago_row),
                spacing="2", width="100%",
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


def _content_metodos() -> rx.Component:
    return rx.vstack(
        _metodos_section(),
        width="100%",
        spacing="4",
    )


def _paper_width_option(label: str, value: str) -> rx.Component:
    seleccionado = FoodState.config_ticket_paper_width_mm == value
    return rx.box(
        rx.text(label, font_size="13px", font_weight="700"),
        on_click=FoodState.set_config_ticket_paper_width_mm(value),
        background=rx.cond(seleccionado, ACCENT, DARK_800),
        color=rx.cond(seleccionado, "#FFFFFF", "var(--twk-slate-300)"),
        border=rx.cond(seleccionado, "1px solid #EA580C", f"1px solid {DARK_700}"),
        border_radius="8px", padding="10px 20px", cursor="pointer",
        _hover={"border_color": ACCENT},
    )


def _modo_option(label: str, value: str, desc: str) -> rx.Component:
    seleccionado = FoodState.config_modo_impresion == value
    return rx.box(
        rx.vstack(
            rx.text(label, font_size="13px", font_weight="700"),
            rx.text(desc, font_size="11px", opacity="0.85"),
            spacing="1", align="start",
        ),
        on_click=FoodState.set_modo_impresion(value),
        background=rx.cond(seleccionado, ACCENT, DARK_800),
        color=rx.cond(seleccionado, "#FFFFFF", "var(--twk-slate-300)"),
        border=rx.cond(seleccionado, "1px solid #EA580C", f"1px solid {DARK_700}"),
        border_radius="10px", padding="12px 16px", cursor="pointer", flex="1",
        _hover={"border_color": ACCENT},
    )


def _mini_badge(text, bg: str, color: str) -> rx.Component:
    return rx.badge(text, background=bg, color=color, border_radius="5px",
                    font_size="10px", padding="1px 7px")


def _impresora_row(imp: ImpresoraView) -> rx.Component:
    return rx.hstack(
        rx.vstack(
            rx.hstack(
                rx.text(imp.nombre, font_size="13px", font_weight="700", color=TEXT_PRIMARY),
                _mini_badge(imp.rol, "rgba(234,88,12,0.12)", ACCENT),
                _mini_badge(imp.tipo, "rgba(59,130,246,0.12)", "var(--twk-info-text)"),
                rx.cond(
                    imp.activa,
                    _mini_badge("Activa", "rgba(34,197,94,0.12)", SUCCESS_SOLID),
                    _mini_badge("Inactiva", "rgba(239,68,68,0.12)", "var(--twk-danger-text)"),
                ),
                spacing="2", align="center", flex_wrap="wrap",
            ),
            rx.text(
                rx.cond(
                    imp.tipo == "red",
                    "Red · " + imp.ip + ":" + imp.puerto.to_string(),
                    "USB · " + imp.usb_target,
                ),
                font_size="11px", color=TEXT_MUTED, font_family="monospace",
            ),
            spacing="1", align="start", flex="1", min_width="0",
        ),
        rx.tooltip(
            rx.button(
                rx.icon(tag="printer", size=13),
                on_click=FoodState.imprimir_prueba_impresora(imp.rol),
                background="rgba(59,130,246,0.08)", color="var(--twk-info-text)",
                border="1px solid #BFDBFE", border_radius="6px",
                cursor="pointer", padding="5px", min_width="0", height="auto",
                _hover={"opacity": "0.85"},
            ),
            content="Imprimir prueba",
        ),
        rx.tooltip(
            rx.button(
                rx.icon(tag="pencil", size=13),
                on_click=FoodState.editar_impresora_config(imp.id),
                background="rgba(234,88,12,0.08)", color=ACCENT, border="1px solid rgba(234,88,12,0.40)",
                border_radius="6px", cursor="pointer",
                padding="5px", min_width="0", height="auto", _hover={"opacity": "0.85"}),
            content="Editar impresora",
        ),
        rx.tooltip(
            switch_toggle(imp.activa, FoodState.toggle_impresora_activa(imp.id)),
            content=rx.cond(imp.activa, "Desactivar impresora", "Activar impresora"),
        ),
        rx.alert_dialog.root(
            rx.alert_dialog.trigger(
                rx.tooltip(
                    rx.button(
                        rx.icon(tag="trash_2", size=12, color="var(--twk-danger-text)"),
                        background="rgba(239,68,68,0.08)", border="1px solid #FECACA",
                        border_radius="6px", cursor="pointer",
                        padding_x="7px", padding_y="3px", _hover={"opacity": "0.85"},
                    ),
                    content="Eliminar impresora",
                ),
            ),
            rx.alert_dialog.content(
                rx.alert_dialog.title("¿Eliminar impresora?"),
                rx.alert_dialog.description(
                    "Se eliminará \"" + imp.nombre + "\" de forma permanente.", size="2",
                ),
                rx.hstack(
                    rx.alert_dialog.cancel(
                        rx.button("Cancelar", background=DARK_800, color=TEXT_MUTED,
                                  border=f"1px solid {DARK_700}", border_radius="8px",
                                  font_size="13px", cursor="pointer", padding_x="14px", padding_y="8px"),
                    ),
                    rx.alert_dialog.action(
                        rx.button("Eliminar", on_click=FoodState.eliminar_impresora_config(imp.id),
                                  background="#DC2626", color=TEXT_WHITE, border_radius="8px",
                                  font_size="13px", font_weight="700", cursor="pointer",
                                  padding_x="14px", padding_y="8px", _hover={"background": "var(--twk-danger-text)"}),
                    ),
                    spacing="3", justify="end", width="100%", margin_top="16px",
                ),
            ),
        ),
        width="100%", align="center", padding="8px 10px", background=DARK_800,
        border_radius="8px", border=f"1px solid {DARK_700}", gap="8px", flex_wrap="wrap",
    )


def _impresora_form() -> rx.Component:
    _inp = dict(background=PAGE_BACKGROUND, border=f"1px solid {DARK_700}",
                color=TEXT_PRIMARY, border_radius="8px", padding_x="10px",
                padding_y="7px", font_size="13px",
                _focus={"border_color": ACCENT, "box_shadow": "0 0 0 2px rgba(234,88,12,0.1)"})
    return rx.vstack(
        rx.hstack(
            rx.input(placeholder="Nombre (ej: Cocina)", value=FoodState.impresora_form_nombre,
                     on_change=FoodState.set_impresora_form_nombre, flex="1", min_width="140px", **_inp),
            rx.select(["cocina", "caja"], value=FoodState.impresora_form_rol,
                      on_change=FoodState.set_impresora_form_rol, width="120px"),
            rx.select(["red", "usb"], value=FoodState.impresora_form_tipo,
                      on_change=FoodState.set_impresora_form_tipo, width="110px"),
            spacing="2", width="100%", align="center", flex_wrap="wrap",
        ),
        rx.cond(
            FoodState.impresora_form_tipo == "red",
            rx.hstack(
                rx.input(placeholder="IP (ej: 192.168.1.50)", value=FoodState.impresora_form_ip,
                         on_change=FoodState.set_impresora_form_ip, flex="1", min_width="160px", **_inp),
                rx.input(placeholder="Puerto", value=FoodState.impresora_form_puerto,
                         on_change=FoodState.set_impresora_form_puerto, type="number",
                         width="100px", **_inp),
                spacing="2", width="100%", align="center", flex_wrap="wrap",
            ),
            rx.input(placeholder="Nombre exacto de la impresora en Windows",
                     value=FoodState.impresora_form_usb_target,
                     on_change=FoodState.set_impresora_form_usb_target, width="100%", **_inp),
        ),
        rx.hstack(
            rx.button(
                rx.hstack(
                    rx.icon(tag="plus", size=14, color=TEXT_WHITE),
                    rx.text(rx.cond(FoodState.impresora_form_id > 0, "Actualizar", "Agregar impresora"),
                            font_size="12px", font_weight="700", color=TEXT_WHITE),
                    spacing="1", align="center",
                ),
                on_click=FoodState.guardar_impresora_config,
                background=ACCENT, border_radius="8px", cursor="pointer",
                padding_x="14px", padding_y="7px", _hover={"background": ACCENT_HOVER},
            ),
            rx.cond(
                FoodState.impresora_form_id > 0,
                rx.button(rx.icon(tag="x", size=14, color=TEXT_MUTED),
                          on_click=FoodState.cancelar_impresora_form,
                          background=SURFACE_BASE, border=f"1px solid {DARK_700}",
                          border_radius="8px", cursor="pointer", padding="7px",
                          _hover={"background": DARK_700}),
                rx.fragment(),
            ),
            spacing="2", width="100%",
        ),
        spacing="3", width="100%",
    )


def _agente_row(a: AgenteView) -> rx.Component:
    return rx.hstack(
        rx.vstack(
            rx.text(a.nombre, font_size="13px", font_weight="700", color=TEXT_PRIMARY),
            rx.text("Última conexión: " + a.last_seen_texto, font_size="11px", color=TEXT_MUTED),
            spacing="1", align="start", flex="1", min_width="0",
        ),
        rx.cond(
            a.activo,
            _mini_badge("Activo", "rgba(34,197,94,0.12)", SUCCESS_SOLID),
            _mini_badge("Revocado", "rgba(148,163,184,0.15)", TEXT_MUTED),
        ),
        rx.cond(
            a.activo,
            rx.button("Revocar", on_click=FoodState.revocar_agente(a.id),
                      background="rgba(239,68,68,0.08)", color="var(--twk-danger-text)", border="1px solid #FECACA",
                      border_radius="6px", font_size="10px", cursor="pointer",
                      padding_x="8px", padding_y="3px", _hover={"opacity": "0.85"}),
            rx.fragment(),
        ),
        width="100%", align="center", padding="8px 10px", background=DARK_800,
        border_radius="8px", border=f"1px solid {DARK_700}", gap="8px",
    )


def _bloque_navegador() -> rx.Component:
    return rx.vstack(
        rx.box(
            rx.hstack(
                rx.icon(tag="info", size=14, color="var(--twk-info-text)"),
                rx.text(
                    "En modo navegador los tickets se imprimen desde la pestaña "
                    "abierta (con --kiosk-printing sale sin diálogo). Instala la "
                    "impresora en el sistema operativo de esa tablet/PC.",
                    font_size="12px", color="var(--twk-slate-300)",
                ),
                spacing="2", align="start",
            ),
            background="rgba(59,130,246,0.08)", border="1px solid #BFDBFE",
            border_radius="8px", padding="12px 14px", width="100%",
        ),
        rx.button(
            rx.hstack(
                rx.icon(tag="printer", size=14, color=ACCENT),
                rx.text("Imprimir ticket de prueba", font_size="13px",
                        font_weight="700", color=ACCENT),
                spacing="2", align="center",
            ),
            on_click=FoodState.imprimir_ticket_prueba,
            background="rgba(234,88,12,0.08)", border="1px solid rgba(234,88,12,0.40)",
            border_radius="8px", padding_x="16px", padding_y="9px", cursor="pointer",
            align_self="start",
            _hover={"background": "rgba(234,88,12,0.12)", "border_color": ACCENT},
        ),
        spacing="4", width="100%",
    )


def _paso_agente(numero: str, texto) -> rx.Component:
    return rx.hstack(
        rx.box(
            rx.text(numero, font_size="12px", font_weight="800", color=TEXT_WHITE),
            background=ACCENT, border_radius="50%",
            min_width="22px", height="22px", display="flex",
            align_items="center", justify_content="center", flex_shrink="0",
        ),
        rx.text(texto, font_size="13px", color=TEXT_PRIMARY, line_height="1.5"),
        spacing="3", align="start", width="100%",
    )


def _bloque_agente() -> rx.Component:
    return rx.vstack(
        # ── Descargar e instalar el agente ──
        rx.box(
            rx.vstack(
                _section_header("Descargar e instalar el agente", "download"),
                rx.text("Instala esta app UNA sola vez en la PC de la caja (la que "
                        "tiene las impresoras). Imprime en segundo plano, sin dejar "
                        "ninguna pestaña abierta.",
                        font_size="12px", color=TEXT_MUTED),
                rx.link(
                    rx.hstack(
                        rx.icon(tag="download", size=16, color=TEXT_WHITE),
                        rx.text("Descargar agente (Windows)", font_size="13px",
                                font_weight="700", color=TEXT_WHITE),
                        spacing="2", align="center",
                    ),
                    href=AGENTE_DOWNLOAD_URL,
                    is_external=True,
                    background=ACCENT, border_radius="8px", padding="10px 16px",
                    text_decoration="none", width="fit-content",
                    _hover={"background": ACCENT_HOVER},
                ),
                rx.vstack(
                    _paso_agente("1", "Descarga el archivo TuwaykifoodAgente.exe y "
                                      "guárdalo en la PC de la caja."),
                    _paso_agente("2", "Ábrelo con doble clic. La primera vez crea un "
                                      "archivo config.ini justo al lado y aparece un "
                                      "ícono en la bandeja del sistema (junto al reloj)."),
                    _paso_agente("3", "Genera un token aquí abajo y pégalo dentro de "
                                      "config.ini (ábrelo con el Bloc de notas)."),
                    _paso_agente("4", "Cierra y vuelve a abrir el agente. El ícono "
                                      "queda en verde y ya imprime solo."),
                    spacing="3", align="start", width="100%",
                    background=PAGE_BACKGROUND, border=f"1px solid {DARK_700}",
                    border_radius="10px", padding="16px",
                ),
                spacing="4", width="100%",
            ),
            background=SURFACE_BASE, border=f"1px solid {DARK_700}",
            border_radius="12px", padding="20px", width="100%",
            box_shadow="0 1px 3px rgba(0,0,0,0.06)",
        ),
        # ── Impresoras ──
        rx.box(
            rx.vstack(
                _section_header("Impresoras", "printer"),
                rx.text("Carga cada impresora física del local (de red por IP o USB "
                        "conectada a la PC de la caja) y su rol.",
                        font_size="12px", color=TEXT_MUTED),
                _impresora_form(),
                rx.cond(
                    FoodState.impresoras_config.length() == 0,
                    rx.center(rx.text("Sin impresoras. Agrega una arriba.",
                                      font_size="12px", color=TEXT_MUTED),
                              padding_y="16px", width="100%"),
                    rx.vstack(rx.foreach(FoodState.impresoras_config, _impresora_row),
                              spacing="2", width="100%"),
                ),
                spacing="4", width="100%",
            ),
            background=SURFACE_BASE, border=f"1px solid {DARK_700}",
            border_radius="12px", padding="20px", width="100%",
            box_shadow="0 1px 3px rgba(0,0,0,0.06)",
        ),
        # ── Agentes ──
        rx.box(
            rx.vstack(
                _section_header("Agente de impresión", "monitor"),
                rx.text("Genera un token y pégalo en el archivo config.ini del agente "
                        "instalado en la PC de la caja.",
                        font_size="12px", color=TEXT_MUTED),
                rx.hstack(
                    rx.input(placeholder="Nombre del agente (ej: Caja principal)",
                             value=FoodState.agente_form_nombre,
                             on_change=FoodState.set_agente_form_nombre, flex="1",
                             background=PAGE_BACKGROUND, border=f"1px solid {DARK_700}",
                             color=TEXT_PRIMARY, border_radius="8px", padding_x="10px",
                             padding_y="7px", font_size="13px"),
                    rx.button(
                        rx.hstack(rx.icon(tag="key_round", size=14, color=TEXT_WHITE),
                                  rx.text("Generar agente", font_size="12px",
                                          font_weight="700", color=TEXT_WHITE),
                                  spacing="1", align="center"),
                        on_click=FoodState.crear_agente_impresion,
                        background=ACCENT, border_radius="8px", cursor="pointer",
                        padding_x="14px", padding_y="7px", white_space="nowrap",
                        _hover={"background": ACCENT_HOVER},
                    ),
                    spacing="2", width="100%", align="center", flex_wrap="wrap",
                ),
                rx.cond(
                    FoodState.agente_token_revelado != "",
                    rx.box(
                        rx.vstack(
                            rx.hstack(
                                rx.icon(tag="triangle_alert", size=14, color=WARNING_TEXT),
                                rx.text("Token — cópialo ahora, se muestra una sola vez",
                                        font_size="12px", font_weight="700", color=TEXT_PRIMARY),
                                spacing="2", align="center",
                            ),
                            rx.box(
                                rx.text(FoodState.agente_token_revelado, font_size="12px",
                                        color="var(--twk-slate-300)", word_break="break-all",
                                        font_family="monospace"),
                                background=PAGE_BACKGROUND, border=f"1px solid {DARK_700}",
                                border_radius="6px", padding="8px 10px", width="100%",
                            ),
                            rx.hstack(
                                rx.button(
                                    rx.hstack(rx.icon(tag="copy", size=13), rx.text("Copiar", font_size="12px"),
                                              spacing="1", align="center"),
                                    on_click=rx.set_clipboard(FoodState.agente_token_revelado),
                                    background=ACCENT, color=TEXT_WHITE, border_radius="7px",
                                    cursor="pointer", padding_x="12px", padding_y="6px",
                                    _hover={"background": ACCENT_HOVER},
                                ),
                                rx.button("Ya lo copié", on_click=FoodState.ocultar_token_revelado,
                                          background=DARK_800, color=TEXT_MUTED,
                                          border=f"1px solid {DARK_700}", border_radius="7px",
                                          font_size="12px", cursor="pointer",
                                          padding_x="12px", padding_y="6px"),
                                spacing="2",
                            ),
                            spacing="3", width="100%",
                        ),
                        background="rgba(234,179,8,0.08)", border="1px solid rgba(234,179,8,0.40)",
                        border_radius="10px", padding="14px", width="100%",
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    FoodState.agentes_config.length() == 0,
                    rx.fragment(),
                    rx.vstack(rx.foreach(FoodState.agentes_config, _agente_row),
                              spacing="2", width="100%"),
                ),
                spacing="4", width="100%",
            ),
            background=SURFACE_BASE, border=f"1px solid {DARK_700}",
            border_radius="12px", padding="20px", width="100%",
            box_shadow="0 1px 3px rgba(0,0,0,0.06)",
        ),
        spacing="4", width="100%",
    )


def _content_impresoras() -> rx.Component:
    return rx.vstack(
        # ── Selector de modo ──
        rx.box(
            rx.vstack(
                _section_header("Modo de impresión", "printer"),
                rx.text("Elige cómo se imprimen las comandas y comprobantes.",
                        font_size="12px", color=TEXT_MUTED),
                rx.hstack(
                    _modo_option("Navegador (kiosk)", "navegador",
                                 "Imprime desde la pestaña abierta."),
                    _modo_option("Agente local", "agente",
                                 "Una app en la PC imprime en red o USB."),
                    spacing="3", width="100%", flex_wrap="wrap",
                ),
                spacing="3", width="100%",
            ),
            background=SURFACE_BASE, border=f"1px solid {DARK_700}",
            border_radius="12px", padding="20px", width="100%",
            box_shadow="0 1px 3px rgba(0,0,0,0.06)",
        ),
        # ── Ancho de papel (aplica a ambos modos) ──
        rx.box(
            rx.vstack(
                rx.text("Ancho de papel", font_size="13px", color="var(--twk-slate-300)", font_weight="600"),
                rx.text(
                    "58 mm = tickets angostos; 80 mm = estándar. Elige según tu impresora.",
                    font_size="11px", color=TEXT_MUTED,
                ),
                rx.hstack(
                    _paper_width_option("58mm", "58"),
                    _paper_width_option("80mm", "80"),
                    rx.spacer(),
                    rx.button(
                        rx.hstack(rx.icon(tag="save", size=14, color=TEXT_WHITE),
                                  rx.text("Guardar", font_size="13px", font_weight="700", color=TEXT_WHITE),
                                  spacing="2", align="center"),
                        on_click=FoodState.guardar_config_impresora,
                        background=ACCENT, border_radius="8px", padding_x="16px", padding_y="9px",
                        cursor="pointer", _hover={"background": ACCENT_HOVER},
                    ),
                    spacing="3", width="100%", align="center",
                ),
                spacing="3", width="100%",
            ),
            background=SURFACE_BASE, border=f"1px solid {DARK_700}",
            border_radius="12px", padding="20px", width="100%",
            box_shadow="0 1px 3px rgba(0,0,0,0.06)",
        ),
        # ── Qué se imprime automáticamente ──
        rx.box(
            rx.vstack(
                _section_header("Qué se imprime automáticamente", "receipt"),
                rx.text(
                    "Controla qué documentos salen solos. Apagar uno ahorra papel; "
                    "igual puedes imprimir a demanda cuando haga falta.",
                    font_size="12px", color=TEXT_MUTED,
                ),
                # Comanda de cocina
                rx.hstack(
                    rx.vstack(
                        rx.text("Imprimir comanda de cocina", font_size="13px",
                                font_weight="600", color="var(--twk-slate-300)"),
                        rx.text(
                            "Al enviar un pedido a cocina. Si lo desactivas, la cocina "
                            "trabaja solo con la pantalla del KDS (sin papel).",
                            font_size="11px", color=TEXT_MUTED,
                        ),
                        spacing="0", align="start",
                    ),
                    rx.spacer(),
                    _toggle_btn(
                        FoodState.config_comanda_auto,
                        FoodState.set_config_comanda_auto(
                            ~FoodState.config_comanda_auto
                        ),
                    ),
                    width="100%", align="center",
                ),
                rx.divider(border_color=DARK_700),
                # Comprobante de pago
                rx.hstack(
                    rx.vstack(
                        rx.text("Imprimir comprobante al cobrar", font_size="13px",
                                font_weight="600", color="var(--twk-slate-300)"),
                        rx.text(
                            "Al cobrar un pedido. Si lo desactivas, no sale solo: lo "
                            "imprimes a demanda con el botón Imprimir comprobante en Caja.",
                            font_size="11px", color=TEXT_MUTED,
                        ),
                        spacing="0", align="start",
                    ),
                    rx.spacer(),
                    _toggle_btn(
                        FoodState.config_comprobante_auto,
                        FoodState.set_config_comprobante_auto(
                            ~FoodState.config_comprobante_auto
                        ),
                    ),
                    width="100%", align="center",
                ),
                rx.hstack(
                    rx.spacer(),
                    rx.button(
                        rx.hstack(rx.icon(tag="save", size=14, color=TEXT_WHITE),
                                  rx.text("Guardar", font_size="13px", font_weight="700", color=TEXT_WHITE),
                                  spacing="2", align="center"),
                        on_click=FoodState.guardar_config_impresora,
                        background=ACCENT, border_radius="8px", padding_x="16px", padding_y="9px",
                        cursor="pointer", _hover={"background": ACCENT_HOVER},
                    ),
                    width="100%",
                ),
                spacing="3", width="100%",
            ),
            background=SURFACE_BASE, border=f"1px solid {DARK_700}",
            border_radius="12px", padding="20px", width="100%",
            box_shadow="0 1px 3px rgba(0,0,0,0.06)",
        ),
        # ── Bloque según modo ──
        rx.cond(
            FoodState.config_modo_impresion == "agente",
            _bloque_agente(),
            _bloque_navegador(),
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
        rx.tooltip(
            rx.button(
                rx.icon(tag="pencil", size=14),
                on_click=FoodState.abrir_form_sucursal(suc.id),
                variant="ghost", size="1", cursor="pointer",
            ),
            content="Editar sucursal",
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
                    "Si tienes más de un local, cada sucursal tiene sus propias mesas, "
                    "impresoras y turnos, y el personal elige sucursal al iniciar sesión. "
                    "Con un solo local no necesitas tocar nada acá.",
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
            background=SURFACE_BASE, border=f"1px solid {DARK_700}",
            border_radius="12px", padding="20px", width="100%",
        ),
        # Modal form
        rx.dialog.root(
            rx.dialog.content(
                rx.dialog.title("Sucursal"),
                rx.vstack(
                    rx.text("Nombre *", font_size="12px", font_weight="600", color="var(--twk-slate-300)"),
                    rx.input(
                        value=FoodState.sucursal_admin_form_nombre,
                        on_change=FoodState.on_change_suc_nombre,
                        placeholder="Sede Central",
                    ),
                    rx.text("Dirección", font_size="12px", font_weight="600", color="var(--twk-slate-300)"),
                    rx.input(
                        value=FoodState.sucursal_admin_form_direccion,
                        on_change=FoodState.on_change_suc_direccion,
                        placeholder="Av. Principal 123",
                    ),
                    rx.text("Teléfono", font_size="12px", font_weight="600", color="var(--twk-slate-300)"),
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
                max_width="560px",
                width="92vw",
                max_height="90vh",
                overflow_y="auto",
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
                        ConfigSeccionState.seccion == "metodos",
                        _content_metodos(),
                        rx.cond(
                            ConfigSeccionState.seccion == "impresoras",
                            _content_impresoras(),
                            _content_cuenta(),
                        ),
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
