"""corregir emojis de producto/combo doble-codificados (mojibake)

Revision ID: r8m9n0o1p2q3
Revises: q7l8m9n0o1p2
Create Date: 2026-08-09 00:00:00.000000

Los emojis históricos de `food_productos.emoji` (y `food_combos.emoji`) quedaron
guardados con DOBLE codificación: los bytes UTF-8 del emoji fueron interpretados
como windows-1252 y re-codificados a UTF-8. Ej: 🍔 (UTF-8 F0 9F 8D 94) quedó
almacenado como C3B0C5B8C28DE2809D, y en la UI se ve "ðŸ\x8d”".

Esto NO es un problema de charset de conexión (la tabla es utf8mb4 y el alta de
productos nueva guarda bien): es dato ya persistido, importado/restaurado en su
momento con doble codificación. Los emojis de CATEGORÍA no están afectados.

`fix_encoding.sql` corrige `nombre`/`descripcion` con el round-trip latin1 de
MySQL, pero NO sirve para `emoji`: la doble codificación usó windows-1252 (con
caracteres como Ÿ 0x9F y ” 0x94 que NO existen como byte único en latin1), así
que `CONVERT(... USING latin1)` los perdería. Por eso la reversión se hace en
Python, reinterpretando cada carácter como windows-1252 (variante WHATWG, con
fallback C1 para los 5 bytes sin asignar) para recuperar los bytes UTF-8 reales.

Idempotente: un emoji ya correcto contiene un carácter fuera de windows-1252
(el propio emoji), así que no es reversible y se deja intacto. Correr de nuevo
no cambia ninguna fila.
"""
from __future__ import annotations

from typing import Iterator, Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'r8m9n0o1p2q3'
down_revision: Union[str, None] = 'q7l8m9n0o1p2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLAS = ('food_productos', 'food_combos')

# ── Reversión mojibake: windows-1252 (WHATWG, con fallback C1) ────────────────
# cp1252 deja 5 bytes sin asignar (0x81, 0x8D, 0x8F, 0x90, 0x9D); la variante web
# (WHATWG) los mapea a su control C1 del mismo valor. Ese es el comportamiento
# que produjo la doble codificación, así que lo replicamos para invertirlo.
_UNDEFINED = (0x81, 0x8D, 0x8F, 0x90, 0x9D)


def _decode_byte(b: int) -> str:
    if b in _UNDEFINED:
        return chr(b)
    return bytes([b]).decode('cp1252')


_DECODE = {b: _decode_byte(b) for b in range(256)}
_ENCODE = {c: b for b, c in _DECODE.items()}  # inverso char -> byte (biyección)


def _fix_mojibake(s: str | None) -> str | None:
    """Revierte doble codificación UTF-8→windows-1252. Idempotente y segura:
    si `s` no es reversible (contiene un char fuera de windows-1252, p.ej. un
    emoji ya correcto, o los bytes revertidos no son UTF-8 válido), lo devuelve
    intacto."""
    if not s:
        return s
    try:
        raw = bytes(_ENCODE[ch] for ch in s)
    except KeyError:
        return s  # ya correcto: contiene un char no representable en windows-1252
    try:
        return raw.decode('utf-8')
    except UnicodeDecodeError:
        return s  # los bytes revertidos no son UTF-8 válido -> no tocar


def _cambios(conn, tabla: str) -> Iterator[tuple[int, str]]:
    rows = conn.execute(
        sa.text(
            f"SELECT id, emoji FROM {tabla} WHERE emoji IS NOT NULL AND emoji <> ''"
        )
    ).all()
    for rid, emoji in rows:
        fixed = _fix_mojibake(emoji)
        if fixed != emoji:
            yield rid, fixed


def upgrade() -> None:
    # Guardarraíl: verifica el algoritmo contra el caso conocido 🍔 antes de tocar
    # datos. Si algún día cambia el runtime y la reversión no da 🍔, aborta.
    caso = bytes.fromhex('C3B0C5B8C28DE2809D').decode('utf-8')
    assert _fix_mojibake(caso) == '\U0001f354', 'reversión mojibake inválida'

    conn = op.get_bind()
    for tabla in _TABLAS:
        for rid, fixed in list(_cambios(conn, tabla)):
            conn.execute(
                sa.text(f"UPDATE {tabla} SET emoji = :e WHERE id = :id"),
                {'e': fixed, 'id': rid},
            )


def downgrade() -> None:
    # No-op deliberado: revertir significaría VOLVER a corromper los emojis
    # (re-codificarlos a mojibake), lo que no aporta valor y es riesgoso. El
    # estado "corregido" es el correcto; se deja como terminal.
    pass
