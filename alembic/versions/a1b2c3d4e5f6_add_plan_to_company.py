"""add plan and plan_expires_at to food_companies

Revision ID: a1b2c3d4e5f6
Revises: e8f1a2b3c4d5
Create Date: 2026-07-08 00:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'a7b8c9d0e1f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(table: str, column: str) -> bool:
    conn = op.get_bind()
    insp = sa.inspect(conn)
    return any(c["name"] == column for c in insp.get_columns(table))


def upgrade() -> None:
    if not _has_column("food_companies", "plan"):
        op.add_column(
            "food_companies",
            sa.Column("plan", sa.String(20), nullable=False, server_default="trial"),
        )
    if not _has_column("food_companies", "plan_expires_at"):
        op.add_column(
            "food_companies",
            sa.Column("plan_expires_at", sa.DateTime(), nullable=True),
        )


def downgrade() -> None:
    if _has_column("food_companies", "plan_expires_at"):
        op.drop_column("food_companies", "plan_expires_at")
    if _has_column("food_companies", "plan"):
        op.drop_column("food_companies", "plan")
