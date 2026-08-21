"""Página de gestión de inventario — insumos, recetas y planificador de producción."""

from __future__ import annotations

import reflex as rx

from app.states.food_state import (
    FoodState,
    InsumoView,
    ProduccionNecesidadView,
    ProduccionPlanItem,
    RecetaItemView,
)
from app.states.food_state import AdminLocalState
from app.pages.dono import _dono_shell
from app.components.ayuda import ayuda_modal, ayuda_trigger, empty_state
from app.components.shared import (
    WARNING_TEXT, SUCCESS_TEXT, DANGER_TEXT,
    ACCENT, ACCENT_HOVER,
    DANGER_SOLID,
    DARK_700, DARK_800,
    PAGE_BACKGROUND,
    SUCCESS_SOLID,
    TEXT_MUTED, TEXT_PRIMARY, TEXT_WHITE,
    WARNING_SOLID,
    switch_toggle,
)


# ── Helpers de estilo ────────────────────────────────────────────────────────

def _section_card(title: str, icon: str, *children) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.icon(tag=icon, size=15, color=ACCENT),
                rx.text(title, font_size="15px", font_weight="700", color=TEXT_PRIMARY),
                spacing="2",
                align="center",
            ),
            *children,
            spacing="4",
            width="100%",
        ),
        background=DARK_800,
        border=f"1px solid {DARK_700}",
        border_radius="12px",
        padding="16px 18px",
        width="100%",
        box_shadow="0 1px 3px rgba(0,0,0,0.06)",
    )


# ── Alertas de bajo stock ────────────────────────────────────────────────────

def _alerta_bajo_stock() -> rx.Component:
    return rx.cond(
        FoodState.inv_alertas_bajo_stock.length() > 0,
        rx.box(
            rx.hstack(
                rx.text("⚠️", font_size="20px", line_height="1"),
                rx.vstack(
                    rx.text(
                        "Stock bajo — requiere reposición",
                        font_size="13px",
                        font_weight="700",
                        color=WARNING_TEXT,
                    ),
                    rx.text(
                        rx.foreach(
                            FoodState.inv_alertas_bajo_stock,
                            lambda n: rx.text(n, font_size="12px", color=WARNING_TEXT),
                        ),
                    ),
                    spacing="1",
                    align="start",
                ),
                spacing="3",
                align="start",
                width="100%",
            ),
            background="rgba(245,158,11,0.10)",
            border="1px solid rgba(245,158,11,0.25)",
            border_radius="10px",
            padding="12px 14px",
            width="100%",
        ),
        rx.fragment(),
    )


# ── Tabla de insumos ─────────────────────────────────────────────────────────

_INV_GRID_COLS = "2fr 1fr 1fr 1fr 150px"


def _alerta_vencimientos() -> rx.Component:
    return rx.cond(
        FoodState.inv_alertas_vencimiento.length() > 0,
        rx.box(
            rx.hstack(
                rx.icon(tag="calendar_x", size=14, color="var(--twk-danger-text)"),
                rx.text("Vencimientos: " + FoodState.inv_alertas_vencimiento_texto,
                        font_size="12px", color="var(--twk-danger-text)", font_weight="600"),
                spacing="2", align="center",
            ),
            background="rgba(239,68,68,0.08)", border="1px solid #FECACA",
            border_radius="10px", padding="10px 14px", width="100%",
        ),
        rx.fragment(),
    )


def _mov_insumo_modal() -> rx.Component:
    es_merma = FoodState.inv_mov_tipo == "merma"
    es_ajuste = FoodState.inv_mov_tipo == "ajuste"
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.dialog.title(
                    rx.cond(es_merma, "Registrar merma — ",
                            rx.cond(es_ajuste, "Ajuste de conteo — ", "Entrada de stock — "))
                    + FoodState.inv_mov_insumo_nombre,
                    font_size="16px", font_weight="800", color=TEXT_PRIMARY, margin="0",
                ),
                rx.hstack(
                    rx.select(
                        ["entrada", "merma", "ajuste"],
                        value=FoodState.inv_mov_tipo,
                        on_change=FoodState.set_inv_mov_tipo,
                        width="130px",
                    ),
                    rx.input(
                        placeholder=rx.cond(es_ajuste, "Stock contado", "Cantidad"),
                        value=FoodState.inv_mov_cantidad,
                        on_change=FoodState.set_inv_mov_cantidad,
                        type="number", min="0", step="0.001",
                        flex="1",
                        background=PAGE_BACKGROUND, border=f"1px solid {DARK_700}",
                        border_radius="7px", font_size="13px",
                        _focus={"border_color": "#EA580C"},
                    ),
                    spacing="2", width="100%", align="center",
                ),
                rx.cond(
                    es_merma,
                    rx.select(
                        FoodState.inv_categorias_merma,
                        value=FoodState.inv_mov_merma_categoria,
                        on_change=FoodState.set_inv_mov_merma_categoria,
                        width="100%",
                    ),
                    rx.fragment(),
                ),
                rx.input(
                    placeholder=rx.cond(
                        es_merma, "Detalle de la merma (obligatorio si es 'Otro')",
                        "Motivo (opcional)",
                    ),
                    value=FoodState.inv_mov_motivo,
                    on_change=FoodState.set_inv_mov_motivo,
                    width="100%",
                    background=PAGE_BACKGROUND, border=f"1px solid {DARK_700}",
                    border_radius="7px", font_size="13px",
                    _focus={"border_color": "#EA580C"},
                ),
                rx.cond(
                    FoodState.inv_mov_error != "",
                    rx.text(FoodState.inv_mov_error, font_size="12px",
                            color="var(--twk-danger-text)", font_weight="600"),
                    rx.fragment(),
                ),
                rx.hstack(
                    rx.button(
                        "Cancelar",
                        on_click=FoodState.set_inv_mov_modal_visible(False),
                        background=DARK_800, color=TEXT_MUTED,
                        border=f"1px solid {DARK_700}", border_radius="8px",
                        font_size="13px", font_weight="600", cursor="pointer", flex="1",
                    ),
                    rx.button(
                        "Registrar movimiento",
                        on_click=FoodState.guardar_mov_insumo,
                        background=ACCENT, color=TEXT_WHITE,
                        border_radius="8px", font_size="13px", font_weight="700",
                        cursor="pointer", _hover={"background": ACCENT_HOVER}, flex="2",
                    ),
                    spacing="2", width="100%",
                ),
                spacing="3", width="100%",
            ),
            max_width="460px",
            width="92vw",
            max_height="90vh",
            overflow_y="auto",
            background=PAGE_BACKGROUND, border=f"1px solid {DARK_800}",
        ),
        open=FoodState.inv_mov_modal_visible,
        on_open_change=FoodState.set_inv_mov_modal_visible,
    )


