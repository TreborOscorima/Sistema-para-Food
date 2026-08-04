"""Modelos SQLModel de TUWAYKIFOOD (multi-tenant, MySQL)."""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import Column, Date, JSON, Numeric, Text, UniqueConstraint, event
from sqlmodel import Field, Relationship, SQLModel
from tuwayki_core.utils.timezone import utc_now_naive


class EstadoMesa(str, Enum):
    LIBRE = "libre"
    OCUPADA = "ocupada"
    ESPERANDO_CUENTA = "esperando_cuenta"


class EstadoPedido(str, Enum):
    BORRADOR = "borrador"
    ENVIADO = "enviado"
    EN_PREPARACION = "en_preparacion"
    LISTO = "listo"
    COBRADO = "cobrado"
    CANCELADO = "cancelado"


class EstadoProduccion(str, Enum):
    PENDIENTE = "pendiente"
    EN_PREPARACION = "en_preparacion"
    LISTO_PARA_ENTREGAR = "listo_para_entregar"
    ENTREGADO_AL_CLIENTE = "entregado_al_cliente"


class TipoPedido(str, Enum):
    MESA = "Mesa"
    MOSTRADOR = "Mostrador"
    DELIVERY = "Delivery"


class EstadoDelivery(str, Enum):
    PENDIENTE = "pendiente"
    EN_CAMINO = "en_camino"
    ENTREGADO = "entregado"
    CANCELADO = "cancelado"


class RolUsuario(str, Enum):
    MOZO = "Mozo"
    CAJA = "Caja"
    COCINA = "Cocina"
    ADMIN = "Admin"
    REPARTIDOR = "Repartidor"


class EstacionCocina(str, Enum):
    COCINA = "cocina"
    BARRA = "barra"


class TipoPromocion(str, Enum):
    PORCENTAJE = "porcentaje"
    MONTO_FIJO = "monto_fijo"
    HAPPY_HOUR = "happy_hour"
    DOSXUNO = "dosxuno"  # 2x1 sobre un producto o categoría


class EstadoTurnoCaja(str, Enum):
    ABIERTO = "abierto"
    CERRADO = "cerrado"


class TipoMovimientoInsumo(str, Enum):
    ENTRADA = "entrada"          # compra / reposición de mercadería
    CONSUMO = "consumo"          # descuento automático por venta (receta)
    MERMA = "merma"              # pérdida: vencido, dañado, plato devuelto
    AJUSTE = "ajuste"            # conteo físico (diferencia +/-)
    REPOSICION = "reposicion"    # reverso automático por anulación de venta


class TipoMovimientoCaja(str, Enum):
    INGRESO = "ingreso"
    EGRESO = "egreso"


class EstadoReserva(str, Enum):
    PENDIENTE = "pendiente"
    CONFIRMADA = "confirmada"
    SENTADA = "sentada"
    CANCELADA = "cancelada"
    NO_SHOW = "no_show"


class TimestampedModel(SQLModel):
    created_at: datetime = Field(default_factory=utc_now_naive, nullable=False)
    updated_at: datetime = Field(default_factory=utc_now_naive, nullable=False)


class Sucursal(TimestampedModel, table=True):
    """Sucursal / local de un restaurante. Retrocompat: tablas operativas
    usan sucursal_id=NULL cuando la empresa opera en modo single-location."""

    __tablename__ = "food_sucursales"
    __table_args__ = (
        UniqueConstraint("company_id", "nombre", name="uq_food_sucursales_company_nombre"),
    )

    id: int | None = Field(default=None, primary_key=True)
    company_id: int = Field(index=True, nullable=False)
    nombre: str = Field(max_length=120, nullable=False)
    direccion: str = Field(default="", max_length=200, nullable=False)
    telefono: str = Field(default="", max_length=40, nullable=False)
    activa: bool = Field(default=True, nullable=False)
    es_principal: bool = Field(default=False, nullable=False)


class UsuarioFood(TimestampedModel, table=True):
    """Usuario operativo del restaurante, autenticado por PIN + company_id."""

    __tablename__ = "food_usuarios"
    id: int | None = Field(default=None, primary_key=True)
    company_id: int = Field(index=True, nullable=False)
    sucursal_id: int | None = Field(default=None, foreign_key="food_sucursales.id", index=True)
    nombre: str = Field(max_length=120, nullable=False)
    pin: str = Field(max_length=72, nullable=False)
    rol: str = Field(index=True, max_length=32, nullable=False)
    activo: bool = Field(default=True, nullable=False)
    perm_descuento: bool = Field(default=True, nullable=False)
    perm_anular: bool = Field(default=False, nullable=False)
    perm_reportes: bool = Field(default=False, nullable=False)
    perm_turno: bool = Field(default=False, nullable=False)
    perm_inventario: bool = Field(default=False, nullable=False)
    perm_costos: bool = Field(default=False, nullable=False)
    perm_reimprimir: bool = Field(default=False, nullable=False)
    acceso_mozos: bool = Field(default=False, nullable=False)
    acceso_caja: bool = Field(default=False, nullable=False)
    acceso_cocina: bool = Field(default=False, nullable=False)
    acceso_mostrador: bool = Field(default=False, nullable=False)


