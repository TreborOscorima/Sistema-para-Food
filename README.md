# TUWAYKIFOOD

Sistema **SaaS multi-tenant** de gestión integral para el rubro gastronómico (restaurantes, restobares,
bares, cafeterías y comida rápida). Mercado inicial: Perú (moneda S/, IGV 18%). Construido 100% en Python
con **Reflex**, corre en la LAN del local (tabletas de mozos, PC de caja, pantalla de cocina) y en Docker
para producción (`food.tuwayki.app`).

> **Documentación completa:** [`PROYECTO_TUWAYKIFOOD.md`](PROYECTO_TUWAYKIFOOD.md) es el documento maestro
> (visión, arquitectura, modelo de datos, convenciones, roadmap). Este README es solo el arranque rápido.

---

## Stack

| Capa | Tecnología |
|---|---|
| Framework full-stack | **Reflex 0.9.8** (Python → React/Vite, estado por websockets) |
| Base de datos | **MySQL 8.0** (`food_db`), SQLModel + SQLAlchemy 2.0, PyMySQL |
| Migraciones | Alembic |
| Servidor | Granian, contenedor Docker único (frontend + backend, puerto interno 3000) |
| Auth | bcrypt (PIN operativo + email/contraseña del dueño) |
| Compartido | `tuwayki-core` @ git (paquete privado, pinneado por commit) |

## Módulos

- **Operativo:** mapa de mesas / toma de pedidos (Mozos), KDS de cocina, Mostrador (takeaway),
  Caja (cobros, turnos con arqueo), estación de impresión.
- **Administrador (dueño):** dashboard, carta (categorías/productos/combos/modificadores),
  inventario y recetas, clientes, cuentas corrientes (fiado), promociones, cupones,
  reportes/analítica, usuarios/PINs, configuración.
- **Cliente:** carta digital pública por QR (`/menu/<slug>`) con autopedido.

---

## Desarrollo local

Requisitos: Python 3.13, un MySQL accesible y el paquete `tuwayki-core` (se instala desde git).
La preparación del entorno sigue el skill `setup-python-env`; para correr/recargar, `reflex-process-management`.

```bash
# 1. Entorno virtual + dependencias
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt   # Windows (Git Bash)

# 2. Variables de entorno (copiar y completar)
cp .env.example .env

# 3. Migraciones
alembic upgrade head

# 4. Correr
reflex run
```

Puertos en dev: **3003** (frontend) / **3004** (backend API).

## Docker (local, réplica de producción)

```bash
docker compose -f docker-compose.yml -f docker-compose.local.yml up -d
```

Levanta MySQL + la app en `http://localhost:3003`. El frontend se compila dentro del contenedor en el
primer arranque (healthcheck en `/api/ping`).

> ⚠️ Tras un **cambio de versión de Reflex**, recrear el volumen `food_web` para forzar un build fresco
> del frontend (evita servir un bundle cacheado): `docker volume rm <proyecto>_food_web` con el stack abajo.

## Despliegue a producción

Flujo trunk-based (sin PR): un push a `docker-deploy-prod` dispara el deploy automático (GitHub Actions →
SSH a EC2 → backup MySQL + build + health check). `main` y `docker-deploy-prod` se mantienen sincronizadas.

```bash
git push origin HEAD:main HEAD:docker-deploy-prod
```

---

## Tests

```bash
pytest tests/
```

Suite de integración de la lógica de negocio (pagos, cobros, turnos de caja, stock/kardex, aislamiento
multi-tenant, promociones, producción).

## Documentación

| Documento | Contenido |
|---|---|
| [`PROYECTO_TUWAYKIFOOD.md`](PROYECTO_TUWAYKIFOOD.md) | Documento maestro (arquitectura, datos, convenciones, roadmap) |
| [`AUDITORIA_FRONTEND_TUWAYKIFOOD.md`](AUDITORIA_FRONTEND_TUWAYKIFOOD.md) | Auditoría de frontend y guía de UI |
| [`PLAN_ACTUALIZACION_REFLEX.md`](PLAN_ACTUALIZACION_REFLEX.md) | Plan y verificación del upgrade de Reflex (flota) |
| [`docs/ESTACION_IMPRESION.md`](docs/ESTACION_IMPRESION.md) | Impresión térmica / agente local |
| [`docs/FACTURACION_ELECTRONICA.md`](docs/FACTURACION_ELECTRONICA.md) | Diseño de facturación electrónica (FEAT-06) |
| [`CLAUDE.md`](CLAUDE.md) | Instrucciones para agentes IA (skills de Reflex obligatorios) |

---

**Proyecto hermano:** Sistema-de-Ventas (retail). Comparten `tuwayki-core` y el Owner Panel de activación
de empresas. Los repos son 100% independientes.
