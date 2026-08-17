"""Analítica de ventas para restobar — por mozo, por franja horaria y margen por plato.

Todas las agregaciones se ejecutan en SQL (no en Python) para escalar con
meses de historial sin saturar memoria ni bloquear el event loop.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy import func, case
from sqlmodel import select

from tuwayki_core.utils.timezone import country_now, to_local_datetime


def _country_offset(country_code: str) -> tuple[str, int]:
    """Offset UTC del país como ('+HH:MM', horas_int) para CONVERT_TZ / strftime.

    Usa el offset vigente del país (aprox. para rangos que cruzan DST; suficiente
    para un histograma por hora). Cae a UTC-5 (Perú) si no se puede resolver.
    """
    try:
        off = country_now(country_code).utcoffset() or timedelta(hours=-5)
    except Exception:
        off = timedelta(hours=-5)
    total = int(off.total_seconds())
    sign = "+" if total >= 0 else "-"
    total = abs(total)
    h, m = total // 3600, (total % 3600) // 60
    return f"{sign}{h:02d}:{m:02d}", int(off.total_seconds() // 3600)

from app.models.food import (
    DetallePedido,
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
        filters.append(Pedido.cerrado_en < hasta)
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
    session, company_id: int, desde: datetime | None = None,
    hasta: datetime | None = None, country_code: str = "PE",
) -> list[dict]:
    """Ventas agrupadas por hora local del país — extracción de hora en SQL.

    Convierte cerrado_en (UTC) al offset del país antes de extraer la hora, para
    que el histograma refleje la hora local real (Perú UTC-5, Argentina UTC-3…).
    """
    filters = _cobrado_filters(company_id, desde, hasta)
    filters.append(Pedido.cerrado_en.isnot(None))

    offset_str, offset_h = _country_offset(country_code)
    dialect = session.bind.dialect.name if session.bind else "mysql"
    if dialect == "sqlite":
        # strftime returns text; cast to int for grouping consistency
        hora_local = func.cast(
            func.strftime("%H", Pedido.cerrado_en, f"{offset_h} hours"), sa.Integer
        ).label("hora")
    else:
        hora_local = func.hour(
            func.convert_tz(Pedido.cerrado_en, "+00:00", offset_str)
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


def matriz_estrella_perro(
    session, company_id: int,
    desde: datetime | None = None, hasta: datetime | None = None,
) -> list[dict]:
    """Matriz BCG adaptada a restaurante: unidades vendidas × margen %.

    Clasificación:
    - estrella: alta venta + alto margen
    - vaca: alta venta + bajo margen
    - puzzle: baja venta + alto margen
    - perro: baja venta + bajo margen

    Los umbrales son las medianas del dataset.
    """
    filters = _cobrado_filters(company_id, desde, hasta)
    pedido_ids_rows = session.exec(
        select(Pedido.id).where(*filters)
    ).all()
    if not pedido_ids_rows:
        return []
    pedido_ids = [r for r in pedido_ids_rows]

    rows = session.exec(
        select(
            DetallePedido.producto_id,
            func.sum(DetallePedido.cantidad).label("unidades"),
            func.sum(DetallePedido.subtotal).label("ingreso"),
        )
        .where(DetallePedido.pedido_id.in_(pedido_ids))
        .group_by(DetallePedido.producto_id)
    ).all()
    if not rows:
        return []

    ventas_map: dict[int, dict] = {}
    for r in rows:
        ventas_map[r[0]] = {"unidades": int(r[1]), "ingreso": _dec(r[2])}

    productos = {
        p.id: p for p in session.exec(
            select(Producto).where(Producto.company_id == company_id)
        ).all()
    }
    recetas = session.exec(
        select(RecetaItem).where(RecetaItem.company_id == company_id)
    ).all()
    insumos = {
        i.id: i for i in session.exec(
            select(Insumo).where(Insumo.company_id == company_id)
        ).all()
    }
    receta_por_prod: dict[int, list[RecetaItem]] = {}
    for r in recetas:
        receta_por_prod.setdefault(r.producto_id, []).append(r)

    filas: list[dict] = []
    for pid, vdata in ventas_map.items():
        prod = productos.get(pid)
        if prod is None:
            continue
        precio = _dec(prod.precio)
        items = receta_por_prod.get(pid, [])
        costo = Decimal("0.00")
        for item in items:
            ins = insumos.get(item.insumo_id)
            if ins:
                costo += _dec(ins.costo_unitario) * Decimal(str(item.cantidad))
        costo = costo.quantize(Decimal("0.01"))
        margen = precio - costo
        margen_pct = float(margen / precio * 100) if precio > 0 else 0.0
        filas.append({
            "producto_id": pid,
            "nombre": prod.nombre,
            "unidades": vdata["unidades"],
            "ingreso": vdata["ingreso"],
            "precio": precio,
            "costo": costo,
            "margen_pct": round(margen_pct, 1),
            "categoria": "",
        })

    if not filas:
        return []

    unidades_list = sorted(f["unidades"] for f in filas)
    margen_list = sorted(f["margen_pct"] for f in filas)
    med_unidades = unidades_list[len(unidades_list) // 2]
    med_margen = margen_list[len(margen_list) // 2]

    for f in filas:
        alta_venta = f["unidades"] >= med_unidades
        alto_margen = f["margen_pct"] >= med_margen
        if alta_venta and alto_margen:
            f["categoria"] = "estrella"
        elif alta_venta and not alto_margen:
            f["categoria"] = "vaca"
        elif not alta_venta and alto_margen:
            f["categoria"] = "puzzle"
        else:
            f["categoria"] = "perro"

    return sorted(filas, key=lambda f: (-f["unidades"], -f["margen_pct"]))
