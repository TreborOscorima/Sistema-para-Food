"""Primitivas del sistema de diseño de TUWAYKIFOOD.

Nivel **atómico**: botón, chip de estado, punto de estado, campo, input,
select, interruptor, pestañas (segmentadas y con subrayado), tarjeta KPI y
celdas de tabla. Todo se construye sobre los tokens de ``theme.py`` — así las
páginas componen pantallas sin repetir estilos, y un rebrand sigue siendo un
solo archivo.

Este módulo es una **hoja** del grafo de dependencias: solo importa de
``theme.py``. Las piezas *compuestas* de la app (sidebar, ``app_shell``,
modales, ``surface_card``, ``kpi_card``) viven en ``shared.py`` y pueden usar
estas primitivas, no al revés.

Refleja 1:1 el tablero «Componentes» del sistema de diseño. Uso típico::

    from app.components import ui

    ui.button("Cobrar", FoodState.cobrar, icon="check", size="lg")
    ui.chip("Cobrado", tone="success")
    ui.field("Precio", ui.number_input(value=State.precio, on_change=State.set_precio))
    ui.segmented(["Promociones", "Cupones"], State.tab, State.set_tab)
"""

from __future__ import annotations

import reflex as rx

from app.components.theme import (
    ACCENT, ACCENT_BG, ACCENT_HOVER, ACCENT_SHADOW, ACCENT_SOFT, ACCENT_TEXT,
    BORDER_COLOR, BORDER_STRONG,
    DANGER_BG, DANGER_BORDER, DANGER_SOLID, DANGER_TEXT,
    DARK_600, DARK_700,
    GLOW, SOFT_GLOW,
    INFO_BG, INFO_BORDER, INFO_TEXT,
    PURPLE_LIGHT,
    SUCCESS_BG, SUCCESS_BORDER, SUCCESS_TEXT,
    SURFACE_BASE, SURFACE_HOVER, SURFACE_SOFT,
    TEXT_MUTED, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_WHITE,
    WARNING_BG, WARNING_BORDER, WARNING_TEXT,
)


# ─── helper: valor sensible a `disabled` (bool o Var) ────────────────────────
def _da(disabled, normal, dis):
    """Devuelve ``normal`` o ``dis`` según ``disabled``.

    Soporta las tres formas de ``disabled``: ``False`` (default → estilo
    normal), ``True`` (estilo deshabilitado fijo) y un ``Var`` reactivo
    (se resuelve con ``rx.cond`` en el cliente). Evita pasarle un bool de
    Python a ``rx.cond``.
    """
    if disabled is False:
        return normal
    if disabled is True:
        return dis
    return rx.cond(disabled, dis, normal)


# ═════════════════════════════════════════════════════════════════════════════
# Botones
# ═════════════════════════════════════════════════════════════════════════════

_BTN_SIZES = {
    "sm": {"height": "36px", "font_size": "13px", "padding_x": "14px", "radius": "8px",  "icon": 15},
    "md": {"height": "44px", "font_size": "14px", "padding_x": "18px", "radius": "10px", "icon": 17},
    "lg": {"height": "52px", "font_size": "16px", "padding_x": "24px", "radius": "12px", "icon": 19},
}

# Cada variante: (background, color, border, extra _hover)
_BTN_VARIANTS = {
    "primary":   (ACCENT, TEXT_WHITE, "none", {"background": ACCENT_HOVER}),
    "secondary": ("transparent", TEXT_SECONDARY, f"1px solid {BORDER_STRONG}",
                  {"background": SURFACE_HOVER}),
    "ghost":     ("transparent", TEXT_MUTED, "none",
                  {"background": SURFACE_HOVER, "color": TEXT_PRIMARY}),
    "danger":    (DANGER_SOLID, TEXT_WHITE, "none", {"opacity": "0.9"}),
}


