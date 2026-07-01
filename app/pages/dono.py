"""Panel Administrativo del dueño — dashboard con sub-módulos navegables."""

from __future__ import annotations

import reflex as rx

from app.states.food_state import AdminLocalState, FoodState
from app.components.shared import _CSS_SCRIPT


# ── Paleta ────────────────────────────────────────────────────────────────────
_ORANGE    = "#EA580C"
_ORANGE_DK = "#C2410C"
_ORANGE_LT = "#FFF7ED"
_ORANGE_BD = "#FED7AA"
_SLATE_900 = "#0F172A"
_SLATE_700 = "#334155"
_SLATE_500 = "#64748B"
_SLATE_200 = "#E2E8F0"
_SLATE_100 = "#F1F5F9"
_SLATE_50  = "#F8FAFC"
_WHITE     = "#FFFFFF"
_GREEN     = "#15803D"
_GREEN_LT  = "#F0FDF4"
_BLUE      = "#1D4ED8"
_BLUE_LT   = "#EFF6FF"
_AMBER     = "#B45309"
_AMBER_LT  = "#FFFBEB"
_AMBER_BD  = "#FDE68A"


# ── Estado local para sub-módulo activo ───────────────────────────────────────

class AdminPanelState(rx.State):
    seccion: str = "resumen"

    def ir_a(self, s: str) -> None:
        self.seccion = s


# ── Topbar del shell ──────────────────────────────────────────────────────────

def _dono_topbar() -> rx.Component:
    return rx.hstack(
        rx.hstack(
            rx.image(src="/TUWAYKIFOOD.png", height="44px", width="auto",
                     alt="TUWAYKIFOOD"),
            rx.badge(
                "Panel Administrativo",
                background=_ORANGE_LT,
                color=_ORANGE,
                border=f"1px solid {_ORANGE_BD}",
                border_radius="6px",
                font_size="10px",
                font_weight="700",
                padding="3px 8px",
            ),
            spacing="3",
            align="center",
        ),
        rx.spacer(),
        rx.button(
            rx.hstack(
                rx.icon(tag="log_out", size=14, color=_SLATE_500),
                rx.text("Salir", font_size="13px", font_weight="600",
                        color=_SLATE_500,
                        display=rx.breakpoints(initial="none", sm="block")),
                spacing="2",
                align="center",
            ),
            on_click=AdminLocalState.logout_admin_local,
            background=_SLATE_100,
            border=f"1px solid {_SLATE_200}",
            border_radius="8px",
            padding_x="12px",
            padding_y="8px",
            cursor="pointer",
            _hover={"background": _SLATE_200},
        ),
        width="100%",
        align="center",
        padding=rx.breakpoints(initial="0 16px", md="0 28px"),
        height="60px",
        background=_WHITE,
        border_bottom=f"1px solid {_SLATE_200}",
        position="sticky",
        top="0",
        z_index="20",
        box_shadow="0 1px 4px rgba(0,0,0,0.06)",
    )


# ── Sidebar de sub-módulos ────────────────────────────────────────────────────

def _admin_nav_item(key: str, label: str, icon: str, desc: str) -> rx.Component:
    active = AdminPanelState.seccion == key
    return rx.box(
        rx.hstack(
            rx.box(
                rx.icon(tag=icon, size=16,
                        color=rx.cond(active, _ORANGE, _SLATE_500)),
                width="34px", height="34px",
                border_radius="9px",
                background=rx.cond(active, _ORANGE_LT, _SLATE_100),
                border=rx.cond(active, f"1px solid {_ORANGE_BD}",
                               "1px solid transparent"),
                display="flex", align_items="center",
                justify_content="center", flex_shrink="0",
            ),
            rx.vstack(
                rx.text(label, font_size="13px",
                        font_weight=rx.cond(active, "700", "500"),
                        color=rx.cond(active, _SLATE_900, _SLATE_700),
                        line_height="1"),
                rx.text(desc, font_size="11px",
                        color=rx.cond(active, _SLATE_500, "#94A3B8"),
                        line_height="1"),
                spacing="1", align="start",
            ),
            spacing="3", align="center", width="100%",
        ),
        padding="10px 12px",
        border_radius="10px",
        background=rx.cond(active, _WHITE, "transparent"),
        border=rx.cond(active, f"1px solid {_ORANGE_BD}",
                       "1px solid transparent"),
        box_shadow=rx.cond(active, "0 1px 4px rgba(234,88,12,0.1)", "none"),
        cursor="pointer",
        on_click=AdminPanelState.ir_a(key),
        width="100%",
        transition="all 0.12s ease",
        _hover={
            "background": rx.cond(active, _WHITE, _SLATE_50),
            "border": rx.cond(active, f"1px solid {_ORANGE_BD}",
                              f"1px solid {_SLATE_200}"),
        },
    )


