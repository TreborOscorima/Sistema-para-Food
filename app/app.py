"""TUWAYKIFOOD — entry point Reflex."""

from __future__ import annotations

import reflex as rx

# Importar páginas para que los decoradores @rx.page las registren
import app.pages  # noqa: F401
from app.states.food_state import FoodState
from app.api import health_app


def index() -> rx.Component:
    return rx.fragment(
        rx.cond(
            FoodState.autenticado,
            rx.script("window.location.href = '/mozos';"),
            rx.script("window.location.href = '/login';"),
        )
    )


app = rx.App(api_transformer=health_app)

app.add_page(index, route="/", on_load=FoodState.on_load_root)
