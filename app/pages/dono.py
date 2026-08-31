"""Panel Administrativo del dueño — dashboard con sub-módulos navegables."""

from __future__ import annotations

import reflex as rx

from app.states.food_state import AdminLocalState, FoodState
from app.states.dono_state import DeliveryPedidoView, DonoOperacionesState, ReservaView
from app.states.reportes_state import ReportesState
from app.components.upgrade import upgrade_cta
from app.components.shared import _connection_banner_es, color_mode_toggle
from app.components.modulos import MODULOS as _M
from app.components.theme import (
    ACCENT as _ORANGE,
    ACCENT_HOVER as _ORANGE_DK,
    ACCENT_BG as _ORANGE_LT,
    ACCENT_MUTED as _ORANGE_BD,
    DARK_900 as _SLATE_900,
    DARK_700 as _SLATE_700,
    SLATE_500 as _SLATE_500,
    BORDER_COLOR as _SLATE_200,
    SURFACE_BASE as _SLATE_100,
    PAGE_BACKGROUND as _SLATE_50,
    TEXT_WHITE as _WHITE,
    SURFACE_BASE as _SURFACE,
    SUCCESS_TEXT as _GREEN,
    SUCCESS_BG as _GREEN_LT,
    INFO_TEXT as _BLUE,
    INFO_BG as _BLUE_LT,
    WARNING_TEXT as _AMBER,
    WARNING_BG as _AMBER_LT,
    WARNING_BORDER as _AMBER_BD,
    WARNING_SOLID as _WARN_SOLID,
    DARK_800 as _SLATE_800,
    TEXT_PRIMARY as _TEXT,
    SUCCESS_SOLID as _GREEN_SOLID,
    DANGER_SOLID as _RED,
    INFO_SOLID as _BLUE_SOLID,
    PURPLE as _PURPLE,
)


# ── Estado local para sub-módulo activo ───────────────────────────────────────

class AdminPanelState(rx.State):
    seccion: str = "resumen"
    sidebar_open: bool = True

    async def ir_a(self, s: str) -> None:
        self.seccion = s
        food_state = await self.get_state(FoodState)
        food_state._cargar_plan_empresa()
        if s in ("reservas", "delivery"):
            dono_state = await self.get_state(DonoOperacionesState)
            await dono_state._sync_tenant()
            if s == "reservas":
                dono_state.cargar_reservas()
            else:
                dono_state.cargar_deliveries()
        elif s == "usuarios":
            # La lista de usuarios no tiene on_load propio dentro del SPA del
            # panel: sin esto, la sección abría vacía ("No hay usuarios") hasta
            # la primera escritura. Cargamos al navegar.
            from app.states.usuarios_state import UsuariosAdminState
            usuarios_state = await self.get_state(UsuariosAdminState)
            await usuarios_state.cargar_usuarios_admin()

    def toggle_sidebar(self) -> None:
        self.sidebar_open = not self.sidebar_open

    def cerrar_sidebar(self) -> None:
        self.sidebar_open = False

    promo_tab: str = "automaticas"

    def set_promo_tab(self, tab: str) -> None:
        self.promo_tab = tab


# ── Topbar del shell ──────────────────────────────────────────────────────────

def _dono_topbar(show_hamburger: bool = False) -> rx.Component:
    return rx.hstack(
        rx.button(
            rx.icon(tag="panel_left", size=18, color="var(--twk-slate-300)"),
            on_click=AdminPanelState.toggle_sidebar,
            background="transparent",
            border="none",
            border_radius="8px",
            padding="6px",
            min_width="0",
            cursor="pointer",
            _hover={"background": _SLATE_700},
            aria_label="Abrir/cerrar menú",
        ) if show_hamburger else rx.fragment(),
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
            rx.badge(
                rx.text(rx.icon(tag=FoodState.empresa_plan_icon, size=10), " ",
                        FoodState.empresa_plan_label,
                        display="inline-flex", align_items="center", gap="3px"),
                background=rx.cond(
                    FoodState.empresa_plan == "profesional",
                    "rgba(59,130,246,0.12)", rx.cond(
                        FoodState.empresa_plan == "trial",
                        _AMBER_LT, _TEXT,
                    ),
                ),
                color=rx.cond(
                    FoodState.empresa_plan == "profesional",
                    "var(--twk-info-text)", rx.cond(
                        FoodState.empresa_plan == "trial",
                        _AMBER, _SLATE_500,
                    ),
                ),
                border=rx.cond(
                    FoodState.empresa_plan == "profesional",
                    "1px solid #93C5FD", rx.cond(
                        FoodState.empresa_plan == "trial",
                        f"1px solid {_AMBER_BD}", "1px solid var(--twk-slate-300)",
                    ),
                ),
                border_radius="6px",
                font_size="10px",
                font_weight="700",
                padding="3px 8px",
            ),
            spacing="3",
            align="center",
        ),
        rx.spacer(),
        color_mode_toggle(on_sidebar=False, size=34),
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
            _hover={"background": _SLATE_700},
        ),
        width="100%",
        align="center",
        padding=rx.breakpoints(initial="0 16px", md="0 28px"),
        height="60px",
        background=_SURFACE,
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
                        color=rx.cond(active, _ORANGE, "var(--twk-slate-200)")),
                width="34px", height="34px",
                border_radius="9px",
                background=rx.cond(active, _ORANGE_LT, _SLATE_800),
                border=rx.cond(active, f"1px solid {_ORANGE_BD}",
                               "1px solid transparent"),
                display="flex", align_items="center",
                justify_content="center", flex_shrink="0",
            ),
            # Texto — se oculta cuando el sidebar está colapsado
            rx.cond(
                AdminPanelState.sidebar_open,
                rx.vstack(
                    rx.text(label, font_size="13px",
                            font_weight="600",
                            color=rx.cond(active, _ORANGE, "var(--twk-sb-tx-strong)"),
                            line_height="1"),
                    rx.text(desc, font_size="11px",
                            font_weight="500",
                            color=rx.cond(active, "var(--twk-slate-200)", _SLATE_500),
                            line_height="1"),
                    spacing="1", align="start",
                ),
                rx.fragment(),
            ),
            spacing="3",
            align="center",
            width="100%",
            justify_content=rx.cond(AdminPanelState.sidebar_open, "flex-start", "center"),
        ),
        padding=rx.cond(AdminPanelState.sidebar_open, "10px 12px", "10px 4px"),
        border_radius="10px",
        background=rx.cond(active, _SURFACE, "transparent"),
        border=rx.cond(active, f"1px solid {_ORANGE_BD}",
                       "1px solid transparent"),
        box_shadow=rx.cond(active, "0 1px 4px rgba(234,88,12,0.1)", "none"),
        cursor="pointer",
        on_click=AdminPanelState.ir_a(key),
        title=label,
        width="100%",
        overflow="hidden",
        transition="all 0.12s ease",
        _hover={
            "background": rx.cond(active, _SURFACE, _SLATE_700),
            "border": rx.cond(active, f"1px solid {_ORANGE_BD}",
                              f"1px solid {_SLATE_200}"),
        },
    )


def _admin_group_label(text: str) -> rx.Component:
    """Encabezado de grupo del sidebar del dono (T-07). Cuando el sidebar está
    colapsado se reemplaza por un pequeño espacio que separa los grupos."""
    return rx.cond(
        AdminPanelState.sidebar_open,
        rx.text(text, font_size="10px", font_weight="700",
                color=_SLATE_500, text_transform="uppercase",
                letter_spacing="0.08em", padding_x="4px",
                padding_top="10px", padding_bottom="2px"),
        rx.box(height="10px", width="100%"),
    )


