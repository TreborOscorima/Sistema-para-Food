"""Pagina de caja — turno con arqueo, cobro de mesas con método de pago y propina."""

from __future__ import annotations

import reflex as rx

from app.components.shared import (
    WARNING_TEXT, SUCCESS_TEXT, DANGER_TEXT,
    anulacion_modal, app_shell, cumpleanos_banner, loading_placeholder, preview_ticket_modal, styled_switch,
    ACCENT, ACCENT_HOVER,
    DANGER_SOLID,
    DARK_700, DARK_800,
    PAGE_BACKGROUND, SURFACE_BASE,
    SUCCESS_SOLID,
    TEXT_MUTED, TEXT_PRIMARY, TEXT_WHITE,
    WARNING_SOLID,
)
from app.states.caja_turno_mixin import (
    CierrePreviewMovRow,
    CierrePreviewPedidoRow,
    CierreProductoRow,
    DenominacionRow,
    MetodoPagoView,
    MovimientoCajaView,
    ResumenCierreRow,
    TurnoHistorialView,
)
from app.components.ayuda import ayuda_modal, ayuda_trigger, empty_state
from app.states.food_state import FoodState, MesaView, CajaItemView, MostradorPendienteView, PagoStagedView, UltimoCobroView, ProductoView, CorreccionLineaView
from app.states.reportes_state import ReportesState


def _caja_ayuda() -> rx.Component:
    return ayuda_modal(
        titulo="¿Cómo funciona Caja?",
        subtitulo="Cobra los pedidos y maneja el turno de caja.",
        secciones=[
            {
                "titulo": "Cobrar",
                "pasos": [
                    "Elige una mesa (o un pedido para llevar) de la izquierda.",
                    "Revisa el consumo y elige el método de pago.",
                    "Confirma el cobro: se imprime el ticket y la mesa queda libre.",
                ],
            },
            {
                "titulo": "Turno de caja",
                "pasos": [
                    "Abre el turno con un fondo inicial. Nadie puede cobrar sin turno abierto.",
                    "Opera durante el día; registra ingresos y gastos si hace falta.",
                    "Ciérralo con el arqueo: el sistema compara lo contado con lo esperado.",
                ],
            },
        ],
    )

def _metodo_btn_dyn(metodo: MetodoPagoView) -> rx.Component:
    """Botón de método de pago renderizado desde la config (Efectivo, Yape…)."""
    activo = FoodState.caja_cobro_metodo == metodo.codigo
    return rx.box(
        rx.text(metodo.icono, font_size="15px", line_height="1"),
        rx.text(metodo.nombre, font_size="12px", font_weight="700",
                color=rx.cond(activo, "#FFFFFF", "var(--twk-slate-400)"),
                text_align="center", line_height="1.1"),
        on_click=FoodState.set_caja_cobro_metodo(metodo.codigo),
        background=rx.cond(activo, ACCENT, DARK_800),
        border=rx.cond(activo, "2px solid #EA580C", "2px solid var(--twk-d700)"),
        border_radius="10px",
        padding="9px 4px",
        cursor="pointer",
        display="flex",
        flex_direction="column",
        align_items="center",
        gap="4px",
        transition="all 0.15s ease",
        _hover={"border": "2px solid #EA580C"},
    )


def _caja_item_row(item: CajaItemView, idx: int) -> rx.Component:
    asignado = item.asignado_pago > 0
    return rx.box(
        rx.grid(
            rx.cond(
                FoodState.caja_split_por_items,
                rx.cond(
                    asignado,
                    rx.badge(
                        "Pago " + item.asignado_pago.to_string(),
                        background="rgba(59,130,246,0.12)", color="#3B82F6",
                        font_size="9px", font_weight="700",
                        border_radius="4px", padding_x="4px", padding_y="1px",
                    ),
                    rx.icon(
                        tag=rx.cond(item.seleccionado, "square_check_big", "square"),
                        size=16,
                        color=rx.cond(item.seleccionado, ACCENT, TEXT_MUTED),
                        cursor="pointer",
                        on_click=FoodState.toggle_split_item_sel(idx),
                    ),
                ),
                rx.fragment(),
            ),
            rx.vstack(
                rx.text(item.producto_nombre, font_size="13px", font_weight="600",
                        color=rx.cond(asignado & FoodState.caja_split_por_items, "var(--twk-slate-400)", "var(--twk-text-primary)")),
                rx.cond(
                    item.notas != "",
                    rx.text(item.notas, font_size="11px", color=TEXT_MUTED),
                    rx.text(item.precio_unitario_texto + " c/u", font_size="11px", color=TEXT_MUTED),
                ),
                spacing="0", align="start",
            ),
            rx.text("×" + item.cantidad.to_string(), font_size="13px", font_weight="600",
                    color="var(--twk-slate-300)", text_align="center"),
            rx.text(item.subtotal_texto, font_size="13px", font_weight="700",
                    color=rx.cond(asignado & FoodState.caja_split_por_items, "var(--twk-slate-400)", "var(--twk-text-primary)"),
                    text_align="right"),
            # Quitar ítem de la cuenta (mesa o pedido para llevar), fuera del
            # modo dividido.
            rx.cond(
                FoodState.caja_cobro_activo & ~FoodState.caja_split_por_items,
                rx.tooltip(
                    rx.icon(
                        tag="x", size=15, color=TEXT_MUTED, cursor="pointer",
                        on_click=FoodState.caja_solicitar_quitar(item.detalle_id).stop_propagation,
                        _hover={"color": "#EF4444"},
                    ),
                    content="Quitar producto de la cuenta",
                ),
                rx.fragment(),
            ),
            columns=rx.cond(
                FoodState.caja_split_por_items,
                "32px 1fr 50px 80px",
                "1fr 50px 80px 28px",
            ),
            gap="8px", align_items="center", width="100%",
        ),
        padding="12px 16px",
        border_bottom=f"1px solid {DARK_700}",
        background=rx.cond(
            item.seleccionado & FoodState.caja_split_por_items,
            "rgba(234,88,12,0.08)",
            rx.cond(asignado & FoodState.caja_split_por_items, "var(--twk-d900)", "transparent"),
        ),
        width="100%",
        cursor=rx.cond(
            FoodState.caja_split_por_items & ~asignado,
            "pointer", "default",
        ),
        on_click=rx.cond(
            FoodState.caja_split_por_items & ~asignado,
            FoodState.toggle_split_item_sel(idx),
            None,
        ),
    )


def _pago_staged_chip(pago: PagoStagedView, idx) -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.text(pago.metodo_label, font_size="12px", font_weight="700", color="var(--twk-slate-300)"),
            rx.text(pago.monto_texto, font_size="12px", font_weight="800", color=TEXT_PRIMARY),
            rx.icon(
                tag="x", size=13, color=TEXT_MUTED, cursor="pointer",
                on_click=FoodState.quitar_pago_staged(idx),
            ),
            spacing="2", align="center",
        ),
        rx.cond(
            pago.items_texto != "",
            rx.text(pago.items_texto, font_size="10px", color=TEXT_MUTED,
                    no_of_lines=1, max_width="200px"),
            rx.fragment(),
        ),
        spacing="0", align="start",
        background=PAGE_BACKGROUND, border=f"1px solid {DARK_700}",
        border_radius="12px", padding="6px 12px",
    )


def _pagos_divididos_panel() -> rx.Component:
    """Panel de pagos múltiples: cuenta dividida entre comensales o pago mixto."""
    return rx.box(
        rx.hstack(
            rx.text("Pagos de la cuenta", font_size="12px", font_weight="700", color=TEXT_MUTED,
                    text_transform="uppercase", letter_spacing="0.05em"),
            rx.spacer(),
            rx.hstack(
                styled_switch(
                    FoodState.caja_split_por_items,
                    FoodState.set_caja_split_por_items,
                    size="sm",
                ),
                rx.text("Por ítems", font_size="10px", color=TEXT_MUTED, font_weight="600"),
                spacing="1", align="center",
            ),
            width="100%", align="center", margin_bottom="12px",
        ),
        rx.vstack(
            # Subtotal de selección (solo en split por ítems)
            rx.cond(
                FoodState.caja_split_por_items & FoodState.caja_split_hay_seleccion,
                rx.hstack(
                    rx.text("Subtotal selección:", font_size="11px", font_weight="600", color=ACCENT),
                    rx.text(FoodState.caja_split_subtotal_sel_texto, font_size="13px",
                            font_weight="800", color=ACCENT),
                    spacing="2", align="center", width="100%",
                    background="rgba(234,88,12,0.08)", border="1px solid rgba(234,88,12,0.40)",
                    border_radius="8px", padding="6px 10px",
                ),
                rx.fragment(),
            ),
            rx.hstack(
                rx.select(
                    FoodState.metodos_pago_codigos,
                    value=FoodState.caja_pago_staged_metodo,
                    on_change=FoodState.set_caja_pago_staged_metodo,
                    width="130px",
                ),
                rx.cond(
                    FoodState.caja_split_por_items,
                    rx.fragment(),
                    rx.input(
                        placeholder="Monto (vacío = restante)",
                        value=FoodState.caja_pago_staged_monto,
                        on_change=FoodState.set_caja_pago_staged_monto,
                        type="number", min="0", step="0.50",
                        flex="1",
                        background=PAGE_BACKGROUND, border=f"1px solid {DARK_700}",
                        border_radius="8px", font_size="13px",
                        padding_x="10px",
                        _focus={"border_color": ACCENT},
                    ),
                ),
                rx.button(
                    rx.cond(FoodState.caja_split_por_items, "Asignar pago", "Agregar"),
                    on_click=FoodState.agregar_pago_staged,
                    background=ACCENT, color=TEXT_WHITE,
                    border_radius="8px", font_size="13px", font_weight="700",
                    cursor="pointer", _hover={"background": ACCENT_HOVER},
                ),
                spacing="2", width="100%", align="center", flex_wrap="wrap",
            ),
            # Botón "Seleccionar restantes" en split mode
            rx.cond(
                FoodState.caja_split_por_items & ~FoodState.caja_split_todos_asignados,
                rx.button(
                    "Seleccionar restantes",
                    on_click=FoodState.seleccionar_todos_restantes,
                    background="transparent", color="var(--twk-info-text)",
                    border="0.5px solid #BFDBFE", border_radius="6px",
                    font_size="11px", font_weight="600", cursor="pointer",
                    padding_x="8px", padding_y="4px",
                    _hover={"background": "rgba(59,130,246,0.08)"},
                ),
                rx.fragment(),
            ),
            rx.cond(
                FoodState.caja_pagos_staged.length() > 0,
                rx.flex(
                    rx.foreach(FoodState.caja_pagos_staged, _pago_staged_chip),
                    gap="8px", width="100%", flex_wrap="wrap",
                ),
                rx.cond(
                    FoodState.caja_split_por_items,
                    rx.text("Selecciona ítems en la lista y asigna un pago por comensal.",
                            font_size="12px", color=TEXT_MUTED),
                    rx.text("Agrega un pago por comensal o por método.",
                            font_size="12px", color=TEXT_MUTED),
                ),
            ),
            rx.hstack(
                rx.cond(
                    FoodState.caja_pagos_cubierto,
                    rx.badge(
                        "Cuenta cubierta ✓", background="rgba(34,197,94,0.12)", color=SUCCESS_TEXT,
                        border_radius="8px", font_size="12px", font_weight="700",
                        padding_x="10px", padding_y="4px",
                    ),
                    rx.badge(
                        "Restante: " + FoodState.caja_pagos_restante_texto,
                        background="rgba(245,158,11,0.12)", color=WARNING_TEXT,
                        border_radius="8px", font_size="12px", font_weight="700",
                        padding_x="10px", padding_y="4px",
                    ),
                ),
                rx.spacer(),
                rx.cond(
                    FoodState.caja_pagos_vuelto_texto != "",
                    rx.text("Vuelto: " + FoodState.caja_pagos_vuelto_texto,
                            font_size="13px", font_weight="700", color=SUCCESS_TEXT),
                    rx.fragment(),
                ),
                width="100%", align="center",
            ),
            spacing="3", width="100%",
        ),
        background=SURFACE_BASE, border=f"1px solid {DARK_700}",
        border_radius="14px", padding="18px", width="100%",
    )


