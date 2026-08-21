"""Estación de impresión dedicada.

Esta página se deja abierta a pantalla completa en la PC de la caja (la que
tiene la impresora térmica conectada por USB). Su único trabajo es escuchar
las comandas nuevas que envían los mozos desde cualquier dispositivo
(celular, tablet, mostrador, QR del cliente) e imprimirlas automáticamente
en esa impresora.

Para que la impresión sea SILENCIOSA (sin el diálogo de Windows), el
navegador de esa PC debe abrirse en modo kiosk-printing:

    chrome.exe --kiosk-printing https://<tu-dominio>/estacion-impresion

y la impresora térmica debe estar como predeterminada en Windows.
"""

from __future__ import annotations

import reflex as rx

from app.components.shared import (
    _connection_banner_es,
    ACCENT,
    DARK_600, DARK_700, DARK_800,
    PAGE_BACKGROUND,
    SUCCESS_DARK,
    SURFACE_BASE,
    TEXT_MUTED, TEXT_PRIMARY, TEXT_WHITE,
)
from app.states.food_state import FoodState


def _stat_card(label: str, value, icon_tag: str) -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.icon(tag=icon_tag, size=15, color=ACCENT),
            rx.text(
                label,
                font_size="11px",
                font_weight="700",
                color=TEXT_MUTED,
                text_transform="uppercase",
                letter_spacing="0.06em",
            ),
            spacing="2",
            align="center",
        ),
        rx.text(value, font_size="22px", font_weight="800", color=TEXT_PRIMARY),
        background=SURFACE_BASE,
        border=f"1px solid {DARK_700}",
        border_radius="12px",
        padding="16px 18px",
        spacing="2",
        align="start",
        width="100%",
    )


def _instruccion(paso: str, texto) -> rx.Component:
    return rx.hstack(
        rx.box(
            rx.text(paso, font_size="12px", font_weight="800", color=TEXT_WHITE),
            background=ACCENT,
            border_radius="50%",
            min_width="22px",
            height="22px",
            display="flex",
            align_items="center",
            justify_content="center",
            flex_shrink="0",
        ),
        rx.text(texto, font_size="13px", color=TEXT_PRIMARY, line_height="1.5"),
        spacing="3",
        align="start",
        width="100%",
    )


