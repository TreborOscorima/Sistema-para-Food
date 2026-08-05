"""add comprobante_impreso_at to pedido

Revision ID: l2g3h4i5j6k8
Revises: k1f2g3h4i5j7
Create Date: 2026-08-05 00:10:00.000000

Distingue la primera emisión del comprobante (libre para caja) de una
reimpresión (requiere permiso). NULL = todavía no se imprimió.

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect as sa_inspect

# revision identifiers, used by Alembic.
revision: str = 'l2g3h4i5j6k8'
down_revision: Union[str, None] = 'k1f2g3h4i5j7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(conn, table: str, column: str) -> bool:
    insp = sa_inspect(conn)
    return any(c["name"] == column for c in insp.get_columns(table))


def upgrade() -> None:
    conn = op.get_bind()
    if not _has_column(conn, 'food_pedidos', 'comprobante_impreso_at'):
        op.add_column(
            'food_pedidos',
            sa.Column('comprobante_impreso_at', sa.DateTime(), nullable=True),
        )


def downgrade() -> None:
    conn = op.get_bind()
    if _has_column(conn, 'food_pedidos', 'comprobante_impreso_at'):
        op.drop_column('food_pedidos', 'comprobante_impreso_at')
