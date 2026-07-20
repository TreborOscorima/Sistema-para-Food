"""Carta digital publica — accesible por QR sin login."""

from __future__ import annotations

import reflex as rx

from app.components.shared import (
    ACCENT, ACCENT_HOVER, ACCENT_TEXT,
    DANGER_SOLID, DANGER_TEXT,
    DARK_600, DARK_700, DARK_800,
    INFO_SOLID,
    PAGE_BACKGROUND,
    SUCCESS_SOLID,
    TEXT_MUTED, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_WHITE,
)
from app.states.food_state import CategoriaPublicaView, MenuPublicoState, ProductoPublicoView, PromoPublicaView
from app.states.self_order_state import CarritoItemView, SelfOrderState


def _promo_card(promo: PromoPublicaView) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.text("🔥", font_size="16px", line_height="1"),
                rx.text(
                    promo.descuento_texto,
                    font_size="14px", font_weight="800", color=TEXT_WHITE,
                    line_height="1",
                ),
                spacing="1", align="center",
            ),
            rx.text(
                promo.nombre, font_size="12px", font_weight="700",
                color="#FED7AA", line_height="1.2", no_of_lines=2,
            ),
            rx.cond(
                promo.descripcion != "",
                rx.text(
                    promo.descripcion, font_size="10px", color="#FDBA74",
                    line_height="1.3", no_of_lines=2,
                ),
                rx.fragment(),
            ),
            rx.text(
                promo.horario_texto + " · " + promo.dias_texto,
                font_size="9px", color="#FB923C", line_height="1",
            ),
            spacing="1", align="start",
        ),
        background="linear-gradient(135deg, #9A3412, #C2410C)",
        border_radius="12px",
        padding="10px 14px",
        min_width="180px",
        max_width="220px",
        flex_shrink="0",
    )


def _promos_banner() -> rx.Component:
    return rx.cond(
        MenuPublicoState.promos_activas.length() > 0,
        rx.box(
            rx.hstack(
                rx.foreach(MenuPublicoState.promos_activas, _promo_card),
                spacing="2",
                overflow_x="auto",
                width="100%",
                padding_bottom="4px",
            ),
            padding="0 16px 8px",
            width="100%",
        ),
        rx.fragment(),
    )


def _categoria_chip(cat: CategoriaPublicaView, idx: int) -> rx.Component:
    return rx.link(
        cat.emoji + " " + cat.nombre,
        href=f"#cat-{idx}",
        background=DARK_700,
        color=TEXT_MUTED,
        font_size="12px",
        font_weight="600",
        padding="6px 14px",
        border_radius="20px",
        white_space="nowrap",
        flex_shrink="0",
        _hover={"background": "rgba(234,88,12,0.15)", "color": ACCENT},
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
                loading="lazy",
            ),
            rx.center(
                rx.text(prod.emoji, font_size="32px", line_height="1"),
                width="72px", height="72px",
                background="linear-gradient(135deg,#FED7AA,#FB923C)",
                border_radius="12px", flex_shrink="0",
            ),
        ),
        rx.vstack(
            rx.text(prod.nombre, font_size="15px", font_weight="700", color=TEXT_PRIMARY, line_height="1.3"),
            rx.cond(
                prod.descripcion != "",
                rx.text(prod.descripcion, font_size="12px", color=TEXT_MUTED,
                        line_height="1.4", no_of_lines=2),
                rx.fragment(),
            ),
            rx.cond(
                prod.tags_texto != "",
                rx.text(prod.tags_texto, font_size="10px", color=TEXT_MUTED,
                        line_height="1.3"),
                rx.fragment(),
            ),
            rx.hstack(
                rx.text(prod.precio_texto, font_size="18px", font_weight="800",
                        color=ACCENT),
                rx.spacer(),
                rx.cond(
                    SelfOrderState.tiene_mesa_qr,
                    rx.button(
                        rx.hstack(
                            rx.icon(tag="plus", size=14),
                            rx.text("Agregar", font_size="12px", font_weight="700"),
                            spacing="1", align="center",
                        ),
                        on_click=SelfOrderState.agregar_al_carrito(
                            prod.id, prod.nombre, prod.precio_texto, prod.precio_float,
                        ),
                        background=ACCENT, color=TEXT_WHITE,
                        border_radius="10px", padding="6px 14px",
                        cursor="pointer", height="auto",
                        _hover={"background": ACCENT_HOVER},
                        _active={"transform": "scale(0.95)"},
                    ),
                    rx.fragment(),
                ),
                width="100%", align="center", margin_top="6px",
            ),
            spacing="0", align="start", flex="1", min_width="0",
        ),
        spacing="3", align="start", width="100%",
        background=DARK_800, border_radius="16px", padding="14px",
        box_shadow="0 1px 4px rgba(0,0,0,0.06)",
    )


