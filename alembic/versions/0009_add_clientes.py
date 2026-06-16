"""add food_clientes and cliente_id in food_pedidos

Revision ID: 0009
Revises: 0008
Create Date: 2026-06-16

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0009"
down_revision: Union[str, None] = "0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "food_clientes",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(120), nullable=False),
        sa.Column("telefono", sa.String(20), nullable=True),
        sa.Column("email", sa.String(120), nullable=True),
        sa.Column("fecha_nacimiento", sa.Date(), nullable=True),
        sa.Column("notas", sa.String(240), nullable=True),
        sa.Column("puntos", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", "telefono", name="uq_food_clientes_company_tel"),
    )
    op.create_index("ix_food_clientes_company_id", "food_clientes", ["company_id"])

    op.add_column(
        "food_pedidos",
        sa.Column("cliente_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_food_pedidos_cliente_id",
        "food_pedidos", "food_clientes",
        ["cliente_id"], ["id"],
    )
    op.create_index("ix_food_pedidos_cliente_id", "food_pedidos", ["cliente_id"])


def downgrade() -> None:
    op.drop_index("ix_food_pedidos_cliente_id", "food_pedidos")
    op.drop_constraint("fk_food_pedidos_cliente_id", "food_pedidos", type_="foreignkey")
    op.drop_column("food_pedidos", "cliente_id")
    op.drop_table("food_clientes")
