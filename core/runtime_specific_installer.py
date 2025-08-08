# -*- coding: utf-8 -*-
"""
Runtime-Specific Installation Handler for Environment Dev Deep Evaluation
Implements runtime-specific installation logic for the 8 essential runtimes
"""

import os
import sys
import logging
import subprocess
import shutil
import tempfile
import json
import platform
import re
from pathlib import Path
from typing import Dict, Optional, Tuple, List, Any, Set, Union
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from core.advanced_installation_manager import AdvancedInstallationManager, InstallationResult, InstallationStatus
from core.intelligent_preparation_manager import IntelligentPreparationManager
from utils.env_manager import set_env_var, get_env_var, add_to_path
from core.error_handler import EnvDevError, ErrorSeverity, ErrorCategory

logger = logging.getLogger(__name__)

class RuntimeType(Enum):
    """Types of supported runtimes"""
    JAVA = "java"
    PYTHON = "python"
    NODEJS = "nodejs"
    DOTNET = "dotnet"
    GO = "go"
    RUST = "rust"
    GCC = "gcc"
    CMAKE = "cmake"

class RuntimeInstallationMethod(Enum):
    """Installation methods for runtimes"""
    ARCHIVE = "archive"
    INSTALLER = "installer"
    PACKAGE_MANAGER = "package_manager"
    SCRIPT = "script"
    BINARY = "binary"

@dataclass
class RuntimeConfiguration:
    """Configuration for a specific runtime"""
    name: str
    runtime_type: RuntimeType
    version: str
    download_url: str
    installation_method: RuntimeInstallationMethod
    install_path: str
    environment_variables: Dict[str, str] = field(default_factory=dict)
    path_entries: List[str] = field(default_factory=list)
    verification_commands: List[List[str]] = field(default_factory=list)
    post_install_commands: List[List[str]] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    platform_specific: Dict[str, Any] = field(default_factory=dict)
    sha256_hash: Optional[str] = None
    install_args: List[str] = field(default_factory=list)
    uninstall_command: Optional[List[str]] = None

@dataclass
class RuntimeInstallationResult:
    """Result of runtime installation"""
    success: bool
    runtime_type: RuntimeType
    version: str
    installed_path: str
    environment_variables: Dict[str, str] = field(default_factory=dict)
    path_entries: List[str] = field(default_factory=list)
    verification_results: List[Dict[str, Any]] = field(default_factory=list)
    installation_time: float = 0.0
    message: str = ""
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

class RuntimeInstaller(ABC):
    """Abstract base class for runtime-specific installers"""
    
    def __init__(self, base_path: str):
        self.base_path = base_path
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.platform = platform.system().lower()
        self.is_windows = self.platform == "windows"
        self.is_linux = self.platform == "linux"
        self.is_macos = self.platform == "darwin"
    
    @abstractmethod
    def get_runtime_type(self) -> RuntimeType:
        """Get the runtime type this installer handles"""
        pass
    
    @abstractmethod
    def get_default_configuration(self, version: str = "latest") -> RuntimeConfiguration:
        """Get default configuration for this runtime"""
        pass
    
    @abstractmethod
    def install_runtime(self, config: RuntimeConfiguration) -> RuntimeInstallationResult:
        """Install the runtime with the given configuration"""
        pass
    
    @abstractmethod
    def verify_installation(self, config: RuntimeConfiguration) -> Dict[str, Any]:
        """Verify that the runtime is properly installed"""
        pass
    
    def configure_environment(self, config: RuntimeConfiguration) -> bool:
        """Configure environment variables and PATH for the runtime"""
        try:
            # Set environment variables
            for var_name, var_value in config.environment_variables.items():
                if not set_env_var(var_name, var_value, scope='user'):
                    self.logger.warning(f"Failed to set environment variable: {var_name}")
                    return False
            
            # Add to PATH
            for path_entry in config.path_entries:
                if not add_to_path(path_entry, scope='user'):
                    self.logger.warning(f"Failed to add to PATH: {path_entry}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error configuring environment for {config.name}: {e}")
            return False
    
    def run_post_install_commands(self, config: RuntimeConfiguration) -> List[Dict[str, Any]]:
        """Run post-installation commands"""
        results = []
        
        for command in config.post_install_commands:
            try:
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    timeout=300,
                    check=False
                )
                
                results.append({
                    'command': ' '.join(command),
                    'return_code': result.returncode,
                    'stdout': result.stdout,
                    'stderr': result.stderr,
                    'success': result.returncode == 0
                })
                
            except subprocess.TimeoutExpired:
                results.append({
                    'command': ' '.join(command),
                    'return_code': -1,
                    'stdout': '',
                    'stderr': 'Command timed out',
                    'success': False
                })
            except Exception as e:
                results.append({
                    'command': ' '.join(command),
                    'return_code': -1,
                    'stdout': '',
                    'stderr': str(e),
                    'success': False
                })
        
        return results

