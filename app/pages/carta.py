"""Pagina admin de carta — gestión de categorias y productos."""

from __future__ import annotations

import reflex as rx

from app.components.shared import app_shell
from app.states.food_state import CategoriaView, FoodState, ProductoView


def _categoria_row(cat: CategoriaView) -> rx.Component:
    return rx.hstack(
        rx.vstack(
            rx.hstack(
                rx.text(cat.nombre, font_size="14px", font_weight="600", color="#F1F5F9"),
                rx.cond(
                    cat.activa,
                    rx.badge("Activa", background="rgba(34,197,94,0.14)", color="#4ADE80", border_radius="5px", font_size="10px"),
                    rx.badge("Inactiva", background="rgba(239,68,68,0.12)", color="#FCA5A5", border_radius="5px", font_size="10px"),
                ),
                spacing="2",
                align="center",
            ),
            rx.cond(
                cat.descripcion != "",
                rx.text(cat.descripcion, font_size="11px", color="rgba(255,255,255,0.4)"),
                rx.fragment(),
            ),
            spacing="0",
            align="start",
        ),
        rx.spacer(),
        rx.text(f"Orden: {cat.orden}", font_size="11px", color="rgba(255,255,255,0.3)"),
        rx.button(
            "Editar",
            on_click=FoodState.editar_categoria(cat.id),
            background="rgba(249,115,22,0.12)",
            color="#F97316",
            border="1px solid rgba(249,115,22,0.25)",
            border_radius="6px",
            font_size="11px",
            cursor="pointer",
            padding_x="8px",
            padding_y="4px",
            _hover={"opacity": "0.85"},
        ),
        rx.button(
            rx.cond(cat.activa, "Desactivar", "Activar"),
            on_click=FoodState.toggle_categoria_activa(cat.id),
            background=rx.cond(
                cat.activa,
                "rgba(239,68,68,0.10)",
                "rgba(34,197,94,0.10)",
            ),
            color=rx.cond(cat.activa, "#FCA5A5", "#4ADE80"),
            border=rx.cond(
                cat.activa,
                "1px solid rgba(239,68,68,0.22)",
                "1px solid rgba(34,197,94,0.22)",
            ),
            border_radius="6px",
            font_size="11px",
            cursor="pointer",
            padding_x="8px",
            padding_y="4px",
            _hover={"opacity": "0.85"},
        ),
        width="100%",
        align="center",
        padding="10px 14px",
        background="rgba(255,255,255,0.03)",
        border_radius="8px",
        border="1px solid rgba(255,255,255,0.06)",
    )


def _categoria_form() -> rx.Component:
    return rx.vstack(
        rx.text(
            rx.cond(FoodState.categoria_form_id > 0, "Editar Categoria", "Nueva Categoria"),
            font_size="14px",
            font_weight="700",
            color="#F97316",
        ),
        rx.input(
            placeholder="Nombre *",
            value=FoodState.categoria_form_nombre,
            on_change=FoodState.set_categoria_form_nombre,
            background="rgba(255,255,255,0.05)",
            border="1px solid rgba(255,255,255,0.12)",
            color="#F1F5F9",
            border_radius="8px",
            padding_x="12px",
            padding_y="8px",
            font_size="13px",
            width="100%",
        ),
        rx.input(
            placeholder="Descripcion (opcional)",
            value=FoodState.categoria_form_descripcion,
            on_change=FoodState.set_categoria_form_descripcion,
            background="rgba(255,255,255,0.05)",
            border="1px solid rgba(255,255,255,0.12)",
            color="#F1F5F9",
            border_radius="8px",
            padding_x="12px",
            padding_y="8px",
            font_size="13px",
            width="100%",
        ),
        rx.input(
            placeholder="Orden",
            value=FoodState.categoria_form_orden,
            on_change=FoodState.set_categoria_form_orden,
            background="rgba(255,255,255,0.05)",
            border="1px solid rgba(255,255,255,0.12)",
            color="#F1F5F9",
            border_radius="8px",
            padding_x="12px",
            padding_y="8px",
            font_size="13px",
            width="80px",
            type="number",
        ),
        rx.hstack(
            rx.button(
                "Cancelar",
                on_click=FoodState.cancelar_categoria_form,
                background="rgba(255,255,255,0.05)",
                color="#94A3B8",
                border="1px solid rgba(255,255,255,0.10)",
                border_radius="8px",
                font_size="13px",
                cursor="pointer",
                _hover={"opacity": "0.85"},
            ),
            rx.button(
                "Guardar Categoria",
                on_click=FoodState.guardar_categoria,
                background="rgba(249,115,22,0.20)",
                color="#F97316",
                border="1px solid rgba(249,115,22,0.35)",
                border_radius="8px",
                font_size="13px",
                font_weight="700",
                cursor="pointer",
                flex="1",
                _hover={"opacity": "0.85"},
            ),
            spacing="2",
            width="100%",
        ),
        spacing="3",
        padding="16px",
        background="rgba(249,115,22,0.06)",
        border="1px solid rgba(249,115,22,0.20)",
        border_radius="12px",
        width="100%",
    )


