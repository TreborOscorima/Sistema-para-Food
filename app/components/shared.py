"""Componentes compartidos y shell visual de TUWAYKIFOOD POS."""

from __future__ import annotations

import json
import reflex as rx

from app.states.food_state import FoodState

# ─── CSS GLOBAL ─────────────────────────────────────────────────────────────────
# Inyectado via rx.script() IIFE porque Emotion scopea el CSS y lo rompe.
# El id='twk-css' evita duplicados en navegación SPA.
_TWK_CSS = (
    # ── Design Tokens ────────────────────────────────────────────────────────
    ":root{"
    "--twk-orange:#EA580C;--twk-orange-dk:#C2410C;--twk-orange-lt:#FFF7ED;--twk-orange-muted:#FED7AA;"
    "--twk-900:#0F172A;--twk-800:#1E293B;--twk-700:#334155;--twk-600:#475569;"
    "--twk-500:#64748B;--twk-400:#94A3B8;--twk-300:#CBD5E1;--twk-200:#E2E8F0;"
    "--twk-100:#F1F5F9;--twk-50:#F8FAFC;"
    "--twk-success:#16A34A;--twk-success-lt:#DCFCE7;--twk-success-bd:#BBF7D0;"
    "--twk-error:#DC2626;--twk-error-lt:#FEF2F2;--twk-error-bd:#FECACA;"
    "--twk-warning:#D97706;--twk-warning-lt:#FFFBEB;--twk-warning-bd:#FDE68A;"
    "--twk-info:#2563EB;--twk-info-lt:#EFF6FF;--twk-info-bd:#BFDBFE;"
    "--twk-r-sm:6px;--twk-r-md:10px;--twk-r-lg:16px;--twk-r-xl:24px;--twk-r-full:9999px;"
    "--twk-sh-sm:0 1px 3px rgba(0,0,0,0.06),0 1px 2px rgba(0,0,0,0.04);"
    "--twk-sh-md:0 4px 16px rgba(0,0,0,0.08),0 2px 4px rgba(0,0,0,0.04);"
    "--twk-sh-lg:0 12px 40px rgba(0,0,0,0.12),0 4px 8px rgba(0,0,0,0.06);"
    "--twk-sh-orange:0 4px 14px rgba(234,88,12,0.35);"
    "--twk-font:'Inter',system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;"
    "--twk-sb:#0F172A;--twk-sb-bd:#1E293B;"
    "--twk-sb-tx:rgba(255,255,255,0.58);--twk-sb-tx-act:#FFFFFF;"
    "--twk-sb-hover:rgba(255,255,255,0.08);"
    "}"

    # ── Tipografía global ─────────────────────────────────────────────────────
    "html,body,*,*::before,*::after{font-family:var(--twk-font)!important}"
    "html{scroll-behavior:smooth}"
    "*{box-sizing:border-box;-webkit-tap-highlight-color:rgba(234,88,12,0.08)}"
    "input::placeholder,textarea::placeholder{color:#94A3B8!important;opacity:1!important}"

    # Evita zoom de iOS en inputs
    "@media(max-width:1023px){"
    "input[type=text],input[type=number],input[type=email],"
    "input[type=password],input[type=search],textarea,select{font-size:16px!important}}"

    # ── Scrollbar ─────────────────────────────────────────────────────────────
    "::-webkit-scrollbar{width:5px;height:5px}"
    "::-webkit-scrollbar-track{background:transparent}"
    "::-webkit-scrollbar-thumb{background:#CBD5E1;border-radius:8px}"
    "::-webkit-scrollbar-thumb:hover{background:#94A3B8}"
    "[data-radix-select-viewport]{font-size:14px!important}"

    # ── Layout utils ──────────────────────────────────────────────────────────
    ".twk-cols-lg,.twk-cols-md{display:flex!important;flex-wrap:wrap!important;gap:20px;width:100%;align-items:flex-start}"
    ".twk-panel{flex:0 0 100%!important;min-width:0!important}"
    "@media(min-width:1024px){.twk-cols-lg{flex-wrap:nowrap!important}.twk-cols-lg .twk-panel{flex:1 1 0!important}}"
    "@media(min-width:768px){.twk-cols-md{flex-wrap:nowrap!important}.twk-cols-md .twk-panel{flex:1 1 0!important}}"
    ".twk-form-row{display:flex!important;flex-direction:column!important;gap:12px;width:100%}"
    "@media(min-width:768px){.twk-form-row{flex-direction:row!important}.twk-form-row>*{flex:1!important;min-width:0!important}}"
    ".twk-field-row{display:flex!important;flex-direction:column!important;gap:6px;width:100%;align-items:flex-start}"
    "@media(min-width:640px){.twk-field-row{flex-direction:row!important;align-items:center!important}"
    ".twk-field-row>*:first-child{flex:0 0 140px!important}"
    ".twk-field-row>*:last-child{flex:1!important;min-width:0}}"

    # ── Inputs ────────────────────────────────────────────────────────────────
    ".twk-input,.twk-login-input{width:100%;padding:10px 14px;font-size:14px;"
    "border-radius:var(--twk-r-md);border:1.5px solid var(--twk-200);"
    "background:#fff;color:var(--twk-900);outline:none;"
    "transition:border .15s,box-shadow .15s}"
    ".twk-input:focus,.twk-login-input:focus{"
    "border-color:var(--twk-orange)!important;"
    "box-shadow:0 0 0 3px rgba(234,88,12,0.1)!important;outline:none!important}"
    ".twk-input:-webkit-autofill,.twk-login-input:-webkit-autofill{"
    "-webkit-box-shadow:0 0 0 1000px #fff inset!important;"
    "-webkit-text-fill-color:var(--twk-900)!important}"

    # ── Buttons ───────────────────────────────────────────────────────────────
    ".twk-btn{display:inline-flex;align-items:center;justify-content:center;gap:6px;"
    "padding:9px 18px;border-radius:var(--twk-r-md);font-size:13px;font-weight:600;"
    "border:none;cursor:pointer;transition:all .15s;white-space:nowrap;text-decoration:none;line-height:1}"
    ".twk-btn-primary{background:var(--twk-orange);color:#fff!important;box-shadow:var(--twk-sh-orange)}"
    ".twk-btn-primary:hover{background:var(--twk-orange-dk);transform:translateY(-1px);box-shadow:0 6px 18px rgba(234,88,12,0.4)}"
    ".twk-btn-primary:active{transform:translateY(0)}"
    ".twk-btn-secondary{background:#fff;color:var(--twk-orange)!important;border:1.5px solid var(--twk-orange)}"
    ".twk-btn-secondary:hover{background:var(--twk-orange-lt)}"
    ".twk-btn-ghost{background:transparent;color:var(--twk-700)!important;border:1.5px solid var(--twk-200)}"
    ".twk-btn-ghost:hover{background:var(--twk-100);border-color:var(--twk-300)}"
    ".twk-btn-danger{background:var(--twk-error-lt);color:var(--twk-error)!important;border:1.5px solid var(--twk-error-bd)}"
    ".twk-btn-danger:hover{background:#FEE2E2}"
    ".twk-btn-success{background:var(--twk-success-lt);color:var(--twk-success)!important;border:1.5px solid var(--twk-success-bd)}"
    ".twk-btn-success:hover{background:#BBFCD0}"
    ".twk-btn-sm{padding:5px 12px!important;font-size:12px!important;border-radius:var(--twk-r-sm)!important}"
    ".twk-btn-lg{padding:12px 24px!important;font-size:15px!important;border-radius:var(--twk-r-lg)!important}"
    ".twk-btn-xl{padding:15px 32px!important;font-size:16px!important;border-radius:var(--twk-r-lg)!important;font-weight:700!important}"

    # ── Badges ────────────────────────────────────────────────────────────────
    ".twk-badge{display:inline-flex;align-items:center;gap:4px;padding:3px 9px;"
    "border-radius:var(--twk-r-full);font-size:11px;font-weight:600;line-height:1.4}"
    ".twk-badge-success{background:var(--twk-success-lt);color:var(--twk-success)}"
    ".twk-badge-error{background:var(--twk-error-lt);color:var(--twk-error)}"
    ".twk-badge-warning{background:var(--twk-warning-lt);color:var(--twk-warning)}"
    ".twk-badge-info{background:var(--twk-info-lt);color:var(--twk-info)}"
    ".twk-badge-orange{background:var(--twk-orange-lt);color:var(--twk-orange)}"
    ".twk-badge-gray{background:var(--twk-100);color:var(--twk-600)}"
    ".twk-badge-dark{background:var(--twk-900);color:#fff}"

    # ── Cards ─────────────────────────────────────────────────────────────────
    ".twk-card{background:#fff;border:1px solid var(--twk-200);"
    "border-radius:var(--twk-r-lg);padding:20px;box-shadow:var(--twk-sh-sm)}"
    ".twk-card-sm{background:#fff;border:1px solid var(--twk-100);"
    "border-radius:var(--twk-r-md);padding:14px}"
    ".twk-card:hover{box-shadow:var(--twk-sh-md)}"

    # ── Mesa cards (mapa de salón) ─────────────────────────────────────────────
    ".twk-mesa{background:#fff;border:2px solid var(--twk-200);"
    "border-radius:var(--twk-r-lg);padding:14px 16px;cursor:pointer;"
    "transition:all .18s;user-select:none;position:relative}"
    ".twk-mesa:hover{transform:translateY(-2px);box-shadow:var(--twk-sh-md)}"
    ".twk-mesa:active{transform:translateY(0)}"
    ".twk-mesa-libre{border-color:#BBF7D0;background:linear-gradient(135deg,#F0FDF4 0%,#FFFFFF 100%)}"
    ".twk-mesa-ocupada{border-color:var(--twk-orange-muted);background:linear-gradient(135deg,#FFF7ED 0%,#FFFFFF 100%)}"
    ".twk-mesa-cuenta{border-color:#FECACA;background:linear-gradient(135deg,#FEF2F2 0%,#FFFFFF 100%)}"
    ".twk-mesa-selected{border-color:var(--twk-orange)!important;"
    "box-shadow:0 0 0 3px rgba(234,88,12,0.18)!important;transform:translateY(-2px)!important}"

    # ── KDS Cocina cards ──────────────────────────────────────────────────────
    ".twk-kds-card{background:#fff;border-left:4px solid var(--twk-300);"
    "border-radius:0 var(--twk-r-md) var(--twk-r-md) 0;"
    "box-shadow:var(--twk-sh-sm);overflow:hidden}"
    ".twk-kds-pendiente{border-left-color:var(--twk-warning)}"
    ".twk-kds-preparando{border-left-color:var(--twk-orange)}"
    ".twk-kds-listo{border-left-color:var(--twk-success)}"

    # ── Tables ────────────────────────────────────────────────────────────────
    ".twk-table{width:100%;border-collapse:collapse}"
    ".twk-table th{padding:10px 14px;text-align:left;font-size:11px;"
    "font-weight:700;color:var(--twk-500);text-transform:uppercase;"
    "letter-spacing:0.06em;border-bottom:2px solid var(--twk-100)}"
    ".twk-table td{padding:10px 14px;font-size:13px;color:var(--twk-700);"
    "border-bottom:1px solid var(--twk-100)}"
    ".twk-table tr:last-child td{border-bottom:none}"
    ".twk-table tr:hover td{background:var(--twk-50)}"

    # ── Status dots ───────────────────────────────────────────────────────────
    ".twk-dot{width:8px;height:8px;border-radius:50%;display:inline-block;flex-shrink:0}"
    ".twk-dot-green{background:var(--twk-success)}"
    ".twk-dot-red{background:var(--twk-error)}"
    ".twk-dot-yellow{background:var(--twk-warning)}"
    ".twk-dot-gray{background:var(--twk-400)}"
    ".twk-dot-orange{background:var(--twk-orange)}"
    ".twk-dot-pulse{animation:twk-pulse 2s infinite}"
    "@keyframes twk-pulse{0%,100%{opacity:1}50%{opacity:0.4}}"

    # ── Section title con barra naranja ───────────────────────────────────────
    ".twk-section-title{display:flex;align-items:center;gap:8px;"
    "font-size:13px;font-weight:700;color:var(--twk-900)}"
    ".twk-section-title::before{content:'';display:block;width:3px;height:16px;"
    "background:var(--twk-orange);border-radius:2px;flex-shrink:0}"

    # ── Sidebar dark nav ──────────────────────────────────────────────────────
    ".twk-nav-item{display:flex;align-items:center;gap:10px;"
    "padding:8px 10px;border-radius:var(--twk-r-md);cursor:pointer;"
    "transition:all .15s;text-decoration:none;width:100%;"
    "color:var(--twk-sb-tx)}"
    ".twk-nav-item:hover{background:var(--twk-sb-hover);color:#fff}"
    ".twk-nav-item-active{background:var(--twk-orange)!important;"
    "color:#fff!important;box-shadow:var(--twk-sh-orange)}"
    ".twk-nav-icon-box{width:32px;height:32px;border-radius:8px;"
    "display:flex;align-items:center;justify-content:center;flex-shrink:0;"
    "background:rgba(255,255,255,0.06);transition:all .15s}"
    ".twk-nav-item-active .twk-nav-icon-box{background:rgba(255,255,255,0.22)}"
    ".twk-nav-item:hover .twk-nav-icon-box{background:rgba(255,255,255,0.12)}"

    # ── Login dark card ────────────────────────────────────────────────────────
    ".twk-login-card{background:#1E293B;border:1px solid #334155;"
    "border-radius:20px;padding:32px;box-shadow:0 20px 60px rgba(0,0,0,0.4)}"
    ".twk-login-input{border:2px solid #334155!important;"
    "background:#0F172A!important;color:#FFFFFF!important;"
    "border-radius:10px!important;padding:12px 14px!important;"
    "height:auto!important;min-height:44px!important}"
    ".twk-login-input:focus{border-color:#EA580C!important;"
    "box-shadow:0 0 0 3px rgba(234,88,12,0.15)!important}"
    ".twk-login-input::placeholder{color:#475569!important}"
)

