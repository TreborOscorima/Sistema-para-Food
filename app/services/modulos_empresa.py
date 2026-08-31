"""Módulos y límites habilitables por empresa (override del owner).

Fase 3 de la paridad Owner Panel. El owner (plataforma) puede habilitar o
deshabilitar módulos por empresa y ajustar sus límites desde el panel. El
override MANDA sobre el default del plan: si hay una fila en `food_company_modulos`
para un módulo, gana; si no, se usa el default del plan (`plan_service`).

Los módulos "core" (mozos, caja, cocina, etc.) no son toggleables: siempre están.
"""
from __future__ import annotations

from sqlmodel import select

from app.models.company import Company
from app.models.food import CompanyModulo
from app.services.plan_service import (
    FEAT_CLIENTES,
    FEAT_CUENTAS_CORRIENTES,
    FEAT_INVENTARIO,
    FEAT_PROMOCIONES,
    FEAT_REPORTES_AVANZADOS,
    plan_limite,
    plan_permite,
)

# Catálogo de módulos toggleables por empresa.
#   key         — identificador estable (se guarda en la tabla).
#   label       — nombre visible en el panel.
#   feature     — feature de plan que define el DEFAULT (None si es "próximamente"
#                 o si es un módulo "core opcional").
#   core        — módulo del núcleo operativo que viene ON en TODOS los planes pero
#                 el owner puede APAGAR por empresa (ej.: Cocina para un local sin
#                 pantalla KDS). No depende del plan; el default es habilitado.
#   descripcion — texto de ayuda para la tarjeta del panel del owner.
#   coming_soon — el módulo aún no tiene página; se muestra deshabilitado.
MODULOS_TOGGLEABLES: list[dict] = [
    {"key": "cocina",             "label": "Cocina (pantalla / KDS)", "feature": None, "core": True, "coming_soon": False,
     "descripcion": "Pantalla para ver y avanzar el estado de los pedidos en cocina. "
                    "Al desactivarla, las comandas se siguen imprimiendo pero sin pantalla de seguimiento."},
    {"key": "inventario",         "label": "Inventario",        "feature": FEAT_INVENTARIO,         "coming_soon": False},
    {"key": "promociones",        "label": "Promociones",       "feature": FEAT_PROMOCIONES,        "coming_soon": False},
    {"key": "cuentas",            "label": "Cuentas / Fiado",   "feature": FEAT_CUENTAS_CORRIENTES, "coming_soon": False},
    {"key": "clientes",           "label": "Clientes",          "feature": FEAT_CLIENTES,           "coming_soon": False},
    {"key": "reportes_avanzados", "label": "Reportes avanzados", "feature": FEAT_REPORTES_AVANZADOS, "coming_soon": False},
    {"key": "reservas",           "label": "Reservas",          "feature": None,                    "coming_soon": True},
    {"key": "delivery",           "label": "Delivery",          "feature": None,                    "coming_soon": True},
]

_FEATURE_POR_MODULO: dict[str, str | None] = {m["key"]: m["feature"] for m in MODULOS_TOGGLEABLES}
_KEYS_APLICABLES: set[str] = {m["key"] for m in MODULOS_TOGGLEABLES if not m["coming_soon"]}
# Módulos "core opcional": ON por defecto en todos los planes, apagables por empresa.
_CORE_MODULOS: set[str] = {m["key"] for m in MODULOS_TOGGLEABLES if m.get("core")}

# Ruta de página -> módulo (para el gate de navegación en food_state).
PAGINAS_MODULO: dict[str, str] = {
    "cocina": "cocina",
    "inventario": "inventario",
    "promociones": "promociones",
    "cupones": "promociones",
    "cuentas": "cuentas",
    "clientes": "clientes",
}

# Límites ajustables por empresa. `recurso` es la clave del default del plan
# (None = sin default de plan, arranca ilimitado salvo override).
LIMITES: list[dict] = [
    {"key": "max_usuarios",   "label": "Máx. usuarios",   "recurso": "max_usuarios"},
    {"key": "max_mesas",      "label": "Máx. mesas",      "recurso": "max_mesas"},
    {"key": "max_sucursales", "label": "Máx. sucursales", "recurso": None},
]
_LIMITE_KEYS: set[str] = {l["key"] for l in LIMITES}


def modulo_habilitado(overrides: dict[str, bool], plan: str, modulo: str) -> bool:
    """Resuelve si un módulo está habilitado.

    Orden: override de la empresa → si es "core opcional", ON por defecto → si no,
    el default del feature de plan → False ("próximamente"/desconocido).
    """
    if modulo in overrides:
        return bool(overrides[modulo])
    if modulo in _CORE_MODULOS:
        return True  # núcleo operativo: ON salvo que el owner lo apague (override)
    feat = _FEATURE_POR_MODULO.get(modulo)
    if feat is None:
        return False  # "próximamente" / desconocido: apagado hasta que exista
    return plan_permite(plan, feat)


def cargar_overrides(session, company_id: int) -> dict[str, bool]:
    """Lee las filas de override de una empresa como {modulo: habilitado}."""
    rows = session.exec(
        select(CompanyModulo).where(CompanyModulo.company_id == company_id)
    ).all()
    return {r.modulo: bool(r.habilitado) for r in rows}


def estado_modulos(overrides: dict[str, bool], plan: str) -> dict[str, bool]:
    """Estado resuelto de TODOS los módulos toggleables (para el panel)."""
    return {
        m["key"]: modulo_habilitado(overrides, plan, m["key"])
        for m in MODULOS_TOGGLEABLES
    }


def guardar_modulos(session, company_id: int, modulos: dict[str, bool]) -> None:
    """Upsert de los overrides. Ignora keys desconocidas o 'próximamente'."""
    from tuwayki_core.utils.timezone import utc_now_naive

    existentes = {
        r.modulo: r
        for r in session.exec(
            select(CompanyModulo).where(CompanyModulo.company_id == company_id)
        ).all()
    }
    now = utc_now_naive()
    for key, val in (modulos or {}).items():
        if key not in _KEYS_APLICABLES:
            continue
        row = existentes.get(key)
        if row is not None:
            row.habilitado = bool(val)
            row.updated_at = now
            session.add(row)
        else:
            session.add(CompanyModulo(
                company_id=company_id, modulo=key, habilitado=bool(val),
                created_at=now, updated_at=now,
            ))


def limite_efectivo(company: Company, key: str, plan: str) -> int | None:
    """Límite vigente de un recurso: override de la empresa si no es NULL, si no
    el default del plan. Devuelve None cuando no hay límite (ilimitado)."""
    override = getattr(company, key, None)
    if override is not None:
        return int(override)
    recurso = next((l["recurso"] for l in LIMITES if l["key"] == key), None)
    if recurso is None:
        return None
    return plan_limite(plan, recurso)


def guardar_limites(session, company: Company, limites: dict) -> None:
    """Setea las columnas de límite de la empresa. Valor None/'' = volver al
    default del plan (columna NULL). Valores fuera de rango se ignoran."""
    for key, raw in (limites or {}).items():
        if key not in _LIMITE_KEYS:
            continue
        if raw in (None, ""):
            setattr(company, key, None)
            continue
        try:
            val = int(raw)
        except (TypeError, ValueError):
            continue
        if val < 1 or val > 100000:
            continue
        setattr(company, key, val)
    session.add(company)
