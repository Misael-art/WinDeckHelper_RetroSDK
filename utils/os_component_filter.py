#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sistema de filtros de componentes por sistema operacional
Evita falsos positivos em componentes específicos de plataforma
"""

import platform
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class OSComponentFilter:
    """Filtra componentes baseado no sistema operacional"""
    
    def __init__(self):
        self.current_os = platform.system().lower()
        
        # Componentes específicos por SO
        self.os_specific_components = {
            'linux': [
                'KDE Plasma Mobile Info',
                'Heroic Games Launcher (Flatpak)',
                'Lutris (Flatpak)',
                'RetroArch (Flatpak)',
                'PCSX2 (Flatpak)',
                'SteamDeck Windows Drivers'
            ],
            'windows': [
                'HardLinkShellExt_X64',
                'Revo Uninstaller',
                'PowerShell Preview'
            ],
            'darwin': [
                # Componentes específicos do macOS
            ]
        }
        
        # Componentes que nunca devem ser detectados como instalados
        self.never_installable = [
            'ProtonDB Notes',
            'KDE Plasma Mobile Info',  # No Windows
        ]
        
        # Categorias específicas por SO
        self.os_specific_categories = {
            'linux': [
                'Game Launchers (Steam Deck)',
                'Emulators (Steam Deck)',
                'Drivers'
            ],
            'windows': [
                'Optimization (Windows)',
                'Modding Tools (Windows)',
                'Backup & Sync (Windows)',
                'Audio Tools (Windows)',
                'Capture & Streaming (Windows)',
                'Network Tools (Windows)',
                'System Optimization (Windows)'
            ]
        }
    
    def should_check_component(self, component_name: str) -> bool:
        """Verifica se um componente deve ser verificado no SO atual"""
        
        # Componentes que nunca devem ser detectados
        if component_name in self.never_installable:
            if self.current_os == 'windows' and 'KDE' in component_name:
                return False
            if 'ProtonDB' in component_name:
                return False
        
        # Verifica componentes específicos do Linux no Windows
        if self.current_os == 'windows':
            linux_components = self.os_specific_components.get('linux', [])
            if component_name in linux_components:
                logger.info(f"Componente '{component_name}' é específico do Linux, pulando no Windows")
                return False
        
        # Verifica componentes específicos do Windows no Linux
        elif self.current_os == 'linux':
            windows_components = self.os_specific_components.get('windows', [])
            if component_name in windows_components:
                logger.info(f"Componente '{component_name}' é específico do Windows, pulando no Linux")
                return False
        
        return True
    
    def should_include_component(self, component_name: str, component_data: Dict[str, Any]) -> bool:
        """Determina se um componente deve ser incluído baseado no SO atual"""
        
        # Primeiro verifica se o componente deve ser verificado
        if not self.should_check_component(component_name):
            return False
        
        # Verifica se a categoria é específica de outro SO
        component_category = component_data.get('category', '')
        for os_name, categories in self.os_specific_categories.items():
            if component_category in categories and os_name != self.current_os:
                logger.info(f"Componente '{component_name}' da categoria '{component_category}' é específico do {os_name}, pulando no {self.current_os}")
                return False
        
        # Verifica filtros de OS específicos no componente
        os_filter = component_data.get('os_filter', {})
        if os_filter:
            # Se tem filtro de OS, verifica se o SO atual está incluído
            return self.current_os in os_filter and os_filter[self.current_os]
        
        # Verifica supported_os (formato antigo)
        supported_os = component_data.get('supported_os', [])
        if supported_os:
            return self.current_os in supported_os
        
        # Se não tem filtro específico, inclui por padrão
        return True
    
    def filter_components_data(self, components_data: Dict[str, Any]) -> Dict[str, Any]:
        """Filtra dados de componentes baseado no SO atual"""
        filtered_data = {}
        
        for component_name, component_data in components_data.items():
            if self.should_include_component(component_name, component_data):
                filtered_data[component_name] = component_data
        
        return filtered_data
    
    def get_os_info(self) -> Dict[str, str]:
        """Retorna informações do sistema operacional"""
        return {
            'system': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor()
        }

# Instância global do filtro
os_filter = OSComponentFilter()
