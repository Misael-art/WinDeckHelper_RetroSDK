#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para testar componentes retro e verificar suas configurações
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.loader import load_all_components
from core.installer import _verify_installation

def test_retro_components():
    """Testa componentes retro e suas verificações"""
    print("=== Teste de Componentes Retro ===")
    
    # Carrega todos os componentes
    components = load_all_components()
    
    # Filtra componentes retro
    retro_components = {
        k: v for k, v in components.items() 
        if 'Retro' in v.get('category', '') or 'Devkit' in k
    }
    
    print(f"\nEncontrados {len(retro_components)} componentes retro:")
    
    for name, data in retro_components.items():
        print(f"\n--- {name} ---")
        print(f"Categoria: {data.get('category', 'N/A')}")
        print(f"Método de instalação: {data.get('install_method', 'N/A')}")
        
        verify_actions = data.get('verify_actions', [])
        print(f"Verificações definidas: {len(verify_actions)}")
        
        if verify_actions:
            for i, action in enumerate(verify_actions, 1):
                print(f"  {i}. Tipo: {action.get('type')}, Path: {action.get('path', 'N/A')}")
        
        # Testa verificação
        try:
            is_installed = _verify_installation(name, data)
            print(f"Status de instalação: {'INSTALADO' if is_installed else 'NÃO INSTALADO'}")
        except Exception as e:
            print(f"Erro na verificação: {e}")

def test_runtime_components():
    """Testa componentes de runtime"""
    print("\n\n=== Teste de Componentes Runtime ===")
    
    components = load_all_components()
    
    # Filtra componentes de runtime
    runtime_components = {
        k: v for k, v in components.items() 
        if v.get('category', '') == 'Runtimes'
    }
    
    print(f"\nEncontrados {len(runtime_components)} componentes de runtime:")
    
    for name, data in runtime_components.items():
        print(f"\n--- {name} ---")
        print(f"Método de instalação: {data.get('install_method', 'N/A')}")
        
        verify_actions = data.get('verify_actions', [])
        print(f"Verificações definidas: {len(verify_actions)}")
        
        if verify_actions:
            for i, action in enumerate(verify_actions, 1):
                action_type = action.get('type')
                if action_type == 'command_exists':
                    print(f"  {i}. Comando: {action.get('name')}")
                elif action_type == 'file_exists':
                    print(f"  {i}. Arquivo: {action.get('path')}")
                else:
                    print(f"  {i}. Tipo: {action_type}")
        
        # Testa verificação
        try:
            is_installed = _verify_installation(name, data)
            print(f"Status de instalação: {'INSTALADO' if is_installed else 'NÃO INSTALADO'}")
        except Exception as e:
            print(f"Erro na verificação: {e}")

if __name__ == "__main__":
    test_retro_components()
    test_runtime_components()