class Mesa(TimestampedModel, table=True):
    """Mesa física del salón, scoped por empresa."""

    __tablename__ = "food_mesas"
    __table_args__ = (
        UniqueConstraint("company_id", "numero", name="uq_food_mesas_company_numero"),
    )

    id: int | None = Field(default=None, primary_key=True)
    company_id: int = Field(index=True, nullable=False)
    sucursal_id: int | None = Field(default=None, foreign_key="food_sucursales.id", index=True)
    numero: int = Field(index=True, nullable=False)
    nombre: str = Field(default="", max_length=80, nullable=False)
    capacidad: int = Field(default=4, ge=1, nullable=False)
    estado: str = Field(
        default=EstadoMesa.LIBRE.value,
        index=True,
        max_length=32,
        nullable=False,
    )
    sector: str = Field(default="Salón", max_length=60, nullable=False)
    activa: bool = Field(default=True, nullable=False)
    qr_token: str | None = Field(default=None, max_length=64, index=True)

    pedidos: list["Pedido"] = Relationship(back_populates="mesa")


class Categoria(TimestampedModel, table=True):
    """Categoría de la carta, scoped por empresa."""

    __tablename__ = "food_categorias"
    __table_args__ = (
        UniqueConstraint("company_id", "nombre", name="uq_food_categorias_company_nombre"),
    )

    id: int | None = Field(default=None, primary_key=True)
    company_id: int = Field(index=True, nullable=False)
    nombre: str = Field(max_length=120, nullable=False)
    descripcion: str | None = Field(default=None, max_length=240)
    orden: int = Field(default=0, nullable=False)
    activa: bool = Field(default=True, nullable=False)
    estacion: str = Field(default=EstacionCocina.COCINA.value, max_length=20, nullable=False)

    productos: list["Producto"] = Relationship(back_populates="categoria")


class Producto(TimestampedModel, table=True):
    """Producto vendible del restaurante, scoped por empresa."""

    __tablename__ = "food_productos"

    id: int | None = Field(default=None, primary_key=True)
    company_id: int = Field(index=True, nullable=False)
    categoria_id: int = Field(foreign_key="food_categorias.id", index=True, nullable=False)
    nombre: str = Field(index=True, max_length=160, nullable=False)
    descripcion: str | None = Field(default=None, max_length=240)
    precio: Decimal = Field(
        default=Decimal("0.00"),
        sa_column=Column(Numeric(10, 2), nullable=False),
    )
    disponible: bool = Field(default=True, nullable=False)
    imagen_url: str | None = Field(default=None, max_length=500)
    emoji: str | None = Field(default=None, max_length=16)
    estacion: str | None = Field(default=None, max_length=20)
    tags: list[str] | None = Field(default=None, sa_column=Column(JSON, nullable=True))
    stock_diario: int | None = Field(default=None, nullable=True)
    stock_diario_alerta: int = Field(default=5, nullable=False)

    categoria: Categoria | None = Relationship(back_populates="productos")
    detalles: list["DetallePedido"] = Relationship(back_populates="producto")
    receta_items: list["RecetaItem"] = Relationship(back_populates="producto")
    producto_grupos: list["ProductoGrupoModificador"] = Relationship(back_populates="producto")


class GrupoModificador(TimestampedModel, table=True):
    """Grupo de opciones (ej: Tamaño, Extras, Término)."""

    __tablename__ = "food_grupo_modificadores"

    id: int | None = Field(default=None, primary_key=True)
    company_id: int = Field(index=True, nullable=False)
    nombre: str = Field(max_length=120, nullable=False)
    min_selecciones: int = Field(default=0, nullable=False)
    max_selecciones: int = Field(default=1, nullable=False)
    activo: bool = Field(default=True, nullable=False)
    orden: int = Field(default=0, nullable=False)

    opciones: list["OpcionModificador"] = Relationship(back_populates="grupo")
    producto_grupos: list["ProductoGrupoModificador"] = Relationship(back_populates="grupo")


class OpcionModificador(TimestampedModel, table=True):
    """Opción dentro de un grupo (ej: Pinta +S/5, Media +S/0)."""

    __tablename__ = "food_opcion_modificadores"

    id: int | None = Field(default=None, primary_key=True)
    company_id: int = Field(index=True, nullable=False)
    grupo_id: int = Field(foreign_key="food_grupo_modificadores.id", index=True, nullable=False)
    nombre: str = Field(max_length=120, nullable=False)
    precio_extra: Decimal = Field(
        default=Decimal("0.00"),
        sa_column=Column(Numeric(10, 2), nullable=False, server_default="0.00"),
    )
    activo: bool = Field(default=True, nullable=False)
    orden: int = Field(default=0, nullable=False)

    grupo: GrupoModificador | None = Relationship(back_populates="opciones")