def button(
    label,
    on_click=None,
    *,
    variant: str = "primary",
    size: str = "md",
    icon: str | None = None,
    icon_right: str | None = None,
    disabled=False,
    full_width: bool = False,
    **props,
) -> rx.Component:
    """Botón del sistema de diseño.

    ``variant``: ``"primary"`` (naranja), ``"secondary"`` (borde), ``"ghost"``
    (sin fondo), ``"danger"`` (rojo). ``size``: ``"sm"|"md"|"lg"``. ``icon`` /
    ``icon_right`` son tags de lucide (``rx.icon``). ``disabled`` acepta bool o
    ``Var``: cuando aplica, el botón se ve gris y con cursor bloqueado. Cualquier
    prop extra (``padding_x``, ``width``…) se pasa a ``rx.button``.
    """
    s = _BTN_SIZES.get(size, _BTN_SIZES["md"])
    bg, color, border, hover = _BTN_VARIANTS.get(variant, _BTN_VARIANTS["primary"])

    inner = [rx.text(label, font_weight="700", line_height="1")]
    if icon:
        inner.insert(0, rx.icon(tag=icon, size=s["icon"]))
    if icon_right:
        inner.append(rx.icon(tag=icon_right, size=s["icon"]))

    box_shadow = ACCENT_SHADOW if variant == "primary" else "none"

    return rx.button(
        rx.hstack(*inner, spacing="2", align="center", justify="center"),
        on_click=on_click,
        disabled=disabled,
        height=s["height"],
        padding_x=props.pop("padding_x", s["padding_x"]),
        font_size=s["font_size"],
        border_radius=s["radius"],
        border=border,
        background=_da(disabled, bg, DARK_700),
        color=_da(disabled, color, TEXT_MUTED),
        box_shadow=_da(disabled, box_shadow, "none"),
        cursor=_da(disabled, "pointer", "not-allowed"),
        width="100%" if full_width else props.pop("width", "auto"),
        white_space="nowrap",
        transition="background .15s ease, opacity .15s ease, border-color .15s ease",
        _hover=hover,
        **props,
    )


def icon_button(
    icon: str,
    on_click=None,
    *,
    variant: str = "secondary",
    size: int = 36,
    tooltip: str | None = None,
    disabled=False,
    **props,
) -> rx.Component:
    """Botón cuadrado de solo ícono (editar, cerrar, ver…)."""
    bg, color, border, hover = _BTN_VARIANTS.get(variant, _BTN_VARIANTS["secondary"])
    el = rx.button(
        rx.icon(tag=icon, size=int(size * 0.46)),
        on_click=on_click,
        disabled=disabled,
        width=f"{size}px",
        height=f"{size}px",
        padding="0",
        border_radius="8px",
        border=border,
        background=_da(disabled, bg, DARK_700),
        color=_da(disabled, color, TEXT_MUTED),
        cursor=_da(disabled, "pointer", "not-allowed"),
        display="flex",
        align_items="center",
        justify_content="center",
        transition="background .15s ease, color .15s ease",
        _hover=hover,
        **props,
    )
    if tooltip:
        return rx.tooltip(el, content=tooltip)
    return el


# ═════════════════════════════════════════════════════════════════════════════
# Chips de estado y puntos de estado
# ═════════════════════════════════════════════════════════════════════════════

# tone → (texto, fondo, borde)
_CHIP_TONES = {
    "success": (SUCCESS_TEXT, SUCCESS_BG, SUCCESS_BORDER),
    "danger":  (DANGER_TEXT, DANGER_BG, DANGER_BORDER),
    "warning": (WARNING_TEXT, WARNING_BG, WARNING_BORDER),
    "info":    (INFO_TEXT, INFO_BG, INFO_BORDER),
    "purple":  (PURPLE_LIGHT, "rgba(124,58,237,0.10)", "rgba(124,58,237,0.25)"),
    "accent":  (ACCENT_TEXT, ACCENT_BG, "rgba(234,88,12,0.25)"),
    "neutral": (TEXT_MUTED, "rgba(148,163,184,0.10)", BORDER_COLOR),
}


def chip(label, *, tone: str = "neutral", icon: str | None = None, **props) -> rx.Component:
    """Píldora de estado con fondo suave y texto por contraste.

    ``tone``: ``success | danger | warning | info | purple | accent | neutral``.
    """
    color, bg, border = _CHIP_TONES.get(tone, _CHIP_TONES["neutral"])
    inner = [rx.text(label, font_size="12px", font_weight="600", line_height="1")]
    if icon:
        inner.insert(0, rx.icon(tag=icon, size=12))
    return rx.box(
        rx.hstack(*inner, spacing="1", align="center"),
        style={
            "color": color, "background": bg, "border": f"1px solid {border}",
            "border_radius": "9999px", "padding": "5px 11px",
            "display": "inline-flex", "width": "fit-content",
        },
        **props,
    )


