"""Pagina de login con teclado PIN."""

from __future__ import annotations

import reflex as rx

from app.states.food_state import FoodState


def _pin_dot(filled: bool) -> rx.Component:
    return rx.box(
        width="13px",
        height="13px",
        border_radius="50%",
        background=rx.cond(filled, "#EA580C", "#E2E8F0"),
        border=rx.cond(filled, "2px solid #EA580C", "2px solid #CBD5E1"),
        transition="all 0.15s ease",
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
        spacing="3",
        justify="center",
        padding_y="8px",
    )


def _keypad_button(label: str, on_click=None, variant: str = "normal") -> rx.Component:
    if variant == "backspace":
        bg = "#FEF2F2"
        hover_bg = "#FEE2E2"
        color = "#B91C1C"
        border = "1px solid #FECACA"
    elif variant == "confirm":
        bg = "#FFF7ED"
        hover_bg = "#FFEDD5"
        color = "#EA580C"
        border = "1px solid #FED7AA"
    else:
        bg = "#F8FAFC"
        hover_bg = "#F1F5F9"
        color = "#0F172A"
        border = "1px solid #E2E8F0"
    return rx.button(
        label,
        on_click=on_click,
        width="70px",
        height="70px",
        border_radius="12px",
        background=bg,
        color=color,
        font_size="20px",
        font_weight="600",
        border=border,
        cursor="pointer",
        _hover={"background": hover_bg, "transform": "scale(1.03)"},
        transition="all 0.12s ease",
    )


def _keypad() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            _keypad_button("1", FoodState.append_login_digit("1")),
            _keypad_button("2", FoodState.append_login_digit("2")),
            _keypad_button("3", FoodState.append_login_digit("3")),
            spacing="3",
        ),
        rx.hstack(
            _keypad_button("4", FoodState.append_login_digit("4")),
            _keypad_button("5", FoodState.append_login_digit("5")),
            _keypad_button("6", FoodState.append_login_digit("6")),
            spacing="3",
        ),
        rx.hstack(
            _keypad_button("7", FoodState.append_login_digit("7")),
            _keypad_button("8", FoodState.append_login_digit("8")),
            _keypad_button("9", FoodState.append_login_digit("9")),
            spacing="3",
        ),
        rx.hstack(
            _keypad_button("C", FoodState.clear_login_pin, variant="backspace"),
            _keypad_button("0", FoodState.append_login_digit("0")),
            _keypad_button("OK", FoodState.submit_login_pin, variant="confirm"),
            spacing="3",
        ),
        spacing="3",
        align="center",
    )


@rx.page(route="/login", on_load=FoodState.on_load_login, title="TUWAYKIFOOD | Iniciar Sesión")
def login_page() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.image(
                src="/TUWAYKIFOOD.png",
                width="220px",
                height="auto",
                alt="TUWAYKIFOOD",
            ),
            rx.box(
                rx.vstack(
                    rx.text(
                        "Ingresa tu PIN",
                        font_size="14px",
                        font_weight="600",
                        color="#0F172A",
                        text_align="center",
                    ),
                    _pin_display(),
                    rx.cond(
                        FoodState.login_error != "",
                        rx.hstack(
                            rx.icon(tag="circle_x", size=14, color="#B91C1C"),
                            rx.text(
                                FoodState.login_error,
                                font_size="12px",
                                color="#B91C1C",
                                font_weight="600",
                            ),
                            spacing="1",
                            align="center",
                            background="#FEF2F2",
                            border="1px solid #FECACA",
                            border_radius="8px",
                            padding="8px 12px",
                            width="100%",
                            justify="center",
                        ),
                        rx.cond(
                            FoodState.login_pin_input.length() > 0,
                            rx.text(
                                FoodState.login_pin_input.length().to_string() + " dígito(s) ingresado(s)",
                                font_size="11px",
                                color="#64748B",
                                text_align="center",
                            ),
                            rx.text(
                                "Ingresa tu PIN de 4 a 6 dígitos",
                                font_size="11px",
                                color="#94A3B8",
                                text_align="center",
                            ),
                        ),
                    ),
                    _keypad(),
                    spacing="4",
                    align="center",
                    padding="28px 24px",
                ),
                background="#FFFFFF",
                border="1px solid #E2E8F0",
                border_radius="16px",
                box_shadow="0 4px 24px rgba(0,0,0,0.08)",
            ),
            spacing="6",
            align="center",
        ),
        min_height="100vh",
        background="#F8FAFC",
    )
