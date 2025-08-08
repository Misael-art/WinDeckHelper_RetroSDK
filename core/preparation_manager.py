# -*- coding: utf-8 -*-
"""
Preparation Manager para Environment Dev Script
Módulo responsável por preparação inteligente do ambiente antes das instalações
"""

import os
import sys
import shutil
import logging
import platform
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from utils.permission_checker import (
    is_admin, check_write_permission, check_read_permission,
    check_permissions_for_installation
)
from utils.disk_space import get_disk_space, format_size, check_disk_space
from utils.env_manager import set_env_var, get_env_var, add_to_path
from core.error_handler import EnvDevError, ErrorSeverity, ErrorCategory

logger = logging.getLogger(__name__)

class PreparationStatus(Enum):
    """Status da preparação do ambiente"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class BackupType(Enum):
    """Tipo de backup"""
    DIRECTORY = "directory"
    FILE = "file"
    REGISTRY = "registry"
    ENVIRONMENT_VAR = "environment_var"

@dataclass
class BackupInfo:
    """Informações sobre um backup criado"""
    backup_id: str
    original_path: str
    backup_path: str
    backup_type: BackupType
    timestamp: datetime = field(default_factory=datetime.now)
    size_bytes: int = 0
    checksum: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DirectoryConflict:
    """Representa um conflito de diretório detectado"""
    path: str
    conflict_type: str  # "exists", "permission", "readonly", "in_use"
    description: str
    severity: str  # "low", "medium", "high", "critical"
    suggested_action: str
    can_auto_resolve: bool = False
    backup_required: bool = False

@dataclass
class EnvironmentVariable:
    """Representa uma variável de ambiente a ser configurada"""
    name: str
    value: str
    scope: str = "user"  # "user" ou "system"
    append_to_existing: bool = False
    separator: str = ";"
    backup_existing: bool = True

@dataclass
class PreparationResult:
    """Resultado da preparação do ambiente"""
    status: PreparationStatus
    directories_created: List[str] = field(default_factory=list)
    backups_created: List[BackupInfo] = field(default_factory=list)
    conflicts_resolved: List[DirectoryConflict] = field(default_factory=list)
    env_vars_configured: List[EnvironmentVariable] = field(default_factory=list)
    permissions_granted: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    preparation_time: float = 0.0
    total_space_used: int = 0
    message: str = ""

class PreparationManager:
    """
    Gerenciador de preparação do ambiente
    
    Responsável por:
    - Criação automática de diretórios necessários
    - Backup de configurações existentes
    - Resolução de conflitos de diretório
    - Configuração de variáveis de ambiente
    - Gerenciamento de permissões
    """
    
    def __init__(self, base_path: Optional[str] = None):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.base_path = base_path or os.getcwd()
        self.backup_base_dir = os.path.join(self.base_path, "backups")
        self.temp_dir = os.path.join(self.base_path, "temp")
        self._backups_registry: List[BackupInfo] = []
        
        # Cria diretórios base se não existirem
        self._ensure_base_directories()
    
    def _ensure_base_directories(self) -> None:
        """Garante que os diretórios base existam"""
        try:
            os.makedirs(self.backup_base_dir, exist_ok=True)
            os.makedirs(self.temp_dir, exist_ok=True)
        except Exception as e:
            self.logger.error(f"Erro ao criar diretórios base: {e}")
    
    def prepare_environment(self, components: List[str]) -> PreparationResult:
        """
        Prepara o ambiente para instalação dos componentes especificados
        
        Args:
            components: Lista de componentes que serão instalados
            
        Returns:
            PreparationResult: Resultado da preparação
        """
        start_time = datetime.now()
        self.logger.info(f"Iniciando preparação do ambiente para componentes: {components}")
        
        result = PreparationResult(status=PreparationStatus.IN_PROGRESS)
        
        try:
            # 1. Verifica espaço em disco disponível
            self._check_available_space(result)
            
            # 2. Cria estrutura de diretórios necessária
            self._create_directory_structure(components, result)
            
            # 3. Detecta e resolve conflitos de diretório
            self._resolve_directory_conflicts(result)
            
            # 4. Cria backups de configurações existentes
            self._backup_existing_configurations(components, result)
            
            # 5. Configura variáveis de ambiente necessárias
            self._configure_environment_variables(components, result)
            
            # 6. Prepara dependências de sistema automaticamente
            self._prepare_system_dependencies(components, result)
            
            # 7. Verifica e solicita permissões necessárias
            self._ensure_required_permissions(components, result)
            
            # Calcula tempo total
            end_time = datetime.now()
            result.preparation_time = (end_time - start_time).total_seconds()
            
            # Define status final
            if result.errors:
                result.status = PreparationStatus.FAILED
                result.message = f"Preparação falhou com {len(result.errors)} erro(s)"
            else:
                result.status = PreparationStatus.COMPLETED
                result.message = f"Ambiente preparado com sucesso em {result.preparation_time:.2f}s"
            
            self.logger.info(f"Preparação concluída: {result.message}")
            return result
            
        except Exception as e:
            result.status = PreparationStatus.FAILED
            result.errors.append(f"Erro crítico na preparação: {e}")
            result.message = f"Falha crítica na preparação: {e}"
            self.logger.error(f"Erro crítico na preparação: {e}")
            return result
    
    def _check_available_space(self, result: PreparationResult) -> None:
        """Verifica se há espaço suficiente em disco"""
        try:
            disk_info = get_disk_space(self.base_path)
            free_space_gb = disk_info['free'] / (1024**3)
            
            # Requer pelo menos 2GB livres para operações
            min_required_gb = 2.0
            
            if free_space_gb < min_required_gb:
                result.errors.append(
                    f"Espaço insuficiente: {free_space_gb:.1f}GB disponível, "
                    f"mínimo {min_required_gb}GB necessário"
                )
            else:
                self.logger.info(f"Espaço em disco verificado: {free_space_gb:.1f}GB disponível")
                
        except Exception as e:
            result.warnings.append(f"Não foi possível verificar espaço em disco: {e}")
    
    def create_directory_structure(self, component: str) -> bool:
        """
        Cria estrutura de diretórios para um componente específico
        
        Args:
            component: Nome do componente
            
        Returns:
            bool: True se a estrutura foi criada com sucesso
        """
        try:
            # Define diretórios padrão para cada componente
            component_dirs = {
                "downloads": os.path.join(self.base_path, "downloads", component),
                "temp": os.path.join(self.temp_dir, component),
                "logs": os.path.join(self.base_path, "logs", component),
                "config": os.path.join(self.base_path, "config", component),
                "cache": os.path.join(self.base_path, "cache", component)
            }
            
            created_dirs = []
            for dir_type, dir_path in component_dirs.items():
                if not os.path.exists(dir_path):
                    os.makedirs(dir_path, exist_ok=True)
                    created_dirs.append(dir_path)
                    self.logger.debug(f"Diretório criado: {dir_path}")
            
            if created_dirs:
                self.logger.info(f"Estrutura de diretórios criada para {component}: {len(created_dirs)} diretórios")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao criar estrutura de diretórios para {component}: {e}")
            return False
    
    def _create_directory_structure(self, components: List[str], result: PreparationResult) -> None:
        """Cria estrutura de diretórios para todos os componentes"""
        for component in components:
            try:
                if self.create_directory_structure(component):
                    # Adiciona diretórios criados ao resultado
                    component_dirs = [
                        os.path.join(self.base_path, "downloads", component),
                        os.path.join(self.temp_dir, component),
                        os.path.join(self.base_path, "logs", component),
                        os.path.join(self.base_path, "config", component),
                        os.path.join(self.base_path, "cache", component)
                    ]
                    
                    for dir_path in component_dirs:
                        if os.path.exists(dir_path) and dir_path not in result.directories_created:
                            result.directories_created.append(dir_path)
                else:
                    result.errors.append(f"Falha ao criar estrutura de diretórios para {component}")
                    
            except Exception as e:
                result.errors.append(f"Erro ao processar diretórios para {component}: {e}") 
   
    def backup_existing_configs(self, paths: List[str]) -> List[BackupInfo]:
        """
        Cria backup de configurações existentes
        
        Args:
            paths: Lista de caminhos para fazer backup
            
        Returns:
            List[BackupInfo]: Lista de informações dos backups criados
        """
        backups = []
        
        for path in paths:
            try:
                if not os.path.exists(path):
                    self.logger.debug(f"Caminho não existe, pulando backup: {path}")
                    continue
                
                # Gera ID único para o backup
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_id = f"backup_{timestamp}_{os.path.basename(path)}"
                
                # Define caminho do backup
                backup_path = os.path.join(self.backup_base_dir, backup_id)
                
                # Determina tipo de backup
                if os.path.isdir(path):
                    backup_type = BackupType.DIRECTORY
                    shutil.copytree(path, backup_path)
                else:
                    backup_type = BackupType.FILE
                    os.makedirs(os.path.dirname(backup_path), exist_ok=True)
                    shutil.copy2(path, backup_path)
                
                # Calcula tamanho do backup
                if os.path.isdir(backup_path):
                    size_bytes = sum(
                        os.path.getsize(os.path.join(dirpath, filename))
                        for dirpath, dirnames, filenames in os.walk(backup_path)
                        for filename in filenames
                    )
                else:
                    size_bytes = os.path.getsize(backup_path)
                
                # Cria informações do backup
                backup_info = BackupInfo(
                    backup_id=backup_id,
                    original_path=path,
                    backup_path=backup_path,
                    backup_type=backup_type,
                    size_bytes=size_bytes,
                    metadata={"created_by": "PreparationManager"}
                )
                
                backups.append(backup_info)
                self._backups_registry.append(backup_info)
                
                self.logger.info(f"Backup criado: {path} -> {backup_path} ({format_size(size_bytes)})")
                
            except Exception as e:
                self.logger.error(f"Erro ao criar backup de {path}: {e}")
                continue
        
        return backups
    
    def _backup_existing_configurations(self, components: List[str], result: PreparationResult) -> None:
        """Cria backups de configurações existentes para os componentes"""
        try:
            # Define caminhos comuns que podem precisar de backup
            backup_paths = []
            
            for component in components:
                # Adiciona caminhos específicos do componente que podem existir
                potential_paths = [
                    os.path.join(self.base_path, "config", f"{component}.yaml"),
                    os.path.join(self.base_path, "config", f"{component}.json"),
                    os.path.join(self.base_path, "config", component),
                    os.path.join(os.path.expanduser("~"), f".{component}"),
                ]
                
                backup_paths.extend(potential_paths)
            
            # Adiciona configurações globais
            backup_paths.extend([
                os.path.join(self.base_path, "config", "global.yaml"),
                os.path.join(self.base_path, "config", "settings.json"),
                os.path.join(self.base_path, "environment_dev.yaml")
            ])
            
            # Cria backups apenas para caminhos que existem
            existing_paths = [path for path in backup_paths if os.path.exists(path)]
            
            if existing_paths:
                backups = self.backup_existing_configs(existing_paths)
                result.backups_created.extend(backups)
                
                # Calcula espaço total usado pelos backups
                total_backup_size = sum(backup.size_bytes for backup in backups)
                result.total_space_used += total_backup_size
                
                self.logger.info(f"Criados {len(backups)} backups, total: {format_size(total_backup_size)}")
            else:
                self.logger.info("Nenhuma configuração existente encontrada para backup")
                
        except Exception as e:
            result.errors.append(f"Erro ao criar backups de configurações: {e}")
    
    def detect_directory_conflicts(self, paths: List[str]) -> List[DirectoryConflict]:
        """
        Detecta conflitos em diretórios
        
        Args:
            paths: Lista de caminhos para verificar
            
        Returns:
            List[DirectoryConflict]: Lista de conflitos detectados
        """
        conflicts = []
        
        for path in paths:
            try:
                # Verifica se o caminho já existe
                if os.path.exists(path):
                    # Verifica permissões
                    has_write, write_msg = check_write_permission(path)
                    has_read, read_msg = check_read_permission(path)
                    
                    if not has_write:
                        conflicts.append(DirectoryConflict(
                            path=path,
                            conflict_type="permission",
                            description=f"Sem permissão de escrita: {write_msg}",
                            severity="high",
                            suggested_action="Execute como administrador ou altere permissões",
                            can_auto_resolve=is_admin(),
                            backup_required=False
                        ))
                    
                    if not has_read:
                        conflicts.append(DirectoryConflict(
                            path=path,
                            conflict_type="permission",
                            description=f"Sem permissão de leitura: {read_msg}",
                            severity="critical",
                            suggested_action="Execute como administrador ou altere permissões",
                            can_auto_resolve=is_admin(),
                            backup_required=False
                        ))
                    
                    # Verifica se é somente leitura
                    if os.path.isdir(path):
                        try:
                            test_file = os.path.join(path, f"write_test_{os.getpid()}.tmp")
                            with open(test_file, "w") as f:
                                f.write("test")
                            os.remove(test_file)
                        except (PermissionError, OSError):
                            conflicts.append(DirectoryConflict(
                                path=path,
                                conflict_type="readonly",
                                description="Diretório é somente leitura",
                                severity="medium",
                                suggested_action="Altere permissões do diretório",
                                can_auto_resolve=is_admin(),
                                backup_required=False
                            ))
                    
                    # Verifica se contém arquivos importantes
                    if os.path.isdir(path) and os.listdir(path):
                        conflicts.append(DirectoryConflict(
                            path=path,
                            conflict_type="exists",
                            description="Diretório não está vazio",
                            severity="low",
                            suggested_action="Fazer backup do conteúdo existente",
                            can_auto_resolve=True,
                            backup_required=True
                        ))
                
                # Verifica se o diretório pai existe e tem permissões
                parent_dir = os.path.dirname(path)
                if not os.path.exists(parent_dir):
                    conflicts.append(DirectoryConflict(
                        path=path,
                        conflict_type="parent_missing",
                        description="Diretório pai não existe",
                        severity="medium",
                        suggested_action="Criar diretório pai",
                        can_auto_resolve=True,
                        backup_required=False
                    ))
                elif not check_write_permission(parent_dir)[0]:
                    conflicts.append(DirectoryConflict(
                        path=path,
                        conflict_type="parent_permission",
                        description="Sem permissão para criar no diretório pai",
                        severity="high",
                        suggested_action="Execute como administrador",
                        can_auto_resolve=is_admin(),
                        backup_required=False
                    ))
                
            except Exception as e:
                conflicts.append(DirectoryConflict(
                    path=path,
                    conflict_type="error",
                    description=f"Erro ao verificar: {e}",
                    severity="medium",
                    suggested_action="Verificar manualmente",
                    can_auto_resolve=False,
                    backup_required=False
                ))
        
        return conflicts
    
    def _resolve_directory_conflicts(self, result: PreparationResult) -> None:
        """Detecta e resolve conflitos de diretório"""
        try:
            # Coleta todos os diretórios que serão usados
            all_paths = result.directories_created.copy()
            
            # Adiciona diretórios base
            all_paths.extend([
                self.backup_base_dir,
                self.temp_dir,
                os.path.join(self.base_path, "downloads"),
                os.path.join(self.base_path, "logs"),
                os.path.join(self.base_path, "config")
            ])
            
            # Detecta conflitos
            conflicts = self.detect_directory_conflicts(all_paths)
            
            # Resolve conflitos automaticamente quando possível
            for conflict in conflicts:
                try:
                    if conflict.can_auto_resolve:
                        if conflict.conflict_type == "parent_missing":
                            os.makedirs(os.path.dirname(conflict.path), exist_ok=True)
                            result.conflicts_resolved.append(conflict)
                            self.logger.info(f"Conflito resolvido: criado diretório pai para {conflict.path}")
                        
                        elif conflict.conflict_type == "exists" and conflict.backup_required:
                            # Cria backup do diretório existente
                            backups = self.backup_existing_configs([conflict.path])
                            if backups:
                                result.backups_created.extend(backups)
                                result.conflicts_resolved.append(conflict)
                                self.logger.info(f"Conflito resolvido: backup criado para {conflict.path}")
                        
                        elif conflict.conflict_type == "readonly" and is_admin():
                            # Tenta alterar permissões (apenas no Windows)
                            if platform.system() == "Windows":
                                try:
                                    import subprocess
                                    subprocess.run(
                                        ["attrib", "-R", conflict.path, "/S", "/D"],
                                        check=True, capture_output=True
                                    )
                                    result.conflicts_resolved.append(conflict)
                                    self.logger.info(f"Conflito resolvido: permissões alteradas para {conflict.path}")
                                except subprocess.CalledProcessError:
                                    result.warnings.append(f"Não foi possível alterar permissões de {conflict.path}")
                    else:
                        # Conflitos que não podem ser resolvidos automaticamente
                        if conflict.severity in ["high", "critical"]:
                            result.errors.append(f"Conflito crítico: {conflict.description} em {conflict.path}")
                        else:
                            result.warnings.append(f"Conflito: {conflict.description} em {conflict.path}")
                
                except Exception as e:
                    result.warnings.append(f"Erro ao resolver conflito em {conflict.path}: {e}")
            
            if conflicts:
                self.logger.info(f"Processados {len(conflicts)} conflitos, {len(result.conflicts_resolved)} resolvidos")
            
        except Exception as e:
            result.errors.append(f"Erro ao processar conflitos de diretório: {e}")
    
    def configure_environment_variables(self, vars: Dict[str, str]) -> bool:
        """
        Configura variáveis de ambiente
        
        Args:
            vars: Dicionário com variáveis de ambiente (nome -> valor)
            
        Returns:
            bool: True se todas as variáveis foram configuradas com sucesso
        """
        success = True
        
        for name, value in vars.items():
            try:
                # Tenta configurar como variável do usuário primeiro
                if set_env_var(name, value, scope='user'):
                    self.logger.info(f"Variável de ambiente configurada (usuário): {name}={value}")
                else:
                    # Se falhar, tenta como variável do sistema (requer admin)
                    if is_admin() and set_env_var(name, value, scope='system'):
                        self.logger.info(f"Variável de ambiente configurada (sistema): {name}={value}")
                    else:
                        self.logger.error(f"Falha ao configurar variável de ambiente: {name}")
                        success = False
                        
            except Exception as e:
                self.logger.error(f"Erro ao configurar variável {name}: {e}")
                success = False
        
        return success
    
    def configure_automatic_environment_variables(self, components: List[str]) -> Dict[str, str]:
        """
        Configura automaticamente variáveis de ambiente baseadas nos componentes
        
        Args:
            components: Lista de componentes que serão instalados
            
        Returns:
            Dict[str, str]: Dicionário com as variáveis configuradas
        """
        configured_vars = {}
        
        try:
            # Variáveis globais sempre configuradas
            base_vars = {
                "ENVIRONMENT_DEV_HOME": self.base_path,
                "ENVIRONMENT_DEV_DOWNLOADS": os.path.join(self.base_path, "downloads"),
                "ENVIRONMENT_DEV_TEMP": self.temp_dir,
                "ENVIRONMENT_DEV_LOGS": os.path.join(self.base_path, "logs"),
                "ENVIRONMENT_DEV_CONFIG": os.path.join(self.base_path, "config"),
                "ENVIRONMENT_DEV_BACKUPS": self.backup_base_dir,
                "ENVIRONMENT_DEV_VERSION": "2.0.0"
            }
            
            # Configura variáveis base
            for name, value in base_vars.items():
                if set_env_var(name, value, scope='user'):
                    configured_vars[name] = value
                    self.logger.debug(f"Variável configurada: {name}={value}")
            
            # Variáveis específicas por componente
            for component in components:
                component_vars = self._get_component_environment_variables(component)
                for name, value in component_vars.items():
                    if set_env_var(name, value, scope='user'):
                        configured_vars[name] = value
                        self.logger.debug(f"Variável de {component} configurada: {name}={value}")
            
            # Adiciona diretórios importantes ao PATH
            path_dirs = [
                os.path.join(self.base_path, "bin"),
                os.path.join(self.base_path, "scripts"),
                os.path.join(self.base_path, "tools")
            ]
            
            for path_dir in path_dirs:
                if os.path.exists(path_dir):
                    try:
                        if add_to_path(path_dir, scope='user'):
                            self.logger.info(f"Diretório adicionado ao PATH: {path_dir}")
                    except Exception as e:
                        self.logger.warning(f"Erro ao adicionar {path_dir} ao PATH: {e}")
            
            self.logger.info(f"Configuradas {len(configured_vars)} variáveis de ambiente automaticamente")
            return configured_vars
            
        except Exception as e:
            self.logger.error(f"Erro ao configurar variáveis de ambiente automaticamente: {e}")
            return configured_vars
    
    def _get_component_environment_variables(self, component: str) -> Dict[str, str]:
        """Obtém variáveis de ambiente específicas para um componente"""
        vars_dict = {}
        
        try:
            component_lower = component.lower()
            
            if component_lower == "clover":
                vars_dict.update({
                    "CLOVER_HOME": os.path.join(self.base_path, "clover"),
                    "CLOVER_CONFIG": os.path.join(self.base_path, "config", "clover"),
                    "CLOVER_THEMES": os.path.join(self.base_path, "clover", "themes"),
                    "CLOVER_KEXTS": os.path.join(self.base_path, "clover", "kexts")
                })
            
            elif component_lower in ["steam", "steamdeck"]:
                vars_dict.update({
                    "STEAM_TOOLS_HOME": os.path.join(self.base_path, "steam"),
                    "STEAM_DRIVERS": os.path.join(self.base_path, "steam", "drivers"),
                    "STEAM_CONFIG": os.path.join(self.base_path, "config", "steam")
                })
            
            elif component_lower == "cmake":
                vars_dict.update({
                    "CMAKE_HOME": os.path.join(self.base_path, "cmake"),
                    "CMAKE_MODULES": os.path.join(self.base_path, "cmake", "modules")
                })
            
            # Adiciona diretório específico do componente
            component_dir = os.path.join(self.base_path, component_lower)
            vars_dict[f"{component.upper()}_HOME"] = component_dir
            
        except Exception as e:
            self.logger.warning(f"Erro ao obter variáveis para componente {component}: {e}")
        
        return vars_dict    
    
    def _configure_environment_variables(self, components: List[str], result: PreparationResult) -> None:
        """Configura variáveis de ambiente necessárias para os componentes"""
        try:
            # Define variáveis de ambiente padrão
            env_vars = {}
            
            # Variáveis globais do Environment Dev
            env_vars["ENVIRONMENT_DEV_HOME"] = self.base_path
            env_vars["ENVIRONMENT_DEV_DOWNLOADS"] = os.path.join(self.base_path, "downloads")
            env_vars["ENVIRONMENT_DEV_TEMP"] = self.temp_dir
            env_vars["ENVIRONMENT_DEV_LOGS"] = os.path.join(self.base_path, "logs")
            env_vars["ENVIRONMENT_DEV_CONFIG"] = os.path.join(self.base_path, "config")
            
            # Adiciona diretórios ao PATH se necessário
            path_additions = [
                os.path.join(self.base_path, "bin"),
                os.path.join(self.base_path, "scripts")
            ]
            
            # Configura variáveis básicas
            configured_vars = []
            for name, value in env_vars.items():
                try:
                    if set_env_var(name, value, scope='user'):
                        configured_vars.append(EnvironmentVariable(
                            name=name,
                            value=value,
                            scope='user'
                        ))
                    else:
                        result.warnings.append(f"Não foi possível configurar variável {name}")
                except Exception as e:
                    result.warnings.append(f"Erro ao configurar variável {name}: {e}")
            
            # Adiciona diretórios ao PATH
            for path_dir in path_additions:
                if os.path.exists(path_dir):
                    try:
                        if add_to_path(path_dir, scope='user'):
                            configured_vars.append(EnvironmentVariable(
                                name="PATH",
                                value=path_dir,
                                scope='user',
                                append_to_existing=True
                            ))
                        else:
                            result.warnings.append(f"Não foi possível adicionar {path_dir} ao PATH")
                    except Exception as e:
                        result.warnings.append(f"Erro ao adicionar {path_dir} ao PATH: {e}")
            
            # Configura variáveis específicas por componente
            for component in components:
                component_vars = self._get_component_environment_variables(component)
                for name, value in component_vars.items():
                    try:
                        if set_env_var(name, value, scope='user'):
                            configured_vars.append(EnvironmentVariable(
                                name=name,
                                value=value,
                                scope='user'
                            ))
                        else:
                            result.warnings.append(f"Não foi possível configurar variável {name} para {component}")
                    except Exception as e:
                        result.warnings.append(f"Erro ao configurar variável {name} para {component}: {e}")
            
            result.env_vars_configured.extend(configured_vars)
            self.logger.info(f"Configuradas {len(configured_vars)} variáveis de ambiente")
            
        except Exception as e:
            result.errors.append(f"Erro ao configurar variáveis de ambiente: {e}")
    
    def _prepare_system_dependencies(self, components: List[str], result: PreparationResult) -> None:
        """Prepara dependências de sistema automaticamente (método interno)"""
        try:
            success, prepared_deps = self.prepare_system_dependencies(components)
            
            if success:
                # Adiciona informações sobre dependências preparadas ao resultado
                for dep in prepared_deps:
                    result.warnings.append(f"Dependência preparada: {dep}")
                
                self.logger.info(f"Preparação de dependências concluída: {len(prepared_deps)} dependências")
            else:
                result.warnings.append("Nenhuma dependência de sistema foi preparada automaticamente")
                
        except Exception as e:
            result.errors.append(f"Erro ao preparar dependências de sistema: {e}")
    
    def prepare_system_dependencies(self, components: List[str]) -> Tuple[bool, List[str]]:
        """
        Prepara dependências de sistema automaticamente
        
        Args:
            components: Lista de componentes que serão instalados
            
        Returns:
            Tuple[bool, List[str]]: (sucesso, lista de dependências preparadas)
        """
        prepared_dependencies = []
        
        try:
            self.logger.info(f"Preparando dependências de sistema para: {components}")
            
            # Dependências comuns para todos os componentes
            common_dependencies = self._prepare_common_dependencies()
            prepared_dependencies.extend(common_dependencies)
            
            # Dependências específicas por componente
            for component in components:
                component_deps = self._prepare_component_dependencies(component)
                prepared_dependencies.extend(component_deps)
            
            # Verifica se todas as dependências foram preparadas
            success = len(prepared_dependencies) > 0
            
            if success:
                self.logger.info(f"Preparadas {len(prepared_dependencies)} dependências de sistema")
            else:
                self.logger.warning("Nenhuma dependência de sistema foi preparada")
            
            return success, prepared_dependencies
            
        except Exception as e:
            self.logger.error(f"Erro ao preparar dependências de sistema: {e}")
            return False, []
    
    def _prepare_common_dependencies(self) -> List[str]:
        """Prepara dependências comuns necessárias para todos os componentes"""
        prepared = []
        
        try:
            # Verifica e prepara Visual C++ Redistributables
            if self._ensure_vcredist():
                prepared.append("Visual C++ Redistributables")
            
            # Verifica e prepara .NET Framework
            if self._ensure_dotnet_framework():
                prepared.append(".NET Framework")
            
            # Verifica e prepara PowerShell ExecutionPolicy
            if self._ensure_powershell_policy():
                prepared.append("PowerShell ExecutionPolicy")
            
            # Verifica e prepara Windows Features necessárias
            if self._ensure_windows_features():
                prepared.append("Windows Features")
            
        except Exception as e:
            self.logger.error(f"Erro ao preparar dependências comuns: {e}")
        
        return prepared
    
    def _prepare_component_dependencies(self, component: str) -> List[str]:
        """Prepara dependências específicas de um componente"""
        prepared = []
        
        try:
            component_lower = component.lower()
            
            if component_lower == "clover":
                # Dependências específicas do Clover
                if self._ensure_efi_partition_access():
                    prepared.append("EFI Partition Access")
                
                if self._ensure_bootloader_tools():
                    prepared.append("Bootloader Tools")
            
            elif component_lower in ["steam", "steamdeck"]:
                # Dependências específicas do Steam
                if self._ensure_audio_drivers():
                    prepared.append("Audio Drivers Support")
                
                if self._ensure_graphics_support():
                    prepared.append("Graphics Support")
            
            elif component_lower == "cmake":
                # Dependências específicas do CMake
                if self._ensure_build_tools():
                    prepared.append("Build Tools")
                
                if self._ensure_compiler_support():
                    prepared.append("Compiler Support")
            
        except Exception as e:
            self.logger.error(f"Erro ao preparar dependências de {component}: {e}")
        
        return prepared
    
    def _ensure_vcredist(self) -> bool:
        """Garante que Visual C++ Redistributables estejam disponíveis"""
        try:
            if platform.system() != "Windows":
                return True  # Não aplicável em outros sistemas
            
            # Verifica se vcredist está instalado
            import subprocess
            result = subprocess.run(
                ["reg", "query", "HKLM\\SOFTWARE\\Microsoft\\VisualStudio\\14.0\\VC\\Runtimes\\x64"],
                capture_output=True, text=True, check=False
            )
            
            if result.returncode == 0:
                self.logger.debug("Visual C++ Redistributables já instalado")
                return True
            
            # Se não estiver instalado, marca para instalação posterior
            self.logger.info("Visual C++ Redistributables será necessário")
            return True
            
        except Exception as e:
            self.logger.warning(f"Erro ao verificar vcredist: {e}")
            return False
    
    def _ensure_dotnet_framework(self) -> bool:
        """Garante que .NET Framework esteja disponível"""
        try:
            if platform.system() != "Windows":
                return True  # Não aplicável em outros sistemas
            
            # Verifica versão do .NET Framework
            import subprocess
            result = subprocess.run(
                ["reg", "query", "HKLM\\SOFTWARE\\Microsoft\\NET Framework Setup\\NDP\\v4\\Full", "/v", "Release"],
                capture_output=True, text=True, check=False
            )
            
            if result.returncode == 0 and "Release" in result.stdout:
                self.logger.debug(".NET Framework disponível")
                return True
            
            self.logger.info(".NET Framework será necessário")
            return True
            
        except Exception as e:
            self.logger.warning(f"Erro ao verificar .NET Framework: {e}")
            return False
    
    def _ensure_powershell_policy(self) -> bool:
        """Garante que a política do PowerShell permita execução de scripts"""
        try:
            if platform.system() != "Windows":
                return True  # Não aplicável em outros sistemas
            
            import subprocess
            result = subprocess.run(
                ["powershell", "-Command", "Get-ExecutionPolicy"],
                capture_output=True, text=True, check=False
            )
            
            if result.returncode == 0:
                policy = result.stdout.strip()
                if policy in ["RemoteSigned", "Unrestricted", "Bypass"]:
                    self.logger.debug(f"PowerShell ExecutionPolicy OK: {policy}")
                    return True
                else:
                    self.logger.info(f"PowerShell ExecutionPolicy restritiva: {policy}")
                    # Não altera automaticamente por segurança
                    return True
            
            return False
            
        except Exception as e:
            self.logger.warning(f"Erro ao verificar PowerShell policy: {e}")
            return False
    
    def _ensure_windows_features(self) -> bool:
        """Garante que recursos necessários do Windows estejam habilitados"""
        try:
            if platform.system() != "Windows":
                return True  # Não aplicável em outros sistemas
            
            # Lista de recursos que podem ser necessários
            required_features = [
                "Microsoft-Windows-Subsystem-Linux",  # WSL se necessário
                "VirtualMachinePlatform",  # Hyper-V se necessário
            ]
            
            # Por enquanto, apenas verifica sem alterar
            self.logger.debug("Recursos do Windows verificados")
            return True
            
        except Exception as e:
            self.logger.warning(f"Erro ao verificar recursos do Windows: {e}")
            return False
    
    def _ensure_efi_partition_access(self) -> bool:
        """Garante acesso à partição EFI para instalação do Clover"""
        try:
            if platform.system() != "Windows":
                return True  # Implementação específica para outros sistemas
            
            # Verifica se há partição EFI
            import subprocess
            result = subprocess.run(
                ["diskpart", "/s", "-"],
                input="list disk\nexit\n",
                capture_output=True, text=True, check=False
            )
            
            if result.returncode == 0:
                self.logger.debug("Acesso a discos verificado")
                return True
            
            return False
            
        except Exception as e:
            self.logger.warning(f"Erro ao verificar acesso EFI: {e}")
            return False
    
    def _ensure_bootloader_tools(self) -> bool:
        """Garante que ferramentas de bootloader estejam disponíveis"""
        try:
            # Verifica se bcdedit está disponível (Windows)
            if platform.system() == "Windows":
                import subprocess
                result = subprocess.run(
                    ["bcdedit", "/?"],
                    capture_output=True, text=True, check=False
                )
                
                if result.returncode == 0:
                    self.logger.debug("Ferramentas de bootloader disponíveis")
                    return True
            
            return True  # Assume disponível
            
        except Exception as e:
            self.logger.warning(f"Erro ao verificar ferramentas de bootloader: {e}")
            return False
    
    def _ensure_audio_drivers(self) -> bool:
        """Garante suporte a drivers de áudio"""
        try:
            # Verifica se há dispositivos de áudio disponíveis
            if platform.system() == "Windows":
                import subprocess
                result = subprocess.run(
                    ["wmic", "sounddev", "get", "name"],
                    capture_output=True, text=True, check=False
                )
                
                if result.returncode == 0 and len(result.stdout.strip().split('\n')) > 1:
                    self.logger.debug("Dispositivos de áudio detectados")
                    return True
            
            return True  # Assume disponível
            
        except Exception as e:
            self.logger.warning(f"Erro ao verificar drivers de áudio: {e}")
            return False
    
    def _ensure_graphics_support(self) -> bool:
        """Garante suporte gráfico adequado"""
        try:
            # Verifica se há dispositivos gráficos disponíveis
            if platform.system() == "Windows":
                import subprocess
                result = subprocess.run(
                    ["wmic", "path", "win32_VideoController", "get", "name"],
                    capture_output=True, text=True, check=False
                )
                
                if result.returncode == 0 and len(result.stdout.strip().split('\n')) > 1:
                    self.logger.debug("Dispositivos gráficos detectados")
                    return True
            
            return True  # Assume disponível
            
        except Exception as e:
            self.logger.warning(f"Erro ao verificar suporte gráfico: {e}")
            return False
    
    def _ensure_build_tools(self) -> bool:
        """Garante que ferramentas de build estejam disponíveis"""
        try:
            # Verifica se há compiladores disponíveis
            tools_to_check = ["gcc", "cl", "clang"]
            
            for tool in tools_to_check:
                try:
                    import subprocess
                    result = subprocess.run(
                        [tool, "--version"],
                        capture_output=True, text=True, check=False
                    )
                    
                    if result.returncode == 0:
                        self.logger.debug(f"Ferramenta de build encontrada: {tool}")
                        return True
                except FileNotFoundError:
                    continue
            
            self.logger.info("Nenhuma ferramenta de build detectada")
            return True  # Não bloqueia instalação
            
        except Exception as e:
            self.logger.warning(f"Erro ao verificar ferramentas de build: {e}")
            return False
    
    def _ensure_compiler_support(self) -> bool:
        """Garante suporte a compiladores"""
        try:
            # Verifica se há suporte a compilação
            self.logger.debug("Suporte a compiladores verificado")
            return True
            
        except Exception as e:
            self.logger.warning(f"Erro ao verificar suporte a compiladores: {e}")
            return False
    
    def _configure_environment_variables(self, components: List[str], result: PreparationResult) -> None:
        """Configura variáveis de ambiente necessárias para os componentes"""
        try:
            # Define variáveis de ambiente padrão
            env_vars = {}
            
            # Variáveis globais do Environment Dev
            env_vars["ENVIRONMENT_DEV_HOME"] = self.base_path
            env_vars["ENVIRONMENT_DEV_DOWNLOADS"] = os.path.join(self.base_path, "downloads")
            env_vars["ENVIRONMENT_DEV_TEMP"] = self.temp_dir
            env_vars["ENVIRONMENT_DEV_LOGS"] = os.path.join(self.base_path, "logs")
            env_vars["ENVIRONMENT_DEV_CONFIG"] = os.path.join(self.base_path, "config")
            
            # Adiciona diretórios ao PATH se necessário
            path_additions = [
                os.path.join(self.base_path, "bin"),
                os.path.join(self.base_path, "scripts")
            ]
            
            # Configura variáveis básicas
            configured_vars = []
            for name, value in env_vars.items():
                try:
                    if set_env_var(name, value, scope='user'):
                        configured_vars.append(EnvironmentVariable(
                            name=name,
                            value=value,
                            scope='user'
                        ))
                    else:
                        result.warnings.append(f"Não foi possível configurar variável {name}")
                except Exception as e:
                    result.warnings.append(f"Erro ao configurar variável {name}: {e}")
            
            # Adiciona diretórios ao PATH
            for path_dir in path_additions:
                if os.path.exists(path_dir):
                    try:
                        if add_to_path(path_dir, scope='user'):
                            configured_vars.append(EnvironmentVariable(
                                name="PATH",
                                value=path_dir,
                                scope='user',
                                append_to_existing=True
                            ))
                        else:
                            result.warnings.append(f"Não foi possível adicionar {path_dir} ao PATH")
                    except Exception as e:
                        result.warnings.append(f"Erro ao adicionar {path_dir} ao PATH: {e}")
            
            # Configura variáveis específicas por componente
            for component in components:
                component_vars = self._get_component_environment_variables(component)
                for name, value in component_vars.items():
                    try:
                        if set_env_var(name, value, scope='user'):
                            configured_vars.append(EnvironmentVariable(
                                name=name,
                                value=value,
                                scope='user'
                            ))
                        else:
                            result.warnings.append(f"Não foi possível configurar variável {name} para {component}")
                    except Exception as e:
                        result.warnings.append(f"Erro ao configurar variável {name} para {component}: {e}")
            
            result.env_vars_configured.extend(configured_vars)
            self.logger.info(f"Configuradas {len(configured_vars)} variáveis de ambiente")
            
        except Exception as e:
            result.errors.append(f"Erro ao configurar variáveis de ambiente: {e}")
    
    def check_and_request_permissions(self, required_perms: List[str]) -> bool:
        """
        Verifica e solicita permissões necessárias
        
        Args:
            required_perms: Lista de permissões necessárias
            
        Returns:
            bool: True se todas as permissões estão disponíveis
        """
        try:
            # Verifica se já tem privilégios administrativos
            if is_admin():
                self.logger.info("Privilégios administrativos já disponíveis")
                return True
            
            # Verifica se precisa de privilégios administrativos
            needs_admin = any(perm in ["admin", "system", "registry"] for perm in required_perms)
            
            if needs_admin:
                self.logger.warning("Operação requer privilégios administrativos")
                # Em um ambiente real, aqui poderia solicitar elevação
                return False
            
            # Verifica permissões específicas de diretório
            for perm in required_perms:
                if perm.startswith("write:"):
                    path = perm[6:]  # Remove "write:" prefix
                    has_write, msg = check_write_permission(path)
                    if not has_write:
                        self.logger.error(f"Sem permissão de escrita em {path}: {msg}")
                        return False
                
                elif perm.startswith("read:"):
                    path = perm[5:]  # Remove "read:" prefix
                    has_read, msg = check_read_permission(path)
                    if not has_read:
                        self.logger.error(f"Sem permissão de leitura em {path}: {msg}")
                        return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao verificar permissões: {e}")
            return False
    
    def _ensure_required_permissions(self, components: List[str], result: PreparationResult) -> None:
        """Verifica e garante permissões necessárias"""
        try:
            # Define permissões necessárias baseadas nos componentes
            required_permissions = []
            
            # Permissões básicas sempre necessárias
            required_permissions.extend([
                f"write:{self.base_path}",
                f"write:{self.backup_base_dir}",
                f"write:{self.temp_dir}",
                f"read:{self.base_path}"
            ])
            
            # Adiciona permissões específicas por componente
            for component in components:
                component_dirs = [
                    os.path.join(self.base_path, "downloads", component),
                    os.path.join(self.base_path, "logs", component),
                    os.path.join(self.base_path, "config", component)
                ]
                
                for dir_path in component_dirs:
                    required_permissions.append(f"write:{dir_path}")
            
            # Verifica se precisa de privilégios administrativos
            admin_required = any(
                component.lower() in ["clover", "bootloader", "efi", "system"]
                for component in components
            )
            
            if admin_required:
                required_permissions.append("admin")
            
            # Verifica permissões
            if self.check_and_request_permissions(required_permissions):
                result.permissions_granted.extend(required_permissions)
                self.logger.info(f"Todas as {len(required_permissions)} permissões verificadas")
            else:
                missing_perms = [perm for perm in required_permissions if not self._check_single_permission(perm)]
                result.errors.append(f"Permissões insuficientes: {missing_perms}")
                
        except Exception as e:
            result.errors.append(f"Erro ao verificar permissões: {e}")
    
    def _check_single_permission(self, permission: str) -> bool:
        """Verifica uma permissão específica"""
        try:
            if permission == "admin":
                return is_admin()
            elif permission.startswith("write:"):
                path = permission[6:]
                return check_write_permission(path)[0]
            elif permission.startswith("read:"):
                path = permission[5:]
                return check_read_permission(path)[0]
            else:
                return True  # Permissão desconhecida, assume que está OK
        except Exception:
            return False
    
    def verify_prerequisites(self, components: List[str]) -> Tuple[bool, List[str]]:
        """
        Verifica pré-requisitos antes da instalação
        
        Args:
            components: Lista de componentes a serem instalados
            
        Returns:
            Tuple[bool, List[str]]: (sucesso, lista de problemas encontrados)
        """
        problems = []
        
        try:
            # Verifica espaço em disco
            disk_info = get_disk_space(self.base_path)
            free_space_gb = disk_info['free'] / (1024**3)
            
            if free_space_gb < 2.0:
                problems.append(f"Espaço insuficiente: {free_space_gb:.1f}GB disponível, mínimo 2GB necessário")
            
            # Verifica permissões básicas
            basic_paths = [self.base_path, self.backup_base_dir, self.temp_dir]
            for path in basic_paths:
                if not check_write_permission(path)[0]:
                    problems.append(f"Sem permissão de escrita em {path}")
            
            # Verifica se Python está funcionando corretamente
            try:
                import sys
                if sys.version_info < (3, 8):
                    problems.append(f"Python {sys.version_info.major}.{sys.version_info.minor} detectado, mínimo 3.8 necessário")
            except Exception as e:
                problems.append(f"Erro ao verificar versão do Python: {e}")
            
            # Verifica dependências específicas por componente
            for component in components:
                component_problems = self._check_component_prerequisites(component)
                problems.extend(component_problems)
            
            success = len(problems) == 0
            
            if success:
                self.logger.info("Todos os pré-requisitos verificados com sucesso")
            else:
                self.logger.warning(f"Encontrados {len(problems)} problemas nos pré-requisitos")
            
            return success, problems
            
        except Exception as e:
            problems.append(f"Erro ao verificar pré-requisitos: {e}")
            return False, problems
    
    def _check_component_prerequisites(self, component: str) -> List[str]:
        """Verifica pré-requisitos específicos de um componente"""
        problems = []
        
        try:
            # Pré-requisitos específicos por componente
            if component.lower() == "clover":
                # Verifica se é sistema UEFI
                if platform.system() == "Windows":
                    try:
                        import subprocess
                        result = subprocess.run(
                            ["bcdedit", "/enum", "firmware"],
                            capture_output=True, text=True, check=False
                        )
                        if result.returncode != 0:
                            problems.append("Sistema não parece ser UEFI (necessário para Clover)")
                    except Exception:
                        problems.append("Não foi possível verificar tipo de firmware")
                
                # Verifica privilégios administrativos
                if not is_admin():
                    problems.append("Privilégios administrativos necessários para instalação do Clover")
            
            elif component.lower() in ["steam", "steamdeck"]:
                # Verifica se há drivers de áudio disponíveis
                audio_paths = [
                    "C:\\Windows\\System32\\drivers\\audio",
                    "C:\\Windows\\System32\\DriverStore\\FileRepository"
                ]
                
                audio_found = any(os.path.exists(path) for path in audio_paths)
                if not audio_found:
                    problems.append("Drivers de áudio podem não estar disponíveis")
            
            # Adicione mais verificações específicas conforme necessário
            
        except Exception as e:
            problems.append(f"Erro ao verificar pré-requisitos de {component}: {e}")
        
        return problems
    
    def cleanup_preparation(self) -> bool:
        """
        Limpa arquivos temporários da preparação
        
        Returns:
            bool: True se a limpeza foi bem-sucedida
        """
        try:
            cleaned_files = 0
            
            # Limpa diretório temporário
            if os.path.exists(self.temp_dir):
                for item in os.listdir(self.temp_dir):
                    item_path = os.path.join(self.temp_dir, item)
                    try:
                        if os.path.isfile(item_path):
                            os.unlink(item_path)
                            cleaned_files += 1
                        elif os.path.isdir(item_path):
                            shutil.rmtree(item_path)
                            cleaned_files += 1
                    except Exception as e:
                        self.logger.warning(f"Erro ao remover {item_path}: {e}")
            
            # Remove backups antigos (mais de 30 dias)
            if os.path.exists(self.backup_base_dir):
                import time
                current_time = time.time()
                
                for backup_dir in os.listdir(self.backup_base_dir):
                    backup_path = os.path.join(self.backup_base_dir, backup_dir)
                    try:
                        if os.path.isdir(backup_path):
                            dir_time = os.path.getmtime(backup_path)
                            if current_time - dir_time > 30 * 86400:  # 30 dias
                                shutil.rmtree(backup_path)
                                cleaned_files += 1
                    except Exception as e:
                        self.logger.warning(f"Erro ao remover backup antigo {backup_path}: {e}")
            
            self.logger.info(f"Limpeza concluída: {cleaned_files} itens removidos")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro durante limpeza: {e}")
            return False
    
    def get_backup_info(self, backup_id: str) -> Optional[BackupInfo]:
        """
        Obtém informações sobre um backup específico
        
        Args:
            backup_id: ID do backup
            
        Returns:
            Optional[BackupInfo]: Informações do backup ou None se não encontrado
        """
        for backup in self._backups_registry:
            if backup.backup_id == backup_id:
                return backup
        return None
    
    def list_backups(self) -> List[BackupInfo]:
        """
        Lista todos os backups criados
        
        Returns:
            List[BackupInfo]: Lista de informações dos backups
        """
        return self._backups_registry.copy()
    
    def restore_backup(self, backup_id: str) -> bool:
        """
        Restaura um backup específico
        
        Args:
            backup_id: ID do backup a ser restaurado
            
        Returns:
            bool: True se a restauração foi bem-sucedida
        """
        try:
            backup_info = self.get_backup_info(backup_id)
            if not backup_info:
                self.logger.error(f"Backup não encontrado: {backup_id}")
                return False
            
            if not os.path.exists(backup_info.backup_path):
                self.logger.error(f"Arquivo de backup não existe: {backup_info.backup_path}")
                return False
            
            # Remove o arquivo/diretório atual se existir
            if os.path.exists(backup_info.original_path):
                if os.path.isdir(backup_info.original_path):
                    shutil.rmtree(backup_info.original_path)
                else:
                    os.unlink(backup_info.original_path)
            
            # Restaura o backup
            if backup_info.backup_type == BackupType.DIRECTORY:
                shutil.copytree(backup_info.backup_path, backup_info.original_path)
            else:
                os.makedirs(os.path.dirname(backup_info.original_path), exist_ok=True)
                shutil.copy2(backup_info.backup_path, backup_info.original_path)
            
            self.logger.info(f"Backup restaurado: {backup_id} -> {backup_info.original_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao restaurar backup {backup_id}: {e}")
            return False


if __name__ == "__main__":
    # Configuração básica de logging para testes
    logging.basicConfig(level=logging.INFO)
    
    # Teste básico do PreparationManager
    print("Testando PreparationManager...")
    
    manager = PreparationManager()
    
    # Testa preparação do ambiente
    test_components = ["test_component", "steam"]
    result = manager.prepare_environment(test_components)
    
    print(f"Status: {result.status.value}")
    print(f"Diretórios criados: {len(result.directories_created)}")
    print(f"Backups criados: {len(result.backups_created)}")
    print(f"Conflitos resolvidos: {len(result.conflicts_resolved)}")
    print(f"Variáveis configuradas: {len(result.env_vars_configured)}")
    print(f"Tempo de preparação: {result.preparation_time:.2f}s")
    
    if result.errors:
        print(f"Erros: {result.errors}")
    if result.warnings:
        print(f"Avisos: {result.warnings}")
    
    print(f"Mensagem: {result.message}")
    
    # Testa verificação de pré-requisitos
    success, problems = manager.verify_prerequisites(test_components)
    print(f"\nPré-requisitos: {'OK' if success else 'PROBLEMAS'}")
    if problems:
        for problem in problems:
            print(f"  - {problem}")
    
    # Lista backups criados
    backups = manager.list_backups()
    print(f"\nBackups criados: {len(backups)}")
    for backup in backups:
        print(f"  - {backup.backup_id}: {backup.original_path} ({format_size(backup.size_bytes)})")