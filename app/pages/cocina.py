"""Pagina KDS de cocina — tickets por estado, tema oscuro tipo pantalla de cocina."""

from __future__ import annotations

import reflex as rx

from app.components.shared import (
    _connection_banner_es, app_shell, loading_placeholder,
    ACCENT, DANGER_SOLID, DANGER_TEXT,
    DARK_600, DARK_700, DARK_800,
    PAGE_BACKGROUND,
    SUCCESS_DARK,
    TEXT_MUTED, TEXT_PRIMARY, TEXT_WHITE,
    WARNING_SOLID,
)
from app.components.ayuda import ayuda_modal, ayuda_trigger
from app.states.food_state import CocinaTicketView, FoodState


def _cocina_ayuda() -> rx.Component:
    return ayuda_modal(
        titulo="¿Cómo funciona Cocina?",
        subtitulo="Pantalla de preparación (KDS): las comandas llegan solas.",
        secciones=[{
            "titulo": None,
            "pasos": [
                "Cada tarjeta es una comanda enviada por los mozos o el mostrador.",
                "Tócala para avanzarla: Pendiente → En preparación → Listo.",
                "Usa los filtros (Todo / Cocina / Barra) para ver solo tu estación.",
                "Una tarjeta en rojo está demorada: atiéndela primero.",
            ],
        }],
        leyenda=[
            (WARNING_SOLID, "Pendiente"),
            (ACCENT, "En preparación"),
            (SUCCESS_DARK, "Listo"),
            (DANGER_SOLID, "Demorado"),
        ],
    )


