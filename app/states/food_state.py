"""Estado global de TUWAYKIFOOD — mozos, caja, cocina, mostrador, carta."""

from __future__ import annotations

import asyncio
import base64
import io
import os
import re
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation

import reflex as rx
from pydantic import BaseModel
from sqlmodel import select

from app.models.food import (
    Categoria,
    ConfigImpresora,
    DetallePedido,
    EstadoMesa,
    EstadoPedido,
    EstadoProduccion,
    Mesa,
    Pedido,
    Producto,
    RolUsuario,
    TipoPedido,
    UsuarioFood,
)
from app.services.printer_service import SilentPrinterService, TicketLine
from app.utils.db import get_session

# ─── Constantes de negocio ───────────────────────────────────────────────────
CURRENCY_SYMBOL = "S/"

OPEN_ORDER_STATES = (
    EstadoPedido.BORRADOR.value,
    EstadoPedido.ENVIADO.value,
    EstadoPedido.EN_PREPARACION.value,
    EstadoPedido.LISTO.value,
)

KITCHEN_VISIBLE_STATES = (
    EstadoProduccion.PENDIENTE.value,
    EstadoProduccion.EN_PREPARACION.value,
)

MESA_LABELS = {
    EstadoMesa.LIBRE.value: "Libre",
    EstadoMesa.OCUPADA.value: "Ocupada",
    EstadoMesa.ESPERANDO_CUENTA.value: "Esperando cuenta",
}
MESA_BADGE_BACKGROUNDS = {
    EstadoMesa.LIBRE.value: "#DCFCE7",
    EstadoMesa.OCUPADA.value: "#FEE2E2",
    EstadoMesa.ESPERANDO_CUENTA.value: "#FEF3C7",
}
MESA_BADGE_TEXTS = {
    EstadoMesa.LIBRE.value: "#15803D",
    EstadoMesa.OCUPADA.value: "#B91C1C",
    EstadoMesa.ESPERANDO_CUENTA.value: "#B45309",
}
MESA_CARD_BACKGROUNDS = {
    EstadoMesa.LIBRE.value: "#F0FDF4",
    EstadoMesa.OCUPADA.value: "#FEF2F2",
    EstadoMesa.ESPERANDO_CUENTA.value: "#FFFBEB",
}
MESA_CARD_BORDERS = {
    EstadoMesa.LIBRE.value: "1px solid #BBF7D0",
    EstadoMesa.OCUPADA.value: "1px solid #FECACA",
    EstadoMesa.ESPERANDO_CUENTA.value: "1px solid #FDE68A",
}
READY_ALERT_BORDER = "3px solid #F59E0B"

PRODUCTION_LABELS = {
    EstadoProduccion.PENDIENTE.value: "Pendiente",
    EstadoProduccion.EN_PREPARACION.value: "En preparacion",
    EstadoProduccion.LISTO_PARA_ENTREGAR.value: "Listo para entregar",
    EstadoProduccion.ENTREGADO_AL_CLIENTE.value: "Entregado al cliente",
}
PRODUCTION_BADGE_BACKGROUNDS = {
    EstadoProduccion.PENDIENTE.value: "#FEF3C7",
    EstadoProduccion.EN_PREPARACION.value: "#FFEDD5",
    EstadoProduccion.LISTO_PARA_ENTREGAR.value: "#DCFCE7",
    EstadoProduccion.ENTREGADO_AL_CLIENTE.value: "#DBEAFE",
}
PRODUCTION_BADGE_TEXTS = {
    EstadoProduccion.PENDIENTE.value: "#B45309",
    EstadoProduccion.EN_PREPARACION.value: "#9A3412",
    EstadoProduccion.LISTO_PARA_ENTREGAR.value: "#15803D",
    EstadoProduccion.ENTREGADO_AL_CLIENTE.value: "#1D4ED8",
}
KITCHEN_CARD_BACKGROUNDS = {
    EstadoProduccion.PENDIENTE.value: "#FFFBEB",
    EstadoProduccion.EN_PREPARACION.value: "#FFF7ED",
}
KITCHEN_CARD_BORDERS = {
    EstadoProduccion.PENDIENTE.value: "#FDE68A",
    EstadoProduccion.EN_PREPARACION.value: "#FED7AA",
}

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
}

_ROL_LABELS: dict[str, str] = {
    RolUsuario.ADMIN.value: "Admin",
    RolUsuario.MOZO.value: "Mozo",
    RolUsuario.CAJA.value: "Caja",
    RolUsuario.COCINA.value: "Cocina",
}
_ROL_BADGE_BG: dict[str, str] = {
    RolUsuario.ADMIN.value: "#FFEDD5",
    RolUsuario.MOZO.value: "#DBEAFE",
    RolUsuario.CAJA.value: "#DCFCE7",
    RolUsuario.COCINA.value: "#FEF3C7",
}
_ROL_BADGE_TEXT: dict[str, str] = {
    RolUsuario.ADMIN.value: "#9A3412",
    RolUsuario.MOZO.value: "#1D4ED8",
    RolUsuario.CAJA.value: "#15803D",
    RolUsuario.COCINA.value: "#B45309",
}

# company_id y base URL leídos del entorno en tiempo de importación
_COMPANY_ID: int = int(os.getenv("FOOD_COMPANY_ID", "0") or "0")
_FOOD_BASE_URL: str = os.getenv("FOOD_BASE_URL", "http://localhost:3003").rstrip("/")


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


