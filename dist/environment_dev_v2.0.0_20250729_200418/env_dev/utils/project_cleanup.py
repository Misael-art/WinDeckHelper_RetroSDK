#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo para limpeza de arquivos obsoletos e duplicados do projeto.

Este módulo identifica e remove arquivos desnecessários, backups antigos,
e estruturas duplicadas para manter o projeto organizado.
"""

import os
import sys
import shutil
import logging
import hashlib
import time
from typing import List, Dict, Set, Tuple, Optional
from pathlib import Path
import fnmatch
import json

logger = logging.getLogger(__name__)

class ProjectCleaner:
    """
    Classe para limpeza e organização do projeto.
    """
    
    def __init__(self, project_root: str):
        """
        Inicializa o limpador de projeto.
        
        Args:
            project_root: Caminho raiz do projeto
        """
        self.project_root = os.path.abspath(project_root)
        self.backup_patterns = [
            '*.bak', '*.backup', '*.old', '*.orig', '*.original',
            '*.tmp', '*.temp', '*~', '*.swp', '*.swo'
        ]
        self.log_patterns = [
            '*.log', 'debug_trace.log', 'main_execution.log'
        ]
        self.cache_patterns = [
            '__pycache__', '*.pyc', '*.pyo', '.pytest_cache',
            'node_modules', '.vscode', '.idea'
        ]
        
        # Arquivos que devem ser preservados mesmo se parecem obsoletos
        self.preserve_files = {
            'LICENSE', 'README.md', 'requirements.txt', 'setup.py',
            'setup.cfg', '.gitignore', '.gitattributes'
        }
        
        # Diretórios que podem ser removidos se vazios
        self.removable_empty_dirs = {
            'temp_download', 'downloads', '__pycache__', '.pytest_cache'
        }
    
    def scan_project(self) -> Dict[str, List[str]]:
        """
        Escaneia o projeto e categoriza arquivos para limpeza.
        
        Returns:
            Dicionário com categorias de arquivos encontrados
        """
        scan_results = {
            'backup_files': [],
            'log_files': [],
            'cache_files': [],
            'duplicate_files': [],
            'empty_directories': [],
            'large_files': [],
            'obsolete_files': []
        }
        
        logger.info(f"Escaneando projeto em: {self.project_root}")
        
        # Escanear todos os arquivos
        for root, dirs, files in os.walk(self.project_root):
            # Pular diretórios de controle de versão
            if '.git' in root or '.svn' in root:
                continue
            
            # Verificar diretórios vazios
            if not dirs and not files:
                rel_path = os.path.relpath(root, self.project_root)
                if any(pattern in rel_path for pattern in self.removable_empty_dirs):
                    scan_results['empty_directories'].append(root)
            
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, self.project_root)
                
                # Verificar arquivos de backup
                if self._matches_patterns(file, self.backup_patterns):
                    scan_results['backup_files'].append(file_path)
                
                # Verificar arquivos de log
                elif self._matches_patterns(file, self.log_patterns):
                    scan_results['log_files'].append(file_path)
                
                # Verificar arquivos de cache
                elif self._matches_patterns(file, self.cache_patterns) or \
                     any(pattern in root for pattern in self.cache_patterns):
                    scan_results['cache_files'].append(file_path)
                
                # Verificar arquivos grandes (>50MB)
                try:
                    if os.path.getsize(file_path) > 50 * 1024 * 1024:
                        scan_results['large_files'].append(file_path)
                except OSError:
                    pass
                
                # Verificar arquivos obsoletos específicos
                if self._is_obsolete_file(file_path, rel_path):
                    scan_results['obsolete_files'].append(file_path)
        
        # Encontrar arquivos duplicados
        scan_results['duplicate_files'] = self._find_duplicate_files()
        
        return scan_results
    
    def _matches_patterns(self, filename: str, patterns: List[str]) -> bool:
        """
        Verifica se um arquivo corresponde a algum dos padrões.
        
        Args:
            filename: Nome do arquivo
            patterns: Lista de padrões para verificar
            
        Returns:
            True se corresponde a algum padrão, False caso contrário
        """
        return any(fnmatch.fnmatch(filename.lower(), pattern.lower()) 
                  for pattern in patterns)
    
    def _is_obsolete_file(self, file_path: str, rel_path: str) -> bool:
        """
        Verifica se um arquivo é obsoleto baseado em regras específicas.
        
        Args:
            file_path: Caminho completo do arquivo
            rel_path: Caminho relativo do arquivo
            
        Returns:
            True se o arquivo é obsoleto, False caso contrário
        """
        filename = os.path.basename(file_path)
        
        # Preservar arquivos importantes
        if filename in self.preserve_files:
            return False
        
        # Arquivos específicos obsoletos do projeto
        obsolete_patterns = [
            # Arquivos de migração antigos
            'migrate_*.bat', 'migrate_*.py', 'migration_*.txt',
            # Arquivos de teste antigos
            'test_*.py.bak', 'debug_*.py',
            # Configurações antigas
            'components.yaml.bak', 'components.yaml.original',
            # Scripts de setup antigos
            'setup_*.ps1.old', 'install_*.bat.backup'
        ]
        
        if self._matches_patterns(filename, obsolete_patterns):
            return True
        
        # Verificar estruturas duplicadas (ex: env_dev/env_dev/)
        if 'env_dev/env_dev/' in rel_path.replace('\\', '/'):
            return True
        
        # Arquivos muito antigos (mais de 30 dias sem modificação)
        try:
            mtime = os.path.getmtime(file_path)
            if time.time() - mtime > 30 * 24 * 3600:  # 30 dias
                # Só considerar obsoleto se for arquivo temporário ou de teste
                if any(pattern in filename.lower() for pattern in ['temp', 'test', 'debug', 'tmp']):
                    return True
        except OSError:
            pass
        
        return False
    
    def _find_duplicate_files(self) -> List[Tuple[str, List[str]]]:
        """
        Encontra arquivos duplicados baseado no hash MD5.
        
        Returns:
            Lista de tuplas (hash, lista_de_arquivos_duplicados)
        """
        file_hashes = {}
        duplicates = []
        
        logger.info("Procurando arquivos duplicados...")
        
        for root, dirs, files in os.walk(self.project_root):
            # Pular diretórios de controle de versão
            if '.git' in root or '.svn' in root:
                continue
            
            for file in files:
                file_path = os.path.join(root, file)
                
                # Pular arquivos muito grandes para verificação de hash
                try:
                    if os.path.getsize(file_path) > 100 * 1024 * 1024:  # 100MB
                        continue
                except OSError:
                    continue
                
                # Calcular hash do arquivo
                file_hash = self._calculate_file_hash(file_path)
                if file_hash:
                    if file_hash in file_hashes:
                        file_hashes[file_hash].append(file_path)
                    else:
                        file_hashes[file_hash] = [file_path]
        
        # Filtrar apenas arquivos que têm duplicatas
        for file_hash, file_list in file_hashes.items():
            if len(file_list) > 1:
                duplicates.append((file_hash, file_list))
        
        return duplicates
    
    def _calculate_file_hash(self, file_path: str) -> Optional[str]:
        """
        Calcula o hash MD5 de um arquivo.
        
        Args:
            file_path: Caminho do arquivo
            
        Returns:
            Hash MD5 do arquivo ou None se erro
        """
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logger.debug(f"Erro ao calcular hash de {file_path}: {e}")
            return None
    
    def clean_backup_files(self, backup_files: List[str], dry_run: bool = True) -> int:
        """
        Remove arquivos de backup.
        
        Args:
            backup_files: Lista de arquivos de backup
            dry_run: Se True, apenas simula a remoção
            
        Returns:
            Número de arquivos removidos
        """
        removed_count = 0
        
        for file_path in backup_files:
            try:
                if dry_run:
                    logger.info(f"[DRY RUN] Removeria: {file_path}")
                else:
                    os.remove(file_path)
                    logger.info(f"Removido: {file_path}")
                removed_count += 1
            except Exception as e:
                logger.error(f"Erro ao remover {file_path}: {e}")
        
        return removed_count
    
    def clean_log_files(self, log_files: List[str], keep_recent: int = 5, dry_run: bool = True) -> int:
        """
        Remove arquivos de log antigos, mantendo os mais recentes.
        
        Args:
            log_files: Lista de arquivos de log
            keep_recent: Número de logs recentes para manter
            dry_run: Se True, apenas simula a remoção
            
        Returns:
            Número de arquivos removidos
        """
        removed_count = 0
        
        # Agrupar logs por diretório
        log_groups = {}
        for log_file in log_files:
            log_dir = os.path.dirname(log_file)
            if log_dir not in log_groups:
                log_groups[log_dir] = []
            log_groups[log_dir].append(log_file)
        
        # Para cada grupo, manter apenas os mais recentes
        for log_dir, logs in log_groups.items():
            # Ordenar por data de modificação (mais recente primeiro)
            logs.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            
            # Remover logs antigos
            for log_file in logs[keep_recent:]:
                try:
                    if dry_run:
                        logger.info(f"[DRY RUN] Removeria log: {log_file}")
                    else:
                        os.remove(log_file)
                        logger.info(f"Removido log: {log_file}")
                    removed_count += 1
                except Exception as e:
                    logger.error(f"Erro ao remover log {log_file}: {e}")
        
        return removed_count
    
    def clean_cache_files(self, cache_files: List[str], dry_run: bool = True) -> int:
        """
        Remove arquivos de cache.
        
        Args:
            cache_files: Lista de arquivos de cache
            dry_run: Se True, apenas simula a remoção
            
        Returns:
            Número de arquivos removidos
        """
        removed_count = 0
        removed_dirs = set()
        
        for file_path in cache_files:
            try:
                if os.path.isdir(file_path):
                    if file_path not in removed_dirs:
                        if dry_run:
                            logger.info(f"[DRY RUN] Removeria diretório: {file_path}")
                        else:
                            shutil.rmtree(file_path)
                            logger.info(f"Removido diretório: {file_path}")
                        removed_dirs.add(file_path)
                        removed_count += 1
                else:
                    if dry_run:
                        logger.info(f"[DRY RUN] Removeria cache: {file_path}")
                    else:
                        os.remove(file_path)
                        logger.info(f"Removido cache: {file_path}")
                    removed_count += 1
            except Exception as e:
                logger.error(f"Erro ao remover cache {file_path}: {e}")
        
        return removed_count
    
    def clean_empty_directories(self, empty_dirs: List[str], dry_run: bool = True) -> int:
        """
        Remove diretórios vazios.
        
        Args:
            empty_dirs: Lista de diretórios vazios
            dry_run: Se True, apenas simula a remoção
            
        Returns:
            Número de diretórios removidos
        """
        removed_count = 0
        
        # Ordenar por profundidade (mais profundo primeiro)
        empty_dirs.sort(key=lambda x: x.count(os.sep), reverse=True)
        
        for dir_path in empty_dirs:
            try:
                # Verificar se ainda está vazio
                if os.path.exists(dir_path) and not os.listdir(dir_path):
                    if dry_run:
                        logger.info(f"[DRY RUN] Removeria diretório vazio: {dir_path}")
                    else:
                        os.rmdir(dir_path)
                        logger.info(f"Removido diretório vazio: {dir_path}")
                    removed_count += 1
            except Exception as e:
                logger.error(f"Erro ao remover diretório {dir_path}: {e}")
        
        return removed_count
    
    def resolve_duplicates(self, duplicates: List[Tuple[str, List[str]]], 
                          dry_run: bool = True) -> int:
        """
        Resolve arquivos duplicados mantendo o mais apropriado.
        
        Args:
            duplicates: Lista de tuplas (hash, lista_de_arquivos)
            dry_run: Se True, apenas simula a remoção
            
        Returns:
            Número de arquivos removidos
        """
        removed_count = 0
        
        for file_hash, file_list in duplicates:
            if len(file_list) <= 1:
                continue
            
            # Escolher qual arquivo manter (preferir o no local mais apropriado)
            best_file = self._choose_best_duplicate(file_list)
            
            # Remover os outros
            for file_path in file_list:
                if file_path != best_file:
                    try:
                        if dry_run:
                            logger.info(f"[DRY RUN] Removeria duplicata: {file_path}")
                        else:
                            os.remove(file_path)
                            logger.info(f"Removida duplicata: {file_path} (mantendo {best_file})")
                        removed_count += 1
                    except Exception as e:
                        logger.error(f"Erro ao remover duplicata {file_path}: {e}")
        
        return removed_count
    
    def _choose_best_duplicate(self, file_list: List[str]) -> str:
        """
        Escolhe o melhor arquivo entre duplicatas.
        
        Args:
            file_list: Lista de arquivos duplicados
            
        Returns:
            Caminho do arquivo a ser mantido
        """
        # Critérios de preferência (em ordem):
        # 1. Arquivo no diretório principal (não em subdiretórios)
        # 2. Arquivo com nome mais simples
        # 3. Arquivo mais recente
        
        def score_file(file_path: str) -> Tuple[int, int, float]:
            rel_path = os.path.relpath(file_path, self.project_root)
            
            # Penalizar arquivos em subdiretórios profundos
            depth_penalty = rel_path.count(os.sep)
            
            # Penalizar nomes complexos
            name_penalty = len(os.path.basename(file_path))
            
            # Preferir arquivos mais recentes
            try:
                mtime = os.path.getmtime(file_path)
            except OSError:
                mtime = 0
            
            return (depth_penalty, name_penalty, -mtime)
        
        # Ordenar por critérios e retornar o melhor
        file_list.sort(key=score_file)
        return file_list[0]
    
    def generate_cleanup_report(self, scan_results: Dict[str, List]) -> str:
        """
        Gera um relatório de limpeza.
        
        Args:
            scan_results: Resultados do escaneamento
            
        Returns:
            String com o relatório
        """
        report = []
        report.append("=== RELATÓRIO DE LIMPEZA DO PROJETO ===\n")
        
        total_files = sum(len(files) for files in scan_results.values() 
                         if isinstance(files, list))
        report.append(f"Total de itens encontrados: {total_files}\n")
        
        for category, items in scan_results.items():
            if isinstance(items, list) and items:
                report.append(f"{category.replace('_', ' ').title()}: {len(items)} itens")
                
                # Mostrar alguns exemplos
                for item in items[:3]:
                    if isinstance(item, tuple):  # Duplicatas
                        report.append(f"  - {len(item[1])} arquivos duplicados")
                    else:
                        rel_path = os.path.relpath(item, self.project_root)
                        report.append(f"  - {rel_path}")
                
                if len(items) > 3:
                    report.append(f"  ... e mais {len(items) - 3} itens")
                report.append("")
        
        return "\n".join(report)
    
    def full_cleanup(self, dry_run: bool = True) -> Dict[str, int]:
        """
        Executa limpeza completa do projeto.
        
        Args:
            dry_run: Se True, apenas simula as operações
            
        Returns:
            Dicionário com contadores de itens removidos
        """
        logger.info("Iniciando limpeza completa do projeto...")
        
        # Escanear projeto
        scan_results = self.scan_project()
        
        # Gerar relatório
        report = self.generate_cleanup_report(scan_results)
        logger.info(f"Relatório de escaneamento:\n{report}")
        
        # Executar limpezas
        cleanup_results = {}
        
        cleanup_results['backup_files'] = self.clean_backup_files(
            scan_results['backup_files'], dry_run
        )
        
        cleanup_results['log_files'] = self.clean_log_files(
            scan_results['log_files'], dry_run=dry_run
        )
        
        cleanup_results['cache_files'] = self.clean_cache_files(
            scan_results['cache_files'], dry_run
        )
        
        cleanup_results['empty_directories'] = self.clean_empty_directories(
            scan_results['empty_directories'], dry_run
        )
        
        cleanup_results['duplicate_files'] = self.resolve_duplicates(
            scan_results['duplicate_files'], dry_run
        )
        
        # Remover arquivos obsoletos
        cleanup_results['obsolete_files'] = self.clean_backup_files(
            scan_results['obsolete_files'], dry_run
        )
        
        total_removed = sum(cleanup_results.values())
        
        if dry_run:
            logger.info(f"[DRY RUN] Total de itens que seriam removidos: {total_removed}")
        else:
            logger.info(f"Limpeza concluída. Total de itens removidos: {total_removed}")
        
        return cleanup_results

def cleanup_project(project_root: str = None, dry_run: bool = True) -> Dict[str, int]:
    """
    Função utilitária para limpeza de projeto.
    
    Args:
        project_root: Caminho raiz do projeto (None para usar diretório atual)
        dry_run: Se True, apenas simula as operações
        
    Returns:
        Dicionário com contadores de itens removidos
    """
    if project_root is None:
        project_root = os.getcwd()
    
    cleaner = ProjectCleaner(project_root)
    return cleaner.full_cleanup(dry_run)

if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    # Determinar diretório do projeto
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir))  # Subir 2 níveis
    
    print(f"Limpando projeto em: {project_root}")
    
    # Executar limpeza em modo dry-run por padrão
    dry_run = True
    if len(sys.argv) > 1 and sys.argv[1] == "--execute":
        dry_run = False
        print("ATENÇÃO: Executando limpeza real (não é simulação)")
    else:
        print("Executando em modo simulação (dry-run)")
        print("Use --execute para executar a limpeza real")
    
    results = cleanup_project(project_root, dry_run)
    
    print("\n=== RESUMO DA LIMPEZA ===")
    for category, count in results.items():
        if count > 0:
            print(f"{category.replace('_', ' ').title()}: {count} itens")