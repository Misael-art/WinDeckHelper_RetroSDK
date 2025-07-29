# -*- coding: utf-8 -*-
"""
Organization Manager para Environment Dev Script
Módulo responsável por manutenção de diretórios limpos e organizados
"""

import os
import sys
import shutil
import logging
import glob
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta

from env_dev.utils.disk_space import get_disk_space, format_size
from env_dev.utils.permission_checker import check_write_permission
from env_dev.core.error_handler import EnvDevError, ErrorSeverity, ErrorCategory

logger = logging.getLogger(__name__)

class CleanupStatus(Enum):
    """Status da operação de limpeza"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class FileType(Enum):
    """Tipos de arquivos para organização"""
    TEMPORARY = "temporary"
    DOWNLOAD = "download"
    LOG = "log"
    BACKUP = "backup"
    CACHE = "cache"
    INSTALLER = "installer"

@dataclass
class CleanupResult:
    """Resultado de uma operação de limpeza"""
    status: CleanupStatus
    files_removed: int = 0
    directories_removed: int = 0
    space_freed: int = 0  # bytes
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class OrganizationResult:
    """Resultado de uma operação de organização"""
    status: CleanupStatus
    files_organized: int = 0
    directories_created: int = 0
    files_moved: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class BackupManagementResult:
    """Resultado do gerenciamento de backups"""
    status: CleanupStatus
    backups_processed: int = 0
    backups_archived: int = 0
    backups_removed: int = 0
    space_freed: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class OptimizationResult:
    """Resultado da otimização de espaço"""
    status: CleanupStatus
    total_space_freed: int = 0
    operations_performed: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

class OrganizationManager:
    """
    Gerenciador de organização automática de arquivos e diretórios.
    
    Responsável por:
    - Limpeza automática de arquivos temporários
    - Organização inteligente de downloads
    - Rotação automática de logs
    - Gerenciamento de backups
    - Otimização de uso de disco
    """
    
    def __init__(self, base_path: Optional[Path] = None):
        """
        Inicializa o OrganizationManager.
        
        Args:
            base_path: Caminho base do projeto (padrão: diretório atual)
        """
        self.base_path = Path(base_path) if base_path else Path.cwd()
        self.temp_dir = self.base_path / "temp"
        self.downloads_dir = self.base_path / "downloads"
        self.logs_dir = self.base_path / "logs"
        self.backups_dir = self.base_path / "backups"
        self.cache_dir = self.base_path / "cache"
        
        # Configurações padrão
        self.max_log_age_days = 30
        self.max_temp_age_hours = 24
        self.max_backup_age_days = 90
        self.max_log_files = 50
        self.max_backup_size_mb = 1000
        
        logger.info(f"OrganizationManager inicializado com base_path: {self.base_path}")
    
    def cleanup_temporary_files(self) -> CleanupResult:
        """
        Remove arquivos temporários antigos e desnecessários.
        
        Returns:
            CleanupResult: Resultado da operação de limpeza
        """
        logger.info("Iniciando limpeza de arquivos temporários")
        result = CleanupResult(status=CleanupStatus.IN_PROGRESS)
        
        try:
            # Diretórios temporários para limpar
            temp_dirs = [
                self.temp_dir,
                self.base_path / "temp_download",
                self.cache_dir / "temp",
                Path.cwd() / "temp"
            ]
            
            cutoff_time = datetime.now() - timedelta(hours=self.max_temp_age_hours)
            
            for temp_dir in temp_dirs:
                if not temp_dir.exists():
                    continue
                    
                logger.debug(f"Limpando diretório temporário: {temp_dir}")
                dir_result = self._cleanup_directory(
                    temp_dir, 
                    cutoff_time=cutoff_time,
                    file_patterns=["*.tmp", "*.temp", "*.cache", "*.partial", "*.download"]
                )
                
                result.files_removed += dir_result.files_removed
                result.directories_removed += dir_result.directories_removed
                result.space_freed += dir_result.space_freed
                result.errors.extend(dir_result.errors)
                result.warnings.extend(dir_result.warnings)
            
            # Limpar arquivos temporários específicos do sistema
            self._cleanup_system_temp_files(result)
            
            result.status = CleanupStatus.COMPLETED
            logger.info(f"Limpeza de temporários concluída: {result.files_removed} arquivos, "
                       f"{format_size(result.space_freed)} liberados")
            
        except Exception as e:
            result.status = CleanupStatus.FAILED
            result.errors.append(f"Erro na limpeza de temporários: {str(e)}")
            logger.error(f"Erro na limpeza de temporários: {e}", exc_info=True)
        
        return result    

    def organize_downloads(self) -> OrganizationResult:
        """
        Organiza downloads em estrutura hierárquica por categoria e data.
        
        Returns:
            OrganizationResult: Resultado da operação de organização
        """
        logger.info("Iniciando organização de downloads")
        result = OrganizationResult(status=CleanupStatus.IN_PROGRESS)
        
        try:
            if not self.downloads_dir.exists():
                self.downloads_dir.mkdir(parents=True, exist_ok=True)
                result.directories_created += 1
            
            # Estrutura de organização por categoria
            categories = {
                'installers': ['.exe', '.msi', '.dmg', '.pkg', '.deb', '.rpm'],
                'archives': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'],
                'drivers': ['.inf', '.sys', '.cat', '.cer'],
                'documents': ['.pdf', '.doc', '.docx', '.txt', '.md'],
                'images': ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico'],
                'others': []  # Arquivos que não se encaixam em outras categorias
            }
            
            # Criar estrutura de diretórios por categoria
            for category in categories.keys():
                category_dir = self.downloads_dir / category
                if not category_dir.exists():
                    category_dir.mkdir(parents=True, exist_ok=True)
                    result.directories_created += 1
            
            # Organizar arquivos existentes
            for file_path in self.downloads_dir.iterdir():
                if file_path.is_file():
                    category = self._get_file_category(file_path, categories)
                    target_dir = self.downloads_dir / category
                    
                    # Criar subdiretório por data se necessário
                    file_date = datetime.fromtimestamp(file_path.stat().st_mtime)
                    date_dir = target_dir / file_date.strftime("%Y-%m")
                    
                    if not date_dir.exists():
                        date_dir.mkdir(parents=True, exist_ok=True)
                        result.directories_created += 1
                    
                    # Mover arquivo para categoria apropriada
                    target_path = date_dir / file_path.name
                    if not target_path.exists():
                        shutil.move(str(file_path), str(target_path))
                        result.files_moved += 1
                        logger.debug(f"Arquivo movido: {file_path} -> {target_path}")
            
            result.status = CleanupStatus.COMPLETED
            logger.info(f"Organização de downloads concluída: {result.files_moved} arquivos organizados")
            
        except Exception as e:
            result.status = CleanupStatus.FAILED
            result.errors.append(f"Erro na organização de downloads: {str(e)}")
            logger.error(f"Erro na organização de downloads: {e}", exc_info=True)
        
        return result
    
    def rotate_logs(self) -> CleanupResult:
        """
        Executa rotação automática de logs, arquivando logs antigos.
        
        Returns:
            CleanupResult: Resultado da operação de rotação
        """
        logger.info("Iniciando rotação de logs")
        result = CleanupResult(status=CleanupStatus.IN_PROGRESS)
        
        try:
            if not self.logs_dir.exists():
                logger.warning("Diretório de logs não existe")
                result.status = CleanupStatus.SKIPPED
                return result
            
            cutoff_date = datetime.now() - timedelta(days=self.max_log_age_days)
            archive_dir = self.logs_dir / "archived"
            
            if not archive_dir.exists():
                archive_dir.mkdir(parents=True, exist_ok=True)
            
            # Processar arquivos de log
            log_files = list(self.logs_dir.glob("*.log")) + list(self.logs_dir.glob("*.json"))
            log_files = [f for f in log_files if f.is_file()]
            
            # Ordenar por data de modificação (mais antigos primeiro)
            log_files.sort(key=lambda x: x.stat().st_mtime)
            
            # Arquivar logs antigos
            for log_file in log_files:
                file_date = datetime.fromtimestamp(log_file.stat().st_mtime)
                
                if file_date < cutoff_date or len(log_files) > self.max_log_files:
                    # Criar estrutura de arquivo por ano/mês
                    year_month = file_date.strftime("%Y-%m")
                    archive_subdir = archive_dir / year_month
                    
                    if not archive_subdir.exists():
                        archive_subdir.mkdir(parents=True, exist_ok=True)
                    
                    # Mover para arquivo
                    archive_path = archive_subdir / log_file.name
                    if not archive_path.exists():
                        shutil.move(str(log_file), str(archive_path))
                        result.files_removed += 1
                        result.space_freed += archive_path.stat().st_size
                        logger.debug(f"Log arquivado: {log_file} -> {archive_path}")
            
            # Comprimir arquivos antigos se necessário
            self._compress_old_archives(archive_dir, result)
            
            result.status = CleanupStatus.COMPLETED
            logger.info(f"Rotação de logs concluída: {result.files_removed} logs arquivados")
            
        except Exception as e:
            result.status = CleanupStatus.FAILED
            result.errors.append(f"Erro na rotação de logs: {str(e)}")
            logger.error(f"Erro na rotação de logs: {e}", exc_info=True)
        
        return result
    
    def manage_backups(self) -> BackupManagementResult:
        """
        Gerencia backups existentes, removendo antigos e organizando por data.
        
        Returns:
            BackupManagementResult: Resultado do gerenciamento de backups
        """
        logger.info("Iniciando gerenciamento de backups")
        result = BackupManagementResult(status=CleanupStatus.IN_PROGRESS)
        
        try:
            if not self.backups_dir.exists():
                logger.warning("Diretório de backups não existe")
                result.status = CleanupStatus.SKIPPED
                return result
            
            cutoff_date = datetime.now() - timedelta(days=self.max_backup_age_days)
            
            # Processar diretórios de backup
            backup_dirs = [d for d in self.backups_dir.iterdir() if d.is_dir()]
            
            for backup_dir in backup_dirs:
                try:
                    # Extrair data do nome do backup (formato: backup_YYYYMMDD_HHMMSS_*)
                    backup_date = self._extract_backup_date(backup_dir.name)
                    
                    if backup_date and backup_date < cutoff_date:
                        # Backup muito antigo - remover
                        dir_size = self._get_directory_size(backup_dir)
                        shutil.rmtree(backup_dir)
                        result.backups_removed += 1
                        result.space_freed += dir_size
                        logger.debug(f"Backup antigo removido: {backup_dir}")
                    
                    elif backup_date:
                        # Backup válido - verificar se precisa ser arquivado
                        if self._should_archive_backup(backup_dir):
                            self._archive_backup(backup_dir, result)
                    
                    result.backups_processed += 1
                    
                except Exception as e:
                    result.errors.append(f"Erro processando backup {backup_dir}: {str(e)}")
                    logger.error(f"Erro processando backup {backup_dir}: {e}")
            
            # Verificar se há muitos backups (manter apenas os mais recentes)
            self._cleanup_excess_backups(result)
            
            result.status = CleanupStatus.COMPLETED
            logger.info(f"Gerenciamento de backups concluído: {result.backups_processed} processados, "
                       f"{result.backups_removed} removidos")
            
        except Exception as e:
            result.status = CleanupStatus.FAILED
            result.errors.append(f"Erro no gerenciamento de backups: {str(e)}")
            logger.error(f"Erro no gerenciamento de backups: {e}", exc_info=True)
        
        return result 
   
    def optimize_disk_usage(self) -> OptimizationResult:
        """
        Otimiza o uso de disco executando várias operações de limpeza.
        
        Returns:
            OptimizationResult: Resultado da otimização
        """
        logger.info("Iniciando otimização de uso de disco")
        result = OptimizationResult(status=CleanupStatus.IN_PROGRESS)
        
        try:
            # Executar operações de limpeza em sequência
            operations = [
                ("Limpeza de temporários", self.cleanup_temporary_files),
                ("Rotação de logs", self.rotate_logs),
                ("Gerenciamento de backups", self.manage_backups)
            ]
            
            for operation_name, operation_func in operations:
                try:
                    logger.debug(f"Executando: {operation_name}")
                    op_result = operation_func()
                    
                    if hasattr(op_result, 'space_freed'):
                        result.total_space_freed += op_result.space_freed
                    
                    result.operations_performed.append(operation_name)
                    
                    if op_result.errors:
                        result.errors.extend([f"{operation_name}: {err}" for err in op_result.errors])
                    
                    if op_result.warnings:
                        result.warnings.extend([f"{operation_name}: {warn}" for warn in op_result.warnings])
                    
                except Exception as e:
                    error_msg = f"Erro em {operation_name}: {str(e)}"
                    result.errors.append(error_msg)
                    logger.error(error_msg)
            
            # Detectar arquivos desnecessários adicionais
            self._detect_unnecessary_files(result)
            
            # Gerar recomendações
            self._generate_optimization_recommendations(result)
            
            result.status = CleanupStatus.COMPLETED
            logger.info(f"Otimização concluída: {format_size(result.total_space_freed)} liberados")
            
        except Exception as e:
            result.status = CleanupStatus.FAILED
            result.errors.append(f"Erro na otimização: {str(e)}")
            logger.error(f"Erro na otimização: {e}", exc_info=True)
        
        return result
    
    # Métodos auxiliares privados
    
    def _cleanup_directory(self, directory: Path, cutoff_time: datetime = None, 
                          file_patterns: List[str] = None) -> CleanupResult:
        """
        Limpa um diretório específico baseado em critérios.
        
        Args:
            directory: Diretório para limpar
            cutoff_time: Remover arquivos mais antigos que este tempo
            file_patterns: Padrões de arquivos para remover
        
        Returns:
            CleanupResult: Resultado da limpeza
        """
        result = CleanupResult(status=CleanupStatus.IN_PROGRESS)
        
        if not directory.exists():
            result.status = CleanupStatus.SKIPPED
            return result
        
        try:
            for item in directory.rglob("*"):
                if item.is_file():
                    should_remove = False
                    
                    # Verificar padrões de arquivo primeiro
                    matches_pattern = False
                    if file_patterns:
                        for pattern in file_patterns:
                            if item.match(pattern):
                                matches_pattern = True
                                break
                    
                    # Se corresponde ao padrão, verificar idade
                    if matches_pattern:
                        if cutoff_time:
                            file_time = datetime.fromtimestamp(item.stat().st_mtime)
                            if file_time < cutoff_time:
                                should_remove = True
                        else:
                            # Se não há cutoff_time, remover todos os arquivos que correspondem ao padrão
                            should_remove = True
                    elif cutoff_time and not file_patterns:
                        # Se não há padrões, mas há cutoff_time, remover arquivos antigos
                        file_time = datetime.fromtimestamp(item.stat().st_mtime)
                        if file_time < cutoff_time:
                            should_remove = True
                    
                    if should_remove:
                        try:
                            file_size = item.stat().st_size
                            item.unlink()
                            result.files_removed += 1
                            result.space_freed += file_size
                        except Exception as e:
                            result.errors.append(f"Erro removendo {item}: {str(e)}")
            
            # Remover diretórios vazios
            self._remove_empty_directories(directory, result)
            
            result.status = CleanupStatus.COMPLETED
            
        except Exception as e:
            result.status = CleanupStatus.FAILED
            result.errors.append(f"Erro limpando diretório {directory}: {str(e)}")
        
        return result
    
    def _cleanup_system_temp_files(self, result: CleanupResult):
        """
        Limpa arquivos temporários específicos do sistema.
        
        Args:
            result: Resultado para atualizar
        """
        try:
            # Arquivos temporários comuns do Windows
            if os.name == 'nt':
                temp_patterns = [
                    os.path.expandvars(r"%TEMP%\*.tmp"),
                    os.path.expandvars(r"%TEMP%\*.temp"),
                    os.path.expandvars(r"%LOCALAPPDATA%\Temp\*.tmp")
                ]
                
                for pattern in temp_patterns:
                    for file_path in glob.glob(pattern):
                        try:
                            file_size = os.path.getsize(file_path)
                            os.remove(file_path)
                            result.files_removed += 1
                            result.space_freed += file_size
                        except Exception as e:
                            result.warnings.append(f"Não foi possível remover {file_path}: {str(e)}")
            
        except Exception as e:
            result.warnings.append(f"Erro na limpeza de temporários do sistema: {str(e)}")
    
    def _get_file_category(self, file_path: Path, categories: Dict[str, List[str]]) -> str:
        """
        Determina a categoria de um arquivo baseado na extensão.
        
        Args:
            file_path: Caminho do arquivo
            categories: Dicionário de categorias e extensões
        
        Returns:
            str: Nome da categoria
        """
        file_ext = file_path.suffix.lower()
        
        for category, extensions in categories.items():
            if file_ext in extensions:
                return category
        
        return 'others'
    
    def _compress_old_archives(self, archive_dir: Path, result: CleanupResult):
        """
        Comprime arquivos de log antigos para economizar espaço.
        
        Args:
            archive_dir: Diretório de arquivos
            result: Resultado para atualizar
        """
        try:
            import gzip
            
            # Comprimir logs com mais de 3 meses
            cutoff_date = datetime.now() - timedelta(days=90)
            
            for log_file in archive_dir.rglob("*.log"):
                if log_file.is_file():
                    file_date = datetime.fromtimestamp(log_file.stat().st_mtime)
                    
                    if file_date < cutoff_date and not log_file.name.endswith('.gz'):
                        compressed_path = log_file.with_suffix(log_file.suffix + '.gz')
                        
                        with open(log_file, 'rb') as f_in:
                            with gzip.open(compressed_path, 'wb') as f_out:
                                shutil.copyfileobj(f_in, f_out)
                        
                        original_size = log_file.stat().st_size
                        compressed_size = compressed_path.stat().st_size
                        
                        log_file.unlink()
                        result.space_freed += (original_size - compressed_size)
                        
        except ImportError:
            result.warnings.append("Módulo gzip não disponível para compressão")
        except Exception as e:
            result.warnings.append(f"Erro na compressão de arquivos: {str(e)}")
    
    def _extract_backup_date(self, backup_name: str) -> Optional[datetime]:
        """
        Extrai a data de um nome de backup.
        
        Args:
            backup_name: Nome do diretório de backup
        
        Returns:
            datetime: Data extraída ou None se não conseguir extrair
        """
        try:
            # Formato esperado: backup_YYYYMMDD_HHMMSS_*
            parts = backup_name.split('_')
            if len(parts) >= 3 and parts[0] == 'backup':
                date_str = f"{parts[1]}_{parts[2]}"
                return datetime.strptime(date_str, "%Y%m%d_%H%M%S")
        except Exception:
            pass
        
        return None 
   
    def _get_directory_size(self, directory: Path) -> int:
        """
        Calcula o tamanho total de um diretório.
        
        Args:
            directory: Diretório para calcular
        
        Returns:
            int: Tamanho em bytes
        """
        total_size = 0
        try:
            for item in directory.rglob("*"):
                if item.is_file():
                    total_size += item.stat().st_size
        except Exception as e:
            logger.warning(f"Erro calculando tamanho de {directory}: {e}")
        
        return total_size
    
    def _should_archive_backup(self, backup_dir: Path) -> bool:
        """
        Determina se um backup deve ser arquivado.
        
        Args:
            backup_dir: Diretório do backup
        
        Returns:
            bool: True se deve ser arquivado
        """
        try:
            # Arquivar backups maiores que o limite configurado
            dir_size = self._get_directory_size(backup_dir)
            size_mb = dir_size / (1024 * 1024)
            
            return size_mb > self.max_backup_size_mb
            
        except Exception:
            return False
    
    def _archive_backup(self, backup_dir: Path, result: BackupManagementResult):
        """
        Arquiva um backup comprimindo-o.
        
        Args:
            backup_dir: Diretório do backup
            result: Resultado para atualizar
        """
        try:
            import zipfile
            
            archive_path = backup_dir.with_suffix('.zip')
            
            with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in backup_dir.rglob("*"):
                    if file_path.is_file():
                        arcname = file_path.relative_to(backup_dir)
                        zipf.write(file_path, arcname)
            
            # Calcular espaço economizado
            original_size = self._get_directory_size(backup_dir)
            compressed_size = archive_path.stat().st_size
            
            # Remover diretório original
            shutil.rmtree(backup_dir)
            
            result.backups_archived += 1
            result.space_freed += (original_size - compressed_size)
            
            logger.debug(f"Backup arquivado: {backup_dir} -> {archive_path}")
            
        except ImportError:
            result.warnings.append("Módulo zipfile não disponível para arquivamento")
        except Exception as e:
            result.errors.append(f"Erro arquivando backup {backup_dir}: {str(e)}")
    
    def _cleanup_excess_backups(self, result: BackupManagementResult):
        """
        Remove backups em excesso, mantendo apenas os mais recentes.
        
        Args:
            result: Resultado para atualizar
        """
        try:
            max_backups = 10  # Manter apenas os 10 backups mais recentes
            
            # Listar todos os backups (diretórios e arquivos zip)
            backups = []
            
            for item in self.backups_dir.iterdir():
                if item.is_dir() or item.suffix == '.zip':
                    backup_date = self._extract_backup_date(item.stem)
                    if backup_date:
                        backups.append((backup_date, item))
            
            # Ordenar por data (mais recentes primeiro)
            backups.sort(key=lambda x: x[0], reverse=True)
            
            # Remover backups em excesso
            for _, backup_item in backups[max_backups:]:
                try:
                    if backup_item.is_dir():
                        size = self._get_directory_size(backup_item)
                        shutil.rmtree(backup_item)
                    else:
                        size = backup_item.stat().st_size
                        backup_item.unlink()
                    
                    result.backups_removed += 1
                    result.space_freed += size
                    
                except Exception as e:
                    result.errors.append(f"Erro removendo backup {backup_item}: {str(e)}")
            
        except Exception as e:
            result.errors.append(f"Erro na limpeza de backups em excesso: {str(e)}")
    
    def _remove_empty_directories(self, base_dir: Path, result: CleanupResult):
        """
        Remove diretórios vazios recursivamente.
        
        Args:
            base_dir: Diretório base
            result: Resultado para atualizar
        """
        try:
            for dir_path in sorted(base_dir.rglob("*"), key=lambda x: len(str(x)), reverse=True):
                if dir_path.is_dir() and dir_path != base_dir:
                    try:
                        if not any(dir_path.iterdir()):
                            dir_path.rmdir()
                            result.directories_removed += 1
                    except Exception:
                        pass  # Diretório não está vazio ou não pode ser removido
        except Exception as e:
            result.warnings.append(f"Erro removendo diretórios vazios: {str(e)}")
    
    def _detect_unnecessary_files(self, result: OptimizationResult):
        """
        Detecta arquivos desnecessários que podem ser removidos.
        
        Args:
            result: Resultado para atualizar
        """
        try:
            unnecessary_patterns = [
                "*.tmp", "*.temp", "*.cache", "*.bak", "*.old",
                "Thumbs.db", ".DS_Store", "desktop.ini"
            ]
            
            for pattern in unnecessary_patterns:
                for file_path in self.base_path.rglob(pattern):
                    if file_path.is_file():
                        try:
                            file_size = file_path.stat().st_size
                            result.total_space_freed += file_size
                        except Exception:
                            pass
            
            result.recommendations.append("Considere executar limpeza de arquivos desnecessários")
            
        except Exception as e:
            result.warnings.append(f"Erro detectando arquivos desnecessários: {str(e)}")
    
    def _generate_optimization_recommendations(self, result: OptimizationResult):
        """
        Gera recomendações de otimização baseadas na análise.
        
        Args:
            result: Resultado para atualizar
        """
        try:
            # Verificar espaço em disco
            try:
                free_space, total_space = get_disk_space(self.base_path)
                usage_percent = ((total_space - free_space) / total_space) * 100
                
                if usage_percent > 90:
                    result.recommendations.append("Disco quase cheio - considere mover arquivos grandes")
                elif usage_percent > 80:
                    result.recommendations.append("Uso de disco alto - monitore o crescimento")
                
            except Exception:
                pass
            
            # Recomendações baseadas nos resultados
            if result.total_space_freed > 1024 * 1024 * 100:  # > 100MB
                result.recommendations.append("Boa quantidade de espaço foi liberada")
            else:
                result.recommendations.append("Considere executar limpeza mais frequentemente")
            
            if len(result.errors) > 0:
                result.recommendations.append("Verifique os erros reportados para melhor otimização")
                
        except Exception as e:
            result.warnings.append(f"Erro gerando recomendações: {str(e)}")

# Exemplo de uso
if __name__ == "__main__":
    # Exemplo de uso do OrganizationManager
    manager = OrganizationManager()
    
    print("=== Teste do Organization Manager ===")
    
    # Teste de limpeza de temporários
    print("\n1. Limpeza de arquivos temporários:")
    temp_result = manager.cleanup_temporary_files()
    print(f"Status: {temp_result.status.value}")
    print(f"Arquivos removidos: {temp_result.files_removed}")
    print(f"Espaço liberado: {format_size(temp_result.space_freed)}")
    
    # Teste de organização de downloads
    print("\n2. Organização de downloads:")
    org_result = manager.organize_downloads()
    print(f"Status: {org_result.status.value}")
    print(f"Arquivos organizados: {org_result.files_moved}")
    print(f"Diretórios criados: {org_result.directories_created}")
    
    # Teste de rotação de logs
    print("\n3. Rotação de logs:")
    log_result = manager.rotate_logs()
    print(f"Status: {log_result.status.value}")
    print(f"Logs arquivados: {log_result.files_removed}")
    
    # Teste de otimização geral
    print("\n4. Otimização geral:")
    opt_result = manager.optimize_disk_usage()
    print(f"Status: {opt_result.status.value}")
    print(f"Espaço total liberado: {format_size(opt_result.total_space_freed)}")
    print(f"Operações realizadas: {', '.join(opt_result.operations_performed)}")
    
    if opt_result.recommendations:
        print("\nRecomendações:")
        for rec in opt_result.recommendations:
            print(f"- {rec}")