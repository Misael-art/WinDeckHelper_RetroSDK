@echo off
echo Iniciando WinDeckHelper...

:: Executa o PowerShell com privilégios elevados
powershell -Command "Start-Process powershell -Verb RunAs -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File \"%~dp0Windeckhelper.ps1\"' -Wait"

exit /b