def _admin_sidebar() -> rx.Component:
    return rx.box(
        rx.vstack(
            _admin_group_label("Análisis"),
            _admin_nav_item("resumen", "Resumen", "layout_dashboard", "Vista general del día"),
            _admin_nav_item("ventas", _M["reportes"].label, _M["reportes"].icon, _M["reportes"].desc),
            # Catálogo — solo si algún módulo del grupo está activo para el plan.
            rx.cond(
                FoodState.plan_permite_inventario | FoodState.plan_permite_promociones,
                _admin_group_label("Catálogo"),
                rx.fragment(),
            ),
            rx.cond(
                FoodState.plan_permite_inventario,
                _admin_nav_item("inventario", _M["inventario"].label, _M["inventario"].icon, _M["inventario"].desc),
                rx.fragment(),
            ),
            rx.cond(
                FoodState.plan_permite_promociones,
                _admin_nav_item("promociones", _M["promociones"].label, _M["promociones"].icon, _M["promociones"].desc),
                rx.fragment(),
            ),
            # Clientes — grupo premium; se oculta entero si ningún módulo aplica.
            rx.cond(
                FoodState.plan_permite_clientes | FoodState.plan_permite_cuentas,
                _admin_group_label("Clientes"),
                rx.fragment(),
            ),
            rx.cond(
                FoodState.plan_permite_clientes,
                _admin_nav_item("clientes", _M["clientes"].label, _M["clientes"].icon, _M["clientes"].desc),
                rx.fragment(),
            ),
            rx.cond(
                FoodState.plan_permite_cuentas,
                _admin_nav_item("cuentas", _M["cuentas"].label, _M["cuentas"].icon, _M["cuentas"].desc),
                rx.fragment(),
            ),
            # Canales de venta — módulos "próximamente"; se muestran al activarlos.
            rx.cond(
                FoodState.plan_permite_reservas | FoodState.plan_permite_delivery,
                _admin_group_label("Canales de venta"),
                rx.fragment(),
            ),
            rx.cond(
                FoodState.plan_permite_reservas,
                _admin_nav_item("reservas", _M["reservas"].label, _M["reservas"].icon, _M["reservas"].desc),
                rx.fragment(),
            ),
            rx.cond(
                FoodState.plan_permite_delivery,
                _admin_nav_item("delivery", _M["delivery"].label, _M["delivery"].icon, _M["delivery"].desc),
                rx.fragment(),
            ),
            _admin_group_label("Sistema"),
            _admin_nav_item("usuarios", _M["usuarios"].label, _M["usuarios"].icon, _M["usuarios"].desc),
            _admin_nav_item("config", _M["config"].label, _M["config"].icon, _M["config"].desc),
            spacing="1", width="100%", align="start",
        ),
        padding=rx.cond(AdminPanelState.sidebar_open, "12px", "8px 6px"),
        class_name=rx.cond(AdminPanelState.sidebar_open, "twk-admin-sb open", "twk-admin-sb"),
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
        color=rx.cond(value >= 0, _GREEN, _RED),
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
            rx.text(value,
                    font_size=rx.breakpoints(initial="20px", sm="24px", md="26px"),
                    font_weight="800",
                    color=_TEXT, line_height="1", margin_top="4px"),
            rx.text(label, font_size="11px", font_weight="600",
                    color=_SLATE_500, text_transform="uppercase",
                    letter_spacing="0.05em"),
            trend if trend is not None else rx.fragment(),
            spacing="2", align="start", width="100%",
        ),
        background=_SURFACE, border=f"1px solid {_SLATE_200}",
        border_radius="14px",
        padding=rx.breakpoints(initial="14px 16px", md="18px 20px"),
        box_shadow="0 1px 4px rgba(0,0,0,0.06)", flex="1",
        min_width=rx.breakpoints(initial="140px", sm="160px"),
    )