def _kardex_row(mov) -> rx.Component:
    return rx.hstack(
        rx.vstack(
            rx.hstack(
                rx.badge(
                    mov.tipo_label,
                    background=rx.cond(mov.es_entrada, "rgba(34,197,94,0.12)", "rgba(239,68,68,0.12)"),
                    color=rx.cond(mov.es_entrada, "#22C55E", "var(--twk-danger-text)"),
                    border_radius="6px", font_size="10px", font_weight="700",
                ),
                rx.text(mov.fecha_texto, font_size="11px", color=TEXT_MUTED),
                spacing="2", align="center",
            ),
            rx.cond(
                mov.motivo != "",
                rx.text(mov.motivo + " · " + mov.usuario, font_size="11px", color=TEXT_MUTED),
                rx.text(mov.usuario, font_size="11px", color=TEXT_MUTED),
            ),
            spacing="0", align="start",
        ),
        rx.spacer(),
        rx.vstack(
            rx.text(mov.cantidad_texto, font_size="13px", font_weight="800",
                    color=rx.cond(mov.es_entrada, "#16A34A", "#DC2626"), text_align="right"),
            rx.text("Saldo: " + mov.stock_resultante_texto, font_size="11px",
                    color=TEXT_MUTED, text_align="right"),
            spacing="0", align="end",
        ),
        width="100%", align="center", gap="8px",
        padding="8px 10px", border_bottom=f"1px solid {DARK_800}",
    )


def _kardex_modal() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.hstack(
                    rx.dialog.title("Kardex — " + FoodState.inv_kardex_insumo_nombre,
                            font_size="16px", font_weight="800", color=TEXT_PRIMARY, margin="0"),
                    rx.spacer(),
                    rx.icon(tag="x", size=18, color=TEXT_MUTED, cursor="pointer",
                            on_click=FoodState.set_inv_kardex_visible(False)),
                    width="100%", align="center",
                ),
                rx.box(
                    rx.cond(
                        FoodState.inv_kardex_movimientos.length() > 0,
                        rx.vstack(
                            rx.foreach(FoodState.inv_kardex_movimientos, _kardex_row),
                            spacing="0", width="100%",
                        ),
                        rx.center(
                            rx.text("Sin movimientos registrados.", font_size="13px", color=TEXT_MUTED),
                            padding_y="20px", width="100%",
                        ),
                    ),
                    max_height="420px", overflow_y="auto", width="100%",
                    border=f"1px solid {DARK_800}", border_radius="10px",
                ),
                rx.text("Últimos 50 movimientos.", font_size="11px", color=TEXT_MUTED),
                spacing="3", width="100%",
            ),
            max_width="560px",
            width="92vw",
            max_height="90vh",
            overflow_y="auto",
            background=PAGE_BACKGROUND, border=f"1px solid {DARK_800}",
        ),
        open=FoodState.inv_kardex_visible,
        on_open_change=FoodState.set_inv_kardex_visible,
    )


