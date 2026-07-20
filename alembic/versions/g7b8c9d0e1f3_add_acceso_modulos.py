"""add acceso_modulos — campos de acceso multi-módulo independiente del rol

Revision ID: g7b8c9d0e1f3
Revises: f6a7b8c9d0e1
Create Date: 2026-07-18

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "g7b8c9d0e1f3"
down_revision: Union[str, None] = "f6a7b8c9d0e1"
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
    cols = [
        ("acceso_mozos", sa.Boolean(), sa.text("0")),
        ("acceso_caja", sa.Boolean(), sa.text("0")),
        ("acceso_cocina", sa.Boolean(), sa.text("0")),
        ("acceso_mostrador", sa.Boolean(), sa.text("0")),
    ]
    for name, type_, default in cols:
        if not _column_exists("food_usuarios", name):
            op.add_column(
                "food_usuarios",
                sa.Column(name, type_, nullable=False, server_default=default),
            )

    op.execute("UPDATE food_usuarios SET acceso_mozos=1 WHERE rol='Mozo' AND acceso_mozos=0")
    op.execute("UPDATE food_usuarios SET acceso_caja=1, acceso_mostrador=1 WHERE rol='Caja' AND acceso_caja=0")
    op.execute("UPDATE food_usuarios SET acceso_cocina=1 WHERE rol='Cocina' AND acceso_cocina=0")
    op.execute(
        "UPDATE food_usuarios SET acceso_mozos=1, acceso_caja=1, acceso_cocina=1, acceso_mostrador=1 "
        "WHERE rol='Admin' AND acceso_mozos=0"
    )


def downgrade() -> None:
    op.drop_column("food_usuarios", "acceso_mostrador")
    op.drop_column("food_usuarios", "acceso_cocina")
    op.drop_column("food_usuarios", "acceso_caja")
    op.drop_column("food_usuarios", "acceso_mozos")
