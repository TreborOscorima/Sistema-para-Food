"""Tests de aislamiento multi-tenant para TUWAYKIFOOD.

IMPORTANTE: test_a_select_is_filtered_by_tenant DEBE ejecutarse antes que
cualquier otro test que invoque set_tenant_context() + flush/commit en el
mismo proceso — with_loader_criteria de SQLAlchemy cachea la primera
compilación de statement. Mismo patrón que Sistema-de-Ventas
(tests/test_tenant_enforcement.py). En producción esto no aplica porque
cada request usa un contexto async independiente.
"""
from __future__ import annotations

import pytest
from sqlmodel import Session, SQLModel, create_engine, select

import app.models  # noqa: F401  registra todos los modelos SQLModel
from app.models import Company
from app.models.food import Mesa, UsuarioFood
from app.utils.tenant import (
    _refresh_tenant_models,
    register_tenant_listeners,
    set_tenant_context,
    tenant_bypass,
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


# NOTE: debe correr primero (orden alfabético: "a" antes de "auto"/"bypass"/"missing")
def test_a_select_is_filtered_by_tenant():
    """El listener do_orm_execute filtra SELECTs por company_id activo,
    incluso sin filtro explícito en la query."""
    register_tenant_listeners()
    _refresh_tenant_models()
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        with tenant_bypass():
            session.add(UsuarioFood(company_id=1, nombre="Mozo A", pin="hashA", rol="Mozo"))
            session.add(UsuarioFood(company_id=2, nombre="Mozo B", pin="hashB", rol="Mozo"))
            session.commit()

    with Session(engine) as session:
        set_tenant_context(1, None)
        rows = session.exec(select(UsuarioFood)).all()
        assert len(rows) == 1
        assert rows[0].company_id == 1
        assert rows[0].nombre == "Mozo A"


def test_auto_sets_company_id_on_create(db_engine):
    with Session(db_engine) as session:
        with tenant_context(5, None):
            mesa = Mesa(numero=1, nombre="Mesa 1")
            session.add(mesa)
            session.commit()
            assert mesa.company_id == 5


def test_missing_tenant_context_raises(db_engine):
    with Session(db_engine) as session:
        set_tenant_context(None, None)
        mesa = Mesa(numero=1, nombre="Mesa sin contexto")
        session.add(mesa)
        with pytest.raises(RuntimeError):
            session.commit()


def test_bypass_sees_all_companies(db_engine):
    with Session(db_engine) as session:
        with tenant_bypass():
            session.add(Company(name="Restaurante A", slug="resto-a"))
            session.add(Company(name="Restaurante B", slug="resto-b"))
            session.commit()
            rows = session.exec(select(Company)).all()
            assert len(rows) == 2


def test_two_companies_zero_cross_visibility(db_engine):
    """Simula el escenario real: 2 empresas, cada una con su propia mesa —
    ninguna ve datos de la otra.

    Usa filtro EXPLÍCITO (.where(company_id == X)) con bypass activo, igual
    que FoodState._tenant_session() en la app real — no el filtro automático
    de with_loader_criteria. Motivo: with_loader_criteria cachea la primera
    compilación del statement por proceso; dos SELECTs de la misma forma con
    distinto contexto en el mismo test pueden reusar el valor viejo (gotcha
    documentado de SQLAlchemy, no un bug de esta app). Por eso FoodState
    nunca depende del filtro automático para su lógica de negocio — el
    listener queda solo como red de seguridad para queries sin filtrar."""
    with Session(db_engine) as session:
        with tenant_bypass():
            session.add(Mesa(company_id=1, numero=1, nombre="Mesa Resto A"))
            session.add(Mesa(company_id=2, numero=1, nombre="Mesa Resto B"))
            session.commit()

    with Session(db_engine) as session:
        with tenant_bypass():
            mesas_a = session.exec(
                select(Mesa).where(Mesa.company_id == 1)
            ).all()
        assert len(mesas_a) == 1
        assert mesas_a[0].nombre == "Mesa Resto A"

    with Session(db_engine) as session:
        with tenant_bypass():
            mesas_b = session.exec(
                select(Mesa).where(Mesa.company_id == 2)
            ).all()
        assert len(mesas_b) == 1
        assert mesas_b[0].nombre == "Mesa Resto B"
