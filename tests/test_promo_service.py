"""Tests del motor de promociones — vigencia local, alcance, tipos y mejor promo."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from app.models.food import Promocion, TipoPromocion
from app.services.promo_service import (
    ItemCobro,
    calcular_descuento,
    mejor_promo,
    promo_vigente,
)

# Lunes 2026-07-06 a las 19:00 (hora local)
LUNES_19 = datetime(2026, 7, 6, 19, 0)
# Sábado 2026-07-04 a la 01:00 (madrugada)
SABADO_01 = datetime(2026, 7, 4, 1, 0)


def _promo(**kwargs) -> Promocion:
    base = dict(
        company_id=1, nombre="Promo", tipo=TipoPromocion.PORCENTAJE.value,
        valor=Decimal("10.00"), activa=True, dias_semana_mask=127, auto_aplicar=True,
    )
    base.update(kwargs)
    return Promocion(**base)


def _items() -> list[ItemCobro]:
    return [
        ItemCobro(producto_id=1, categoria_id=10, cantidad=3, precio_unitario=Decimal("20.00")),  # 60
        ItemCobro(producto_id=2, categoria_id=20, cantidad=1, precio_unitario=Decimal("40.00")),  # 40
    ]


# ─── Vigencia ─────────────────────────────────────────────────────────────────

def test_vigencia_por_dia_de_semana():
    solo_martes = _promo(dias_semana_mask=2)  # martes = bit 2
    assert not promo_vigente(solo_martes, LUNES_19)
    solo_lunes = _promo(dias_semana_mask=1)
    assert promo_vigente(solo_lunes, LUNES_19)


def test_franja_horaria_que_cruza_medianoche():
    nocturna = _promo(hora_inicio="22:00", hora_fin="02:00")
    assert promo_vigente(nocturna, SABADO_01)      # 01:00 está dentro
    assert not promo_vigente(nocturna, LUNES_19)   # 19:00 está fuera


def test_promo_inactiva_no_aplica():
    assert not promo_vigente(_promo(activa=False), LUNES_19)


# ─── Descuentos ───────────────────────────────────────────────────────────────

def test_porcentaje_global_y_por_categoria():
    global_10 = _promo(valor=Decimal("10.00"))
    assert calcular_descuento(global_10, _items()) == Decimal("10.00")  # 10% de 100
    solo_cat10 = _promo(valor=Decimal("50.00"), categoria_id=10)
    assert calcular_descuento(solo_cat10, _items()) == Decimal("30.00")  # 50% de 60


def test_monto_fijo_no_supera_la_base():
    fijo = _promo(tipo=TipoPromocion.MONTO_FIJO.value, valor=Decimal("500.00"), producto_id=2)
    assert calcular_descuento(fijo, _items()) == Decimal("40.00")  # tope: subtotal del scope


def test_dosxuno_por_producto():
    # 3 unidades del producto 1 → 1 gratis (20.00)
    dos_por_uno = _promo(tipo=TipoPromocion.DOSXUNO.value, valor=Decimal("0"), producto_id=1)
    assert calcular_descuento(dos_por_uno, _items()) == Decimal("20.00")
    # 4 unidades → 2 gratis
    items4 = [ItemCobro(producto_id=1, categoria_id=10, cantidad=4, precio_unitario=Decimal("20.00"))]
    assert calcular_descuento(dos_por_uno, items4) == Decimal("40.00")
    # 1 unidad → nada
    items1 = [ItemCobro(producto_id=1, categoria_id=10, cantidad=1, precio_unitario=Decimal("20.00"))]
    assert calcular_descuento(dos_por_uno, items1) == Decimal("0.00")


def test_alcance_sin_items_no_descuenta():
    otro_producto = _promo(valor=Decimal("50.00"), producto_id=999)
    assert calcular_descuento(otro_producto, _items()) == Decimal("0.00")


# ─── Mejor promo ──────────────────────────────────────────────────────────────

def test_mejor_promo_elige_mayor_descuento_y_respeta_auto():
    p10 = _promo(nombre="10 global", valor=Decimal("10.00"))                    # 10.00
    p50cat = _promo(nombre="50 cat10", valor=Decimal("50.00"), categoria_id=10)  # 30.00
    manual = _promo(nombre="90 manual", valor=Decimal("90.00"), auto_aplicar=False)
    resultado = mejor_promo([p10, p50cat, manual], _items(), LUNES_19, solo_auto=True)
    assert resultado is not None
    promo, descuento = resultado
    assert promo.nombre == "50 cat10"
    assert descuento == Decimal("30.00")


def test_mejor_promo_sin_candidatas():
    assert mejor_promo([_promo(activa=False)], _items(), LUNES_19) is None
