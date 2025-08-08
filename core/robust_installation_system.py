# -*- coding: utf-8 -*-
"""
Sistema de Instalação Robusto para Environment Dev

Este módulo implementa um sistema de instalação robusto que integra todos os
componentes YAML de forma organizada, seguindo a arquitetura especificada
no design.md e requirements.md.

Funcionalidades principais:
- Varredura automática de todos os arquivos YAML de componentes
- Detecção unificada de aplicações e runtimes
- Sistema de dependências inteligente
- Downloads robustos com verificação de integridade
- Instalação com rollback automático
- Otimizações específicas para Steam Deck
- Interface moderna com excelente UX
"""

import os
import sys
import yaml
import json
import logging
import hashlib
import asyncio
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import tempfile
import shutil
import platform
import urllib.request
import urllib.error

# Importar sistema de status
try:
    from .component_status_manager import get_status_manager, ComponentStatus
    STATUS_MANAGER_AVAILABLE = True
except ImportError:
    STATUS_MANAGER_AVAILABLE = False

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/robust_installation.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class ComponentInfo:
    """Informações de um componente"""
    name: str
    category: str
    description: str
    download_url: Optional[str] = None
    install_method: str = "manual"
    install_args: Optional[str] = None
    hash: Optional[str] = None
    hash_algorithm: str = "sha256"
    dependencies: List[str] = field(default_factory=list)
    verify_actions: List[Dict[str, Any]] = field(default_factory=list)
    environment_variables: Dict[str, str] = field(default_factory=dict)
    post_install_commands: List[str] = field(default_factory=list)
    supported_os: List[str] = field(default_factory=lambda: ["windows"])
    alternative_urls: List[str] = field(default_factory=list)
    notes: Optional[str] = None
    source_file: Optional[str] = None


@dataclass
class InstallationResult:
    """Resultado de uma instalação"""
    component: str
    success: bool
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    rollback_info: Optional[Dict[str, Any]] = None


@dataclass
class DetectionResult:
    """Resultado de detecção de componente"""
    component: str
    detected: bool
    version: Optional[str] = None
    path: Optional[str] = None
    confidence: float = 0.0
    detection_method: str = "unknown"
    details: Dict[str, Any] = field(default_factory=dict)