def _producto_row(prod: ProductoView) -> rx.Component:
    return rx.hstack(
        rx.vstack(
            rx.hstack(
                rx.text(prod.nombre, font_size="13px", font_weight="600", color="#F1F5F9"),
                rx.cond(
                    prod.disponible,
                    rx.badge("Disponible", background="rgba(34,197,94,0.14)", color="#4ADE80", border_radius="5px", font_size="10px"),
                    rx.badge("No disponible", background="rgba(239,68,68,0.12)", color="#FCA5A5", border_radius="5px", font_size="10px"),
                ),
                spacing="2",
                align="center",
            ),
            rx.hstack(
                rx.text(prod.precio_texto, font_size="13px", font_weight="700", color="#F97316"),
                rx.text("·", color="rgba(255,255,255,0.2)", font_size="10px"),
                rx.text(prod.categoria_nombre, font_size="11px", color="rgba(255,255,255,0.4)"),
                spacing="1",
                align="center",
            ),
            spacing="0",
            align="start",
        ),
        rx.spacer(),
        rx.button(
            "Editar",
            on_click=FoodState.editar_producto(prod.id),
            background="rgba(249,115,22,0.10)",
            color="#F97316",
            border="1px solid rgba(249,115,22,0.22)",
            border_radius="6px",
            font_size="11px",
            cursor="pointer",
            padding_x="8px",
            padding_y="4px",
            _hover={"opacity": "0.85"},
        ),
        rx.button(
            rx.cond(prod.disponible, "86 it", "Activar"),
            on_click=FoodState.toggle_producto_disponible(prod.id),
            background=rx.cond(
                prod.disponible,
                "rgba(239,68,68,0.10)",
                "rgba(34,197,94,0.10)",
            ),
            color=rx.cond(prod.disponible, "#FCA5A5", "#4ADE80"),
            border=rx.cond(
                prod.disponible,
                "1px solid rgba(239,68,68,0.22)",
                "1px solid rgba(34,197,94,0.22)",
            ),
            border_radius="6px",
            font_size="11px",
            cursor="pointer",
            padding_x="8px",
            padding_y="4px",
            _hover={"opacity": "0.85"},
        ),
        width="100%",
        align="center",
        padding="10px 14px",
        background="rgba(255,255,255,0.03)",
        border_radius="8px",
        border="1px solid rgba(255,255,255,0.06)",
    )


