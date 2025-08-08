#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste para verificar se a lógica OR funciona corretamente para outros componentes
com múltiplas verify_actions do mesmo tipo.
"""

import sys
import os
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent))

from core.yaml_component_detection import YAMLComponentDetectionStrategy

def test_multiple_verify_actions():
    """Testa componentes com múltiplas verify_actions."""
    
    with open('multiple_verify_actions_test.txt', 'w', encoding='utf-8') as f:
        f.write("=== TESTE DE COMPONENTES COM MÚLTIPLAS VERIFY_ACTIONS ===\n\n")
        
        # Inicializar estratégia
        strategy = YAMLComponentDetectionStrategy()
        f.write(f"Componentes carregados: {len(strategy.components)}\n\n")
        
        # Encontrar componentes com múltiplas verify_actions do mesmo tipo
        components_with_multiple_actions = []
        
        for name, component in strategy.components.items():
            verify_actions = component.get('verify_actions', [])
            if len(verify_actions) > 1:
                # Agrupar por tipo
                types_count = {}
                for action in verify_actions:
                    action_type = action.get('type')
                    types_count[action_type] = types_count.get(action_type, 0) + 1
                
                # Se algum tipo tem mais de 1 action
                for action_type, count in types_count.items():
                    if count > 1:
                        components_with_multiple_actions.append((name, component, action_type, count))
                        break
        
        f.write(f"Componentes com múltiplas verify_actions do mesmo tipo: {len(components_with_multiple_actions)}\n\n")
        
        # Testar alguns componentes
        for name, component, action_type, count in components_with_multiple_actions[:5]:  # Testar apenas os primeiros 5
            f.write(f"=== TESTANDO: {name} ===\n")
            f.write(f"Tipo de action duplicada: {action_type} ({count} actions)\n")
            
            # Mostrar as actions
            verify_actions = component.get('verify_actions', [])
            actions_of_type = [a for a in verify_actions if a.get('type') == action_type]
            
            f.write(f"Actions do tipo {action_type}:\n")
            for i, action in enumerate(actions_of_type, 1):
                path = action.get('path', '')
                f.write(f"  {i}. {path}\n")
                
                # Expandir e testar
                if '${env:' in path:
                    expanded_path = strategy._expand_env_variables(path)
                    f.write(f"     Expandido: {expanded_path}\n")
                    
                    # Verificar existência
                    if action_type == 'file_exists':
                        from utils import env_checker
                        exists = env_checker.check_file_exists(expanded_path)
                        f.write(f"     Existe: {exists}\n")
            
            # Testar detecção
            detected = strategy._detect_yaml_component(name, component)
            if detected:
                f.write(f"✓ DETECTADO: {detected.executable_path}\n")
            else:
                f.write(f"✗ NÃO DETECTADO\n")
            
            f.write("\n")
        
        # Teste específico do TRAE AI IDE
        f.write("=== TESTE ESPECÍFICO: TRAE AI IDE ===\n")
        if 'TRAE AI IDE' in strategy.components:
            component = strategy.components['TRAE AI IDE']
            detected = strategy._detect_yaml_component('TRAE AI IDE', component)
            
            if detected:
                f.write("✓ TRAE AI IDE detectado com sucesso!\n")
                f.write(f"Executável: {detected.executable_path}\n")
                f.write(f"Instalação: {detected.install_path}\n")
            else:
                f.write("✗ TRAE AI IDE não foi detectado\n")
        
        f.write("\n=== TESTE CONCLUÍDO ===\n")

if __name__ == '__main__':
    test_multiple_verify_actions()
    print("Teste concluído. Verifique o arquivo 'multiple_verify_actions_test.txt' para os resultados.")