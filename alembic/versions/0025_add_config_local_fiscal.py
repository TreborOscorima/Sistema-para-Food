"""add fiscal/ticket config fields to ConfigImpresora

Revision ID: 0025
Revises: 0024
Create Date: 2026-07-03

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0025"
down_revision: Union[str, None] = "0024"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "food_config_impresora",
        sa.Column("ruc", sa.String(30), nullable=False, server_default=""),
    )
    op.add_column(
        "food_config_impresora",
        sa.Column("sucursal", sa.String(80), nullable=False, server_default=""),
    )
    op.add_column(
        "food_config_impresora",
        sa.Column("direccion", sa.String(160), nullable=False, server_default=""),
    )
    op.add_column(
        "food_config_impresora",
        sa.Column("telefono", sa.String(40), nullable=False, server_default=""),
    )
    op.add_column(
        "food_config_impresora",
        sa.Column(
            "mensaje_ticket",
            sa.String(200),
            nullable=False,
            server_default="¡Gracias por su preferencia!",
        ),
    )
    op.add_column(
        "food_config_impresora",
        sa.Column("mostrar_iva", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "food_config_impresora",
        sa.Column("porcentaje_iva", sa.Float(), nullable=False, server_default="18.0"),
    )


def downgrade() -> None:
    op.drop_column("food_config_impresora", "porcentaje_iva")
    op.drop_column("food_config_impresora", "mostrar_iva")
    op.drop_column("food_config_impresora", "mensaje_ticket")
    op.drop_column("food_config_impresora", "telefono")
    op.drop_column("food_config_impresora", "direccion")
    op.drop_column("food_config_impresora", "sucursal")
    op.drop_column("food_config_impresora", "ruc")
