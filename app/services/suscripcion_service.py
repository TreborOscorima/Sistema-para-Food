"""Enforcement de suscripción — lógica pura de bloqueo por plan.

Réplica adaptada del billing_service de Sistema-de-Ventas: la activación y
suspensión de empresas se gestiona desde el Owner Admin compartido; acá solo
se decide si una empresa puede operar en este momento.
"""

from __future__ import annotations

from datetime import datetime

from app.models.company import Company

MSG_SUSPENDIDA = "Cuenta suspendida. Contacta a soporte de TUWAYKI para reactivarla."
MSG_TRIAL_VENCIDO = (
    "Tu período de prueba finalizó. "
    "Contacta a TUWAYKI para activar tu plan y seguir operando."
)


def evaluar_bloqueo(company: Company | None, ahora: datetime) -> str:
    """'' si la empresa puede operar; mensaje de bloqueo si no."""
    if company is None or not company.is_active:
        return MSG_SUSPENDIDA
    if company.trial_ends_at and ahora > company.trial_ends_at:
        return MSG_TRIAL_VENCIDO
    return ""
