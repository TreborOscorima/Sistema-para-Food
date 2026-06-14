"""add descuento column to food_pedidos

Revision ID: 0007
Revises: 0006
Create Date: 2026-06-14

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "food_pedidos",
        sa.Column(
            "descuento",
            sa.Numeric(precision=10, scale=2),
            nullable=False,
            server_default="0.00",
        ),
    )


def downgrade() -> None:
    op.drop_column("food_pedidos", "descuento")
