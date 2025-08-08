#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para corrigir problemas de validação de componentes
Este script integra os componentes dinâmicos (Dotnet Desktop, Dotnet SDK, Anaconda3)
ao sistema de validação principal.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.loader import load_all_components
from core.installer import _verify_installation
from core.runtime_catalog_manager import RuntimeCatalogManager
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_dynamic_component_configs():
    """Cria configurações de componentes dinâmicos baseados no RuntimeCatalogManager"""
    logger.info("=== Criando Configurações de Componentes Dinâmicos ===")
    
    runtime_manager = RuntimeCatalogManager()
    dynamic_components = {}
    
    # Mapear runtimes para componentes
    runtime_mappings = {
        'dotnet_desktop': 'Dotnet Desktop',
        'dotnet_sdk': 'Dotnet Sdk',
        'anaconda': 'Anaconda3'
    }
    
    for runtime_name, component_name in runtime_mappings.items():
        runtime_config = runtime_manager.get_runtime_info(runtime_name)
        if runtime_config:
            # Criar configuração de componente baseada no runtime
            component_config = {
                'category': 'Runtimes',
                'description': runtime_config.description,
                'install_method': 'exe' if runtime_config.installation_type.value == 'exe' else runtime_config.installation_type.value,
                'download_url': runtime_config.download_url,
                'verify_actions': []
            }
            
            # Adicionar verificações baseadas nos comandos de validação
            for cmd in runtime_config.validation_commands:
                if 'dotnet --version' in cmd:
                    component_config['verify_actions'].append({
                        'type': 'command_exists',
                        'name': 'dotnet'
                    })
                elif 'dotnet --list-runtimes' in cmd:
                    component_config['verify_actions'].append({
                        'type': 'command_output',
                        'command': 'dotnet --list-runtimes',
                        'expected_contains': 'Microsoft.WindowsDesktop.App' if 'desktop' in runtime_name else 'Microsoft.NETCore.App',
                        'description': f'Verifica se {runtime_name} está instalado'
                    })
                elif 'conda --version' in cmd:
                    component_config['verify_actions'].append({
                        'type': 'command_exists',
                        'name': 'conda'
                    })
                elif 'python --version' in cmd and runtime_name == 'anaconda':
                    component_config['verify_actions'].append({
                        'type': 'file_exists',
                        'path': '${env:USERPROFILE}\\anaconda3'
                    })
            
            # Adicionar verificações baseadas nas chaves de registro
            for reg_key in runtime_config.registry_keys:
                component_config['verify_actions'].append({
                    'type': 'registry_exists',
                    'path': reg_key,
                    'description': f'Verifica registro do {runtime_name}'
                })
            
            # Adicionar verificações de arquivos executáveis
            for exe_path in runtime_config.executable_paths:
                if exe_path == 'dotnet.exe':
                    component_config['verify_actions'].extend([
                        {
                            'type': 'file_exists',
                            'path': 'C:\\Program Files\\dotnet\\dotnet.exe'
                        },
                        {
                            'type': 'file_exists',
                            'path': 'C:\\Program Files (x86)\\dotnet\\dotnet.exe'
                        }
                    ])
                elif exe_path in ['conda.exe', 'python.exe'] and runtime_name == 'anaconda':
                    component_config['verify_actions'].append({
                        'type': 'file_exists',
                        'path': '${env:USERPROFILE}\\anaconda3\\Scripts\\conda.exe' if 'conda' in exe_path else '${env:USERPROFILE}\\anaconda3\\python.exe'
                    })
            
            # Se não há verificações específicas, adicionar verificação padrão
            if not component_config['verify_actions']:
                if 'dotnet' in runtime_name:
                    component_config['verify_actions'] = [
                        {
                            'type': 'command_exists',
                            'name': 'dotnet'
                        }
                    ]
                elif runtime_name == 'anaconda':
                    component_config['verify_actions'] = [
                        {
                            'type': 'file_exists',
                            'path': '${env:USERPROFILE}\\anaconda3'
                        }
                    ]
            
            dynamic_components[component_name] = component_config
            logger.info(f"✓ Configuração criada para {component_name}")
            logger.info(f"  - Método: {component_config['install_method']}")
            logger.info(f"  - Verificações: {len(component_config['verify_actions'])} ações")
        else:
            logger.warning(f"✗ Runtime {runtime_name} não encontrado no catálogo")
    
    return dynamic_components

def test_component_validation(component_name, component_config):
    """Testa a validação de um componente específico"""
    logger.info(f"\n=== Testando Validação: {component_name} ===")
    
    try:
        # Simular a verificação de instalação
        verify_actions = component_config.get('verify_actions', [])
        
        if not verify_actions:
            logger.warning(f"Nenhuma ação de verificação definida para {component_name}")
            return False
        
        logger.info(f"Executando {len(verify_actions)} verificações...")
        
        for i, action in enumerate(verify_actions, 1):
            action_type = action.get('type')
            logger.info(f"  [{i}] Verificação: {action_type}")
            
            if action_type == 'command_exists':
                cmd_name = action.get('name')
                logger.info(f"      Comando: {cmd_name}")
            elif action_type == 'command_output':
                cmd = action.get('command')
                expected = action.get('expected_contains', '')
                logger.info(f"      Comando: {cmd}")
                logger.info(f"      Esperado: {expected}")
            elif action_type == 'file_exists':
                path = action.get('path')
                logger.info(f"      Arquivo: {path}")
            elif action_type == 'registry_exists':
                path = action.get('path')
                logger.info(f"      Registro: {path}")
        
        # Criar dados do componente para a função de verificação
        component_data = {
            'verify_actions': verify_actions,
            'install_method': component_config.get('install_method', 'exe')
        }
        
        # Usar a função de verificação real
        result = _verify_installation(component_name, component_data)
        
        if result:
            logger.info(f"✓ {component_name}: INSTALADO")
        else:
            logger.info(f"✗ {component_name}: NÃO INSTALADO")
        
        return result
        
    except Exception as e:
        logger.error(f"Erro ao verificar {component_name}: {e}")
        return False

def main():
    """Função principal"""
    logger.info("=== Correção de Validação de Componentes ===")
    
    # Criar configurações dinâmicas
    dynamic_components = create_dynamic_component_configs()
    
    # Testar cada componente dinâmico
    results = {}
    for component_name, component_config in dynamic_components.items():
        results[component_name] = test_component_validation(component_name, component_config)
    
    # Resumo dos resultados
    logger.info("\n=== Resumo dos Resultados ===")
    for component_name, is_installed in results.items():
        status = "INSTALADO" if is_installed else "NÃO INSTALADO"
        logger.info(f"  {component_name}: {status}")
    
    # Verificar componentes existentes para comparação
    logger.info("\n=== Verificação de Componentes Existentes ===")
    existing_components = load_all_components()
    
    test_components = ['Nodejs', 'Powershell7', 'Vcpp Redist']
    for comp_name in test_components:
        if comp_name in existing_components:
            comp_config = existing_components[comp_name]
            verify_actions = comp_config.get('verify_actions', [])
            if verify_actions:
                result = _verify_installation(comp_name, comp_config)
                status = "INSTALADO" if result else "NÃO INSTALADO"
                logger.info(f"  {comp_name}: {status}")
    
    logger.info("\n=== Correção Concluída ===")

if __name__ == "__main__":
    main()