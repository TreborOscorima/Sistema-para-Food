"""Componentes compartidos y shell visual de TUWAYKIFOOD POS."""

from __future__ import annotations

import reflex as rx

from app.states.food_state import FoodState
from app.components.modulos import MODULOS as _M


# ─── PALETA — re-exportada desde theme.py (fuente única de verdad) ───────────
from app.components.theme import (  # noqa: F401 — re-export
    ACCENT, ACCENT_BG, ACCENT_GLOW, ACCENT_HOVER, ACCENT_MUTED, ACCENT_SHADOW,
    ACCENT_SOFT, ACCENT_TEXT,
    BORDER_ACCENT, BORDER_COLOR, BORDER_STRONG,
    DANGER_BG, DANGER_BORDER, DANGER_ICON, DANGER_SOLID, DANGER_TEXT,
    DARK_600, DARK_700, DARK_800, DARK_900,
    GLOW,
    INFO_BG, INFO_BORDER, INFO_SOLID, INFO_TEXT,
    PAGE_BACKGROUND,
    PURPLE, PURPLE_LIGHT,
    SIDEBAR_BG, SIDEBAR_BORDER, SIDEBAR_HOVER_BG, SIDEBAR_TEXT, SIDEBAR_TEXT_ACTIVE,
    SLATE_100, SLATE_200, SLATE_300, SLATE_400, SLATE_50, SLATE_500,
    SOFT_GLOW,
    SUCCESS_BG, SUCCESS_BORDER, SUCCESS_DARK, SUCCESS_SOLID, SUCCESS_TEXT,
    SURFACE_BASE, SURFACE_ELEVATED, SURFACE_GHOST, SURFACE_HOVER, SURFACE_INTERACTIVE,
    SURFACE_MUTED, SURFACE_SOFT,
    TEXT_MUTED, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_WHITE,
    WARNING_BG, WARNING_BORDER, WARNING_SOLID, WARNING_TEXT,
    Z_ADMIN_BACKDROP, Z_ADMIN_SIDEBAR, Z_DRAWER, Z_MENU_PUBLIC, Z_MODAL,
    Z_STICKY_HEADER, Z_TOAST,
    DARK_MODAL_PROPS, DARK_MODAL_TEXT, DARK_MODAL_MUTED, DARK_MODAL_BORDER,
    DARK_MODAL_INPUT_BG, DARK_MODAL_INPUT_BORDER, DARK_MODAL_BTN_BG, DARK_MODAL_BTN_BORDER,
)


# ─── UTILIDADES PÚBLICAS ──────────────────────────────────────────────────────────

def styled_switch(checked, on_change, *, color: str = ACCENT, size: str = "md") -> rx.Component:
    """Toggle estilo iOS, reutilizable — reemplazo estético de rx.switch.

    ``checked`` es un Var bool y ``on_change`` el setter (misma firma que
    rx.switch: recibe el nuevo valor). Al tocar dispara ``on_change(~checked)``.
    ``size``: "sm" (compacto) o "md" (default).
    """
    w, h, thumb, travel = {
        "sm": ("34px", "20px", "16px", "14px"),
        "md": ("42px", "24px", "20px", "18px"),
    }.get(size, ("42px", "24px", "20px", "18px"))
    return rx.box(
        rx.box(
            position="absolute", top="2px", left="2px",
            width=thumb, height=thumb, border_radius="9999px",
            background="#FFFFFF", box_shadow="0 1px 3px rgba(0,0,0,0.45)",
            transform=rx.cond(checked, f"translateX({travel})", "translateX(0)"),
            transition="transform 0.22s cubic-bezier(0.4,0,0.2,1)",
        ),
        on_click=on_change(~checked),
        position="relative", width=w, height=h, border_radius="9999px",
        background=rx.cond(checked, color, DARK_600),
        border=rx.cond(checked, f"1px solid {color}", f"1px solid {DARK_700}"),
        cursor="pointer", flex_shrink="0",
        transition="background 0.22s ease, border-color 0.22s ease",
        _hover={"opacity": "0.88"},
    )


def switch_toggle(checked, on_click, *, color: str = ACCENT, size: str = "sm") -> rx.Component:
    """Switch iOS igual que ``styled_switch`` pero recibe un ``on_click`` ya armado.

    Útil en filas de tablas donde el evento es un handler tipo ``toggle_x(id)``
    (no un setter que recibe el nuevo valor). Default ``size="sm"`` para filas.
    """
    w, h, thumb, travel = {
        "sm": ("34px", "20px", "16px", "14px"),
        "md": ("42px", "24px", "20px", "18px"),
    }.get(size, ("34px", "20px", "16px", "14px"))
    return rx.box(
        rx.box(
            position="absolute", top="2px", left="2px",
            width=thumb, height=thumb, border_radius="9999px",
            background="#FFFFFF", box_shadow="0 1px 3px rgba(0,0,0,0.45)",
            transform=rx.cond(checked, f"translateX({travel})", "translateX(0)"),
            transition="transform 0.22s cubic-bezier(0.4,0,0.2,1)",
        ),
        on_click=on_click,
        position="relative", width=w, height=h, border_radius="9999px",
        background=rx.cond(checked, color, DARK_600),
        border=rx.cond(checked, f"1px solid {color}", f"1px solid {DARK_700}"),
        cursor="pointer", flex_shrink="0",
        transition="background 0.22s ease, border-color 0.22s ease",
        _hover={"opacity": "0.88"},
    )


