"""Métodos de pago configurables por empresa.

Fuente única de verdad para: qué métodos existen, cómo se muestran y en qué
balde del cierre caen (vía :class:`TipoMetodoPago`). Réplica adaptada del
configurador de métodos de pago de Sistema-de-Ventas.

Los defaults están pensados para Perú (Efectivo, Yape, Plin, Tarjeta,
Transferencia). ``qr`` se siembra INACTIVO: no se ofrece como botón nuevo, pero
resuelve el nombre/tipo de los pagos históricos guardados como "qr".
"""

from __future__ import annotations

from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from app.models.food import MetodoPagoConfig, TipoMetodoPago

# Códigos base siempre aceptados aunque falte configuración (datos legacy).
METODOS_PAGO_BASE_SET: set[str] = {"efectivo", "tarjeta", "qr", "fiado"}

# (codigo, nombre, tipo, icono, permite_vuelto, activo, orden)
DEFAULT_METODOS: list[tuple[str, str, str, str, bool, bool, int]] = [
    ("efectivo", "Efectivo", TipoMetodoPago.EFECTIVO.value, "💵", True, True, 1),
    ("yape", "Yape", TipoMetodoPago.DIGITAL.value, "📱", False, True, 2),
    ("plin", "Plin", TipoMetodoPago.DIGITAL.value, "📲", False, True, 3),
    ("tarjeta", "Tarjeta", TipoMetodoPago.TARJETA.value, "💳", False, True, 4),
    ("transferencia", "Transferencia", TipoMetodoPago.DIGITAL.value, "🏦", False, True, 5),
    ("fiado", "Fiado / Cuenta", TipoMetodoPago.FIADO.value, "📒", False, True, 6),
    # Histórico: pagos ya guardados como "qr" (antes de los métodos configurables).
    ("qr", "QR", TipoMetodoPago.DIGITAL.value, "🔳", False, False, 99),
]


def sembrar_defaults(session, company_id: int) -> list[MetodoPagoConfig]:
    """Crea los métodos por defecto para una empresa que aún no tiene ninguno.

    Idempotente: solo inserta los ``codigo`` que falten, nunca pisa lo existente
    (así respeta ediciones del usuario). Devuelve las filas creadas.

    **Persiste con commit** (no solo flush): antes se sembraba con ``flush()`` y,
    como el ``get_session()`` que envuelve las lecturas cierra sin commit, los
    defaults se hacían rollback y NUNCA quedaban en la tabla. Efecto: la Caja los
    mostraba (se re-sembraban en memoria cada carga) pero Configuración salía
    vacía y editar/activar/eliminar no hacía nada (el id no existía en la DB). El
    commit solo dispara cuando la empresa tenía 0 métodos (primera carga), así que
    no interfiere con transacciones de cobro/cierre (ahí ya existen métodos).
    """
    existentes = {
        m.codigo
        for m in session.exec(
            select(MetodoPagoConfig).where(
                MetodoPagoConfig.company_id == company_id
            )
        ).all()
    }
    creados: list[MetodoPagoConfig] = []
    for codigo, nombre, tipo, icono, vuelto, activo, orden in DEFAULT_METODOS:
        if codigo in existentes:
            continue
        fila = MetodoPagoConfig(
            company_id=company_id,
            codigo=codigo,
            nombre=nombre,
            tipo=tipo,
            icono=icono,
            permite_vuelto=vuelto,
            activo=activo,
            orden=orden,
        )
        session.add(fila)
        creados.append(fila)
    if creados:
        try:
            session.commit()
        except IntegrityError:
            # Carrera: otro request sembró primero (viola el único
            # (company_id, codigo)). Descartamos; el caller re-consulta y ve
            # los métodos ya persistidos por el otro request.
            session.rollback()
            return []
    return creados


def obtener_metodos(
    session, company_id: int, solo_activos: bool = False
) -> list[MetodoPagoConfig]:
    """Métodos de la empresa ordenados; siembra los defaults si no hay ninguno."""
    metodos = session.exec(
        select(MetodoPagoConfig)
        .where(MetodoPagoConfig.company_id == company_id)
        .order_by(MetodoPagoConfig.orden, MetodoPagoConfig.id)
    ).all()
    if not metodos:
        sembrar_defaults(session, company_id)
        metodos = session.exec(
            select(MetodoPagoConfig)
            .where(MetodoPagoConfig.company_id == company_id)
            .order_by(MetodoPagoConfig.orden, MetodoPagoConfig.id)
        ).all()
    if solo_activos:
        return [m for m in metodos if m.activo]
    return list(metodos)


def mapa_tipos(session, company_id: int) -> dict[str, str]:
    """``{codigo: tipo}`` para clasificar pagos en el cierre.

    Incluye siempre los códigos legacy con un tipo razonable, por si un pago
    guardado apunta a un código que ya no está configurado.
    """
    mapa = {
        "efectivo": TipoMetodoPago.EFECTIVO.value,
        "tarjeta": TipoMetodoPago.TARJETA.value,
        "qr": TipoMetodoPago.DIGITAL.value,
        "fiado": TipoMetodoPago.FIADO.value,
    }
    for m in obtener_metodos(session, company_id):
        mapa[m.codigo] = m.tipo
    return mapa


def validos_y_efectivos(session, company_id: int) -> tuple[set[str], set[str]]:
    """``(codigos_validos, codigos_efectivo)`` para pasar a ``validar_pagos``.

    Válidos = métodos activos + fiado (siempre) + base legacy. Efectivo = los de
    tipo EFECTIVO (o ``{"efectivo"}`` como piso).
    """
    metodos = obtener_metodos(session, company_id)
    validos = {m.codigo for m in metodos if m.activo} | METODOS_PAGO_BASE_SET
    efectivos = {
        m.codigo for m in metodos if m.tipo == TipoMetodoPago.EFECTIVO.value
    } or {"efectivo"}
    return validos, efectivos


def mapa_nombres(session, company_id: int) -> dict[str, str]:
    """``{codigo: nombre visible}`` para tickets y reportes."""
    nombres = {
        "efectivo": "Efectivo",
        "tarjeta": "Tarjeta",
        "qr": "QR",
        "fiado": "Fiado / Cuenta",
        "mixto": "Mixto",
    }
    for m in obtener_metodos(session, company_id):
        nombres[m.codigo] = m.nombre
    return nombres
