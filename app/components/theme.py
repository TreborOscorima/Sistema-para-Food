"""Fuente única de verdad para la paleta de colores de TUWAYKIFOOD.

Todas las páginas importan de acá. shared.py re-exporta para compatibilidad.

Convención: los nombres siguen la función semántica (ACCENT, TEXT_PRIMARY,
SUCCESS_BG) en vez del nombre de color (ORANGE, SLATE) — así un rebrand
es un solo archivo.

Z-Index scale documentada: evita conflictos entre sticky headers, drawers y modals.

TEMA: claro/oscuro conmutable. Los tokens de superficie/texto/borde ya NO son un
hex fijo: apuntan a variables CSS (``var(--twk-…)``) cuyos valores viven en
``assets/twk.css`` en dos paletas — oscura (``:root``, el default) y clara
(``html.light``). El interruptor lo maneja el color-mode de Reflex, que agrega la
clase ``light`` / ``dark`` al ``<html>`` y persiste la elección en el navegador.
Cada ``var(--x, fallback)`` lleva como fallback su valor oscuro histórico, así si
por lo que sea la hoja no cargó, la app se sigue viendo (nunca invisible).
"""

from __future__ import annotations


def _v(name: str, fallback: str) -> str:
    """Azúcar para emitir ``var(--twk-name, fallback)``."""
    return f"var(--twk-{name}, {fallback})"


# ─── Accent ──────────────────────────────────────────────────────────────────
# El naranja de marca funciona igual sobre claro y oscuro → se deja fijo.
ACCENT           = "#EA580C"
ACCENT_HOVER     = "#C2410C"
ACCENT_BG        = "rgba(234,88,12,0.12)"
ACCENT_TEXT      = _v("accent-text", "#FB923C")   # texto naranja: se oscurece en claro
ACCENT_SOFT      = "rgba(234,88,12,0.08)"
ACCENT_MUTED     = _v("accent-text", "#FB923C")
ACCENT_GLOW      = "0 2px 8px rgba(234,88,12,0.25)"
ACCENT_SHADOW    = "0 4px 14px rgba(234,88,12,0.35)"

# ─── Surfaces (conmutables) ─────────────────────────────────────────────────
PAGE_BACKGROUND      = _v("page-bg", "#0F172A")
SURFACE_BASE         = _v("surface-base", "#1E293B")
SURFACE_ELEVATED     = _v("surface-elevated", "#1E293B")
SURFACE_SOFT         = _v("surface-soft", "#0F172A")
SURFACE_MUTED        = _v("surface-muted", "#1E293B")
SURFACE_GHOST        = _v("surface-ghost", "#0F172A")
SURFACE_HOVER        = _v("surface-hover", "#334155")
SURFACE_INTERACTIVE  = "rgba(234,88,12,0.08)"

# ─── Escala de superficies "dark" (se INVIERTE en modo claro) ───────────────
# Antes eran grises oscuros fijos. Se usan como fondo/borde (nunca como texto),
# por eso invertirlas a grises claros en modo claro es seguro y no genera nada
# invisible. DARK_700 (385 usos) y DARK_800 (307) son los caballos de batalla.
DARK_900 = _v("d900", "#0F172A")
DARK_800 = _v("d800", "#1E293B")
DARK_700 = _v("d700", "#334155")
DARK_600 = _v("d600", "#475569")

# ─── Neutral / slate (se INVIERTE en modo claro) ────────────────────────────
SLATE_500 = _v("slate-500", "#94A3B8")
SLATE_400 = _v("slate-400", "#94A3B8")
SLATE_300 = _v("slate-300", "#CBD5E1")
SLATE_200 = _v("slate-200", "#E2E8F0")
SLATE_100 = _v("slate-100", "#F1F5F9")
SLATE_50  = _v("slate-50", "#F8FAFC")

# ─── Borders (conmutables) ──────────────────────────────────────────────────
BORDER_COLOR     = _v("border", "#334155")
BORDER_STRONG    = _v("border-strong", "#475569")
BORDER_ACCENT    = "#EA580C"

# ─── Text (conmutable) ──────────────────────────────────────────────────────
TEXT_PRIMARY      = _v("text-primary", "#F1F5F9")
TEXT_SECONDARY    = _v("text-secondary", "#CBD5E1")
TEXT_MUTED        = _v("text-muted", "#94A3B8")
TEXT_WHITE        = "#FFFFFF"   # texto sobre acento/sólidos → siempre blanco

