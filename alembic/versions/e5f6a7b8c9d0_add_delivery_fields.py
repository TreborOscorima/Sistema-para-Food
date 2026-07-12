"""add delivery fields to food_pedidos

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-07-09 00:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(table: str, column: str) -> bool:
    conn = op.get_bind()
    insp = sa.inspect(conn)
    return any(c["name"] == column for c in insp.get_columns(table))


def upgrade() -> None:
    table = "food_pedidos"
    if not _has_column(table, "delivery_direccion"):
        op.add_column(table, sa.Column("delivery_direccion", sa.String(240), nullable=True))
    if not _has_column(table, "delivery_telefono"):
        op.add_column(table, sa.Column("delivery_telefono", sa.String(20), nullable=True))
    if not _has_column(table, "delivery_repartidor_id"):
        op.add_column(table, sa.Column("delivery_repartidor_id", sa.Integer(), nullable=True))
        op.create_foreign_key(
            "fk_food_pedidos_repartidor",
            table, "food_usuarios",
            ["delivery_repartidor_id"], ["id"],
        )
    if not _has_column(table, "delivery_estado"):
        op.add_column(table, sa.Column("delivery_estado", sa.String(20), nullable=True))
    if not _has_column(table, "delivery_notas"):
        op.add_column(table, sa.Column("delivery_notas", sa.String(240), nullable=True))


def downgrade() -> None:
    table = "food_pedidos"
    for col in ["delivery_notas", "delivery_estado", "delivery_repartidor_id",
                 "delivery_telefono", "delivery_direccion"]:
        if _has_column(table, col):
            if col == "delivery_repartidor_id":
                op.drop_constraint("fk_food_pedidos_repartidor", table, type_="foreignkey")
            op.drop_column(table, col)
