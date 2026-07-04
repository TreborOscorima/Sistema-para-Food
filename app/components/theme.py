"""Fuente única de verdad para la paleta de colores de TUWAYKIFOOD.

Todas las páginas importan de acá. shared.py re-exporta para compatibilidad.
dono.py ya no necesita su propia paleta local.

Convención: los nombres siguen la función semántica (ACCENT, TEXT_PRIMARY,
SUCCESS_BG) en vez del nombre de color (ORANGE, SLATE) — así un rebrand
es un solo archivo.

Z-Index scale documentada: evita conflictos entre sticky headers, drawers y modals.
"""

from __future__ import annotations

# ─── Accent ──────────────────────────────────────────────────────────────────
ACCENT           = "#EA580C"
ACCENT_HOVER     = "#C2410C"
ACCENT_BG        = "#FFF7ED"
ACCENT_TEXT      = "#9A3412"
ACCENT_SOFT      = "#FFF7ED"
ACCENT_MUTED     = "#FED7AA"
ACCENT_GLOW      = "0 2px 8px rgba(234,88,12,0.18)"
ACCENT_SHADOW    = "0 4px 14px rgba(234,88,12,0.35)"

# ─── Surfaces ────────────────────────────────────────────────────────────────
PAGE_BACKGROUND      = "#F8FAFC"
SURFACE_BASE         = "#FFFFFF"
SURFACE_ELEVATED     = "#FFFFFF"
SURFACE_SOFT         = "#F8FAFC"
SURFACE_MUTED        = "#F1F5F9"
SURFACE_GHOST        = "#F8FAFC"
SURFACE_HOVER        = "#F1F5F9"
SURFACE_INTERACTIVE  = "#FFF7ED"

# ─── Dark surfaces (login, mozos, cocina, mostrador) ─────────────────────────
DARK_900 = "#0F172A"
DARK_800 = "#1E293B"
DARK_700 = "#334155"
DARK_600 = "#475569"

# ─── Neutral / slate ────────────────────────────────────────────────────────
SLATE_500 = "#64748B"
SLATE_400 = "#94A3B8"
SLATE_300 = "#CBD5E1"
SLATE_200 = "#E2E8F0"
SLATE_100 = "#F1F5F9"
SLATE_50  = "#F8FAFC"

# ─── Borders ─────────────────────────────────────────────────────────────────
BORDER_COLOR     = "#E2E8F0"
BORDER_STRONG    = "#CBD5E1"
BORDER_ACCENT    = "#FED7AA"

# ─── Text ────────────────────────────────────────────────────────────────────
TEXT_PRIMARY      = "#0F172A"
TEXT_SECONDARY    = "#334155"
TEXT_MUTED        = "#64748B"
TEXT_WHITE        = "#FFFFFF"

# ─── Semantic: success ───────────────────────────────────────────────────────
SUCCESS_BG       = "#F0FDF4"
SUCCESS_TEXT     = "#15803D"
SUCCESS_BORDER   = "#BBF7D0"

# ─── Semantic: danger ────────────────────────────────────────────────────────
DANGER_BG        = "#FEF2F2"
DANGER_TEXT      = "#B91C1C"
DANGER_BORDER    = "#FECACA"

# ─── Semantic: warning ───────────────────────────────────────────────────────
WARNING_BG       = "#FFFBEB"
WARNING_TEXT     = "#B45309"
WARNING_BORDER   = "#FDE68A"

# ─── Semantic: info ──────────────────────────────────────────────────────────
INFO_BG          = "#EFF6FF"
INFO_TEXT        = "#1D4ED8"
INFO_BORDER      = "#BFDBFE"

# ─── Shadows ─────────────────────────────────────────────────────────────────
GLOW             = "0 1px 3px rgba(0,0,0,0.07),0 1px 2px rgba(0,0,0,0.04)"
SOFT_GLOW        = "0 1px 2px rgba(0,0,0,0.05)"

# ─── Z-Index scale ──────────────────────────────────────────────────────────
Z_MENU_PUBLIC    = 10
Z_ADMIN_BACKDROP = 29
Z_ADMIN_SIDEBAR  = 30
Z_STICKY_HEADER  = 50
Z_DRAWER         = 200
Z_MODAL          = 300
Z_TOAST          = 400

# ─── Sidebar dark ───────────────────────────────────────────────────────────
SIDEBAR_BG           = DARK_900
SIDEBAR_BORDER       = DARK_800
SIDEBAR_TEXT         = "rgba(255,255,255,0.58)"
SIDEBAR_TEXT_ACTIVE  = TEXT_WHITE
SIDEBAR_HOVER_BG    = "rgba(255,255,255,0.08)"
