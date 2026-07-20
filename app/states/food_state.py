"""Estado global de TUWAYKIFOOD — mozos, caja, cocina, mostrador, carta."""

from __future__ import annotations

import asyncio
import base64
import hashlib
import hmac
import io
import json as _json
import os
import pathlib
import re
import secrets
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation

import bcrypt as _bcrypt

import reflex as rx
from pydantic import BaseModel
from sqlalchemy import and_, or_, update as sa_update
from sqlmodel import select

from app.models.company import Company
from app.models.food import (
    Categoria,
    Cliente,
    Combo,
    ComboItem,
    ConfigImpresora,
    CuponLote,
    CuentaCorriente,
    DetallePedido,
    EstacionCocina,
    EstadoMesa,
    EstadoPedido,
    EstadoProduccion,
    GrupoModificador,
    Insumo,
    Mesa,
    MovimientoCuenta,
    OpcionModificador,
    Pedido,
    Producto,
    ProductoGrupoModificador,
    Promocion,
    RecetaItem,
    Reserva,
    EstadoReserva,
    RolUsuario,
    Sucursal,
    TipoPedido,
    TipoPromocion,
    UsuarioFood,
)
from app.services.receipt_service import (
    TicketLine,
    build_print_script,
    generate_cashier_ticket_html,
    generate_kitchen_ticket_html,
    generate_precuenta_html,
)
from tuwayki_core.utils.timezone import format_local_datetime, utc_now_naive

from app.models.food import MovimientoInsumo, PagoPedido, TipoMovimientoInsumo
from app.services.analitica_service import (
    margen_por_plato,
    ventas_por_hora,
    ventas_por_mozo,
)
from app.services.auditoria_service import registrar_auditoria
from app.utils.image import optimize_image
from app.services.anulacion_service import (
    anular_pedido_abierto,
    anular_venta_cobrada,
    reponer_stock_por_pedido,
    revertir_fiado_pedido,
)
from app.services.kardex_service import (
    CATEGORIAS_MERMA,
    registrar_ajuste,
    registrar_consumo,
    registrar_entrada,
    registrar_merma,
)
from app.services.pago_service import (
    metodo_pago_resumen,
    registrar_pagos_pedido,
    validar_pagos,
)
from app.services.suscripcion_service import evaluar_bloqueo
from app.services.plan_service import (
    PAGINAS_PREMIUM,
    MSG_UPGRADE,
    plan_permite,
    plan_label,
    check_limite_mesas,
)
from tuwayki_core.utils.rate_limit import (
    clear_login_attempts as _clear_login_attempts,
    is_rate_limited as _is_rate_limited,
    record_failed_attempt as _record_failed_attempt,
    remaining_lockout_time as _remaining_lockout_time,
)
from app.services.promo_service import (
    DIAS_SEMANA as PROMO_DIAS,
    ItemCobro,
    ahora_local_pe,
    mejor_promo,
    promo_vigente,
)
from app.services.cupon_service import redimir_cupon, validar_cupon
from app.states.caja_turno_mixin import CajaTurnoMixin, get_turno_abierto
from app.utils.db import get_session
from app.utils.tenant import set_tenant_context, tenant_bypass

# ─── Helpers de polling (compare-before-assign para evitar reenvío innecesario
# de listas completas por websocket cada 3s) ──────────────────────────────────

def _mesas_fingerprint(mesas: list) -> tuple:
    """Fingerprint estable de mesas — excluye tiempo_abierto_texto (cambia cada tick)."""
    return tuple(
        (m.id, m.estado, m.total_abierto, m.items_listos_count, m.items_total_count)
        for m in mesas
    )


def _list_fingerprint(items: list) -> tuple:
    """Fingerprint genérico para listas de BaseModel (tickets cocina, mostrador)."""
    return tuple(item.model_dump_json() for item in items)


# ─── Constantes de negocio ───────────────────────────────────────────────────
CURRENCY_SYMBOL = "S/"

OPEN_ORDER_STATES = (
    EstadoPedido.BORRADOR.value,
    EstadoPedido.ENVIADO.value,
    EstadoPedido.EN_PREPARACION.value,
    EstadoPedido.LISTO.value,
)

PEDIDO_EXPIRACION_MIN = 480
PEDIDO_ALERTA_INACTIVIDAD_MIN = 240

KITCHEN_VISIBLE_STATES = (
    EstadoProduccion.PENDIENTE.value,
    EstadoProduccion.EN_PREPARACION.value,
    EstadoProduccion.LISTO_PARA_ENTREGAR.value,
)

MESA_LABELS = {
    EstadoMesa.LIBRE.value: "Libre",
    EstadoMesa.OCUPADA.value: "Ocupada",
    EstadoMesa.ESPERANDO_CUENTA.value: "Esperando cuenta",
}
MESA_BADGE_BACKGROUNDS = {
    EstadoMesa.LIBRE.value: "rgba(51,65,85,0.5)",
    EstadoMesa.OCUPADA.value: "rgba(234,88,12,0.18)",
    EstadoMesa.ESPERANDO_CUENTA.value: "rgba(245,158,11,0.18)",
}
MESA_BADGE_TEXTS = {
    EstadoMesa.LIBRE.value: "#94A3B8",
    EstadoMesa.OCUPADA.value: "#FDBA74",
    EstadoMesa.ESPERANDO_CUENTA.value: "#FCD34D",
}
MESA_CARD_BACKGROUNDS = {
    EstadoMesa.LIBRE.value: "#1E293B",
    EstadoMesa.OCUPADA.value: "#1E293B",
    EstadoMesa.ESPERANDO_CUENTA.value: "#1E293B",
}
MESA_CARD_BORDERS = {
    EstadoMesa.LIBRE.value: "2px solid #334155",
    EstadoMesa.OCUPADA.value: "2px solid #EA580C",
    EstadoMesa.ESPERANDO_CUENTA.value: "2px solid #F59E0B",
}
READY_ALERT_BORDER = "3px solid #F59E0B"

_SOUND_BELL_JS = """(function(){try{var c=new(window.AudioContext||window.webkitAudioContext)();var o=c.createOscillator();var g=c.createGain();o.type='triangle';o.frequency.value=880;g.gain.setValueAtTime(0.3,c.currentTime);g.gain.exponentialRampToValueAtTime(0.01,c.currentTime+0.4);o.connect(g);g.connect(c.destination);o.start();o.stop(c.currentTime+0.4)}catch(e){}})()"""
_SOUND_CHIME_JS = """(function(){try{var c=new(window.AudioContext||window.webkitAudioContext)();function b(f,t){var o=c.createOscillator();var g=c.createGain();o.type='sine';o.frequency.value=f;g.gain.setValueAtTime(0.25,c.currentTime+t);g.gain.exponentialRampToValueAtTime(0.01,c.currentTime+t+0.3);o.connect(g);g.connect(c.destination);o.start(c.currentTime+t);o.stop(c.currentTime+t+0.3)}b(659,0);b(784,0.15);b(988,0.3)}catch(e){}})()"""
_VIBRATE_JS = """(function(){try{if(navigator.vibrate)navigator.vibrate([200,100,200])}catch(e){}})()"""

PRODUCTION_LABELS = {
    EstadoProduccion.PENDIENTE.value: "Pendiente",
    EstadoProduccion.EN_PREPARACION.value: "En preparacion",
    EstadoProduccion.LISTO_PARA_ENTREGAR.value: "Listo para entregar",
    EstadoProduccion.ENTREGADO_AL_CLIENTE.value: "Entregado al cliente",
}
PRODUCTION_BADGE_BACKGROUNDS = {
    EstadoProduccion.PENDIENTE.value: "#F59E0B",
    EstadoProduccion.EN_PREPARACION.value: "#EA580C",
    EstadoProduccion.LISTO_PARA_ENTREGAR.value: "#16A34A",
    EstadoProduccion.ENTREGADO_AL_CLIENTE.value: "#3B82F6",
}
PRODUCTION_BADGE_TEXTS = {
    EstadoProduccion.PENDIENTE.value: "#FFFFFF",
    EstadoProduccion.EN_PREPARACION.value: "#FFFFFF",
    EstadoProduccion.LISTO_PARA_ENTREGAR.value: "#FFFFFF",
    EstadoProduccion.ENTREGADO_AL_CLIENTE.value: "#FFFFFF",
}
KITCHEN_CARD_BACKGROUNDS = {
    EstadoProduccion.PENDIENTE.value: "#0F172A",
    EstadoProduccion.EN_PREPARACION.value: "#0F172A",
    EstadoProduccion.LISTO_PARA_ENTREGAR.value: "#0F172A",
}
KITCHEN_CARD_BORDERS = {
    EstadoProduccion.PENDIENTE.value: "#F59E0B",
    EstadoProduccion.EN_PREPARACION.value: "#EA580C",
    EstadoProduccion.LISTO_PARA_ENTREGAR.value: "#16A34A",
}
KITCHEN_DEMORADO_MINUTOS = 15
KITCHEN_DEMORADO_COLOR = "#DC2626"
CLIENTE_VIP_VISITAS_MIN = 15

ROLE_HOME_ROUTES: dict[str, str] = {
    RolUsuario.MOZO.value: "/mozos",
    RolUsuario.CAJA.value: "/caja",
    RolUsuario.COCINA.value: "/cocina",
    RolUsuario.ADMIN.value: "/carta",
}
ROLE_ALLOWED_ROUTES: dict[str, set[str]] = {
    "mozos": {RolUsuario.MOZO.value, RolUsuario.ADMIN.value},
    "caja": {RolUsuario.CAJA.value, RolUsuario.ADMIN.value},
    "mostrador": {RolUsuario.CAJA.value, RolUsuario.ADMIN.value},
    "cocina": {RolUsuario.COCINA.value, RolUsuario.ADMIN.value},
    "carta": {RolUsuario.ADMIN.value},
    "reportes": {RolUsuario.ADMIN.value},
    "usuarios": {RolUsuario.ADMIN.value},
    "configuracion": {RolUsuario.ADMIN.value},
    "inventario": {RolUsuario.ADMIN.value},
    "clientes": {RolUsuario.ADMIN.value},
    "cuentas": {RolUsuario.ADMIN.value},
    "promociones": {RolUsuario.ADMIN.value},
    "cupones": {RolUsuario.ADMIN.value},
}

_ROL_LABELS: dict[str, str] = {
    RolUsuario.ADMIN.value: "Admin",
    RolUsuario.MOZO.value: "Mozo",
    RolUsuario.CAJA.value: "Caja",
    RolUsuario.COCINA.value: "Cocina",
}
_ROL_BADGE_BG: dict[str, str] = {
    RolUsuario.ADMIN.value: "rgba(234,88,12,0.12)",
    RolUsuario.MOZO.value: "rgba(59,130,246,0.12)",
    RolUsuario.CAJA.value: "rgba(34,197,94,0.12)",
    RolUsuario.COCINA.value: "rgba(245,158,11,0.12)",
}
_ROL_BADGE_TEXT: dict[str, str] = {
    RolUsuario.ADMIN.value: "#EA580C",
    RolUsuario.MOZO.value: "#3B82F6",
    RolUsuario.CAJA.value: "#22C55E",
    RolUsuario.COCINA.value: "#F59E0B",
}
_ROL_PERM_DEFAULTS: dict[str, dict[str, bool]] = {
    RolUsuario.ADMIN.value:  {"descuento": True,  "anular": True,  "reportes": True,  "turno": True,  "inventario": True,  "costos": True,  "reimprimir": True},
    RolUsuario.CAJA.value:   {"descuento": True,  "anular": False, "reportes": False, "turno": True,  "inventario": False, "costos": False, "reimprimir": True},
    RolUsuario.MOZO.value:   {"descuento": False, "anular": False, "reportes": False, "turno": False, "inventario": False, "costos": False, "reimprimir": False},
    RolUsuario.COCINA.value: {"descuento": False, "anular": False, "reportes": False, "turno": False, "inventario": False, "costos": False, "reimprimir": False},
}
_ROL_ACCESO_DEFAULTS: dict[str, dict[str, bool]] = {
    RolUsuario.ADMIN.value:  {"mozos": True,  "caja": True,  "cocina": True,  "mostrador": True},
    RolUsuario.MOZO.value:   {"mozos": True,  "caja": False, "cocina": False, "mostrador": False},
    RolUsuario.CAJA.value:   {"mozos": False, "caja": True,  "cocina": False, "mostrador": True},
    RolUsuario.COCINA.value: {"mozos": False, "caja": False, "cocina": True,  "mostrador": False},
}

# Base URLs leídas del entorno en tiempo de importación. El company_id ya no es
# fijo: FoodState._company_id() lo resuelve por sesión (ver clase FoodState).
_FOOD_BASE_URL: str = (os.getenv("FOOD_BASE_URL") or os.getenv("PUBLIC_API_URL", "http://localhost:3003")).rstrip("/")
_FOOD_API_URL: str = os.getenv("PUBLIC_API_URL", "http://localhost:3004").rstrip("/")


def _utcnow() -> datetime:
    """Datetime UTC naive compatible con columnas MySQL sin TZ."""
    return datetime.now(timezone.utc).replace(tzinfo=None)

# Operativo: 8 horas (turno completo). Admin local: 2 horas.
_SESSION_TIMEOUT_OPERATIVO_S = 8 * 3600
_SESSION_TIMEOUT_ADMIN_S = 2 * 3600

_COOKIE_SECRET: str = (
    os.getenv("FOOD_ADMIN_API_SECRET")
    or "fallback-dev-key-not-for-prod"
)


def _sign_session(payload: dict) -> str:
    raw = _json.dumps(payload, separators=(",", ":"), sort_keys=True)
    sig = hmac.new(
        _COOKIE_SECRET.encode(), raw.encode(), hashlib.sha256
    ).hexdigest()
    return base64.urlsafe_b64encode(f"{raw}|{sig}".encode()).decode()