_FONT_JS = (
    "if(!document.getElementById('twk-inter')){"
    "var p1=document.createElement('link');p1.rel='preconnect';"
    "p1.href='https://fonts.googleapis.com';document.head.appendChild(p1);"
    "var p2=document.createElement('link');p2.rel='preconnect';"
    "p2.href='https://fonts.gstatic.com';p2.crossOrigin='anonymous';document.head.appendChild(p2);"
    "var fl=document.createElement('link');fl.id='twk-inter';fl.rel='stylesheet';"
    "fl.href='https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,400;0,14..32,500;0,14..32,600;0,14..32,700;0,14..32,800&display=swap';"
    "document.head.appendChild(fl);}"
)
_CSS_SCRIPT = f"(function(){{{_FONT_JS}if(!document.getElementById('twk-css')){{var s=document.createElement('style');s.id='twk-css';s.textContent={json.dumps(_TWK_CSS)};document.head.appendChild(s);}}}})();"


# ─── PALETA (usada por todas las páginas) ────────────────────────────────────────
PAGE_BACKGROUND  = "#F8FAFC"
SURFACE_BASE     = "#FFFFFF"
SURFACE_ELEVATED = "#FFFFFF"
SURFACE_SOFT     = "#F8FAFC"
SURFACE_MUTED    = "#F1F5F9"
SURFACE_GHOST    = "#F8FAFC"
SURFACE_HOVER    = "#F1F5F9"
SURFACE_INTERACTIVE = "#FFF7ED"
BORDER_COLOR     = "#E2E8F0"
BORDER_STRONG    = "#CBD5E1"
BORDER_ACCENT    = "#FED7AA"
TEXT_PRIMARY     = "#0F172A"
TEXT_SECONDARY   = "#334155"
TEXT_MUTED       = "#64748B"
ACCENT           = "#EA580C"
ACCENT_HOVER     = "#C2410C"
ACCENT_BG        = "#FFF7ED"
ACCENT_TEXT      = "#9A3412"
ACCENT_SOFT      = "#FFF7ED"
SUCCESS_BG       = "#F0FDF4"
SUCCESS_TEXT     = "#15803D"
SUCCESS_BORDER   = "#BBF7D0"
DANGER_BG        = "#FEF2F2"
DANGER_TEXT      = "#B91C1C"
DANGER_BORDER    = "#FECACA"
WARNING_BG       = "#FFFBEB"
WARNING_TEXT     = "#B45309"
WARNING_BORDER   = "#FDE68A"
INFO_BG          = "#EFF6FF"
INFO_TEXT        = "#1D4ED8"
INFO_BORDER      = "#BFDBFE"
GLOW             = "0 1px 3px rgba(0,0,0,0.07),0 1px 2px rgba(0,0,0,0.04)"
SOFT_GLOW        = "0 1px 2px rgba(0,0,0,0.05)"
ACCENT_GLOW      = "0 2px 8px rgba(234,88,12,0.18)"


