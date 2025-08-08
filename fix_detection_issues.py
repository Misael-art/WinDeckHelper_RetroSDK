#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para corrigir problemas de detecção de software
Corrige falsos positivos e melhora a detecção de componentes específicos
"""

import os
import sys
import yaml
import platform
from pathlib import Path

def fix_kde_plasma_protondb():
    """Corrige KDE Plasma e ProtonDB para não serem detectados no Windows"""
    print("\n=== Corrigindo KDE Plasma e ProtonDB ===")
    
    steam_deck_file = Path("f:/Projetos/env_dev/config/components/steam_deck_tools.yaml")
    
    if not steam_deck_file.exists():
        print(f"❌ Arquivo não encontrado: {steam_deck_file}")
        return False
    
    try:
        with open(steam_deck_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        # Adiciona verificação de sistema operacional para KDE Plasma
        if 'KDE Plasma Mobile Info' in data:
            if 'verify_actions' not in data['KDE Plasma Mobile Info']:
                data['KDE Plasma Mobile Info']['verify_actions'] = []
            
            # Adiciona verificação que sempre falha no Windows
            data['KDE Plasma Mobile Info']['verify_actions'] = [
                {
                    'type': 'command_exists',
                    'name': 'kde-plasma-desktop',
                    'description': 'KDE Plasma só está disponível em sistemas Linux'
                }
            ]
            print("✓ KDE Plasma configurado para verificação correta")
        
        # Adiciona verificação de sistema operacional para ProtonDB
        if 'ProtonDB Notes' in data:
            if 'verify_actions' not in data['ProtonDB Notes']:
                data['ProtonDB Notes']['verify_actions'] = []
            
            # ProtonDB é apenas um site, nunca deve ser detectado como instalado
            data['ProtonDB Notes']['verify_actions'] = [
                {
                    'type': 'command_output',
                    'command': 'echo "ProtonDB is a website, not installable software"',
                    'expected_contains': 'never_match_this_string_12345',
                    'description': 'ProtonDB é apenas um site web, não software instalável'
                }
            ]
            print("✓ ProtonDB configurado para nunca ser detectado como instalado")
        
        # Salva as alterações
        with open(steam_deck_file, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        
        print("✓ Arquivo steam_deck_tools.yaml atualizado")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao processar {steam_deck_file}: {e}")
        return False

def fix_hardlinkshellext():
    """Melhora a detecção do HardLinkShellExt"""
    print("\n=== Melhorando detecção do HardLinkShellExt ===")
    
    common_utils_file = Path("f:/Projetos/env_dev/config/components/common_utils.yaml")
    
    if not common_utils_file.exists():
        print(f"❌ Arquivo não encontrado: {common_utils_file}")
        return False
    
    try:
        with open(common_utils_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        if 'HardLinkShellExt_X64' in data:
            # Adiciona múltiplos caminhos de verificação
            data['HardLinkShellExt_X64']['verify_actions'] = [
                {
                    'type': 'file_exists',
                    'path': 'C:\\Program Files\\HardlinkShellExt\\HardlinkShellExt.dll'
                },
                {
                    'type': 'file_exists', 
                    'path': 'C:\\Program Files (x86)\\HardlinkShellExt\\HardlinkShellExt.dll'
                },
                {
                    'type': 'file_exists',
                    'path': 'C:\\Windows\\System32\\HardlinkShellExt.dll'
                },
                {
                    'type': 'file_exists',
                    'path': 'C:\\Windows\\SysWOW64\\HardlinkShellExt.dll'
                },
                {
                    'type': 'registry_key_exists',
                    'hive': 'HKLM',
                    'path': 'SOFTWARE\\Classes\\CLSID\\{00021401-0000-0000-C000-000000000046}\\InprocServer32',
                    'description': 'Verifica registro do shell extension'
                }
            ]
            print("✓ HardLinkShellExt configurado com múltiplos caminhos de verificação")
        
        # Salva as alterações
        with open(common_utils_file, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        
        print("✓ Arquivo common_utils.yaml atualizado")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao processar {common_utils_file}: {e}")
        return False

def fix_revo_uninstaller():
    """Melhora a detecção do Revo Uninstaller"""
    print("\n=== Melhorando detecção do Revo Uninstaller ===")
    
    common_utils_file = Path("f:/Projetos/env_dev/config/components/common_utils.yaml")
    
    if not common_utils_file.exists():
        print(f"❌ Arquivo não encontrado: {common_utils_file}")
        return False
    
    try:
        with open(common_utils_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        if 'Revo Uninstaller' in data:
            # Adiciona múltiplos caminhos de verificação
            data['Revo Uninstaller']['verify_actions'] = [
                {
                    'type': 'file_exists',
                    'path': '${env:ProgramFiles}\\Revo Uninstaller Free\\RevoUPort.exe'
                },
                {
                    'type': 'file_exists',
                    'path': 'C:\\Program Files\\Revo Uninstaller Free\\RevoUPort.exe'
                },
                {
                    'type': 'file_exists',
                    'path': 'C:\\Program Files (x86)\\Revo Uninstaller Free\\RevoUPort.exe'
                },
                {
                    'type': 'file_exists',
                    'path': 'C:\\Program Files\\VS Revo Group\\Revo Uninstaller\\Revouninstaller.exe'
                },
                {
                    'type': 'file_exists',
                    'path': 'C:\\Program Files (x86)\\VS Revo Group\\Revo Uninstaller\\Revouninstaller.exe'
                },
                {
                    'type': 'registry_key_exists',
                    'hive': 'HKLM',
                    'path': 'SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\Revo Uninstaller',
                    'description': 'Verifica registro de desinstalação'
                }
            ]
            print("✓ Revo Uninstaller configurado com múltiplos caminhos de verificação")
        
        # Salva as alterações
        with open(common_utils_file, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        
        print("✓ Arquivo common_utils.yaml atualizado")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao processar {common_utils_file}: {e}")
        return False

def add_powershell_preview():
    """Adiciona configuração para PowerShell Preview"""
    print("\n=== Adicionando PowerShell Preview ===")
    
    runtimes_file = Path("f:/Projetos/env_dev/config/components/runtimes.yaml")
    
    if not runtimes_file.exists():
        print(f"❌ Arquivo não encontrado: {runtimes_file}")
        return False
    
    try:
        with open(runtimes_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        # Adiciona PowerShell Preview se não existir
        if 'PowerShell Preview' not in data:
            data['PowerShell Preview'] = {
                'category': 'Runtimes',
                'description': 'PowerShell Core Preview (versão de desenvolvimento)',
                'download_url': 'https://github.com/PowerShell/PowerShell/releases',
                'install_method': 'manual',
                'notes': 'Instalação manual via GitHub releases',
                'verify_actions': [
                    {
                        'type': 'command_exists',
                        'name': 'pwsh-preview'
                    },
                    {
                        'type': 'file_exists',
                        'path': 'C:\\Program Files\\PowerShell\\7-preview\\pwsh.exe'
                    },
                    {
                        'type': 'command_output',
                        'command': 'pwsh-preview -Command "$PSVersionTable.PSVersion"',
                        'expected_contains': 'preview',
                        'description': 'Verifica se é versão preview'
                    }
                ]
            }
            print("✓ PowerShell Preview adicionado à configuração")
        else:
            print("✓ PowerShell Preview já existe na configuração")
        
        # Salva as alterações
        with open(runtimes_file, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        
        print("✓ Arquivo runtimes.yaml atualizado")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao processar {runtimes_file}: {e}")
        return False

def improve_python_detection():
    """Melhora a detecção do Python para incluir versão 3.13"""
    print("\n=== Melhorando detecção do Python ===")
    
    runtimes_file = Path("f:/Projetos/env_dev/config/components/runtimes.yaml")
    
    if not runtimes_file.exists():
        print(f"❌ Arquivo não encontrado: {runtimes_file}")
        return False
    
    try:
        with open(runtimes_file, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        if 'Python' in data:
            # Atualiza a descrição e verificações
            data['Python']['description'] = 'Linguagem de programação Python (3.12+)'
            data['Python']['verify_actions'] = [
                {
                    'type': 'command_exists',
                    'name': 'python'
                },
                {
                    'type': 'command_exists',
                    'name': 'python3'
                },
                {
                    'type': 'command_exists',
                    'name': 'py'
                },
                {
                    'type': 'command_output',
                    'command': 'python --version',
                    'expected_contains': 'Python 3.',
                    'description': 'Verifica versão do Python'
                }
            ]
            print("✓ Python configurado com verificações melhoradas")
        
        # Adiciona Python 3.13 específico se não existir
        if 'Python 3.13' not in data:
            data['Python 3.13'] = {
                'category': 'Runtimes',
                'description': 'Python 3.13 (versão específica)',
                'download_url': 'https://www.python.org/downloads/release/python-3132/',
                'install_method': 'manual',
                'notes': 'Versão específica do Python 3.13',
                'verify_actions': [
                    {
                        'type': 'command_output',
                        'command': 'python --version',
                        'expected_contains': 'Python 3.13',
                        'description': 'Verifica se é Python 3.13'
                    },
                    {
                        'type': 'command_exists',
                        'name': 'python3.13'
                    }
                ]
            }
            print("✓ Python 3.13 adicionado à configuração")
        
        # Salva as alterações
        with open(runtimes_file, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        
        print("✓ Arquivo runtimes.yaml atualizado")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao processar {runtimes_file}: {e}")
        return False

def create_os_filter_system():
    """Cria sistema de filtros por sistema operacional"""
    print("\n=== Criando sistema de filtros por SO ===")
    
    filter_file = Path("f:/Projetos/env_dev/utils/os_component_filter.py")
    
    filter_code = '''#!/usr/bin/env python3
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
                'PCSX2 (Flatpak)'
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
    
    def filter_components_data(self, components_data: Dict[str, Any]) -> Dict[str, Any]:
        """Filtra dados de componentes baseado no SO atual"""
        filtered_data = {}
        
        for name, data in components_data.items():
            if self.should_check_component(name):
                filtered_data[name] = data
            else:
                logger.debug(f"Componente '{name}' filtrado para SO '{self.current_os}'")
        
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
'''
    
    try:
        os.makedirs(filter_file.parent, exist_ok=True)
        with open(filter_file, 'w', encoding='utf-8') as f:
            f.write(filter_code)
        
        print(f"✓ Sistema de filtros criado: {filter_file}")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar sistema de filtros: {e}")
        return False

def main():
    """Função principal"""
    print("Script de Correção de Problemas de Detecção")
    print("=" * 50)
    
    results = {
        "KDE Plasma/ProtonDB": fix_kde_plasma_protondb(),
        "HardLinkShellExt": fix_hardlinkshellext(),
        "Revo Uninstaller": fix_revo_uninstaller(),
        "PowerShell Preview": add_powershell_preview(),
        "Python Detection": improve_python_detection(),
        "OS Filter System": create_os_filter_system()
    }
    
    print("\n" + "=" * 50)
    print("RESUMO DAS CORREÇÕES:")
    print("=" * 50)
    
    for fix_name, success in results.items():
        status = "✓ APLICADO" if success else "✗ FALHOU"
        print(f"{fix_name:20} : {status}")
    
    print("\nPróximos passos:")
    print("1. Reinicie a aplicação para aplicar as mudanças")
    print("2. Teste a detecção dos componentes corrigidos")
    print("3. Verifique se os falsos positivos foram eliminados")

if __name__ == "__main__":
    main()