class JavaInstaller(RuntimeInstaller):
    """Installer for Java/OpenJDK runtime"""
    
    def get_runtime_type(self) -> RuntimeType:
        return RuntimeType.JAVA
    
    def get_default_configuration(self, version: str = "17") -> RuntimeConfiguration:
        """Get default Java configuration"""
        install_path = os.path.join(self.base_path, "java")
        
        # Platform-specific download URLs
        if self.is_windows:
            download_url = f"https://download.java.net/java/GA/jdk{version}/0d483333a00540d886896bac774ff48b/35/GPL/openjdk-{version}_windows-x64_bin.zip"
            filename = f"openjdk-{version}_windows-x64_bin.zip"
        elif self.is_linux:
            download_url = f"https://download.java.net/java/GA/jdk{version}/0d483333a00540d886896bac774ff48b/35/GPL/openjdk-{version}_linux-x64_bin.tar.gz"
            filename = f"openjdk-{version}_linux-x64_bin.tar.gz"
        else:  # macOS
            download_url = f"https://download.java.net/java/GA/jdk{version}/0d483333a00540d886896bac774ff48b/35/GPL/openjdk-{version}_osx-x64_bin.tar.gz"
            filename = f"openjdk-{version}_osx-x64_bin.tar.gz"
        
        return RuntimeConfiguration(
            name=f"OpenJDK {version}",
            runtime_type=RuntimeType.JAVA,
            version=version,
            download_url=download_url,
            installation_method=RuntimeInstallationMethod.ARCHIVE,
            install_path=install_path,
            environment_variables={
                "JAVA_HOME": install_path,
                "JDK_HOME": install_path
            },
            path_entries=[
                os.path.join(install_path, "bin")
            ],
            verification_commands=[
                ["java", "-version"],
                ["javac", "-version"]
            ],
            platform_specific={
                "filename": filename,
                "extract_subdir": f"jdk-{version}" if version != "latest" else "jdk-*"
            }
        )
    
    def install_runtime(self, config: RuntimeConfiguration) -> RuntimeInstallationResult:
        """Install Java runtime"""
        start_time = datetime.now()
        result = RuntimeInstallationResult(
            success=False,
            runtime_type=config.runtime_type,
            version=config.version,
            installed_path=config.install_path
        )
        
        try:
            self.logger.info(f"Installing {config.name}")
            
            # Use advanced installation manager for atomic installation
            advanced_installer = AdvancedInstallationManager(self.base_path)
            
            # Prepare component data for advanced installer
            component_data = {
                'install_method': 'archive',
                'download_url': config.download_url,
                'filename': config.platform_specific.get('filename'),
                'sha256_hash': config.sha256_hash,
                'install_path': config.install_path,
                'verification_paths': [os.path.join(config.install_path, "bin", "java.exe" if self.is_windows else "java")],
                'verification_commands': config.verification_commands,
                'environment_variables': config.environment_variables
            }
            
            # Install using advanced installer
            install_result = advanced_installer.install_component_atomic(
                f"java_{config.version}", 
                component_data
            )
            
            if not install_result.success:
                result.errors.append(f"Advanced installation failed: {install_result.message}")
                result.message = install_result.message
                return result
            
            # Configure environment
            if not self.configure_environment(config):
                result.warnings.append("Environment configuration had issues")
            
            # Run post-install commands
            post_install_results = self.run_post_install_commands(config)
            
            # Verify installation
            verification_result = self.verify_installation(config)
            result.verification_results.append(verification_result)
            
            if verification_result['success']:
                result.success = True
                result.installed_path = config.install_path
                result.environment_variables = config.environment_variables
                result.path_entries = config.path_entries
                result.message = f"Java {config.version} installed successfully"
            else:
                result.errors.append("Installation verification failed")
                result.message = "Java installation failed verification"
            
            end_time = datetime.now()
            result.installation_time = (end_time - start_time).total_seconds()
            
            return result
            
        except Exception as e:
            result.errors.append(f"Critical error during Java installation: {e}")
            result.message = f"Java installation failed: {e}"
            self.logger.error(f"Critical error during Java installation: {e}")
            return result
    
    def verify_installation(self, config: RuntimeConfiguration) -> Dict[str, Any]:
        """Verify Java installation"""
        verification_result = {
            'success': False,
            'version_detected': None,
            'java_home_valid': False,
            'commands_working': [],
            'errors': []
        }
        
        try:
            # Check JAVA_HOME
            java_home = get_env_var("JAVA_HOME")
            if java_home and os.path.exists(java_home):
                verification_result['java_home_valid'] = True
            else:
                verification_result['errors'].append("JAVA_HOME not set or invalid")
            
            # Test verification commands
            for command in config.verification_commands:
                try:
                    result = subprocess.run(
                        command,
                        capture_output=True,
                        text=True,
                        timeout=30,
                        check=False
                    )
                    
                    if result.returncode == 0:
                        verification_result['commands_working'].append(' '.join(command))
                        
                        # Extract version from java -version output
                        if command[0] == "java" and command[1] == "-version":
                            version_match = re.search(r'"([^"]+)"', result.stderr)
                            if version_match:
                                verification_result['version_detected'] = version_match.group(1)
                    else:
                        verification_result['errors'].append(f"Command failed: {' '.join(command)}")
                        
                except subprocess.TimeoutExpired:
                    verification_result['errors'].append(f"Command timed out: {' '.join(command)}")
                except Exception as e:
                    verification_result['errors'].append(f"Command error: {' '.join(command)} - {e}")
            
            # Overall success check
            verification_result['success'] = (
                verification_result['java_home_valid'] and
                len(verification_result['commands_working']) >= 1 and
                verification_result['version_detected'] is not None
            )
            
            return verification_result
            
        except Exception as e:
            verification_result['errors'].append(f"Verification error: {e}")
            return verification_result

