"""Pagina de caja — cobro de mesas con método de pago y propina."""

from __future__ import annotations

import reflex as rx

from app.components.shared import app_shell
from app.states.food_state import FoodState, MesaView

_METODOS = [
    ("efectivo", "Efectivo", "banknote"),
    ("tarjeta", "Tarjeta", "credit_card"),
    ("qr", "QR / Yape", "qr_code"),
    ("fiado", "Fiado / CC", "clipboard_list"),
]


def _metodo_btn(value: str, label: str, icon: str) -> rx.Component:
    activo = FoodState.caja_cobro_metodo == value
    return rx.button(
        rx.vstack(
            rx.icon(tag=icon, size=18, color=rx.cond(activo, "#FFFFFF", "#64748B")),
            rx.text(label, font_size="12px", font_weight="700",
                    color=rx.cond(activo, "#FFFFFF", "#64748B")),
            spacing="1",
            align="center",
        ),
        on_click=FoodState.set_caja_cobro_metodo(value),
        background=rx.cond(activo, "#EA580C", "#F8FAFC"),
        border=rx.cond(activo, "2px solid #EA580C", "2px solid #E2E8F0"),
        border_radius="10px",
        padding="10px 0",
        cursor="pointer",
        flex=rx.breakpoints(initial="1 0 calc(50% - 4px)", sm="1"),
        min_width="0",
        transition="all 0.15s ease",
        _hover={"border": "2px solid #EA580C", "background": rx.cond(activo, "#C2410C", "#FFF7ED")},
    )


