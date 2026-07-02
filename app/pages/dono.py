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
            rx.image(src="/TUWAYKIFOODFAVICON.png", height="36px", width="36px",
                     border_radius="9px", alt="TUWAYKIFOOD"),
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
            _admin_nav_item("ventas",     "Reportes",     "trending_up",      "Dashboard y ventas del día"),
            _admin_nav_item("clientes",   "Clientes",     "users",            "Fidelización y alertas"),
            _admin_nav_item("cuentas",    "Cuentas",      "credit_card",      "Fiado y créditos"),
            _admin_nav_item("promociones","Promociones",  "tag",              "Happy hour y descuentos"),
            _admin_nav_item("inventario", "Inventario",   "package",          "Stock y alertas"),
            _admin_nav_item("usuarios",   "Usuarios",     "users_round",      "Personal y PINs"),
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

def _kpi_trend(value, suffix: str = "%") -> rx.Component:
    """Indicador '↑ 12% vs ayer' / '↓ 3% vs ayer', color segun signo."""
    return rx.hstack(
        rx.text(
            rx.cond(value >= 0, "↑ ", "↓ "),
            rx.cond(value >= 0, value, -value),
            suffix, " vs ayer",
            font_size="12px", font_weight="600",
        ),
        color=rx.cond(value >= 0, _GREEN, "#DC2626"),
        margin_top="4px",
    )


def _kpi_card(label: str, value, icon: str, accent: str, bg: str,
              trend: rx.Component | None = None) -> rx.Component:
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
            trend if trend is not None else rx.fragment(),
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


def _top_plato_row(plato, index: int) -> rx.Component:
    max_cantidad = FoodState.dashboard_top_platos[0].cantidad
    pct = rx.cond(
        max_cantidad > 0,
        (plato.cantidad * 100) / max_cantidad,
        0,
    )
    return rx.hstack(
        rx.box(
            rx.text((index + 1).to_string(), font_size="11px",
                    font_weight="800", color=_WHITE),
            width="24px", height="24px", border_radius="6px",
            background=rx.cond(
                index == 0, _ORANGE,
                rx.cond(index == 1, "#F97316",
                rx.cond(index == 2, "#FB923C", "#CBD5E1"))),
            display="flex", align_items="center", justify_content="center",
            flex_shrink="0",
        ),
        rx.vstack(
            rx.text(plato.nombre, font_size="13px", font_weight="600",
                    color=_SLATE_900, width="100%", overflow="hidden",
                    text_overflow="ellipsis", white_space="nowrap"),
            rx.box(
                rx.box(
                    width=pct.to_string() + "%", height="100%",
                    background=_ORANGE, border_radius="99px",
                ),
                width="100%", height="4px", background=_SLATE_200,
                border_radius="99px", overflow="hidden", margin_top="4px",
            ),
            spacing="0", align="start", flex="1", min_width="0",
        ),
        rx.text(plato.cantidad.to_string(), font_size="12px",
                font_weight="700", color=_SLATE_500, flex_shrink="0"),
        width="100%", align="center", gap="10px",
    )


def _alerta_cumpleanos() -> rx.Component:
    return rx.cond(
        FoodState.clientes_cumpleanos_hoy.length() > 0,
        rx.box(
            rx.hstack(
                rx.box(
                    rx.text("🎂", font_size="16px", line_height="1"),
                    width="36px", height="36px",
                    border_radius="9px",
                    background="#FEE2E2",
                    border="1px solid #FCA5A5",
                    display="flex", align_items="center",
                    justify_content="center", flex_shrink="0",
                ),
                rx.vstack(
                    rx.text("Cumpleaños hoy", font_size="12px",
                            font_weight="700", color="#991B1B"),
                    rx.foreach(
                        FoodState.clientes_cumpleanos_hoy,
                        lambda c: rx.text(
                            c.nombre + rx.cond(c.telefono != "",
                                               " · " + c.telefono, ""),
                            font_size="11px", color="#B91C1C",
                        ),
                    ),
                    spacing="0", align="start",
                ),
                rx.spacer(),
                rx.hstack(
                    rx.text("Ver", font_size="11px",
                            font_weight="700", color=_ORANGE),
                    rx.icon(tag="arrow_right", size=11, color=_ORANGE),
                    spacing="1", align="center",
                    on_click=AdminPanelState.ir_a("clientes"),
                    cursor="pointer",
                ),
                width="100%", align="center", gap="12px",
            ),
            background="#FEF2F2", border="1px solid #FCA5A5",
            border_radius="12px", padding="14px 16px",
            flex="1", min_width=rx.breakpoints(initial="100%", sm="260px"),
        ),
        rx.fragment(),
    )


