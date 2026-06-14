"""add config_impresora table

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-14

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "food_config_impresora",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("nombre_local", sa.String(length=120), nullable=False, server_default="Mi Restaurante"),
        sa.Column("cocina_activa", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("cocina_ip", sa.String(length=64), nullable=False, server_default="192.168.1.100"),
        sa.Column("cocina_puerto", sa.Integer(), nullable=False, server_default="9100"),
        sa.Column("caja_activa", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("caja_ip", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("caja_puerto", sa.Integer(), nullable=False, server_default="9100"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", name="uq_food_config_impresora_company"),
    )
    op.create_index(
        op.f("ix_food_config_impresora_company_id"),
        "food_config_impresora",
        ["company_id"],
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_food_config_impresora_company_id"), table_name="food_config_impresora")
    op.drop_table("food_config_impresora")
