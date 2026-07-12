"""Tests de integración del flujo confirmar_cobro.

Simula las operaciones DB que confirmar_cobro orquesta, sin depender del
runtime de Reflex. Cubre: cobro simple de mesa, fiado, split de pagos,
y combos con descuento de stock.
"""
from __future__ import annotations

import json
from decimal import Decimal

import pytest
from sqlmodel import Session, SQLModel, create_engine, select

import app.models  # noqa: F401
from app.models.food import (
    Categoria,
    Cliente,
    CuentaCorriente,
    DetallePedido,
    EstadoMesa,
    EstadoPedido,
    Insumo,
    Mesa,
    MovimientoCuenta,
    MovimientoInsumo,
    PagoPedido,
    Pedido,
    Producto,
    RecetaItem,
)
from app.services.pago_service import (
    metodo_pago_resumen,
    registrar_pagos_pedido,
    validar_pagos,
)
from app.states.caja_turno_mixin import abrir_turno_caja
from app.states.food_state import _descontar_stock_por_pedido
from app.utils.tenant import (
    _refresh_tenant_models,
    register_tenant_listeners,
    set_tenant_context,
    tenant_context,
)

COMPANY = 1


@pytest.fixture(autouse=True)
def _clean_tenant_context():
    yield
    set_tenant_context(None, None)


@pytest.fixture()
def db_engine():
    register_tenant_listeners()
    _refresh_tenant_models()
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    return engine


def _utcnow():
    from tuwayki_core.utils.timezone import utc_now_naive
    return utc_now_naive()


def _cobrar_pedido(
    session,
    pedido: Pedido,
    turno_id: int,
    pagos_lista: list[tuple[str, Decimal]],
    *,
    mesa: Mesa | None = None,
    descuento: Decimal = Decimal("0.00"),
    propina: Decimal = Decimal("0.00"),
    recargo: Decimal = Decimal("0.00"),
    cliente_id: int = 0,
):
    """Replica la lógica DB de confirmar_cobro (sin Reflex State)."""
    total_base = Decimal(str(pedido.total))
    total_final = max(total_base - descuento + propina + recargo, Decimal("0.00"))

    resultado_pagos = validar_pagos(total_final, pagos_lista) if pagos_lista else None
    total_fiado = resultado_pagos.total_fiado if resultado_pagos else Decimal("0.00")

    now = _utcnow()
    pedido.pagado = total_fiado == 0
    pedido.estado = EstadoPedido.COBRADO.value
    pedido.cerrado_en = now
    pedido.updated_at = now
    pedido.metodo_pago = metodo_pago_resumen(pagos_lista)
    pedido.turno_caja_id = turno_id
    pedido.propina = propina
    pedido.descuento = descuento
    pedido.recargo = recargo
    if cliente_id > 0:
        pedido.cliente_id = cliente_id
    session.add(pedido)

    if mesa is not None:
        mesa.estado = EstadoMesa.LIBRE.value
        mesa.updated_at = now
        session.add(mesa)

    _descontar_stock_por_pedido(session, pedido.id or 0, COMPANY)

    if total_fiado > 0 and cliente_id > 0:
        cc = session.exec(
            select(CuentaCorriente).where(
                CuentaCorriente.company_id == COMPANY,
                CuentaCorriente.cliente_id == cliente_id,
            )
        ).first()
        if cc is None:
            cc = CuentaCorriente(
                company_id=COMPANY, cliente_id=cliente_id,
                saldo_deuda=Decimal("0.00"), limite_credito=Decimal("0.00"),
            )
            session.add(cc)
            session.flush()
        cc.saldo_deuda = Decimal(str(cc.saldo_deuda)) + total_fiado
        session.add(cc)
        session.add(MovimientoCuenta(
            company_id=COMPANY, cuenta_id=cc.id or 0,
            pedido_id=pedido.id, tipo="cargo",
            monto=total_fiado,
            descripcion=f"Fiado pedido #{pedido.id}",
        ))

    if resultado_pagos is not None:
        registrar_pagos_pedido(
            session, pedido, turno_id,
            usuario_id=None,
            pagos=pagos_lista,
            resultado=resultado_pagos,
        )

    session.commit()


