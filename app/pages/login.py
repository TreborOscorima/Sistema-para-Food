"""Pagina de login con teclado PIN estilo iPhone."""

from __future__ import annotations

import reflex as rx

from app.states.food_state import FoodState


def _pin_dot(filled: bool) -> rx.Component:
    return rx.box(
        width="14px",
        height="14px",
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
        spacing="4",
        justify="center",
        padding_y="10px",
    )


def _key_num(digit: str, letters: str, on_click) -> rx.Component:
    return rx.button(
        rx.vstack(
            rx.text(digit, font_size="24px", font_weight="300", color="#0F172A", line_height="1.1"),
            rx.text(letters, font_size="9px", font_weight="600", color="#475569", letter_spacing="0.14em"),
            spacing="0",
            align="center",
        ),
        on_click=on_click,
        width="78px",
        height="78px",
        border_radius="50%",
        background="#E9E9EB",
        border="none",
        cursor="pointer",
        _hover={"background": "#D1D1D6", "transform": "scale(0.96)"},
        _active={"background": "#C7C7CC", "transform": "scale(0.92)"},
        transition="all 0.1s ease",
        display="flex",
        align_items="center",
        justify_content="center",
        padding="0",
    )


def _key_zero(on_click) -> rx.Component:
    return rx.button(
        rx.text("0", font_size="24px", font_weight="300", color="#0F172A"),
        on_click=on_click,
        width="78px",
        height="78px",
        border_radius="50%",
        background="#E9E9EB",
        border="none",
        cursor="pointer",
        _hover={"background": "#D1D1D6", "transform": "scale(0.96)"},
        _active={"background": "#C7C7CC", "transform": "scale(0.92)"},
        transition="all 0.1s ease",
        display="flex",
        align_items="center",
        justify_content="center",
        padding="0",
    )


def _key_backspace(on_click) -> rx.Component:
    return rx.button(
        rx.icon(tag="delete", size=22, color="#64748B"),
        on_click=on_click,
        width="78px",
        height="78px",
        border_radius="50%",
        background="#E9E9EB",
        border="none",
        cursor="pointer",
        _hover={"background": "#FEE2E2", "color": "#B91C1C"},
        _active={"background": "#FECACA", "transform": "scale(0.92)"},
        transition="all 0.1s ease",
        display="flex",
        align_items="center",
        justify_content="center",
        padding="0",
    )


def _key_ok(on_click) -> rx.Component:
    return rx.button(
        rx.text("OK", font_size="16px", font_weight="700", color="#FFFFFF"),
        on_click=on_click,
        width="78px",
        height="78px",
        border_radius="50%",
        background="#EA580C",
        border="none",
        cursor="pointer",
        _hover={"background": "#C2410C", "transform": "scale(0.96)"},
        _active={"background": "#9A3412", "transform": "scale(0.92)"},
        transition="all 0.1s ease",
        display="flex",
        align_items="center",
        justify_content="center",
        padding="0",
        box_shadow="0 4px 12px rgba(234,88,12,0.35)",
    )


def _keypad() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            _key_num("1", "", FoodState.append_login_digit("1")),
            _key_num("2", "ABC", FoodState.append_login_digit("2")),
            _key_num("3", "DEF", FoodState.append_login_digit("3")),
            spacing="5",
        ),
        rx.hstack(
            _key_num("4", "GHI", FoodState.append_login_digit("4")),
            _key_num("5", "JKL", FoodState.append_login_digit("5")),
            _key_num("6", "MNO", FoodState.append_login_digit("6")),
            spacing="5",
        ),
        rx.hstack(
            _key_num("7", "PQRS", FoodState.append_login_digit("7")),
            _key_num("8", "TUV", FoodState.append_login_digit("8")),
            _key_num("9", "WXYZ", FoodState.append_login_digit("9")),
            spacing="5",
        ),
        rx.hstack(
            _key_backspace(FoodState.clear_login_pin),
            _key_zero(FoodState.append_login_digit("0")),
            _key_ok(FoodState.submit_login_pin),
            spacing="5",
        ),
        spacing="4",
        align="center",
    )


@rx.page(route="/login", on_load=FoodState.on_load_login, title="TUWAYKIFOOD | Iniciar Sesión")
def login_page() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.image(
                src="/TUWAYKIFOOD.png",
                width="200px",
                height="auto",
                alt="TUWAYKIFOOD",
            ),
            rx.box(
                rx.vstack(
                    rx.text(
                        "Ingresa tu PIN",
                        font_size="15px",
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
                    padding="28px 32px",
                ),
                background="#FFFFFF",
                border="1px solid #E2E8F0",
                border_radius="20px",
                box_shadow="0 4px 32px rgba(0,0,0,0.08)",
            ),
            spacing="6",
            align="center",
        ),
        min_height="100vh",
        background="#F8FAFC",
    )
