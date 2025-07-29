#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para corrigir bugs críticos do Environment Dev
Executar após a análise completa para resolver problemas imediatos
"""

import os
import sys
import logging
from pathlib import Path

# Configuração do logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def fix_import_duplicates():
    """Remove imports duplicados nos arquivos Python"""
    logger.info("🔧 Corrigindo imports duplicados...")
    
    # Lista de arquivos para verificar
    files_to_check = [
        "env_dev/main.py",
        "env_dev/core/installer.py",
        "env_dev/utils/downloader.py"
    ]
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                # Remove imports duplicados
                seen_imports = set()
                cleaned_lines = []
                
                for line in lines:
                    stripped = line.strip()
                    if stripped.startswith('import ') or stripped.startswith('from '):
                        if stripped not in seen_imports:
                            seen_imports.add(stripped)
                            cleaned_lines.append(line)
                        else:
                            logger.warning(f"Removendo import duplicado em {file_path}: {stripped}")
                    else:
                        cleaned_lines.append(line)
                
                # Escreve o arquivo limpo
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(cleaned_lines)
                    
                logger.info(f"✅ Arquivo {file_path} verificado e limpo")
                
            except Exception as e:
                logger.error(f"❌ Erro ao processar {file_path}: {e}")
        else:
            logger.warning(f"⚠️ Arquivo não encontrado: {file_path}")

def verify_dependencies():
    """Verifica e instala dependências necessárias"""
    logger.info("🔧 Verificando dependências...")
    
    required_packages = [
        'requests',
        'pyyaml', 
        'jsonschema'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            logger.info(f"✅ {package} disponível")
        except ImportError:
            missing_packages.append(package)
            logger.warning(f"❌ {package} não encontrado")
    
    if missing_packages:
        logger.info(f"Instalando pacotes faltantes: {missing_packages}")
        import subprocess
        
        for package in missing_packages:
            try:
                result = subprocess.run([
                    sys.executable, '-m', 'pip', 'install', package
                ], capture_output=True, text=True, check=True)
                logger.info(f"✅ {package} instalado com sucesso")
            except subprocess.CalledProcessError as e:
                logger.error(f"❌ Erro ao instalar {package}: {e}")
                return False
    
    return True

def test_basic_functionality():
    """Testa funcionalidades básicas do projeto"""
    logger.info("🧪 Testando funcionalidades básicas...")
    
    try:
        # Testa importação dos módulos principais
        from env_dev.config.loader import load_all_components
        from env_dev.utils.downloader import download_file
        
        logger.info("✅ Importações principais funcionando")
        
        # Testa carregamento de componentes
        components = load_all_components()
        component_count = len(components)
        logger.info(f"✅ Carregados {component_count} componentes")
        
        if component_count == 0:
            logger.warning("⚠️ Nenhum componente carregado - verificar arquivos YAML")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erro no teste básico: {e}")
        return False

def clean_temp_files():
    """Remove arquivos temporários e obsoletos"""
    logger.info("🧹 Limpando arquivos temporários...")
    
    temp_patterns = [
        "*.pyc",
        "__pycache__",
        "*.tmp",
        "*.log",
        ".pytest_cache"
    ]
    
    import glob
    import shutil
    
    cleaned_count = 0
    
    for pattern in temp_patterns:
        for path in glob.glob(f"**/{pattern}", recursive=True):
            try:
                if os.path.isfile(path):
                    os.remove(path)
                    cleaned_count += 1
                elif os.path.isdir(path):
                    shutil.rmtree(path)
                    cleaned_count += 1
                logger.debug(f"Removido: {path}")
            except Exception as e:
                logger.warning(f"Erro ao remover {path}: {e}")
    
    logger.info(f"✅ {cleaned_count} arquivos temporários removidos")

def main():
    """Função principal do script de correção"""
    logger.info("🚀 Iniciando correção de bugs críticos...")
    logger.info("=" * 50)
    
    success = True
    
    # 1. Corrigir imports duplicados
    try:
        fix_import_duplicates()
    except Exception as e:
        logger.error(f"Erro ao corrigir imports: {e}")
        success = False
    
    # 2. Verificar dependências
    try:
        if not verify_dependencies():
            success = False
    except Exception as e:
        logger.error(f"Erro ao verificar dependências: {e}")
        success = False
    
    # 3. Testar funcionalidades básicas
    try:
        if not test_basic_functionality():
            success = False
    except Exception as e:
        logger.error(f"Erro no teste básico: {e}")
        success = False
    
    # 4. Limpar arquivos temporários
    try:
        clean_temp_files()
    except Exception as e:
        logger.error(f"Erro na limpeza: {e}")
        # Não marca como falha crítica
    
    logger.info("=" * 50)
    if success:
        logger.info("✅ Correção de bugs concluída com sucesso!")
        logger.info("🎯 O projeto está pronto para execução")
        return 0
    else:
        logger.error("❌ Alguns problemas não puderam ser corrigidos")
        logger.error("🔍 Verifique os logs acima para detalhes")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 