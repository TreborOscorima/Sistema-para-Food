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

from tuwayki_core.utils.timezone import country_now
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


def ticket_text(lines: list[str]) -> str:
    """Texto plano final de un ticket (lo que consume el agente de impresión)."""
    return "\n".join(lines)


def render_ticket_html(title: str, lines: list[str], paper_width_mm: int) -> str:
    """Envuelve unas líneas de ticket en el HTML de impresión del navegador."""
    return _render_html(title, lines, paper_width_mm)


def build_kitchen_ticket_lines(
    *,
    mesa_label: str,
    pedido_id: int,
    items: Iterable[TicketLine],
    notes: str = "",
    paper_width_mm: int = 80,
    width: int = 0,
) -> list[str]:
    """Líneas de texto de la comanda de cocina (reutilizable por HTML y agente)."""
    if width == 0:
        width = _chars_for_mm(paper_width_mm)
    lines: list[str] = [_center("COCINA", width), ""]
    lines.append(mesa_label)
    lines.append(f"Pedido: #{pedido_id}")
    lines.append(f"Fecha: {country_now('PE'):%Y-%m-%d %H:%M}")
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
    return lines


def generate_kitchen_ticket_html(
    *,
    mesa_label: str,
    pedido_id: int,
    items: Iterable[TicketLine],
    notes: str = "",
    paper_width_mm: int = 80,
    width: int = 0,
) -> str:
    lines = build_kitchen_ticket_lines(
        mesa_label=mesa_label,
        pedido_id=pedido_id,
        items=items,
        notes=notes,
        paper_width_mm=paper_width_mm,
        width=width,
    )
    return _render_html("Comanda de Cocina", lines, paper_width_mm)


def build_cashier_ticket_lines(
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
    propina: float = 0.0,
    recargo: float = 0.0,
    recargo_concepto: str = "",
    metodo_pago: str = "",
    mensaje_footer: str = "",
    mostrar_iva: bool = False,
    nombre_impuesto: str = "IGV",
    porcentaje_iva: float = 18.0,
    paper_width_mm: int = 80,
    width: int = 0,
) -> list[str]:
    """Líneas de texto del comprobante de pago (reutilizable por HTML y agente)."""
    if width == 0:
        width = _chars_for_mm(paper_width_mm)
    now = country_now("PE")
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
    if recargo > 0:
        label = f"Recargo ({recargo_concepto}):" if recargo_concepto else "Recargo:"
        lines.append(_row(label, "+" + _money(recargo), width))
    if propina > 0:
        lines.append(_row("Propina:", "+" + _money(propina), width))
    if descuento > 0 or recargo > 0 or propina > 0:
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
    return lines


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
    propina: float = 0.0,
    recargo: float = 0.0,
    recargo_concepto: str = "",
    metodo_pago: str = "",
    mensaje_footer: str = "",
    mostrar_iva: bool = False,
    nombre_impuesto: str = "IGV",
    porcentaje_iva: float = 18.0,
    paper_width_mm: int = 80,
    width: int = 0,
) -> str:
    return _render_html(
        "Comprobante de Pago",
        build_cashier_ticket_lines(
            order_reference=order_reference,
            pedido_id=pedido_id,
            items=items,
            total=total,
            attended_by=attended_by,
            company_name=company_name,
            company_ruc=company_ruc,
            company_sucursal=company_sucursal,
            company_direccion=company_direccion,
            company_telefono=company_telefono,
            descuento=descuento,
            propina=propina,
            recargo=recargo,
            recargo_concepto=recargo_concepto,
            metodo_pago=metodo_pago,
            mensaje_footer=mensaje_footer,
            mostrar_iva=mostrar_iva,
            nombre_impuesto=nombre_impuesto,
            porcentaje_iva=porcentaje_iva,
            paper_width_mm=paper_width_mm,
            width=width,
        ),
        paper_width_mm,
    )


def build_precuenta_lines(
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
    paper_width_mm: int = 80,
    width: int = 0,
) -> list[str]:
    """Pre-cuenta (proforma): sin métodos de pago, con aviso legal."""
    if width == 0:
        width = _chars_for_mm(paper_width_mm)
    now = country_now("PE")
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
    return lines


def generate_precuenta_html(
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
    paper_width_mm: int = 80,
    width: int = 0,
) -> str:
    return _render_html(
        "Pre-cuenta",
        build_precuenta_lines(
            order_reference=order_reference,
            pedido_id=pedido_id,
            items=items,
            total=total,
            attended_by=attended_by,
            company_name=company_name,
            company_ruc=company_ruc,
            company_sucursal=company_sucursal,
            company_direccion=company_direccion,
            company_telefono=company_telefono,
            descuento=descuento,
            paper_width_mm=paper_width_mm,
            width=width,
        ),
        paper_width_mm,
    )


