"""Página de gestión de inventario — insumos y recetas."""

from __future__ import annotations

import reflex as rx

from app.states.food_state import FoodState, InsumoView, RecetaItemView
from app.states.food_state import AdminLocalState
from app.pages.dono import _dono_shell


# ── Helpers de estilo ────────────────────────────────────────────────────────

def _section_card(title: str, icon: str, *children) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.icon(tag=icon, size=15, color="#EA580C"),
                rx.text(title, font_size="15px", font_weight="700", color="#0F172A"),
                spacing="2",
                align="center",
            ),
            *children,
            spacing="4",
            width="100%",
        ),
        background="#FFFFFF",
        border="1px solid #E2E8F0",
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
                        color="#92400E",
                    ),
                    rx.text(
                        rx.foreach(
                            FoodState.inv_alertas_bajo_stock,
                            lambda n: rx.text(n, font_size="12px", color="#78350F"),
                        ),
                    ),
                    spacing="1",
                    align="start",
                ),
                spacing="3",
                align="start",
                width="100%",
            ),
            background="#FFFBEB",
            border="1px solid #FDE68A",
            border_radius="10px",
            padding="12px 14px",
            width="100%",
        ),
        rx.fragment(),
    )


# ── Tabla de insumos ─────────────────────────────────────────────────────────

_INV_GRID_COLS = "2fr 1fr 1fr 1fr 90px"


def _alerta_vencimientos() -> rx.Component:
    return rx.cond(
        FoodState.inv_alertas_vencimiento.length() > 0,
        rx.box(
            rx.hstack(
                rx.icon(tag="calendar_x", size=14, color="#B91C1C"),
                rx.text("Vencimientos: " + FoodState.inv_alertas_vencimiento_texto,
                        font_size="12px", color="#B91C1C", font_weight="600"),
                spacing="2", align="center",
            ),
            background="#FEF2F2", border="1px solid #FECACA",
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
                rx.text(
                    rx.cond(es_merma, "Registrar merma — ",
                            rx.cond(es_ajuste, "Ajuste de conteo — ", "Entrada de stock — "))
                    + FoodState.inv_mov_insumo_nombre,
                    font_size="16px", font_weight="800", color="#0F172A",
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
                        background="#F8FAFC", border="1px solid #E2E8F0",
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
                    background="#F8FAFC", border="1px solid #E2E8F0",
                    border_radius="7px", font_size="13px",
                    _focus={"border_color": "#EA580C"},
                ),
                rx.cond(
                    FoodState.inv_mov_error != "",
                    rx.text(FoodState.inv_mov_error, font_size="12px",
                            color="#B91C1C", font_weight="600"),
                    rx.fragment(),
                ),
                rx.hstack(
                    rx.button(
                        "Cancelar",
                        on_click=FoodState.set_inv_mov_modal_visible(False),
                        background="#FFFFFF", color="#64748B",
                        border="1px solid #E2E8F0", border_radius="8px",
                        font_size="13px", font_weight="600", cursor="pointer", flex="1",
                    ),
                    rx.button(
                        "Registrar movimiento",
                        on_click=FoodState.guardar_mov_insumo,
                        background="#EA580C", color="#FFFFFF",
                        border_radius="8px", font_size="13px", font_weight="700",
                        cursor="pointer", _hover={"background": "#C2410C"}, flex="2",
                    ),
                    spacing="2", width="100%",
                ),
                spacing="3", width="100%",
            ),
            class_name="light", max_width="460px",
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
                    background=rx.cond(mov.es_entrada, "#DCFCE7", "#FEE2E2"),
                    color=rx.cond(mov.es_entrada, "#166534", "#B91C1C"),
                    border_radius="6px", font_size="10px", font_weight="700",
                ),
                rx.text(mov.fecha_texto, font_size="11px", color="#94A3B8"),
                spacing="2", align="center",
            ),
            rx.cond(
                mov.motivo != "",
                rx.text(mov.motivo + " · " + mov.usuario, font_size="11px", color="#64748B"),
                rx.text(mov.usuario, font_size="11px", color="#94A3B8"),
            ),
            spacing="0", align="start",
        ),
        rx.spacer(),
        rx.vstack(
            rx.text(mov.cantidad_texto, font_size="13px", font_weight="800",
                    color=rx.cond(mov.es_entrada, "#16A34A", "#DC2626"), text_align="right"),
            rx.text("Saldo: " + mov.stock_resultante_texto, font_size="11px",
                    color="#64748B", text_align="right"),
            spacing="0", align="end",
        ),
        width="100%", align="center", gap="8px",
        padding="8px 10px", border_bottom="1px solid #F1F5F9",
    )


