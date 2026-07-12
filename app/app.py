"""TUWAYKIFOOD — entry point Reflex."""

from __future__ import annotations

import reflex as rx

import app.models  # noqa: F401  Importar modelos ANTES de registrar los listeners de tenant

# IMPORTANTE: registrar aislamiento multi-tenant antes de cualquier query.
from app.utils.tenant import register_tenant_listeners
register_tenant_listeners()

# Importar páginas para que los decoradores @rx.page las registren
import app.pages  # noqa: F401
from app.states.food_state import FoodState
from app.api import health_app


def index() -> rx.Component:
    return rx.fragment()


app = rx.App(
    api_transformer=health_app,
    theme=rx.theme(appearance="light"),
    stylesheets=["/twk.css"],
    head_components=[
        rx.el.link(rel="icon", type="image/png", href="/TUWAYKIFOODFAVICON.png"),
        rx.el.link(rel="shortcut icon", href="/TUWAYKIFOODFAVICON.png"),
        rx.el.link(rel="preconnect", href="https://fonts.googleapis.com"),
        rx.el.link(
            rel="preconnect",
            href="https://fonts.gstatic.com",
            crossorigin="",
        ),
        rx.el.link(
            rel="stylesheet",
            href="https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,400;0,14..32,500;0,14..32,600;0,14..32,700;0,14..32,800&display=swap",
        ),
    ],
)

app.add_page(index, route="/", on_load=FoodState.on_load_root)
