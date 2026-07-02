"""add ticket_paper_width_mm to config_impresora

Revision ID: 0017
Revises: 0016
Create Date: 2026-07-02

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0017"
down_revision: Union[str, None] = "0016"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "food_config_impresora",
        sa.Column("ticket_paper_width_mm", sa.Integer(), nullable=False, server_default="80"),
    )


def downgrade() -> None:
    op.drop_column("food_config_impresora", "ticket_paper_width_mm")
