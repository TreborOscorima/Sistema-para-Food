"""Matriz de features por plan y enforcement de límites.

Planes:
  trial       — todo habilitado durante el período de prueba
  standard    — operación básica (mozos, cocina, caja, carta, reportes básicos)
  profesional — todo sin límites (inventario, promos, reportes avanzados, CC)
"""

from __future__ import annotations

PLAN_TRIAL = "trial"
PLAN_STANDARD = "standard"
PLAN_PROFESIONAL = "profesional"
PLANES_VALIDOS = {PLAN_TRIAL, PLAN_STANDARD, PLAN_PROFESIONAL}

FEAT_INVENTARIO = "inventario"
FEAT_REPORTES_AVANZADOS = "reportes_avanzados"
FEAT_PROMOCIONES = "promociones"
FEAT_CUPONES = "cupones"
FEAT_CUENTAS_CORRIENTES = "cuentas_corrientes"
FEAT_EXPORT_EXCEL = "export_excel"
FEAT_CLIENTES = "clientes"

_FEATURES_STANDARD: set[str] = set()

_FEATURES_PROFESIONAL: set[str] = {
    FEAT_INVENTARIO,
    FEAT_REPORTES_AVANZADOS,
    FEAT_PROMOCIONES,
    FEAT_CUPONES,
    FEAT_CUENTAS_CORRIENTES,
    FEAT_EXPORT_EXCEL,
    FEAT_CLIENTES,
}

_PLAN_FEATURES: dict[str, set[str]] = {
    PLAN_TRIAL: _FEATURES_PROFESIONAL,
    PLAN_STANDARD: _FEATURES_STANDARD,
    PLAN_PROFESIONAL: _FEATURES_PROFESIONAL,
}

_LIMITES: dict[str, dict[str, int]] = {
    PLAN_TRIAL: {"max_usuarios": 999, "max_mesas": 999},
    PLAN_STANDARD: {"max_usuarios": 5, "max_mesas": 10},
    PLAN_PROFESIONAL: {"max_usuarios": 999, "max_mesas": 999},
}

PLAN_LABELS: dict[str, str] = {
    PLAN_TRIAL: "Prueba",
    PLAN_STANDARD: "Standard",
    PLAN_PROFESIONAL: "Profesional",
}

PAGINAS_PREMIUM: dict[str, str] = {
    "inventario": FEAT_INVENTARIO,
    "promociones": FEAT_PROMOCIONES,
    "cupones": FEAT_CUPONES,
    "cuentas": FEAT_CUENTAS_CORRIENTES,
    "clientes": FEAT_CLIENTES,
}

MSG_UPGRADE = (
    "Esta función requiere el plan Profesional. "
    "Contacte a TUWAYKI para actualizar su plan."
)


def _validate_plan(plan: str) -> str:
    if plan not in PLANES_VALIDOS:
        return PLAN_STANDARD
    return plan


def plan_permite(plan: str, feature: str) -> bool:
    feats = _PLAN_FEATURES.get(_validate_plan(plan), _FEATURES_STANDARD)
    return feature in feats


def plan_limite(plan: str, recurso: str) -> int:
    limites = _LIMITES.get(_validate_plan(plan), _LIMITES[PLAN_STANDARD])
    if recurso not in limites:
        return 999
    return limites[recurso]


def plan_label(plan: str) -> str:
    return PLAN_LABELS.get(plan, plan.capitalize())


def check_limite_usuarios(plan: str, usuarios_actuales: int) -> str:
    maximo = plan_limite(plan, "max_usuarios")
    if usuarios_actuales >= maximo:
        return (
            f"Plan {plan_label(plan)}: máximo {maximo} usuarios. "
            f"Actualice al plan Profesional para agregar más."
        )
    return ""


def check_limite_mesas(plan: str, mesas_actuales: int) -> str:
    maximo = plan_limite(plan, "max_mesas")
    if mesas_actuales >= maximo:
        return (
            f"Plan {plan_label(plan)}: máximo {maximo} mesas. "
            f"Actualice al plan Profesional para agregar más."
        )
    return ""
