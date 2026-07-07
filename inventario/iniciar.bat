@echo off
cd /d "%~dp0"
echo Instalando Flask si no esta instalado...
pip install flask --quiet
echo.
echo Iniciando Inventario Punado Sano...
echo Abri tu navegador en: http://localhost:5000
echo Para cerrar la app, presiona Ctrl+C en esta ventana.
echo.
start "" http://localhost:5000
python app.py
pause
