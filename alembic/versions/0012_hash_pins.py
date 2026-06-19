"""hash_pins — hashear PINs existentes con bcrypt, ampliar columna

Revision ID: 0012
Revises: 0011
Create Date: 2026-06-19

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0012"
down_revision: Union[str, None] = "0011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    import bcrypt

    conn = op.get_bind()

    # 1. Eliminar unique constraint que ya no aplica (cada bcrypt hash es único por salt)
    #    Nombre real en DB según 0001: uq_food_usuario_pin_company
    result = conn.execute(
        sa.text(
            "SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS "
            "WHERE TABLE_SCHEMA = DATABASE() "
            "AND TABLE_NAME = 'food_usuarios' "
            "AND CONSTRAINT_NAME = 'uq_food_usuario_pin_company'"
        )
    ).scalar()
    if result:
        op.drop_constraint("uq_food_usuario_pin_company", "food_usuarios", type_="unique")

    # 2. Ampliar columna pin a 72 chars (bcrypt hash ~60 chars)
    op.alter_column(
        "food_usuarios",
        "pin",
        existing_type=sa.String(length=6),
        type_=sa.String(length=72),
        existing_nullable=False,
    )

    # 3. Hashear PINs en texto plano (los que no comiencen con $2b$ ya están hasheados)
    rows = conn.execute(sa.text("SELECT id, pin FROM food_usuarios")).fetchall()
    for row in rows:
        plain = row[1]
        if not plain.startswith("$2b$"):
            hashed = bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()
            conn.execute(
                sa.text("UPDATE food_usuarios SET pin = :h WHERE id = :id"),
                {"h": hashed, "id": row[0]},
            )


def downgrade() -> None:
    # No reversible: no podemos recuperar PINs en texto plano desde bcrypt
    raise NotImplementedError(
        "Downgrade de 0012 no soportado: los PINs en texto plano no son recuperables."
    )
