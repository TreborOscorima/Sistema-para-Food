"""Tests de _descontar_stock_por_pedido — descuento de insumos al cobrar."""
from __future__ import annotations

import json
from decimal import Decimal

import pytest
from sqlmodel import Session, SQLModel, create_engine, select

import app.models  # noqa: F401
from app.models.food import (
    Categoria,
    DetallePedido,
    Insumo,
    MovimientoInsumo,
    Pedido,
    Producto,
    RecetaItem,
)
from app.states.food_state import _descontar_stock_por_pedido
from app.utils.tenant import (
    _refresh_tenant_models,
    register_tenant_listeners,
    set_tenant_context,
    tenant_context,
)

COMPANY = 1


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


def _setup_base(session: Session):
    cat = Categoria(company_id=COMPANY, nombre="Platos")
    session.add(cat)
    session.flush()
    return cat


def _producto(session, cat_id: int, nombre: str, precio: str = "10.00") -> Producto:
    p = Producto(
        company_id=COMPANY,
        categoria_id=cat_id,
        nombre=nombre,
        precio=Decimal(precio),
    )
    session.add(p)
    session.flush()
    return p


def _insumo(session, nombre: str, stock: str = "10.000") -> Insumo:
    ins = Insumo(
        company_id=COMPANY, nombre=nombre, unidad="kg",
        stock_actual=Decimal(stock),
    )
    session.add(ins)
    session.flush()
    return ins


def _receta(session, producto_id: int, insumo_id: int, cantidad: str) -> RecetaItem:
    r = RecetaItem(
        company_id=COMPANY,
        producto_id=producto_id,
        insumo_id=insumo_id,
        cantidad=Decimal(cantidad),
    )
    session.add(r)
    session.flush()
    return r


def _pedido(session) -> Pedido:
    p = Pedido(company_id=COMPANY, tipo_pedido="mesa")
    session.add(p)
    session.flush()
    return p


def _detalle(
    session, pedido_id: int, producto_id: int, cantidad: int = 1,
    combo_items_json: str | None = None,
) -> DetallePedido:
    d = DetallePedido(
        company_id=COMPANY,
        pedido_id=pedido_id,
        producto_id=producto_id,
        cantidad=cantidad,
        precio_unitario=Decimal("10.00"),
        subtotal=Decimal(str(10 * cantidad)),
        combo_items_json=combo_items_json,
    )
    session.add(d)
    session.flush()
    return d


# ─── Tests ────────────────────────────────────────────────────────────────────


def test_producto_simple_descuenta_stock(db_engine):
    with Session(db_engine) as session:
        with tenant_context(COMPANY, None):
            cat = _setup_base(session)
            pollo = _producto(session, cat.id, "Pollo a la brasa")
            ins_pollo = _insumo(session, "Pollo entero", "5.000")
            ins_papa = _insumo(session, "Papa", "20.000")
            _receta(session, pollo.id, ins_pollo.id, "0.500")
            _receta(session, pollo.id, ins_papa.id, "0.300")
            pedido = _pedido(session)
            _detalle(session, pedido.id, pollo.id, cantidad=2)
            session.flush()

            _descontar_stock_por_pedido(session, pedido.id, COMPANY)
            session.flush()

            assert ins_pollo.stock_actual == Decimal("4.000")
            assert ins_papa.stock_actual == Decimal("19.400")

            movs = session.exec(select(MovimientoInsumo)).all()
            assert len(movs) == 2


def test_producto_sin_receta_no_afecta_stock(db_engine):
    with Session(db_engine) as session:
        with tenant_context(COMPANY, None):
            cat = _setup_base(session)
            agua = _producto(session, cat.id, "Agua")
            pedido = _pedido(session)
            _detalle(session, pedido.id, agua.id, cantidad=3)
            session.flush()

            _descontar_stock_por_pedido(session, pedido.id, COMPANY)

            movs = session.exec(select(MovimientoInsumo)).all()
            assert len(movs) == 0


