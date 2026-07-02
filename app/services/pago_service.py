"""Pagos divididos y mixtos de un pedido — validación y persistencia.

Réplica adaptada del patrón SalePayment + payment_mixin de Sistema-de-Ventas:
un cobro se compone de 1..N pagos (efectivo + tarjeta, o un pago por comensal).

Reglas de negocio:
- La suma de pagos debe cubrir el total a pagar (consumo - descuento + propina).
- El vuelto solo puede salir del efectivo: los métodos electrónicos y el fiado
  no pueden exceder, en conjunto, el total a pagar.
- El fiado dentro de un pago dividido carga a la cuenta corriente solo su parte.
- El efectivo se persiste neto de vuelto (lo que realmente queda en el cajón).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from app.models.food import PagoPedido, Pedido

METODOS_PAGO_VALIDOS = ("efectivo", "tarjeta", "qr", "fiado")


def _dec(value) -> Decimal:
    if value is None:
        return Decimal("0.00")
    if isinstance(value, Decimal):
        return value.quantize(Decimal("0.01"))
    return Decimal(str(value)).quantize(Decimal("0.01"))


@dataclass(slots=True)
class ResultadoPagos:
    """Resultado de validar una lista de pagos contra el total a pagar."""

    total_pagado: Decimal
    total_efectivo: Decimal      # bruto entregado por el cliente
    total_fiado: Decimal
    vuelto: Decimal              # sale del efectivo
    efectivo_neto: Decimal       # lo que queda en el cajón


def validar_pagos(
    total_a_pagar: Decimal,
    pagos: list[tuple[str, Decimal]],
) -> ResultadoPagos:
    """Valida una lista de pagos (metodo, monto) contra el total a pagar.

    Lanza ValueError con mensaje para la UI si la combinación es inválida.
    """
    total_a_pagar = _dec(total_a_pagar)
    if not pagos:
        raise ValueError("Agrega al menos un pago.")
    total_pagado = Decimal("0.00")
    total_efectivo = Decimal("0.00")
    total_no_efectivo = Decimal("0.00")
    total_fiado = Decimal("0.00")
    for metodo, monto in pagos:
        if metodo not in METODOS_PAGO_VALIDOS:
            raise ValueError(f"Método de pago inválido: {metodo}.")
        monto = _dec(monto)
        if monto <= 0:
            raise ValueError("Cada pago debe ser mayor a cero.")
        total_pagado += monto
        if metodo == "efectivo":
            total_efectivo += monto
        else:
            total_no_efectivo += monto
            if metodo == "fiado":
                total_fiado += monto
    if total_pagado < total_a_pagar:
        faltante = total_a_pagar - total_pagado
        raise ValueError(f"Los pagos no cubren el total: faltan S/ {faltante:.2f}.")
    if total_no_efectivo > total_a_pagar:
        raise ValueError(
            "Los métodos sin efectivo no pueden superar el total a pagar "
            "(el vuelto solo sale del efectivo)."
        )
    vuelto = total_pagado - total_a_pagar
    return ResultadoPagos(
        total_pagado=total_pagado,
        total_efectivo=total_efectivo,
        total_fiado=total_fiado,
        vuelto=vuelto,
        efectivo_neto=total_efectivo - vuelto,
    )


def registrar_pagos_pedido(
    session,
    pedido: Pedido,
    turno_caja_id: int | None,
    usuario_id: int | None,
    pagos: list[tuple[str, Decimal]],
    resultado: ResultadoPagos,
) -> list[PagoPedido]:
    """Persiste los pagos de un pedido. El efectivo se consolida en una sola
    fila neta de vuelto (lo que queda en el cajón); el resto va fila por fila."""
    filas: list[PagoPedido] = []
    if resultado.efectivo_neto > 0:
        filas.append(PagoPedido(
            company_id=pedido.company_id,
            pedido_id=pedido.id or 0,
            turno_caja_id=turno_caja_id,
            usuario_id=usuario_id,
            metodo="efectivo",
            monto=resultado.efectivo_neto,
        ))
    for metodo, monto in pagos:
        if metodo == "efectivo":
            continue
        filas.append(PagoPedido(
            company_id=pedido.company_id,
            pedido_id=pedido.id or 0,
            turno_caja_id=turno_caja_id,
            usuario_id=usuario_id,
            metodo=metodo,
            monto=_dec(monto),
        ))
    for fila in filas:
        session.add(fila)
    session.flush()
    return filas


def metodo_pago_resumen(pagos: list[tuple[str, Decimal]]) -> str:
    """Etiqueta para Pedido.metodo_pago: el método único, o 'mixto'."""
    metodos = {metodo for metodo, _ in pagos}
    if len(metodos) == 1:
        return next(iter(metodos))
    return "mixto"
