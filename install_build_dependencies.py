#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Instalador de Dependências para Build
Instala todas as dependências necessárias para criar o pacote de deployment.
"""

import subprocess
import sys
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def install_package(package_name, version=None):
    """Instala um pacote Python"""
    try:
        package_spec = f"{package_name}=={version}" if version else package_name
        subprocess.run([
            sys.executable, "-m", "pip", "install", "--upgrade", package_spec
        ], check=True, capture_output=True)
        logger.info(f"✅ Instalado: {package_spec}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Erro ao instalar {package_spec}: {e}")
        return False

def main():
    """Instala todas as dependências necessárias"""
    print("📦 Instalando dependências para build do Environment Dev...")
    print("=" * 60)
    
    # Dependências essenciais para o build
    build_dependencies = [
        ("pyinstaller", "5.13.2"),  # Versão estável
        ("pillow", None),           # Processamento de imagens
        ("pyyaml", None),          # Arquivos YAML
        ("requests", None),         # HTTP requests
        ("psutil", None),          # Informações do sistema
        ("py7zr", None),           # Compressão 7z
        ("setuptools", None),       # Build tools
        ("wheel", None),           # Wheel packages
    ]
    
    # Dependências opcionais para otimização
    optional_dependencies = [
        ("upx", None),             # Compressor de executáveis
        ("auto-py-to-exe", None),  # GUI para PyInstaller
    ]
    
    success_count = 0
    total_count = len(build_dependencies)
    
    logger.info("Instalando dependências essenciais...")
    for package, version in build_dependencies:
        if install_package(package, version):
            success_count += 1
    
    logger.info("Instalando dependências opcionais...")
    for package, version in optional_dependencies:
        install_package(package, version)  # Não conta para o sucesso essencial
    
    # Verificar se PyInstaller foi instalado corretamente
    try:
        result = subprocess.run([
            sys.executable, "-m", "PyInstaller", "--version"
        ], capture_output=True, text=True, check=True)
        logger.info(f"✅ PyInstaller versão: {result.stdout.strip()}")
    except subprocess.CalledProcessError:
        logger.error("❌ PyInstaller não foi instalado corretamente")
        success_count -= 1
    
    print(f"\n📊 Resultado: {success_count}/{total_count} dependências essenciais instaladas")
    
    if success_count == total_count:
        print("✅ Todas as dependências foram instaladas com sucesso!")
        print("\n🎯 Próximos passos:")
        print("1. Execute: python build_deployment.py")
        print("2. Ou execute: python create_deployment_package.py")
        return True
    else:
        print("❌ Algumas dependências falharam na instalação.")
        print("Verifique os erros acima e tente novamente.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)