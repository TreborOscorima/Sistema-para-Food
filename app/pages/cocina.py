"""Pagina KDS de cocina — tickets por estado, tema oscuro tipo pantalla de cocina."""

from __future__ import annotations

import reflex as rx

from app.components.shared import _connection_banner_es, app_shell, loading_placeholder
from app.states.food_state import CocinaTicketView, FoodState


def _ticket_card_header_wrapped(ticket: CocinaTicketView) -> rx.Component:
    # Header de color sólido (bg = color del estado) + resto en la card oscura
    return rx.box(
        rx.box(
            rx.hstack(
                rx.text(
                    ticket.mesa_label,
                    font_size="26px",
                    font_weight="900",
                    color="#FFFFFF",
                    letter_spacing="-1px",
                ),
                rx.spacer(),
                rx.vstack(
                    rx.text(
                        ticket.estado_label,
                        font_size="10px",
                        font_weight="700",
                        color="#FFFFFF",
                        text_transform="uppercase",
                        letter_spacing="0.06em",
                        opacity="0.9",
                    ),
                    rx.text(
                        "⏱ " + ticket.minutos_texto,
                        font_size="12px",
                        color="#FFFFFF",
                        opacity="0.85",
                    ),
                    spacing="0",
                    align="end",
                ),
                width="100%",
                align="center",
            ),
            background=ticket.estado_bg,
            padding="14px 18px",
        ),
        rx.vstack(
            rx.cond(
                ticket.mozo_nombre != "",
                rx.text(
                    "Mozo: " + ticket.mozo_nombre,
                    font_size="11px",
                    color="#64748B",
                ),
                rx.fragment(),
            ),
            rx.cond(
                ticket.bumpable,
                rx.vstack(
                    rx.foreach(
                        ticket.items_ids,
                        lambda detalle_id, idx: rx.hstack(
                            rx.icon(tag="circle_check", size=16, color="#475569", flex_shrink="0"),
                            rx.text(
                                ticket.items_lines[idx],
                                font_size="17px", font_weight="700",
                                color="#F1F5F9", letter_spacing="-0.3px",
                            ),
                            on_click=FoodState.bump_item_cocina(detalle_id),
                            cursor="pointer",
                            padding="4px 6px",
                            border_radius="6px",
                            width="100%",
                            align="center",
                            spacing="2",
                            _hover={"background": "#1E293B"},
                            transition="background 0.15s ease",
                        ),
                    ),
                    width="100%",
                    spacing="2",
                    align="start",
                ),
                rx.vstack(
                    rx.foreach(
                        ticket.items_lines,
                        lambda line: rx.text(
                            line,
                            font_size="17px", font_weight="700",
                            color="#F1F5F9", letter_spacing="-0.3px",
                            padding_y="2px",
                        ),
                    ),
                    width="100%",
                    spacing="2",
                    align="start",
                ),
            ),
            rx.button(
                ticket.action_label,
                on_click=rx.cond(
                    ticket.estado_produccion == "pendiente",
                    FoodState.iniciar_preparacion_ticket(ticket.detalle_ids_csv),
                    rx.cond(
                        ticket.estado_produccion == "listo_para_entregar",
                        FoodState.devolver_ticket_a_preparacion(ticket.detalle_ids_csv),
                        FoodState.marcar_ticket_listo(ticket.detalle_ids_csv),
                    ),
                ),
                width="100%",
                background=rx.cond(
                    ticket.estado_produccion == "pendiente",
                    "#EA580C",
                    rx.cond(
                        ticket.estado_produccion == "listo_para_entregar",
                        "#475569",
                        "#16A34A",
                    ),
                ),
                color="#FFFFFF",
                border_radius="10px",
                padding_y="12px",
                font_size="14px",
                font_weight="700",
                cursor="pointer",
                margin_top="6px",
                _hover={"opacity": "0.9"},
                transition="all 0.15s ease",
            ),
            spacing="3",
            align="start",
            width="100%",
            padding="16px",
        ),
        background="#0F172A",
        border=f"2px solid {ticket.accent_border}",
        border_radius="16px",
        overflow="hidden",
        min_width="280px",
        max_width="340px",
        flex="0 0 auto",
    )


