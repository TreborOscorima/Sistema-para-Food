"""Tests del planificador de producción — explosión de insumos para N platos."""
from __future__ import annotations

from decimal import Decimal

import pytest
from sqlmodel import Session, SQLModel, create_engine

import app.models  # noqa: F401
from app.models.food import Insumo, Producto, Categoria, RecetaItem, Combo, ComboItem
from app.services.produccion_service import (
    costo_total_plan,
    explosionar_insumos,
    faltantes_plan,
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


def _setup_arroz_con_pollo(session):
    cat = Categoria(company_id=1, nombre="Platos")
    session.add(cat)
    session.flush()

    prod = Producto(company_id=1, categoria_id=cat.id, nombre="Arroz con pollo", precio=Decimal("25.00"))
    session.add(prod)
    session.flush()

    arroz = Insumo(company_id=1, nombre="Arroz", unidad="kg", stock_actual=Decimal("5.000"), costo_unitario=Decimal("3.50"))
    pollo = Insumo(company_id=1, nombre="Pollo", unidad="kg", stock_actual=Decimal("2.000"), costo_unitario=Decimal("12.00"))
    aceite = Insumo(company_id=1, nombre="Aceite", unidad="lt", stock_actual=Decimal("10.000"), costo_unitario=Decimal("5.00"))
    session.add_all([arroz, pollo, aceite])
    session.flush()

    session.add(RecetaItem(company_id=1, producto_id=prod.id, insumo_id=arroz.id, cantidad=Decimal("0.150")))
    session.add(RecetaItem(company_id=1, producto_id=prod.id, insumo_id=pollo.id, cantidad=Decimal("0.250")))
    session.add(RecetaItem(company_id=1, producto_id=prod.id, insumo_id=aceite.id, cantidad=Decimal("0.030")))
    session.flush()

    return prod, arroz, pollo, aceite


def test_explosion_basica(db_engine):
    with Session(db_engine) as session:
        with tenant_context(1, None):
            prod, arroz, pollo, aceite = _setup_arroz_con_pollo(session)

            result = explosionar_insumos(session, 1, [(prod.id, 20)])

            assert len(result) == 3
            by_name = {r.nombre: r for r in result}

            assert by_name["Arroz"].cantidad_necesaria == Decimal("3.000")
            assert by_name["Pollo"].cantidad_necesaria == Decimal("5.000")
            assert by_name["Aceite"].cantidad_necesaria == Decimal("0.600")

            assert by_name["Arroz"].faltante == Decimal("0")
            assert by_name["Pollo"].faltante == Decimal("3.000")
            assert by_name["Aceite"].faltante == Decimal("0")


def test_costo_total(db_engine):
    with Session(db_engine) as session:
        with tenant_context(1, None):
            prod, *_ = _setup_arroz_con_pollo(session)
            result = explosionar_insumos(session, 1, [(prod.id, 20)])

            total = costo_total_plan(result)
            # 3kg×3.50 + 5kg×12.00 + 0.6lt×5.00 = 10.50 + 60.00 + 3.00 = 73.50
            assert total == Decimal("73.50")


def test_faltantes(db_engine):
    with Session(db_engine) as session:
        with tenant_context(1, None):
            prod, *_ = _setup_arroz_con_pollo(session)
            result = explosionar_insumos(session, 1, [(prod.id, 20)])
            faltan = faltantes_plan(result)
            assert len(faltan) == 1
            assert faltan[0].nombre == "Pollo"


def test_plan_vacio(db_engine):
    with Session(db_engine) as session:
        with tenant_context(1, None):
            assert explosionar_insumos(session, 1, []) == []


def test_multiples_productos(db_engine):
    with Session(db_engine) as session:
        with tenant_context(1, None):
            prod, arroz, pollo, aceite = _setup_arroz_con_pollo(session)

            cat = session.get(Categoria, prod.categoria_id)
            lomo = Producto(company_id=1, categoria_id=cat.id, nombre="Lomo saltado", precio=Decimal("30.00"))
            session.add(lomo)
            session.flush()
            session.add(RecetaItem(company_id=1, producto_id=lomo.id, insumo_id=aceite.id, cantidad=Decimal("0.050")))
            session.flush()

            result = explosionar_insumos(session, 1, [(prod.id, 10), (lomo.id, 5)])
            by_name = {r.nombre: r for r in result}

            # Aceite: 10×0.030 + 5×0.050 = 0.550
            assert by_name["Aceite"].cantidad_necesaria == Decimal("0.550")


def test_combo_expansion(db_engine):
    with Session(db_engine) as session:
        with tenant_context(1, None):
            prod, arroz, pollo, aceite = _setup_arroz_con_pollo(session)

            combo = Combo(company_id=1, nombre="Combo Familiar", precio=Decimal("90.00"))
            session.add(combo)
            session.flush()
            session.add(ComboItem(combo_id=combo.id, producto_id=prod.id, cantidad=2))
            session.flush()

            # 5 combos × 2 arroz c/pollo cada uno = 10 platos
            result = explosionar_insumos(session, 1, [(combo.id, 5)])
            by_name = {r.nombre: r for r in result}

            assert by_name["Arroz"].cantidad_necesaria == Decimal("1.500")  # 10×0.150
            assert by_name["Pollo"].cantidad_necesaria == Decimal("2.500")  # 10×0.250
