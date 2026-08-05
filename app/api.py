"""Health check + API pública de TUWAYKIFOOD.

Se integran con Reflex via api_transformer en app/app.py.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import pathlib
import re
import time
from datetime import timedelta

from tuwayki_core.utils.timezone import utc_now_naive

from sqlalchemy import update as sa_update
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
from app.models.food import (
    ConfigImpresora,
    EstadoTrabajo,
    Impresora,
    TrabajoImpresion,
)
from app.services import print_queue
from app.utils.db import get_session
from app.utils.tenant import tenant_bypass

logger = get_logger("api")

# Reflex 0.9.x no genera HTML estático para rutas dinámicas ([slug]).
# El static-files handler devuelve 404 para /menu/algo.
# Interceptamos /menu/{slug} antes y servimos el SPA entry point.
_BUILD_DIR = pathlib.Path(".web/build/client")

_BOOT_TS = time.monotonic()


def _utcnow_iso() -> str:
    return utc_now_naive().strftime("%Y-%m-%dT%H:%M:%SZ")


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
        return JSONResponse({"error": "Ingresa un correo válido."}, status_code=400)
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

                now = utc_now_naive()
                company = Company(
                    name=company_name,
                    slug=slug,
                    is_active=True,
                    trial_ends_at=now + timedelta(days=_trial_days()),
                )
                session.add(company)
                session.flush()

                import bcrypt as _bcrypt_api
                password_hash = _bcrypt_api.hashpw(password.encode(), _bcrypt_api.gensalt()).decode()
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
    if not expected or not hmac.compare_digest(provided, expected):
        return JSONResponse({"error": "No autorizado."}, status_code=401)
    return None


def _company_admin_dict(company: Company, config: ConfigImpresora | None) -> dict:
    return {
        "id": company.id,
        "name": company.name,
        "slug": company.slug,
        "admin_email": (config.admin_email if config else "") or "",
        "is_active": bool(company.is_active),
        "plan": company.plan or "trial",
        "trial_ends_at": company.trial_ends_at.strftime("%Y-%m-%d") if company.trial_ends_at else None,
        "plan_expires_at": company.plan_expires_at.strftime("%Y-%m-%d") if company.plan_expires_at else None,
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
            company.updated_at = utc_now_naive()
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
            now = utc_now_naive()
            base = company.trial_ends_at if company.trial_ends_at and company.trial_ends_at > now else now
            company.trial_ends_at = base + timedelta(days=extra_days)
            company.is_active = True
            company.updated_at = now
            session.add(company)
            session.commit()
            result = {"id": company.id, "trial_ends_at": company.trial_ends_at.strftime("%Y-%m-%d")}

    return JSONResponse(result, status_code=200)


async def _admin_set_plan(request: Request) -> JSONResponse:
    err = _require_admin_secret(request)
    if err is not None:
        return err
    try:
        company_id = int(request.path_params["id"])
    except (KeyError, ValueError):
        return JSONResponse({"error": "id inválido."}, status_code=400)
    try:
        body = await request.json()
        plan = (body.get("plan") or "").strip().lower()
        expires_days = body.get("expires_days")
    except Exception:
        return JSONResponse({"error": "JSON inválido."}, status_code=400)

    from app.services.plan_service import PLANES_VALIDOS, plan_label
    if plan not in PLANES_VALIDOS:
        return JSONResponse(
            {"error": f"Plan inválido. Opciones: {', '.join(sorted(PLANES_VALIDOS))}"},
            status_code=400,
        )

    with tenant_bypass():
        with get_session() as session:
            company = session.get(Company, company_id)
            if company is None:
                return JSONResponse({"error": "No encontrado."}, status_code=404)
            now = utc_now_naive()
            company.plan = plan
            if expires_days is not None:
                try:
                    days = int(expires_days)
                    if days < 1 or days > 3650:
                        return JSONResponse({"error": "expires_days debe estar entre 1 y 3650."}, status_code=400)
                    company.plan_expires_at = now + timedelta(days=days)
                except (TypeError, ValueError):
                    return JSONResponse({"error": "expires_days debe ser un entero."}, status_code=400)
            else:
                company.plan_expires_at = None
            company.is_active = True
            company.updated_at = now
            session.add(company)
            session.commit()
            result = {
                "id": company.id,
                "plan": company.plan,
                "plan_label": plan_label(company.plan),
                "plan_expires_at": company.plan_expires_at.strftime("%Y-%m-%d") if company.plan_expires_at else None,
            }

    return JSONResponse(result, status_code=200)


async def _admin_renew_subscription(request: Request) -> JSONResponse:
    """Renueva la suscripción de un plan pago extendiendo su vencimiento.

    Mantiene el plan actual y suma `months` meses (x30 días). Si la suscripción
    sigue vigente, se apila sobre el vencimiento; si venció, cuenta desde hoy.
    Trial no se renueva por acá (usar Cambiar Plan o Extender Prueba).
    """
    err = _require_admin_secret(request)
    if err is not None:
        return err
    try:
        company_id = int(request.path_params["id"])
    except (KeyError, ValueError):
        return JSONResponse({"error": "id inválido."}, status_code=400)
    try:
        body = await request.json()
        months = int(body.get("months"))
    except Exception:
        return JSONResponse({"error": "months inválido."}, status_code=400)
    if months < 1 or months > 120:
        return JSONResponse({"error": "months debe estar entre 1 y 120."}, status_code=400)

    from app.services.plan_service import PLAN_TRIAL, plan_label

    with tenant_bypass():
        with get_session() as session:
            company = session.get(Company, company_id)
            if company is None:
                return JSONResponse({"error": "No encontrado."}, status_code=404)
            if (company.plan or PLAN_TRIAL) == PLAN_TRIAL:
                return JSONResponse(
                    {"error": "La empresa está en prueba. Usá Cambiar Plan o Extender Prueba."},
                    status_code=409,
                )
            now = utc_now_naive()
            base = (
                company.plan_expires_at
                if company.plan_expires_at and company.plan_expires_at > now
                else now
            )
            company.plan_expires_at = base + timedelta(days=months * 30)
            company.is_active = True
            company.updated_at = now
            session.add(company)
            session.commit()
            result = {
                "id": company.id,
                "plan": company.plan,
                "plan_label": plan_label(company.plan),
                "plan_expires_at": company.plan_expires_at.strftime("%Y-%m-%d"),
            }

    return JSONResponse(result, status_code=200)


async def _admin_list_users(request: Request) -> JSONResponse:
    """Cuentas cuya contraseña puede resetear el Owner Admin.

    En Food la cuenta administrable es la del **dueño** (Panel Administrativo:
    email + contraseña, guardada en ConfigImpresora). El personal operativo entra
    con PIN, que no se gestiona por acá.
    """
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
            items = []
            if config is not None and config.admin_email:
                items.append({
                    "id": company_id,
                    "username": config.admin_email,
                    "full_name": company.name,
                    "role": "Dueño",
                })

    return JSONResponse({"items": items}, status_code=200)


def _generar_password_temporal() -> str:
    """Contraseña temporal legible para entregar al dueño una sola vez."""
    import secrets
    return "Food-" + secrets.token_urlsafe(6)


async def _admin_reset_password(request: Request) -> JSONResponse:
    """Resetea la contraseña del dueño de una empresa Food.

    Genera una temporal, la guarda hasheada (bcrypt) y la devuelve UNA vez para
    que el Owner Admin se la pase al dueño. Queda auditado (sin el valor).
    """
    err = _require_admin_secret(request)
    if err is not None:
        return err
    try:
        company_id = int(request.path_params["id"])
    except (KeyError, ValueError):
        return JSONResponse({"error": "id inválido."}, status_code=400)
    try:
        body = await request.json()
    except Exception:
        body = {}
    actor = (body.get("actor") or body.get("actor_email") or "owner-admin").strip() or "owner-admin"

    import bcrypt as _bcrypt_api
    from app.services.auditoria_service import registrar_auditoria

    temp_password = _generar_password_temporal()
    with tenant_bypass():
        with get_session() as session:
            company = session.get(Company, company_id)
            if company is None:
                return JSONResponse({"error": "No encontrado."}, status_code=404)
            config = session.exec(
                select(ConfigImpresora).where(ConfigImpresora.company_id == company_id)
            ).first()
            if config is None or not config.admin_email:
                return JSONResponse(
                    {"error": "La empresa no tiene cuenta de dueño configurada."},
                    status_code=409,
                )
            config.admin_password_hash = _bcrypt_api.hashpw(
                temp_password.encode(), _bcrypt_api.gensalt()
            ).decode()
            config.updated_at = utc_now_naive()
            session.add(config)
            registrar_auditoria(
                session, company_id, "reset_password_owner",
                usuario_nombre=actor,
                entidad="config_impresora", entidad_id=company_id,
                detalle={
                    "origen": "owner_admin",
                    "actor": actor,
                    "email": config.admin_email,
                    "password_reseteada": True,
                },
            )
            session.commit()
            username = config.admin_email

    return JSONResponse(
        {"temp_password": temp_password, "username": username}, status_code=200
    )


# ─── API del agente de impresión local ────────────────────────────────────────
# El agente se autentica con `X-Agent-Token: "<id>.<secreto>"`. Todas las rutas
# filtran explícitamente por company_id del agente bajo tenant_bypass().

# Segundos sin ack tras los que un trabajo "entregado" se reencola (agente que
# crasheó mientras imprimía).
_ACK_TIMEOUT_S = 90


def _agente_from_request(session, request: Request):
    token = request.headers.get("X-Agent-Token", "")
    agente = print_queue.verificar_token(session, token)
    if agente is not None:
        agente.last_seen_at = utc_now_naive()
        session.add(agente)
        session.commit()
    return agente


def _reaper_reencolar(session, company_id: int) -> None:
    cutoff = utc_now_naive() - timedelta(seconds=_ACK_TIMEOUT_S)
    session.exec(
        sa_update(TrabajoImpresion)
        .where(
            TrabajoImpresion.company_id == company_id,
            TrabajoImpresion.estado == EstadoTrabajo.ENTREGADO.value,
            TrabajoImpresion.claimed_at < cutoff,
        )
        .values(estado=EstadoTrabajo.PENDIENTE.value, claimed_at=None)
    )
    session.commit()


async def _agente_config(request: Request) -> JSONResponse:
    with tenant_bypass():
        with get_session() as session:
            agente = _agente_from_request(session, request)
            if agente is None:
                return JSONResponse({"error": "No autorizado."}, status_code=401)
            cfg = session.exec(
                select(ConfigImpresora).where(
                    ConfigImpresora.company_id == agente.company_id
                )
            ).first()
            default_width = cfg.ticket_paper_width_mm if cfg else 80
            stmt = select(Impresora).where(
                Impresora.company_id == agente.company_id,
                Impresora.activa.is_(True),
            )
            if agente.sucursal_id is not None:
                stmt = stmt.where(Impresora.sucursal_id == agente.sucursal_id)
            imps = session.exec(stmt.order_by(Impresora.id)).all()
            items = [
                {
                    "id": i.id,
                    "nombre": i.nombre,
                    "rol": i.rol,
                    "tipo": i.tipo,
                    "ip": i.ip,
                    "puerto": i.puerto,
                    "usb_target": i.usb_target,
                    "paper_width_mm": i.paper_width_mm or default_width,
                }
                for i in imps
            ]
    return JSONResponse(
        {"impresoras": items, "default_paper_width_mm": default_width},
        status_code=200,
    )


async def _agente_trabajos(request: Request) -> JSONResponse:
    with tenant_bypass():
        with get_session() as session:
            agente = _agente_from_request(session, request)
            if agente is None:
                return JSONResponse({"error": "No autorizado."}, status_code=401)
            # Reencolar trabajos entregados sin ack (agente caído).
            _reaper_reencolar(session, agente.company_id)
            # Reclamar comandas nuevas de cocina y encolarlas.
            print_queue.reclamar_comandas_pendientes(
                session, agente.company_id, agente.sucursal_id
            )
            # Entregar todos los pendientes de esta empresa/sucursal.
            stmt = select(TrabajoImpresion).where(
                TrabajoImpresion.company_id == agente.company_id,
                TrabajoImpresion.estado == EstadoTrabajo.PENDIENTE.value,
            )
            if agente.sucursal_id is not None:
                stmt = stmt.where(TrabajoImpresion.sucursal_id == agente.sucursal_id)
            trabajos = session.exec(stmt.order_by(TrabajoImpresion.id)).all()
            now = utc_now_naive()
            items = []
            for t in trabajos:
                t.estado = EstadoTrabajo.ENTREGADO.value
                t.claimed_at = now
                session.add(t)
                items.append(
                    {
                        "id": t.id,
                        "rol": t.rol,
                        "tipo_doc": t.tipo_doc,
                        "contenido": t.contenido,
                        "paper_width_mm": t.paper_width_mm,
                        "pedido_id": t.pedido_id,
                    }
                )
            session.commit()
    return JSONResponse({"trabajos": items}, status_code=200)


async def _agente_ack(request: Request) -> JSONResponse:
    try:
        trabajo_id = int(request.path_params["id"])
    except (KeyError, ValueError):
        return JSONResponse({"error": "id inválido."}, status_code=400)
    try:
        body = await request.json()
    except Exception:
        body = {}
    ok = bool(body.get("ok", True))
    error_msg = (body.get("error") or "")[:300]

    with tenant_bypass():
        with get_session() as session:
            agente = _agente_from_request(session, request)
            if agente is None:
                return JSONResponse({"error": "No autorizado."}, status_code=401)
            trabajo = session.get(TrabajoImpresion, trabajo_id)
            if trabajo is None or trabajo.company_id != agente.company_id:
                return JSONResponse({"error": "No encontrado."}, status_code=404)
            trabajo.estado = (
                EstadoTrabajo.IMPRESO.value if ok else EstadoTrabajo.ERROR.value
            )
            trabajo.error_msg = None if ok else (error_msg or "Error de impresión")
            trabajo.intentos = (trabajo.intentos or 0) + 1
            trabajo.done_at = utc_now_naive()
            session.add(trabajo)
            session.commit()
            result = {"id": trabajo.id, "estado": trabajo.estado}
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
        Route("/api/admin/companies/{id}/set-plan", _admin_set_plan, methods=["POST"]),
        Route("/api/admin/companies/{id}/renew", _admin_renew_subscription, methods=["POST"]),
        Route("/api/admin/companies/{id}/users", _admin_list_users, methods=["GET"]),
        Route("/api/admin/companies/{id}/reset-password", _admin_reset_password, methods=["POST"]),
        Route("/api/agente/config", _agente_config, methods=["GET"]),
        Route("/api/agente/trabajos", _agente_trabajos, methods=["GET"]),
        Route("/api/agente/trabajos/{id}/ack", _agente_ack, methods=["POST"]),
    ],
)