class ProductoGrupoModificador(TimestampedModel, table=True):
    """Asignación de un grupo de modificadores a un producto."""

    __tablename__ = "food_producto_grupo_modificadores"

    id: int | None = Field(default=None, primary_key=True)
    producto_id: int = Field(foreign_key="food_productos.id", index=True, nullable=False)
    grupo_id: int = Field(foreign_key="food_grupo_modificadores.id", index=True, nullable=False)

    producto: Producto | None = Relationship(back_populates="producto_grupos")
    grupo: GrupoModificador | None = Relationship(back_populates="producto_grupos")


class Combo(TimestampedModel, table=True):
    """Combo a precio fijo (ej: hamburguesa+papas+bebida S/25)."""

    __tablename__ = "food_combos"

    id: int | None = Field(default=None, primary_key=True)
    company_id: int = Field(index=True, nullable=False)
    nombre: str = Field(max_length=160, nullable=False)
    descripcion: str | None = Field(default=None, max_length=240)
    precio: Decimal = Field(
        default=Decimal("0.00"),
        sa_column=Column(Numeric(10, 2), nullable=False),
    )
    emoji: str | None = Field(default=None, max_length=16)
    activo: bool = Field(default=True, nullable=False)
    orden: int = Field(default=0, nullable=False)

    items: list["ComboItem"] = Relationship(back_populates="combo")


class ComboItem(TimestampedModel, table=True):
    """Componente de un combo (producto + cantidad)."""

    __tablename__ = "food_combo_items"

    id: int | None = Field(default=None, primary_key=True)
    combo_id: int = Field(foreign_key="food_combos.id", index=True, nullable=False)
    producto_id: int = Field(foreign_key="food_productos.id", index=True, nullable=False)
    cantidad: int = Field(default=1, nullable=False)

    combo: Combo | None = Relationship(back_populates="items")
    producto: Producto | None = Relationship()


class Pedido(TimestampedModel, table=True):
    """Pedido de mesa o mostrador, scoped por empresa."""

    __tablename__ = "food_pedidos"

    id: int | None = Field(default=None, primary_key=True)
    company_id: int = Field(index=True, nullable=False)
    sucursal_id: int | None = Field(default=None, foreign_key="food_sucursales.id", index=True)
    mesa_id: int | None = Field(default=None, foreign_key="food_mesas.id", index=True)
    mozo_id: int | None = Field(default=None, foreign_key="food_usuarios.id", index=True)
    cajero_id: int | None = Field(default=None, foreign_key="food_usuarios.id", index=True)
    tipo_pedido: str = Field(
        default=TipoPedido.MESA.value,
        index=True,
        max_length=24,
        nullable=False,
    )
    nombre_cliente: str | None = Field(default=None, max_length=120)
    pagado: bool = Field(default=False, index=True, nullable=False)
    estado: str = Field(
        default=EstadoPedido.BORRADOR.value,
        index=True,
        max_length=32,
        nullable=False,
    )
    notas: str | None = Field(default=None, max_length=500)
    total: Decimal = Field(
        default=Decimal("0.00"),
        sa_column=Column(Numeric(10, 2), nullable=False),
    )
    propina: Decimal = Field(
        default=Decimal("0.00"),
        sa_column=Column(Numeric(10, 2), nullable=False, server_default="0.00"),
    )
    descuento: Decimal = Field(
        default=Decimal("0.00"),
        sa_column=Column(Numeric(10, 2), nullable=False, server_default="0.00"),
    )
    recargo: Decimal = Field(
        default=Decimal("0.00"),
        sa_column=Column(Numeric(10, 2), nullable=False, server_default="0.00"),
    )
    recargo_concepto: str | None = Field(default=None, max_length=60)
    metodo_pago: str | None = Field(default=None, max_length=24)
    abierto_en: datetime = Field(default_factory=utc_now_naive, nullable=False)
    cerrado_en: datetime | None = Field(default=None)

    cliente_id: int | None = Field(default=None, foreign_key="food_clientes.id", index=True)
    turno_caja_id: int | None = Field(default=None, foreign_key="food_turnos_caja.id", index=True)

    # Auditoría de anulación (estado CANCELADO con motivo obligatorio)
    motivo_cancelacion: str | None = Field(default=None, max_length=240)
    cancelado_por_id: int | None = Field(default=None, foreign_key="food_usuarios.id")
    cancelado_en: datetime | None = Field(default=None)

    # Delivery (FEAT-07)
    delivery_direccion: str | None = Field(default=None, max_length=240)
    delivery_telefono: str | None = Field(default=None, max_length=20)
    delivery_repartidor_id: int | None = Field(default=None, foreign_key="food_usuarios.id")
    delivery_estado: str | None = Field(default=None, max_length=20)
    delivery_notas: str | None = Field(default=None, max_length=240)
    self_order: bool = Field(default=False, nullable=False)
    self_order_aprobado: bool = Field(default=False, nullable=False)

    mesa: Mesa | None = Relationship(back_populates="pedidos")
    detalles: list["DetallePedido"] = Relationship(back_populates="pedido")
    cliente: "Cliente" = Relationship(back_populates="pedidos")


