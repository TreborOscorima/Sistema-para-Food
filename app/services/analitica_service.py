"""Analítica de ventas para restobar — por mozo, por franja horaria y margen por plato.

Réplica adaptada de la analítica del report_service de Sistema-de-Ventas:
- ¿Quién vende más? → ranking de mozos del período.
- ¿A qué hora conviene el happy hour? → ventas por hora local.
- ¿Qué plato deja margen? → precio de carta vs costo de receta (insumos).
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

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
    return Decimal(str(value)).quantize(Decimal("0.01"))


def _pedidos_cobrados(session, company_id: int, desde: datetime | None, hasta: datetime | None):
    query = select(Pedido).where(
        Pedido.company_id == company_id,
        Pedido.estado == EstadoPedido.COBRADO.value,
    )
    if desde is not None:
        query = query.where(Pedido.cerrado_en >= desde)
    if hasta is not None:
        query = query.where(Pedido.cerrado_en <= hasta)
    return session.exec(query).all()


def ventas_por_mozo(
    session, company_id: int, desde: datetime | None = None, hasta: datetime | None = None
) -> list[dict]:
    """Ranking de mozos: pedidos atendidos, total vendido y propinas del período.

    Los pedidos de mostrador (sin mozo) se agrupan como 'Mostrador'.
    """
    pedidos = _pedidos_cobrados(session, company_id, desde, hasta)
    usuarios = {
        u.id: u.nombre
        for u in session.exec(
            select(UsuarioFood).where(UsuarioFood.company_id == company_id)
        ).all()
    }
    acumulado: dict[int, dict] = {}
    for p in pedidos:
        clave = p.mozo_id or 0
        fila = acumulado.setdefault(clave, {
            "nombre": usuarios.get(clave, "Mostrador"),
            "pedidos": 0,
            "total": Decimal("0.00"),
            "propinas": Decimal("0.00"),
        })
        fila["pedidos"] += 1
        fila["total"] += _dec(p.total) - _dec(p.descuento)
        fila["propinas"] += _dec(p.propina)
    return sorted(acumulado.values(), key=lambda f: f["total"], reverse=True)


def ventas_por_hora(
    session, company_id: int, desde: datetime | None = None, hasta: datetime | None = None
) -> list[dict]:
    """Ventas agrupadas por hora local (solo horas con actividad)."""
    pedidos = _pedidos_cobrados(session, company_id, desde, hasta)
    buckets: dict[int, dict] = {}
    for p in pedidos:
        if p.cerrado_en is None:
            continue
        local = to_local_datetime(p.cerrado_en, "PE")
        hora = (local or p.cerrado_en).hour
        fila = buckets.setdefault(hora, {"hora": hora, "pedidos": 0, "total": Decimal("0.00")})
        fila["pedidos"] += 1
        fila["total"] += _dec(p.total) - _dec(p.descuento)
    return [buckets[h] for h in sorted(buckets)]


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
