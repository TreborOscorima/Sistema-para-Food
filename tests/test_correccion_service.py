"""Tests de corrección de cobro — edita la misma venta, sin anular ni duplicar.

Verifica la identidad clave del arqueo (Σ pagos == Σ totales de pedidos
cobrados: sin doble venta), la reconciliación de stock por delta, la auditoría
y el manejo de fiado, ejercitando el servicio real `corregir_venta`.
"""
from __future__ import annotations

from decimal import Decimal

import pytest
from sqlmodel import Session, SQLModel, create_engine, select

import app.models  # noqa: F401  registra todos los modelos SQLModel
from app.models.food import (
    Auditoria,
    Categoria,
    Cliente,
    CuentaCorriente,
    DetallePedido,
    EstadoPedido,
    Insumo,
    MetodoPagoConfig,
    MovimientoCuenta,
    PagoPedido,
    Pedido,
    Producto,
    RecetaItem,
    TipoMetodoPago,
)
from app.services.correccion_service import LineaCorreccion, corregir_venta
from app.services.metodos_pago_service import validos_y_efectivos
from app.services.pago_service import (
    registrar_pagos_pedido,
    validar_pagos,
)
from app.states.caja_turno_mixin import abrir_turno_caja
from app.utils.tenant import (
    _refresh_tenant_models,
    register_tenant_listeners,
    set_tenant_context,
    tenant_context,
)

CO = 1


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


def _sembrar_metodos(session):
    for cod, nombre, tipo in [
        ("efectivo", "Efectivo", TipoMetodoPago.EFECTIVO.value),
        ("yape", "Yape", TipoMetodoPago.DIGITAL.value),
        ("fiado", "Fiado", TipoMetodoPago.FIADO.value),
    ]:
        session.add(MetodoPagoConfig(
            company_id=CO, codigo=cod, nombre=nombre, tipo=tipo, activo=True,
        ))
    session.flush()


def _categoria(session):
    cat = Categoria(company_id=CO, nombre="General")
    session.add(cat)
    session.flush()
    return cat


def _producto(session, nombre, precio, stock_diario=None, insumo=None, uso=None,
              categoria_id=None):
    p = Producto(company_id=CO, nombre=nombre, precio=Decimal(str(precio)),
                 stock_diario=stock_diario, categoria_id=categoria_id)
    session.add(p)
    session.flush()
    if insumo is not None and uso is not None:
        session.add(RecetaItem(company_id=CO, producto_id=p.id,
                               insumo_id=insumo.id, cantidad=Decimal(str(uso))))
        session.flush()
    return p


def _cobrar(session, turno_id, lineas, pagos):
    """Cobra un pedido nuevo por la ruta real (validar + registrar pagos)."""
    total = sum((Decimal(str(pu)) * c for _pid, pu, c in lineas), Decimal("0.00"))
    ped = Pedido(company_id=CO, turno_caja_id=turno_id, total=total,
                 estado=EstadoPedido.COBRADO.value, pagado=True)
    session.add(ped)
    session.flush()
    for pid, pu, c in lineas:
        session.add(DetallePedido(
            company_id=CO, pedido_id=ped.id, producto_id=pid,
            cantidad=c, precio_unitario=Decimal(str(pu)),
            subtotal=Decimal(str(pu)) * c,
        ))
    session.flush()
    validos, efectivos = validos_y_efectivos(session, CO)
    res = validar_pagos(total, pagos, validos, efectivos)
    registrar_pagos_pedido(session, ped, turno_id, None, pagos, res,
                           metodos_efectivo=efectivos)
    return ped


def _suma_pagos_turno(session, turno_id) -> Decimal:
    return sum(
        (Decimal(str(p.monto)) for p in session.exec(
            select(PagoPedido).where(PagoPedido.turno_caja_id == turno_id)
        ).all()),
        Decimal("0.00"),
    )


