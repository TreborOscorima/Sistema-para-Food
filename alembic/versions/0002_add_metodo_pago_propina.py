"""add metodo_pago y propina a food_pedidos

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-14

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "food_pedidos",
        sa.Column("metodo_pago", sa.String(length=24), nullable=True),
    )
    op.add_column(
        "food_pedidos",
        sa.Column(
            "propina",
            sa.Numeric(precision=10, scale=2),
            nullable=False,
            server_default="0.00",
        ),
    )


def downgrade() -> None:
    op.drop_column("food_pedidos", "propina")
    op.drop_column("food_pedidos", "metodo_pago")
