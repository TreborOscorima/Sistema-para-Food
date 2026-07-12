"""Enforcement de suscripción — lógica pura de bloqueo por plan.

Réplica adaptada del billing_service de Sistema-de-Ventas: la activación y
suspensión de empresas se gestiona desde el Owner Admin compartido; acá solo
se decide si una empresa puede operar en este momento.
"""

from __future__ import annotations

from datetime import datetime

from app.models.company import Company
from app.services.plan_service import PLAN_TRIAL

MSG_SUSPENDIDA = "Cuenta suspendida. Contacta a soporte de TUWAYKI para reactivarla."
MSG_TRIAL_VENCIDO = (
    "Tu período de prueba finalizó. "
    "Contacta a TUWAYKI para activar tu plan y seguir operando."
)
MSG_PLAN_VENCIDO = (
    "Tu plan ha expirado. "
    "Contacta a TUWAYKI para renovar tu suscripción."
)


def evaluar_bloqueo(company: Company | None, ahora: datetime) -> str:
    """'' si la empresa puede operar; mensaje de bloqueo si no."""
    if company is None:
        return "Empresa no encontrada — contacte soporte."
    if not company.is_active:
        return MSG_SUSPENDIDA
    if ahora.tzinfo is not None:
        ahora = ahora.replace(tzinfo=None)
    plan = getattr(company, "plan", PLAN_TRIAL) or PLAN_TRIAL
    if plan == PLAN_TRIAL and company.trial_ends_at and ahora > company.trial_ends_at:
        return MSG_TRIAL_VENCIDO
    if plan != PLAN_TRIAL and company.plan_expires_at and ahora > company.plan_expires_at:
        return MSG_PLAN_VENCIDO
    return ""
