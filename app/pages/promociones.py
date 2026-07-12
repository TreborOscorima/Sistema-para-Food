"""Página de gestión de promociones y happy hours."""

from __future__ import annotations

import reflex as rx

from app.states.food_state import FoodState, PromocionView, AdminLocalState
from app.pages.dono import _dono_shell, AdminPanelState


def _tipo_label(tipo: str) -> rx.Component:
    return rx.cond(
        tipo == "PORCENTAJE",
        rx.badge("%", background="rgba(124,58,237,0.12)", color="#A78BFA",
                 border_radius="5px", font_size="10px", padding="2px 6px"),
        rx.cond(
            tipo == "MONTO_FIJO",
            rx.badge("S/", background="rgba(34,197,94,0.12)", color="#22C55E",
                     border_radius="5px", font_size="10px", padding="2px 6px"),
            rx.badge("HH", background="#FEF9C3", color="#713F12",
                     border_radius="5px", font_size="10px", padding="2px 6px"),
        ),
    )


def _promo_card(p: PromocionView) -> rx.Component:
    header_bg = rx.cond(p.activa, "#16A34A", "#94A3B8")
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.text(
                    rx.cond(p.activa, "🟢 ACTIVA", "⏸ PAUSADA"),
                    font_size="12px", font_weight="700", color="#FFFFFF",
                ),
                rx.spacer(),
                rx.cond(
                    p.aplica_ahora,
                    rx.text("Aplica ahora", font_size="11px", color="#FFFFFF", opacity="0.85"),
                    rx.fragment(),
                ),
                width="100%", align="center",
            ),
            background=header_bg, padding="12px 16px", width="100%",
        ),
        rx.vstack(
            rx.hstack(
                rx.text(p.nombre, font_size="16px", font_weight="800", color="#F1F5F9"),
                _tipo_label(p.tipo),
                spacing="2", align="center",
            ),
            rx.text(p.descuento_texto, font_size="13px", color="#94A3B8", line_height="1.4"),
            rx.cond(
                p.horario_texto != "",
                rx.text(p.horario_texto, font_size="11px", color="#94A3B8"),
                rx.fragment(),
            ),
            rx.text(p.dias_texto + " · " + p.alcance_texto, font_size="11px", color="#94A3B8"),
            rx.cond(
                p.auto_aplicar,
                rx.badge("Auto en caja", background="rgba(34,197,94,0.12)", color="#22C55E",
                         border_radius="6px", font_size="10px", font_weight="700"),
                rx.badge("Sugerencia manual", background="#1E293B", color="#94A3B8",
                         border_radius="6px", font_size="10px", font_weight="700"),
            ),
            rx.hstack(
                rx.link(
                    "Editar",
                    on_click=FoodState.editar_promocion(p.id),
                    font_size="12px", font_weight="600", color="#94A3B8",
                    cursor="pointer", padding="5px 10px",
                    border="1px solid #334155", border_radius="6px",
                    _hover={"border_color": "#94A3B8"},
                ),
                rx.link(
                    rx.cond(p.activa, "Pausar", "Activar"),
                    on_click=FoodState.toggle_promo_activa(p.id),
                    font_size="12px", font_weight="600",
                    color=rx.cond(p.activa, "#DC2626", "#EA580C"),
                    cursor="pointer", padding="5px 10px",
                    border=rx.cond(p.activa, "1px solid rgba(239,68,68,0.40)", "1px solid rgba(234,88,12,0.40)"),
                    border_radius="6px",
                    _hover={"opacity": "0.8"},
                ),
                spacing="2", justify="end", width="100%", margin_top="6px",
            ),
            spacing="2", align="start", width="100%", padding="16px",
        ),
        background="#1E293B",
        border=rx.cond(p.aplica_ahora, "2px solid #EA580C", "1px solid #334155"),
        border_radius="16px", overflow="hidden",
        opacity=rx.cond(p.activa, "1", "0.65"),
        width="100%",
    )


