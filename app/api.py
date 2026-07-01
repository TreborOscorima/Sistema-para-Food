"""Health check + API pública de TUWAYKIFOOD.

Se integran con Reflex via api_transformer en app/app.py.
"""
from __future__ import annotations

import hashlib
import os
import pathlib
import re
import time
from datetime import datetime, timedelta, timezone

from sqlalchemy.exc import IntegrityError
from sqlmodel import select
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import FileResponse, JSONResponse, Response
from starlette.routing import Route

from tuwayki_core.utils.rate_limit import (
    clear_login_attempts,
    is_rate_limited,
    record_failed_attempt,
    remaining_lockout_time,
)
from tuwayki_core.utils.sanitization import sanitize_name, sanitize_phone
from tuwayki_core.utils.validators import validate_email, validate_password

from tuwayki_core.utils.logger import get_logger

from app.models.company import Company
from app.models.food import ConfigImpresora
from app.utils.db import get_session
from app.utils.tenant import tenant_bypass

logger = get_logger("api")

# Reflex 0.9.x no genera HTML estático para rutas dinámicas ([slug]).
# El static-files handler devuelve 404 para /menu/algo.
# Interceptamos /menu/{slug} antes y servimos el SPA entry point.
_BUILD_DIR = pathlib.Path(".web/build/client")

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


async def _menu_spa(request: Request) -> Response:
    """Sirve el SPA entry para /menu/{slug} — Reflex no pre-genera HTML para rutas dinámicas."""
    for candidate in ("__spa-fallback.html", "index.html"):
        p = _BUILD_DIR / candidate
        if p.exists():
            return FileResponse(str(p), media_type="text/html")
    return JSONResponse({"error": "frontend not built"}, status_code=503)


# ─── Registro público de restaurantes ─────────────────────────────────────────

def _slugify_registro(texto: str) -> str:
    texto = (texto or "").lower().strip()
    texto = re.sub(r"[áàä]", "a", texto)
    texto = re.sub(r"[éèë]", "e", texto)
    texto = re.sub(r"[íìï]", "i", texto)
    texto = re.sub(r"[óòö]", "o", texto)
    texto = re.sub(r"[úùü]", "u", texto)
    texto = re.sub(r"[ñ]", "n", texto)
    texto = re.sub(r"[^a-z0-9\s-]", "", texto)
    texto = re.sub(r"[\s]+", "-", texto)
    texto = re.sub(r"-+", "-", texto)
    return texto[:80].strip("-") or "restaurante"


def _trial_days() -> int:
    raw_value = (os.getenv("FOOD_TRIAL_DAYS") or "15").strip()
    try:
        days = int(raw_value)
    except (TypeError, ValueError):
        days = 15
    return max(1, min(days, 365))


def _client_ip(request: Request) -> str | None:
    forwarded = request.headers.get("x-forwarded-for") or request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return None


