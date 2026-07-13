"""Estado de Reservas + Delivery para el panel administrativo (dono.py)."""

from __future__ import annotations

from contextlib import contextmanager
from decimal import Decimal

import reflex as rx
from pydantic import BaseModel
from sqlmodel import select

from app.models.food import (
    DetallePedido,
    EstadoDelivery,
    EstadoPedido,
    EstadoReserva,
    Mesa,
    Pedido,
    Producto,
    Reserva,
    RolUsuario,
    TipoPedido,
    UsuarioFood,
)
from app.utils.db import get_session
from app.utils.tenant import set_tenant_context
from tuwayki_core.utils.timezone import utc_now_naive


# ─── Helpers ────────────────────────────────────────────────────────────────

CURRENCY_SYMBOL = "S/"


def _to_decimal(value) -> Decimal:
    if value is None:
        return Decimal("0.00")
    if isinstance(value, Decimal):
        return value.quantize(Decimal("0.01"))
    return Decimal(str(value)).quantize(Decimal("0.01"))


def _money_text(value) -> str:
    return f"{CURRENCY_SYMBOL} {_to_decimal(value):.2f}"


def _actor_name(value: str | None) -> str:
    return (value or "").strip()


def _list_fingerprint(items: list) -> tuple:
    """Fingerprint genérico para listas de BaseModel."""
    return tuple(item.model_dump_json() for item in items)


# ─── View models ─────────────────────────────────────────────────────────────

class ReservaView(BaseModel):
    id: int
    mesa_id: int = 0
    mesa_label: str = ""
    nombre_cliente: str
    telefono: str = ""
    fecha: str
    hora: str
    pax: int
    estado: str
    estado_label: str
    notas: str = ""
    badge_bg: str = ""
    badge_text: str = ""


class DeliveryPedidoView(BaseModel):
    pedido_id: int = 0
    nombre_cliente: str = ""
    delivery_direccion: str = ""
    delivery_telefono: str = ""
    delivery_estado: str = ""
    delivery_estado_label: str = ""
    repartidor_nombre: str = ""
    repartidor_id: int = 0
    total_texto: str = ""
    items_resumen: str = ""
    hora_texto: str = ""
    notas: str = ""
    badge_bg: str = ""
    badge_text: str = ""
    pagado: bool = False


# ─── State ───────────────────────────────────────────────────────────────────

