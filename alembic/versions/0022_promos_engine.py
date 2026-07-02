"""promos_engine — días de semana, alcance producto/categoría, 2x1, auto-aplicación

Revision ID: 0022
Revises: 0021
Create Date: 2026-07-02

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0022"
down_revision: Union[str, None] = "0021"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "food_promociones",
        sa.Column("dias_semana_mask", sa.Integer(), nullable=False, server_default="127"),
    )
    op.add_column("food_promociones", sa.Column("producto_id", sa.Integer(), nullable=True))
    op.add_column("food_promociones", sa.Column("categoria_id", sa.Integer(), nullable=True))
    op.add_column(
        "food_promociones",
        sa.Column("auto_aplicar", sa.Boolean(), nullable=False, server_default="1"),
    )
    op.create_index("ix_food_promociones_producto_id", "food_promociones", ["producto_id"])
    op.create_index("ix_food_promociones_categoria_id", "food_promociones", ["categoria_id"])
    op.create_foreign_key(
        "fk_food_promociones_producto_id",
        "food_promociones", "food_productos", ["producto_id"], ["id"],
    )
    op.create_foreign_key(
        "fk_food_promociones_categoria_id",
        "food_promociones", "food_categorias", ["categoria_id"], ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_food_promociones_categoria_id", "food_promociones", type_="foreignkey")
    op.drop_constraint("fk_food_promociones_producto_id", "food_promociones", type_="foreignkey")
    op.drop_index("ix_food_promociones_categoria_id", table_name="food_promociones")
    op.drop_index("ix_food_promociones_producto_id", table_name="food_promociones")
    op.drop_column("food_promociones", "auto_aplicar")
    op.drop_column("food_promociones", "categoria_id")
    op.drop_column("food_promociones", "producto_id")
    op.drop_column("food_promociones", "dias_semana_mask")