class Cliente(TimestampedModel, table=True):
    """Cliente registrado con historial y datos de contacto."""

    __tablename__ = "food_clientes"
    __table_args__ = (
        UniqueConstraint("company_id", "telefono", name="uq_food_clientes_company_tel"),
    )

    id: int | None = Field(default=None, primary_key=True)
    company_id: int = Field(index=True, nullable=False)
    nombre: str = Field(max_length=120, nullable=False)
    telefono: str | None = Field(default=None, max_length=20)
    email: str | None = Field(default=None, max_length=120)
    fecha_nacimiento: date | None = Field(
        default=None,
        sa_column=Column(Date, nullable=True),
    )
    notas: str | None = Field(default=None, max_length=240)
    puntos: int = Field(default=0, nullable=False)
    activo: bool = Field(default=True, nullable=False)

    pedidos: list["Pedido"] = Relationship(back_populates="cliente")
    cuenta_corriente: "CuentaCorriente" = Relationship(back_populates="cliente")


class CuentaCorriente(TimestampedModel, table=True):
    """Cuenta corriente / fiado por cliente, scoped por empresa."""

    __tablename__ = "food_cuentas_corrientes"
    __table_args__ = (
        UniqueConstraint("company_id", "cliente_id", name="uq_food_cc_company_cliente"),
    )

    id: int | None = Field(default=None, primary_key=True)
    company_id: int = Field(index=True, nullable=False)
    cliente_id: int = Field(foreign_key="food_clientes.id", index=True, nullable=False)
    saldo_deuda: Decimal = Field(
        default=Decimal("0.00"),
        sa_column=Column(Numeric(10, 2), nullable=False, server_default="0.00"),
    )
    limite_credito: Decimal = Field(
        default=Decimal("0.00"),
        sa_column=Column(Numeric(10, 2), nullable=False, server_default="0.00"),
    )

    cliente: "Cliente" = Relationship(back_populates="cuenta_corriente")
    movimientos: list["MovimientoCuenta"] = Relationship(back_populates="cuenta")


class MovimientoCuenta(TimestampedModel, table=True):
    """Cargo o pago en una cuenta corriente de cliente."""

    __tablename__ = "food_movimientos_cuenta"

    id: int | None = Field(default=None, primary_key=True)
    company_id: int = Field(index=True, nullable=False)
    cuenta_id: int = Field(foreign_key="food_cuentas_corrientes.id", index=True, nullable=False)
    pedido_id: int | None = Field(default=None, foreign_key="food_pedidos.id", index=True)
    tipo: str = Field(max_length=10, nullable=False)  # "cargo" | "pago"
    monto: Decimal = Field(
        default=Decimal("0.00"),
        sa_column=Column(Numeric(10, 2), nullable=False),
    )
    descripcion: str | None = Field(default=None, max_length=240)

    cuenta: "CuentaCorriente" = Relationship(back_populates="movimientos")


class Promocion(TimestampedModel, table=True):
    """Promoción activa del restaurante (descuento %, monto fijo o happy hour)."""

    __tablename__ = "food_promociones"

    id: int | None = Field(default=None, primary_key=True)
    company_id: int = Field(index=True, nullable=False)
    nombre: str = Field(max_length=120, nullable=False)
    tipo: str = Field(max_length=20, nullable=False)
    valor: Decimal = Field(
        default=Decimal("0.00"),
        sa_column=Column(Numeric(10, 2), nullable=False),
    )
    descripcion: str | None = Field(default=None, max_length=240)
    hora_inicio: str | None = Field(default=None, max_length=5)  # "HH:MM"
    hora_fin: str | None = Field(default=None, max_length=5)
    activa: bool = Field(default=True, nullable=False)

    # Motor de promos (réplica adaptada del engine de Sistema-de-Ventas)
    # Bitmask lunes=1, martes=2, ... domingo=64; 127 = todos los días
    dias_semana_mask: int = Field(default=127, nullable=False)
    producto_id: int | None = Field(default=None, foreign_key="food_productos.id", index=True)
    categoria_id: int | None = Field(default=None, foreign_key="food_categorias.id", index=True)
    auto_aplicar: bool = Field(default=True, nullable=False)


