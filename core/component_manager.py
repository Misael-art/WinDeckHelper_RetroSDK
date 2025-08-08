"""Gerenciador de componentes integrado com retro devkits
Gerencia a instalação e configuração de todos os componentes do sistema"""

import os
import sys
import json
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum

# Importar managers de retro devkits
from .retro_devkit_manager import RetroDevKitManager
from .retro_devkit_detector import RetroDevkitDetector
from .retro_devkit_config import RetroDevkitConfigManager
from .retro_devkit_logger import RetroDevkitLogger

# Importar outros managers do sistema
from .installation_manager import InstallationManager
from .configuration_manager import ConfigurationManager
from .download_manager import DownloadManager
from .storage_manager import StorageManager

class ComponentType(Enum):
    """Tipos de componentes"""
    RETRO_DEVKIT = "retro_devkit"
    EMULATOR = "emulator"
    RUNTIME = "runtime"
    TOOL = "tool"
    GAME = "game"
    UTILITY = "utility"
    DRIVER = "driver"
    PLUGIN = "plugin"

@dataclass
class ComponentInfo:
    """Informações de um componente"""
    name: str
    category: str
    description: str
    component_type: ComponentType
    download_url: Optional[str] = None
    install_method: str = "auto"
    custom_installer: Optional[str] = None
    dependencies: List[str] = None
    verify_actions: List[Dict[str, Any]] = None
    is_installed: bool = False
    installation_path: Optional[Path] = None
    version: Optional[str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.verify_actions is None:
            self.verify_actions = []

class ComponentManager:
    """Gerenciador principal de componentes"""
    
    def __init__(self, base_path: Path, config_path: Optional[Path] = None):
        self.base_path = base_path
        self.config_path = config_path or base_path / "config"
        
        # Configurar logging
        self.logger_manager = RetroDevkitLogger(base_path)
        self.logger = self.logger_manager.get_main_logger()
        
        # Inicializar managers
        self.retro_manager = RetroDevKitManager(base_path)
        self.retro_detector = RetroDevkitDetector(base_path, self.logger)
        self.retro_config = RetroDevkitConfigManager(base_path, self.logger)
        
        # Managers do sistema existente
        self.installation_manager = InstallationManager(base_path)
        self.download_manager = DownloadManager(base_path)
        self.storage_manager = StorageManager(base_path)
        
        # Cache de componentes
        self.components: Dict[str, ComponentInfo] = {}
        self.component_files: List[Path] = []
        
        # Carregar componentes
        self.load_all_components()
        
    def load_all_components(self) -> bool:
        """Carrega todos os componentes do sistema"""
        try:
            self.logger.info("Carregando componentes do sistema...")
            
            # Carregar componentes modulares
            components_dir = self.config_path / "components"
            if components_dir.exists():
                for yaml_file in components_dir.glob("*.yaml"):
                    if yaml_file.name.endswith(".backup"):
                        continue
                    self._load_component_file(yaml_file)
                    
            # Carregar componentes de retro devkits
            self._load_retro_devkit_components()
            
            self.logger.info(f"Total de {len(self.components)} componentes carregados")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar componentes: {e}")
            return False
            
    def _load_component_file(self, yaml_file: Path) -> bool:
        """Carrega componentes de um arquivo YAML"""
        try:
            with open(yaml_file, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                
            if not data:
                return True
                
            self.component_files.append(yaml_file)
            
            for component_name, component_data in data.items():
                if component_name.startswith('_'):
                    continue  # Pular metadados
                    
                # Determinar tipo do componente
                component_type = self._determine_component_type(component_data)
                
                component_info = ComponentInfo(
                    name=component_name,
                    category=component_data.get('category', 'Unknown'),
                    description=component_data.get('description', ''),
                    component_type=component_type,
                    download_url=component_data.get('download_url'),
                    install_method=component_data.get('install_method', 'auto'),
                    custom_installer=component_data.get('custom_installer'),
                    dependencies=component_data.get('dependencies', []),
                    verify_actions=component_data.get('verify_actions', [])
                )
                
                self.components[component_name] = component_info
                
            self.logger.debug(f"Carregados {len(data)} componentes de {yaml_file.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar {yaml_file}: {e}")
            return False
            
    def _determine_component_type(self, component_data: Dict[str, Any]) -> ComponentType:
        """Determina o tipo do componente baseado nos dados"""
        category = component_data.get('category', '').lower()
        custom_installer = component_data.get('custom_installer', '')
        
        if 'retro development' in category:
            return ComponentType.RETRO_DEVKIT
        elif 'retro emulators' in category or 'emulator' in category:
            return ComponentType.EMULATOR
        elif 'runtime' in category:
            return ComponentType.RUNTIME
        elif custom_installer and 'retro_devkit_manager' in custom_installer:
            return ComponentType.RETRO_DEVKIT
        elif 'driver' in category:
            return ComponentType.DRIVER
        elif 'game' in category:
            return ComponentType.GAME
        else:
            return ComponentType.TOOL
            
    def _load_retro_devkit_components(self):
        """Carrega componentes específicos de retro devkits"""
        try:
            # Detectar devkits instalados
            detection_results = self.retro_detector.detect_all_devkits()
            
            for devkit_name, result in detection_results.items():
                if devkit_name in self.components:
                    # Atualizar informações de instalação
                    self.components[devkit_name].is_installed = result.is_installed
                    self.components[devkit_name].installation_path = result.installation_path
                    self.components[devkit_name].version = result.version
                    
        except Exception as e:
            self.logger.error(f"Erro ao carregar componentes de retro devkits: {e}")
            
    def get_component(self, name: str) -> Optional[ComponentInfo]:
        """Obtém informações de um componente"""
        return self.components.get(name)
        
    def get_components_by_type(self, component_type: ComponentType) -> List[ComponentInfo]:
        """Obtém componentes por tipo"""
        return [comp for comp in self.components.values() if comp.component_type == component_type]
        
    def get_components_by_category(self, category: str) -> List[ComponentInfo]:
        """Obtém componentes por categoria"""
        return [comp for comp in self.components.values() if comp.category.lower() == category.lower()]
        
    def is_component_installed(self, name: str) -> bool:
        """Verifica se um componente está instalado"""
        component = self.get_component(name)
        if not component:
            return False
            
        # Para retro devkits, usar detecção específica
        if component.component_type == ComponentType.RETRO_DEVKIT:
            return self._verify_retro_devkit_installation(name)
            
        # Para outros componentes, usar verificação padrão
        return self._verify_component_installation(component)
        
    def _verify_retro_devkit_installation(self, devkit_name: str) -> bool:
        """Verifica instalação de um retro devkit"""
        try:
            detection_results = self.retro_detector.detect_all_devkits()
            result = detection_results.get(devkit_name)
            return result.is_installed if result else False
        except:
            return False
            
    def _verify_component_installation(self, component: ComponentInfo) -> bool:
        """Verifica instalação de um componente padrão"""
        try:
            for action in component.verify_actions:
                if action.get('type') == 'file_exists':
                    file_path = Path(action.get('path', ''))
                    if not file_path.is_absolute():
                        file_path = self.base_path / file_path
                    if not file_path.exists():
                        return False
                        
            return True
        except:
            return False
            
    def install_component(self, name: str, force_reinstall: bool = False) -> bool:
        """Instala um componente"""
        component = self.get_component(name)
        if not component:
            self.logger.error(f"Componente '{name}' não encontrado")
            return False
            
        if component.is_installed and not force_reinstall:
            self.logger.info(f"Componente '{name}' já está instalado")
            return True
            
        self.logger.info(f"Iniciando instalação do componente '{name}'...")
        
        try:
            # Instalar dependências primeiro
            if not self._install_dependencies(component):
                self.logger.error(f"Falha ao instalar dependências de '{name}'")
                return False
                
            # Instalar o componente
            if component.component_type == ComponentType.RETRO_DEVKIT:
                return self._install_retro_devkit(name)
            elif component.component_type == ComponentType.EMULATOR:
                return self._install_emulator(name)
            else:
                return self._install_standard_component(component)
                
        except Exception as e:
            self.logger.error(f"Erro na instalação de '{name}': {e}")
            return False
            
    def _install_dependencies(self, component: ComponentInfo) -> bool:
        """Instala dependências de um componente"""
        for dep_name in component.dependencies:
            if not self.is_component_installed(dep_name):
                self.logger.info(f"Instalando dependência: {dep_name}")
                if not self.install_component(dep_name):
                    return False
        return True
        
    def _install_retro_devkit(self, devkit_name: str) -> bool:
        """Instala um retro devkit"""
        try:
            return self.retro_manager.install_devkit(devkit_name)
        except Exception as e:
            self.logger.error(f"Erro na instalação do devkit '{devkit_name}': {e}")
            return False
            
    def _install_emulator(self, emulator_name: str) -> bool:
        """Instala um emulador"""
        try:
            return self.retro_manager.install_emulator(emulator_name)
        except Exception as e:
            self.logger.error(f"Erro na instalação do emulador '{emulator_name}': {e}")
            return False
            
    def _install_standard_component(self, component: ComponentInfo) -> bool:
        """Instala um componente padrão"""
        try:
            if component.custom_installer:
                # Usar instalador customizado
                return self._run_custom_installer(component)
            else:
                # Usar instalação padrão
                return self.installation_manager.install_component(component.name)
        except Exception as e:
            self.logger.error(f"Erro na instalação padrão de '{component.name}': {e}")
            return False
            
    def _run_custom_installer(self, component: ComponentInfo) -> bool:
        """Executa instalador customizado"""
        try:
            if not component.custom_installer:
                self.logger.error(f"Instalador customizado não especificado para {component.name}")
                return False
            
            self.logger.info(f"Executando instalador customizado: {component.custom_installer}")
            
            # Dividir o instalador em módulo e função
            if "." in component.custom_installer:
                module_name, function_name = component.custom_installer.rsplit(".", 1)
            else:
                self.logger.error(f"Formato de instalador inválido: {component.custom_installer}")
                return False
            
            # Importar e executar o instalador
            if module_name == "retro_devkit_manager":
                installer_func = getattr(self.retro_manager, function_name, None)
                if installer_func and callable(installer_func):
                    return installer_func()
                else:
                    self.logger.error(f"Função {function_name} não encontrada em retro_devkit_manager")
                    return False
            elif module_name == "intelligent_sgdk_installer":
                # Usar o instalador inteligente do SGDK
                from .intelligent_sgdk_installer import get_intelligent_sgdk_installer
                installer = get_intelligent_sgdk_installer(self.base_path, self.logger)
                installer_func = getattr(installer, function_name, None)
                if installer_func and callable(installer_func):
                    return installer_func()
                else:
                    self.logger.error(f"Função {function_name} não encontrada em intelligent_sgdk_installer")
                    return False
            else:
                self.logger.error(f"Módulo de instalador não suportado: {module_name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Erro ao executar instalador customizado: {e}")
            return False
            
    def uninstall_component(self, name: str) -> bool:
        """Desinstala um componente"""
        component = self.get_component(name)
        if not component:
            self.logger.error(f"Componente '{name}' não encontrado")
            return False
            
        if not component.is_installed:
            self.logger.info(f"Componente '{name}' não está instalado")
            return True
            
        self.logger.info(f"Desinstalando componente '{name}'...")
        
        try:
            if component.component_type == ComponentType.RETRO_DEVKIT:
                return self.retro_manager.uninstall_devkit(name)
            else:
                # Desinstalação padrão
                return self._uninstall_standard_component(component)
                
        except Exception as e:
            self.logger.error(f"Erro na desinstalação de '{name}': {e}")
            return False
            
    def _uninstall_standard_component(self, component: ComponentInfo) -> bool:
        """Desinstala um componente padrão"""
        try:
            if component.installation_path and component.installation_path.exists():
                import shutil
                shutil.rmtree(component.installation_path)
                self.logger.info(f"Removido diretório: {component.installation_path}")
                
            component.is_installed = False
            component.installation_path = None
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na desinstalação padrão: {e}")
            return False
            
    def update_component(self, name: str) -> bool:
        """Atualiza um componente"""
        component = self.get_component(name)
        if not component:
            self.logger.error(f"Componente '{name}' não encontrado")
            return False
            
        self.logger.info(f"Atualizando componente '{name}'...")
        
        try:
            if component.component_type == ComponentType.RETRO_DEVKIT:
                return self.retro_manager.update_devkit(name)
            else:
                # Atualização padrão (reinstalar)
                return self.install_component(name, force_reinstall=True)
                
        except Exception as e:
            self.logger.error(f"Erro na atualização de '{name}': {e}")
            return False
            
    def get_installation_status(self) -> Dict[str, Any]:
        """Obtém status de instalação de todos os componentes"""
        status = {
            "total_components": len(self.components),
            "installed_count": 0,
            "by_type": {},
            "by_category": {},
            "retro_devkits": {},
            "components": {}
        }
        
        for name, component in self.components.items():
            is_installed = self.is_component_installed(name)
            
            if is_installed:
                status["installed_count"] += 1
                
            # Contar por tipo
            type_name = component.component_type.value
            if type_name not in status["by_type"]:
                status["by_type"][type_name] = {"total": 0, "installed": 0}
            status["by_type"][type_name]["total"] += 1
            if is_installed:
                status["by_type"][type_name]["installed"] += 1
                
            # Contar por categoria
            if component.category not in status["by_category"]:
                status["by_category"][component.category] = {"total": 0, "installed": 0}
            status["by_category"][component.category]["total"] += 1
            if is_installed:
                status["by_category"][component.category]["installed"] += 1
                
            # Status individual
            status["components"][name] = {
                "installed": is_installed,
                "type": type_name,
                "category": component.category,
                "version": component.version
            }
            
        # Status específico de retro devkits
        try:
            retro_results = self.retro_detector.detect_all_devkits()
            status["retro_devkits"] = {
                name: {
                    "installed": result.is_installed,
                    "confidence": result.confidence,
                    "version": result.version,
                    "path": str(result.installation_path) if result.installation_path else None
                }
                for name, result in retro_results.items()
            }
        except Exception as e:
            self.logger.error(f"Erro ao obter status de retro devkits: {e}")
            
        return status
        
    def generate_installation_report(self) -> str:
        """Gera relatório de instalação"""
        status = self.get_installation_status()
        
        report = []
        report.append("=" * 60)
        report.append("RELATÓRIO DE COMPONENTES DO SISTEMA")
        report.append("=" * 60)
        report.append("")
        
        # Resumo geral
        report.append("📊 RESUMO GERAL:")
        report.append(f"  Total de componentes: {status['total_components']}")
        report.append(f"  Componentes instalados: {status['installed_count']}")
        report.append(f"  Taxa de instalação: {status['installed_count']/status['total_components']*100:.1f}%")
        report.append("")
        
        # Por tipo
        report.append("📦 POR TIPO:")
        for type_name, type_data in status["by_type"].items():
            report.append(f"  {type_name}: {type_data['installed']}/{type_data['total']}")
        report.append("")
        
        # Por categoria
        report.append("🏷️ POR CATEGORIA:")
        for category, cat_data in status["by_category"].items():
            report.append(f"  {category}: {cat_data['installed']}/{cat_data['total']}")
        report.append("")
        
        # Retro devkits específicos
        if status["retro_devkits"]:
            report.append("🎮 RETRO DEVKITS:")
            for name, devkit_data in status["retro_devkits"].items():
                status_icon = "✅" if devkit_data["installed"] else "❌"
                report.append(f"  {status_icon} {name}")
                if devkit_data["installed"]:
                    report.append(f"    Versão: {devkit_data['version'] or 'Desconhecida'}")
                    report.append(f"    Confiança: {devkit_data['confidence']:.1%}")
                    if devkit_data["path"]:
                        report.append(f"    Caminho: {devkit_data['path']}")
                report.append("")
                
        report.append("=" * 60)
        
        return "\n".join(report)
        
    def refresh_component_status(self) -> bool:
        """Atualiza status de todos os componentes"""
        try:
            self.logger.info("Atualizando status dos componentes...")
            
            # Recarregar detecção de retro devkits
            self._load_retro_devkit_components()
            
            # Verificar outros componentes
            for name, component in self.components.items():
                if component.component_type != ComponentType.RETRO_DEVKIT:
                    component.is_installed = self._verify_component_installation(component)
                    
            self.logger.info("Status dos componentes atualizado")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao atualizar status: {e}")
            return False
            
    def export_component_list(self, export_path: Path) -> bool:
        """Exporta lista de componentes"""
        try:
            export_data = {
                "export_timestamp": str(Path().cwd()),  # Placeholder
                "total_components": len(self.components),
                "components": {}
            }
            
            for name, component in self.components.items():
                export_data["components"][name] = {
                    "category": component.category,
                    "description": component.description,
                    "type": component.component_type.value,
                    "installed": self.is_component_installed(name),
                    "version": component.version,
                    "dependencies": component.dependencies
                }
                
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
                
            self.logger.info(f"Lista de componentes exportada para: {export_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao exportar lista: {e}")
            return False

# Função de conveniência
def get_component_manager(base_path: Optional[Path] = None) -> ComponentManager:
    """Função de conveniência para obter o gerenciador de componentes"""
    if base_path is None:
        base_path = Path.cwd()
    return ComponentManager(base_path)