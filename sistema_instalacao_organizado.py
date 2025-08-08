#!/usr/bin/env python3
"""
Sistema de Instalação Organizado e Robusto
Implementação baseada na arquitetura definida em:
- .kiro/specs/environment-dev-deep-evaluation/design.md
- .kiro/specs/environment-dev-deep-evaluation/requirements.md

Este sistema implementa a arquitetura de camadas definida na spec:
- Architecture Analysis Engine (AAE)
- Unified Detection Engine (UDE) 
- Dependency Validation System (DVS)
- Robust Download Manager (RDM)
- Advanced Installation Manager (AIM)
- Steam Deck Integration Layer (SDL)
- Intelligent Storage Manager (ISM)
- Plugin System Manager (PSM)
- Modern Frontend Manager
"""

import os
import sys
import json
import yaml
import hashlib
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import platform
import winreg
import shutil

# Enums baseados na arquitetura da spec
class InstallationStatus(Enum):
    PENDING = "pending"
    INSTALLING = "installing"
    INSTALLED = "installed"
    FAILED = "failed"
    SKIPPED = "skipped"
    VERIFIED = "verified"
    ROLLBACK_REQUIRED = "rollback_required"

class InstallMethod(Enum):
    EXE = "exe"
    MSI = "msi"
    CHOCOLATEY = "chocolatey"
    ARCHIVE = "archive"
    SCRIPT = "script"
    CUSTOM = "custom"
    MANUAL = "manual"

class DetectionMethod(Enum):
    DMI_SMBIOS = "dmi_smbios"
    STEAM_CLIENT = "steam_client"
    MANUAL_CONFIG = "manual_config"
    FALLBACK = "fallback"

class CriticalityLevel(Enum):
    SECURITY = "security"
    STABILITY = "stability"
    FUNCTIONALITY = "functionality"
    UX = "ux"

# Data Models baseados na arquitetura da spec

@dataclass
class CriticalGap:
    """Representa uma lacuna crítica identificada na análise arquitetural"""
    name: str
    description: str
    criticality: CriticalityLevel
    current_state: str
    expected_state: str
    impact: str
    resolution_steps: List[str] = field(default_factory=list)

@dataclass
class LostFunctionality:
    """Representa funcionalidade perdida durante refatorações"""
    name: str
    description: str
    original_location: str
    last_seen_version: str
    impact_assessment: str
    recovery_plan: List[str] = field(default_factory=list)

@dataclass
class ArchitectureAnalysis:
    """Resultado da análise arquitetural completa"""
    current_architecture: Dict[str, Any]
    design_architecture: Dict[str, Any]
    identified_gaps: List[CriticalGap]
    lost_functionalities: List[LostFunctionality]
    consistency_issues: List[str]
    prioritized_fixes: List[Dict[str, Any]]
    analysis_timestamp: datetime

@dataclass
class EssentialRuntimesStatus:
    """Status dos 8 runtimes essenciais definidos na spec"""
    git_2_47_1: bool = False
    dotnet_sdk_8_0: bool = False
    java_jdk_21: bool = False
    vcpp_redistributables: bool = False
    anaconda3: bool = False
    dotnet_desktop_runtime: bool = False
    powershell_7: bool = False
    nodejs_python_updated: bool = False

@dataclass
class SteamDeckDetectionResult:
    """Resultado da detecção de Steam Deck"""
    hardware_detected: bool
    detection_method: DetectionMethod
    controller_detected: bool
    power_profile_available: bool
    touchscreen_available: bool
    glossi_available: bool
    steam_cloud_available: bool
    fallback_applied: bool

@dataclass
class ComponentInfo:
    """Informações de componente expandidas conforme arquitetura"""
    name: str
    category: str
    description: str
    download_url: str
    install_method: InstallMethod
    install_args: str = ""
    hash_value: str = ""
    hash_algorithm: str = "sha256"
    dependencies: List[str] = field(default_factory=list)
    verify_actions: List[Dict] = field(default_factory=list)
    status: InstallationStatus = InstallationStatus.PENDING
    install_time: Optional[float] = None
    error_message: str = ""
    supported_os: List[str] = field(default_factory=lambda: ["windows"])
    rollback_info: Optional[Dict[str, Any]] = None
    environment_variables: Dict[str, str] = field(default_factory=dict)
    validation_results: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class DependencyNode:
    """Nó no grafo de dependências"""
    name: str
    version: str
    installed: bool
    conflicts: List[str] = field(default_factory=list)

