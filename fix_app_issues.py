#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para corrigir problemas identificados na aplicação:
1. Filtrar componentes Steam Deck no Windows
2. Unificar categorias de emuladores
3. Sincronizar detecção de componentes na interface
"""

import os
import sys
import yaml
from pathlib import Path

# Adiciona o diretório raiz do projeto ao path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def fix_steam_deck_filtering():
    """Adiciona filtros de SO para componentes Steam Deck"""
    steam_deck_file = project_root / "config" / "components" / "steam_deck_tools.yaml"
    
    if not steam_deck_file.exists():
        print(f"❌ Arquivo não encontrado: {steam_deck_file}")
        return False
    
    try:
        with open(steam_deck_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        # Adiciona filtro de SO para todos os componentes Steam Deck
        modified = False
        for component_name, component_data in data.items():
            if isinstance(component_data, dict):
                # Adiciona supported_os apenas para Linux se não existir
                if 'supported_os' not in component_data:
                    component_data['supported_os'] = ['linux']
                    modified = True
                    print(f"✅ Adicionado filtro Linux para: {component_name}")
        
        if modified:
            with open(steam_deck_file, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
            print(f"✅ Arquivo atualizado: {steam_deck_file}")
        else:
            print(f"ℹ️ Nenhuma modificação necessária em: {steam_deck_file}")
        
        return True
    except Exception as e:
        print(f"❌ Erro ao processar {steam_deck_file}: {e}")
        return False

def unify_emulator_categories():
    """Unifica as categorias de emuladores"""
    emulators_file = project_root / "config" / "components" / "emulators_windows.yaml"
    retro_emulators_file = project_root / "config" / "components" / "emulators_retro_windows.yaml"
    
    if not emulators_file.exists() or not retro_emulators_file.exists():
        print(f"❌ Arquivos de emuladores não encontrados")
        return False
    
    try:
        # Carrega ambos os arquivos
        with open(emulators_file, 'r', encoding='utf-8') as f:
            emulators_data = yaml.safe_load(f)
        
        with open(retro_emulators_file, 'r', encoding='utf-8') as f:
            retro_data = yaml.safe_load(f)
        
        # Unifica as categorias para "Emuladores (Windows)"
        unified_category = "Emuladores (Windows)"
        
        # Atualiza categoria dos emuladores principais
        for component_name, component_data in emulators_data.items():
            if isinstance(component_data, dict):
                component_data['category'] = unified_category
        
        # Atualiza categoria dos retro emuladores e mescla
        for component_name, component_data in retro_data.items():
            if isinstance(component_data, dict):
                component_data['category'] = unified_category
                # Adiciona ao arquivo principal se não existir
                if component_name not in emulators_data:
                    emulators_data[component_name] = component_data
                    print(f"✅ Movido {component_name} para categoria unificada")
        
        # Salva o arquivo unificado
        with open(emulators_file, 'w', encoding='utf-8') as f:
            yaml.dump(emulators_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        
        print(f"✅ Categorias de emuladores unificadas em: {emulators_file}")
        print(f"ℹ️ Considere remover o arquivo: {retro_emulators_file}")
        
        return True
    except Exception as e:
        print(f"❌ Erro ao unificar categorias de emuladores: {e}")
        return False

def fix_component_detection_sync():
    """Corrige a sincronização de detecção de componentes na interface"""
    gui_file = project_root / "gui" / "app_gui_qt.py"
    
    if not gui_file.exists():
        print(f"❌ Arquivo GUI não encontrado: {gui_file}")
        return False
    
    try:
        with open(gui_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Verifica se já tem a correção
        if "self.refresh_component_status()" in content:
            print("ℹ️ Correção de sincronização já aplicada")
            return True
        
        # Adiciona método para atualizar status dos componentes
        refresh_method = '''
    def refresh_component_status(self):
        """Atualiza o status de instalação dos componentes na interface"""
        for i in range(self.components_list.count()):
            item = self.components_list.item(i)
            component_name = item.data(Qt.UserRole)
            
            if component_name and component_name in self.components_data:
                component_data = self.components_data[component_name]
                is_installed = self.check_component_installed(component_name, component_data)
                
                # Atualiza o texto do item
                description = component_data.get('description', 'Sem descrição')
                if is_installed:
                    item.setText(f"  ✅ {component_name} - {description} (Instalado)")
                else:
                    item.setText(f"  ⬜ {component_name} - {description}")
'''
        
        # Encontra onde inserir o método (antes do método install_selected)
        install_method_pos = content.find("def install_selected(self):")
        if install_method_pos == -1:
            print("❌ Não foi possível encontrar o método install_selected")
            return False
        
        # Insere o novo método
        content = content[:install_method_pos] + refresh_method + "\n    " + content[install_method_pos:]
        
        # Adiciona chamada para refresh após populate_components_list
        populate_end = content.find("def populate_components_list(self):")
        if populate_end != -1:
            # Encontra o final do método populate_components_list
            method_start = populate_end
            brace_count = 0
            in_method = False
            end_pos = method_start
            
            for i, char in enumerate(content[method_start:], method_start):
                if char == ':' and not in_method:
                    in_method = True
                    continue
                if in_method:
                    if char == '\n':
                        # Verifica se a próxima linha não está indentada (fim do método)
                        next_line_start = i + 1
                        while next_line_start < len(content) and content[next_line_start] in ' \t':
                            next_line_start += 1
                        if next_line_start < len(content) and content[next_line_start] not in ' \t\n':
                            if not content[next_line_start:].startswith('    '):
                                end_pos = i
                                break
            
            # Adiciona chamada para refresh
            refresh_call = "\n        # Atualiza status de instalação após popular a lista\n        self.refresh_component_status()\n"
            content = content[:end_pos] + refresh_call + content[end_pos:]
        
        # Salva o arquivo modificado
        with open(gui_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Correção de sincronização aplicada em: {gui_file}")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao corrigir sincronização: {e}")
        return False

def main():
    """Função principal"""
    print("🔧 Iniciando correções da aplicação...\n")
    
    success_count = 0
    total_fixes = 3
    
    # 1. Corrigir filtros Steam Deck
    print("1️⃣ Corrigindo filtros Steam Deck...")
    if fix_steam_deck_filtering():
        success_count += 1
    print()
    
    # 2. Unificar categorias de emuladores
    print("2️⃣ Unificando categorias de emuladores...")
    if unify_emulator_categories():
        success_count += 1
    print()
    
    # 3. Corrigir sincronização de detecção
    print("3️⃣ Corrigindo sincronização de detecção...")
    if fix_component_detection_sync():
        success_count += 1
    print()
    
    # Resumo
    print("="*50)
    print(f"📊 RESUMO: {success_count}/{total_fixes} correções aplicadas com sucesso")
    
    if success_count == total_fixes:
        print("✅ Todas as correções foram aplicadas!")
        print("\n📝 Próximos passos:")
        print("   1. Reinicie a aplicação para ver as mudanças")
        print("   2. Teste a detecção de componentes")
        print("   3. Verifique se os emuladores Steam Deck não aparecem no Windows")
        print("   4. Confirme que as categorias de emuladores estão unificadas")
    else:
        print("⚠️ Algumas correções falharam. Verifique os logs acima.")
    
    return success_count == total_fixes

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)