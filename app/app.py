"""TUWAYKIFOOD — entry point Reflex."""

from __future__ import annotations

import json
import reflex as rx

# Importar páginas para que los decoradores @rx.page las registren
import app.pages  # noqa: F401
from app.states.food_state import FoodState
from app.api import health_app

# CSS global embebido en JS porque rx.el.style() pasa siempre por Emotion,
# que scopea todas las reglas con un prefix (.css-XXXX .twk-panel) que nunca
# existe en el DOM del body. Solución: inyectar via <script> que crea el
# <style> directamente — los scripts no son procesados por Emotion.
_GLOBAL_CSS = (
    "input::placeholder,textarea::placeholder{color:#94A3B8!important;opacity:1!important}"
    "html{scroll-behavior:smooth}"
    "*{-webkit-tap-highlight-color:rgba(234,88,12,0.12)}"
    "@media(max-width:1023px){"
    "input[type=text],input[type=number],input[type=email],"
    "input[type=password],input[type=search],input[type=tel],"
    "input[type=url],input[type=date],textarea,select{font-size:16px!important}}"
    ".twk-cols-lg,.twk-cols-md{display:flex!important;flex-wrap:wrap!important;gap:20px;width:100%;align-items:flex-start}"
    ".twk-panel{flex:0 0 100%!important;min-width:0!important;box-sizing:border-box}"
    "@media(min-width:1024px){"
    ".twk-cols-lg{flex-wrap:nowrap!important}"
    ".twk-cols-lg .twk-panel{flex:1 1 0!important}}"
    "@media(min-width:768px){"
    ".twk-cols-md{flex-wrap:nowrap!important}"
    ".twk-cols-md .twk-panel{flex:1 1 0!important}}"
    ".twk-sep{display:none!important}"
    "@media(min-width:1024px){.twk-cols-lg .twk-sep{display:block!important;flex:0 0 auto!important}}"
    "@media(min-width:768px){.twk-cols-md .twk-sep{display:block!important;flex:0 0 auto!important}}"
    ".twk-form-row{display:flex!important;flex-direction:column!important;gap:12px;width:100%}"
    "@media(min-width:768px){"
    ".twk-form-row{flex-direction:row!important;gap:12px}"
    ".twk-form-row>*{flex:1!important;min-width:0!important}}"
    ".twk-form-row>*{width:100%}"
    ".twk-field-row{display:flex!important;flex-direction:column!important;gap:6px;width:100%;align-items:flex-start}"
    "@media(min-width:640px){"
    ".twk-field-row{flex-direction:row!important;align-items:center!important}"
    ".twk-field-row>*:first-child{flex:0 0 140px!important;min-width:0}"
    ".twk-field-row>*:last-child{flex:1!important;min-width:0}}"
    "::-webkit-scrollbar{width:6px;height:6px}"
    "::-webkit-scrollbar-track{background:#F1F5F9}"
    "::-webkit-scrollbar-thumb{background:#CBD5E1;border-radius:3px}"
    "::-webkit-scrollbar-thumb:hover{background:#94A3B8}"
    "[data-radix-select-viewport]{font-size:15px!important}"
)

# Script que inyecta el CSS como <style> raw, sin pasar por Emotion
_CSS_INJECT_SCRIPT = f"""(function(){{
  if(document.getElementById('twk-css'))return;
  var s=document.createElement('style');
  s.id='twk-css';
  s.textContent={json.dumps(_GLOBAL_CSS)};
  document.head.appendChild(s);
}})();"""


def index() -> rx.Component:
    return rx.fragment(
        rx.cond(
            FoodState.autenticado,
            rx.script("window.location.href = '/mozos';"),
            rx.script("window.location.href = '/login';"),
        )
    )


app = rx.App(
    api_transformer=health_app,
    head_components=[
        rx.el.link(rel="icon", type="image/png", href="/TUWAYKIFOODFAVICON.png"),
        rx.el.link(rel="shortcut icon", href="/TUWAYKIFOODFAVICON.png"),
        rx.script(_CSS_INJECT_SCRIPT),
    ],
)

app.add_page(index, route="/", on_load=FoodState.on_load_root)
