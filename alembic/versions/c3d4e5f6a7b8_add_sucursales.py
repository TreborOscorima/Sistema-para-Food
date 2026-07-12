"""add food_sucursales table and sucursal_id to operational tables

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-07-09 00:00:00.000000

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(name: str) -> bool:
    conn = op.get_bind()
    insp = sa.inspect(conn)
    return name in insp.get_table_names()


def _has_column(table: str, column: str) -> bool:
    conn = op.get_bind()
    insp = sa.inspect(conn)
    return any(c["name"] == column for c in insp.get_columns(table))


def upgrade() -> None:
    if not _has_table("food_sucursales"):
        op.create_table(
            "food_sucursales",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("company_id", sa.Integer(), nullable=False, index=True),
            sa.Column("nombre", sa.String(120), nullable=False),
            sa.Column("direccion", sa.String(200), nullable=False, server_default=""),
            sa.Column("telefono", sa.String(40), nullable=False, server_default=""),
            sa.Column("activa", sa.Boolean(), nullable=False, server_default=sa.text("1")),
            sa.Column("es_principal", sa.Boolean(), nullable=False, server_default=sa.text("0")),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.UniqueConstraint("company_id", "nombre", name="uq_food_sucursales_company_nombre"),
        )

    _targets = [
        "food_usuarios",
        "food_mesas",
        "food_pedidos",
        "food_turnos_caja",
        "food_insumos",
    ]
    for table in _targets:
        if not _has_column(table, "sucursal_id"):
            op.add_column(
                table,
                sa.Column("sucursal_id", sa.Integer(), nullable=True, index=True),
            )
            op.create_foreign_key(
                f"fk_{table}_sucursal",
                table,
                "food_sucursales",
                ["sucursal_id"],
                ["id"],
            )


def downgrade() -> None:
    _targets = [
        "food_insumos",
        "food_turnos_caja",
        "food_pedidos",
        "food_mesas",
        "food_usuarios",
    ]
    for table in _targets:
        if _has_column(table, "sucursal_id"):
            op.drop_constraint(f"fk_{table}_sucursal", table, type_="foreignkey")
            op.drop_column(table, "sucursal_id")
    if _has_table("food_sucursales"):
        op.drop_table("food_sucursales")
