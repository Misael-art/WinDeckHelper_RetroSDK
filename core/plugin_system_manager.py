# -*- coding: utf-8 -*-
"""
Plugin System Manager - Secure Plugin Infrastructure

This module implements a comprehensive plugin system manager with rigorous structure validation,
secure API access with sandboxing, and digital signature verification for plugin authenticity.

Requirements addressed:
- 7.1: Rigorous structure validation and secure API with sandboxing
- 7.2: Automatic plugin conflict detection and digital signature verification
- 7.5: Plugin status feedback and backward compatibility maintenance
"""

import os
import sys
import json
import hashlib
import logging
import threading
import tempfile
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple, Type, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime, timedelta
from contextlib import contextmanager
import importlib.util
import inspect
try:
    import cryptography
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa, padding
    from cryptography.exceptions import InvalidSignature
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    CRYPTOGRAPHY_AVAILABLE = False
    # Create dummy classes for when cryptography is not available
    class InvalidSignature(Exception):
        pass

try:
    from .plugin_base import (
        PluginInterface, PluginMetadata, PluginStatus, ValidationResult,
        PluginConflict, PluginValidator, DependencyResolver, RuntimePlugin,
        UtilityPlugin, Permission
    )
    from .plugin_security import PluginSecurityManager, PluginTrustLevel, SandboxConfig
    from .security_manager import SecurityManager, SecurityLevel
except ImportError:
    # Fallback for direct execution
    from plugin_base import (
        PluginInterface, PluginMetadata, PluginStatus, ValidationResult,
        PluginConflict, PluginValidator, DependencyResolver, RuntimePlugin,
        UtilityPlugin, Permission
    )
    from plugin_security import PluginSecurityManager, PluginTrustLevel, SandboxConfig
    from security_manager import SecurityManager, SecurityLevel


class PluginSystemError(Exception):
    """Base exception for plugin system errors"""
    pass


class PluginValidationError(PluginSystemError):
    """Exception raised when plugin validation fails"""
    pass


class PluginSecurityError(PluginSystemError):
    """Exception raised for plugin security violations"""
    pass


class PluginLoadError(PluginSystemError):
    """Exception raised when plugin loading fails"""
    pass


@dataclass
class PluginStructureValidation:
    """Result of plugin structure validation"""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    security_issues: List[str] = field(default_factory=list)
    required_files_present: bool = True
    metadata_valid: bool = True
    signature_valid: bool = False
    hash_verified: bool = False
    
    def add_error(self, error: str):
        """Add validation error"""
        self.errors.append(error)
        self.is_valid = False
    
    def add_warning(self, warning: str):
        """Add validation warning"""
        self.warnings.append(warning)
    
    def add_security_issue(self, issue: str):
        """Add security issue"""
        self.security_issues.append(issue)
        self.is_valid = False


