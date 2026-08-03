@echo off
REM ============================================================================
REM  TUWAYKIFOOD - Estacion de impresion (PC de la caja con impresora termica)
REM ----------------------------------------------------------------------------
REM  Lanza Google Chrome en modo impresion SILENCIOSA (--kiosk-printing) sobre
REM  la pantalla /estacion-impresion. Con esto, las comandas que los mozos
REM  envian desde cualquier celular/tablet se imprimen SOLAS en la termica,
REM  sin el dialogo de Windows.
REM
REM  USO: doble clic en este archivo al iniciar el turno. Deja la ventana de
REM       Chrome abierta durante todo el servicio.
REM
REM  Requisitos (una sola vez):
REM   - Impresora termica conectada por USB y puesta como PREDETERMINADA en
REM     Windows (Configuracion > Bluetooth y dispositivos > Impresoras).
REM   - La primera vez, inicia sesion con tu PIN en la ventana que abre.
REM ============================================================================

set "URL=https://food.tuwayki.app/estacion-impresion"
REM Perfil dedicado: asegura que --kiosk-printing se aplique aunque tengas
REM otro Chrome abierto. La sesion (PIN) queda guardada en este perfil.
set "PROFILE=%LOCALAPPDATA%\TuwaykiEstacionImpresion"

set "CHROME=%ProgramFiles%\Google\Chrome\Application\chrome.exe"
if not exist "%CHROME%" set "CHROME=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"
if not exist "%CHROME%" set "CHROME=%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"

if not exist "%CHROME%" (
  echo No se encontro Google Chrome. Instala Chrome o edita la ruta en este .bat.
  pause
  exit /b 1
)

start "" "%CHROME%" --kiosk-printing --start-maximized --user-data-dir="%PROFILE%" --new-window "%URL%"
