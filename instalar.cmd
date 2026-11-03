@echo off
rem Doble clic aqui para instalar dam en Windows.
rem Lanza instalar.ps1 sin cambiar la politica de ejecucion de PowerShell del equipo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0instalar.ps1"
pause
