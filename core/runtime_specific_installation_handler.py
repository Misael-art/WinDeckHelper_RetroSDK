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
from pathlib import Path
from typing import Dict, Optional, Tuple, List, Any, Set, Union
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from core.error_handler import EnvDevError, ErrorSeverity, ErrorCategory
from core.advanced_installation_manager import AdvancedInstallationManager
from core.intelligent_preparation_manager import IntelligentPreparationManager

logger = logging.getLogger(__name__)

class RuntimeType(Enum):
    """Supported runtime types"""
    JAVA = "java"
    PYTHON = "python"
    NODEJS = "nodejs"
    DOTNET = "dotnet"
    GO = "go"
    RUST = "rust"
    CPP = "cpp"
    GIT = "git"

@dataclass
class RuntimeConfiguration:
    """Configuration for a specific runtime"""
    name: str
    runtime_type: RuntimeType
    version: str
    download_url: str
    install_method: str
    install_args: List[str] = field(default_factory=list)
    environment_variables: Dict[str, str] = field(default_factory=dict)
    path_entries: List[str] = field(default_factory=list)
    verification_commands: List[List[str]] = field(default_factory=list)
    verification_paths: List[str] = field(default_factory=list)
    post_install_commands: List[List[str]] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class RuntimeInstallationResult:
    """Result of runtime installation"""
    success: bool
    runtime_type: RuntimeType
    version: str
    installed_path: str
    environment_variables: Dict[str, str] = field(default_factory=dict)
    path_entries: List[str] = field(default_factory=list)
    verification_results: Dict[str, Any] = field(default_factory=dict)
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
        """Verify the runtime installation"""
        pass
    
    def get_install_path(self, config: RuntimeConfiguration) -> str:
        """Get the installation path for this runtime"""
        return os.path.join(self.base_path, config.runtime_type.value)

