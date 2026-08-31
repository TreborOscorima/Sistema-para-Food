"""Pagina admin de carta — gestión de categorias y productos."""

from __future__ import annotations

import reflex as rx

from app.components.ayuda import ayuda_modal, ayuda_trigger, empty_state
from app.components.shared import (
    SUCCESS_TEXT, DANGER_TEXT,
    app_shell,
    ACCENT, ACCENT_HOVER,
    DANGER_SOLID,
    DARK_700, DARK_800,
    PAGE_BACKGROUND, SURFACE_BASE,
    SUCCESS_SOLID,
    TEXT_MUTED, TEXT_PRIMARY, TEXT_WHITE,
    WARNING_SOLID,
    switch_toggle,
)
from app.states.food_state import CategoriaView, FoodState, GrupoModificadorAdminView, ProductoView


def _categoria_row(cat: CategoriaView) -> rx.Component:
    return rx.hstack(
        rx.vstack(
            rx.hstack(
                rx.text(cat.emoji + " " + cat.nombre, font_size="14px", font_weight="600", color=TEXT_PRIMARY),
                rx.badge(
                    cat.productos_count.to_string() + " items",
                    background=DARK_800, color=TEXT_MUTED,
                    border_radius="5px", font_size="10px", font_weight="700",
                ),
                rx.cond(
                    cat.activa,
                    rx.badge("Activa", background="rgba(34,197,94,0.12)", color=SUCCESS_TEXT, border_radius="5px", font_size="10px"),
                    rx.badge("Inactiva", background="rgba(239,68,68,0.12)", color="var(--twk-danger-text)", border_radius="5px", font_size="10px"),
                ),
                spacing="2",
                align="center",
                flex_wrap="wrap",
            ),
            rx.cond(
                cat.descripcion != "",
                rx.text(cat.descripcion, font_size="11px", color=TEXT_MUTED),
                rx.fragment(),
            ),
            spacing="0",
            align="start",
            flex="1",
            min_width="150px",
        ),
        rx.hstack(
            rx.tooltip(
                rx.icon(
                    tag="chevron_up", size=14, color=TEXT_MUTED, cursor="pointer",
                    on_click=FoodState.mover_categoria(cat.id, "arriba"),
                    _hover={"color": "#EA580C"},
                ),
                content="Subir",
            ),
            rx.tooltip(
                rx.icon(
                    tag="chevron_down", size=14, color=TEXT_MUTED, cursor="pointer",
                    on_click=FoodState.mover_categoria(cat.id, "abajo"),
                    _hover={"color": "#EA580C"},
                ),
                content="Bajar",
            ),
            spacing="0", align="center", flex_shrink="0",
        ),
        rx.tooltip(
            rx.button(
                rx.icon(tag="pencil", size=15),
                on_click=FoodState.editar_categoria(cat.id),
                background="rgba(234,88,12,0.08)",
                color=ACCENT,
                border="1px solid rgba(234,88,12,0.40)",
                border_radius="6px",
                cursor="pointer",
                padding="6px", min_width="0", height="auto",
                _hover={"opacity": "0.85"},
            ),
            content="Editar categoría",
        ),
        rx.tooltip(
            switch_toggle(cat.activa, FoodState.toggle_categoria_activa(cat.id)),
            content=rx.cond(cat.activa, "Desactivar categoría", "Activar categoría"),
        ),
        width="100%",
        align="center",
        flex_wrap="wrap",
        padding="10px 14px",
        background=DARK_800,
        border_radius="8px",
        border=f"1px solid {DARK_700}",
        gap="8px",
    )


def _producto_row(prod: ProductoView) -> rx.Component:
    return rx.hstack(
        rx.cond(
            prod.imagen_url != "",
            rx.image(
                src=prod.imagen_url,
                width="40px",
                height="40px",
                object_fit="cover",
                border_radius="6px",
                border=f"1px solid {DARK_700}",
                flex_shrink="0",
            ),
            rx.box(
                rx.text(prod.emoji, font_size="18px", line_height="1"),
                width="40px",
                height="40px",
                border_radius="10px",
                background="linear-gradient(135deg,var(--twk-accent-text),#EA580C)",
                display="flex",
                align_items="center",
                justify_content="center",
                flex_shrink="0",
                box_shadow="0 2px 6px rgba(234,88,12,0.35)",
            ),
        ),
        rx.vstack(
            rx.hstack(
                rx.text(prod.nombre, font_size="13px", font_weight="600", color=TEXT_PRIMARY),
                rx.cond(
                    prod.disponible,
                    rx.badge("Disponible", background="rgba(34,197,94,0.12)", color=SUCCESS_TEXT, border_radius="5px", font_size="10px"),
                    rx.badge("No disponible", background="rgba(239,68,68,0.12)", color="var(--twk-danger-text)", border_radius="5px", font_size="10px"),
                ),
                rx.cond(
                    prod.stock_diario >= 0,
                    rx.badge(
                        rx.cond(
                            prod.stock_diario > prod.stock_diario_alerta,
                            "Stock: " + prod.stock_diario.to_string(),
                            rx.cond(
                                prod.stock_diario > 0,
                                "Stock: " + prod.stock_diario.to_string(),
                                "AGOTADO",
                            ),
                        ),
                        background=rx.cond(
                            prod.stock_diario > prod.stock_diario_alerta,
                            "rgba(59,130,246,0.12)",
                            rx.cond(
                                prod.stock_diario > 0,
                                "rgba(245,158,11,0.15)",
                                "rgba(239,68,68,0.15)",
                            ),
                        ),
                        color=rx.cond(
                            prod.stock_diario > prod.stock_diario_alerta,
                            "var(--twk-info-text)",
                            rx.cond(
                                prod.stock_diario > 0,
                                "var(--twk-warning-text)",
                                "var(--twk-danger-text)",
                            ),
                        ),
                        border_radius="5px", font_size="10px", font_weight="700",
                        padding="1px 6px",
                    ),
                    rx.fragment(),
                ),
                # M-07d: aviso "sin receta → no descuenta stock" con link a Inventario.
                rx.cond(
                    ~prod.tiene_receta,
                    rx.tooltip(
                        rx.link(
                            rx.badge(
                                rx.hstack(
                                    rx.icon(tag="info", size=10),
                                    rx.text("Sin receta"),
                                    spacing="1", align="center",
                                ),
                                background="rgba(148,163,184,0.12)",
                                color=TEXT_MUTED,
                                border=f"1px solid {DARK_700}",
                                border_radius="5px", font_size="10px", font_weight="600",
                                padding="1px 6px",
                            ),
                            href="/inventario",
                            _hover={"text_decoration": "none", "opacity": "0.8"},
                        ),
                        content="No descuenta stock al venderse. Cárgale una receta en Inventario.",
                    ),
                    rx.fragment(),
                ),
                spacing="2",
                align="center",
                flex_wrap="wrap",
            ),
            rx.hstack(
                rx.text(prod.precio_texto, font_size="13px", font_weight="700", color=ACCENT),
                rx.cond(
                    prod.margen_pct >= 0,
                    rx.badge(
                        prod.margen_pct.to_string() + "%",
                        background=rx.cond(
                            prod.margen_pct >= 50, "rgba(34,197,94,0.12)",
                            rx.cond(prod.margen_pct >= 30, "rgba(245,158,11,0.12)", "rgba(239,68,68,0.12)"),
                        ),
                        color=rx.cond(
                            prod.margen_pct >= 50, "#22C55E",
                            rx.cond(prod.margen_pct >= 30, "#713F12", "var(--twk-danger-text)"),
                        ),
                        border_radius="5px", font_size="10px", font_weight="700",
                        padding="1px 6px",
                    ),
                    rx.fragment(),
                ),
                rx.text("·", color="var(--twk-slate-300)", font_size="10px"),
                rx.text(prod.categoria_nombre, font_size="11px", color=TEXT_MUTED),
                spacing="1",
                align="center",
            ),
            spacing="0",
            align="start",
            flex="1",
            min_width="150px",
        ),
        # Acciones de fila como ícono + tooltip (item 5): compactas y prolijas,
        # conservando el código de colores de estado.
        rx.tooltip(
            rx.button(
                rx.icon(tag="pencil", size=15),
                on_click=FoodState.editar_producto(prod.id),
                background="rgba(234,88,12,0.08)",
                color=ACCENT,
                border="1px solid rgba(234,88,12,0.40)",
                border_radius="6px", cursor="pointer",
                padding="6px", min_width="0", height="auto",
                _hover={"opacity": "0.85"},
            ),
            content="Editar",
        ),
        rx.tooltip(
            rx.button(
                rx.icon(tag="copy", size=15),
                on_click=FoodState.duplicar_producto(prod.id),
                background="#F0F9FF",
                color="#0369A1",
                border="1px solid #BAE6FD",
                border_radius="6px", cursor="pointer",
                padding="6px", min_width="0", height="auto",
                _hover={"opacity": "0.85"},
            ),
            content="Duplicar",
        ),
        rx.tooltip(
            rx.button(
                rx.icon(tag="settings_2", size=15),
                on_click=FoodState.abrir_mod_asignar(prod.id),
                background=rx.cond(prod.tiene_modificadores, "rgba(124,58,237,0.12)", "var(--twk-d900)"),
                color=rx.cond(prod.tiene_modificadores, "#7C3AED", "var(--twk-slate-400)"),
                border=rx.cond(prod.tiene_modificadores, "1px solid rgba(124,58,237,0.30)", f"1px solid {DARK_700}"),
                border_radius="6px", cursor="pointer",
                padding="6px", min_width="0", height="auto",
                _hover={"opacity": "0.85"},
            ),
            content=rx.cond(prod.tiene_modificadores, "Editar modificadores", "Agregar modificadores"),
        ),
        rx.tooltip(
            switch_toggle(prod.disponible, FoodState.toggle_producto_disponible(prod.id)),
            content=rx.cond(prod.disponible, "Deshabilitar", "Activar"),
        ),
        rx.tooltip(
            rx.button(
                rx.icon(tag="trash_2", size=15),
                on_click=FoodState.solicitar_eliminar_producto(prod.id),
                background="rgba(239,68,68,0.08)",
                color="var(--twk-danger-text)",
                border="1px solid #FECACA",
                border_radius="6px", cursor="pointer",
                padding="6px", min_width="0", height="auto",
                _hover={"opacity": "0.85"},
            ),
            content="Eliminar",
        ),
        width="100%",
        align="center",
        flex_wrap="wrap",
        padding="10px 14px",
        background=DARK_800,
        border_radius="8px",
        border=f"1px solid {DARK_700}",
        gap="10px",
    )


