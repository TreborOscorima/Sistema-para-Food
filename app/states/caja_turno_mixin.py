"""Turnos de caja — apertura con fondo inicial, movimientos de efectivo y cierre con arqueo.

Réplica adaptada del módulo de caja de Sistema-de-Ventas (states/cash/) al flujo
de un restobar: turno por servicio (almuerzo/cena), gastos de mercado como
egresos de caja chica y propinas en efectivo dentro del arqueo.

La lógica de negocio vive en funciones puras (testeables sin Reflex); el mixin
solo traduce entre la UI y esas funciones. FoodState provee en runtime
`_tenant_session()`, `_company_id()`, `usuario_actual`, `config_nombre_local`
y `_ticket_paper_width_mm()`.
"""

from __future__ import annotations

import io
import json
from decimal import Decimal, InvalidOperation

import reflex as rx
from pydantic import BaseModel
from sqlmodel import select

from tuwayki_core.utils.timezone import format_local_datetime, utc_now_naive

from app.models.food import (
    DetallePedido,
    EstadoPedido,
    EstadoTurnoCaja,
    Mesa,
    MovimientoCaja,
    PagoPedido,
    Pedido,
    Producto,
    TipoMetodoPago,
    TipoMovimientoCaja,
    TurnoCaja,
    UsuarioFood,
)
from app.services.auditoria_service import registrar_auditoria
from app.services.metodos_pago_service import (
    mapa_nombres,
    mapa_tipos,
    obtener_metodos,
)
from app.services.receipt_service import (
    build_cash_close_ticket_lines,
    render_ticket_html,
    ticket_text,
)


def _bucket_tipo(tipo: str) -> str:
    """Mapea un TipoMetodoPago al balde histórico del turno (efectivo/tarjeta/qr/fiado)."""
    if tipo == TipoMetodoPago.EFECTIVO.value:
        return "efectivo"
    if tipo == TipoMetodoPago.TARJETA.value:
        return "tarjeta"
    if tipo == TipoMetodoPago.FIADO.value:
        return "fiado"
    return "qr"  # digital / otro: venta que no deja efectivo en caja

CURRENCY_SYMBOL = "S/"
_HORA_FMT = "%d/%m %H:%M"

DENOMINACIONES_PEN: list[tuple[str, Decimal, str]] = [
    ("b200", Decimal("200.00"), "Billete S/ 200"),
    ("b100", Decimal("100.00"), "Billete S/ 100"),
    ("b50", Decimal("50.00"), "Billete S/ 50"),
    ("b20", Decimal("20.00"), "Billete S/ 20"),
    ("b10", Decimal("10.00"), "Billete S/ 10"),
    ("m5", Decimal("5.00"), "Moneda S/ 5"),
    ("m2", Decimal("2.00"), "Moneda S/ 2"),
    ("m1", Decimal("1.00"), "Moneda S/ 1"),
    ("m050", Decimal("0.50"), "Moneda S/ 0.50"),
    ("m020", Decimal("0.20"), "Moneda S/ 0.20"),
    ("m010", Decimal("0.10"), "Moneda S/ 0.10"),
]

CATEGORIAS_EGRESO = ["Mercado", "Insumos", "Servicios", "Propinas pagadas", "Otros"]
CATEGORIAS_INGRESO = ["Fondo adicional", "Otros"]


def _dec(value) -> Decimal:
    if value is None:
        return Decimal("0.00")
    if isinstance(value, Decimal):
        return value.quantize(Decimal("0.01"))
    return Decimal(str(value)).quantize(Decimal("0.01"))


def _money(value) -> str:
    return f"{CURRENCY_SYMBOL} {_dec(value):.2f}"


def _hora_local(dt) -> str:
    return format_local_datetime(dt, _HORA_FMT, "PE") if dt else "—"


# ─── Lógica de negocio (funciones puras, testeables sin Reflex) ──────────────

def get_turno_abierto(session, company_id: int, sucursal_id: int = 0) -> TurnoCaja | None:
    """Turno abierto de la empresa (y sucursal si aplica), o None."""
    q = select(TurnoCaja).where(
        TurnoCaja.company_id == company_id,
        TurnoCaja.estado == EstadoTurnoCaja.ABIERTO.value,
    )
    if sucursal_id:
        q = q.where(TurnoCaja.sucursal_id == sucursal_id)
    return session.exec(q.order_by(TurnoCaja.id.desc())).first()


def abrir_turno_caja(
    session,
    company_id: int,
    usuario_id: int | None,
    monto_inicial: Decimal,
    sucursal_id: int = 0,
) -> TurnoCaja:
    monto_inicial = _dec(monto_inicial)
    if monto_inicial < 0:
        raise ValueError("El fondo inicial no puede ser negativo.")
    if get_turno_abierto(session, company_id, sucursal_id) is not None:
        raise ValueError("Ya hay un turno de caja abierto. Ciérralo antes de abrir otro.")
    turno = TurnoCaja(
        company_id=company_id,
        sucursal_id=sucursal_id or None,
        abierto_por_id=usuario_id,
        estado=EstadoTurnoCaja.ABIERTO.value,
        monto_inicial=monto_inicial,
        abierto_en=utc_now_naive(),
    )
    session.add(turno)
    session.flush()
    return turno


def registrar_movimiento_caja(
    session,
    turno: TurnoCaja,
    usuario_id: int | None,
    tipo: str,
    categoria: str,
    monto: Decimal,
    motivo: str,
) -> MovimientoCaja:
    if turno.estado != EstadoTurnoCaja.ABIERTO.value:
        raise ValueError("El turno de caja ya está cerrado.")
    if tipo not in (TipoMovimientoCaja.INGRESO.value, TipoMovimientoCaja.EGRESO.value):
        raise ValueError("Tipo de movimiento inválido.")
    monto = _dec(monto)
    if monto <= 0:
        raise ValueError("El monto debe ser mayor a cero.")
    if not (motivo or "").strip():
        raise ValueError("Indica el motivo del movimiento.")
    movimiento = MovimientoCaja(
        company_id=turno.company_id,
        turno_id=turno.id or 0,
        usuario_id=usuario_id,
        tipo=tipo,
        categoria=(categoria or "Otros").strip()[:40],
        monto=monto,
        motivo=motivo.strip()[:240],
    )
    session.add(movimiento)
    session.flush()
    return movimiento


def _mov_snapshot(m: MovimientoCaja) -> dict:
    """Estado auditable de un movimiento (para el rastro antes/después)."""
    return {
        "tipo": m.tipo,
        "categoria": m.categoria,
        "monto": str(_dec(m.monto)),
        "motivo": m.motivo,
    }


def _mov_del_turno(session, turno: TurnoCaja, movimiento_id: int) -> MovimientoCaja:
    """Carga un movimiento verificando que pertenece a este turno/empresa."""
    movimiento = session.exec(
        select(MovimientoCaja).where(
            MovimientoCaja.id == movimiento_id,
            MovimientoCaja.company_id == turno.company_id,
            MovimientoCaja.turno_id == turno.id,
        )
    ).first()
    if movimiento is None:
        raise ValueError("El movimiento no existe o no pertenece a este turno.")
    return movimiento


def editar_movimiento_caja(
    session,
    turno: TurnoCaja,
    movimiento_id: int,
    usuario_id: int | None,
    usuario_nombre: str,
    tipo: str,
    categoria: str,
    monto: Decimal,
    motivo: str,
) -> MovimientoCaja:
    """Corrige un movimiento de caja ya registrado, in-place y auditado.

    Solo se permite dentro del turno abierto. Registra un asiento de Auditoría
    con el estado antes/después para que la corrección quede rastreable (quién,
    cuándo, qué cambió).
    """
    if turno.estado != EstadoTurnoCaja.ABIERTO.value:
        raise ValueError("El turno de caja ya está cerrado.")
    if tipo not in (TipoMovimientoCaja.INGRESO.value, TipoMovimientoCaja.EGRESO.value):
        raise ValueError("Tipo de movimiento inválido.")
    monto = _dec(monto)
    if monto <= 0:
        raise ValueError("El monto debe ser mayor a cero.")
    if not (motivo or "").strip():
        raise ValueError("Indica el motivo del movimiento.")
    movimiento = _mov_del_turno(session, turno, movimiento_id)
    before = _mov_snapshot(movimiento)
    movimiento.tipo = tipo
    movimiento.categoria = (categoria or "Otros").strip()[:40]
    movimiento.monto = monto
    movimiento.motivo = motivo.strip()[:240]
    movimiento.updated_at = utc_now_naive()
    session.add(movimiento)
    after = _mov_snapshot(movimiento)
    registrar_auditoria(
        session, turno.company_id, "correccion_movimiento_caja",
        usuario_id=usuario_id, usuario_nombre=usuario_nombre,
        entidad="movimiento_caja", entidad_id=movimiento_id,
        detalle={"before": before, "after": after},
    )
    session.flush()
    return movimiento


