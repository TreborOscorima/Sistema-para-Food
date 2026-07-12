"""Servicio de auditoría transversal — registra acciones sensibles de forma inmutable."""

from __future__ import annotations

import json
from tuwayki_core.utils.timezone import utc_now_naive

from app.models.food import Auditoria


def registrar_auditoria(
    session,
    company_id: int,
    accion: str,
    *,
    usuario_id: int | None = None,
    usuario_nombre: str = "",
    entidad: str = "",
    entidad_id: int | None = None,
    detalle: str | dict | None = None,
    ip: str | None = None,
) -> None:
    if isinstance(detalle, dict):
        detalle = json.dumps(detalle, ensure_ascii=False, default=str)
    registro = Auditoria(
        company_id=company_id,
        usuario_id=usuario_id,
        usuario_nombre=usuario_nombre,
        accion=accion,
        entidad=entidad,
        entidad_id=entidad_id,
        detalle=detalle,
        ip=ip,
        created_at=utc_now_naive(),
    )
    session.add(registro)