def _producto_archivado_row(prod: ProductoView) -> rx.Component:
    """Fila de producto archivado con acción de Restaurar."""
    return rx.hstack(
        rx.cond(
            prod.imagen_url != "",
            rx.image(
                src=prod.imagen_url,
                width="36px", height="36px", object_fit="cover",
                border_radius="6px", border=f"1px solid {DARK_700}",
                flex_shrink="0", opacity="0.65",
            ),
            rx.box(
                rx.text(prod.emoji, font_size="16px", line_height="1"),
                width="36px", height="36px", border_radius="9px",
                background=DARK_700,
                display="flex", align_items="center", justify_content="center",
                flex_shrink="0",
            ),
        ),
        rx.vstack(
            rx.hstack(
                rx.text(prod.nombre, font_size="13px", font_weight="600", color="var(--twk-slate-300)"),
                rx.badge(
                    "Archivado",
                    background="rgba(148,163,184,0.14)", color=TEXT_MUTED,
                    border_radius="5px", font_size="10px", font_weight="700",
                ),
                spacing="2", align="center", flex_wrap="wrap",
            ),
            rx.hstack(
                rx.text(prod.precio_texto, font_size="12px", font_weight="700", color=TEXT_MUTED),
                rx.text("·", color="var(--twk-slate-300)", font_size="10px"),
                rx.text(prod.categoria_nombre, font_size="11px", color=TEXT_MUTED),
                spacing="1", align="center",
            ),
            spacing="0", align="start", flex="1", min_width="120px",
        ),
        rx.tooltip(
            rx.button(
                rx.hstack(
                    rx.icon(tag="rotate_ccw", size=14),
                    rx.text("Restaurar", font_size="12px", font_weight="700"),
                    spacing="1", align="center",
                ),
                on_click=FoodState.desarchivar_producto(prod.id),
                background="rgba(34,197,94,0.10)",
                color=SUCCESS_TEXT,
                border="1px solid rgba(34,197,94,0.35)",
                border_radius="6px", cursor="pointer",
                padding="6px 10px", min_width="0", height="auto",
                _hover={"opacity": "0.85"},
            ),
            content="Devolver a la carta",
        ),
        width="100%",
        align="center",
        flex_wrap="wrap",
        padding="10px 14px",
        background=SURFACE_BASE,
        border_radius="8px",
        border=f"1px dashed {DARK_700}",
        gap="10px",
    )


def _cat_modal() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.hstack(
                    rx.dialog.title(
                        rx.cond(FoodState.categoria_form_id > 0, "Editar Categoría", "Nueva Categoría"),
                        font_size="16px", font_weight="800", color=TEXT_PRIMARY, margin="0",
                    ),
                    rx.spacer(),
                    rx.icon_button(
                        rx.icon(tag="x", size=14),
                        on_click=FoodState.cancelar_categoria_form,
                        background="transparent",
                        color=TEXT_MUTED,
                        border="none",
                        border_radius="6px",
                        _hover={"background": "var(--twk-d700)", "color": "var(--twk-text-primary)"},
                    ),
                    width="100%", align="center",
                ),
                rx.box(height="1px", width="100%", background=DARK_800),
                rx.input(
                    placeholder="Nombre *",
                    value=FoodState.categoria_form_nombre,
                    on_change=FoodState.set_categoria_form_nombre,
                    background=DARK_800,
                    border=f"1px solid {DARK_700}",
                    color=TEXT_PRIMARY,
                    border_radius="8px",
                    padding_x="12px",
                    padding_y="8px",
                    font_size="13px",
                    width="100%",
                ),
                rx.input(
                    placeholder="Descripción (opcional)",
                    value=FoodState.categoria_form_descripcion,
                    on_change=FoodState.set_categoria_form_descripcion,
                    background=DARK_800,
                    border=f"1px solid {DARK_700}",
                    color=TEXT_PRIMARY,
                    border_radius="8px",
                    padding_x="12px",
                    padding_y="8px",
                    font_size="13px",
                    width="100%",
                ),
                rx.hstack(
                    rx.text("Orden:", font_size="13px", color=TEXT_MUTED, white_space="nowrap"),
                    rx.input(
                        value=FoodState.categoria_form_orden,
                        on_change=FoodState.set_categoria_form_orden,
                        background=DARK_800,
                        border=f"1px solid {DARK_700}",
                        color=TEXT_PRIMARY,
                        border_radius="8px",
                        padding_x="12px",
                        padding_y="8px",
                        font_size="13px",
                        width="80px",
                        type="number",
                    ),
                    spacing="2", align="center",
                ),
                rx.hstack(
                    rx.text("Estación:", font_size="13px", color=TEXT_MUTED, white_space="nowrap"),
                    rx.select.root(
                        rx.select.trigger(
                            background=DARK_800,
                            border=f"1px solid {DARK_700}",
                            color=TEXT_PRIMARY,
                            border_radius="8px",
                            font_size="13px",
                            width="200px",
                        ),
                        rx.select.content(
                            rx.select.item("Cocina", value="cocina"),
                            rx.select.item("Barra", value="barra"),
                            rx.select.item("Sin preparación (directo a caja)", value="ninguna"),
                        ),
                        value=FoodState.categoria_form_estacion,
                        on_change=FoodState.set_categoria_form_estacion,
                    ),
                    spacing="2", align="center",
                ),
                rx.box(height="1px", width="100%", background=DARK_800),
                rx.hstack(
                    rx.button(
                        "Cancelar",
                        on_click=FoodState.cancelar_categoria_form,
                        background=DARK_800,
                        color=TEXT_MUTED,
                        border=f"1px solid {DARK_700}",
                        border_radius="8px",
                        font_size="13px",
                        cursor="pointer",
                        _hover={"opacity": "0.85"},
                    ),
                    rx.button(
                        rx.cond(FoodState.categoria_form_id > 0, "Guardar cambios", "Guardar Categoría"),
                        on_click=FoodState.guardar_categoria,
                        background=ACCENT,
                        color=TEXT_WHITE,
                        border_radius="8px",
                        font_size="13px",
                        font_weight="700",
                        cursor="pointer",
                        flex="1",
                        _hover={"background": ACCENT_HOVER},
                    ),
                    spacing="2",
                    width="100%",
                ),
                spacing="3",
                width="100%",
            ),
            max_width="440px",
            width="90vw",
            max_height="90vh",
            overflow_y="auto",
            background=PAGE_BACKGROUND,
            border=f"1px solid {DARK_800}",
            border_radius="16px",
            padding="24px",
            box_shadow="0 20px 60px rgba(0,0,0,0.15)",
        ),
        open=FoodState.carta_cat_modal,
        on_open_change=FoodState.set_carta_cat_modal,
    )


