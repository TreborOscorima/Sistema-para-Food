"""Paginas del dueño del local — login email/pass y dashboard de configuracion."""

from __future__ import annotations

import reflex as rx

from app.states.food_state import AdminLocalState, FoodState
from app.components.shared import _CSS_SCRIPT
from app.pages.configuracion import (
    _admin_cuenta_section,
    _field_row,
    _mesas_section,
    _printer_section,
    _qr_section,
    _section_header,
)


def _dono_shell(content: rx.Component) -> rx.Component:
    return rx.box(
        rx.script(_CSS_SCRIPT),
        rx.vstack(
            # Top bar
            rx.hstack(
                rx.hstack(
                    rx.box(
                        rx.icon(tag="utensils", size=16, color="#FFFFFF"),
                        width="34px",
                        height="34px",
                        border_radius="8px",
                        background="linear-gradient(135deg, #EA580C 0%, #C2410C 100%)",
                        display="flex",
                        align_items="center",
                        justify_content="center",
                    ),
                    rx.text("TUWAYKIFOOD", font_size="15px", font_weight="800", color="#0F172A"),
                    rx.badge(
                        "Panel del Dueño",
                        background="#FFF7ED",
                        color="#EA580C",
                        border="1px solid #FED7AA",
                        border_radius="5px",
                        font_size="10px",
                        font_weight="700",
                        padding_x="6px",
                    ),
                    spacing="2",
                    align="center",
                ),
                rx.spacer(),
                rx.button(
                    rx.hstack(
                        rx.icon(tag="log_out", size=13, color="#64748B"),
                        rx.text("Salir", font_size="12px", color="#64748B"),
                        spacing="1",
                        align="center",
                    ),
                    on_click=AdminLocalState.logout_admin_local,
                    background="#F1F5F9",
                    border="1px solid #E2E8F0",
                    border_radius="6px",
                    padding_x="10px",
                    padding_y="6px",
                    cursor="pointer",
                    _hover={"opacity": "0.85"},
                ),
                width="100%",
                align="center",
                padding="12px 20px",
                background="#FFFFFF",
                border_bottom="1px solid #E2E8F0",
                position="sticky",
                top="0",
                z_index="10",
            ),
            # Content
            rx.box(
                content,
                padding="24px 20px",
                max_width="640px",
                margin="0 auto",
                width="100%",
            ),
            spacing="0",
            width="100%",
            min_height="100vh",
        ),
        background="#F8FAFC",
        min_height="100vh",
    )


# ── Login ────────────────────────────────────────────────────────────────────

