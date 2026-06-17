"""Pagina de mostrador — pedidos para llevar."""

from __future__ import annotations

import reflex as rx

from app.components.shared import app_shell
from app.states.food_state import (
    CarritoItem,
    FoodState,
    MostradorEntregaView,
    MostradorEntregadoView,
    ProductoView,
)


def _producto_card(producto: ProductoView) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.text(
                producto.nombre,
                font_size="13px",
                font_weight="600",
                color="#0F172A",
                no_of_lines=2,
            ),
            rx.text(producto.precio_texto, font_size="14px", font_weight="700", color="#EA580C"),
            rx.button(
                "+",
                on_click=FoodState.agregar_producto_mostrador(producto.id),
                width="100%",
                background="#EA580C",
                color="#FFFFFF",
                border_radius="6px",
                font_size="16px",
                cursor="pointer",
                _hover={"background": "#C2410C"},
            ),
            spacing="2",
            align="start",
        ),
        background="#FFFFFF",
        border="1px solid #E2E8F0",
        border_radius="10px",
        padding="12px",
        box_shadow="0 1px 2px rgba(0,0,0,0.05)",
        _hover={"border": "1px solid #FED7AA", "box_shadow": "0 2px 8px rgba(234,88,12,0.10)"},
        transition="all 0.15s ease",
    )


def _carrito_item(item: CarritoItem) -> rx.Component:
    return rx.hstack(
        rx.text(item.nombre, font_size="13px", color="#334155", flex="1"),
        rx.hstack(
            rx.button(
                "-",
                on_click=FoodState.restar_producto_mostrador(item.producto_id),
                width="24px",
                height="24px",
                background="#FEF2F2",
                color="#B91C1C",
                border="none",
                border_radius="5px",
                font_size="14px",
                cursor="pointer",
                padding="0",
                _hover={"opacity": "0.8"},
            ),
            rx.text(item.cantidad.to_string(), font_size="13px", font_weight="700", color="#EA580C", min_width="18px", text_align="center"),
            rx.button(
                "+",
                on_click=FoodState.agregar_producto_mostrador(item.producto_id),
                width="24px",
                height="24px",
                background="#F0FDF4",
                color="#15803D",
                border="none",
                border_radius="5px",
                font_size="14px",
                cursor="pointer",
                padding="0",
                _hover={"opacity": "0.8"},
            ),
            spacing="1",
            align="center",
        ),
        rx.text(item.subtotal_texto, font_size="12px", color="#64748B", min_width="56px", text_align="right"),
        width="100%",
        align="center",
    )


def _listo_card(pedido: MostradorEntregaView) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.text(pedido.cliente_nombre, font_size="14px", font_weight="700", color="#0F172A"),
                rx.spacer(),
                rx.text(pedido.hora_texto, font_size="11px", color="#64748B"),
                width="100%",
            ),
            rx.vstack(
                rx.foreach(
                    pedido.items_lines,
                    lambda line: rx.text(line, font_size="12px", color="#64748B"),
                ),
                spacing="0",
                align="start",
                width="100%",
            ),
            rx.button(
                "Entregar al cliente",
                on_click=FoodState.entregar_pedido_mostrador(pedido.pedido_id),
                width="100%",
                background="#15803D",
                color="#FFFFFF",
                border_radius="8px",
                font_size="13px",
                font_weight="700",
                cursor="pointer",
                padding_y="8px",
                _hover={"background": "#166534"},
            ),
            spacing="2",
            width="100%",
        ),
        background="#F0FDF4",
        border="2px solid #BBF7D0",
        border_radius="12px",
        padding="14px",
        box_shadow="0 1px 3px rgba(0,0,0,0.06)",
    )


