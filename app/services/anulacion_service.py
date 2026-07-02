"""Anulación auditada de pedidos — motivo obligatorio, quién y cuándo.

Réplica adaptada del flujo delete_sale de Sistema-de-Ventas (states/cash/
_delete_mixin.py): en un restobar la anulación post-comanda es el vector
clásico de robo hormiga, así que nunca se borra la fila — el pedido queda
CANCELADO con motivo, usuario y timestamp.

Dos flujos:
- Pedido abierto (mesa activa, aún sin cobrar): libera la mesa. El stock de
  insumos no se toca porque se descuenta recién al cobrar.
- Venta cobrada: repone el stock de insumos, revierte el fiado en la cuenta
  corriente con un contraasiento (nunca borrando el cargo original) y saca
  la venta del arqueo (los pagos de pedidos cancelados se excluyen).
"""

from __future__ import annotations

from decimal import Decimal

from sqlmodel import select

from tuwayki_core.utils.timezone import utc_now_naive

from app.services.kardex_service import registrar_reposicion
from app.models.food import (
    CuentaCorriente,
    DetallePedido,
    EstadoMesa,
    EstadoPedido,
    Insumo,
    Mesa,
    MovimientoCuenta,
    Pedido,
    RecetaItem,
)

_ESTADOS_ABIERTOS = (
    EstadoPedido.BORRADOR.value,
    EstadoPedido.ENVIADO.value,
    EstadoPedido.EN_PREPARACION.value,
    EstadoPedido.LISTO.value,
)


def _validar_motivo(motivo: str | None) -> str:
    motivo = (motivo or "").strip()
    if len(motivo) < 3:
        raise ValueError("Indica el motivo de la anulación (mínimo 3 caracteres).")
    return motivo[:240]


def _marcar_cancelado(pedido: Pedido, usuario_id: int | None, motivo: str) -> None:
    now = utc_now_naive()
    pedido.estado = EstadoPedido.CANCELADO.value
    pedido.pagado = False
    pedido.motivo_cancelacion = motivo
    pedido.cancelado_por_id = usuario_id
    pedido.cancelado_en = now
    pedido.updated_at = now


def reponer_stock_por_pedido(session, pedido_id: int, company_id: int) -> None:
    """Devuelve al stock los insumos consumidos por las recetas del pedido.

    Espejo exacto de _descontar_stock_por_pedido (food_state): mismo cálculo,
    signo inverso.
    """
    detalles = session.exec(
        select(DetallePedido).where(DetallePedido.pedido_id == pedido_id)
    ).all()
    if not detalles:
        return
    producto_ids = list({d.producto_id for d in detalles})
    recetas = session.exec(
        select(RecetaItem).where(
            RecetaItem.company_id == company_id,
            RecetaItem.producto_id.in_(producto_ids),
        )
    ).all()
    if not recetas:
        return
    receta_por_producto: dict[int, list] = {}
    for r in recetas:
        receta_por_producto.setdefault(r.producto_id, []).append(r)
    insumo_ids = list({r.insumo_id for r in recetas})
    insumos = {
        i.id: i
        for i in session.exec(
            select(Insumo).where(
                Insumo.company_id == company_id,
                Insumo.id.in_(insumo_ids),
            )
        ).all()
    }
    reposiciones: dict[int, Decimal] = {}
    for d in detalles:
        for ri in receta_por_producto.get(d.producto_id, []):
            uso = Decimal(str(ri.cantidad)) * d.cantidad
            reposiciones[ri.insumo_id] = reposiciones.get(ri.insumo_id, Decimal("0")) + uso
    for insumo_id, cantidad in reposiciones.items():
        ins = insumos.get(insumo_id)
        if ins:
            registrar_reposicion(session, ins, cantidad, pedido_id)


def revertir_fiado_pedido(session, pedido: Pedido) -> Decimal:
    """Revierte los cargos de cuenta corriente del pedido con un contraasiento.

    Devuelve el monto total revertido (0 si el pedido no tenía fiado).
    """
    cargos = session.exec(
        select(MovimientoCuenta).where(
            MovimientoCuenta.company_id == pedido.company_id,
            MovimientoCuenta.pedido_id == pedido.id,
            MovimientoCuenta.tipo == "cargo",
        )
    ).all()
    total_revertido = Decimal("0.00")
    now = utc_now_naive()
    for cargo in cargos:
        monto = Decimal(str(cargo.monto))
        cuenta = session.get(CuentaCorriente, cargo.cuenta_id)
        if cuenta is None:
            continue
        session.add(MovimientoCuenta(
            company_id=pedido.company_id,
            cuenta_id=cargo.cuenta_id,
            pedido_id=pedido.id,
            tipo="pago",
            monto=monto,
            descripcion=f"Anulación pedido #{pedido.id} — reverso de fiado",
        ))
        cuenta.saldo_deuda = Decimal(str(cuenta.saldo_deuda)) - monto
        cuenta.updated_at = now
        session.add(cuenta)
        total_revertido += monto
    return total_revertido


def anular_pedido_abierto(
    session,
    pedido: Pedido,
    usuario_id: int | None,
    motivo: str | None,
) -> Pedido:
    """Anula un pedido aún no cobrado y libera su mesa."""
    motivo = _validar_motivo(motivo)
    if pedido.estado == EstadoPedido.CANCELADO.value:
        raise ValueError("El pedido ya está anulado.")
    if pedido.estado not in _ESTADOS_ABIERTOS:
        raise ValueError("Este pedido ya fue cobrado — usa la anulación de venta desde Reportes.")
    _marcar_cancelado(pedido, usuario_id, motivo)
    session.add(pedido)
    if pedido.mesa_id:
        mesa = session.get(Mesa, pedido.mesa_id)
        if mesa is not None:
            mesa.estado = EstadoMesa.LIBRE.value
            mesa.updated_at = utc_now_naive()
            session.add(mesa)
    session.flush()
    return pedido


def anular_venta_cobrada(
    session,
    pedido: Pedido,
    usuario_id: int | None,
    motivo: str | None,
) -> Decimal:
    """Anula una venta ya cobrada: repone stock y revierte el fiado.

    Devuelve el monto de fiado revertido. Los pagos registrados quedan como
    evidencia pero dejan de contar en el arqueo (pedido CANCELADO).
    """
    motivo = _validar_motivo(motivo)
    if pedido.estado == EstadoPedido.CANCELADO.value:
        raise ValueError("La venta ya está anulada.")
    if pedido.estado != EstadoPedido.COBRADO.value:
        raise ValueError("Solo se pueden anular ventas cobradas.")
    reponer_stock_por_pedido(session, pedido.id or 0, pedido.company_id)
    fiado_revertido = revertir_fiado_pedido(session, pedido)
    _marcar_cancelado(pedido, usuario_id, motivo)
    session.add(pedido)
    session.flush()
    return fiado_revertido
