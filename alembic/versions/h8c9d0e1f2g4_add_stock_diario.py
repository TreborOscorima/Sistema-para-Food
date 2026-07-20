"""add stock_diario — control de stock diario de productos terminados

Revision ID: h8c9d0e1f2g4
Revises: g7b8c9d0e1f3
Create Date: 2026-07-20

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "h8c9d0e1f2g4"
down_revision: Union[str, None] = "g7b8c9d0e1f3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(table: str, column: str) -> bool:
    conn = op.get_bind()
    result = conn.execute(
        sa.text(
            "SELECT COUNT(*) FROM information_schema.columns "
            "WHERE table_name = :table AND column_name = :col"
        ),
        {"table": table, "col": column},
    )
    return result.scalar() > 0


def upgrade() -> None:
    if not _column_exists("food_productos", "stock_diario"):
        op.add_column(
            "food_productos",
            sa.Column("stock_diario", sa.Integer(), nullable=True),
        )
    if not _column_exists("food_productos", "stock_diario_alerta"):
        op.add_column(
            "food_productos",
            sa.Column(
                "stock_diario_alerta",
                sa.Integer(),
                nullable=False,
                server_default=sa.text("5"),
            ),
        )


def downgrade() -> None:
    op.drop_column("food_productos", "stock_diario_alerta")
    op.drop_column("food_productos", "stock_diario")