def _admin_sidebar() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.text("Menú", font_size="10px", font_weight="700",
                    color="#94A3B8", text_transform="uppercase",
                    letter_spacing="0.08em", padding_x="4px",
                    padding_bottom="4px"),
            _admin_nav_item("resumen",    "Resumen",      "layout_dashboard", "Vista general del día"),
            _admin_nav_item("ventas",     "Ventas",       "trending_up",      "Historial de cobros"),
            _admin_nav_item("clientes",   "Clientes",     "users",            "Fidelización y alertas"),
            _admin_nav_item("inventario", "Inventario",   "package",          "Stock y alertas"),
            _admin_nav_item("config",     "Configuración","settings",         "Ajustes del sistema"),
            spacing="1", width="100%", align="start",
        ),
        padding="12px",
        background=_SLATE_50,
        border="1px solid #E2E8F0",
        border_radius="14px",
        min_width=rx.breakpoints(initial="100%", md="210px"),
        width=rx.breakpoints(initial="100%", md="210px"),
        flex_shrink="0",
    )


# ── Componentes reutilizables ─────────────────────────────────────────────────

def _kpi_card(label: str, value, icon: str, accent: str, bg: str) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.box(
                    rx.icon(tag=icon, size=18, color=accent),
                    width="40px", height="40px",
                    border_radius="10px",
                    background=bg,
                    display="flex",
                    align_items="center",
                    justify_content="center",
                    flex_shrink="0",
                ),
                rx.spacer(),
            ),
            rx.text(value, font_size="26px", font_weight="800",
                    color=_SLATE_900, line_height="1", margin_top="4px"),
            rx.text(label, font_size="11px", font_weight="600",
                    color=_SLATE_500, text_transform="uppercase",
                    letter_spacing="0.05em"),
            spacing="2", align="start", width="100%",
        ),
        background=_WHITE, border=f"1px solid {_SLATE_200}",
        border_radius="14px", padding="18px 20px",
        box_shadow="0 1px 4px rgba(0,0,0,0.06)", flex="1", min_width="0",
    )


def _venta_row(venta) -> rx.Component:
    return rx.hstack(
        rx.text("#" + venta.pedido_id.to_string(), font_size="11px",
                color=_SLATE_500, min_width="32px", flex_shrink="0"),
        rx.text(venta.mesa_label, font_size="13px", color=_SLATE_700,
                flex="1", text_overflow="ellipsis", overflow="hidden",
                white_space="nowrap"),
        rx.badge(
            venta.metodo_pago,
            background=rx.cond(
                venta.metodo_pago == "efectivo", "#DCFCE7",
                rx.cond(venta.metodo_pago == "tarjeta", "#DBEAFE",
                rx.cond(venta.metodo_pago == "qr", "#FEF3C7",
                rx.cond(venta.metodo_pago == "fiado", "#FFEDD5", _SLATE_100)))),
            color=rx.cond(
                venta.metodo_pago == "efectivo", _GREEN,
                rx.cond(venta.metodo_pago == "tarjeta", _BLUE,
                rx.cond(venta.metodo_pago == "qr", _AMBER,
                rx.cond(venta.metodo_pago == "fiado", _ORANGE_DK, _SLATE_500)))),
            border_radius="5px", font_size="10px", font_weight="700",
            padding="2px 6px", flex_shrink="0",
        ),
        rx.text(venta.total_con_propina_texto, font_size="13px",
                font_weight="700", color=_GREEN, min_width="70px",
                text_align="right", flex_shrink="0"),
        width="100%", align="center",
        padding="8px 10px", border_radius="8px",
        background=_WHITE, border=f"1px solid {_SLATE_100}",
        gap="8px", _hover={"background": _SLATE_50},
    )


