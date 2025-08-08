"""
Plugin Registry System

This module provides plugin registration, discovery, and metadata management
capabilities for the plugin system.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from dataclasses import asdict
from datetime import datetime
import hashlib

from .plugin_base import PluginMetadata, ValidationResult, PluginValidator


class PluginRegistry:
    """
    Plugin registry for managing plugin metadata and discovery
    
    Maintains a registry of available plugins, their metadata, and provides
    search and discovery capabilities.
    """
    
    def __init__(self, registry_file: Optional[str] = None):
        """
        Initialize plugin registry
        
        Args:
            registry_file: Path to registry file (defaults to plugins/registry.json)
        """
        self.logger = logging.getLogger(__name__)
        
        # Registry file path
        self.registry_file = Path(registry_file or "plugins/registry.json")
        self.registry_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Registry data
        self.plugins: Dict[str, Dict[str, Any]] = {}
        self.categories: Dict[str, List[str]] = {}
        self.tags: Dict[str, Set[str]] = {}
        
        # Validator
        self.validator = PluginValidator()
        
        # Load existing registry
        self._load_registry()
        
        self.logger.info(f"Plugin registry initialized with {len(self.plugins)} plugins")
    
    def register_plugin(self, metadata: PluginMetadata, plugin_path: Path) -> bool:
        """
        Register a plugin in the registry
        
        Args:
            metadata: Plugin metadata
            plugin_path: Path to plugin directory
            
        Returns:
            True if successfully registered
        """
        try:
            # Validate metadata
            validation_result = self.