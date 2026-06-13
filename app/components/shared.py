"""Componentes compartidos y shell visual de TUWAYKIFOOD POS."""

from __future__ import annotations

import reflex as rx

from app.states.food_state import FoodState


PAGE_BACKGROUND = "linear-gradient(180deg, #060A10 0%, #0B1220 100%)"

SURFACE_BASE = "#0F1826"
SURFACE_ELEVATED = "#111B2E"
SURFACE_SOFT = "#162030"
SURFACE_MUTED = "#0D1520"
SURFACE_GHOST = "#131F36"
SURFACE_HOVER = "#1A2540"
SURFACE_INTERACTIVE = "#1E2B42"

BORDER_COLOR = "#1E2B40"
BORDER_STRONG = "#2A3958"
BORDER_ACCENT = "#623410"

TEXT_PRIMARY = "#F8FAFC"
TEXT_SECONDARY = "#CBD5E1"
TEXT_MUTED = "#64748B"

ACCENT = "#F97316"
ACCENT_HOVER = "#EA580C"
ACCENT_BG = "#3D1A06"
ACCENT_TEXT = "#FDBA74"
ACCENT_SOFT = ACCENT_BG

SUCCESS_BG = "#0A2818"
SUCCESS_TEXT = "#4ADE80"
SUCCESS_BORDER = "#155229"

DANGER_BG = "#2A0A0A"
DANGER_TEXT = "#FCA5A5"
DANGER_BORDER = "#521515"

WARNING_BG = "#2A1A04"
WARNING_TEXT = "#FCD34D"
WARNING_BORDER = "#52360A"

INFO_BG = "#0A1522"
INFO_TEXT = "#93C5FD"
INFO_BORDER = "#1A3550"

GLOW = "0 22px 60px rgba(2, 6, 23, 0.60)"
SOFT_GLOW = "0 14px 36px rgba(2, 6, 23, 0.40)"
ACCENT_GLOW = "0 12px 28px rgba(249, 115, 22, 0.22)"


def surface_card(*children, **props) -> rx.Component:
    bg = props.pop("background", SURFACE_BASE)
    border = props.pop("border", f"1px solid {BORDER_COLOR}")
    border_radius = props.pop("border_radius", "28px")
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
    border_radius = props.pop("border_radius", "24px")
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
        color=TEXT_PRIMARY,
        border_radius="18px",
        height="44px",
        padding_x="1rem",
        _hover={"background": ACCENT_HOVER},
    )


def status_banner(message) -> rx.Component:
    return section_card(
        rx.hstack(
            rx.box(
                width="10px",
                height="10px",
                border_radius="999px",
                style={"background": ACCENT},
                box_shadow=f"0 0 0 8px {ACCENT_BG}",
            ),
            rx.text(message, color=TEXT_SECONDARY, font_weight="600"),
            spacing="4",
            align="center",
        ),
        padding="1rem 1.2rem",
    )


def kpi_card(title: str, value, description: str = "", accent_color: str = ACCENT) -> rx.Component:
    return surface_card(
        rx.vstack(
            rx.text(
                title,
                color=TEXT_MUTED,
                font_size="0.78rem",
                font_weight="800",
                letter_spacing="0.12em",
                text_transform="uppercase",
            ),
            rx.text(
                value,
                color=TEXT_PRIMARY,
                font_weight="800",
                font_size="2rem",
                line_height="1.05",
            ),
            rx.cond(
                description != "",
                rx.text(description, color=TEXT_MUTED, font_size="0.9rem"),
                rx.fragment(),
            ),
            align="start",
            spacing="2",
            width="100%",
        ),
        padding="1.2rem 1.3rem",
        border=f"1px solid {accent_color}",
        background="linear-gradient(160deg, #131F33 0%, #0F1826 100%)",
    )


