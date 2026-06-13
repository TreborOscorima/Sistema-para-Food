"""Pagina KDS de cocina — tickets por estado."""

from __future__ import annotations

import reflex as rx

from app.components.shared import app_shell, section_card
from app.states.food_state import CocinaTicketView, FoodState


def _ticket_card(ticket: CocinaTicketView) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.vstack(
                    rx.text(
                        ticket.mesa_label,
                        font_size="15px",
                        font_weight="700",
                        color="#F1F5F9",
                    ),
                    rx.text(
                        "Hora: " + ticket.hora_texto,
                        font_size="11px",
                        color="rgba(255,255,255,0.4)",
                    ),
                    spacing="0",
                ),
                rx.spacer(),
                rx.badge(
                    ticket.estado_label,
                    background=ticket.estado_bg,
                    color=ticket.estado_color,
                    border_radius="6px",
                    font_size="11px",
                    padding="3px 8px",
                ),
                width="100%",
            ),
            rx.cond(
                ticket.mozo_nombre != "",
                rx.text(
                    "Mozo: " + ticket.mozo_nombre,
                    font_size="11px",
                    color="rgba(255,255,255,0.35)",
                ),
                rx.fragment(),
            ),
            rx.divider(border_color="rgba(255,255,255,0.08)"),
            rx.vstack(
                rx.foreach(
                    ticket.items_lines,
                    lambda line: rx.text(
                        line,
                        font_size="14px",
                        color="#E2E8F0",
                        padding_y="2px",
                    ),
                ),
                width="100%",
                spacing="1",
                align="start",
            ),
            rx.divider(border_color="rgba(255,255,255,0.08)"),
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
                    "rgba(249,115,22,0.20)",
                    "rgba(34,197,94,0.18)",
                ),
                color=rx.cond(
                    ticket.estado_produccion == "pendiente",
                    "#F97316",
                    "#4ADE80",
                ),
                border=rx.cond(
                    ticket.estado_produccion == "pendiente",
                    "1px solid rgba(249,115,22,0.35)",
                    "1px solid rgba(34,197,94,0.35)",
                ),
                border_radius="8px",
                padding_y="10px",
                font_size="13px",
                font_weight="600",
                cursor="pointer",
                _hover={
                    "opacity": "0.85",
                    "transform": "translateY(-1px)",
                },
                transition="all 0.15s ease",
            ),
            spacing="3",
            align="start",
            width="100%",
        ),
        background=ticket.accent_bg,
        border=f"1px solid {ticket.accent_border}",
        border_radius="12px",
        padding="16px",
        min_width="260px",
        max_width="300px",
        flex="0 0 auto",
    )


def _column_nuevos() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.text(
                "Nuevos",
                font_size="14px",
                font_weight="700",
                color="#FCD34D",
            ),
            rx.badge(
                FoodState.cantidad_tickets_nuevos.to_string(),
                background="rgba(251,191,36,0.16)",
                color="#FCD34D",
                border_radius="20px",
                font_size="11px",
            ),
            spacing="2",
            align="center",
        ),
        rx.cond(
            FoodState.tickets_nuevos.length() == 0,
            rx.center(
                rx.text("Sin pedidos nuevos", font_size="13px", color="rgba(255,255,255,0.3)"),
                padding_y="40px",
            ),
            rx.vstack(
                rx.foreach(FoodState.tickets_nuevos, _ticket_card),
                spacing="3",
                width="100%",
            ),
        ),
        spacing="3",
        align="start",
        flex="1",
        min_width="0",
    )


def _column_en_preparacion() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.text(
                "En preparacion",
                font_size="14px",
                font_weight="700",
                color="#FDBA74",
            ),
            rx.badge(
                FoodState.cantidad_tickets_en_preparacion.to_string(),
                background="rgba(249,115,22,0.18)",
                color="#FDBA74",
                border_radius="20px",
                font_size="11px",
            ),
            spacing="2",
            align="center",
        ),
        rx.cond(
            FoodState.tickets_en_preparacion.length() == 0,
            rx.center(
                rx.text("Sin pedidos en preparacion", font_size="13px", color="rgba(255,255,255,0.3)"),
                padding_y="40px",
            ),
            rx.vstack(
                rx.foreach(FoodState.tickets_en_preparacion, _ticket_card),
                spacing="3",
                width="100%",
            ),
        ),
        spacing="3",
        align="start",
        flex="1",
        min_width="0",
    )


def _cocina_content() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.text(
                "Cocina",
                font_size="22px",
                font_weight="800",
                color="#F1F5F9",
            ),
            rx.spacer(),
            rx.button(
                "Actualizar",
                on_click=FoodState.cargar_cocina,
                background="rgba(249,115,22,0.14)",
                color="#F97316",
                border="1px solid rgba(249,115,22,0.28)",
                border_radius="8px",
                font_size="13px",
                cursor="pointer",
                _hover={"opacity": "0.85"},
            ),
            width="100%",
            align="center",
        ),
        rx.hstack(
            _column_nuevos(),
            rx.divider(orientation="vertical", border_color="rgba(255,255,255,0.08)", height="auto"),
            _column_en_preparacion(),
            spacing="5",
            width="100%",
            align="start",
        ),
        spacing="5",
        width="100%",
    )


@rx.page(
    route="/cocina",
    on_load=[FoodState.on_load_cocina, FoodState.start_cocina_polling],
)
def cocina_page() -> rx.Component:
    return app_shell(_cocina_content(), page_key="cocina")