def _insumos_table_header() -> rx.Component:
    return rx.grid(
        rx.text("Producto", font_size="11px", font_weight="600", color=TEXT_MUTED,
                text_transform="uppercase", letter_spacing="0.05em"),
        rx.text("Stock actual", font_size="11px", font_weight="600", color=TEXT_MUTED,
                text_transform="uppercase", letter_spacing="0.05em"),
        rx.text("Unidad", font_size="11px", font_weight="600", color=TEXT_MUTED,
                text_transform="uppercase", letter_spacing="0.05em"),
        rx.text("Stock mínimo", font_size="11px", font_weight="600", color=TEXT_MUTED,
                text_transform="uppercase", letter_spacing="0.05em"),
        rx.text("Acción", font_size="11px", font_weight="600", color=TEXT_MUTED,
                text_transform="uppercase", letter_spacing="0.05em", text_align="right"),
        columns=_INV_GRID_COLS,
        gap="8px", width="100%",
        padding="0 10px 8px", border_bottom=f"1px solid {DARK_800}",
        display=rx.breakpoints(initial="none", md="grid"),
    )


def _insumo_row(ins: InsumoView) -> rx.Component:
    return rx.grid(
        rx.hstack(
            rx.box(
                width="8px", height="8px", border_radius="full",
                background=rx.cond(
                    ins.bajo_stock, "#EF4444",
                    rx.cond(ins.activo, "#22C55E", "var(--twk-slate-400)"),
                ),
                flex_shrink="0",
            ),
            rx.text(ins.nombre, font_size="13px", font_weight="600", color=TEXT_PRIMARY,
                    overflow="hidden", text_overflow="ellipsis", white_space="nowrap"),
            spacing="2", align="center", min_width="0",
        ),
        rx.vstack(
            rx.badge(
                ins.stock_texto,
                background=rx.cond(ins.bajo_stock, "rgba(239,68,68,0.12)", "rgba(34,197,94,0.12)"),
                color=rx.cond(ins.bajo_stock, "#DC2626", "#16A34A"),
                border_radius="20px", font_size="12px", font_weight="700",
                padding="3px 10px", width="fit-content",
            ),
            rx.cond(
                ins.vencimiento_estado != "",
                rx.badge(
                    rx.cond(ins.vencimiento_estado == "vencido", "Vencido ", "Vence ")
                    + ins.vencimiento_texto,
                    background=rx.cond(ins.vencimiento_estado == "vencido", "rgba(239,68,68,0.12)", "rgba(245,158,11,0.12)"),
                    color=rx.cond(ins.vencimiento_estado == "vencido", "var(--twk-danger-text)", "#F59E0B"),
                    border_radius="20px", font_size="10px", font_weight="700",
                    padding="2px 8px", width="fit-content",
                ),
                rx.fragment(),
            ),
            spacing="1", align="start",
        ),
        rx.text(ins.unidad, font_size="13px", color=TEXT_MUTED,
                display=rx.breakpoints(initial="none", md="block")),
        rx.text(ins.stock_minimo_texto, font_size="13px", color=TEXT_MUTED,
                display=rx.breakpoints(initial="none", md="block")),
        rx.hstack(
            rx.tooltip(
                rx.button(
                    rx.icon(tag="circle_plus", size=15),
                    on_click=FoodState.abrir_mov_insumo(ins.id, "entrada"),
                    background="transparent", color="#16A34A",
                    border="none", padding="2px", cursor="pointer",
                    _hover={"opacity": "0.7"},
                ),
                content="Registrar entrada / compra",
            ),
            rx.tooltip(
                rx.button(
                    rx.icon(tag="circle_minus", size=15),
                    on_click=FoodState.abrir_mov_insumo(ins.id, "merma"),
                    background="transparent", color=DANGER_TEXT,
                    border="none", padding="2px", cursor="pointer",
                    _hover={"opacity": "0.7"},
                ),
                content="Registrar merma",
            ),
            rx.tooltip(
                rx.button(
                    rx.icon(tag="scroll_text", size=15),
                    on_click=FoodState.abrir_kardex_insumo(ins.id),
                    background="transparent", color=TEXT_MUTED,
                    border="none", padding="2px", cursor="pointer",
                    _hover={"color": "#EA580C"},
                ),
                content="Ver kardex",
            ),
            rx.tooltip(
                rx.button(
                    rx.icon(tag="pencil", size=15),
                    on_click=FoodState.editar_insumo(ins.id),
                    background="transparent", color=TEXT_MUTED,
                    border="none", padding="2px", cursor="pointer",
                    _hover={"color": "#EA580C"},
                ),
                content="Editar",
            ),
            rx.tooltip(
                switch_toggle(ins.activo, FoodState.toggle_insumo_activo(ins.id)),
                content=rx.cond(ins.activo, "Desactivar insumo", "Activar insumo"),
            ),
            spacing="1", align="center", justify="end", flex_wrap="nowrap", width="100%",
        ),
        columns=rx.breakpoints(initial="1fr auto auto", md=_INV_GRID_COLS),
        gap="8px", width="100%", align_items="center",
        padding="10px", border_radius="8px",
        background=rx.cond(ins.bajo_stock, "rgba(245,158,11,0.10)", "var(--twk-d800)"),
        border=rx.cond(ins.bajo_stock, "1px solid rgba(245,158,11,0.25)", f"1px solid {DARK_700}"),
        _hover={"background": rx.cond(ins.bajo_stock, "rgba(245,158,11,0.15)", "var(--twk-d700)")},
    )