def _venta_row(venta) -> rx.Component:
    return rx.hstack(
        rx.text("#" + venta.pedido_id.to_string(), font_size="11px",
                color=_SLATE_500, min_width="32px", flex_shrink="0"),
        rx.text(venta.mesa_label, font_size="13px", color="var(--twk-slate-300)",
                flex="1", text_overflow="ellipsis", overflow="hidden",
                white_space="nowrap"),
        rx.badge(
            venta.metodo_pago,
            background=rx.cond(
                venta.metodo_pago == "efectivo", "rgba(34,197,94,0.12)",
                rx.cond(venta.metodo_pago == "tarjeta", "rgba(59,130,246,0.12)",
                rx.cond(venta.metodo_pago == "qr", "rgba(245,158,11,0.12)",
                rx.cond(venta.metodo_pago == "fiado", "rgba(234,88,12,0.12)", _SLATE_100)))),
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
        background=_SURFACE, border=f"1px solid {_SLATE_100}",
        gap="8px", _hover={"background": _SLATE_700},
    )


def _top_plato_row(plato, index: int) -> rx.Component:
    max_cantidad = ReportesState.dashboard_top_platos[0].cantidad
    pct = rx.cond(
        max_cantidad > 0,
        (plato.cantidad * 100) / max_cantidad,
        0,
    )
    return rx.hstack(
        rx.box(
            rx.text((index + 1).to_string(), font_size="11px",
                    font_weight="800", color=_TEXT),
            width="24px", height="24px", border_radius="6px",
            background=rx.cond(
                index == 0, _ORANGE,
                rx.cond(index == 1, "#F97316",
                rx.cond(index == 2, "#FB923C", "var(--twk-slate-300)"))),
            display="flex", align_items="center", justify_content="center",
            flex_shrink="0",
        ),
        rx.vstack(
            rx.text(plato.nombre, font_size="13px", font_weight="600",
                    color=_TEXT, width="100%", overflow="hidden",
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
                    background="rgba(239,68,68,0.12)",
                    border="1px solid rgba(239,68,68,0.30)",
                    display="flex", align_items="center",
                    justify_content="center", flex_shrink="0",
                ),
                rx.vstack(
                    rx.text("Cumpleaños hoy", font_size="12px",
                            font_weight="700", color="var(--twk-danger-text)"),
                    rx.foreach(
                        FoodState.clientes_cumpleanos_hoy,
                        lambda c: rx.text(
                            c.nombre + rx.cond(c.telefono != "",
                                               " · " + c.telefono, ""),
                            font_size="11px", color="var(--twk-danger-text)",
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
            background="rgba(239,68,68,0.08)", border="1px solid rgba(239,68,68,0.30)",
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
                            font_weight="700", color=_TEXT),
                    rx.text(FoodState.inv_alertas_bajo_stock_texto,
                            font_size="11px", color=_AMBER),
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
                        color=_TEXT),
                rx.text(desc, font_size="11px", color=_SLATE_500,
                        line_height="1.3"),
                spacing="0", align="start",
            ),
            rx.spacer(),
            rx.icon(tag="arrow_right", size=14, color=_SLATE_200),
            spacing="3", align="center", width="100%",
        ),
        href=href,
        background=_SURFACE, border=f"1px solid {_SLATE_200}",
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

def _ob_paso(numero: int, label: str, done, href: str) -> rx.Component:
    return rx.hstack(
        rx.cond(
            done,
            rx.icon(tag="circle_check_big", size=20, color=_GREEN_SOLID),
            rx.box(
                rx.text(str(numero), font_size="12px", font_weight="800", color=_SLATE_500),
                min_width="22px", height="22px", border_radius="50%",
                border=f"2px solid {_SLATE_200}", display="flex",
                align_items="center", justify_content="center", flex_shrink="0",
            ),
        ),
        rx.text(
            label, font_size="13px", font_weight="600",
            color=rx.cond(done, _SLATE_500, _TEXT),
            text_decoration=rx.cond(done, "line-through", "none"),
        ),
        rx.spacer(),
        rx.cond(
            done,
            rx.fragment(),
            rx.link(
                rx.hstack(
                    rx.text("Configurar", font_size="12px", font_weight="700", color=_ORANGE),
                    rx.icon(tag="arrow_right", size=13, color=_ORANGE),
                    spacing="1", align="center",
                ),
                href=href, text_decoration="none", _hover={"opacity": "0.75"},
                flex_shrink="0",
            ),
        ),
        width="100%", align="center", spacing="3", padding_y="4px",
    )


def _onboarding_card() -> rx.Component:
    return rx.cond(
        FoodState.onboarding_visible,
        rx.box(
            rx.vstack(
                rx.hstack(
                    rx.box(
                        rx.icon(tag="rocket", size=18, color=_ORANGE),
                        min_width="34px", height="34px", border_radius="9px",
                        background=_ORANGE_LT, display="flex",
                        align_items="center", justify_content="center", flex_shrink="0",
                    ),
                    rx.vstack(
                        rx.text("Primeros pasos", font_size="15px", font_weight="800", color=_TEXT),
                        rx.text(
                            "Deja tu local listo — "
                            + FoodState.onboarding_pasos_ok.to_string()
                            + " de 5 completados",
                            font_size="12px", color=_SLATE_500,
                        ),
                        spacing="0", align="start",
                    ),
                    rx.spacer(),
                    rx.button(
                        "No mostrar más",
                        on_click=FoodState.descartar_onboarding,
                        background="transparent", color=_SLATE_500,
                        border=f"1px solid {_SLATE_200}", border_radius="7px",
                        font_size="11px", font_weight="600",
                        padding_x="10px", padding_y="5px", cursor="pointer",
                        _hover={"color": _TEXT, "border_color": _SLATE_500},
                        flex_shrink="0",
                    ),
                    width="100%", align="center", gap="10px", flex_wrap="wrap",
                ),
                rx.box(height="1px", width="100%", background=_SLATE_200),
                _ob_paso(1, "Ponle nombre a tu local", FoodState.ob_nombre_ok, "/configuracion"),
                _ob_paso(2, "Carga tu carta (categorías y productos)", FoodState.ob_carta_ok, "/carta"),
                _ob_paso(3, "Configura tus mesas y sectores", FoodState.ob_mesas_ok, "/configuracion"),
                _ob_paso(4, "Crea los usuarios y PINs de tu equipo", FoodState.ob_usuarios_ok, "/usuarios"),
                _ob_paso(5, "Configura la impresión (navegador o agente)", FoodState.ob_impresion_ok, "/configuracion"),
                _ob_paso(6, "Opcional: activa tu carta digital QR", FoodState.ob_qr_ok, "/configuracion"),
                spacing="2", width="100%",
            ),
            background=_SURFACE,
            border=f"1px solid {_ORANGE_BD}",
            border_left=f"3px solid {_ORANGE}",
            border_radius="14px",
            padding="16px 20px",
            width="100%",
            box_shadow="0 1px 3px rgba(0,0,0,0.06)",
        ),
        rx.fragment(),
    )


def _section_resumen() -> rx.Component:
    return rx.vstack(
        # Encabezado
        rx.hstack(
            rx.vstack(
                rx.text("Resumen del día", font_size="18px",
                        font_weight="800", color=_TEXT, line_height="1"),
                rx.text("Vista general de tu negocio hoy",
                        font_size="13px", color=_SLATE_500),
                spacing="1", align="start",
            ),
            rx.spacer(),
            rx.cond(
                FoodState.tiene_sucursales,
                rx.hstack(
                    rx.icon(tag="map_pin", size=13, color=_SLATE_500),
                    rx.button(
                        "Todas",
                        on_click=ReportesState.cambiar_sucursal_reportes("0"),
                        background=rx.cond(
                            ReportesState.reportes_sucursal_id == 0,
                            _ORANGE, _SURFACE,
                        ),
                        color=rx.cond(
                            ReportesState.reportes_sucursal_id == 0,
                            _WHITE, _SLATE_500,
                        ),
                        border=rx.cond(
                            ReportesState.reportes_sucursal_id == 0,
                            f"1px solid {_ORANGE}",
                            f"1px solid {_SLATE_200}",
                        ),
                        border_radius="7px", font_size="11px", font_weight="600",
                        padding_x="8px", padding_y="4px", cursor="pointer",
                    ),
                    rx.foreach(
                        FoodState.sucursales_empresa,
                        lambda s: rx.button(
                            s.nombre,
                            on_click=ReportesState.cambiar_sucursal_reportes(
                                s.id.to_string()
                            ),
                            background=rx.cond(
                                ReportesState.reportes_sucursal_id == s.id,
                                _ORANGE, _SURFACE,
                            ),
                            color=rx.cond(
                                ReportesState.reportes_sucursal_id == s.id,
                                _WHITE, _SLATE_500,
                            ),
                            border=rx.cond(
                                ReportesState.reportes_sucursal_id == s.id,
                                f"1px solid {_ORANGE}",
                                f"1px solid {_SLATE_200}",
                            ),
                            border_radius="7px", font_size="11px", font_weight="600",
                            padding_x="8px", padding_y="4px", cursor="pointer",
                        ),
                    ),
                    spacing="1", align="center", flex_wrap="wrap",
                ),
                rx.fragment(),
            ),
            rx.button(
                rx.hstack(
                    rx.icon(tag="refresh_cw", size=13, color=_ORANGE),
                    rx.text("Actualizar", font_size="12px",
                            font_weight="600", color=_ORANGE),
                    spacing="1", align="center",
                ),
                on_click=[ReportesState.cargar_dashboard,
                          ReportesState.cargar_historial_ventas],
                background=_ORANGE_LT, border=f"1px solid {_ORANGE_BD}",
                border_radius="7px", padding_x="12px", padding_y="7px",
                cursor="pointer", _hover={"opacity": "0.85"},
            ),
            width="100%", align="center",
        ),
        _onboarding_card(),
        # KPIs
        rx.flex(
            _kpi_card("Ventas hoy", ReportesState.dashboard_ventas_hoy_texto,
                      "trending_up", _GREEN, _GREEN_LT,
                      trend=_kpi_trend(ReportesState.dashboard_ventas_trend_pct)),
            _kpi_card("Pedidos cobrados",
                      ReportesState.dashboard_pedidos_hoy.to_string(),
                      "receipt_text", _BLUE, _BLUE_LT,
                      trend=_kpi_trend(ReportesState.dashboard_pedidos_trend, suffix="")),
            _kpi_card("Ticket promedio",
                      ReportesState.dashboard_ticket_promedio_texto,
                      "calculator", _PURPLE, "rgba(124,58,237,0.08)",
                      trend=_kpi_trend(ReportesState.dashboard_ticket_trend_pct)),
            _kpi_card("Propinas hoy",
                      ReportesState.dashboard_propina_hoy_texto,
                      "heart", _ORANGE, _ORANGE_LT,
                      trend=_kpi_trend(ReportesState.dashboard_propina_trend_pct)),
            gap="12px", width="100%", flex_wrap="wrap",
        ),
        # KPIs operativos en vivo
        rx.flex(
            _kpi_card("Mesas ocupadas",
                      ReportesState.dashboard_mesas_ocupadas.to_string()
                      + " / " + ReportesState.dashboard_total_mesas.to_string(),
                      "armchair", _ORANGE, _ORANGE_LT),
            _kpi_card("En cocina",
                      ReportesState.dashboard_items_en_cocina.to_string() + " ítems",
                      "chef_hat", "#D97706", _AMBER_LT),
            _kpi_card("Reservas hoy",
                      ReportesState.dashboard_reservas_hoy.to_string(),
                      "calendar_clock", _PURPLE, "rgba(124,58,237,0.08)"),
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
                                font_weight="700", color="var(--twk-slate-300)"),
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
                        ReportesState.historial_ventas.length() == 0,
                        rx.center(
                            rx.text("Sin ventas todavía", font_size="12px",
                                    color=_SLATE_500),
                            padding_y="24px", width="100%",
                        ),
                        rx.vstack(
                            rx.foreach(
                                ReportesState.historial_ventas_recientes,
                                _venta_row,
                            ),
                            spacing="2", width="100%",
                        ),
                    ),
                    spacing="3", width="100%",
                ),
                background=_SURFACE, border=f"1px solid {_SLATE_200}",
                border_radius="16px", padding="18px 20px",
                width="100%", box_shadow="0 1px 4px rgba(0,0,0,0.06)",
            ),
            rx.vstack(
                # Accesos operativos
                rx.box(
                    rx.vstack(
                        rx.text("Accesos operativos", font_size="13px",
                                font_weight="700", color="var(--twk-slate-300)"),
                        rx.grid(
                            _quick_link_card(_M["mozos"].label, _M["mozos"].desc,
                                             _M["mozos"].icon, "/mozos", "🧑‍🍳"),
                            # El acceso a Cocina se oculta si la empresa tiene la pantalla apagada.
                            rx.cond(
                                FoodState.puede_ver_cocina,
                                _quick_link_card(_M["cocina"].label, _M["cocina"].desc,
                                                 _M["cocina"].icon, "/cocina", "🍳"),
                                rx.fragment(),
                            ),
                            _quick_link_card(_M["caja"].label, _M["caja"].desc,
                                             _M["caja"].icon, "/caja", "🖥️"),
                            _quick_link_card(_M["mostrador"].label, _M["mostrador"].desc,
                                             _M["mostrador"].icon, "/mostrador", "🛍️"),
                            columns="1", gap="8px", width="100%",
                        ),
                        spacing="3", width="100%",
                    ),
                    background=_SURFACE, border=f"1px solid {_SLATE_200}",
                    border_radius="16px", padding="18px 20px",
                    width="100%", box_shadow="0 1px 4px rgba(0,0,0,0.06)",
                ),
                # Top platos hoy
                rx.box(
                    rx.vstack(
                        rx.text("Top platos hoy", font_size="13px",
                                font_weight="700", color="var(--twk-slate-300)"),
                        rx.cond(
                            ReportesState.dashboard_top_platos.length() == 0,
                            rx.center(
                                rx.text("Sin datos todavía", font_size="12px",
                                        color=_SLATE_500),
                                padding_y="16px", width="100%",
                            ),
                            rx.vstack(
                                rx.foreach(
                                    ReportesState.dashboard_top_platos,
                                    _top_plato_row,
                                ),
                                spacing="2", width="100%",
                            ),
                        ),
                        spacing="3", width="100%",
                    ),
                    background=_SURFACE, border=f"1px solid {_SLATE_200}",
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




# ── SECCIÓN: RESERVAS ────────────────────────────────────────────────────────

def _reserva_row(r: ReservaView) -> rx.Component:
    return rx.hstack(
        rx.vstack(
            rx.hstack(
                rx.text(r.nombre_cliente, font_size="14px", font_weight="700",
                        color=_TEXT, no_of_lines=1),
                rx.badge(
                    r.estado_label,
                    background=r.badge_bg,
                    color=r.badge_text,
                    border_radius="5px",
                    font_size="10px",
                    font_weight="700",
                    padding="2px 8px",
                ),
                spacing="2", align="center",
            ),
            rx.hstack(
                rx.cond(
                    r.mesa_label != "",
                    rx.hstack(
                        rx.icon(tag="armchair", size=12, color=_SLATE_500),
                        rx.text(r.mesa_label, font_size="12px", color=_SLATE_500),
                        spacing="1", align="center",
                    ),
                    rx.fragment(),
                ),
                rx.hstack(
                    rx.icon(tag="clock", size=12, color=_SLATE_500),
                    rx.text(r.hora, font_size="12px", font_weight="600",
                            color="var(--twk-slate-300)"),
                    spacing="1", align="center",
                ),
                rx.hstack(
                    rx.icon(tag="users", size=12, color=_SLATE_500),
                    rx.text(r.pax.to_string() + " pax", font_size="12px",
                            color=_SLATE_500),
                    spacing="1", align="center",
                ),
                rx.cond(
                    r.telefono != "",
                    rx.hstack(
                        rx.icon(tag="phone", size=12, color=_SLATE_500),
                        rx.text(r.telefono, font_size="12px", color=_SLATE_500),
                        spacing="1", align="center",
                    ),
                    rx.fragment(),
                ),
                spacing="3", align="center", flex_wrap="wrap",
            ),
            rx.cond(
                r.notas != "",
                rx.text(r.notas, font_size="11px", color=_SLATE_500,
                        font_style="italic", no_of_lines=1),
                rx.fragment(),
            ),
            spacing="1", align="start", flex="1", min_width="0",
        ),
        rx.hstack(
            rx.cond(
                r.estado == "pendiente",
                rx.tooltip(
                    rx.button(
                        rx.icon(tag="check", size=13),
                        on_click=DonoOperacionesState.confirmar_reserva(r.id),
                        background="rgba(34,197,94,0.12)", color=_GREEN_SOLID,
                        border="1px solid #BBF7D0", border_radius="7px",
                        padding="6px", cursor="pointer", height="auto",
                        _hover={"background": "rgba(34,197,94,0.25)"},
                    ),
                    content="Confirmar reserva",
                ),
                rx.fragment(),
            ),
            rx.cond(
                (r.estado == "pendiente") | (r.estado == "confirmada"),
                rx.tooltip(
                    rx.button(
                        rx.icon(tag="armchair", size=13),
                        on_click=DonoOperacionesState.sentar_reserva(r.id),
                        background="rgba(59,130,246,0.12)", color=_BLUE_SOLID,
                        border="1px solid #93C5FD", border_radius="7px",
                        padding="6px", cursor="pointer", height="auto",
                        _hover={"background": "#BFDBFE"},
                    ),
                    content="Sentar (marcar como presente)",
                ),
                rx.fragment(),
            ),
            rx.cond(
                (r.estado == "pendiente") | (r.estado == "confirmada"),
                rx.tooltip(
                    rx.button(
                        rx.icon(tag="user_x", size=13),
                        on_click=DonoOperacionesState.marcar_no_show(r.id),
                        background=_SLATE_100, color=_SLATE_500,
                        border=f"1px solid {_SLATE_200}", border_radius="7px",
                        padding="6px", cursor="pointer", height="auto",
                        _hover={"background": _SLATE_700},
                    ),
                    content="No asistió",
                ),
                rx.fragment(),
            ),
            rx.cond(
                (r.estado == "pendiente") | (r.estado == "confirmada"),
                rx.tooltip(
                    rx.button(
                        rx.icon(tag="x", size=13),
                        on_click=DonoOperacionesState.cancelar_reserva(r.id),
                        background="rgba(239,68,68,0.12)", color="var(--twk-danger-text)",
                        border="1px solid #FECACA", border_radius="7px",
                        padding="6px", cursor="pointer", height="auto",
                        _hover={"background": "rgba(239,68,68,0.25)"},
                    ),
                    content="Cancelar reserva",
                ),
                rx.fragment(),
            ),
            rx.tooltip(
                rx.button(
                    rx.icon(tag="pencil", size=13),
                    on_click=DonoOperacionesState.abrir_form_reserva(r.id),
                    background=_ORANGE_LT, color=_ORANGE,
                    border=f"1px solid {_ORANGE_BD}", border_radius="7px",
                    padding="6px", cursor="pointer", height="auto",
                    _hover={"background": _ORANGE_BD},
                ),
                content="Editar reserva",
            ),
            spacing="1", align="center", flex_shrink="0",
        ),
        width="100%", align="center",
        padding="12px 14px",
        background=_SURFACE,
        border=f"1px solid {_SLATE_200}",
        border_radius="10px",
        _hover={"border_color": _ORANGE_BD, "box_shadow": "0 1px 4px rgba(0,0,0,0.06)"},
        transition="all 0.12s ease",
    )


def _reserva_form_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.hstack(
                    rx.icon(tag="calendar_clock", size=18, color=_ORANGE),
                    rx.dialog.title(
                        rx.cond(DonoOperacionesState.reserva_form_id > 0,
                                "Editar reserva", "Nueva reserva"),
                        font_size="16px", font_weight="700", color=_TEXT, margin="0",
                    ),
                    rx.spacer(),
                    rx.dialog.close(
                        rx.box(
                            rx.icon(tag="x", size=16, color=_SLATE_500),
                            cursor="pointer", padding="4px",
                            border_radius="6px",
                            _hover={"background": _SLATE_700},
                        ),
                    ),
                    width="100%", align="center",
                ),
                rx.grid(
                    rx.vstack(
                        rx.text("Nombre *", font_size="11px", font_weight="600",
                                color=_SLATE_500, text_transform="uppercase",
                                letter_spacing="0.06em"),
                        rx.input(
                            value=DonoOperacionesState.reserva_form_nombre,
                            on_change=DonoOperacionesState.on_change_reserva_nombre,
                            placeholder="Nombre del cliente",
                            background=_SLATE_50,
                            border=f"1px solid {_SLATE_200}",
                            border_radius="8px",
                            color=_TEXT,
                            font_size="13px",
                            width="100%",
                            _focus={"border_color": _ORANGE},
                        ),
                        spacing="1", width="100%",
                    ),
                    rx.vstack(
                        rx.text("Teléfono", font_size="11px", font_weight="600",
                                color=_SLATE_500, text_transform="uppercase",
                                letter_spacing="0.06em"),
                        rx.input(
                            value=DonoOperacionesState.reserva_form_telefono,
                            on_change=DonoOperacionesState.on_change_reserva_telefono,
                            placeholder="999 999 999",
                            background=_SLATE_50,
                            border=f"1px solid {_SLATE_200}",
                            border_radius="8px",
                            color=_TEXT,
                            font_size="13px",
                            width="100%",
                            _focus={"border_color": _ORANGE},
                        ),
                        spacing="1", width="100%",
                    ),
                    columns="2", gap="12px", width="100%",
                ),
                rx.grid(
                    rx.vstack(
                        rx.text("Fecha *", font_size="11px", font_weight="600",
                                color=_SLATE_500, text_transform="uppercase",
                                letter_spacing="0.06em"),
                        rx.input(
                            value=DonoOperacionesState.reserva_form_fecha,
                            on_change=DonoOperacionesState.on_change_reserva_fecha,
                            type="date",
                            background=_SLATE_50,
                            border=f"1px solid {_SLATE_200}",
                            border_radius="8px",
                            color=_TEXT,
                            font_size="13px",
                            width="100%",
                            _focus={"border_color": _ORANGE},
                        ),
                        spacing="1", width="100%",
                    ),
                    rx.vstack(
                        rx.text("Hora *", font_size="11px", font_weight="600",
                                color=_SLATE_500, text_transform="uppercase",
                                letter_spacing="0.06em"),
                        rx.input(
                            value=DonoOperacionesState.reserva_form_hora,
                            on_change=DonoOperacionesState.on_change_reserva_hora,
                            type="time",
                            background=_SLATE_50,
                            border=f"1px solid {_SLATE_200}",
                            border_radius="8px",
                            color=_TEXT,
                            font_size="13px",
                            width="100%",
                            _focus={"border_color": _ORANGE},
                        ),
                        spacing="1", width="100%",
                    ),
                    rx.vstack(
                        rx.text("Personas", font_size="11px", font_weight="600",
                                color=_SLATE_500, text_transform="uppercase",
                                letter_spacing="0.06em"),
                        rx.input(
                            value=DonoOperacionesState.reserva_form_pax.to_string(),
                            on_change=DonoOperacionesState.on_change_reserva_pax,
                            type="number",
                            min="1",
                            background=_SLATE_50,
                            border=f"1px solid {_SLATE_200}",
                            border_radius="8px",
                            color=_TEXT,
                            font_size="13px",
                            width="100%",
                            _focus={"border_color": _ORANGE},
                        ),
                        spacing="1", width="100%",
                    ),
                    columns="3", gap="12px", width="100%",
                ),
                rx.vstack(
                    rx.text("Notas", font_size="11px", font_weight="600",
                            color=_SLATE_500, text_transform="uppercase",
                            letter_spacing="0.06em"),
                    rx.text_area(
                        value=DonoOperacionesState.reserva_form_notas,
                        on_change=DonoOperacionesState.on_change_reserva_notas,
                        placeholder="Notas adicionales (alergias, celebración, etc.)",
                        background=_SLATE_50,
                        border=f"1px solid {_SLATE_200}",
                        border_radius="8px",
                        color=_TEXT,
                        font_size="13px",
                        width="100%",
                        rows="2",
                        _focus={"border_color": _ORANGE},
                    ),
                    spacing="1", width="100%",
                ),
                rx.hstack(
                    rx.dialog.close(
                        rx.button(
                            "Cancelar",
                            background=_SLATE_100,
                            color="var(--twk-slate-300)",
                            border=f"1px solid {_SLATE_200}",
                            border_radius="8px",
                            font_size="13px",
                            font_weight="600",
                            cursor="pointer",
                            _hover={"background": _SLATE_700},
                        ),
                    ),
                    rx.button(
                        rx.cond(DonoOperacionesState.reserva_form_id > 0,
                                "Guardar cambios", "Crear reserva"),
                        on_click=DonoOperacionesState.guardar_reserva,
                        background=_ORANGE,
                        color=_WHITE,
                        border_radius="8px",
                        font_size="13px",
                        font_weight="700",
                        cursor="pointer",
                        _hover={"background": _ORANGE_DK},
                    ),
                    spacing="2", justify="end", width="100%",
                ),
                spacing="4", width="100%",
            ),
            background=_SURFACE,
            border=f"1px solid {_SLATE_200}",
            border_radius="16px",
            padding="24px",
            max_width="520px",
            width="90vw",
            max_height="90vh",
            overflow_y="auto",
        ),
        open=DonoOperacionesState.reserva_form_visible,
        on_open_change=DonoOperacionesState.set_reserva_form_visible,
    )


