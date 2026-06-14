"""add admin_email and admin_password_hash to config_impresora

Revision ID: 0006
Revises: 0005
Create Date: 2026-06-14

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "food_config_impresora",
        sa.Column("admin_email", sa.String(length=120), nullable=False, server_default=""),
    )
    op.add_column(
        "food_config_impresora",
        sa.Column("admin_password_hash", sa.String(length=128), nullable=False, server_default=""),
    )


def downgrade() -> None:
    op.drop_column("food_config_impresora", "admin_password_hash")
    op.drop_column("food_config_impresora", "admin_email")
