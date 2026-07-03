"""add permission columns to food_usuarios

Revision ID: 0026
Revises: 0025
Create Date: 2026-07-03

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0026"
down_revision: Union[str, None] = "0025"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "food_usuarios",
        sa.Column("perm_descuento", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column(
        "food_usuarios",
        sa.Column("perm_anular", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "food_usuarios",
        sa.Column("perm_reportes", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("food_usuarios", "perm_reportes")
    op.drop_column("food_usuarios", "perm_anular")
    op.drop_column("food_usuarios", "perm_descuento")
