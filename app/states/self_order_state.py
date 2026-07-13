"""Estado independiente para Self-Order QR — carrito del cliente final."""

from __future__ import annotations

from decimal import Decimal

import reflex as rx
from pydantic import BaseModel
from sqlmodel import select

from app.models.food import (
    ConfigImpresora,
    DetallePedido,
    EstadoPedido,
    Mesa,
    Pedido,
    Producto,
    TipoPedido,
)
from app.utils.db import get_session
from app.utils.tenant import tenant_bypass
from tuwayki_core.utils.timezone import utc_now_naive


# ── View models ───────────────────────────────────────────────────────────────

class CarritoItemView(BaseModel):
    producto_id: int = 0
    nombre: str = ""
    precio_texto: str = ""
    precio_float: float = 0.0
    cantidad: int = 1
    subtotal_texto: str = ""


# ── Helpers ───────────────────────────────────────────────────────────────────

def _recalculate_order_total_selforder(session, pedido: Pedido) -> Decimal:
    """Recalcula el total del pedido sumando subtotales de detalles."""
    detalles = session.exec(
        select(DetallePedido).where(DetallePedido.pedido_id == pedido.id)
    ).all()
    from datetime import datetime, timezone
    total = sum((Decimal(str(d.subtotal)) for d in detalles), Decimal("0.00"))
    pedido.total = total
    pedido.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
    session.add(pedido)
    return total


# ── State ─────────────────────────────────────────────────────────────────────

class SelfOrderState(rx.State):
    """Carrito y envío de pedido self-order QR — independiente de FoodState."""

    carrito: list[CarritoItemView] = []
    carrito_visible: bool = False
    mesa_token: str = ""
    mesa_nombre_qr: str = ""
    pedido_enviado: bool = False
    pedido_error: str = ""
    nombre_cliente_qr: str = ""

    # ── Computed vars ─────────────────────────────────────────────────────────

    @rx.var
    def carrito_count(self) -> int:
        return sum(i.cantidad for i in self.carrito)

    @rx.var
    def carrito_total_texto(self) -> str:
        total = sum(i.precio_float * i.cantidad for i in self.carrito)
        return f"S/ {total:.2f}"

    @rx.var
    def tiene_mesa_qr(self) -> bool:
        return self.mesa_token != "" and self.mesa_nombre_qr != ""

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def on_load(self) -> None:
        """Reset del carrito al cargar la página pública."""
        self.pedido_enviado = False
        self.pedido_error = ""
        self.carrito = []
        self.carrito_visible = False
        self._init_from_token()

    def _init_from_token(self) -> None:
        token = self.router.page.params.get("mesa", "")
        if not token:
            self.mesa_token = ""
            self.mesa_nombre_qr = ""
            return
        slug = self.router.page.params.get("slug", "")
        if not slug:
            return
        with tenant_bypass(), get_session() as session:
            cfg = session.exec(
                select(ConfigImpresora).where(ConfigImpresora.slug == slug)
            ).first()
            if not cfg:
                return
            mesa = session.exec(
                select(Mesa).where(
                    Mesa.company_id == cfg.company_id,
                    Mesa.qr_token == token,
                    Mesa.activa.is_(True),
                )
            ).first()
            if mesa:
                self.mesa_token = token
                self.mesa_nombre_qr = mesa.nombre or f"Mesa {mesa.numero}"

    # ── Cart actions ──────────────────────────────────────────────────────────

    def agregar_al_carrito(self, producto_id: int, nombre: str, precio_texto: str, precio_float: float) -> None:
        for i, item in enumerate(self.carrito):
            if item.producto_id == producto_id:
                nuevo = item.model_copy()
                nuevo.cantidad += 1
                nuevo.subtotal_texto = f"S/ {nuevo.precio_float * nuevo.cantidad:.2f}"
                self.carrito[i] = nuevo
                return
        self.carrito.append(CarritoItemView(
            producto_id=producto_id,
            nombre=nombre,
            precio_texto=precio_texto,
            precio_float=precio_float,
            cantidad=1,
            subtotal_texto=precio_texto,
        ))

    def quitar_del_carrito(self, producto_id: int) -> None:
        for i, item in enumerate(self.carrito):
            if item.producto_id == producto_id:
                if item.cantidad > 1:
                    nuevo = item.model_copy()
                    nuevo.cantidad -= 1
                    nuevo.subtotal_texto = f"S/ {nuevo.precio_float * nuevo.cantidad:.2f}"
                    self.carrito[i] = nuevo
                else:
                    self.carrito.pop(i)
                return

    def vaciar_carrito(self) -> None:
        self.carrito = []

    def toggle_carrito(self) -> None:
        self.carrito_visible = not self.carrito_visible

    def set_nombre_cliente_qr(self, v: str) -> None:
        self.nombre_cliente_qr = v

    def set_carrito_visible(self, v: bool) -> None:
        self.carrito_visible = v

    # ── Submit order ──────────────────────────────────────────────────────────

    def enviar_self_order(self) -> None:
        if not self.mesa_token or not self.carrito:
            return
        self.pedido_error = ""
        slug = self.router.page.params.get("slug", "")
        with tenant_bypass(), get_session() as session:
            cfg = session.exec(
                select(ConfigImpresora).where(ConfigImpresora.slug == slug)
            ).first()
            if not cfg:
                self.pedido_error = "Local no encontrado."
                return
            mesa = session.exec(
                select(Mesa).where(
                    Mesa.company_id == cfg.company_id,
                    Mesa.qr_token == self.mesa_token,
                    Mesa.activa.is_(True),
                )
            ).first()
            if not mesa:
                self.pedido_error = "Mesa no válida. Escanee el QR nuevamente."
                return
            pedido = Pedido(
                company_id=cfg.company_id,
                mesa_id=mesa.id,
                tipo_pedido=TipoPedido.MESA.value,
                nombre_cliente=self.nombre_cliente_qr.strip() or None,
                estado=EstadoPedido.ENVIADO.value,
                abierto_en=utc_now_naive(),
                self_order=True,
                self_order_aprobado=False,
                sucursal_id=mesa.sucursal_id,
            )
            session.add(pedido)
            session.flush()
            for item in self.carrito:
                producto = session.get(Producto, item.producto_id)
                if not producto or producto.company_id != cfg.company_id:
                    continue
                detalle = DetallePedido(
                    pedido_id=pedido.id,
                    company_id=cfg.company_id,
                    producto_id=item.producto_id,
                    cantidad=item.cantidad,
                    precio_unitario=producto.precio,
                    subtotal=producto.precio * item.cantidad,
                    impreso_cocina=False,
                )
                session.add(detalle)
            _recalculate_order_total_selforder(session, pedido)
            session.commit()
        self.carrito = []
        self.carrito_visible = False
        self.pedido_enviado = True

    def volver_a_carta(self) -> None:
        self.pedido_enviado = False
