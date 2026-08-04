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
    stylesheets=["/twk.css"],
    head_components=[
        rx.el.link(rel="icon", type="image/png", href="/TUWAYKIFOODFAVICON.png"),
        rx.el.link(rel="shortcut icon", href="/TUWAYKIFOODFAVICON.png"),
        # ── PWA: instalable como app nativa (ventana propia, sin barra de URL) ──
        rx.el.link(rel="manifest", href="/manifest.webmanifest"),
        rx.el.meta(name="theme-color", content="#503beb"),
        rx.el.meta(name="application-name", content="TUWAYKIFOOD"),
        rx.el.meta(name="mobile-web-app-capable", content="yes"),
        rx.el.meta(name="apple-mobile-web-app-capable", content="yes"),
        rx.el.meta(name="apple-mobile-web-app-title", content="TUWAYKIFOOD"),
        rx.el.meta(
            name="apple-mobile-web-app-status-bar-style",
            content="black-translucent",
        ),
        rx.el.link(rel="apple-touch-icon", href="/pwa/apple-touch-icon.png"),
        # Registro del service worker (habilita "Instalar app"). Se difiere al
        # load para no competir con el arranque del frontend.
        rx.el.script(
            "if('serviceWorker' in navigator){"
            "window.addEventListener('load',function(){"
            "navigator.serviceWorker.register('/sw.js').catch(function(e){"
            "console.warn('SW registration failed:',e);});});}"
        ),
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