def _delivery_row(d: DeliveryPedidoView) -> rx.Component:
    return rx.hstack(
        rx.vstack(
            rx.hstack(
                rx.text(d.nombre_cliente, font_size="14px", font_weight="700",
                        color=_TEXT, no_of_lines=1),
                rx.badge(
                    d.delivery_estado_label,
                    background=d.badge_bg,
                    color=d.badge_text,
                    border_radius="5px",
                    font_size="10px",
                    font_weight="700",
                    padding="2px 8px",
                ),
                rx.cond(
                    d.pagado,
                    rx.badge("Pagado", background="rgba(34,197,94,0.12)", color=_GREEN_SOLID,
                             border_radius="5px", font_size="10px",
                             font_weight="700", padding="2px 8px"),
                    rx.fragment(),
                ),
                spacing="2", align="center",
            ),
            rx.hstack(
                rx.hstack(
                    rx.icon(tag="map_pin", size=12, color=_SLATE_500),
                    rx.text(d.delivery_direccion, font_size="12px",
                            color="var(--twk-slate-300)", no_of_lines=1),
                    spacing="1", align="center",
                ),
                rx.cond(
                    d.delivery_telefono != "",
                    rx.hstack(
                        rx.icon(tag="phone", size=12, color=_SLATE_500),
                        rx.text(d.delivery_telefono, font_size="12px",
                                color=_SLATE_500),
                        spacing="1", align="center",
                    ),
                    rx.fragment(),
                ),
                rx.hstack(
                    rx.icon(tag="clock", size=12, color=_SLATE_500),
                    rx.text(d.hora_texto, font_size="12px", font_weight="600",
                            color="var(--twk-slate-300)"),
                    spacing="1", align="center",
                ),
                spacing="3", align="center", flex_wrap="wrap",
            ),
            rx.hstack(
                rx.text(d.items_resumen, font_size="11px", color=_SLATE_500,
                        no_of_lines=1, flex="1"),
                rx.text(d.total_texto, font_size="13px", font_weight="700",
                        color=_TEXT),
                spacing="2", align="center", width="100%",
            ),
            rx.cond(
                d.repartidor_nombre != "",
                rx.hstack(
                    rx.icon(tag="bike", size=12, color=_PURPLE),
                    rx.text(d.repartidor_nombre, font_size="12px",
                            font_weight="600", color=_PURPLE),
                    spacing="1", align="center",
                ),
                rx.fragment(),
            ),
            rx.cond(
                d.notas != "",
                rx.text(d.notas, font_size="11px", color=_SLATE_500,
                        font_style="italic", no_of_lines=1),
                rx.fragment(),
            ),
            spacing="1", align="start", flex="1", min_width="0",
        ),
        rx.hstack(
            rx.cond(
                d.delivery_estado == "pendiente",
                rx.tooltip(
                    rx.button(
                        rx.icon(tag="bike", size=13),
                        on_click=DonoOperacionesState.delivery_marcar_en_camino(d.pedido_id),
                        background="rgba(59,130,246,0.12)", color=_BLUE_SOLID,
                        border="1px solid #93C5FD", border_radius="7px",
                        padding="6px", cursor="pointer", height="auto",
                        _hover={"background": "#BFDBFE"},
                    ),
                    content="Marcar en camino",
                ),
                rx.fragment(),
            ),
            rx.cond(
                d.delivery_estado == "en_camino",
                rx.tooltip(
                    rx.button(
                        rx.icon(tag="check", size=13),
                        on_click=DonoOperacionesState.delivery_marcar_entregado(d.pedido_id),
                        background="rgba(34,197,94,0.12)", color=_GREEN_SOLID,
                        border="1px solid #BBF7D0", border_radius="7px",
                        padding="6px", cursor="pointer", height="auto",
                        _hover={"background": "rgba(34,197,94,0.25)"},
                    ),
                    content="Marcar entregado",
                ),
                rx.fragment(),
            ),
            rx.cond(
                (d.delivery_estado == "pendiente") | (d.delivery_estado == "en_camino"),
                rx.tooltip(
                    rx.button(
                        rx.icon(tag="x", size=13),
                        on_click=DonoOperacionesState.delivery_cancelar(d.pedido_id),
                        background="rgba(239,68,68,0.12)", color="var(--twk-danger-text)",
                        border="1px solid #FECACA", border_radius="7px",
                        padding="6px", cursor="pointer", height="auto",
                        _hover={"background": "rgba(239,68,68,0.25)"},
                    ),
                    content="Cancelar delivery",
                ),
                rx.fragment(),
            ),
            spacing="1", align="center", flex_shrink="0",
        ),
        width="100%", align="center",
        padding="12px 14px",
        background=_SURFACE,
        border=f"1px solid {_SLATE_200}",
        border_radius="10px",
        _hover={"border_color": _ORANGE_BD, "box_shadow": "0 1px 4px rgba(0,0,0,0.06)"},
        transition="all 0.12s ease",
    )


