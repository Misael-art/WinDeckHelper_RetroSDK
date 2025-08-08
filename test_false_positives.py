#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from core.installer import _verify_installation
from config.loader import load_all_components

def test_false_positives():
    print("Carregando componentes...")
    components = load_all_components()
    
    print(f"Total de componentes carregados: {len(components)}")
    print("\nVerificando quais componentes estão sendo detectados como instalados...\n")
    
    installed_components = []
    not_installed_components = []
    
    for component_name, component in components.items():
        try:
            status = _verify_installation(component_name, component)
            if status:
                installed_components.append(component_name)
                print(f"✓ INSTALADO: {component_name} ({component.get('category', 'Sem categoria')})")
            else:
                not_installed_components.append(component_name)
        except Exception as e:
            print(f"✗ ERRO ao verificar {component_name}: {e}")
            not_installed_components.append(component_name)
    
    print(f"\n=== RESUMO ===")
    print(f"Componentes detectados como INSTALADOS: {len(installed_components)}")
    print(f"Componentes detectados como NÃO INSTALADOS: {len(not_installed_components)}")
    
    if installed_components:
        print("\n=== COMPONENTES INSTALADOS ===")
        for comp in installed_components:
            print(f"  - {comp}")
    
    # Verificar especificamente TRAE AI IDE e WinScript
    print("\n=== VERIFICAÇÃO ESPECÍFICA ===")
    if 'TRAE AI IDE' in installed_components:
        print("⚠️  TRAE AI IDE está sendo detectado como INSTALADO (possível falso positivo)")
    else:
        print("✓ TRAE AI IDE corretamente detectado como NÃO INSTALADO")
    
    if 'WinScript' in installed_components:
        print("⚠️  WinScript está sendo detectado como INSTALADO (possível falso positivo)")
    else:
        print("✓ WinScript corretamente detectado como NÃO INSTALADO")

if __name__ == "__main__":
    test_false_positives()