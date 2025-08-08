#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Package Manager Integrator - Advanced Package Manager Integration
Provides unified interface for npm, pip, conda, yarn, and pipenv operations.
"""

import os
import sys
import json
import logging
import platform
import subprocess
import tempfile
import shutil
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Set, Tuple, Union
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import re
import time


class PackageManagerType(Enum):
    """Types of supported package managers."""
    NPM = "npm"
    YARN = "yarn"
    PIP = "pip"
    PIPENV = "pipenv"
    CONDA = "conda"
    POETRY = "poetry"


class InstallationScope(Enum):
    """Scope of package installation."""
    GLOBAL = "global"
    LOCAL = "local"
    USER = "user"
    VIRTUAL_ENV = "virtual_env"


class PackageStatus(Enum):
    """Status of package installation."""
    INSTALLED = "installed"
    NOT_INSTALLED = "not_installed"
    OUTDATED = "outdated"
    UNKNOWN = "unknown"
    ERROR = "error"


@dataclass
class PackageInfo:
    """Information about a package."""
    name: str
    version: str = ""
    latest_version: str = ""
    description: str = ""
    install_path: str = ""
    status: PackageStatus = PackageStatus.UNKNOWN
    manager: PackageManagerType = PackageManagerType.NPM
    scope: InstallationScope = InstallationScope.LOCAL
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InstallationResult:
    """Result of package installation operation."""
    success: bool = False
    package_name: str = ""
    installed_version: str = ""
    manager_used: PackageManagerType = PackageManagerType.NPM
    scope_used: InstallationScope = InstallationScope.LOCAL
    output: str = ""
    error_message: str = ""
    duration_seconds: float = 0.0
    dependencies_installed: List[str] = field(default_factory=list)


@dataclass
class EnvironmentInfo:
    """Information about package manager environment."""
    manager: PackageManagerType
    version: str = ""
    executable_path: str = ""
    config_path: str = ""
    cache_path: str = ""
    global_packages_path: str = ""
    is_available: bool = False
    environment_variables: Dict[str, str] = field(default_factory=dict)


class PackageManagerStrategy(ABC):
    """Base class for package manager strategies."""
    
    def __init__(self):
        self.logger = logging.getLogger(f"package_manager_{self.__class__.__name__.lower()}")
        self._executable_path: Optional[str] = None
    
    @abstractmethod
    def get_manager_type(self) -> PackageManagerType:
        """Get the package manager type."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if package manager is available."""
        pass
    
    @abstractmethod
    def install_package(self, package_name: str, version: Optional[str] = None, 
                       scope: InstallationScope = InstallationScope.LOCAL) -> InstallationResult:
        """Install a package."""
        pass
    
    @abstractmethod
    def uninstall_package(self, package_name: str, 
                         scope: InstallationScope = InstallationScope.LOCAL) -> bool:
        """Uninstall a package."""
        pass
    
    @abstractmethod
    def list_packages(self, scope: InstallationScope = InstallationScope.LOCAL) -> List[PackageInfo]:
        """List installed packages."""
        pass
    
    @abstractmethod
    def get_package_info(self, package_name: str) -> Optional[PackageInfo]:
        """Get information about a specific package."""
        pass
    
    def get_environment_info(self) -> EnvironmentInfo:
        """Get environment information for this package manager."""
        return EnvironmentInfo(
            manager=self.get_manager_type(),
            executable_path=self._find_executable(),
            is_available=self.is_available()
        )
    
    def _find_executable(self) -> str:
        """Find the executable path for this package manager."""
        if self._executable_path:
            return self._executable_path
        
        manager_name = self.get_manager_type().value
        try:
            result = subprocess.run(
                ["where", manager_name],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                self._executable_path = result.stdout.strip().split('\n')[0]
                return self._executable_path
        except Exception as e:
            self.logger.debug(f"Failed to find {manager_name} executable: {e}")
        
        return ""
    
    def _run_command(self, args: List[str], cwd: Optional[str] = None, 
                    timeout: int = 300) -> subprocess.CompletedProcess:
        """Run a command with the package manager."""
        executable = self._find_executable()
        if not executable:
            raise RuntimeError(f"Package manager {self.get_manager_type().value} not found")
        
        cmd = [executable] + args
        
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=timeout
        )


