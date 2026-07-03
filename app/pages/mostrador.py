"""Pagina de mostrador — pedidos para llevar."""

from __future__ import annotations

import reflex as rx

from app.components.shared import app_shell, cumpleanos_banner
from app.states.food_state import (
    CarritoItem,
    FoodState,
    MostradorEntregadoView,
    MostradorPendienteView,
    ProductoView,
)


def _producto_card(producto: ProductoView) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.text(producto.emoji, font_size="24px", line_height="1"),
                rx.spacer(),
                rx.box(
                    rx.icon(tag="plus", size=13, color="#FFFFFF"),
                    width="24px", height="24px", border_radius="7px",
                    background="#EA580C", display="flex",
                    align_items="center", justify_content="center",
                    flex_shrink="0",
                ),
                width="100%", align="center",
            ),
            rx.text(
                producto.nombre,
                font_size="13px",
                font_weight="600",
                color="#F1F5F9",
                no_of_lines=2,
            ),
            rx.text(producto.precio_texto, font_size="14px", font_weight="700", color="#EA580C"),
            spacing="2",
            align="start",
        ),
        on_click=FoodState.agregar_producto_mostrador(producto.id),
        background="#1E293B",
        border="2px solid #334155",
        border_radius="10px",
        padding="12px",
        cursor="pointer",
        _hover={"border": "2px solid #EA580C"},
        transition="all 0.15s ease",
    )


def _carrito_item(item: CarritoItem) -> rx.Component:
    return rx.hstack(
        rx.text(item.nombre, font_size="13px", color="#F1F5F9", flex="1"),
        rx.hstack(
            rx.button(
                "-",
                on_click=FoodState.restar_producto_mostrador(item.producto_id),
                width="24px",
                height="24px",
                background="#334155",
                color="#FCA5A5",
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
                background="#EA580C",
                color="#FFFFFF",
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
        rx.text(item.subtotal_texto, font_size="12px", color="#94A3B8", min_width="56px", text_align="right"),
        width="100%",
        align="center",
    )


def _pendiente_card(pedido: MostradorPendienteView) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.text(pedido.cliente_nombre, font_size="13px", font_weight="700", color="#FFFFFF"),
                rx.spacer(),
                rx.cond(
                    pedido.en_cocina,
                    rx.badge("En cocina", background="#0F172A", color="#FCD34D",
                             border="1px solid #FCD34D", border_radius="20px",
                             font_size="10px", font_weight="700", padding_x="8px"),
                    rx.badge("Listo", background="#052E16", color="#4ADE80",
                             border="1px solid #4ADE80", border_radius="20px",
                             font_size="10px", font_weight="700", padding_x="8px"),
                ),
                width="100%", align="center",
            ),
            rx.text(pedido.items_resumen, font_size="11px", color="#94A3B8", no_of_lines=2),
            rx.hstack(
                rx.text(pedido.total_texto, font_size="13px", font_weight="800", color="#EA580C"),
                rx.spacer(),
                rx.text(pedido.hora_texto, font_size="11px", color="#64748B"),
                width="100%", align="center",
            ),
            spacing="1",
            width="100%",
        ),
        background="#0F172A",
        border="1px solid #334155",
        border_radius="10px",
        padding="12px",
    )


def _entregado_card(pedido: MostradorEntregadoView) -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.vstack(
                rx.text(pedido.cliente_nombre, font_size="13px", font_weight="600", color="#F1F5F9"),
                rx.text(pedido.items_resumen, font_size="11px", color="#64748B"),
                spacing="0",
                align="start",
            ),
            rx.spacer(),
            rx.vstack(
                rx.text(pedido.total_texto, font_size="13px", font_weight="700", color="#4ADE80"),
                rx.text(pedido.hora_texto, font_size="11px", color="#64748B"),
                align="end",
                spacing="0",
            ),
            width="100%",
            align="center",
        ),
        background="#1E293B",
        border="1px solid #334155",
        border_radius="8px",
        padding="10px 14px",
    )


