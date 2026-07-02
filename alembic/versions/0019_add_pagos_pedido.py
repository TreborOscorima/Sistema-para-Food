"""add_pagos_pedido — pagos múltiples por pedido (pago mixto / cuenta dividida)

Revision ID: 0019
Revises: 0018
Create Date: 2026-07-02

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0019"
down_revision: Union[str, None] = "0018"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "food_pagos_pedido",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("pedido_id", sa.Integer(), nullable=False),
        sa.Column("turno_caja_id", sa.Integer(), nullable=True),
        sa.Column("usuario_id", sa.Integer(), nullable=True),
        sa.Column("metodo", sa.String(length=24), nullable=False),
        sa.Column("monto", sa.Numeric(10, 2), nullable=False, server_default="0.00"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["pedido_id"], ["food_pedidos.id"]),
        sa.ForeignKeyConstraint(["turno_caja_id"], ["food_turnos_caja.id"]),
        sa.ForeignKeyConstraint(["usuario_id"], ["food_usuarios.id"]),
    )
    op.create_index("ix_food_pagos_pedido_company_id", "food_pagos_pedido", ["company_id"])
    op.create_index("ix_food_pagos_pedido_pedido_id", "food_pagos_pedido", ["pedido_id"])
    op.create_index("ix_food_pagos_pedido_turno_caja_id", "food_pagos_pedido", ["turno_caja_id"])


def downgrade() -> None:
    op.drop_index("ix_food_pagos_pedido_turno_caja_id", table_name="food_pagos_pedido")
    op.drop_index("ix_food_pagos_pedido_pedido_id", table_name="food_pagos_pedido")
    op.drop_index("ix_food_pagos_pedido_company_id", table_name="food_pagos_pedido")
    op.drop_table("food_pagos_pedido")
