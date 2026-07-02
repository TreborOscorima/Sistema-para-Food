"""Modelo Company — registro de tenants (restaurantes) de TUWAYKIFOOD."""

from datetime import datetime

from sqlalchemy import UniqueConstraint
from sqlmodel import Field

from app.models.food import TimestampedModel


class Company(TimestampedModel, table=True):
    """Un restaurante/cliente de TUWAYKIFOOD. No tiene company_id propio: ES el tenant."""

    __tablename__ = "food_companies"
    __table_args__ = (
        UniqueConstraint("slug", name="uq_food_companies_slug"),
    )

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=160, nullable=False)
    slug: str = Field(max_length=80, nullable=False, index=True)
    is_active: bool = Field(default=True, nullable=False)
    trial_ends_at: datetime | None = Field(default=None)
    logo_url: str | None = Field(default=None, max_length=500)
