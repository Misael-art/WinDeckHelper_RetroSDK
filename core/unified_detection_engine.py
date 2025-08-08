#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unified Detection Engine - Sistema de Detecção Unificado
Implementa detecção completa e unificada de aplicativos, runtimes e gerenciadores de pacotes.
"""

import logging
import time
import threading
import platform
import subprocess
import json
import os
import sys
from typing import Dict, List, Any, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum
from abc import ABC, abstractmethod

# Import existing components
from .detection_engine import DetectionEngine, DetectionResult, DetectedApplication
from .essential_runtime_detector import EssentialRuntimeDetector
from .package_manager_integrator import (
    PackageManagerIntegrator, PackageManagerType, PackageInfo, 
    EnvironmentInfo, InstallationScope, PackageStatus
)
from .hierarchical_detection_prioritizer import (
    HierarchicalDetectionPrioritizer, HierarchicalDetectionResult, 
    HierarchicalDetectionReport, DetectionPriority, CompatibilityLevel
)
from .component_status_manager import get_status_manager, ComponentStatus


class DetectionPriority(Enum):
    """Prioridades hierárquicas de detecção"""
    INSTALLED_APPLICATIONS = 1  # Aplicações já instaladas (prioridade máxima)
    COMPATIBLE_VERSIONS = 2     # Versões compatíveis
    STANDARD_LOCATIONS = 3      # Localizações padrão do sistema
    CUSTOM_CONFIGURATIONS = 4   # Configurações personalizadas do usuário


class EnvironmentType(Enum):
    """Tipos de ambiente detectados"""
    GLOBAL = "global"
    VIRTUAL = "virtual"
    USER = "user"
    SYSTEM = "system"
    CONDA_ENV = "conda_env"
    PIPENV = "pipenv"
    POETRY = "poetry"


@dataclass
class PackageManagerDetectionResult:
    """Resultado da detecção de gerenciadores de pacotes"""
    manager_type: PackageManagerType
    is_available: bool = False
    version: str = ""
    executable_path: str = ""
    config_path: str = ""
    global_packages_path: str = ""
    environments: List[Dict[str, Any]] = field(default_factory=list)
    installed_packages: List[PackageInfo] = field(default_factory=list)
    environment_variables: Dict[str, str] = field(default_factory=dict)
    detection_confidence: float = 0.0
    detection_method: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VirtualEnvironmentInfo:
    """Informações sobre ambiente virtual"""
    name: str
    path: str
    environment_type: EnvironmentType
    manager: PackageManagerType
    python_version: str = ""
    is_active: bool = False
    packages: List[PackageInfo] = field(default_factory=list)
    created_date: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HierarchicalDetectionResult:
    """Resultado de detecção hierárquica com priorização"""
    component_name: str
    priority_level: DetectionPriority
    detection_results: List[Dict[str, Any]] = field(default_factory=list)
    recommended_option: Optional[Dict[str, Any]] = None
    confidence_score: float = 0.0
    reasoning: str = ""


@dataclass
class UnifiedDetectionResult:
    """Resultado unificado de detecção"""
    # Detecção base de aplicações
    applications: List[DetectedApplication] = field(default_factory=list)
    
    # Detecção de runtimes essenciais
    essential_runtimes: Dict[str, Any] = field(default_factory=dict)
    
    # Detecção de gerenciadores de pacotes
    package_managers: List[PackageManagerDetectionResult] = field(default_factory=list)
    
    # Ambientes virtuais detectados
    virtual_environments: List[VirtualEnvironmentInfo] = field(default_factory=list)
    
    # Resultados hierárquicos
    hierarchical_results: List[HierarchicalDetectionResult] = field(default_factory=list)
    
    # Métricas de detecção
    total_detected: int = 0
    detection_time: float = 0.0
    detection_confidence: float = 0.0
    
    # Metadados
    detection_timestamp: float = field(default_factory=time.time)
    system_info: Dict[str, str] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)


class PackageManagerDetector(ABC):
    """Classe base para detectores de gerenciadores de pacotes"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"detector_{self.__class__.__name__.lower()}")
    
    @abstractmethod
    def get_manager_type(self) -> PackageManagerType:
        """Retorna o tipo do gerenciador de pacotes"""
        pass
    
    @abstractmethod
    def detect_installation(self) -> PackageManagerDetectionResult:
        """Detecta a instalação do gerenciador de pacotes"""
        pass
    
    @abstractmethod
    def detect_environments(self) -> List[VirtualEnvironmentInfo]:
        """Detecta ambientes virtuais"""
        pass
    
    def _run_command(self, args: List[str], timeout: int = 10) -> Optional[subprocess.CompletedProcess]:
        """Executa comando com timeout"""
        try:
            return subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=timeout
            )
        except Exception as e:
            self.logger.debug(f"Command failed {' '.join(args)}: {e}")
            return None
    
    def _find_executable(self, name: str) -> str:
        """Encontra o executável do gerenciador"""
        try:
            if platform.system() == "Windows":
                result = subprocess.run(
                    ["where", name],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
            else:
                result = subprocess.run(
                    ["which", name],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
            
            if result.returncode == 0:
                return result.stdout.strip().split('\n')[0]
        except Exception as e:
            self.logger.debug(f"Failed to find {name}: {e}")
        
        return ""


class NpmDetector(PackageManagerDetector):
    """Detector para NPM"""
    
    def get_manager_type(self) -> PackageManagerType:
        return PackageManagerType.NPM
    
    def detect_installation(self) -> PackageManagerDetectionResult:
        result = PackageManagerDetectionResult(
            manager_type=PackageManagerType.NPM,
            detection_method="executable_check"
        )
        
        try:
            # Encontrar executável
            executable_path = self._find_executable("npm")
            if not executable_path:
                return result
            
            result.executable_path = executable_path
            result.is_available = True
            
            # Obter versão
            version_result = self._run_command(["npm", "--version"])
            if version_result and version_result.returncode == 0:
                result.version = version_result.stdout.strip()
                result.detection_confidence = 0.9
            
            # Obter configurações
            config_result = self._run_command(["npm", "config", "get", "prefix"])
            if config_result and config_result.returncode == 0:
                result.global_packages_path = config_result.stdout.strip()
            
            # Obter pacotes globais
            global_packages = self._get_global_packages()
            result.installed_packages.extend(global_packages)
            
            # Variáveis de ambiente
            result.environment_variables = {
                "NPM_CONFIG_PREFIX": result.global_packages_path,
                "NODE_PATH": os.environ.get("NODE_PATH", "")
            }
            
            result.metadata = {
                "registry": self._get_registry_url(),
                "cache_path": self._get_cache_path()
            }
            
        except Exception as e:
            self.logger.error(f"Error detecting NPM: {e}")
            result.metadata["error"] = str(e)
        
        return result
    
    def detect_environments(self) -> List[VirtualEnvironmentInfo]:
        """NPM não tem ambientes virtuais tradicionais, mas detecta projetos locais"""
        environments = []
        
        try:
            # Detectar projetos Node.js no diretório atual e subdiretórios
            for root, dirs, files in os.walk(os.getcwd()):
                if "package.json" in files:
                    package_json_path = os.path.join(root, "package.json")
                    try:
                        with open(package_json_path, 'r') as f:
                            package_data = json.load(f)
                        
                        env_info = VirtualEnvironmentInfo(
                            name=package_data.get("name", os.path.basename(root)),
                            path=root,
                            environment_type=EnvironmentType.GLOBAL,
                            manager=PackageManagerType.NPM,
                            metadata={
                                "version": package_data.get("version", ""),
                                "dependencies": package_data.get("dependencies", {}),
                                "devDependencies": package_data.get("devDependencies", {})
                            }
                        )
                        
                        # Detectar pacotes instalados localmente
                        node_modules_path = os.path.join(root, "node_modules")
                        if os.path.exists(node_modules_path):
                            env_info.packages = self._get_local_packages(root)
                        
                        environments.append(env_info)
                        
                    except Exception as e:
                        self.logger.debug(f"Error reading package.json at {package_json_path}: {e}")
        
        except Exception as e:
            self.logger.error(f"Error detecting NPM environments: {e}")
        
        return environments
    
    def _get_global_packages(self) -> List[PackageInfo]:
        """Obtém lista de pacotes globais"""
        packages = []
        try:
            result = self._run_command(["npm", "list", "-g", "--json", "--depth=0"])
            if result and result.returncode == 0:
                data = json.loads(result.stdout)
                dependencies = data.get("dependencies", {})
                
                for name, info in dependencies.items():
                    packages.append(PackageInfo(
                        name=name,
                        version=info.get("version", ""),
                        manager=PackageManagerType.NPM,
                        scope=InstallationScope.GLOBAL,
                        status=PackageStatus.INSTALLED
                    ))
        except Exception as e:
            self.logger.debug(f"Error getting global NPM packages: {e}")
        
        return packages
    
    def _get_local_packages(self, project_path: str) -> List[PackageInfo]:
        """Obtém pacotes locais de um projeto"""
        packages = []
        try:
            result = self._run_command(["npm", "list", "--json", "--depth=0"], timeout=15)
            if result and result.returncode == 0:
                data = json.loads(result.stdout)
                dependencies = data.get("dependencies", {})
                
                for name, info in dependencies.items():
                    packages.append(PackageInfo(
                        name=name,
                        version=info.get("version", ""),
                        install_path=os.path.join(project_path, "node_modules", name),
                        manager=PackageManagerType.NPM,
                        scope=InstallationScope.LOCAL,
                        status=PackageStatus.INSTALLED
                    ))
        except Exception as e:
            self.logger.debug(f"Error getting local NPM packages: {e}")
        
        return packages
    
    def _get_registry_url(self) -> str:
        """Obtém URL do registry"""
        try:
            result = self._run_command(["npm", "config", "get", "registry"])
            if result and result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return "https://registry.npmjs.org/"
    
    def _get_cache_path(self) -> str:
        """Obtém caminho do cache"""
        try:
            result = self._run_command(["npm", "config", "get", "cache"])
            if result and result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return ""


class PipDetector(PackageManagerDetector):
    """Detector para PIP"""
    
    def get_manager_type(self) -> PackageManagerType:
        return PackageManagerType.PIP
    
    def detect_installation(self) -> PackageManagerDetectionResult:
        result = PackageManagerDetectionResult(
            manager_type=PackageManagerType.PIP,
            detection_method="executable_check"
        )
        
        try:
            # Tentar diferentes nomes de executável
            for pip_name in ["pip", "pip3", "python -m pip"]:
                executable_path = self._find_executable(pip_name.split()[0])
                if executable_path or pip_name == "python -m pip":
                    if pip_name == "python -m pip":
                        # Verificar se python -m pip funciona
                        test_result = self._run_command(["python", "-m", "pip", "--version"])
                        if test_result and test_result.returncode == 0:
                            result.executable_path = "python -m pip"
                            result.is_available = True
                            result.version = test_result.stdout.split()[1]
                            break
                    else:
                        result.executable_path = executable_path
                        result.is_available = True
                        
                        # Obter versão
                        version_result = self._run_command([pip_name, "--version"])
                        if version_result and version_result.returncode == 0:
                            result.version = version_result.stdout.split()[1]
                        break
            
            if not result.is_available:
                return result
            
            result.detection_confidence = 0.9
            
            # Obter pacotes instalados
            result.installed_packages = self._get_installed_packages()
            
            # Variáveis de ambiente
            result.environment_variables = {
                "PYTHONPATH": os.environ.get("PYTHONPATH", ""),
                "PIP_CONFIG_FILE": os.environ.get("PIP_CONFIG_FILE", ""),
                "VIRTUAL_ENV": os.environ.get("VIRTUAL_ENV", "")
            }
            
            result.metadata = {
                "python_version": self._get_python_version(),
                "site_packages": self._get_site_packages_path()
            }
            
        except Exception as e:
            self.logger.error(f"Error detecting PIP: {e}")
            result.metadata["error"] = str(e)
        
        return result
    
    def detect_environments(self) -> List[VirtualEnvironmentInfo]:
        """Detecta ambientes virtuais Python"""
        environments = []
        
        try:
            # Detectar ambiente virtual ativo
            virtual_env = os.environ.get("VIRTUAL_ENV")
            if virtual_env:
                env_info = VirtualEnvironmentInfo(
                    name=os.path.basename(virtual_env),
                    path=virtual_env,
                    environment_type=EnvironmentType.VIRTUAL,
                    manager=PackageManagerType.PIP,
                    is_active=True,
                    python_version=self._get_python_version()
                )
                
                # Obter pacotes do ambiente virtual
                env_info.packages = self._get_installed_packages()
                environments.append(env_info)
            
            # Detectar outros ambientes virtuais comuns
            common_venv_paths = [
                os.path.expanduser("~/.virtualenvs"),
                os.path.expanduser("~/venvs"),
                os.path.join(os.getcwd(), "venv"),
                os.path.join(os.getcwd(), ".venv")
            ]
            
            for venv_base in common_venv_paths:
                if os.path.exists(venv_base):
                    if os.path.isdir(venv_base) and venv_base.endswith(("venv", ".venv")):
                        # Ambiente virtual individual
                        env_info = self._create_venv_info(venv_base)
                        if env_info:
                            environments.append(env_info)
                    else:
                        # Diretório com múltiplos ambientes
                        try:
                            for env_name in os.listdir(venv_base):
                                env_path = os.path.join(venv_base, env_name)
                                if os.path.isdir(env_path):
                                    env_info = self._create_venv_info(env_path)
                                    if env_info:
                                        environments.append(env_info)
                        except Exception as e:
                            self.logger.debug(f"Error scanning {venv_base}: {e}")
        
        except Exception as e:
            self.logger.error(f"Error detecting Python environments: {e}")
        
        return environments
    
    def _get_installed_packages(self) -> List[PackageInfo]:
        """Obtém lista de pacotes instalados"""
        packages = []
        try:
            # Tentar pip list --format=json primeiro
            result = self._run_command(["pip", "list", "--format=json"])
            if not result or result.returncode != 0:
                # Fallback para python -m pip
                result = self._run_command(["python", "-m", "pip", "list", "--format=json"])
            
            if result and result.returncode == 0:
                data = json.loads(result.stdout)
                for item in data:
                    packages.append(PackageInfo(
                        name=item.get("name", ""),
                        version=item.get("version", ""),
                        manager=PackageManagerType.PIP,
                        scope=InstallationScope.LOCAL,
                        status=PackageStatus.INSTALLED
                    ))
        except Exception as e:
            self.logger.debug(f"Error getting PIP packages: {e}")
        
        return packages
    
    def _get_python_version(self) -> str:
        """Obtém versão do Python"""
        try:
            result = self._run_command(["python", "--version"])
            if result and result.returncode == 0:
                return result.stdout.strip().replace("Python ", "")
        except Exception:
            pass
        return ""
    
    def _get_site_packages_path(self) -> str:
        """Obtém caminho do site-packages"""
        try:
            result = self._run_command([
                "python", "-c", 
                "import site; print(site.getsitepackages()[0])"
            ])
            if result and result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return ""
    
    def _create_venv_info(self, venv_path: str) -> Optional[VirtualEnvironmentInfo]:
        """Cria informações de ambiente virtual"""
        try:
            # Verificar se é um ambiente virtual válido
            if platform.system() == "Windows":
                python_exe = os.path.join(venv_path, "Scripts", "python.exe")
                pip_exe = os.path.join(venv_path, "Scripts", "pip.exe")
            else:
                python_exe = os.path.join(venv_path, "bin", "python")
                pip_exe = os.path.join(venv_path, "bin", "pip")
            
            if not os.path.exists(python_exe):
                return None
            
            env_info = VirtualEnvironmentInfo(
                name=os.path.basename(venv_path),
                path=venv_path,
                environment_type=EnvironmentType.VIRTUAL,
                manager=PackageManagerType.PIP,
                is_active=venv_path == os.environ.get("VIRTUAL_ENV")
            )
            
            # Obter versão do Python
            try:
                result = subprocess.run(
                    [python_exe, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    env_info.python_version = result.stdout.strip().replace("Python ", "")
            except Exception:
                pass
            
            # Obter pacotes instalados
            if os.path.exists(pip_exe):
                try:
                    result = subprocess.run(
                        [pip_exe, "list", "--format=json"],
                        capture_output=True,
                        text=True,
                        timeout=15
                    )
                    if result.returncode == 0:
                        data = json.loads(result.stdout)
                        for item in data:
                            env_info.packages.append(PackageInfo(
                                name=item.get("name", ""),
                                version=item.get("version", ""),
                                manager=PackageManagerType.PIP,
                                scope=InstallationScope.LOCAL,
                                status=PackageStatus.INSTALLED
                            ))
                except Exception:
                    pass
            
            return env_info
            
        except Exception as e:
            self.logger.debug(f"Error creating venv info for {venv_path}: {e}")
            return None


class CondaDetector(PackageManagerDetector):
    """Detector para Conda"""
    
    def get_manager_type(self) -> PackageManagerType:
        return PackageManagerType.CONDA
    
    def detect_installation(self) -> PackageManagerDetectionResult:
        result = PackageManagerDetectionResult(
            manager_type=PackageManagerType.CONDA,
            detection_method="executable_check"
        )
        
        try:
            # Tentar diferentes executáveis conda
            for conda_name in ["conda", "mamba"]:
                executable_path = self._find_executable(conda_name)
                if executable_path:
                    result.executable_path = executable_path
                    result.is_available = True
                    
                    # Obter versão
                    version_result = self._run_command([conda_name, "--version"])
                    if version_result and version_result.returncode == 0:
                        result.version = version_result.stdout.strip().split()[-1]
                    
                    result.detection_confidence = 0.9
                    break
            
            if not result.is_available:
                return result
            
            # Obter informações de configuração
            info_result = self._run_command(["conda", "info", "--json"])
            if info_result and info_result.returncode == 0:
                info_data = json.loads(info_result.stdout)
                result.config_path = info_data.get("config_files", [""])[0]
                result.global_packages_path = info_data.get("default_prefix", "")
                
                result.metadata = {
                    "conda_version": info_data.get("conda_version", ""),
                    "python_version": info_data.get("python_version", ""),
                    "platform": info_data.get("platform", ""),
                    "channels": info_data.get("channels", [])
                }
            
            # Obter pacotes do ambiente base
            result.installed_packages = self._get_installed_packages("base")
            
            # Variáveis de ambiente
            result.environment_variables = {
                "CONDA_DEFAULT_ENV": os.environ.get("CONDA_DEFAULT_ENV", ""),
                "CONDA_PREFIX": os.environ.get("CONDA_PREFIX", ""),
                "CONDA_SHLVL": os.environ.get("CONDA_SHLVL", "")
            }
            
        except Exception as e:
            self.logger.error(f"Error detecting Conda: {e}")
            result.metadata["error"] = str(e)
        
        return result
    
    def detect_environments(self) -> List[VirtualEnvironmentInfo]:
        """Detecta ambientes Conda"""
        environments = []
        
        try:
            # Listar ambientes conda
            result = self._run_command(["conda", "env", "list", "--json"])
            if result and result.returncode == 0:
                data = json.loads(result.stdout)
                envs = data.get("envs", [])
                
                for env_path in envs:
                    env_name = os.path.basename(env_path)
                    if env_name == "base":
                        env_name = "base"
                    
                    env_info = VirtualEnvironmentInfo(
                        name=env_name,
                        path=env_path,
                        environment_type=EnvironmentType.CONDA_ENV,
                        manager=PackageManagerType.CONDA,
                        is_active=env_path == os.environ.get("CONDA_PREFIX")
                    )
                    
                    # Obter pacotes do ambiente
                    env_info.packages = self._get_installed_packages(env_name)
                    
                    # Obter informações adicionais
                    env_info.metadata = self._get_env_metadata(env_name)
                    
                    environments.append(env_info)
        
        except Exception as e:
            self.logger.error(f"Error detecting Conda environments: {e}")
        
        return environments
    
    def _get_installed_packages(self, env_name: str) -> List[PackageInfo]:
        """Obtém pacotes instalados em um ambiente"""
        packages = []
        try:
            args = ["conda", "list", "--json"]
            if env_name != "base":
                args.extend(["-n", env_name])
            
            result = self._run_command(args)
            if result and result.returncode == 0:
                data = json.loads(result.stdout)
                for item in data:
                    packages.append(PackageInfo(
                        name=item.get("name", ""),
                        version=item.get("version", ""),
                        manager=PackageManagerType.CONDA,
                        scope=InstallationScope.LOCAL,
                        status=PackageStatus.INSTALLED,
                        metadata={
                            "build": item.get("build_string", ""),
                            "channel": item.get("channel", "")
                        }
                    ))
        except Exception as e:
            self.logger.debug(f"Error getting Conda packages for {env_name}: {e}")
        
        return packages
    
    def _get_env_metadata(self, env_name: str) -> Dict[str, Any]:
        """Obtém metadados do ambiente"""
        metadata = {}
        try:
            # Obter informações do Python no ambiente
            args = ["conda", "run"]
            if env_name != "base":
                args.extend(["-n", env_name])
            args.extend(["python", "--version"])
            
            result = self._run_command(args)
            if result and result.returncode == 0:
                metadata["python_version"] = result.stdout.strip().replace("Python ", "")
        except Exception:
            pass
        
        return metadata


class YarnDetector(PackageManagerDetector):
    """Detector para Yarn"""
    
    def get_manager_type(self) -> PackageManagerType:
        return PackageManagerType.YARN
    
    def detect_installation(self) -> PackageManagerDetectionResult:
        result = PackageManagerDetectionResult(
            manager_type=PackageManagerType.YARN,
            detection_method="executable_check"
        )
        
        try:
            executable_path = self._find_executable("yarn")
            if not executable_path:
                return result
            
            result.executable_path = executable_path
            result.is_available = True
            
            # Obter versão
            version_result = self._run_command(["yarn", "--version"])
            if version_result and version_result.returncode == 0:
                result.version = version_result.stdout.strip()
                result.detection_confidence = 0.9
            
            # Obter configurações
            config_result = self._run_command(["yarn", "config", "get", "prefix"])
            if config_result and config_result.returncode == 0:
                result.global_packages_path = config_result.stdout.strip()
            
            # Obter pacotes globais
            global_packages = self._get_global_packages()
            result.installed_packages.extend(global_packages)
            
            result.metadata = {
                "cache_folder": self._get_cache_folder(),
                "registry": self._get_registry()
            }
            
        except Exception as e:
            self.logger.error(f"Error detecting Yarn: {e}")
            result.metadata["error"] = str(e)
        
        return result
    
    def detect_environments(self) -> List[VirtualEnvironmentInfo]:
        """Detecta projetos Yarn"""
        environments = []
        
        try:
            # Detectar projetos Yarn no diretório atual e subdiretórios
            for root, dirs, files in os.walk(os.getcwd()):
                if "yarn.lock" in files or ("package.json" in files and self._has_yarn_config(root)):
                    package_json_path = os.path.join(root, "package.json")
                    if os.path.exists(package_json_path):
                        try:
                            with open(package_json_path, 'r') as f:
                                package_data = json.load(f)
                            
                            env_info = VirtualEnvironmentInfo(
                                name=package_data.get("name", os.path.basename(root)),
                                path=root,
                                environment_type=EnvironmentType.GLOBAL,
                                manager=PackageManagerType.YARN,
                                metadata={
                                    "version": package_data.get("version", ""),
                                    "dependencies": package_data.get("dependencies", {}),
                                    "devDependencies": package_data.get("devDependencies", {}),
                                    "has_yarn_lock": "yarn.lock" in files
                                }
                            )
                            
                            # Detectar pacotes instalados
                            node_modules_path = os.path.join(root, "node_modules")
                            if os.path.exists(node_modules_path):
                                env_info.packages = self._get_local_packages(root)
                            
                            environments.append(env_info)
                            
                        except Exception as e:
                            self.logger.debug(f"Error reading package.json at {package_json_path}: {e}")
        
        except Exception as e:
            self.logger.error(f"Error detecting Yarn environments: {e}")
        
        return environments
    
    def _get_global_packages(self) -> List[PackageInfo]:
        """Obtém pacotes globais do Yarn"""
        packages = []
        try:
            result = self._run_command(["yarn", "global", "list", "--json"])
            if result and result.returncode == 0:
                # Yarn retorna múltiplas linhas JSON
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        try:
                            data = json.loads(line)
                            if data.get("type") == "tree":
                                for item in data.get("data", {}).get("trees", []):
                                    name_version = item.get("name", "")
                                    if "@" in name_version:
                                        name, version = name_version.rsplit("@", 1)
                                    else:
                                        name, version = name_version, ""
                                    
                                    packages.append(PackageInfo(
                                        name=name,
                                        version=version,
                                        manager=PackageManagerType.YARN,
                                        scope=InstallationScope.GLOBAL,
                                        status=PackageStatus.INSTALLED
                                    ))
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            self.logger.debug(f"Error getting global Yarn packages: {e}")
        
        return packages
    
    def _get_local_packages(self, project_path: str) -> List[PackageInfo]:
        """Obtém pacotes locais de um projeto Yarn"""
        packages = []
        try:
            result = self._run_command(["yarn", "list", "--json"], timeout=15)
            if result and result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if line.strip():
                        try:
                            data = json.loads(line)
                            if data.get("type") == "tree":
                                for item in data.get("data", {}).get("trees", []):
                                    name_version = item.get("name", "")
                                    if "@" in name_version:
                                        name, version = name_version.rsplit("@", 1)
                                    else:
                                        name, version = name_version, ""
                                    
                                    packages.append(PackageInfo(
                                        name=name,
                                        version=version,
                                        install_path=os.path.join(project_path, "node_modules", name),
                                        manager=PackageManagerType.YARN,
                                        scope=InstallationScope.LOCAL,
                                        status=PackageStatus.INSTALLED
                                    ))
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            self.logger.debug(f"Error getting local Yarn packages: {e}")
        
        return packages
    
    def _has_yarn_config(self, project_path: str) -> bool:
        """Verifica se o projeto tem configuração Yarn"""
        yarn_config_files = [".yarnrc", ".yarnrc.yml", ".yarnrc.yaml"]
        return any(os.path.exists(os.path.join(project_path, config)) for config in yarn_config_files)
    
    def _get_cache_folder(self) -> str:
        """Obtém pasta de cache do Yarn"""
        try:
            result = self._run_command(["yarn", "cache", "dir"])
            if result and result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return ""
    
    def _get_registry(self) -> str:
        """Obtém registry do Yarn"""
        try:
            result = self._run_command(["yarn", "config", "get", "registry"])
            if result and result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return "https://registry.yarnpkg.com"


class PipenvDetector(PackageManagerDetector):
    """Detector para Pipenv"""
    
    def get_manager_type(self) -> PackageManagerType:
        return PackageManagerType.PIPENV
    
    def detect_installation(self) -> PackageManagerDetectionResult:
        result = PackageManagerDetectionResult(
            manager_type=PackageManagerType.PIPENV,
            detection_method="executable_check"
        )
        
        try:
            executable_path = self._find_executable("pipenv")
            if not executable_path:
                return result
            
            result.executable_path = executable_path
            result.is_available = True
            
            # Obter versão
            version_result = self._run_command(["pipenv", "--version"])
            if version_result and version_result.returncode == 0:
                # Pipenv retorna "pipenv, version X.X.X"
                version_line = version_result.stdout.strip()
                if "version" in version_line:
                    result.version = version_line.split("version")[-1].strip()
                result.detection_confidence = 0.9
            
            # Variáveis de ambiente
            result.environment_variables = {
                "PIPENV_VENV_IN_PROJECT": os.environ.get("PIPENV_VENV_IN_PROJECT", ""),
                "PIPENV_PIPFILE": os.environ.get("PIPENV_PIPFILE", ""),
                "WORKON_HOME": os.environ.get("WORKON_HOME", "")
            }
            
            result.metadata = {
                "venv_location": self._get_venv_location()
            }
            
        except Exception as e:
            self.logger.error(f"Error detecting Pipenv: {e}")
            result.metadata["error"] = str(e)
        
        return result
    
    def detect_environments(self) -> List[VirtualEnvironmentInfo]:
        """Detecta ambientes Pipenv"""
        environments = []
        
        try:
            # Detectar projetos Pipenv no diretório atual e subdiretórios
            for root, dirs, files in os.walk(os.getcwd()):
                if "Pipfile" in files:
                    pipfile_path = os.path.join(root, "Pipfile")
                    try:
                        # Ler Pipfile para obter informações
                        with open(pipfile_path, 'r') as f:
                            pipfile_content = f.read()
                        
                        env_info = VirtualEnvironmentInfo(
                            name=os.path.basename(root),
                            path=root,
                            environment_type=EnvironmentType.PIPENV,
                            manager=PackageManagerType.PIPENV
                        )
                        
                        # Tentar obter localização do ambiente virtual
                        try:
                            venv_result = self._run_command(["pipenv", "--venv"], timeout=10)
                            if venv_result and venv_result.returncode == 0:
                                venv_path = venv_result.stdout.strip()
                                env_info.metadata["venv_path"] = venv_path
                                
                                # Verificar se o ambiente está ativo
                                current_venv = os.environ.get("VIRTUAL_ENV")
                                env_info.is_active = current_venv == venv_path
                        except Exception:
                            pass
                        
                        # Obter pacotes instalados
                        env_info.packages = self._get_pipenv_packages(root)
                        
                        # Obter versão do Python
                        try:
                            python_result = self._run_command(["pipenv", "run", "python", "--version"], timeout=10)
                            if python_result and python_result.returncode == 0:
                                env_info.python_version = python_result.stdout.strip().replace("Python ", "")
                        except Exception:
                            pass
                        
                        environments.append(env_info)
                        
                    except Exception as e:
                        self.logger.debug(f"Error processing Pipfile at {pipfile_path}: {e}")
        
        except Exception as e:
            self.logger.error(f"Error detecting Pipenv environments: {e}")
        
        return environments
    
    def _get_pipenv_packages(self, project_path: str) -> List[PackageInfo]:
        """Obtém pacotes de um projeto Pipenv"""
        packages = []
        try:
            # Mudar para o diretório do projeto temporariamente
            original_cwd = os.getcwd()
            os.chdir(project_path)
            
            try:
                result = self._run_command(["pipenv", "graph", "--json"], timeout=15)
                if result and result.returncode == 0:
                    data = json.loads(result.stdout)
                    for item in data:
                        packages.append(PackageInfo(
                            name=item.get("package_name", ""),
                            version=item.get("installed_version", ""),
                            manager=PackageManagerType.PIPENV,
                            scope=InstallationScope.LOCAL,
                            status=PackageStatus.INSTALLED,
                            dependencies=item.get("dependencies", [])
                        ))
            finally:
                os.chdir(original_cwd)
                
        except Exception as e:
            self.logger.debug(f"Error getting Pipenv packages for {project_path}: {e}")
        
        return packages
    
    def _get_venv_location(self) -> str:
        """Obtém localização padrão dos ambientes virtuais"""
        try:
            result = self._run_command(["pipenv", "--venv"])
            if result and result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return ""


class UnifiedDetectionEngine:
    """Motor de detecção unificado"""
    
    def __init__(self, security_manager=None):
        self.logger = logging.getLogger("unified_detection_engine")
        self.security_manager = security_manager
        
        # Componentes de detecção
        self.base_engine = DetectionEngine()
        self.runtime_detector = EssentialRuntimeDetector()
        self.package_integrator = PackageManagerIntegrator()
        
        # Detectores de gerenciadores de pacotes
        self.package_detectors = {
            PackageManagerType.NPM: NpmDetector(),
            PackageManagerType.PIP: PipDetector(),
            PackageManagerType.CONDA: CondaDetector(),
            PackageManagerType.YARN: YarnDetector(),
            PackageManagerType.PIPENV: PipenvDetector()
        }
        
        # Cache de detecção
        self.detection_cache = {}
        self.cache_ttl = 300  # 5 minutos
        
        # Lock para thread safety
        self.lock = threading.RLock()
    
    def detect_all_unified(self, enable_hierarchical: bool = True) -> UnifiedDetectionResult:
        """Executa detecção unificada completa com sincronização de status"""
        start_time = time.time()
        result = UnifiedDetectionResult()
        status_manager = get_status_manager()
        
        try:
            self.logger.info("Iniciando detecção unificada")
            
            # 1. Detecção base de aplicações
            self.logger.info("Detectando aplicações base...")
            base_result = self.base_engine.detect_all_applications()
            result.applications = base_result.applications
            result.errors.extend(base_result.errors)
            
            # Sincronizar aplicações detectadas com status manager
            self._sync_applications_status(result.applications, status_manager)
            
            # 2. Detecção de runtimes essenciais
            self.logger.info("Detectando runtimes essenciais...")
            result.essential_runtimes = self._detect_essential_runtimes()
            
            # Sincronizar runtimes com status manager
            self._sync_runtimes_status(result.essential_runtimes, status_manager)
            
            # 3. Detecção de gerenciadores de pacotes
            self.logger.info("Detectando gerenciadores de pacotes...")
            result.package_managers = self._detect_package_managers()
            
            # Sincronizar gerenciadores com status manager
            self._sync_package_managers_status(result.package_managers, status_manager)
            
            # 4. Detecção de ambientes virtuais
            self.logger.info("Detectando ambientes virtuais...")
            result.virtual_environments = self._detect_virtual_environments()
            
            # 5. Detecção hierárquica (se habilitada)
            if enable_hierarchical:
                self.logger.info("Aplicando detecção hierárquica...")
                result.hierarchical_results = self._apply_hierarchical_detection(result)
            
            # 6. Calcular métricas
            result.total_detected = len(result.applications) + len(result.package_managers)
            result.detection_time = time.time() - start_time
            result.detection_confidence = self._calculate_overall_confidence(result)
            
            # 7. Informações do sistema
            result.system_info = {
                "platform": platform.system(),
                "architecture": platform.machine(),
                "python_version": platform.python_version(),
                "hostname": platform.node()
            }
            
            self.logger.info(f"Detecção unificada concluída em {result.detection_time:.2f}s")
            
        except Exception as e:
            self.logger.error(f"Erro durante detecção unificada: {e}")
            result.errors.append(f"Erro na detecção unificada: {e}")
        
        return result
    
    def _detect_essential_runtimes(self) -> Dict[str, Any]:
        """Detecta runtimes essenciais"""
        try:
            # Usar o detector existente
            runtime_results = {}
            
            # Lista dos 8 runtimes essenciais conforme especificação
            essential_runtimes = [
                "git",
                "dotnet_sdk",
                "java_jdk",
                "vcpp_redistributables", 
                "anaconda3",
                "dotnet_desktop_runtime",
                "powershell",
                "nodejs_python"
            ]
            
            for runtime in essential_runtimes:
                try:
                    # Usar métodos do detector existente se disponíveis
                    if hasattr(self.runtime_detector, f"detect_{runtime}"):
                        detection_method = getattr(self.runtime_detector, f"detect_{runtime}")
                        runtime_results[runtime] = detection_method()
                    else:
                        # Fallback para detecção básica
                        runtime_results[runtime] = self._basic_runtime_detection(runtime)
                except Exception as e:
                    self.logger.error(f"Erro detectando runtime {runtime}: {e}")
                    runtime_results[runtime] = {"detected": False, "error": str(e)}
            
            return runtime_results
            
        except Exception as e:
            self.logger.error(f"Erro na detecção de runtimes essenciais: {e}")
            return {}
    
    def _basic_runtime_detection(self, runtime_name: str) -> Dict[str, Any]:
        """Detecção básica de runtime"""
        try:
            # Mapeamento de comandos de teste
            test_commands = {
                "git": ["git", "--version"],
                "dotnet_sdk": ["dotnet", "--version"],
                "java_jdk": ["java", "-version"],
                "powershell": ["pwsh", "--version"],
                "nodejs_python": ["node", "--version"]
            }
            
            if runtime_name in test_commands:
                result = subprocess.run(
                    test_commands[runtime_name],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                return {
                    "detected": result.returncode == 0,
                    "version": result.stdout.strip() if result.returncode == 0 else "",
                    "error": result.stderr if result.returncode != 0 else ""
                }
            
            return {"detected": False, "error": "No test command defined"}
            
        except Exception as e:
            return {"detected": False, "error": str(e)}
    
    def _detect_package_managers(self) -> List[PackageManagerDetectionResult]:
        """Detecta todos os gerenciadores de pacotes"""
        results = []
        
        for manager_type, detector in self.package_detectors.items():
            try:
                self.logger.debug(f"Detectando {manager_type.value}...")
                detection_result = detector.detect_installation()
                results.append(detection_result)
                
                if detection_result.is_available:
                    self.logger.info(f"✓ {manager_type.value} detectado: v{detection_result.version}")
                else:
                    self.logger.debug(f"✗ {manager_type.value} não encontrado")
                    
            except Exception as e:
                self.logger.error(f"Erro detectando {manager_type.value}: {e}")
                error_result = PackageManagerDetectionResult(
                    manager_type=manager_type,
                    detection_method="error"
                )
                error_result.metadata["error"] = str(e)
                results.append(error_result)
        
        return results
    
    def _detect_virtual_environments(self) -> List[VirtualEnvironmentInfo]:
        """Detecta todos os ambientes virtuais"""
        all_environments = []
        
        for manager_type, detector in self.package_detectors.items():
            try:
                self.logger.debug(f"Detectando ambientes {manager_type.value}...")
                environments = detector.detect_environments()
                all_environments.extend(environments)
                
                if environments:
                    self.logger.info(f"✓ Encontrados {len(environments)} ambientes {manager_type.value}")
                    
            except Exception as e:
                self.logger.error(f"Erro detectando ambientes {manager_type.value}: {e}")
        
        return all_environments
    
    def _apply_hierarchical_detection(self, result: UnifiedDetectionResult) -> List[HierarchicalDetectionResult]:
        """Aplica detecção hierárquica com priorização"""
        hierarchical_results = []
        
        try:
            # Agrupar detecções por componente
            component_detections = {}
            
            # Adicionar aplicações detectadas
            for app in result.applications:
                if app.name not in component_detections:
                    component_detections[app.name] = []
                
                component_detections[app.name].append({
                    "type": "application",
                    "priority": DetectionPriority.INSTALLED_APPLICATIONS,
                    "data": app,
                    "confidence": 0.9
                })
            
            # Adicionar gerenciadores de pacotes
            for pm in result.package_managers:
                if pm.is_available:
                    component_name = f"{pm.manager_type.value}_package_manager"
                    if component_name not in component_detections:
                        component_detections[component_name] = []
                    
                    component_detections[component_name].append({
                        "type": "package_manager",
                        "priority": DetectionPriority.INSTALLED_APPLICATIONS,
                        "data": pm,
                        "confidence": pm.detection_confidence
                    })
            
            # Processar cada componente
            for component_name, detections in component_detections.items():
                # Ordenar por prioridade e confiança
                sorted_detections = sorted(
                    detections,
                    key=lambda x: (x["priority"].value, -x["confidence"])
                )
                
                # Criar resultado hierárquico
                hierarchical_result = HierarchicalDetectionResult(
                    component_name=component_name,
                    priority_level=sorted_detections[0]["priority"],
                    detection_results=sorted_detections,
                    recommended_option=sorted_detections[0],
                    confidence_score=sorted_detections[0]["confidence"],
                    reasoning=self._generate_reasoning(component_name, sorted_detections)
                )
                
                hierarchical_results.append(hierarchical_result)
        
        except Exception as e:
            self.logger.error(f"Erro na detecção hierárquica: {e}")
        
        return hierarchical_results
    
    def _generate_reasoning(self, component_name: str, detections: List[Dict[str, Any]]) -> str:
        """Gera raciocínio para a escolha hierárquica"""
        if not detections:
            return "Nenhuma detecção disponível"
        
        best = detections[0]
        priority_names = {
            DetectionPriority.INSTALLED_APPLICATIONS: "aplicação já instalada",
            DetectionPriority.COMPATIBLE_VERSIONS: "versão compatível",
            DetectionPriority.STANDARD_LOCATIONS: "localização padrão",
            DetectionPriority.CUSTOM_CONFIGURATIONS: "configuração personalizada"
        }
        
        reasoning = f"Recomendado por ser {priority_names.get(best['priority'], 'detectado')} "
        reasoning += f"com confiança de {best['confidence']:.1%}"
        
        if len(detections) > 1:
            reasoning += f" (entre {len(detections)} opções detectadas)"
        
        return reasoning
    
    def _calculate_overall_confidence(self, result: UnifiedDetectionResult) -> float:
        """Calcula confiança geral da detecção"""
        try:
            confidences = []
            
            # Confiança dos gerenciadores de pacotes
            for pm in result.package_managers:
                if pm.is_available:
                    confidences.append(pm.detection_confidence)
            
            # Confiança dos resultados hierárquicos
            for hr in result.hierarchical_results:
                confidences.append(hr.confidence_score)
            
            if confidences:
                return sum(confidences) / len(confidences)
            
            return 0.0
            
        except Exception:
            return 0.0
    
    def get_package_manager_integration_interfaces(self) -> Dict[PackageManagerType, Any]:
        """Retorna interfaces de integração dos gerenciadores de pacotes"""
        return {
            manager_type: detector 
            for manager_type, detector in self.package_detectors.items()
        }
    
    def _sync_applications_status(self, applications: List[DetectedApplication], status_manager):
        """Sincroniza aplicações detectadas com o status manager"""
        try:
            for app in applications:
                # Determinar status baseado na detecção
                # DetectedApplication sempre representa algo detectado
                status = ComponentStatus.INSTALLED
                
                # Atualizar status no manager
                status_manager.update_component_status(
                    component_id=app.name.lower().replace(" ", "_"),
                    name=app.name,
                    status=status,
                    version_detected=getattr(app, 'version', None),
                    install_path=getattr(app, 'install_path', None)
                )
                
                self.logger.debug(f"Synced application {app.name} with status {status.value}")
                
        except Exception as e:
            self.logger.error(f"Error syncing applications status: {e}")

    def _sync_runtimes_status(self, runtimes: Dict[str, Any], status_manager):
        """Sincroniza runtimes detectados com o status manager"""
        try:
            for runtime_id, runtime_info in runtimes.items():
                # Determinar se está instalado
                is_detected = False
                version = None
                install_path = None
                
                if isinstance(runtime_info, dict):
                    is_detected = runtime_info.get("detected", False)
                    version = runtime_info.get("version")
                    install_path = runtime_info.get("install_path")
                elif hasattr(runtime_info, 'detected'):
                    is_detected = runtime_info.detected
                    version = getattr(runtime_info, 'version', None)
                    install_path = getattr(runtime_info, 'install_path', None)
                
                status = ComponentStatus.INSTALLED if is_detected else ComponentStatus.NOT_DETECTED
                
                # Atualizar status no manager
                status_manager.update_component_status(
                    component_id=runtime_id,
                    name=runtime_id.replace("_", " ").title(),
                    status=status,
                    version_detected=version,
                    install_path=install_path
                )
                
                self.logger.debug(f"Synced runtime {runtime_id} with status {status.value}")
                
        except Exception as e:
            self.logger.error(f"Error syncing runtimes status: {e}")

    def _sync_package_managers_status(self, package_managers: List[PackageManagerDetectionResult], status_manager):
        """Sincroniza gerenciadores de pacotes com o status manager"""
        try:
            for pm in package_managers:
                # Determinar status baseado na detecção
                status = ComponentStatus.INSTALLED if getattr(pm, 'is_installed', True) else ComponentStatus.NOT_DETECTED
                
                # Atualizar status no manager
                status_manager.update_component_status(
                    component_id=pm.manager_type.value,
                    name=pm.manager_type.value.upper(),
                    status=status,
                    version_detected=getattr(pm, 'version', None),
                    install_path=getattr(pm, 'install_path', None)
                )
                
                self.logger.debug(f"Synced package manager {pm.manager_type.value} with status {status.value}")
                
        except Exception as e:
            self.logger.error(f"Error syncing package managers status: {e}")

    def generate_comprehensive_report(self, result: UnifiedDetectionResult) -> str:
        """Gera relatório abrangente da detecção"""
        report = []
        report.append("=== Relatório de Detecção Unificada ===")
        report.append(f"Tempo de detecção: {result.detection_time:.2f}s")
        report.append(f"Confiança geral: {result.detection_confidence:.1%}")
        report.append(f"Total detectado: {result.total_detected} componentes")
        report.append("")
        
        # Aplicações detectadas
        if result.applications:
            report.append(f"Aplicações Detectadas ({len(result.applications)}):")
            for app in result.applications[:10]:  # Limitar a 10 para brevidade
                report.append(f"  ✓ {app.name} v{app.version}")
            if len(result.applications) > 10:
                report.append(f"  ... e mais {len(result.applications) - 10} aplicações")
            report.append("")
        
        # Gerenciadores de pacotes
        report.append("Gerenciadores de Pacotes:")
        for pm in result.package_managers:
            status = "✓" if pm.is_available else "✗"
            version_info = f" v{pm.version}" if pm.version else ""
            report.append(f"  {status} {pm.manager_type.value}{version_info}")
            
            if pm.is_available and pm.installed_packages:
                report.append(f"    └─ {len(pm.installed_packages)} pacotes instalados")
        report.append("")
        
        # Ambientes virtuais
        if result.virtual_environments:
            report.append(f"Ambientes Virtuais ({len(result.virtual_environments)}):")
            for env in result.virtual_environments:
                active_marker = " (ativo)" if env.is_active else ""
                report.append(f"  ✓ {env.name} ({env.manager.value}){active_marker}")
                if env.packages:
                    report.append(f"    └─ {len(env.packages)} pacotes")
            report.append("")
        
        # Runtimes essenciais
        if result.essential_runtimes:
            report.append("Runtimes Essenciais:")
            for runtime, info in result.essential_runtimes.items():
                if hasattr(info, 'get'):
                    status = "✓" if info.get("detected", False) else "✗"
                    version = info.get("version", "")
                elif hasattr(info, 'detected'):
                    status = "✓" if info.detected else "✗"
                    version = getattr(info, 'version', "")
                else:
                    status = "✗"
                    version = ""
                version_info = f" v{version}" if version else ""
                report.append(f"  {status} {runtime}{version_info}")
            report.append("")
        
        # Erros
        if result.errors:
            report.append("Erros Encontrados:")
            for error in result.errors:
                report.append(f"  ⚠ {error}")
        
        return "\n".join(report)


# Instância global
_unified_engine: Optional[UnifiedDetectionEngine] = None

def get_unified_detection_engine() -> UnifiedDetectionEngine:
    """Obtém instância global do motor de detecção unificado"""
    global _unified_engine
    if _unified_engine is None:
        _unified_engine = UnifiedDetectionEngine()
    return _unified_engine


# Teste do módulo quando executado diretamente
if __name__ == "__main__":
    print("Testando Unified Detection Engine...")
    
    # Configurar logging
    logging.basicConfig(level=logging.INFO)
    
    # Testar motor de detecção unificado
    engine = UnifiedDetectionEngine()
    
    # Executar detecção completa
    result = engine.detect_all_unified()
    
    # Gerar e exibir relatório
    report = engine.generate_comprehensive_report(result)
    print("\n" + report)
    
    print(f"\nDetecção concluída em {result.detection_time:.2f}s!")