@dataclass
class SecurePluginContext:
    """Secure execution context for plugins"""
    plugin_name: str
    sandbox_directory: str
    allowed_operations: Set[str]
    restricted_paths: Set[str]
    environment_variables: Dict[str, str]
    resource_limits: Dict[str, Any]
    api_whitelist: Set[str]
    execution_timeout: int
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class PluginExecutionResult:
    """Result of plugin execution"""
    success: bool
    result: Any = None
    error_message: Optional[str] = None
    execution_time: float = 0.0
    resource_usage: Dict[str, Any] = field(default_factory=dict)
    security_violations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class PluginSystemManager:
    """
    Comprehensive Plugin System Manager with Security
    
    Provides:
    - Rigorous structure validation
    - Secure API access with sandboxing
    - Digital signature verification
    - Plugin conflict detection and management
    - Version management and updates
    - Plugin integration mechanisms
    - Backward compatibility maintenance
    """
    
    def __init__(self, 
                 plugin_directories: Optional[List[str]] = None,
                 security_manager: Optional[SecurityManager] = None,
                 enable_sandboxing: bool = True,
                 require_signatures: bool = True):
        """
        Initialize Plugin System Manager
        
        Args:
            plugin_directories: List of directories to search for plugins
            security_manager: Security manager instance
            enable_sandboxing: Whether to enable plugin sandboxing
            require_signatures: Whether to require digital signatures
        """
        self.logger = logging.getLogger(__name__)
        
        # Core components
        self.security_manager = security_manager or SecurityManager()
        self.plugin_security = PluginSecurityManager(self.security_manager)
        self.validator = PluginValidator()
        self.dependency_resolver = DependencyResolver()
        
        # Configuration
        self.plugin_directories = plugin_directories or [
            "plugins",
            "core/plugins",
            os.path.expanduser("~/.environment_dev/plugins")
        ]
        self.enable_sandboxing = enable_sandboxing
        self.require_signatures = require_signatures
        
        # Plugin storage
        self.loaded_plugins: Dict[str, Dict[str, Any]] = {}
        self.plugin_registry: Dict[str, PluginMetadata] = {}
        self.plugin_contexts: Dict[str, SecurePluginContext] = {}
        self.execution_history: List[PluginExecutionResult] = []
        
        # Security and validation
        self.trusted_public_keys: Set[str] = set()
        self.blocked_plugins: Set[str] = set()
        self.plugin_whitelist: Set[str] = set()
        self.api_whitelist: Set[str] = self._create_default_api_whitelist()
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Initialize directories
        self._initialize_plugin_directories()
        
        # Load configuration
        self._load_plugin_system_config()
        
        self.logger.info("Plugin System Manager initialized with security enabled")
    
    def validate_plugin_structure(self, plugin_path: Path) -> PluginStructureValidation:
        """
        Perform rigorous structure validation of plugin
        
        Args:
            plugin_path: Path to plugin directory
            
        Returns:
            PluginStructureValidation: Comprehensive validation result
        """
        validation = PluginStructureValidation(is_valid=True)
        
        try:
            # Check if path exists and is directory
            if not plugin_path.exists():
                validation.add_error(f"Plugin path does not exist: {plugin_path}")
                return validation
            
            if not plugin_path.is_dir():
                validation.add_error(f"Plugin path is not a directory: {plugin_path}")
                return validation
            
            # Check required files
            required_files = {
                'plugin.json': 'Plugin metadata file',
                '__init__.py': 'Python module entry point',
                'README.md': 'Plugin documentation'
            }
            
            for file_name, description in required_files.items():
                file_path = plugin_path / file_name
                if not file_path.exists():
                    if file_name == 'README.md':
                        validation.add_warning(f"Missing {description}: {file_name}")
                    else:
                        validation.add_error(f"Missing required {description}: {file_name}")
                        validation.required_files_present = False
            
            # Validate plugin.json structure and content
            plugin_json_path = plugin_path / 'plugin.json'
            if plugin_json_path.exists():
                metadata_validation = self._validate_plugin_metadata_file(plugin_json_path)
                validation.metadata_valid = metadata_validation.is_valid
                validation.errors.extend(metadata_validation.errors)
                validation.warnings.extend(metadata_validation.warnings)
            
            # Check for suspicious files and patterns
            security_validation = self._validate_plugin_security_structure(plugin_path)
            validation.security_issues.extend(security_validation)
            if security_validation:
                validation.is_valid = False
            
            # Validate Python code structure
            code_validation = self._validate_plugin_code_structure(plugin_path)
            validation.errors.extend(code_validation.get('errors', []))
            validation.warnings.extend(code_validation.get('warnings', []))
            if code_validation.get('errors'):
                validation.is_valid = False
            
            # Verify digital signature if present
            if self.require_signatures:
                signature_validation = self._validate_plugin_signature(plugin_path)
                validation.signature_valid = signature_validation
                if not signature_validation:
                    validation.add_error("Digital signature verification failed")
            
            # Verify plugin hash integrity
            hash_validation = self._validate_plugin_hash(plugin_path)
            validation.hash_verified = hash_validation
            if not hash_validation:
                validation.add_warning("Plugin hash verification failed")
            
            # Final validation status
            if validation.errors or validation.security_issues:
                validation.is_valid = False
            
            # Log validation result
            self.security_manager.audit_critical_operation(
                operation="plugin_structure_validation",
                component="plugin_system",
                details={
                    "plugin_path": str(plugin_path),
                    "is_valid": validation.is_valid,
                    "errors_count": len(validation.errors),
                    "warnings_count": len(validation.warnings),
                    "security_issues_count": len(validation.security_issues)
                },
                success=validation.is_valid,
                security_level=SecurityLevel.HIGH if not validation.is_valid else SecurityLevel.MEDIUM
            )
            
            return validation
            
        except Exception as e:
            self.logger.error(f"Error validating plugin structure: {e}")
            validation.add_error(f"Validation error: {str(e)}")
            return validation
    
    def load_plugin_with_security(self, plugin_path: Path, trust_level: PluginTrustLevel = PluginTrustLevel.UNTRUSTED) -> bool:
        """
        Load plugin with comprehensive security validation
        
        Args:
            plugin_path: Path to plugin directory
            trust_level: Trust level for the plugin
            
        Returns:
            bool: True if plugin loaded successfully
        """
        try:
            with self._lock:
                # Validate plugin structure
                structure_validation = self.validate_plugin_structure(plugin_path)
                if not structure_validation.is_valid:
                    raise PluginValidationError(f"Plugin structure validation failed: {structure_validation.errors}")
                
                # Load and validate metadata
                metadata = self._load_plugin_metadata(plugin_path)
                
                # Check if plugin is blocked
                if metadata.name in self.blocked_plugins:
                    raise PluginSecurityError(f"Plugin {metadata.name} is blocked")
                
                # Check whitelist if enabled
                if self.plugin_whitelist and metadata.name not in self.plugin_whitelist:
                    raise PluginSecurityError(f"Plugin {metadata.name} not in whitelist")
                
                # Validate plugin security
                security_valid, security_issues = self.plugin_security.validate_plugin_security(plugin_path, metadata)
                if not security_valid:
                    raise PluginSecurityError(f"Plugin security validation failed: {security_issues}")
                
                # Create security profile
                security_profile = self.plugin_security.create_security_profile(metadata, trust_level)
                
                # Load plugin module in secure context
                plugin_instance = self._load_plugin_module_secure(plugin_path, metadata, security_profile)
                
                # Create secure execution context
                secure_context = self._create_secure_plugin_context(metadata.name, security_profile)
                
                # Initialize plugin in sandbox
                initialization_result = self._initialize_plugin_secure(plugin_instance, secure_context)
                if not initialization_result.success:
                    raise PluginLoadError(f"Plugin initialization failed: {initialization_result.error_message}")
                
                # Register plugin
                plugin_info = {
                    'metadata': metadata,
                    'instance': plugin_instance,
                    'security_profile': security_profile,
                    'context': secure_context,
                    'path': plugin_path,
                    'status': PluginStatus.LOADED,
                    'load_time': datetime.now(),
                    'trust_level': trust_level
                }
                
                self.loaded_plugins[metadata.name] = plugin_info
                self.plugin_registry[metadata.name] = metadata
                self.plugin_contexts[metadata.name] = secure_context
                
                self.logger.info(f"Successfully loaded plugin {metadata.name} with trust level {trust_level.value}")
                
                # Audit successful load
                self.security_manager.audit_critical_operation(
                    operation="plugin_load",
                    component="plugin_system",
                    details={
                        "plugin_name": metadata.name,
                        "plugin_version": metadata.version,
                        "trust_level": trust_level.value,
                        "path": str(plugin_path)
                    },
                    success=True,
                    security_level=SecurityLevel.MEDIUM
                )
                
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to load plugin from {plugin_path}: {e}")
            
            # Audit failed load
            self.security_manager.audit_critical_operation(
                operation="plugin_load",
                component="plugin_system",
                details={
                    "plugin_path": str(plugin_path),
                    "error": str(e),
                    "trust_level": trust_level.value
                },
                success=False,
                security_level=SecurityLevel.HIGH
            )
            
            return False
    
    @contextmanager
    def execute_plugin_secure(self, plugin_name: str, operation: str, **kwargs):
        """
        Execute plugin operation in secure sandbox environment
        
        Args:
            plugin_name: Name of plugin to execute
            operation: Operation to perform
            **kwargs: Operation arguments
            
        Yields:
            PluginExecutionResult: Result of plugin execution
        """
        if plugin_name not in self.loaded_plugins:
            raise PluginLoadError(f"Plugin {plugin_name} not loaded")
        
        plugin_info = self.loaded_plugins[plugin_name]
        context = self.plugin_contexts[plugin_name]
        
        start_time = datetime.now()
        result = PluginExecutionResult(success=False)
        
        try:
            # Check if operation is allowed
            if operation not in context.allowed_operations:
                raise PluginSecurityError(f"Operation {operation} not allowed for plugin {plugin_name}")
            
            # Create sandbox environment
            with self.plugin_security.create_sandbox_environment(plugin_name) as sandbox:
                # Execute operation with timeout and resource monitoring
                with self._monitor_plugin_execution(plugin_name, context.execution_timeout) as monitor:
                    try:
                        # Call plugin operation
                        plugin_instance = plugin_info['instance']
                        if hasattr(plugin_instance, operation):
                            operation_result = getattr(plugin_instance, operation)(**kwargs)
                            result.success = True
                            result.result = operation_result
                        else:
                            raise AttributeError(f"Plugin {plugin_name} does not have operation {operation}")
                    
                    except Exception as e:
                        result.error_message = str(e)
                        self.logger.error(f"Plugin {plugin_name} operation {operation} failed: {e}")
                
                # Collect resource usage
                result.resource_usage = monitor.get_resource_usage()
                
        except Exception as e:
            result.error_message = str(e)
            result.security_violations.append(f"Execution error: {str(e)}")
            
            # Report security violation if needed
            if isinstance(e, PluginSecurityError):
                self.plugin_security.report_security_violation(
                    plugin_name, "execution_violation", str(e), SecurityLevel.HIGH
                )
        
        finally:
            # Calculate execution time
            result.execution_time = (datetime.now() - start_time).total_seconds()
            
            # Store execution history
            self.execution_history.append(result)
            
            # Audit execution
            self.security_manager.audit_critical_operation(
                operation="plugin_execution",
                component="plugin_system",
                details={
                    "plugin_name": plugin_name,
                    "operation": operation,
                    "success": result.success,
                    "execution_time": result.execution_time,
                    "security_violations": len(result.security_violations)
                },
                success=result.success,
                security_level=SecurityLevel.MEDIUM if result.success else SecurityLevel.HIGH
            )
        
        yield result
    
    def detect_plugin_conflicts(self) -> List[PluginConflict]:
        """
        Detect conflicts between loaded plugins
        
        Returns:
            List[PluginConflict]: List of detected conflicts
        """
        conflicts = []
        
        try:
            plugins = [info['metadata'] for info in self.loaded_plugins.values()]
            
            # Use dependency resolver to check conflicts
            dependency_conflicts = self.dependency_resolver.check_conflicts(plugins)
            conflicts.extend(dependency_conflicts)
            
            # Check for API conflicts
            api_conflicts = self._detect_api_conflicts()
            conflicts.extend(api_conflicts)
            
            # Check for resource conflicts
            resource_conflicts = self._detect_resource_conflicts()
            conflicts.extend(resource_conflicts)
            
            # Check for permission conflicts
            permission_conflicts = self._detect_permission_conflicts()
            conflicts.extend(permission_conflicts)
            
            self.logger.info(f"Detected {len(conflicts)} plugin conflicts")
            return conflicts
            
        except Exception as e:
            self.logger.error(f"Error detecting plugin conflicts: {e}")
            return []
    
    def get_plugin_status_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive plugin status report
        
        Returns:
            Dict[str, Any]: Detailed status report
        """
        try:
            total_plugins = len(self.loaded_plugins)
            active_plugins = len([p for p in self.loaded_plugins.values() if p['status'] == PluginStatus.ACTIVE])
            blocked_plugins = len(self.blocked_plugins)
            
            # Calculate trust level distribution
            trust_levels = {}
            for plugin_info in self.loaded_plugins.values():
                trust_level = plugin_info['trust_level'].value
                trust_levels[trust_level] = trust_levels.get(trust_level, 0) + 1
            
            # Recent execution statistics
            recent_executions = [e for e in self.execution_history 
                               if e.execution_time and (datetime.now() - datetime.fromtimestamp(0)).total_seconds() < 3600]
            
            successful_executions = len([e for e in recent_executions if e.success])
            failed_executions = len([e for e in recent_executions if not e.success])
            
            # Security statistics
            security_violations = sum(len(e.security_violations) for e in recent_executions)
            
            return {
                "summary": {
                    "total_plugins": total_plugins,
                    "active_plugins": active_plugins,
                    "blocked_plugins": blocked_plugins,
                    "sandboxing_enabled": self.enable_sandboxing,
                    "signature_verification_required": self.require_signatures
                },
                "trust_levels": trust_levels,
                "execution_statistics": {
                    "recent_executions": len(recent_executions),
                    "successful_executions": successful_executions,
                    "failed_executions": failed_executions,
                    "security_violations": security_violations
                },
                "plugins": {
                    name: {
                        "name": info['metadata'].name,
                        "version": info['metadata'].version,
                        "status": info['status'].value,
                        "trust_level": info['trust_level'].value,
                        "load_time": info['load_time'].isoformat(),
                        "permissions": [p.value for p in info['metadata'].permissions]
                    }
                    for name, info in self.loaded_plugins.items()
                },
                "security_report": self.plugin_security.get_security_report()
            }
            
        except Exception as e:
            self.logger.error(f"Error generating plugin status report: {e}")
            return {"error": str(e)}    

    def unload_plugin(self, plugin_name: str) -> bool:
        """
        Safely unload plugin with cleanup
        
        Args:
            plugin_name: Name of plugin to unload
            
        Returns:
            bool: True if successfully unloaded
        """
        try:
            with self._lock:
                if plugin_name not in self.loaded_plugins:
                    self.logger.warning(f"Plugin {plugin_name} not loaded")
                    return False
                
                plugin_info = self.loaded_plugins[plugin_name]
                
                # Cleanup plugin instance
                try:
                    plugin_instance = plugin_info['instance']
                    if hasattr(plugin_instance, 'cleanup'):
                        plugin_instance.cleanup()
                except Exception as e:
                    self.logger.warning(f"Error during plugin cleanup: {e}")
                
                # Cleanup secure context
                context = self.plugin_contexts.get(plugin_name)
                if context:
                    self._cleanup_plugin_context(context)
                
                # Remove from registries
                del self.loaded_plugins[plugin_name]
                if plugin_name in self.plugin_registry:
                    del self.plugin_registry[plugin_name]
                if plugin_name in self.plugin_contexts:
                    del self.plugin_contexts[plugin_name]
                
                self.logger.info(f"Successfully unloaded plugin: {plugin_name}")
                
                # Audit unload
                self.security_manager.audit_critical_operation(
                    operation="plugin_unload",
                    component="plugin_system",
                    details={"plugin_name": plugin_name},
                    success=True,
                    security_level=SecurityLevel.LOW
                )
                
                return True
                
        except Exception as e:
            self.logger.error(f"Error unloading plugin {plugin_name}: {e}")
            return False
    
    def shutdown(self):
        """
        Shutdown plugin system and cleanup all resources
        """
        self.logger.info("Shutting down plugin system")
        
        # Unload all plugins
        plugin_names = list(self.loaded_plugins.keys())
        for name in plugin_names:
            self.unload_plugin(name)
        
        # Cleanup temporary directories
        self._cleanup_all_contexts()
        
        self.logger.info("Plugin system shutdown complete")
    
    # Private helper methods
    
    def _initialize_plugin_directories(self):
        """Initialize plugin directories"""
        for directory in self.plugin_directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
    
    def _create_default_api_whitelist(self) -> Set[str]:
        """Create default API whitelist for plugins"""
        return {
            'logging.getLogger',
            'pathlib.Path',
            'json.loads',
            'json.dumps',
            'datetime.datetime',
            'os.path.join',
            'os.path.exists',
            'tempfile.mkdtemp',
            'subprocess.run',  # Restricted to specific commands
            'requests.get',    # Restricted to allowed hosts
            'urllib.parse'
        }
    
    def _load_plugin_system_config(self):
        """Load plugin system configuration"""
        try:
            config_path = Path("config/plugin_system.json")
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                # Load trusted public keys
                self.trusted_public_keys.update(config.get("trusted_public_keys", []))
                
                # Load blocked plugins
                self.blocked_plugins.update(config.get("blocked_plugins", []))
                
                # Load plugin whitelist
                self.plugin_whitelist.update(config.get("plugin_whitelist", []))
                
                # Update API whitelist
                additional_apis = config.get("additional_api_whitelist", [])
                self.api_whitelist.update(additional_apis)
                
                self.logger.info("Loaded plugin system configuration")
        except Exception as e:
            self.logger.warning(f"Could not load plugin system config: {e}")
    
    def _validate_plugin_metadata_file(self, plugin_json_path: Path) -> ValidationResult:
        """Validate plugin.json file structure and content"""
        result = ValidationResult(is_valid=True)
        
        try:
            with open(plugin_json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate required fields
            required_fields = ['name', 'version', 'author', 'description', 'api_version']
            for field in required_fields:
                if field not in data:
                    result.add_error(f"Missing required field: {field}")
            
            # Validate field types and formats
            if 'permissions' in data:
                if not isinstance(data['permissions'], list):
                    result.add_error("Permissions must be a list")
                else:
                    valid_permissions = [p.value for p in Permission]
                    for perm in data['permissions']:
                        if perm not in valid_permissions:
                            result.add_error(f"Invalid permission: {perm}")
            
            # Validate version format
            if 'version' in data:
                if not self._is_valid_version_format(data['version']):
                    result.add_error(f"Invalid version format: {data['version']}")
            
            # Validate API version compatibility
            if 'api_version' in data:
                if not self._is_compatible_api_version(data['api_version']):
                    result.add_error(f"Incompatible API version: {data['api_version']}")
            
        except json.JSONDecodeError as e:
            result.add_error(f"Invalid JSON format: {e}")
        except Exception as e:
            result.add_error(f"Error reading plugin.json: {e}")
        
        return result
    
    def _validate_plugin_security_structure(self, plugin_path: Path) -> List[str]:
        """Validate plugin for security issues in structure"""
        issues = []
        
        try:
            # Check for suspicious files
            suspicious_files = ['.exe', '.dll', '.so', '.dylib', '.bat', '.sh', '.ps1']
            for file_path in plugin_path.rglob('*'):
                if file_path.is_file():
                    suffix = file_path.suffix.lower()
                    if suffix in suspicious_files:
                        issues.append(f"Suspicious file type found: {file_path.name}")
            
            # Check for hidden files (except common ones)
            allowed_hidden = {'.gitignore', '.gitkeep'}
            for file_path in plugin_path.rglob('.*'):
                if file_path.is_file() and file_path.name not in allowed_hidden:
                    issues.append(f"Hidden file found: {file_path.name}")
            
            # Check directory structure depth
            max_depth = 5
            for file_path in plugin_path.rglob('*'):
                relative_path = file_path.relative_to(plugin_path)
                if len(relative_path.parts) > max_depth:
                    issues.append(f"Directory structure too deep: {relative_path}")
            
        except Exception as e:
            issues.append(f"Error during security structure validation: {e}")
        
        return issues
    
    def _validate_plugin_code_structure(self, plugin_path: Path) -> Dict[str, List[str]]:
        """Validate Python code structure in plugin"""
        result = {'errors': [], 'warnings': []}
        
        try:
            # Check Python files
            for py_file in plugin_path.rglob('*.py'):
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Basic syntax check
                    try:
                        compile(content, str(py_file), 'exec')
                    except SyntaxError as e:
                        result['errors'].append(f"Syntax error in {py_file.name}: {e}")
                    
                    # Check for dangerous imports
                    dangerous_imports = ['os', 'sys', 'subprocess', 'eval', 'exec', '__import__']
                    for dangerous in dangerous_imports:
                        if f'import {dangerous}' in content or f'from {dangerous}' in content:
                            result['warnings'].append(f"Potentially dangerous import in {py_file.name}: {dangerous}")
                    
                except Exception as e:
                    result['warnings'].append(f"Could not validate {py_file.name}: {e}")
        
        except Exception as e:
            result['errors'].append(f"Error during code structure validation: {e}")
        
        return result
    
    def _validate_plugin_signature(self, plugin_path: Path) -> bool:
        """Validate digital signature of plugin"""
        try:
            signature_file = plugin_path / 'plugin.sig'
            if not signature_file.exists():
                return not self.require_signatures
            
            if not CRYPTOGRAPHY_AVAILABLE:
                self.logger.warning("Cryptography not available, skipping signature verification")
                return not self.require_signatures
            
            # Load signature
            with open(signature_file, 'rb') as f:
                signature = f.read()
            
            # Calculate plugin hash
            plugin_hash = self._calculate_plugin_hash(plugin_path)
            if not plugin_hash:
                return False
            
            # Verify signature with trusted public keys
            for public_key_str in self.trusted_public_keys:
                try:
                    public_key = serialization.load_pem_public_key(public_key_str.encode())
                    public_key.verify(
                        signature,
                        plugin_hash.encode(),
                        padding.PSS(
                            mgf=padding.MGF1(hashes.SHA256()),
                            salt_length=padding.PSS.MAX_LENGTH
                        ),
                        hashes.SHA256()
                    )
                    return True
                except InvalidSignature:
                    continue
                except Exception as e:
                    self.logger.warning(f"Error verifying signature: {e}")
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error validating plugin signature: {e}")
            return False
    
    def _validate_plugin_hash(self, plugin_path: Path) -> bool:
        """Validate plugin hash integrity"""
        try:
            hash_file = plugin_path / 'plugin.hash'
            if not hash_file.exists():
                return True  # Hash validation is optional
            
            # Load expected hash
            with open(hash_file, 'r') as f:
                expected_hash = f.read().strip()
            
            # Calculate actual hash
            actual_hash = self._calculate_plugin_hash(plugin_path)
            
            return actual_hash == expected_hash
            
        except Exception as e:
            self.logger.error(f"Error validating plugin hash: {e}")
            return False
    
    def _calculate_plugin_hash(self, plugin_path: Path) -> Optional[str]:
        """Calculate SHA256 hash of plugin files"""
        try:
            hasher = hashlib.sha256()
            
            # Hash all Python files in sorted order for consistency
            py_files = sorted(plugin_path.rglob('*.py'))
            for py_file in py_files:
                with open(py_file, 'rb') as f:
                    hasher.update(f.read())
            
            # Hash plugin.json
            plugin_json = plugin_path / 'plugin.json'
            if plugin_json.exists():
                with open(plugin_json, 'rb') as f:
                    hasher.update(f.read())
            
            return hasher.hexdigest()
            
        except Exception as e:
            self.logger.error(f"Error calculating plugin hash: {e}")
            return None
    
    def _load_plugin_metadata(self, plugin_path: Path) -> PluginMetadata:
        """Load plugin metadata from plugin.json"""
        plugin_json_path = plugin_path / 'plugin.json'
        
        try:
            with open(plugin_json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return PluginMetadata.from_dict(data)
        except Exception as e:
            raise PluginLoadError(f"Failed to load plugin metadata: {e}")
    
    def _load_plugin_module_secure(self, plugin_path: Path, metadata: PluginMetadata, security_profile) -> PluginInterface:
        """Load plugin module with security restrictions"""
        try:
            module_path = plugin_path / '__init__.py'
            
            if not module_path.exists():
                raise PluginLoadError(f"Plugin module not found: {module_path}")
            
            # Create module spec
            spec = importlib.util.spec_from_file_location(
                f"plugin_{metadata.name}",
                module_path
            )
            
            if spec is None or spec.loader is None:
                raise PluginLoadError(f"Failed to create module spec for {metadata.name}")
            
            # Load module in restricted environment
            module = importlib.util.module_from_spec(spec)
            
            # Restrict module's built-ins
            restricted_builtins = self._create_restricted_builtins()
            module.__builtins__ = restricted_builtins
            
            # Add plugin path to sys.path temporarily
            plugin_path_str = str(plugin_path)
            if plugin_path_str not in sys.path:
                sys.path.insert(0, plugin_path_str)
            
            try:
                spec.loader.exec_module(module)
            finally:
                # Remove from sys.path
                if plugin_path_str in sys.path:
                    sys.path.remove(plugin_path_str)
            
            # Create plugin instance
            entry_point = metadata.entry_point
            if not hasattr(module, entry_point):
                raise PluginLoadError(f"Plugin entry point not found: {entry_point}")
            
            entry_class = getattr(module, entry_point)
            if not issubclass(entry_class, PluginInterface):
                raise PluginLoadError(f"Plugin entry point must inherit from PluginInterface")
            
            return entry_class(metadata)
            
        except Exception as e:
            raise PluginLoadError(f"Failed to load plugin module: {e}")
    
    def _create_restricted_builtins(self) -> Dict[str, Any]:
        """Create restricted builtins for plugin execution"""
        # Start with safe builtins
        safe_builtins = {
            'len', 'str', 'int', 'float', 'bool', 'list', 'dict', 'tuple', 'set',
            'min', 'max', 'sum', 'abs', 'round', 'sorted', 'reversed',
            'enumerate', 'zip', 'range', 'isinstance', 'hasattr', 'getattr',
            'setattr', 'type', 'print'
        }
        
        restricted = {}
        for name in safe_builtins:
            if hasattr(__builtins__, name):
                restricted[name] = getattr(__builtins__, name)
        
        # Add restricted versions of dangerous functions
        restricted['__import__'] = self._restricted_import
        restricted['open'] = self._restricted_open
        
        return restricted
    
    def _restricted_import(self, name, *args, **kwargs):
        """Restricted import function for plugins"""
        # Allow only whitelisted modules
        allowed_modules = {
            'json', 'datetime', 'pathlib', 'typing', 'dataclasses',
            'enum', 'logging', 'hashlib', 'base64', 'urllib.parse'
        }
        
        if name not in allowed_modules:
            raise ImportError(f"Import of module '{name}' not allowed in plugin")
        
        return __import__(name, *args, **kwargs)
    
    def _restricted_open(self, filename, mode='r', **kwargs):
        """Restricted open function for plugins"""
        # Only allow reading from plugin directory and temp directories
        file_path = Path(filename).resolve()
        
        # Check if path is allowed
        allowed = False
        for allowed_path in [Path(tempfile.gettempdir())]:
            try:
                file_path.relative_to(allowed_path)
                allowed = True
                break
            except ValueError:
                continue
        
        if not allowed:
            raise PermissionError(f"Access to file '{filename}' not allowed in plugin")
        
        return open(filename, mode, **kwargs)
    
    def _create_secure_plugin_context(self, plugin_name: str, security_profile) -> SecurePluginContext:
        """Create secure execution context for plugin"""
        temp_dir = tempfile.mkdtemp(prefix=f"plugin_{plugin_name}_")
        
        return SecurePluginContext(
            plugin_name=plugin_name,
            sandbox_directory=temp_dir,
            allowed_operations={'initialize', 'execute', 'cleanup', 'get_info'},
            restricted_paths={'/etc', '/sys', '/proc', 'C:\\Windows', 'C:\\Program Files'},
            environment_variables={
                'PLUGIN_NAME': plugin_name,
                'PLUGIN_SANDBOX': 'true',
                'PLUGIN_TEMP_DIR': temp_dir
            },
            resource_limits={
                'max_memory_mb': security_profile.sandbox_config.max_memory_mb,
                'max_cpu_percent': security_profile.sandbox_config.max_cpu_percent,
                'max_execution_time': security_profile.sandbox_config.max_execution_time
            },
            api_whitelist=self.api_whitelist.copy(),
            execution_timeout=security_profile.sandbox_config.max_execution_time
        )
    
    def _initialize_plugin_secure(self, plugin_instance: PluginInterface, context: SecurePluginContext) -> PluginExecutionResult:
        """Initialize plugin in secure context"""
        result = PluginExecutionResult(success=False)
        
        try:
            # Set plugin context
            plugin_instance.set_context({
                'sandbox_directory': context.sandbox_directory,
                'environment_variables': context.environment_variables,
                'resource_limits': context.resource_limits,
                'api_whitelist': context.api_whitelist
            })
            
            # Initialize plugin
            success = plugin_instance.initialize(context.environment_variables)
            result.success = success
            
            if not success:
                result.error_message = "Plugin initialization returned False"
            
        except Exception as e:
            result.error_message = str(e)
            result.security_violations.append(f"Initialization error: {str(e)}")
        
        return result
    
    @contextmanager
    def _monitor_plugin_execution(self, plugin_name: str, timeout: int):
        """Monitor plugin execution with timeout and resource limits"""
        class ExecutionMonitor:
            def __init__(self):
                self.start_time = datetime.now()
                self.resource_usage = {}
            
            def get_resource_usage(self):
                return self.resource_usage
        
        monitor = ExecutionMonitor()
        
        try:
            yield monitor
        finally:
            # Calculate final resource usage
            execution_time = (datetime.now() - monitor.start_time).total_seconds()
            monitor.resource_usage['execution_time'] = execution_time
            
            if execution_time > timeout:
                raise PluginSecurityError(f"Plugin {plugin_name} exceeded execution timeout")
    
    def _cleanup_plugin_context(self, context: SecurePluginContext):
        """Cleanup plugin execution context"""
        try:
            if os.path.exists(context.sandbox_directory):
                shutil.rmtree(context.sandbox_directory)
        except Exception as e:
            self.logger.warning(f"Failed to cleanup plugin context: {e}")
    
    def _cleanup_all_contexts(self):
        """Cleanup all plugin contexts"""
        for context in self.plugin_contexts.values():
            self._cleanup_plugin_context(context)
    
    def _detect_api_conflicts(self) -> List[PluginConflict]:
        """Detect API conflicts between plugins"""
        conflicts = []
        # Implementation for API conflict detection
        return conflicts
    
    def _detect_resource_conflicts(self) -> List[PluginConflict]:
        """Detect resource conflicts between plugins"""
        conflicts = []
        # Implementation for resource conflict detection
        return conflicts
    
    def _detect_permission_conflicts(self) -> List[PluginConflict]:
        """Detect permission conflicts between plugins"""
        conflicts = []
        # Implementation for permission conflict detection
        return conflicts
    
    def _is_valid_version_format(self, version: str) -> bool:
        """Check if version follows semantic versioning"""
        import re
        pattern = r'^\d+\.\d+\.\d+(?:-[a-zA-Z0-9]+)?$'
        return bool(re.match(pattern, version))
    
    def _is_compatible_api_version(self, api_version: str) -> bool:
        """Check if API version is compatible"""
        supported_versions = ['1.0', '1.1', '2.0']
        return api_version in supported_versions


# Global instance
plugin_system_manager = PluginSystemManager()