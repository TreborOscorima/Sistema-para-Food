"""add_costo_insumo — costo unitario del insumo para margen por plato

Revision ID: 0023
Revises: 0022
Create Date: 2026-07-02

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0023"
down_revision: Union[str, None] = "0022"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "food_insumos",
        sa.Column("costo_unitario", sa.Numeric(10, 2), nullable=False, server_default="0.00"),
    )


def downgrade() -> None:
    op.drop_column("food_insumos", "costo_unitario")
