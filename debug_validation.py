#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para debugar problemas de validação de componentes
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.loader import load_all_components
from core.installer import _verify_installation

def check_specific_components():
    """Verifica componentes específicos mencionados pelo usuário"""
    print("=== Debug de Validação de Componentes ===")
    
    components = load_all_components()
    
    # Componentes específicos mencionados
    target_components = [
        'Anaconda3',
        'Dotnet Desktop',
        'Dotnet Sdk',
        'GBA Devkit',
        'GBDK (Game Boy Development Kit)',
        'NES Development Kit (CC65)',
        'SGDK (Sega Genesis Development Kit)',
        'Retro Devkit Manager'
    ]
    
    print(f"\nVerificando {len(target_components)} componentes específicos:\n")
    
    for component_name in target_components:
        print(f"--- {component_name} ---")
        
        if component_name in components:
            data = components[component_name]
            print(f"✓ Componente encontrado")
            print(f"Categoria: {data.get('category', 'N/A')}")
            print(f"Método de instalação: {data.get('install_method', 'N/A')}")
            
            verify_actions = data.get('verify_actions', [])
            print(f"Verificações definidas: {len(verify_actions)}")
            
            if verify_actions:
                for i, action in enumerate(verify_actions, 1):
                    action_type = action.get('type')
                    if action_type == 'file_exists':
                        path = action.get('path', 'N/A')
                        print(f"  {i}. Verificação de arquivo: {path}")
                        # Verifica se o arquivo existe
                        if os.path.isabs(path):
                            exists = os.path.exists(path)
                        else:
                            exists = os.path.exists(os.path.join(os.getcwd(), path))
                        print(f"     Arquivo existe: {exists}")
                    elif action_type == 'command_exists':
                        cmd = action.get('name', 'N/A')
                        print(f"  {i}. Verificação de comando: {cmd}")
                    else:
                        print(f"  {i}. Tipo: {action_type}")
            
            # Testa verificação oficial
            try:
                is_installed = _verify_installation(component_name, data)
                print(f"Status oficial: {'INSTALADO' if is_installed else 'NÃO INSTALADO'}")
            except Exception as e:
                print(f"Erro na verificação: {e}")
        else:
            print(f"✗ Componente NÃO encontrado na configuração")
            # Busca por nomes similares
            similar = [name for name in components.keys() if component_name.lower() in name.lower() or name.lower() in component_name.lower()]
            if similar:
                print(f"Componentes similares encontrados: {similar}")
        
        print()

def check_python_runtimes():
    """Verifica especificamente os runtimes Python"""
    print("\n=== Verificação de Runtimes Python ===")
    
    components = load_all_components()
    
    python_runtimes = {
        k: v for k, v in components.items() 
        if v.get('install_method') == 'python_runtime'
    }
    
    print(f"\nEncontrados {len(python_runtimes)} runtimes Python:")
    
    for name, data in python_runtimes.items():
        print(f"\n--- {name} ---")
        verify_actions = data.get('verify_actions', [])
        
        if verify_actions:
            for action in verify_actions:
                if action.get('type') == 'file_exists':
                    path = action.get('path')
                    print(f"Verificando arquivo: {path}")
                    exists = os.path.exists(path)
                    print(f"Arquivo existe: {exists}")
                    if exists:
                        print(f"Tamanho do arquivo: {os.path.getsize(path)} bytes")
        
        # Teste de verificação
        try:
            is_installed = _verify_installation(name, data)
            print(f"Status: {'INSTALADO' if is_installed else 'NÃO INSTALADO'}")
        except Exception as e:
            print(f"Erro: {e}")

if __name__ == "__main__":
    check_specific_components()
    check_python_runtimes()