def _delivery_form_dialog() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.dialog.title("Nuevo pedido delivery",
                            font_weight="800", color=_TEXT),
            rx.vstack(
                rx.text("Nombre del cliente *", font_size="12px",
                        font_weight="600", color="var(--twk-slate-300)"),
                rx.input(
                    value=DonoOperacionesState.delivery_form_nombre,
                    on_change=DonoOperacionesState.on_change_delivery_nombre,
                    placeholder="Juan Pérez",
                    background=_SURFACE, border=f"1px solid {_SLATE_200}",
                    border_radius="8px", color=_TEXT,
                    _focus={"border_color": _ORANGE},
                ),
                rx.text("Dirección *", font_size="12px",
                        font_weight="600", color="var(--twk-slate-300)"),
                rx.input(
                    value=DonoOperacionesState.delivery_form_direccion,
                    on_change=DonoOperacionesState.on_change_delivery_direccion,
                    placeholder="Av. Principal 123, Dpto 4B",
                    background=_SURFACE, border=f"1px solid {_SLATE_200}",
                    border_radius="8px", color=_TEXT,
                    _focus={"border_color": _ORANGE},
                ),
                rx.text("Teléfono", font_size="12px",
                        font_weight="600", color="var(--twk-slate-300)"),
                rx.input(
                    value=DonoOperacionesState.delivery_form_telefono,
                    on_change=DonoOperacionesState.on_change_delivery_telefono,
                    placeholder="987 654 321",
                    background=_SURFACE, border=f"1px solid {_SLATE_200}",
                    border_radius="8px", color=_TEXT,
                    _focus={"border_color": _ORANGE},
                ),
                rx.text("Notas", font_size="12px",
                        font_weight="600", color="var(--twk-slate-300)"),
                rx.text_area(
                    value=DonoOperacionesState.delivery_form_notas,
                    on_change=DonoOperacionesState.on_change_delivery_notas,
                    placeholder="Indicaciones de entrega...",
                    background=_SURFACE, border=f"1px solid {_SLATE_200}",
                    border_radius="8px", color=_TEXT, rows="2",
                    _focus={"border_color": _ORANGE},
                ),
                spacing="2", width="100%",
            ),
            rx.hstack(
                rx.dialog.close(
                    rx.button(
                        "Cancelar",
                        background=_SLATE_100, color="var(--twk-slate-300)",
                        border_radius="8px", cursor="pointer",
                        _hover={"background": _SLATE_700},
                    ),
                ),
                rx.button(
                    "Crear pedido",
                    on_click=DonoOperacionesState.crear_pedido_delivery,
                    background=_ORANGE, color=_WHITE,
                    border_radius="8px", cursor="pointer",
                    _hover={"background": _ORANGE_DK},
                ),
                spacing="2", width="100%", justify="end",
                padding_top="8px",
            ),
            max_width="520px",
            width="92vw",
            max_height="90vh",
            overflow_y="auto",
            background=_SURFACE, border_radius="14px",
            padding="24px",
        ),
        open=DonoOperacionesState.delivery_form_visible,
        on_open_change=DonoOperacionesState.set_delivery_form_visible,
    )


