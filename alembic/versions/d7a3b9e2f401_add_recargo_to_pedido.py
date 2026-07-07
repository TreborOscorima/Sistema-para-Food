"""add recargo and recargo_concepto to food_pedidos

Revision ID: d7a3b9e2f401
Revises: b4e2a7f1c309
Create Date: 2026-07-07 00:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'd7a3b9e2f401'
down_revision: Union[str, None] = 'b4e2a7f1c309'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(table: str, column: str) -> bool:
    conn = op.get_bind()
    insp = sa.inspect(conn)
    return any(c["name"] == column for c in insp.get_columns(table))


def upgrade() -> None:
    if not _has_column("food_pedidos", "recargo"):
        op.add_column(
            "food_pedidos",
            sa.Column("recargo", sa.Numeric(10, 2), nullable=False, server_default="0.00"),
        )
    if not _has_column("food_pedidos", "recargo_concepto"):
        op.add_column(
            "food_pedidos",
            sa.Column("recargo_concepto", sa.String(60), nullable=True),
        )


def downgrade() -> None:
    if _has_column("food_pedidos", "recargo_concepto"):
        op.drop_column("food_pedidos", "recargo_concepto")
    if _has_column("food_pedidos", "recargo"):
        op.drop_column("food_pedidos", "recargo")