# ─── Tests ────────────────────────────────────────────────────────────────────


def test_cobro_simple_mesa_efectivo(db_engine):
    """Mesa con 2 items, pago efectivo. Verifica: pedido cobrado, mesa libre,
    stock descontado, pago registrado."""
    with Session(db_engine) as session:
        with tenant_context(COMPANY, None):
            turno = abrir_turno_caja(session, COMPANY, None, Decimal("100.00"))
            cat = Categoria(company_id=COMPANY, nombre="Platos")
            session.add(cat); session.flush()
            prod = Producto(company_id=COMPANY, categoria_id=cat.id, nombre="Lomo",
                            precio=Decimal("35.00"))
            ins = Insumo(company_id=COMPANY, nombre="Lomo fino", unidad="kg",
                         stock_actual=Decimal("10.000"))
            session.add_all([prod, ins]); session.flush()
            session.add(RecetaItem(company_id=COMPANY, producto_id=prod.id,
                                   insumo_id=ins.id, cantidad=Decimal("0.300")))
            mesa = Mesa(company_id=COMPANY, numero=1, estado=EstadoMesa.OCUPADA.value)
            session.add(mesa); session.flush()
            pedido = Pedido(company_id=COMPANY, mesa_id=mesa.id,
                            estado=EstadoPedido.ENVIADO.value, total=Decimal("70.00"))
            session.add(pedido); session.flush()
            session.add(DetallePedido(
                company_id=COMPANY, pedido_id=pedido.id, producto_id=prod.id,
                cantidad=2, precio_unitario=Decimal("35.00"), subtotal=Decimal("70.00"),
            ))
            session.flush()

            _cobrar_pedido(
                session, pedido, turno.id,
                [("efectivo", Decimal("70.00"))],
                mesa=mesa,
            )

            assert pedido.estado == EstadoPedido.COBRADO.value
            assert pedido.pagado is True
            assert pedido.metodo_pago == "efectivo"
            assert mesa.estado == EstadoMesa.LIBRE.value
            assert ins.stock_actual == Decimal("9.400")

            pagos = session.exec(
                select(PagoPedido).where(PagoPedido.pedido_id == pedido.id)
            ).all()
            assert len(pagos) == 1
            assert pagos[0].metodo == "efectivo"


def test_cobro_con_descuento_propina_recargo(db_engine):
    """Verifica que descuento, propina y recargo se registran correctamente."""
    with Session(db_engine) as session:
        with tenant_context(COMPANY, None):
            turno = abrir_turno_caja(session, COMPANY, None, Decimal("0.00"))
            cat = Categoria(company_id=COMPANY, nombre="Platos")
            session.add(cat); session.flush()
            prod = Producto(company_id=COMPANY, categoria_id=cat.id, nombre="Arroz",
                            precio=Decimal("20.00"))
            session.add(prod); session.flush()
            pedido = Pedido(company_id=COMPANY, tipo_pedido="mostrador",
                            estado=EstadoPedido.ENVIADO.value, total=Decimal("40.00"))
            session.add(pedido); session.flush()
            session.add(DetallePedido(
                company_id=COMPANY, pedido_id=pedido.id, producto_id=prod.id,
                cantidad=2, precio_unitario=Decimal("20.00"), subtotal=Decimal("40.00"),
            ))
            session.flush()

            total_final = Decimal("40.00") - Decimal("5.00") + Decimal("3.00") + Decimal("2.00")
            _cobrar_pedido(
                session, pedido, turno.id,
                [("efectivo", total_final)],
                descuento=Decimal("5.00"),
                propina=Decimal("3.00"),
                recargo=Decimal("2.00"),
            )

            assert pedido.descuento == Decimal("5.00")
            assert pedido.propina == Decimal("3.00")
            assert pedido.recargo == Decimal("2.00")
            assert pedido.pagado is True


