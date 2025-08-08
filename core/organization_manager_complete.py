# -*- coding: utf-8 -*-
"""
Organization Manager Completo - Implementação final dos requisitos 5.1, 5.2, 5.3, 5.4 e 5.5
Manutenção de diretórios limpos e organizados com funcionalidades avançadas
"""

import os
import logging
import threading
import time
import json
import hashlib
import shutil
import glob
from typing import Dict, List, Optional, Callable, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

from env_dev.core.organization_manager import (
    OrganizationManager, CleanupResult, OrganizationResult, 
    BackupManagementResult, OptimizationResult, CleanupStatus, FileType
)

logger = logging.getLogger(__name__)

@dataclass
class DiskAnalysis:
    """Análise detalhada do uso de disco"""
    total_space: int
    used_space: int
    free_space: int
    temp_files_size: int
    log_files_size: int
    backup_files_size: int
    duplicate_files_size: int
    largest_files: List[Tuple[str, int]]  # (path, size)
    oldest_files: List[Tuple[str, datetime]]  # (path, modified_time)
    recommendations: List[str]

@dataclass
class AutoCleanupSchedule:
    """Configuração de limpeza automática"""
    enabled: bool = True
    interval_hours: int = 24
    cleanup_temp_files: bool = True
    cleanup_old_logs: bool = True
    cleanup_old_backups: bool = True
    max_temp_age_hours: int = 24
    max_log_age_days: int = 7
    max_backup_age_days: int = 30
    max_temp_size_mb: int = 1000