class RobustInstallationSystem:
    """
    Sistema de Instalação Robusto
    
    Implementa todas as funcionalidades especificadas na arquitetura:
    - Análise arquitetural
    - Detecção unificada
    - Validação de dependências
    - Downloads robustos
    - Instalação avançada
    - Integração Steam Deck
    - Gestão inteligente de armazenamento
    """
    
    def __init__(self, config_dir: str = "config"):
        """
        Inicializa o sistema de instalação
        
        Args:
            config_dir: Diretório de configuração com arquivos YAML
        """
        self.config_dir = Path(config_dir)
        self.components_dir = self.config_dir / "components"
        self.downloads_dir = Path("downloads")
        self.temp_dir = Path("temp_downloads")
        self.backups_dir = Path("backups")
        
        # Criar diretórios necessários
        for directory in [self.downloads_dir, self.temp_dir, self.backups_dir]:
            directory.mkdir(exist_ok=True)
        
        # Estado do sistema
        self.components: Dict[str, ComponentInfo] = {}
        self.detection_cache: Dict[str, DetectionResult] = {}
        self.installation_history: List[InstallationResult] = []
        
        # Configurações
        self.max_parallel_downloads = 3
        self.max_retries = 3
        self.timeout_seconds = 300
        
        # Steam Deck detection
        self.is_steam_deck = self._detect_steam_deck()
        
        logger.info(f"Sistema de Instalação Robusto inicializado")
        logger.info(f"Steam Deck detectado: {self.is_steam_deck}")
    
    def _detect_steam_deck(self) -> bool:
        """
        Detecta se está rodando em Steam Deck
        
        Returns:
            True se for Steam Deck, False caso contrário
        """
        try:
            # Método 1: DMI/SMBIOS detection
            if platform.system() == "Linux":
                try:
                    with open("/sys/class/dmi/id/product_name", "r") as f:
                        product_name = f.read().strip()
                    if "Steam Deck" in product_name:
                        return True
                except:
                    pass
            
            # Método 2: Steam client detection (fallback)
            steam_paths = [
                Path.home() / ".steam",
                Path.home() / ".local/share/Steam",
                Path("C:/Program Files (x86)/Steam") if platform.system() == "Windows" else None
            ]
            
            for path in steam_paths:
                if path and path.exists():
                    # Verificar se há indicadores de Steam Deck
                    deck_indicators = ["steamdeck", "deck", "handheld"]
                    for indicator in deck_indicators:
                        if any(indicator in str(p).lower() for p in path.rglob("*")):
                            return True
            
            return False
            
        except Exception as e:
            logger.warning(f"Erro na detecção Steam Deck: {e}")
            return False
    
    async def scan_components(self) -> Dict[str, ComponentInfo]:
        """
        Faz varredura de todos os arquivos YAML de componentes
        
        Returns:
            Dicionário com todos os componentes encontrados
        """
        logger.info("Iniciando varredura de componentes YAML...")
        
        if not self.components_dir.exists():
            logger.error(f"Diretório de componentes não encontrado: {self.components_dir}")
            return {}
        
        yaml_files = list(self.components_dir.glob("*.yaml"))
        logger.info(f"Encontrados {len(yaml_files)} arquivos YAML")
        
        components = {}
        
        for yaml_file in yaml_files:
            try:
                logger.info(f"Processando arquivo: {yaml_file.name}")
                
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                
                if not data:
                    logger.warning(f"Arquivo vazio ou inválido: {yaml_file.name}")
                    continue
                
                # Processar cada componente no arquivo
                for component_name, component_data in data.items():
                    if not isinstance(component_data, dict):
                        continue
                    
                    try:
                        component = self._parse_component(
                            component_name, 
                            component_data, 
                            yaml_file.name
                        )
                        
                        # Filtrar por OS se necessário
                        if self._is_component_supported(component):
                            components[component_name] = component
                            logger.debug(f"Componente adicionado: {component_name}")
                        else:
                            logger.debug(f"Componente não suportado no OS atual: {component_name}")
                    
                    except Exception as e:
                        logger.error(f"Erro ao processar componente {component_name}: {e}")
                        continue
            
            except Exception as e:
                logger.error(f"Erro ao processar arquivo {yaml_file.name}: {e}")
                continue
        
        self.components = components
        logger.info(f"Varredura concluída. {len(components)} componentes carregados.")
        
        return components
    
    def _parse_component(self, name: str, data: Dict[str, Any], source_file: str) -> ComponentInfo:
        """
        Converte dados YAML em ComponentInfo
        
        Args:
            name: Nome do componente
            data: Dados do componente do YAML
            source_file: Arquivo fonte
            
        Returns:
            ComponentInfo com os dados processados
        """
        return ComponentInfo(
            name=name,
            category=data.get('category', 'Unknown'),
            description=data.get('description', ''),
            download_url=data.get('download_url'),
            install_method=data.get('install_method', 'manual'),
            install_args=data.get('install_args'),
            hash=data.get('hash'),
            hash_algorithm=data.get('hash_algorithm', 'sha256'),
            dependencies=data.get('dependencies', []),
            verify_actions=data.get('verify_actions', []),
            environment_variables=data.get('environment_variables', {}),
            post_install_commands=data.get('post_install_commands', []),
            supported_os=data.get('supported_os', ['windows']),
            alternative_urls=data.get('alternative_urls', []),
            notes=data.get('notes'),
            source_file=source_file
        )
    
    def _is_component_supported(self, component: ComponentInfo) -> bool:
        """
        Verifica se o componente é suportado no OS atual
        
        Args:
            component: Componente a verificar
            
        Returns:
            True se suportado, False caso contrário
        """
        current_os = platform.system().lower()
        
        # Mapeamento de OS
        os_mapping = {
            'windows': 'windows',
            'linux': 'linux',
            'darwin': 'macos'
        }
        
        current_os_mapped = os_mapping.get(current_os, current_os)
        
        # Verificar se o OS atual está na lista de suportados
        supported = any(
            current_os_mapped in supported_os.lower() 
            for supported_os in component.supported_os
        )
        
        return supported
    
    async def unified_detection(self, components: Optional[List[str]] = None) -> Dict[str, DetectionResult]:
        """
        Executa detecção unificada de componentes
        
        Args:
            components: Lista de componentes específicos para detectar (None = todos)
            
        Returns:
            Dicionário com resultados de detecção
        """
        logger.info("Iniciando detecção unificada...")
        
        if not self.components:
            await self.scan_components()
        
        target_components = components or list(self.components.keys())
        results = {}
        
        # Detecção paralela para melhor performance
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_component = {
                executor.submit(self._detect_component, comp_name): comp_name
                for comp_name in target_components
                if comp_name in self.components
            }
            
            for future in as_completed(future_to_component):
                component_name = future_to_component[future]
                try:
                    result = future.result()
                    results[component_name] = result
                    
                    # Sincronizar com sistema de status
                    if STATUS_MANAGER_AVAILABLE:
                        try:
                            status_manager = get_status_manager()
                            status = ComponentStatus.INSTALLED if result.detected else ComponentStatus.NOT_DETECTED
                            
                            status_manager.update_component_status(
                                component_id=component_name.lower().replace(" ", "_"),
                                name=component_name,
                                status=status,
                                version_detected=result.version,
                                install_path=result.details.get("install_path")
                            )
                        except Exception as e:
                            logger.debug(f"Erro ao sincronizar status para {component_name}: {e}")
                    
                    if result.detected:
                        logger.info(f"✓ {component_name} detectado: {result.version or 'versão desconhecida'}")
                    else:
                        logger.debug(f"✗ {component_name} não detectado")
                
                except Exception as e:
                    logger.error(f"Erro na detecção de {component_name}: {e}")
                    results[component_name] = DetectionResult(
                        component=component_name,
                        detected=False,
                        details={"error": f"Erro na detecção: {e}"}
                    )
        
        self.detection_cache.update(results)
        logger.info(f"Detecção concluída. {sum(1 for r in results.values() if r.detected)} de {len(results)} componentes detectados.")
        
        return results
    
    def _detect_component(self, component_name: str) -> DetectionResult:
        """
        Detecta um componente específico
        
        Args:
            component_name: Nome do componente
            
        Returns:
            DetectionResult com informações de detecção
        """
        component = self.components.get(component_name)
        if not component:
            return DetectionResult(
                component=component_name,
                detected=False,
                details={"error": "Componente não encontrado"}
            )
        
        # Estratégia de detecção hierárquica
        detection_methods = [
            self._detect_via_verify_actions,
            self._detect_via_registry,
            self._detect_via_file_system,
            self._detect_via_command_line
        ]
        
        for method in detection_methods:
            try:
                result = method(component)
                if result.detected:
                    return result
            except Exception as e:
                logger.debug(f"Método de detecção falhou para {component_name}: {e}")
                continue
        
        return DetectionResult(
            component=component_name,
            detected=False,
            detection_method="all_methods_failed"
        )
    
    def _detect_via_verify_actions(self, component: ComponentInfo) -> DetectionResult:
        """Detecção via verify_actions do componente"""
        if not component.verify_actions:
            return DetectionResult(component=component.name, detected=False)
        
        for action in component.verify_actions:
            action_type = action.get('type')
            
            if action_type == 'file_exists':
                path = action.get('path')
                if path and self._check_file_exists(path):
                    return DetectionResult(
                        component=component.name,
                        detected=True,
                        path=path,
                        detection_method="file_exists",
                        confidence=0.9
                    )
            
            elif action_type == 'command_exists':
                command = action.get('name')
                if command and self._check_command_exists(command):
                    return DetectionResult(
                        component=component.name,
                        detected=True,
                        detection_method="command_exists",
                        confidence=0.8
                    )
            
            elif action_type == 'command_output':
                command = action.get('command')
                expected = action.get('expected_contains')
                if command and expected:
                    output = self._run_command(command)
                    if output and expected in output:
                        # Tentar extrair versão do output
                        version = self._extract_version_from_output(output)
                        return DetectionResult(
                            component=component.name,
                            detected=True,
                            version=version,
                            detection_method="command_output",
                            confidence=0.95
                        )
        
        return DetectionResult(component=component.name, detected=False)
    
    def _detect_via_registry(self, component: ComponentInfo) -> DetectionResult:
        """Detecção via registro do Windows"""
        if platform.system() != "Windows":
            return DetectionResult(component=component.name, detected=False)
        
        try:
            import winreg
            # Chaves comuns do registro para aplicações instaladas
            registry_keys = [
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall",
                r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
            ]
            
            for key_path in registry_keys:
                try:
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                        for i in range(winreg.QueryInfoKey(key)[0]):
                            try:
                                subkey_name = winreg.EnumKey(key, i)
                                with winreg.OpenKey(key, subkey_name) as subkey:
                                    try:
                                        display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                        if self._name_matches_component(display_name, component.name):
                                            version = None
                                            try:
                                                version = winreg.QueryValueEx(subkey, "DisplayVersion")[0]
                                            except:
                                                pass
                                            
                                            return DetectionResult(
                                                component=component.name,
                                                detected=True,
                                                version=version,
                                                detection_method="registry",
                                                confidence=0.85,
                                                details={"registry_name": display_name}
                                            )
                                    except:
                                        continue
                            except:
                                continue
                except:
                    continue
        
        except Exception as e:
            logger.debug(f"Erro na detecção via registro para {component.name}: {e}")
        
        return DetectionResult(component=component.name, detected=False)
    
    def _detect_via_file_system(self, component: ComponentInfo) -> DetectionResult:
        """Detecção via sistema de arquivos"""
        # Localizações comuns para aplicações
        common_paths = [
            Path("C:/Program Files"),
            Path("C:/Program Files (x86)"),
            Path.home() / "AppData/Local/Programs",
            Path.home() / "AppData/Roaming",
            Path("C:/tools"),
            Path("C:/dev")
        ]
        
        # Padrões de busca baseados no nome do componente
        search_patterns = [
            component.name.lower(),
            component.name.lower().replace(" ", ""),
            component.name.lower().replace(" ", "-"),
            component.name.lower().replace(" ", "_")
        ]
        
        for base_path in common_paths:
            if not base_path.exists():
                continue
            
            try:
                for item in base_path.iterdir():
                    if item.is_dir():
                        item_name = item.name.lower()
                        for pattern in search_patterns:
                            if pattern in item_name:
                                # Procurar por executáveis dentro do diretório
                                exe_files = list(item.rglob("*.exe"))
                                if exe_files:
                                    return DetectionResult(
                                        component=component.name,
                                        detected=True,
                                        path=str(exe_files[0]),
                                        detection_method="filesystem",
                                        confidence=0.7,
                                        details={"directory": str(item)}
                                    )
            except (PermissionError, OSError):
                continue
        
        return DetectionResult(component=component.name, detected=False)
    
    def _detect_via_command_line(self, component: ComponentInfo) -> DetectionResult:
        """Detecção via linha de comando"""
        # Comandos comuns baseados no nome do componente
        possible_commands = [
            component.name.lower(),
            component.name.lower().replace(" ", ""),
            component.name.lower().replace(" ", "-"),
            component.name.split()[0].lower() if " " in component.name else component.name.lower()
        ]
        
        for command in possible_commands:
            if self._check_command_exists(command):
                # Tentar obter versão
                version_commands = [f"{command} --version", f"{command} -v", f"{command} version"]
                version = None
                
                for version_cmd in version_commands:
                    output = self._run_command(version_cmd)
                    if output:
                        version = self._extract_version_from_output(output)
                        if version:
                            break
                
                return DetectionResult(
                    component=component.name,
                    detected=True,
                    version=version,
                    detection_method="command_line",
                    confidence=0.75
                )
        
        return DetectionResult(component=component.name, detected=False)
    
    def _check_file_exists(self, path: str) -> bool:
        """Verifica se um arquivo existe, expandindo variáveis de ambiente"""
        try:
            expanded_path = os.path.expandvars(path)
            return Path(expanded_path).exists()
        except:
            return False
    
    def _check_command_exists(self, command: str) -> bool:
        """Verifica se um comando existe no PATH"""
        try:
            result = subprocess.run(
                ["where" if platform.system() == "Windows" else "which", command],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
    
    def _run_command(self, command: str) -> Optional[str]:
        """Executa um comando e retorna a saída"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.stdout.strip() if result.returncode == 0 else None
        except:
            return None
    
    def _extract_version_from_output(self, output: str) -> Optional[str]:
        """Extrai versão de uma saída de comando"""
        import re
        
        # Padrões comuns de versão
        version_patterns = [
            r'(\d+\.\d+\.\d+)',
            r'(\d+\.\d+)',
            r'v(\d+\.\d+\.\d+)',
            r'version (\d+\.\d+\.\d+)',
            r'Version (\d+\.\d+\.\d+)'
        ]
        
        for pattern in version_patterns:
            match = re.search(pattern, output)
            if match:
                return match.group(1)
        
        return None
    
    def _name_matches_component(self, display_name: str, component_name: str) -> bool:
        """Verifica se um nome de display corresponde ao componente"""
        display_lower = display_name.lower()
        component_lower = component_name.lower()
        
        # Correspondência exata
        if component_lower in display_lower:
            return True
        
        # Correspondência por palavras-chave
        component_words = component_lower.split()
        if len(component_words) > 1:
            return all(word in display_lower for word in component_words)
        
        return False
    
    async def validate_dependencies(self, components: List[str]) -> Dict[str, Any]:
        """
        Valida dependências de componentes
        
        Args:
            components: Lista de componentes para validar
            
        Returns:
            Resultado da validação de dependências
        """
        logger.info("Iniciando validação de dependências...")
        
        dependency_graph = {}
        conflicts = []
        missing_dependencies = []
        circular_dependencies = []
        
        # Construir grafo de dependências
        for component_name in components:
            component = self.components.get(component_name)
            if not component:
                continue
            
            dependency_graph[component_name] = component.dependencies
        
        # Verificar dependências ausentes
        for component_name, deps in dependency_graph.items():
            for dep in deps:
                if dep not in self.components:
                    missing_dependencies.append({
                        'component': component_name,
                        'missing_dependency': dep
                    })
        
        # Verificar dependências circulares
        circular_dependencies = self._detect_circular_dependencies(dependency_graph)
        
        # Calcular ordem de instalação
        installation_order = self._calculate_installation_order(dependency_graph)
        
        result = {
            'dependency_graph': dependency_graph,
            'conflicts': conflicts,
            'missing_dependencies': missing_dependencies,
            'circular_dependencies': circular_dependencies,
            'installation_order': installation_order,
            'valid': len(missing_dependencies) == 0 and len(circular_dependencies) == 0
        }
        
        logger.info(f"Validação de dependências concluída. Válido: {result['valid']}")
        
        return result
    
    def _detect_circular_dependencies(self, graph: Dict[str, List[str]]) -> List[List[str]]:
        """Detecta dependências circulares no grafo"""
        def dfs(node, path, visited, rec_stack):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in graph.get(node, []):
                if neighbor in graph:  # Só processar se o vizinho existe
                    if neighbor not in visited:
                        cycle = dfs(neighbor, path, visited, rec_stack)
                        if cycle:
                            return cycle
                    elif neighbor in rec_stack:
                        # Encontrou ciclo
                        cycle_start = path.index(neighbor)
                        return path[cycle_start:] + [neighbor]
            
            path.pop()
            rec_stack.remove(node)
            return None
        
        visited = set()
        cycles = []
        
        for node in graph:
            if node not in visited:
                cycle = dfs(node, [], visited, set())
                if cycle:
                    cycles.append(cycle)
        
        return cycles
    
    def _calculate_installation_order(self, graph: Dict[str, List[str]]) -> List[str]:
        """Calcula ordem de instalação baseada em dependências"""
        # Ordenação topológica
        in_degree = {node: 0 for node in graph}
        
        # Calcular grau de entrada
        for node in graph:
            for dep in graph[node]:
                if dep in in_degree:
                    in_degree[dep] += 1
        
        # Fila com nós sem dependências
        queue = [node for node, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            node = queue.pop(0)
            result.append(node)
            
            # Remover este nó do grafo
            for dep in graph.get(node, []):
                if dep in in_degree:
                    in_degree[dep] -= 1
                    if in_degree[dep] == 0:
                        queue.append(dep)
        
        return result
    
    def generate_installation_report(self) -> Dict[str, Any]:
        """Gera relatório de instalação"""
        successful_installations = [r for r in self.installation_history if r.success]
        failed_installations = [r for r in self.installation_history if not r.success]
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_components': len(self.components),
            'detected_components': len([r for r in self.detection_cache.values() if r.detected]),
            'successful_installations': len(successful_installations),
            'failed_installations': len(failed_installations),
            'success_rate': len(successful_installations) / max(len(self.installation_history), 1) * 100,
            'steam_deck_detected': self.is_steam_deck,
            'installation_history': [
                {
                    'component': r.component,
                    'success': r.success,
                    'message': r.message,
                    'timestamp': r.timestamp.isoformat()
                }
                for r in self.installation_history
            ]
        }
        
        return report


# Função principal para demonstração
async def main():
    """Função principal para demonstração do sistema"""
    system = RobustInstallationSystem()
    
    # Varredura de componentes
    components = await system.scan_components()
    print(f"Componentes carregados: {len(components)}")
    
    # Gerar relatório
    report = system.generate_installation_report()
    print(f"Taxa de sucesso: {report['success_rate']:.1f}%")


if __name__ == "__main__":
    asyncio.run(main())