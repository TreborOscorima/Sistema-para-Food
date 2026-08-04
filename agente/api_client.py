"""Cliente HTTP de la API del agente (Fase 1).

Endpoints (auth por header X-Agent-Token: "<id>.<secreto>"):
- GET  /api/agente/config           -> {"impresoras": [...], "default_paper_width_mm": int}
- GET  /api/agente/trabajos         -> {"trabajos": [...]}
- POST /api/agente/trabajos/{id}/ack -> {"id":..., "estado": "impreso"|"error"}
"""
from __future__ import annotations

import requests


class ApiError(Exception):
    """Error de negocio/autorización de la API (p. ej. token inválido)."""


class ApiClient:
    def __init__(self, base_url: str, token: str, timeout: int = 15) -> None:
        self.base_url = (base_url or "").rstrip("/")
        self.token = (token or "").strip()
        self.timeout = timeout

    @property
    def _headers(self) -> dict:
        return {"X-Agent-Token": self.token}

    def _get(self, path: str) -> dict:
        r = requests.get(f"{self.base_url}{path}", headers=self._headers, timeout=self.timeout)
        if r.status_code == 401:
            raise ApiError("Token inválido o agente inactivo (401). Revisa config.ini.")
        r.raise_for_status()
        return r.json()

    def get_config(self) -> dict:
        return self._get("/api/agente/config")

    def get_trabajos(self) -> list[dict]:
        return self._get("/api/agente/trabajos").get("trabajos", [])

    def ack(self, trabajo_id: int, ok: bool, error: str = "") -> dict:
        r = requests.post(
            f"{self.base_url}/api/agente/trabajos/{trabajo_id}/ack",
            headers=self._headers,
            json={"ok": bool(ok), "error": error or ""},
            timeout=self.timeout,
        )
        if r.status_code == 401:
            raise ApiError("Token inválido (401) al confirmar el trabajo.")
        r.raise_for_status()
        return r.json()