def _entregado_card(pedido: MostradorEntregadoView) -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.vstack(
                rx.text(pedido.cliente_nombre, font_size="13px", font_weight="600", color="#334155"),
                rx.text(pedido.items_resumen, font_size="11px", color="#94A3B8"),
                spacing="0",
                align="start",
            ),
            rx.spacer(),
            rx.vstack(
                rx.text(pedido.total_texto, font_size="13px", font_weight="700", color="#15803D"),
                rx.text(pedido.hora_texto, font_size="11px", color="#94A3B8"),
                align="end",
                spacing="0",
            ),
            width="100%",
            align="center",
        ),
        background="#F8FAFC",
        border="1px solid #E2E8F0",
        border_radius="8px",
        padding="10px 14px",
    )


def _mostrador_content() -> rx.Component:
    return rx.vstack(
        rx.text("Mostrador", font_size="22px", font_weight="800", color="#0F172A"),
        rx.hstack(
            # ─── Panel izq: menu + carrito ────────────────────────────────
            rx.vstack(
                rx.text("Nuevo pedido para llevar", font_size="14px", font_weight="700", color="#EA580C"),
                rx.input(
                    placeholder="Nombre del cliente (opcional)",
                    value=FoodState.mostrador_cliente_nombre,
                    on_change=FoodState.set_mostrador_cliente_nombre,
                    background="#FFFFFF",
                    border="1px solid #E2E8F0",
                    color="#0F172A",
                    border_radius="8px",
                    padding_x="12px",
                    padding_y="8px",
                    font_size="13px",
                    width="100%",
                ),
                rx.hstack(
                    rx.button(
                        "Todos",
                        on_click=FoodState.seleccionar_mostrador_categoria(0),
                        background=rx.cond(FoodState.mostrador_categoria_activa_id == 0, "#FFF7ED", "#F1F5F9"),
                        color=rx.cond(FoodState.mostrador_categoria_activa_id == 0, "#EA580C", "#64748B"),
                        border=rx.cond(FoodState.mostrador_categoria_activa_id == 0, "1px solid #FED7AA", "1px solid #E2E8F0"),
                        border_radius="6px",
                        font_size="12px",
                        cursor="pointer",
                        padding_x="10px",
                        padding_y="5px",
                        _hover={"opacity": "0.85"},
                    ),
                    rx.foreach(
                        FoodState.categorias_activas,
                        lambda cat: rx.button(
                            cat.nombre,
                            on_click=FoodState.seleccionar_mostrador_categoria(cat.id),
                            background=rx.cond(FoodState.mostrador_categoria_activa_id == cat.id, "#FFF7ED", "#F1F5F9"),
                            color=rx.cond(FoodState.mostrador_categoria_activa_id == cat.id, "#EA580C", "#64748B"),
                            border=rx.cond(FoodState.mostrador_categoria_activa_id == cat.id, "1px solid #FED7AA", "1px solid #E2E8F0"),
                            border_radius="6px",
                            font_size="12px",
                            cursor="pointer",
                            padding_x="10px",
                            padding_y="5px",
                            _hover={"opacity": "0.85"},
                        ),
                    ),
                    flex_wrap="wrap",
                    gap="6px",
                    width="100%",
                ),
                rx.grid(
                    rx.foreach(FoodState.mostrador_productos_filtrados, _producto_card),
                    columns="2",
                    gap="8px",
                    width="100%",
                ),
                rx.divider(border_color="#E2E8F0"),
                rx.text("Carrito", font_size="13px", font_weight="700", color="#64748B"),
                rx.cond(
                    FoodState.mostrador_carrito.length() == 0,
                    rx.center(
                        rx.text("Sin productos", font_size="12px", color="#94A3B8"),
                        padding_y="8px",
                    ),
                    rx.vstack(
                        rx.foreach(FoodState.mostrador_carrito, _carrito_item),
                        spacing="1",
                        width="100%",
                    ),
                ),
                rx.hstack(
                    rx.text("Total:", font_size="14px", color="#64748B"),
                    rx.spacer(),
                    rx.text(FoodState.total_mostrador_texto, font_size="16px", font_weight="800", color="#0F172A"),
                    width="100%",
                ),
                # ── Método de pago ──────────────────────────────────────────
                rx.vstack(
                    rx.text("Método de pago", font_size="12px", font_weight="700", color="#64748B"),
                    rx.hstack(
                        *[
                            rx.button(
                                rx.hstack(
                                    rx.icon(tag=icon, size=14,
                                            color=rx.cond(FoodState.mostrador_metodo_pago == val, "#FFFFFF", "#64748B")),
                                    rx.text(label, font_size="12px", font_weight="700",
                                            color=rx.cond(FoodState.mostrador_metodo_pago == val, "#FFFFFF", "#64748B")),
                                    spacing="1", align="center",
                                ),
                                on_click=FoodState.seleccionar_mostrador_metodo(val),
                                background=rx.cond(FoodState.mostrador_metodo_pago == val, "#EA580C", "#F8FAFC"),
                                border=rx.cond(FoodState.mostrador_metodo_pago == val, "2px solid #EA580C", "2px solid #E2E8F0"),
                                border_radius="8px",
                                padding="6px 0",
                                cursor="pointer",
                                flex="1",
                                _hover={"border": "2px solid #EA580C"},
                            )
                            for val, label, icon in [
                                ("efectivo", "Efectivo", "banknote"),
                                ("tarjeta", "Tarjeta", "credit_card"),
                                ("qr", "QR / Yape", "qr_code"),
                            ]
                        ],
                        spacing="2",
                        width="100%",
                    ),
                    spacing="1",
                    width="100%",
                ),
                rx.hstack(
                    rx.button(
                        "Limpiar",
                        on_click=FoodState.limpiar_carrito_mostrador,
                        background="#FEF2F2",
                        color="#B91C1C",
                        border="1px solid #FECACA",
                        border_radius="8px",
                        font_size="12px",
                        cursor="pointer",
                        _hover={"opacity": "0.85"},
                    ),
                    rx.button(
                        "Cobrar y Enviar a Cocina",
                        on_click=FoodState.cobrar_y_enviar_mostrador,
                        background="#EA580C",
                        color="#FFFFFF",
                        border_radius="8px",
                        font_size="13px",
                        font_weight="700",
                        cursor="pointer",
                        _hover={"background": "#C2410C"},
                        flex="1",
                    ),
                    spacing="2",
                    width="100%",
                ),
                spacing="3",
                flex="1",
                min_width="0",
            ),
            rx.divider(orientation="vertical", border_color="#E2E8F0", height="auto"),
            # ─── Panel der: listos + historial ───────────────────────────
            rx.vstack(
                rx.text("Listos para entrega", font_size="14px", font_weight="700", color="#15803D"),
                rx.cond(
                    FoodState.pedidos_mostrador_listos.length() == 0,
                    rx.center(
                        rx.text("Sin pedidos listos", font_size="12px", color="#94A3B8"),
                        padding_y="16px",
                    ),
                    rx.vstack(
                        rx.foreach(FoodState.pedidos_mostrador_listos, _listo_card),
                        spacing="3",
                        width="100%",
                    ),
                ),
                rx.divider(border_color="#E2E8F0"),
                rx.text("Entregados hoy", font_size="13px", font_weight="700", color="#64748B"),
                rx.cond(
                    FoodState.pedidos_mostrador_entregados.length() == 0,
                    rx.center(
                        rx.text("Sin historial", font_size="12px", color="#94A3B8"),
                        padding_y="16px",
                    ),
                    rx.vstack(
                        rx.foreach(FoodState.pedidos_mostrador_entregados, _entregado_card),
                        spacing="2",
                        width="100%",
                    ),
                ),
                spacing="3",
                flex="1",
                min_width="0",
                max_width="340px",
            ),
            spacing="5",
            width="100%",
            align="start",
            flex_wrap=rx.breakpoints(initial="wrap", md="nowrap"),
        ),
        spacing="5",
        width="100%",
    )


@rx.page(
    route="/mostrador",
    on_load=[FoodState.on_load_mostrador, FoodState.start_mostrador_polling],
)
def mostrador_page() -> rx.Component:
    return app_shell(_mostrador_content(), page_key="mostrador")
