"""add nombre_impuesto to food_config_impresora

Revision ID: 0027
Revises: 0026
Create Date: 2026-07-03

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0027"
down_revision: Union[str, None] = "0026"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "food_config_impresora",
        sa.Column("nombre_impuesto", sa.String(20), nullable=False, server_default="IGV"),
    )


def downgrade() -> None:
    op.drop_column("food_config_impresora", "nombre_impuesto")