def _insumo_form() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.icon(
                    tag=rx.cond(FoodState.inv_form_editando, "pencil", "plus"),
                    size=13,
                    color=ACCENT,
                ),
                rx.text(
                    rx.cond(FoodState.inv_form_editando, "Editar insumo", "Nuevo insumo"),
                    font_size="13px",
                    font_weight="700",
                    color=TEXT_PRIMARY,
                ),
                spacing="1",
                align="center",
            ),
            rx.hstack(
                rx.vstack(
                    rx.text("Nombre", font_size="11px", font_weight="600", color=TEXT_MUTED),
                    rx.input(
                        placeholder="Ej: Harina de trigo",
                        value=FoodState.inv_form_nombre,
                        on_change=FoodState.set_inv_form_nombre,
                        background=PAGE_BACKGROUND,
                        border=f"1px solid {DARK_700}",
                        border_radius="7px",
                        font_size="13px",
                        padding_x="10px",
                        padding_y="8px",
                        width="100%",
                        _focus={"border": f"1px solid {ACCENT}"},
                    ),
                    spacing="1",
                    align="start",
                    flex="2",
                ),
                rx.vstack(
                    rx.text("Unidad", font_size="11px", font_weight="600", color=TEXT_MUTED),
                    rx.select(
                        ["unidad", "kg", "gramos", "litros", "ml", "porción"],
                        value=FoodState.inv_form_unidad,
                        on_change=FoodState.set_inv_form_unidad,
                        background=PAGE_BACKGROUND,
                        border=f"1px solid {DARK_700}",
                        border_radius="7px",
                        font_size="13px",
                        width="100%",
                    ),
                    spacing="1",
                    align="start",
                    flex="1",
                ),
                spacing="3",
                width="100%",
                class_name="twk-form-row",
            ),
            rx.hstack(
                rx.vstack(
                    rx.text("Stock actual", font_size="11px", font_weight="600", color=TEXT_MUTED),
                    rx.input(
                        placeholder="0",
                        value=FoodState.inv_form_stock_actual,
                        on_change=FoodState.set_inv_form_stock_actual,
                        type="number",
                        background=PAGE_BACKGROUND,
                        border=f"1px solid {DARK_700}",
                        border_radius="7px",
                        font_size="13px",
                        padding_x="10px",
                        padding_y="8px",
                        width="100%",
                        _focus={"border": f"1px solid {ACCENT}"},
                    ),
                    spacing="1",
                    align="start",
                    flex="1",
                ),
                rx.vstack(
                    rx.text("Stock mínimo (alerta)", font_size="11px", font_weight="600", color=TEXT_MUTED),
                    rx.input(
                        placeholder="0",
                        value=FoodState.inv_form_stock_minimo,
                        on_change=FoodState.set_inv_form_stock_minimo,
                        type="number",
                        background=PAGE_BACKGROUND,
                        border=f"1px solid {DARK_700}",
                        border_radius="7px",
                        font_size="13px",
                        padding_x="10px",
                        padding_y="8px",
                        width="100%",
                        _focus={"border": f"1px solid {ACCENT}"},
                    ),
                    spacing="1",
                    align="start",
                    flex="1",
                ),
                rx.vstack(
                    rx.text("Costo por unidad S/", font_size="11px", font_weight="600", color=TEXT_MUTED),
                    rx.input(
                        placeholder="0.00",
                        value=FoodState.inv_form_costo,
                        on_change=FoodState.set_inv_form_costo,
                        type="number", min="0", step="0.01",
                        background=PAGE_BACKGROUND,
                        border=f"1px solid {DARK_700}",
                        border_radius="7px",
                        font_size="13px",
                        padding_x="10px",
                        padding_y="8px",
                        width="100%",
                        _focus={"border": f"1px solid {ACCENT}"},
                    ),
                    spacing="1",
                    align="start",
                    flex="1",
                ),
                rx.vstack(
                    rx.text("Vencimiento (opcional)", font_size="11px", font_weight="600", color=TEXT_MUTED),
                    rx.input(
                        value=FoodState.inv_form_vencimiento,
                        on_change=FoodState.set_inv_form_vencimiento,
                        type="date",
                        background=PAGE_BACKGROUND,
                        border=f"1px solid {DARK_700}",
                        border_radius="7px",
                        font_size="13px",
                        padding_x="10px",
                        padding_y="8px",
                        width="100%",
                        _focus={"border": f"1px solid {ACCENT}"},
                    ),
                    spacing="1",
                    align="start",
                    flex="1",
                ),
                spacing="3",
                width="100%",
                class_name="twk-form-row",
            ),
            rx.hstack(
                rx.button(
                    rx.cond(FoodState.inv_form_editando, "Actualizar", "Agregar"),
                    on_click=FoodState.guardar_insumo,
                    background=ACCENT,
                    color=TEXT_WHITE,
                    border_radius="7px",
                    font_size="13px",
                    font_weight="700",
                    padding_x="16px",
                    padding_y="8px",
                    cursor="pointer",
                    _hover={"background": ACCENT_HOVER},
                ),
                rx.button(
                    "Cancelar",
                    on_click=FoodState.cancelar_insumo_form,
                    background=DARK_800,
                    color=TEXT_MUTED,
                    border=f"1px solid {DARK_700}",
                    border_radius="7px",
                    font_size="13px",
                    padding_x="16px",
                    padding_y="8px",
                    cursor="pointer",
                    _hover={"background": DARK_700},
                ),
                spacing="2",
                justify="end",
                width="100%",
            ),
            spacing="3",
            width="100%",
        ),
        background=PAGE_BACKGROUND,
        border=f"1px solid {DARK_700}",
        border_radius="8px",
        padding="12px 14px",
        width="100%",
    )


