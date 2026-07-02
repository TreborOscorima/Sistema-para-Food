"""add_turnos_caja — turnos de caja con arqueo + movimientos de efectivo

Revision ID: 0018
Revises: 0017
Create Date: 2026-07-02

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0018"
down_revision: Union[str, None] = "0017"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "food_turnos_caja",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("abierto_por_id", sa.Integer(), nullable=True),
        sa.Column("cerrado_por_id", sa.Integer(), nullable=True),
        sa.Column("estado", sa.String(length=16), nullable=False, server_default="abierto"),
        sa.Column("monto_inicial", sa.Numeric(10, 2), nullable=False, server_default="0.00"),
        sa.Column("abierto_en", sa.DateTime(), nullable=False),
        sa.Column("cerrado_en", sa.DateTime(), nullable=True),
        sa.Column("total_efectivo", sa.Numeric(10, 2), nullable=False, server_default="0.00"),
        sa.Column("total_tarjeta", sa.Numeric(10, 2), nullable=False, server_default="0.00"),
        sa.Column("total_qr", sa.Numeric(10, 2), nullable=False, server_default="0.00"),
        sa.Column("total_fiado", sa.Numeric(10, 2), nullable=False, server_default="0.00"),
        sa.Column("total_propinas", sa.Numeric(10, 2), nullable=False, server_default="0.00"),
        sa.Column("total_ingresos", sa.Numeric(10, 2), nullable=False, server_default="0.00"),
        sa.Column("total_egresos", sa.Numeric(10, 2), nullable=False, server_default="0.00"),
        sa.Column("esperado_efectivo", sa.Numeric(10, 2), nullable=False, server_default="0.00"),
        sa.Column("contado_efectivo", sa.Numeric(10, 2), nullable=False, server_default="0.00"),
        sa.Column("descuadre", sa.Numeric(10, 2), nullable=False, server_default="0.00"),
        sa.Column("arqueo_detalle", sa.String(length=1000), nullable=True),
        sa.Column("notas_cierre", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["abierto_por_id"], ["food_usuarios.id"]),
        sa.ForeignKeyConstraint(["cerrado_por_id"], ["food_usuarios.id"]),
    )
    op.create_index("ix_food_turnos_caja_company_id", "food_turnos_caja", ["company_id"])
    op.create_index("ix_food_turnos_caja_estado", "food_turnos_caja", ["estado"])
    op.create_index("ix_food_turnos_caja_abierto_por_id", "food_turnos_caja", ["abierto_por_id"])

    op.create_table(
        "food_movimientos_caja",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("turno_id", sa.Integer(), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=True),
        sa.Column("tipo", sa.String(length=10), nullable=False),
        sa.Column("categoria", sa.String(length=40), nullable=False, server_default="Otros"),
        sa.Column("monto", sa.Numeric(10, 2), nullable=False, server_default="0.00"),
        sa.Column("motivo", sa.String(length=240), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["turno_id"], ["food_turnos_caja.id"]),
        sa.ForeignKeyConstraint(["usuario_id"], ["food_usuarios.id"]),
    )
    op.create_index("ix_food_movimientos_caja_company_id", "food_movimientos_caja", ["company_id"])
    op.create_index("ix_food_movimientos_caja_turno_id", "food_movimientos_caja", ["turno_id"])

    op.add_column(
        "food_pedidos",
        sa.Column("turno_caja_id", sa.Integer(), nullable=True),
    )
    op.create_index("ix_food_pedidos_turno_caja_id", "food_pedidos", ["turno_caja_id"])
    op.create_foreign_key(
        "fk_food_pedidos_turno_caja_id",
        "food_pedidos",
        "food_turnos_caja",
        ["turno_caja_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_food_pedidos_turno_caja_id", "food_pedidos", type_="foreignkey")
    op.drop_index("ix_food_pedidos_turno_caja_id", table_name="food_pedidos")
    op.drop_column("food_pedidos", "turno_caja_id")
    op.drop_index("ix_food_movimientos_caja_turno_id", table_name="food_movimientos_caja")
    op.drop_index("ix_food_movimientos_caja_company_id", table_name="food_movimientos_caja")
    op.drop_table("food_movimientos_caja")
    op.drop_index("ix_food_turnos_caja_abierto_por_id", table_name="food_turnos_caja")
    op.drop_index("ix_food_turnos_caja_estado", table_name="food_turnos_caja")
    op.drop_index("ix_food_turnos_caja_company_id", table_name="food_turnos_caja")
    op.drop_table("food_turnos_caja")
