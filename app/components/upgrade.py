"""Bloque de upgrade de plan + modal comparativo (estilo Sistema de Ventas).

Reemplaza los mensajes sueltos de "Contacte a TUWAYKI para actualizar su plan"
por un bloque con dos acciones claras:

  • **Mejorar Plan**       → abre el modal comparativo de planes (in-app).
  • **Contactar a Ventas** → abre WhatsApp/email de TUWAYKI con el asunto listo.

El cambio de plan no es self-service (lo aprovisiona TUWAYKI), así que los
botones de cada tarjeta también llevan a Ventas con el plan pre-cargado en el
mensaje. Todos los colores salen de ``theme`` → funciona en claro y oscuro.
"""
from __future__ import annotations

from urllib.parse import quote

import reflex as rx

from tuwayki_core.constants import WHATSAPP_NUMBER

from app.components.theme import (
    ACCENT,
    ACCENT_HOVER,
    ACCENT_SOFT,
    ACCENT_TEXT,
    BORDER_COLOR,
    SUCCESS_SOLID,
    SURFACE_BASE,
    SURFACE_ELEVATED,
    TEXT_MUTED,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    TEXT_WHITE,
    WARNING_TEXT,
)

# ─── Contacto de Ventas ───────────────────────────────────────────────────────
# El número de WhatsApp comercial es el MISMO de toda la suite: vive en
# tuwayki_core.constants (WHATSAPP_NUMBER), igual que en Sistema de Ventas. Así
# se cambia en un solo lugar para todos los productos.
def _contacto_href(plan: str | None = None) -> str:
    """Link de WhatsApp de Ventas con el mensaje pre-cargado."""
    if plan:
        msg = f"Hola TUWAYKI, quiero mejorar mi plan de TUWAYKIFOOD al plan {plan}."
    else:
        msg = "Hola TUWAYKI, quiero más información sobre los planes de TUWAYKIFOOD."
    return f"https://wa.me/{WHATSAPP_NUMBER}?text={quote(msg)}"


# ─── Estado del modal ────────────────────────────────────────────────────────
class PlanUpgradeState(rx.State):
    """Controla la apertura del modal comparativo de planes."""

    modal_abierto: bool = False

    def abrir_planes(self):
        self.modal_abierto = True

    def cerrar_planes(self):
        self.modal_abierto = False

    def set_modal_abierto(self, valor: bool):
        self.modal_abierto = bool(valor)


# ─── Datos de los planes (Food) ──────────────────────────────────────────────
_PLANES: list[dict] = [
    {
        "nombre": "Standard",
        "icono": "sparkles",
        "popular": False,
        "limites": ["Hasta 10 mesas", "5 usuarios"],
        "modulos": [
            "Mozos, mesas y comandas",
            "Caja, cobros y cierre de turno",
            "Carta / menú digital con QR",
            "Cocina (impresión de comandas)",
            "Inventario básico: stock, alertas y kardex",
            "Reportes diarios de ventas",
        ],
        "cta": "Elegir Standard",
    },
    {
        "nombre": "Profesional",
        "icono": "crown",
        "popular": True,
        "limites": ["Mesas ilimitadas", "Usuarios ilimitados"],
        "modulos": [
            "Todo lo del Standard",
            "Inventario avanzado: recetas + producción",
            "Promociones, cupones y descuentos",
            "Clientes y fidelización",
            "Cuentas corrientes / fiado",
            "Reportes avanzados (P&L, IGV, márgenes) + Excel",
        ],
        "cta": "Mejorar a Profesional",
    },
    {
        "nombre": "Enterprise",
        "icono": "rocket",
        "popular": False,
        "en_planeacion": True,
        "limites": ["Sucursales a medida", "Usuarios ilimitados"],
        "modulos": [
            "Todo lo del Profesional",
            "Facturación electrónica (SUNAT)",
            "Multi-sucursal y consolidado",
            "Onboarding e implementación a medida",
            "Soporte dedicado",
        ],
        "cta": "Contactar",
    },
]


