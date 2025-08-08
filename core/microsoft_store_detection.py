"""Detecção de aplicações da Microsoft Store (UWP).

Este módulo implementa detecção de aplicações Universal Windows Platform (UWP)
instaladas através da Microsoft Store usando PowerShell e comandos do sistema.

Author: AI Assistant
Date: 2024
"""

import json
import logging
import subprocess
import re
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass
from pathlib import Path

# Importações movidas para evitar circular import


@dataclass
class UWPApplication:
    """Informações de uma aplicação UWP."""
    name: str
    package_full_name: str
    package_family_name: str
    version: str
    publisher: str
    install_location: str
    is_framework: bool = False
    is_bundle: bool = False
    architecture: str = ""
    

class MicrosoftStoreDetectionStrategy:
    """Estratégia de detecção para aplicações da Microsoft Store."""
    
    def __init__(self):
        self.logger = logging.getLogger(f"detection_{self.__class__.__name__.lower()}")
        self.confidence_level = 0.9  # Alta confiança para detecção UWP
        
        # Mapeamento de PackageFamilyName para nomes amigáveis
        self.known_apps = {
            # Ferramentas de Desenvolvimento
            "Microsoft.VisualStudioCode_8wekyb3d8bbwe": "Visual Studio Code",
            "Microsoft.VisualStudio.Community.2022_8wekyb3d8bbwe": "Visual Studio Community 2022",
            "Microsoft.VisualStudio.Professional.2022_8wekyb3d8bbwe": "Visual Studio Professional 2022",
            "Microsoft.VisualStudio.Enterprise.2022_8wekyb3d8bbwe": "Visual Studio Enterprise 2022",
            "Microsoft.WindowsTerminal_8wekyb3d8bbwe": "Windows Terminal",
            "Microsoft.PowerShell_8wekyb3d8bbwe": "PowerShell",
            "GitHubDesktop_317af281d39c6": "GitHub Desktop",
            "Docker.DockerDesktop_9npnbdxp4ssz": "Docker Desktop",
            
            # Runtimes e SDKs
            "Microsoft.DotNetFramework_8wekyb3d8bbwe": ".NET Framework",
            "Microsoft.VCLibs.140.00_8wekyb3d8bbwe": "Visual C++ Redistributable",
            "Microsoft.VCLibs.140.00.UWPDesktop_8wekyb3d8bbwe": "Visual C++ UWP Desktop",
            
            # Navegadores
            "Microsoft.MicrosoftEdge_8wekyb3d8bbwe": "Microsoft Edge",
            "Mozilla.Firefox_n80bbvh6b1yt2": "Firefox",
            "Google.Chrome_q5xwmzleaqy6t": "Google Chrome",
            
            # Editores de Texto/IDEs
            "Microsoft.WindowsNotepad_8wekyb3d8bbwe": "Notepad",
            "Notepad++.Notepad++_7njy0v32s6xk6": "Notepad++",
            "SublimeHQ.SublimeText_8wekyb3d8bbwe": "Sublime Text",
            
            # Utilitários
            "7zip.7zip_qzc4129jw3ce2": "7-Zip",
            "WinRAR.WinRAR_s4jet1zx4n2a4": "WinRAR",
            "Microsoft.WindowsCalculator_8wekyb3d8bbwe": "Calculator",
            "Microsoft.Paint_8wekyb3d8bbwe": "Paint",
            
            # Comunicação
            "Microsoft.Teams_8wekyb3d8bbwe": "Microsoft Teams",
            "Discord.Discord_79x9qrjyw6we8": "Discord",
            "SlackTechnologies.Slack_8wekyb3d8bbwe": "Slack",
            
            # Mídia
            "Microsoft.WindowsMediaPlayer_8wekyb3d8bbwe": "Windows Media Player",
            "VLC.VideoLAN_13xsb5r4jzb6p": "VLC Media Player",
            
            # Jogos e Entretenimento
            "Microsoft.XboxApp_8wekyb3d8bbwe": "Xbox",
            "Microsoft.XboxGameOverlay_8wekyb3d8bbwe": "Xbox Game Overlay",
            "Steam.Steam_1wkx4s9jw8qwj": "Steam",
        }
        
        # Categorias de aplicações para melhor organização
        self.app_categories = {
            "development": [
                "Visual Studio Code", "Visual Studio Community 2022", "Visual Studio Professional 2022",
                "Visual Studio Enterprise 2022", "Windows Terminal", "PowerShell", "GitHub Desktop",
                "Docker Desktop", "Notepad++", "Sublime Text"
            ],
            "runtime": [
                ".NET Framework", "Visual C++ Redistributable", "Visual C++ UWP Desktop"
            ],
            "browser": [
                "Microsoft Edge", "Firefox", "Google Chrome"
            ],
            "utility": [
                "7-Zip", "WinRAR", "Calculator", "Paint", "Notepad"
            ],
            "communication": [
                "Microsoft Teams", "Discord", "Slack"
            ],
            "media": [
                "Windows Media Player", "VLC Media Player"
            ],
            "gaming": [
                "Xbox", "Xbox Game Overlay", "Steam"
            ]
        }
    
    def detect_applications(self, target_apps: Optional[List[str]] = None):
        """Detecta aplicações UWP instaladas."""
        # Importação dinâmica para evitar circular import
        from .detection_engine import DetectedApplication, DetectionMethod, ApplicationStatus
        
        detected_apps = []
        
        try:
            # Obter lista de pacotes UWP instalados
            uwp_apps = self._get_uwp_packages()
            
            # Filtrar e processar aplicações relevantes
            for uwp_app in uwp_apps:
                # Verificar se é uma aplicação conhecida ou relevante
                if self._is_relevant_app(uwp_app, target_apps):
                    detected_app = self._create_detected_application(uwp_app)
                    if detected_app:
                        detected_apps.append(detected_app)
            
            self.logger.info(f"Detectadas {len(detected_apps)} aplicações UWP relevantes")
            
        except Exception as e:
            self.logger.error(f"Erro na detecção de aplicações UWP: {e}")
        
        return detected_apps
    
    def _get_uwp_packages(self) -> List[UWPApplication]:
        """Obtém lista de pacotes UWP usando PowerShell."""
        uwp_apps = []
        
        try:
            # Comando PowerShell para obter pacotes instalados
            cmd = [
                "powershell", "-Command",
                "Get-AppxPackage | Where-Object { $_.SignatureKind -eq 'Store' -or $_.SignatureKind -eq 'Developer' } | "
                "Select-Object Name, PackageFullName, PackageFamilyName, Version, Publisher, InstallLocation, "
                "IsFramework, IsBundle, Architecture | ConvertTo-Json -Depth 3"
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                encoding='utf-8'
            )
            
            if result.returncode == 0 and result.stdout.strip():
                try:
                    # Parse JSON output
                    packages_data = json.loads(result.stdout)
                    
                    # Garantir que é uma lista
                    if isinstance(packages_data, dict):
                        packages_data = [packages_data]
                    
                    for package in packages_data:
                        uwp_app = UWPApplication(
                            name=package.get('Name', ''),
                            package_full_name=package.get('PackageFullName', ''),
                            package_family_name=package.get('PackageFamilyName', ''),
                            version=package.get('Version', ''),
                            publisher=package.get('Publisher', ''),
                            install_location=package.get('InstallLocation', ''),
                            is_framework=package.get('IsFramework', False),
                            is_bundle=package.get('IsBundle', False),
                            architecture=package.get('Architecture', '')
                        )
                        uwp_apps.append(uwp_app)
                        
                except json.JSONDecodeError as e:
                    self.logger.error(f"Erro ao parsear JSON do PowerShell: {e}")
                    # Fallback: tentar parsing linha por linha
                    uwp_apps = self._parse_powershell_output_fallback(result.stdout)
            
            else:
                self.logger.warning(f"Comando PowerShell falhou: {result.stderr}")
                # Tentar método alternativo
                uwp_apps = self._get_uwp_packages_alternative()
        
        except subprocess.TimeoutExpired:
            self.logger.error("Timeout ao executar comando PowerShell")
        except Exception as e:
            self.logger.error(f"Erro ao obter pacotes UWP: {e}")
        
        return uwp_apps
    
    def _get_uwp_packages_alternative(self) -> List[UWPApplication]:
        """Método alternativo para obter pacotes UWP."""
        uwp_apps = []
        
        try:
            # Comando mais simples
            cmd = ["powershell", "-Command", "Get-AppxPackage | Select-Object Name, PackageFullName, Version"]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=20,
                encoding='utf-8'
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                current_app = {}
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        if current_app.get('Name'):
                            uwp_app = UWPApplication(
                                name=current_app.get('Name', ''),
                                package_full_name=current_app.get('PackageFullName', ''),
                                package_family_name='',
                                version=current_app.get('Version', ''),
                                publisher='',
                                install_location=''
                            )
                            uwp_apps.append(uwp_app)
                        current_app = {}
                    elif ':' in line:
                        key, value = line.split(':', 1)
                        current_app[key.strip()] = value.strip()
        
        except Exception as e:
            self.logger.error(f"Erro no método alternativo: {e}")
        
        return uwp_apps
    
    def _parse_powershell_output_fallback(self, output: str) -> List[UWPApplication]:
        """Parse manual da saída do PowerShell como fallback."""
        uwp_apps = []
        
        try:
            # Tentar extrair informações usando regex
            lines = output.split('\n')
            current_app = {}
            
            for line in lines:
                line = line.strip()
                if line.startswith('Name'):
                    if current_app:
                        uwp_app = self._create_uwp_app_from_dict(current_app)
                        if uwp_app:
                            uwp_apps.append(uwp_app)
                    current_app = {'Name': line.split(':', 1)[1].strip() if ':' in line else ''}
                elif ':' in line and current_app:
                    key, value = line.split(':', 1)
                    current_app[key.strip()] = value.strip()
            
            # Processar último app
            if current_app:
                uwp_app = self._create_uwp_app_from_dict(current_app)
                if uwp_app:
                    uwp_apps.append(uwp_app)
        
        except Exception as e:
            self.logger.error(f"Erro no parse fallback: {e}")
        
        return uwp_apps
    
    def _create_uwp_app_from_dict(self, app_dict: Dict[str, str]) -> Optional[UWPApplication]:
        """Cria UWPApplication a partir de dicionário."""
        try:
            return UWPApplication(
                name=app_dict.get('Name', ''),
                package_full_name=app_dict.get('PackageFullName', ''),
                package_family_name=app_dict.get('PackageFamilyName', ''),
                version=app_dict.get('Version', ''),
                publisher=app_dict.get('Publisher', ''),
                install_location=app_dict.get('InstallLocation', ''),
                is_framework=app_dict.get('IsFramework', '').lower() == 'true',
                is_bundle=app_dict.get('IsBundle', '').lower() == 'true',
                architecture=app_dict.get('Architecture', '')
            )
        except Exception:
            return None
    
    def _is_relevant_app(self, uwp_app: UWPApplication, target_apps: Optional[List[str]]) -> bool:
        """Verifica se a aplicação UWP é relevante para detecção."""
        # Ignorar frameworks e bundles vazios
        if uwp_app.is_framework and not uwp_app.name:
            return False
        
        # Se target_apps especificado, verificar se está na lista
        if target_apps:
            friendly_name = self._get_friendly_name(uwp_app)
            for target in target_apps:
                if target.lower() in friendly_name.lower() or target.lower() in uwp_app.name.lower():
                    return True
            return False
        
        # Verificar se é uma aplicação conhecida
        if uwp_app.package_family_name in self.known_apps:
            return True
        
        # Verificar padrões de nomes para aplicações de desenvolvimento
        dev_patterns = [
            r'.*visual.*studio.*',
            r'.*code.*',
            r'.*git.*',
            r'.*docker.*',
            r'.*terminal.*',
            r'.*powershell.*',
            r'.*notepad.*',
            r'.*sublime.*'
        ]
        
        name_lower = uwp_app.name.lower()
        for pattern in dev_patterns:
            if re.match(pattern, name_lower):
                return True
        
        return False
    
    def _get_friendly_name(self, uwp_app: UWPApplication) -> str:
        """Obtém nome amigável da aplicação."""
        # Verificar mapeamento conhecido
        if uwp_app.package_family_name in self.known_apps:
            return self.known_apps[uwp_app.package_family_name]
        
        # Tentar extrair nome amigável do nome do pacote
        if uwp_app.name:
            # Remover prefixos comuns
            name = uwp_app.name
            name = re.sub(r'^Microsoft\.', '', name)
            name = re.sub(r'^Windows\.', '', name)
            
            # Converter CamelCase para espaços
            name = re.sub(r'([a-z])([A-Z])', r'\1 \2', name)
            
            return name
        
        return uwp_app.package_family_name.split('_')[0] if '_' in uwp_app.package_family_name else uwp_app.package_family_name
    
    def _create_detected_application(self, uwp_app: UWPApplication):
        """Cria DetectedApplication a partir de UWPApplication."""
        # Importação dinâmica para evitar circular import
        from .detection_engine import DetectedApplication, DetectionMethod, ApplicationStatus
        
        try:
            friendly_name = self._get_friendly_name(uwp_app)
            
            # Determinar categoria
            category = self._get_app_category(friendly_name)
            
            detected_app = DetectedApplication(
                name=friendly_name,
                version=uwp_app.version,
                install_path=uwp_app.install_location,
                executable_path="",  # UWP apps não têm executável tradicional
                detection_method=DetectionMethod.PACKAGE_MANAGER,
                status=ApplicationStatus.INSTALLED,
                confidence=self.confidence_level,
                metadata={
                    "package_full_name": uwp_app.package_full_name,
                    "package_family_name": uwp_app.package_family_name,
                    "publisher": uwp_app.publisher,
                    "architecture": uwp_app.architecture,
                    "is_framework": uwp_app.is_framework,
                    "is_bundle": uwp_app.is_bundle,
                    "app_type": "uwp",
                    "category": category
                }
            )
            
            return detected_app
            
        except Exception as e:
            self.logger.error(f"Erro ao criar DetectedApplication: {e}")
            return None
    
    def _get_app_category(self, app_name: str) -> str:
        """Determina a categoria da aplicação."""
        app_name_lower = app_name.lower()
        
        for category, apps in self.app_categories.items():
            for app in apps:
                if app.lower() in app_name_lower:
                    return category
        
        return "other"
    
    def get_method_name(self):
        """Retorna o método de detecção."""
        # Importação dinâmica para evitar circular import
        from .detection_engine import DetectionMethod
        return DetectionMethod.PACKAGE_MANAGER
    
    def get_installed_uwp_apps_summary(self) -> Dict[str, Any]:
        """Obtém resumo das aplicações UWP instaladas."""
        try:
            uwp_apps = self._get_uwp_packages()
            
            summary = {
                "total_packages": len(uwp_apps),
                "by_category": {},
                "frameworks": 0,
                "bundles": 0,
                "known_apps": 0
            }
            
            for app in uwp_apps:
                if app.is_framework:
                    summary["frameworks"] += 1
                if app.is_bundle:
                    summary["bundles"] += 1
                if app.package_family_name in self.known_apps:
                    summary["known_apps"] += 1
                
                friendly_name = self._get_friendly_name(app)
                category = self._get_app_category(friendly_name)
                summary["by_category"][category] = summary["by_category"].get(category, 0) + 1
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Erro ao obter resumo UWP: {e}")
            return {"error": str(e)}