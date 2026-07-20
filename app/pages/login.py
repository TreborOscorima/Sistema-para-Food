"""Login PIN — diseño Claude Design: pantalla única, selector de rol + teclado estilo iPhone."""

from __future__ import annotations

import reflex as rx

from app.components.shared import (
    ACCENT, ACCENT_HOVER,
    DANGER_TEXT,
    DARK_600, DARK_700, DARK_800,
    PAGE_BACKGROUND,
    TEXT_MUTED, TEXT_WHITE,
    _connection_banner_es,
)
from app.states.food_state import CompanyOptionView, FoodState, SucursalView


# ─── Tarjeta de rol ───────────────────────────────────────────────────────────
# El rol seleccionado se valida contra el rol real del usuario dueño del PIN de 4 a 6 Digitos
# (ver FoodState._authenticate_with_pin) — no es solo decorativo.

def _rol_card(emoji: str, label: str, rol_value: str) -> rx.Component:
    activo = FoodState.login_rol_seleccionado == rol_value
    return rx.box(
        rx.vstack(
            rx.text(emoji, font_size="20px", line_height="1"),
            rx.text(
                label,
                font_size="13px",
                font_weight="600",
                color=rx.cond(activo, TEXT_WHITE, TEXT_MUTED),
                line_height="1",
            ),
            spacing="1",
            align="center",
        ),
        on_click=FoodState.seleccionar_login_rol(rol_value),
        background=PAGE_BACKGROUND,
        border=rx.cond(activo, f"2px solid {ACCENT}", f"2px solid {DARK_700}"),
        border_radius="12px",
        padding="12px",
        text_align="center",
        cursor="pointer",
        transition="border-color 0.15s, transform 0.1s",
        _hover={"border_color": ACCENT, "transform": "scale(0.98)"},
        _active={"transform": "scale(0.95)"},
    )


# ─── PIN dots ─────────────────────────────────────────────────────────────────

def _pin_dot(filled: bool) -> rx.Component:
    return rx.box(
        width="14px",
        height="14px",
        border_radius="50%",
        background=rx.cond(filled, TEXT_WHITE, "transparent"),
        border=rx.cond(filled, f"2px solid {TEXT_WHITE}", f"2px solid {DARK_600}"),
        transition="all 0.12s ease",
        box_shadow=rx.cond(filled, "0 0 6px rgba(255,255,255,0.4)", "none"),
    )


def _pin_display() -> rx.Component:
    n = FoodState.login_pin_input.length()
    return rx.hstack(
        _pin_dot(n >= 1),
        _pin_dot(n >= 2),
        _pin_dot(n >= 3),
        _pin_dot(n >= 4),
        _pin_dot(n >= 5),
        _pin_dot(n >= 6),
        spacing="3",
        justify="center",
        padding_y="4px",
    )


# ─── Teclas estilo iPhone ─────────────────────────────────────────────────────

def _key_iphone(num: str, on_click) -> rx.Component:
    return rx.button(
        rx.text(num, font_size="28px", font_weight="300", color=TEXT_WHITE,
                line_height="1"),
        on_click=on_click,
        aria_label=f"Dígito {num}",
        width="64px",
        height="64px",
        border_radius="50%",
        background="rgba(255,255,255,0.13)",
        border="none",
        padding="0",
        min_width="0",
        display="flex",
        align_items="center",
        justify_content="center",
        cursor="pointer",
        transition="background 0.1s ease, transform 0.1s ease",
        _hover={"background": "rgba(255,255,255,0.22)"},
        _active={"transform": "scale(0.88)", "background": "rgba(255,255,255,0.32)"},
    )


def _key_iphone_ghost(content: rx.Component, on_click, aria_label: str) -> rx.Component:
    return rx.button(
        content,
        on_click=on_click,
        aria_label=aria_label,
        width="68px",
        height="68px",
        border_radius="50%",
        background="transparent",
        border="none",
        padding="0",
        min_width="0",
        display="flex",
        align_items="center",
        justify_content="center",
        cursor="pointer",
        transition="background 0.1s ease, transform 0.1s ease",
        _hover={"background": "rgba(255,255,255,0.1)"},
        _active={"transform": "scale(0.88)"},
    )


