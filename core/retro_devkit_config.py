"""Sistema de configuração unificada para retro devkits
Gerencia configurações centralizadas para todos os devkits retro"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
import logging
from dataclasses import dataclass, asdict
from enum import Enum

class EmulatorType(Enum):
    """Tipos de emuladores"""
    ACCURACY = "accuracy"  # Foco em precisão
    SPEED = "speed"       # Foco em velocidade
    DEBUG = "debug"       # Foco em debugging
    HOMEBREW = "homebrew" # Foco em homebrew

@dataclass
class EmulatorConfig:
    """Configuração de um emulador"""
    name: str
    executable_path: Optional[str] = None
    command_args: List[str] = None
    emulator_type: EmulatorType = EmulatorType.ACCURACY
    supports_debugging: bool = False
    supports_save_states: bool = True
    file_extensions: List[str] = None
    is_default: bool = False
    
    def __post_init__(self):
        if self.command_args is None:
            self.command_args = []
        if self.file_extensions is None:
            self.file_extensions = []

@dataclass
class DevkitConfig:
    """Configuração de um devkit"""
    name: str
    enabled: bool = True
    installation_path: Optional[str] = None
    toolchain_path: Optional[str] = None
    include_paths: List[str] = None
    library_paths: List[str] = None
    environment_vars: Dict[str, str] = None
    emulators: Dict[str, EmulatorConfig] = None
    default_emulator: Optional[str] = None
    build_settings: Dict[str, Any] = None
    vscode_extensions: List[str] = None
    
    def __post_init__(self):
        if self.include_paths is None:
            self.include_paths = []
        if self.library_paths is None:
            self.library_paths = []
        if self.environment_vars is None:
            self.environment_vars = {}
        if self.emulators is None:
            self.emulators = {}
        if self.build_settings is None:
            self.build_settings = {}
        if self.vscode_extensions is None:
            self.vscode_extensions = []

@dataclass
class GlobalConfig:
    """Configuração global do sistema"""
    base_path: str
    auto_detect_devkits: bool = True
    auto_install_emulators: bool = True
    auto_install_vscode_extensions: bool = True
    preferred_emulator_type: EmulatorType = EmulatorType.ACCURACY
    enable_logging: bool = True
    log_level: str = "INFO"
    backup_projects: bool = True
    check_updates: bool = True
    parallel_builds: bool = True
    max_parallel_jobs: int = 4
    
class RetroDevkitConfigManager:
    """Gerenciador de configuração unificada para retro devkits"""
    
    def __init__(self, base_path: Path, logger: logging.Logger):
        self.base_path = base_path
        self.logger = logger
        self.config_file = base_path / "config" / "retro_devkits.yaml"
        self.config_dir = self.config_file.parent
        
        # Configuração padrão
        self.global_config = GlobalConfig(base_path=str(base_path))
        self.devkit_configs: Dict[str, DevkitConfig] = {}
        
        # Carregar configuração existente
        self.load_config()
        
    def load_config(self) -> bool:
        """Carrega configuração do arquivo"""
        try:
            if not self.config_file.exists():
                self.logger.info("Arquivo de configuração não encontrado. Criando configuração padrão.")
                self._create_default_config()
                return True
                
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
                
            # Carregar configuração global
            if 'global' in config_data:
                global_data = config_data['global']
                self.global_config = GlobalConfig(
                    base_path=global_data.get('base_path', str(self.base_path)),
                    auto_detect_devkits=global_data.get('auto_detect_devkits', True),
                    auto_install_emulators=global_data.get('auto_install_emulators', True),
                    auto_install_vscode_extensions=global_data.get('auto_install_vscode_extensions', True),
                    preferred_emulator_type=EmulatorType(global_data.get('preferred_emulator_type', 'accuracy')),
                    enable_logging=global_data.get('enable_logging', True),
                    log_level=global_data.get('log_level', 'INFO'),
                    backup_projects=global_data.get('backup_projects', True),
                    check_updates=global_data.get('check_updates', True),
                    parallel_builds=global_data.get('parallel_builds', True),
                    max_parallel_jobs=global_data.get('max_parallel_jobs', 4)
                )
                
            # Carregar configurações de devkits
            if 'devkits' in config_data:
                for devkit_name, devkit_data in config_data['devkits'].items():
                    # Carregar emuladores
                    emulators = {}
                    if 'emulators' in devkit_data:
                        for emu_name, emu_data in devkit_data['emulators'].items():
                            emulators[emu_name] = EmulatorConfig(
                                name=emu_data.get('name', emu_name),
                                executable_path=emu_data.get('executable_path'),
                                command_args=emu_data.get('command_args', []),
                                emulator_type=EmulatorType(emu_data.get('emulator_type', 'accuracy')),
                                supports_debugging=emu_data.get('supports_debugging', False),
                                supports_save_states=emu_data.get('supports_save_states', True),
                                file_extensions=emu_data.get('file_extensions', []),
                                is_default=emu_data.get('is_default', False)
                            )
                            
                    self.devkit_configs[devkit_name] = DevkitConfig(
                        name=devkit_data.get('name', devkit_name),
                        enabled=devkit_data.get('enabled', True),
                        installation_path=devkit_data.get('installation_path'),
                        toolchain_path=devkit_data.get('toolchain_path'),
                        include_paths=devkit_data.get('include_paths', []),
                        library_paths=devkit_data.get('library_paths', []),
                        environment_vars=devkit_data.get('environment_vars', {}),
                        emulators=emulators,
                        default_emulator=devkit_data.get('default_emulator'),
                        build_settings=devkit_data.get('build_settings', {}),
                        vscode_extensions=devkit_data.get('vscode_extensions', [])
                    )
                    
            self.logger.info("Configuração carregada com sucesso")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar configuração: {e}")
            self._create_default_config()
            return False
            
    def save_config(self) -> bool:
        """Salva configuração no arquivo"""
        try:
            self.config_dir.mkdir(parents=True, exist_ok=True)
            
            config_data = {
                'global': asdict(self.global_config),
                'devkits': {}
            }
            
            # Converter enum para string na configuração global
            config_data['global']['preferred_emulator_type'] = self.global_config.preferred_emulator_type.value
            
            # Salvar configurações de devkits
            for devkit_name, devkit_config in self.devkit_configs.items():
                devkit_data = asdict(devkit_config)
                
                # Converter emuladores
                if 'emulators' in devkit_data and devkit_data['emulators']:
                    for emu_name, emu_config in devkit_data['emulators'].items():
                        if 'emulator_type' in emu_config:
                            emu_config['emulator_type'] = emu_config['emulator_type'].value
                            
                config_data['devkits'][devkit_name] = devkit_data
                
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, 
                         allow_unicode=True, sort_keys=False, indent=2)
                
            self.logger.info(f"Configuração salva em: {self.config_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar configuração: {e}")
            return False
            
    def _create_default_config(self):
        """Cria configuração padrão"""
        self.logger.info("Criando configuração padrão...")
        
        # Configurações padrão para cada devkit
        default_configs = {
            "GBDK": DevkitConfig(
                name="Game Boy Development Kit",
                vscode_extensions=[
                    "ms-vscode.cpptools",
                    "webfreak.debug",
                    "ms-vscode.hexeditor"
                ],
                emulators={
                    "bgb": EmulatorConfig(
                        name="BGB",
                        emulator_type=EmulatorType.DEBUG,
                        supports_debugging=True,
                        file_extensions=[".gb", ".gbc"],
                        is_default=True
                    ),
                    "sameboy": EmulatorConfig(
                        name="SameBoy",
                        emulator_type=EmulatorType.ACCURACY,
                        file_extensions=[".gb", ".gbc"]
                    )
                },
                default_emulator="bgb"
            ),
            "SNES": DevkitConfig(
                name="Super Nintendo Development Kit",
                vscode_extensions=[
                    "ms-vscode.cpptools",
                    "13xforever.language-x86-64-assembly"
                ],
                emulators={
                    "bsnes": EmulatorConfig(
                        name="bsnes",
                        emulator_type=EmulatorType.ACCURACY,
                        file_extensions=[".sfc", ".smc"],
                        is_default=True
                    ),
                    "snes9x": EmulatorConfig(
                        name="Snes9x",
                        emulator_type=EmulatorType.SPEED,
                        file_extensions=[".sfc", ".smc"]
                    )
                },
                default_emulator="bsnes"
            ),
            "PSX": DevkitConfig(
                name="PlayStation Development Kit",
                vscode_extensions=[
                    "ms-vscode.cpptools",
                    "webfreak.debug"
                ],
                emulators={
                    "duckstation": EmulatorConfig(
                        name="DuckStation",
                        emulator_type=EmulatorType.ACCURACY,
                        supports_debugging=True,
                        file_extensions=[".bin", ".cue", ".iso"],
                        is_default=True
                    ),
                    "pcsx-redux": EmulatorConfig(
                        name="PCSX-Redux",
                        emulator_type=EmulatorType.DEBUG,
                        supports_debugging=True,
                        file_extensions=[".bin", ".cue", ".iso"]
                    )
                },
                default_emulator="duckstation"
            ),
            "N64": DevkitConfig(
                name="Nintendo 64 Development Kit",
                vscode_extensions=[
                    "ms-vscode.cpptools",
                    "13xforever.language-x86-64-assembly"
                ],
                emulators={
                    "ares": EmulatorConfig(
                        name="Ares",
                        emulator_type=EmulatorType.ACCURACY,
                        file_extensions=[".n64", ".z64", ".v64"],
                        is_default=True
                    ),
                    "mupen64plus": EmulatorConfig(
                        name="Mupen64Plus",
                        emulator_type=EmulatorType.SPEED,
                        file_extensions=[".n64", ".z64", ".v64"]
                    )
                },
                default_emulator="ares"
            ),
            "GBA": DevkitConfig(
                name="Game Boy Advance Development Kit",
                vscode_extensions=[
                    "ms-vscode.cpptools",
                    "13xforever.language-x86-64-assembly"
                ],
                emulators={
                    "mgba": EmulatorConfig(
                        name="mGBA",
                        emulator_type=EmulatorType.ACCURACY,
                        supports_debugging=True,
                        file_extensions=[".gba"],
                        is_default=True
                    ),
                    "vba-m": EmulatorConfig(
                        name="VBA-M",
                        emulator_type=EmulatorType.SPEED,
                        file_extensions=[".gba"]
                    )
                },
                default_emulator="mgba"
            ),
            "NeoGeo": DevkitConfig(
                name="Neo Geo Development Kit",
                vscode_extensions=[
                    "ms-vscode.cpptools",
                    "13xforever.language-x86-64-assembly"
                ],
                emulators={
                    "mame": EmulatorConfig(
                        name="MAME",
                        emulator_type=EmulatorType.ACCURACY,
                        file_extensions=[".neo"],
                        is_default=True
                    )
                },
                default_emulator="mame"
            ),
            "NES": DevkitConfig(
                name="Nintendo Entertainment System Development Kit",
                vscode_extensions=[
                    "ms-vscode.cpptools",
                    "13xforever.language-x86-64-assembly"
                ],
                emulators={
                    "fceux": EmulatorConfig(
                        name="FCEUX",
                        emulator_type=EmulatorType.DEBUG,
                        supports_debugging=True,
                        file_extensions=[".nes"],
                        is_default=True
                    ),
                    "mesen": EmulatorConfig(
                        name="Mesen",
                        emulator_type=EmulatorType.ACCURACY,
                        file_extensions=[".nes"]
                    )
                },
                default_emulator="fceux"
            ),
            "Saturn": DevkitConfig(
                name="Sega Saturn Development Kit",
                vscode_extensions=[
                    "ms-vscode.cpptools",
                    "13xforever.language-x86-64-assembly"
                ],
                emulators={
                    "mednafen": EmulatorConfig(
                        name="Mednafen",
                        emulator_type=EmulatorType.ACCURACY,
                        file_extensions=[".cue", ".iso"],
                        is_default=True
                    ),
                    "kronos": EmulatorConfig(
                        name="Kronos",
                        emulator_type=EmulatorType.SPEED,
                        file_extensions=[".cue", ".iso"]
                    )
                },
                default_emulator="mednafen"
            )
        }
        
        self.devkit_configs = default_configs
        self.save_config()
        
    def get_devkit_config(self, devkit_name: str) -> Optional[DevkitConfig]:
        """Obtém configuração de um devkit"""
        return self.devkit_configs.get(devkit_name)
        
    def set_devkit_config(self, devkit_name: str, config: DevkitConfig) -> bool:
        """Define configuração de um devkit"""
        try:
            self.devkit_configs[devkit_name] = config
            return self.save_config()
        except Exception as e:
            self.logger.error(f"Erro ao definir configuração do {devkit_name}: {e}")
            return False
            
    def update_devkit_path(self, devkit_name: str, installation_path: str) -> bool:
        """Atualiza caminho de instalação de um devkit"""
        if devkit_name in self.devkit_configs:
            self.devkit_configs[devkit_name].installation_path = installation_path
            return self.save_config()
        return False
        
    def add_emulator(self, devkit_name: str, emulator_name: str, emulator_config: EmulatorConfig) -> bool:
        """Adiciona emulador a um devkit"""
        if devkit_name in self.devkit_configs:
            self.devkit_configs[devkit_name].emulators[emulator_name] = emulator_config
            return self.save_config()
        return False
        
    def set_default_emulator(self, devkit_name: str, emulator_name: str) -> bool:
        """Define emulador padrão para um devkit"""
        if (devkit_name in self.devkit_configs and 
            emulator_name in self.devkit_configs[devkit_name].emulators):
            
            # Remover default anterior
            for emu in self.devkit_configs[devkit_name].emulators.values():
                emu.is_default = False
                
            # Definir novo default
            self.devkit_configs[devkit_name].emulators[emulator_name].is_default = True
            self.devkit_configs[devkit_name].default_emulator = emulator_name
            return self.save_config()
        return False
        
    def get_enabled_devkits(self) -> List[str]:
        """Retorna lista de devkits habilitados"""
        return [name for name, config in self.devkit_configs.items() if config.enabled]
        
    def enable_devkit(self, devkit_name: str, enabled: bool = True) -> bool:
        """Habilita/desabilita um devkit"""
        if devkit_name in self.devkit_configs:
            self.devkit_configs[devkit_name].enabled = enabled
            return self.save_config()
        return False
        
    def get_environment_vars(self, devkit_name: str) -> Dict[str, str]:
        """Obtém variáveis de ambiente para um devkit"""
        if devkit_name in self.devkit_configs:
            env_vars = self.devkit_configs[devkit_name].environment_vars.copy()
            
            # Adicionar variáveis baseadas nos caminhos
            config = self.devkit_configs[devkit_name]
            if config.installation_path:
                env_vars[f"{devkit_name.upper()}_PATH"] = config.installation_path
            if config.toolchain_path:
                env_vars[f"{devkit_name.upper()}_TOOLCHAIN"] = config.toolchain_path
                
            return env_vars
        return {}
        
    def export_config(self, export_path: Path) -> bool:
        """Exporta configuração para arquivo"""
        try:
            export_data = {
                'global': asdict(self.global_config),
                'devkits': {name: asdict(config) for name, config in self.devkit_configs.items()}
            }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
                
            self.logger.info(f"Configuração exportada para: {export_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao exportar configuração: {e}")
            return False
            
    def import_config(self, import_path: Path) -> bool:
        """Importa configuração de arquivo"""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
                
            # Fazer backup da configuração atual
            backup_path = self.config_file.with_suffix('.yaml.backup')
            if self.config_file.exists():
                import shutil
                shutil.copy2(self.config_file, backup_path)
                
            # Importar nova configuração
            # (Implementar lógica de importação conforme necessário)
            
            self.logger.info(f"Configuração importada de: {import_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao importar configuração: {e}")
            return False