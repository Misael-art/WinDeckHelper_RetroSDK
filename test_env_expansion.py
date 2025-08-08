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
    
    with open('env_expansion_test.txt', 'w', encoding='utf-8') as f:
        f.write("TESTE DE EXPANSÃO DE VARIÁVEIS DE AMBIENTE\n")
        f.write("=" * 50 + "\n")
        
        # Testar expansão de variáveis
        test_paths = [
            '${env:LOCALAPPDATA}\\Programs\\TRAE\\TRAE.exe',
            '${env:ProgramFiles}\\TRAE\\TRAE.exe',
            '${env:USERPROFILE}\\Desktop',
            '${env:TEMP}\\test.txt'
        ]
        
        for original_path in test_paths:
            expanded_path = strategy._expand_env_variables(original_path)
            f.write(f"Original: {original_path}\n")
            f.write(f"Expandido: {expanded_path}\n")
            f.write(f"Arquivo existe: {os.path.exists(expanded_path)}\n")
            f.write("-" * 30 + "\n")
        
        # Verificar especificamente o TRAE
        f.write("\nVERIFICAÇÃO ESPECÍFICA DO TRAE:\n")
        trae_path = '${env:LOCALAPPDATA}\\Programs\\TRAE\\TRAE.exe'
        expanded_trae = strategy._expand_env_variables(trae_path)
        f.write(f"Caminho TRAE original: {trae_path}\n")
        f.write(f"Caminho TRAE expandido: {expanded_trae}\n")
        f.write(f"TRAE existe: {os.path.exists(expanded_trae)}\n")
        
        # Verificar variáveis de ambiente
        f.write("\nVARIÁVEIS DE AMBIENTE:\n")
        env_vars = ['LOCALAPPDATA', 'ProgramFiles', 'USERPROFILE', 'TEMP']
        for var in env_vars:
            value = os.environ.get(var, 'NÃO DEFINIDA')
            f.write(f"{var}: {value}\n")
    
    print("Teste de expansão concluído! Verifique o arquivo env_expansion_test.txt")
    
except Exception as e:
    print(f"Erro: {e}")
    import traceback
    traceback.print_exc()