def _kardex_modal() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.hstack(
                    rx.text("Kardex — " + FoodState.inv_kardex_insumo_nombre,
                            font_size="16px", font_weight="800", color="#0F172A"),
                    rx.spacer(),
                    rx.icon(tag="x", size=18, color="#64748B", cursor="pointer",
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
                            rx.text("Sin movimientos registrados.", font_size="13px", color="#94A3B8"),
                            padding_y="20px", width="100%",
                        ),
                    ),
                    max_height="420px", overflow_y="auto", width="100%",
                    border="1px solid #F1F5F9", border_radius="10px",
                ),
                rx.text("Últimos 50 movimientos.", font_size="11px", color="#94A3B8"),
                spacing="3", width="100%",
            ),
            class_name="light", max_width="560px",
        ),
        open=FoodState.inv_kardex_visible,
        on_open_change=FoodState.set_inv_kardex_visible,
    )


def _insumos_table_header() -> rx.Component:
    return rx.grid(
        rx.text("Producto", font_size="11px", font_weight="600", color="#94A3B8",
                text_transform="uppercase", letter_spacing="0.05em"),
        rx.text("Stock actual", font_size="11px", font_weight="600", color="#94A3B8",
                text_transform="uppercase", letter_spacing="0.05em"),
        rx.text("Unidad", font_size="11px", font_weight="600", color="#94A3B8",
                text_transform="uppercase", letter_spacing="0.05em"),
        rx.text("Stock mínimo", font_size="11px", font_weight="600", color="#94A3B8",
                text_transform="uppercase", letter_spacing="0.05em"),
        rx.text("Acción", font_size="11px", font_weight="600", color="#94A3B8",
                text_transform="uppercase", letter_spacing="0.05em"),
        columns=_INV_GRID_COLS,
        gap="8px", width="100%",
        padding="0 10px 8px", border_bottom="1px solid #F1F5F9",
        display=rx.breakpoints(initial="none", md="grid"),
    )


