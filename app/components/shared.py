"""Componentes compartidos y shell visual de TUWAYKIFOOD POS."""

from __future__ import annotations

import json
import reflex as rx

from app.states.food_state import FoodState

# CSS global inyectado via script en el body porque:
# - assets/ está bakeado en la imagen Docker (no es volumen)
# - rx.el.style() en head_components pasa por Emotion y scopea TODO como
#   .css-XXXX .twk-panel, donde .css-XXXX es el <style> tag mismo, nunca
#   un ancestro del body → las reglas no matchean nada en el DOM.
# - rx.script() en head_components no ejecuta (React no ejecuta <script>
#   creados vía virtual DOM).
# Solución: rx.script() en el body sí ejecuta (usado también para redirects).
# El IIFE guarda con id='twk-css' para no duplicar en navegación SPA.
_TWK_CSS = (
    "input::placeholder,textarea::placeholder{color:#94A3B8!important;opacity:1!important}"
    "html{scroll-behavior:smooth}"
    "*{-webkit-tap-highlight-color:rgba(234,88,12,0.12)}"
    "@media(max-width:1023px){"
    "input[type=text],input[type=number],input[type=email],"
    "input[type=password],input[type=search],input[type=tel],"
    "input[type=url],input[type=date],textarea,select{font-size:16px!important}}"
    ".twk-cols-lg,.twk-cols-md{display:flex!important;flex-wrap:wrap!important;gap:20px;width:100%;align-items:flex-start}"
    ".twk-panel{flex:0 0 100%!important;min-width:0!important;box-sizing:border-box}"
    "@media(min-width:1024px){.twk-cols-lg{flex-wrap:nowrap!important}.twk-cols-lg .twk-panel{flex:1 1 0!important}}"
    "@media(min-width:768px){.twk-cols-md{flex-wrap:nowrap!important}.twk-cols-md .twk-panel{flex:1 1 0!important}}"
    ".twk-sep{display:none!important}"
    "@media(min-width:1024px){.twk-cols-lg .twk-sep{display:block!important;flex:0 0 auto!important}}"
    "@media(min-width:768px){.twk-cols-md .twk-sep{display:block!important;flex:0 0 auto!important}}"
    ".twk-form-row{display:flex!important;flex-direction:column!important;gap:12px;width:100%}"
    "@media(min-width:768px){.twk-form-row{flex-direction:row!important;gap:12px}.twk-form-row>*{flex:1!important;min-width:0!important}}"
    ".twk-form-row>*{width:100%}"
    ".twk-field-row{display:flex!important;flex-direction:column!important;gap:6px;width:100%;align-items:flex-start}"
    "@media(min-width:640px){.twk-field-row{flex-direction:row!important;align-items:center!important}"
    ".twk-field-row>*:first-child{flex:0 0 140px!important;min-width:0}"
    ".twk-field-row>*:last-child{flex:1!important;min-width:0}}"
    "::-webkit-scrollbar{width:6px;height:6px}"
    "::-webkit-scrollbar-track{background:#F1F5F9}"
    "::-webkit-scrollbar-thumb{background:#CBD5E1;border-radius:3px}"
    "::-webkit-scrollbar-thumb:hover{background:#94A3B8}"
    "[data-radix-select-viewport]{font-size:15px!important}"
)

_CSS_SCRIPT = f"(function(){{if(document.getElementById('twk-css'))return;var s=document.createElement('style');s.id='twk-css';s.textContent={json.dumps(_TWK_CSS)};document.head.appendChild(s);}})();"


# ── Paleta light (misma escala que Sistema de Ventas, acento naranja para food) ─
PAGE_BACKGROUND = "#F8FAFC"

SURFACE_BASE = "#FFFFFF"
SURFACE_ELEVATED = "#FFFFFF"
SURFACE_SOFT = "#F8FAFC"
SURFACE_MUTED = "#F1F5F9"
SURFACE_GHOST = "#F8FAFC"
SURFACE_HOVER = "#F1F5F9"
SURFACE_INTERACTIVE = "#FFF7ED"