# ─── UTILIDADES PÚBLICAS ──────────────────────────────────────────────────────────

def surface_card(*children, **props) -> rx.Component:
    bg           = props.pop("background", SURFACE_BASE)
    border       = props.pop("border", f"1px solid {BORDER_COLOR}")
    border_radius = props.pop("border_radius", "14px")
    box_shadow   = props.pop("box_shadow", GLOW)
    width        = props.pop("width", "100%")
    incoming     = props.pop("style", {})
    return rx.box(
        *children,
        style={"background": bg, "border": border, "border_radius": border_radius,
               "box_shadow": box_shadow, **incoming},
        width=width,
        **props,
    )


def section_card(*children, **props) -> rx.Component:
    bg           = props.pop("background", SURFACE_SOFT)
    border       = props.pop("border", f"1px solid {BORDER_COLOR}")
    border_radius = props.pop("border_radius", "10px")
    box_shadow   = props.pop("box_shadow", SOFT_GLOW)
    width        = props.pop("width", "100%")
    incoming     = props.pop("style", {})
    return rx.box(
        *children,
        style={"background": bg, "border": border, "border_radius": border_radius,
               "box_shadow": box_shadow, **incoming},
        width=width,
        **props,
    )


def action_button(label: str, on_click, icon_tag: str = "arrow_right") -> rx.Component:
    return rx.button(
        rx.hstack(
            rx.icon(tag=icon_tag, size=16),
            rx.text(label, font_weight="700"),
            spacing="2",
            align="center",
        ),
        on_click=on_click,
        background=ACCENT,
        color="#FFFFFF",
        border_radius="9px",
        height="40px",
        padding_x="1rem",
        _hover={"background": ACCENT_HOVER},
    )


