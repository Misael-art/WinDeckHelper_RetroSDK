#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demonstração Simplificada do Sistema de Sugestões Inteligentes

Este script demonstra o uso básico do sistema de sugestões sem depender
de todos os módulos complexos do projeto.
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass

# Adicionar o diretório do projeto ao path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / 'core'))

# Classe simplificada para aplicação detectada
@dataclass
class SimpleDetectedApp:
    name: str
    version: str = ""
    install_path: str = ""
    executable_path: str = ""

def test_component_matcher():
    """Testa o ComponentMatcher com dados simulados."""
    print("\n=== Teste do Component Matcher ===")
    
    # Dados simulados de componentes
    components_data = {
        "development_tools": {
            "Visual Studio Code": {
                "name": "Visual Studio Code",
                "category": "editor",
                "aliases": ["vscode", "code", "vs code"]
            },
            "Git": {
                "name": "Git",
                "category": "version_control",
                "aliases": ["git-scm"]
            },
            "Node.js": {
                "name": "Node.js",
                "category": "runtime",
                "aliases": ["nodejs", "node"]
            }
        }
    }
    
    try:
        from component_matcher import ComponentMatcher
        
        matcher = ComponentMatcher(components_data)
        
        # Simular aplicações detectadas
        detected_apps = [
            SimpleDetectedApp("Visual Studio Code", "1.85.0"),
            SimpleDetectedApp("Git for Windows", "2.43.0"),
            SimpleDetectedApp("Node.js", "20.10.0")
        ]
        
        print(f"Aplicações detectadas: {len(detected_apps)}")
        
        for app in detected_apps:
            print(f"\nTestando correspondência para: {app.name}")
            # Simular o objeto DetectedApplication
            class MockDetectedApp:
                def __init__(self, name, version):
                    self.name = name
                    self.version = version
                    self.install_path = ""
                    self.executable_path = ""
            
            mock_app = MockDetectedApp(app.name, app.version)
            matches = matcher.find_component_matches(mock_app)
            
            if matches:
                for match in matches:
                    print(f"  ✓ Correspondência: {match.component_name} (confiança: {match.confidence:.2f})")
            else:
                print(f"  ✗ Nenhuma correspondência encontrada")
                
    except ImportError as e:
        print(f"Erro ao importar ComponentMatcher: {e}")
        return False
    except Exception as e:
        print(f"Erro durante o teste: {e}")
        return False
    
    return True

def test_metadata_manager():
    """Testa o ComponentMetadataManager."""
    print("\n=== Teste do Metadata Manager ===")
    
    try:
        from component_metadata_manager import ComponentMetadataManager
        
        # Usar um arquivo temporário para metadados
        temp_metadata_file = str(project_root / "temp_metadata.json")
        manager = ComponentMetadataManager(temp_metadata_file)
        
        # Testar busca de metadados
        vscode_metadata = manager.get_metadata("Visual Studio Code")
        if vscode_metadata:
            print(f"Metadados do VS Code: {vscode_metadata.aliases}")
        else:
            print("Metadados do VS Code não encontrados")
        
        # Testar busca por categoria
        dev_tools = manager.get_components_by_category("editor")
        print(f"Ferramentas de edição: {dev_tools}")
        
        # Limpar arquivo temporário
        if os.path.exists(temp_metadata_file):
            os.remove(temp_metadata_file)
            
    except ImportError as e:
        print(f"Erro ao importar ComponentMetadataManager: {e}")
        return False
    except Exception as e:
        print(f"Erro durante o teste: {e}")
        return False
    
    return True

def main():
    """Função principal de demonstração."""
    print("Demonstração Simplificada do Sistema de Sugestões Inteligentes")
    print("=" * 60)
    
    print(f"Diretório do projeto: {project_root}")
    print(f"Python path: {sys.path[:3]}")
    
    success_count = 0
    total_tests = 2
    
    # Executar testes
    if test_component_matcher():
        success_count += 1
        print("\n✓ Teste do Component Matcher: SUCESSO")
    else:
        print("\n✗ Teste do Component Matcher: FALHOU")
    
    if test_metadata_manager():
        success_count += 1
        print("\n✓ Teste do Metadata Manager: SUCESSO")
    else:
        print("\n✗ Teste do Metadata Manager: FALHOU")
    
    # Resumo
    print("\n" + "=" * 60)
    print(f"Resumo: {success_count}/{total_tests} testes passaram")
    
    if success_count == total_tests:
        print("🎉 Todos os testes do sistema de sugestões passaram!")
        return 0
    else:
        print("⚠️  Alguns testes falharam. Verifique os logs acima.")
        return 1

if __name__ == "__main__":
    sys.exit(main())