def _brand(compact: bool = False) -> rx.Component:
    return rx.hstack(
        rx.box(
            rx.icon(tag="utensils", size=20, color=TEXT_PRIMARY),
            width="42px",
            height="42px",
            border_radius="18px",
            style={"background": "linear-gradient(135deg, #C85A08 0%, #A04806 100%)"},
            display="flex",
            align_items="center",
            justify_content="center",
            box_shadow=ACCENT_GLOW,
        ),
        rx.cond(
            compact,
            rx.fragment(),
            rx.vstack(
                rx.text(
                    "TUWAYKIFOOD",
                    color=TEXT_PRIMARY,
                    font_weight="800",
                    letter_spacing="0.12em",
                    font_size="0.78rem",
                    text_transform="uppercase",
                ),
                rx.text("Sistema para restaurantes", color=TEXT_MUTED, font_size="0.86rem"),
                align="start",
                spacing="1",
            ),
        ),
        spacing="3",
        align="center",
    )


def _user_summary() -> rx.Component:
    return rx.hstack(
        rx.box(
            rx.icon(tag="user_round", size=18, color=TEXT_PRIMARY),
            width="42px",
            height="42px",
            border_radius="16px",
            style={"background": SURFACE_INTERACTIVE},
            display="flex",
            align_items="center",
            justify_content="center",
            border=f"1px solid {BORDER_STRONG}",
        ),
        rx.vstack(
            rx.text(
                FoodState.usuario_nombre,
                color=TEXT_PRIMARY,
                font_weight="800",
                font_size="0.92rem",
                max_width="190px",
                text_overflow="ellipsis",
                overflow="hidden",
                white_space="nowrap",
            ),
            rx.text(FoodState.usuario_rol, color=TEXT_MUTED, font_weight="600", font_size="0.82rem"),
            align="start",
            spacing="1",
        ),
        spacing="3",
        align="center",
    )


def user_session_badge() -> rx.Component:
    return rx.hstack(
        _user_summary(),
        rx.button(
            rx.hstack(
                rx.icon(tag="log_out", size=16),
                rx.text("Salir", font_weight="700"),
                spacing="2",
                align="center",
            ),
            on_click=FoodState.logout,
            background=DANGER_BG,
            color=DANGER_TEXT,
            border=f"1px solid {DANGER_BORDER}",
            border_radius="16px",
            height="42px",
            padding_x="0.95rem",
            _hover={"background": "#3D1010"},
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
}


def _desktop_nav_item(label: str, href: str, icon_tag: str, active: bool) -> rx.Component:
    description = _NAV_DESCRIPTIONS.get(label, "Modulo operativo")
    return rx.link(
        rx.box(
            rx.hstack(
                rx.box(
                    rx.icon(tag=icon_tag, size=18, color=TEXT_PRIMARY),
                    width="40px",
                    height="40px",
                    border_radius="14px",
                    style={"background": rx.cond(active, SURFACE_INTERACTIVE, SURFACE_GHOST)},
                    display="flex",
                    align_items="center",
                    justify_content="center",
                ),
                rx.cond(
                    FoodState.sidebar_collapsed,
                    rx.fragment(),
                    rx.vstack(
                        rx.text(label, color=TEXT_PRIMARY, font_weight="700"),
                        rx.text(description, color=TEXT_MUTED, font_size="0.74rem"),
                        align="start",
                        spacing="1",
                    ),
                ),
                width="100%",
                align="center",
                spacing="3",
            ),
            width="100%",
            padding=rx.cond(FoodState.sidebar_collapsed, "0.6rem", "0.7rem 0.8rem"),
            border_radius="20px",
            style={
                "background": rx.cond(
                    active,
                    "linear-gradient(135deg, #4A2208 0%, #2A1408 100%)",
                    "transparent",
                )
            },
            border=rx.cond(active, f"1px solid {BORDER_ACCENT}", "1px solid transparent"),
            _hover={"background": SURFACE_GHOST},
        ),
        href=href,
        width="100%",
        text_decoration="none",
    )


def _mobile_nav_item(label: str, href: str, icon_tag: str, active: bool) -> rx.Component:
    return rx.link(
        rx.box(
            rx.hstack(
                rx.icon(tag=icon_tag, size=18, color=TEXT_PRIMARY),
                rx.text(label, color=TEXT_PRIMARY, font_weight="700"),
                width="100%",
                spacing="3",
                align="center",
            ),
            width="100%",
            padding="0.85rem 1rem",
            min_height="48px",
            border_radius="18px",
            style={"background": rx.cond(active, ACCENT_BG, SURFACE_MUTED)},
            border=rx.cond(active, f"1px solid {BORDER_ACCENT}", f"1px solid {BORDER_COLOR}"),
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
        width="100%",
        spacing="3",
        align="stretch",
    )


def _desktop_sidebar(active: str) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.cond(FoodState.sidebar_collapsed, _brand(compact=True), _brand(compact=False)),
                rx.icon_button(
                    rx.icon(tag="menu", size=18),
                    on_click=FoodState.toggle_sidebar,
                    background=SURFACE_GHOST,
                    color=TEXT_PRIMARY,
                    border=f"1px solid {BORDER_COLOR}",
                    border_radius="16px",
                    _hover={"background": SURFACE_HOVER},
                ),
                width="100%",
                justify="between",
                align="center",
            ),
            rx.box(height="1px", width="100%", background=BORDER_COLOR),
            _nav_stack(active, mobile=False),
            rx.spacer(),
            rx.cond(
                FoodState.sidebar_collapsed,
                rx.fragment(),
                rx.box(
                    rx.vstack(
                        rx.text("Operacion en LAN", color=TEXT_PRIMARY, font_weight="700"),
                        rx.text(
                            "Optimizado para tablets, caja y cocina.",
                            color=TEXT_MUTED,
                            font_size="0.84rem",
                        ),
                        align="start",
                        spacing="2",
                    ),
                    width="100%",
                    padding="1rem",
                    border_radius="20px",
                    style={"background": SURFACE_MUTED},
                    border=f"1px solid {BORDER_COLOR}",
                ),
            ),
            height="100%",
            width="100%",
            spacing="5",
            align="start",
        ),
        width=rx.cond(FoodState.sidebar_collapsed, "96px", "280px"),
        min_width=rx.cond(FoodState.sidebar_collapsed, "96px", "280px"),
        height="calc(100vh - 2rem)",
        position="sticky",
        top="1rem",
        padding="1rem",
        background=SURFACE_ELEVATED,
        border=f"1px solid {BORDER_COLOR}",
        border_radius="30px",
        box_shadow=GLOW,
        display=rx.breakpoints(initial="none", lg="block"),
    )


