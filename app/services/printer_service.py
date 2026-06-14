"""Integración con impresoras térmicas ESC/POS (red + USB)."""

from __future__ import annotations

import os
import textwrap
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable


TICKET_WIDTH = 32
COCINA_IP = os.getenv("PRINTER_KITCHEN_HOST", "192.168.1.100")
COCINA_PORT = int(os.getenv("PRINTER_KITCHEN_PORT", "9100"))
COCINA_TIMEOUT = int(os.getenv("PRINTER_KITCHEN_TIMEOUT", "10"))

CAJA_ID_VENDOR = int(os.getenv("PRINTER_CASHIER_VENDOR_ID", "0x04b8"), 0)
CAJA_ID_PRODUCT = int(os.getenv("PRINTER_CASHIER_PRODUCT_ID", "0x0202"), 0)
CAJA_USB_TIMEOUT = int(os.getenv("PRINTER_CASHIER_TIMEOUT", "0"))
CAJA_USB_INTERFACE = int(os.getenv("PRINTER_CASHIER_INTERFACE", "0"))
CAJA_USB_IN_EP = int(os.getenv("PRINTER_CASHIER_IN_EP", "0x82"), 0)
CAJA_USB_OUT_EP = int(os.getenv("PRINTER_CASHIER_OUT_EP", "0x01"), 0)


@dataclass(slots=True)
class NetworkPrinterConfig:
    host: str
    port: int = 9100
    timeout: int = 10


@dataclass(slots=True)
class UsbPrinterConfig:
    id_vendor: int
    id_product: int
    interface: int = 0
    in_ep: int = 0x82
    out_ep: int = 0x01
    timeout: int = 0


@dataclass(slots=True)
class TicketLine:
    name: str
    quantity: int
    unit_price: float = 0.0
    subtotal: float = 0.0
    note: str = ""


