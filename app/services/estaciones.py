"""Ruteo de preparación: dónde (o si) se prepara un producto.

La "estación efectiva" de un producto resuelve, en orden:
  1. `producto.estacion` (override por producto), si está seteado.
  2. `categoria.estacion` de su categoría.
  3. COCINA por defecto.

Un producto cuya estación efectiva es `NINGUNA` ("Sin preparación") NO pasa por
cocina/barra: no genera comanda ni aparece en la pantalla de cocina (KDS); va
directo a la cuenta/caja. Esto se snapshotea en `DetallePedido.requiere_preparacion`
al agregar el ítem, para que el ruteo no cambie si luego editan la carta.
"""
from __future__ import annotations

from sqlmodel import Session

from app.models.food import Categoria, EstacionCocina, Producto


def estacion_efectiva(producto: Producto, categoria: Categoria | None) -> str:
    """Estación efectiva: override del producto → categoría → COCINA."""
    return (
        (producto.estacion or None)
        or (categoria.estacion if categoria is not None else None)
        or EstacionCocina.COCINA.value
    )


def requiere_preparacion(session: Session, producto: Producto | None) -> bool:
    """¿El producto se prepara (cocina/barra) o va directo a caja?

    Resuelve la estación efectiva cargando la categoría si el producto no define
    un override propio. Ante la duda (producto None), devuelve True para no
    "esconder" ítems de cocina por error.
    """
    if producto is None:
        return True
    categoria = None
    if not producto.estacion and producto.categoria_id:
        categoria = session.get(Categoria, producto.categoria_id)
    return estacion_efectiva(producto, categoria) != EstacionCocina.NINGUNA.value