BORDER_COLOR = "#E2E8F0"
BORDER_STRONG = "#CBD5E1"
BORDER_ACCENT = "#FED7AA"

TEXT_PRIMARY = "#0F172A"
TEXT_SECONDARY = "#334155"
TEXT_MUTED = "#64748B"

ACCENT = "#EA580C"
ACCENT_HOVER = "#C2410C"
ACCENT_BG = "#FFF7ED"
ACCENT_TEXT = "#9A3412"
ACCENT_SOFT = "#FFF7ED"

SUCCESS_BG = "#F0FDF4"
SUCCESS_TEXT = "#15803D"
SUCCESS_BORDER = "#BBF7D0"

DANGER_BG = "#FEF2F2"
DANGER_TEXT = "#B91C1C"
DANGER_BORDER = "#FECACA"

WARNING_BG = "#FFFBEB"
WARNING_TEXT = "#B45309"
WARNING_BORDER = "#FDE68A"

INFO_BG = "#EFF6FF"
INFO_TEXT = "#1D4ED8"
INFO_BORDER = "#BFDBFE"

GLOW = "0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.04)"
SOFT_GLOW = "0 1px 2px rgba(0,0,0,0.05)"
ACCENT_GLOW = "0 1px 3px rgba(234,88,12,0.12)"


def surface_card(*children, **props) -> rx.Component:
    bg = props.pop("background", SURFACE_BASE)
    border = props.pop("border", f"1px solid {BORDER_COLOR}")
    border_radius = props.pop("border_radius", "12px")
    box_shadow = props.pop("box_shadow", GLOW)
    width = props.pop("width", "100%")
    incoming_style = props.pop("style", {})
    final_style = {
        "background": bg,
        "border": border,
        "border_radius": border_radius,
        "box_shadow": box_shadow,
        **incoming_style,
    }
    return rx.box(*children, style=final_style, width=width, **props)


def section_card(*children, **props) -> rx.Component:
    bg = props.pop("background", SURFACE_SOFT)
    border = props.pop("border", f"1px solid {BORDER_COLOR}")
    border_radius = props.pop("border_radius", "10px")
    box_shadow = props.pop("box_shadow", SOFT_GLOW)
    width = props.pop("width", "100%")
    incoming_style = props.pop("style", {})
    final_style = {
        "background": bg,
        "border": border,
        "border_radius": border_radius,
        "box_shadow": box_shadow,
        **incoming_style,
    }
    return rx.box(*children, style=final_style, width=width, **props)


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
        border_radius="8px",
        height="40px",
        padding_x="1rem",
        _hover={"background": ACCENT_HOVER},
    )


def status_banner(message) -> rx.Component:
    return section_card(
        rx.hstack(
            rx.box(
                width="8px",
                height="8px",
                border_radius="999px",
                style={"background": ACCENT},
            ),
            rx.text(message, color=TEXT_SECONDARY, font_weight="600", font_size="0.9rem"),
            spacing="3",
            align="center",
        ),
        padding="0.75rem 1rem",
    )


