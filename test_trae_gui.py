#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from core.installer import _verify_installation
from config.loader import load_all_components

def test_trae_detection():
    print("Carregando componentes...")
    components = load_all_components()
    
    # Procurar pelo TRAE AI IDE
    trae_component = None
    for component_name, component in components.items():
        if component_name == 'TRAE AI IDE':
            trae_component = component
            break
    
    print(f"TRAE AI IDE encontrado: {trae_component is not None}")
    
    if trae_component:
        print(f"Verificando instalação...")
        status = _verify_installation('TRAE AI IDE', trae_component)
        print(f"Status de instalação: {status}")
        
        # Mostrar detalhes do componente
        print(f"Detalhes do componente:")
        print(f"  Nome: {trae_component.get('name')}")
        print(f"  Categoria: {trae_component.get('category')}")
        print(f"  Verify Actions: {len(trae_component.get('verify_actions', []))}")
    else:
        print("TRAE AI IDE não encontrado nos componentes carregados")

if __name__ == "__main__":
    test_trae_detection()