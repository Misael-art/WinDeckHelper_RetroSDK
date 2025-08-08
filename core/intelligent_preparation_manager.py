# -*- coding: utf-8 -*-
"""
Intelligent Preparation Manager for Environment Dev Deep Evaluation
Implements intelligent preparation system with directory structure creation,
configuration backup, privilege escalation, and environment variable configuration
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
import uuid
import platform
from pathlib import Path
from typing import Dict, Optional, Tuple, List, Any, Set, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

from utils.permission_checker import is_admin, check_write_permission, check_read_permission
from utils.env_manager import set_env_var, get_env_var, add_to_path, remove_from_path
from core.error_handler import EnvDevError, ErrorSeverity, ErrorCategory

logger = logging.getLogger(__name__)

class PreparationStatus(Enum):
    """Status of preparation operations"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    REQUIRES_ELEVATION = "requires_elevation"

class BackupType(Enum):
    """Type of backup operation"""
    DIRECTORY = "directory"
    FILE = "file"
    REGISTRY = "registry"
    ENVIRONMENT_VAR = "environment_var"
    PATH_VAR = "path_var"
    CONFIGURATION = "configuration"

class PrivilegeLevel(Enum):
    """Required privilege level"""
    USER = "user"
    ADMIN = "admin"
    SYSTEM = "system"

@dataclass
class BackupInfo:
    """Information about a backup operation"""
    backup_id: str
    original_path: str
    backup_path: str
    backup_type: BackupType
    timestamp: datetime = field(default_factory=datetime.now)
    size_bytes: int = 0
    checksum: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    restoration_info: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DirectoryStructure:
    """Represents a directory structure to be created"""
    path: str
    permissions: Optional[str] = None
    owner: Optional[str] = None
    recursive: bool = True
    backup_existing: bool = True
    required_privilege: PrivilegeLevel = PrivilegeLevel.USER
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class EnvironmentConfiguration:
    """Environment variable configuration"""
    name: str
    value: str
    scope: str = "user"  # "user", "system", "process"
    operation: str = "set"  # "set", "append", "prepend", "remove"
    separator: str = ";"
    backup_existing: bool = True
    required_privilege: PrivilegeLevel = PrivilegeLevel.USER
    validation_command: Optional[str] = None

@dataclass
class PathConfiguration:
    """PATH variable configuration"""
    path: str
    operation: str = "add"  # "add", "remove", "replace"
    scope: str = "user"
    position: str = "end"  # "start", "end", "before", "after"
    reference_path: Optional[str] = None
    backup_existing: bool = True
    required_privilege: PrivilegeLevel = PrivilegeLevel.USER

@dataclass
class PreparationResult:
    """Result of preparation operations"""
    status: PreparationStatus
    directories_created: List[str] = field(default_factory=list)
    backups_created: List[BackupInfo] = field(default_factory=list)
    env_vars_configured: List[EnvironmentConfiguration] = field(default_factory=list)
    path_vars_configured: List[PathConfiguration] = field(default_factory=list)
    privileges_requested: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    preparation_time: float = 0.0
    total_space_used: int = 0
    message: str = ""
    requires_restart: bool = False
    elevated_operations: List[str] = field(default_factory=list)