def status_dot(label, color: str, **props) -> rx.Component:
    """Punto de color + etiqueta (mesa libre / ocupada / por cobrar…)."""
    return rx.hstack(
        rx.box(width="9px", height="9px", border_radius="9999px",
               background=color, flex_shrink="0"),
        rx.text(label, font_size="13px", font_weight="600", color=TEXT_SECONDARY),
        spacing="2", align="center", **props,
    )


# ═════════════════════════════════════════════════════════════════════════════
# Campos: etiqueta + control (+ ayuda)
# ═════════════════════════════════════════════════════════════════════════════

def field(label, control, *, hint=None, error=None, **props) -> rx.Component:
    """Envuelve un control con su etiqueta arriba y ayuda/error opcional abajo."""
    parts = [
        rx.text(label, font_size="12px", font_weight="600", color=TEXT_MUTED),
        control,
    ]
    if hint is not None:
        parts.append(rx.text(hint, font_size="11px", color=TEXT_MUTED))
    if error is not None:
        parts.append(rx.text(error, font_size="11px", color=DANGER_TEXT))
    return rx.vstack(*parts, spacing="1", align="stretch", width="100%", **props)


def text_input(**props) -> rx.Component:
    """``rx.input`` con el estilo del sistema: alto 44, radio 10, foco naranja."""
    return rx.input(
        height=props.pop("height", "44px"),
        padding_x=props.pop("padding_x", "14px"),
        font_size=props.pop("font_size", "14px"),
        color=TEXT_PRIMARY,
        background=props.pop("background", SURFACE_SOFT),
        border=props.pop("border", f"1px solid {BORDER_COLOR}"),
        border_radius=props.pop("border_radius", "10px"),
        width=props.pop("width", "100%"),
        _placeholder={"color": TEXT_MUTED},
        _focus={"border_color": ACCENT, "box_shadow": f"0 0 0 3px {ACCENT_SOFT}",
                "outline": "none"},
        **props,
    )


def number_input(**props) -> rx.Component:
    """Como :func:`text_input` pero numérico y alineado a la derecha."""
    props.setdefault("type", "number")
    props.setdefault("text_align", "right")
    props.setdefault("min", "0")
    return text_input(**props)


def search_input(placeholder: str = "Buscar…", **props) -> rx.Component:
    """Campo de búsqueda con lupa a la izquierda."""
    return rx.hstack(
        rx.icon(tag="search", size=16, color=TEXT_MUTED),
        rx.el.input(
            placeholder=placeholder,
            style={
                "background": "transparent", "border": "none", "outline": "none",
                "fontSize": "14px", "color": TEXT_PRIMARY, "width": "100%",
                "fontFamily": "inherit",
            },
            **props,
        ),
        spacing="2",
        align="center",
        height="44px",
        padding_x="14px",
        background=SURFACE_SOFT,
        border=f"1px solid {BORDER_COLOR}",
        border_radius="10px",
        width="100%",
        _focus_within={"border_color": ACCENT},
    )


def select_input(items, **props) -> rx.Component:
    """``rx.select`` de alto nivel con el ancho del sistema.

    Estilo del trigger acotado por Radix; se deja el tamaño coherente y el resto
    pasa (``value``, ``on_change``, ``placeholder``).
    """
    props.setdefault("width", "100%")
    return rx.select(items, **props)


# ═════════════════════════════════════════════════════════════════════════════
# Interruptor (switch)
# ═════════════════════════════════════════════════════════════════════════════

def toggle(checked, on_click, *, color: str = ACCENT, size: str = "md") -> rx.Component:
    """Interruptor estilo iOS. ``on_click`` es el evento ya armado (p. ej.
    ``State.toggle_disponible(id)`` o ``State.set_x(~State.x)``).
    ``size``: ``"sm"`` (filas) o ``"md"``.
    """
    w, h, thumb, travel = {
        "sm": ("34px", "20px", "16px", "14px"),
        "md": ("46px", "26px", "20px", "20px"),
    }.get(size, ("46px", "26px", "20px", "20px"))
    return rx.box(
        rx.box(
            position="absolute", top="2px", left="2px",
            width=thumb, height=thumb, border_radius="9999px",
            background="#FFFFFF", box_shadow="0 1px 3px rgba(0,0,0,0.45)",
            transform=rx.cond(checked, f"translateX({travel})", "translateX(0)"),
            transition="transform 0.22s cubic-bezier(0.4,0,0.2,1)",
        ),
        on_click=on_click,
        position="relative", width=w, height=h, border_radius="9999px",
        background=rx.cond(checked, color, DARK_600),
        border=rx.cond(checked, f"1px solid {color}", f"1px solid {DARK_700}"),
        cursor="pointer", flex_shrink="0",
        transition="background 0.22s ease, border-color 0.22s ease",
        _hover={"opacity": "0.88"},
    )


