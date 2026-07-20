"""Admin de la carta (categorias, productos, modificadores y combos).

Mixin que extrae del FoodState toda la logica de CRUD de la carta digital:
categorias, productos (con duplicacion, upload de imagen y paginacion),
grupos de modificadores con opciones, asignacion producto-grupo, seleccion
de modificadores al pedir (modal compartido mozos/mostrador), y combos
(admin + agregar a mesa/mostrador).

FoodState provee en runtime: ``_tenant_session()``, ``_company_id()``,
``mensaje``, ``categorias``, ``productos``, ``cargar_menu()``,
``cargar_mesas()``, ``mesa_seleccionada_id``, ``mesa_seleccionada_label``,
``usuario_actual``, ``mostrador_carrito``, ``_cargar_carrito_mesa()``,
``_cargar_historial_mesa()``, ``mesas_config``.
"""

from __future__ import annotations

import json as _json
import pathlib
import uuid

from app.utils.image import optimize_image
from decimal import Decimal

import reflex as rx
from pydantic import BaseModel
from sqlmodel import select

from app.models.food import (
    Categoria,
    Combo,
    ComboItem,
    DetallePedido,
    EstadoMesa,
    EstadoProduccion,
    GrupoModificador,
    Mesa,
    OpcionModificador,
    Producto,
    ProductoGrupoModificador,
)
from app.services.auditoria_service import registrar_auditoria
from app.states.food_state import (
    CarritoItem,
    CategoriaView,
    GrupoModificadorAdminView,
    ProductoView,
    _emoji_para_producto,
    _ensure_open_order,
    _FOOD_API_URL,
    _money_text,
    _parse_positive_price,
    _recalculate_order_total,
    _to_decimal,
    _utcnow,
)


# ─── Mixin de estado ────────────────────────────────────────────────────────

