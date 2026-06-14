"""Pagina de mozos — mapa de salon + menu + carrito."""

from __future__ import annotations

import reflex as rx

from app.components.shared import app_shell, section_card, surface_card
from app.states.food_state import CarritoItem, FoodState, HistorialItem, MesaView, ProductoView


# ─── Tarjeta de mesa ─────────────────────────────────────────────────────────

def _mesa_card(mesa: MesaView) -> rx.Component:
    selected = FoodState.mesa_seleccionada_id == mesa.id
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.text(
                    mesa.nombre,
                    font_size="14px",
                    font_weight="700",
                    color=rx.cond(selected, "#EA580C", "#0F172A"),
                ),
                rx.spacer(),
                rx.badge(
                    mesa.estado_label,
                    background=mesa.badge_bg,
                    color=mesa.badge_text,
                    border_radius="6px",
                    font_size="10px",
                    padding="2px 7px",
                ),
                width="100%",
            ),
            rx.cond(
                mesa.total_abierto > 0,
                rx.text(
                    mesa.total_abierto_texto,
                    font_size="13px",
                    font_weight="600",
                    color="#64748B",
                ),
                rx.fragment(),
            ),
            rx.cond(
                mesa.tiene_items_listos,
                rx.hstack(
                    rx.text(
                        mesa.items_listos_count.to_string() + " items listos",
                        font_size="11px",
                        color="#B45309",
                        font_weight="600",
                    ),
                    spacing="1",
                ),
                rx.fragment(),
            ),
            spacing="1",
            align="start",
        ),
        background=rx.cond(selected, "#FFF7ED", mesa.card_bg),
        border=rx.cond(selected, "2px solid #EA580C", mesa.card_border),
        border_radius="10px",
        padding="12px",
        cursor="pointer",
        on_click=FoodState.seleccionar_mesa(mesa.id),
        _hover={"border": "2px solid rgba(234,88,12,0.45)", "transform": "translateY(-1px)"},
        transition="all 0.15s ease",
        min_width="140px",
        box_shadow="0 1px 3px rgba(0,0,0,0.06)",
    )


# ─── Salon (mapa de mesas) ────────────────────────────────────────────────────

def _salon_content() -> rx.Component:
    return rx.vstack(
        rx.cond(
            FoodState.mesas_con_alerta_entrega > 0,
            rx.box(
                rx.text(
                    FoodState.mesas_con_alerta_entrega.to_string() + " mesa(s) con items listos para entregar",
                    font_size="13px",
                    font_weight="600",
                    color="#B45309",
                ),
                background="#FFFBEB",
                border="1px solid #FDE68A",
                border_radius="8px",
                padding="8px 14px",
                width="100%",
            ),
            rx.fragment(),
        ),
        rx.cond(
            FoodState.mesas.length() == 0,
            rx.center(
                rx.text("No hay mesas configuradas.", font_size="14px", color="#94A3B8"),
                padding_y="40px",
            ),
            rx.flex(
                rx.foreach(FoodState.mesas, _mesa_card),
                flex_wrap="wrap",
                gap="12px",
                width="100%",
            ),
        ),
        spacing="3",
        width="100%",
    )


# ─── Carrito ──────────────────────────────────────────────────────────────────

def _carrito_item_row(item: CarritoItem) -> rx.Component:
    return rx.hstack(
        rx.vstack(
            rx.text(item.nombre, font_size="13px", font_weight="600", color="#0F172A"),
            rx.cond(
                item.nota != "",
                rx.text("Nota: " + item.nota, font_size="11px", color="#94A3B8"),
                rx.fragment(),
            ),
            spacing="0",
            align="start",
        ),
        rx.spacer(),
        rx.hstack(
            rx.button(
                "-",
                on_click=FoodState.restar_producto(item.producto_id),
                width="26px",
                height="26px",
                background="#FEF2F2",
                color="#B91C1C",
                border="1px solid #FECACA",
                border_radius="6px",
                font_size="14px",
                cursor="pointer",
                _hover={"opacity": "0.8"},
                padding="0",
            ),
            rx.text(
                item.cantidad.to_string(),
                font_size="13px",
                font_weight="700",
                color="#EA580C",
                min_width="20px",
                text_align="center",
            ),
            rx.button(
                "+",
                on_click=FoodState.agregar_producto(item.producto_id),
                width="26px",
                height="26px",
                background="#F0FDF4",
                color="#15803D",
                border="1px solid #BBF7D0",
                border_radius="6px",
                font_size="14px",
                cursor="pointer",
                _hover={"opacity": "0.8"},
                padding="0",
            ),
            spacing="2",
            align="center",
        ),
        rx.text(
            item.subtotal_texto,
            font_size="12px",
            font_weight="600",
            color="#64748B",
            min_width="56px",
            text_align="right",
        ),
        width="100%",
        align="center",
        padding_y="4px",
    )


