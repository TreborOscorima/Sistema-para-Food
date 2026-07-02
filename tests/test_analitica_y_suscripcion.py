"""Tests de la analítica de reportes (P6) y del enforcement de suscripción (P7)."""
from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from sqlmodel import Session, SQLModel, create_engine

import app.models  # noqa: F401
from app.models.company import Company
from app.models.food import (
    Categoria,
    EstadoPedido,
    Insumo,
    Pedido,
    Producto,
    RecetaItem,
    UsuarioFood,
)
from app.services.analitica_service import (
    margen_por_plato,
    ventas_por_hora,
    ventas_por_mozo,
)
from app.services.suscripcion_service import (
    MSG_SUSPENDIDA,
    MSG_TRIAL_VENCIDO,
    evaluar_bloqueo,
)
from app.utils.tenant import (
    _refresh_tenant_models,
    register_tenant_listeners,
    set_tenant_context,
    tenant_context,
)

AHORA = datetime(2026, 7, 2, 12, 0)


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


# ─── P7: enforcement de suscripción ──────────────────────────────────────────

def test_bloqueo_empresa_suspendida_o_inexistente():
    assert evaluar_bloqueo(None, AHORA) == MSG_SUSPENDIDA
    suspendida = Company(name="X", slug="x", is_active=False)
    assert evaluar_bloqueo(suspendida, AHORA) == MSG_SUSPENDIDA


def test_bloqueo_trial_vencido_y_vigente():
    vencida = Company(name="X", slug="x", is_active=True,
                      trial_ends_at=AHORA - timedelta(days=1))
    assert evaluar_bloqueo(vencida, AHORA) == MSG_TRIAL_VENCIDO
    vigente = Company(name="X", slug="x", is_active=True,
                      trial_ends_at=AHORA + timedelta(days=10))
    assert evaluar_bloqueo(vigente, AHORA) == ""


def test_sin_trial_configurado_opera_normal():
    sin_trial = Company(name="X", slug="x", is_active=True, trial_ends_at=None)
    assert evaluar_bloqueo(sin_trial, AHORA) == ""


# ─── P6: analítica ────────────────────────────────────────────────────────────

def _pedido(company_id, mozo_id, total, cerrado_en, descuento="0.00", propina="0.00"):
    return Pedido(
        company_id=company_id, mozo_id=mozo_id,
        estado=EstadoPedido.COBRADO.value, pagado=True,
        total=Decimal(total), descuento=Decimal(descuento), propina=Decimal(propina),
        cerrado_en=cerrado_en,
    )


def test_ventas_por_mozo_agrupa_y_ordena(db_engine):
    with Session(db_engine) as session:
        with tenant_context(1, None):
            ana = UsuarioFood(company_id=1, nombre="Ana", pin="x", rol="Mozo")
            beto = UsuarioFood(company_id=1, nombre="Beto", pin="x", rol="Mozo")
            session.add(ana)
            session.add(beto)
            session.flush()
            session.add(_pedido(1, ana.id, "100.00", AHORA, propina="5.00"))
            session.add(_pedido(1, ana.id, "50.00", AHORA, descuento="10.00"))
            session.add(_pedido(1, beto.id, "30.00", AHORA))
            session.add(_pedido(1, None, "20.00", AHORA))  # mostrador
            session.commit()

            ranking = ventas_por_mozo(session, 1)
            assert ranking[0]["nombre"] == "Ana"
            assert ranking[0]["total"] == Decimal("140.00")  # 100 + (50-10)
            assert ranking[0]["pedidos"] == 2
            assert ranking[0]["propinas"] == Decimal("5.00")
            nombres = [f["nombre"] for f in ranking]
            assert "Mostrador" in nombres


def test_ventas_por_hora_convierte_a_hora_local(db_engine):
    with Session(db_engine) as session:
        with tenant_context(1, None):
            # 18:00 UTC = 13:00 en Perú (UTC-5)
            session.add(_pedido(1, None, "60.00", datetime(2026, 7, 2, 18, 30)))
            session.add(_pedido(1, None, "40.00", datetime(2026, 7, 2, 18, 45)))
            session.add(_pedido(1, None, "10.00", datetime(2026, 7, 2, 23, 15)))  # 18:00 local
            session.commit()

            filas = ventas_por_hora(session, 1)
            por_hora = {f["hora"]: f for f in filas}
            assert por_hora[13]["total"] == Decimal("100.00")
            assert por_hora[13]["pedidos"] == 2
            assert por_hora[18]["total"] == Decimal("10.00")


def test_margen_por_plato_con_costos(db_engine):
    with Session(db_engine) as session:
        with tenant_context(1, None):
            cat = Categoria(company_id=1, nombre="Platos")
            session.add(cat)
            session.flush()
            ceviche = Producto(company_id=1, categoria_id=cat.id or 0,
                               nombre="Ceviche", precio=Decimal("30.00"))
            arroz = Producto(company_id=1, categoria_id=cat.id or 0,
                             nombre="Arroz", precio=Decimal("20.00"))
            sin_receta = Producto(company_id=1, categoria_id=cat.id or 0,
                                  nombre="Gaseosa", precio=Decimal("5.00"))
            pescado = Insumo(company_id=1, nombre="Pescado", unidad="kg",
                             costo_unitario=Decimal("40.00"))
            limon = Insumo(company_id=1, nombre="Limón", unidad="kg",
                           costo_unitario=Decimal("0.00"))  # sin costo cargado
            session.add_all([ceviche, arroz, sin_receta, pescado, limon])
            session.flush()
            # Ceviche: 0.25 kg pescado (10.00) + 0.1 kg limón (sin costo)
            session.add(RecetaItem(company_id=1, producto_id=ceviche.id or 0,
                                   insumo_id=pescado.id or 0, cantidad=Decimal("0.250")))
            session.add(RecetaItem(company_id=1, producto_id=ceviche.id or 0,
                                   insumo_id=limon.id or 0, cantidad=Decimal("0.100")))
            # Arroz: 0.1 kg pescado → costo 4.00, margen 16.00 (80%)
            session.add(RecetaItem(company_id=1, producto_id=arroz.id or 0,
                                   insumo_id=pescado.id or 0, cantidad=Decimal("0.100")))
            session.commit()

            filas = margen_por_plato(session, 1)
            nombres = [f["nombre"] for f in filas]
            assert "Gaseosa" not in nombres  # sin receta no aparece
            ceviche_fila = next(f for f in filas if f["nombre"] == "Ceviche")
            assert ceviche_fila["costo"] == Decimal("10.00")
            assert ceviche_fila["margen"] == Decimal("20.00")
            assert ceviche_fila["costo_completo"] is False  # limón sin costo
            arroz_fila = next(f for f in filas if f["nombre"] == "Arroz")
            assert arroz_fila["margen_pct"] == 80.0
            assert arroz_fila["costo_completo"] is True
            # Ordenado por margen % ascendente (peor primero)
            assert filas[0]["margen_pct"] <= filas[-1]["margen_pct"]