def color_mode_toggle(*, on_sidebar: bool = False, size: int = 30) -> rx.Component:
    """Interruptor claro/oscuro (sol/luna).

    Usa el color-mode nativo de Reflex: ``rx.toggle_color_mode`` alterna y la
    elección se persiste sola en el navegador (localStorage 'theme'), agregando
    la clase ``light``/``dark`` al <html>. En modo oscuro muestra el sol (para
    pasar a claro); en claro muestra la luna. ``on_sidebar`` usa la paleta del
    sidebar; si no, la de header/superficie.
    """
    if on_sidebar:
        base_color, base_bg = SIDEBAR_TEXT, SIDEBAR_HOVER_BG
        hover = {"background": SURFACE_HOVER, "color": SIDEBAR_TEXT_ACTIVE}
    else:
        base_color, base_bg = TEXT_SECONDARY, SURFACE_MUTED
        hover = {"background": SURFACE_HOVER, "color": TEXT_PRIMARY}
    return rx.tooltip(
        rx.box(
            rx.color_mode_cond(
                light=rx.icon(tag="moon", size=15),
                dark=rx.icon(tag="sun", size=15),
            ),
            on_click=rx.toggle_color_mode,
            width=f"{size}px",
            height=f"{size}px",
            border_radius="8px",
            display="flex",
            align_items="center",
            justify_content="center",
            cursor="pointer",
            flex_shrink="0",
            color=base_color,
            background=base_bg,
            border=f"1px solid {BORDER_COLOR}" if not on_sidebar else "1px solid transparent",
            _hover=hover,
            transition="background .15s ease, color .15s ease",
        ),
        content="Cambiar tema (claro / oscuro)",
    )


def surface_card(*children, **props) -> rx.Component:
    bg           = props.pop("background", SURFACE_BASE)
    border       = props.pop("border", f"1px solid {BORDER_COLOR}")
    border_radius = props.pop("border_radius", "14px")
    box_shadow   = props.pop("box_shadow", GLOW)
    width        = props.pop("width", "100%")
    incoming     = props.pop("style", {})
    return rx.box(
        *children,
        style={"background": bg, "border": border, "border_radius": border_radius,
               "box_shadow": box_shadow, **incoming},
        width=width,
        **props,
    )


def section_card(*children, **props) -> rx.Component:
    bg           = props.pop("background", SURFACE_SOFT)
    border       = props.pop("border", f"1px solid {BORDER_COLOR}")
    border_radius = props.pop("border_radius", "10px")
    box_shadow   = props.pop("box_shadow", SOFT_GLOW)
    width        = props.pop("width", "100%")
    incoming     = props.pop("style", {})
    return rx.box(
        *children,
        style={"background": bg, "border": border, "border_radius": border_radius,
               "box_shadow": box_shadow, **incoming},
        width=width,
        **props,
    )


def action_button(label: str, on_click, icon_tag: str = "arrow_right") -> rx.Component:
    return rx.button(
        rx.hstack(
            rx.icon(tag=icon_tag, size=16),
            rx.text(label, font_weight="700"),
            spacing="2",
            align="center",
        ),
        on_click=on_click,
        background=ACCENT,
        color="#FFFFFF",
        border_radius="9px",
        height="40px",
        padding_x="1rem",
        _hover={"background": ACCENT_HOVER},
    )


def status_banner(message) -> rx.Component:
    return section_card(
        rx.hstack(
            rx.box(width="8px", height="8px", border_radius="999px",
                   style={"background": ACCENT}),
            rx.text(message, color=TEXT_SECONDARY, font_weight="600", font_size="0.9rem"),
            spacing="3",
            align="center",
        ),
        padding="0.75rem 1rem",
    )


def kpi_card(title: str, value, description: str = "",
             accent_color: str = ACCENT) -> rx.Component:
    return surface_card(
        rx.vstack(
            rx.text(title, color=TEXT_MUTED, font_size="0.72rem", font_weight="700",
                    letter_spacing="0.08em", text_transform="uppercase"),
            rx.text(value, color=TEXT_PRIMARY, font_weight="800", font_size="1.75rem",
                    line_height="1.1"),
            rx.cond(
                description != "",
                rx.text(description, color=TEXT_MUTED, font_size="0.85rem"),
                rx.fragment(),
            ),
            align="start",
            spacing="2",
            width="100%",
        ),
        padding="1.1rem 1.2rem",
        border=f"1px solid {accent_color}",
    )