def _get_open_order(session, mesa_id: int) -> Pedido | None:
    return session.exec(
        select(Pedido).where(
            Pedido.company_id == _COMPANY_ID,
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
    pedido.updated_at = datetime.utcnow()
    session.add(pedido)
    return total


def _sync_order_status(session, pedido: Pedido) -> None:
    sent_details = session.exec(
        select(DetallePedido).where(
            DetallePedido.pedido_id == pedido.id,
            DetallePedido.impreso_cocina.is_(True),
        )
    ).all()
    if not sent_details:
        pedido.estado = EstadoPedido.BORRADOR.value
    elif any(d.estado_produccion == EstadoProduccion.LISTO_PARA_ENTREGAR.value for d in sent_details):
        pedido.estado = EstadoPedido.LISTO.value
    elif any(d.estado_produccion == EstadoProduccion.EN_PREPARACION.value for d in sent_details):
        pedido.estado = EstadoPedido.EN_PREPARACION.value
    elif any(d.estado_produccion == EstadoProduccion.PENDIENTE.value for d in sent_details):
        pedido.estado = EstadoPedido.ENVIADO.value
    elif pedido.pagado and all(d.estado_produccion == EstadoProduccion.ENTREGADO_AL_CLIENTE.value for d in sent_details):
        pedido.estado = EstadoPedido.COBRADO.value
    else:
        pedido.estado = EstadoPedido.ENVIADO.value
    pedido.updated_at = datetime.utcnow()
    session.add(pedido)


def _ensure_open_order(session, mesa: Mesa, mozo_id: int | None = None) -> Pedido:
    pedido = _get_open_order(session, mesa.id or 0)
    if pedido is not None:
        if mozo_id is not None and pedido.mozo_id is None:
            pedido.mozo_id = mozo_id
            pedido.updated_at = datetime.utcnow()
            session.add(pedido)
        return pedido
    pedido = Pedido(
        company_id=_COMPANY_ID,
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


class UsuarioSesion(BaseModel):
    id: int
    nombre: str
    rol: str


class CategoriaView(BaseModel):
    id: int
    nombre: str
    descripcion: str
    orden: int
    activa: bool


class ProductoView(BaseModel):
    id: int
    categoria_id: int
    categoria_nombre: str
    nombre: str
    descripcion: str
    precio: float
    precio_texto: str
    disponible: bool


class CarritoItem(BaseModel):
    producto_id: int
    nombre: str
    cantidad: int
    precio_unitario: float
    subtotal: float
    subtotal_texto: str
    nota: str = ""


class HistorialItem(BaseModel):
    detalle_id: int
    nombre: str
    cantidad: int
    precio_unitario_texto: str
    subtotal_texto: str
    nota: str
    enviado_en_texto: str
    estado_clave: str
    estado_label: str
    estado_bg: str
    estado_color: str
    preparado_por_nombre: str
    puede_entregar: bool


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
    items_lines: list[str]


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


class TopPlatoView(BaseModel):
    nombre: str
    cantidad: int
    total_generado: float
    total_texto: str


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


# ─── Estado principal ─────────────────────────────────────────────────────────

class FoodState(rx.State):
    """Estado global de la app TUWAYKIFOOD."""

    mesas: list[MesaView] = []
    categorias: list[CategoriaView] = []
    productos: list[ProductoView] = []
    carrito: list[CarritoItem] = []
    mostrador_carrito: list[CarritoItem] = []
    historial_pedido: list[HistorialItem] = []
    tickets_cocina: list[CocinaTicketView] = []
    historial_ventas: list[VentaHistorialView] = []
    pedidos_mostrador_listos: list[MostradorEntregaView] = []
    pedidos_mostrador_entregados: list[MostradorEntregadoView] = []

    mesa_seleccionada_id: int = 0
    mesa_atendida_por_nombre: str = ""
    categoria_activa_id: int = 0
    mostrador_categoria_activa_id: int = 0
    mostrador_cliente_nombre: str = ""
    ultimo_pedido_id: int = 0
    mensaje: str = ""
    usuario_actual: UsuarioSesion | None = None
    login_pin_input: str = ""
    sidebar_collapsed: bool = False

    categoria_form_id: int = 0
    categoria_form_nombre: str = ""
    categoria_form_descripcion: str = ""
    categoria_form_orden: str = "1"

    producto_form_id: int = 0
    producto_form_categoria_nombre: str = ""
    producto_form_nombre: str = ""
    producto_form_descripcion: str = ""
    producto_form_precio: str = ""
    producto_form_disponible: bool = True

    mozos_polling_enabled: bool = False
    cocina_polling_enabled: bool = False
    caja_polling_enabled: bool = False
    mostrador_polling_enabled: bool = False

    usuarios_admin: list[UsuarioAdminView] = []
    usuario_form_id: int = 0
    usuario_form_nombre: str = ""
    usuario_form_rol: str = RolUsuario.MOZO.value
    usuario_form_pin: str = ""
    usuario_form_pin_confirm: str = ""
    usuario_form_activo: bool = True

    mozos_tab_activa: str = "salon"
    nota_producto_activo_id: int = 0
    nota_input_temporal: str = ""

    # Caja — flujo de cobro con método de pago
    caja_cobro_mesa_id: int = 0
    caja_cobro_metodo: str = "efectivo"
    caja_cobro_propina: str = ""
    caja_cobro_efectivo_recibido: str = ""

    # Dashboard KPIs
    dashboard_ventas_hoy_texto: str = "S/ 0.00"
    dashboard_pedidos_hoy: int = 0
    dashboard_mesas_ocupadas: int = 0
    dashboard_propina_hoy_texto: str = "S/ 0.00"
    dashboard_top_platos: list[TopPlatoView] = []

    # Historial — filtros
    historial_filtro_fecha_desde: str = ""
    historial_filtro_fecha_hasta: str = ""
    historial_filtro_metodo: str = ""

    # Configuración impresoras + carta digital
    config_nombre_local: str = "Mi Restaurante"
    config_cocina_activa: bool = False
    config_cocina_ip: str = "192.168.1.100"
    config_cocina_puerto: str = "9100"
    config_caja_activa: bool = False
    config_caja_ip: str = ""
    config_caja_puerto: str = "9100"
    config_slug: str = "mi-restaurante"
    config_menu_qr_base64: str = ""
    config_menu_url: str = ""

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
        return self.usuario_actual.rol in ROLE_ALLOWED_ROUTES["mozos"]

    @rx.var
    def puede_ver_caja(self) -> bool:
        if self.usuario_actual is None:
            return False
        return self.usuario_actual.rol in ROLE_ALLOWED_ROUTES["caja"]

    @rx.var
    def puede_ver_mostrador(self) -> bool:
        if self.usuario_actual is None:
            return False
        return self.usuario_actual.rol in ROLE_ALLOWED_ROUTES["mostrador"]

    @rx.var
    def puede_ver_cocina(self) -> bool:
        if self.usuario_actual is None:
            return False
        return self.usuario_actual.rol in ROLE_ALLOWED_ROUTES["cocina"]

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
    def historial_filtro_activo(self) -> bool:
        return bool(
            self.historial_filtro_fecha_desde
            or self.historial_filtro_fecha_hasta
            or self.historial_filtro_metodo
        )

    @rx.var
    def puede_ver_usuarios(self) -> bool:
        if self.usuario_actual is None:
            return False
        return self.usuario_actual.rol in ROLE_ALLOWED_ROUTES["usuarios"]

    @rx.var
    def roles_disponibles(self) -> list[str]:
        return [r.value for r in RolUsuario]

    @rx.var
    def usuario_form_es_edicion(self) -> bool:
        return self.usuario_form_id > 0

    @rx.var
    def mesa_seleccionada_label(self) -> str:
        mesa = next((m for m in self.mesas if m.id == self.mesa_seleccionada_id), None)
        return mesa.nombre if mesa else "Sin mesa"

    @rx.var
    def mesa_seleccionada_total_texto(self) -> str:
        mesa = next((m for m in self.mesas if m.id == self.mesa_seleccionada_id), None)
        return mesa.total_abierto_texto if mesa else _money_text(0)

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
    def mesas_con_alerta_entrega(self) -> int:
        return sum(1 for m in self.mesas if m.tiene_items_listos)

    @rx.var
    def categorias_activas(self) -> list[CategoriaView]:
        return [c for c in self.categorias if c.activa]

    @rx.var
    def categorias_activas_nombres(self) -> list[str]:
        return [c.nombre for c in self.categorias if c.activa]

    @rx.var
    def productos_filtrados(self) -> list[ProductoView]:
        if self.categoria_activa_id == 0:
            return [p for p in self.productos if p.disponible]
        return [p for p in self.productos if p.disponible and p.categoria_id == self.categoria_activa_id]

    @rx.var
    def mostrador_productos_filtrados(self) -> list[ProductoView]:
        if self.mostrador_categoria_activa_id == 0:
            return [p for p in self.productos if p.disponible]
        return [p for p in self.productos if p.disponible and p.categoria_id == self.mostrador_categoria_activa_id]

    @rx.var
    def total_mostrador_texto(self) -> str:
        total = sum(_to_decimal(item.subtotal) for item in self.mostrador_carrito)
        return _money_text(total)

    @rx.var
    def caja_cobro_activo(self) -> bool:
        return self.caja_cobro_mesa_id > 0

    @rx.var
    def caja_cobro_mesa_nombre(self) -> str:
        mesa = next((m for m in self.mesas if m.id == self.caja_cobro_mesa_id), None)
        return mesa.nombre if mesa else ""

    @rx.var
    def caja_cobro_total_base(self) -> float:
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
    def caja_cobro_total_final(self) -> float:
        return round(self.caja_cobro_total_base + self.caja_cobro_propina_decimal, 2)

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
        self.cargar_pedidos_mostrador_listos()
        self.cargar_pedidos_mostrador_entregados()
        self.mensaje = "Datos actualizados."

    def _clear_operational_context(self) -> None:
        self.mesas = []
        self.categorias = []
        self.productos = []
        self.carrito = []
        self.mostrador_carrito = []
        self.historial_pedido = []
        self.tickets_cocina = []
        self.historial_ventas = []
        self.pedidos_mostrador_listos = []
        self.pedidos_mostrador_entregados = []
        self.mesa_seleccionada_id = 0
        self.mesa_atendida_por_nombre = ""
        self.categoria_activa_id = 0
        self.mostrador_categoria_activa_id = 0
        self.mostrador_cliente_nombre = ""
        self.ultimo_pedido_id = 0
        self.mensaje = ""
        self.login_pin_input = ""
        self.sidebar_collapsed = False
        self.mozos_polling_enabled = False
        self.cocina_polling_enabled = False
        self.caja_polling_enabled = False
        self.mostrador_polling_enabled = False
        self.usuarios_admin = []
        self._limpiar_usuario_form()
        self.caja_cobro_mesa_id = 0
        self.caja_cobro_metodo = "efectivo"
        self.caja_cobro_propina = ""
        self.caja_cobro_efectivo_recibido = ""

    # ─── Navegación / Shell ───────────────────────────────────────────────────

    def toggle_sidebar(self) -> None:
        self.sidebar_collapsed = not self.sidebar_collapsed

    def _route_access_result(self, route_key: str):
        if self.usuario_actual is None:
            return rx.redirect("/login", replace=True)
        if self.usuario_actual.rol not in ROLE_ALLOWED_ROUTES[route_key]:
            return [
                rx.window_alert("No tienes permisos para este modulo."),
                rx.redirect(self.usuario_home_route, replace=True),
            ]
        self.cargar_datos_iniciales()
        return None

    def on_load_root(self):
        if self.usuario_actual is None:
            return rx.redirect("/login", replace=True)
        return rx.redirect(self.usuario_home_route, replace=True)

    def on_load_login(self):
        self.login_pin_input = ""
        if self.usuario_actual is not None:
            return rx.redirect(self.usuario_home_route, replace=True)
        return None

    def on_load_mozos(self):
        return self._route_access_result("mozos")

    def on_load_caja(self):
        return self._route_access_result("caja")

    def on_load_mostrador(self):
        result = self._route_access_result("mostrador")
        if result is not None:
            return result
        self.cargar_pedidos_mostrador_listos()
        self.cargar_pedidos_mostrador_entregados()
        return None

    def on_load_cocina(self):
        return self._route_access_result("cocina")

    def on_load_carta(self):
        return self._route_access_result("carta")

    def on_load_reportes(self):
        result = self._route_access_result("reportes")
        if result is not None:
            return result
        self.cargar_dashboard()
        self.cargar_historial_ventas()
        return None

    def on_load_usuarios(self):
        if self.usuario_actual is None:
            return rx.redirect("/login", replace=True)
        if self.usuario_actual.rol not in ROLE_ALLOWED_ROUTES["usuarios"]:
            return [
                rx.window_alert("No tienes permisos para este modulo."),
                rx.redirect(self.usuario_home_route, replace=True),
            ]
        self.cargar_usuarios_admin()
        self._limpiar_usuario_form()
        return None

    def on_load_configuracion(self):
        result = self._route_access_result("configuracion")
        if result is not None:
            return result
        self.cargar_config_impresora()
        return None

    # ─── Autenticación (PIN + company_id) ────────────────────────────────────

    def set_login_pin(self, value: str) -> None:
        self.login_pin_input = _normalize_pin(value)

    def append_login_digit(self, digit: str) -> None:
        if not digit.isdigit() or len(self.login_pin_input) >= 6:
            return
        self.login_pin_input = f"{self.login_pin_input}{digit}"

    def backspace_login_pin(self) -> None:
        self.login_pin_input = self.login_pin_input[:-1]

    def clear_login_pin(self) -> None:
        self.login_pin_input = ""

    def _authenticate_with_pin(self, pin: str):
        normalized = _normalize_pin(pin)
        if len(normalized) < 4:
            self.login_pin_input = ""
            return rx.window_alert("Ingresa un PIN valido de 4 a 6 digitos.")
        with get_session() as session:
            usuario = session.exec(
                select(UsuarioFood).where(
                    UsuarioFood.company_id == _COMPANY_ID,
                    UsuarioFood.pin == normalized,
                    UsuarioFood.activo.is_(True),
                )
            ).first()
        if usuario is None:
            self.login_pin_input = ""
            return rx.window_alert("PIN incorrecto. Intenta nuevamente.")
        self.usuario_actual = UsuarioSesion(
            id=usuario.id or 0,
            nombre=usuario.nombre,
            rol=usuario.rol,
        )
        self.login_pin_input = ""
        self.mensaje = f"Sesion iniciada como {usuario.nombre}."
        return rx.redirect(_role_home_route(usuario.rol), replace=True)

    def login(self, pin: str):
        return self._authenticate_with_pin(pin)

    def submit_login_pin(self):
        return self._authenticate_with_pin(self.login_pin_input)

    def logout(self):
        self.usuario_actual = None
        self._clear_operational_context()
        return rx.redirect("/login", replace=True)

    # ─── Gestión de usuarios del local ───────────────────────────────────────

    def on_change_uf_nombre(self, value: str) -> None:
        self.usuario_form_nombre = value

    def on_change_uf_rol(self, value: str) -> None:
        self.usuario_form_rol = value

    def on_change_uf_pin(self, value: str) -> None:
        self.usuario_form_pin = value

    def on_change_uf_pin_confirm(self, value: str) -> None:
        self.usuario_form_pin_confirm = value

    def toggle_uf_activo(self) -> None:
        self.usuario_form_activo = not self.usuario_form_activo

    def _limpiar_usuario_form(self) -> None:
        self.usuario_form_id = 0
        self.usuario_form_nombre = ""
        self.usuario_form_rol = RolUsuario.MOZO.value
        self.usuario_form_pin = ""
        self.usuario_form_pin_confirm = ""
        self.usuario_form_activo = True

    def cargar_usuarios_admin(self) -> None:
        mi_id = self.usuario_actual.id if self.usuario_actual else 0
        with get_session() as session:
            rows = session.exec(
                select(UsuarioFood)
                .where(UsuarioFood.company_id == _COMPANY_ID)
                .order_by(UsuarioFood.rol, UsuarioFood.nombre)
            ).all()
        self.usuarios_admin = [
            UsuarioAdminView(
                id=u.id or 0,
                nombre=u.nombre,
                rol=u.rol,
                rol_label=_ROL_LABELS.get(u.rol, u.rol),
                pin_masked="●" * len(u.pin),
                activo=u.activo,
                badge_bg=_ROL_BADGE_BG.get(u.rol, "rgba(100,116,139,0.16)"),
                badge_text=_ROL_BADGE_TEXT.get(u.rol, "#94A3B8"),
                es_yo=u.id == mi_id,
            )
            for u in rows
        ]

    def nuevo_usuario_form(self) -> None:
        self._limpiar_usuario_form()
        self.mensaje = ""

    def editar_usuario(self, user_id: int) -> None:
        with get_session() as session:
            u = session.get(UsuarioFood, user_id)
        if u is None or u.company_id != _COMPANY_ID:
            self.mensaje = "Usuario no encontrado."
            return
        self.usuario_form_id = u.id or 0
        self.usuario_form_nombre = u.nombre
        self.usuario_form_rol = u.rol
        self.usuario_form_pin = ""
        self.usuario_form_pin_confirm = ""
        self.usuario_form_activo = u.activo
        self.mensaje = ""

    def guardar_usuario(self) -> None:
        nombre = self.usuario_form_nombre.strip()
        if not nombre:
            self.mensaje = "El nombre es obligatorio."
            return
        rol = self.usuario_form_rol
        if rol not in [r.value for r in RolUsuario]:
            self.mensaje = "Rol invalido."
            return

        nuevo_pin = _normalize_pin(self.usuario_form_pin)
        es_edicion = self.usuario_form_id > 0

        if not es_edicion:
            if len(nuevo_pin) < 4:
                self.mensaje = "El PIN debe tener al menos 4 digitos."
                return
        else:
            if self.usuario_form_pin and len(nuevo_pin) < 4:
                self.mensaje = "El nuevo PIN debe tener al menos 4 digitos."
                return

        if self.usuario_form_pin:
            pin_confirm = _normalize_pin(self.usuario_form_pin_confirm)
            if nuevo_pin != pin_confirm:
                self.mensaje = "Los PINs no coinciden."
                return

        with get_session() as session:
            if es_edicion:
                u = session.get(UsuarioFood, self.usuario_form_id)
                if u is None or u.company_id != _COMPANY_ID:
                    self.mensaje = "Usuario no encontrado."
                    return
                if nuevo_pin:
                    conflicto = session.exec(
                        select(UsuarioFood).where(
                            UsuarioFood.company_id == _COMPANY_ID,
                            UsuarioFood.pin == nuevo_pin,
                            UsuarioFood.id != self.usuario_form_id,
                        )
                    ).first()
                    if conflicto:
                        self.mensaje = f"El PIN {nuevo_pin} ya lo usa {conflicto.nombre}."
                        return
                    u.pin = nuevo_pin
                u.nombre = nombre
                u.rol = rol
                u.activo = self.usuario_form_activo
                u.updated_at = datetime.utcnow()
                session.add(u)
                session.commit()
                self.mensaje = f"Usuario '{nombre}' actualizado."
            else:
                conflicto = session.exec(
                    select(UsuarioFood).where(
                        UsuarioFood.company_id == _COMPANY_ID,
                        UsuarioFood.pin == nuevo_pin,
                    )
                ).first()
                if conflicto:
                    self.mensaje = f"El PIN {nuevo_pin} ya lo usa {conflicto.nombre}."
                    return
                u = UsuarioFood(
                    company_id=_COMPANY_ID,
                    nombre=nombre,
                    pin=nuevo_pin,
                    rol=rol,
                    activo=True,
                )
                session.add(u)
                session.commit()
                self.mensaje = f"Usuario '{nombre}' creado."

        self._limpiar_usuario_form()
        self.cargar_usuarios_admin()

    def toggle_usuario_activo(self, user_id: int) -> None:
        mi_id = self.usuario_actual.id if self.usuario_actual else 0
        if user_id == mi_id:
            self.mensaje = "No puedes desactivarte a ti mismo."
            return
        with get_session() as session:
            u = session.get(UsuarioFood, user_id)
            if u is None or u.company_id != _COMPANY_ID:
                self.mensaje = "Usuario no encontrado."
                return
            if u.activo and u.rol == RolUsuario.ADMIN.value:
                admins_activos = session.exec(
                    select(UsuarioFood).where(
                        UsuarioFood.company_id == _COMPANY_ID,
                        UsuarioFood.rol == RolUsuario.ADMIN.value,
                        UsuarioFood.activo.is_(True),
                    )
                ).all()
                if len(admins_activos) <= 1:
                    self.mensaje = "No puedes desactivar al ultimo administrador."
                    return
            u.activo = not u.activo
            u.updated_at = datetime.utcnow()
            session.add(u)
            session.commit()
            accion = "activado" if u.activo else "desactivado"
            self.mensaje = f"Usuario '{u.nombre}' {accion}."
        self.cargar_usuarios_admin()

    def cancelar_usuario_form(self) -> None:
        self._limpiar_usuario_form()
        self.mensaje = ""

    # ─── Configuración impresoras ─────────────────────────────────────────────

    def cargar_config_impresora(self) -> None:
        with get_session() as session:
            cfg = session.exec(
                select(ConfigImpresora).where(ConfigImpresora.company_id == _COMPANY_ID)
            ).first()
            if cfg:
                self.config_nombre_local = cfg.nombre_local
                self.config_cocina_activa = cfg.cocina_activa
                self.config_cocina_ip = cfg.cocina_ip
                self.config_cocina_puerto = str(cfg.cocina_puerto)
                self.config_caja_activa = cfg.caja_activa
                self.config_caja_ip = cfg.caja_ip or ""
                self.config_caja_puerto = str(cfg.caja_puerto)
                self.config_slug = cfg.slug or "mi-restaurante"
                url = f"{_FOOD_BASE_URL}/menu/{self.config_slug}"
                self.config_menu_url = url
                self.config_menu_qr_base64 = _generar_qr_base64(url)

    def guardar_config_impresora(self) -> None:
        with get_session() as session:
            cfg = session.exec(
                select(ConfigImpresora).where(ConfigImpresora.company_id == _COMPANY_ID)
            ).first()
            if cfg is None:
                cfg = ConfigImpresora(company_id=_COMPANY_ID)
            cfg.nombre_local = self.config_nombre_local.strip() or "Mi Restaurante"
            cfg.cocina_activa = self.config_cocina_activa
            cfg.cocina_ip = self.config_cocina_ip.strip()
            try:
                cfg.cocina_puerto = int(self.config_cocina_puerto.strip())
            except (ValueError, AttributeError):
                cfg.cocina_puerto = 9100
            cfg.caja_activa = self.config_caja_activa
            cfg.caja_ip = self.config_caja_ip.strip()
            try:
                cfg.caja_puerto = int(self.config_caja_puerto.strip())
            except (ValueError, AttributeError):
                cfg.caja_puerto = 9100
            slug = _slugify(self.config_slug) if self.config_slug.strip() else _slugify(cfg.nombre_local)
            cfg.slug = slug
            cfg.updated_at = datetime.utcnow()
            session.add(cfg)
            session.commit()
        self.config_slug = slug
        url = f"{_FOOD_BASE_URL}/menu/{slug}"
        self.config_menu_url = url
        self.config_menu_qr_base64 = _generar_qr_base64(url)
        self.mensaje = "Configuracion guardada."

    def set_config_nombre_local(self, v: str) -> None:
        self.config_nombre_local = v

    def set_config_cocina_ip(self, v: str) -> None:
        self.config_cocina_ip = v

    def set_config_cocina_puerto(self, v: str) -> None:
        self.config_cocina_puerto = v

    def set_config_caja_ip(self, v: str) -> None:
        self.config_caja_ip = v

    def set_config_caja_puerto(self, v: str) -> None:
        self.config_caja_puerto = v

    def toggle_config_cocina_activa(self) -> None:
        self.config_cocina_activa = not self.config_cocina_activa

    def toggle_config_caja_activa(self) -> None:
        self.config_caja_activa = not self.config_caja_activa

    def set_config_slug(self, v: str) -> None:
        self.config_slug = v

    def _get_printer_service(self) -> "SilentPrinterService":
        try:
            with get_session() as session:
                cfg = session.exec(
                    select(ConfigImpresora).where(ConfigImpresora.company_id == _COMPANY_ID)
                ).first()
                if cfg is not None:
                    return SilentPrinterService.from_db_config(cfg)
        except Exception:
            pass
        return SilentPrinterService.from_env()

    # ─── Polling ──────────────────────────────────────────────────────────────

    def _refresh_mozos_slice(self) -> None:
        if self.usuario_actual is None:
            return
        self.cargar_mesas()
        if self.mesa_seleccionada_id:
            self._cargar_carrito_mesa(self.mesa_seleccionada_id)
            self._cargar_historial_mesa(self.mesa_seleccionada_id)

    def _refresh_cocina_slice(self) -> None:
        if self.usuario_actual is None:
            return
        self.cargar_cocina()
        self.cargar_mesas()

    def _refresh_caja_slice(self) -> None:
        if self.usuario_actual is None:
            return
        self.cargar_mesas()
        if self.mesa_seleccionada_id:
            self._cargar_historial_mesa(self.mesa_seleccionada_id)

    def _refresh_mostrador_slice(self) -> None:
        if self.usuario_actual is None:
            return
        self.cargar_pedidos_mostrador_listos()
        self.cargar_pedidos_mostrador_entregados()

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
                    refresh_callback()
            except Exception:
                break

    @rx.event(background=True)
    async def start_mozos_polling(self) -> None:
        await self._run_polling_loop("mozos_polling_enabled", 5, self._refresh_mozos_slice)

    def stop_mozos_polling(self) -> None:
        self.mozos_polling_enabled = False

    @rx.event(background=True)
    async def start_cocina_polling(self) -> None:
        await self._run_polling_loop("cocina_polling_enabled", 5, self._refresh_cocina_slice)

    def stop_cocina_polling(self) -> None:
        self.cocina_polling_enabled = False

    @rx.event(background=True)
    async def start_caja_polling(self) -> None:
        await self._run_polling_loop("caja_polling_enabled", 10, self._refresh_caja_slice)

    def stop_caja_polling(self) -> None:
        self.caja_polling_enabled = False

    @rx.event(background=True)
    async def start_mostrador_polling(self) -> None:
        await self._run_polling_loop("mostrador_polling_enabled", 5, self._refresh_mostrador_slice)

    def stop_mostrador_polling(self) -> None:
        self.mostrador_polling_enabled = False

    # ─── Mesas ───────────────────────────────────────────────────────────────

    def cargar_mesas(self) -> None:
        mesas_ui: list[MesaView] = []
        with get_session() as session:
            mesas_db = session.exec(
                select(Mesa).where(
                    Mesa.company_id == _COMPANY_ID,
                    Mesa.activa.is_(True),
                ).order_by(Mesa.numero)
            ).all()
            for mesa in mesas_db:
                pedido_abierto = _get_open_order(session, mesa.id or 0)
                total_abierto = _to_decimal(pedido_abierto.total if pedido_abierto else Decimal("0.00"))
                ready_details = _get_ready_details(session, pedido_abierto.id or 0) if pedido_abierto else []
                items_listos_count = sum(d.cantidad for d in ready_details)
                tiene_items_listos = items_listos_count > 0
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
                ))
        self.mesas = mesas_ui
        if self.mesa_seleccionada_id and not any(m.id == self.mesa_seleccionada_id for m in self.mesas):
            self.mesa_seleccionada_id = 0
            self.carrito = []
            self.historial_pedido = []

    # ─── Carta ────────────────────────────────────────────────────────────────

    def cargar_menu(self) -> None:
        with get_session() as session:
            categorias_db = session.exec(
                select(Categoria).where(Categoria.company_id == _COMPANY_ID).order_by(Categoria.orden, Categoria.nombre)
            ).all()
            productos_db = session.exec(
                select(Producto).where(Producto.company_id == _COMPANY_ID).order_by(Producto.nombre)
            ).all()
            categorias_map = {c.id: c.nombre for c in categorias_db}
            self.categorias = [
                CategoriaView(
                    id=c.id or 0,
                    nombre=c.nombre,
                    descripcion=c.descripcion or "",
                    orden=c.orden,
                    activa=c.activa,
                )
                for c in categorias_db
            ]
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
                )
                for p in productos_db
            ]

    def seleccionar_categoria(self, categoria_id: int) -> None:
        self.categoria_activa_id = categoria_id

    def seleccionar_mostrador_categoria(self, categoria_id: int) -> None:
        self.mostrador_categoria_activa_id = categoria_id

    # ─── Mozos — Selección de mesa ────────────────────────────────────────────

    def seleccionar_mesa(self, mesa_id: int) -> None:
        self.mesa_seleccionada_id = mesa_id
        self._cargar_carrito_mesa(mesa_id)
        self._cargar_historial_mesa(mesa_id)
        mesa = next((m for m in self.mesas if m.id == mesa_id), None)
        alerta = (
            f" {mesa.items_listos_count} items listos para entregar."
            if mesa and mesa.tiene_items_listos else ""
        )
        self.mensaje = f"{self.mesa_seleccionada_label} seleccionada. {self.cantidad_items_carrito} items pendientes.{alerta}"

    def _cargar_carrito_mesa(self, mesa_id: int) -> None:
        with get_session() as session:
            pedido = _get_open_order(session, mesa_id)
            if pedido is None:
                self.carrito = []
                return
            detalles = _get_unsent_details(session, pedido.id or 0)
            productos_map = {p.id: p for p in session.exec(select(Producto).where(Producto.company_id == _COMPANY_ID)).all()}
            self.carrito = [
                CarritoItem(
                    producto_id=d.producto_id,
                    nombre=(productos_map[d.producto_id].nombre if d.producto_id in productos_map else f"Producto {d.producto_id}"),
                    cantidad=d.cantidad,
                    precio_unitario=float(_to_decimal(d.precio_unitario)),
                    subtotal=float(_to_decimal(d.subtotal)),
                    subtotal_texto=_money_text(d.subtotal),
                    nota=d.notas or "",
                )
                for d in detalles
            ]

    def _cargar_historial_mesa(self, mesa_id: int) -> None:
        with get_session() as session:
            pedido = _get_open_order(session, mesa_id)
            if pedido is None:
                self.historial_pedido = []
                self.mesa_atendida_por_nombre = ""
                return
            detalles = session.exec(
                select(DetallePedido).where(
                    DetallePedido.pedido_id == pedido.id,
                    DetallePedido.impreso_cocina.is_(True),
                ).order_by(DetallePedido.enviado_cocina_at, DetallePedido.id)
            ).all()
            productos_map = {p.id: p for p in session.exec(select(Producto).where(Producto.company_id == _COMPANY_ID)).all()}
            usuarios_map = {u.id: u for u in session.exec(select(UsuarioFood).where(UsuarioFood.company_id == _COMPANY_ID)).all()}
            mozo = usuarios_map.get(pedido.mozo_id)
            self.mesa_atendida_por_nombre = _actor_name(mozo.nombre if mozo else "")
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
                    nota=d.notas or "",
                    enviado_en_texto=enviado_en.strftime("%H:%M"),
                    estado_clave=estado_produccion,
                    estado_label=PRODUCTION_LABELS.get(estado_produccion, estado_produccion),
                    estado_bg=PRODUCTION_BADGE_BACKGROUNDS.get(estado_produccion, "#E2E8F0"),
                    estado_color=PRODUCTION_BADGE_TEXTS.get(estado_produccion, "#334155"),
                    preparado_por_nombre=_actor_name(preparado_por.nombre if preparado_por else ""),
                    puede_entregar=(estado_produccion == EstadoProduccion.LISTO_PARA_ENTREGAR.value),
                ))
            self.historial_pedido = historial

    def agregar_producto(self, producto_id: int) -> None:
        if self.mesa_seleccionada_id == 0:
            self.mensaje = "Selecciona una mesa antes de agregar productos."
            return
        with get_session() as session:
            mesa = session.get(Mesa, self.mesa_seleccionada_id)
            if mesa is None or mesa.company_id != _COMPANY_ID:
                self.mensaje = "La mesa seleccionada ya no existe."
                return
            producto = session.get(Producto, producto_id)
            if producto is None or producto.company_id != _COMPANY_ID or not producto.disponible:
                self.mensaje = "Producto no disponible."
                return
            producto_nombre = producto.nombre
            pedido = _ensure_open_order(session, mesa, mozo_id=self.usuario_actual.id if self.usuario_actual else None)
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
                    company_id=_COMPANY_ID,
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
            mesa.updated_at = datetime.utcnow()
            session.add(mesa)
            session.commit()
        self._cargar_carrito_mesa(self.mesa_seleccionada_id)
        self._cargar_historial_mesa(self.mesa_seleccionada_id)
        self.cargar_mesas()
        self.mensaje = f"{producto_nombre} agregado a {self.mesa_seleccionada_label}."

    def restar_producto(self, producto_id: int) -> None:
        if self.mesa_seleccionada_id == 0:
            self.mensaje = "Selecciona una mesa antes de editar el carrito."
            return
        with get_session() as session:
            mesa = session.get(Mesa, self.mesa_seleccionada_id)
            if mesa is None:
                self.mensaje = "La mesa seleccionada ya no existe."
                return
            pedido = _get_open_order(session, mesa.id or 0)
            if pedido is None:
                self.mensaje = "No hay pedido abierto para esta mesa."
                return
            detalle = session.exec(
                select(DetallePedido).where(
                    DetallePedido.pedido_id == pedido.id,
                    DetallePedido.producto_id == producto_id,
                    DetallePedido.impreso_cocina.is_(False),
                ).order_by(DetallePedido.id.desc())
            ).first()
            if detalle is None:
                self.mensaje = "Ese producto ya fue enviado o no existe en el carrito."
                return
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
        self.mensaje = "Carrito actualizado."

    def _finalize_cart_cleanup(self, session, pedido: Pedido, mesa: Mesa) -> None:
        detalles_restantes = session.exec(
            select(DetallePedido).where(DetallePedido.pedido_id == pedido.id)
        ).all()
        if not detalles_restantes:
            session.delete(pedido)
            mesa.estado = EstadoMesa.LIBRE.value
            mesa.updated_at = datetime.utcnow()
            session.add(mesa)
            return
        _recalculate_order_total(session, pedido)
        _sync_order_status(session, pedido)
        mesa.estado = EstadoMesa.OCUPADA.value
        mesa.updated_at = datetime.utcnow()
        session.add(mesa)

    def limpiar_carrito(self) -> None:
        if self.mesa_seleccionada_id == 0:
            self.carrito = []
            self.mensaje = "No hay mesa seleccionada."
            return
        with get_session() as session:
            mesa = session.get(Mesa, self.mesa_seleccionada_id)
            if mesa is None:
                self.mensaje = "La mesa seleccionada ya no existe."
                return
            pedido = _get_open_order(session, mesa.id or 0)
            if pedido is None:
                self.carrito = []
                self.mensaje = "No hay pedido abierto para limpiar."
                return
            for d in _get_unsent_details(session, pedido.id or 0):
                session.delete(d)
            self._finalize_cart_cleanup(session, pedido, mesa)
            session.commit()
        self._cargar_carrito_mesa(self.mesa_seleccionada_id)
        self._cargar_historial_mesa(self.mesa_seleccionada_id)
        self.cargar_mesas()
        self.mensaje = "Items pendientes eliminados."

    # ─── Notas ────────────────────────────────────────────────────────────────

    def set_mozos_tab(self, tab: str) -> None:
        self.mozos_tab_activa = tab

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
        with get_session() as session:
            pedido = _get_open_order(session, self.mesa_seleccionada_id)
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
                self.mensaje = "El item ya fue enviado a cocina; no se puede editar."
                self.nota_producto_activo_id = 0
                return
            detalle.notas = nota or None
            detalle.updated_at = datetime.utcnow()
            session.add(detalle)
            session.commit()
        self.nota_producto_activo_id = 0
        self.nota_input_temporal = ""
        self._cargar_carrito_mesa(self.mesa_seleccionada_id)
        self.mensaje = "Nota guardada." if nota else "Nota eliminada."

    def cerrar_nota_item(self) -> None:
        self.nota_producto_activo_id = 0
        self.nota_input_temporal = ""

    # ─── Enviar a cocina ─────────────────────────────────────────────────────

    def solicitar_cuenta(self) -> None:
        if self.mesa_seleccionada_id == 0:
            self.mensaje = "Selecciona una mesa antes de solicitar cuenta."
            return
        if self.cantidad_items_carrito > 0:
            self.mensaje = "Primero envia a cocina los items pendientes."
            return
        with get_session() as session:
            mesa = session.get(Mesa, self.mesa_seleccionada_id)
            if mesa is None:
                self.mensaje = "La mesa seleccionada ya no existe."
                return
            pedido = _get_open_order(session, mesa.id or 0)
            if pedido is None or _to_decimal(pedido.total) <= 0:
                self.mensaje = "No hay consumo pendiente en esa mesa."
                return
            if _get_not_delivered_details(session, pedido.id or 0):
                self.mensaje = "Todavia hay items en cocina o listos por entregar."
                return
            mesa.estado = EstadoMesa.ESPERANDO_CUENTA.value
            mesa.updated_at = datetime.utcnow()
            session.add(mesa)
            session.commit()
        self.cargar_mesas()
        self.mensaje = f"{self.mesa_seleccionada_label} marcada para cobrar."

    def enviar_pedido(self) -> None:
        if self.mesa_seleccionada_id == 0:
            self.mensaje = "Selecciona una mesa antes de enviar el pedido."
            return
        pedido_id = 0
        mesa_label = ""
        ticket_lines: list[TicketLine] = []
        with get_session() as session:
            mesa = session.get(Mesa, self.mesa_seleccionada_id)
            if mesa is None:
                self.mensaje = "La mesa seleccionada ya no existe."
                return
            pedido = _get_open_order(session, mesa.id or 0)
            if pedido is None:
                self.mensaje = "No hay items pendientes para enviar."
                return
            if self.usuario_actual and pedido.mozo_id is None:
                pedido.mozo_id = self.usuario_actual.id
                pedido.updated_at = datetime.utcnow()
                session.add(pedido)
            detalles_pendientes = _get_unsent_details(session, pedido.id or 0)
            if not detalles_pendientes:
                self.mensaje = "No hay items nuevos pendientes de enviar."
                return
            productos_map = {p.id: p for p in session.exec(select(Producto).where(Producto.company_id == _COMPANY_ID)).all()}
            now = datetime.utcnow()
            for d in detalles_pendientes:
                producto = productos_map.get(d.producto_id)
                ticket_lines.append(TicketLine(
                    name=producto.nombre if producto else f"Producto {d.producto_id}",
                    quantity=d.cantidad,
                    unit_price=float(_to_decimal(d.precio_unitario)),
                    subtotal=float(_to_decimal(d.subtotal)),
                    note=d.notas or "",
                ))
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
        try:
            self._get_printer_service().print_kitchen_ticket(
                mesa_label=mesa_label, pedido_id=pedido_id, items=ticket_lines,
            )
        except Exception as error:
            self.mensaje = f"Pedido #{pedido_id} guardado. Fallo impresion cocina: {error}"
            return
        self.mensaje = f"Pedido #{pedido_id} enviado correctamente."

    # ─── Cocina (KDS) ────────────────────────────────────────────────────────

    def cargar_cocina(self) -> None:
        with get_session() as session:
            detalles = session.exec(
                select(DetallePedido).where(
                    DetallePedido.company_id == _COMPANY_ID,
                    DetallePedido.impreso_cocina.is_(True),
                    DetallePedido.estado_produccion.in_(KITCHEN_VISIBLE_STATES),
                ).order_by(DetallePedido.enviado_cocina_at, DetallePedido.id)
            ).all()
            pedido_ids = {d.pedido_id for d in detalles}
            pedidos = {p.id: p for p in session.exec(select(Pedido).where(Pedido.id.in_(pedido_ids))).all()}
            mesas = {m.id: m for m in session.exec(select(Mesa).where(Mesa.company_id == _COMPANY_ID)).all()}
            usuarios = {u.id: u for u in session.exec(select(UsuarioFood).where(UsuarioFood.company_id == _COMPANY_ID)).all()}
            productos = {p.id: p for p in session.exec(select(Producto).where(Producto.company_id == _COMPANY_ID)).all()}
            grupos: dict = {}
            for d in detalles:
                pedido = pedidos.get(d.pedido_id)
                if pedido is None:
                    continue
                marca = d.enviado_cocina_at or d.updated_at
                lote = marca.isoformat()
                estado_produccion = d.estado_produccion or EstadoProduccion.PENDIENTE.value
                mozo = usuarios.get(pedido.mozo_id)
                key = (pedido.id or 0, lote, estado_produccion)
                if key not in grupos:
                    grupos[key] = {
                        "pedido_id": pedido.id or 0,
                        "mesa_label": _pedido_kitchen_label(pedido, mesas),
                        "hora_texto": marca.strftime("%H:%M"),
                        "estado_produccion": estado_produccion,
                        "estado_label": PRODUCTION_LABELS.get(estado_produccion, estado_produccion),
                        "estado_bg": PRODUCTION_BADGE_BACKGROUNDS.get(estado_produccion, "#E2E8F0"),
                        "estado_color": PRODUCTION_BADGE_TEXTS.get(estado_produccion, "#334155"),
                        "mozo_nombre": _actor_name(mozo.nombre if mozo else ""),
                        "action_label": (
                            "Empezar a Preparar"
                            if estado_produccion == EstadoProduccion.PENDIENTE.value
                            else "Marcar como Listo"
                        ),
                        "accent_bg": KITCHEN_CARD_BACKGROUNDS.get(estado_produccion, "#FFF7ED"),
                        "accent_border": KITCHEN_CARD_BORDERS.get(estado_produccion, "#FCD34D"),
                        "detalle_ids": [],
                        "items_lines": [],
                    }
                producto = productos.get(d.producto_id)
                line = f"{d.cantidad} x {producto.nombre if producto else f'Producto {d.producto_id}'}"
                if d.notas:
                    line = f"{line} · Nota: {d.notas}"
                grupos[key]["items_lines"].append(line)
                grupos[key]["detalle_ids"].append(str(d.id or 0))
            self.tickets_cocina = [
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
                )
                for _, data in grupos.items()
            ]

    def _transition_ticket_state(self, detalle_ids_csv: str, source_state: str, target_state: str, success_message: str, actor_user_id: int | None = None, actor_field_name: str | None = None) -> None:
        ids = [int(x) for x in detalle_ids_csv.split(",") if x.strip()]
        if not ids:
            self.mensaje = "No se encontro el ticket de cocina."
            return
        with get_session() as session:
            detalles = session.exec(select(DetallePedido).where(DetallePedido.id.in_(ids))).all()
            actualizables = [d for d in detalles if d.impreso_cocina and d.estado_produccion == source_state]
            if not actualizables:
                self.mensaje = "El ticket ya cambio de estado."
                return
            pedidos_afectados: set[int] = set()
            now = datetime.utcnow()
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
        self.mensaje = success_message

    def iniciar_preparacion_ticket(self, detalle_ids_csv: str) -> None:
        self._transition_ticket_state(
            detalle_ids_csv, EstadoProduccion.PENDIENTE.value,
            EstadoProduccion.EN_PREPARACION.value, "Ticket movido a preparacion.",
        )

    def marcar_ticket_listo(self, detalle_ids_csv: str) -> None:
        self._transition_ticket_state(
            detalle_ids_csv, EstadoProduccion.EN_PREPARACION.value,
            EstadoProduccion.LISTO_PARA_ENTREGAR.value, "Pedido listo para entregar a salon.",
            actor_user_id=(self.usuario_actual.id if self.usuario_actual else None),
            actor_field_name="preparado_por_id",
        )

    def entregar_item_historial(self, detalle_id: int) -> None:
        with get_session() as session:
            detalle = session.get(DetallePedido, detalle_id)
            if detalle is None or not detalle.impreso_cocina:
                self.mensaje = "El item indicado ya no existe."
                return
            if detalle.estado_produccion != EstadoProduccion.LISTO_PARA_ENTREGAR.value:
                self.mensaje = "Ese item no esta listo para entrega."
                return
            detalle.estado_produccion = EstadoProduccion.ENTREGADO_AL_CLIENTE.value
            detalle.updated_at = datetime.utcnow()
            session.add(detalle)
            pedido = session.get(Pedido, detalle.pedido_id)
            if pedido is not None:
                _sync_order_status(session, pedido)
            session.commit()
        if self.mesa_seleccionada_id:
            self._cargar_historial_mesa(self.mesa_seleccionada_id)
        self.cargar_mesas()
        self.cargar_cocina()
        self.mensaje = "Item entregado a la mesa."

    # ─── Caja — Flujo de cobro con método de pago ────────────────────────────

    def abrir_cobro_mesa(self, mesa_id: int) -> None:
        mesa = next((m for m in self.mesas if m.id == mesa_id), None)
        if mesa is None or mesa.estado == EstadoMesa.LIBRE.value or mesa.total_abierto <= 0:
            self.mensaje = "Esa mesa no tiene consumo pendiente."
            return
        self.caja_cobro_mesa_id = mesa_id
        self.caja_cobro_metodo = "efectivo"
        self.caja_cobro_propina = ""
        self.caja_cobro_efectivo_recibido = ""
        self.mensaje = ""

    def cancelar_cobro(self) -> None:
        self.caja_cobro_mesa_id = 0
        self.caja_cobro_metodo = "efectivo"
        self.caja_cobro_propina = ""
        self.caja_cobro_efectivo_recibido = ""

    def set_caja_cobro_metodo(self, v: str) -> None:
        self.caja_cobro_metodo = v
        self.caja_cobro_efectivo_recibido = ""

    def set_caja_cobro_propina(self, v: str) -> None:
        self.caja_cobro_propina = v

    def set_caja_cobro_efectivo_recibido(self, v: str) -> None:
        self.caja_cobro_efectivo_recibido = v

    def confirmar_cobro(self) -> None:
        objetivo = self.caja_cobro_mesa_id
        if objetivo == 0:
            self.mensaje = "No hay mesa seleccionada para cobrar."
            return
        metodo = self.caja_cobro_metodo or "efectivo"
        try:
            propina_raw = float(self.caja_cobro_propina.replace(",", ".").strip())
            propina = Decimal(str(round(propina_raw, 2))) if propina_raw > 0 else Decimal("0.00")
        except (ValueError, AttributeError, InvalidOperation):
            propina = Decimal("0.00")

        pedido_id = 0
        mesa_label = ""
        attended_by = ""
        total_base = Decimal("0.00")
        ticket_lines: list[TicketLine] = []
        with get_session() as session:
            mesa = session.get(Mesa, objetivo)
            if mesa is None:
                self.mensaje = "La mesa indicada ya no existe."
                return
            pedido = _get_open_order(session, mesa.id or 0)
            if pedido is None:
                self.mensaje = "No hay pedido abierto para esa mesa."
                return
            if _get_unsent_details(session, pedido.id or 0):
                self.mensaje = "Todavia hay items pendientes de enviar a cocina."
                return
            if _get_not_delivered_details(session, pedido.id or 0):
                self.mensaje = "Todavia hay items en cocina o listos por entregar."
                return
            detalles = session.exec(select(DetallePedido).where(DetallePedido.pedido_id == pedido.id)).all()
            productos = {p.id: p for p in session.exec(select(Producto).where(Producto.company_id == _COMPANY_ID)).all()}
            usuarios = {u.id: u for u in session.exec(select(UsuarioFood).where(UsuarioFood.company_id == _COMPANY_ID)).all()}
            ticket_lines = [
                TicketLine(
                    name=(productos[d.producto_id].nombre if d.producto_id in productos else f"Producto {d.producto_id}"),
                    quantity=d.cantidad,
                    unit_price=float(_to_decimal(d.precio_unitario)),
                    subtotal=float(_to_decimal(d.subtotal)),
                    note=d.notas or "",
                )
                for d in detalles
            ]
            mozo = usuarios.get(pedido.mozo_id)
            attended_by = _actor_name(
                mozo.nombre if mozo else (self.usuario_actual.nombre if self.usuario_actual else "")
            ) or "Sin asignar"
            total_base = _to_decimal(pedido.total)
            total_final = total_base + propina
            now = datetime.utcnow()
            if self.usuario_actual:
                pedido.cajero_id = self.usuario_actual.id
            pedido.pagado = True
            pedido.estado = EstadoPedido.COBRADO.value
            pedido.cerrado_en = now
            pedido.updated_at = now
            pedido.metodo_pago = metodo
            pedido.propina = propina
            session.add(pedido)
            mesa.estado = EstadoMesa.LIBRE.value
            mesa.updated_at = now
            session.add(mesa)
            session.commit()
            pedido_id = pedido.id or 0
            mesa_label = mesa.nombre or f"Mesa {mesa.numero}"

        if self.mesa_seleccionada_id == objetivo:
            self.mesa_seleccionada_id = 0
            self.carrito = []
            self.historial_pedido = []
        self.cancelar_cobro()
        self.cargar_mesas()
        self.cargar_historial_ventas()
        total_final = total_base + propina
        try:
            self._get_printer_service().print_cashier_ticket(
                order_reference=mesa_label,
                pedido_id=pedido_id,
                items=ticket_lines,
                total=float(total_final),
                attended_by=attended_by,
            )
        except Exception as error:
            self.mensaje = f"Mesa {mesa_label} cobrada. Fallo impresion caja: {error}"
            return
        propina_txt = f" + propina {_money_text(propina)}" if propina > 0 else ""
        self.mensaje = f"Mesa {mesa_label} cobrada ({metodo}). Total: {_money_text(total_final)}{propina_txt}."

    # ─── Caja — Cobro de mesa ─────────────────────────────────────────────────

    def cobrar_mesa(self, mesa_id: int) -> None:
        objetivo = mesa_id or self.mesa_seleccionada_id
        if objetivo == 0:
            self.mensaje = "Selecciona una mesa antes de cobrar."
            return
        pedido_id = 0
        mesa_label = ""
        attended_by = ""
        total = 0.0
        ticket_lines: list[TicketLine] = []
        with get_session() as session:
            mesa = session.get(Mesa, objetivo)
            if mesa is None:
                self.mensaje = "La mesa indicada ya no existe."
                return
            pedido = _get_open_order(session, mesa.id or 0)
            if pedido is None:
                self.mensaje = "No hay pedido abierto para esa mesa."
                return
            if _get_unsent_details(session, pedido.id or 0):
                self.mensaje = "Todavia hay items pendientes de enviar a cocina."
                return
            if _get_not_delivered_details(session, pedido.id or 0):
                self.mensaje = "Todavia hay items en cocina o listos por entregar."
                return
            detalles = session.exec(select(DetallePedido).where(DetallePedido.pedido_id == pedido.id)).all()
            productos = {p.id: p for p in session.exec(select(Producto).where(Producto.company_id == _COMPANY_ID)).all()}
            usuarios = {u.id: u for u in session.exec(select(UsuarioFood).where(UsuarioFood.company_id == _COMPANY_ID)).all()}
            ticket_lines = [
                TicketLine(
                    name=(productos[d.producto_id].nombre if d.producto_id in productos else f"Producto {d.producto_id}"),
                    quantity=d.cantidad,
                    unit_price=float(_to_decimal(d.precio_unitario)),
                    subtotal=float(_to_decimal(d.subtotal)),
                    note=d.notas or "",
                )
                for d in detalles
            ]
            mozo = usuarios.get(pedido.mozo_id)
            attended_by = _actor_name(
                mozo.nombre if mozo else (self.usuario_actual.nombre if self.usuario_actual else "")
            ) or "Sin asignar"
            total = float(_to_decimal(pedido.total))
            now = datetime.utcnow()
            if self.usuario_actual:
                pedido.cajero_id = self.usuario_actual.id
            pedido.pagado = True
            pedido.estado = EstadoPedido.COBRADO.value
            pedido.cerrado_en = now
            pedido.updated_at = now
            session.add(pedido)
            mesa.estado = EstadoMesa.LIBRE.value
            mesa.updated_at = now
            session.add(mesa)
            session.commit()
            pedido_id = pedido.id or 0
            mesa_label = mesa.nombre or f"Mesa {mesa.numero}"
        if self.mesa_seleccionada_id == objetivo:
            self.mesa_seleccionada_id = 0
            self.carrito = []
            self.historial_pedido = []
        self.cargar_mesas()
        self.cargar_historial_ventas()
        try:
            self._get_printer_service().print_cashier_ticket(
                order_reference=mesa_label,
                pedido_id=pedido_id,
                items=ticket_lines,
                total=total,
                attended_by=attended_by,
            )
        except Exception as error:
            self.mensaje = f"Mesa {mesa_label} cobrada. Fallo impresion caja: {error}"
            return
        self.mensaje = f"Mesa {mesa_label} cobrada. Total: {_money_text(total)}."

    # ─── Mostrador ────────────────────────────────────────────────────────────

    def set_mostrador_cliente_nombre(self, value: str) -> None:
        self.mostrador_cliente_nombre = str(value)[:120]

    def agregar_producto_mostrador(self, producto_id: int) -> None:
        producto = next((p for p in self.productos if p.id == producto_id and p.disponible), None)
        if producto is None:
            self.mensaje = "Producto no disponible para mostrador."
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
                )
                self.mostrador_carrito = carrito
                self.mensaje = f"{producto.nombre} agregado a mostrador."
                return
        carrito.append(CarritoItem(
            producto_id=producto.id,
            nombre=producto.nombre,
            cantidad=1,
            precio_unitario=producto.precio,
            subtotal=producto.precio,
            subtotal_texto=producto.precio_texto,
        ))
        self.mostrador_carrito = carrito
        self.mensaje = f"{producto.nombre} agregado a mostrador."

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
                ))
        if not encontrado:
            self.mensaje = "Ese producto no esta en el carrito de mostrador."
            return
        self.mostrador_carrito = carrito_actualizado
        self.mensaje = "Carrito de mostrador actualizado."

    def limpiar_carrito_mostrador(self) -> None:
        self.mostrador_carrito = []
        self.mensaje = "Carrito de mostrador limpio."

    def cobrar_y_enviar_mostrador(self) -> None:
        if not self.mostrador_carrito:
            self.mensaje = "Agrega productos antes de cobrar en mostrador."
            return
        if self.usuario_actual is None:
            self.mensaje = "Inicia sesion para registrar la venta de mostrador."
            return
        pedido_id = 0
        total = 0.0
        cliente_nombre = _actor_name(self.mostrador_cliente_nombre) or "Sin nombre"
        ticket_label = f"Para Llevar - Cliente: {cliente_nombre}"
        attended_by = _actor_name(self.usuario_actual.nombre if self.usuario_actual else "") or "Sin asignar"
        ticket_lines: list[TicketLine] = []
        with get_session() as session:
            productos = {p.id: p for p in session.exec(select(Producto).where(Producto.company_id == _COMPANY_ID)).all()}
            invalidos = [item.nombre for item in self.mostrador_carrito if item.producto_id not in productos or not productos[item.producto_id].disponible]
            if invalidos:
                self.mensaje = f"Productos no disponibles: {', '.join(invalidos)}"
                return
            now = datetime.utcnow()
            pedido = Pedido(
                company_id=_COMPANY_ID,
                mesa_id=None,
                cajero_id=self.usuario_actual.id,
                tipo_pedido=TipoPedido.MOSTRADOR.value,
                nombre_cliente=_actor_name(self.mostrador_cliente_nombre) or None,
                pagado=True,
                estado=EstadoPedido.ENVIADO.value,
                total=Decimal("0.00"),
                abierto_en=now,
                cerrado_en=now,
            )
            session.add(pedido)
            session.commit()
            session.refresh(pedido)
            for item in self.mostrador_carrito:
                producto = productos[item.producto_id]
                precio = _to_decimal(producto.precio)
                subtotal = precio * item.cantidad
                detalle = DetallePedido(
                    company_id=_COMPANY_ID,
                    pedido_id=pedido.id or 0,
                    producto_id=producto.id or 0,
                    cantidad=item.cantidad,
                    precio_unitario=precio,
                    subtotal=subtotal,
                    estado_produccion=EstadoProduccion.PENDIENTE.value,
                    impreso_cocina=True,
                    impreso_caja=True,
                    enviado_cocina_at=now,
                )
                session.add(detalle)
                ticket_lines.append(TicketLine(
                    name=producto.nombre,
                    quantity=item.cantidad,
                    unit_price=float(precio),
                    subtotal=float(subtotal),
                    note="",
                ))
            total = float(_recalculate_order_total(session, pedido))
            _sync_order_status(session, pedido)
            session.add(pedido)
            session.commit()
            pedido_id = pedido.id or 0
        self.ultimo_pedido_id = pedido_id
        self.mostrador_carrito = []
        self.mostrador_cliente_nombre = ""
        self.cargar_cocina()
        self.cargar_historial_ventas()
        try:
            svc = self._get_printer_service()
            svc.print_kitchen_ticket(mesa_label=ticket_label, pedido_id=pedido_id, items=ticket_lines)
            svc.print_cashier_ticket(order_reference=f"Cliente: {cliente_nombre}", pedido_id=pedido_id, items=ticket_lines, total=total, attended_by=attended_by)
        except Exception as error:
            self.mensaje = f"Pedido de mostrador #{pedido_id} cobrado. Fallo impresion: {error}"
            return
        self.mensaje = f"Pedido de mostrador #{pedido_id} cobrado y enviado."

    def cargar_pedidos_mostrador_listos(self) -> None:
        with get_session() as session:
            detalles = session.exec(
                select(DetallePedido).where(
                    DetallePedido.company_id == _COMPANY_ID,
                    DetallePedido.impreso_cocina.is_(True),
                    DetallePedido.estado_produccion == EstadoProduccion.LISTO_PARA_ENTREGAR.value,
                ).order_by(DetallePedido.enviado_cocina_at, DetallePedido.id)
            ).all()
            if not detalles:
                self.pedidos_mostrador_listos = []
                return
            pedido_ids = {d.pedido_id for d in detalles}
            pedidos = {
                p.id: p
                for p in session.exec(select(Pedido).where(Pedido.id.in_(pedido_ids))).all()
                if p.tipo_pedido == TipoPedido.MOSTRADOR.value
            }
            productos = {p.id: p for p in session.exec(select(Producto).where(Producto.company_id == _COMPANY_ID)).all()}
            grupos: dict = {}
            for d in detalles:
                pedido = pedidos.get(d.pedido_id)
                if pedido is None:
                    continue
                marca = d.updated_at or d.enviado_cocina_at or d.created_at
                if pedido.id not in grupos:
                    grupos[pedido.id] = {
                        "pedido_id": pedido.id or 0,
                        "cliente_nombre": _actor_name(pedido.nombre_cliente) or "Sin nombre",
                        "hora_texto": marca.strftime("%H:%M"),
                        "items_lines": [],
                        "items_count": 0,
                    }
                producto = productos.get(d.producto_id)
                grupos[pedido.id]["items_lines"].append(f"{d.cantidad} x {producto.nombre if producto else f'Producto {d.producto_id}'}")
                grupos[pedido.id]["items_count"] += d.cantidad
            self.pedidos_mostrador_listos = [
                MostradorEntregaView(**data) for data in grupos.values()
            ]

    def cargar_pedidos_mostrador_entregados(self) -> None:
        with get_session() as session:
            pedidos = session.exec(
                select(Pedido).where(
                    Pedido.company_id == _COMPANY_ID,
                    Pedido.tipo_pedido == TipoPedido.MOSTRADOR.value,
                    Pedido.pagado.is_(True),
                ).order_by(Pedido.updated_at.desc(), Pedido.id.desc())
            ).all()
            if not pedidos:
                self.pedidos_mostrador_entregados = []
                return
            productos = {p.id: p for p in session.exec(select(Producto).where(Producto.company_id == _COMPANY_ID)).all()}
            historial: list = []
            for pedido in pedidos:
                detalles = session.exec(
                    select(DetallePedido).where(DetallePedido.pedido_id == pedido.id).order_by(DetallePedido.id)
                ).all()
                if not detalles or any(d.estado_produccion != EstadoProduccion.ENTREGADO_AL_CLIENTE.value for d in detalles):
                    continue
                entregado_en = max(d.updated_at for d in detalles)
                resumen = " · ".join(
                    f"{d.cantidad}x {productos[d.producto_id].nombre if d.producto_id in productos else f'Producto {d.producto_id}'}"
                    for d in detalles
                )
                historial.append((
                    entregado_en,
                    MostradorEntregadoView(
                        pedido_id=pedido.id or 0,
                        cliente_nombre=_actor_name(pedido.nombre_cliente) or "Sin nombre",
                        hora_texto=entregado_en.strftime("%H:%M"),
                        items_resumen=resumen,
                        total_texto=_money_text(pedido.total),
                    ),
                ))
            historial.sort(key=lambda x: x[0], reverse=True)
            self.pedidos_mostrador_entregados = [item for _, item in historial[:10]]

    def entregar_pedido_mostrador(self, pedido_id: int) -> None:
        with get_session() as session:
            pedido = session.get(Pedido, pedido_id)
            if pedido is None or pedido.tipo_pedido != TipoPedido.MOSTRADOR.value or pedido.company_id != _COMPANY_ID:
                self.mensaje = "El pedido de mostrador ya no existe."
                return
            detalles_listos = session.exec(
                select(DetallePedido).where(
                    DetallePedido.pedido_id == pedido_id,
                    DetallePedido.impreso_cocina.is_(True),
                    DetallePedido.estado_produccion == EstadoProduccion.LISTO_PARA_ENTREGAR.value,
                )
            ).all()
            if not detalles_listos:
                self.mensaje = "Ese pedido ya no tiene items listos para entregar."
                return
            now = datetime.utcnow()
            for d in detalles_listos:
                d.estado_produccion = EstadoProduccion.ENTREGADO_AL_CLIENTE.value
                d.updated_at = now
                session.add(d)
            _sync_order_status(session, pedido)
            session.add(pedido)
            session.commit()
        self.cargar_cocina()
        self.cargar_pedidos_mostrador_listos()
        self.cargar_pedidos_mostrador_entregados()
        self.cargar_historial_ventas()
        self.mensaje = "Pedido de mostrador entregado al cliente."

    # ─── Dashboard KPIs ───────────────────────────────────────────────────────

    def cargar_dashboard(self) -> None:
        hoy = datetime.utcnow().date()
        inicio_hoy = datetime(hoy.year, hoy.month, hoy.day)
        fin_hoy = inicio_hoy + timedelta(days=1)
        with get_session() as session:
            pedidos_hoy = session.exec(
                select(Pedido).where(
                    Pedido.company_id == _COMPANY_ID,
                    Pedido.pagado.is_(True),
                    Pedido.cerrado_en >= inicio_hoy,
                    Pedido.cerrado_en < fin_hoy,
                )
            ).all()
            ventas = sum(
                _to_decimal(p.total) + _to_decimal(getattr(p, "propina", 0))
                for p in pedidos_hoy
            )
            propina_total = sum(_to_decimal(getattr(p, "propina", 0)) for p in pedidos_hoy)
            mesas_no_libres = session.exec(
                select(Mesa).where(
                    Mesa.company_id == _COMPANY_ID,
                    Mesa.estado != EstadoMesa.LIBRE.value,
                    Mesa.activa.is_(True),
                )
            ).all()
            pedido_ids_hoy = {p.id for p in pedidos_hoy}
            top_data: dict[int, dict] = {}
            if pedido_ids_hoy:
                detalles = session.exec(
                    select(DetallePedido).where(DetallePedido.pedido_id.in_(pedido_ids_hoy))
                ).all()
                productos = {
                    p.id: p
                    for p in session.exec(select(Producto).where(Producto.company_id == _COMPANY_ID)).all()
                }
                for d in detalles:
                    pid = d.producto_id
                    if pid not in top_data:
                        prod = productos.get(pid)
                        top_data[pid] = {
                            "nombre": prod.nombre if prod else f"Producto {pid}",
                            "cantidad": 0,
                            "total": Decimal("0.00"),
                        }
                    top_data[pid]["cantidad"] += d.cantidad
                    top_data[pid]["total"] += _to_decimal(d.subtotal)
            top_sorted = sorted(top_data.values(), key=lambda x: x["cantidad"], reverse=True)[:5]
        self.dashboard_ventas_hoy_texto = _money_text(ventas)
        self.dashboard_pedidos_hoy = len(pedidos_hoy)
        self.dashboard_mesas_ocupadas = len(mesas_no_libres)
        self.dashboard_propina_hoy_texto = _money_text(propina_total)
        self.dashboard_top_platos = [
            TopPlatoView(
                nombre=p["nombre"],
                cantidad=p["cantidad"],
                total_generado=float(p["total"]),
                total_texto=_money_text(p["total"]),
            )
            for p in top_sorted
        ]

    # ─── Historial de ventas ──────────────────────────────────────────────────

    def cargar_historial_ventas(self) -> None:
        with get_session() as session:
            query = (
                select(Pedido)
                .where(
                    Pedido.company_id == _COMPANY_ID,
                    Pedido.pagado.is_(True),
                )
            )
            if self.historial_filtro_fecha_desde:
                try:
                    desde = datetime.strptime(self.historial_filtro_fecha_desde, "%Y-%m-%d")
                    query = query.where(Pedido.cerrado_en >= desde)
                except ValueError:
                    pass
            if self.historial_filtro_fecha_hasta:
                try:
                    hasta = datetime.strptime(self.historial_filtro_fecha_hasta, "%Y-%m-%d")
                    hasta = hasta.replace(hour=23, minute=59, second=59)
                    query = query.where(Pedido.cerrado_en <= hasta)
                except ValueError:
                    pass
            if self.historial_filtro_metodo:
                query = query.where(Pedido.metodo_pago == self.historial_filtro_metodo)
            query = query.order_by(Pedido.cerrado_en.desc(), Pedido.id.desc())
            pedidos = session.exec(query).all()
            mesas = {m.id: m for m in session.exec(select(Mesa).where(Mesa.company_id == _COMPANY_ID)).all()}
            usuarios = {u.id: u for u in session.exec(select(UsuarioFood).where(UsuarioFood.company_id == _COMPANY_ID)).all()}
            historial: list[VentaHistorialView] = []
            for p in pedidos:
                total_base = _to_decimal(p.total)
                propina = _to_decimal(getattr(p, "propina", Decimal("0.00")))
                total_con_propina = total_base + propina
                historial.append(VentaHistorialView(
                    pedido_id=p.id or 0,
                    mesa_label=_pedido_sales_label(p, mesas),
                    total=float(total_base),
                    total_texto=_money_text(total_base),
                    propina=float(propina),
                    propina_texto=_money_text(propina) if propina > 0 else "",
                    total_con_propina=float(total_con_propina),
                    total_con_propina_texto=_money_text(total_con_propina),
                    metodo_pago=getattr(p, "metodo_pago", None) or "—",
                    mozo_nombre=_actor_name(usuarios[p.mozo_id].nombre if p.mozo_id in usuarios else "Sin asignar"),
                    cajero_nombre=_actor_name(usuarios[p.cajero_id].nombre if p.cajero_id in usuarios else "Sin asignar"),
                ))
            self.historial_ventas = historial

    def set_historial_filtro_fecha_desde(self, v: str) -> None:
        self.historial_filtro_fecha_desde = v

    def set_historial_filtro_fecha_hasta(self, v: str) -> None:
        self.historial_filtro_fecha_hasta = v

    def set_historial_filtro_metodo(self, v: str) -> None:
        self.historial_filtro_metodo = v

    def aplicar_filtros_historial(self) -> None:
        self.cargar_historial_ventas()

    def limpiar_filtros_historial(self) -> None:
        self.historial_filtro_fecha_desde = ""
        self.historial_filtro_fecha_hasta = ""
        self.historial_filtro_metodo = ""
        self.cargar_historial_ventas()

    # ─── Admin Carta — Categorías ─────────────────────────────────────────────

    def set_categoria_form_nombre(self, v: str) -> None:
        self.categoria_form_nombre = str(v)[:120]

    def set_categoria_form_descripcion(self, v: str) -> None:
        self.categoria_form_descripcion = str(v)[:240]

    def set_categoria_form_orden(self, v: str) -> None:
        self.categoria_form_orden = v

    def guardar_categoria(self) -> None:
        nombre = self.categoria_form_nombre.strip()
        if not nombre:
            self.mensaje = "El nombre de la categoria es obligatorio."
            return
        try:
            orden = int(self.categoria_form_orden)
        except ValueError:
            orden = len(self.categorias) + 1
        with get_session() as session:
            if self.categoria_form_id:
                cat = session.get(Categoria, self.categoria_form_id)
                if cat is None or cat.company_id != _COMPANY_ID:
                    self.mensaje = "Categoria no encontrada."
                    return
                cat.nombre = nombre
                cat.descripcion = self.categoria_form_descripcion.strip() or None
                cat.orden = orden
                cat.updated_at = datetime.utcnow()
                session.add(cat)
            else:
                cat = Categoria(
                    company_id=_COMPANY_ID,
                    nombre=nombre,
                    descripcion=self.categoria_form_descripcion.strip() or None,
                    orden=orden,
                )
                session.add(cat)
            session.commit()
        self.cargar_menu()
        self._reset_categoria_form()
        self.mensaje = "Categoria guardada."

    def editar_categoria(self, categoria_id: int) -> None:
        cat = next((c for c in self.categorias if c.id == categoria_id), None)
        if cat is None:
            return
        self.categoria_form_id = cat.id
        self.categoria_form_nombre = cat.nombre
        self.categoria_form_descripcion = cat.descripcion
        self.categoria_form_orden = str(cat.orden)

    def toggle_categoria_activa(self, categoria_id: int) -> None:
        with get_session() as session:
            cat = session.get(Categoria, categoria_id)
            if cat is None or cat.company_id != _COMPANY_ID:
                return
            cat.activa = not cat.activa
            cat.updated_at = datetime.utcnow()
            session.add(cat)
            session.commit()
        self.cargar_menu()

    def _reset_categoria_form(self) -> None:
        self.categoria_form_id = 0
        self.categoria_form_nombre = ""
        self.categoria_form_descripcion = ""
        self.categoria_form_orden = str(len(self.categorias) + 1)

    def cancelar_categoria_form(self) -> None:
        self._reset_categoria_form()

    # ─── Admin Carta — Productos ──────────────────────────────────────────────

    def set_producto_form_nombre(self, v: str) -> None:
        self.producto_form_nombre = str(v)[:160]

    def set_producto_form_descripcion(self, v: str) -> None:
        self.producto_form_descripcion = str(v)[:240]

    def set_producto_form_precio(self, v: str) -> None:
        self.producto_form_precio = v

    def set_producto_form_categoria(self, v: str) -> None:
        self.producto_form_categoria_nombre = v

    def set_producto_form_disponible(self, v: bool) -> None:
        self.producto_form_disponible = v

    def guardar_producto(self) -> None:
        nombre = self.producto_form_nombre.strip()
        if not nombre:
            self.mensaje = "El nombre del producto es obligatorio."
            return
        precio = _parse_positive_price(self.producto_form_precio)
        if precio is None:
            self.mensaje = "El precio debe ser un numero mayor a 0."
            return
        with get_session() as session:
            cat = session.exec(
                select(Categoria).where(
                    Categoria.company_id == _COMPANY_ID,
                    Categoria.nombre == self.producto_form_categoria_nombre,
                )
            ).first()
            if cat is None:
                self.mensaje = f"Categoria '{self.producto_form_categoria_nombre}' no encontrada."
                return
            if self.producto_form_id:
                prod = session.get(Producto, self.producto_form_id)
                if prod is None or prod.company_id != _COMPANY_ID:
                    self.mensaje = "Producto no encontrado."
                    return
                prod.nombre = nombre
                prod.descripcion = self.producto_form_descripcion.strip() or None
                prod.precio = precio
                prod.categoria_id = cat.id or 0
                prod.disponible = self.producto_form_disponible
                prod.updated_at = datetime.utcnow()
                session.add(prod)
            else:
                prod = Producto(
                    company_id=_COMPANY_ID,
                    categoria_id=cat.id or 0,
                    nombre=nombre,
                    descripcion=self.producto_form_descripcion.strip() or None,
                    precio=precio,
                    disponible=self.producto_form_disponible,
                )
                session.add(prod)
            session.commit()
        self.cargar_menu()
        self._reset_producto_form()
        self.mensaje = "Producto guardado."

    def editar_producto(self, producto_id: int) -> None:
        prod = next((p for p in self.productos if p.id == producto_id), None)
        if prod is None:
            return
        self.producto_form_id = prod.id
        self.producto_form_nombre = prod.nombre
        self.producto_form_descripcion = prod.descripcion
        self.producto_form_precio = str(prod.precio)
        self.producto_form_categoria_nombre = prod.categoria_nombre
        self.producto_form_disponible = prod.disponible

    def toggle_producto_disponible(self, producto_id: int) -> None:
        with get_session() as session:
            prod = session.get(Producto, producto_id)
            if prod is None or prod.company_id != _COMPANY_ID:
                return
            prod.disponible = not prod.disponible
            prod.updated_at = datetime.utcnow()
            session.add(prod)
            session.commit()
        self.cargar_menu()

    def _reset_producto_form(self) -> None:
        self.producto_form_id = 0
        self.producto_form_nombre = ""
        self.producto_form_descripcion = ""
        self.producto_form_precio = ""
        self.producto_form_disponible = True
        if self.categorias:
            self.producto_form_categoria_nombre = self.categorias[0].nombre

    def cancelar_producto_form(self) -> None:
        self._reset_producto_form()