def _alerta_stock() -> rx.Component:
    return rx.cond(
        FoodState.inv_alertas_bajo_stock.length() > 0,
        rx.box(
            rx.hstack(
                rx.box(
                    rx.text("⚠️", font_size="16px", line_height="1"),
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
                rx.hstack(
                    rx.text("Inventario", font_size="11px",
                            font_weight="700", color=_ORANGE),
                    rx.icon(tag="arrow_right", size=11, color=_ORANGE),
                    spacing="1", align="center",
                    on_click=AdminPanelState.ir_a("inventario"),
                    cursor="pointer",
                ),
                width="100%", align="center", gap="12px",
            ),
            background=_AMBER_LT, border=f"1px solid {_AMBER_BD}",
            border_radius="12px", padding="14px 16px",
            flex="1", min_width=rx.breakpoints(initial="100%", sm="260px"),
        ),
        rx.fragment(),
    )


def _quick_link_card(label: str, desc: str, icon: str, href: str, emoji: str = "") -> rx.Component:
    return rx.link(
        rx.hstack(
            rx.box(
                rx.text(emoji, font_size="16px", line_height="1") if emoji
                else rx.icon(tag=icon, size=16, color=_ORANGE),
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
                      "trending_up", _GREEN, _GREEN_LT,
                      trend=_kpi_trend(FoodState.dashboard_ventas_trend_pct)),
            _kpi_card("Pedidos cobrados",
                      FoodState.dashboard_pedidos_hoy.to_string(),
                      "receipt_text", _BLUE, _BLUE_LT,
                      trend=_kpi_trend(FoodState.dashboard_pedidos_trend, suffix="")),
            _kpi_card("Ticket promedio",
                      FoodState.dashboard_ticket_promedio_texto,
                      "calculator", "#7C3AED", "#F5F3FF",
                      trend=_kpi_trend(FoodState.dashboard_ticket_trend_pct)),
            _kpi_card("Propinas hoy",
                      FoodState.dashboard_propina_hoy_texto,
                      "heart", "#9A3412", _ORANGE_LT,
                      trend=_kpi_trend(FoodState.dashboard_propina_trend_pct)),
            gap="12px", width="100%", flex_wrap="wrap",
        ),
        # Alertas
        rx.flex(
            _alerta_cumpleanos(),
            _alerta_stock(),
            gap="12px", width="100%", flex_wrap="wrap",
        ),
        # Últimas ventas + accesos operativos / top platos
        rx.grid(
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.text("Últimas ventas", font_size="13px",
                                font_weight="700", color=_SLATE_700),
                        rx.spacer(),
                        rx.link(
                            rx.hstack(
                                rx.text("Ver todas", font_size="11px",
                                        font_weight="700", color=_ORANGE),
                                rx.icon(tag="arrow_right", size=11, color=_ORANGE),
                                spacing="1", align="center",
                            ),
                            on_click=AdminPanelState.ir_a("ventas"),
                            cursor="pointer",
                        ),
                        width="100%", align="center",
                    ),
                    rx.cond(
                        FoodState.historial_ventas.length() == 0,
                        rx.center(
                            rx.text("Sin ventas todavía", font_size="12px",
                                    color=_SLATE_500),
                            padding_y="24px", width="100%",
                        ),
                        rx.vstack(
                            rx.foreach(
                                FoodState.historial_ventas_recientes,
                                _venta_row,
                            ),
                            spacing="2", width="100%",
                        ),
                    ),
                    spacing="3", width="100%",
                ),
                background=_WHITE, border=f"1px solid {_SLATE_200}",
                border_radius="16px", padding="18px 20px",
                width="100%", box_shadow="0 1px 4px rgba(0,0,0,0.06)",
            ),
            rx.vstack(
                # Accesos operativos
                rx.box(
                    rx.vstack(
                        rx.text("Accesos operativos", font_size="13px",
                                font_weight="700", color=_SLATE_700),
                        rx.grid(
                            _quick_link_card("Mozos", "Mesas y comanda",
                                             "utensils", "/mozos", "🧑‍🍳"),
                            _quick_link_card("Cocina", "KDS / Producción",
                                             "chef_hat", "/cocina", "🍳"),
                            _quick_link_card("Caja", "Cobro y tickets",
                                             "landmark", "/caja", "🖥️"),
                            _quick_link_card("Mostrador", "Takeaway rápido",
                                             "shopping_bag", "/mostrador", "🛍️"),
                            columns="1", gap="8px", width="100%",
                        ),
                        spacing="3", width="100%",
                    ),
                    background=_WHITE, border=f"1px solid {_SLATE_200}",
                    border_radius="16px", padding="18px 20px",
                    width="100%", box_shadow="0 1px 4px rgba(0,0,0,0.06)",
                ),
                # Top platos hoy
                rx.box(
                    rx.vstack(
                        rx.text("Top platos hoy", font_size="13px",
                                font_weight="700", color=_SLATE_700),
                        rx.cond(
                            FoodState.dashboard_top_platos.length() == 0,
                            rx.center(
                                rx.text("Sin datos todavía", font_size="12px",
                                        color=_SLATE_500),
                                padding_y="16px", width="100%",
                            ),
                            rx.vstack(
                                rx.foreach(
                                    FoodState.dashboard_top_platos,
                                    _top_plato_row,
                                ),
                                spacing="2", width="100%",
                            ),
                        ),
                        spacing="3", width="100%",
                    ),
                    background=_WHITE, border=f"1px solid {_SLATE_200}",
                    border_radius="16px", padding="18px 20px",
                    width="100%", box_shadow="0 1px 4px rgba(0,0,0,0.06)",
                ),
                spacing="4", width="100%",
            ),
            columns=rx.breakpoints(initial="1", lg="2fr 1fr"),
            gap="16px", width="100%",
        ),
        spacing="4", width="100%",
    )




