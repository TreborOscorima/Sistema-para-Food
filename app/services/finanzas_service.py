"""Reportes financieros — P&L operativo, descuentos/anulaciones y mermas valorizado.

Todas las agregaciones se ejecutan en SQL para escalar con meses de historial.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy import func, case, literal_column
from sqlmodel import select

import json

from app.models.food import (
    Auditoria,
    EstadoPedido,
    Insumo,
    MovimientoInsumo,
    Pedido,
    TipoMovimientoInsumo,
    UsuarioFood,
)


def _dec(value) -> Decimal:
    if isinstance(value, Decimal):
        return value.quantize(Decimal("0.01"))
    return Decimal(str(value or 0)).quantize(Decimal("0.01"))


def _month_filters(company_id: int, anio: int, mes: int):
    inicio = datetime(anio, mes, 1)
    if mes == 12:
        fin = datetime(anio + 1, 1, 1)
    else:
        fin = datetime(anio, mes + 1, 1)
    return inicio, fin


# ─── ADM-01: P&L mensual ────────────────────────────────────────────────────


def pyl_mensual(
    session, company_id: int, anio: int, mes: int
) -> dict:
    """Estado de resultados operativo simple para un mes.

    Ventas netas (cobrado - descuentos) - costo insumos consumidos (kardex CONSUMO
    valorizado) - egresos de caja = utilidad bruta operativa.
    """
    inicio, fin = _month_filters(company_id, anio, mes)

    # Ventas netas: sum(total) de pedidos cobrados en el mes
    row_ventas = session.exec(
        select(
            func.coalesce(func.sum(Pedido.total), 0).label("ventas_brutas"),
            func.coalesce(func.sum(Pedido.descuento), 0).label("descuentos"),
            func.coalesce(func.sum(Pedido.propina), 0).label("propinas"),
            func.coalesce(func.sum(Pedido.recargo), 0).label("recargos"),
            func.count(Pedido.id).label("pedidos"),
        ).where(
            Pedido.company_id == company_id,
            Pedido.estado == EstadoPedido.COBRADO.value,
            Pedido.cerrado_en >= inicio,
            Pedido.cerrado_en < fin,
        )
    ).one()

    ventas_brutas = _dec(row_ventas[0])
    descuentos = _dec(row_ventas[1])
    propinas = _dec(row_ventas[2])
    recargos = _dec(row_ventas[3])
    pedidos_count = row_ventas[4]
    ventas_netas = ventas_brutas - descuentos

    # Costo de insumos consumidos: kardex CONSUMO valorizado
    # Unimos MovimientoInsumo con Insumo para obtener costo_unitario
    costo_consumo_val = session.exec(
        select(
            func.coalesce(
                func.sum(func.abs(MovimientoInsumo.cantidad) * Insumo.costo_unitario),
                0,
            ),
        )
        .select_from(MovimientoInsumo)
        .join(Insumo, MovimientoInsumo.insumo_id == Insumo.id)
        .where(
            MovimientoInsumo.company_id == company_id,
            MovimientoInsumo.tipo == TipoMovimientoInsumo.CONSUMO.value,
            MovimientoInsumo.created_at >= inicio,
            MovimientoInsumo.created_at < fin,
        )
    ).one()
    costo_consumo = _dec(costo_consumo_val)

    # Egresos de caja del mes
    from app.models.food import MovimientoCaja
    egresos_val = session.exec(
        select(
            func.coalesce(func.sum(MovimientoCaja.monto), 0),
        )
        .where(
            MovimientoCaja.company_id == company_id,
            MovimientoCaja.tipo == "egreso",
            MovimientoCaja.created_at >= inicio,
            MovimientoCaja.created_at < fin,
        )
    ).one()
    egresos = _dec(egresos_val)

    utilidad = ventas_netas - costo_consumo - egresos

    return {
        "anio": anio,
        "mes": mes,
        "ventas_brutas": ventas_brutas,
        "descuentos": descuentos,
        "ventas_netas": ventas_netas,
        "propinas": propinas,
        "recargos": recargos,
        "pedidos": pedidos_count,
        "costo_consumo": costo_consumo,
        "egresos_caja": egresos,
        "utilidad": utilidad,
        "margen_pct": float(
            round(utilidad / ventas_netas * 100, 1) if ventas_netas > 0 else 0
        ),
    }


# ─── ADM-05: Resumen IGV mensual ─────────────────────────────────────────────


def resumen_igv_mensual(
    session, company_id: int, anio: int, mes: int, porcentaje_igv: float = 18.0,
) -> dict:
    """Base imponible + IGV del mes. Precios incluyen IGV (estándar peruano)."""
    inicio, fin = _month_filters(company_id, anio, mes)
    row = session.exec(
        select(
            func.coalesce(func.sum(Pedido.total - Pedido.descuento + Pedido.recargo), 0),
            func.count(Pedido.id),
        ).where(
            Pedido.company_id == company_id,
            Pedido.estado == EstadoPedido.COBRADO.value,
            Pedido.cerrado_en >= inicio,
            Pedido.cerrado_en < fin,
        )
    ).one()
    ventas_netas = _dec(row[0])
    pedidos = row[1]
    factor = Decimal(str(1 + porcentaje_igv / 100))
    base_imponible = (ventas_netas / factor).quantize(Decimal("0.01"))
    igv = ventas_netas - base_imponible
    return {
        "anio": anio,
        "mes": mes,
        "ventas_netas": ventas_netas,
        "base_imponible": base_imponible,
        "igv": igv,
        "porcentaje_igv": porcentaje_igv,
        "pedidos": pedidos,
    }


# ─── ADM-02: Descuentos y anulaciones (anti-fraude) ─────────────────────────


def reporte_descuentos(
    session, company_id: int, desde: datetime | None = None, hasta: datetime | None = None
) -> list[dict]:
    """Pedidos con descuento > 0, agrupados por cajero: quién aplicó cuánto."""
    filters = [
        Pedido.company_id == company_id,
        Pedido.estado == EstadoPedido.COBRADO.value,
        Pedido.descuento > 0,
    ]
    if desde:
        filters.append(Pedido.cerrado_en >= desde)
    if hasta:
        filters.append(Pedido.cerrado_en < hasta)

    rows = session.exec(
        select(
            func.coalesce(Pedido.cajero_id, 0).label("cajero_id"),
            func.count(Pedido.id).label("pedidos"),
            func.sum(Pedido.descuento).label("total_descuento"),
            func.sum(Pedido.total).label("total_ventas"),
        )
        .where(*filters)
        .group_by(func.coalesce(Pedido.cajero_id, 0))
        .order_by(func.sum(Pedido.descuento).desc())
    ).all()

    if not rows:
        return []

    user_ids = [r[0] for r in rows if r[0] > 0]
    nombres: dict[int, str] = {}
    if user_ids:
        for u in session.exec(
            select(UsuarioFood).where(UsuarioFood.id.in_(user_ids))
        ).all():
            nombres[u.id or 0] = u.nombre

    return [
        {
            "cajero": nombres.get(r[0], "Sin asignar"),
            "pedidos": r[1],
            "total_descuento": _dec(r[2]),
            "total_ventas": _dec(r[3]),
            "pct_descuento": float(
                round(_dec(r[2]) / _dec(r[3]) * 100, 1) if _dec(r[3]) > 0 else 0
            ),
        }
        for r in rows
    ]


def reporte_anulaciones(
    session, company_id: int, desde: datetime | None = None, hasta: datetime | None = None
) -> list[dict]:
    """Ventas anuladas con detalle: quién anuló, cuándo, motivo, monto."""
    filters = [
        Pedido.company_id == company_id,
        Pedido.estado == EstadoPedido.CANCELADO.value,
        Pedido.cancelado_en.isnot(None),
    ]
    if desde:
        filters.append(Pedido.cancelado_en >= desde)
    if hasta:
        filters.append(Pedido.cancelado_en < hasta)

    pedidos = session.exec(
        select(Pedido).where(*filters).order_by(Pedido.cancelado_en.desc())
    ).all()

    if not pedidos:
        return []

    user_ids = set()
    for p in pedidos:
        if p.cancelado_por_id:
            user_ids.add(p.cancelado_por_id)
        if p.cajero_id:
            user_ids.add(p.cajero_id)
    nombres: dict[int, str] = {}
    if user_ids:
        for u in session.exec(
            select(UsuarioFood).where(UsuarioFood.id.in_(list(user_ids)))
        ).all():
            nombres[u.id or 0] = u.nombre

    return [
        {
            "pedido_id": p.id or 0,
            "total": _dec(p.total),
            "motivo": p.motivo_cancelacion or "Sin motivo",
            "cancelado_por": nombres.get(p.cancelado_por_id or 0, "Sistema"),
            "cancelado_en": p.cancelado_en,
            "cajero_original": nombres.get(p.cajero_id or 0, "Sin asignar"),
        }
        for p in pedidos
    ]


def reporte_reversiones(
    session, company_id: int, desde: datetime | None = None, hasta: datetime | None = None
) -> list[dict]:
    """Cobros revertidos con motivo, extraídos de la tabla de auditoría."""
    filters = [
        Auditoria.company_id == company_id,
        Auditoria.accion == "revertir_cobro",
    ]
    if desde:
        filters.append(Auditoria.created_at >= desde)
    if hasta:
        filters.append(Auditoria.created_at < hasta)

    registros = session.exec(
        select(Auditoria).where(*filters).order_by(Auditoria.created_at.desc())
    ).all()
    if not registros:
        return []

    user_ids = {r.usuario_id for r in registros if r.usuario_id}
    nombres: dict[int, str] = {}
    if user_ids:
        for u in session.exec(
            select(UsuarioFood).where(UsuarioFood.id.in_(list(user_ids)))
        ).all():
            nombres[u.id or 0] = u.nombre

    result = []
    for r in registros:
        try:
            detalle = json.loads(r.detalle) if r.detalle else {}
        except (json.JSONDecodeError, TypeError):
            detalle = {}
        result.append({
            "pedido_id": r.entidad_id or 0,
            "total": _dec(detalle.get("total", 0)),
            "motivo": detalle.get("motivo", "Sin motivo"),
            "revertido_por": nombres.get(r.usuario_id or 0, "Sistema"),
            "revertido_en": r.created_at,
        })
    return result


# ─── ADM-03: Mermas valorizado ──────────────────────────────────────────────


def reporte_mermas(
    session, company_id: int, desde: datetime | None = None, hasta: datetime | None = None
) -> dict:
    """Mermas del kardex valorizado: S/ perdidos por categoría y por insumo.

    El motivo del kardex de mermas contiene la categoría (Vencido, Dañado, etc.).
    """
    filters = [
        MovimientoInsumo.company_id == company_id,
        MovimientoInsumo.tipo == TipoMovimientoInsumo.MERMA.value,
    ]
    if desde:
        filters.append(MovimientoInsumo.created_at >= desde)
    if hasta:
        filters.append(MovimientoInsumo.created_at < hasta)

    movimientos = session.exec(
        select(MovimientoInsumo).where(*filters).order_by(MovimientoInsumo.created_at.desc())
    ).all()

    if not movimientos:
        return {"por_categoria": [], "por_insumo": [], "total": Decimal("0.00")}

    insumo_ids = list({m.insumo_id for m in movimientos})
    insumos = {
        i.id: i
        for i in session.exec(
            select(Insumo).where(Insumo.id.in_(insumo_ids))
        ).all()
    }

    por_cat: dict[str, dict] = {}
    por_insumo: dict[int, dict] = {}
    total = Decimal("0.00")

    for m in movimientos:
        insumo = insumos.get(m.insumo_id)
        if insumo is None:
            continue
        cantidad_abs = abs(_dec(m.cantidad))
        costo = _dec(insumo.costo_unitario)
        valor = (cantidad_abs * costo).quantize(Decimal("0.01"))
        total += valor

        cat = (m.motivo or "Otro").strip()
        if cat not in por_cat:
            por_cat[cat] = {"categoria": cat, "cantidad_total": Decimal("0.000"), "valor": Decimal("0.00"), "registros": 0}
        por_cat[cat]["cantidad_total"] += cantidad_abs
        por_cat[cat]["valor"] += valor
        por_cat[cat]["registros"] += 1

        iid = m.insumo_id
        if iid not in por_insumo:
            por_insumo[iid] = {
                "nombre": insumo.nombre,
                "unidad": insumo.unidad,
                "cantidad_total": Decimal("0.000"),
                "valor": Decimal("0.00"),
                "registros": 0,
            }
        por_insumo[iid]["cantidad_total"] += cantidad_abs
        por_insumo[iid]["valor"] += valor
        por_insumo[iid]["registros"] += 1

    return {
        "por_categoria": sorted(por_cat.values(), key=lambda x: x["valor"], reverse=True),
        "por_insumo": sorted(por_insumo.values(), key=lambda x: x["valor"], reverse=True),
        "total": total.quantize(Decimal("0.01")),
    }