class SilentPrinterService:
    """Servicio para enviar tickets sin diálogo del navegador."""

    def __init__(
        self,
        kitchen: NetworkPrinterConfig | None = None,
        cashier: UsbPrinterConfig | NetworkPrinterConfig | None = None,
    ) -> None:
        self.kitchen = kitchen
        self.cashier = cashier

    @classmethod
    def from_env(cls) -> "SilentPrinterService":
        kitchen = NetworkPrinterConfig(
            host=COCINA_IP,
            port=COCINA_PORT,
            timeout=COCINA_TIMEOUT,
        )
        cashier = UsbPrinterConfig(
            id_vendor=CAJA_ID_VENDOR,
            id_product=CAJA_ID_PRODUCT,
            interface=CAJA_USB_INTERFACE,
            in_ep=CAJA_USB_IN_EP,
            out_ep=CAJA_USB_OUT_EP,
            timeout=CAJA_USB_TIMEOUT,
        )
        return cls(kitchen=kitchen, cashier=cashier)

    @classmethod
    def from_db_config(cls, cfg) -> "SilentPrinterService":
        kitchen = (
            NetworkPrinterConfig(host=cfg.cocina_ip, port=cfg.cocina_puerto)
            if cfg.cocina_activa and cfg.cocina_ip
            else None
        )
        cashier = (
            NetworkPrinterConfig(host=cfg.caja_ip, port=cfg.caja_puerto)
            if cfg.caja_activa and cfg.caja_ip
            else None
        )
        return cls(kitchen=kitchen, cashier=cashier)

    def print_kitchen_ticket(
        self,
        *,
        mesa_label: str,
        pedido_id: int,
        items: Iterable[TicketLine],
        notes: str = "",
    ) -> None:
        if not self.kitchen:
            return
        try:
            def render(printer) -> None:
                printer.set(align="center", bold=True, width=2, height=2)
                printer.text("COCINA\n")
                printer.set(align="left", bold=False, width=1, height=1)
                printer.text(f"{mesa_label}\n")
                printer.text(f"Pedido: #{pedido_id}\n")
                printer.text(f"Fecha: {datetime.now():%Y-%m-%d %H:%M}\n")
                printer.text(_separator())
                for item in items:
                    printer.text(f"{item.quantity} x {item.name}\n")
                    if item.note:
                        printer.text(f"  * {item.note}\n")
                if notes:
                    printer.text(f"\nNotas: {notes}\n")

            self._send_to_printer(self._open_network_printer(self.kitchen), render)
        except Exception as error:
            print(f"Error impresora cocina: {error}")

    def print_cashier_ticket(
        self,
        *,
        order_reference: str,
        pedido_id: int,
        items: Iterable[TicketLine],
        total: float,
        attended_by: str = "",
        company_name: str = "TUWAYKIFOOD",
    ) -> None:
        if not self.cashier:
            return
        try:
            def render(printer) -> None:
                now = datetime.now()
                printer.set(align="center", bold=True, width=2, height=2)
                printer.text(f"{company_name}\n")
                printer.set(align="center", bold=False, width=1, height=1)
                printer.text("Ticket de Venta\n")
                printer.text(f"{now:%Y-%m-%d %H:%M}\n")
                printer.set(align="left", bold=False, width=1, height=1)
                printer.text(_separator())
                printer.text(f"{order_reference}\n")
                printer.text(f"Pedido: #{pedido_id}\n")
                printer.text(f"Atendido por: {attended_by or 'Sin asignar'}\n")
                printer.text(_separator())
                printer.text("Cant Producto             Subt.\n")
                printer.text(_separator())
                for item in items:
                    for line in _format_sale_line(item):
                        printer.text(f"{line}\n")
                    if item.note:
                        for note_line in textwrap.wrap(f"* {item.note}", width=TICKET_WIDTH - 2):
                            printer.text(f"  {note_line}\n")
                printer.text(_separator())
                printer.set(align="left", bold=True, width=2, height=2)
                printer.text(f"TOTAL {_money(total)}\n")
                printer.set(align="center", bold=False, width=1, height=1)
                printer.text("\n¡Gracias por su preferencia!\n")

            if isinstance(self.cashier, NetworkPrinterConfig):
                self._send_to_printer(self._open_network_printer(self.cashier), render)
            else:
                self._send_to_printer(self._open_usb_printer(self.cashier), render)
        except Exception as error:
            print(f"Error impresora caja: {error}")

    def _send_to_printer(self, printer, render_ticket) -> None:
        try:
            render_ticket(printer)
            printer.cut()
        finally:
            try:
                printer.close()
            except Exception:
                pass

    @staticmethod
    def _open_network_printer(config: NetworkPrinterConfig):
        try:
            from escpos.printer import Network
        except ImportError as exc:
            raise RuntimeError("Instala 'python-escpos' para imprimir.") from exc
        return Network(config.host, port=config.port, timeout=config.timeout)

    @staticmethod
    def _open_usb_printer(config: UsbPrinterConfig):
        try:
            from escpos.printer import Usb
        except ImportError as exc:
            raise RuntimeError("Instala 'python-escpos' y 'pyusb' para imprimir.") from exc
        return Usb(
            config.id_vendor,
            config.id_product,
            interface=config.interface,
            in_ep=config.in_ep,
            out_ep=config.out_ep,
            timeout=config.timeout,
        )


def _money(value: float) -> str:
    return f"S/ {value:.2f}"


def _separator() -> str:
    return "-" * TICKET_WIDTH + "\n"


def _format_sale_line(item: TicketLine) -> list[str]:
    subtotal = _money(item.subtotal)
    label = f"{item.quantity}x {item.name}"
    first_line_width = max(8, TICKET_WIDTH - len(subtotal) - 1)
    wrapped = textwrap.wrap(label, width=first_line_width) or [label]
    lines = [f"{wrapped[0]:<{first_line_width}} {subtotal}"]
    for extra in wrapped[1:]:
        lines.append(f"   {extra}")
    return lines
