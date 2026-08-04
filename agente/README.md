# Agente de impresión TUWAYKIFOOD

App liviana que corre en la **PC de la caja** del restaurante. Recibe los tickets
desde el sistema en la nube (por internet, saliente/HTTPS) e imprime cada uno en
la impresora que corresponde —**de red (IP) o USB**— según su rol (cocina/caja).
Aparece como **ícono en la bandeja del sistema**.

Con esto no hace falta configurar cada PC ni usar `--kiosk-printing`: el mozo
manda el pedido desde el celular, la comanda sale sola en cocina, y el
comprobante en caja.

## Cómo funciona

```
Sistema en la nube  ──(cola de tickets)──>  Agente (esta PC)  ──>  Impresoras
                        el agente los jala                          cocina / caja
                        por HTTPS cada pocos seg.                    (red o USB)
```

La nube nunca entra a tu red: el agente **sale** a buscar los trabajos. Un solo
agente por local maneja impresoras de red **y** USB a la vez.

## Instalación (una vez por restaurante)

1. **Impresoras en Windows**
   - **USB**: instala la impresora térmica en Windows. Anota su **nombre exacto**
     (*Configuración → Bluetooth y dispositivos → Impresoras*). Para tickets ESC/POS
     conviene el driver **"Generic / Text Only"** o el driver ESC/POS del fabricante.
   - **Red**: anota la **IP** de la impresora (puerto ESC/POS estándar: 9100).

2. **En el sistema (web)**: carga cada impresora (nombre, rol cocina/caja, tipo
   red/USB, IP o nombre Windows) y genera el **token del agente**. *(La pantalla
   de gestión es parte de la Fase 3; por ahora el token se genera desde el
   backend.)*

3. **El agente**
   - Copia `config.example.ini` como **`config.ini`** (junto al `.exe`) y pega el
     token:
     ```ini
     [agente]
     base_url = https://food.tuwayki.app
     token = 1.xxxxxxxxxxxxxxxx
     poll_segundos = 3
     ```
   - Doble clic en `TuwaykifoodAgente.exe`. Aparece el ícono en la bandeja.
   - Para que arranque solo con Windows: `instalar-autostart.bat`.

## El ícono de la bandeja

- 🟢 verde = conectado y al día · 🟡 amarillo = imprimiendo · 🔴 rojo = error o falta token.
- Menú (clic derecho): **Estado**, **Imprimir prueba**, **Reintentar ahora**,
  **Abrir logs**, **Salir**.

## Desarrollo / build

```bat
:: correr en desarrollo (Python 3.10+)
python -m pip install -r requirements.txt
python main.py

:: generar el .exe
build.bat        :: -> dist\TuwaykifoodAgente.exe
```

## Solución de problemas

| Síntoma | Causa / solución |
|---|---|
| Ícono rojo "Falta token" | Completa `token` en `config.ini` y reinicia el agente. |
| Ícono rojo "Error de conexión" | Sin internet o `base_url` mal. Reintenta solo con backoff. |
| No imprime una comanda | Revisa que exista una impresora con ese **rol** en el sistema. Revisa `agente.log`. |
| Sale garabato en vez del ticket | El driver no es ESC/POS. Usa "Generic / Text Only" o el driver del fabricante. |
| No corta el papel | Igual que arriba: driver que no pasa el comando de corte ESC/POS. |
| Acentos raros | El agente reintenta sin acentos automáticamente; para acentos usa driver ESC/POS. |

Los detalles quedan en **`agente.log`** (junto al `.exe`).
