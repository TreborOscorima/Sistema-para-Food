"""Ayuda contextual reutilizable por módulo.

Provee dos piezas para que cada módulo se entienda solo (plan UX T-02/T-03):

- `ayuda_trigger()` + `ayuda_modal(...)`: un botón "¿Cómo funciona?" que abre un
  modal con el flujo del módulo en pasos y, opcionalmente, la leyenda de colores.
- `empty_state(...)`: un estado vacío con ícono, explicación y un botón que lleva
  a la solución, en vez de un texto muerto.

El contenido de cada módulo se define en la propia página (datos estáticos de
Python), y estos helpers se encargan de renderizarlo de forma consistente.
"""

from __future__ import annotations

import reflex as rx

from app.components.shared import (
    ACCENT, ACCENT_HOVER,
    DARK_700, DARK_800,
    DARK_MODAL_MUTED, DARK_MODAL_PROPS, DARK_MODAL_TEXT,
    PAGE_BACKGROUND, SURFACE_BASE,
    TEXT_MUTED, TEXT_PRIMARY, TEXT_WHITE,
)


class AyudaState(rx.State):
    """Controla la visibilidad del modal de ayuda. Una sola instancia alcanza:
    cada página monta su propio `ayuda_modal`, y solo una está montada a la vez."""

    abierto: bool = False

    def abrir(self) -> None:
        self.abierto = True

    def cerrar(self) -> None:
        self.abierto = False

    def set_abierto(self, valor: bool) -> None:
        self.abierto = valor


# ─── Botón que abre la ayuda ──────────────────────────────────────────────────

def ayuda_trigger() -> rx.Component:
    return rx.hstack(
        rx.icon(tag="circle_help", size=16, color=TEXT_MUTED),
        rx.text("¿Cómo funciona?", font_size="12px", font_weight="600", color=TEXT_MUTED),
        on_click=AyudaState.abrir,
        spacing="2", align="center", cursor="pointer",
        background=SURFACE_BASE, border=f"1px solid {DARK_700}",
        border_radius="8px", padding="6px 12px",
        _hover={"border_color": ACCENT, "color": TEXT_WHITE},
        flex_shrink="0",
    )


# ─── Modal de ayuda ───────────────────────────────────────────────────────────

def _num(n: int) -> rx.Component:
    return rx.box(
        rx.text(str(n), font_size="12px", font_weight="800", color=TEXT_WHITE),
        background=ACCENT, border_radius="50%",
        min_width="22px", height="22px", display="flex",
        align_items="center", justify_content="center", flex_shrink="0",
    )


def _paso(n: int, texto: str) -> rx.Component:
    return rx.hstack(
        _num(n),
        rx.text(texto, font_size="13px", color=DARK_MODAL_TEXT, line_height="1.5"),
        spacing="3", align="start", width="100%",
    )


def _seccion(sec: dict) -> rx.Component:
    hijos = []
    if sec.get("titulo"):
        hijos.append(
            rx.text(sec["titulo"], font_size="11px", font_weight="700",
                    color=ACCENT, text_transform="uppercase", letter_spacing="0.05em")
        )
    for i, paso in enumerate(sec["pasos"], start=1):
        hijos.append(_paso(i, paso))
    return rx.vstack(*hijos, spacing="2", align="start", width="100%")


def _leyenda_item(color: str, label: str) -> rx.Component:
    return rx.hstack(
        rx.box(width="12px", height="12px", border_radius="3px",
               background=color, flex_shrink="0"),
        rx.text(label, font_size="12px", color=DARK_MODAL_MUTED),
        spacing="2", align="center",
    )


def ayuda_modal(*, titulo: str, subtitulo: str,
                secciones: list[dict], leyenda: list[tuple] | None = None) -> rx.Component:
    """Modal de ayuda de un módulo.

    - `secciones`: lista de {"titulo": str | None, "pasos": [str, ...]}. Los pasos
      se numeran; si hay título de sección, la numeración reinicia en cada bloque.
    - `leyenda`: lista opcional de (color, etiqueta) para explicar estados/colores.
    """
    cuerpo: list = [
        rx.hstack(
            rx.icon(tag="circle_help", size=18, color=ACCENT),
            rx.text(titulo, font_size="17px", font_weight="800", color=DARK_MODAL_TEXT),
            spacing="2", align="center",
        ),
        rx.text(subtitulo, font_size="13px", color=DARK_MODAL_MUTED),
        rx.box(height="2px", width="100%", background=DARK_700, border_radius="1px"),
    ]
    for sec in secciones:
        cuerpo.append(_seccion(sec))
    if leyenda:
        cuerpo.append(rx.box(height="1px", width="100%", background=DARK_700))
        cuerpo.append(
            rx.text("Qué significa cada color", font_size="11px", font_weight="700",
                    color=DARK_MODAL_MUTED, text_transform="uppercase", letter_spacing="0.05em")
        )
        cuerpo.append(
            rx.hstack(
                *[_leyenda_item(color, label) for color, label in leyenda],
                spacing="4", wrap="wrap", width="100%",
            )
        )
    cuerpo.append(
        rx.button(
            "Entendido",
            on_click=AyudaState.cerrar,
            background=ACCENT, color=TEXT_WHITE,
            border_radius="10px", font_size="14px", font_weight="700",
            cursor="pointer", width="100%", height="42px",
            _hover={"background": ACCENT_HOVER},
        )
    )
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(*cuerpo, spacing="3", width="100%", align="start"),
            max_width="460px", width="92vw",
            **DARK_MODAL_PROPS,
        ),
        open=AyudaState.abierto,
        on_open_change=AyudaState.set_abierto,
    )


# ─── Estado vacío accionable ──────────────────────────────────────────────────

def empty_state(*, icono: str, titulo: str, texto: str,
                cta_label: str | None = None, cta_on_click=None,
                cta_href: str | None = None) -> rx.Component:
    """Estado vacío con ícono, explicación y (opcional) un botón que lleva a la
    solución. Pensado para las vistas oscuras (Mozos/Caja/Cocina)."""
    hijos = [
        rx.icon(tag=icono, size=30, color=TEXT_MUTED),
        rx.text(titulo, font_size="14px", font_weight="700", color=TEXT_PRIMARY),
        rx.text(texto, font_size="12px", color=TEXT_MUTED,
                line_height="1.5", text_align="center"),
    ]
    if cta_label:
        contenido = rx.hstack(
            rx.icon(tag="arrow_right", size=14, color=TEXT_WHITE),
            rx.text(cta_label, font_size="13px", font_weight="700", color=TEXT_WHITE),
            spacing="2", align="center",
        )
        if cta_href:
            hijos.append(
                rx.link(contenido, href=cta_href, background=ACCENT,
                        border_radius="8px", padding="9px 16px", text_decoration="none",
                        _hover={"background": ACCENT_HOVER})
            )
        elif cta_on_click is not None:
            hijos.append(
                rx.button(contenido, on_click=cta_on_click, background=ACCENT,
                          border_radius="8px", padding="9px 16px", cursor="pointer",
                          _hover={"background": ACCENT_HOVER})
            )
    return rx.center(
        rx.vstack(*hijos, spacing="3", align="center", max_width="360px"),
        padding_y="40px", width="100%",
    )