class PythonInstaller(RuntimeInstaller):
    """Installer for Python runtime"""
    
    def get_runtime_type(self) -> RuntimeType:
        return RuntimeType.PYTHON
    
    def get_default_configuration(self, version: str = "3.11") -> RuntimeConfiguration:
        """Get default Python configuration"""
        install_path = os.path.join(self.base_path, "python")
        
        # Platform-specific download URLs
        if self.is_windows:
            download_url = f"https://www.python.org/ftp/python/{version}.0/python-{version}.0-amd64.exe"
            installation_method = RuntimeInstallationMethod.INSTALLER
            filename = f"python-{version}.0-amd64.exe"
            install_args = ["/quiet", f"InstallAllUsers=0", f"TargetDir={install_path}"]
        else:
            download_url = f"https://www.python.org/ftp/python/{version}.0/Python-{version}.0.tgz"
            installation_method = RuntimeInstallationMethod.SCRIPT
            filename = f"Python-{version}.0.tgz"
            install_args = []
        
        return RuntimeConfiguration(
            name=f"Python {version}",
            runtime_type=RuntimeType.PYTHON,
            version=version,
            download_url=download_url,
            installation_method=installation_method,
            install_path=install_path,
            environment_variables={
                "PYTHON_HOME": install_path,
                "PYTHONPATH": os.path.join(install_path, "Lib", "site-packages") if self.is_windows else os.path.join(install_path, "lib", f"python{version}", "site-packages")
            },
            path_entries=[
                install_path,
                os.path.join(install_path, "Scripts") if self.is_windows else os.path.join(install_path, "bin")
            ],
            verification_commands=[
                ["python", "--version"],
                ["pip", "--version"]
            ],
            post_install_commands=[
                ["python", "-m", "ensurepip", "--upgrade"] if not self.is_windows else []
            ],
            platform_specific={
                "filename": filename
            },
            install_args=install_args
        )
    
    def install_runtime(self, config: RuntimeConfiguration) -> RuntimeInstallationResult:
        """Install Python runtime"""
        start_time = datetime.now()
        result = RuntimeInstallationResult(
            success=False,
            runtime_type=config.runtime_type,
            version=config.version,
            installed_path=config.install_path
        )
        
        try:
            self.logger.info(f"Installing {config.name}")
            
            # Use advanced installation manager
            advanced_installer = AdvancedInstallationManager(self.base_path)
            
            # Prepare component data
            if config.installation_method == RuntimeInstallationMethod.INSTALLER:
                component_data = {
                    'install_method': 'executable',
                    'download_url': config.download_url,
                    'filename': config.platform_specific.get('filename'),
                    'sha256_hash': config.sha256_hash,
                    'install_args': config.install_args,
                    'verification_paths': [os.path.join(config.install_path, "python.exe" if self.is_windows else "bin/python")],
                    'verification_commands': config.verification_commands,
                    'environment_variables': config.environment_variables
                }
            else:
                component_data = {
                    'install_method': 'script',
                    'download_url': config.download_url,
                    'filename': config.platform_specific.get('filename'),
                    'sha256_hash': config.sha256_hash,
                    'script_path': self._create_python_build_script(config),
                    'verification_paths': [os.path.join(config.install_path, "bin", "python")],
                    'verification_commands': config.verification_commands,
                    'environment_variables': config.environment_variables
                }
            
            # Install using advanced installer
            install_result = advanced_installer.install_component_atomic(
                f"python_{config.version}",
                component_data
            )
            
            if not install_result.success:
                result.errors.append(f"Advanced installation failed: {install_result.message}")
                result.message = install_result.message
                return result
            
            # Configure environment
            if not self.configure_environment(config):
                result.warnings.append("Environment configuration had issues")
            
            # Run post-install commands
            post_install_results = self.run_post_install_commands(config)
            for post_result in post_install_results:
                if not post_result['success']:
                    result.warnings.append(f"Post-install command failed: {post_result['command']}")
            
            # Verify installation
            verification_result = self.verify_installation(config)
            result.verification_results.append(verification_result)
            
            if verification_result['success']:
                result.success = True
                result.installed_path = config.install_path
                result.environment_variables = config.environment_variables
                result.path_entries = config.path_entries
                result.message = f"Python {config.version} installed successfully"
            else:
                result.errors.append("Installation verification failed")
                result.message = "Python installation failed verification"
            
            end_time = datetime.now()
            result.installation_time = (end_time - start_time).total_seconds()
            
            return result
            
        except Exception as e:
            result.errors.append(f"Critical error during Python installation: {e}")
            result.message = f"Python installation failed: {e}"
            self.logger.error(f"Critical error during Python installation: {e}")
            return result
    
    def _create_python_build_script(self, config: RuntimeConfiguration) -> str:
        """Create a build script for Python on Unix systems"""
        script_content = f"""#!/bin/bash
set -e

# Extract Python source
tar -xzf {config.platform_specific.get('filename')}
cd Python-{config.version}.0

# Configure build
./configure --prefix={config.install_path} --enable-optimizations

# Build and install
make -j$(nproc)
make install

# Create symlinks
ln -sf {config.install_path}/bin/python{config.version} {config.install_path}/bin/python
ln -sf {config.install_path}/bin/pip{config.version} {config.install_path}/bin/pip

echo "Python {config.version} installation completed"
"""
        
        script_path = os.path.join(self.base_path, "temp", f"install_python_{config.version}.sh")
        os.makedirs(os.path.dirname(script_path), exist_ok=True)
        
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        # Make script executable
        os.chmod(script_path, 0o755)
        
        return script_path
    
    def verify_installation(self, config: RuntimeConfiguration) -> Dict[str, Any]:
        """Verify Python installation"""
        verification_result = {
            'success': False,
            'version_detected': None,
            'python_home_valid': False,
            'pip_available': False,
            'commands_working': [],
            'errors': []
        }
        
        try:
            # Check PYTHON_HOME
            python_home = get_env_var("PYTHON_HOME")
            if python_home and os.path.exists(python_home):
                verification_result['python_home_valid'] = True
            else:
                verification_result['errors'].append("PYTHON_HOME not set or invalid")
            
            # Test verification commands
            for command in config.verification_commands:
                try:
                    result = subprocess.run(
                        command,
                        capture_output=True,
                        text=True,
                        timeout=30,
                        check=False
                    )
                    
                    if result.returncode == 0:
                        verification_result['commands_working'].append(' '.join(command))
                        
                        # Extract version information
                        if command[0] == "python" and command[1] == "--version":
                            version_match = re.search(r'Python (\d+\.\d+\.\d+)', result.stdout)
                            if version_match:
                                verification_result['version_detected'] = version_match.group(1)
                        elif command[0] == "pip":
                            verification_result['pip_available'] = True
                    else:
                        verification_result['errors'].append(f"Command failed: {' '.join(command)}")
                        
                except subprocess.TimeoutExpired:
                    verification_result['errors'].append(f"Command timed out: {' '.join(command)}")
                except Exception as e:
                    verification_result['errors'].append(f"Command error: {' '.join(command)} - {e}")
            
            # Overall success check
            verification_result['success'] = (
                verification_result['python_home_valid'] and
                len(verification_result['commands_working']) >= 1 and
                verification_result['version_detected'] is not None
            )
            
            return verification_result
            
        except Exception as e:
            verification_result['errors'].append(f"Verification error: {e}")
            return verification_result

