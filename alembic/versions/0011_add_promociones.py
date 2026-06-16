"""add food_promociones table

Revision ID: 0011
Revises: 0010
Create Date: 2026-06-16

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0011"
down_revision: Union[str, None] = "0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "food_promociones",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(120), nullable=False),
        sa.Column("tipo", sa.String(20), nullable=False),
        sa.Column("valor", sa.Numeric(10, 2), nullable=False, server_default="0.00"),
        sa.Column("descripcion", sa.String(240), nullable=True),
        sa.Column("hora_inicio", sa.String(5), nullable=True),
        sa.Column("hora_fin", sa.String(5), nullable=True),
        sa.Column("activa", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_food_promociones_company_id", "food_promociones", ["company_id"])


def downgrade() -> None:
    op.drop_table("food_promociones")