class NpmStrategy(PackageManagerStrategy):
    """NPM package manager strategy."""
    
    def get_manager_type(self) -> PackageManagerType:
        return PackageManagerType.NPM
    
    def is_available(self) -> bool:
        try:
            result = self._run_command(["--version"], timeout=10)
            return result.returncode == 0
        except Exception:
            return False
    
    def install_package(self, package_name: str, version: Optional[str] = None, 
                       scope: InstallationScope = InstallationScope.LOCAL) -> InstallationResult:
        start_time = time.time()
        result = InstallationResult(
            package_name=package_name,
            manager_used=PackageManagerType.NPM,
            scope_used=scope
        )
        
        try:
            # Build install command
            args = ["install"]
            
            if scope == InstallationScope.GLOBAL:
                args.append("-g")
            
            package_spec = package_name
            if version:
                package_spec = f"{package_name}@{version}"
            
            args.append(package_spec)
            
            # Run installation
            proc_result = self._run_command(args)
            
            result.success = proc_result.returncode == 0
            result.output = proc_result.stdout
            result.error_message = proc_result.stderr if not result.success else ""
            result.duration_seconds = time.time() - start_time
            
            if result.success:
                # Get installed version
                installed_info = self.get_package_info(package_name)
                if installed_info:
                    result.installed_version = installed_info.version
            
        except Exception as e:
            result.success = False
            result.error_message = str(e)
            result.duration_seconds = time.time() - start_time
        
        return result
    
    def uninstall_package(self, package_name: str, 
                         scope: InstallationScope = InstallationScope.LOCAL) -> bool:
        try:
            args = ["uninstall"]
            
            if scope == InstallationScope.GLOBAL:
                args.append("-g")
            
            args.append(package_name)
            
            result = self._run_command(args)
            return result.returncode == 0
        except Exception as e:
            self.logger.error(f"Failed to uninstall {package_name}: {e}")
            return False
    
    def list_packages(self, scope: InstallationScope = InstallationScope.LOCAL) -> List[PackageInfo]:
        try:
            args = ["list", "--json"]
            
            if scope == InstallationScope.GLOBAL:
                args.append("-g")
            
            result = self._run_command(args)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                packages = []
                
                dependencies = data.get("dependencies", {})
                for name, info in dependencies.items():
                    packages.append(PackageInfo(
                        name=name,
                        version=info.get("version", ""),
                        manager=PackageManagerType.NPM,
                        scope=scope,
                        status=PackageStatus.INSTALLED
                    ))
                
                return packages
        except Exception as e:
            self.logger.error(f"Failed to list NPM packages: {e}")
        
        return []
    
    def get_package_info(self, package_name: str) -> Optional[PackageInfo]:
        try:
            # Check local installation
            result = self._run_command(["list", package_name, "--json"])
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                dependencies = data.get("dependencies", {})
                
                if package_name in dependencies:
                    info = dependencies[package_name]
                    return PackageInfo(
                        name=package_name,
                        version=info.get("version", ""),
                        manager=PackageManagerType.NPM,
                        scope=InstallationScope.LOCAL,
                        status=PackageStatus.INSTALLED
                    )
            
            # Check global installation
            result = self._run_command(["list", "-g", package_name, "--json"])
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                dependencies = data.get("dependencies", {})
                
                if package_name in dependencies:
                    info = dependencies[package_name]
                    return PackageInfo(
                        name=package_name,
                        version=info.get("version", ""),
                        manager=PackageManagerType.NPM,
                        scope=InstallationScope.GLOBAL,
                        status=PackageStatus.INSTALLED
                    )
        
        except Exception as e:
            self.logger.error(f"Failed to get NPM package info for {package_name}: {e}")
        
        return None


