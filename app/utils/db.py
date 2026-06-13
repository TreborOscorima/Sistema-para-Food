from __future__ import annotations

import os
from contextlib import contextmanager
from urllib.parse import quote_plus

from sqlmodel import Session, create_engine

_engine = None


def _build_url() -> str:
    user = quote_plus(os.getenv("DB_USER", "root"))
    password = quote_plus(os.getenv("DB_PASSWORD", ""))
    host = os.getenv("DB_HOST", "localhost")
    port = int(os.getenv("DB_PORT", "3306") or "3306")
    name = os.getenv("DB_NAME", "food_db")
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{name}?charset=utf8mb4"


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(
            _build_url(),
            pool_pre_ping=True,
            pool_recycle=1800,
            echo=False,
        )
    return _engine


@contextmanager
def get_session():
    with Session(get_engine()) as session:
        yield session
