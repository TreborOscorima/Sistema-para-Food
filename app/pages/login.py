"""Pagina de login con teclado PIN."""

from __future__ import annotations

import reflex as rx

from app.states.food_state import FoodState


def _pin_dot(filled: bool) -> rx.Component:
    return rx.box(
        width="14px",
        height="14px",
        border_radius="50%",
        background=rx.cond(filled, "#F97316", "rgba(255,255,255,0.15)"),
        border=rx.cond(filled, "2px solid #F97316", "2px solid rgba(255,255,255,0.25)"),
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
        bg = "rgba(239,68,68,0.12)"
        hover_bg = "rgba(239,68,68,0.22)"
        color = "#FCA5A5"
    elif variant == "confirm":
        bg = "rgba(249,115,22,0.18)"
        hover_bg = "rgba(249,115,22,0.30)"
        color = "#F97316"
    else:
        bg = "rgba(255,255,255,0.06)"
        hover_bg = "rgba(255,255,255,0.12)"
        color = "#F1F5F9"
    return rx.button(
        label,
        on_click=on_click,
        width="72px",
        height="72px",
        border_radius="12px",
        background=bg,
        color=color,
        font_size="22px",
        font_weight="600",
        border="1px solid rgba(255,255,255,0.08)",
        cursor="pointer",
        _hover={"background": hover_bg, "transform": "scale(1.05)"},
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


@rx.page(route="/login", on_load=FoodState.on_load_login)
def login_page() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.vstack(
                rx.text(
                    "TUWAYKIFOOD",
                    font_size="26px",
                    font_weight="800",
                    color="#F97316",
                    letter_spacing="0.06em",
                    text_align="center",
                ),
                rx.text(
                    "POS Sistema para Restaurantes",
                    font_size="13px",
                    color="rgba(255,255,255,0.4)",
                    text_align="center",
                ),
                spacing="1",
                align="center",
                padding_bottom="8px",
            ),
            rx.box(
                rx.vstack(
                    rx.text(
                        "Ingresa tu PIN",
                        font_size="15px",
                        font_weight="600",
                        color="#F1F5F9",
                        text_align="center",
                    ),
                    _pin_display(),
                    rx.cond(
                        FoodState.login_pin_input.length() > 0,
                        rx.text(
                            FoodState.login_pin_input.length().to_string() + " digito(s) ingresado(s)",
                            font_size="11px",
                            color="rgba(255,255,255,0.3)",
                            text_align="center",
                        ),
                        rx.text(
                            "4 a 6 digitos",
                            font_size="11px",
                            color="rgba(255,255,255,0.2)",
                            text_align="center",
                        ),
                    ),
                    _keypad(),
                    spacing="4",
                    align="center",
                    padding="32px 28px",
                ),
                background="#0F172A",
                border="1px solid rgba(249,115,22,0.20)",
                border_radius="20px",
                box_shadow="0 24px 64px rgba(0,0,0,0.60)",
            ),
            spacing="6",
            align="center",
        ),
        min_height="100vh",
        background="linear-gradient(135deg, #080E18 0%, #0C1624 100%)",
    )