class NodeJSInstaller(RuntimeInstaller):
    """Installer for Node.js runtime"""
    
    def get_runtime_type(self) -> RuntimeType:
        return RuntimeType.NODEJS
    
    def get_default_configuration(self, version: str = "18") -> RuntimeConfiguration:
        """Get default Node.js configuration"""
        install_path = os.path.join(self.base_path, "nodejs")
        
        # Platform-specific download URLs
        if self.is_windows:
            download_url = f"https://nodejs.org/dist/v{version}.0.0/node-v{version}.0.0-win-x64.zip"
            filename = f"node-v{version}.0.0-win-x64.zip"
        elif self.is_linux:
            download_url = f"https://nodejs.org/dist/v{version}.0.0/node-v{version}.0.0-linux-x64.tar.xz"
            filename = f"node-v{version}.0.0-linux-x64.tar.xz"
        else:  # macOS
            download_url = f"https://nodejs.org/dist/v{version}.0.0/node-v{version}.0.0-darwin-x64.tar.gz"
            filename = f"node-v{version}.0.0-darwin-x64.tar.gz"
        
        return RuntimeConfiguration(
            name=f"Node.js {version}",
            runtime_type=RuntimeType.NODEJS,
            version=version,
            download_url=download_url,
            installation_method=RuntimeInstallationMethod.ARCHIVE,
            install_path=install_path,
            environment_variables={
                "NODE_HOME": install_path,
                "NPM_CONFIG_PREFIX": os.path.join(install_path, "global")
            },
            path_entries=[
                os.path.join(install_path, "bin") if not self.is_windows else install_path,
                os.path.join(install_path, "global", "bin")
            ],
            verification_commands=[
                ["node", "--version"],
                ["npm", "--version"]
            ],
            post_install_commands=[
                ["npm", "config", "set", "prefix", os.path.join(install_path, "global")]
            ],
            platform_specific={
                "filename": filename,
                "extract_subdir": f"node-v{version}.0.0-win-x64" if self.is_windows else f"node-v{version}.0.0-linux-x64" if self.is_linux else f"node-v{version}.0.0-darwin-x64"
            }
        )
    
    def install_runtime(self, config: RuntimeConfiguration) -> RuntimeInstallationResult:
        """Install Node.js runtime"""
        start_time = datetime.now()
        result = RuntimeInstallationResult(
            success=False,
            runtime_type=config.runtime_type,
            version=config.version,
            installed_path=config.install_path
        )
        
        try:
            self.logger.info(f"Installing {config.name}")
            
            # Use advanced installation manager
            advanced_installer = AdvancedInstallationManager(self.base_path)
            
            # Prepare component data
            component_data = {
                'install_method': 'archive',
                'download_url': config.download_url,
                'filename': config.platform_specific.get('filename'),
                'sha256_hash': config.sha256_hash,
                'install_path': config.install_path,
                'verification_paths': [os.path.join(config.install_path, "node.exe" if self.is_windows else "bin/node")],
                'verification_commands': config.verification_commands,
                'environment_variables': config.environment_variables
            }
            
            # Install using advanced installer
            install_result = advanced_installer.install_component_atomic(
                f"nodejs_{config.version}",
                component_data
            )
            
            if not install_result.success:
                result.errors.append(f"Advanced installation failed: {install_result.message}")
                result.message = install_result.message
                return result
            
            # Configure environment
            if not self.configure_environment(config):
                result.warnings.append("Environment configuration had issues")
            
            # Run post-install commands
            post_install_results = self.run_post_install_commands(config)
            for post_result in post_install_results:
                if not post_result['success']:
                    result.warnings.append(f"Post-install command failed: {post_result['command']}")
            
            # Verify installation
            verification_result = self.verify_installation(config)
            result.verification_results.append(verification_result)
            
            if verification_result['success']:
                result.success = True
                result.installed_path = config.install_path
                result.environment_variables = config.environment_variables
                result.path_entries = config.path_entries
                result.message = f"Node.js {config.version} installed successfully"
            else:
                result.errors.append("Installation verification failed")
                result.message = "Node.js installation failed verification"
            
            end_time = datetime.now()
            result.installation_time = (end_time - start_time).total_seconds()
            
            return result
            
        except Exception as e:
            result.errors.append(f"Critical error during Node.js installation: {e}")
            result.message = f"Node.js installation failed: {e}"
            self.logger.error(f"Critical error during Node.js installation: {e}")
            return result
    
    def verify_installation(self, config: RuntimeConfiguration) -> Dict[str, Any]:
        """Verify Node.js installation"""
        verification_result = {
            'success': False,
            'node_version': None,
            'npm_version': None,
            'node_home_valid': False,
            'commands_working': [],
            'errors': []
        }
        
        try:
            # Check NODE_HOME
            node_home = get_env_var("NODE_HOME")
            if node_home and os.path.exists(node_home):
                verification_result['node_home_valid'] = True
            else:
                verification_result['errors'].append("NODE_HOME not set or invalid")
            
            # Test verification commands
            for command in config.verification_commands:
                try:
                    result = subprocess.run(
                        command,
                        capture_output=True,
                        text=True,
                        timeout=30,
                        check=False
                    )
                    
                    if result.returncode == 0:
                        verification_result['commands_working'].append(' '.join(command))
                        
                        # Extract version information
                        if command[0] == "node":
                            verification_result['node_version'] = result.stdout.strip()
                        elif command[0] == "npm":
                            verification_result['npm_version'] = result.stdout.strip()
                    else:
                        verification_result['errors'].append(f"Command failed: {' '.join(command)}")
                        
                except subprocess.TimeoutExpired:
                    verification_result['errors'].append(f"Command timed out: {' '.join(command)}")
                except Exception as e:
                    verification_result['errors'].append(f"Command error: {' '.join(command)} - {e}")
            
            # Overall success check
            verification_result['success'] = (
                verification_result['node_home_valid'] and
                verification_result['node_version'] is not None and
                verification_result['npm_version'] is not None
            )
            
            return verification_result
            
        except Exception as e:
            verification_result['errors'].append(f"Verification error: {e}")
            return verification_result

