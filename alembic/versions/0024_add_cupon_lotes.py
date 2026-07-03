"""add_cupon_lotes — cupones por código de lote para apertura, fidelidad, marketing

Revision ID: 0024
Revises: 0023
Create Date: 2026-07-03

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0024"
down_revision: Union[str, None] = "0023"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS food_cupon_lotes (
            id INTEGER NOT NULL AUTO_INCREMENT,
            company_id INTEGER NOT NULL,
            nombre VARCHAR(120) NOT NULL,
            codigo VARCHAR(40) NOT NULL,
            tipo VARCHAR(20) NOT NULL,
            valor NUMERIC(10, 2) NOT NULL DEFAULT '0.00',
            fecha_inicio DATE,
            fecha_fin DATE,
            usos_max INTEGER,
            usos_actuales INTEGER NOT NULL DEFAULT 0,
            activo BOOL NOT NULL DEFAULT 1,
            created_at DATETIME NOT NULL DEFAULT (NOW()),
            updated_at DATETIME NOT NULL DEFAULT (NOW()),
            PRIMARY KEY (id),
            CONSTRAINT uq_food_cupon_lotes_company_codigo UNIQUE (company_id, codigo),
            INDEX ix_food_cupon_lotes_company_id (company_id)
        )
    """)


def downgrade() -> None:
    op.drop_table("food_cupon_lotes")
