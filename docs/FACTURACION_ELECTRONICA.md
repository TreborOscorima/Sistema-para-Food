# DISEÑO — Facturación Electrónica (Perú SUNAT · Argentina ARCA)

> **Estado:** Borrador de diseño (Fase 1) · **Fecha:** 2026-08-05
> **Alcance:** Servicio de comprobantes electrónicos **centralizado, multi-país y multi-producto**, administrado desde el **Owner Panel**, consumido por todos los sistemas de la suite (Food, Shop, Ventas, Life…).
> **Origen:** FEAT-06 de `PENDIENTES_TUWAYKIFOOD.md` (marcado "Muy Alta, regulatoria"). Se replantea de un feature de Food a una capacidad transversal.

> ⚠️ **Documento de diseño, no de implementación.** Los detalles finos de cada proveedor (endpoints exactos, formatos de sandbox) se confirman en la Fase 0 contra la documentación oficial. Este doc fija la **arquitectura y los contratos**, que deben ser validados por el equipo y la contadora antes de codear.

---

## 1. Objetivo

Emitir comprobantes electrónicos válidos ante la autoridad fiscal (SUNAT en Perú, ARCA —ex-AFIP— en Argentina) desde cualquiera de los productos de la suite, con:

- **Una sola integración** por país/proveedor, reutilizada por todos los productos.
- **Multi-tenant:** cada empresa cliente emite bajo su propio RUC (PE) / CUIT (AR), con sus propias credenciales y series.
- **Administración centralizada** desde el Owner Panel (alta del emisor, credenciales, series/puntos de venta, activar/desactivar el módulo por empresa).
- **Aislamiento de secretos fiscales** (certificados, tokens, credenciales SOL) fuera de las apps de producto.

## 2. Decisiones ya tomadas

| Decisión | Elección | Motivo |
|---|---|---|
| Dónde vive el código | **Microservicio dedicado** (`comprobantes-service`) | Aísla credenciales, centraliza estado/reintentos, una sola integración por proveedor, administrable desde Owner |
| Proveedor Perú | **Nubefact** (API REST por RUC) | Maduro, simple, ya evaluado |
| Proveedor Argentina | **KeyCAE.ar** | Onboarding self-service multi-tenant: el cliente vincula su CUIT en 1 clic y emite bajo su razón social |
| Alcance | **Multi-tenant** (todo el SaaS) | Cada empresa con su propio emisor |
| Comprobantes MVP | **Boleta + Factura** desde el inicio | Cubre consumidor final y empresas |

Alternativas contempladas y descartadas para el MVP: integración directa con SUNAT/ARCA (UBL/WSFE + firma propia) — máximo control pero esfuerzo y mantenimiento perpetuo desproporcionados frente a un OSE/PSE.

### 2.1 Stack técnico del `comprobantes-service` (decidido)

| Aspecto | Elección | Motivo |
|---|---|---|
| Repo | **Nuevo repo dedicado** `comprobantes-service` en la org | Versionado/deploy propios, no ensucia productos, consumido por todos por igual |
| Framework | **FastAPI** (NO Reflex) | Es una API **headless**, no una UI. Estándar profesional para microservicios REST en Python: async, Pydantic (ya en uso), ideal para colas/reintentos. Importa `tuwayki-core` |
| Base de datos | Propia y chica (config fiscal + log de comprobantes) | Aísla **secretos fiscales** fuera de las apps; cifrados en reposo |
| Cola / reintentos | **Redis** (ya existe `tuwayki_redis` en el stack) | Emisión asíncrona, reintentos con backoff, contingencia; sin infra nueva |
| Despliegue | **Container propio** en el stack Docker existente, red interna | Solo lo llaman los productos (no público), salvo un endpoint **webhook** vía nginx-proxy-manager para estado async del proveedor |
| Constantes fiscales | En **`tuwayki-core`** junto a `countries.py` | Data pura por país (tipos de comprobante, alícuotas) = compartida; la lógica con estado/secretos vive en el servicio |

### 2.2 Enfoque fiscal (decidido, sin contador de por medio)

- **IGV/IVA incluido en el precio = default** (`precio_incluye_impuesto: true`), configurable por tenant. Es el estándar de restaurantes en Perú (precio de carta final). El proveedor calcula base e impuesto desde el precio bruto — sin cálculo manual.
- **Boleta como flujo principal** (consumidor final, sin RUC del cliente); **factura a demanda** cuando el cliente la pide con su RUC.
- **Los proveedores OSE/PSE (Nubefact/KeyCAE) reemplazan la mayor parte de lo que aportaría un contador para *emitir*.** Su onboarding guía la afiliación del RUC a emisión electrónica y las credenciales SOL.
- **Estrategia sin riesgo:** todo se construye y prueba contra el **sandbox** del proveedor (no emite nada real). El contador o el soporte del proveedor solo entra **antes de producción**, no antes de construir. Así se separa "construir" (ahora, sin riesgo) de "cumplir" (después, guiado por el proveedor).

