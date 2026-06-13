"""Pagina de caja — cobro de mesas."""

from __future__ import annotations

import reflex as rx

from app.components.shared import app_shell
from app.states.food_state import FoodState, MesaView


def _mesa_cobro_card(mesa: MesaView) -> rx.Component:
    cobrable = (mesa.estado != "libre") & (mesa.total_abierto > 0)
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.vstack(
                    rx.text(mesa.nombre, font_size="15px", font_weight="700", color="#F1F5F9"),
                    rx.badge(
                        mesa.estado_label,
                        background=mesa.badge_bg,
                        color=mesa.badge_text,
                        border_radius="5px",
                        font_size="10px",
                    ),
                    spacing="1",
                    align="start",
                ),
                rx.spacer(),
                rx.text(
                    mesa.total_abierto_texto,
                    font_size="20px",
                    font_weight="800",
                    color="#F97316",
                ),
                width="100%",
                align="center",
            ),
            rx.cond(
                mesa.tiene_items_listos,
                rx.text(
                    mesa.items_listos_count.to_string() + " items listos para entregar",
                    font_size="11px",
                    color="#FCD34D",
                    font_weight="600",
                ),
                rx.fragment(),
            ),
            rx.button(
                "Cobrar Mesa",
                on_click=FoodState.cobrar_mesa(mesa.id),
                width="100%",
                background=rx.cond(cobrable, "rgba(34,197,94,0.18)", "rgba(255,255,255,0.04)"),
                color=rx.cond(cobrable, "#4ADE80", "rgba(255,255,255,0.25)"),
                border=rx.cond(
                    cobrable,
                    "1px solid rgba(34,197,94,0.35)",
                    "1px solid rgba(255,255,255,0.08)",
                ),
                border_radius="8px",
                font_size="13px",
                font_weight="700",
                cursor=rx.cond(cobrable, "pointer", "not-allowed"),
                padding_y="10px",
                _hover=rx.cond(cobrable, {"opacity": "0.85"}, {}),
                disabled=~cobrable,
            ),
            spacing="3",
            align="start",
            width="100%",
        ),
        background=mesa.card_bg,
        border=mesa.card_border,
        border_radius="12px",
        padding="16px",
        opacity=rx.cond(cobrable, "1", "0.55"),
    )


def _caja_content() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.vstack(
                rx.text("Caja", font_size="22px", font_weight="800", color="#F1F5F9"),
                rx.text(
                    FoodState.cantidad_mesas_abiertas.to_string() + " mesa(s) abiertas",
                    font_size="13px",
                    color="rgba(255,255,255,0.4)",
                ),
                spacing="0",
            ),
            rx.spacer(),
            rx.button(
                "Actualizar",
                on_click=FoodState.cargar_mesas,
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
        rx.cond(
            FoodState.mensaje != "",
            rx.box(
                rx.text(FoodState.mensaje, font_size="12px", color="#94A3B8"),
                background="rgba(255,255,255,0.04)",
                border_radius="6px",
                padding="8px 12px",
                width="100%",
            ),
            rx.fragment(),
        ),
        rx.cond(
            FoodState.mesas.length() == 0,
            rx.center(
                rx.text("No hay mesas configuradas.", font_size="14px", color="rgba(255,255,255,0.35)"),
                padding_y="60px",
            ),
            rx.grid(
                rx.foreach(FoodState.mesas, _mesa_cobro_card),
                columns=rx.breakpoints(initial="1", sm="2", md="3"),
                gap="16px",
                width="100%",
            ),
        ),
        spacing="5",
        width="100%",
    )


@rx.page(
    route="/caja",
    on_load=[FoodState.on_load_caja, FoodState.start_caja_polling],
)
def caja_page() -> rx.Component:
    return app_shell(_caja_content(), page_key="caja")
