"""Sistema de Verificação Inteligente de Atualizações.

Este módulo implementa um sistema inteligente para verificação e gerenciamento
de atualizações de aplicações, com foco em segurança e priorização.

Author: AI Assistant
Date: 2024
"""

import logging
import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from .version_manager import VersionManager, get_version_manager
# from security_update_checker import SecurityUpdateChecker


class UpdatePriority(Enum):
    """Prioridade de atualização."""
    CRITICAL = "critical"  # Vulnerabilidades críticas
    HIGH = "high"        # Atualizações de segurança importantes
    MEDIUM = "medium"    # Atualizações funcionais
    LOW = "low"          # Atualizações menores
    OPTIONAL = "optional" # Atualizações opcionais


class UpdateStrategy(Enum):
    """Estratégia de atualização."""
    IMMEDIATE = "immediate"    # Atualizar imediatamente
    SCHEDULED = "scheduled"    # Agendar atualização
    MANUAL = "manual"          # Aguardar ação manual
    DEFERRED = "deferred"      # Adiar atualização
    BLOCKED = "blocked"        # Bloqueada por dependências


class UpdateReason(Enum):
    """Razão para atualização."""
    SECURITY_VULNERABILITY = "security_vulnerability"
    BUG_FIX = "bug_fix"
    FEATURE_UPDATE = "feature_update"
    COMPATIBILITY = "compatibility"
    PERFORMANCE = "performance"
    DEPENDENCY = "dependency"
    EOL_VERSION = "eol_version"  # End of Life