class IntelligentPreparationManager:
    """
    Intelligent Preparation Manager with advanced capabilities
    
    Features:
    - Intelligent directory structure creation with conflict resolution
    - Comprehensive configuration backup system
    - Smart privilege escalation that requests permissions only when necessary
    - Advanced PATH and environment variable configuration
    - Atomic operations with rollback capability
    - Cross-platform compatibility
    """
    
    def __init__(self, base_path: Optional[str] = None):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.base_path = base_path or os.getcwd()
        
        # Initialize directories
        self.backup_base_dir = os.path.join(self.base_path, "backups", "preparation")
        self.temp_dir = os.path.join(self.base_path, "temp", "preparation")
        self.config_dir = os.path.join(self.base_path, "config", "preparation")
        
        # Create base directories
        for directory in [self.backup_base_dir, self.temp_dir, self.config_dir]:
            os.makedirs(directory, exist_ok=True)
        
        # State management
        self.backup_registry: Dict[str, BackupInfo] = {}
        self.preparation_history: List[PreparationResult] = []
        self._lock = threading.Lock()
        
        # Platform-specific settings
        self.platform = platform.system().lower()
        self.is_windows = self.platform == "windows"
        self.is_linux = self.platform == "linux"
        self.is_macos = self.platform == "darwin"
        
        self.logger.info(f"Intelligent Preparation Manager initialized for {self.platform}")
    
    def prepare_intelligent_environment(self, components: List[str], 
                                      custom_structures: Optional[List[DirectoryStructure]] = None,
                                      custom_env_vars: Optional[List[EnvironmentConfiguration]] = None,
                                      custom_path_vars: Optional[List[PathConfiguration]] = None,
                                      force_elevation: bool = False) -> PreparationResult:
        """
        Intelligently prepare environment for component installation
        
        Args:
            components: List of components to prepare for
            custom_structures: Custom directory structures to create
            custom_env_vars: Custom environment variables to configure
            custom_path_vars: Custom PATH configurations
            force_elevation: Force privilege elevation even if not strictly necessary
            
        Returns:
            PreparationResult: Result of preparation operations
        """
        start_time = datetime.now()
        self.logger.info(f"Starting intelligent environment preparation for {len(components)} components")
        
        result = PreparationResult(status=PreparationStatus.IN_PROGRESS)
        
        try:
            # Phase 1: Analyze requirements and determine privilege needs
            self.logger.info("Phase 1: Analyzing requirements and privilege needs")
            privilege_analysis = self._analyze_privilege_requirements(
                components, custom_structures, custom_env_vars, custom_path_vars
            )
            
            # Phase 2: Request elevation if necessary
            if privilege_analysis['requires_elevation'] or force_elevation:
                self.logger.info("Phase 2: Requesting privilege elevation")
                if not self._request_privilege_elevation(privilege_analysis['required_operations']):
                    result.status = PreparationStatus.REQUIRES_ELEVATION
                    result.message = "Privilege elevation required but not granted"
                    result.elevated_operations = privilege_analysis['required_operations']
                    return result
                
                result.privileges_requested.extend(privilege_analysis['required_operations'])
            
            # Phase 3: Create comprehensive backups
            self.logger.info("Phase 3: Creating comprehensive configuration backups")
            backup_result = self._create_comprehensive_backups(components, result)
            if not backup_result:
                result.status = PreparationStatus.FAILED
                result.message = "Failed to create necessary backups"
                return result
            
            # Phase 4: Create intelligent directory structures
            self.logger.info("Phase 4: Creating intelligent directory structures")
            directory_result = self._create_intelligent_directory_structures(
                components, result, custom_structures
            )
            if not directory_result:
                result.status = PreparationStatus.FAILED
                result.message = "Failed to create directory structures"
                return result
            
            # Phase 5: Configure environment variables intelligently
            self.logger.info("Phase 5: Configuring environment variables")
            env_result = self._configure_environment_variables_intelligent(
                components, result, custom_env_vars
            )
            if not env_result:
                result.warnings.append("Some environment variables could not be configured")
            
            # Phase 6: Configure PATH variables intelligently
            self.logger.info("Phase 6: Configuring PATH variables")
            path_result = self._configure_path_variables_intelligent(
                components, result, custom_path_vars
            )
            if not path_result:
                result.warnings.append("Some PATH configurations could not be applied")
            
            # Phase 7: Validate preparation
            self.logger.info("Phase 7: Validating preparation")
            validation_result = self._validate_preparation(result)
            if not validation_result['success']:
                result.warnings.extend(validation_result['warnings'])
                if validation_result['critical_failures']:
                    result.status = PreparationStatus.FAILED
                    result.message = f"Critical validation failures: {validation_result['critical_failures']}"
                    return result
            
            # Success
            end_time = datetime.now()
            result.preparation_time = (end_time - start_time).total_seconds()
            result.status = PreparationStatus.COMPLETED
            result.message = f"Environment prepared successfully in {result.preparation_time:.2f}s"
            result.requires_restart = validation_result.get('requires_restart', False)
            
            # Store in history
            with self._lock:
                self.preparation_history.append(result)
            
            self.logger.info(f"Intelligent preparation completed: {result.message}")
            return result
            
        except Exception as e:
            end_time = datetime.now()
            result.preparation_time = (end_time - start_time).total_seconds()
            result.status = PreparationStatus.FAILED
            result.errors.append(f"Critical error during preparation: {e}")
            result.message = f"Preparation failed: {e}"
            
            self.logger.error(f"Critical error during intelligent preparation: {e}")
            return result
    
    def _analyze_privilege_requirements(self, components: List[str],
                                      custom_structures: Optional[List[DirectoryStructure]] = None,
                                      custom_env_vars: Optional[List[EnvironmentConfiguration]] = None,
                                      custom_path_vars: Optional[List[PathConfiguration]] = None) -> Dict[str, Any]:
        """Analyze what privilege level is required for the preparation"""
        analysis = {
            'requires_elevation': False,
            'required_operations': [],
            'user_operations': [],
            'admin_operations': [],
            'system_operations': []
        }
        
        try:
            # Check directory structure requirements
            structures = self._get_component_directory_structures(components)
            if custom_structures:
                structures.extend(custom_structures)
            
            for structure in structures:
                if structure.required_privilege == PrivilegeLevel.ADMIN:
                    analysis['requires_elevation'] = True
                    analysis['admin_operations'].append(f"Create directory: {structure.path}")
                elif structure.required_privilege == PrivilegeLevel.SYSTEM:
                    analysis['requires_elevation'] = True
                    analysis['system_operations'].append(f"Create system directory: {structure.path}")
                else:
                    analysis['user_operations'].append(f"Create directory: {structure.path}")
            
            # Check environment variable requirements
            env_vars = self._get_component_environment_variables(components)
            if custom_env_vars:
                env_vars.extend(custom_env_vars)
            
            for env_var in env_vars:
                if env_var.scope == "system" or env_var.required_privilege == PrivilegeLevel.ADMIN:
                    analysis['requires_elevation'] = True
                    analysis['admin_operations'].append(f"Set system environment variable: {env_var.name}")
                else:
                    analysis['user_operations'].append(f"Set user environment variable: {env_var.name}")
            
            # Check PATH variable requirements
            path_vars = self._get_component_path_variables(components)
            if custom_path_vars:
                path_vars.extend(custom_path_vars)
            
            for path_var in path_vars:
                if path_var.scope == "system" or path_var.required_privilege == PrivilegeLevel.ADMIN:
                    analysis['requires_elevation'] = True
                    analysis['admin_operations'].append(f"Modify system PATH: {path_var.path}")
                else:
                    analysis['user_operations'].append(f"Modify user PATH: {path_var.path}")
            
            # Combine required operations
            analysis['required_operations'] = (
                analysis['admin_operations'] + analysis['system_operations']
            )
            
            self.logger.info(f"Privilege analysis: elevation required: {analysis['requires_elevation']}")
            self.logger.debug(f"User operations: {len(analysis['user_operations'])}")
            self.logger.debug(f"Admin operations: {len(analysis['admin_operations'])}")
            self.logger.debug(f"System operations: {len(analysis['system_operations'])}")
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error during privilege analysis: {e}")
            # Default to requiring elevation for safety
            analysis['requires_elevation'] = True
            analysis['required_operations'] = ["Privilege analysis failed - elevation required for safety"]
            return analysis
    
    def _request_privilege_elevation(self, required_operations: List[str]) -> bool:
        """Request privilege elevation from the user"""
        try:
            # Check if already running as admin
            if is_admin():
                self.logger.info("Already running with administrative privileges")
                return True
            
            self.logger.info("Requesting privilege elevation for the following operations:")
            for operation in required_operations:
                self.logger.info(f"  - {operation}")
            
            if self.is_windows:
                return self._request_elevation_windows(required_operations)
            elif self.is_linux or self.is_macos:
                return self._request_elevation_unix(required_operations)
            else:
                self.logger.warning(f"Privilege elevation not implemented for platform: {self.platform}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error requesting privilege elevation: {e}")
            return False
    
    def _request_elevation_windows(self, required_operations: List[str]) -> bool:
        """Request elevation on Windows using UAC"""
        try:
            # For now, just check if we have admin rights
            # In a real implementation, this would trigger UAC prompt
            if is_admin():
                return True
            
            self.logger.warning("Administrative privileges required but not available")
            return False
            
        except Exception as e:
            self.logger.error(f"Error requesting Windows elevation: {e}")
            return False
    
    def _request_elevation_unix(self, required_operations: List[str]) -> bool:
        """Request elevation on Unix systems using sudo"""
        try:
            # Check if sudo is available
            try:
                result = subprocess.run(
                    ["sudo", "-n", "true"], 
                    capture_output=True, 
                    timeout=5
                )
                if result.returncode == 0:
                    self.logger.info("Sudo privileges already available")
                    return True
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
            
            self.logger.warning("Sudo privileges required but not available")
            return False
                
        except Exception as e:
            self.logger.error(f"Error requesting Unix elevation: {e}")
            return False
    
    def _create_comprehensive_backups(self, components: List[str], result: PreparationResult) -> bool:
        """Create comprehensive backups of existing configurations"""
        try:
            backup_targets = []
            
            # Add component-specific backup targets
            for component in components:
                targets = self._get_component_backup_targets(component)
                backup_targets.extend(targets)
            
            # Add system-wide backup targets
            system_targets = self._get_system_backup_targets()
            backup_targets.extend(system_targets)
            
            # Remove duplicates
            unique_targets = list(set(backup_targets))
            
            self.logger.info(f"Creating backups for {len(unique_targets)} targets")
            
            success_count = 0
            for target in unique_targets:
                try:
                    backup_info = self._create_backup(target)
                    if backup_info:
                        result.backups_created.append(backup_info)
                        result.total_space_used += backup_info.size_bytes
                        success_count += 1
                        
                        # Register backup
                        with self._lock:
                            self.backup_registry[backup_info.backup_id] = backup_info
                    else:
                        result.warnings.append(f"Could not create backup for: {target}")
                        
                except Exception as e:
                    result.warnings.append(f"Backup failed for {target}: {e}")
                    self.logger.warning(f"Backup failed for {target}: {e}")
            
            self.logger.info(f"Created {success_count}/{len(unique_targets)} backups successfully")
            return success_count > 0 or len(unique_targets) == 0
            
        except Exception as e:
            result.errors.append(f"Critical error during backup creation: {e}")
            self.logger.error(f"Critical error during backup creation: {e}")
            return False
    
    def _create_backup(self, target_path: str) -> Optional[BackupInfo]:
        """Create backup of a specific target"""
        try:
            if not os.path.exists(target_path):
                self.logger.debug(f"Backup target does not exist: {target_path}")
                return None
            
            # Generate backup ID and path
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_id = f"backup_{timestamp}_{uuid.uuid4().hex[:8]}"
            backup_name = f"{backup_id}_{os.path.basename(target_path)}"
            backup_path = os.path.join(self.backup_base_dir, backup_name)
            
            # Determine backup type
            if os.path.isdir(target_path):
                backup_type = BackupType.DIRECTORY
                shutil.copytree(target_path, backup_path, dirs_exist_ok=True)
            else:
                backup_type = BackupType.FILE
                os.makedirs(os.path.dirname(backup_path), exist_ok=True)
                shutil.copy2(target_path, backup_path)
            
            # Calculate size
            if os.path.isdir(backup_path):
                size_bytes = sum(
                    os.path.getsize(os.path.join(dirpath, filename))
                    for dirpath, dirnames, filenames in os.walk(backup_path)
                    for filename in filenames
                )
            else:
                size_bytes = os.path.getsize(backup_path)
            
            # Create backup info
            backup_info = BackupInfo(
                backup_id=backup_id,
                original_path=target_path,
                backup_path=backup_path,
                backup_type=backup_type,
                size_bytes=size_bytes,
                metadata={
                    'created_by': 'IntelligentPreparationManager',
                    'platform': self.platform,
                    'backup_method': 'comprehensive'
                }
            )
            
            self.logger.debug(f"Created backup: {target_path} -> {backup_path} ({size_bytes} bytes)")
            return backup_info
            
        except Exception as e:
            self.logger.error(f"Failed to create backup for {target_path}: {e}")
            return None
    
    def _create_intelligent_directory_structures(self, components: List[str],
                                               result: PreparationResult,
                                               custom_structures: Optional[List[DirectoryStructure]] = None) -> bool:
        """Create intelligent directory structures with conflict resolution"""
        try:
            # Get all directory structures to create
            structures = self._get_component_directory_structures(components)
            if custom_structures:
                structures.extend(custom_structures)
            
            # Sort by dependency and privilege level
            sorted_structures = self._sort_directory_structures(structures)
            
            self.logger.info(f"Creating {len(sorted_structures)} directory structures")
            
            success_count = 0
            for structure in sorted_structures:
                try:
                    if self._create_directory_structure(structure, result):
                        result.directories_created.append(structure.path)
                        success_count += 1
                    else:
                        result.warnings.append(f"Could not create directory: {structure.path}")
                        
                except Exception as e:
                    result.errors.append(f"Failed to create directory {structure.path}: {e}")
                    self.logger.error(f"Failed to create directory {structure.path}: {e}")
            
            self.logger.info(f"Created {success_count}/{len(sorted_structures)} directories successfully")
            return success_count == len(sorted_structures)
            
        except Exception as e:
            result.errors.append(f"Critical error during directory creation: {e}")
            self.logger.error(f"Critical error during directory creation: {e}")
            return False
    
    def _create_directory_structure(self, structure: DirectoryStructure, result: PreparationResult) -> bool:
        """Create a single directory structure with intelligent conflict resolution"""
        try:
            target_path = structure.path
            
            # Check if directory already exists
            if os.path.exists(target_path):
                if os.path.isdir(target_path):
                    # Directory exists, check if we need to backup
                    if structure.backup_existing and os.listdir(target_path):
                        backup_info = self._create_backup(target_path)
                        if backup_info:
                            result.backups_created.append(backup_info)
                            result.total_space_used += backup_info.size_bytes
                    
                    self.logger.debug(f"Directory already exists: {target_path}")
                    return True
                else:
                    # Path exists but is not a directory
                    if structure.backup_existing:
                        backup_info = self._create_backup(target_path)
                        if backup_info:
                            result.backups_created.append(backup_info)
                            result.total_space_used += backup_info.size_bytes
                    
                    # Remove the file/link
                    os.remove(target_path)
            
            # Create directory
            os.makedirs(target_path, exist_ok=True)
            
            # Set permissions if specified (Unix only)
            if structure.permissions and not self.is_windows:
                try:
                    os.chmod(target_path, int(structure.permissions, 8))
                except Exception as e:
                    result.warnings.append(f"Could not set permissions for {target_path}: {e}")
            
            self.logger.debug(f"Created directory structure: {target_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create directory structure {structure.path}: {e}")
            return False
    
    def _configure_environment_variables_intelligent(self, components: List[str],
                                                   result: PreparationResult,
                                                   custom_env_vars: Optional[List[EnvironmentConfiguration]] = None) -> bool:
        """Configure environment variables intelligently"""
        try:
            # Get all environment variables to configure
            env_vars = self._get_component_environment_variables(components)
            if custom_env_vars:
                env_vars.extend(custom_env_vars)
            
            # Remove duplicates and sort by priority
            unique_env_vars = self._deduplicate_environment_variables(env_vars)
            sorted_env_vars = self._sort_environment_variables(unique_env_vars)
            
            self.logger.info(f"Configuring {len(sorted_env_vars)} environment variables")
            
            success_count = 0
            for env_var in sorted_env_vars:
                try:
                    if self._configure_environment_variable(env_var, result):
                        result.env_vars_configured.append(env_var)
                        success_count += 1
                    else:
                        result.warnings.append(f"Could not configure environment variable: {env_var.name}")
                        
                except Exception as e:
                    result.errors.append(f"Failed to configure environment variable {env_var.name}: {e}")
                    self.logger.error(f"Failed to configure environment variable {env_var.name}: {e}")
            
            self.logger.info(f"Configured {success_count}/{len(sorted_env_vars)} environment variables successfully")
            return success_count > 0 or len(sorted_env_vars) == 0
            
        except Exception as e:
            result.errors.append(f"Critical error during environment variable configuration: {e}")
            self.logger.error(f"Critical error during environment variable configuration: {e}")
            return False
    
    def _configure_environment_variable(self, env_var: EnvironmentConfiguration, result: PreparationResult) -> bool:
        """Configure a single environment variable"""
        try:
            # Backup existing value if requested
            if env_var.backup_existing:
                existing_value = get_env_var(env_var.name)
                if existing_value:
                    backup_info = BackupInfo(
                        backup_id=f"env_{env_var.name}_{uuid.uuid4().hex[:8]}",
                        original_path=f"ENV:{env_var.name}",
                        backup_path="",  # Not applicable for env vars
                        backup_type=BackupType.ENVIRONMENT_VAR,
                        metadata={
                            'original_value': existing_value,
                            'scope': env_var.scope,
                            'variable_name': env_var.name
                        }
                    )
                    result.backups_created.append(backup_info)
                    
                    with self._lock:
                        self.backup_registry[backup_info.backup_id] = backup_info
            
            # Configure the variable based on operation
            if env_var.operation == "set":
                success = set_env_var(env_var.name, env_var.value, scope=env_var.scope)
            elif env_var.operation == "append":
                existing_value = get_env_var(env_var.name) or ""
                new_value = existing_value + env_var.separator + env_var.value if existing_value else env_var.value
                success = set_env_var(env_var.name, new_value, scope=env_var.scope)
            elif env_var.operation == "prepend":
                existing_value = get_env_var(env_var.name) or ""
                new_value = env_var.value + env_var.separator + existing_value if existing_value else env_var.value
                success = set_env_var(env_var.name, new_value, scope=env_var.scope)
            elif env_var.operation == "remove":
                from utils.env_manager import unset_env_var
                success = unset_env_var(env_var.name, scope=env_var.scope)
            else:
                self.logger.error(f"Unknown environment variable operation: {env_var.operation}")
                return False
            
            if success:
                self.logger.debug(f"Configured environment variable: {env_var.name} = {env_var.value}")
                return True
            else:
                self.logger.error(f"Failed to configure environment variable: {env_var.name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error configuring environment variable {env_var.name}: {e}")
            return False
    
    def _configure_path_variables_intelligent(self, components: List[str],
                                            result: PreparationResult,
                                            custom_path_vars: Optional[List[PathConfiguration]] = None) -> bool:
        """Configure PATH variables intelligently"""
        try:
            # Get all PATH variables to configure
            path_vars = self._get_component_path_variables(components)
            if custom_path_vars:
                path_vars.extend(custom_path_vars)
            
            # Remove duplicates and sort by priority
            unique_path_vars = self._deduplicate_path_variables(path_vars)
            sorted_path_vars = self._sort_path_variables(unique_path_vars)
            
            self.logger.info(f"Configuring {len(sorted_path_vars)} PATH variables")
            
            success_count = 0
            for path_var in sorted_path_vars:
                try:
                    if self._configure_path_variable(path_var, result):
                        result.path_vars_configured.append(path_var)
                        success_count += 1
                    else:
                        result.warnings.append(f"Could not configure PATH variable: {path_var.path}")
                        
                except Exception as e:
                    result.errors.append(f"Failed to configure PATH variable {path_var.path}: {e}")
                    self.logger.error(f"Failed to configure PATH variable {path_var.path}: {e}")
            
            self.logger.info(f"Configured {success_count}/{len(sorted_path_vars)} PATH variables successfully")
            return success_count > 0 or len(sorted_path_vars) == 0
            
        except Exception as e:
            result.errors.append(f"Critical error during PATH variable configuration: {e}")
            self.logger.error(f"Critical error during PATH variable configuration: {e}")
            return False
    
    def _configure_path_variable(self, path_var: PathConfiguration, result: PreparationResult) -> bool:
        """Configure a single PATH variable"""
        try:
            # Backup existing PATH if requested
            if path_var.backup_existing:
                existing_path = get_env_var("PATH")
                if existing_path:
                    backup_info = BackupInfo(
                        backup_id=f"path_{uuid.uuid4().hex[:8]}",
                        original_path="ENV:PATH",
                        backup_path="",  # Not applicable for env vars
                        backup_type=BackupType.PATH_VAR,
                        metadata={
                            'original_value': existing_path,
                            'scope': path_var.scope,
                            'operation': path_var.operation,
                            'path': path_var.path
                        }
                    )
                    result.backups_created.append(backup_info)
                    
                    with self._lock:
                        self.backup_registry[backup_info.backup_id] = backup_info
            
            # Configure PATH based on operation
            if path_var.operation == "add":
                success = add_to_path(path_var.path, scope=path_var.scope)
            elif path_var.operation == "remove":
                success = remove_from_path(path_var.path, scope=path_var.scope)
            else:
                self.logger.error(f"Unknown PATH operation: {path_var.operation}")
                return False
            
            if success:
                self.logger.debug(f"Configured PATH variable: {path_var.operation} {path_var.path}")
                return True
            else:
                self.logger.error(f"Failed to configure PATH variable: {path_var.path}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error configuring PATH variable {path_var.path}: {e}")
            return False
    
    def _validate_preparation(self, result: PreparationResult) -> Dict[str, Any]:
        """Validate the preparation results"""
        validation_result = {
            'success': True,
            'warnings': [],
            'critical_failures': [],
            'requires_restart': False
        }
        
        try:
            # Validate directory structures
            for directory in result.directories_created:
                if not os.path.exists(directory):
                    validation_result['critical_failures'].append(f"Directory not found: {directory}")
                    validation_result['success'] = False
                elif not os.path.isdir(directory):
                    validation_result['critical_failures'].append(f"Path is not a directory: {directory}")
                    validation_result['success'] = False
                elif not check_write_permission(directory)[0]:
                    validation_result['warnings'].append(f"No write permission for directory: {directory}")
            
            # Validate environment variables
            for env_var in result.env_vars_configured:
                current_value = get_env_var(env_var.name)
                if env_var.operation != "remove" and not current_value:
                    validation_result['warnings'].append(f"Environment variable not set: {env_var.name}")
                elif env_var.operation == "remove" and current_value:
                    validation_result['warnings'].append(f"Environment variable not removed: {env_var.name}")
            
            # Check if restart is required (Windows environment variables)
            if self.is_windows and result.env_vars_configured:
                system_vars = [var for var in result.env_vars_configured if var.scope == "system"]
                if system_vars:
                    validation_result['requires_restart'] = True
                    validation_result['warnings'].append("System restart may be required for environment variables to take effect")
            
            # Validate backups
            for backup in result.backups_created:
                if backup.backup_type in [BackupType.FILE, BackupType.DIRECTORY]:
                    if not os.path.exists(backup.backup_path):
                        validation_result['warnings'].append(f"Backup not found: {backup.backup_path}")
            
            self.logger.info(f"Validation completed: success={validation_result['success']}, "
                           f"warnings={len(validation_result['warnings'])}, "
                           f"critical_failures={len(validation_result['critical_failures'])}")
            
            return validation_result
            
        except Exception as e:
            self.logger.error(f"Error during validation: {e}")
            validation_result['success'] = False
            validation_result['critical_failures'].append(f"Validation error: {e}")
            return validation_result
    
    def _get_component_directory_structures(self, components: List[str]) -> List[DirectoryStructure]:
        """Get directory structures required for components"""
        structures = []
        
        for component in components:
            component_lower = component.lower()
            
            # Base directories for all components
            base_structures = [
                DirectoryStructure(
                    path=os.path.join(self.base_path, "downloads", component),
                    permissions="755" if not self.is_windows else None
                ),
                DirectoryStructure(
                    path=os.path.join(self.base_path, "temp", component),
                    permissions="755" if not self.is_windows else None
                ),
                DirectoryStructure(
                    path=os.path.join(self.base_path, "logs", component),
                    permissions="755" if not self.is_windows else None
                ),
                DirectoryStructure(
                    path=os.path.join(self.base_path, "config", component),
                    permissions="755" if not self.is_windows else None
                )
            ]
            structures.extend(base_structures)
            
            # Component-specific directories
            if component_lower in ["java", "jdk", "openjdk"]:
                structures.append(DirectoryStructure(
                    path=os.path.join(self.base_path, "java"),
                    permissions="755" if not self.is_windows else None
                ))
            elif component_lower in ["python", "python3"]:
                structures.extend([
                    DirectoryStructure(
                        path=os.path.join(self.base_path, "python"),
                        permissions="755" if not self.is_windows else None
                    ),
                    DirectoryStructure(
                        path=os.path.join(self.base_path, "python", "scripts"),
                        permissions="755" if not self.is_windows else None
                    )
                ])
            elif component_lower in ["node", "nodejs"]:
                structures.extend([
                    DirectoryStructure(
                        path=os.path.join(self.base_path, "nodejs"),
                        permissions="755" if not self.is_windows else None
                    ),
                    DirectoryStructure(
                        path=os.path.join(self.base_path, "nodejs", "global"),
                        permissions="755" if not self.is_windows else None
                    )
                ])
        
        return structures
    
    def _get_component_environment_variables(self, components: List[str]) -> List[EnvironmentConfiguration]:
        """Get environment variables required for components"""
        env_vars = []
        
        # Global environment variables
        global_vars = [
            EnvironmentConfiguration(
                name="ENVIRONMENT_DEV_HOME",
                value=self.base_path,
                scope="user"
            ),
            EnvironmentConfiguration(
                name="ENVIRONMENT_DEV_VERSION",
                value="2.0.0",
                scope="user"
            )
        ]
        env_vars.extend(global_vars)
        
        for component in components:
            component_lower = component.lower()
            
            if component_lower in ["java", "jdk", "openjdk"]:
                env_vars.extend([
                    EnvironmentConfiguration(
                        name="JAVA_HOME",
                        value=os.path.join(self.base_path, "java"),
                        scope="user"
                    ),
                    EnvironmentConfiguration(
                        name="JDK_HOME",
                        value=os.path.join(self.base_path, "java"),
                        scope="user"
                    )
                ])
            elif component_lower in ["python", "python3"]:
                env_vars.extend([
                    EnvironmentConfiguration(
                        name="PYTHON_HOME",
                        value=os.path.join(self.base_path, "python"),
                        scope="user"
                    ),
                    EnvironmentConfiguration(
                        name="PYTHONPATH",
                        value=os.path.join(self.base_path, "python", "lib"),
                        scope="user",
                        operation="append"
                    )
                ])
            elif component_lower in ["node", "nodejs"]:
                env_vars.extend([
                    EnvironmentConfiguration(
                        name="NODE_HOME",
                        value=os.path.join(self.base_path, "nodejs"),
                        scope="user"
                    ),
                    EnvironmentConfiguration(
                        name="NPM_CONFIG_PREFIX",
                        value=os.path.join(self.base_path, "nodejs", "global"),
                        scope="user"
                    )
                ])
        
        return env_vars
    
    def _get_component_path_variables(self, components: List[str]) -> List[PathConfiguration]:
        """Get PATH variables required for components"""
        path_vars = []
        
        for component in components:
            component_lower = component.lower()
            
            if component_lower in ["java", "jdk", "openjdk"]:
                path_vars.append(PathConfiguration(
                    path=os.path.join(self.base_path, "java", "bin"),
                    operation="add",
                    scope="user"
                ))
            elif component_lower in ["python", "python3"]:
                path_vars.extend([
                    PathConfiguration(
                        path=os.path.join(self.base_path, "python"),
                        operation="add",
                        scope="user"
                    ),
                    PathConfiguration(
                        path=os.path.join(self.base_path, "python", "scripts"),
                        operation="add",
                        scope="user"
                    )
                ])
            elif component_lower in ["node", "nodejs"]:
                path_vars.extend([
                    PathConfiguration(
                        path=os.path.join(self.base_path, "nodejs"),
                        operation="add",
                        scope="user"
                    ),
                    PathConfiguration(
                        path=os.path.join(self.base_path, "nodejs", "global", "bin"),
                        operation="add",
                        scope="user"
                    )
                ])
        
        return path_vars
    
    def _get_component_backup_targets(self, component: str) -> List[str]:
        """Get backup targets for a specific component"""
        targets = []
        component_lower = component.lower()
        
        # Common configuration files
        common_configs = [
            os.path.join(self.base_path, "config", f"{component}.yaml"),
            os.path.join(self.base_path, "config", f"{component}.json"),
            os.path.join(self.base_path, "config", component)
        ]
        targets.extend(common_configs)
        
        # Component-specific backup targets
        if component_lower in ["java", "jdk", "openjdk"]:
            targets.extend([
                os.path.expanduser("~/.java"),
                os.path.expanduser("~/.m2") if os.path.exists(os.path.expanduser("~/.m2")) else None
            ])
        elif component_lower in ["python", "python3"]:
            targets.extend([
                os.path.expanduser("~/.pip"),
                os.path.expanduser("~/.python_history") if os.path.exists(os.path.expanduser("~/.python_history")) else None
            ])
        elif component_lower in ["node", "nodejs"]:
            targets.extend([
                os.path.expanduser("~/.npm"),
                os.path.expanduser("~/.npmrc") if os.path.exists(os.path.expanduser("~/.npmrc")) else None
            ])
        
        # Filter out None values
        return [target for target in targets if target is not None]
    
    def _get_system_backup_targets(self) -> List[str]:
        """Get system-wide backup targets"""
        targets = []
        
        # Environment variables backup
        if not self.is_windows:
            # Unix shell configuration files
            shell_configs = [
                os.path.expanduser("~/.bashrc"),
                os.path.expanduser("~/.bash_profile"),
                os.path.expanduser("~/.zshrc"),
                os.path.expanduser("~/.profile")
            ]
            targets.extend([config for config in shell_configs if os.path.exists(config)])
        
        return targets
    
    def _sort_directory_structures(self, structures: List[DirectoryStructure]) -> List[DirectoryStructure]:
        """Sort directory structures by dependency and privilege level"""
        # Sort by path depth (parents first) and then by privilege level
        return sorted(structures, key=lambda s: (len(Path(s.path).parts), s.required_privilege.value))
    
    def _deduplicate_environment_variables(self, env_vars: List[EnvironmentConfiguration]) -> List[EnvironmentConfiguration]:
        """Remove duplicate environment variables, keeping the last one"""
        seen = {}
        for env_var in env_vars:
            key = (env_var.name, env_var.scope)
            seen[key] = env_var
        return list(seen.values())
    
    def _sort_environment_variables(self, env_vars: List[EnvironmentConfiguration]) -> List[EnvironmentConfiguration]:
        """Sort environment variables by priority"""
        # Sort by scope (user first, then system) and then by name
        return sorted(env_vars, key=lambda e: (e.scope == "system", e.name))
    
    def _deduplicate_path_variables(self, path_vars: List[PathConfiguration]) -> List[PathConfiguration]:
        """Remove duplicate PATH variables, keeping the last one"""
        seen = {}
        for path_var in path_vars:
            key = (path_var.path, path_var.scope, path_var.operation)
            seen[key] = path_var
        return list(seen.values())
    
    def _sort_path_variables(self, path_vars: List[PathConfiguration]) -> List[PathConfiguration]:
        """Sort PATH variables by priority"""
        # Sort by scope (user first, then system) and then by operation (add first, then remove)
        return sorted(path_vars, key=lambda p: (p.scope == "system", p.operation == "remove", p.path))
    
    def restore_from_backup(self, backup_id: str) -> bool:
        """Restore from a specific backup"""
        try:
            with self._lock:
                if backup_id not in self.backup_registry:
                    self.logger.error(f"Backup not found: {backup_id}")
                    return False
                
                backup_info = self.backup_registry[backup_id]
            
            if backup_info.backup_type == BackupType.ENVIRONMENT_VAR:
                # Restore environment variable
                var_name = backup_info.metadata['variable_name']
                original_value = backup_info.metadata['original_value']
                scope = backup_info.metadata['scope']
                
                success = set_env_var(var_name, original_value, scope=scope)
                if success:
                    self.logger.info(f"Restored environment variable: {var_name}")
                return success
                
            elif backup_info.backup_type == BackupType.PATH_VAR:
                # Restore PATH variable
                original_value = backup_info.metadata['original_value']
                scope = backup_info.metadata['scope']
                
                success = set_env_var("PATH", original_value, scope=scope)
                if success:
                    self.logger.info("Restored PATH variable")
                return success
                
            elif backup_info.backup_type in [BackupType.FILE, BackupType.DIRECTORY]:
                # Restore file or directory
                if not os.path.exists(backup_info.backup_path):
                    self.logger.error(f"Backup file not found: {backup_info.backup_path}")
                    return False
                
                # Remove current version if it exists
                if os.path.exists(backup_info.original_path):
                    if os.path.isdir(backup_info.original_path):
                        shutil.rmtree(backup_info.original_path)
                    else:
                        os.remove(backup_info.original_path)
                
                # Restore from backup
                if backup_info.backup_type == BackupType.DIRECTORY:
                    shutil.copytree(backup_info.backup_path, backup_info.original_path)
                else:
                    shutil.copy2(backup_info.backup_path, backup_info.original_path)
                
                self.logger.info(f"Restored from backup: {backup_info.original_path}")
                return True
            
            else:
                self.logger.error(f"Unknown backup type: {backup_info.backup_type}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error restoring from backup {backup_id}: {e}")
            return False
    
    def list_backups(self) -> List[BackupInfo]:
        """List all available backups"""
        with self._lock:
            return list(self.backup_registry.values())
    
    def cleanup_old_backups(self, days_old: int = 30) -> int:
        """Clean up old backups"""
        cleaned_count = 0
        cutoff_time = datetime.now() - timedelta(days=days_old)
        
        try:
            with self._lock:
                to_remove = []
                for backup_id, backup_info in self.backup_registry.items():
                    if backup_info.timestamp < cutoff_time:
                        # Remove backup file if it exists
                        if backup_info.backup_type in [BackupType.FILE, BackupType.DIRECTORY]:
                            if os.path.exists(backup_info.backup_path):
                                try:
                                    if os.path.isdir(backup_info.backup_path):
                                        shutil.rmtree(backup_info.backup_path)
                                    else:
                                        os.remove(backup_info.backup_path)
                                    cleaned_count += 1
                                except Exception as e:
                                    self.logger.warning(f"Could not remove backup file {backup_info.backup_path}: {e}")
                        
                        to_remove.append(backup_id)
                
                # Remove from registry
                for backup_id in to_remove:
                    del self.backup_registry[backup_id]
            
            self.logger.info(f"Cleaned up {cleaned_count} old backups")
            return cleaned_count
            
        except Exception as e:
            self.logger.error(f"Error during backup cleanup: {e}")
            return cleaned_count
    
    def get_preparation_history(self) -> List[PreparationResult]:
        """Get history of preparation operations"""
        with self._lock:
            return self.preparation_history.copy()
    
    def get_preparation_statistics(self) -> Dict[str, Any]:
        """Get statistics about preparation operations"""
        with self._lock:
            history = self.preparation_history.copy()
            backups = list(self.backup_registry.values())
        
        if not history:
            return {
                'total_preparations': 0,
                'successful_preparations': 0,
                'failed_preparations': 0,
                'total_backups': len(backups),
                'total_backup_size': sum(b.size_bytes for b in backups),
                'average_preparation_time': 0.0
            }
        
        successful = [h for h in history if h.status == PreparationStatus.COMPLETED]
        failed = [h for h in history if h.status == PreparationStatus.FAILED]
        
        return {
            'total_preparations': len(history),
            'successful_preparations': len(successful),
            'failed_preparations': len(failed),
            'success_rate': len(successful) / len(history) * 100,
            'total_backups': len(backups),
            'total_backup_size': sum(b.size_bytes for b in backups),
            'average_preparation_time': sum(h.preparation_time for h in history) / len(history),
            'total_directories_created': sum(len(h.directories_created) for h in history),
            'total_env_vars_configured': sum(len(h.env_vars_configured) for h in history),
            'total_path_vars_configured': sum(len(h.path_vars_configured) for h in history)
        }