def _delivery_filtro_btn(label: str, valor: str) -> rx.Component:
    activo = DonoOperacionesState.delivery_filtro_estado == valor
    return rx.button(
        label,
        on_click=DonoOperacionesState.set_delivery_filtro_estado(valor),
        background=rx.cond(activo, _ORANGE, _SURFACE),
        color=rx.cond(activo, _WHITE, _SLATE_500),
        border=rx.cond(activo, f"1px solid {_ORANGE}", f"1px solid {_SLATE_200}"),
        border_radius="8px", font_size="12px", font_weight="600",
        padding="4px 12px", cursor="pointer", height="auto",
        _hover={"background": rx.cond(activo, _ORANGE_DK, _SLATE_700)},
    )


def _section_delivery() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.vstack(
                rx.text("Delivery", font_size="18px", font_weight="800",
                        color=_TEXT, line_height="1"),
                rx.text("Pedidos a domicilio",
                        font_size="13px", color=_SLATE_500),
                spacing="1", align="start",
            ),
            rx.spacer(),
            rx.hstack(
                _delivery_filtro_btn("Activos", ""),
                _delivery_filtro_btn("Pendientes", "pendiente"),
                _delivery_filtro_btn("En camino", "en_camino"),
                _delivery_filtro_btn("Entregados", "entregado"),
                spacing="1", align="center", flex_wrap="wrap",
            ),
            rx.button(
                rx.hstack(
                    rx.icon(tag="plus", size=14),
                    rx.text("Nuevo delivery", font_size="13px",
                            font_weight="700",
                            display=rx.breakpoints(initial="none", sm="block")),
                    spacing="2", align="center",
                ),
                on_click=DonoOperacionesState.abrir_form_delivery,
                background=_ORANGE, color=_WHITE,
                border_radius="8px", padding_x="14px", padding_y="8px",
                cursor="pointer",
                _hover={"background": _ORANGE_DK},
            ),
            width="100%", align="center", flex_wrap="wrap", gap="8px",
        ),
        rx.hstack(
            rx.icon(tag="info", size=14, color=_SLATE_500, flex_shrink="0"),
            rx.text(
                "Cada pedido avanza por Pendiente → En camino → Entregado. "
                "Cambia el estado desde cada tarjeta; el cobro se hace en Caja al entregar.",
                font_size="12px", color=_SLATE_500, line_height="1.4",
            ),
            spacing="2", align="center", width="100%",
        ),
        rx.cond(
            DonoOperacionesState.deliveries_lista.length() == 0,
            rx.center(
                rx.vstack(
                    rx.icon(tag="truck", size=40, color=_SLATE_200),
                    rx.text("Sin pedidos delivery",
                            font_size="14px", color=_SLATE_500),
                    rx.text("Crea un nuevo pedido con el botón de arriba",
                            font_size="12px", color=_SLATE_500),
                    spacing="2", align="center",
                ),
                padding_y="48px", width="100%",
                background=_SURFACE, border=f"1px solid {_SLATE_200}",
                border_radius="14px",
            ),
            rx.vstack(
                rx.foreach(DonoOperacionesState.deliveries_lista, _delivery_row),
                spacing="2", width="100%",
            ),
        ),
        _delivery_form_dialog(),
        spacing="4", width="100%",
    )


