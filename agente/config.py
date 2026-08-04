"""Configuración del agente: lee/crea config.ini junto al ejecutable."""
from __future__ import annotations

import configparser
import sys
from pathlib import Path

DEFAULTS = {
    "base_url": "https://food.tuwayki.app",
    "token": "",
    "poll_segundos": "3",
}


def base_dir() -> Path:
    """Carpeta del .exe (PyInstaller) o del script en desarrollo."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def bundle_dir() -> Path:
    """Carpeta de recursos empaquetados (assets). En PyInstaller onefile es
    el directorio temporal _MEIPASS; en desarrollo, la carpeta del script."""
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        return Path(meipass)
    return base_dir()


def config_path() -> Path:
    return base_dir() / "config.ini"


def _to_int(value: str | None, default: int) -> int:
    try:
        return max(1, int(str(value).strip()))
    except (TypeError, ValueError):
        return default


def cargar() -> dict:
    """Devuelve la config efectiva (con defaults). No falla si el archivo no existe."""
    cp = configparser.ConfigParser()
    path = config_path()
    if path.exists():
        cp.read(path, encoding="utf-8")
    sec = cp["agente"] if cp.has_section("agente") else {}
    return {
        "base_url": (sec.get("base_url") or DEFAULTS["base_url"]).strip().rstrip("/"),
        "token": (sec.get("token") or "").strip(),
        "poll_segundos": _to_int(sec.get("poll_segundos"), 3),
    }


def crear_plantilla_si_falta() -> bool:
    """Crea un config.ini vacío (con base_url) si no existe. Devuelve True si lo creó."""
    path = config_path()
    if path.exists():
        return False
    cp = configparser.ConfigParser()
    cp["agente"] = {
        "base_url": DEFAULTS["base_url"],
        "token": "",
        "poll_segundos": "3",
    }
    with open(path, "w", encoding="utf-8") as fh:
        cp.write(fh)
    return True
