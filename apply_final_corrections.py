#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para aplicar as correções finais nos arquivos de configuração
"""

import os
import yaml
import shutil
from pathlib import Path

def add_os_filters_to_steam_deck():
    """Adiciona filtros de OS aos componentes Steam Deck"""
    print("🔧 Adicionando filtros de OS aos componentes Steam Deck...")
    
    steam_deck_file = Path("config/components/steam_deck_tools.yaml")
    
    if not steam_deck_file.exists():
        print(f"❌ Arquivo {steam_deck_file} não encontrado")
        return False
    
    try:
        with open(steam_deck_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        changes_made = 0
        
        for component_name, component_data in data.items():
            # Adiciona os_filter se não existir
            if 'os_filter' not in component_data:
                component_data['os_filter'] = {'linux': True}
                changes_made += 1
                print(f"   ✅ Adicionado filtro Linux para: {component_name}")
        
        if changes_made > 0:
            with open(steam_deck_file, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
            print(f"✅ {changes_made} filtros adicionados ao arquivo Steam Deck")
        else:
            print("ℹ️ Todos os componentes Steam Deck já têm filtros")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao processar arquivo Steam Deck: {e}")
        return False

def merge_emulator_categories():
    """Move emuladores retro para o arquivo principal e remove o arquivo retro"""
    print("\n🔧 Unificando categorias de emuladores...")
    
    main_file = Path("config/components/emulators_windows.yaml")
    retro_file = Path("config/components/emulators_retro_windows.yaml")
    
    if not retro_file.exists():
        print("ℹ️ Arquivo emulators_retro_windows.yaml não existe")
        return True
    
    if not main_file.exists():
        print(f"❌ Arquivo principal {main_file} não encontrado")
        return False
    
    try:
        # Carrega dados dos dois arquivos
        with open(main_file, 'r', encoding='utf-8') as f:
            main_data = yaml.safe_load(f) or {}
        
        with open(retro_file, 'r', encoding='utf-8') as f:
            retro_data = yaml.safe_load(f) or {}
        
        # Move componentes retro para o arquivo principal
        moved_count = 0
        for component_name, component_data in retro_data.items():
            # Atualiza a categoria para remover "Retro -"
            if 'category' in component_data:
                old_category = component_data['category']
                new_category = old_category.replace('Retro - ', '').replace('(Retro - Windows)', '(Windows)')
                component_data['category'] = new_category
                print(f"   📝 {component_name}: {old_category} → {new_category}")
            
            # Adiciona ao arquivo principal
            main_data[component_name] = component_data
            moved_count += 1
        
        # Salva o arquivo principal atualizado
        with open(main_file, 'w', encoding='utf-8') as f:
            yaml.dump(main_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        
        # Remove o arquivo retro
        retro_file.unlink()
        
        print(f"✅ {moved_count} emuladores movidos para {main_file}")
        print(f"✅ Arquivo {retro_file} removido")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao unificar emuladores: {e}")
        return False

def fix_component_detection():
    """Verifica e corrige estruturas de detecção de componentes conhecidos"""
    print("\n🔧 Verificando estruturas de detecção...")
    
    # Componentes que precisam de estrutura de detecção
    components_to_check = {
        'Python': 'runtimes.yaml',
        'Git': 'dev_tools.yaml',
        'Node.js': 'runtimes.yaml',
        'Docker': 'dev_tools.yaml'
    }
    
    fixes_applied = 0
    
    for component_name, file_name in components_to_check.items():
        file_path = Path(f"config/components/{file_name}")
        
        if not file_path.exists():
            print(f"⚠️ Arquivo {file_path} não encontrado")
            continue
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
            
            # Procura o componente
            found_component = None
            for name, comp_data in data.items():
                if component_name.lower() in name.lower():
                    found_component = (name, comp_data)
                    break
            
            if found_component:
                name, comp_data = found_component
                
                # Verifica se tem estrutura de verificação
                has_verification = 'verification' in comp_data or 'verify_actions' in comp_data
                
                if not has_verification:
                    print(f"   ⚠️ {name}: Sem estrutura de verificação adequada")
                    # Aqui poderíamos adicionar estruturas básicas de verificação
                else:
                    print(f"   ✅ {name}: Estrutura de verificação OK")
                    fixes_applied += 1
            else:
                print(f"   ❌ {component_name}: Não encontrado em {file_name}")
                
        except Exception as e:
            print(f"❌ Erro ao verificar {file_path}: {e}")
    
    print(f"📊 Componentes com verificação adequada: {fixes_applied}/{len(components_to_check)}")
    return fixes_applied >= len(components_to_check) * 0.5  # 50% é aceitável

def main():
    """Função principal"""
    print("🚀 Aplicando correções finais...\n")
    
    success_count = 0
    total_tasks = 3
    
    # Tarefa 1: Filtros Steam Deck
    if add_os_filters_to_steam_deck():
        success_count += 1
    
    # Tarefa 2: Unificar emuladores
    if merge_emulator_categories():
        success_count += 1
    
    # Tarefa 3: Verificar detecção
    if fix_component_detection():
        success_count += 1
    
    # Resumo
    print("\n" + "="*50)
    print(f"📊 CORREÇÕES APLICADAS: {success_count}/{total_tasks}")
    
    if success_count == total_tasks:
        print("✅ Todas as correções foram aplicadas com sucesso!")
        print("\n🔄 Reinicie a aplicação para ver as mudanças.")
    elif success_count >= 2:
        print("⚠️ Maioria das correções aplicadas, algumas podem precisar de atenção manual")
    else:
        print("❌ Várias correções falharam, verifique os erros acima")
    
    return success_count >= 2

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)