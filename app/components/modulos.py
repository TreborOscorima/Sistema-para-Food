"""Fuente única de nombre + ícono + descripción por módulo (plan UX T-05).

Un mismo módulo se mostraba con distintos nombres/íconos según dónde se mirara
(nav del staff, sidebar del dono, quick-links), lo que rompía el modelo mental.
Este registro es la única fuente de verdad: lo consumen la nav del staff
(`shared.py`), el sidebar y los quick-links del dono (`dono.py`). Así un módulo
se ve igual en todos lados y no vuelve a divergir.

Los íconos son nombres de lucide (los que usa `rx.icon(tag=...)`).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Modulo:
    label: str
    icon: str
    desc: str


MODULOS: dict[str, Modulo] = {
    # ── Operativos (nav del staff) ──────────────────────────────────────────
    "mozos":       Modulo("Mozos",         "layout_grid",    "Mesas y comanda"),
    "caja":        Modulo("Caja",          "wallet",         "Cobro y tickets"),
    "mostrador":   Modulo("Mostrador",     "shopping_bag",   "Takeaway rápido"),
    "cocina":      Modulo("Cocina",        "chef_hat",       "KDS / Producción"),
    "impresion":   Modulo("Impresión",     "printer",        "Comandas a la térmica"),
    "carta":       Modulo("Carta",         "book_open",      "Categorías y productos"),
    # ── Administrativos (sidebar del dono) ──────────────────────────────────
    "reportes":    Modulo("Reportes",      "trending_up",    "Dashboard y ventas del día"),
    "clientes":    Modulo("Clientes",      "users",          "Fidelización y alertas"),
    "cuentas":     Modulo("Cuentas",       "credit_card",    "Fiado y créditos"),
    "promociones": Modulo("Promociones",   "tag",            "Descuentos y cupones"),
    "reservas":    Modulo("Reservas",      "calendar_clock", "Mesas reservadas"),
    "delivery":    Modulo("Delivery",      "truck",          "Pedidos a domicilio"),
    "inventario":  Modulo("Inventario",    "package",        "Stock y alertas"),
    "usuarios":    Modulo("Usuarios",      "users_round",    "Personal y PINs"),
    "config":      Modulo("Configuración", "settings",       "Ajustes del sistema"),
}