async def _registro(request: Request) -> JSONResponse:
    """Autoregistro público de un restaurante nuevo — crea Company + admin."""
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "JSON inválido."}, status_code=400)

    company_name = sanitize_name(body.get("company_name") or "").strip()
    email = (body.get("email") or "").strip().lower()
    phone = sanitize_phone(body.get("phone") or "").strip()
    password = body.get("password") or ""
    confirm_password = body.get("confirm_password") or ""
    client_ip = _client_ip(request)

    if is_rate_limited(email, ip_address=client_ip):
        remaining = remaining_lockout_time(email, ip_address=client_ip)
        return JSONResponse(
            {"error": f"Demasiados intentos. Espere {remaining} minuto(s) para registrar."},
            status_code=429,
        )

    if not company_name:
        return JSONResponse({"error": "El nombre del restaurante es obligatorio."}, status_code=400)
    if not email or not validate_email(email):
        return JSONResponse({"error": "Ingrese un correo válido."}, status_code=400)
    if not phone:
        return JSONResponse({"error": "El número de contacto es obligatorio."}, status_code=400)
    if password != confirm_password:
        return JSONResponse({"error": "Las contraseñas no coinciden."}, status_code=400)

    is_valid, error = validate_password(password)
    if not is_valid:
        return JSONResponse({"error": error}, status_code=400)

    try:
        with tenant_bypass():
            with get_session() as session:
                existing = session.exec(
                    select(ConfigImpresora).where(ConfigImpresora.admin_email == email)
                ).first()
                if existing:
                    record_failed_attempt(email, ip_address=client_ip)
                    return JSONResponse({"error": "El correo ya está registrado."}, status_code=409)

                base_slug = _slugify_registro(company_name)
                slug = base_slug
                suffix = 2
                while session.exec(
                    select(ConfigImpresora).where(ConfigImpresora.slug == slug)
                ).first():
                    slug = f"{base_slug}-{suffix}"
                    suffix += 1

                now = datetime.utcnow()
                company = Company(
                    name=company_name,
                    slug=slug,
                    is_active=True,
                    trial_ends_at=now + timedelta(days=_trial_days()),
                )
                session.add(company)
                session.flush()

                password_hash = hashlib.sha256(password.encode()).hexdigest()
                config = ConfigImpresora(
                    company_id=company.id,
                    nombre_local=company_name,
                    admin_email=email,
                    admin_password_hash=password_hash,
                    slug=slug,
                )
                session.add(config)
                session.commit()

                company_id = company.id
    except IntegrityError:
        record_failed_attempt(email, ip_address=client_ip)
        logger.error("Conflicto de integridad al registrar restaurante Food.", exc_info=True)
        return JSONResponse({"error": "El correo o el nombre ya están en uso."}, status_code=409)
    except Exception:
        logger.error("Error inesperado al registrar restaurante Food.", exc_info=True)
        return JSONResponse({"error": "No se pudo completar el registro."}, status_code=500)

    clear_login_attempts(email, ip_address=client_ip)
    return JSONResponse(
        {
            "company_id": company_id,
            "slug": slug,
            "message": "Cuenta creada. Ya puedes iniciar sesión.",
        },
        status_code=201,
    )


# ─── API admin (Owner Admin de Sistema-de-Ventas gestiona empresas Food) ──────

def _require_admin_secret(request: Request) -> JSONResponse | None:
    expected = (os.getenv("FOOD_ADMIN_API_SECRET") or "").strip()
    provided = request.headers.get("X-Admin-Secret", "")
    if not expected or provided != expected:
        return JSONResponse({"error": "No autorizado."}, status_code=401)
    return None


def _company_admin_dict(company: Company, config: ConfigImpresora | None) -> dict:
    return {
        "id": company.id,
        "name": company.name,
        "slug": company.slug,
        "admin_email": (config.admin_email if config else "") or "",
        "is_active": bool(company.is_active),
        "trial_ends_at": company.trial_ends_at.strftime("%Y-%m-%d") if company.trial_ends_at else None,
        "created_at": company.created_at.strftime("%Y-%m-%dT%H:%M:%SZ") if company.created_at else None,
    }


async def _admin_list_companies(request: Request) -> JSONResponse:
    err = _require_admin_secret(request)
    if err is not None:
        return err
    search = (request.query_params.get("search") or "").strip()
    try:
        page = max(1, int(request.query_params.get("page", "1")))
        per_page = max(1, min(100, int(request.query_params.get("per_page", "15"))))
    except ValueError:
        page, per_page = 1, 15

    with tenant_bypass():
        with get_session() as session:
            stmt = select(Company)
            if search:
                stmt = stmt.where(Company.name.ilike(f"%{search}%"))
            all_companies = session.exec(stmt.order_by(Company.id.desc())).all()
            total = len(all_companies)
            page_items = all_companies[(page - 1) * per_page: page * per_page]
            configs = {
                c.company_id: c
                for c in session.exec(
                    select(ConfigImpresora).where(
                        ConfigImpresora.company_id.in_([c.id for c in page_items])
                    )
                ).all()
            }
            items = [_company_admin_dict(c, configs.get(c.id)) for c in page_items]

    return JSONResponse({"items": items, "total": total}, status_code=200)


