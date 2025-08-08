#!/usr/bin/env python3
"""
Script de demonstração do sistema de sugestões inteligentes.

Este script demonstra como usar os novos módulos de correspondência e sugestões
para encontrar componentes relevantes baseados em aplicações detectadas.
"""

import sys
import os
from pathlib import Path

# Garantir que o diretório do projeto está no path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    # Importar diretamente dos módulos sem usar env_dev
    sys.path.insert(0, str(project_root / 'core'))
    
    from suggestion_service import create_suggestion_service
    from component_matcher import ComponentMatcher
    from component_metadata_manager import ComponentMetadataManager
    from intelligent_suggestions import IntelligentSuggestionEngine
    from detection_engine import DetectedApplication
except ImportError as e:
    print(f"Erro ao importar módulos: {e}")
    print("Certifique-se de que todos os módulos foram criados corretamente.")
    
    # Debug info
    print(f"Diretório atual: {os.getcwd()}")
    print(f"Project root: {project_root}")
    print(f"Sys path: {sys.path[:5]}")
    
    sys.exit(1)

def demo_basic_matching():
    """Demonstra correspondência básica entre aplicações e componentes"""
    print("\n=== DEMONSTRAÇÃO: Correspondência Básica ===")
    
    # Inicializa o matcher
    matcher = ComponentMatcher()
    
    # Simula algumas aplicações detectadas
    detected_apps = [
        {
            'name': 'Visual Studio Code',
            'version': '1.84.0',
            'path': r'C:\Users\User\AppData\Local\Programs\Microsoft VS Code\Code.exe'
        },
        {
            'name': 'Git for Windows',
            'version': '2.42.0',
            'path': r'C:\Program Files\Git\bin\git.exe'
        },
        {
            'name': 'Node.js',
            'version': '20.8.0',
            'path': r'C:\Program Files\nodejs\node.exe'
        }
    ]
    
    print("Aplicações detectadas:")
    for app in detected_apps:
        print(f"  - {app['name']} v{app['version']}")
    
    print("\nBuscando correspondências...")
    for app in detected_apps:
        matches = matcher.find_matches_for_app(app)
        print(f"\n{app['name']}:")
        if matches:
            for match in matches:
                print(f"  ✅ {match.component_name} (confiança: {match.confidence:.2f})")
                print(f"     Razão: {match.match_reason}")
        else:
            print("  ❌ Nenhuma correspondência encontrada")

def demo_fuzzy_matching():
    """Demonstra correspondência fuzzy para nomes similares"""
    print("\n=== DEMONSTRAÇÃO: Correspondência Fuzzy ===")
    
    matcher = ComponentMatcher()
    
    # Testa nomes com variações
    test_names = [
        "VS Code",
        "visual studio code",
        "vscode",
        "Git",
        "git scm",
        "nodejs",
        "node js",
        "Chrome",
        "Google Chrome"
    ]
    
    print("Testando correspondência fuzzy:")
    for name in test_names:
        app = {'name': name, 'version': '1.0.0', 'path': '/fake/path'}
        matches = matcher.find_matches_for_app(app)
        
        print(f"\n'{name}':")
        if matches:
            best_match = matches[0]  # Melhor correspondência
            print(f"  ✅ {best_match.component_name} (confiança: {best_match.confidence:.2f})")
        else:
            print("  ❌ Nenhuma correspondência")

def demo_intelligent_suggestions():
    """Demonstra o sistema de sugestões inteligentes"""
    print("\n=== DEMONSTRAÇÃO: Sugestões Inteligentes ===")
    
    # Cria o serviço completo
    service = create_suggestion_service()
    
    if not service:
        print("❌ Serviço de sugestões não disponível")
        return
    
    # Simula aplicações detectadas para diferentes cenários
    scenarios = {
        "Desenvolvedor Web": [
            {'name': 'Visual Studio Code', 'version': '1.84.0'},
            {'name': 'Node.js', 'version': '20.8.0'},
            {'name': 'Git', 'version': '2.42.0'}
        ],
        "Desenvolvedor Python": [
            {'name': 'Python', 'version': '3.11.0'},
            {'name': 'PyCharm', 'version': '2023.2'},
            {'name': 'Git', 'version': '2.42.0'}
        ],
        "Gamer/Emulação": [
            {'name': 'Steam', 'version': '1.0'},
            {'name': 'RetroArch', 'version': '1.16.0'},
            {'name': 'OBS Studio', 'version': '29.1.0'}
        ]
    }
    
    for scenario_name, apps in scenarios.items():
        print(f"\n--- Cenário: {scenario_name} ---")
        print("Aplicações detectadas:")
        for app in apps:
            print(f"  - {app['name']} v{app['version']}")
        
        # Obtém sugestões
        suggestions = service.get_suggestions(apps)
        
        print("\nSugestões:")
        if suggestions:
            for suggestion in suggestions[:5]:  # Top 5
                print(f"  🎯 {suggestion.component_name} (confiança: {suggestion.confidence:.2f})")
                print(f"     Categoria: {suggestion.category}")
                print(f"     Razão: {suggestion.reason}")
                if suggestion.tags:
                    print(f"     Tags: {', '.join(suggestion.tags)}")
                print()
        else:
            print("  ❌ Nenhuma sugestão disponível")