def _carrito_section() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.text(
                "Carrito — " + FoodState.mesa_seleccionada_label,
                font_size="13px",
                font_weight="700",
                color="#EA580C",
            ),
            rx.spacer(),
            rx.text(FoodState.total_carrito_texto, font_size="13px", font_weight="700", color="#0F172A"),
            width="100%",
            align="center",
        ),
        rx.cond(
            FoodState.carrito.length() == 0,
            rx.center(
                rx.text("Carrito vacio", font_size="12px", color="#94A3B8"),
                padding_y="12px",
            ),
            rx.vstack(
                rx.foreach(FoodState.carrito, _carrito_item_row),
                width="100%",
                spacing="1",
            ),
        ),
        rx.hstack(
            rx.button(
                "Limpiar",
                on_click=FoodState.limpiar_carrito,
                background="#FEF2F2",
                color="#B91C1C",
                border="1px solid #FECACA",
                border_radius="8px",
                font_size="12px",
                cursor="pointer",
                _hover={"opacity": "0.85"},
            ),
            rx.button(
                "Enviar a Cocina",
                on_click=FoodState.enviar_pedido,
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
        width="100%",
    )


# ─── Historial de pedido ──────────────────────────────────────────────────────

def _historial_item_row(item: HistorialItem) -> rx.Component:
    return rx.hstack(
        rx.vstack(
            rx.hstack(
                rx.text(item.nombre, font_size="12px", font_weight="600", color="#334155"),
                rx.text(
                    "x" + item.cantidad.to_string(),
                    font_size="12px",
                    color="#64748B",
                ),
                spacing="1",
            ),
            rx.cond(
                item.nota != "",
                rx.text("Nota: " + item.nota, font_size="10px", color="#94A3B8"),
                rx.fragment(),
            ),
            rx.text(item.enviado_en_texto, font_size="10px", color="#94A3B8"),
            spacing="0",
            align="start",
        ),
        rx.spacer(),
        rx.vstack(
            rx.badge(
                item.estado_label,
                background=item.estado_bg,
                color=item.estado_color,
                border_radius="5px",
                font_size="10px",
                padding="2px 6px",
            ),
            rx.cond(
                item.puede_entregar,
                rx.button(
                    "Entregar",
                    on_click=FoodState.entregar_item_historial(item.detalle_id),
                    background="#F0FDF4",
                    color="#15803D",
                    border="1px solid #BBF7D0",
                    border_radius="6px",
                    font_size="10px",
                    font_weight="600",
                    cursor="pointer",
                    padding_x="8px",
                    padding_y="3px",
                    _hover={"opacity": "0.85"},
                ),
                rx.fragment(),
            ),
            spacing="1",
            align="end",
        ),
        width="100%",
        align="start",
        padding_y="4px",
    )


def _historial_section() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.text("Pedido enviado", font_size="13px", font_weight="700", color="#64748B"),
            rx.spacer(),
            rx.text(FoodState.mesa_seleccionada_total_texto, font_size="13px", font_weight="700", color="#0F172A"),
            width="100%",
            align="center",
        ),
        rx.cond(
            FoodState.mesa_atendida_por_nombre != "",
            rx.text(
                "Atendido por: " + FoodState.mesa_atendida_por_nombre,
                font_size="11px",
                color="#94A3B8",
            ),
            rx.fragment(),
        ),
        rx.cond(
            FoodState.historial_pedido.length() == 0,
            rx.center(
                rx.text("Sin items enviados", font_size="12px", color="#94A3B8"),
                padding_y="12px",
            ),
            rx.vstack(
                rx.foreach(FoodState.historial_pedido, _historial_item_row),
                width="100%",
                spacing="1",
            ),
        ),
        rx.cond(
            FoodState.hay_historial_pedido,
            rx.button(
                "Solicitar Cuenta",
                on_click=FoodState.solicitar_cuenta,
                background="#FFFBEB",
                color="#B45309",
                border="1px solid #FDE68A",
                border_radius="8px",
                font_size="13px",
                font_weight="700",
                width="100%",
                cursor="pointer",
                _hover={"opacity": "0.85"},
            ),
            rx.fragment(),
        ),
        spacing="3",
        width="100%",
    )


