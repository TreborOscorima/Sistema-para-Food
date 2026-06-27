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

# ── Colores del sistema ───────────────────────────────────────────────────────
_ORANGE     = "#EA580C"
_ORANGE_DK  = "#C2410C"
_ORANGE_LT  = "#FFF7ED"
_ORANGE_BD  = "#FED7AA"
_SLATE_900  = "#0F172A"
_SLATE_700  = "#334155"
_SLATE_500  = "#64748B"
_SLATE_200  = "#E2E8F0"
_SLATE_100  = "#F1F5F9"
_SLATE_50   = "#F8FAFC"
_WHITE      = "#FFFFFF"
_GREEN      = "#15803D"
_GREEN_LT   = "#F0FDF4"
_BLUE       = "#1D4ED8"
_BLUE_LT    = "#EFF6FF"


# ── Shell ─────────────────────────────────────────────────────────────────────

def _dono_shell(content: rx.Component) -> rx.Component:
    return rx.box(
        rx.script(_CSS_SCRIPT),
        rx.vstack(
            # ── Topbar ────────────────────────────────────────────────────────
            rx.hstack(
                # Logo
                rx.hstack(
                    rx.image(
                        src="/TUWAYKIFOOD.png",
                        height="36px",
                        width="auto",
                        alt="TUWAYKIFOOD",
                    ),
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
                        rx.text(
                            "Salir",
                            font_size="13px",
                            font_weight="600",
                            color=_SLATE_500,
                            display=rx.breakpoints(initial="none", sm="block"),
                        ),
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
            ),
            # ── Contenido ─────────────────────────────────────────────────────
            rx.box(
                content,
                padding=rx.breakpoints(initial="16px", sm="20px", lg="28px 32px"),
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

@rx.page(route="/dono/login", on_load=AdminLocalState.on_load_dono_login, title="TUWAYKIFOOD | Acceso Administrativo")
def dono_login_page() -> rx.Component:
    return rx.box(
        rx.script(_CSS_SCRIPT),
        rx.center(
            rx.vstack(
                # Logo + header
                rx.vstack(
                    rx.image(
                        src="/TUWAYKIFOOD.png",
                        height="110px",
                        width="auto",
                        alt="TUWAYKIFOOD",
                    ),
                    rx.vstack(
                        rx.text(
                            "Panel Administrativo",
                            font_size="22px",
                            font_weight="800",
                            color=_SLATE_900,
                            text_align="center",
                        ),
                        rx.text(
                            "Ingresa con tu email y contraseña",
                            font_size="13px",
                            color=_SLATE_500,
                            text_align="center",
                        ),
                        spacing="1",
                        align="center",
                    ),
                    spacing="3",
                    align="center",
                ),
                # Card de formulario
                rx.box(
                    rx.vstack(
                        # Error
                        rx.cond(
                            AdminLocalState.error_msg != "",
                            rx.box(
                                rx.hstack(
                                    rx.icon(tag="circle_alert", size=14, color="#B91C1C"),
                                    rx.text(AdminLocalState.error_msg, font_size="13px", color="#B91C1C", font_weight="600"),
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
                        # Script para desactivar autofill de Chrome post-render
                        rx.script("""
(function(){
  function patchAC(){
    var inputs = document.querySelectorAll('input[type="text"], input[type="password"]');
    inputs.forEach(function(el){
      el.setAttribute('autocomplete','off');
      el.setAttribute('readonly','');
    });
    setTimeout(function(){
      inputs.forEach(function(el){ el.removeAttribute('readonly'); });
    }, 300);
  }
  setTimeout(patchAC, 500);
  setTimeout(patchAC, 1500);
})();
"""),
                        # Email
                        rx.vstack(
                            rx.text("Email", font_size="12px", font_weight="700", color=_SLATE_700),
                            rx.input(
                                placeholder="dueño@restaurante.com",
                                value=AdminLocalState.email_input,
                                on_change=AdminLocalState.set_email_input,
                                type="text",
                                auto_complete=False,
                                background=_WHITE,
                                border=f"1px solid {_SLATE_200}",
                                color=_SLATE_900,
                                border_radius="8px",
                                padding_x="14px",
                                padding_y="11px",
                                font_size="14px",
                                width="100%",
                                _focus={"border": f"1px solid {_ORANGE}", "box_shadow": "0 0 0 3px rgba(234,88,12,0.12)"},
                            ),
                            spacing="1",
                            width="100%",
                            align="start",
                        ),
                        # Contraseña
                        rx.vstack(
                            rx.text("Contraseña", font_size="12px", font_weight="700", color=_SLATE_700),
                            rx.input(
                                placeholder="••••••••",
                                value=AdminLocalState.password_input,
                                on_change=AdminLocalState.set_password_input,
                                type="password",
                                auto_complete=False,
                                background=_WHITE,
                                border=f"1px solid {_SLATE_200}",
                                color=_SLATE_900,
                                border_radius="8px",
                                padding_x="14px",
                                padding_y="11px",
                                font_size="14px",
                                width="100%",
                                _focus={"border": f"1px solid {_ORANGE}", "box_shadow": "0 0 0 3px rgba(234,88,12,0.12)"},
                            ),
                            spacing="1",
                            width="100%",
                            align="start",
                        ),
                        # Botón
                        rx.button(
                            "Ingresar al Panel",
                            on_click=AdminLocalState.login_admin_local,
                            background=_ORANGE,
                            color=_WHITE,
                            border_radius="8px",
                            font_size="14px",
                            font_weight="700",
                            width="100%",
                            padding_y="12px",
                            cursor="pointer",
                            _hover={"background": _ORANGE_DK},
                            box_shadow="0 2px 8px rgba(234,88,12,0.25)",
                        ),
                        # Link volver
                        rx.center(
                            rx.link(
                                "← Volver al sistema (login con PIN)",
                                href="/login",
                                font_size="12px",
                                color=_SLATE_500,
                                _hover={"color": _ORANGE},
                            ),
                            width="100%",
                        ),
                        spacing="4",
                        width="100%",
                    ),
                    background=_WHITE,
                    border=f"1px solid {_SLATE_200}",
                    border_radius="16px",
                    padding="32px 28px",
                    box_shadow="0 8px 32px rgba(0,0,0,0.08)",
                    width="100%",
                ),
                spacing="6",
                align="center",
                width="100%",
                max_width="400px",
            ),
            min_height="100vh",
            background=_SLATE_50,
            padding="24px 16px",
        ),
    )


# ── KPI card ──────────────────────────────────────────────────────────────────

def _dono_kpi(label: str, value, icon: str, accent: str, bg: str) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.box(
                    rx.icon(tag=icon, size=18, color=accent),
                    width="40px",
                    height="40px",
                    border_radius="10px",
                    background=bg,
                    display="flex",
                    align_items="center",
                    justify_content="center",
                    flex_shrink="0",
                ),
                rx.spacer(),
            ),
            rx.text(
                value,
                font_size="26px",
                font_weight="800",
                color=_SLATE_900,
                line_height="1",
                margin_top="4px",
            ),
            rx.text(
                label,
                font_size="11px",
                font_weight="600",
                color=_SLATE_500,
                text_transform="uppercase",
                letter_spacing="0.05em",
            ),
            spacing="2",
            align="start",
            width="100%",
        ),
        background=_WHITE,
        border=f"1px solid {_SLATE_200}",
        border_radius="14px",
        padding="18px 20px",
        box_shadow="0 1px 4px rgba(0,0,0,0.06)",
        flex="1",
        min_width="0",
    )


# ── Fila de venta ─────────────────────────────────────────────────────────────

def _dono_ventas_row(venta) -> rx.Component:
    return rx.hstack(
        rx.text(
            "#" + venta.pedido_id.to_string(),
            font_size="11px",
            color=_SLATE_500,
            min_width="32px",
            flex_shrink="0",
        ),
        rx.text(
            venta.mesa_label,
            font_size="13px",
            color=_SLATE_700,
            flex="1",
            text_overflow="ellipsis",
            overflow="hidden",
            white_space="nowrap",
        ),
        rx.badge(
            venta.metodo_pago,
            background=rx.cond(
                venta.metodo_pago == "efectivo", "#DCFCE7",
                rx.cond(venta.metodo_pago == "tarjeta", "#DBEAFE",
                rx.cond(venta.metodo_pago == "qr", "#FEF3C7",
                rx.cond(venta.metodo_pago == "fiado", "#FFEDD5", _SLATE_100))),
            ),
            color=rx.cond(
                venta.metodo_pago == "efectivo", _GREEN,
                rx.cond(venta.metodo_pago == "tarjeta", _BLUE,
                rx.cond(venta.metodo_pago == "qr", "#B45309",
                rx.cond(venta.metodo_pago == "fiado", _ORANGE_DK, _SLATE_500))),
            ),
            border_radius="5px",
            font_size="10px",
            font_weight="700",
            padding="2px 6px",
            flex_shrink="0",
        ),
        rx.text(
            venta.total_con_propina_texto,
            font_size="13px",
            font_weight="700",
            color=_GREEN,
            min_width="70px",
            text_align="right",
            flex_shrink="0",
        ),
        width="100%",
        align="center",
        padding="8px 10px",
        border_radius="8px",
        background=_WHITE,
        border=f"1px solid {_SLATE_100}",
        gap="8px",
        _hover={"background": _SLATE_50},
    )


# ── Sección ventas / KPIs ─────────────────────────────────────────────────────

def _dono_ventas_section() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.hstack(
                    rx.icon(tag="trending_up", size=16, color=_ORANGE),
                    rx.text("Ventas de hoy", font_size="15px", font_weight="700", color=_SLATE_900),
                    spacing="2",
                    align="center",
                ),
                rx.spacer(),
                rx.button(
                    rx.hstack(
                        rx.icon(tag="refresh_cw", size=13, color=_ORANGE),
                        rx.text("Actualizar", font_size="12px", font_weight="600", color=_ORANGE),
                        spacing="1",
                        align="center",
                    ),
                    on_click=[FoodState.cargar_dashboard, FoodState.cargar_historial_ventas],
                    background=_ORANGE_LT,
                    border=f"1px solid {_ORANGE_BD}",
                    border_radius="7px",
                    padding_x="12px",
                    padding_y="7px",
                    cursor="pointer",
                    _hover={"opacity": "0.85"},
                ),
                width="100%",
                align="center",
            ),
            # KPIs
            rx.flex(
                _dono_kpi("Ventas hoy", FoodState.dashboard_ventas_hoy_texto,
                          "trending_up", _GREEN, _GREEN_LT),
                _dono_kpi("Pedidos cobrados", FoodState.dashboard_pedidos_hoy.to_string(),
                          "receipt_text", _BLUE, _BLUE_LT),
                _dono_kpi("Propinas hoy", FoodState.dashboard_propina_hoy_texto,
                          "heart", "#9A3412", _ORANGE_LT),
                gap="12px",
                width="100%",
                flex_wrap="wrap",
            ),
            # Últimas ventas
            rx.cond(
                FoodState.historial_ventas.length() > 0,
                rx.vstack(
                    rx.hstack(
                        rx.text("Ultimas ventas", font_size="12px", font_weight="600", color=_SLATE_500),
                        rx.spacer(),
                        rx.link(
                            "Ver todas →",
                            href="/reportes",
                            font_size="11px",
                            color=_ORANGE,
                            font_weight="600",
                            _hover={"opacity": "0.8"},
                        ),
                        width="100%",
                        align="center",
                    ),
                    rx.vstack(
                        rx.foreach(FoodState.historial_ventas, _dono_ventas_row),
                        spacing="1",
                        width="100%",
                    ),
                    spacing="2",
                    width="100%",
                ),
                rx.center(
                    rx.vstack(
                        rx.icon(tag="receipt_text", size=28, color=_SLATE_200),
                        rx.text("Sin ventas hoy.", font_size="13px", color=_SLATE_500),
                        spacing="2",
                        align="center",
                    ),
                    padding_y="20px",
                    width="100%",
                ),
            ),
            spacing="4",
            width="100%",
        ),
        background=_WHITE,
        border=f"1px solid {_SLATE_200}",
        border_radius="16px",
        padding="20px",
        width="100%",
        box_shadow="0 1px 4px rgba(0,0,0,0.06)",
    )


# ── Quick links ───────────────────────────────────────────────────────────────

def _quick_link(label: str, desc: str, icon: str, href: str, accent: str = _ORANGE) -> rx.Component:
    return rx.link(
        rx.hstack(
            rx.box(
                rx.icon(tag=icon, size=16, color=accent),
                width="36px",
                height="36px",
                border_radius="9px",
                background=_ORANGE_LT,
                border=f"1px solid {_ORANGE_BD}",
                display="flex",
                align_items="center",
                justify_content="center",
                flex_shrink="0",
            ),
            rx.vstack(
                rx.text(label, font_size="13px", font_weight="700", color=_SLATE_900),
                rx.text(desc, font_size="11px", color=_SLATE_500, line_height="1.3"),
                spacing="0",
                align="start",
            ),
            rx.spacer(),
            rx.icon(tag="arrow_right", size=14, color=_SLATE_200),
            spacing="3",
            align="center",
            width="100%",
        ),
        href=href,
        background=_WHITE,
        border=f"1px solid {_SLATE_200}",
        border_radius="12px",
        padding="12px 14px",
        text_decoration="none",
        _hover={"border": f"1px solid {_ORANGE_BD}", "background": _ORANGE_LT, "transform": "translateX(2px)"},
        transition="all 0.15s ease",
        width="100%",
        display="block",
    )


def _quick_links_section() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.icon(tag="layout_grid", size=14, color=_SLATE_500),
                rx.text("Acceso rapido", font_size="13px", font_weight="700", color=_SLATE_700),
                spacing="2",
                align="center",
            ),
            rx.grid(
                _quick_link("Clientes", "Cumpleanos y fidelizacion", "users", "/clientes"),
                _quick_link("Fiado", "Cuentas corrientes", "credit_card", "/cuentas"),
                _quick_link("Promociones", "Happy hour y descuentos", "tag", "/promociones"),
                _quick_link("Inventario", "Insumos, recetas y stock", "package", "/inventario"),
                columns=rx.breakpoints(initial="1", sm="2"),
                gap="10px",
                width="100%",
            ),
            spacing="3",
            width="100%",
        ),
        background=_WHITE,
        border=f"1px solid {_SLATE_200}",
        border_radius="16px",
        padding="18px 20px",
        width="100%",
        box_shadow="0 1px 4px rgba(0,0,0,0.06)",
    )


