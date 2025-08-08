# -*- coding: utf-8 -*-
"""
Plugin Runtime Integration System
Módulo responsável por integração de plugins com sistema de runtimes,
registro de novos runtimes via plugins e detecção de conflitos
"""

import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Type, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import threading
import importlib
import inspect

from .plugin_base import PluginInterface, PluginMetadata, RuntimePlugin
from .plugin_manager import PluginManager, LoadedPlugin
from .runtime_catalog_manager import RuntimeCatalogManager, RuntimeConfig
from .security_manager import SecurityManager, SecurityLevel

logger = logging.getLogger(__name__)

class ConflictType(Enum):
    """Tipos de conflitos entre plugins/runtimes"""
    VERSION_CONFLICT = "version_conflict"
    DEPENDENCY_CONFLICT = "dependency_conflict"
    RESOURCE_CONFLICT = "resource_conflict"
    API_CONFLICT = "api_conflict"
    RUNTIME_OVERLAP = "runtime_overlap"
    PERMISSION_CONFLICT = "permission_conflict"

class ConflictSeverity(Enum):
    """Severidade dos conflitos"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ResolutionStrategy(Enum):
    """Estratégias de resolução de conflitos"""
    MANUAL = "manual"
    AUTOMATIC = "automatic"
    PRIORITY_BASED = "priority_based"
    USER_CHOICE = "user_choice"
    DISABLE_CONFLICTING = "disable_conflicting"

@dataclass
class RuntimeConflict:
    """Conflito entre runtimes/plugins"""
    id: str
    conflict_type: ConflictType
    severity: ConflictSeverity
    description: str
    affected_plugins: List[str]
    affected_runtimes: List[str]
    resolution_strategy: ResolutionStrategy
    auto_resolvable: bool = False
    resolution_options: List[str] = field(default_factory=list)
    detected_at: datetime = field(default_factory=datetime.now)
    resolved: bool = False
    resolution_details: Optional[str] = None

@dataclass
class PluginRuntimeRegistration:
    """Registro de runtime por plugin"""
    plugin_name: str
    runtime_name: str
    runtime_config: RuntimeConfig
    registration_time: datetime
    priority: int = 50  # 0-100, higher = more priority
    override_existing: bool = False
    dependencies: List[str] = field(default_factory=list)
    conflicts_with: List[str] = field(default_factory=list)

@dataclass
class UpdateInfo:
    """Informações de atualização de plugin/runtime"""
    name: str
    current_version: str
    available_version: str
    update_type: str  # "plugin" or "runtime"
    update_url: Optional[str] = None
    changelog: Optional[str] = None
    requires_restart: bool = False
    breaking_changes: bool = False
    dependencies_updated: List[str] = field(default_factory=list)

class PluginRuntimeIntegrator:
    """
    Sistema de integração entre plugins e runtimes
    
    Funcionalidades:
    - Registro de novos runtimes via plugins
    - Detecção e resolução de conflitos
    - Gerenciamento de versões e atualizações
    - Validação de compatibilidade
    - Sistema de prioridades
    """
    
    def __init__(self, plugin_manager: Optional[PluginManager] = None, 
                 runtime_catalog: Optional[RuntimeCatalogManager] = None,
                 security_manager: Optional[SecurityManager] = None):
        """Inicializar integrador de plugins e runtimes"""
        self.logger = logging.getLogger(__name__)
        
        # Componentes principais
        self.plugin_manager = plugin_manager or PluginManager()
        self.runtime_catalog = runtime_catalog or RuntimeCatalogManager()
        self.security_manager = security_manager or SecurityManager()
        
        # Armazenamento de registros e conflitos
        self.runtime_registrations: Dict[str, PluginRuntimeRegistration] = {}
        self.detected_conflicts: Dict[str, RuntimeConflict] = {}
        self.plugin_priorities: Dict[str, int] = {}
        self.update_info: Dict[str, UpdateInfo] = {}
        
        # Configurações
        self.auto_resolve_conflicts = True
        self.allow_runtime_override = False
        self.max_conflict_resolution_attempts = 3
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Carregar configurações
        self._load_integration_config()
        
        self.logger.info("Plugin runtime integrator initialized")
    
    def register_plugin_runtime(self, plugin_name: str, runtime_config: RuntimeConfig, 
                              priority: int = 50, override_existing: bool = False) -> bool:
        """
        Registrar novo runtime via plugin
        
        Args:
            plugin_name: Nome do plugin
            runtime_config: Configuração do runtime
            priority: Prioridade do registro (0-100)
            override_existing: Se deve sobrescrever runtime existente
            
        Returns:
            bool: True se registrado com sucesso
        """
        try:
            with self._lock:
                # Verificar se plugin tem permissão
                if not self._check_plugin_permission(plugin_name, "register_runtime"):
                    self.logger.warning(f"Plugin {plugin_name} does not have permission to register runtimes")
                    return False
                
                # Verificar se runtime já existe
                existing_runtime = self.runtime_catalog.get_runtime_config(runtime_config.name)
                if existing_runtime and not override_existing:
                    self.logger.warning(f"Runtime {runtime_config.name} already exists and override not allowed")
                    return False
                
                # Validar configuração do runtime
                validation_result = self._validate_runtime_config(runtime_config)
                if not validation_result[0]:
                    self.logger.error(f"Runtime config validation failed: {validation_result[1]}")
                    return False
                
                # Criar registro
                registration = PluginRuntimeRegistration(
                    plugin_name=plugin_name,
                    runtime_name=runtime_config.name,
                    runtime_config=runtime_config,
                    registration_time=datetime.now(),
                    priority=priority,
                    override_existing=override_existing
                )
                
                # Detectar conflitos
                conflicts = self._detect_runtime_conflicts(registration)
                if conflicts and not self.auto_resolve_conflicts:
                    self.logger.warning(f"Conflicts detected for runtime {runtime_config.name}: {len(conflicts)}")
                    for conflict in conflicts:
                        self.detected_conflicts[conflict.id] = conflict
                    return False
                
                # Registrar runtime no catálogo
                success = self.runtime_catalog.add_runtime_config(runtime_config)
                if success:
                    self.runtime_registrations[runtime_config.name] = registration
                    self.logger.info(f"Successfully registered runtime {runtime_config.name} from plugin {plugin_name}")
                    
                    # Auditar operação
                    self.security_manager.audit_critical_operation(
                        operation="plugin_runtime_registration",
                        component="plugin_runtime_integration",
                        details={
                            "plugin_name": plugin_name,
                            "runtime_name": runtime_config.name,
                            "priority": priority,
                            "override_existing": override_existing
                        },
                        success=True,
                        security_level=SecurityLevel.MEDIUM
                    )
                    
                    return True
                else:
                    self.logger.error(f"Failed to register runtime {runtime_config.name} in catalog")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Error registering plugin runtime: {e}")
            return False
    
    def unregister_plugin_runtime(self, plugin_name: str, runtime_name: str) -> bool:
        """
        Desregistrar runtime de plugin
        
        Args:
            plugin_name: Nome do plugin
            runtime_name: Nome do runtime
            
        Returns:
            bool: True se desregistrado com sucesso
        """
        try:
            with self._lock:
                # Verificar se registro existe
                registration = self.runtime_registrations.get(runtime_name)
                if not registration or registration.plugin_name != plugin_name:
                    self.logger.warning(f"No registration found for runtime {runtime_name} from plugin {plugin_name}")
                    return False
                
                # Verificar dependências
                dependent_runtimes = self._find_dependent_runtimes(runtime_name)
                if dependent_runtimes:
                    self.logger.warning(f"Cannot unregister runtime {runtime_name}: has dependents {dependent_runtimes}")
                    return False
                
                # Remover do catálogo
                success = self.runtime_catalog.remove_runtime_config(runtime_name)
                if success:
                    del self.runtime_registrations[runtime_name]
                    self.logger.info(f"Successfully unregistered runtime {runtime_name} from plugin {plugin_name}")
                    return True
                else:
                    self.logger.error(f"Failed to unregister runtime {runtime_name} from catalog")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Error unregistering plugin runtime: {e}")
            return False
    
    def detect_all_conflicts(self) -> List[RuntimeConflict]:
        """
        Detectar todos os conflitos entre plugins e runtimes
        
        Returns:
            List[RuntimeConflict]: Lista de conflitos detectados
        """
        conflicts = []
        
        try:
            with self._lock:
                # Detectar conflitos entre plugins
                plugin_conflicts = self._detect_plugin_conflicts()
                conflicts.extend(plugin_conflicts)
                
                # Detectar conflitos entre runtimes
                runtime_conflicts = self._detect_runtime_version_conflicts()
                conflicts.extend(runtime_conflicts)
                
                # Detectar conflitos de recursos
                resource_conflicts = self._detect_resource_conflicts()
                conflicts.extend(resource_conflicts)
                
                # Detectar conflitos de API
                api_conflicts = self._detect_api_conflicts()
                conflicts.extend(api_conflicts)
                
                # Armazenar conflitos detectados
                for conflict in conflicts:
                    self.detected_conflicts[conflict.id] = conflict
                
                self.logger.info(f"Detected {len(conflicts)} conflicts")
                return conflicts
                
        except Exception as e:
            self.logger.error(f"Error detecting conflicts: {e}")
            return []
    
    def resolve_conflict(self, conflict_id: str, strategy: ResolutionStrategy, 
                        user_choice: Optional[str] = None) -> bool:
        """
        Resolver conflito específico
        
        Args:
            conflict_id: ID do conflito
            strategy: Estratégia de resolução
            user_choice: Escolha do usuário (se aplicável)
            
        Returns:
            bool: True se resolvido com sucesso
        """
        try:
            conflict = self.detected_conflicts.get(conflict_id)
            if not conflict:
                self.logger.warning(f"Conflict {conflict_id} not found")
                return False
            
            if conflict.resolved:
                self.logger.info(f"Conflict {conflict_id} already resolved")
                return True
            
            success = False
            resolution_details = ""
            
            if strategy == ResolutionStrategy.AUTOMATIC:
                success, resolution_details = self._auto_resolve_conflict(conflict)
            elif strategy == ResolutionStrategy.PRIORITY_BASED:
                success, resolution_details = self._priority_resolve_conflict(conflict)
            elif strategy == ResolutionStrategy.USER_CHOICE:
                success, resolution_details = self._user_choice_resolve_conflict(conflict, user_choice)
            elif strategy == ResolutionStrategy.DISABLE_CONFLICTING:
                success, resolution_details = self._disable_conflicting_resolve(conflict)
            else:
                self.logger.warning(f"Manual resolution required for conflict {conflict_id}")
                return False
            
            if success:
                conflict.resolved = True
                conflict.resolution_details = resolution_details
                self.logger.info(f"Successfully resolved conflict {conflict_id}: {resolution_details}")
            else:
                self.logger.error(f"Failed to resolve conflict {conflict_id}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error resolving conflict {conflict_id}: {e}")
            return False
    
    def check_plugin_updates(self) -> List[UpdateInfo]:
        """
        Verificar atualizações disponíveis para plugins
        
        Returns:
            List[UpdateInfo]: Lista de atualizações disponíveis
        """
        updates = []
        
        try:
            # Verificar atualizações de plugins
            loaded_plugins = self.plugin_manager.loaded_plugins
            for plugin_name, loaded_plugin in loaded_plugins.items():
                update_info = self._check_plugin_update(loaded_plugin)
                if update_info:
                    updates.append(update_info)
                    self.update_info[plugin_name] = update_info
            
            # Verificar atualizações de runtimes registrados por plugins
            for runtime_name, registration in self.runtime_registrations.items():
                update_info = self._check_runtime_update(registration)
                if update_info:
                    updates.append(update_info)
                    self.update_info[runtime_name] = update_info
            
            self.logger.info(f"Found {len(updates)} available updates")
            return updates
            
        except Exception as e:
            self.logger.error(f"Error checking updates: {e}")
            return []
    
    def get_integration_status(self) -> Dict[str, Any]:
        """
        Obter status da integração
        
        Returns:
            Dict[str, Any]: Status da integração
        """
        try:
            total_plugins = len(self.plugin_manager.loaded_plugins)
            runtime_plugins = len([p for p in self.plugin_manager.loaded_plugins.values() 
                                 if isinstance(p.instance, RuntimePlugin)])
            registered_runtimes = len(self.runtime_registrations)
            active_conflicts = len([c for c in self.detected_conflicts.values() if not c.resolved])
            available_updates = len(self.update_info)
            
            return {
                "summary": {
                    "total_plugins": total_plugins,
                    "runtime_plugins": runtime_plugins,
                    "registered_runtimes": registered_runtimes,
                    "active_conflicts": active_conflicts,
                    "available_updates": available_updates
                },
                "plugin_registrations": {
                    name: {
                        "plugin_name": reg.plugin_name,
                        "runtime_name": reg.runtime_name,
                        "priority": reg.priority,
                        "registration_time": reg.registration_time.isoformat()
                    }
                    for name, reg in self.runtime_registrations.items()
                },
                "conflicts": {
                    conflict_id: {
                        "type": conflict.conflict_type.value,
                        "severity": conflict.severity.value,
                        "description": conflict.description,
                        "resolved": conflict.resolved,
                        "affected_plugins": conflict.affected_plugins,
                        "affected_runtimes": conflict.affected_runtimes
                    }
                    for conflict_id, conflict in self.detected_conflicts.items()
                },
                "updates": {
                    name: {
                        "current_version": update.current_version,
                        "available_version": update.available_version,
                        "update_type": update.update_type,
                        "requires_restart": update.requires_restart,
                        "breaking_changes": update.breaking_changes
                    }
                    for name, update in self.update_info.items()
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting integration status: {e}")
            return {}
    
    def _check_plugin_permission(self, plugin_name: str, operation: str) -> bool:
        """
        Verificar se plugin tem permissão para operação
        
        Args:
            plugin_name: Nome do plugin
            operation: Operação a verificar
            
        Returns:
            bool: True se tem permissão
        """
        # TODO: Integrar com sistema de permissões do plugin_security
        # Por enquanto, permitir para todos os plugins carregados
        return plugin_name in self.plugin_manager.loaded_plugins
    
    def _validate_runtime_config(self, config: RuntimeConfig) -> Tuple[bool, List[str]]:
        """
        Validar configuração de runtime
        
        Args:
            config: Configuração do runtime
            
        Returns:
            Tuple[bool, List[str]]: (is_valid, issues)
        """
        issues = []
        
        # Validações básicas
        if not config.name or not config.name.strip():
            issues.append("Runtime name is required")
        
        if not config.version or not config.version.strip():
            issues.append("Runtime version is required")
        
        if not config.download_urls:
            issues.append("At least one download URL is required")
        
        # Validar URLs
        for url in config.download_urls:
            validation_result = self.security_manager.validate_input(url, "url")
            if validation_result.validation_result.value != "safe":
                issues.append(f"Unsafe download URL: {url}")
        
        # Validar comandos de validação
        if config.validation_commands:
            for cmd in config.validation_commands:
                validation_result = self.security_manager.validate_input(cmd, "command")
                if validation_result.validation_result.value != "safe":
                    issues.append(f"Unsafe validation command: {cmd}")
        
        return len(issues) == 0, issues
    
    def _detect_runtime_conflicts(self, registration: PluginRuntimeRegistration) -> List[RuntimeConflict]:
        """
        Detectar conflitos para novo registro de runtime
        
        Args:
            registration: Registro do runtime
            
        Returns:
            List[RuntimeConflict]: Lista de conflitos
        """
        conflicts = []
        
        # Verificar conflito de nome
        existing_registration = self.runtime_registrations.get(registration.runtime_name)
        if existing_registration and not registration.override_existing:
            conflict = RuntimeConflict(
                id=f"name_conflict_{registration.runtime_name}",
                conflict_type=ConflictType.RUNTIME_OVERLAP,
                severity=ConflictSeverity.HIGH,
                description=f"Runtime {registration.runtime_name} already registered by plugin {existing_registration.plugin_name}",
                affected_plugins=[registration.plugin_name, existing_registration.plugin_name],
                affected_runtimes=[registration.runtime_name],
                resolution_strategy=ResolutionStrategy.PRIORITY_BASED,
                auto_resolvable=True,
                resolution_options=["use_higher_priority", "rename_runtime", "merge_configs"]
            )
            conflicts.append(conflict)
        
        return conflicts
    
    def _detect_plugin_conflicts(self) -> List[RuntimeConflict]:
        """
        Detectar conflitos entre plugins
        
        Returns:
            List[RuntimeConflict]: Lista de conflitos
        """
        conflicts = []
        
        # Implementar detecção de conflitos entre plugins
        # Por exemplo: plugins que registram runtimes com mesmo nome
        
        return conflicts
    
    def _detect_runtime_version_conflicts(self) -> List[RuntimeConflict]:
        """
        Detectar conflitos de versão entre runtimes
        
        Returns:
            List[RuntimeConflict]: Lista de conflitos
        """
        conflicts = []
        
        # Implementar detecção de conflitos de versão
        # Por exemplo: versões incompatíveis do mesmo runtime
        
        return conflicts
    
    def _detect_resource_conflicts(self) -> List[RuntimeConflict]:
        """
        Detectar conflitos de recursos
        
        Returns:
            List[RuntimeConflict]: Lista de conflitos
        """
        conflicts = []
        
        # Implementar detecção de conflitos de recursos
        # Por exemplo: plugins que usam mesmas portas ou arquivos
        
        return conflicts
    
    def _detect_api_conflicts(self) -> List[RuntimeConflict]:
        """
        Detectar conflitos de API
        
        Returns:
            List[RuntimeConflict]: Lista de conflitos
        """
        conflicts = []
        
        # Implementar detecção de conflitos de API
        # Por exemplo: plugins que expõem mesmas APIs
        
        return conflicts
    
    def _auto_resolve_conflict(self, conflict: RuntimeConflict) -> Tuple[bool, str]:
        """
        Resolver conflito automaticamente
        
        Args:
            conflict: Conflito a resolver
            
        Returns:
            Tuple[bool, str]: (success, resolution_details)
        """
        if not conflict.auto_resolvable:
            return False, "Conflict is not auto-resolvable"
        
        # Implementar resolução automática baseada no tipo de conflito
        if conflict.conflict_type == ConflictType.RUNTIME_OVERLAP:
            return self._resolve_runtime_overlap(conflict)
        
        return False, "No automatic resolution strategy available"
    
    def _priority_resolve_conflict(self, conflict: RuntimeConflict) -> Tuple[bool, str]:
        """
        Resolver conflito baseado em prioridades
        
        Args:
            conflict: Conflito a resolver
            
        Returns:
            Tuple[bool, str]: (success, resolution_details)
        """
        # Implementar resolução baseada em prioridades dos plugins
        return False, "Priority-based resolution not implemented"
    
    def _user_choice_resolve_conflict(self, conflict: RuntimeConflict, choice: Optional[str]) -> Tuple[bool, str]:
        """
        Resolver conflito baseado na escolha do usuário
        
        Args:
            conflict: Conflito a resolver
            choice: Escolha do usuário
            
        Returns:
            Tuple[bool, str]: (success, resolution_details)
        """
        if not choice or choice not in conflict.resolution_options:
            return False, "Invalid user choice"
        
        # Implementar resolução baseada na escolha do usuário
        return False, "User choice resolution not implemented"
    
    def _disable_conflicting_resolve(self, conflict: RuntimeConflict) -> Tuple[bool, str]:
        """
        Resolver conflito desabilitando plugins conflitantes
        
        Args:
            conflict: Conflito a resolver
            
        Returns:
            Tuple[bool, str]: (success, resolution_details)
        """
        # Implementar resolução desabilitando plugins
        return False, "Disable conflicting resolution not implemented"
    
    def _resolve_runtime_overlap(self, conflict: RuntimeConflict) -> Tuple[bool, str]:
        """
        Resolver sobreposição de runtimes
        
        Args:
            conflict: Conflito a resolver
            
        Returns:
            Tuple[bool, str]: (success, resolution_details)
        """
        # Implementar resolução de sobreposição de runtimes
        return False, "Runtime overlap resolution not implemented"
    
    def _find_dependent_runtimes(self, runtime_name: str) -> List[str]:
        """
        Encontrar runtimes que dependem do runtime especificado
        
        Args:
            runtime_name: Nome do runtime
            
        Returns:
            List[str]: Lista de runtimes dependentes
        """
        dependents = []
        
        for reg in self.runtime_registrations.values():
            if runtime_name in reg.dependencies:
                dependents.append(reg.runtime_name)
        
        return dependents
    
    def _check_plugin_update(self, loaded_plugin: LoadedPlugin) -> Optional[UpdateInfo]:
        """
        Verificar atualização para plugin
        
        Args:
            loaded_plugin: Plugin carregado
            
        Returns:
            Optional[UpdateInfo]: Informação de atualização se disponível
        """
        # TODO: Implementar verificação real de atualizações
        # Por enquanto, retornar None (sem atualizações)
        return None
    
    def _check_runtime_update(self, registration: PluginRuntimeRegistration) -> Optional[UpdateInfo]:
        """
        Verificar atualização para runtime registrado por plugin
        
        Args:
            registration: Registro do runtime
            
        Returns:
            Optional[UpdateInfo]: Informação de atualização se disponível
        """
        # TODO: Implementar verificação real de atualizações
        # Por enquanto, retornar None (sem atualizações)
        return None
    
    def _load_integration_config(self):
        """
        Carregar configurações de integração
        """
        try:
            config_path = Path("config/plugin_integration.json")
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                self.auto_resolve_conflicts = config.get("auto_resolve_conflicts", True)
                self.allow_runtime_override = config.get("allow_runtime_override", False)
                self.max_conflict_resolution_attempts = config.get("max_conflict_resolution_attempts", 3)
                
                # Carregar prioridades de plugins
                self.plugin_priorities.update(config.get("plugin_priorities", {}))
                
                self.logger.info("Loaded plugin integration configuration")
        except Exception as e:
            self.logger.warning(f"Could not load plugin integration config: {e}")


# Instância global do integrador
plugin_runtime_integrator = PluginRuntimeIntegrator()


if __name__ == "__main__":
    # Teste do sistema de integração
    from .runtime_catalog_manager import RuntimeConfig
    
    # Criar configuração de runtime de teste
    test_runtime_config = RuntimeConfig(
        name="test_runtime",
        version="1.0.0",
        description="Test runtime from plugin",
        download_urls=["https://example.com/test_runtime.exe"],
        installation_type="executable",
        validation_commands=["test_runtime --version"]
    )
    
    # Testar integração
    integrator = PluginRuntimeIntegrator()
    
    # Registrar runtime
    success = integrator.register_plugin_runtime(
        plugin_name="test_plugin",
        runtime_config=test_runtime_config,
        priority=75
    )
    print(f"Runtime registration: {success}")
    
    # Detectar conflitos
    conflicts = integrator.detect_all_conflicts()
    print(f"Detected conflicts: {len(conflicts)}")
    
    # Verificar atualizações
    updates = integrator.check_plugin_updates()
    print(f"Available updates: {len(updates)}")
    
    # Obter status
    status = integrator.get_integration_status()
    print(f"Integration status: {json.dumps(status, indent=2)}")