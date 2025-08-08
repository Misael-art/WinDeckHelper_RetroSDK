#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.yaml_component_detection import YAMLComponentDetectionStrategy

def test_visual_detection():
    """Testa a detecção visual do TRAE AI IDE e WinScript."""
    
    print("=== TESTE DE DETECÇÃO VISUAL ===")
    print()
    
    # Inicializar estratégia
    strategy = YAMLComponentDetectionStrategy()
    print(f"Componentes carregados: {len(strategy.components)}")
    print()
    
    # Testar TRAE AI IDE
    print("🔍 Testando TRAE AI IDE:")
    if 'TRAE AI IDE' in strategy.components:
        component = strategy.components['TRAE AI IDE']
        result = strategy._detect_yaml_component('TRAE AI IDE', component)
        
        if result:
            print(f"✅ TRAE AI IDE detectado com sucesso!")
            print(f"   Status: {result.status}")
            print(f"   Caminho de instalação: {result.install_path}")
            print(f"   Executável: {result.executable_path}")
        else:
            print("❌ TRAE AI IDE não foi detectado")
    else:
        print("❌ TRAE AI IDE não encontrado na configuração")
    
    print()
    
    # Testar WinScript
    print("🔍 Testando WinScript:")
    if 'WinScript' in strategy.components:
        component = strategy.components['WinScript']
        result = strategy._detect_yaml_component('WinScript', component)
        
        if result:
            print(f"✅ WinScript detectado com sucesso!")
            print(f"   Status: {result.status}")
            print(f"   Caminho de instalação: {result.install_path}")
            print(f"   Executável: {result.executable_path}")
        else:
            print("❌ WinScript não foi detectado")
            print("   Verificando caminhos manualmente:")
            
            # Verificar manualmente os caminhos
            import os
            userprofile = os.environ.get('USERPROFILE', '')
            winscript_dir = os.path.join(userprofile, 'winscript')
            winscript_file = os.path.join(userprofile, 'winscript', 'winscript.ps1')
            
            print(f"   Diretório {winscript_dir}: {'✅ Existe' if os.path.exists(winscript_dir) else '❌ Não existe'}")
            print(f"   Arquivo {winscript_file}: {'✅ Existe' if os.path.exists(winscript_file) else '❌ Não existe'}")
    else:
        print("❌ WinScript não encontrado na configuração")
    
    print()
    print("=== TESTE CONCLUÍDO ===")

if __name__ == '__main__':
    test_visual_detection()