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

import json
from decimal import Decimal, InvalidOperation

import reflex as rx
from pydantic import BaseModel
from sqlmodel import select

from tuwayki_core.utils.timezone import format_local_datetime, utc_now_naive

from app.models.food import (
    EstadoPedido,
    EstadoTurnoCaja,
    MovimientoCaja,
    PagoPedido,
    Pedido,
    TipoMovimientoCaja,
    TurnoCaja,
    UsuarioFood,
)
from app.services.receipt_service import (
    build_print_script,
    generate_cash_close_ticket_html,
)

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

def get_turno_abierto(session, company_id: int) -> TurnoCaja | None:
    """Turno abierto de la empresa, o None. Solo puede existir uno a la vez."""
    return session.exec(
        select(TurnoCaja)
        .where(
            TurnoCaja.company_id == company_id,
            TurnoCaja.estado == EstadoTurnoCaja.ABIERTO.value,
        )
        .order_by(TurnoCaja.id.desc())
    ).first()


def abrir_turno_caja(
    session,
    company_id: int,
    usuario_id: int | None,
    monto_inicial: Decimal,
) -> TurnoCaja:
    monto_inicial = _dec(monto_inicial)
    if monto_inicial < 0:
        raise ValueError("El fondo inicial no puede ser negativo.")
    if get_turno_abierto(session, company_id) is not None:
        raise ValueError("Ya hay un turno de caja abierto. Ciérralo antes de abrir otro.")
    turno = TurnoCaja(
        company_id=company_id,
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
    resumen: dict[str, Decimal] = {
        "efectivo": Decimal("0.00"),
        "tarjeta": Decimal("0.00"),
        "qr": Decimal("0.00"),
        "fiado": Decimal("0.00"),
        "propinas": Decimal("0.00"),
    }
    pedidos_con_pagos: set[int] = set()
    for pago in pagos:
        if pago.pedido_id not in pedidos_validos:
            continue  # pago de un pedido cancelado
        pedidos_con_pagos.add(pago.pedido_id)
        metodo = (pago.metodo or "efectivo").lower()
        monto = _dec(pago.monto)
        if metodo == "fiado":
            resumen["fiado"] += monto
        elif metodo == "tarjeta":
            resumen["tarjeta"] += monto
        elif metodo == "qr":
            resumen["qr"] += monto
        else:
            resumen["efectivo"] += monto
    for pedido in pedidos:
        propina = _dec(pedido.propina)
        resumen["propinas"] += propina
        if (pedido.id or 0) in pedidos_con_pagos:
            continue
        neto = _dec(pedido.total) - _dec(pedido.descuento)
        metodo = (pedido.metodo_pago or "efectivo").lower()
        if metodo == "fiado":
            resumen["fiado"] += neto
        elif metodo == "tarjeta":
            resumen["tarjeta"] += neto + propina
        elif metodo == "qr":
            resumen["qr"] += neto + propina
        else:
            resumen["efectivo"] += neto + propina
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


# ─── Views para la UI ────────────────────────────────────────────────────────

class MovimientoCajaView(BaseModel):
    id: int
    hora_texto: str
    tipo: str
    tipo_label: str
    categoria: str
    monto_texto: str
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


class TurnoHistorialView(BaseModel):
    id: int
    rango_texto: str
    cajero: str
    ventas_texto: str
    esperado_texto: str
    contado_texto: str
    descuadre_texto: str
    descuadre_color: str


# ─── Mixin de estado ─────────────────────────────────────────────────────────

class CajaTurnoMixin(rx.State, mixin=True):
    """Estado del turno de caja activo, sus movimientos y el cierre con arqueo."""

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
            turno = get_turno_abierto(session, self._company_id())
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
            self._cargar_historial_turnos(session)

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
            ventas = _dec(t.total_efectivo) + _dec(t.total_tarjeta) + _dec(t.total_qr)
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
        raw = (self.turno_apertura_monto or "").replace(",", ".").strip()
        try:
            monto = Decimal(raw) if raw else Decimal("0.00")
        except InvalidOperation:
            self.turno_error = "Fondo inicial inválido."
            return
        try:
            with self._tenant_session() as session:
                abrir_turno_caja(
                    session, self._company_id(), self.usuario_actual.id, monto
                )
                session.commit()
        except ValueError as exc:
            self.turno_error = str(exc)
            return
        self.turno_apertura_monto = ""
        self.cargar_turno_caja()
        self.mensaje = f"Turno de caja abierto con fondo de {_money(monto)}."

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
        self.turno_mov_tipo = TipoMovimientoCaja.EGRESO.value
        self.turno_mov_categoria = "Mercado"
        self.turno_mov_monto = ""
        self.turno_mov_motivo = ""

    def cerrar_mov_modal(self) -> None:
        self.turno_mov_modal_visible = False

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
        self.turno_mov_error = ""
        raw = (self.turno_mov_monto or "").replace(",", ".").strip()
        try:
            monto = Decimal(raw) if raw else Decimal("0.00")
        except InvalidOperation:
            self.turno_mov_error = "Monto inválido."
            return
        try:
            with self._tenant_session() as session:
                turno = get_turno_abierto(session, self._company_id())
                if turno is None:
                    self.turno_mov_error = "No hay turno de caja abierto."
                    return
                registrar_movimiento_caja(
                    session,
                    turno,
                    self.usuario_actual.id if self.usuario_actual else None,
                    self.turno_mov_tipo,
                    self.turno_mov_categoria,
                    monto,
                    self.turno_mov_motivo,
                )
                session.commit()
        except ValueError as exc:
            self.turno_mov_error = str(exc)
            return
        self.turno_mov_monto = ""
        self.turno_mov_motivo = ""
        self.cargar_turno_caja()
        self.turno_mov_modal_visible = True

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
            self.turno_cierre_resumen = [
                ResumenCierreRow(etiqueta="Fondo inicial", monto_texto=_money(turno.monto_inicial)),
                ResumenCierreRow(etiqueta="Ventas en efectivo", monto_texto=_money(resumen["efectivo"])),
                ResumenCierreRow(etiqueta="Ventas con tarjeta", monto_texto=_money(resumen["tarjeta"])),
                ResumenCierreRow(etiqueta="Ventas por QR / Yape", monto_texto=_money(resumen["qr"])),
                ResumenCierreRow(etiqueta="Fiado (no entra a caja)", monto_texto=_money(resumen["fiado"])),
                ResumenCierreRow(etiqueta="Propinas del turno", monto_texto=_money(resumen["propinas"])),
                ResumenCierreRow(etiqueta="Otros ingresos", monto_texto=_money(resumen["ingresos"])),
                ResumenCierreRow(etiqueta="Egresos / gastos", monto_texto="- " + _money(resumen["egresos"])),
            ]
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
        self.turno_cierre_error = ""
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
                    self.usuario_actual.id if self.usuario_actual else None,
                    contado,
                    arqueo_detalle=json.dumps(conteo_limpio) if conteo_limpio else None,
                    notas=self.turno_cierre_notas,
                )
                session.commit()
                session.refresh(turno)
                usuarios = {
                    u.id: u.nombre
                    for u in session.exec(
                        select(UsuarioFood).where(
                            UsuarioFood.company_id == self._company_id()
                        )
                    ).all()
                }
                descuadre = _dec(turno.descuadre)
                if descuadre > 0:
                    descuadre_texto = f"+{CURRENCY_SYMBOL} {descuadre:.2f} (sobra)"
                elif descuadre < 0:
                    descuadre_texto = f"-{CURRENCY_SYMBOL} {abs(descuadre):.2f} (falta)"
                else:
                    descuadre_texto = f"{CURRENCY_SYMBOL} 0.00 (cuadra)"
                ticket_html = generate_cash_close_ticket_html(
                    company_name=self.config_nombre_local or "TUWAYKIFOOD",
                    turno_id=turno.id or 0,
                    abierto_por=usuarios.get(turno.abierto_por_id or 0, "—"),
                    cerrado_por=usuarios.get(turno.cerrado_por_id or 0, "—"),
                    abierto_en_texto=_hora_local(turno.abierto_en),
                    cerrado_en_texto=_hora_local(turno.cerrado_en),
                    resumen_rows=[
                        ("Fondo inicial", _money(turno.monto_inicial)),
                        ("Ventas efectivo", _money(turno.total_efectivo)),
                        ("Ventas tarjeta", _money(turno.total_tarjeta)),
                        ("Ventas QR/Yape", _money(turno.total_qr)),
                        ("Fiado", _money(turno.total_fiado)),
                        ("Propinas", _money(turno.total_propinas)),
                        ("Otros ingresos", _money(turno.total_ingresos)),
                        ("Egresos", "- " + _money(turno.total_egresos)),
                        ("Esperado en caja", _money(turno.esperado_efectivo)),
                        ("Contado en caja", _money(turno.contado_efectivo)),
                    ],
                    descuadre_texto=descuadre_texto,
                    notas=turno.notas_cierre or "",
                    paper_width_mm=self._ticket_paper_width_mm(),
                )
        except ValueError as exc:
            self.turno_cierre_error = str(exc)
            return
        self.turno_cierre_visible = False
        self.turno_cierre_conteo = {}
        self.cargar_turno_caja()
        self.mensaje = "Turno de caja cerrado. Arqueo registrado."
        return rx.call_script(build_print_script(ticket_html))

    # ── Historial ────────────────────────────────────────────────────────────

    def toggle_historial_turnos(self) -> None:
        self.turno_historial_visible = not self.turno_historial_visible
