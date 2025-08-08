#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para corrigir o problema de verificação 'registry_exists' não reconhecida
pelo sistema de validação de componentes.

Problemas identificados:
1. Dotnet Desktop falhou porque 'registry_exists' não é um tipo de verificação reconhecido
2. O sistema de validação precisa suportar verificações de registro do Windows
"""

import os
import sys
import logging
from pathlib import Path

# Adicionar o diretório raiz ao path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

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

def check_installer_verification_methods():
    """Verificar os métodos de verificação disponíveis no installer.py"""
    logger = logging.getLogger(__name__)
    
    installer_path = project_root / "core" / "installer.py"
    if not installer_path.exists():
        logger.error(f"Arquivo installer.py não encontrado: {installer_path}")
        return False
    
    logger.info("Verificando métodos de verificação no installer.py...")
    
    with open(installer_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Procurar por métodos de verificação
    verification_methods = []
    lines = content.split('\n')
    
    for i, line in enumerate(lines):
        if 'def _verify_' in line or 'elif verify_type ==' in line:
            verification_methods.append((i+1, line.strip()))
    
    logger.info(f"Métodos de verificação encontrados ({len(verification_methods)}):")
    for line_num, method in verification_methods:
        logger.info(f"  Linha {line_num}: {method}")
    
    # Verificar se registry_exists está implementado
    has_registry = any('registry' in method.lower() for _, method in verification_methods)
    logger.info(f"Suporte a verificação de registro: {'SIM' if has_registry else 'NÃO'}")
    
    return has_registry

def add_registry_verification_support():
    """Adicionar suporte para verificação de registro no installer.py"""
    logger = logging.getLogger(__name__)
    
    installer_path = project_root / "core" / "installer.py"
    
    with open(installer_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verificar se já existe suporte a registry_exists
    if 'registry_exists' in content:
        logger.info("Suporte a 'registry_exists' já existe no installer.py")
        return True
    
    logger.info("Adicionando suporte a verificação 'registry_exists'...")
    
    # Encontrar onde adicionar o novo método
    lines = content.split('\n')
    insert_position = None
    
    for i, line in enumerate(lines):
        if 'elif verify_type == "command_output"' in line:
            # Encontrar o final deste bloco elif
            j = i + 1
            indent_level = len(line) - len(line.lstrip())
            while j < len(lines):
                current_line = lines[j]
                if current_line.strip() == '':
                    j += 1
                    continue
                current_indent = len(current_line) - len(current_line.lstrip())
                if current_indent <= indent_level and current_line.strip().startswith(('elif', 'else')):
                    insert_position = j
                    break
                j += 1
            break
    
    if insert_position is None:
        logger.error("Não foi possível encontrar posição para inserir o código")
        return False
    
    # Código para verificação de registro
    registry_code = '''        elif verify_type == "registry_exists":
            try:
                import winreg
                registry_path = action.get('path', '')
                if not registry_path:
                    logger.warning(f"Caminho do registro não especificado para {component_name}")
                    return False
                
                # Dividir o caminho do registro
                parts = registry_path.split('\\\\', 1)
                if len(parts) != 2:
                    logger.warning(f"Formato de caminho de registro inválido: {registry_path}")
                    return False
                
                root_key_name, subkey_path = parts
                
                # Mapear nomes de chaves raiz para constantes winreg
                root_keys = {
                    'HKEY_LOCAL_MACHINE': winreg.HKEY_LOCAL_MACHINE,
                    'HKLM': winreg.HKEY_LOCAL_MACHINE,
                    'HKEY_CURRENT_USER': winreg.HKEY_CURRENT_USER,
                    'HKCU': winreg.HKEY_CURRENT_USER,
                    'HKEY_CLASSES_ROOT': winreg.HKEY_CLASSES_ROOT,
                    'HKCR': winreg.HKEY_CLASSES_ROOT,
                    'HKEY_USERS': winreg.HKEY_USERS,
                    'HKU': winreg.HKEY_USERS,
                    'HKEY_CURRENT_CONFIG': winreg.HKEY_CURRENT_CONFIG,
                    'HKCC': winreg.HKEY_CURRENT_CONFIG
                }
                
                root_key = root_keys.get(root_key_name.upper())
                if root_key is None:
                    logger.warning(f"Chave raiz do registro desconhecida: {root_key_name}")
                    return False
                
                # Tentar abrir a chave do registro
                try:
                    with winreg.OpenKey(root_key, subkey_path, 0, winreg.KEY_READ):
                        logger.info(f"Registro encontrado: {registry_path}")
                        return True
                except FileNotFoundError:
                    logger.info(f"Registro não encontrado: {registry_path}")
                    return False
                except PermissionError:
                    logger.warning(f"Sem permissão para acessar registro: {registry_path}")
                    return False
                    
            except ImportError:
                logger.warning("Módulo winreg não disponível (não é Windows?)")
                return False
            except Exception as e:
                logger.error(f"Erro ao verificar registro {registry_path}: {e}")
                return False'''
    
    # Inserir o código
    lines.insert(insert_position, registry_code)
    
    # Salvar o arquivo modificado
    backup_path = installer_path.with_suffix('.py.backup')
    if not backup_path.exists():
        logger.info(f"Criando backup: {backup_path}")
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    logger.info(f"Salvando installer.py modificado...")
    with open(installer_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    logger.info("Suporte a 'registry_exists' adicionado com sucesso!")
    return True

def test_registry_verification():
    """Testar a verificação de registro com um exemplo"""
    logger = logging.getLogger(__name__)
    
    try:
        # Importar o módulo installer modificado
        sys.path.insert(0, str(project_root / "core"))
        from installer import Installer
        
        logger.info("Testando verificação de registro...")
        
        # Criar um componente de teste com verificação de registro
        test_component = {
            'name': 'Test Registry',
            'verify_actions': [
                {
                    'type': 'registry_exists',
                    'path': 'HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion'
                }
            ]
        }
        
        installer = Installer()
        result = installer._verify_installation(test_component, test_component)
        
        logger.info(f"Resultado do teste: {'PASSOU' if result else 'FALHOU'}")
        return result
        
    except Exception as e:
        logger.error(f"Erro durante o teste: {e}")
        return False

def main():
    """Função principal"""
    logger = setup_logging()
    
    logger.info("=== Correção de Verificação de Registro ===")
    logger.info("Identificando e corrigindo problema com 'registry_exists'")
    
    # Verificar métodos existentes
    has_registry = check_installer_verification_methods()
    
    if not has_registry:
        logger.info("Adicionando suporte a verificação de registro...")
        if add_registry_verification_support():
            logger.info("Suporte adicionado com sucesso!")
            
            # Testar a implementação
            if test_registry_verification():
                logger.info("✓ Verificação de registro funcionando corretamente")
            else:
                logger.warning("⚠ Teste de verificação de registro falhou")
        else:
            logger.error("Falha ao adicionar suporte a verificação de registro")
            return False
    else:
        logger.info("Suporte a verificação de registro já existe")
    
    logger.info("=== Correção Concluída ===")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)