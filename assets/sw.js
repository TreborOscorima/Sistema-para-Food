/*
 * TUWAYKIFOOD — Service Worker (PWA).
 *
 * Esta app es un POS "siempre online": usa un WebSocket persistente para el
 * estado y bundles JS con hash dinamico de Reflex. Por eso NO cacheamos nada:
 * un cache serviria JS/estado viejo y romperia la app. Este SW existe solo
 * para habilitar la instalacion ("Instalar app" en Chrome/Edge exige un SW
 * con un fetch handler registrado) y hace passthrough puro a la red.
 */

self.addEventListener("install", () => {
  // Tomar control de inmediato al publicar una version nueva del SW.
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    (async () => {
      // Barrido defensivo: si alguna vez existio un cache, lo borramos para
      // no arrastrar assets viejos entre despliegues.
      const keys = await caches.keys();
      await Promise.all(keys.map((k) => caches.delete(k)));
      await self.clients.claim();
    })()
  );
});

self.addEventListener("fetch", (event) => {
  // Passthrough a la red. Tener este handler registrado es lo que habilita
  // instalar la app; a proposito NO interceptamos ni cacheamos para evitar
  // servir versiones desactualizadas del frontend.
  return;
});
