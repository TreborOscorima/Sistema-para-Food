"""add combos tables

Revision ID: 211cb3440c87
Revises: 72325b029491
Create Date: 2026-07-06 14:48:26.830106

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel

revision: str = '211cb3440c87'
down_revision: Union[str, None] = '72325b029491'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(name: str) -> bool:
    conn = op.get_bind()
    insp = sa.inspect(conn)
    return name in insp.get_table_names()


def _has_column(table: str, column: str) -> bool:
    conn = op.get_bind()
    insp = sa.inspect(conn)
    return any(c["name"] == column for c in insp.get_columns(table))


def upgrade() -> None:
    if not _table_exists("food_combos"):
        op.create_table(
            "food_combos",
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("company_id", sa.Integer(), nullable=False),
            sa.Column("nombre", sqlmodel.sql.sqltypes.AutoString(length=160), nullable=False),
            sa.Column("descripcion", sqlmodel.sql.sqltypes.AutoString(length=240), nullable=True),
            sa.Column("precio", sa.Numeric(precision=10, scale=2), nullable=False),
            sa.Column("emoji", sqlmodel.sql.sqltypes.AutoString(length=16), nullable=True),
            sa.Column("activo", sa.Boolean(), nullable=False),
            sa.Column("orden", sa.Integer(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_food_combos_company_id", "food_combos", ["company_id"], unique=False)

    if not _table_exists("food_combo_items"):
        op.create_table(
            "food_combo_items",
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("combo_id", sa.Integer(), nullable=False),
            sa.Column("producto_id", sa.Integer(), nullable=False),
            sa.Column("cantidad", sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(["combo_id"], ["food_combos.id"]),
            sa.ForeignKeyConstraint(["producto_id"], ["food_productos.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_food_combo_items_combo_id", "food_combo_items", ["combo_id"], unique=False)
        op.create_index("ix_food_combo_items_producto_id", "food_combo_items", ["producto_id"], unique=False)

    if not _has_column("food_detalle_pedidos", "combo_items_json"):
        op.add_column("food_detalle_pedidos", sa.Column("combo_items_json", sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("food_detalle_pedidos") as batch_op:
        batch_op.drop_column("combo_items_json")

    op.drop_table("food_combo_items")
    op.drop_table("food_combos")
