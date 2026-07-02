"""Motor de promociones — vigencia por día/hora local y descuento por tipo.

Réplica adaptada del engine de promociones de Sistema-de-Ventas:
- Vigencia: día de la semana (bitmask lunes=1 ... domingo=64) + franja horaria
  en hora local del país (soporta franjas que cruzan medianoche).
- Alcance: toda la carta, una categoría o un producto puntual.
- Tipos: porcentaje, monto fijo, happy hour (porcentaje con franja) y 2x1.
- Se aplica automáticamente la mejor promo (mayor descuento) al abrir el cobro.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from tuwayki_core.utils.timezone import to_local_datetime, utc_now_naive

from app.models.food import Promocion, TipoPromocion

DIAS_SEMANA = [
    ("lun", "Lunes", 1),
    ("mar", "Martes", 2),
    ("mie", "Miércoles", 4),
    ("jue", "Jueves", 8),
    ("vie", "Viernes", 16),
    ("sab", "Sábado", 32),
    ("dom", "Domingo", 64),
]
MASK_TODOS_LOS_DIAS = 127


@dataclass(slots=True)
class ItemCobro:
    """Ítem del pedido visto por el motor de promos."""

    producto_id: int
    categoria_id: int
    cantidad: int
    precio_unitario: Decimal


def _dec(value) -> Decimal:
    if isinstance(value, Decimal):
        return value.quantize(Decimal("0.01"))
    return Decimal(str(value)).quantize(Decimal("0.01"))


def ahora_local_pe(referencia: datetime | None = None) -> datetime:
    """Hora local de Perú (naive) — las franjas de promos se configuran en local."""
    local = to_local_datetime(referencia or utc_now_naive(), "PE")
    return local.replace(tzinfo=None) if local else utc_now_naive()


def promo_vigente(promo: Promocion, ahora_local: datetime) -> bool:
    """¿La promo aplica en este momento? (activa + día de semana + franja horaria)."""
    if not promo.activa:
        return False
    mask = promo.dias_semana_mask if promo.dias_semana_mask else MASK_TODOS_LOS_DIAS
    if not mask & (1 << ahora_local.weekday()):
        return False
    if promo.hora_inicio and promo.hora_fin:
        hora_actual = ahora_local.strftime("%H:%M")
        if promo.hora_inicio <= promo.hora_fin:
            return promo.hora_inicio <= hora_actual <= promo.hora_fin
        # La franja cruza medianoche (ej. 22:00 → 02:00)
        return hora_actual >= promo.hora_inicio or hora_actual <= promo.hora_fin
    return True


def _items_en_alcance(promo: Promocion, items: list[ItemCobro]) -> list[ItemCobro]:
    if promo.producto_id:
        return [i for i in items if i.producto_id == promo.producto_id]
    if promo.categoria_id:
        return [i for i in items if i.categoria_id == promo.categoria_id]
    return list(items)


def calcular_descuento(promo: Promocion, items: list[ItemCobro]) -> Decimal:
    """Descuento en soles que produce la promo sobre los ítems del pedido."""
    alcance = _items_en_alcance(promo, items)
    if not alcance:
        return Decimal("0.00")
    base = sum((_dec(i.precio_unitario) * i.cantidad for i in alcance), Decimal("0.00"))
    if base <= 0:
        return Decimal("0.00")
    valor = _dec(promo.valor)
    if promo.tipo in (TipoPromocion.PORCENTAJE.value, TipoPromocion.HAPPY_HOUR.value):
        descuento = (base * valor / Decimal("100")).quantize(Decimal("0.01"))
    elif promo.tipo == TipoPromocion.MONTO_FIJO.value:
        descuento = valor
    elif promo.tipo == TipoPromocion.DOSXUNO.value:
        # Por cada 2 unidades del mismo producto, una es gratis
        descuento = Decimal("0.00")
        por_producto: dict[int, ItemCobro] = {}
        for item in alcance:
            previo = por_producto.get(item.producto_id)
            if previo is None:
                por_producto[item.producto_id] = ItemCobro(
                    producto_id=item.producto_id,
                    categoria_id=item.categoria_id,
                    cantidad=item.cantidad,
                    precio_unitario=item.precio_unitario,
                )
            else:
                previo.cantidad += item.cantidad
        for agrupado in por_producto.values():
            gratis = agrupado.cantidad // 2
            descuento += _dec(agrupado.precio_unitario) * gratis
    else:
        return Decimal("0.00")
    return min(descuento, base)


def mejor_promo(
    promos: list[Promocion],
    items: list[ItemCobro],
    ahora_local: datetime,
    solo_auto: bool = True,
) -> tuple[Promocion, Decimal] | None:
    """La promo vigente con mayor descuento para este pedido (no se acumulan)."""
    mejor: tuple[Promocion, Decimal] | None = None
    for promo in promos:
        if solo_auto and not promo.auto_aplicar:
            continue
        if not promo_vigente(promo, ahora_local):
            continue
        descuento = calcular_descuento(promo, items)
        if descuento <= 0:
            continue
        if mejor is None or descuento > mejor[1]:
            mejor = (promo, descuento)
    return mejor
