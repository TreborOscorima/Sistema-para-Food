"""add_companies — tabla food_companies + backfill de la empresa existente

Revision ID: 0013
Revises: 0012
Create Date: 2026-07-01

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0013"
down_revision: Union[str, None] = "0012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "food_companies",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("slug", sa.String(length=80), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("trial_ends_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug", name="uq_food_companies_slug"),
    )
    op.create_index("ix_food_companies_slug", "food_companies", ["slug"])

    conn = op.get_bind()

    # Backfill: la empresa que ya existe hoy (deployment single-tenant, FOOD_COMPANY_ID=1)
    # se convierte en la primera fila real de food_companies. Idempotente: no duplica
    # si la migración corre dos veces o si ya existe una empresa con id=1.
    existing = conn.execute(
        sa.text("SELECT COUNT(*) FROM food_companies WHERE id = 1")
    ).scalar()
    if not existing:
        row = conn.execute(
            sa.text(
                "SELECT nombre_local, slug FROM food_config_impresora "
                "WHERE company_id = 1 LIMIT 1"
            )
        ).fetchone()
        name = (row[0] if row and row[0] else "Restaurante 1").strip() or "Restaurante 1"
        slug = (row[1] if row and row[1] else "restaurante-1").strip() or "restaurante-1"
        conn.execute(
            sa.text(
                "INSERT INTO food_companies (id, name, slug, is_active) "
                "VALUES (1, :name, :slug, 1)"
            ),
            {"name": name, "slug": slug},
        )
        conn.execute(sa.text("ALTER TABLE food_companies AUTO_INCREMENT = 2"))


def downgrade() -> None:
    op.drop_table("food_companies")