def _alerta_cumpleanos() -> rx.Component:
    return rx.cond(
        FoodState.clientes_cumpleanos_hoy.length() > 0,
        rx.box(
            rx.hstack(
                rx.box(
                    rx.icon(tag="cake", size=16, color=_AMBER),
                    width="36px", height="36px",
                    border_radius="9px",
                    background=_AMBER_LT,
                    border=f"1px solid {_AMBER_BD}",
                    display="flex", align_items="center",
                    justify_content="center", flex_shrink="0",
                ),
                rx.vstack(
                    rx.text("Cumpleaños hoy", font_size="12px",
                            font_weight="700", color=_SLATE_900),
                    rx.foreach(
                        FoodState.clientes_cumpleanos_hoy,
                        lambda c: rx.text(
                            c.nombre + rx.cond(c.telefono != "",
                                               " · " + c.telefono, ""),
                            font_size="11px", color="#78350F",
                        ),
                    ),
                    spacing="0", align="start",
                ),
                rx.spacer(),
                rx.link(
                    rx.hstack(
                        rx.text("Ver", font_size="11px",
                                font_weight="700", color=_ORANGE),
                        rx.icon(tag="arrow_right", size=11, color=_ORANGE),
                        spacing="1", align="center",
                    ),
                    href="/clientes",
                ),
                width="100%", align="center", gap="12px",
            ),
            background=_AMBER_LT, border=f"1px solid {_AMBER_BD}",
            border_radius="12px", padding="14px 16px", width="100%",
        ),
        rx.fragment(),
    )


def _alerta_stock() -> rx.Component:
    return rx.cond(
        FoodState.inv_alertas_bajo_stock.length() > 0,
        rx.box(
            rx.hstack(
                rx.box(
                    rx.icon(tag="triangle_alert", size=16, color=_AMBER),
                    width="36px", height="36px",
                    border_radius="9px",
                    background=_AMBER_LT,
                    border=f"1px solid {_AMBER_BD}",
                    display="flex", align_items="center",
                    justify_content="center", flex_shrink="0",
                ),
                rx.vstack(
                    rx.text("Stock bajo", font_size="12px",
                            font_weight="700", color=_SLATE_900),
                    rx.text(FoodState.inv_alertas_bajo_stock_texto,
                            font_size="11px", color="#92400E"),
                    spacing="0", align="start",
                ),
                rx.spacer(),
                rx.link(
                    rx.hstack(
                        rx.text("Inventario", font_size="11px",
                                font_weight="700", color=_ORANGE),
                        rx.icon(tag="arrow_right", size=11, color=_ORANGE),
                        spacing="1", align="center",
                    ),
                    href="/inventario",
                ),
                width="100%", align="center", gap="12px",
            ),
            background=_AMBER_LT, border=f"1px solid {_AMBER_BD}",
            border_radius="12px", padding="14px 16px", width="100%",
        ),
        rx.fragment(),
    )


def _quick_link_card(label: str, desc: str, icon: str, href: str) -> rx.Component:
    return rx.link(
        rx.hstack(
            rx.box(
                rx.icon(tag=icon, size=16, color=_ORANGE),
                width="36px", height="36px",
                border_radius="9px",
                background=_ORANGE_LT,
                border=f"1px solid {_ORANGE_BD}",
                display="flex", align_items="center",
                justify_content="center", flex_shrink="0",
            ),
            rx.vstack(
                rx.text(label, font_size="13px", font_weight="700",
                        color=_SLATE_900),
                rx.text(desc, font_size="11px", color=_SLATE_500,
                        line_height="1.3"),
                spacing="0", align="start",
            ),
            rx.spacer(),
            rx.icon(tag="arrow_right", size=14, color=_SLATE_200),
            spacing="3", align="center", width="100%",
        ),
        href=href,
        background=_WHITE, border=f"1px solid {_SLATE_200}",
        border_radius="12px", padding="12px 14px",
        text_decoration="none",
        _hover={
            "border": f"1px solid {_ORANGE_BD}",
            "background": _ORANGE_LT,
            "transform": "translateX(2px)",
        },
        transition="all 0.15s ease",
        width="100%", display="block",
    )


