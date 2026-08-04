"""Cola de impresión para el agente local.

El backend encola trabajos (comandas y comprobantes) y el agente local los jala
por HTTPS, imprime en la impresora que corresponde (red o USB) y confirma.

- `crear_agente` / `verificar_token`: alta y auth de agentes (token hasheado).
- `encolar_trabajo`: mete un documento ya renderizado en la cola.
- `reclamar_comandas_pendientes`: reclama de forma ATÓMICA las comandas nuevas
  enviadas a cocina (reutiliza `DetallePedido.ticket_impreso_at`) y las encola.
  Es el equivalente en modo agente de `_check_cocina_auto_print`.
"""
from __future__ import annotations

import hashlib
import hmac
import secrets

from sqlalchemy import update as sa_update
from sqlmodel import Session, select
from tuwayki_core.utils.timezone import utc_now_naive

from app.models.food import (
    AgenteImpresion,
    ConfigImpresora,
    DetallePedido,
    EstadoPedido,
    Impresora,
    Mesa,
    Pedido,
    Producto,
    RolImpresora,
    TipoDocumento,
    TipoPedido,
    TrabajoImpresion,
)
from app.services.receipt_service import (
    TicketLine,
    build_kitchen_ticket_lines,
    ticket_text,
)


# ─── Agentes (auth) ───────────────────────────────────────────────────────────


def _hash_token(secret: str) -> str:
    return hashlib.sha256(secret.encode()).hexdigest()


def crear_agente(
    session: Session,
    *,
    company_id: int,
    sucursal_id: int | None = None,
    nombre: str = "Agente de impresión",
) -> tuple[AgenteImpresion, str]:
    """Crea un agente y devuelve (agente, token_en_claro). El token se muestra
    UNA sola vez; en la BD queda solo su hash."""
    secret = secrets.token_urlsafe(32)
    agente = AgenteImpresion(
        company_id=company_id,
        sucursal_id=sucursal_id,
        nombre=nombre,
        token_hash=_hash_token(secret),
    )
    session.add(agente)
    session.commit()
    session.refresh(agente)
    return agente, f"{agente.id}.{secret}"


def verificar_token(session: Session, token: str) -> AgenteImpresion | None:
    """Valida un token `"<id>.<secreto>"`. Devuelve el agente activo o None."""
    if not token or "." not in token:
        return None
    id_str, _, secret = token.partition(".")
    try:
        agente_id = int(id_str)
    except ValueError:
        return None
    agente = session.get(AgenteImpresion, agente_id)
    if agente is None or not agente.activo:
        return None
    if not hmac.compare_digest(agente.token_hash, _hash_token(secret)):
        return None
    return agente


# ─── Encolado ─────────────────────────────────────────────────────────────────


def _paper_width_for(
    session: Session, company_id: int, sucursal_id: int | None, rol: str
) -> int:
    """Ancho de papel del destino: el de la impresora del rol si lo define, si no
    el de la empresa (ConfigImpresora), con fallback 80mm."""
    stmt = select(Impresora).where(
        Impresora.company_id == company_id,
        Impresora.rol == rol,
        Impresora.activa.is_(True),
    )
    if sucursal_id is not None:
        stmt = stmt.where(Impresora.sucursal_id == sucursal_id)
    imp = session.exec(stmt.order_by(Impresora.id)).first()
    if imp is not None and imp.paper_width_mm:
        return imp.paper_width_mm
    cfg = session.exec(
        select(ConfigImpresora).where(ConfigImpresora.company_id == company_id)
    ).first()
    if cfg is not None and cfg.ticket_paper_width_mm:
        return cfg.ticket_paper_width_mm
    return 80


def encolar_trabajo(
    session: Session,
    *,
    company_id: int,
    rol: str,
    tipo_doc: str,
    contenido: str,
    paper_width_mm: int,
    sucursal_id: int | None = None,
    pedido_id: int | None = None,
    commit: bool = True,
) -> TrabajoImpresion:
    """Encola un documento ya renderizado (texto) para que el agente lo imprima."""
    trabajo = TrabajoImpresion(
        company_id=company_id,
        sucursal_id=sucursal_id,
        rol=rol,
        tipo_doc=tipo_doc,
        contenido=contenido,
        paper_width_mm=paper_width_mm,
        pedido_id=pedido_id,
    )
    session.add(trabajo)
    if commit:
        session.commit()
        session.refresh(trabajo)
    return trabajo