def kpi_card(title: str, value, description: str = "", accent_color: str = ACCENT) -> rx.Component:
    return surface_card(
        rx.vstack(
            rx.text(
                title,
                color=TEXT_MUTED,
                font_size="0.75rem",
                font_weight="700",
                letter_spacing="0.08em",
                text_transform="uppercase",
            ),
            rx.text(
                value,
                color=TEXT_PRIMARY,
                font_weight="800",
                font_size="1.75rem",
                line_height="1.1",
            ),
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


def _brand(compact: bool = False) -> rx.Component:
    return rx.hstack(
        rx.box(
            rx.icon(tag="utensils", size=18, color="#FFFFFF"),
            width="38px",
            height="38px",
            border_radius="10px",
            style={"background": "linear-gradient(135deg, #EA580C 0%, #C2410C 100%)"},
            display="flex",
            align_items="center",
            justify_content="center",
            box_shadow=ACCENT_GLOW,
            flex_shrink="0",
        ),
        rx.cond(
            compact,
            rx.fragment(),
            rx.vstack(
                rx.text(
                    "TUWAYKIFOOD",
                    color=TEXT_PRIMARY,
                    font_weight="800",
                    letter_spacing="0.08em",
                    font_size="0.78rem",
                    text_transform="uppercase",
                ),
                rx.text("Sistema para restaurantes", color=TEXT_MUTED, font_size="0.78rem"),
                align="start",
                spacing="0",
            ),
        ),
        spacing="3",
        align="center",
    )


def _user_summary() -> rx.Component:
    return rx.hstack(
        rx.box(
            rx.icon(tag="user_round", size=16, color="#FFFFFF"),
            width="36px",
            height="36px",
            border_radius="full",
            style={"background": "linear-gradient(135deg, #EA580C 0%, #C2410C 100%)"},
            display="flex",
            align_items="center",
            justify_content="center",
            flex_shrink="0",
        ),
        rx.vstack(
            rx.text(
                FoodState.usuario_nombre,
                color=TEXT_PRIMARY,
                font_weight="700",
                font_size="0.875rem",
                max_width="180px",
                text_overflow="ellipsis",
                overflow="hidden",
                white_space="nowrap",
            ),
            rx.text(
                FoodState.usuario_rol,
                color=ACCENT,
                font_weight="500",
                font_size="0.72rem",
                background=ACCENT_BG,
                padding_x="0.4rem",
                padding_y="0.1rem",
                border_radius="full",
                display="inline-block",
            ),
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
                rx.icon(tag="log_out", size=15),
                rx.text("Salir", font_weight="600", font_size="0.84rem"),
                spacing="1",
                align="center",
            ),
            on_click=FoodState.logout,
            background=DANGER_BG,
            color=DANGER_TEXT,
            border=f"1px solid {DANGER_BORDER}",
            border_radius="8px",
            height="36px",
            padding_x="0.75rem",
            _hover={"background": "#FEE2E2"},
        ),
        spacing="3",
        align="center",
    )


_NAV_DESCRIPTIONS = {
    "Mozos": "Mesas y comanda",
    "Caja": "Cobro y tickets",
    "Mostrador": "Takeaway rapido",
    "Cocina": "KDS / Produccion",
    "Carta": "Carta y precios",
    "Reportes": "Ventas del dia",
    "Usuarios": "Personal y PINs",
    "Configuracion": "Impresoras y local",
}


def _desktop_nav_item(label: str, href: str, icon_tag: str, active: bool) -> rx.Component:
    description = _NAV_DESCRIPTIONS.get(label, "Modulo operativo")
    return rx.link(
        rx.box(
            rx.hstack(
                rx.icon(
                    tag=icon_tag,
                    size=17,
                    color=rx.cond(active, "#FFFFFF", TEXT_MUTED),
                    flex_shrink="0",
                ),
                rx.cond(
                    FoodState.sidebar_collapsed,
                    rx.fragment(),
                    rx.vstack(
                        rx.text(
                            label,
                            color=rx.cond(active, "#FFFFFF", TEXT_SECONDARY),
                            font_weight="600",
                            font_size="0.875rem",
                        ),
                        rx.text(description, color=rx.cond(active, "rgba(255,255,255,0.70)", TEXT_MUTED), font_size="0.72rem"),
                        align="start",
                        spacing="0",
                    ),
                ),
                width="100%",
                align="center",
                spacing="3",
            ),
            width="100%",
            padding=rx.cond(FoodState.sidebar_collapsed, "0.6rem", "0.6rem 0.75rem"),
            border_radius="10px",
            style={
                "background": rx.cond(active, ACCENT, "transparent"),
                "box_shadow": rx.cond(active, "0 1px 3px rgba(234,88,12,0.25)", "none"),
            },
            _hover={
                "background": rx.cond(active, ACCENT_HOVER, SURFACE_MUTED),
            },
        ),
        href=href,
        width="100%",
        text_decoration="none",
    )


def _mobile_nav_item(label: str, href: str, icon_tag: str, active: bool) -> rx.Component:
    return rx.link(
        rx.box(
            rx.hstack(
                rx.icon(
                    tag=icon_tag,
                    size=17,
                    color=rx.cond(active, "#FFFFFF", TEXT_SECONDARY),
                ),
                rx.text(
                    label,
                    color=rx.cond(active, "#FFFFFF", TEXT_SECONDARY),
                    font_weight="600",
                    font_size="0.9rem",
                ),
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
        rx.cond(
            FoodState.puede_ver_mozos,
            nav_item("Mozos", "/mozos", "layout_grid", active == "mozos"),
            rx.fragment(),
        ),
        rx.cond(
            FoodState.puede_ver_caja,
            nav_item("Caja", "/caja", "wallet", active == "caja"),
            rx.fragment(),
        ),
        rx.cond(
            FoodState.puede_ver_mostrador,
            nav_item("Mostrador", "/mostrador", "shopping_bag", active == "mostrador"),
            rx.fragment(),
        ),
        rx.cond(
            FoodState.puede_ver_cocina,
            nav_item("Cocina", "/cocina", "chef_hat", active == "cocina"),
            rx.fragment(),
        ),
        rx.cond(
            FoodState.puede_ver_carta,
            nav_item("Carta", "/carta", "book_open", active == "carta"),
            rx.fragment(),
        ),
        rx.cond(
            FoodState.puede_ver_reportes,
            nav_item("Reportes", "/reportes", "receipt_text", active == "reportes"),
            rx.fragment(),
        ),
        rx.cond(
            FoodState.puede_ver_usuarios,
            nav_item("Usuarios", "/usuarios", "users", active == "usuarios"),
            rx.fragment(),
        ),
        rx.cond(
            FoodState.puede_ver_configuracion,
            nav_item("Configuracion", "/configuracion", "settings", active == "configuracion"),
            rx.fragment(),
        ),
        width="100%",
        spacing="1",
        align="stretch",
    )


def _desktop_sidebar(active: str) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.cond(FoodState.sidebar_collapsed, _brand(compact=True), _brand(compact=False)),
                rx.cond(
                    FoodState.sidebar_collapsed,
                    rx.fragment(),
                    rx.icon_button(
                        rx.icon(tag="panel_left_close", size=16),
                        on_click=FoodState.toggle_sidebar,
                        background="transparent",
                        color=TEXT_MUTED,
                        border="none",
                        border_radius="8px",
                        _hover={"background": SURFACE_MUTED, "color": TEXT_SECONDARY},
                    ),
                ),
                width="100%",
                justify="between",
                align="center",
                padding_x="0.25rem",
                padding_y="0.5rem",
                min_height="56px",
            ),
            rx.box(
                height="1px",
                width="100%",
                background="linear-gradient(to right, transparent, #E2E8F0, transparent)",
            ),
            rx.box(
                _nav_stack(active, mobile=False),
                width="100%",
                padding_top="0.5rem",
            ),
            rx.spacer(),
            rx.cond(
                FoodState.sidebar_collapsed,
                rx.fragment(),
                rx.box(
                    rx.vstack(
                        rx.text("Operacion en LAN", color=TEXT_SECONDARY, font_weight="600", font_size="0.8rem"),
                        rx.text(
                            "Optimizado para tablets, caja y cocina.",
                            color=TEXT_MUTED,
                            font_size="0.74rem",
                        ),
                        align="start",
                        spacing="1",
                    ),
                    width="100%",
                    padding="0.65rem 0.75rem",
                    border_radius="10px",
                    style={"background": SURFACE_MUTED},
                    border=f"1px solid {BORDER_COLOR}",
                ),
            ),
            rx.cond(
                FoodState.sidebar_collapsed,
                rx.fragment(),
                rx.box(
                    user_session_badge(),
                    width="100%",
                    padding_top="0.25rem",
                ),
            ),
            height="100%",
            width="100%",
            spacing="0",
            gap="0.5rem",
            align="start",
        ),
        width=rx.cond(FoodState.sidebar_collapsed, "72px", "256px"),
        min_width=rx.cond(FoodState.sidebar_collapsed, "72px", "256px"),
        height="100vh",
        position="sticky",
        top="0",
        padding="0.75rem",
        background="linear-gradient(to bottom, #F8FAFC, rgba(255,255,255,0.97))",
        border_right=f"1px solid {BORDER_COLOR}",
        display=rx.breakpoints(initial="none", lg="block"),
        flex_shrink="0",
    )


