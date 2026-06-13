"""Alembic env — TUWAYKIFOOD."""

from __future__ import annotations

import os
from logging.config import fileConfig
from urllib.parse import quote_plus

from alembic import context
from sqlmodel import SQLModel

# Importar modelos para que SQLModel.metadata los registre
import app.models.food  # noqa: F401

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def _build_url() -> str:
    user = quote_plus(os.getenv("DB_USER", "root"))
    password = quote_plus(os.getenv("DB_PASSWORD", ""))
    host = os.getenv("DB_HOST", "localhost")
    port = int(os.getenv("DB_PORT", "3306") or "3306")
    name = os.getenv("DB_NAME", "food_db")
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{name}?charset=utf8mb4"


target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    url = _build_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    from sqlalchemy import create_engine

    connectable = create_engine(_build_url(), pool_pre_ping=True)
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
