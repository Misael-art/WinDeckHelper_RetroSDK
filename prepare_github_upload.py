#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prepare GitHub Upload
Prepara o projeto para upload no GitHub, limpando arquivos desnecessários
e organizando a estrutura.
"""

import os
import shutil
import logging
from pathlib import Path
import json

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class GitHubUploadPreparer:
    """Preparador para upload no GitHub"""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.files_to_remove = []
        self.dirs_to_remove = []
        self.files_cleaned = 0
        self.space_saved = 0
    
    def clean_temporary_files(self):
        """Remove arquivos temporários e de teste"""
        logger.info("Limpando arquivos temporários...")
        
        # Padrões de arquivos para remover
        temp_patterns = [
            "*.tmp",
            "*.temp",
            "*.bak",
            "*.backup",
            "*.log",
            "*_test.txt",
            "*_debug.txt",
            "test_output.txt",
            "debug_output.txt",
            "trae_detection_*.txt",
            "multiple_verify_actions_test.txt",
        ]
        
        for pattern in temp_patterns:
            for file_path in self.project_root.glob(pattern):
                if file_path.is_file():
                    size = file_path.stat().st_size
                    file_path.unlink()
                    self.files_cleaned += 1
                    self.space_saved += size
                    logger.info(f"  Removido: {file_path.name}")
    
    def clean_build_artifacts(self):
        """Remove artefatos de build"""
        logger.info("Limpando artefatos de build...")
        
        build_dirs = [
            "build",
            "dist", 
            "__pycache__",
            ".pytest_cache",
            "deployment/build",
            "deployment/dist"
        ]
        
        for dir_name in build_dirs:
            dir_path = self.project_root / dir_name
            if dir_path.exists():
                size = sum(f.stat().st_size for f in dir_path.rglob('*') if f.is_file())
                shutil.rmtree(dir_path)
                self.space_saved += size
                logger.info(f"  Removido diretório: {dir_name}")
        
        # Remover arquivos .pyc
        for pyc_file in self.project_root.rglob("*.pyc"):
            size = pyc_file.stat().st_size
            pyc_file.unlink()
            self.files_cleaned += 1
            self.space_saved += size
    
    def clean_test_artifacts(self):
        """Remove artefatos de teste"""
        logger.info("Limpando artefatos de teste...")
        
        test_files = [
            "component_status.json",
            "installation_test_results*.json",
            "steamdeck_*.json",
            "optimization_*.json",
            "analysis_results.json",
            "final_*.json",
            "demonstration_report.json",
            "dependency_test_results.json",
        ]
        
        for pattern in test_files:
            for file_path in self.project_root.glob(pattern):
                if file_path.is_file():
                    size = file_path.stat().st_size
                    file_path.unlink()
                    self.files_cleaned += 1
                    self.space_saved += size
                    logger.info(f"  Removido: {file_path.name}")
    
    def clean_deployment_packages(self):
        """Remove pacotes de deployment (muito grandes para GitHub)"""
        logger.info("Limpando pacotes de deployment...")
        
        deployment_dir = self.project_root / "deployment"
        if deployment_dir.exists():
            # Manter apenas os scripts, remover pacotes
            for item in deployment_dir.iterdir():
                if item.is_dir() and "Portable" in item.name:
                    size = sum(f.stat().st_size for f in item.rglob('*') if f.is_file())
                    shutil.rmtree(item)
                    self.space_saved += size
                    logger.info(f"  Removido pacote: {item.name}")
                elif item.suffix in ['.zip', '.7z', '.exe']:
                    size = item.stat().st_size
                    item.unlink()
                    self.files_cleaned += 1
                    self.space_saved += size
                    logger.info(f"  Removido: {item.name}")
    
    def organize_documentation(self):
        """Organiza documentação"""
        logger.info("Organizando documentação...")
        
        # Mover arquivos de documentação importantes para docs/
        docs_dir = self.project_root / "docs"
        docs_dir.mkdir(exist_ok=True)
        
        important_docs = [
            "FINAL_FIXES_SUMMARY.md",
            "SGDK_FIXES_SUMMARY.md", 
            "DEPLOYMENT_README.md",
            "DEPLOYMENT_COMPLETE_SUMMARY.md",
            "SISTEMA_INSTALACAO_ROBUSTO_COMPLETO.md",
            "UNIFIED_DETECTION_ENGINE_SUMMARY.md",
            "HIERARCHICAL_DETECTION_IMPLEMENTATION_SUMMARY.md",
        ]
        
        for doc_file in important_docs:
            source = self.project_root / doc_file
            if source.exists():
                dest = docs_dir / doc_file
                if not dest.exists():
                    shutil.copy2(source, dest)
                    logger.info(f"  Copiado para docs/: {doc_file}")
    
    def create_github_files(self):
        """Cria arquivos específicos do GitHub"""
        logger.info("Criando arquivos do GitHub...")
        
        # Criar diretório .github
        github_dir = self.project_root / ".github"
        github_dir.mkdir(exist_ok=True)
        
        # Issue template
        issue_template = github_dir / "ISSUE_TEMPLATE.md"
        if not issue_template.exists():
            issue_template.write_text("""---
name: Bug Report
about: Criar um relatório de bug
title: '[BUG] '
labels: bug
assignees: ''
---

**Descreva o bug**
Uma descrição clara e concisa do que é o bug.

