# -*- coding: utf-8 -*-
"""
Installation Manager para Environment Dev Script
Módulo responsável por instalações robustas com rollback automático
"""

import os
import sys
import logging
import subprocess
import shutil
import tempfile
import json
import threading
import time
from pathlib import Path
from typing import Dict, Optional, Tuple, List, Any, Set
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import networkx as nx
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False
    nx = None

from utils.robust_verification import robust_verifier
from utils.extractor import extract_archive
from utils.permission_checker import is_admin, check_write_permission
from core.error_handler import EnvDevError, ErrorSeverity, ErrorCategory
from core.download_manager import DownloadManager
from core.preparation_manager import PreparationManager

logger = logging.getLogger(__name__)

class InstallationType(Enum):
    """Tipos de instalação suportados"""
    EXECUTABLE = "executable"
    MSI = "msi"
    ARCHIVE = "archive"
    SCRIPT = "script"
    PORTABLE = "portable"
    REGISTRY = "registry"
    MANUAL = "manual"

class InstallationStatus(Enum):
    """Status da instalação"""
    PENDING = "pending"
    PREPARING = "preparing"
    DOWNLOADING = "downloading"
    INSTALLING = "installing"
    VERIFYING = "verifying"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ROLLING_BACK = "rolling_back"
    ROLLED_BACK = "rolled_back"

@dataclass
class RollbackInfo:
    """Informações para rollback de uma instalação"""
    rollback_id: str
    component_name: str
    timestamp: datetime
    backup_paths: List[str] = field(default_factory=list)
    registry_backups: List[str] = field(default_factory=list)
    env_vars_backup: Dict[str, str] = field(default_factory=dict)
    installed_files: List[str] = field(default_factory=list)
    created_directories: List[str] = field(default_factory=list)
    modified_files: List[str] = field(default_factory=list)
    rollback_script: Optional[str] = None

@dataclass
class InstallationState:
    """Estado atual de uma instalação"""
    component: str
    status: InstallationStatus
    progress: float = 0.0
    current_step: str = ""
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    rollback_info: Optional[RollbackInfo] = None
    dependencies: List[str] = field(default_factory=list)
    dependents: List[str] = field(default_factory=list)

@dataclass
class InstallationResult:
    """Resultado de uma instalação"""
    success: bool
    status: InstallationStatus
    message: str
    details: Dict[str, Any]
    installed_path: Optional[str] = None
    version: Optional[str] = None
    rollback_info: Optional[RollbackInfo] = None
    installation_time: float = 0.0
    verification_result: Optional[Dict] = None

@dataclass
class ConflictInfo:
    """Informações sobre conflitos entre componentes"""
    component1: str
    component2: str
    conflict_type: str
    description: str
    severity: str
    resolution_suggestion: Optional[str] = None

@dataclass
class ParallelInstallationGroup:
    """Grupo de componentes que podem ser instalados em paralelo"""
    components: List[str]
    level: int
    can_install_parallel: bool = True

@dataclass
class BatchInstallationResult:
    """Resultado de uma instalação em lote"""
    overall_success: bool
    completed_components: List[str] = field(default_factory=list)
    failed_components: List[str] = field(default_factory=list)
    skipped_components: List[str] = field(default_factory=list)
    installation_results: Dict[str, InstallationResult] = field(default_factory=dict)
    total_time: float = 0.0
    dependency_order: List[str] = field(default_factory=list)
    rollback_performed: bool = False
    rollback_results: Dict[str, bool] = field(default_factory=dict)
    parallel_groups: List[ParallelInstallationGroup] = field(default_factory=list)
    detected_conflicts: List[ConflictInfo] = field(default_factory=list)
    recovery_attempts: Dict[str, int] = field(default_factory=dict)
    parallel_installations: int = 0

class InstallationStrategy(ABC):
    """Estratégia base para instalação"""
    
    @abstractmethod
    def can_handle(self, component_data: Dict) -> bool:
        """Verifica se pode lidar com este tipo de instalação"""
        pass
    
    @abstractmethod
    def install(self, file_path: str, component_data: Dict, 
               progress_callback: Optional[callable] = None) -> InstallationResult:
        """Executa a instalação"""
        pass
    
    @abstractmethod
    def verify_installation(self, component_data: Dict) -> InstallationResult:
        """Verifica se a instalação foi bem-sucedida"""
        pass