class CompleteOrganizationManager(OrganizationManager):
    """
    Implementação completa do Organization Manager com todas as funcionalidades
    necessárias para atender aos requisitos 5.1, 5.2, 5.3, 5.4 e 5.5
    """
    
    def __init__(self, base_path: Optional[str] = None):
        super().__init__(base_path)
        self.auto_cleanup_schedule = AutoCleanupSchedule()
        self.cleanup_thread = None
        self.cleanup_running = False
        self.cleanup_lock = threading.Lock()
        self.last_analysis = None
        
        # Diretórios gerenciados
        self.managed_directories = {
            'temp': ['temp', 'temp_download', 'tmp'],
            'logs': ['logs', 'log'],
            'downloads': ['downloads', 'download'],
            'backups': ['backups', 'backup', 'rollback'],
            'cache': ['cache', '.cache']
        }
        
        # Inicia limpeza automática se habilitada
        if self.auto_cleanup_schedule.enabled:
            self.start_auto_cleanup()
    
    def cleanup_temporary_files(self, max_age_hours: int = 24, 
                               aggressive: bool = False) -> CleanupResult:
        """
        Limpeza automática de arquivos temporários (Requisito 5.1)
        
        Args:
            max_age_hours: Idade máxima dos arquivos em horas
            aggressive: Se deve fazer limpeza agressiva
            
        Returns:
            CleanupResult: Resultado da limpeza
        """
        logger.info(f"Iniciando limpeza de arquivos temporários (idade máxima: {max_age_hours}h)")
        
        result = CleanupResult(status=CleanupStatus.IN_PROGRESS)
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        
        try:
            # Extensões de arquivos temporários
            temp_extensions = [
                '.tmp', '.temp', '.bak', '.old', '.cache', '.partial',
                '.download', '.crdownload', '.part', '~', '.swp'
            ]
            
            # Diretórios temporários para limpar
            temp_dirs = []
            for dir_type in ['temp', 'cache']:
                for dir_name in self.managed_directories[dir_type]:
                    temp_path = self.base_path / dir_name
                    if temp_path.exists():
                        temp_dirs.append(temp_path)
            
            # Adiciona diretórios temporários do sistema se agressivo
            if aggressive:
                import tempfile
                system_temp = Path(tempfile.gettempdir())
                temp_dirs.append(system_temp / "environment_dev_*")
            
            for temp_dir in temp_dirs:
                if not temp_dir.exists():
                    continue
                
                logger.debug(f"Limpando diretório temporário: {temp_dir}")
                
                # Limpa arquivos temporários
                for root, dirs, files in os.walk(temp_dir):
                    root_path = Path(root)
                    
                    for file in files:
                        file_path = root_path / file
                        
                        try:
                            # Verifica se é arquivo temporário
                            is_temp = (
                                any(file.endswith(ext) for ext in temp_extensions) or
                                file.startswith('tmp') or
                                file.startswith('temp')
                            )
                            
                            if is_temp:
                                # Verifica idade do arquivo
                                file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                                
                                if file_time < cutoff_time:
                                    file_size = file_path.stat().st_size
                                    file_path.unlink()
                                    
                                    result.files_removed += 1
                                    result.space_freed += file_size
                                    
                                    logger.debug(f"Removido arquivo temporário: {file_path}")
                        
                        except Exception as e:
                            error_msg = f"Erro ao remover {file_path}: {e}"
                            result.errors.append(error_msg)
                            logger.warning(error_msg)
                    
                    # Remove diretórios vazios
                    for dir_name in dirs:
                        dir_path = root_path / dir_name
                        try:
                            if dir_path.exists() and not any(dir_path.iterdir()):
                                dir_path.rmdir()
                                result.directories_removed += 1
                                logger.debug(f"Removido diretório vazio: {dir_path}")
                        except Exception as e:
                            logger.debug(f"Não foi possível remover diretório {dir_path}: {e}")
            
            result.status = CleanupStatus.COMPLETED
            result.details = {
                'max_age_hours': max_age_hours,
                'aggressive': aggressive,
                'directories_cleaned': len(temp_dirs)
            }
            
            logger.info(f"Limpeza de temporários concluída: {result.files_removed} arquivos, "
                       f"{self._format_size(result.space_freed)} liberados")
            
        except Exception as e:
            result.status = CleanupStatus.FAILED
            result.errors.append(f"Erro na limpeza de temporários: {e}")
            logger.error(f"Erro na limpeza de temporários: {e}")
        
        return result
    
    def organize_downloads(self, create_subdirs: bool = True) -> OrganizationResult:
        """
        Organização inteligente de downloads (Requisito 5.2)
        
        Args:
            create_subdirs: Se deve criar subdiretórios por tipo
            
        Returns:
            OrganizationResult: Resultado da organização
        """
        logger.info("Iniciando organização inteligente de downloads")
        
        result = OrganizationResult(status=CleanupStatus.IN_PROGRESS)
        
        try:
            # Encontra diretórios de download
            download_dirs = []
            for dir_name in self.managed_directories['downloads']:
                download_path = self.base_path / dir_name
                if download_path.exists():
                    download_dirs.append(download_path)
            
            if not download_dirs:
                result.status = CleanupStatus.SKIPPED
                result.warnings.append("Nenhum diretório de download encontrado")
                return result
            
            # Categorias de arquivos
            file_categories = {
                'executables': ['.exe', '.msi', '.dmg', '.pkg', '.deb', '.rpm'],
                'archives': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'],
                'documents': ['.pdf', '.doc', '.docx', '.txt', '.rtf'],
                'images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg'],
                'videos': ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv'],
                'audio': ['.mp3', '.wav', '.flac', '.aac', '.ogg'],
                'development': ['.py', '.js', '.html', '.css', '.json', '.xml']
            }
            
            for download_dir in download_dirs:
                logger.debug(f"Organizando diretório: {download_dir}")
                
                # Cria subdiretórios se necessário
                category_dirs = {}
                if create_subdirs:
                    for category in file_categories.keys():
                        category_dir = download_dir / category
                        category_dir.mkdir(exist_ok=True)
                        category_dirs[category] = category_dir
                        result.directories_created += 1
                
                # Organiza arquivos
                for file_path in download_dir.iterdir():
                    if file_path.is_file():
                        file_ext = file_path.suffix.lower()
                        
                        # Encontra categoria do arquivo
                        target_category = None
                        for category, extensions in file_categories.items():
                            if file_ext in extensions:
                                target_category = category
                                break
                        
                        if target_category and create_subdirs:
                            # Move arquivo para subdiretório apropriado
                            target_dir = category_dirs[target_category]
                            target_path = target_dir / file_path.name
                            
                            # Evita sobrescrever arquivos existentes
                            counter = 1
                            while target_path.exists():
                                name_parts = file_path.stem, counter, file_path.suffix
                                target_path = target_dir / f"{name_parts[0]}_{name_parts[1]}{name_parts[2]}"
                                counter += 1
                            
                            try:
                                shutil.move(str(file_path), str(target_path))
                                result.files_moved += 1
                                result.files_organized += 1
                                logger.debug(f"Movido {file_path.name} para {target_category}/")
                            except Exception as e:
                                error_msg = f"Erro ao mover {file_path}: {e}"
                                result.errors.append(error_msg)
                                logger.warning(error_msg)
                        else:
                            result.files_organized += 1
            
            result.status = CleanupStatus.COMPLETED
            result.details = {
                'directories_processed': len(download_dirs),
                'categories_created': len(file_categories) if create_subdirs else 0,
                'create_subdirs': create_subdirs
            }
            
            logger.info(f"Organização de downloads concluída: {result.files_organized} arquivos organizados")
            
        except Exception as e:
            result.status = CleanupStatus.FAILED
            result.errors.append(f"Erro na organização de downloads: {e}")
            logger.error(f"Erro na organização de downloads: {e}")
        
        return result    
 
   def rotate_logs(self, max_age_days: int = 7, max_size_mb: int = 100) -> CleanupResult:
        """
        Rotação automática de logs (Requisito 5.4)
        
        Args:
            max_age_days: Idade máxima dos logs em dias
            max_size_mb: Tamanho máximo dos logs em MB
            
        Returns:
            CleanupResult: Resultado da rotação
        """
        logger.info(f"Iniciando rotação de logs (idade máxima: {max_age_days} dias, "
                   f"tamanho máximo: {max_size_mb} MB)")
        
        result = CleanupResult(status=CleanupStatus.IN_PROGRESS)
        cutoff_time = datetime.now() - timedelta(days=max_age_days)
        max_size_bytes = max_size_mb * 1024 * 1024
        
        try:
            # Encontra diretórios de log
            log_dirs = []
            for dir_name in self.managed_directories['logs']:
                log_path = self.base_path / dir_name
                if log_path.exists():
                    log_dirs.append(log_path)
            
            if not log_dirs:
                result.status = CleanupStatus.SKIPPED
                result.warnings.append("Nenhum diretório de log encontrado")
                return result
            
            # Extensões de arquivos de log
            log_extensions = ['.log', '.txt', '.out', '.err']
            
            for log_dir in log_dirs:
                logger.debug(f"Processando diretório de logs: {log_dir}")
                
                # Cria diretório de arquivo se não existir
                archive_dir = log_dir / "archived"
                archive_dir.mkdir(exist_ok=True)
                
                for file_path in log_dir.iterdir():
                    if file_path.is_file() and file_path.suffix.lower() in log_extensions:
                        try:
                            file_stat = file_path.stat()
                            file_time = datetime.fromtimestamp(file_stat.st_mtime)
                            file_size = file_stat.st_size
                            
                            # Verifica se precisa rotacionar por idade
                            if file_time < cutoff_time:
                                # Arquiva log antigo
                                archive_name = f"{file_path.stem}_{file_time.strftime('%Y%m%d')}{file_path.suffix}"
                                archive_path = archive_dir / archive_name
                                
                                # Comprime se possível
                                try:
                                    import gzip
                                    with open(file_path, 'rb') as f_in:
                                        with gzip.open(f"{archive_path}.gz", 'wb') as f_out:
                                            shutil.copyfileobj(f_in, f_out)
                                    
                                    file_path.unlink()
                                    result.files_removed += 1
                                    result.space_freed += file_size
                                    
                                    logger.debug(f"Log arquivado e comprimido: {file_path.name}")
                                    
                                except ImportError:
                                    # Fallback: apenas move o arquivo
                                    shutil.move(str(file_path), str(archive_path))
                                    result.files_removed += 1
                                    
                                    logger.debug(f"Log arquivado: {file_path.name}")
                            
                            # Verifica se precisa rotacionar por tamanho
                            elif file_size > max_size_bytes:
                                # Rotaciona log grande
                                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                                rotated_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
                                rotated_path = archive_dir / rotated_name
                                
                                shutil.move(str(file_path), str(rotated_path))
                                
                                # Cria novo arquivo de log vazio
                                file_path.touch()
                                
                                result.files_removed += 1
                                logger.debug(f"Log rotacionado por tamanho: {file_path.name}")
                        
                        except Exception as e:
                            error_msg = f"Erro ao processar log {file_path}: {e}"
                            result.errors.append(error_msg)
                            logger.warning(error_msg)
                
                # Limpa arquivos muito antigos do diretório de arquivo
                archive_cutoff = datetime.now() - timedelta(days=max_age_days * 3)
                for archive_file in archive_dir.iterdir():
                    if archive_file.is_file():
                        try:
                            archive_time = datetime.fromtimestamp(archive_file.stat().st_mtime)
                            if archive_time < archive_cutoff:
                                archive_size = archive_file.stat().st_size
                                archive_file.unlink()
                                result.files_removed += 1
                                result.space_freed += archive_size
                                logger.debug(f"Arquivo antigo removido: {archive_file.name}")
                        except Exception as e:
                            logger.warning(f"Erro ao remover arquivo antigo {archive_file}: {e}")
            
            result.status = CleanupStatus.COMPLETED
            result.details = {
                'max_age_days': max_age_days,
                'max_size_mb': max_size_mb,
                'log_directories_processed': len(log_dirs)
            }
            
            logger.info(f"Rotação de logs concluída: {result.files_removed} arquivos processados, "
                       f"{self._format_size(result.space_freed)} liberados")
            
        except Exception as e:
            result.status = CleanupStatus.FAILED
            result.errors.append(f"Erro na rotação de logs: {e}")
            logger.error(f"Erro na rotação de logs: {e}")
        
        return result
    
    def manage_backups(self, max_backups: int = 10, max_age_days: int = 30) -> BackupManagementResult:
        """
        Gerenciamento inteligente de backups (Requisito 5.3)
        
        Args:
            max_backups: Número máximo de backups por componente
            max_age_days: Idade máxima dos backups em dias
            
        Returns:
            BackupManagementResult: Resultado do gerenciamento
        """
        logger.info(f"Iniciando gerenciamento de backups (máximo: {max_backups}, "
                   f"idade máxima: {max_age_days} dias)")
        
        result = BackupManagementResult(status=CleanupStatus.IN_PROGRESS)
        cutoff_time = datetime.now() - timedelta(days=max_age_days)
        
        try:
            # Encontra diretórios de backup
            backup_dirs = []
            for dir_name in self.managed_directories['backups']:
                backup_path = self.base_path / dir_name
                if backup_path.exists():
                    backup_dirs.append(backup_path)
            
            if not backup_dirs:
                result.status = CleanupStatus.SKIPPED
                result.warnings.append("Nenhum diretório de backup encontrado")
                return result
            
            for backup_dir in backup_dirs:
                logger.debug(f"Processando diretório de backup: {backup_dir}")
                
                # Agrupa backups por componente
                component_backups = {}
                
                for backup_file in backup_dir.iterdir():
                    if backup_file.is_file():
                        # Extrai nome do componente do nome do arquivo
                        # Formato esperado: component_name_timestamp.ext
                        name_parts = backup_file.stem.split('_')
                        if len(name_parts) >= 2:
                            component_name = '_'.join(name_parts[:-1])
                            
                            if component_name not in component_backups:
                                component_backups[component_name] = []
                            
                            component_backups[component_name].append(backup_file)
                
                # Processa backups de cada componente
                for component_name, backups in component_backups.items():
                    logger.debug(f"Processando backups do componente: {component_name}")
                    
                    # Ordena backups por data de modificação (mais recente primeiro)
                    backups.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                    
                    # Remove backups antigos
                    for backup_file in backups:
                        try:
                            backup_time = datetime.fromtimestamp(backup_file.stat().st_mtime)
                            
                            if backup_time < cutoff_time:
                                backup_size = backup_file.stat().st_size
                                backup_file.unlink()
                                
                                result.backups_removed += 1
                                result.space_freed += backup_size
                                
                                logger.debug(f"Backup antigo removido: {backup_file.name}")
                        
                        except Exception as e:
                            error_msg = f"Erro ao remover backup {backup_file}: {e}"
                            result.errors.append(error_msg)
                            logger.warning(error_msg)
                    
                    # Remove backups excedentes (mantém apenas os mais recentes)
                    if len(backups) > max_backups:
                        excess_backups = backups[max_backups:]
                        
                        for backup_file in excess_backups:
                            try:
                                if backup_file.exists():  # Pode ter sido removido por idade
                                    backup_size = backup_file.stat().st_size
                                    backup_file.unlink()
                                    
                                    result.backups_removed += 1
                                    result.space_freed += backup_size
                                    
                                    logger.debug(f"Backup excedente removido: {backup_file.name}")
                            
                            except Exception as e:
                                error_msg = f"Erro ao remover backup excedente {backup_file}: {e}"
                                result.errors.append(error_msg)
                                logger.warning(error_msg)
                    
                    result.backups_processed += len(backups)
                
                # Cria arquivo de índice de backups
                self._create_backup_index(backup_dir, component_backups)
            
            result.status = CleanupStatus.COMPLETED
            result.details = {
                'max_backups': max_backups,
                'max_age_days': max_age_days,
                'backup_directories_processed': len(backup_dirs),
                'components_processed': sum(len(cb) for cb in [
                    self._get_component_backups(bd) for bd in backup_dirs
                ])
            }
            
            logger.info(f"Gerenciamento de backups concluído: {result.backups_processed} backups processados, "
                       f"{result.backups_removed} removidos, {self._format_size(result.space_freed)} liberados")
            
        except Exception as e:
            result.status = CleanupStatus.FAILED
            result.errors.append(f"Erro no gerenciamento de backups: {e}")
            logger.error(f"Erro no gerenciamento de backups: {e}")
        
        return result
    
    def optimize_disk_usage(self, target_free_space_gb: float = 5.0) -> OptimizationResult:
        """
        Otimização automática de uso de disco (Requisito 5.5)
        
        Args:
            target_free_space_gb: Espaço livre desejado em GB
            
        Returns:
            OptimizationResult: Resultado da otimização
        """
        logger.info(f"Iniciando otimização de disco (espaço livre desejado: {target_free_space_gb} GB)")
        
        result = OptimizationResult(status=CleanupStatus.IN_PROGRESS)
        target_free_bytes = int(target_free_space_gb * 1024 * 1024 * 1024)
        
        try:
            # Analisa uso atual do disco
            analysis = self.analyze_disk_usage()
            
            if analysis.free_space >= target_free_bytes:
                result.status = CleanupStatus.SKIPPED
                result.recommendations.append(f"Espaço livre suficiente: {self._format_size(analysis.free_space)}")
                return result
            
            space_needed = target_free_bytes - analysis.free_space
            logger.info(f"Necessário liberar: {self._format_size(space_needed)}")
            
            # Estratégias de otimização (em ordem de prioridade)
            optimization_strategies = [
                ('cleanup_temp', self._optimize_temp_files),
                ('cleanup_logs', self._optimize_log_files),
                ('cleanup_old_backups', self._optimize_backup_files),
                ('remove_duplicates', self._optimize_duplicate_files),
                ('compress_large_files', self._optimize_large_files)
            ]
            
            space_freed = 0
            
            for strategy_name, strategy_func in optimization_strategies:
                if space_freed >= space_needed:
                    break
                
                logger.debug(f"Executando estratégia: {strategy_name}")
                
                try:
                    strategy_result = strategy_func(space_needed - space_freed)
                    space_freed += strategy_result.get('space_freed', 0)
                    
                    result.operations_performed.append(strategy_name)
                    result.total_space_freed += strategy_result.get('space_freed', 0)
                    
                    if strategy_result.get('errors'):
                        result.errors.extend(strategy_result['errors'])
                    
                    if strategy_result.get('warnings'):
                        result.warnings.extend(strategy_result['warnings'])
                
                except Exception as e:
                    error_msg = f"Erro na estratégia {strategy_name}: {e}"
                    result.errors.append(error_msg)
                    logger.warning(error_msg)
            
            # Gera recomendações adicionais
            if space_freed < space_needed:
                remaining_needed = space_needed - space_freed
                result.recommendations.extend([
                    f"Ainda necessário liberar: {self._format_size(remaining_needed)}",
                    "Considere mover arquivos grandes para armazenamento externo",
                    "Desinstale programas não utilizados",
                    "Execute limpeza de disco do sistema operacional"
                ])
            
            result.status = CleanupStatus.COMPLETED
            result.details = {
                'target_free_space_gb': target_free_space_gb,
                'space_needed': space_needed,
                'space_freed': space_freed,
                'strategies_used': len(result.operations_performed)
            }
            
            logger.info(f"Otimização de disco concluída: {self._format_size(result.total_space_freed)} liberados")
            
        except Exception as e:
            result.status = CleanupStatus.FAILED
            result.errors.append(f"Erro na otimização de disco: {e}")
            logger.error(f"Erro na otimização de disco: {e}")
        
        return result  
  
    def analyze_disk_usage(self) -> DiskAnalysis:
        """
        Análise detalhada do uso de disco
        
        Returns:
            DiskAnalysis: Análise completa do disco
        """
        logger.info("Iniciando análise de uso de disco")
        
        try:
            # Obtém informações básicas do disco
            total, used, free = shutil.disk_usage(self.base_path)
            
            analysis = DiskAnalysis(
                total_space=total,
                used_space=used,
                free_space=free,
                temp_files_size=0,
                log_files_size=0,
                backup_files_size=0,
                duplicate_files_size=0,
                largest_files=[],
                oldest_files=[],
                recommendations=[]
            )
            
            # Analisa tamanho por categoria
            file_sizes = {}
            file_ages = {}
            
            for root, dirs, files in os.walk(self.base_path):
                root_path = Path(root)
                
                for file in files:
                    file_path = root_path / file
                    
                    try:
                        file_stat = file_path.stat()
                        file_size = file_stat.st_size
                        file_time = datetime.fromtimestamp(file_stat.st_mtime)
                        
                        # Categoriza por tipo
                        if any(temp_dir in str(file_path) for temp_dir in self.managed_directories['temp']):
                            analysis.temp_files_size += file_size
                        elif any(log_dir in str(file_path) for log_dir in self.managed_directories['logs']):
                            analysis.log_files_size += file_size
                        elif any(backup_dir in str(file_path) for backup_dir in self.managed_directories['backups']):
                            analysis.backup_files_size += file_size
                        
                        # Coleta informações para análise
                        file_sizes[str(file_path)] = file_size
                        file_ages[str(file_path)] = file_time
                    
                    except Exception as e:
                        logger.debug(f"Erro ao analisar arquivo {file_path}: {e}")
            
            # Encontra maiores arquivos
            largest = sorted(file_sizes.items(), key=lambda x: x[1], reverse=True)[:20]
            analysis.largest_files = [(path, size) for path, size in largest]
            
            # Encontra arquivos mais antigos
            oldest = sorted(file_ages.items(), key=lambda x: x[1])[:20]
            analysis.oldest_files = [(path, time) for path, time in oldest]
            
            # Gera recomendações
            free_percent = (analysis.free_space / analysis.total_space) * 100
            
            if free_percent < 10:
                analysis.recommendations.append("Espaço livre crítico (<10%)")
            elif free_percent < 20:
                analysis.recommendations.append("Espaço livre baixo (<20%)")
            
            if analysis.temp_files_size > 1024 * 1024 * 1024:  # 1GB
                analysis.recommendations.append("Muitos arquivos temporários (>1GB)")
            
            if analysis.log_files_size > 500 * 1024 * 1024:  # 500MB
                analysis.recommendations.append("Logs ocupando muito espaço (>500MB)")
            
            if analysis.backup_files_size > 5 * 1024 * 1024 * 1024:  # 5GB
                analysis.recommendations.append("Backups ocupando muito espaço (>5GB)")
            
            self.last_analysis = analysis
            logger.info(f"Análise concluída: {self._format_size(analysis.free_space)} livres de "
                       f"{self._format_size(analysis.total_space)}")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Erro na análise de disco: {e}")
            return DiskAnalysis(
                total_space=0, used_space=0, free_space=0,
                temp_files_size=0, log_files_size=0, backup_files_size=0,
                duplicate_files_size=0, largest_files=[], oldest_files=[],
                recommendations=[f"Erro na análise: {e}"]
            )
    
    def start_auto_cleanup(self):
        """Inicia limpeza automática em thread separada"""
        if self.cleanup_running:
            logger.warning("Limpeza automática já está em execução")
            return
        
        def cleanup_worker():
            self.cleanup_running = True
            logger.info("Limpeza automática iniciada")
            
            while self.cleanup_running:
                try:
                    # Executa limpeza baseada na configuração
                    if self.auto_cleanup_schedule.cleanup_temp_files:
                        self.cleanup_temporary_files(
                            max_age_hours=self.auto_cleanup_schedule.max_temp_age_hours
                        )
                    
                    if self.auto_cleanup_schedule.cleanup_old_logs:
                        self.rotate_logs(max_age_days=self.auto_cleanup_schedule.max_log_age_days)
                    
                    if self.auto_cleanup_schedule.cleanup_old_backups:
                        self.manage_backups(max_age_days=self.auto_cleanup_schedule.max_backup_age_days)
                    
                    # Aguarda próximo ciclo
                    time.sleep(self.auto_cleanup_schedule.interval_hours * 3600)
                    
                except Exception as e:
                    logger.error(f"Erro na limpeza automática: {e}")
                    time.sleep(3600)  # Aguarda 1 hora em caso de erro
        
        self.cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        self.cleanup_thread.start()
    
    def stop_auto_cleanup(self):
        """Para a limpeza automática"""
        self.cleanup_running = False
        if self.cleanup_thread and self.cleanup_thread.is_alive():
            self.cleanup_thread.join(timeout=5)
        logger.info("Limpeza automática parada")
    
    # Métodos auxiliares para otimização
    def _optimize_temp_files(self, space_needed: int) -> Dict:
        """Otimiza arquivos temporários"""
        result = self.cleanup_temporary_files(max_age_hours=1, aggressive=True)
        return {
            'space_freed': result.space_freed,
            'errors': result.errors,
            'warnings': result.warnings
        }
    
    def _optimize_log_files(self, space_needed: int) -> Dict:
        """Otimiza arquivos de log"""
        result = self.rotate_logs(max_age_days=3, max_size_mb=50)
        return {
            'space_freed': result.space_freed,
            'errors': result.errors,
            'warnings': result.warnings
        }
    
    def _optimize_backup_files(self, space_needed: int) -> Dict:
        """Otimiza arquivos de backup"""
        result = self.manage_backups(max_backups=5, max_age_days=15)
        return {
            'space_freed': result.space_freed,
            'errors': result.errors,
            'warnings': result.warnings
        }
    
    def _optimize_duplicate_files(self, space_needed: int) -> Dict:
        """Remove arquivos duplicados"""
        space_freed = 0
        errors = []
        warnings = []
        
        try:
            # Implementação básica de detecção de duplicatas
            file_hashes = {}
            duplicates_found = []
            
            for root, dirs, files in os.walk(self.base_path):
                for file in files:
                    file_path = Path(root) / file
                    
                    try:
                        if file_path.stat().st_size > 1024:  # Apenas arquivos > 1KB
                            file_hash = self._calculate_file_hash(file_path)
                            
                            if file_hash in file_hashes:
                                duplicates_found.append((file_path, file_hashes[file_hash]))
                            else:
                                file_hashes[file_hash] = file_path
                    
                    except Exception as e:
                        logger.debug(f"Erro ao processar {file_path}: {e}")
            
            # Remove duplicatas (mantém o mais antigo)
            for duplicate_path, original_path in duplicates_found:
                try:
                    if duplicate_path.stat().st_mtime > original_path.stat().st_mtime:
                        file_size = duplicate_path.stat().st_size
                        duplicate_path.unlink()
                        space_freed += file_size
                        logger.debug(f"Duplicata removida: {duplicate_path}")
                
                except Exception as e:
                    errors.append(f"Erro ao remover duplicata {duplicate_path}: {e}")
        
        except Exception as e:
            errors.append(f"Erro na detecção de duplicatas: {e}")
        
        return {
            'space_freed': space_freed,
            'errors': errors,
            'warnings': warnings
        }
    
    def _optimize_large_files(self, space_needed: int) -> Dict:
        """Comprime arquivos grandes"""
        space_freed = 0
        errors = []
        warnings = []
        
        try:
            import gzip
            
            # Encontra arquivos grandes (>100MB) que podem ser comprimidos
            large_files = []
            compressible_extensions = ['.log', '.txt', '.json', '.xml', '.csv']
            
            for root, dirs, files in os.walk(self.base_path):
                for file in files:
                    file_path = Path(root) / file
                    
                    try:
                        if (file_path.stat().st_size > 100 * 1024 * 1024 and  # >100MB
                            file_path.suffix.lower() in compressible_extensions):
                            large_files.append(file_path)
                    
                    except Exception as e:
                        logger.debug(f"Erro ao verificar {file_path}: {e}")
            
            # Comprime arquivos grandes
            for file_path in large_files[:5]:  # Limita a 5 arquivos por vez
                try:
                    original_size = file_path.stat().st_size
                    compressed_path = file_path.with_suffix(file_path.suffix + '.gz')
                    
                    with open(file_path, 'rb') as f_in:
                        with gzip.open(compressed_path, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    
                    compressed_size = compressed_path.stat().st_size
                    
                    if compressed_size < original_size * 0.8:  # Só substitui se compressão > 20%
                        file_path.unlink()
                        space_freed += (original_size - compressed_size)
                        logger.debug(f"Arquivo comprimido: {file_path}")
                    else:
                        compressed_path.unlink()  # Remove compressão ineficiente
                
                except Exception as e:
                    errors.append(f"Erro ao comprimir {file_path}: {e}")
        
        except ImportError:
            warnings.append("Módulo gzip não disponível para compressão")
        except Exception as e:
            errors.append(f"Erro na compressão de arquivos: {e}")
        
        return {
            'space_freed': space_freed,
            'errors': errors,
            'warnings': warnings
        }
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calcula hash MD5 de um arquivo"""
        hash_md5 = hashlib.md5()
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        
        return hash_md5.hexdigest()
    
    def _create_backup_index(self, backup_dir: Path, component_backups: Dict):
        """Cria índice de backups"""
        try:
            index_file = backup_dir / "backup_index.json"
            
            index_data = {
                'created': datetime.now().isoformat(),
                'components': {}
            }
            
            for component, backups in component_backups.items():
                index_data['components'][component] = [
                    {
                        'file': backup.name,
                        'size': backup.stat().st_size,
                        'created': datetime.fromtimestamp(backup.stat().st_mtime).isoformat()
                    }
                    for backup in backups if backup.exists()
                ]
            
            with open(index_file, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, indent=2, ensure_ascii=False)
        
        except Exception as e:
            logger.warning(f"Erro ao criar índice de backups: {e}")
    
    def _get_component_backups(self, backup_dir: Path) -> Dict:
        """Obtém backups agrupados por componente"""
        component_backups = {}
        
        if not backup_dir.exists():
            return component_backups
        
        for backup_file in backup_dir.iterdir():
            if backup_file.is_file():
                name_parts = backup_file.stem.split('_')
                if len(name_parts) >= 2:
                    component_name = '_'.join(name_parts[:-1])
                    
                    if component_name not in component_backups:
                        component_backups[component_name] = []
                    
                    component_backups[component_name].append(backup_file)
        
        return component_backups
    
    def _format_size(self, size_bytes: int) -> str:
        """Formata tamanho em bytes para formato legível"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
    
    def get_organization_statistics(self) -> Dict:
        """
        Retorna estatísticas de organização
        
        Returns:
            Dict: Estatísticas detalhadas
        """
        try:
            stats = {
                'last_analysis': self.last_analysis.__dict__ if self.last_analysis else None,
                'auto_cleanup_enabled': self.auto_cleanup_schedule.enabled,
                'cleanup_interval_hours': self.auto_cleanup_schedule.interval_hours,
                'managed_directories': len(sum(self.managed_directories.values(), [])),
                'cleanup_running': self.cleanup_running
            }
            
            # Adiciona estatísticas de espaço se análise disponível
            if self.last_analysis:
                stats.update({
                    'total_space_gb': self.last_analysis.total_space / (1024**3),
                    'free_space_gb': self.last_analysis.free_space / (1024**3),
                    'free_space_percent': (self.last_analysis.free_space / self.last_analysis.total_space) * 100,
                    'temp_files_mb': self.last_analysis.temp_files_size / (1024**2),
                    'log_files_mb': self.last_analysis.log_files_size / (1024**2),
                    'backup_files_mb': self.last_analysis.backup_files_size / (1024**2)
                })
            
            return stats
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {e}")
            return {'error': str(e)}


# Instância global completa
complete_organization_manager = CompleteOrganizationManager()