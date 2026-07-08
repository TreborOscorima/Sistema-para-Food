"""Planificador de producción — explosión de insumos para N platos.

Dado un plan de producción [(producto_id, cantidad), ...], calcula la cantidad
total de cada insumo necesario según las recetas cargadas, comparando contra
stock actual y estimando el costo.  Expande combos a sus productos componentes.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from sqlmodel import select

from app.models.food import (
    Combo,
    ComboItem,
    Insumo,
    Producto,
    RecetaItem,
)


@dataclass
class InsumoNecesidad:
    insumo_id: int
    nombre: str
    unidad: str
    cantidad_necesaria: Decimal
    stock_actual: Decimal
    faltante: Decimal
    costo_estimado: Decimal
    costo_unitario: Decimal


def explosionar_insumos(
    session,
    company_id: int,
    plan: list[tuple[int, int]],
) -> list[InsumoNecesidad]:
    """Calcula la necesidad de insumos para un plan de producción.

    Args:
        session: sesión SQLModel activa.
        company_id: tenant.
        plan: lista de (producto_id, cantidad_a_producir).
              Un producto_id puede ser un combo — se expande automáticamente.

    Returns:
        Lista de InsumoNecesidad ordenada por nombre, con faltantes y costos.
    """
    if not plan:
        return []

    plan_ids = {pid for pid, _ in plan}

    combos_por_producto: dict[int, list[tuple[int, int]]] = {}
    combo_ids = set()
    combos = session.exec(
        select(Combo).where(Combo.company_id == company_id, Combo.activo.is_(True))
    ).all()
    for c in combos:
        if c.id in plan_ids:
            combo_ids.add(c.id)
    if combo_ids:
        combo_items = session.exec(
            select(ComboItem).where(ComboItem.combo_id.in_(list(combo_ids)))
        ).all()
        for ci in combo_items:
            combos_por_producto.setdefault(ci.combo_id, []).append(
                (ci.producto_id, ci.cantidad)
            )

    producto_cantidades: dict[int, Decimal] = {}
    for producto_id, cantidad in plan:
        if producto_id in combo_ids:
            for sub_pid, sub_cant in combos_por_producto.get(producto_id, []):
                producto_cantidades[sub_pid] = (
                    producto_cantidades.get(sub_pid, Decimal("0"))
                    + Decimal(str(sub_cant)) * Decimal(str(cantidad))
                )
        else:
            producto_cantidades[producto_id] = (
                producto_cantidades.get(producto_id, Decimal("0"))
                + Decimal(str(cantidad))
            )

    if not producto_cantidades:
        return []

    recetas = session.exec(
        select(RecetaItem).where(
            RecetaItem.company_id == company_id,
            RecetaItem.producto_id.in_(list(producto_cantidades.keys())),
        )
    ).all()

    if not recetas:
        return []

    necesidad_por_insumo: dict[int, Decimal] = {}
    for r in recetas:
        cant_plan = producto_cantidades.get(r.producto_id, Decimal("0"))
        uso = Decimal(str(r.cantidad)) * cant_plan
        necesidad_por_insumo[r.insumo_id] = (
            necesidad_por_insumo.get(r.insumo_id, Decimal("0")) + uso
        )

    insumo_ids = list(necesidad_por_insumo.keys())
    insumos = {
        i.id: i
        for i in session.exec(
            select(Insumo).where(
                Insumo.company_id == company_id,
                Insumo.id.in_(insumo_ids),
            )
        ).all()
    }

    resultado: list[InsumoNecesidad] = []
    for insumo_id, necesario in necesidad_por_insumo.items():
        insumo = insumos.get(insumo_id)
        if insumo is None:
            continue
        necesario_q = necesario.quantize(Decimal("0.001"))
        stock = insumo.stock_actual
        faltante = max(Decimal("0"), necesario_q - stock)
        costo_unit = insumo.costo_unitario or Decimal("0")
        costo_est = (necesario_q * costo_unit).quantize(Decimal("0.01"))
        resultado.append(InsumoNecesidad(
            insumo_id=insumo.id or 0,
            nombre=insumo.nombre,
            unidad=insumo.unidad,
            cantidad_necesaria=necesario_q,
            stock_actual=stock,
            faltante=faltante,
            costo_estimado=costo_est,
            costo_unitario=costo_unit,
        ))

    resultado.sort(key=lambda x: x.nombre)
    return resultado


def costo_total_plan(necesidades: list[InsumoNecesidad]) -> Decimal:
    return sum((n.costo_estimado for n in necesidades), Decimal("0.00"))


def faltantes_plan(necesidades: list[InsumoNecesidad]) -> list[InsumoNecesidad]:
    return [n for n in necesidades if n.faltante > 0]
