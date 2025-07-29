@echo off
echo 🔧 Corrigindo problema de propriedade do Git
echo ==========================================
echo.

echo 📋 Problema identificado: Git detectou propriedade duvidosa do repositório
echo 🔧 Aplicando correção...

echo.
echo Executando comando de correção do Git...
git config --global --add safe.directory "F:/Steamapps/DevProjetos/PC Engines Projects/Environment_dev_Script"

echo.
echo ✅ Correção aplicada!
echo.

echo 🧪 Testando se o problema foi resolvido...
git status

if %errorlevel% equ 0 (
    echo.
    echo ✅ Problema resolvido com sucesso!
    echo 🚀 Agora você pode executar o upload normalmente:
    echo    .\scripts\upload_to_github.ps1
    echo    ou
    echo    git_upload_commands.bat
) else (
    echo.
    echo ❌ Ainda há problemas. Tentando correção adicional...
    echo.
    
    echo Aplicando correção de propriedade do diretório...
    takeown /f "F:\Steamapps\DevProjetos\PC Engines Projects\Environment_dev_Script" /r /d y
    
    echo.
    echo Testando novamente...
    git status
    
    if %errorlevel% equ 0 (
        echo ✅ Problema resolvido!
    ) else (
        echo ❌ Problema persiste. Execute como administrador.
    )
)

echo.
pause