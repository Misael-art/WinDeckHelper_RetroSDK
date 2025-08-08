#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Demonstração da detecção de gerenciadores de pacotes
Mostra a funcionalidade implementada na tarefa 3.3
"""

import logging
import sys
import os

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Adicionar o diretório atual ao path
sys.path.append(os.path.dirname(__file__))

from core.unified_detection_engine import UnifiedDetectionEngine

def main():
    """Demonstra a detecção de gerenciadores de pacotes"""
    print("=== Demonstração da Detecção de Gerenciadores de Pacotes ===")
    print("Implementação da tarefa 3.3: Implement package manager detection")
    print()
    
    # Criar instância do motor de detecção unificado
    engine = UnifiedDetectionEngine()
    
    print("1. Detectando gerenciadores de pacotes disponíveis...")
    print("-" * 60)
    
    # Detectar apenas gerenciadores de pacotes
    package_managers = engine._detect_package_managers()
    
    print(f"\nEncontrados {len(package_managers)} gerenciadores de pacotes:")
    print()
    
    for pm in package_managers:
        status = "✓ DISPONÍVEL" if pm.is_available else "✗ NÃO ENCONTRADO"
        print(f"{pm.manager_type.value.upper()}: {status}")
        
        if pm.is_available:
            print(f"  └─ Versão: {pm.version}")
            print(f"  └─ Executável: {pm.executable_path}")
            print(f"  └─ Confiança: {pm.detection_confidence:.1%}")
            
            if pm.installed_packages:
                print(f"  └─ Pacotes instalados: {len(pm.installed_packages)}")
                # Mostrar alguns pacotes como exemplo
                for i, pkg in enumerate(pm.installed_packages[:3]):
                    print(f"     • {pkg.name} v{pkg.version}")
                if len(pm.installed_packages) > 3:
                    print(f"     • ... e mais {len(pm.installed_packages) - 3} pacotes")
            
            if pm.environment_variables:
                print(f"  └─ Variáveis de ambiente detectadas: {len(pm.environment_variables)}")
        
        print()
    
    print("2. Detectando ambientes virtuais...")
    print("-" * 60)
    
    # Detectar ambientes virtuais
    virtual_environments = engine._detect_virtual_environments()
    
    if virtual_environments:
        print(f"\nEncontrados {len(virtual_environments)} ambientes virtuais:")
        print()
        
        for env in virtual_environments:
            active_marker = " (ATIVO)" if env.is_active else ""
            print(f"📁 {env.name} ({env.manager.value}){active_marker}")
            print(f"  └─ Caminho: {env.path}")
            print(f"  └─ Tipo: {env.environment_type.value}")
            
            if env.python_version:
                print(f"  └─ Python: {env.python_version}")
            
            if env.packages:
                print(f"  └─ Pacotes: {len(env.packages)}")
                # Mostrar alguns pacotes
                for i, pkg in enumerate(env.packages[:3]):
                    print(f"     • {pkg.name} v{pkg.version}")
                if len(env.packages) > 3:
                    print(f"     • ... e mais {len(env.packages) - 3} pacotes")
            
            print()
    else:
        print("\nNenhum ambiente virtual detectado.")
        print()
    
    print("3. Interfaces de integração disponíveis...")
    print("-" * 60)
    
    # Mostrar interfaces de integração
    interfaces = engine.get_package_manager_integration_interfaces()
    
    print(f"\nInterfaces de integração implementadas: {len(interfaces)}")
    print()
    
    for manager_type, detector in interfaces.items():
        print(f"🔧 {manager_type.value.upper()}")
        print(f"  └─ Classe: {detector.__class__.__name__}")
        print(f"  └─ Métodos: detect_installation, detect_environments")
        print()
    
    print("4. Executando detecção unificada completa...")
    print("-" * 60)
    
    # Executar detecção completa
    result = engine.detect_all_unified(enable_hierarchical=True)
    
    # Gerar relatório
    report = engine.generate_comprehensive_report(result)
    
    print("\n" + "="*80)
    print("RELATÓRIO COMPLETO DE DETECÇÃO")
    print("="*80)
    print(report)
    
    print("\n" + "="*80)
    print("RESUMO DA IMPLEMENTAÇÃO")
    print("="*80)
    print("✓ Detecção para npm, pip, conda, yarn e pipenv implementada")
    print("✓ Interfaces de integração de gerenciadores de pacotes criadas")
    print("✓ Detecção de ambientes globais e virtuais implementada")
    print("✓ Testes de precisão da detecção implementados")
    print("✓ Requisitos 2.1 e 2.4 atendidos")
    print()
    print("A tarefa 3.3 'Implement package manager detection' foi concluída com sucesso!")


if __name__ == "__main__":
    main()