# ── SECCIÓN: RESUMEN ──────────────────────────────────────────────────────────

def _section_resumen() -> rx.Component:
    return rx.vstack(
        # Encabezado
        rx.hstack(
            rx.vstack(
                rx.text("Resumen del día", font_size="18px",
                        font_weight="800", color=_SLATE_900, line_height="1"),
                rx.text("Vista general de tu negocio hoy",
                        font_size="13px", color=_SLATE_500),
                spacing="1", align="start",
            ),
            rx.spacer(),
            rx.button(
                rx.hstack(
                    rx.icon(tag="refresh_cw", size=13, color=_ORANGE),
                    rx.text("Actualizar", font_size="12px",
                            font_weight="600", color=_ORANGE),
                    spacing="1", align="center",
                ),
                on_click=[FoodState.cargar_dashboard,
                          FoodState.cargar_historial_ventas],
                background=_ORANGE_LT, border=f"1px solid {_ORANGE_BD}",
                border_radius="7px", padding_x="12px", padding_y="7px",
                cursor="pointer", _hover={"opacity": "0.85"},
            ),
            width="100%", align="center",
        ),
        # KPIs
        rx.flex(
            _kpi_card("Ventas hoy", FoodState.dashboard_ventas_hoy_texto,
                      "trending_up", _GREEN, _GREEN_LT),
            _kpi_card("Pedidos cobrados",
                      FoodState.dashboard_pedidos_hoy.to_string(),
                      "receipt_text", _BLUE, _BLUE_LT),
            _kpi_card("Propinas hoy",
                      FoodState.dashboard_propina_hoy_texto,
                      "heart", "#9A3412", _ORANGE_LT),
            gap="12px", width="100%", flex_wrap="wrap",
        ),
        # Alertas
        _alerta_cumpleanos(),
        _alerta_stock(),
        # Acceso rápido
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.icon(tag="layout_grid", size=14, color=_SLATE_500),
                    rx.text("Acceso rápido", font_size="13px",
                            font_weight="700", color=_SLATE_700),
                    spacing="2", align="center",
                ),
                rx.grid(
                    _quick_link_card("Clientes",
                                     "Cumpleaños y fidelización",
                                     "users", "/clientes"),
                    _quick_link_card("Fiado",
                                     "Cuentas corrientes",
                                     "credit_card", "/cuentas"),
                    _quick_link_card("Promociones",
                                     "Happy hour y descuentos",
                                     "tag", "/promociones"),
                    _quick_link_card("Inventario",
                                     "Insumos, recetas y stock",
                                     "package", "/inventario"),
                    columns=rx.breakpoints(initial="1", sm="2"),
                    gap="10px", width="100%",
                ),
                spacing="3", width="100%",
            ),
            background=_WHITE, border=f"1px solid {_SLATE_200}",
            border_radius="16px", padding="18px 20px",
            width="100%", box_shadow="0 1px 4px rgba(0,0,0,0.06)",
        ),
        spacing="4", width="100%",
    )


# ── SECCIÓN: VENTAS ───────────────────────────────────────────────────────────