# ── Alertas ───────────────────────────────────────────────────────────────────

def _alertas_section() -> rx.Component:
    return rx.vstack(
        # Cumpleaños
        rx.cond(
            FoodState.clientes_cumpleanos_hoy.length() > 0,
            rx.box(
                rx.hstack(
                    rx.box(
                        rx.icon(tag="cake", size=16, color="#B45309"),
                        width="36px",
                        height="36px",
                        border_radius="9px",
                        background="#FFFBEB",
                        border="1px solid #FDE68A",
                        display="flex",
                        align_items="center",
                        justify_content="center",
                        flex_shrink="0",
                    ),
                    rx.vstack(
                        rx.text("Cumpleanos hoy", font_size="12px", font_weight="700", color=_SLATE_900),
                        rx.foreach(
                            FoodState.clientes_cumpleanos_hoy,
                            lambda c: rx.text(
                                c.nombre + rx.cond(c.telefono != "", " · " + c.telefono, ""),
                                font_size="11px",
                                color="#78350F",
                            ),
                        ),
                        spacing="0",
                        align="start",
                    ),
                    rx.spacer(),
                    rx.link(
                        rx.hstack(
                            rx.text("Ver", font_size="11px", font_weight="700", color=_ORANGE),
                            rx.icon(tag="arrow_right", size=11, color=_ORANGE),
                            spacing="1",
                            align="center",
                        ),
                        href="/clientes",
                    ),
                    width="100%",
                    align="center",
                    gap="12px",
                ),
                background="#FFFBEB",
                border="1px solid #FDE68A",
                border_radius="12px",
                padding="14px 16px",
                width="100%",
            ),
            rx.fragment(),
        ),
        # Stock bajo
        rx.cond(
            FoodState.inv_alertas_bajo_stock.length() > 0,
            rx.box(
                rx.hstack(
                    rx.box(
                        rx.icon(tag="triangle_alert", size=16, color="#B45309"),
                        width="36px",
                        height="36px",
                        border_radius="9px",
                        background="#FFFBEB",
                        border="1px solid #FDE68A",
                        display="flex",
                        align_items="center",
                        justify_content="center",
                        flex_shrink="0",
                    ),
                    rx.vstack(
                        rx.text("Stock bajo", font_size="12px", font_weight="700", color=_SLATE_900),
                        rx.text(
                            FoodState.inv_alertas_bajo_stock_texto,
                            font_size="11px",
                            color="#92400E",
                        ),
                        spacing="0",
                        align="start",
                    ),
                    rx.spacer(),
                    rx.link(
                        rx.hstack(
                            rx.text("Inventario", font_size="11px", font_weight="700", color=_ORANGE),
                            rx.icon(tag="arrow_right", size=11, color=_ORANGE),
                            spacing="1",
                            align="center",
                        ),
                        href="/inventario",
                    ),
                    width="100%",
                    align="center",
                    gap="12px",
                ),
                background="#FFFBEB",
                border="1px solid #FDE68A",
                border_radius="12px",
                padding="14px 16px",
                width="100%",
            ),
            rx.fragment(),
        ),
        spacing="2",
        width="100%",
    )