class DonoOperacionesState(rx.State):
    """Estado independiente para Reservas + Delivery (usado solo en dono.py)."""

    # ── Reservas ──────────────────────────────────────────────────────────────
    reservas_lista: list[ReservaView] = []
    reservas_fecha_filtro: str = ""
    reserva_form_id: int = 0
    reserva_form_nombre: str = ""
    reserva_form_telefono: str = ""
    reserva_form_fecha: str = ""
    reserva_form_hora: str = "20:00"
    reserva_form_pax: int = 2
    reserva_form_mesa_id: int = 0
    reserva_form_notas: str = ""
    reserva_form_visible: bool = False

    # ── Delivery ─────────────────────────────────────────────────────────────
    deliveries_lista: list[DeliveryPedidoView] = []
    delivery_filtro_estado: str = ""
    delivery_form_visible: bool = False
    delivery_form_nombre: str = ""
    delivery_form_direccion: str = ""
    delivery_form_telefono: str = ""
    delivery_form_notas: str = ""
    delivery_form_repartidor_id: int = 0
    delivery_form_items: list[dict] = []

    # ── Tenant helpers ───────────────────────────────────────────────────────

    def _company_id(self) -> int:
        """Obtener company_id del FoodState padre."""
        from app.states.food_state import FoodState
        # En Reflex 0.9 los substates independientes acceden a otros via
        # async get_state, pero los handlers sync usan _get_state.
        # Usamos el acceso interno de Reflex al state manager.
        # Para event handlers sync: leemos del token del state.
        # Approach: guardamos company_id en un var propio al cargar.
        # Fallback: leer de FoodState via _get_state si disponible.
        return self._cached_company_id

    def _sucursal_id(self) -> int:
        return self._cached_sucursal_id

    def _sucursal_filter(self, model_class, query):
        sid = self._sucursal_id()
        if sid:
            return query.where(model_class.sucursal_id == sid)
        return query

    @contextmanager
    def _tenant_session(self):
        set_tenant_context(self._company_id(), None)
        with get_session() as session:
            session.info["tenant_bypass"] = True
            yield session

    # Cached tenant context (set on load)
    _cached_company_id: int = 0
    _cached_sucursal_id: int = 0

    async def _sync_tenant(self) -> None:
        """Sincronizar company_id y sucursal_id desde FoodState."""
        from app.states.food_state import FoodState
        food = await self.get_state(FoodState)
        self._cached_company_id = food._company_id()
        self._cached_sucursal_id = food._sucursal_id()

    # ─── Reservas de mesa ─────────────────────────────────────────────────────

    _RESERVA_BADGE = {
        "pendiente":  ("rgba(245,158,11,0.12)", "#F59E0B"),
        "confirmada": ("rgba(34,197,94,0.12)", "#22C55E"),
        "sentada":    ("rgba(59,130,246,0.12)", "#3B82F6"),
        "cancelada":  ("rgba(239,68,68,0.12)", "#F87171"),
        "no_show":    ("#334155", "#94A3B8"),
    }
    _RESERVA_LABEL = {
        "pendiente": "Pendiente",
        "confirmada": "Confirmada",
        "sentada": "Sentada",
        "cancelada": "Cancelada",
        "no_show": "No asistio",
    }

    def _reserva_to_view(self, r: Reserva, mesas_map: dict) -> ReservaView:
        bg, text = self._RESERVA_BADGE.get(r.estado, ("#F1F5F9", "#94A3B8"))
        mesa_label = ""
        if r.mesa_id and r.mesa_id in mesas_map:
            m = mesas_map[r.mesa_id]
            mesa_label = f"Mesa {m}"
        return ReservaView(
            id=r.id or 0,
            mesa_id=r.mesa_id or 0,
            mesa_label=mesa_label,
            nombre_cliente=r.nombre_cliente,
            telefono=r.telefono or "",
            fecha=r.fecha.isoformat() if r.fecha else "",
            hora=r.hora,
            pax=r.pax,
            estado=r.estado,
            estado_label=self._RESERVA_LABEL.get(r.estado, r.estado),
            notas=r.notas or "",
            badge_bg=bg,
            badge_text=text,
        )

    def cargar_reservas(self) -> None:
        from datetime import date as _date
        fecha_str = self.reservas_fecha_filtro or _date.today().isoformat()
        try:
            fecha = _date.fromisoformat(fecha_str)
        except ValueError:
            fecha = _date.today()
        with self._tenant_session() as session:
            q = select(Reserva).where(
                Reserva.company_id == self._company_id(),
                Reserva.fecha == fecha,
            ).order_by(Reserva.hora)
            q = self._sucursal_filter(Reserva, q)
            rows = session.exec(q).all()
            mesa_ids = {r.mesa_id for r in rows if r.mesa_id}
            mesas_map: dict[int, int] = {}
            if mesa_ids:
                for m in session.exec(select(Mesa).where(Mesa.id.in_(mesa_ids))).all():
                    mesas_map[m.id] = m.numero
        self.reservas_lista = [self._reserva_to_view(r, mesas_map) for r in rows]

    def set_reservas_fecha_filtro(self, v: str) -> None:
        self.reservas_fecha_filtro = v
        self.cargar_reservas()

    def abrir_form_reserva(self, reserva_id: int = 0) -> None:
        from datetime import date as _date
        if reserva_id:
            rv = next((r for r in self.reservas_lista if r.id == reserva_id), None)
            if rv:
                self.reserva_form_id = rv.id
                self.reserva_form_nombre = rv.nombre_cliente
                self.reserva_form_telefono = rv.telefono
                self.reserva_form_fecha = rv.fecha
                self.reserva_form_hora = rv.hora
                self.reserva_form_pax = rv.pax
                self.reserva_form_mesa_id = rv.mesa_id
                self.reserva_form_notas = rv.notas
        else:
            self.reserva_form_id = 0
            self.reserva_form_nombre = ""
            self.reserva_form_telefono = ""
            self.reserva_form_fecha = self.reservas_fecha_filtro or _date.today().isoformat()
            self.reserva_form_hora = "20:00"
            self.reserva_form_pax = 2
            self.reserva_form_mesa_id = 0
            self.reserva_form_notas = ""
        self.reserva_form_visible = True

    def cerrar_form_reserva(self) -> None:
        self.reserva_form_visible = False

    def set_reserva_form_visible(self, v: bool) -> None:
        self.reserva_form_visible = v

    def on_change_reserva_nombre(self, v: str) -> None:
        self.reserva_form_nombre = v

    def on_change_reserva_telefono(self, v: str) -> None:
        self.reserva_form_telefono = v

    def on_change_reserva_fecha(self, v: str) -> None:
        self.reserva_form_fecha = v

    def on_change_reserva_hora(self, v: str) -> None:
        self.reserva_form_hora = v

    def on_change_reserva_pax(self, v: str) -> None:
        try:
            self.reserva_form_pax = max(1, int(v))
        except ValueError:
            pass

    def on_change_reserva_mesa(self, v: str) -> None:
        try:
            self.reserva_form_mesa_id = int(v)
        except ValueError:
            self.reserva_form_mesa_id = 0

    def on_change_reserva_notas(self, v: str) -> None:
        self.reserva_form_notas = v

    def guardar_reserva(self) -> None:
        from datetime import date as _date
        nombre = self.reserva_form_nombre.strip()
        if not nombre:
            return rx.toast.error("El nombre del cliente es obligatorio.")
        if not self.reserva_form_fecha or not self.reserva_form_hora:
            return rx.toast.error("Fecha y hora son obligatorias.")
        try:
            fecha = _date.fromisoformat(self.reserva_form_fecha)
        except ValueError:
            return rx.toast.error("Fecha invalida.")
        company_id = self._company_id()
        with self._tenant_session() as session:
            if self.reserva_form_id:
                reserva = session.get(Reserva, self.reserva_form_id)
                if reserva and reserva.company_id == company_id:
                    reserva.nombre_cliente = nombre
                    reserva.telefono = self.reserva_form_telefono.strip()
                    reserva.fecha = fecha
                    reserva.hora = self.reserva_form_hora.strip()
                    reserva.pax = self.reserva_form_pax
                    reserva.mesa_id = self.reserva_form_mesa_id or None
                    reserva.notas = self.reserva_form_notas.strip() or None
                    session.add(reserva)
            else:
                reserva = Reserva(
                    company_id=company_id,
                    sucursal_id=self._sucursal_id() or None,
                    nombre_cliente=nombre,
                    telefono=self.reserva_form_telefono.strip(),
                    fecha=fecha,
                    hora=self.reserva_form_hora.strip(),
                    pax=self.reserva_form_pax,
                    mesa_id=self.reserva_form_mesa_id or None,
                    estado=EstadoReserva.PENDIENTE.value,
                    notas=self.reserva_form_notas.strip() or None,
                )
                session.add(reserva)
            session.commit()
        self.reserva_form_visible = False
        self.cargar_reservas()
        return rx.toast.success(f"Reserva de '{nombre}' guardada.")

    def cambiar_estado_reserva(self, reserva_id: int, nuevo_estado: str) -> None:
        company_id = self._company_id()
        with self._tenant_session() as session:
            reserva = session.get(Reserva, reserva_id)
            if reserva and reserva.company_id == company_id:
                reserva.estado = nuevo_estado
                session.add(reserva)
                session.commit()
        self.cargar_reservas()

    def confirmar_reserva(self, reserva_id: int) -> None:
        self.cambiar_estado_reserva(reserva_id, EstadoReserva.CONFIRMADA.value)

    def sentar_reserva(self, reserva_id: int) -> None:
        self.cambiar_estado_reserva(reserva_id, EstadoReserva.SENTADA.value)

    def cancelar_reserva(self, reserva_id: int) -> None:
        self.cambiar_estado_reserva(reserva_id, EstadoReserva.CANCELADA.value)

    def marcar_no_show(self, reserva_id: int) -> None:
        self.cambiar_estado_reserva(reserva_id, EstadoReserva.NO_SHOW.value)

    # ── Delivery ─────────────────────────────────────────────────────────────

    _DELIVERY_BADGE = {
        EstadoDelivery.PENDIENTE.value: ("Pendiente", "#F59E0B", "rgba(245,158,11,0.12)"),
        EstadoDelivery.EN_CAMINO.value: ("En camino", "#3B82F6", "rgba(59,130,246,0.12)"),
        EstadoDelivery.ENTREGADO.value: ("Entregado", "#22C55E", "rgba(34,197,94,0.12)"),
        EstadoDelivery.CANCELADO.value: ("Cancelado", "#F87171", "rgba(239,68,68,0.12)"),
    }

    def _delivery_to_view(self, pedido, detalles, productos, repartidores_map) -> DeliveryPedidoView:
        resumen = " · ".join(
            f"{d.cantidad}x {productos[d.producto_id].nombre if d.producto_id in productos else f'Producto {d.producto_id}'}"
            for d in detalles
        )
        hora = pedido.abierto_en or pedido.created_at
        estado = pedido.delivery_estado or EstadoDelivery.PENDIENTE.value
        label, bg, txt = self._DELIVERY_BADGE.get(estado, ("?", "#6B7280", "#F3F4F6"))
        rep_nombre = ""
        if pedido.delivery_repartidor_id and pedido.delivery_repartidor_id in repartidores_map:
            rep_nombre = repartidores_map[pedido.delivery_repartidor_id]
        return DeliveryPedidoView(
            pedido_id=pedido.id or 0,
            nombre_cliente=_actor_name(pedido.nombre_cliente) or "Sin nombre",
            delivery_direccion=pedido.delivery_direccion or "",
            delivery_telefono=pedido.delivery_telefono or "",
            delivery_estado=estado,
            delivery_estado_label=label,
            repartidor_nombre=rep_nombre,
            repartidor_id=pedido.delivery_repartidor_id or 0,
            total_texto=_money_text(pedido.total),
            items_resumen=resumen,
            hora_texto=hora.strftime("%H:%M") if hora else "",
            notas=pedido.delivery_notas or "",
            badge_bg=bg,
            badge_text=txt,
            pagado=bool(pedido.pagado),
        )

    def cargar_deliveries(self) -> None:
        with self._tenant_session() as session:
            q = select(Pedido).where(
                Pedido.company_id == self._company_id(),
                Pedido.tipo_pedido == TipoPedido.DELIVERY.value,
            )
            filtro = self.delivery_filtro_estado
            if filtro:
                q = q.where(Pedido.delivery_estado == filtro)
            else:
                q = q.where(Pedido.delivery_estado != EstadoDelivery.ENTREGADO.value)
            q = self._sucursal_filter(Pedido, q)
            q = q.order_by(Pedido.abierto_en.desc(), Pedido.id.desc())
            pedidos = session.exec(q).all()
            if not pedidos:
                if self.deliveries_lista:
                    self.deliveries_lista = []
                return
            productos = {p.id: p for p in session.exec(
                select(Producto).where(Producto.company_id == self._company_id())
            ).all()}
            repartidores = session.exec(
                select(UsuarioFood).where(
                    UsuarioFood.company_id == self._company_id(),
                    UsuarioFood.rol == RolUsuario.REPARTIDOR.value,
                )
            ).all()
            repartidores_map = {u.id: u.nombre for u in repartidores if u.id}
            result: list[DeliveryPedidoView] = []
            for pedido in pedidos:
                detalles = session.exec(
                    select(DetallePedido).where(DetallePedido.pedido_id == pedido.id).order_by(DetallePedido.id)
                ).all()
                result.append(self._delivery_to_view(pedido, detalles, productos, repartidores_map))
            if _list_fingerprint(result) != _list_fingerprint(self.deliveries_lista):
                self.deliveries_lista = result

    @rx.var
    def repartidores_lista(self) -> list[dict]:
        with self._tenant_session() as session:
            reps = session.exec(
                select(UsuarioFood).where(
                    UsuarioFood.company_id == self._company_id(),
                    UsuarioFood.rol == RolUsuario.REPARTIDOR.value,
                    UsuarioFood.activo.is_(True),
                )
            ).all()
            return [{"id": u.id or 0, "nombre": u.nombre} for u in reps]

    def set_delivery_filtro_estado(self, v: str) -> None:
        self.delivery_filtro_estado = v
        self.cargar_deliveries()

    def abrir_form_delivery(self) -> None:
        self.delivery_form_nombre = ""
        self.delivery_form_direccion = ""
        self.delivery_form_telefono = ""
        self.delivery_form_notas = ""
        self.delivery_form_repartidor_id = 0
        self.delivery_form_items = []
        self.delivery_form_visible = True

    def cerrar_form_delivery(self) -> None:
        self.delivery_form_visible = False

    def set_delivery_form_visible(self, v: bool) -> None:
        self.delivery_form_visible = v

    def on_change_delivery_nombre(self, v: str) -> None:
        self.delivery_form_nombre = v

    def on_change_delivery_direccion(self, v: str) -> None:
        self.delivery_form_direccion = v

    def on_change_delivery_telefono(self, v: str) -> None:
        self.delivery_form_telefono = v

    def on_change_delivery_notas(self, v: str) -> None:
        self.delivery_form_notas = v

    def on_change_delivery_repartidor(self, v: str) -> None:
        try:
            self.delivery_form_repartidor_id = int(v)
        except (ValueError, TypeError):
            self.delivery_form_repartidor_id = 0

    def crear_pedido_delivery(self) -> None:
        nombre = self.delivery_form_nombre.strip()
        direccion = self.delivery_form_direccion.strip()
        telefono = self.delivery_form_telefono.strip()
        if not nombre or not direccion:
            return
        with self._tenant_session() as session:
            pedido = Pedido(
                company_id=self._company_id(),
                tipo_pedido=TipoPedido.DELIVERY.value,
                nombre_cliente=nombre,
                delivery_direccion=direccion,
                delivery_telefono=telefono,
                delivery_notas=self.delivery_form_notas.strip() or None,
                delivery_estado=EstadoDelivery.PENDIENTE.value,
                delivery_repartidor_id=self.delivery_form_repartidor_id or None,
                sucursal_id=self._sucursal_id() or None,
                estado=EstadoPedido.ENVIADO.value,
                abierto_en=utc_now_naive(),
            )
            session.add(pedido)
            session.commit()
        self.delivery_form_visible = False
        self.cargar_deliveries()

    def asignar_repartidor_delivery(self, pedido_id: int, repartidor_id: int) -> None:
        with self._tenant_session() as session:
            pedido = session.get(Pedido, pedido_id)
            if pedido and pedido.company_id == self._company_id():
                pedido.delivery_repartidor_id = repartidor_id or None
                session.add(pedido)
                session.commit()
        self.cargar_deliveries()

    def cambiar_estado_delivery(self, pedido_id: int, nuevo_estado: str) -> None:
        with self._tenant_session() as session:
            pedido = session.get(Pedido, pedido_id)
            if pedido and pedido.company_id == self._company_id():
                pedido.delivery_estado = nuevo_estado
                session.add(pedido)
                session.commit()
        self.cargar_deliveries()

    def delivery_marcar_en_camino(self, pedido_id: int) -> None:
        self.cambiar_estado_delivery(pedido_id, EstadoDelivery.EN_CAMINO.value)

    def delivery_marcar_entregado(self, pedido_id: int) -> None:
        self.cambiar_estado_delivery(pedido_id, EstadoDelivery.ENTREGADO.value)

    def delivery_cancelar(self, pedido_id: int) -> None:
        self.cambiar_estado_delivery(pedido_id, EstadoDelivery.CANCELADO.value)