**Para Reproduzir**
Passos para reproduzir o comportamento:
1. Vá para '...'
2. Clique em '....'
3. Role para baixo até '....'
4. Veja o erro

**Comportamento Esperado**
Uma descrição clara e concisa do que você esperava que acontecesse.

**Screenshots**
Se aplicável, adicione screenshots para ajudar a explicar seu problema.

**Informações do Sistema:**
 - OS: [e.g. Windows 11]
 - Python Version: [e.g. 3.11]
 - Versão do App: [e.g. 2.0.0]

**Contexto Adicional**
Adicione qualquer outro contexto sobre o problema aqui.
""", encoding='utf-8')
        
        # Pull request template
        pr_template = github_dir / "pull_request_template.md"
        if not pr_template.exists():
            pr_template.write_text("""## Descrição
Breve descrição das mudanças.

## Tipo de Mudança
- [ ] Bug fix (mudança que corrige um problema)
- [ ] Nova funcionalidade (mudança que adiciona funcionalidade)
- [ ] Breaking change (correção ou funcionalidade que causaria quebra de funcionalidade existente)
- [ ] Documentação (mudanças na documentação)

## Como Foi Testado?
Descreva os testes que você executou para verificar suas mudanças.

## Checklist:
- [ ] Meu código segue as diretrizes de estilo deste projeto
- [ ] Eu fiz uma auto-revisão do meu próprio código
- [ ] Eu comentei meu código, particularmente em áreas difíceis de entender
- [ ] Eu fiz mudanças correspondentes na documentação
- [ ] Minhas mudanças não geram novos warnings
- [ ] Eu adicionei testes que provam que minha correção é efetiva ou que minha funcionalidade funciona
- [ ] Testes unitários novos e existentes passam localmente com minhas mudanças
""", encoding='utf-8')
        
        logger.info("  Arquivos do GitHub criados")
    
    def update_requirements(self):
        """Atualiza arquivo requirements.txt"""
        logger.info("Atualizando requirements.txt...")
        
        # Requirements essenciais
        requirements = [
            "PyYAML>=6.0",
            "requests>=2.28.0",
            "Pillow>=9.0.0",
            "psutil>=5.9.0",
            "py7zr>=0.20.0",
        ]
        
        req_file = self.project_root / "requirements.txt"
        req_file.write_text('\n'.join(requirements) + '\n', encoding='utf-8')
        
        # Requirements de desenvolvimento
        dev_requirements = [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=0.991",
            "pyinstaller>=5.0.0",
        ]
        
        dev_req_file = self.project_root / "requirements-dev.txt"
        dev_req_file.write_text('\n'.join(dev_requirements) + '\n', encoding='utf-8')
        
        logger.info("  Requirements atualizados")
    
    def generate_project_stats(self):
        """Gera estatísticas do projeto"""
        logger.info("Gerando estatísticas do projeto...")
        
        # Contar arquivos Python
        py_files = list(self.project_root.rglob("*.py"))
        py_lines = 0
        for py_file in py_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    py_lines += len(f.readlines())
            except:
                pass
        
        # Contar arquivos YAML
        yaml_files = list(self.project_root.rglob("*.yaml"))
        yaml_files.extend(list(self.project_root.rglob("*.yml")))
        
        # Contar documentação
        doc_files = list(self.project_root.rglob("*.md"))
        
        stats = {
            "python_files": len(py_files),
            "python_lines": py_lines,
            "yaml_files": len(yaml_files),
            "documentation_files": len(doc_files),
            "total_files": len(list(self.project_root.rglob("*"))),
        }
        
        stats_file = self.project_root / "PROJECT_STATS.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2)
        
        logger.info(f"  Arquivos Python: {stats['python_files']}")
        logger.info(f"  Linhas de código: {stats['python_lines']}")
        logger.info(f"  Arquivos YAML: {stats['yaml_files']}")
        logger.info(f"  Documentação: {stats['documentation_files']}")
    
    def prepare_for_github(self):
        """Executa toda a preparação"""
        logger.info("Preparando projeto para GitHub...")
        
        # Limpeza
        self.clean_temporary_files()
        self.clean_build_artifacts()
        self.clean_test_artifacts()
        self.clean_deployment_packages()
        
        # Organização
        self.organize_documentation()
        self.create_github_files()
        self.update_requirements()
        self.generate_project_stats()
        
        # Relatório final
        space_saved_mb = self.space_saved / (1024 * 1024)
        
        print(f"\n{'='*50}")
        print("PREPARAÇÃO PARA GITHUB CONCLUÍDA")
        print(f"{'='*50}")
        print(f"Arquivos removidos: {self.files_cleaned}")
        print(f"Espaço economizado: {space_saved_mb:.1f} MB")
        print(f"Projeto pronto para upload!")
        print(f"{'='*50}")
        
        return True

def main():
    """Função principal"""
    print("Preparando Environment Dev Deep Evaluation para GitHub...")
    print("=" * 60)
    
    preparer = GitHubUploadPreparer()
    success = preparer.prepare_for_github()
    
    if success:
        print("\nPróximos passos:")
        print("1. git init")
        print("2. git add .")
        print("3. git commit -m 'Initial commit: Environment Dev Deep Evaluation v2.0'")
        print("4. git branch -M main")
        print("5. git remote add origin https://github.com/Misael-art/EnvironmentDev_MISA.git")
        print("6. git push -u origin main")
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)