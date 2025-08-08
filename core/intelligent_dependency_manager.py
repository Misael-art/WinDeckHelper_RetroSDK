#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema Inteligente de Gestão de Dependências

Este módulo implementa um sistema avançado de gestão de dependências que:
1. Detecta dependências já instaladas no sistema
2. Evita reinstalações desnecessárias
3. Gerencia dependências condicionais baseadas no ambiente
4. Otimiza a experiência de instalação
5. Fornece relatórios detalhados de decisões

Autor: Environment Dev Team
Versão: 1.0.0
"""

import os
import sys
import logging
import shutil
import subprocess
import platform
import json
from typing import Dict, List, Optional, Tuple, Any, Set
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import time
from datetime import datetime

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DependencyStatus(Enum):
    """Status de uma dependência"""
    NOT_FOUND = "not_found"
    INSTALLED = "installed"
    PARTIALLY_INSTALLED = "partially_installed"
    OUTDATED = "outdated"
    CONFLICTED = "conflicted"

class InstallationDecision(Enum):
    """Decisão de instalação para uma dependência"""
    INSTALL = "install"
    SKIP = "skip"
    UPDATE = "update"
    CONFIGURE = "configure"
    MANUAL_REQUIRED = "manual_required"

@dataclass
class DependencyInfo:
    """Informações sobre uma dependência"""
    name: str
    status: DependencyStatus
    version_found: Optional[str] = None
    version_required: Optional[str] = None
    install_path: Optional[str] = None
    detection_method: Optional[str] = None
    alternatives: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class InstallationPlan:
    """Plano de instalação inteligente"""
    component_name: str
    dependencies_to_install: List[str] = field(default_factory=list)
    dependencies_to_skip: List[str] = field(default_factory=list)
    dependencies_to_configure: List[str] = field(default_factory=list)
    conditional_actions: Dict[str, List[str]] = field(default_factory=dict)
    estimated_time: int = 0  # em segundos
    estimated_size: int = 0  # em MB
    warnings: List[str] = field(default_factory=list)
    optimizations: List[str] = field(default_factory=list)

class IntelligentDependencyManager:
    """Gerenciador inteligente de dependências"""
    
    def __init__(self, cache_enabled: bool = True):
        self.cache_enabled = cache_enabled
        self.detection_cache = {}
        self.dependency_registry = self._initialize_dependency_registry()
        self.platform_info = self._get_platform_info()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
    def _initialize_dependency_registry(self) -> Dict[str, Dict[str, Any]]:
        """Inicializa o registro de dependências conhecidas"""
        return {
            # Editores de Código
            "Visual Studio Code": {
                "detection_methods": [
                    {"type": "executable", "names": ["code", "code.exe"]},
                    {"type": "registry", "path": r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{EA457B21-F73E-494C-ACAB-524FDE069978}_is1"},
                    {"type": "directory", "paths": [
                        "C:\\Program Files\\Microsoft VS Code",
                        "C:\\Users\\{username}\\AppData\\Local\\Programs\\Microsoft VS Code"
                    ]}
                ],
                "alternatives": ["Visual Studio Code Insiders", "VSCodium", "Cursor IDE", "TRAE AI IDE"],
                "category": "editor",
                "priority": 1
            },
            "Cursor IDE": {
                "detection_methods": [
                    {"type": "executable", "names": ["cursor", "cursor.exe"]},
                    {"type": "directory", "paths": [
                        "C:\\Users\\{username}\\AppData\\Local\\Programs\\cursor"
                    ]}
                ],
                "alternatives": ["Visual Studio Code", "TRAE AI IDE"],
                "category": "editor",
                "priority": 1
            },
            "TRAE AI IDE": {
                "detection_methods": [
                    {"type": "executable", "names": ["trae", "trae.exe"]},
                    {"type": "directory", "paths": [
                        "C:\\Users\\{username}\\AppData\\Local\\Programs\\TRAE"
                    ]}
                ],
                "alternatives": ["Visual Studio Code", "Cursor IDE"],
                "category": "editor",
                "priority": 1
            },
            
            # Runtimes
            "Java Runtime Environment": {
                "detection_methods": [
                    {"type": "executable", "names": ["java", "java.exe"]},
                    {"type": "environment_var", "name": "JAVA_HOME"},
                    {"type": "registry", "path": r"HKEY_LOCAL_MACHINE\SOFTWARE\JavaSoft\Java Runtime Environment"}
                ],
                "alternatives": ["OpenJDK", "Oracle JDK"],
                "category": "runtime",
                "priority": 2
            },
            "Node.js": {
                "detection_methods": [
                    {"type": "executable", "names": ["node", "node.exe"]},
                    {"type": "executable", "names": ["npm", "npm.exe"]}
                ],
                "alternatives": ["Bun", "Deno"],
                "category": "runtime",
                "priority": 2
            },
            "Python": {
                "detection_methods": [
                    {"type": "executable", "names": ["python", "python.exe", "python3", "python3.exe"]},
                    {"type": "registry", "path": r"HKEY_LOCAL_MACHINE\SOFTWARE\Python"}
                ],
                "alternatives": ["PyPy", "Anaconda"],
                "category": "runtime",
                "priority": 2
            },
            
            # Ferramentas de Build
            "Make": {
                "detection_methods": [
                    {"type": "executable", "names": ["make", "make.exe", "mingw32-make", "mingw32-make.exe"]}
                ],
                "alternatives": ["CMake", "Ninja"],
                "category": "build_tool",
                "priority": 3
            },
            "Git": {
                "detection_methods": [
                    {"type": "executable", "names": ["git", "git.exe"]},
                    {"type": "registry", "path": r"HKEY_LOCAL_MACHINE\SOFTWARE\GitForWindows"}
                ],
                "alternatives": [],
                "category": "vcs",
                "priority": 3
            },
            
            # Bibliotecas do Sistema
            "Microsoft Visual C++ Redistributable": {
                "detection_methods": [
                    {"type": "registry", "path": r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes"},
                    {"type": "file_exists", "paths": [
                        "C:\\Windows\\System32\\msvcp140.dll",
                        "C:\\Windows\\System32\\vcruntime140.dll"
                    ]}
                ],
                "alternatives": [],
                "category": "system_library",
                "priority": 4
            }
        }
    
    def _get_platform_info(self) -> Dict[str, str]:
        """Obtém informações da plataforma"""
        return {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor()
        }
    
    def detect_dependency(self, dependency_name: str) -> DependencyInfo:
        """Detecta se uma dependência está instalada"""
        # Verificar cache primeiro
        if self.cache_enabled and dependency_name in self.detection_cache:
            cached_result = self.detection_cache[dependency_name]
            if time.time() - cached_result['timestamp'] < 300:  # Cache válido por 5 minutos
                return cached_result['info']
        
        self.logger.info(f"🔍 Detectando dependência: {dependency_name}")
        
        dependency_info = DependencyInfo(
            name=dependency_name,
            status=DependencyStatus.NOT_FOUND
        )
        
        # Verificar se a dependência está no registro
        if dependency_name in self.dependency_registry:
            registry_entry = self.dependency_registry[dependency_name]
            dependency_info = self._detect_using_registry(dependency_name, registry_entry)
        else:
            # Detecção genérica
            dependency_info = self._detect_generic(dependency_name)
        
        # Armazenar no cache
        if self.cache_enabled:
            self.detection_cache[dependency_name] = {
                'info': dependency_info,
                'timestamp': time.time()
            }
        
        return dependency_info
    
    def _detect_using_registry(self, dependency_name: str, registry_entry: Dict[str, Any]) -> DependencyInfo:
        """Detecta dependência usando informações do registro"""
        dependency_info = DependencyInfo(
            name=dependency_name,
            status=DependencyStatus.NOT_FOUND,
            alternatives=registry_entry.get('alternatives', [])
        )
        
        detection_methods = registry_entry.get('detection_methods', [])
        
        for method in detection_methods:
            method_type = method.get('type')
            
            if method_type == 'executable':
                result = self._detect_by_executable(method.get('names', []))
                if result['found']:
                    dependency_info.status = DependencyStatus.INSTALLED
                    dependency_info.install_path = result['path']
                    dependency_info.version_found = result['version']
                    dependency_info.detection_method = 'executable'
                    break
            
            elif method_type == 'directory':
                result = self._detect_by_directory(method.get('paths', []))
                if result['found']:
                    dependency_info.status = DependencyStatus.INSTALLED
                    dependency_info.install_path = result['path']
                    dependency_info.detection_method = 'directory'
                    break
            
            elif method_type == 'registry' and self.platform_info['system'] == 'Windows':
                result = self._detect_by_registry(method.get('path', ''))
                if result['found']:
                    dependency_info.status = DependencyStatus.INSTALLED
                    dependency_info.version_found = result['version']
                    dependency_info.detection_method = 'registry'
                    break
            
            elif method_type == 'environment_var':
                result = self._detect_by_env_var(method.get('name', ''))
                if result['found']:
                    dependency_info.status = DependencyStatus.INSTALLED
                    dependency_info.install_path = result['value']
                    dependency_info.detection_method = 'environment_var'
                    break
            
            elif method_type == 'file_exists':
                result = self._detect_by_file_exists(method.get('paths', []))
                if result['found']:
                    dependency_info.status = DependencyStatus.INSTALLED
                    dependency_info.install_path = result['path']
                    dependency_info.detection_method = 'file_exists'
                    break
        
        return dependency_info
    
    def _detect_generic(self, dependency_name: str) -> DependencyInfo:
        """Detecção genérica para dependências não registradas"""
        dependency_info = DependencyInfo(
            name=dependency_name,
            status=DependencyStatus.NOT_FOUND
        )
        
        # Tentar detecção por executável (nome da dependência)
        executable_names = [dependency_name.lower(), f"{dependency_name.lower()}.exe"]
        result = self._detect_by_executable(executable_names)
        
        if result['found']:
            dependency_info.status = DependencyStatus.INSTALLED
            dependency_info.install_path = result['path']
            dependency_info.version_found = result['version']
            dependency_info.detection_method = 'executable_generic'
        
        return dependency_info
    
    def _detect_by_executable(self, executable_names: List[str]) -> Dict[str, Any]:
        """Detecta dependência por executável"""
        for name in executable_names:
            path = shutil.which(name)
            if path:
                version = self._get_executable_version(path)
                return {
                    'found': True,
                    'path': path,
                    'version': version
                }
        
        return {'found': False}
    
    def _detect_by_directory(self, directory_paths: List[str]) -> Dict[str, Any]:
        """Detecta dependência por diretório"""
        for path_template in directory_paths:
            # Expandir template com username
            if '{username}' in path_template:
                username = os.environ.get('USERNAME', os.environ.get('USER', ''))
                path = path_template.replace('{username}', username)
            else:
                path = path_template
            
            if os.path.exists(path) and os.path.isdir(path):
                return {
                    'found': True,
                    'path': path
                }
        
        return {'found': False}
    
    def _detect_by_registry(self, registry_path: str) -> Dict[str, Any]:
        """Detecta dependência por registro do Windows"""
        if self.platform_info['system'] != 'Windows':
            return {'found': False}
        
        try:
            import winreg
            
            # Dividir o caminho do registro
            parts = registry_path.split('\\')
            if len(parts) < 2:
                return {'found': False}
            
            # Mapear hives
            hive_map = {
                'HKEY_LOCAL_MACHINE': winreg.HKEY_LOCAL_MACHINE,
                'HKEY_CURRENT_USER': winreg.HKEY_CURRENT_USER,
                'HKEY_CLASSES_ROOT': winreg.HKEY_CLASSES_ROOT
            }
            
            hive = hive_map.get(parts[0])
            if not hive:
                return {'found': False}
            
            subkey = '\\'.join(parts[1:])
            
            with winreg.OpenKey(hive, subkey) as key:
                # Tentar obter versão
                version = None
                try:
                    version, _ = winreg.QueryValueEx(key, 'Version')
                except FileNotFoundError:
                    try:
                        version, _ = winreg.QueryValueEx(key, 'DisplayVersion')
                    except FileNotFoundError:
                        pass
                
                return {
                    'found': True,
                    'version': version
                }
        
        except (ImportError, OSError, FileNotFoundError):
            return {'found': False}
    
    def _detect_by_env_var(self, env_var_name: str) -> Dict[str, Any]:
        """Detecta dependência por variável de ambiente"""
        value = os.environ.get(env_var_name)
        if value and os.path.exists(value):
            return {
                'found': True,
                'value': value
            }
        
        return {'found': False}
    
    def _detect_by_file_exists(self, file_paths: List[str]) -> Dict[str, Any]:
        """Detecta dependência por existência de arquivo"""
        for path in file_paths:
            if os.path.exists(path):
                return {
                    'found': True,
                    'path': path
                }
        
        return {'found': False}
    
    def _get_executable_version(self, executable_path: str) -> Optional[str]:
        """Obtém versão de um executável"""
        version_commands = [
            ['--version'],
            ['-version'],
            ['-V'],
            ['version']
        ]
        
        for cmd_args in version_commands:
            try:
                result = subprocess.run(
                    [executable_path] + cmd_args,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0 and result.stdout:
                    # Extrair versão do output
                    import re
                    version_pattern = r'(\d+\.\d+(?:\.\d+)?(?:\.\d+)?)'
                    match = re.search(version_pattern, result.stdout)
                    if match:
                        return match.group(1)
            
            except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
                continue
        
        return None
    
    def create_installation_plan(self, component_name: str, dependencies: List[str], 
                               conditional_dependencies: Dict[str, Any] = None) -> InstallationPlan:
        """Cria um plano de instalação inteligente"""
        self.logger.info(f"🎯 Criando plano de instalação inteligente para {component_name}...")
        
        plan = InstallationPlan(component_name=component_name)
        detected_dependencies = {}
        
        # Detectar todas as dependências
        for dep in dependencies:
            detected_dependencies[dep] = self.detect_dependency(dep)
        
        # Analisar dependências condicionais
        if conditional_dependencies:
            self._analyze_conditional_dependencies(plan, detected_dependencies, conditional_dependencies)
        
        # Determinar ações para cada dependência
        for dep_name, dep_info in detected_dependencies.items():
            decision = self._make_installation_decision(dep_info)
            
            if decision == InstallationDecision.INSTALL:
                plan.dependencies_to_install.append(dep_name)
            elif decision == InstallationDecision.SKIP:
                plan.dependencies_to_skip.append(dep_name)
                plan.optimizations.append(f"Pulando {dep_name} - já instalado")
            elif decision == InstallationDecision.CONFIGURE:
                plan.dependencies_to_configure.append(dep_name)
            elif decision == InstallationDecision.MANUAL_REQUIRED:
                plan.warnings.append(f"Instalação manual necessária para {dep_name}")
        
        # Calcular estimativas
        plan.estimated_time = len(plan.dependencies_to_install) * 60  # 1 min por dependência
        plan.estimated_size = len(plan.dependencies_to_install) * 100  # 100MB por dependência
        
        self._log_installation_plan(plan)
        return plan
    
    def _analyze_conditional_dependencies(self, plan: InstallationPlan, 
                                        detected_dependencies: Dict[str, DependencyInfo],
                                        conditional_dependencies: Dict[str, Any]) -> None:
        """Analisa dependências condicionais"""
        for condition_type, condition_data in conditional_dependencies.items():
            if condition_type == 'editors':
                self._analyze_editor_condition(plan, detected_dependencies, condition_data)
    
    def _analyze_editor_condition(self, plan: InstallationPlan,
                                detected_dependencies: Dict[str, DependencyInfo],
                                condition_data: Dict[str, Any]) -> None:
        """Analisa condição de editores"""
        condition = condition_data.get('condition')
        dependencies = condition_data.get('dependencies', [])
        
        if condition == 'no_compatible_editor_detected':
            # Verificar se há editores compatíveis instalados
            compatible_editors = [
                'Visual Studio Code', 'Cursor IDE', 'TRAE AI IDE',
                'Visual Studio Code Insiders', 'VSCodium'
            ]
            
            editors_found = []
            for editor in compatible_editors:
                editor_info = self.detect_dependency(editor)
                if editor_info.status == DependencyStatus.INSTALLED:
                    editors_found.append(editor)
            
            if editors_found:
                # Editores compatíveis encontrados - pular dependências condicionais
                for dep in dependencies:
                    if dep not in plan.dependencies_to_skip:
                        plan.dependencies_to_skip.append(dep)
                        plan.optimizations.append(
                            f"Pulando {dep} - editor compatível encontrado: {', '.join(editors_found)}"
                        )
            else:
                # Nenhum editor compatível - instalar dependências condicionais
                for dep in dependencies:
                    if dep not in plan.dependencies_to_install:
                        plan.dependencies_to_install.append(dep)
                        plan.conditional_actions.setdefault('editors', []).append(dep)
    
    def _make_installation_decision(self, dependency_info: DependencyInfo) -> InstallationDecision:
        """Toma decisão de instalação para uma dependência"""
        if dependency_info.status == DependencyStatus.INSTALLED:
            return InstallationDecision.SKIP
        elif dependency_info.status == DependencyStatus.PARTIALLY_INSTALLED:
            return InstallationDecision.CONFIGURE
        elif dependency_info.status == DependencyStatus.OUTDATED:
            return InstallationDecision.UPDATE
        elif dependency_info.status == DependencyStatus.CONFLICTED:
            return InstallationDecision.MANUAL_REQUIRED
        else:
            return InstallationDecision.INSTALL
    
    def _log_installation_plan(self, plan: InstallationPlan) -> None:
        """Registra o plano de instalação"""
        self.logger.info(f"📋 Plano de instalação para {plan.component_name}:")
        
        if plan.dependencies_to_install:
            self.logger.info(f"  📦 Instalar: {', '.join(plan.dependencies_to_install)}")
        
        if plan.dependencies_to_skip:
            self.logger.info(f"  ⏭️  Pular: {', '.join(plan.dependencies_to_skip)}")
        
        if plan.dependencies_to_configure:
            self.logger.info(f"  🔧 Configurar: {', '.join(plan.dependencies_to_configure)}")
        
        if plan.optimizations:
            self.logger.info(f"  ⚡ Otimizações: {len(plan.optimizations)} aplicadas")
        
        if plan.warnings:
            self.logger.warning(f"  ⚠️  Avisos: {len(plan.warnings)} encontrados")
        
        self.logger.info(f"  ⏱️  Tempo estimado: {plan.estimated_time // 60} minutos")
        self.logger.info(f"  💾 Tamanho estimado: {plan.estimated_size} MB")
    
    def generate_report(self, plan: InstallationPlan) -> Dict[str, Any]:
        """Gera relatório detalhado do plano de instalação"""
        return {
            'component_name': plan.component_name,
            'timestamp': datetime.now().isoformat(),
            'platform': self.platform_info,
            'summary': {
                'total_dependencies': len(plan.dependencies_to_install) + len(plan.dependencies_to_skip) + len(plan.dependencies_to_configure),
                'to_install': len(plan.dependencies_to_install),
                'to_skip': len(plan.dependencies_to_skip),
                'to_configure': len(plan.dependencies_to_configure),
                'optimizations_applied': len(plan.optimizations),
                'warnings': len(plan.warnings)
            },
            'details': {
                'dependencies_to_install': plan.dependencies_to_install,
                'dependencies_to_skip': plan.dependencies_to_skip,
                'dependencies_to_configure': plan.dependencies_to_configure,
                'conditional_actions': plan.conditional_actions,
                'optimizations': plan.optimizations,
                'warnings': plan.warnings
            },
            'estimates': {
                'time_seconds': plan.estimated_time,
                'size_mb': plan.estimated_size
            }
        }
    
    def clear_cache(self) -> None:
        """Limpa o cache de detecção"""
        self.detection_cache.clear()
        self.logger.info("🧹 Cache de detecção limpo")

def get_intelligent_dependency_manager() -> IntelligentDependencyManager:
    """Factory function para obter uma instância do gerenciador"""
    return IntelligentDependencyManager()

if __name__ == "__main__":
    # Exemplo de uso
    manager = get_intelligent_dependency_manager()
    
    # Testar detecção de dependências
    dependencies = [
        "Visual Studio Code",
        "Java Runtime Environment",
        "Node.js",
        "Git",
        "Make"
    ]
    
    print("🔍 Testando detecção de dependências...")
    for dep in dependencies:
        info = manager.detect_dependency(dep)
        status_icon = "✅" if info.status == DependencyStatus.INSTALLED else "❌"
        print(f"  {status_icon} {dep}: {info.status.value}")
        if info.version_found:
            print(f"    Versão: {info.version_found}")
        if info.install_path:
            print(f"    Caminho: {info.install_path}")
    
    # Testar criação de plano
    print("\n📋 Criando plano de instalação...")
    conditional_deps = {
        'editors': {
            'condition': 'no_compatible_editor_detected',
            'dependencies': ['Visual Studio Code']
        }
    }
    
    plan = manager.create_installation_plan(
        "Teste Component",
        dependencies,
        conditional_deps
    )
    
    # Gerar relatório
    report = manager.generate_report(plan)
    print(f"\n📊 Relatório gerado: {json.dumps(report, indent=2, ensure_ascii=False)}")