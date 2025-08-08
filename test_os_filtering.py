#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de teste para verificar se o sistema de filtros de OS está funcionando corretamente.
Testa se componentes específicos do Linux/Steam Deck são filtrados no Windows.
"""

import sys
import os
from pathlib import Path

# Adicionar o diretório do projeto ao path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Importar diretamente para evitar problemas com __init__.py
sys.path.insert(0, str(project_root / 'config'))
sys.path.insert(0, str(project_root / 'utils'))

from loader import load_all_components
from os_component_filter import os_filter

def test_os_filtering():
    """Testa o sistema de filtros de OS"""
    print("=== Teste do Sistema de Filtros de OS ===")
    print(f"Sistema operacional atual: {os_filter.current_os}")
    print()
    
    # Carregar todos os componentes
    components = load_all_components()
    print(f"Total de componentes carregados: {len(components)}")
    
    # Verificar se componentes específicos do Steam Deck foram filtrados no Windows
    steam_deck_components = [
        'Heroic Games Launcher (Flatpak)',
        'Lutris (Flatpak)',
        'RetroArch (Flatpak)'
    ]
    
    print("\n=== Verificando filtros de componentes Steam Deck ===")
    for component in steam_deck_components:
        if component in components:
            print(f"❌ ERRO: '{component}' não foi filtrado (deveria ser removido no Windows)")
        else:
            print(f"✅ OK: '{component}' foi corretamente filtrado")
    
    # Verificar categorias específicas
    print("\n=== Verificando filtros de categorias ===")
    categories_found = set()
    for name, data in components.items():
        category = data.get('category', '')
        categories_found.add(category)
    
    steam_deck_categories = [
        'Game Launchers (Steam Deck)',
        'Emulators (Steam Deck)'
    ]
    
    for category in steam_deck_categories:
        if category in categories_found:
            print(f"❌ ERRO: Categoria '{category}' não foi filtrada (deveria ser removida no Windows)")
        else:
            print(f"✅ OK: Categoria '{category}' foi corretamente filtrada")
    
    # Verificar se a categoria unificada de emuladores existe
    print("\n=== Verificando categoria unificada de emuladores ===")
    emulator_category = 'Emuladores (Windows)'
    emulator_components = [name for name, data in components.items() 
                          if data.get('category') == emulator_category]
    
    if emulator_components:
        print(f"✅ OK: Categoria '{emulator_category}' encontrada com {len(emulator_components)} componentes:")
        for comp in sorted(emulator_components):
            print(f"  - {comp}")
    else:
        print(f"❌ ERRO: Categoria '{emulator_category}' não encontrada")
    
    # Listar todas as categorias disponíveis
    print("\n=== Todas as categorias disponíveis ===")
    for category in sorted(categories_found):
        if category:
            count = len([name for name, data in components.items() 
                        if data.get('category') == category])
            print(f"  - {category} ({count} componentes)")

if __name__ == "__main__":
    test_os_filtering()