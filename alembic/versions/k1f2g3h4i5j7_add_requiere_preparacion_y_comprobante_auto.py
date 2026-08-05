"""add requiere_preparacion to detalle and comprobante_auto to config

Revision ID: k1f2g3h4i5j7
Revises: j0e1f2g3h4i6
Create Date: 2026-08-05 00:00:00.000000

Ruteo de preparación: los ítems que no se preparan (estación "ninguna") no
generan comanda ni van al KDS. Se snapshotea en food_detalle_pedidos. Además,
el comprobante de pago puede imprimirse "a demanda" (comprobante_auto=False).

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect as sa_inspect

# revision identifiers, used by Alembic.
revision: str = 'k1f2g3h4i5j7'
down_revision: Union[str, None] = 'j0e1f2g3h4i6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(conn, table: str, column: str) -> bool:
    insp = sa_inspect(conn)
    return any(c["name"] == column for c in insp.get_columns(table))


def upgrade() -> None:
    conn = op.get_bind()
    # Filas existentes = productos que sí se preparaban → default True (backfill).
    if not _has_column(conn, 'food_detalle_pedidos', 'requiere_preparacion'):
        op.add_column(
            'food_detalle_pedidos',
            sa.Column(
                'requiere_preparacion',
                sa.Boolean(),
                server_default=sa.text('1'),
                nullable=False,
            ),
        )
    if not _has_column(conn, 'food_config_impresora', 'comprobante_auto'):
        op.add_column(
            'food_config_impresora',
            sa.Column(
                'comprobante_auto',
                sa.Boolean(),
                server_default=sa.text('1'),
                nullable=False,
            ),
        )


def downgrade() -> None:
    conn = op.get_bind()
    if _has_column(conn, 'food_config_impresora', 'comprobante_auto'):
        op.drop_column('food_config_impresora', 'comprobante_auto')
    if _has_column(conn, 'food_detalle_pedidos', 'requiere_preparacion'):
        op.drop_column('food_detalle_pedidos', 'requiere_preparacion')
