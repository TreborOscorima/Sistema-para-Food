"""Pagina de caja — turno con arqueo, cobro de mesas con método de pago y propina."""

from __future__ import annotations

import reflex as rx

from app.components.shared import (
    anulacion_modal, app_shell, cumpleanos_banner, loading_placeholder,
    ACCENT, ACCENT_HOVER,
    DANGER_SOLID,
    DARK_700, DARK_800,
    PAGE_BACKGROUND,
    SUCCESS_SOLID,
    TEXT_MUTED, TEXT_PRIMARY, TEXT_WHITE,
    WARNING_SOLID,
)
from app.states.caja_turno_mixin import (
    DenominacionRow,
    MovimientoCajaView,
    ResumenCierreRow,
    TurnoHistorialView,
)
from app.components.ayuda import ayuda_modal, ayuda_trigger, empty_state
from app.states.food_state import FoodState, MesaView, CajaItemView, MostradorPendienteView, PagoStagedView, UltimoCobroView
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

_METODOS = [
    ("efectivo", "Efectivo", "💵"),
    ("tarjeta", "Tarjeta", "💳"),
    ("qr", "QR / Yape", "📱"),
    ("fiado", "Fiado / CC", "📒"),
]


def _metodo_btn(value: str, label: str, icon: str) -> rx.Component:
    activo = FoodState.caja_cobro_metodo == value
    return rx.box(
        rx.text(icon, font_size="18px", line_height="1"),
        rx.text(label, font_size="12px", font_weight="700",
                color=rx.cond(activo, "#FFFFFF", "#94A3B8")),
        on_click=FoodState.set_caja_cobro_metodo(value),
        background=rx.cond(activo, ACCENT, DARK_800),
        border=rx.cond(activo, "2px solid #EA580C", "2px solid #334155"),
        border_radius="10px",
        padding="12px 4px",
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
                        color=rx.cond(asignado & FoodState.caja_split_por_items, "#94A3B8", "#F1F5F9")),
                rx.cond(
                    item.notas != "",
                    rx.text(item.notas, font_size="11px", color=TEXT_MUTED),
                    rx.text(item.precio_unitario_texto + " c/u", font_size="11px", color=TEXT_MUTED),
                ),
                spacing="0", align="start",
            ),
            rx.text("×" + item.cantidad.to_string(), font_size="13px", font_weight="600",
                    color="#CBD5E1", text_align="center"),
            rx.text(item.subtotal_texto, font_size="13px", font_weight="700",
                    color=rx.cond(asignado & FoodState.caja_split_por_items, "#94A3B8", "#F1F5F9"),
                    text_align="right"),
            columns=rx.cond(
                FoodState.caja_split_por_items,
                "32px 1fr 50px 80px",
                "1fr 50px 80px",
            ),
            gap="8px", align_items="center", width="100%",
        ),
        padding="12px 16px",
        border_bottom=f"1px solid {DARK_700}",
        background=rx.cond(
            item.seleccionado & FoodState.caja_split_por_items,
            "rgba(234,88,12,0.08)",
            rx.cond(asignado & FoodState.caja_split_por_items, "#0F172A", "transparent"),
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
            rx.text(pago.metodo_label, font_size="12px", font_weight="700", color="#CBD5E1"),
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
                rx.switch(
                    checked=FoodState.caja_split_por_items,
                    on_change=FoodState.set_caja_split_por_items,
                    color_scheme="blue", size="1",
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
                    ["efectivo", "tarjeta", "qr", "fiado"],
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
                    background="transparent", color="#60A5FA",
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
                        "Cuenta cubierta ✓", background="rgba(34,197,94,0.12)", color=SUCCESS_SOLID,
                        border_radius="8px", font_size="12px", font_weight="700",
                        padding_x="10px", padding_y="4px",
                    ),
                    rx.badge(
                        "Restante: " + FoodState.caja_pagos_restante_texto,
                        background="rgba(245,158,11,0.12)", color=WARNING_SOLID,
                        border_radius="8px", font_size="12px", font_weight="700",
                        padding_x="10px", padding_y="4px",
                    ),
                ),
                rx.spacer(),
                rx.cond(
                    FoodState.caja_pagos_vuelto_texto != "",
                    rx.text("Vuelto: " + FoodState.caja_pagos_vuelto_texto,
                            font_size="13px", font_weight="700", color=SUCCESS_SOLID),
                    rx.fragment(),
                ),
                width="100%", align="center",
            ),
            spacing="3", width="100%",
        ),
        background=DARK_800, border=f"1px solid {DARK_700}",
        border_radius="14px", padding="18px", width="100%",
    )