@rx.page(route="/dono/login", on_load=AdminLocalState.on_load_dono_login, title="TUWAYKIFOOD | Acceso Dono")
def dono_login_page() -> rx.Component:
    return rx.box(
        rx.script(_CSS_SCRIPT),
        rx.center(
        rx.vstack(
            rx.vstack(
                rx.image(
                    src="/TUWAYKIFOOD.png",
                    width="180px",
                    height="auto",
                    alt="TUWAYKIFOOD",
                ),
                rx.text(
                    "Panel del Dueño",
                    font_size="20px",
                    font_weight="800",
                    color="#0F172A",
                ),
                rx.text(
                    "Ingresa con tu email y contraseña",
                    font_size="13px",
                    color="#64748B",
                ),
                spacing="2",
                align="center",
            ),
            rx.box(
                rx.vstack(
                    rx.cond(
                        AdminLocalState.error_msg != "",
                        rx.box(
                            rx.text(AdminLocalState.error_msg, font_size="13px", color="#B91C1C", font_weight="600"),
                            background="#FEF2F2",
                            border="1px solid #FECACA",
                            border_radius="8px",
                            padding="10px 14px",
                            width="100%",
                        ),
                        rx.fragment(),
                    ),
                    rx.vstack(
                        rx.text("Email", font_size="12px", font_weight="600", color="#334155"),
                        rx.input(
                            placeholder="dueño@restaurante.com",
                            value=AdminLocalState.email_input,
                            on_change=AdminLocalState.set_email_input,
                            type="text",
                            auto_complete=False,
                            background="#FFFFFF",
                            border="1px solid #E2E8F0",
                            color="#0F172A",
                            border_radius="8px",
                            padding_x="12px",
                            padding_y="10px",
                            font_size="14px",
                            width="100%",
                            _focus={"border": "1px solid #EA580C", "box_shadow": "0 0 0 2px rgba(234,88,12,0.1)"},
                        ),
                        spacing="1",
                        width="100%",
                        align="start",
                    ),
                    rx.vstack(
                        rx.text("Contraseña", font_size="12px", font_weight="600", color="#334155"),
                        rx.input(
                            placeholder="••••••••",
                            value=AdminLocalState.password_input,
                            on_change=AdminLocalState.set_password_input,
                            type="password",
                            auto_complete=False,
                            background="#FFFFFF",
                            border="1px solid #E2E8F0",
                            color="#0F172A",
                            border_radius="8px",
                            padding_x="12px",
                            padding_y="10px",
                            font_size="14px",
                            width="100%",
                            _focus={"border": "1px solid #EA580C", "box_shadow": "0 0 0 2px rgba(234,88,12,0.1)"},
                        ),
                        spacing="1",
                        width="100%",
                        align="start",
                    ),
                    rx.button(
                        "Ingresar",
                        on_click=AdminLocalState.login_admin_local,
                        background="#EA580C",
                        color="#FFFFFF",
                        border_radius="8px",
                        font_size="14px",
                        font_weight="700",
                        width="100%",
                        padding_y="10px",
                        cursor="pointer",
                        _hover={"background": "#C2410C"},
                    ),
                    rx.center(
                        rx.link(
                            "← Volver al sistema (login con PIN)",
                            href="/login",
                            font_size="12px",
                            color="#94A3B8",
                            _hover={"color": "#EA580C"},
                        ),
                        width="100%",
                    ),
                    spacing="4",
                    width="100%",
                ),
                background="#FFFFFF",
                border="1px solid #E2E8F0",
                border_radius="16px",
                padding="28px 24px",
                box_shadow="0 4px 24px rgba(0,0,0,0.08)",
                width="100%",
            ),
            spacing="6",
            align="center",
            width="100%",
            max_width="380px",
        ),
        min_height="100vh",
        background="#F8FAFC",
        padding="24px 16px",
    ),
)


# ── Ventas de hoy (mini-dashboard) ──────────────────────────────────────────

def _dono_kpi(label: str, value, icon: str, accent: str, bg: str) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.box(
                    rx.icon(tag=icon, size=14, color=accent),
                    width="28px",
                    height="28px",
                    border_radius="7px",
                    background=bg,
                    display="flex",
                    align_items="center",
                    justify_content="center",
                    flex_shrink="0",
                ),
                rx.spacer(),
            ),
            rx.text(value, font_size="19px", font_weight="800", color="#0F172A", line_height="1"),
            rx.text(label, font_size="10px", font_weight="600", color="#64748B",
                    text_transform="uppercase", letter_spacing="0.06em"),
            spacing="1",
            align="start",
            width="100%",
        ),
        background="#FFFFFF",
        border="1px solid #E2E8F0",
        border_radius="10px",
        padding="12px 14px",
        box_shadow="0 1px 3px rgba(0,0,0,0.05)",
        flex="1",
    )