def _insumo_row(ins: InsumoView) -> rx.Component:
    return rx.grid(
        rx.hstack(
            rx.box(
                width="8px", height="8px", border_radius="full",
                background=rx.cond(
                    ins.bajo_stock, "#EF4444",
                    rx.cond(ins.activo, "#22C55E", "#94A3B8"),
                ),
                flex_shrink="0",
            ),
            rx.text(ins.nombre, font_size="13px", font_weight="600", color="#0F172A",
                    overflow="hidden", text_overflow="ellipsis", white_space="nowrap"),
            spacing="2", align="center", min_width="0",
        ),
        rx.vstack(
            rx.badge(
                ins.stock_texto,
                background=rx.cond(ins.bajo_stock, "#FEE2E2", "#DCFCE7"),
                color=rx.cond(ins.bajo_stock, "#DC2626", "#16A34A"),
                border_radius="20px", font_size="12px", font_weight="700",
                padding="3px 10px", width="fit-content",
            ),
            rx.cond(
                ins.vencimiento_estado != "",
                rx.badge(
                    rx.cond(ins.vencimiento_estado == "vencido", "Vencido ", "Vence ")
                    + ins.vencimiento_texto,
                    background=rx.cond(ins.vencimiento_estado == "vencido", "#FEE2E2", "#FEF3C7"),
                    color=rx.cond(ins.vencimiento_estado == "vencido", "#B91C1C", "#92400E"),
                    border_radius="20px", font_size="10px", font_weight="700",
                    padding="2px 8px", width="fit-content",
                ),
                rx.fragment(),
            ),
            spacing="1", align="start",
        ),
        rx.text(ins.unidad, font_size="13px", color="#64748B",
                display=rx.breakpoints(initial="none", md="block")),
        rx.text(ins.stock_minimo_texto, font_size="13px", color="#64748B",
                display=rx.breakpoints(initial="none", md="block")),
        rx.hstack(
            rx.icon(
                tag="circle_plus", size=15, color="#16A34A", cursor="pointer",
                on_click=FoodState.abrir_mov_insumo(ins.id, "entrada"),
                _hover={"opacity": "0.7"}, title="Registrar entrada / compra",
            ),
            rx.icon(
                tag="circle_minus", size=15, color="#DC2626", cursor="pointer",
                on_click=FoodState.abrir_mov_insumo(ins.id, "merma"),
                _hover={"opacity": "0.7"}, title="Registrar merma",
            ),
            rx.icon(
                tag="scroll_text", size=15, color="#64748B", cursor="pointer",
                on_click=FoodState.abrir_kardex_insumo(ins.id),
                _hover={"color": "#EA580C"}, title="Ver kardex",
            ),
            rx.link(
                "Editar",
                on_click=FoodState.editar_insumo(ins.id),
                font_size="12px", font_weight="600", color="#64748B",
                cursor="pointer", _hover={"color": "#EA580C"},
            ),
            rx.button(
                rx.cond(ins.activo, rx.icon(tag="toggle_right", size=13),
                        rx.icon(tag="toggle_left", size=13)),
                on_click=FoodState.toggle_insumo_activo(ins.id),
                background="transparent",
                color=rx.cond(ins.activo, "#15803D", "#94A3B8"),
                border="none", padding="0", cursor="pointer",
                _hover={"opacity": "0.7"},
            ),
            spacing="2", align="center",
        ),
        columns=rx.breakpoints(initial="1fr auto auto", md=_INV_GRID_COLS),
        gap="8px", width="100%", align_items="center",
        padding="10px", border_radius="8px",
        background=rx.cond(ins.bajo_stock, "#FFFBEB", "#FFFFFF"),
        border=rx.cond(ins.bajo_stock, "1px solid #FDE68A", "1px solid #F1F5F9"),
        _hover={"background": rx.cond(ins.bajo_stock, "#FEF9E7", "#F8FAFC")},
    )


