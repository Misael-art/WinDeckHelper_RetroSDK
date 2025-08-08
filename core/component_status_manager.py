# -*- coding: utf-8 -*-
"""
Component Status Manager
Sistema para gerenciar o status de instalação dos componentes,
sincronizando detecção com status real de instalação.
"""
import logging
import json
import threading
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

class ComponentStatus(Enum):
    """Status de um componente"""
    NOT_DETECTED = "not_detected"
    DETECTED = "detected"
    INSTALLED = "installed"
    NEEDS_UPDATE = "needs_update"
    INSTALLATION_FAILED = "installation_failed"
    VERIFICATION_FAILED = "verification_failed"

@dataclass
class ComponentInfo:
    """Informações de um componente"""
    component_id: str
    name: str
    status: ComponentStatus
    version_detected: Optional[str] = None
    version_expected: Optional[str] = None
    install_path: Optional[str] = None
    last_checked: Optional[datetime] = None
    last_installed: Optional[datetime] = None
    installation_verified: bool = False
    error_message: Optional[str] = None

class ComponentStatusManager:
    """Gerenciador de status de componentes"""
    
    def __init__(self, status_file: str = "component_status.json"):
        self.logger = logging.getLogger(__name__)
        self.status_file = Path(status_file)
        self.components: Dict[str, ComponentInfo] = {}
        self._lock = threading.RLock()
        
        # Carregar status existente
        self._load_status()
        self.logger.info("Component Status Manager initialized")

    def _load_status(self):
        """Carrega status dos componentes do arquivo"""
        try:
            if self.status_file.exists():
                with open(self.status_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for comp_id, comp_data in data.items():
                    # Converter datetime strings de volta
                    if comp_data.get('last_checked'):
                        comp_data['last_checked'] = datetime.fromisoformat(comp_data['last_checked'])
                    if comp_data.get('last_installed'):
                        comp_data['last_installed'] = datetime.fromisoformat(comp_data['last_installed'])
                    
                    # Converter status string para enum
                    comp_data['status'] = ComponentStatus(comp_data['status'])
                    self.components[comp_id] = ComponentInfo(**comp_data)
                
                self.logger.info(f"Loaded status for {len(self.components)} components")
        except Exception as e:
            self.logger.error(f"Error loading component status: {e}")
            self.components = {}

    def _save_status(self):
        """Salva status dos componentes no arquivo"""
        try:
            # Converter para formato serializável
            data = {}
            for comp_id, comp_info in self.components.items():
                comp_dict = asdict(comp_info)
                
                # Converter datetime para string
                if comp_dict.get('last_checked'):
                    comp_dict['last_checked'] = comp_dict['last_checked'].isoformat()
                if comp_dict.get('last_installed'):
                    comp_dict['last_installed'] = comp_dict['last_installed'].isoformat()
                
                # Converter enum para string
                comp_dict['status'] = comp_dict['status'].value
                data[comp_id] = comp_dict
            
            # Salvar arquivo
            with open(self.status_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"Error saving component status: {e}")

    def update_component_status(self, 
                              component_id: str,
                              name: str,
                              status: ComponentStatus,
                              version_detected: Optional[str] = None,
                              version_expected: Optional[str] = None,
                              install_path: Optional[str] = None,
                              error_message: Optional[str] = None):
        """
        Atualiza o status de um componente
        """
        with self._lock:
            now = datetime.now()
            
            if component_id in self.components:
                comp_info = self.components[component_id]
                comp_info.status = status
                comp_info.last_checked = now
                
                if version_detected:
                    comp_info.version_detected = version_detected
                if version_expected:
                    comp_info.version_expected = version_expected
                if install_path:
                    comp_info.install_path = install_path
                if error_message:
                    comp_info.error_message = error_message
                
                # Marcar como instalado se status for INSTALLED
                if status == ComponentStatus.INSTALLED:
                    comp_info.last_installed = now
                    comp_info.installation_verified = True
                    comp_info.error_message = None
            else:
                # Criar novo componente
                self.components[component_id] = ComponentInfo(
                    component_id=component_id,
                    name=name,
                    status=status,
                    version_detected=version_detected,
                    version_expected=version_expected,
                    install_path=install_path,
                    last_checked=now,
                    last_installed=now if status == ComponentStatus.INSTALLED else None,
                    installation_verified=status == ComponentStatus.INSTALLED,
                    error_message=error_message
                )
            
            # Salvar mudanças
            self._save_status()
            self.logger.info(f"Updated component {component_id} status to {status.value}")

    def get_component_status(self, component_id: str) -> Optional[ComponentInfo]:
        """Obtém o status de um componente"""
        with self._lock:
            return self.components.get(component_id)

    def get_all_components(self) -> Dict[str, ComponentInfo]:
        """Obtém status de todos os componentes"""
        with self._lock:
            return self.components.copy()

    def mark_component_installed(self, 
                                component_id: str, 
                                name: str,
                                version: str,
                                install_path: str):
        """Marca um componente como instalado"""
        self.update_component_status(
            component_id=component_id,
            name=name,
            status=ComponentStatus.INSTALLED,
            version_detected=version,
            install_path=install_path
        )

    def mark_component_failed(self, 
                             component_id: str, 
                             name: str,
                             error_message: str):
        """Marca um componente como falha na instalação"""
        self.update_component_status(
            component_id=component_id,
            name=name,
            status=ComponentStatus.INSTALLATION_FAILED,
            error_message=error_message
        )

    def is_component_installed(self, component_id: str) -> bool:
        """Verifica se um componente está instalado"""
        with self._lock:
            comp_info = self.components.get(component_id)
            return comp_info and comp_info.status == ComponentStatus.INSTALLED

    def clear_component_status(self, component_id: str):
        """Remove o status de um componente"""
        with self._lock:
            if component_id in self.components:
                del self.components[component_id]
                self._save_status()
                self.logger.info(f"Cleared status for component {component_id}")

# Instância global do gerenciador
_status_manager = None

def get_status_manager() -> ComponentStatusManager:
    """Obtém instância global do gerenciador de status"""
    global _status_manager
    if _status_manager is None:
        _status_manager = ComponentStatusManager()
    return _status_manager