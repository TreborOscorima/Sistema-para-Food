"""Analítica de ventas para restobar — por mozo, por franja horaria y margen por plato.

Todas las agregaciones se ejecutan en SQL (no en Python) para escalar con
meses de historial sin saturar memoria ni bloquear el event loop.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy import func, case
from sqlmodel import select

from tuwayki_core.utils.timezone import to_local_datetime

from app.models.food import (
    EstadoPedido,
    Insumo,
    Pedido,
    Producto,
    RecetaItem,
    UsuarioFood,
)


def _dec(value) -> Decimal:
    if isinstance(value, Decimal):
        return value.quantize(Decimal("0.01"))
    return Decimal(str(value or 0)).quantize(Decimal("0.01"))


def _cobrado_filters(company_id: int, desde: datetime | None, hasta: datetime | None):
    filters = [
        Pedido.company_id == company_id,
        Pedido.estado == EstadoPedido.COBRADO.value,
    ]
    if desde is not None:
        filters.append(Pedido.cerrado_en >= desde)
    if hasta is not None:
        filters.append(Pedido.cerrado_en <= hasta)
    return filters


def ventas_por_mozo(
    session, company_id: int, desde: datetime | None = None, hasta: datetime | None = None
) -> list[dict]:
    """Ranking de mozos: pedidos atendidos, total vendido y propinas — agregado en SQL."""
    filters = _cobrado_filters(company_id, desde, hasta)
    mozo_col = func.coalesce(Pedido.mozo_id, 0).label("mozo_clave")
    rows = session.exec(
        select(
            mozo_col,
            func.count(Pedido.id).label("pedidos"),
            func.sum(Pedido.total - Pedido.descuento).label("total"),
            func.sum(Pedido.propina).label("propinas"),
        )
        .where(*filters)
        .group_by(mozo_col)
        .order_by(func.sum(Pedido.total - Pedido.descuento).desc())
    ).all()

    if not rows:
        return []

    mozo_ids = [r[0] for r in rows if r[0] > 0]
    nombres: dict[int, str] = {}
    if mozo_ids:
        for u in session.exec(
            select(UsuarioFood).where(UsuarioFood.id.in_(mozo_ids))
        ).all():
            nombres[u.id or 0] = u.nombre

    return [
        {
            "nombre": nombres.get(r[0], "Mostrador"),
            "pedidos": r[1],
            "total": _dec(r[2]),
            "propinas": _dec(r[3]),
        }
        for r in rows
    ]


def ventas_por_hora(
    session, company_id: int, desde: datetime | None = None, hasta: datetime | None = None
) -> list[dict]:
    """Ventas agrupadas por hora local — extracción de hora en SQL (MySQL HOUR).

    Usa CONVERT_TZ para hora peruana (America/Lima = UTC-5 fijo, sin DST).
    Si la función TZ de MySQL no tiene las tablas cargadas, fallback a UTC-5.
    """
    filters = _cobrado_filters(company_id, desde, hasta)
    filters.append(Pedido.cerrado_en.isnot(None))

    dialect = session.bind.dialect.name if session.bind else "mysql"
    if dialect == "sqlite":
        # strftime returns text; cast to int for grouping consistency
        hora_local = func.cast(
            func.strftime("%H", Pedido.cerrado_en, "-5 hours"), sa.Integer
        ).label("hora")
    else:
        hora_local = func.hour(
            func.convert_tz(Pedido.cerrado_en, "+00:00", "-05:00")
        ).label("hora")

    rows = session.exec(
        select(
            hora_local,
            func.count(Pedido.id).label("pedidos"),
            func.sum(Pedido.total - Pedido.descuento).label("total"),
        )
        .where(*filters)
        .group_by(hora_local)
        .order_by(hora_local)
    ).all()

    return [
        {"hora": r[0], "pedidos": r[1], "total": _dec(r[2])}
        for r in rows
    ]


def margen_por_plato(session, company_id: int) -> list[dict]:
    """Margen por producto: precio de carta menos costo de la receta.

    Solo productos con receta cargada. Si algún insumo no tiene costo, el
    margen se marca como incompleto (costo_completo=False).
    """
    productos = session.exec(
        select(Producto).where(Producto.company_id == company_id)
    ).all()
    recetas = session.exec(
        select(RecetaItem).where(RecetaItem.company_id == company_id)
    ).all()
    insumos = {
        i.id: i
        for i in session.exec(
            select(Insumo).where(Insumo.company_id == company_id)
        ).all()
    }
    receta_por_producto: dict[int, list[RecetaItem]] = {}
    for r in recetas:
        receta_por_producto.setdefault(r.producto_id, []).append(r)

    filas: list[dict] = []
    for prod in productos:
        items = receta_por_producto.get(prod.id or 0)
        if not items:
            continue
        costo = Decimal("0.00")
        costo_completo = True
        for item in items:
            insumo = insumos.get(item.insumo_id)
            if insumo is None:
                continue
            costo_unit = _dec(insumo.costo_unitario)
            if costo_unit <= 0:
                costo_completo = False
            costo += costo_unit * Decimal(str(item.cantidad))
        precio = _dec(prod.precio)
        margen = precio - costo
        margen_pct = float(margen / precio * 100) if precio > 0 else 0.0
        filas.append({
            "nombre": prod.nombre,
            "precio": precio,
            "costo": costo.quantize(Decimal("0.01")),
            "margen": margen.quantize(Decimal("0.01")),
            "margen_pct": round(margen_pct, 1),
            "costo_completo": costo_completo,
        })
    return sorted(filas, key=lambda f: f["margen_pct"])
