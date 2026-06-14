"""add imagen_url to producto

Revision ID: 0005
Revises: 0004
Create Date: 2026-06-14

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "food_productos",
        sa.Column("imagen_url", sa.String(length=500), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("food_productos", "imagen_url")
