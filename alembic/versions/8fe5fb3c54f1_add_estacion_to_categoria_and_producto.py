"""add estacion to categoria and producto

Revision ID: 8fe5fb3c54f1
Revises: 0027
Create Date: 2026-07-06 05:06:59.765347

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect as sa_inspect

# revision identifiers, used by Alembic.
revision: str = '8fe5fb3c54f1'
down_revision: Union[str, None] = '0027'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(conn, table: str, column: str) -> bool:
    insp = sa_inspect(conn)
    return any(c["name"] == column for c in insp.get_columns(table))


def upgrade() -> None:
    conn = op.get_bind()
    if not _has_column(conn, 'food_categorias', 'estacion'):
        op.add_column('food_categorias', sa.Column('estacion', sa.String(20), server_default=sa.text("'cocina'"), nullable=False))
    if not _has_column(conn, 'food_productos', 'estacion'):
        op.add_column('food_productos', sa.Column('estacion', sa.String(20), nullable=True))


def downgrade() -> None:
    conn = op.get_bind()
    if _has_column(conn, 'food_productos', 'estacion'):
        op.drop_column('food_productos', 'estacion')
    if _has_column(conn, 'food_categorias', 'estacion'):
        op.drop_column('food_categorias', 'estacion')
