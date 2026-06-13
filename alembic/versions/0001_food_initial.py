"""food initial schema

Revision ID: 0001
Revises:
Create Date: 2026-06-13

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "food_usuarios",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(length=120), nullable=False),
        sa.Column("pin", sa.String(length=6), nullable=False),
        sa.Column("rol", sa.String(length=20), nullable=False),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", "pin", name="uq_food_usuario_pin_company"),
    )
    op.create_index("ix_food_usuarios_company_id", "food_usuarios", ["company_id"])

    op.create_table(
        "food_mesas",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("numero", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(length=80), nullable=True),
        sa.Column("capacidad", sa.Integer(), nullable=False, server_default="4"),
        sa.Column("estado", sa.String(length=30), nullable=False, server_default="libre"),
        sa.Column("activa", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("company_id", "numero", name="uq_food_mesa_numero_company"),
    )
    op.create_index("ix_food_mesas_company_id", "food_mesas", ["company_id"])

    op.create_table(
        "food_categorias",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(length=120), nullable=False),
        sa.Column("descripcion", sa.String(length=255), nullable=True),
        sa.Column("orden", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("activa", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_food_categorias_company_id", "food_categorias", ["company_id"])

    op.create_table(
        "food_productos",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("categoria_id", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(length=160), nullable=False),
        sa.Column("descripcion", sa.String(length=255), nullable=True),
        sa.Column("precio", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("disponible", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["categoria_id"], ["food_categorias.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_food_productos_company_id", "food_productos", ["company_id"])
    op.create_index("ix_food_productos_categoria_id", "food_productos", ["categoria_id"])

    op.create_table(
        "food_pedidos",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("mesa_id", sa.Integer(), nullable=True),
        sa.Column("mozo_id", sa.Integer(), nullable=True),
        sa.Column("cajero_id", sa.Integer(), nullable=True),
        sa.Column("tipo_pedido", sa.String(length=20), nullable=False, server_default="Mesa"),
        sa.Column("nombre_cliente", sa.String(length=120), nullable=True),
        sa.Column("pagado", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("estado", sa.String(length=30), nullable=False, server_default="borrador"),
        sa.Column("total", sa.Numeric(precision=10, scale=2), nullable=False, server_default="0.00"),
        sa.Column("notas", sa.Text(), nullable=True),
        sa.Column("abierto_en", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("cerrado_en", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["mesa_id"], ["food_mesas.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["mozo_id"], ["food_usuarios.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["cajero_id"], ["food_usuarios.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_food_pedidos_company_id", "food_pedidos", ["company_id"])
    op.create_index("ix_food_pedidos_mesa_id", "food_pedidos", ["mesa_id"])
    op.create_index("ix_food_pedidos_estado", "food_pedidos", ["estado"])
    op.create_index("ix_food_pedidos_pagado", "food_pedidos", ["pagado"])

    op.create_table(
        "food_detalle_pedidos",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("company_id", sa.Integer(), nullable=False),
        sa.Column("pedido_id", sa.Integer(), nullable=False),
        sa.Column("producto_id", sa.Integer(), nullable=False),
        sa.Column("cantidad", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("precio_unitario", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("subtotal", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("notas", sa.String(length=255), nullable=True),
        sa.Column("estado_produccion", sa.String(length=30), nullable=False, server_default="pendiente"),
        sa.Column("impreso_cocina", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("impreso_caja", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("enviado_cocina_at", sa.DateTime(), nullable=True),
        sa.Column("preparado_por_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["pedido_id"], ["food_pedidos.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["producto_id"], ["food_productos.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["preparado_por_id"], ["food_usuarios.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_food_detalle_pedidos_pedido_id", "food_detalle_pedidos", ["pedido_id"])
    op.create_index("ix_food_detalle_pedidos_impreso_cocina", "food_detalle_pedidos", ["impreso_cocina"])
    op.create_index("ix_food_detalle_pedidos_estado_produccion", "food_detalle_pedidos", ["estado_produccion"])


def downgrade() -> None:
    op.drop_table("food_detalle_pedidos")
    op.drop_table("food_pedidos")
    op.drop_table("food_productos")
    op.drop_table("food_categorias")
    op.drop_table("food_mesas")
    op.drop_table("food_usuarios")