def _section_ventas() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.vstack(
                rx.text("Ventas del día", font_size="18px",
                        font_weight="800", color=_SLATE_900, line_height="1"),
                rx.text("Historial de cobros de hoy",
                        font_size="13px", color=_SLATE_500),
                spacing="1", align="start",
            ),
            rx.spacer(),
            rx.button(
                rx.hstack(
                    rx.icon(tag="refresh_cw", size=13, color=_ORANGE),
                    rx.text("Actualizar", font_size="12px",
                            font_weight="600", color=_ORANGE),
                    spacing="1", align="center",
                ),
                on_click=[FoodState.cargar_dashboard,
                          FoodState.cargar_historial_ventas],
                background=_ORANGE_LT, border=f"1px solid {_ORANGE_BD}",
                border_radius="7px", padding_x="12px", padding_y="7px",
                cursor="pointer", _hover={"opacity": "0.85"},
            ),
            width="100%", align="center",
        ),
        # KPIs
        rx.flex(
            _kpi_card("Total recaudado", FoodState.dashboard_ventas_hoy_texto,
                      "dollar_sign", _GREEN, _GREEN_LT),
            _kpi_card("Pedidos cobrados",
                      FoodState.dashboard_pedidos_hoy.to_string(),
                      "receipt_text", _BLUE, _BLUE_LT),
            _kpi_card("Propinas", FoodState.dashboard_propina_hoy_texto,
                      "heart", "#9A3412", _ORANGE_LT),
            gap="12px", width="100%", flex_wrap="wrap",
        ),
        # Lista de ventas
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.icon(tag="list", size=14, color=_SLATE_500),
                    rx.text("Cobros realizados", font_size="13px",
                            font_weight="700", color=_SLATE_700),
                    rx.spacer(),
                    rx.link(
                        "Ver reportes completos →",
                        href="/reportes",
                        font_size="11px", color=_ORANGE,
                        font_weight="600", _hover={"opacity": "0.8"},
                    ),
                    spacing="2", align="center", width="100%",
                ),
                rx.cond(
                    FoodState.historial_ventas.length() > 0,
                    rx.vstack(
                        rx.foreach(FoodState.historial_ventas, _venta_row),
                        spacing="1", width="100%",
                    ),
                    rx.center(
                        rx.vstack(
                            rx.icon(tag="receipt_text", size=32,
                                    color=_SLATE_200),
                            rx.text("Sin ventas registradas hoy.",
                                    font_size="13px", color=_SLATE_500),
                            spacing="2", align="center",
                        ),
                        padding_y="28px", width="100%",
                    ),
                ),
                spacing="3", width="100%",
            ),
            background=_WHITE, border=f"1px solid {_SLATE_200}",
            border_radius="16px", padding="20px",
            width="100%", box_shadow="0 1px 4px rgba(0,0,0,0.06)",
        ),
        spacing="4", width="100%",
    )


# ── SECCIÓN: CLIENTES ─────────────────────────────────────────────────────────

def _section_clientes() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.vstack(
                rx.text("Clientes", font_size="18px",
                        font_weight="800", color=_SLATE_900, line_height="1"),
                rx.text("Fidelización y alertas del día",
                        font_size="13px", color=_SLATE_500),
                spacing="1", align="start",
            ),
            rx.spacer(),
            rx.link(
                rx.hstack(
                    rx.icon(tag="arrow_right", size=14, color=_WHITE),
                    rx.text("Ir a Clientes", font_size="13px",
                            font_weight="700", color=_WHITE),
                    spacing="2", align="center",
                ),
                href="/clientes",
                background=_ORANGE, border_radius="8px",
                padding="8px 14px", text_decoration="none",
                _hover={"background": _ORANGE_DK},
            ),
            width="100%", align="center",
        ),
        # Alertas de cumpleaños
        _alerta_cumpleanos(),
        # Card de acceso
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.icon(tag="users", size=16, color=_ORANGE),
                    rx.text("Gestión de clientes", font_size="14px",
                            font_weight="700", color=_SLATE_900),
                    spacing="2", align="center",
                ),
                rx.text(
                    "Registra clientes frecuentes, lleva el historial de sus "
                    "consumos, gestiona cuentas corrientes (fiado) y recibe "
                    "alertas automáticas de cumpleaños.",
                    font_size="13px", color=_SLATE_500, line_height="1.6",
                ),
                rx.grid(
                    _quick_link_card("Todos los clientes",
                                     "Lista completa",
                                     "users", "/clientes"),
                    _quick_link_card("Cuentas corrientes",
                                     "Fiado y créditos",
                                     "credit_card", "/cuentas"),
                    columns=rx.breakpoints(initial="1", sm="2"),
                    gap="10px", width="100%",
                ),
                spacing="3", width="100%",
            ),
            background=_WHITE, border=f"1px solid {_SLATE_200}",
            border_radius="16px", padding="20px",
            width="100%", box_shadow="0 1px 4px rgba(0,0,0,0.06)",
        ),
        spacing="4", width="100%",
    )