def _cobro_panel() -> rx.Component:
    return rx.vstack(
        # Header: espeja el ancho de las 2 columnas de abajo (recibo | terminal),
        # con cada título centrado sobre su card.
        rx.flex(
            # Centrado sobre la card central (recibo / lista de productos).
            rx.box(
                rx.vstack(
                    rx.text(FoodState.caja_cobro_mesa_nombre, font_size="18px", font_weight="800",
                            color=TEXT_PRIMARY, text_align="center"),
                    rx.text("Consumo pendiente de cobro", font_size="12px", color=TEXT_MUTED,
                            text_align="center"),
                    spacing="0", align="center",
                ),
                flex="1", min_width="0",
                display="flex", align_items="center", justify_content="center",
            ),
            # Centrado sobre el terminal (encima de TOTAL A COBRAR).
            rx.box(
                rx.badge(
                    "Cuenta pedida", background="rgba(239,68,68,0.12)", color=DANGER_TEXT,
                    border_radius="20px", font_size="11px", font_weight="700",
                    padding_x="12px", padding_y="5px",
                ),
                width=rx.breakpoints(initial="100%", lg="340px"),
                min_width=rx.breakpoints(initial="100%", lg="340px"),
                flex_shrink="0",
                display="flex", align_items="center", justify_content="center",
            ),
            gap="16px", width="100%", align="center",
            direction=rx.breakpoints(initial="column", lg="row"),
        ),
        # 2 columnas: recibo (items) | terminal de pago. El terminal define la
        # altura visible; el recibo se acota con max_height y scrollea por dentro
        # hasta llegar al nivel de las acciones inferiores del terminal.
        rx.flex(
            # ── Columna izquierda: recibo (solo items + promos + subtotal) ──
            rx.vstack(
                rx.vstack(
                    rx.hstack(
                        rx.text("PRODUCTO", flex="1", font_size="9px", font_weight="600",
                                color=TEXT_MUTED, text_transform="uppercase", letter_spacing="0.06em"),
                        rx.text("CANT.", width="50px", text_align="center", font_size="9px",
                                font_weight="600", color=TEXT_MUTED, text_transform="uppercase"),
                        rx.text("TOTAL", width="80px", text_align="right", font_size="9px",
                                font_weight="600", color=TEXT_MUTED, text_transform="uppercase"),
                        padding="9px 16px", border_bottom="0.5px solid var(--twk-text-primary)", width="100%",
                    ),
                    rx.cond(
                        FoodState.caja_cobro_items.length() > 0,
                        rx.box(
                            rx.foreach(FoodState.caja_cobro_items, _caja_item_row),
                            width="100%", overflow_y="auto", flex="1", min_height="0",
                        ),
                        rx.center(
                            rx.text("Sin items registrados.", font_size="13px", color=TEXT_MUTED),
                            padding_y="20px", width="100%",
                        ),
                    ),
                    # Agregar productos a la cuenta (mesa o pedido para llevar).
                    rx.cond(
                        FoodState.caja_cobro_activo,
                        rx.button(
                            rx.hstack(
                                rx.icon(tag="plus", size=14),
                                rx.text("Agregar productos"),
                                spacing="2", align="center",
                            ),
                            on_click=FoodState.caja_abrir_add,
                            background="transparent", color=ACCENT,
                            border=f"1px dashed {ACCENT}", border_radius="8px",
                            font_size="12px", font_weight="700", width="100%",
                            cursor="pointer", margin="8px 14px", padding_y="8px",
                            _hover={"background": "rgba(234,88,12,0.08)"},
                        ),
                        rx.fragment(),
                    ),
                    rx.cond(
                        FoodState.caja_promo_aplicada_nombre != "",
                        rx.hstack(
                            rx.icon(tag="badge_percent", size=12, color="#16A34A"),
                            rx.text(
                                "Promo: " + FoodState.caja_promo_aplicada_nombre
                                + " · " + FoodState.caja_promo_aplicada_texto + " descontado",
                                font_size="11px", color=SUCCESS_TEXT, font_weight="600",
                            ),
                            rx.spacer(),
                            rx.button(
                                "Quitar", on_click=FoodState.quitar_promo_aplicada,
                                background="transparent", color=TEXT_MUTED, border="none",
                                font_size="10px", cursor="pointer", padding="0",
                            ),
                            width="100%", align="center", gap="6px",
                            padding="5px 14px",
                            background="rgba(34,197,94,0.08)", border_top="0.5px solid #BBF7D0",
                        ),
                        rx.fragment(),
                    ),
                    rx.cond(
                        FoodState.hay_promo_activa & (FoodState.caja_promo_aplicada_nombre == ""),
                        rx.hstack(
                            rx.icon(tag="zap", size=12, color=ACCENT),
                            rx.text(
                                "Promo: " + FoodState.promo_activa_nombre
                                + " · " + FoodState.promo_activa_descuento_texto,
                                font_size="11px", color="#C2410C", font_weight="600",
                            ),
                            rx.spacer(),
                            rx.button(
                                "Aplicar", on_click=FoodState.aplicar_promo_al_cobro,
                                background=ACCENT, color=TEXT_WHITE,
                                border_radius="5px", font_size="10px", font_weight="700",
                                padding_x="8px", padding_y="3px", cursor="pointer",
                            ),
                            width="100%", align="center", gap="6px",
                            padding="5px 14px",
                            background="rgba(234,88,12,0.08)", border_top="0.5px solid rgba(234,88,12,0.40)",
                        ),
                        rx.fragment(),
                    ),
                    rx.hstack(
                        rx.text("Subtotal items", font_size="13px", font_weight="600", color="var(--twk-slate-300)"),
                        rx.spacer(),
                        rx.text(FoodState.caja_cobro_total_base_texto, font_size="20px",
                                font_weight="800", color="var(--twk-slate-300)", letter_spacing="-0.5px"),
                        align="center", padding="10px 16px", width="100%",
                        border_top=f"1px solid {DARK_700}",
                    ),
                    spacing="0",
                    border=f"1px solid {DARK_700}", border_radius="12px",
                    background=DARK_800, overflow="hidden",
                    # En desktop la card se posiciona ABSOLUTA dentro de su columna
                    # (que se estira a la altura del terminal). Al ser absoluta no
                    # aporta alto, así el recibo NUNCA estira la fila: la lista
                    # scrollea por dentro y el subtotal queda fijo abajo, al nivel
                    # de las acciones inferiores del terminal — sin números mágicos.
                    min_width="0", width="100%", min_height="0",
                    display="flex", flex_direction="column",
                    position=rx.breakpoints(initial="static", lg="absolute"),
                    top="0", left="0", right="0", bottom="0",
                ),
                # Columna del recibo: contenedor relativo que se estira (align
                # stretch de la fila) a la altura del terminal.
                flex="1", min_width="0", width="100%", min_height="0",
                position=rx.breakpoints(initial="static", lg="relative"),
                overflow=rx.breakpoints(initial="visible", lg="hidden"),
            ),
            # ── Columna derecha: terminal completo de cobro ─────────────
            rx.vstack(
                # Display total final
                rx.vstack(
                    rx.text("TOTAL A COBRAR", font_size="9px", color=TEXT_MUTED,
                            text_transform="uppercase", letter_spacing="0.1em"),
                    rx.text(FoodState.caja_cobro_total_final_texto, font_size="26px",
                            font_weight="800", color="#FB923C", letter_spacing="-0.5px"),
                    spacing="0", align="center",
                    background="rgba(234,88,12,0.06)", border_radius="12px",
                    border="1.5px solid rgba(234,88,12,0.55)",
                    box_shadow="0 0 0 3px rgba(234,88,12,0.10)",
                    padding="12px 18px", width="100%",
                ),
                # Ajustes: Descuento + Propina (grid 2 columnas)
                rx.grid(
                    rx.vstack(
                        rx.hstack(
                            rx.text(
                                rx.cond(FoodState.caja_cobro_descuento_es_pct, "Descuento %", "Descuento S/"),
                                font_size="11px", color=TEXT_MUTED, font_weight="600",
                            ),
                            rx.box(
                                rx.text(
                                    rx.cond(FoodState.caja_cobro_descuento_es_pct, "S/", "%"),
                                    font_size="10px", font_weight="700",
                                    color=rx.cond(FoodState.caja_cobro_descuento_es_pct, TEXT_MUTED, ACCENT),
                                ),
                                on_click=FoodState.toggle_descuento_modo,
                                padding="1px 5px",
                                border="1px solid var(--twk-slate-300)",
                                border_radius="4px",
                                cursor="pointer",
                                _hover={"background": DARK_700},
                            ),
                            align="center", spacing="1",
                        ),
                        rx.input(
                            placeholder=rx.cond(FoodState.caja_cobro_descuento_es_pct, "0", "0.00"),
                            value=FoodState.caja_cobro_descuento,
                            on_change=FoodState.set_caja_cobro_descuento,
                            type="number", min="0",
                            step=rx.cond(FoodState.caja_cobro_descuento_es_pct, "1", "0.50"),
                            font_size="13px", padding="5px 8px",
                            border=f"1px solid {DARK_700}", border_radius="8px",
                            width="100%", text_align="right",
                            _focus={"border_color": ACCENT},
                        ),
                        spacing="1", width="100%",
                    ),
                    rx.vstack(
                        rx.hstack(
                            rx.text("Propina S/", font_size="11px", color=TEXT_MUTED, font_weight="600"),
                            rx.spacer(),
                            *[
                                rx.box(
                                    rx.text(f"{p}%", font_size="10px", font_weight="700",
                                            color=rx.cond(FoodState.caja_cobro_propina_pct == p, "#FFFFFF", "var(--twk-slate-400)")),
                                    on_click=FoodState.seleccionar_propina_pct(p),
                                    padding="1px 6px",
                                    background=rx.cond(FoodState.caja_cobro_propina_pct == p, ACCENT, TEXT_PRIMARY),
                                    border_radius="4px",
                                    cursor="pointer",
                                    _hover={"opacity": "0.8"},
                                )
                                for p in [5, 10, 15]
                            ],
                            align="center", spacing="1", width="100%",
                        ),
                        rx.input(
                            placeholder="0.00",
                            value=FoodState.caja_cobro_propina,
                            on_change=FoodState.set_caja_cobro_propina,
                            type="number", min="0", step="0.50",
                            font_size="13px", padding="5px 8px",
                            border=f"1px solid {DARK_700}", border_radius="8px",
                            width="100%", text_align="right",
                            _focus={"border_color": ACCENT},
                        ),
                        spacing="1", width="100%",
                    ),
                    columns="2", gap="8px", width="100%",
                ),
                # Ajustes: Cupón + Recargo (grid 2 columnas)
                rx.grid(
                    rx.vstack(
                        rx.text("Cupón", font_size="11px", color=TEXT_MUTED, font_weight="600"),
                        rx.cond(
                            FoodState.caja_cupon_id_aplicado > 0,
                            rx.hstack(
                                rx.icon(tag="ticket_percent", size=13, color="#16A34A"),
                                rx.text(FoodState.caja_cupon_nombre_aplicado,
                                        font_size="11px", color=SUCCESS_TEXT, font_weight="600", no_of_lines=1),
                                rx.text("-" + FoodState.caja_cupon_descuento_aplicado,
                                        font_size="11px", color=SUCCESS_TEXT),
                                rx.icon(tag="x", size=13, color=TEXT_MUTED, cursor="pointer",
                                        on_click=FoodState.quitar_cupon_caja),
                                spacing="1", align="center",
                                padding="5px 8px",
                                border="1px solid #BBF7D0", border_radius="8px",
                                background="rgba(34,197,94,0.08)",
                            ),
                            rx.hstack(
                                rx.input(
                                    placeholder="Código",
                                    value=FoodState.caja_cupon_codigo,
                                    on_change=FoodState.set_caja_cupon_codigo,
                                    font_size="13px", padding="5px 8px",
                                    border=f"1px solid {DARK_700}", border_radius="8px",
                                    flex="1",
                                    _focus={"border_color": ACCENT},
                                ),
                                rx.button(
                                    "Aplicar", on_click=FoodState.aplicar_cupon_caja,
                                    background=ACCENT, color=TEXT_WHITE,
                                    border_radius="7px", font_size="11px", font_weight="600",
                                    padding_x="10px", padding_y="5px", cursor="pointer", border="none",
                                    _hover={"background": ACCENT_HOVER},
                                ),
                                spacing="1", align="center", width="100%",
                            ),
                        ),
                        rx.cond(
                            FoodState.caja_cupon_error != "",
                            rx.text(FoodState.caja_cupon_error, font_size="10px", color=DANGER_TEXT),
                            rx.fragment(),
                        ),
                        spacing="1", width="100%",
                    ),
                    rx.vstack(
                        rx.text("Recargo S/", font_size="11px", color=TEXT_MUTED, font_weight="600"),
                        rx.input(
                            placeholder="0.00",
                            value=FoodState.caja_cobro_recargo,
                            on_change=FoodState.set_caja_cobro_recargo,
                            type="number", min="0", step="0.50",
                            font_size="13px", padding="5px 8px",
                            border=f"1px solid {DARK_700}", border_radius="8px",
                            width="100%", text_align="right",
                            _focus={"border_color": ACCENT},
                        ),
                        rx.select(
                            ["Delivery", "Envases", "Servicio", "Otro"],
                            value=FoodState.caja_cobro_recargo_concepto,
                            on_change=FoodState.set_caja_cobro_recargo_concepto,
                            size="1",
                        ),
                        spacing="1", width="100%",
                    ),
                    columns="2", gap="8px", width="100%",
                ),
                # Método de pago (simple) o panel dividido
                rx.cond(
                    FoodState.caja_cobro_dividido,
                    _pagos_divididos_panel(),
                    rx.vstack(
                        rx.text("Forma de pago", font_size="9px", font_weight="600", color=TEXT_MUTED,
                                text_transform="uppercase", letter_spacing="0.07em"),
                        rx.grid(
                            rx.foreach(FoodState.metodos_pago_activos, _metodo_btn_dyn),
                            columns="3", gap="6px", width="100%",
                        ),
                        spacing="2", width="100%",
                    ),
                ),
                # Toggle dividir (debajo de las formas de pago)
                rx.hstack(
                    styled_switch(
                        FoodState.caja_cobro_dividido,
                        FoodState.set_caja_cobro_dividido,
                    ),
                    rx.text("DIVIDIR / PAGO MIXTO", font_size="11px", font_weight="700",
                            color=TEXT_MUTED, letter_spacing="0.05em"),
                    spacing="2", align="center",
                ),
                # Selector de cliente para fiado
                rx.cond(
                    FoodState.caja_cobro_es_fiado | FoodState.caja_pagos_tiene_fiado,
                    rx.vstack(
                        rx.hstack(
                            rx.text("Cliente", font_size="11px", font_weight="700", color="var(--twk-slate-300)"),
                            rx.text("*", font_size="11px", font_weight="700", color=DANGER_TEXT),
                            rx.text("(fiado)", font_size="11px", color=TEXT_MUTED),
                            spacing="1", align="center",
                        ),
                        rx.select(
                            FoodState.clientes_activos_nombres,
                            value=FoodState.caja_cobro_cliente_nombre,
                            on_change=FoodState.set_caja_cobro_cliente_nombre,
                            placeholder="— Seleccionar cliente —",
                            background=DARK_800, color=TEXT_PRIMARY,
                            border="1px solid #EA580C", border_radius="8px",
                            font_size="13px", width="100%",
                        ),
                        spacing="2", width="100%",
                    ),
                    rx.fragment(),
                ),
                # Efectivo recibido (solo efectivo en modo simple)
                rx.cond(
                    FoodState.caja_cobro_es_efectivo & ~FoodState.caja_cobro_dividido,
                    rx.vstack(
                        rx.text("Efectivo recibido S/", font_size="11px", font_weight="600", color=TEXT_MUTED),
                        rx.input(
                            placeholder="0.00",
                            value=FoodState.caja_cobro_efectivo_recibido,
                            on_change=FoodState.set_caja_cobro_efectivo_recibido,
                            type="number", min="0", step="0.50",
                            font_size="18px", font_weight="800", text_align="right",
                            color=TEXT_PRIMARY,
                            border="1.5px solid var(--twk-slate-300)", border_radius="8px",
                            width="100%", height="44px",
                            _focus={"border_color": ACCENT},
                        ),
                        rx.cond(
                            FoodState.caja_cobro_efectivo_recibido != "",
                            rx.hstack(
                                rx.text("Vuelto", font_size="10px", color="#16A34A", font_weight="500"),
                                rx.spacer(),
                                rx.text(FoodState.caja_cobro_vuelto_texto, font_size="14px",
                                        font_weight="700", color="#16A34A"),
                                width="100%", align="center", padding="5px 10px",
                                background="rgba(34,197,94,0.08)",
                                border="0.5px solid rgba(34,197,94,0.3)", border_radius="7px",
                            ),
                            rx.fragment(),
                        ),
                        spacing="2", width="100%",
                    ),
                    rx.fragment(),
                ),
                # Error de cobro
                rx.cond(
                    FoodState.caja_cobro_error != "",
                    rx.hstack(
                        rx.icon(tag="circle_alert", size=13, color="var(--twk-danger-text)"),
                        rx.text(FoodState.caja_cobro_error, font_size="11px",
                                color="var(--twk-danger-text)", font_weight="600"),
                        spacing="2", align="center",
                        background="rgba(239,68,68,0.08)", border="1px solid #FECACA",
                        border_radius="7px", padding="8px 10px", width="100%",
                    ),
                    rx.fragment(),
                ),
                # Botón confirmar
                rx.button(
                    "Confirmar cobro",
                    on_click=FoodState.confirmar_cobro,
                    is_loading=FoodState.caja_cobrando,
                    font_size="15px", font_weight="700",
                    text_transform="uppercase", letter_spacing="0.05em",
                    background=ACCENT, color=TEXT_WHITE,
                    border_radius="10px", border="none",
                    padding="14px 12px", cursor="pointer", width="100%",
                    _hover={"background": ACCENT_HOVER},
                ),
                # Acciones secundarias
                rx.hstack(
                    rx.cond(
                        FoodState.caja_cobro_pedido_id == 0,
                        rx.button(
                            rx.hstack(rx.icon(tag="printer", size=12), rx.text("Pre-cuenta"),
                                      spacing="1", align="center"),
                            on_click=FoodState.imprimir_precuenta(FoodState.caja_cobro_mesa_id),
                            background="transparent", color="var(--twk-info-text)",
                            border="0.5px solid #BFDBFE", border_radius="8px",
                            font_size="12px", font_weight="600", cursor="pointer",
                            _hover={"background": "rgba(59,130,246,0.08)"}, flex="1", padding_y="7px",
                        ),
                        rx.fragment(),
                    ),
                    rx.cond(
                        FoodState.caja_cobro_pedido_id == 0,
                        rx.button(
                            rx.hstack(rx.icon(tag="ban", size=12), rx.text("Anular"),
                                      spacing="1", align="center"),
                            on_click=FoodState.abrir_anulacion_pedido_abierto(FoodState.caja_cobro_mesa_id),
                            background="transparent", color=DANGER_TEXT,
                            border="0.5px solid #FECACA", border_radius="8px",
                            font_size="12px", font_weight="600", cursor="pointer",
                            _hover={"background": "rgba(239,68,68,0.10)"}, flex="1", padding_y="7px",
                        ),
                        rx.fragment(),
                    ),
                    rx.button(
                        "Cancelar",
                        on_click=FoodState.cancelar_cobro,
                        background="transparent", color=TEXT_MUTED,
                        border="0.5px solid var(--twk-d700)", border_radius="8px",
                        font_size="12px", font_weight="600", cursor="pointer",
                        _hover={"background": DARK_700}, flex="1", padding_y="7px",
                    ),
                    spacing="2", width="100%",
                ),
                spacing="3",
                width=rx.breakpoints(initial="100%", lg="340px"),
                min_width=rx.breakpoints(initial="100%", lg="340px"),
                flex_shrink="0",
            ),
            # align stretch: la columna del recibo se estira a la altura del
            # terminal (que define el alto por su contenido fijo).
            gap="16px", width="100%", align="stretch",
            direction=rx.breakpoints(initial="column", lg="row"),
        ),
        spacing="3", width="100%",
    )


