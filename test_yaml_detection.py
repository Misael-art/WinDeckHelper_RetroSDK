#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste específico para YAMLComponentDetectionStrategy
"""

import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.yaml_component_detection import YAMLComponentDetectionStrategy

def test_yaml_detection():
    """Testa especificamente a YAMLComponentDetectionStrategy."""
    print("\n" + "="*60)
    print("TESTE ESPECÍFICO DA YAMLComponentDetectionStrategy")
    print("="*60)
    
    # Criar a estratégia
    strategy = YAMLComponentDetectionStrategy()
    
    print(f"\nComponentes YAML carregados: {len(strategy.components)}")
    
    # Listar alguns componentes para verificar se o Trae está lá
    print("\nPrimeiros 15 componentes carregados:")
    for i, name in enumerate(list(strategy.components.keys())[:15]):
        print(f"  {i+1:2d}. {name}")
    
    # Verificar se o Trae está nos componentes
    trae_components = [name for name in strategy.components.keys() if 'trae' in name.lower()]
    print(f"\nComponentes relacionados ao Trae: {trae_components}")
    
    # Verificar se há componentes com nomes similares
    similar_components = [name for name in strategy.components.keys() if any(word in name.lower() for word in ['ide', 'editor', 'code'])]
    print(f"\nComponentes relacionados a IDEs/Editores (primeiros 10): {similar_components[:10]}")
    
    # Testar detecção com target específico
    print("\n" + "-"*40)
    print("TESTANDO DETECÇÃO COM TARGET ['Trae']")
    print("-"*40)
    
    try:
        detected = strategy.detect_applications(['Trae'])
        print(f"\nResultado da detecção: {len(detected)} aplicações detectadas")
        
        for app in detected:
            print(f"  ✓ {app.name} - {app.executable_path}")
    except Exception as e:
        print(f"Erro na detecção: {e}")
    
    print("\n" + "="*60)
    print("TESTE CONCLUÍDO")
    print("="*60)

if __name__ == "__main__":
    test_yaml_detection()