def labeled_toggle(label, checked, on_click, *, color: str = ACCENT,
                   size: str = "md", **props) -> rx.Component:
    """Interruptor + etiqueta que se atenúa cuando está apagado."""
    return rx.hstack(
        toggle(checked, on_click, color=color, size=size),
        rx.text(label, font_size="13px", font_weight="600",
                color=rx.cond(checked, TEXT_SECONDARY, TEXT_MUTED)),
        spacing="2", align="center", **props,
    )


# ═════════════════════════════════════════════════════════════════════════════
# Pestañas
# ═════════════════════════════════════════════════════════════════════════════

def _norm_options(options):
    """Acepta ``["A","B"]`` o ``[("a","A"),("b","B")]`` → lista de (clave, etiqueta)."""
    out = []
    for o in options:
        if isinstance(o, (tuple, list)):
            out.append((o[0], o[1]))
        else:
            out.append((o, o))
    return out


def segmented(options, value, on_change, **props) -> rx.Component:
    """Control segmentado (píldora). La opción activa se pinta de naranja.

    ``options``: lista de claves o de ``(clave, etiqueta)``. ``value`` es un
    ``Var`` con la clave activa. ``on_change`` es un manejador que recibe la
    clave (``on_change(clave)``, igual que ``State.set_tab``).
    """
    items = _norm_options(options)
    pills = [
        rx.box(
            rx.text(label, font_size="13px", font_weight="600", line_height="1",
                    color=rx.cond(value == key, TEXT_WHITE, TEXT_MUTED)),
            on_click=on_change(key),
            background=rx.cond(value == key, ACCENT, "transparent"),
            border_radius="8px", padding="8px 16px", cursor="pointer",
            transition="background .15s ease, color .15s ease",
            _hover={"color": TEXT_PRIMARY},
        )
        for key, label in items
    ]
    return rx.hstack(
        *pills,
        spacing="1",
        background=SURFACE_SOFT,
        border=f"1px solid {BORDER_COLOR}",
        border_radius="12px",
        padding="4px",
        width="fit-content",
        **props,
    )


def tabs_underline(options, value, on_change, **props) -> rx.Component:
    """Pestañas con subrayado (filtros de fecha, secciones)."""
    items = _norm_options(options)
    tabs = [
        rx.box(
            rx.text(label, font_size="13px", font_weight="600", line_height="1",
                    color=rx.cond(value == key, TEXT_PRIMARY, TEXT_MUTED)),
            on_click=on_change(key),
            padding="0 2px 10px", cursor="pointer",
            border_bottom=rx.cond(value == key, f"2px solid {ACCENT}",
                                  "2px solid transparent"),
            transition="color .15s ease, border-color .15s ease",
        )
        for key, label in items
    ]
    return rx.hstack(
        *tabs, spacing="5", align="end",
        border_bottom=f"1px solid {BORDER_COLOR}", width="100%", **props,
    )


# ═════════════════════════════════════════════════════════════════════════════
# Tarjeta KPI (dato protagonista + delta opcional)
# ═════════════════════════════════════════════════════════════════════════════

