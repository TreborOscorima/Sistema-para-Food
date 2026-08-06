"""add composite index food_pedidos(company_id, estado) — PERF-03

Revision ID: n4i5j6k7l8m0
Revises: m3h4i5j6k7l9
Create Date: 2026-08-05 21:00:00.000000

PERF-03: agrega el único índice compuesto de la auditoría que faltaba en la BD:
- food_pedidos (company_id, estado)  -> filtrado caliente del polling de mesas/pedidos.

Los otros tres índices compuestos del audit ya existían desde migraciones previas:
- food_pedidos (company_id, cerrado_en)                -> ix_food_pedidos_company_cerrado_en
- food_detalle_pedidos (company_id, estado_produccion) -> ix_food_detalle_pedidos_company_estado_prod
- food_detalle_pedidos (pedido_id, estado_produccion)  -> ix_food_detalle_pedidos_pedido_estado_prod

Costo cero (solo un índice), beneficio directo en cada tick del polling.

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
from sqlalchemy import inspect as sa_inspect

# revision identifiers, used by Alembic.
revision: str = 'n4i5j6k7l8m0'
down_revision: Union[str, None] = 'm3h4i5j6k7l9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (nombre_indice, tabla, [columnas])
_INDEXES = [
    ("ix_food_pedidos_company_estado", "food_pedidos", ["company_id", "estado"]),
]


def _has_index(conn, table: str, name: str) -> bool:
    insp = sa_inspect(conn)
    return any(ix["name"] == name for ix in insp.get_indexes(table))


def upgrade() -> None:
    conn = op.get_bind()
    for name, table, cols in _INDEXES:
        if not _has_index(conn, table, name):
            op.create_index(name, table, cols)


def downgrade() -> None:
    conn = op.get_bind()
    for name, table, _cols in reversed(_INDEXES):
        if _has_index(conn, table, name):
            op.drop_index(name, table_name=table)