def _insumos_section() -> rx.Component:
    return _section_card(
        "Insumos / Ingredientes",
        "package",
        rx.hstack(
            rx.input(
                placeholder="Buscar insumo...",
                value=FoodState.inv_search,
                on_change=FoodState.set_inv_search,
                background=PAGE_BACKGROUND, border=f"1px solid {DARK_700}",
                border_radius="8px", font_size="13px",
                padding_x="10px", padding_y="7px",
                width=rx.breakpoints(initial="100%", sm="240px"),
                _focus={"border": f"1px solid {ACCENT}"},
            ),
            rx.spacer(),
            rx.dialog.root(
                rx.button(
                    rx.hstack(
                        rx.icon(tag="plus", size=13),
                        rx.text("Agregar", font_size="13px", font_weight="700"),
                        spacing="1", align="center",
                    ),
                    on_click=FoodState.abrir_nuevo_insumo,
                    background=ACCENT, color=TEXT_WHITE,
                    border_radius="8px", padding_x="14px", padding_y="8px",
                    cursor="pointer", _hover={"background": ACCENT_HOVER},
                ),
                rx.dialog.content(
                    rx.dialog.title("Insumo", visibility="hidden", height="0", margin="0", padding="0"),
                    _insumo_form(),
                    max_width="560px",
                    width="92vw",
                    max_height="90vh",
                    overflow_y="auto",
                    background=PAGE_BACKGROUND, border=f"1px solid {DARK_800}",
                ),
                open=FoodState.inv_form_visible,
                on_open_change=FoodState.set_inv_form_visible,
            ),
            width="100%", align="center", wrap="wrap", gap="8px",
        ),
        _insumos_table_header(),
        rx.cond(
            FoodState.inv_insumos_filtrados.length() > 0,
            rx.vstack(
                rx.foreach(FoodState.inv_insumos_filtrados, _insumo_row),
                spacing="1",
                width="100%",
            ),
            empty_state(
                icono="package",
                titulo="Sin insumos registrados",
                texto="Da de alta tus insumos para controlar stock, mermas y alertas de reposición.",
                cta_label="Nuevo insumo",
                cta_on_click=FoodState.abrir_nuevo_insumo,
            ),
        ),
        rx.button(
            rx.hstack(
                rx.icon(tag="refresh_cw", size=12),
                rx.text("Actualizar", font_size="12px"),
                spacing="1",
                align="center",
            ),
            on_click=FoodState.cargar_inventario,
            background=DARK_800,
            color=TEXT_MUTED,
            border=f"1px solid {DARK_700}",
            border_radius="7px",
            cursor="pointer",
            align_self="end",
            _hover={"background": DARK_700},
        ),
    )


# ── Recetas ──────────────────────────────────────────────────────────────────

def _receta_item_row(item: RecetaItemView) -> rx.Component:
    return rx.hstack(
        rx.text(item.insumo_nombre, font_size="13px", color=TEXT_PRIMARY, flex="1"),
        rx.badge(
            item.cantidad_texto,
            background="rgba(59,130,246,0.08)",
            color="var(--twk-info-text)",
            border_radius="5px",
            font_size="11px",
            padding="2px 7px",
        ),
        rx.tooltip(
            rx.button(
                rx.icon(tag="trash_2", size=12),
                on_click=FoodState.eliminar_receta_item(item.id),
                background="rgba(239,68,68,0.08)",
                color="var(--twk-danger-text)",
                border="1px solid #FECACA",
                border_radius="6px",
                padding="4px 7px",
                cursor="pointer",
                _hover={"opacity": "0.8"},
            ),
            content="Quitar ingrediente",
        ),
        width="100%",
        align="center",
        padding="6px 8px",
        background=DARK_800,
        border_radius="7px",
        border=f"1px solid {DARK_800}",
        gap="8px",
    )


def _receta_add_form() -> rx.Component:
    return rx.hstack(
        rx.select(
            FoodState.inv_insumos_activos_nombres,
            placeholder="Insumo…",
            value=FoodState.inv_receta_insumo_sel_nombre,
            on_change=FoodState.set_inv_receta_insumo_sel_nombre,
            background=PAGE_BACKGROUND,
            border=f"1px solid {DARK_700}",
            border_radius="7px",
            font_size="13px",
            flex="2",
        ),
        rx.input(
            placeholder="Cantidad",
            value=FoodState.inv_receta_cantidad,
            on_change=FoodState.set_inv_receta_cantidad,
            type="number",
            background=PAGE_BACKGROUND,
            border=f"1px solid {DARK_700}",
            border_radius="7px",
            font_size="13px",
            padding_x="10px",
            padding_y="8px",
            flex="1",
            _focus={"border": f"1px solid {ACCENT}"},
        ),
        rx.button(
            rx.icon(tag="plus", size=14),
            on_click=FoodState.guardar_receta_item,
            background=ACCENT,
            color=TEXT_WHITE,
            border_radius="7px",
            padding="8px 12px",
            cursor="pointer",
            _hover={"background": ACCENT_HOVER},
            flex_shrink="0",
        ),
        spacing="2",
        width="100%",
        align="center",
    )