def _keypad() -> rx.Component:
    return rx.grid(
        _key_iphone("1", FoodState.append_login_digit("1")),
        _key_iphone("2", FoodState.append_login_digit("2")),
        _key_iphone("3", FoodState.append_login_digit("3")),
        _key_iphone("4", FoodState.append_login_digit("4")),
        _key_iphone("5", FoodState.append_login_digit("5")),
        _key_iphone("6", FoodState.append_login_digit("6")),
        _key_iphone("7", FoodState.append_login_digit("7")),
        _key_iphone("8", FoodState.append_login_digit("8")),
        _key_iphone("9", FoodState.append_login_digit("9")),
        _key_iphone_ghost(
            rx.text("C", font_size="20px", font_weight="400", color=TEXT_MUTED,
                    line_height="1"),
            FoodState.clear_login_pin,
            "Borrar PIN completo",
        ),
        _key_iphone("0", FoodState.append_login_digit("0")),
        _key_iphone_ghost(
            rx.icon(tag="delete", size=20, color=TEXT_MUTED),
            FoodState.backspace_login_pin,
            "Borrar último dígito",
        ),
        columns="3",
        gap="14px",
        width="100%",
        justify_items="center",
    )


# ─── Selector de restaurante (paso previo al PIN) ─────────────────────────────

def _restaurant_card(empresa: CompanyOptionView) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.cond(
                empresa.logo_url != "",
                rx.image(
                    src=empresa.logo_url,
                    width="56px", height="56px",
                    object_fit="cover",
                    border_radius="12px",
                ),
                rx.box(
                    rx.text(empresa.name[:1].upper(), font_size="22px",
                            font_weight="800", color=TEXT_WHITE, line_height="1"),
                    width="56px", height="56px", border_radius="12px",
                    background=DARK_700,
                    display="flex", align_items="center", justify_content="center",
                ),
            ),
            rx.text(empresa.name, font_size="13px", font_weight="600",
                    color=TEXT_WHITE, text_align="center", no_of_lines=2),
            spacing="2", align="center",
        ),
        on_click=FoodState.seleccionar_restaurante(empresa.id),
        background=PAGE_BACKGROUND,
        border=f"2px solid {DARK_700}",
        border_radius="14px",
        padding="16px 10px",
        cursor="pointer",
        transition="border-color 0.15s, transform 0.1s",
        _hover={"border_color": TEXT_MUTED, "transform": "scale(0.98)"},
        _active={"transform": "scale(0.95)"},
    )


def _restaurant_selector_card() -> rx.Component:
    return rx.box(
        rx.text(
            "ELIGE TU RESTAURANTE",
            font_size="11px",
            font_weight="700",
            color=TEXT_MUTED,
            text_transform="uppercase",
            letter_spacing="0.08em",
            margin_bottom="16px",
        ),
        rx.cond(
            FoodState.companies_activas.length() > 0,
            rx.grid(
                rx.foreach(FoodState.companies_activas, _restaurant_card),
                columns="2",
                gap="10px",
                width="100%",
            ),
            rx.text(
                "No hay restaurantes activos por ahora.",
                font_size="13px",
                color=TEXT_MUTED,
                text_align="center",
            ),
        ),
        background=DARK_800,
        border_radius="20px",
        border=f"1px solid {DARK_700}",
        padding="32px",
        width="100%",
        max_width="400px",
    )


# ─── Card principal ────────────────────────────────────────────────────────────