class PipStrategy(PackageManagerStrategy):
    """PIP package manager strategy."""
    
    def get_manager_type(self) -> PackageManagerType:
        return PackageManagerType.PIP
    
    def is_available(self) -> bool:
        try:
            result = self._run_command(["--version"], timeout=10)
            return result.returncode == 0
        except Exception:
            return False
    
    def install_package(self, package_name: str, version: Optional[str] = None, 
                       scope: InstallationScope = InstallationScope.LOCAL) -> InstallationResult:
        start_time = time.time()
        result = InstallationResult(
            package_name=package_name,
            manager_used=PackageManagerType.PIP,
            scope_used=scope
        )
        
        try:
            args = ["install"]
            
            if scope == InstallationScope.USER:
                args.append("--user")
            
            package_spec = package_name
            if version:
                package_spec = f"{package_name}=={version}"
            
            args.append(package_spec)
            
            proc_result = self._run_command(args)
            
            result.success = proc_result.returncode == 0
            result.output = proc_result.stdout
            result.error_message = proc_result.stderr if not result.success else ""
            result.duration_seconds = time.time() - start_time
            
            if result.success:
                installed_info = self.get_package_info(package_name)
                if installed_info:
                    result.installed_version = installed_info.version
        
        except Exception as e:
            result.success = False
            result.error_message = str(e)
            result.duration_seconds = time.time() - start_time
        
        return result
    
    def uninstall_package(self, package_name: str, 
                         scope: InstallationScope = InstallationScope.LOCAL) -> bool:
        try:
            args = ["uninstall", "-y", package_name]
            result = self._run_command(args)
            return result.returncode == 0
        except Exception as e:
            self.logger.error(f"Failed to uninstall {package_name}: {e}")
            return False
    
    def list_packages(self, scope: InstallationScope = InstallationScope.LOCAL) -> List[PackageInfo]:
        try:
            args = ["list", "--format=json"]
            
            if scope == InstallationScope.USER:
                args.append("--user")
            
            result = self._run_command(args)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                packages = []
                
                for item in data:
                    packages.append(PackageInfo(
                        name=item.get("name", ""),
                        version=item.get("version", ""),
                        manager=PackageManagerType.PIP,
                        scope=scope,
                        status=PackageStatus.INSTALLED
                    ))
                
                return packages
        except Exception as e:
            self.logger.error(f"Failed to list PIP packages: {e}")
        
        return []
    
    def get_package_info(self, package_name: str) -> Optional[PackageInfo]:
        try:
            result = self._run_command(["show", package_name])
            
            if result.returncode == 0:
                output = result.stdout
                
                # Parse pip show output
                version_match = re.search(r'Version: (.+)', output)
                location_match = re.search(r'Location: (.+)', output)
                
                version = version_match.group(1) if version_match else ""
                location = location_match.group(1) if location_match else ""
                
                return PackageInfo(
                    name=package_name,
                    version=version,
                    install_path=location,
                    manager=PackageManagerType.PIP,
                    scope=InstallationScope.LOCAL,
                    status=PackageStatus.INSTALLED
                )
        
        except Exception as e:
            self.logger.error(f"Failed to get PIP package info for {package_name}: {e}")
        
        return None