# ─── BRAND COMPONENT ──────────────────────────────────────────────────────────────

def _brand(compact: bool = False, dark: bool = False) -> rx.Component:
    title_color = TEXT_PRIMARY
    sub_color   = TEXT_MUTED
    return rx.hstack(
        rx.image(
            src="/TUWAYKIFOODFAVICON.png",
            width="34px",
            height="34px",
            border_radius="9px",
            flex_shrink="0",
            alt="TUWAYKIFOOD",
        ),
        rx.cond(
            compact,
            rx.fragment(),
            rx.vstack(
                rx.text(
                    "TUWAYKIFOOD",
                    color=title_color,
                    font_weight="800",
                    letter_spacing="0.07em",
                    font_size="12px",
                    text_transform="uppercase",
                    line_height="1",
                ),
                rx.text(
                    "Sistema para restaurantes",
                    color=sub_color,
                    font_size="11px",
                    line_height="1",
                ),
                align="start",
                spacing="1",
            ),
        ),
        spacing="3",
        align="center",
    )


# ─── USER SUMMARY (header claro) ─────────────────────────────────────────────────

def _user_summary() -> rx.Component:
    return rx.hstack(
        rx.box(
            rx.icon(tag="user_round", size=15, color="#FFFFFF"),
            width="34px",
            height="34px",
            border_radius="full",
            style={"background": "linear-gradient(135deg,#EA580C 0%,#C2410C 100%)"},
            display="flex",
            align_items="center",
            justify_content="center",
            flex_shrink="0",
        ),
        rx.vstack(
            rx.text(FoodState.usuario_nombre, color=TEXT_PRIMARY, font_weight="700",
                    font_size="13px", max_width="160px",
                    text_overflow="ellipsis", overflow="hidden", white_space="nowrap"),
            rx.text(FoodState.usuario_rol, color=ACCENT, font_weight="600", font_size="11px",
                    background=ACCENT_BG, padding_x="0.4rem", padding_y="1px",
                    border_radius="full", display="inline-block"),
            align="start",
            spacing="0",
        ),
        spacing="2",
        align="center",
    )


def user_session_badge() -> rx.Component:
    return rx.hstack(
        _user_summary(),
        rx.button(
            rx.hstack(
                rx.icon(tag="log_out", size=14),
                rx.text("Salir", font_weight="600", font_size="12px"),
                spacing="1",
                align="center",
            ),
            on_click=FoodState.logout,
            background=DANGER_BG,
            color=DANGER_TEXT,
            border=f"1px solid {DANGER_BORDER}",
            border_radius="8px",
            height="34px",
            padding_x="10px",
            _hover={"background": "rgba(239,68,68,0.12)"},
        ),
        spacing="3",
        align="center",
    )


# ─── USER BADGE OSCURO (sidebar) ─────────────────────────────────────────────────

def _sidebar_user_badge() -> rx.Component:
    return rx.hstack(
        rx.box(
            rx.icon(tag="user_round", size=14, color="#FFFFFF"),
            width="32px",
            height="32px",
            border_radius="full",
            background="rgba(234,88,12,0.85)",
            display="flex",
            align_items="center",
            justify_content="center",
            flex_shrink="0",
        ),
        rx.cond(
            FoodState.sidebar_collapsed,
            rx.fragment(),
            rx.vstack(
                rx.text(FoodState.usuario_nombre, color="var(--twk-sb-tx-strong)",
                        font_weight="600", font_size="12px",
                        max_width="110px", overflow="hidden",
                        text_overflow="ellipsis", white_space="nowrap"),
                rx.text(FoodState.usuario_rol, color="var(--twk-sb-tx-dim)",
                        font_size="11px"),
                align="start",
                spacing="0",
            ),
        ),
        rx.cond(
            FoodState.sidebar_collapsed,
            rx.fragment(),
            rx.spacer(),
        ),
        rx.cond(
            FoodState.sidebar_collapsed,
            rx.fragment(),
            rx.icon_button(
                rx.icon(tag="log_out", size=13),
                on_click=FoodState.logout,
                background="rgba(220,38,38,0.15)",
                color="var(--twk-danger-text)",
                border="1px solid rgba(220,38,38,0.2)",
                border_radius="7px",
                width="30px",
                height="30px",
                _hover={"background": "rgba(220,38,38,0.28)", "color": "var(--twk-danger-text)"},
            ),
        ),
        spacing="2",
        align="center",
        width="100%",
    )


# ─── NAV ITEMS ────────────────────────────────────────────────────────────────────

