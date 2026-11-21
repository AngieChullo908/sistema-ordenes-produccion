@echo off
cd /d "%~dp0"
if not exist runtime\python.exe (
  echo Falta runtime. Extraiga todo el ZIP o reinstale.
  pause
  exit /b 1
)
runtime\python.exe verificar_entorno.py
if errorlevel 1 (
  echo ERROR: copie el mensaje anterior para revisar el entorno.
  pause
  exit /b 1
)
pause