def status_banner(message) -> rx.Component:
    return section_card(
        rx.hstack(
            rx.box(width="8px", height="8px", border_radius="999px",
                   style={"background": ACCENT}),
            rx.text(message, color=TEXT_SECONDARY, font_weight="600", font_size="0.9rem"),
            spacing="3",
            align="center",
        ),
        padding="0.75rem 1rem",
    )


def kpi_card(title: str, value, description: str = "",
             accent_color: str = ACCENT) -> rx.Component:
    return surface_card(
        rx.vstack(
            rx.text(title, color=TEXT_MUTED, font_size="0.72rem", font_weight="700",
                    letter_spacing="0.08em", text_transform="uppercase"),
            rx.text(value, color=TEXT_PRIMARY, font_weight="800", font_size="1.75rem",
                    line_height="1.1"),
            rx.cond(
                description != "",
                rx.text(description, color=TEXT_MUTED, font_size="0.85rem"),
                rx.fragment(),
            ),
            align="start",
            spacing="2",
            width="100%",
        ),
        padding="1.1rem 1.2rem",
        border=f"1px solid {accent_color}",
    )


# ─── BRAND COMPONENT ──────────────────────────────────────────────────────────────

def _brand(compact: bool = False, dark: bool = False) -> rx.Component:
    title_color = "rgba(255,255,255,0.95)" if dark else TEXT_PRIMARY
    sub_color   = "rgba(255,255,255,0.42)" if dark else TEXT_MUTED
    return rx.hstack(
        rx.image(
            src="/TUWAYKIFOODFAVICON.png",
            width="34px",
            height="34px",
            border_radius="9px",
            flex_shrink="0",
            alt="TUWAYKIFOOD",
        ),
        rx.cond(
            compact,
            rx.fragment(),
            rx.vstack(
                rx.text(
                    "TUWAYKIFOOD",
                    color=title_color,
                    font_weight="800",
                    letter_spacing="0.07em",
                    font_size="12px",
                    text_transform="uppercase",
                    line_height="1",
                ),
                rx.text(
                    "Sistema para restaurantes",
                    color=sub_color,
                    font_size="11px",
                    line_height="1",
                ),
                align="start",
                spacing="1",
            ),
        ),
        spacing="3",
        align="center",
    )