def _mostrador_content() -> rx.Component:
    return rx.vstack(
        cumpleanos_banner(),
        rx.vstack(
            rx.text("Mostrador", font_size="22px", font_weight="800", color="#FFFFFF"),
            rx.text("Pedidos para llevar", font_size="13px", color="#94A3B8"),
            spacing="0",
        ),
        rx.flex(
            # ─── Panel izq: menu (scroll) + carrito (fijo abajo) ──────────
            rx.box(
                # ── zona scrolleable: cliente + filtros + productos ────────
                rx.box(
                    rx.vstack(
                        rx.text("Nuevo pedido para llevar", font_size="14px", font_weight="700", color="#EA580C"),
                        rx.input(
                            placeholder="Nombre del cliente (opcional)",
                            value=FoodState.mostrador_cliente_nombre,
                            on_change=FoodState.set_mostrador_cliente_nombre,
                            background="#0F172A",
                            border="1px solid #334155",
                            color="#F1F5F9",
                            border_radius="8px",
                            padding_x="12px",
                            padding_y="8px",
                            font_size="13px",
                            width="100%",
                            _focus={"border_color": "#EA580C"},
                        ),
                        rx.hstack(
                            rx.button(
                                "🍖 Todos",
                                on_click=FoodState.seleccionar_mostrador_categoria(0),
                                background=rx.cond(FoodState.mostrador_categoria_activa_id == 0, "#EA580C", "#1E293B"),
                                color=rx.cond(FoodState.mostrador_categoria_activa_id == 0, "#FFFFFF", "#94A3B8"),
                                border=rx.cond(FoodState.mostrador_categoria_activa_id == 0, "1px solid #EA580C", "1px solid #334155"),
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
                                    cat.emoji + " " + cat.nombre,
                                    on_click=FoodState.seleccionar_mostrador_categoria(cat.id),
                                    background=rx.cond(FoodState.mostrador_categoria_activa_id == cat.id, "#EA580C", "#1E293B"),
                                    color=rx.cond(FoodState.mostrador_categoria_activa_id == cat.id, "#FFFFFF", "#94A3B8"),
                                    border=rx.cond(FoodState.mostrador_categoria_activa_id == cat.id, "1px solid #EA580C", "1px solid #334155"),
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
                            columns=rx.breakpoints(initial="1", sm="2"),
                            gap="8px",
                            width="100%",
                        ),
                        spacing="3",
                        width="100%",
                    ),
                    class_name="twk-pos-scroll",
                ),
                # ── zona fija abajo: carrito + cobro ──────────────────────
                rx.box(
                    rx.vstack(
                        rx.hstack(
                            rx.text("Carrito", font_size="13px", font_weight="700", color="#94A3B8"),
                            rx.spacer(),
                            rx.vstack(
                                rx.cond(
                                    FoodState.mostrador_cupon_id_aplicado > 0,
                                    rx.text(FoodState.total_mostrador_texto,
                                            font_size="12px", color="#64748B",
                                            text_decoration="line-through"),
                                    rx.fragment(),
                                ),
                                rx.text(FoodState.total_mostrador_neto_texto,
                                        font_size="16px", font_weight="800", color="#FFFFFF"),
                                spacing="0", align="end",
                            ),
                            width="100%",
                            align="center",
                        ),
                        rx.cond(
                            FoodState.mostrador_carrito.length() == 0,
                            rx.center(
                                rx.text("Sin productos", font_size="12px", color="#64748B"),
                                padding_y="4px",
                            ),
                            rx.vstack(
                                rx.foreach(FoodState.mostrador_carrito, _carrito_item),
                                spacing="1",
                                width="100%",
                                max_height="120px",
                                overflow_y="auto",
                            ),
                        ),
                        rx.hstack(
                            rx.button(
                                "Limpiar",
                                on_click=FoodState.limpiar_carrito_mostrador,
                                background="#1E293B",
                                color="#FCA5A5",
                                border="1px solid #334155",
                                border_radius="8px",
                                font_size="12px",
                                cursor="pointer",
                                _hover={"border_color": "#DC2626"},
                            ),
                            rx.button(
                                rx.hstack(
                                    rx.icon(tag="send", size=14, color="#FFFFFF"),
                                    rx.text("Enviar a cocina", font_size="13px", font_weight="700", color="#FFFFFF"),
                                    spacing="2", align="center",
                                ),
                                on_click=FoodState.enviar_pedido_mostrador,
                                background="#EA580C",
                                color="#FFFFFF",
                                border_radius="8px",
                                cursor="pointer",
                                _hover={"background": "#C2410C"},
                                flex="1",
                            ),
                            spacing="2",
                            width="100%",
                            max_width="520px",
                        ),
                        spacing="2",
                        width="100%",
                    ),
                    class_name="twk-pos-foot",
                ),
                class_name="twk-panel twk-pos-col",
            ),
            rx.divider(orientation="vertical", border_color="#334155", height="auto",
                       class_name="twk-sep"),
            # ─── Panel der: pendientes + cobrados ────────────────────────
            rx.vstack(
                rx.hstack(
                    rx.icon(tag="clock", size=13, color="#FCD34D"),
                    rx.text("Pendientes de cobro", font_size="14px", font_weight="700", color="#FCD34D"),
                    spacing="2", align="center",
                ),
                rx.cond(
                    FoodState.pedidos_mostrador_pendientes.length() == 0,
                    rx.center(
                        rx.text("Sin pedidos en espera", font_size="12px", color="#64748B"),
                        padding_y="16px",
                    ),
                    rx.vstack(
                        rx.foreach(FoodState.pedidos_mostrador_pendientes, _pendiente_card),
                        spacing="2",
                        width="100%",
                    ),
                ),
                rx.divider(border_color="#334155"),
                rx.text("Cobrados hoy", font_size="13px", font_weight="700", color="#94A3B8"),
                rx.cond(
                    FoodState.pedidos_mostrador_entregados.length() == 0,
                    rx.center(
                        rx.text("Sin historial", font_size="12px", color="#64748B"),
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
                max_width=rx.breakpoints(initial="100%", md="340px"),
                class_name="twk-panel",
            ),
            gap="5",
            width="100%",
            align="start",
            class_name="twk-cols-md",
        ),
        spacing="5",
        width="100%",
    )


@rx.page(
    route="/mostrador",
    on_load=[FoodState.on_load_mostrador, FoodState.start_mostrador_polling,
             FoodState.cargar_clientes],
    title="TUWAYKIFOOD | Mostrador",
)
def mostrador_page() -> rx.Component:
    return app_shell(_mostrador_content(), page_key="mostrador", dark=True)
