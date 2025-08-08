#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Detection Engine - Multi-method Application Detection System
Provides comprehensive application detection using multiple strategies.
"""

import os
import sys
import json
import logging
import platform
import subprocess
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Set, Tuple, Union
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import re

# Importação condicional do winreg para Windows
try:
    import winreg
except ImportError:
    winreg = None

from .detection_base import DetectionStrategy, DetectedApplication, DetectionMethod, ApplicationStatus
from .detection_cache import get_detection_cache
from .microsoft_store_detection import MicrosoftStoreDetectionStrategy
from .yaml_component_detection import YAMLComponentDetectionStrategy
from .intelligent_update_checker import get_intelligent_update_checker, UpdateRecommendation


# Classes base movidas para detection_base.py


@dataclass
class DetectionResult:
    """Result of application detection process."""
    applications: List[DetectedApplication] = field(default_factory=list)
    detection_summary: Dict[str, int] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    total_detected: int = 0
    detection_time_seconds: float = 0.0


# DetectionStrategy movida para detection_base.py


class RegistryDetectionStrategy(DetectionStrategy):
    """Windows Registry-based application detection."""
    
    def __init__(self):
        super().__init__()
        self.registry_paths = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall")
        ]
    
    def detect_applications(self, target_apps: Optional[List[str]] = None) -> List[DetectedApplication]:
        """Detect applications via Windows Registry."""
        detected = []
        
        for hkey, subkey_path in self.registry_paths:
            try:
                with winreg.OpenKey(hkey, subkey_path) as key:
                    i = 0
                    while True:
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            app_info = self._get_application_info(hkey, f"{subkey_path}\\{subkey_name}")
                            
                            if app_info and self._is_target_application(app_info, target_apps):
                                detected.append(app_info)
                            
                            i += 1
                        except WindowsError:
                            break
            except Exception as e:
                self.logger.error(f"Registry detection error for {subkey_path}: {e}")
        
        return detected
    
    def _get_application_info(self, hkey: int, subkey_path: str) -> Optional[DetectedApplication]:
        """Extract application information from registry key."""
        try:
            with winreg.OpenKey(hkey, subkey_path) as key:
                app_name = self._get_registry_value(key, "DisplayName")
                if not app_name:
                    return None
                
                version = self._get_registry_value(key, "DisplayVersion", "")
                install_path = self._get_registry_value(key, "InstallLocation", "")
                
                return DetectedApplication(
                    name=app_name,
                    version=version,
                    install_path=install_path,
                    detection_method=DetectionMethod.REGISTRY,
                    status=ApplicationStatus.INSTALLED,
                    confidence=0.9
                )
        except Exception as e:
            self.logger.debug(f"Failed to read registry key {subkey_path}: {e}")
            return None
    
    def _get_registry_value(self, key, value_name: str, default: str = None) -> Optional[str]:
        """Get value from registry key."""
        try:
            value, _ = winreg.QueryValueEx(key, value_name)
            return str(value) if value else default
        except WindowsError:
            return default
    
    def _is_target_application(self, app: DetectedApplication, target_apps: Optional[List[str]]) -> bool:
        """Check if application matches target criteria."""
        if not target_apps:
            return True
        
        app_name_lower = app.name.lower()
        return any(target.lower() in app_name_lower for target in target_apps)
    
    def get_method_name(self) -> DetectionMethod:
        return DetectionMethod.REGISTRY


class ExecutableScanStrategy(DetectionStrategy):
    """Executable scanning-based detection for portable applications."""
    
    def __init__(self):
        super().__init__()
        self.scan_paths = [
            Path("C:\\Program Files"),
            Path("C:\\Program Files (x86)"),
            Path.home() / "AppData" / "Local",
            Path.home() / "AppData" / "Roaming",
            Path("C:\\Tools"),
            Path("C:\\Portable")
        ]
        
        # Common executable patterns for known applications
        self.executable_patterns = {
            "git": ["git.exe"],
            "python": ["python.exe", "python3.exe"],
            "node": ["node.exe"],
            "java": ["java.exe", "javac.exe"],
            "dotnet": ["dotnet.exe"],
            "code": ["Code.exe"],
            "chrome": ["chrome.exe"],
            "firefox": ["firefox.exe"]
        }
    
    def detect_applications(self, target_apps: Optional[List[str]] = None) -> List[DetectedApplication]:
        """Detect applications by scanning for executables."""
        detected = []
        
        for scan_path in self.scan_paths:
            if scan_path.exists():
                detected.extend(self._scan_directory(scan_path, target_apps))
        
        return detected
    
    def _scan_directory(self, directory: Path, target_apps: Optional[List[str]]) -> List[DetectedApplication]:
        """Scan directory for application executables."""
        detected = []
        
        try:
            for pattern_name, executables in self.executable_patterns.items():
                if target_apps and pattern_name not in [app.lower() for app in target_apps]:
                    continue
                
                for executable in executables:
                    for exe_path in directory.rglob(executable):
                        if exe_path.is_file():
                            app_info = self._create_application_info(exe_path, pattern_name)
                            if app_info:
                                detected.append(app_info)
                                break  # Found one instance, move to next pattern
        except Exception as e:
            self.logger.error(f"Error scanning directory {directory}: {e}")
        
        return detected
    
    def _create_application_info(self, exe_path: Path, app_name: str) -> Optional[DetectedApplication]:
        """Create application info from executable path."""
        try:
            version = self._get_executable_version(exe_path)
            
            return DetectedApplication(
                name=app_name,
                version=version,
                install_path=str(exe_path.parent),
                executable_path=str(exe_path),
                detection_method=DetectionMethod.EXECUTABLE_SCAN,
                status=ApplicationStatus.INSTALLED,
                confidence=0.7
            )
        except Exception as e:
            self.logger.debug(f"Failed to create app info for {exe_path}: {e}")
            return None
    
    def _get_executable_version(self, exe_path: Path) -> str:
        """Get version information from executable."""
        try:
            # Try to get version using subprocess
            result = subprocess.run(
                [str(exe_path), "--version"],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            if result.returncode == 0:
                version_text = result.stdout.strip()
                # Extract version number using regex
                version_match = re.search(r'(\d+\.\d+(?:\.\d+)*)', version_text)
                if version_match:
                    return version_match.group(1)
        except Exception:
            pass
        
        return "unknown"
    
    def get_method_name(self) -> DetectionMethod:
        return DetectionMethod.EXECUTABLE_SCAN


class PathBasedDetectionStrategy(DetectionStrategy):
    """PATH environment variable-based detection."""
    
    def detect_applications(self, target_apps: Optional[List[str]] = None) -> List[DetectedApplication]:
        """Detect applications available in PATH."""
        detected = []
        
        # Common command-line tools to check
        tools_to_check = [
            "git", "python", "python3", "node", "npm", "java", "javac",
            "dotnet", "powershell", "pwsh", "code", "docker"
        ]
        
        if target_apps:
            tools_to_check = [tool for tool in tools_to_check if tool in target_apps]
        
        for tool in tools_to_check:
            app_info = self._check_tool_in_path(tool)
            if app_info:
                detected.append(app_info)
        
        return detected
    
    def _check_tool_in_path(self, tool_name: str) -> Optional[DetectedApplication]:
        """Check if tool is available in PATH."""
        try:
            # Use 'where' command on Windows
            result = subprocess.run(
                ["where", tool_name],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0
            )
            
            if result.returncode == 0:
                exe_path = result.stdout.strip().split('\n')[0]  # Get first result
                version = self._get_tool_version(tool_name)
                
                return DetectedApplication(
                    name=tool_name,
                    version=version,
                    executable_path=exe_path,
                    install_path=str(Path(exe_path).parent),
                    detection_method=DetectionMethod.PATH_BASED,
                    status=ApplicationStatus.INSTALLED,
                    confidence=0.8
                )
        except Exception as e:
            self.logger.debug(f"PATH check failed for {tool_name}: {e}")
        
        return None
    
    def _get_tool_version(self, tool_name: str) -> str:
        """Get version of tool using common version commands."""
        version_commands = [
            [tool_name, "--version"],
            [tool_name, "-version"],
            [tool_name, "-V"]
        ]
        
        for cmd in version_commands:
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=5,
                    creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                
                if result.returncode == 0:
                    version_text = result.stdout.strip()
                    # Extract version number
                    version_match = re.search(r'(\d+\.\d+(?:\.\d+)*)', version_text)
                    if version_match:
                        return version_match.group(1)
            except Exception:
                continue
        
        return "unknown"
    
    def get_method_name(self) -> DetectionMethod:
        return DetectionMethod.PATH_BASED


class CustomApplicationDetectionStrategy(DetectionStrategy):
    """Custom detection strategy for specific applications with known paths."""
    
    def __init__(self):
        super().__init__()
        # Configurações dos aplicativos customizados
        self.custom_applications = {
            "trae": {
                "name": "Trae",
                "description": "Trae AI-powered IDE",
                "publisher": "Trae",
                "paths": [
                    r"C:\Users\{username}\AppData\Local\Programs\Trae\Trae.exe",
                    r"C:\Program Files\Trae\Trae.exe",
                    r"C:\Program Files (x86)\Trae\Trae.exe",
                    r"C:\Users\{username}\AppData\Roaming\Trae\Trae.exe"
                ],
                "version_command": ["--version"],
                "registry_keys": [
                    r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Trae",
                    r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Trae"
                ]
            },
            "vscode_insiders": {
                "name": "Visual Studio Code Insiders",
                "description": "Microsoft Visual Studio Code Insiders",
                "publisher": "Microsoft Corporation",
                "paths": [
                    r"C:\Users\{username}\AppData\Local\Programs\Microsoft VS Code Insiders\Code - Insiders.exe",
                    r"C:\Program Files\Microsoft VS Code Insiders\Code - Insiders.exe",
                    r"C:\Program Files (x86)\Microsoft VS Code Insiders\Code - Insiders.exe",
                    r"C:\Users\{username}\AppData\Local\Programs\Microsoft VS Code Insiders\bin\code-insiders.cmd"
                ],
                "version_command": ["--version"],
                "registry_keys": [
                    r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{1287CAD5-7C8D-410D-9DAD-2D2D8E64F0B2}_is1",
                    r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\{1287CAD5-7C8D-410D-9DAD-2D2D8E64F0B2}_is1",
                    r"SOFTWARE\Classes\Applications\Code - Insiders.exe"
                ]
            },
            "revo_uninstaller": {
                "name": "Revo Uninstaller",
                "description": "VS Revo Group Revo Uninstaller",
                "publisher": "VS Revo Group",
                "paths": [
                    r"C:\Program Files\VS Revo Group\Revo Uninstaller\RevoUnin.exe",
                    r"C:\Program Files (x86)\VS Revo Group\Revo Uninstaller\RevoUnin.exe",
                    r"C:\Users\{username}\AppData\Local\Programs\VS Revo Group\Revo Uninstaller\RevoUnin.exe"
                ],
                "version_command": None,  # Não tem comando de versão confiável
                "registry_keys": [
                    r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Revo Uninstaller",
                    r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Revo Uninstaller",
                    r"SOFTWARE\VS Revo Group\Revo Uninstaller"
                ]
            },
            "git_bash": {
                "name": "Git Bash",
                "description": "Git for Windows - Bash",
                "publisher": "Git for Windows Project",
                "paths": [
                    r"C:\Program Files\Git\git-bash.exe",
                    r"C:\Program Files (x86)\Git\git-bash.exe",
                    r"C:\Users\{username}\AppData\Local\Programs\Git\git-bash.exe",
                    r"C:\Program Files\Git\bin\bash.exe"
                ],
                "version_command": ["-c", "git --version"],
                "registry_keys": [
                    r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Git_is1",
                    r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Git_is1",
                    r"SOFTWARE\GitForWindows"
                ],
                "additional_args": ["--cd-to-home"]
            },
            "winscript": {
                "name": "WinScript",
                "description": "Ferramenta open-source para personalização do Windows",
                "publisher": "WinScript Project",
                "paths": [
                    r"C:\Program Files\WinScript\WinScript.exe",
                    r"C:\Program Files (x86)\WinScript\WinScript.exe",
                    r"C:\Users\{username}\AppData\Local\Programs\WinScript\WinScript.exe",
                    r"C:\Users\{username}\winscript\WinScript.exe",
                    r"C:\Users\{username}\AppData\Roaming\WinScript\WinScript.exe",
                    r"C:\Tools\WinScript\WinScript.exe",
                    r"C:\WinScript\WinScript.exe"
                ],
                "version_command": ["--version"],
                "registry_keys": [
                    r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\WinScript",
                    r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\WinScript",
                    r"SOFTWARE\WinScript"
                ],
                "fallback_detection": {
                    "powershell_script": r"C:\Users\{username}\winscript\winscript.ps1",
                    "directory_check": r"C:\Users\{username}\winscript"
                }
            },
            "python": {
                "name": "Python",
                "description": "Python Programming Language",
                "publisher": "Python Software Foundation",
                "paths": [
                    r"C:\Program Files\Python313\python.exe",
                    r"C:\Program Files\Python312\python.exe",
                    r"C:\Program Files\Python311\python.exe",
                    r"C:\Program Files\Python310\python.exe",
                    r"C:\Program Files (x86)\Python313\python.exe",
                    r"C:\Program Files (x86)\Python312\python.exe",
                    r"C:\Program Files (x86)\Python311\python.exe",
                    r"C:\Program Files (x86)\Python310\python.exe",
                    r"C:\Users\{username}\AppData\Local\Programs\Python\Python313\python.exe",
                    r"C:\Users\{username}\AppData\Local\Programs\Python\Python312\python.exe",
                    r"C:\Users\{username}\AppData\Local\Programs\Python\Python311\python.exe",
                    r"C:\Users\{username}\AppData\Local\Programs\Python\Python310\python.exe",
                    r"C:\Python313\python.exe",
                    r"C:\Python312\python.exe",
                    r"C:\Python311\python.exe",
                    r"C:\Python310\python.exe"
                ],
                "version_command": ["--version"],
                "registry_keys": [
                    r"SOFTWARE\Python\PythonCore\3.13",
                    r"SOFTWARE\Python\PythonCore\3.12",
                    r"SOFTWARE\Python\PythonCore\3.11",
                    r"SOFTWARE\Python\PythonCore\3.10",
                    r"SOFTWARE\WOW6432Node\Python\PythonCore\3.13",
                    r"SOFTWARE\WOW6432Node\Python\PythonCore\3.12",
                    r"SOFTWARE\WOW6432Node\Python\PythonCore\3.11",
                    r"SOFTWARE\WOW6432Node\Python\PythonCore\3.10"
                ],
                "version_logic": "intelligent_versioning",
                "supported_versions": ["3.10", "3.11", "3.12", "3.13"]
            },
            "powershell": {
                "name": "PowerShell",
                "description": "PowerShell Core",
                "publisher": "Microsoft Corporation",
                "paths": [
                    r"C:\Program Files\PowerShell\7\pwsh.exe",
                    r"C:\Program Files\PowerShell\7-preview\pwsh.exe",
                    r"C:\Program Files (x86)\PowerShell\7\pwsh.exe",
                    r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe",
                    r"C:\Windows\SysWOW64\WindowsPowerShell\v1.0\powershell.exe",
                    r"C:\Users\{username}\AppData\Local\Microsoft\powershell\pwsh.exe"
                ],
                "version_command": ["-Command", "$PSVersionTable.PSVersion.ToString()"],
                "registry_keys": [
                    r"SOFTWARE\Microsoft\PowerShell\7",
                    r"SOFTWARE\Microsoft\PowerShell\1",
                    r"SOFTWARE\WOW6432Node\Microsoft\PowerShell\7",
                    r"SOFTWARE\WOW6432Node\Microsoft\PowerShell\1"
                ],
                "fallback_detection": {
                    "environment_var": "PSModulePath",
                    "command_check": "pwsh"
                }
            }
        }
    
    def detect_applications(self, target_apps: Optional[List[str]] = None) -> List[DetectedApplication]:
        """Detect custom applications with robust validation."""
        detected = []
        
        apps_to_check = self.custom_applications.keys()
        if target_apps:
            # Filtrar apenas aplicações solicitadas
            target_lower = [app.lower() for app in target_apps]
            apps_to_check = [
                key for key in self.custom_applications.keys()
                if any(target in key.lower() or key.lower() in target for target in target_lower)
            ]
        
        for app_key in apps_to_check:
            app_config = self.custom_applications[app_key]
            detected_app = self._detect_custom_application(app_key, app_config)
            if detected_app:
                detected.append(detected_app)
                self.logger.info(f"✅ Detected {app_config['name']} at {detected_app.executable_path}")
            else:
                self.logger.debug(f"❌ {app_config['name']} not found in expected paths")
        
        return detected
    
    def _detect_custom_application(self, app_key: str, app_config: Dict[str, Any]) -> Optional[DetectedApplication]:
        """Detect a specific custom application with robust validation."""
        username = os.getenv('USERNAME', 'User')
        
        # Primeiro, tentar detecção via arquivos executáveis
        for path_template in app_config["paths"]:
            # Substituir placeholder do username
            exe_path = path_template.replace('{username}', username)
            path_obj = Path(exe_path)
            
            # Verificar se o arquivo existe
            if not path_obj.exists():
                self.logger.debug(f"Path not found: {exe_path}")
                continue
            
            # Verificar se é um arquivo executável
            if not path_obj.is_file():
                self.logger.debug(f"Path is not a file: {exe_path}")
                continue
            
            # Verificar se tem extensão .exe (no Windows)
            if not exe_path.lower().endswith('.exe'):
                self.logger.debug(f"Path is not an executable: {exe_path}")
                continue
            
            # Tentar obter versão se suportado
            version = self._get_application_version(exe_path, app_config.get("version_command"))
            
            # Validar se o executável é funcional
            is_functional = self._validate_executable_functionality(exe_path, app_config)
            
            if is_functional:
                detected_app = DetectedApplication(
                    name=app_config["name"],
                    version=version,
                    install_path=str(path_obj.parent),
                    executable_path=exe_path,
                    detection_method=DetectionMethod.MANUAL_OVERRIDE,
                    status=ApplicationStatus.INSTALLED,
                    confidence=0.95,  # Alta confiança para detecção customizada
                    metadata={
                        "description": app_config.get("description", ""),
                        "custom_detection": True,
                        "app_key": app_key,
                        "additional_args": app_config.get("additional_args", [])
                    }
                )
                
                # Aplicar lógica de versionamento inteligente para Python
                if app_key == "python" and app_config.get("version_logic") == "intelligent_versioning":
                    detected_app = self._apply_intelligent_versioning(detected_app, app_config)
                
                return detected_app
        
        # Se não encontrou via arquivo, tentar via registro do Windows
        if platform.system() == "Windows" and 'registry_keys' in app_config:
            registry_result = self._detect_via_registry(app_key, app_config)
            if registry_result:
                return registry_result
        
        # Detecção especial para WinScript via PowerShell script
        if app_key == "winscript":
            winscript_result = self._detect_winscript_fallback(app_key, app_config)
            if winscript_result:
                return winscript_result
        
        # Detecção especial para PowerShell via variáveis de ambiente
        if app_key == "powershell":
            powershell_result = self._detect_powershell_fallback(app_key, app_config)
            if powershell_result:
                return powershell_result
        
        return None
    
    def _detect_winscript_fallback(self, app_key: str, app_config: Dict[str, Any]) -> Optional[DetectedApplication]:
        """Detecção especial para WinScript via PowerShell script ou diretório."""
        try:
            username = os.getenv('USERNAME', 'User')
            fallback_config = app_config.get("fallback_detection", {})
            
            # Verificar se existe o script PowerShell
            ps_script_path = fallback_config.get("powershell_script", "").replace('{username}', username)
            if ps_script_path and os.path.exists(ps_script_path):
                # Verificar se existe o diretório
                dir_path = fallback_config.get("directory_check", "").replace('{username}', username)
                if dir_path and os.path.exists(dir_path):
                    return DetectedApplication(
                        name=app_config["name"],
                        version="Unknown",
                        install_path=dir_path,
                        executable_path=ps_script_path,
                        detection_method=DetectionMethod.MANUAL_OVERRIDE,
                        status=ApplicationStatus.INSTALLED,
                        confidence=0.85,
                        metadata={
                            "description": app_config.get("description", ""),
                            "custom_detection": True,
                            "app_key": app_key,
                            "detection_type": "powershell_script"
                        }
                    )
            return None
        except Exception as e:
            self.logger.error(f"Erro na detecção fallback do WinScript: {e}")
            return None
    
    def _detect_powershell_fallback(self, app_key: str, app_config: Dict[str, Any]) -> Optional[DetectedApplication]:
        """Detecção especial para PowerShell via variáveis de ambiente."""
        try:
            fallback_config = app_config.get("fallback_detection", {})
            
            # Verificar variável de ambiente PSModulePath
            ps_module_path = os.getenv(fallback_config.get("environment_var", ""))
            if ps_module_path:
                # Tentar executar comando pwsh para verificar se está disponível
                try:
                    import subprocess
                    result = subprocess.run(["pwsh", "-Command", "$PSVersionTable.PSVersion.ToString()"], 
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        version = result.stdout.strip()
                        # Encontrar o executável pwsh
                        pwsh_path = None
                        for path in app_config["paths"]:
                            if os.path.exists(path):
                                pwsh_path = path
                                break
                        
                        if not pwsh_path:
                            # Usar o comando which/where para encontrar pwsh
                            try:
                                which_result = subprocess.run(["where", "pwsh"], capture_output=True, text=True)
                                if which_result.returncode == 0:
                                    pwsh_path = which_result.stdout.strip().split('\n')[0]
                            except:
                                pwsh_path = "pwsh"  # Fallback para comando no PATH
                        
                        return DetectedApplication(
                            name=app_config["name"],
                            version=version,
                            install_path=os.path.dirname(pwsh_path) if pwsh_path != "pwsh" else "System PATH",
                            executable_path=pwsh_path,
                            detection_method=DetectionMethod.MANUAL_OVERRIDE,
                            status=ApplicationStatus.INSTALLED,
                            confidence=0.90,
                            metadata={
                                "description": app_config.get("description", ""),
                                "custom_detection": True,
                                "app_key": app_key,
                                "detection_type": "environment_variable"
                            }
                        )
                except subprocess.TimeoutExpired:
                    pass
                except Exception:
                    pass
            
            return None
        except Exception as e:
            self.logger.error(f"Erro na detecção fallback do PowerShell: {e}")
            return None
    
    def _apply_intelligent_versioning(self, detected_app: DetectedApplication, app_config: Dict[str, Any]) -> DetectedApplication:
        """Aplica lógica de versionamento inteligente para Python."""
        try:
            if not detected_app.version:
                return detected_app
            
            # Extrair versão principal (ex: "3.12" de "Python 3.12.0")
            import re
            version_match = re.search(r'(\d+\.\d+)', detected_app.version)
            if not version_match:
                return detected_app
            
            detected_version = version_match.group(1)
            supported_versions = app_config.get("supported_versions", [])
            
            # Encontrar todas as versões menores ou iguais à detectada
            compatible_versions = []
            for version in supported_versions:
                try:
                    if float(version) <= float(detected_version):
                        compatible_versions.append(version)
                except ValueError:
                    continue
            
            if compatible_versions:
                # Adicionar informação sobre versões compatíveis nos metadados
                metadata = detected_app.metadata.copy()
                metadata.update({
                    "intelligent_versioning": True,
                    "detected_version": detected_version,
                    "compatible_versions": compatible_versions,
                    "version_note": f"Python {detected_version} é compatível com versões: {', '.join(compatible_versions)}"
                })
                
                # Criar nova instância com metadados atualizados
                return DetectedApplication(
                    name=detected_app.name,
                    version=detected_app.version,
                    install_path=detected_app.install_path,
                    executable_path=detected_app.executable_path,
                    detection_method=detected_app.detection_method,
                    status=detected_app.status,
                    confidence=detected_app.confidence,
                    metadata=metadata
                )
            
            return detected_app
        except Exception as e:
            self.logger.error(f"Erro na aplicação de versionamento inteligente: {e}")
            return detected_app
    
    def _detect_via_registry(self, app_key: str, app_config: Dict[str, Any]) -> Optional[DetectedApplication]:
         """Detect application via Windows Registry."""
         try:
             if not winreg:
                 return None
                 
             for registry_key in app_config.get('registry_keys', []):
                 try:
                     # Tentar HKEY_LOCAL_MACHINE primeiro
                     with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, registry_key) as key:
                         # Obter informações do registro
                         display_name = self._get_registry_value(key, 'DisplayName')
                         install_location = self._get_registry_value(key, 'InstallLocation')
                         display_version = self._get_registry_value(key, 'DisplayVersion')
                         publisher = self._get_registry_value(key, 'Publisher')
                         
                         if display_name and install_location:
                             # Tentar encontrar o executável na localização de instalação
                             exe_path = self._find_executable_in_location(install_location, app_config)
                             
                             if exe_path:
                                 return DetectedApplication(
                                     name=display_name or app_config['name'],
                                     version=display_version or 'unknown',
                                     path=exe_path,
                                     publisher=publisher or app_config.get('publisher', 'Unknown'),
                                     install_date=self._get_install_date(exe_path),
                                     size=self._get_application_size(exe_path),
                                     description=app_config.get('description', ''),
                                     detection_method=DetectionMethod.REGISTRY
                                 )
                 
                 except (FileNotFoundError, PermissionError, OSError):
                     continue
             
             return None
             
         except Exception as e:
             self.logger.debug(f"Registry detection failed for {app_key}: {e}")
             return None
    
    def _get_registry_value(self, key, value_name: str) -> Optional[str]:
         """Get a value from Windows Registry key."""
         try:
             if not winreg:
                 return None
             value, _ = winreg.QueryValueEx(key, value_name)
             return str(value) if value else None
         except (FileNotFoundError, OSError):
             return None
    
    def _find_executable_in_location(self, install_location: str, app_config: Dict[str, Any]) -> Optional[str]:
        """Find executable in installation location."""
        try:
            if not os.path.isdir(install_location):
                return None
            
            # Procurar por executáveis conhecidos
            for path_template in app_config['paths']:
                exe_name = os.path.basename(path_template)
                potential_path = os.path.join(install_location, exe_name)
                
                if os.path.isfile(potential_path):
                    return potential_path
            
            # Busca recursiva por executáveis
            for root, dirs, files in os.walk(install_location):
                for file in files:
                    if file.endswith('.exe'):
                        for path_template in app_config['paths']:
                            if file.lower() == os.path.basename(path_template).lower():
                                return os.path.join(root, file)
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Error finding executable in {install_location}: {e}")
            return None
    
    def _get_application_version(self, exe_path: str, version_command: Optional[List[str]]) -> str:
        """Get version information from application."""
        if not version_command:
            return self._get_file_version(exe_path)
        
        try:
            # Tentar comando de versão
            cmd = [exe_path] + version_command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            
            if result.returncode == 0:
                version_text = result.stdout.strip()
                # Extrair número da versão usando regex
                version_match = re.search(r'(\d+\.\d+(?:\.\d+)*(?:-[\w\.-]+)?)', version_text)
                if version_match:
                    return version_match.group(1)
                
                # Se não encontrou padrão, retornar primeira linha não vazia
                lines = [line.strip() for line in version_text.split('\n') if line.strip()]
                if lines:
                    return lines[0][:50]  # Limitar tamanho
        
        except Exception as e:
            self.logger.debug(f"Version command failed for {exe_path}: {e}")
        
        # Fallback para versão do arquivo
        return self._get_file_version(exe_path)
    
    def _get_file_version(self, exe_path: str) -> str:
        """Get file version from executable metadata (Windows)."""
        try:
            if platform.system() == "Windows":
                # Tentar usar win32api se disponível
                try:
                    import win32api
                    info = win32api.GetFileVersionInfo(exe_path, "\\")
                    ms = info['FileVersionMS']
                    ls = info['FileVersionLS']
                    version = f"{win32api.HIWORD(ms)}.{win32api.LOWORD(ms)}.{win32api.HIWORD(ls)}.{win32api.LOWORD(ls)}"
                    return version
                except ImportError:
                    self.logger.debug("pywin32 not available, using alternative method")
                    # Fallback para método alternativo usando PowerShell
                    return self._get_file_version_powershell(exe_path)
        except Exception as e:
            self.logger.debug(f"File version extraction failed for {exe_path}: {e}")
        
        return "unknown"
    
    def _get_file_version_powershell(self, exe_path: str) -> str:
        """Get file version using PowerShell as fallback."""
        try:
            ps_command = f"(Get-ItemProperty '{exe_path}').VersionInfo.FileVersion"
            result = subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True,
                text=True,
                timeout=10,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if result.returncode == 0 and result.stdout.strip():
                version = result.stdout.strip()
                # Limpar versão se necessário
                if version and version != "":
                    return version
        except Exception as e:
            self.logger.debug(f"PowerShell version extraction failed for {exe_path}: {e}")
        
        return "unknown"
    
    def _validate_executable_functionality(self, exe_path: str, app_config: Dict[str, Any]) -> bool:
        """Validate that the executable is functional."""
        try:
            path_obj = Path(exe_path)
            app_name = app_config.get('name', '').lower()
            
            # Verificações básicas
            if not path_obj.exists() or not path_obj.is_file():
                return False
            
            # Verificar tamanho do arquivo (deve ser > 0)
            if path_obj.stat().st_size == 0:
                self.logger.debug(f"Executable has zero size: {exe_path}")
                return False
            
            # Verificar se não é um link quebrado
            try:
                path_obj.resolve(strict=True)
            except (OSError, RuntimeError):
                self.logger.debug(f"Broken link or invalid path: {exe_path}")
                return False
            
            # Verificar se o arquivo é executável
            if not os.access(exe_path, os.X_OK):
                self.logger.debug(f"File is not executable: {exe_path}")
                return False
            
            # Validações específicas por aplicativo
            if 'git' in app_name and 'bash' in app_name:
                # Para Git Bash, verificar se consegue executar comando básico
                try:
                    result = subprocess.run(
                        [exe_path, '-c', 'echo test'],
                        capture_output=True,
                        text=True,
                        timeout=5,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                    return result.returncode == 0 and 'test' in result.stdout
                except:
                    # Se falhar, verificar se git.exe existe no mesmo diretório
                    git_exe = path_obj.parent / "bin" / "git.exe"
                    if not git_exe.exists():
                        git_exe = path_obj.parent / "git.exe"
                    return git_exe.exists()
            
            elif 'code' in app_name or 'vscode' in app_name:
                # Para VS Code, verificar se consegue mostrar versão sem opening GUI
                try:
                    result = subprocess.run(
                        [exe_path, '--version', '--disable-extensions', '--disable-gpu'],
                        capture_output=True,
                        text=True,
                        timeout=10,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                    return result.returncode == 0 and result.stdout.strip()
                except:
                    # Fallback: verificar estrutura de diretórios
                    resources_dir = path_obj.parent / "resources"
                    return resources_dir.exists() and resources_dir.is_dir()
            
            elif 'revo' in app_name:
                # Para Revo Uninstaller, verificar se consegue mostrar ajuda
                try:
                    result = subprocess.run(
                        [exe_path, '/?'],
                        capture_output=True,
                        text=True,
                        timeout=5,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                    # Revo pode retornar código diferente de 0 mesmo funcionando
                    return True
                except:
                    # Fallback: verificar arquivos de configuração
                    config_files = [
                        path_obj.parent / "RevoUnin.ini",
                        path_obj.parent / "RevoUninPro.exe"
                    ]
                    return any(f.exists() for f in config_files) or True
            
            elif 'trae' in app_name:
                # Para Trae, tentar verificar versão ou apenas aceitar se existe
                try:
                    result = subprocess.run(
                        [exe_path, '--version'],
                        capture_output=True,
                        text=True,
                        timeout=5,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                    return True  # Aceitar independente do resultado
                except:
                    return True  # Aceitar se executável existe
            
            else:
                # Validação genérica - arquivo existe e é executável
                return True
            
        except Exception as e:
            self.logger.debug(f"Functionality validation failed for {exe_path}: {e}")
            return False
    
    def get_method_name(self) -> DetectionMethod:
        return DetectionMethod.MANUAL_OVERRIDE


class DetectionEngine:
    """Main detection engine that coordinates multiple detection strategies."""
    
    def __init__(self, use_cache: bool = True, enable_updates: bool = True):
        self.logger = logging.getLogger("detection_engine")
        self.strategies = [
            RegistryDetectionStrategy(),
            ExecutableScanStrategy(),
            PathBasedDetectionStrategy(),
            MicrosoftStoreDetectionStrategy(),
            CustomApplicationDetectionStrategy(),  # Aplicações hardcoded
            YAMLComponentDetectionStrategy()  # Componentes YAML com verify_actions
        ]
        self.use_cache = use_cache
        self.enable_updates = enable_updates
        if self.use_cache:
            self.cache = get_detection_cache()
        else:
            self.cache = None
        
        self.update_checker = get_intelligent_update_checker() if enable_updates else None
        
        # Version comparison cache
        self._version_cache: Dict[str, str] = {}
        
        self.logger.info(f"DetectionEngine initialized with {len(self.strategies)} strategies")
        if enable_updates:
            self.logger.info("Update checking enabled")
    
    def detect_all_applications(self, target_apps: Optional[List[str]] = None) -> DetectionResult:
        """Run comprehensive application detection using all strategies with caching support."""
        start_time = time.time()
        
        result = DetectionResult()
        all_detected = []
        cache_hits = 0
        cache_misses = 0
        
        # Se target_apps não especificado, detectar todas as aplicações conhecidas
        apps_to_detect = target_apps or ["git", "python", "node", "java", "dotnet", "code", "docker", "kubectl"]
        
        # Verificar cache primeiro se habilitado
        if self.use_cache and self.cache:
            cached_apps = []
            uncached_apps = []
            
            for app_name in apps_to_detect:
                cached_result = self.cache.get_cached_result(app_name)
                if cached_result:
                    # Converter resultado do cache para DetectedApplication
                    if cached_result.get("installed", False):
                        detected_app = DetectedApplication(
                            name=app_name,
                            version=cached_result.get("version", ""),
                            install_path=cached_result.get("install_path", ""),
                            executable_path=cached_result.get("executable_path", ""),
                            detection_method=DetectionMethod(cached_result.get("detection_method", "registry")),
                            status=ApplicationStatus.INSTALLED,
                            confidence=cached_result.get("confidence", 1.0),
                            metadata=cached_result.get("metadata", {})
                        )
                        all_detected.append(detected_app)
                        cached_apps.append(app_name)
                        cache_hits += 1
                    else:
                        cache_hits += 1  # Cache hit para "não instalado"
                else:
                    uncached_apps.append(app_name)
                    cache_misses += 1
            
            self.logger.info(f"Cache: {cache_hits} hits, {cache_misses} misses")
            
            # Detectar apenas aplicações não encontradas no cache
            target_apps_for_detection = uncached_apps if uncached_apps else None
        else:
            target_apps_for_detection = target_apps
        
        # Executar detecção para aplicações não cacheadas
        if not self.use_cache or not self.cache or target_apps_for_detection:
            # Run each detection strategy
            for strategy in self.strategies:
                try:
                    self.logger.info(f"Running {strategy.get_method_name().value} detection...")
                    detected = strategy.detect_applications(target_apps_for_detection)
                    all_detected.extend(detected)
                    
                    result.detection_summary[strategy.get_method_name().value] = len(detected)
                    
                except Exception as e:
                    error_msg = f"Detection strategy {strategy.get_method_name().value} failed: {e}"
                    self.logger.error(error_msg)
                    result.errors.append(error_msg)
        
        # Merge and deduplicate results
        result.applications = self._merge_detections(all_detected)
        result.total_detected = len(result.applications)
        result.detection_time_seconds = time.time() - start_time
        
        # Armazenar resultados no cache se habilitado
        if self.use_cache and self.cache:
            self._cache_detection_results(result.applications, apps_to_detect)
        
        # Validate versions and dependencies
        self._validate_detected_applications(result)
        
        return result
    
    def _merge_detections(self, detections: List[DetectedApplication]) -> List[DetectedApplication]:
        """Merge and deduplicate detection results."""
        merged = {}
        
        # Special handling for Python to deduplicate entries
        python_detections = []
        other_detections = []
        
        for detection in detections:
            # Group Python-related detections
            if 'python' in detection.name.lower():
                python_detections.append(detection)
            else:
                other_detections.append(detection)
        
        # Process Python detections with smarter deduplication
        if python_detections:
            # Sort by confidence (highest first) and then by detection method priority
            method_priority = {
                DetectionMethod.REGISTRY: 5,
                DetectionMethod.MANUAL_OVERRIDE: 4,
                DetectionMethod.PATH_BASED: 3,
                DetectionMethod.EXECUTABLE_SCAN: 2,
                DetectionMethod.PACKAGE_MANAGER: 1
            }
            
            python_detections.sort(key=lambda x: (
                x.confidence,
                method_priority.get(x.detection_method, 0),
                x.version if x.version != "unknown" else ""
            ), reverse=True)
            
            # Keep the best Python detection
            best_python = python_detections[0]
            other_detections.append(best_python)
            
            # Log other Python detections that were filtered out
            for detection in python_detections[1:]:
                self.logger.debug(f"Filtered duplicate Python detection: {detection.name} v{detection.version} ({detection.detection_method.value})")
        
        # Process other detections with existing logic
        for detection in other_detections:
            key = detection.name.lower()
            
            if key not in merged:
                merged[key] = detection
            else:
                # Keep detection with higher confidence
                existing = merged[key]
                if detection.confidence > existing.confidence:
                    merged[key] = detection
                elif detection.confidence == existing.confidence:
                    # Prefer registry detection, then path-based, then executable scan
                    method_priority = {
                        DetectionMethod.REGISTRY: 3,
                        DetectionMethod.PATH_BASED: 2,
                        DetectionMethod.EXECUTABLE_SCAN: 1
                    }
                    
                    if method_priority.get(detection.detection_method, 0) > method_priority.get(existing.detection_method, 0):
                        merged[key] = detection
        
        return list(merged.values())
    
    def _cache_detection_results(self, detections: List[DetectedApplication], target_apps: List[str]) -> None:
        """Armazena resultados de detecção no cache."""
        if not self.cache:
            return
        
        # Criar conjunto de aplicações detectadas
        detected_names = {app.name.lower() for app in detections}
        
        # Cachear aplicações detectadas
        for app in detections:
            result_data = {
                "installed": True,
                "version": app.version,
                "install_path": app.install_path,
                "executable_path": app.executable_path,
                "detection_method": app.detection_method.value,
                "confidence": app.confidence,
                "metadata": app.metadata
            }
            
            # Determinar tipo de aplicação para TTL
            app_type = self._determine_app_type(app.name)
            
            self.cache.cache_result(
                app_name=app.name,
                result=result_data,
                app_type=app_type,
                detection_method=app.detection_method.value,
                confidence_level=app.confidence
            )
        
        # Cachear aplicações não encontradas
        for app_name in target_apps:
            if app_name.lower() not in detected_names:
                result_data = {
                    "installed": False,
                    "version": "",
                    "install_path": "",
                    "executable_path": "",
                    "detection_method": "comprehensive_scan",
                    "confidence": 1.0,
                    "metadata": {}
                }
                
                app_type = self._determine_app_type(app_name)
                
                self.cache.cache_result(
                    app_name=app_name,
                    result=result_data,
                    app_type=app_type,
                    detection_method="comprehensive_scan",
                    confidence_level=1.0
                )
    
    def _determine_app_type(self, app_name: str) -> str:
        """Determina o tipo de aplicação para configuração de TTL."""
        app_name_lower = app_name.lower()
        
        # Runtimes e linguagens
        if app_name_lower in ["python", "node", "java", "dotnet", "go", "rust", "php"]:
            return "runtime"
        
        # Ferramentas de desenvolvimento
        if app_name_lower in ["git", "docker", "kubectl", "code", "vim", "emacs"]:
            return "development_tool"
        
        # Ferramentas do sistema
        if app_name_lower in ["powershell", "cmd", "bash", "zsh"]:
            return "system_tool"
        
        return "application"
    
    def _validate_detected_applications(self, result: DetectionResult) -> None:
        """Validate detected applications and check for version compatibility."""
        # Filter out project components
        filtered_applications = []
        for app in result.applications:
            if not self._is_project_component(app):
                filtered_applications.append(app)
            else:
                self.logger.debug(f"Filtered out project component: {app.name}")
        
        # Update the applications list with filtered results
        result.applications = filtered_applications
        result.total_detected = len(filtered_applications)
        
        # Validate remaining applications
        for app in result.applications:
            try:
                # Validate executable exists and is accessible
                if app.executable_path and not Path(app.executable_path).exists():
                    app.status = ApplicationStatus.CORRUPTED
                    result.warnings.append(f"{app.name}: Executable not found at {app.executable_path}")
                
                # Check if version is outdated (would need version requirements)
                # This is a placeholder for version comparison logic
                if app.version == "unknown":
                    result.warnings.append(f"{app.name}: Version could not be determined")
                
            except Exception as e:
                self.logger.error(f"Validation failed for {app.name}: {e}")
                result.errors.append(f"Validation failed for {app.name}: {e}")
    
    def _is_project_component(self, app: DetectedApplication) -> bool:
        """Check if a detected application is part of the project rather than a user installation."""
        # Check if install path is within project directory
        if app.install_path:
            try:
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                install_path_abs = os.path.abspath(app.install_path)
                if install_path_abs.startswith(project_root):
                    return True
            except:
                pass
        
        # Check if executable path is within project directory
        if app.executable_path:
            try:
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                exe_path_abs = os.path.abspath(app.executable_path)
                if exe_path_abs.startswith(project_root):
                    return True
            except:
                pass
        
        return False
    
    def get_application_status(self, app_name: str) -> ApplicationStatus:
        """Get status of a specific application."""
        # Verificar cache primeiro se habilitado
        if self.use_cache and self.cache:
            cached_result = self.cache.get_cached_result(app_name)
            if cached_result:
                if cached_result.get("installed", False):
                    return ApplicationStatus.INSTALLED
                else:
                    return ApplicationStatus.NOT_INSTALLED
        
        # Se não encontrado no cache, executar detecção
        result = self.detect_all_applications([app_name])
        
        for app in result.applications:
            if app.name.lower() == app_name.lower():
                return app.status
        
        return ApplicationStatus.NOT_INSTALLED
    
    def generate_detection_report(self, result: DetectionResult) -> str:
        """Generate a human-readable detection report."""
        report = []
        report.append("=== Application Detection Report ===")
        report.append(f"Total applications detected: {result.total_detected}")
        report.append(f"Detection time: {result.detection_time_seconds:.2f} seconds")
        
        # Cache statistics if available
        if self.use_cache and self.cache:
            cache_stats = self.cache.get_cache_stats()
            report.append(f"Cache Hit Rate: {cache_stats['hit_rate_percent']:.1f}%")
        
        report.append("")
        
        # Summary by detection method
        report.append("Detection Summary:")
        for method, count in result.detection_summary.items():
            report.append(f"  {method}: {count} applications")
        report.append("")
        
        # Detected applications
        report.append("Detected Applications:")
        for app in sorted(result.applications, key=lambda x: x.name.lower()):
            status_icon = "✓" if app.status == ApplicationStatus.INSTALLED else "✗"
            report.append(f"  {status_icon} {app.name} v{app.version} ({app.detection_method.value})")
            if app.install_path:
                report.append(f"    Path: {app.install_path}")
        
        # Warnings and errors
        if result.warnings:
            report.append("")
            report.append("Warnings:")
            for warning in result.warnings:
                report.append(f"  ⚠ {warning}")
        
        if result.errors:
            report.append("")
            report.append("Errors:")
            for error in result.errors:
                report.append(f"  ❌ {error}")
        
        return "\n".join(report)
    
    def invalidate_cache(self, app_name: str) -> bool:
        """Invalida cache para uma aplicação específica."""
        if self.use_cache and self.cache:
            return self.cache.invalidate_cache(app_name)
        return False
    
    def clear_cache(self) -> None:
        """Limpa todo o cache de detecção."""
        if self.use_cache and self.cache:
            self.cache.clear_all_cache()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas do cache."""
        if self.use_cache and self.cache:
            return self.cache.get_cache_stats()
        return {}
    
    async def check_updates_for_detected_apps(self, result: DetectionResult) -> UpdateRecommendation:
        """Verificar atualizações para aplicações detectadas."""
        if not self.update_checker:
            self.logger.warning("Update checker não está habilitado")
            return UpdateRecommendation(
                total_updates=0,
                critical_updates=0,
                high_priority_updates=0,
                medium_priority_updates=0,
                low_priority_updates=0,
                security_updates=0,
                recommended_action="Sistema de atualizações desabilitado",
                estimated_time_minutes=0,
                risk_assessment="N/A",
                batch_groups=[],
                warnings=[]
            )
        
        try:
            self.logger.info(f"Verificando atualizações para {len(result.applications)} aplicações")
            recommendation = await self.update_checker.check_updates_for_applications(result.applications)
            
            self.logger.info(f"Verificação concluída: {recommendation.total_updates} atualizações encontradas")
            if recommendation.critical_updates > 0:
                self.logger.warning(f"ATENÇÃO: {recommendation.critical_updates} atualizações críticas encontradas!")
            
            return recommendation
            
        except Exception as e:
            self.logger.error(f"Erro ao verificar atualizações: {e}")
            return UpdateRecommendation(
                total_updates=0,
                critical_updates=0,
                high_priority_updates=0,
                medium_priority_updates=0,
                low_priority_updates=0,
                security_updates=0,
                recommended_action=f"Erro na verificação: {str(e)}",
                estimated_time_minutes=0,
                risk_assessment="Erro",
                batch_groups=[],
                warnings=[f"Erro na verificação de atualizações: {str(e)}"]
            )
    
    def get_update_checker_stats(self) -> Dict[str, Any]:
        """Obter estatísticas do verificador de atualizações."""
        if not self.update_checker:
            return {"update_checker_disabled": True}
        
        return self.update_checker.get_cache_stats()
    
    def clear_update_cache(self) -> None:
        """Limpar cache de atualizações."""
        if self.update_checker:
            self.update_checker.clear_cache()
            self.logger.info("Cache de atualizações limpo")
        else:
            self.logger.warning("Update checker não está habilitado")
    
    def configure_update_checker(self, config: Dict[str, Any]) -> None:
        """Configurar o verificador de atualizações."""
        if self.update_checker:
            self.update_checker.configure(config)
            self.logger.info("Configuração do update checker atualizada")
        else:
            self.logger.warning("Update checker não está habilitado")


# Test the module when run directly
if __name__ == "__main__":
    print("Testing DetectionEngine...")
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Test detection engine
    engine = DetectionEngine()
    
    # Test detection of common development tools
    target_apps = ["git", "python", "node", "java", "dotnet", "code"]
    result = engine.detect_all_applications(target_apps)
    
    # Print report
    print(engine.generate_detection_report(result))
    
    print("\nDetectionEngine test completed!")