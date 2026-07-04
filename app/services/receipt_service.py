"""Generación de comanda de cocina y comprobante de caja como HTML.

La impresión se dispara desde el navegador (window.print()), no desde el
servidor — así funciona sin importar si el backend corre en un servidor
remoto (AWS) y la impresora está conectada localmente por USB o por red en
la tablet/PC de caja del local. Mismo mecanismo que usa Sistema-de-Ventas.
"""

from __future__ import annotations

import html
import json
import textwrap
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

TICKET_WIDTH = 32  # chars para papel 58mm


def _chars_for_mm(mm: int) -> int:
    """Columnas de texto para fuente monospace 12px según ancho de papel."""
    if mm <= 58:
        return 32
    return 42  # 80 mm


@dataclass(slots=True)
class TicketLine:
    name: str
    quantity: int
    unit_price: float = 0.0
    subtotal: float = 0.0
    note: str = ""


def _money(value: float) -> str:
    return f"S/ {value:.2f}"


def _wrap(text: str, width: int) -> list[str]:
    return textwrap.wrap(text, width=max(width, 1)) or [text]


def _center(text: str, width: int) -> str:
    return text.center(width)


def _line(width: int) -> str:
    return "-" * width


def _row(left: str, right: str, width: int) -> str:
    spaces = width - len(left) - len(right)
    return left + " " * max(spaces, 1) + right


def _format_sale_line(item: TicketLine, width: int) -> list[str]:
    subtotal = _money(item.subtotal)
    label = f"{item.quantity}x {item.name}"
    first_line_width = max(8, width - len(subtotal) - 1)
    wrapped = _wrap(label, first_line_width)
    lines = [f"{wrapped[0]:<{first_line_width}} {subtotal}"]
    for extra in wrapped[1:]:
        lines.append(f"   {extra}")
    return lines


def _render_html(document_title: str, lines: list[str], paper_width_mm: int) -> str:
    lines = lines + [""] * 5
    text = "\n".join(lines)
    safe_text = html.escape(text)
    safe_title = html.escape(document_title)
    return f"""<html>
<head>
<meta charset="utf-8"/>
<title>{safe_title}</title>
<style>
@page {{ size: {paper_width_mm}mm auto; margin: 0; }}
body {{ margin: 0; padding: 2mm; }}
pre {{ font-family: monospace; font-size: 12px; margin: 0; white-space: pre-wrap; word-break: break-word; }}
</style>
</head>
<body>
<pre>{safe_text}</pre>
</body>
</html>"""


def generate_kitchen_ticket_html(
    *,
    mesa_label: str,
    pedido_id: int,
    items: Iterable[TicketLine],
    notes: str = "",
    paper_width_mm: int = 80,
    width: int = 0,
) -> str:
    if width == 0:
        width = _chars_for_mm(paper_width_mm)
    lines: list[str] = [_center("COCINA", width), ""]
    lines.append(mesa_label)
    lines.append(f"Pedido: #{pedido_id}")
    lines.append(f"Fecha: {datetime.now():%Y-%m-%d %H:%M}")
    lines.append(_line(width))
    for item in items:
        lines.append(f"{item.quantity} x {item.name}")
        if item.note:
            for note_line in _wrap(f"* {item.note}", width - 2):
                lines.append(f"  {note_line}")
    if notes:
        lines.append("")
        for note_line in _wrap(f"Notas: {notes}", width):
            lines.append(note_line)
    return _render_html("Comanda de Cocina", lines, paper_width_mm)


def generate_cashier_ticket_html(
    *,
    order_reference: str,
    pedido_id: int,
    items: Iterable[TicketLine],
    total: float,
    attended_by: str = "",
    company_name: str = "TUWAYKIFOOD",
    company_ruc: str = "",
    company_sucursal: str = "",
    company_direccion: str = "",
    company_telefono: str = "",
    descuento: float = 0.0,
    metodo_pago: str = "",
    mensaje_footer: str = "",
    mostrar_iva: bool = False,
    nombre_impuesto: str = "IGV",
    porcentaje_iva: float = 18.0,
    paper_width_mm: int = 80,
    width: int = 0,
) -> str:
    if width == 0:
        width = _chars_for_mm(paper_width_mm)
    now = datetime.now()
    lines: list[str] = [
        _center(company_name.upper(), width),
    ]
    if company_sucursal:
        lines.append(_center(company_sucursal.upper(), width))
    if company_ruc:
        lines.append(_center(f"RUC: {company_ruc}", width))
    if company_direccion:
        for dl in _wrap(company_direccion, width):
            lines.append(_center(dl, width))
    if company_telefono:
        lines.append(_center(f"Tel.: {company_telefono}", width))
    lines += [
        "",
        _center("COMPROBANTE DE PAGO", width),
        _center(f"{now:%Y-%m-%d  %H:%M}", width),
        _line(width),
        order_reference,
        f"Pedido: #{pedido_id}",
        f"Atendido por: {attended_by or 'Sin asignar'}",
        _line(width),
    ]
    for item in items:
        for line in _format_sale_line(item, width):
            lines.append(line)
        if item.note:
            for note_line in _wrap(f"* {item.note}", width - 2):
                lines.append(f"  {note_line}")
    lines.append(_line(width))
    if descuento > 0:
        lines.append(_row("Descuento:", "-" + _money(descuento), width))
        lines.append(_line(width))
    if mostrar_iva and porcentaje_iva > 0:
        iva_amount = total * porcentaje_iva / (100 + porcentaje_iva)
        net_subtotal = total - iva_amount
        pct_label = f"{porcentaje_iva:.4g}".rstrip("0").rstrip(".")
        lines.append(_row("Subtotal:", _money(net_subtotal), width))
        tax_label = nombre_impuesto or "IGV"
        lines.append(_row(f"{tax_label} ({pct_label}%):", _money(iva_amount), width))
    lines.append(_row("TOTAL A PAGAR:", _money(total), width))
    if metodo_pago:
        lines += [
            _line(width),
            _row("Método de pago:", metodo_pago.capitalize(), width),
        ]
    footer = mensaje_footer.strip() or "¡Gracias por su preferencia!"
    lines += [
        _line(width),
        _center(footer, width),
    ]
    return _render_html("Comprobante de Pago", lines, paper_width_mm)


