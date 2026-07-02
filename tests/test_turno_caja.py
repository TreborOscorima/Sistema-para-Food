"""Tests del turno de caja — apertura, movimientos, resumen y cierre con arqueo.

Ejercitan las funciones puras de app/states/caja_turno_mixin.py con SQLite
en memoria y los listeners de tenant activos (mismo patrón que
test_tenant_isolation.py).
"""
from __future__ import annotations

from decimal import Decimal

import pytest
from sqlmodel import Session, SQLModel, create_engine

import app.models  # noqa: F401  registra todos los modelos SQLModel
from app.models.food import EstadoPedido, EstadoTurnoCaja, Pedido, TipoMovimientoCaja
from app.states.caja_turno_mixin import (
    abrir_turno_caja,
    calcular_resumen_turno,
    cerrar_turno_caja,
    get_turno_abierto,
    registrar_movimiento_caja,
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


def _pedido_cobrado(
    company_id: int,
    turno_id: int,
    metodo: str,
    total: str,
    descuento: str = "0.00",
    propina: str = "0.00",
    estado: str = EstadoPedido.COBRADO.value,
) -> Pedido:
    return Pedido(
        company_id=company_id,
        turno_caja_id=turno_id,
        metodo_pago=metodo,
        total=Decimal(total),
        descuento=Decimal(descuento),
        propina=Decimal(propina),
        estado=estado,
        pagado=metodo != "fiado",
    )


def test_abrir_turno_y_unicidad(db_engine):
    with Session(db_engine) as session:
        with tenant_context(1, None):
            turno = abrir_turno_caja(session, 1, usuario_id=None, monto_inicial=Decimal("100.00"))
            session.commit()
            assert turno.estado == EstadoTurnoCaja.ABIERTO.value
            assert turno.monto_inicial == Decimal("100.00")
            assert get_turno_abierto(session, 1) is not None

            with pytest.raises(ValueError, match="Ya hay un turno"):
                abrir_turno_caja(session, 1, usuario_id=None, monto_inicial=Decimal("50.00"))


def test_abrir_turno_monto_negativo(db_engine):
    with Session(db_engine) as session:
        with tenant_context(1, None):
            with pytest.raises(ValueError, match="negativo"):
                abrir_turno_caja(session, 1, usuario_id=None, monto_inicial=Decimal("-1.00"))


def test_movimientos_validaciones(db_engine):
    with Session(db_engine) as session:
        with tenant_context(1, None):
            turno = abrir_turno_caja(session, 1, usuario_id=None, monto_inicial=Decimal("0.00"))
            session.commit()

            with pytest.raises(ValueError, match="mayor a cero"):
                registrar_movimiento_caja(
                    session, turno, None, TipoMovimientoCaja.EGRESO.value,
                    "Mercado", Decimal("0.00"), "compra",
                )
            with pytest.raises(ValueError, match="motivo"):
                registrar_movimiento_caja(
                    session, turno, None, TipoMovimientoCaja.EGRESO.value,
                    "Mercado", Decimal("10.00"), "   ",
                )
            with pytest.raises(ValueError, match="inválido"):
                registrar_movimiento_caja(
                    session, turno, None, "retiro",
                    "Mercado", Decimal("10.00"), "x",
                )

            mov = registrar_movimiento_caja(
                session, turno, None, TipoMovimientoCaja.EGRESO.value,
                "Mercado", Decimal("35.50"), "Verduras del día",
            )
            session.commit()
            assert mov.monto == Decimal("35.50")
            assert mov.turno_id == turno.id


def test_resumen_turno_buckets_y_esperado(db_engine):
    with Session(db_engine) as session:
        with tenant_context(1, None):
            turno = abrir_turno_caja(session, 1, usuario_id=None, monto_inicial=Decimal("100.00"))
            session.commit()
            tid = turno.id or 0

            # Efectivo: (50 - 5 desc + 3 propina) → cajón 48
            session.add(_pedido_cobrado(1, tid, "efectivo", "50.00", "5.00", "3.00"))
            # Tarjeta: (80 + 2 propina) → no toca el cajón
            session.add(_pedido_cobrado(1, tid, "tarjeta", "80.00", "0.00", "2.00"))
            # QR: 20
            session.add(_pedido_cobrado(1, tid, "qr", "20.00"))
            # Fiado: 30 → no entra a caja
            session.add(_pedido_cobrado(1, tid, "fiado", "30.00"))
            # Cancelado: se excluye
            session.add(_pedido_cobrado(
                1, tid, "efectivo", "99.00", estado=EstadoPedido.CANCELADO.value,
            ))
            registrar_movimiento_caja(
                session, turno, None, TipoMovimientoCaja.INGRESO.value,
                "Fondo adicional", Decimal("20.00"), "sencillo",
            )
            registrar_movimiento_caja(
                session, turno, None, TipoMovimientoCaja.EGRESO.value,
                "Mercado", Decimal("35.00"), "verduras",
            )
            session.commit()

            resumen = calcular_resumen_turno(session, turno)
            assert resumen["efectivo"] == Decimal("48.00")
            assert resumen["tarjeta"] == Decimal("82.00")
            assert resumen["qr"] == Decimal("20.00")
            assert resumen["fiado"] == Decimal("30.00")
            assert resumen["propinas"] == Decimal("5.00")
            assert resumen["ingresos"] == Decimal("20.00")
            assert resumen["egresos"] == Decimal("35.00")
            # 100 fondo + 48 efectivo + 20 ingresos - 35 egresos
            assert resumen["esperado_efectivo"] == Decimal("133.00")


def test_cierre_snapshot_y_descuadre(db_engine):
    with Session(db_engine) as session:
        with tenant_context(1, None):
            turno = abrir_turno_caja(session, 1, usuario_id=None, monto_inicial=Decimal("50.00"))
            session.commit()
            session.add(_pedido_cobrado(1, turno.id or 0, "efectivo", "40.00"))
            session.commit()

            cerrado = cerrar_turno_caja(
                session, turno, usuario_id=None,
                contado_efectivo=Decimal("85.00"),
                arqueo_detalle='{"b50": 1, "b20": 1, "b10": 1, "m5": 1}',
                notas="faltó sencillo",
            )
            session.commit()

            assert cerrado.estado == EstadoTurnoCaja.CERRADO.value
            assert cerrado.cerrado_en is not None
            assert cerrado.total_efectivo == Decimal("40.00")
            assert cerrado.esperado_efectivo == Decimal("90.00")
            assert cerrado.contado_efectivo == Decimal("85.00")
            assert cerrado.descuadre == Decimal("-5.00")
            assert cerrado.notas_cierre == "faltó sencillo"
            assert get_turno_abierto(session, 1) is None

            with pytest.raises(ValueError, match="cerrado"):
                cerrar_turno_caja(session, turno, None, Decimal("0.00"))


def test_turnos_aislados_por_empresa(db_engine):
    with Session(db_engine) as session:
        with tenant_context(1, None):
            abrir_turno_caja(session, 1, usuario_id=None, monto_inicial=Decimal("10.00"))
            session.commit()
    with Session(db_engine) as session:
        with tenant_context(2, None):
            # La empresa 2 no ve el turno de la 1 y puede abrir el suyo
            assert get_turno_abierto(session, 2) is None
            turno2 = abrir_turno_caja(session, 2, usuario_id=None, monto_inicial=Decimal("30.00"))
            session.commit()
            assert turno2.company_id == 2
    with Session(db_engine) as session:
        with tenant_context(1, None):
            turno1 = get_turno_abierto(session, 1)
            assert turno1 is not None
            assert turno1.monto_inicial == Decimal("10.00")
