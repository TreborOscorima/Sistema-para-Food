"""add tags JSON column to food_productos

Revision ID: e8f1a2b3c4d5
Revises: d7a3b9e2f401
Create Date: 2026-07-07 00:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'e8f1a2b3c4d5'
down_revision: Union[str, None] = 'd7a3b9e2f401'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(table: str, column: str) -> bool:
    conn = op.get_bind()
    insp = sa.inspect(conn)
    return any(c["name"] == column for c in insp.get_columns(table))


def upgrade() -> None:
    if not _has_column("food_productos", "tags"):
        op.add_column(
            "food_productos",
            sa.Column("tags", sa.JSON(), nullable=True),
        )


def downgrade() -> None:
    if _has_column("food_productos", "tags"):
        op.drop_column("food_productos", "tags")
