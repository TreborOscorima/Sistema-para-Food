"""add qr_token to mesas and self_order fields to pedidos

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-07-09 00:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'f6a7b8c9d0e1'
down_revision: Union[str, None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(table: str, column: str) -> bool:
    conn = op.get_bind()
    insp = sa.inspect(conn)
    return any(c["name"] == column for c in insp.get_columns(table))


def upgrade() -> None:
    if not _has_column("food_mesas", "qr_token"):
        op.add_column("food_mesas", sa.Column("qr_token", sa.String(64), nullable=True))
        op.create_index("ix_food_mesas_qr_token", "food_mesas", ["qr_token"])
    if not _has_column("food_pedidos", "self_order"):
        op.add_column("food_pedidos", sa.Column("self_order", sa.Boolean(), nullable=False, server_default=sa.text("0")))
    if not _has_column("food_pedidos", "self_order_aprobado"):
        op.add_column("food_pedidos", sa.Column("self_order_aprobado", sa.Boolean(), nullable=False, server_default=sa.text("0")))


def downgrade() -> None:
    if _has_column("food_pedidos", "self_order_aprobado"):
        op.drop_column("food_pedidos", "self_order_aprobado")
    if _has_column("food_pedidos", "self_order"):
        op.drop_column("food_pedidos", "self_order")
    if _has_column("food_mesas", "qr_token"):
        op.drop_index("ix_food_mesas_qr_token", table_name="food_mesas")
        op.drop_column("food_mesas", "qr_token")