class CondaStrategy(PackageManagerStrategy):
    """Conda package manager strategy."""
    
    def get_manager_type(self) -> PackageManagerType:
        return PackageManagerType.CONDA
    
    def is_available(self) -> bool:
        try:
            result = self._run_command(["--version"], timeout=10)
            return result.returncode == 0
        except Exception:
            return False
    
    def install_package(self, package_name: str, version: Optional[str] = None, 
                       scope: InstallationScope = InstallationScope.LOCAL) -> InstallationResult:
        start_time = time.time()
        result = InstallationResult(
            package_name=package_name,
            manager_used=PackageManagerType.CONDA,
            scope_used=scope
        )
        
        try:
            args = ["install", "-y"]
            
            package_spec = package_name
            if version:
                package_spec = f"{package_name}={version}"
            
            args.append(package_spec)
            
            proc_result = self._run_command(args)
            
            result.success = proc_result.returncode == 0
            result.output = proc_result.stdout
            result.error_message = proc_result.stderr if not result.success else ""
            result.duration_seconds = time.time() - start_time
            
            if result.success:
                installed_info = self.get_package_info(package_name)
                if installed_info:
                    result.installed_version = installed_info.version
        
        except Exception as e:
            result.success = False
            result.error_message = str(e)
            result.duration_seconds = time.time() - start_time
        
        return result
    
    def uninstall_package(self, package_name: str, 
                         scope: InstallationScope = InstallationScope.LOCAL) -> bool:
        try:
            args = ["remove", "-y", package_name]
            result = self._run_command(args)
            return result.returncode == 0
        except Exception as e:
            self.logger.error(f"Failed to uninstall {package_name}: {e}")
            return False
    
    def list_packages(self, scope: InstallationScope = InstallationScope.LOCAL) -> List[PackageInfo]:
        try:
            result = self._run_command(["list", "--json"])
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                packages = []
                
                for item in data:
                    packages.append(PackageInfo(
                        name=item.get("name", ""),
                        version=item.get("version", ""),
                        manager=PackageManagerType.CONDA,
                        scope=scope,
                        status=PackageStatus.INSTALLED
                    ))
                
                return packages
        except Exception as e:
            self.logger.error(f"Failed to list Conda packages: {e}")
        
        return []
    
    def get_package_info(self, package_name: str) -> Optional[PackageInfo]:
        try:
            result = self._run_command(["list", package_name, "--json"])
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                
                if data:
                    item = data[0]
                    return PackageInfo(
                        name=item.get("name", ""),
                        version=item.get("version", ""),
                        manager=PackageManagerType.CONDA,
                        scope=InstallationScope.LOCAL,
                        status=PackageStatus.INSTALLED
                    )
        
        except Exception as e:
            self.logger.error(f"Failed to get Conda package info for {package_name}: {e}")
        
        return None