def generate_precuenta_html(
    *,
    order_reference: str,
    pedido_id: int,
    items: Iterable[TicketLine],
    total: float,
    attended_by: str = "",
    company_name: str = "TUWAYKIFOOD",
    descuento: float = 0.0,
    paper_width_mm: int = 80,
    width: int = 0,
) -> str:
    """Pre-cuenta (proforma): sin métodos de pago, con aviso legal."""
    if width == 0:
        width = _chars_for_mm(paper_width_mm)
    now = datetime.now()
    lines: list[str] = [
        _center(company_name.upper(), width),
        "",
        _center("PRE-CUENTA", width),
        _center("*** NO ES COMPROBANTE ***", width),
        _center(f"{now:%Y-%m-%d  %H:%M}", width),
        _line(width),
        order_reference,
        f"Pedido: #{pedido_id}",
        f"Atendido por: {attended_by or 'Sin asignar'}",
        _line(width),
    ]
    for item in items:
        for line in _format_sale_line(item, width):
            lines.append(line)
        if item.note:
            for note_line in _wrap(f"* {item.note}", width - 2):
                lines.append(f"  {note_line}")
    lines.append(_line(width))
    if descuento > 0:
        lines.append(_row("Descuento:", "-" + _money(descuento), width))
        lines.append(_line(width))
    lines.append(_row("TOTAL:", _money(total), width))
    lines += [
        _line(width),
        _center("Documento sin valor fiscal", width),
    ]
    return _render_html("Pre-cuenta", lines, paper_width_mm)


def generate_cash_close_ticket_html(
    *,
    company_name: str,
    turno_id: int,
    abierto_por: str,
    cerrado_por: str,
    abierto_en_texto: str,
    cerrado_en_texto: str,
    resumen_rows: Iterable[tuple[str, str]],
    descuadre_texto: str,
    notas: str = "",
    paper_width_mm: int = 80,
    width: int = 0,
) -> str:
    """Ticket de cierre de turno de caja (arqueo) para impresora térmica."""
    if width == 0:
        width = _chars_for_mm(paper_width_mm)
    lines: list[str] = [
        _center(company_name, width),
        _center("CIERRE DE CAJA", width),
        _line(width),
        f"Turno: #{turno_id}",
        f"Apertura: {abierto_en_texto}",
        f"  por {abierto_por or 'Sin asignar'}",
        f"Cierre:   {cerrado_en_texto}",
        f"  por {cerrado_por or 'Sin asignar'}",
        _line(width),
    ]
    for etiqueta, monto in resumen_rows:
        lines.append(_row(etiqueta, monto, width))
    lines.append(_line(width))
    lines.append(_row("DESCUADRE", descuadre_texto, width))
    if notas:
        lines.append("")
        for note_line in _wrap(f"Notas: {notas}", width):
            lines.append(note_line)
    lines.append("")
    lines.append(_center("Documento interno", width))
    return _render_html("Cierre de Caja", lines, paper_width_mm)


def build_print_script(html_content: str) -> str:
    """JS que abre el comprobante en una ventana nueva y dispara el diálogo
    de impresión del navegador — imprime en la impresora ya instalada en el
    sistema operativo local (USB o red, da igual).

    Usa Blob + URL.createObjectURL para evitar problemas de document.write
    en browsers modernos (Chrome 120+ restringe document.write en popups).
    El setTimeout de 400ms espera a que el navegador termine de renderizar;
    sin él los trabajos llegan al buffer de la impresora térmica antes de que
    se complete el render y los tickets se mezclan en el mismo papel.
    El afterprint cierra la ventana automáticamente al terminar.
    """
    return f"""
    (function() {{
        var blob = new Blob([{json.dumps(html_content)}], {{type: 'text/html; charset=utf-8'}});
        var url = URL.createObjectURL(blob);
        var w = window.open(url, '_blank');
        if (!w) {{ URL.revokeObjectURL(url); return; }}
        w.focus();
        w.addEventListener('afterprint', function() {{
            w.close();
            URL.revokeObjectURL(url);
        }});
        function doPrint() {{
            setTimeout(function() {{ w.print(); }}, 400);
        }}
        if (w.document.readyState === 'complete') {{
            doPrint();
        }} else {{
            w.onload = doPrint;
        }}
    }})();
    """
