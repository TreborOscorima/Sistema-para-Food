"""add_kardex_insumos — kardex de movimientos de insumos + vencimiento

Revision ID: 0021
Revises: 0020
Create Date: 2026-07-02

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0021"
down_revision: Union[str, None] = "0020"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "food_movimientos_insumo",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("insumo_id", sa.Integer(), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=True),
        sa.Column("pedido_id", sa.Integer(), nullable=True),
        sa.Column("tipo", sa.String(length=16), nullable=False),
        sa.Column("cantidad", sa.Numeric(12, 3), nullable=False, server_default="0.000"),
        sa.Column("stock_resultante", sa.Numeric(12, 3), nullable=False, server_default="0.000"),
        sa.Column("motivo", sa.String(length=240), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["insumo_id"], ["food_insumos.id"]),
        sa.ForeignKeyConstraint(["usuario_id"], ["food_usuarios.id"]),
        sa.ForeignKeyConstraint(["pedido_id"], ["food_pedidos.id"]),
    )
    op.create_index("ix_food_movimientos_insumo_company_id", "food_movimientos_insumo", ["company_id"])
    op.create_index("ix_food_movimientos_insumo_insumo_id", "food_movimientos_insumo", ["insumo_id"])
    op.create_index("ix_food_movimientos_insumo_pedido_id", "food_movimientos_insumo", ["pedido_id"])
    op.create_index("ix_food_movimientos_insumo_tipo", "food_movimientos_insumo", ["tipo"])

    op.add_column("food_insumos", sa.Column("fecha_vencimiento", sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column("food_insumos", "fecha_vencimiento")
    op.drop_index("ix_food_movimientos_insumo_tipo", table_name="food_movimientos_insumo")
    op.drop_index("ix_food_movimientos_insumo_pedido_id", table_name="food_movimientos_insumo")
    op.drop_index("ix_food_movimientos_insumo_insumo_id", table_name="food_movimientos_insumo")
    op.drop_index("ix_food_movimientos_insumo_company_id", table_name="food_movimientos_insumo")
    op.drop_table("food_movimientos_insumo")
