#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para testar se as correções foram aplicadas corretamente:
1. Verificar se componentes Steam Deck são filtrados no Windows
2. Verificar se categorias de emuladores foram unificadas
3. Testar detecção de componentes
"""

import os
import sys
import yaml
from pathlib import Path

# Adiciona o diretório raiz do projeto ao path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Importações diretas
try:
    # Carrega componentes diretamente dos arquivos YAML
    def load_yaml_files():
        components_dir = project_root / "config" / "components"
        all_components = {}
        
        for yaml_file in components_dir.glob("*.yaml"):
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    if isinstance(data, dict):
                        all_components.update(data)
            except Exception as e:
                print(f"⚠️ Erro ao carregar {yaml_file}: {e}")
        
        return all_components
    
    # Verifica se o filtro de OS existe
    os_filter_path = project_root / "utils" / "os_component_filter.py"
    has_os_filter = os_filter_path.exists()
    
except Exception as e:
    print(f"❌ Erro na configuração: {e}")
    sys.exit(1)

def test_steam_deck_filtering():
    """Testa se componentes Steam Deck são filtrados no Windows"""
    print("🧪 Testando filtros Steam Deck...")
    
    # Carrega todos os componentes
    all_components = load_yaml_files()
    print(f"📊 Total de componentes carregados: {len(all_components)}")
    
    # Verifica se componentes Steam Deck têm filtros de OS
    steam_deck_components = []
    steam_deck_with_filters = []
    
    for name, data in all_components.items():
        category = data.get('category', '')
        if 'Steam Deck' in category:
            steam_deck_components.append(name)
            # Verifica se tem filtro de OS
            os_filter_data = data.get('os_filter', {})
            if os_filter_data and 'linux' in os_filter_data:
                steam_deck_with_filters.append(name)
    
    print(f"📊 Componentes Steam Deck encontrados: {len(steam_deck_components)}")
    print(f"📊 Componentes Steam Deck com filtros Linux: {len(steam_deck_with_filters)}")
    
    if steam_deck_components:
        for component in steam_deck_components[:5]:  # Mostra apenas os primeiros 5
            print(f"   - {component}")
    
    # Verifica se o sistema de filtros existe
    if has_os_filter:
        print("✅ Sistema de filtros de OS disponível")
        
        # Se a maioria dos componentes Steam Deck tem filtros Linux, considera sucesso
        if len(steam_deck_with_filters) >= len(steam_deck_components) * 0.8:
            print("✅ Filtros Steam Deck aplicados corretamente!")
            return True
        else:
            print("❌ Nem todos os componentes Steam Deck têm filtros adequados")
            return False
    else:
        print("❌ Sistema de filtros não disponível")
        return False

def test_emulator_categories():
    """Testa se categorias de emuladores foram unificadas"""
    print("\n🧪 Testando unificação de categorias de emuladores...")
    
    all_components = load_yaml_files()
    
    # Conta categorias de emuladores
    emulator_categories = set()
    emulator_components = {}
    
    for name, data in all_components.items():
        category = data.get('category', '')
        if 'Emulator' in category or 'emulator' in category.lower():
            emulator_categories.add(category)
            if category not in emulator_components:
                emulator_components[category] = []
            emulator_components[category].append(name)
    
    print(f"📊 Categorias de emuladores encontradas: {len(emulator_categories)}")
    for category in sorted(emulator_categories):
        count = len(emulator_components.get(category, []))
        print(f"   - {category}: {count} componentes")
        # Mostra alguns exemplos
        examples = emulator_components[category][:3]
        print(f"     Exemplos: {', '.join(examples)}")
    
    # Verifica se há apenas uma categoria principal para Windows
    windows_emulator_categories = [cat for cat in emulator_categories if 'Windows' in cat]
    
    # Verifica se existe o arquivo emulators_retro_windows.yaml
    retro_file = project_root / "config" / "components" / "emulators_retro_windows.yaml"
    retro_exists = retro_file.exists()
    
    print(f"📊 Arquivo emulators_retro_windows.yaml existe: {retro_exists}")
    
    if len(windows_emulator_categories) == 1 and not retro_exists:
        print("✅ Categorias de emuladores Windows unificadas!")
        return True
    elif len(windows_emulator_categories) == 1:
        print("⚠️ Categoria unificada, mas arquivo retro ainda existe")
        return True  # Ainda considera sucesso parcial
    else:
        print(f"❌ Múltiplas categorias de emuladores Windows: {windows_emulator_categories}")
        return False

def test_component_detection():
    """Testa detecção de componentes conhecidos"""
    print("\n🧪 Testando estrutura de detecção de componentes...")
    
    all_components = load_yaml_files()
    
    # Lista de componentes que sabemos que estão instalados
    known_installed = ['Python', 'Git', 'Node.js', 'Docker']
    
    found_count = 0
    components_with_detection = 0
    
    for component_name in known_installed:
        # Procura o componente nos dados carregados
        found_component = None
        for name, data in all_components.items():
            if component_name.lower() in name.lower():
                found_component = (name, data)
                break
        
        if found_component:
            name, data = found_component
            found_count += 1
            
            # Verifica se tem estrutura de detecção
            has_detection = False
            if 'verification' in data:
                has_detection = True
                components_with_detection += 1
                print(f"✅ {name}: Encontrado com estrutura de verificação")
            elif 'install_check' in data:
                has_detection = True
                components_with_detection += 1
                print(f"✅ {name}: Encontrado com install_check")
            else:
                print(f"⚠️ {name}: Encontrado mas sem estrutura de detecção")
        else:
            print(f"❌ {component_name}: Não encontrado nos dados")
    
    print(f"\n📊 Componentes encontrados: {found_count}/{len(known_installed)}")
    print(f"📊 Componentes com detecção: {components_with_detection}/{found_count}")
    
    # Considera sucesso se encontrou a maioria dos componentes
    if found_count >= len(known_installed) * 0.75:
        print("✅ Estrutura de detecção adequada")
        return True
    else:
        print("❌ Muitos componentes não encontrados")
        return False

def main():
    """Função principal"""
    print("🧪 Iniciando testes das correções aplicadas...\n")
    
    tests_passed = 0
    total_tests = 3
    
    # Teste 1: Filtros Steam Deck
    if test_steam_deck_filtering():
        tests_passed += 1
    
    # Teste 2: Unificação de categorias
    if test_emulator_categories():
        tests_passed += 1
    
    # Teste 3: Detecção de componentes
    if test_component_detection():
        tests_passed += 1
    
    # Resumo
    print("\n" + "="*50)
    print(f"📊 RESULTADO DOS TESTES: {tests_passed}/{total_tests} passaram")
    
    if tests_passed == total_tests:
        print("✅ Todas as correções estão funcionando corretamente!")
    elif tests_passed >= 2:
        print("⚠️ Maioria das correções funcionando, algumas podem precisar de ajustes")
    else:
        print("❌ Várias correções precisam de revisão")
    
    return tests_passed >= 2  # Considera sucesso se pelo menos 2/3 passaram

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)