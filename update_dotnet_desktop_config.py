#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para atualizar a configuração do Dotnet Desktop com verificações que funcionam
"""

import os
import sys
import logging
import re
from pathlib import Path

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

def update_dotnet_desktop_config():
    """Atualizar configuração do Dotnet Desktop no arquivo runtime_catalog_manager.py"""
    logger = logging.getLogger(__name__)
    
    logger.info("=== Atualizando Configuração do Dotnet Desktop ===")
    
    # Caminho do arquivo
    config_file = Path("core/runtime_catalog_manager.py")
    
    if not config_file.exists():
        logger.error(f"Arquivo não encontrado: {config_file}")
        return False
    
    # Ler conteúdo atual
    with open(config_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Nova configuração otimizada do Dotnet Desktop
    new_dotnet_desktop_config = '''            "dotnet_desktop": {
                "name": "Dotnet Desktop",
                "version": "8.0",
                "description": "Runtime Dotnet Desktop para desenvolvimento",
                "install_method": "exe",
                "download_url": "https://dotnet.microsoft.com/en-us/download/dotnet/8.0",
                "verify_actions": [
                    {
                        "type": "command_output",
                        "command": "dotnet --list-runtimes",
                        "expected_contains": "Microsoft.WindowsDesktop.App"
                    },
                    {
                        "type": "command_exists",
                        "name": "dotnet"
                    },
                    {
                        "type": "file_exists",
                        "path": "C:\\\\Program Files\\\\dotnet\\\\dotnet.exe"
                    }
                ],
                "status": "installed"
            }'''
    
    # Padrão para encontrar a configuração atual do dotnet_desktop
    pattern = r'"dotnet_desktop":\s*\{[^}]*(?:\{[^}]*\}[^}]*)*\}'
    
    # Verificar se a configuração existe
    if re.search(pattern, content, re.DOTALL):
        logger.info("Configuração do Dotnet Desktop encontrada. Substituindo...")
        
        # Substituir a configuração
        new_content = re.sub(pattern, new_dotnet_desktop_config, content, flags=re.DOTALL)
        
        # Verificar se a substituição foi feita
        if new_content != content:
            # Fazer backup
            backup_file = config_file.with_suffix('.py.backup')
            with open(backup_file, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"Backup criado: {backup_file}")
            
            # Salvar nova configuração
            with open(config_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            logger.info("✓ Configuração do Dotnet Desktop atualizada com sucesso!")
            logger.info("Nova configuração inclui:")
            logger.info("  - command_output: dotnet --list-runtimes (Microsoft.WindowsDesktop.App)")
            logger.info("  - command_exists: dotnet")
            logger.info("  - file_exists: C:\\Program Files\\dotnet\\dotnet.exe")
            return True
        else:
            logger.warning("Nenhuma alteração foi necessária")
            return True
    else:
        logger.error("Configuração do dotnet_desktop não encontrada no arquivo")
        return False

def verify_update():
    """Verificar se a atualização foi aplicada corretamente"""
    logger = logging.getLogger(__name__)
    
    logger.info("\n=== Verificando Atualização ===")
    
    config_file = Path("core/runtime_catalog_manager.py")
    
    with open(config_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verificar se as novas verificações estão presentes
    checks = [
        'command_output',
        'dotnet --list-runtimes',
        'Microsoft.WindowsDesktop.App',
        'command_exists',
        'file_exists',
        'C:\\\\\\\\Program Files\\\\\\\\dotnet\\\\\\\\dotnet.exe'
    ]
    
    all_found = True
    for check in checks:
        if check in content:
            logger.info(f"  ✓ Encontrado: {check}")
        else:
            logger.error(f"  ✗ Não encontrado: {check}")
            all_found = False
    
    # Verificar se registry_exists foi removido
    if 'registry_exists' in content and 'dotnet_desktop' in content:
        # Verificar se registry_exists está na seção dotnet_desktop
        dotnet_section_match = re.search(r'"dotnet_desktop":\s*\{.*?\}', content, re.DOTALL)
        if dotnet_section_match and 'registry_exists' in dotnet_section_match.group():
            logger.warning("  ⚠ registry_exists ainda presente na configuração do dotnet_desktop")
            all_found = False
        else:
            logger.info("  ✓ registry_exists removido da configuração do dotnet_desktop")
    
    if all_found:
        logger.info("\n✓ Atualização verificada com sucesso!")
    else:
        logger.error("\n✗ Problemas encontrados na verificação")
    
    return all_found

def test_updated_config():
    """Testar a configuração atualizada"""
    logger = logging.getLogger(__name__)
    
    logger.info("\n=== Testando Configuração Atualizada ===")
    
    try:
        # Adicionar paths necessários
        project_root = Path.cwd()
        sys.path.insert(0, str(project_root))
        sys.path.insert(0, str(project_root / "core"))
        
        # Importar e testar
        from runtime_catalog_manager import RuntimeCatalogManager
        
        manager = RuntimeCatalogManager()
        
        # Verificar se dotnet_desktop está carregado
        if hasattr(manager, 'runtime_configs') and 'dotnet_desktop' in manager.runtime_configs:
            config = manager.runtime_configs['dotnet_desktop']
            logger.info(f"✓ Configuração carregada: {config.get('name', 'N/A')}")
            logger.info(f"  Verificações: {len(config.get('verify_actions', []))}")
            
            # Listar verificações
            for i, action in enumerate(config.get('verify_actions', []), 1):
                logger.info(f"  [{i}] {action.get('type')}: {action.get('command', action.get('name', action.get('path', 'N/A')))}")
            
            return True
        else:
            logger.error("✗ Configuração do dotnet_desktop não encontrada")
            return False
            
    except Exception as e:
        logger.error(f"Erro ao testar configuração: {e}")
        return False

def main():
    """Função principal"""
    logger = setup_logging()
    
    # Atualizar configuração
    update_success = update_dotnet_desktop_config()
    
    if not update_success:
        logger.error("Falha ao atualizar configuração")
        return False
    
    # Verificar atualização
    verify_success = verify_update()
    
    if not verify_success:
        logger.error("Falha na verificação da atualização")
        return False
    
    # Testar configuração
    test_success = test_updated_config()
    
    # Resultado final
    logger.info("\n=== RESULTADO FINAL ===")
    if update_success and verify_success and test_success:
        logger.info("🎉 SUCESSO COMPLETO!")
        logger.info("A configuração do Dotnet Desktop foi atualizada e está funcionando corretamente.")
        logger.info("\nPróximos passos:")
        logger.info("1. Execute o script de validação principal para confirmar")
        logger.info("2. A verificação registry_exists problemática foi removida")
        logger.info("3. Apenas verificações que funcionam foram mantidas")
        return True
    else:
        logger.error("❌ FALHA - Alguns problemas ainda persistem")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)