# ─── Semantic: success ──────────────────────────────────────────────────────
# Los fondos con alfa (0.10) leen bien sobre claro y oscuro → fijos. El TEXTO
# sí se ajusta por contraste (claro más oscuro, oscuro más luminoso).
SUCCESS_BG       = "rgba(34,197,94,0.10)"
SUCCESS_TEXT     = _v("success-text", "#4ADE80")
SUCCESS_SOLID    = _v("success-solid", "#22C55E")   # en claro se oscurece (texto/botón legible)
SUCCESS_DARK     = "#16A34A"
SUCCESS_BORDER   = "rgba(34,197,94,0.25)"

# ─── Semantic: danger ───────────────────────────────────────────────────────
DANGER_BG        = "rgba(239,68,68,0.10)"
DANGER_TEXT      = _v("danger-text", "#F87171")
DANGER_SOLID     = "#DC2626"
DANGER_ICON      = "#EF4444"
DANGER_BORDER    = "rgba(239,68,68,0.25)"

# ─── Semantic: warning ──────────────────────────────────────────────────────
WARNING_BG       = "rgba(245,158,11,0.10)"
WARNING_TEXT     = _v("warning-text", "#FBBF24")
WARNING_SOLID    = _v("warning-solid", "#F59E0B")   # en claro se oscurece (texto/botón legible)
WARNING_BORDER   = "rgba(245,158,11,0.25)"

# ─── Semantic: info ─────────────────────────────────────────────────────────
INFO_BG          = "rgba(59,130,246,0.10)"
INFO_TEXT         = _v("info-text", "#60A5FA")
INFO_SOLID       = _v("info-solid", "#3B82F6")   # en claro se oscurece (texto/botón legible)
INFO_BORDER      = "rgba(59,130,246,0.25)"

# ─── Semantic: purple (roles, features) ────────────────────────────────────
PURPLE           = "#7C3AED"
PURPLE_LIGHT     = _v("purple-text", "#A78BFA")

# ─── Shadows (conmutables: más suaves en claro) ─────────────────────────────
GLOW             = _v("glow", "0 1px 3px rgba(0,0,0,0.3),0 1px 2px rgba(0,0,0,0.2)")
SOFT_GLOW        = _v("soft-glow", "0 1px 2px rgba(0,0,0,0.2)")

# ─── Z-Index scale ──────────────────────────────────────────────────────────
Z_MENU_PUBLIC    = 10
Z_ADMIN_BACKDROP = 29
Z_ADMIN_SIDEBAR  = 30
Z_STICKY_HEADER  = 50
Z_DRAWER         = 200
Z_MODAL          = 300
Z_TOAST          = 400

# ─── Modal props (conmutables) ──────────────────────────────────────────────
# El nombre DARK_* se conserva por compatibilidad (28 usos), pero ahora los
# modales siguen el modo activo.
DARK_MODAL_PROPS: dict = {
    "background": _v("modal-bg", "#0F172A"),
    "border": f"1px solid {_v('modal-border', '#1E293B')}",
}
DARK_MODAL_TEXT      = _v("text-primary", "#F1F5F9")
DARK_MODAL_MUTED     = _v("text-muted", "#94A3B8")
DARK_MODAL_BORDER    = _v("modal-border", "#1E293B")
DARK_MODAL_INPUT_BG  = _v("modal-input-bg", "#1E293B")
DARK_MODAL_INPUT_BORDER = _v("modal-input-bd", "#334155")
DARK_MODAL_BTN_BG    = _v("modal-btn-bg", "#1E293B")
DARK_MODAL_BTN_BORDER = _v("modal-btn-bd", "#334155")

# ─── Sidebar (conmutable) ───────────────────────────────────────────────────
SIDEBAR_BG           = _v("sb", "#0F172A")
SIDEBAR_BORDER       = _v("sb-bd", "#1E293B")
SIDEBAR_TEXT         = _v("sb-tx", "rgba(255,255,255,0.78)")
SIDEBAR_TEXT_ACTIVE  = "#FFFFFF"
SIDEBAR_HOVER_BG    = _v("sb-hover", "rgba(255,255,255,0.10)")