class JavaInstaller(RuntimeInstaller):
    """Java runtime installer"""
    
    def get_runtime_type(self) -> RuntimeType:
        return RuntimeType.JAVA
    
    def get_default_configuration(self, version: str = "17") -> RuntimeConfiguration:
        """Get default Java configuration"""
        if self.is_windows:
            download_url = f"https://download.oracle.com/java/{version}/latest/jdk-{version}_windows-x64_bin.exe"
            install_method = "executable"
            install_args = ["/s", "INSTALLDIR=" + self.get_install_path(RuntimeConfiguration("java", RuntimeType.JAVA, version, "", ""))]
        else:
            download_url = f"https://download.oracle.com/java/{version}/latest/jdk-{version}_linux-x64_bin.tar.gz"
            install_method = "archive"
            install_args = []
        
        install_path = self.get_install_path(RuntimeConfiguration("java", RuntimeType.JAVA, version, "", ""))
        
        return RuntimeConfiguration(
            name="java",
            runtime_type=RuntimeType.JAVA,
            version=version,
            download_url=download_url,
            install_method=install_method,
            install_args=install_args,
            environment_variables={
                "JAVA_HOME": install_path,
                "JDK_HOME": install_path
            },
            path_entries=[os.path.join(install_path, "bin")],
            verification_commands=[["java", "-version"], ["javac", "-version"]],
            verification_paths=[
                os.path.join(install_path, "bin", "java.exe" if self.is_windows else "java"),
                os.path.join(install_path, "bin", "javac.exe" if self.is_windows else "javac")
            ]
        )
    
    def install_runtime(self, config: RuntimeConfiguration) -> RuntimeInstallationResult:
        """Install Java runtime"""
        start_time = datetime.now()
        result = RuntimeInstallationResult(
            success=False,
            runtime_type=RuntimeType.JAVA,
            version=config.version,
            installed_path=self.get_install_path(config)
        )
        
        try:
            self.logger.info(f"Installing Java {config.version}")
            
            # Use advanced installation manager for atomic installation
            installation_manager = AdvancedInstallationManager(self.base_path)
            
            # Prepare component data for installation manager
            component_data = {
                'install_method': config.install_method,
                'download_url': config.download_url,
                'filename': f"jdk-{config.version}.{'exe' if self.is_windows else 'tar.gz'}",
                'install_args': config.install_args,
                'install_path': result.installed_path,
                'environment_variables': config.environment_variables,
                'verification_commands': config.verification_commands,
                'verification_paths': config.verification_paths
            }
            
            # Perform installation
            install_result = installation_manager.install_component_atomic(
                f"java-{config.version}", 
                component_data
            )
            
            if install_result.success:
                # Post-installation configuration
                self._configure_java_environment(config, result)
                
                # Verify installation
                verification_result = self.verify_installation(config)
                result.verification_results = verification_result
                
                if verification_result['success']:
                    result.success = True
                    result.message = f"Java {config.version} installed successfully"
                    result.environment_variables = config.environment_variables
                    result.path_entries = config.path_entries
                else:
                    result.message = f"Java installation failed verification: {verification_result['message']}"
                    result.errors.append(verification_result['message'])
            else:
                result.message = f"Java installation failed: {install_result.message}"
                result.errors.append(install_result.message)
            
            end_time = datetime.now()
            result.installation_time = (end_time - start_time).total_seconds()
            
            return result
            
        except Exception as e:
            end_time = datetime.now()
            result.installation_time = (end_time - start_time).total_seconds()
            result.message = f"Critical error during Java installation: {e}"
            result.errors.append(str(e))
            self.logger.error(f"Critical error during Java installation: {e}")
            return result
    
    def _configure_java_environment(self, config: RuntimeConfiguration, result: RuntimeInstallationResult):
        """Configure Java-specific environment"""
        try:
            # Set up Maven if needed
            maven_path = os.path.join(result.installed_path, "maven")
            if not os.path.exists(maven_path):
                self.logger.info("Setting up Maven")
                # Download and setup Maven
                # This is a simplified version - in reality you'd download Maven
                os.makedirs(maven_path, exist_ok=True)
                result.environment_variables["M2_HOME"] = maven_path
                result.path_entries.append(os.path.join(maven_path, "bin"))
            
            # Create Java project template
            templates_path = os.path.join(result.installed_path, "templates")
            os.makedirs(templates_path, exist_ok=True)
            
            # Create a simple Hello World template
            hello_world_template = """public class HelloWorld {
    public static void main(String[] args) {
        System.out.println("Hello, World!");
    }
}"""
            
            with open(os.path.join(templates_path, "HelloWorld.java"), 'w') as f:
                f.write(hello_world_template)
            
            self.logger.info("Java environment configured successfully")
            
        except Exception as e:
            result.warnings.append(f"Failed to configure Java environment: {e}")
            self.logger.warning(f"Failed to configure Java environment: {e}")
    
    def verify_installation(self, config: RuntimeConfiguration) -> Dict[str, Any]:
        """Verify Java installation"""
        result = {
            'success': False,
            'message': '',
            'details': {}
        }
        
        try:
            # Check if Java executable exists
            java_exe = os.path.join(self.get_install_path(config), "bin", "java.exe" if self.is_windows else "java")
            if not os.path.exists(java_exe):
                result['message'] = f"Java executable not found: {java_exe}"
                return result
            
            # Run java -version
            try:
                java_result = subprocess.run(
                    [java_exe, "-version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if java_result.returncode == 0:
                    result['details']['java_version'] = java_result.stderr.strip()
                    result['success'] = True
                    result['message'] = "Java installation verified successfully"
                else:
                    result['message'] = f"Java version check failed: {java_result.stderr}"
                    
            except subprocess.TimeoutExpired:
                result['message'] = "Java version check timed out"
            except Exception as e:
                result['message'] = f"Error running Java version check: {e}"
            
            return result
            
        except Exception as e:
            result['message'] = f"Error during Java verification: {e}"
            return result

class PythonInstaller(RuntimeInstaller):
    """Python runtime installer"""
    
    def get_runtime_type(self) -> RuntimeType:
        return RuntimeType.PYTHON
    
    def get_default_configuration(self, version: str = "3.11") -> RuntimeConfiguration:
        """Get default Python configuration"""
        if self.is_windows:
            download_url = f"https://www.python.org/ftp/python/{version}.0/python-{version}.0-amd64.exe"
            install_method = "executable"
            install_args = ["/quiet", "InstallAllUsers=1", f"TargetDir={self.get_install_path(RuntimeConfiguration('python', RuntimeType.PYTHON, version, '', ''))}"]
        else:
            download_url = f"https://www.python.org/ftp/python/{version}.0/Python-{version}.0.tgz"
            install_method = "archive"
            install_args = []
        
        install_path = self.get_install_path(RuntimeConfiguration("python", RuntimeType.PYTHON, version, "", ""))
        
        return RuntimeConfiguration(
            name="python",
            runtime_type=RuntimeType.PYTHON,
            version=version,
            download_url=download_url,
            install_method=install_method,
            install_args=install_args,
            environment_variables={
                "PYTHON_HOME": install_path,
                "PYTHONPATH": os.path.join(install_path, "Lib" if self.is_windows else "lib")
            },
            path_entries=[
                install_path,
                os.path.join(install_path, "Scripts" if self.is_windows else "bin")
            ],
            verification_commands=[["python", "--version"], ["pip", "--version"]],
            verification_paths=[
                os.path.join(install_path, "python.exe" if self.is_windows else "bin/python"),
                os.path.join(install_path, "Scripts/pip.exe" if self.is_windows else "bin/pip")
            ]
        )
    
    def install_runtime(self, config: RuntimeConfiguration) -> RuntimeInstallationResult:
        """Install Python runtime"""
        start_time = datetime.now()
        result = RuntimeInstallationResult(
            success=False,
            runtime_type=RuntimeType.PYTHON,
            version=config.version,
            installed_path=self.get_install_path(config)
        )
        
        try:
            self.logger.info(f"Installing Python {config.version}")
            
            # Use advanced installation manager
            installation_manager = AdvancedInstallationManager(self.base_path)
            
            component_data = {
                'install_method': config.install_method,
                'download_url': config.download_url,
                'filename': f"python-{config.version}.{'exe' if self.is_windows else 'tgz'}",
                'install_args': config.install_args,
                'install_path': result.installed_path,
                'environment_variables': config.environment_variables,
                'verification_commands': config.verification_commands,
                'verification_paths': config.verification_paths
            }
            
            install_result = installation_manager.install_component_atomic(
                f"python-{config.version}", 
                component_data
            )
            
            if install_result.success:
                # Post-installation configuration
                self._configure_python_environment(config, result)
                
                # Verify installation
                verification_result = self.verify_installation(config)
                result.verification_results = verification_result
                
                if verification_result['success']:
                    result.success = True
                    result.message = f"Python {config.version} installed successfully"
                    result.environment_variables = config.environment_variables
                    result.path_entries = config.path_entries
                else:
                    result.message = f"Python installation failed verification: {verification_result['message']}"
                    result.errors.append(verification_result['message'])
            else:
                result.message = f"Python installation failed: {install_result.message}"
                result.errors.append(install_result.message)
            
            end_time = datetime.now()
            result.installation_time = (end_time - start_time).total_seconds()
            
            return result
            
        except Exception as e:
            end_time = datetime.now()
            result.installation_time = (end_time - start_time).total_seconds()
            result.message = f"Critical error during Python installation: {e}"
            result.errors.append(str(e))
            self.logger.error(f"Critical error during Python installation: {e}")
            return result
    
    def _configure_python_environment(self, config: RuntimeConfiguration, result: RuntimeInstallationResult):
        """Configure Python-specific environment"""
        try:
            # Install common packages
            pip_exe = os.path.join(result.installed_path, "Scripts/pip.exe" if self.is_windows else "bin/pip")
            if os.path.exists(pip_exe):
                common_packages = ["requests", "numpy", "pandas", "matplotlib", "pytest"]
                for package in common_packages:
                    try:
                        subprocess.run([pip_exe, "install", package], 
                                     capture_output=True, timeout=60, check=False)
                        self.logger.debug(f"Installed Python package: {package}")
                    except Exception as e:
                        result.warnings.append(f"Failed to install package {package}: {e}")
            
            # Create virtual environment template
            venv_template_path = os.path.join(result.installed_path, "templates", "venv")
            os.makedirs(venv_template_path, exist_ok=True)
            
            # Create requirements.txt template
            requirements_template = """# Common Python packages
requests>=2.28.0
numpy>=1.21.0
pandas>=1.3.0
matplotlib>=3.5.0
pytest>=7.0.0
"""
            
            with open(os.path.join(venv_template_path, "requirements.txt"), 'w') as f:
                f.write(requirements_template)
            
            self.logger.info("Python environment configured successfully")
            
        except Exception as e:
            result.warnings.append(f"Failed to configure Python environment: {e}")
            self.logger.warning(f"Failed to configure Python environment: {e}")
    
    def verify_installation(self, config: RuntimeConfiguration) -> Dict[str, Any]:
        """Verify Python installation"""
        result = {
            'success': False,
            'message': '',
            'details': {}
        }
        
        try:
            # Check if Python executable exists
            python_exe = os.path.join(self.get_install_path(config), "python.exe" if self.is_windows else "bin/python")
            if not os.path.exists(python_exe):
                result['message'] = f"Python executable not found: {python_exe}"
                return result
            
            # Run python --version
            try:
                python_result = subprocess.run(
                    [python_exe, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if python_result.returncode == 0:
                    result['details']['python_version'] = python_result.stdout.strip()
                    result['success'] = True
                    result['message'] = "Python installation verified successfully"
                else:
                    result['message'] = f"Python version check failed: {python_result.stderr}"
                    
            except subprocess.TimeoutExpired:
                result['message'] = "Python version check timed out"
            except Exception as e:
                result['message'] = f"Error running Python version check: {e}"
            
            return result
            
        except Exception as e:
            result['message'] = f"Error during Python verification: {e}"
            return result

class NodeJSInstaller(RuntimeInstaller):
    """Node.js runtime installer"""
    
    def get_runtime_type(self) -> RuntimeType:
        return RuntimeType.NODEJS
    
    def get_default_configuration(self, version: str = "18") -> RuntimeConfiguration:
        """Get default Node.js configuration"""
        if self.is_windows:
            download_url = f"https://nodejs.org/dist/v{version}.0.0/node-v{version}.0.0-x64.msi"
            install_method = "msi"
            install_args = ["/quiet"]
        else:
            download_url = f"https://nodejs.org/dist/v{version}.0.0/node-v{version}.0.0-linux-x64.tar.xz"
            install_method = "archive"
            install_args = []
        
        install_path = self.get_install_path(RuntimeConfiguration("nodejs", RuntimeType.NODEJS, version, "", ""))
        
        return RuntimeConfiguration(
            name="nodejs",
            runtime_type=RuntimeType.NODEJS,
            version=version,
            download_url=download_url,
            install_method=install_method,
            install_args=install_args,
            environment_variables={
                "NODE_HOME": install_path,
                "NPM_CONFIG_PREFIX": os.path.join(install_path, "global")
            },
            path_entries=[
                install_path,
                os.path.join(install_path, "global", "bin")
            ],
            verification_commands=[["node", "--version"], ["npm", "--version"]],
            verification_paths=[
                os.path.join(install_path, "node.exe" if self.is_windows else "bin/node"),
                os.path.join(install_path, "npm.cmd" if self.is_windows else "bin/npm")
            ]
        )
    
    def install_runtime(self, config: RuntimeConfiguration) -> RuntimeInstallationResult:
        """Install Node.js runtime"""
        start_time = datetime.now()
        result = RuntimeInstallationResult(
            success=False,
            runtime_type=RuntimeType.NODEJS,
            version=config.version,
            installed_path=self.get_install_path(config)
        )
        
        try:
            self.logger.info(f"Installing Node.js {config.version}")
            
            # Use advanced installation manager
            installation_manager = AdvancedInstallationManager(self.base_path)
            
            component_data = {
                'install_method': config.install_method,
                'download_url': config.download_url,
                'filename': f"nodejs-{config.version}.{'msi' if self.is_windows else 'tar.xz'}",
                'install_args': config.install_args,
                'install_path': result.installed_path,
                'environment_variables': config.environment_variables,
                'verification_commands': config.verification_commands,
                'verification_paths': config.verification_paths
            }
            
            install_result = installation_manager.install_component_atomic(
                f"nodejs-{config.version}", 
                component_data
            )
            
            if install_result.success:
                # Post-installation configuration
                self._configure_nodejs_environment(config, result)
                
                # Verify installation
                verification_result = self.verify_installation(config)
                result.verification_results = verification_result
                
                if verification_result['success']:
                    result.success = True
                    result.message = f"Node.js {config.version} installed successfully"
                    result.environment_variables = config.environment_variables
                    result.path_entries = config.path_entries
                else:
                    result.message = f"Node.js installation failed verification: {verification_result['message']}"
                    result.errors.append(verification_result['message'])
            else:
                result.message = f"Node.js installation failed: {install_result.message}"
                result.errors.append(install_result.message)
            
            end_time = datetime.now()
            result.installation_time = (end_time - start_time).total_seconds()
            
            return result
            
        except Exception as e:
            end_time = datetime.now()
            result.installation_time = (end_time - start_time).total_seconds()
            result.message = f"Critical error during Node.js installation: {e}"
            result.errors.append(str(e))
            self.logger.error(f"Critical error during Node.js installation: {e}")
            return result
    
    def _configure_nodejs_environment(self, config: RuntimeConfiguration, result: RuntimeInstallationResult):
        """Configure Node.js-specific environment"""
        try:
            # Install common global packages
            npm_exe = os.path.join(result.installed_path, "npm.cmd" if self.is_windows else "bin/npm")
            if os.path.exists(npm_exe):
                global_packages = ["typescript", "nodemon", "express-generator", "create-react-app"]
                for package in global_packages:
                    try:
                        subprocess.run([npm_exe, "install", "-g", package], 
                                     capture_output=True, timeout=120, check=False)
                        self.logger.debug(f"Installed Node.js global package: {package}")
                    except Exception as e:
                        result.warnings.append(f"Failed to install global package {package}: {e}")
            
            # Create project templates
            templates_path = os.path.join(result.installed_path, "templates")
            os.makedirs(templates_path, exist_ok=True)
            
            # Create package.json template
            package_json_template = """{
  "name": "my-node-project",
  "version": "1.0.0",
  "description": "A Node.js project template",
  "main": "index.js",
  "scripts": {
    "start": "node index.js",
    "dev": "nodemon index.js",
    "test": "jest"
  },
  "dependencies": {
    "express": "^4.18.0"
  },
  "devDependencies": {
    "nodemon": "^2.0.0",
    "jest": "^29.0.0"
  }
}"""
            
            with open(os.path.join(templates_path, "package.json"), 'w') as f:
                f.write(package_json_template)
            
            # Create index.js template
            index_js_template = """const express = require('express');
const app = express();
const port = process.env.PORT || 3000;

app.get('/', (req, res) => {
  res.send('Hello World!');
});

app.listen(port, () => {
  console.log(`Server running at http://localhost:${port}`);
});"""
            
            with open(os.path.join(templates_path, "index.js"), 'w') as f:
                f.write(index_js_template)
            
            self.logger.info("Node.js environment configured successfully")
            
        except Exception as e:
            result.warnings.append(f"Failed to configure Node.js environment: {e}")
            self.logger.warning(f"Failed to configure Node.js environment: {e}")
    
    def verify_installation(self, config: RuntimeConfiguration) -> Dict[str, Any]:
        """Verify Node.js installation"""
        result = {
            'success': False,
            'message': '',
            'details': {}
        }
        
        try:
            # Check if Node.js executable exists
            node_exe = os.path.join(self.get_install_path(config), "node.exe" if self.is_windows else "bin/node")
            if not os.path.exists(node_exe):
                result['message'] = f"Node.js executable not found: {node_exe}"
                return result
            
            # Run node --version
            try:
                node_result = subprocess.run(
                    [node_exe, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if node_result.returncode == 0:
                    result['details']['node_version'] = node_result.stdout.strip()
                    result['success'] = True
                    result['message'] = "Node.js installation verified successfully"
                else:
                    result['message'] = f"Node.js version check failed: {node_result.stderr}"
                    
            except subprocess.TimeoutExpired:
                result['message'] = "Node.js version check timed out"
            except Exception as e:
                result['message'] = f"Error running Node.js version check: {e}"
            
            return result
            
        except Exception as e:
            result['message'] = f"Error during Node.js verification: {e}"
            return resultclass
 RuntimeSpecificInstallationHandler:
    """
    Main handler for runtime-specific installations
    
    Manages installation of the 8 essential runtimes:
    - Java
    - Python
    - Node.js
    - .NET
    - Go
    - Rust
    - C++
    - Git
    """
    
    def __init__(self, base_path: Optional[str] = None):
        self.base_path = base_path or os.getcwd()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        # Initialize preparation manager
        self.preparation_manager = IntelligentPreparationManager(self.base_path)
        
        # Initialize runtime installers
        self.installers: Dict[RuntimeType, RuntimeInstaller] = {
            RuntimeType.JAVA: JavaInstaller(self.base_path),
            R