def _categoria_section(cat: CategoriaPublicaView, idx: int) -> rx.Component:
    return rx.vstack(
        rx.text(cat.emoji + " " + cat.nombre, font_size="16px", font_weight="800", color=TEXT_PRIMARY),
        rx.vstack(
            rx.foreach(cat.productos, _producto_item),
            spacing="2", width="100%",
        ),
        id=f"cat-{idx}",
        spacing="3", width="100%", padding_top="4px",
        scroll_margin_top="120px",
    )


def _carrito_item(item: CarritoItemView) -> rx.Component:
    return rx.hstack(
        rx.vstack(
            rx.text(item.nombre, font_size="14px", font_weight="700",
                    color=TEXT_PRIMARY, no_of_lines=1),
            rx.text(item.precio_texto + " c/u", font_size="11px",
                    color=TEXT_MUTED),
            spacing="0", align="start", flex="1", min_width="0",
        ),
        rx.hstack(
            rx.button(
                rx.icon(tag="minus", size=14),
                on_click=SelfOrderState.quitar_del_carrito(item.producto_id),
                background=DARK_700, color=TEXT_MUTED,
                border_radius="8px", padding="4px",
                cursor="pointer", height="auto", min_width="28px",
                _hover={"background": DARK_600},
            ),
            rx.text(item.cantidad.to_string(), font_size="14px",
                    font_weight="700", color=TEXT_PRIMARY,
                    min_width="20px", text_align="center"),
            rx.button(
                rx.icon(tag="plus", size=14),
                on_click=SelfOrderState.agregar_al_carrito(
                    item.producto_id, item.nombre, item.precio_texto, item.precio_float,
                ),
                background="rgba(234,88,12,0.15)", color=ACCENT,
                border_radius="8px", padding="4px",
                cursor="pointer", height="auto", min_width="28px",
                _hover={"background": "rgba(234,88,12,0.25)"},
            ),
            spacing="1", align="center",
        ),
        rx.text(item.subtotal_texto, font_size="14px", font_weight="800",
                color=ACCENT, min_width="70px", text_align="right"),
        width="100%", align="center", padding="8px 0",
        border_bottom=f"1px solid {DARK_700}",
    )


def _carrito_drawer() -> rx.Component:
    return rx.drawer.root(
        rx.drawer.content(
            rx.vstack(
                rx.hstack(
                    rx.text("Tu pedido", font_size="18px", font_weight="800",
                            color=TEXT_PRIMARY),
                    rx.spacer(),
                    rx.drawer.close(
                        rx.icon(tag="x", size=20, color=TEXT_MUTED,
                                cursor="pointer"),
                    ),
                    width="100%", align="center",
                ),
                rx.cond(
                    SelfOrderState.tiene_mesa_qr,
                    rx.badge(
                        SelfOrderState.mesa_nombre_qr,
                        background="rgba(59,130,246,0.12)", color=INFO_SOLID,
                        border_radius="8px", font_size="12px",
                        font_weight="700", padding="4px 10px",
                    ),
                    rx.fragment(),
                ),
                rx.cond(
                    SelfOrderState.carrito_count > 0,
                    rx.vstack(
                        rx.vstack(
                            rx.foreach(SelfOrderState.carrito, _carrito_item),
                            spacing="0", width="100%",
                            max_height="50vh", overflow_y="auto",
                        ),
                        rx.hstack(
                            rx.text("Total", font_size="16px", font_weight="700",
                                    color=TEXT_PRIMARY),
                            rx.spacer(),
                            rx.text(SelfOrderState.carrito_total_texto,
                                    font_size="20px", font_weight="800",
                                    color=ACCENT),
                            width="100%", align="center",
                            padding="12px 0", border_top=f"2px solid {DARK_700}",
                        ),
                        rx.input(
                            value=SelfOrderState.nombre_cliente_qr,
                            on_change=SelfOrderState.set_nombre_cliente_qr,
                            placeholder="Tu nombre (opcional)",
                            background=PAGE_BACKGROUND,
                            border=f"1px solid {DARK_700}",
                            border_radius="10px", color=TEXT_PRIMARY,
                            font_size="14px",
                            _focus={"border_color": ACCENT},
                        ),
                        rx.cond(
                            SelfOrderState.pedido_error != "",
                            rx.text(SelfOrderState.pedido_error,
                                    font_size="12px", color=DANGER_SOLID,
                                    font_weight="600"),
                            rx.fragment(),
                        ),
                        rx.button(
                            rx.hstack(
                                rx.icon(tag="send", size=16),
                                rx.text("Enviar pedido", font_size="15px",
                                        font_weight="800"),
                                spacing="2", align="center",
                            ),
                            on_click=SelfOrderState.enviar_self_order,
                            background=ACCENT, color=TEXT_WHITE,
                            border_radius="12px", width="100%",
                            padding_y="12px", cursor="pointer",
                            _hover={"background": ACCENT_HOVER},
                        ),
                        rx.button(
                            "Vaciar carrito",
                            on_click=SelfOrderState.vaciar_carrito,
                            background="transparent", color=TEXT_MUTED,
                            border=f"1px solid {DARK_700}",
                            border_radius="10px", width="100%",
                            padding_y="8px", cursor="pointer",
                            font_size="13px",
                            _hover={"background": "rgba(239,68,68,0.10)", "color": "#F87171"},
                        ),
                        spacing="3", width="100%",
                    ),
                    rx.center(
                        rx.vstack(
                            rx.icon(tag="shopping_cart", size=40, color="#CBD5E1"),
                            rx.text("Carrito vacío", font_size="14px",
                                    color=TEXT_MUTED),
                            spacing="2", align="center",
                        ),
                        padding_y="48px", width="100%",
                    ),
                ),
                spacing="3", width="100%",
            ),
            background=DARK_800,
            padding="20px",
            max_width="420px",
            width="100%",
        ),
        open=SelfOrderState.carrito_visible,
        on_open_change=SelfOrderState.set_carrito_visible,
        direction="bottom",
    )