# ── SECCIÓN: INVENTARIO ───────────────────────────────────────────────────────

def _section_inventario() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.vstack(
                rx.text("Inventario", font_size="18px",
                        font_weight="800", color=_SLATE_900, line_height="1"),
                rx.text("Stock y alertas de insumos",
                        font_size="13px", color=_SLATE_500),
                spacing="1", align="start",
            ),
            rx.spacer(),
            rx.link(
                rx.hstack(
                    rx.icon(tag="arrow_right", size=14, color=_WHITE),
                    rx.text("Ir a Inventario", font_size="13px",
                            font_weight="700", color=_WHITE),
                    spacing="2", align="center",
                ),
                href="/inventario",
                background=_ORANGE, border_radius="8px",
                padding="8px 14px", text_decoration="none",
                _hover={"background": _ORANGE_DK},
            ),
            width="100%", align="center",
        ),
        # Alerta stock bajo
        _alerta_stock(),
        # Card descriptiva
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.icon(tag="package", size=16, color=_ORANGE),
                    rx.text("Control de insumos", font_size="14px",
                            font_weight="700", color=_SLATE_900),
                    spacing="2", align="center",
                ),
                rx.text(
                    "Registra insumos, define niveles mínimos de stock y recibe "
                    "alertas automáticas cuando un insumo está por agotarse. "
                    "Asocia recetas a los platos para descuento automático de stock.",
                    font_size="13px", color=_SLATE_500, line_height="1.6",
                ),
                rx.grid(
                    _quick_link_card("Insumos y stock",
                                     "Ver inventario completo",
                                     "package", "/inventario"),
                    _quick_link_card("Promociones",
                                     "Happy hour y descuentos",
                                     "tag", "/promociones"),
                    columns=rx.breakpoints(initial="1", sm="2"),
                    gap="10px", width="100%",
                ),
                spacing="3", width="100%",
            ),
            background=_WHITE, border=f"1px solid {_SLATE_200}",
            border_radius="16px", padding="20px",
            width="100%", box_shadow="0 1px 4px rgba(0,0,0,0.06)",
        ),
        spacing="4", width="100%",
    )


# ── SECCIÓN: CONFIGURACIÓN ────────────────────────────────────────────────────

def _config_shortcut(icon: str, label: str, desc: str, tab: str) -> rx.Component:
    return rx.link(
        rx.hstack(
            rx.box(
                rx.icon(tag=icon, size=15, color=_ORANGE),
                width="36px", height="36px",
                border_radius="9px",
                background=_ORANGE_LT,
                border=f"1px solid {_ORANGE_BD}",
                display="flex", align_items="center",
                justify_content="center", flex_shrink="0",
            ),
            rx.vstack(
                rx.text(label, font_size="13px",
                        font_weight="700", color=_SLATE_900),
                rx.text(desc, font_size="11px", color=_SLATE_500),
                spacing="0", align="start",
            ),
            rx.spacer(),
            rx.icon(tag="arrow_right", size=13, color=_SLATE_200),
            spacing="3", align="center", width="100%",
        ),
        href=f"/configuracion",
        background=_WHITE, border=f"1px solid {_SLATE_200}",
        border_radius="12px", padding="12px 14px",
        text_decoration="none",
        _hover={
            "border": f"1px solid {_ORANGE_BD}",
            "background": _ORANGE_LT,
            "transform": "translateX(2px)",
        },
        transition="all 0.15s ease",
        width="100%", display="block",
    )


