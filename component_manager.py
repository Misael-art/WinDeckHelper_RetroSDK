import os
import yaml
import logging
import platform
from typing import Dict, List, Any, Optional, Set, Tuple
from pathlib import Path

from env_dev.utils.error_handler import (
    EnvDevError, ErrorCategory, ErrorSeverity,
    config_error, dependency_error, handle_exception
)
from env_dev.utils.dependency_resolver import DependencyResolver, CircularDependencyError

# Tipos de componentes suportados
COMPONENT_TYPES = ['application', 'utility', 'developer_tool', 'system_component']

# Configuração do logger
logger = logging.getLogger(__name__)

class ComponentManager:
    """
    Gerencia o carregamento, validação e processamento de componentes.
    """
    
    def __init__(self, yaml_file_path: str):
        """
        Inicializa o gerenciador de componentes com o caminho para o arquivo YAML.
        
        Args:
            yaml_file_path: Caminho para o arquivo YAML com definições de componentes
        """
        self.yaml_file_path = os.path.abspath(yaml_file_path)
        self.components = {}
        self.dependencies_map = {}
        self.installation_order = []
        self._load_components()
    
    def _load_components(self):
        """Carrega componentes do arquivo YAML e valida sua estrutura."""
        try:
            if not os.path.exists(self.yaml_file_path):
                err = config_error(
                    f"Arquivo de componentes não encontrado: {self.yaml_file_path}",
                    severity=ErrorSeverity.CRITICAL
                )
                err.log()
                raise FileNotFoundError(f"Arquivo YAML não encontrado: {self.yaml_file_path}")
            
            logger.info(f"Carregando componentes de: {self.yaml_file_path}")
            with open(self.yaml_file_path, 'r', encoding='utf-8') as file:
                try:
                    data = yaml.safe_load(file)
                    if not data:
                        err = config_error(
                            f"Arquivo YAML vazio ou inválido: {self.yaml_file_path}",
                            severity=ErrorSeverity.CRITICAL
                        )
                        err.log()
                        raise ValueError(f"Arquivo YAML vazio ou inválido: {self.yaml_file_path}")
                except yaml.YAMLError as e:
                    err = config_error(
                        f"Erro de sintaxe no arquivo YAML: {e}",
                        severity=ErrorSeverity.CRITICAL,
                        original_error=e
                    )
                    err.log()
                    raise ValueError(f"Erro ao analisar arquivo YAML: {e}")
            
            # Verifica se a estrutura do YAML contém o campo 'components'
            if 'components' not in data:
                err = config_error(
                    "Estrutura YAML inválida: campo 'components' não encontrado",
                    severity=ErrorSeverity.CRITICAL
                )
                err.log()
                raise ValueError("Estrutura YAML inválida: campo 'components' não encontrado")
            
            # Validação e processamento de componentes
            self.components = {}
            validation_errors = []
            
            for name, component_data in data['components'].items():
                try:
                    if self._validate_component(name, component_data):
                        self.components[name] = component_data
                    else:
                        validation_errors.append(name)
                except Exception as e:
                    logger.error(f"Erro ao validar componente '{name}': {e}")
                    validation_errors.append(name)
            
            if validation_errors:
                err_msg = f"Erros de validação para os seguintes componentes: {', '.join(validation_errors)}"
                err = config_error(
                    err_msg,
                    severity=ErrorSeverity.WARNING
                )
                err.log()
                logger.warning(err_msg)
            
            # Constrói o mapa de dependências e ordena os componentes para instalação
            self._build_dependencies_map()
            self._compute_installation_order()
            
            logger.info(f"Componentes carregados com sucesso: {len(self.components)} componentes válidos")
            
        except Exception as e:
            err = handle_exception(
                e,
                message="Erro ao carregar configuração de componentes",
                category=ErrorCategory.CONFIG,
                severity=ErrorSeverity.CRITICAL
            )
            err.log()
            raise
    
    def _validate_component(self, name: str, component_data: Dict) -> bool:
        """
        Valida a estrutura e dados de um componente.
        
        Args:
            name: Nome do componente
            component_data: Dados do componente do arquivo YAML
            
        Returns:
            True se o componente for válido, False caso contrário
        """
        # Lista de campos obrigatórios
        required_fields = ['name', 'type', 'description', 'platforms']
        
        # Verifica campos obrigatórios
        for field in required_fields:
            if field not in component_data:
                logger.error(f"Componente '{name}' não possui o campo obrigatório '{field}'")
                return False
        
        # Verifica se o tipo é válido
        if component_data['type'] not in COMPONENT_TYPES:
            logger.error(f"Componente '{name}' tem tipo inválido: '{component_data['type']}'. "
                         f"Tipos válidos: {', '.join(COMPONENT_TYPES)}")
            return False
        
        # Verifica se o nome no YAML corresponde à chave
        if component_data['name'] != name:
            logger.warning(f"Componente com chave '{name}' tem nome diferente no YAML: '{component_data['name']}'. "
                          f"Usando chave '{name}' como nome oficial.")
            # Atualiza o nome para garantir consistência
            component_data['name'] = name
        
        # Verifica se as plataformas são válidas
        valid_platforms = ['windows', 'linux', 'macos', 'all']
        platforms = component_data['platforms']
        if not isinstance(platforms, list):
            logger.error(f"Campo 'platforms' para '{name}' deve ser uma lista")
            return False
        
        for platform_entry in platforms:
            if not isinstance(platform_entry, str) or platform_entry.lower() not in valid_platforms:
                logger.error(f"Plataforma inválida para '{name}': '{platform_entry}'")
                return False
        
        # Verifica se a URL de download existe para cada plataforma suportada
        if 'download' in component_data:
            for platform_name, download_info in component_data['download'].items():
                if platform_name not in valid_platforms:
                    logger.warning(f"Plataforma de download desconhecida para '{name}': '{platform_name}'")
                if not isinstance(download_info, dict) or 'url' not in download_info:
                    logger.error(f"Informação de download inválida para '{name}' na plataforma '{platform_name}'")
                    return False
        
        # Verifica dependências se existirem
        if 'dependencies' in component_data:
            if not isinstance(component_data['dependencies'], list):
                logger.error(f"Campo 'dependencies' para '{name}' deve ser uma lista")
                return False
        
        # Verifica instruções de instalação personalizada
        if 'custom_install' in component_data and not isinstance(component_data['custom_install'], dict):
            logger.error(f"Campo 'custom_install' para '{name}' deve ser um objeto")
            return False
        
        # Verifica se o componente tem configurações específicas do sistema
        self._validate_platform_specific_config(name, component_data)
        
        return True
    
    def _validate_platform_specific_config(self, name: str, component_data: Dict):
        """Valida configurações específicas da plataforma atual."""
        current_platform = self._get_current_platform()
        
        # Verifica download para plataforma atual
        if 'download' in component_data:
            platform_downloads = component_data['download']
            if current_platform not in platform_downloads and 'all' not in platform_downloads:
                logger.warning(f"Componente '{name}' não possui configuração de download para a plataforma atual ({current_platform})")
        
        # Verifica especificações da plataforma atual
        if current_platform not in component_data.get('platforms', []) and 'all' not in component_data.get('platforms', []):
            logger.warning(f"Componente '{name}' não suporta a plataforma atual ({current_platform})")
    
    def _get_current_platform(self) -> str:
        """Retorna a plataforma atual em formato compatível com o YAML."""
        system = platform.system().lower()
        if system == 'darwin':
            return 'macos'
        elif system == 'windows':
            return 'windows'
        elif system == 'linux':
            return 'linux'
        return 'unknown'
    
    def _build_dependencies_map(self):
        """Constrói um mapa de dependências entre componentes."""
        self.dependencies_map = {}
        
        for name, component in self.components.items():
            self.dependencies_map[name] = component.get('dependencies', [])
            
            # Verifica dependências inexistentes
            for dependency in self.dependencies_map[name]:
                if dependency not in self.components:
                    logger.warning(f"Componente '{name}' depende de '{dependency}' que não está definido no YAML")
                    # Adiciona o erro ao log de erros globais
                    err = dependency_error(
                        f"Dependência indefinida: '{name}' requer '{dependency}' que não está no arquivo de componentes",
                        severity=ErrorSeverity.WARNING
                    )
                    err.log()
    
    def _compute_installation_order(self):
        """
        Computa a ordem de instalação dos componentes com base nas dependências.
        Usa ordenação topológica para garantir que dependências sejam instaladas primeiro.
        """
        # Inicializa estruturas para ordenação topológica
        visited = set()
        temp_visited = set()
        order = []
        
        def visit(component_name):
            """Função recursiva para ordenação topológica."""
            if component_name in temp_visited:
                # Detecta dependência circular
                cycle = self._find_dependency_cycle(component_name)
                err = dependency_error(
                    f"Dependência circular detectada entre componentes: {' -> '.join(cycle)}",
                    severity=ErrorSeverity.ERROR
                )
                err.log()
                logger.error(f"Dependência circular detectada: {' -> '.join(cycle)}")
                # Trata a dependência circular como se não existisse para permitir a continuação
                return
            
            if component_name not in visited:
                temp_visited.add(component_name)
                
                # Visita dependências primeiro
                for dependency in self.dependencies_map.get(component_name, []):
                    if dependency in self.components:  # Só considera dependências válidas
                        visit(dependency)
                
                # Após visitar todas as dependências, adiciona à ordem
                temp_visited.remove(component_name)
                visited.add(component_name)
                order.append(component_name)
        
        # Executa a ordenação para todos os componentes
        for component_name in self.components:
            if component_name not in visited:
                visit(component_name)
        
        self.installation_order = order
        logger.info(f"Ordem de instalação computada: {', '.join(order)}")
    
    def _find_dependency_cycle(self, start_component: str) -> List[str]:
        """
        Encontra e retorna o ciclo de dependência que começa com o componente informado.
        Usado para diagnóstico de dependências circulares.
        
        Args:
            start_component: Componente inicial do ciclo
            
        Returns:
            Lista de componentes que formam o ciclo
        """
        visited = set()
        path = [start_component]
        current = start_component
        
        while True:
            visited.add(current)
            
            # Procura o próximo componente no ciclo
            for dependency in self.dependencies_map.get(current, []):
                if dependency == start_component:
                    # Ciclo encontrado
                    path.append(start_component)
                    return path
                
                if dependency not in visited and dependency in self.components:
                    current = dependency
                    path.append(current)
                    break
            else:
                # Se não encontrar próximo componente válido, remove o atual e retrocede
                if len(path) > 1:
                    path.pop()
                    current = path[-1]
                else:
                    # Se não foi possível encontrar o ciclo completo
                    return [start_component, "???", start_component]
    
    def get_component(self, name: str) -> Optional[Dict]:
        """
        Retorna os dados de um componente pelo nome.
        
        Args:
            name: Nome do componente
            
        Returns:
            Dados do componente ou None se não encontrado
        """
        return self.components.get(name)
    
    def get_all_components(self) -> Dict[str, Dict]:
        """
        Retorna todos os componentes carregados.
        
        Returns:
            Dicionário de componentes
        """
        return self.components
    
    def get_components_by_type(self, component_type: str) -> Dict[str, Dict]:
        """
        Retorna componentes filtrados por tipo.
        
        Args:
            component_type: Tipo de componente para filtrar
            
        Returns:
            Dicionário de componentes do tipo especificado
        """
        if component_type not in COMPONENT_TYPES:
            logger.warning(f"Tipo de componente inválido: {component_type}")
            return {}
        
        return {name: data for name, data in self.components.items() 
                if data.get('type') == component_type}
    
    def get_components_for_platform(self, platform_name: str = None) -> Dict[str, Dict]:
        """
        Retorna componentes disponíveis para a plataforma especificada.
        Se nenhuma plataforma for especificada, usa a plataforma atual.
        
        Args:
            platform_name: Nome da plataforma ou None para usar a atual
            
        Returns:
            Dicionário de componentes para a plataforma
        """
        if platform_name is None:
            platform_name = self._get_current_platform()
        
        return {name: data for name, data in self.components.items() 
                if platform_name in data.get('platforms', []) or 'all' in data.get('platforms', [])}
    
    def get_installation_order(self) -> List[str]:
        """
        Retorna a ordem de instalação calculada para os componentes.
        
        Returns:
            Lista de nomes de componentes na ordem de instalação
        """
        return self.installation_order
    
    def get_component_dependencies(self, name: str) -> List[str]:
        """
        Retorna a lista de dependências diretas de um componente.
        
        Args:
            name: Nome do componente
            
        Returns:
            Lista de nomes das dependências diretas
        """
        if name not in self.components:
            logger.warning(f"Tentativa de obter dependências para componente inexistente: {name}")
            return []
        
        return self.dependencies_map.get(name, [])
    
    def get_all_dependencies(self, name: str) -> Set[str]:
        """
        Retorna todas as dependências (diretas e indiretas) de um componente.
        
        Args:
            name: Nome do componente
            
        Returns:
            Conjunto com todas as dependências
        """
        if name not in self.components:
            logger.warning(f"Tentativa de obter dependências para componente inexistente: {name}")
            return set()
        
        all_deps = set()
        to_visit = list(self.dependencies_map.get(name, []))
        
        while to_visit:
            current = to_visit.pop(0)
            if current not in all_deps and current in self.components:
                all_deps.add(current)
                # Adiciona as dependências deste componente à lista de visita
                to_visit.extend([dep for dep in self.dependencies_map.get(current, []) 
                                if dep not in all_deps])
        
        return all_deps
    
    def validate_download_information(self, name: str) -> Tuple[bool, Optional[str]]:
        """
        Valida se um componente tem informações de download válidas para a plataforma atual.
        
        Args:
            name: Nome do componente
            
        Returns:
            Tupla (é_válido, mensagem_erro)
        """
        component = self.get_component(name)
        if not component:
            return False, f"Componente não encontrado: {name}"
        
        current_platform = self._get_current_platform()
        valid_platforms = [current_platform, 'all']
        
        # Verifica se o componente suporta a plataforma atual
        if not any(platform in component.get('platforms', []) for platform in valid_platforms):
            return False, f"Componente '{name}' não suporta a plataforma {current_platform}"
        
        # Verifica informações de download
        if 'download' not in component:
            return False, f"Componente '{name}' não possui informações de download"
        
        # Procura URL para a plataforma atual ou 'all'
        download_info = None
        for platform in valid_platforms:
            if platform in component['download']:
                download_info = component['download'][platform]
                break
        
        if not download_info:
            return False, f"Não há informações de download para '{name}' na plataforma {current_platform}"
        
        if 'url' not in download_info:
            return False, f"URL de download não especificada para '{name}'"
        
        return True, None
    
    def get_download_url(self, name: str) -> Optional[str]:
        """
        Retorna a URL de download para um componente na plataforma atual.
        
        Args:
            name: Nome do componente
            
        Returns:
            URL de download ou None se não disponível
        """
        valid, error_msg = self.validate_download_information(name)
        if not valid:
            logger.error(error_msg)
            return None
        
        component = self.get_component(name)
        current_platform = self._get_current_platform()
        
        # Tenta obter URL para plataforma atual, senão tenta 'all'
        if current_platform in component['download']:
            return component['download'][current_platform]['url']
        else:
            return component['download']['all']['url']
    
    def get_hash_information(self, name: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Retorna informações de hash para verificação de download.
        
        Args:
            name: Nome do componente
            
        Returns:
            Tupla (hash_value, hash_algorithm) ou (None, None) se não disponível
        """
        valid, _ = self.validate_download_information(name)
        if not valid:
            return None, None
        
        component = self.get_component(name)
        current_platform = self._get_current_platform()
        
        # Determina qual plataforma usar para o download
        platform_key = current_platform if current_platform in component['download'] else 'all'
        download_info = component['download'][platform_key]
        
        hash_value = download_info.get('hash')
        hash_algorithm = download_info.get('hash_algorithm', 'sha256')
        
        return hash_value, hash_algorithm
    
    def reload_components(self):
        """Recarrega os componentes do arquivo YAML."""
        logger.info(f"Recarregando componentes de: {self.yaml_file_path}")
        self.components = {}
        self.dependencies_map = {}
        self.installation_order = []
        self._load_components()
    
    def save_components(self, filepath: Optional[str] = None):
        """
        Salva os componentes atuais de volta para um arquivo YAML.
        
        Args:
            filepath: Caminho para salvar o arquivo ou None para usar o caminho original
        """
        save_path = filepath or self.yaml_file_path
        
        try:
            # Cria o diretório de destino se não existir
            os.makedirs(os.path.dirname(os.path.abspath(save_path)), exist_ok=True)
            
            # Prepara a estrutura de dados para salvar
            data = {'components': self.components}
            
            # Salva o arquivo
            with open(save_path, 'w', encoding='utf-8') as file:
                yaml.dump(data, file, default_flow_style=False, sort_keys=False, allow_unicode=True)
            
            logger.info(f"Componentes salvos com sucesso em: {save_path}")
            return True
            
        except Exception as e:
            err = handle_exception(
                e,
                message=f"Erro ao salvar componentes em {save_path}",
                category=ErrorCategory.FILE,
                severity=ErrorSeverity.ERROR
            )
            err.log()
            return False

# Função auxiliar para inicializar o gerenciador a partir de um caminho de arquivo
def load_component_manager(yaml_file_path: str) -> ComponentManager:
    """
    Carrega e retorna um gerenciador de componentes inicializado.
    
    Args:
        yaml_file_path: Caminho para o arquivo YAML
        
    Returns:
        Gerenciador de componentes inicializado
    """
    logger.info(f"Iniciando carregamento do gerenciador de componentes de: {yaml_file_path}")
    return ComponentManager(yaml_file_path) 