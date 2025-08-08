#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from core.yaml_component_detection import YAMLComponentDetectionStrategy
    
    # Criar a estratégia
    strategy = YAMLComponentDetectionStrategy()
    
    with open('test_output.txt', 'w', encoding='utf-8') as f:
        f.write("TESTE YAML DETECTION\n")
        f.write("=" * 50 + "\n")
        f.write(f"Componentes carregados: {len(strategy.components)}\n\n")
        
        f.write("Primeiros 20 componentes:\n")
        for i, name in enumerate(list(strategy.components.keys())[:20]):
            f.write(f"  {i+1:2d}. {name}\n")
        
        # Verificar Trae
        trae_components = [name for name in strategy.components.keys() if 'trae' in name.lower()]
        f.write(f"\nComponentes com 'trae': {trae_components}\n")
        
        # Verificar IDEs
        ide_components = [name for name in strategy.components.keys() if any(word in name.lower() for word in ['ide', 'editor', 'code', 'studio'])]
        f.write(f"\nComponentes IDE/Editor (primeiros 15):\n")
        for i, name in enumerate(ide_components[:15]):
            f.write(f"  {i+1:2d}. {name}\n")
        
        # Testar detecção do Trae
        f.write("\nTestando detecção do Trae:\n")
        try:
            detected = strategy.detect_applications(['Trae'])
            f.write(f"Detectados: {len(detected)} aplicações\n")
            for app in detected:
                f.write(f"  - {app.name}: {app.executable_path}\n")
        except Exception as e:
            f.write(f"Erro na detecção: {e}\n")
    
    print("Teste concluído! Verifique o arquivo test_output.txt")
    
except Exception as e:
    print(f"Erro: {e}")
    import traceback
    traceback.print_exc()