def test_cobro_fiado_registra_deuda(db_engine):
    """Pago fiado completo: pedido.pagado=False, CC con saldo_deuda, movimiento cargo."""
    with Session(db_engine) as session:
        with tenant_context(COMPANY, None):
            turno = abrir_turno_caja(session, COMPANY, None, Decimal("0.00"))
            cat = Categoria(company_id=COMPANY, nombre="Platos")
            session.add(cat); session.flush()
            prod = Producto(company_id=COMPANY, categoria_id=cat.id, nombre="Pollo",
                            precio=Decimal("25.00"))
            session.add(prod); session.flush()
            cliente = Cliente(company_id=COMPANY, nombre="Juan Pérez")
            session.add(cliente); session.flush()
            pedido = Pedido(company_id=COMPANY, mesa_id=None,
                            estado=EstadoPedido.ENVIADO.value, total=Decimal("50.00"))
            session.add(pedido); session.flush()
            session.add(DetallePedido(
                company_id=COMPANY, pedido_id=pedido.id, producto_id=prod.id,
                cantidad=2, precio_unitario=Decimal("25.00"), subtotal=Decimal("50.00"),
            ))
            session.flush()

            _cobrar_pedido(
                session, pedido, turno.id,
                [("fiado", Decimal("50.00"))],
                cliente_id=cliente.id,
            )

            assert pedido.pagado is False
            assert pedido.metodo_pago == "fiado"
            assert pedido.cliente_id == cliente.id

            cc = session.exec(
                select(CuentaCorriente).where(
                    CuentaCorriente.cliente_id == cliente.id,
                )
            ).first()
            assert cc is not None
            assert cc.saldo_deuda == Decimal("50.00")

            mov = session.exec(
                select(MovimientoCuenta).where(
                    MovimientoCuenta.cuenta_id == cc.id,
                )
            ).first()
            assert mov is not None
            assert mov.tipo == "cargo"
            assert mov.monto == Decimal("50.00")


def test_cobro_split_efectivo_tarjeta(db_engine):
    """Pago dividido: parte efectivo, parte tarjeta. Verifica 2 pagos registrados."""
    with Session(db_engine) as session:
        with tenant_context(COMPANY, None):
            turno = abrir_turno_caja(session, COMPANY, None, Decimal("0.00"))
            cat = Categoria(company_id=COMPANY, nombre="Platos")
            session.add(cat); session.flush()
            prod = Producto(company_id=COMPANY, categoria_id=cat.id, nombre="Ceviche",
                            precio=Decimal("30.00"))
            session.add(prod); session.flush()
            mesa = Mesa(company_id=COMPANY, numero=3, estado=EstadoMesa.OCUPADA.value)
            session.add(mesa); session.flush()
            pedido = Pedido(company_id=COMPANY, mesa_id=mesa.id,
                            estado=EstadoPedido.ENVIADO.value, total=Decimal("90.00"))
            session.add(pedido); session.flush()
            session.add(DetallePedido(
                company_id=COMPANY, pedido_id=pedido.id, producto_id=prod.id,
                cantidad=3, precio_unitario=Decimal("30.00"), subtotal=Decimal("90.00"),
            ))
            session.flush()

            _cobrar_pedido(
                session, pedido, turno.id,
                [("efectivo", Decimal("50.00")), ("tarjeta", Decimal("40.00"))],
                mesa=mesa,
            )

            assert pedido.pagado is True
            assert pedido.metodo_pago == "mixto"

            pagos = session.exec(
                select(PagoPedido).where(PagoPedido.pedido_id == pedido.id)
            ).all()
            assert len(pagos) == 2
            metodos = {p.metodo for p in pagos}
            assert metodos == {"efectivo", "tarjeta"}


