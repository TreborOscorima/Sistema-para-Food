"""add_composite_indexes — índices compuestos para queries calientes de polling

Revision ID: f1a2b3c4d5e6
Revises: e8f1a2b3c4d5
Create Date: 2026-07-07

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f1a2b3c4d5e6"
down_revision: Union[str, None] = "e8f1a2b3c4d5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_index(
        "ix_food_pedidos_company_estado",
        "food_pedidos",
        ["company_id", "estado"],
    )
    op.create_index(
        "ix_food_pedidos_company_cerrado_en",
        "food_pedidos",
        ["company_id", "cerrado_en"],
    )
    op.create_index(
        "ix_food_detalle_pedidos_company_estado_prod",
        "food_detalle_pedidos",
        ["company_id", "estado_produccion"],
    )
    op.create_index(
        "ix_food_detalle_pedidos_pedido_estado_prod",
        "food_detalle_pedidos",
        ["pedido_id", "estado_produccion"],
    )


def downgrade() -> None:
    op.drop_index("ix_food_detalle_pedidos_pedido_estado_prod", "food_detalle_pedidos")
    op.drop_index("ix_food_detalle_pedidos_company_estado_prod", "food_detalle_pedidos")
    op.drop_index("ix_food_pedidos_company_cerrado_en", "food_pedidos")
    op.drop_index("ix_food_pedidos_company_estado", "food_pedidos")
