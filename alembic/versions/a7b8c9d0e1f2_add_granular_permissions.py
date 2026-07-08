"""add_granular_permissions — SEC-05: 4 nuevos permisos por usuario

Revision ID: a7b8c9d0e1f2
Revises: f1a2b3c4d5e6
Create Date: 2026-07-07

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a7b8c9d0e1f2"
down_revision: Union[str, None] = "f1a2b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "food_usuarios",
        sa.Column("perm_turno", sa.Boolean(), nullable=False, server_default=sa.text("0")),
    )
    op.add_column(
        "food_usuarios",
        sa.Column("perm_inventario", sa.Boolean(), nullable=False, server_default=sa.text("0")),
    )
    op.add_column(
        "food_usuarios",
        sa.Column("perm_costos", sa.Boolean(), nullable=False, server_default=sa.text("0")),
    )
    op.add_column(
        "food_usuarios",
        sa.Column("perm_reimprimir", sa.Boolean(), nullable=False, server_default=sa.text("0")),
    )
    # Admin users get all new permissions enabled by default
    op.execute(
        "UPDATE food_usuarios SET perm_turno=1, perm_inventario=1, perm_costos=1, perm_reimprimir=1 WHERE rol='Admin'"
    )
    # Caja users get turno + reimprimir by default
    op.execute(
        "UPDATE food_usuarios SET perm_turno=1, perm_reimprimir=1 WHERE rol='Caja'"
    )


def downgrade() -> None:
    op.drop_column("food_usuarios", "perm_reimprimir")
    op.drop_column("food_usuarios", "perm_costos")
    op.drop_column("food_usuarios", "perm_inventario")
    op.drop_column("food_usuarios", "perm_turno")
