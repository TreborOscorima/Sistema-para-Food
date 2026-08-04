"""add print-agent tables — impresoras, cola de trabajos y agentes locales

Agrega el backend del agente de impresión local:
- food_impresoras: impresoras físicas (red/USB) por empresa/sucursal, con rol.
- food_trabajos_impresion: cola de trabajos que el agente jala e imprime.
- food_agentes_impresion: agentes autorizados (auth por token hasheado).
- food_config_impresora.modo_impresion: "navegador" (kiosk actual) | "agente".

Backfill: siembra food_impresoras desde los campos cocina_ip/caja_ip que ya
tenían las empresas en food_config_impresora, para no perder esa config.

Revision ID: j0e1f2g3h4i6
Revises: i9d0e1f2g3h5
Create Date: 2026-08-03

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "j0e1f2g3h4i6"
down_revision: Union[str, None] = "i9d0e1f2g3h5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(name: str) -> bool:
    insp = sa.inspect(op.get_bind())
    return name in insp.get_table_names()


def _has_column(table: str, column: str) -> bool:
    insp = sa.inspect(op.get_bind())
    return any(c["name"] == column for c in insp.get_columns(table))


def upgrade() -> None:
    if not _has_table("food_impresoras"):
        op.create_table(
            "food_impresoras",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("company_id", sa.Integer(), nullable=False, index=True),
            sa.Column("sucursal_id", sa.Integer(), nullable=True, index=True),
            sa.Column("nombre", sa.String(120), nullable=False),
            sa.Column("rol", sa.String(20), nullable=False, server_default="cocina"),
            sa.Column("tipo", sa.String(10), nullable=False, server_default="red"),
            sa.Column("ip", sa.String(64), nullable=False, server_default=""),
            sa.Column("puerto", sa.Integer(), nullable=False, server_default="9100"),
            sa.Column("usb_target", sa.String(160), nullable=False, server_default=""),
            sa.Column("paper_width_mm", sa.Integer(), nullable=True),
            sa.Column("activa", sa.Boolean(), nullable=False, server_default=sa.text("1")),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
        )
        # Backfill: sembrar impresoras de red desde la config previa por empresa.
        op.execute(
            "INSERT INTO food_impresoras "
            "(company_id, sucursal_id, nombre, rol, tipo, ip, puerto, usb_target, "
            " paper_width_mm, activa, created_at, updated_at) "
            "SELECT company_id, NULL, 'Cocina', 'cocina', 'red', cocina_ip, "
            " cocina_puerto, '', NULL, 1, UTC_TIMESTAMP(), UTC_TIMESTAMP() "
            "FROM food_config_impresora "
            "WHERE cocina_activa = 1 AND cocina_ip <> ''"
        )
        op.execute(
            "INSERT INTO food_impresoras "
            "(company_id, sucursal_id, nombre, rol, tipo, ip, puerto, usb_target, "
            " paper_width_mm, activa, created_at, updated_at) "
            "SELECT company_id, NULL, 'Caja', 'caja', 'red', caja_ip, "
            " caja_puerto, '', NULL, 1, UTC_TIMESTAMP(), UTC_TIMESTAMP() "
            "FROM food_config_impresora "
            "WHERE caja_activa = 1 AND caja_ip <> ''"
        )

    if not _has_table("food_trabajos_impresion"):
        op.create_table(
            "food_trabajos_impresion",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("company_id", sa.Integer(), nullable=False, index=True),
            sa.Column("sucursal_id", sa.Integer(), nullable=True, index=True),
            sa.Column("rol", sa.String(20), nullable=False, server_default="cocina", index=True),
            sa.Column("tipo_doc", sa.String(20), nullable=False, server_default="comanda"),
            sa.Column("contenido", sa.Text(), nullable=False),
            sa.Column("paper_width_mm", sa.Integer(), nullable=False, server_default="80"),
            sa.Column("pedido_id", sa.Integer(), nullable=True, index=True),
            sa.Column("estado", sa.String(20), nullable=False, server_default="pendiente", index=True),
            sa.Column("intentos", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("error_msg", sa.String(300), nullable=True),
            sa.Column("claimed_at", sa.DateTime(), nullable=True),
            sa.Column("done_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
        )
        # Índice compuesto para el poll caliente del agente.
        op.create_index(
            "ix_food_trabajos_impresion_company_estado",
            "food_trabajos_impresion",
            ["company_id", "estado"],
        )

    if not _has_table("food_agentes_impresion"):
        op.create_table(
            "food_agentes_impresion",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column("company_id", sa.Integer(), nullable=False, index=True),
            sa.Column("sucursal_id", sa.Integer(), nullable=True, index=True),
            sa.Column("nombre", sa.String(120), nullable=False, server_default="Agente de impresión"),
            sa.Column("token_hash", sa.String(128), nullable=False, index=True),
            sa.Column("activo", sa.Boolean(), nullable=False, server_default=sa.text("1")),
            sa.Column("last_seen_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
        )

    if not _has_column("food_config_impresora", "modo_impresion"):
        op.add_column(
            "food_config_impresora",
            sa.Column(
                "modo_impresion",
                sa.String(20),
                nullable=False,
                server_default="navegador",
            ),
        )


def downgrade() -> None:
    if _has_column("food_config_impresora", "modo_impresion"):
        op.drop_column("food_config_impresora", "modo_impresion")
    if _has_table("food_agentes_impresion"):
        op.drop_table("food_agentes_impresion")
    if _has_table("food_trabajos_impresion"):
        op.drop_table("food_trabajos_impresion")
    if _has_table("food_impresoras"):
        op.drop_table("food_impresoras")