def _insumo_form() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.icon(
                    tag=rx.cond(FoodState.inv_form_editando, "pencil", "plus"),
                    size=13,
                    color="#EA580C",
                ),
                rx.text(
                    rx.cond(FoodState.inv_form_editando, "Editar insumo", "Nuevo insumo"),
                    font_size="13px",
                    font_weight="700",
                    color="#0F172A",
                ),
                spacing="1",
                align="center",
            ),
            rx.hstack(
                rx.vstack(
                    rx.text("Nombre", font_size="11px", font_weight="600", color="#64748B"),
                    rx.input(
                        placeholder="Ej: Harina de trigo",
                        value=FoodState.inv_form_nombre,
                        on_change=FoodState.set_inv_form_nombre,
                        background="#F8FAFC",
                        border="1px solid #E2E8F0",
                        border_radius="7px",
                        font_size="13px",
                        padding_x="10px",
                        padding_y="8px",
                        width="100%",
                        _focus={"border": "1px solid #EA580C"},
                    ),
                    spacing="1",
                    align="start",
                    flex="2",
                ),
                rx.vstack(
                    rx.text("Unidad", font_size="11px", font_weight="600", color="#64748B"),
                    rx.select(
                        ["unidad", "kg", "gramos", "litros", "ml", "porción"],
                        value=FoodState.inv_form_unidad,
                        on_change=FoodState.set_inv_form_unidad,
                        background="#F8FAFC",
                        border="1px solid #E2E8F0",
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
                    rx.text("Stock actual", font_size="11px", font_weight="600", color="#64748B"),
                    rx.input(
                        placeholder="0",
                        value=FoodState.inv_form_stock_actual,
                        on_change=FoodState.set_inv_form_stock_actual,
                        type="number",
                        background="#F8FAFC",
                        border="1px solid #E2E8F0",
                        border_radius="7px",
                        font_size="13px",
                        padding_x="10px",
                        padding_y="8px",
                        width="100%",
                        _focus={"border": "1px solid #EA580C"},
                    ),
                    spacing="1",
                    align="start",
                    flex="1",
                ),
                rx.vstack(
                    rx.text("Stock mínimo (alerta)", font_size="11px", font_weight="600", color="#64748B"),
                    rx.input(
                        placeholder="0",
                        value=FoodState.inv_form_stock_minimo,
                        on_change=FoodState.set_inv_form_stock_minimo,
                        type="number",
                        background="#F8FAFC",
                        border="1px solid #E2E8F0",
                        border_radius="7px",
                        font_size="13px",
                        padding_x="10px",
                        padding_y="8px",
                        width="100%",
                        _focus={"border": "1px solid #EA580C"},
                    ),
                    spacing="1",
                    align="start",
                    flex="1",
                ),
                rx.vstack(
                    rx.text("Vencimiento (opcional)", font_size="11px", font_weight="600", color="#64748B"),
                    rx.input(
                        value=FoodState.inv_form_vencimiento,
                        on_change=FoodState.set_inv_form_vencimiento,
                        type="date",
                        background="#F8FAFC",
                        border="1px solid #E2E8F0",
                        border_radius="7px",
                        font_size="13px",
                        padding_x="10px",
                        padding_y="8px",
                        width="100%",
                        _focus={"border": "1px solid #EA580C"},
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
                    background="#EA580C",
                    color="#FFFFFF",
                    border_radius="7px",
                    font_size="13px",
                    font_weight="700",
                    padding_x="16px",
                    padding_y="8px",
                    cursor="pointer",
                    _hover={"background": "#C2410C"},
                ),
                rx.button(
                    "Cancelar",
                    on_click=FoodState.cancelar_insumo_form,
                    background="#F1F5F9",
                    color="#64748B",
                    border="1px solid #E2E8F0",
                    border_radius="7px",
                    font_size="13px",
                    padding_x="16px",
                    padding_y="8px",
                    cursor="pointer",
                    _hover={"background": "#E2E8F0"},
                ),
                spacing="2",
                justify="end",
                width="100%",
            ),
            spacing="3",
            width="100%",
        ),
        background="#F8FAFC",
        border="1px solid #E2E8F0",
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
                background="#F8FAFC", border="1px solid #E2E8F0",
                border_radius="8px", font_size="13px",
                padding_x="10px", padding_y="7px",
                width=rx.breakpoints(initial="100%", sm="240px"),
                _focus={"border": "1px solid #EA580C"},
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
                    background="#EA580C", color="#FFFFFF",
                    border_radius="8px", padding_x="14px", padding_y="8px",
                    cursor="pointer", _hover={"background": "#C2410C"},
                ),
                rx.dialog.content(_insumo_form(), class_name="light"),
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
            rx.center(
                rx.text("Sin insumos registrados. Agrega el primero.", font_size="13px", color="#94A3B8"),
                padding_y="16px",
                width="100%",
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
            background="#F1F5F9",
            color="#64748B",
            border="1px solid #E2E8F0",
            border_radius="7px",
            cursor="pointer",
            align_self="end",
            _hover={"background": "#E2E8F0"},
        ),
    )


