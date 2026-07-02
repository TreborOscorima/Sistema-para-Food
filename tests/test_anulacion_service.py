"""Tests de anulación auditada — pedido abierto y venta cobrada."""
from __future__ import annotations

from decimal import Decimal

import pytest
from sqlmodel import Session, SQLModel, create_engine, select

import app.models  # noqa: F401  registra todos los modelos SQLModel
from app.models.food import (
    CuentaCorriente,
    Cliente,
    DetallePedido,
    EstadoMesa,
    EstadoPedido,
    Insumo,
    Mesa,
    MovimientoCuenta,
    Pedido,
    Producto,
    Categoria,
    RecetaItem,
)
from app.services.anulacion_service import (
    anular_pedido_abierto,
    anular_venta_cobrada,
)
from app.states.caja_turno_mixin import abrir_turno_caja, calcular_resumen_turno
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


def test_anular_abierto_libera_mesa_y_registra_motivo(db_engine):
    with Session(db_engine) as session:
        with tenant_context(1, None):
            mesa = Mesa(company_id=1, numero=5, estado=EstadoMesa.OCUPADA.value)
            session.add(mesa)
            session.flush()
            pedido = Pedido(
                company_id=1, mesa_id=mesa.id,
                estado=EstadoPedido.ENVIADO.value, total=Decimal("40.00"),
            )
            session.add(pedido)
            session.flush()

            anular_pedido_abierto(session, pedido, usuario_id=None, motivo="Cliente se retiró")
            session.commit()

            assert pedido.estado == EstadoPedido.CANCELADO.value
            assert pedido.motivo_cancelacion == "Cliente se retiró"
            assert pedido.cancelado_en is not None
            assert mesa.estado == EstadoMesa.LIBRE.value


def test_anular_requiere_motivo_y_bloquea_doble(db_engine):
    with Session(db_engine) as session:
        with tenant_context(1, None):
            pedido = Pedido(company_id=1, estado=EstadoPedido.ENVIADO.value)
            session.add(pedido)
            session.flush()

            with pytest.raises(ValueError, match="motivo"):
                anular_pedido_abierto(session, pedido, None, "  ")

            anular_pedido_abierto(session, pedido, None, "error de carga")
            with pytest.raises(ValueError, match="ya está anulado"):
                anular_pedido_abierto(session, pedido, None, "otra vez")


def test_anular_abierto_rechaza_cobrado(db_engine):
    with Session(db_engine) as session:
        with tenant_context(1, None):
            pedido = Pedido(company_id=1, estado=EstadoPedido.COBRADO.value, pagado=True)
            session.add(pedido)
            session.flush()
            with pytest.raises(ValueError, match="Reportes"):
                anular_pedido_abierto(session, pedido, None, "quiero anularlo")


def test_anular_venta_repone_stock_y_sale_del_arqueo(db_engine):
    with Session(db_engine) as session:
        with tenant_context(1, None):
            turno = abrir_turno_caja(session, 1, usuario_id=None, monto_inicial=Decimal("0.00"))
            cat = Categoria(company_id=1, nombre="Platos")
            session.add(cat)
            session.flush()
            prod = Producto(company_id=1, categoria_id=cat.id or 0, nombre="Ceviche",
                            precio=Decimal("30.00"))
            insumo = Insumo(company_id=1, nombre="Pescado", unidad="kg",
                            stock_actual=Decimal("8.000"))
            session.add(prod)
            session.add(insumo)
            session.flush()
            session.add(RecetaItem(company_id=1, producto_id=prod.id or 0,
                                   insumo_id=insumo.id or 0, cantidad=Decimal("0.250")))
            pedido = Pedido(
                company_id=1, turno_caja_id=turno.id, estado=EstadoPedido.COBRADO.value,
                pagado=True, metodo_pago="efectivo", total=Decimal("60.00"),
                cerrado_en=pedido_cerrado_en(),
            )
            session.add(pedido)
            session.flush()
            session.add(DetallePedido(
                company_id=1, pedido_id=pedido.id or 0, producto_id=prod.id or 0,
                cantidad=2, precio_unitario=Decimal("30.00"), subtotal=Decimal("60.00"),
            ))
            # Simular el descuento que ocurrió al cobrar: 2 × 0.250 = 0.5 kg
            insumo.stock_actual = Decimal("7.500")
            session.commit()

            assert calcular_resumen_turno(session, turno)["efectivo"] == Decimal("60.00")

            anular_venta_cobrada(session, pedido, usuario_id=None, motivo="Plato devuelto")
            session.commit()
            session.refresh(insumo)

            assert pedido.estado == EstadoPedido.CANCELADO.value
            assert insumo.stock_actual == Decimal("8.000")  # stock repuesto
            resumen = calcular_resumen_turno(session, turno)
            assert resumen["efectivo"] == Decimal("0.00")  # fuera del arqueo


def pedido_cerrado_en():
    from tuwayki_core.utils.timezone import utc_now_naive
    return utc_now_naive()


def test_anular_venta_fiada_revierte_cc(db_engine):
    with Session(db_engine) as session:
        with tenant_context(1, None):
            cliente = Cliente(company_id=1, nombre="Don Julio")
            session.add(cliente)
            session.flush()
            cuenta = CuentaCorriente(
                company_id=1, cliente_id=cliente.id or 0,
                saldo_deuda=Decimal("50.00"), limite_credito=Decimal("200.00"),
            )
            session.add(cuenta)
            session.flush()
            pedido = Pedido(
                company_id=1, estado=EstadoPedido.COBRADO.value, pagado=False,
                metodo_pago="fiado", total=Decimal("50.00"), cliente_id=cliente.id,
                cerrado_en=pedido_cerrado_en(),
            )
            session.add(pedido)
            session.flush()
            session.add(MovimientoCuenta(
                company_id=1, cuenta_id=cuenta.id or 0, pedido_id=pedido.id,
                tipo="cargo", monto=Decimal("50.00"), descripcion="Fiado mesa 3",
            ))
            session.commit()

            revertido = anular_venta_cobrada(session, pedido, None, "Venta duplicada")
            session.commit()
            session.refresh(cuenta)

            assert revertido == Decimal("50.00")
            assert cuenta.saldo_deuda == Decimal("0.00")
            # El cargo original sigue existiendo + contraasiento de pago
            movimientos = session.exec(
                select(MovimientoCuenta).where(MovimientoCuenta.pedido_id == pedido.id)
            ).all()
            tipos = sorted(m.tipo for m in movimientos)
            assert tipos == ["cargo", "pago"]


def test_anular_venta_rechaza_pedido_abierto(db_engine):
    with Session(db_engine) as session:
        with tenant_context(1, None):
            pedido = Pedido(company_id=1, estado=EstadoPedido.ENVIADO.value)
            session.add(pedido)
            session.flush()
            with pytest.raises(ValueError, match="Solo se pueden anular ventas cobradas"):
                anular_venta_cobrada(session, pedido, None, "no corresponde")
