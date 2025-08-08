# Environment Development Tools Package
# Este arquivo torna o diretório env_dev um pacote Python válido

__version__ = "1.0.0"
__author__ = "Environment Development Team"
__description__ = "Ferramentas avançadas para gerenciamento de ambiente de desenvolvimento"

# Importações principais do pacote
try:
    from .core.detection_engine import DetectionEngine, DetectedApplication
    from .core.installer import Installer
    from .core.suggestion_service import SuggestionService
    from .core.component_matcher import ComponentMatcher
    from .core.intelligent_suggestions import IntelligentSuggestionEngine
    from .core.component_metadata_manager import ComponentMetadataManager
except ImportError as e:
    # Fallback para quando os módulos não estão disponíveis
    print(f"Aviso: Alguns módulos não puderam ser importados: {e}")

__all__ = [
    'DetectionEngine',
    'DetectedApplication', 
    'Installer',
    'SuggestionService',
    'ComponentMatcher',
    'IntelligentSuggestionEngine',
    'ComponentMetadataManager'
]