_NAV_DESCRIPTIONS = {
    "Mozos":        "Mesas y comanda",
    "Caja":         "Cobro y tickets",
    "Mostrador":    "Takeaway rápido",
    "Cocina":       "KDS / Producción",
    "Impresión":    "Comandas a la térmica",
    "Carta":        "Carta y precios",
    "Reportes":     "Ventas del día",
    "Usuarios":     "Personal y PINs",
    "Configuración": "Impresoras y local",
}


def _desktop_nav_item(label: str, href: str, icon_tag: str,
                      active: bool) -> rx.Component:
    # T-08: la entrada "Impresión" refleja el modo activo (navegador imprime
    # comandas; el agente local solo se monitorea desde la estación).
    if label == "Impresión":
        desc = rx.cond(
            FoodState.config_modo_impresion == "navegador",
            "Comandas a la térmica",
            "Estado de impresión",
        )
    else:
        desc = _NAV_DESCRIPTIONS.get(label, "Módulo operativo")
    return rx.link(
        rx.box(
            rx.hstack(
                # Icon box
                rx.box(
                    rx.icon(
                        tag=icon_tag,
                        size=15,
                        color=rx.cond(active, "#FFFFFF", "var(--twk-sb-tx)"),
                    ),
                    class_name="twk-nav-icon-box",
                ),
                # Label + description
                rx.cond(
                    FoodState.sidebar_collapsed,
                    rx.fragment(),
                    rx.vstack(
                        rx.text(
                            label,
                            color=rx.cond(active, "#FFFFFF", "var(--twk-sb-tx-strong)"),
                            font_weight=rx.cond(active, "700", "500"),
                            font_size="13px",
                            line_height="1",
                        ),
                        rx.text(
                            desc,
                            color=rx.cond(active, "rgba(255,255,255,0.95)",
                                          "var(--twk-sb-tx-dim)"),
                            font_size="10.5px",
                            line_height="1",
                        ),
                        align="start",
                        spacing="1",
                    ),
                ),
                align="center",
                spacing="3",
                width="100%",
            ),
            width="100%",
            padding=rx.cond(FoodState.sidebar_collapsed, "8px", "8px 10px"),
            border_radius="10px",
            background=rx.cond(active, "#EA580C", "transparent"),
            box_shadow=rx.cond(active, "0 2px 10px rgba(234,88,12,0.35)", "none"),
            class_name=rx.cond(active, "twk-nav-item twk-nav-item-active", "twk-nav-item"),
        ),
        href=href,
        width="100%",
        text_decoration="none",
    )


def _mobile_nav_item(label: str, href: str, icon_tag: str,
                     active: bool) -> rx.Component:
    return rx.link(
        rx.box(
            rx.hstack(
                rx.icon(tag=icon_tag, size=17,
                        color=rx.cond(active, "#FFFFFF", TEXT_SECONDARY)),
                rx.text(label, color=rx.cond(active, "#FFFFFF", TEXT_SECONDARY),
                        font_weight="600", font_size="0.9rem"),
                width="100%",
                spacing="3",
                align="center",
            ),
            width="100%",
            padding="0.75rem 0.9rem",
            min_height="46px",
            border_radius="10px",
            style={"background": rx.cond(active, ACCENT, SURFACE_MUTED)},
        ),
        href=href,
        width="100%",
        text_decoration="none",
    )


def _nav_group_label(text: str, mobile: bool = False) -> rx.Component:
    """Encabezado de grupo del sidebar operativo. En desktop colapsado se
    reduce a una línea divisoria (sin texto) para no romper el layout angosto."""
    if mobile:
        return rx.text(
            text, font_size="10px", font_weight="700", color=TEXT_MUTED,
            text_transform="uppercase", letter_spacing="0.08em",
            padding_x="4px", padding_top="12px", padding_bottom="2px",
        )
    return rx.cond(
        FoodState.sidebar_collapsed,
        rx.box(height="1px", width="70%", margin="10px auto 4px",
               background="var(--twk-sb-divider)"),
        rx.text(
            text, font_size="10px", font_weight="700", color="var(--twk-sb-tx-faint)",
            text_transform="uppercase", letter_spacing="0.08em",
            padding_x="6px", padding_top="12px", padding_bottom="2px",
        ),
    )


