# -*- coding: utf-8 -*-
"""
Wrapper de Compatibilidade para Installer
Mantém interface antiga mas usa nova arquitetura
"""

import logging
import os
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path

# Importa novo instalador
from .installer_v2 import modern_installer, InstallationResult, InstallerState
from utils.robust_verification import robust_verifier
from .error_handler import EnvDevError, ErrorSeverity, ErrorCategory

logger = logging.getLogger(__name__)

class InstallerWrapper:
    """
    Wrapper que mantém compatibilidade com a interface antiga
    mas usa a nova arquitetura internamente
    """
    
    def __init__(self):
        self.modern_installer = modern_installer
        self.progress_callback = None
        self.installation_results = {}
    
    def set_progress_callback(self, callback: Callable):
        """Define callback de progresso (compatibilidade)"""
        self.progress_callback = callback
        self.modern_installer.progress_callback = self._convert_progress_callback
    
    def _convert_progress_callback(self, progress_info):
        """Converte callback moderno para formato antigo"""
        if self.progress_callback:
            try:
                # Converte para formato esperado pela interface antiga
                old_format = {
                    'component': progress_info.component_name,
                    'step': progress_info.current_step,
                    'progress': progress_info.progress_percent,
                    'state': progress_info.state.value,
                    'details': progress_info.details
                }
                
                if progress_info.error:
                    old_format['error'] = progress_info.error
                
                self.progress_callback(old_format)
            except Exception as e:
                logger.error(f"Erro no callback de progresso: {e}")
    
    def install_component(self, component_data: Dict, **kwargs) -> bool:
        """
        Interface de compatibilidade para instalação de componente
        
        Args:
            component_data: Dados do componente
            **kwargs: Argumentos adicionais (ignorados)
        
        Returns:
            bool: True se instalação foi bem-sucedida
        """
        try:
            component_name = component_data.get('name', 'Unknown')
            logger.info(f"Instalando {component_name} via wrapper de compatibilidade")
            
            # Usa novo instalador
            result = self.modern_installer.install_component(component_data)
            
            # Armazena resultado
            self.installation_results[component_name] = result
            
            if result.success:
                logger.info(f"Instalação de {component_name} concluída com sucesso")
                return True
            else:
                logger.error(f"Falha na instalação de {component_name}: {result.message}")
                return False
                
        except Exception as e:
            logger.error(f"Erro na instalação via wrapper: {e}")
            return False
    
    def install_multiple_components(self, components: List[Dict], 
                                  parallel: bool = False) -> Dict[str, bool]:
        """
        Interface de compatibilidade para instalação múltipla
        
        Args:
            components: Lista de componentes
            parallel: Instalação paralela
        
        Returns:
            Dict com status de cada componente
        """
        try:
            # Usa novo instalador
            results = self.modern_installer.install_multiple_components(components, parallel)
            
            # Converte para formato antigo
            old_format = {}
            for name, result in results.items():
                old_format[name] = result.success
                self.installation_results[name] = result
            
            return old_format
            
        except Exception as e:
            logger.error(f"Erro na instalação múltipla via wrapper: {e}")
            return {comp.get('name', 'Unknown'): False for comp in components}
    
    def check_component_installed(self, component_data: Dict) -> bool:
        """
        Interface de compatibilidade para verificação de instalação
        
        Args:
            component_data: Dados do componente
        
        Returns:
            bool: True se componente está instalado
        """
        try:
            status = robust_verifier.get_comprehensive_status(component_data)
            return status['overall_status'] in ['fully_verified', 'partially_verified']
        except Exception as e:
            logger.error(f"Erro na verificação via wrapper: {e}")
            return False
    
    def get_installation_status(self, component_name: str) -> Dict[str, Any]:
        """
        Obtém status detalhado de uma instalação
        
        Args:
            component_name: Nome do componente
        
        Returns:
            Dict com status detalhado
        """
        if component_name in self.installation_results:
            result = self.installation_results[component_name]
            return {
                'success': result.success,
                'status': result.status.value,
                'message': result.message,
                'details': result.details,
                'installed_path': result.installed_path,
                'version': result.version
            }
        else:
            return {
                'success': False,
                'status': 'unknown',
                'message': 'Componente não encontrado nos resultados',
                'details': {},
                'installed_path': None,
                'version': None
            }
    
    def get_installation_summary(self) -> Dict[str, Any]:
        """
        Obtém resumo de todas as instalações
        
        Returns:
            Dict com resumo das instalações
        """
        return self.modern_installer.get_installation_summary(self.installation_results)
    
    def cleanup(self):
        """Limpa recursos (compatibilidade)"""
        try:
            self.modern_installer._cleanup_temp_files()
        except Exception as e:
            logger.error(f"Erro na limpeza via wrapper: {e}")

# Funções de compatibilidade global
_installer_wrapper = InstallerWrapper()

def install_component(component_data: Dict, progress_callback: Optional[Callable] = None, **kwargs) -> bool:
    """
    Função de compatibilidade global para instalação de componente
    
    Args:
        component_data: Dados do componente
        progress_callback: Callback de progresso
        **kwargs: Argumentos adicionais
    
    Returns:
        bool: True se instalação foi bem-sucedida
    """
    if progress_callback:
        _installer_wrapper.set_progress_callback(progress_callback)
    
    return _installer_wrapper.install_component(component_data, **kwargs)

def install_multiple_components(components: List[Dict], 
                              progress_callback: Optional[Callable] = None,
                              parallel: bool = False, **kwargs) -> Dict[str, bool]:
    """
    Função de compatibilidade global para instalação múltipla
    
    Args:
        components: Lista de componentes
        progress_callback: Callback de progresso
        parallel: Instalação paralela
        **kwargs: Argumentos adicionais
    
    Returns:
        Dict com status de cada componente
    """
    if progress_callback:
        _installer_wrapper.set_progress_callback(progress_callback)
    
    return _installer_wrapper.install_multiple_components(components, parallel)

def check_component_installed(component_data: Dict) -> bool:
    """
    Função de compatibilidade global para verificação
    
    Args:
        component_data: Dados do componente
    
    Returns:
        bool: True se componente está instalado
    """
    return _installer_wrapper.check_component_installed(component_data)

def get_installation_status(component_name: str) -> Dict[str, Any]:
    """
    Função de compatibilidade global para status
    
    Args:
        component_name: Nome do componente
    
    Returns:
        Dict com status detalhado
    """
    return _installer_wrapper.get_installation_status(component_name)

def get_installation_summary() -> Dict[str, Any]:
    """
    Função de compatibilidade global para resumo
    
    Returns:
        Dict com resumo das instalações
    """
    return _installer_wrapper.get_installation_summary()

def cleanup_installer():
    """
    Função de compatibilidade global para limpeza
    """
    _installer_wrapper.cleanup()

# Aliases para compatibilidade total
install_software = install_component
install_softwares = install_multiple_components
check_software_installed = check_component_installed