# ─── USER SUMMARY (header claro) ─────────────────────────────────────────────────

def _user_summary() -> rx.Component:
    return rx.hstack(
        rx.box(
            rx.icon(tag="user_round", size=15, color="#FFFFFF"),
            width="34px",
            height="34px",
            border_radius="full",
            style={"background": "linear-gradient(135deg,#EA580C 0%,#C2410C 100%)"},
            display="flex",
            align_items="center",
            justify_content="center",
            flex_shrink="0",
        ),
        rx.vstack(
            rx.text(FoodState.usuario_nombre, color=TEXT_PRIMARY, font_weight="700",
                    font_size="13px", max_width="160px",
                    text_overflow="ellipsis", overflow="hidden", white_space="nowrap"),
            rx.text(FoodState.usuario_rol, color=ACCENT, font_weight="600", font_size="11px",
                    background=ACCENT_BG, padding_x="0.4rem", padding_y="1px",
                    border_radius="full", display="inline-block"),
            align="start",
            spacing="0",
        ),
        spacing="2",
        align="center",
    )


def user_session_badge() -> rx.Component:
    return rx.hstack(
        _user_summary(),
        rx.button(
            rx.hstack(
                rx.icon(tag="log_out", size=14),
                rx.text("Salir", font_weight="600", font_size="12px"),
                spacing="1",
                align="center",
            ),
            on_click=FoodState.logout,
            background=DANGER_BG,
            color=DANGER_TEXT,
            border=f"1px solid {DANGER_BORDER}",
            border_radius="8px",
            height="34px",
            padding_x="10px",
            _hover={"background": "#FEE2E2"},
        ),
        spacing="3",
        align="center",
    )


# ─── USER BADGE OSCURO (sidebar) ─────────────────────────────────────────────────

