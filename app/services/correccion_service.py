"""Corrección auditada de un cobro ya confirmado — sin anular ni duplicar.

Cuando el cajero se equivoca en un cobro (producto de más/de menos, método de
pago errado, descuento mal puesto), corregirlo NO debe borrar la venta ni
generar una venta nueva: eso inflaría las ventas del turno (doble conteo). En
cambio, se **edita el mismo Pedido en su lugar** (mismo id, sigue COBRADO, mismo
turno_caja_id y cerrado_en) y se **reemplazan** sus pagos.

El cierre/arqueo agrega en vivo desde `PagoPedido` + `Pedido` filtrando por
turno, así que reemplazar las filas de pago y ajustar el total en el mismo
registro hace que la venta corregida cuente exactamente una vez.

Conceptualmente: "revertir los efectos del cobro previo (stock, fiado, pagos) y
re-aplicar el estado corregido, todo atómico y auditado", sin salir de COBRADO.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from sqlmodel import select

from tuwayki_core.utils.timezone import utc_now_naive

from app.models.food import (
    CuentaCorriente,
    DetallePedido,
    EstadoPedido,
    EstadoProduccion,
    MovimientoCuenta,
    PagoPedido,
    Pedido,
    Producto,
)
from app.services.anulacion_service import (
    reponer_stock_por_pedido,
    revertir_fiado_pedido,
)
from app.services.auditoria_service import registrar_auditoria
from app.services.pago_service import (
    metodo_pago_resumen,
    registrar_pagos_pedido,
    validar_pagos,
)


def _dec(value) -> Decimal:
    if value is None:
        return Decimal("0.00")
    if isinstance(value, Decimal):
        return value.quantize(Decimal("0.01"))
    return Decimal(str(value)).quantize(Decimal("0.01"))


def _validar_motivo(motivo: str | None) -> str:
    motivo = (motivo or "").strip()
    if len(motivo) < 3:
        raise ValueError("Indica el motivo de la corrección (mínimo 3 caracteres).")
    return motivo[:240]


@dataclass(slots=True)
class LineaCorreccion:
    """Una línea deseada del pedido corregido.

    ``detalle_id`` referencia una línea existente (para conservar su registro) o
    es ``None``/0 para una línea nueva agregada en la corrección.
    """

    producto_id: int
    cantidad: int
    precio_unitario: Decimal
    detalle_id: int | None = None
    notas: str | None = None


def _lineas_snapshot(session, pedido_id: int, company_id: int) -> list[dict]:
    detalles = session.exec(
        select(DetallePedido).where(DetallePedido.pedido_id == pedido_id)
    ).all()
    prod_ids = list({d.producto_id for d in detalles})
    nombres = {
        p.id: p.nombre
        for p in session.exec(
            select(Producto).where(
                Producto.company_id == company_id,
                Producto.id.in_(prod_ids),
            )
        ).all()
    } if prod_ids else {}
    return [
        {
            "producto": nombres.get(d.producto_id, f"#{d.producto_id}"),
            "producto_id": d.producto_id,
            "cantidad": d.cantidad,
            "subtotal": str(_dec(d.subtotal)),
        }
        for d in detalles
    ]


def _reponer_stock_diario_qty(session, uso: dict[int, int], company_id: int) -> None:
    """Devuelve al stock_diario las cantidades indicadas por producto."""
    if not uso:
        return
    productos = {
        p.id: p
        for p in session.exec(
            select(Producto).where(
                Producto.company_id == company_id,
                Producto.id.in_(list(uso.keys())),
                Producto.stock_diario.isnot(None),
            )
        ).all()
    }
    for pid, cant in uso.items():
        prod = productos.get(pid)
        if prod is None or cant <= 0:
            continue
        prod.stock_diario = (prod.stock_diario or 0) + cant
        if not prod.disponible and prod.stock_diario > 0:
            prod.disponible = True
        prod.updated_at = utc_now_naive()
        session.add(prod)


def _descontar_stock_diario_qty(session, uso: dict[int, int], company_id: int) -> None:
    """Descuenta del stock_diario las cantidades indicadas por producto."""
    if not uso:
        return
    productos = {
        p.id: p
        for p in session.exec(
            select(Producto).where(
                Producto.company_id == company_id,
                Producto.id.in_(list(uso.keys())),
                Producto.stock_diario.isnot(None),
            )
        ).all()
    }
    for pid, cant in uso.items():
        prod = productos.get(pid)
        if prod is None or cant <= 0:
            continue
        nuevo = max((prod.stock_diario or 0) - cant, 0)
        prod.stock_diario = nuevo
        if nuevo <= 0:
            prod.disponible = False
        prod.updated_at = utc_now_naive()
        session.add(prod)


def _registrar_cargo_cc(
    session, company_id: int, cliente_id: int, monto: Decimal,
    pedido_id: int | None, descripcion: str,
) -> None:
    """Carga ``monto`` a la cuenta corriente del cliente (standalone).

    Espejo de FoodState._registrar_cargo_cc, sin depender del estado de Reflex.
    """
    cc = session.exec(
        select(CuentaCorriente).where(
            CuentaCorriente.company_id == company_id,
            CuentaCorriente.cliente_id == cliente_id,
        )
    ).first()
    if cc is None:
        cc = CuentaCorriente(
            company_id=company_id,
            cliente_id=cliente_id,
            saldo_deuda=Decimal("0.00"),
            limite_credito=Decimal("0.00"),
        )
        session.add(cc)
        session.flush()
    saldo_actual = Decimal(str(cc.saldo_deuda))
    limite = Decimal(str(cc.limite_credito))
    if limite > Decimal("0.00") and saldo_actual + monto > limite:
        raise ValueError(
            f"Límite de crédito excedido. Deuda actual: S/ {saldo_actual:.2f}, "
            f"límite: S/ {limite:.2f}, cargo solicitado: S/ {monto:.2f}."
        )
    session.add(MovimientoCuenta(
        company_id=company_id,
        cuenta_id=cc.id or 0,
        pedido_id=pedido_id,
        tipo="cargo",
        monto=monto,
        descripcion=descripcion,
    ))
    cc.saldo_deuda = saldo_actual + monto
    cc.updated_at = utc_now_naive()
    session.add(cc)


def corregir_venta(
    session,
    pedido: Pedido,
    turno_id: int,
    usuario_id: int | None,
    usuario_nombre: str,
    *,
    lineas: list[LineaCorreccion],
    pagos: list[tuple[str, Decimal]],
    descuento: Decimal,
    propina: Decimal,
    recargo: Decimal,
    recargo_concepto: str | None,
    cliente_id: int | None,
    motivo: str | None,
    metodos_validos: set[str] | None = None,
    metodos_efectivo: set[str] | None = None,
) -> dict:
    """Corrige un cobro ya confirmado editando el MISMO pedido (una sola venta).

    Devuelve un dict ``{before, after}`` con los snapshots auditados. El caller
    hace ``commit``. Lanza ``ValueError`` (mensaje para la UI) ante entradas
    inválidas.
    """
    motivo = _validar_motivo(motivo)
    if pedido.estado != EstadoPedido.COBRADO.value:
        raise ValueError("Solo se pueden corregir cobros ya confirmados.")
    if not lineas:
        raise ValueError("La venta corregida debe tener al menos un producto.")

    company_id = pedido.company_id
    efectivos = set(metodos_efectivo) if metodos_efectivo else {"efectivo"}
    now = utc_now_naive()

    # 1) Snapshot ANTES (para auditoría)
    before = {
        "total": str(_dec(pedido.total)),
        "descuento": str(_dec(pedido.descuento)),
        "propina": str(_dec(pedido.propina)),
        "recargo": str(_dec(pedido.recargo)),
        "metodo": pedido.metodo_pago or "",
        "lineas": _lineas_snapshot(session, pedido.id or 0, company_id),
    }
    old_detalles = session.exec(
        select(DetallePedido).where(DetallePedido.pedido_id == pedido.id)
    ).all()
    old_qty: dict[int, int] = {}
    for d in old_detalles:
        old_qty[d.producto_id] = old_qty.get(d.producto_id, 0) + d.cantidad

    # 2) Revertir efectos del cobro previo
    #    Insumos (se descontaron al cobrar) y fiado (contraasiento idempotente).
    reponer_stock_por_pedido(session, pedido.id or 0, company_id)
    revertir_fiado_pedido(session, pedido)
    #    Pagos: se borran para no duplicar en el arqueo (el cierre suma en vivo).
    for pago in session.exec(
        select(PagoPedido).where(PagoPedido.pedido_id == pedido.id)
    ).all():
        session.delete(pago)
    session.flush()

    # 3) Recalcular las líneas deseadas contra las existentes (in-place).
    por_detalle = {d.id: d for d in old_detalles if d.id is not None}
    conservados: set[int] = set()
    nuevo_subtotal = Decimal("0.00")
    for ln in lineas:
        cantidad = int(ln.cantidad)
        if cantidad <= 0:
            continue
        precio = _dec(ln.precio_unitario)
        sub = precio * cantidad
        nuevo_subtotal += sub
        det = por_detalle.get(ln.detalle_id) if ln.detalle_id else None
        if det is not None:
            det.cantidad = cantidad
            det.precio_unitario = precio
            det.subtotal = sub
            if ln.notas is not None:
                det.notas = ln.notas or None
            det.updated_at = now
            session.add(det)
            conservados.add(det.id)
        else:
            session.add(DetallePedido(
                company_id=company_id,
                pedido_id=pedido.id or 0,
                producto_id=ln.producto_id,
                cantidad=cantidad,
                precio_unitario=precio,
                subtotal=sub,
                notas=ln.notas or None,
                # Corrección post-venta: la línea se da por entregada y NO se
                # rutea a cocina (no es una comanda nueva).
                estado_produccion=EstadoProduccion.ENTREGADO_AL_CLIENTE.value,
                impreso_cocina=True,
                impreso_caja=False,
                requiere_preparacion=False,
            ))
    # Borrar las líneas que ya no están
    for det in old_detalles:
        if det.id is not None and det.id not in conservados:
            session.delete(det)
    session.flush()

    nuevo_subtotal = _dec(nuevo_subtotal)
    descuento = _dec(descuento)
    propina = _dec(propina)
    recargo = _dec(recargo)
    if descuento > nuevo_subtotal:
        raise ValueError(
            f"El descuento (S/ {descuento:.2f}) no puede superar el nuevo "
            f"subtotal (S/ {nuevo_subtotal:.2f})."
        )
    total_final = max(nuevo_subtotal - descuento + propina + recargo, Decimal("0.00"))

    # 4) Reconciliar stock_diario por delta (se descuenta al agregar el ítem,
    #    no al cobrar): repone lo quitado, descuenta lo agregado.
    new_qty: dict[int, int] = {}
    for ln in lineas:
        if int(ln.cantidad) > 0:
            new_qty[ln.producto_id] = new_qty.get(ln.producto_id, 0) + int(ln.cantidad)
    repone: dict[int, int] = {}
    descuenta: dict[int, int] = {}
    for pid in set(old_qty) | set(new_qty):
        delta = new_qty.get(pid, 0) - old_qty.get(pid, 0)
        if delta > 0:
            descuenta[pid] = delta
        elif delta < 0:
            repone[pid] = -delta
    _reponer_stock_diario_qty(session, repone, company_id)
    _descontar_stock_diario_qty(session, descuenta, company_id)

    # 5) Validar y persistir los pagos corregidos
    pagos = [(m, _dec(v)) for m, v in pagos if _dec(v) > 0]
    resultado = None
    total_fiado = Decimal("0.00")
    if total_final > 0:
        if not pagos:
            raise ValueError("Agrega al menos un pago que cubra el total corregido.")
        resultado = validar_pagos(
            total_final, pagos,
            metodos_validos=metodos_validos, metodos_efectivo=efectivos,
        )
        total_fiado = resultado.total_fiado
    if total_fiado > 0 and (not cliente_id or cliente_id <= 0):
        raise ValueError("Selecciona el cliente para registrar el fiado.")

    # 6) Aplicar el estado corregido al MISMO pedido (sigue COBRADO)
    pedido.total = nuevo_subtotal
    pedido.descuento = descuento
    pedido.propina = propina
    pedido.recargo = recargo
    pedido.recargo_concepto = recargo_concepto if recargo > 0 else None
    pedido.metodo_pago = metodo_pago_resumen(pagos) if pagos else pedido.metodo_pago
    pedido.pagado = total_fiado == 0
    if cliente_id and cliente_id > 0:
        pedido.cliente_id = cliente_id
    pedido.updated_at = now
    session.add(pedido)

    # Descontar insumos del estado nuevo (espejo del cobro)
    from app.states.food_state import _descontar_stock_por_pedido  # evitar ciclo
    _descontar_stock_por_pedido(session, pedido.id or 0, company_id)

    if resultado is not None:
        registrar_pagos_pedido(
            session, pedido, turno_id, usuario_id, pagos, resultado,
            metodos_efectivo=efectivos,
        )
    if total_fiado > 0 and cliente_id:
        _registrar_cargo_cc(
            session, company_id, cliente_id, total_fiado, pedido.id,
            f"Fiado (corrección) pedido #{pedido.id}",
        )

    after = {
        "total": str(total_final),
        "subtotal": str(nuevo_subtotal),
        "descuento": str(descuento),
        "propina": str(propina),
        "recargo": str(recargo),
        "metodo": pedido.metodo_pago or "",
        "lineas": _lineas_snapshot(session, pedido.id or 0, company_id),
    }

    # 7) Auditoría inmutable
    registrar_auditoria(
        session, company_id, "correccion_cobro",
        usuario_id=usuario_id,
        usuario_nombre=usuario_nombre,
        entidad="pedido", entidad_id=pedido.id,
        detalle={"motivo": motivo, "before": before, "after": after},
    )
    session.flush()
    return {"before": before, "after": after}
