"""Carta digital publica — accesible por QR sin login."""

from __future__ import annotations

import reflex as rx

from app.states.food_state import CategoriaPublicaView, MenuPublicoState, ProductoPublicoView


def _producto_card(prod: ProductoPublicoView) -> rx.Component:
    return rx.hstack(
        rx.vstack(
            rx.text(prod.nombre, font_size="14px", font_weight="600", color="#0F172A"),
            rx.cond(
                prod.descripcion != "",
                rx.text(prod.descripcion, font_size="12px", color="#64748B", line_height="1.4"),
                rx.fragment(),
            ),
            spacing="1",
            align="start",
            flex="1",
        ),
        rx.text(
            prod.precio_texto,
            font_size="15px",
            font_weight="700",
            color="#EA580C",
            min_width="72px",
            text_align="right",
        ),
        width="100%",
        align="start",
        padding="12px 0",
        border_bottom="1px solid #F1F5F9",
    )


def _categoria_section(cat: CategoriaPublicaView) -> rx.Component:
    return rx.vstack(
        rx.box(
            rx.text(
                cat.nombre,
                font_size="13px",
                font_weight="800",
                color="#EA580C",
                text_transform="uppercase",
                letter_spacing="0.08em",
            ),
            padding="6px 0 4px",
            border_bottom="2px solid #EA580C",
            margin_bottom="2px",
            width="100%",
        ),
        rx.vstack(
            rx.foreach(cat.productos, _producto_card),
            width="100%",
            spacing="0",
        ),
        spacing="0",
        width="100%",
        margin_bottom="8px",
    )


def _menu_content() -> rx.Component:
    return rx.box(
        rx.vstack(
            # Header
            rx.vstack(
                rx.hstack(
                    rx.box(
                        rx.text("🍽", font_size="26px"),
                        width="48px",
                        height="48px",
                        border_radius="12px",
                        background="#FFF7ED",
                        border="1px solid #FED7AA",
                        display="flex",
                        align_items="center",
                        justify_content="center",
                    ),
                    rx.vstack(
                        rx.text(
                            MenuPublicoState.nombre_local,
                            font_size="20px",
                            font_weight="800",
                            color="#0F172A",
                        ),
                        rx.text(
                            "Carta digital",
                            font_size="12px",
                            color="#94A3B8",
                            font_weight="500",
                        ),
                        spacing="0",
                        align="start",
                    ),
                    spacing="3",
                    align="center",
                ),
                padding="20px 16px 12px",
                width="100%",
                background="linear-gradient(135deg, #FFF7ED 0%, #FFFFFF 100%)",
                border_bottom="1px solid #FED7AA",
            ),
            # Loading
            rx.cond(
                MenuPublicoState.cargando,
                rx.center(
                    rx.vstack(
                        rx.spinner(color="#EA580C", size="3"),
                        rx.text("Cargando carta...", font_size="13px", color="#94A3B8"),
                        spacing="3",
                        align="center",
                    ),
                    padding_y="60px",
                    width="100%",
                ),
                rx.cond(
                    MenuPublicoState.no_encontrado,
                    rx.center(
                        rx.vstack(
                            rx.icon(tag="search_x", size=40, color="#CBD5E1"),
                            rx.text(
                                "Carta no encontrada",
                                font_size="16px",
                                font_weight="700",
                                color="#475569",
                            ),
                            rx.text(
                                "El restaurante no tiene una carta digital activa.",
                                font_size="13px",
                                color="#94A3B8",
                                text_align="center",
                            ),
                            spacing="3",
                            align="center",
                        ),
                        padding_y="60px",
                        padding_x="24px",
                        width="100%",
                    ),
                    rx.cond(
                        MenuPublicoState.categorias_menu.length() == 0,
                        rx.center(
                            rx.vstack(
                                rx.icon(tag="book_open", size=40, color="#CBD5E1"),
                                rx.text(
                                    "Carta sin productos",
                                    font_size="15px",
                                    font_weight="600",
                                    color="#475569",
                                ),
                                spacing="3",
                                align="center",
                            ),
                            padding_y="60px",
                            width="100%",
                        ),
                        rx.vstack(
                            rx.foreach(MenuPublicoState.categorias_menu, _categoria_section),
                            width="100%",
                            spacing="4",
                            padding="16px",
                        ),
                    ),
                ),
            ),
            # Footer
            rx.center(
                rx.hstack(
                    rx.text("Powered by", font_size="11px", color="#94A3B8"),
                    rx.text(
                        "TUWAYKIFOOD",
                        font_size="11px",
                        font_weight="800",
                        color="#EA580C",
                    ),
                    spacing="1",
                    align="center",
                ),
                padding="16px",
                border_top="1px solid #F1F5F9",
                width="100%",
            ),
            spacing="0",
            width="100%",
            min_height="100vh",
        ),
        background="#FFFFFF",
        max_width="480px",
        margin="0 auto",
        min_height="100vh",
    )


@rx.page(route="/menu/[slug]", on_load=MenuPublicoState.on_load)
def menu_publico_page() -> rx.Component:
    return rx.box(
        _menu_content(),
        background="#F8FAFC",
        min_height="100vh",
    )
