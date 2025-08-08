#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from core.yaml_component_detection import YAMLComponentDetectionStrategy
    from utils import env_checker
    
    # Criar a estratégia
    strategy = YAMLComponentDetectionStrategy()
    
    with open('integration_debug.txt', 'w', encoding='utf-8') as f:
        f.write("TESTE DE INTEGRAÇÃO - DEBUG DETALHADO\n")
        f.write("=" * 50 + "\n")
        
        # Acessar componentes carregados
        components = strategy.components
        f.write(f"Componentes carregados: {len(components)}\n\n")
        
        # Encontrar o componente TRAE AI IDE
        trae_component = None
        for name, comp in components.items():
            if name == 'TRAE AI IDE':
                trae_component = comp
                break
        
        if trae_component:
            f.write("COMPONENTE TRAE AI IDE ENCONTRADO:\n")
            f.write(f"Nome: TRAE AI IDE\n")
            f.write(f"Categoria: {trae_component.get('category')}\n")
            f.write(f"Verify Actions: {trae_component.get('verify_actions')}\n\n")
            
            # Testar cada verify_action manualmente
            verify_actions = trae_component.get('verify_actions', [])
            f.write("TESTANDO VERIFY ACTIONS MANUALMENTE:\n")
            
            for i, action in enumerate(verify_actions):
                f.write(f"\nAction {i+1}:\n")
                f.write(f"  Tipo: {action.get('type')}\n")
                f.write(f"  Path original: {action.get('path')}\n")
                
                # Expandir variáveis
                path = action.get('path', '')
                if '${env:' in path:
                    expanded_path = strategy._expand_env_variables(path)
                    f.write(f"  Path expandido: {expanded_path}\n")
                else:
                    expanded_path = path
                    f.write(f"  Path (sem expansão): {expanded_path}\n")
                
                # Testar com env_checker
                if action.get('type') == 'file_exists':
                    exists_env_checker = env_checker.check_file_exists(expanded_path)
                    exists_os = os.path.exists(expanded_path)
                    exists_isfile = os.path.isfile(expanded_path)
                    
                    f.write(f"  env_checker.check_file_exists(): {exists_env_checker}\n")
                    f.write(f"  os.path.exists(): {exists_os}\n")
                    f.write(f"  os.path.isfile(): {exists_isfile}\n")
                    
                    if exists_os and not exists_env_checker:
                        f.write(f"  ⚠️ INCONSISTÊNCIA DETECTADA!\n")
            
            # Testar o método _detect_yaml_component completo
            f.write("\n" + "=" * 30 + "\n")
            f.write("TESTANDO MÉTODO _detect_yaml_component COMPLETO:\n")
            
            result = strategy._detect_yaml_component('TRAE AI IDE', trae_component)
            f.write(f"Resultado _detect_yaml_component: {result}\n")
            
            if result:
                f.write(f"Name: {result.name}\n")
                f.write(f"Executable path: {result.executable_path}\n")
                f.write(f"Install path: {result.install_path}\n")
                f.write(f"Version: {result.version}\n")
                f.write(f"Status: {result.status}\n")
                f.write(f"Confidence: {result.confidence}\n")
        else:
            f.write("COMPONENTE TRAE AI IDE NÃO ENCONTRADO!\n")
    
    print("Teste de integração concluído! Verifique o arquivo integration_debug.txt")
    
except Exception as e:
    print(f"Erro: {e}")
    import traceback
    traceback.print_exc()