def _prod_modal() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.hstack(
                    rx.dialog.title(
                        rx.cond(FoodState.producto_form_id > 0, "Editar Producto", "Nuevo Producto"),
                        font_size="16px", font_weight="800", color=TEXT_PRIMARY, margin="0",
                    ),
                    rx.spacer(),
                    rx.icon_button(
                        rx.icon(tag="x", size=14),
                        on_click=FoodState.cancelar_producto_form,
                        background="transparent",
                        color=TEXT_MUTED,
                        border="none",
                        border_radius="6px",
                        _hover={"background": "var(--twk-d700)", "color": "var(--twk-text-primary)"},
                    ),
                    width="100%", align="center",
                ),
                rx.box(height="1px", width="100%", background=DARK_800),
                rx.hstack(
                    rx.input(
                        placeholder="Nombre del producto *",
                        value=FoodState.producto_form_nombre,
                        on_change=FoodState.set_producto_form_nombre,
                        background=DARK_800,
                        border=f"1px solid {DARK_700}",
                        color=TEXT_PRIMARY,
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
                        background=DARK_800,
                        border=f"1px solid {DARK_700}",
                        color=TEXT_PRIMARY,
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
                    background=DARK_800,
                    color=TEXT_PRIMARY,
                    border=f"1px solid {DARK_700}",
                    border_radius="8px",
                    padding_x="12px",
                    padding_y="8px",
                    font_size="13px",
                    width="100%",
                ),
                # Estación del producto (override opcional de la categoría). Si es
                # "Sin preparación", el producto no genera comanda ni va al KDS.
                rx.vstack(
                    rx.text("Estación (dónde se prepara)", font_size="12px",
                            font_weight="600", color=TEXT_MUTED),
                    rx.select.root(
                        rx.select.trigger(
                            placeholder="Heredar de la categoría",
                            background=DARK_800,
                            border=f"1px solid {DARK_700}",
                            color=TEXT_PRIMARY,
                            border_radius="8px",
                            font_size="13px",
                            width="100%",
                        ),
                        rx.select.content(
                            rx.select.item("Heredar de la categoría", value="heredar"),
                            rx.select.item("Cocina", value="cocina"),
                            rx.select.item("Barra", value="barra"),
                            rx.select.item("Sin preparación (directo a caja)", value="ninguna"),
                        ),
                        value=FoodState.producto_form_estacion,
                        on_change=FoodState.set_producto_form_estacion,
                        width="100%",
                    ),
                    spacing="1", width="100%", align="start",
                ),
                rx.text_area(
                    placeholder="Descripción del producto (se muestra en la carta QR)",
                    value=FoodState.producto_form_descripcion,
                    on_change=FoodState.set_producto_form_descripcion,
                    background=DARK_800,
                    border=f"1px solid {DARK_700}",
                    color=TEXT_PRIMARY,
                    border_radius="8px",
                    padding_x="12px",
                    padding_y="8px",
                    font_size="13px",
                    rows="2",
                    resize="vertical",
                    width="100%",
                    max_length=240,
                ),
                # ── Ícono ────────────────────────────────────────────────────
                rx.vstack(
                    rx.hstack(
                        rx.text("Ícono", font_size="12px", font_weight="600", color=TEXT_MUTED),
                        rx.text("— se muestra si el producto no tiene foto",
                                font_size="11px", color=TEXT_MUTED),
                        spacing="1", align="center",
                    ),
                    rx.hstack(
                        rx.box(
                            rx.text(
                                rx.cond(FoodState.producto_form_emoji != "",
                                        FoodState.producto_form_emoji,
                                        FoodState.producto_form_emoji_sugerido),
                                font_size="20px", line_height="1",
                            ),
                            width="40px", height="40px", border_radius="10px",
                            background="linear-gradient(135deg,var(--twk-accent-text),#EA580C)",
                            display="flex", align_items="center", justify_content="center",
                            flex_shrink="0",
                        ),
                        rx.input(
                            placeholder="Auto: " + FoodState.producto_form_emoji_sugerido,
                            value=FoodState.producto_form_emoji,
                            on_change=FoodState.set_producto_form_emoji,
                            background=SURFACE_BASE, border=f"1px solid {DARK_700}",
                            color=TEXT_PRIMARY, border_radius="8px",
                            padding_x="12px", padding_y="8px", font_size="13px",
                            flex="1",
                        ),
                        spacing="3", align="center", width="100%",
                    ),
                    rx.flex(
                        *[
                            rx.box(
                                rx.text(e, font_size="16px", line_height="1"),
                                on_click=FoodState.set_producto_form_emoji(e),
                                cursor="pointer", padding="6px",
                                border_radius="6px", border=f"1px solid {DARK_700}",
                                background=DARK_800,
                                _hover={"border_color": "#EA580C", "background": "rgba(234,88,12,0.08)"},
                            )
                            for e in [
                                "🍗", "🥩", "🍔", "🍕", "🍝", "🥗", "🍲", "🥔",
                                "🍟", "🍚", "🥚", "🍰", "🍨", "☕", "🥤", "🍺",
                                "🍷", "🥪", "🥟", "🫔", "🐟", "🍽️",
                            ]
                        ],
                        gap="6px", flex_wrap="wrap", width="100%",
                    ),
                    spacing="2", width="100%",
                ),
                # ── Etiquetas ────────────────────────────────────────────────
                rx.vstack(
                    rx.text("Etiquetas", font_size="12px", font_weight="600", color=TEXT_MUTED),
                    rx.hstack(
                        *[
                            rx.box(
                                f"{emoji} {label}",
                                on_click=FoodState.toggle_producto_tag(tag),
                                background=rx.cond(
                                    FoodState.producto_form_tags.contains(tag),
                                    "rgba(234,88,12,0.08)", "var(--twk-d900)",
                                ),
                                color=rx.cond(
                                    FoodState.producto_form_tags.contains(tag),
                                    "#C2410C", "var(--twk-slate-400)",
                                ),
                                border=rx.cond(
                                    FoodState.producto_form_tags.contains(tag),
                                    "1.5px solid #EA580C", f"1px solid {DARK_700}",
                                ),
                                font_size="11px", font_weight="600",
                                padding="4px 10px", border_radius="14px",
                                cursor="pointer",
                                _hover={"border_color": ACCENT},
                            )
                            for tag, emoji, label in [
                                ("picante", "🌶️", "Picante"),
                                ("veggie", "🌱", "Vegetariano"),
                                ("vegano", "🥦", "Vegano"),
                                ("sin_gluten", "🚫🌾", "Sin gluten"),
                                ("frutos_secos", "🥜", "Frutos secos"),
                                ("lacteos", "🥛", "Lácteos"),
                            ]
                        ],
                        gap="6px", flex_wrap="wrap", width="100%",
                    ),
                    spacing="2", width="100%",
                ),
                # ── Imagen ───────────────────────────────────────────────────
                rx.vstack(
                    rx.text("Imagen del plato", font_size="12px", font_weight="600", color=TEXT_MUTED),
                    rx.cond(
                        FoodState.producto_form_imagen_url != "",
                        rx.hstack(
                            rx.image(
                                src=FoodState.producto_form_imagen_url,
                                width="80px", height="80px",
                                object_fit="cover", border_radius="8px",
                                border=f"1px solid {DARK_700}",
                            ),
                            rx.vstack(
                                rx.text("Imagen cargada", font_size="11px", color=SUCCESS_TEXT, font_weight="600"),
                                rx.button(
                                    "Quitar imagen",
                                    on_click=FoodState.quitar_imagen_producto,
                                    background="rgba(239,68,68,0.08)", color="var(--twk-danger-text)",
                                    border="1px solid #FECACA", border_radius="6px",
                                    font_size="11px", cursor="pointer",
                                    padding_x="8px", padding_y="3px",
                                    _hover={"opacity": "0.85"},
                                ),
                                spacing="2", align="start",
                            ),
                            spacing="3", align="center",
                        ),
                        rx.upload(
                            rx.vstack(
                                rx.icon(tag="image_plus", size=20, color=TEXT_MUTED),
                                rx.text("Arrastra o toca aquí", font_size="11px", color=TEXT_MUTED),
                                rx.text("JPG, PNG, WEBP — max 5MB", font_size="10px", color=TEXT_MUTED),
                                spacing="1", align="center",
                            ),
                            id="upload_imagen_producto",
                            on_drop=FoodState.handle_upload_imagen_producto(
                                rx.upload_files(upload_id="upload_imagen_producto")
                            ),
                            accept={"image/jpeg": [".jpg", ".jpeg"], "image/png": [".png"], "image/webp": [".webp"]},
                            max_files=1,
                            border="2px dashed var(--twk-d700)",
                            border_radius="8px",
                            padding="16px",
                            width="100%",
                            background=PAGE_BACKGROUND,
                            cursor="pointer",
                            _hover={"border_color": "#EA580C", "background": "rgba(234,88,12,0.08)"},
                        ),
                    ),
                    spacing="2", width="100%",
                ),
                rx.box(height="1px", width="100%", background=DARK_800),
                rx.vstack(
                    rx.text("Stock diario (opcional)", font_size="12px", font_weight="600", color=TEXT_MUTED),
                    rx.hstack(
                        rx.vstack(
                            rx.text("Cantidad preparada", font_size="11px", color=TEXT_MUTED),
                            rx.input(
                                placeholder="Ej: 30 (vacío = ilimitado)",
                                value=FoodState.producto_form_stock_diario,
                                on_change=FoodState.set_producto_form_stock_diario,
                                background=DARK_800,
                                color=TEXT_PRIMARY,
                                border=f"1px solid {DARK_700}",
                                border_radius="8px",
                                font_size="13px",
                                type="number",
                                min_="0",
                            ),
                            spacing="1", flex="1",
                        ),
                        rx.vstack(
                            rx.text("Alerta mínima", font_size="11px", color=TEXT_MUTED),
                            rx.input(
                                placeholder="5",
                                value=FoodState.producto_form_stock_diario_alerta,
                                on_change=FoodState.set_producto_form_stock_diario_alerta,
                                background=DARK_800,
                                color=TEXT_PRIMARY,
                                border=f"1px solid {DARK_700}",
                                border_radius="8px",
                                font_size="13px",
                                type="number",
                                min_="1",
                            ),
                            spacing="1", flex="1",
                        ),
                        spacing="2", width="100%",
                    ),
                    rx.text(
                        "Deja vacío si el producto no necesita control de stock. Al llegar a 0 se marca como 86 automáticamente.",
                        font_size="10px", color=TEXT_MUTED, line_height="1.3",
                    ),
                    spacing="1", width="100%",
                ),
                rx.box(height="1px", width="100%", background=DARK_800),
                rx.hstack(
                    rx.button(
                        rx.cond(FoodState.producto_form_disponible, "Disponible", "No disponible"),
                        on_click=FoodState.set_producto_form_disponible(~FoodState.producto_form_disponible),
                        background=rx.cond(FoodState.producto_form_disponible, "rgba(34,197,94,0.12)", "rgba(239,68,68,0.12)"),
                        color=rx.cond(FoodState.producto_form_disponible, "#22C55E", "var(--twk-danger-text)"),
                        border=rx.cond(FoodState.producto_form_disponible, "1px solid #BBF7D0", "1px solid #FECACA"),
                        border_radius="6px",
                        font_size="12px",
                        cursor="pointer",
                        _hover={"opacity": "0.85"},
                    ),
                    rx.spacer(),
                    rx.button(
                        "Cancelar",
                        on_click=FoodState.cancelar_producto_form,
                        background=DARK_800,
                        color=TEXT_MUTED,
                        border=f"1px solid {DARK_700}",
                        border_radius="8px",
                        font_size="13px",
                        cursor="pointer",
                        _hover={"opacity": "0.85"},
                    ),
                    rx.button(
                        rx.cond(FoodState.producto_form_id > 0, "Guardar cambios", "Guardar Producto"),
                        on_click=FoodState.guardar_producto,
                        background=ACCENT,
                        color=TEXT_WHITE,
                        border_radius="8px",
                        font_size="13px",
                        font_weight="700",
                        cursor="pointer",
                        _hover={"background": ACCENT_HOVER},
                    ),
                    spacing="2",
                    width="100%",
                ),
                spacing="3",
                width="100%",
            ),
            max_width="520px",
            width="92vw",
            background=PAGE_BACKGROUND,
            border=f"1px solid {DARK_800}",
            border_radius="16px",
            padding="24px",
            box_shadow="0 20px 60px rgba(0,0,0,0.15)",
            max_height="90vh",
            overflow_y="auto",
        ),
        open=FoodState.carta_prod_modal,
        on_open_change=FoodState.set_carta_prod_modal,
    )


