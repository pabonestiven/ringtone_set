@echo off
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] No se encontro el entorno virtual en Github\.venv
    echo Por favor, ejecuta primero: instalar.bat
    pause
    exit /b 1
)

:: Iniciar la app directamente y mantener la ventana abierta para ver errores
".venv\Scripts\python.exe" -m pip install audioop-lts requests
".venv\Scripts\python.exe" Scripts\app.py
pause
exit /b