def _nav_stack(active: str, mobile: bool = False) -> rx.Component:
    nav_item = _mobile_nav_item if mobile else _desktop_nav_item
    # Grupos coherentes: Servicio (operación en tiempo real), Catálogo y Gestión.
    # Cada encabezado solo aparece si el rol ve al menos un ítem del grupo, para
    # no dejar títulos huérfanos.
    grupo_servicio = (
        FoodState.puede_ver_mozos | FoodState.puede_ver_caja
        | FoodState.puede_ver_mostrador | FoodState.puede_ver_cocina
        | FoodState.puede_ver_estacion_impresion
    )
    grupo_gestion = (
        FoodState.puede_ver_reportes | FoodState.puede_ver_usuarios
        | FoodState.puede_ver_configuracion
    )
    return rx.vstack(
        # ── Servicio ──
        rx.cond(grupo_servicio, _nav_group_label("Servicio", mobile), rx.fragment()),
        rx.cond(FoodState.puede_ver_mozos,
                nav_item(_M["mozos"].label, "/mozos", _M["mozos"].icon, active == "mozos"),
                rx.fragment()),
        rx.cond(FoodState.puede_ver_caja,
                nav_item(_M["caja"].label, "/caja", _M["caja"].icon, active == "caja"),
                rx.fragment()),
        rx.cond(FoodState.puede_ver_mostrador,
                nav_item(_M["mostrador"].label, "/mostrador", _M["mostrador"].icon, active == "mostrador"),
                rx.fragment()),
        rx.cond(FoodState.puede_ver_cocina,
                nav_item(_M["cocina"].label, "/cocina", _M["cocina"].icon, active == "cocina"),
                rx.fragment()),
        rx.cond(FoodState.puede_ver_estacion_impresion,
                nav_item(_M["impresion"].label, "/estacion-impresion", _M["impresion"].icon,
                         active == "estacion_impresion"),
                rx.fragment()),
        # ── Catálogo ──
        rx.cond(FoodState.puede_ver_carta, _nav_group_label("Catálogo", mobile), rx.fragment()),
        rx.cond(FoodState.puede_ver_carta,
                nav_item(_M["carta"].label, "/carta", _M["carta"].icon, active == "carta"),
                rx.fragment()),
        # ── Gestión ──
        rx.cond(grupo_gestion, _nav_group_label("Gestión", mobile), rx.fragment()),
        rx.cond(FoodState.puede_ver_reportes,
                nav_item(_M["reportes"].label, "/reportes", _M["reportes"].icon, active == "reportes"),
                rx.fragment()),
        rx.cond(FoodState.puede_ver_usuarios,
                nav_item(_M["usuarios"].label, "/usuarios", _M["usuarios"].icon, active == "usuarios"),
                rx.fragment()),
        rx.cond(FoodState.puede_ver_configuracion,
                nav_item(_M["config"].label, "/configuracion", _M["config"].icon,
                         active == "configuracion"),
                rx.fragment()),
        width="100%",
        spacing="1",
        align="stretch",
    )


# ─── SIDEBAR DESKTOP (dark navy) ──────────────────────────────────────────────────