# ─── Estado público (sin auth) ────────────────────────────────────────────────

class ProductoPublicoView(BaseModel):
    nombre: str
    descripcion: str
    precio_texto: str


class CategoriaPublicaView(BaseModel):
    nombre: str
    productos: list[ProductoPublicoView]


class MenuPublicoState(rx.State):
    """Estado de la carta pública — no requiere sesión."""

    nombre_local: str = ""
    categorias_menu: list[CategoriaPublicaView] = []
    cargando: bool = True
    no_encontrado: bool = False

    def on_load(self) -> None:
        slug = self.router.page.params.get("slug", "")
        self.cargando = True
        self.no_encontrado = False
        self.nombre_local = ""
        self.categorias_menu = []

        if not slug:
            self.no_encontrado = True
            self.cargando = False
            return

        with get_session() as session:
            cfg = session.exec(
                select(ConfigImpresora).where(ConfigImpresora.slug == slug)
            ).first()
            if cfg is None:
                self.no_encontrado = True
                self.cargando = False
                return

            company_id = cfg.company_id
            self.nombre_local = cfg.nombre_local

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
                            productos=[
                                ProductoPublicoView(
                                    nombre=p.nombre,
                                    descripcion=p.descripcion or "",
                                    precio_texto=_money_text(p.precio),
                                )
                                for p in prods
                            ],
                        )
                    )

            self.categorias_menu = result

        self.cargando = False