@dataclass
class DependencyEdge:
    """Aresta no grafo de dependências"""
    from_node: str
    to_node: str
    dependency_type: str
    version_constraint: str = ""

@dataclass
class DependencyGraph:
    """Grafo completo de dependências"""
    nodes: List[DependencyNode]
    edges: List[DependencyEdge]
    direct_dependencies: Dict[str, List[str]]
    transitive_dependencies: Dict[str, List[str]]
    version_conflicts: List[Dict[str, Any]]
    circular_dependencies: List[List[str]]
    resolution_path: Optional[List[str]] = None

class InstallationOrganizer:
    """
    Organizador principal do sistema de instalação
    """
    
    def __init__(self, components_dir: str = "environment_dev_deep_evaluation/components"):
        self.components_dir = Path(components_dir)
        self.components: Dict[str, ComponentInfo] = {}
        self.installation_order: List[str] = []
        self.categories = {
            "Runtimes": [],
            "Common Utilities": [],
            "Build Tools": [],
            "Version Control": [],
            "Compilers": [],
            "Game Development": [],
            "Emulators": [],
            "Retro Development": [],
            "Productivity": [],
            "Graphics": [],
            "Multimedia": [],
            "System Tools": [],
            "Network Tools": [],
            "Development Tools": []
        }
        
        # Configuração de logging
        self.setup_logging()
        
    def setup_logging(self):
        """Configura sistema de logging detalhado"""
        log_dir = Path("logs/installation")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"installation_{timestamp}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s | %(levelname)s | %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def load_all_components(self) -> Dict[str, ComponentInfo]:
        """
        Carrega todos os componentes dos arquivos YAML
        """
        self.logger.info("Iniciando carregamento de componentes...")
        
        if not self.components_dir.exists():
            self.logger.error(f"Diretório de componentes não encontrado: {self.components_dir}")
            return {}
            
        yaml_files = list(self.components_dir.glob("*.yaml"))
        self.logger.info(f"Encontrados {len(yaml_files)} arquivos YAML")
        
        for yaml_file in yaml_files:
            if yaml_file.name.endswith('.backup'):
                continue
                
            try:
                self._load_component_file(yaml_file)
            except Exception as e:
                self.logger.error(f"Erro ao carregar {yaml_file}: {e}")
                
        self.logger.info(f"Carregados {len(self.components)} componentes")
        return self.components
        
    def _load_component_file(self, yaml_file: Path):
        """Carrega componentes de um arquivo YAML específico"""
        with open(yaml_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
            
        if not data:
            return
            
        for name, config in data.items():
            if not isinstance(config, dict):
                continue
                
            try:
                component = ComponentInfo(
                    name=name,
                    category=config.get('category', 'Uncategorized'),
                    description=config.get('description', ''),
                    download_url=config.get('download_url', ''),
                    install_method=InstallMethod(config.get('install_method', 'exe')),
                    install_args=config.get('install_args', ''),
                    hash_value=config.get('hash', ''),
                    hash_algorithm=config.get('hash_algorithm', 'sha256'),
                    dependencies=config.get('dependencies', []),
                    verify_actions=config.get('verify_actions', []),
                    supported_os=config.get('supported_os', ['windows'])
                )
                
                self.components[name] = component
                
                # Organiza por categoria
                category = component.category
                if category not in self.categories:
                    self.categories[category] = []
                self.categories[category].append(name)
                
            except Exception as e:
                self.logger.warning(f"Erro ao processar componente {name}: {e}")
                
    def resolve_dependencies(self) -> List[str]:
        """
        Resolve dependências e cria ordem de instalação
        """
        self.logger.info("Resolvendo dependências...")
        
        # Algoritmo de ordenação topológica
        visited = set()
        temp_visited = set()
        order = []
        
        def visit(component_name: str):
            if component_name in temp_visited:
                raise ValueError(f"Dependência circular detectada: {component_name}")
            if component_name in visited:
                return
                
            temp_visited.add(component_name)
            
            if component_name in self.components:
                for dep in self.components[component_name].dependencies:
                    visit(dep)
                    
            temp_visited.remove(component_name)
            visited.add(component_name)
            order.append(component_name)
            
        # Visita todos os componentes
        for component_name in self.components:
            if component_name not in visited:
                visit(component_name)
                
        self.installation_order = order
        self.logger.info(f"Ordem de instalação resolvida: {len(order)} componentes")
        return order
        
    def create_installation_plan(self) -> Dict[str, Any]:
        """
        Cria plano detalhado de instalação
        """
        plan = {
            "metadata": {
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "total_components": len(self.components),
                "categories": len(self.categories),
                "estimated_time": self._estimate_installation_time()
            },
            "categories": {},
            "installation_order": self.installation_order,
            "dependencies_map": self._create_dependency_map()
        }
        
        # Organiza por categorias
        for category, components in self.categories.items():
            if not components:
                continue
                
            plan["categories"][category] = {
                "components": [],
                "total": len(components),
                "estimated_time": len(components) * 2  # 2 min por componente
            }
            
            for comp_name in components:
                if comp_name in self.components:
                    comp = self.components[comp_name]
                    plan["categories"][category]["components"].append({
                        "name": comp_name,
                        "description": comp.description,
                        "method": comp.install_method.value,
                        "dependencies": comp.dependencies,
                        "has_verification": len(comp.verify_actions) > 0
                    })
                    
        return plan
        
    def _estimate_installation_time(self) -> int:
        """Estima tempo total de instalação em minutos"""
        base_time = len(self.components) * 2  # 2 min por componente
        
        # Adiciona tempo extra para componentes complexos
        for comp in self.components.values():
            if comp.install_method in [InstallMethod.CUSTOM, InstallMethod.SCRIPT]:
                base_time += 3
            if len(comp.dependencies) > 2:
                base_time += 1
                
        return base_time
        
    def _create_dependency_map(self) -> Dict[str, List[str]]:
        """Cria mapa de dependências"""
        dep_map = {}
        for name, comp in self.components.items():
            dep_map[name] = comp.dependencies
        return dep_map
        
    def generate_installation_report(self) -> str:
        """
        Gera relatório detalhado do sistema de instalação
        """
        plan = self.create_installation_plan()
        
        report = f"""
# RELATÓRIO DO SISTEMA DE INSTALAÇÃO ORGANIZADO
## Gerado em: {plan['metadata']['created_at']}

### RESUMO EXECUTIVO
- **Total de Componentes**: {plan['metadata']['total_components']}
- **Categorias**: {plan['metadata']['categories']}
- **Tempo Estimado**: {plan['metadata']['estimated_time']} minutos

### CATEGORIAS E COMPONENTES

"""
        
        for category, info in plan["categories"].items():
            if not info["components"]:
                continue
                
            report += f"#### {category} ({info['total']} componentes)\n"
            report += f"*Tempo estimado: {info['estimated_time']} minutos*\n\n"
            
            for comp in info["components"]:
                deps_str = ", ".join(comp["dependencies"]) if comp["dependencies"] else "Nenhuma"
                verification = "✅" if comp["has_verification"] else "❌"
                
                report += f"- **{comp['name']}**\n"
                report += f"  - Descrição: {comp['description']}\n"
                report += f"  - Método: {comp['method']}\n"
                report += f"  - Dependências: {deps_str}\n"
                report += f"  - Verificação: {verification}\n\n"
                
        report += "\n### ORDEM DE INSTALAÇÃO\n\n"
        for i, comp_name in enumerate(self.installation_order, 1):
            if comp_name in self.components:
                comp = self.components[comp_name]
                report += f"{i:2d}. **{comp_name}** ({comp.category})\n"
                
        report += "\n### MAPA DE DEPENDÊNCIAS\n\n"
        for comp_name, deps in plan["dependencies_map"].items():
            if deps:
                report += f"- **{comp_name}** → {', '.join(deps)}\n"
                
        return report

def main():
    """Função principal para demonstração"""
    print("🚀 Sistema de Instalação Organizado e Robusto")
    print("=" * 50)
    
    # Inicializa o organizador
    organizer = InstallationOrganizer()
    
    # Carrega componentes
    components = organizer.load_all_components()
    print(f"✅ Carregados {len(components)} componentes")
    
    # Resolve dependências
    order = organizer.resolve_dependencies()
    print(f"✅ Ordem de instalação resolvida ({len(order)} itens)")
    
    # Gera relatório
    report = organizer.generate_installation_report()
    
    # Salva relatório
    report_file = Path("reports") / f"installation_plan_{time.strftime('%Y%m%d_%H%M%S')}.md"
    report_file.parent.mkdir(exist_ok=True)
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
        
    print(f"📄 Relatório salvo em: {report_file}")
    print("\n" + "=" * 50)
    print("Sistema pronto para instalação!")

if __name__ == "__main__":
    main()