def _para_llevar_card(pedido: MostradorPendienteView) -> rx.Component:
    seleccionado = FoodState.caja_cobro_pedido_id == pedido.pedido_id
    return rx.box(
        rx.box(
            rx.hstack(
                rx.vstack(
                    rx.hstack(
                        rx.text(pedido.cliente_nombre, font_size="14px", font_weight="700",
                                color=rx.cond(seleccionado, ACCENT, "var(--twk-slate-300)")),
                        rx.text("#" + pedido.pedido_id.to_string(),
                                font_size="13px", font_weight="800", color=ACCENT),
                        spacing="2", align="center",
                    ),
                    rx.text(pedido.items_resumen, font_size="11px", color=TEXT_MUTED, no_of_lines=2),
                    spacing="0", align="start",
                ),
                rx.spacer(),
                rx.vstack(
                    rx.text(pedido.total_texto, font_size="16px", font_weight="800",
                            color=rx.cond(seleccionado, ACCENT, "var(--twk-slate-300)")),
                    rx.cond(
                        pedido.en_cocina,
                        rx.badge("En cocina", background="rgba(245,158,11,0.12)", color=WARNING_TEXT,
                                 border_radius="20px", font_size="10px", font_weight="700",
                                 padding_x="8px", padding_y="2px"),
                        rx.badge("Listo", background="rgba(34,197,94,0.12)", color=SUCCESS_TEXT,
                                 border_radius="20px", font_size="10px", font_weight="700",
                                 padding_x="8px", padding_y="2px"),
                    ),
                    align="end", spacing="1",
                ),
                width="100%", align="center",
            ),
            on_click=FoodState.abrir_cobro_pedido_mostrador(pedido.pedido_id),
            cursor="pointer",
            padding="14px 16px",
        ),
        # Seleccioná el pedido para agregar o quitar productos en el panel central
        # (igual que una mesa). El "Editar" se quitó: ya no hace falta.
        background=rx.cond(seleccionado, "rgba(234,88,12,0.08)", "var(--twk-d800)"),
        border_left=rx.cond(seleccionado, "3px solid #EA580C", "3px solid transparent"),
        border_bottom=f"1px solid {DARK_700}",
        width="100%",
    )


def _mesa_sidebar_row(mesa: MesaView) -> rx.Component:
    seleccionada = FoodState.caja_cobro_mesa_id == mesa.id
    return rx.box(
        rx.hstack(
            rx.vstack(
                rx.text(
                    mesa.nombre, font_size="15px", font_weight="700",
                    color=rx.cond(seleccionada, ACCENT, "var(--twk-slate-300)"),
                ),
                rx.text(
                    mesa.items_total_count.to_string() + " items · " + mesa.tiempo_abierto_texto,
                    font_size="12px", color=TEXT_MUTED,
                ),
                spacing="0", align="start",
            ),
            rx.spacer(),
            rx.text(
                mesa.total_abierto_texto, font_size="17px", font_weight="800",
                color=rx.cond(seleccionada, "var(--twk-text-primary)", "var(--twk-slate-300)"),
            ),
            width="100%", align="center",
        ),
        on_click=FoodState.abrir_cobro_mesa(mesa.id),
        padding="14px 16px",
        background=rx.cond(seleccionada, "rgba(234,88,12,0.08)", "var(--twk-d800)"),
        border_left=rx.cond(seleccionada, "3px solid #EA580C", "3px solid transparent"),
        border_bottom=f"1px solid {DARK_700}",
        cursor="pointer",
        width="100%",
        _hover={"background": rx.cond(seleccionada, "rgba(234,88,12,0.08)", "var(--twk-d700)")},
    )


