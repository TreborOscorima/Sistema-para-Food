"""Componentes compartidos y shell visual de TUWAYKIFOOD POS."""

from __future__ import annotations

import reflex as rx

from app.states.food_state import FoodState


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
                rx.text(FoodState.usuario_nombre, color="rgba(255,255,255,0.88)",
                        font_weight="600", font_size="12px",
                        max_width="110px", overflow="hidden",
                        text_overflow="ellipsis", white_space="nowrap"),
                rx.text(FoodState.usuario_rol, color="rgba(255,255,255,0.42)",
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
                color="#FCA5A5",
                border="1px solid rgba(220,38,38,0.2)",
                border_radius="7px",
                width="30px",
                height="30px",
                _hover={"background": "rgba(220,38,38,0.28)", "color": "#FCA5A5"},
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
    desc = _NAV_DESCRIPTIONS.get(label, "Módulo operativo")
    return rx.link(
        rx.box(
            rx.hstack(
                # Icon box
                rx.box(
                    rx.icon(
                        tag=icon_tag,
                        size=15,
                        color=rx.cond(active, "#FFFFFF", "rgba(255,255,255,0.80)"),
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
                            color=rx.cond(active, "#FFFFFF", "rgba(255,255,255,0.92)"),
                            font_weight=rx.cond(active, "700", "500"),
                            font_size="13px",
                            line_height="1",
                        ),
                        rx.text(
                            desc,
                            color=rx.cond(active, "rgba(255,255,255,0.85)",
                                          "rgba(255,255,255,0.55)"),
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


def _nav_stack(active: str, mobile: bool = False) -> rx.Component:
    nav_item = _mobile_nav_item if mobile else _desktop_nav_item
    return rx.vstack(
        rx.cond(FoodState.puede_ver_mozos,
                nav_item("Mozos", "/mozos", "layout_grid", active == "mozos"),
                rx.fragment()),
        rx.cond(FoodState.puede_ver_caja,
                nav_item("Caja", "/caja", "wallet", active == "caja"),
                rx.fragment()),
        rx.cond(FoodState.puede_ver_mostrador,
                nav_item("Mostrador", "/mostrador", "shopping_bag", active == "mostrador"),
                rx.fragment()),
        rx.cond(FoodState.puede_ver_cocina,
                nav_item("Cocina", "/cocina", "chef_hat", active == "cocina"),
                rx.fragment()),
        rx.cond(FoodState.puede_ver_estacion_impresion,
                nav_item("Impresión", "/estacion-impresion", "printer",
                         active == "estacion_impresion"),
                rx.fragment()),
        rx.cond(FoodState.puede_ver_carta,
                nav_item("Carta", "/carta", "book_open", active == "carta"),
                rx.fragment()),
        rx.cond(FoodState.puede_ver_reportes,
                nav_item("Reportes", "/reportes", "receipt_text", active == "reportes"),
                rx.fragment()),
        rx.cond(FoodState.puede_ver_usuarios,
                nav_item("Usuarios", "/usuarios", "users", active == "usuarios"),
                rx.fragment()),
        rx.cond(FoodState.puede_ver_configuracion,
                nav_item("Configuración", "/configuracion", "settings",
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
                rx.icon_button(
                    rx.icon(
                        tag=rx.cond(FoodState.sidebar_collapsed, "panel_left_open", "panel_left_close"),
                        size=14,
                    ),
                    on_click=FoodState.toggle_sidebar,
                    background="rgba(255,255,255,0.07)",
                    color="rgba(255,255,255,0.45)",
                    border="none",
                    border_radius="7px",
                    width="28px",
                    height="28px",
                    flex_shrink="0",
                    _hover={"background": "rgba(255,255,255,0.12)", "color": "#fff"},
                ),
                width="100%",
                justify="between",
                align="center",
            ),
            # ── Separador ─────────────────────────────────────────────────────
            rx.box(height="1px", width="100%",
                   background="rgba(255,255,255,0.07)"),
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
                        rx.icon(tag="arrow_left", size=13, color="rgba(255,255,255,0.6)"),
                        rx.cond(
                            FoodState.sidebar_collapsed,
                            rx.fragment(),
                            rx.text("Panel Administrativo", font_size="12px",
                                    color="rgba(255,255,255,0.6)", font_weight="600"),
                        ),
                        spacing="2", align="center",
                    ),
                    href="/admin",
                    width="100%",
                    padding="8px 10px",
                    border_radius="8px",
                    text_decoration="none",
                    _hover={"background": "rgba(255,255,255,0.06)"},
                ),
                rx.fragment(),
            ),
            # ── Info LAN ──────────────────────────────────────────────────────
            rx.cond(
                FoodState.sidebar_collapsed,
                rx.fragment(),
                rx.box(
                    rx.vstack(
                        rx.text("Operacion en LAN", color="rgba(255,255,255,0.45)",
                                font_size="10.5px", font_weight="700",
                                letter_spacing="0.04em", text_transform="uppercase"),
                        rx.text("Optimizado para tablets, caja y cocina.",
                                color="rgba(255,255,255,0.28)", font_size="10px"),
                        align="start",
                        spacing="1",
                    ),
                    width="100%",
                    padding="8px 10px",
                    border_radius="8px",
                    background="rgba(255,255,255,0.04)",
                    border="1px solid rgba(255,255,255,0.06)",
                ),
            ),
            # ── Separador ─────────────────────────────────────────────────────
            rx.box(height="1px", width="100%",
                   background="rgba(255,255,255,0.07)"),
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
                            font_size="11px", color="rgba(255,255,255,0.6)",
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
        background="#0F172A",
        border_right="1px solid #1E293B",
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
                                rx.drawer.close(
                                    rx.icon_button(
                                        rx.icon(tag="x", size=16),
                                        background=SURFACE_MUTED,
                                        color=TEXT_SECONDARY,
                                        border=f"1px solid {BORDER_COLOR}",
                                        border_radius="8px",
                                    )
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
            spacing="3",
            align="center",
            width="100%",
        ),
        display=rx.breakpoints(initial="flex", lg="none"),
        padding="10px 14px",
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
                        color="#991B1B", flex_shrink="0"),
                rx.foreach(
                    FoodState.clientes_cumpleanos_hoy,
                    lambda c: rx.badge(
                        c.nombre,
                        background="#1E293B", color="#F87171",
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
            rx.text("Cargando…", font_size="13px", color="#94A3B8", font_weight="500"),
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