def _recetas_section() -> rx.Component:
    return _section_card(
        "Recetas por producto",
        "book_open",
        rx.text(
            "Vincula ingredientes (insumos) a cada plato. El stock se descuenta automáticamente al cobrar.",
            font_size="12px",
            color=TEXT_MUTED,
        ),
        rx.vstack(
            rx.text("Seleccionar producto", font_size="11px", font_weight="600", color=TEXT_MUTED),
            rx.select(
                FoodState.inv_productos_nombres,
                placeholder="Elige un plato…",
                value=FoodState.inv_producto_sel_nombre,
                on_change=FoodState.set_inv_producto_sel_nombre,
                background=PAGE_BACKGROUND,
                border=f"1px solid {DARK_700}",
                border_radius="7px",
                font_size="13px",
                width="100%",
            ),
            spacing="1",
            align="start",
            width="100%",
        ),
        rx.cond(
            FoodState.inv_producto_sel_id > 0,
            rx.vstack(
                rx.cond(
                    FoodState.inv_receta_items.length() > 0,
                    rx.vstack(
                        rx.foreach(FoodState.inv_receta_items, _receta_item_row),
                        spacing="1",
                        width="100%",
                    ),
                    rx.center(
                        rx.vstack(
                            rx.text(
                                "Sin ingredientes en la receta. Agrega uno abajo.",
                                font_size="12px",
                                color=TEXT_MUTED,
                            ),
                            rx.text(
                                "Sin receta el producto se vende igual, pero no descuenta stock.",
                                font_size="11px",
                                color=TEXT_MUTED,
                                font_style="italic",
                            ),
                            spacing="1",
                            align="center",
                        ),
                        padding_y="10px",
                        width="100%",
                    ),
                ),
                rx.box(
                    rx.vstack(
                        rx.text(
                            "Agregar ingrediente",
                            font_size="12px",
                            font_weight="600",
                            color=TEXT_MUTED,
                        ),
                        _receta_add_form(),
                        spacing="2",
                        width="100%",
                    ),
                    background=PAGE_BACKGROUND,
                    border=f"1px solid {DARK_700}",
                    border_radius="8px",
                    padding="10px 12px",
                    width="100%",
                ),
                spacing="3",
                width="100%",
            ),
            rx.fragment(),
        ),
    )


# ── Planificador de producción ───────────────────────────────────────────────

def _plan_item_row(item: ProduccionPlanItem) -> rx.Component:
    return rx.hstack(
        rx.text(item.nombre, font_size="13px", color=TEXT_PRIMARY, font_weight="600", flex="1"),
        rx.badge(
            rx.text(item.cantidad, font_size="12px"),
            background="rgba(59,130,246,0.08)", color="var(--twk-info-text)",
            border_radius="5px", padding="2px 10px",
        ),
        rx.tooltip(
            rx.button(
                rx.icon(tag="x", size=12),
                on_click=FoodState.prod_quitar_item(item.producto_id),
                background="rgba(239,68,68,0.08)", color="var(--twk-danger-text)",
                border="1px solid #FECACA", border_radius="6px",
                padding="4px 7px", cursor="pointer",
                _hover={"opacity": "0.8"},
            ),
            content="Quitar producto",
        ),
        width="100%", align="center",
        padding="6px 8px", background=DARK_800,
        border_radius="7px", border=f"1px solid {DARK_800}", gap="8px",
    )


def _resultado_row(nec: ProduccionNecesidadView) -> rx.Component:
    es_faltante = nec.estado == "faltante"
    return rx.grid(
        rx.text(nec.nombre, font_size="13px", font_weight="600", color=TEXT_PRIMARY,
                overflow="hidden", text_overflow="ellipsis", white_space="nowrap"),
        rx.text(nec.cantidad_necesaria_texto, font_size="13px", color="var(--twk-slate-300)",
                text_align="right"),
        rx.text(nec.stock_actual_texto, font_size="13px", color=TEXT_MUTED,
                text_align="right"),
        rx.text(
            nec.faltante_texto, font_size="13px", font_weight="700",
            color=rx.cond(es_faltante, "#DC2626", "#16A34A"),
            text_align="right",
        ),
        rx.text(nec.costo_estimado_texto, font_size="13px", color="var(--twk-slate-300)",
                text_align="right"),
        rx.box(
            width="10px", height="10px", border_radius="full",
            background=rx.cond(es_faltante, "#EF4444", "#22C55E"),
            flex_shrink="0",
        ),
        columns="2fr 1fr 1fr 1fr 1fr 30px",
        gap="8px", width="100%", align_items="center",
        padding="8px 10px", border_radius="6px",
        background=rx.cond(es_faltante, "rgba(239,68,68,0.10)", "var(--twk-d800)"),
        border=rx.cond(es_faltante, "1px solid rgba(239,68,68,0.25)", f"1px solid {DARK_700}"),
    )