# ── Área de contenido dinámico ────────────────────────────────────────────────

def _content_area() -> rx.Component:
    # Import diferido: cuentas.py/promociones.py/clientes.py/inventario.py
    # importan _dono_shell de este módulo, así que importarlos a nivel de
    # módulo aquí generaría un ciclo.
    from app.pages.cuentas import _cuentas_content
    from app.pages.promociones import _promociones_content
    from app.pages.reportes import _reportes_content
    from app.pages.clientes import _clientes_content
    from app.pages.inventario import _inventario_content
    from app.pages.configuracion import _configuracion_content
    from app.pages.usuarios import _usuarios_content

    return rx.cond(
        AdminPanelState.seccion == "resumen",
        _section_resumen(),
        rx.cond(
            AdminPanelState.seccion == "ventas",
            _reportes_content(),
            rx.cond(
                AdminPanelState.seccion == "clientes",
                _clientes_content(),
                rx.cond(
                    AdminPanelState.seccion == "cuentas",
                    _cuentas_content(),
                    rx.cond(
                        AdminPanelState.seccion == "promociones",
                        _promociones_content(),
                        rx.cond(
                            AdminPanelState.seccion == "inventario",
                            _inventario_content(),
                            rx.cond(
                                AdminPanelState.seccion == "usuarios",
                                _usuarios_content(),
                                _configuracion_content(),
                            ),
                        ),
                    ),
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
                rx.icon(tag="circle_check", size=14, color=_GREEN),
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
        class_name="light",
    )


# ── Login ─────────────────────────────────────────────────────────────────────

def _admin_glow() -> rx.Component:
    return rx.box(
        position="absolute",
        top="50%", left="50%",
        transform="translate(-50%, -50%)",
        width=rx.breakpoints(initial="280px", md="420px"),
        height=rx.breakpoints(initial="280px", md="420px"),
        background="radial-gradient(circle, rgba(234,88,12,0.35) 0%, rgba(234,88,12,0) 70%)",
        pointer_events="none",
        z_index="0",
    )


def _brand_banner_generico() -> rx.Component:
    """Sin empresa en la URL — logo de marca TUWAYKIFOOD, tamaño grande."""
    return rx.box(
        _admin_glow(),
        rx.center(
            rx.image(
                src="/TUWAYKIFOOD.png",
                height=rx.breakpoints(initial="122px", sm="150px", md="178px"),
                width="auto",
                alt="TUWAYKIFOOD",
            ),
            width="100%", height="100%",
        ),
        background=_WHITE,
        border_radius="20px",
        width=rx.breakpoints(initial="190px", sm="230px", md="270px"),
        height=rx.breakpoints(initial="130px", sm="158px", md="186px"),
        box_shadow="0 0 0 3px rgba(234,88,12,0.4), 0 12px 40px rgba(0,0,0,0.5)",
        position="relative",
        z_index="1",
    )


def _brand_banner_empresa() -> rx.Component:
    """Con ?empresa= en la URL — logo de esa empresa, un poco más chico."""
    return rx.box(
        _admin_glow(),
        rx.cond(
            AdminLocalState.login_empresa_logo != "",
            rx.center(
                rx.image(
                    src=AdminLocalState.login_empresa_logo,
                    height=rx.breakpoints(initial="90px", sm="112px", md="132px"),
                    width="auto",
                    alt=AdminLocalState.login_empresa_nombre,
                ),
                width="100%", height="100%",
            ),
            rx.box(
                rx.text(
                    AdminLocalState.login_empresa_nombre[:1].upper(),
                    font_size=rx.breakpoints(initial="38px", md="52px"),
                    font_weight="800", color=_WHITE, line_height="1",
                ),
                width="100%", height="100%",
                display="flex", align_items="center", justify_content="center",
                background="linear-gradient(135deg,#FDBA74,#EA580C)",
                border_radius="20px",
            ),
        ),
        background=_WHITE,
        border_radius="20px",
        width=rx.breakpoints(initial="155px", sm="190px", md="220px"),
        height=rx.breakpoints(initial="105px", sm="128px", md="150px"),
        box_shadow="0 0 0 3px rgba(234,88,12,0.4), 0 12px 40px rgba(0,0,0,0.5)",
        position="relative",
        z_index="1",
    )


def _brand_banner() -> rx.Component:
    """Logo de marca — usado en los dos puntos de entrada (login PIN y login
    admin) para que se vea prominente sin cubrir todo el ancho de la pantalla."""
    return rx.cond(
        AdminLocalState.login_empresa_nombre != "",
        _brand_banner_empresa(),
        _brand_banner_generico(),
    )


@rx.page(route="/admin/login",
         on_load=AdminLocalState.on_load_dono_login,
         title="TUWAYKIFOOD | Acceso Administrativo")
def dono_login_page() -> rx.Component:
    return rx.box(
        rx.script(_CSS_SCRIPT),
        rx.center(
            rx.vstack(
                _brand_banner(),
                rx.vstack(
                    rx.text("Panel Administrativo", font_size="22px",
                            font_weight="800", color=_WHITE,
                            text_align="center"),
                    rx.text("Ingresa con tu email y contraseña",
                            font_size="13px", color="#475569",
                            text_align="center"),
                    spacing="1", align="center",
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
                            rx.input(
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
                            rx.box(
                                rx.input(
                                    placeholder="••••••••",
                                    value=AdminLocalState.password_input,
                                    on_change=AdminLocalState.set_password_input,
                                    on_key_down=AdminLocalState.login_on_enter,
                                    type=rx.cond(
                                        AdminLocalState.show_password,
                                        "text",
                                        "password",
                                    ),
                                    autocomplete="new-password",
                                    class_name="twk-login-input",
                                    padding_right="40px",
                                ),
                                rx.icon_button(
                                    rx.icon(
                                        tag=rx.cond(
                                            AdminLocalState.show_password,
                                            "eye_off",
                                            "eye",
                                        ),
                                        size=15,
                                    ),
                                    on_click=AdminLocalState.toggle_show_password,
                                    type="button",
                                    background="transparent",
                                    color="#64748B",
                                    border="none",
                                    width="26px",
                                    height="26px",
                                    _hover={"background": "rgba(255,255,255,0.06)",
                                            "color": "#FFFFFF"},
                                    position="absolute",
                                    right="6px",
                                    top="50%",
                                    transform="translateY(-50%)",
                                    cursor="pointer",
                                ),
                                position="relative",
                                width="100%",
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
                        spacing="4", width="100%",
                    ),
                    background="#1E293B",
                    border="1px solid #334155",
                    border_radius="20px",
                    padding="32px 28px",
                    box_shadow="0 20px 60px rgba(0,0,0,0.4)",
                    width="100%",
                ),
                rx.center(
                    rx.hstack(
                        rx.text("¿Sos empleado?", font_size="12px", color="#475569"),
                        rx.link(
                            "Ingresar con PIN",
                            href="/login?empresa=" + AdminLocalState.login_empresa_slug,
                            font_size="12px", color=_ORANGE, font_weight="600",
                            _hover={"color": _ORANGE_DK},
                        ),
                        spacing="1",
                    ),
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