def _promo_form() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.hstack(
                rx.icon(
                    tag=rx.cond(FoodState.promo_form_editando, "pencil", "plus"),
                    size=13, color="#EA580C",
                ),
                rx.text(
                    rx.cond(FoodState.promo_form_editando, "Editar promoción", "Nueva promoción"),
                    font_size="13px", font_weight="700", color="#F1F5F9",
                ),
                spacing="1", align="center",
            ),
            rx.hstack(
                rx.vstack(
                    rx.text("Nombre *", font_size="11px", font_weight="600", color="#94A3B8"),
                    rx.input(
                        placeholder="Ej: 2x1 en cenas",
                        value=FoodState.promo_form_nombre,
                        on_change=FoodState.set_promo_form_nombre,
                        background="#0F172A", border="1px solid #334155",
                        border_radius="7px", font_size="13px",
                        padding_x="10px", padding_y="8px", width="100%",
                        _focus={"border": "1px solid #EA580C"},
                    ),
                    spacing="1", align="start", flex="2",
                ),
                rx.vstack(
                    rx.text("Tipo", font_size="11px", font_weight="600", color="#94A3B8"),
                    rx.select(
                        FoodState.tipos_promo_disponibles,
                        value=FoodState.promo_form_tipo,
                        on_change=FoodState.set_promo_form_tipo,
                        background="#0F172A", border="1px solid #334155",
                        border_radius="7px", font_size="13px", width="100%",
                    ),
                    spacing="1", align="start", flex="1",
                ),
                spacing="3", width="100%",
                class_name="twk-form-row",
            ),
            rx.hstack(
                rx.vstack(
                    rx.text("Valor (% ó S/)", font_size="11px", font_weight="600", color="#94A3B8"),
                    rx.input(
                        placeholder="Ej: 10",
                        value=FoodState.promo_form_valor,
                        on_change=FoodState.set_promo_form_valor,
                        type="number", min="0", step="0.01",
                        background="#0F172A", border="1px solid #334155",
                        border_radius="7px", font_size="13px",
                        padding_x="10px", padding_y="8px", width="100%",
                        _focus={"border": "1px solid #EA580C"},
                    ),
                    spacing="1", align="start", flex="1",
                ),
                rx.vstack(
                    rx.text("Hora inicio", font_size="11px", font_weight="600", color="#94A3B8"),
                    rx.input(
                        placeholder="18:00",
                        value=FoodState.promo_form_hora_inicio,
                        on_change=FoodState.set_promo_form_hora_inicio,
                        type="time",
                        background="#0F172A", border="1px solid #334155",
                        border_radius="7px", font_size="13px",
                        padding_x="10px", padding_y="8px", width="100%",
                        _focus={"border": "1px solid #EA580C"},
                    ),
                    spacing="1", align="start", flex="1",
                ),
                rx.vstack(
                    rx.text("Hora fin", font_size="11px", font_weight="600", color="#94A3B8"),
                    rx.input(
                        placeholder="21:00",
                        value=FoodState.promo_form_hora_fin,
                        on_change=FoodState.set_promo_form_hora_fin,
                        type="time",
                        background="#0F172A", border="1px solid #334155",
                        border_radius="7px", font_size="13px",
                        padding_x="10px", padding_y="8px", width="100%",
                        _focus={"border": "1px solid #EA580C"},
                    ),
                    spacing="1", align="start", flex="1",
                ),
                spacing="3", width="100%",
                class_name="twk-form-row",
            ),
            rx.vstack(
                rx.text("Descripción", font_size="11px", font_weight="600", color="#94A3B8"),
                rx.input(
                    placeholder="Descripción breve (opcional)",
                    value=FoodState.promo_form_descripcion,
                    on_change=FoodState.set_promo_form_descripcion,
                    background="#0F172A", border="1px solid #334155",
                    border_radius="7px", font_size="13px",
                    padding_x="10px", padding_y="8px", width="100%",
                    _focus={"border": "1px solid #EA580C"},
                ),
                spacing="1", align="start", width="100%",
            ),
            # Días de la semana
            rx.vstack(
                rx.text("Días en que aplica", font_size="11px", font_weight="600", color="#94A3B8"),
                rx.flex(
                    rx.foreach(
                        FoodState.promo_form_dias_ui,
                        lambda d: rx.box(
                            rx.text(d["abrev"].to_string(), font_size="12px", font_weight="700",
                                    color=rx.cond(d["activo"], "#FFFFFF", "#94A3B8")),
                            on_click=FoodState.toggle_promo_dia(d["bit"]),
                            background=rx.cond(d["activo"], "#EA580C", "#1E293B"),
                            border=rx.cond(d["activo"], "1px solid #EA580C", "1px solid #334155"),
                            border_radius="8px", padding="6px 10px", cursor="pointer",
                            _hover={"border_color": "#EA580C"},
                        ),
                    ),
                    gap="6px", flex_wrap="wrap", width="100%",
                ),
                spacing="1", align="start", width="100%",
            ),
            # Alcance
            rx.hstack(
                rx.vstack(
                    rx.text("Alcance", font_size="11px", font_weight="600", color="#94A3B8"),
                    rx.select(
                        ["todo", "categoria", "producto"],
                        value=FoodState.promo_form_alcance,
                        on_change=FoodState.set_promo_form_alcance,
                        background="#0F172A", border="1px solid #334155",
                        border_radius="7px", font_size="13px", width="100%",
                    ),
                    spacing="1", align="start", flex="1",
                ),
                rx.cond(
                    FoodState.promo_form_alcance == "categoria",
                    rx.vstack(
                        rx.text("Categoría", font_size="11px", font_weight="600", color="#94A3B8"),
                        rx.select(
                            FoodState.promo_categorias_nombres,
                            value=FoodState.promo_form_categoria_nombre,
                            on_change=FoodState.set_promo_form_categoria_nombre,
                            placeholder="— Elegir —",
                            width="100%",
                        ),
                        spacing="1", align="start", flex="2",
                    ),
                    rx.cond(
                        FoodState.promo_form_alcance == "producto",
                        rx.vstack(
                            rx.text("Producto", font_size="11px", font_weight="600", color="#94A3B8"),
                            rx.select(
                                FoodState.promo_productos_nombres,
                                value=FoodState.promo_form_producto_nombre,
                                on_change=FoodState.set_promo_form_producto_nombre,
                                placeholder="— Elegir —",
                                width="100%",
                            ),
                            spacing="1", align="start", flex="2",
                        ),
                        rx.fragment(),
                    ),
                ),
                spacing="3", width="100%", align="end",
            ),
            # Auto-aplicación
            rx.hstack(
                rx.switch(
                    checked=FoodState.promo_form_auto,
                    on_change=FoodState.set_promo_form_auto,
                    color_scheme="orange",
                ),
                rx.text("Aplicar automáticamente en caja", font_size="12px",
                        font_weight="600", color="#CBD5E1"),
                rx.text("(si no, queda como sugerencia)", font_size="11px", color="#94A3B8"),
                spacing="2", align="center", width="100%",
            ),
            rx.hstack(
                rx.button(
                    rx.cond(FoodState.promo_form_editando, "Actualizar", "Crear promoción"),
                    on_click=FoodState.guardar_promocion,
                    background="#EA580C", color="#FFFFFF",
                    border_radius="7px", font_size="13px", font_weight="700",
                    padding_x="16px", padding_y="8px", cursor="pointer",
                    _hover={"background": "#C2410C"},
                ),
                rx.button(
                    "Cancelar",
                    on_click=FoodState.cancelar_promo_form,
                    background="#1E293B", color="#94A3B8",
                    border="1px solid #334155", border_radius="7px",
                    font_size="13px", padding_x="16px", padding_y="8px",
                    cursor="pointer", _hover={"background": "#334155"},
                ),
                spacing="2", justify="end", width="100%",
            ),
            spacing="3", width="100%",
        ),
        background="#0F172A", border="1px solid #334155",
        border_radius="8px", padding="12px 14px", width="100%",
    )


