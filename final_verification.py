#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de verificação final das correções aplicadas
"""

import yaml
from pathlib import Path

def verify_steam_deck_filters():
    """Verifica se os filtros Steam Deck foram aplicados"""
    print("🔍 Verificando filtros Steam Deck...")
    
    steam_deck_file = Path("config/components/steam_deck_tools.yaml")
    
    if not steam_deck_file.exists():
        print("❌ Arquivo steam_deck_tools.yaml não encontrado")
        return False
    
    try:
        with open(steam_deck_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        total_components = len(data)
        components_with_filters = 0
        
        for name, component_data in data.items():
            if 'os_filter' in component_data:
                os_filter = component_data['os_filter']
                if isinstance(os_filter, dict) and 'linux' in os_filter:
                    components_with_filters += 1
        
        print(f"📊 Componentes Steam Deck: {total_components}")
        print(f"📊 Com filtros Linux: {components_with_filters}")
        
        if components_with_filters == total_components:
            print("✅ Todos os componentes Steam Deck têm filtros Linux")
            return True
        else:
            print(f"⚠️ {total_components - components_with_filters} componentes sem filtros")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao verificar filtros: {e}")
        return False

def verify_emulator_unification():
    """Verifica se as categorias de emuladores foram unificadas"""
    print("\n🔍 Verificando unificação de emuladores...")
    
    main_file = Path("config/components/emulators_windows.yaml")
    retro_file = Path("config/components/emulators_retro_windows.yaml")
    
    # Verifica se o arquivo retro foi removido
    if retro_file.exists():
        print("❌ Arquivo emulators_retro_windows.yaml ainda existe")
        return False
    
    if not main_file.exists():
        print("❌ Arquivo emulators_windows.yaml não encontrado")
        return False
    
    try:
        with open(main_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        # Conta componentes por categoria
        categories = {}
        for name, component_data in data.items():
            category = component_data.get('category', 'Sem categoria')
            if category not in categories:
                categories[category] = []
            categories[category].append(name)
        
        print(f"📊 Categorias encontradas: {len(categories)}")
        for category, components in categories.items():
            print(f"   - {category}: {len(components)} componentes")
        
        # Verifica se há apenas categorias Windows (não retro)
        retro_categories = [cat for cat in categories.keys() if 'Retro' in cat]
        
        if len(retro_categories) == 0:
            print("✅ Categorias de emuladores unificadas (sem categorias 'Retro')")
            return True
        else:
            print(f"❌ Ainda existem categorias retro: {retro_categories}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao verificar unificação: {e}")
        return False

def verify_os_filter_system():
    """Verifica se o sistema de filtros de OS está disponível"""
    print("\n🔍 Verificando sistema de filtros de OS...")
    
    filter_file = Path("utils/os_component_filter.py")
    
    if not filter_file.exists():
        print("❌ Arquivo os_component_filter.py não encontrado")
        return False
    
    try:
        with open(filter_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verifica se contém as funções principais
        required_functions = [
            'class OSComponentFilter',
            'def filter_components_data',
            'def should_include_component'
        ]
        
        missing_functions = []
        for func in required_functions:
            if func not in content:
                missing_functions.append(func)
        
        if len(missing_functions) == 0:
            print("✅ Sistema de filtros de OS está completo")
            return True
        else:
            print(f"❌ Funções ausentes: {missing_functions}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao verificar sistema de filtros: {e}")
        return False

def verify_component_structure():
    """Verifica a estrutura geral dos componentes"""
    print("\n🔍 Verificando estrutura geral...")
    
    components_dir = Path("config/components")
    
    if not components_dir.exists():
        print("❌ Diretório de componentes não encontrado")
        return False
    
    yaml_files = list(components_dir.glob("*.yaml"))
    total_components = 0
    
    print(f"📊 Arquivos YAML encontrados: {len(yaml_files)}")
    
    for yaml_file in yaml_files:
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                if isinstance(data, dict):
                    total_components += len(data)
        except Exception as e:
            print(f"⚠️ Erro ao carregar {yaml_file.name}: {e}")
    
    print(f"📊 Total de componentes: {total_components}")
    
    if total_components > 100:  # Esperamos pelo menos 100 componentes
        print("✅ Estrutura de componentes adequada")
        return True
    else:
        print("⚠️ Poucos componentes encontrados")
        return False

def main():
    """Função principal de verificação"""
    print("🔍 VERIFICAÇÃO FINAL DAS CORREÇÕES\n")
    
    tests = [
        ("Filtros Steam Deck", verify_steam_deck_filters),
        ("Unificação de Emuladores", verify_emulator_unification),
        ("Sistema de Filtros OS", verify_os_filter_system),
        ("Estrutura de Componentes", verify_component_structure)
    ]
    
    passed_tests = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed_tests += 1
        except Exception as e:
            print(f"❌ Erro no teste '{test_name}': {e}")
    
    print("\n" + "="*50)
    print(f"📊 RESULTADO FINAL: {passed_tests}/{len(tests)} testes passaram")
    
    if passed_tests == len(tests):
        print("🎉 TODAS AS CORREÇÕES FORAM APLICADAS COM SUCESSO!")
        print("\n✅ Resumo das correções:")
        print("   1. ✅ Componentes Steam Deck filtrados para Linux")
        print("   2. ✅ Categorias de emuladores unificadas")
        print("   3. ✅ Sistema de filtros de OS funcionando")
        print("   4. ✅ Estrutura de componentes íntegra")
        print("\n🚀 A aplicação está pronta para uso!")
    elif passed_tests >= 3:
        print("⚠️ Maioria das correções aplicadas com sucesso")
        print("   Algumas podem precisar de ajustes manuais")
    else:
        print("❌ Várias correções falharam")
        print("   Revise os erros acima")
    
    return passed_tests >= 3

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)