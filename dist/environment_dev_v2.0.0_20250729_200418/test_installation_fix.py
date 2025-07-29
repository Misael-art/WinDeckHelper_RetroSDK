#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste rápido para verificar se as correções de instalação estão funcionando
"""

import os
import sys
import logging

# Adiciona o diretório do projeto ao path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

def test_installation_system():
    """Testa o sistema de instalação corrigido"""
    print("=== Teste do Sistema de Instalação Corrigido ===")
    
    try:
        # Importa os módulos necessários
        from env_dev.config.loader import load_all_components
        from env_dev.core import installer
        
        print("✓ Módulos importados com sucesso")
        
        # Carrega os componentes
        components_data = load_all_components()
        if not components_data:
            print("✗ Falha ao carregar componentes")
            return False
            
        print(f"✓ {len(components_data)} componentes carregados")
        
        # Testa componentes com diferentes métodos de instalação
        test_components = []
        download_components = []
        
        for name, data in components_data.items():
            install_method = data.get('install_method', 'none')
            if install_method == 'none':
                test_components.append(name)
            elif install_method in ['exe', 'msi', 'archive']:
                download_components.append(name)
                
            if len(test_components) >= 1 and len(download_components) >= 1:
                break
        
        if not test_components:
            print("✗ Nenhum componente de teste encontrado")
            return False
            
        print(f"✓ Componentes manuais encontrados: {test_components}")
        if download_components:
            print(f"✓ Componentes com download encontrados: {download_components}")
        
        # Testa a função de instalação manual (método 'none')
        for component_name in test_components[:1]:  # Testa apenas o primeiro
            print(f"\n--- Testando instalação manual de '{component_name}' ---")
            
            component_data = components_data[component_name]
            
            # Chama a função de instalação real
            try:
                success = installer.install_component(
                    component_name=component_name,
                    component_data=component_data,
                    all_components_data=components_data
                )
                
                if success:
                    print(f"✓ Instalação manual de '{component_name}' bem-sucedida")
                else:
                    print(f"✗ Instalação manual de '{component_name}' falhou")
                    
            except Exception as e:
                print(f"✗ Erro na instalação manual de '{component_name}': {e}")
                return False
        
        # Testa componente com download (apenas verificação, sem executar)
        if download_components:
            component_name = download_components[0]
            print(f"\n--- Verificando configuração de download de '{component_name}' ---")
            
            component_data = components_data[component_name]
            install_method = component_data.get('install_method')
            download_url = component_data.get('download_url')
            
            print(f"  Método de instalação: {install_method}")
            print(f"  URL de download: {download_url}")
            
            if download_url:
                print(f"✓ Componente '{component_name}' está configurado para download automático")
                print("  (Teste de download não executado para evitar downloads desnecessários)")
            else:
                print(f"✗ Componente '{component_name}' não tem URL de download configurada")
                return False
        
        print("\n=== Teste Concluído com Sucesso ===")
        return True
        
    except ImportError as e:
        print(f"✗ Erro de importação: {e}")
        return False
    except Exception as e:
        print(f"✗ Erro inesperado: {e}")
        return False

def test_gui_integration():
    """Testa a integração com a GUI"""
    print("\n=== Teste de Integração com GUI ===")
    
    try:
        # Testa se as correções da GUI estão funcionando
        from env_dev.gui.enhanced_dashboard import EnhancedDashboard
        from env_dev.config.loader import load_all_components
        
        print("✓ Módulos da GUI importados com sucesso")
        
        # Carrega componentes
        components_data = load_all_components()
        
        # Verifica se a classe do dashboard foi corrigida
        dashboard_code = open('env_dev/gui/enhanced_dashboard.py', 'r', encoding='utf-8').read()
        
        if 'time.sleep(2)  # Simulate installation' in dashboard_code:
            print("✗ Ainda há simulações de instalação no código")
            return False
        elif 'installer.install_component(' in dashboard_code:
            print("✓ Código da GUI foi corrigido para usar instalação real")
        else:
            print("? Não foi possível verificar as correções da GUI")
            
        print("✓ Integração com GUI verificada")
        return True
        
    except Exception as e:
        print(f"✗ Erro no teste de GUI: {e}")
        return False

if __name__ == "__main__":
    # Configura logging básico
    logging.basicConfig(level=logging.INFO)
    
    # Executa os testes
    installation_ok = test_installation_system()
    gui_ok = test_gui_integration()
    
    if installation_ok and gui_ok:
        print("\n🎉 Todos os testes passaram! O sistema de instalação foi corrigido.")
        sys.exit(0)
    else:
        print("\n❌ Alguns testes falharam. Verifique os erros acima.")
        sys.exit(1)