class ConfigImpresora(TimestampedModel, table=True):
    """Configuracion de impresoras por empresa (una fila por company)."""

    __tablename__ = "food_config_impresora"
    __table_args__ = (
        UniqueConstraint("company_id", name="uq_food_config_impresora_company"),
        UniqueConstraint("admin_email", name="uq_food_config_impresora_admin_email"),
        UniqueConstraint("slug", name="uq_food_config_impresora_slug"),
    )

    id: int | None = Field(default=None, primary_key=True)
    company_id: int = Field(index=True, nullable=False)
    nombre_local: str = Field(default="Mi Restaurante", max_length=120, nullable=False)
    cocina_activa: bool = Field(default=False, nullable=False)
    cocina_ip: str = Field(default="192.168.1.100", max_length=64, nullable=False)
    cocina_puerto: int = Field(default=9100, nullable=False)
    caja_activa: bool = Field(default=False, nullable=False)
    caja_ip: str = Field(default="", max_length=64, nullable=False)
    caja_puerto: int = Field(default=9100, nullable=False)
    ticket_paper_width_mm: int = Field(default=80, nullable=False)
    slug: str = Field(default="mi-restaurante", max_length=80, nullable=False)
    admin_email: str = Field(default="", max_length=120, nullable=False)
    admin_password_hash: str = Field(default="", max_length=128, nullable=False)
    ruc: str = Field(default="", max_length=30, nullable=False)
    sucursal: str = Field(default="", max_length=80, nullable=False)
    direccion: str = Field(default="", max_length=160, nullable=False)
    telefono: str = Field(default="", max_length=40, nullable=False)
    mensaje_ticket: str = Field(default="¡Gracias por su preferencia!", max_length=200, nullable=False)
    mostrar_iva: bool = Field(default=False, nullable=False)
    nombre_impuesto: str = Field(default="IGV", max_length=20, nullable=False)
    porcentaje_iva: float = Field(default=18.0, nullable=False)
    kds_minutos_alerta: int = Field(default=15, nullable=False)
    # Quién imprime: "navegador" (kiosk-printing actual) o "agente" (agente local
    # que jala los trabajos desde la nube). Ver Impresora/TrabajoImpresion/AgenteImpresion.
    modo_impresion: str = Field(default="navegador", max_length=20, nullable=False)


# ─── Impresión con agente local ──────────────────────────────────────────────


class RolImpresora(str, Enum):
    COCINA = "cocina"
    CAJA = "caja"


class TipoImpresora(str, Enum):
    RED = "red"
    USB = "usb"


class TipoDocumento(str, Enum):
    COMANDA = "comanda"
    COMPROBANTE = "comprobante"
    PRUEBA = "prueba"


class EstadoTrabajo(str, Enum):
    PENDIENTE = "pendiente"
    ENTREGADO = "entregado"
    IMPRESO = "impreso"
    ERROR = "error"


class ModoImpresion(str, Enum):
    NAVEGADOR = "navegador"
    AGENTE = "agente"


class Impresora(TimestampedModel, table=True):
    """Impresora física de un restaurante (red por IP o USB local), con un rol
    (cocina/caja). El agente local la usa para rutear cada trabajo a su destino."""

    __tablename__ = "food_impresoras"

    id: int | None = Field(default=None, primary_key=True)
    company_id: int = Field(index=True, nullable=False)
    sucursal_id: int | None = Field(
        default=None, foreign_key="food_sucursales.id", index=True
    )
    nombre: str = Field(max_length=120, nullable=False)
    rol: str = Field(default=RolImpresora.COCINA.value, max_length=20, nullable=False)
    tipo: str = Field(default=TipoImpresora.RED.value, max_length=10, nullable=False)
    # tipo == "red": impresora ESC/POS en la LAN del local
    ip: str = Field(default="", max_length=64, nullable=False)
    puerto: int = Field(default=9100, nullable=False)
    # tipo == "usb": nombre de la impresora en el SO / identificador del device
    usb_target: str = Field(default="", max_length=160, nullable=False)
    # None → usa ConfigImpresora.ticket_paper_width_mm de la empresa
    paper_width_mm: int | None = Field(default=None)
    activa: bool = Field(default=True, nullable=False)


class TrabajoImpresion(TimestampedModel, table=True):
    """Cola de trabajos de impresión. El backend encola; el agente los jala,
    imprime y confirma (ack). El `contenido` es el texto ya formateado al ancho."""

    __tablename__ = "food_trabajos_impresion"

    id: int | None = Field(default=None, primary_key=True)
    company_id: int = Field(index=True, nullable=False)
    sucursal_id: int | None = Field(default=None, index=True)
    rol: str = Field(default=RolImpresora.COCINA.value, index=True, max_length=20, nullable=False)
    tipo_doc: str = Field(default=TipoDocumento.COMANDA.value, max_length=20, nullable=False)
    contenido: str = Field(sa_column=Column(Text, nullable=False))
    paper_width_mm: int = Field(default=80, nullable=False)
    pedido_id: int | None = Field(default=None, index=True)
    estado: str = Field(default=EstadoTrabajo.PENDIENTE.value, index=True, max_length=20, nullable=False)
    intentos: int = Field(default=0, nullable=False)
    error_msg: str | None = Field(default=None, max_length=300)
    claimed_at: datetime | None = Field(default=None)
    done_at: datetime | None = Field(default=None)


