"""add logo_url to company

Revision ID: 0016
Revises: 0015
Create Date: 2026-07-02

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0016"
down_revision: Union[str, None] = "0015"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "food_companies",
        sa.Column("logo_url", sa.String(length=500), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("food_companies", "logo_url")