def demo_metadata_management():
    """Demonstra o gerenciamento de metadados"""
    print("\n=== DEMONSTRAÇÃO: Gerenciamento de Metadados ===")
    
    metadata_manager = ComponentMetadataManager()
    
    # Inicializa metadados padrão
    metadata_manager.initialize_default_metadata()
    
    print("Componentes com metadados:")
    for component_name in metadata_manager.get_all_components():
        metadata = metadata_manager.get_metadata(component_name)
        if metadata:
            print(f"\n{component_name}:")
            print(f"  Categoria: {metadata.category}")
            print(f"  Tags: {', '.join(metadata.tags)}")
            print(f"  Aliases: {', '.join(metadata.aliases)}")
    
    # Demonstra busca por categoria
    print("\n--- Busca por Categoria ---")
    categories = ["Editores de Código", "Ferramentas de Desenvolvimento", "Emuladores"]
    
    for category in categories:
        components = metadata_manager.find_components_by_category(category)
        print(f"\n{category}: {', '.join(components) if components else 'Nenhum componente'}")
    
    # Demonstra busca por tag
    print("\n--- Busca por Tag ---")
    tags = ["editor", "desenvolvimento", "javascript", "emulador"]
    
    for tag in tags:
        components = metadata_manager.find_components_by_tag(tag)
        print(f"\nTag '{tag}': {', '.join(components) if components else 'Nenhum componente'}")

def demo_detection_integration():
    """Demonstra integração com o sistema de detecção existente"""
    print("\n=== DEMONSTRAÇÃO: Integração com Detecção ===")
    
    try:
        # Tenta usar o sistema de detecção real
        detection_engine = DetectionEngine()
        print("Executando detecção real de aplicações...")
        
        # Executa detecção (pode demorar um pouco)
        detected_apps = detection_engine.detect_installed_applications()
        
        print(f"\nDetectadas {len(detected_apps)} aplicações:")
        for app in detected_apps[:10]:  # Mostra apenas as primeiras 10
            print(f"  - {app.get('name', 'Nome desconhecido')} v{app.get('version', 'N/A')}")
        
        # Usa o serviço de sugestões com aplicações reais
        service = create_suggestion_service()
        if service and detected_apps:
            print("\nGerando sugestões baseadas em aplicações reais...")
            suggestions = service.get_suggestions(detected_apps[:5])  # Usa apenas as primeiras 5
            
            print("\nSugestões baseadas em aplicações reais:")
            for suggestion in suggestions[:3]:  # Top 3
                print(f"  🎯 {suggestion.component_name} (confiança: {suggestion.confidence:.2f})")
                print(f"     Razão: {suggestion.reason}")
        
    except Exception as e:
        print(f"❌ Erro na detecção real: {e}")
        print("Usando dados simulados...")
        
        # Fallback para dados simulados
        simulated_apps = [
            {'name': 'Google Chrome', 'version': '118.0'},
            {'name': 'Microsoft Edge', 'version': '118.0'},
            {'name': 'Windows Terminal', 'version': '1.18.0'}
        ]
        
        service = create_suggestion_service()
        if service:
            suggestions = service.get_suggestions(simulated_apps)
            print("\nSugestões baseadas em dados simulados:")
            for suggestion in suggestions[:3]:
                print(f"  🎯 {suggestion.component_name} (confiança: {suggestion.confidence:.2f})")

def main():
    """Função principal que executa todas as demonstrações"""
    print("🚀 DEMONSTRAÇÃO DO SISTEMA DE SUGESTÕES INTELIGENTES")
    print("=" * 60)
    
    try:
        demo_basic_matching()
        demo_fuzzy_matching()
        demo_metadata_management()
        demo_intelligent_suggestions()
        demo_detection_integration()
        
        print("\n" + "=" * 60)
        print("✅ Demonstração concluída com sucesso!")
        print("\nPróximos passos:")
        print("1. Execute a aplicação principal para ver as sugestões na interface")
        print("2. Adicione metadados aos seus componentes YAML usando o exemplo")
        print("3. Customize as regras de sugestão conforme necessário")
        
    except Exception as e:
        print(f"\n❌ Erro durante a demonstração: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()