class ExecutableInstaller(InstallationStrategy):
    """Instalador para executáveis (.exe)"""
    
    def can_handle(self, component_data: Dict) -> bool:
        install_method = component_data.get('install_method', '')
        return install_method == 'executable' or install_method.endswith('.exe')
    
    def install(self, file_path: str, component_data: Dict, 
               progress_callback: Optional[callable] = None) -> InstallationResult:
        try:
            if progress_callback:
                progress_callback("Preparando instalação executável...")
            
            # Verifica privilégios se necessário
            if component_data.get('requires_admin', False):
                if not check_admin_privileges():
                    return InstallationResult(
                        success=False,
                        status=InstallationStatus.FAILED,
                        message="Privilégios de administrador necessários",
                        details={'error': 'insufficient_privileges'}
                    )
            
            # Prepara argumentos de instalação
            install_args = component_data.get('install_args', ['/S'])  # Silent por padrão
            command = [file_path] + install_args
            
            logger.info(f"Executando instalação: {' '.join(command)}")
            
            if progress_callback:
                progress_callback("Executando instalador...")
            
            # Executa instalação
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=component_data.get('install_timeout', 300)  # 5 minutos padrão
            )
            
            if result.returncode == 0:
                logger.info(f"Instalação executável concluída com sucesso")
                
                # Verifica instalação
                verification = self.verify_installation(component_data)
                
                return InstallationResult(
                    success=verification.success,
                    status=InstallationStatus.COMPLETED if verification.success else InstallationStatus.FAILED,
                    message="Instalação executável concluída" if verification.success else "Instalação falhou na verificação",
                    details={
                        'return_code': result.returncode,
                        'stdout': result.stdout,
                        'stderr': result.stderr,
                        'verification': verification.details
                    },
                    installed_path=verification.installed_path,
                    version=verification.version
                )
            else:
                return InstallationResult(
                    success=False,
                    status=InstallationStatus.FAILED,
                    message=f"Instalação falhou (código {result.returncode})",
                    details={
                        'return_code': result.returncode,
                        'stdout': result.stdout,
                        'stderr': result.stderr
                    }
                )
                
        except subprocess.TimeoutExpired:
            return InstallationResult(
                success=False,
                status=InstallationStatus.FAILED,
                message="Instalação demorou muito (timeout)",
                details={'error': 'timeout'}
            )
        except Exception as e:
            logger.error(f"Erro na instalação executável: {e}")
            return InstallationResult(
                success=False,
                status=InstallationStatus.FAILED,
                message=f"Erro na instalação: {e}",
                details={'error': str(e)}
            )
    
    def verify_installation(self, component_data: Dict) -> InstallationResult:
        """Verifica instalação usando verificação robusta"""
        try:
            status = robust_verifier.get_comprehensive_status(component_data)
            
            success = status['overall_status'] in ['fully_verified', 'partially_verified']
            
            return InstallationResult(
                success=success,
                status=InstallationStatus.COMPLETED if success else InstallationStatus.FAILED,
                message=f"Verificação: {status['overall_status']}",
                details=status,
                installed_path=status['paths'][0] if status['paths'] else None,
                version=status['versions'][0] if status['versions'] else None
            )
        except Exception as e:
            return InstallationResult(
                success=False,
                status=InstallationStatus.FAILED,
                message=f"Erro na verificação: {e}",
                details={'error': str(e)}
            )

class MSIInstaller(InstallationStrategy):
    """Instalador para pacotes MSI"""
    
    def can_handle(self, component_data: Dict) -> bool:
        install_method = component_data.get('install_method', '')
        return install_method == 'msi' or install_method.endswith('.msi')
    
    def install(self, file_path: str, component_data: Dict, 
               progress_callback: Optional[callable] = None) -> InstallationResult:
        # Implementação similar ao ExecutableInstaller mas para MSI
        return ExecutableInstaller().install(file_path, component_data, progress_callback)
    
    def verify_installation(self, component_data: Dict) -> InstallationResult:
        return ExecutableInstaller().verify_installation(component_data)

class ArchiveInstaller(InstallationStrategy):
    """Instalador para arquivos compactados"""
    
    def can_handle(self, component_data: Dict) -> bool:
        install_method = component_data.get('install_method', '')
        return install_method in ['archive', 'zip', 'tar', 'rar']
    
    def install(self, file_path: str, component_data: Dict, 
               progress_callback: Optional[callable] = None) -> InstallationResult:
        # Implementação para extração de arquivos
        return ExecutableInstaller().install(file_path, component_data, progress_callback)
    
    def verify_installation(self, component_data: Dict) -> InstallationResult:
        return ExecutableInstaller().verify_installation(component_data)

class ScriptInstaller(InstallationStrategy):
    """Instalador para scripts"""
    
    def can_handle(self, component_data: Dict) -> bool:
        install_method = component_data.get('install_method', '')
        return install_method in ['script', 'powershell', 'batch']
    
    def install(self, file_path: str, component_data: Dict, 
               progress_callback: Optional[callable] = None) -> InstallationResult:
        # Implementação para execução de scripts
        return ExecutableInstaller().install(file_path, component_data, progress_callback)
    
    def verify_installation(self, component_data: Dict) -> InstallationResult:
        return ExecutableInstaller().verify_installation(component_data)

