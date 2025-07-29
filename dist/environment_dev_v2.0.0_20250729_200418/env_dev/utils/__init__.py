"""
Módulo de utilitários para o Environment Dev

Este pacote contém funções utilitárias para o instalador do Environment Dev,
incluindo download de arquivos, cálculo de hash, detecção de display,
gerenciamento de variáveis de ambiente e logging personalizado.

Contém funções auxiliares utilizadas por diversos componentes do projeto.
"""

# Expõe as funções principais para facilitar a importação
from env_dev.utils.downloader import download_file
from env_dev.utils.hash_utils import get_file_hash, verify_file_hash
from env_dev.utils.network import test_internet_connection
from env_dev.utils.display_utils import get_display_type
from env_dev.utils.env_manager import add_to_path, get_path, is_admin
from env_dev.utils.log_manager import setup_logging, SUCCESS

# Importa funções de gestão de erros
from env_dev.utils.error_handler import (
    EnvDevError, ErrorSeverity, ErrorCategory,
    handle_exception, try_recover, handle_errors,
    get_error_context,
    file_error, network_error, permission_error,
    config_error, dependency_error, installation_error
)

# Importa funções de gestão de mirrors
from env_dev.utils.mirror_manager import (
    find_best_mirror, generate_alternative_urls,
    download_with_mirror_fallback, register_mirror,
    remove_mirror, load_mirrors_config, save_mirrors_config
)

# Importa funções avançadas de download
from env_dev.utils.downloader import (
    download_with_cache, download_files_batch,
    verify_url_status, pre_validate_urls
)

# Exporta constantes úteis
from env_dev.utils.display_utils import (
    DISPLAY_TYPE_LCD,
    DISPLAY_TYPE_OLED10,
    DISPLAY_TYPE_OLED11,
    DISPLAY_TYPE_UNKNOWN
)

__all__ = [
    # Funções de download e hash
    'download_file',
    'get_file_hash',
    'verify_file_hash',
    
    # Funções de rede
    'test_internet_connection',
    
    # Funções de detecção de hardware
    'get_display_type',
    
    # Funções de gerenciamento de ambiente
    'add_to_path',
    'get_path',
    'is_admin',
    
    # Funções de logging
    'setup_logging',
    'SUCCESS',
    
    # Constantes
    'DISPLAY_TYPE_LCD',
    'DISPLAY_TYPE_OLED10',
    'DISPLAY_TYPE_OLED11',
    'DISPLAY_TYPE_UNKNOWN',
    
    # Gestão de erros
    'EnvDevError',
    'ErrorSeverity',
    'ErrorCategory',
    'handle_exception',
    'try_recover',
    'handle_errors',
    'get_error_context',
    'file_error',
    'network_error',
    'permission_error',
    'config_error',
    'dependency_error',
    'installation_error',
    
    # Validação YAML
    'yaml_validator',
    'yaml_fix_tool',
    
    # Gestão de mirrors
    'find_best_mirror',
    'generate_alternative_urls',
    'download_with_mirror_fallback',
    'register_mirror',
    'remove_mirror',
    'load_mirrors_config',
    'save_mirrors_config',
    
    # Funções avançadas de download
    'download_with_cache',
    'download_files_batch',
    'verify_url_status',
    'pre_validate_urls',
] 