#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Essential Runtime Detector - Detects and validates essential development runtimes.

This module implements detection for the 8 essential runtimes required by the Environment Dev system:
1. Git 2.47.1
2. .NET SDK 8.0
3. Java JDK 21
4. Visual C++ Redistributables
5. Anaconda3
6. .NET Desktop Runtime 8.0/9.0
7. PowerShell 7
8. Node.js/Python updated

Each runtime has specific detection logic with version verification and environment variable detection.
"""

import os
import sys
import json
import logging
import platform
import subprocess
import re
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Set, Tuple, Union
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import time

# Importação condicional do winreg para Windows
try:
    import winreg
except ImportError:
    winreg = None

from .detection_base import DetectionStrategy, DetectedApplication, DetectionMethod, ApplicationStatus


@dataclass
class RuntimeDetectionResult:
    """Result of runtime detection with comprehensive information."""
    runtime_name: str
    detected: bool = False
    version: Optional[str] = None
    install_path: Optional[str] = None
    executable_path: Optional[str] = None
    environment_variables: Dict[str, str] = field(default_factory=dict)
    validation_commands: List[str] = field(default_factory=list)
    validation_results: Dict[str, bool] = field(default_factory=dict)
    detection_method: DetectionMethod = DetectionMethod.MANUAL_OVERRIDE
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class EnvironmentVariableInfo:
    """Information about environment variables for a runtime."""
    name: str
    expected_value: Optional[str] = None
    current_value: Optional[str] = None
    is_set: bool = False
    is_correct: bool = False
    description: str = ""


class EssentialRuntimeDetector:
    """
    Detector for essential development runtimes with comprehensive validation.
    
    This class implements detection logic for all 8 essential runtimes required
    by the Environment Dev system, including version verification and environment
    variable validation.
    """
    
    def __init__(self):
        """Initialize the essential runtime detector."""
        self.logger = logging.getLogger("EssentialRuntimeDetector")
        
        # Runtime configurations for the 8 essential runtimes
        self._runtime_configs = {
            "git": {
                "name": "Git",
                "target_version": "2.47.1",
                "version_command": ["git", "--version"],
                "version_regex": r"git version (\d+\.\d+\.\d+)",
                "executable_names": ["git.exe", "git"],
                "registry_keys": [
                    r"SOFTWARE\GitForWindows",
                    r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Git_is1"
                ],
                "environment_variables": {
                    "GIT_HOME": "Git installation directory",
                    "PATH": "Should contain Git bin directory"
                },
                "validation_commands": [
                    ["git", "--version"],
                    ["git", "config", "--global", "--list"]
                ],
                "common_paths": [
                    r"C:\Program Files\Git",
                    r"C:\Program Files (x86)\Git",
                    r"C:\Git"
                ]
            },
            "dotnet_sdk": {
                "name": ".NET SDK",
                "target_version": "8.0",
                "version_command": ["dotnet", "--version"],
                "version_regex": r"(\d+\.\d+\.\d+)",
                "executable_names": ["dotnet.exe", "dotnet"],
                "registry_keys": [
                    r"SOFTWARE\dotnet\Setup\InstalledVersions\x64\sdk",
                    r"SOFTWARE\WOW6432Node\dotnet\Setup\InstalledVersions\x86\sdk"
                ],
                "environment_variables": {
                    "DOTNET_ROOT": ".NET installation root",
                    "PATH": "Should contain .NET directory"
                },
                "validation_commands": [
                    ["dotnet", "--version"],
                    ["dotnet", "--list-sdks"],
                    ["dotnet", "--list-runtimes"]
                ],
                "common_paths": [
                    r"C:\Program Files\dotnet",
                    r"C:\Program Files (x86)\dotnet"
                ]
            },
            "java_jdk": {
                "name": "Java JDK",
                "target_version": "21",
                "version_command": ["java", "-version"],
                "version_regex": r"openjdk version \"(\d+)\..*?\"",
                "executable_names": ["java.exe", "javac.exe", "java", "javac"],
                "registry_keys": [
                    r"SOFTWARE\JavaSoft\JDK",
                    r"SOFTWARE\JavaSoft\Java Development Kit",
                    r"SOFTWARE\WOW6432Node\JavaSoft\JDK"
                ],
                "environment_variables": {
                    "JAVA_HOME": "Java JDK installation directory",
                    "PATH": "Should contain Java bin directory"
                },
                "validation_commands": [
                    ["java", "-version"],
                    ["javac", "-version"]
                ],
                "common_paths": [
                    r"C:\Program Files\Java",
                    r"C:\Program Files\Eclipse Adoptium",
                    r"C:\Program Files\Microsoft"
                ]
            },
            "vcpp_redistributables": {
                "name": "Visual C++ Redistributables",
                "target_version": "14.0",  # Visual Studio 2015-2022
                "version_command": None,  # No direct command, use registry
                "version_regex": r"(\d+\.\d+)",
                "executable_names": [],
                "registry_keys": [
                    r"SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64",
                    r"SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x86",
                    r"SOFTWARE\WOW6432Node\Microsoft\VisualStudio\14.0\VC\Runtimes\x64",
                    r"SOFTWARE\WOW6432Node\Microsoft\VisualStudio\14.0\VC\Runtimes\x86"
                ],
                "environment_variables": {},
                "validation_commands": [],
                "common_paths": [
                    r"C:\Windows\System32",
                    r"C:\Windows\SysWOW64"
                ]
            },
            "anaconda3": {
                "name": "Anaconda3",
                "target_version": "3.11",  # Python version in Anaconda
                "version_command": ["conda", "--version"],
                "version_regex": r"conda (\d+\.\d+\.\d+)",
                "executable_names": ["conda.exe", "python.exe", "conda", "python"],
                "registry_keys": [
                    r"SOFTWARE\Python\ContinuumAnalytics",
                    r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Anaconda3"
                ],
                "environment_variables": {
                    "CONDA_DEFAULT_ENV": "Default conda environment",
                    "CONDA_PREFIX": "Current conda environment prefix",
                    "PATH": "Should contain Anaconda directories"
                },
                "validation_commands": [
                    ["conda", "--version"],
                    ["conda", "info"],
                    ["python", "--version"]
                ],
                "common_paths": [
                    r"C:\Users\{username}\anaconda3",
                    r"C:\Users\{username}\miniconda3",
                    r"C:\Anaconda3",
                    r"C:\ProgramData\Anaconda3"
                ]
            },
            "dotnet_desktop_runtime": {
                "name": ".NET Desktop Runtime",
                "target_version": "8.0",  # Also supports 9.0
                "version_command": ["dotnet", "--list-runtimes"],
                "version_regex": r"Microsoft\.WindowsDesktop\.App (\d+\.\d+\.\d+)",
                "executable_names": ["dotnet.exe", "dotnet"],
                "registry_keys": [
                    r"SOFTWARE\dotnet\Setup\InstalledVersions\x64\Microsoft.WindowsDesktop.App",
                    r"SOFTWARE\WOW6432Node\dotnet\Setup\InstalledVersions\x86\Microsoft.WindowsDesktop.App"
                ],
                "environment_variables": {
                    "DOTNET_ROOT": ".NET installation root",
                    "PATH": "Should contain .NET directory"
                },
                "validation_commands": [
                    ["dotnet", "--list-runtimes"]
                ],
                "common_paths": [
                    r"C:\Program Files\dotnet",
                    r"C:\Program Files (x86)\dotnet"
                ]
            },
            "powershell": {
                "name": "PowerShell",
                "target_version": "7.0",
                "version_command": ["pwsh", "-Command", "$PSVersionTable.PSVersion.ToString()"],
                "version_regex": r"(\d+\.\d+\.\d+)",
                "executable_names": ["pwsh.exe", "powershell.exe", "pwsh", "powershell"],
                "registry_keys": [
                    r"SOFTWARE\Microsoft\PowerShell\7",
                    r"SOFTWARE\Microsoft\PowerShell\1"
                ],
                "environment_variables": {
                    "PSModulePath": "PowerShell module paths",
                    "PATH": "Should contain PowerShell directory"
                },
                "validation_commands": [
                    ["pwsh", "-Command", "$PSVersionTable.PSVersion.ToString()"],
                    ["pwsh", "-Command", "Get-Module -ListAvailable | Select-Object -First 5"]
                ],
                "common_paths": [
                    r"C:\Program Files\PowerShell\7",
                    r"C:\Windows\System32\WindowsPowerShell\v1.0"
                ]
            },
            "nodejs_python": {
                "name": "Node.js/Python Updated",
                "target_version": "20.0",  # Node.js LTS
                "version_command": ["node", "--version"],
                "version_regex": r"v(\d+\.\d+\.\d+)",
                "executable_names": ["node.exe", "npm.exe", "python.exe", "node", "npm", "python"],
                "registry_keys": [
                    r"SOFTWARE\Node.js",
                    r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{*Node.js*}"
                ],
                "environment_variables": {
                    "NODE_PATH": "Node.js module paths",
                    "PATH": "Should contain Node.js and Python directories"
                },
                "validation_commands": [
                    ["node", "--version"],
                    ["npm", "--version"],
                    ["python", "--version"]
                ],
                "common_paths": [
                    r"C:\Program Files\nodejs",
                    r"C:\Program Files (x86)\nodejs",
                    r"C:\Users\{username}\AppData\Roaming\npm"
                ]
            }
        }
    
    def detect_all_essential_runtimes(self) -> List[RuntimeDetectionResult]:
        """
        Detect all 8 essential runtimes.
        
        Returns:
            List of RuntimeDetectionResult for each essential runtime
        """
        results = []
        
        self.logger.info("Starting detection of all essential runtimes...")
        
        for runtime_key, config in self._runtime_configs.items():
            self.logger.info(f"Detecting {config['name']}...")
            result = self._detect_single_runtime(runtime_key, config)
            results.append(result)
            
            if result.detected:
                self.logger.info(f"✅ {config['name']} detected: v{result.version}")
            else:
                self.logger.warning(f"❌ {config['name']} not detected")
        
        detected_count = sum(1 for r in results if r.detected)
        self.logger.info(f"Detection complete: {detected_count}/{len(results)} runtimes detected")
        
        return results
    
    def _detect_single_runtime(self, runtime_key: str, config: Dict[str, Any]) -> RuntimeDetectionResult:
        """
        Detect a single runtime using multiple detection methods.
        
        Args:
            runtime_key: Key identifying the runtime
            config: Runtime configuration dictionary
            
        Returns:
            RuntimeDetectionResult with detection information
        """
        result = RuntimeDetectionResult(
            runtime_name=config["name"],
            detected=False,
            confidence=0.0
        )
        
        try:
            # Method 1: Command-line detection
            if config.get("version_command"):
                cmd_result = self._detect_via_command(config)
                if cmd_result["detected"]:
                    result.detected = True
                    result.version = cmd_result["version"]
                    result.executable_path = cmd_result.get("executable_path")
                    result.detection_method = DetectionMethod.PATH_BASED
                    result.confidence = 0.9
            
            # Method 2: Registry detection (Windows)
            if not result.detected and platform.system() == "Windows" and winreg:
                reg_result = self._detect_via_registry(config)
                if reg_result["detected"]:
                    result.detected = True
                    result.version = reg_result.get("version", "Unknown")
                    result.install_path = reg_result.get("install_path")
                    result.detection_method = DetectionMethod.REGISTRY
                    result.confidence = 0.8
            
            # Method 3: Filesystem scanning
            if not result.detected:
                fs_result = self._detect_via_filesystem(config)
                if fs_result["detected"]:
                    result.detected = True
                    result.version = fs_result.get("version", "Unknown")
                    result.install_path = fs_result.get("install_path")
                    result.executable_path = fs_result.get("executable_path")
                    result.detection_method = DetectionMethod.EXECUTABLE_SCAN
                    result.confidence = 0.7
            
            # Environment variable detection
            result.environment_variables = self._detect_environment_variables(config)
            
            # Validation if detected
            if result.detected:
                result.validation_results = self._validate_runtime(config, result)
                
                # Adjust confidence based on validation
                validation_success_rate = sum(result.validation_results.values()) / max(len(result.validation_results), 1)
                result.confidence *= (0.5 + 0.5 * validation_success_rate)
            
            # Special handling for specific runtimes
            result = self._apply_runtime_specific_logic(runtime_key, config, result)
            
        except Exception as e:
            result.errors.append(f"Detection error: {str(e)}")
            self.logger.error(f"Error detecting {config['name']}: {e}")
        
        return result
    
    def _detect_via_command(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Detect runtime via command-line execution."""
        result = {"detected": False}
        
        try:
            version_command = config.get("version_command")
            if not version_command:
                return result
            
            # Execute version command
            process_result = subprocess.run(
                version_command,
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
            )
            
            if process_result.returncode == 0:
                output = process_result.stdout + process_result.stderr
                
                # Extract version using regex
                version_regex = config.get("version_regex")
                if version_regex:
                    match = re.search(version_regex, output)
                    if match:
                        result["detected"] = True
                        result["version"] = match.group(1)
                        
                        # Try to find executable path
                        executable_path = self._find_executable_path(version_command[0])
                        if executable_path:
                            result["executable_path"] = executable_path
                
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError) as e:
            self.logger.debug(f"Command detection failed: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error in command detection: {e}")
        
        return result
    
    def _detect_via_registry(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Detect runtime via Windows Registry."""
        result = {"detected": False}
        
        if not winreg or platform.system() != "Windows":
            return result
        
        try:
            registry_keys = config.get("registry_keys", [])
            
            for key_path in registry_keys:
                try:
                    # Try both HKEY_LOCAL_MACHINE and HKEY_CURRENT_USER
                    for hkey in [winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER]:
                        try:
                            with winreg.OpenKey(hkey, key_path) as key:
                                # Try to get version information
                                version = self._get_registry_version(key)
                                if version:
                                    result["detected"] = True
                                    result["version"] = version
                                
                                # Try to get install path
                                install_path = self._get_registry_install_path(key)
                                if install_path:
                                    result["install_path"] = install_path
                                
                                if result["detected"]:
                                    return result
                                    
                        except WindowsError:
                            continue
                            
                except Exception as e:
                    self.logger.debug(f"Registry key {key_path} failed: {e}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"Registry detection error: {e}")
        
        return result
    
    def _detect_via_filesystem(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Detect runtime via filesystem scanning."""
        result = {"detected": False}
        
        try:
            common_paths = config.get("common_paths", [])
            executable_names = config.get("executable_names", [])
            
            # Replace username placeholder
            username = os.getenv("USERNAME", "User")
            expanded_paths = [path.replace("{username}", username) for path in common_paths]
            
            for base_path in expanded_paths:
                if not os.path.exists(base_path):
                    continue
                
                # Search for executables in this path
                for root, dirs, files in os.walk(base_path):
                    for executable_name in executable_names:
                        if executable_name in files:
                            executable_path = os.path.join(root, executable_name)
                            
                            # Try to get version from this executable
                            version = self._get_executable_version(executable_path, config)
                            
                            result["detected"] = True
                            result["executable_path"] = executable_path
                            result["install_path"] = base_path
                            if version:
                                result["version"] = version
                            
                            return result
                    
                    # Limit depth to avoid excessive scanning
                    if len(root.split(os.sep)) - len(base_path.split(os.sep)) > 3:
                        dirs.clear()
                        
        except Exception as e:
            self.logger.error(f"Filesystem detection error: {e}")
        
        return result
    
    def _detect_environment_variables(self, config: Dict[str, Any]) -> Dict[str, str]:
        """Detect and validate environment variables for a runtime."""
        env_vars = {}
        
        expected_vars = config.get("environment_variables", {})
        
        for var_name, description in expected_vars.items():
            current_value = os.getenv(var_name)
            if current_value:
                env_vars[var_name] = current_value
        
        return env_vars
    
    def _validate_runtime(self, config: Dict[str, Any], result: RuntimeDetectionResult) -> Dict[str, bool]:
        """Validate runtime installation using validation commands."""
        validation_results = {}
        
        validation_commands = config.get("validation_commands", [])
        
        for i, command in enumerate(validation_commands):
            command_name = f"validation_{i+1}"
            
            try:
                process_result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    timeout=10,
                    creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
                )
                
                validation_results[command_name] = process_result.returncode == 0
                
            except Exception as e:
                validation_results[command_name] = False
                self.logger.debug(f"Validation command {command} failed: {e}")
        
        return validation_results
    
    def _apply_runtime_specific_logic(self, runtime_key: str, config: Dict[str, Any], result: RuntimeDetectionResult) -> RuntimeDetectionResult:
        """Apply runtime-specific detection logic."""
        
        if runtime_key == "vcpp_redistributables":
            # Special handling for Visual C++ Redistributables
            result = self._detect_vcpp_redistributables_special(result)
        
        elif runtime_key == "dotnet_desktop_runtime":
            # Special handling for .NET Desktop Runtime (supports both 8.0 and 9.0)
            result = self._detect_dotnet_desktop_special(result)
        
        elif runtime_key == "nodejs_python":
            # Special handling for Node.js/Python combination
            result = self._detect_nodejs_python_special(result)
        
        elif runtime_key == "anaconda3":
            # Special handling for Anaconda3
            result = self._detect_anaconda3_special(result)
        
        return result
    
    def _detect_vcpp_redistributables_special(self, result: RuntimeDetectionResult) -> RuntimeDetectionResult:
        """Special detection logic for Visual C++ Redistributables."""
        if not winreg or platform.system() != "Windows":
            return result
        
        try:
            # Check for various versions of VC++ Redistributables
            vcpp_versions = []
            
            # Common registry paths for VC++ Redistributables
            registry_paths = [
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x86"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\VisualStudio\14.0\VC\Runtimes\x64"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\VisualStudio\14.0\VC\Runtimes\x86"),
            ]
            
            for hkey, key_path in registry_paths:
                try:
                    with winreg.OpenKey(hkey, key_path) as key:
                        try:
                            version, _ = winreg.QueryValueEx(key, "Version")
                            installed, _ = winreg.QueryValueEx(key, "Installed")
                            
                            if installed and version:
                                vcpp_versions.append(version)
                                
                        except WindowsError:
                            continue
                            
                except WindowsError:
                    continue
            
            if vcpp_versions:
                result.detected = True
                result.version = max(vcpp_versions)  # Use highest version found
                result.detection_method = DetectionMethod.REGISTRY
                result.confidence = 0.9
                result.metadata["all_versions"] = vcpp_versions
                
        except Exception as e:
            result.errors.append(f"VC++ Redistributables special detection error: {str(e)}")
        
        return result
    
    def _detect_dotnet_desktop_special(self, result: RuntimeDetectionResult) -> RuntimeDetectionResult:
        """Special detection logic for .NET Desktop Runtime (supports 8.0 and 9.0)."""
        try:
            # Try to get list of installed runtimes
            process_result = subprocess.run(
                ["dotnet", "--list-runtimes"],
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
            )
            
            if process_result.returncode == 0:
                output = process_result.stdout
                
                # Look for Microsoft.WindowsDesktop.App runtimes
                desktop_runtimes = []
                for line in output.split('\n'):
                    if 'Microsoft.WindowsDesktop.App' in line:
                        # Extract version
                        match = re.search(r'Microsoft\.WindowsDesktop\.App (\d+\.\d+\.\d+)', line)
                        if match:
                            version = match.group(1)
                            desktop_runtimes.append(version)
                
                if desktop_runtimes:
                    result.detected = True
                    result.version = max(desktop_runtimes)  # Use highest version
                    result.detection_method = DetectionMethod.PATH_BASED
                    result.confidence = 0.95
                    result.metadata["all_desktop_runtimes"] = desktop_runtimes
                    
                    # Check if we have 8.0 or 9.0
                    has_8_0 = any(v.startswith("8.") for v in desktop_runtimes)
                    has_9_0 = any(v.startswith("9.") for v in desktop_runtimes)
                    result.metadata["has_8_0"] = has_8_0
                    result.metadata["has_9_0"] = has_9_0
                    
        except Exception as e:
            result.errors.append(f".NET Desktop Runtime special detection error: {str(e)}")
        
        return result
    
    def _detect_nodejs_python_special(self, result: RuntimeDetectionResult) -> RuntimeDetectionResult:
        """Special detection logic for Node.js/Python combination."""
        try:
            # Detect Node.js
            node_detected = False
            node_version = None
            
            try:
                node_result = subprocess.run(
                    ["node", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
                )
                
                if node_result.returncode == 0:
                    node_output = node_result.stdout.strip()
                    match = re.search(r'v(\d+\.\d+\.\d+)', node_output)
                    if match:
                        node_detected = True
                        node_version = match.group(1)
                        
            except Exception:
                pass
            
            # Detect Python
            python_detected = False
            python_version = None
            
            try:
                python_result = subprocess.run(
                    ["python", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
                )
                
                if python_result.returncode == 0:
                    python_output = python_result.stdout.strip()
                    match = re.search(r'Python (\d+\.\d+\.\d+)', python_output)
                    if match:
                        python_detected = True
                        python_version = match.group(1)
                        
            except Exception:
                pass
            
            # Update result based on detections
            if node_detected or python_detected:
                result.detected = True
                result.detection_method = DetectionMethod.PATH_BASED
                result.confidence = 0.8
                
                if node_detected and python_detected:
                    result.version = f"Node.js {node_version}, Python {python_version}"
                    result.confidence = 0.9
                elif node_detected:
                    result.version = f"Node.js {node_version}"
                else:
                    result.version = f"Python {python_version}"
                
                result.metadata["node_detected"] = node_detected
                result.metadata["node_version"] = node_version
                result.metadata["python_detected"] = python_detected
                result.metadata["python_version"] = python_version
                
        except Exception as e:
            result.errors.append(f"Node.js/Python special detection error: {str(e)}")
        
        return result
    
    def _detect_anaconda3_special(self, result: RuntimeDetectionResult) -> RuntimeDetectionResult:
        """Special detection logic for Anaconda3."""
        try:
            # Try conda command first
            conda_detected = False
            conda_version = None
            
            try:
                conda_result = subprocess.run(
                    ["conda", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                    creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
                )
                
                if conda_result.returncode == 0:
                    conda_output = conda_result.stdout.strip()
                    match = re.search(r'conda (\d+\.\d+\.\d+)', conda_output)
                    if match:
                        conda_detected = True
                        conda_version = match.group(1)
                        
            except Exception:
                pass
            
            # Try to get Python version from conda environment
            python_version = None
            if conda_detected:
                try:
                    python_result = subprocess.run(
                        ["python", "--version"],
                        capture_output=True,
                        text=True,
                        timeout=10,
                        creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
                    )
                    
                    if python_result.returncode == 0:
                        python_output = python_result.stdout.strip()
                        match = re.search(r'Python (\d+\.\d+\.\d+)', python_output)
                        if match:
                            python_version = match.group(1)
                            
                except Exception:
                    pass
            
            if conda_detected:
                result.detected = True
                result.version = conda_version
                result.detection_method = DetectionMethod.PATH_BASED
                result.confidence = 0.9
                result.metadata["conda_version"] = conda_version
                result.metadata["python_version"] = python_version
                
                # Check for conda environment variables
                conda_prefix = os.getenv("CONDA_PREFIX")
                conda_default_env = os.getenv("CONDA_DEFAULT_ENV")
                
                if conda_prefix:
                    result.environment_variables["CONDA_PREFIX"] = conda_prefix
                if conda_default_env:
                    result.environment_variables["CONDA_DEFAULT_ENV"] = conda_default_env
                    
        except Exception as e:
            result.errors.append(f"Anaconda3 special detection error: {str(e)}")
        
        return result
    
    def _find_executable_path(self, executable_name: str) -> Optional[str]:
        """Find the full path of an executable."""
        try:
            if platform.system() == "Windows":
                result = subprocess.run(
                    ["where", executable_name],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
            else:
                result = subprocess.run(
                    ["which", executable_name],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
            
            if result.returncode == 0:
                return result.stdout.strip().split('\n')[0]
                
        except Exception:
            pass
        
        return None
    
    def _get_registry_version(self, key) -> Optional[str]:
        """Get version from registry key."""
        version_names = ["Version", "DisplayVersion", "CurrentVersion"]
        
        for version_name in version_names:
            try:
                version, _ = winreg.QueryValueEx(key, version_name)
                if version:
                    return str(version)
            except WindowsError:
                continue
        
        return None
    
    def _get_registry_install_path(self, key) -> Optional[str]:
        """Get install path from registry key."""
        path_names = ["InstallLocation", "InstallPath", "Path", "JavaHome"]
        
        for path_name in path_names:
            try:
                path, _ = winreg.QueryValueEx(key, path_name)
                if path and os.path.exists(path):
                    return str(path)
            except WindowsError:
                continue
        
        return None
    
    def _get_executable_version(self, executable_path: str, config: Dict[str, Any]) -> Optional[str]:
        """Get version from executable file."""
        try:
            version_command = config.get("version_command")
            if not version_command:
                return None
            
            # Replace first element with full path
            command = [executable_path] + version_command[1:]
            
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
            )
            
            if result.returncode == 0:
                output = result.stdout + result.stderr
                version_regex = config.get("version_regex")
                if version_regex:
                    match = re.search(version_regex, output)
                    if match:
                        return match.group(1)
                        
        except Exception:
            pass
        
        return None
    
    # Individual runtime detection methods (as required by the interface)
    
    def detect_git_2_47_1(self) -> RuntimeDetectionResult:
        """Detect Git 2.47.1."""
        return self._detect_single_runtime("git", self._runtime_configs["git"])
    
    def detect_dotnet_sdk_8_0(self) -> RuntimeDetectionResult:
        """Detect .NET SDK 8.0."""
        return self._detect_single_runtime("dotnet_sdk", self._runtime_configs["dotnet_sdk"])
    
    def detect_java_jdk_21(self) -> RuntimeDetectionResult:
        """Detect Java JDK 21."""
        return self._detect_single_runtime("java_jdk", self._runtime_configs["java_jdk"])
    
    def detect_vcpp_redistributables(self) -> RuntimeDetectionResult:
        """Detect Visual C++ Redistributables."""
        return self._detect_single_runtime("vcpp_redistributables", self._runtime_configs["vcpp_redistributables"])
    
    def detect_anaconda3(self) -> RuntimeDetectionResult:
        """Detect Anaconda3."""
        return self._detect_single_runtime("anaconda3", self._runtime_configs["anaconda3"])
    
    def detect_dotnet_desktop_runtime(self) -> RuntimeDetectionResult:
        """Detect .NET Desktop Runtime 8.0/9.0."""
        return self._detect_single_runtime("dotnet_desktop_runtime", self._runtime_configs["dotnet_desktop_runtime"])
    
    def detect_powershell_7(self) -> RuntimeDetectionResult:
        """Detect PowerShell 7."""
        return self._detect_single_runtime("powershell", self._runtime_configs["powershell"])
    
    def detect_updated_nodejs_python(self) -> RuntimeDetectionResult:
        """Detect updated Node.js/Python."""
        return self._detect_single_runtime("nodejs_python", self._runtime_configs["nodejs_python"])