"""Promociones y cupones — gestión admin, aplicación automática al cobro y cupones por código.

Extrae el dominio Promos + Cupones de FoodState en un mixin reutilizable.
FoodState provee en runtime: `_tenant_session()`, `_company_id()`, `mensaje`,
`usuario_actual`, `categorias`, `productos`, `caja_cobro_total_base`,
`caja_cobro_descuento`, `mostrador_carrito`, `cargar_menu()`.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

import reflex as rx
from sqlmodel import select

from app.models.food import (
    Categoria,
    CuponLote,
    Producto,
    Promocion,
    TipoPromocion,
)
from app.services.promo_service import (
    DIAS_SEMANA as PROMO_DIAS,
    ahora_local_pe,
    promo_vigente,
)
from app.services.cupon_service import validar_cupon
from app.states.food_state import (
    CuponLoteView,
    PromocionView,
    _money_text,
    _to_decimal,
    _utcnow,
)


# ─── Mixin de estado ────────────────────────────────────────────────────────

class PromosCuponesMixin(rx.State, mixin=True):
    """Promociones (CRUD + auto-aplicar) y cupones (validar/redimir + CRUD admin)."""

    # ── Promociones ─────────────────────────────────────────────────────────
    promociones_lista: list[PromocionView] = []
    promo_form_id: int = 0
    promo_form_nombre: str = ""
    promo_form_tipo: str = TipoPromocion.PORCENTAJE.value
    promo_form_valor: str = ""
    promo_form_descripcion: str = ""
    promo_form_hora_inicio: str = ""
    promo_form_hora_fin: str = ""
    promo_form_dias_mask: int = 127
    promo_form_alcance: str = "todo"  # todo | categoria | producto
    promo_form_categoria_nombre: str = ""
    promo_form_producto_nombre: str = ""
    promo_form_auto: bool = True
    promo_form_editando: bool = False
    promo_form_visible: bool = False

    # Promo aplicada automáticamente al cobro actual
    caja_promo_aplicada_nombre: str = ""
    caja_promo_aplicada_texto: str = ""

    # ── Cupones — Caja (mesas) ──────────────────────────────────────────────
    caja_cupon_codigo: str = ""
    caja_cupon_id_aplicado: int = 0      # 0 = ninguno
    caja_cupon_nombre_aplicado: str = ""
    caja_cupon_descuento_aplicado: str = ""   # valor decimal como string "10.00"
    caja_cupon_error: str = ""

    # ── Cupones — Mostrador ─────────────────────────────────────────────────
    mostrador_cupon_codigo: str = ""
    mostrador_cupon_id_aplicado: int = 0
    mostrador_cupon_nombre_aplicado: str = ""
    mostrador_cupon_descuento_aplicado: str = ""
    mostrador_cupon_error: str = ""

    # ── Cupones — gestión admin ─────────────────────────────────────────────
    cupones_lista: list[CuponLoteView] = []
    cupon_form_visible: bool = False
    cupon_form_editando: bool = False
    cupon_form_id: int = 0
    cupon_form_nombre: str = ""
    cupon_form_codigo: str = ""
    cupon_form_tipo: str = "porcentaje"
    cupon_form_valor: str = ""
    cupon_form_fecha_inicio: str = ""
    cupon_form_fecha_fin: str = ""
    cupon_form_usos_max: str = ""

    # ── Computed vars ───────────────────────────────────────────────────────

    @rx.var
    def hay_promo_activa(self) -> bool:
        return any(p.aplica_ahora and p.activa for p in self.promociones_lista)

    @rx.var
    def promo_activa_nombre(self) -> str:
        for p in self.promociones_lista:
            if p.aplica_ahora and p.activa:
                return p.nombre
        return ""

    @rx.var
    def promo_activa_descuento_texto(self) -> str:
        for p in self.promociones_lista:
            if p.aplica_ahora and p.activa:
                return p.descuento_texto
        return ""

    @rx.var
    def promo_activa_descuento_sugerido(self) -> float:
        for p in self.promociones_lista:
            if p.aplica_ahora and p.activa:
                if p.tipo == TipoPromocion.PORCENTAJE.value or p.tipo == TipoPromocion.HAPPY_HOUR.value:
                    return round(self.caja_cobro_total_base * p.valor / 100, 2)
                elif p.tipo == TipoPromocion.MONTO_FIJO.value:
                    return p.valor
        return 0.0

    @rx.var
    def tipos_promo_disponibles(self) -> list[str]:
        return [t.value for t in TipoPromocion]

    @rx.var
    def promo_form_dias_ui(self) -> list[dict]:
        return [
            {
                "abrev": abrev.capitalize(),
                "bit": bit,
                "activo": bool(self.promo_form_dias_mask & bit),
            }
            for abrev, _nombre, bit in PROMO_DIAS
        ]

    @rx.var
    def promo_categorias_nombres(self) -> list[str]:
        return [c.nombre for c in self.categorias]

    @rx.var
    def promo_productos_nombres(self) -> list[str]:
        return [p.nombre for p in self.productos]

    # ── Promociones — carga y on_load ───────────────────────────────────────

    def on_load_promociones(self):
        result = self._route_access_result("promociones")
        if result is not None:
            return result
        self.cargar_menu()
        self.cargar_promociones()
        self.cargar_cupones()

    def cargar_promociones(self) -> None:
        # Vigencia evaluada en hora local del país (no UTC): un happy hour de
        # 18:00 configurado por el usuario es 18:00 en Perú.
        ahora = ahora_local_pe()
        tipo_labels = {
            TipoPromocion.PORCENTAJE.value: "% Descuento",
            TipoPromocion.MONTO_FIJO.value: "Monto fijo",
            TipoPromocion.HAPPY_HOUR.value: "Happy Hour",
            TipoPromocion.DOSXUNO.value: "2x1",
        }
        with self._tenant_session() as session:
            promos_db = session.exec(
                select(Promocion)
                .where(Promocion.company_id == self._company_id())
                .order_by(Promocion.activa.desc(), Promocion.nombre)
            ).all()
            productos = {p.id: p.nombre for p in session.exec(
                select(Producto).where(Producto.company_id == self._company_id())
            ).all()}
            categorias = {c.id: c.nombre for c in session.exec(
                select(Categoria).where(Categoria.company_id == self._company_id())
            ).all()}
        views: list[PromocionView] = []
        for p in promos_db:
            val = Decimal(str(p.valor))
            if p.tipo in (TipoPromocion.PORCENTAJE.value, TipoPromocion.HAPPY_HOUR.value):
                desc_txt = f"{val:.0f}% off"
            elif p.tipo == TipoPromocion.DOSXUNO.value:
                desc_txt = "2x1"
            else:
                desc_txt = f"- {_money_text(val)}"
            if p.hora_inicio and p.hora_fin:
                horario = f"{p.hora_inicio} – {p.hora_fin}"
            else:
                horario = "Todo el día"
            mask = p.dias_semana_mask or 127
            if mask >= 127:
                dias_texto = "Todos los días"
            else:
                dias_texto = ", ".join(
                    abrev.capitalize() for abrev, _nombre, bit in PROMO_DIAS if mask & bit
                ) or "Todos los días"
            if p.producto_id:
                alcance = productos.get(p.producto_id, f"Producto #{p.producto_id}")
            elif p.categoria_id:
                alcance = "Cat. " + categorias.get(p.categoria_id, f"#{p.categoria_id}")
            else:
                alcance = "Toda la carta"
            views.append(PromocionView(
                id=p.id or 0,
                nombre=p.nombre,
                tipo=p.tipo,
                tipo_label=tipo_labels.get(p.tipo, p.tipo),
                valor=float(val),
                descripcion=p.descripcion or "",
                hora_inicio=p.hora_inicio or "",
                hora_fin=p.hora_fin or "",
                activa=p.activa,
                aplica_ahora=promo_vigente(p, ahora),
                descuento_texto=desc_txt,
                horario_texto=horario,
                dias_texto=dias_texto,
                alcance_texto=alcance,
                auto_aplicar=p.auto_aplicar,
            ))
        self.promociones_lista = views

    # ── Promociones — form setters ──────────────────────────────────────────

    def set_promo_form_nombre(self, v: str) -> None:
        self.promo_form_nombre = v

    def set_promo_form_tipo(self, v: str) -> None:
        self.promo_form_tipo = v

    def set_promo_form_valor(self, v: str) -> None:
        self.promo_form_valor = v

    def set_promo_form_descripcion(self, v: str) -> None:
        self.promo_form_descripcion = v

    def set_promo_form_hora_inicio(self, v: str) -> None:
        self.promo_form_hora_inicio = v

    def set_promo_form_hora_fin(self, v: str) -> None:
        self.promo_form_hora_fin = v

    def set_promo_form_alcance(self, v: str) -> None:
        self.promo_form_alcance = v

    def set_promo_form_categoria_nombre(self, v: str) -> None:
        self.promo_form_categoria_nombre = v

    def set_promo_form_producto_nombre(self, v: str) -> None:
        self.promo_form_producto_nombre = v

    def set_promo_form_auto(self, v: bool) -> None:
        self.promo_form_auto = bool(v)

    def toggle_promo_dia(self, bit: int) -> None:
        self.promo_form_dias_mask ^= bit

    def _reset_promo_form(self) -> None:
        self.promo_form_id = 0
        self.promo_form_nombre = ""
        self.promo_form_tipo = TipoPromocion.PORCENTAJE.value
        self.promo_form_valor = ""
        self.promo_form_descripcion = ""
        self.promo_form_hora_inicio = ""
        self.promo_form_hora_fin = ""
        self.promo_form_dias_mask = 127
        self.promo_form_alcance = "todo"
        self.promo_form_categoria_nombre = ""
        self.promo_form_producto_nombre = ""
        self.promo_form_auto = True
        self.promo_form_editando = False

    # ── Promociones — CRUD ──────────────────────────────────────────────────

    def guardar_promocion(self) -> None:
        nombre = self.promo_form_nombre.strip()
        if not nombre:
            return rx.toast.error("El nombre de la promoción es obligatorio.")
        es_dosxuno = self.promo_form_tipo == TipoPromocion.DOSXUNO.value
        if es_dosxuno:
            valor = Decimal("0.00")  # el 2x1 no usa valor: regala 1 de cada 2
        else:
            try:
                valor = Decimal(self.promo_form_valor.replace(",", ".").strip() or "0")
                if valor <= 0:
                    raise ValueError
            except (InvalidOperation, ValueError):
                return rx.toast.error("Valor inválido. Ingresa un número mayor a 0.")
        if self.promo_form_dias_mask == 0:
            return rx.toast.error("Selecciona al menos un día de la semana.")
        producto_id = None
        categoria_id = None
        if self.promo_form_alcance == "producto":
            prod = next(
                (p for p in self.productos if p.nombre == self.promo_form_producto_nombre),
                None,
            )
            if prod is None:
                return rx.toast.error("Selecciona el producto para la promoción.")
            producto_id = prod.id
        elif self.promo_form_alcance == "categoria":
            cat = next(
                (c for c in self.categorias if c.nombre == self.promo_form_categoria_nombre),
                None,
            )
            if cat is None:
                return rx.toast.error("Selecciona la categoría para la promoción.")
            categoria_id = cat.id
        if es_dosxuno and producto_id is None and categoria_id is None:
            return rx.toast.error("El 2x1 necesita un producto o una categoría como alcance.")
        hora_ini = self.promo_form_hora_inicio.strip() or None
        hora_fin = self.promo_form_hora_fin.strip() or None
        with self._tenant_session() as session:
            if self.promo_form_id == 0:
                p = Promocion(
                    company_id=self._company_id(),
                    nombre=nombre,
                    tipo=self.promo_form_tipo,
                    valor=valor,
                    descripcion=self.promo_form_descripcion.strip() or None,
                    hora_inicio=hora_ini,
                    hora_fin=hora_fin,
                    dias_semana_mask=self.promo_form_dias_mask,
                    producto_id=producto_id,
                    categoria_id=categoria_id,
                    auto_aplicar=self.promo_form_auto,
                    activa=True,
                )
                session.add(p)
                _msg = f"Promoción '{nombre}' creada."
            else:
                p = session.get(Promocion, self.promo_form_id)
                if p is None or p.company_id != self._company_id():
                    return rx.toast.error("Promoción no encontrada.")
                p.nombre = nombre
                p.tipo = self.promo_form_tipo
                p.valor = valor
                p.descripcion = self.promo_form_descripcion.strip() or None
                p.hora_inicio = hora_ini
                p.hora_fin = hora_fin
                p.dias_semana_mask = self.promo_form_dias_mask
                p.producto_id = producto_id
                p.categoria_id = categoria_id
                p.auto_aplicar = self.promo_form_auto
                p.updated_at = _utcnow()
                session.add(p)
                _msg = f"Promoción '{nombre}' actualizada."
            session.commit()
        self._reset_promo_form()
        self.promo_form_visible = False
        self.cargar_promociones()
        return rx.toast.success(_msg)

    def abrir_nueva_promo(self) -> None:
        self._reset_promo_form()
        self.promo_form_visible = True

    def set_promo_form_visible(self, v: bool) -> None:
        self.promo_form_visible = v

    def editar_promocion(self, promo_id: int) -> None:
        with self._tenant_session() as session:
            p = session.get(Promocion, promo_id)
            if p is None or p.company_id != self._company_id():
                return
            self.promo_form_id = p.id or 0
            self.promo_form_nombre = p.nombre
            self.promo_form_tipo = p.tipo
            self.promo_form_valor = str(Decimal(str(p.valor)).normalize())
            self.promo_form_descripcion = p.descripcion or ""
            self.promo_form_hora_inicio = p.hora_inicio or ""
            self.promo_form_hora_fin = p.hora_fin or ""
            self.promo_form_dias_mask = p.dias_semana_mask or 127
            self.promo_form_auto = p.auto_aplicar
            if p.producto_id:
                self.promo_form_alcance = "producto"
                prod = session.get(Producto, p.producto_id)
                self.promo_form_producto_nombre = prod.nombre if prod else ""
                self.promo_form_categoria_nombre = ""
            elif p.categoria_id:
                self.promo_form_alcance = "categoria"
                cat = session.get(Categoria, p.categoria_id)
                self.promo_form_categoria_nombre = cat.nombre if cat else ""
                self.promo_form_producto_nombre = ""
            else:
                self.promo_form_alcance = "todo"
                self.promo_form_producto_nombre = ""
                self.promo_form_categoria_nombre = ""
        self.promo_form_editando = True
        self.promo_form_visible = True

    def cancelar_promo_form(self) -> None:
        self._reset_promo_form()
        self.promo_form_visible = False

    def toggle_promo_activa(self, promo_id: int) -> None:
        with self._tenant_session() as session:
            p = session.get(Promocion, promo_id)
            if p is None or p.company_id != self._company_id():
                return
            p.activa = not p.activa
            p.updated_at = _utcnow()
            session.add(p)
            session.commit()
        self.cargar_promociones()

    def aplicar_promo_al_cobro(self) -> None:
        desc = self.promo_activa_descuento_sugerido
        if desc > 0:
            self.caja_cobro_descuento = str(round(desc, 2))

    def quitar_promo_aplicada(self) -> None:
        self.caja_cobro_descuento = ""
        self.caja_promo_aplicada_nombre = ""
        self.caja_promo_aplicada_texto = ""

    def refrescar_promos(self) -> None:
        self.cargar_promociones()

    # ─── Cupones — Caja (mesas) ─────────────────────────────────────────────

    def set_caja_cupon_codigo(self, v: str) -> None:
        self.caja_cupon_codigo = v.upper()
        self.caja_cupon_error = ""

    def aplicar_cupon_caja(self) -> None:
        """Valida el código de cupón y aplica el descuento al cobro de caja."""
        self.caja_cupon_error = ""
        try:
            total_base = Decimal(str(self.caja_cobro_total_base))
            with self._tenant_session() as session:
                cupon, descuento = validar_cupon(
                    session, self.caja_cupon_codigo, self._company_id(), total_base
                )
            self.caja_cupon_id_aplicado = cupon.id or 0
            self.caja_cupon_nombre_aplicado = cupon.nombre
            self.caja_cupon_descuento_aplicado = str(round(float(descuento), 2))
            self.caja_cobro_descuento = self.caja_cupon_descuento_aplicado
        except ValueError as exc:
            self.caja_cupon_error = str(exc)

    def quitar_cupon_caja(self) -> None:
        self.caja_cupon_codigo = ""
        self.caja_cupon_id_aplicado = 0
        self.caja_cupon_nombre_aplicado = ""
        self.caja_cupon_descuento_aplicado = ""
        self.caja_cupon_error = ""
        self.caja_cobro_descuento = ""

    # ─── Cupones — Mostrador ────────────────────────────────────────────────

    def set_mostrador_cupon_codigo(self, v: str) -> None:
        self.mostrador_cupon_codigo = v.upper()
        self.mostrador_cupon_error = ""

    def aplicar_cupon_mostrador(self) -> None:
        """Valida el código de cupón para el carrito de mostrador."""
        self.mostrador_cupon_error = ""
        try:
            total_base = sum(_to_decimal(item.subtotal) for item in self.mostrador_carrito)
            if total_base <= 0:
                self.mostrador_cupon_error = "Agrega productos antes de aplicar un cupón."
                return
            with self._tenant_session() as session:
                cupon, descuento = validar_cupon(
                    session, self.mostrador_cupon_codigo, self._company_id(), total_base
                )
            self.mostrador_cupon_id_aplicado = cupon.id or 0
            self.mostrador_cupon_nombre_aplicado = cupon.nombre
            self.mostrador_cupon_descuento_aplicado = str(round(float(descuento), 2))
        except ValueError as exc:
            self.mostrador_cupon_error = str(exc)

    def quitar_cupon_mostrador(self) -> None:
        self.mostrador_cupon_codigo = ""
        self.mostrador_cupon_id_aplicado = 0
        self.mostrador_cupon_nombre_aplicado = ""
        self.mostrador_cupon_descuento_aplicado = ""
        self.mostrador_cupon_error = ""

    # ─── Cupones — Gestión admin ────────────────────────────────────────────

    def on_load_cupones(self):
        result = self._route_access_result("cupones")
        if result is not None:
            return result
        self.cargar_cupones()

    def cargar_cupones(self) -> None:
        from datetime import date as _date
        hoy = _date.today()
        with self._tenant_session() as session:
            lotes = session.exec(
                select(CuponLote)
                .where(CuponLote.company_id == self._company_id())
                .order_by(CuponLote.activo.desc(), CuponLote.nombre)
            ).all()
        views: list[CuponLoteView] = []
        for c in lotes:
            tipo_label = "% Porcentaje" if c.tipo == "porcentaje" else "S/ Monto fijo"
            valor_txt = f"{Decimal(str(c.valor)):.0f}%" if c.tipo == "porcentaje" else _money_text(Decimal(str(c.valor)))
            fi = c.fecha_inicio.strftime("%d/%m/%Y") if c.fecha_inicio else "Sin inicio"
            ff = c.fecha_fin.strftime("%d/%m/%Y") if c.fecha_fin else "Sin vence"
            usos_max_txt = str(c.usos_max) if c.usos_max is not None else "Ilimitado"
            usos_txt = f"{c.usos_actuales} / {c.usos_max}" if c.usos_max is not None else f"{c.usos_actuales} usos"
            vencido = bool(c.fecha_fin and hoy > c.fecha_fin)
            views.append(CuponLoteView(
                id=c.id or 0,
                nombre=c.nombre,
                codigo=c.codigo,
                tipo=tipo_label,
                valor_texto=valor_txt,
                fecha_inicio_texto=fi,
                fecha_fin_texto=ff,
                usos_actuales=c.usos_actuales,
                usos_max_texto=usos_max_txt,
                usos_texto=usos_txt,
                activo=c.activo,
                vencido=vencido,
            ))
        self.cupones_lista = views

    # ── Cupones — form setters ──────────────────────────────────────────────

    def set_cupon_form_nombre(self, v: str) -> None:
        self.cupon_form_nombre = v

    def set_cupon_form_codigo(self, v: str) -> None:
        self.cupon_form_codigo = v.upper().strip()

    def set_cupon_form_tipo(self, v: str) -> None:
        self.cupon_form_tipo = v

    def set_cupon_form_valor(self, v: str) -> None:
        self.cupon_form_valor = v

    def set_cupon_form_fecha_inicio(self, v: str) -> None:
        self.cupon_form_fecha_inicio = v

    def set_cupon_form_fecha_fin(self, v: str) -> None:
        self.cupon_form_fecha_fin = v

    def set_cupon_form_usos_max(self, v: str) -> None:
        self.cupon_form_usos_max = v

    def set_cupon_form_visible(self, v: bool) -> None:
        self.cupon_form_visible = bool(v)
        if not v:
            self._reset_cupon_form()

    def abrir_nuevo_cupon(self) -> None:
        self._reset_cupon_form()
        self.cupon_form_visible = True

    def _reset_cupon_form(self) -> None:
        self.cupon_form_id = 0
        self.cupon_form_nombre = ""
        self.cupon_form_codigo = ""
        self.cupon_form_tipo = "porcentaje"
        self.cupon_form_valor = ""
        self.cupon_form_fecha_inicio = ""
        self.cupon_form_fecha_fin = ""
        self.cupon_form_usos_max = ""
        self.cupon_form_editando = False

    # ── Cupones — CRUD ──────────────────────────────────────────────────────

    def editar_cupon(self, cupon_id: int) -> None:
        with self._tenant_session() as session:
            c = session.get(CuponLote, cupon_id)
            if c is None or c.company_id != self._company_id():
                return
        self.cupon_form_id = c.id or 0
        self.cupon_form_nombre = c.nombre
        self.cupon_form_codigo = c.codigo
        self.cupon_form_tipo = c.tipo
        self.cupon_form_valor = str(Decimal(str(c.valor)))
        self.cupon_form_fecha_inicio = c.fecha_inicio.strftime("%Y-%m-%d") if c.fecha_inicio else ""
        self.cupon_form_fecha_fin = c.fecha_fin.strftime("%Y-%m-%d") if c.fecha_fin else ""
        self.cupon_form_usos_max = str(c.usos_max) if c.usos_max is not None else ""
        self.cupon_form_editando = True
        self.cupon_form_visible = True

    def guardar_cupon(self) -> None:
        from datetime import date as _date
        nombre = self.cupon_form_nombre.strip()
        codigo = self.cupon_form_codigo.strip().upper()
        if not nombre:
            return rx.toast.error("El nombre es obligatorio.")
        if not codigo:
            return rx.toast.error("El código es obligatorio.")
        try:
            valor = Decimal(str(self.cupon_form_valor.replace(",", ".")))
            if valor <= 0:
                raise ValueError
        except (ValueError, InvalidOperation):
            return rx.toast.error("Valor inválido. Ingresa un número mayor a cero.")
        if self.cupon_form_tipo == "porcentaje" and valor > 100:
            return rx.toast.error("El porcentaje no puede superar 100%.")
        usos_max: int | None = None
        if self.cupon_form_usos_max.strip():
            try:
                usos_max = int(self.cupon_form_usos_max.strip())
                if usos_max <= 0:
                    raise ValueError
            except ValueError:
                return rx.toast.error("Usos máximos debe ser un número entero positivo.")
        fecha_inicio: _date | None = None
        fecha_fin: _date | None = None
        try:
            if self.cupon_form_fecha_inicio:
                fecha_inicio = _date.fromisoformat(self.cupon_form_fecha_inicio)
            if self.cupon_form_fecha_fin:
                fecha_fin = _date.fromisoformat(self.cupon_form_fecha_fin)
        except ValueError:
            return rx.toast.error("Fechas inválidas.")
        with self._tenant_session() as session:
            if self.cupon_form_editando and self.cupon_form_id:
                c = session.get(CuponLote, self.cupon_form_id)
                if c is None or c.company_id != self._company_id():
                    return rx.toast.error("Cupón no encontrado.")
                c.nombre = nombre
                c.codigo = codigo
                c.tipo = self.cupon_form_tipo
                c.valor = valor
                c.fecha_inicio = fecha_inicio
                c.fecha_fin = fecha_fin
                c.usos_max = usos_max
                c.updated_at = _utcnow()
                session.add(c)
            else:
                c = CuponLote(
                    company_id=self._company_id(),
                    nombre=nombre,
                    codigo=codigo,
                    tipo=self.cupon_form_tipo,
                    valor=valor,
                    fecha_inicio=fecha_inicio,
                    fecha_fin=fecha_fin,
                    usos_max=usos_max,
                    usos_actuales=0,
                    activo=True,
                )
                session.add(c)
            try:
                session.commit()
            except Exception:
                session.rollback()
                return rx.toast.error(f"El código '{codigo}' ya existe.")
        self.cupon_form_visible = False
        self._reset_cupon_form()
        self.cargar_cupones()
        return rx.toast.success(f"Cupón '{nombre}' guardado.")

    def toggle_cupon_activo(self, cupon_id: int) -> None:
        with self._tenant_session() as session:
            c = session.get(CuponLote, cupon_id)
            if c is None or c.company_id != self._company_id():
                return
            c.activo = not c.activo
            c.updated_at = _utcnow()
            session.add(c)
            session.commit()
        self.cargar_cupones()

    def cancelar_cupon_form(self) -> None:
        self._reset_cupon_form()
        self.cupon_form_visible = False