def _promo_activa_banner() -> rx.Component:
    return rx.cond(
        FoodState.hay_promo_activa,
        rx.box(
            rx.hstack(
                rx.icon(tag="zap", size=14, color="#F59E0B"),
                rx.vstack(
                    rx.text(
                        "¡Promoción activa ahora: " + FoodState.promo_activa_nombre + "!",
                        font_size="13px", font_weight="700", color="#F1F5F9",
                    ),
                    rx.text(
                        FoodState.promo_activa_descuento_texto,
                        font_size="12px", color="#78350F",
                    ),
                    spacing="0", align="start",
                ),
                spacing="2", align="center", width="100%",
            ),
            background="rgba(245,158,11,0.10)", border="1px solid rgba(245,158,11,0.25)",
            border_radius="10px", padding="12px 16px", width="100%",
        ),
        rx.fragment(),
    )


def _promo_modal_content() -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.icon(
                tag=rx.cond(FoodState.promo_form_editando, "pencil", "circle_plus"),
                size=14, color="#EA580C",
            ),
            rx.text(
                rx.cond(FoodState.promo_form_editando, "Editar promoción", "Nueva promoción"),
                font_size="14px", font_weight="700", color="#F1F5F9",
            ),
            spacing="2", align="center", margin_bottom="12px",
        ),
        _promo_form(),
        width="100%",
    )