class DotNetInstaller(RuntimeInstaller):
    """Installer for .NET runtime"""
    
    def get_runtime_type(self) -> RuntimeType:
        return RuntimeType.DOTNET
    
    def get_default_configuration(self, version: str = "6.0") -> RuntimeConfiguration:
        """Get default .NET configuration"""
        install_path = os.path.join(self.base_path, "dotnet")
        
        # Platform-specific download URLs
        if self.is_windows:
            download_url = f"https://download.visualstudio.microsoft.com/download/pr/dotnet-sdk-{version}-win-x64.zip"
            filename = f"dotnet-sdk-{version}-win-x64.zip"
        elif self.is_linux:
            download_url = f"https://download.visualstudio.microsoft.com/download/pr/dotnet-sdk-{version}-linux-x64.tar.gz"
            filename = f"dotnet-sdk-{version}-linux-x64.tar.gz"
        else:  # macOS
            download_url = f"https://download.visualstudio.microsoft.com/download/pr/dotnet-sdk-{version}-osx-x64.tar.gz"
            filename = f"dotnet-sdk-{version}-osx-x64.tar.gz"
        
        return RuntimeConfiguration(
            name=f".NET {version}",
            runtime_type=RuntimeType.DOTNET,
            version=version,
            download_url=download_url,
            installation_method=RuntimeInstallationMethod.ARCHIVE,
            install_path=install_path,
            environment_variables={
                "DOTNET_ROOT": install_path,
                "DOTNET_CLI_TELEMETRY_OPTOUT": "1"
            },
            path_entries=[
                install_path
            ],
            verification_commands=[
                ["dotnet", "--version"],
                ["dotnet", "--info"]
            ],
            platform_specific={
                "filename": filename
            }
        )
    
    def install_runtime(self, config: RuntimeConfiguration) -> RuntimeInstallationResult:
        """Install .NET runtime"""
        start_time = datetime.now()
        result = RuntimeInstallationResult(
            success=False,
            runtime_type=config.runtime_type,
            version=config.version,
            installed_path=config.install_path
        )
        
        try:
            self.logger.info(f"Installing {config.name}")
            
            # Use advanced installation manager
            advanced_installer = AdvancedInstallationManager(self.base_path)
            
            # Prepare component data
            component_data = {
                'install_method': 'archive',
                'download_url': config.download_url,
                'filename': config.platform_specific.get('filename'),
                'sha256_hash': config.sha256_hash,
                'install_path': config.install_path,
                'verification_paths': [os.path.join(config.install_path, "dotnet.exe" if self.is_windows else "dotnet")],
                'verification_commands': config.verification_commands,
                'environment_variables': config.environment_variables
            }
            
            # Install using advanced installer
            install_result = advanced_installer.install_component_atomic(
                f"dotnet_{config.version}",
                component_data
            )
            
            if not install_result.success:
                result.errors.append(f"Advanced installation failed: {install_result.message}")
                result.message = install_result.message
                return result
            
            # Configure environment
            if not self.configure_environment(config):
                result.warnings.append("Environment configuration had issues")
            
            # Verify installation
            verification_result = self.verify_installation(config)
            result.verification_results.append(verification_result)
            
            if verification_result['success']:
                result.success = True
                result.installed_path = config.install_path
                result.environment_variables = config.environment_variables
                result.path_entries = config.path_entries
                result.message = f".NET {config.version} installed successfully"
            else:
                result.errors.append("Installation verification failed")
                result.message = ".NET installation failed verification"
            
            end_time = datetime.now()
            result.installation_time = (end_time - start_time).total_seconds()
            
            return result
            
        except Exception as e:
            result.errors.append(f"Critical error during .NET installation: {e}")
            result.message = f".NET installation failed: {e}"
            self.logger.error(f"Critical error during .NET installation: {e}")
            return result
    
    def verify_installation(self, config: RuntimeConfiguration) -> Dict[str, Any]:
        """Verify .NET installation"""
        verification_result = {
            'success': False,
            'version_detected': None,
            'dotnet_root_valid': False,
            'commands_working': [],
            'errors': []
        }
        
        try:
            # Check DOTNET_ROOT
            dotnet_root = get_env_var("DOTNET_ROOT")
            if dotnet_root and os.path.exists(dotnet_root):
                verification_result['dotnet_root_valid'] = True
            else:
                verification_result['errors'].append("DOTNET_ROOT not set or invalid")
            
            # Test verification commands
            for command in config.verification_commands:
                try:
                    result = subprocess.run(
                        command,
                        capture_output=True,
                        text=True,
                        timeout=30,
                        check=False
                    )
                    
                    if result.returncode == 0:
                        verification_result['commands_working'].append(' '.join(command))
                        
                        # Extract version information
                        if command[1] == "--version":
                            verification_result['version_detected'] = result.stdout.strip()
                    else:
                        verification_result['errors'].append(f"Command failed: {' '.join(command)}")
                        
                except subprocess.TimeoutExpired:
                    verification_result['errors'].append(f"Command timed out: {' '.join(command)}")
                except Exception as e:
                    verification_result['errors'].append(f"Command error: {' '.join(command)} - {e}")
            
            # Overall success check
            verification_result['success'] = (
                verification_result['dotnet_root_valid'] and
                len(verification_result['commands_working']) >= 1 and
                verification_result['version_detected'] is not None
            )
            
            return verification_result
            
        except Exception as e:
            verification_result['errors'].append(f"Verification error: {e}")
            return verification_result

