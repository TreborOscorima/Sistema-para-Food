"""add detalle_ids_json to pagos_pedido

Revision ID: a3f1c2d8e901
Revises: 211cb3440c87
Create Date: 2026-07-06 20:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'a3f1c2d8e901'
down_revision: Union[str, None] = '211cb3440c87'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(table: str, column: str) -> bool:
    conn = op.get_bind()
    insp = sa.inspect(conn)
    return any(c["name"] == column for c in insp.get_columns(table))


def upgrade() -> None:
    if not _has_column("food_pagos_pedido", "detalle_ids_json"):
        op.add_column(
            "food_pagos_pedido",
            sa.Column("detalle_ids_json", sa.Text(), nullable=True),
        )


def downgrade() -> None:
    with op.batch_alter_table("food_pagos_pedido") as batch_op:
        batch_op.drop_column("detalle_ids_json")
