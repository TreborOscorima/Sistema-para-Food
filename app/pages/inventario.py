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
                rx.icon(tag="triangle_alert", size=16, color="#B45309"),
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

def _insumo_row(ins: InsumoView) -> rx.Component:
    return rx.hstack(
        # Stock indicator dot
        rx.box(
            width="8px",
            height="8px",
            border_radius="full",
            background=rx.cond(
                ins.bajo_stock,
                "#EF4444",
                rx.cond(ins.activo, "#22C55E", "#94A3B8"),
            ),
            flex_shrink="0",
        ),
        rx.vstack(
            rx.text(ins.nombre, font_size="13px", font_weight="600", color="#0F172A"),
            rx.text(ins.unidad, font_size="11px", color="#94A3B8"),
            spacing="0",
            align="start",
            flex="1",
        ),
        rx.vstack(
            rx.text(
                ins.stock_texto,
                font_size="13px",
                font_weight="700",
                color=rx.cond(ins.bajo_stock, "#EF4444", "#0F172A"),
            ),
            rx.text(
                "Mín: " + ins.stock_minimo_texto,
                font_size="11px",
                color="#94A3B8",
            ),
            spacing="0",
            align="end",
            min_width="100px",
        ),
        rx.hstack(
            rx.button(
                rx.icon(tag="pencil", size=12),
                on_click=FoodState.editar_insumo(ins.id),
                background="#F1F5F9",
                color="#475569",
                border="1px solid #E2E8F0",
                border_radius="6px",
                padding="4px 8px",
                cursor="pointer",
                _hover={"background": "#E2E8F0"},
            ),
            rx.button(
                rx.cond(ins.activo, rx.icon(tag="toggle_right", size=14), rx.icon(tag="toggle_left", size=14)),
                on_click=FoodState.toggle_insumo_activo(ins.id),
                background=rx.cond(ins.activo, "#FEF2F2", "#F0FDF4"),
                color=rx.cond(ins.activo, "#B91C1C", "#15803D"),
                border=rx.cond(ins.activo, "1px solid #FECACA", "1px solid #BBF7D0"),
                border_radius="6px",
                padding="4px 8px",
                cursor="pointer",
                _hover={"opacity": "0.8"},
            ),
            spacing="2",
            flex_shrink="0",
        ),
        width="100%",
        align="center",
        padding="8px 10px",
        background=rx.cond(ins.bajo_stock, "#FFFBEB", "#FFFFFF"),
        border_radius="8px",
        border=rx.cond(ins.bajo_stock, "1px solid #FDE68A", "1px solid #F1F5F9"),
        gap="10px",
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
                spacing="3",
                width="100%",
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
                rx.cond(
                    FoodState.inv_form_editando,
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
                    rx.fragment(),
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
        _insumo_form(),
        rx.cond(
            FoodState.inv_insumos.length() > 0,
            rx.vstack(
                rx.foreach(FoodState.inv_insumos, _insumo_row),
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
        rx.hstack(
            rx.link(
                rx.hstack(
                    rx.icon(tag="arrow_left", size=13, color="#64748B"),
                    rx.text("Panel del Dueño", font_size="12px", color="#64748B"),
                    spacing="1",
                    align="center",
                ),
                href="/dono",
                _hover={"opacity": "0.7"},
            ),
            rx.spacer(),
            width="100%",
            align="center",
        ),
        rx.text(
            "Inventario",
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
        _alerta_bajo_stock(),
        _insumos_section(),
        _recetas_section(),
        spacing="4",
        width="100%",
    )


# ── Página ───────────────────────────────────────────────────────────────────

@rx.page(
    route="/inventario",
    on_load=[AdminLocalState.on_load_dono, FoodState.on_load_inventario],
)
def inventario_page() -> rx.Component:
    return _dono_shell(_inventario_content())
