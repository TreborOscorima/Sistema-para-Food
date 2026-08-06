"""set estaciones de la carta (pasteles y bebidas → sin preparación)

Revision ID: p6k7l8m9n0o1
Revises: o5j6k7l8m9n0
Create Date: 2026-08-06 00:00:00.000000

Backfill de DATOS (no toca esquema). Configura la estación efectiva de la carta
según la operación acordada con el negocio, para que el ruteo a cocina/caja sea
correcto sin tener que tocar cada producto a mano en la Carta:

  - Categoría "Pasteles y Porciones" → "ninguna" (sin preparación): porciones
    pre-hechas que se cortan y sirven; van directo a caja, no al KDS.
  - Categoría "Bebidas" → "ninguna" (aguas, gaseosas, cerveza embotellada).
  - Excepción: las jarras ("Jarra ...") se preparan al momento → "cocina".

Se hace por NOMBRE de categoría/producto (no por company_id) para que aplique a
la empresa real y a cualquier duplicado del mismo catálogo. Idempotente: correrla
de nuevo deja el mismo estado. El negocio puede cambiarlo luego desde la Carta
(la migración no vuelve a correr sobre esa BD).

La estación efectiva se resuelve producto.estacion → categoria.estacion →
"cocina" por defecto (ver app/services/estaciones.py). Por eso NO hay que tocar
las categorías de comida ni las bebidas hechas al momento: quedan en "cocina".
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'p6k7l8m9n0o1'
down_revision: Union[str, None] = 'o5j6k7l8m9n0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_SIN_PREP = 'ninguna'
_COCINA = 'cocina'


def upgrade() -> None:
    conn = op.get_bind()
    # 1) Categorías pre-hechas / embotelladas → sin preparación (directo a caja).
    conn.execute(
        sa.text(
            "UPDATE food_categorias SET estacion = :est "
            "WHERE nombre IN ('Pasteles y Porciones', 'Bebidas')"
        ),
        {"est": _SIN_PREP},
    )
    # 2) Excepción dentro de Bebidas: las jarras se preparan al momento → cocina.
    conn.execute(
        sa.text(
            "UPDATE food_productos SET estacion = :est "
            "WHERE nombre LIKE 'Jarra%' AND categoria_id IN "
            "(SELECT id FROM food_categorias WHERE nombre = 'Bebidas')"
        ),
        {"est": _COCINA},
    )


def downgrade() -> None:
    # Volver a "heredar de la categoría" (NULL) es lo más neutro; no forzamos
    # 'cocina' para no pisar ajustes hechos a mano después de esta migración.
    conn = op.get_bind()
    conn.execute(
        sa.text(
            "UPDATE food_categorias SET estacion = NULL "
            "WHERE nombre IN ('Pasteles y Porciones', 'Bebidas')"
        )
    )
    conn.execute(
        sa.text(
            "UPDATE food_productos SET estacion = NULL "
            "WHERE nombre LIKE 'Jarra%' AND categoria_id IN "
            "(SELECT id FROM food_categorias WHERE nombre = 'Bebidas')"
        )
    )
