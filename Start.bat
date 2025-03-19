@echo off
title WinDeckHelper Launcher
color 0A

echo ========================================
echo          WinDeckHelper Launcher
echo ========================================
echo.

:: Verifica se PowerShell está instalado
where powershell >nul 2>nul
if %errorlevel% neq 0 (
    echo ERRO: PowerShell não encontrado!
    echo Por favor, instale o PowerShell 5.1 ou superior.
    pause
    exit /b 1
)

:: Verifica se está rodando como administrador
net session >nul 2>nul
if %errorlevel% neq 0 (
    echo Solicitando privilégios de administrador...
    powershell -Command "Start-Process '%~dpnx0' -Verb RunAs"
    exit /b
)

echo Verificando ambiente...
echo - Executando como Administrador: OK
echo - PowerShell encontrado: OK
echo.

:: Limpa logs anteriores se existirem
if exist "%~dp0windeckhelper.log" del /f /q "%~dp0windeckhelper.log"

:: Executa o PowerShell launcher
echo Iniciando WinDeckHelper...
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0launcher.ps1"

:: Verifica se houve erro
if %errorlevel% neq 0 (
    color 0C
    echo.
    echo ========================================
    echo              ERRO DETECTADO
    echo ========================================
    echo.
    echo O WinDeckHelper encontrou um erro durante a execução.
    echo Pressione qualquer tecla para ver o log de erros...
    pause >nul
    
    if exist "%~dp0windeckhelper.log" (
        type "%~dp0windeckhelper.log"
    ) else (
        echo ERRO: Arquivo de log não encontrado!
    )
    
    echo.
    echo Para suporte, por favor:
    echo 1. Tire um print desta tela
    echo 2. Abra uma issue no GitHub
    echo 3. Anexe o print e o arquivo de log
    echo.
    pause
    exit /b 1
)

exit /b 0