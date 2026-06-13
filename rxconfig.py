from __future__ import annotations

import os
from urllib.parse import quote_plus

from dotenv import load_dotenv
import reflex as rx

load_dotenv()

ENV = (os.getenv("ENV") or "dev").strip().lower()
IS_PROD = ENV in {"prod", "production"}
API_URL = os.getenv("PUBLIC_API_URL", "http://localhost:3003")
# En prod Reflex corre frontend + backend en el mismo proceso/puerto (3003)
FRONTEND_PORT = int(os.getenv("FRONTEND_PORT", "3003"))


def _require_env(var_name: str, *, dev_default: str = "") -> str:
    value = os.getenv(var_name)
    if value:
        return value
    if IS_PROD:
        raise RuntimeError(f"[rxconfig] Variable obligatoria en producción: {var_name}")
    return dev_default


DB_USER = _require_env("DB_USER", dev_default="root")
DB_PASSWORD = _require_env("DB_PASSWORD")
DB_HOST = _require_env("DB_HOST", dev_default="localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306") or "3306")
DB_NAME = _require_env("DB_NAME", dev_default="food_db")

_USER_ESC = quote_plus(DB_USER)
_PASS_ESC = quote_plus(DB_PASSWORD)

DB_URL = (
    f"mysql+pymysql://{_USER_ESC}:{_PASS_ESC}@{DB_HOST}:{int(DB_PORT)}/{DB_NAME}"
    f"?charset=utf8mb4"
)

from reflex_base.plugins.sitemap import SitemapPlugin  # noqa: E402
from reflex_components_radix.plugin import RadixThemesPlugin  # noqa: E402

config = rx.Config(
    app_name="app",
    db_url=DB_URL,
    api_url=API_URL,
    plugins=[
        rx.plugins.TailwindV4Plugin(),
        SitemapPlugin(),
        RadixThemesPlugin(theme=rx.theme(appearance="dark", accent_color="orange")),
    ],
    telemetry_enabled=not IS_PROD,
    show_built_with_reflex=False,
)
