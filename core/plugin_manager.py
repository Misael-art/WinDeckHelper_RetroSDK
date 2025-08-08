"""
Plugin Manager

This module implements the core plugin management system, providing plugin loading,
validation, dependency resolution, and lifecycle management capabilities.
"""

import os
import sys
import json
import importlib.util
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Type
from dataclasses import dataclass
import threading
from concurrent.futures import ThreadPoolExecutor, Future

from .plugin_base import (
    PluginInterface, PluginMetadata, PluginStatus, ValidationResult,
    PluginConflict, PluginValidator, DependencyResolver, RuntimePlugin,
    UtilityPlugin, Permission
)


@dataclass
class LoadedPlugin:
    """Container for loaded plugin information"""
    metadata: PluginMetadata
    instance: PluginInterface
    module: Any
    path: Path
    status: PluginStatus
    load_time: float
    error_message: Optional[str] = None


class PluginLoadError(Exception):
    """Exception raised when plugin loading fails"""
    pass


class PluginManager:
    """
    Core plugin management system
    
    Handles plugin discovery, loading, validation, dependency resolution,
    and lifecycle management for the Environment Dev system.
    """
    
    def __init__(self, plugin_directories: Optional[List[str]] = None):
        """
        Initialize plugin manager
        
        Args:
            plugin_directories: List of directories to search for plugins
        """
        self.logger = logging.getLogger(__name__)
        
        # Plugin storage
        self.loaded_plugins: Dict[str, LoadedPlugin] = {}
        self.plugin_registry: Dict[str, PluginMetadata] = {}
        
        # Plugin directories
        self.plugin_directories = plugin_directories or [
            "plugins",
            "env_dev/plugins",
            os.path.expanduser("~/.environment_dev/plugins")
        ]
        
        # Core components
        self.validator = PluginValidator()
        self.dependency_resolver = DependencyResolver()
        
        # Thread safety
        self._lock = threading.RLock()
        self._executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="plugin")
        
        # Plugin API context
        self._api_context = self._create_api_context()
        
        self.logger.info("Plugin manager initialized")
    
    def discover_plugins(self) -> List[Path]:
        """
        Discover all available plugins in configured directories
        
        Returns:
            List of plugin directory paths
        """
        discovered_plugins = []
        
        for directory in self.plugin_directories:
            plugin_dir = Path(directory)
            if not plugin_dir.exists():
                self.logger.debug(f"Plugin directory does not exist: {plugin_dir}")
                continue
            
            # Look for plugin directories (containing plugin.json)
            for item in plugin_dir.iterdir():
                if item.is_dir():
                    plugin_json = item / "plugin.json"
                    if plugin_json.exists():
                        discovered_plugins.append(item)
                        self.logger.debug(f"Discovered plugin: {item}")
        
        self.logger.info(f"Discovered {len(discovered_plugins)} plugins")
        return discovered_plugins
    
    def load_plugin(self, plugin_path: Path) -> LoadedPlugin:
        """
        Load a single plugin from the specified path
        
        Args:
            plugin_path: Path to plugin directory
            
        Returns:
            LoadedPlugin instance
            
        Raises:
            PluginLoadError: If plugin loading fails
        """
        with self._lock:
            try:
                import time
                start_time = time.time()
                
                # Validate plugin structure
                structure_result = self.validator.validate_plugin_structure(plugin_path)
                if not structure_result.is_valid:
                    raise PluginLoadError(f"Plugin structure validation failed: {structure_result.errors}")
                
                # Load plugin metadata
                metadata = self._load_plugin_metadata(plugin_path)
                
                # Validate metadata
                metadata_result = self.validator.validate_metadata(metadata)
                if not metadata_result.is_valid:
                    raise PluginLoadError(f"Plugin metadata validation failed: {metadata_result.errors}")
                
                # Check if plugin is already loaded
                if metadata.name in self.loaded_plugins:
                    existing = self.loaded_plugins[metadata.name]
                    if existing.metadata.version == metadata.version:
                        self.logger.warning(f"Plugin {metadata.name} v{metadata.version} already loaded")
                        return existing
                    else:
                        self.logger.info(f"Updating plugin {metadata.name} from v{existing.metadata.version} to v{metadata.version}")
                        self.unload_plugin(metadata.name)
                
                # Load plugin module
                module = self._load_plugin_module(plugin_path, metadata)
                
                # Create plugin instance
                instance = self._create_plugin_instance(module, metadata)
                
                # Initialize plugin
                if not instance.initialize(self._api_context):
                    raise PluginLoadError(f"Plugin initialization failed: {metadata.name}")
                
                # Create loaded plugin container
                loaded_plugin = LoadedPlugin(
                    metadata=metadata,
                    instance=instance,
                    module=module,
                    path=plugin_path,
                    status=PluginStatus.LOADED,
                    load_time=time.time() - start_time
                )
                
                # Register plugin
                self.loaded_plugins[metadata.name] = loaded_plugin
                self.plugin_registry[metadata.name] = metadata
                self.dependency_resolver.add_plugin(metadata)
                
                self.logger.info(f"Successfully loaded plugin: {metadata.name} v{metadata.version}")
                return loaded_plugin
                
            except Exception as e:
                error_msg = f"Failed to load plugin from {plugin_path}: {str(e)}"
                self.logger.error(error_msg)
                raise PluginLoadError(error_msg) from e
    
    def load_all_plugins(self) -> Dict[str, LoadedPlugin]:
        """
        Load all discovered plugins
        
        Returns:
            Dictionary of successfully loaded plugins
        """
        discovered = self.discover_plugins()
        loaded = {}
        failed = []
        
        # Load plugins in parallel
        futures: Dict[str, Future] = {}
        
        for plugin_path in discovered:
            future = self._executor.submit(self._safe_load_plugin, plugin_path)
            futures[str(plugin_path)] = future
        
        # Collect results
        for path_str, future in futures.items():
            try:
                result = future.result(timeout=30)  # 30 second timeout per plugin
                if result:
                    loaded[result.metadata.name] = result
            except Exception as e:
                failed.append((path_str, str(e)))
                self.logger.error(f"Failed to load plugin from {path_str}: {e}")
        
        # Resolve dependencies and activate plugins
        if loaded:
            self._resolve_and_activate_plugins(list(loaded.values()))
        
        self.logger.info(f"Loaded {len(loaded)} plugins successfully, {len(failed)} failed")
        return loaded
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """
        Unload a specific plugin
        
        Args:
            plugin_name: Name of plugin to unload
            
        Returns:
            True if successfully unloaded
        """
        with self._lock:
            if plugin_name not in self.loaded_plugins:
                self.logger.warning(f"Plugin not loaded: {plugin_name}")
                return False
            
            try:
                loaded_plugin = self.loaded_plugins[plugin_name]
                
                # Cleanup plugin
                if hasattr(loaded_plugin.instance, 'cleanup'):
                    loaded_plugin.instance.cleanup()
                
                # Remove from registries
                del self.loaded_plugins[plugin_name]
                if plugin_name in self.plugin_registry:
                    del self.plugin_registry[plugin_name]
                
                # Update dependency resolver
                if plugin_name in self.dependency_resolver.dependency_graph:
                    del self.dependency_resolver.dependency_graph[plugin_name]
                
                self.logger.info(f"Successfully unloaded plugin: {plugin_name}")
                return True
                
            except Exception as e:
                self.logger.error(f"Error unloading plugin {plugin_name}: {e}")
                return False
    
    def get_plugin(self, plugin_name: str) -> Optional[LoadedPlugin]:
        """Get loaded plugin by name"""
        return self.loaded_plugins.get(plugin_name)
    
    def get_plugins_by_type(self, plugin_type: Type[PluginInterface]) -> List[LoadedPlugin]:
        """Get all loaded plugins of specific type"""
        return [
            plugin for plugin in self.loaded_plugins.values()
            if isinstance(plugin.instance, plugin_type)
        ]
    
    def get_runtime_plugins(self) -> List[LoadedPlugin]:
        """Get all loaded runtime plugins"""
        return self.get_plugins_by_type(RuntimePlugin)
    
    def get_utility_plugins(self) -> List[LoadedPlugin]:
        """Get all loaded utility plugins"""
        return self.get_plugins_by_type(UtilityPlugin)
    
    def validate_plugin(self, plugin_path: Path) -> ValidationResult:
        """Validate plugin without loading it"""
        return self.validator.validate_plugin_structure(plugin_path)
    
    def detect_conflicts(self) -> List[PluginConflict]:
        """Detect conflicts between loaded plugins"""
        plugins = [p.metadata for p in self.loaded_plugins.values()]
        return self.dependency_resolver.check_conflicts(plugins)
    
    def get_plugin_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status information for all plugins"""
        status = {}
        for name, plugin in self.loaded_plugins.items():
            status[name] = {
                'name': plugin.metadata.name,
                'version': plugin.metadata.version,
                'status': plugin.status.value,
                'load_time': plugin.load_time,
                'path': str(plugin.path),
                'dependencies': plugin.metadata.dependencies,
                'permissions': [p.value for p in plugin.metadata.permissions],
                'error_message': plugin.error_message
            }
        return status
    
    def shutdown(self):
        """Shutdown plugin manager and cleanup resources"""
        self.logger.info("Shutting down plugin manager")
        
        # Unload all plugins
        plugin_names = list(self.loaded_plugins.keys())
        for name in plugin_names:
            self.unload_plugin(name)
        
        # Shutdown executor
        self._executor.shutdown(wait=True)
        
        self.logger.info("Plugin manager shutdown complete")
    
    def _load_plugin_metadata(self, plugin_path: Path) -> PluginMetadata:
        """Load plugin metadata from plugin.json"""
        plugin_json_path = plugin_path / "plugin.json"
        
        try:
            with open(plugin_json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return PluginMetadata.from_dict(data)
        except Exception as e:
            raise PluginLoadError(f"Failed to load plugin metadata: {e}")
    
    def _load_plugin_module(self, plugin_path: Path, metadata: PluginMetadata) -> Any:
        """Load plugin Python module"""
        module_path = plugin_path / "__init__.py"
        
        if not module_path.exists():
            raise PluginLoadError(f"Plugin module not found: {module_path}")
        
        try:
            spec = importlib.util.spec_from_file_location(
                f"plugin_{metadata.name}",
                module_path
            )
            if spec is None or spec.loader is None:
                raise PluginLoadError(f"Failed to create module spec for {metadata.name}")
            
            module = importlib.util.module_from_spec(spec)
            
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
            
            return module
            
        except Exception as e:
            raise PluginLoadError(f"Failed to load plugin module: {e}")
    
    def _create_plugin_instance(self, module: Any, metadata: PluginMetadata) -> PluginInterface:
        """Create plugin instance from loaded module"""
        entry_point = metadata.entry_point
        
        if not hasattr(module, entry_point):
            raise PluginLoadError(f"Plugin entry point not found: {entry_point}")
        
        entry_class = getattr(module, entry_point)
        
        if not issubclass(entry_class, PluginInterface):
            raise PluginLoadError(f"Plugin entry point must inherit from PluginInterface")
        
        try:
            return entry_class(metadata)
        except Exception as e:
            raise PluginLoadError(f"Failed to create plugin instance: {e}")
    
    def _safe_load_plugin(self, plugin_path: Path) -> Optional[LoadedPlugin]:
        """Safely load plugin with error handling"""
        try:
            return self.load_plugin(plugin_path)
        except Exception as e:
            self.logger.error(f"Failed to load plugin from {plugin_path}: {e}")
            return None
    
    def _resolve_and_activate_plugins(self, plugins: List[LoadedPlugin]):
        """Resolve dependencies and activate plugins in correct order"""
        try:
            # Build dependency graph
            for plugin in plugins:
                self.dependency_resolver.add_plugin(plugin.metadata)
            
            # Check for conflicts
            conflicts = self.detect_conflicts()
            if conflicts:
                critical_conflicts = [c for c in conflicts if c.severity == "critical"]
                if critical_conflicts:
                    self.logger.error(f"Critical plugin conflicts detected: {critical_conflicts}")
                    return
                else:
                    self.logger.warning(f"Plugin conflicts detected: {conflicts}")
            
            # Activate plugins in dependency order
            activated = set()
            for plugin in plugins:
                if plugin.metadata.name not in activated:
                    self._activate_plugin_with_dependencies(plugin.metadata.name, activated)
            
        except Exception as e:
            self.logger.error(f"Failed to resolve and activate plugins: {e}")
    
    def _activate_plugin_with_dependencies(self, plugin_name: str, activated: set):
        """Activate plugin and its dependencies recursively"""
        if plugin_name in activated:
            return
        
        if plugin_name not in self.loaded_plugins:
            self.logger.error(f"Cannot activate plugin {plugin_name}: not loaded")
            return
        
        plugin = self.loaded_plugins[plugin_name]
        
        # Activate dependencies first
        for dep in plugin.metadata.dependencies:
            if dep not in activated:
                self._activate_plugin_with_dependencies(dep, activated)
        
        # Activate this plugin
        try:
            plugin.status = PluginStatus.ACTIVE
            activated.add(plugin_name)
            self.logger.info(f"Activated plugin: {plugin_name}")
        except Exception as e:
            plugin.status = PluginStatus.ERROR
            plugin.error_message = str(e)
            self.logger.error(f"Failed to activate plugin {plugin_name}: {e}")
    
    def _create_api_context(self) -> Dict[str, Any]:
        """Create API context for plugins"""
        return {
            'version': '1.0',
            'system_info': {
                'platform': sys.platform,
                'python_version': sys.version,
            },
            'logger': self.logger,
            'plugin_manager': self
        }