def _mesas_sidebar() -> rx.Component:
    mesas_cobrables = FoodState.mesas_por_cobrar
    # Cada sección ocupa la mitad de la card (flex 1) y scrollea por dentro, de
    # modo que ni "Mesas por cobrar" ni "Para llevar" se pisen entre sí cuando
    # crecen los pedidos: se scrollea dentro de cada mitad para elegir cuál cobrar.
    return rx.box(
        # ── Mitad superior: Mesas por cobrar ──
        rx.box(
            rx.box(
                rx.text("Mesas por cobrar", font_size="11px", font_weight="700", color=TEXT_MUTED,
                        text_transform="uppercase", letter_spacing="0.05em"),
                padding="14px 16px", border_bottom=f"1px solid {DARK_700}", flex_shrink="0",
            ),
            rx.box(
                rx.cond(
                    mesas_cobrables.length() > 0,
                    rx.vstack(
                        rx.foreach(mesas_cobrables, _mesa_sidebar_row),
                        spacing="0", width="100%",
                    ),
                    rx.center(
                        rx.text("No hay mesas abiertas.", font_size="13px", color=TEXT_MUTED),
                        padding_y="20px", width="100%",
                    ),
                ),
                flex="1", width="100%",
                overflow_y=rx.breakpoints(initial="visible", lg="auto"),
                min_height=rx.breakpoints(initial="auto", lg="0"),
            ),
            display="flex", flex_direction="column", width="100%", overflow="hidden",
            flex=rx.breakpoints(initial="0 0 auto", lg="1"),
            min_height=rx.breakpoints(initial="auto", lg="0"),
        ),
        # ── Mitad inferior: Para llevar (pedidos de Mostrador pendientes) ──
        rx.box(
            rx.box(
                rx.hstack(
                    rx.icon(tag="package", size=12, color=ACCENT),
                    rx.text("Para llevar", font_size="11px", font_weight="700", color=ACCENT,
                            text_transform="uppercase", letter_spacing="0.05em"),
                    spacing="1", align="center",
                ),
                padding="12px 16px",
                border_top=f"1px solid {DARK_700}", border_bottom=f"1px solid {DARK_700}",
                flex_shrink="0",
            ),
            rx.box(
                rx.cond(
                    FoodState.pedidos_mostrador_pendientes.length() > 0,
                    rx.vstack(
                        rx.foreach(FoodState.pedidos_mostrador_pendientes, _para_llevar_card),
                        spacing="0", width="100%",
                    ),
                    rx.center(
                        rx.text("Sin pedidos para llevar.", font_size="13px", color=TEXT_MUTED),
                        padding_y="20px", width="100%",
                    ),
                ),
                flex="1", width="100%",
                overflow_y=rx.breakpoints(initial="visible", lg="auto"),
                min_height=rx.breakpoints(initial="auto", lg="0"),
            ),
            display="flex", flex_direction="column", width="100%", overflow="hidden",
            flex=rx.breakpoints(initial="0 0 auto", lg="1"),
            min_height=rx.breakpoints(initial="auto", lg="0"),
        ),
        background=DARK_800,
        border=f"1px solid {DARK_700}",
        border_radius="14px",
        width=rx.breakpoints(initial="100%", lg="260px"),
        min_width=rx.breakpoints(initial="100%", lg="260px"),
        # En desktop la card se estira (align stretch de la fila) a la altura del
        # panel central, con las dos mitades (Mesas por cobrar / Para llevar) al
        # 50/50 y su fondo al nivel de "DIVIDIR"; en móvil crece con el contenido.
        min_height="0", overflow="hidden",
        display="flex", flex_direction="column",
        flex_shrink="0",
    )


def _resumen_dia() -> rx.Component:
    return rx.box(
        rx.text("Resumen del día", font_size="12px", font_weight="700", color=TEXT_MUTED,
                text_transform="uppercase", letter_spacing="0.05em", margin_bottom="16px"),
        rx.vstack(
            rx.box(
                rx.text("Ventas", font_size="11px", color=TEXT_MUTED, font_weight="600"),
                rx.text(ReportesState.dashboard_ventas_hoy_texto, font_size="22px", font_weight="800",
                        color=TEXT_PRIMARY, letter_spacing="-0.5px"),
                rx.text(
                    rx.cond(ReportesState.dashboard_ventas_trend_pct >= 0, "↑ ", "↓ ")
                    + ReportesState.dashboard_ventas_trend_pct.to_string() + "% vs ayer",
                    font_size="11px", font_weight="600",
                    color=rx.cond(ReportesState.dashboard_ventas_trend_pct >= 0, "#16A34A", "#DC2626"),
                ),
                background=PAGE_BACKGROUND, border_radius="10px", padding="14px", width="100%",
            ),
            rx.box(
                rx.text("Pedidos cobrados", font_size="11px", color=TEXT_MUTED, font_weight="600"),
                rx.text(ReportesState.dashboard_pedidos_hoy.to_string(), font_size="22px",
                        font_weight="800", color=TEXT_PRIMARY),
                rx.text(
                    rx.cond(ReportesState.dashboard_pedidos_trend >= 0, "↑ +", "↓ ")
                    + ReportesState.dashboard_pedidos_trend.to_string() + " vs ayer",
                    font_size="11px", font_weight="600",
                    color=rx.cond(ReportesState.dashboard_pedidos_trend >= 0, "#16A34A", "#DC2626"),
                ),
                background=PAGE_BACKGROUND, border_radius="10px", padding="14px", width="100%",
            ),
            rx.box(
                rx.text("Propinas", font_size="11px", color=TEXT_MUTED, font_weight="600"),
                rx.text(ReportesState.dashboard_propina_hoy_texto, font_size="22px",
                        font_weight="800", color=TEXT_PRIMARY),
                rx.text(
                    rx.cond(ReportesState.dashboard_propina_trend_pct >= 0, "↑ ", "↓ ")
                    + ReportesState.dashboard_propina_trend_pct.to_string() + "% vs ayer",
                    font_size="11px", font_weight="600",
                    color=rx.cond(ReportesState.dashboard_propina_trend_pct >= 0, "#16A34A", "#DC2626"),
                ),
                background=PAGE_BACKGROUND, border_radius="10px", padding="14px", width="100%",
            ),
            rx.link(
                rx.center(
                    rx.text("Ver reportes del día", font_size="13px", font_weight="600", color=TEXT_MUTED),
                    padding="12px", width="100%",
                ),
                href="/reportes",
                border=f"1px solid {DARK_700}", border_radius="10px", width="100%",
                _hover={"background": DARK_700},
            ),
            spacing="3", width="100%",
        ),
        background=DARK_800,
        border=f"1px solid {DARK_700}",
        border_radius="14px",
        padding="18px",
        width=rx.breakpoints(initial="100%", lg="260px"),
        min_width=rx.breakpoints(initial="100%", lg="260px"),
        flex_shrink="0",
    )


def _panel_central() -> rx.Component:
    return rx.box(
        rx.cond(
            FoodState.caja_cobro_activo,
            _cobro_panel(),
            # Sin mesa seleccionada no hay terminal que fije la altura; le damos un
            # alto de referencia para que la card de mesas no se encoja. No afecta
            # la vista de cobro (esta rama solo se ve sin mesa elegida).
            rx.box(
                empty_state(
                    icono="credit_card",
                    titulo="Selecciona una mesa para cobrar",
                    texto="Elige una mesa de la lista de la izquierda para ver su consumo y cobrar. "
                          "Los pedidos para llevar aparecen más abajo.",
                ),
                width="100%",
                min_height=rx.breakpoints(initial="auto", lg="calc(100vh - 230px)"),
                display="flex", align_items="center", justify_content="center",
            ),
        ),
        flex="1", min_width="0", width="100%",
    )


# ─── Turno de caja ────────────────────────────────────────────────────────────

def _turno_cerrado_card() -> rx.Component:
    """Card de apertura de turno cuando no hay ninguno abierto."""
    return rx.box(
        rx.hstack(
            rx.icon(tag="lock", size=18, color="#D97706"),
            rx.vstack(
                rx.text("Caja cerrada", font_size="15px", font_weight="800", color=TEXT_PRIMARY),
                rx.text("Abre el turno con el fondo inicial para empezar a cobrar.",
                        font_size="12px", color=TEXT_MUTED),
                spacing="0", align="start",
            ),
            rx.spacer(),
            rx.hstack(
                rx.input(
                    placeholder="Fondo inicial S/",
                    value=FoodState.turno_apertura_monto,
                    on_change=FoodState.set_turno_apertura_monto,
                    type="number", min="0", step="0.50",
                    background=SURFACE_BASE, border=f"1px solid {DARK_700}",
                    border_radius="8px", padding_x="12px", padding_y="8px",
                    font_size="13px", width="150px",
                    _focus={"border_color": ACCENT},
                ),
                rx.button(
                    "Abrir turno",
                    on_click=FoodState.abrir_turno,
                    background=ACCENT, color=TEXT_WHITE,
                    border_radius="8px", font_size="13px", font_weight="700",
                    padding_x="16px", cursor="pointer",
                    _hover={"background": ACCENT_HOVER},
                ),
                rx.button(
                    "Historial",
                    on_click=FoodState.toggle_historial_turnos,
                    background=DARK_800, color=TEXT_MUTED,
                    border=f"1px solid {DARK_700}", border_radius="8px",
                    font_size="13px", font_weight="600", cursor="pointer",
                    _hover={"border_color": ACCENT},
                ),
                spacing="2", align="center",
            ),
            width="100%", align="center", gap="12px",
            flex_wrap="wrap",
        ),
        rx.cond(
            FoodState.turno_error != "",
            rx.text(FoodState.turno_error, font_size="12px", color="var(--twk-danger-text)",
                    font_weight="600", margin_top="8px"),
            rx.fragment(),
        ),
        background="rgba(245,158,11,0.10)", border="1px solid rgba(245,158,11,0.25)",
        border_radius="14px", padding="14px 18px", width="100%",
    )


def _turno_abierto_bar() -> rx.Component:
    """Barra de estado cuando el turno está abierto."""
    return rx.box(
        rx.hstack(
            rx.icon(tag="badge_check", size=18, color="#16A34A"),
            rx.vstack(
                rx.text("Turno abierto", font_size="14px", font_weight="800", color=TEXT_PRIMARY),
                rx.text(
                    "Desde " + FoodState.turno_abierto_desde_texto
                    + " · por " + FoodState.turno_abierto_por_nombre
                    + " · Fondo " + FoodState.turno_fondo_texto,
                    font_size="12px", color=TEXT_MUTED,
                ),
                spacing="0", align="start",
            ),
            rx.tooltip(
                rx.box(
                    rx.hstack(
                        rx.icon(tag="wallet", size=16, color="#16A34A"),
                        rx.vstack(
                            rx.text("EN CAJA AHORA", font_size="9px", font_weight="700",
                                    color=TEXT_MUTED, letter_spacing="0.06em"),
                            rx.text(FoodState.turno_efectivo_caja_texto, font_size="16px",
                                    font_weight="900", color="#16A34A", line_height="1.1"),
                            spacing="0", align="start",
                        ),
                        spacing="2", align="center",
                    ),
                    background="rgba(34,197,94,0.08)",
                    border="1px solid rgba(34,197,94,0.25)",
                    border_radius="10px", padding="6px 12px", margin_left="14px",
                ),
                content="Efectivo que debería haber en el cajón ahora: fondo + ventas en efectivo + ingresos − egresos.",
            ),
            rx.spacer(),
            rx.hstack(
                rx.button(
                    rx.hstack(rx.icon(tag="arrow_down_up", size=14), rx.text("Ingresos / Gastos"),
                              spacing="1", align="center"),
                    on_click=FoodState.abrir_mov_modal,
                    background=DARK_800, color="var(--twk-slate-300)",
                    border=f"1px solid {DARK_700}", border_radius="8px",
                    font_size="13px", font_weight="600", cursor="pointer",
                    _hover={"border_color": ACCENT},
                ),
                rx.button(
                    rx.hstack(rx.icon(tag="printer", size=14), rx.text("Últimos cobros"),
                              spacing="1", align="center"),
                    on_click=FoodState.toggle_ultimos_cobros,
                    background=DARK_800, color="var(--twk-slate-300)",
                    border=f"1px solid {DARK_700}", border_radius="8px",
                    font_size="13px", font_weight="600", cursor="pointer",
                    _hover={"border_color": ACCENT},
                ),
                rx.button(
                    "Historial",
                    on_click=FoodState.toggle_historial_turnos,
                    background=DARK_800, color=TEXT_MUTED,
                    border=f"1px solid {DARK_700}", border_radius="8px",
                    font_size="13px", font_weight="600", cursor="pointer",
                    _hover={"border_color": ACCENT},
                ),
                rx.button(
                    rx.hstack(rx.icon(tag="lock", size=14), rx.text("Cerrar turno"),
                              spacing="1", align="center"),
                    on_click=FoodState.abrir_cierre_turno,
                    background=PAGE_BACKGROUND, color=TEXT_PRIMARY,
                    border=f"1px solid {DARK_700}",
                    border_radius="8px", font_size="13px", font_weight="700",
                    cursor="pointer", _hover={"opacity": "0.9"},
                ),
                spacing="2", align="center",
            ),
            width="100%", align="center", gap="12px",
            flex_wrap="wrap",
        ),
        background="rgba(34,197,94,0.08)", border="1px solid #BBF7D0",
        border_radius="14px", padding="12px 18px", width="100%",
    )