def _resultado_header() -> rx.Component:
    cols = ["Insumo", "Necesario", "En stock", "Faltante", "Costo est.", ""]
    return rx.grid(
        *[rx.text(c, font_size="11px", font_weight="600", color=TEXT_MUTED,
                  text_transform="uppercase", letter_spacing="0.05em",
                  text_align="right" if i > 0 else "left")
          for i, c in enumerate(cols)],
        columns="2fr 1fr 1fr 1fr 1fr 30px",
        gap="8px", width="100%",
        padding="0 10px 6px", border_bottom=f"1px solid {DARK_800}",
        display=rx.breakpoints(initial="none", md="grid"),
    )


def _produccion_section() -> rx.Component:
    return _section_card(
        "Planificador de producción",
        "calculator",
        rx.text(
            "Arma el plan del día: elige productos con sus cantidades y calcula los insumos necesarios.",
            font_size="12px", color=TEXT_MUTED,
        ),
        # Formulario para agregar productos al plan
        rx.hstack(
            rx.select(
                FoodState.prod_opciones_productos,
                placeholder="Selecciona producto o combo…",
                value=FoodState.prod_agregar_nombre,
                on_change=FoodState.set_prod_agregar_nombre,
                background=PAGE_BACKGROUND, border=f"1px solid {DARK_700}",
                border_radius="7px", font_size="13px", flex="2",
            ),
            rx.input(
                placeholder="Cant.",
                value=FoodState.prod_agregar_cantidad,
                on_change=FoodState.set_prod_agregar_cantidad,
                type="number", min="1", step="1",
                background=PAGE_BACKGROUND, border=f"1px solid {DARK_700}",
                border_radius="7px", font_size="13px",
                padding_x="10px", padding_y="8px",
                width="80px",
                _focus={"border": f"1px solid {ACCENT}"},
            ),
            rx.button(
                rx.hstack(
                    rx.icon(tag="plus", size=13),
                    rx.text("Agregar", font_size="13px", font_weight="700"),
                    spacing="1", align="center",
                ),
                on_click=FoodState.prod_agregar_item,
                background=ACCENT, color=TEXT_WHITE,
                border_radius="7px", padding_x="14px", padding_y="8px",
                cursor="pointer", _hover={"background": ACCENT_HOVER},
                flex_shrink="0",
            ),
            spacing="2", width="100%", align="center", wrap="wrap",
        ),
        # Lista del plan actual
        rx.cond(
            FoodState.prod_plan_items.length() > 0,
            rx.vstack(
                rx.hstack(
                    rx.text("Plan del día", font_size="12px", font_weight="700", color=TEXT_PRIMARY),
                    rx.spacer(),
                    rx.button(
                        rx.hstack(
                            rx.icon(tag="trash_2", size=11),
                            rx.text("Limpiar", font_size="11px"),
                            spacing="1", align="center",
                        ),
                        on_click=FoodState.prod_limpiar_plan,
                        background=DARK_800, color=TEXT_MUTED,
                        border=f"1px solid {DARK_700}", border_radius="6px",
                        padding="4px 10px", cursor="pointer",
                        _hover={"background": DARK_700},
                    ),
                    width="100%", align="center",
                ),
                rx.foreach(FoodState.prod_plan_items, _plan_item_row),
                rx.button(
                    rx.hstack(
                        rx.icon(tag="calculator", size=14),
                        rx.text("Calcular insumos necesarios", font_size="13px", font_weight="700"),
                        spacing="2", align="center",
                    ),
                    on_click=FoodState.prod_calcular,
                    background="var(--twk-info-text)", color=TEXT_WHITE,
                    border_radius="8px", padding_x="20px", padding_y="10px",
                    cursor="pointer", width="100%",
                    _hover={"background": "#3B82F6"},
                ),
                spacing="2", width="100%",
            ),
            rx.fragment(),
        ),
        # Resultados
        rx.cond(
            FoodState.prod_calculado,
            rx.vstack(
                rx.hstack(
                    rx.text("Resultado de explosión", font_size="14px", font_weight="800", color=TEXT_PRIMARY),
                    rx.spacer(),
                    rx.cond(
                        FoodState.prod_faltantes_count > 0,
                        rx.badge(
                            rx.text(FoodState.prod_faltantes_count, font_size="11px"),
                            " faltante(s)",
                            background="rgba(239,68,68,0.12)", color=DANGER_TEXT,
                            border_radius="20px", font_size="11px", font_weight="700",
                            padding="3px 10px",
                        ),
                        rx.badge(
                            "Stock suficiente",
                            background="rgba(34,197,94,0.12)", color=SUCCESS_TEXT,
                            border_radius="20px", font_size="11px", font_weight="700",
                            padding="3px 10px",
                        ),
                    ),
                    width="100%", align="center",
                ),
                rx.cond(
                    FoodState.prod_resultado.length() > 0,
                    rx.vstack(
                        _resultado_header(),
                        rx.foreach(FoodState.prod_resultado, _resultado_row),
                        spacing="1", width="100%",
                    ),
                    rx.center(
                        rx.text(
                            "Sin resultados. Verifica que los productos tengan recetas cargadas.",
                            font_size="13px", color=TEXT_MUTED,
                        ),
                        padding_y="12px", width="100%",
                    ),
                ),
                rx.box(
                    rx.hstack(
                        rx.text("Costo total estimado del plan:", font_size="14px",
                                font_weight="700", color=TEXT_PRIMARY),
                        rx.spacer(),
                        rx.text(FoodState.prod_costo_total_texto, font_size="18px",
                                font_weight="800", color="var(--twk-info-text)"),
                        width="100%", align="center",
                    ),
                    background="rgba(59,130,246,0.08)", border="1px solid #BFDBFE",
                    border_radius="10px", padding="12px 16px", width="100%",
                ),
                spacing="3", width="100%",
                background=PAGE_BACKGROUND, border=f"1px solid {DARK_700}",
                border_radius="10px", padding="14px 16px",
            ),
            rx.fragment(),
        ),
    )