def _cobro_panel() -> rx.Component:
    return rx.vstack(
        # Header
        rx.hstack(
            rx.button(
                rx.icon(tag="arrow_left", size=16),
                on_click=FoodState.cancelar_cobro,
                background="#F1F5F9",
                color="#64748B",
                border="1px solid #E2E8F0",
                border_radius="8px",
                cursor="pointer",
                padding="6px 10px",
                _hover={"opacity": "0.85"},
            ),
            rx.vstack(
                rx.text("Cobrar mesa", font_size="22px", font_weight="800", color="#0F172A"),
                rx.text(FoodState.caja_cobro_mesa_nombre, font_size="13px", color="#64748B"),
                spacing="0",
            ),
            spacing="3",
            align="center",
            width="100%",
        ),
        # Banner de error de cobro
        rx.cond(
            FoodState.caja_cobro_error != "",
            rx.hstack(
                rx.icon(tag="circle_alert", size=14, color="#B91C1C"),
                rx.text(FoodState.caja_cobro_error, font_size="12px", color="#B91C1C", font_weight="600"),
                spacing="2",
                align="center",
                background="#FEF2F2",
                border="1px solid #FECACA",
                border_radius="8px",
                padding="10px 12px",
                width="100%",
            ),
            rx.fragment(),
        ),
        # Total base
        rx.box(
            rx.hstack(
                rx.text("Consumo", font_size="14px", color="#334155"),
                rx.spacer(),
                rx.text(FoodState.caja_cobro_total_base_texto, font_size="20px",
                        font_weight="800", color="#0F172A"),
                width="100%",
                align="center",
            ),
            background="#F8FAFC",
            border="1px solid #E2E8F0",
            border_radius="10px",
            padding="14px 16px",
            width="100%",
        ),
        # Método de pago
        rx.vstack(
            rx.text("Método de pago", font_size="13px", font_weight="700", color="#334155"),
            rx.flex(
                *[_metodo_btn(v, l, i) for v, l, i in _METODOS],
                flex_wrap="wrap",
                gap="8px",
                width="100%",
            ),
            spacing="2",
            width="100%",
        ),
        # Descuento + Propina (fila par)
        rx.hstack(
            rx.vstack(
                rx.text("Descuento", font_size="13px", font_weight="700", color="#334155"),
                rx.hstack(
                    rx.text("S/", font_size="14px", font_weight="700", color="#64748B"),
                    rx.input(
                        placeholder="0.00",
                        value=FoodState.caja_cobro_descuento,
                        on_change=FoodState.set_caja_cobro_descuento,
                        type="number",
                        min="0",
                        step="0.50",
                        background="#FFFFFF",
                        border="1px solid #E2E8F0",
                        color="#0F172A",
                        border_radius="8px",
                        padding_x="12px",
                        padding_y="8px",
                        font_size="14px",
                        flex="1",
                    ),
                    spacing="2",
                    align="center",
                    width="100%",
                ),
                spacing="2",
                flex="1",
            ),
            rx.vstack(
                rx.text("Propina (opcional)", font_size="13px", font_weight="700", color="#334155"),
                rx.hstack(
                    rx.text("S/", font_size="14px", font_weight="700", color="#64748B"),
                    rx.input(
                        placeholder="0.00",
                        value=FoodState.caja_cobro_propina,
                        on_change=FoodState.set_caja_cobro_propina,
                        type="number",
                        min="0",
                        step="0.50",
                        background="#FFFFFF",
                        border="1px solid #E2E8F0",
                        color="#0F172A",
                        border_radius="8px",
                        padding_x="12px",
                        padding_y="8px",
                        font_size="14px",
                        flex="1",
                    ),
                    spacing="2",
                    align="center",
                    width="100%",
                ),
                spacing="2",
                flex="1",
            ),
            spacing="3",
            width="100%",
            align="start",
        ),
        # Selector de cliente (solo fiado)
        rx.cond(
            FoodState.caja_cobro_es_fiado,
            rx.vstack(
                rx.hstack(
                    rx.text("Cliente", font_size="13px", font_weight="700", color="#334155"),
                    rx.text("*", font_size="13px", font_weight="700", color="#B91C1C"),
                    rx.text("(requerido para fiado)", font_size="12px", color="#94A3B8"),
                    spacing="1",
                    align="center",
                ),
                rx.select(
                    FoodState.clientes_activos_nombres,
                    value=FoodState.caja_cobro_cliente_nombre,
                    on_change=FoodState.set_caja_cobro_cliente_nombre,
                    placeholder="— Seleccionar cliente —",
                    background="#FFFFFF",
                    border="2px solid #FED7AA",
                    border_radius="8px",
                    font_size="14px",
                    width="100%",
                ),
                spacing="2",
                width="100%",
            ),
            rx.fragment(),
        ),
        # Banner de promo activa
        rx.cond(
            FoodState.hay_promo_activa,
            rx.box(
                rx.hstack(
                    rx.icon(tag="zap", size=13, color="#B45309"),
                    rx.vstack(
                        rx.text(
                            "Promo activa: " + FoodState.promo_activa_nombre,
                            font_size="12px", font_weight="700", color="#0F172A",
                        ),
                        rx.text(FoodState.promo_activa_descuento_texto,
                                font_size="11px", color="#78350F"),
                        spacing="0", align="start",
                    ),
                    rx.spacer(),
                    rx.button(
                        "Aplicar",
                        on_click=FoodState.aplicar_promo_al_cobro,
                        background="#F59E0B", color="#FFFFFF",
                        border_radius="6px", font_size="12px", font_weight="700",
                        padding_x="12px", padding_y="6px", cursor="pointer",
                        _hover={"background": "#D97706"},
                    ),
                    width="100%", align="center", gap="8px",
                ),
                background="#FFFBEB", border="1px solid #FDE68A",
                border_radius="8px", padding="10px 12px", width="100%",
            ),
            rx.fragment(),
        ),
        # Monto recibido (solo efectivo)
        rx.cond(
            FoodState.caja_cobro_es_efectivo,
            rx.vstack(
                rx.text("Efectivo recibido", font_size="13px", font_weight="700", color="#334155"),
                rx.hstack(
                    rx.text("S/", font_size="14px", font_weight="700", color="#64748B"),
                    rx.input(
                        placeholder="0.00",
                        value=FoodState.caja_cobro_efectivo_recibido,
                        on_change=FoodState.set_caja_cobro_efectivo_recibido,
                        type="number",
                        min="0",
                        step="0.50",
                        background="#FFFFFF",
                        border="1px solid #E2E8F0",
                        color="#0F172A",
                        border_radius="8px",
                        padding_x="12px",
                        padding_y="8px",
                        font_size="14px",
                        flex="1",
                    ),
                    spacing="2",
                    align="center",
                    width="100%",
                ),
                rx.cond(
                    FoodState.caja_cobro_efectivo_recibido != "",
                    rx.hstack(
                        rx.text("Vuelto:", font_size="13px", color="#64748B"),
                        rx.spacer(),
                        rx.text(FoodState.caja_cobro_vuelto_texto,
                                font_size="16px", font_weight="700", color="#15803D"),
                        width="100%",
                        align="center",
                        padding="8px 12px",
                        background="#F0FDF4",
                        border="1px solid #BBF7D0",
                        border_radius="8px",
                    ),
                    rx.fragment(),
                ),
                spacing="2",
                width="100%",
            ),
            rx.fragment(),
        ),
        # Total final
        rx.box(
            rx.hstack(
                rx.text("TOTAL A COBRAR", font_size="13px", font_weight="700", color="#EA580C"),
                rx.spacer(),
                rx.text(FoodState.caja_cobro_total_final_texto,
                        font_size="26px", font_weight="900", color="#EA580C"),
                width="100%",
                align="center",
            ),
            background="#FFF7ED",
            border="2px solid #FED7AA",
            border_radius="12px",
            padding="16px",
            width="100%",
        ),
        # Botones
        rx.hstack(
            rx.button(
                "Cancelar",
                on_click=FoodState.cancelar_cobro,
                background="#F1F5F9",
                color="#64748B",
                border="1px solid #E2E8F0",
                border_radius="10px",
                font_size="14px",
                font_weight="600",
                padding_y="12px",
                cursor="pointer",
                _hover={"opacity": "0.85"},
                flex="1",
            ),
            rx.button(
                rx.hstack(
                    rx.icon(tag="circle_check", size=16, color="#FFFFFF"),
                    rx.text("Confirmar Cobro", font_size="14px", font_weight="700", color="#FFFFFF"),
                    spacing="2",
                    align="center",
                ),
                on_click=FoodState.confirmar_cobro,
                background="#15803D",
                color="#FFFFFF",
                border_radius="10px",
                font_size="14px",
                font_weight="700",
                padding_y="12px",
                cursor="pointer",
                _hover={"background": "#166534"},
                flex="2",
            ),
            spacing="2",
            width="100%",
        ),
        spacing="4",
        width="100%",
        max_width="520px",
    )