def _producto_form() -> rx.Component:
    return rx.vstack(
        rx.text(
            rx.cond(FoodState.producto_form_id > 0, "Editar Producto", "Nuevo Producto"),
            font_size="14px",
            font_weight="700",
            color="#F97316",
        ),
        rx.hstack(
            rx.input(
                placeholder="Nombre del producto *",
                value=FoodState.producto_form_nombre,
                on_change=FoodState.set_producto_form_nombre,
                background="rgba(255,255,255,0.05)",
                border="1px solid rgba(255,255,255,0.12)",
                color="#F1F5F9",
                border_radius="8px",
                padding_x="12px",
                padding_y="8px",
                font_size="13px",
                flex="1",
            ),
            rx.input(
                placeholder="Precio *",
                value=FoodState.producto_form_precio,
                on_change=FoodState.set_producto_form_precio,
                background="rgba(255,255,255,0.05)",
                border="1px solid rgba(255,255,255,0.12)",
                color="#F1F5F9",
                border_radius="8px",
                padding_x="12px",
                padding_y="8px",
                font_size="13px",
                width="100px",
                type="number",
                min="0.01",
                step="0.01",
            ),
            spacing="2",
            width="100%",
        ),
        rx.select(
            FoodState.categorias_activas_nombres,
            value=FoodState.producto_form_categoria_nombre,
            on_change=FoodState.set_producto_form_categoria,
            background="rgba(255,255,255,0.05)",
            color="#F1F5F9",
            border="1px solid rgba(255,255,255,0.12)",
            border_radius="8px",
            padding_x="12px",
            padding_y="8px",
            font_size="13px",
            width="100%",
        ),
        rx.hstack(
            rx.button(
                rx.cond(FoodState.producto_form_disponible, "Disponible", "No disponible"),
                on_click=FoodState.set_producto_form_disponible(~FoodState.producto_form_disponible),
                background=rx.cond(FoodState.producto_form_disponible, "rgba(34,197,94,0.14)", "rgba(239,68,68,0.12)"),
                color=rx.cond(FoodState.producto_form_disponible, "#4ADE80", "#FCA5A5"),
                border="1px solid rgba(255,255,255,0.10)",
                border_radius="6px",
                font_size="12px",
                cursor="pointer",
                _hover={"opacity": "0.85"},
            ),
            rx.spacer(),
            rx.button(
                "Cancelar",
                on_click=FoodState.cancelar_producto_form,
                background="rgba(255,255,255,0.05)",
                color="#94A3B8",
                border="1px solid rgba(255,255,255,0.10)",
                border_radius="8px",
                font_size="13px",
                cursor="pointer",
                _hover={"opacity": "0.85"},
            ),
            rx.button(
                "Guardar Producto",
                on_click=FoodState.guardar_producto,
                background="rgba(249,115,22,0.20)",
                color="#F97316",
                border="1px solid rgba(249,115,22,0.35)",
                border_radius="8px",
                font_size="13px",
                font_weight="700",
                cursor="pointer",
                _hover={"opacity": "0.85"},
            ),
            spacing="2",
            width="100%",
        ),
        spacing="3",
        padding="16px",
        background="rgba(249,115,22,0.06)",
        border="1px solid rgba(249,115,22,0.20)",
        border_radius="12px",
        width="100%",
    )


def _carta_content() -> rx.Component:
    return rx.vstack(
        rx.text("Carta / Admin", font_size="22px", font_weight="800", color="#F1F5F9"),
        rx.cond(
            FoodState.mensaje != "",
            rx.box(
                rx.text(FoodState.mensaje, font_size="12px", color="#94A3B8"),
                background="rgba(255,255,255,0.04)",
                border_radius="6px",
                padding="8px 12px",
                width="100%",
            ),
            rx.fragment(),
        ),
        rx.hstack(
            # ─── Categorias ───────────────────────────────────────────────
            rx.vstack(
                rx.text("Categorias", font_size="15px", font_weight="700", color="#94A3B8"),
                _categoria_form(),
                rx.vstack(
                    rx.foreach(FoodState.categorias, _categoria_row),
                    spacing="2",
                    width="100%",
                ),
                spacing="3",
                flex="1",
                min_width="0",
            ),
            rx.divider(orientation="vertical", border_color="rgba(255,255,255,0.08)", height="auto"),
            # ─── Productos ────────────────────────────────────────────────
            rx.vstack(
                rx.text("Productos", font_size="15px", font_weight="700", color="#94A3B8"),
                _producto_form(),
                rx.vstack(
                    rx.foreach(FoodState.productos, _producto_row),
                    spacing="2",
                    width="100%",
                ),
                spacing="3",
                flex="1",
                min_width="0",
            ),
            spacing="5",
            width="100%",
            align="start",
            flex_wrap=rx.breakpoints(initial="wrap", lg="nowrap"),
        ),
        spacing="5",
        width="100%",
    )


@rx.page(route="/carta", on_load=FoodState.on_load_carta)
def carta_page() -> rx.Component:
    return app_shell(_carta_content(), page_key="carta")