def _bullet(texto: str) -> rx.Component:
    return rx.hstack(
        rx.icon(tag="circle_check", size=15, color=SUCCESS_SOLID, flex_shrink="0",
                margin_top="2px"),
        rx.text(texto, font_size="13px", color=TEXT_SECONDARY, line_height="1.35"),
        spacing="2", align="start", width="100%",
    )


def _plan_badge(plan: dict) -> rx.Component:
    if plan.get("popular"):
        return rx.badge("Más popular", background=ACCENT, color=TEXT_WHITE,
                        border_radius="999px", font_size="10px", font_weight="700",
                        padding="3px 10px")
    if plan.get("en_planeacion"):
        return rx.badge("En planeación", background="rgba(148,163,184,0.15)",
                        color=TEXT_MUTED, border_radius="999px", font_size="10px",
                        font_weight="700", padding="3px 10px")
    return rx.box(height="0px")


def _plan_card(plan: dict) -> rx.Component:
    popular = bool(plan.get("popular", False))
    return rx.box(
        rx.vstack(
            # Encabezado: ícono + "PLAN / Nombre"
            rx.hstack(
                rx.box(
                    rx.icon(tag=plan["icono"], size=20,
                            color=ACCENT if popular else ACCENT_TEXT),
                    width="42px", height="42px", border_radius="11px",
                    background=ACCENT_SOFT, display="flex",
                    align_items="center", justify_content="center", flex_shrink="0",
                ),
                rx.spacer(),
                rx.vstack(
                    rx.text("PLAN", font_size="10px", font_weight="700",
                            letter_spacing="0.12em", color=TEXT_MUTED),
                    rx.text(plan["nombre"], font_size="17px", font_weight="800",
                            color=TEXT_PRIMARY, line_height="1"),
                    spacing="1", align="end",
                ),
                width="100%", align="center",
            ),
            _plan_badge(plan),
            # Límites
            rx.text("LÍMITES", font_size="10px", font_weight="700",
                    letter_spacing="0.1em", color=TEXT_MUTED, margin_top="6px"),
            rx.vstack(*[_bullet(l) for l in plan["limites"]], spacing="2", width="100%"),
            # Módulos
            rx.text("MÓDULOS", font_size="10px", font_weight="700",
                    letter_spacing="0.1em", color=TEXT_MUTED, margin_top="6px"),
            rx.vstack(*[_bullet(m) for m in plan["modulos"]], spacing="2", width="100%"),
            rx.spacer(),
            rx.link(
                rx.button(
                    plan["cta"],
                    width="100%",
                    background=ACCENT if popular else "transparent",
                    color=TEXT_WHITE if popular else ACCENT_TEXT,
                    border=f"1px solid {ACCENT if popular else BORDER_COLOR}",
                    border_radius="10px", font_weight="700", font_size="13px",
                    padding="10px", cursor="pointer",
                    _hover={"background": ACCENT_HOVER if popular else ACCENT_SOFT},
                ),
                href=_contacto_href(plan["nombre"]),
                is_external=True,
                width="100%",
                margin_top="10px",
            ),
            spacing="2", align="start", width="100%", height="100%",
        ),
        background=ACCENT_SOFT if popular else SURFACE_ELEVATED,
        border=f"2px solid {ACCENT if popular else BORDER_COLOR}",
        border_radius="16px", padding="18px",
        flex="1", min_width="240px",
        box_shadow="0 8px 30px rgba(234,88,12,0.18)" if popular else "none",
    )


