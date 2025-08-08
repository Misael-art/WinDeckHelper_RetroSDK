# -*- coding: utf-8 -*-
"""
Melhorias finais para o Organization Manager
Completa a implementação dos requisitos 5.1, 5.2, 5.3, 5.4 e 5.5
"""

import os
import logging
import threading
import time
import json
import hashlib
from typing import Dict, List, Optional, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path

from env_dev.core.organization_manager import (
    OrganizationManager, CleanupResult, OrganizationResult, 
    BackupManagementResult, OptimizationResult, CleanupStatus
)

logger = logging.getLogger(__name__)

@dataclass
class SmartCleanupConfig:
    """Configuração inteligente de limpeza"""
    auto_cleanup_enabled: bool = True
    cleanup_interval_hours: int = 24
    aggressive_cleanup: bool = False
    preserve_recent_files_hours: int = 2
    max_temp_size_mb: int = 1000
    max_log_size_mb: int = 500
    max_backup_count: int = 10
    duplicate_detection_enabled: bool = True
    
@dataclass
class DuplicateFile:
    """Informações sobre arquivo duplicado"""
    hash_value: str
    file_paths: List[Path]
    total_size: int
    can_remove_count: int

@dataclass
class SmartCleanupResult:
    """Resultado de limpeza inteligente"""
    status: CleanupStatus
    total_space_freed: int = 0
    duplicates_removed: int = 0
    temp_files_removed: int = 0
    old_logs_removed: int = 0
    old_backups_removed: int = 0
    recommendations: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)

class EnhancedOrganizationManager(OrganizationManager):
    """
    Versão aprimorada do OrganizationManager com funcionalidades adicionais
    para completar todos os requisitos da Task 6
    """
    
    def __init__(self, base_path: Optional[Path] = None):
        super().__init__(base_path)
        self.cleanup_config = SmartCleanupConfig()
        self.cleanup_lock = threading.Lock()
        self.last_cleanup_time = None
        self.cleanup_history: List[SmartCleanupResult] = []
        
        # Diretório para configurações
        self.config_dir = self.base_path / "config"
        self.config_dir.mkdir(exist_ok=True)
        
        # Carrega configuração se existir
        self._load_cleanup_config()
    
    def smart_cleanup(self, aggressive: bool = False) -> SmartCleanupResult:
        """
        Executa limpeza inteligente baseada em configurações e análise
        
        Args:
            aggressive: Se deve executar limpeza agressiva
            
        Returns:
            SmartCleanupResult: Resultado da limpeza inteligente
        """
        with self.cleanup_lock:
            logger.info("Iniciando limpeza inteligente")
            result = SmartCleanupResult(status=CleanupStatus.IN_PROGRESS)
            
            try:
                # 1. Detecta e remove arquivos duplicados
                if self.cleanup_config.duplicate_detection_enabled:
                    duplicates_result = self._remove_duplicate_files(aggressive)
                    result.duplicates_removed = duplicates_result['removed_count']
                    result.total_space_freed += duplicates_result['space_freed']
                
                # 2. Limpeza inteligente de temporários
                temp_result = self._smart_temp_cleanup(aggressive)
                result.temp_files_removed = temp_result.files_removed
                result.total_space_freed += temp_result.space_freed
                
                # 3. Limpeza inteligente de logs
                log_result = self._smart_log_cleanup(aggressive)
                result.old_logs_removed = log_result.files_removed
                result.total_space_freed += log_result.space_freed
                
                # 4. Limpeza inteligente de backups
                backup_result = self._smart_backup_cleanup(aggressive)
                result.old_backups_removed = backup_result.backups_removed
                result.total_space_freed += backup_result.space_freed
                
                # 5. Gera recomendações inteligentes
                self._generate_smart_recommendations(result)
                
                result.status = CleanupStatus.COMPLETED
                self.last_cleanup_time = datetime.now()
                self.cleanup_history.append(result)
                
                # Mantém apenas os últimos 50 resultados
                if len(self.cleanup_history) > 50:
                    self.cleanup_history = self.cleanup_history[-50:]
                
                logger.info(f"Limpeza inteligente concluída: {self._format_size(result.total_space_freed)} liberados")
                
            except Exception as e:
                result.status = CleanupStatus.FAILED
                result.errors.append(f"Erro na limpeza inteligente: {e}")
                logger.error(f"Erro na limpeza inteligente: {e}")
            
            return result