def _desktop_sidebar(active: str) -> rx.Component:
    return rx.box(
        rx.vstack(
            # ── Brand ─────────────────────────────────────────────────────────
            rx.hstack(
                rx.cond(
                    FoodState.sidebar_collapsed,
                    rx.image(src="/TUWAYKIFOODFAVICON.png", width="34px", height="34px",
                             border_radius="9px", alt="TUWAYKIFOOD"),
                    _brand(compact=False, dark=True),
                ),
                rx.hstack(
                    rx.cond(
                        FoodState.sidebar_collapsed,
                        rx.fragment(),
                        color_mode_toggle(on_sidebar=True, size=28),
                    ),
                    rx.tooltip(
                        rx.icon_button(
                            rx.icon(
                                tag=rx.cond(FoodState.sidebar_collapsed, "panel_left_open", "panel_left_close"),
                                size=14,
                            ),
                            on_click=FoodState.toggle_sidebar,
                            background=SIDEBAR_HOVER_BG,
                            color=SIDEBAR_TEXT,
                            border="none",
                            border_radius="7px",
                            width="28px",
                            height="28px",
                            flex_shrink="0",
                            _hover={"background": SURFACE_HOVER, "color": SIDEBAR_TEXT_ACTIVE},
                        ),
                        content=rx.cond(FoodState.sidebar_collapsed, "Expandir menú", "Contraer menú"),
                    ),
                    spacing="2",
                    align="center",
                    flex_shrink="0",
                ),
                width="100%",
                justify="between",
                align="center",
            ),
            # ── Separador ─────────────────────────────────────────────────────
            rx.box(height="1px", width="100%",
                   background="var(--twk-sb-divider)"),
            # ── Navegacion ────────────────────────────────────────────────────
            rx.box(
                _nav_stack(active, mobile=False),
                width="100%",
                flex="1",
                overflow_y="auto",
            ),
            # ── Volver al Panel Administrativo (solo Admin) ──────────────────
            rx.cond(
                FoodState.puede_ver_panel_admin,
                rx.link(
                    rx.hstack(
                        rx.icon(tag="arrow_left", size=13, color="var(--twk-sb-tx-dim)"),
                        rx.cond(
                            FoodState.sidebar_collapsed,
                            rx.fragment(),
                            rx.vstack(
                                rx.text("Panel Administrativo", font_size="12px",
                                        color="var(--twk-sb-tx-dim)", font_weight="600",
                                        line_height="1.1"),
                                rx.text("Reportes del dueño, inventario y más",
                                        font_size="10px", color="var(--twk-sb-tx-faint)",
                                        line_height="1.1"),
                                spacing="1", align="start",
                            ),
                        ),
                        spacing="2", align="center",
                    ),
                    href="/admin",
                    width="100%",
                    padding="8px 10px",
                    border_radius="8px",
                    text_decoration="none",
                    _hover={"background": "var(--twk-sb-hover)"},
                ),
                rx.fragment(),
            ),
            # ── Info LAN ──────────────────────────────────────────────────────
            rx.cond(
                FoodState.sidebar_collapsed,
                rx.fragment(),
                rx.box(
                    rx.vstack(
                        rx.text("Operacion en LAN", color="var(--twk-sb-tx-dim)",
                                font_size="10.5px", font_weight="700",
                                letter_spacing="0.04em", text_transform="uppercase"),
                        rx.text("Optimizado para tablets, caja y cocina.",
                                color="var(--twk-sb-tx-faint)", font_size="10px"),
                        align="start",
                        spacing="1",
                    ),
                    width="100%",
                    padding="8px 10px",
                    border_radius="8px",
                    background="var(--twk-sb-soft)",
                    border="1px solid var(--twk-sb-divider)",
                ),
            ),
            # ── Separador ─────────────────────────────────────────────────────
            rx.box(height="1px", width="100%",
                   background="var(--twk-sb-divider)"),
            # ── Usuario ───────────────────────────────────────────────────────
            _sidebar_user_badge(),
            # ── Sucursal (solo si multi-local) ────────────────────────────────
            rx.cond(
                FoodState.tiene_sucursales,
                rx.hstack(
                    rx.icon(tag="map_pin", size=12, color="#EA580C"),
                    rx.cond(
                        FoodState.sidebar_collapsed,
                        rx.fragment(),
                        rx.text(
                            FoodState.sucursal_actual_nombre,
                            font_size="11px", color="var(--twk-sb-tx-dim)",
                            max_width="130px", overflow="hidden",
                            text_overflow="ellipsis", white_space="nowrap",
                        ),
                    ),
                    spacing="2", align="center", padding_x="4px",
                ),
                rx.fragment(),
            ),
            spacing="0",
            gap="8px",
            height="100%",
            width="100%",
            align="start",
        ),
        width=rx.cond(FoodState.sidebar_collapsed, "64px", "236px"),
        min_width=rx.cond(FoodState.sidebar_collapsed, "64px", "236px"),
        height="100vh",
        position="sticky",
        top="0",
        padding="14px 10px",
        background=SIDEBAR_BG,
        border_right=f"1px solid {SIDEBAR_BORDER}",
        display=rx.breakpoints(initial="none", lg="flex"),
        flex_direction="column",
        flex_shrink="0",
        overflow_y="auto",
        overflow_x="hidden",
    )


# ─── DRAWER MÓVIL ─────────────────────────────────────────────────────────────────

def _mobile_nav_drawer(active: str) -> rx.Component:
    return rx.box(
        rx.drawer.root(
            rx.drawer.trigger(
                rx.icon_button(
                    rx.icon(tag="menu", size=18),
                    background=SURFACE_MUTED,
                    color=TEXT_SECONDARY,
                    border=f"1px solid {BORDER_COLOR}",
                    border_radius="9px",
                    width="38px",
                    height="38px",
                    _hover={"background": SURFACE_HOVER},
                )
            ),
            rx.drawer.portal(
                rx.drawer.overlay(background="rgba(15,23,42,0.5)"),
                rx.drawer.content(
                    rx.box(
                        rx.vstack(
                            rx.hstack(
                                _brand(compact=False, dark=False),
                                rx.hstack(
                                    color_mode_toggle(on_sidebar=False, size=34),
                                    rx.drawer.close(
                                        rx.icon_button(
                                            rx.icon(tag="x", size=16),
                                            background=SURFACE_MUTED,
                                            color=TEXT_SECONDARY,
                                            border=f"1px solid {BORDER_COLOR}",
                                            border_radius="8px",
                                        )
                                    ),
                                    spacing="2",
                                    align="center",
                                ),
                                width="100%",
                                justify="between",
                                align="center",
                            ),
                            rx.box(height="1px", width="100%",
                                   background=BORDER_COLOR),
                            _nav_stack(active, mobile=True),
                            rx.cond(
                                FoodState.puede_ver_panel_admin,
                                rx.link(
                                    rx.hstack(
                                        rx.icon(tag="arrow_left", size=14, color=TEXT_SECONDARY),
                                        rx.text("Panel Administrativo", font_size="13px",
                                                color=TEXT_SECONDARY, font_weight="600"),
                                        spacing="2", align="center",
                                    ),
                                    href="/admin",
                                    width="100%",
                                    padding="0.6rem 0.9rem",
                                    border_radius="8px",
                                    text_decoration="none",
                                    _hover={"background": SURFACE_HOVER},
                                ),
                                rx.fragment(),
                            ),
                            rx.box(height="1px", width="100%",
                                   background=BORDER_COLOR),
                            user_session_badge(),
                            width="100%",
                            align="start",
                            spacing="4",
                        ),
                        width="290px",
                        max_width="88vw",
                        height="100%",
                        padding="1rem",
                        background=SURFACE_ELEVATED,
                    ),
                    justify_content="flex-start",
                ),
            ),
            direction="left",
        ),
        display=rx.breakpoints(initial="block", lg="none"),
    )