class RuntimeSpecificInstallationManager:
    """
    Manager for runtime-specific installations
    
    Coordinates the installation of the 8 essential runtimes:
    - Java/OpenJDK
    - Python
    - Node.js
    - .NET
    - Go
    - Rust
    - GCC
    - CMake
    """
    
    def __init__(self, base_path: Optional[str] = None):
        self.base_path = base_path or os.getcwd()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Initialize runtime installers
        self.installers = {
            RuntimeType.JAVA: JavaInstaller(self.base_path),
            RuntimeType.PYTHON: PythonInstaller(self.base_path),
            RuntimeType.NODEJS: NodeJSInstaller(self.base_path),
            RuntimeType.DOTNET: DotNetInstaller(self.base_path),
            # TODO: Add remaining installers
            # RuntimeType.GO: GoInstaller(self.base_path),
            # RuntimeType.RUST: RustInstaller(self.base_path),
            # RuntimeType.GCC: GccInstaller(self.base_path),
            # RuntimeType.CMAKE: CMakeInstaller(self.base_path),
        }
        
        # Initialize preparation manager
        self.preparation_manager = IntelligentPreparationManager(self.base_path)
        
        self.logger.info(f"Runtime-Specific Installation Manager initialized with {len(self.installers)} installers")
    
    def install_runtime(self, runtime_type: RuntimeType, version: str = "latest", 
                       custom_config: Optional[RuntimeConfiguration] = None) -> RuntimeInstallationResult:
        """
        Install a specific runtime
        
        Args:
            runtime_type: Type of runtime to install
            version: Version to install (default: "latest")
            custom_config: Custom configuration (optional)
            
        Returns:
            RuntimeInstallationResult: Result of the installation
        """
        try:
            if runtime_type not in self.installers:
                return RuntimeInstallationResult(
                    success=False,
                    runtime_type=runtime_type,
                    version=version,
                    installed_path="",
                    message=f"No installer available for runtime type: {runtime_type.value}",
                    errors=[f"Unsupported runtime type: {runtime_type.value}"]
                )
            
            installer = self.installers[runtime_type]
            
            # Get configuration
            if custom_config:
                config = custom_config
            else:
                config = installer.get_default_configuration(version)
            
            self.logger.info(f"Installing {runtime_type.value} version {version}")
            
            # Prepare environment
            prep_result = self.preparation_manager.prepare_intelligent_environment(
                components=[runtime_type.value]
            )
            
            if prep_result.status.value != "completed":
                return RuntimeInstallationResult(
                    success=False,
                    runtime_type=runtime_type,
                    version=version,
                    installed_path="",
                    message=f"Environment preparation failed: {prep_result.message}",
                    errors=[f"Preparation failed: {prep_result.message}"]
                )
            
            # Install runtime
            result = installer.install_runtime(config)
            
            self.logger.info(f"Runtime installation completed: {result.message}")
            return result
            
        except Exception as e:
            self.logger.error(f"Critical error installing {runtime_type.value}: {e}")
            return RuntimeInstallationResult(
                success=False,
                runtime_type=runtime_type,
                version=version,
                installed_path="",
                message=f"Critical installation error: {e}",
                errors=[f"Critical error: {e}"]
            )
    
    def install_multiple_runtimes(self, runtime_specs: List[Tuple[RuntimeType, str]], 
                                 parallel: bool = True) -> Dict[RuntimeType, RuntimeInstallationResult]:
        """
        Install multiple runtimes
        
        Args:
            runtime_specs: List of (runtime_type, version) tuples
            parallel: Whether to install in parallel (default: True)
            
        Returns:
            Dict[RuntimeType, RuntimeInstallationResult]: Results for each runtime
        """
        results = {}
        
        try:
            self.logger.info(f"Installing {len(runtime_specs)} runtimes")
            
            # Prepare environment for all runtimes
            components = [spec[0].value for spec in runtime_specs]
            prep_result = self.preparation_manager.prepare_intelligent_environment(components)
            
            if prep_result.status.value != "completed":
                self.logger.warning(f"Environment preparation had issues: {prep_result.message}")
            
            if parallel:
                # TODO: Implement parallel installation
                # For now, install sequentially
                for runtime_type, version in runtime_specs:
                    results[runtime_type] = self.install_runtime(runtime_type, version)
            else:
                # Sequential installation
                for runtime_type, version in runtime_specs:
                    results[runtime_type] = self.install_runtime(runtime_type, version)
            
            successful = sum(1 for result in results.values() if result.success)
            self.logger.info(f"Multiple runtime installation completed: {successful}/{len(runtime_specs)} successful")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Critical error during multiple runtime installation: {e}")
            
            # Return error results for all runtimes
            for runtime_type, version in runtime_specs:
                if runtime_type not in results:
                    results[runtime_type] = RuntimeInstallationResult(
                        success=False,
                        runtime_type=runtime_type,
                        version=version,
                        installed_path="",
                        message=f"Installation failed due to critical error: {e}",
                        errors=[f"Critical error: {e}"]
                    )
            
            return results
    
    def verify_runtime(self, runtime_type: RuntimeType) -> Dict[str, Any]:
        """
        Verify a specific runtime installation
        
        Args:
            runtime_type: Type of runtime to verify
            
        Returns:
            Dict[str, Any]: Verification results
        """
        try:
            if runtime_type not in self.installers:
                return {
                    'success': False,
                    'errors': [f"No installer available for runtime type: {runtime_type.value}"]
                }
            
            installer = self.installers[runtime_type]
            config = installer.get_default_configuration()
            
            return installer.verify_installation(config)
            
        except Exception as e:
            return {
                'success': False,
                'errors': [f"Verification error: {e}"]
            }
    
    def get_supported_runtimes(self) -> List[RuntimeType]:
        """Get list of supported runtime types"""
        return list(self.installers.keys())
    
    def get_runtime_configuration(self, runtime_type: RuntimeType, version: str = "latest") -> Optional[RuntimeConfiguration]:
        """Get default configuration for a runtime"""
        try:
            if runtime_type not in self.installers:
                return None
            
            installer = self.installers[runtime_type]
            return installer.get_default_configuration(version)
            
        except Exception as e:
            self.logger.error(f"Error getting configuration for {runtime_type.value}: {e}")
            return None
    
    def generate_installation_report(self, results: Dict[RuntimeType, RuntimeInstallationResult]) -> Dict[str, Any]:
        """Generate detailed installation report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_runtimes': len(results),
            'successful_installations': 0,
            'failed_installations': 0,
            'total_installation_time': 0.0,
            'runtime_details': {},
            'summary': {
                'success_rate': 0.0,
                'average_installation_time': 0.0,
                'environment_variables_set': 0,
                'path_entries_added': 0
            }
        }
        
        try:
            for runtime_type, result in results.items():
                if result.success:
                    report['successful_installations'] += 1
                else:
                    report['failed_installations'] += 1
                
                report['total_installation_time'] += result.installation_time
                
                report['runtime_details'][runtime_type.value] = {
                    'success': result.success,
                    'version': result.version,
                    'installed_path': result.installed_path,
                    'installation_time': result.installation_time,
                    'message': result.message,
                    'errors': result.errors,
                    'warnings': result.warnings,
                    'environment_variables': result.environment_variables,
                    'path_entries': result.path_entries,
                    'verification_results': result.verification_results
                }
                
                # Count environment variables and path entries
                report['summary']['environment_variables_set'] += len(result.environment_variables)
                report['summary']['path_entries_added'] += len(result.path_entries)
            
            # Calculate summary statistics
            if report['total_runtimes'] > 0:
                report['summary']['success_rate'] = (report['successful_installations'] / report['total_runtimes']) * 100
                report['summary']['average_installation_time'] = report['total_installation_time'] / report['total_runtimes']
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating installation report: {e}")
            report['error'] = f"Report generation failed: {e}"
            return report