class AgenteImpresion(TimestampedModel, table=True):
    """Agente local autorizado a jalar trabajos de una empresa (1 por local).
    Se guarda solo el hash del token; el token en claro se muestra una sola vez."""

    __tablename__ = "food_agentes_impresion"

    id: int | None = Field(default=None, primary_key=True)
    company_id: int = Field(index=True, nullable=False)
    sucursal_id: int | None = Field(
        default=None, foreign_key="food_sucursales.id", index=True
    )
    nombre: str = Field(default="Agente de impresión", max_length=120, nullable=False)
    token_hash: str = Field(max_length=128, index=True, nullable=False)
    activo: bool = Field(default=True, nullable=False)
    last_seen_at: datetime | None = Field(default=None)


class Insumo(TimestampedModel, table=True):
    """Insumo/ingrediente con control de stock, scoped por empresa."""

    __tablename__ = "food_insumos"
    __table_args__ = (
        UniqueConstraint("company_id", "nombre", name="uq_food_insumos_company_nombre"),
    )

    id: int | None = Field(default=None, primary_key=True)
    company_id: int = Field(index=True, nullable=False)
    sucursal_id: int | None = Field(default=None, foreign_key="food_sucursales.id", index=True)
    nombre: str = Field(max_length=120, nullable=False)
    unidad: str = Field(default="unidad", max_length=30, nullable=False)
    stock_actual: Decimal = Field(
        default=Decimal("0.000"),
        sa_column=Column(Numeric(12, 3), nullable=False, server_default="0.000"),
    )
    stock_minimo: Decimal = Field(
        default=Decimal("0.000"),
        sa_column=Column(Numeric(12, 3), nullable=False, server_default="0.000"),
    )
    fecha_vencimiento: date | None = Field(
        default=None,
        sa_column=Column(Date, nullable=True),
    )
    costo_unitario: Decimal = Field(
        default=Decimal("0.00"),
        sa_column=Column(Numeric(10, 2), nullable=False, server_default="0.00"),
    )  # costo por unidad de medida — alimenta el margen por plato
    activo: bool = Field(default=True, nullable=False)

    receta_items: list["RecetaItem"] = Relationship(back_populates="insumo")


class MovimientoInsumo(TimestampedModel, table=True):
    """Kardex de insumos: cada entrada/salida de stock con su motivo y saldo.

    Réplica adaptada de StockMovement de Sistema-de-Ventas. Las mermas son
    el caso clave del rubro: registran qué se perdió y por qué.
    """

    __tablename__ = "food_movimientos_insumo"

    id: int | None = Field(default=None, primary_key=True)
    company_id: int = Field(index=True, nullable=False)
    insumo_id: int = Field(foreign_key="food_insumos.id", index=True, nullable=False)
    usuario_id: int | None = Field(default=None, foreign_key="food_usuarios.id")
    pedido_id: int | None = Field(default=None, foreign_key="food_pedidos.id", index=True)
    tipo: str = Field(index=True, max_length=16, nullable=False)
    cantidad: Decimal = Field(
        default=Decimal("0.000"),
        sa_column=Column(Numeric(12, 3), nullable=False),
    )  # positiva entra, negativa sale
    stock_resultante: Decimal = Field(
        default=Decimal("0.000"),
        sa_column=Column(Numeric(12, 3), nullable=False),
    )
    motivo: str | None = Field(default=None, max_length=240)