def plan_upgrade_modal() -> rx.Component:
    """Modal comparativo de planes. Se abre con ``PlanUpgradeState.abrir_planes``."""
    return rx.dialog.root(
        rx.dialog.content(
            rx.hstack(
                rx.vstack(
                    rx.heading("Elige el plan ideal para tu crecimiento",
                               size="5", color=TEXT_PRIMARY),
                    rx.text("Compara opciones y elige el plan que mejor se adapta a tu negocio.",
                            font_size="13px", color=TEXT_MUTED),
                    spacing="1", align="start",
                ),
                rx.spacer(),
                rx.button(
                    rx.icon(tag="x", size=18),
                    on_click=PlanUpgradeState.cerrar_planes,
                    background="transparent", color=TEXT_MUTED, cursor="pointer",
                    padding="6px", _hover={"background": SURFACE_BASE},
                    border_radius="8px",
                ),
                width="100%", align="start", margin_bottom="16px",
            ),
            rx.box(
                rx.flex(
                    *[_plan_card(p) for p in _PLANES],
                    direction=rx.breakpoints(initial="column", md="row"),
                    gap="14px", width="100%", align="stretch",
                ),
                width="100%",
            ),
            rx.hstack(
                rx.spacer(),
                rx.button(
                    "Cerrar",
                    on_click=PlanUpgradeState.cerrar_planes,
                    background=SURFACE_BASE, color=TEXT_SECONDARY,
                    border=f"1px solid {BORDER_COLOR}", border_radius="10px",
                    font_weight="600", padding="9px 18px", cursor="pointer",
                    margin_top="16px",
                ),
                width="100%",
            ),
            max_width="1040px", width="94vw",
            max_height="90vh", overflow_y="auto",
            background=SURFACE_BASE,
            border=f"1px solid {BORDER_COLOR}",
        ),
        open=PlanUpgradeState.modal_abierto,
        on_open_change=PlanUpgradeState.set_modal_abierto,
    )


def upgrade_cta(mensaje: str, titulo: str | None = None,
                incluir_modal: bool = True) -> rx.Component:
    """Bloque de upgrade con botones 'Mejorar Plan' y 'Contactar a Ventas'.

    - ``mensaje``: por qué la función requiere un plan superior.
    - ``titulo``: encabezado opcional (ej. 'Reportes avanzados').
    - ``incluir_modal``: renderiza el modal comparativo junto al bloque. Dejar en
      True salvo que la página ya monte ``plan_upgrade_modal`` aparte.
    """
    return rx.fragment(
        rx.box(
            rx.hstack(
                rx.icon(tag="lock", size=18, color=ACCENT, flex_shrink="0"),
                rx.vstack(
                    rx.text(titulo, font_size="14px", font_weight="700",
                            color=TEXT_PRIMARY) if titulo else rx.fragment(),
                    rx.text(mensaje, font_size="13px", color=TEXT_SECONDARY,
                            line_height="1.4"),
                    spacing="1", align="start", flex="1", min_width="0",
                ),
                spacing="3", align="start", width="100%",
            ),
            rx.hstack(
                rx.button(
                    rx.icon(tag="rocket", size=15),
                    rx.text("Mejorar Plan", font_size="13px", font_weight="700"),
                    on_click=PlanUpgradeState.abrir_planes,
                    background=ACCENT, color=TEXT_WHITE, border_radius="10px",
                    padding="9px 16px", cursor="pointer", spacing="2",
                    _hover={"background": ACCENT_HOVER},
                ),
                rx.link(
                    rx.button(
                        rx.icon(tag="message_circle", size=15),
                        rx.text("Contactar a Ventas", font_size="13px", font_weight="600"),
                        background="transparent", color=ACCENT_TEXT,
                        border=f"1px solid {BORDER_COLOR}", border_radius="10px",
                        padding="9px 16px", cursor="pointer", spacing="2",
                        _hover={"background": ACCENT_SOFT},
                    ),
                    href=_contacto_href(),
                    is_external=True,
                ),
                spacing="3", margin_top="14px", flex_wrap="wrap",
            ),
            background=ACCENT_SOFT,
            border=f"1px solid {ACCENT}",
            border_radius="12px", padding="16px 18px", width="100%",
        ),
        plan_upgrade_modal() if incluir_modal else rx.fragment(),
    )
