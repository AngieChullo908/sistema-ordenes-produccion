@echo off
cd /d "%~dp0.."
python packaging\preparar_windows.py
if errorlevel 1 exit /b 1
cd packaging
makensis launcher.nsi
if errorlevel 1 exit /b 1
makensis installer.nsi
if errorlevel 1 exit /b 1
echo Instalador generado en la carpeta principal.
pause