# ── Contenido principal ──────────────────────────────────────────────────────

def _inventario_ayuda() -> rx.Component:
    return ayuda_modal(
        titulo="¿Cómo funciona Inventario?",
        subtitulo="Insumos, stock y alertas de reposición",
        secciones=[
            {"titulo": "Insumos y stock", "pasos": [
                "Da de alta cada insumo con su unidad y su stock mínimo.",
                "Registra entradas (compras) con «+» y mermas con «−» en cada insumo.",
                "El sistema te avisa cuando un insumo baja del mínimo o está por vencer.",
            ]},
            {"titulo": "Recetas y producción", "pasos": [
                "Asocia insumos a cada plato en «Recetas» para descontar stock al vender.",
                "En «Producción» armas preparaciones que consumen insumos y generan stock.",
            ]},
            {"titulo": "Kardex", "pasos": [
                "El ícono de historial abre el kardex: todos los movimientos del insumo.",
            ]},
        ],
        leyenda=[
            ("#EF4444", "Bajo stock"),
            ("#22C55E", "Stock OK"),
            ("var(--twk-slate-400)", "Inactivo"),
        ],
    )


def _inventario_tabs() -> rx.Component:
    """Insumos / Recetas / Producción como pestañas (M-10c): dejan claro que son
    tres herramientas distintas en vez de una página larga apilada. El estado de
    la pestaña activa lo maneja el propio componente (client-side), sin tocar
    FoodState."""
    _trigger_style = {
        "font_size": "13px",
        "font_weight": "700",
        "color": TEXT_MUTED,
        "padding": "10px 16px",
        "cursor": "pointer",
        "white_space": "nowrap",
        "&[data-state='active']": {
            "color": TEXT_PRIMARY,
            "box_shadow": f"inset 0 -2px 0 {ACCENT}",
        },
    }
    return rx.tabs.root(
        rx.box(
            rx.tabs.list(
                rx.tabs.trigger("Insumos", value="insumos", style=_trigger_style),
                rx.tabs.trigger("Recetas", value="recetas", style=_trigger_style),
                rx.tabs.trigger("Producción", value="produccion", style=_trigger_style),
            ),
            overflow_x="auto",
            width="100%",
        ),
        rx.tabs.content(_insumos_section(), value="insumos", padding_top="16px"),
        rx.tabs.content(_recetas_section(), value="recetas", padding_top="16px"),
        rx.tabs.content(_produccion_section(), value="produccion", padding_top="16px"),
        default_value="insumos",
        width="100%",
    )


def _inventario_content() -> rx.Component:
    return rx.vstack(
        rx.cond(
            FoodState.es_pagina_standalone,
            rx.hstack(
                rx.link(
                    rx.hstack(
                        rx.icon(tag="arrow_left", size=13, color=TEXT_MUTED),
                        rx.text("Panel Administrativo", font_size="12px", color=TEXT_MUTED),
                        spacing="1",
                        align="center",
                    ),
                    href="/admin",
                    _hover={"opacity": "0.7"},
                ),
                rx.spacer(),
                width="100%",
                align="center",
            ),
            rx.fragment(),
        ),
        rx.hstack(
            rx.vstack(
                rx.text(
                    "Inventario",
                    font_size="22px",
                    font_weight="800",
                    color=TEXT_PRIMARY,
                ),
                rx.text("Insumos, stock y alertas de reposición",
                        font_size="13px", color=TEXT_MUTED),
                spacing="0",
            ),
            rx.spacer(),
            ayuda_trigger(),
            width="100%", align="center",
        ),
        _inventario_ayuda(),
        _alerta_bajo_stock(),
        _alerta_vencimientos(),
        _inventario_tabs(),
        _mov_insumo_modal(),
        _kardex_modal(),
        spacing="4",
        width="100%",
    )


# ── Página ───────────────────────────────────────────────────────────────────

@rx.page(
    route="/inventario",
    on_load=[AdminLocalState.on_load_dono, FoodState.on_load_inventario],
    title="TUWAYKIFOOD | Inventario",
)
def inventario_page() -> rx.Component:
    return _dono_shell(_inventario_content())
