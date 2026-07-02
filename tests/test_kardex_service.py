"""Tests del kardex de insumos — entradas, mermas, ajustes y saldo por fila."""
from __future__ import annotations

from decimal import Decimal

import pytest
from sqlmodel import Session, SQLModel, create_engine, select

import app.models  # noqa: F401
from app.models.food import Insumo, MovimientoInsumo, TipoMovimientoInsumo
from app.services.kardex_service import (
    registrar_ajuste,
    registrar_consumo,
    registrar_entrada,
    registrar_merma,
)
from app.utils.tenant import (
    _refresh_tenant_models,
    register_tenant_listeners,
    set_tenant_context,
    tenant_context,
)


@pytest.fixture(autouse=True)
def _clean_tenant_context():
    yield
    set_tenant_context(None, None)


@pytest.fixture()
def db_engine():
    register_tenant_listeners()
    _refresh_tenant_models()
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    return engine


def _insumo(session, stock: str = "10.000") -> Insumo:
    ins = Insumo(company_id=1, nombre="Papa", unidad="kg", stock_actual=Decimal(stock))
    session.add(ins)
    session.flush()
    return ins


def test_entrada_merma_y_saldos(db_engine):
    with Session(db_engine) as session:
        with tenant_context(1, None):
            ins = _insumo(session, "10.000")
            registrar_entrada(session, ins, None, Decimal("5.000"), "Compra mercado")
            assert ins.stock_actual == Decimal("15.000")
            registrar_merma(session, ins, None, Decimal("2.000"), "Vencido")
            assert ins.stock_actual == Decimal("13.000")
            session.commit()

            movs = session.exec(
                select(MovimientoInsumo).where(MovimientoInsumo.insumo_id == ins.id)
                .order_by(MovimientoInsumo.id)
            ).all()
            assert [m.tipo for m in movs] == [
                TipoMovimientoInsumo.ENTRADA.value, TipoMovimientoInsumo.MERMA.value,
            ]
            assert movs[0].cantidad == Decimal("5.000")
            assert movs[0].stock_resultante == Decimal("15.000")
            assert movs[1].cantidad == Decimal("-2.000")
            assert movs[1].stock_resultante == Decimal("13.000")


def test_merma_validaciones(db_engine):
    with Session(db_engine) as session:
        with tenant_context(1, None):
            ins = _insumo(session, "3.000")
            with pytest.raises(ValueError, match="motivo"):
                registrar_merma(session, ins, None, Decimal("1.000"), "  ")
            with pytest.raises(ValueError, match="superar el stock"):
                registrar_merma(session, ins, None, Decimal("5.000"), "Dañado")
            with pytest.raises(ValueError, match="mayor a cero"):
                registrar_merma(session, ins, None, Decimal("0"), "Dañado")


def test_ajuste_registra_diferencia_y_omite_sin_cambio(db_engine):
    with Session(db_engine) as session:
        with tenant_context(1, None):
            ins = _insumo(session, "10.000")
            # Conteo físico encontró 8.5 → ajuste de -1.5
            mov = registrar_ajuste(session, ins, None, Decimal("8.500"), "Conteo semanal")
            assert mov is not None
            assert mov.cantidad == Decimal("-1.500")
            assert ins.stock_actual == Decimal("8.500")
            # Mismo conteo otra vez → sin diferencia, no ensucia el kardex
            assert registrar_ajuste(session, ins, None, Decimal("8.500")) is None


def test_consumo_clampa_en_cero_y_registra_lo_aplicado(db_engine):
    with Session(db_engine) as session:
        with tenant_context(1, None):
            ins = _insumo(session, "1.000")
            mov = registrar_consumo(session, ins, Decimal("3.000"), pedido_id=None)
            # Solo había 1.0: el kardex refleja lo que realmente salió
            assert ins.stock_actual == Decimal("0.000")
            assert mov.cantidad == Decimal("-1.000")
            assert mov.tipo == TipoMovimientoInsumo.CONSUMO.value