def _ticket_card_header_wrapped(ticket: CocinaTicketView) -> rx.Component:
    # Header de color sólido (bg = color del estado) + resto en la card oscura
    return rx.box(
        rx.box(
            rx.hstack(
                rx.text(
                    ticket.mesa_label,
                    font_size="26px",
                    font_weight="900",
                    color=TEXT_WHITE,
                    letter_spacing="-1px",
                ),
                rx.spacer(),
                rx.vstack(
                    rx.text(
                        ticket.estado_label,
                        font_size="10px",
                        font_weight="700",
                        color=TEXT_WHITE,
                        text_transform="uppercase",
                        letter_spacing="0.06em",
                        opacity="0.9",
                    ),
                    rx.text(
                        "⏱ " + ticket.minutos_texto,
                        font_size="12px",
                        color=TEXT_WHITE,
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
                    color=TEXT_MUTED,
                ),
                rx.fragment(),
            ),
            rx.cond(
                ticket.bumpable,
                rx.vstack(
                    rx.foreach(
                        ticket.items_ids,
                        lambda detalle_id, idx: rx.hstack(
                            rx.icon(tag="circle_check", size=16, color=TEXT_MUTED, flex_shrink="0"),
                            rx.text(
                                ticket.items_lines[idx],
                                font_size="17px", font_weight="700",
                                color=TEXT_PRIMARY, letter_spacing="-0.3px",
                                flex="1", min_width="0",
                                cursor="pointer",
                                on_click=FoodState.bump_item_cocina(detalle_id),
                            ),
                            rx.button(
                                "86",
                                on_click=FoodState.marcar_86_cocina(ticket.items_producto_ids[idx]),
                                background="#7F1D1D",
                                color="#FCA5A5",
                                border="1px solid #991B1B",
                                border_radius="6px",
                                font_size="11px",
                                font_weight="800",
                                padding="2px 10px",
                                min_width="auto",
                                height=rx.breakpoints(initial="40px", lg="28px"),
                                cursor="pointer",
                                flex_shrink="0",
                                _hover={"background": DANGER_TEXT},
                            ),
                            padding="4px 6px",
                            border_radius="6px",
                            width="100%",
                            align="center",
                            spacing="2",
                            _hover={"background": DARK_800},
                            transition="background 0.15s ease",
                        ),
                    ),
                    width="100%",
                    spacing="2",
                    align="start",
                ),
                rx.vstack(
                    rx.foreach(
                        ticket.items_producto_ids,
                        lambda prod_id, idx: rx.hstack(
                            rx.text(
                                ticket.items_lines[idx],
                                font_size="17px", font_weight="700",
                                color=TEXT_PRIMARY, letter_spacing="-0.3px",
                                flex="1", min_width="0",
                            ),
                            rx.button(
                                "86",
                                on_click=FoodState.marcar_86_cocina(prod_id),
                                background="#7F1D1D",
                                color="#FCA5A5",
                                border="1px solid #991B1B",
                                border_radius="6px",
                                font_size="11px",
                                font_weight="800",
                                padding="2px 10px",
                                min_width="auto",
                                height=rx.breakpoints(initial="40px", lg="28px"),
                                cursor="pointer",
                                flex_shrink="0",
                                _hover={"background": DANGER_TEXT},
                            ),
                            width="100%",
                            align="center",
                            spacing="2",
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
                    ACCENT,
                    rx.cond(
                        ticket.estado_produccion == "listo_para_entregar",
                        DARK_600,
                        SUCCESS_DARK,
                    ),
                ),
                color=TEXT_WHITE,
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
        background=PAGE_BACKGROUND,
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
            rx.box(width="3px", height="18px", background=ACCENT, border_radius="2px"),
            rx.text(
                titulo,
                font_size="13px",
                font_weight="700",
                color=TEXT_MUTED,
                text_transform="uppercase",
                letter_spacing="0.08em",
            ),
            rx.badge(
                count.to_string(),
                background=DARK_800,
                color=ACCENT,
                border=f"1px solid {DARK_700}",
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
                    rx.text(empty_msg, font_size="13px", color=TEXT_MUTED),
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
                    color=TEXT_WHITE,
                ),
                rx.text("Pedidos en preparación", font_size="13px", color=TEXT_MUTED),
                spacing="0",
            ),
            rx.spacer(),
            ayuda_trigger(),
            rx.hstack(
                rx.button(
                    "Todo",
                    on_click=FoodState.set_cocina_filtro_estacion(""),
                    background=rx.cond(FoodState.cocina_filtro_estacion == "", ACCENT, DARK_800),
                    color=rx.cond(FoodState.cocina_filtro_estacion == "", TEXT_WHITE, TEXT_MUTED),
                    border=rx.cond(FoodState.cocina_filtro_estacion == "", f"1px solid {ACCENT}", f"1px solid {DARK_700}"),
                    border_radius="6px", font_size="12px", font_weight="600",
                    padding_x="10px", padding_y="5px", cursor="pointer",
                    _hover={"border_color": ACCENT},
                ),
                rx.button(
                    "Cocina",
                    on_click=FoodState.set_cocina_filtro_estacion("cocina"),
                    background=rx.cond(FoodState.cocina_filtro_estacion == "cocina", ACCENT, DARK_800),
                    color=rx.cond(FoodState.cocina_filtro_estacion == "cocina", TEXT_WHITE, TEXT_MUTED),
                    border=rx.cond(FoodState.cocina_filtro_estacion == "cocina", f"1px solid {ACCENT}", f"1px solid {DARK_700}"),
                    border_radius="6px", font_size="12px", font_weight="600",
                    padding_x="10px", padding_y="5px", cursor="pointer",
                    _hover={"border_color": ACCENT},
                ),
                rx.button(
                    "Barra",
                    on_click=FoodState.set_cocina_filtro_estacion("barra"),
                    background=rx.cond(FoodState.cocina_filtro_estacion == "barra", ACCENT, DARK_800),
                    color=rx.cond(FoodState.cocina_filtro_estacion == "barra", TEXT_WHITE, TEXT_MUTED),
                    border=rx.cond(FoodState.cocina_filtro_estacion == "barra", f"1px solid {ACCENT}", f"1px solid {DARK_700}"),
                    border_radius="6px", font_size="12px", font_weight="600",
                    padding_x="10px", padding_y="5px", cursor="pointer",
                    _hover={"border_color": ACCENT},
                ),
                spacing="1", align="center",
            ),
            rx.hstack(
                rx.hstack(
                    rx.box(width="10px", height="10px", border_radius="3px", background=WARNING_SOLID),
                    rx.text("Pendiente", font_size="13px", color=TEXT_MUTED, font_weight="500"),
                    spacing="2", align="center",
                ),
                rx.hstack(
                    rx.box(width="10px", height="10px", border_radius="3px", background=ACCENT),
                    rx.text("En preparación", font_size="13px", color=TEXT_MUTED, font_weight="500"),
                    spacing="2", align="center",
                ),
                rx.hstack(
                    rx.box(width="10px", height="10px", border_radius="3px", background=SUCCESS_DARK),
                    rx.text("Listo", font_size="13px", color=TEXT_MUTED, font_weight="500"),
                    spacing="2", align="center",
                ),
                rx.hstack(
                    rx.box(width="10px", height="10px", border_radius="3px", background=DANGER_SOLID),
                    rx.text("Demorado", font_size="13px", color=TEXT_MUTED, font_weight="500"),
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
                background=rx.cond(FoodState.sonidos_activos, DARK_800, PAGE_BACKGROUND),
                color=rx.cond(FoodState.sonidos_activos, ACCENT, DARK_600),
                border=rx.cond(FoodState.sonidos_activos, f"1px solid {DARK_700}", f"1px solid {DARK_800}"),
                border_radius="8px",
                cursor="pointer",
                padding="8px",
                _hover={"border_color": ACCENT},
            ),
            rx.button(
                rx.icon(
                    tag=rx.cond(FoodState.cocina_fullscreen, "minimize_2", "maximize_2"),
                    size=16,
                ),
                rx.text(rx.cond(FoodState.cocina_fullscreen, "Salir", "Expandir"),
                        font_size="13px"),
                on_click=FoodState.toggle_cocina_fullscreen,
                background=DARK_800,
                color=ACCENT,
                border=f"1px solid {DARK_700}",
                border_radius="8px",
                font_size="13px",
                font_weight="600",
                cursor="pointer",
                display="flex",
                align_items="center",
                gap="6px",
                _hover={"border_color": ACCENT},
            ),
            rx.hstack(
                rx.text(
                    FoodState.ultima_actualizacion,
                    font_size="11px", color=TEXT_MUTED,
                ),
                rx.icon(
                    tag="refresh_cw", size=14, color=ACCENT,
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
        _cocina_ayuda(),
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
        background=PAGE_BACKGROUND,
        color=TEXT_WHITE,
        class_name="dark",
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