# ─── Menu de productos ────────────────────────────────────────────────────────

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
            rx.text(
                producto.precio_texto,
                font_size="14px",
                font_weight="700",
                color="#EA580C",
            ),
            rx.button(
                "+",
                on_click=FoodState.agregar_producto(producto.id),
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


def _menu_section() -> rx.Component:
    return rx.vstack(
        rx.cond(
            FoodState.mesa_seleccionada_id == 0,
            rx.center(
                rx.text("Selecciona una mesa para agregar productos.", font_size="13px", color="#94A3B8"),
                padding_y="20px",
            ),
            rx.vstack(
                rx.hstack(
                    rx.button(
                        "Todos",
                        on_click=FoodState.seleccionar_categoria(0),
                        background=rx.cond(FoodState.categoria_activa_id == 0, "#FFF7ED", "#F1F5F9"),
                        color=rx.cond(FoodState.categoria_activa_id == 0, "#EA580C", "#64748B"),
                        border=rx.cond(FoodState.categoria_activa_id == 0, "1px solid #FED7AA", "1px solid #E2E8F0"),
                        border_radius="6px",
                        font_size="12px",
                        font_weight=rx.cond(FoodState.categoria_activa_id == 0, "700", "500"),
                        cursor="pointer",
                        padding_x="10px",
                        padding_y="5px",
                        _hover={"opacity": "0.85"},
                    ),
                    rx.foreach(
                        FoodState.categorias_activas,
                        lambda cat: rx.button(
                            cat.nombre,
                            on_click=FoodState.seleccionar_categoria(cat.id),
                            background=rx.cond(FoodState.categoria_activa_id == cat.id, "#FFF7ED", "#F1F5F9"),
                            color=rx.cond(FoodState.categoria_activa_id == cat.id, "#EA580C", "#64748B"),
                            border=rx.cond(FoodState.categoria_activa_id == cat.id, "1px solid #FED7AA", "1px solid #E2E8F0"),
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
                rx.cond(
                    FoodState.productos_filtrados.length() == 0,
                    rx.center(
                        rx.text("Sin productos disponibles en esta categoria.", font_size="13px", color="#94A3B8"),
                        padding_y="24px",
                    ),
                    rx.grid(
                        rx.foreach(FoodState.productos_filtrados, _producto_card),
                        columns="2",
                        gap="10px",
                        width="100%",
                    ),
                ),
                spacing="3",
                width="100%",
            ),
        ),
        spacing="3",
        width="100%",
    )


# ─── Layout principal (tabs) ──────────────────────────────────────────────────

def _mozos_content() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.text(
                "Salon",
                font_size="22px",
                font_weight="800",
                color="#0F172A",
            ),
            rx.spacer(),
            rx.hstack(
                rx.button(
                    "Salon",
                    on_click=FoodState.set_mozos_tab("salon"),
                    background=rx.cond(FoodState.mozos_tab_activa == "salon", "#FFF7ED", "#F1F5F9"),
                    color=rx.cond(FoodState.mozos_tab_activa == "salon", "#EA580C", "#64748B"),
                    border=rx.cond(FoodState.mozos_tab_activa == "salon", "1px solid #FED7AA", "1px solid #E2E8F0"),
                    border_radius="8px",
                    font_size="13px",
                    font_weight=rx.cond(FoodState.mozos_tab_activa == "salon", "700", "500"),
                    cursor="pointer",
                    padding_x="14px",
                    _hover={"opacity": "0.85"},
                ),
                rx.button(
                    "Agregar",
                    on_click=FoodState.set_mozos_tab("menu"),
                    background=rx.cond(FoodState.mozos_tab_activa == "menu", "#FFF7ED", "#F1F5F9"),
                    color=rx.cond(FoodState.mozos_tab_activa == "menu", "#EA580C", "#64748B"),
                    border=rx.cond(FoodState.mozos_tab_activa == "menu", "1px solid #FED7AA", "1px solid #E2E8F0"),
                    border_radius="8px",
                    font_size="13px",
                    font_weight=rx.cond(FoodState.mozos_tab_activa == "menu", "700", "500"),
                    cursor="pointer",
                    padding_x="14px",
                    _hover={"opacity": "0.85"},
                ),
                rx.button(
                    "Historial",
                    on_click=FoodState.set_mozos_tab("historial"),
                    background=rx.cond(FoodState.mozos_tab_activa == "historial", "#FFF7ED", "#F1F5F9"),
                    color=rx.cond(FoodState.mozos_tab_activa == "historial", "#EA580C", "#64748B"),
                    border=rx.cond(FoodState.mozos_tab_activa == "historial", "1px solid #FED7AA", "1px solid #E2E8F0"),
                    border_radius="8px",
                    font_size="13px",
                    font_weight=rx.cond(FoodState.mozos_tab_activa == "historial", "700", "500"),
                    cursor="pointer",
                    padding_x="14px",
                    _hover={"opacity": "0.85"},
                ),
                spacing="1",
            ),
            width="100%",
            align="center",
            flex_wrap="wrap",
            gap="8px",
        ),
        rx.cond(
            FoodState.mensaje != "",
            rx.box(
                rx.text(FoodState.mensaje, font_size="12px", color="#334155"),
                background="#F1F5F9",
                border="1px solid #E2E8F0",
                border_radius="6px",
                padding="8px 12px",
                width="100%",
            ),
            rx.fragment(),
        ),
        rx.cond(
            FoodState.mozos_tab_activa == "salon",
            _salon_content(),
            rx.cond(
                FoodState.mozos_tab_activa == "menu",
                _menu_section(),
                rx.cond(
                    FoodState.mozos_tab_activa == "historial",
                    rx.vstack(
                        _carrito_section(),
                        rx.divider(border_color="#E2E8F0"),
                        _historial_section(),
                        spacing="4",
                        width="100%",
                    ),
                    rx.fragment(),
                ),
            ),
        ),
        spacing="4",
        width="100%",
    )


@rx.page(
    route="/mozos",
    on_load=[FoodState.on_load_mozos, FoodState.start_mozos_polling],
)
def mozos_page() -> rx.Component:
    return app_shell(_mozos_content(), page_key="mozos")
