@echo off
echo 🧪 Executando testes de validação...
echo.

echo Teste 1: Sistema básico
python test_installation_fix.py
echo.

echo Teste 2: Sistema de download
python test_real_download_installation.py
echo.

echo ✓ Testes concluídos!
pause
