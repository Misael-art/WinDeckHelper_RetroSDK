#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Runtime Catalog Manager - Foundation (New Version)
Manages runtime components with automatic configuration and environment setup.
"""

import os
import sys
import json
import logging
import platform
import subprocess
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Set, Tuple, Union
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

# Import winreg safely for Windows
try:
    import winreg
except ImportError:
    winreg = None


class InstallationType(Enum):
    """Types of installation methods supported."""
    MSI = "msi"
    EXE = "exe"
    ZIP = "zip"
    PORTABLE = "portable"
    PACKAGE_MANAGER = "package_manager"


class RuntimeStatus(Enum):
    """Status of runtime installation."""
    NOT_INSTALLED = "not_installed"
    INSTALLED = "installed"
    OUTDATED = "outdated"
    CORRUPTED = "corrupted"
    INSTALLING = "installing"
    FAILED = "failed"


@dataclass
class RuntimeConfig:
    """Configuration for a runtime component."""
    name: str
    version: str
    download_url: str
    mirrors: List[str] = field(default_factory=list)
    installation_type: InstallationType = InstallationType.EXE
    environment_variables: Dict[str, str] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    post_install_scripts: List[str] = field(default_factory=list)
    validation_commands: List[str] = field(default_factory=list)
    registry_keys: List[str] = field(default_factory=list)
    executable_paths: List[str] = field(default_factory=list)
    size_mb: int = 0
    description: str = ""


@dataclass
class ValidationResult:
    """Result of runtime validation."""
    is_valid: bool
    version_detected: Optional[str] = None
    issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


class Runtime(ABC):
    """Base interface for all runtime implementations."""
    
    def __init__(self, config: RuntimeConfig):
        self.config = config
        self.logger = logging.getLogger(f"runtime.{config.name}")
    
    @abstractmethod
    def install(self) -> bool:
        """Install the runtime component."""
        pass
    
    @abstractmethod
    def configure_environment(self) -> bool:
        """Configure environment variables and system settings."""
        pass
    
    @abstractmethod
    def validate_installation(self) -> ValidationResult:
        """Validate that the runtime is properly installed."""
        pass
    
    @abstractmethod
    def get_installed_version(self) -> Optional[str]:
        """Get the currently installed version."""
        pass
    
    @abstractmethod
    def uninstall(self) -> bool:
        """Uninstall the runtime component."""
        pass


class RuntimeRegistry:
    """Registry for managing runtime configurations and instances."""
    
    def __init__(self):
        self.configs: Dict[str, RuntimeConfig] = {}
        self.instances: Dict[str, Runtime] = {}
        self.logger = logging.getLogger("runtime_registry")
    
    def register_config(self, config: RuntimeConfig) -> None:
        """Register a runtime configuration."""
        self.configs[config.name] = config
        self.logger.info(f"Registered runtime config: {config.name} v{config.version}")
    
    def get_config(self, name: str) -> Optional[RuntimeConfig]:
        """Get runtime configuration by name."""
        return self.configs.get(name)
    
    def list_runtimes(self) -> List[str]:
        """List all registered runtime names."""
        return list(self.configs.keys())
    
    def get_dependencies(self, runtime_name: str) -> List[str]:
        """Get dependencies for a runtime."""
        config = self.get_config(runtime_name)
        return config.dependencies if config else []
    
    def resolve_dependency_order(self, runtime_names: List[str]) -> List[str]:
        """Resolve installation order based on dependencies."""
        resolved = []
        visited = set()
        temp_visited = set()
        
        def visit(name: str):
            if name in temp_visited:
                raise ValueError(f"Circular dependency detected involving {name}")
            if name in visited:
                return
            
            temp_visited.add(name)
            dependencies = self.get_dependencies(name)
            
            for dep in dependencies:
                if dep in self.configs:
                    visit(dep)
            
            temp_visited.remove(name)
            visited.add(name)
            resolved.append(name)
        
        for name in runtime_names:
            if name not in visited:
                visit(name)
        
        return resolved


class RuntimeCatalogManager:
    """Main manager for runtime catalog operations."""
    
    def __init__(self, config_dir: Optional[Path] = None):
        self.config_dir = config_dir or Path("config/runtimes")
        self.registry = RuntimeRegistry()
        self.logger = logging.getLogger("runtime_catalog_manager")
        
        # Ensure config directory exists
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Load configurations
        self._load_configurations()
    
    def _load_configurations(self) -> None:
        """Load runtime configurations from config files."""
        try:
            # Load default runtime configurations
            default_configs = self._get_default_runtime_configs()
            for config in default_configs:
                self.registry.register_config(config)
            
            self.logger.info(f"Loaded {len(self.registry.configs)} runtime configurations")
        
        except Exception as e:
            self.logger.error(f"Error loading configurations: {e}")
    
    def _get_default_runtime_configs(self) -> List[RuntimeConfig]:
        """Get default runtime configurations for essential runtimes."""
        return [
            RuntimeConfig(
                name="git",
                version="2.47.1",
                download_url="https://github.com/git-for-windows/git/releases/download/v2.47.1.windows.1/Git-2.47.1-64-bit.exe",
                mirrors=[
                    "https://git-scm.com/download/win",
                    "https://github.com/git-for-windows/git/releases/latest"
                ],
                installation_type=InstallationType.EXE,
                environment_variables={},
                validation_commands=["git --version"],
                executable_paths=["git.exe"],
                size_mb=50,
                description="Git version control system"
            ),
            RuntimeConfig(
                name="dotnet_sdk",
                version="8.0",
                download_url="https://download.visualstudio.microsoft.com/download/pr/b280d97f-25a9-4ab7-8a12-8291aa3af117/a7de3d8d6f4c8e9c6e8b8c8f8e8f8e8f/dotnet-sdk-8.0.404-win-x64.exe",
                mirrors=[
                    "https://dotnet.microsoft.com/download/dotnet/8.0",
                    "https://github.com/dotnet/core/releases"
                ],
                installation_type=InstallationType.EXE,
                environment_variables={
                    "DOTNET_ROOT": "%ProgramFiles%\\dotnet"
                },
                validation_commands=["dotnet --version"],
                executable_paths=["dotnet.exe"],
                size_mb=200,
                description=".NET SDK 8.0"
            ),
            RuntimeConfig(
                name="java_jdk",
                version="21",
                download_url="https://download.oracle.com/java/21/latest/jdk-21_windows-x64_bin.exe",
                mirrors=[
                    "https://adoptium.net/temurin/releases/",
                    "https://www.oracle.com/java/technologies/downloads/"
                ],
                installation_type=InstallationType.EXE,
                environment_variables={
                    "JAVA_HOME": "%ProgramFiles%\\Java\\jdk-21"
                },
                validation_commands=["java -version", "javac -version"],
                executable_paths=["java.exe", "javac.exe"],
                registry_keys=["HKEY_LOCAL_MACHINE\\SOFTWARE\\JavaSoft\\JDK"],
                size_mb=300,
                description="Java JDK 21"
            ),
            RuntimeConfig(
                name="vcpp_redist",
                version="2015-2022",
                download_url="https://aka.ms/vs/17/release/vc_redist.x64.exe",
                mirrors=[
                    "https://docs.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist"
                ],
                installation_type=InstallationType.EXE,
                validation_commands=[],
                registry_keys=[
                    "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\VisualStudio\\14.0\\VC\\Runtimes\\x64",
                    "HKEY_LOCAL_MACHINE\\SOFTWARE\\WOW6432Node\\Microsoft\\VisualStudio\\14.0\\VC\\Runtimes\\x64"
                ],
                size_mb=25,
                description="Visual C++ Redistributable 2015-2022"
            ),
            RuntimeConfig(
                name="anaconda",
                version="2024.10",
                download_url="https://repo.anaconda.com/archive/Anaconda3-2024.10-1-Windows-x86_64.exe",
                mirrors=[
                    "https://www.anaconda.com/download",
                    "https://repo.anaconda.com/archive/"
                ],
                installation_type=InstallationType.EXE,
                environment_variables={
                    "CONDA_DEFAULT_ENV": "base"
                },
                validation_commands=["conda --version", "python --version"],
                executable_paths=["conda.exe", "python.exe"],
                size_mb=500,
                description="Anaconda Python Distribution"
            ),
            RuntimeConfig(
                name="dotnet_desktop",
                version="8.0",
                download_url="https://download.visualstudio.microsoft.com/download/pr/b280d97f-25a9-4ab7-8a12-8291aa3af117/windowsdesktop-runtime-8.0.11-win-x64.exe",
                mirrors=[
                    "https://dotnet.microsoft.com/download/dotnet/8.0"
                ],
                installation_type=InstallationType.EXE,
                validation_commands=["dotnet --list-runtimes"],
                registry_keys=["HKEY_LOCAL_MACHINE\\SOFTWARE\\WOW6432Node\\dotnet\\Setup\\InstalledVersions\\x64\\sharedhost"],
                size_mb=50,
                description=".NET Desktop Runtime 8.0"
            ),
            RuntimeConfig(
                name="powershell7",
                version="7.4.6",
                download_url="https://github.com/PowerShell/PowerShell/releases/download/v7.4.6/PowerShell-7.4.6-win-x64.msi",
                mirrors=[
                    "https://github.com/PowerShell/PowerShell/releases/latest"
                ],
                installation_type=InstallationType.MSI,
                validation_commands=["pwsh --version"],
                executable_paths=["pwsh.exe"],
                size_mb=100,
                description="PowerShell 7"
            )
        ]
    
    def list_available_runtimes(self) -> List[str]:
        """List all available runtime names."""
        return self.registry.list_runtimes()
    
    def get_runtime_info(self, runtime_name: str) -> Optional[RuntimeConfig]:
        """Get configuration information for a runtime."""
        return self.registry.get_config(runtime_name)
    
    def calculate_total_size(self, runtime_names: List[str]) -> int:
        """Calculate total size in MB for selected runtimes."""
        total_size = 0
        for name in runtime_names:
            config = self.registry.get_config(name)
            if config:
                total_size += config.size_mb
        return total_size
    
    def export_configuration(self, runtime_name: str, file_path: Path) -> bool:
        """Export runtime configuration to a JSON file."""
        try:
            config = self.registry.get_config(runtime_name)
            if not config:
                return False
            
            # Convert dataclass to dict for JSON serialization
            config_dict = {
                'name': config.name,
                'version': config.version,
                'download_url': config.download_url,
                'mirrors': config.mirrors,
                'installation_type': config.installation_type.value,
                'environment_variables': config.environment_variables,
                'dependencies': config.dependencies,
                'post_install_scripts': config.post_install_scripts,
                'validation_commands': config.validation_commands,
                'registry_keys': config.registry_keys,
                'executable_paths': config.executable_paths,
                'size_mb': config.size_mb,
                'description': config.description
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)
            
            return True
        
        except Exception as e:
            self.logger.error(f"Error exporting configuration: {e}")
            return False


# Test the module when run directly
if __name__ == "__main__":
    print("Testing RuntimeCatalogManager...")
    manager = RuntimeCatalogManager()
    print(f"Available runtimes: {manager.list_available_runtimes()}")
    print("RuntimeCatalogManager test completed successfully!")