def _sidebar_user_badge() -> rx.Component:
    return rx.hstack(
        rx.box(
            rx.icon(tag="user_round", size=14, color="#FFFFFF"),
            width="32px",
            height="32px",
            border_radius="full",
            background="rgba(234,88,12,0.85)",
            display="flex",
            align_items="center",
            justify_content="center",
            flex_shrink="0",
        ),
        rx.cond(
            FoodState.sidebar_collapsed,
            rx.fragment(),
            rx.vstack(
                rx.text(FoodState.usuario_nombre, color="rgba(255,255,255,0.88)",
                        font_weight="600", font_size="12px",
                        max_width="110px", overflow="hidden",
                        text_overflow="ellipsis", white_space="nowrap"),
                rx.text(FoodState.usuario_rol, color="rgba(255,255,255,0.42)",
                        font_size="11px"),
                align="start",
                spacing="0",
            ),
        ),
        rx.cond(
            FoodState.sidebar_collapsed,
            rx.fragment(),
            rx.spacer(),
        ),
        rx.cond(
            FoodState.sidebar_collapsed,
            rx.fragment(),
            rx.icon_button(
                rx.icon(tag="log_out", size=13),
                on_click=FoodState.logout,
                background="rgba(220,38,38,0.15)",
                color="#FCA5A5",
                border="1px solid rgba(220,38,38,0.2)",
                border_radius="7px",
                width="30px",
                height="30px",
                _hover={"background": "rgba(220,38,38,0.28)", "color": "#FCA5A5"},
            ),
        ),
        spacing="2",
        align="center",
        width="100%",
    )


# ─── NAV ITEMS ────────────────────────────────────────────────────────────────────

_NAV_DESCRIPTIONS = {
    "Mozos":        "Mesas y comanda",
    "Caja":         "Cobro y tickets",
    "Mostrador":    "Takeaway rapido",
    "Cocina":       "KDS / Produccion",
    "Carta":        "Carta y precios",
    "Reportes":     "Ventas del dia",
    "Usuarios":     "Personal y PINs",
    "Configuracion": "Impresoras y local",
}


def _desktop_nav_item(label: str, href: str, icon_tag: str,
                      active: bool) -> rx.Component:
    desc = _NAV_DESCRIPTIONS.get(label, "Modulo operativo")
    return rx.link(
        rx.box(
            rx.hstack(
                # Icon box
                rx.box(
                    rx.icon(
                        tag=icon_tag,
                        size=15,
                        color=rx.cond(active, "#FFFFFF", "rgba(255,255,255,0.65)"),
                    ),
                    class_name="twk-nav-icon-box",
                ),
                # Label + description
                rx.cond(
                    FoodState.sidebar_collapsed,
                    rx.fragment(),
                    rx.vstack(
                        rx.text(
                            label,
                            color=rx.cond(active, "#FFFFFF", "rgba(255,255,255,0.82)"),
                            font_weight=rx.cond(active, "700", "500"),
                            font_size="13px",
                            line_height="1",
                        ),
                        rx.text(
                            desc,
                            color=rx.cond(active, "rgba(255,255,255,0.65)",
                                          "rgba(255,255,255,0.32)"),
                            font_size="10.5px",
                            line_height="1",
                        ),
                        align="start",
                        spacing="1",
                    ),
                ),
                align="center",
                spacing="3",
                width="100%",
            ),
            width="100%",
            padding=rx.cond(FoodState.sidebar_collapsed, "8px", "8px 10px"),
            border_radius="10px",
            background=rx.cond(active, "#EA580C", "transparent"),
            box_shadow=rx.cond(active, "0 2px 10px rgba(234,88,12,0.35)", "none"),
            class_name=rx.cond(active, "twk-nav-item twk-nav-item-active", "twk-nav-item"),
        ),
        href=href,
        width="100%",
        text_decoration="none",
    )


def _mobile_nav_item(label: str, href: str, icon_tag: str,
                     active: bool) -> rx.Component:
    return rx.link(
        rx.box(
            rx.hstack(
                rx.icon(tag=icon_tag, size=17,
                        color=rx.cond(active, "#FFFFFF", TEXT_SECONDARY)),
                rx.text(label, color=rx.cond(active, "#FFFFFF", TEXT_SECONDARY),
                        font_weight="600", font_size="0.9rem"),
                width="100%",
                spacing="3",
                align="center",
            ),
            width="100%",
            padding="0.75rem 0.9rem",
            min_height="46px",
            border_radius="10px",
            style={"background": rx.cond(active, ACCENT, SURFACE_MUTED)},
        ),
        href=href,
        width="100%",
        text_decoration="none",
    )


