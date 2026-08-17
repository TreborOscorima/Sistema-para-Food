"""país de operación por empresa (zona horaria de reportes)

Revision ID: t0o1p2q3r4s5
Revises: s9n0o1p2q3r4
Create Date: 2026-08-17 07:30:00.000000

Agrega `food_config_impresora.pais` (código ISO-2, default 'PE'). Define la zona
horaria con la que los reportes/turnos agrupan por día local, para soportar el
uso del sistema en distintos países (Perú, Argentina, Chile…). Las empresas
existentes quedan en 'PE' (comportamiento actual, sin cambios).
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 't0o1p2q3r4s5'
down_revision: Union[str, None] = 's9n0o1p2q3r4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "food_config_impresora",
        sa.Column(
            "pais", sa.String(length=4), nullable=False, server_default="PE"
        ),
    )


def downgrade() -> None:
    op.drop_column("food_config_impresora", "pais")
