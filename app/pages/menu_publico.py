"""Carta digital publica — accesible por QR sin login."""

from __future__ import annotations

import reflex as rx

from app.states.food_state import CategoriaPublicaView, MenuPublicoState, ProductoPublicoView


def _categoria_chip(cat: CategoriaPublicaView, idx: int) -> rx.Component:
    return rx.link(
        cat.emoji + " " + cat.nombre,
        href=f"#cat-{idx}",
        background="#F1F5F9",
        color="#64748B",
        font_size="12px",
        font_weight="600",
        padding="6px 14px",
        border_radius="20px",
        white_space="nowrap",
        flex_shrink="0",
        _hover={"background": "#FED7AA", "color": "#C2410C"},
    )


def _producto_item(prod: ProductoPublicoView) -> rx.Component:
    return rx.hstack(
        rx.cond(
            prod.imagen_url != "",
            rx.image(
                src=prod.imagen_url,
                width="72px", height="72px",
                object_fit="cover", border_radius="12px",
                flex_shrink="0",
            ),
            rx.center(
                rx.text(prod.emoji, font_size="32px", line_height="1"),
                width="72px", height="72px",
                background="linear-gradient(135deg,#FED7AA,#FB923C)",
                border_radius="12px", flex_shrink="0",
            ),
        ),
        rx.vstack(
            rx.text(prod.nombre, font_size="15px", font_weight="700", color="#0F172A", line_height="1.3"),
            rx.cond(
                prod.descripcion != "",
                rx.text(prod.descripcion, font_size="12px", color="#64748B",
                        line_height="1.4", no_of_lines=2),
                rx.fragment(),
            ),
            rx.text(prod.precio_texto, font_size="18px", font_weight="800", color="#EA580C", margin_top="6px"),
            spacing="0", align="start", flex="1", min_width="0",
        ),
        spacing="3", align="start", width="100%",
        background="#FFFFFF", border_radius="16px", padding="14px",
        box_shadow="0 1px 4px rgba(0,0,0,0.06)",
    )


def _categoria_section(cat: CategoriaPublicaView, idx: int) -> rx.Component:
    return rx.vstack(
        rx.text(cat.emoji + " " + cat.nombre, font_size="16px", font_weight="800", color="#0F172A"),
        rx.vstack(
            rx.foreach(cat.productos, _producto_item),
            spacing="2", width="100%",
        ),
        id=f"cat-{idx}",
        spacing="3", width="100%", padding_top="4px",
        scroll_margin_top="120px",
    )


def _menu_content() -> rx.Component:
    return rx.box(
        rx.vstack(
            # Header sticky con nombre + categorías
            rx.box(
                rx.hstack(
                    rx.vstack(
                        rx.text(MenuPublicoState.nombre_local, font_size="20px", font_weight="800",
                                color="#0F172A", letter_spacing="-0.02em", line_height="1.2"),
                        rx.text("Menú digital", font_size="13px", color="#94A3B8"),
                        spacing="0", align="start",
                    ),
                    rx.spacer(),
                    rx.image(
                        src="/TUWAYKIFOODFAVICON.png",
                        width="44px", height="44px", border_radius="12px",
                        alt="TUWAYKIFOOD",
                        box_shadow="0 4px 12px rgba(234,88,12,0.3)",
                    ),
                    width="100%", align="center", margin_bottom="14px",
                ),
                rx.cond(
                    MenuPublicoState.categorias_menu.length() > 0,
                    rx.hstack(
                        rx.link(
                            "Todo", href="#menu-categorias",
                            background="#EA580C", color="#FFFFFF",
                            font_size="12px", font_weight="700",
                            padding="6px 14px", border_radius="20px",
                            white_space="nowrap", flex_shrink="0",
                        ),
                        rx.foreach(
                            MenuPublicoState.categorias_menu,
                            lambda cat, idx: _categoria_chip(cat, idx),
                        ),
                        spacing="2", overflow_x="auto", width="100%", padding_bottom="4px",
                    ),
                    rx.fragment(),
                ),
                background="#FFFFFF",
                border_bottom="1px solid #F1F5F9",
                padding=rx.breakpoints(initial="16px 16px 12px", md="20px 24px 14px"),
                position="sticky", top="0", z_index="10",
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
                            rx.foreach(
                                MenuPublicoState.categorias_menu,
                                lambda cat, idx: _categoria_section(cat, idx),
                            ),
                            id="menu-categorias",
                            width="100%",
                            spacing="6",
                            padding=rx.breakpoints(initial="18px 16px", md="20px 24px"),
                            scroll_margin_top="120px",
                        ),
                    ),
                ),
            ),
            # Footer
            rx.center(
                rx.text(
                    "Powered by TUWAYKIFOOD · Escaneá el QR de la mesa",
                    font_size="12px", color="#CBD5E1",
                ),
                padding="24px 16px",
                width="100%",
            ),
            spacing="0",
            width="100%",
            min_height="100vh",
        ),
        background="#FFFBF7",
        max_width=rx.breakpoints(initial="100%", sm="480px"),
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
        class_name="light",
    )
