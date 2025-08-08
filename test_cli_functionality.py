#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de teste para demonstrar a funcionalidade de linha de comando do Environment Dev.

Este script testa todas as novas funcionalidades implementadas:
- Instalação de múltiplos componentes
- Instalação por categoria
- Verificação de múltiplos componentes
- Verificação de todos os componentes
- Modos quiet e verbose
"""

import os
import sys
import subprocess
import time
from pathlib import Path

# Adicionar o diretório raiz ao path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def run_cli_command(command_args, description=""):
    """
    Executa um comando CLI e exibe o resultado
    
    Args:
        command_args: Lista de argumentos para o comando
        description: Descrição do teste
    """
    print(f"\n{'='*60}")
    print(f"TESTE: {description}")
    print(f"COMANDO: python main.py {' '.join(command_args)}")
    print(f"{'='*60}")
    
    try:
        # Executar o comando
        result = subprocess.run(
            [sys.executable, "main.py"] + command_args,
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        print(f"CÓDIGO DE SAÍDA: {result.returncode}")
        
        if result.stdout:
            print("\nSAÍDA:")
            print(result.stdout)
        
        if result.stderr:
            print("\nERROS:")
            print(result.stderr)
            
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("ERRO: Comando expirou (timeout de 60s)")
        return False
    except Exception as e:
        print(f"ERRO: {str(e)}")
        return False

def test_help_and_info():
    """Testa comandos de ajuda e informação"""
    print("\n" + "#"*80)
    print("# TESTANDO COMANDOS DE AJUDA E INFORMAÇÃO")
    print("#"*80)
    
    tests = [
        (["--help"], "Exibir ajuda completa"),
        (["--list"], "Listar todos os componentes"),
        (["--categories"], "Listar todas as categorias"),
        (["--list-category", "retro"], "Listar componentes da categoria retro"),
    ]
    
    for args, desc in tests:
        run_cli_command(args, desc)
        time.sleep(1)

def test_verification():
    """Testa comandos de verificação"""
    print("\n" + "#"*80)
    print("# TESTANDO COMANDOS DE VERIFICAÇÃO")
    print("#"*80)
    
    tests = [
        (["--verify", "sgdk"], "Verificar SGDK (componente único)"),
        (["--verify", "sgdk", "java"], "Verificar SGDK e Java (múltiplos componentes)"),
        (["--verify", "sgdk", "--quiet"], "Verificar SGDK (modo silencioso)"),
        (["--verify-all", "--quiet"], "Verificar todos os componentes (modo silencioso)"),
    ]
    
    for args, desc in tests:
        run_cli_command(args, desc)
        time.sleep(1)

def test_installation_dry_run():
    """Testa comandos de instalação (sem realmente instalar)"""
    print("\n" + "#"*80)
    print("# TESTANDO COMANDOS DE INSTALAÇÃO (SIMULAÇÃO)")
    print("#"*80)
    
    # Nota: Estes testes podem falhar se os componentes não estiverem disponíveis
    # ou se as dependências não estiverem instaladas
    
    tests = [
        (["--install", "nonexistent_component"], "Tentar instalar componente inexistente"),
        (["--verify", "sgdk", "--verbose"], "Verificar SGDK (modo verboso)"),
    ]
    
    for args, desc in tests:
        run_cli_command(args, desc)
        time.sleep(1)

def test_error_handling():
    """Testa tratamento de erros"""
    print("\n" + "#"*80)
    print("# TESTANDO TRATAMENTO DE ERROS")
    print("#"*80)
    
    tests = [
        (["--install"], "Comando install sem argumentos"),
        (["--verify"], "Comando verify sem argumentos"),
        (["--list-category", "categoria_inexistente"], "Listar categoria inexistente"),
        (["--install-category", "categoria_inexistente"], "Instalar categoria inexistente"),
    ]
    
    for args, desc in tests:
        run_cli_command(args, desc)
        time.sleep(1)

def test_advanced_features():
    """Testa funcionalidades avançadas"""
    print("\n" + "#"*80)
    print("# TESTANDO FUNCIONALIDADES AVANÇADAS")
    print("#"*80)
    
    tests = [
        (["--debug", "--list"], "Listar componentes (modo debug)"),
        (["--quiet", "--categories"], "Listar categorias (modo silencioso)"),
        (["--verbose", "--verify", "sgdk"], "Verificar SGDK (modo verboso)"),
    ]
    
    for args, desc in tests:
        run_cli_command(args, desc)
        time.sleep(1)

def main():
    """
    Função principal que executa todos os testes
    """
    print("INICIANDO TESTES DA FUNCIONALIDADE CLI DO ENVIRONMENT DEV")
    print(f"Diretório de trabalho: {project_root}")
    print(f"Python: {sys.executable}")
    
    # Verificar se o main.py existe
    main_py = project_root / "main.py"
    if not main_py.exists():
        print(f"ERRO: {main_py} não encontrado!")
        return 1
    
    try:
        # Executar todos os testes
        test_help_and_info()
        test_verification()
        test_installation_dry_run()
        test_error_handling()
        test_advanced_features()
        
        print("\n" + "="*80)
        print("TESTES CONCLUÍDOS")
        print("="*80)
        print("\nNOTA: Alguns testes podem falhar se os componentes não estiverem")
        print("configurados ou se as dependências não estiverem instaladas.")
        print("Isso é esperado e não indica um problema com a funcionalidade CLI.")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\nTestes interrompidos pelo usuário.")
        return 130
    except Exception as e:
        print(f"\nERRO DURANTE OS TESTES: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())