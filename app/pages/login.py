"""Login con teclado PIN — diseño split screen."""

from __future__ import annotations

import reflex as rx

from app.components.shared import _CSS_SCRIPT
from app.states.food_state import FoodState


# ─── PIN dots ─────────────────────────────────────────────────────────────────

def _pin_dot(filled: bool) -> rx.Component:
    return rx.box(
        width="13px",
        height="13px",
        border_radius="50%",
        background=rx.cond(filled, "#EA580C", "rgba(0,0,0,0)"),
        border=rx.cond(filled, "2px solid #EA580C", "2px solid #CBD5E1"),
        transition="all 0.12s ease",
        box_shadow=rx.cond(filled, "0 0 8px rgba(234,88,12,0.4)", "none"),
    )


def _pin_display() -> rx.Component:
    length = FoodState.login_pin_input.length()
    return rx.hstack(
        _pin_dot(length >= 1),
        _pin_dot(length >= 2),
        _pin_dot(length >= 3),
        _pin_dot(length >= 4),
        _pin_dot(length >= 5),
        _pin_dot(length >= 6),
        spacing="4",
        justify="center",
        padding_y="8px",
    )


# ─── Teclas ────────────────────────────────────────────────────────────────────

def _key_btn(content: rx.Component, on_click, variant: str = "default") -> rx.Component:
    bg_map = {
        "default":    "#FFFFFF",
        "backspace":  "#F8FAFC",
        "ok":         "#EA580C",
    }
    color_map = {
        "default":   "#0F172A",
        "backspace": "#64748B",
        "ok":        "#FFFFFF",
    }
    hover_map = {
        "default":   {"background": "#FFF7ED", "border_color": "#FED7AA",
                      "transform": "scale(0.97)"},
        "backspace": {"background": "#FEF2F2", "border_color": "#FECACA",
                      "transform": "scale(0.97)"},
        "ok":        {"background": "#C2410C", "box_shadow": "0 6px 20px rgba(234,88,12,0.5)",
                      "transform": "scale(0.97)"},
    }
    shadow = "0 4px 16px rgba(234,88,12,0.35)" if variant == "ok" else "0 1px 4px rgba(0,0,0,0.07)"
    border = "none" if variant == "ok" else "1.5px solid #E2E8F0"
    return rx.button(
        content,
        on_click=on_click,
        width=rx.breakpoints(initial="68px", sm="76px"),
        height=rx.breakpoints(initial="68px", sm="76px"),
        border_radius="50%",
        background=bg_map[variant],
        color=color_map[variant],
        border=border,
        cursor="pointer",
        box_shadow=shadow,
        _hover=hover_map[variant],
        _active={"transform": "scale(0.92)", "box_shadow": "none"},
        transition="all 0.1s ease",
        display="flex",
        align_items="center",
        justify_content="center",
        padding="0",
    )


def _key_num(digit: str, letters: str, on_click) -> rx.Component:
    return _key_btn(
        rx.vstack(
            rx.text(digit, font_size=rx.breakpoints(initial="22px", sm="26px"),
                    font_weight="300", color="#0F172A", line_height="1"),
            rx.text(letters, font_size="8px", font_weight="700",
                    color="#94A3B8", letter_spacing="0.16em"),
            spacing="0",
            align="center",
        ),
        on_click,
        variant="default",
    )


def _key_zero(on_click) -> rx.Component:
    return _key_btn(
        rx.text("0", font_size=rx.breakpoints(initial="22px", sm="26px"),
                font_weight="300", color="#0F172A"),
        on_click,
        variant="default",
    )


def _key_backspace(on_click) -> rx.Component:
    return _key_btn(
        rx.icon(tag="delete", size=20, color="#64748B"),
        on_click,
        variant="backspace",
    )


def _key_ok(on_click) -> rx.Component:
    return _key_btn(
        rx.text("OK", font_size="16px", font_weight="800", color="#FFFFFF"),
        on_click,
        variant="ok",
    )


