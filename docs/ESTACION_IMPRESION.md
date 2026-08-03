# Estación de impresión de comandas

Guía para que las **comandas de cocina se impriman automáticamente** en la
impresora térmica de la caja, sin importar desde qué dispositivo (celular,
tablet, mostrador) el mozo envía el pedido.

## Cómo funciona

- El sistema corre en la nube. La impresora térmica está local, por USB, en la
  PC de la caja.
- Cuando un mozo envía un pedido a cocina, **no imprime desde su celular**: solo
  marca la comanda como lista para cocina en la base de datos.
- La **PC de la caja** tiene abierta la página `/estacion-impresion`, que cada
  pocos segundos detecta las comandas nuevas y las imprime en la térmica.
- Es el **único punto de impresión de comandas**, así que nunca salen tickets
  duplicados.

> Requisito clave: la página `/estacion-impresion` debe estar **abierta** en la
> PC de la caja durante todo el servicio. Si se cierra, no se imprime.

## Configuración de la PC de la caja (una sola vez)

1. **Impresora predeterminada**
   Conecta la térmica por USB y ponla como **impresora predeterminada** en
   Windows: *Configuración → Bluetooth y dispositivos → Impresoras y escáneres*.
   Verifica el tamaño de papel (58 mm u 80 mm) en las propiedades de la
   impresora; debe coincidir con el configurado en el sistema
   (*Configuración → Impresoras*).

2. **Modo de impresión silenciosa (kiosk-printing)**
   Usa el acceso directo `scripts/estacion-impresion-caja.bat` (incluido en el
   proyecto). Lanza Chrome con la opción `--kiosk-printing`, que imprime **sin
   mostrar el diálogo** de Windows — el ticket sale directo.

   Para que arranque solo con Windows, puedes copiar un acceso directo del
   `.bat` en la carpeta de Inicio: presiona `Win + R`, escribe `shell:startup`
   y pega ahí el acceso directo.

3. **Iniciar sesión (primera vez)**
   La primera vez que abras la estación, inicia sesión con el PIN de un usuario
   con rol **Caja**, **Cocina** o **Admin**. La sesión queda guardada en ese
   perfil de Chrome; las próximas veces abre directo.

## Uso diario

1. Al iniciar el turno, doble clic en **`estacion-impresion-caja.bat`**
   (o se abre solo si lo pusiste en Inicio).
2. Deja esa ventana de Chrome abierta. Verás el estado **"Activa — escuchando
   comandas"**, cuántos tickets se imprimieron y la hora de la última impresión.
3. Toca **"Imprimir ticket de prueba"** para confirmar que la impresora
   responde.
4. Listo: cada pedido que un mozo envíe a cocina (desde cualquier dispositivo)
   se imprime solo en la caja.

## Solución de problemas

| Síntoma | Causa probable | Solución |
|---|---|---|
| No sale ningún ticket | La estación no está abierta en la PC de la caja | Abre `/estacion-impresion` en esa PC y déjala abierta |
| Aparece el diálogo de imprimir de Windows | Chrome no se abrió con `--kiosk-printing` | Abre siempre con el `.bat`, no con el ícono normal de Chrome |
| Imprime en otra impresora | La térmica no es la predeterminada | Ponla como predeterminada en Windows |
| El ticket sale con formato raro / cortado | Ancho de papel mal configurado | Ajusta 58/80 mm en *Configuración → Impresoras* y en Windows |
| Salen tickets duplicados | Hay más de una estación/pestaña imprimiendo | Deja una sola PC con `/estacion-impresion` abierta |

## Notas técnicas

- La impresión se dispara desde un **iframe oculto** en el navegador
  (`build_print_script` en `app/services/receipt_service.py`), no desde un popup
  — así no lo bloquea el bloqueador de ventanas emergentes.
- Con `--kiosk-printing`, `window.print()` imprime directo a la impresora
  predeterminada, sin diálogo.
- URL de la estación en producción: `https://food.tuwayki.app/estacion-impresion`