def _column(titulo: str, count, tickets, empty_msg: str) -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.box(width="3px", height="18px", background="#EA580C", border_radius="2px"),
            rx.text(
                titulo,
                font_size="13px",
                font_weight="700",
                color="#94A3B8",
                text_transform="uppercase",
                letter_spacing="0.08em",
            ),
            rx.badge(
                count.to_string(),
                background="#1E293B",
                color="#EA580C",
                border="1px solid #334155",
                border_radius="20px",
                font_size="11px",
                font_weight="700",
            ),
            spacing="2",
            align="center",
        ),
        rx.box(
            rx.cond(
                tickets.length() == 0,
                rx.center(
                    rx.text(empty_msg, font_size="13px", color="#475569"),
                    padding_y="40px",
                ),
                rx.flex(
                    rx.foreach(tickets, _ticket_card_header_wrapped),
                    flex_wrap="wrap",
                    gap="16px",
                    width="100%",
                ),
            ),
            overflow_y="auto",
            overflow_x="auto",
            max_height=rx.cond(FoodState.cocina_fullscreen, "85vh", "72vh"),
            width="100%",
            padding_right="4px",
        ),
        spacing="3",
        align="start",
        width="100%",
    )


def _cocina_content() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.vstack(
                rx.text(
                    "Cocina KDS",
                    font_size="22px",
                    font_weight="800",
                    color="#FFFFFF",
                ),
                rx.text("Pedidos en preparación", font_size="13px", color="#94A3B8"),
                spacing="0",
            ),
            rx.spacer(),
            rx.hstack(
                rx.button(
                    "Todo",
                    on_click=FoodState.set_cocina_filtro_estacion(""),
                    background=rx.cond(FoodState.cocina_filtro_estacion == "", "#EA580C", "#1E293B"),
                    color=rx.cond(FoodState.cocina_filtro_estacion == "", "#FFFFFF", "#94A3B8"),
                    border=rx.cond(FoodState.cocina_filtro_estacion == "", "1px solid #EA580C", "1px solid #334155"),
                    border_radius="6px", font_size="12px", font_weight="600",
                    padding_x="10px", padding_y="5px", cursor="pointer",
                    _hover={"border_color": "#EA580C"},
                ),
                rx.button(
                    "Cocina",
                    on_click=FoodState.set_cocina_filtro_estacion("cocina"),
                    background=rx.cond(FoodState.cocina_filtro_estacion == "cocina", "#EA580C", "#1E293B"),
                    color=rx.cond(FoodState.cocina_filtro_estacion == "cocina", "#FFFFFF", "#94A3B8"),
                    border=rx.cond(FoodState.cocina_filtro_estacion == "cocina", "1px solid #EA580C", "1px solid #334155"),
                    border_radius="6px", font_size="12px", font_weight="600",
                    padding_x="10px", padding_y="5px", cursor="pointer",
                    _hover={"border_color": "#EA580C"},
                ),
                rx.button(
                    "Barra",
                    on_click=FoodState.set_cocina_filtro_estacion("barra"),
                    background=rx.cond(FoodState.cocina_filtro_estacion == "barra", "#EA580C", "#1E293B"),
                    color=rx.cond(FoodState.cocina_filtro_estacion == "barra", "#FFFFFF", "#94A3B8"),
                    border=rx.cond(FoodState.cocina_filtro_estacion == "barra", "1px solid #EA580C", "1px solid #334155"),
                    border_radius="6px", font_size="12px", font_weight="600",
                    padding_x="10px", padding_y="5px", cursor="pointer",
                    _hover={"border_color": "#EA580C"},
                ),
                spacing="1", align="center",
            ),
            rx.hstack(
                rx.hstack(
                    rx.box(width="10px", height="10px", border_radius="3px", background="#F59E0B"),
                    rx.text("Pendiente", font_size="13px", color="#94A3B8", font_weight="500"),
                    spacing="2", align="center",
                ),
                rx.hstack(
                    rx.box(width="10px", height="10px", border_radius="3px", background="#EA580C"),
                    rx.text("En preparación", font_size="13px", color="#94A3B8", font_weight="500"),
                    spacing="2", align="center",
                ),
                rx.hstack(
                    rx.box(width="10px", height="10px", border_radius="3px", background="#16A34A"),
                    rx.text("Listo", font_size="13px", color="#94A3B8", font_weight="500"),
                    spacing="2", align="center",
                ),
                rx.hstack(
                    rx.box(width="10px", height="10px", border_radius="3px", background="#DC2626"),
                    rx.text("Demorado", font_size="13px", color="#94A3B8", font_weight="500"),
                    spacing="2", align="center",
                ),
                spacing="4", align="center",
                display=rx.breakpoints(initial="none", lg="flex"),
            ),
            rx.button(
                rx.icon(
                    tag=rx.cond(FoodState.sonidos_activos, "volume_2", "volume_off"),
                    size=16,
                ),
                on_click=FoodState.toggle_sonidos,
                background=rx.cond(FoodState.sonidos_activos, "#1E293B", "#0F172A"),
                color=rx.cond(FoodState.sonidos_activos, "#EA580C", "#475569"),
                border=rx.cond(FoodState.sonidos_activos, "1px solid #334155", "1px solid #1E293B"),
                border_radius="8px",
                cursor="pointer",
                padding="8px",
                _hover={"border_color": "#EA580C"},
            ),
            rx.button(
                rx.icon(
                    tag=rx.cond(FoodState.cocina_fullscreen, "minimize_2", "maximize_2"),
                    size=16,
                ),
                rx.text(rx.cond(FoodState.cocina_fullscreen, "Salir", "Expandir"),
                        font_size="13px"),
                on_click=FoodState.toggle_cocina_fullscreen,
                background="#1E293B",
                color="#EA580C",
                border="1px solid #334155",
                border_radius="8px",
                font_size="13px",
                font_weight="600",
                cursor="pointer",
                display="flex",
                align_items="center",
                gap="6px",
                _hover={"border_color": "#EA580C"},
            ),
            rx.hstack(
                rx.text(
                    FoodState.ultima_actualizacion,
                    font_size="11px", color="#64748B",
                ),
                rx.icon(
                    tag="refresh_cw", size=14, color="#EA580C",
                    cursor="pointer",
                    on_click=FoodState.cargar_cocina,
                    _hover={"opacity": "0.7"},
                ),
                spacing="1", align="center",
            ),
            width="100%",
            align="center",
            gap="16px",
        ),
        _column(
            "Pendiente", FoodState.cantidad_tickets_nuevos, FoodState.tickets_nuevos,
            "Sin pedidos nuevos",
        ),
        _column(
            "En preparación", FoodState.cantidad_tickets_en_preparacion,
            FoodState.tickets_en_preparacion, "Sin pedidos en preparación",
        ),
        _column(
            "Listo", FoodState.cantidad_tickets_listos,
            FoodState.tickets_listos, "Sin pedidos listos",
        ),
        spacing="5",
        width="100%",
    )


def _fullscreen_shell() -> rx.Component:
    return rx.box(
        _connection_banner_es(),
        rx.box(
            rx.vstack(
                _cocina_content(),
                width="100%",
                align="start",
                spacing="5",
            ),
            padding="16px 24px",
            width="100%",
        ),
        min_height="100vh",
        width="100%",
        background="#0F172A",
        color="#FFFFFF",
    )


@rx.page(
    route="/cocina",
    on_load=[FoodState.on_load_cocina, FoodState.start_cocina_polling],
    title="TUWAYKIFOOD | Cocina",
)
def cocina_page() -> rx.Component:
    return rx.cond(
        FoodState.pagina_cargada,
        rx.cond(
            FoodState.cocina_fullscreen,
            _fullscreen_shell(),
            app_shell(_cocina_content(), page_key="cocina", dark=True),
        ),
        app_shell(loading_placeholder(dark=True), page_key="cocina", dark=True),
    )
