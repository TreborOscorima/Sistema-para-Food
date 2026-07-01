"""Pagina KDS de cocina — tickets por estado, tema oscuro tipo pantalla de cocina."""

from __future__ import annotations

import reflex as rx

from app.components.shared import app_shell
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
                        "⏱ " + ticket.hora_texto,
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
            rx.vstack(
                rx.foreach(
                    ticket.items_lines,
                    lambda line: rx.text(
                        line,
                        font_size="17px",
                        font_weight="700",
                        color="#F1F5F9",
                        letter_spacing="-0.3px",
                        padding_y="2px",
                    ),
                ),
                width="100%",
                spacing="2",
                align="start",
            ),
            rx.button(
                ticket.action_label,
                on_click=rx.cond(
                    ticket.estado_produccion == "pendiente",
                    FoodState.iniciar_preparacion_ticket(ticket.detalle_ids_csv),
                    FoodState.marcar_ticket_listo(ticket.detalle_ids_csv),
                ),
                width="100%",
                background=rx.cond(
                    ticket.estado_produccion == "pendiente",
                    "#EA580C",
                    "#16A34A",
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
            max_height="72vh",
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
            rx.text(
                "Cocina KDS",
                font_size="22px",
                font_weight="800",
                color="#FFFFFF",
            ),
            rx.spacer(),
            rx.button(
                "Actualizar",
                on_click=FoodState.cargar_cocina,
                background="#1E293B",
                color="#EA580C",
                border="1px solid #334155",
                border_radius="8px",
                font_size="13px",
                font_weight="600",
                cursor="pointer",
                _hover={"border_color": "#EA580C"},
            ),
            width="100%",
            align="center",
        ),
        _column(
            "Pendiente", FoodState.cantidad_tickets_nuevos, FoodState.tickets_nuevos,
            "Sin pedidos nuevos",
        ),
        _column(
            "En preparación", FoodState.cantidad_tickets_en_preparacion,
            FoodState.tickets_en_preparacion, "Sin pedidos en preparación",
        ),
        spacing="5",
        width="100%",
    )


@rx.page(
    route="/cocina",
    on_load=[FoodState.on_load_cocina, FoodState.start_cocina_polling],
    title="TUWAYKIFOOD | Cocina",
)
def cocina_page() -> rx.Component:
    return app_shell(_cocina_content(), page_key="cocina", dark=True)