def _keypad() -> rx.Component:
    sp = rx.breakpoints(initial="4", sm="5")
    return rx.vstack(
        rx.hstack(
            _key_num("1", "", FoodState.append_login_digit("1")),
            _key_num("2", "ABC", FoodState.append_login_digit("2")),
            _key_num("3", "DEF", FoodState.append_login_digit("3")),
            spacing=sp,
        ),
        rx.hstack(
            _key_num("4", "GHI", FoodState.append_login_digit("4")),
            _key_num("5", "JKL", FoodState.append_login_digit("5")),
            _key_num("6", "MNO", FoodState.append_login_digit("6")),
            spacing=sp,
        ),
        rx.hstack(
            _key_num("7", "PQRS", FoodState.append_login_digit("7")),
            _key_num("8", "TUV", FoodState.append_login_digit("8")),
            _key_num("9", "WXYZ", FoodState.append_login_digit("9")),
            spacing=sp,
        ),
        rx.hstack(
            _key_backspace(FoodState.clear_login_pin),
            _key_zero(FoodState.append_login_digit("0")),
            _key_ok(FoodState.submit_login_pin),
            spacing=sp,
        ),
        spacing=rx.breakpoints(initial="4", sm="5"),
        align="center",
    )


# ─── Panel izquierdo (branding) ───────────────────────────────────────────────

def _left_panel() -> rx.Component:
    return rx.box(
        rx.vstack(
            # Logo grande
            rx.image(
                src="/TUWAYKIFOODFAVICON.png",
                width="80px",
                height="80px",
                border_radius="22px",
                box_shadow="0 8px 32px rgba(0,0,0,0.25)",
                alt="TUWAYKIFOOD",
            ),
            rx.vstack(
                rx.text(
                    "TUWAYKIFOOD",
                    font_size="28px",
                    font_weight="800",
                    color="#FFFFFF",
                    letter_spacing="0.04em",
                    text_align="center",
                    line_height="1",
                ),
                rx.text(
                    "Sistema para restaurantes",
                    font_size="14px",
                    color="rgba(255,255,255,0.55)",
                    text_align="center",
                    font_weight="500",
                ),
                spacing="2",
                align="center",
            ),
            # Separador decorativo
            rx.box(
                width="48px",
                height="3px",
                border_radius="2px",
                background="rgba(255,255,255,0.3)",
                margin_y="8px",
            ),
            # Features bullets
            rx.vstack(
                rx.hstack(
                    rx.box(width="6px", height="6px", border_radius="50%",
                           background="rgba(255,255,255,0.5)", flex_shrink="0"),
                    rx.text("Mesas en tiempo real", color="rgba(255,255,255,0.68)",
                            font_size="13px"),
                    spacing="2",
                    align="center",
                ),
                rx.hstack(
                    rx.box(width="6px", height="6px", border_radius="50%",
                           background="rgba(255,255,255,0.5)", flex_shrink="0"),
                    rx.text("Cocina KDS integrada", color="rgba(255,255,255,0.68)",
                            font_size="13px"),
                    spacing="2",
                    align="center",
                ),
                rx.hstack(
                    rx.box(width="6px", height="6px", border_radius="50%",
                           background="rgba(255,255,255,0.5)", flex_shrink="0"),
                    rx.text("Carta digital QR", color="rgba(255,255,255,0.68)",
                            font_size="13px"),
                    spacing="2",
                    align="center",
                ),
                rx.hstack(
                    rx.box(width="6px", height="6px", border_radius="50%",
                           background="rgba(255,255,255,0.5)", flex_shrink="0"),
                    rx.text("Reportes y ventas del dia", color="rgba(255,255,255,0.68)",
                            font_size="13px"),
                    spacing="2",
                    align="center",
                ),
                spacing="3",
                align="start",
            ),
            spacing="6",
            align="center",
        ),
        width="100%",
        height="100%",
        display="flex",
        align_items="center",
        justify_content="center",
        background="linear-gradient(145deg, #0F172A 0%, #1E293B 50%, #292524 100%)",
        padding=rx.breakpoints(initial="0", md="40px"),
        position="relative",
        overflow="hidden",
        # Decoración de fondo
        _before={
            "content": "''",
            "position": "absolute",
            "top": "-80px",
            "right": "-80px",
            "width": "300px",
            "height": "300px",
            "border_radius": "50%",
            "background": "rgba(234,88,12,0.12)",
            "pointer_events": "none",
        },
    )