def _mesa_cobro_card(mesa: MesaView) -> rx.Component:
    cobrable = (mesa.estado != "libre") & (mesa.total_abierto > 0)
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.vstack(
                    rx.text(mesa.nombre, font_size="15px", font_weight="700", color="#0F172A"),
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
                    color="#EA580C",
                ),
                width="100%",
                align="center",
            ),
            rx.cond(
                mesa.tiene_items_listos,
                rx.text(
                    mesa.items_listos_count.to_string() + " items listos para entregar",
                    font_size="11px",
                    color="#B45309",
                    font_weight="600",
                ),
                rx.fragment(),
            ),
            rx.button(
                "Cobrar Mesa",
                on_click=FoodState.abrir_cobro_mesa(mesa.id),
                width="100%",
                background=rx.cond(cobrable, "#15803D", "#F1F5F9"),
                color=rx.cond(cobrable, "#FFFFFF", "#94A3B8"),
                border=rx.cond(
                    cobrable,
                    "1px solid #15803D",
                    "1px solid #E2E8F0",
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
        opacity=rx.cond(cobrable, "1", "0.6"),
        box_shadow="0 1px 3px rgba(0,0,0,0.06)",
    )


def _caja_content() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.vstack(
                rx.text("Caja", font_size="22px", font_weight="800", color="#0F172A"),
                rx.text(
                    FoodState.cantidad_mesas_abiertas.to_string() + " mesa(s) abiertas",
                    font_size="13px",
                    color="#64748B",
                ),
                spacing="0",
            ),
            rx.spacer(),
            rx.cond(
                ~FoodState.caja_cobro_activo,
                rx.button(
                    "Actualizar",
                    on_click=FoodState.cargar_mesas,
                    background="#FFF7ED",
                    color="#EA580C",
                    border="1px solid #FED7AA",
                    border_radius="8px",
                    font_size="13px",
                    cursor="pointer",
                    _hover={"opacity": "0.85"},
                ),
                rx.fragment(),
            ),
            width="100%",
            align="center",
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
            FoodState.caja_cobro_activo,
            _cobro_panel(),
            rx.cond(
                FoodState.mesas.length() == 0,
                rx.center(
                    rx.text("No hay mesas configuradas.", font_size="14px", color="#94A3B8"),
                    padding_y="60px",
                ),
                rx.grid(
                    rx.foreach(FoodState.mesas, _mesa_cobro_card),
                    columns=rx.breakpoints(initial="1", sm="2", md="3"),
                    gap="16px",
                    width="100%",
                ),
            ),
        ),
        spacing="5",
        width="100%",
    )


@rx.page(
    route="/caja",
    on_load=[FoodState.on_load_caja, FoodState.start_caja_polling,
             FoodState.cargar_clientes, FoodState.cargar_promociones],
    title="TUWAYKIFOOD | Caja",
)
def caja_page() -> rx.Component:
    return app_shell(_caja_content(), page_key="caja")