## 3. Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│  PRODUCTOS (consumidores)                                    │
│  Food (:3003) · Shop · Ventas · Life · …                     │
│    al cobrar → POST /v1/comprobantes  (tenant + items)       │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTP (API interna, auth por servicio)
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  comprobantes-service  (microservicio dedicado + DB propia)  │
│                                                              │
│  API:  emitir · anular · consultar · reintentar              │
│  Core: validación fiscal · numeración (serie/correlativo)    │
│        cola de emisión · reintentos · estado                 │
│  Config fiscal por tenant (país, RUC/CUIT, credenciales,     │
│        series/puntos de venta, tipo de contribuyente)        │
│                                                              │
│        ┌──────────────── Adaptadores ────────────────┐       │
│        │  PaisAdapter: Perú (SUNAT) │ Argentina (ARCA)│       │
│        │  ProveedorAdapter:                           │       │
│        │    PE → Nubefact | (apisperu) | SUNAT directo│       │
│        │    AR → KeyCAE   | (TusFacturas) | ARCA direct│      │
│        └──────────────────────────────────────────────┘      │
└───────────────────────────┬─────────────────────────────────┘
                            │ REST del proveedor
                            ▼
                Nubefact / KeyCAE  →  SUNAT / ARCA
                            │
                            ▼  respuesta: número oficial, CDR(PE)/CAE(AR), PDF, XML
                back al servicio → back al producto (imprimir/enviar)

