"""Hilo worker: hace polling de la cola, imprime cada trabajo y confirma (ack).

Estados que reporta por `on_status(estado, detalle)`:
- "sin_token"   falta configurar el token
- "ok"          conectado, al día
- "imprimiendo" procesando trabajos
- "error"       error de red/servidor (con backoff)
"""
from __future__ import annotations

import logging
import threading
import time

import printers
from api_client import ApiError

log = logging.getLogger("agente")

_CONFIG_TTL = 60  # refrescar impresoras cada 60 s


class Worker(threading.Thread):
    def __init__(self, client, poll_segundos: int, on_status=None) -> None:
        super().__init__(daemon=True)
        self.client = client
        self.poll = max(1, int(poll_segundos))
        self.on_status = on_status or (lambda estado, detalle="": None)
        self._stop = threading.Event()
        self._wake = threading.Event()
        self._impresoras: dict[str, dict] = {}
        self._last_config = 0.0

    # ── control desde la bandeja ──────────────────────────────────────────
    def stop(self) -> None:
        self._stop.set()
        self._wake.set()

    def poke(self) -> None:
        """Forzar un ciclo inmediato (menú 'Reintentar ahora')."""
        self._wake.set()

    def impresoras(self) -> dict[str, dict]:
        return dict(self._impresoras)

    # ── loop ──────────────────────────────────────────────────────────────
    def _refrescar_config(self) -> None:
        data = self.client.get_config()
        default_w = data.get("default_paper_width_mm", 80)
        impresoras: dict[str, dict] = {}
        for imp in data.get("impresoras", []):
            imp.setdefault("paper_width_mm", default_w)
            impresoras.setdefault(imp.get("rol"), imp)  # primera activa por rol
        self._impresoras = impresoras
        self._last_config = time.monotonic()
        log.info("Config: %d impresora(s) %s", len(impresoras), list(impresoras))

    def _procesar(self, t: dict) -> None:
        rol = t.get("rol")
        imp = self._impresoras.get(rol)
        if imp is None:
            log.warning("Trabajo %s sin impresora de rol '%s'", t.get("id"), rol)
            self._ack_seguro(t["id"], False, f"sin impresora de rol '{rol}'")
            return
        try:
            printers.imprimir_trabajo(imp, t.get("contenido") or "")
            self.client.ack(t["id"], True)
            log.info("Trabajo %s impreso en '%s' (%s)", t["id"], imp.get("nombre"), rol)
        except Exception as exc:  # noqa: BLE001 — cualquier fallo de impresión
            log.exception("Fallo al imprimir trabajo %s", t.get("id"))
            self._ack_seguro(t["id"], False, str(exc)[:280])

    def _ack_seguro(self, trabajo_id, ok, error="") -> None:
        try:
            self.client.ack(trabajo_id, ok, error)
        except Exception:
            log.exception("No se pudo confirmar (ack) el trabajo %s", trabajo_id)

    def run(self) -> None:
        backoff = 1
        while not self._stop.is_set():
            try:
                if not self.client.token:
                    self.on_status("sin_token", "Falta el token en config.ini")
                    self._esperar(5)
                    continue
                if not self._impresoras or (time.monotonic() - self._last_config) > _CONFIG_TTL:
                    self._refrescar_config()
                trabajos = self.client.get_trabajos()
                if trabajos:
                    self.on_status("imprimiendo", f"{len(trabajos)} trabajo(s)")
                    for t in trabajos:
                        self._procesar(t)
                self.on_status("ok", f"{len(self._impresoras)} impresora(s) · al día")
                backoff = 1
                self._esperar(self.poll)
            except ApiError as exc:
                self.on_status("error", str(exc))
                self._esperar(10)
            except Exception as exc:  # noqa: BLE001 — red caída, servidor, etc.
                log.exception("Error en el ciclo del worker")
                self.on_status("error", str(exc))
                backoff = min(backoff * 2, 30)
                self._esperar(backoff)

    def _esperar(self, segundos: float) -> None:
        # Espera interrumpible por poke()/stop().
        self._wake.wait(timeout=segundos)
        self._wake.clear()
