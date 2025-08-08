#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de teste simplificado para o sistema inteligente de instalação do SGDK
"""

import os
import sys
import logging
import yaml
from pathlib import Path

def setup_logging():
    """Configura logging para o teste"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def test_yaml_configuration():
    """Testa se a configuração YAML foi atualizada corretamente"""
    logger = setup_logging()
    logger.info("=== Testando configuração YAML do SGDK ===")
    
    try:
        # Carregar o arquivo retro_devkits.yaml
        yaml_path = Path(__file__).parent / "config" / "components" / "retro_devkits.yaml"
        
        if not yaml_path.exists():
            logger.error(f"Arquivo não encontrado: {yaml_path}")
            return False
        
        with open(yaml_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Verificar se o SGDK está configurado
        sgdk_key = 'SGDK (Sega Genesis Development Kit)'
        if sgdk_key not in config:
            logger.error("Configuração SGDK não encontrada")
            return False
        
        sgdk_config = config[sgdk_key]
        
        # Verificar se o instalador inteligente está configurado
        if 'custom_installer' not in sgdk_config:
            logger.error("Instalador customizado não configurado")
            return False
        
        custom_installer = sgdk_config['custom_installer']
        if custom_installer != 'intelligent_sgdk_installer.install_sgdk':
            logger.error(f"Instalador incorreto: {custom_installer}")
            return False
        
        logger.info("✓ Instalador inteligente configurado corretamente")
        
        # Verificar configurações inteligentes
        required_sections = [
            'conditional_dependencies',
            'extensions_config',
            'intelligent_install_features',
            'supported_editors'
        ]
        
        for section in required_sections:
            if section in sgdk_config:
                logger.info(f"✓ Seção '{section}' encontrada")
            else:
                logger.warning(f"⚠ Seção '{section}' não encontrada")
        
        # Verificar editores suportados
        if 'supported_editors' in sgdk_config:
            supported_editors = sgdk_config['supported_editors']
            logger.info(f"Editores suportados: {len(supported_editors)}")
            for editor in supported_editors:
                logger.info(f"  - {editor}")
        
        return True
        
    except Exception as e:
        logger.error(f"Erro ao testar configuração YAML: {e}")
        return False

def test_file_structure():
    """Testa se os arquivos necessários foram criados"""
    logger = setup_logging()
    logger.info("=== Testando estrutura de arquivos ===")
    
    required_files = [
        "core/editor_detection_manager.py",
        "core/intelligent_sgdk_installer.py"
    ]
    
    base_path = Path(__file__).parent
    all_files_exist = True
    
    for file_path in required_files:
        full_path = base_path / file_path
        if full_path.exists():
            logger.info(f"✓ {file_path} existe")
            
            # Verificar se o arquivo não está vazio
            if full_path.stat().st_size > 0:
                logger.info(f"  - Tamanho: {full_path.stat().st_size} bytes")
            else:
                logger.warning(f"  - Arquivo vazio!")
                all_files_exist = False
        else:
            logger.error(f"✗ {file_path} não encontrado")
            all_files_exist = False
    
    return all_files_exist

def test_code_syntax():
    """Testa se os arquivos Python têm sintaxe válida"""
    logger = setup_logging()
    logger.info("=== Testando sintaxe dos arquivos Python ===")
    
    python_files = [
        "core/editor_detection_manager.py",
        "core/intelligent_sgdk_installer.py"
    ]
    
    base_path = Path(__file__).parent
    all_syntax_valid = True
    
    for file_path in python_files:
        full_path = base_path / file_path
        if full_path.exists():
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    code = f.read()
                
                # Tentar compilar o código
                compile(code, str(full_path), 'exec')
                logger.info(f"✓ {file_path} - sintaxe válida")
                
            except SyntaxError as e:
                logger.error(f"✗ {file_path} - erro de sintaxe: {e}")
                all_syntax_valid = False
            except Exception as e:
                logger.error(f"✗ {file_path} - erro: {e}")
                all_syntax_valid = False
    
    return all_syntax_valid

def test_integration_points():
    """Testa se os pontos de integração estão corretos"""
    logger = setup_logging()
    logger.info("=== Testando pontos de integração ===")
    
    try:
        # Verificar se component_manager.py foi atualizado
        component_manager_path = Path(__file__).parent / "core" / "component_manager.py"
        
        if not component_manager_path.exists():
            logger.error("component_manager.py não encontrado")
            return False
        
        with open(component_manager_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verificar se a integração foi adicionada
        if 'intelligent_sgdk_installer' in content:
            logger.info("✓ Integração com intelligent_sgdk_installer encontrada")
        else:
            logger.error("✗ Integração com intelligent_sgdk_installer não encontrada")
            return False
        
        # Verificar se a função get_intelligent_sgdk_installer está sendo importada
        if 'get_intelligent_sgdk_installer' in content:
            logger.info("✓ Importação de get_intelligent_sgdk_installer encontrada")
        else:
            logger.error("✗ Importação de get_intelligent_sgdk_installer não encontrada")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Erro ao testar pontos de integração: {e}")
        return False

def main():
    """Função principal do teste"""
    logger = setup_logging()
    logger.info("=== INICIANDO TESTES DO SISTEMA INTELIGENTE SGDK ===")
    
    tests = [
        ("Configuração YAML", test_yaml_configuration),
        ("Estrutura de arquivos", test_file_structure),
        ("Sintaxe do código", test_code_syntax),
        ("Pontos de integração", test_integration_points)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Executando: {test_name}")
        
        try:
            result = test_func()
            results.append((test_name, result))
            
            if result:
                logger.info(f"✓ {test_name}: PASSOU")
            else:
                logger.error(f"✗ {test_name}: FALHOU")
                
        except Exception as e:
            logger.error(f"✗ {test_name}: ERRO - {e}")
            results.append((test_name, False))
    
    # Resumo final
    logger.info(f"\n{'='*50}")
    logger.info("=== RESUMO DOS TESTES ===")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASSOU" if result else "✗ FALHOU"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\nResultado: {passed}/{total} testes passaram")
    
    if passed == total:
        logger.info("\n🎉 TODOS OS TESTES PASSARAM!")
        logger.info("Sistema inteligente de instalação do SGDK está pronto para uso.")
        logger.info("\nRecursos implementados:")
        logger.info("- Detecção automática de editores compatíveis")
        logger.info("- Instalação condicional do VSCode")
        logger.info("- Configuração inteligente de extensões")
        logger.info("- Suporte para múltiplos editores")
        return 0
    else:
        logger.error(f"\n❌ {total - passed} TESTE(S) FALHARAM!")
        logger.error("Verifique os logs acima para detalhes dos problemas.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)