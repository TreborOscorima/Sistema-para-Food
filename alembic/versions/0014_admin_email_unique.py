"""admin_email_unique — email de admin y slug publico unicos globalmente

Revision ID: 0014
Revises: 0013
Create Date: 2026-07-01

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0014"
down_revision: Union[str, None] = "0013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # Guardas previas: si algún día dos empresas comparten admin_email o slug
    # (colisión legítima o dato de prueba sucio), esta migración debe fallar
    # ruidosamente en vez de aplicar una constraint que la DB ya no cumple.
    dup_emails = conn.execute(
        sa.text(
            "SELECT admin_email, COUNT(*) c FROM food_config_impresora "
            "WHERE admin_email != '' GROUP BY admin_email HAVING c > 1"
        )
    ).fetchall()
    if dup_emails:
        raise RuntimeError(
            f"admin_email duplicado en food_config_impresora: {[r[0] for r in dup_emails]}. "
            "Resolvé el duplicado a mano antes de correr esta migración."
        )

    dup_slugs = conn.execute(
        sa.text(
            "SELECT slug, COUNT(*) c FROM food_config_impresora "
            "GROUP BY slug HAVING c > 1"
        )
    ).fetchall()
    if dup_slugs:
        raise RuntimeError(
            f"slug duplicado en food_config_impresora: {[r[0] for r in dup_slugs]}. "
            "Resolvé el duplicado a mano antes de correr esta migración."
        )

    op.create_unique_constraint(
        "uq_food_config_impresora_admin_email", "food_config_impresora", ["admin_email"]
    )
    op.create_unique_constraint(
        "uq_food_config_impresora_slug", "food_config_impresora", ["slug"]
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_food_config_impresora_slug", "food_config_impresora", type_="unique"
    )
    op.drop_constraint(
        "uq_food_config_impresora_admin_email", "food_config_impresora", type_="unique"
    )