def _section_reservas() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.vstack(
                rx.text("Reservas", font_size="18px", font_weight="800",
                        color=_TEXT, line_height="1"),
                rx.text("Gestión de reservas de mesas",
                        font_size="13px", color=_SLATE_500),
                spacing="1", align="start",
            ),
            rx.spacer(),
            rx.hstack(
                rx.input(
                    value=DonoOperacionesState.reservas_fecha_filtro,
                    on_change=DonoOperacionesState.set_reservas_fecha_filtro,
                    type="date",
                    background=_SURFACE,
                    border=f"1px solid {_SLATE_200}",
                    border_radius="8px",
                    color=_TEXT,
                    font_size="13px",
                    width="160px",
                    _focus={"border_color": _ORANGE},
                ),
                rx.button(
                    rx.hstack(
                        rx.icon(tag="plus", size=14),
                        rx.text("Nueva reserva", font_size="13px",
                                font_weight="700",
                                display=rx.breakpoints(initial="none", sm="block")),
                        spacing="2", align="center",
                    ),
                    on_click=DonoOperacionesState.abrir_form_reserva(0),
                    background=_ORANGE, color=_WHITE,
                    border_radius="8px", padding_x="14px", padding_y="8px",
                    cursor="pointer",
                    _hover={"background": _ORANGE_DK},
                ),
                spacing="2", align="center",
            ),
            width="100%", align="center", flex_wrap="wrap", gap="8px",
        ),
        rx.hstack(
            rx.icon(tag="info", size=14, color=_SLATE_500, flex_shrink="0"),
            rx.text(
                "Al anotar una reserva, esa mesa aparece morada en el salón del mozo "
                "a la hora reservada, para que no la ocupe otro cliente.",
                font_size="12px", color=_SLATE_500, line_height="1.4",
            ),
            spacing="2", align="center", width="100%",
        ),
        rx.cond(
            DonoOperacionesState.reservas_lista.length() == 0,
            rx.center(
                rx.vstack(
                    rx.icon(tag="calendar_x_2", size=40, color=_SLATE_200),
                    rx.text("Sin reservas para esta fecha",
                            font_size="14px", color=_SLATE_500),
                    rx.text("Crea una nueva reserva con el botón de arriba",
                            font_size="12px", color=_SLATE_500),
                    spacing="2", align="center",
                ),
                padding_y="48px", width="100%",
                background=_SURFACE, border=f"1px solid {_SLATE_200}",
                border_radius="14px",
            ),
            rx.vstack(
                rx.foreach(DonoOperacionesState.reservas_lista, _reserva_row),
                spacing="2", width="100%",
            ),
        ),
        _reserva_form_dialog(),
        spacing="4", width="100%",
    )


# ── Banner upgrade para módulos premium ────────────────────────────────────────

def _upgrade_banner(modulo: str) -> rx.Component:
    return rx.center(
        rx.box(
            upgrade_cta(
                titulo=f"{modulo} — Plan Profesional",
                mensaje=(
                    f"{modulo} está disponible en el plan Profesional. "
                    "Mejorá tu plan para activarlo."
                ),
            ),
            max_width="560px", width="100%",
        ),
        width="100%", min_height="300px", padding="24px",
    )


# ── Área de contenido dinámico ────────────────────────────────────────────────