def _mobile_nav_drawer(active: str) -> rx.Component:
    return rx.box(
        rx.drawer.root(
            rx.drawer.trigger(
                rx.icon_button(
                    rx.icon(tag="menu", size=17),
                    background=SURFACE_MUTED,
                    color=TEXT_SECONDARY,
                    border=f"1px solid {BORDER_COLOR}",
                    border_radius="8px",
                    _hover={"background": SURFACE_HOVER},
                )
            ),
            rx.drawer.portal(
                rx.drawer.overlay(),
                rx.drawer.content(
                    rx.box(
                        rx.vstack(
                            rx.hstack(
                                _brand(compact=False),
                                rx.drawer.close(
                                    rx.icon_button(
                                        rx.icon(tag="x", size=17),
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
                            rx.box(height="1px", width="100%", background=BORDER_COLOR),
                            _nav_stack(active, mobile=True),
                            rx.box(height="1px", width="100%", background=BORDER_COLOR),
                            user_session_badge(),
                            width="100%",
                            align="start",
                            spacing="4",
                        ),
                        width="300px",
                        max_width="88vw",
                        height="100%",
                        padding="1rem",
                        background=SURFACE_ELEVATED,
                        border_right=f"1px solid {BORDER_STRONG}",
                    ),
                    justify_content="flex-start",
                ),
            ),
            direction="left",
        ),
        display=rx.breakpoints(initial="block", lg="none"),
    )


def _page_header(active: str, title: str, subtitle: str, action=None) -> rx.Component:
    return surface_card(
        rx.vstack(
            rx.hstack(
                rx.hstack(
                    _mobile_nav_drawer(active),
                    rx.vstack(
                        rx.text(
                            "TUWAYKIFOOD",
                            color=ACCENT,
                            font_size="0.70rem",
                            font_weight="800",
                            letter_spacing="0.12em",
                            text_transform="uppercase",
                        ),
                        rx.heading(
                            title,
                            size=rx.breakpoints(initial="5", md="6"),
                            color=TEXT_PRIMARY,
                            line_height="1.1",
                        ),
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
                        rx.box(
                            user_session_badge(),
                            display=rx.breakpoints(initial="none", lg="block"),
                        ),
                        rx.fragment(),
                    ),
                    spacing="3",
                    align="center",
                    flex_shrink="0",
                ),
                width="100%",
                justify="between",
                align="center",
                gap="0.75rem",
            ),
            rx.box(
                rx.text(subtitle, color=TEXT_MUTED, font_size="0.85rem", max_width="720px"),
                display=rx.breakpoints(initial="none", md="block"),
                width="100%",
            ),
            width="100%",
            spacing="2",
            align="start",
        ),
        padding=rx.breakpoints(initial="0.85rem 1rem", md="1.1rem 1.25rem"),
        background=SURFACE_ELEVATED,
    )


def _mobile_topbar(active: str) -> rx.Component:
    return rx.box(
        rx.hstack(
            _mobile_nav_drawer(active),
            _brand(compact=False),
            spacing="3",
            align="center",
            width="100%",
        ),
        display=rx.breakpoints(initial="block", lg="none"),
        padding="0.6rem 1rem",
        border_bottom=f"1px solid {BORDER_COLOR}",
        background=SURFACE_ELEVATED,
        width="100%",
        position="sticky",
        top="0",
        z_index="200",
        box_shadow="0 1px 4px rgba(0,0,0,0.06)",
    )


def app_shell(
    content: rx.Component,
    *,
    page_key: str = "",
    active: str = "",
) -> rx.Component:
    _active = page_key or active
    return rx.box(
        rx.script(_CSS_SCRIPT),
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
                    padding=rx.breakpoints(initial="1rem", md="1.5rem", xl="2rem"),
                    width="100%",
                ),
                width="100%",
                min_height="100vh",
            ),
            width="100%",
            align="start",
            gap="0",
        ),
        min_height="100vh",
        width="100%",
        background=PAGE_BACKGROUND,
        color=TEXT_PRIMARY,
    )
