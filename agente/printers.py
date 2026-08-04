"""Impresión ESC/POS: rutea cada trabajo a su impresora (red o USB).

El `contenido` de cada trabajo ya viene formateado al ancho desde el backend;
acá solo se agrega el texto + corte y (en USB) se manda por el spooler de Windows.
"""
from __future__ import annotations

import unicodedata

# python-escpos. Win32Raw solo existe/funciona en Windows (usa pywin32).
from escpos.printer import Network

try:  # Win32Raw no está disponible fuera de Windows
    from escpos.printer import Win32Raw
except Exception:  # pragma: no cover
    Win32Raw = None


def crear_impresora(imp: dict):
    """Instancia un printer de python-escpos según la config de la impresora."""
    tipo = (imp.get("tipo") or "red").lower()
    if tipo == "usb":
        if Win32Raw is None:
            raise RuntimeError("Impresión USB solo soportada en Windows (falta pywin32).")
        target = (imp.get("usb_target") or "").strip()
        if not target:
            raise ValueError("Impresora USB sin nombre configurado (usb_target).")
        return Win32Raw(target)
    ip = (imp.get("ip") or "").strip()
    if not ip:
        raise ValueError("Impresora de red sin IP configurada.")
    puerto = int(imp.get("puerto") or 9100)
    return Network(ip, puerto, timeout=10)


def _sin_acentos(texto: str) -> str:
    """Translitera acentos a ASCII (fallback si el codepage no los soporta)."""
    return unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")


def imprimir_en(printer, texto: str) -> None:
    """Imprime `texto` y corta. Reintenta sin acentos si falla la codificación."""
    try:
        printer.text(texto + "\n")
    except (UnicodeError, ValueError):
        printer.text(_sin_acentos(texto) + "\n")
    printer.cut()


def imprimir_trabajo(imp: dict, texto: str) -> None:
    """Crea la impresora, imprime el trabajo y cierra la conexión."""
    printer = crear_impresora(imp)
    try:
        imprimir_en(printer, texto or "")
    finally:
        try:
            printer.close()
        except Exception:
            pass


def imprimir_prueba(imp: dict) -> None:
    """Ticket de prueba local (para el menú de la bandeja)."""
    ancho = int(imp.get("paper_width_mm") or 80)
    cols = 32 if ancho <= 58 else 42
    lineas = [
        "TUWAYKIFOOD".center(cols),
        "Agente de impresion".center(cols),
        "-" * cols,
        f"Impresora: {imp.get('nombre', '')}",
        f"Rol: {imp.get('rol', '')}  Tipo: {imp.get('tipo', '')}",
        "Prueba OK - acentos: aeiou nnn".center(cols),
        "-" * cols,
    ]
    imprimir_trabajo(imp, "\n".join(lineas))