def _content_area() -> rx.Component:
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
                rx.cond(
                    FoodState.plan_permite_clientes,
                    _clientes_content(),
                    _upgrade_banner("Clientes"),
                ),
                rx.cond(
                    AdminPanelState.seccion == "cuentas",
                    rx.cond(
                        FoodState.plan_permite_cuentas,
                        _cuentas_content(),
                        _upgrade_banner("Cuentas por cobrar"),
                    ),
                    rx.cond(
                        AdminPanelState.seccion == "promociones",
                        rx.cond(
                            FoodState.plan_permite_promociones,
                            _promociones_content(),
                            _upgrade_banner("Promociones"),
                        ),
                        rx.cond(
                            AdminPanelState.seccion == "reservas",
                            _section_reservas(),
                            rx.cond(
                                AdminPanelState.seccion == "delivery",
                                _section_delivery(),
                                rx.cond(
                                    AdminPanelState.seccion == "inventario",
                                    rx.cond(
                                        FoodState.plan_permite_inventario,
                                        _inventario_content(),
                                        _upgrade_banner("Inventario"),
                                    ),
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
            ),
        ),
    )


# ── Cuerpo del dashboard ──────────────────────────────────────────────────────

def _dono_dashboard() -> rx.Component:
    return rx.vstack(
        _content_area(),
        spacing="4",
        width="100%",
    )


# ── Shell del panel ───────────────────────────────────────────────────────────

def _dono_shell(content: rx.Component, with_sidebar: bool = False) -> rx.Component:
    if with_sidebar:
        # Layout con sidebar: topbar fijo + fila (sidebar + contenido)
        body = rx.box(
            # Backdrop (mobile) — click cierra el drawer
            rx.box(
                on_click=AdminPanelState.cerrar_sidebar,
                class_name=rx.cond(
                    AdminPanelState.sidebar_open,
                    "twk-admin-bd open",
                    "twk-admin-bd",
                ),
            ),
            # Fila: sidebar + área de contenido
            rx.box(
                _admin_sidebar(),
                rx.box(
                    content,
                    padding=rx.breakpoints(initial="16px", sm="20px", lg="24px 28px"),
                    flex="1",
                    min_width="0",
                    overflow="hidden",
                ),
                display="flex",
                align_items="start",
                width="100%",
                min_height="calc(100vh - 60px)",
            ),
            position="relative",
            width="100%",
        )
    else:
        body = rx.box(
            content,
            padding=rx.breakpoints(initial="16px", sm="20px", lg="28px 32px"),
            max_width="1400px",
            margin="0 auto",
            width="100%",
        )

    return rx.box(
        rx.vstack(
            _dono_topbar(show_hamburger=with_sidebar),
            body,
            spacing="0",
            width="100%",
            min_height="100vh",
        ),
        background=_SLATE_50,
        min_height="100vh",
    )


# ── Login ─────────────────────────────────────────────────────────────────────

def _admin_glow() -> rx.Component:
    return rx.box(
        position="absolute",
        top="50%", left="50%",
        transform="translate(-50%, -50%)",
        width=rx.breakpoints(initial="280px", md="420px"),
        height=rx.breakpoints(initial="280px", md="420px"),
        background="radial-gradient(circle, rgba(255,255,255,0.06) 0%, rgba(255,255,255,0) 70%)",
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
        background=_SURFACE,
        border_radius="20px",
        width=rx.breakpoints(initial="190px", sm="230px", md="270px"),
        height=rx.breakpoints(initial="130px", sm="158px", md="186px"),
        box_shadow="0 12px 40px rgba(0,0,0,0.5)",
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
                    font_weight="800", color=_TEXT, line_height="1",
                ),
                width="100%", height="100%",
                display="flex", align_items="center", justify_content="center",
                background=_SLATE_700,
                border_radius="20px",
            ),
        ),
        background=_SURFACE,
        border_radius="20px",
        width=rx.breakpoints(initial="155px", sm="190px", md="220px"),
        height=rx.breakpoints(initial="105px", sm="128px", md="150px"),
        box_shadow="0 12px 40px rgba(0,0,0,0.5)",
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
         title="TUWAYKIFOOD | Acceso administrativo")
def dono_login_page() -> rx.Component:
    return rx.box(
        _connection_banner_es(),
        rx.center(
            rx.vstack(
                _brand_banner(),
                rx.vstack(
                    rx.text("Panel Administrativo", font_size="22px",
                            font_weight="800", color=_TEXT,
                            text_align="center"),
                    rx.text("Ingresa con tu email y contraseña",
                            font_size="13px", color=_SLATE_500,
                            text_align="center"),
                    spacing="1", align="center",
                ),
                rx.box(
                    rx.form(
                    rx.vstack(
                        rx.cond(
                            AdminLocalState.error_msg != "",
                            rx.box(
                                rx.hstack(
                                    rx.icon(tag="circle_alert", size=14,
                                            color="var(--twk-danger-text)"),
                                    rx.text(AdminLocalState.error_msg,
                                            font_size="13px", color="var(--twk-danger-text)",
                                            font_weight="600"),
                                    spacing="2", align="center",
                                ),
                                background="rgba(239,68,68,0.08)",
                                border="1px solid #FECACA",
                                border_radius="8px",
                                padding="10px 14px",
                                width="100%",
                            ),
                            rx.fragment(),
                        ),
                        rx.vstack(
                            rx.text("Email", font_size="11px",
                                    font_weight="600", color=_SLATE_500,
                                    text_transform="uppercase",
                                    letter_spacing="0.06em"),
                            rx.input(
                                placeholder="dueño@restaurante.com",
                                name="email",
                                value=AdminLocalState.email_input,
                                on_change=AdminLocalState.set_email_input,
                                type="text",
                                autocomplete="off",
                                class_name="twk-login-input",
                            ),
                            spacing="1", width="100%", align="start",
                        ),
                        rx.vstack(
                            rx.text("Contraseña", font_size="11px",
                                    font_weight="600", color=_SLATE_500,
                                    text_transform="uppercase",
                                    letter_spacing="0.06em"),
                            rx.box(
                                rx.input(
                                    placeholder="••••••••",
                                    name="password",
                                    value=AdminLocalState.password_input,
                                    on_change=AdminLocalState.set_password_input,
                                    type=rx.cond(
                                        AdminLocalState.show_password,
                                        "text",
                                        "password",
                                    ),
                                    autocomplete="current-password",
                                    class_name="twk-login-input",
                                    padding_right="40px",
                                ),
                                rx.tooltip(
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
                                        color=_SLATE_500,
                                        border="none",
                                        width="26px",
                                        height="26px",
                                        _hover={"background": "rgba(255,255,255,0.06)",
                                                "color": _WHITE},
                                        position="absolute",
                                        right="6px",
                                        top="50%",
                                        transform="translateY(-50%)",
                                        cursor="pointer",
                                    ),
                                    content="Mostrar u ocultar contraseña",
                                ),
                                position="relative",
                                width="100%",
                            ),
                            spacing="1", width="100%", align="start",
                        ),
                        rx.button(
                            "Ingresar al Panel",
                            type="submit",
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
                    on_submit=AdminLocalState.login_admin_local_submit,
                    reset_on_submit=False,
                    width="100%",
                    ),
                    background=_SURFACE,
                    border=f"1px solid {_SLATE_700}",
                    border_radius="20px",
                    padding="32px 28px",
                    box_shadow="0 20px 60px rgba(0,0,0,0.4)",
                    width="100%",
                ),
                rx.center(
                    rx.hstack(
                        rx.text("¿Eres empleado?", font_size="12px", color=_SLATE_500),
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
            background=_SLATE_50,
            padding="24px 16px",
        ),
    )


# ── Dashboard ─────────────────────────────────────────────────────────────────

@rx.page(
    route="/admin",
    on_load=[AdminLocalState.on_load_dono, FoodState.on_load_dono_page, ReportesState.init_reportes_dono],
    title="TUWAYKIFOOD | Panel administrativo",
)
def dono_page() -> rx.Component:
    return _dono_shell(_dono_dashboard(), with_sidebar=True)