def eliminar_movimiento_caja(
    session,
    turno: TurnoCaja,
    movimiento_id: int,
    usuario_id: int | None,
    usuario_nombre: str,
) -> None:
    """Elimina un movimiento de caja ya registrado (auditado).

    Solo dentro del turno abierto. El movimiento eliminado queda registrado en
    Auditoría con su snapshot completo: el rastro no se pierde aunque la fila
    salga de la lista y del arqueo.
    """
    if turno.estado != EstadoTurnoCaja.ABIERTO.value:
        raise ValueError("El turno de caja ya está cerrado.")
    movimiento = _mov_del_turno(session, turno, movimiento_id)
    before = _mov_snapshot(movimiento)
    registrar_auditoria(
        session, turno.company_id, "eliminacion_movimiento_caja",
        usuario_id=usuario_id, usuario_nombre=usuario_nombre,
        entidad="movimiento_caja", entidad_id=movimiento_id,
        detalle={"before": before},
    )
    session.delete(movimiento)
    session.flush()


def calcular_resumen_turno(session, turno: TurnoCaja) -> dict[str, Decimal]:
    """Totales del turno: ventas por método, propinas, movimientos y efectivo esperado.

    La fuente primaria son las filas de PagoPedido (soportan pago mixto y
    cuenta dividida; el efectivo ya viene neto de vuelto). Los pedidos sin
    filas de pago (cobrados antes de la migración 0019) se clasifican por
    Pedido.metodo_pago como antes. El fiado no mueve efectivo.
    """
    pedidos = session.exec(
        select(Pedido).where(
            Pedido.company_id == turno.company_id,
            Pedido.turno_caja_id == turno.id,
            Pedido.estado != EstadoPedido.CANCELADO.value,
        )
    ).all()
    pagos = session.exec(
        select(PagoPedido).where(
            PagoPedido.company_id == turno.company_id,
            PagoPedido.turno_caja_id == turno.id,
        )
    ).all()
    pedidos_validos = {p.id for p in pedidos}
    tipos = mapa_tipos(session, turno.company_id)

    def _bucket(metodo: str) -> str:
        tipo = tipos.get(
            (metodo or "efectivo").lower(), TipoMetodoPago.DIGITAL.value
        )
        return _bucket_tipo(tipo)

    resumen: dict[str, Decimal] = {
        "efectivo": Decimal("0.00"),
        "tarjeta": Decimal("0.00"),
        "qr": Decimal("0.00"),
        "fiado": Decimal("0.00"),
        "propinas": Decimal("0.00"),
        # Venta neta = ingreso real del local (subtotal + recargo − descuento),
        # SIN propina. La propina no es venta: pasa por caja pero es del mozo.
        "ventas_netas": Decimal("0.00"),
    }
    # Desglose fino por código de método (Yape, Plin, …) para el detalle del cierre.
    por_metodo: dict[str, Decimal] = {}
    pedidos_con_pagos: set[int] = set()
    for pago in pagos:
        if pago.pedido_id not in pedidos_validos:
            continue  # pago de un pedido cancelado
        pedidos_con_pagos.add(pago.pedido_id)
        metodo = (pago.metodo or "efectivo").lower()
        monto = _dec(pago.monto)
        resumen[_bucket(metodo)] += monto
        por_metodo[metodo] = por_metodo.get(metodo, Decimal("0.00")) + monto
    for pedido in pedidos:
        propina = _dec(pedido.propina)
        resumen["propinas"] += propina
        resumen["ventas_netas"] += (
            _dec(pedido.total) + _dec(pedido.recargo) - _dec(pedido.descuento)
        )
        if (pedido.id or 0) in pedidos_con_pagos:
            continue
        neto = _dec(pedido.total) - _dec(pedido.descuento)
        metodo = (pedido.metodo_pago or "efectivo").lower()
        bucket = _bucket(metodo)
        # El fiado no mueve efectivo; los demás cobran también la propina.
        monto = neto if bucket == "fiado" else neto + propina
        resumen[bucket] += monto
        por_metodo[metodo] = por_metodo.get(metodo, Decimal("0.00")) + monto
    movimientos = session.exec(
        select(MovimientoCaja).where(
            MovimientoCaja.company_id == turno.company_id,
            MovimientoCaja.turno_id == turno.id,
        )
    ).all()
    ingresos = sum(
        (_dec(m.monto) for m in movimientos if m.tipo == TipoMovimientoCaja.INGRESO.value),
        Decimal("0.00"),
    )
    egresos = sum(
        (_dec(m.monto) for m in movimientos if m.tipo == TipoMovimientoCaja.EGRESO.value),
        Decimal("0.00"),
    )
    resumen["ingresos"] = ingresos
    resumen["egresos"] = egresos
    resumen["esperado_efectivo"] = (
        _dec(turno.monto_inicial) + resumen["efectivo"] + ingresos - egresos
    )
    resumen["por_metodo"] = por_metodo  # type: ignore[assignment]
    return resumen


def cerrar_turno_caja(
    session,
    turno: TurnoCaja,
    usuario_id: int | None,
    contado_efectivo: Decimal,
    arqueo_detalle: str | None = None,
    notas: str | None = None,
) -> TurnoCaja:
    if turno.estado != EstadoTurnoCaja.ABIERTO.value:
        raise ValueError("El turno de caja ya está cerrado.")
    resumen = calcular_resumen_turno(session, turno)
    now = utc_now_naive()
    contado = _dec(contado_efectivo)
    turno.estado = EstadoTurnoCaja.CERRADO.value
    turno.cerrado_en = now
    turno.cerrado_por_id = usuario_id
    turno.total_efectivo = resumen["efectivo"]
    turno.total_tarjeta = resumen["tarjeta"]
    turno.total_qr = resumen["qr"]
    turno.total_fiado = resumen["fiado"]
    turno.total_propinas = resumen["propinas"]
    turno.total_ingresos = resumen["ingresos"]
    turno.total_egresos = resumen["egresos"]
    turno.esperado_efectivo = resumen["esperado_efectivo"]
    turno.contado_efectivo = contado
    turno.descuadre = contado - resumen["esperado_efectivo"]
    turno.arqueo_detalle = arqueo_detalle or None
    turno.notas_cierre = (notas or "").strip()[:500] or None
    turno.updated_at = now
    session.add(turno)
    session.flush()
    return turno


def _cierre_ventas_rows(data: dict) -> list[tuple[str, str, bool]]:
    """Filas del bloque "Ventas del turno" para el cierre (ticket, PDF y pantalla).

    Si hubo recargos (envase/delivery/servicio) o descuentos, muestra el desglose
    Subtotal productos + extras por concepto − descuentos = Ventas netas, para que
    se vea de qué se compone el total. Si no hubo extras, una sola línea "Ventas
    (netas)". Devuelve tuplas (etiqueta, monto, enfasis). Fuente única para las 3
    superficies (que digan lo mismo).
    """
    rows: list[tuple[str, str, bool]] = []
    if data["hay_extras"]:
        rows.append(("Subtotal productos", data["subtotal_productos"], False))
        for r in data["recargos"]:
            rows.append((f"+ {r['concepto']}", r["monto_texto"], False))
        if data["hay_descuentos"]:
            rows.append(("- Descuentos", f"- {data['total_descuentos']}", False))
        rows.append(("= Ventas (netas)", data["ventas_netas"], True))
    else:
        rows.append(("Ventas (netas)", data["ventas_netas"], False))
    rows.append(("Propinas", data["total_propinas"], False))
    if data["hay_fiado"]:
        rows.append(("Fiado (pendiente de cobro)", data["total_fiado"], False))
    return rows


# ─── Views para la UI ────────────────────────────────────────────────────────

class MovimientoCajaView(BaseModel):
    id: int
    hora_texto: str
    tipo: str
    tipo_label: str
    categoria: str
    monto_texto: str
    monto_raw: str  # "10.00" — para precargar el formulario al corregir
    motivo: str
    usuario: str