class RecetaItem(TimestampedModel, table=True):
    """Ingrediente de la receta de un producto — cuánto insumo consume por unidad vendida."""

    __tablename__ = "food_receta_items"
    __table_args__ = (
        UniqueConstraint(
            "company_id", "producto_id", "insumo_id",
            name="uq_food_receta_company_prod_insumo",
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    company_id: int = Field(index=True, nullable=False)
    producto_id: int = Field(foreign_key="food_productos.id", index=True, nullable=False)
    insumo_id: int = Field(foreign_key="food_insumos.id", index=True, nullable=False)
    cantidad: Decimal = Field(
        default=Decimal("1.000"),
        sa_column=Column(Numeric(10, 3), nullable=False, server_default="1.000"),
    )

    producto: "Producto" = Relationship(back_populates="receta_items")
    insumo: "Insumo" = Relationship(back_populates="receta_items")


class TurnoCaja(TimestampedModel, table=True):
    """Turno de caja: apertura con fondo inicial, cierre con arqueo y descuadre."""

    __tablename__ = "food_turnos_caja"

    id: int | None = Field(default=None, primary_key=True)
    company_id: int = Field(index=True, nullable=False)
    sucursal_id: int | None = Field(default=None, foreign_key="food_sucursales.id", index=True)
    abierto_por_id: int | None = Field(default=None, foreign_key="food_usuarios.id", index=True)
    cerrado_por_id: int | None = Field(default=None, foreign_key="food_usuarios.id")
    estado: str = Field(
        default=EstadoTurnoCaja.ABIERTO.value,
        index=True,
        max_length=16,
        nullable=False,
    )
    monto_inicial: Decimal = Field(
        default=Decimal("0.00"),
        sa_column=Column(Numeric(10, 2), nullable=False),
    )
    abierto_en: datetime = Field(default_factory=utc_now_naive, nullable=False)
    cerrado_en: datetime | None = Field(default=None)

    # Snapshot congelado al cierre del turno
    total_efectivo: Decimal = Field(
        default=Decimal("0.00"),
        sa_column=Column(Numeric(10, 2), nullable=False, server_default="0.00"),
    )
    total_tarjeta: Decimal = Field(
        default=Decimal("0.00"),
        sa_column=Column(Numeric(10, 2), nullable=False, server_default="0.00"),
    )
    total_qr: Decimal = Field(
        default=Decimal("0.00"),
        sa_column=Column(Numeric(10, 2), nullable=False, server_default="0.00"),
    )
    total_fiado: Decimal = Field(
        default=Decimal("0.00"),
        sa_column=Column(Numeric(10, 2), nullable=False, server_default="0.00"),
    )
    total_propinas: Decimal = Field(
        default=Decimal("0.00"),
        sa_column=Column(Numeric(10, 2), nullable=False, server_default="0.00"),
    )
    total_ingresos: Decimal = Field(
        default=Decimal("0.00"),
        sa_column=Column(Numeric(10, 2), nullable=False, server_default="0.00"),
    )
    total_egresos: Decimal = Field(
        default=Decimal("0.00"),
        sa_column=Column(Numeric(10, 2), nullable=False, server_default="0.00"),
    )
    esperado_efectivo: Decimal = Field(
        default=Decimal("0.00"),
        sa_column=Column(Numeric(10, 2), nullable=False, server_default="0.00"),
    )
    contado_efectivo: Decimal = Field(
        default=Decimal("0.00"),
        sa_column=Column(Numeric(10, 2), nullable=False, server_default="0.00"),
    )
    descuadre: Decimal = Field(
        default=Decimal("0.00"),
        sa_column=Column(Numeric(10, 2), nullable=False, server_default="0.00"),
    )
    arqueo_detalle: str | None = Field(default=None, max_length=1000)  # JSON denominaciones
    notas_cierre: str | None = Field(default=None, max_length=500)

    movimientos: list["MovimientoCaja"] = Relationship(back_populates="turno")


class MovimientoCaja(TimestampedModel, table=True):
    """Ingreso o egreso de efectivo registrado durante un turno de caja."""

    __tablename__ = "food_movimientos_caja"

    id: int | None = Field(default=None, primary_key=True)
    company_id: int = Field(index=True, nullable=False)
    turno_id: int = Field(foreign_key="food_turnos_caja.id", index=True, nullable=False)
    usuario_id: int | None = Field(default=None, foreign_key="food_usuarios.id")
    tipo: str = Field(max_length=10, nullable=False)  # "ingreso" | "egreso"
    categoria: str = Field(default="Otros", max_length=40, nullable=False)
    monto: Decimal = Field(
        default=Decimal("0.00"),
        sa_column=Column(Numeric(10, 2), nullable=False),
    )
    motivo: str = Field(max_length=240, nullable=False)

    turno: "TurnoCaja" = Relationship(back_populates="movimientos")


class PagoPedido(TimestampedModel, table=True):
    """Pago individual de un pedido — permite pago mixto y cuenta dividida.

    Un pedido cobrado tiene 1..N pagos (efectivo + tarjeta, o un pago por
    comensal). El monto de efectivo se guarda neto de vuelto: es lo que
    queda en el cajón. Réplica adaptada de SalePayment de Sistema-de-Ventas.
    """

    __tablename__ = "food_pagos_pedido"

    id: int | None = Field(default=None, primary_key=True)
    company_id: int = Field(index=True, nullable=False)
    pedido_id: int = Field(foreign_key="food_pedidos.id", index=True, nullable=False)
    turno_caja_id: int | None = Field(
        default=None, foreign_key="food_turnos_caja.id", index=True
    )
    usuario_id: int | None = Field(default=None, foreign_key="food_usuarios.id")
    metodo: str = Field(max_length=24, nullable=False)
    monto: Decimal = Field(
        default=Decimal("0.00"),
        sa_column=Column(Numeric(10, 2), nullable=False),
    )
    detalle_ids_json: str | None = Field(
        default=None, sa_column=Column(Text, nullable=True),
    )


class DetallePedido(TimestampedModel, table=True):
    """Línea individual de producto dentro de un pedido."""

    __tablename__ = "food_detalle_pedidos"

    id: int | None = Field(default=None, primary_key=True)
    company_id: int = Field(index=True, nullable=False)
    pedido_id: int = Field(foreign_key="food_pedidos.id", index=True, nullable=False)
    producto_id: int = Field(foreign_key="food_productos.id", index=True, nullable=False)
    cantidad: int = Field(default=1, ge=1, nullable=False)
    precio_unitario: Decimal = Field(
        default=Decimal("0.00"),
        sa_column=Column(Numeric(10, 2), nullable=False),
    )
    subtotal: Decimal = Field(
        default=Decimal("0.00"),
        sa_column=Column(Numeric(10, 2), nullable=False),
    )
    notas: str | None = Field(default=None, max_length=240)
    enviado_cocina_at: datetime | None = Field(default=None)
    preparado_por_id: int | None = Field(
        default=None,
        foreign_key="food_usuarios.id",
        index=True,
    )
    estado_produccion: str = Field(
        default=EstadoProduccion.PENDIENTE.value,
        index=True,
        max_length=40,
        nullable=False,
    )
    impreso_cocina: bool = Field(default=False, nullable=False)
    impreso_caja: bool = Field(default=False, nullable=False)
    # Marca de "comanda ya impresa en papel". La pone la primera pantalla que
    # la imprime (Caja o /estacion-impresion), de forma atómica, para que cada
    # comanda salga UNA sola vez sin importar cuántas pantallas estén abiertas.
    ticket_impreso_at: datetime | None = Field(default=None, index=True)
    modificadores_json: str | None = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
    )
    combo_items_json: str | None = Field(
        default=None,
        sa_column=Column(Text, nullable=True),
    )

    pedido: Pedido | None = Relationship(back_populates="detalles")
    producto: Producto | None = Relationship(back_populates="detalles")


class CuponLote(TimestampedModel, table=True):
    """Lote de cupones por código — apertura, fidelidad, marketing, etc."""

    __tablename__ = "food_cupon_lotes"
    __table_args__ = (
        UniqueConstraint("company_id", "codigo", name="uq_food_cupon_lotes_company_codigo"),
    )

    id: int | None = Field(default=None, primary_key=True)
    company_id: int = Field(index=True, nullable=False)
    nombre: str = Field(max_length=120, nullable=False)
    codigo: str = Field(max_length=40, nullable=False)
    tipo: str = Field(max_length=20, nullable=False)  # "porcentaje" | "monto_fijo"
    valor: Decimal = Field(
        default=Decimal("0.00"),
        sa_column=Column(Numeric(10, 2), nullable=False),
    )
    fecha_inicio: date | None = Field(default=None, sa_column=Column(Date, nullable=True))
    fecha_fin: date | None = Field(default=None, sa_column=Column(Date, nullable=True))
    usos_max: int | None = Field(default=None, nullable=True)
    usos_actuales: int = Field(default=0, nullable=False)
    activo: bool = Field(default=True, nullable=False)


class Reserva(TimestampedModel, table=True):
    """Reserva de mesa — fecha, hora, pax, cliente opcional."""

    __tablename__ = "food_reservas"

    id: int | None = Field(default=None, primary_key=True)
    company_id: int = Field(index=True, nullable=False)
    sucursal_id: int | None = Field(default=None, foreign_key="food_sucursales.id", index=True)
    mesa_id: int | None = Field(default=None, foreign_key="food_mesas.id", index=True)
    cliente_id: int | None = Field(default=None, foreign_key="food_clientes.id", index=True)
    nombre_cliente: str = Field(max_length=120, nullable=False)
    telefono: str = Field(default="", max_length=20, nullable=False)
    fecha: date = Field(sa_column=Column(Date, nullable=False, index=True))
    hora: str = Field(max_length=5, nullable=False)
    pax: int = Field(default=2, ge=1, nullable=False)
    estado: str = Field(
        default=EstadoReserva.PENDIENTE.value,
        index=True,
        max_length=20,
        nullable=False,
    )
    notas: str | None = Field(default=None, max_length=240)


class Auditoria(SQLModel, table=True):
    """Log de auditoría transversal — cambios sensibles registrados de forma inmutable."""

    __tablename__ = "food_auditoria"

    id: int | None = Field(default=None, primary_key=True)
    company_id: int = Field(index=True, nullable=False)
    usuario_id: int | None = Field(default=None, index=True)
    usuario_nombre: str = Field(default="", max_length=120)
    accion: str = Field(max_length=60, nullable=False, index=True)
    entidad: str = Field(default="", max_length=60)
    entidad_id: int | None = Field(default=None)
    detalle: str | None = Field(default=None, sa_column=Column(Text, nullable=True))
    ip: str | None = Field(default=None, max_length=45)
    created_at: datetime = Field(default_factory=utc_now_naive, nullable=False, index=True)


@event.listens_for(TimestampedModel, "before_update", propagate=True)
def _auto_updated_at(mapper, connection, target) -> None:
    target.updated_at = utc_now_naive()
