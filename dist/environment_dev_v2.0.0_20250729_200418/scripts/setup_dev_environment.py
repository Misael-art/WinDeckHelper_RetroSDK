#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para configurar o ambiente de desenvolvimento do Environment Dev

Este script:
1. Instala todas as dependências de desenvolvimento
2. Configura pre-commit hooks
3. Executa verificações iniciais de qualidade
4. Cria estrutura de diretórios necessária
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(command: str, description: str, check: bool = True) -> bool:
    """
    Executa um comando e exibe o resultado.
    
    Args:
        command: Comando a ser executado
        description: Descrição do que o comando faz
        check: Se deve verificar o código de saída
        
    Returns:
        bool: True se o comando foi executado com sucesso
    """
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            check=check
        )
        
        if result.returncode == 0:
            print(f"  ✅ {description} - Concluído")
            if result.stdout.strip():
                print(f"     {result.stdout.strip()}")
            return True
        else:
            print(f"  ❌ {description} - Falhou")
            if result.stderr.strip():
                print(f"     Erro: {result.stderr.strip()}")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"  ❌ {description} - Erro: {e}")
        return False
    except Exception as e:
        print(f"  ❌ {description} - Erro inesperado: {e}")
        return False


def check_python_version():
    """Verifica se a versão do Python é adequada."""
    print("🐍 Verificando versão do Python...")
    
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"  ❌ Python {version.major}.{version.minor} não é suportado")
        print("     É necessário Python 3.8 ou superior")
        return False
    
    print(f"  ✅ Python {version.major}.{version.minor}.{version.micro} - OK")
    return True


def setup_virtual_environment():
    """Configura o ambiente virtual se não existir."""
    venv_path = Path(".venv")
    
    if venv_path.exists():
        print("  ✅ Ambiente virtual já existe")
        return True
    
    return run_command(
        "python -m venv .venv",
        "Criando ambiente virtual"
    )


def install_dependencies():
    """Instala as dependências de desenvolvimento."""
    commands = [
        ("python -m pip install --upgrade pip", "Atualizando pip"),
        ("pip install -r requirements-dev.txt", "Instalando dependências de desenvolvimento"),
        ("pip install -r env_dev/requirements.txt", "Instalando dependências do projeto"),
    ]
    
    success = True
    for command, description in commands:
        if not run_command(command, description):
            success = False
    
    return success


def setup_pre_commit():
    """Configura pre-commit hooks."""
    # Primeiro, cria o arquivo de configuração se não existir
    pre_commit_config = Path(".pre-commit-config.yaml")
    
    if not pre_commit_config.exists():
        config_content = """
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict
      - id: debug-statements

  - repo: https://github.com/psf/black
    rev: 23.7.0
    hooks:
      - id: black
        language_version: python3

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ["--profile", "black"]

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
""".strip()
        
        with open(pre_commit_config, 'w', encoding='utf-8') as f:
            f.write(config_content)
        
        print("  ✅ Arquivo .pre-commit-config.yaml criado")
    
    return run_command(
        "pre-commit install",
        "Instalando pre-commit hooks"
    )


def create_directory_structure():
    """Cria estrutura de diretórios necessária."""
    directories = [
        "logs",
        "downloads",
        "temp_download",
        "scripts",
        "docs/api",
        "docs/examples",
        "tests/unit",
        "tests/integration",
    ]
    
    print("📁 Criando estrutura de diretórios...")
    
    for directory in directories:
        dir_path = Path(directory)
        dir_path.mkdir(parents=True, exist_ok=True)
        
        # Cria arquivo .gitkeep para manter diretórios vazios no git
        gitkeep = dir_path / ".gitkeep"
        if not gitkeep.exists() and not any(dir_path.iterdir()):
            gitkeep.touch()
    
    print("  ✅ Estrutura de diretórios criada")
    return True


def run_initial_checks():
    """Executa verificações iniciais de qualidade."""
    print("🔍 Executando verificações iniciais...")
    
    # Executa verificações básicas (sem falhar se encontrar problemas)
    checks = [
        ("python -m flake8 env_dev --count --statistics", "Verificação de estilo com flake8"),
        ("python -m pytest tests/ -v --tb=short", "Executando testes existentes"),
    ]
    
    for command, description in checks:
        run_command(command, description, check=False)


def main():
    """Função principal do setup."""
    print("🚀 Configurando ambiente de desenvolvimento do Environment Dev")
    print("=" * 60)
    
    # Verifica pré-requisitos
    if not check_python_version():
        sys.exit(1)
    
    # Configura ambiente
    steps = [
        (setup_virtual_environment, "Configuração do ambiente virtual"),
        (install_dependencies, "Instalação de dependências"),
        (setup_pre_commit, "Configuração de pre-commit hooks"),
        (create_directory_structure, "Criação de estrutura de diretórios"),
        (run_initial_checks, "Verificações iniciais"),
    ]
    
    failed_steps = []
    
    for step_func, step_name in steps:
        print(f"\n📋 {step_name}")
        if not step_func():
            failed_steps.append(step_name)
    
    # Resumo final
    print("\n" + "=" * 60)
    if failed_steps:
        print("⚠️  Setup concluído com alguns problemas:")
        for step in failed_steps:
            print(f"   - {step}")
        print("\nVerifique os erros acima e execute novamente se necessário.")
    else:
        print("✅ Setup do ambiente de desenvolvimento concluído com sucesso!")
    
    print("\n📋 Próximos passos:")
    print("  1. Ativar o ambiente virtual: .venv\\Scripts\\activate (Windows) ou source .venv/bin/activate (Linux/Mac)")
    print("  2. Executar: python scripts/cleanup_project.py")
    print("  3. Executar testes: pytest")
    print("  4. Verificar qualidade: flake8 env_dev")


if __name__ == "__main__":
    main() 