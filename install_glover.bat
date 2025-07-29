@echo off
title Assistente de Instalacao GloverWindows
echo.
echo *** AVISO IMPORTANTE ***
echo Este assistente GUIA um processo MANUAL e AVANCADO de dual boot.
echo A modificacao de particoes e configuracoes de boot envolve RISCOS,
echo incluindo PERDA DE DADOS ou impossibilidade de iniciar o sistema.
echo PROCEDA COM CAUTELA E POR SUA CONTA E RISCO. Faca BACKUP dos seus dados!
echo ***********************
echo.
echo === Assistente de Instalacao do GloverWindows ===
echo [1] Executar assistente de preparacao (Guia)
echo [2] Abrir Gerenciamento de Disco (Manual)
echo [3] Abrir/Instalar Grub2Win (Configuracao Manual)

choice /c 123 /n /m "Escolha uma opcao (1-3): "

if errorlevel 3 goto ConfigureGrub
if errorlevel 2 goto ManageDisk
if errorlevel 1 goto RunAssistant

:RunAssistant
echo Executando assistente de instalacao...
powershell -ExecutionPolicy Bypass -File "%~dp0setup_glover.ps1"
goto End

:ManageDisk
echo Abrindo gerenciamento de disco...
diskmgmt.msc
goto End

:ConfigureGrub
echo Verificando instalacao do Grub2Win...

set GRUB2WIN_FOUND=false
set GRUB2WIN_PATH=

if exist "%ProgramFiles%\Grub2Win\grub2win.exe" (
    set GRUB2WIN_FOUND=true
    set GRUB2WIN_PATH="%ProgramFiles%\Grub2Win\grub2win.exe"
) else if exist "%USERPROFILE%\AppData\Local\Grub2Win\grub2win.exe" (
    set GRUB2WIN_FOUND=true
    set GRUB2WIN_PATH="%USERPROFILE%\AppData\Local\Grub2Win\grub2win.exe"
) else if exist "C:\Grub2Win\grub2win.exe" (
    set GRUB2WIN_FOUND=true
    set GRUB2WIN_PATH="C:\Grub2Win\grub2win.exe"
)

if "%GRUB2WIN_FOUND%"=="true" (
    echo Abrindo Grub2Win para configuracao...
    start "" %GRUB2WIN_PATH%
) else (
    echo Grub2Win nao encontrado. Deseja instala-lo agora?
    choice /c SN /n /m "Instalar Grub2Win (S/N)? "
    if errorlevel 2 goto End
    if errorlevel 1 (
        echo Instalando Grub2Win...
        cd /d %~dp0\..\..\
        python environment_dev.py --install Grub2Win
        echo Instalacao concluida. Por favor, execute este assistente novamente.
    )
)

:End
echo.
echo === Configuracao do GloverWindows ===
echo.
echo Lembre-se de seguir estes passos para completar a instalacao:
echo 1. Baixe a ISO do GloverWindows do site oficial
echo 2. Crie uma particao para o GloverWindows (minimo 20GB)
echo 3. Crie uma midia bootavel com a ISO do GloverWindows
echo 4. Instale o GloverWindows na particao criada
echo 5. Configure o Grub2Win para adicionar uma entrada para o GloverWindows
echo.
echo *** LEMBRE-SE: A configuracao incorreta do bootloader (Grub2Win) ***
echo *** pode impedir o acesso ao Windows ou ao GloverWindows.      ***
echo *** Consulte a documentacao do Grub2Win e do GloverWindows.    ***
echo.
echo Pressione qualquer tecla para sair...
pause > nul