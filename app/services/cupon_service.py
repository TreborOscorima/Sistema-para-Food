"""Motor de cupones por código de lote.

Validación: código exacto (case-insensitive) + activo + fechas + cupo de usos.
Redención: incrementa usos_actuales y desactiva el lote si agota el cupo.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlmodel import Session, select

from app.models.food import CuponLote


def _dec(value) -> Decimal:
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value)).quantize(Decimal("0.01"))


def validar_cupon(
    session: Session,
    codigo: str,
    company_id: int,
    total_base: Decimal,
) -> tuple[CuponLote, Decimal]:
    """Valida el código y devuelve (cupon, descuento_calculado).

    Raises ValueError con mensaje legible si el cupón no aplica.
    """
    codigo_upper = codigo.strip().upper()
    if not codigo_upper:
        raise ValueError("Ingrese un código de cupón.")

    cupon = session.exec(
        select(CuponLote).where(
            CuponLote.company_id == company_id,
            CuponLote.codigo == codigo_upper,
        )
    ).first()

    if cupon is None:
        raise ValueError(f"Código '{codigo_upper}' no encontrado.")

    if not cupon.activo:
        raise ValueError(f"El cupón '{codigo_upper}' no está activo.")

    hoy = date.today()
    if cupon.fecha_inicio and hoy < cupon.fecha_inicio:
        raise ValueError(f"El cupón aún no está vigente (inicia {cupon.fecha_inicio}).")
    if cupon.fecha_fin and hoy > cupon.fecha_fin:
        raise ValueError(f"El cupón venció el {cupon.fecha_fin}.")

    if cupon.usos_max is not None and cupon.usos_actuales >= cupon.usos_max:
        raise ValueError(f"El cupón '{codigo_upper}' agotó sus usos.")

    # Calcular descuento
    base = _dec(total_base)
    valor = _dec(cupon.valor)
    if cupon.tipo == "porcentaje":
        descuento = (base * valor / Decimal("100")).quantize(Decimal("0.01"))
    elif cupon.tipo == "monto_fijo":
        descuento = min(valor, base)
    else:
        raise ValueError("Tipo de cupón no reconocido.")

    if descuento <= 0:
        raise ValueError("El cupón no genera descuento sobre el total actual.")

    return cupon, descuento


def redimir_cupon(session: Session, cupon_id: int) -> None:
    """Incrementa usos_actuales; desactiva el lote si se agota."""
    cupon = session.get(CuponLote, cupon_id)
    if cupon is None:
        return
    cupon.usos_actuales += 1
    if cupon.usos_max is not None and cupon.usos_actuales >= cupon.usos_max:
        cupon.activo = False
    session.add(cupon)
