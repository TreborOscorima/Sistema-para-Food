"""add kds_minutos_alerta to config_impresora

Revision ID: b4e2a7f1c309
Revises: a3f1c2d8e901
Create Date: 2026-07-06 20:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'b4e2a7f1c309'
down_revision: Union[str, None] = 'a3f1c2d8e901'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(table: str, column: str) -> bool:
    conn = op.get_bind()
    insp = sa.inspect(conn)
    return any(c["name"] == column for c in insp.get_columns(table))


def upgrade() -> None:
    if not _has_column("food_config_impresora", "kds_minutos_alerta"):
        op.add_column(
            "food_config_impresora",
            sa.Column("kds_minutos_alerta", sa.Integer(), nullable=False, server_default="15"),
        )


def downgrade() -> None:
    with op.batch_alter_table("food_config_impresora") as batch_op:
        batch_op.drop_column("kds_minutos_alerta")
