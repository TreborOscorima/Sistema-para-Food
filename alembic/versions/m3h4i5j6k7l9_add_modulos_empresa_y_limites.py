"""add company modulos override table + limit columns

Revision ID: m3h4i5j6k7l9
Revises: l2g3h4i5j6k8
Create Date: 2026-08-05 02:00:00.000000

Fase 3 Owner Panel: capa de módulos habilitados por empresa (override del owner
sobre el plan) + límites por empresa (usuarios, mesas, sucursales). NULL en las
columnas de límite = usar el default del plan.

"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect as sa_inspect

# revision identifiers, used by Alembic.
revision: str = 'm3h4i5j6k7l9'
down_revision: Union[str, None] = 'l2g3h4i5j6k8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(conn, table: str) -> bool:
    return sa_inspect(conn).has_table(table)


def _has_column(conn, table: str, column: str) -> bool:
    insp = sa_inspect(conn)
    return any(c["name"] == column for c in insp.get_columns(table))


def upgrade() -> None:
    conn = op.get_bind()

    if not _has_table(conn, 'food_company_modulos'):
        op.create_table(
            'food_company_modulos',
            sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
            sa.Column('company_id', sa.Integer(), nullable=False),
            sa.Column('modulo', sa.String(length=40), nullable=False),
            sa.Column('habilitado', sa.Boolean(), nullable=False, server_default=sa.text('1')),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.UniqueConstraint('company_id', 'modulo', name='uq_food_company_modulos'),
        )
        op.create_index('ix_food_company_modulos_company_id', 'food_company_modulos', ['company_id'])

    for col in ('max_usuarios', 'max_mesas', 'max_sucursales'):
        if not _has_column(conn, 'food_companies', col):
            op.add_column('food_companies', sa.Column(col, sa.Integer(), nullable=True))


def downgrade() -> None:
    conn = op.get_bind()
    for col in ('max_sucursales', 'max_mesas', 'max_usuarios'):
        if _has_column(conn, 'food_companies', col):
            op.drop_column('food_companies', col)
    if _has_table(conn, 'food_company_modulos'):
        op.drop_index('ix_food_company_modulos_company_id', table_name='food_company_modulos')
        op.drop_table('food_company_modulos')