def test_cobro_split_parcial_fiado(db_engine):
    """Split: efectivo + fiado. pedido.pagado=False, CC actualizada."""
    with Session(db_engine) as session:
        with tenant_context(COMPANY, None):
            turno = abrir_turno_caja(session, COMPANY, None, Decimal("0.00"))
            cat = Categoria(company_id=COMPANY, nombre="Platos")
            session.add(cat); session.flush()
            prod = Producto(company_id=COMPANY, categoria_id=cat.id, nombre="Parrilla",
                            precio=Decimal("80.00"))
            session.add(prod); session.flush()
            cliente = Cliente(company_id=COMPANY, nombre="María López")
            session.add(cliente); session.flush()
            pedido = Pedido(company_id=COMPANY,
                            estado=EstadoPedido.ENVIADO.value, total=Decimal("80.00"))
            session.add(pedido); session.flush()
            session.add(DetallePedido(
                company_id=COMPANY, pedido_id=pedido.id, producto_id=prod.id,
                cantidad=1, precio_unitario=Decimal("80.00"), subtotal=Decimal("80.00"),
            ))
            session.flush()

            _cobrar_pedido(
                session, pedido, turno.id,
                [("efectivo", Decimal("50.00")), ("fiado", Decimal("30.00"))],
                cliente_id=cliente.id,
            )

            assert pedido.pagado is False
            assert pedido.metodo_pago == "mixto"

            cc = session.exec(
                select(CuentaCorriente).where(
                    CuentaCorriente.cliente_id == cliente.id,
                )
            ).first()
            assert cc is not None
            assert cc.saldo_deuda == Decimal("30.00")


def test_cobro_combo_descuenta_stock_sub_items(db_engine):
    """Combo con recetas en sub-productos: stock se descuenta de los insumos."""
    with Session(db_engine) as session:
        with tenant_context(COMPANY, None):
            turno = abrir_turno_caja(session, COMPANY, None, Decimal("0.00"))
            cat = Categoria(company_id=COMPANY, nombre="Combos")
            session.add(cat); session.flush()

            combo = Producto(company_id=COMPANY, categoria_id=cat.id,
                             nombre="Combo Familiar", precio=Decimal("60.00"))
            burger = Producto(company_id=COMPANY, categoria_id=cat.id,
                              nombre="Hamburguesa", precio=Decimal("20.00"))
            papas = Producto(company_id=COMPANY, categoria_id=cat.id,
                             nombre="Papas fritas", precio=Decimal("10.00"))
            ins_carne = Insumo(company_id=COMPANY, nombre="Carne", unidad="kg",
                               stock_actual=Decimal("5.000"))
            ins_papa = Insumo(company_id=COMPANY, nombre="Papa", unidad="kg",
                              stock_actual=Decimal("15.000"))
            session.add_all([combo, burger, papas, ins_carne, ins_papa])
            session.flush()

            session.add(RecetaItem(company_id=COMPANY, producto_id=burger.id,
                                   insumo_id=ins_carne.id, cantidad=Decimal("0.200")))
            session.add(RecetaItem(company_id=COMPANY, producto_id=papas.id,
                                   insumo_id=ins_papa.id, cantidad=Decimal("0.400")))
            session.flush()

            mesa = Mesa(company_id=COMPANY, numero=5, estado=EstadoMesa.OCUPADA.value)
            session.add(mesa); session.flush()
            pedido = Pedido(company_id=COMPANY, mesa_id=mesa.id,
                            estado=EstadoPedido.ENVIADO.value, total=Decimal("60.00"))
            session.add(pedido); session.flush()

            combo_items = json.dumps([
                {"producto_id": burger.id, "cantidad": 2},
                {"producto_id": papas.id, "cantidad": 1},
            ])
            session.add(DetallePedido(
                company_id=COMPANY, pedido_id=pedido.id, producto_id=combo.id,
                cantidad=1, precio_unitario=Decimal("60.00"), subtotal=Decimal("60.00"),
                combo_items_json=combo_items,
            ))
            session.flush()

            _cobrar_pedido(
                session, pedido, turno.id,
                [("efectivo", Decimal("60.00"))],
                mesa=mesa,
            )

            assert ins_carne.stock_actual == Decimal("4.600")
            assert ins_papa.stock_actual == Decimal("14.600")

            movs = session.exec(select(MovimientoInsumo)).all()
            assert len(movs) == 2


