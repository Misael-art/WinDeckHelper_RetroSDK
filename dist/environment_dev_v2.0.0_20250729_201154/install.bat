@echo off
echo 🚀 Environment Dev v2.0.0 - Instalação Rápida
echo.

echo Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python não encontrado! Instale Python 3.8+ primeiro.
    echo    Download: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✓ Python encontrado

echo.
echo Instalando dependências...
pip install -r requirements-dev.txt

echo.
echo ✓ Instalação concluída!
echo.
echo Para executar:
echo   python env_dev/main.py
echo.
pause