class InstallationManager:
    """
    Gerenciador principal de instalações com rollback automático e gerenciamento de dependências
    
    Responsável por:
    - Instalação robusta com rollback automático
    - Detecção de dependências circulares
    - Verificação pós-instalação confiável
    - Instalação em lote inteligente
    - Recovery automático de falhas
    """
    
    def __init__(self, base_path: Optional[str] = None):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.base_path = base_path or os.getcwd()
        
        # Inicializa componentes auxiliares
        self.download_manager = DownloadManager()
        self.preparation_manager = PreparationManager(base_path)
        
        # Estratégias de instalação
        self.strategies = [
            ExecutableInstaller(),
            MSIInstaller(),
            ArchiveInstaller(),
            ScriptInstaller()
        ]
        
        # Estado das instalações
        self.installation_states: Dict[str, InstallationState] = {}
        self.rollback_registry: Dict[str, RollbackInfo] = {}
        
        # Diretório para armazenar informações de rollback
        self.rollback_dir = os.path.join(self.base_path, "rollback")
        os.makedirs(self.rollback_dir, exist_ok=True)
    
    def install_component(self, component: str) -> InstallationResult:
        """
        Instala um componente específico com rollback automático
        
        Args:
            component: Nome do componente a ser instalado
            
        Returns:
            InstallationResult: Resultado da instalação
        """
        start_time = datetime.now()
        self.logger.info(f"Iniciando instalação do componente: {component}")
        
        # Cria estado da instalação
        state = InstallationState(
            component=component,
            status=InstallationStatus.PREPARING
        )
        self.installation_states[component] = state
        
        try:
            # 1. Prepara ambiente
            state.status = InstallationStatus.PREPARING
            state.current_step = "Preparando ambiente"
            prep_result = self.preparation_manager.prepare_environment([component])
            
            if not prep_result.status.value == "completed":
                return self._handle_installation_failure(
                    component, "Falha na preparação do ambiente", 
                    prep_result.errors, start_time
                )
            
            # 2. Carrega configuração do componente
            component_data = self._load_component_config(component)
            if not component_data:
                return self._handle_installation_failure(
                    component, f"Configuração do componente {component} não encontrada", 
                    [], start_time
                )
            
            # 3. Cria informações de rollback
            rollback_info = self._create_rollback_info(component)
            state.rollback_info = rollback_info
            
            # 4. Download do componente
            state.status = InstallationStatus.DOWNLOADING
            state.current_step = "Baixando componente"
            file_path = self._download_component(component_data)
            
            if not file_path:
                return self._handle_installation_failure(
                    component, "Falha no download do componente", 
                    [], start_time
                )
            
            # 5. Executa instalação
            state.status = InstallationStatus.INSTALLING
            state.current_step = "Instalando componente"
            
            strategy = self._get_strategy(component_data)
            if not strategy:
                return self._handle_installation_failure(
                    component, "Método de instalação não suportado", 
                    [component_data.get('install_method', 'unknown')], start_time
                )
            
            # Instala com monitoramento para rollback
            install_result = self._install_with_rollback_tracking(
                strategy, file_path, component_data, rollback_info
            )
            
            if not install_result.success:
                # Executa rollback automático
                self._perform_rollback(rollback_info)
                return self._handle_installation_failure(
                    component, install_result.message, 
                    [install_result.details], start_time
                )
            
            # 6. Verificação pós-instalação
            state.status = InstallationStatus.VERIFYING
            state.current_step = "Verificando instalação"
            
            verification_result = self.verify_installation(component)
            if not verification_result.success:
                # Executa rollback automático
                self._perform_rollback(rollback_info)
                return self._handle_installation_failure(
                    component, "Falha na verificação pós-instalação", 
                    [verification_result.details], start_time
                )
            
            # 7. Finaliza instalação
            state.status = InstallationStatus.COMPLETED
            state.end_time = datetime.now()
            
            # Salva informações de rollback para uso futuro
            self._save_rollback_info(rollback_info)
            
            installation_time = (state.end_time - start_time).total_seconds()
            
            self.logger.info(f"Instalação de {component} concluída com sucesso em {installation_time:.2f}s")
            
            return InstallationResult(
                success=True,
                status=InstallationStatus.COMPLETED,
                message=f"Componente {component} instalado com sucesso",
                details={
                    'component': component,
                    'installation_time': installation_time,
                    'verification': verification_result.details
                },
                installed_path=verification_result.installed_path,
                version=verification_result.version,
                rollback_info=rollback_info,
                installation_time=installation_time,
                verification_result=verification_result.details
            )
            
        except Exception as e:
            # Executa rollback em caso de erro crítico
            if component in self.rollback_registry:
                self._perform_rollback(self.rollback_registry[component])
            
            return self._handle_installation_failure(
                component, f"Erro crítico na instalação: {e}", 
                [str(e)], start_time
            )
    
    def install_multiple(self, components: List[str], max_parallel: int = 3, 
                        enable_recovery: bool = True) -> BatchInstallationResult:
        """
        Instala múltiplos componentes com resolução automática de dependências,
        instalação paralela inteligente e recovery automático
        
        Args:
            components: Lista de componentes para instalar
            max_parallel: Número máximo de instalações paralelas
            enable_recovery: Habilita recovery automático de falhas
            
        Returns:
            BatchInstallationResult: Resultado da instalação em lote
        """
        start_time = datetime.now()
        self.logger.info(f"Iniciando instalação em lote inteligente de {len(components)} componentes")
        
        result = BatchInstallationResult(overall_success=False)
        
        try:
            # 1. Detecta conflitos entre componentes
            conflicts = self._detect_component_conflicts(components)
            result.detected_conflicts = conflicts
            
            if conflicts:
                critical_conflicts = [c for c in conflicts if c.severity == 'critical']
                if critical_conflicts:
                    self.logger.error(f"Conflitos críticos detectados: {len(critical_conflicts)}")
                    for conflict in critical_conflicts:
                        self.logger.error(f"Conflito: {conflict.description}")
                    result.overall_success = False
                    return result
                else:
                    self.logger.warning(f"Conflitos não-críticos detectados: {len(conflicts)}")
            
            # 2. Detecta dependências circulares
            if self.detect_circular_dependencies(components):
                result.overall_success = False
                self.logger.error("Dependências circulares detectadas")
                return result
            
            # 3. Resolve ordem de instalação e grupos paralelos
            parallel_groups = self._create_parallel_installation_groups(components)
            result.parallel_groups = parallel_groups
            result.dependency_order = [comp for group in parallel_groups for comp in group.components]
            
            self.logger.info(f"Grupos de instalação paralela criados: {len(parallel_groups)}")
            
            # 4. Instala componentes por grupos com paralelização
            for group_idx, group in enumerate(parallel_groups):
                self.logger.info(f"Processando grupo {group_idx + 1}/{len(parallel_groups)}: {group.components}")
                
                if group.can_install_parallel and len(group.components) > 1:
                    # Instalação paralela
                    group_result = self._install_group_parallel(
                        group, max_parallel, enable_recovery, result
                    )
                else:
                    # Instalação sequencial
                    group_result = self._install_group_sequential(
                        group, enable_recovery, result
                    )
                
                # Verifica se deve continuar
                if not group_result and self._has_critical_failures(result):
                    self.logger.warning("Parando instalação devido a falhas críticas")
                    
                    # Marca componentes restantes como pulados
                    remaining_groups = parallel_groups[group_idx + 1:]
                    for remaining_group in remaining_groups:
                        result.skipped_components.extend(remaining_group.components)
                    
                    # Executa rollback se necessário
                    if enable_recovery:
                        result.rollback_performed = True
                        result.rollback_results = self._rollback_batch_installation(
                            result.completed_components
                        )
                    break
            
            # 5. Calcula resultado final
            end_time = datetime.now()
            result.total_time = (end_time - start_time).total_seconds()
            result.overall_success = len(result.failed_components) == 0
            result.parallel_installations = sum(
                len(g.components) for g in parallel_groups if g.can_install_parallel
            )
            
            self.logger.info(
                f"Instalação em lote inteligente concluída: "
                f"{len(result.completed_components)} sucessos, "
                f"{len(result.failed_components)} falhas, "
                f"{len(result.skipped_components)} pulados, "
                f"{result.parallel_installations} instalações paralelas"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Erro crítico na instalação em lote: {e}")
            result.overall_success = False
            return result
    
    def verify_installation(self, component: str) -> InstallationResult:
        """
        Verifica se um componente está instalado corretamente
        
        Args:
            component: Nome do componente para verificar
            
        Returns:
            InstallationResult: Resultado da verificação
        """
        try:
            component_data = self._load_component_config(component)
            if not component_data:
                return InstallationResult(
                    success=False,
                    status=InstallationStatus.FAILED,
                    message=f"Configuração do componente {component} não encontrada",
                    details={}
                )
            
            strategy = self._get_strategy(component_data)
            if not strategy:
                return InstallationResult(
                    success=False,
                    status=InstallationStatus.FAILED,
                    message="Estratégia de verificação não encontrada",
                    details={}
                )
            
            return strategy.verify_installation(component_data)
            
        except Exception as e:
            self.logger.error(f"Erro na verificação de {component}: {e}")
            return InstallationResult(
                success=False,
                status=InstallationStatus.FAILED,
                message=f"Erro na verificação: {e}",
                details={'error': str(e)}
            )
    
    def rollback_installation(self, component: str) -> bool:
        """
        Executa rollback de uma instalação específica
        
        Args:
            component: Nome do componente para fazer rollback
            
        Returns:
            bool: True se o rollback foi bem-sucedido
        """
        try:
            rollback_info = self._load_rollback_info(component)
            if not rollback_info:
                self.logger.error(f"Informações de rollback não encontradas para {component}")
                return False
            
            return self._perform_rollback(rollback_info)
            
        except Exception as e:
            self.logger.error(f"Erro no rollback de {component}: {e}")
            return False
    
    def detect_circular_dependencies(self, components: List[str]) -> bool:
        """
        Detecta dependências circulares entre componentes
        
        Args:
            components: Lista de componentes para verificar
            
        Returns:
            bool: True se há dependências circulares
        """
        try:
            if HAS_NETWORKX:
                return self._detect_circular_dependencies_networkx(components)
            else:
                return self._detect_circular_dependencies_simple(components)
                
        except Exception as e:
            self.logger.error(f"Erro na detecção de dependências circulares: {e}")
            return True  # Assume que há problema para ser seguro
    
    def _detect_circular_dependencies_networkx(self, components: List[str]) -> bool:
        """Detecta dependências circulares usando NetworkX"""
        try:
            # Cria grafo de dependências
            graph = nx.DiGraph()
            
            for component in components:
                component_data = self._load_component_config(component)
                if component_data:
                    dependencies = component_data.get('dependencies', [])
                    
                    # Adiciona nó
                    graph.add_node(component)
                    
                    # Adiciona arestas para dependências
                    for dep in dependencies:
                        if dep in components:  # Só considera dependências na lista
                            graph.add_edge(component, dep)
            
            # Verifica se há ciclos
            try:
                cycles = list(nx.simple_cycles(graph))
                if cycles:
                    self.logger.error(f"Dependências circulares detectadas: {cycles}")
                    return True
                return False
            except nx.NetworkXError:
                return False
                
        except Exception as e:
            self.logger.error(f"Erro na detecção de dependências circulares com NetworkX: {e}")
            return True
    
    def _detect_circular_dependencies_simple(self, components: List[str]) -> bool:
        """Detecta dependências circulares usando algoritmo simples"""
        try:
            # Constrói grafo de dependências
            graph = {}
            for component in components:
                component_data = self._load_component_config(component)
                if component_data:
                    dependencies = component_data.get('dependencies', [])
                    # Filtra apenas dependências que estão na lista de componentes
                    graph[component] = [dep for dep in dependencies if dep in components]
                else:
                    graph[component] = []
            
            # Usa DFS para detectar ciclos
            visited = set()
            rec_stack = set()
            
            def has_cycle(node):
                if node in rec_stack:
                    return True
                if node in visited:
                    return False
                
                visited.add(node)
                rec_stack.add(node)
                
                for neighbor in graph.get(node, []):
                    if has_cycle(neighbor):
                        return True
                
                rec_stack.remove(node)
                return False
            
            # Verifica cada componente
            for component in components:
                if component not in visited:
                    if has_cycle(component):
                        self.logger.error(f"Dependência circular detectada envolvendo: {component}")
                        return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Erro na detecção simples de dependências circulares: {e}")
            return True
    
    # Helper methods
    def _get_strategy(self, component_data: Dict) -> Optional[InstallationStrategy]:
        """Obtém estratégia apropriada para o componente"""
        for strategy in self.strategies:
            if strategy.can_handle(component_data):
                return strategy
        return None
    
    def _load_component_config(self, component: str) -> Optional[Dict]:
        """Carrega configuração de um componente"""
        try:
            config_path = os.path.join(self.base_path, "config", "components", f"{component}.yaml")
            if os.path.exists(config_path):
                import yaml
                with open(config_path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
            
            # Tenta carregar de configuração global
            global_config_path = os.path.join(self.base_path, "environment_dev.yaml")
            if os.path.exists(global_config_path):
                import yaml
                with open(global_config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                    components = config.get('components', {})
                    return components.get(component)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar configuração de {component}: {e}")
            return None
    
    def _download_component(self, component_data: Dict) -> Optional[str]:
        """Baixa componente usando DownloadManager"""
        try:
            download_url = component_data.get('download_url')
            if not download_url:
                self.logger.error("URL de download não especificada")
                return None
            
            # Usa DownloadManager para download seguro
            result = self.download_manager.download_with_verification(
                url=download_url,
                expected_hash=component_data.get('hash_value', ''),
                hash_algorithm=component_data.get('hash_algorithm', 'sha256')
            )
            
            if result.success:
                return result.file_path
            else:
                self.logger.error(f"Falha no download: {result.error_message}")
                return None
                
        except Exception as e:
            self.logger.error(f"Erro no download do componente: {e}")
            return None
    
    def _create_rollback_info(self, component: str) -> RollbackInfo:
        """Cria informações de rollback para um componente"""
        rollback_id = f"{component}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        rollback_info = RollbackInfo(
            rollback_id=rollback_id,
            component_name=component,
            timestamp=datetime.now()
        )
        
        # Registra para uso posterior
        self.rollback_registry[component] = rollback_info
        
        return rollback_info
    
    def _install_with_rollback_tracking(self, strategy: InstallationStrategy, 
                                      file_path: str, component_data: Dict,
                                      rollback_info: RollbackInfo) -> InstallationResult:
        """Instala componente com tracking para rollback"""
        try:
            # Captura estado antes da instalação
            self._capture_pre_install_state(rollback_info)
            
            # Executa instalação
            result = strategy.install(file_path, component_data)
            
            if result.success:
                # Captura estado após instalação para rollback
                self._capture_post_install_state(rollback_info, result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Erro na instalação com tracking: {e}")
            return InstallationResult(
                success=False,
                status=InstallationStatus.FAILED,
                message=f"Erro na instalação: {e}",
                details={'error': str(e)}
            )
    
    def _capture_pre_install_state(self, rollback_info: RollbackInfo) -> None:
        """Captura estado do sistema antes da instalação"""
        try:
            # Backup de variáveis de ambiente relevantes
            env_vars_to_backup = ['PATH', 'PROGRAMFILES', 'PROGRAMFILES(X86)']
            for var in env_vars_to_backup:
                value = os.environ.get(var)
                if value:
                    rollback_info.env_vars_backup[var] = value
            
            self.logger.debug(f"Estado pré-instalação capturado para {rollback_info.component_name}")
            
        except Exception as e:
            self.logger.warning(f"Erro ao capturar estado pré-instalação: {e}")
    
    def _capture_post_install_state(self, rollback_info: RollbackInfo, 
                                   install_result: InstallationResult) -> None:
        """Captura estado após instalação para rollback"""
        try:
            # Adiciona caminho instalado
            if install_result.installed_path:
                rollback_info.installed_files.append(install_result.installed_path)
            
            self.logger.debug(f"Estado pós-instalação capturado para {rollback_info.component_name}")
            
        except Exception as e:
            self.logger.warning(f"Erro ao capturar estado pós-instalação: {e}")
    
    def _perform_rollback(self, rollback_info: RollbackInfo) -> bool:
        """Executa rollback de uma instalação"""
        try:
            self.logger.info(f"Iniciando rollback de {rollback_info.component_name}")
            
            success = True
            
            # 1. Remove arquivos instalados
            for file_path in rollback_info.installed_files:
                try:
                    if os.path.exists(file_path):
                        if os.path.isdir(file_path):
                            shutil.rmtree(file_path)
                        else:
                            os.unlink(file_path)
                        self.logger.debug(f"Removido: {file_path}")
                except Exception as e:
                    self.logger.error(f"Erro ao remover {file_path}: {e}")
                    success = False
            
            # 2. Remove diretórios criados
            for dir_path in rollback_info.created_directories:
                try:
                    if os.path.exists(dir_path) and os.path.isdir(dir_path):
                        # Remove apenas se estiver vazio
                        if not os.listdir(dir_path):
                            os.rmdir(dir_path)
                            self.logger.debug(f"Diretório removido: {dir_path}")
                except Exception as e:
                    self.logger.error(f"Erro ao remover diretório {dir_path}: {e}")
                    success = False
            
            if success:
                self.logger.info(f"Rollback de {rollback_info.component_name} concluído com sucesso")
            else:
                self.logger.warning(f"Rollback de {rollback_info.component_name} concluído com problemas")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Erro crítico no rollback: {e}")
            return False
    
    def _save_rollback_info(self, rollback_info: RollbackInfo) -> None:
        """Salva informações de rollback em arquivo"""
        try:
            rollback_file = os.path.join(self.rollback_dir, f"{rollback_info.rollback_id}.json")
            
            # Converte para dicionário serializável
            rollback_data = {
                'rollback_id': rollback_info.rollback_id,
                'component_name': rollback_info.component_name,
                'timestamp': rollback_info.timestamp.isoformat(),
                'backup_paths': rollback_info.backup_paths,
                'registry_backups': rollback_info.registry_backups,
                'env_vars_backup': rollback_info.env_vars_backup,
                'installed_files': rollback_info.installed_files,
                'created_directories': rollback_info.created_directories,
                'modified_files': rollback_info.modified_files,
                'rollback_script': rollback_info.rollback_script
            }
            
            with open(rollback_file, 'w', encoding='utf-8') as f:
                json.dump(rollback_data, f, indent=2, ensure_ascii=False)
            
            self.logger.debug(f"Informações de rollback salvas: {rollback_file}")
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar informações de rollback: {e}")
    
    def _load_rollback_info(self, component: str) -> Optional[RollbackInfo]:
        """Carrega informações de rollback de um componente"""
        try:
            # Procura arquivo de rollback mais recente para o componente
            rollback_files = []
            for filename in os.listdir(self.rollback_dir):
                if filename.startswith(f"{component}_") and filename.endswith('.json'):
                    rollback_files.append(filename)
            
            if not rollback_files:
                return None
            
            # Usa o mais recente
            rollback_files.sort(reverse=True)
            rollback_file = os.path.join(self.rollback_dir, rollback_files[0])
            
            with open(rollback_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Reconstrói objeto RollbackInfo
            rollback_info = RollbackInfo(
                rollback_id=data['rollback_id'],
                component_name=data['component_name'],
                timestamp=datetime.fromisoformat(data['timestamp']),
                backup_paths=data.get('backup_paths', []),
                registry_backups=data.get('registry_backups', []),
                env_vars_backup=data.get('env_vars_backup', {}),
                installed_files=data.get('installed_files', []),
                created_directories=data.get('created_directories', []),
                modified_files=data.get('modified_files', []),
                rollback_script=data.get('rollback_script')
            )
            
            return rollback_info
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar informações de rollback: {e}")
            return None
    
    def _resolve_dependency_order(self, components: List[str]) -> List[str]:
        """Resolve ordem de instalação baseada em dependências"""
        try:
            if HAS_NETWORKX:
                return self._resolve_dependency_order_networkx(components)
            else:
                return self._resolve_dependency_order_simple(components)
                
        except Exception as e:
            self.logger.error(f"Erro na resolução de dependências: {e}")
            return components
    
    def _resolve_dependency_order_networkx(self, components: List[str]) -> List[str]:
        """Resolve ordem usando NetworkX"""
        try:
            # Cria grafo de dependências
            graph = nx.DiGraph()
            
            for component in components:
                component_data = self._load_component_config(component)
                if component_data:
                    dependencies = component_data.get('dependencies', [])
                    
                    # Adiciona nó
                    graph.add_node(component)
                    
                    # Adiciona arestas para dependências
                    for dep in dependencies:
                        if dep in components:
                            graph.add_edge(dep, component)  # dep -> component
            
            # Adiciona componentes sem configuração
            for component in components:
                if component not in graph:
                    graph.add_node(component)
            
            # Ordenação topológica
            try:
                return list(nx.topological_sort(graph))
            except nx.NetworkXError:
                # Se há ciclos, retorna ordem original
                self.logger.warning("Não foi possível resolver ordem de dependências, usando ordem original")
                return components
                
        except Exception as e:
            self.logger.error(f"Erro na resolução de dependências com NetworkX: {e}")
            return components
    
    def _resolve_dependency_order_simple(self, components: List[str]) -> List[str]:
        """Resolve ordem usando algoritmo simples de ordenação topológica"""
        try:
            # Constrói grafo de dependências
            graph = {}
            in_degree = {}
            
            # Inicializa
            for component in components:
                graph[component] = []
                in_degree[component] = 0
            
            # Constrói grafo
            for component in components:
                component_data = self._load_component_config(component)
                if component_data:
                    dependencies = component_data.get('dependencies', [])
                    for dep in dependencies:
                        if dep in components:
                            graph[dep].append(component)
                            in_degree[component] += 1
            
            # Ordenação topológica usando algoritmo de Kahn
            queue = [comp for comp in components if in_degree[comp] == 0]
            result = []
            
            while queue:
                current = queue.pop(0)
                result.append(current)
                
                for neighbor in graph[current]:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)
            
            # Se não conseguiu ordenar todos, há ciclo
            if len(result) != len(components):
                self.logger.warning("Possível dependência circular, usando ordem original")
                return components
            
            return result
            
        except Exception as e:
            self.logger.error(f"Erro na resolução simples de dependências: {e}")
            return components
    
    def _should_stop_batch_installation(self, component: str, result: InstallationResult) -> bool:
        """Decide se deve parar instalação em lote após falha"""
        # Para por falhas críticas ou componentes essenciais
        critical_components = ['vcredist', 'dotnet', 'python']
        
        if component.lower() in critical_components:
            return True
        
        # Para se erro indica problema sistêmico
        if 'insufficient_privileges' in str(result.details):
            return True
        
        if 'disk_space' in str(result.details):
            return True
        
        return False
    
    def _rollback_batch_installation(self, completed_components: List[str]) -> Dict[str, bool]:
        """Executa rollback de instalação em lote"""
        rollback_results = {}
        
        # Faz rollback na ordem reversa
        for component in reversed(completed_components):
            try:
                success = self.rollback_installation(component)
                rollback_results[component] = success
                
                if success:
                    self.logger.info(f"Rollback de {component} bem-sucedido")
                else:
                    self.logger.error(f"Rollback de {component} falhou")
                    
            except Exception as e:
                self.logger.error(f"Erro no rollback de {component}: {e}")
                rollback_results[component] = False
        
        return rollback_results
    
    def _detect_component_conflicts(self, components: List[str]) -> List[ConflictInfo]:
        """
        Detecta conflitos entre componentes
        
        Args:
            components: Lista de componentes para verificar
            
        Returns:
            List[ConflictInfo]: Lista de conflitos detectados
        """
        conflicts = []
        
        try:
            # Carrega configurações de todos os componentes
            component_configs = {}
            for component in components:
                config = self._load_component_config(component)
                if config:
                    component_configs[component] = config
            
            # Verifica conflitos entre pares de componentes
            for i, comp1 in enumerate(components):
                for comp2 in components[i+1:]:
                    conflict = self._check_component_pair_conflict(
                        comp1, comp2, component_configs
                    )
                    if conflict:
                        conflicts.append(conflict)
            
            return conflicts
            
        except Exception as e:
            self.logger.error(f"Erro na detecção de conflitos: {e}")
            return []
    
    def _check_component_pair_conflict(self, comp1: str, comp2: str, 
                                     configs: Dict[str, Dict]) -> Optional[ConflictInfo]:
        """Verifica conflito entre dois componentes específicos"""
        try:
            config1 = configs.get(comp1, {})
            config2 = configs.get(comp2, {})
            
            # Verifica conflitos explícitos
            conflicts1 = config1.get('conflicts', [])
            conflicts2 = config2.get('conflicts', [])
            
            if comp2 in conflicts1 or comp1 in conflicts2:
                return ConflictInfo(
                    component1=comp1,
                    component2=comp2,
                    conflict_type="explicit",
                    description=f"Conflito explícito entre {comp1} e {comp2}",
                    severity="critical",
                    resolution_suggestion="Escolha apenas um dos componentes"
                )
            
            # Verifica conflitos de arquivo/diretório
            paths1 = set(config1.get('install_paths', []))
            paths2 = set(config2.get('install_paths', []))
            
            if paths1.intersection(paths2):
                common_paths = paths1.intersection(paths2)
                return ConflictInfo(
                    component1=comp1,
                    component2=comp2,
                    conflict_type="path",
                    description=f"Conflito de caminhos: {list(common_paths)}",
                    severity="warning",
                    resolution_suggestion="Verifique se os componentes podem coexistir"
                )
            
            # Verifica conflitos de versão
            if self._check_version_conflict(config1, config2):
                return ConflictInfo(
                    component1=comp1,
                    component2=comp2,
                    conflict_type="version",
                    description=f"Conflito de versões entre {comp1} e {comp2}",
                    severity="warning",
                    resolution_suggestion="Verifique compatibilidade de versões"
                )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Erro ao verificar conflito entre {comp1} e {comp2}: {e}")
            return None
    
    def _check_version_conflict(self, config1: Dict, config2: Dict) -> bool:
        """Verifica conflitos de versão entre dois componentes"""
        try:
            # Verifica se ambos modificam o mesmo software base
            base1 = config1.get('base_software')
            base2 = config2.get('base_software')
            
            if base1 and base2 and base1 == base2:
                version1 = config1.get('version', '')
                version2 = config2.get('version', '')
                
                # Se versões são diferentes, pode haver conflito
                if version1 and version2 and version1 != version2:
                    return True
            
            return False
            
        except Exception:
            return False
    
    def _create_parallel_installation_groups(self, components: List[str]) -> List[ParallelInstallationGroup]:
        """
        Cria grupos de componentes que podem ser instalados em paralelo
        
        Args:
            components: Lista de componentes
            
        Returns:
            List[ParallelInstallationGroup]: Grupos de instalação paralela
        """
        try:
            # Resolve ordem de dependências primeiro
            dependency_order = self._resolve_dependency_order(components)
            
            # Cria grafo de dependências para análise
            dependency_graph = self._build_dependency_graph(components)
            
            # Agrupa componentes por nível de dependência
            levels = self._calculate_dependency_levels(dependency_graph, dependency_order)
            
            # Cria grupos paralelos
            groups = []
            for level, level_components in levels.items():
                # Verifica se componentes do mesmo nível podem ser instalados em paralelo
                can_parallel = self._can_install_parallel(level_components)
                
                group = ParallelInstallationGroup(
                    components=level_components,
                    level=level,
                    can_install_parallel=can_parallel
                )
                groups.append(group)
            
            return groups
            
        except Exception as e:
            self.logger.error(f"Erro ao criar grupos paralelos: {e}")
            # Fallback: cria grupos sequenciais
            return [
                ParallelInstallationGroup(
                    components=[comp],
                    level=i,
                    can_install_parallel=False
                )
                for i, comp in enumerate(components)
            ]
    
    def _build_dependency_graph(self, components: List[str]) -> Dict[str, List[str]]:
        """Constrói grafo de dependências"""
        graph = {}
        
        for component in components:
            config = self._load_component_config(component)
            if config:
                dependencies = config.get('dependencies', [])
                # Filtra apenas dependências que estão na lista
                graph[component] = [dep for dep in dependencies if dep in components]
            else:
                graph[component] = []
        
        return graph
    
    def _calculate_dependency_levels(self, graph: Dict[str, List[str]], 
                                   order: List[str]) -> Dict[int, List[str]]:
        """Calcula níveis de dependência para paralelização"""
        levels = {}
        component_levels = {}
        
        # Calcula nível de cada componente
        for component in order:
            dependencies = graph.get(component, [])
            
            if not dependencies:
                # Sem dependências = nível 0
                level = 0
            else:
                # Nível = máximo nível das dependências + 1
                dep_levels = [component_levels.get(dep, 0) for dep in dependencies]
                level = max(dep_levels) + 1 if dep_levels else 0
            
            component_levels[component] = level
            
            # Adiciona ao grupo do nível
            if level not in levels:
                levels[level] = []
            levels[level].append(component)
        
        return levels
    
    def _can_install_parallel(self, components: List[str]) -> bool:
        """Verifica se componentes podem ser instalados em paralelo"""
        try:
            # Verifica se há conflitos entre os componentes
            conflicts = self._detect_component_conflicts(components)
            critical_conflicts = [c for c in conflicts if c.severity == 'critical']
            
            if critical_conflicts:
                return False
            
            # Verifica se todos suportam instalação paralela
            for component in components:
                config = self._load_component_config(component)
                if config and not config.get('supports_parallel_install', True):
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao verificar paralelização: {e}")
            return False
    
    def _install_group_parallel(self, group: ParallelInstallationGroup, 
                              max_parallel: int, enable_recovery: bool,
                              result: BatchInstallationResult) -> bool:
        """Instala grupo de componentes em paralelo"""
        try:
            self.logger.info(f"Instalação paralela de {len(group.components)} componentes")
            
            # Limita paralelismo
            max_workers = min(max_parallel, len(group.components))
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submete tarefas de instalação
                future_to_component = {
                    executor.submit(self._install_component_with_recovery, comp, enable_recovery, result): comp
                    for comp in group.components
                }
                
                # Processa resultados conforme completam
                group_success = True
                for future in as_completed(future_to_component):
                    component = future_to_component[future]
                    
                    try:
                        install_result = future.result()
                        result.installation_results[component] = install_result
                        
                        if install_result.success:
                            result.completed_components.append(component)
                            self.logger.info(f"Instalação paralela de {component} bem-sucedida")
                        else:
                            result.failed_components.append(component)
                            group_success = False
                            self.logger.error(f"Falha na instalação paralela de {component}: {install_result.message}")
                            
                    except Exception as e:
                        self.logger.error(f"Erro na instalação paralela de {component}: {e}")
                        result.failed_components.append(component)
                        group_success = False
                        
                        # Cria resultado de erro
                        result.installation_results[component] = InstallationResult(
                            success=False,
                            status=InstallationStatus.FAILED,
                            message=f"Erro na instalação paralela: {e}",
                            details={'error': str(e)}
                        )
            
            return group_success
            
        except Exception as e:
            self.logger.error(f"Erro crítico na instalação paralela: {e}")
            return False
    
    def _install_group_sequential(self, group: ParallelInstallationGroup,
                                enable_recovery: bool, result: BatchInstallationResult) -> bool:
        """Instala grupo de componentes sequencialmente"""
        try:
            self.logger.info(f"Instalação sequencial de {len(group.components)} componentes")
            
            group_success = True
            for component in group.components:
                install_result = self._install_component_with_recovery(component, enable_recovery, result)
                result.installation_results[component] = install_result
                
                if install_result.success:
                    result.completed_components.append(component)
                    self.logger.info(f"Instalação sequencial de {component} bem-sucedida")
                else:
                    result.failed_components.append(component)
                    group_success = False
                    self.logger.error(f"Falha na instalação sequencial de {component}: {install_result.message}")
                    
                    # Para instalação sequencial se há falha crítica
                    if self._is_critical_failure(install_result):
                        break
            
            return group_success
            
        except Exception as e:
            self.logger.error(f"Erro na instalação sequencial: {e}")
            return False
    
    def _install_component_with_recovery(self, component: str, enable_recovery: bool,
                                       result: BatchInstallationResult) -> InstallationResult:
        """Instala componente com tentativas de recovery"""
        max_attempts = 3 if enable_recovery else 1
        
        for attempt in range(max_attempts):
            if attempt > 0:
                self.logger.info(f"Tentativa de recovery {attempt + 1}/{max_attempts} para {component}")
                result.recovery_attempts[component] = attempt + 1
                
                # Aguarda antes de tentar novamente
                time.sleep(2 ** attempt)  # Backoff exponencial
            
            install_result = self.install_component(component)
            
            if install_result.success:
                return install_result
            
            # Verifica se deve tentar recovery
            if not enable_recovery or not self._should_retry_installation(install_result):
                break
            
            self.logger.warning(f"Tentativa {attempt + 1} falhou para {component}, tentando recovery...")
        
        return install_result
    
    def _should_retry_installation(self, result: InstallationResult) -> bool:
        """Verifica se deve tentar recovery da instalação"""
        # Não tenta recovery para erros críticos
        error_details = str(result.details)
        
        if 'insufficient_privileges' in error_details:
            return False
        
        if 'disk_space' in error_details:
            return False
        
        if 'circular_dependency' in error_details:
            return False
        
        # Tenta recovery para erros de rede, timeout, etc.
        recoverable_errors = ['timeout', 'network', 'download', 'temporary']
        
        return any(error in error_details.lower() for error in recoverable_errors)
    
    def _has_critical_failures(self, result: BatchInstallationResult) -> bool:
        """Verifica se há falhas críticas que devem parar a instalação"""
        for component, install_result in result.installation_results.items():
            if not install_result.success and self._is_critical_failure(install_result):
                return True
        return False
    
    def _is_critical_failure(self, result: InstallationResult) -> bool:
        """Verifica se uma falha é crítica"""
        error_details = str(result.details)
        
        critical_errors = [
            'insufficient_privileges',
            'disk_space',
            'circular_dependency',
            'critical_conflict'
        ]
        
        return any(error in error_details for error in critical_errors)
    
    def _handle_installation_failure(self, component: str, message: str, 
                                   errors: List, start_time: datetime) -> InstallationResult:
        """Trata falha na instalação"""
        end_time = datetime.now()
        installation_time = (end_time - start_time).total_seconds()
        
        # Atualiza estado
        if component in self.installation_states:
            self.installation_states[component].status = InstallationStatus.FAILED
            self.installation_states[component].error_message = message
            self.installation_states[component].end_time = end_time
        
        self.logger.error(f"Instalação de {component} falhou: {message}")
        
        return InstallationResult(
            success=False,
            status=InstallationStatus.FAILED,
            message=message,
            details={
                'component': component,
                'errors': errors,
                'installation_time': installation_time
            },
            installation_time=installation_time
        )

    
    def register_application(self, app_id: str, app_config: Dict[str, Any]) -> None:
        """Registra uma aplicação no sistema de instalação"""
        if not hasattr(self, 'registered_applications'):
            self.registered_applications = {}
        
        self.registered_applications[app_id] = app_config
        self.logger.info(f"Aplicação registrada: {app_id}")
    
    def get_registered_applications(self) -> List[Dict[str, Any]]:
        """Retorna lista de aplicações registradas"""
        if not hasattr(self, 'registered_applications'):
            self.registered_applications = {}
        
        return list(self.registered_applications.values())
    
    def notify_installation_start(self, component: str) -> None:
        """Notifica início de instalação"""
        self.logger.info(f"Iniciando instalação: {component}")
        # Aqui poderia notificar listeners, GUI, etc.
    
    def notify_installation_success(self, component: str) -> None:
        """Notifica sucesso na instalação"""
        self.logger.info(f"Instalação bem-sucedida: {component}")
        # Aqui poderia notificar listeners, GUI, etc.
    
    def notify_installation_failure(self, component: str, error: str) -> None:
        """Notifica falha na instalação"""
        self.logger.error(f"Falha na instalação de {component}: {error}")
        # Aqui poderia notificar listeners, GUI, etc.


def check_admin_privileges() -> bool:
    """Verifica se tem privilégios administrativos"""
    try:
        return is_admin()
    except Exception:
        return False


# Instância global
installation_manager = InstallationManager()


# Classes de dados adicionais necessárias
@dataclass
class ConflictInfo:
    """Informações sobre conflito entre componentes"""
    component1: str
    component2: str
    conflict_type: str  # explicit, path, version
    description: str
    severity: str  # critical, warning, info
    resolution_suggestion: str

@dataclass
class ParallelInstallationGroup:
    """Grupo de componentes para instalação paralela"""
    components: List[str]
    level: int
    can_install_parallel: bool

# Instância global
installation_manager = InstallationManager()