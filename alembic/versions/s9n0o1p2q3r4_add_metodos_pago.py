"""métodos de pago configurables por empresa (Yape, Plin, Tarjeta…)

Revision ID: s9n0o1p2q3r4
Revises: r8m9n0o1p2q3
Create Date: 2026-08-17 06:00:00.000000

Crea `food_metodos_pago` y siembra el set por defecto (Perú) para cada empresa
existente. Los pagos siguen guardando su `codigo` en `food_pagos_pedido.metodo`
y `food_pedidos.metodo_pago` (columnas ya existentes, sin cambios de esquema);
esta tabla solo define qué métodos se ofrecen y en qué balde del cierre caen.

`qr` se siembra INACTIVO: no se ofrece como botón, pero da nombre/tipo a los
pagos históricos guardados como "qr" antes de esta función.
"""
from __future__ import annotations

from datetime import datetime
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 's9n0o1p2q3r4'
down_revision: Union[str, None] = 'r8m9n0o1p2q3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# (codigo, nombre, tipo, icono, permite_vuelto, activo, orden)
_DEFAULTS = [
    ("efectivo", "Efectivo", "efectivo", "💵", True, True, 1),
    ("yape", "Yape", "digital", "📱", False, True, 2),
    ("plin", "Plin", "digital", "📲", False, True, 3),
    ("tarjeta", "Tarjeta", "tarjeta", "💳", False, True, 4),
    ("transferencia", "Transferencia", "digital", "🏦", False, True, 5),
    ("fiado", "Fiado / Cuenta", "fiado", "📒", False, True, 6),
    ("qr", "QR", "digital", "🔳", False, False, 99),
]


def upgrade() -> None:
    op.create_table(
        "food_metodos_pago",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("codigo", sa.String(length=24), nullable=False),
        sa.Column("nombre", sa.String(length=40), nullable=False),
        sa.Column("tipo", sa.String(length=16), nullable=False, server_default="digital"),
        sa.Column("icono", sa.String(length=8), nullable=True),
        sa.Column("permite_vuelto", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("orden", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "company_id", "codigo", name="uq_food_metodos_pago_company_codigo"
        ),
    )
    op.create_index(
        "ix_food_metodos_pago_company_id", "food_metodos_pago", ["company_id"]
    )
    op.create_index("ix_food_metodos_pago_codigo", "food_metodos_pago", ["codigo"])
    op.create_index("ix_food_metodos_pago_activo", "food_metodos_pago", ["activo"])

    # Siembra los defaults para cada empresa existente.
    conn = op.get_bind()
    company_ids = [
        r[0] for r in conn.execute(sa.text("SELECT id FROM food_companies")).all()
    ]
    ahora = datetime.utcnow().replace(microsecond=0)
    for cid in company_ids:
        for codigo, nombre, tipo, icono, vuelto, activo, orden in _DEFAULTS:
            conn.execute(
                sa.text(
                    "INSERT INTO food_metodos_pago "
                    "(company_id, codigo, nombre, tipo, icono, permite_vuelto, "
                    " activo, orden, created_at, updated_at) VALUES "
                    "(:cid, :codigo, :nombre, :tipo, :icono, :vuelto, :activo, "
                    " :orden, :ts, :ts)"
                ),
                {
                    "cid": cid,
                    "codigo": codigo,
                    "nombre": nombre,
                    "tipo": tipo,
                    "icono": icono,
                    "vuelto": vuelto,
                    "activo": activo,
                    "orden": orden,
                    "ts": ahora,
                },
            )


def downgrade() -> None:
    op.drop_index("ix_food_metodos_pago_activo", table_name="food_metodos_pago")
    op.drop_index("ix_food_metodos_pago_codigo", table_name="food_metodos_pago")
    op.drop_index("ix_food_metodos_pago_company_id", table_name="food_metodos_pago")
    op.drop_table("food_metodos_pago")
