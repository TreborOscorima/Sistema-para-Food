"""add comanda_auto to config impresora

Revision ID: o5j6k7l8m9n0
Revises: n4i5j6k7l8m0
Create Date: 2026-08-06 00:00:00.000000

Toggle simétrico al de comprobante_auto: la comanda de cocina puede NO imprimirse
automáticamente (comanda_auto=False) para locales que trabajan solo con la
pantalla del KDS, sin impresora en cocina. Default True (backfill: se sigue
imprimiendo como hasta ahora).

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect as sa_inspect

# revision identifiers, used by Alembic.
revision: str = 'o5j6k7l8m9n0'
down_revision: Union[str, None] = 'n4i5j6k7l8m0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(conn, table: str, column: str) -> bool:
    insp = sa_inspect(conn)
    return any(c["name"] == column for c in insp.get_columns(table))


def upgrade() -> None:
    conn = op.get_bind()
    if not _has_column(conn, 'food_config_impresora', 'comanda_auto'):
        op.add_column(
            'food_config_impresora',
            sa.Column(
                'comanda_auto',
                sa.Boolean(),
                server_default=sa.text('1'),
                nullable=False,
            ),
        )


def downgrade() -> None:
    conn = op.get_bind()
    if _has_column(conn, 'food_config_impresora', 'comanda_auto'):
        op.drop_column('food_config_impresora', 'comanda_auto')