# ── Panel de configuracion ────────────────────────────────────────────────────

def _config_panel() -> rx.Component:
    return rx.vstack(
        # Nombre del local
        rx.box(
            rx.vstack(
                _section_header("Nombre del local", "store"),
                _field_row(
                    "Nombre",
                    FoodState.config_nombre_local,
                    FoodState.set_config_nombre_local,
                    "Mi Restaurante",
                ),
                rx.button(
                    "Guardar nombre",
                    on_click=FoodState.guardar_config_impresora,
                    background=_ORANGE,
                    color=_WHITE,
                    border_radius="8px",
                    font_size="13px",
                    font_weight="700",
                    cursor="pointer",
                    _hover={"background": _ORANGE_DK},
                    align_self="end",
                ),
                spacing="4",
                width="100%",
            ),
            background=_WHITE,
            border=f"1px solid {_SLATE_200}",
            border_radius="16px",
            padding="20px",
            width="100%",
            box_shadow="0 1px 4px rgba(0,0,0,0.06)",
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


# ── Dashboard del dueño ───────────────────────────────────────────────────────

def _dono_config_content() -> rx.Component:
    return rx.vstack(
        # Encabezado de pagina
        rx.hstack(
            rx.vstack(
                rx.text(
                    "Panel Administrativo",
                    font_size=rx.breakpoints(initial="20px", md="24px"),
                    font_weight="800",
                    color=_SLATE_900,
                    line_height="1",
                ),
                rx.text(
                    "Gestion y configuracion del local",
                    font_size="13px",
                    color=_SLATE_500,
                ),
                spacing="1",
                align="start",
            ),
            rx.spacer(),
            width="100%",
            align="center",
        ),
        # Mensaje de exito
        rx.cond(
            FoodState.mensaje != "",
            rx.box(
                rx.hstack(
                    rx.icon(tag="check_circle", size=14, color=_GREEN),
                    rx.text(FoodState.mensaje, font_size="13px", color=_GREEN, font_weight="600"),
                    spacing="2",
                    align="center",
                ),
                background=_GREEN_LT,
                border="1px solid #BBF7D0",
                border_radius="10px",
                padding="10px 16px",
                width="100%",
            ),
            rx.fragment(),
        ),
        # Layout dos columnas: operativo | configuracion
        rx.flex(
            # ── Columna izquierda: Dashboard operativo ──────────────────────
            rx.vstack(
                _dono_ventas_section(),
                _alertas_section(),
                _quick_links_section(),
                spacing="4",
                width="100%",
                class_name="twk-panel",
            ),
            # ── Columna derecha: Configuracion ──────────────────────────────
            rx.vstack(
                _config_panel(),
                spacing="4",
                width="100%",
                class_name="twk-panel",
            ),
            class_name="twk-cols-lg",
            gap="20px",
            width="100%",
            align_items="flex-start",
        ),
        spacing="5",
        width="100%",
    )


@rx.page(
    route="/dono",
    on_load=[AdminLocalState.on_load_dono, FoodState.on_load_dono_page],
    title="TUWAYKIFOOD | Panel Administrativo",
)
def dono_page() -> rx.Component:
    return _dono_shell(_dono_config_content())