def build_cash_close_ticket_lines(
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
    detalle_pedidos: list[dict] | None = None,
    detalle_movimientos: list[dict] | None = None,
) -> list[str]:
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

    if detalle_pedidos:
        lines.append("")
        lines.append(_center("DETALLE DE VENTAS", width))
        lines.append(_line(width))
        for p in detalle_pedidos:
            lines.append(f"{p.get('hora', '')}  {p.get('mesa', '')}")
            lines.append(f"Metodo: {p.get('metodo', '')}")
            items = p.get("items", "")
            if items:
                for item_line in _wrap(f"  {items}", width):
                    lines.append(item_line)
            lines.append(_row("Total:", p.get("neto_texto", ""), width))
            lines.append(_line(width))

    if detalle_movimientos:
        lines.append("")
        lines.append(_center("MOVIMIENTOS DE CAJA", width))
        lines.append(_line(width))
        for m in detalle_movimientos:
            lines.append(f"{m.get('hora', '')} {m.get('tipo', '')}")
            lines.append(f"  {m.get('categoria', '')}: {m.get('motivo', '')}")
            lines.append(_row("Monto:", m.get("monto", ""), width))
            lines.append(_line(width))

    if notas:
        lines.append("")
        for note_line in _wrap(f"Notas: {notas}", width):
            lines.append(note_line)
    lines.append("")
    lines.append(_center("Documento interno", width))
    return lines


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
    detalle_pedidos: list[dict] | None = None,
    detalle_movimientos: list[dict] | None = None,
) -> str:
    return _render_html(
        "Cierre de Caja",
        build_cash_close_ticket_lines(
            company_name=company_name,
            turno_id=turno_id,
            abierto_por=abierto_por,
            cerrado_por=cerrado_por,
            abierto_en_texto=abierto_en_texto,
            cerrado_en_texto=cerrado_en_texto,
            resumen_rows=resumen_rows,
            descuadre_texto=descuadre_texto,
            notas=notas,
            paper_width_mm=paper_width_mm,
            width=width,
            detalle_pedidos=detalle_pedidos,
            detalle_movimientos=detalle_movimientos,
        ),
        paper_width_mm,
    )


def build_print_script(html_content: str) -> str:
    """JS que imprime el comprobante usando un IFRAME OCULTO (no un popup).

    Antes se usaba window.open(), pero los navegadores bloquean los popups que
    NO nacen de un click directo del usuario. La auto-impresión de comandas se
    dispara desde un polling en segundo plano (sin gesto del usuario), así que
    el popup se bloqueaba silenciosamente y no salía ningún ticket. Un iframe
    oculto no está sujeto al bloqueador de popups y permite imprimir directo en
    la impresora instalada en el sistema operativo local (USB o red, da igual).

    En modo kiosk-printing de Chrome/Edge (`--kiosk-printing`) la impresión es
    silenciosa (sin diálogo), ideal para la impresora térmica de la caja.

    El setTimeout de 400ms espera a que el iframe termine de renderizar antes
    de imprimir; sin él, el trabajo llega al buffer de la térmica antes de que
    se complete el render y los tickets se mezclan en el mismo papel. Se usa
    `srcdoc` (fiable para disparar onload) con un timeout de respaldo por si el
    onload no dispara. El iframe se elimina 2s después de imprimir.
    """
    return f"""
    (function() {{
        var html = {json.dumps(html_content)};
        var iframe = document.createElement('iframe');
        iframe.setAttribute('aria-hidden', 'true');
        iframe.style.cssText = 'position:fixed;right:0;bottom:0;width:0;height:0;border:0;visibility:hidden;';
        var printed = false;
        function cleanup() {{
            setTimeout(function() {{
                if (iframe && iframe.parentNode) {{ iframe.parentNode.removeChild(iframe); }}
            }}, 2000);
        }}
        function doPrint() {{
            if (printed) {{ return; }}
            printed = true;
            setTimeout(function() {{
                try {{
                    iframe.contentWindow.focus();
                    iframe.contentWindow.print();
                }} catch (e) {{}}
                cleanup();
            }}, 400);
        }}
        iframe.onload = doPrint;
        document.body.appendChild(iframe);
        iframe.srcdoc = html;
        setTimeout(doPrint, 1500);
    }})();
    """