def _nav_stack(active: str, mobile: bool = False) -> rx.Component:
    nav_item = _mobile_nav_item if mobile else _desktop_nav_item
    return rx.vstack(
        rx.cond(FoodState.puede_ver_mozos,
                nav_item("Mozos", "/mozos", "layout_grid", active == "mozos"),
                rx.fragment()),
        rx.cond(FoodState.puede_ver_caja,
                nav_item("Caja", "/caja", "wallet", active == "caja"),
                rx.fragment()),
        rx.cond(FoodState.puede_ver_mostrador,
                nav_item("Mostrador", "/mostrador", "shopping_bag", active == "mostrador"),
                rx.fragment()),
        rx.cond(FoodState.puede_ver_cocina,
                nav_item("Cocina", "/cocina", "chef_hat", active == "cocina"),
                rx.fragment()),
        rx.cond(FoodState.puede_ver_carta,
                nav_item("Carta", "/carta", "book_open", active == "carta"),
                rx.fragment()),
        rx.cond(FoodState.puede_ver_reportes,
                nav_item("Reportes", "/reportes", "receipt_text", active == "reportes"),
                rx.fragment()),
        rx.cond(FoodState.puede_ver_usuarios,
                nav_item("Usuarios", "/usuarios", "users", active == "usuarios"),
                rx.fragment()),
        rx.cond(FoodState.puede_ver_configuracion,
                nav_item("Configuracion", "/configuracion", "settings",
                         active == "configuracion"),
                rx.fragment()),
        width="100%",
        spacing="1",
        align="stretch",
    )


# ─── SIDEBAR DESKTOP (dark navy) ──────────────────────────────────────────────────

def _desktop_sidebar(active: str) -> rx.Component:
    return rx.box(
        rx.vstack(
            # ── Brand ─────────────────────────────────────────────────────────
            rx.hstack(
                rx.cond(
                    FoodState.sidebar_collapsed,
                    rx.image(src="/TUWAYKIFOODFAVICON.png", width="34px", height="34px",
                             border_radius="9px", alt="TUWAYKIFOOD"),
                    _brand(compact=False, dark=True),
                ),
                rx.cond(
                    FoodState.sidebar_collapsed,
                    rx.fragment(),
                    rx.icon_button(
                        rx.icon(tag="panel_left_close", size=14),
                        on_click=FoodState.toggle_sidebar,
                        background="rgba(255,255,255,0.07)",
                        color="rgba(255,255,255,0.45)",
                        border="none",
                        border_radius="7px",
                        width="28px",
                        height="28px",
                        _hover={"background": "rgba(255,255,255,0.12)",
                                "color": "#fff"},
                    ),
                ),
                width="100%",
                justify="between",
                align="center",
            ),
            # ── Separador ─────────────────────────────────────────────────────
            rx.box(height="1px", width="100%",
                   background="rgba(255,255,255,0.07)"),
            # ── Navegacion ────────────────────────────────────────────────────
            rx.box(
                _nav_stack(active, mobile=False),
                width="100%",
                flex="1",
                overflow_y="auto",
            ),
            # ── Info LAN ──────────────────────────────────────────────────────
            rx.cond(
                FoodState.sidebar_collapsed,
                rx.fragment(),
                rx.box(
                    rx.vstack(
                        rx.text("Operacion en LAN", color="rgba(255,255,255,0.45)",
                                font_size="10.5px", font_weight="700",
                                letter_spacing="0.04em", text_transform="uppercase"),
                        rx.text("Optimizado para tablets, caja y cocina.",
                                color="rgba(255,255,255,0.28)", font_size="10px"),
                        align="start",
                        spacing="1",
                    ),
                    width="100%",
                    padding="8px 10px",
                    border_radius="8px",
                    background="rgba(255,255,255,0.04)",
                    border="1px solid rgba(255,255,255,0.06)",
                ),
            ),
            # ── Separador ─────────────────────────────────────────────────────
            rx.box(height="1px", width="100%",
                   background="rgba(255,255,255,0.07)"),
            # ── Usuario ───────────────────────────────────────────────────────
            _sidebar_user_badge(),
            spacing="0",
            gap="8px",
            height="100%",
            width="100%",
            align="start",
        ),
        width=rx.cond(FoodState.sidebar_collapsed, "64px", "236px"),
        min_width=rx.cond(FoodState.sidebar_collapsed, "64px", "236px"),
        height="100vh",
        position="sticky",
        top="0",
        padding="14px 10px",
        background="#0F172A",
        border_right="1px solid #1E293B",
        display=rx.breakpoints(initial="none", lg="flex"),
        flex_direction="column",
        flex_shrink="0",
        overflow_y="auto",
        overflow_x="hidden",
    )


# ─── DRAWER MÓVIL ─────────────────────────────────────────────────────────────────

