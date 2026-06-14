"""add food_insumos and food_receta_items tables

Revision ID: 0008
Revises: 0007
Create Date: 2026-06-14

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "food_insumos",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(120), nullable=False),
        sa.Column("unidad", sa.String(30), nullable=False, server_default="unidad"),
        sa.Column("stock_actual", sa.Numeric(12, 3), nullable=False, server_default="0.000"),
        sa.Column("stock_minimo", sa.Numeric(12, 3), nullable=False, server_default="0.000"),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", "nombre", name="uq_food_insumos_company_nombre"),
    )
    op.create_index("ix_food_insumos_company_id", "food_insumos", ["company_id"])

    op.create_table(
        "food_receta_items",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("producto_id", sa.Integer(), nullable=False),
        sa.Column("insumo_id", sa.Integer(), nullable=False),
        sa.Column("cantidad", sa.Numeric(10, 3), nullable=False, server_default="1.000"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["producto_id"], ["food_productos.id"]),
        sa.ForeignKeyConstraint(["insumo_id"], ["food_insumos.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "company_id", "producto_id", "insumo_id",
            name="uq_food_receta_company_prod_insumo",
        ),
    )
    op.create_index("ix_food_receta_items_company_id", "food_receta_items", ["company_id"])
    op.create_index("ix_food_receta_items_producto_id", "food_receta_items", ["producto_id"])
    op.create_index("ix_food_receta_items_insumo_id", "food_receta_items", ["insumo_id"])


def downgrade() -> None:
    op.drop_table("food_receta_items")
    op.drop_table("food_insumos")