async def _admin_company_detail(request: Request) -> JSONResponse:
    err = _require_admin_secret(request)
    if err is not None:
        return err
    try:
        company_id = int(request.path_params["id"])
    except (KeyError, ValueError):
        return JSONResponse({"error": "id inválido."}, status_code=400)

    with tenant_bypass():
        with get_session() as session:
            company = session.get(Company, company_id)
            if company is None:
                return JSONResponse({"error": "No encontrado."}, status_code=404)
            config = session.exec(
                select(ConfigImpresora).where(ConfigImpresora.company_id == company_id)
            ).first()

    return JSONResponse(_company_admin_dict(company, config), status_code=200)


async def _admin_activate(request: Request) -> JSONResponse:
    return await _admin_set_active(request, True)


async def _admin_suspend(request: Request) -> JSONResponse:
    return await _admin_set_active(request, False)


async def _admin_set_active(request: Request, active: bool) -> JSONResponse:
    err = _require_admin_secret(request)
    if err is not None:
        return err
    try:
        company_id = int(request.path_params["id"])
    except (KeyError, ValueError):
        return JSONResponse({"error": "id inválido."}, status_code=400)

    with tenant_bypass():
        with get_session() as session:
            company = session.get(Company, company_id)
            if company is None:
                return JSONResponse({"error": "No encontrado."}, status_code=404)
            company.is_active = active
            company.updated_at = datetime.utcnow()
            session.add(company)
            session.commit()
            result = {"id": company.id, "is_active": company.is_active}

    return JSONResponse(result, status_code=200)


async def _admin_extend_trial(request: Request) -> JSONResponse:
    err = _require_admin_secret(request)
    if err is not None:
        return err
    try:
        company_id = int(request.path_params["id"])
    except (KeyError, ValueError):
        return JSONResponse({"error": "id inválido."}, status_code=400)
    try:
        body = await request.json()
        extra_days = int(body.get("extra_days"))
    except Exception:
        return JSONResponse({"error": "extra_days inválido."}, status_code=400)
    if extra_days < 1 or extra_days > 365:
        return JSONResponse({"error": "extra_days debe estar entre 1 y 365."}, status_code=400)

    with tenant_bypass():
        with get_session() as session:
            company = session.get(Company, company_id)
            if company is None:
                return JSONResponse({"error": "No encontrado."}, status_code=404)
            now = datetime.utcnow()
            base = company.trial_ends_at if company.trial_ends_at and company.trial_ends_at > now else now
            company.trial_ends_at = base + timedelta(days=extra_days)
            company.is_active = True
            company.updated_at = now
            session.add(company)
            session.commit()
            result = {"id": company.id, "trial_ends_at": company.trial_ends_at.strftime("%Y-%m-%d")}

    return JSONResponse(result, status_code=200)


health_app = Starlette(
    routes=[
        Route("/api/health", _health, methods=["GET"]),
        Route("/api/ping", _ping, methods=["GET"]),
        Route("/menu/{slug}", _menu_spa, methods=["GET"]),
        Route("/api/registro", _registro, methods=["POST"]),
        Route("/api/admin/companies", _admin_list_companies, methods=["GET"]),
        Route("/api/admin/companies/{id}", _admin_company_detail, methods=["GET"]),
        Route("/api/admin/companies/{id}/activate", _admin_activate, methods=["POST"]),
        Route("/api/admin/companies/{id}/suspend", _admin_suspend, methods=["POST"]),
        Route("/api/admin/companies/{id}/extend-trial", _admin_extend_trial, methods=["POST"]),
    ],
)
