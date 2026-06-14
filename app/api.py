"""Health check endpoints para TUWAYKIFOOD.

Se integran con Reflex via api_transformer en app/app.py.
"""
from __future__ import annotations

import time
from datetime import datetime, timezone

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

_BOOT_TS = time.monotonic()


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _check_db() -> tuple[bool, str | None]:
    """SELECT 1 síncrono contra la DB de Food."""
    import os
    try:
        import pymysql
        from urllib.parse import unquote_plus

        conn = pymysql.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "3306")),
            user=unquote_plus(os.getenv("DB_USER", "root")),
            password=unquote_plus(os.getenv("DB_PASSWORD", "")),
            database=os.getenv("DB_NAME", "food_db"),
            connect_timeout=3,
        )
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
        finally:
            conn.close()
        return True, None
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


async def _health(request: Request) -> JSONResponse:
    """Readiness: verifica DB. Devuelve 503 si está caída."""
    uptime_s = round(time.monotonic() - _BOOT_TS, 1)
    db_ok, db_err = _check_db()
    payload = {
        "status": "ok" if db_ok else "degraded",
        "app": "tuwaykifood",
        "uptime_seconds": uptime_s,
        "timestamp": _utcnow_iso(),
        "checks": {
            "db": {"ok": db_ok, "error": db_err},
        },
    }
    return JSONResponse(content=payload, status_code=200 if db_ok else 503)


async def _ping(request: Request) -> JSONResponse:
    """Liveness: responde sin tocar DB. Usar en HEALTHCHECK de Docker."""
    return JSONResponse(content={"pong": True}, status_code=200)


health_app = Starlette(
    routes=[
        Route("/api/health", _health, methods=["GET"]),
        Route("/api/ping", _ping, methods=["GET"]),
    ],
)
