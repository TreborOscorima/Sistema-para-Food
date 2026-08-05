@echo off
REM ============================================================================
REM  Empaqueta el Agente de impresion TUWAYKIFOOD como un unico .exe (Windows).
REM  Requiere Python 3.10+ instalado.
REM ============================================================================
cd /d "%~dp0"

echo Instalando dependencias...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt || goto :error

echo.
echo Empaquetando con PyInstaller...
REM  --collect-all escpos: python-escpos carga "capabilities.json" en tiempo de
REM  ejecucion via importlib_resources. Sin esto, el .exe arranca y falla con
REM  "[Errno 2] No such file or directory: ...\escpos\capabilities.json".
pyinstaller --noconfirm --onefile --windowed ^
  --name "TuwaykifoodAgente" ^
  --icon "assets\tuwayki.ico" ^
  --add-data "assets;assets" ^
  --collect-all escpos ^
  main.py || goto :error

echo.
echo ============================================================================
echo  Listo: dist\TuwaykifoodAgente.exe
echo  Copia junto al .exe un "config.ini" (ver config.example.ini) con tu token.
echo  Para que arranque con Windows, corre instalar-autostart.bat
echo ============================================================================
pause
exit /b 0

:error
echo.
echo *** Error en el build. Revisa los mensajes de arriba. ***
pause
exit /b 1