def _cobro_panel() -> rx.Component:
    return rx.vstack(
        # Header
        rx.hstack(
            rx.vstack(
                rx.text(FoodState.caja_cobro_mesa_nombre, font_size="18px", font_weight="800", color=TEXT_PRIMARY),
                rx.text("Consumo pendiente de cobro", font_size="12px", color=TEXT_MUTED),
                spacing="0",
            ),
            rx.spacer(),
            rx.badge(
                "Cuenta pedida", background="rgba(239,68,68,0.12)", color=DANGER_SOLID,
                border_radius="20px", font_size="11px", font_weight="700",
                padding_x="12px", padding_y="5px",
            ),
            width="100%", align="center",
        ),
        # 2 columnas: recibo (items) | terminal de pago (todo lo operativo)
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
                        padding="9px 16px", border_bottom="0.5px solid #F1F5F9", width="100%",
                    ),
                    rx.cond(
                        FoodState.caja_cobro_items.length() > 0,
                        rx.box(
                            rx.foreach(FoodState.caja_cobro_items, _caja_item_row),
                            width="100%", overflow_y="auto", flex="1",
                        ),
                        rx.center(
                            rx.text("Sin items registrados.", font_size="13px", color=TEXT_MUTED),
                            padding_y="20px", width="100%",
                        ),
                    ),
                    rx.cond(
                        FoodState.caja_promo_aplicada_nombre != "",
                        rx.hstack(
                            rx.icon(tag="badge_percent", size=12, color="#16A34A"),
                            rx.text(
                                "Promo: " + FoodState.caja_promo_aplicada_nombre
                                + " · " + FoodState.caja_promo_aplicada_texto + " descontado",
                                font_size="11px", color=SUCCESS_SOLID, font_weight="600",
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
                        rx.text("Subtotal items", font_size="13px", font_weight="600", color="#CBD5E1"),
                        rx.spacer(),
                        rx.text(FoodState.caja_cobro_total_base_texto, font_size="20px",
                                font_weight="800", color="#CBD5E1", letter_spacing="-0.5px"),
                        align="center", padding="10px 16px", width="100%",
                        border_top=f"1px solid {DARK_700}",
                    ),
                    spacing="0",
                    border=f"1px solid {DARK_700}", border_radius="12px",
                    background=DARK_800, overflow="hidden",
                    flex="1", min_width="0", width="100%",
                ),
                flex="1", min_width="0", width="100%",
            ),
            # ── Columna derecha: terminal completo de cobro ─────────────
            rx.vstack(
                # Display total final
                rx.vstack(
                    rx.text("TOTAL A COBRAR", font_size="9px", color=TEXT_MUTED,
                            text_transform="uppercase", letter_spacing="0.1em"),
                    rx.text(FoodState.caja_cobro_total_final_texto, font_size="24px",
                            font_weight="800", color="#FB923C", letter_spacing="-0.5px"),
                    spacing="0", align="center",
                    background=PAGE_BACKGROUND, border_radius="10px",
                    padding="10px 18px", width="100%",
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
                                border="1px solid #CBD5E1",
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
                                            color=rx.cond(FoodState.caja_cobro_propina_pct == p, "#FFFFFF", "#94A3B8")),
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
                                        font_size="11px", color=SUCCESS_SOLID, font_weight="600", no_of_lines=1),
                                rx.text("-" + FoodState.caja_cupon_descuento_aplicado,
                                        font_size="11px", color=SUCCESS_SOLID),
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
                            rx.text(FoodState.caja_cupon_error, font_size="10px", color=DANGER_SOLID),
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
                            *[_metodo_btn(v, l, i) for v, l, i in _METODOS],
                            columns="4", gap="6px", width="100%",
                        ),
                        spacing="2", width="100%",
                    ),
                ),
                # Selector de cliente para fiado
                rx.cond(
                    FoodState.caja_cobro_es_fiado | FoodState.caja_pagos_tiene_fiado,
                    rx.vstack(
                        rx.hstack(
                            rx.text("Cliente", font_size="11px", font_weight="700", color="#CBD5E1"),
                            rx.text("*", font_size="11px", font_weight="700", color=DANGER_SOLID),
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
                            border="1.5px solid #CBD5E1", border_radius="8px",
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
                        rx.icon(tag="circle_alert", size=13, color="#F87171"),
                        rx.text(FoodState.caja_cobro_error, font_size="11px",
                                color="#F87171", font_weight="600"),
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
                            background="transparent", color="#60A5FA",
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
                            background="transparent", color=DANGER_SOLID,
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
                        border="0.5px solid #334155", border_radius="8px",
                        font_size="12px", font_weight="600", cursor="pointer",
                        _hover={"background": DARK_700}, flex="1", padding_y="7px",
                    ),
                    spacing="2", width="100%",
                ),
                # Toggle dividir
                rx.hstack(
                    rx.switch(
                        checked=FoodState.caja_cobro_dividido,
                        on_change=FoodState.set_caja_cobro_dividido,
                        color_scheme="orange",
                    ),
                    rx.text("Dividir / pago mixto", font_size="11px", color=TEXT_MUTED),
                    spacing="2", align="center",
                ),
                spacing="3",
                width=rx.breakpoints(initial="100%", lg="340px"),
                min_width=rx.breakpoints(initial="100%", lg="340px"),
                flex_shrink="0",
            ),
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
                                color=rx.cond(seleccionado, ACCENT, "#CBD5E1")),
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
                            color=rx.cond(seleccionado, ACCENT, "#CBD5E1")),
                    rx.cond(
                        pedido.en_cocina,
                        rx.badge("En cocina", background="rgba(245,158,11,0.12)", color=WARNING_SOLID,
                                 border_radius="20px", font_size="10px", font_weight="700",
                                 padding_x="8px", padding_y="2px"),
                        rx.badge("Listo", background="rgba(34,197,94,0.12)", color=SUCCESS_SOLID,
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
        rx.hstack(
            rx.spacer(),
            rx.button(
                "✏️ Editar",
                on_click=FoodState.editar_pedido_mostrador(pedido.pedido_id),
                size="1",
                variant="outline",
                color=ACCENT,
                border="1px solid #EA580C",
                border_radius="6px",
                font_size="11px",
                font_weight="600",
                padding_x="8px",
                padding_y="2px",
                cursor="pointer",
                _hover={"background": "rgba(234,88,12,0.08)"},
            ),
            padding_x="16px",
            padding_bottom="8px",
        ),
        background=rx.cond(seleccionado, "rgba(234,88,12,0.08)", "#1E293B"),
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
                    color=rx.cond(seleccionada, ACCENT, "#CBD5E1"),
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
                color=rx.cond(seleccionada, "#F1F5F9", "#CBD5E1"),
            ),
            width="100%", align="center",
        ),
        on_click=FoodState.abrir_cobro_mesa(mesa.id),
        padding="14px 16px",
        background=rx.cond(seleccionada, "rgba(234,88,12,0.08)", "#1E293B"),
        border_left=rx.cond(seleccionada, "3px solid #EA580C", "3px solid transparent"),
        border_bottom=f"1px solid {DARK_700}",
        cursor="pointer",
        width="100%",
        _hover={"background": rx.cond(seleccionada, "rgba(234,88,12,0.08)", "#334155")},
    )