def _grupo_mod_row(grupo: GrupoModificadorAdminView) -> rx.Component:
    return rx.hstack(
        rx.vstack(
            rx.text(grupo.nombre, font_size="13px", font_weight="600", color=TEXT_PRIMARY),
            rx.hstack(
                rx.text(
                    grupo.opciones_count.to_string() + " opciones",
                    font_size="11px", color=TEXT_MUTED,
                ),
                rx.text("·", color="var(--twk-slate-300)", font_size="10px"),
                rx.text(
                    grupo.productos_count.to_string() + " productos",
                    font_size="11px", color=TEXT_MUTED,
                ),
                rx.text("·", color="var(--twk-slate-300)", font_size="10px"),
                rx.text(
                    "mín " + grupo.min_selecciones.to_string() + " / máx " + grupo.max_selecciones.to_string(),
                    font_size="11px", color=TEXT_MUTED,
                ),
                spacing="1", align="center", flex_wrap="wrap",
            ),
            spacing="0", align="start", flex="1", min_width="0",
        ),
        rx.button(
            "Editar",
            on_click=FoodState.editar_grupo_modificador(grupo.id),
            background="rgba(234,88,12,0.08)", color=ACCENT,
            border="1px solid rgba(234,88,12,0.40)", border_radius="6px",
            font_size="10px", cursor="pointer",
            padding_x="7px", padding_y="3px",
            _hover={"opacity": "0.85"},
        ),
        rx.button(
            rx.icon(tag="trash_2", size=12, color="var(--twk-danger-text)"),
            on_click=FoodState.eliminar_grupo_modificador(grupo.id),
            background="rgba(239,68,68,0.08)", border="1px solid #FECACA",
            border_radius="6px", cursor="pointer",
            padding_x="7px", padding_y="3px",
            _hover={"opacity": "0.85"},
        ),
        width="100%", align="center",
        padding="8px 10px", background=DARK_800,
        border_radius="8px", border=f"1px solid {DARK_700}",
        gap="8px",
    )


