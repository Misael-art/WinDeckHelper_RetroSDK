@echo off
title Teste de Interface - WinDeckHelper
color 0A

echo Testando interface básica do WinDeckHelper...
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0TesteInterface.ps1"

if %errorlevel% neq 0 (
    color 0C
    echo.
    echo ERRO: Não foi possível carregar a interface básica.
    echo Verifique se você tem o .NET Framework instalado.
    echo.
    pause
    exit /b 1
)

exit /b 0 