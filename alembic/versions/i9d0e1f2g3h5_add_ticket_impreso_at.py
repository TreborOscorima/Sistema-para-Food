"""add ticket_impreso_at — dedupe global de impresión de comandas

Marca en cada línea de pedido si su comanda ya se imprimió en papel, para que
cada comanda salga UNA sola vez sin importar cuántas pantallas (Caja,
/estacion-impresion) estén imprimiendo a la vez.

Backfill: las líneas YA enviadas a cocina (impreso_cocina=1) se marcan como
impresas, para que al desplegar NO se reimprima todo el historial. Las líneas
aún no enviadas (impreso_cocina=0) quedan en NULL y se imprimirán cuando el
mozo las envíe.

Revision ID: i9d0e1f2g3h5
Revises: h8c9d0e1f2g4
Create Date: 2026-08-03

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "i9d0e1f2g3h5"
down_revision: Union[str, None] = "h8c9d0e1f2g4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(table: str, column: str) -> bool:
    conn = op.get_bind()
    result = conn.execute(
        sa.text(
            "SELECT COUNT(*) FROM information_schema.columns "
            "WHERE table_name = :table AND column_name = :col"
        ),
        {"table": table, "col": column},
    )
    return result.scalar() > 0


def upgrade() -> None:
    if not _column_exists("food_detalle_pedidos", "ticket_impreso_at"):
        op.add_column(
            "food_detalle_pedidos",
            sa.Column("ticket_impreso_at", sa.DateTime(), nullable=True),
        )
        # No reimprimir comandas ya enviadas antes de este deploy.
        op.execute(
            "UPDATE food_detalle_pedidos "
            "SET ticket_impreso_at = UTC_TIMESTAMP() "
            "WHERE impreso_cocina = 1 AND ticket_impreso_at IS NULL"
        )
        op.create_index(
            "ix_food_detalle_pedidos_ticket_impreso_at",
            "food_detalle_pedidos",
            ["ticket_impreso_at"],
        )


def downgrade() -> None:
    op.drop_index(
        "ix_food_detalle_pedidos_ticket_impreso_at",
        table_name="food_detalle_pedidos",
    )
    op.drop_column("food_detalle_pedidos", "ticket_impreso_at")
