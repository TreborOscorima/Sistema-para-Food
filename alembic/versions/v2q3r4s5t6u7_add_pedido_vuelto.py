"""add_pedido_vuelto — persistir el vuelto del cobro en el pedido

Revision ID: v2q3r4s5t6u7
Revises: u1p2q3r4s5t6
Create Date: 2026-08-29

Agrega `food_pedidos.vuelto`: el vuelto entregado al cliente en el cobro (sale
solo del efectivo). Antes solo se calculaba en el momento del cobro y no se
guardaba —el efectivo se persiste neto de vuelto en food_pagos_pedido—, así que
al REIMPRIMIR el comprobante el vuelto se había perdido. Con esta columna el
comprobante puede mostrar el vuelto tanto al cobrar como en reimpresiones.
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "v2q3r4s5t6u7"
down_revision: Union[str, None] = "u1p2q3r4s5t6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "food_pedidos",
        sa.Column(
            "vuelto",
            sa.Numeric(10, 2),
            nullable=False,
            server_default="0.00",
        ),
    )


def downgrade() -> None:
    op.drop_column("food_pedidos", "vuelto")
