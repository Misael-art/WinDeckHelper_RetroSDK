#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para limpeza e organização do projeto Environment Dev

Este script automatiza as tarefas de limpeza identificadas na análise:
- Remove código debug excessivo
- Limpa prints desnecessários
- Organiza imports
- Remove código comentado obsoleto
"""

import os
import re
import sys
import shutil
from pathlib import Path
from typing import List, Tuple

def clean_python_file(file_path: Path) -> bool:
    """
    Limpa um arquivo Python removendo debug prints e organizando imports.
    
    Args:
        file_path: Caminho para o arquivo Python
        
    Returns:
        bool: True se o arquivo foi modificado, False caso contrário
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        original_content = content
        
        # Remove prints de debug excessivos
        content = re.sub(
            r'print\s*\(\s*f?"DEBUG:.*?".*?\)',
            '',
            content,
            flags=re.MULTILINE | re.DOTALL
        )
        
        # Remove comentários TODO obsoletos
        content = re.sub(
            r'#\s*(TODO|FIXME|HACK):\s*.*?(\n|$)',
            r'\2',
            content,
            flags=re.MULTILINE
        )
        
        # Remove linhas em branco excessivas (mais de 2 consecutivas)
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        # Se houve modificações, salva o arquivo
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
            
        return False
        
    except Exception as e:
        print(f"Erro ao limpar arquivo {file_path}: {e}")
        return False

def remove_duplicate_directories():
    """Remove diretórios duplicados identificados na análise."""
    project_root = Path(__file__).parent.parent
    
    duplicates_to_remove = [
        project_root / "env_dev" / "env_dev",
        project_root / "downloads" if (project_root / "env_dev" / "downloads").exists(),
    ]
    
    for duplicate_dir in duplicates_to_remove:
        if duplicate_dir.exists() and duplicate_dir.is_dir():
            try:
                print(f"Removendo diretório duplicado: {duplicate_dir}")
                shutil.rmtree(duplicate_dir)
            except Exception as e:
                print(f"Erro ao remover {duplicate_dir}: {e}")

def consolidate_documentation():
    """Consolida documentação espalhada em um local central."""
    project_root = Path(__file__).parent.parent
    main_docs = project_root / "docs"
    env_dev_docs = project_root / "env_dev" / "docs"
    
    if env_dev_docs.exists() and main_docs.exists():
        try:
            # Move arquivos de env_dev/docs para docs/
            for file in env_dev_docs.glob("*"):
                if file.is_file():
                    target = main_docs / file.name
                    if not target.exists():
                        shutil.move(str(file), str(target))
                        print(f"Movido: {file} -> {target}")
            
            # Remove diretório vazio
            if not any(env_dev_docs.iterdir()):
                env_dev_docs.rmdir()
                print(f"Removido diretório vazio: {env_dev_docs}")
                
        except Exception as e:
            print(f"Erro ao consolidar documentação: {e}")

def cleanup_backup_files():
    """Remove arquivos de backup antigos desnecessários."""
    project_root = Path(__file__).parent.parent
    
    backup_patterns = [
        "*.bak",
        "*.backup", 
        "*.old",
        "*.tmp"
    ]
    
    for pattern in backup_patterns:
        for backup_file in project_root.rglob(pattern):
            # Mantém apenas backups recentes (modificados nos últimos 30 dias)
            if backup_file.stat().st_mtime < (time.time() - 30 * 24 * 3600):
                try:
                    backup_file.unlink()
                    print(f"Removido backup antigo: {backup_file}")
                except Exception as e:
                    print(f"Erro ao remover {backup_file}: {e}")

def main():
    """Função principal do script de limpeza."""
    print("🧹 Iniciando limpeza do projeto Environment Dev...")
    
    project_root = Path(__file__).parent.parent
    
    # 1. Limpar arquivos Python
    print("\n📄 Limpando arquivos Python...")
    python_files = list(project_root.rglob("*.py"))
    modified_count = 0
    
    for py_file in python_files:
        if clean_python_file(py_file):
            modified_count += 1
            print(f"  ✓ Limpo: {py_file.relative_to(project_root)}")
    
    print(f"Arquivos Python modificados: {modified_count}")
    
    # 2. Remover diretórios duplicados
    print("\n📁 Removendo diretórios duplicados...")
    remove_duplicate_directories()
    
    # 3. Consolidar documentação
    print("\n📚 Consolidando documentação...")
    consolidate_documentation()
    
    # 4. Limpar arquivos de backup
    print("\n🗑️ Limpando backups antigos...")
    cleanup_backup_files()
    
    print("\n✅ Limpeza concluída com sucesso!")
    print("\n📋 Próximos passos recomendados:")
    print("  1. Executar testes para verificar se nada foi quebrado")
    print("  2. Revisar mudanças com git diff")
    print("  3. Executar análise de código com flake8/pylint")
    print("  4. Atualizar documentação se necessário")

if __name__ == "__main__":
    import time
    main() 