def _mod_grupo_modal() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.dialog.title(
                    rx.cond(FoodState.mod_grupo_form_id > 0, "Editar grupo", "Nuevo grupo de modificadores"),
                    font_size="16px", font_weight="700", color=TEXT_PRIMARY, margin="0",
                ),
                rx.input(
                    placeholder="Nombre del grupo (ej: Tamaño, Extras, Término)",
                    value=FoodState.mod_grupo_form_nombre,
                    on_change=FoodState.set_mod_grupo_form_nombre,
                    background=SURFACE_BASE, border=f"1px solid {DARK_700}",
                    color=TEXT_PRIMARY, border_radius="8px",
                    padding="8px 12px", font_size="13px", width="100%",
                    _focus={"border_color": "#EA580C"},
                ),
                rx.hstack(
                    rx.vstack(
                        rx.text("Mín selecciones", font_size="11px", color=TEXT_MUTED),
                        rx.input(
                            value=FoodState.mod_grupo_form_min,
                            on_change=FoodState.set_mod_grupo_form_min,
                            type="number", min="0", width="80px",
                            background=SURFACE_BASE, border=f"1px solid {DARK_700}",
                            color=TEXT_PRIMARY, border_radius="8px",
                            padding="6px 10px", font_size="13px",
                        ),
                        spacing="1",
                    ),
                    rx.vstack(
                        rx.text("Máx selecciones", font_size="11px", color=TEXT_MUTED),
                        rx.input(
                            value=FoodState.mod_grupo_form_max,
                            on_change=FoodState.set_mod_grupo_form_max,
                            type="number", min="1", width="80px",
                            background=SURFACE_BASE, border=f"1px solid {DARK_700}",
                            color=TEXT_PRIMARY, border_radius="8px",
                            padding="6px 10px", font_size="13px",
                        ),
                        spacing="1",
                    ),
                    spacing="3",
                ),
                rx.text("Opciones", font_size="13px", font_weight="600", color="var(--twk-slate-300)"),
                rx.vstack(
                    rx.foreach(
                        FoodState.mod_opciones_form,
                        lambda op, idx: rx.hstack(
                            rx.input(
                                placeholder="Nombre opción",
                                value=op["nombre"].to(str),
                                on_change=lambda v: FoodState.set_opcion_mod_nombre(idx.to_string() + "|" + v),
                                flex="1", min_width="100px",
                                background=SURFACE_BASE, border=f"1px solid {DARK_700}",
                                color=TEXT_PRIMARY, border_radius="6px",
                                padding="5px 8px", font_size="12px",
                            ),
                            rx.input(
                                placeholder="+S/",
                                value=op["precio_extra"].to(str),
                                on_change=lambda v: FoodState.set_opcion_mod_precio(idx.to_string() + "|" + v),
                                type="number", step="0.50", width="80px",
                                background=SURFACE_BASE, border=f"1px solid {DARK_700}",
                                color=TEXT_PRIMARY, border_radius="6px",
                                padding="5px 8px", font_size="12px",
                            ),
                            rx.button(
                                rx.icon(tag="x", size=12, color="var(--twk-danger-text)"),
                                on_click=FoodState.eliminar_opcion_mod_form(idx),
                                background="rgba(239,68,68,0.08)", border="1px solid #FECACA",
                                border_radius="6px", padding="4px", cursor="pointer",
                            ),
                            spacing="2", align="center", width="100%",
                        ),
                    ),
                    spacing="2", width="100%",
                ),
                rx.button(
                    rx.hstack(
                        rx.icon(tag="plus", size=12),
                        rx.text("Agregar opción", font_size="12px"),
                        spacing="1", align="center",
                    ),
                    on_click=FoodState.agregar_opcion_mod_form,
                    background=PAGE_BACKGROUND, color=TEXT_MUTED,
                    border="1px dashed var(--twk-slate-300)", border_radius="6px",
                    font_size="12px", cursor="pointer", width="100%",
                    padding_y="6px",
                    _hover={"background": DARK_700},
                ),
                rx.hstack(
                    rx.dialog.close(
                        rx.button(
                            "Cancelar",
                            background=DARK_800, color=TEXT_MUTED,
                            border=f"1px solid {DARK_700}", border_radius="8px",
                            font_size="13px", cursor="pointer",
                            padding_x="14px", padding_y="8px",
                        ),
                    ),
                    rx.button(
                        "Guardar",
                        on_click=FoodState.guardar_grupo_modificador,
                        background=ACCENT, color=TEXT_WHITE,
                        border_radius="8px", font_size="13px",
                        font_weight="700", cursor="pointer",
                        padding_x="14px", padding_y="8px",
                        _hover={"background": ACCENT_HOVER},
                    ),
                    spacing="3", justify="end", width="100%",
                ),
                spacing="3", width="100%",
            ),
            max_width="500px", width="90vw",
            max_height="90vh", overflow_y="auto",
            background=PAGE_BACKGROUND,
            border=f"1px solid {DARK_800}",
        ),
        open=FoodState.mod_grupo_modal,
        on_open_change=FoodState.set_mod_grupo_modal,
    )


def _mod_asignar_modal() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.dialog.title(
                    "Modificadores de " + FoodState.mod_asignar_producto_nombre,
                    font_size="15px", font_weight="700", color=TEXT_PRIMARY, margin="0",
                ),
                rx.text(
                    "Selecciona los grupos que aplican a este producto",
                    font_size="12px", color=TEXT_MUTED,
                ),
                rx.cond(
                    FoodState.grupos_modificadores.length() == 0,
                    rx.text(
                        "No hay grupos definidos. Crea uno primero en la sección Modificadores.",
                        font_size="12px", color=TEXT_MUTED,
                    ),
                    rx.vstack(
                        rx.foreach(
                            FoodState.grupos_modificadores,
                            lambda g: rx.hstack(
                                rx.checkbox(
                                    checked=FoodState.mod_asignar_grupo_ids.contains(g.id),
                                    on_change=lambda _v: FoodState.toggle_mod_asignar_grupo(g.id),
                                ),
                                rx.text(g.nombre, font_size="13px", color=TEXT_PRIMARY, font_weight="500"),
                                rx.text(
                                    g.opciones_count.to_string() + " opc.",
                                    font_size="11px", color=TEXT_MUTED,
                                ),
                                spacing="2", align="center", width="100%",
                                padding="6px 8px",
                                border_radius="6px",
                                cursor="pointer",
                                _hover={"background": DARK_700},
                            ),
                        ),
                        spacing="1", width="100%",
                    ),
                ),
                rx.hstack(
                    rx.dialog.close(
                        rx.button(
                            "Cancelar",
                            background=DARK_800, color=TEXT_MUTED,
                            border=f"1px solid {DARK_700}", border_radius="8px",
                            font_size="13px", cursor="pointer",
                            padding_x="14px", padding_y="8px",
                        ),
                    ),
                    rx.button(
                        "Guardar",
                        on_click=FoodState.guardar_mod_asignacion,
                        background=ACCENT, color=TEXT_WHITE,
                        border_radius="8px", font_size="13px",
                        font_weight="700", cursor="pointer",
                        padding_x="14px", padding_y="8px",
                        _hover={"background": ACCENT_HOVER},
                    ),
                    spacing="3", justify="end", width="100%",
                ),
                spacing="3", width="100%",
            ),
            max_width="420px", width="90vw",
            max_height="90vh", overflow_y="auto",
            background=PAGE_BACKGROUND,
            border=f"1px solid {DARK_800}",
        ),
        open=FoodState.mod_asignar_modal,
        on_open_change=FoodState.set_mod_asignar_modal,
    )


def _combo_row(combo: dict) -> rx.Component:
    return rx.hstack(
        rx.text(combo["emoji"].to(str), font_size="16px", flex_shrink="0"),
        rx.vstack(
            rx.text(combo["nombre"].to(str), font_size="13px", font_weight="600", color=TEXT_PRIMARY),
            rx.text(combo["items_texto"].to(str), font_size="11px", color=TEXT_MUTED, no_of_lines=1),
            spacing="0", flex="1", min_width="0",
        ),
        rx.text(combo["precio_texto"].to(str), font_size="13px", font_weight="700", color=ACCENT, flex_shrink="0"),
        rx.hstack(
            rx.tooltip(
                rx.icon_button(
                    rx.icon(tag="pencil", size=12),
                    on_click=FoodState.editar_combo(combo["id"].to(int)),
                    background="transparent", color=TEXT_MUTED, border="none", size="1",
                    cursor="pointer", _hover={"color": "var(--twk-text-primary)"},
                ),
                content="Editar combo",
            ),
            rx.tooltip(
                rx.icon_button(
                    rx.icon(tag=rx.cond(combo["activo"].to(bool), "eye", "eye_off"), size=12),
                    on_click=FoodState.toggle_combo_activo(combo["id"].to(int)),
                    background="transparent",
                    color=rx.cond(combo["activo"].to(bool), "#16A34A", "var(--twk-slate-400)"),
                    border="none", size="1", cursor="pointer",
                ),
                content=rx.cond(combo["activo"].to(bool), "Ocultar de la carta", "Mostrar en la carta"),
            ),
            rx.tooltip(
                rx.icon_button(
                    rx.icon(tag="trash_2", size=12),
                    on_click=FoodState.eliminar_combo(combo["id"].to(int)),
                    background="transparent", color=DANGER_TEXT, border="none", size="1",
                    cursor="pointer", _hover={"color": "var(--twk-danger-text)"},
                ),
                content="Eliminar combo",
            ),
            spacing="1",
        ),
        width="100%", align="center", spacing="3",
        padding="10px 12px",
        border=f"1px solid {DARK_700}", border_radius="8px",
        background=rx.cond(combo["activo"].to(bool), "var(--twk-d800)", "var(--twk-d900)"),
        opacity=rx.cond(combo["activo"].to(bool), "1", "0.6"),
    )