def _section_config() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.vstack(
                rx.text("Configuración", font_size="18px",
                        font_weight="800", color=_SLATE_900, line_height="1"),
                rx.text("Ajustes del sistema y del restaurante",
                        font_size="13px", color=_SLATE_500),
                spacing="1", align="start",
            ),
            rx.spacer(),
            rx.link(
                rx.hstack(
                    rx.icon(tag="settings", size=14, color=_WHITE),
                    rx.text("Abrir configuración", font_size="13px",
                            font_weight="700", color=_WHITE),
                    spacing="2", align="center",
                ),
                href="/configuracion",
                background=_ORANGE, border_radius="8px",
                padding="8px 14px", text_decoration="none",
                _hover={"background": _ORANGE_DK},
            ),
            width="100%", align="center",
        ),
        # Accesos directos a cada sub-módulo de /configuracion
        rx.box(
            rx.vstack(
                rx.text("Sub-módulos disponibles", font_size="12px",
                        font_weight="600", color=_SLATE_500,
                        text_transform="uppercase", letter_spacing="0.06em"),
                rx.vstack(
                    _config_shortcut("store", "Local",
                                     "Nombre del restaurante", "local"),
                    _config_shortcut("qr_code", "Carta digital",
                                     "Slug URL y código QR", "carta"),
                    _config_shortcut("layout_grid", "Mesas",
                                     "Salon y sectores", "mesas"),
                    _config_shortcut("printer", "Impresoras",
                                     "Cocina y caja ESC/POS", "impresoras"),
                    _config_shortcut("key_round", "Cuenta Admin",
                                     "Email y contraseña de acceso", "cuenta"),
                    spacing="2", width="100%",
                ),
                spacing="3", width="100%",
            ),
            background=_WHITE, border=f"1px solid {_SLATE_200}",
            border_radius="16px", padding="20px",
            width="100%", box_shadow="0 1px 4px rgba(0,0,0,0.06)",
        ),
        spacing="4", width="100%",
    )


# ── Área de contenido dinámico ────────────────────────────────────────────────

def _content_area() -> rx.Component:
    return rx.cond(
        AdminPanelState.seccion == "resumen",
        _section_resumen(),
        rx.cond(
            AdminPanelState.seccion == "ventas",
            _section_ventas(),
            rx.cond(
                AdminPanelState.seccion == "clientes",
                _section_clientes(),
                rx.cond(
                    AdminPanelState.seccion == "inventario",
                    _section_inventario(),
                    _section_config(),
                ),
            ),
        ),
    )


# ── Cuerpo del dashboard ──────────────────────────────────────────────────────

def _dono_dashboard() -> rx.Component:
    return rx.vstack(
        # Mensaje global de éxito
        rx.cond(
            FoodState.mensaje != "",
            rx.hstack(
                rx.icon(tag="check_circle", size=14, color=_GREEN),
                rx.text(FoodState.mensaje, font_size="13px",
                        color=_GREEN, font_weight="600"),
                spacing="2", align="center",
                background=_GREEN_LT,
                border="1px solid #BBF7D0",
                border_radius="10px",
                padding="10px 16px",
                width="100%",
            ),
            rx.fragment(),
        ),
        # Layout: sidebar + contenido
        rx.flex(
            _admin_sidebar(),
            rx.box(_content_area(), flex="1", min_width="0"),
            direction=rx.breakpoints(initial="column", md="row"),
            gap="16px",
            width="100%",
            align="start",
        ),
        spacing="4",
        width="100%",
    )


# ── Shell del panel ───────────────────────────────────────────────────────────

def _dono_shell(content: rx.Component) -> rx.Component:
    return rx.box(
        rx.script(_CSS_SCRIPT),
        rx.vstack(
            _dono_topbar(),
            rx.box(
                content,
                padding=rx.breakpoints(
                    initial="16px", sm="20px", lg="28px 32px"),
                max_width="1400px",
                margin="0 auto",
                width="100%",
            ),
            spacing="0",
            width="100%",
            min_height="100vh",
        ),
        background=_SLATE_50,
        min_height="100vh",
    )


# ── Login ─────────────────────────────────────────────────────────────────────

@rx.page(route="/admin/login",
         on_load=AdminLocalState.on_load_dono_login,
         title="TUWAYKIFOOD | Acceso Administrativo")