def test_cobro_pedido_mixto_simple_combo_con_fiado(db_engine):
    """Escenario completo: producto simple + combo en mismo pedido, con split
    efectivo + fiado. Verifica stock, pagos, CC, y estado de pedido."""
    with Session(db_engine) as session:
        with tenant_context(COMPANY, None):
            turno = abrir_turno_caja(session, COMPANY, None, Decimal("50.00"))
            cat = Categoria(company_id=COMPANY, nombre="Carta")
            session.add(cat); session.flush()

            arroz = Producto(company_id=COMPANY, categoria_id=cat.id,
                             nombre="Arroz con pollo", precio=Decimal("25.00"))
            combo = Producto(company_id=COMPANY, categoria_id=cat.id,
                             nombre="Combo duo", precio=Decimal("45.00"))
            ensalada = Producto(company_id=COMPANY, categoria_id=cat.id,
                                nombre="Ensalada", precio=Decimal("12.00"))
            ins_arroz = Insumo(company_id=COMPANY, nombre="Arroz", unidad="kg",
                               stock_actual=Decimal("20.000"))
            ins_lechuga = Insumo(company_id=COMPANY, nombre="Lechuga", unidad="kg",
                                 stock_actual=Decimal("5.000"))
            session.add_all([arroz, combo, ensalada, ins_arroz, ins_lechuga])
            session.flush()

            session.add(RecetaItem(company_id=COMPANY, producto_id=arroz.id,
                                   insumo_id=ins_arroz.id, cantidad=Decimal("0.350")))
            session.add(RecetaItem(company_id=COMPANY, producto_id=ensalada.id,
                                   insumo_id=ins_lechuga.id, cantidad=Decimal("0.100")))
            session.flush()

            cliente = Cliente(company_id=COMPANY, nombre="Carlos Ruiz")
            session.add(cliente); session.flush()

            mesa = Mesa(company_id=COMPANY, numero=7, estado=EstadoMesa.OCUPADA.value)
            session.add(mesa); session.flush()

            total = Decimal("25.00") * 2 + Decimal("45.00")
            pedido = Pedido(company_id=COMPANY, mesa_id=mesa.id,
                            estado=EstadoPedido.ENVIADO.value, total=total)
            session.add(pedido); session.flush()

            session.add(DetallePedido(
                company_id=COMPANY, pedido_id=pedido.id, producto_id=arroz.id,
                cantidad=2, precio_unitario=Decimal("25.00"), subtotal=Decimal("50.00"),
            ))
            combo_items = json.dumps([
                {"producto_id": ensalada.id, "cantidad": 3},
            ])
            session.add(DetallePedido(
                company_id=COMPANY, pedido_id=pedido.id, producto_id=combo.id,
                cantidad=1, precio_unitario=Decimal("45.00"), subtotal=Decimal("45.00"),
                combo_items_json=combo_items,
            ))
            session.flush()

            _cobrar_pedido(
                session, pedido, turno.id,
                [("efectivo", Decimal("55.00")), ("fiado", Decimal("40.00"))],
                mesa=mesa,
                cliente_id=cliente.id,
            )

            assert pedido.estado == EstadoPedido.COBRADO.value
            assert pedido.pagado is False
            assert pedido.turno_caja_id == turno.id
            assert mesa.estado == EstadoMesa.LIBRE.value

            assert ins_arroz.stock_actual == Decimal("19.300")
            assert ins_lechuga.stock_actual == Decimal("4.700")

            pagos = session.exec(
                select(PagoPedido).where(PagoPedido.pedido_id == pedido.id)
            ).all()
            assert len(pagos) == 2

            cc = session.exec(
                select(CuentaCorriente).where(
                    CuentaCorriente.cliente_id == cliente.id,
                )
            ).first()
            assert cc is not None
            assert cc.saldo_deuda == Decimal("40.00")
