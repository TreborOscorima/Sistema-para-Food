"""add food_auditoria table

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-07-08 00:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)
    if "food_auditoria" not in insp.get_table_names():
        op.create_table(
            "food_auditoria",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("company_id", sa.Integer(), nullable=False, index=True),
            sa.Column("usuario_id", sa.Integer(), nullable=True, index=True),
            sa.Column("usuario_nombre", sa.String(120), nullable=False, server_default=""),
            sa.Column("accion", sa.String(60), nullable=False, index=True),
            sa.Column("entidad", sa.String(60), nullable=False, server_default=""),
            sa.Column("entidad_id", sa.Integer(), nullable=True),
            sa.Column("detalle", sa.Text(), nullable=True),
            sa.Column("ip", sa.String(45), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
        )


def downgrade() -> None:
    conn = op.get_bind()
    insp = sa.inspect(conn)
    if "food_auditoria" in insp.get_table_names():
        op.drop_table("food_auditoria")
