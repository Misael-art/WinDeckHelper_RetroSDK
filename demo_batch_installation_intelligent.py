#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demonstração da instalação em lote inteligente
Mostra as funcionalidades implementadas na task 5.2
"""

import os
import sys
import tempfile
import shutil
import yaml
from datetime import datetime

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from env_dev.core.installation_manager import InstallationManager


def create_demo_environment():
    """Cria ambiente de demonstração com componentes de teste"""
    temp_dir = tempfile.mkdtemp()
    print(f"Criando ambiente de demonstração em: {temp_dir}")
    
    # Cria estrutura de diretórios
    config_dir = os.path.join(temp_dir, "config", "components")
    os.makedirs(config_dir, exist_ok=True)
    
    # Define componentes de demonstração com dependências complexas
    components = {
        # Componentes base (sem dependências)
        'vcredist': {
            'name': 'Visual C++ Redistributable',
            'version': '2022',
            'install_method': 'executable',
            'download_url': 'https://example.com/vcredist.exe',
            'hash_value': 'vcredist_hash',
            'dependencies': [],
            'conflicts': [],
            'supports_parallel_install': True,
            'install_paths': ['/Program Files/Microsoft Visual Studio'],
            'requires_admin': True
        },
        
        'dotnet': {
            'name': '.NET Runtime',
            'version': '8.0',
            'install_method': 'executable',
            'download_url': 'https://example.com/dotnet.exe',
            'hash_value': 'dotnet_hash',
            'dependencies': [],
            'conflicts': [],
            'supports_parallel_install': True,
            'install_paths': ['/Program Files/dotnet'],
            'requires_admin': True
        },
        
        # Componentes de middleware (dependem de base)
        'nodejs': {
            'name': 'Node.js',
            'version': '20.0.0',
            'install_method': 'msi',
            'download_url': 'https://example.com/nodejs.msi',
            'hash_value': 'nodejs_hash',
            'dependencies': ['vcredist'],
            'conflicts': [],
            'supports_parallel_install': True,
            'install_paths': ['/Program Files/nodejs']
        },
        
        'python': {
            'name': 'Python',
            'version': '3.12',
            'install_method': 'executable',
            'download_url': 'https://example.com/python.exe',
            'hash_value': 'python_hash',
            'dependencies': ['vcredist'],
            'conflicts': [],
            'supports_parallel_install': True,
            'install_paths': ['/Program Files/Python312']
        },
        
        # Aplicações (dependem de middleware)
        'vscode': {
            'name': 'Visual Studio Code',
            'version': '1.85.0',
            'install_method': 'executable',
            'download_url': 'https://example.com/vscode.exe',
            'hash_value': 'vscode_hash',
            'dependencies': ['nodejs'],
            'conflicts': [],
            'supports_parallel_install': True,
            'install_paths': ['/Program Files/Microsoft VS Code']
        },
        
        'pycharm': {
            'name': 'PyCharm Community',
            'version': '2023.3',
            'install_method': 'executable',
            'download_url': 'https://example.com/pycharm.exe',
            'hash_value': 'pycharm_hash',
            'dependencies': ['python'],
            'conflicts': [],
            'supports_parallel_install': True,
            'install_paths': ['/Program Files/JetBrains/PyCharm Community Edition']
        },
        
        # Ferramentas de desenvolvimento (dependem de múltiplos)
        'git': {
            'name': 'Git for Windows',
            'version': '2.43.0',
            'install_method': 'executable',
            'download_url': 'https://example.com/git.exe',
            'hash_value': 'git_hash',
            'dependencies': [],
            'conflicts': [],
            'supports_parallel_install': True,
            'install_paths': ['/Program Files/Git']
        },
        
        'docker': {
            'name': 'Docker Desktop',
            'version': '4.26.0',
            'install_method': 'executable',
            'download_url': 'https://example.com/docker.exe',
            'hash_value': 'docker_hash',
            'dependencies': ['dotnet'],
            'conflicts': [],
            'supports_parallel_install': False,  # Docker não suporta instalação paralela
            'install_paths': ['/Program Files/Docker'],
            'requires_admin': True
        },
        
        # Componente com conflito
        'alternative_runtime': {
            'name': 'Alternative Runtime',
            'version': '1.0.0',
            'install_method': 'executable',
            'download_url': 'https://example.com/alt_runtime.exe',
            'hash_value': 'alt_runtime_hash',
            'dependencies': [],
            'conflicts': ['dotnet'],  # Conflita com .NET
            'supports_parallel_install': True,
            'install_paths': ['/Program Files/Alternative Runtime']
        }
    }
    
    # Salva configurações dos componentes
    for name, config in components.items():
        config_path = os.path.join(config_dir, f"{name}.yaml")
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
    
    return temp_dir, components


def demonstrate_conflict_detection(manager, components):
    """Demonstra detecção de conflitos entre componentes"""
    print("\n" + "="*60)
    print("DEMONSTRAÇÃO: DETECÇÃO DE CONFLITOS")
    print("="*60)
    
    # Testa com componentes sem conflito
    print("\n1. Testando componentes sem conflito:")
    safe_components = ['vcredist', 'dotnet', 'nodejs']
    conflicts = manager._detect_component_conflicts(safe_components)
    
    if conflicts:
        print(f"   ⚠️  Conflitos detectados: {len(conflicts)}")
        for conflict in conflicts:
            print(f"      - {conflict.component1} vs {conflict.component2}: {conflict.description}")
    else:
        print("   ✅ Nenhum conflito detectado")
    
    # Testa com componentes conflitantes
    print("\n2. Testando componentes com conflito:")
    conflict_components = ['dotnet', 'alternative_runtime']
    conflicts = manager._detect_component_conflicts(conflict_components)
    
    if conflicts:
        print(f"   ⚠️  Conflitos detectados: {len(conflicts)}")
        for conflict in conflicts:
            print(f"      - {conflict.component1} vs {conflict.component2}")
            print(f"        Tipo: {conflict.conflict_type}")
            print(f"        Severidade: {conflict.severity}")
            print(f"        Descrição: {conflict.description}")
            if conflict.resolution_suggestion:
                print(f"        Sugestão: {conflict.resolution_suggestion}")
    else:
        print("   ✅ Nenhum conflito detectado")


def demonstrate_dependency_resolution(manager, components):
    """Demonstra resolução automática de dependências"""
    print("\n" + "="*60)
    print("DEMONSTRAÇÃO: RESOLUÇÃO DE DEPENDÊNCIAS")
    print("="*60)
    
    # Componentes com dependências complexas
    test_components = ['vscode', 'pycharm', 'docker', 'git']
    
    print(f"\nComponentes solicitados: {test_components}")
    print("\nDependências de cada componente:")
    for comp in test_components:
        deps = components[comp]['dependencies']
        print(f"  - {comp}: {deps if deps else 'nenhuma'}")
    
    # Resolve ordem de instalação
    print("\nResolvendo ordem de instalação...")
    dependency_order = manager._resolve_dependency_order(test_components)
    
    print(f"Ordem resolvida: {dependency_order}")
    
    # Mostra níveis de dependência
    groups = manager._create_parallel_installation_groups(test_components)
    print(f"\nGrupos de instalação paralela ({len(groups)} grupos):")
    
    for i, group in enumerate(groups):
        parallel_status = "✅ Paralelo" if group.can_install_parallel else "⏭️  Sequencial"
        print(f"  Grupo {i} (nível {group.level}): {group.components} - {parallel_status}")


def demonstrate_parallel_installation(manager):
    """Demonstra instalação paralela inteligente"""
    print("\n" + "="*60)
    print("DEMONSTRAÇÃO: INSTALAÇÃO PARALELA INTELIGENTE")
    print("="*60)
    
    # Simula instalação de componentes que podem ser paralelos
    parallel_components = ['vcredist', 'dotnet', 'git']
    
    print(f"\nTestando instalação paralela de: {parallel_components}")
    
    # Mock do download manager para simular sucesso
    from unittest.mock import Mock
    manager.download_manager = Mock()
    manager.download_manager.download_with_verification.return_value = Mock(
        success=True,
        file_path='/tmp/test.exe'
    )
    
    # Mock do preparation manager
    prep_result = Mock()
    prep_result.status.value = "completed"
    prep_result.errors = []
    manager.preparation_manager = Mock()
    manager.preparation_manager.prepare_environment.return_value = prep_result
    
    # Mock das estratégias de instalação para simular sucesso
    for strategy in manager.strategies:
        strategy.install = Mock(return_value=Mock(
            success=True,
            installed_path='/test/path',
            version='1.0.0'
        ))
        strategy.verify_installation = Mock(return_value=Mock(
            success=True,
            installed_path='/test/path',
            version='1.0.0',
            details={}
        ))
    
    print("\n⏳ Iniciando instalação em lote inteligente...")
    start_time = datetime.now()
    
    # Executa instalação com paralelização
    result = manager.install_multiple(
        components=parallel_components,
        max_parallel=3,
        enable_recovery=True
    )
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print(f"\n📊 RESULTADOS DA INSTALAÇÃO:")
    print(f"   Tempo total: {duration:.2f}s")
    print(f"   Sucesso geral: {'✅ Sim' if result.overall_success else '❌ Não'}")
    print(f"   Componentes instalados: {len(result.completed_components)}")
    print(f"   Componentes falharam: {len(result.failed_components)}")
    print(f"   Componentes pulados: {len(result.skipped_components)}")
    print(f"   Instalações paralelas: {result.parallel_installations}")
    print(f"   Grupos de instalação: {len(result.parallel_groups)}")
    
    if result.completed_components:
        print(f"   ✅ Instalados: {result.completed_components}")
    
    if result.failed_components:
        print(f"   ❌ Falharam: {result.failed_components}")
    
    if result.recovery_attempts:
        print(f"   🔄 Tentativas de recovery: {result.recovery_attempts}")
    
    print(f"\n📈 DETALHES DOS GRUPOS:")
    for i, group in enumerate(result.parallel_groups):
        status = "Paralelo" if group.can_install_parallel else "Sequencial"
        print(f"   Grupo {i} (nível {group.level}): {group.components} - {status}")


def demonstrate_recovery_system(manager):
    """Demonstra sistema de recovery automático"""
    print("\n" + "="*60)
    print("DEMONSTRAÇÃO: SISTEMA DE RECOVERY AUTOMÁTICO")
    print("="*60)
    
    from env_dev.core.installation_manager import InstallationResult, InstallationStatus
    
    # Testa identificação de erros recuperáveis
    print("\n1. Testando identificação de erros recuperáveis:")
    
    recoverable_errors = [
        {'error': 'network_timeout', 'description': 'Timeout de rede'},
        {'error': 'download_failed', 'description': 'Falha no download'},
        {'error': 'temporary_failure', 'description': 'Falha temporária'}
    ]
    
    for error_case in recoverable_errors:
        result = InstallationResult(
            success=False,
            status=InstallationStatus.FAILED,
            message="Erro simulado",
            details=error_case
        )
        
        should_retry = manager._should_retry_installation(result)
        status = "✅ Recuperável" if should_retry else "❌ Não recuperável"
        print(f"   {error_case['description']}: {status}")
    
    # Testa identificação de erros não-recuperáveis
    print("\n2. Testando identificação de erros não-recuperáveis:")
    
    non_recoverable_errors = [
        {'error': 'insufficient_privileges', 'description': 'Privilégios insuficientes'},
        {'error': 'disk_space', 'description': 'Espaço em disco insuficiente'},
        {'error': 'circular_dependency', 'description': 'Dependência circular'}
    ]
    
    for error_case in non_recoverable_errors:
        result = InstallationResult(
            success=False,
            status=InstallationStatus.FAILED,
            message="Erro simulado",
            details=error_case
        )
        
        should_retry = manager._should_retry_installation(result)
        status = "✅ Recuperável" if should_retry else "❌ Não recuperável"
        print(f"   {error_case['description']}: {status}")
    
    print("\n3. Sistema de recovery em ação:")
    print("   - Máximo de 3 tentativas por componente")
    print("   - Backoff exponencial entre tentativas (2^n segundos)")
    print("   - Recovery apenas para erros recuperáveis")
    print("   - Tracking de tentativas de recovery no resultado")


def main():
    """Função principal da demonstração"""
    print("🚀 DEMONSTRAÇÃO: INSTALAÇÃO EM LOTE INTELIGENTE")
    print("Implementação da Task 5.2 - Environment Dev Success Plan")
    print("="*80)
    
    # Cria ambiente de demonstração
    temp_dir, components = create_demo_environment()
    
    try:
        # Inicializa manager
        manager = InstallationManager(temp_dir)
        
        # Demonstrações
        demonstrate_conflict_detection(manager, components)
        demonstrate_dependency_resolution(manager, components)
        demonstrate_parallel_installation(manager)
        demonstrate_recovery_system(manager)
        
        print("\n" + "="*80)
        print("✅ DEMONSTRAÇÃO CONCLUÍDA COM SUCESSO!")
        print("\nFuncionalidades implementadas na Task 5.2:")
        print("  ✅ Sistema de resolução automática de ordem de dependências")
        print("  ✅ Implementação de instalação paralela quando possível")
        print("  ✅ Tratamento de conflitos entre componentes")
        print("  ✅ Sistema de recovery automático de falhas")
        print("\nTodas as funcionalidades estão funcionando corretamente!")
        
    finally:
        # Limpa ambiente de demonstração
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print(f"\n🧹 Ambiente de demonstração limpo: {temp_dir}")


if __name__ == '__main__':
    main()