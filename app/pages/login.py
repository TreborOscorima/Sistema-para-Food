"""Login PIN — diseño Claude Design: pantalla única, selector de rol + teclado rectangular."""

from __future__ import annotations

import reflex as rx

from app.components.shared import _CSS_SCRIPT
from app.states.food_state import FoodState


# ─── Tarjeta de rol ───────────────────────────────────────────────────────────
# El rol seleccionado se valida contra el rol real del usuario dueño del PIN
# (ver FoodState._authenticate_with_pin) — no es solo decorativo.

def _rol_card(emoji: str, label: str, rol_value: str) -> rx.Component:
    activo = FoodState.login_rol_seleccionado == rol_value
    return rx.box(
        rx.vstack(
            rx.text(emoji, font_size="20px", line_height="1"),
            rx.text(
                label,
                font_size="13px",
                font_weight="600",
                color=rx.cond(activo, "#FFFFFF", "#94A3B8"),
                line_height="1",
            ),
            spacing="1",
            align="center",
        ),
        on_click=FoodState.seleccionar_login_rol(rol_value),
        background="#0F172A",
        border=rx.cond(activo, "2px solid #EA580C", "2px solid #334155"),
        border_radius="12px",
        padding="12px",
        text_align="center",
        cursor="pointer",
        transition="border-color 0.15s, transform 0.1s",
        _hover={"border_color": "#EA580C", "transform": "scale(0.98)"},
        _active={"transform": "scale(0.95)"},
    )


# ─── PIN dots ─────────────────────────────────────────────────────────────────

def _pin_dot(filled: bool) -> rx.Component:
    return rx.box(
        width="16px",
        height="16px",
        border_radius="50%",
        background=rx.cond(filled, "#EA580C", "transparent"),
        border=rx.cond(filled, "2px solid #EA580C", "2px solid #334155"),
        transition="all 0.12s ease",
        box_shadow=rx.cond(filled, "0 0 8px rgba(234,88,12,0.5)", "none"),
    )


def _pin_display() -> rx.Component:
    n = FoodState.login_pin_input.length()
    return rx.hstack(
        _pin_dot(n >= 1),
        _pin_dot(n >= 2),
        _pin_dot(n >= 3),
        _pin_dot(n >= 4),
        _pin_dot(n >= 5),
        _pin_dot(n >= 6),
        spacing="3",
        justify="center",
        padding_y="4px",
    )


# ─── Teclas rectangulares ─────────────────────────────────────────────────────

def _key_rect(content: rx.Component, on_click, aria_label: str,
              bg: str = "#0F172A", border_color: str = "#334155") -> rx.Component:
    return rx.button(
        content,
        on_click=on_click,
        aria_label=aria_label,
        background=bg,
        border=f"1px solid {border_color}",
        border_radius="12px",
        padding="18px 0",
        width="100%",
        display="flex",
        align_items="center",
        justify_content="center",
        cursor="pointer",
        transition="all 0.1s",
        _hover={"background": "#1E293B", "border_color": "#475569"},
        _active={"transform": "scale(0.95)"},
    )


def _key_digit(digit: str, on_click) -> rx.Component:
    return _key_rect(
        rx.text(digit, font_size="22px", font_weight="600", color="#FFFFFF",
                line_height="1"),
        on_click,
        aria_label=f"Dígito {digit}",
    )


def _key_clear_btn(on_click) -> rx.Component:
    return _key_rect(
        rx.text("C", font_size="14px", font_weight="700", color="#64748B",
                line_height="1"),
        on_click,
        aria_label="Borrar PIN completo",
        bg="#1E293B",
        border_color="#334155",
    )


def _key_backspace_btn(on_click) -> rx.Component:
    return _key_rect(
        rx.icon(tag="delete", size=18, color="#94A3B8"),
        on_click,
        aria_label="Borrar último dígito",
        bg="#1E293B",
        border_color="#334155",
    )


def _keypad() -> rx.Component:
    return rx.grid(
        _key_digit("1", FoodState.append_login_digit("1")),
        _key_digit("2", FoodState.append_login_digit("2")),
        _key_digit("3", FoodState.append_login_digit("3")),
        _key_digit("4", FoodState.append_login_digit("4")),
        _key_digit("5", FoodState.append_login_digit("5")),
        _key_digit("6", FoodState.append_login_digit("6")),
        _key_digit("7", FoodState.append_login_digit("7")),
        _key_digit("8", FoodState.append_login_digit("8")),
        _key_digit("9", FoodState.append_login_digit("9")),
        _key_clear_btn(FoodState.clear_login_pin),
        _key_digit("0", FoodState.append_login_digit("0")),
        _key_backspace_btn(FoodState.backspace_login_pin),
        columns="3",
        gap="10px",
        width="100%",
    )


