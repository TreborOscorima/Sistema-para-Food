"""add food_cuentas_corrientes and food_movimientos_cuenta

Revision ID: 0010
Revises: 0009
Create Date: 2026-06-16

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0010"
down_revision: Union[str, None] = "0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "food_cuentas_corrientes",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("cliente_id", sa.Integer(), nullable=False),
        sa.Column("saldo_deuda", sa.Numeric(10, 2), nullable=False, server_default="0.00"),
        sa.Column("limite_credito", sa.Numeric(10, 2), nullable=False, server_default="0.00"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["cliente_id"], ["food_clientes.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", "cliente_id", name="uq_food_cc_company_cliente"),
    )
    op.create_index("ix_food_cuentas_corrientes_company_id", "food_cuentas_corrientes", ["company_id"])
    op.create_index("ix_food_cuentas_corrientes_cliente_id", "food_cuentas_corrientes", ["cliente_id"])

    op.create_table(
        "food_movimientos_cuenta",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("cuenta_id", sa.Integer(), nullable=False),
        sa.Column("pedido_id", sa.Integer(), nullable=True),
        sa.Column("tipo", sa.String(10), nullable=False),
        sa.Column("monto", sa.Numeric(10, 2), nullable=False),
        sa.Column("descripcion", sa.String(240), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["cuenta_id"], ["food_cuentas_corrientes.id"]),
        sa.ForeignKeyConstraint(["pedido_id"], ["food_pedidos.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_food_movimientos_cuenta_company_id", "food_movimientos_cuenta", ["company_id"])
    op.create_index("ix_food_movimientos_cuenta_cuenta_id", "food_movimientos_cuenta", ["cuenta_id"])


def downgrade() -> None:
    op.drop_table("food_movimientos_cuenta")
    op.drop_table("food_cuentas_corrientes")