def _mesas_sidebar() -> rx.Component:
    mesas_cobrables = FoodState.mesas_por_cobrar
    return rx.box(
        # Mesas por cobrar
        rx.box(
            rx.text("Mesas por cobrar", font_size="11px", font_weight="700", color=TEXT_MUTED,
                    text_transform="uppercase", letter_spacing="0.05em"),
            padding="16px", border_bottom="1px solid #F1F5F9",
        ),
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
        # Para llevar — pedidos de Mostrador pendientes de cobro
        rx.box(
            rx.hstack(
                rx.icon(tag="package", size=12, color=ACCENT),
                rx.text("Para llevar", font_size="11px", font_weight="700", color=ACCENT,
                        text_transform="uppercase", letter_spacing="0.05em"),
                spacing="1", align="center",
            ),
            padding="12px 16px", border_top="1px solid #F1F5F9", border_bottom="1px solid #F1F5F9",
        ),
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
        background=DARK_800,
        border=f"1px solid {DARK_700}",
        border_radius="14px",
        width=rx.breakpoints(initial="100%", lg="260px"),
        min_width=rx.breakpoints(initial="100%", lg="260px"),
        max_height=rx.breakpoints(initial="none", lg="calc(100vh - 180px)"),
        overflow_y="auto",
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
            empty_state(
                icono="credit_card",
                titulo="Selecciona una mesa para cobrar",
                texto="Elige una mesa de la lista de la izquierda para ver su consumo y cobrar. "
                      "Los pedidos para llevar aparecen más abajo.",
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
                    background=DARK_800, border=f"1px solid {DARK_700}",
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
            rx.text(FoodState.turno_error, font_size="12px", color="#F87171",
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
            rx.spacer(),
            rx.hstack(
                rx.button(
                    rx.hstack(rx.icon(tag="arrow_down_up", size=14), rx.text("Ingresos / Gastos"),
                              spacing="1", align="center"),
                    on_click=FoodState.abrir_mov_modal,
                    background=DARK_800, color="#CBD5E1",
                    border=f"1px solid {DARK_700}", border_radius="8px",
                    font_size="13px", font_weight="600", cursor="pointer",
                    _hover={"border_color": ACCENT},
                ),
                rx.button(
                    rx.hstack(rx.icon(tag="printer", size=14), rx.text("Últimos cobros"),
                              spacing="1", align="center"),
                    on_click=FoodState.toggle_ultimos_cobros,
                    background=DARK_800, color="#CBD5E1",
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
                    background=PAGE_BACKGROUND, color=TEXT_WHITE,
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
            color=rx.cond(es_ingreso, "#22C55E", "#F87171"),
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
                            font_size="12px", font_weight="700", color=DANGER_SOLID),
                    spacing="4",
                ),
                # Formulario
                rx.box(
                    rx.vstack(
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
                                background=DARK_800, border=f"1px solid {DARK_700}",
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
                                background=DARK_800, border=f"1px solid {DARK_700}",
                                border_radius="8px", font_size="13px", color=TEXT_PRIMARY,
                                _focus={"border_color": ACCENT},
                            ),
                            rx.button(
                                "Registrar",
                                on_click=FoodState.guardar_movimiento_caja,
                                is_loading=FoodState.caja_registrando_mov,
                                background=ACCENT, color=TEXT_WHITE,
                                border_radius="8px", font_size="13px", font_weight="700",
                                cursor="pointer", _hover={"background": ACCENT_HOVER},
                            ),
                            spacing="2", width="100%",
                        ),
                        rx.cond(
                            FoodState.turno_mov_error != "",
                            rx.text(FoodState.turno_mov_error, font_size="12px",
                                    color="#F87171", font_weight="600"),
                            rx.fragment(),
                        ),
                        spacing="2", width="100%",
                    ),
                    background=DARK_800, border=f"1px solid {DARK_700}",
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
        rx.text(row.etiqueta, font_size="13px", color="#CBD5E1", width="140px"),
        rx.input(
            placeholder="0",
            value=row.cantidad,
            on_change=lambda v: FoodState.set_conteo_denominacion(row.key, v),
            type="number", min="0", step="1",
            width="70px", text_align="center",
            background=DARK_800, border=f"1px solid {DARK_700}",
            border_radius="7px", font_size="13px", color=TEXT_PRIMARY,
            _focus={"border_color": ACCENT},
        ),
        rx.spacer(),
        rx.text(row.subtotal_texto, font_size="13px", font_weight="700", color=TEXT_PRIMARY),
        width="100%", align="center", gap="8px",
    )


def _resumen_cierre_row(row: ResumenCierreRow) -> rx.Component:
    return rx.hstack(
        rx.text(row.etiqueta, font_size="13px", color=TEXT_MUTED),
        rx.spacer(),
        rx.text(row.monto_texto, font_size="13px", font_weight="700", color="#CBD5E1"),
        width="100%", align="center",
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
                            rx.box(border_top="2px solid #334155", width="100%", padding_top="4px"),
                            rx.hstack(
                                rx.text("Efectivo esperado en caja", font_size="14px",
                                        font_weight="800", color=TEXT_PRIMARY),
                                rx.spacer(),
                                rx.text(FoodState.turno_cierre_esperado_texto, font_size="16px",
                                        font_weight="900", color=ACCENT),
                                width="100%", align="center",
                            ),
                            spacing="2", width="100%",
                        ),
                        background=DARK_800, border=f"1px solid {DARK_700}",
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
                    background=DARK_800, border=f"1px solid {DARK_700}",
                    border_radius="10px", padding="12px 16px", width="100%",
                ),
                rx.input(
                    placeholder="Notas del cierre (opcional)",
                    value=FoodState.turno_cierre_notas,
                    on_change=FoodState.set_turno_cierre_notas,
                    width="100%",
                    background=DARK_800, border=f"1px solid {DARK_700}",
                    border_radius="8px", font_size="13px", color=TEXT_PRIMARY,
                    _focus={"border_color": ACCENT},
                ),
                rx.cond(
                    FoodState.turno_cierre_error != "",
                    rx.text(FoodState.turno_cierre_error, font_size="12px",
                            color="#F87171", font_weight="600"),
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
        rx.icon_button(
            rx.icon(tag="printer", size=14),
            variant="ghost", size="1", color=TEXT_MUTED, cursor="pointer",
            title="Reimprimir cierre",
            on_click=FoodState.reimprimir_cierre_turno(t.id),
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
        rx.text(cobro.total_texto, font_size="13px", font_weight="700", color=SUCCESS_SOLID,
                min_width="80px", text_align="right"),
        rx.tooltip(
            rx.icon(tag="printer", size=16, color=ACCENT, cursor="pointer",
                    on_click=FoodState.reimprimir_comprobante(cobro.pedido_id),
                    _hover={"opacity": "0.7"}),
            content="Reimprimir",
        ),
        rx.tooltip(
            rx.icon(tag="trash_2", size=16, color="#EF4444", cursor="pointer",
                    on_click=FoodState.abrir_reversion_cobro(cobro.pedido_id),
                    _hover={"opacity": "0.7"}),
            content="Anular cobro",
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
                            _hover={"color": "#F1F5F9"}),
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


def _reversion_modal() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.hstack(
                    rx.icon(tag="triangle_alert", size=18, color=DANGER_SOLID),
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
                    background=DARK_800, border=f"1px solid {DARK_700}",
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
                        _hover={"background": "#334155", "color": "#F1F5F9"}, flex="1",
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
        rx.flex(
            _mesas_sidebar(),
            _panel_central(),
            direction=rx.breakpoints(initial="column", lg="row"),
            gap="16px", width="100%", align="start",
        ),
        _mov_modal(),
        _cierre_modal(),
        _historial_modal(),
        _ultimos_cobros_modal(),
        _reversion_modal(),
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
