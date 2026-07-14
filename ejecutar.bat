@echo off
echo Iniciando Buscador Mercado Publico...
echo.
python src\main.py
if %errorlevel% neq 0 (
  echo.
  echo Ocurrio un error. Revisa el mensaje de arriba y avisale a Claude.
)
echo.
pause