def _turno_banner() -> rx.Component:
    return rx.cond(FoodState.turno_caja_abierto, _turno_abierto_bar(), _turno_cerrado_card())


def _mov_row(mov: MovimientoCajaView) -> rx.Component:
    es_ingreso = mov.tipo == "ingreso"
    return rx.hstack(
        rx.badge(
            mov.tipo_label,
            background=rx.cond(es_ingreso, "rgba(34,197,94,0.12)", "rgba(239,68,68,0.12)"),
            color=rx.cond(es_ingreso, "#22C55E", "var(--twk-danger-text)"),
            border_radius="6px", font_size="11px", font_weight="700",
        ),
        rx.vstack(
            rx.text(mov.motivo, font_size="13px", font_weight="600", color=TEXT_PRIMARY),
            rx.text(mov.categoria + " · " + mov.hora_texto + " · " + mov.usuario,
                    font_size="11px", color=TEXT_MUTED),
            spacing="0", align="start",
        ),
        rx.spacer(),
        rx.text(
            rx.cond(es_ingreso, "+", "-") + mov.monto_texto,
            font_size="14px", font_weight="800",
            color=rx.cond(es_ingreso, "#16A34A", "#DC2626"),
        ),
        # Corregir / eliminar (solo con permiso). Auditado en ambos casos.
        rx.cond(
            FoodState.tiene_perm_corregir,
            rx.cond(
                FoodState.turno_mov_confirm_delete_id == mov.id,
                rx.hstack(
                    rx.text("¿Eliminar?", font_size="11px", font_weight="700",
                            color=DANGER_TEXT),
                    rx.button(
                        "Sí", on_click=FoodState.eliminar_movimiento(mov.id),
                        size="1", background="#DC2626", color=TEXT_WHITE,
                        border_radius="6px", font_size="11px", font_weight="700",
                        cursor="pointer", _hover={"opacity": "0.9"},
                    ),
                    rx.button(
                        "No", on_click=FoodState.cancelar_borrar_movimiento,
                        size="1", variant="soft", color_scheme="gray",
                        border_radius="6px", font_size="11px", cursor="pointer",
                    ),
                    spacing="1", align="center",
                ),
                rx.hstack(
                    rx.tooltip(
                        rx.icon(
                            tag="pencil", size=15, color=TEXT_MUTED, cursor="pointer",
                            on_click=FoodState.iniciar_edicion_movimiento(mov.id),
                            _hover={"color": ACCENT},
                        ),
                        content="Corregir movimiento",
                    ),
                    rx.tooltip(
                        rx.icon(
                            tag="trash-2", size=15, color=TEXT_MUTED, cursor="pointer",
                            on_click=FoodState.pedir_borrar_movimiento(mov.id),
                            _hover={"color": "#DC2626"},
                        ),
                        content="Eliminar movimiento",
                    ),
                    spacing="3", align="center",
                ),
            ),
            rx.fragment(),
        ),
        width="100%", align="center", gap="10px",
        padding="10px 12px", border_bottom=f"1px solid {DARK_800}",
    )


def _mov_modal() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.hstack(
                    rx.dialog.title("Movimientos de caja", font_size="18px", font_weight="800", color=TEXT_PRIMARY, margin="0"),
                    rx.spacer(),
                    rx.icon(tag="x", size=18, color=TEXT_MUTED, cursor="pointer",
                            on_click=FoodState.cerrar_mov_modal),
                    width="100%", align="center",
                ),
                rx.hstack(
                    rx.text("Ingresos: " + FoodState.turno_ingresos_texto,
                            font_size="12px", font_weight="700", color="#16A34A"),
                    rx.text("Egresos: " + FoodState.turno_egresos_texto,
                            font_size="12px", font_weight="700", color=DANGER_TEXT),
                    spacing="4",
                ),
                # Formulario
                rx.box(
                    rx.vstack(
                        rx.cond(
                            FoodState.turno_mov_editando_id > 0,
                            rx.hstack(
                                rx.icon(tag="pencil", size=13, color=ACCENT),
                                rx.text(
                                    "Corrigiendo un movimiento — el cambio queda auditado.",
                                    font_size="11px", font_weight="700", color=ACCENT,
                                ),
                                spacing="1", align="center", width="100%",
                            ),
                            rx.fragment(),
                        ),
                        rx.hstack(
                            rx.select(
                                ["egreso", "ingreso"],
                                value=FoodState.turno_mov_tipo,
                                on_change=FoodState.set_turno_mov_tipo,
                                width="120px",
                            ),
                            rx.select(
                                FoodState.turno_mov_categorias,
                                value=FoodState.turno_mov_categoria,
                                on_change=FoodState.set_turno_mov_categoria,
                                width="170px",
                            ),
                            rx.input(
                                placeholder="Monto S/",
                                value=FoodState.turno_mov_monto,
                                on_change=FoodState.set_turno_mov_monto,
                                type="number", min="0", step="0.50",
                                width="110px",
                                background=SURFACE_BASE, border=f"1px solid {DARK_700}",
                                border_radius="8px", font_size="13px", color=TEXT_PRIMARY,
                                _focus={"border_color": ACCENT},
                            ),
                            spacing="2", width="100%", flex_wrap="wrap",
                        ),
                        rx.hstack(
                            rx.input(
                                placeholder="Motivo (ej: compra de mercado)",
                                value=FoodState.turno_mov_motivo,
                                on_change=FoodState.set_turno_mov_motivo,
                                flex="1",
                                background=SURFACE_BASE, border=f"1px solid {DARK_700}",
                                border_radius="8px", font_size="13px", color=TEXT_PRIMARY,
                                _focus={"border_color": ACCENT},
                            ),
                            rx.button(
                                rx.cond(
                                    FoodState.turno_mov_editando_id > 0,
                                    "Guardar cambios", "Registrar",
                                ),
                                on_click=FoodState.guardar_movimiento_caja,
                                is_loading=FoodState.caja_registrando_mov,
                                background=ACCENT, color=TEXT_WHITE,
                                border_radius="8px", font_size="13px", font_weight="700",
                                cursor="pointer", _hover={"background": ACCENT_HOVER},
                            ),
                            rx.cond(
                                FoodState.turno_mov_editando_id > 0,
                                rx.button(
                                    "Cancelar",
                                    on_click=FoodState.cancelar_edicion_movimiento,
                                    variant="soft", color_scheme="gray",
                                    border_radius="8px", font_size="13px",
                                    cursor="pointer",
                                ),
                                rx.fragment(),
                            ),
                            spacing="2", width="100%",
                        ),
                        rx.cond(
                            FoodState.turno_mov_error != "",
                            rx.text(FoodState.turno_mov_error, font_size="12px",
                                    color="var(--twk-danger-text)", font_weight="600"),
                            rx.fragment(),
                        ),
                        spacing="2", width="100%",
                    ),
                    background=SURFACE_BASE, border=f"1px solid {DARK_700}",
                    border_radius="10px", padding="12px", width="100%",
                ),
                # Lista
                rx.box(
                    rx.cond(
                        FoodState.turno_movimientos.length() > 0,
                        rx.vstack(
                            rx.foreach(FoodState.turno_movimientos, _mov_row),
                            spacing="0", width="100%",
                        ),
                        rx.center(
                            rx.text("Sin movimientos en este turno.", font_size="13px", color=TEXT_MUTED),
                            padding_y="20px", width="100%",
                        ),
                    ),
                    max_height="260px", overflow_y="auto", width="100%",
                    border=f"1px solid {DARK_800}", border_radius="10px",
                ),
                spacing="3", width="100%",
            ),
            max_width="560px",
            width="92vw",
            max_height="90vh",
            overflow_y="auto",
            background=PAGE_BACKGROUND,
            border=f"1px solid {DARK_800}",
        ),
        open=FoodState.turno_mov_modal_visible,
        on_open_change=FoodState.set_turno_mov_modal_visible,
    )


def _denominacion_row(row: DenominacionRow) -> rx.Component:
    return rx.hstack(
        rx.text(row.etiqueta, font_size="13px", color="var(--twk-slate-300)", width="140px"),
        rx.input(
            placeholder="0",
            value=row.cantidad,
            on_change=lambda v: FoodState.set_conteo_denominacion(row.key, v),
            type="number", min="0", step="1",
            width="70px", text_align="center",
            background=SURFACE_BASE, border=f"1px solid {DARK_700}",
            border_radius="7px", font_size="13px", color=TEXT_PRIMARY,
            _focus={"border_color": ACCENT},
        ),
        rx.spacer(),
        rx.text(row.subtotal_texto, font_size="13px", font_weight="700", color=TEXT_PRIMARY),
        width="100%", align="center", gap="8px",
    )


def _resumen_cierre_row(row: ResumenCierreRow) -> rx.Component:
    return rx.hstack(
        rx.text(
            row.etiqueta, font_size="13px",
            color=rx.cond(row.enfasis, TEXT_PRIMARY, TEXT_MUTED),
            font_weight=rx.cond(row.enfasis, "800", "400"),
        ),
        rx.spacer(),
        rx.text(
            row.monto_texto,
            font_size=rx.cond(row.enfasis, "14px", "13px"),
            font_weight=rx.cond(row.enfasis, "900", "700"),
            color=rx.cond(row.enfasis, ACCENT, "var(--twk-slate-300)"),
        ),
        width="100%", align="center",
    )


def _cierre_seccion(titulo: str, filas) -> rx.Component:
    """Bloque titulado del resumen de cierre (Caja / Otros cobros / Ventas)."""
    return rx.vstack(
        rx.text(titulo, font_size="10px", font_weight="700", color=TEXT_MUTED,
                text_transform="uppercase", letter_spacing="0.06em"),
        rx.foreach(filas, _resumen_cierre_row),
        spacing="1", width="100%", align="stretch",
    )


def _cierre_producto_row(row: CierreProductoRow) -> rx.Component:
    """Fila del resumen por producto en el modal de cierre (nombre + unidades)."""
    return rx.hstack(
        rx.text(row.nombre, font_size="12px", color=TEXT_MUTED,
                white_space="nowrap", overflow="hidden", text_overflow="ellipsis"),
        rx.spacer(),
        rx.text(row.cantidad_texto, font_size="12px", font_weight="700", color=TEXT_PRIMARY),
        width="100%", align="center", gap="8px",
        padding="6px 10px", border_bottom=f"1px solid {DARK_800}",
    )