def _combo_item_form_row(item: dict, idx: int) -> rx.Component:
    return rx.hstack(
        rx.select(
            FoodState.productos.to(list).map(
                lambda p: p.nombre
            ),
            placeholder="Seleccionar producto...",
            value=rx.cond(
                item["producto_id"].to(str) != "",
                FoodState.productos.to(list)[item["producto_id"].to(int)].nombre,
                "",
            ),
            on_change=lambda v: FoodState.combo_set_item_field(idx.to_string() + "|producto_id|" + v),
            width="100%",
        ),
    )


def _combo_modal() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.hstack(
                    rx.dialog.title(
                        rx.cond(FoodState.combo_form_id > 0, "Editar Combo", "Nuevo Combo"),
                        font_size="16px", font_weight="700", color=TEXT_PRIMARY, margin="0",
                    ),
                    rx.spacer(),
                    rx.dialog.close(
                        rx.box(rx.icon(tag="x", size=16, color=TEXT_MUTED),
                               cursor="pointer", padding="4px", border_radius="6px",
                               _hover={"background": DARK_700}),
                    ),
                    width="100%", align="center",
                ),
                rx.vstack(
                    rx.text("Nombre", font_size="12px", font_weight="600", color="var(--twk-slate-300)"),
                    rx.input(
                        value=FoodState.combo_form_nombre,
                        on_change=FoodState.set_combo_form_nombre,
                        placeholder="Ej: Combo Hamburguesa",
                        border=f"1px solid {DARK_700}", border_radius="6px",
                        font_size="13px", width="100%",
                        _focus={"border": f"1px solid {ACCENT}"},
                    ),
                    spacing="1", width="100%",
                ),
                rx.hstack(
                    rx.vstack(
                        rx.text("Precio", font_size="12px", font_weight="600", color="var(--twk-slate-300)"),
                        rx.input(
                            value=FoodState.combo_form_precio,
                            on_change=FoodState.set_combo_form_precio,
                            placeholder="25.00",
                            border=f"1px solid {DARK_700}", border_radius="6px",
                            font_size="13px", width="100%",
                            _focus={"border": f"1px solid {ACCENT}"},
                        ),
                        spacing="1", flex="1",
                    ),
                    rx.vstack(
                        rx.text("Emoji", font_size="12px", font_weight="600", color="var(--twk-slate-300)"),
                        rx.input(
                            value=FoodState.combo_form_emoji,
                            on_change=FoodState.set_combo_form_emoji,
                            placeholder="🍱",
                            border=f"1px solid {DARK_700}", border_radius="6px",
                            font_size="13px", width="80px",
                            _focus={"border": f"1px solid {ACCENT}"},
                        ),
                        spacing="1",
                    ),
                    width="100%", spacing="3",
                ),
                rx.vstack(
                    rx.text("Descripción (opcional)", font_size="12px", font_weight="600", color="var(--twk-slate-300)"),
                    rx.text_area(
                        value=FoodState.combo_form_descripcion,
                        on_change=FoodState.set_combo_form_descripcion,
                        placeholder="Ej: Incluye hamburguesa, papas fritas y bebida",
                        border=f"1px solid {DARK_700}", border_radius="6px",
                        font_size="12px", width="100%", rows="2",
                        _focus={"border": f"1px solid {ACCENT}"},
                    ),
                    spacing="1", width="100%",
                ),
                rx.vstack(
                    rx.hstack(
                        rx.text("Productos del combo", font_size="12px", font_weight="600", color="var(--twk-slate-300)"),
                        rx.spacer(),
                        rx.button(
                            rx.hstack(rx.icon(tag="plus", size=10), rx.text("Agregar", font_size="10px"), spacing="1", align="center"),
                            on_click=FoodState.combo_add_item,
                            background=DARK_800, color=TEXT_MUTED,
                            border=f"1px solid {DARK_700}", border_radius="5px",
                            cursor="pointer", padding_x="8px", padding_y="3px",
                            _hover={"background": DARK_700},
                        ),
                        width="100%", align="center",
                    ),
                    rx.vstack(
                        rx.foreach(
                            FoodState.combo_form_items,
                            lambda item, idx: rx.hstack(
                                rx.input(
                                    value=item["producto_id"].to(str),
                                    on_change=lambda v: FoodState.combo_set_item_field(idx.to_string() + "|producto_id|" + v),
                                    placeholder="ID producto",
                                    border=f"1px solid {DARK_700}", border_radius="6px",
                                    font_size="12px", flex="1",
                                    _focus={"border": f"1px solid {ACCENT}"},
                                ),
                                rx.input(
                                    value=item["cantidad"].to(str),
                                    on_change=lambda v: FoodState.combo_set_item_field(idx.to_string() + "|cantidad|" + v),
                                    placeholder="Cant",
                                    border=f"1px solid {DARK_700}", border_radius="6px",
                                    font_size="12px", width="60px",
                                    _focus={"border": f"1px solid {ACCENT}"},
                                ),
                                rx.icon_button(
                                    rx.icon(tag="trash_2", size=11),
                                    on_click=FoodState.combo_remove_item(idx),
                                    background="transparent", color=DANGER_TEXT,
                                    border="none", size="1", cursor="pointer",
                                ),
                                spacing="2", width="100%", align="center",
                            ),
                        ),
                        spacing="2", width="100%",
                    ),
                    spacing="2", width="100%",
                ),
                rx.button(
                    rx.cond(FoodState.combo_form_id > 0, "Guardar cambios", "Crear Combo"),
                    on_click=FoodState.guardar_combo,
                    background=ACCENT, color=TEXT_WHITE,
                    border_radius="8px", font_size="13px", font_weight="700",
                    width="100%", cursor="pointer",
                    _hover={"background": ACCENT_HOVER},
                ),
                spacing="3", width="100%",
            ),
            background=PAGE_BACKGROUND,
            border=f"1px solid {DARK_800}",
            border_radius="14px",
            padding="20px",
            max_width="480px",
            width="90vw",
            max_height="90vh",
            overflow_y="auto",
        ),
        open=FoodState.combo_modal,
        on_open_change=FoodState.set_combo_modal,
    )


def _combos_section() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.text("Combos", font_size="15px", font_weight="700", color=TEXT_MUTED),
            rx.badge(
                FoodState.combos_admin.length().to_string(),
                background="rgba(245,158,11,0.12)", color="var(--twk-warning-text)",
                border_radius="12px", font_size="11px", font_weight="700",
                padding_x="8px",
            ),
            rx.spacer(),
            rx.button(
                rx.hstack(
                    rx.icon(tag="plus", size=12),
                    rx.text("Nuevo Combo", font_size="11px", font_weight="700"),
                    spacing="1", align="center",
                ),
                on_click=FoodState.abrir_combo_modal,
                background="rgba(245,158,11,0.12)", color="var(--twk-warning-text)",
                border="1px solid rgba(245,158,11,0.25)", border_radius="6px",
                cursor="pointer", padding_x="10px", padding_y="5px",
                _hover={"background": "rgba(245,158,11,0.20)"},
            ),
            spacing="2", align="center", width="100%",
        ),
        rx.cond(
            FoodState.combos_admin.length() == 0,
            rx.box(
                rx.text(
                    "Sin combos. Crea uno para ofrecer paquetes a precio fijo (ej: hamburguesa + papas + bebida).",
                    font_size="12px", color=TEXT_MUTED, text_align="center",
                ),
                padding="24px 16px", width="100%",
            ),
            rx.vstack(
                rx.foreach(FoodState.combos_admin, _combo_row),
                spacing="2", width="100%",
            ),
        ),
        spacing="3",
        width="100%",
        class_name="twk-panel",
    )


