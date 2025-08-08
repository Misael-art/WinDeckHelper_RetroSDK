#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
YAML Component Detection Strategy
Integra os componentes YAML com verify_actions ao DetectionEngine.
"""

import os
import logging
from typing import List, Optional, Dict, Any
from pathlib import Path
from dataclasses import dataclass

from .detection_base import DetectionStrategy, DetectedApplication, DetectionMethod, ApplicationStatus
from config.loader import load_all_components
from utils import env_checker


class YAMLComponentDetectionStrategy(DetectionStrategy):
    """Estratégia de detecção baseada nos componentes YAML com verify_actions."""
    
    def __init__(self):
        self.logger = logging.getLogger("yaml_component_detection")
        self.components = {}
        self._load_yaml_components()
    
    def _load_yaml_components(self):
        """Carrega todos os componentes YAML."""
        try:
            all_components = load_all_components()
            
            # Filtrar apenas componentes que têm verify_actions
            for name, component_data in all_components.items():
                if 'verify_actions' in component_data and component_data['verify_actions']:
                    self.components[name] = component_data
                    
            self.logger.info(f"Carregados {len(self.components)} componentes YAML com verify_actions")
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar componentes YAML: {e}")
    
    def get_method_name(self) -> DetectionMethod:
        return DetectionMethod.MANUAL_OVERRIDE
    
    def detect_applications(self, target_apps: Optional[List[str]] = None) -> List[DetectedApplication]:
        """Detecta aplicações baseado nas verify_actions dos componentes YAML."""
        self.logger.info(f"YAMLComponentDetectionStrategy: Iniciando detecção com target_apps={target_apps}")
        detected = []
        
        components_to_check = self.components.keys()
        if target_apps:
            # Filtrar apenas componentes solicitados com correspondência mais flexível
            target_lower = [app.lower() for app in target_apps]
            components_to_check = []
            
            self.logger.info(f"YAMLComponentDetectionStrategy: Filtrando componentes para targets: {target_lower}")
            
            for component_name in self.components.keys():
                component_lower = component_name.lower()
                # Verificar correspondência direta ou parcial
                for target in target_lower:
                    if (target in component_lower or 
                        component_lower in target or
                        any(word in component_lower for word in target.split()) or
                        any(word in target for word in component_lower.split())):
                        components_to_check.append(component_name)
                        self.logger.debug(f"YAMLComponentDetectionStrategy: Componente '{component_name}' corresponde ao target '{target}'")
                        break
        
        self.logger.info(f"YAMLComponentDetectionStrategy: Verificando {len(components_to_check)} componentes")
        
        for component_name in components_to_check:
            component_data = self.components[component_name]
            self.logger.debug(f"YAMLComponentDetectionStrategy: Verificando componente '{component_name}'")
            detected_app = self._detect_yaml_component(component_name, component_data)
            if detected_app:
                detected.append(detected_app)
                self.logger.info(f"✅ Detected {component_name} via YAML verify_actions")
            else:
                self.logger.debug(f"❌ {component_name} not detected via YAML verify_actions")
        
        self.logger.info(f"YAMLComponentDetectionStrategy: Detecção concluída. {len(detected)} aplicações detectadas")
        return detected
    
    def _detect_yaml_component(self, component_name: str, component_data: Dict[str, Any]) -> Optional[DetectedApplication]:
        """Detecta um componente específico usando suas verify_actions."""
        verify_actions = component_data.get('verify_actions', [])
        
        if not verify_actions:
            return None
        
        # Agrupar actions por tipo para aplicar lógica OR dentro do grupo
        actions_by_type = {}
        for action in verify_actions:
            action_type = action.get('type')
            if action_type not in actions_by_type:
                actions_by_type[action_type] = []
            actions_by_type[action_type].append(action)
        
        executable_path = ""
        install_path = ""
        all_groups_passed = True
        
        # Para cada tipo de action, pelo menos uma deve passar (OR dentro do grupo)
        for action_type, actions in actions_by_type.items():
            group_passed = False
            
            for action in actions:
                path = action.get('path', '')
                
                # Expandir variáveis de ambiente
                if '${env:' in path:
                    path = self._expand_env_variables(path)
                
                if action_type == 'file_exists':
                    # Resolve path relative to project root to avoid false positives
                    resolved_path = self._resolve_path(path)
                    if env_checker.check_file_exists(resolved_path):
                        group_passed = True
                        # Se é um executável, usar como executable_path
                        if resolved_path.lower().endswith('.exe'):
                            executable_path = resolved_path
                        # Determinar install_path
                        if not install_path:
                            install_path = str(Path(resolved_path).parent)
                        break  # Primeira que passar é suficiente
                        
                elif action_type == 'directory_exists':
                    if env_checker.check_directory_exists(path):
                        group_passed = True
                        # Usar como install_path se não temos um ainda
                        if not install_path:
                            install_path = path
                        break
                        
                elif action_type == 'registry_key_exists':
                    if env_checker.check_registry_key_exists(path):
                        group_passed = True
                        break
                        
                elif action_type == 'command_check':
                    command = action.get('command', path)
                    if env_checker.check_command_available(command):
                        group_passed = True
                        break
            
            # Se nenhuma action do grupo passou, falha geral
            if not group_passed:
                all_groups_passed = False
                break
        
        if not all_groups_passed:
            return None
        
        # Check if this is a project component that should be excluded
        if self._is_project_component(component_data):
            self.logger.debug(f"Skipping project component: {component_name}")
            return None
        
        # Criar DetectedApplication
        return DetectedApplication(
            name=component_name,
            version=self._extract_version(component_data, executable_path),
            install_path=install_path,
            executable_path=executable_path,
            detection_method=DetectionMethod.MANUAL_OVERRIDE,
            status=ApplicationStatus.INSTALLED,
            confidence=0.9,  # Alta confiança pois passou em todas as verificações
            metadata={
                'description': component_data.get('description', ''),
                'category': component_data.get('category', ''),
                'install_method': component_data.get('install_method', ''),
                'download_url': component_data.get('download_url', ''),
                'detection_source': 'yaml_verify_actions'
            }
        )
    
    def _expand_env_variables(self, path: str) -> str:
        """Expande variáveis de ambiente no formato ${env:VARIABLE}."""
        import re
        
        def replace_env_var(match):
            var_name = match.group(1)
            return os.environ.get(var_name, match.group(0))
        
        return re.sub(r'\$\{env:([^}]+)\}', replace_env_var, path)
    
    def _resolve_path(self, path: str) -> str:
        """Resolve relative paths correctly to avoid false positives."""
        # If path is already absolute, return as is
        if os.path.isabs(path):
            return path
        
        # For relative paths, resolve against system paths, not project directory
        # Check common installation directories first
        common_paths = [
            r"C:\Program Files",
            r"C:\Program Files (x86)",
            os.path.expanduser(r"~\AppData\Local"),
            os.path.expanduser(r"~\AppData\Roaming"),
            r"C:\Tools"
        ]
        
        # Check if this is a project component (to be excluded)
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if path.startswith('retro_devkits') or path.startswith('emulators') or path.startswith('core'):
            # For project components, check if they exist in common installation paths
            for base_path in common_paths:
                full_path = os.path.join(base_path, path)
                if os.path.exists(full_path):
                    return full_path
            # If not found in common paths, this is likely a false positive
            return ""  # Return empty string to indicate non-existent path
        
        # For other paths, resolve normally
        return path
    
    def _is_project_component(self, component_data: Dict[str, Any]) -> bool:
        """Check if a component is part of the project rather than a user installation."""
        # Check verify_actions for paths that indicate project components
        verify_actions = component_data.get('verify_actions', [])
        for action in verify_actions:
            path = action.get('path', '')
            # Project components typically have these path patterns
            if (path.startswith('retro_devkits') or
                path.startswith('emulators') or
                path.startswith('core') or
                path.startswith('tools') or
                'env_dev' in path):
                # Check if the path actually exists outside the project directory
                resolved_path = self._resolve_path(path)
                if not resolved_path:
                    return True  # Empty path means it's likely a project component
                
                # Check if resolved path is within project directory
                project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                try:
                    resolved_path = os.path.abspath(resolved_path)
                    if resolved_path.startswith(project_root):
                        return True  # Component is within project directory
                except:
                    pass
        
        return False
    
    def _extract_version(self, component_data: Dict[str, Any], executable_path: str) -> str:
        """Tenta extrair a versão do componente."""
        # Tentar obter versão de diferentes fontes
        
        # 1. Se há um comando de versão definido
        version_command = component_data.get('version_command')
        if version_command and executable_path:
            try:
                import subprocess
                result = subprocess.run(
                    [executable_path] + version_command,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    # Extrair versão do output
                    version = self._parse_version_output(result.stdout)
                    if version:
                        return version
            except Exception:
                pass
        
        # 2. Tentar obter versão do arquivo executável (Windows)
        if executable_path and os.path.exists(executable_path):
            try:
                import win32api
                info = win32api.GetFileVersionInfo(executable_path, "\\")
                ms = info['FileVersionMS']
                ls = info['FileVersionLS']
                version = f"{win32api.HIWORD(ms)}.{win32api.LOWORD(ms)}.{win32api.HIWORD(ls)}.{win32api.LOWORD(ls)}"
                return version
            except Exception:
                pass
        
        # 3. Versão padrão
        return "Unknown"
    
    def _parse_version_output(self, output: str) -> str:
        """Extrai versão de um output de comando."""
        import re
        
        # Padrões comuns de versão
        patterns = [
            r'version\s+([0-9]+\.[0-9]+\.[0-9]+(?:\.[0-9]+)?)',
            r'v([0-9]+\.[0-9]+\.[0-9]+(?:\.[0-9]+)?)',
            r'([0-9]+\.[0-9]+\.[0-9]+(?:\.[0-9]+)?)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return "Unknown"