def _mesa_label(pedido: Pedido, mesa: Mesa | None) -> str:
    if mesa is not None:
        return mesa.nombre or f"Mesa {mesa.numero}"
    if pedido.tipo_pedido == TipoPedido.MOSTRADOR.value:
        nombre_cli = (pedido.nombre_cliente or "").strip() or "Sin nombre"
        return f"Para Llevar - {nombre_cli}"
    return f"Pedido #{pedido.id}"


def reclamar_comandas_pendientes(
    session: Session, company_id: int, sucursal_id: int | None = None
) -> list[TrabajoImpresion]:
    """Reclama ATÓMICAMENTE las comandas enviadas a cocina aún no impresas y las
    encola como trabajos de rol 'cocina'. Cada comanda se reclama una sola vez
    (UPDATE ... WHERE ticket_impreso_at IS NULL, rowcount == 1), así no se
    duplica entre agentes/pantallas. Devuelve los trabajos creados."""
    stmt = select(DetallePedido).where(
        DetallePedido.company_id == company_id,
        DetallePedido.impreso_cocina.is_(True),
        DetallePedido.ticket_impreso_at.is_(None),
    )
    if sucursal_id is not None:
        stmt = stmt.join(Pedido, Pedido.id == DetallePedido.pedido_id).where(
            Pedido.sucursal_id == sucursal_id
        )
    candidates = session.exec(stmt.order_by(DetallePedido.id)).all()
    if not candidates:
        return []

    now = utc_now_naive()
    claimed: list[dict] = []
    for d in candidates:
        res = session.exec(
            sa_update(DetallePedido)
            .where(
                DetallePedido.id == d.id,
                DetallePedido.ticket_impreso_at.is_(None),
            )
            .values(ticket_impreso_at=now)
        )
        if (res.rowcount or 0) == 1:
            claimed.append(
                {
                    "pedido_id": d.pedido_id,
                    "producto_id": d.producto_id,
                    "cantidad": d.cantidad,
                    "notas": d.notas,
                }
            )
    session.commit()
    if not claimed:
        return []

    groups: dict[int, list[dict]] = {}
    for d in claimed:
        groups.setdefault(d["pedido_id"], []).append(d)
    pedido_ids = list(groups.keys())
    pedidos = {
        p.id: p
        for p in session.exec(select(Pedido).where(Pedido.id.in_(pedido_ids))).all()
    }
    mesas = {
        m.id: m
        for m in session.exec(
            select(Mesa).where(Mesa.company_id == company_id)
        ).all()
    }
    productos = {
        p.id: p
        for p in session.exec(
            select(Producto).where(Producto.company_id == company_id)
        ).all()
    }
    width = _paper_width_for(session, company_id, sucursal_id, RolImpresora.COCINA.value)

    trabajos: list[TrabajoImpresion] = []
    for pid, dets in groups.items():
        pedido = pedidos.get(pid)
        if pedido is None or pedido.estado == EstadoPedido.CANCELADO.value:
            continue
        mesa = mesas.get(pedido.mesa_id) if pedido.mesa_id else None
        lines = build_kitchen_ticket_lines(
            mesa_label=_mesa_label(pedido, mesa),
            pedido_id=pid,
            items=[
                TicketLine(
                    name=(
                        productos.get(d["producto_id"]).nombre
                        if productos.get(d["producto_id"])
                        else f"Producto {d['producto_id']}"
                    ),
                    quantity=d["cantidad"],
                    note=d["notas"] or "",
                )
                for d in dets
            ],
            paper_width_mm=width,
        )
        trabajos.append(
            encolar_trabajo(
                session,
                company_id=company_id,
                sucursal_id=pedido.sucursal_id,
                rol=RolImpresora.COCINA.value,
                tipo_doc=TipoDocumento.COMANDA.value,
                contenido=ticket_text(lines),
                paper_width_mm=width,
                pedido_id=pid,
                commit=False,
            )
        )
    session.commit()
    return trabajos
