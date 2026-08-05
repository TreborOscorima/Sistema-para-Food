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


def _debug_backend_exception_handler(exception: Exception):
    """TEMPORAL / DIAGNÓSTICO — REVERTIR una vez identificado el bug.

    En producción, Reflex oculta el error real y solo muestra "Contact the
    website administrator". Como el deploy es en AWS por GitHub Actions y no hay
    acceso directo a los logs del contenedor, este handler expone el tipo, el
    mensaje y las últimas líneas del traceback en el propio toast, para poder
    diagnosticar desde el navegador. Una vez encontrado el fallo se vuelve al
    handler por defecto.
    """
    import traceback

    tb = traceback.format_exception(type(exception), exception, exception.__traceback__)
    print("[Reflex Backend Exception]\n" + "".join(tb), flush=True)
    detalle = "".join(tb[-6:])[-1000:]
    return rx.toast.error(
        f"{type(exception).__name__}: {exception}",
        description=detalle,
        position="top-center",
        duration=120000,
        close_button=True,
        style={
            "width": "620px",
            "white-space": "pre-wrap",
            "font-size": "11px",
            "font-family": "monospace",
        },
    )


app = rx.App(
    api_transformer=health_app,
    # TEMPORAL: handler de diagnóstico que muestra el traceback en pantalla.
    # Revertir (quitar este kwarg) cuando se identifique el bug de /usuarios.
    backend_exception_handler=_debug_backend_exception_handler,
    # La app es 100% en español: declaramos el idioma y marcamos el <html> como
    # no traducible. Junto al <meta name="google" content="notranslate">, esto
    # evita que Chrome auto-traduzca y rompa el render (crash "removeChild").
    html_lang="es",
    html_custom_attrs={"translate": "no"},
    stylesheets=["/twk.css"],
    head_components=[
        # viewport-fit=cover: permite usar env(safe-area-inset-*) para respetar
        # el notch / isla de los iPhone cuando la PWA corre en standalone.
        rx.el.meta(
            name="viewport",
            content="width=device-width, initial-scale=1, viewport-fit=cover",
        ),
        # notranslate: la app ya está en español. Si Chrome la auto-traduce
        # (a veces detecta mal el idioma y la "traduce" al español), reescribe
        # los nodos de texto y entra en conflicto con el render de React/Reflex
        # → crash "NotFoundError: removeChild" al cambiar selects o navegar.
        # Con esto Chrome no ofrece ni aplica traducción y el problema desaparece
        # sin que el usuario tenga que tocar nada del navegador.
        rx.el.meta(name="google", content="notranslate"),
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
