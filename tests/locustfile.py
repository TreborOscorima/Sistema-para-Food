"""Test de carga TUWAYKIFOOD — simula 7 clientes concurrentes con polling.

Uso:
    pip install locust
    locust -f tests/locustfile.py --host http://localhost:3003

Luego abrir http://localhost:8089 y configurar 7 usuarios, spawn rate 1/s.
"""
from __future__ import annotations

from locust import HttpUser, between, task


class HealthCheckUser(HttpUser):
    """Simula el polling de health que cada cliente WebSocket dispara."""
    wait_time = between(3, 8)

    @task(5)
    def ping(self):
        self.client.get("/api/ping", name="/api/ping")

    @task(2)
    def health(self):
        self.client.get("/api/health", name="/api/health")

    @task(3)
    def load_login_page(self):
        self.client.get("/login", name="/login (SPA)")

    @task(2)
    def load_menu_publico(self):
        self.client.get("/menu/demo", name="/menu/[slug] (SPA)")

    @task(1)
    def load_mozos_page(self):
        self.client.get("/mozos", name="/mozos (SPA)")

    @task(1)
    def load_cocina_page(self):
        self.client.get("/cocina", name="/cocina (SPA)")

    @task(1)
    def load_caja_page(self):
        self.client.get("/caja", name="/caja (SPA)")

    @task(1)
    def load_reportes_page(self):
        self.client.get("/reportes", name="/reportes (SPA)")