def test_correccion_no_duplica_y_audita(db_engine):
    with Session(db_engine) as session:
        with tenant_context(CO, None):
            _sembrar_metodos(session)
            cat = _categoria(session)
            insumo = Insumo(company_id=CO, nombre="Pollo",
                            stock_actual=Decimal("100"), unidad="kg")
            session.add(insumo)
            session.flush()
            broaster = _producto(session, "Broaster", 20, stock_diario=50,
                                  insumo=insumo, uso=1, categoria_id=cat.id)
            gaseosa = _producto(session, "Gaseosa", 5, stock_diario=30,
                                categoria_id=cat.id)
            turno = abrir_turno_caja(session, CO, None, Decimal("100.00"))
            session.commit()
            tid = turno.id

            # Cobro original: 2 Broaster + 1 Gaseosa = 45, todo efectivo
            ped = _cobrar(
                session, tid,
                [(broaster.id, 20, 2), (gaseosa.id, 5, 1)],
                [("efectivo", Decimal("45.00"))],
            )
            session.commit()
            ped_id = ped.id
            stock_broaster_0 = broaster.stock_diario  # 50 - 2 = 48 (al agregar)
            # nota: en este test el descuento de stock_diario del cobro no corre
            # (se hace en la UI al agregar ítems), así que fijamos base:
            broaster.stock_diario = 48
            gaseosa.stock_diario = 29
            session.add(broaster); session.add(gaseosa)
            session.commit()

            insumo_antes = insumo.stock_actual

            # Corrección: quitar la gaseosa, subir Broaster a 3, agregar Yape,
            # cambiar método a yape, aplicar descuento de 5.
            det_broaster = session.exec(
                select(DetallePedido).where(
                    DetallePedido.pedido_id == ped_id,
                    DetallePedido.producto_id == broaster.id,
                )
            ).first()
            corregir_venta(
                session, ped, tid, usuario_id=None, usuario_nombre="Tester",
                lineas=[
                    LineaCorreccion(producto_id=broaster.id, cantidad=3,
                                    precio_unitario=Decimal("20.00"),
                                    detalle_id=det_broaster.id),
                ],
                pagos=[("yape", Decimal("55.00"))],  # 60 - 5 desc = 55
                descuento=Decimal("5.00"),
                propina=Decimal("0.00"),
                recargo=Decimal("0.00"),
                recargo_concepto=None,
                cliente_id=None,
                motivo="Se cobró de más una gaseosa",
                metodos_validos={"efectivo", "yape", "fiado"},
                metodos_efectivo={"efectivo"},
            )
            session.commit()
            session.refresh(ped)

            # 1) Misma venta: mismo id, sigue COBRADO, no hay pedido nuevo
            assert ped.id == ped_id
            assert ped.estado == EstadoPedido.COBRADO.value
            assert session.exec(
                select(Pedido).where(Pedido.turno_caja_id == tid)
            ).all().__len__() == 1

            # 2) Total y método corregidos
            assert Decimal(str(ped.total)) == Decimal("60.00")   # subtotal
            assert ped.descuento == Decimal("5.00")
            assert ped.metodo_pago == "yape"

            # 3) Sin doble venta: Σ pagos == total neto (55), y una sola fila
            assert _suma_pagos_turno(session, tid) == Decimal("55.00")

            # 4) Líneas: solo Broaster x3, la gaseosa se quitó
            dets = session.exec(
                select(DetallePedido).where(DetallePedido.pedido_id == ped_id)
            ).all()
            assert len(dets) == 1
            assert dets[0].producto_id == broaster.id
            assert dets[0].cantidad == 3

            # 5) Stock insumos reconciliado por delta: repone 2 (viejo) y
            #    descuenta 3 (nuevo) => -1 respecto de antes de corregir
            session.refresh(insumo)
            assert Decimal(str(insumo.stock_actual)) == Decimal(str(insumo_antes)) - Decimal("1")

            # 6) stock_diario: gaseosa +1 (se quitó), broaster -1 (2->3)
            session.refresh(broaster); session.refresh(gaseosa)
            assert broaster.stock_diario == 47
            assert gaseosa.stock_diario == 30

            # 7) Auditoría con before/after/motivo
            aud = session.exec(
                select(Auditoria).where(Auditoria.accion == "correccion_cobro")
            ).all()
            assert len(aud) == 1
            assert "Se cobró de más" in (aud[0].detalle or "")


def test_correccion_a_fiado_carga_cuenta(db_engine):
    with Session(db_engine) as session:
        with tenant_context(CO, None):
            _sembrar_metodos(session)
            cat = _categoria(session)
            combo = _producto(session, "Combo", 30, categoria_id=cat.id)
            cliente = Cliente(company_id=CO, nombre="Juan")
            session.add(cliente)
            session.flush()
            turno = abrir_turno_caja(session, CO, None, Decimal("0.00"))
            session.commit()
            tid = turno.id

            ped = _cobrar(session, tid, [(combo.id, 30, 1)],
                          [("efectivo", Decimal("30.00"))])
            session.commit()

            det = session.exec(
                select(DetallePedido).where(DetallePedido.pedido_id == ped.id)
            ).first()
            corregir_venta(
                session, ped, tid, usuario_id=None, usuario_nombre="Tester",
                lineas=[LineaCorreccion(producto_id=combo.id, cantidad=1,
                                        precio_unitario=Decimal("30.00"),
                                        detalle_id=det.id)],
                pagos=[("fiado", Decimal("30.00"))],
                descuento=Decimal("0.00"), propina=Decimal("0.00"),
                recargo=Decimal("0.00"), recargo_concepto=None,
                cliente_id=cliente.id,
                motivo="Cliente pidió que quede fiado",
                metodos_validos={"efectivo", "yape", "fiado"},
                metodos_efectivo={"efectivo"},
            )
            session.commit()
            session.refresh(ped)

            assert ped.pagado is False  # fiado no está pagado
            cc = session.exec(
                select(CuentaCorriente).where(
                    CuentaCorriente.cliente_id == cliente.id)
            ).first()
            assert cc is not None
            assert Decimal(str(cc.saldo_deuda)) == Decimal("30.00")
            # el pago efectivo original se reemplazó: no queda efectivo en el turno
            pagos = session.exec(
                select(PagoPedido).where(PagoPedido.turno_caja_id == tid)
            ).all()
            assert all(p.metodo == "fiado" for p in pagos)
