"""Substate independiente — gestión de usuarios y PINs del local.

Hereda de rx.State (NO de FoodState). Accede a datos de tenant vía
`await self.get_state(FoodState)` para obtener `_company_id()`,
`usuario_actual`, y `empresa_plan`.
"""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone

import bcrypt as _bcrypt

import reflex as rx
from sqlmodel import select

from app.models.food import RolUsuario, UsuarioFood
from app.services.plan_service import check_limite_usuarios
from app.states.food_state import (
    UsuarioAdminView,
    ROLE_ALLOWED_ROUTES,
    _ROL_LABELS,
    _ROL_BADGE_BG,
    _ROL_BADGE_TEXT,
    _ROL_PERM_DEFAULTS,
    _ROL_ACCESO_DEFAULTS,
)
from app.utils.db import get_session
from app.utils.tenant import set_tenant_context


# ─── Helpers locales ──────────────────────────────────────────────────────────

def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _normalize_pin(raw: str) -> str:
    return "".join(c for c in str(raw) if c.isdigit())[:6]


def _hash_pin(plain: str) -> str:
    return _bcrypt.hashpw(plain.encode(), _bcrypt.gensalt()).decode()


def _verify_pin(plain: str, hashed: str) -> bool:
    try:
        return _bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False


# ─── State ────────────────────────────────────────────────────────────────────