def _login_card() -> rx.Component:
    return rx.box(
        # Selector de rol
        rx.hstack(
            rx.text(
                "SELECCIONA TU ROL",
                font_size="11px",
                font_weight="700",
                color=TEXT_MUTED,
                text_transform="uppercase",
                letter_spacing="0.08em",
            ),
            rx.spacer(),
            rx.link(
                "← Volver",
                on_click=FoodState.volver_a_seleccion_restaurante,
                font_size="11px",
                color=TEXT_MUTED,
                cursor="pointer",
                text_decoration="none",
                _hover={"color": TEXT_MUTED},
            ),
            width="100%",
            align="center",
            margin_bottom="12px",
        ),
        rx.grid(
            _rol_card("🧑‍🍳", "Mozo", "Mozo"),
            _rol_card("🍳", "Cocina", "Cocina"),
            _rol_card("🖥️", "Caja", "Caja"),
            columns="3",
            gap="8px",
            margin_bottom="28px",
        ),
        rx.text(
            "Ingrese su PIN",
            font_size="11px",
            font_weight="700",
            color=TEXT_MUTED,
            text_transform="uppercase",
            letter_spacing="0.08em",
            margin_bottom="16px",
        ),
        _pin_display(),
        # Error (solo ocupa espacio cuando existe)
        rx.cond(
            FoodState.login_error != "",
            rx.hstack(
                rx.icon(tag="circle_x", size=13, color=DANGER_TEXT),
                rx.text(FoodState.login_error, font_size="12px",
                        color=DANGER_TEXT, font_weight="600"),
                spacing="2",
                align="center",
                background="rgba(239,68,68,0.08)",
                border="1px solid #FECACA",
                border_radius="8px",
                padding="8px 12px",
                width="100%",
                justify="center",
                margin_y="10px",
            ),
            rx.fragment(),
        ),
        # Contador de dígitos — altura fija siempre para que el teclado
        # de abajo no salte al escribir el primer dígito.
        rx.box(
            rx.cond(
                FoodState.login_pin_input.length() > 0,
                rx.text(
                    FoodState.login_pin_input.length().to_string() + " dígito(s)",
                    font_size="11px",
                    color=TEXT_MUTED,
                    text_align="center",
                ),
                rx.fragment(),
            ),
            height="22px",
            margin_y="4px",
            display="flex",
            align_items="center",
            justify_content="center",
        ),
        # Teclado iPhone
        _keypad(),
        # Botón Ingresar
        rx.button(
            rx.text("Ingresar", font_size="15px", font_weight="700",
                    color=TEXT_WHITE),
            on_click=FoodState.submit_login_pin,
            background=ACCENT,
            border_radius="12px",
            padding="16px",
            width="100%",
            cursor="pointer",
            margin_top="16px",
            _hover={"background": ACCENT_HOVER,
                    "box_shadow": "0 6px 20px rgba(234,88,12,0.45)"},
            _active={"transform": "scale(0.98)"},
            transition="all 0.15s",
        ),
        # Interior del card
        background=DARK_800,
        border_radius="20px",
        border=f"1px solid {DARK_700}",
        padding="32px",
        width="100%",
        max_width="400px",
    )


# ─── Selector de sucursal (paso posterior al PIN) ────────────────────────────

def _sucursal_card(suc: SucursalView) -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.icon(tag="map_pin", size=24, color=ACCENT),
            rx.text(suc.nombre, font_size="14px", font_weight="600",
                    color=TEXT_WHITE, text_align="center", no_of_lines=2),
            rx.cond(
                suc.direccion != "",
                rx.text(suc.direccion, font_size="11px", color=TEXT_MUTED,
                        text_align="center", no_of_lines=1),
                rx.fragment(),
            ),
            spacing="2", align="center",
        ),
        on_click=FoodState.seleccionar_sucursal_login(suc.id),
        background=PAGE_BACKGROUND,
        border=f"2px solid {DARK_700}",
        border_radius="14px",
        padding="16px 10px",
        cursor="pointer",
        transition="border-color 0.15s, transform 0.1s",
        _hover={"border_color": ACCENT, "transform": "scale(0.98)"},
        _active={"transform": "scale(0.95)"},
    )


def _sucursal_selector_card() -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.text(
                "ELIGE TU SUCURSAL",
                font_size="11px",
                font_weight="700",
                color=TEXT_MUTED,
                text_transform="uppercase",
                letter_spacing="0.08em",
            ),
            rx.spacer(),
            rx.link(
                "← Volver",
                on_click=FoodState.volver_a_pin_login,
                font_size="11px",
                color=TEXT_MUTED,
                cursor="pointer",
                text_decoration="none",
                _hover={"color": TEXT_MUTED},
            ),
            width="100%",
            align="center",
            margin_bottom="16px",
        ),
        rx.cond(
            FoodState.sucursales_empresa.length() > 0,
            rx.grid(
                rx.foreach(FoodState.sucursales_empresa, _sucursal_card),
                columns="2",
                gap="10px",
                width="100%",
            ),
            rx.text(
                "No hay sucursales configuradas.",
                font_size="13px",
                color=TEXT_MUTED,
                text_align="center",
            ),
        ),
        background=DARK_800,
        border_radius="20px",
        border=f"1px solid {DARK_700}",
        padding="32px",
        width="100%",
        max_width="400px",
    )