def _cierre_modal() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.dialog.title("Cierre de turno — Arqueo", font_size="18px", font_weight="800", color=TEXT_PRIMARY, margin="0"),
                rx.flex(
                    # Columna resumen
                    rx.box(
                        rx.text("Resumen del turno", font_size="11px", font_weight="700",
                                color=TEXT_MUTED, text_transform="uppercase",
                                letter_spacing="0.05em", margin_bottom="10px"),
                        rx.vstack(
                            rx.foreach(FoodState.turno_cierre_resumen, _resumen_cierre_row),
                            rx.box(border_top="2px solid var(--twk-d700)", width="100%", padding_top="4px"),
                            rx.hstack(
                                rx.text("Total ingreso", font_size="14px",
                                        font_weight="800", color=TEXT_PRIMARY),
                                rx.spacer(),
                                rx.text(FoodState.turno_cierre_esperado_texto, font_size="16px",
                                        font_weight="900", color=ACCENT),
                                width="100%", align="center",
                            ),
                            rx.cond(
                                FoodState.turno_cierre_otros.length() > 0,
                                rx.vstack(
                                    rx.text("Ingresos por método", font_size="10px", font_weight="700",
                                            color=TEXT_MUTED, text_transform="uppercase",
                                            letter_spacing="0.06em", margin_top="6px"),
                                    rx.foreach(FoodState.turno_cierre_otros, _resumen_cierre_row),
                                    spacing="1", width="100%", align="stretch",
                                ),
                                rx.fragment(),
                            ),
                            spacing="2", width="100%",
                        ),
                        background=SURFACE_BASE, border=f"1px solid {DARK_700}",
                        border_radius="10px", padding="14px", flex="1", min_width="240px",
                    ),
                    # Columna arqueo
                    rx.box(
                        rx.text("Conteo de efectivo", font_size="11px", font_weight="700",
                                color=TEXT_MUTED, text_transform="uppercase",
                                letter_spacing="0.05em", margin_bottom="10px"),
                        rx.vstack(
                            rx.foreach(FoodState.turno_cierre_denominaciones, _denominacion_row),
                            spacing="1", width="100%",
                        ),
                        border=f"1px solid {DARK_700}", border_radius="10px",
                        padding="14px", flex="1", min_width="260px",
                        max_height="320px", overflow_y="auto",
                    ),
                    gap="14px", width="100%",
                    direction=rx.breakpoints(initial="column", md="row"),
                ),
                # Contado + descuadre
                rx.box(
                    rx.hstack(
                        rx.vstack(
                            rx.text("Contado", font_size="11px", color=TEXT_MUTED, font_weight="600"),
                            rx.text(FoodState.turno_cierre_contado_texto, font_size="18px",
                                    font_weight="800", color=TEXT_PRIMARY),
                            spacing="0", align="start",
                        ),
                        rx.spacer(),
                        rx.vstack(
                            rx.text("Descuadre", font_size="11px", color=TEXT_MUTED, font_weight="600"),
                            rx.text(FoodState.turno_cierre_descuadre_texto, font_size="18px",
                                    font_weight="900", color=FoodState.turno_cierre_descuadre_color),
                            spacing="0", align="end",
                        ),
                        width="100%", align="center",
                    ),
                    background=SURFACE_BASE, border=f"1px solid {DARK_700}",
                    border_radius="10px", padding="12px 16px", width="100%",
                ),
                rx.input(
                    placeholder="Notas del cierre (opcional)",
                    value=FoodState.turno_cierre_notas,
                    on_change=FoodState.set_turno_cierre_notas,
                    width="100%",
                    background=SURFACE_BASE, border=f"1px solid {DARK_700}",
                    border_radius="8px", font_size="13px", color=TEXT_PRIMARY,
                    _focus={"border_color": ACCENT},
                ),
                rx.cond(
                    FoodState.turno_cierre_error != "",
                    rx.text(FoodState.turno_cierre_error, font_size="12px",
                            color="var(--twk-danger-text)", font_weight="600"),
                    rx.fragment(),
                ),
                rx.hstack(
                    rx.button(
                        "Cancelar",
                        on_click=FoodState.cancelar_cierre_turno,
                        background=DARK_800, color=TEXT_MUTED,
                        border=f"1px solid {DARK_700}", border_radius="10px",
                        font_size="14px", font_weight="600", cursor="pointer",
                        _hover={"background": DARK_700}, flex="1",
                    ),
                    rx.button(
                        rx.hstack(rx.icon(tag="file_text", size=14), rx.text("Descargar PDF"),
                                  spacing="1", align="center"),
                        on_click=FoodState.descargar_pdf_cierre,
                        background="#DC2626", color=TEXT_WHITE,
                        border_radius="10px", font_size="14px", font_weight="700",
                        cursor="pointer", _hover={"opacity": "0.9"}, flex="1",
                    ),
                    rx.button(
                        rx.hstack(rx.icon(tag="lock", size=14), rx.text("Cerrar turno e imprimir"),
                                  spacing="1", align="center"),
                        on_click=FoodState.confirmar_cierre_turno,
                        is_loading=FoodState.turno_cerrando,
                        background="#7C3AED", color=TEXT_WHITE,
                        border_radius="10px", font_size="14px", font_weight="800",
                        cursor="pointer", _hover={"opacity": "0.9"}, flex="2",
                    ),
                    spacing="3", width="100%",
                ),
                spacing="3", width="100%",
            ),
            max_width="640px",
            width="92vw",
            max_height="90vh",
            overflow_y="auto",
            background=PAGE_BACKGROUND,
            border=f"1px solid {DARK_800}",
        ),
        open=FoodState.turno_cierre_visible,
        on_open_change=FoodState.set_turno_cierre_visible,
    )


def _turno_historial_row(t: TurnoHistorialView) -> rx.Component:
    return rx.hstack(
        rx.vstack(
            rx.text("Turno #" + t.id.to_string() + " · " + t.rango_texto,
                    font_size="13px", font_weight="600", color=TEXT_PRIMARY),
            rx.text("Cerró: " + t.cajero + " · Ventas " + t.ventas_texto,
                    font_size="11px", color=TEXT_MUTED),
            spacing="0", align="start",
        ),
        rx.spacer(),
        rx.vstack(
            rx.text("Esperado " + t.esperado_texto + " · Contado " + t.contado_texto,
                    font_size="11px", color=TEXT_MUTED),
            rx.text(t.descuadre_texto, font_size="13px", font_weight="800",
                    color=t.descuadre_color, text_align="right"),
            spacing="0", align="end",
        ),
        rx.tooltip(
            rx.icon_button(
                rx.icon(tag="eye", size=14),
                variant="ghost", size="1", color=TEXT_MUTED, cursor="pointer",
                on_click=FoodState.previsualizar_cierre_turno(t.id),
            ),
            content="Ver detalle del cierre",
        ),
        rx.tooltip(
            rx.icon_button(
                rx.icon(tag="printer", size=14),
                variant="ghost", size="1", color=TEXT_MUTED, cursor="pointer",
                on_click=FoodState.reimprimir_cierre_turno(t.id),
            ),
            content="Reimprimir cierre",
        ),
        rx.tooltip(
            rx.icon_button(
                rx.icon(tag="file_text", size=14),
                variant="ghost", size="1", color=TEXT_MUTED, cursor="pointer",
                on_click=FoodState.descargar_pdf_cierre_turno(t.id),
            ),
            content="Descargar PDF del cierre",
        ),
        width="100%", align="center", gap="10px",
        padding="10px 12px", border_bottom=f"1px solid {DARK_800}",
    )


def _historial_modal() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.hstack(
                    rx.dialog.title("Historial de turnos", font_size="18px", font_weight="800", color=TEXT_PRIMARY, margin="0"),
                    rx.spacer(),
                    rx.icon(tag="x", size=18, color=TEXT_MUTED, cursor="pointer",
                            on_click=FoodState.toggle_historial_turnos),
                    width="100%", align="center",
                ),
                rx.box(
                    rx.cond(
                        FoodState.turno_historial.length() > 0,
                        rx.vstack(
                            rx.foreach(FoodState.turno_historial, _turno_historial_row),
                            spacing="0", width="100%",
                        ),
                        rx.center(
                            rx.text("Todavía no hay turnos cerrados.", font_size="13px", color=TEXT_MUTED),
                            padding_y="20px", width="100%",
                        ),
                    ),
                    max_height="380px", overflow_y="auto", width="100%",
                    border=f"1px solid {DARK_800}", border_radius="10px",
                ),
                spacing="3", width="100%",
            ),
            max_width="600px",
            width="92vw",
            max_height="90vh",
            overflow_y="auto",
            background=PAGE_BACKGROUND,
            border=f"1px solid {DARK_800}",
        ),
        open=FoodState.turno_historial_visible,
        on_open_change=FoodState.set_turno_historial_visible,
    )


def _cierre_preview_pedido_row(p: CierrePreviewPedidoRow) -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.text(p.hora, font_size="11px", color=TEXT_MUTED, font_weight="600"),
            rx.text(p.mesa, font_size="12px", color=TEXT_PRIMARY, font_weight="700"),
            rx.spacer(),
            rx.text(p.neto_texto, font_size="12px", font_weight="800", color="var(--twk-slate-300)"),
            width="100%", align="center", gap="8px",
        ),
        rx.text("Método: " + p.metodo, font_size="11px", color=TEXT_MUTED),
        rx.cond(p.items_texto != "", rx.text(p.items_texto, font_size="11px", color=TEXT_MUTED, no_of_lines=2), rx.fragment()),
        rx.cond(
            p.extras != "",
            rx.text(p.extras, font_size="11px", color=ACCENT, font_weight="600"),
            rx.fragment(),
        ),
        spacing="0", width="100%", align="start",
        padding="8px 10px", border_bottom=f"1px solid {DARK_800}",
    )


def _cierre_preview_mov_row(m: CierrePreviewMovRow) -> rx.Component:
    return rx.hstack(
        rx.text(m.hora, font_size="11px", color=TEXT_MUTED, min_width="70px"),
        rx.text(m.tipo, font_size="11px", color=TEXT_PRIMARY, font_weight="700", min_width="60px"),
        rx.text(m.detalle, font_size="11px", color=TEXT_MUTED, no_of_lines=1, flex="1"),
        rx.text(m.monto_texto, font_size="11px", font_weight="700", color="var(--twk-slate-300)"),
        width="100%", align="center", gap="8px",
        padding="6px 10px", border_bottom=f"1px solid {DARK_800}",
    )


