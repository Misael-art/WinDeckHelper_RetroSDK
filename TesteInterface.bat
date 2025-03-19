@echo off
echo =======================================
echo  WinDeckHelper - Teste de Interface
echo =======================================
echo.

REM Verifica se está rodando como administrador
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Executando com privilégios de administrador...
) else (
    echo AVISO: Não está rodando como administrador!
    echo Alguns testes podem falhar sem privilégios adequados.
    echo.
    echo Pressione qualquer tecla para continuar mesmo assim ou feche esta janela.
    pause >nul
)

echo Iniciando testes de interface...
echo.

powershell.exe -ExecutionPolicy Bypass -File .\TesteInterface.ps1 -Interactive -GenerateReport

echo.
echo Testes concluídos!
echo.
echo Para executar diagnóstico completo, use: Diagnostico.bat
echo.

pause 