def _modificadores_section() -> rx.Component:
    return rx.vstack(
        rx.hstack(
            rx.text("Modificadores", font_size="15px", font_weight="700", color=TEXT_MUTED),
            rx.badge(
                FoodState.grupos_modificadores.length().to_string(),
                background="rgba(124,58,237,0.12)", color="#7C3AED",
                border_radius="12px", font_size="11px", font_weight="700",
                padding_x="8px",
            ),
            rx.spacer(),
            rx.button(
                rx.hstack(
                    rx.icon(tag="plus", size=12),
                    rx.text("Nuevo Grupo", font_size="11px", font_weight="700"),
                    spacing="1", align="center",
                ),
                on_click=FoodState.abrir_mod_grupo_modal,
                background="rgba(124,58,237,0.12)", color="#7C3AED",
                border="1px solid rgba(124,58,237,0.30)", border_radius="6px",
                cursor="pointer", padding_x="10px", padding_y="5px",
                _hover={"background": "rgba(124,58,237,0.20)"},
            ),
            spacing="2", align="center", width="100%",
        ),
        rx.cond(
            FoodState.grupos_modificadores.length() == 0,
            rx.box(
                rx.text(
                    "Sin grupos de modificadores. Crea uno para agregar opciones como tamaño, extras o término de cocción.",
                    font_size="12px", color=TEXT_MUTED, text_align="center",
                ),
                padding="24px 16px", width="100%",
            ),
            rx.vstack(
                rx.foreach(FoodState.grupos_modificadores, _grupo_mod_row),
                spacing="2", width="100%",
            ),
        ),
        spacing="3",
        width="100%",
        class_name="twk-panel",
    )


def _carta_ayuda() -> rx.Component:
    return ayuda_modal(
        titulo="¿Cómo funciona la Carta?",
        subtitulo="Todo lo que vendes se arma acá",
        secciones=[
            {"titulo": "Las 4 piezas", "pasos": [
                "Categorías: ordenan la carta (ej. Entradas, Platos, Bebidas). Arrástralas para cambiar el orden.",
                "Productos: cada ítem con precio, foto y estación (Cocina o Barra).",
                "Modificadores: opciones que el mozo elige al pedir (ej. término de cocción, sin cebolla).",
                "Combos: varios productos en un paquete a precio fijo.",
            ]},
            {"titulo": "Dónde repercute", "pasos": [
                "Lo que cargas acá aparece al toque en Mozos, Mostrador y en tu carta digital QR.",
                "La estación decide a qué pantalla de cocina llega cada producto.",
                "Si un producto tiene receta en Inventario, al venderse descuenta el stock solo.",
            ]},
        ],
    )


def _eliminar_prod_modal() -> rx.Component:
    return rx.dialog.root(
        rx.dialog.content(
            rx.vstack(
                rx.hstack(
                    rx.box(
                        rx.icon(tag="triangle_alert", size=20, color=DANGER_TEXT),
                        background="rgba(239,68,68,0.12)",
                        border_radius="10px", padding="10px",
                        display="flex", align_items="center", justify_content="center",
                    ),
                    rx.vstack(
                        rx.dialog.title(
                            "Eliminar producto",
                            font_size="16px", font_weight="800", color=TEXT_PRIMARY, margin="0",
                        ),
                        rx.text(
                            FoodState.carta_eliminar_prod_nombre,
                            font_size="13px", font_weight="600", color=TEXT_MUTED,
                        ),
                        spacing="0", align="start",
                    ),
                    spacing="3", align="center", width="100%",
                ),
                rx.box(height="1px", width="100%", background=DARK_800),
                # Producto con ventas/uso → se archiva; sin uso → se borra de verdad.
                rx.cond(
                    FoodState.carta_eliminar_prod_en_uso,
                    rx.vstack(
                        rx.text(
                            "Este producto tiene historial de ventas (o está en un "
                            "combo/promoción), así que se archivará en lugar de borrarse.",
                            font_size="13px", color="var(--twk-slate-300)", line_height="1.5",
                        ),
                        rx.text(
                            "Desaparecerá de la carta y del punto de venta, pero sus "
                            "ventas anteriores seguirán en los reportes.",
                            font_size="12px", color=TEXT_MUTED, line_height="1.5",
                        ),
                        spacing="2", width="100%", align="start",
                    ),
                    rx.text(
                        "Este producto nunca se ha vendido, así que se eliminará "
                        "definitivamente de la carta. Esta acción no se puede deshacer.",
                        font_size="13px", color="var(--twk-slate-300)", line_height="1.5",
                    ),
                ),
                rx.box(height="1px", width="100%", background=DARK_800),
                rx.hstack(
                    rx.button(
                        "Cancelar",
                        on_click=FoodState.cancelar_eliminar_producto,
                        background=DARK_800,
                        color=TEXT_MUTED,
                        border=f"1px solid {DARK_700}",
                        border_radius="8px",
                        font_size="13px",
                        cursor="pointer",
                        flex="1",
                        _hover={"opacity": "0.85"},
                    ),
                    rx.button(
                        rx.cond(
                            FoodState.carta_eliminar_prod_en_uso,
                            "Archivar producto",
                            "Eliminar definitivamente",
                        ),
                        on_click=FoodState.confirmar_eliminar_producto,
                        background=DANGER_SOLID,
                        color=TEXT_WHITE,
                        border_radius="8px",
                        font_size="13px",
                        font_weight="700",
                        cursor="pointer",
                        flex="1",
                        _hover={"opacity": "0.9"},
                    ),
                    spacing="2", width="100%",
                ),
                spacing="3",
                width="100%",
            ),
            max_width="440px",
            width="90vw",
            background=PAGE_BACKGROUND,
            border=f"1px solid {DARK_800}",
            border_radius="16px",
            padding="24px",
            box_shadow="0 20px 60px rgba(0,0,0,0.15)",
        ),
        open=FoodState.carta_eliminar_prod_modal,
        on_open_change=FoodState.set_carta_eliminar_prod_modal,
    )