def _mobile_nav_drawer(active: str) -> rx.Component:
    return rx.box(
        rx.drawer.root(
            rx.drawer.trigger(
                rx.icon_button(
                    rx.icon(tag="menu", size=18),
                    background=SURFACE_MUTED,
                    color=TEXT_SECONDARY,
                    border=f"1px solid {BORDER_COLOR}",
                    border_radius="9px",
                    width="38px",
                    height="38px",
                    _hover={"background": SURFACE_HOVER},
                )
            ),
            rx.drawer.portal(
                rx.drawer.overlay(background="rgba(15,23,42,0.5)"),
                rx.drawer.content(
                    rx.box(
                        rx.vstack(
                            rx.hstack(
                                _brand(compact=False, dark=False),
                                rx.drawer.close(
                                    rx.icon_button(
                                        rx.icon(tag="x", size=16),
                                        background=SURFACE_MUTED,
                                        color=TEXT_SECONDARY,
                                        border=f"1px solid {BORDER_COLOR}",
                                        border_radius="8px",
                                    )
                                ),
                                width="100%",
                                justify="between",
                                align="center",
                            ),
                            rx.box(height="1px", width="100%",
                                   background=BORDER_COLOR),
                            _nav_stack(active, mobile=True),
                            rx.box(height="1px", width="100%",
                                   background=BORDER_COLOR),
                            user_session_badge(),
                            width="100%",
                            align="start",
                            spacing="4",
                        ),
                        width="290px",
                        max_width="88vw",
                        height="100%",
                        padding="1rem",
                        background=SURFACE_ELEVATED,
                    ),
                    justify_content="flex-start",
                ),
            ),
            direction="left",
        ),
        display=rx.breakpoints(initial="block", lg="none"),
    )


# ─── PAGE HEADER ──────────────────────────────────────────────────────────────────

def _page_header(active: str, title: str, subtitle: str,
                 action=None) -> rx.Component:
    return rx.box(
        rx.hstack(
            rx.hstack(
                _mobile_nav_drawer(active),
                rx.vstack(
                    rx.text("TUWAYKIFOOD", color=ACCENT, font_size="10px",
                            font_weight="800", letter_spacing="0.14em",
                            text_transform="uppercase"),
                    rx.heading(title, size=rx.breakpoints(initial="5", md="6"),
                               color=TEXT_PRIMARY, line_height="1.1"),
                    align="start",
                    spacing="0",
                ),
                spacing="3",
                align="center",
                flex="1",
                min_width="0",
            ),
            rx.hstack(
                action if action is not None else rx.fragment(),
                rx.cond(
                    FoodState.autenticado,
                    rx.box(user_session_badge(),
                           display=rx.breakpoints(initial="none", lg="block")),
                    rx.fragment(),
                ),
                spacing="3",
                align="center",
                flex_shrink="0",
            ),
            width="100%",
            justify="between",
            align="center",
            gap="12px",
        ),
        rx.cond(
            subtitle != "",
            rx.text(subtitle, color=TEXT_MUTED, font_size="13px",
                    display=rx.breakpoints(initial="none", md="block"),
                    margin_top="4px"),
            rx.fragment(),
        ),
        padding=rx.breakpoints(initial="12px 16px", md="16px 20px"),
        background=SURFACE_ELEVATED,
        border_bottom=f"1px solid {BORDER_COLOR}",
        width="100%",
        position="sticky",
        top="0",
        z_index="50",
        box_shadow="0 1px 3px rgba(0,0,0,0.04)",
    )


# ─── TOPBAR MÓVIL ─────────────────────────────────────────────────────────────────

def _mobile_topbar(active: str) -> rx.Component:
    return rx.box(
        rx.hstack(
            _mobile_nav_drawer(active),
            _brand(compact=False, dark=False),
            rx.spacer(),
            spacing="3",
            align="center",
            width="100%",
        ),
        display=rx.breakpoints(initial="flex", lg="none"),
        padding="10px 14px",
        border_bottom=f"1px solid {BORDER_COLOR}",
        background=SURFACE_ELEVATED,
        width="100%",
        position="sticky",
        top="0",
        z_index="200",
        box_shadow="0 1px 4px rgba(0,0,0,0.05)",
        align_items="center",
    )


# ─── APP SHELL ────────────────────────────────────────────────────────────────────

def app_shell(
    content: rx.Component,
    *,
    page_key: str = "",
    active: str = "",
    dark: bool = False,
) -> rx.Component:
    _active = page_key or active
    _bg = "#0F172A" if dark else PAGE_BACKGROUND
    _text = "#FFFFFF" if dark else TEXT_PRIMARY
    return rx.box(
        rx.script(_CSS_SCRIPT),
        rx.hstack(
            _desktop_sidebar(_active),
            rx.box(
                _mobile_topbar(_active),
                rx.box(
                    rx.vstack(
                        content,
                        width="100%",
                        align="start",
                        spacing="5",
                    ),
                    padding=rx.breakpoints(initial="16px", md="20px 24px", xl="24px 32px"),
                    width="100%",
                ),
                width="100%",
                min_height="100vh",
                overflow_x="hidden",
            ),
            width="100%",
            align="start",
            gap="0",
        ),
        min_height="100vh",
        width="100%",
        background=_bg,
        color=_text,
    )
