"""Ícono en la bandeja del sistema (pystray): estado + menú de acciones."""
from __future__ import annotations

import logging
import os
import threading
from pathlib import Path

import pystray
from pystray import Menu, MenuItem
from PIL import Image, ImageDraw

import config as config_mod
import printers

log = logging.getLogger("agente")

_STATUS_COLOR = {
    "init": (150, 150, 150),
    "ok": (34, 197, 94),
    "imprimiendo": (234, 179, 8),
    "error": (239, 68, 68),
    "sin_token": (239, 68, 68),
}
_STATUS_LABEL = {
    "init": "Iniciando…",
    "ok": "Conectado",
    "imprimiendo": "Imprimiendo…",
    "error": "Error de conexión",
    "sin_token": "Falta token (config.ini)",
}


class TrayApp:
    def __init__(self, worker, config: dict, base_dir) -> None:
        self.worker = worker
        self.config = config
        self.base_dir = Path(base_dir)
        self._estado = "init"
        self._detalle = ""
        self._lock = threading.Lock()
        self.icon = pystray.Icon(
            "tuwaykifood_agente",
            self._imagen(),
            "TUWAYKIFOOD — Agente",
            menu=self._menu(),
        )

    # ── imagen del ícono (logo + punto de estado) ─────────────────────────
    def _base_logo(self) -> Image.Image:
        ico = config_mod.bundle_dir() / "assets" / "tuwayki.ico"
        if ico.exists():
            try:
                return Image.open(ico).convert("RGBA").resize((64, 64), Image.LANCZOS)
            except Exception:
                pass
        return Image.new("RGBA", (64, 64), (80, 59, 235, 255))  # morado de marca

    def _imagen(self) -> Image.Image:
        img = self._base_logo().copy()
        draw = ImageDraw.Draw(img)
        color = _STATUS_COLOR.get(self._estado, (150, 150, 150))
        draw.ellipse([39, 39, 63, 63], fill=(255, 255, 255, 255))
        draw.ellipse([42, 42, 60, 60], fill=color + (255,))
        return img

    # ── menú ──────────────────────────────────────────────────────────────
    def _menu(self) -> Menu:
        return Menu(
            MenuItem(lambda i: f"Estado: {_STATUS_LABEL.get(self._estado, self._estado)}", None, enabled=False),
            MenuItem(lambda i: f"  {self._detalle or '—'}", None, enabled=False),
            Menu.SEPARATOR,
            MenuItem("Imprimir prueba", self._on_prueba),
            MenuItem("Reintentar ahora", self._on_reintentar),
            MenuItem("Abrir logs", self._on_logs),
            Menu.SEPARATOR,
            MenuItem("Salir", self._on_salir),
        )

    # ── callback de estado desde el worker ────────────────────────────────
    def set_status(self, estado: str, detalle: str = "") -> None:
        with self._lock:
            self._estado = estado
            self._detalle = detalle
        try:
            self.icon.icon = self._imagen()
            self.icon.title = f"TUWAYKIFOOD — {_STATUS_LABEL.get(estado, estado)}"
            self.icon.update_menu()
        except Exception:
            pass

    # ── acciones del menú ─────────────────────────────────────────────────
    def _on_prueba(self, icon, item) -> None:
        impresoras = self.worker.impresoras()
        imp = impresoras.get("caja") or next(iter(impresoras.values()), None)
        if not imp:
            self.set_status(self._estado, "Sin impresoras para la prueba")
            return

        def _run() -> None:
            try:
                printers.imprimir_prueba(imp)
                log.info("Ticket de prueba enviado a '%s'", imp.get("nombre"))
            except Exception as exc:  # noqa: BLE001
                log.exception("Fallo el ticket de prueba")
                self.set_status("error", f"Prueba falló: {exc}")

        threading.Thread(target=_run, daemon=True).start()

    def _on_reintentar(self, icon, item) -> None:
        self.worker.poke()

    def _on_logs(self, icon, item) -> None:
        ruta = self.base_dir / "agente.log"
        try:
            os.startfile(str(ruta))  # solo Windows
        except Exception:
            log.info("Archivo de log: %s", ruta)

    def _on_salir(self, icon, item) -> None:
        self.worker.stop()
        icon.stop()

    def run(self) -> None:
        self.icon.run()
