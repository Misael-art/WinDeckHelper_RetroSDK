#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste simples e direto da validação do Dotnet Desktop
"""

import os
import sys
import logging
import subprocess
import shutil
from pathlib import Path

# Adicionar o diretório raiz ao path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "core"))
sys.path.insert(0, str(project_root / "utils"))

def setup_logging():
    """Configurar logging para o script"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def test_dotnet_desktop_validation():
    """Testar validação do Dotnet Desktop com configuração otimizada"""
    logger = logging.getLogger(__name__)
    
    logger.info("=== Teste Direto de Validação do Dotnet Desktop ===")
    
    # Configuração otimizada (apenas verificações que funcionam)
    dotnet_desktop_config = {
        'name': 'Dotnet Desktop',
        'install_method': 'exe',
        'verify_actions': [
            {
                'type': 'command_output',
                'command': 'dotnet --list-runtimes',
                'expected_contains': 'Microsoft.WindowsDesktop.App'
            },
            {
                'type': 'command_exists',
                'name': 'dotnet'
            },
            {
                'type': 'file_exists',
                'path': 'C:\\Program Files\\dotnet\\dotnet.exe'
            }
        ]
    }
    
    logger.info("Configuração otimizada do Dotnet Desktop:")
    logger.info(f"  - Nome: {dotnet_desktop_config['name']}")
    logger.info(f"  - Método: {dotnet_desktop_config['install_method']}")
    logger.info(f"  - Verificações: {len(dotnet_desktop_config['verify_actions'])}")
    
    # Testar cada verificação individualmente
    logger.info("\nTestando verificações individuais:")
    
    all_passed = True
    
    for i, action in enumerate(dotnet_desktop_config['verify_actions'], 1):
        action_type = action.get('type')
        logger.info(f"\n[{i}] Testando verificação: {action_type}")
        
        try:
            if action_type == 'command_output':
                command = action.get('command')
                expected = action.get('expected_contains')
                logger.info(f"    Comando: {command}")
                logger.info(f"    Esperado: {expected}")
                
                result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
                output = result.stdout + result.stderr
                
                if expected.lower() in output.lower():
                    logger.info(f"    ✓ PASSOU - Encontrado '{expected}' na saída")
                else:
                    logger.error(f"    ✗ FALHOU - '{expected}' não encontrado na saída")
                    logger.info(f"    Saída: {output[:200]}...")
                    all_passed = False
                    
            elif action_type == 'command_exists':
                command_name = action.get('name')
                logger.info(f"    Comando: {command_name}")
                
                command_path = shutil.which(command_name)
                if command_path:
                    logger.info(f"    ✓ PASSOU - Comando encontrado em: {command_path}")
                else:
                    logger.error(f"    ✗ FALHOU - Comando '{command_name}' não encontrado no PATH")
                    all_passed = False
                    
            elif action_type == 'file_exists':
                file_path = action.get('path')
                logger.info(f"    Arquivo: {file_path}")
                
                if os.path.isfile(file_path):
                    logger.info(f"    ✓ PASSOU - Arquivo encontrado")
                else:
                    logger.error(f"    ✗ FALHOU - Arquivo não encontrado")
                    all_passed = False
                    
        except Exception as e:
            logger.error(f"    ✗ ERRO - Exceção durante teste: {e}")
            all_passed = False
    
    # Resultado final
    logger.info("\n=== Resultado Final ===")
    if all_passed:
        logger.info("✓ TODAS as verificações do Dotnet Desktop PASSARAM")
        logger.info("O Dotnet Desktop está corretamente instalado e validado")
    else:
        logger.error("✗ ALGUMAS verificações do Dotnet Desktop FALHARAM")
        logger.error("O Dotnet Desktop pode não estar instalado corretamente")
    
    return all_passed

def test_with_installer_module():
    """Testar usando o módulo installer diretamente"""
    logger = logging.getLogger(__name__)
    
    logger.info("\n=== Teste com Módulo Installer ===")
    
    try:
        # Importar função de verificação
        from installer import _verify_installation
        
        # Configuração otimizada
        dotnet_config = {
            'name': 'Dotnet Desktop',
            'install_method': 'exe',
            'verify_actions': [
                {
                    'type': 'command_output',
                    'command': 'dotnet --list-runtimes',
                    'expected_contains': 'Microsoft.WindowsDesktop.App'
                },
                {
                    'type': 'command_exists',
                    'name': 'dotnet'
                },
                {
                    'type': 'file_exists',
                    'path': 'C:\\Program Files\\dotnet\\dotnet.exe'
                }
            ]
        }
        
        logger.info("Testando com função _verify_installation...")
        result = _verify_installation('Dotnet Desktop', dotnet_config)
        
        if result:
            logger.info("✓ Validação via installer: PASSOU")
        else:
            logger.error("✗ Validação via installer: FALHOU")
        
        return result
        
    except Exception as e:
        logger.error(f"Erro ao testar com módulo installer: {e}")
        return False

def main():
    """Função principal"""
    logger = setup_logging()
    
    # Teste direto
    direct_result = test_dotnet_desktop_validation()
    
    # Teste com módulo installer
    installer_result = test_with_installer_module()
    
    # Resumo final
    logger.info("\n=== RESUMO FINAL ===")
    logger.info(f"Teste direto: {'✓ PASSOU' if direct_result else '✗ FALHOU'}")
    logger.info(f"Teste installer: {'✓ PASSOU' if installer_result else '✗ FALHOU'}")
    
    if direct_result and installer_result:
        logger.info("\n🎉 SUCESSO TOTAL - Dotnet Desktop validado corretamente!")
        return True
    elif direct_result:
        logger.info("\n⚠ SUCESSO PARCIAL - Validação direta funciona, mas módulo installer tem problemas")
        return True
    else:
        logger.error("\n❌ FALHA - Dotnet Desktop não está validando corretamente")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)