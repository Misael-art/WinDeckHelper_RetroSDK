#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from core.yaml_component_detection import YAMLComponentDetectionStrategy
    from utils.env_checker import check_file_exists
    
    # Criar a estratégia
    strategy = YAMLComponentDetectionStrategy()
    
    with open('trae_detection_debug.txt', 'w', encoding='utf-8') as f:
        f.write("DEBUG DETECÇÃO DO TRAE\n")
        f.write("=" * 50 + "\n")
        
        # Verificar se o componente TRAE AI IDE existe
        if 'TRAE AI IDE' in strategy.components:
            f.write("✓ Componente 'TRAE AI IDE' encontrado nos componentes YAML\n")
            component = strategy.components['TRAE AI IDE']
            f.write(f"Configuração do componente:\n{component}\n\n")
            
            # Verificar as verify_actions
            if 'verify_actions' in component:
                f.write("Verificando verify_actions:\n")
                for i, action in enumerate(component['verify_actions']):
                    f.write(f"  Action {i+1}: {action}\n")
                    
                    if action.get('type') == 'file_exists':
                        path = action.get('path', '')
                        f.write(f"    Caminho original: {path}\n")
                        
                        # Expandir variáveis de ambiente
                        expanded_path = os.path.expandvars(path)
                        f.write(f"    Caminho expandido: {expanded_path}\n")
                        
                        # Verificar se o arquivo existe
                        exists = check_file_exists(expanded_path)
                        f.write(f"    Arquivo existe: {exists}\n")
                        
                        if exists:
                            f.write(f"    ✓ ARQUIVO ENCONTRADO!\n")
                        else:
                            f.write(f"    ✗ Arquivo não encontrado\n")
                    f.write("\n")
            else:
                f.write("✗ Nenhuma verify_action encontrada\n")
        else:
            f.write("✗ Componente 'TRAE AI IDE' NÃO encontrado\n")
        
        # Testar detecção direta
        f.write("\nTestando detecção direta:\n")
        try:
            detected = strategy.detect_applications(['TRAE AI IDE'])
            f.write(f"Detectados: {len(detected)} aplicações\n")
            for app in detected:
                f.write(f"  - {app.name}: {app.executable_path}\n")
        except Exception as e:
            f.write(f"Erro na detecção: {e}\n")
            import traceback
            f.write(traceback.format_exc())
        
        # Testar com diferentes variações do nome
        f.write("\nTestando com variações do nome:\n")
        test_names = ['Trae', 'TRAE', 'trae', 'Trae AI', 'TRAE AI IDE']
        for name in test_names:
            try:
                detected = strategy.detect_applications([name])
                f.write(f"  '{name}': {len(detected)} detectados\n")
            except Exception as e:
                f.write(f"  '{name}': Erro - {e}\n")
    
    print("Debug concluído! Verifique o arquivo trae_detection_debug.txt")
    
except Exception as e:
    print(f"Erro: {e}")
    import traceback
    traceback.print_exc()