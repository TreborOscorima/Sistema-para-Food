@echo off
REM ============================================================================
REM  Crea un acceso directo del Agente en la carpeta de Inicio de Windows,
REM  para que arranque solo al encender la PC.
REM ============================================================================
set "EXE=%~dp0dist\TuwaykifoodAgente.exe"
if not exist "%EXE%" set "EXE=%~dp0TuwaykifoodAgente.exe"

if not exist "%EXE%" (
  echo No se encontro TuwaykifoodAgente.exe. Corre primero build.bat.
  pause
  exit /b 1
)

powershell -NoProfile -Command ^
  "$w=New-Object -ComObject WScript.Shell; $lnk=$w.CreateShortcut([Environment]::GetFolderPath('Startup')+'\TUWAYKIFOOD Agente.lnk'); $lnk.TargetPath='%EXE%'; $lnk.WorkingDirectory=Split-Path '%EXE%'; $lnk.Save()"

echo Listo: el agente arrancara automaticamente con Windows.
pause
