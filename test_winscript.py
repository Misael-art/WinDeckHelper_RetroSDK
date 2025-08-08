#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from core.installer import _verify_installation
from config.loader import load_all_components

def test_winscript_detection():
    print("Carregando componentes...")
    components = load_all_components()
    
    # Procurar pelo WinScript
    winscript_component = None
    for component_name, component in components.items():
        if component_name == 'WinScript':
            winscript_component = component
            break
    
    print(f"WinScript encontrado: {winscript_component is not None}")
    
    if winscript_component:
        print(f"Verificando instalação...")
        status = _verify_installation('WinScript', winscript_component)
        print(f"Status de instalação: {status}")
        
        print("\nDetalhes do componente:")
        print(f"  Nome: {winscript_component.get('name')}")
        print(f"  Categoria: {winscript_component.get('category')}")
        print(f"  Verify Actions: {len(winscript_component.get('verify_actions', []))}")
    else:
        print("WinScript não foi encontrado nos componentes carregados!")
        print("\nComponentes disponíveis que contêm 'script' no nome:")
        for name in components.keys():
            if 'script' in name.lower():
                print(f"  - {name}")

if __name__ == "__main__":
    test_winscript_detection()