# ─── PAGE HEADER ──────────────────────────────────────────────────────────────────

def _page_header(active: str, title: str, subtitle: str,
                 action=None) -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.hstack(
                _mobile_nav_drawer(active),
                rx.vstack(
                    rx.text("TUWAYKIFOOD", color=ACCENT, font_size="10px",
                            font_weight="800", letter_spacing="0.14em",
                            text_transform="uppercase"),
                    rx.heading(title, size=rx.breakpoints(initial="5", md="6"),
                               color=TEXT_PRIMARY, line_height="1.1"),
                    align="start",
                    spacing="0",
                ),
                spacing="3",
                align="center",
                flex="1",
                min_width="0",
            ),
            rx.hstack(
                action if action is not None else rx.fragment(),
                rx.cond(
                    FoodState.autenticado,
                    rx.box(user_session_badge(),
                           display=rx.breakpoints(initial="none", lg="block")),
                    rx.fragment(),
                ),
                spacing="3",
                align="center",
                flex_shrink="0",
            ),
            width="100%",
            justify="between",
            align="center",
            gap="12px",
        ),
        rx.cond(
            subtitle != "",
            rx.text(subtitle, color=TEXT_MUTED, font_size="13px",
                    display=rx.breakpoints(initial="none", md="block"),
                    margin_top="4px"),
            rx.fragment(),
        ),
        padding=rx.breakpoints(initial="12px 16px", md="16px 20px"),
        background=SURFACE_ELEVATED,
        border_bottom=f"1px solid {BORDER_COLOR}",
        width="100%",
        position="sticky",
        top="0",
        z_index="50",
        box_shadow="0 1px 3px rgba(0,0,0,0.04)",
    )


# ─── TOPBAR MÓVIL ─────────────────────────────────────────────────────────────────

def _mobile_topbar(active: str) -> rx.Component:
    return rx.box(
        rx.hstack(
            _mobile_nav_drawer(active),
            _brand(compact=False, dark=False),
            rx.spacer(),
            color_mode_toggle(on_sidebar=False, size=36),
            spacing="3",
            align="center",
            width="100%",
        ),
        display=rx.breakpoints(initial="flex", lg="none"),
        padding="10px 14px",
        class_name="twk-safe-top",  # respeta el notch/isla en PWA iOS (D-07)
        border_bottom=f"1px solid {BORDER_COLOR}",
        background=SURFACE_ELEVATED,
        width="100%",
        position="sticky",
        top="0",
        z_index="200",
        box_shadow="0 1px 4px rgba(0,0,0,0.05)",
        align_items="center",
    )


# ─── Aviso de cumpleaños (uso en Mozos/Caja/Mostrador) ─────────────────────────────

def cumpleanos_banner() -> rx.Component:
    """Aviso informativo de clientes que cumplen años hoy, para que el staff
    pueda reconocerlos y ofrecer una cortesía. No está atado a un pedido
    puntual — hoy los pedidos normales no se vinculan a un cliente registrado
    (solo el pago fiado en Caja lo hace)."""
    return rx.cond(
        FoodState.clientes_cumpleanos_hoy.length() > 0,
        rx.box(
            rx.hstack(
                rx.text("🎂", font_size="16px", line_height="1"),
                rx.text("Hoy cumplen años:", font_size="12px", font_weight="700",
                        color=DANGER_TEXT, flex_shrink="0"),
                rx.foreach(
                    FoodState.clientes_cumpleanos_hoy,
                    lambda c: rx.badge(
                        c.nombre,
                        background=SURFACE_BASE, color=DANGER_TEXT,
                        border="1px solid rgba(239,68,68,0.25)", border_radius="6px",
                        font_size="11px", font_weight="600",
                    ),
                ),
                spacing="2", align="center", wrap="wrap",
            ),
            background="rgba(239,68,68,0.10)", border="1px solid rgba(239,68,68,0.25)",
            border_radius="10px", padding="10px 14px", width="100%",
        ),
        rx.fragment(),
    )


# ─── SKELETON DE CARGA ────────────────────────────────────────────────────────

