"""Helpers para exportaciones a Excel autoexplicativas (openpyxl).

Compartidos por Reportes y Carta. El objetivo: que cualquiera que abra el .xlsx
entienda qué reporte es, de qué empresa y de qué período, sin contexto extra.
"""
from __future__ import annotations


def escribir_encabezado(ws, titulo: str, descripcion: str,
                        meta: list[tuple[str, str]], n_cols: int) -> int:
    """Escribe un encabezado (título + descripción + metadatos) al inicio de la
    hoja y devuelve el número de fila donde debe ir la fila de encabezados de la
    tabla. Las ``ws.append`` posteriores caen debajo.
    """
    from openpyxl.styles import Font

    ncol = max(1, n_cols)
    ws.append([titulo])
    ws.merge_cells(start_row=ws.max_row, start_column=1, end_row=ws.max_row, end_column=ncol)
    ws.cell(row=ws.max_row, column=1).font = Font(bold=True, size=14, color="EA580C")
    if descripcion:
        ws.append([descripcion])
        ws.merge_cells(start_row=ws.max_row, start_column=1, end_row=ws.max_row, end_column=ncol)
        ws.cell(row=ws.max_row, column=1).font = Font(italic=True, size=10, color="555555")
    for label, val in meta:
        ws.append([f"{label}:", val])
        ws.cell(row=ws.max_row, column=1).font = Font(bold=True, size=10)
    # Fila en blanco separadora. Se escribe "" (no lista vacía) para que
    # ``max_row`` la cuente y el número de fila devuelto sea el correcto.
    ws.append([""])
    return ws.max_row + 1


def autofit_columnas(ws, start_row: int = 1, max_width: int = 48) -> None:
    """Ajusta el ancho de columnas mirando solo las filas de datos (``>= start_row``),
    para que el título/descripción fusionados de arriba no inflen el ancho."""
    from openpyxl.utils import get_column_letter

    for col_cells in ws.columns:
        letter = get_column_letter(col_cells[0].column)
        lengths = [len(str(c.value)) for c in col_cells
                   if c.value is not None and c.row >= start_row]
        ancho = (max(lengths) + 2) if lengths else 10
        ws.column_dimensions[letter].width = min(ancho, max_width)