class UsuariosAdminState(rx.State):
    """Estado independiente para el CRUD de usuarios del local."""

    usuarios_admin: list[UsuarioAdminView] = []
    usuario_form_id: int = 0
    usuario_form_nombre: str = ""
    usuario_form_rol: str = RolUsuario.MOZO.value
    usuario_form_pin: str = ""
    usuario_form_pin_confirm: str = ""
    usuario_form_activo: bool = True
    usuario_form_visible: bool = False
    usuario_form_perm_descuento: bool = False
    usuario_form_perm_anular: bool = False
    usuario_form_perm_reportes: bool = False
    usuario_form_perm_turno: bool = False
    usuario_form_perm_inventario: bool = False
    usuario_form_perm_costos: bool = False
    usuario_form_perm_reimprimir: bool = False
    usuario_form_perm_corregir: bool = False
    usuario_form_acceso_mozos: bool = False
    usuario_form_acceso_caja: bool = False
    usuario_form_acceso_cocina: bool = False
    usuario_form_acceso_mostrador: bool = False

    # ─── Helpers internos ─────────────────────────────────────────────────────

    async def _food(self):
        from app.states.food_state import FoodState
        return await self.get_state(FoodState)

    def _company_id_from(self, food) -> int:
        """Obtiene company_id desde una referencia ya resuelta de FoodState."""
        company_id = (
            food.usuario_actual.company_id
            if food.usuario_actual is not None
            else food.login_selected_company_id
        )
        set_tenant_context(company_id, None)
        return company_id

    @contextmanager
    def _tenant_session_from(self, food):
        """Abre sesión DB con tenant armado desde food state resuelto."""
        self._company_id_from(food)
        with get_session() as session:
            session.info["tenant_bypass"] = True
            yield session

    # ─── Computed vars ────────────────────────────────────────────────────────

    @rx.var
    def usuario_form_es_edicion(self) -> bool:
        return self.usuario_form_id > 0

    @rx.var
    def roles_disponibles(self) -> list[str]:
        return [r.value for r in RolUsuario]

    # ─── Event handlers ───────────────────────────────────────────────────────

    def on_change_uf_nombre(self, value: str) -> None:
        self.usuario_form_nombre = value

    def on_change_uf_rol(self, value: str) -> None:
        self.usuario_form_rol = value
        _defs = _ROL_PERM_DEFAULTS.get(value, {})
        self.usuario_form_perm_descuento = _defs.get("descuento", False)
        self.usuario_form_perm_anular = _defs.get("anular", False)
        self.usuario_form_perm_reportes = _defs.get("reportes", False)
        self.usuario_form_perm_turno = _defs.get("turno", False)
        self.usuario_form_perm_inventario = _defs.get("inventario", False)
        self.usuario_form_perm_costos = _defs.get("costos", False)
        self.usuario_form_perm_reimprimir = _defs.get("reimprimir", False)
        self.usuario_form_perm_corregir = _defs.get("corregir", False)
        _acc = _ROL_ACCESO_DEFAULTS.get(value, {})
        self.usuario_form_acceso_mozos = _acc.get("mozos", False)
        self.usuario_form_acceso_caja = _acc.get("caja", False)
        self.usuario_form_acceso_cocina = _acc.get("cocina", False)
        self.usuario_form_acceso_mostrador = _acc.get("mostrador", False)

    def toggle_uf_perm_descuento(self) -> None:
        self.usuario_form_perm_descuento = not self.usuario_form_perm_descuento

    def toggle_uf_perm_anular(self) -> None:
        self.usuario_form_perm_anular = not self.usuario_form_perm_anular

    def toggle_uf_perm_reportes(self) -> None:
        self.usuario_form_perm_reportes = not self.usuario_form_perm_reportes

    def toggle_uf_perm_turno(self) -> None:
        self.usuario_form_perm_turno = not self.usuario_form_perm_turno

    def toggle_uf_perm_inventario(self) -> None:
        self.usuario_form_perm_inventario = not self.usuario_form_perm_inventario

    def toggle_uf_perm_costos(self) -> None:
        self.usuario_form_perm_costos = not self.usuario_form_perm_costos

    def toggle_uf_perm_reimprimir(self) -> None:
        self.usuario_form_perm_reimprimir = not self.usuario_form_perm_reimprimir

    def toggle_uf_perm_corregir(self) -> None:
        self.usuario_form_perm_corregir = not self.usuario_form_perm_corregir

    def toggle_uf_acceso_mozos(self) -> None:
        self.usuario_form_acceso_mozos = not self.usuario_form_acceso_mozos

    def toggle_uf_acceso_caja(self) -> None:
        self.usuario_form_acceso_caja = not self.usuario_form_acceso_caja

    def toggle_uf_acceso_cocina(self) -> None:
        self.usuario_form_acceso_cocina = not self.usuario_form_acceso_cocina

    def toggle_uf_acceso_mostrador(self) -> None:
        self.usuario_form_acceso_mostrador = not self.usuario_form_acceso_mostrador

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
        self.usuario_form_visible = False
        _defs = _ROL_PERM_DEFAULTS[RolUsuario.MOZO.value]
        self.usuario_form_perm_descuento = _defs["descuento"]
        self.usuario_form_perm_anular = _defs["anular"]
        self.usuario_form_perm_reportes = _defs["reportes"]
        self.usuario_form_perm_turno = _defs["turno"]
        self.usuario_form_perm_inventario = _defs["inventario"]
        self.usuario_form_perm_costos = _defs["costos"]
        self.usuario_form_perm_reimprimir = _defs["reimprimir"]
        self.usuario_form_perm_corregir = _defs["corregir"]
        _acc = _ROL_ACCESO_DEFAULTS[RolUsuario.MOZO.value]
        self.usuario_form_acceso_mozos = _acc["mozos"]
        self.usuario_form_acceso_caja = _acc["caja"]
        self.usuario_form_acceso_cocina = _acc["cocina"]
        self.usuario_form_acceso_mostrador = _acc["mostrador"]

    def set_usuario_form_visible(self, v: bool) -> None:
        self.usuario_form_visible = v

    def _do_cargar_usuarios_admin(self, food) -> None:
        """Carga sincrónica — requiere food ya resuelto."""
        mi_id = food.usuario_actual.id if food.usuario_actual else 0
        company_id = self._company_id_from(food)
        with self._tenant_session_from(food) as session:
            rows = session.exec(
                select(UsuarioFood)
                .where(UsuarioFood.company_id == company_id)
                .order_by(UsuarioFood.rol, UsuarioFood.nombre)
            ).all()
        self.usuarios_admin = [
            UsuarioAdminView(
                id=u.id or 0,
                nombre=u.nombre,
                rol=u.rol,
                rol_label=_ROL_LABELS.get(u.rol, u.rol),
                pin_masked="●●●●",
                activo=u.activo,
                badge_bg=_ROL_BADGE_BG.get(u.rol, "rgba(100,116,139,0.16)"),
                badge_text=_ROL_BADGE_TEXT.get(u.rol, "#94A3B8"),
                es_yo=u.id == mi_id,
                perm_descuento=u.perm_descuento,
                perm_anular=u.perm_anular,
                perm_reportes=u.perm_reportes,
                perm_turno=u.perm_turno,
                perm_inventario=u.perm_inventario,
                perm_costos=u.perm_costos,
                perm_reimprimir=u.perm_reimprimir,
                perm_corregir=u.perm_corregir,
                acceso_mozos=u.acceso_mozos,
                acceso_caja=u.acceso_caja,
                acceso_cocina=u.acceso_cocina,
                acceso_mostrador=u.acceso_mostrador,
            )
            for u in rows
        ]

    async def cargar_usuarios_admin(self) -> None:
        food = await self._food()
        self._do_cargar_usuarios_admin(food)

    def nuevo_usuario_form(self) -> None:
        self._limpiar_usuario_form()
        self.usuario_form_visible = True

    async def editar_usuario(self, user_id: int) -> None:
        food = await self._food()
        company_id = self._company_id_from(food)
        with self._tenant_session_from(food) as session:
            u = session.get(UsuarioFood, user_id)
        if u is None or u.company_id != company_id:
            return rx.toast.error("Usuario no encontrado.")
        self.usuario_form_id = u.id or 0
        self.usuario_form_nombre = u.nombre
        self.usuario_form_rol = u.rol
        self.usuario_form_pin = ""
        self.usuario_form_pin_confirm = ""
        self.usuario_form_activo = u.activo
        self.usuario_form_perm_descuento = u.perm_descuento
        self.usuario_form_perm_anular = u.perm_anular
        self.usuario_form_perm_reportes = u.perm_reportes
        self.usuario_form_perm_turno = u.perm_turno
        self.usuario_form_perm_inventario = u.perm_inventario
        self.usuario_form_perm_costos = u.perm_costos
        self.usuario_form_perm_reimprimir = u.perm_reimprimir
        self.usuario_form_perm_corregir = u.perm_corregir
        self.usuario_form_acceso_mozos = u.acceso_mozos
        self.usuario_form_acceso_caja = u.acceso_caja
        self.usuario_form_acceso_cocina = u.acceso_cocina
        self.usuario_form_acceso_mostrador = u.acceso_mostrador
        self.usuario_form_visible = True

    async def guardar_usuario(self) -> None:
        food = await self._food()
        company_id = self._company_id_from(food)

        nombre = self.usuario_form_nombre.strip()
        if not nombre:
            return rx.toast.error("El nombre es obligatorio.")
        rol = self.usuario_form_rol
        if rol not in [r.value for r in RolUsuario]:
            return rx.toast.error("Rol inválido.")

        nuevo_pin = _normalize_pin(self.usuario_form_pin)
        es_edicion = self.usuario_form_id > 0

        if not es_edicion:
            with self._tenant_session_from(food) as session:
                total_usuarios = len(session.exec(
                    select(UsuarioFood).where(
                        UsuarioFood.company_id == company_id,
                        UsuarioFood.activo.is_(True),
                    )
                ).all())
            msg_limite = check_limite_usuarios(food.empresa_plan, total_usuarios, food.empresa_max_usuarios)
            if msg_limite:
                return rx.toast.error(msg_limite, duration=5000)

        if not es_edicion:
            if len(nuevo_pin) < 4:
                return rx.toast.error("El PIN debe tener al menos 4 dígitos.")
        else:
            if self.usuario_form_pin and len(nuevo_pin) < 4:
                return rx.toast.error("El nuevo PIN debe tener al menos 4 dígitos.")

        if self.usuario_form_pin:
            pin_confirm = _normalize_pin(self.usuario_form_pin_confirm)
            if nuevo_pin != pin_confirm:
                return rx.toast.error("Los PINs no coinciden.")

        with self._tenant_session_from(food) as session:
            otros = session.exec(
                select(UsuarioFood).where(
                    UsuarioFood.company_id == company_id,
                    UsuarioFood.id != self.usuario_form_id,
                )
            ).all()
            if es_edicion:
                u = session.get(UsuarioFood, self.usuario_form_id)
                if u is None or u.company_id != company_id:
                    return rx.toast.error("Usuario no encontrado.")
                if nuevo_pin:
                    conflicto = next((o for o in otros if _verify_pin(nuevo_pin, o.pin)), None)
                    if conflicto:
                        return rx.toast.error(f"El PIN {nuevo_pin} ya lo usa {conflicto.nombre}.")
                    u.pin = _hash_pin(nuevo_pin)
                u.nombre = nombre
                u.rol = rol
                u.activo = self.usuario_form_activo
                u.perm_descuento = self.usuario_form_perm_descuento
                u.perm_anular = self.usuario_form_perm_anular
                u.perm_reportes = self.usuario_form_perm_reportes
                u.perm_turno = self.usuario_form_perm_turno
                u.perm_inventario = self.usuario_form_perm_inventario
                u.perm_costos = self.usuario_form_perm_costos
                u.perm_reimprimir = self.usuario_form_perm_reimprimir
                u.perm_corregir = self.usuario_form_perm_corregir
                u.acceso_mozos = self.usuario_form_acceso_mozos
                u.acceso_caja = self.usuario_form_acceso_caja
                u.acceso_cocina = self.usuario_form_acceso_cocina
                u.acceso_mostrador = self.usuario_form_acceso_mostrador
                u.updated_at = _utcnow()
                session.add(u)
                session.commit()
                _toast_msg = f"Usuario '{nombre}' actualizado."
            else:
                conflicto = next((o for o in otros if _verify_pin(nuevo_pin, o.pin)), None)
                if conflicto:
                    return rx.toast.error(f"El PIN {nuevo_pin} ya lo usa {conflicto.nombre}.")
                u = UsuarioFood(
                    company_id=company_id,
                    nombre=nombre,
                    pin=_hash_pin(nuevo_pin),
                    rol=rol,
                    activo=True,
                    perm_descuento=self.usuario_form_perm_descuento,
                    perm_anular=self.usuario_form_perm_anular,
                    perm_reportes=self.usuario_form_perm_reportes,
                    perm_turno=self.usuario_form_perm_turno,
                    perm_inventario=self.usuario_form_perm_inventario,
                    perm_costos=self.usuario_form_perm_costos,
                    perm_reimprimir=self.usuario_form_perm_reimprimir,
                    perm_corregir=self.usuario_form_perm_corregir,
                    acceso_mozos=self.usuario_form_acceso_mozos,
                    acceso_caja=self.usuario_form_acceso_caja,
                    acceso_cocina=self.usuario_form_acceso_cocina,
                    acceso_mostrador=self.usuario_form_acceso_mostrador,
                )
                session.add(u)
                session.commit()
                _toast_msg = f"Usuario '{nombre}' creado."

        self._limpiar_usuario_form()
        self._do_cargar_usuarios_admin(food)
        return rx.toast.success(_toast_msg)

    async def toggle_usuario_activo(self, user_id: int) -> None:
        food = await self._food()
        company_id = self._company_id_from(food)
        mi_id = food.usuario_actual.id if food.usuario_actual else 0
        if user_id == mi_id:
            return rx.toast.error("No puedes desactivarte a ti mismo.")
        with self._tenant_session_from(food) as session:
            u = session.get(UsuarioFood, user_id)
            if u is None or u.company_id != company_id:
                return rx.toast.error("Usuario no encontrado.")
            if u.activo and u.rol == RolUsuario.ADMIN.value:
                admins_activos = session.exec(
                    select(UsuarioFood).where(
                        UsuarioFood.company_id == company_id,
                        UsuarioFood.rol == RolUsuario.ADMIN.value,
                        UsuarioFood.activo.is_(True),
                    )
                ).all()
                if len(admins_activos) <= 1:
                    return rx.toast.error("No puedes desactivar al último administrador.")
            u.activo = not u.activo
            u.updated_at = _utcnow()
            session.add(u)
            session.commit()
            accion = "activado" if u.activo else "desactivado"
            _toast_msg = f"Usuario '{u.nombre}' {accion}."
        self._do_cargar_usuarios_admin(food)
        return rx.toast.success(_toast_msg)

    def cancelar_usuario_form(self) -> None:
        self._limpiar_usuario_form()

    async def on_load_usuarios(self):
        """Handler on_load de la pagina /usuarios."""
        food = await self._food()
        if food.usuario_actual is None:
            return rx.redirect("/login", replace=True)
        if food.usuario_actual.rol not in ROLE_ALLOWED_ROUTES["usuarios"]:
            return [
                rx.window_alert("No tienes permiso para este módulo."),
                rx.redirect(food.usuario_home_route, replace=True),
            ]
        self._do_cargar_usuarios_admin(food)
        self._limpiar_usuario_form()
        return None