@dataclass
class UpdateInfo:
    """Informações sobre uma atualização disponível."""
    application_name: str
    current_version: str
    available_version: str
    priority: UpdatePriority
    strategy: UpdateStrategy
    reasons: List[UpdateReason]
    description: str = ""
    release_date: Optional[datetime] = None
    security_score: float = 0.0  # 0.0 a 10.0
    download_url: str = ""
    changelog_url: str = ""
    dependencies: List[str] = field(default_factory=list)
    conflicts: List[str] = field(default_factory=list)
    estimated_download_size: int = 0  # bytes
    requires_restart: bool = False
    backup_recommended: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UpdateRecommendation:
    """Recomendação de atualização."""
    updates: List[UpdateInfo]
    total_updates: int
    critical_updates: int
    security_updates: int
    recommended_action: str
    estimated_time: timedelta
    risk_assessment: str
    batch_groups: List[List[str]] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class IntelligentUpdateChecker:
    """Verificador inteligente de atualizações."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Inicializa o verificador de atualizações."""
        self.logger = logging.getLogger(__name__)
        self.version_manager = get_version_manager()
        # self.security_checker = SecurityUpdateChecker()
        
        # Configurações padrão
        self.config = {
            "check_interval_hours": 24,
            "security_check_interval_hours": 6,
            "max_concurrent_checks": 5,
            "timeout_seconds": 30,
            "enable_auto_security_updates": False,
            "enable_notifications": True,
            "notification_threshold": UpdatePriority.MEDIUM,
            "batch_size": 10,
            "retry_attempts": 3,
            "cache_duration_hours": 4
        }
        
        if config:
            self.config.update(config)
        
        # Cache de verificações
        self._update_cache: Dict[str, UpdateInfo] = {}
        self._last_check: Dict[str, datetime] = {}
        self._notification_history: List[Dict[str, Any]] = []
        
        # Fontes de atualização conhecidas
        self.update_sources = {
            "git": {
                "check_url": "https://api.github.com/repos/git/git/releases/latest",
                "pattern": r"v?(\d+\.\d+\.\d+)",
                "security_feed": "https://github.com/git/git/security/advisories"
            },
            "nodejs": {
                "check_url": "https://nodejs.org/dist/index.json",
                "pattern": r"v?(\d+\.\d+\.\d+)",
                "security_feed": "https://nodejs.org/en/security/"
            },
            "python": {
                "check_url": "https://api.github.com/repos/python/cpython/releases/latest",
                "pattern": r"v?(\d+\.\d+\.\d+)",
                "security_feed": "https://python.org/news/security/"
            },
            "java": {
                "check_url": "https://api.adoptium.net/v3/info/release_versions",
                "pattern": r"(\d+\.\d+\.\d+)",
                "security_feed": "https://www.oracle.com/security-alerts/"
            },
            "dotnet": {
                "check_url": "https://api.nuget.org/v3-flatcontainer/microsoft.netcore.app/index.json",
                "pattern": r"(\d+\.\d+\.\d+)",
                "security_feed": "https://github.com/dotnet/announcements/issues"
            },
            "visual_studio_code": {
                "check_url": "https://api.github.com/repos/microsoft/vscode/releases/latest",
                "pattern": r"(\d+\.\d+\.\d+)",
                "security_feed": "https://code.visualstudio.com/updates"
            }
        }
        
        self.logger.info("IntelligentUpdateChecker inicializado")
    
    async def check_updates_for_applications(self, applications) -> UpdateRecommendation:
        """Verifica atualizações para uma lista de aplicações."""
        # Importação dinâmica para evitar circular import
        from .detection_engine import DetectedApplication
        
        self.logger.info(f"Verificando atualizações para {len(applications)} aplicações")
        
        updates = []
        semaphore = asyncio.Semaphore(self.config["max_concurrent_checks"])
        
        # Verificar atualizações em paralelo
        tasks = []
        for app in applications:
            task = self._check_single_application_update(app, semaphore)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Processar resultados
        for result in results:
            if isinstance(result, UpdateInfo):
                updates.append(result)
            elif isinstance(result, Exception):
                self.logger.error(f"Erro na verificação de atualização: {result}")
        
        # Gerar recomendação
        recommendation = self._generate_update_recommendation(updates)
        
        self.logger.info(f"Encontradas {len(updates)} atualizações disponíveis")
        return recommendation
    
    async def _check_single_application_update(self, app, semaphore: asyncio.Semaphore):
        """Verifica atualização para uma única aplicação."""
        # Importação dinâmica para evitar circular import
        from .detection_engine import DetectedApplication
        
        async with semaphore:
            try:
                # Verificar cache
                cache_key = f"{app.name}_{app.version}"
                if self._is_cache_valid(cache_key):
                    return self._update_cache.get(cache_key)
                
                # Verificar se temos fonte de atualização para esta aplicação
                app_key = self._normalize_app_name(app.name)
                if app_key not in self.update_sources:
                    return None
                
                # Obter informações de atualização
                latest_version = await self._get_latest_version(app_key)
                if not latest_version:
                    return None
                
                # Comparar versões
                if not self.version_manager.is_newer_version(latest_version, app.version):
                    return None
                
                # Verificar informações de segurança
                security_info = await self.security_checker.check_security_updates(app.name, app.version, latest_version)
                
                # Criar informações de atualização
                update_info = self._create_update_info(
                    app, latest_version, security_info
                )
                
                # Armazenar no cache
                self._update_cache[cache_key] = update_info
                self._last_check[cache_key] = datetime.now()
                
                return update_info
                
            except Exception as e:
                self.logger.error(f"Erro ao verificar atualização para {app.name}: {e}")
                return None
    
    def _normalize_app_name(self, app_name: str) -> str:
        """Normaliza nome da aplicação para busca."""
        name_lower = app_name.lower()
        
        # Mapeamentos conhecidos
        mappings = {
            "visual studio code": "visual_studio_code",
            "vscode": "visual_studio_code",
            "code": "visual_studio_code",
            "node.js": "nodejs",
            "node": "nodejs",
            "npm": "nodejs",
            "java jdk": "java",
            "openjdk": "java",
            "oracle jdk": "java",
            ".net": "dotnet",
            ".net core": "dotnet",
            ".net framework": "dotnet",
            "python": "python",
            "git": "git"
        }
        
        for pattern, key in mappings.items():
            if pattern in name_lower:
                return key
        
        return name_lower.replace(" ", "_")
    
    async def _get_latest_version(self, app_key: str) -> Optional[str]:
        """Obtém a versão mais recente de uma aplicação."""
        try:
            source = self.update_sources.get(app_key)
            if not source:
                return None
            
            # Simular verificação de versão (implementação real dependeria de HTTP requests)
            # Por enquanto, retornar versões fictícias para demonstração
            mock_versions = {
                "git": "2.43.0",
                "nodejs": "20.10.0",
                "python": "3.12.1",
                "java": "21.0.1",
                "dotnet": "8.0.0",
                "visual_studio_code": "1.85.0"
            }
            
            return mock_versions.get(app_key)
            
        except Exception as e:
            self.logger.error(f"Erro ao obter versão mais recente para {app_key}: {e}")
            return None
    
    def _create_update_info(self, app, latest_version: str, security_info: Dict[str, Any]) -> UpdateInfo:
        """Cria informações de atualização."""
        # Importação dinâmica para evitar circular import
        from .detection_engine import DetectedApplication
        
        # Determinar prioridade baseada em segurança e idade da versão
        priority = self._determine_update_priority(app, latest_version, security_info)
        
        # Determinar estratégia
        strategy = self._determine_update_strategy(priority, security_info)
        
        # Determinar razões
        reasons = self._determine_update_reasons(security_info, app.version, latest_version)
        
        return UpdateInfo(
            application_name=app.name,
            current_version=app.version,
            available_version=latest_version,
            priority=priority,
            strategy=strategy,
            reasons=reasons,
            description=f"Atualização disponível de {app.version} para {latest_version}",
            security_score=security_info.get("score", 0.0),
            requires_restart=self._requires_restart(app.name),
            backup_recommended=priority in [UpdatePriority.CRITICAL, UpdatePriority.HIGH],
            metadata={
                "security_info": security_info,
                "app_metadata": app.metadata
            }
        )
    
    def _determine_update_priority(self, app, latest_version: str, security_info: Dict[str, Any]) -> UpdatePriority:
        """Determina a prioridade da atualização."""
        # Importação dinâmica para evitar circular import
        from .detection_engine import DetectedApplication
        
        # Verificar vulnerabilidades críticas
        if security_info.get("critical_vulnerabilities", 0) > 0:
            return UpdatePriority.CRITICAL
        
        # Verificar vulnerabilidades de alta severidade
        if security_info.get("high_vulnerabilities", 0) > 0:
            return UpdatePriority.HIGH
        
        # Verificar se é uma atualização de segurança
        if security_info.get("is_security_update", False):
            return UpdatePriority.HIGH
        
        # Verificar diferença de versão
        try:
            current_parts = [int(x) for x in app.version.split(".")[:3]]
            latest_parts = [int(x) for x in latest_version.split(".")[:3]]
            
            # Major version change
            if latest_parts[0] > current_parts[0]:
                return UpdatePriority.MEDIUM
            
            # Minor version change
            if latest_parts[1] > current_parts[1]:
                return UpdatePriority.MEDIUM
            
            # Patch version change
            if latest_parts[2] > current_parts[2]:
                return UpdatePriority.LOW
                
        except (ValueError, IndexError):
            pass
        
        return UpdatePriority.OPTIONAL
    
    def _determine_update_strategy(self, priority: UpdatePriority, security_info: Dict[str, Any]) -> UpdateStrategy:
        """Determina a estratégia de atualização."""
        if priority == UpdatePriority.CRITICAL:
            return UpdateStrategy.IMMEDIATE
        
        if priority == UpdatePriority.HIGH and security_info.get("is_security_update", False):
            if self.config["enable_auto_security_updates"]:
                return UpdateStrategy.IMMEDIATE
            else:
                return UpdateStrategy.SCHEDULED
        
        if priority in [UpdatePriority.MEDIUM, UpdatePriority.HIGH]:
            return UpdateStrategy.SCHEDULED
        
        return UpdateStrategy.MANUAL
    
    def _determine_update_reasons(self, security_info: Dict[str, Any], current_version: str, latest_version: str) -> List[UpdateReason]:
        """Determina as razões para atualização."""
        reasons = []
        
        if security_info.get("critical_vulnerabilities", 0) > 0 or security_info.get("high_vulnerabilities", 0) > 0:
            reasons.append(UpdateReason.SECURITY_VULNERABILITY)
        
        if security_info.get("is_security_update", False):
            reasons.append(UpdateReason.SECURITY_VULNERABILITY)
        
        # Verificar se é EOL
        if security_info.get("is_eol", False):
            reasons.append(UpdateReason.EOL_VERSION)
        
        # Assumir que é bug fix se não for major version
        try:
            current_major = int(current_version.split(".")[0])
            latest_major = int(latest_version.split(".")[0])
            
            if latest_major > current_major:
                reasons.append(UpdateReason.FEATURE_UPDATE)
            else:
                reasons.append(UpdateReason.BUG_FIX)
        except (ValueError, IndexError):
            reasons.append(UpdateReason.BUG_FIX)
        
        return reasons if reasons else [UpdateReason.FEATURE_UPDATE]
    
    def _requires_restart(self, app_name: str) -> bool:
        """Verifica se a aplicação requer reinicialização após atualização."""
        restart_required = {
            "visual studio", "visual studio code", "git", "java", "dotnet",
            "python", "nodejs", "docker", "virtualbox"
        }
        
        app_lower = app_name.lower()
        return any(req in app_lower for req in restart_required)
    
    def _generate_update_recommendation(self, updates: List[UpdateInfo]) -> UpdateRecommendation:
        """Gera recomendação de atualização."""
        if not updates:
            return UpdateRecommendation(
                updates=[],
                total_updates=0,
                critical_updates=0,
                security_updates=0,
                recommended_action="Nenhuma atualização necessária",
                estimated_time=timedelta(0),
                risk_assessment="Baixo"
            )
        
        # Contar por prioridade
        critical_count = sum(1 for u in updates if u.priority == UpdatePriority.CRITICAL)
        security_count = sum(1 for u in updates if UpdateReason.SECURITY_VULNERABILITY in u.reasons)
        
        # Determinar ação recomendada
        if critical_count > 0:
            recommended_action = f"Atualizar {critical_count} aplicação(ões) crítica(s) imediatamente"
            risk_assessment = "Alto"
        elif security_count > 0:
            recommended_action = f"Atualizar {security_count} aplicação(ões) de segurança em breve"
            risk_assessment = "Médio"
        else:
            recommended_action = "Agendar atualizações quando conveniente"
            risk_assessment = "Baixo"
        
        # Estimar tempo
        estimated_minutes = len(updates) * 5  # 5 minutos por atualização
        estimated_time = timedelta(minutes=estimated_minutes)
        
        # Criar grupos de lote
        batch_groups = self._create_batch_groups(updates)
        
        # Gerar avisos
        warnings = self._generate_warnings(updates)
        
        return UpdateRecommendation(
            updates=sorted(updates, key=lambda x: x.priority.value),
            total_updates=len(updates),
            critical_updates=critical_count,
            security_updates=security_count,
            recommended_action=recommended_action,
            estimated_time=estimated_time,
            risk_assessment=risk_assessment,
            batch_groups=batch_groups,
            warnings=warnings
        )
    
    def _create_batch_groups(self, updates: List[UpdateInfo]) -> List[List[str]]:
        """Cria grupos de lote para atualizações."""
        # Agrupar por prioridade e dependências
        critical = [u.application_name for u in updates if u.priority == UpdatePriority.CRITICAL]
        high = [u.application_name for u in updates if u.priority == UpdatePriority.HIGH]
        medium = [u.application_name for u in updates if u.priority == UpdatePriority.MEDIUM]
        low = [u.application_name for u in updates if u.priority in [UpdatePriority.LOW, UpdatePriority.OPTIONAL]]
        
        batches = []
        if critical:
            batches.append(critical)
        if high:
            batches.append(high)
        if medium:
            batches.append(medium)
        if low:
            batches.append(low)
        
        return batches
    
    def _generate_warnings(self, updates: List[UpdateInfo]) -> List[str]:
        """Gera avisos para as atualizações."""
        warnings = []
        
        restart_required = [u.application_name for u in updates if u.requires_restart]
        if restart_required:
            warnings.append(f"As seguintes aplicações requerem reinicialização: {', '.join(restart_required)}")
        
        backup_recommended = [u.application_name for u in updates if u.backup_recommended]
        if backup_recommended:
            warnings.append(f"Backup recomendado antes de atualizar: {', '.join(backup_recommended)}")
        
        conflicts = []
        for update in updates:
            conflicts.extend(update.conflicts)
        if conflicts:
            warnings.append(f"Possíveis conflitos detectados: {', '.join(set(conflicts))}")
        
        return warnings
    
    def _is_cache_valid(self, cache_key: str) -> bool:
        """Verifica se o cache é válido."""
        if cache_key not in self._last_check:
            return False
        
        cache_duration = timedelta(hours=self.config["cache_duration_hours"])
        return datetime.now() - self._last_check[cache_key] < cache_duration
    
    def clear_cache(self) -> None:
        """Limpa o cache de atualizações."""
        self._update_cache.clear()
        self._last_check.clear()
        self.logger.info("Cache de atualizações limpo")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas do cache."""
        return {
            "cached_updates": len(self._update_cache),
            "last_checks": len(self._last_check),
            "notification_history": len(self._notification_history)
        }


# Instância global
_intelligent_update_checker: Optional[IntelligentUpdateChecker] = None


def get_intelligent_update_checker(config: Optional[Dict[str, Any]] = None) -> IntelligentUpdateChecker:
    """Obtém instância global do verificador inteligente de atualizações."""
    global _intelligent_update_checker
    if _intelligent_update_checker is None:
        _intelligent_update_checker = IntelligentUpdateChecker(config)
    return _intelligent_update_checker


def configure_intelligent_update_checker(config: Dict[str, Any]) -> None:
    """Configura o verificador inteligente de atualizações."""
    global _intelligent_update_checker
    _intelligent_update_checker = IntelligentUpdateChecker(config)