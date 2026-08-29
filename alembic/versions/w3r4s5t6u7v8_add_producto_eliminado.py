"""add_producto_eliminado — borrado lógico de productos de la carta

Revision ID: w3r4s5t6u7v8
Revises: v2q3r4s5t6u7
Create Date: 2026-08-29

Agrega `food_productos.eliminado`: marca de archivado para productos que ya no
se venden. Un producto con historial de ventas no puede borrarse físicamente
(rompería `food_detalle_pedidos.producto_id` y los reportes), así que se
archiva: `eliminado = True` lo oculta de la carta y del POS conservando el
historial. Los productos sin ninguna referencia se borran de verdad y nunca
llegan a marcarse aquí.
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "w3r4s5t6u7v8"
down_revision: Union[str, None] = "v2q3r4s5t6u7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "food_productos",
        sa.Column(
            "eliminado",
            sa.Boolean(),
            nullable=False,
            server_default="0",
        ),
    )


def downgrade() -> None:
    op.drop_column("food_productos", "eliminado")
