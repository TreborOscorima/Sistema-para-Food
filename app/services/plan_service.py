"""Matriz de features por plan y enforcement de límites.

Planes:
  trial       — todo habilitado durante el período de prueba
  standard    — operación básica (mozos, cocina, caja, carta, reportes básicos)
                + INVENTARIO BÁSICO (stock, alertas, movimientos, kardex)
  profesional — todo sin límites; suma inventario avanzado (recetas con
                descuento automático + planificador de producción), promos,
                reportes avanzados, clientes y cuentas corrientes
  enterprise  — (en planeación) aún no habilitado como plan válido
"""

from __future__ import annotations

PLAN_TRIAL = "trial"
PLAN_STANDARD = "standard"
PLAN_PROFESIONAL = "profesional"
PLAN_ENTERPRISE = "enterprise"  # en planeación; todavía no es un plan operativo
PLANES_VALIDOS = {PLAN_TRIAL, PLAN_STANDARD, PLAN_PROFESIONAL}

FEAT_INVENTARIO = "inventario"
# Inventario avanzado = recetas (descuento automático de stock) + planificador de
# producción. Es lo que diferencia el inventario "completo" (Profesional) del
# "básico" que ya trae Standard (stock, alertas, movimientos, kardex).
FEAT_INVENTARIO_AVANZADO = "inventario_avanzado"
FEAT_REPORTES_AVANZADOS = "reportes_avanzados"
FEAT_PROMOCIONES = "promociones"
FEAT_CUPONES = "cupones"
FEAT_CUENTAS_CORRIENTES = "cuentas_corrientes"
FEAT_EXPORT_EXCEL = "export_excel"
FEAT_CLIENTES = "clientes"

# Standard trae inventario BÁSICO (el módulo Inventario visible, sin recetas ni
# planificador de producción — esos son inventario avanzado del plan Profesional).
_FEATURES_STANDARD: set[str] = {
    FEAT_INVENTARIO,
}

_FEATURES_PROFESIONAL: set[str] = {
    FEAT_INVENTARIO,
    FEAT_INVENTARIO_AVANZADO,
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
    PLAN_ENTERPRISE: "Enterprise",
}

# Ícono (tag de lucide) propio de cada plan, para que el badge no quede siempre
# con la corona. Coincide con la vista comparativa mostrada a clientes.
PLAN_ICONS: dict[str, str] = {
    PLAN_TRIAL: "hourglass",
    PLAN_STANDARD: "sparkles",
    PLAN_PROFESIONAL: "crown",
    PLAN_ENTERPRISE: "rocket",
}
_PLAN_ICON_DEFAULT = "badge-check"

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


def plan_icon(plan: str) -> str:
    """Tag de ícono (lucide) del plan, para el badge del panel."""
    return PLAN_ICONS.get(plan, _PLAN_ICON_DEFAULT)


def check_limite_usuarios(plan: str, usuarios_actuales: int, maximo: int | None = None) -> str:
    # `maximo` permite pasar el límite efectivo por empresa (override del owner);
    # si es None se usa el default del plan. 0 = ilimitado.
    if maximo is None:
        maximo = plan_limite(plan, "max_usuarios")
    if maximo and usuarios_actuales >= maximo:
        return (
            f"Límite alcanzado: máximo {maximo} usuarios. "
            f"Contacte a TUWAYKI para ampliar su plan."
        )
    return ""


def check_limite_mesas(plan: str, mesas_actuales: int, maximo: int | None = None) -> str:
    if maximo is None:
        maximo = plan_limite(plan, "max_mesas")
    if maximo and mesas_actuales >= maximo:
        return (
            f"Límite alcanzado: máximo {maximo} mesas. "
            f"Contacte a TUWAYKI para ampliar su plan."
        )
    return ""
