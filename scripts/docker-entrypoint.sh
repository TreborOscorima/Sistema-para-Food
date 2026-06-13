#!/bin/bash
set -e

echo "[entrypoint] Corriendo migraciones Alembic..."
alembic upgrade head

echo "[entrypoint] Iniciando Reflex..."
exec reflex run --env prod --backend-host 0.0.0.0 --backend-port 3004 --frontend-port 3003