def _cierre_preview_modal() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.hstack(
                    rx.vstack(
                        rx.dialog.title("Detalle del cierre", font_size="17px", font_weight="800", color=TEXT_PRIMARY, margin="0"),
                        rx.text(FoodState.cierre_preview_titulo, font_size="12px", color=TEXT_MUTED),
                        spacing="0", align="start",
                    ),
                    rx.spacer(),
                    rx.icon(tag="x", size=18, color=TEXT_MUTED, cursor="pointer",
                            on_click=FoodState.set_cierre_preview_visible(False)),
                    width="100%", align="center",
                ),
                # Resumen de caja (efectivo, lo que se cuadra) + Ingresos por método.
                rx.box(
                    rx.vstack(
                        _cierre_seccion("Resumen de caja", FoodState.cierre_preview_arqueo),
                        rx.cond(
                            FoodState.cierre_preview_cobros.length() > 0,
                            rx.fragment(
                                rx.divider(),
                                _cierre_seccion("Ingresos por método", FoodState.cierre_preview_cobros),
                            ),
                            rx.fragment(),
                        ),
                        rx.text(
                            "Solo el efectivo se cuadra contra el cajón. \"Ingresos por "
                            "método\" es el desglose de todas las ventas; Yape y tarjeta "
                            "no entran al cajón.",
                            font_size="11px", color=TEXT_MUTED, line_height="1.4",
                        ),
                        rx.cond(
                            ~FoodState.cierre_preview_recon_cuadra,
                            rx.hstack(
                                rx.icon(tag="triangle_alert", size=13, color="#F59E0B"),
                                rx.text("Revisar cobros:", font_size="12px", color=TEXT_MUTED),
                                rx.spacer(),
                                rx.text(
                                    FoodState.cierre_preview_recon_texto,
                                    font_size="12px", font_weight="800", color="#F59E0B",
                                ),
                                width="100%", align="center", gap="6px",
                            ),
                            rx.fragment(),
                        ),
                        spacing="2", width="100%",
                    ),
                    padding="12px 14px", width="100%",
                    border=f"1px solid {DARK_800}", border_radius="10px",
                ),
                # Productos vendidos (resumen por producto)
                rx.text("Productos vendidos", font_size="12px", font_weight="800", color=TEXT_PRIMARY),
                rx.box(
                    rx.cond(
                        FoodState.cierre_preview_productos.length() > 0,
                        rx.vstack(
                            rx.foreach(FoodState.cierre_preview_productos, _cierre_producto_row),
                            spacing="0", width="100%",
                        ),
                        rx.center(rx.text("Sin ventas en el turno.", font_size="12px", color=TEXT_MUTED), padding_y="14px", width="100%"),
                    ),
                    max_height="240px", overflow_y="auto", width="100%",
                    border=f"1px solid {DARK_800}", border_radius="10px",
                ),
                # Movimientos (si hay)
                rx.cond(
                    FoodState.cierre_preview_movimientos.length() > 0,
                    rx.vstack(
                        rx.text("Movimientos de caja", font_size="12px", font_weight="800", color=TEXT_PRIMARY),
                        rx.box(
                            rx.vstack(
                                rx.foreach(FoodState.cierre_preview_movimientos, _cierre_preview_mov_row),
                                spacing="0", width="100%",
                            ),
                            max_height="140px", overflow_y="auto", width="100%",
                            border=f"1px solid {DARK_800}", border_radius="10px",
                        ),
                        spacing="1", width="100%", align="start",
                    ),
                    rx.fragment(),
                ),
                # Acciones
                rx.hstack(
                    rx.button(
                        rx.icon(tag="file_text", size=15), "Descargar PDF",
                        on_click=FoodState.descargar_pdf_cierre_turno(FoodState.cierre_preview_turno_id),
                        variant="soft", size="2", cursor="pointer", flex="1",
                    ),
                    rx.button(
                        rx.icon(tag="printer", size=15), "Reimprimir",
                        on_click=FoodState.reimprimir_cierre_desde_preview,
                        background=ACCENT, color="white", size="2",
                        cursor="pointer", _hover={"opacity": "0.9"}, flex="1",
                    ),
                    spacing="3", width="100%",
                ),
                spacing="3", width="100%",
            ),
            max_width="620px",
            width="92vw",
            max_height="90vh",
            overflow_y="auto",
            background=PAGE_BACKGROUND,
            border=f"1px solid {DARK_800}",
        ),
        open=FoodState.cierre_preview_visible,
        on_open_change=FoodState.set_cierre_preview_visible,
    )


def _ultimo_cobro_row(cobro: UltimoCobroView) -> rx.Component:
    return rx.hstack(
        rx.text(cobro.hora, font_size="13px", color=TEXT_MUTED, font_weight="600",
                min_width="50px"),
        rx.vstack(
            rx.text(cobro.referencia, font_size="13px", font_weight="700", color=TEXT_PRIMARY,
                    no_of_lines=1),
            rx.text(cobro.detalle, font_size="12px", color=TEXT_MUTED, no_of_lines=1),
            spacing="0", flex="1", min_width="0",
        ),
        rx.text(cobro.total_texto, font_size="13px", font_weight="700", color=SUCCESS_TEXT,
                min_width="80px", text_align="right"),
        rx.tooltip(
            rx.icon(tag="printer", size=16, color=ACCENT, cursor="pointer",
                    on_click=FoodState.reimprimir_comprobante(cobro.pedido_id),
                    _hover={"opacity": "0.7"}),
            content=rx.cond(cobro.comprobante_impreso, "Reimprimir comprobante", "Imprimir comprobante"),
        ),
        rx.cond(
            FoodState.tiene_perm_corregir,
            rx.tooltip(
                rx.icon(tag="pencil", size=16, color=ACCENT, cursor="pointer",
                        on_click=FoodState.abrir_correccion_cobro(cobro.pedido_id),
                        _hover={"opacity": "0.7"}),
                content="Corregir cobro",
            ),
            rx.fragment(),
        ),
        rx.cond(
            FoodState.tiene_perm_anular,
            rx.tooltip(
                rx.icon(tag="trash_2", size=16, color="#EF4444", cursor="pointer",
                        on_click=FoodState.abrir_reversion_cobro(cobro.pedido_id),
                        _hover={"opacity": "0.7"}),
                content="Anular cobro",
            ),
            rx.fragment(),
        ),
        width="100%", align="center", gap="10px",
        padding="10px 12px", border_bottom=f"1px solid {DARK_800}",
    )


def _ultimos_cobros_modal() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.hstack(
                    rx.hstack(
                        rx.icon(tag="receipt", size=20, color=ACCENT),
                        rx.dialog.title("Últimos cobros", font_size="18px", font_weight="800",
                                color=TEXT_PRIMARY, margin="0"),
                        spacing="2", align="center",
                    ),
                    rx.spacer(),
                    rx.icon(tag="x", size=18, color=TEXT_MUTED, cursor="pointer",
                            on_click=FoodState.toggle_ultimos_cobros,
                            _hover={"color": "var(--twk-text-primary)"}),
                    width="100%", align="center",
                ),
                rx.text("Últimas 20 ventas cobradas en el turno activo.",
                        font_size="12px", color=TEXT_MUTED),
                rx.box(
                    rx.cond(
                        FoodState.ultimos_cobros.length() > 0,
                        rx.vstack(
                            rx.foreach(FoodState.ultimos_cobros, _ultimo_cobro_row),
                            spacing="0", width="100%",
                        ),
                        rx.center(
                            rx.text("No hay cobros en este turno.",
                                    font_size="13px", color=TEXT_MUTED),
                            padding_y="20px", width="100%",
                        ),
                    ),
                    max_height="420px", overflow_y="auto", width="100%",
                    border=f"1px solid {DARK_800}", border_radius="10px",
                ),
                rx.dialog.close(
                    rx.button(
                        "Cerrar",
                        background=DARK_800, color=TEXT_MUTED,
                        border=f"1px solid {DARK_700}", border_radius="8px",
                        font_size="13px", font_weight="600", cursor="pointer",
                        width="100%",
                        _hover={"border_color": ACCENT, "color": TEXT_PRIMARY},
                    ),
                ),
                spacing="3", width="100%",
            ),
            max_width="650px",
            width="92vw",
            max_height="90vh",
            overflow_y="auto",
            background=PAGE_BACKGROUND,
            border=f"1px solid {DARK_800}",
        ),
        open=FoodState.ultimos_cobros_visible,
        on_open_change=FoodState.set_ultimos_cobros_visible,
    )


def _correccion_metodo_btn(metodo: MetodoPagoView) -> rx.Component:
    """Botón de método de pago para el modal de corrección."""
    activo = FoodState.correccion_metodo == metodo.codigo
    return rx.box(
        rx.text(metodo.icono, font_size="16px", line_height="1"),
        rx.text(metodo.nombre, font_size="11px", font_weight="700",
                color=rx.cond(activo, "#FFFFFF", "var(--twk-slate-400)"),
                text_align="center", line_height="1.1"),
        on_click=FoodState.set_correccion_metodo(metodo.codigo),
        background=rx.cond(activo, ACCENT, DARK_800),
        border=rx.cond(activo, "2px solid #EA580C", "2px solid var(--twk-d700)"),
        border_radius="10px", padding="8px 4px", cursor="pointer",
        display="flex", flex_direction="column", align_items="center", gap="3px",
        transition="all 0.15s ease", _hover={"border": "2px solid #EA580C"},
    )


def _correccion_linea_row(linea: CorreccionLineaView, idx: int) -> rx.Component:
    return rx.hstack(
        rx.vstack(
            rx.text(linea.nombre, font_size="13px", font_weight="700",
                    color=TEXT_PRIMARY, no_of_lines=1),
            rx.text(linea.subtotal_texto, font_size="11px", color=TEXT_MUTED),
            spacing="0", align="start", flex="1", min_width="0",
        ),
        rx.hstack(
            rx.icon(tag="circle_minus", size=18, color="var(--twk-slate-400)", cursor="pointer",
                    on_click=FoodState.correccion_dec_linea(idx),
                    _hover={"color": "#EF4444"}),
            rx.text(linea.cantidad, font_size="14px", font_weight="800",
                    color=TEXT_PRIMARY, min_width="24px", text_align="center"),
            rx.icon(tag="circle_plus", size=18, color=ACCENT, cursor="pointer",
                    on_click=FoodState.correccion_inc_linea(idx),
                    _hover={"opacity": "0.7"}),
            spacing="2", align="center",
        ),
        rx.icon(tag="trash_2", size=15, color="#EF4444", cursor="pointer",
                on_click=FoodState.correccion_quitar_linea(idx),
                _hover={"opacity": "0.7"}),
        width="100%", align="center", gap="10px",
        padding="8px 10px", border_bottom=f"1px solid {DARK_700}",
    )


def _correccion_modal() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.hstack(
                    rx.icon(tag="pencil", size=18, color=ACCENT),
                    rx.dialog.title("Corregir cobro — " + FoodState.correccion_referencia,
                            font_size="17px", font_weight="800", color=TEXT_PRIMARY, margin="0"),
                    rx.spacer(),
                    rx.icon(tag="x", size=18, color=TEXT_MUTED, cursor="pointer",
                            on_click=FoodState.cancelar_correccion),
                    width="100%", align="center",
                ),
                rx.text(
                    "Corrige esta misma venta (quitar/sumar productos, método, "
                    "descuento) sin anularla ni duplicarla. Queda registrada en "
                    "auditoría con el motivo.",
                    font_size="12px", color=TEXT_MUTED,
                ),
                # Líneas editables
                rx.box(
                    rx.foreach(FoodState.correccion_lineas, _correccion_linea_row),
                    width="100%", max_height="220px", overflow_y="auto",
                    border=f"1px solid {DARK_700}", border_radius="10px",
                ),
                # Agregar producto
                rx.select.root(
                    rx.select.trigger(
                        placeholder="+ Agregar producto…", width="100%",
                    ),
                    rx.select.content(
                        rx.foreach(
                            FoodState.correccion_productos,
                            lambda o: rx.select.item(o.label, value=o.id.to_string()),
                        ),
                    ),
                    value=FoodState.correccion_producto_sel,
                    on_change=FoodState.correccion_agregar_producto,
                    width="100%",
                ),
                # Método de pago
                rx.text("Método de pago", font_size="12px", font_weight="700",
                        color=TEXT_MUTED, margin_top="4px"),
                rx.grid(
                    rx.foreach(FoodState.metodos_pago_activos, _correccion_metodo_btn),
                    columns="4", spacing="2", width="100%",
                ),
                # Descuento / propina
                rx.hstack(
                    rx.vstack(
                        rx.text("Descuento (S/)", font_size="11px", color=TEXT_MUTED),
                        rx.input(
                            placeholder="0.00", value=FoodState.correccion_descuento,
                            on_change=FoodState.set_correccion_descuento,
                            type="number", width="100%",
                            background=SURFACE_BASE, border=f"1px solid {DARK_700}",
                            color=TEXT_PRIMARY, border_radius="8px", font_size="13px",
                            _focus={"border_color": ACCENT},
                        ),
                        spacing="1", flex="1",
                    ),
                    rx.vstack(
                        rx.text("Propina (S/)", font_size="11px", color=TEXT_MUTED),
                        rx.input(
                            placeholder="0.00", value=FoodState.correccion_propina,
                            on_change=FoodState.set_correccion_propina,
                            type="number", width="100%",
                            background=SURFACE_BASE, border=f"1px solid {DARK_700}",
                            color=TEXT_PRIMARY, border_radius="8px", font_size="13px",
                            _focus={"border_color": ACCENT},
                        ),
                        spacing="1", flex="1",
                    ),
                    spacing="3", width="100%",
                ),
                # Total
                rx.hstack(
                    rx.text("Total corregido", font_size="13px", font_weight="700",
                            color=TEXT_MUTED),
                    rx.spacer(),
                    rx.text(FoodState.correccion_total_texto, font_size="18px",
                            font_weight="800", color=SUCCESS_TEXT),
                    width="100%", align="center",
                ),
                # Motivo
                rx.input(
                    placeholder="Motivo de la corrección (obligatorio)",
                    value=FoodState.correccion_motivo,
                    on_change=FoodState.set_correccion_motivo,
                    width="100%", background=SURFACE_BASE, border=f"1px solid {DARK_700}",
                    color=TEXT_PRIMARY, border_radius="8px", font_size="13px",
                    _focus={"border_color": ACCENT},
                ),
                rx.cond(
                    FoodState.correccion_error != "",
                    rx.text(FoodState.correccion_error, font_size="12px",
                            color="#EF4444", font_weight="600"),
                    rx.fragment(),
                ),
                rx.hstack(
                    rx.button(
                        "Cancelar",
                        on_click=FoodState.cancelar_correccion,
                        background=DARK_800, color=TEXT_MUTED,
                        border=f"1px solid {DARK_700}", border_radius="10px",
                        font_size="14px", font_weight="600", cursor="pointer",
                        _hover={"background": "var(--twk-d700)", "color": "var(--twk-text-primary)"}, flex="1",
                    ),
                    rx.button(
                        "Guardar corrección",
                        on_click=FoodState.confirmar_correccion_cobro,
                        loading=FoodState.correccion_guardando,
                        background=ACCENT, color=TEXT_WHITE,
                        border_radius="10px", font_size="14px", font_weight="800",
                        cursor="pointer", _hover={"opacity": "0.9"}, flex="2",
                    ),
                    spacing="3", width="100%",
                ),
                spacing="3", width="100%",
            ),
            max_width="480px", width="94vw", max_height="92vh", overflow_y="auto",
            background=PAGE_BACKGROUND, border=f"1px solid {DARK_800}",
        ),
        open=FoodState.correccion_modal_visible,
        on_open_change=FoodState.set_correccion_modal_visible,
    )