# ── Recetas ──────────────────────────────────────────────────────────────────

def _receta_item_row(item: RecetaItemView) -> rx.Component:
    return rx.hstack(
        rx.text(item.insumo_nombre, font_size="13px", color="#0F172A", flex="1"),
        rx.badge(
            item.cantidad_texto,
            background="#EFF6FF",
            color="#1D4ED8",
            border_radius="5px",
            font_size="11px",
            padding="2px 7px",
        ),
        rx.button(
            rx.icon(tag="trash_2", size=12),
            on_click=FoodState.eliminar_receta_item(item.id),
            background="#FEF2F2",
            color="#B91C1C",
            border="1px solid #FECACA",
            border_radius="6px",
            padding="4px 7px",
            cursor="pointer",
            _hover={"opacity": "0.8"},
        ),
        width="100%",
        align="center",
        padding="6px 8px",
        background="#FFFFFF",
        border_radius="7px",
        border="1px solid #F1F5F9",
        gap="8px",
    )


def _receta_add_form() -> rx.Component:
    return rx.hstack(
        rx.select(
            FoodState.inv_insumos_activos_nombres,
            placeholder="Insumo…",
            value=FoodState.inv_receta_insumo_sel_nombre,
            on_change=FoodState.set_inv_receta_insumo_sel_nombre,
            background="#F8FAFC",
            border="1px solid #E2E8F0",
            border_radius="7px",
            font_size="13px",
            flex="2",
        ),
        rx.input(
            placeholder="Cantidad",
            value=FoodState.inv_receta_cantidad,
            on_change=FoodState.set_inv_receta_cantidad,
            type="number",
            background="#F8FAFC",
            border="1px solid #E2E8F0",
            border_radius="7px",
            font_size="13px",
            padding_x="10px",
            padding_y="8px",
            flex="1",
            _focus={"border": "1px solid #EA580C"},
        ),
        rx.button(
            rx.icon(tag="plus", size=14),
            on_click=FoodState.guardar_receta_item,
            background="#EA580C",
            color="#FFFFFF",
            border_radius="7px",
            padding="8px 12px",
            cursor="pointer",
            _hover={"background": "#C2410C"},
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
            color="#64748B",
        ),
        rx.vstack(
            rx.text("Seleccionar producto", font_size="11px", font_weight="600", color="#64748B"),
            rx.select(
                FoodState.inv_productos_nombres,
                placeholder="Elige un plato…",
                value=FoodState.inv_producto_sel_nombre,
                on_change=FoodState.set_inv_producto_sel_nombre,
                background="#F8FAFC",
                border="1px solid #E2E8F0",
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
                        rx.text(
                            "Sin ingredientes en la receta. Agrega uno abajo.",
                            font_size="12px",
                            color="#94A3B8",
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
                            color="#64748B",
                        ),
                        _receta_add_form(),
                        spacing="2",
                        width="100%",
                    ),
                    background="#F8FAFC",
                    border="1px solid #E2E8F0",
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


# ── Contenido principal ──────────────────────────────────────────────────────

def _inventario_content() -> rx.Component:
    return rx.vstack(
        rx.cond(
            FoodState.es_pagina_standalone,
            rx.hstack(
                rx.link(
                    rx.hstack(
                        rx.icon(tag="arrow_left", size=13, color="#64748B"),
                        rx.text("Panel Administrativo", font_size="12px", color="#64748B"),
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
        rx.vstack(
            rx.text(
                "Inventario",
                font_size="22px",
                font_weight="800",
                color="#0F172A",
            ),
            rx.text("Insumos, stock y alertas de reposición",
                    font_size="13px", color="#64748B"),
            spacing="0",
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
        _alerta_bajo_stock(),
        _alerta_vencimientos(),
        _insumos_section(),
        _recetas_section(),
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
