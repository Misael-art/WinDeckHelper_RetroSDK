"""Plugin Base Interface and Core Classes

This module defines the base interfaces and core classes for the plugin system,
providing the foundation for extensible plugin architecture.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Union
from enum import Enum
import json
import hashlib
from pathlib import Path
try:
    from .version_manager import version_manager
except ImportError:
    from version_manager import version_manager


class PluginStatus(Enum):
    """Plugin status enumeration"""
    UNKNOWN = "unknown"
    LOADED = "loaded"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    DISABLED = "disabled"


class Permission(Enum):
    """Plugin permission levels"""
    READ_FILESYSTEM = "read_filesystem"
    WRITE_FILESYSTEM = "write_filesystem"
    NETWORK_ACCESS = "network_access"
    REGISTRY_READ = "registry_read"
    REGISTRY_WRITE = "registry_write"
    SYSTEM_COMMANDS = "system_commands"
    ENVIRONMENT_VARIABLES = "environment_variables"
    PRIVILEGED_OPERATIONS = "privileged_operations"


@dataclass
class PluginMetadata:
    """Plugin metadata structure"""
    name: str
    version: str
    author: str
    description: str
    api_version: str
    dependencies: List[str] = field(default_factory=list)
    permissions: List[Permission] = field(default_factory=list)
    signature: Optional[str] = None
    entry_point: str = "main"
    min_system_version: Optional[str] = None
    max_system_version: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary"""
        return {
            'name': self.name,
            'version': self.version,
            'author': self.author,
            'description': self.description,
            'api_version': self.api_version,
            'dependencies': self.dependencies,
            'permissions': [p.value for p in self.permissions],
            'signature': self.signature,
            'entry_point': self.entry_point,
            'min_system_version': self.min_system_version,
            'max_system_version': self.max_system_version
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PluginMetadata':
        """Create metadata from dictionary"""
        permissions = [Permission(p) for p in data.get('permissions', [])]
        return cls(
            name=data['name'],
            version=data['version'],
            author=data['author'],
            description=data['description'],
            api_version=data['api_version'],
            dependencies=data.get('dependencies', []),
            permissions=permissions,
            signature=data.get('signature'),
            entry_point=data.get('entry_point', 'main'),
            min_system_version=data.get('min_system_version'),
            max_system_version=data.get('max_system_version')
        )


@dataclass
class ValidationResult:
    """Plugin validation result"""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def add_error(self, error: str):
        """Add validation error"""
        self.errors.append(error)
        self.is_valid = False
    
    def add_warning(self, warning: str):
        """Add validation warning"""
        self.warnings.append(warning)


@dataclass
class PluginConflict:
    """Plugin conflict information"""
    plugin_a: str
    plugin_b: str
    conflict_type: str
    description: str
    severity: str = "medium"  # low, medium, high, critical


class PluginInterface(ABC):
    """Base interface for all plugins"""
    
    def __init__(self, metadata: PluginMetadata):
        self.metadata = metadata
        self.status = PluginStatus.UNKNOWN
        self._context: Optional[Dict[str, Any]] = None
    
    @abstractmethod
    def initialize(self, context: Dict[str, Any]) -> bool:
        """Initialize the plugin with given context"""
        pass
    
    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """Execute the plugin's main functionality"""
        pass
    
    @abstractmethod
    def cleanup(self) -> bool:
        """Cleanup plugin resources"""
        pass
    
    def get_metadata(self) -> PluginMetadata:
        """Get plugin metadata"""
        return self.metadata
    
    def get_status(self) -> PluginStatus:
        """Get current plugin status"""
        return self.status
    
    def set_context(self, context: Dict[str, Any]):
        """Set plugin execution context"""
        self._context = context
    
    def get_context(self) -> Optional[Dict[str, Any]]:
        """Get plugin execution context"""
        return self._context


class RuntimePlugin(PluginInterface):
    """Base class for runtime plugins"""
    
    @abstractmethod
    def install_runtime(self) -> bool:
        """Install the runtime"""
        pass
    
    @abstractmethod
    def configure_runtime(self) -> bool:
        """Configure the runtime"""
        pass
    
    @abstractmethod
    def validate_runtime(self) -> bool:
        """Validate runtime installation"""
        pass
    
    @abstractmethod
    def get_runtime_info(self) -> Dict[str, Any]:
        """Get runtime information"""
        pass


class UtilityPlugin(PluginInterface):
    """Base class for utility plugins"""
    
    @abstractmethod
    def get_utility_info(self) -> Dict[str, Any]:
        """Get utility information"""
        pass


class PluginValidator:
    """Plugin validation system"""
    
    def __init__(self):
        self.required_metadata_fields = [
            'name', 'version', 'author', 'description', 'api_version'
        ]
        self.supported_api_versions = ['1.0', '1.1']
    
    def validate_metadata(self, metadata: PluginMetadata) -> ValidationResult:
        """Validate plugin metadata"""
        result = ValidationResult(is_valid=True)
        
        # Check required fields
        for field in self.required_metadata_fields:
            if not getattr(metadata, field, None):
                result.add_error(f"Missing required field: {field}")
        
        # Check API version compatibility
        if metadata.api_version not in self.supported_api_versions:
            result.add_error(f"Unsupported API version: {metadata.api_version}")
        
        # Validate version format (basic semver check)
        if not self._is_valid_version(metadata.version):
            result.add_error(f"Invalid version format: {metadata.version}")
        
        # Check for dangerous permissions
        dangerous_permissions = [
            Permission.REGISTRY_WRITE,
            Permission.SYSTEM_COMMANDS,
            Permission.PRIVILEGED_OPERATIONS
        ]
        
        for perm in metadata.permissions:
            if perm in dangerous_permissions:
                result.add_warning(f"Plugin requests dangerous permission: {perm.value}")
        
        return result
    
    def validate_plugin_structure(self, plugin_path: Path) -> ValidationResult:
        """Validate plugin file structure"""
        result = ValidationResult(is_valid=True)
        
        if not plugin_path.exists():
            result.add_error(f"Plugin path does not exist: {plugin_path}")
            return result
        
        # Check for required files
        required_files = ['plugin.json', '__init__.py']
        for file_name in required_files:
            file_path = plugin_path / file_name
            if not file_path.exists():
                result.add_error(f"Missing required file: {file_name}")
        
        # Check plugin.json format
        plugin_json_path = plugin_path / 'plugin.json'
        if plugin_json_path.exists():
            try:
                with open(plugin_json_path, 'r', encoding='utf-8') as f:
                    plugin_data = json.load(f)
                    metadata = PluginMetadata.from_dict(plugin_data)
                    metadata_result = self.validate_metadata(metadata)
                    result.errors.extend(metadata_result.errors)
                    result.warnings.extend(metadata_result.warnings)
                    if not metadata_result.is_valid:
                        result.is_valid = False
            except json.JSONDecodeError as e:
                result.add_error(f"Invalid JSON in plugin.json: {e}")
            except Exception as e:
                result.add_error(f"Error reading plugin.json: {e}")
        
        return result
    
    def _is_valid_version(self, version: str) -> bool:
        """Check if version follows semantic versioning"""
        try:
            parsed = version_manager.parse_version(version)
            return parsed is not None
        except Exception:
            return False


class DependencyResolver:
    """Plugin dependency resolution system"""
    
    def __init__(self):
        self.dependency_graph: Dict[str, List[str]] = {}
        self.plugin_registry: Dict[str, PluginMetadata] = {}
    
    def add_plugin(self, metadata: PluginMetadata):
        """Add plugin to dependency graph"""
        self.plugin_registry[metadata.name] = metadata
        self.dependency_graph[metadata.name] = metadata.dependencies.copy()
    
    def resolve_dependencies(self, plugin_name: str) -> List[str]:
        """Resolve plugin dependencies in correct order"""
        resolved = []
        visited = set()
        temp_visited = set()
        
        def visit(name: str):
            if name in temp_visited:
                raise ValueError(f"Circular dependency detected involving {name}")
            if name in visited:
                return
            
            temp_visited.add(name)
            
            # Visit dependencies first
            for dep in self.dependency_graph.get(name, []):
                if dep not in self.plugin_registry:
                    raise ValueError(f"Missing dependency: {dep}")
                visit(dep)
            
            temp_visited.remove(name)
            visited.add(name)
            resolved.append(name)
        
        visit(plugin_name)
        return resolved
    
    def check_conflicts(self, plugins: List[PluginMetadata]) -> List[PluginConflict]:
        """Check for conflicts between plugins"""
        conflicts = []
        
        # Check for name conflicts
        names = {}
        for plugin in plugins:
            if plugin.name in names:
                conflicts.append(PluginConflict(
                    plugin_a=names[plugin.name].name,
                    plugin_b=plugin.name,
                    conflict_type="name_conflict",
                    description=f"Multiple plugins with same name: {plugin.name}",
                    severity="critical"
                ))
            names[plugin.name] = plugin
        
        # Check for version conflicts in dependencies
        for plugin in plugins:
            for dep in plugin.dependencies:
                dep_parts = dep.split('>=') if '>=' in dep else dep.split('==')
                if len(dep_parts) == 2:
                    dep_name, required_version = dep_parts
                    if dep_name in names:
                        installed_version = names[dep_name].version
                        if not self._version_satisfies(installed_version, dep, required_version):
                            conflicts.append(PluginConflict(
                                plugin_a=plugin.name,
                                plugin_b=dep_name,
                                conflict_type="version_conflict",
                                description=f"{plugin.name} requires {dep} but {installed_version} is available",
                                severity="high"
                            ))
        
        return conflicts
    
    def _version_satisfies(self, installed: str, operator: str, required: str) -> bool:
        """Check if installed version satisfies requirement"""
        try:
            # Use centralized version manager for compatibility checking
            requirement = f"{operator}{required}"
            return version_manager.is_compatible(installed, requirement)
        except Exception:
            return False