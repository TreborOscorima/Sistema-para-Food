"""add sector to mesa

Revision ID: c6c6d83f95dd
Revises: 8fe5fb3c54f1
Create Date: 2026-07-06 05:19:13.255448

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect as sa_inspect

# revision identifiers, used by Alembic.
revision: str = 'c6c6d83f95dd'
down_revision: Union[str, None] = '8fe5fb3c54f1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(conn, table: str, column: str) -> bool:
    insp = sa_inspect(conn)
    return any(c["name"] == column for c in insp.get_columns(table))


def upgrade() -> None:
    conn = op.get_bind()
    if not _has_column(conn, 'food_mesas', 'sector'):
        op.add_column('food_mesas', sa.Column('sector', sa.String(60), server_default=sa.text("'Salón'"), nullable=False))


def downgrade() -> None:
    conn = op.get_bind()
    if _has_column(conn, 'food_mesas', 'sector'):
        op.drop_column('food_mesas', 'sector')
