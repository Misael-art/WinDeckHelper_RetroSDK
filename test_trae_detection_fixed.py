#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste da detecção do TRAE AI IDE após correção da lógica OR.
"""

import sys
import os
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent))

from core.yaml_component_detection import YAMLComponentDetectionStrategy
from utils import env_checker

def test_trae_detection_fixed():
    """Testa a detecção do TRAE AI IDE após a correção."""
    
    with open('trae_detection_fixed_test.txt', 'w', encoding='utf-8') as f:
        f.write("=== TESTE DE DETECÇÃO DO TRAE AI IDE (APÓS CORREÇÃO) ===\n\n")
        
        # Inicializar estratégia
        strategy = YAMLComponentDetectionStrategy()
        f.write(f"Componentes carregados: {len(strategy.components)}\n\n")
        
        # Verificar se o componente TRAE AI IDE existe
        if 'TRAE AI IDE' in strategy.components:
            f.write("✓ Componente 'TRAE AI IDE' encontrado nos componentes YAML\n")
            component = strategy.components['TRAE AI IDE']
            
            f.write(f"Descrição: {component.get('description', 'N/A')}\n")
            f.write(f"Categoria: {component.get('category', 'N/A')}\n")
            f.write(f"Verify Actions: {len(component.get('verify_actions', []))}\n\n")
            
            # Testar cada verify_action individualmente
            verify_actions = component.get('verify_actions', [])
            for i, action in enumerate(verify_actions, 1):
                action_type = action.get('type')
                path = action.get('path', '')
                
                f.write(f"Verify Action {i}:\n")
                f.write(f"  Tipo: {action_type}\n")
                f.write(f"  Caminho original: {path}\n")
                
                # Expandir variáveis de ambiente
                if '${env:' in path:
                    expanded_path = strategy._expand_env_variables(path)
                    f.write(f"  Caminho expandido: {expanded_path}\n")
                    
                    # Testar se existe
                    if action_type == 'file_exists':
                        exists = env_checker.check_file_exists(expanded_path)
                        f.write(f"  Arquivo existe: {exists}\n")
                        if exists:
                            f.write(f"  ✓ PASSOU\n")
                        else:
                            f.write(f"  ✗ FALHOU\n")
                f.write("\n")
            
            # Testar detecção completa
            f.write("=== TESTE DE DETECÇÃO COMPLETA ===\n")
            detected = strategy._detect_yaml_component('TRAE AI IDE', component)
            
            if detected:
                f.write("✓ TRAE AI IDE DETECTADO COM SUCESSO!\n")
                f.write(f"Nome: {detected.name}\n")
                f.write(f"Caminho do executável: {detected.executable_path}\n")
                f.write(f"Caminho de instalação: {detected.install_path}\n")
                f.write(f"Versão: {detected.version}\n")
                f.write(f"Status: {detected.status}\n")
                f.write(f"Confiança: {detected.confidence}\n")
            else:
                f.write("✗ TRAE AI IDE NÃO FOI DETECTADO\n")
                
        else:
            f.write("✗ Componente 'TRAE AI IDE' NÃO encontrado\n")
        
        # Testar método detect_applications
        f.write("\n=== TESTE DO MÉTODO detect_applications ===\n")
        detected_apps = strategy.detect_applications(['TRAE AI IDE'])
        f.write(f"Aplicações detectadas: {len(detected_apps)}\n")
        
        for app in detected_apps:
            f.write(f"\nAplicação detectada:\n")
            f.write(f"  Nome: {app.name}\n")
            f.write(f"  Executável: {app.executable_path}\n")
            f.write(f"  Instalação: {app.install_path}\n")
            f.write(f"  Status: {app.status}\n")
        
        f.write("\n=== TESTE CONCLUÍDO ===\n")

if __name__ == '__main__':
    test_trae_detection_fixed()
    print("Teste concluído. Verifique o arquivo 'trae_detection_fixed_test.txt' para os resultados.")