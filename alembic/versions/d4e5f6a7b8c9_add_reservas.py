"""add food_reservas table

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-07-09 00:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(name: str) -> bool:
    conn = op.get_bind()
    insp = sa.inspect(conn)
    return name in insp.get_table_names()


def upgrade() -> None:
    if not _has_table("food_reservas"):
        op.create_table(
            "food_reservas",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("company_id", sa.Integer(), nullable=False, index=True),
            sa.Column("sucursal_id", sa.Integer(), nullable=True, index=True),
            sa.Column("mesa_id", sa.Integer(), nullable=True, index=True),
            sa.Column("cliente_id", sa.Integer(), nullable=True, index=True),
            sa.Column("nombre_cliente", sa.String(120), nullable=False),
            sa.Column("telefono", sa.String(20), nullable=False, server_default=""),
            sa.Column("fecha", sa.Date(), nullable=False, index=True),
            sa.Column("hora", sa.String(5), nullable=False),
            sa.Column("pax", sa.Integer(), nullable=False, server_default="2"),
            sa.Column("estado", sa.String(20), nullable=False, server_default="pendiente", index=True),
            sa.Column("notas", sa.String(240), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["sucursal_id"], ["food_sucursales.id"], name="fk_food_reservas_sucursal"),
            sa.ForeignKeyConstraint(["mesa_id"], ["food_mesas.id"], name="fk_food_reservas_mesa"),
            sa.ForeignKeyConstraint(["cliente_id"], ["food_clientes.id"], name="fk_food_reservas_cliente"),
        )


def downgrade() -> None:
    if _has_table("food_reservas"):
        op.drop_table("food_reservas")
