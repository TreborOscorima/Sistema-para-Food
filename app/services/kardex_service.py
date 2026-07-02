"""Kardex de insumos — registro de cada movimiento de stock con su saldo.

Réplica adaptada de StockMovement + _adjustment_mixin de Sistema-de-Ventas.
Toda modificación de stock pasa por acá para que el historial nunca tenga
huecos: consumo por venta, reposición por anulación, compras, mermas y
ajustes de conteo físico.
"""

from __future__ import annotations

from decimal import Decimal

from tuwayki_core.utils.timezone import utc_now_naive

from app.models.food import Insumo, MovimientoInsumo, TipoMovimientoInsumo

CATEGORIAS_MERMA = ["Vencido", "Dañado", "Plato devuelto", "Error de cocina", "Otro"]


def _dec3(value) -> Decimal:
    if value is None:
        return Decimal("0.000")
    if isinstance(value, Decimal):
        return value.quantize(Decimal("0.001"))
    return Decimal(str(value)).quantize(Decimal("0.001"))


def _registrar(
    session,
    insumo: Insumo,
    usuario_id: int | None,
    tipo: str,
    delta: Decimal,
    motivo: str | None = None,
    pedido_id: int | None = None,
) -> MovimientoInsumo:
    """Aplica el delta al stock (clampeado en 0) y registra la fila de kardex.

    El delta registrado es el realmente aplicado: si un consumo pide más de
    lo disponible, el kardex refleja lo que efectivamente salió.
    """
    stock_previo = _dec3(insumo.stock_actual)
    stock_nuevo = stock_previo + _dec3(delta)
    if stock_nuevo < 0:
        stock_nuevo = Decimal("0.000")
    delta_real = stock_nuevo - stock_previo
    now = utc_now_naive()
    insumo.stock_actual = stock_nuevo
    insumo.updated_at = now
    session.add(insumo)
    movimiento = MovimientoInsumo(
        company_id=insumo.company_id,
        insumo_id=insumo.id or 0,
        usuario_id=usuario_id,
        pedido_id=pedido_id,
        tipo=tipo,
        cantidad=delta_real,
        stock_resultante=stock_nuevo,
        motivo=(motivo or "").strip()[:240] or None,
    )
    session.add(movimiento)
    return movimiento


def registrar_entrada(
    session, insumo: Insumo, usuario_id: int | None, cantidad: Decimal, motivo: str | None = None
) -> MovimientoInsumo:
    cantidad = _dec3(cantidad)
    if cantidad <= 0:
        raise ValueError("La cantidad de entrada debe ser mayor a cero.")
    return _registrar(
        session, insumo, usuario_id, TipoMovimientoInsumo.ENTRADA.value, cantidad, motivo
    )


def registrar_merma(
    session, insumo: Insumo, usuario_id: int | None, cantidad: Decimal, motivo: str | None
) -> MovimientoInsumo:
    cantidad = _dec3(cantidad)
    if cantidad <= 0:
        raise ValueError("La cantidad de merma debe ser mayor a cero.")
    if not (motivo or "").strip():
        raise ValueError("Indica el motivo de la merma.")
    if cantidad > _dec3(insumo.stock_actual):
        raise ValueError("La merma no puede superar el stock actual.")
    return _registrar(
        session, insumo, usuario_id, TipoMovimientoInsumo.MERMA.value, -cantidad, motivo
    )


def registrar_ajuste(
    session, insumo: Insumo, usuario_id: int | None, stock_contado: Decimal, motivo: str | None = None
) -> MovimientoInsumo | None:
    """Conteo físico: registra la diferencia entre lo contado y el sistema.

    Devuelve None si no hay diferencia (no ensucia el kardex).
    """
    stock_contado = _dec3(stock_contado)
    if stock_contado < 0:
        raise ValueError("El stock contado no puede ser negativo.")
    delta = stock_contado - _dec3(insumo.stock_actual)
    if delta == 0:
        return None
    return _registrar(
        session, insumo, usuario_id, TipoMovimientoInsumo.AJUSTE.value, delta,
        motivo or "Conteo físico",
    )


def registrar_consumo(
    session, insumo: Insumo, cantidad: Decimal, pedido_id: int | None
) -> MovimientoInsumo:
    """Descuento automático por venta (recetas). Cantidad en positivo."""
    return _registrar(
        session, insumo, None, TipoMovimientoInsumo.CONSUMO.value,
        -_dec3(cantidad), None, pedido_id,
    )


def registrar_reposicion(
    session, insumo: Insumo, cantidad: Decimal, pedido_id: int | None
) -> MovimientoInsumo:
    """Reverso automático por anulación de venta. Cantidad en positivo."""
    return _registrar(
        session, insumo, None, TipoMovimientoInsumo.REPOSICION.value,
        _dec3(cantidad), "Anulación de venta", pedido_id,
    )