# ─── Panel derecho (PIN form) ─────────────────────────────────────────────────

def _right_panel() -> rx.Component:
    return rx.center(
        rx.vstack(
            # Encabezado
            rx.vstack(
                rx.text(
                    "Ingresa tu PIN",
                    font_size=rx.breakpoints(initial="20px", sm="22px"),
                    font_weight="800",
                    color="#0F172A",
                    text_align="center",
                ),
                rx.text(
                    "Acceso con PIN de 4 a 6 dígitos",
                    font_size="13px",
                    color="#64748B",
                    text_align="center",
                    font_weight="400",
                ),
                spacing="1",
                align="center",
            ),
            # PIN display
            _pin_display(),
            # Error / estado
            rx.cond(
                FoodState.login_error != "",
                rx.hstack(
                    rx.icon(tag="circle_x", size=14, color="#B91C1C"),
                    rx.text(FoodState.login_error, font_size="12px",
                            color="#B91C1C", font_weight="600"),
                    spacing="2",
                    align="center",
                    background="#FEF2F2",
                    border="1px solid #FECACA",
                    border_radius="8px",
                    padding="8px 14px",
                    width="100%",
                    justify="center",
                ),
                rx.cond(
                    FoodState.login_pin_input.length() > 0,
                    rx.text(
                        FoodState.login_pin_input.length().to_string() + " dígito(s)",
                        font_size="11px",
                        color="#64748B",
                        text_align="center",
                        font_weight="500",
                    ),
                    rx.box(height="22px"),
                ),
            ),
            # Teclado
            _keypad(),
            # Link admin
            rx.link(
                rx.hstack(
                    rx.icon(tag="shield", size=11, color="#94A3B8"),
                    rx.text("Acceso Administrativo", font_size="11px",
                            color="#94A3B8", font_weight="500"),
                    spacing="1",
                    align="center",
                ),
                href="/admin/login",
                _hover={"opacity": "0.75"},
            ),
            spacing="5",
            align="center",
            width="100%",
            max_width="340px",
        ),
        width="100%",
        height="100%",
        padding=rx.breakpoints(initial="32px 20px", sm="40px 32px"),
        background="#FFFFFF",
        min_height=rx.breakpoints(initial="100vh", md="auto"),
    )


@rx.page(route="/login", on_load=FoodState.on_load_login,
         title="TUWAYKIFOOD | Iniciar Sesión")
def login_page() -> rx.Component:
    return rx.box(
        rx.script(_CSS_SCRIPT),
        # ── Desktop: split 45/55 ── Mobile: solo panel derecho ────────────────
        rx.box(
            # Panel izquierdo: oculto en mobile
            rx.box(
                _left_panel(),
                display=rx.breakpoints(initial="none", md="flex"),
                width="45%",
                min_height="100vh",
                flex_shrink="0",
            ),
            # Panel derecho: full width en mobile, 55% en desktop
            rx.box(
                _right_panel(),
                width=rx.breakpoints(initial="100%", md="55%"),
                min_height="100vh",
                display="flex",
                align_items="center",
                justify_content="center",
            ),
            display="flex",
            flex_direction="row",
            width="100%",
            min_height="100vh",
        ),
        min_height="100vh",
        background="#FFFFFF",
    )
