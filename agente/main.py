"""Punto de entrada del Agente de impresión TUWAYKIFOOD.

Arranca el ícono de bandeja (hilo principal) y el worker de polling (hilo daemon).
"""
from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

import config as config_mod
from api_client import ApiClient
from worker import Worker


def _setup_logging(base_dir) -> logging.Logger:
    log = logging.getLogger("agente")
    log.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    fh = RotatingFileHandler(
        base_dir / "agente.log", maxBytes=500_000, backupCount=3, encoding="utf-8"
    )
    fh.setFormatter(fmt)
    log.addHandler(fh)
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    log.addHandler(ch)
    return log


def main() -> None:
    base_dir = config_mod.base_dir()
    log = _setup_logging(base_dir)
    creado = config_mod.crear_plantilla_si_falta()
    cfg = config_mod.cargar()
    log.info("Agente iniciando. base_url=%s token=%s", cfg["base_url"], "sí" if cfg["token"] else "NO")
    if creado:
        log.warning("Se creó config.ini — completa el token del agente y reinicia.")

    client = ApiClient(cfg["base_url"], cfg["token"])
    worker = Worker(client, cfg["poll_segundos"])

    # La bandeja necesita pystray; se importa acá para poder correr/testear el
    # worker en entornos sin GUI.
    from tray import TrayApp

    app = TrayApp(worker=worker, config=cfg, base_dir=base_dir)
    worker.on_status = app.set_status
    worker.start()
    app.run()  # bloquea hasta "Salir"
    worker.stop()


if __name__ == "__main__":
    main()