# ─── Logo de marca — caja apaisada (más ancha que alta), no todo el ancho ─────

def _glow() -> rx.Component:
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


def _brand_logo_box_restaurant() -> rx.Component:
    """Paso 1 (elegir empresa) — logo de marca TUWAYKIFOOD, tamaño grande."""
    return rx.box(
        _glow(),
        rx.center(
            rx.image(
                src="/TUWAYKIFOOD.png",
                height=rx.breakpoints(initial="122px", sm="150px", md="178px"),
                width="auto",
                alt="TUWAYKIFOOD",
            ),
            width="100%", height="100%",
        ),
        background=TEXT_WHITE,
        border_radius="20px",
        width=rx.breakpoints(initial="190px", sm="230px", md="270px"),
        height=rx.breakpoints(initial="130px", sm="158px", md="186px"),
        box_shadow="0 12px 40px rgba(0,0,0,0.5)",
        position="relative",
        z_index="1",
    )


def _brand_logo_box_pin() -> rx.Component:
    """Paso 2 (rol/PIN) — logo de la empresa elegida, un poco más chico."""
    return rx.box(
        _glow(),
        rx.cond(
            FoodState.login_selected_company_logo != "",
            rx.center(
                rx.image(
                    src=FoodState.login_selected_company_logo,
                    height=rx.breakpoints(initial="90px", sm="112px", md="132px"),
                    width="auto",
                    alt=FoodState.login_selected_company_name,
                ),
                width="100%", height="100%",
            ),
            rx.box(
                rx.text(
                    FoodState.login_selected_company_name[:1].upper(),
                    font_size=rx.breakpoints(initial="38px", md="52px"),
                    font_weight="800", color=TEXT_WHITE, line_height="1",
                ),
                width="100%", height="100%",
                display="flex", align_items="center", justify_content="center",
                background=DARK_700,
                border_radius="20px",
            ),
        ),
        background=TEXT_WHITE,
        border_radius="20px",
        width=rx.breakpoints(initial="155px", sm="190px", md="220px"),
        height=rx.breakpoints(initial="105px", sm="128px", md="150px"),
        box_shadow="0 12px 40px rgba(0,0,0,0.5)",
        position="relative",
        z_index="1",
    )


def _brand_logo_box() -> rx.Component:
    return rx.cond(
        FoodState.login_step == "restaurant",
        _brand_logo_box_restaurant(),
        _brand_logo_box_pin(),
    )


# ─── Página de login ──────────────────────────────────────────────────────────

@rx.page(route="/login", on_load=FoodState.on_load_login,
         title="TUWAYKIFOOD | Iniciar Sesión")
def login_page() -> rx.Component:
    return rx.box(
        _connection_banner_es(),
        rx.el.input(
            id="login-key-capture",
            value="",
            on_key_down=FoodState.login_keydown,
            auto_focus=True,
            position="fixed",
            opacity="0",
            width="1px",
            height="1px",
            overflow="hidden",
            pointer_events="none",
            z_index="-1",
        ),
        rx.script(
            "setInterval(function(){var e=document.getElementById('login-key-capture');"
            "if(e&&document.activeElement!==e)e.focus();},500);"
        ),
        rx.center(
            rx.vstack(
                _brand_logo_box(),
                # Card principal — 3 pasos: restaurant → pin → sucursal
                rx.cond(
                    FoodState.login_step == "restaurant",
                    _restaurant_selector_card(),
                    rx.cond(
                        FoodState.login_step == "sucursal",
                        _sucursal_selector_card(),
                        _login_card(),
                    ),
                ),
                # Link administrador — solo visible en paso PIN
                rx.cond(
                    FoodState.login_step == "pin",
                    rx.link(
                        "Ingresar como Administrador →",
                        href="/admin/login?empresa=" + FoodState.login_selected_company_slug,
                        font_size="13px",
                        color=TEXT_MUTED,
                        font_weight="500",
                        text_decoration="none",
                        _hover={"color": TEXT_MUTED},
                    ),
                    rx.fragment(),
                ),
                spacing="6",
                align="center",
                width="100%",
                max_width="400px",
                padding_x="20px",
            ),
            min_height="100vh",
            padding_y="40px",
        ),
        background=PAGE_BACKGROUND,
        min_height="100vh",
        class_name="dark",
    )