def _dono_ventas_row(venta) -> rx.Component:
    return rx.hstack(
        rx.text("#" + venta.pedido_id.to_string(), font_size="11px", color="#94A3B8", min_width="36px", flex_shrink="0"),
        rx.text(venta.mesa_label, font_size="12px", color="#334155", flex="1",
                text_overflow="ellipsis", overflow="hidden", white_space="nowrap"),
        rx.badge(
            venta.metodo_pago,
            background=rx.cond(
                venta.metodo_pago == "efectivo", "#DCFCE7",
                rx.cond(venta.metodo_pago == "tarjeta", "#DBEAFE",
                rx.cond(venta.metodo_pago == "qr", "#FEF3C7",
                rx.cond(venta.metodo_pago == "fiado", "#FFEDD5", "#F1F5F9"))),
            ),
            color=rx.cond(
                venta.metodo_pago == "efectivo", "#15803D",
                rx.cond(venta.metodo_pago == "tarjeta", "#1D4ED8",
                rx.cond(venta.metodo_pago == "qr", "#B45309",
                rx.cond(venta.metodo_pago == "fiado", "#C2410C", "#64748B"))),
            ),
            border_radius="5px",
            font_size="10px",
            font_weight="700",
            padding="2px 5px",
            flex_shrink="0",
        ),
        rx.text(venta.total_con_propina_texto, font_size="12px", font_weight="700",
                color="#15803D", min_width="72px", text_align="right", flex_shrink="0"),
        width="100%",
        align="center",
        padding="7px 10px",
        background="#FFFFFF",
        border_radius="7px",
        border="1px solid #F1F5F9",
        gap="8px",
        _hover={"background": "#F8FAFC"},
    )


def _dono_ventas_section() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.hstack(
                    rx.icon(tag="trending_up", size=15, color="#EA580C"),
                    rx.text("Ventas de hoy", font_size="15px", font_weight="700", color="#0F172A"),
                    spacing="2",
                    align="center",
                ),
                rx.spacer(),
                rx.button(
                    rx.hstack(
                        rx.icon(tag="refresh_cw", size=12),
                        rx.text("Actualizar", font_size="12px", font_weight="600"),
                        spacing="1",
                        align="center",
                    ),
                    on_click=[FoodState.cargar_dashboard, FoodState.cargar_historial_ventas],
                    background="#FFF7ED",
                    color="#EA580C",
                    border="1px solid #FED7AA",
                    border_radius="7px",
                    cursor="pointer",
                    _hover={"opacity": "0.85"},
                ),
                width="100%",
                align="center",
            ),
            # KPIs
            rx.hstack(
                _dono_kpi("Ventas hoy", FoodState.dashboard_ventas_hoy_texto,
                          "trending_up", "#15803D", "#F0FDF4"),
                _dono_kpi("Pedidos cobrados", FoodState.dashboard_pedidos_hoy.to_string(),
                          "receipt_text", "#1D4ED8", "#EFF6FF"),
                _dono_kpi("Propinas hoy", FoodState.dashboard_propina_hoy_texto,
                          "heart", "#9A3412", "#FFF7ED"),
                spacing="3",
                width="100%",
                class_name="twk-form-row",
            ),
            # Últimas ventas
            rx.cond(
                FoodState.historial_ventas.length() > 0,
                rx.vstack(
                    rx.text("Últimas ventas", font_size="12px", font_weight="600", color="#64748B"),
                    rx.foreach(FoodState.historial_ventas, _dono_ventas_row),
                    spacing="1",
                    width="100%",
                ),
                rx.center(
                    rx.text("Sin ventas hoy.", font_size="13px", color="#94A3B8"),
                    padding_y="16px",
                    width="100%",
                ),
            ),
            spacing="3",
            width="100%",
        ),
        background="#FFFFFF",
        border="1px solid #E2E8F0",
        border_radius="12px",
        padding="16px 18px",
        width="100%",
        box_shadow="0 1px 3px rgba(0,0,0,0.06)",
    )


# ── Dashboard del dueño ──────────────────────────────────────────────────────