def stat_tile(
    label,
    value,
    *,
    delta=None,
    delta_up: bool = True,
    caption=None,
    accent: str = ACCENT,
    **props,
) -> rx.Component:
    """KPI: etiqueta chica, número protagonista, delta y pie opcionales.

    ``delta`` es texto (``"12%"``); ``delta_up`` elige verde/rojo y la flecha.
    """
    head = [rx.text(label, font_size="12px", font_weight="700",
                    letter_spacing="0.08em", text_transform="uppercase",
                    color=TEXT_MUTED)]
    if delta is not None:
        d_color = SUCCESS_TEXT if delta_up else DANGER_TEXT
        d_bg = SUCCESS_BG if delta_up else DANGER_BG
        head.append(rx.spacer())
        head.append(
            rx.hstack(
                rx.icon(tag="trending_up" if delta_up else "trending_down",
                        size=12, color=d_color),
                rx.text(delta, font_size="12px", font_weight="700", color=d_color),
                spacing="1", align="center",
                background=d_bg, border_radius="9999px", padding="4px 9px",
            )
        )

    body = [
        rx.hstack(*head, align="center", width="100%"),
        rx.text(value, font_size="1.9rem", font_weight="800", line_height="1.05",
                color=TEXT_PRIMARY, style={"font_variant_numeric": "tabular-nums"}),
    ]
    if caption is not None:
        body.append(rx.text(caption, font_size="12px", color=TEXT_MUTED))

    return rx.box(
        rx.vstack(*body, align="start", spacing="2", width="100%"),
        style={
            "background": SURFACE_BASE, "border": f"1px solid {BORDER_COLOR}",
            "border_radius": "16px", "box_shadow": GLOW, "padding": "1.15rem 1.25rem",
            "border_top": f"2px solid {accent}",
        },
        width="100%",
        **props,
    )


# ═════════════════════════════════════════════════════════════════════════════
# Tabla (piezas para componer con rx.foreach)
# ═════════════════════════════════════════════════════════════════════════════

def table_cell(content, *, flex: str = "1", align: str = "left",
               muted: bool = False, mono: bool = False, **props) -> rx.Component:
    """Celda de tabla. ``align``: left|right|center. ``mono`` = cifras tabulares."""
    just = {"left": "flex-start", "right": "flex-end", "center": "center"}.get(align, "flex-start")
    node = content
    if isinstance(content, str):
        node = rx.text(
            content, font_size="14px",
            color=TEXT_MUTED if muted else TEXT_SECONDARY,
            style={"font_variant_numeric": "tabular-nums"} if mono else {},
            no_of_lines=1,
        )
    return rx.box(
        node,
        flex=flex, min_width="0",
        display="flex", align_items="center", justify_content=just,
        padding="15px 20px", **props,
    )


def table_head_cell(label, *, flex: str = "1", align: str = "left", **props) -> rx.Component:
    """Celda de encabezado (mayúsculas, tenue)."""
    just = {"left": "flex-start", "right": "flex-end", "center": "center"}.get(align, "flex-start")
    return rx.box(
        rx.text(label, font_size="11px", font_weight="700", letter_spacing="0.08em",
                text_transform="uppercase", color=TEXT_MUTED, no_of_lines=1),
        flex=flex, min_width="0",
        display="flex", align_items="center", justify_content=just,
        padding="12px 20px", **props,
    )


def table_row(*cells, striped: bool = False, **props) -> rx.Component:
    """Fila de datos. ``striped`` alterna un fondo muy sutil."""
    return rx.hstack(
        *cells,
        spacing="0", align="center", width="100%",
        border_top=f"1px solid {BORDER_COLOR}",
        background="rgba(255,255,255,0.02)" if striped else "transparent",
        _hover={"background": SURFACE_HOVER},
        transition="background .12s ease",
        **props,
    )


def table(head, *rows, **props) -> rx.Component:
    """Contenedor de tabla: encabezado + filas, dentro de una tarjeta con scroll.

    ``head`` es un ``rx.hstack`` de :func:`table_head_cell`; cada fila usa
    :func:`table_row` con :func:`table_cell`. Los ``flex`` de encabezado y celdas
    deben coincidir para alinear las columnas.
    """
    return rx.box(
        rx.hstack(head, spacing="0", width="100%", background=SURFACE_SOFT),
        rx.box(*rows, width="100%"),
        style={
            "background": SURFACE_BASE, "border": f"1px solid {BORDER_COLOR}",
            "border_radius": "16px", "box_shadow": SOFT_GLOW, "overflow": "hidden",
        },
        width="100%",
        overflow_x="auto",
        **props,
    )


# ═════════════════════════════════════════════════════════════════════════════
# Misceláneos
# ═════════════════════════════════════════════════════════════════════════════

def divider(*, vertical: bool = False, **props) -> rx.Component:
    """Línea divisoria fina en el color de borde del tema."""
    if vertical:
        return rx.box(width="1px", height=props.pop("height", "100%"),
                      background=BORDER_COLOR, flex_shrink="0", **props)
    return rx.box(height="1px", width="100%", background=BORDER_COLOR, **props)