class PackageManagerIntegrator:
    """Main integrator for package manager operations."""
    
    def __init__(self):
        self.logger = logging.getLogger("package_manager_integrator")
        
        # Initialize strategies
        self.strategies = {
            PackageManagerType.NPM: NpmStrategy(),
            PackageManagerType.PIP: PipStrategy(),
            PackageManagerType.CONDA: CondaStrategy()
        }
        
        # Installation registry for tracking
        self.installation_registry: Dict[str, List[InstallationResult]] = {}
    
    def detect_available_managers(self) -> Dict[PackageManagerType, EnvironmentInfo]:
        """Detect which package managers are available."""
        available = {}
        
        for manager_type, strategy in self.strategies.items():
            try:
                env_info = strategy.get_environment_info()
                env_info.is_available = strategy.is_available()
                available[manager_type] = env_info
                
                if env_info.is_available:
                    self.logger.info(f"Detected {manager_type.value} at {env_info.executable_path}")
            except Exception as e:
                self.logger.error(f"Failed to detect {manager_type.value}: {e}")
        
        return available
    
    def install_packages(self, packages: Dict[PackageManagerType, List[Tuple[str, Optional[str]]]], 
                        scope: InstallationScope = InstallationScope.LOCAL) -> Dict[str, InstallationResult]:
        """Install multiple packages across different package managers."""
        results = {}
        
        for manager_type, package_list in packages.items():
            if manager_type not in self.strategies:
                self.logger.warning(f"Unsupported package manager: {manager_type}")
                continue
            
            strategy = self.strategies[manager_type]
            
            if not strategy.is_available():
                self.logger.warning(f"Package manager {manager_type.value} not available")
                continue
            
            for package_name, version in package_list:
                try:
                    result = strategy.install_package(package_name, version, scope)
                    results[f"{manager_type.value}:{package_name}"] = result
                    
                    # Track installation
                    if package_name not in self.installation_registry:
                        self.installation_registry[package_name] = []
                    self.installation_registry[package_name].append(result)
                    
                    if result.success:
                        self.logger.info(f"Successfully installed {package_name} v{result.installed_version} via {manager_type.value}")
                    else:
                        self.logger.error(f"Failed to install {package_name} via {manager_type.value}: {result.error_message}")
                
                except Exception as e:
                    error_msg = f"Exception installing {package_name} via {manager_type.value}: {e}"
                    self.logger.error(error_msg)
                    results[f"{manager_type.value}:{package_name}"] = InstallationResult(
                        success=False,
                        package_name=package_name,
                        manager_used=manager_type,
                        error_message=error_msg
                    )
        
        return results
    
    def get_all_installed_packages(self) -> Dict[PackageManagerType, List[PackageInfo]]:
        """Get all installed packages from all available managers."""
        all_packages = {}
        
        for manager_type, strategy in self.strategies.items():
            if strategy.is_available():
                try:
                    packages = strategy.list_packages()
                    all_packages[manager_type] = packages
                    self.logger.info(f"Found {len(packages)} packages in {manager_type.value}")
                except Exception as e:
                    self.logger.error(f"Failed to list packages for {manager_type.value}: {e}")
                    all_packages[manager_type] = []
        
        return all_packages
    
    def create_environment(self, manager_type: PackageManagerType, env_name: str, 
                          packages: Optional[List[Tuple[str, Optional[str]]]] = None) -> bool:
        """Create a new environment (for managers that support it)."""
        if manager_type == PackageManagerType.CONDA:
            try:
                strategy = self.strategies[PackageManagerType.CONDA]
                
                # Create environment
                args = ["create", "-y", "-n", env_name]
                
                if packages:
                    for package_name, version in packages:
                        package_spec = package_name
                        if version:
                            package_spec = f"{package_name}={version}"
                        args.append(package_spec)
                
                result = strategy._run_command(args)
                
                if result.returncode == 0:
                    self.logger.info(f"Successfully created conda environment: {env_name}")
                    return True
                else:
                    self.logger.error(f"Failed to create conda environment: {result.stderr}")
                    return False
            
            except Exception as e:
                self.logger.error(f"Exception creating conda environment {env_name}: {e}")
                return False
        
        else:
            self.logger.warning(f"Environment creation not supported for {manager_type.value}")
            return False
    
    def get_installation_history(self, package_name: Optional[str] = None) -> Dict[str, List[InstallationResult]]:
        """Get installation history for packages."""
        if package_name:
            return {package_name: self.installation_registry.get(package_name, [])}
        return self.installation_registry.copy()
    
    def rollback_installation(self, package_name: str, manager_type: PackageManagerType) -> bool:
        """Rollback a package installation."""
        if manager_type not in self.strategies:
            return False
        
        strategy = self.strategies[manager_type]
        
        try:
            success = strategy.uninstall_package(package_name)
            
            if success:
                self.logger.info(f"Successfully rolled back {package_name} from {manager_type.value}")
                
                # Update registry
                if package_name in self.installation_registry:
                    rollback_result = InstallationResult(
                        success=True,
                        package_name=package_name,
                        manager_used=manager_type,
                        output="Package rolled back"
                    )
                    self.installation_registry[package_name].append(rollback_result)
            
            return success
        
        except Exception as e:
            self.logger.error(f"Failed to rollback {package_name}: {e}")
            return False
    
    def generate_installation_report(self) -> str:
        """Generate a comprehensive installation report."""
        report = []
        report.append("=== Package Manager Integration Report ===")
        report.append("")
        
        # Available managers
        available_managers = self.detect_available_managers()
        report.append("Available Package Managers:")
        for manager_type, env_info in available_managers.items():
            status = "✓" if env_info.is_available else "✗"
            report.append(f"  {status} {manager_type.value} - {env_info.executable_path}")
        report.append("")
        
        # Installed packages summary
        all_packages = self.get_all_installed_packages()
        report.append("Installed Packages Summary:")
        total_packages = 0
        for manager_type, packages in all_packages.items():
            count = len(packages)
            total_packages += count
            report.append(f"  {manager_type.value}: {count} packages")
        
        report.append(f"  Total: {total_packages} packages")
        report.append("")
        
        # Installation history
        if self.installation_registry:
            report.append("Recent Installations:")
            for package_name, installations in self.installation_registry.items():
                latest = installations[-1] if installations else None
                if latest:
                    status = "✓" if latest.success else "✗"
                    report.append(f"  {status} {package_name} v{latest.installed_version} ({latest.manager_used.value})")
        
        return "\n".join(report)


# Test the module when run directly
if __name__ == "__main__":
    print("Testing PackageManagerIntegrator...")
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Test package manager integrator
    integrator = PackageManagerIntegrator()
    
    # Detect available managers
    available = integrator.detect_available_managers()
    print(f"Available managers: {list(available.keys())}")
    
    # Generate report
    print("\n" + integrator.generate_installation_report())
    
    print("\nPackageManagerIntegrator test completed!")