def test_combo_descuenta_sub_productos(db_engine):
    with Session(db_engine) as session:
        with tenant_context(COMPANY, None):
            cat = _setup_base(session)
            combo = _producto(session, cat.id, "Combo familiar", "50.00")
            hamburguesa = _producto(session, cat.id, "Hamburguesa", "15.00")
            papas_fritas = _producto(session, cat.id, "Papas fritas", "8.00")

            ins_carne = _insumo(session, "Carne molida", "10.000")
            ins_papa = _insumo(session, "Papa", "20.000")
            ins_aceite = _insumo(session, "Aceite", "5.000")

            _receta(session, hamburguesa.id, ins_carne.id, "0.200")
            _receta(session, papas_fritas.id, ins_papa.id, "0.400")
            _receta(session, papas_fritas.id, ins_aceite.id, "0.050")

            pedido = _pedido(session)
            combo_items = json.dumps([
                {"producto_id": hamburguesa.id, "cantidad": 2},
                {"producto_id": papas_fritas.id, "cantidad": 1},
            ])
            _detalle(session, pedido.id, combo.id, cantidad=1,
                     combo_items_json=combo_items)
            session.flush()

            _descontar_stock_por_pedido(session, pedido.id, COMPANY)
            session.flush()

            assert ins_carne.stock_actual == Decimal("9.600")
            assert ins_papa.stock_actual == Decimal("19.600")
            assert ins_aceite.stock_actual == Decimal("4.950")


def test_combo_cantidad_mayor_a_uno(db_engine):
    """2 combos, cada uno con 1 hamburguesa → 2x descuento."""
    with Session(db_engine) as session:
        with tenant_context(COMPANY, None):
            cat = _setup_base(session)
            combo = _producto(session, cat.id, "Combo x2")
            burger = _producto(session, cat.id, "Burger")
            ins = _insumo(session, "Carne", "10.000")
            _receta(session, burger.id, ins.id, "0.250")

            pedido = _pedido(session)
            combo_items = json.dumps([
                {"producto_id": burger.id, "cantidad": 1},
            ])
            _detalle(session, pedido.id, combo.id, cantidad=2,
                     combo_items_json=combo_items)
            session.flush()

            _descontar_stock_por_pedido(session, pedido.id, COMPANY)
            session.flush()

            assert ins.stock_actual == Decimal("9.500")


def test_pedido_mixto_simple_y_combo(db_engine):
    """Pedido con un producto simple + un combo en la misma orden."""
    with Session(db_engine) as session:
        with tenant_context(COMPANY, None):
            cat = _setup_base(session)
            arroz = _producto(session, cat.id, "Arroz con pollo")
            combo = _producto(session, cat.id, "Combo")
            sub_item = _producto(session, cat.id, "Ensalada")

            ins_arroz = _insumo(session, "Arroz", "15.000")
            ins_lechuga = _insumo(session, "Lechuga", "8.000")

            _receta(session, arroz.id, ins_arroz.id, "0.300")
            _receta(session, sub_item.id, ins_lechuga.id, "0.150")

            pedido = _pedido(session)
            _detalle(session, pedido.id, arroz.id, cantidad=3)
            _detalle(session, pedido.id, combo.id, cantidad=1,
                     combo_items_json=json.dumps([
                         {"producto_id": sub_item.id, "cantidad": 2},
                     ]))
            session.flush()

            _descontar_stock_por_pedido(session, pedido.id, COMPANY)
            session.flush()

            assert ins_arroz.stock_actual == Decimal("14.100")
            assert ins_lechuga.stock_actual == Decimal("7.700")


def test_pedido_vacio_no_falla(db_engine):
    with Session(db_engine) as session:
        with tenant_context(COMPANY, None):
            pedido = _pedido(session)
            session.flush()
            _descontar_stock_por_pedido(session, pedido.id, COMPANY)
            movs = session.exec(select(MovimientoInsumo)).all()
            assert len(movs) == 0
