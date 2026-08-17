"""CRUD de métodos de pago configurables (sección Configuración).

Permite crear/editar/activar/eliminar los métodos que la caja ofrece al cobrar.
Algunos códigos son de sistema (efectivo, fiado, qr): se pueden renombrar o
desactivar, pero no eliminar ni cambiarles el código/tipo, porque la lógica de
cierre y cuenta corriente depende de ellos.
"""

from __future__ import annotations

import re

import reflex as rx
from pydantic import BaseModel
from sqlmodel import select

from app.models.food import MetodoPagoConfig, TipoMetodoPago
from app.services.metodos_pago_service import obtener_metodos

# Códigos que no se pueden eliminar ni recodificar (los usa la lógica de negocio).
CODIGOS_SISTEMA = {"efectivo", "fiado", "qr"}

# Opciones de tipo ofrecidas en el formulario (fiado queda reservado al sistema).
TIPOS_METODO = [
    (TipoMetodoPago.EFECTIVO.value, "Efectivo (entra al cajón)"),
    (TipoMetodoPago.TARJETA.value, "Tarjeta"),
    (TipoMetodoPago.DIGITAL.value, "Digital (Yape / Plin / QR)"),
    (TipoMetodoPago.OTRO.value, "Otro"),
]
_TIPO_LABEL = {
    TipoMetodoPago.EFECTIVO.value: "Efectivo",
    TipoMetodoPago.TARJETA.value: "Tarjeta",
    TipoMetodoPago.DIGITAL.value: "Digital",
    TipoMetodoPago.FIADO.value: "Fiado",
    TipoMetodoPago.OTRO.value: "Otro",
}


def _slug(texto: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", (texto or "").strip().lower()).strip("_")
    return s[:24] or "metodo"


class MetodoPagoAdminView(BaseModel):
    id: int
    codigo: str
    nombre: str
    tipo: str
    tipo_label: str
    icono: str
    activo: bool
    es_sistema: bool


class MetodosPagoMixin(rx.State, mixin=True):
    """Estado del configurador de métodos de pago."""

    metodos_admin: list[MetodoPagoAdminView] = []

    # Formulario
    metodo_form_id: int = 0
    metodo_form_codigo: str = ""
    metodo_form_nombre: str = ""
    metodo_form_tipo: str = TipoMetodoPago.DIGITAL.value
    metodo_form_icono: str = ""
    metodo_form_error: str = ""

    @rx.var
    def metodo_form_es_edicion(self) -> bool:
        return self.metodo_form_id > 0

    @rx.var
    def metodo_form_es_sistema(self) -> bool:
        return self.metodo_form_codigo in CODIGOS_SISTEMA

    def cargar_metodos_pago_admin(self) -> None:
        with self._tenant_session() as session:
            metodos = obtener_metodos(session, self._company_id())
            self.metodos_admin = [
                MetodoPagoAdminView(
                    id=m.id or 0,
                    codigo=m.codigo,
                    nombre=m.nombre,
                    tipo=m.tipo,
                    tipo_label=_TIPO_LABEL.get(m.tipo, m.tipo),
                    icono=m.icono or "💳",
                    activo=m.activo,
                    es_sistema=(m.codigo in CODIGOS_SISTEMA),
                )
                for m in metodos
            ]

    # ── Formulario ──────────────────────────────────────────────────────────
    def set_metodo_form_nombre(self, v: str) -> None:
        self.metodo_form_nombre = v

    def set_metodo_form_tipo(self, v: str) -> None:
        self.metodo_form_tipo = v

    def set_metodo_form_icono(self, v: str) -> None:
        self.metodo_form_icono = v[:8]

    def nuevo_metodo_form(self) -> None:
        self.metodo_form_id = 0
        self.metodo_form_codigo = ""
        self.metodo_form_nombre = ""
        self.metodo_form_tipo = TipoMetodoPago.DIGITAL.value
        self.metodo_form_icono = ""
        self.metodo_form_error = ""

    def cancelar_metodo_form(self) -> None:
        self.nuevo_metodo_form()

    def editar_metodo(self, metodo_id: int) -> None:
        with self._tenant_session() as session:
            m = session.get(MetodoPagoConfig, metodo_id)
            if m is None or m.company_id != self._company_id():
                return
            self.metodo_form_id = m.id or 0
            self.metodo_form_codigo = m.codigo
            self.metodo_form_nombre = m.nombre
            self.metodo_form_tipo = m.tipo
            self.metodo_form_icono = m.icono or ""
            self.metodo_form_error = ""

    def guardar_metodo(self):
        nombre = self.metodo_form_nombre.strip()
        if not nombre:
            self.metodo_form_error = "El nombre es obligatorio."
            return
        tipo = self.metodo_form_tipo or TipoMetodoPago.DIGITAL.value
        icono = self.metodo_form_icono.strip() or None
        with self._tenant_session() as session:
            if self.metodo_form_id > 0:
                m = session.get(MetodoPagoConfig, self.metodo_form_id)
                if m is None or m.company_id != self._company_id():
                    self.metodo_form_error = "Método no encontrado."
                    return
                m.nombre = nombre[:40]
                m.icono = icono
                # Los códigos de sistema conservan su tipo (la lógica depende de él).
                if m.codigo not in CODIGOS_SISTEMA:
                    m.tipo = tipo
                session.add(m)
                session.commit()
            else:
                codigo = _slug(nombre)
                existentes = {
                    r.codigo
                    for r in session.exec(
                        select(MetodoPagoConfig).where(
                            MetodoPagoConfig.company_id == self._company_id()
                        )
                    ).all()
                }
                if codigo in existentes:
                    self.metodo_form_error = (
                        f"Ya existe un método con el código '{codigo}'."
                    )
                    return
                orden = 10 + len(existentes)
                session.add(
                    MetodoPagoConfig(
                        company_id=self._company_id(),
                        codigo=codigo,
                        nombre=nombre[:40],
                        tipo=tipo,
                        icono=icono,
                        permite_vuelto=(tipo == TipoMetodoPago.EFECTIVO.value),
                        activo=True,
                        orden=orden,
                    )
                )
                session.commit()
        self.nuevo_metodo_form()
        self.cargar_metodos_pago_admin()
        return rx.toast.success("Método de pago guardado.")

    def toggle_metodo_activo(self, metodo_id: int):
        with self._tenant_session() as session:
            m = session.get(MetodoPagoConfig, metodo_id)
            if m is None or m.company_id != self._company_id():
                return
            m.activo = not m.activo
            session.add(m)
            session.commit()
        self.cargar_metodos_pago_admin()

    def eliminar_metodo(self, metodo_id: int):
        with self._tenant_session() as session:
            m = session.get(MetodoPagoConfig, metodo_id)
            if m is None or m.company_id != self._company_id():
                return
            if m.codigo in CODIGOS_SISTEMA:
                return rx.toast.error(
                    "Este método es del sistema: puedes desactivarlo, pero no eliminarlo."
                )
            session.delete(m)
            session.commit()
        self.cargar_metodos_pago_admin()
        return rx.toast.success("Método de pago eliminado.")
