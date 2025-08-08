# -*- coding: utf-8 -*-
"""
Catalog Update Manager
Módulo responsável por atualizações automáticas do catálogo,
gerenciamento de mirrors e sistema de fallback
"""

import os
import json
import logging
import hashlib
import time
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import requests
from urllib.parse import urljoin, urlparse
import tempfile
import shutil
import zipfile
import tarfile

from .security_manager import SecurityManager, SecurityLevel
from .runtime_catalog_manager import RuntimeCatalogManager

logger = logging.getLogger(__name__)

class UpdateStatus(Enum):
    """Status da atualização"""
    IDLE = "idle"
    CHECKING = "checking"
    DOWNLOADING = "downloading"
    INSTALLING = "installing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class MirrorStatus(Enum):
    """Status do mirror"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    FAILED = "failed"
    TESTING = "testing"
    OBSOLETE = "obsolete"

class UpdateChannel(Enum):
    """Canal de atualização"""
    STABLE = "stable"
    BETA = "beta"
    ALPHA = "alpha"
    NIGHTLY = "nightly"

@dataclass
class MirrorInfo:
    """Informações do mirror"""
    url: str
    name: str
    location: str
    priority: int = 50  # 0-100, higher = more priority
    status: MirrorStatus = MirrorStatus.ACTIVE
    last_check: Optional[datetime] = None
    response_time: Optional[float] = None
    success_rate: float = 100.0
    error_count: int = 0
    last_error: Optional[str] = None
    supported_channels: List[UpdateChannel] = field(default_factory=lambda: [UpdateChannel.STABLE])
    bandwidth_limit: Optional[int] = None  # KB/s

@dataclass
class UpdateInfo:
    """Informações de atualização"""
    version: str
    release_date: datetime
    channel: UpdateChannel
    download_url: str
    checksum: str
    size: int
    changelog: str
    breaking_changes: bool = False
    required_restart: bool = False
    dependencies: List[str] = field(default_factory=list)
    mirror_urls: List[str] = field(default_factory=list)

@dataclass
class CacheEntry:
    """Entrada do cache"""
    key: str
    data: Any
    timestamp: datetime
    expiry: datetime
    size: int
    access_count: int = 0
    last_access: Optional[datetime] = None

@dataclass
class UpdateProgress:
    """Progresso da atualização"""
    status: UpdateStatus
    current_step: str
    progress_percent: float = 0.0
    downloaded_bytes: int = 0
    total_bytes: int = 0
    speed_kbps: float = 0.0
    eta_seconds: Optional[int] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class CatalogUpdateManager:
    """
    Gerenciador de atualizações do catálogo
    
    Funcionalidades:
    - Verificação automática de atualizações
    - Download em background
    - Gerenciamento de mirrors com fallback
    - Cache local para cenários offline
    - Validação de integridade
    - Sistema de rollback
    """
    
    def __init__(self, catalog_manager: Optional[RuntimeCatalogManager] = None,
                 security_manager: Optional[SecurityManager] = None):
        """Inicializar gerenciador de atualizações"""
        self.logger = logging.getLogger(__name__)
        
        # Componentes principais
        self.catalog_manager = catalog_manager or RuntimeCatalogManager()
        self.security_manager = security_manager or SecurityManager()
        
        # Configurações
        self.update_channel = UpdateChannel.STABLE
        self.auto_check_enabled = True
        self.auto_download_enabled = True
        self.auto_install_enabled = False
        self.check_interval_hours = 24
        self.download_timeout = 300  # seconds
        self.max_retries = 3
        self.cache_max_size_mb = 500
        self.cache_expiry_days = 7
        
        # Estado
        self.mirrors: List[MirrorInfo] = []
        self.current_version = "1.0.0"
        self.last_check_time: Optional[datetime] = None
        self.update_progress = UpdateProgress(status=UpdateStatus.IDLE, current_step="Idle")
        self.available_update: Optional[UpdateInfo] = None
        
        # Cache
        self.cache_directory = Path("cache/catalog_updates")
        self.cache_directory.mkdir(parents=True, exist_ok=True)
        self.cache_entries: Dict[str, CacheEntry] = {}
        
        # Thread safety
        self._lock = threading.RLock()
        self._update_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # Carregar configurações
        self._load_configuration()
        self._load_mirrors()
        self._load_cache_index()
        
        # Iniciar verificação automática
        if self.auto_check_enabled:
            self._start_auto_check()
        
        self.logger.info("Catalog update manager initialized")
    
    def check_for_updates(self, force: bool = False) -> Optional[UpdateInfo]:
        """
        Verificar atualizações disponíveis
        
        Args:
            force: Forçar verificação mesmo se recente
            
        Returns:
            Optional[UpdateInfo]: Informação da atualização se disponível
        """
        try:
            with self._lock:
                # Verificar se precisa checar
                if not force and self.last_check_time:
                    time_since_check = datetime.now() - self.last_check_time
                    if time_since_check.total_seconds() < self.check_interval_hours * 3600:
                        self.logger.debug("Skipping update check - too recent")
                        return self.available_update
                
                self.update_progress.status = UpdateStatus.CHECKING
                self.update_progress.current_step = "Checking for updates"
                
                # Tentar cada mirror até encontrar atualização
                active_mirrors = [m for m in self.mirrors if m.status == MirrorStatus.ACTIVE]
                active_mirrors.sort(key=lambda m: m.priority, reverse=True)
                
                for mirror in active_mirrors:
                    try:
                        update_info = self._check_mirror_for_updates(mirror)
                        if update_info:
                            self.available_update = update_info
                            self.last_check_time = datetime.now()
                            
                            self.logger.info(f"Update available: {update_info.version} from {mirror.name}")
                            
                            # Auditar verificação
                            self.security_manager.audit_critical_operation(
                                operation="catalog_update_check",
                                component="catalog_update_manager",
                                details={
                                    "current_version": self.current_version,
                                    "available_version": update_info.version,
                                    "channel": update_info.channel.value,
                                    "mirror": mirror.name
                                },
                                success=True,
                                security_level=SecurityLevel.MEDIUM
                            )
                            
                            self.update_progress.status = UpdateStatus.IDLE
                            return update_info
                            
                    except Exception as e:
                        self.logger.warning(f"Failed to check mirror {mirror.name}: {e}")
                        self._mark_mirror_error(mirror, str(e))
                        continue
                
                # Nenhuma atualização encontrada
                self.last_check_time = datetime.now()
                self.update_progress.status = UpdateStatus.IDLE
                self.logger.info("No updates available")
                return None
                
        except Exception as e:
            self.logger.error(f"Error checking for updates: {e}")
            self.update_progress.status = UpdateStatus.FAILED
            self.update_progress.error_message = str(e)
            return None
    
    def download_update(self, update_info: Optional[UpdateInfo] = None, background: bool = True) -> bool:
        """
        Baixar atualização
        
        Args:
            update_info: Informação da atualização (usa available_update se None)
            background: Executar em background
            
        Returns:
            bool: True se iniciado com sucesso
        """
        try:
            update_info = update_info or self.available_update
            if not update_info:
                self.logger.warning("No update available to download")
                return False
            
            if background:
                if self._update_thread and self._update_thread.is_alive():
                    self.logger.warning("Update already in progress")
                    return False
                
                self._update_thread = threading.Thread(
                    target=self._download_update_worker,
                    args=(update_info,),
                    name="CatalogUpdateDownload"
                )
                self._update_thread.start()
                return True
            else:
                return self._download_update_worker(update_info)
                
        except Exception as e:
            self.logger.error(f"Error starting update download: {e}")
            return False
    
    def install_update(self, update_file: Optional[Path] = None) -> bool:
        """
        Instalar atualização
        
        Args:
            update_file: Arquivo da atualização (detecta automaticamente se None)
            
        Returns:
            bool: True se instalado com sucesso
        """
        try:
            with self._lock:
                self.update_progress.status = UpdateStatus.INSTALLING
                self.update_progress.current_step = "Installing update"
                
                # Encontrar arquivo de atualização
                if not update_file:
                    update_file = self._find_downloaded_update()
                
                if not update_file or not update_file.exists():
                    self.logger.error("Update file not found")
                    self.update_progress.status = UpdateStatus.FAILED
                    self.update_progress.error_message = "Update file not found"
                    return False
                
                # Validar integridade
                if not self._validate_update_file(update_file):
                    self.logger.error("Update file validation failed")
                    self.update_progress.status = UpdateStatus.FAILED
                    self.update_progress.error_message = "Update file validation failed"
                    return False
                
                # Criar backup do catálogo atual
                backup_path = self._create_catalog_backup()
                if not backup_path:
                    self.logger.error("Failed to create catalog backup")
                    self.update_progress.status = UpdateStatus.FAILED
                    self.update_progress.error_message = "Failed to create backup"
                    return False
                
                # Extrair e instalar atualização
                success = self._extract_and_install_update(update_file)
                
                if success:
                    self.update_progress.status = UpdateStatus.COMPLETED
                    self.update_progress.completed_at = datetime.now()
                    self.available_update = None
                    
                    self.logger.info("Catalog update installed successfully")
                    
                    # Auditar instalação
                    self.security_manager.audit_critical_operation(
                        operation="catalog_update_install",
                        component="catalog_update_manager",
                        details={
                            "update_file": str(update_file),
                            "backup_path": str(backup_path)
                        },
                        success=True,
                        security_level=SecurityLevel.HIGH
                    )
                    
                    return True
                else:
                    # Restaurar backup em caso de falha
                    self._restore_catalog_backup(backup_path)
                    self.update_progress.status = UpdateStatus.FAILED
                    self.update_progress.error_message = "Installation failed, backup restored"
                    return False
                    
        except Exception as e:
            self.logger.error(f"Error installing update: {e}")
            self.update_progress.status = UpdateStatus.FAILED
            self.update_progress.error_message = str(e)
            return False
    
    def add_mirror(self, mirror_info: MirrorInfo) -> bool:
        """
        Adicionar novo mirror
        
        Args:
            mirror_info: Informações do mirror
            
        Returns:
            bool: True se adicionado com sucesso
        """
        try:
            # Validar URL do mirror
            validation_result = self.security_manager.validate_input(mirror_info.url, "url")
            if validation_result.validation_result.value != "safe":
                self.logger.warning(f"Unsafe mirror URL: {mirror_info.url}")
                return False
            
            # Testar conectividade
            if not self._test_mirror_connectivity(mirror_info):
                self.logger.warning(f"Mirror connectivity test failed: {mirror_info.url}")
                mirror_info.status = MirrorStatus.FAILED
            
            with self._lock:
                self.mirrors.append(mirror_info)
                self._save_mirrors()
            
            self.logger.info(f"Added mirror: {mirror_info.name} ({mirror_info.url})")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding mirror: {e}")
            return False
    
    def remove_mirror(self, mirror_url: str) -> bool:
        """
        Remover mirror
        
        Args:
            mirror_url: URL do mirror
            
        Returns:
            bool: True se removido com sucesso
        """
        try:
            with self._lock:
                self.mirrors = [m for m in self.mirrors if m.url != mirror_url]
                self._save_mirrors()
            
            self.logger.info(f"Removed mirror: {mirror_url}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error removing mirror: {e}")
            return False
    
    def test_all_mirrors(self) -> Dict[str, bool]:
        """
        Testar conectividade de todos os mirrors
        
        Returns:
            Dict[str, bool]: Resultado dos testes por URL
        """
        results = {}
        
        for mirror in self.mirrors:
            try:
                mirror.status = MirrorStatus.TESTING
                success = self._test_mirror_connectivity(mirror)
                
                if success:
                    mirror.status = MirrorStatus.ACTIVE
                    mirror.error_count = 0
                    mirror.last_error = None
                else:
                    mirror.status = MirrorStatus.FAILED
                    mirror.error_count += 1
                
                mirror.last_check = datetime.now()
                results[mirror.url] = success
                
            except Exception as e:
                self.logger.error(f"Error testing mirror {mirror.url}: {e}")
                mirror.status = MirrorStatus.FAILED
                mirror.error_count += 1
                mirror.last_error = str(e)
                results[mirror.url] = False
        
        self._save_mirrors()
        return results
    
    def get_cache_info(self) -> Dict[str, Any]:
        """
        Obter informações do cache
        
        Returns:
            Dict[str, Any]: Informações do cache
        """
        total_size = sum(entry.size for entry in self.cache_entries.values())
        total_entries = len(self.cache_entries)
        expired_entries = sum(1 for entry in self.cache_entries.values() 
                            if entry.expiry < datetime.now())
        
        return {
            "total_entries": total_entries,
            "total_size_mb": total_size / (1024 * 1024),
            "max_size_mb": self.cache_max_size_mb,
            "expired_entries": expired_entries,
            "cache_directory": str(self.cache_directory),
            "entries": {
                key: {
                    "size": entry.size,
                    "timestamp": entry.timestamp.isoformat(),
                    "expiry": entry.expiry.isoformat(),
                    "access_count": entry.access_count,
                    "last_access": entry.last_access.isoformat() if entry.last_access else None
                }
                for key, entry in self.cache_entries.items()
            }
        }
    
    def cleanup_cache(self, force: bool = False) -> int:
        """
        Limpar cache expirado
        
        Args:
            force: Forçar limpeza de todas as entradas
            
        Returns:
            int: Número de entradas removidas
        """
        removed_count = 0
        current_time = datetime.now()
        
        try:
            with self._lock:
                keys_to_remove = []
                
                for key, entry in self.cache_entries.items():
                    should_remove = force or entry.expiry < current_time
                    
                    if should_remove:
                        # Remover arquivo do cache
                        cache_file = self.cache_directory / f"{key}.cache"
                        if cache_file.exists():
                            cache_file.unlink()
                        
                        keys_to_remove.append(key)
                        removed_count += 1
                
                # Remover entradas do índice
                for key in keys_to_remove:
                    del self.cache_entries[key]
                
                # Salvar índice atualizado
                self._save_cache_index()
            
            self.logger.info(f"Cleaned up {removed_count} cache entries")
            return removed_count
            
        except Exception as e:
            self.logger.error(f"Error cleaning up cache: {e}")
            return 0
    
    def get_update_status(self) -> Dict[str, Any]:
        """
        Obter status das atualizações
        
        Returns:
            Dict[str, Any]: Status das atualizações
        """
        return {
            "current_version": self.current_version,
            "update_channel": self.update_channel.value,
            "auto_check_enabled": self.auto_check_enabled,
            "auto_download_enabled": self.auto_download_enabled,
            "auto_install_enabled": self.auto_install_enabled,
            "last_check_time": self.last_check_time.isoformat() if self.last_check_time else None,
            "available_update": {
                "version": self.available_update.version,
                "channel": self.available_update.channel.value,
                "release_date": self.available_update.release_date.isoformat(),
                "size": self.available_update.size,
                "breaking_changes": self.available_update.breaking_changes,
                "required_restart": self.available_update.required_restart
            } if self.available_update else None,
            "progress": {
                "status": self.update_progress.status.value,
                "current_step": self.update_progress.current_step,
                "progress_percent": self.update_progress.progress_percent,
                "downloaded_bytes": self.update_progress.downloaded_bytes,
                "total_bytes": self.update_progress.total_bytes,
                "speed_kbps": self.update_progress.speed_kbps,
                "eta_seconds": self.update_progress.eta_seconds,
                "error_message": self.update_progress.error_message,
                "started_at": self.update_progress.started_at.isoformat() if self.update_progress.started_at else None,
                "completed_at": self.update_progress.completed_at.isoformat() if self.update_progress.completed_at else None
            },
            "mirrors": [
                {
                    "name": mirror.name,
                    "url": mirror.url,
                    "location": mirror.location,
                    "status": mirror.status.value,
                    "priority": mirror.priority,
                    "response_time": mirror.response_time,
                    "success_rate": mirror.success_rate,
                    "error_count": mirror.error_count,
                    "last_check": mirror.last_check.isoformat() if mirror.last_check else None
                }
                for mirror in self.mirrors
            ]
        }
    
    def stop_update(self) -> bool:
        """
        Parar atualização em andamento
        
        Returns:
            bool: True se parado com sucesso
        """
        try:
            self._stop_event.set()
            
            if self._update_thread and self._update_thread.is_alive():
                self._update_thread.join(timeout=10)
            
            self.update_progress.status = UpdateStatus.CANCELLED
            self.update_progress.current_step = "Cancelled"
            
            self.logger.info("Update cancelled")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping update: {e}")
            return False
    
    def _check_mirror_for_updates(self, mirror: MirrorInfo) -> Optional[UpdateInfo]:
        """
        Verificar atualizações em mirror específico
        
        Args:
            mirror: Informações do mirror
            
        Returns:
            Optional[UpdateInfo]: Informação da atualização se disponível
        """
        try:
            # Construir URL de verificação
            check_url = urljoin(mirror.url, f"updates/{self.update_channel.value}/latest.json")
            
            # Fazer requisição
            start_time = time.time()
            response = requests.get(check_url, timeout=30)
            response_time = time.time() - start_time
            
            response.raise_for_status()
            
            # Atualizar estatísticas do mirror
            mirror.response_time = response_time
            mirror.last_check = datetime.now()
            
            # Parsear resposta
            update_data = response.json()
            
            # Verificar se há atualização disponível
            available_version = update_data.get("version")
            if not available_version or available_version <= self.current_version:
                return None
            
            # Criar informação da atualização
            update_info = UpdateInfo(
                version=available_version,
                release_date=datetime.fromisoformat(update_data["release_date"]),
                channel=UpdateChannel(update_data["channel"]),
                download_url=update_data["download_url"],
                checksum=update_data["checksum"],
                size=update_data["size"],
                changelog=update_data.get("changelog", ""),
                breaking_changes=update_data.get("breaking_changes", False),
                required_restart=update_data.get("required_restart", False),
                dependencies=update_data.get("dependencies", []),
                mirror_urls=update_data.get("mirror_urls", [])
            )
            
            return update_info
            
        except Exception as e:
            self.logger.error(f"Error checking mirror {mirror.url}: {e}")
            raise
    
    def _download_update_worker(self, update_info: UpdateInfo) -> bool:
        """
        Worker para download da atualização
        
        Args:
            update_info: Informação da atualização
            
        Returns:
            bool: True se baixado com sucesso
        """
        try:
            self.update_progress.status = UpdateStatus.DOWNLOADING
            self.update_progress.current_step = "Downloading update"
            self.update_progress.started_at = datetime.now()
            self.update_progress.total_bytes = update_info.size
            
            # Tentar download de cada URL
            download_urls = [update_info.download_url] + update_info.mirror_urls
            
            for url in download_urls:
                if self._stop_event.is_set():
                    return False
                
                try:
                    success = self._download_file(url, update_info)
                    if success:
                        self.update_progress.status = UpdateStatus.COMPLETED
                        self.update_progress.completed_at = datetime.now()
                        return True
                except Exception as e:
                    self.logger.warning(f"Failed to download from {url}: {e}")
                    continue
            
            # Todos os downloads falharam
            self.update_progress.status = UpdateStatus.FAILED
            self.update_progress.error_message = "All download URLs failed"
            return False
            
        except Exception as e:
            self.logger.error(f"Error in download worker: {e}")
            self.update_progress.status = UpdateStatus.FAILED
            self.update_progress.error_message = str(e)
            return False
    
    def _download_file(self, url: str, update_info: UpdateInfo) -> bool:
        """
        Baixar arquivo de atualização
        
        Args:
            url: URL do arquivo
            update_info: Informação da atualização
            
        Returns:
            bool: True se baixado com sucesso
        """
        try:
            # Criar arquivo temporário
            download_path = self.cache_directory / f"update_{update_info.version}.tmp"
            
            # Download com progresso
            response = requests.get(url, stream=True, timeout=self.download_timeout)
            response.raise_for_status()
            
            downloaded_bytes = 0
            start_time = time.time()
            
            with open(download_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if self._stop_event.is_set():
                        return False
                    
                    if chunk:
                        f.write(chunk)
                        downloaded_bytes += len(chunk)
                        
                        # Atualizar progresso
                        elapsed_time = time.time() - start_time
                        if elapsed_time > 0:
                            speed_kbps = (downloaded_bytes / 1024) / elapsed_time
                            self.update_progress.speed_kbps = speed_kbps
                            
                            if speed_kbps > 0:
                                remaining_bytes = update_info.size - downloaded_bytes
                                eta_seconds = (remaining_bytes / 1024) / speed_kbps
                                self.update_progress.eta_seconds = int(eta_seconds)
                        
                        self.update_progress.downloaded_bytes = downloaded_bytes
                        self.update_progress.progress_percent = (downloaded_bytes / update_info.size) * 100
            
            # Verificar checksum
            if not self._verify_checksum(download_path, update_info.checksum):
                download_path.unlink()
                raise ValueError("Checksum verification failed")
            
            # Mover para local final
            final_path = self.cache_directory / f"update_{update_info.version}.zip"
            download_path.rename(final_path)
            
            self.logger.info(f"Successfully downloaded update to {final_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error downloading file: {e}")
            if download_path.exists():
                download_path.unlink()
            raise
    
    def _verify_checksum(self, file_path: Path, expected_checksum: str) -> bool:
        """
        Verificar checksum do arquivo
        
        Args:
            file_path: Caminho do arquivo
            expected_checksum: Checksum esperado
            
        Returns:
            bool: True se checksum é válido
        """
        try:
            hasher = hashlib.sha256()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hasher.update(chunk)
            
            actual_checksum = hasher.hexdigest()
            return actual_checksum.lower() == expected_checksum.lower()
            
        except Exception as e:
            self.logger.error(f"Error verifying checksum: {e}")
            return False
    
    def _test_mirror_connectivity(self, mirror: MirrorInfo) -> bool:
        """
        Testar conectividade do mirror
        
        Args:
            mirror: Informações do mirror
            
        Returns:
            bool: True se conectividade OK
        """
        try:
            test_url = urljoin(mirror.url, "health")
            response = requests.head(test_url, timeout=10)
            return response.status_code < 400
        except:
            return False
    
    def _mark_mirror_error(self, mirror: MirrorInfo, error: str):
        """
        Marcar erro no mirror
        
        Args:
            mirror: Informações do mirror
            error: Mensagem de erro
        """
        mirror.error_count += 1
        mirror.last_error = error
        mirror.last_check = datetime.now()
        
        # Calcular taxa de sucesso
        if mirror.error_count > 0:
            mirror.success_rate = max(0, 100 - (mirror.error_count * 10))
        
        # Marcar como falho se muitos erros
        if mirror.error_count >= 5:
            mirror.status = MirrorStatus.FAILED
    
    def _find_downloaded_update(self) -> Optional[Path]:
        """
        Encontrar arquivo de atualização baixado
        
        Returns:
            Optional[Path]: Caminho do arquivo se encontrado
        """
        try:
            for file_path in self.cache_directory.glob("update_*.zip"):
                return file_path
            return None
        except:
            return None
    
    def _validate_update_file(self, file_path: Path) -> bool:
        """
        Validar arquivo de atualização
        
        Args:
            file_path: Caminho do arquivo
            
        Returns:
            bool: True se válido
        """
        try:
            # Verificar se é arquivo ZIP válido
            with zipfile.ZipFile(file_path, 'r') as zip_file:
                # Verificar estrutura básica
                required_files = ['catalog.json', 'version.txt']
                zip_contents = zip_file.namelist()
                
                for required_file in required_files:
                    if required_file not in zip_contents:
                        self.logger.error(f"Missing required file in update: {required_file}")
                        return False
                
                # Testar extração
                zip_file.testzip()
                
            return True
            
        except Exception as e:
            self.logger.error(f"Update file validation failed: {e}")
            return False
    
    def _create_catalog_backup(self) -> Optional[Path]:
        """
        Criar backup do catálogo atual
        
        Returns:
            Optional[Path]: Caminho do backup se criado
        """
        try:
            backup_dir = Path("backups/catalog")
            backup_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = backup_dir / f"catalog_backup_{timestamp}.zip"
            
            # Criar backup ZIP
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # Adicionar arquivos do catálogo
                catalog_dir = Path("config/components")
                if catalog_dir.exists():
                    for file_path in catalog_dir.rglob("*.yaml"):
                        zip_file.write(file_path, file_path.relative_to(catalog_dir.parent))
            
            self.logger.info(f"Created catalog backup: {backup_path}")
            return backup_path
            
        except Exception as e:
            self.logger.error(f"Error creating catalog backup: {e}")
            return None
    
    def _restore_catalog_backup(self, backup_path: Path) -> bool:
        """
        Restaurar backup do catálogo
        
        Args:
            backup_path: Caminho do backup
            
        Returns:
            bool: True se restaurado com sucesso
        """
        try:
            with zipfile.ZipFile(backup_path, 'r') as zip_file:
                zip_file.extractall("config")
            
            self.logger.info(f"Restored catalog from backup: {backup_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error restoring catalog backup: {e}")
            return False
    
    def _extract_and_install_update(self, update_file: Path) -> bool:
        """
        Extrair e instalar atualização
        
        Args:
            update_file: Arquivo da atualização
            
        Returns:
            bool: True se instalado com sucesso
        """
        try:
            # Extrair para diretório temporário
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                with zipfile.ZipFile(update_file, 'r') as zip_file:
                    zip_file.extractall(temp_path)
                
                # Verificar versão
                version_file = temp_path / "version.txt"
                if version_file.exists():
                    new_version = version_file.read_text().strip()
                    self.current_version = new_version
                
                # Copiar arquivos do catálogo
                catalog_file = temp_path / "catalog.json"
                if catalog_file.exists():
                    # Atualizar catálogo
                    self.catalog_manager.load_catalog_from_file(catalog_file)
                
                # Copiar outros arquivos de configuração
                config_dir = temp_path / "config"
                if config_dir.exists():
                    target_config_dir = Path("config")
                    shutil.copytree(config_dir, target_config_dir, dirs_exist_ok=True)
            
            self.logger.info("Update installation completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Error installing update: {e}")
            return False
    
    def _start_auto_check(self):
        """
        Iniciar verificação automática de atualizações
        """
        def auto_check_worker():
            while not self._stop_event.is_set():
                try:
                    # Verificar atualizações
                    update_info = self.check_for_updates()
                    
                    # Auto-download se habilitado
                    if update_info and self.auto_download_enabled:
                        self.download_update(update_info, background=True)
                    
                    # Aguardar próxima verificação
                    self._stop_event.wait(self.check_interval_hours * 3600)
                    
                except Exception as e:
                    self.logger.error(f"Error in auto-check worker: {e}")
                    self._stop_event.wait(3600)  # Aguardar 1 hora em caso de erro
        
        auto_check_thread = threading.Thread(
            target=auto_check_worker,
            name="CatalogAutoCheck",
            daemon=True
        )
        auto_check_thread.start()
    
    def _load_configuration(self):
        """
        Carregar configurações
        """
        try:
            config_path = Path("config/catalog_update.json")
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                self.update_channel = UpdateChannel(config.get("update_channel", "stable"))
                self.auto_check_enabled = config.get("auto_check_enabled", True)
                self.auto_download_enabled = config.get("auto_download_enabled", True)
                self.auto_install_enabled = config.get("auto_install_enabled", False)
                self.check_interval_hours = config.get("check_interval_hours", 24)
                self.current_version = config.get("current_version", "1.0.0")
                
                self.logger.info("Loaded catalog update configuration")
        except Exception as e:
            self.logger.warning(f"Could not load catalog update config: {e}")
    
    def _load_mirrors(self):
        """
        Carregar lista de mirrors
        """
        try:
            mirrors_path = Path("config/mirrors.json")
            if mirrors_path.exists():
                with open(mirrors_path, 'r') as f:
                    mirrors_data = json.load(f)
                
                self.mirrors = [
                    MirrorInfo(
                        url=mirror["url"],
                        name=mirror["name"],
                        location=mirror["location"],
                        priority=mirror.get("priority", 50),
                        status=MirrorStatus(mirror.get("status", "active")),
                        supported_channels=[UpdateChannel(ch) for ch in mirror.get("supported_channels", ["stable"])]
                    )
                    for mirror in mirrors_data.get("mirrors", [])
                ]
                
                self.logger.info(f"Loaded {len(self.mirrors)} mirrors")
            else:
                # Mirrors padrão
                self.mirrors = [
                    MirrorInfo(
                        url="https://updates.environmentdev.com/",
                        name="Primary",
                        location="Global",
                        priority=100
                    )
                ]
        except Exception as e:
            self.logger.warning(f"Could not load mirrors config: {e}")
    
    def _save_mirrors(self):
        """
        Salvar lista de mirrors
        """
        try:
            mirrors_data = {
                "mirrors": [
                    {
                        "url": mirror.url,
                        "name": mirror.name,
                        "location": mirror.location,
                        "priority": mirror.priority,
                        "status": mirror.status.value,
                        "supported_channels": [ch.value for ch in mirror.supported_channels]
                    }
                    for mirror in self.mirrors
                ]
            }
            
            mirrors_path = Path("config/mirrors.json")
            mirrors_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(mirrors_path, 'w') as f:
                json.dump(mirrors_data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving mirrors config: {e}")
    
    def _load_cache_index(self):
        """
        Carregar índice do cache
        """
        try:
            cache_index_path = self.cache_directory / "index.json"
            if cache_index_path.exists():
                with open(cache_index_path, 'r') as f:
                    cache_data = json.load(f)
                
                for key, entry_data in cache_data.items():
                    self.cache_entries[key] = CacheEntry(
                        key=key,
                        data=entry_data["data"],
                        timestamp=datetime.fromisoformat(entry_data["timestamp"]),
                        expiry=datetime.fromisoformat(entry_data["expiry"]),
                        size=entry_data["size"],
                        access_count=entry_data.get("access_count", 0),
                        last_access=datetime.fromisoformat(entry_data["last_access"]) if entry_data.get("last_access") else None
                    )
                
                self.logger.info(f"Loaded {len(self.cache_entries)} cache entries")
        except Exception as e:
            self.logger.warning(f"Could not load cache index: {e}")
    
    def _save_cache_index(self):
        """
        Salvar índice do cache
        """
        try:
            cache_data = {
                key: {
                    "data": entry.data,
                    "timestamp": entry.timestamp.isoformat(),
                    "expiry": entry.expiry.isoformat(),
                    "size": entry.size,
                    "access_count": entry.access_count,
                    "last_access": entry.last_access.isoformat() if entry.last_access else None
                }
                for key, entry in self.cache_entries.items()
            }
            
            cache_index_path = self.cache_directory / "index.json"
            with open(cache_index_path, 'w') as f:
                json.dump(cache_data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving cache index: {e}")


# Instância global do gerenciador de atualizações
catalog_update_manager = CatalogUpdateManager()


if __name__ == "__main__":
    # Teste do sistema de atualizações
    import asyncio
    
    # Testar gerenciador de atualizações
    update_manager = CatalogUpdateManager()
    
    # Verificar atualizações
    print("Checking for updates...")
    update_info = update_manager.check_for_updates(force=True)
    if update_info:
        print(f"Update available: {update_info.version}")
    else:
        print("No updates available")
    
    # Testar mirrors
    print("\nTesting mirrors...")
    mirror_results = update_manager.test_all_mirrors()
    for url, success in mirror_results.items():
        print(f"Mirror {url}: {'OK' if success else 'FAILED'}")
    
    # Obter status
    print("\nUpdate status:")
    status = update_manager.get_update_status()
    print(json.dumps(status, indent=2, default=str))
    
    # Informações do cache
    print("\nCache info:")
    cache_info = update_manager.get_cache_info()
    print(json.dumps(cache_info, indent=2, default=str))