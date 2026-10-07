@echo off
cd /d "%~dp0"

echo [1/3] Creando entorno virtual .venv...
python -m venv .venv

echo [2/3] Activando entorno virtual y actualizando pip...
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip

echo [3/3] Instalando dependencias desde requirements.txt...
pip install -r requirements.txt

echo.
echo ==================================================
echo Instalacion completada.
echo Ya puedes ejecutar Iniciar_Web_Local.bat
echo ==================================================
pause
