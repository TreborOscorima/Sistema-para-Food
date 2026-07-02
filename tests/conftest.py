"""Fixtures compartidos entre todos los tests de TUWAYKIFOOD.

Cada módulo define sus propios fixtures db_engine si necesita configuración
especial; este conftest sólo provee el teardown de tenant context para
evitar que un test contamine al siguiente.
"""
from __future__ import annotations

import pytest

from app.utils.tenant import set_tenant_context


@pytest.fixture(autouse=True)
def _clean_tenant_context():
    """Limpia el tenant context al final de cada test."""
    yield
    set_tenant_context(None, None)
