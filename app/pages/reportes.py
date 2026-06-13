"""Pagina de reportes — historial de ventas."""

from __future__ import annotations

import reflex as rx

from app.components.shared import app_shell
from app.states.food_state import FoodState, VentaHistorialView


def _venta_row(venta: VentaHistorialView) -> rx.Component:
    return rx.hstack(
        rx.text(
            "#" + venta.pedido_id.to_string(),
            font_size="12px",
            color="rgba(255,255,255,0.35)",
            min_width="44px",
        ),
        rx.text(venta.mesa_label, font_size="13px", color="#F1F5F9", flex="1"),
        rx.text(venta.mozo_nombre, font_size="12px", color="#94A3B8", min_width="80px", text_align="center"),
        rx.text(venta.cajero_nombre, font_size="12px", color="#94A3B8", min_width="80px", text_align="center"),
        rx.text(venta.total_texto, font_size="14px", font_weight="700", color="#4ADE80", min_width="80px", text_align="right"),
        width="100%",
        align="center",
        padding="10px 14px",
        background="rgba(255,255,255,0.03)",
        border_radius="8px",
        border="1px solid rgba(255,255,255,0.05)",
        _hover={"background": "rgba(255,255,255,0.05)"},
    )


def _reportes_content() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.text("Reportes", font_size="22px", font_weight="800", color="#F1F5F9"),
            rx.spacer(),
            rx.button(
                "Actualizar",
                on_click=FoodState.cargar_historial_ventas,
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
            FoodState.historial_ventas.length() == 0,
            rx.center(
                rx.text("Sin ventas registradas.", font_size="14px", color="rgba(255,255,255,0.35)"),
                padding_y="60px",
            ),
            rx.vstack(
                rx.hstack(
                    rx.text("#", font_size="11px", color="rgba(255,255,255,0.3)", min_width="44px"),
                    rx.text("Mesa / Pedido", font_size="11px", color="rgba(255,255,255,0.3)", flex="1"),
                    rx.text("Mozo", font_size="11px", color="rgba(255,255,255,0.3)", min_width="80px", text_align="center"),
                    rx.text("Cajero", font_size="11px", color="rgba(255,255,255,0.3)", min_width="80px", text_align="center"),
                    rx.text("Total", font_size="11px", color="rgba(255,255,255,0.3)", min_width="80px", text_align="right"),
                    width="100%",
                    padding_x="14px",
                ),
                rx.foreach(FoodState.historial_ventas, _venta_row),
                spacing="1",
                width="100%",
            ),
        ),
        spacing="5",
        width="100%",
    )


@rx.page(route="/reportes", on_load=FoodState.on_load_reportes)
def reportes_page() -> rx.Component:
    return app_shell(_reportes_content(), page_key="reportes")