def dono_login_page() -> rx.Component:
    return rx.box(
        rx.script(_CSS_SCRIPT),
        rx.center(
            rx.vstack(
                rx.vstack(
                    rx.box(
                        rx.image(src="/TUWAYKIFOOD.png", height="60px",
                                 width="auto", alt="TUWAYKIFOOD"),
                        background=_ORANGE,
                        border_radius="16px",
                        padding="10px 14px",
                        display="flex",
                        align_items="center",
                        justify_content="center",
                    ),
                    rx.vstack(
                        rx.text("Panel Administrativo", font_size="22px",
                                font_weight="800", color=_WHITE,
                                text_align="center"),
                        rx.text("Ingresa con tu email y contraseña",
                                font_size="13px", color="#475569",
                                text_align="center"),
                        spacing="1", align="center",
                    ),
                    spacing="4", align="center",
                ),
                rx.box(
                    rx.vstack(
                        rx.cond(
                            AdminLocalState.error_msg != "",
                            rx.box(
                                rx.hstack(
                                    rx.icon(tag="circle_alert", size=14,
                                            color="#B91C1C"),
                                    rx.text(AdminLocalState.error_msg,
                                            font_size="13px", color="#B91C1C",
                                            font_weight="600"),
                                    spacing="2", align="center",
                                ),
                                background="#FEF2F2",
                                border="1px solid #FECACA",
                                border_radius="8px",
                                padding="10px 14px",
                                width="100%",
                            ),
                            rx.fragment(),
                        ),
                        rx.vstack(
                            rx.text("Email", font_size="11px",
                                    font_weight="600", color="#64748B",
                                    text_transform="uppercase",
                                    letter_spacing="0.06em"),
                            rx.el.input(
                                placeholder="dueño@restaurante.com",
                                value=AdminLocalState.email_input,
                                on_change=AdminLocalState.set_email_input,
                                on_key_down=AdminLocalState.login_on_enter,
                                type="text",
                                autocomplete="off",
                                class_name="twk-login-input",
                            ),
                            spacing="1", width="100%", align="start",
                        ),
                        rx.vstack(
                            rx.text("Contraseña", font_size="11px",
                                    font_weight="600", color="#64748B",
                                    text_transform="uppercase",
                                    letter_spacing="0.06em"),
                            rx.el.input(
                                placeholder="••••••••",
                                value=AdminLocalState.password_input,
                                on_change=AdminLocalState.set_password_input,
                                on_key_down=AdminLocalState.login_on_enter,
                                type="password",
                                autocomplete="new-password",
                                class_name="twk-login-input",
                            ),
                            spacing="1", width="100%", align="start",
                        ),
                        rx.button(
                            "Ingresar al Panel",
                            on_click=AdminLocalState.login_admin_local,
                            background=_ORANGE, color=_WHITE,
                            border_radius="10px", font_size="14px",
                            font_weight="700", width="100%",
                            padding_y="14px", cursor="pointer",
                            _hover={"background": _ORANGE_DK,
                                    "box_shadow": "0 6px 20px rgba(234,88,12,0.45)"},
                            box_shadow="0 4px 14px rgba(234,88,12,0.35)",
                            transition="all 0.15s",
                        ),
                        rx.center(
                            rx.link(
                                "← Volver al login con PIN",
                                href="/login",
                                font_size="12px", color="#64748B",
                                _hover={"color": _ORANGE},
                            ),
                            width="100%",
                        ),
                        spacing="4", width="100%",
                    ),
                    background="#1E293B",
                    border="1px solid #334155",
                    border_radius="20px",
                    padding="32px 28px",
                    box_shadow="0 20px 60px rgba(0,0,0,0.4)",
                    width="100%",
                ),
                spacing="6", align="center",
                width="100%", max_width="400px",
            ),
            min_height="100vh",
            background="#0F172A",
            padding="24px 16px",
        ),
    )


# ── Dashboard ─────────────────────────────────────────────────────────────────

@rx.page(
    route="/admin",
    on_load=[AdminLocalState.on_load_dono, FoodState.on_load_dono_page],
    title="TUWAYKIFOOD | Panel Administrativo",
)
def dono_page() -> rx.Component:
    return _dono_shell(_dono_dashboard())