def _reversion_modal() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.hstack(
                    rx.icon(tag="triangle_alert", size=18, color=DANGER_TEXT),
                    rx.dialog.title("Anular cobro — " + FoodState.reversion_referencia,
                            font_size="17px", font_weight="800", color=TEXT_PRIMARY, margin="0"),
                    spacing="2", align="center",
                ),
                rx.text(
                    "La venta se anulará definitivamente: se repondrá el stock, se revertirá "
                    "el fiado si lo hubo y la venta saldrá del arqueo. "
                    "Si necesitas cobrar de nuevo, crea un nuevo pedido. "
                    "La operación queda registrada en auditoría y reportes.",
                    font_size="13px", color=TEXT_MUTED,
                ),
                rx.input(
                    placeholder="Motivo de la anulación (obligatorio)",
                    value=FoodState.reversion_motivo,
                    on_change=FoodState.set_reversion_motivo,
                    width="100%",
                    background=SURFACE_BASE, border=f"1px solid {DARK_700}",
                    color=TEXT_PRIMARY,
                    border_radius="8px", font_size="13px",
                    _focus={"border_color": "#DC2626"},
                ),
                rx.cond(
                    FoodState.reversion_error != "",
                    rx.text(FoodState.reversion_error, font_size="12px",
                            color="#EF4444", font_weight="600"),
                    rx.fragment(),
                ),
                rx.hstack(
                    rx.button(
                        "Volver",
                        on_click=FoodState.cancelar_reversion,
                        background=DARK_800, color=TEXT_MUTED,
                        border=f"1px solid {DARK_700}", border_radius="10px",
                        font_size="14px", font_weight="600", cursor="pointer",
                        _hover={"background": "var(--twk-d700)", "color": "var(--twk-text-primary)"}, flex="1",
                    ),
                    rx.button(
                        "Confirmar anulación",
                        on_click=FoodState.confirmar_reversion_cobro,
                        background="#DC2626", color=TEXT_WHITE,
                        border_radius="10px", font_size="14px", font_weight="800",
                        cursor="pointer", _hover={"background": "#B91C1C"}, flex="2",
                    ),
                    spacing="3", width="100%",
                ),
                spacing="3", width="100%",
            ),
            max_width="440px",
            width="92vw",
            max_height="90vh",
            overflow_y="auto",
            background=PAGE_BACKGROUND,
            border=f"1px solid {DARK_800}",
        ),
        open=FoodState.reversion_modal_visible,
        on_open_change=FoodState.set_reversion_modal_visible,
    )


def _caja_add_producto_row(p: ProductoView) -> rx.Component:
    return rx.hstack(
        rx.text(p.emoji, font_size="18px"),
        rx.vstack(
            rx.text(p.nombre, font_size="13px", font_weight="600", color=TEXT_PRIMARY,
                    no_of_lines=1),
            rx.text(p.categoria_nombre, font_size="11px", color=TEXT_MUTED),
            spacing="0", align="start", flex="1", min_width="0",
        ),
        rx.text(p.precio_texto, font_size="13px", font_weight="700", color="var(--twk-slate-300)"),
        rx.icon(tag="circle_plus", size=18, color=ACCENT),
        on_click=FoodState.caja_agregar_producto(p.id),
        width="100%", align="center", gap="10px",
        padding="10px 12px", border_bottom=f"1px solid {DARK_700}",
        cursor="pointer", _hover={"background": DARK_800},
    )


def _caja_add_modal() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.hstack(
                    rx.dialog.title("Agregar a la cuenta", font_size="17px", font_weight="800",
                            color=TEXT_PRIMARY, margin="0"),
                    rx.spacer(),
                    rx.icon(tag="x", size=18, color=TEXT_MUTED, cursor="pointer",
                            on_click=FoodState.set_caja_add_modal(False)),
                    width="100%", align="center",
                ),
                rx.text(
                    "Se suman a esta misma cuenta. Lo que necesita cocina dispara su "
                    "comanda; lo que no (bebidas, porciones) va directo.",
                    font_size="12px", color=TEXT_MUTED,
                ),
                rx.input(
                    placeholder="Buscar producto...",
                    value=FoodState.caja_add_busqueda,
                    on_change=FoodState.set_caja_add_busqueda,
                    width="100%", background=SURFACE_BASE, border=f"1px solid {DARK_700}",
                    color=TEXT_PRIMARY, border_radius="8px", font_size="13px",
                    _focus={"border_color": ACCENT},
                ),
                rx.box(
                    rx.cond(
                        FoodState.caja_add_productos_filtrados.length() > 0,
                        rx.foreach(FoodState.caja_add_productos_filtrados, _caja_add_producto_row),
                        rx.center(
                            rx.text("Sin resultados.", font_size="13px", color=TEXT_MUTED),
                            padding_y="24px", width="100%",
                        ),
                    ),
                    width="100%", max_height="46vh", overflow_y="auto",
                    border=f"1px solid {DARK_700}", border_radius="10px",
                    background=DARK_800,
                ),
                rx.button(
                    "Listo", on_click=FoodState.set_caja_add_modal(False),
                    background=ACCENT, color=TEXT_WHITE, border_radius="10px",
                    font_size="14px", font_weight="800", cursor="pointer",
                    width="100%", _hover={"background": ACCENT_HOVER},
                ),
                spacing="3", width="100%",
            ),
            max_width="460px", width="92vw", max_height="90vh", overflow_y="auto",
            background=PAGE_BACKGROUND, border=f"1px solid {DARK_800}",
        ),
        open=FoodState.caja_add_modal,
        on_open_change=FoodState.set_caja_add_modal,
    )


def _caja_quitar_modal() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.hstack(
                    rx.icon(tag="triangle_alert", size=18, color=DANGER_TEXT),
                    rx.dialog.title("Quitar — " + FoodState.caja_quitar_item_nombre,
                            font_size="17px", font_weight="800", color=TEXT_PRIMARY, margin="0"),
                    spacing="2", align="center",
                ),
                rx.text(
                    "Este ítem ya fue enviado a cocina. Al quitarlo se repone el stock y "
                    "la operación queda registrada en auditoría.",
                    font_size="13px", color=TEXT_MUTED,
                ),
                rx.input(
                    placeholder="Motivo (obligatorio)",
                    value=FoodState.caja_quitar_motivo,
                    on_change=FoodState.set_caja_quitar_motivo,
                    width="100%", background=SURFACE_BASE, border=f"1px solid {DARK_700}",
                    color=TEXT_PRIMARY, border_radius="8px", font_size="13px",
                    _focus={"border_color": "#DC2626"},
                ),
                rx.cond(
                    FoodState.caja_quitar_error != "",
                    rx.text(FoodState.caja_quitar_error, font_size="12px",
                            color="#EF4444", font_weight="600"),
                    rx.fragment(),
                ),
                rx.hstack(
                    rx.button(
                        "Volver", on_click=FoodState.cancelar_caja_quitar,
                        background=DARK_800, color=TEXT_MUTED, border=f"1px solid {DARK_700}",
                        border_radius="10px", font_size="14px", font_weight="600",
                        cursor="pointer", _hover={"background": "var(--twk-d700)", "color": "var(--twk-text-primary)"}, flex="1",
                    ),
                    rx.button(
                        "Quitar ítem", on_click=FoodState.caja_confirmar_quitar,
                        background="#DC2626", color=TEXT_WHITE, border_radius="10px",
                        font_size="14px", font_weight="800", cursor="pointer",
                        _hover={"background": "#B91C1C"}, flex="2",
                    ),
                    spacing="3", width="100%",
                ),
                spacing="3", width="100%",
            ),
            max_width="440px", width="92vw", max_height="90vh", overflow_y="auto",
            background=PAGE_BACKGROUND, border=f"1px solid {DARK_800}",
        ),
        open=FoodState.caja_quitar_modal,
        on_open_change=FoodState.set_caja_quitar_modal,
    )


def _caja_content() -> rx.Component:
    return rx.vstack(
        cumpleanos_banner(),
        rx.hstack(
            rx.vstack(
                rx.text("Caja", font_size="22px", font_weight="800", color=TEXT_PRIMARY),
                rx.text(
                    FoodState.cantidad_mesas_abiertas.to_string() + " mesa(s) abiertas",
                    font_size="13px", color=TEXT_MUTED,
                ),
                spacing="0",
            ),
            rx.spacer(),
            ayuda_trigger(),
            rx.hstack(
                rx.text(
                    FoodState.ultima_actualizacion,
                    font_size="11px", color=TEXT_MUTED,
                ),
                rx.icon(
                    tag="refresh_cw", size=14, color=ACCENT,
                    cursor="pointer",
                    on_click=FoodState.cargar_mesas,
                    _hover={"opacity": "0.7"},
                ),
                spacing="1", align="center",
            ),
            width="100%", align="center", flex_wrap="wrap", gap="8px",
        ),
        _turno_banner(),
        # align stretch: la card de mesas se estira a la misma altura que el panel
        # central (cuyo alto lo fija el terminal), quedando su fondo al nivel de
        # "DIVIDIR / PAGO MIXTO".
        rx.flex(
            _mesas_sidebar(),
            _panel_central(),
            direction=rx.breakpoints(initial="column", lg="row"),
            gap="16px", width="100%", align="stretch",
        ),
        _mov_modal(),
        _cierre_modal(),
        _historial_modal(),
        _cierre_preview_modal(),
        _ultimos_cobros_modal(),
        preview_ticket_modal(),
        _reversion_modal(),
        _correccion_modal(),
        _caja_add_modal(),
        _caja_quitar_modal(),
        anulacion_modal(),
        _caja_ayuda(),
        spacing="4", width="100%",
    )


@rx.page(
    route="/caja",
    on_load=[FoodState.on_load_caja, FoodState.start_caja_polling,
             FoodState.cargar_clientes, FoodState.cargar_promociones,
             ReportesState.cargar_dashboard],
    title="TUWAYKIFOOD | Caja",
)
def caja_page() -> rx.Component:
    return app_shell(
        rx.cond(FoodState.pagina_cargada, _caja_content(), loading_placeholder()),
        page_key="caja",
    )
