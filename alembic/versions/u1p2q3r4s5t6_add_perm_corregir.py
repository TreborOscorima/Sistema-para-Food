"""add_perm_corregir — permiso para corregir cobros ya confirmados

Revision ID: u1p2q3r4s5t6
Revises: t0o1p2q3r4s5
Create Date: 2026-08-19

Agrega `food_usuarios.perm_corregir`: habilita la corrección de un cobro ya
confirmado (quitar/sumar ítems, cambiar método de pago, ajustar descuento)
sobre la misma venta, sin anularla ni duplicarla. Los usuarios Admin lo reciben
activo por defecto; el resto queda en 0 (se configura por usuario).
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "u1p2q3r4s5t6"
down_revision: Union[str, None] = "t0o1p2q3r4s5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "food_usuarios",
        sa.Column("perm_corregir", sa.Boolean(), nullable=False, server_default=sa.text("0")),
    )
    # Los Admin corrigen cobros por defecto
    op.execute("UPDATE food_usuarios SET perm_corregir=1 WHERE rol='Admin'")


def downgrade() -> None:
    op.drop_column("food_usuarios", "perm_corregir")