class DenominacionRow(BaseModel):
    key: str
    etiqueta: str
    cantidad: str
    subtotal_texto: str


class ResumenCierreRow(BaseModel):
    etiqueta: str
    monto_texto: str
    enfasis: bool = False  # fila destacada (totales: Total cobrado, Esperado)


class TurnoHistorialView(BaseModel):
    id: int
    rango_texto: str
    cajero: str
    ventas_texto: str
    esperado_texto: str
    contado_texto: str
    descuadre_texto: str
    descuadre_color: str


class MetodoPagoView(BaseModel):
    """Método de pago activo para los botones de cobro."""

    codigo: str
    nombre: str
    icono: str
    es_efectivo: bool
    es_fiado: bool


class CierrePreviewPedidoRow(BaseModel):
    """Fila de la previsualización del cierre (un pedido con su detalle)."""

    hora: str
    mesa: str
    metodo: str
    items_texto: str     # 'items' choca con ObjectVar.items() en Reflex
    extras: str          # recargo/descuento/propina resumidos, si aplican
    neto_texto: str


class CierrePreviewMovRow(BaseModel):
    hora: str
    tipo: str
    detalle: str
    monto_texto: str


# ─── Mixin de estado ─────────────────────────────────────────────────────────

class CajaTurnoMixin(rx.State, mixin=True):
    """Estado del turno de caja activo, sus movimientos y el cierre con arqueo."""

    # Métodos de pago configurados (activos), para los botones de cobro
    metodos_pago_activos: list[MetodoPagoView] = []
    metodos_pago_codigos: list[str] = []

    # Turno activo
    turno_activo_id: int = 0
    turno_fondo_texto: str = ""
    turno_abierto_desde_texto: str = ""
    turno_abierto_por_nombre: str = ""

    # Formulario de apertura
    turno_apertura_monto: str = ""
    turno_error: str = ""

    # Movimientos (caja chica)
    turno_mov_modal_visible: bool = False
    turno_mov_tipo: str = TipoMovimientoCaja.EGRESO.value
    turno_mov_categoria: str = "Mercado"
    turno_mov_monto: str = ""
    turno_mov_motivo: str = ""
    turno_mov_error: str = ""
    turno_movimientos: list[MovimientoCajaView] = []
    turno_ingresos_texto: str = "S/ 0.00"
    turno_egresos_texto: str = "S/ 0.00"
    # Corrección auditada de un movimiento existente
    turno_mov_editando_id: int = 0        # 0 = alta nueva; >0 = corrigiendo ese id
    turno_mov_confirm_delete_id: int = 0  # id con confirmación de borrado pendiente

    # Cierre con arqueo
    turno_cierre_visible: bool = False
    turno_cierre_resumen: list[ResumenCierreRow] = []
    turno_cierre_esperado: float = 0.0
    turno_cierre_esperado_texto: str = "S/ 0.00"
    turno_cierre_conteo: dict[str, str] = {}
    turno_cierre_notas: str = ""
    turno_cierre_error: str = ""

    # Historial de turnos cerrados
    turno_historial: list[TurnoHistorialView] = []
    turno_historial_visible: bool = False

    # Previsualización del cierre (ver el detalle antes de reimprimir)
    cierre_preview_visible: bool = False
    cierre_preview_turno_id: int = 0
    cierre_preview_titulo: str = ""
    # Resumen en 3 bloques: qué se vendió, cómo se cobró, y el arqueo de efectivo.
    cierre_preview_ventas: list[ResumenCierreRow] = []
    cierre_preview_cobros: list[ResumenCierreRow] = []
    cierre_preview_arqueo: list[ResumenCierreRow] = []
    cierre_preview_pedidos: list[CierrePreviewPedidoRow] = []
    cierre_preview_movimientos: list[CierrePreviewMovRow] = []
    cierre_preview_descuadre_texto: str = ""
    cierre_preview_recon_texto: str = ""
    cierre_preview_recon_cuadra: bool = True

    # ── Computed vars ────────────────────────────────────────────────────────

    @rx.var
    def turno_caja_abierto(self) -> bool:
        return self.turno_activo_id > 0

    @rx.var
    def turno_mov_categorias(self) -> list[str]:
        if self.turno_mov_tipo == TipoMovimientoCaja.INGRESO.value:
            return CATEGORIAS_INGRESO
        return CATEGORIAS_EGRESO

    @rx.var
    def turno_cierre_denominaciones(self) -> list[DenominacionRow]:
        rows: list[DenominacionRow] = []
        for key, valor, etiqueta in DENOMINACIONES_PEN:
            raw = (self.turno_cierre_conteo.get(key) or "").strip()
            try:
                cantidad = max(int(raw), 0) if raw else 0
            except ValueError:
                cantidad = 0
            rows.append(DenominacionRow(
                key=key,
                etiqueta=etiqueta,
                cantidad=raw,
                subtotal_texto=_money(valor * cantidad) if cantidad else "",
            ))
        return rows

    @rx.var
    def turno_cierre_contado(self) -> float:
        total = Decimal("0.00")
        for key, valor, _etiqueta in DENOMINACIONES_PEN:
            raw = (self.turno_cierre_conteo.get(key) or "").strip()
            try:
                cantidad = max(int(raw), 0) if raw else 0
            except ValueError:
                cantidad = 0
            total += valor * cantidad
        return float(total)

    @rx.var
    def turno_cierre_contado_texto(self) -> str:
        return _money(self.turno_cierre_contado)

    @rx.var
    def turno_cierre_descuadre(self) -> float:
        return round(self.turno_cierre_contado - self.turno_cierre_esperado, 2)

    @rx.var
    def turno_cierre_descuadre_texto(self) -> str:
        valor = self.turno_cierre_descuadre
        if valor > 0:
            return f"+{CURRENCY_SYMBOL} {valor:.2f} (sobra)"
        if valor < 0:
            return f"-{CURRENCY_SYMBOL} {abs(valor):.2f} (falta)"
        return f"{CURRENCY_SYMBOL} 0.00 (cuadra)"

    @rx.var
    def turno_cierre_descuadre_color(self) -> str:
        valor = self.turno_cierre_descuadre
        if valor < 0:
            return "#DC2626"
        if valor > 0:
            return "#D97706"
        return "#16A34A"

    # ── Carga ────────────────────────────────────────────────────────────────

    def cargar_turno_caja(self) -> None:
        with self._tenant_session() as session:
            turno = get_turno_abierto(session, self._company_id(), self._sucursal_id())
            if turno is None:
                self.turno_activo_id = 0
                self.turno_fondo_texto = ""
                self.turno_abierto_desde_texto = ""
                self.turno_abierto_por_nombre = ""
                self.turno_movimientos = []
                self.turno_ingresos_texto = _money(0)
                self.turno_egresos_texto = _money(0)
            else:
                self.turno_activo_id = turno.id or 0
                self.turno_fondo_texto = _money(turno.monto_inicial)
                self.turno_abierto_desde_texto = _hora_local(turno.abierto_en)
                usuario = (
                    session.get(UsuarioFood, turno.abierto_por_id)
                    if turno.abierto_por_id
                    else None
                )
                self.turno_abierto_por_nombre = usuario.nombre if usuario else "—"
                self._cargar_movimientos_turno(session, turno)
            self._cargar_metodos_pago(session)
            self._cargar_historial_turnos(session)

    def _cargar_metodos_pago(self, session) -> None:
        """Carga los métodos de pago activos para los botones de cobro."""
        metodos = obtener_metodos(session, self._company_id(), solo_activos=True)
        self.metodos_pago_activos = [
            MetodoPagoView(
                codigo=m.codigo,
                nombre=m.nombre,
                icono=m.icono or "💳",
                es_efectivo=(m.tipo == TipoMetodoPago.EFECTIVO.value),
                es_fiado=(m.tipo == TipoMetodoPago.FIADO.value),
            )
            for m in metodos
        ]
        self.metodos_pago_codigos = [m.codigo for m in metodos]

    def _cargar_movimientos_turno(self, session, turno: TurnoCaja) -> None:
        movimientos = session.exec(
            select(MovimientoCaja)
            .where(
                MovimientoCaja.company_id == turno.company_id,
                MovimientoCaja.turno_id == turno.id,
            )
            .order_by(MovimientoCaja.id.desc())
        ).all()
        usuarios = {
            u.id: u.nombre
            for u in session.exec(
                select(UsuarioFood).where(UsuarioFood.company_id == turno.company_id)
            ).all()
        }
        vistas: list[MovimientoCajaView] = []
        ingresos = Decimal("0.00")
        egresos = Decimal("0.00")
        for m in movimientos:
            es_ingreso = m.tipo == TipoMovimientoCaja.INGRESO.value
            if es_ingreso:
                ingresos += _dec(m.monto)
            else:
                egresos += _dec(m.monto)
            vistas.append(MovimientoCajaView(
                id=m.id or 0,
                hora_texto=_hora_local(m.created_at),
                tipo=m.tipo,
                tipo_label="Ingreso" if es_ingreso else "Egreso",
                categoria=m.categoria,
                monto_texto=_money(m.monto),
                monto_raw=f"{_dec(m.monto):.2f}",
                motivo=m.motivo,
                usuario=usuarios.get(m.usuario_id or 0, "—"),
            ))
        self.turno_movimientos = vistas
        self.turno_ingresos_texto = _money(ingresos)
        self.turno_egresos_texto = _money(egresos)

    def _cargar_historial_turnos(self, session) -> None:
        turnos = session.exec(
            select(TurnoCaja)
            .where(
                TurnoCaja.company_id == self._company_id(),
                TurnoCaja.estado == EstadoTurnoCaja.CERRADO.value,
            )
            .order_by(TurnoCaja.id.desc())
            .limit(15)
        ).all()
        usuarios = {
            u.id: u.nombre
            for u in session.exec(
                select(UsuarioFood).where(UsuarioFood.company_id == self._company_id())
            ).all()
        }
        vistas: list[TurnoHistorialView] = []
        for t in turnos:
            descuadre = _dec(t.descuadre)
            if descuadre < 0:
                color = "#DC2626"
                descuadre_texto = f"-{CURRENCY_SYMBOL} {abs(descuadre):.2f}"
            elif descuadre > 0:
                color = "#D97706"
                descuadre_texto = f"+{CURRENCY_SYMBOL} {descuadre:.2f}"
            else:
                color = "#16A34A"
                descuadre_texto = f"{CURRENCY_SYMBOL} 0.00"
            # "Ventas" = venta neta (ingreso del local), consistente con el detalle
            # y el reporte del día: cobrado por método − propinas + fiado (neto).
            # Las propinas viven en los baldes no-fiado; el fiado ya es neto.
            ventas = (
                _dec(t.total_efectivo) + _dec(t.total_tarjeta) + _dec(t.total_qr)
                - _dec(t.total_propinas) + _dec(t.total_fiado)
            )
            vistas.append(TurnoHistorialView(
                id=t.id or 0,
                rango_texto=f"{_hora_local(t.abierto_en)} → {_hora_local(t.cerrado_en)}",
                cajero=usuarios.get(t.cerrado_por_id or 0, "—"),
                ventas_texto=_money(ventas),
                esperado_texto=_money(t.esperado_efectivo),
                contado_texto=_money(t.contado_efectivo),
                descuadre_texto=descuadre_texto,
                descuadre_color=color,
            ))
        self.turno_historial = vistas

    # ── Apertura ─────────────────────────────────────────────────────────────

    def set_turno_apertura_monto(self, v: str) -> None:
        self.turno_apertura_monto = v

    def abrir_turno(self) -> None:
        self.turno_error = ""
        if self.usuario_actual is None:
            self.turno_error = "Inicia sesión para abrir el turno."
            return
        if not (self.usuario_actual.rol == "Admin" or self.usuario_actual.perm_turno):
            self.turno_error = "No tiene permiso para abrir turno de caja."
            return
        raw = (self.turno_apertura_monto or "").replace(",", ".").strip()
        try:
            monto = Decimal(raw) if raw else Decimal("0.00")
        except InvalidOperation:
            self.turno_error = "Fondo inicial inválido."
            return
        try:
            with self._tenant_session() as session:
                abrir_turno_caja(
                    session, self._company_id(), self.usuario_actual.id or None, monto,
                    self._sucursal_id(),
                )
                session.commit()
        except ValueError as exc:
            self.turno_error = str(exc)
            return
        self.turno_apertura_monto = ""
        self.cargar_turno_caja()
        return rx.toast.success(f"Turno de caja abierto con fondo de {_money(monto)}.")

    # ── Movimientos ──────────────────────────────────────────────────────────

    def set_turno_mov_modal_visible(self, v: bool) -> None:
        self.turno_mov_modal_visible = bool(v)

    def set_turno_cierre_visible(self, v: bool) -> None:
        self.turno_cierre_visible = bool(v)

    def set_turno_historial_visible(self, v: bool) -> None:
        self.turno_historial_visible = bool(v)

    def abrir_mov_modal(self) -> None:
        self.turno_mov_modal_visible = True
        self.turno_mov_error = ""
        self.turno_mov_editando_id = 0
        self.turno_mov_confirm_delete_id = 0
        self.turno_mov_tipo = TipoMovimientoCaja.EGRESO.value
        self.turno_mov_categoria = "Mercado"
        self.turno_mov_monto = ""
        self.turno_mov_motivo = ""

    def cerrar_mov_modal(self) -> None:
        self.turno_mov_modal_visible = False
        self.turno_mov_editando_id = 0
        self.turno_mov_confirm_delete_id = 0

    def set_turno_mov_tipo(self, v: str) -> None:
        self.turno_mov_tipo = v
        opciones = (
            CATEGORIAS_INGRESO
            if v == TipoMovimientoCaja.INGRESO.value
            else CATEGORIAS_EGRESO
        )
        self.turno_mov_categoria = opciones[0]

    def set_turno_mov_categoria(self, v: str) -> None:
        self.turno_mov_categoria = v

    def set_turno_mov_monto(self, v: str) -> None:
        self.turno_mov_monto = v

    def set_turno_mov_motivo(self, v: str) -> None:
        self.turno_mov_motivo = v

    def guardar_movimiento_caja(self) -> None:
        if self.caja_registrando_mov:
            return
        self.turno_mov_error = ""
        editando_id = self.turno_mov_editando_id
        # Corregir un movimiento existente exige el permiso dedicado.
        if editando_id and not self.tiene_perm_corregir:
            self.turno_mov_error = "No tienes permiso para corregir movimientos de caja."
            return
        motivo = (self.turno_mov_motivo or "").strip()
        if not motivo:
            self.turno_mov_error = "El motivo es obligatorio."
            return
        raw = (self.turno_mov_monto or "").replace(",", ".").strip()
        try:
            monto = Decimal(raw) if raw else Decimal("0.00")
        except InvalidOperation:
            self.turno_mov_error = "Monto inválido."
            return
        self.caja_registrando_mov = True
        try:
            with self._tenant_session() as session:
                turno = get_turno_abierto(session, self._company_id(), self._sucursal_id())
                if turno is None:
                    self.turno_mov_error = "No hay turno de caja abierto."
                    self.caja_registrando_mov = False
                    return
                usuario_id = (self.usuario_actual.id or None) if self.usuario_actual else None
                if editando_id:
                    editar_movimiento_caja(
                        session, turno, editando_id, usuario_id,
                        self.usuario_actual.nombre if self.usuario_actual else "",
                        self.turno_mov_tipo, self.turno_mov_categoria, monto, motivo,
                    )
                else:
                    registrar_movimiento_caja(
                        session, turno, usuario_id,
                        self.turno_mov_tipo, self.turno_mov_categoria, monto, motivo,
                    )
                session.commit()
        except ValueError as exc:
            self.turno_mov_error = str(exc)
            self.caja_registrando_mov = False
            return
        self.caja_registrando_mov = False
        self.turno_mov_editando_id = 0
        self.turno_mov_tipo = TipoMovimientoCaja.EGRESO.value
        self.turno_mov_categoria = "Mercado"
        self.turno_mov_monto = ""
        self.turno_mov_motivo = ""
        self.cargar_turno_caja()
        self.turno_mov_modal_visible = True

    def iniciar_edicion_movimiento(self, mov_id: int):
        """Precarga un movimiento en el formulario para corregirlo (auditado)."""
        if not self.tiene_perm_corregir:
            return rx.toast.error("No tienes permiso para corregir movimientos de caja.")
        self.turno_mov_confirm_delete_id = 0
        self.turno_mov_error = ""
        for m in self.turno_movimientos:
            if m.id == mov_id:
                self.turno_mov_editando_id = mov_id
                self.turno_mov_tipo = m.tipo
                self.turno_mov_categoria = m.categoria
                self.turno_mov_monto = m.monto_raw
                self.turno_mov_motivo = m.motivo
                break

    def cancelar_edicion_movimiento(self) -> None:
        """Vuelve el formulario al modo 'alta nueva' sin guardar cambios."""
        self.turno_mov_editando_id = 0
        self.turno_mov_error = ""
        self.turno_mov_tipo = TipoMovimientoCaja.EGRESO.value
        self.turno_mov_categoria = "Mercado"
        self.turno_mov_monto = ""
        self.turno_mov_motivo = ""

    def pedir_borrar_movimiento(self, mov_id: int):
        """Muestra la confirmación en línea para eliminar ese movimiento."""
        if not self.tiene_perm_corregir:
            return rx.toast.error("No tienes permiso para eliminar movimientos de caja.")
        self.turno_mov_confirm_delete_id = mov_id

    def cancelar_borrar_movimiento(self) -> None:
        self.turno_mov_confirm_delete_id = 0

    def eliminar_movimiento(self, mov_id: int):
        """Elimina un movimiento (auditado). Solo con permiso y turno abierto."""
        if not self.tiene_perm_corregir:
            return rx.toast.error("No tienes permiso para eliminar movimientos de caja.")
        self.turno_mov_confirm_delete_id = 0
        try:
            with self._tenant_session() as session:
                turno = get_turno_abierto(session, self._company_id(), self._sucursal_id())
                if turno is None:
                    return rx.toast.error("No hay turno de caja abierto.")
                eliminar_movimiento_caja(
                    session, turno, mov_id,
                    (self.usuario_actual.id or None) if self.usuario_actual else None,
                    self.usuario_actual.nombre if self.usuario_actual else "",
                )
                session.commit()
        except ValueError as exc:
            return rx.toast.error(str(exc))
        # Si estabas corrigiendo justo el que borraste, sal del modo edición.
        if self.turno_mov_editando_id == mov_id:
            self.cancelar_edicion_movimiento()
        self.cargar_turno_caja()
        self.turno_mov_modal_visible = True
        return rx.toast.success("Movimiento eliminado. Queda registrado en auditoría.")

    # ── Cierre con arqueo ────────────────────────────────────────────────────

    def abrir_cierre_turno(self) -> None:
        if self.turno_activo_id == 0:
            return
        with self._tenant_session() as session:
            turno = session.get(TurnoCaja, self.turno_activo_id)
            if turno is None or turno.estado != EstadoTurnoCaja.ABIERTO.value:
                self.cargar_turno_caja()
                return
            resumen = calcular_resumen_turno(session, turno)
            nombres = mapa_nombres(session, turno.company_id)
            tipos = mapa_tipos(session, turno.company_id)
            por_metodo = resumen.get("por_metodo", {})  # type: ignore[assignment]
            # Info de ventas primero (lo que facturó el local).
            filas = [
                ResumenCierreRow(etiqueta="Ventas (netas)", monto_texto=_money(resumen["ventas_netas"])),
                ResumenCierreRow(etiqueta="Propinas del turno", monto_texto=_money(resumen["propinas"])),
            ]
            # Cobros NO-efectivo (Yape, tarjeta, …): entran a ventas pero NO al cajón.
            for cod in [m.codigo for m in obtener_metodos(session, turno.company_id)]:
                monto = por_metodo.get(cod)
                bucket = _bucket_tipo(tipos.get(cod, TipoMetodoPago.DIGITAL.value))
                if monto and bucket not in ("efectivo", "fiado"):
                    filas.append(ResumenCierreRow(
                        etiqueta=f"Cobrado en {nombres.get(cod, cod.capitalize())}",
                        monto_texto=_money(monto)))
            if resumen["fiado"]:
                filas.append(ResumenCierreRow(
                    etiqueta="Fiado (no entra a caja)", monto_texto=_money(resumen["fiado"])))
            # Armado del efectivo del cajón, con signos, justo antes del footer.
            filas.append(ResumenCierreRow(
                etiqueta="Fondo inicial", monto_texto=_money(turno.monto_inicial)))
            filas.append(ResumenCierreRow(
                etiqueta="+ Cobrado en efectivo", monto_texto=_money(resumen["efectivo"])))
            if resumen["ingresos"]:
                filas.append(ResumenCierreRow(
                    etiqueta="+ Otros ingresos", monto_texto=_money(resumen["ingresos"])))
            if resumen["egresos"]:
                filas.append(ResumenCierreRow(
                    etiqueta="− Egresos / gastos", monto_texto="- " + _money(resumen["egresos"])))
            self.turno_cierre_resumen = filas
            self.turno_cierre_esperado = float(resumen["esperado_efectivo"])
            self.turno_cierre_esperado_texto = _money(resumen["esperado_efectivo"])
        self.turno_cierre_conteo = {}
        self.turno_cierre_notas = ""
        self.turno_cierre_error = ""
        self.turno_cierre_visible = True

    def cancelar_cierre_turno(self) -> None:
        self.turno_cierre_visible = False
        self.turno_cierre_error = ""

    def set_conteo_denominacion(self, key: str, v: str) -> None:
        self.turno_cierre_conteo[key] = v

    def set_turno_cierre_notas(self, v: str) -> None:
        self.turno_cierre_notas = v

    def confirmar_cierre_turno(self):
        if self.turno_cerrando:
            return
        self.turno_cerrando = True
        self.turno_cierre_error = ""
        if self.usuario_actual is not None and not (
            self.usuario_actual.rol == "Admin" or self.usuario_actual.perm_turno
        ):
            self.turno_cierre_error = "No tiene permiso para cerrar turno de caja."
            self.turno_cerrando = False
            return
        conteo_limpio: dict[str, int] = {}
        for key, _valor, _etiqueta in DENOMINACIONES_PEN:
            raw = (self.turno_cierre_conteo.get(key) or "").strip()
            if not raw:
                continue
            try:
                cantidad = int(raw)
            except ValueError:
                self.turno_cierre_error = "Hay cantidades inválidas en el arqueo."
                return
            if cantidad < 0:
                self.turno_cierre_error = "Las cantidades no pueden ser negativas."
                return
            if cantidad:
                conteo_limpio[key] = cantidad
        contado = Decimal(str(round(self.turno_cierre_contado, 2)))
        ticket_html = ""
        try:
            with self._tenant_session() as session:
                turno = session.get(TurnoCaja, self.turno_activo_id)
                if turno is None:
                    self.turno_cierre_error = "El turno ya no existe."
                    return
                cerrar_turno_caja(
                    session,
                    turno,
                    (self.usuario_actual.id or None) if self.usuario_actual else None,
                    contado,
                    arqueo_detalle=json.dumps(conteo_limpio) if conteo_limpio else None,
                    notas=self.turno_cierre_notas,
                )
                session.commit()
                session.refresh(turno)
                data = self._build_cierre_data(session, turno)
                # Ticket térmico = SOLO resumen (sin volcar los pedidos). El
                # detalle por pedido queda en el PDF y en Historial. Ver
                # _print_cierre_ticket para el detalle de por qué.
                _cierre_lines = build_cash_close_ticket_lines(
                    company_name=data["empresa"],
                    turno_id=turno.id or 0,
                    abierto_por=data["abierto_por"],
                    cerrado_por=data["cerrado_por"],
                    abierto_en_texto=data["abierto_en"],
                    cerrado_en_texto=data["cerrado_en"],
                    resumen_rows=self._cierre_resumen_rows(data),
                    descuadre_texto=data["descuadre_texto"],
                    notas=data["notas"],
                    paper_width_mm=self._ticket_paper_width_mm(),
                    detalle_movimientos=data["movimientos"],
                )
                ticket_html = render_ticket_html(
                    "Cierre de Caja", _cierre_lines, self._ticket_paper_width_mm()
                )
        except ValueError as exc:
            self.turno_cierre_error = str(exc)
            self.turno_cerrando = False
            return
        self.turno_cerrando = False
        self.turno_cierre_visible = False
        self.turno_cierre_conteo = {}
        self.cargar_turno_caja()
        eventos = [rx.toast.success(
            "Turno de caja cerrado. Puedes reimprimirlo o descargarlo desde Historial.",
            duration=6000,
        )]
        _evt = self._imprimir_o_encolar(
            rol="caja",
            tipo_doc="comprobante",
            texto=ticket_text(_cierre_lines),
            html=ticket_html,
        )
        if _evt is not None:
            eventos.append(_evt)
        return eventos

    # ── Historial ────────────────────────────────────────────────────────────

    def toggle_historial_turnos(self) -> None:
        self.turno_historial_visible = not self.turno_historial_visible

    # ── PDF / impresión detallada del cierre ────────────────────────────────

    def _build_cierre_data(self, session, turno: TurnoCaja) -> dict:
        """Recolecta toda la info del turno para PDF e impresión."""
        usuarios = {
            u.id: u.nombre
            for u in session.exec(
                select(UsuarioFood).where(UsuarioFood.company_id == turno.company_id)
            ).all()
        }
        mesas = {
            m.id: m.nombre or f"Mesa {m.numero}"
            for m in session.exec(
                select(Mesa).where(Mesa.company_id == turno.company_id)
            ).all()
        }
        pedidos = session.exec(
            select(Pedido).where(
                Pedido.company_id == turno.company_id,
                Pedido.turno_caja_id == turno.id,
                Pedido.estado != EstadoPedido.CANCELADO.value,
            ).order_by(Pedido.cerrado_en)
        ).all()
        pagos = session.exec(
            select(PagoPedido).where(
                PagoPedido.company_id == turno.company_id,
                PagoPedido.turno_caja_id == turno.id,
            )
        ).all()
        pagos_por_pedido: dict[int, list] = {}
        for p in pagos:
            pagos_por_pedido.setdefault(p.pedido_id, []).append(p)
        productos = {
            p.id: p.nombre
            for p in session.exec(
                select(Producto).where(Producto.company_id == turno.company_id)
            ).all()
        }
        nombres = mapa_nombres(session, turno.company_id)
        tipos = mapa_tipos(session, turno.company_id)
        detalle_pedidos = []
        # Desglose de lo cobrado por método real (Efectivo, Yape, Plin, …) para
        # mostrarlo detallado en vez del balde genérico "QR/Yape".
        cobrado_por_metodo: dict[str, Decimal] = {}
        # Reconciliación: Σ (total a cobrar por pedido) debe igualar lo cobrado.
        ventas_esperadas = Decimal("0.00")
        cobrado_por_pagos = Decimal("0.00")
        # Venta neta = ingreso del local (sin propina). Es el "Ventas" que debe
        # coincidir con el reporte; la propina va como línea aparte.
        ventas_netas = Decimal("0.00")
        # Desglose de ventas: subtotal de productos + recargos por concepto
        # (Envase/Delivery/Servicio…) − descuentos = venta neta. Para que la hoja
        # muestre de qué se compone el total.
        subtotal_productos = Decimal("0.00")
        recargos_acc: dict[str, Decimal] = {}
        total_descuentos = Decimal("0.00")
        for ped in pedidos:
            items = session.exec(
                select(DetallePedido).where(DetallePedido.pedido_id == ped.id)
            ).all()
            items_texto = ", ".join(
                f"{productos.get(d.producto_id, '?')} (x{d.cantidad})" for d in items if d.cantidad > 0
            )
            pags = pagos_por_pedido.get(ped.id or 0, [])
            if pags:
                metodo = ", ".join(
                    f"{(p.metodo or 'efectivo').capitalize()}: {_money(p.monto)}" for p in pags
                )
            else:
                metodo = (ped.metodo_pago or "efectivo").capitalize()
            recargo = _dec(ped.recargo)
            # Venta neta = subtotal ítems + recargo (envases/delivery) − descuento.
            neto = _dec(ped.total) + recargo - _dec(ped.descuento)
            # Total a cobrar = venta neta + propina; y lo realmente cobrado.
            ventas_esperadas += neto + _dec(ped.propina)
            ventas_netas += neto
            subtotal_productos += _dec(ped.total)
            if recargo > 0:
                concepto = (ped.recargo_concepto or "Recargo").strip() or "Recargo"
                recargos_acc[concepto] = (
                    recargos_acc.get(concepto, Decimal("0.00")) + recargo
                )
            total_descuentos += _dec(ped.descuento)
            if pags:
                cobrado_por_pagos += sum((_dec(p.monto) for p in pags), Decimal("0.00"))
                for p in pags:
                    cod = (p.metodo or "efectivo").lower()
                    cobrado_por_metodo[cod] = (
                        cobrado_por_metodo.get(cod, Decimal("0.00")) + _dec(p.monto)
                    )
            else:
                cobrado_por_pagos += neto + _dec(ped.propina)
                cod = (ped.metodo_pago or "efectivo").lower()
                cobrado_por_metodo[cod] = (
                    cobrado_por_metodo.get(cod, Decimal("0.00")) + neto + _dec(ped.propina)
                )
            detalle_pedidos.append({
                "id": ped.id,
                "hora": _hora_local(ped.cerrado_en or ped.updated_at),
                "mesa": mesas.get(ped.mesa_id or 0, "Para llevar"),
                "mozo": usuarios.get(ped.mozo_id or 0, "—"),
                "metodo": metodo,
                "items": items_texto,
                "recargo": recargo,
                "recargo_concepto": ped.recargo_concepto or "",
                "descuento": _dec(ped.descuento),
                "propina": _dec(ped.propina),
                "neto": neto,
            })
        movimientos = session.exec(
            select(MovimientoCaja).where(
                MovimientoCaja.company_id == turno.company_id,
                MovimientoCaja.turno_id == turno.id,
            ).order_by(MovimientoCaja.created_at)
        ).all()
        movs = [{
            "hora": _hora_local(m.created_at),
            "tipo": m.tipo.capitalize(),
            "categoria": m.categoria,
            "monto": _money(m.monto),
            "motivo": m.motivo,
            "usuario": usuarios.get(m.usuario_id or 0, "—"),
        } for m in movimientos]
        descuadre = _dec(turno.descuadre)
        if descuadre > 0:
            descuadre_texto = f"+{_money(descuadre)} (sobra)"
        elif descuadre < 0:
            descuadre_texto = f"-{_money(abs(descuadre))} (falta)"
        else:
            descuadre_texto = f"{_money(0)} (cuadra)"
        # Reconciliación de ventas: lo cobrado (Σ pagos) vs lo esperado por los
        # pedidos (Σ total a cobrar). Si difiere, hay pagos que no coinciden con
        # la cuenta (sobrepago/vuelto mal registrado o edición post-cobro).
        recon_ventas = cobrado_por_pagos - ventas_esperadas
        if recon_ventas == 0:
            recon_ventas_texto = f"{_money(0)} (cuadra)"
        elif recon_ventas > 0:
            recon_ventas_texto = f"+{_money(recon_ventas)} (cobrado de más)"
        else:
            recon_ventas_texto = f"-{_money(abs(recon_ventas))} (cobrado de menos)"
        # Lista ordenada de "cobrado por método" (solo métodos usados, en el orden
        # configurado). El fiado no es dinero cobrado: no entra a esta lista.
        cobrado_metodo_rows: list[dict] = []
        vistos: set[str] = set()
        for cod in [m.codigo for m in obtener_metodos(session, turno.company_id)]:
            monto = cobrado_por_metodo.get(cod)
            es_fiado = _bucket_tipo(tipos.get(cod, TipoMetodoPago.DIGITAL.value)) == "fiado"
            if monto and not es_fiado:
                cobrado_metodo_rows.append(
                    {"nombre": nombres.get(cod, cod.capitalize()), "monto_texto": _money(monto)}
                )
            vistos.add(cod)
        for cod, monto in cobrado_por_metodo.items():
            if cod in vistos or not monto:
                continue
            if _bucket_tipo(tipos.get(cod, TipoMetodoPago.DIGITAL.value)) == "fiado":
                continue
            cobrado_metodo_rows.append(
                {"nombre": nombres.get(cod, cod.capitalize()), "monto_texto": _money(monto)}
            )
        return {
            "empresa": self.config_nombre_local or "TUWAYKIFOOD",
            "turno_id": turno.id,
            "abierto_por": usuarios.get(turno.abierto_por_id or 0, "—"),
            "cerrado_por": usuarios.get(turno.cerrado_por_id or 0, "—"),
            "abierto_en": _hora_local(turno.abierto_en),
            "cerrado_en": _hora_local(turno.cerrado_en),
            "fondo_inicial": _money(turno.monto_inicial),
            "total_efectivo": _money(turno.total_efectivo),
            "total_tarjeta": _money(turno.total_tarjeta),
            "total_qr": _money(turno.total_qr),
            "total_fiado": _money(turno.total_fiado),
            "total_propinas": _money(turno.total_propinas),
            "total_ingresos": _money(turno.total_ingresos),
            "total_egresos": _money(turno.total_egresos),
            "esperado": _money(turno.esperado_efectivo),
            "contado": _money(turno.contado_efectivo),
            "descuadre_texto": descuadre_texto,
            "recon_ventas_texto": recon_ventas_texto,
            "recon_ventas_cuadra": recon_ventas == 0,
            "notas": turno.notas_cierre or "",
            "pedidos": detalle_pedidos,
            "movimientos": movs,
            # Ventas (netas) = ingreso real del local, SIN propina. Coincide con
            # el "Ventas" del reporte del día.
            "ventas_netas": _money(ventas_netas),
            # Total cobrado = dinero que efectivamente entró (Σ pagos, incluye
            # propina). Es lo que usa el arqueo de caja.
            "total_cobrado": _money(cobrado_por_pagos),
            # Compat: el "Total ventas" del cierre ahora es la venta neta.
            "total_ventas_neto": _money(ventas_netas),
            # Cobrado detallado por método real (Efectivo, Yape, Plin, …).
            "cobrado_por_metodo": cobrado_metodo_rows,
            # Flags para no ensuciar el resumen con líneas en cero.
            "hay_fiado": _dec(turno.total_fiado) > 0,
            "hay_ingresos": _dec(turno.total_ingresos) > 0,
            "hay_egresos": _dec(turno.total_egresos) > 0,
            # Desglose del bloque de ventas (subtotal + extras por concepto).
            "subtotal_productos": _money(subtotal_productos),
            "recargos": [
                {"concepto": c, "monto_texto": _money(m)}
                for c, m in recargos_acc.items()
            ],
            "total_descuentos": _money(total_descuentos),
            "hay_descuentos": total_descuentos > 0,
            "hay_extras": bool(recargos_acc) or total_descuentos > 0,
        }

    @staticmethod
    def _cierre_resumen_rows(data: dict) -> list[tuple[str, str]]:
        """Filas del resumen para el ticket, en 3 bloques: ventas, cobros por
        método real y arqueo de efectivo. Compartido por el ticket de cierre y
        la reimpresión para que siempre digan lo mismo."""
        rows: list[tuple[str, str]] = [
            (etiqueta, monto) for etiqueta, monto, _enf in _cierre_ventas_rows(data)
        ]
        rows.append(("-- Cobrado por metodo --", ""))
        for m in data["cobrado_por_metodo"]:
            rows.append((f"  {m['nombre']}", m["monto_texto"]))
        rows.append(("Total cobrado", data["total_cobrado"]))
        rows.append(("-- Arqueo de efectivo --", ""))
        rows.append(("Fondo inicial", data["fondo_inicial"]))
        rows.append(("+ Cobrado en efectivo", data["total_efectivo"]))
        if data["hay_ingresos"]:
            rows.append(("+ Ingresos de caja", data["total_ingresos"]))
        if data["hay_egresos"]:
            rows.append(("- Egresos de caja", data["total_egresos"]))
        rows.append(("= Esperado en caja", data["esperado"]))
        rows.append(("Contado en caja", data["contado"]))
        return rows

    def descargar_pdf_cierre(self):
        """Descarga el PDF del cierre del turno activo (botón del modal de cierre)."""
        if self.turno_activo_id == 0:
            return rx.toast.error("No hay turno para generar el PDF.")
        return self._generar_pdf_cierre(self.turno_activo_id)

    def descargar_pdf_cierre_turno(self, turno_id: int):
        """Descarga el PDF del cierre de un turno ya cerrado (desde el historial)."""
        return self._generar_pdf_cierre(turno_id)

    def _generar_pdf_cierre(self, turno_id: int):
        if not turno_id:
            return rx.toast.error("No hay turno para generar el PDF.")
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import cm, mm
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        )
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

        with self._tenant_session() as session:
            turno = session.get(TurnoCaja, turno_id)
            if turno is None:
                return rx.toast.error("El turno ya no existe.")
            data = self._build_cierre_data(session, turno)

        buf = io.BytesIO()
        doc = SimpleDocTemplate(
            buf, pagesize=A4,
            leftMargin=1.5 * cm, rightMargin=1.5 * cm,
            topMargin=1.2 * cm, bottomMargin=1.2 * cm,
        )
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(
            "PDFTitle", parent=styles["Title"], fontSize=16, spaceAfter=2 * mm,
        ))
        styles.add(ParagraphStyle(
            "PDFSub", parent=styles["Normal"], fontSize=9,
            textColor=colors.grey, spaceAfter=6 * mm,
        ))
        styles.add(ParagraphStyle(
            "Section", parent=styles["Heading2"], fontSize=12,
            spaceBefore=5 * mm, spaceAfter=2 * mm,
            textColor=colors.HexColor("#1E293B"),
        ))
        hdr_style = TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E1")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
        ])
        elems = []
        elems.append(Paragraph(f"Resumen de Caja — {data['empresa']}", styles["PDFTitle"]))
        elems.append(Paragraph(
            f"Turno #{data['turno_id']} · Apertura: {data['abierto_en']} por {data['abierto_por']}"
            f" · Cierre: {data['cerrado_en']} por {data['cerrado_por']}",
            styles["PDFSub"],
        ))

        # Bloque 1 — Ventas del turno (facturado por el local), desglosado en
        # subtotal de productos + extras por concepto − descuentos = venta neta.
        elems.append(Paragraph("Ventas del turno", styles["Section"]))
        ventas_data = [["Concepto", "Monto"]]
        for etiqueta, monto, _enf in _cierre_ventas_rows(data):
            ventas_data.append([etiqueta, monto])
        t = Table(ventas_data, colWidths=[10 * cm, 7 * cm])
        t.setStyle(hdr_style)
        elems.append(t)
        elems.append(Spacer(1, 4 * mm))

        # Bloque 2 — Cobrado por método real (Efectivo, Yape, Plin, …).
        elems.append(Paragraph("Cobrado por método", styles["Section"]))
        met_data = [["Método", "Monto"]]
        for m in data["cobrado_por_metodo"]:
            met_data.append([m["nombre"], m["monto_texto"]])
        met_data.append(["Total cobrado", data["total_cobrado"]])
        t2 = Table(met_data, colWidths=[10 * cm, 7 * cm])
        t2.setStyle(hdr_style)
        elems.append(t2)
        elems.append(Spacer(1, 4 * mm))

        # Bloque 3 — Arqueo de caja: solo el efectivo entra al cajón.
        elems.append(Paragraph("Arqueo de caja (efectivo)", styles["Section"]))
        arqueo_data = [
            ["Concepto", "Monto"],
            ["Fondo inicial", data["fondo_inicial"]],
            ["+ Cobrado en efectivo", data["total_efectivo"]],
        ]
        if data["hay_ingresos"]:
            arqueo_data.append(["+ Ingresos de caja", data["total_ingresos"]])
        if data["hay_egresos"]:
            arqueo_data.append(["- Egresos de caja", f"- {data['total_egresos']}"])
        arqueo_data.append(["= Esperado en caja", data["esperado"]])
        arqueo_data.append(["Contado en caja", data["contado"]])
        arqueo_data.append(["Descuadre", data["descuadre_texto"]])
        t3 = Table(arqueo_data, colWidths=[10 * cm, 7 * cm])
        t3.setStyle(hdr_style)
        elems.append(t3)
        elems.append(Paragraph(
            "El esperado en caja solo cuenta el efectivo (fondo + cobros en efectivo "
            "+ ingresos − egresos). Yape, tarjeta y transferencias no entran al cajón.",
            styles["PDFSub"],
        ))
        if not data["recon_ventas_cuadra"]:
            elems.append(Paragraph(
                f"Reconciliación (cobrado vs pedidos): {data['recon_ventas_texto']}",
                styles["PDFSub"],
            ))
        elems.append(Spacer(1, 4 * mm))

        # Detalle de pedidos
        if data["pedidos"]:
            elems.append(Paragraph(f"Detalle de Ingresos ({len(data['pedidos'])} pedidos)", styles["Section"]))
            ped_data = [["Hora", "Mesa", "Método", "Detalle", "Monto"]]
            for p in data["pedidos"]:
                # El detalle incluye los conceptos que ajustan la cuenta para
                # que el PDF cuadre exactamente con el reporte.
                extras = []
                if p.get("recargo", 0) > 0:
                    extras.append(f"+ {p.get('recargo_concepto') or 'Recargo'}: {_money(p['recargo'])}")
                if p.get("descuento", 0) > 0:
                    extras.append(f"- Descuento: {_money(p['descuento'])}")
                if p.get("propina", 0) > 0:
                    extras.append(f"Propina: {_money(p['propina'])}")
                detalle_txt = p["items"][:120]
                if extras:
                    detalle_txt = (detalle_txt + " · " + " · ".join(extras)).strip(" ·")
                items_p = Paragraph(detalle_txt, styles["Normal"])
                ped_data.append([
                    p["hora"], p["mesa"], p["metodo"],
                    items_p, _money(p["neto"]),
                ])
            col_w = [2.2 * cm, 2 * cm, 3 * cm, 7 * cm, 2.8 * cm]
            t3 = Table(ped_data, colWidths=col_w, repeatRows=1)
            t3.setStyle(hdr_style)
            elems.append(t3)
            elems.append(Spacer(1, 4 * mm))

        # Movimientos de caja
        if data["movimientos"]:
            elems.append(Paragraph("Movimientos de Caja", styles["Section"]))
            mov_data = [["Hora", "Tipo", "Categoría", "Motivo", "Monto"]]
            for m in data["movimientos"]:
                mov_data.append([m["hora"], m["tipo"], m["categoria"], m["motivo"], m["monto"]])
            t4 = Table(mov_data, colWidths=[2.2 * cm, 2 * cm, 2.5 * cm, 7.5 * cm, 2.8 * cm])
            t4.setStyle(hdr_style)
            elems.append(t4)
            elems.append(Spacer(1, 4 * mm))

        if data["notas"]:
            elems.append(Paragraph(f"Notas: {data['notas']}", styles["Normal"]))

        doc.build(elems)
        from tuwayki_core.utils.timezone import utc_now_naive as _now
        filename = f"cierre_caja_{_now().strftime('%Y%m%d_%H%M')}.pdf"
        return rx.download(data=buf.getvalue(), filename=filename)

    def _print_cierre_ticket(self, turno_id: int):
        """Genera e imprime el ticket detallado de cierre para cualquier turno."""
        with self._tenant_session() as session:
            turno = session.get(TurnoCaja, turno_id)
            if turno is None:
                return rx.toast.error("El turno ya no existe.")
            data = self._build_cierre_data(session, turno)
            # Ticket térmico = SOLO resumen. El detalle por pedido NO se imprime
            # (queda en el PDF y en Historial): volcarlo hacía un rollo de ~1 m
            # ilegible. Los movimientos de caja sí van, porque son pocos y
            # justifican los ingresos/egresos del arqueo.
            _cierre_lines = build_cash_close_ticket_lines(
                company_name=data["empresa"],
                turno_id=turno.id or 0,
                abierto_por=data["abierto_por"],
                cerrado_por=data["cerrado_por"],
                abierto_en_texto=data["abierto_en"],
                cerrado_en_texto=data["cerrado_en"],
                resumen_rows=self._cierre_resumen_rows(data),
                descuadre_texto=data["descuadre_texto"],
                notas=data["notas"],
                paper_width_mm=self._ticket_paper_width_mm(),
                detalle_movimientos=data["movimientos"],
                recon_ventas_texto=(
                    "" if data.get("recon_ventas_cuadra", True)
                    else data.get("recon_ventas_texto", "")
                ),
            )
            ticket_html = render_ticket_html(
                "Cierre de Caja", _cierre_lines, self._ticket_paper_width_mm()
            )
        return self._imprimir_o_encolar(
            rol="caja",
            tipo_doc="comprobante",
            texto=ticket_text(_cierre_lines),
            html=ticket_html,
            feedback=True,
        )

    def imprimir_resumen_cierre(self):
        """Imprime ticket detallado del cierre del turno activo."""
        if self.turno_activo_id == 0:
            return rx.toast.error("No hay turno para imprimir.")
        return self._print_cierre_ticket(self.turno_activo_id)

    def reimprimir_cierre_turno(self, turno_id: int):
        """Reimprime ticket de cierre desde el historial de turnos cerrados."""
        return self._print_cierre_ticket(turno_id)

    def set_cierre_preview_visible(self, v: bool) -> None:
        self.cierre_preview_visible = bool(v)

    def previsualizar_cierre_turno(self, turno_id: int):
        """Abre un modal con el detalle del cierre para verlo antes de reimprimir."""
        with self._tenant_session() as session:
            turno = session.get(TurnoCaja, turno_id)
            if turno is None:
                return rx.toast.error("El turno ya no existe.")
            data = self._build_cierre_data(session, turno)
        self.cierre_preview_turno_id = turno_id
        self.cierre_preview_titulo = (
            f"Turno #{data['turno_id']} · {data['abierto_en']} → {data['cerrado_en']}"
        )
        # Bloque 1 — Ventas del turno (lo que facturó el local; sin efectivo aún).
        # Desglosado: subtotal productos + extras por concepto = venta neta.
        self.cierre_preview_ventas = [
            ResumenCierreRow(etiqueta=et, monto_texto=mo, enfasis=en)
            for et, mo, en in _cierre_ventas_rows(data)
        ]
        # Bloque 2 — Cobrado por método real (Efectivo, Yape, Plin, …) + total.
        cobros = [
            ResumenCierreRow(etiqueta=m["nombre"], monto_texto=m["monto_texto"])
            for m in data["cobrado_por_metodo"]
        ]
        cobros.append(ResumenCierreRow(
            etiqueta="Total cobrado", monto_texto=data["total_cobrado"], enfasis=True))
        self.cierre_preview_cobros = cobros
        # Bloque 3 — Arqueo de caja: SOLO efectivo entra al cajón.
        arqueo = [
            ResumenCierreRow(etiqueta="Fondo inicial", monto_texto=data["fondo_inicial"]),
            ResumenCierreRow(etiqueta="+ Cobrado en efectivo", monto_texto=data["total_efectivo"]),
        ]
        if data["hay_ingresos"]:
            arqueo.append(ResumenCierreRow(
                etiqueta="+ Ingresos de caja", monto_texto=data["total_ingresos"]))
        if data["hay_egresos"]:
            arqueo.append(ResumenCierreRow(
                etiqueta="− Egresos de caja", monto_texto=f"- {data['total_egresos']}"))
        arqueo.append(ResumenCierreRow(
            etiqueta="= Esperado en caja", monto_texto=data["esperado"], enfasis=True))
        arqueo.append(ResumenCierreRow(etiqueta="Contado en caja", monto_texto=data["contado"]))
        self.cierre_preview_arqueo = arqueo
        pedidos_rows: list[CierrePreviewPedidoRow] = []
        for p in data["pedidos"]:
            extras = []
            if p.get("recargo", 0) > 0:
                extras.append(f"+ {p.get('recargo_concepto') or 'Recargo'}: {_money(p['recargo'])}")
            if p.get("descuento", 0) > 0:
                extras.append(f"- Descuento: {_money(p['descuento'])}")
            if p.get("propina", 0) > 0:
                extras.append(f"Propina: {_money(p['propina'])}")
            pedidos_rows.append(CierrePreviewPedidoRow(
                hora=p.get("hora", ""),
                mesa=p.get("mesa", ""),
                metodo=p.get("metodo", ""),
                items_texto=p.get("items", ""),
                extras=" · ".join(extras),
                neto_texto=_money(p["neto"]),
            ))
        self.cierre_preview_pedidos = pedidos_rows
        self.cierre_preview_movimientos = [
            CierrePreviewMovRow(
                hora=m.get("hora", ""),
                tipo=m.get("tipo", ""),
                detalle=f"{m.get('categoria', '')}: {m.get('motivo', '')}",
                monto_texto=m.get("monto", ""),
            )
            for m in data["movimientos"]
        ]
        self.cierre_preview_descuadre_texto = data["descuadre_texto"]
        self.cierre_preview_recon_texto = data["recon_ventas_texto"]
        self.cierre_preview_recon_cuadra = data["recon_ventas_cuadra"]
        self.cierre_preview_visible = True

    def reimprimir_cierre_desde_preview(self):
        """Reimprime el cierre que se está previsualizando y cierra el modal."""
        turno_id = self.cierre_preview_turno_id
        self.cierre_preview_visible = False
        if turno_id:
            return self._print_cierre_ticket(turno_id)
