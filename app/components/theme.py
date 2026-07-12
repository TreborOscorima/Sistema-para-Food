"""Fuente única de verdad para la paleta de colores de TUWAYKIFOOD.

Todas las páginas importan de acá. shared.py re-exporta para compatibilidad.

Convención: los nombres siguen la función semántica (ACCENT, TEXT_PRIMARY,
SUCCESS_BG) en vez del nombre de color (ORANGE, SLATE) — así un rebrand
es un solo archivo.

Z-Index scale documentada: evita conflictos entre sticky headers, drawers y modals.

TEMA: Dark unificado — toda la app usa fondo oscuro.
"""

from __future__ import annotations

# ─── Accent ──────────────────────────────────────────────────────────────────
ACCENT           = "#EA580C"
ACCENT_HOVER     = "#C2410C"
ACCENT_BG        = "rgba(234,88,12,0.12)"
ACCENT_TEXT      = "#FB923C"
ACCENT_SOFT      = "rgba(234,88,12,0.08)"
ACCENT_MUTED     = "#FB923C"
ACCENT_GLOW      = "0 2px 8px rgba(234,88,12,0.25)"
ACCENT_SHADOW    = "0 4px 14px rgba(234,88,12,0.35)"

# ─── Surfaces (dark) ────────────────────────────────────────────────────────
PAGE_BACKGROUND      = "#0F172A"
SURFACE_BASE         = "#1E293B"
SURFACE_ELEVATED     = "#1E293B"
SURFACE_SOFT         = "#0F172A"
SURFACE_MUTED        = "#1E293B"
SURFACE_GHOST        = "#0F172A"
SURFACE_HOVER        = "#334155"
SURFACE_INTERACTIVE  = "rgba(234,88,12,0.08)"

# ─── Dark surfaces ──────────────────────────────────────────────────────────
DARK_900 = "#0F172A"
DARK_800 = "#1E293B"
DARK_700 = "#334155"
DARK_600 = "#475569"

# ─── Neutral / slate ────────────────────────────────────────────────────────
SLATE_500 = "#94A3B8"
SLATE_400 = "#94A3B8"
SLATE_300 = "#CBD5E1"
SLATE_200 = "#E2E8F0"
SLATE_100 = "#F1F5F9"
SLATE_50  = "#F8FAFC"

# ─── Borders (dark) ─────────────────────────────────────────────────────────
BORDER_COLOR     = "#334155"
BORDER_STRONG    = "#475569"
BORDER_ACCENT    = "#EA580C"

# ─── Text (dark) ────────────────────────────────────────────────────────────
TEXT_PRIMARY      = "#F1F5F9"
TEXT_SECONDARY    = "#CBD5E1"
TEXT_MUTED        = "#94A3B8"
TEXT_WHITE        = "#FFFFFF"

# ─── Semantic: success (dark) ───────────────────────────────────────────────
SUCCESS_BG       = "rgba(34,197,94,0.10)"
SUCCESS_TEXT     = "#4ADE80"
SUCCESS_BORDER   = "rgba(34,197,94,0.25)"

# ─── Semantic: danger (dark) ────────────────────────────────────────────────
DANGER_BG        = "rgba(239,68,68,0.10)"
DANGER_TEXT      = "#F87171"
DANGER_BORDER    = "rgba(239,68,68,0.25)"

# ─── Semantic: warning (dark) ───────────────────────────────────────────────
WARNING_BG       = "rgba(245,158,11,0.10)"
WARNING_TEXT     = "#FBBF24"
WARNING_BORDER   = "rgba(245,158,11,0.25)"

# ─── Semantic: info (dark) ──────────────────────────────────────────────────
INFO_BG          = "rgba(59,130,246,0.10)"
INFO_TEXT         = "#60A5FA"
INFO_BORDER      = "rgba(59,130,246,0.25)"

# ─── Shadows ─────────────────────────────────────────────────────────────────
GLOW             = "0 1px 3px rgba(0,0,0,0.3),0 1px 2px rgba(0,0,0,0.2)"
SOFT_GLOW        = "0 1px 2px rgba(0,0,0,0.2)"

# ─── Z-Index scale ──────────────────────────────────────────────────────────
Z_MENU_PUBLIC    = 10
Z_ADMIN_BACKDROP = 29
Z_ADMIN_SIDEBAR  = 30
Z_STICKY_HEADER  = 50
Z_DRAWER         = 200
Z_MODAL          = 300
Z_TOAST          = 400

# ─── Dark modal props ───────────────────────────────────────────────────────
DARK_MODAL_PROPS: dict = {
    "background": DARK_900,
    "border": f"1px solid {DARK_800}",
}
DARK_MODAL_TEXT      = "#F1F5F9"
DARK_MODAL_MUTED     = "#94A3B8"
DARK_MODAL_BORDER    = DARK_800
DARK_MODAL_INPUT_BG  = DARK_800
DARK_MODAL_INPUT_BORDER = DARK_700
DARK_MODAL_BTN_BG    = DARK_800
DARK_MODAL_BTN_BORDER = DARK_700

# ─── Sidebar dark ───────────────────────────────────────────────────────────
SIDEBAR_BG           = DARK_900
SIDEBAR_BORDER       = DARK_800
SIDEBAR_TEXT         = "rgba(255,255,255,0.78)"
SIDEBAR_TEXT_ACTIVE  = TEXT_WHITE
SIDEBAR_HOVER_BG    = "rgba(255,255,255,0.10)"
