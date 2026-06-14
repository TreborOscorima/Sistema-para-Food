"""add slug to config_impresora

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-14

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "food_config_impresora",
        sa.Column("slug", sa.String(length=80), nullable=False, server_default="mi-restaurante"),
    )


def downgrade() -> None:
    op.drop_column("food_config_impresora", "slug")