def _carrito_fab() -> rx.Component:
    return rx.cond(
        SelfOrderState.tiene_mesa_qr,
        rx.box(
            rx.button(
                rx.hstack(
                    rx.icon(tag="shopping_cart", size=20),
                    rx.cond(
                        SelfOrderState.carrito_count > 0,
                        rx.badge(
                            SelfOrderState.carrito_count.to_string(),
                            background=DARK_800, color=ACCENT,
                            border_radius="50%", font_size="11px",
                            font_weight="800", padding="2px 6px",
                            position="absolute", top="-6px", right="-6px",
                        ),
                        rx.fragment(),
                    ),
                    spacing="0", position="relative",
                ),
                on_click=SelfOrderState.toggle_carrito,
                background=ACCENT, color=TEXT_WHITE,
                border_radius="50%",
                width="56px", height="56px",
                cursor="pointer",
                box_shadow="0 4px 16px rgba(234,88,12,0.4)",
                _hover={"background": ACCENT_HOVER, "transform": "scale(1.05)"},
                transition="all 0.15s ease",
            ),
            position="fixed", bottom="24px", right="24px",
            z_index="20",
        ),
        rx.fragment(),
    )


def _pedido_enviado_screen() -> rx.Component:
    return rx.center(
        rx.vstack(
            rx.icon(tag="circle_check", size=64, color=SUCCESS_SOLID),
            rx.text("Pedido enviado", font_size="22px", font_weight="800",
                    color=TEXT_PRIMARY),
            rx.text(
                "Tu pedido fue enviado al mozo para aprobación. "
                "Te atenderán en unos minutos.",
                font_size="14px", color=TEXT_MUTED,
                text_align="center", max_width="300px",
            ),
            rx.cond(
                SelfOrderState.tiene_mesa_qr,
                rx.badge(
                    SelfOrderState.mesa_nombre_qr,
                    background="rgba(59,130,246,0.12)", color=INFO_SOLID,
                    border_radius="8px", font_size="14px",
                    font_weight="700", padding="6px 14px",
                ),
                rx.fragment(),
            ),
            rx.button(
                "Ver carta nuevamente",
                on_click=SelfOrderState.volver_a_carta,
                background=ACCENT, color=TEXT_WHITE,
                border_radius="12px", padding_x="24px", padding_y="10px",
                cursor="pointer", font_weight="700",
                _hover={"background": ACCENT_HOVER},
                margin_top="8px",
            ),
            spacing="3", align="center",
        ),
        min_height="100vh", padding="48px 24px",
        background=PAGE_BACKGROUND,
    )