┌─────────────────────────────────────────────────────────────┐
│  Owner Panel (:3002)  — administración                       │
│  Por empresa: alta de emisor, credenciales del proveedor,    │
│  series/puntos de venta, activar módulo "Facturación"        │
└─────────────────────────────────────────────────────────────┘
```

**Principio clave:** los productos **no conocen** SUNAT/ARCA ni a los proveedores. Solo hablan con `comprobantes-service` en un lenguaje neutro. Cambiar de proveedor o agregar un país = un adaptador nuevo, sin tocar los productos.

### 3.1 Fundación existente en `tuwayki-core`

`tuwayki-core` (paquete compartido ya instalado por todos los productos) **ya provee la base multi-país** en `tuwayki_core/countries.py`:

- `SUPPORTED_COUNTRIES` con **10 países** (PE, AR, EC, CO, CL, MX, BO, UY, PY, VE): `tax_id_label` (RUC/CUIT/RUT/NIT/RFC…), `personal_id_label`, longitudes de documento, moneda, símbolo, zona horaria, denominaciones y métodos de pago por país.
- Helpers `get_country_config()`, `get_payment_methods_for_country()`.

**Implicancia para el diseño:** el servicio de comprobantes **reutiliza** este layer para la validación de documento fiscal (RUC vs CUIT, longitudes) y el pivote por país. Lo que **no** cubre hoy `countries.py` y agrega el servicio es la **capa fiscal/emisión**: tipos de comprobante (01/03 PE, A/B/C AR), series/puntos de venta, proveedor OSE/PSE, CDR/CAE, cálculo de impuesto. Sugerencia: las **constantes fiscales por país** (tipos de comprobante, alícuotas, mecanismos de anulación) pueden vivir junto a `countries.py` en el core; la **lógica de emisión con estado y secretos** vive en el microservicio.

> El alcance del core (10 países) confirma que la ambición multi-país del servicio está alineada con la infraestructura existente: PE + AR primero, y los adaptadores fiscales se extienden después (EC/SRI, CO/DIAN, CL/SII, etc.).

## 4. Contrato del servicio (borrador)

Interfaz neutra respecto de país/proveedor. Formas de request/response ilustrativas (se afinan en F1).

### 4.1 Emitir

`POST /v1/comprobantes`

```jsonc
{
  "tenant_id": "food:1",                 // producto:company_id
  "idempotency_key": "food-pedido-1234", // evita duplicados en reintentos
  "tipo": "boleta",                       // "boleta" | "factura" (mapea a 03/01 PE, B/A AR)
  "moneda": "PEN",                        // PEN | ARS
  "cliente": {
    "tipo_doc": "DNI",                    // DNI/RUC (PE) · DNI/CUIT/CUIL (AR)
    "numero": "12345678",
    "razon_social": "Juan Pérez",
    "direccion": "Av. Siempre Viva 123"   // requerido para factura
  },
  "items": [
    {
      "descripcion": "Hamburguesa Clásica",
      "cantidad": 2,
      "precio_unitario": 25.00,           // criterio de IGV/IVA incluido: ver §7
      "codigo": "PROD-15"
    }
  ],
  "descuento_global": 0.00,
  "observaciones": "Mesa 5"
}
```

Respuesta (síncrona si el proveedor responde en línea; ver §6 para asíncrono):

```jsonc
{
  "id": "cmp_abc123",
  "estado": "aceptado",       // aceptado | pendiente | rechazado | error
  "tipo": "boleta",
  "serie": "B001",
  "numero": 245,
  "numero_completo": "B001-245",
  "total": 50.00,
  "gravado": 42.37, "impuesto": 7.63, "impuesto_nombre": "IGV",
  "autorizacion": { "tipo": "CDR", "codigo": "..." },  // CDR (PE) | CAE + vencimiento (AR)
  "pdf_url": "https://.../B001-245.pdf",
  "xml_url": "https://.../B001-245.xml",
  "emitido_at": "2026-08-05T20:00:00Z"
}
```

### 4.2 Anular / consultar / reintentar

- `POST /v1/comprobantes/{id}/anular` — dispara el flujo de anulación del país (§5).
- `GET  /v1/comprobantes/{id}` — estado actual (para polling de emisión asíncrona).
- `POST /v1/comprobantes/{id}/reintentar` — reintenta emisión fallida (rechazo transitorio/contingencia).

## 5. Flujos por país

| Concepto | Perú (SUNAT) | Argentina (ARCA) |
|---|---|---|
| Comprobante consumidor | **Boleta (03)** | **Factura B / C** |
| Comprobante empresa | **Factura (01)** con RUC | **Factura A** con CUIT |
| Autorización | **CDR** de SUNAT | **CAE** + fecha de vencimiento |
| Numeración | Serie + correlativo | Punto de venta + número |
| Anular consumidor | **Resumen diario** de baja (boletas) | **Nota de crédito** |
| Anular empresa | **Comunicación de baja** (facturas) | **Nota de crédito** |
| Envío consumidor | Individual + **resumen diario (RC)** | Individual |

El servicio expone `emitir/anular` neutros; **cada adaptador de país traduce** al mecanismo correcto. Los productos nunca ven "resumen diario" ni "nota de crédito": piden `anular` y el adaptador hace lo que corresponde.

## 6. Emisión síncrona vs asíncrona (contingencia)

Los proveedores suelen responder en línea, pero SUNAT/ARCA pueden demorar o rechazar. El servicio maneja:

- **Cola de emisión** con estado (`pendiente → aceptado | rechazado`).
- **Reintentos** con backoff ante fallas transitorias.
- **Idempotencia** (`idempotency_key`) para no duplicar ante reintentos del producto.
- **Contingencia:** si el proveedor no responde, el producto puede seguir cobrando (ticket interno) y el comprobante se emite/reintenta luego; el estado se refleja en el producto y en el Owner.

## 7. Impuestos (IGV / IVA)

**Decisión a confirmar en F0:** en la práctica de restaurantes peruanos el precio de carta suele ser **IGV incluido**. El servicio debe soportar ambos criterios por tenant:

- `precio_incluye_impuesto: true|false` en la config del emisor.
- El adaptador calcula base gravada e impuesto según el criterio y el porcentaje del país (PE 18% IGV; AR 21%/10.5%/… según alícuota).

Hoy en Food existe config parcial (`ConfigImpresora.porcentaje_iva=18`, `nombre_impuesto`, `mostrar_iva`) — se migra/consume desde la config fiscal centralizada.

## 8. Modelo de datos (comprobantes-service)

### 8.1 `emisor_fiscal` (config por tenant)
| Campo | Notas |
|---|---|
| `tenant_id` | producto:company_id (único) |
| `pais` | PE \| AR |
| `proveedor` | nubefact \| keycae \| … |
| `identificacion` | RUC (PE) \| CUIT (AR) |
| `razon_social`, `direccion_fiscal`, `tipo_contribuyente` | |
| `credenciales` | **cifradas** (token API / usuario+clave del proveedor) |
| `precio_incluye_impuesto` | bool |
| `activo` | gating del módulo |

### 8.2 `serie` / punto de venta
`tenant_id`, `tipo` (boleta/factura), `serie`/`punto_venta`, `correlativo_actual`.

### 8.3 `comprobante` (log de emisión)
`id`, `tenant_id`, `idempotency_key`, `tipo`, `serie`, `numero`, `estado`, `cliente_*`, `total/gravado/impuesto`, `autorizacion` (CDR/CAE), `pdf_url`, `xml_url`, `proveedor_response` (raw), `emitido_at`, `error_detalle`.

## 9. Seguridad de credenciales fiscales

- Credenciales del proveedor y certificados **cifrados en reposo**, nunca en las apps de producto ni en logs.
- Acceso solo desde `comprobantes-service`.
- Alta/rotación desde el Owner Panel (que llama a la API del servicio; el Owner no almacena secretos, los delega al servicio).
- Auditoría de cambios de config fiscal (reusar el patrón de `food_auditoria`).

## 10. Integración con los productos (Food como piloto)

Puntos de cambio en cada producto (empezando por **Food**):

1. **Cliente fiscal:** persistir tipo/número de documento + razón social + dirección (hoy `Cliente` **no** guarda el documento; el lookup DNI/RUC de `apiperu.dev` solo rellena el nombre). → migración: agregar campos fiscales a `Cliente`.
2. **Pedido:** referencia al comprobante emitido (id, número oficial, estado). Los totales/desgloses viven en el servicio, no se duplican.
3. **Caja (UI):** al cobrar, elegir **boleta/factura** + cliente fiscal; llamar al servicio; mostrar estado de emisión; imprimir el **comprobante oficial** (PDF del proveedor o render propio con los datos válidos + QR/hash). Reemplaza al "comprobante de pago" interno actual (que **no** es fiscal).
4. **Reimpresión/anulación:** reusar permisos existentes (`perm_reimprimir`, anulación con motivo).

## 11. Owner Panel

Nueva sección por empresa: **Facturación**
- Alta/edición del emisor (país, proveedor, RUC/CUIT, razón social, dirección).
- Carga de credenciales del proveedor (formulario seguro → API del servicio).
- Gestión de series / puntos de venta.
- Activar/desactivar el módulo "Facturación" (integra con el sistema de módulos por empresa existente, `modulos_empresa.py`).
- Vista de comprobantes emitidos / rechazados y reintentos.

## 12. Plan por fases

| Fase | Entregable | Repos |
|---|---|---|
| **F0** | Cuentas sandbox (Nubefact + KeyCAE); confirmar modelo de credenciales, criterio IGV-incluido y specs de API | — |
| **F1** | Este documento + contrato del servicio + modelo de datos congelados | doc |
| **F2** | `comprobantes-service`: esqueleto + adapter **Perú/Nubefact** en sandbox; emitir boleta+factura end-to-end; guardar número/CDR/PDF/XML | servicio nuevo |
| **F3** | Integrar **Food** (piloto): cliente fiscal persistido, UI de Caja (boleta/factura), emitir, imprimir oficial, estado | Food |
| **F4** | Adapter **Argentina/KeyCAE** (mismo contrato) | servicio |
| **F5** | **Owner Panel**: administración fiscal por empresa + gating de módulo | Owner |
| **F6** | Robustez: anulaciones (baja/resumen PE, NC AR), contingencia, reintentos, reportes; rollout a los demás productos | todos |

## 13. Riesgos y decisiones abiertas

- ~~**Multi-repo:**~~ **Resuelto.** Repos clonados como hermanos bajo `D:\PROYECTOS\` — `Sistema-para-Food` (Food), `Sistema-de-Ventas` (Shop + **Owner Panel**), `Sistema-Gestion-Clinica` (Life), `tuwayki-core`. El `comprobantes-service` es un **repo nuevo** por crear (ver §2.1).
- ~~**Dónde vive/despliega el servicio:**~~ **Resuelto** (§2.1): repo nuevo, FastAPI, DB propia, Redis existente, container en el stack.
- ~~**Criterio de impuesto:**~~ **Resuelto** (§2.2): IGV/IVA incluido = default, configurable por tenant.
- **Onboarding fiscal por tenant:** cada empresa debe afiliarse a emisión electrónica y tener credenciales válidas ante SUNAT/ARCA. Estrategia: apoyarse en el onboarding del proveedor (KeyCAE 1-clic en AR; guía de Nubefact en PE). Definir la UX de alta en el Owner Panel (F5).
- **Costos del proveedor:** por documento / por RUC / mensual — confirmar en F0 y definir si se traslada al plan del tenant.
- **Validación previa a producción:** probar en **sandbox/homologación** de cada proveedor; el contador o el soporte del proveedor entra **solo antes de ir a producción**, no antes de construir.

## 14. Fuentes (investigación Argentina)

- [KeyCAE.ar — Facturación electrónica ARCA por API REST (multi-tenant)](https://keycae.ar/)
- [TusFacturasAPP — API Factura electrónica AFIP/ARCA](https://developers.tusfacturas.app/)
- [Facturación Electrónica ARCA 2026 — Guía (Develop Argentina)](https://developargentina.com/blog/facturacion-electronica-arca-guia-completa-2026)
- [API de facturación electrónica ARCA para POS y ecommerce (Sistemas 360)](https://sistemas360.ar/public/blog/api-de-facturacion-electronica-arca-para-sistemas-pos-y-ecommerce)