def _estacion_content() -> rx.Component:
    return rx.center(
        rx.vstack(
            # Encabezado
            rx.hstack(
                rx.box(
                    rx.icon(tag="printer", size=26, color=TEXT_WHITE),
                    background=ACCENT,
                    border_radius="14px",
                    padding="12px",
                    display="flex",
                ),
                rx.vstack(
                    rx.text(
                        "Estación de impresión",
                        font_size="22px",
                        font_weight="800",
                        color=TEXT_PRIMARY,
                    ),
                    rx.text(
                        FoodState.config_nombre_local,
                        font_size="13px",
                        color=TEXT_MUTED,
                    ),
                    spacing="0",
                    align="start",
                ),
                spacing="4",
                align="center",
                width="100%",
            ),
            # Estado — depende del modo de impresión configurado
            rx.cond(
                FoodState.config_modo_impresion == "agente",
                # Modo agente: esta pantalla no imprime; lo hace el agente local
                rx.hstack(
                    rx.icon(tag="info", size=18, color=ACCENT, flex_shrink="0"),
                    rx.vstack(
                        rx.text(
                            "El agente local está a cargo de la impresión",
                            font_size="15px",
                            font_weight="700",
                            color=TEXT_PRIMARY,
                        ),
                        rx.text(
                            "Tienes el modo \"Agente local\" activado, así que las "
                            "comandas se imprimen solas en segundo plano. No necesitas "
                            "dejar esta pantalla abierta.",
                            font_size="12px",
                            color=TEXT_MUTED,
                            line_height="1.5",
                        ),
                        spacing="1",
                        align="start",
                    ),
                    spacing="3",
                    align="center",
                    background=SURFACE_BASE,
                    border=f"1px solid {DARK_700}",
                    border_radius="12px",
                    padding="16px 18px",
                    width="100%",
                ),
                # Modo navegador (kiosk): esta pantalla es la que imprime
                rx.hstack(
                    rx.box(
                        width="12px",
                        height="12px",
                        border_radius="50%",
                        background=SUCCESS_DARK,
                        box_shadow=f"0 0 0 4px rgba(34,197,94,0.20)",
                        flex_shrink="0",
                    ),
                    rx.vstack(
                        rx.text(
                            "Activa — escuchando comandas",
                            font_size="15px",
                            font_weight="700",
                            color=TEXT_PRIMARY,
                        ),
                        rx.text(
                            "Las comandas enviadas desde cualquier celular o tablet "
                            "se imprimen aquí automáticamente. Deja esta pantalla "
                            "abierta durante todo el servicio.",
                            font_size="12px",
                            color=TEXT_MUTED,
                            line_height="1.5",
                        ),
                        spacing="1",
                        align="start",
                    ),
                    spacing="3",
                    align="center",
                    background=SURFACE_BASE,
                    border=f"1px solid {SUCCESS_DARK}",
                    border_radius="12px",
                    padding="16px 18px",
                    width="100%",
                ),
            ),
            # Métricas
            rx.hstack(
                _stat_card("Impresas (sesión)", FoodState.estacion_tickets_impresos.to_string(), "receipt_text"),
                _stat_card(
                    "Última impresión",
                    rx.cond(FoodState.estacion_ultima_impresion != "", FoodState.estacion_ultima_impresion, "—"),
                    "clock",
                ),
                _stat_card("Ancho papel", FoodState.config_ticket_paper_width_mm + " mm", "ruler"),
                spacing="3",
                width="100%",
                flex_wrap="wrap",
            ),
            # Botón de prueba
            rx.button(
                rx.icon(tag="printer", size=16),
                rx.text("Imprimir ticket de prueba", font_size="14px", font_weight="700"),
                on_click=FoodState.imprimir_ticket_prueba,
                background=ACCENT,
                color=TEXT_WHITE,
                border_radius="10px",
                padding="12px 18px",
                cursor="pointer",
                display="flex",
                align_items="center",
                gap="8px",
                width="100%",
                _hover={"opacity": "0.9"},
            ),
            # Instrucciones de configuración (una sola vez por PC)
            rx.vstack(
                rx.hstack(
                    rx.icon(tag="settings", size=15, color=TEXT_MUTED),
                    rx.text(
                        "Configuración de la PC (una sola vez)",
                        font_size="12px",
                        font_weight="700",
                        color=TEXT_MUTED,
                        text_transform="uppercase",
                        letter_spacing="0.06em",
                    ),
                    spacing="2",
                    align="center",
                ),
                _instruccion("1", "Conecta la impresora térmica por USB y ponla como impresora predeterminada en Windows."),
                _instruccion("2", "Abre Google Chrome en modo impresión silenciosa (kiosk-printing) con el acceso directo entregado."),
                _instruccion("3", "Permite las ventanas emergentes para este sitio y deja esta pantalla abierta durante el servicio."),
                _instruccion("4", "Usa el botón de arriba para imprimir un ticket de prueba y confirmar que sale el papel."),
                spacing="3",
                align="start",
                background=SURFACE_BASE,
                border=f"1px solid {DARK_700}",
                border_radius="12px",
                padding="18px",
                width="100%",
            ),
            rx.link(
                rx.hstack(
                    rx.icon(tag="arrow_left", size=14),
                    rx.text("Volver a Caja", font_size="13px"),
                    spacing="2",
                    align="center",
                ),
                href="/caja",
                color=TEXT_MUTED,
                text_decoration="none",
                _hover={"color": ACCENT},
            ),
            spacing="4",
            align="start",
            width="100%",
            max_width="640px",
        ),
        width="100%",
        padding_y="32px",
    )


def _shell(content: rx.Component) -> rx.Component:
    return rx.box(
        _connection_banner_es(),
        rx.box(
            content,
            padding=rx.breakpoints(initial="16px", md="24px"),
            width="100%",
        ),
        min_height="100vh",
        width="100%",
        background=PAGE_BACKGROUND,
        color=TEXT_PRIMARY,
    )


@rx.page(
    route="/estacion-impresion",
    on_load=[
        FoodState.on_load_estacion_impresion,
        FoodState.start_estacion_impresion_polling,
    ],
    title="TUWAYKIFOOD | Estación de impresión",
)
def estacion_impresion_page() -> rx.Component:
    return rx.cond(
        FoodState.pagina_cargada,
        _shell(_estacion_content()),
        _shell(
            rx.center(
                rx.spinner(size="3", color=ACCENT),
                padding_y="80px",
                width="100%",
            )
        ),
    )