def _carta_content() -> rx.Component:
    return rx.vstack(
        _cat_modal(),
        _prod_modal(),
        _mod_grupo_modal(),
        _mod_asignar_modal(),
        _combo_modal(),
        _eliminar_prod_modal(),
        _carta_ayuda(),
        # ── Header ────────────────────────────────────────────────────────────
        rx.hstack(
            rx.vstack(
                rx.text("Carta", font_size="22px", font_weight="800", color=TEXT_PRIMARY),
                rx.text("Categorías y productos de la carta", font_size="13px", color=TEXT_MUTED),
                spacing="0",
            ),
            rx.spacer(),
            ayuda_trigger(),
            rx.hstack(
                rx.button(
                    rx.hstack(
                        rx.icon(tag="download", size=14),
                        rx.text("Exportar stock", font_size="13px", font_weight="700"),
                        spacing="1", align="center",
                    ),
                    on_click=FoodState.exportar_stock_carta_excel,
                    background="rgba(34,197,94,0.08)",
                    color=SUCCESS_TEXT,
                    border="1px solid rgba(34,197,94,0.35)",
                    border_radius="8px",
                    cursor="pointer",
                    padding_x="14px",
                    padding_y="8px",
                    _hover={"background": "rgba(34,197,94,0.14)"},
                ),
                rx.button(
                    rx.hstack(
                        rx.icon(tag="plus", size=14),
                        rx.text("Nueva Categoría", font_size="13px", font_weight="700"),
                        spacing="1", align="center",
                    ),
                    on_click=FoodState.abrir_cat_modal,
                    background="rgba(234,88,12,0.08)",
                    color=ACCENT,
                    border="1px solid rgba(234,88,12,0.40)",
                    border_radius="8px",
                    cursor="pointer",
                    padding_x="14px",
                    padding_y="8px",
                    _hover={"background": "rgba(234,88,12,0.12)"},
                ),
                rx.button(
                    rx.hstack(
                        rx.icon(tag="plus", size=14),
                        rx.text("Nuevo Producto", font_size="13px", font_weight="700"),
                        spacing="1", align="center",
                    ),
                    on_click=FoodState.abrir_prod_modal,
                    background=ACCENT,
                    color=TEXT_WHITE,
                    border_radius="8px",
                    cursor="pointer",
                    padding_x="14px",
                    padding_y="8px",
                    _hover={"background": ACCENT_HOVER},
                ),
                spacing="2",
                flex_wrap="wrap",
            ),
            width="100%",
            align="center",
            flex_wrap="wrap",
            gap="12px",
        ),
        # ── Columnas ──────────────────────────────────────────────────────────
        rx.flex(
            # ─── Categorias ───────────────────────────────────────────────
            rx.vstack(
                rx.hstack(
                    rx.text("Categorías", font_size="15px", font_weight="700", color=TEXT_MUTED),
                    rx.badge(
                        FoodState.categorias.length().to_string(),
                        background=DARK_800, color=TEXT_MUTED,
                        border_radius="12px", font_size="11px", font_weight="700",
                        padding_x="8px",
                    ),
                    spacing="2", align="center", width="100%",
                ),
                rx.cond(
                    FoodState.categorias.length() == 0,
                    empty_state(
                        icono="folder_plus",
                        titulo="Sin categorías",
                        texto="Agrupa tus productos en categorías (Bebidas, Platos, Postres) para ordenar la carta.",
                        cta_label="Nueva Categoría",
                        cta_on_click=FoodState.abrir_cat_modal,
                    ),
                    rx.vstack(
                        rx.foreach(FoodState.categorias, _categoria_row),
                        spacing="2",
                        width="100%",
                    ),
                ),
                spacing="3",
                flex="1",
                min_width="0",
                class_name="twk-panel",
            ),
            rx.divider(orientation="vertical", border_color="var(--twk-d700)", height="auto",
                       class_name="twk-sep"),
            # ─── Productos ────────────────────────────────────────────────
            rx.vstack(
                # encabezado
                rx.hstack(
                    rx.text("Productos", font_size="15px", font_weight="700", color=TEXT_MUTED),
                    rx.badge(
                        rx.cond(
                            FoodState.carta_ver_archivados,
                            FoodState.productos_archivados.length().to_string(),
                            FoodState.carta_productos_filtrados_count.to_string(),
                        ),
                        background=DARK_800, color=TEXT_MUTED,
                        border_radius="12px", font_size="11px", font_weight="700",
                        padding_x="8px",
                    ),
                    rx.spacer(),
                    rx.cond(
                        FoodState.productos_archivados.length() > 0,
                        rx.button(
                            rx.hstack(
                                rx.icon(
                                    tag=rx.cond(FoodState.carta_ver_archivados, "arrow_left", "archive"),
                                    size=13,
                                ),
                                rx.text(
                                    rx.cond(
                                        FoodState.carta_ver_archivados,
                                        "Ver activos",
                                        "Archivados (" + FoodState.productos_archivados.length().to_string() + ")",
                                    ),
                                    font_size="12px", font_weight="700",
                                ),
                                spacing="1", align="center",
                            ),
                            on_click=FoodState.toggle_carta_ver_archivados,
                            background=rx.cond(FoodState.carta_ver_archivados, "rgba(148,163,184,0.18)", "transparent"),
                            color=TEXT_MUTED,
                            border=f"1px solid {DARK_700}",
                            border_radius="8px", cursor="pointer",
                            padding_x="10px", padding_y="5px",
                            _hover={"background": "var(--twk-d700)"},
                        ),
                        rx.fragment(),
                    ),
                    spacing="2", align="center", width="100%",
                ),
                # Vista de archivados (restaurar) o catálogo normal (buscador+lista)
                rx.cond(
                    FoodState.carta_ver_archivados,
                    rx.cond(
                        FoodState.productos_archivados.length() > 0,
                        rx.vstack(
                            rx.foreach(FoodState.productos_archivados, _producto_archivado_row),
                            spacing="2", width="100%",
                        ),
                        rx.box(
                            rx.text(
                                "No hay productos archivados.",
                                font_size="13px", color=TEXT_MUTED, text_align="center",
                            ),
                            padding="32px 16px", width="100%",
                        ),
                    ),
                    rx.vstack(
                        # buscador
                        rx.hstack(
                    rx.icon(tag="search", size=14, color=TEXT_MUTED, flex_shrink="0"),
                    rx.input(
                        placeholder="Buscar producto o categoría...",
                        value=FoodState.carta_busqueda_productos,
                        on_change=FoodState.set_carta_busqueda_productos,
                        border="none",
                        outline="none",
                        background="transparent",
                        color=TEXT_PRIMARY,
                        font_size="13px",
                        flex="1",
                        _placeholder={"color": "var(--twk-slate-400)"},
                    ),
                    rx.cond(
                        FoodState.carta_busqueda_productos != "",
                        rx.icon_button(
                            rx.icon(tag="x", size=12),
                            on_click=FoodState.set_carta_busqueda_productos(""),
                            background="transparent",
                            color=TEXT_MUTED,
                            border="none",
                            size="1",
                            cursor="pointer",
                            _hover={"color": "var(--twk-text-primary)"},
                        ),
                        rx.fragment(),
                    ),
                    background=PAGE_BACKGROUND,
                    border=f"1px solid {DARK_700}",
                    border_radius="8px",
                    padding_x="10px",
                    padding_y="5px",
                    align="center",
                    width="100%",
                ),
                # lista paginada
                rx.cond(
                    FoodState.carta_productos_filtrados_count == 0,
                    rx.cond(
                        FoodState.carta_busqueda_productos != "",
                        rx.box(
                            rx.text(
                                "Sin resultados para esa búsqueda.",
                                font_size="13px", color=TEXT_MUTED, text_align="center",
                            ),
                            padding="32px 16px",
                            width="100%",
                        ),
                        empty_state(
                            icono="utensils_crossed",
                            titulo="Sin productos todavía",
                            texto="Crea tu primer producto para que aparezca en la carta de mozos, caja y el QR.",
                            cta_label="Nuevo Producto",
                            cta_on_click=FoodState.abrir_prod_modal,
                        ),
                    ),
                    rx.vstack(
                        rx.foreach(FoodState.carta_productos_paginados, _producto_row),
                        spacing="2",
                        width="100%",
                    ),
                ),
                # paginación
                rx.cond(
                    FoodState.carta_productos_total_paginas > 1,
                    rx.hstack(
                        rx.button(
                            rx.icon(tag="chevron_left", size=14),
                            on_click=FoodState.carta_pagina_anterior,
                            disabled=FoodState.carta_productos_pagina <= 1,
                            background=DARK_800,
                            color=TEXT_MUTED,
                            border=f"1px solid {DARK_700}",
                            border_radius="6px",
                            padding_x="8px",
                            padding_y="4px",
                            cursor="pointer",
                            _hover={"background": DARK_700},
                            _disabled={"opacity": "0.4", "cursor": "not-allowed"},
                        ),
                        rx.text(
                            "Página ",
                            rx.text.span(
                                FoodState.carta_productos_pagina.to_string(),
                                font_weight="700", color=ACCENT,
                            ),
                            " de ",
                            FoodState.carta_productos_total_paginas.to_string(),
                            font_size="12px",
                            color=TEXT_MUTED,
                            white_space="nowrap",
                        ),
                        rx.button(
                            rx.icon(tag="chevron_right", size=14),
                            on_click=FoodState.carta_pagina_siguiente,
                            disabled=FoodState.carta_productos_pagina >= FoodState.carta_productos_total_paginas,
                            background=DARK_800,
                            color=TEXT_MUTED,
                            border=f"1px solid {DARK_700}",
                            border_radius="6px",
                            padding_x="8px",
                            padding_y="4px",
                            cursor="pointer",
                            _hover={"background": DARK_700},
                            _disabled={"opacity": "0.4", "cursor": "not-allowed"},
                        ),
                        justify="center",
                        align="center",
                        width="100%",
                        padding_top="4px",
                        gap="12px",
                    ),
                    rx.fragment(),
                ),
                        spacing="3", width="100%",
                    ),
                ),
                spacing="3",
                flex="1",
                min_width="0",
                class_name="twk-panel",
            ),
            gap="5",
            width="100%",
            align="start",
            class_name="twk-cols-lg",
        ),
        _combos_section(),
        _modificadores_section(),
        spacing="5",
        width="100%",
    )


@rx.page(route="/carta", on_load=FoodState.on_load_carta, title="TUWAYKIFOOD | Carta")
def carta_page() -> rx.Component:
    return app_shell(_carta_content(), page_key="carta")