# ─── Card principal ────────────────────────────────────────────────────────────

def _login_card() -> rx.Component:
    return rx.box(
        # Selector de rol
        rx.text(
            "Seleccioná tu rol",
            font_size="11px",
            font_weight="700",
            color="#64748B",
            text_transform="uppercase",
            letter_spacing="0.08em",
            margin_bottom="12px",
        ),
        rx.grid(
            _rol_card("🧑‍🍳", "Mozo", "Mozo"),
            _rol_card("🍳", "Cocina", "Cocina"),
            _rol_card("🖥️", "Caja", "Caja"),
            columns="3",
            gap="8px",
            margin_bottom="28px",
        ),
        # Ingresá tu PIN
        rx.text(
            "Ingresá tu PIN",
            font_size="11px",
            font_weight="700",
            color="#64748B",
            text_transform="uppercase",
            letter_spacing="0.08em",
            margin_bottom="16px",
        ),
        _pin_display(),
        # Error (solo ocupa espacio cuando existe)
        rx.cond(
            FoodState.login_error != "",
            rx.hstack(
                rx.icon(tag="circle_x", size=13, color="#B91C1C"),
                rx.text(FoodState.login_error, font_size="12px",
                        color="#B91C1C", font_weight="600"),
                spacing="2",
                align="center",
                background="#FEF2F2",
                border="1px solid #FECACA",
                border_radius="8px",
                padding="8px 12px",
                width="100%",
                justify="center",
                margin_y="10px",
            ),
            rx.fragment(),
        ),
        # Contador de dígitos — altura fija siempre para que el teclado
        # de abajo no salte al escribir el primer dígito.
        rx.box(
            rx.cond(
                FoodState.login_pin_input.length() > 0,
                rx.text(
                    FoodState.login_pin_input.length().to_string() + " dígito(s)",
                    font_size="11px",
                    color="#475569",
                    text_align="center",
                ),
                rx.fragment(),
            ),
            height="22px",
            margin_y="4px",
            display="flex",
            align_items="center",
            justify_content="center",
        ),
        # Teclado
        _keypad(),
        # Botón Ingresar
        rx.button(
            rx.text("Ingresar", font_size="15px", font_weight="700",
                    color="#FFFFFF"),
            on_click=FoodState.submit_login_pin,
            background="#EA580C",
            border_radius="12px",
            padding="16px",
            width="100%",
            cursor="pointer",
            margin_top="16px",
            _hover={"background": "#C2410C",
                    "box_shadow": "0 6px 20px rgba(234,88,12,0.45)"},
            _active={"transform": "scale(0.98)"},
            transition="all 0.15s",
        ),
        # Interior del card
        background="#1E293B",
        border_radius="20px",
        border="1px solid #334155",
        padding="32px",
        width="100%",
        max_width="400px",
    )


# ─── Página de login ──────────────────────────────────────────────────────────

@rx.page(route="/login", on_load=FoodState.on_load_login,
         title="TUWAYKIFOOD | Iniciar Sesión")
def login_page() -> rx.Component:
    return rx.box(
        rx.script(_CSS_SCRIPT),
        rx.center(
            rx.vstack(
                # Logo completo (marca) — pantalla de login
                rx.box(
                    rx.image(
                        src="/TUWAYKIFOOD.png",
                        height="100px",
                        width="auto",
                        alt="TUWAYKIFOOD",
                    ),
                    background="#FFFFFF",
                    border_radius="16px",
                    padding="12px 20px",
                    box_shadow="0 8px 28px rgba(0,0,0,0.35)",
                    margin_bottom="8px",
                ),
                # Card principal
                _login_card(),
                # Link administrador
                rx.link(
                    "Acceso administrador →",
                    href="/admin/login",
                    font_size="13px",
                    color="#475569",
                    font_weight="500",
                    text_decoration="none",
                    _hover={"color": "#64748B"},
                ),
                spacing="6",
                align="center",
                width="100%",
                max_width="400px",
                padding_x="20px",
            ),
            min_height="100vh",
            padding_y="40px",
        ),
        background="#0F172A",
        min_height="100vh",
    )
