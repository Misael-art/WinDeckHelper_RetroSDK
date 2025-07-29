#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para criar distribuição do Environment Dev
"""

import os
import sys
import shutil
import zipfile
import datetime
from pathlib import Path

def create_distribution():
    """Cria uma distribuição completa do Environment Dev"""
    
    print("🚀 Criando distribuição do Environment Dev...")
    
    # Diretório base do projeto
    project_root = Path(__file__).parent.parent
    
    # Nome da distribuição com timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    dist_name = f"environment_dev_v2.0.0_{timestamp}"
    dist_dir = project_root / "dist" / dist_name
    
    # Cria diretório de distribuição
    dist_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📁 Diretório de distribuição: {dist_dir}")
    
    # Arquivos e diretórios essenciais para incluir
    essential_items = [
        # Código principal
        "env_dev/",
        
        # Scripts de entrada
        "environment_dev.py",
        
        # Documentação
        "README.md",
        "RELEASE_NOTES.md",
        "CORREÇÕES_INSTALAÇÃO_RESUMO.md",
        "LICENSE",
        
        # Testes de validação
        "test_installation_fix.py",
        "test_real_download_installation.py",
        
        # Configurações
        "requirements-dev.txt",
        "setup.cfg",
        
        # Recursos
        "resources/",
        
        # Scripts utilitários
        "scripts/",
    ]
    
    # Diretórios opcionais (incluir se existirem)
    optional_items = [
        "docs/",
        "config/",
        "tools/",
    ]
    
    # Copia arquivos essenciais
    print("📋 Copiando arquivos essenciais...")
    for item in essential_items:
        src_path = project_root / item
        dst_path = dist_dir / item
        
        if src_path.exists():
            if src_path.is_dir():
                shutil.copytree(src_path, dst_path, ignore=shutil.ignore_patterns(
                    '__pycache__', '*.pyc', '*.pyo', '.git*', '*.log'
                ))
                print(f"  ✓ Copiado diretório: {item}")
            else:
                dst_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_path, dst_path)
                print(f"  ✓ Copiado arquivo: {item}")
        else:
            print(f"  ⚠ Item não encontrado: {item}")
    
    # Copia arquivos opcionais
    print("📋 Copiando arquivos opcionais...")
    for item in optional_items:
        src_path = project_root / item
        dst_path = dist_dir / item
        
        if src_path.exists():
            if src_path.is_dir():
                shutil.copytree(src_path, dst_path, ignore=shutil.ignore_patterns(
                    '__pycache__', '*.pyc', '*.pyo', '.git*', '*.log'
                ))
                print(f"  ✓ Copiado diretório opcional: {item}")
            else:
                dst_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_path, dst_path)
                print(f"  ✓ Copiado arquivo opcional: {item}")
    
    # Cria diretórios necessários
    print("📁 Criando diretórios necessários...")
    necessary_dirs = [
        "logs",
        "downloads", 
        "temp",
        "cache",
        "backups"
    ]
    
    for dir_name in necessary_dirs:
        dir_path = dist_dir / dir_name
        dir_path.mkdir(exist_ok=True)
        
        # Cria arquivo .gitkeep para manter o diretório no git
        gitkeep_path = dir_path / ".gitkeep"
        gitkeep_path.touch()
        print(f"  ✓ Criado diretório: {dir_name}")
    
    # Cria arquivo de instalação rápida
    print("📝 Criando scripts de instalação...")
    
    # Script de instalação para Windows
    install_script = dist_dir / "install.bat"
    install_script.write_text(f"""@echo off
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
""", encoding='utf-8')
    
    # Script de execução rápida
    run_script = dist_dir / "run.bat"
    run_script.write_text("""@echo off
echo 🚀 Iniciando Environment Dev...
python env_dev/main.py
pause
""", encoding='utf-8')
    
    # Script de teste
    test_script = dist_dir / "test.bat"
    test_script.write_text("""@echo off
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
""", encoding='utf-8')
    
    print("  ✓ Criados scripts: install.bat, run.bat, test.bat")
    
    # Cria arquivo README da distribuição
    dist_readme = dist_dir / "LEIA-ME.txt"
    dist_readme.write_text(f"""
🚀 ENVIRONMENT DEV v2.0.0 - SISTEMA DE INSTALAÇÃO REAL
=====================================================

📅 Data da distribuição: {datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S")}

🎯 INSTALAÇÃO RÁPIDA
===================

1. Execute: install.bat
2. Execute: run.bat

🧪 VALIDAÇÃO
============

Execute: test.bat

📋 REQUISITOS
=============

- Windows 10/11
- Python 3.8+
- Conexão com internet

🔧 CORREÇÕES DESTA VERSÃO
=========================

✅ Sistema de instalação REAL (não mais simulações)
✅ Downloads funcionais com progresso real
✅ Interface gráfica corrigida
✅ 86+ componentes validados
✅ Sistema de diagnósticos real

📖 DOCUMENTAÇÃO
===============

- README.md - Documentação principal
- RELEASE_NOTES.md - Notas da versão
- CORREÇÕES_INSTALAÇÃO_RESUMO.md - Resumo das correções

🆘 SUPORTE
==========

Se encontrar problemas:
1. Execute test.bat para validar
2. Verifique logs/ para detalhes
3. Consulte a documentação

""", encoding='utf-8')
    
    # Cria arquivo ZIP da distribuição
    print("📦 Criando arquivo ZIP...")
    zip_path = project_root / "dist" / f"{dist_name}.zip"
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(dist_dir):
            # Remove diretórios desnecessários
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
            
            for file in files:
                if not file.endswith(('.pyc', '.pyo', '.log')):
                    file_path = Path(root) / file
                    arc_path = file_path.relative_to(dist_dir)
                    zipf.write(file_path, arc_path)
    
    # Estatísticas da distribuição
    print("\n📊 Estatísticas da distribuição:")
    
    # Conta arquivos
    total_files = 0
    total_size = 0
    
    for root, dirs, files in os.walk(dist_dir):
        for file in files:
            file_path = Path(root) / file
            if file_path.exists():
                total_files += 1
                total_size += file_path.stat().st_size
    
    zip_size = zip_path.stat().st_size
    
    print(f"  📁 Diretório: {dist_dir}")
    print(f"  📄 Arquivos: {total_files}")
    print(f"  💾 Tamanho total: {total_size / 1024 / 1024:.1f} MB")
    print(f"  📦 ZIP: {zip_path}")
    print(f"  🗜️ Tamanho ZIP: {zip_size / 1024 / 1024:.1f} MB")
    print(f"  📉 Compressão: {(1 - zip_size/total_size)*100:.1f}%")
    
    print(f"\n🎉 Distribuição criada com sucesso!")
    print(f"📦 Arquivo: {zip_path}")
    print(f"📁 Pasta: {dist_dir}")
    
    return zip_path, dist_dir

if __name__ == "__main__":
    try:
        zip_path, dist_dir = create_distribution()
        print(f"\n✅ Distribuição pronta para uso!")
        
        # Pergunta se deve abrir o diretório
        try:
            import subprocess
            response = input("\n🔍 Abrir diretório da distribuição? (s/N): ").lower()
            if response in ['s', 'sim', 'y', 'yes']:
                subprocess.run(['explorer', str(dist_dir)], check=False)
        except:
            pass
            
    except Exception as e:
        print(f"\n❌ Erro ao criar distribuição: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)