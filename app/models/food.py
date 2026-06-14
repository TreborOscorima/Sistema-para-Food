"""Modelos SQLModel de TUWAYKIFOOD (multi-tenant, MySQL)."""

from datetime import datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import Column, Numeric, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel


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


class RolUsuario(str, Enum):
    MOZO = "Mozo"
    CAJA = "Caja"
    COCINA = "Cocina"
    ADMIN = "Admin"


class TimestampedModel(SQLModel):
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)


class UsuarioFood(TimestampedModel, table=True):
    """Usuario operativo del restaurante, autenticado por PIN + company_id."""

    __tablename__ = "food_usuarios"
    __table_args__ = (
        UniqueConstraint("company_id", "pin", name="uq_food_usuarios_company_pin"),
    )

    id: int | None = Field(default=None, primary_key=True)
    company_id: int = Field(index=True, nullable=False)
    nombre: str = Field(max_length=120, nullable=False)
    pin: str = Field(max_length=6, nullable=False)
    rol: str = Field(index=True, max_length=32, nullable=False)
    activo: bool = Field(default=True, nullable=False)


class Mesa(TimestampedModel, table=True):
    """Mesa física del salón, scoped por empresa."""

    __tablename__ = "food_mesas"
    __table_args__ = (
        UniqueConstraint("company_id", "numero", name="uq_food_mesas_company_numero"),
    )

    id: int | None = Field(default=None, primary_key=True)
    company_id: int = Field(index=True, nullable=False)
    numero: int = Field(index=True, nullable=False)
    nombre: str = Field(default="", max_length=80, nullable=False)
    capacidad: int = Field(default=4, ge=1, nullable=False)
    estado: str = Field(
        default=EstadoMesa.LIBRE.value,
        index=True,
        max_length=32,
        nullable=False,
    )
    activa: bool = Field(default=True, nullable=False)

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

    categoria: Categoria | None = Relationship(back_populates="productos")
    detalles: list["DetallePedido"] = Relationship(back_populates="producto")
    receta_items: list["RecetaItem"] = Relationship(back_populates="producto")


class Pedido(TimestampedModel, table=True):
    """Pedido de mesa o mostrador, scoped por empresa."""

    __tablename__ = "food_pedidos"

    id: int | None = Field(default=None, primary_key=True)
    company_id: int = Field(index=True, nullable=False)
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
    metodo_pago: str | None = Field(default=None, max_length=24)
    abierto_en: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    cerrado_en: datetime | None = Field(default=None)

    mesa: Mesa | None = Relationship(back_populates="pedidos")
    detalles: list["DetallePedido"] = Relationship(back_populates="pedido")


class ConfigImpresora(TimestampedModel, table=True):
    """Configuracion de impresoras por empresa (una fila por company)."""

    __tablename__ = "food_config_impresora"
    __table_args__ = (
        UniqueConstraint("company_id", name="uq_food_config_impresora_company"),
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
    slug: str = Field(default="mi-restaurante", max_length=80, nullable=False)
    admin_email: str = Field(default="", max_length=120, nullable=False)
    admin_password_hash: str = Field(default="", max_length=128, nullable=False)


class Insumo(TimestampedModel, table=True):
    """Insumo/ingrediente con control de stock, scoped por empresa."""

    __tablename__ = "food_insumos"
    __table_args__ = (
        UniqueConstraint("company_id", "nombre", name="uq_food_insumos_company_nombre"),
    )

    id: int | None = Field(default=None, primary_key=True)
    company_id: int = Field(index=True, nullable=False)
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
    activo: bool = Field(default=True, nullable=False)

    receta_items: list["RecetaItem"] = Relationship(back_populates="insumo")


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

    producto: "Producto | None" = Relationship(back_populates="receta_items")
    insumo: "Insumo | None" = Relationship(back_populates="receta_items")


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

    pedido: Pedido | None = Relationship(back_populates="detalles")
    producto: Producto | None = Relationship(back_populates="detalles")
