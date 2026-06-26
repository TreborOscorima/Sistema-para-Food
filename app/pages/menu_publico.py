"""Carta digital publica — accesible por QR sin login."""

from __future__ import annotations

import reflex as rx

from app.states.food_state import CategoriaPublicaView, MenuPublicoState, ProductoPublicoView


def _producto_card(prod: ProductoPublicoView) -> rx.Component:
    return rx.box(
        rx.vstack(
            # Imagen o placeholder
            rx.cond(
                prod.imagen_url != "",
                rx.image(
                    src=prod.imagen_url,
                    width="100%",
                    height="140px",
                    object_fit="cover",
                    border_radius="10px 10px 0 0",
                ),
                rx.center(
                    rx.icon(tag="utensils", size=32, color="#CBD5E1"),
                    width="100%",
                    height="140px",
                    background="linear-gradient(135deg, #FFF7ED 0%, #FEF3C7 100%)",
                    border_radius="10px 10px 0 0",
                ),
            ),
            # Info
            rx.vstack(
                rx.text(
                    prod.nombre,
                    font_size="13px",
                    font_weight="700",
                    color="#0F172A",
                    no_of_lines=2,
                    line_height="1.3",
                ),
                rx.cond(
                    prod.descripcion != "",
                    rx.text(
                        prod.descripcion,
                        font_size="11px",
                        color="#64748B",
                        no_of_lines=2,
                        line_height="1.4",
                    ),
                    rx.fragment(),
                ),
                rx.text(
                    prod.precio_texto,
                    font_size="15px",
                    font_weight="800",
                    color="#EA580C",
                    margin_top="4px",
                ),
                spacing="1",
                align="start",
                padding="10px 12px 12px",
                width="100%",
            ),
            spacing="0",
            width="100%",
        ),
        background="#FFFFFF",
        border_radius="12px",
        border="1px solid #F1F5F9",
        box_shadow="0 2px 8px rgba(0,0,0,0.07)",
        overflow="hidden",
        _hover={"box_shadow": "0 4px 16px rgba(234,88,12,0.12)", "border_color": "#FED7AA"},
        transition="all 0.15s ease",
    )


def _categoria_section(cat: CategoriaPublicaView) -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.box(width="3px", height="18px", background="#EA580C", border_radius="2px"),
            rx.text(
                cat.nombre,
                font_size="14px",
                font_weight="800",
                color="#0F172A",
                text_transform="uppercase",
                letter_spacing="0.06em",
            ),
            spacing="2",
            align="center",
        ),
        rx.grid(
            rx.foreach(cat.productos, _producto_card),
            columns=rx.breakpoints(initial="2", sm="3", md="4"),
            gap="12px",
            width="100%",
        ),
        spacing="3",
        width="100%",
    )


def _menu_content() -> rx.Component:
    return rx.box(
        rx.vstack(
            # Header
            rx.box(
                rx.hstack(
                    rx.box(
                        rx.text("🍽", font_size="28px"),
                        width="52px",
                        height="52px",
                        border_radius="14px",
                        background="linear-gradient(135deg, #EA580C 0%, #F97316 100%)",
                        display="flex",
                        align_items="center",
                        justify_content="center",
                        box_shadow="0 4px 12px rgba(234,88,12,0.3)",
                    ),
                    rx.vstack(
                        rx.text(
                            MenuPublicoState.nombre_local,
                            font_size="22px",
                            font_weight="800",
                            color="#0F172A",
                            line_height="1.2",
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
                    padding="20px 16px",
                ),
                background="linear-gradient(135deg, #FFFFFF 0%, #FFF7ED 100%)",
                border_bottom="1px solid #FED7AA",
                width="100%",
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
                    padding_y="80px",
                    width="100%",
                ),
                rx.cond(
                    MenuPublicoState.no_encontrado,
                    rx.center(
                        rx.vstack(
                            rx.icon(tag="search_x", size=48, color="#CBD5E1"),
                            rx.text("Carta no encontrada", font_size="17px", font_weight="700", color="#475569"),
                            rx.text(
                                "El restaurante no tiene carta digital activa.",
                                font_size="13px",
                                color="#94A3B8",
                                text_align="center",
                            ),
                            spacing="3",
                            align="center",
                        ),
                        padding_y="80px",
                        padding_x="24px",
                        width="100%",
                    ),
                    rx.cond(
                        MenuPublicoState.categorias_menu.length() == 0,
                        rx.center(
                            rx.vstack(
                                rx.icon(tag="book_open", size=48, color="#CBD5E1"),
                                rx.text("Carta sin productos", font_size="15px", font_weight="600", color="#475569"),
                                spacing="3",
                                align="center",
                            ),
                            padding_y="80px",
                            width="100%",
                        ),
                        rx.vstack(
                            rx.foreach(MenuPublicoState.categorias_menu, _categoria_section),
                            width="100%",
                            spacing="6",
                            padding="16px",
                        ),
                    ),
                ),
            ),
            # Footer
            rx.center(
                rx.hstack(
                    rx.text("Powered by", font_size="11px", color="#94A3B8"),
                    rx.text("TUWAYKIFOOD", font_size="11px", font_weight="800", color="#EA580C"),
                    spacing="1",
                    align="center",
                ),
                padding="20px 16px",
                border_top="1px solid #F1F5F9",
                width="100%",
            ),
            spacing="0",
            width="100%",
            min_height="100vh",
        ),
        background="#FFFFFF",
        max_width="600px",
        margin="0 auto",
        min_height="100vh",
        box_shadow=rx.breakpoints(initial="none", sm="0 0 40px rgba(0,0,0,0.08)"),
    )


@rx.page(route="/menu/[slug]", on_load=MenuPublicoState.on_load, title="TUWAYKIFOOD | Carta Digital")
def menu_publico_page() -> rx.Component:
    return rx.box(
        _menu_content(),
        background="#F8FAFC",
        min_height="100vh",
    )