def loading_placeholder(*, dark: bool = False) -> rx.Component:
    # `dark` se mantiene por compatibilidad con las llamadas existentes; el
    # spinner y el texto gris funcionan igual en ambos temas.
    return rx.center(
        rx.vstack(
            rx.spinner(size="3", color="#EA580C"),
            rx.text("Cargando…", font_size="13px", color=TEXT_MUTED, font_weight="500"),
            spacing="3",
            align="center",
        ),
        width="100%",
        padding_y="60px",
    )


# ─── APP SHELL ────────────────────────────────────────────────────────────────────

def _connection_banner_es() -> rx.Component:
    return rx.connection_banner(
        comp=rx.el.div(
            rx.el.span(
                "⚠ Sin conexión con el servidor — reintentando…",
                color="white",
                font_size="14px",
                font_weight="600",
            ),
            display="flex",
            justify_content="center",
            align_items="center",
            gap="8px",
            background_color="#DC2626",
            width="100vw",
            padding="8px 16px",
            position="fixed",
            top="0",
            left="0",
            z_index="9999",
        ),
    )


def app_shell(
    content: rx.Component,
    *,
    page_key: str = "",
    active: str = "",
    dark: bool = False,
) -> rx.Component:
    _active = page_key or active
    _bg = PAGE_BACKGROUND
    _text = TEXT_PRIMARY
    return rx.box(
        _connection_banner_es(),
        rx.hstack(
            _desktop_sidebar(_active),
            rx.box(
                _mobile_topbar(_active),
                rx.box(
                    rx.vstack(
                        content,
                        width="100%",
                        align="start",
                        spacing="5",
                    ),
                    padding=rx.breakpoints(initial="16px", md="20px 24px", xl="24px 32px"),
                    width="100%",
                ),
                width="100%",
                min_height="100vh",
                overflow_x="hidden",
            ),
            width="100%",
            align="start",
            gap="0",
        ),
        min_height="100vh",
        width="100%",
        background=_bg,
        color=_text,
        class_name="dark" if dark else "",
    )


# ─── Modal de anulación auditada (compartido por Caja y Reportes) ─────────────

def anulacion_modal() -> rx.Component:
    """Modal de anulación con motivo obligatorio. La anulación nunca borra el
    pedido: queda CANCELADO con motivo, usuario y hora."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.hstack(
                    rx.icon(tag="triangle_alert", size=18, color="#DC2626"),
                    rx.text("Anular " + FoodState.anulacion_referencia,
                            font_size="17px", font_weight="800", color=DARK_MODAL_TEXT),
                    spacing="2", align="center",
                ),
                rx.text(
                    rx.cond(
                        FoodState.anulacion_es_venta,
                        "Se repondrá el stock de insumos, se revertirá el fiado si lo hubo "
                        "y la venta saldrá del arqueo del turno. La operación queda registrada.",
                        "El pedido se cancelará y la mesa quedará libre. La operación queda registrada.",
                    ),
                    font_size="13px", color=DARK_MODAL_MUTED,
                ),
                rx.input(
                    placeholder="Motivo de la anulación (obligatorio)",
                    value=FoodState.anulacion_motivo,
                    on_change=FoodState.set_anulacion_motivo,
                    width="100%",
                    background=DARK_MODAL_INPUT_BG, border=f"1px solid {DARK_MODAL_INPUT_BORDER}",
                    color=DARK_MODAL_TEXT,
                    border_radius="8px", font_size="13px",
                    _focus={"border_color": "#DC2626"},
                ),
                rx.cond(
                    FoodState.anulacion_error != "",
                    rx.text(FoodState.anulacion_error, font_size="12px",
                            color="#EF4444", font_weight="600"),
                    rx.fragment(),
                ),
                rx.hstack(
                    rx.button(
                        "Volver",
                        on_click=FoodState.cancelar_anulacion,
                        background=DARK_MODAL_BTN_BG, color=DARK_MODAL_MUTED,
                        border=f"1px solid {DARK_MODAL_BTN_BORDER}", border_radius="10px",
                        font_size="14px", font_weight="600", cursor="pointer",
                        _hover={"background": DARK_700, "color": DARK_MODAL_TEXT}, flex="1",
                    ),
                    rx.button(
                        "Confirmar anulación",
                        on_click=FoodState.confirmar_anulacion,
                        background="#DC2626", color="#FFFFFF",
                        border_radius="10px", font_size="14px", font_weight="800",
                        cursor="pointer", _hover={"background": "#B91C1C"}, flex="2",
                    ),
                    spacing="3", width="100%",
                ),
                spacing="3", width="100%",
            ),
            max_width="440px",
            **DARK_MODAL_PROPS,
        ),
        open=FoodState.anulacion_modal_visible,
        on_open_change=FoodState.set_anulacion_modal_visible,
    )