def _verify_session(token: str) -> dict | None:
    try:
        decoded = base64.urlsafe_b64decode(token.encode()).decode()
        raw, sig = decoded.rsplit("|", 1)
        expected = hmac.new(
            _COOKIE_SECRET.encode(), raw.encode(), hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(sig, expected):
            return None
        return _json.loads(raw)
    except Exception:
        return None


def _session_expired(ultima_actividad_iso: str, rol: str) -> bool:
    if not ultima_actividad_iso:
        return False
    try:
        last = datetime.fromisoformat(ultima_actividad_iso)
    except ValueError:
        return True
    timeout = _SESSION_TIMEOUT_ADMIN_S if rol == RolUsuario.ADMIN.value else _SESSION_TIMEOUT_OPERATIVO_S
    return (_utcnow() - last).total_seconds() > timeout


def _bloqueo_suscripcion(company_id: int) -> str:
    """'' si la empresa puede operar; mensaje de bloqueo si está suspendida o
    su período de prueba venció. Se verifica al iniciar sesión y en cada carga
    de página operativa (enforcement del plan, gestionado desde el Owner Admin)."""
    if not company_id:
        return "Empresa no válida."
    with tenant_bypass():
        with get_session() as session:
            company = session.get(Company, company_id)
    return evaluar_bloqueo(company, _utcnow())


def _hash_pin(plain: str) -> str:
    """Hashea un PIN con bcrypt. Retorna el hash como str."""
    return _bcrypt.hashpw(plain.encode(), _bcrypt.gensalt()).decode()


def _verify_pin(plain: str, hashed: str) -> bool:
    """Verifica un PIN contra su hash bcrypt."""
    try:
        return _bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False


# ─── Helpers puros ───────────────────────────────────────────────────────────

def _slugify(texto: str) -> str:
    """Convierte texto a slug URL-safe (minúsculas, solo alfanumérico y guión)."""
    texto = texto.lower().strip()
    texto = re.sub(r"[áàä]", "a", texto)
    texto = re.sub(r"[éèë]", "e", texto)
    texto = re.sub(r"[íìï]", "i", texto)
    texto = re.sub(r"[óòö]", "o", texto)
    texto = re.sub(r"[úùü]", "u", texto)
    texto = re.sub(r"[ñ]", "n", texto)
    texto = re.sub(r"[^a-z0-9\s-]", "", texto)
    texto = re.sub(r"[\s]+", "-", texto)
    texto = re.sub(r"-+", "-", texto)
    return texto[:80].strip("-") or "mi-restaurante"


def _generar_qr_base64(url: str) -> str:
    try:
        import qrcode
        qr = qrcode.QRCode(version=None, box_size=6, border=3)
        qr.add_data(url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="#0F172A", back_color="#FFFFFF")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
    except Exception:
        return ""


def _to_decimal(value) -> Decimal:
    if value is None:
        return Decimal("0.00")
    if isinstance(value, Decimal):
        return value.quantize(Decimal("0.01"))
    return Decimal(str(value)).quantize(Decimal("0.01"))


def _money_text(value) -> str:
    return f"{CURRENCY_SYMBOL} {_to_decimal(value):.2f}"


_PRODUCTO_EMOJI_KEYWORDS: list[tuple[str, str]] = [
    ("pizza", "🍕"),
    ("hamburgues", "🍔"),
    ("sandwich", "🥪"),
    ("sanguche", "🥪"),
    ("pan ", "🥪"),
    ("pescado", "🐟"),
    ("ceviche", "🐟"),
    ("gallina", "🍗"),
    ("pollo", "🍗"),
    ("brasa", "🍗"),
    ("carne", "🥩"),
    ("lomo", "🥩"),
    ("bife", "🥩"),
    ("milanesa", "🥩"),
    ("chancho", "🥩"),
    ("cerdo", "🥩"),
    ("pasta", "🍝"),
    ("tallarin", "🍝"),
    ("spaghetti", "🍝"),
    ("fideos", "🍝"),
    ("ensalada", "🥗"),
    ("sopa", "🍲"),
    ("caldo", "🍲"),
    ("chupe", "🍲"),
    ("causa", "🥔"),
    ("papa", "🍟"),
    ("arroz", "🍚"),
    ("huevo", "🥚"),
    ("torta", "🍰"),
    ("mazamorra", "🍰"),
    ("helado", "🍨"),
    ("flan", "🍮"),
    ("postre", "🍰"),
    ("cafe", "☕"),
    ("café", "☕"),
    ("cerveza", "🍺"),
    ("vino", "🍷"),
    ("chicha", "🥤"),
    ("agua", "💧"),
    ("gaseosa", "🥤"),
    ("cola", "🥤"),
    ("kola", "🥤"),
    ("jugo", "🥤"),
    ("bebida", "🥤"),
    ("empanada", "🥟"),
    ("wrap", "🫔"),
]

_CATEGORIA_EMOJI_KEYWORDS: list[tuple[str, str]] = [
    ("bebida", "🥤"),
    ("postre", "🍰"),
    ("entrada", "🥗"),
    ("ensalada", "🥗"),
    ("hamburgues", "🍔"),
    ("pizza", "🍕"),
    ("principal", "🍖"),
    ("fondo", "🍖"),
    ("carta", "🍽️"),
]


def _emoji_para_producto(nombre: str) -> str:
    n = nombre.lower()
    for kw, emoji in _PRODUCTO_EMOJI_KEYWORDS:
        if kw in n:
            return emoji
    return "🍽️"


def _emoji_para_categoria(nombre: str) -> str:
    n = nombre.lower()
    for kw, emoji in _CATEGORIA_EMOJI_KEYWORDS:
        if kw in n:
            return emoji
    return "🍽️"


_TAG_LABELS: dict[str, str] = {
    "picante": "🌶️ Picante",
    "veggie": "🌱 Vegetariano",
    "vegano": "🥦 Vegano",
    "sin_gluten": "🚫🌾 Sin gluten",
    "frutos_secos": "🥜 Frutos secos",
    "lacteos": "🥛 Lácteos",
}


def _tags_to_text(tags: list[str] | None) -> str:
    if not tags:
        return ""
    return " · ".join(_TAG_LABELS.get(t, t) for t in tags)


def _parse_positive_price(raw: str) -> Decimal | None:
    try:
        value = Decimal(raw.replace(",", ".").strip())
    except (InvalidOperation, AttributeError):
        return None
    return value.quantize(Decimal("0.01")) if value > 0 else None


def _normalize_pin(raw: str) -> str:
    return "".join(c for c in str(raw) if c.isdigit())[:6]


def _role_home_route(role: str) -> str:
    return ROLE_HOME_ROUTES.get(role, "/login")


def _actor_name(value: str | None) -> str:
    return (value or "").strip()


def _pedido_table_label(pedido: Pedido, mesas: dict) -> str:
    if pedido.mesa_id is None:
        return "Mesa no asignada"
    mesa = mesas.get(pedido.mesa_id)
    if mesa is None:
        return f"Mesa {pedido.mesa_id}"
    return mesa.nombre or f"Mesa {mesa.numero}"


def _pedido_kitchen_label(pedido: Pedido, mesas: dict) -> str:
    if pedido.tipo_pedido == TipoPedido.MOSTRADOR.value:
        return f"Para Llevar - Cliente: {_actor_name(pedido.nombre_cliente) or 'Sin nombre'}"
    return _pedido_table_label(pedido, mesas)


def _pedido_sales_label(pedido: Pedido, mesas: dict) -> str:
    if pedido.tipo_pedido == TipoPedido.MOSTRADOR.value:
        return f"Mostrador ({_actor_name(pedido.nombre_cliente) or 'Sin nombre'})"
    return _pedido_table_label(pedido, mesas)


def _get_open_order(session, mesa_id: int, company_id: int) -> Pedido | None:
    return session.exec(
        select(Pedido).where(
            Pedido.company_id == company_id,
            Pedido.mesa_id == mesa_id,
            Pedido.estado.in_(OPEN_ORDER_STATES),
        ).order_by(Pedido.id.desc())
    ).first()


def _get_unsent_details(session, pedido_id: int) -> list:
    return session.exec(
        select(DetallePedido).where(
            DetallePedido.pedido_id == pedido_id,
            DetallePedido.impreso_cocina.is_(False),
        ).order_by(DetallePedido.id)
    ).all()


def _get_ready_details(session, pedido_id: int) -> list:
    return session.exec(
        select(DetallePedido).where(
            DetallePedido.pedido_id == pedido_id,
            DetallePedido.impreso_cocina.is_(True),
            DetallePedido.estado_produccion == EstadoProduccion.LISTO_PARA_ENTREGAR.value,
        ).order_by(DetallePedido.id)
    ).all()


def _get_not_delivered_details(session, pedido_id: int) -> list:
    return session.exec(
        select(DetallePedido).where(
            DetallePedido.pedido_id == pedido_id,
            DetallePedido.impreso_cocina.is_(True),
            DetallePedido.estado_produccion != EstadoProduccion.ENTREGADO_AL_CLIENTE.value,
        ).order_by(DetallePedido.id)
    ).all()


def _recalculate_order_total(session, pedido: Pedido) -> Decimal:
    detalles = session.exec(
        select(DetallePedido).where(DetallePedido.pedido_id == pedido.id)
    ).all()
    total = sum((_to_decimal(d.subtotal) for d in detalles), Decimal("0.00"))
    pedido.total = total
    pedido.updated_at = _utcnow()
    session.add(pedido)
    return total


def _sync_order_status(session, pedido: Pedido) -> None:
    if pedido.estado == EstadoPedido.COBRADO.value or pedido.estado == EstadoPedido.CANCELADO.value:
        return
    sent_details = session.exec(
        select(DetallePedido).where(
            DetallePedido.pedido_id == pedido.id,
            DetallePedido.impreso_cocina.is_(True),
        )
    ).all()
    if not sent_details:
        pedido.estado = EstadoPedido.BORRADOR.value
    elif pedido.pagado and all(d.estado_produccion == EstadoProduccion.ENTREGADO_AL_CLIENTE.value for d in sent_details):
        pedido.estado = EstadoPedido.COBRADO.value
    elif any(d.estado_produccion == EstadoProduccion.LISTO_PARA_ENTREGAR.value for d in sent_details):
        pedido.estado = EstadoPedido.LISTO.value
    elif any(d.estado_produccion == EstadoProduccion.EN_PREPARACION.value for d in sent_details):
        pedido.estado = EstadoPedido.EN_PREPARACION.value
    elif any(d.estado_produccion == EstadoProduccion.PENDIENTE.value for d in sent_details):
        pedido.estado = EstadoPedido.ENVIADO.value
    else:
        pedido.estado = EstadoPedido.ENVIADO.value
    pedido.updated_at = _utcnow()
    session.add(pedido)


def _ensure_open_order(session, mesa: Mesa, company_id: int, mozo_id: int | None = None, sucursal_id: int = 0) -> Pedido:
    pedido = _get_open_order(session, mesa.id or 0, company_id)
    if pedido is not None:
        if mozo_id is not None and pedido.mozo_id is None:
            pedido.mozo_id = mozo_id
            pedido.updated_at = _utcnow()
            session.add(pedido)
        return pedido
    pedido = Pedido(
        company_id=company_id,
        sucursal_id=sucursal_id or None,
        mesa_id=mesa.id or 0,
        mozo_id=mozo_id,
        estado=EstadoPedido.BORRADOR.value,
        total=Decimal("0.00"),
    )
    session.add(pedido)
    session.commit()
    session.refresh(pedido)
    return pedido


# ─── ViewModels (Pydantic, serializables a JSON) ─────────────────────────────

class MesaView(BaseModel):
    id: int
    numero: int
    label: str
    nombre: str
    estado: str
    estado_label: str
    badge_bg: str
    badge_text: str
    capacidad: int
    total_abierto: float
    total_abierto_texto: str
    card_bg: str
    card_border: str
    tiene_items_listos: bool
    items_listos_count: int
    items_total_count: int = 0
    tiempo_abierto_texto: str = ""
    sector: str = "Salón"
    mozo_nombre: str = ""
    reserva_texto: str = ""
    inactivo_minutos: int = 0


class SelfOrderPendienteView(BaseModel):
    pedido_id: int = 0
    mesa_label: str = ""
    nombre_cliente: str = ""
    items_resumen: str = ""
    total_texto: str = ""
    hora_texto: str = ""


class PagoStagedView(BaseModel):
    """Pago agregado a la lista del cobro dividido/mixto (aún no persistido)."""

    metodo: str
    metodo_label: str
    monto: float
    monto_texto: str
    items_indices_json: str = ""
    items_texto: str = ""


class CajaItemView(BaseModel):
    detalle_id: int = 0
    producto_nombre: str = ""
    cantidad: int = 0
    precio_unitario_texto: str = ""
    subtotal_texto: str = ""
    subtotal_float: float = 0.0
    notas: str = ""
    seleccionado: bool = False
    asignado_pago: int = 0


class MesaAdminView(BaseModel):
    id: int
    numero: int
    nombre: str
    capacidad: int
    activa: bool
    estado: str
    sector: str = "Salón"
    qr_token: str = ""
    qr_url: str = ""
    qr_base64: str = ""


class InsumoView(BaseModel):
    id: int = 0
    nombre: str = ""
    unidad: str = ""
    stock_actual: float = 0.0
    stock_minimo: float = 0.0
    activo: bool = True
    bajo_stock: bool = False
    stock_texto: str = ""
    stock_minimo_texto: str = ""
    vencimiento_texto: str = ""      # "" si no tiene fecha
    vencimiento_estado: str = ""     # "" | "por_vencer" | "vencido"


class KardexView(BaseModel):
    id: int = 0
    fecha_texto: str = ""
    tipo: str = ""
    tipo_label: str = ""
    cantidad_texto: str = ""
    es_entrada: bool = False
    stock_resultante_texto: str = ""
    motivo: str = ""
    usuario: str = ""


class MozoRankView(BaseModel):
    nombre: str = ""
    pedidos: int = 0
    total: float = 0.0
    total_texto: str = ""
    propinas: float = 0.0
    propinas_texto: str = ""


class FranjaHoraView(BaseModel):
    hora_label: str = ""
    pedidos: int = 0
    total: float = 0.0
    total_texto: str = ""
    barra_pct: int = 0


class MargenPlatoView(BaseModel):
    nombre: str = ""
    precio_texto: str = ""
    costo_texto: str = ""
    margen_texto: str = ""
    margen_pct_texto: str = ""
    color: str = "#16A34A"
    costo_completo: bool = True


class RecetaItemView(BaseModel):
    id: int = 0
    producto_id: int = 0
    insumo_id: int = 0
    insumo_nombre: str = ""
    insumo_unidad: str = ""
    cantidad: float = 0.0
    cantidad_texto: str = ""


class ProduccionPlanItem(BaseModel):
    producto_id: int = 0
    nombre: str = ""
    cantidad: int = 1


class ProduccionNecesidadView(BaseModel):
    insumo_id: int = 0
    nombre: str = ""
    unidad: str = ""
    cantidad_necesaria: float = 0.0
    cantidad_necesaria_texto: str = ""
    stock_actual: float = 0.0
    stock_actual_texto: str = ""
    faltante: float = 0.0
    faltante_texto: str = ""
    costo_estimado: float = 0.0
    costo_estimado_texto: str = ""
    estado: str = "ok"


class ClienteView(BaseModel):
    id: int = 0
    nombre: str = ""
    telefono: str = ""
    email: str = ""
    fecha_nac_iso: str = ""
    fecha_nac_texto: str = ""
    notas: str = ""
    puntos: int = 0
    activo: bool = True
    cumple_hoy: bool = False
    cumple_pronto: bool = False
    dias_para_cumple: int = 999
    visitas_count: int = 0
    gastado_texto: str = "S/ 0.00"
    ultima_visita_texto: str = "Sin visitas"
    es_vip: bool = False


class CuentaView(BaseModel):
    id: int = 0
    cliente_id: int = 0
    cliente_nombre: str = ""
    cliente_telefono: str = ""
    saldo_deuda: float = 0.0
    saldo_texto: str = ""
    limite_credito: float = 0.0


class MovimientoView(BaseModel):
    id: int = 0
    tipo: str = ""
    tipo_label: str = ""
    monto: float = 0.0
    monto_texto: str = ""
    descripcion: str = ""
    fecha_texto: str = ""


class PromocionView(BaseModel):
    id: int = 0
    nombre: str = ""
    tipo: str = ""
    tipo_label: str = ""
    valor: float = 0.0
    descripcion: str = ""
    hora_inicio: str = ""
    hora_fin: str = ""
    activa: bool = True
    aplica_ahora: bool = False
    descuento_texto: str = ""
    horario_texto: str = ""
    dias_texto: str = "Todos los días"
    alcance_texto: str = "Toda la carta"
    auto_aplicar: bool = True


class CuponLoteView(BaseModel):
    id: int = 0
    nombre: str = ""
    codigo: str = ""
    tipo: str = ""
    valor_texto: str = ""
    fecha_inicio_texto: str = ""
    fecha_fin_texto: str = ""
    usos_actuales: int = 0
    usos_max_texto: str = "Ilimitado"
    usos_texto: str = ""
    activo: bool = True
    vencido: bool = False


class UltimoCobroView(BaseModel):
    pedido_id: int = 0
    hora: str = ""
    referencia: str = ""
    detalle: str = ""
    total_texto: str = ""
    metodo_pago: str = ""


class UsuarioSesion(BaseModel):
    id: int
    nombre: str
    rol: str
    company_id: int
    sucursal_id: int = 0
    sucursal_nombre: str = ""
    perm_descuento: bool = True
    perm_anular: bool = False
    perm_reportes: bool = False
    perm_turno: bool = False
    perm_inventario: bool = False
    perm_costos: bool = False
    perm_reimprimir: bool = False
    acceso_mozos: bool = False
    acceso_caja: bool = False
    acceso_cocina: bool = False
    acceso_mostrador: bool = False


class CompanyOptionView(BaseModel):
    id: int
    name: str
    slug: str
    logo_url: str = ""


class SucursalView(BaseModel):
    id: int
    nombre: str
    direccion: str = ""
    telefono: str = ""
    activa: bool = True
    es_principal: bool = False


class CategoriaView(BaseModel):
    id: int
    nombre: str
    descripcion: str
    orden: int
    activa: bool
    productos_count: int = 0
    emoji: str = "🍽️"
    estacion: str = "cocina"


class OpcionModificadorView(BaseModel):
    id: int
    nombre: str
    precio_extra: float
    precio_extra_texto: str

class GrupoModificadorView(BaseModel):
    id: int
    nombre: str
    min_selecciones: int
    max_selecciones: int
    opciones: list[dict[str, object]] = []

class GrupoModificadorAdminView(BaseModel):
    id: int
    nombre: str
    min_selecciones: int
    max_selecciones: int
    activo: bool
    orden: int
    opciones_count: int = 0
    productos_count: int = 0


class ComboItemView(BaseModel):
    producto_id: int
    producto_nombre: str
    cantidad: int

class ComboAdminView(BaseModel):
    id: int
    nombre: str
    descripcion: str = ""
    precio: float
    precio_texto: str
    emoji: str = ""
    activo: bool
    orden: int
    items_count: int = 0
    items_texto: str = ""

class ComboMenuView(BaseModel):
    id: int
    nombre: str
    descripcion: str = ""
    precio: float
    precio_texto: str
    emoji: str = ""
    items_texto: str = ""


class ProductoView(BaseModel):
    id: int
    categoria_id: int
    categoria_nombre: str
    nombre: str
    descripcion: str
    precio: float
    precio_texto: str
    disponible: bool
    imagen_url: str
    emoji: str = "🍽️"
    tiene_modificadores: bool = False
    margen_pct: float = -1.0


class CarritoItem(BaseModel):
    producto_id: int
    nombre: str
    cantidad: int
    precio_unitario: float
    subtotal: float
    subtotal_texto: str
    nota: str = ""
    modificadores_texto: str = ""
    modificadores_json: str = ""
    combo_items_json: str = ""
    es_combo: bool = False


class HistorialItem(BaseModel):
    detalle_id: int
    nombre: str
    cantidad: int
    precio_unitario_texto: str
    subtotal_texto: str
    subtotal_float: float = 0.0
    nota: str
    enviado_en_texto: str
    estado_clave: str
    estado_label: str
    estado_bg: str
    estado_color: str
    preparado_por_nombre: str
    puede_entregar: bool
    puede_cancelar: bool
    sel_precuenta: bool = False


class CocinaTicketView(BaseModel):
    pedido_id: int
    mesa_label: str
    hora_texto: str
    estado_produccion: str
    estado_label: str
    estado_bg: str
    estado_color: str
    mozo_nombre: str
    action_label: str
    accent_bg: str
    accent_border: str
    detalle_ids_csv: str
    items_lines: list[str] = []
    items_ids: list[str] = []
    items_producto_ids: list[str] = []
    bumpable: bool = False
    minutos_texto: str = ""
    demorado: bool = False


class VentaHistorialView(BaseModel):
    pedido_id: int
    mesa_label: str
    total: float
    total_texto: str
    propina: float
    propina_texto: str
    total_con_propina: float
    total_con_propina_texto: str
    metodo_pago: str
    mozo_nombre: str
    cajero_nombre: str
    anulada: bool = False
    anulacion_texto: str = ""


class VentaDetalleItemView(BaseModel):
    nombre: str
    cantidad: int
    precio_unitario_texto: str
    subtotal_texto: str
    notas: str = ""


class TopPlatoView(BaseModel):
    nombre: str
    cantidad: int
    total_generado: float
    total_texto: str


class PylLineView(BaseModel):
    concepto: str
    valor_texto: str
    es_total: bool = False
    es_negativo: bool = False
    margen_pct_texto: str = ""


class DescuentoRankView(BaseModel):
    cajero: str
    pedidos: int
    total_descuento_texto: str
    total_ventas_texto: str
    pct_descuento_texto: str


class AnulacionView(BaseModel):
    pedido_id: int
    total_texto: str
    motivo: str
    cancelado_por: str
    cancelado_en_texto: str
    cajero_original: str


class ReversionView(BaseModel):
    pedido_id: int
    total_texto: str
    motivo: str
    revertido_por: str
    revertido_en_texto: str


class MermaCategoriaView(BaseModel):
    categoria: str
    registros: int
    valor_texto: str


class MermaInsumoView(BaseModel):
    nombre: str
    unidad: str
    cantidad_texto: str
    valor_texto: str
    registros: int


class MatrizProductoView(BaseModel):
    nombre: str
    unidades: int
    ingreso_texto: str
    margen_pct_texto: str
    categoria: str
    categoria_emoji: str


class MostradorEntregaView(BaseModel):
    pedido_id: int
    cliente_nombre: str
    hora_texto: str
    items_lines: list[str]
    items_count: int


class MostradorEntregadoView(BaseModel):
    pedido_id: int
    cliente_nombre: str
    hora_texto: str
    items_resumen: str
    total_texto: str


class MostradorPendienteView(BaseModel):
    """Orden de mostrador pendiente de cobro — usada en panel derecho de Mostrador y sidebar de Caja."""
    pedido_id: int = 0
    cliente_nombre: str = ""
    hora_texto: str = ""
    items_resumen: str = ""
    total_texto: str = ""
    total: float = 0.0
    en_cocina: bool = False


class UsuarioAdminView(BaseModel):
    id: int
    nombre: str
    rol: str
    rol_label: str
    pin_masked: str
    activo: bool
    badge_bg: str
    badge_text: str
    es_yo: bool
    perm_descuento: bool = True
    perm_anular: bool = False
    perm_reportes: bool = False
    perm_turno: bool = False
    perm_inventario: bool = False
    perm_costos: bool = False
    perm_reimprimir: bool = False
    acceso_mozos: bool = False
    acceso_caja: bool = False
    acceso_cocina: bool = False
    acceso_mostrador: bool = False


# ─── Helpers de inventario ───────────────────────────────────────────────────

def _validar_stock_para_items(session, items: list[tuple[int, int]], company_id: int) -> list[str]:
    """Devuelve mensajes de error si el stock es insuficiente. Lista vacía = OK.
    items: lista de (producto_id, cantidad)."""
    if not items:
        return []
    producto_ids = list({pid for pid, _ in items})
    recetas = session.exec(
        select(RecetaItem).where(
            RecetaItem.company_id == company_id,
            RecetaItem.producto_id.in_(producto_ids),
        )
    ).all()
    if not recetas:
        return []
    receta_por_producto: dict[int, list] = {}
    for r in recetas:
        receta_por_producto.setdefault(r.producto_id, []).append(r)
    uso_total: dict[int, Decimal] = {}
    for pid, cantidad in items:
        for ri in receta_por_producto.get(pid, []):
            uso = Decimal(str(ri.cantidad)) * cantidad
            uso_total[ri.insumo_id] = uso_total.get(ri.insumo_id, Decimal("0")) + uso
    if not uso_total:
        return []
    insumos = {
        i.id: i
        for i in session.exec(
            select(Insumo).where(
                Insumo.company_id == company_id,
                Insumo.id.in_(list(uso_total.keys())),
            )
        ).all()
    }
    errores: list[str] = []
    for insumo_id, uso in uso_total.items():
        ins = insumos.get(insumo_id)
        if ins is None:
            continue
        stock = Decimal(str(ins.stock_actual))
        if stock < uso:
            errores.append(f"{ins.nombre}: necesario {uso:.2f}, disponible {stock:.2f} {ins.unidad}")
    return errores


def _descontar_stock_por_pedido(session, pedido_id: int, company_id: int) -> None:
    """Descuenta stock de insumos según las recetas de los ítems del pedido."""
    detalles = session.exec(
        select(DetallePedido).where(DetallePedido.pedido_id == pedido_id)
    ).all()
    if not detalles:
        return
    producto_ids_set: set[int] = set()
    for d in detalles:
        producto_ids_set.add(d.producto_id)
        if d.combo_items_json:
            import json as _json
            try:
                for ci in _json.loads(d.combo_items_json):
                    producto_ids_set.add(ci.get("producto_id", 0))
            except Exception:
                pass
    producto_ids = list(producto_ids_set)
    recetas = session.exec(
        select(RecetaItem).where(
            RecetaItem.company_id == company_id,
            RecetaItem.producto_id.in_(producto_ids),
        )
    ).all()
    if not recetas:
        return
    receta_por_producto: dict[int, list] = {}
    for r in recetas:
        receta_por_producto.setdefault(r.producto_id, []).append(r)
    insumo_ids = list({r.insumo_id for r in recetas})
    insumos = {
        i.id: i
        for i in session.exec(
            select(Insumo).where(
                Insumo.company_id == company_id,
                Insumo.id.in_(insumo_ids),
            )
        ).all()
    }
    descuentos: dict[int, Decimal] = {}
    for d in detalles:
        if d.combo_items_json:
            import json as _json
            try:
                combo_items = _json.loads(d.combo_items_json)
            except Exception:
                combo_items = []
            for ci in combo_items:
                ci_pid = ci.get("producto_id", 0)
                ci_cant = ci.get("cantidad", 1)
                for ri in receta_por_producto.get(ci_pid, []):
                    uso = Decimal(str(ri.cantidad)) * ci_cant * d.cantidad
                    descuentos[ri.insumo_id] = descuentos.get(ri.insumo_id, Decimal("0")) + uso
        else:
            for ri in receta_por_producto.get(d.producto_id, []):
                uso = Decimal(str(ri.cantidad)) * d.cantidad
                descuentos[ri.insumo_id] = descuentos.get(ri.insumo_id, Decimal("0")) + uso
    for insumo_id, uso_total in descuentos.items():
        ins = insumos.get(insumo_id)
        if ins:
            stock_actual = Decimal(str(ins.stock_actual))
            if stock_actual < uso_total:
                uso_total = max(stock_actual, Decimal("0"))
                if uso_total <= 0:
                    continue
            registrar_consumo(session, ins, uso_total, pedido_id)


# ─── Imports de mixins (después de ViewModels/helpers para evitar circular) ───
from app.states.carta_mixin import CartaMixin
from app.states.clientes_cuentas_mixin import ClientesCuentasMixin
from app.states.inventario_mixin import InventarioMixin
from app.states.produccion_mixin import ProduccionMixin
from app.states.promos_cupones_mixin import PromosCuponesMixin
from app.states.reportes_state import ReportesState  # noqa: F401


# ─── Estado principal ─────────────────────────────────────────────────────────

class FoodState(
    CajaTurnoMixin,
    CartaMixin,
    InventarioMixin,
    ProduccionMixin,
    ClientesCuentasMixin,
    PromosCuponesMixin,
    rx.State,
):
    """Estado global de la app TUWAYKIFOOD."""

    mesas: list[MesaView] = []
    categorias: list[CategoriaView] = []
    productos: list[ProductoView] = []
    carrito: list[CarritoItem] = []
    mostrador_carrito: list[CarritoItem] = []
    historial_pedido: list[HistorialItem] = []
    tickets_cocina: list[CocinaTicketView] = []
    pedidos_mostrador_pendientes: list[MostradorPendienteView] = []
    pedidos_mostrador_entregados: list[MostradorEntregadoView] = []

    mesa_seleccionada_id: int = 0
    mesa_cliente_busqueda: str = ""
    mesa_cliente_id: int = 0
    mesa_cliente_nombre: str = ""
    transfer_modal_abierto: bool = False
    precuenta_parcial_modo: bool = False
    mozos_filtro_sector: str = ""
    mesa_atendida_por_nombre: str = ""
    categoria_activa_id: int = 0
    mostrador_categoria_activa_id: int = 0
    mostrador_cliente_nombre: str = ""
    busqueda_producto_mostrador: str = ""
    mostrador_metodo_pago: str = "efectivo"
    ultimo_pedido_id: int = 0
    mensaje: str = ""
    login_error: str = ""
    usuario_actual: UsuarioSesion | None = None
    ultima_actividad: str = ""
    empresa_plan: str = "trial"
    session_token: str = rx.Cookie("", name="twk_session", max_age=28800)
    login_pin_input: str = ""
    login_rol_seleccionado: str = RolUsuario.MOZO.value
    sidebar_collapsed: bool = False

    login_step: str = "restaurant"
    companies_activas: list[CompanyOptionView] = []
    login_selected_company_id: int = 0
    login_selected_company_slug: str = ""

    sucursales_empresa: list[SucursalView] = []
    sucursal_admin_form_id: int = 0
    sucursal_admin_form_nombre: str = ""
    sucursal_admin_form_direccion: str = ""
    sucursal_admin_form_telefono: str = ""
    sucursal_admin_form_activa: bool = True
    sucursal_admin_form_es_principal: bool = False
    sucursal_admin_form_visible: bool = False

    # ── Self-order (aprobación) ──────────────────────────────────────────────
    self_orders_pendientes: list[SelfOrderPendienteView] = []

    @rx.var
    def login_selected_company_name(self) -> str:
        c = next((c for c in self.companies_activas if c.id == self.login_selected_company_id), None)
        return c.name if c else ""

    @rx.var
    def login_selected_company_logo(self) -> str:
        c = next((c for c in self.companies_activas if c.id == self.login_selected_company_id), None)
        return c.logo_url if c else ""

    def _company_id(self) -> int:
        """company_id del tenant activo — de la sesión logueada, o del restaurante
        elegido en el paso previo al login. Arma el contexto de aislamiento tenant."""
        company_id = (
            self.usuario_actual.company_id
            if self.usuario_actual is not None
            else self.login_selected_company_id
        )
        set_tenant_context(company_id, None)
        return company_id

    @contextmanager
    def _tenant_session(self):
        """Como get_session(), pero arma el contexto tenant y evita que el listener
        de tuwayki_core dispare un RuntimeError — el filtro real sigue siendo
        explícito en cada query vía self._company_id()."""
        self._company_id()
        with get_session() as session:
            session.info["tenant_bypass"] = True
            yield session

    def _sucursal_id(self) -> int:
        """sucursal_id de la sesión activa. 0 = sin sucursal (single-location)."""
        if self.usuario_actual is not None:
            return self.usuario_actual.sucursal_id
        return 0

    def _sucursal_filter(self, model_class, query):
        """Aplica filtro de sucursal a un query si hay sucursal activa.
        Si sucursal_id == 0, no filtra (retrocompat single-location)."""
        sid = self._sucursal_id()
        if sid:
            return query.where(model_class.sucursal_id == sid)
        return query

    @rx.var
    def tiene_sucursales(self) -> bool:
        return len(self.sucursales_empresa) > 1

    @rx.var
    def sucursal_actual_nombre(self) -> str:
        if self.usuario_actual and self.usuario_actual.sucursal_nombre:
            return self.usuario_actual.sucursal_nombre
        return ""

    pagina_cargada: bool = False
    ultima_actualizacion: str = ""
    mozos_polling_enabled: bool = False
    cocina_polling_enabled: bool = False
    cocina_fullscreen: bool = False
    caja_polling_enabled: bool = False
    mostrador_polling_enabled: bool = False
    cocina_auto_print_max_id: int = 0
    cocina_filtro_estacion: str = ""

    sonidos_activos: bool = True
    _prev_tickets_pendientes: int = -1
    _prev_mesas_alerta_entrega: int = -1

    mozos_tab_activa: str = "salon"
    modal_agregar_abierto: bool = False
    busqueda_producto_modal: str = ""
    nota_producto_activo_id: int = 0
    nota_input_temporal: str = ""

    # Caja — cliente vinculado al cobro (fiado / facturación)
    caja_cobro_cliente_nombre: str = ""
    caja_cobro_cliente_id: int = 0

    # Guards contra doble-click en operaciones críticas
    caja_cobrando: bool = False
    turno_cerrando: bool = False
    mostrador_enviando: bool = False
    caja_registrando_mov: bool = False

    # Caja — flujo de cobro con método de pago
    caja_cobro_mesa_id: int = 0
    caja_cobro_metodo: str = "efectivo"
    caja_cobro_propina: str = ""
    caja_cobro_propina_pct: int = 0
    caja_cobro_descuento: str = ""
    caja_cobro_descuento_es_pct: bool = False
    caja_cobro_recargo: str = ""
    caja_cobro_recargo_concepto: str = "delivery"
    caja_cobro_efectivo_recibido: str = ""
    caja_cobro_error: str = ""
    caja_cobro_items: list[CajaItemView] = []
    # Cobro de pedidos para llevar desde Mostrador
    caja_cobro_pedido_id: int = 0
    caja_cobro_pedido_label: str = ""
    caja_cobro_total_override: float = 0.0

    # Caja — cobro dividido / pago mixto
    caja_cobro_dividido: bool = False
    caja_split_por_items: bool = False
    caja_pago_staged_metodo: str = "efectivo"
    caja_pago_staged_monto: str = ""
    caja_pagos_staged: list[PagoStagedView] = []

    # Últimos cobros — modal de reimpresión
    ultimos_cobros_visible: bool = False
    ultimos_cobros: list[UltimoCobroView] = []

    # Anulación auditada de pedidos/ventas
    anulacion_modal_visible: bool = False
    anulacion_pedido_id: int = 0
    anulacion_es_venta: bool = False
    anulacion_referencia: str = ""
    anulacion_motivo: str = ""
    anulacion_error: str = ""

    # Reversión de cobro — con motivo obligatorio
    reversion_modal_visible: bool = False
    reversion_pedido_id: int = 0
    reversion_referencia: str = ""
    reversion_motivo: str = ""
    reversion_error: str = ""

    # Nota global del pedido de mesa activo
    nota_pedido_mesa: str = ""

    # Configuración impresoras + carta digital
    config_nombre_local: str = "Mi Restaurante"
    config_logo_url: str = ""
    config_ticket_paper_width_mm: str = "80"
    config_slug: str = "mi-restaurante"
    config_menu_qr_base64: str = ""
    config_menu_url: str = ""
    # Datos fiscales del ticket
    config_ruc: str = ""
    config_sucursal: str = ""
    config_direccion: str = ""
    config_telefono: str = ""
    config_mensaje_ticket: str = "¡Gracias por su preferencia!"
    config_mostrar_iva: bool = False
    config_nombre_impuesto: str = "IGV"
    config_porcentaje_iva: str = "18.0"
    config_kds_minutos_alerta: str = "15"
    config_admin_email: str = ""
    config_admin_password_nueva: str = ""
    config_admin_password_confirm: str = ""
    config_admin_show_password: bool = False

    # CRUD mesas (admin)
    mesas_config: list[MesaAdminView] = []
    mesa_config_form_id: int = 0
    mesa_config_form_numero: str = ""
    mesa_config_form_nombre: str = ""
    mesa_config_form_capacidad: str = "4"
    mesa_config_form_sector: str = "Salón"

    # ─── Computed vars ────────────────────────────────────────────────────────


    @rx.var
    def autenticado(self) -> bool:
        return self.usuario_actual is not None

    @rx.var
    def usuario_nombre(self) -> str:
        return self.usuario_actual.nombre if self.usuario_actual else ""

    @rx.var
    def usuario_rol(self) -> str:
        return self.usuario_actual.rol if self.usuario_actual else ""

    @rx.var
    def usuario_home_route(self) -> str:
        if self.usuario_actual is None:
            return "/login"
        return _role_home_route(self.usuario_actual.rol)

    @rx.var
    def puede_ver_mozos(self) -> bool:
        if self.usuario_actual is None:
            return False
        return self.usuario_actual.rol in ROLE_ALLOWED_ROUTES["mozos"] or self.usuario_actual.acceso_mozos

    @rx.var
    def puede_ver_caja(self) -> bool:
        if self.usuario_actual is None:
            return False
        return self.usuario_actual.rol in ROLE_ALLOWED_ROUTES["caja"] or self.usuario_actual.acceso_caja

    @rx.var
    def puede_ver_mostrador(self) -> bool:
        if self.usuario_actual is None:
            return False
        return self.usuario_actual.rol in ROLE_ALLOWED_ROUTES["mostrador"] or self.usuario_actual.acceso_mostrador

    @rx.var
    def puede_ver_cocina(self) -> bool:
        if self.usuario_actual is None:
            return False
        return self.usuario_actual.rol in ROLE_ALLOWED_ROUTES["cocina"] or self.usuario_actual.acceso_cocina

    @rx.var
    def puede_ver_carta(self) -> bool:
        if self.usuario_actual is None:
            return False
        return self.usuario_actual.rol in ROLE_ALLOWED_ROUTES["carta"]

    @rx.var
    def puede_ver_reportes(self) -> bool:
        if self.usuario_actual is None:
            return False
        return self.usuario_actual.rol in ROLE_ALLOWED_ROUTES["reportes"]

    @rx.var
    def puede_ver_configuracion(self) -> bool:
        if self.usuario_actual is None:
            return False
        return self.usuario_actual.rol in ROLE_ALLOWED_ROUTES["configuracion"]

    @rx.var
    def puede_ver_panel_admin(self) -> bool:
        if self.usuario_actual is None:
            return False
        return self.usuario_actual.rol == RolUsuario.ADMIN.value

    @rx.var
    def es_pagina_standalone(self) -> bool:
        """True si esta página (Cuentas/Promociones/Clientes/Inventario) se
        accede como ruta independiente — False si está embebida como pestaña
        dentro de /admin, donde el link "Panel Administrativo" es redundante."""
        return self.router.page.path != "/admin"


    @rx.var
    def puede_ver_usuarios(self) -> bool:
        if self.usuario_actual is None:
            return False
        return self.usuario_actual.rol in ROLE_ALLOWED_ROUTES["usuarios"]

    @rx.var
    def tiene_perm_turno(self) -> bool:
        if self.usuario_actual is None:
            return False
        return self.usuario_actual.rol == RolUsuario.ADMIN.value or self.usuario_actual.perm_turno

    @rx.var
    def tiene_perm_inventario(self) -> bool:
        if self.usuario_actual is None:
            return False
        return self.usuario_actual.rol == RolUsuario.ADMIN.value or self.usuario_actual.perm_inventario

    @rx.var
    def tiene_perm_costos(self) -> bool:
        if self.usuario_actual is None:
            return False
        return self.usuario_actual.rol == RolUsuario.ADMIN.value or self.usuario_actual.perm_costos

    @rx.var
    def tiene_perm_reimprimir(self) -> bool:
        if self.usuario_actual is None:
            return False
        return self.usuario_actual.rol == RolUsuario.ADMIN.value or self.usuario_actual.perm_reimprimir

    def _touch_actividad(self) -> None:
        self.ultima_actividad = _utcnow().isoformat()

    def _check_session_expiry(self) -> bool:
        """Returns True if session expired and user was logged out."""
        if self.usuario_actual is None:
            return False
        if _session_expired(self.ultima_actividad, self.usuario_actual.rol):
            self.usuario_actual = None
            self.session_token = ""
            self.ultima_actividad = ""
            self._clear_operational_context()
            self.mensaje = "Sesión expirada por inactividad. Ingrese nuevamente."
            return True
        return False

    @rx.var
    def mesa_seleccionada_label(self) -> str:
        mesa = next((m for m in self.mesas if m.id == self.mesa_seleccionada_id), None)
        return mesa.nombre if mesa else "Sin mesa"

    @rx.var
    def mesa_seleccionada_total_texto(self) -> str:
        mesa = next((m for m in self.mesas if m.id == self.mesa_seleccionada_id), None)
        return mesa.total_abierto_texto if mesa else _money_text(0)

    @rx.var
    def hay_items_para_entregar(self) -> bool:
        return any(item.puede_entregar for item in self.historial_pedido)

    @rx.var
    def cantidad_items_carrito(self) -> int:
        return sum(item.cantidad for item in self.carrito)

    @rx.var
    def total_carrito_texto(self) -> str:
        total = sum(_to_decimal(item.subtotal) for item in self.carrito)
        return _money_text(total)

    @rx.var
    def hay_historial_pedido(self) -> bool:
        return len(self.historial_pedido) > 0

    @rx.var
    def cantidad_mesas_abiertas(self) -> int:
        return sum(1 for m in self.mesas if m.estado != EstadoMesa.LIBRE.value)

    @rx.var
    def mesas_destino_transfer(self) -> list[MesaView]:
        return [m for m in self.mesas if m.id != self.mesa_seleccionada_id]

    @rx.var
    def mesa_seleccionada_ocupada(self) -> bool:
        mesa = next((m for m in self.mesas if m.id == self.mesa_seleccionada_id), None)
        return mesa is not None and mesa.estado != EstadoMesa.LIBRE.value

    @rx.var
    def mesas_por_cobrar(self) -> list[MesaView]:
        return [m for m in self.mesas if m.estado != EstadoMesa.LIBRE.value and m.total_abierto > 0]

    @rx.var
    def tickets_nuevos(self) -> list[CocinaTicketView]:
        return [t for t in self.tickets_cocina if t.estado_produccion == EstadoProduccion.PENDIENTE.value]

    @rx.var
    def tickets_en_preparacion(self) -> list[CocinaTicketView]:
        return [t for t in self.tickets_cocina if t.estado_produccion == EstadoProduccion.EN_PREPARACION.value]

    @rx.var
    def cantidad_tickets_nuevos(self) -> int:
        return len(self.tickets_nuevos)

    @rx.var
    def cantidad_tickets_en_preparacion(self) -> int:
        return len(self.tickets_en_preparacion)

    @rx.var
    def tickets_listos(self) -> list[CocinaTicketView]:
        return [t for t in self.tickets_cocina if t.estado_produccion == EstadoProduccion.LISTO_PARA_ENTREGAR.value]

    @rx.var
    def cantidad_tickets_listos(self) -> int:
        return len(self.tickets_listos)

    @rx.var
    def mesas_con_alerta_entrega(self) -> int:
        return sum(1 for m in self.mesas if m.tiene_items_listos)

    @rx.var
    def sectores_unicos(self) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for m in self.mesas:
            if m.sector not in seen:
                seen.add(m.sector)
                result.append(m.sector)
        return result

    @rx.var
    def mesas_filtradas_por_sector(self) -> list[MesaView]:
        if not self.mozos_filtro_sector:
            return self.mesas
        return [m for m in self.mesas if m.sector == self.mozos_filtro_sector]

    @rx.var
    def sectores_config(self) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for m in self.mesas_config:
            if m.sector not in seen:
                seen.add(m.sector)
                result.append(m.sector)
        return result


    @rx.var
    def caja_cobro_es_fiado(self) -> bool:
        return self.caja_cobro_metodo == "fiado"


    @rx.var
    def productos_filtrados(self) -> list[ProductoView]:
        if self.categoria_activa_id == 0:
            return [p for p in self.productos if p.disponible]
        return [p for p in self.productos if p.disponible and p.categoria_id == self.categoria_activa_id]

    @rx.var
    def productos_modal_filtrados(self) -> list[ProductoView]:
        resultado = list(self.productos)
        if self.categoria_activa_id != 0:
            resultado = [p for p in resultado if p.categoria_id == self.categoria_activa_id]
        q = self.busqueda_producto_modal.strip().lower()
        if q:
            resultado = [p for p in resultado if q in p.nombre.lower()]
        return sorted(resultado, key=lambda p: (not p.disponible, p.nombre))


    @rx.var
    def mostrador_productos_filtrados(self) -> list[ProductoView]:
        disponibles = [p for p in self.productos if p.disponible]
        if self.mostrador_categoria_activa_id != 0:
            disponibles = [p for p in disponibles if p.categoria_id == self.mostrador_categoria_activa_id]
        q = self.busqueda_producto_mostrador.strip().lower()
        if q:
            disponibles = [p for p in disponibles if q in p.nombre.lower()]
        return disponibles

    @rx.var
    def total_mostrador_texto(self) -> str:
        total = sum(_to_decimal(item.subtotal) for item in self.mostrador_carrito)
        return _money_text(total)

    @rx.var
    def total_mostrador_neto_texto(self) -> str:
        """Total del carrito de mostrador menos cupón aplicado."""
        total = sum(_to_decimal(item.subtotal) for item in self.mostrador_carrito)
        if self.mostrador_cupon_descuento_aplicado:
            try:
                dcto = Decimal(self.mostrador_cupon_descuento_aplicado)
                total = max(total - dcto, Decimal("0.00"))
            except (ValueError, Exception):
                pass
        return _money_text(total)

    @rx.var
    def caja_cobro_activo(self) -> bool:
        return self.caja_cobro_mesa_id > 0 or self.caja_cobro_pedido_id > 0

    @rx.var
    def caja_cobro_mesa_nombre(self) -> str:
        if self.caja_cobro_pedido_id > 0:
            return self.caja_cobro_pedido_label
        mesa = next((m for m in self.mesas if m.id == self.caja_cobro_mesa_id), None)
        return mesa.nombre if mesa else ""

    @rx.var
    def caja_cobro_total_base(self) -> float:
        if self.caja_cobro_pedido_id > 0:
            return self.caja_cobro_total_override
        mesa = next((m for m in self.mesas if m.id == self.caja_cobro_mesa_id), None)
        return mesa.total_abierto if mesa else 0.0

    @rx.var
    def caja_cobro_total_base_texto(self) -> str:
        return _money_text(self.caja_cobro_total_base)

    @rx.var
    def caja_cobro_propina_decimal(self) -> float:
        try:
            v = float(self.caja_cobro_propina.replace(",", ".").strip())
            return round(v, 2) if v >= 0 else 0.0
        except (ValueError, AttributeError):
            return 0.0

    @rx.var
    def caja_cobro_descuento_decimal(self) -> float:
        try:
            v = float(self.caja_cobro_descuento.replace(",", ".").strip())
            v = max(v, 0.0)
            if self.caja_cobro_descuento_es_pct:
                v = min(v, 100.0)
                v = self.caja_cobro_total_base * v / 100
            return round(v, 2)
        except (ValueError, AttributeError):
            return 0.0

    @rx.var
    def caja_cobro_recargo_decimal(self) -> float:
        try:
            v = float(self.caja_cobro_recargo.replace(",", ".").strip())
            return round(max(v, 0.0), 2)
        except (ValueError, AttributeError):
            return 0.0

    @rx.var
    def caja_cobro_total_final(self) -> float:
        total = self.caja_cobro_total_base - self.caja_cobro_descuento_decimal + self.caja_cobro_propina_decimal + self.caja_cobro_recargo_decimal
        return round(max(total, 0.0), 2)

    @rx.var
    def caja_cobro_total_final_texto(self) -> str:
        return _money_text(self.caja_cobro_total_final)

    @rx.var
    def caja_cobro_vuelto(self) -> float:
        try:
            recibido = float(self.caja_cobro_efectivo_recibido.replace(",", ".").strip())
            vuelto = round(recibido - self.caja_cobro_total_final, 2)
            return vuelto if vuelto >= 0 else 0.0
        except (ValueError, AttributeError):
            return 0.0

    @rx.var
    def caja_cobro_vuelto_texto(self) -> str:
        return _money_text(self.caja_cobro_vuelto)

    @rx.var
    def caja_cobro_es_efectivo(self) -> bool:
        return self.caja_cobro_metodo == "efectivo"

    # ─── Inicialización ───────────────────────────────────────────────────────

    def cargar_datos_iniciales(self) -> None:
        self.cargar_mesas()
        self.cargar_menu()
        self.cargar_cocina()
        self.cargar_grupos_modificadores()
        self.cargar_combos()
        self._bootstrap_forms()
        if self.mesa_seleccionada_id:
            self._cargar_carrito_mesa(self.mesa_seleccionada_id)
            self._cargar_historial_mesa(self.mesa_seleccionada_id)

    def _bootstrap_forms(self) -> None:
        if not self.producto_form_categoria_nombre and self.categorias:
            self.producto_form_categoria_nombre = self.categorias[0].nombre
        if self.categoria_form_orden == "1" and self.categorias:
            self.categoria_form_orden = str(len(self.categorias) + 1)

    def refrescar(self) -> None:
        self.cargar_datos_iniciales()
        self.cargar_pedidos_mostrador_pendientes()
        self.cargar_pedidos_mostrador_entregados()
        return rx.toast.success("Datos actualizados.")

    def _clear_operational_context(self) -> None:
        self.mesas = []
        self.categorias = []
        self.productos = []
        self.carrito = []
        self.mostrador_carrito = []
        self.historial_pedido = []
        self.tickets_cocina = []
        self.pedidos_mostrador_pendientes = []
        self.pedidos_mostrador_entregados = []
        self.mesa_seleccionada_id = 0
        self.mesa_atendida_por_nombre = ""
        self.categoria_activa_id = 0
        self.mostrador_categoria_activa_id = 0
        self.mostrador_cliente_nombre = ""
        self.busqueda_producto_mostrador = ""
        self.mostrador_metodo_pago = "efectivo"
        self.ultimo_pedido_id = 0
        self.login_pin_input = ""
        self.sidebar_collapsed = False
        self.mozos_polling_enabled = False
        self.cocina_polling_enabled = False
        self.caja_polling_enabled = False
        self.mostrador_polling_enabled = False
        self.caja_cobro_mesa_id = 0
        self.caja_cobro_metodo = "efectivo"
        self.caja_cobro_propina = ""
        self.caja_cobro_propina_pct = 0
        self.caja_cobro_recargo = ""
        self.caja_cobro_recargo_concepto = "delivery"
        self.caja_cobro_efectivo_recibido = ""
        self.ultimos_cobros_visible = False
        self.ultimos_cobros = []
        self.nota_pedido_mesa = ""

    # ─── Navegación / Shell ───────────────────────────────────────────────────

    def toggle_sidebar(self) -> None:
        self.sidebar_collapsed = not self.sidebar_collapsed

    def _set_session_cookie(
        self, usuario: UsuarioFood, company_id: int,
        sucursal_id: int, sucursal_nombre: str,
    ) -> None:
        self.session_token = _sign_session({
            "uid": usuario.id or 0,
            "cid": company_id,
            "sid": sucursal_id,
            "sname": sucursal_nombre,
            "slug": self.login_selected_company_slug,
        })

    def _set_session_cookie_from_current(self) -> None:
        if self.usuario_actual is None:
            return
        u = self.usuario_actual
        self.session_token = _sign_session({
            "uid": u.id,
            "cid": u.company_id,
            "sid": u.sucursal_id,
            "sname": u.sucursal_nombre,
            "slug": self.login_selected_company_slug,
        })

    def _try_restore_session(self) -> bool:
        """Restaura sesión desde cookie firmada (para pestañas nuevas)."""
        token = self.session_token
        if not token:
            return False
        payload = _verify_session(token)
        if payload is None:
            self.session_token = ""
            return False
        uid = payload.get("uid", 0)
        cid = payload.get("cid", 0)
        if not uid or not cid:
            self.session_token = ""
            return False
        with tenant_bypass():
            with get_session() as session:
                usuario = session.exec(
                    select(UsuarioFood).where(
                        UsuarioFood.id == uid,
                        UsuarioFood.company_id == cid,
                        UsuarioFood.activo.is_(True),
                    )
                ).first()
        if usuario is None:
            self.session_token = ""
            return False
        sid = payload.get("sid", 0)
        sname = payload.get("sname", "")
        self.usuario_actual = UsuarioSesion(
            id=usuario.id or 0,
            nombre=usuario.nombre,
            rol=usuario.rol,
            company_id=usuario.company_id,
            sucursal_id=sid,
            sucursal_nombre=sname,
            perm_descuento=usuario.perm_descuento,
            perm_anular=usuario.perm_anular,
            perm_reportes=usuario.perm_reportes,
            perm_turno=usuario.perm_turno,
            perm_inventario=usuario.perm_inventario,
            perm_costos=usuario.perm_costos,
            perm_reimprimir=usuario.perm_reimprimir,
            acceso_mozos=usuario.acceso_mozos,
            acceso_caja=usuario.acceso_caja,
            acceso_cocina=usuario.acceso_cocina,
            acceso_mostrador=usuario.acceso_mostrador,
        )
        self.ultima_actividad = _utcnow().isoformat()
        self.login_selected_company_id = cid
        self.login_selected_company_slug = payload.get("slug", "")
        self.cargar_config_impresora()
        self._cargar_plan_empresa()
        return True

    def _route_access_result(self, route_key: str, also_allowed: bool = False):
        if self.usuario_actual is None:
            if not self._try_restore_session():
                return rx.redirect("/login", replace=True)
        if _session_expired(self.ultima_actividad, self.usuario_actual.rol):
            self.usuario_actual = None
            self.session_token = ""
            self.ultima_actividad = ""
            self._clear_operational_context()
            self.login_error = "Sesión expirada por inactividad."
            return rx.redirect("/login", replace=True)
        _acceso_extra = getattr(self.usuario_actual, f"acceso_{route_key}", False)
        if self.usuario_actual.rol not in ROLE_ALLOWED_ROUTES[route_key] and not also_allowed and not _acceso_extra:
            return [
                rx.window_alert("No tienes permiso para este módulo."),
                rx.redirect(self.usuario_home_route, replace=True),
            ]
        bloqueo = _bloqueo_suscripcion(self._company_id())
        if bloqueo:
            self.usuario_actual = None
            self.session_token = ""
            self._clear_operational_context()
            self.login_error = bloqueo
            return [
                rx.window_alert(bloqueo),
                rx.redirect("/login", replace=True),
            ]
        feat_requerido = PAGINAS_PREMIUM.get(route_key)
        if feat_requerido and not plan_permite(self.empresa_plan, feat_requerido):
            return [
                rx.toast.error(MSG_UPGRADE, duration=5000),
                rx.redirect(self.usuario_home_route, replace=True),
            ]
        self._touch_actividad()
        self.cargar_datos_iniciales()
        return None

    def on_load_root(self):
        if self.usuario_actual is not None:
            return rx.redirect(self.usuario_home_route, replace=True)
        if self._try_restore_session():
            return rx.redirect(self.usuario_home_route, replace=True)
        return rx.redirect("/login", replace=True)

    def on_load_login(self):
        if self.usuario_actual is not None:
            return rx.redirect(self.usuario_home_route, replace=True)
        if self._try_restore_session():
            return rx.redirect(self.usuario_home_route, replace=True)
        self.login_pin_input = ""
        self.login_error = ""
        with tenant_bypass():
            with get_session() as session:
                empresas = session.exec(
                    select(Company)
                    .where(Company.is_active.is_(True))
                    .order_by(Company.name)
                ).all()
        self.companies_activas = [
            CompanyOptionView(id=c.id or 0, name=c.name, slug=c.slug,
                               logo_url=c.logo_url or "")
            for c in empresas
        ]
        # Si venimos de "Ingresar como Administrador" con el link "¿Sos
        # empleado?", el slug en la URL nos devuelve directo al paso del PIN
        # de esa misma empresa en vez de hacer elegir de nuevo.
        slug = self.router.page.params.get("empresa", "")
        empresa = next((c for c in self.companies_activas if c.slug == slug), None) if slug else None
        if empresa is not None:
            self.login_selected_company_id = empresa.id
            self.login_selected_company_slug = empresa.slug
            self.login_step = "pin"
        else:
            self.login_step = "restaurant"
            self.login_selected_company_id = 0
            self.login_selected_company_slug = ""
        return None

    def seleccionar_restaurante(self, company_id: int) -> None:
        empresa = next((c for c in self.companies_activas if c.id == company_id), None)
        if empresa is None:
            return
        self.login_selected_company_id = empresa.id
        self.login_selected_company_slug = empresa.slug
        self.login_step = "pin"
        self.login_error = ""

    def volver_a_seleccion_restaurante(self) -> None:
        self.login_step = "restaurant"
        self.login_pin_input = ""
        self.login_error = ""

    def on_load_mozos(self):
        self.pagina_cargada = False
        self.stop_caja_polling()
        self.stop_cocina_polling()
        self.stop_mostrador_polling()
        result = self._route_access_result("mozos")
        self.pagina_cargada = True
        return result

    def on_load_caja(self):
        self.pagina_cargada = False
        self.stop_mozos_polling()
        self.stop_cocina_polling()
        self.stop_mostrador_polling()
        self._init_cocina_auto_print()
        result = self._route_access_result("caja")
        if result is not None:
            self.pagina_cargada = True
            return result
        self.cargar_turno_caja()
        self.cargar_pedidos_mostrador_pendientes()
        self.pagina_cargada = True
        return None

    def on_load_mostrador(self):
        self.pagina_cargada = False
        self.stop_mozos_polling()
        self.stop_caja_polling()
        self.stop_cocina_polling()
        result = self._route_access_result("mostrador")
        if result is not None:
            self.pagina_cargada = True
            return result
        self.cargar_turno_caja()
        self.cargar_pedidos_mostrador_pendientes()
        self.cargar_pedidos_mostrador_entregados()
        self.pagina_cargada = True
        return None

    def on_load_cocina(self):
        self.pagina_cargada = False
        self.stop_mozos_polling()
        self.stop_caja_polling()
        self.stop_mostrador_polling()
        self._init_cocina_auto_print()
        result = self._route_access_result("cocina")
        self.pagina_cargada = True
        return result

    def on_load_carta(self):
        return self._route_access_result("carta")

    @rx.var
    def reportes_avanzados_habilitados(self) -> bool:
        return plan_permite(self.empresa_plan, "reportes_avanzados")

    def on_load_configuracion(self):
        result = self._route_access_result("configuracion")
        if result is not None:
            return result
        self.cargar_config_impresora()
        self.cargar_mesas_config()
        self.cargar_sucursales_admin()
        return None

    def on_load_dono_page(self) -> None:
        self._cargar_plan_empresa()
        self.cargar_config_impresora()
        self.cargar_mesas_config()
        self.cargar_inventario()
        self.cargar_clientes()
        self.cargar_promociones()
        self.cargar_cuentas()

    # ─── Autenticación (PIN + company_id) ────────────────────────────────────

    def set_login_pin(self, value: str) -> None:
        self.login_pin_input = _normalize_pin(value)

    def append_login_digit(self, digit: str) -> None:
        if not digit.isdigit() or len(self.login_pin_input) >= 6:
            return
        self.login_error = ""
        self.login_pin_input = f"{self.login_pin_input}{digit}"

    def backspace_login_pin(self) -> None:
        self.login_pin_input = self.login_pin_input[:-1]

    def clear_login_pin(self) -> None:
        self.login_pin_input = ""

    def login_keydown(self, key: str):
        if self.login_step != "pin":
            return
        if key in "0123456789":
            return self.append_login_digit(key)
        if key == "Backspace":
            return self.backspace_login_pin()
        if key == "Enter":
            return self.submit_login_pin()
        if key == "Escape" or key == "Delete":
            return self.clear_login_pin()

    def seleccionar_login_rol(self, rol: str) -> None:
        self.login_rol_seleccionado = rol
        self.login_error = ""

    def _authenticate_with_pin(self, pin: str):
        normalized = _normalize_pin(pin)
        if len(normalized) < 4:
            self.login_pin_input = ""
            self.login_error = "Ingrese un PIN válido de 4 a 6 dígitos."
            return
        company_id = self._company_id()
        rate_key = f"pin:company:{company_id}"
        if _is_rate_limited(rate_key):
            remaining = _remaining_lockout_time(rate_key)
            self.login_pin_input = ""
            self.login_error = f"Demasiados intentos. Espere {remaining} minuto(s)."
            return
        bloqueo = _bloqueo_suscripcion(company_id)
        if bloqueo:
            self.login_pin_input = ""
            self.login_error = bloqueo
            return
        self.login_error = ""
        with self._tenant_session() as session:
            candidatos = session.exec(
                select(UsuarioFood).where(
                    UsuarioFood.company_id == company_id,
                    UsuarioFood.activo.is_(True),
                )
            ).all()
            usuario = next((u for u in candidatos if _verify_pin(normalized, u.pin)), None)
        if usuario is None:
            _record_failed_attempt(rate_key)
            self.login_pin_input = ""
            self.login_error = "PIN incorrecto. Intente nuevamente."
            return
        if (
            self.login_rol_seleccionado
            and usuario.rol != RolUsuario.ADMIN.value
            and usuario.rol != self.login_rol_seleccionado
        ):
            self.login_pin_input = ""
            self.login_error = (
                f"Ese PIN pertenece al rol {usuario.rol}. "
                f"Seleccione {usuario.rol} para ingresar."
            )
            return
        _clear_login_attempts(rate_key)
        self.login_error = ""
        sucursal_id = 0
        sucursal_nombre = ""
        sucursales = self._cargar_sucursales_empresa(company_id)
        needs_sucursal_step = False
        if usuario.sucursal_id:
            suc = next((s for s in sucursales if s.id == usuario.sucursal_id), None)
            if suc:
                sucursal_id = suc.id
                sucursal_nombre = suc.nombre
        elif len(sucursales) == 1:
            sucursal_id = sucursales[0].id
            sucursal_nombre = sucursales[0].nombre
        elif len(sucursales) > 1:
            needs_sucursal_step = True
        self.usuario_actual = UsuarioSesion(
            id=usuario.id or 0,
            nombre=usuario.nombre,
            rol=usuario.rol,
            company_id=usuario.company_id,
            sucursal_id=sucursal_id,
            sucursal_nombre=sucursal_nombre,
            perm_descuento=usuario.perm_descuento,
            perm_anular=usuario.perm_anular,
            perm_reportes=usuario.perm_reportes,
            perm_turno=usuario.perm_turno,
            perm_inventario=usuario.perm_inventario,
            perm_costos=usuario.perm_costos,
            perm_reimprimir=usuario.perm_reimprimir,
            acceso_mozos=usuario.acceso_mozos,
            acceso_caja=usuario.acceso_caja,
            acceso_cocina=usuario.acceso_cocina,
            acceso_mostrador=usuario.acceso_mostrador,
        )
        self.ultima_actividad = _utcnow().isoformat()
        self.login_pin_input = ""
        if needs_sucursal_step:
            self.login_step = "sucursal"
            return
        self._set_session_cookie(usuario, company_id, sucursal_id, sucursal_nombre)
        self.cargar_config_impresora()
        self._cargar_plan_empresa()
        return [rx.toast.success(f"Sesion iniciada como {usuario.nombre}."), rx.redirect(_role_home_route(usuario.rol), replace=True)]

    def _cargar_plan_empresa(self) -> None:
        with tenant_bypass():
            with get_session() as session:
                company = session.get(Company, self._company_id())
                if company:
                    self.empresa_plan = getattr(company, "plan", "trial") or "trial"

    def _cargar_sucursales_empresa(self, company_id: int) -> list[SucursalView]:
        with tenant_bypass():
            with get_session() as session:
                rows = session.exec(
                    select(Sucursal)
                    .where(Sucursal.company_id == company_id, Sucursal.activa.is_(True))
                    .order_by(Sucursal.es_principal.desc(), Sucursal.nombre)
                ).all()
        self.sucursales_empresa = [
            SucursalView(
                id=s.id or 0, nombre=s.nombre, direccion=s.direccion,
                telefono=s.telefono, activa=s.activa, es_principal=s.es_principal,
            )
            for s in rows
        ]
        return self.sucursales_empresa

    def seleccionar_sucursal_login(self, sucursal_id: int) -> None:
        suc = next((s for s in self.sucursales_empresa if s.id == sucursal_id), None)
        if suc is None or self.usuario_actual is None:
            return
        self.usuario_actual = self.usuario_actual.model_copy(
            update={"sucursal_id": suc.id, "sucursal_nombre": suc.nombre}
        )
        self._set_session_cookie_from_current()
        self.cargar_config_impresora()
        self._cargar_plan_empresa()
        return [rx.toast.success(f"Sesion iniciada como {self.usuario_actual.nombre}."), rx.redirect(_role_home_route(self.usuario_actual.rol), replace=True)]

    def volver_a_pin_login(self) -> None:
        self.usuario_actual = None
        self.login_step = "pin"
        self.login_pin_input = ""
        self.login_error = ""

    def cambiar_sucursal(self, sucursal_id: int) -> None:
        if self.usuario_actual is None:
            return
        suc = next((s for s in self.sucursales_empresa if s.id == sucursal_id), None)
        if suc is None:
            return
        self.usuario_actual = self.usuario_actual.model_copy(
            update={"sucursal_id": suc.id, "sucursal_nombre": suc.nombre}
        )
        self._set_session_cookie_from_current()
        self._clear_operational_context()
        self.cargar_datos_iniciales()

    # ─── Admin CRUD sucursales ────────────────────────────────────────────────

    def cargar_sucursales_admin(self) -> None:
        with self._tenant_session() as session:
            rows = session.exec(
                select(Sucursal)
                .where(Sucursal.company_id == self._company_id())
                .order_by(Sucursal.es_principal.desc(), Sucursal.nombre)
            ).all()
        self.sucursales_empresa = [
            SucursalView(
                id=s.id or 0, nombre=s.nombre, direccion=s.direccion,
                telefono=s.telefono, activa=s.activa, es_principal=s.es_principal,
            )
            for s in rows
        ]

    def abrir_form_sucursal(self, sucursal_id: int = 0) -> None:
        if sucursal_id:
            suc = next((s for s in self.sucursales_empresa if s.id == sucursal_id), None)
            if suc:
                self.sucursal_admin_form_id = suc.id
                self.sucursal_admin_form_nombre = suc.nombre
                self.sucursal_admin_form_direccion = suc.direccion
                self.sucursal_admin_form_telefono = suc.telefono
                self.sucursal_admin_form_activa = suc.activa
                self.sucursal_admin_form_es_principal = suc.es_principal
        else:
            self.sucursal_admin_form_id = 0
            self.sucursal_admin_form_nombre = ""
            self.sucursal_admin_form_direccion = ""
            self.sucursal_admin_form_telefono = ""
            self.sucursal_admin_form_activa = True
            self.sucursal_admin_form_es_principal = False
        self.sucursal_admin_form_visible = True

    def cerrar_form_sucursal(self) -> None:
        self.sucursal_admin_form_visible = False

    def on_change_suc_nombre(self, v: str) -> None:
        self.sucursal_admin_form_nombre = v

    def on_change_suc_direccion(self, v: str) -> None:
        self.sucursal_admin_form_direccion = v

    def on_change_suc_telefono(self, v: str) -> None:
        self.sucursal_admin_form_telefono = v

    def toggle_suc_activa(self) -> None:
        self.sucursal_admin_form_activa = not self.sucursal_admin_form_activa

    def toggle_suc_principal(self) -> None:
        self.sucursal_admin_form_es_principal = not self.sucursal_admin_form_es_principal

    def guardar_sucursal(self) -> None:
        nombre = self.sucursal_admin_form_nombre.strip()
        if not nombre:
            return rx.toast.error("El nombre de la sucursal es obligatorio.")
        company_id = self._company_id()
        with self._tenant_session() as session:
            if self.sucursal_admin_form_es_principal:
                session.exec(
                    sa_update(Sucursal)
                    .where(Sucursal.company_id == company_id)
                    .values(es_principal=False)
                )
            if self.sucursal_admin_form_id:
                suc = session.get(Sucursal, self.sucursal_admin_form_id)
                if suc and suc.company_id == company_id:
                    suc.nombre = nombre
                    suc.direccion = self.sucursal_admin_form_direccion.strip()
                    suc.telefono = self.sucursal_admin_form_telefono.strip()
                    suc.activa = self.sucursal_admin_form_activa
                    suc.es_principal = self.sucursal_admin_form_es_principal
                    session.add(suc)
            else:
                suc = Sucursal(
                    company_id=company_id,
                    nombre=nombre,
                    direccion=self.sucursal_admin_form_direccion.strip(),
                    telefono=self.sucursal_admin_form_telefono.strip(),
                    activa=self.sucursal_admin_form_activa,
                    es_principal=self.sucursal_admin_form_es_principal,
                )
                session.add(suc)
            session.commit()
        self.sucursal_admin_form_visible = False
        self.cargar_sucursales_admin()
        return rx.toast.success(f"Sucursal '{nombre}' guardada.")

    # ── Self-order (QR tokens + aprobación) ──────────────────────────────────

    def generar_qr_tokens_mesas(self):
        count = 0
        with self._tenant_session() as session:
            mesas = session.exec(
                select(Mesa).where(
                    Mesa.company_id == self._company_id(),
                    Mesa.activa.is_(True),
                )
            ).all()
            for mesa in mesas:
                if not mesa.qr_token:
                    mesa.qr_token = secrets.token_urlsafe(16)
                    session.add(mesa)
                    count += 1
            session.commit()
        self.cargar_mesas()
        self.cargar_mesas_config()
        if count:
            return rx.toast.success(f"Tokens QR generados para {count} mesa(s)")
        return rx.toast.info("Todas las mesas ya tienen token QR")

    def regenerar_qr_token_mesa(self, mesa_id: int) -> None:
        with self._tenant_session() as session:
            mesa = session.get(Mesa, mesa_id)
            if mesa and mesa.company_id == self._company_id():
                mesa.qr_token = secrets.token_urlsafe(16)
                session.add(mesa)
                session.commit()
        self.cargar_mesas_config()

    def cargar_self_orders_pendientes(self) -> None:
        with self._tenant_session() as session:
            pedidos = session.exec(
                select(Pedido).where(
                    Pedido.company_id == self._company_id(),
                    Pedido.self_order.is_(True),
                    Pedido.self_order_aprobado.is_(False),
                    Pedido.estado != EstadoPedido.CANCELADO.value,
                ).order_by(Pedido.abierto_en.desc())
            ).all()
            if not pedidos:
                if self.self_orders_pendientes:
                    self.self_orders_pendientes = []
                return
            mesas = {m.id: m for m in session.exec(
                select(Mesa).where(Mesa.company_id == self._company_id())
            ).all()}
            productos = {p.id: p for p in session.exec(
                select(Producto).where(Producto.company_id == self._company_id())
            ).all()}
            result: list[SelfOrderPendienteView] = []
            for pedido in pedidos:
                mesa = mesas.get(pedido.mesa_id or 0)
                mesa_label = (mesa.nombre or f"Mesa {mesa.numero}") if mesa else "?"
                detalles = session.exec(
                    select(DetallePedido).where(DetallePedido.pedido_id == pedido.id)
                ).all()
                resumen = " · ".join(
                    f"{d.cantidad}x {productos[d.producto_id].nombre if d.producto_id in productos else '?'}"
                    for d in detalles
                )
                hora = pedido.abierto_en or pedido.created_at
                result.append(SelfOrderPendienteView(
                    pedido_id=pedido.id or 0,
                    mesa_label=mesa_label,
                    nombre_cliente=_actor_name(pedido.nombre_cliente) or "Cliente QR",
                    items_resumen=resumen,
                    total_texto=_money_text(pedido.total),
                    hora_texto=hora.strftime("%H:%M") if hora else "",
                ))
            if _list_fingerprint(result) != _list_fingerprint(self.self_orders_pendientes):
                self.self_orders_pendientes = result

    def aprobar_self_order(self, pedido_id: int) -> None:
        with self._tenant_session() as session:
            pedido = session.get(Pedido, pedido_id)
            if not (pedido and pedido.company_id == self._company_id() and pedido.self_order):
                return
            pedido.self_order_aprobado = True
            now = utc_now_naive()
            existing = session.exec(
                select(Pedido).where(
                    Pedido.company_id == self._company_id(),
                    Pedido.mesa_id == pedido.mesa_id,
                    Pedido.id != pedido.id,
                    Pedido.estado.in_(OPEN_ORDER_STATES),
                ).order_by(Pedido.id.desc())
            ).first() if pedido.mesa_id else None
            if existing:
                detalles = session.exec(
                    select(DetallePedido).where(
                        DetallePedido.pedido_id == pedido.id,
                    )
                ).all()
                for d in detalles:
                    d.pedido_id = existing.id
                    d.impreso_cocina = True
                    d.enviado_cocina_at = now
                    d.estado_produccion = EstadoProduccion.PENDIENTE.value
                    session.add(d)
                pedido.estado = EstadoPedido.COBRADO.value
                session.add(pedido)
                _recalculate_order_total(session, existing)
                _sync_order_status(session, existing)
            else:
                detalles = session.exec(
                    select(DetallePedido).where(
                        DetallePedido.pedido_id == pedido.id,
                        DetallePedido.impreso_cocina.is_(False),
                    )
                ).all()
                for d in detalles:
                    d.impreso_cocina = True
                    d.enviado_cocina_at = now
                    d.estado_produccion = EstadoProduccion.PENDIENTE.value
                    session.add(d)
                _recalculate_order_total(session, pedido)
                _sync_order_status(session, pedido)
            mesa = session.get(Mesa, pedido.mesa_id) if pedido.mesa_id else None
            if mesa:
                mesa.estado = EstadoMesa.OCUPADA.value
                mesa.updated_at = now
                session.add(mesa)
            session.commit()
        self.cargar_self_orders_pendientes()
        self.cargar_mesas()
        self.cargar_cocina()

    def rechazar_self_order(self, pedido_id: int) -> None:
        with self._tenant_session() as session:
            pedido = session.get(Pedido, pedido_id)
            if pedido and pedido.company_id == self._company_id() and pedido.self_order:
                pedido.estado = EstadoPedido.CANCELADO.value
                session.add(pedido)
                session.commit()
        self.cargar_self_orders_pendientes()

    @rx.var
    def empresa_plan_label(self) -> str:
        return plan_label(self.empresa_plan)

    @rx.var
    def plan_permite_inventario(self) -> bool:
        return plan_permite(self.empresa_plan, "inventario")

    @rx.var
    def plan_permite_clientes(self) -> bool:
        return plan_permite(self.empresa_plan, "clientes")

    @rx.var
    def plan_permite_cuentas(self) -> bool:
        return plan_permite(self.empresa_plan, "cuentas_corrientes")

    @rx.var
    def plan_permite_promociones(self) -> bool:
        return plan_permite(self.empresa_plan, "promociones")

    @rx.var
    def plan_permite_cupones(self) -> bool:
        return plan_permite(self.empresa_plan, "cupones")

    def login(self, pin: str):
        return self._authenticate_with_pin(pin)

    def submit_login_pin(self):
        return self._authenticate_with_pin(self.login_pin_input)

    def logout(self):
        self.usuario_actual = None
        self.session_token = ""
        self._clear_operational_context()
        return rx.redirect("/login", replace=True)

    # ─── Configuración impresoras ─────────────────────────────────────────────

    def cargar_config_impresora(self) -> None:
        with self._tenant_session() as session:
            cfg = session.exec(
                select(ConfigImpresora).where(ConfigImpresora.company_id == self._company_id())
            ).first()
            if cfg:
                self.config_nombre_local = cfg.nombre_local
                self.config_ticket_paper_width_mm = str(cfg.ticket_paper_width_mm)
                self.config_slug = cfg.slug or "mi-restaurante"
                self.config_admin_email = cfg.admin_email or ""
                self.config_ruc = cfg.ruc or ""
                self.config_sucursal = cfg.sucursal or ""
                self.config_direccion = cfg.direccion or ""
                self.config_telefono = cfg.telefono or ""
                self.config_mensaje_ticket = cfg.mensaje_ticket or "¡Gracias por su preferencia!"
                self.config_mostrar_iva = cfg.mostrar_iva
                self.config_nombre_impuesto = cfg.nombre_impuesto or "IGV"
                self.config_porcentaje_iva = str(cfg.porcentaje_iva)
                self.config_kds_minutos_alerta = str(cfg.kds_minutos_alerta)
                url = f"{_FOOD_BASE_URL}/menu/{self.config_slug}"
                self.config_menu_url = url
                self.config_menu_qr_base64 = _generar_qr_base64(url)
            empresa = session.get(Company, self._company_id())
            self.config_logo_url = (empresa.logo_url or "") if empresa else ""

    def guardar_config_impresora(self) -> None:
        with self._tenant_session() as session:
            cfg = session.exec(
                select(ConfigImpresora).where(ConfigImpresora.company_id == self._company_id())
            ).first()
            if cfg is None:
                cfg = ConfigImpresora(company_id=self._company_id())
            cfg.nombre_local = self.config_nombre_local.strip() or "Mi Restaurante"
            try:
                ancho = int(self.config_ticket_paper_width_mm.strip())
                cfg.ticket_paper_width_mm = ancho if ancho in (58, 80) else 80
            except (ValueError, AttributeError):
                cfg.ticket_paper_width_mm = 80
            cfg.ruc = self.config_ruc.strip()
            cfg.sucursal = self.config_sucursal.strip()
            cfg.direccion = self.config_direccion.strip()
            cfg.telefono = self.config_telefono.strip()
            cfg.mensaje_ticket = self.config_mensaje_ticket.strip() or "¡Gracias por su preferencia!"
            cfg.mostrar_iva = self.config_mostrar_iva
            cfg.nombre_impuesto = self.config_nombre_impuesto.strip() or "IGV"
            try:
                pct = float(self.config_porcentaje_iva.strip())
                cfg.porcentaje_iva = pct if 0 < pct <= 100 else 18.0
            except (ValueError, AttributeError):
                cfg.porcentaje_iva = 18.0
            try:
                kds_min = int(self.config_kds_minutos_alerta.strip())
                cfg.kds_minutos_alerta = kds_min if 1 <= kds_min <= 120 else 15
            except (ValueError, AttributeError):
                cfg.kds_minutos_alerta = 15
            slug = _slugify(self.config_slug) if self.config_slug.strip() else _slugify(cfg.nombre_local)
            cfg.slug = slug
            cfg.updated_at = _utcnow()
            session.add(cfg)
            empresa = session.get(Company, self._company_id())
            if empresa is not None:
                empresa.logo_url = self.config_logo_url or None
                empresa.slug = slug
                session.add(empresa)
            session.commit()
        self.config_slug = slug
        url = f"{_FOOD_BASE_URL}/menu/{slug}"
        self.config_menu_url = url
        self.config_menu_qr_base64 = _generar_qr_base64(url)
        return rx.toast.success("Configuración guardada.")

    @rx.var
    def ticket_preview_text(self) -> str:
        from app.services.receipt_service import (
            _center, _chars_for_mm, _format_sale_line, _line, _money, _row,
        )
        try:
            paper_mm = int(self.config_ticket_paper_width_mm.strip())
        except (ValueError, AttributeError):
            paper_mm = 80
        w = _chars_for_mm(paper_mm)
        nombre = self.config_nombre_local.strip() or "Mi Restaurante"
        items_demo = [
            TicketLine(name="Lomo Saltado", quantity=2, unit_price=32.0, subtotal=64.0),
            TicketLine(name="Inka Cola 500ml", quantity=2, unit_price=5.0, subtotal=10.0, note="bien fría"),
            TicketLine(name="Ceviche Clásico", quantity=1, unit_price=38.0, subtotal=38.0),
        ]
        lines: list[str] = [_center(nombre.upper(), w)]
        suc = self.config_sucursal.strip()
        if suc:
            lines.append(_center(suc.upper(), w))
        ruc = self.config_ruc.strip()
        if ruc:
            lines.append(_center(f"RUC: {ruc}", w))
        direc = self.config_direccion.strip()
        if direc:
            lines.append(_center(direc, w))
        tel = self.config_telefono.strip()
        if tel:
            lines.append(_center(f"Tel.: {tel}", w))
        lines += ["", _center("COMPROBANTE DE PAGO", w), _line(w), "Mesa 1", "Pedido: #99",
                   "Atendido por: Demo", _line(w)]
        for item in items_demo:
            lines.extend(_format_sale_line(item, w))
            if item.note:
                lines.append(f"  * {item.note}")
        lines.append(_line(w))
        if self.config_mostrar_iva:
            try:
                pct = float(self.config_porcentaje_iva.strip() or "18")
            except ValueError:
                pct = 18.0
            tax_name = self.config_nombre_impuesto.strip() or "IGV"
            iva_amount = 112.0 * pct / (100 + pct)
            net = 112.0 - iva_amount
            lines.append(_row("Subtotal:", _money(net), w))
            lines.append(_row(f"{tax_name} ({pct:.4g}%):", _money(iva_amount), w))
        lines.append(_row("TOTAL A PAGAR:", _money(112.0), w))
        lines += [_line(w), _row("Método de pago:", "Efectivo", w), _line(w)]
        footer = self.config_mensaje_ticket.strip() or "¡Gracias por su preferencia!"
        lines.append(_center(footer, w))
        return "\n".join(lines)

    def imprimir_ticket_prueba(self):
        try:
            paper_mm = int(self.config_ticket_paper_width_mm.strip())
        except (ValueError, AttributeError):
            paper_mm = 80
        nombre = self.config_nombre_local.strip() or "Mi Restaurante"
        items_demo = [
            TicketLine(name="Lomo Saltado", quantity=2, unit_price=32.0, subtotal=64.0),
            TicketLine(name="Inka Cola 500ml", quantity=2, unit_price=5.0, subtotal=10.0, note="bien fría"),
            TicketLine(name="Ceviche Clásico", quantity=1, unit_price=38.0, subtotal=38.0),
        ]
        html = generate_cashier_ticket_html(
            order_reference="Mesa 1",
            pedido_id=0,
            items=items_demo,
            total=112.0,
            attended_by="Ticket de Prueba",
            company_name=nombre,
            company_ruc=self.config_ruc.strip(),
            company_sucursal=self.config_sucursal.strip(),
            company_direccion=self.config_direccion.strip(),
            company_telefono=self.config_telefono.strip(),
            descuento=0.0,
            metodo_pago="efectivo",
            mensaje_footer=self.config_mensaje_ticket.strip() or "¡Gracias por su preferencia!",
            mostrar_iva=self.config_mostrar_iva,
            nombre_impuesto=self.config_nombre_impuesto.strip() or "IGV",
            porcentaje_iva=float(self.config_porcentaje_iva.strip() or "18"),
            paper_width_mm=paper_mm,
        )
        return rx.call_script(build_print_script(html))

    def set_config_nombre_local(self, v: str) -> None:
        self.config_nombre_local = v

    def set_config_ticket_paper_width_mm(self, v: str) -> None:
        self.config_ticket_paper_width_mm = v

    def set_config_ruc(self, v: str) -> None:
        self.config_ruc = v

    def set_config_sucursal(self, v: str) -> None:
        self.config_sucursal = v

    def set_config_direccion(self, v: str) -> None:
        self.config_direccion = v

    def set_config_telefono(self, v: str) -> None:
        self.config_telefono = v

    def set_config_mensaje_ticket(self, v: str) -> None:
        self.config_mensaje_ticket = v

    def toggle_config_mostrar_iva(self) -> None:
        self.config_mostrar_iva = not self.config_mostrar_iva

    def set_config_nombre_impuesto(self, v: str) -> None:
        self.config_nombre_impuesto = v

    def set_config_porcentaje_iva(self, v: str) -> None:
        self.config_porcentaje_iva = v

    def set_config_kds_minutos_alerta(self, v: str) -> None:
        self.config_kds_minutos_alerta = v

    def set_config_slug(self, v: str) -> None:
        self.config_slug = v

    def set_config_admin_email(self, v: str) -> None:
        self.config_admin_email = v

    def set_config_admin_password_nueva(self, v: str) -> None:
        self.config_admin_password_nueva = v

    def set_config_admin_password_confirm(self, v: str) -> None:
        self.config_admin_password_confirm = v

    def toggle_config_admin_show_password(self) -> None:
        self.config_admin_show_password = not self.config_admin_show_password

    def guardar_admin_cuenta(self) -> None:
        email = self.config_admin_email.strip().lower()
        if not email or "@" not in email:
            return rx.toast.error("Ingrese un email válido.")
        nueva = self.config_admin_password_nueva.strip()
        confirm = self.config_admin_password_confirm.strip()
        if nueva and nueva != confirm:
            return rx.toast.error("Las contraseñas no coinciden.")
        with self._tenant_session() as session:
            cfg = session.exec(
                select(ConfigImpresora).where(ConfigImpresora.company_id == self._company_id())
            ).first()
            if cfg is None:
                cfg = ConfigImpresora(company_id=self._company_id())
            cfg.admin_email = email
            if nueva:
                cfg.admin_password_hash = _bcrypt.hashpw(nueva.encode(), _bcrypt.gensalt()).decode()
            session.add(cfg)
            session.commit()
        self.config_admin_email = email
        self.config_admin_password_nueva = ""
        self.config_admin_password_confirm = ""
        return rx.toast.success("Cuenta del dueño guardada.")

    async def handle_upload_logo_empresa(self, files: list[rx.UploadFile]) -> None:
        for file in files:
            try:
                data = await file.read()
                if len(data) > 5 * 1024 * 1024:
                    return rx.toast.error("La imagen excede 5 MB.", duration=4000)
                data, ext = optimize_image(data)
                filename = f"food_logo_{uuid.uuid4().hex[:12]}{ext}"
                upload_dir = pathlib.Path(rx.get_upload_dir()) / "food_empresas"
                upload_dir.mkdir(parents=True, exist_ok=True)
                (upload_dir / filename).write_bytes(data)
                self.config_logo_url = f"{_FOOD_API_URL}/_upload/food_empresas/{filename}"
            except Exception:
                return rx.toast.error(
                    "Error al subir la imagen. Verifique permisos del servidor.",
                    duration=5000,
                )
            break

    def quitar_logo_empresa(self) -> None:
        self.config_logo_url = ""

    # ─── CRUD Mesas (admin config) ────────────────────────────────────────────

    def cargar_mesas_config(self) -> None:
        base_url = self.config_menu_url
        with self._tenant_session() as session:
            mesas = session.exec(
                select(Mesa)
                .where(Mesa.company_id == self._company_id())
                .order_by(Mesa.numero)
            ).all()
            result = []
            for m in mesas:
                qr_url = f"{base_url}?mesa={m.qr_token}" if m.qr_token and base_url else ""
                result.append(MesaAdminView(
                    id=m.id or 0,
                    numero=m.numero,
                    nombre=m.nombre or "",
                    capacidad=m.capacidad,
                    activa=m.activa,
                    estado=m.estado,
                    sector=m.sector or "Salón",
                    qr_token=m.qr_token or "",
                    qr_url=qr_url,
                    qr_base64=_generar_qr_base64(qr_url) if qr_url else "",
                ))
            self.mesas_config = result

    def _reset_mesa_config_form(self) -> None:
        self.mesa_config_form_id = 0
        self.mesa_config_form_numero = ""
        self.mesa_config_form_nombre = ""
        self.mesa_config_form_capacidad = "4"
        self.mesa_config_form_sector = "Salón"

    def cancelar_mesa_config_form(self) -> None:
        self._reset_mesa_config_form()

    def editar_mesa_config(self, mesa_id: int) -> None:
        with self._tenant_session() as session:
            m = session.get(Mesa, mesa_id)
        if m is None or m.company_id != self._company_id():
            return
        self.mesa_config_form_id = m.id or 0
        self.mesa_config_form_numero = str(m.numero)
        self.mesa_config_form_nombre = m.nombre or ""
        self.mesa_config_form_capacidad = str(m.capacidad)
        self.mesa_config_form_sector = m.sector or "Salón"

    def guardar_mesa_config(self) -> None:
        try:
            numero = int(self.mesa_config_form_numero.strip())
        except (ValueError, AttributeError):
            return rx.toast.error("El número de mesa debe ser un entero.")
        try:
            capacidad = max(1, int(self.mesa_config_form_capacidad.strip() or "4"))
        except ValueError:
            capacidad = 4
        nombre = self.mesa_config_form_nombre.strip()
        with self._tenant_session() as session:
            es_edicion = self.mesa_config_form_id > 0
            if es_edicion:
                m = session.get(Mesa, self.mesa_config_form_id)
                if m is None or m.company_id != self._company_id():
                    return rx.toast.error("Mesa no encontrada.")
            else:
                total_mesas = len(session.exec(
                    select(Mesa).where(
                        Mesa.company_id == self._company_id(),
                        Mesa.activa.is_(True),
                    )
                ).all())
                msg_limite = check_limite_mesas(self.empresa_plan, total_mesas)
                if msg_limite:
                    return rx.toast.error(msg_limite, duration=5000)
                conflicto = session.exec(
                    select(Mesa).where(
                        Mesa.company_id == self._company_id(),
                        Mesa.numero == numero,
                    )
                ).first()
                if conflicto:
                    return rx.toast.error(f"Ya existe la mesa #{numero}.")
                m = Mesa(company_id=self._company_id(), numero=numero)
            m.numero = numero
            m.nombre = nombre
            m.capacidad = capacidad
            m.sector = self.mesa_config_form_sector.strip() or "Salón"
            m.updated_at = _utcnow()
            session.add(m)
            session.commit()
        accion = "actualizada" if self.mesa_config_form_id > 0 else "creada"
        self._reset_mesa_config_form()
        self.cargar_mesas_config()
        return rx.toast.success(f"Mesa #{numero} {accion}.")

    def toggle_mesa_activa_config(self, mesa_id: int) -> None:
        with self._tenant_session() as session:
            m = session.get(Mesa, mesa_id)
            if m is None or m.company_id != self._company_id():
                return
            m.activa = not m.activa
            m.updated_at = _utcnow()
            session.add(m)
            session.commit()
        self.cargar_mesas_config()

    def eliminar_mesa_config(self, mesa_id: int) -> None:
        with self._tenant_session() as session:
            m = session.get(Mesa, mesa_id)
            if m is None or m.company_id != self._company_id():
                return rx.toast.error("Mesa no encontrada.")
            pedido_abierto = session.exec(
                select(Pedido).where(
                    Pedido.mesa_id == mesa_id,
                    Pedido.estado.in_(list(OPEN_ORDER_STATES)),
                )
            ).first()
            if pedido_abierto:
                return rx.toast.error(f"La mesa #{m.numero} tiene un pedido activo — no se puede eliminar.")
            _toast_msg = f"Mesa #{m.numero} eliminada."
            session.delete(m)
            session.commit()
        self.cargar_mesas_config()
        return rx.toast.success(_toast_msg)

    def set_mesa_config_form_numero(self, v: str) -> None:
        self.mesa_config_form_numero = v

    def set_mesa_config_form_nombre(self, v: str) -> None:
        self.mesa_config_form_nombre = v

    def set_mesa_config_form_capacidad(self, v: str) -> None:
        self.mesa_config_form_capacidad = v

    def set_mesa_config_form_sector(self, v: str) -> None:
        self.mesa_config_form_sector = v

    def _ticket_paper_width_mm(self) -> int:
        try:
            with self._tenant_session() as session:
                cfg = session.exec(
                    select(ConfigImpresora).where(ConfigImpresora.company_id == self._company_id())
                ).first()
                if cfg is not None:
                    return cfg.ticket_paper_width_mm
        except Exception:
            pass
        return 80

    # ─── Polling ──────────────────────────────────────────────────────────────

    def _refresh_mozos_slice(self) -> bool:
        if self.usuario_actual is None:
            return False
        prev = self._prev_mesas_alerta_entrega
        self.cargar_mesas()
        self.cargar_self_orders_pendientes()
        if self.mesa_seleccionada_id:
            self._cargar_carrito_mesa(self.mesa_seleccionada_id)
            if not self.precuenta_parcial_modo:
                self._cargar_historial_mesa(self.mesa_seleccionada_id)
        current = sum(1 for m in self.mesas if m.tiene_items_listos)
        self._prev_mesas_alerta_entrega = current
        return self.sonidos_activos and prev >= 0 and current > prev

    def _refresh_cocina_slice(self) -> bool:
        if self.usuario_actual is None:
            return False
        prev = self._prev_tickets_pendientes
        self.cargar_cocina()
        self.cargar_mesas()
        current = len([t for t in self.tickets_cocina if t.estado_produccion == "pendiente"])
        self._prev_tickets_pendientes = current
        return self.sonidos_activos and prev >= 0 and current > prev

    def _refresh_caja_slice(self) -> None:
        if self.usuario_actual is None:
            return
        self.cargar_mesas()
        self.cargar_pedidos_mostrador_pendientes()
        if self.mesa_seleccionada_id:
            self._cargar_historial_mesa(self.mesa_seleccionada_id)

    def _refresh_mostrador_slice(self) -> None:
        if self.usuario_actual is None:
            return
        self.cargar_pedidos_mostrador_pendientes()
        self.cargar_pedidos_mostrador_entregados()

    # ─── Auto-impresión de tickets de cocina ───────────────────────────────

    def _init_cocina_auto_print(self) -> None:
        """Marca el max detalle ID actual para no reimprimir tickets viejos."""
        with self._tenant_session() as session:
            result = session.exec(
                select(DetallePedido.id)
                .where(DetallePedido.company_id == self._company_id())
                .order_by(DetallePedido.id.desc())
                .limit(1)
            ).first()
            self.cocina_auto_print_max_id = result or 0

    def _check_cocina_auto_print(self) -> str:
        """Detecta items nuevos enviados a cocina y genera ticket HTML combinado."""
        with self._tenant_session() as session:
            if self.cocina_auto_print_max_id == 0:
                cur_max = session.exec(
                    select(DetallePedido.id)
                    .where(DetallePedido.company_id == self._company_id())
                    .order_by(DetallePedido.id.desc())
                    .limit(1)
                ).first()
                self.cocina_auto_print_max_id = cur_max or 0
                return ""
            new_detalles = session.exec(
                select(DetallePedido)
                .where(
                    DetallePedido.company_id == self._company_id(),
                    DetallePedido.impreso_cocina.is_(True),
                    DetallePedido.id > self.cocina_auto_print_max_id,
                )
                .order_by(DetallePedido.id)
            ).all()
            if not new_detalles:
                return ""
            self.cocina_auto_print_max_id = max(d.id or 0 for d in new_detalles)
            pedido_groups: dict[int, list] = {}
            for d in new_detalles:
                pedido_groups.setdefault(d.pedido_id, []).append(d)
            pedido_ids = list(pedido_groups.keys())
            pedidos = {p.id: p for p in session.exec(select(Pedido).where(Pedido.id.in_(pedido_ids))).all()}
            mesas = {m.id: m for m in session.exec(select(Mesa).where(Mesa.company_id == self._company_id())).all()}
            productos = {p.id: p for p in session.exec(select(Producto).where(Producto.company_id == self._company_id())).all()}
            htmls: list[str] = []
            for pid, detalles in pedido_groups.items():
                pedido = pedidos.get(pid)
                if pedido is None or pedido.estado == EstadoPedido.CANCELADO.value:
                    continue
                mesa = mesas.get(pedido.mesa_id) if pedido.mesa_id else None
                if mesa:
                    mesa_label = mesa.nombre or f"Mesa {mesa.numero}"
                elif pedido.tipo_pedido == TipoPedido.MOSTRADOR.value:
                    nombre_cli = _actor_name(pedido.nombre_cliente or "") or "Sin nombre"
                    mesa_label = f"Para Llevar - {nombre_cli}"
                else:
                    mesa_label = f"Pedido #{pid}"
                lines = [
                    TicketLine(
                        name=(productos.get(d.producto_id).nombre if productos.get(d.producto_id) else f"Producto {d.producto_id}"),
                        quantity=d.cantidad,
                        note=d.notas or "",
                    )
                    for d in detalles
                ]
                htmls.append(generate_kitchen_ticket_html(
                    mesa_label=mesa_label,
                    pedido_id=pid,
                    items=lines,
                    paper_width_mm=self._ticket_paper_width_mm(),
                ))
            if not htmls:
                return ""
            if len(htmls) == 1:
                return htmls[0]
            import re as _re
            parts = []
            for h in htmls:
                m = _re.search(r"<pre>(.*?)</pre>", h, _re.DOTALL)
                if m:
                    parts.append(m.group(1))
            cut = "\n" + "- " * 16 + "\n" + "        ✂ CORTAR" + "\n" + "- " * 16 + "\n\n\n"
            combined = cut.join(parts)
            pw = self._ticket_paper_width_mm()
            return (
                f'<html><head><meta charset="utf-8"/><title>Comandas</title>'
                f"<style>@page{{size:{pw}mm auto;margin:0}}body{{margin:0;padding:2mm}}"
                f"pre{{font-family:monospace;font-size:12px;margin:0;white-space:pre-wrap;word-break:break-word}}</style>"
                f"</head><body><pre>{combined}</pre></body></html>"
            )

    # ─── Polling ─────────────────────────────────────────────────────────

    async def _run_polling_loop(self, flag_name: str, interval_seconds: int, refresh_callback) -> None:
        async with self:
            if getattr(self, flag_name):
                return
            setattr(self, flag_name, True)
            refresh_callback()
        while True:
            await asyncio.sleep(interval_seconds)
            try:
                async with self:
                    if not getattr(self, flag_name):
                        break
                    if self._check_session_expiry():
                        setattr(self, flag_name, False)
                        break
                    refresh_callback()
            except Exception:
                break

    @rx.event(background=True)
    async def start_mozos_polling(self) -> None:
        async with self:
            if self.mozos_polling_enabled:
                return
            self.mozos_polling_enabled = True
            self._refresh_mozos_slice()
        while True:
            await asyncio.sleep(3)
            try:
                play_sound = False
                async with self:
                    if not self.mozos_polling_enabled:
                        break
                    if self._check_session_expiry():
                        self.mozos_polling_enabled = False
                        break
                    play_sound = self._refresh_mozos_slice()
                if play_sound:
                    yield rx.call_script(_SOUND_CHIME_JS)
                    yield rx.call_script(_VIBRATE_JS)
            except Exception:
                break

    def stop_mozos_polling(self) -> None:
        self.mozos_polling_enabled = False

    @rx.event(background=True)
    async def start_cocina_polling(self) -> None:
        async with self:
            if self.cocina_polling_enabled:
                return
            self.cocina_polling_enabled = True
            self._refresh_cocina_slice()
        while True:
            await asyncio.sleep(3)
            try:
                print_html = ""
                play_sound = False
                async with self:
                    if not self.cocina_polling_enabled:
                        break
                    if self._check_session_expiry():
                        self.cocina_polling_enabled = False
                        break
                    play_sound = self._refresh_cocina_slice()
                    print_html = self._check_cocina_auto_print()
                if print_html:
                    yield rx.call_script(build_print_script(print_html))
                if play_sound:
                    yield rx.call_script(_SOUND_BELL_JS)
                    yield rx.call_script(_VIBRATE_JS)
            except Exception:
                break

    def stop_cocina_polling(self) -> None:
        self.cocina_polling_enabled = False

    def toggle_cocina_fullscreen(self) -> None:
        self.cocina_fullscreen = not self.cocina_fullscreen

    def toggle_sonidos(self) -> None:
        self.sonidos_activos = not self.sonidos_activos
        return rx.toast.info("Sonidos activados" if self.sonidos_activos else "Sonidos desactivados")

    @rx.event(background=True)
    async def start_caja_polling(self) -> None:
        async with self:
            if self.caja_polling_enabled:
                return
            self.caja_polling_enabled = True
            self._refresh_caja_slice()
        while True:
            await asyncio.sleep(3)
            try:
                print_html = ""
                async with self:
                    if not self.caja_polling_enabled:
                        break
                    if self._check_session_expiry():
                        self.caja_polling_enabled = False
                        break
                    self._refresh_caja_slice()
                    print_html = self._check_cocina_auto_print()
                if print_html:
                    yield rx.call_script(build_print_script(print_html))
            except Exception:
                break

    def stop_caja_polling(self) -> None:
        self.caja_polling_enabled = False

    @rx.event(background=True)
    async def start_mostrador_polling(self) -> None:
        await self._run_polling_loop("mostrador_polling_enabled", 3, self._refresh_mostrador_slice)

    def stop_mostrador_polling(self) -> None:
        self.mostrador_polling_enabled = False

    # ─── Mesas ───────────────────────────────────────────────────────────────

    def cargar_mesas(self) -> None:
        mesas_ui: list[MesaView] = []
        with self._tenant_session() as session:
            q = select(Mesa).where(
                Mesa.company_id == self._company_id(),
                Mesa.activa.is_(True),
            ).order_by(Mesa.numero)
            q = self._sucursal_filter(Mesa, q)
            mesas_db = session.exec(q).all()

            mesa_ids = [m.id for m in mesas_db if m.id]

            # Bulk: 1 query para todos los pedidos abiertos del tenant
            pedidos_abiertos: dict[int, Pedido] = {}
            if mesa_ids:
                for p in session.exec(
                    select(Pedido).where(
                        Pedido.company_id == self._company_id(),
                        Pedido.mesa_id.in_(mesa_ids),
                        Pedido.estado.in_(OPEN_ORDER_STATES),
                    ).order_by(Pedido.id.desc())
                ).all():
                    if p.mesa_id not in pedidos_abiertos:
                        pedidos_abiertos[p.mesa_id] = p

            # Nivel 2: Expirar pedidos abandonados (> 8h sin actividad)
            ahora = _utcnow()
            pedidos_expirados_ids: list[int] = []
            for mesa_id, pedido in list(pedidos_abiertos.items()):
                inactivo_min = max(0, int((ahora - pedido.updated_at).total_seconds() // 60))
                if inactivo_min >= PEDIDO_EXPIRACION_MIN:
                    pedido.estado = EstadoPedido.CANCELADO.value
                    pedido.motivo_cancelacion = f"Expirado automáticamente por {inactivo_min} min de inactividad"
                    pedido.cancelado_en = ahora
                    session.add(pedido)
                    registrar_auditoria(
                        session, pedido.company_id, "pedido_expirado",
                        entidad="Pedido", entidad_id=pedido.id,
                        detalle={"mesa_id": mesa_id, "inactivo_min": inactivo_min, "total": str(pedido.total)},
                    )
                    pedidos_expirados_ids.append(mesa_id)
                    del pedidos_abiertos[mesa_id]
            if pedidos_expirados_ids:
                session.commit()

            pedido_ids = [p.id for p in pedidos_abiertos.values() if p.id]

            # Bulk: 1 query para detalles listos para entregar
            ready_by_pedido: dict[int, list] = {}
            if pedido_ids:
                for d in session.exec(
                    select(DetallePedido).where(
                        DetallePedido.pedido_id.in_(pedido_ids),
                        DetallePedido.impreso_cocina.is_(True),
                        DetallePedido.estado_produccion == EstadoProduccion.LISTO_PARA_ENTREGAR.value,
                    )
                ).all():
                    ready_by_pedido.setdefault(d.pedido_id, []).append(d)

            # Bulk: 1 query para conteo total de items por pedido
            items_total_by_pedido: dict[int, int] = {}
            if pedido_ids:
                for d in session.exec(
                    select(DetallePedido).where(DetallePedido.pedido_id.in_(pedido_ids))
                ).all():
                    items_total_by_pedido[d.pedido_id] = (
                        items_total_by_pedido.get(d.pedido_id, 0) + d.cantidad
                    )

            # Bulk: 1 query para nombres de mozos
            mozo_ids = {p.mozo_id for p in pedidos_abiertos.values() if p.mozo_id}
            mozos_map: dict[int, str] = {}
            if mozo_ids:
                for u in session.exec(
                    select(UsuarioFood).where(UsuarioFood.id.in_(list(mozo_ids)))
                ).all():
                    mozos_map[u.id or 0] = u.nombre

            # Bulk: reservas de hoy por mesa
            from datetime import date as _date_today
            hoy = _date_today.today()
            reservas_by_mesa: dict[int, str] = {}
            for rv in session.exec(
                select(Reserva).where(
                    Reserva.company_id == self._company_id(),
                    Reserva.fecha == hoy,
                    Reserva.estado.in_([
                        EstadoReserva.PENDIENTE.value,
                        EstadoReserva.CONFIRMADA.value,
                    ]),
                )
            ).all():
                if rv.mesa_id and rv.mesa_id not in reservas_by_mesa:
                    reservas_by_mesa[rv.mesa_id] = f"Reservada {rv.hora}"

            # Construir vistas y acumular correcciones de mesas stuck
            hay_stuck = bool(pedidos_expirados_ids)
            for mesa in mesas_db:
                pedido_abierto = pedidos_abiertos.get(mesa.id or 0)
                # Nivel 1: Auto-corregir mesa stuck (bidireccional)
                necesita_libre = (mesa.estado != EstadoMesa.LIBRE.value and pedido_abierto is None)
                necesita_ocupada = (mesa.estado == EstadoMesa.LIBRE.value and pedido_abierto is not None)
                if necesita_libre:
                    mesa.estado = EstadoMesa.LIBRE.value
                    mesa.updated_at = ahora
                    session.add(mesa)
                    hay_stuck = True
                elif necesita_ocupada:
                    mesa.estado = EstadoMesa.OCUPADA.value
                    mesa.updated_at = ahora
                    session.add(mesa)
                    hay_stuck = True
                total_abierto = _to_decimal(pedido_abierto.total if pedido_abierto else Decimal("0.00"))
                pid = (pedido_abierto.id or 0) if pedido_abierto else 0
                ready_details = ready_by_pedido.get(pid, [])
                items_listos_count = sum(d.cantidad for d in ready_details)
                tiene_items_listos = items_listos_count > 0
                items_total_count = items_total_by_pedido.get(pid, 0) if pedido_abierto else 0
                tiempo_abierto_texto = ""
                mozo_nombre = ""
                inactivo_min = 0
                if pedido_abierto is not None:
                    elapsed_min = max(0, int((ahora - pedido_abierto.created_at).total_seconds() // 60))
                    tiempo_abierto_texto = f"{elapsed_min} min"
                    inactivo_min = max(0, int((ahora - pedido_abierto.updated_at).total_seconds() // 60))
                    if pedido_abierto.mozo_id:
                        mozo_nombre = mozos_map.get(pedido_abierto.mozo_id, "")
                mesas_ui.append(MesaView(
                    id=mesa.id or 0,
                    numero=mesa.numero,
                    label=f"Mesa {mesa.numero}",
                    nombre=mesa.nombre or f"Mesa {mesa.numero}",
                    estado=mesa.estado,
                    estado_label=MESA_LABELS.get(mesa.estado, mesa.estado),
                    badge_bg=MESA_BADGE_BACKGROUNDS.get(mesa.estado, "#E5E7EB"),
                    badge_text=MESA_BADGE_TEXTS.get(mesa.estado, "#111827"),
                    capacidad=mesa.capacidad,
                    total_abierto=float(total_abierto),
                    total_abierto_texto=_money_text(total_abierto),
                    card_bg=MESA_CARD_BACKGROUNDS.get(mesa.estado, "#FFFFFF"),
                    card_border=(
                        READY_ALERT_BORDER if tiene_items_listos
                        else MESA_CARD_BORDERS.get(mesa.estado, "1px solid #E5E7EB")
                    ),
                    tiene_items_listos=tiene_items_listos,
                    items_listos_count=items_listos_count,
                    items_total_count=items_total_count,
                    tiempo_abierto_texto=tiempo_abierto_texto,
                    mozo_nombre=mozo_nombre,
                    sector=mesa.sector or "Salón",
                    reserva_texto=reservas_by_mesa.get(mesa.id or 0, ""),
                    inactivo_minutos=inactivo_min,
                ))
            if hay_stuck:
                session.commit()
        if _mesas_fingerprint(mesas_ui) != _mesas_fingerprint(self.mesas):
            self.mesas = mesas_ui
        self.ultima_actualizacion = ahora_local_pe().strftime("%H:%M:%S")
        if self.mesa_seleccionada_id and not any(m.id == self.mesa_seleccionada_id for m in self.mesas):
            self.mesa_seleccionada_id = 0
            self.carrito = []
            self.historial_pedido = []

    # ─── Carta ────────────────────────────────────────────────────────────────

    def cargar_menu(self) -> None:
        with self._tenant_session() as session:
            categorias_db = session.exec(
                select(Categoria).where(Categoria.company_id == self._company_id()).order_by(Categoria.orden, Categoria.nombre)
            ).all()
            productos_db = session.exec(
                select(Producto).where(Producto.company_id == self._company_id()).order_by(Producto.nombre)
            ).all()
            categorias_map = {c.id: c.nombre for c in categorias_db}
            conteo_por_categoria: dict[int, int] = {}
            for p in productos_db:
                conteo_por_categoria[p.categoria_id] = conteo_por_categoria.get(p.categoria_id, 0) + 1
            self.categorias = [
                CategoriaView(
                    id=c.id or 0,
                    nombre=c.nombre,
                    descripcion=c.descripcion or "",
                    orden=c.orden,
                    activa=c.activa,
                    productos_count=conteo_por_categoria.get(c.id or 0, 0),
                    emoji=_emoji_para_categoria(c.nombre),
                    estacion=c.estacion or "cocina",
                )
                for c in categorias_db
            ]
            productos_con_mods: set[int] = set()
            pids = [p.id for p in productos_db if p.id]
            if pids:
                for pg in session.exec(
                    select(ProductoGrupoModificador)
                    .where(ProductoGrupoModificador.producto_id.in_(pids))
                ).all():
                    productos_con_mods.add(pg.producto_id)
            margen_map: dict[int, float] = {}
            if pids:
                recetas = session.exec(
                    select(RecetaItem).where(RecetaItem.company_id == self._company_id())
                ).all()
                insumos = {
                    i.id: i for i in session.exec(
                        select(Insumo).where(Insumo.company_id == self._company_id())
                    ).all()
                }
                receta_por_prod: dict[int, list] = {}
                for r in recetas:
                    receta_por_prod.setdefault(r.producto_id, []).append(r)
                for prod in productos_db:
                    items_r = receta_por_prod.get(prod.id or 0)
                    if not items_r:
                        continue
                    costo = Decimal("0.00")
                    for item in items_r:
                        ins = insumos.get(item.insumo_id)
                        if ins:
                            costo += _to_decimal(ins.costo_unitario) * Decimal(str(item.cantidad))
                    precio_d = _to_decimal(prod.precio)
                    if precio_d > 0:
                        margen_map[prod.id or 0] = round(float((precio_d - costo) / precio_d * 100), 1)
            self.productos = [
                ProductoView(
                    id=p.id or 0,
                    categoria_id=p.categoria_id,
                    categoria_nombre=categorias_map.get(p.categoria_id, "General"),
                    nombre=p.nombre,
                    descripcion=p.descripcion or "",
                    precio=float(_to_decimal(p.precio)),
                    precio_texto=_money_text(p.precio),
                    disponible=p.disponible,
                    imagen_url=p.imagen_url or "",
                    emoji=p.emoji or _emoji_para_producto(p.nombre),
                    tiene_modificadores=(p.id or 0) in productos_con_mods,
                    margen_pct=margen_map.get(p.id or 0, -1.0),
                )
                for p in productos_db
            ]

    def seleccionar_categoria(self, categoria_id: int) -> None:
        self.categoria_activa_id = categoria_id

    def seleccionar_mostrador_categoria(self, categoria_id: int) -> None:
        self.mostrador_categoria_activa_id = categoria_id

    def set_mozos_filtro_sector(self, v: str) -> None:
        self.mozos_filtro_sector = v

    # ─── Mozos — Selección de mesa ────────────────────────────────────────────

    def seleccionar_mesa(self, mesa_id: int) -> None:
        self.mesa_seleccionada_id = mesa_id
        self._cargar_carrito_mesa(mesa_id)
        self._cargar_historial_mesa(mesa_id)
        self._cargar_cliente_mesa(mesa_id)
        mesa = next((m for m in self.mesas if m.id == mesa_id), None)
        alerta = (
            f" {mesa.items_listos_count} items listos para entregar."
            if mesa and mesa.tiene_items_listos else ""
        )
        _toast_msg = f"{self.mesa_seleccionada_label} seleccionada. {self.cantidad_items_carrito} items pendientes.{alerta}"
        self.busqueda_producto_modal = ""
        self.categoria_activa_id = 0
        self.modal_agregar_abierto = True
        return rx.toast.success(_toast_msg)

    def _cargar_cliente_mesa(self, mesa_id: int) -> None:
        self.mesa_cliente_busqueda = ""
        self.mesa_cliente_id = 0
        self.mesa_cliente_nombre = ""
        if not self.clientes_lista:
            self.cargar_clientes()
        with self._tenant_session() as session:
            pedido = _get_open_order(session, mesa_id, self._company_id())
            if pedido and pedido.cliente_id:
                cliente = session.get(Cliente, pedido.cliente_id)
                if cliente:
                    self.mesa_cliente_id = cliente.id or 0
                    self.mesa_cliente_nombre = cliente.nombre

    def vincular_cliente_mesa(self, nombre_input: str):
        self.mesa_cliente_busqueda = nombre_input
        nombre_parte = nombre_input.split(" — ")[0].strip()
        tel_parte = nombre_input.split(" — ")[1].strip() if " — " in nombre_input else ""
        cli = next(
            (c for c in self.clientes_lista
             if c.nombre == nombre_parte and (not tel_parte or c.telefono == tel_parte)),
            None,
        )
        if not cli:
            self.mesa_cliente_id = 0
            self.mesa_cliente_nombre = ""
            return
        if not self.mesa_seleccionada_id:
            return
        with self._tenant_session() as session:
            pedido = _get_open_order(session, self.mesa_seleccionada_id, self._company_id())
            if pedido:
                pedido.cliente_id = cli.id
                pedido.updated_at = _utcnow()
                session.add(pedido)
                session.commit()
        self.mesa_cliente_id = cli.id
        self.mesa_cliente_nombre = cli.nombre
        self.mesa_cliente_busqueda = ""
        return rx.toast.success(f"Cliente {cli.nombre} vinculado a la mesa")

    def desvincular_cliente_mesa(self):
        if not self.mesa_seleccionada_id:
            return
        with self._tenant_session() as session:
            pedido = _get_open_order(session, self.mesa_seleccionada_id, self._company_id())
            if pedido:
                pedido.cliente_id = None
                pedido.updated_at = _utcnow()
                session.add(pedido)
                session.commit()
        nombre = self.mesa_cliente_nombre
        self.mesa_cliente_id = 0
        self.mesa_cliente_nombre = ""
        self.mesa_cliente_busqueda = ""
        return rx.toast.warning(f"Cliente {nombre} desvinculado")

    def abrir_transfer_modal(self) -> None:
        self.transfer_modal_abierto = True

    def cerrar_transfer_modal(self) -> None:
        self.transfer_modal_abierto = False

    def set_transfer_modal_abierto(self, v: bool) -> None:
        self.transfer_modal_abierto = v

    # ─── Precuenta parcial desde mozos (OP-02) ──────────────────────────────

    def activar_precuenta_parcial(self) -> None:
        self.precuenta_parcial_modo = True
        items = list(self.historial_pedido)
        for i in range(len(items)):
            items[i] = items[i].model_copy(update={"sel_precuenta": False})
        self.historial_pedido = items

    def cancelar_precuenta_parcial(self) -> None:
        self.precuenta_parcial_modo = False
        items = list(self.historial_pedido)
        for i in range(len(items)):
            items[i] = items[i].model_copy(update={"sel_precuenta": False})
        self.historial_pedido = items

    def toggle_precuenta_item(self, idx: int) -> None:
        if not self.precuenta_parcial_modo:
            return
        items = list(self.historial_pedido)
        if 0 <= idx < len(items):
            items[idx] = items[idx].model_copy(update={"sel_precuenta": not items[idx].sel_precuenta})
            self.historial_pedido = items

    def seleccionar_todos_precuenta(self) -> None:
        items = list(self.historial_pedido)
        all_selected = all(it.sel_precuenta for it in items)
        for i in range(len(items)):
            items[i] = items[i].model_copy(update={"sel_precuenta": not all_selected})
        self.historial_pedido = items

    @rx.var
    def precuenta_parcial_subtotal(self) -> float:
        if not self.precuenta_parcial_modo:
            return 0.0
        return round(sum(it.subtotal_float for it in self.historial_pedido if it.sel_precuenta), 2)

    @rx.var
    def precuenta_parcial_subtotal_texto(self) -> str:
        return _money_text(self.precuenta_parcial_subtotal)

    @rx.var
    def precuenta_parcial_hay_seleccion(self) -> bool:
        return any(it.sel_precuenta for it in self.historial_pedido)

    def imprimir_precuenta_parcial(self):
        seleccionados = [it for it in self.historial_pedido if it.sel_precuenta]
        if not seleccionados:
            return rx.toast.error("Seleccione al menos un ítem.")
        ticket_lines = [
            TicketLine(
                name=it.nombre,
                quantity=it.cantidad,
                unit_price=float(_to_decimal(it.precio_unitario_texto.replace("S/ ", "").replace(",", ""))),
                subtotal=it.subtotal_float,
                note=it.nota,
            )
            for it in seleccionados
        ]
        total_parcial = sum(it.subtotal_float for it in seleccionados)
        mesa_label = self.mesa_seleccionada_label or "Mesa"
        pedido_id = 0
        attended_by = _actor_name(self.usuario_actual.nombre) if self.usuario_actual else ""
        if self.mesa_seleccionada_id:
            with self._tenant_session() as session:
                pedido = _get_open_order(session, self.mesa_seleccionada_id, self._company_id())
                if pedido:
                    pedido_id = pedido.id or 0
                    mozo = session.get(UsuarioFood, pedido.mozo_id) if pedido.mozo_id else None
                    if mozo:
                        attended_by = _actor_name(mozo.nombre)
        html_ticket = generate_precuenta_html(
            order_reference=mesa_label,
            pedido_id=pedido_id,
            items=ticket_lines,
            total=total_parcial,
            attended_by=attended_by,
            company_name=self.config_nombre_local or "TUWAYKIFOOD",
            company_ruc=self.config_ruc,
            company_sucursal=self.config_sucursal,
            company_direccion=self.config_direccion,
            company_telefono=self.config_telefono,
            descuento=0.0,
            paper_width_mm=self._ticket_paper_width_mm(),
        )
        self.precuenta_parcial_modo = False
        items = list(self.historial_pedido)
        for i in range(len(items)):
            items[i] = items[i].model_copy(update={"sel_precuenta": False})
        self.historial_pedido = items
        return rx.call_script(build_print_script(html_ticket))
        self.transfer_modal_abierto = v

    def transferir_a_mesa(self, mesa_destino_id: int) -> None:
        if not self.mesa_seleccionada_id or self.mesa_seleccionada_id == mesa_destino_id:
            return
        with self._tenant_session() as session:
            pedido_origen = _get_open_order(session, self.mesa_seleccionada_id, self._company_id())
            if pedido_origen is None:
                self.transfer_modal_abierto = False
                return rx.toast.error("No hay pedido abierto en la mesa origen.")
            mesa_origen = session.get(Mesa, self.mesa_seleccionada_id)
            mesa_destino = session.get(Mesa, mesa_destino_id)
            if mesa_destino is None:
                self.transfer_modal_abierto = False
                return rx.toast.error("Mesa destino no encontrada.")
            pedido_destino = _get_open_order(session, mesa_destino_id, self._company_id())
            now = _utcnow()
            if pedido_destino is not None:
                detalles = session.exec(
                    select(DetallePedido).where(DetallePedido.pedido_id == pedido_origen.id)
                ).all()
                for d in detalles:
                    d.pedido_id = pedido_destino.id
                    d.updated_at = now
                    session.add(d)
                pedido_origen.estado = EstadoPedido.CANCELADO.value
                pedido_origen.notas = f"Fusionado con pedido #{pedido_destino.id} (mesa {mesa_destino.numero})"
                pedido_origen.updated_at = now
                session.add(pedido_origen)
                _recalculate_order_total(session, pedido_destino)
                _sync_order_status(session, pedido_destino)
                label_destino = mesa_destino.nombre or f"Mesa {mesa_destino.numero}"
                msg = f"Pedido fusionado con {label_destino}."
            else:
                pedido_origen.mesa_id = mesa_destino_id
                pedido_origen.updated_at = now
                session.add(pedido_origen)
                mesa_destino.estado = EstadoMesa.OCUPADA.value
                mesa_destino.updated_at = now
                session.add(mesa_destino)
                label_destino = mesa_destino.nombre or f"Mesa {mesa_destino.numero}"
                msg = f"Pedido transferido a {label_destino}."
            if mesa_origen is not None:
                mesa_origen.estado = EstadoMesa.LIBRE.value
                mesa_origen.updated_at = now
                session.add(mesa_origen)
            session.commit()
        self.transfer_modal_abierto = False
        self.modal_agregar_abierto = False
        self.mesa_seleccionada_id = 0
        self.cargar_mesas()
        self.cargar_cocina()
        return rx.toast.success(msg)

    def _cargar_carrito_mesa(self, mesa_id: int) -> None:
        with self._tenant_session() as session:
            pedido = _get_open_order(session, mesa_id, self._company_id())
            if pedido is None:
                self.carrito = []
                return
            detalles = _get_unsent_details(session, pedido.id or 0)
            productos_map = {p.id: p for p in session.exec(select(Producto).where(Producto.company_id == self._company_id())).all()}
            items: list[CarritoItem] = []
            for d in detalles:
                import json as _json
                mods_texto = ""
                if d.modificadores_json:
                    try:
                        mods_list = _json.loads(d.modificadores_json)
                        mods_texto = ", ".join(
                            m.get("opcion", "") + (f" +S/{m['precio_extra']:.2f}" if m.get("precio_extra", 0) > 0 else "")
                            for m in mods_list
                        )
                    except Exception:
                        pass
                es_combo = bool(d.combo_items_json)
                if es_combo:
                    try:
                        combo_items = _json.loads(d.combo_items_json)
                        combo_nombre = "Combo: " + ", ".join(
                            f"{ci.get('cantidad', 1)}x {ci.get('nombre', '?')}" for ci in combo_items
                        )
                    except Exception:
                        combo_nombre = ""
                else:
                    combo_nombre = ""
                nombre_display = combo_nombre if es_combo else (productos_map[d.producto_id].nombre if d.producto_id in productos_map else f"Producto {d.producto_id}")
                items.append(CarritoItem(
                    producto_id=d.producto_id,
                    nombre=nombre_display,
                    cantidad=d.cantidad,
                    precio_unitario=float(_to_decimal(d.precio_unitario)),
                    subtotal=float(_to_decimal(d.subtotal)),
                    subtotal_texto=_money_text(d.subtotal),
                    nota=d.notas or "",
                    modificadores_texto=mods_texto,
                    modificadores_json=d.modificadores_json or "",
                    combo_items_json=d.combo_items_json or "",
                    es_combo=es_combo,
                ))
            self.carrito = items

    def _cargar_historial_mesa(self, mesa_id: int) -> None:
        with self._tenant_session() as session:
            pedido = _get_open_order(session, mesa_id, self._company_id())
            if pedido is None:
                self.historial_pedido = []
                self.mesa_atendida_por_nombre = ""
                self.nota_pedido_mesa = ""
                return
            detalles = session.exec(
                select(DetallePedido).where(
                    DetallePedido.pedido_id == pedido.id,
                    DetallePedido.impreso_cocina.is_(True),
                ).order_by(DetallePedido.enviado_cocina_at, DetallePedido.id)
            ).all()
            productos_map = {p.id: p for p in session.exec(select(Producto).where(Producto.company_id == self._company_id())).all()}
            usuarios_map = {u.id: u for u in session.exec(select(UsuarioFood).where(UsuarioFood.company_id == self._company_id())).all()}
            mozo = usuarios_map.get(pedido.mozo_id)
            self.mesa_atendida_por_nombre = _actor_name(mozo.nombre if mozo else "")
            self.nota_pedido_mesa = pedido.notas or ""
            historial: list[HistorialItem] = []
            for d in detalles:
                producto = productos_map.get(d.producto_id)
                preparado_por = usuarios_map.get(d.preparado_por_id)
                enviado_en = d.enviado_cocina_at or d.updated_at
                estado_produccion = d.estado_produccion or EstadoProduccion.PENDIENTE.value
                historial.append(HistorialItem(
                    detalle_id=d.id or 0,
                    nombre=producto.nombre if producto else f"Producto {d.producto_id}",
                    cantidad=d.cantidad,
                    precio_unitario_texto=_money_text(d.precio_unitario),
                    subtotal_texto=_money_text(d.subtotal),
                    subtotal_float=float(_to_decimal(d.subtotal)),
                    nota=d.notas or "",
                    enviado_en_texto=enviado_en.strftime("%H:%M"),
                    estado_clave=estado_produccion,
                    estado_label=PRODUCTION_LABELS.get(estado_produccion, estado_produccion),
                    estado_bg=PRODUCTION_BADGE_BACKGROUNDS.get(estado_produccion, "#334155"),
                    estado_color=PRODUCTION_BADGE_TEXTS.get(estado_produccion, "#334155"),
                    preparado_por_nombre=_actor_name(preparado_por.nombre if preparado_por else ""),
                    puede_entregar=(estado_produccion == EstadoProduccion.LISTO_PARA_ENTREGAR.value),
                    puede_cancelar=(estado_produccion == EstadoProduccion.PENDIENTE.value),
                ))
            self.historial_pedido = historial

    def agregar_producto(self, producto_id: int) -> None:
        if self.mesa_seleccionada_id == 0:
            return rx.toast.error("Seleccione una mesa antes de agregar productos.")
        prod_view = next((p for p in self.productos if p.id == producto_id), None)
        if prod_view and prod_view.tiene_modificadores:
            self._abrir_seleccion_modificadores(producto_id, prod_view.nombre, prod_view.precio)
            return
        with self._tenant_session() as session:
            mesa = session.get(Mesa, self.mesa_seleccionada_id)
            if mesa is None or mesa.company_id != self._company_id():
                return rx.toast.error("La mesa seleccionada ya no existe.")
            producto = session.get(Producto, producto_id)
            if producto is None or producto.company_id != self._company_id() or not producto.disponible:
                return rx.toast.error("Producto no disponible.")
            producto_nombre = producto.nombre
            pedido = _ensure_open_order(session, mesa, self._company_id(), mozo_id=(self.usuario_actual.id or None) if self.usuario_actual else None, sucursal_id=self._sucursal_id())
            detalle = session.exec(
                select(DetallePedido).where(
                    DetallePedido.pedido_id == pedido.id,
                    DetallePedido.producto_id == producto.id,
                    DetallePedido.impreso_cocina.is_(False),
                ).order_by(DetallePedido.id.desc())
            ).first()
            precio = _to_decimal(producto.precio)
            if detalle is None:
                detalle = DetallePedido(
                    company_id=self._company_id(),
                    pedido_id=pedido.id or 0,
                    producto_id=producto.id or 0,
                    cantidad=1,
                    precio_unitario=precio,
                    subtotal=precio,
                    estado_produccion=EstadoProduccion.PENDIENTE.value,
                    impreso_cocina=False,
                    impreso_caja=False,
                )
            else:
                detalle.cantidad += 1
                detalle.precio_unitario = precio
                detalle.subtotal = precio * detalle.cantidad
            session.add(detalle)
            _recalculate_order_total(session, pedido)
            mesa.estado = EstadoMesa.OCUPADA.value
            mesa.updated_at = _utcnow()
            session.add(mesa)
            session.commit()
        self._cargar_carrito_mesa(self.mesa_seleccionada_id)
        self._cargar_historial_mesa(self.mesa_seleccionada_id)
        self.cargar_mesas()
        return rx.toast.success(f"{producto_nombre} agregado a {self.mesa_seleccionada_label}.")

    def restar_producto(self, producto_id: int) -> None:
        if self.mesa_seleccionada_id == 0:
            return rx.toast.error("Seleccione una mesa antes de editar el carrito.")
        with self._tenant_session() as session:
            mesa = session.get(Mesa, self.mesa_seleccionada_id)
            if mesa is None:
                return rx.toast.error("La mesa seleccionada ya no existe.")
            pedido = _get_open_order(session, mesa.id or 0, self._company_id())
            if pedido is None:
                return rx.toast.error("No hay pedido abierto para esta mesa.")
            detalle = session.exec(
                select(DetallePedido).where(
                    DetallePedido.pedido_id == pedido.id,
                    DetallePedido.producto_id == producto_id,
                    DetallePedido.impreso_cocina.is_(False),
                ).order_by(DetallePedido.id.desc())
            ).first()
            if detalle is None:
                return rx.toast.error("Ese producto ya fue enviado o no existe en el carrito.")
            detalle.cantidad -= 1
            if detalle.cantidad <= 0:
                session.delete(detalle)
            else:
                detalle.subtotal = _to_decimal(detalle.precio_unitario) * detalle.cantidad
                session.add(detalle)
            self._finalize_cart_cleanup(session, pedido, mesa)
            session.commit()
        self._cargar_carrito_mesa(self.mesa_seleccionada_id)
        self._cargar_historial_mesa(self.mesa_seleccionada_id)
        self.cargar_mesas()
        return rx.toast.success("Carrito actualizado.")

    def _finalize_cart_cleanup(self, session, pedido: Pedido, mesa: Mesa) -> None:
        detalles_restantes = session.exec(
            select(DetallePedido).where(DetallePedido.pedido_id == pedido.id)
        ).all()
        if not detalles_restantes:
            session.delete(pedido)
            mesa.estado = EstadoMesa.LIBRE.value
            mesa.updated_at = _utcnow()
            session.add(mesa)
            return
        _recalculate_order_total(session, pedido)
        _sync_order_status(session, pedido)
        mesa.estado = EstadoMesa.OCUPADA.value
        mesa.updated_at = _utcnow()
        session.add(mesa)

    def limpiar_carrito(self) -> None:
        if self.mesa_seleccionada_id == 0:
            self.carrito = []
            return rx.toast.error("No hay mesa seleccionada.")
        with self._tenant_session() as session:
            mesa = session.get(Mesa, self.mesa_seleccionada_id)
            if mesa is None:
                return rx.toast.error("La mesa seleccionada ya no existe.")
            pedido = _get_open_order(session, mesa.id or 0, self._company_id())
            if pedido is None:
                self.carrito = []
                return rx.toast.error("No hay pedido abierto para limpiar.")
            for d in _get_unsent_details(session, pedido.id or 0):
                session.delete(d)
            self._finalize_cart_cleanup(session, pedido, mesa)
            session.commit()
        self._cargar_carrito_mesa(self.mesa_seleccionada_id)
        self._cargar_historial_mesa(self.mesa_seleccionada_id)
        self.cargar_mesas()
        return rx.toast.success("Items pendientes eliminados.")

    # ─── Notas ────────────────────────────────────────────────────────────────

    def set_mozos_tab(self, tab: str) -> None:
        self.mozos_tab_activa = tab

    def set_modal_agregar_abierto(self, value: bool) -> None:
        self.modal_agregar_abierto = value
        if not value:
            self.busqueda_producto_modal = ""

    def cerrar_modal_agregar(self) -> None:
        self.modal_agregar_abierto = False
        self.busqueda_producto_modal = ""
        self.precuenta_parcial_modo = False

    def set_busqueda_producto_modal(self, value: str) -> None:
        self.busqueda_producto_modal = value

    def abrir_nota_item(self, producto_id: int) -> None:
        item = next((i for i in self.carrito if i.producto_id == producto_id), None)
        self.nota_producto_activo_id = producto_id
        self.nota_input_temporal = item.nota if item else ""

    def set_nota_input_temporal(self, value: str) -> None:
        self.nota_input_temporal = str(value)[:120]

    def guardar_nota_carrito_item(self, producto_id: int) -> None:
        if self.mesa_seleccionada_id == 0:
            self.nota_producto_activo_id = 0
            return
        nota = self.nota_input_temporal.strip()
        with self._tenant_session() as session:
            pedido = _get_open_order(session, self.mesa_seleccionada_id, self._company_id())
            if pedido is None:
                self.nota_producto_activo_id = 0
                return
            detalle = session.exec(
                select(DetallePedido).where(
                    DetallePedido.pedido_id == pedido.id,
                    DetallePedido.producto_id == producto_id,
                    DetallePedido.impreso_cocina.is_(False),
                ).order_by(DetallePedido.id.desc())
            ).first()
            if detalle is None:
                self.nota_producto_activo_id = 0
                return rx.toast.error("El item ya fue enviado a cocina; no se puede editar.")
            detalle.notas = nota or None
            detalle.updated_at = _utcnow()
            session.add(detalle)
            session.commit()
        self.nota_producto_activo_id = 0
        self.nota_input_temporal = ""
        self._cargar_carrito_mesa(self.mesa_seleccionada_id)
        return rx.toast.success("Nota guardada." if nota else "Nota eliminada.")

    def cerrar_nota_item(self) -> None:
        self.nota_producto_activo_id = 0
        self.nota_input_temporal = ""

    def set_nota_pedido_mesa(self, value: str) -> None:
        self.nota_pedido_mesa = str(value)[:500]

    def guardar_nota_pedido_mesa(self) -> None:
        if self.mesa_seleccionada_id == 0:
            return
        nota = self.nota_pedido_mesa.strip()
        with self._tenant_session() as session:
            pedido = _get_open_order(session, self.mesa_seleccionada_id, self._company_id())
            if pedido is None:
                return
            pedido.notas = nota or None
            pedido.updated_at = _utcnow()
            session.add(pedido)
            session.commit()
        return rx.toast.success("Nota del pedido guardada." if nota else "Nota del pedido eliminada.")

    # ─── Enviar a cocina ─────────────────────────────────────────────────────

    def solicitar_cuenta(self) -> None:
        if self.mesa_seleccionada_id == 0:
            return rx.toast.error("Seleccione una mesa antes de solicitar cuenta.")
        if self.cantidad_items_carrito > 0:
            return rx.toast.error("Primero envía a cocina los ítems pendientes.")
        with self._tenant_session() as session:
            mesa = session.get(Mesa, self.mesa_seleccionada_id)
            if mesa is None:
                return rx.toast.error("La mesa seleccionada ya no existe.")
            pedido = _get_open_order(session, mesa.id or 0, self._company_id())
            if pedido is None or _to_decimal(pedido.total) <= 0:
                return rx.toast.error("No hay consumo pendiente en esa mesa.")
            mesa.estado = EstadoMesa.ESPERANDO_CUENTA.value
            mesa.updated_at = _utcnow()
            session.add(mesa)
            session.commit()
        self.cargar_mesas()
        return rx.toast.success(f"{self.mesa_seleccionada_label} marcada para cobrar.")

    def enviar_pedido(self) -> None:
        if self.mesa_seleccionada_id == 0:
            return rx.toast.error("Seleccione una mesa antes de enviar el pedido.")
        pedido_id = 0
        with self._tenant_session() as session:
            mesa = session.get(Mesa, self.mesa_seleccionada_id)
            if mesa is None:
                return rx.toast.error("La mesa seleccionada ya no existe.")
            pedido = _get_open_order(session, mesa.id or 0, self._company_id())
            if pedido is None:
                return rx.toast.error("No hay items pendientes para enviar.")
            if self.usuario_actual and pedido.mozo_id is None:
                pedido.mozo_id = self.usuario_actual.id or None
                pedido.updated_at = _utcnow()
                session.add(pedido)
            detalles_pendientes = _get_unsent_details(session, pedido.id or 0)
            if not detalles_pendientes:
                return rx.toast.error("No hay items nuevos pendientes de enviar.")
            errores_stock = _validar_stock_para_items(
                session, [(d.producto_id, d.cantidad) for d in detalles_pendientes], self._company_id()
            )
            if errores_stock:
                return rx.toast.error("Stock insuficiente — " + "; ".join(errores_stock))
            now = _utcnow()
            for d in detalles_pendientes:
                d.impreso_cocina = True
                d.enviado_cocina_at = now
                d.estado_produccion = EstadoProduccion.PENDIENTE.value
                session.add(d)
            _recalculate_order_total(session, pedido)
            _sync_order_status(session, pedido)
            mesa.estado = EstadoMesa.OCUPADA.value
            mesa.updated_at = now
            session.add(pedido)
            session.add(mesa)
            session.commit()
            pedido_id = pedido.id or 0
            mesa_label = mesa.nombre or f"Mesa {mesa.numero}"
        self.ultimo_pedido_id = pedido_id
        self._cargar_carrito_mesa(self.mesa_seleccionada_id)
        self._cargar_historial_mesa(self.mesa_seleccionada_id)
        self.cargar_mesas()
        self.cargar_cocina()
        return [
            rx.toast.success(f"Pedido #{pedido_id} enviado a cocina"),
            rx.call_script(_VIBRATE_JS),
        ]

    # ─── Cocina (KDS) ────────────────────────────────────────────────────────

    def set_cocina_filtro_estacion(self, v: str) -> None:
        self.cocina_filtro_estacion = v
        self.cargar_cocina()

    def cargar_cocina(self) -> None:
        with self._tenant_session() as session:
            cfg = session.exec(
                select(ConfigImpresora).where(ConfigImpresora.company_id == self._company_id())
            ).first()
            kds_umbral = cfg.kds_minutos_alerta if cfg else KITCHEN_DEMORADO_MINUTOS
            detalles = session.exec(
                select(DetallePedido).where(
                    DetallePedido.company_id == self._company_id(),
                    DetallePedido.impreso_cocina.is_(True),
                    DetallePedido.estado_produccion.in_(KITCHEN_VISIBLE_STATES),
                ).order_by(DetallePedido.enviado_cocina_at, DetallePedido.id)
            ).all()
            pedido_ids = {d.pedido_id for d in detalles}
            pedidos = {p.id: p for p in session.exec(select(Pedido).where(Pedido.id.in_(pedido_ids))).all()}
            mesas = {m.id: m for m in session.exec(select(Mesa).where(Mesa.company_id == self._company_id())).all()}
            usuarios = {u.id: u for u in session.exec(select(UsuarioFood).where(UsuarioFood.company_id == self._company_id())).all()}
            productos = {p.id: p for p in session.exec(select(Producto).where(Producto.company_id == self._company_id())).all()}
            categorias = {c.id: c for c in session.exec(select(Categoria).where(Categoria.company_id == self._company_id())).all()}
            filtro_est = self.cocina_filtro_estacion
            grupos: dict = {}
            for d in detalles:
                pedido = pedidos.get(d.pedido_id)
                if pedido is None or pedido.estado in (EstadoPedido.CANCELADO.value, EstadoPedido.COBRADO.value):
                    continue
                producto = productos.get(d.producto_id)
                if filtro_est:
                    cat = categorias.get(producto.categoria_id) if producto else None
                    item_estacion = (producto.estacion if producto and producto.estacion else None) or (cat.estacion if cat else EstacionCocina.COCINA.value)
                    if item_estacion != filtro_est:
                        continue
                marca = d.enviado_cocina_at or d.updated_at
                estado_produccion = d.estado_produccion or EstadoProduccion.PENDIENTE.value
                mozo = usuarios.get(pedido.mozo_id)
                mesa_id = pedido.mesa_id or 0
                key = (mesa_id, pedido.id or 0, estado_produccion)
                if key not in grupos:
                    grupos[key] = {
                        "pedido_id": pedido.id or 0,
                        "mesa_label": _pedido_kitchen_label(pedido, mesas),
                        "hora_texto": marca.strftime("%H:%M"),
                        "estado_produccion": estado_produccion,
                        "estado_label": PRODUCTION_LABELS.get(estado_produccion, estado_produccion),
                        "estado_bg": PRODUCTION_BADGE_BACKGROUNDS.get(estado_produccion, "#334155"),
                        "estado_color": PRODUCTION_BADGE_TEXTS.get(estado_produccion, "#334155"),
                        "mozo_nombre": _actor_name(mozo.nombre if mozo else ""),
                        "action_label": (
                            "▶ Iniciar preparación"
                            if estado_produccion == EstadoProduccion.PENDIENTE.value
                            else "↩ Volver a preparación"
                            if estado_produccion == EstadoProduccion.LISTO_PARA_ENTREGAR.value
                            else "✓ Todo listo"
                        ),
                        "accent_bg": KITCHEN_CARD_BACKGROUNDS.get(estado_produccion, "#0F172A"),
                        "accent_border": KITCHEN_CARD_BORDERS.get(estado_produccion, "#F59E0B"),
                        "detalle_ids": [],
                        "items_lines": [],
                        "items_ids": [],
                        "items_producto_ids": [],
                    }
                import json as _json
                producto = productos.get(d.producto_id)
                if d.combo_items_json:
                    try:
                        combo_items = _json.loads(d.combo_items_json)
                        combo_desc = " + ".join(f"{ci.get('cantidad', 1)}x {ci.get('nombre', '?')}" for ci in combo_items)
                        line = f"{d.cantidad} x COMBO [{combo_desc}]"
                    except Exception:
                        line = f"{d.cantidad} x Combo"
                else:
                    line = f"{d.cantidad} x {producto.nombre if producto else f'Producto {d.producto_id}'}"
                if d.modificadores_json:
                    try:
                        mods_list = _json.loads(d.modificadores_json)
                        mods_str = ", ".join(m.get("opcion", "") for m in mods_list if m.get("opcion"))
                        if mods_str:
                            line = f"{line} [{mods_str}]"
                    except Exception:
                        pass
                if d.notas:
                    line = f"{line} · Nota: {d.notas}"
                grupos[key]["items_lines"].append(line)
                grupos[key]["items_ids"].append(str(d.id or 0))
                grupos[key]["items_producto_ids"].append(str(d.producto_id or 0))
                grupos[key]["detalle_ids"].append(str(d.id or 0))
                grupos[key]["marca"] = marca
            ahora = _utcnow()
            for data in grupos.values():
                elapsed_seg = max(0, int((ahora - data["marca"]).total_seconds()))
                mins, segs = divmod(elapsed_seg, 60)
                if mins >= 99:
                    horas, mins_rest = divmod(mins, 60)
                    data["minutos_texto"] = f"{horas}h {mins_rest}min"
                else:
                    data["minutos_texto"] = f"{mins:02d}:{segs:02d} min"
                data["demorado"] = mins >= kds_umbral
                if data["demorado"]:
                    data["estado_label"] = "⚠ Demorado"
                    data["accent_border"] = KITCHEN_DEMORADO_COLOR
                    data["estado_bg"] = KITCHEN_DEMORADO_COLOR
                    data["estado_color"] = "#FFFFFF"
            nuevos_tickets = [
                CocinaTicketView(
                    pedido_id=data["pedido_id"],
                    mesa_label=data["mesa_label"],
                    hora_texto=data["hora_texto"],
                    estado_produccion=data["estado_produccion"],
                    estado_label=data["estado_label"],
                    estado_bg=data["estado_bg"],
                    estado_color=data["estado_color"],
                    mozo_nombre=data["mozo_nombre"],
                    action_label=data["action_label"],
                    accent_bg=data["accent_bg"],
                    accent_border=data["accent_border"],
                    detalle_ids_csv=",".join(data["detalle_ids"]),
                    items_lines=data["items_lines"],
                    items_ids=data["items_ids"],
                    items_producto_ids=data["items_producto_ids"],
                    bumpable=data["estado_produccion"] == EstadoProduccion.EN_PREPARACION.value,
                    minutos_texto=data["minutos_texto"],
                    demorado=data["demorado"],
                )
                for _, data in grupos.items()
            ]
            if _list_fingerprint(nuevos_tickets) != _list_fingerprint(self.tickets_cocina):
                self.tickets_cocina = nuevos_tickets

    def _transition_ticket_state(self, detalle_ids_csv: str, source_state: str, target_state: str, success_message: str, actor_user_id: int | None = None, actor_field_name: str | None = None) -> None:
        ids = [int(x) for x in detalle_ids_csv.split(",") if x.strip()]
        if not ids:
            return rx.toast.error("No se encontró el ticket de cocina.")
        with self._tenant_session() as session:
            detalles = session.exec(select(DetallePedido).where(DetallePedido.id.in_(ids))).all()
            actualizables = [d for d in detalles if d.impreso_cocina and d.estado_produccion == source_state]
            if not actualizables:
                return rx.toast.error("El ticket ya cambió de estado.")
            pedidos_afectados: set[int] = set()
            now = _utcnow()
            for d in actualizables:
                d.estado_produccion = target_state
                d.updated_at = now
                if actor_field_name and actor_user_id is not None:
                    setattr(d, actor_field_name, actor_user_id)
                session.add(d)
                pedidos_afectados.add(d.pedido_id)
            for pedido_id in pedidos_afectados:
                pedido = session.get(Pedido, pedido_id)
                if pedido is not None:
                    _sync_order_status(session, pedido)
            session.commit()
        self.cargar_cocina()
        self.cargar_mesas()
        if self.mesa_seleccionada_id:
            self._cargar_historial_mesa(self.mesa_seleccionada_id)
        return [rx.toast.success(success_message), rx.call_script(_VIBRATE_JS)]

    def iniciar_preparacion_ticket(self, detalle_ids_csv: str) -> None:
        self._transition_ticket_state(
            detalle_ids_csv, EstadoProduccion.PENDIENTE.value,
            EstadoProduccion.EN_PREPARACION.value, "Ticket movido a preparacion.",
        )

    def marcar_ticket_listo(self, detalle_ids_csv: str) -> None:
        self._transition_ticket_state(
            detalle_ids_csv, EstadoProduccion.EN_PREPARACION.value,
            EstadoProduccion.LISTO_PARA_ENTREGAR.value, "Pedido listo para entregar a salon.",
            actor_user_id=((self.usuario_actual.id or None) if self.usuario_actual else None),
            actor_field_name="preparado_por_id",
        )

    def devolver_ticket_a_preparacion(self, detalle_ids_csv: str) -> None:
        self._transition_ticket_state(
            detalle_ids_csv, EstadoProduccion.LISTO_PARA_ENTREGAR.value,
            EstadoProduccion.EN_PREPARACION.value, "Ticket devuelto a preparación.",
        )

    def bump_item_cocina(self, detalle_id: str) -> None:
        self._transition_ticket_state(
            detalle_id, EstadoProduccion.EN_PREPARACION.value,
            EstadoProduccion.LISTO_PARA_ENTREGAR.value, "Ítem marcado como listo.",
            actor_user_id=((self.usuario_actual.id or None) if self.usuario_actual else None),
            actor_field_name="preparado_por_id",
        )

    def marcar_86_cocina(self, producto_id: str):
        try:
            pid = int(producto_id)
        except (ValueError, TypeError):
            return
        if pid <= 0:
            return
        with self._tenant_session() as session:
            prod = session.get(Producto, pid)
            if prod is None or prod.company_id != self._company_id():
                return
            prod.disponible = False
            prod.updated_at = _utcnow()
            session.add(prod)
            registrar_auditoria(
                session, self._company_id(), "86_cocina",
                usuario_id=(self.usuario_actual.id or None) if self.usuario_actual else None,
                usuario_nombre=(self.usuario_actual.nombre if self.usuario_actual else ""),
                entidad="producto", entidad_id=pid,
                detalle={"nombre": prod.nombre},
            )
            session.commit()
            nombre = prod.nombre
        self.cargar_menu()
        return rx.toast.warning(f"{nombre} marcado como 86 (agotado)")

    def entregar_item_historial(self, detalle_id: int) -> None:
        with self._tenant_session() as session:
            detalle = session.get(DetallePedido, detalle_id)
            if detalle is None or not detalle.impreso_cocina:
                return rx.toast.error("El item indicado ya no existe.")
            if detalle.estado_produccion != EstadoProduccion.LISTO_PARA_ENTREGAR.value:
                return rx.toast.error("Ese ítem no está listo para entrega.")
            detalle.estado_produccion = EstadoProduccion.ENTREGADO_AL_CLIENTE.value
            detalle.updated_at = _utcnow()
            session.add(detalle)
            pedido = session.get(Pedido, detalle.pedido_id)
            if pedido is not None:
                _sync_order_status(session, pedido)
            session.commit()
        if self.mesa_seleccionada_id:
            self._cargar_historial_mesa(self.mesa_seleccionada_id)
        self.cargar_mesas()
        self.cargar_cocina()
        return rx.toast.success("Item entregado a la mesa.")

    def entregar_todos_items_listos(self) -> None:
        if not self.mesa_seleccionada_id:
            return
        with self._tenant_session() as session:
            pedidos = session.exec(
                select(Pedido).where(
                    Pedido.company_id == self._company_id(),
                    Pedido.mesa_id == self.mesa_seleccionada_id,
                    Pedido.estado.in_(OPEN_ORDER_STATES),
                )
            ).all()
            now = _utcnow()
            count = 0
            for pedido in pedidos:
                detalles = session.exec(
                    select(DetallePedido).where(
                        DetallePedido.pedido_id == pedido.id,
                        DetallePedido.estado_produccion == EstadoProduccion.LISTO_PARA_ENTREGAR.value,
                    )
                ).all()
                for d in detalles:
                    d.estado_produccion = EstadoProduccion.ENTREGADO_AL_CLIENTE.value
                    d.updated_at = now
                    session.add(d)
                    count += 1
                if detalles:
                    _sync_order_status(session, pedido)
            session.commit()
        if self.mesa_seleccionada_id:
            self._cargar_historial_mesa(self.mesa_seleccionada_id)
        self.cargar_mesas()
        self.cargar_cocina()
        if count:
            return rx.toast.success(f"{count} ítem(s) marcados como entregados")

    def cancelar_item_pedido(self, detalle_id: int) -> None:
        with self._tenant_session() as session:
            detalle = session.get(DetallePedido, detalle_id)
            if detalle is None or detalle.company_id != self._company_id():
                return rx.toast.error("El item indicado ya no existe.")
            if detalle.estado_produccion != EstadoProduccion.PENDIENTE.value:
                return rx.toast.error("Solo se pueden cancelar items aun pendientes en cocina.")
            pedido = session.get(Pedido, detalle.pedido_id)
            if pedido is None:
                return rx.toast.error("El pedido ya no existe.")
            nombre_item = ""
            producto = session.get(Producto, detalle.producto_id)
            if producto:
                nombre_item = producto.nombre
            session.delete(detalle)
            session.flush()
            _recalculate_order_total(session, pedido)
            _sync_order_status(session, pedido)
            session.commit()
        if self.mesa_seleccionada_id:
            self._cargar_historial_mesa(self.mesa_seleccionada_id)
            self._cargar_carrito_mesa(self.mesa_seleccionada_id)
        self.cargar_mesas()
        self.cargar_cocina()
        return rx.toast.success(f"Item '{nombre_item}' cancelado del pedido.")

    # ─── Caja — Flujo de cobro con método de pago ────────────────────────────

    def abrir_cobro_mesa(self, mesa_id: int) -> None:
        mesa = next((m for m in self.mesas if m.id == mesa_id), None)
        if mesa is None or mesa.estado == EstadoMesa.LIBRE.value or mesa.total_abierto <= 0:
            return rx.toast.error("Esa mesa no tiene consumo pendiente.")
        self.caja_cobro_mesa_id = mesa_id
        self.caja_cobro_pedido_id = 0
        self.caja_cobro_pedido_label = ""
        self.caja_cobro_total_override = 0.0
        self.caja_cobro_metodo = "efectivo"
        self.caja_cobro_propina = ""
        self.caja_cobro_propina_pct = 0
        self.caja_cobro_recargo = ""
        self.caja_cobro_recargo_concepto = "delivery"
        self.caja_cobro_efectivo_recibido = ""
        self.caja_cobro_error = ""
        self.caja_promo_aplicada_nombre = ""
        self.caja_promo_aplicada_texto = ""
        items_ui: list[CajaItemView] = []
        promo_ganadora = None
        with self._tenant_session() as session:
            pedido_abierto = _get_open_order(session, mesa_id, self._company_id())
            if pedido_abierto is not None:
                detalles = session.exec(
                    select(DetallePedido).where(
                        DetallePedido.pedido_id == pedido_abierto.id
                    ).order_by(DetallePedido.id)
                ).all()
                productos = {
                    p.id: p
                    for p in session.exec(
                        select(Producto).where(Producto.company_id == self._company_id())
                    ).all()
                }
                for d in detalles:
                    prod = productos.get(d.producto_id)
                    items_ui.append(CajaItemView(
                        detalle_id=d.id or 0,
                        producto_nombre=prod.nombre if prod else f"Producto {d.producto_id}",
                        cantidad=d.cantidad,
                        precio_unitario_texto=_money_text(_to_decimal(d.precio_unitario)),
                        subtotal_texto=_money_text(_to_decimal(d.subtotal)),
                        subtotal_float=float(_to_decimal(d.subtotal)),
                        notas=d.notas or "",
                    ))
                # Aplicación automática de la mejor promo vigente
                items_promo = [
                    ItemCobro(
                        producto_id=d.producto_id,
                        categoria_id=(
                            productos[d.producto_id].categoria_id
                            if d.producto_id in productos else 0
                        ),
                        cantidad=d.cantidad,
                        precio_unitario=_to_decimal(d.precio_unitario),
                    )
                    for d in detalles
                ]
                promos_activas = session.exec(
                    select(Promocion).where(
                        Promocion.company_id == self._company_id(),
                        Promocion.activa.is_(True),
                    )
                ).all()
                promo_ganadora = mejor_promo(
                    promos_activas, items_promo, ahora_local_pe(), solo_auto=True
                )
        self.caja_cobro_items = items_ui
        if promo_ganadora is not None:
            promo, descuento = promo_ganadora
            self.caja_cobro_descuento = f"{descuento:.2f}"
            self.caja_promo_aplicada_nombre = promo.nombre
            self.caja_promo_aplicada_texto = f"-{_money_text(descuento)}"
        else:
            self.caja_cobro_descuento = ""

    def cancelar_cobro(self) -> None:
        self.caja_cobrando = False
        self.caja_cobro_mesa_id = 0
        self.caja_cobro_pedido_id = 0
        self.caja_cobro_pedido_label = ""
        self.caja_cobro_total_override = 0.0
        self.caja_cobro_metodo = "efectivo"
        self.caja_cobro_propina = ""
        self.caja_cobro_propina_pct = 0
        self.caja_cobro_descuento = ""
        self.caja_cobro_descuento_es_pct = False
        self.caja_cobro_recargo = ""
        self.caja_cobro_recargo_concepto = "delivery"
        self.caja_cobro_efectivo_recibido = ""
        self.caja_cobro_cliente_nombre = ""
        self.caja_cobro_cliente_id = 0
        self.caja_cobro_error = ""
        self.caja_cobro_items = []
        self.caja_cobro_dividido = False
        self.caja_split_por_items = False
        self.caja_pago_staged_metodo = "efectivo"
        self.caja_pago_staged_monto = ""
        self.caja_pagos_staged = []
        self.caja_promo_aplicada_nombre = ""
        self.caja_promo_aplicada_texto = ""

    def set_caja_cobro_metodo(self, v: str) -> None:
        self.caja_cobro_metodo = v
        self.caja_cobro_efectivo_recibido = ""

    def set_caja_cobro_propina(self, v: str) -> None:
        self.caja_cobro_propina = v
        self.caja_cobro_propina_pct = 0

    def seleccionar_propina_pct(self, pct: int) -> None:
        if self.caja_cobro_propina_pct == pct:
            self.caja_cobro_propina_pct = 0
            self.caja_cobro_propina = ""
            return
        self.caja_cobro_propina_pct = pct
        base = self.caja_cobro_total_base
        self.caja_cobro_propina = f"{round(base * pct / 100, 2):.2f}"

    def set_caja_cobro_descuento(self, v: str) -> None:
        self.caja_cobro_descuento = v

    def toggle_descuento_modo(self) -> None:
        self.caja_cobro_descuento_es_pct = not self.caja_cobro_descuento_es_pct
        self.caja_cobro_descuento = ""

    def set_caja_cobro_recargo(self, v: str) -> None:
        self.caja_cobro_recargo = v

    def set_caja_cobro_recargo_concepto(self, v: str) -> None:
        self.caja_cobro_recargo_concepto = v

    def set_caja_cobro_efectivo_recibido(self, v: str) -> None:
        self.caja_cobro_efectivo_recibido = v

    # ─── Caja — Últimos cobros (reimpresión) ─────────────────────────────────

    def set_ultimos_cobros_visible(self, v: bool) -> None:
        self.ultimos_cobros_visible = v
        if v:
            self.cargar_ultimos_cobros()

    def toggle_ultimos_cobros(self) -> None:
        self.ultimos_cobros_visible = not self.ultimos_cobros_visible
        if self.ultimos_cobros_visible:
            self.cargar_ultimos_cobros()

    def cargar_ultimos_cobros(self) -> None:
        with self._tenant_session() as session:
            turno = get_turno_abierto(session, self._company_id(), self._sucursal_id())
            if turno is None:
                self.ultimos_cobros = []
                return
            pedidos = session.exec(
                select(Pedido)
                .where(
                    Pedido.company_id == self._company_id(),
                    Pedido.turno_caja_id == turno.id,
                    or_(
                        Pedido.pagado.is_(True),
                        Pedido.estado == EstadoPedido.COBRADO.value,
                    ),
                )
                .order_by(Pedido.cerrado_en.desc())
                .limit(20)
            ).all()
            mesas = {m.id: m for m in session.exec(select(Mesa).where(Mesa.company_id == self._company_id())).all()}
            result = []
            for p in pedidos:
                if p.tipo_pedido == TipoPedido.MOSTRADOR.value:
                    ref = f"Para llevar — {_actor_name(p.nombre_cliente) or 'Sin nombre'}"
                elif p.mesa_id and p.mesa_id in mesas:
                    m = mesas[p.mesa_id]
                    ref = m.nombre or f"Mesa {m.numero}"
                else:
                    ref = f"Pedido #{p.id}"
                detalles = session.exec(
                    select(DetallePedido).where(DetallePedido.pedido_id == p.id)
                ).all()
                productos = {pr.id: pr for pr in session.exec(
                    select(Producto).where(Producto.company_id == self._company_id())
                ).all()}
                items_txt = ", ".join(
                    f"{d.cantidad}x {productos[d.producto_id].nombre if d.producto_id in productos else '?'}"
                    for d in detalles[:3]
                )
                if len(detalles) > 3:
                    items_txt += f" +{len(detalles) - 3} más"
                metodo = (p.metodo_pago or "efectivo").capitalize()
                total_final = _to_decimal(p.total) - _to_decimal(p.descuento) + _to_decimal(p.propina) + _to_decimal(p.recargo)
                hora = p.cerrado_en.strftime("%H:%M") if p.cerrado_en else ""
                result.append(UltimoCobroView(
                    pedido_id=p.id or 0,
                    hora=hora,
                    referencia=ref,
                    detalle=f"{metodo} – {items_txt}",
                    total_texto=_money_text(total_final),
                    metodo_pago=metodo,
                ))
            self.ultimos_cobros = result

    def reimprimir_comprobante(self, pedido_id: int):
        if self.usuario_actual is not None and not (
            self.usuario_actual.rol == RolUsuario.ADMIN.value or self.usuario_actual.perm_reimprimir
        ):
            return rx.toast.error("No tiene permiso para reimprimir comprobantes.")
        with self._tenant_session() as session:
            pedido = session.get(Pedido, pedido_id)
            if pedido is None:
                return rx.toast.error("El pedido no existe.")
            detalles = session.exec(
                select(DetallePedido).where(DetallePedido.pedido_id == pedido.id)
            ).all()
            productos = {pr.id: pr for pr in session.exec(
                select(Producto).where(Producto.company_id == self._company_id())
            ).all()}
            ticket_lines = []
            for d in detalles:
                if d.combo_items_json:
                    import json as _json
                    try:
                        combo_items = _json.loads(d.combo_items_json)
                        name = "Combo: " + " + ".join(
                            f"{ci.get('cantidad', 1)}x {ci.get('nombre', '?')}" for ci in combo_items
                        )
                    except Exception:
                        name = "Combo"
                else:
                    name = productos[d.producto_id].nombre if d.producto_id in productos else f"Producto {d.producto_id}"
                ticket_lines.append(TicketLine(
                    name=name,
                    quantity=d.cantidad,
                    unit_price=float(_to_decimal(d.precio_unitario)),
                    subtotal=float(_to_decimal(d.subtotal)),
                    note=d.notas or "",
                ))
            if pedido.tipo_pedido == TipoPedido.MOSTRADOR.value:
                mesa_label = f"Para llevar — {_actor_name(pedido.nombre_cliente) or 'Sin nombre'}"
            elif pedido.mesa_id:
                mesa = session.get(Mesa, pedido.mesa_id)
                mesa_label = (mesa.nombre or f"Mesa {mesa.numero}") if mesa else f"Pedido #{pedido.id}"
            else:
                mesa_label = f"Pedido #{pedido.id}"
            usuarios = {u.id: u for u in session.exec(
                select(UsuarioFood).where(UsuarioFood.company_id == self._company_id())
            ).all()}
            mozo = usuarios.get(pedido.mozo_id)
            attended_by = _actor_name(mozo.nombre if mozo else "") or "Sin asignar"
            descuento = float(_to_decimal(pedido.descuento))
            propina = float(_to_decimal(pedido.propina))
            recargo = float(_to_decimal(pedido.recargo))
            recargo_concepto = pedido.recargo_concepto or ""
            total_final = float(_to_decimal(pedido.total)) - descuento + propina + recargo
        try:
            _pct_iva = float(self.config_porcentaje_iva or "18.0")
        except (ValueError, AttributeError):
            _pct_iva = 18.0
        html_ticket = generate_cashier_ticket_html(
            order_reference=mesa_label,
            pedido_id=pedido_id,
            items=ticket_lines,
            total=total_final,
            attended_by=attended_by,
            company_name=self.config_nombre_local or "TUWAYKIFOOD",
            company_ruc=self.config_ruc,
            company_sucursal=self.config_sucursal,
            company_direccion=self.config_direccion,
            company_telefono=self.config_telefono,
            descuento=descuento,
            propina=propina,
            recargo=recargo,
            recargo_concepto=recargo_concepto,
            metodo_pago=(pedido.metodo_pago or "efectivo"),
            mensaje_footer=self.config_mensaje_ticket,
            mostrar_iva=self.config_mostrar_iva,
            nombre_impuesto=self.config_nombre_impuesto or "IGV",
            porcentaje_iva=_pct_iva,
            paper_width_mm=self._ticket_paper_width_mm(),
        )
        return rx.call_script(build_print_script(html_ticket))

    # ─── Caja — Cobro dividido / pago mixto ──────────────────────────────────

    @rx.var
    def caja_pagos_total(self) -> float:
        return round(sum(p.monto for p in self.caja_pagos_staged), 2)

    @rx.var
    def caja_pagos_restante(self) -> float:
        return round(max(self.caja_cobro_total_final - self.caja_pagos_total, 0.0), 2)

    @rx.var
    def caja_pagos_restante_texto(self) -> str:
        return _money_text(self.caja_pagos_restante)

    @rx.var
    def caja_pagos_cubierto(self) -> bool:
        return bool(self.caja_pagos_staged) and self.caja_pagos_total >= round(
            self.caja_cobro_total_final, 2
        )

    @rx.var
    def caja_pagos_vuelto_texto(self) -> str:
        vuelto = round(self.caja_pagos_total - self.caja_cobro_total_final, 2)
        return _money_text(vuelto) if vuelto > 0 else ""

    @rx.var
    def caja_pagos_tiene_fiado(self) -> bool:
        return any(p.metodo == "fiado" for p in self.caja_pagos_staged)

    # ─── Split por ítems (CJ-02 + BE-06) ─────────────────────────────────────

    @rx.var
    def caja_split_subtotal_sel(self) -> float:
        if not self.caja_split_por_items:
            return 0.0
        return round(sum(
            item.subtotal_float for item in self.caja_cobro_items if item.seleccionado
        ), 2)

    @rx.var
    def caja_split_subtotal_sel_texto(self) -> str:
        return _money_text(self.caja_split_subtotal_sel)

    @rx.var
    def caja_split_hay_seleccion(self) -> bool:
        return any(item.seleccionado for item in self.caja_cobro_items)

    @rx.var
    def caja_split_todos_asignados(self) -> bool:
        if not self.caja_split_por_items or not self.caja_cobro_items:
            return False
        return all(item.asignado_pago > 0 for item in self.caja_cobro_items)

    def set_caja_cobro_dividido(self, v: bool) -> None:
        self.caja_cobro_dividido = bool(v)
        self.caja_split_por_items = False
        self._reset_split_items()
        self.caja_pagos_staged = []
        self.caja_pago_staged_metodo = "efectivo"
        self.caja_pago_staged_monto = ""
        self.caja_cobro_error = ""

    def set_caja_split_por_items(self, v: bool) -> None:
        self.caja_split_por_items = bool(v)
        self._reset_split_items()
        self.caja_pagos_staged = []
        self.caja_pago_staged_monto = ""
        self.caja_cobro_error = ""

    def _reset_split_items(self) -> None:
        items = list(self.caja_cobro_items)
        for i, item in enumerate(items):
            items[i] = item.model_copy(update={"seleccionado": False, "asignado_pago": 0})
        self.caja_cobro_items = items

    def toggle_split_item_sel(self, idx: int) -> None:
        items = list(self.caja_cobro_items)
        if 0 <= idx < len(items):
            item = items[idx]
            if item.asignado_pago == 0:
                items[idx] = item.model_copy(update={"seleccionado": not item.seleccionado})
                self.caja_cobro_items = items

    def seleccionar_todos_restantes(self) -> None:
        items = list(self.caja_cobro_items)
        for i, item in enumerate(items):
            if item.asignado_pago == 0:
                items[i] = item.model_copy(update={"seleccionado": True})
        self.caja_cobro_items = items

    def set_caja_pago_staged_metodo(self, v: str) -> None:
        self.caja_pago_staged_metodo = v

    def set_caja_pago_staged_monto(self, v: str) -> None:
        self.caja_pago_staged_monto = v

    def agregar_pago_staged(self) -> None:
        import json as _json
        self.caja_cobro_error = ""
        labels = {"efectivo": "Efectivo", "tarjeta": "Tarjeta", "qr": "QR / Yape", "fiado": "Fiado / CC"}
        metodo = self.caja_pago_staged_metodo or "efectivo"

        if self.caja_split_por_items:
            items = list(self.caja_cobro_items)
            sel_indices = [i for i, it in enumerate(items) if it.seleccionado]
            if not sel_indices:
                self.caja_cobro_error = "Seleccione al menos un ítem."
                return
            monto = round(sum(items[i].subtotal_float for i in sel_indices), 2)
            if monto <= 0:
                self.caja_cobro_error = "El subtotal de la selección es cero."
                return
            items_desc = " + ".join(
                f"{items[i].cantidad}x {items[i].producto_nombre}" for i in sel_indices
            )
            pago_num = len(self.caja_pagos_staged) + 1
            self.caja_pagos_staged.append(PagoStagedView(
                metodo=metodo,
                metodo_label=labels.get(metodo, metodo),
                monto=monto,
                monto_texto=_money_text(monto),
                items_indices_json=_json.dumps(sel_indices),
                items_texto=items_desc,
            ))
            for i in sel_indices:
                items[i] = items[i].model_copy(update={"seleccionado": False, "asignado_pago": pago_num})
            self.caja_cobro_items = items
            self.caja_pago_staged_monto = ""
            return

        raw = (self.caja_pago_staged_monto or "").replace(",", ".").strip()
        if raw:
            try:
                monto = round(float(raw), 2)
            except ValueError:
                self.caja_cobro_error = "Monto de pago inválido."
                return
        else:
            monto = self.caja_pagos_restante
        if monto <= 0:
            self.caja_cobro_error = "El pago debe ser mayor a cero."
            return
        self.caja_pagos_staged.append(PagoStagedView(
            metodo=metodo,
            metodo_label=labels.get(metodo, metodo),
            monto=monto,
            monto_texto=_money_text(monto),
        ))
        self.caja_pago_staged_monto = ""

    def quitar_pago_staged(self, idx: int) -> None:
        import json as _json
        if 0 <= idx < len(self.caja_pagos_staged):
            pagos = list(self.caja_pagos_staged)
            removed = pagos.pop(idx)
            self.caja_pagos_staged = pagos
            if self.caja_split_por_items and removed.items_indices_json:
                try:
                    released = _json.loads(removed.items_indices_json)
                except Exception:
                    released = []
                items = list(self.caja_cobro_items)
                for i in released:
                    if 0 <= i < len(items):
                        items[i] = items[i].model_copy(update={"asignado_pago": 0})
                for p_idx, pago in enumerate(self.caja_pagos_staged):
                    if pago.items_indices_json:
                        try:
                            p_indices = _json.loads(pago.items_indices_json)
                        except Exception:
                            continue
                        for i in p_indices:
                            if 0 <= i < len(items):
                                items[i] = items[i].model_copy(update={"asignado_pago": p_idx + 1})
                self.caja_cobro_items = items

    # ─── Anulación auditada de pedidos y ventas ──────────────────────────────

    def set_anulacion_motivo(self, v: str) -> None:
        self.anulacion_motivo = v

    def set_anulacion_modal_visible(self, v: bool) -> None:
        self.anulacion_modal_visible = bool(v)

    def set_reversion_motivo(self, v: str) -> None:
        self.reversion_motivo = v

    def set_reversion_modal_visible(self, v: bool) -> None:
        if not v:
            self.cancelar_reversion()
        self.reversion_modal_visible = bool(v)

    def cancelar_anulacion(self) -> None:
        self.anulacion_modal_visible = False
        self.anulacion_pedido_id = 0
        self.anulacion_motivo = ""
        self.anulacion_error = ""

    def liberar_mesa_sin_cobro(self) -> None:
        """Mozo libera la mesa actual (cliente se fue sin pagar)."""
        mesa_id = self.mesa_seleccionada_id
        if not mesa_id:
            return
        with self._tenant_session() as session:
            pedido = _get_open_order(session, mesa_id, self._company_id())
            if pedido is None:
                return rx.toast.error("No hay pedido abierto para esa mesa.")
            mesa = session.get(Mesa, mesa_id)
            referencia = (mesa.nombre or f"Mesa {mesa.numero}") if mesa else f"Mesa {mesa_id}"
            self.anulacion_pedido_id = pedido.id or 0
            self.anulacion_referencia = f"{referencia} — pedido #{pedido.id}"
        self.modal_agregar_abierto = False
        self.anulacion_es_venta = False
        self.anulacion_motivo = ""
        self.anulacion_error = ""
        self.anulacion_modal_visible = True

    def abrir_anulacion_pedido_abierto(self, mesa_id: int) -> None:
        """Anular el pedido abierto de una mesa (desde Caja) — libera la mesa."""
        if self.usuario_actual is None or (
            self.usuario_actual.rol != RolUsuario.ADMIN.value
            and not self.usuario_actual.perm_anular
        ):
            return rx.toast.error("No tienes permiso para anular pedidos. Solicítalo al administrador.")
        with self._tenant_session() as session:
            pedido = _get_open_order(session, mesa_id, self._company_id())
            if pedido is None:
                return rx.toast.error("No hay pedido abierto para esa mesa.")
            mesa = session.get(Mesa, mesa_id)
            referencia = (mesa.nombre or f"Mesa {mesa.numero}") if mesa else f"Mesa {mesa_id}"
            self.anulacion_pedido_id = pedido.id or 0
            self.anulacion_referencia = f"{referencia} — pedido #{pedido.id}"
        self.anulacion_es_venta = False
        self.anulacion_motivo = ""
        self.anulacion_error = ""
        self.anulacion_modal_visible = True

    def abrir_anulacion_venta(self, pedido_id: int) -> None:
        """Anular una venta ya cobrada (desde Reportes) — solo Admin."""
        if self.usuario_actual is None or self.usuario_actual.rol != RolUsuario.ADMIN.value:
            return rx.toast.error("Solo el administrador puede anular ventas cobradas.")
        self.anulacion_pedido_id = pedido_id
        self.anulacion_referencia = f"Venta #{pedido_id}"
        self.anulacion_es_venta = True
        self.anulacion_motivo = ""
        self.anulacion_error = ""
        self.anulacion_modal_visible = True

    def confirmar_anulacion(self) -> None:
        self.anulacion_error = ""
        if self.anulacion_pedido_id == 0:
            return
        motivo = (self.anulacion_motivo or "").strip()
        if len(motivo) < 3:
            self.anulacion_error = "Indica el motivo de la anulación (mínimo 3 caracteres)."
            return
        fiado_revertido = Decimal("0.00")
        try:
            with self._tenant_session() as session:
                pedido = session.get(Pedido, self.anulacion_pedido_id)
                if pedido is None:
                    self.anulacion_error = "El pedido ya no existe."
                    return
                usuario_id = (self.usuario_actual.id or None) if self.usuario_actual else None
                if self.anulacion_es_venta:
                    fiado_revertido = anular_venta_cobrada(
                        session, pedido, usuario_id, self.anulacion_motivo
                    )
                else:
                    anular_pedido_abierto(session, pedido, usuario_id, self.anulacion_motivo)
                session.commit()
        except ValueError as exc:
            self.anulacion_error = str(exc)
            return
        referencia = self.anulacion_referencia
        es_venta = self.anulacion_es_venta
        self.cancelar_anulacion()
        if self.caja_cobro_mesa_id:
            self.cancelar_cobro()
        self.cargar_mesas()
        self.cargar_cocina()
        fiado_txt = (
            f" Fiado revertido: {_money_text(fiado_revertido)}."
            if fiado_revertido > 0 else ""
        )
        _toast_msg = f"{referencia} anulado. Motivo registrado.{fiado_txt}"
        if es_venta:
            return [rx.toast.success(_toast_msg), ReportesState.cargar_historial_ventas, ReportesState.cargar_dashboard]
        return rx.toast.success(_toast_msg)

    def abrir_reversion_cobro(self, pedido_id: int) -> None:
        if self.usuario_actual is None:
            return
        with self._tenant_session() as session:
            pedido = session.get(Pedido, pedido_id)
            if pedido is None or pedido.company_id != self._company_id():
                return rx.toast.error("El pedido no existe.")
            if pedido.estado != EstadoPedido.COBRADO.value:
                return rx.toast.error("Solo se pueden anular cobros ya confirmados.")
            turno = get_turno_abierto(session, self._company_id(), self._sucursal_id())
            if turno is None or pedido.turno_caja_id != turno.id:
                return rx.toast.error("Solo se pueden anular cobros del turno actual.")
            ref = f"Pedido #{pedido.id}"
            if pedido.mesa_id:
                mesa = session.get(Mesa, pedido.mesa_id)
                if mesa:
                    ref = f"{mesa.nombre or f'Mesa {mesa.numero}'} — pedido #{pedido.id}"
        self.reversion_pedido_id = pedido_id
        self.reversion_referencia = ref
        self.reversion_motivo = ""
        self.reversion_error = ""
        self.reversion_modal_visible = True

    def cancelar_reversion(self) -> None:
        self.reversion_modal_visible = False
        self.reversion_pedido_id = 0
        self.reversion_motivo = ""
        self.reversion_error = ""

    def confirmar_reversion_cobro(self) -> None:
        self.reversion_error = ""
        motivo = (self.reversion_motivo or "").strip()
        if len(motivo) < 3:
            self.reversion_error = "Indica el motivo de la anulación (mínimo 3 caracteres)."
            return
        pedido_id = self.reversion_pedido_id
        if pedido_id == 0:
            return
        if self.usuario_actual is None:
            return
        fiado_revertido = Decimal("0.00")
        try:
            with self._tenant_session() as session:
                pedido = session.get(Pedido, pedido_id)
                if pedido is None or pedido.company_id != self._company_id():
                    self.reversion_error = "El pedido ya no existe."
                    return
                if pedido.estado != EstadoPedido.COBRADO.value:
                    self.reversion_error = "Solo se pueden anular cobros ya confirmados."
                    return
                turno = get_turno_abierto(session, self._company_id(), self._sucursal_id())
                if turno is None or pedido.turno_caja_id != turno.id:
                    self.reversion_error = "Solo se pueden anular cobros del turno actual."
                    return
                usuario_id = (self.usuario_actual.id or None) if self.usuario_actual else None
                fiado_revertido = anular_venta_cobrada(
                    session, pedido, usuario_id, motivo
                )
                session.commit()
        except ValueError as exc:
            self.reversion_error = str(exc)
            return
        self.cancelar_reversion()
        self.cargar_mesas()
        self.cargar_cocina()
        self.cargar_ultimos_cobros()
        if self.caja_cobro_mesa_id:
            self.cancelar_cobro()
        fiado_txt = f" Fiado revertido: {_money_text(fiado_revertido)}." if fiado_revertido > 0 else ""
        return rx.toast.success(f"Venta #{pedido_id} anulada. Queda registrada en reportes.{fiado_txt}")

    def confirmar_cobro(self) -> None:
        if self.caja_cobrando:
            return
        self.caja_cobrando = True
        self.caja_cobro_error = ""
        es_mostrador = self.caja_cobro_pedido_id > 0
        objetivo_mesa = self.caja_cobro_mesa_id
        objetivo_pedido = self.caja_cobro_pedido_id

        if not es_mostrador and objetivo_mesa == 0:
            self.caja_cobro_error = "No hay mesa seleccionada para cobrar."
            self.caja_cobrando = False
            return

        metodo = self.caja_cobro_metodo or "efectivo"
        try:
            propina_raw = float(self.caja_cobro_propina.replace(",", ".").strip())
            propina = Decimal(str(round(propina_raw, 2))) if propina_raw > 0 else Decimal("0.00")
        except (ValueError, AttributeError, InvalidOperation):
            propina = Decimal("0.00")
        try:
            desc_raw = float(self.caja_cobro_descuento.replace(",", ".").strip())
            desc_raw = max(desc_raw, 0.0)
            if self.caja_cobro_descuento_es_pct:
                desc_raw = min(desc_raw, 100.0)
                desc_raw = float(Decimal(str(self.caja_cobro_total_base)) * Decimal(str(desc_raw)) / 100)
            descuento = Decimal(str(round(desc_raw, 2)))
        except (ValueError, AttributeError, InvalidOperation):
            descuento = Decimal("0.00")
        try:
            rec_raw = float(self.caja_cobro_recargo.replace(",", ".").strip())
            recargo = Decimal(str(round(max(rec_raw, 0.0), 2)))
        except (ValueError, AttributeError, InvalidOperation):
            recargo = Decimal("0.00")
        recargo_concepto = (self.caja_cobro_recargo_concepto or "").strip() or None

        pedido_id = 0
        mesa_label = ""
        attended_by = ""
        total_base = Decimal("0.00")
        ticket_lines: list[TicketLine] = []
        with self._tenant_session() as session:
            if es_mostrador:
                mesa = None
                pedido = session.get(Pedido, objetivo_pedido)
                if pedido is None:
                    self.caja_cobrando = False
                    return rx.toast.error("El pedido ya no existe.")
                if pedido.pagado:
                    self.caja_cobrando = False
                    return rx.toast.error("Este pedido ya fue cobrado.")
            else:
                mesa = session.get(Mesa, objetivo_mesa)
                if mesa is None:
                    self.caja_cobrando = False
                    return rx.toast.error("La mesa indicada ya no existe.")
                pedido = _get_open_order(session, mesa.id or 0, self._company_id())
                if pedido is None:
                    self.caja_cobrando = False
                    return rx.toast.error("No hay pedido abierto para esa mesa.")
            turno = get_turno_abierto(session, self._company_id(), self._sucursal_id())
            if turno is None:
                self.caja_cobro_error = "No hay turno de caja abierto. Abre el turno antes de cobrar."
                self.caja_cobrando = False
                return
            detalles = session.exec(select(DetallePedido).where(DetallePedido.pedido_id == pedido.id)).all()
            prod_ids = {d.producto_id for d in detalles}
            productos = {p.id: p for p in session.exec(select(Producto).where(Producto.id.in_(list(prod_ids)))).all()} if prod_ids else {}
            ticket_lines = []
            for d in detalles:
                if d.combo_items_json:
                    import json as _json
                    try:
                        combo_items = _json.loads(d.combo_items_json)
                        combo_desc = "Combo: " + " + ".join(
                            f"{ci.get('cantidad', 1)}x {ci.get('nombre', '?')}" for ci in combo_items
                        )
                    except Exception:
                        combo_desc = "Combo"
                    name = combo_desc
                else:
                    name = productos[d.producto_id].nombre if d.producto_id in productos else f"Producto {d.producto_id}"
                ticket_lines.append(TicketLine(
                    name=name,
                    quantity=d.cantidad,
                    unit_price=float(_to_decimal(d.precio_unitario)),
                    subtotal=float(_to_decimal(d.subtotal)),
                    note=d.notas or "",
                ))
            if es_mostrador:
                attended_by = _actor_name(
                    self.usuario_actual.nombre if self.usuario_actual else ""
                ) or "Sin asignar"
            else:
                usuarios = {u.id: u for u in session.exec(select(UsuarioFood).where(UsuarioFood.company_id == self._company_id())).all()}
                mozo = usuarios.get(pedido.mozo_id)
                attended_by = _actor_name(
                    mozo.nombre if mozo else (self.usuario_actual.nombre if self.usuario_actual else "")
                ) or "Sin asignar"

            total_base = _to_decimal(pedido.total)
            if descuento > total_base:
                self.caja_cobro_error = f"El descuento ({_money_text(descuento)}) no puede superar el total ({_money_text(total_base)})."
                return
            import json as _json
            if self.caja_cobro_dividido:
                if not self.caja_pagos_staged:
                    self.caja_cobro_error = "Agrega al menos un pago."
                    return
                if self.caja_split_por_items and not all(
                    it.asignado_pago > 0 for it in self.caja_cobro_items
                ):
                    self.caja_cobro_error = "Asigna todos los ítems antes de confirmar."
                    return
                total_final = max(total_base - descuento + propina + recargo, Decimal("0.00"))
                pagos_lista = [
                    (p.metodo, Decimal(str(round(p.monto, 2))))
                    for p in self.caja_pagos_staged
                ]
            else:
                if metodo == "fiado":
                    propina = Decimal("0.00")
                total_final = max(total_base - descuento + propina + recargo, Decimal("0.00"))
                pagos_lista = [(metodo, total_final)] if total_final > 0 else []
            resultado_pagos = None
            if pagos_lista:
                try:
                    resultado_pagos = validar_pagos(total_final, pagos_lista)
                except ValueError as exc:
                    self.caja_cobro_error = str(exc)
                    return
            total_fiado = resultado_pagos.total_fiado if resultado_pagos else Decimal("0.00")
            if total_fiado > 0 and self.caja_cobro_cliente_id <= 0:
                self.caja_cobro_error = "Seleccione el cliente para registrar el fiado."
                return
            now = _utcnow()
            for d in session.exec(
                select(DetallePedido).where(
                    DetallePedido.pedido_id == pedido.id,
                    DetallePedido.estado_produccion != EstadoProduccion.ENTREGADO_AL_CLIENTE.value,
                )
            ).all():
                d.estado_produccion = EstadoProduccion.ENTREGADO_AL_CLIENTE.value
                session.add(d)
            if self.usuario_actual:
                pedido.cajero_id = self.usuario_actual.id or None
            pedido.pagado = total_fiado == 0
            pedido.estado = EstadoPedido.COBRADO.value
            pedido.cerrado_en = now
            pedido.updated_at = now
            pedido.metodo_pago = metodo_pago_resumen(pagos_lista) if pagos_lista else metodo
            pedido.turno_caja_id = turno.id
            pedido.propina = propina
            pedido.descuento = descuento
            pedido.recargo = recargo
            pedido.recargo_concepto = recargo_concepto if recargo > 0 else None
            if self.caja_cobro_cliente_id > 0:
                pedido.cliente_id = self.caja_cobro_cliente_id
            session.add(pedido)
            if mesa is not None:
                mesa.estado = EstadoMesa.LIBRE.value
                mesa.updated_at = now
                session.add(mesa)
            _descontar_stock_por_pedido(session, pedido.id or 0, self._company_id())
            if total_fiado > 0:
                fiado_label = (
                    f"Fiado pedido #{pedido.id}"
                    if es_mostrador
                    else f"Fiado mesa {mesa.nombre or str(mesa.numero)}"
                )
                try:
                    self._registrar_cargo_cc(
                        session,
                        self.caja_cobro_cliente_id,
                        total_fiado,
                        pedido.id,
                        fiado_label,
                    )
                except ValueError as exc:
                    self.caja_cobro_error = str(exc)
                    return
            if resultado_pagos is not None:
                split_det = None
                if self.caja_split_por_items:
                    split_det = []
                    items_snap = list(self.caja_cobro_items)
                    for p in self.caja_pagos_staged:
                        if p.items_indices_json:
                            try:
                                indices = _json.loads(p.items_indices_json)
                                det_ids = [items_snap[i].detalle_id for i in indices if 0 <= i < len(items_snap)]
                            except Exception:
                                det_ids = []
                            split_det.append(_json.dumps(det_ids))
                        else:
                            split_det.append("")
                registrar_pagos_pedido(
                    session,
                    pedido,
                    turno.id,
                    (self.usuario_actual.id or None) if self.usuario_actual else None,
                    pagos_lista,
                    resultado_pagos,
                    split_detalles=split_det,
                )
            metodo_final = pedido.metodo_pago or metodo
            registrar_auditoria(
                session, self._company_id(), "cobro",
                usuario_id=(self.usuario_actual.id or None) if self.usuario_actual else None,
                usuario_nombre=(self.usuario_actual.nombre if self.usuario_actual else ""),
                entidad="pedido", entidad_id=pedido.id,
                detalle={"total": str(total_final), "metodo": metodo_final,
                         "descuento": str(descuento), "propina": str(propina)},
            )
            if self.caja_cupon_id_aplicado > 0:
                try:
                    redimir_cupon(session, self.caja_cupon_id_aplicado)
                except Exception:
                    pass
            session.commit()
            pedido_id = pedido.id or 0
            if es_mostrador:
                cliente_n = _actor_name(pedido.nombre_cliente) or "Sin nombre"
                mesa_label = f"Para llevar — {cliente_n}"
            else:
                mesa_label = mesa.nombre or f"Mesa {mesa.numero}"

        if not es_mostrador and self.mesa_seleccionada_id == objetivo_mesa:
            self.mesa_seleccionada_id = 0
            self.carrito = []
            self.historial_pedido = []
        self.quitar_cupon_caja()
        self.cancelar_cobro()
        self.cargar_mesas()
        if es_mostrador:
            self.cargar_pedidos_mostrador_pendientes()
        total_final = max(total_base - descuento + propina + recargo, Decimal("0.00"))
        try:
            _pct_iva = float(self.config_porcentaje_iva or "18.0")
        except (ValueError, AttributeError):
            _pct_iva = 18.0
        html_ticket = generate_cashier_ticket_html(
            order_reference=mesa_label,
            pedido_id=pedido_id,
            items=ticket_lines,
            total=float(total_final),
            attended_by=attended_by,
            company_name=self.config_nombre_local or "TUWAYKIFOOD",
            company_ruc=self.config_ruc,
            company_sucursal=self.config_sucursal,
            company_direccion=self.config_direccion,
            company_telefono=self.config_telefono,
            descuento=float(descuento),
            propina=float(propina),
            recargo=float(recargo),
            recargo_concepto=recargo_concepto or "",
            metodo_pago=metodo_final,
            mensaje_footer=self.config_mensaje_ticket,
            mostrar_iva=self.config_mostrar_iva,
            nombre_impuesto=self.config_nombre_impuesto or "IGV",
            porcentaje_iva=_pct_iva,
            paper_width_mm=self._ticket_paper_width_mm(),
        )
        desc_txt = f" - descuento {_money_text(descuento)}" if descuento > 0 else ""
        propina_txt = f" + propina {_money_text(propina)}" if propina > 0 else ""
        recargo_txt = f" + recargo {_money_text(recargo)}" if recargo > 0 else ""
        return [
            rx.toast.success(f"{mesa_label} cobrado — {_money_text(total_final)}"),
            rx.call_script(build_print_script(html_ticket)),
            ReportesState.cargar_historial_ventas,
            ReportesState.cargar_dashboard,
        ]

    # ─── Caja — Cobro de mesa ─────────────────────────────────────────────────

    def cobrar_mesa(self, mesa_id: int) -> None:
        """Redirige al panel de cobro completo (método, descuento, propina, turno).
        El cobro directo sin panel quedó deprecado — siempre pasa por abrir_cobro_mesa."""
        return self.abrir_cobro_mesa(mesa_id or self.mesa_seleccionada_id)

    def imprimir_precuenta(self, mesa_id: int = 0):
        objetivo = mesa_id or self.caja_cobro_mesa_id or self.mesa_seleccionada_id
        if objetivo <= 0:
            return rx.toast.error("Seleccione una mesa para imprimir la pre-cuenta.")
        ticket_lines: list[TicketLine] = []
        mesa_label = ""
        pedido_id = 0
        attended_by = ""
        total = 0.0
        descuento = 0.0
        with self._tenant_session() as session:
            mesa = session.get(Mesa, objetivo)
            if mesa is None or mesa.company_id != self._company_id():
                return rx.toast.error("Mesa no encontrada.")
            mesa_label = mesa.nombre or f"Mesa {mesa.numero}"
            pedido = _get_open_order(session, objetivo, self._company_id())
            if pedido is None:
                return rx.toast.error(f"{mesa_label} no tiene pedido abierto.")
            pedido_id = pedido.id or 0
            attended_by = ""
            if pedido.mozo_id:
                mozo = session.get(UsuarioFood, pedido.mozo_id)
                attended_by = mozo.nombre if mozo else ""
            detalles = session.exec(
                select(DetallePedido).where(
                    DetallePedido.pedido_id == pedido.id
                ).order_by(DetallePedido.id)
            ).all()
            pids = {d.producto_id for d in detalles}
            productos_map = {p.id: p for p in session.exec(select(Producto).where(Producto.id.in_(list(pids)))).all()} if pids else {}
            for d in detalles:
                prod = productos_map.get(d.producto_id)
                ticket_lines.append(TicketLine(
                    name=prod.nombre if prod else f"Producto {d.producto_id}",
                    quantity=d.cantidad,
                    unit_price=float(d.precio_unitario),
                    subtotal=float(d.subtotal),
                    note=d.notas or "",
                ))
            total = float(pedido.total)
            descuento = float(pedido.descuento or 0)

        html_ticket = generate_precuenta_html(
            order_reference=mesa_label,
            pedido_id=pedido_id,
            items=ticket_lines,
            total=total,
            attended_by=attended_by,
            company_name=self.config_nombre_local or "TUWAYKIFOOD",
            company_ruc=self.config_ruc,
            company_sucursal=self.config_sucursal,
            company_direccion=self.config_direccion,
            company_telefono=self.config_telefono,
            descuento=descuento,
            paper_width_mm=self._ticket_paper_width_mm(),
        )
        return rx.call_script(build_print_script(html_ticket))

    def abrir_cobro_pedido_mostrador(self, pedido_id: int) -> None:
        """Abre el panel de cobro para una orden de mostrador pendiente de pago."""
        items_ui: list[CajaItemView] = []
        total_override = 0.0
        cliente_nombre = ""
        with self._tenant_session() as session:
            pedido = session.get(Pedido, pedido_id)
            if pedido is None or pedido.company_id != self._company_id():
                return rx.toast.error("El pedido no existe.")
            if pedido.pagado:
                return rx.toast.error("Este pedido ya fue cobrado.")
            detalles = session.exec(
                select(DetallePedido).where(
                    DetallePedido.pedido_id == pedido_id
                ).order_by(DetallePedido.id)
            ).all()
            pids = {d.producto_id for d in detalles}
            productos = {p.id: p for p in session.exec(select(Producto).where(Producto.id.in_(list(pids)))).all()} if pids else {}
            for d in detalles:
                prod = productos.get(d.producto_id)
                items_ui.append(CajaItemView(
                    detalle_id=d.id or 0,
                    producto_nombre=prod.nombre if prod else f"Producto {d.producto_id}",
                    cantidad=d.cantidad,
                    precio_unitario_texto=_money_text(_to_decimal(d.precio_unitario)),
                    subtotal_texto=_money_text(_to_decimal(d.subtotal)),
                    subtotal_float=float(_to_decimal(d.subtotal)),
                    notas=d.notas or "",
                ))
            total_override = float(_to_decimal(pedido.total))
            cliente_nombre = _actor_name(pedido.nombre_cliente) or "Sin nombre"
        self.caja_cobro_pedido_id = pedido_id
        self.caja_cobro_pedido_label = f"Para llevar — {cliente_nombre}"
        self.caja_cobro_total_override = total_override
        self.caja_cobro_mesa_id = 0
        self.caja_cobro_metodo = "efectivo"
        self.caja_cobro_propina = ""
        self.caja_cobro_propina_pct = 0
        self.caja_cobro_descuento = ""
        self.caja_cobro_descuento_es_pct = False
        self.caja_cobro_recargo = ""
        self.caja_cobro_recargo_concepto = "delivery"
        self.caja_cobro_efectivo_recibido = ""
        self.caja_cobro_error = ""
        self.caja_promo_aplicada_nombre = ""
        self.caja_promo_aplicada_texto = ""
        self.caja_cobro_items = items_ui

    def editar_pedido_mostrador(self, pedido_id: int):
        """Carga un pedido de mostrador pendiente en el carrito y lo anula para re-edición."""
        carrito: list[CarritoItem] = []
        cliente = ""
        try:
            with self._tenant_session() as session:
                pedido = session.get(Pedido, pedido_id)
                if pedido is None or pedido.company_id != self._company_id():
                    return rx.toast.error("El pedido no existe.")
                if pedido.pagado:
                    return rx.toast.error("Este pedido ya fue cobrado, no se puede editar.")
                if pedido.estado == EstadoPedido.CANCELADO.value:
                    return rx.toast.error("Este pedido ya fue anulado.")
                detalles = session.exec(
                    select(DetallePedido).where(DetallePedido.pedido_id == pedido_id)
                ).all()
                productos = {
                    p.id: p
                    for p in session.exec(
                        select(Producto).where(Producto.company_id == self._company_id())
                    ).all()
                }
                for d in detalles:
                    prod = productos.get(d.producto_id)
                    if prod is None:
                        continue
                    precio = float(_to_decimal(d.precio_unitario))
                    subtotal = float(_to_decimal(d.subtotal))
                    carrito.append(CarritoItem(
                        producto_id=d.producto_id,
                        nombre=prod.nombre,
                        cantidad=d.cantidad,
                        precio_unitario=precio,
                        subtotal=subtotal,
                        subtotal_texto=_money_text(_to_decimal(d.subtotal)),
                        nota=d.notas or "",
                    ))
                cliente = pedido.nombre_cliente or ""
                usuario_id = (self.usuario_actual.id or None) if self.usuario_actual else None
                anular_pedido_abierto(session, pedido, usuario_id, "Re-edición desde Caja")
                session.commit()
        except ValueError as exc:
            return rx.toast.error(str(exc))
        self.mostrador_carrito = carrito
        self.mostrador_cliente_nombre = cliente
        self.cancelar_cobro()
        self.cargar_pedidos_mostrador_pendientes()
        return [rx.toast.success(f"Pedido #{pedido_id} cargado en Mostrador para edición."), rx.redirect("/mostrador")]

    # ─── Mostrador ────────────────────────────────────────────────────────────

    def set_mostrador_cliente_nombre(self, value: str) -> None:
        self.mostrador_cliente_nombre = str(value)[:120]

    def set_busqueda_producto_mostrador(self, value: str) -> None:
        self.busqueda_producto_mostrador = value

    def agregar_producto_mostrador(self, producto_id: int) -> None:
        producto = next((p for p in self.productos if p.id == producto_id and p.disponible), None)
        if producto is None:
            return rx.toast.error("Producto no disponible para mostrador.")
        if producto.tiene_modificadores:
            self._abrir_seleccion_modificadores(producto_id, producto.nombre, producto.precio, origen="mostrador")
            return
        carrito = list(self.mostrador_carrito)
        for i, item in enumerate(carrito):
            if item.producto_id == producto_id:
                cantidad = item.cantidad + 1
                subtotal = round(producto.precio * cantidad, 2)
                carrito[i] = CarritoItem(
                    producto_id=producto.id,
                    nombre=producto.nombre,
                    cantidad=cantidad,
                    precio_unitario=producto.precio,
                    subtotal=subtotal,
                    subtotal_texto=_money_text(subtotal),
                    nota=item.nota,
                )
                self.mostrador_carrito = carrito
                return rx.toast.success(f"{producto.nombre} agregado a mostrador.")
        carrito.append(CarritoItem(
            producto_id=producto.id,
            nombre=producto.nombre,
            cantidad=1,
            precio_unitario=producto.precio,
            subtotal=producto.precio,
            subtotal_texto=producto.precio_texto,
        ))
        self.mostrador_carrito = carrito
        return rx.toast.success(f"{producto.nombre} agregado a mostrador.")

    def _agregar_producto_mostrador_con_mods(self, producto_id: int, mods_json: str, mods_texto: str, extra: Decimal) -> None:
        producto = next((p for p in self.productos if p.id == producto_id and p.disponible), None)
        if producto is None:
            return rx.toast.error("Producto no disponible para mostrador.")
        precio_unit = round(producto.precio + float(extra), 2)
        carrito = list(self.mostrador_carrito)
        carrito.append(CarritoItem(
            producto_id=producto.id,
            nombre=producto.nombre,
            cantidad=1,
            precio_unitario=precio_unit,
            subtotal=precio_unit,
            subtotal_texto=_money_text(precio_unit),
            modificadores_texto=mods_texto,
            modificadores_json=mods_json,
        ))
        self.mostrador_carrito = carrito
        return rx.toast.success(f"{producto.nombre} agregado a mostrador.")

    def restar_producto_mostrador(self, producto_id: int) -> None:
        carrito_actualizado: list[CarritoItem] = []
        encontrado = False
        for item in self.mostrador_carrito:
            if item.producto_id != producto_id:
                carrito_actualizado.append(item)
                continue
            encontrado = True
            cantidad = item.cantidad - 1
            if cantidad > 0:
                subtotal = round(item.precio_unitario * cantidad, 2)
                carrito_actualizado.append(CarritoItem(
                    producto_id=item.producto_id,
                    nombre=item.nombre,
                    cantidad=cantidad,
                    precio_unitario=item.precio_unitario,
                    subtotal=subtotal,
                    subtotal_texto=_money_text(subtotal),
                    nota=item.nota,
                ))
        if not encontrado:
            return rx.toast.error("Ese producto no está en el carrito de mostrador.")
        self.mostrador_carrito = carrito_actualizado
        return rx.toast.success("Carrito de mostrador actualizado.")

    def limpiar_carrito_mostrador(self) -> None:
        self.mostrador_carrito = []
        self.mostrador_metodo_pago = "efectivo"
        self.busqueda_producto_mostrador = ""
        self.nota_producto_activo_id = 0
        self.nota_input_temporal = ""
        return rx.toast.success("Carrito de mostrador limpio.")

    def abrir_nota_item_mostrador(self, producto_id: int) -> None:
        item = next((i for i in self.mostrador_carrito if i.producto_id == producto_id), None)
        self.nota_producto_activo_id = producto_id
        self.nota_input_temporal = item.nota if item else ""

    def guardar_nota_item_mostrador(self, producto_id: int) -> None:
        nota = self.nota_input_temporal.strip()
        carrito = list(self.mostrador_carrito)
        for i, item in enumerate(carrito):
            if item.producto_id == producto_id:
                carrito[i] = CarritoItem(
                    producto_id=item.producto_id,
                    nombre=item.nombre,
                    cantidad=item.cantidad,
                    precio_unitario=item.precio_unitario,
                    subtotal=item.subtotal,
                    subtotal_texto=item.subtotal_texto,
                    nota=nota,
                )
                break
        self.mostrador_carrito = carrito
        self.nota_producto_activo_id = 0
        self.nota_input_temporal = ""

    def seleccionar_mostrador_metodo(self, metodo: str) -> None:
        self.mostrador_metodo_pago = metodo

    def enviar_pedido_mostrador(self) -> None:
        """Crea el pedido de mostrador y lo manda a cocina. El cobro se realiza en Caja."""
        if self.mostrador_enviando:
            return
        if not self.mostrador_carrito:
            return rx.toast.error("Agrega productos antes de enviar a cocina.")
        if self.usuario_actual is None:
            return rx.toast.error("Inicia sesión para registrar el pedido.")
        self.mostrador_enviando = True
        pedido_id = 0
        cliente_nombre = _actor_name(self.mostrador_cliente_nombre) or "Sin nombre"
        ticket_label = f"Para Llevar - {cliente_nombre}"
        ticket_lines: list[TicketLine] = []
        with self._tenant_session() as session:
            productos = {p.id: p for p in session.exec(select(Producto).where(Producto.company_id == self._company_id())).all()}
            invalidos = [item.nombre for item in self.mostrador_carrito if not item.es_combo and (item.producto_id not in productos or not productos[item.producto_id].disponible)]
            if invalidos:
                self.mostrador_enviando = False
                return rx.toast.error(f"Productos no disponibles: {', '.join(invalidos)}")
            stock_items = [(item.producto_id, item.cantidad) for item in self.mostrador_carrito if not item.es_combo]
            if stock_items:
                errores_stock = _validar_stock_para_items(session, stock_items, self._company_id())
                if errores_stock:
                    self.mostrador_enviando = False
                    return rx.toast.error("Stock insuficiente — " + "; ".join(errores_stock))
            now = _utcnow()
            pedido = Pedido(
                company_id=self._company_id(),
                sucursal_id=self._sucursal_id() or None,
                mesa_id=None,
                cajero_id=self.usuario_actual.id or None,
                tipo_pedido=TipoPedido.MOSTRADOR.value,
                nombre_cliente=_actor_name(self.mostrador_cliente_nombre) or None,
                pagado=False,
                estado=EstadoPedido.ENVIADO.value,
                metodo_pago=None,
                total=Decimal("0.00"),
                abierto_en=now,
                cerrado_en=None,
                turno_caja_id=None,
            )
            session.add(pedido)
            session.commit()
            session.refresh(pedido)
            for item in self.mostrador_carrito:
                if item.es_combo:
                    import json as _json
                    precio = _to_decimal(item.precio_unitario)
                    subtotal = precio * item.cantidad
                    combo_items = []
                    try:
                        combo_items = _json.loads(item.combo_items_json) if item.combo_items_json else []
                    except Exception:
                        pass
                    first_pid = combo_items[0].get("producto_id", 0) if combo_items else 0
                    detalle = DetallePedido(
                        company_id=self._company_id(),
                        pedido_id=pedido.id or 0,
                        producto_id=first_pid,
                        cantidad=item.cantidad,
                        precio_unitario=precio,
                        subtotal=subtotal,
                        notas=item.nota or None,
                        estado_produccion=EstadoProduccion.PENDIENTE.value,
                        impreso_cocina=True,
                        impreso_caja=True,
                        enviado_cocina_at=now,
                        combo_items_json=item.combo_items_json or None,
                    )
                    session.add(detalle)
                    ticket_lines.append(TicketLine(
                        name=item.nombre,
                        quantity=item.cantidad,
                        unit_price=float(precio),
                        subtotal=float(subtotal),
                        note="",
                    ))
                else:
                    producto = productos[item.producto_id]
                    precio = _to_decimal(item.precio_unitario) if item.modificadores_json else _to_decimal(producto.precio)
                    subtotal = precio * item.cantidad
                    detalle = DetallePedido(
                        company_id=self._company_id(),
                        pedido_id=pedido.id or 0,
                        producto_id=producto.id or 0,
                        cantidad=item.cantidad,
                        precio_unitario=precio,
                        subtotal=subtotal,
                        notas=item.nota or None,
                        estado_produccion=EstadoProduccion.PENDIENTE.value,
                        impreso_cocina=True,
                        impreso_caja=True,
                        enviado_cocina_at=now,
                        modificadores_json=item.modificadores_json or None,
                    )
                    session.add(detalle)
                    mod_note = f" ({item.modificadores_texto})" if item.modificadores_texto else ""
                    ticket_lines.append(TicketLine(
                        name=producto.nombre + mod_note,
                        quantity=item.cantidad,
                        unit_price=float(precio),
                        subtotal=float(subtotal),
                        note="",
                    ))
            _recalculate_order_total(session, pedido)
            _sync_order_status(session, pedido)
            session.commit()
            pedido_id = pedido.id or 0

        self.mostrador_enviando = False
        self.ultimo_pedido_id = pedido_id
        self.mostrador_carrito = []
        self.mostrador_cliente_nombre = ""
        self.busqueda_producto_mostrador = ""
        self.cargar_cocina()
        self.cargar_pedidos_mostrador_pendientes()
        return rx.toast.success(f"Pedido #{pedido_id} enviado a cocina")

    def cargar_pedidos_mostrador_pendientes(self) -> None:
        """Carga órdenes de mostrador sin cobrar (pagado=False) — usada en Mostrador y Caja."""
        with self._tenant_session() as session:
            pedidos = session.exec(
                select(Pedido).where(
                    Pedido.company_id == self._company_id(),
                    Pedido.tipo_pedido == TipoPedido.MOSTRADOR.value,
                    Pedido.pagado.is_(False),
                    Pedido.estado != EstadoPedido.CANCELADO.value,
                ).order_by(Pedido.abierto_en.desc(), Pedido.id.desc())
            ).all()
            if not pedidos:
                if self.pedidos_mostrador_pendientes:
                    self.pedidos_mostrador_pendientes = []
                return
            productos = {p.id: p for p in session.exec(select(Producto).where(Producto.company_id == self._company_id())).all()}
            result: list[MostradorPendienteView] = []
            for pedido in pedidos:
                detalles = session.exec(
                    select(DetallePedido).where(DetallePedido.pedido_id == pedido.id).order_by(DetallePedido.id)
                ).all()
                resumen = " · ".join(
                    f"{d.cantidad}x {productos[d.producto_id].nombre if d.producto_id in productos else f'Producto {d.producto_id}'}"
                    for d in detalles
                )
                hora = pedido.abierto_en or pedido.created_at
                en_cocina = any(
                    d.estado_produccion in (EstadoProduccion.PENDIENTE.value, EstadoProduccion.EN_PREPARACION.value)
                    for d in detalles
                )
                result.append(MostradorPendienteView(
                    pedido_id=pedido.id or 0,
                    cliente_nombre=_actor_name(pedido.nombre_cliente) or "Sin nombre",
                    hora_texto=hora.strftime("%H:%M") if hora else "",
                    items_resumen=resumen,
                    total_texto=_money_text(pedido.total),
                    total=float(_to_decimal(pedido.total)),
                    en_cocina=en_cocina,
                ))
            if _list_fingerprint(result) != _list_fingerprint(self.pedidos_mostrador_pendientes):
                self.pedidos_mostrador_pendientes = result

    def cargar_pedidos_mostrador_entregados(self) -> None:
        with self._tenant_session() as session:
            pedidos = session.exec(
                select(Pedido).where(
                    Pedido.company_id == self._company_id(),
                    Pedido.tipo_pedido == TipoPedido.MOSTRADOR.value,
                    Pedido.pagado.is_(True),
                ).order_by(Pedido.updated_at.desc(), Pedido.id.desc())
            ).all()
            if not pedidos:
                if self.pedidos_mostrador_entregados:
                    self.pedidos_mostrador_entregados = []
                return
            productos = {p.id: p for p in session.exec(select(Producto).where(Producto.company_id == self._company_id())).all()}
            historial: list = []
            for pedido in pedidos:
                detalles = session.exec(
                    select(DetallePedido).where(DetallePedido.pedido_id == pedido.id).order_by(DetallePedido.id)
                ).all()
                cobrado_en = pedido.cerrado_en or pedido.updated_at or pedido.created_at
                resumen = " · ".join(
                    f"{d.cantidad}x {productos[d.producto_id].nombre if d.producto_id in productos else f'Producto {d.producto_id}'}"
                    for d in detalles
                )
                historial.append((
                    cobrado_en,
                    MostradorEntregadoView(
                        pedido_id=pedido.id or 0,
                        cliente_nombre=_actor_name(pedido.nombre_cliente) or "Sin nombre",
                        hora_texto=cobrado_en.strftime("%H:%M") if cobrado_en else "",
                        items_resumen=resumen,
                        total_texto=_money_text(pedido.total),
                    ),
                ))
            historial.sort(key=lambda x: x[0], reverse=True)
            nuevos_entregados = [item for _, item in historial[:10]]
            if _list_fingerprint(nuevos_entregados) != _list_fingerprint(self.pedidos_mostrador_entregados):
                self.pedidos_mostrador_entregados = nuevos_entregados

    def entregar_pedido_mostrador(self, pedido_id: int) -> None:
        with self._tenant_session() as session:
            pedido = session.get(Pedido, pedido_id)
            if pedido is None or pedido.tipo_pedido != TipoPedido.MOSTRADOR.value or pedido.company_id != self._company_id():
                return rx.toast.error("El pedido de mostrador ya no existe.")
            detalles_listos = session.exec(
                select(DetallePedido).where(
                    DetallePedido.pedido_id == pedido_id,
                    DetallePedido.impreso_cocina.is_(True),
                    DetallePedido.estado_produccion == EstadoProduccion.LISTO_PARA_ENTREGAR.value,
                )
            ).all()
            if not detalles_listos:
                return rx.toast.error("Ese pedido ya no tiene items listos para entregar.")
            now = _utcnow()
            for d in detalles_listos:
                d.estado_produccion = EstadoProduccion.ENTREGADO_AL_CLIENTE.value
                d.updated_at = now
                session.add(d)
            _sync_order_status(session, pedido)
            session.add(pedido)
            session.commit()
        self.cargar_cocina()
        self.cargar_pedidos_mostrador_pendientes()
        self.cargar_pedidos_mostrador_entregados()
        return [rx.toast.success("Pedido de mostrador entregado al cliente."), ReportesState.cargar_historial_ventas]


# ─── Estado público (sin auth) ────────────────────────────────────────────────

class ProductoPublicoView(BaseModel):
    id: int = 0
    nombre: str
    descripcion: str
    precio_texto: str
    precio_float: float = 0.0
    imagen_url: str
    emoji: str = "🍽️"
    tags_texto: str = ""


class PromoPublicaView(BaseModel):
    nombre: str = ""
    descripcion: str = ""
    descuento_texto: str = ""
    horario_texto: str = ""
    dias_texto: str = ""


class CategoriaPublicaView(BaseModel):
    nombre: str
    productos: list[ProductoPublicoView]
    emoji: str = "🍽️"


class MenuPublicoState(rx.State):
    """Estado de la carta pública — no requiere sesión."""

    nombre_local: str = ""
    logo_url_local: str = ""
    categorias_menu: list[CategoriaPublicaView] = []
    promos_activas: list[PromoPublicaView] = []
    cargando: bool = True
    no_encontrado: bool = False
    busqueda_menu: str = ""

    def set_busqueda_menu(self, v: str) -> None:
        self.busqueda_menu = v

    @rx.var
    def categorias_menu_filtradas(self) -> list[CategoriaPublicaView]:
        q = self.busqueda_menu.strip().lower()
        if not q:
            return self.categorias_menu
        result: list[CategoriaPublicaView] = []
        for cat in self.categorias_menu:
            prods = [
                p for p in cat.productos
                if q in p.nombre.lower() or q in (p.descripcion or "").lower()
            ]
            if prods:
                result.append(CategoriaPublicaView(
                    nombre=cat.nombre, emoji=cat.emoji, productos=prods,
                ))
        return result

    def on_load(self) -> None:
        slug = self.router.page.params.get("slug", "")
        self.cargando = True
        self.no_encontrado = False
        self.nombre_local = ""
        self.logo_url_local = ""
        self.categorias_menu = []
        self.promos_activas = []
        self.busqueda_menu = ""

        if not slug:
            self.no_encontrado = True
            self.cargando = False
            return

        # Único punto legítimamente cross-tenant de todo el sistema: la carta
        # pública se resuelve por slug, no por sesión — ningún contexto tenant
        # está armado todavía cuando llega esta request.
        with tenant_bypass(), get_session() as session:
            cfg = session.exec(
                select(ConfigImpresora).where(ConfigImpresora.slug == slug)
            ).first()
            if cfg is None:
                self.no_encontrado = True
                self.cargando = False
                return

            company_id = cfg.company_id
            # Empresa suspendida o con trial vencido: la carta pública también
            # deja de servirse (mismo enforcement que las páginas operativas).
            if _bloqueo_suscripcion(company_id):
                self.no_encontrado = True
                self.cargando = False
                return
            self.nombre_local = cfg.nombre_local

            empresa = session.get(Company, company_id)
            self.logo_url_local = (empresa.logo_url or "") if empresa else ""

            cats = session.exec(
                select(Categoria)
                .where(Categoria.company_id == company_id, Categoria.activa.is_(True))
                .order_by(Categoria.orden, Categoria.nombre)
            ).all()

            result: list[CategoriaPublicaView] = []
            for cat in cats:
                prods = session.exec(
                    select(Producto)
                    .where(
                        Producto.company_id == company_id,
                        Producto.categoria_id == cat.id,
                        Producto.disponible.is_(True),
                    )
                    .order_by(Producto.nombre)
                ).all()
                if prods:
                    result.append(
                        CategoriaPublicaView(
                            nombre=cat.nombre,
                            emoji=_emoji_para_categoria(cat.nombre),
                            productos=[
                                ProductoPublicoView(
                                    id=p.id or 0,
                                    nombre=p.nombre,
                                    descripcion=p.descripcion or "",
                                    precio_texto=_money_text(p.precio),
                                    precio_float=float(_to_decimal(p.precio)),
                                    imagen_url=p.imagen_url or "",
                                    emoji=p.emoji or _emoji_para_producto(p.nombre),
                                    tags_texto=_tags_to_text(p.tags),
                                )
                                for p in prods
                            ],
                        )
                    )

            self.categorias_menu = result

            ahora = ahora_local_pe()
            promos_db = session.exec(
                select(Promocion).where(
                    Promocion.company_id == company_id,
                    Promocion.activa.is_(True),
                )
            ).all()
            promo_views: list[PromoPublicaView] = []
            for p in promos_db:
                if not promo_vigente(p, ahora):
                    continue
                val = Decimal(str(p.valor))
                if p.tipo in (TipoPromocion.PORCENTAJE.value, TipoPromocion.HAPPY_HOUR.value):
                    dtxt = f"{val:.0f}% OFF"
                elif p.tipo == TipoPromocion.DOSXUNO.value:
                    dtxt = "2x1"
                else:
                    dtxt = f"S/ {val:.2f} OFF"
                if p.hora_inicio and p.hora_fin:
                    htxt = f"{p.hora_inicio} – {p.hora_fin}"
                else:
                    htxt = "Todo el día"
                mask = p.dias_semana_mask or 127
                if mask >= 127:
                    dias = "Todos los días"
                else:
                    dias = ", ".join(
                        abrev.capitalize() for abrev, _, bit in PROMO_DIAS if mask & bit
                    ) or "Todos los días"
                promo_views.append(PromoPublicaView(
                    nombre=p.nombre,
                    descripcion=p.descripcion or "",
                    descuento_texto=dtxt,
                    horario_texto=htxt,
                    dias_texto=dias,
                ))
            self.promos_activas = promo_views

        self.cargando = False


class AdminLocalState(rx.State):
    """Estado para login de dueño del local vía email+contraseña (independiente del PIN)."""

    autenticado: bool = False
    email_input: str = ""
    password_input: str = ""
    error_msg: str = ""
    show_password: bool = False
    login_empresa_nombre: str = ""
    login_empresa_logo: str = ""
    login_empresa_slug: str = ""

    def set_email_input(self, v: str) -> None:
        self.email_input = v

    def set_password_input(self, v: str) -> None:
        self.password_input = v

    def toggle_show_password(self) -> None:
        self.show_password = not self.show_password

    def on_load_dono_login(self):
        self.error_msg = ""
        self.login_empresa_nombre = ""
        self.login_empresa_logo = ""
        self.login_empresa_slug = ""
        slug = self.router.page.params.get("empresa", "")
        if slug:
            with tenant_bypass():
                with get_session() as session:
                    empresa = session.exec(
                        select(Company).where(Company.slug == slug, Company.is_active.is_(True))
                    ).first()
            if empresa is not None:
                self.login_empresa_nombre = empresa.name
                self.login_empresa_logo = empresa.logo_url or ""
                self.login_empresa_slug = empresa.slug
        if self.autenticado:
            return rx.redirect("/admin")
        return None

    async def on_load_dono(self):
        if self.autenticado:
            return None
        # Una sesion PIN de rol Admin (login rapido en /login) tambien
        # habilita el Dashboard, no solo el login por email/contraseña.
        food_state = await self.get_state(FoodState)
        if (
            food_state.usuario_actual is not None
            and food_state.usuario_actual.rol == RolUsuario.ADMIN.value
        ):
            self.autenticado = True
            return None
        return rx.redirect("/admin/login")

    def login_on_enter(self, key: str):
        if key == "Enter":
            return type(self).login_admin_local

    async def login_admin_local(self) -> None:
        import hashlib
        email = self.email_input.strip().lower()
        password = self.password_input.strip()
        self.error_msg = ""
        if not email or not password:
            self.error_msg = "Ingrese email y contraseña."
            return
        if _is_rate_limited(email):
            remaining = _remaining_lockout_time(email)
            self.error_msg = f"Demasiados intentos. Espere {remaining} minuto(s)."
            return
        with tenant_bypass():
            with get_session() as session:
                cfg = session.exec(
                    select(ConfigImpresora).where(
                        ConfigImpresora.admin_email == email,
                    )
                ).first()
                if cfg is None or not cfg.admin_password_hash:
                    _record_failed_attempt(email)
                    self.error_msg = "Credenciales incorrectas."
                    return
                stored = cfg.admin_password_hash
                is_bcrypt = stored.startswith("$2b$") or stored.startswith("$2a$")
                if is_bcrypt:
                    ok = _verify_pin(password, stored)
                else:
                    ok = hashlib.sha256(password.encode()).hexdigest() == stored
                if not ok:
                    _record_failed_attempt(email)
                    self.error_msg = "Credenciales incorrectas."
                    return
                if not is_bcrypt:
                    cfg.admin_password_hash = _bcrypt.hashpw(password.encode(), _bcrypt.gensalt()).decode()
                    session.add(cfg)
                    session.commit()
                company_id = cfg.company_id
        _clear_login_attempts(email)
        bloqueo = _bloqueo_suscripcion(company_id)
        if bloqueo:
            self.error_msg = bloqueo
            return
        self.autenticado = True
        self.password_input = ""
        # Vincular esta sesion con FoodState.usuario_actual: Carta, Reportes,
        # Usuarios y Configuracion validan acceso via usuario_actual.rol, no
        # via AdminLocalState.autenticado, asi que sin esto el dueño podia
        # ver el Dashboard pero quedaba bloqueado en todos sus sub-modulos.
        food_state = await self.get_state(FoodState)
        set_tenant_context(company_id, None)
        with get_session() as session:
            session.info["tenant_bypass"] = True
            admin_usuario = session.exec(
                select(UsuarioFood).where(
                    UsuarioFood.company_id == company_id,
                    UsuarioFood.rol == RolUsuario.ADMIN.value,
                    UsuarioFood.activo.is_(True),
                )
            ).first()
        if admin_usuario is not None:
            food_state.usuario_actual = UsuarioSesion(
                id=admin_usuario.id or 0,
                nombre=admin_usuario.nombre,
                rol=admin_usuario.rol,
                company_id=company_id,
                perm_descuento=True,
                perm_anular=True,
                perm_reportes=True,
                perm_turno=True,
                perm_inventario=True,
                perm_costos=True,
                perm_reimprimir=True,
                acceso_mozos=True,
                acceso_caja=True,
                acceso_cocina=True,
                acceso_mostrador=True,
            )
        else:
            food_state.usuario_actual = UsuarioSesion(
                id=0,
                nombre=email,
                rol=RolUsuario.ADMIN.value,
                company_id=company_id,
                perm_descuento=True,
                perm_anular=True,
                perm_reportes=True,
                acceso_mozos=True,
                acceso_caja=True,
                acceso_cocina=True,
                acceso_mostrador=True,
            )
        food_state.cargar_config_impresora()
        food_state._cargar_plan_empresa()
        return rx.redirect("/admin")

    async def logout_admin_local(self) -> None:
        self.autenticado = False
        self.email_input = ""
        self.password_input = ""
        food_state = await self.get_state(FoodState)
        food_state.usuario_actual = None
        food_state.session_token = ""
        return rx.redirect("/admin/login")