def _promo_nueva_placeholder() -> rx.Component:
    return rx.box(
        rx.text("🏷️", font_size="36px", line_height="1"),
        rx.text("Crear nueva promoción", font_size="14px", font_weight="700", color="#94A3B8",
                margin_top="8px"),
        rx.text("Descuento, combo, 2×1…", font_size="12px", color="#CBD5E1", margin_top="2px"),
        on_click=FoodState.abrir_nueva_promo,
        background="#1E293B", border="2px dashed #334155",
        border_radius="16px", padding="36px 16px",
        display="flex", flex_direction="column",
        align_items="center", justify_content="center",
        cursor="pointer", text_align="center", width="100%", height="100%",
        _hover={"border_color": "#EA580C", "background": "rgba(234,88,12,0.08)"},
    )


def _promo_tab_pill(key: str, icon_tag: str, label: str) -> rx.Component:
    activo = AdminPanelState.promo_tab == key
    return rx.button(
        rx.hstack(
            rx.icon(tag=icon_tag, size=13,
                    color=rx.cond(activo, "#FFFFFF", "#94A3B8")),
            rx.text(label, font_size="13px", font_weight="600",
                    color=rx.cond(activo, "#FFFFFF", "#94A3B8")),
            spacing="2", align="center",
        ),
        on_click=AdminPanelState.set_promo_tab(key),
        background=rx.cond(activo, "#EA580C", "transparent"),
        border="none",
        border_radius="7px",
        padding_x="14px", padding_y="7px",
        cursor="pointer",
        transition="all 0.15s ease",
        _hover={"background": rx.cond(activo, "#C2410C", "#334155")},
    )


def _promociones_content() -> rx.Component:
    from app.pages.cupones import _cupones_body

    return rx.vstack(
        # ── Header ──────────────────────────────────────────────────────
        rx.hstack(
            rx.vstack(
                rx.text("Promociones", font_size="22px", font_weight="800", color="#F1F5F9"),
                rx.text("Descuentos automáticos y cupones de código",
                        font_size="13px", color="#94A3B8"),
                spacing="0", align="start",
            ),
            rx.spacer(),
            # Botón contextual cambia según el tab activo
            rx.cond(
                AdminPanelState.promo_tab == "automaticas",
                rx.dialog.root(
                    rx.button(
                        rx.hstack(
                            rx.icon(tag="plus", size=13),
                            rx.text("Nueva promo", font_size="13px", font_weight="700"),
                            spacing="1", align="center",
                        ),
                        on_click=FoodState.abrir_nueva_promo,
                        background="#EA580C", color="#FFFFFF", border_radius="9px",
                        padding_x="16px", padding_y="9px", cursor="pointer",
                        _hover={"background": "#C2410C"},
                    ),
                    rx.dialog.content(
                        _promo_modal_content(),
                        background="#0F172A", border="1px solid #1E293B",
                    ),
                    open=FoodState.promo_form_visible,
                    on_open_change=FoodState.set_promo_form_visible,
                ),
                rx.button(
                    rx.hstack(
                        rx.icon(tag="plus", size=13),
                        rx.text("Nuevo cupón", font_size="13px", font_weight="700"),
                        spacing="1", align="center",
                    ),
                    on_click=FoodState.abrir_nuevo_cupon,
                    background="#EA580C", color="#FFFFFF", border_radius="9px",
                    padding_x="16px", padding_y="9px", cursor="pointer",
                    _hover={"background": "#C2410C"},
                ),
            ),
            width="100%", align="center",
        ),
        # ── Selector de tab ──────────────────────────────────────────────
        rx.box(
            rx.hstack(
                _promo_tab_pill("automaticas", "tag",            "Automáticas"),
                _promo_tab_pill("cupones",     "ticket_percent", "Cupones"),
                spacing="1",
                padding="4px",
            ),
            background="#1E293B",
            border="1px solid #334155",
            border_radius="10px",
            width="fit-content",
        ),
        # ── Contenido por tab ────────────────────────────────────────────
        rx.cond(
            AdminPanelState.promo_tab == "automaticas",
            rx.vstack(
                _promo_activa_banner(),
                rx.grid(
                    rx.foreach(FoodState.promociones_lista, _promo_card),
                    _promo_nueva_placeholder(),
                    columns=rx.breakpoints(initial="1", sm="2", lg="3"),
                    gap="16px", width="100%",
                ),
                spacing="4", width="100%",
            ),
            _cupones_body(),
        ),
        spacing="4", width="100%",
    )


@rx.page(
    route="/promociones",
    on_load=[AdminLocalState.on_load_dono, FoodState.on_load_promociones],
    title="TUWAYKIFOOD | Promociones",
)
def promociones_page() -> rx.Component:
    return _dono_shell(_promociones_content())