class CartaMixin(rx.State, mixin=True):
    """CRUD de la carta: categorias, productos, modificadores y combos."""

    # ── State vars ──────────────────────────────────────────────────────────

    carta_cat_modal: bool = False
    carta_prod_modal: bool = False
    carta_busqueda_productos: str = ""
    carta_productos_pagina: int = 1

    categoria_form_id: int = 0
    categoria_form_nombre: str = ""
    categoria_form_descripcion: str = ""
    categoria_form_orden: str = "1"
    categoria_form_estacion: str = "cocina"

    producto_form_id: int = 0
    producto_form_categoria_nombre: str = ""
    producto_form_nombre: str = ""
    producto_form_descripcion: str = ""
    producto_form_precio: str = ""
    producto_form_disponible: bool = True
    producto_form_imagen_url: str = ""
    producto_form_emoji: str = ""
    producto_form_tags: list[str] = []
    producto_form_stock_diario: str = ""
    producto_form_stock_diario_alerta: str = "5"

    # Modificadores (admin)
    grupos_modificadores: list[GrupoModificadorAdminView] = []
    mod_grupo_modal: bool = False
    mod_grupo_form_id: int = 0
    mod_grupo_form_nombre: str = ""
    mod_grupo_form_min: str = "0"
    mod_grupo_form_max: str = "1"
    mod_opciones_form: list[dict[str, str]] = []
    mod_asignar_modal: bool = False
    mod_asignar_producto_id: int = 0
    mod_asignar_producto_nombre: str = ""
    mod_asignar_grupo_ids: list[int] = []

    # Modificadores (seleccion al pedir)
    mod_seleccion_modal: bool = False
    mod_seleccion_producto_id: int = 0
    mod_seleccion_producto_nombre: str = ""
    mod_seleccion_producto_precio: float = 0.0
    mod_seleccion_grupos: list[dict[str, object]] = []
    mod_seleccion_elegidos: dict[str, list[int]] = {}
    mod_seleccion_origen: str = "mozos"

    # Combos
    combos_admin: list[dict[str, object]] = []
    combos_menu: list[dict[str, object]] = []
    combo_modal: bool = False
    combo_form_id: int = 0
    combo_form_nombre: str = ""
    combo_form_descripcion: str = ""
    combo_form_precio: str = ""
    combo_form_emoji: str = ""
    combo_form_items: list[dict[str, str]] = []

    # ── Computed vars ───────────────────────────────────────────────────────

    @rx.var
    def carta_productos_filtrados_count(self) -> int:
        q = self.carta_busqueda_productos.strip().lower()
        if not q:
            return len(self.productos)
        return sum(
            1 for p in self.productos
            if q in p.nombre.lower() or q in p.categoria_nombre.lower()
        )

    @rx.var
    def carta_productos_total_paginas(self) -> int:
        q = self.carta_busqueda_productos.strip().lower()
        if q:
            total = sum(
                1 for p in self.productos
                if q in p.nombre.lower() or q in p.categoria_nombre.lower()
            )
        else:
            total = len(self.productos)
        return max(1, (total + 19) // 20)

    @rx.var
    def carta_productos_paginados(self) -> list[ProductoView]:
        q = self.carta_busqueda_productos.strip().lower()
        if q:
            base: list[ProductoView] = [
                p for p in self.productos
                if q in p.nombre.lower() or q in p.categoria_nombre.lower()
            ]
        else:
            base = list(self.productos)
        inicio = (self.carta_productos_pagina - 1) * 20
        return base[inicio:inicio + 20]

    @rx.var
    def categorias_activas(self) -> list[CategoriaView]:
        return [c for c in self.categorias if c.activa]

    @rx.var
    def categorias_activas_nombres(self) -> list[str]:
        return [c.nombre for c in self.categorias if c.activa]

    @rx.var
    def mod_seleccion_items_flat(self) -> list[dict[str, object]]:
        result: list[dict[str, object]] = []
        for g in self.mod_seleccion_grupos:
            gid = str(g.get("id", ""))
            result.append({
                "type": "header",
                "nombre": str(g.get("nombre", "")),
                "min": int(g.get("min", 0)),
                "max": int(g.get("max", 1)),
                "grupo_id": gid,
                "opcion_id": 0,
                "precio_extra": 0.0,
                "selected": False,
                "key": f"h_{gid}",
            })
            opciones = g.get("opciones", [])
            if not isinstance(opciones, list):
                opciones = []
            elegidos = self.mod_seleccion_elegidos.get(gid, [])
            for op in opciones:
                if not isinstance(op, dict):
                    continue
                oid = int(op.get("id", 0))
                result.append({
                    "type": "option",
                    "nombre": str(op.get("nombre", "")),
                    "min": 0,
                    "max": 0,
                    "grupo_id": gid,
                    "opcion_id": oid,
                    "precio_extra": float(op.get("precio_extra", 0)),
                    "selected": oid in elegidos,
                    "key": f"o_{gid}_{oid}",
                })
        return result

    @rx.var
    def mod_seleccion_extra_total(self) -> float:
        total = 0.0
        for g in self.mod_seleccion_grupos:
            gid = str(g.get("id", ""))
            elegidos = self.mod_seleccion_elegidos.get(gid, [])
            opciones = g.get("opciones", [])
            if not isinstance(opciones, list):
                continue
            for op in opciones:
                if not isinstance(op, dict):
                    continue
                if int(op.get("id", 0)) in elegidos:
                    total += float(op.get("precio_extra", 0))
        return total

    @rx.var
    def mod_seleccion_valido(self) -> bool:
        for g in self.mod_seleccion_grupos:
            gid = str(g.get("id", ""))
            elegidos = self.mod_seleccion_elegidos.get(gid, [])
            min_req = int(g.get("min", 0))
            if len(elegidos) < min_req:
                return False
        return True

    @rx.var
    def producto_form_emoji_sugerido(self) -> str:
        return _emoji_para_producto(self.producto_form_nombre or "")

    # ─── Admin Carta -- Categorias ──────────────────────────────────────────

    def set_categoria_form_nombre(self, v: str) -> None:
        self.categoria_form_nombre = str(v)[:120]

    def set_categoria_form_descripcion(self, v: str) -> None:
        self.categoria_form_descripcion = str(v)[:240]

    def set_categoria_form_estacion(self, v: str) -> None:
        self.categoria_form_estacion = v if v in ("cocina", "barra") else "cocina"

    def set_categoria_form_orden(self, v: str) -> None:
        self.categoria_form_orden = v

    def set_carta_busqueda_productos(self, v: str) -> None:
        self.carta_busqueda_productos = v
        self.carta_productos_pagina = 1

    def carta_pagina_anterior(self) -> None:
        if self.carta_productos_pagina > 1:
            self.carta_productos_pagina -= 1

    def carta_pagina_siguiente(self) -> None:
        if self.carta_productos_pagina < self.carta_productos_total_paginas:
            self.carta_productos_pagina += 1

    def set_carta_cat_modal(self, v: bool) -> None:
        self.carta_cat_modal = bool(v)
        if not v:
            self._reset_categoria_form()

    def set_carta_prod_modal(self, v: bool) -> None:
        self.carta_prod_modal = bool(v)
        if not v:
            self._reset_producto_form()

    def abrir_cat_modal(self) -> None:
        self._reset_categoria_form()
        self.carta_cat_modal = True

    def abrir_prod_modal(self) -> None:
        self._reset_producto_form()
        self.carta_prod_modal = True

    def guardar_categoria(self) -> None:
        nombre = self.categoria_form_nombre.strip()
        if not nombre:
            return rx.toast.error("El nombre de la categoria es obligatorio.")
        try:
            orden = int(self.categoria_form_orden)
        except ValueError:
            orden = len(self.categorias) + 1
        with self._tenant_session() as session:
            if self.categoria_form_id:
                cat = session.get(Categoria, self.categoria_form_id)
                if cat is None or cat.company_id != self._company_id():
                    return rx.toast.error("Categoria no encontrada.")
                cat.nombre = nombre
                cat.descripcion = self.categoria_form_descripcion.strip() or None
                cat.orden = orden
                cat.estacion = self.categoria_form_estacion
                cat.updated_at = _utcnow()
                session.add(cat)
            else:
                cat = Categoria(
                    company_id=self._company_id(),
                    nombre=nombre,
                    descripcion=self.categoria_form_descripcion.strip() or None,
                    orden=orden,
                    estacion=self.categoria_form_estacion,
                )
                session.add(cat)
            session.commit()
        self.cargar_menu()
        self._reset_categoria_form()
        self.carta_cat_modal = False
        return rx.toast.success("Categoria guardada")

    def editar_categoria(self, categoria_id: int) -> None:
        cat = next((c for c in self.categorias if c.id == categoria_id), None)
        if cat is None:
            return
        self.categoria_form_id = cat.id
        self.categoria_form_nombre = cat.nombre
        self.categoria_form_descripcion = cat.descripcion
        self.categoria_form_orden = str(cat.orden)
        self.categoria_form_estacion = cat.estacion
        self.carta_cat_modal = True

    def toggle_categoria_activa(self, categoria_id: int) -> None:
        with self._tenant_session() as session:
            cat = session.get(Categoria, categoria_id)
            if cat is None or cat.company_id != self._company_id():
                return
            cat.activa = not cat.activa
            cat.updated_at = _utcnow()
            session.add(cat)
            session.commit()
        self.cargar_menu()

    def mover_categoria(self, categoria_id: int, direccion: str) -> None:
        cats = list(self.categorias)
        idx = next((i for i, c in enumerate(cats) if c.id == categoria_id), -1)
        if idx < 0:
            return
        swap_idx = idx - 1 if direccion == "arriba" else idx + 1
        if swap_idx < 0 or swap_idx >= len(cats):
            return
        with self._tenant_session() as session:
            cat_a = session.get(Categoria, cats[idx].id)
            cat_b = session.get(Categoria, cats[swap_idx].id)
            if cat_a is None or cat_b is None:
                return
            cat_a.orden, cat_b.orden = cat_b.orden, cat_a.orden
            now = _utcnow()
            cat_a.updated_at = now
            cat_b.updated_at = now
            session.add(cat_a)
            session.add(cat_b)
            session.commit()
        self.cargar_menu()

    def _reset_categoria_form(self) -> None:
        self.categoria_form_id = 0
        self.categoria_form_nombre = ""
        self.categoria_form_descripcion = ""
        self.categoria_form_orden = str(len(self.categorias) + 1)
        self.categoria_form_estacion = "cocina"

    def cancelar_categoria_form(self) -> None:
        self._reset_categoria_form()
        self.carta_cat_modal = False

    # ─── Admin Carta -- Modificadores ───────────────────────────────────────

    def cargar_grupos_modificadores(self) -> None:
        with self._tenant_session() as session:
            grupos = session.exec(
                select(GrupoModificador)
                .where(GrupoModificador.company_id == self._company_id())
                .order_by(GrupoModificador.orden, GrupoModificador.nombre)
            ).all()
            result: list[GrupoModificadorAdminView] = []
            for g in grupos:
                opciones_count = len(session.exec(
                    select(OpcionModificador).where(OpcionModificador.grupo_id == g.id)
                ).all())
                productos_count = len(session.exec(
                    select(ProductoGrupoModificador).where(ProductoGrupoModificador.grupo_id == g.id)
                ).all())
                result.append(GrupoModificadorAdminView(
                    id=g.id or 0,
                    nombre=g.nombre,
                    min_selecciones=g.min_selecciones,
                    max_selecciones=g.max_selecciones,
                    activo=g.activo,
                    orden=g.orden,
                    opciones_count=opciones_count,
                    productos_count=productos_count,
                ))
            self.grupos_modificadores = result

    def abrir_mod_grupo_modal(self) -> None:
        self._reset_mod_grupo_form()
        self.mod_grupo_modal = True

    def _reset_mod_grupo_form(self) -> None:
        self.mod_grupo_form_id = 0
        self.mod_grupo_form_nombre = ""
        self.mod_grupo_form_min = "0"
        self.mod_grupo_form_max = "1"
        self.mod_opciones_form = []

    def set_mod_grupo_form_nombre(self, v: str) -> None:
        self.mod_grupo_form_nombre = v

    def set_mod_grupo_form_min(self, v: str) -> None:
        self.mod_grupo_form_min = v

    def set_mod_grupo_form_max(self, v: str) -> None:
        self.mod_grupo_form_max = v

    def set_mod_grupo_modal(self, v: bool) -> None:
        self.mod_grupo_modal = bool(v)

    def agregar_opcion_mod_form(self) -> None:
        self.mod_opciones_form = self.mod_opciones_form + [{"nombre": "", "precio_extra": "0"}]

    def set_opcion_mod_nombre(self, idx_nombre: str) -> None:
        parts = idx_nombre.split("|", 1)
        if len(parts) != 2:
            return
        try:
            idx = int(parts[0])
        except ValueError:
            return
        opciones = list(self.mod_opciones_form)
        if 0 <= idx < len(opciones):
            opciones[idx] = {**opciones[idx], "nombre": parts[1]}
            self.mod_opciones_form = opciones

    def set_opcion_mod_precio(self, idx_precio: str) -> None:
        parts = idx_precio.split("|", 1)
        if len(parts) != 2:
            return
        try:
            idx = int(parts[0])
        except ValueError:
            return
        opciones = list(self.mod_opciones_form)
        if 0 <= idx < len(opciones):
            opciones[idx] = {**opciones[idx], "precio_extra": parts[1]}
            self.mod_opciones_form = opciones

    def eliminar_opcion_mod_form(self, idx: int) -> None:
        opciones = list(self.mod_opciones_form)
        if 0 <= idx < len(opciones):
            opciones.pop(idx)
            self.mod_opciones_form = opciones

    def editar_grupo_modificador(self, grupo_id: int) -> None:
        with self._tenant_session() as session:
            g = session.get(GrupoModificador, grupo_id)
            if g is None or g.company_id != self._company_id():
                return
            self.mod_grupo_form_id = g.id or 0
            self.mod_grupo_form_nombre = g.nombre
            self.mod_grupo_form_min = str(g.min_selecciones)
            self.mod_grupo_form_max = str(g.max_selecciones)
            opciones = session.exec(
                select(OpcionModificador)
                .where(OpcionModificador.grupo_id == g.id)
                .order_by(OpcionModificador.orden)
            ).all()
            self.mod_opciones_form = [
                {"nombre": o.nombre, "precio_extra": str(o.precio_extra)}
                for o in opciones
            ]
        self.mod_grupo_modal = True

    def guardar_grupo_modificador(self) -> None:
        nombre = self.mod_grupo_form_nombre.strip()
        if not nombre:
            return rx.toast.error("El nombre del grupo es obligatorio.")
        try:
            min_sel = max(0, int(self.mod_grupo_form_min))
        except ValueError:
            min_sel = 0
        try:
            max_sel = max(1, int(self.mod_grupo_form_max))
        except ValueError:
            max_sel = 1
        if min_sel > max_sel:
            min_sel = max_sel

        with self._tenant_session() as session:
            if self.mod_grupo_form_id:
                grupo = session.get(GrupoModificador, self.mod_grupo_form_id)
                if grupo is None or grupo.company_id != self._company_id():
                    return rx.toast.error("Grupo no encontrado.")
                grupo.nombre = nombre
                grupo.min_selecciones = min_sel
                grupo.max_selecciones = max_sel
                grupo.updated_at = _utcnow()
                session.exec(
                    select(OpcionModificador)
                    .where(OpcionModificador.grupo_id == grupo.id)
                ).all()
                for old_op in session.exec(
                    select(OpcionModificador).where(OpcionModificador.grupo_id == grupo.id)
                ).all():
                    session.delete(old_op)
                session.flush()
            else:
                grupo = GrupoModificador(
                    company_id=self._company_id(),
                    nombre=nombre,
                    min_selecciones=min_sel,
                    max_selecciones=max_sel,
                    orden=len(self.grupos_modificadores),
                )
                session.add(grupo)
                session.flush()

            for i, op_data in enumerate(self.mod_opciones_form):
                op_nombre = str(op_data.get("nombre", "")).strip()
                if not op_nombre:
                    continue
                try:
                    precio = max(Decimal("0"), Decimal(str(op_data.get("precio_extra", "0"))))
                except Exception:
                    precio = Decimal("0")
                session.add(OpcionModificador(
                    company_id=self._company_id(),
                    grupo_id=grupo.id or 0,
                    nombre=op_nombre,
                    precio_extra=precio,
                    orden=i,
                ))
            session.add(grupo)
            session.commit()
        self.mod_grupo_modal = False
        self._reset_mod_grupo_form()
        self.cargar_grupos_modificadores()
        return rx.toast.success("Grupo de modificadores guardado")

    def eliminar_grupo_modificador(self, grupo_id: int) -> None:
        with self._tenant_session() as session:
            g = session.get(GrupoModificador, grupo_id)
            if g is None or g.company_id != self._company_id():
                return
            for op in session.exec(
                select(OpcionModificador).where(OpcionModificador.grupo_id == grupo_id)
            ).all():
                session.delete(op)
            for pg in session.exec(
                select(ProductoGrupoModificador).where(ProductoGrupoModificador.grupo_id == grupo_id)
            ).all():
                session.delete(pg)
            session.delete(g)
            session.commit()
        self.cargar_grupos_modificadores()
        return rx.toast.success("Grupo eliminado")

    def abrir_mod_asignar(self, producto_id: int) -> None:
        with self._tenant_session() as session:
            p = session.get(Producto, producto_id)
            if p is None or p.company_id != self._company_id():
                return
            self.mod_asignar_producto_id = p.id or 0
            self.mod_asignar_producto_nombre = p.nombre
            asignados = session.exec(
                select(ProductoGrupoModificador)
                .where(ProductoGrupoModificador.producto_id == p.id)
            ).all()
            self.mod_asignar_grupo_ids = [a.grupo_id for a in asignados]
        self.mod_asignar_modal = True

    def set_mod_asignar_modal(self, v: bool) -> None:
        self.mod_asignar_modal = bool(v)

    def toggle_mod_asignar_grupo(self, grupo_id: int) -> None:
        ids = list(self.mod_asignar_grupo_ids)
        if grupo_id in ids:
            ids.remove(grupo_id)
        else:
            ids.append(grupo_id)
        self.mod_asignar_grupo_ids = ids

    def guardar_mod_asignacion(self) -> None:
        with self._tenant_session() as session:
            for pg in session.exec(
                select(ProductoGrupoModificador)
                .where(ProductoGrupoModificador.producto_id == self.mod_asignar_producto_id)
            ).all():
                session.delete(pg)
            session.flush()
            for gid in self.mod_asignar_grupo_ids:
                session.add(ProductoGrupoModificador(
                    producto_id=self.mod_asignar_producto_id,
                    grupo_id=gid,
                ))
            session.commit()
        self.mod_asignar_modal = False
        self.cargar_menu()
        return rx.toast.success("Modificadores asignados")

    # ─── Combos Admin ───────────────────────────────────────────────────────

    def cargar_combos(self) -> None:
        with self._tenant_session() as session:
            combos = session.exec(
                select(Combo).where(Combo.company_id == self._company_id()).order_by(Combo.orden, Combo.nombre)
            ).all()
            admin_list: list[dict[str, object]] = []
            menu_list: list[dict[str, object]] = []
            for c in combos:
                items_db = session.exec(
                    select(ComboItem).where(ComboItem.combo_id == c.id)
                ).all()
                prod_ids = [ci.producto_id for ci in items_db]
                productos = {p.id: p for p in session.exec(select(Producto).where(Producto.id.in_(prod_ids))).all()} if prod_ids else {}
                items_texto = ", ".join(
                    f"{ci.cantidad}x {productos.get(ci.producto_id, Producto(nombre='?')).nombre}"
                    for ci in items_db
                )
                precio_f = float(_to_decimal(c.precio))
                entry: dict[str, object] = {
                    "id": c.id or 0,
                    "nombre": c.nombre,
                    "descripcion": c.descripcion or "",
                    "precio": precio_f,
                    "precio_texto": _money_text(c.precio),
                    "emoji": c.emoji or "\U0001f371",
                    "activo": c.activo,
                    "orden": c.orden,
                    "items_count": len(items_db),
                    "items_texto": items_texto,
                }
                admin_list.append(entry)
                if c.activo:
                    menu_list.append(entry)
            self.combos_admin = admin_list
            self.combos_menu = menu_list

    def abrir_combo_modal(self) -> None:
        self.combo_form_id = 0
        self.combo_form_nombre = ""
        self.combo_form_descripcion = ""
        self.combo_form_precio = ""
        self.combo_form_emoji = ""
        self.combo_form_items = [{"producto_id": "", "cantidad": "1"}]
        self.combo_modal = True

    def set_combo_modal(self, v: bool) -> None:
        self.combo_modal = bool(v)

    def set_combo_form_nombre(self, v: str) -> None:
        self.combo_form_nombre = str(v)[:160]

    def set_combo_form_descripcion(self, v: str) -> None:
        self.combo_form_descripcion = str(v)[:240]

    def set_combo_form_precio(self, v: str) -> None:
        self.combo_form_precio = v

    def set_combo_form_emoji(self, v: str) -> None:
        self.combo_form_emoji = str(v)[:16]

    def combo_add_item(self) -> None:
        items = list(self.combo_form_items)
        items.append({"producto_id": "", "cantidad": "1"})
        self.combo_form_items = items

    def combo_remove_item(self, idx: int) -> None:
        items = list(self.combo_form_items)
        if 0 <= idx < len(items) and len(items) > 1:
            items.pop(idx)
        self.combo_form_items = items

    def combo_set_item_field(self, payload: str) -> None:
        parts = payload.split("|", 2)
        if len(parts) != 3:
            return
        idx_str, field, value = parts
        try:
            idx = int(idx_str)
        except ValueError:
            return
        items = list(self.combo_form_items)
        if 0 <= idx < len(items):
            item = dict(items[idx])
            item[field] = value
            items[idx] = item
        self.combo_form_items = items

    def editar_combo(self, combo_id: int) -> None:
        with self._tenant_session() as session:
            combo = session.get(Combo, combo_id)
            if combo is None or combo.company_id != self._company_id():
                return
            self.combo_form_id = combo.id or 0
            self.combo_form_nombre = combo.nombre
            self.combo_form_descripcion = combo.descripcion or ""
            self.combo_form_precio = str(combo.precio)
            self.combo_form_emoji = combo.emoji or ""
            items_db = session.exec(select(ComboItem).where(ComboItem.combo_id == combo.id)).all()
            self.combo_form_items = [
                {"producto_id": str(ci.producto_id), "cantidad": str(ci.cantidad)}
                for ci in items_db
            ] or [{"producto_id": "", "cantidad": "1"}]
        self.combo_modal = True

    def guardar_combo(self) -> None:
        nombre = self.combo_form_nombre.strip()
        if not nombre:
            return rx.toast.error("El combo necesita un nombre.")
        try:
            precio = Decimal(self.combo_form_precio.replace(",", ".").strip())
        except (ValueError, InvalidOperation):
            return rx.toast.error("Precio invalido para el combo.")
        if precio < 0:
            return rx.toast.error("El precio no puede ser negativo.")
        items_validos: list[tuple[int, int]] = []
        for item in self.combo_form_items:
            pid_str = str(item.get("producto_id", "")).strip()
            cant_str = str(item.get("cantidad", "1")).strip()
            if not pid_str:
                continue
            try:
                pid = int(pid_str)
                cant = max(int(cant_str), 1)
            except ValueError:
                continue
            items_validos.append((pid, cant))
        if not items_validos:
            return rx.toast.error("Agrega al menos un producto al combo.")
        with self._tenant_session() as session:
            if self.combo_form_id > 0:
                combo = session.get(Combo, self.combo_form_id)
                if combo is None or combo.company_id != self._company_id():
                    return rx.toast.error("Combo no encontrado.")
                combo.nombre = nombre
                combo.descripcion = self.combo_form_descripcion.strip() or None
                combo.precio = precio
                combo.emoji = self.combo_form_emoji.strip() or None
                for old_item in session.exec(select(ComboItem).where(ComboItem.combo_id == combo.id)).all():
                    session.delete(old_item)
                session.flush()
            else:
                combo = Combo(
                    company_id=self._company_id(),
                    nombre=nombre,
                    descripcion=self.combo_form_descripcion.strip() or None,
                    precio=precio,
                    emoji=self.combo_form_emoji.strip() or None,
                )
                session.add(combo)
                session.flush()
            for pid, cant in items_validos:
                session.add(ComboItem(combo_id=combo.id or 0, producto_id=pid, cantidad=cant))
            session.commit()
        self.combo_modal = False
        self.cargar_combos()
        action = "actualizado" if self.combo_form_id > 0 else "creado"
        return rx.toast.success(f"Combo \"{nombre}\" {action}")

    def toggle_combo_activo(self, combo_id: int) -> None:
        with self._tenant_session() as session:
            combo = session.get(Combo, combo_id)
            if combo is None or combo.company_id != self._company_id():
                return
            combo.activo = not combo.activo
            session.commit()
        self.cargar_combos()

    def eliminar_combo(self, combo_id: int) -> None:
        with self._tenant_session() as session:
            combo = session.get(Combo, combo_id)
            if combo is None or combo.company_id != self._company_id():
                return
            for ci in session.exec(select(ComboItem).where(ComboItem.combo_id == combo.id)).all():
                session.delete(ci)
            session.delete(combo)
            session.commit()
        self.cargar_combos()
        return rx.toast.success("Combo eliminado")

    def agregar_combo(self, combo_id: int) -> None:
        combo_data = next((c for c in self.combos_menu if c.get("id") == combo_id), None)
        if combo_data is None:
            return rx.toast.error("Combo no disponible.")
        if self.mesa_seleccionada_id == 0:
            return rx.toast.error("Seleccione una mesa antes de agregar combos.")
        with self._tenant_session() as session:
            mesa = session.get(Mesa, self.mesa_seleccionada_id)
            if mesa is None or mesa.company_id != self._company_id():
                return rx.toast.error("La mesa seleccionada ya no existe.")
            combo = session.get(Combo, combo_id)
            if combo is None or combo.company_id != self._company_id() or not combo.activo:
                return rx.toast.error("Combo no disponible.")
            items_db = session.exec(select(ComboItem).where(ComboItem.combo_id == combo.id)).all()
            productos = {p.id: p for p in session.exec(select(Producto).where(Producto.company_id == self._company_id())).all()}
            combo_snapshot = [
                {
                    "producto_id": ci.producto_id,
                    "nombre": productos.get(ci.producto_id, Producto(nombre="?")).nombre,
                    "cantidad": ci.cantidad,
                }
                for ci in items_db
            ]
            pedido = _ensure_open_order(session, mesa, self._company_id(), mozo_id=(self.usuario_actual.id or None) if self.usuario_actual else None)
            precio = _to_decimal(combo.precio)
            first_pid = items_db[0].producto_id if items_db else 0
            detalle = DetallePedido(
                company_id=self._company_id(),
                pedido_id=pedido.id or 0,
                producto_id=first_pid,
                cantidad=1,
                precio_unitario=precio,
                subtotal=precio,
                estado_produccion=EstadoProduccion.PENDIENTE.value,
                impreso_cocina=False,
                impreso_caja=False,
                combo_items_json=_json.dumps(combo_snapshot, ensure_ascii=False),
            )
            session.add(detalle)
            _recalculate_order_total(session, pedido)
            mesa.estado = EstadoMesa.OCUPADA.value
            mesa.updated_at = _utcnow()
            session.add(mesa)
            session.commit()
        self._cargar_carrito_mesa(self.mesa_seleccionada_id)
        self._cargar_historial_mesa(self.mesa_seleccionada_id)
        self.cargar_mesas()
        return rx.toast.success(f"Combo \"{combo_data.get('nombre', '')}\" agregado")

    def agregar_combo_mostrador(self, combo_id: int) -> None:
        combo_data = next((c for c in self.combos_menu if c.get("id") == combo_id), None)
        if combo_data is None:
            return rx.toast.error("Combo no disponible.")
        with self._tenant_session() as session:
            combo = session.get(Combo, combo_id)
            if combo is None or not combo.activo:
                return rx.toast.error("Combo no disponible.")
            items_db = session.exec(select(ComboItem).where(ComboItem.combo_id == combo.id)).all()
            productos = {p.id: p for p in session.exec(select(Producto).where(Producto.company_id == self._company_id())).all()}
            combo_snapshot = [
                {
                    "producto_id": ci.producto_id,
                    "nombre": productos.get(ci.producto_id, Producto(nombre="?")).nombre,
                    "cantidad": ci.cantidad,
                }
                for ci in items_db
            ]
        precio_f = float(combo_data.get("precio", 0))
        carrito = list(self.mostrador_carrito)
        carrito.append(CarritoItem(
            producto_id=0,
            nombre=str(combo_data.get("nombre", "")),
            cantidad=1,
            precio_unitario=precio_f,
            subtotal=precio_f,
            subtotal_texto=_money_text(precio_f),
            combo_items_json=_json.dumps(combo_snapshot, ensure_ascii=False),
            es_combo=True,
        ))
        self.mostrador_carrito = carrito
        return rx.toast.success(f"Combo \"{combo_data.get('nombre', '')}\" agregado a mostrador")

    # ─── Modificadores -- Seleccion al pedir ────────────────────────────────

    def _abrir_seleccion_modificadores(self, producto_id: int, producto_nombre: str, precio: float, origen: str = "mozos") -> None:
        with self._tenant_session() as session:
            asignaciones = session.exec(
                select(ProductoGrupoModificador)
                .where(ProductoGrupoModificador.producto_id == producto_id)
            ).all()
            grupo_ids = [a.grupo_id for a in asignaciones]
            if not grupo_ids:
                return
            grupos = session.exec(
                select(GrupoModificador)
                .where(GrupoModificador.id.in_(grupo_ids), GrupoModificador.activo.is_(True))
                .order_by(GrupoModificador.orden)
            ).all()
            grupos_data: list[dict[str, object]] = []
            for g in grupos:
                opciones = session.exec(
                    select(OpcionModificador)
                    .where(OpcionModificador.grupo_id == g.id, OpcionModificador.activo.is_(True))
                    .order_by(OpcionModificador.orden)
                ).all()
                grupos_data.append({
                    "id": g.id or 0,
                    "nombre": g.nombre,
                    "min": g.min_selecciones,
                    "max": g.max_selecciones,
                    "opciones": [
                        {"id": o.id or 0, "nombre": o.nombre, "precio_extra": float(o.precio_extra)}
                        for o in opciones
                    ],
                })
        self.mod_seleccion_producto_id = producto_id
        self.mod_seleccion_producto_nombre = producto_nombre
        self.mod_seleccion_producto_precio = precio
        self.mod_seleccion_grupos = grupos_data
        self.mod_seleccion_elegidos = {}
        self.mod_seleccion_origen = origen
        self.mod_seleccion_modal = True

    def set_mod_seleccion_modal(self, v: bool) -> None:
        self.mod_seleccion_modal = bool(v)

    def toggle_mod_opcion(self, grupo_id_opcion_id: str) -> None:
        parts = grupo_id_opcion_id.split("_")
        if len(parts) != 2:
            return
        grupo_id_str, opcion_id_str = parts
        elegidos = dict(self.mod_seleccion_elegidos)
        lista = list(elegidos.get(grupo_id_str, []))
        opcion_id = int(opcion_id_str)
        grupo_max = 1
        for g in self.mod_seleccion_grupos:
            if str(g.get("id", "")) == grupo_id_str:
                grupo_max = int(g.get("max", 1))
                break
        if opcion_id in lista:
            lista.remove(opcion_id)
        else:
            if len(lista) >= grupo_max:
                if grupo_max == 1:
                    lista = [opcion_id]
                else:
                    return
            else:
                lista.append(opcion_id)
        elegidos[grupo_id_str] = lista
        self.mod_seleccion_elegidos = elegidos

    def confirmar_mod_seleccion(self) -> None:
        for g in self.mod_seleccion_grupos:
            gid = str(g.get("id", ""))
            elegidos = self.mod_seleccion_elegidos.get(gid, [])
            min_req = int(g.get("min", 0))
            if len(elegidos) < min_req:
                return rx.toast.error(f"Seleccione al menos {min_req} opcion(es) en \"{g.get('nombre', '')}\".")

        mods_snapshot: list[dict[str, object]] = []
        extra_total = Decimal("0")
        for g in self.mod_seleccion_grupos:
            gid = str(g.get("id", ""))
            elegidos = self.mod_seleccion_elegidos.get(gid, [])
            opciones_data = g.get("opciones", [])
            if not isinstance(opciones_data, list):
                opciones_data = []
            for oid in elegidos:
                for op in opciones_data:
                    if not isinstance(op, dict):
                        continue
                    if op.get("id") == oid:
                        precio_extra = Decimal(str(op.get("precio_extra", 0)))
                        extra_total += precio_extra
                        mods_snapshot.append({
                            "grupo": g.get("nombre", ""),
                            "opcion": op.get("nombre", ""),
                            "precio_extra": float(precio_extra),
                        })

        mods_json = _json.dumps(mods_snapshot, ensure_ascii=False)
        mods_texto = ", ".join(
            m.get("opcion", "") + (f" +S/{m['precio_extra']:.2f}" if m.get("precio_extra", 0) > 0 else "")
            for m in mods_snapshot
        ) if mods_snapshot else ""

        self.mod_seleccion_modal = False
        if self.mod_seleccion_origen == "mostrador":
            self._agregar_producto_mostrador_con_mods(
                self.mod_seleccion_producto_id,
                mods_json,
                mods_texto,
                extra_total,
            )
        else:
            self._agregar_producto_con_mods(
                self.mod_seleccion_producto_id,
                mods_json,
                mods_texto,
                extra_total,
            )

    def _agregar_producto_con_mods(self, producto_id: int, mods_json: str, mods_texto: str, extra: Decimal) -> None:
        if self.mesa_seleccionada_id == 0:
            return rx.toast.error("Seleccione una mesa antes de agregar productos.")
        with self._tenant_session() as session:
            mesa = session.get(Mesa, self.mesa_seleccionada_id)
            if mesa is None or mesa.company_id != self._company_id():
                return rx.toast.error("La mesa seleccionada ya no existe.")
            producto = session.get(Producto, producto_id)
            if producto is None or producto.company_id != self._company_id() or not producto.disponible:
                return rx.toast.error("Producto no disponible.")
            producto_nombre = producto.nombre
            pedido = _ensure_open_order(session, mesa, self._company_id(), mozo_id=(self.usuario_actual.id or None) if self.usuario_actual else None)
            precio = _to_decimal(producto.precio) + extra
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
                modificadores_json=mods_json if mods_json else None,
            )
            session.add(detalle)
            _recalculate_order_total(session, pedido)
            mesa.estado = EstadoMesa.OCUPADA.value
            mesa.updated_at = _utcnow()
            session.add(mesa)
            session.commit()
        self._cargar_carrito_mesa(self.mesa_seleccionada_id)
        self._cargar_historial_mesa(self.mesa_seleccionada_id)
        self.cargar_mesas()
        return rx.toast.success(f"{producto_nombre} agregado a {self.mesa_seleccionada_label}")

    # ─── Admin Carta -- Productos ───────────────────────────────────────────

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

    def set_producto_form_emoji(self, v: str) -> None:
        self.producto_form_emoji = str(v)[:8]

    def set_producto_form_stock_diario(self, v: str) -> None:
        self.producto_form_stock_diario = v

    def set_producto_form_stock_diario_alerta(self, v: str) -> None:
        self.producto_form_stock_diario_alerta = v

    def toggle_producto_tag(self, tag: str) -> None:
        if tag in self.producto_form_tags:
            self.producto_form_tags = [t for t in self.producto_form_tags if t != tag]
        else:
            self.producto_form_tags = self.producto_form_tags + [tag]

    def guardar_producto(self) -> None:
        nombre = self.producto_form_nombre.strip()
        if not nombre:
            return rx.toast.error("El nombre del producto es obligatorio.")
        precio = _parse_positive_price(self.producto_form_precio)
        if precio is None:
            return rx.toast.error("El precio debe ser un numero mayor a 0.")
        with self._tenant_session() as session:
            cat = session.exec(
                select(Categoria).where(
                    Categoria.company_id == self._company_id(),
                    Categoria.nombre == self.producto_form_categoria_nombre,
                )
            ).first()
            if cat is None:
                return rx.toast.error(f"Categoria '{self.producto_form_categoria_nombre}' no encontrada.")
            if self.producto_form_id:
                prod = session.get(Producto, self.producto_form_id)
                if prod is None or prod.company_id != self._company_id():
                    return rx.toast.error("Producto no encontrado.")
                precio_anterior = prod.precio
                prod.nombre = nombre
                prod.descripcion = self.producto_form_descripcion.strip() or None
                prod.precio = precio
                prod.categoria_id = cat.id or 0
                prod.disponible = self.producto_form_disponible
                prod.imagen_url = self.producto_form_imagen_url or None
                prod.emoji = self.producto_form_emoji.strip() or None
                prod.tags = self.producto_form_tags or None
                sd = self.producto_form_stock_diario.strip()
                prod.stock_diario = int(sd) if sd else None
                sda = self.producto_form_stock_diario_alerta.strip()
                prod.stock_diario_alerta = int(sda) if sda and int(sda) > 0 else 5
                prod.updated_at = _utcnow()
                session.add(prod)
                if precio != precio_anterior:
                    registrar_auditoria(
                        session, self._company_id(), "cambio_precio",
                        usuario_id=(self.usuario_actual.id or None) if self.usuario_actual else None,
                        usuario_nombre=(self.usuario_actual.nombre if self.usuario_actual else ""),
                        entidad="producto", entidad_id=prod.id,
                        detalle={"nombre": nombre, "anterior": str(precio_anterior), "nuevo": str(precio)},
                    )
            else:
                sd = self.producto_form_stock_diario.strip()
                sda = self.producto_form_stock_diario_alerta.strip()
                prod = Producto(
                    company_id=self._company_id(),
                    categoria_id=cat.id or 0,
                    nombre=nombre,
                    descripcion=self.producto_form_descripcion.strip() or None,
                    precio=precio,
                    disponible=self.producto_form_disponible,
                    imagen_url=self.producto_form_imagen_url or None,
                    emoji=self.producto_form_emoji.strip() or None,
                    tags=self.producto_form_tags or None,
                    stock_diario=int(sd) if sd else None,
                    stock_diario_alerta=int(sda) if sda and int(sda) > 0 else 5,
                )
                session.add(prod)
            session.commit()
        self.cargar_menu()
        self._reset_producto_form()
        self.carta_prod_modal = False
        return rx.toast.success("Producto guardado")

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
        self.producto_form_imagen_url = prod.imagen_url
        with self._tenant_session() as session:
            prod_db = session.get(Producto, producto_id)
            self.producto_form_emoji = (prod_db.emoji or "") if prod_db else ""
            self.producto_form_tags = list(prod_db.tags) if prod_db and prod_db.tags else []
            self.producto_form_stock_diario = str(prod_db.stock_diario) if prod_db and prod_db.stock_diario is not None else ""
            self.producto_form_stock_diario_alerta = str(prod_db.stock_diario_alerta) if prod_db else "5"
        self.carta_prod_modal = True

    def duplicar_producto(self, producto_id: int) -> None:
        prod = next((p for p in self.productos if p.id == producto_id), None)
        if prod is None:
            return
        self.producto_form_id = 0
        self.producto_form_nombre = f"Copia de {prod.nombre}"
        self.producto_form_descripcion = prod.descripcion
        self.producto_form_precio = str(prod.precio)
        self.producto_form_categoria_nombre = prod.categoria_nombre
        self.producto_form_disponible = prod.disponible
        self.producto_form_imagen_url = prod.imagen_url
        with self._tenant_session() as session:
            prod_db = session.get(Producto, producto_id)
            self.producto_form_emoji = (prod_db.emoji or "") if prod_db else ""
            self.producto_form_tags = list(prod_db.tags) if prod_db and prod_db.tags else []
            self.producto_form_stock_diario = str(prod_db.stock_diario) if prod_db and prod_db.stock_diario is not None else ""
            self.producto_form_stock_diario_alerta = str(prod_db.stock_diario_alerta) if prod_db else "5"
        self.carta_prod_modal = True

    def toggle_producto_disponible(self, producto_id: int):
        with self._tenant_session() as session:
            prod = session.get(Producto, producto_id)
            if prod is None or prod.company_id != self._company_id():
                return
            prod.disponible = not prod.disponible
            prod.updated_at = _utcnow()
            nombre = prod.nombre
            nuevo_estado = prod.disponible
            session.add(prod)
            session.commit()
        self.cargar_menu()
        if nuevo_estado:
            return rx.toast.success(f"{nombre} disponible nuevamente")
        return rx.toast(f"{nombre} marcado como agotado (86)", variant="warning")

    def _reset_producto_form(self) -> None:
        self.producto_form_id = 0
        self.producto_form_nombre = ""
        self.producto_form_descripcion = ""
        self.producto_form_precio = ""
        self.producto_form_disponible = True
        self.producto_form_imagen_url = ""
        self.producto_form_emoji = ""
        self.producto_form_tags = []
        self.producto_form_stock_diario = ""
        self.producto_form_stock_diario_alerta = "5"
        if self.categorias:
            self.producto_form_categoria_nombre = self.categorias[0].nombre

    def cancelar_producto_form(self) -> None:
        self._reset_producto_form()
        self.carta_prod_modal = False

    async def handle_upload_imagen_producto(self, files: list[rx.UploadFile]) -> None:
        for file in files:
            try:
                data = await file.read()
                if len(data) > 5 * 1024 * 1024:
                    return rx.toast.error("La imagen excede 5 MB.", duration=4000)
                data, ext = optimize_image(data)
                filename = f"food_prod_{uuid.uuid4().hex[:12]}{ext}"
                upload_dir = pathlib.Path(rx.get_upload_dir()) / "food_productos"
                upload_dir.mkdir(parents=True, exist_ok=True)
                (upload_dir / filename).write_bytes(data)
                self.producto_form_imagen_url = f"{_FOOD_API_URL}/_upload/food_productos/{filename}"
            except Exception:
                return rx.toast.error(
                    "Error al subir la imagen. Verifique permisos del servidor.",
                    duration=5000,
                )
            break

    def quitar_imagen_producto(self) -> None:
        self.producto_form_imagen_url = ""
