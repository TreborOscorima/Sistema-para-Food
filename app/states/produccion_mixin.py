"""Planificador de producción — mixin para FoodState.

Permite armar un plan del día (producto × cantidad), explosionar los insumos
necesarios según recetas, y ver semáforo de stock (alcanza / faltante).

FoodState provee en runtime: ``_tenant_session()``, ``_company_id()``,
``productos``, ``cargar_menu()``, ``mensaje``.
"""

from __future__ import annotations

from decimal import Decimal

import reflex as rx
from sqlmodel import select

from app.models.food import Combo, Producto
from app.services.produccion_service import (
    costo_total_plan,
    explosionar_insumos,
    faltantes_plan,
)
from app.states.food_state import ProduccionNecesidadView, ProduccionPlanItem

CURRENCY_SYMBOL = "S/"


class ProduccionMixin(rx.State, mixin=True):
    """Planificador de producción: explosión de insumos para N platos."""

    prod_plan_items: list[ProduccionPlanItem] = []
    prod_resultado: list[ProduccionNecesidadView] = []
    prod_costo_total_texto: str = ""
    prod_faltantes_count: int = 0
    prod_agregar_nombre: str = ""
    prod_agregar_cantidad: str = "1"
    prod_calculado: bool = False
    prod_opciones_productos: list[str] = []

    def cargar_opciones_produccion(self) -> None:
        nombres = [p.nombre for p in self.productos if p.disponible]
        with self._tenant_session() as session:
            combos = session.exec(
                select(Combo).where(
                    Combo.company_id == self._company_id(),
                    Combo.activo.is_(True),
                )
            ).all()
            for c in combos:
                nombres.append(f"[Combo] {c.nombre}")
        self.prod_opciones_productos = sorted(nombres)

    def set_prod_agregar_nombre(self, v: str) -> None:
        self.prod_agregar_nombre = v

    def set_prod_agregar_cantidad(self, v: str) -> None:
        self.prod_agregar_cantidad = v

    def prod_agregar_item(self) -> None:
        nombre = self.prod_agregar_nombre.strip()
        if not nombre:
            self.mensaje = "Seleccione un producto o combo."
            return
        try:
            cantidad = int(self.prod_agregar_cantidad or "1")
            if cantidad < 1:
                raise ValueError
        except ValueError:
            self.mensaje = "Cantidad inválida. Ingrese un número entero mayor a 0."
            return

        es_combo = nombre.startswith("[Combo] ")
        nombre_real = nombre.removeprefix("[Combo] ")
        producto_id = 0

        if es_combo:
            with self._tenant_session() as session:
                combo = session.exec(
                    select(Combo).where(
                        Combo.company_id == self._company_id(),
                        Combo.nombre == nombre_real,
                        Combo.activo.is_(True),
                    )
                ).first()
                if combo:
                    producto_id = combo.id or 0
        else:
            prod = next((p for p in self.productos if p.nombre == nombre_real), None)
            if prod:
                producto_id = prod.id

        if producto_id == 0:
            self.mensaje = "Producto no encontrado."
            return

        existente = next(
            (i for i in self.prod_plan_items if i.producto_id == producto_id and i.nombre == nombre),
            None,
        )
        if existente:
            nuevos = []
            for item in self.prod_plan_items:
                if item.producto_id == producto_id and item.nombre == nombre:
                    nuevos.append(ProduccionPlanItem(
                        producto_id=producto_id,
                        nombre=nombre,
                        cantidad=item.cantidad + cantidad,
                    ))
                else:
                    nuevos.append(item)
            self.prod_plan_items = nuevos
        else:
            self.prod_plan_items = self.prod_plan_items + [
                ProduccionPlanItem(producto_id=producto_id, nombre=nombre, cantidad=cantidad)
            ]

        self.prod_agregar_nombre = ""
        self.prod_agregar_cantidad = "1"
        self.prod_calculado = False
        self.prod_resultado = []
        self.prod_costo_total_texto = ""
        self.prod_faltantes_count = 0

    def prod_quitar_item(self, producto_id: int) -> None:
        self.prod_plan_items = [i for i in self.prod_plan_items if i.producto_id != producto_id]
        self.prod_calculado = False
        self.prod_resultado = []
        self.prod_costo_total_texto = ""
        self.prod_faltantes_count = 0

    def prod_limpiar_plan(self) -> None:
        self.prod_plan_items = []
        self.prod_resultado = []
        self.prod_costo_total_texto = ""
        self.prod_faltantes_count = 0
        self.prod_calculado = False

    def prod_calcular(self) -> None:
        if not self.prod_plan_items:
            self.mensaje = "Agregue al menos un producto al plan."
            return

        plan = [(item.producto_id, item.cantidad) for item in self.prod_plan_items]

        with self._tenant_session() as session:
            resultado = explosionar_insumos(session, self._company_id(), plan)

        views: list[ProduccionNecesidadView] = []
        for r in resultado:
            necesaria = float(r.cantidad_necesaria)
            stock = float(r.stock_actual)
            falt = float(r.faltante)
            costo = float(r.costo_estimado)

            def _fmt(val: float, unidad: str) -> str:
                d = Decimal(str(val))
                return f"{d:.3f}".rstrip("0").rstrip(".") + f" {unidad}"

            estado = "ok" if falt == 0 else "faltante"
            views.append(ProduccionNecesidadView(
                insumo_id=r.insumo_id,
                nombre=r.nombre,
                unidad=r.unidad,
                cantidad_necesaria=necesaria,
                cantidad_necesaria_texto=_fmt(necesaria, r.unidad),
                stock_actual=stock,
                stock_actual_texto=_fmt(stock, r.unidad),
                faltante=falt,
                faltante_texto=_fmt(falt, r.unidad) if falt > 0 else "—",
                costo_estimado=costo,
                costo_estimado_texto=f"{CURRENCY_SYMBOL} {Decimal(str(costo)):.2f}",
                estado=estado,
            ))

        total = costo_total_plan(resultado)
        faltan = faltantes_plan(resultado)

        self.prod_resultado = views
        self.prod_costo_total_texto = f"{CURRENCY_SYMBOL} {total:.2f}"
        self.prod_faltantes_count = len(faltan)
        self.prod_calculado = True

        if not resultado:
            self.mensaje = "Ningún producto del plan tiene receta cargada. Agregue insumos en la sección Recetas."
        elif faltan:
            self.mensaje = f"Plan calculado. {len(faltan)} insumo(s) con stock insuficiente."
        else:
            self.mensaje = "Plan calculado. Stock suficiente para todos los insumos."