def _mobile_nav_drawer(active: str) -> rx.Component:
    return rx.box(
        rx.drawer.root(
            rx.drawer.trigger(
                rx.icon_button(
                    rx.icon(tag="menu", size=18),
                    background=SURFACE_GHOST,
                    color=TEXT_PRIMARY,
                    border=f"1px solid {BORDER_COLOR}",
                    border_radius="16px",
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
                                        rx.icon(tag="x", size=18),
                                        background=SURFACE_GHOST,
                                        color=TEXT_PRIMARY,
                                        border=f"1px solid {BORDER_COLOR}",
                                        border_radius="16px",
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
                            spacing="5",
                        ),
                        width="320px",
                        max_width="88vw",
                        height="100%",
                        padding="1.1rem",
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
                            font_size="0.75rem",
                            font_weight="800",
                            letter_spacing="0.16em",
                            text_transform="uppercase",
                        ),
                        rx.heading(
                            title,
                            size=rx.breakpoints(initial="5", md="7"),
                            color=TEXT_PRIMARY,
                            line_height="1.1",
                        ),
                        align="start",
                        spacing="1",
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
                rx.text(subtitle, color=TEXT_MUTED, font_size="0.9rem", max_width="760px"),
                display=rx.breakpoints(initial="none", md="block"),
                width="100%",
            ),
            width="100%",
            spacing="2",
            align="start",
        ),
        padding=rx.breakpoints(initial="0.95rem 1rem", md="1.35rem"),
        background=SURFACE_ELEVATED,
    )


def app_shell(
    content: rx.Component,
    *,
    page_key: str = "",
    active: str = "",
) -> rx.Component:
    _active = page_key or active
    return rx.box(
        rx.hstack(
            _desktop_sidebar(_active),
            rx.box(
                rx.vstack(
                    content,
                    width="100%",
                    align="start",
                    spacing="6",
                ),
                width="100%",
                min_height="100vh",
                padding=rx.breakpoints(initial="1rem", md="1.25rem", xl="1.5rem"),
            ),
            width="100%",
            align="start",
            gap="1rem",
        ),
        min_height="100vh",
        width="100%",
        background=PAGE_BACKGROUND,
        color=TEXT_PRIMARY,
    )
