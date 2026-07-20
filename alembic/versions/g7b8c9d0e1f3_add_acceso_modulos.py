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


def upgrade() -> None:
    op.add_column(
        "food_usuarios",
        sa.Column("acceso_mozos", sa.Boolean(), nullable=False, server_default=sa.text("0")),
    )
    op.add_column(
        "food_usuarios",
        sa.Column("acceso_caja", sa.Boolean(), nullable=False, server_default=sa.text("0")),
    )
    op.add_column(
        "food_usuarios",
        sa.Column("acceso_cocina", sa.Boolean(), nullable=False, server_default=sa.text("0")),
    )
    op.add_column(
        "food_usuarios",
        sa.Column("acceso_mostrador", sa.Boolean(), nullable=False, server_default=sa.text("0")),
    )
    op.execute("UPDATE food_usuarios SET acceso_mozos=1 WHERE rol='Mozo'")
    op.execute("UPDATE food_usuarios SET acceso_caja=1, acceso_mostrador=1 WHERE rol='Caja'")
    op.execute("UPDATE food_usuarios SET acceso_cocina=1 WHERE rol='Cocina'")
    op.execute(
        "UPDATE food_usuarios SET acceso_mozos=1, acceso_caja=1, acceso_cocina=1, acceso_mostrador=1 WHERE rol='Admin'"
    )


def downgrade() -> None:
    op.drop_column("food_usuarios", "acceso_mostrador")
    op.drop_column("food_usuarios", "acceso_cocina")
    op.drop_column("food_usuarios", "acceso_caja")
    op.drop_column("food_usuarios", "acceso_mozos")
