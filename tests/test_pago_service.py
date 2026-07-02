"""Tests de pagos divididos/mixtos y su integración con el arqueo del turno."""
from __future__ import annotations

from decimal import Decimal

import pytest
from sqlmodel import Session, SQLModel, create_engine, select

import app.models  # noqa: F401  registra todos los modelos SQLModel
from app.models.food import EstadoPedido, PagoPedido, Pedido
from app.services.pago_service import (
    metodo_pago_resumen,
    registrar_pagos_pedido,
    validar_pagos,
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


# ─── validar_pagos ────────────────────────────────────────────────────────────

def test_pago_exacto_un_metodo():
    r = validar_pagos(Decimal("100.00"), [("tarjeta", Decimal("100.00"))])
    assert r.total_pagado == Decimal("100.00")
    assert r.vuelto == Decimal("0.00")
    assert r.total_fiado == Decimal("0.00")


def test_pago_mixto_con_vuelto_desde_efectivo():
    # Cuenta de 80: 50 en QR + 50 en efectivo → vuelto 20, cajón queda con 30
    r = validar_pagos(
        Decimal("80.00"),
        [("qr", Decimal("50.00")), ("efectivo", Decimal("50.00"))],
    )
    assert r.vuelto == Decimal("20.00")
    assert r.efectivo_neto == Decimal("30.00")
    assert r.total_efectivo == Decimal("50.00")


def test_pagos_insuficientes_rechazados():
    with pytest.raises(ValueError, match="no cubren"):
        validar_pagos(Decimal("100.00"), [("efectivo", Decimal("60.00"))])


def test_sobrepago_electronico_rechazado():
    # El vuelto no puede salir de la tarjeta
    with pytest.raises(ValueError, match="vuelto solo sale del efectivo"):
        validar_pagos(Decimal("80.00"), [("tarjeta", Decimal("100.00"))])


def test_metodo_invalido_y_monto_cero():
    with pytest.raises(ValueError, match="inválido"):
        validar_pagos(Decimal("10.00"), [("cheque", Decimal("10.00"))])
    with pytest.raises(ValueError, match="mayor a cero"):
        validar_pagos(Decimal("10.00"), [("efectivo", Decimal("0.00"))])
    with pytest.raises(ValueError, match="al menos un pago"):
        validar_pagos(Decimal("10.00"), [])


def test_fiado_parcial_en_mixto():
    # 100: 40 efectivo + 60 fiado → CC carga solo 60
    r = validar_pagos(
        Decimal("100.00"),
        [("efectivo", Decimal("40.00")), ("fiado", Decimal("60.00"))],
    )
    assert r.total_fiado == Decimal("60.00")
    assert r.vuelto == Decimal("0.00")


def test_metodo_pago_resumen():
    assert metodo_pago_resumen([("efectivo", Decimal("10"))]) == "efectivo"
    assert metodo_pago_resumen(
        [("efectivo", Decimal("10")), ("efectivo", Decimal("5"))]
    ) == "efectivo"
    assert metodo_pago_resumen(
        [("efectivo", Decimal("10")), ("qr", Decimal("5"))]
    ) == "mixto"


# ─── registrar_pagos_pedido + arqueo ─────────────────────────────────────────

def test_registro_consolida_efectivo_neto_de_vuelto(db_engine):
    with Session(db_engine) as session:
        with tenant_context(1, None):
            pedido = Pedido(
                company_id=1, total=Decimal("80.00"),
                estado=EstadoPedido.COBRADO.value, metodo_pago="mixto",
            )
            session.add(pedido)
            session.flush()
            pagos = [("qr", Decimal("50.00")), ("efectivo", Decimal("50.00"))]
            resultado = validar_pagos(Decimal("80.00"), pagos)
            filas = registrar_pagos_pedido(session, pedido, None, None, pagos, resultado)
            session.commit()
            assert len(filas) == 2
            efectivo = next(f for f in filas if f.metodo == "efectivo")
            assert efectivo.monto == Decimal("30.00")  # 50 entregados - 20 de vuelto
            qr = next(f for f in filas if f.metodo == "qr")
            assert qr.monto == Decimal("50.00")


def test_arqueo_usa_pagos_y_fallback_legacy(db_engine):
    with Session(db_engine) as session:
        with tenant_context(1, None):
            turno = abrir_turno_caja(session, 1, usuario_id=None, monto_inicial=Decimal("100.00"))
            session.commit()
            tid = turno.id or 0

            # Pedido nuevo con pagos divididos: 60 efectivo + 40 tarjeta
            p1 = Pedido(
                company_id=1, turno_caja_id=tid, total=Decimal("100.00"),
                estado=EstadoPedido.COBRADO.value, metodo_pago="mixto",
            )
            session.add(p1)
            session.flush()
            pagos = [("efectivo", Decimal("60.00")), ("tarjeta", Decimal("40.00"))]
            registrar_pagos_pedido(
                session, p1, tid, None, pagos, validar_pagos(Decimal("100.00"), pagos)
            )

            # Pedido legacy (sin filas de pago): efectivo 25 — no se duplica
            session.add(Pedido(
                company_id=1, turno_caja_id=tid, total=Decimal("25.00"),
                estado=EstadoPedido.COBRADO.value, metodo_pago="efectivo", pagado=True,
            ))
            session.commit()

            resumen = calcular_resumen_turno(session, turno)
            assert resumen["efectivo"] == Decimal("85.00")   # 60 + 25, sin doble conteo
            assert resumen["tarjeta"] == Decimal("40.00")
            # 100 fondo + 85 efectivo
            assert resumen["esperado_efectivo"] == Decimal("185.00")


def test_arqueo_ignora_pagos_de_pedidos_cancelados(db_engine):
    with Session(db_engine) as session:
        with tenant_context(1, None):
            turno = abrir_turno_caja(session, 1, usuario_id=None, monto_inicial=Decimal("0.00"))
            session.commit()
            tid = turno.id or 0
            cancelado = Pedido(
                company_id=1, turno_caja_id=tid, total=Decimal("30.00"),
                estado=EstadoPedido.CANCELADO.value, metodo_pago="efectivo",
            )
            session.add(cancelado)
            session.flush()
            session.add(PagoPedido(
                company_id=1, pedido_id=cancelado.id or 0, turno_caja_id=tid,
                metodo="efectivo", monto=Decimal("30.00"),
            ))
            session.commit()

            resumen = calcular_resumen_turno(session, turno)
            assert resumen["efectivo"] == Decimal("0.00")
            assert resumen["esperado_efectivo"] == Decimal("0.00")