def _menu_content() -> rx.Component:
    return rx.box(
        rx.vstack(
            # Header sticky con nombre + categorías
            rx.box(
                rx.hstack(
                    rx.vstack(
                        rx.text(MenuPublicoState.nombre_local, font_size="20px", font_weight="800",
                                color=TEXT_PRIMARY, letter_spacing="-0.02em", line_height="1.2"),
                        rx.text("Menú digital", font_size="13px", color=TEXT_MUTED),
                        spacing="0", align="start",
                    ),
                    rx.spacer(),
                    rx.image(
                        src=rx.cond(
                            MenuPublicoState.logo_url_local != "",
                            MenuPublicoState.logo_url_local,
                            "/TUWAYKIFOODFAVICON.png",
                        ),
                        width="44px", height="44px", border_radius="12px",
                        object_fit="cover",
                        alt=MenuPublicoState.nombre_local,
                        box_shadow="0 4px 12px rgba(234,88,12,0.3)",
                    ),
                    width="100%", align="center", margin_bottom="14px",
                ),
                rx.cond(
                    MenuPublicoState.categorias_menu.length() > 0,
                    rx.vstack(
                        rx.hstack(
                            rx.link(
                                "Todo", href="#menu-categorias",
                                background=ACCENT, color=TEXT_WHITE,
                                font_size="12px", font_weight="700",
                                padding="6px 14px", border_radius="20px",
                                white_space="nowrap", flex_shrink="0",
                            ),
                            rx.foreach(
                                MenuPublicoState.categorias_menu,
                                lambda cat, idx: _categoria_chip(cat, idx),
                            ),
                            spacing="2", overflow_x="auto", width="100%",
                        ),
                        rx.hstack(
                            rx.icon(tag="search", size=16, color=TEXT_MUTED, flex_shrink="0"),
                            rx.input(
                                placeholder="Buscar plato...",
                                value=MenuPublicoState.busqueda_menu,
                                on_change=MenuPublicoState.set_busqueda_menu,
                                border="none", outline="none",
                                font_size="14px", color=TEXT_PRIMARY,
                                padding="0", flex="1",
                                _focus={"border": "none", "box_shadow": "none"},
                                _placeholder={"color": TEXT_MUTED},
                            ),
                            rx.cond(
                                MenuPublicoState.busqueda_menu != "",
                                rx.icon(
                                    tag="x", size=16, color=TEXT_MUTED,
                                    cursor="pointer", flex_shrink="0",
                                    on_click=MenuPublicoState.set_busqueda_menu(""),
                                ),
                                rx.fragment(),
                            ),
                            spacing="2", align="center", width="100%",
                            background=DARK_700, border_radius="12px",
                            padding="8px 12px",
                        ),
                        spacing="2", width="100%",
                    ),
                    rx.fragment(),
                ),
                background=DARK_800,
                border_bottom=f"1px solid {DARK_700}",
                padding=rx.breakpoints(initial="16px 16px 12px", md="20px 24px 14px"),
                position="sticky", top="0", z_index="10",
                width="100%",
            ),
            # Promos activas
            _promos_banner(),
            # Loading
            rx.cond(
                MenuPublicoState.cargando,
                rx.center(
                    rx.vstack(
                        rx.spinner(color=ACCENT, size="3"),
                        rx.text("Cargando carta...", font_size="13px", color=TEXT_MUTED),
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
                            rx.text("Carta no encontrada", font_size="17px", font_weight="700", color=TEXT_MUTED),
                            rx.text(
                                "El restaurante no tiene carta digital activa.",
                                font_size="13px",
                                color=TEXT_MUTED,
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
                                rx.text("Carta sin productos", font_size="15px", font_weight="600", color=TEXT_MUTED),
                                spacing="3",
                                align="center",
                            ),
                            padding_y="80px",
                            width="100%",
                        ),
                        rx.cond(
                            MenuPublicoState.categorias_menu_filtradas.length() == 0,
                            rx.center(
                                rx.vstack(
                                    rx.icon(tag="search_x", size=40, color="#CBD5E1"),
                                    rx.text("Sin resultados", font_size="15px", font_weight="600", color=TEXT_MUTED),
                                    rx.text("Pruebe con otro término", font_size="13px", color=TEXT_MUTED),
                                    spacing="2", align="center",
                                ),
                                padding_y="60px", width="100%",
                            ),
                            rx.vstack(
                                rx.foreach(
                                    MenuPublicoState.categorias_menu_filtradas,
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
            ),
            # Footer
            rx.center(
                rx.text(
                    "Powered by TUWAYKIFOOD · Escanee el QR de la mesa",
                    font_size="12px", color="#CBD5E1",
                ),
                padding="24px 16px",
                width="100%",
            ),
            spacing="0",
            width="100%",
            min_height="100vh",
        ),
        background=PAGE_BACKGROUND,
        max_width=rx.breakpoints(initial="100%", sm="480px"),
        margin="0 auto",
        min_height="100vh",
        box_shadow=rx.breakpoints(initial="none", sm="0 0 40px rgba(0,0,0,0.08)"),
    )


@rx.page(route="/menu/[slug]", on_load=[MenuPublicoState.on_load, SelfOrderState.on_load], title="TUWAYKIFOOD | Carta Digital")
def menu_publico_page() -> rx.Component:
    return rx.box(
        rx.cond(
            SelfOrderState.pedido_enviado,
            _pedido_enviado_screen(),
            rx.fragment(
                _menu_content(),
                _carrito_fab(),
                _carrito_drawer(),
            ),
        ),
        background=PAGE_BACKGROUND,
        min_height="100vh",
    )
