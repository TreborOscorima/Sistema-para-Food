"""add modificadores tables

Revision ID: 72325b029491
Revises: c6c6d83f95dd
Create Date: 2026-07-06 05:37:19.434612

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel

revision: str = '72325b029491'
down_revision: Union[str, None] = 'c6c6d83f95dd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(name: str) -> bool:
    conn = op.get_bind()
    insp = sa.inspect(conn)
    return name in insp.get_table_names()


def _has_column(table: str, column: str) -> bool:
    conn = op.get_bind()
    insp = sa.inspect(conn)
    return any(c["name"] == column for c in insp.get_columns(table))


def upgrade() -> None:
    if not _table_exists("food_grupo_modificadores"):
        op.create_table(
            "food_grupo_modificadores",
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("company_id", sa.Integer(), nullable=False),
            sa.Column("nombre", sqlmodel.sql.sqltypes.AutoString(length=120), nullable=False),
            sa.Column("min_selecciones", sa.Integer(), nullable=False),
            sa.Column("max_selecciones", sa.Integer(), nullable=False),
            sa.Column("activo", sa.Boolean(), nullable=False),
            sa.Column("orden", sa.Integer(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        with op.batch_alter_table("food_grupo_modificadores") as batch_op:
            batch_op.create_index("ix_food_grupo_modificadores_company_id", ["company_id"], unique=False)

    if not _table_exists("food_opcion_modificadores"):
        op.create_table(
            "food_opcion_modificadores",
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("company_id", sa.Integer(), nullable=False),
            sa.Column("grupo_id", sa.Integer(), nullable=False),
            sa.Column("nombre", sqlmodel.sql.sqltypes.AutoString(length=120), nullable=False),
            sa.Column("precio_extra", sa.Numeric(precision=10, scale=2), server_default="0.00", nullable=False),
            sa.Column("activo", sa.Boolean(), nullable=False),
            sa.Column("orden", sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(["grupo_id"], ["food_grupo_modificadores.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        with op.batch_alter_table("food_opcion_modificadores") as batch_op:
            batch_op.create_index("ix_food_opcion_modificadores_company_id", ["company_id"], unique=False)
            batch_op.create_index("ix_food_opcion_modificadores_grupo_id", ["grupo_id"], unique=False)

    if not _table_exists("food_producto_grupo_modificadores"):
        op.create_table(
            "food_producto_grupo_modificadores",
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.Column("id", sa.Integer(), nullable=False),
            sa.Column("producto_id", sa.Integer(), nullable=False),
            sa.Column("grupo_id", sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(["grupo_id"], ["food_grupo_modificadores.id"]),
            sa.ForeignKeyConstraint(["producto_id"], ["food_productos.id"]),
            sa.PrimaryKeyConstraint("id"),
        )
        with op.batch_alter_table("food_producto_grupo_modificadores") as batch_op:
            batch_op.create_index("ix_food_producto_grupo_modificadores_grupo_id", ["grupo_id"], unique=False)
            batch_op.create_index("ix_food_producto_grupo_modificadores_producto_id", ["producto_id"], unique=False)

    if not _has_column("food_detalle_pedidos", "modificadores_json"):
        with op.batch_alter_table("food_detalle_pedidos") as batch_op:
            batch_op.add_column(sa.Column("modificadores_json", sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("food_detalle_pedidos") as batch_op:
        batch_op.drop_column("modificadores_json")

    op.drop_table("food_producto_grupo_modificadores")
    op.drop_table("food_opcion_modificadores")
    op.drop_table("food_grupo_modificadores")
