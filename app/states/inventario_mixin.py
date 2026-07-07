"""Inventario de insumos, kardex y recetas — mixin para FoodState.

Extrae la gestión completa de inventario: CRUD de insumos, movimientos manuales
(entrada, merma, ajuste), historial kardex y armado de recetas por producto.

FoodState provee en runtime: ``_tenant_session()``, ``_company_id()``,
``usuario_actual``, ``mensaje``, ``productos`` y ``cargar_menu()``.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation

import reflex as rx
from sqlmodel import select

from app.models.food import (
    Insumo,
    MovimientoInsumo,
    RecetaItem,
    TipoMovimientoInsumo,
    UsuarioFood,
)
from app.services.kardex_service import (
    CATEGORIAS_MERMA,
    registrar_ajuste,
    registrar_entrada,
    registrar_merma,
)
from app.services.promo_service import ahora_local_pe
from tuwayki_core.utils.timezone import format_local_datetime

# Importar ViewModels y helpers desde food_state (se mantienen allí)
from app.states.food_state import InsumoView, KardexView, RecetaItemView, _utcnow


class InventarioMixin(rx.State, mixin=True):
    """Inventario de insumos, kardex de movimientos y recetas de producto."""

    # ─── State vars ───────────────────────────────────────────────────────────

    # Inventario de insumos / recetas
    inv_insumos: list[InsumoView] = []
    inv_alertas_bajo_stock: list[str] = []
    inv_form_id: int = 0
    inv_form_nombre: str = ""
    inv_form_unidad: str = "unidad"
    inv_form_stock_actual: str = ""
    inv_form_stock_minimo: str = ""
    inv_form_vencimiento: str = ""
    inv_form_costo: str = ""
    inv_form_editando: bool = False
    inv_form_visible: bool = False

    # Kardex — movimiento manual (entrada / merma / ajuste) + historial
    inv_mov_modal_visible: bool = False
    inv_mov_insumo_id: int = 0
    inv_mov_insumo_nombre: str = ""
    inv_mov_tipo: str = "entrada"
    inv_mov_cantidad: str = ""
    inv_mov_merma_categoria: str = "Vencido"
    inv_mov_motivo: str = ""
    inv_mov_error: str = ""
    inv_kardex_visible: bool = False
    inv_kardex_insumo_nombre: str = ""
    inv_kardex_movimientos: list[KardexView] = []
    inv_alertas_vencimiento: list[str] = []
    inv_search: str = ""
    inv_producto_sel_nombre: str = ""
    inv_producto_sel_id: int = 0
    inv_receta_items: list[RecetaItemView] = []
    inv_receta_insumo_sel_nombre: str = ""
    inv_receta_cantidad: str = ""

    # ─── Computed vars ────────────────────────────────────────────────────────

    @rx.var
    def inv_insumos_filtrados(self) -> list[InsumoView]:
        q = self.inv_search.strip().lower()
        if not q:
            return self.inv_insumos
        return [i for i in self.inv_insumos if q in i.nombre.lower()]

    @rx.var
    def inv_categorias_merma(self) -> list[str]:
        return CATEGORIAS_MERMA

    @rx.var
    def inv_alertas_vencimiento_texto(self) -> str:
        return " · ".join(self.inv_alertas_vencimiento)

    @rx.var
    def inv_insumos_activos_nombres(self) -> list[str]:
        return [i.nombre for i in self.inv_insumos if i.activo]

    @rx.var
    def inv_productos_nombres(self) -> list[str]:
        return [p.nombre for p in self.productos]

    @rx.var
    def inv_alertas_bajo_stock_texto(self) -> str:
        return ", ".join(self.inv_alertas_bajo_stock)

    # ─── Inventario ───────────────────────────────────────────────────────────

    def on_load_inventario(self) -> None:
        self.cargar_inventario()
        if not self.productos:
            self.cargar_menu()

    def cargar_inventario(self) -> None:
        with self._tenant_session() as session:
            insumos_db = session.exec(
                select(Insumo)
                .where(Insumo.company_id == self._company_id())
                .order_by(Insumo.nombre)
            ).all()
            views: list[InsumoView] = []
            alertas: list[str] = []
            alertas_venc: list[str] = []
            hoy = ahora_local_pe().date()
            for ins in insumos_db:
                stock = Decimal(str(ins.stock_actual))
                minimo = Decimal(str(ins.stock_minimo))
                bajo = ins.activo and minimo > 0 and stock <= minimo
                venc_texto = ""
                venc_estado = ""
                if ins.fecha_vencimiento:
                    venc_texto = ins.fecha_vencimiento.strftime("%d/%m/%Y")
                    dias = (ins.fecha_vencimiento - hoy).days
                    if ins.activo and dias < 0:
                        venc_estado = "vencido"
                        alertas_venc.append(f"{ins.nombre} (vencido)")
                    elif ins.activo and dias <= 7:
                        venc_estado = "por_vencer"
                        alertas_venc.append(f"{ins.nombre} (vence en {dias} día{'s' if dias != 1 else ''})")
                views.append(InsumoView(
                    id=ins.id or 0,
                    nombre=ins.nombre,
                    unidad=ins.unidad,
                    stock_actual=float(stock),
                    stock_minimo=float(minimo),
                    activo=ins.activo,
                    bajo_stock=bajo,
                    stock_texto=f"{stock:.3f} {ins.unidad}".rstrip("0").rstrip(".").strip(),
                    stock_minimo_texto=f"{minimo:.3f} {ins.unidad}".rstrip("0").rstrip(".").strip(),
                    vencimiento_texto=venc_texto,
                    vencimiento_estado=venc_estado,
                ))
                if bajo:
                    alertas.append(ins.nombre)
            self.inv_insumos = views
            self.inv_alertas_bajo_stock = alertas
            self.inv_alertas_vencimiento = alertas_venc

    def set_inv_search(self, v: str) -> None:
        self.inv_search = v

    def set_inv_form_visible(self, v: bool) -> None:
        self.inv_form_visible = v

    def abrir_nuevo_insumo(self) -> None:
        self.inv_form_id = 0
        self.inv_form_nombre = ""
        self.inv_form_unidad = "unidad"
        self.inv_form_stock_actual = ""
        self.inv_form_stock_minimo = ""
        self.inv_form_vencimiento = ""
        self.inv_form_costo = ""
        self.inv_form_editando = False
        self.inv_form_visible = True

    def set_inv_form_nombre(self, v: str) -> None:
        self.inv_form_nombre = v

    def set_inv_form_unidad(self, v: str) -> None:
        self.inv_form_unidad = v

    def set_inv_form_stock_actual(self, v: str) -> None:
        self.inv_form_stock_actual = v

    def set_inv_form_stock_minimo(self, v: str) -> None:
        self.inv_form_stock_minimo = v

    def set_inv_form_vencimiento(self, v: str) -> None:
        self.inv_form_vencimiento = v

    def set_inv_form_costo(self, v: str) -> None:
        self.inv_form_costo = v

    def guardar_insumo(self) -> None:
        nombre = self.inv_form_nombre.strip()
        if not nombre:
            self.mensaje = "El nombre del insumo es obligatorio."
            return
        unidad = self.inv_form_unidad.strip() or "unidad"
        try:
            stock_actual = Decimal(self.inv_form_stock_actual.replace(",", ".").strip() or "0")
            stock_minimo = Decimal(self.inv_form_stock_minimo.replace(",", ".").strip() or "0")
            if stock_actual < 0 or stock_minimo < 0:
                raise ValueError
        except (InvalidOperation, ValueError):
            self.mensaje = "Stock inválido. Ingrese números positivos."
            return
        fecha_venc = None
        if self.inv_form_vencimiento.strip():
            try:
                fecha_venc = datetime.strptime(self.inv_form_vencimiento.strip(), "%Y-%m-%d").date()
            except ValueError:
                self.mensaje = "Fecha de vencimiento inválida."
                return
        try:
            costo = Decimal(self.inv_form_costo.replace(",", ".").strip() or "0")
            if costo < 0:
                raise ValueError
        except (InvalidOperation, ValueError):
            self.mensaje = "Costo inválido. Ingrese un número positivo."
            return
        with self._tenant_session() as session:
            if self.inv_form_id == 0:
                existente = session.exec(
                    select(Insumo).where(
                        Insumo.company_id == self._company_id(),
                        Insumo.nombre == nombre,
                    )
                ).first()
                if existente:
                    self.mensaje = f"Ya existe un insumo llamado '{nombre}'."
                    return
                ins = Insumo(
                    company_id=self._company_id(),
                    nombre=nombre,
                    unidad=unidad,
                    stock_actual=stock_actual,
                    stock_minimo=stock_minimo,
                    fecha_vencimiento=fecha_venc,
                    costo_unitario=costo,
                    activo=True,
                )
                session.add(ins)
                session.flush()
                if stock_actual > 0:
                    registrar_entrada(
                        session, ins,
                        (self.usuario_actual.id or None) if self.usuario_actual else None,
                        stock_actual, "Stock inicial",
                    )
                self.mensaje = f"Insumo '{nombre}' creado."
            else:
                ins = session.get(Insumo, self.inv_form_id)
                if ins is None or ins.company_id != self._company_id():
                    self.mensaje = "Insumo no encontrado."
                    return
                ins.nombre = nombre
                ins.unidad = unidad
                ins.stock_minimo = stock_minimo
                ins.fecha_vencimiento = fecha_venc
                ins.costo_unitario = costo
                ins.updated_at = _utcnow()
                session.add(ins)
                # El stock no se pisa directo: la diferencia queda en el kardex
                if stock_actual != Decimal(str(ins.stock_actual)):
                    registrar_ajuste(
                        session, ins,
                        (self.usuario_actual.id or None) if self.usuario_actual else None,
                        stock_actual, "Edición manual del insumo",
                    )
                self.mensaje = f"Insumo '{nombre}' actualizado."
            session.commit()
        self.inv_form_id = 0
        self.inv_form_nombre = ""
        self.inv_form_unidad = "unidad"
        self.inv_form_stock_actual = ""
        self.inv_form_stock_minimo = ""
        self.inv_form_vencimiento = ""
        self.inv_form_costo = ""
        self.inv_form_editando = False
        self.inv_form_visible = False
        self.cargar_inventario()

    def editar_insumo(self, insumo_id: int) -> None:
        with self._tenant_session() as session:
            ins = session.get(Insumo, insumo_id)
            if ins is None or ins.company_id != self._company_id():
                return
            self.inv_form_id = ins.id or 0
            self.inv_form_nombre = ins.nombre
            self.inv_form_unidad = ins.unidad
            stock = Decimal(str(ins.stock_actual))
            minimo = Decimal(str(ins.stock_minimo))
            self.inv_form_stock_actual = f"{stock:.3f}".rstrip("0").rstrip(".")
            self.inv_form_stock_minimo = f"{minimo:.3f}".rstrip("0").rstrip(".")
            self.inv_form_vencimiento = (
                ins.fecha_vencimiento.strftime("%Y-%m-%d") if ins.fecha_vencimiento else ""
            )
            costo_dec = Decimal(str(ins.costo_unitario))
            self.inv_form_costo = f"{costo_dec:.2f}" if costo_dec > 0 else ""
        self.inv_form_editando = True
        self.inv_form_visible = True

    def cancelar_insumo_form(self) -> None:
        self.inv_form_id = 0
        self.inv_form_nombre = ""
        self.inv_form_unidad = "unidad"
        self.inv_form_stock_actual = ""
        self.inv_form_stock_minimo = ""
        self.inv_form_vencimiento = ""
        self.inv_form_costo = ""
        self.inv_form_editando = False
        self.inv_form_visible = False

    def toggle_insumo_activo(self, insumo_id: int) -> None:
        with self._tenant_session() as session:
            ins = session.get(Insumo, insumo_id)
            if ins is None or ins.company_id != self._company_id():
                return
            ins.activo = not ins.activo
            ins.updated_at = _utcnow()
            session.add(ins)
            session.commit()
        self.cargar_inventario()

    # ─── Kardex de insumos ────────────────────────────────────────────────────

    def set_inv_mov_modal_visible(self, v: bool) -> None:
        self.inv_mov_modal_visible = bool(v)

    def set_inv_mov_tipo(self, v: str) -> None:
        self.inv_mov_tipo = v
        self.inv_mov_error = ""

    def set_inv_mov_cantidad(self, v: str) -> None:
        self.inv_mov_cantidad = v

    def set_inv_mov_merma_categoria(self, v: str) -> None:
        self.inv_mov_merma_categoria = v

    def set_inv_mov_motivo(self, v: str) -> None:
        self.inv_mov_motivo = v

    def abrir_mov_insumo(self, insumo_id: int, tipo: str) -> None:
        insumo = next((i for i in self.inv_insumos if i.id == insumo_id), None)
        if insumo is None:
            return
        self.inv_mov_insumo_id = insumo_id
        self.inv_mov_insumo_nombre = insumo.nombre
        self.inv_mov_tipo = tipo
        self.inv_mov_cantidad = ""
        self.inv_mov_merma_categoria = "Vencido"
        self.inv_mov_motivo = ""
        self.inv_mov_error = ""
        self.inv_mov_modal_visible = True

    def guardar_mov_insumo(self) -> None:
        self.inv_mov_error = ""
        raw = (self.inv_mov_cantidad or "").replace(",", ".").strip()
        try:
            cantidad = Decimal(raw) if raw else Decimal("0")
        except InvalidOperation:
            self.inv_mov_error = "Cantidad inválida."
            return
        usuario_id = (self.usuario_actual.id or None) if self.usuario_actual else None
        try:
            with self._tenant_session() as session:
                ins = session.get(Insumo, self.inv_mov_insumo_id)
                if ins is None or ins.company_id != self._company_id():
                    self.inv_mov_error = "Insumo no encontrado."
                    return
                if self.inv_mov_tipo == "entrada":
                    registrar_entrada(
                        session, ins, usuario_id, cantidad,
                        self.inv_mov_motivo or "Compra de mercadería",
                    )
                elif self.inv_mov_tipo == "merma":
                    motivo = self.inv_mov_merma_categoria
                    if self.inv_mov_motivo.strip():
                        motivo = f"{motivo}: {self.inv_mov_motivo.strip()}"
                    registrar_merma(session, ins, usuario_id, cantidad, motivo)
                elif self.inv_mov_tipo == "ajuste":
                    registrar_ajuste(
                        session, ins, usuario_id, cantidad,
                        self.inv_mov_motivo or "Conteo físico",
                    )
                else:
                    self.inv_mov_error = "Tipo de movimiento inválido."
                    return
                session.commit()
        except ValueError as exc:
            self.inv_mov_error = str(exc)
            return
        self.inv_mov_modal_visible = False
        self.cargar_inventario()
        self.mensaje = f"Movimiento registrado para '{self.inv_mov_insumo_nombre}'."

    def set_inv_kardex_visible(self, v: bool) -> None:
        self.inv_kardex_visible = bool(v)

    def abrir_kardex_insumo(self, insumo_id: int) -> None:
        tipo_labels = {
            TipoMovimientoInsumo.ENTRADA.value: "Entrada",
            TipoMovimientoInsumo.CONSUMO.value: "Consumo por venta",
            TipoMovimientoInsumo.MERMA.value: "Merma",
            TipoMovimientoInsumo.AJUSTE.value: "Ajuste de conteo",
            TipoMovimientoInsumo.REPOSICION.value: "Reposición por anulación",
        }
        vistas: list[KardexView] = []
        with self._tenant_session() as session:
            ins = session.get(Insumo, insumo_id)
            if ins is None or ins.company_id != self._company_id():
                return
            movimientos = session.exec(
                select(MovimientoInsumo)
                .where(
                    MovimientoInsumo.company_id == self._company_id(),
                    MovimientoInsumo.insumo_id == insumo_id,
                )
                .order_by(MovimientoInsumo.id.desc())
                .limit(50)
            ).all()
            usuarios = {
                u.id: u.nombre
                for u in session.exec(
                    select(UsuarioFood).where(UsuarioFood.company_id == self._company_id())
                ).all()
            }
            unidad = ins.unidad
            for m in movimientos:
                cantidad = Decimal(str(m.cantidad))
                signo = "+" if cantidad >= 0 else ""
                vistas.append(KardexView(
                    id=m.id or 0,
                    fecha_texto=format_local_datetime(m.created_at, "%d/%m %H:%M", "PE"),
                    tipo=m.tipo,
                    tipo_label=tipo_labels.get(m.tipo, m.tipo),
                    cantidad_texto=f"{signo}{cantidad:.3f}".rstrip("0").rstrip(".") + f" {unidad}",
                    es_entrada=cantidad >= 0,
                    stock_resultante_texto=f"{Decimal(str(m.stock_resultante)):.3f}".rstrip("0").rstrip(".") + f" {unidad}",
                    motivo=m.motivo or "",
                    usuario=usuarios.get(m.usuario_id or 0, "Sistema"),
                ))
            self.inv_kardex_insumo_nombre = ins.nombre
        self.inv_kardex_movimientos = vistas
        self.inv_kardex_visible = True

    # ─── Recetas de producto ──────────────────────────────────────────────────

    def set_inv_producto_sel_nombre(self, v: str) -> None:
        self.inv_producto_sel_nombre = v
        prod = next((p for p in self.productos if p.nombre == v), None)
        self.inv_producto_sel_id = prod.id if prod else 0
        self.cargar_receta_producto()

    def cargar_receta_producto(self) -> None:
        pid = self.inv_producto_sel_id
        if pid == 0:
            self.inv_receta_items = []
            return
        with self._tenant_session() as session:
            ris = session.exec(
                select(RecetaItem)
                .where(RecetaItem.company_id == self._company_id(), RecetaItem.producto_id == pid)
                .order_by(RecetaItem.id)
            ).all()
            insumos = {
                i.id: i
                for i in session.exec(
                    select(Insumo).where(Insumo.company_id == self._company_id())
                ).all()
            }
            items: list[RecetaItemView] = []
            for ri in ris:
                ins = insumos.get(ri.insumo_id)
                cant = Decimal(str(ri.cantidad))
                unidad = ins.unidad if ins else ""
                items.append(RecetaItemView(
                    id=ri.id or 0,
                    producto_id=pid,
                    insumo_id=ri.insumo_id,
                    insumo_nombre=ins.nombre if ins else "?",
                    insumo_unidad=unidad,
                    cantidad=float(cant),
                    cantidad_texto=f"{cant:.3f}".rstrip("0").rstrip(".") + f" {unidad}",
                ))
            self.inv_receta_items = items

    def set_inv_receta_insumo_sel_nombre(self, v: str) -> None:
        self.inv_receta_insumo_sel_nombre = v

    def set_inv_receta_cantidad(self, v: str) -> None:
        self.inv_receta_cantidad = v

    def guardar_receta_item(self) -> None:
        if self.inv_producto_sel_id == 0:
            self.mensaje = "Seleccione un producto primero."
            return
        insumo_match = next(
            (i for i in self.inv_insumos if i.nombre == self.inv_receta_insumo_sel_nombre), None
        )
        if insumo_match is None:
            self.mensaje = "Seleccione un insumo válido."
            return
        try:
            cantidad = Decimal(self.inv_receta_cantidad.replace(",", ".").strip() or "0")
            if cantidad <= 0:
                raise ValueError
        except (InvalidOperation, ValueError):
            self.mensaje = "Cantidad inválida. Ingrese un número mayor a 0."
            return
        insumo_id = insumo_match.id
        with self._tenant_session() as session:
            existente = session.exec(
                select(RecetaItem).where(
                    RecetaItem.company_id == self._company_id(),
                    RecetaItem.producto_id == self.inv_producto_sel_id,
                    RecetaItem.insumo_id == insumo_id,
                )
            ).first()
            if existente:
                existente.cantidad = cantidad
                existente.updated_at = _utcnow()
                session.add(existente)
                self.mensaje = "Cantidad actualizada en receta."
            else:
                ri = RecetaItem(
                    company_id=self._company_id(),
                    producto_id=self.inv_producto_sel_id,
                    insumo_id=insumo_id,
                    cantidad=cantidad,
                )
                session.add(ri)
                self.mensaje = "Insumo agregado a la receta."
            session.commit()
        self.inv_receta_cantidad = ""
        self.inv_receta_insumo_sel_nombre = ""
        self.cargar_receta_producto()

    def eliminar_receta_item(self, item_id: int) -> None:
        with self._tenant_session() as session:
            ri = session.get(RecetaItem, item_id)
            if ri is None or ri.company_id != self._company_id():
                return
            session.delete(ri)
            session.commit()
        self.cargar_receta_producto()
        self.mensaje = "Insumo eliminado de la receta."