def _dono_config_content() -> rx.Component:
    return rx.vstack(
        rx.text(
            "Configuracion del local",
            font_size="22px",
            font_weight="800",
            color="#0F172A",
        ),
        rx.cond(
            FoodState.mensaje != "",
            rx.box(
                rx.text(FoodState.mensaje, font_size="13px", color="#15803D", font_weight="600"),
                background="#F0FDF4",
                border="1px solid #BBF7D0",
                border_radius="8px",
                padding="10px 14px",
                width="100%",
            ),
            rx.fragment(),
        ),
        _dono_ventas_section(),
        # Alertas de cumpleaños
        rx.cond(
            FoodState.clientes_cumpleanos_hoy.length() > 0,
            rx.box(
                rx.hstack(
                    rx.icon(tag="cake", size=14, color="#B45309"),
                    rx.vstack(
                        rx.text(
                            "¡Cumpleaños hoy!",
                            font_size="12px", font_weight="700", color="#0F172A",
                        ),
                        rx.foreach(
                            FoodState.clientes_cumpleanos_hoy,
                            lambda c: rx.text(
                                "🎂 " + c.nombre + rx.cond(c.telefono != "", " · " + c.telefono, ""),
                                font_size="11px", color="#78350F",
                            ),
                        ),
                        spacing="1", align="start",
                    ),
                    rx.spacer(),
                    rx.link(
                        rx.hstack(
                            rx.text("Ver", font_size="11px", font_weight="700", color="#EA580C"),
                            rx.icon(tag="arrow_right", size=11, color="#EA580C"),
                            spacing="1", align="center",
                        ),
                        href="/clientes",
                    ),
                    width="100%", align="center", gap="8px",
                ),
                background="#FFFBEB", border="1px solid #FDE68A",
                border_radius="8px", padding="10px 14px", width="100%",
            ),
            rx.fragment(),
        ),
        # Links rápidos: Clientes, Cuentas, Promociones
        rx.hstack(
            rx.link(
                rx.hstack(
                    rx.box(
                        rx.icon(tag="users", size=14, color="#EA580C"),
                        width="28px", height="28px", border_radius="7px",
                        background="#FFF7ED", display="flex",
                        align_items="center", justify_content="center", flex_shrink="0",
                    ),
                    rx.vstack(
                        rx.text("Clientes", font_size="12px", font_weight="700", color="#0F172A"),
                        rx.text("Cumpleaños y fidelización", font_size="10px", color="#64748B"),
                        spacing="0", align="start",
                    ),
                    spacing="2", align="center", flex="1",
                ),
                href="/clientes",
                background="#FFFFFF", border="1px solid #E2E8F0",
                border_radius="9px", padding="10px 12px",
                flex="1", text_decoration="none",
                _hover={"border": "1px solid #FED7AA", "background": "#FFF7ED"},
            ),
            rx.link(
                rx.hstack(
                    rx.box(
                        rx.icon(tag="credit_card", size=14, color="#EA580C"),
                        width="28px", height="28px", border_radius="7px",
                        background="#FFF7ED", display="flex",
                        align_items="center", justify_content="center", flex_shrink="0",
                    ),
                    rx.vstack(
                        rx.text("Fiado", font_size="12px", font_weight="700", color="#0F172A"),
                        rx.text("Cuentas corrientes", font_size="10px", color="#64748B"),
                        spacing="0", align="start",
                    ),
                    spacing="2", align="center", flex="1",
                ),
                href="/cuentas",
                background="#FFFFFF", border="1px solid #E2E8F0",
                border_radius="9px", padding="10px 12px",
                flex="1", text_decoration="none",
                _hover={"border": "1px solid #FED7AA", "background": "#FFF7ED"},
            ),
            rx.link(
                rx.hstack(
                    rx.box(
                        rx.icon(tag="tag", size=14, color="#EA580C"),
                        width="28px", height="28px", border_radius="7px",
                        background="#FFF7ED", display="flex",
                        align_items="center", justify_content="center", flex_shrink="0",
                    ),
                    rx.vstack(
                        rx.text("Promos", font_size="12px", font_weight="700", color="#0F172A"),
                        rx.text("Happy hour y descuentos", font_size="10px", color="#64748B"),
                        spacing="0", align="start",
                    ),
                    spacing="2", align="center", flex="1",
                ),
                href="/promociones",
                background="#FFFFFF", border="1px solid #E2E8F0",
                border_radius="9px", padding="10px 12px",
                flex="1", text_decoration="none",
                _hover={"border": "1px solid #FED7AA", "background": "#FFF7ED"},
            ),
            spacing="2", width="100%",
            class_name="twk-form-row",
        ),
        rx.cond(
            FoodState.inv_alertas_bajo_stock.length() > 0,
            rx.box(
                rx.hstack(
                    rx.hstack(
                        rx.icon(tag="triangle_alert", size=14, color="#B45309"),
                        rx.text(
                            "Stock bajo en: " + FoodState.inv_alertas_bajo_stock_texto,
                            font_size="12px",
                            font_weight="600",
                            color="#92400E",
                        ),
                        spacing="2",
                        align="center",
                        flex="1",
                    ),
                    rx.link(
                        rx.hstack(
                            rx.text("Ver inventario", font_size="11px", font_weight="700", color="#EA580C"),
                            rx.icon(tag="arrow_right", size=11, color="#EA580C"),
                            spacing="1",
                            align="center",
                        ),
                        href="/inventario",
                    ),
                    width="100%",
                    align="center",
                    gap="8px",
                ),
                background="#FFFBEB",
                border="1px solid #FDE68A",
                border_radius="8px",
                padding="10px 14px",
                width="100%",
            ),
            rx.fragment(),
        ),
        rx.link(
            rx.hstack(
                rx.hstack(
                    rx.box(
                        rx.icon(tag="package", size=14, color="#EA580C"),
                        width="28px",
                        height="28px",
                        border_radius="7px",
                        background="#FFF7ED",
                        display="flex",
                        align_items="center",
                        justify_content="center",
                        flex_shrink="0",
                    ),
                    rx.vstack(
                        rx.text("Inventario", font_size="13px", font_weight="700", color="#0F172A"),
                        rx.text("Insumos, recetas y stock", font_size="11px", color="#64748B"),
                        spacing="0",
                        align="start",
                    ),
                    spacing="3",
                    align="center",
                    flex="1",
                ),
                rx.icon(tag="arrow_right", size=14, color="#94A3B8"),
                width="100%",
                align="center",
                justify="between",
            ),
            href="/inventario",
            background="#FFFFFF",
            border="1px solid #E2E8F0",
            border_radius="10px",
            padding="12px 14px",
            width="100%",
            box_shadow="0 1px 3px rgba(0,0,0,0.05)",
            _hover={"border": "1px solid #FED7AA", "background": "#FFF7ED"},
            text_decoration="none",
        ),
        rx.box(
            rx.vstack(
                _section_header("Nombre del local", "store"),
                _field_row("Nombre", FoodState.config_nombre_local, FoodState.set_config_nombre_local, "Mi Restaurante"),
                rx.button(
                    "Guardar nombre",
                    on_click=FoodState.guardar_config_impresora,
                    background="#EA580C",
                    color="#FFFFFF",
                    border_radius="8px",
                    font_size="13px",
                    font_weight="700",
                    cursor="pointer",
                    _hover={"background": "#C2410C"},
                    align_self="end",
                ),
                spacing="4",
                width="100%",
            ),
            background="#FFFFFF",
            border="1px solid #E2E8F0",
            border_radius="12px",
            padding="16px 18px",
            width="100%",
            box_shadow="0 1px 3px rgba(0,0,0,0.06)",
        ),
        _qr_section(),
        _mesas_section(),
        _printer_section(
            title="Impresora Cocina (red)",
            icon="chef_hat",
            activo=FoodState.config_cocina_activa,
            toggle_event=FoodState.toggle_config_cocina_activa,
            ip_value=FoodState.config_cocina_ip,
            ip_change=FoodState.set_config_cocina_ip,
            puerto_value=FoodState.config_cocina_puerto,
            puerto_change=FoodState.set_config_cocina_puerto,
        ),
        _printer_section(
            title="Impresora Caja (red)",
            icon="printer",
            activo=FoodState.config_caja_activa,
            toggle_event=FoodState.toggle_config_caja_activa,
            ip_value=FoodState.config_caja_ip,
            ip_change=FoodState.set_config_caja_ip,
            puerto_value=FoodState.config_caja_puerto,
            puerto_change=FoodState.set_config_caja_puerto,
        ),
        _admin_cuenta_section(),
        spacing="4",
        width="100%",
    )


@rx.page(
    route="/dono",
    on_load=[AdminLocalState.on_load_dono, FoodState.on_load_dono_page],
    title="TUWAYKIFOOD | Panel Dueño",
)
def dono_page() -> rx.Component:
    return _dono_shell(_dono_config_content())
