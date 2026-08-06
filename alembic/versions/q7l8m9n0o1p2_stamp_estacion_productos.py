"""estampar estación explícita en cada producto (según la carta)

Revision ID: q7l8m9n0o1p2
Revises: p6k7l8m9n0o1
Create Date: 2026-08-06 00:00:00.000000

Complemento de la migración p6k7l8m9n0o1 (que configuró las CATEGORÍAS). Acá se
estampa la estación a nivel PRODUCTO para que cada uno muestre su estación
explícita en la Carta (en vez de "Heredar de la categoría"):

  - Bebidas embotelladas (Agua, Gaseosa, Cerveza) y Pasteles y Porciones
    → "ninguna" (sin preparación, directo a caja).
  - Todo el resto (comida, cafés, jugos, cócteles, jarras) → "cocina".

Solo toca productos que estén en "heredar" (estacion NULL/''), así NUNCA pisa una
elección manual previa (protege ajustes de otros locales). Idempotente: al correr
de nuevo no quedan productos en NULL → 0 filas.

Trade-off asumido: al estampar por producto se pierde la herencia por categoría
(cambiar la estación de una categoría ya no arrastra a sus productos). Es lo que
se pidió: máxima claridad, cada producto con su estación visible.
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'q7l8m9n0o1p2'
down_revision: Union[str, None] = 'p6k7l8m9n0o1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_SIN_PREP = 'ninguna'
_COCINA = 'cocina'

# Set de "sin preparación": categoría Pasteles y Porciones, o Bebidas que NO sean
# jarras (las jarras se preparan al momento → cocina).
_SIN_PREP_WHERE = (
    "( c.nombre = 'Pasteles y Porciones' "
    "  OR (c.nombre = 'Bebidas' AND p.nombre NOT LIKE 'Jarra%') )"
)


def upgrade() -> None:
    conn = op.get_bind()
    # 1) Productos que NO se preparan → 'ninguna' explícito (solo los que heredan).
    conn.execute(
        sa.text(
            "UPDATE food_productos p JOIN food_categorias c ON c.id = p.categoria_id "
            "SET p.estacion = :est "
            "WHERE (p.estacion IS NULL OR p.estacion = '') AND " + _SIN_PREP_WHERE
        ),
        {"est": _SIN_PREP},
    )
    # 2) Todo lo demás que aún herede → 'cocina' explícito.
    conn.execute(
        sa.text(
            "UPDATE food_productos p JOIN food_categorias c ON c.id = p.categoria_id "
            "SET p.estacion = :est "
            "WHERE (p.estacion IS NULL OR p.estacion = '') AND NOT " + _SIN_PREP_WHERE
        ),
        {"est": _COCINA},
    )


def downgrade() -> None:
    # Best-effort: vuelve a "heredar" (NULL) los productos del catálogo estándar.
    # Como esta migración solo estampó los que estaban en NULL, revertir a NULL
    # restaura el estado previo para ese catálogo.
    conn = op.get_bind()
    conn.execute(
        sa.text("UPDATE food_productos SET estacion = NULL WHERE estacion IN ('ninguna', 'cocina')")
    )
