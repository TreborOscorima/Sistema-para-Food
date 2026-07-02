"""add_anulacion_pedido — auditoría de anulaciones con motivo obligatorio

Revision ID: 0020
Revises: 0019
Create Date: 2026-07-02

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0020"
down_revision: Union[str, None] = "0019"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("food_pedidos", sa.Column("motivo_cancelacion", sa.String(length=240), nullable=True))
    op.add_column("food_pedidos", sa.Column("cancelado_por_id", sa.Integer(), nullable=True))
    op.add_column("food_pedidos", sa.Column("cancelado_en", sa.DateTime(), nullable=True))
    op.create_foreign_key(
        "fk_food_pedidos_cancelado_por_id",
        "food_pedidos",
        "food_usuarios",
        ["cancelado_por_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_food_pedidos_cancelado_por_id", "food_pedidos", type_="foreignkey")
    op.drop_column("food_pedidos", "cancelado_en")
    op.drop_column("food_pedidos", "cancelado_por_id")
    op.drop_column("food_pedidos", "motivo_cancelacion")
