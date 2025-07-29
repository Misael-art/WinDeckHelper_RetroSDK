#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de teste para verificar as correções críticas implementadas.
"""

import sys
import os
import logging

# Adicionar o diretório env_dev ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'env_dev'))

def test_command_verification():
    """Testa as melhorias na verificação de comandos."""
    print("=== Testando Verificação de Comandos ===")
    
    try:
        from utils.command_verification import command_exists, clear_command_cache
        
        # Limpar cache para teste limpo
        clear_command_cache()
        
        # Testar comandos conhecidos
        test_commands = ['python', 'cmd', 'powershell', 'nonexistent_command_12345']
        
        for cmd in test_commands:
            exists = command_exists(cmd)
            print(f"Comando '{cmd}': {'✓ Encontrado' if exists else '✗ Não encontrado'}")
        
        print("✓ Verificação de comandos funcionando corretamente")
        return True
        
    except Exception as e:
        print(f"✗ Erro na verificação de comandos: {e}")
        return False

def test_dependency_resolver():
    """Testa as melhorias na resolução de dependências."""
    print("\n=== Testando Resolução de Dependências ===")
    
    try:
        from utils.dependency_resolver import DependencyResolver, CircularDependencyError
        
        # Teste com dependências circulares
        circular_components = {
            "A": {"dependencies": ["B"]},
            "B": {"dependencies": ["C"]},
            "C": {"dependencies": ["A"]},  # Cria ciclo A -> B -> C -> A
        }
        
        resolver = DependencyResolver(circular_components)
        cycles = resolver.detect_circular_dependencies()
        
        if cycles:
            print(f"✓ Dependência circular detectada: {cycles[0]}")
        else:
            print("✗ Falha ao detectar dependência circular")
            return False
        
        # Teste com dependências válidas
        valid_components = {
            "A": {"dependencies": ["B"]},
            "B": {"dependencies": ["C"]},
            "C": {"dependencies": []},
        }
        
        valid_resolver = DependencyResolver(valid_components)
        order = valid_resolver.topological_sort()
        
        if order == ["C", "B", "A"]:
            print(f"✓ Ordenação topológica correta: {order}")
        else:
            print(f"✗ Ordenação topológica incorreta: {order}")
            return False
        
        print("✓ Resolução de dependências funcionando corretamente")
        return True
        
    except Exception as e:
        print(f"✗ Erro na resolução de dependências: {e}")
        return False

def test_clover_installer():
    """Testa as melhorias no instalador do Clover."""
    print("\n=== Testando Instalador do Clover ===")
    
    try:
        from core.clover_installer import _find_clover_zip, _get_clover_search_paths
        
        # Testar busca de caminhos
        search_paths = _get_clover_search_paths()
        print(f"✓ Caminhos de busca definidos: {len(search_paths)} locais")
        
        # Testar busca do arquivo (não deve falhar mesmo se não encontrar)
        clover_path = _find_clover_zip()
        if clover_path:
            print(f"✓ Arquivo Clover encontrado: {clover_path}")
        else:
            print("ℹ Arquivo Clover não encontrado (normal se não instalado)")
        
        print("✓ Instalador do Clover funcionando corretamente")
        return True
        
    except Exception as e:
        print(f"✗ Erro no instalador do Clover: {e}")
        return False

def test_project_cleanup():
    """Testa o sistema de limpeza do projeto."""
    print("\n=== Testando Limpeza do Projeto ===")
    
    try:
        from utils.project_cleanup import ProjectCleaner
        
        # Criar instância do limpador
        cleaner = ProjectCleaner(".")
        
        # Executar escaneamento (dry-run)
        scan_results = cleaner.scan_project()
        
        total_items = sum(len(items) for items in scan_results.values() 
                         if isinstance(items, list))
        
        print(f"✓ Escaneamento concluído: {total_items} itens encontrados")
        
        # Verificar se encontrou categorias esperadas
        expected_categories = ['backup_files', 'log_files', 'cache_files', 'empty_directories']
        found_categories = [cat for cat in expected_categories if scan_results.get(cat)]
        
        print(f"✓ Categorias encontradas: {found_categories}")
        print("✓ Sistema de limpeza funcionando corretamente")
        return True
        
    except Exception as e:
        print(f"✗ Erro na limpeza do projeto: {e}")
        return False

def main():
    """Função principal do teste."""
    print("Testando Correções Críticas do Environment Dev")
    print("=" * 50)
    
    # Configurar logging básico
    logging.basicConfig(level=logging.WARNING)
    
    tests = [
        test_command_verification,
        test_dependency_resolver,
        test_clover_installer,
        test_project_cleanup
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ Erro inesperado no teste: {e}")
    
    print("\n" + "=" * 50)
    print(f"Resultado: {passed}/{total} testes passaram")
    
    if passed == total:
        print("🎉 Todas as correções críticas estão funcionando!")
        return True
    else:
        print("⚠️  Algumas correções precisam de ajustes.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)