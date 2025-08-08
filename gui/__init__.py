# -*- coding: utf-8 -*-
"""
GUI Package for Environment Dev Deep Evaluation
Interface gráfica moderna para o sistema de detecção e instalação.
"""

__version__ = "2.0.0"
__author__ = "Environment Dev Team"

# Importações principais da GUI
try:
    from .modern_frontend_manager import ModernFrontendManager
    from .components_viewer_gui import ComponentsViewerGUI
    from .app_gui import AppGUI
    
    __all__ = [
        'ModernFrontendManager',
        'ComponentsViewerGUI', 
        'AppGUI'
    ]
    
except ImportError as e:
    # Fallback se algum módulo não estiver disponível
    __all__ = []
    print(f"Warning: Some GUI modules not available: {e}")