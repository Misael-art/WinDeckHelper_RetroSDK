"""
Retro DevKit Manager - Sistema robusto para instalação de devkits de consoles retro
Suporta consoles de 8, 16 e 32 bits com configuração automática completa
"""

import os
import sys
import json
import subprocess
import shutil
import urllib.request
import zipfile
import tarfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass
from enum import Enum

class ConsoleGeneration(Enum):
    BIT_8 = "8-bit"
    BIT_16 = "16-bit"
    BIT_32 = "32-bit"

class ConsoleType(Enum):
    HOME = "home"
    PORTABLE = "portable"

@dataclass
class DevKitInfo:
    name: str
    console: str
    generation: ConsoleGeneration
    console_type: ConsoleType
    devkit_name: str
    dependencies: List[str]
    environment_vars: Dict[str, str]
    download_url: Optional[str]
    install_commands: List[str]
    verification_commands: List[str]
    emulators: List[str]
    docker_support: bool = False

class RetroDevKitManager:
    """Gerenciador completo de devkits para consoles retro"""
    
    def __init__(self, base_path: str = None):
        self.base_path = Path(base_path) if base_path else Path.home() / "RetroDevKits"
        self.config_file = self.base_path / "devkit_config.json"
        self.logger = self._setup_logging()
        self.devkits = self._initialize_devkits()
        
    def _setup_logging(self) -> logging.Logger:
        """Configura logging específico para devkits"""
        logger = logging.getLogger("RetroDevKitManager")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    def _initialize_devkits(self) -> Dict[str, DevKitInfo]:
        """Inicializa configurações de todos os devkits suportados"""
        devkits = {}
        
        # 8-bit Home Consoles
        devkits.update(self._get_8bit_home_devkits())
        
        # 8-bit Portable Consoles
        devkits.update(self._get_8bit_portable_devkits())
        
        # 16-bit Home Consoles
        devkits.update(self._get_16bit_home_devkits())
        
        # 16-bit Portable Consoles
        devkits.update(self._get_16bit_portable_devkits())
        
        # 32-bit Home Consoles
        devkits.update(self._get_32bit_home_devkits())
        
        # 32-bit Portable Consoles
        devkits.update(self._get_32bit_portable_devkits())
        
        return devkits
    
    def _get_8bit_home_devkits(self) -> Dict[str, DevKitInfo]:
        """Devkits para consoles domésticos de 8-bit"""
        return {
            "nes": DevKitInfo(
                name="NES Development Kit",
                console="Nintendo Entertainment System",
                generation=ConsoleGeneration.BIT_8,
                console_type=ConsoleType.HOME,
                devkit_name="8BitWorkshop + CC65",
                dependencies=["cc65", "make", "python3"],
                environment_vars={
                    "CC65_HOME": str(self.base_path / "cc65"),
                    "PATH": str(self.base_path / "cc65" / "bin")
                },
                download_url="https://github.com/cc65/cc65/releases/latest",
                install_commands=[
                    "git clone https://github.com/cc65/cc65.git",
                    "cd cc65 && make",
                    "make install PREFIX=" + str(self.base_path / "cc65")
                ],
                verification_commands=["cc65 --version", "ca65 --version"],
                emulators=["fceux", "nestopia", "mesen"],
                docker_support=True
            ),
            
            "atari2600": DevKitInfo(
                name="Atari 2600 Development Kit",
                console="Atari 2600",
                generation=ConsoleGeneration.BIT_8,
                console_type=ConsoleType.HOME,
                devkit_name="8BitWorkshop + Stella SDK",
                dependencies=["cc65", "stella", "make"],
                environment_vars={
                    "STELLA_HOME": str(self.base_path / "stella"),
                    "CC65_HOME": str(self.base_path / "cc65")
                },
                download_url="https://github.com/stella-emu/stella/releases/latest",
                install_commands=[
                    "wget https://github.com/stella-emu/stella/releases/latest/download/stella-win64.exe",
                    "mkdir -p stella && mv stella-win64.exe stella/"
                ],
                verification_commands=["stella --version"],
                emulators=["stella", "z26"],
                docker_support=True
            ),
            
            "mastersystem": DevKitInfo(
                name="Master System Development Kit",
                console="Sega Master System",
                generation=ConsoleGeneration.BIT_8,
                console_type=ConsoleType.HOME,
                devkit_name="DevKitSMS",
                dependencies=["sdcc", "make", "python3"],
                environment_vars={
                    "DEVKITSMS": str(self.base_path / "devkitsms"),
                    "SDCC_HOME": str(self.base_path / "sdcc")
                },
                download_url="https://github.com/sverx/devkitSMS/releases/latest",
                install_commands=[
                    "git clone https://github.com/sverx/devkitSMS.git",
                    "cd devkitSMS && make install"
                ],
                verification_commands=["sdcc --version"],
                emulators=["fusion", "blastem", "meka"],
                docker_support=True
            )
        } 
   
    def _get_8bit_portable_devkits(self) -> Dict[str, DevKitInfo]:
        """Devkits para consoles portáteis de 8-bit"""
        return {
            "gameboy": DevKitInfo(
                name="Game Boy Development Kit",
                console="Nintendo Game Boy / Game Boy Color",
                generation=ConsoleGeneration.BIT_8,
                console_type=ConsoleType.PORTABLE,
                devkit_name="GBDK-2020",
                dependencies=["gbdk-2020", "make", "python3"],
                environment_vars={
                    "GBDK_HOME": str(self.base_path / "gbdk"),
                    "PATH": str(self.base_path / "gbdk" / "bin")
                },
                download_url="https://github.com/gbdk-2020/gbdk-2020/releases/latest",
                install_commands=[
                    "wget https://github.com/gbdk-2020/gbdk-2020/releases/latest/download/gbdk-win64.zip",
                    "unzip gbdk-win64.zip -d gbdk",
                    "chmod +x gbdk/bin/*"
                ],
                verification_commands=["lcc --version", "gbdk-n --version"],
                emulators=["bgb", "sameboy", "gambatte"],
                docker_support=True
            ),
            
            "neogeopocket": DevKitInfo(
                name="Neo Geo Pocket Development Kit",
                console="Neo Geo Pocket / Color",
                generation=ConsoleGeneration.BIT_8,
                console_type=ConsoleType.PORTABLE,
                devkit_name="NGPC-SDK",
                dependencies=["gcc-tlcs900", "make"],
                environment_vars={
                    "NGPC_SDK": str(self.base_path / "ngpc-sdk"),
                    "TLCS900_HOME": str(self.base_path / "tlcs900")
                },
                download_url="https://github.com/sodthor/ngpcdev/releases/latest",
                install_commands=[
                    "git clone https://github.com/sodthor/ngpcdev.git ngpc-sdk",
                    "cd ngpc-sdk && make install"
                ],
                verification_commands=["tlcs900-gcc --version"],
                emulators=["race", "mednafen"],
                docker_support=True
            ),
            
            "wonderswan": DevKitInfo(
                name="WonderSwan Development Kit",
                console="Bandai WonderSwan / Color",
                generation=ConsoleGeneration.BIT_8,
                console_type=ConsoleType.PORTABLE,
                devkit_name="WSC-SDK",
                dependencies=["gcc-tlcs900", "cygwin", "make"],
                environment_vars={
                    "WSC_SDK": str(self.base_path / "wsc-sdk"),
                    "CYGWIN_HOME": str(self.base_path / "cygwin")
                },
                download_url="https://github.com/WonderfulToolchain/wonderful-i8086/releases/latest",
                install_commands=[
                    "git clone https://github.com/WonderfulToolchain/wonderful-i8086.git wsc-sdk",
                    "cd wsc-sdk && make install"
                ],
                verification_commands=["ia16-elf-gcc --version"],
                emulators=["oswan", "mednafen"],
                docker_support=True
            )
        }
    
    def _get_16bit_home_devkits(self) -> Dict[str, DevKitInfo]:
        """Devkits para consoles domésticos de 16-bit"""
        return {
            "snes": DevKitInfo(
                name="Super Nintendo Development Kit",
                console="Super Nintendo Entertainment System",
                generation=ConsoleGeneration.BIT_16,
                console_type=ConsoleType.HOME,
                devkit_name="libSFX + ca65",
                dependencies=["ca65", "cc65", "make", "python3"],
                environment_vars={
                    "LIBSFX_HOME": str(self.base_path / "libsfx"),
                    "CA65_HOME": str(self.base_path / "ca65")
                },
                download_url="https://github.com/Optiroc/libSFX/releases/latest",
                install_commands=[
                    "git clone https://github.com/Optiroc/libSFX.git",
                    "cd libSFX && make install"
                ],
                verification_commands=["ca65 --version"],
                emulators=["bsnes", "snes9x", "higan"],
                docker_support=True
            ),
            
            "megadrive": DevKitInfo(
                name="Sega Mega Drive Development Kit",
                console="Sega Mega Drive / Genesis",
                generation=ConsoleGeneration.BIT_16,
                console_type=ConsoleType.HOME,
                devkit_name="SGDK",
                dependencies=["gcc-m68k", "make", "java"],
                environment_vars={
                    "GDK": str(self.base_path / "sgdk"),
                    "GDK_WIN": str(self.base_path / "sgdk"),
                    "JAVA_HOME": str(self.base_path / "java")
                },
                download_url="https://github.com/Stephane-D/SGDK/releases/latest",
                install_commands=[
                    "wget https://github.com/Stephane-D/SGDK/releases/latest/download/sgdk.zip",
                    "unzip sgdk.zip -d sgdk",
                    "chmod +x sgdk/bin/*"
                ],
                verification_commands=["m68k-elf-gcc --version"],
                emulators=["blastem", "gens", "fusion"],
                docker_support=True
            ),
            
            "neogeo": DevKitInfo(
                name="Neo Geo Development Kit",
                console="SNK Neo Geo",
                generation=ConsoleGeneration.BIT_16,
                console_type=ConsoleType.HOME,
                devkit_name="NGDevKit",
                dependencies=["gcc-m68k", "gcc-z80", "gtk", "make"],
                environment_vars={
                    "NGDEVKIT": str(self.base_path / "ngdevkit"),
                    "M68K_HOME": str(self.base_path / "m68k"),
                    "Z80_HOME": str(self.base_path / "z80")
                },
                download_url="https://github.com/dciabrin/ngdevkit/releases/latest",
                install_commands=[
                    "git clone https://github.com/dciabrin/ngdevkit.git",
                    "cd ngdevkit && make install"
                ],
                verification_commands=["m68k-neogeo-elf-gcc --version", "z80-elf-gcc --version"],
                emulators=["mame", "nebula", "kawaks"],
                docker_support=True
            )
        }
    
    def _get_16bit_portable_devkits(self) -> Dict[str, DevKitInfo]:
        """Devkits para consoles portáteis de 16-bit"""
        return {
            "atarilynx": DevKitInfo(
                name="Atari Lynx Development Kit",
                console="Atari Lynx",
                generation=ConsoleGeneration.BIT_16,
                console_type=ConsoleType.PORTABLE,
                devkit_name="Lynx-SDK (BLL) + cc65",
                dependencies=["cc65", "make", "python3"],
                environment_vars={
                    "LYNX_SDK": str(self.base_path / "lynx-sdk"),
                    "CC65_HOME": str(self.base_path / "cc65")
                },
                download_url="https://github.com/cc65/cc65/releases/latest",
                install_commands=[
                    "git clone https://github.com/cc65/cc65.git",
                    "cd cc65 && make lynx",
                    "make install PREFIX=" + str(self.base_path / "lynx-sdk")
                ],
                verification_commands=["cc65 --version"],
                emulators=["handy", "mednafen"],
                docker_support=True
            ),
            
            "pcengine": DevKitInfo(
                name="PC-Engine Development Kit",
                console="NEC PC-Engine / TurboGrafx-16",
                generation=ConsoleGeneration.BIT_16,
                console_type=ConsoleType.PORTABLE,
                devkit_name="HuC + PCEDev",
                dependencies=["huc", "make", "python3"],
                environment_vars={
                    "HUC_HOME": str(self.base_path / "huc"),
                    "PCEDEV_HOME": str(self.base_path / "pcedev")
                },
                download_url="https://github.com/uli/huc/releases/latest",
                install_commands=[
                    "git clone https://github.com/uli/huc.git",
                    "cd huc && make install"
                ],
                verification_commands=["huc --version"],
                emulators=["mednafen", "ootake", "magic-engine"],
                docker_support=True
            )
        }  
  
    def _get_32bit_home_devkits(self) -> Dict[str, DevKitInfo]:
        """Devkits para consoles domésticos de 32-bit"""
        return {
            "playstation1": DevKitInfo(
                name="PlayStation 1 Development Kit",
                console="Sony PlayStation 1",
                generation=ConsoleGeneration.BIT_32,
                console_type=ConsoleType.HOME,
                devkit_name="PSn00bSDK",
                dependencies=["gcc-mips", "mkpsxiso", "make", "cmake"],
                environment_vars={
                    "PSN00BSDK": str(self.base_path / "psn00bsdk"),
                    "MIPS_HOME": str(self.base_path / "mips-toolchain")
                },
                download_url="https://github.com/Lameguy64/PSn00bSDK/releases/latest",
                install_commands=[
                    "git clone https://github.com/Lameguy64/PSn00bSDK.git psn00bsdk",
                    "cd psn00bsdk && cmake . && make install"
                ],
                verification_commands=["mipsel-none-elf-gcc --version", "mkpsxiso --version"],
                emulators=["duckstation", "epsxe", "mednafen"],
                docker_support=True
            ),
            
            "saturn": DevKitInfo(
                name="Sega Saturn Development Kit",
                console="Sega Saturn",
                generation=ConsoleGeneration.BIT_32,
                console_type=ConsoleType.HOME,
                devkit_name="Jo-Engine + Yaul",
                dependencies=["gcc-sh2", "make", "cmake"],
                environment_vars={
                    "JO_ENGINE_HOME": str(self.base_path / "jo-engine"),
                    "YAUL_HOME": str(self.base_path / "yaul"),
                    "SH2_HOME": str(self.base_path / "sh2-toolchain")
                },
                download_url="https://github.com/johannes-fetz/joengine/releases/latest",
                install_commands=[
                    "git clone https://github.com/johannes-fetz/joengine.git jo-engine",
                    "git clone https://github.com/yaul-org/yaul.git",
                    "cd yaul && make install-toolchain"
                ],
                verification_commands=["sh2-elf-gcc --version"],
                emulators=["mednafen", "ssf", "kronos"],
                docker_support=True
            ),
            
            "nintendo64": DevKitInfo(
                name="Nintendo 64 Development Kit",
                console="Nintendo 64",
                generation=ConsoleGeneration.BIT_32,
                console_type=ConsoleType.HOME,
                devkit_name="libdragon",
                dependencies=["gcc-mips64", "make", "cmake", "python3"],
                environment_vars={
                    "N64_INST": str(self.base_path / "n64-toolchain"),
                    "LIBDRAGON_HOME": str(self.base_path / "libdragon")
                },
                download_url="https://github.com/DragonMinded/libdragon/releases/latest",
                install_commands=[
                    "git clone https://github.com/DragonMinded/libdragon.git",
                    "cd libdragon && ./build.sh",
                    "make install"
                ],
                verification_commands=["mips64-elf-gcc --version"],
                emulators=["ares", "mupen64plus", "project64"],
                docker_support=True
            )
        }
    
    def _get_32bit_portable_devkits(self) -> Dict[str, DevKitInfo]:
        """Devkits para consoles portáteis de 32-bit"""
        return {
            "psp": DevKitInfo(
                name="PlayStation Portable Development Kit",
                console="Sony PlayStation Portable",
                generation=ConsoleGeneration.BIT_32,
                console_type=ConsoleType.PORTABLE,
                devkit_name="PSPSDK",
                dependencies=["gcc-mips", "cmake", "make", "python3"],
                environment_vars={
                    "PSPDEV": str(self.base_path / "pspdev"),
                    "PSPSDK": str(self.base_path / "pspdev" / "psp" / "sdk"),
                    "PATH": str(self.base_path / "pspdev" / "bin")
                },
                download_url="https://github.com/pspdev/psptoolchain/releases/latest",
                install_commands=[
                    "git clone https://github.com/pspdev/psptoolchain.git",
                    "cd psptoolchain && ./toolchain.sh"
                ],
                verification_commands=["psp-gcc --version", "psp-config --version"],
                emulators=["ppsspp", "jpcsp"],
                docker_support=True
            ),
            
            "nds": DevKitInfo(
                name="Nintendo DS Development Kit",
                console="Nintendo DS",
                generation=ConsoleGeneration.BIT_32,
                console_type=ConsoleType.PORTABLE,
                devkit_name="devkitARM + libnds",
                dependencies=["devkitpro", "make", "cmake"],
                environment_vars={
                    "DEVKITPRO": str(self.base_path / "devkitpro"),
                    "DEVKITARM": str(self.base_path / "devkitpro" / "devkitARM"),
                    "LIBNDS": str(self.base_path / "devkitpro" / "libnds")
                },
                download_url="https://github.com/devkitPro/installer/releases/latest",
                install_commands=[
                    "wget https://github.com/devkitPro/installer/releases/latest/download/devkitProUpdater-3.0.4.exe",
                    "wine devkitProUpdater-3.0.4.exe /S"
                ],
                verification_commands=["arm-none-eabi-gcc --version"],
                emulators=["desmume", "melonds", "no$gba"],
                docker_support=True
            ),
            
            "gba": DevKitInfo(
                name="Game Boy Advance Development Kit",
                console="Nintendo Game Boy Advance",
                generation=ConsoleGeneration.BIT_32,
                console_type=ConsoleType.PORTABLE,
                devkit_name="devkitARM + libgba",
                dependencies=["devkitpro", "make", "cmake"],
                environment_vars={
                    "DEVKITPRO": str(self.base_path / "devkitpro"),
                    "DEVKITARM": str(self.base_path / "devkitpro" / "devkitARM"),
                    "LIBGBA": str(self.base_path / "devkitpro" / "libgba")
                },
                download_url="https://github.com/devkitPro/installer/releases/latest",
                install_commands=[
                    "wget https://github.com/devkitPro/installer/releases/latest/download/devkitProUpdater-3.0.4.exe",
                    "wine devkitProUpdater-3.0.4.exe /S"
                ],
                verification_commands=["arm-none-eabi-gcc --version"],
                emulators=["mgba", "vba-m", "no$gba"],
                docker_support=True
            )
        }
    
    def install_devkit(self, devkit_id: str, use_docker: bool = False) -> bool:
        """
        Instala um devkit específico com todas as dependências
        
        Args:
            devkit_id: ID do devkit (ex: 'gameboy', 'snes', 'psp')
            use_docker: Se deve usar Docker para instalação isolada
            
        Returns:
            bool: True se instalação foi bem-sucedida
        """
        if devkit_id not in self.devkits:
            self.logger.error(f"DevKit '{devkit_id}' não encontrado")
            return False
            
        devkit = self.devkits[devkit_id]
        self.logger.info(f"Iniciando instalação do {devkit.name}")
        
        try:
            # Criar diretório base
            devkit_path = self.base_path / devkit_id
            devkit_path.mkdir(parents=True, exist_ok=True)
            
            if use_docker and devkit.docker_support:
                return self._install_with_docker(devkit, devkit_path)
            else:
                return self._install_native(devkit, devkit_path)
                
        except Exception as e:
            self.logger.error(f"Erro na instalação do {devkit.name}: {e}")
            return False
    
    def _install_native(self, devkit: DevKitInfo, install_path: Path) -> bool:
        """Instalação nativa do devkit"""
        self.logger.info(f"Instalação nativa do {devkit.name}")
        
        # Instalar dependências do sistema
        if not self._install_system_dependencies(devkit.dependencies):
            return False
            
        # Executar comandos de instalação
        original_cwd = os.getcwd()
        try:
            os.chdir(install_path)
            
            for command in devkit.install_commands:
                self.logger.info(f"Executando: {command}")
                result = subprocess.run(
                    command, 
                    shell=True, 
                    capture_output=True, 
                    text=True
                )
                
                if result.returncode != 0:
                    self.logger.error(f"Comando falhou: {command}")
                    self.logger.error(f"Erro: {result.stderr}")
                    return False
                    
        finally:
            os.chdir(original_cwd)
            
        # Configurar variáveis de ambiente
        self._setup_environment_variables(devkit)
        
        # Verificar instalação
        return self._verify_installation(devkit)
    
    def _install_with_docker(self, devkit: DevKitInfo, install_path: Path) -> bool:
        """Instalação usando Docker para isolamento"""
        self.logger.info(f"Instalação Docker do {devkit.name}")
        
        dockerfile_content = self._generate_dockerfile(devkit)
        dockerfile_path = install_path / "Dockerfile"
        
        with open(dockerfile_path, 'w') as f:
            f.write(dockerfile_content)
            
        # Build da imagem Docker
        image_name = f"retro-devkit-{devkit.console.lower().replace(' ', '-')}"
        
        build_cmd = f"docker build -t {image_name} {install_path}"
        result = subprocess.run(build_cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0:
            self.logger.error(f"Falha no build Docker: {result.stderr}")
            return False
            
        # Criar script de wrapper
        self._create_docker_wrapper(devkit, image_name, install_path)
        
        return True
    
    def _install_system_dependencies(self, dependencies: List[str]) -> bool:
        """Instala dependências do sistema"""
        self.logger.info("Instalando dependências do sistema")
        
        # Detectar gerenciador de pacotes
        package_managers = {
            'apt': ['apt-get', 'install', '-y'],
            'yum': ['yum', 'install', '-y'],
            'dnf': ['dnf', 'install', '-y'],
            'pacman': ['pacman', '-S', '--noconfirm'],
            'brew': ['brew', 'install'],
            'choco': ['choco', 'install', '-y'],
            'winget': ['winget', 'install']
        }
        
        active_pm = None
        for pm in package_managers:
            if shutil.which(pm):
                active_pm = pm
                break
                
        if not active_pm:
            self.logger.warning("Nenhum gerenciador de pacotes encontrado")
            return True  # Continuar mesmo assim
            
        # Mapear dependências para nomes de pacotes específicos
        package_mapping = self._get_package_mapping(active_pm)
        
        for dep in dependencies:
            if dep in package_mapping:
                package_name = package_mapping[dep]
                cmd = package_managers[active_pm] + [package_name]
                
                self.logger.info(f"Instalando {package_name}")
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode != 0:
                    self.logger.warning(f"Falha ao instalar {package_name}: {result.stderr}")
                    
        return True
    
    def _get_package_mapping(self, package_manager: str) -> Dict[str, str]:
        """Mapeia dependências para nomes de pacotes específicos do PM"""
        mappings = {
            'apt': {
                'cc65': 'cc65',
                'sdcc': 'sdcc',
                'make': 'build-essential',
                'cmake': 'cmake',
                'python3': 'python3',
                'java': 'openjdk-11-jdk',
                'gcc-m68k': 'gcc-m68hc1x',
                'gcc-mips': 'gcc-mips-linux-gnu',
                'gcc-mips64': 'gcc-mips64-linux-gnuabi64',
                'gcc-sh2': 'gcc-sh4-linux-gnu',
                'devkitpro': 'devkitpro-pacman',
                'wine': 'wine'
            },
            'choco': {
                'cc65': 'cc65',
                'make': 'make',
                'cmake': 'cmake',
                'python3': 'python3',
                'java': 'openjdk11',
                'git': 'git',
                'wget': 'wget',
                'wine': 'wine'
            },
            'brew': {
                'cc65': 'cc65',
                'sdcc': 'sdcc',
                'make': 'make',
                'cmake': 'cmake',
                'python3': 'python3',
                'java': 'openjdk@11'
            }
        }
        
        return mappings.get(package_manager, {})
    
    def _setup_environment_variables(self, devkit: DevKitInfo) -> None:
        """Configura variáveis de ambiente permanentemente"""
        self.logger.info("Configurando variáveis de ambiente")
        
        # Windows
        if os.name == 'nt':
            for var, value in devkit.environment_vars.items():
                # Adicionar ao PATH se necessário
                if var == 'PATH':
                    current_path = os.environ.get('PATH', '')
                    if value not in current_path:
                        new_path = f"{current_path};{value}"
                        subprocess.run(['setx', 'PATH', new_path], check=False)
                else:
                    subprocess.run(['setx', var, value], check=False)
                    
        # Unix-like
        else:
            profile_files = [
                Path.home() / '.bashrc',
                Path.home() / '.zshrc',
                Path.home() / '.profile'
            ]
            
            for profile in profile_files:
                if profile.exists():
                    with open(profile, 'a') as f:
                        f.write(f"\n# {devkit.name} Environment Variables\n")
                        for var, value in devkit.environment_vars.items():
                            if var == 'PATH':
                                f.write(f'export PATH="{value}:$PATH"\n')
                            else:
                                f.write(f'export {var}="{value}"\n')
                    break
    
    def _verify_installation(self, devkit: DevKitInfo) -> bool:
        """Verifica se a instalação foi bem-sucedida"""
        self.logger.info(f"Verificando instalação do {devkit.name}")
        
        for command in devkit.verification_commands:
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True
            )
            
            if result.returncode != 0:
                self.logger.error(f"Verificação falhou para: {command}")
                return False
                
        self.logger.info(f"✅ {devkit.name} instalado com sucesso!")
        return True
    
    def _generate_dockerfile(self, devkit: DevKitInfo) -> str:
        """Gera Dockerfile para instalação isolada"""
        base_image = "ubuntu:20.04"
        
        dockerfile = f"""FROM {base_image}

# Configurar timezone para evitar prompts interativos
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# Instalar dependências básicas
RUN apt-get update && apt-get install -y \\
    build-essential \\
    git \\
    wget \\
    curl \\
    unzip \\
    python3 \\
    python3-pip \\
    cmake \\
    && rm -rf /var/lib/apt/lists/*

# Instalar dependências específicas do devkit
RUN apt-get update && apt-get install -y \\
    {' '.join(self._get_package_mapping('apt').get(dep, dep) for dep in devkit.dependencies)} \\
    && rm -rf /var/lib/apt/lists/*

# Configurar diretório de trabalho
WORKDIR /devkit

# Configurar variáveis de ambiente
"""
        
        for var, value in devkit.environment_vars.items():
            dockerfile += f"ENV {var}={value}\n"
            
        dockerfile += """
# Comandos de instalação específicos
"""
        
        for command in devkit.install_commands:
            dockerfile += f"RUN {command}\n"
            
        dockerfile += """
# Criar ponto de entrada
ENTRYPOINT ["/bin/bash"]
"""
        
        return dockerfile
    
    def _create_docker_wrapper(self, devkit: DevKitInfo, image_name: str, install_path: Path) -> None:
        """Cria script wrapper para usar o devkit via Docker"""
        wrapper_script = install_path / f"{devkit.console.lower().replace(' ', '_')}_dev.sh"
        
        script_content = f"""#!/bin/bash
# Wrapper script for {devkit.name}

CURRENT_DIR=$(pwd)
DEVKIT_IMAGE="{image_name}"

# Executar container com volume montado
docker run -it --rm \\
    -v "$CURRENT_DIR:/workspace" \\
    -w /workspace \\
    $DEVKIT_IMAGE \\
    "$@"
"""
        
        with open(wrapper_script, 'w') as f:
            f.write(script_content)
            
        # Tornar executável
        wrapper_script.chmod(0o755)
        
        self.logger.info(f"Script wrapper criado: {wrapper_script}")
    
    def install_all_devkits(self, use_docker: bool = False) -> Dict[str, bool]:
        """
        Instala todos os devkits disponíveis
        
        Args:
            use_docker: Se deve usar Docker para todas as instalações
            
        Returns:
            Dict[str, bool]: Status de instalação para cada devkit
        """
        results = {}
        
        self.logger.info("Iniciando instalação de todos os devkits")
        
        for devkit_id in self.devkits:
            self.logger.info(f"Instalando {devkit_id}...")
            results[devkit_id] = self.install_devkit(devkit_id, use_docker)
            
        # Relatório final
        successful = sum(1 for success in results.values() if success)
        total = len(results)
        
        self.logger.info(f"Instalação concluída: {successful}/{total} devkits instalados com sucesso")
        
        return results
    
    def list_available_devkits(self) -> Dict[str, Dict]:
        """Lista todos os devkits disponíveis organizados por categoria"""
        categories = {
            "8-bit Home Consoles": [],
            "8-bit Portable Consoles": [],
            "16-bit Home Consoles": [],
            "16-bit Portable Consoles": [],
            "32-bit Home Consoles": [],
            "32-bit Portable Consoles": []
        }
        
        for devkit_id, devkit in self.devkits.items():
            category_key = f"{devkit.generation.value} {devkit.console_type.value.title()} Consoles"
            
            categories[category_key].append({
                "id": devkit_id,
                "name": devkit.name,
                "console": devkit.console,
                "devkit": devkit.devkit_name,
                "emulators": devkit.emulators,
                "docker_support": devkit.docker_support
            })
            
        return categories
    
    def get_installation_status(self) -> Dict[str, bool]:
        """Verifica status de instalação de todos os devkits"""
        status = {}
        
        for devkit_id, devkit in self.devkits.items():
            # Verificar se comandos de verificação funcionam
            is_installed = True
            for command in devkit.verification_commands:
                result = subprocess.run(
                    command, 
                    shell=True, 
                    capture_output=True, 
                    text=True
                )
                if result.returncode != 0:
                    is_installed = False
                    break
                    
            status[devkit_id] = is_installed
            
        return status
    
    def uninstall_devkit(self, devkit_id: str) -> bool:
        """Remove um devkit instalado"""
        if devkit_id not in self.devkits:
            self.logger.error(f"DevKit '{devkit_id}' não encontrado")
            return False
            
        devkit_path = self.base_path / devkit_id
        
        try:
            if devkit_path.exists():
                shutil.rmtree(devkit_path)
                self.logger.info(f"DevKit {devkit_id} removido com sucesso")
                return True
            else:
                self.logger.warning(f"Diretório do DevKit {devkit_id} não encontrado")
                return True
                
        except Exception as e:
            self.logger.error(f"Erro ao remover DevKit {devkit_id}: {e}")
            return False
    
    def create_project_template(self, devkit_id: str, project_name: str, project_path: str = None) -> bool:
        """Cria template de projeto para um devkit específico"""
        if devkit_id not in self.devkits:
            self.logger.error(f"DevKit '{devkit_id}' não encontrado")
            return False
            
        devkit = self.devkits[devkit_id]
        
        if not project_path:
            project_path = Path.cwd() / project_name
        else:
            project_path = Path(project_path)
            
        project_path.mkdir(parents=True, exist_ok=True)
        
        # Criar estrutura básica do projeto
        self._create_basic_project_structure(devkit, project_path, project_name)
        
        self.logger.info(f"Template de projeto criado em: {project_path}")
        return True
    
    def _create_basic_project_structure(self, devkit: DevKitInfo, project_path: Path, project_name: str) -> None:
        """Cria estrutura básica de projeto para o devkit"""
        # Criar diretórios
        (project_path / "src").mkdir(exist_ok=True)
        (project_path / "assets").mkdir(exist_ok=True)
        (project_path / "build").mkdir(exist_ok=True)
        
        # Criar Makefile básico
        makefile_content = self._generate_makefile_template(devkit, project_name)
        with open(project_path / "Makefile", 'w', encoding='utf-8') as f:
            f.write(makefile_content)
            
        # Criar arquivo fonte principal
        main_file_content = self._generate_main_file_template(devkit, project_name)
        main_file_ext = self._get_main_file_extension(devkit)
        
        with open(project_path / f"src/main.{main_file_ext}", 'w', encoding='utf-8') as f:
            f.write(main_file_content)
            
        # Criar README
        readme_content = self._generate_readme_template(devkit, project_name)
        with open(project_path / "README.md", 'w', encoding='utf-8') as f:
            f.write(readme_content)
    
    def _generate_makefile_template(self, devkit: DevKitInfo, project_name: str) -> str:
        """Gera template de Makefile para o devkit"""
        return f"""# Makefile for {project_name} - {devkit.console}
# Generated by RetroDevKitManager

PROJECT_NAME = {project_name}
SRC_DIR = src
BUILD_DIR = build
ASSETS_DIR = assets

# DevKit specific settings for {devkit.devkit_name}
# Add your compiler flags and settings here

.PHONY: all clean build run

all: build

build:
\t@echo "Building $(PROJECT_NAME) for {devkit.console}..."
\t# Add your build commands here

clean:
\t@echo "Cleaning build files..."
\trm -rf $(BUILD_DIR)/*

run: build
\t@echo "Running $(PROJECT_NAME)..."
\t# Add your run/emulator commands here

help:
\t@echo "Available targets:"
\t@echo "  build  - Build the project"
\t@echo "  clean  - Clean build files"
\t@echo "  run    - Build and run in emulator"
\t@echo "  help   - Show this help"
"""
    
    def _generate_main_file_template(self, devkit: DevKitInfo, project_name: str) -> str:
        """Gera template de arquivo principal para o devkit"""
        if "gameboy" in devkit.console.lower():
            return f"""// {project_name} - Game Boy Development
// Generated by RetroDevKitManager

#include <gb/gb.h>
#include <stdio.h>

void main() {{
    printf("Hello from {project_name}!");
    
    // Main game loop
    while(1) {{
        wait_vbl_done();
    }}
}}
"""
        elif "nes" in devkit.console.lower():
            return f"""// {project_name} - NES Development
// Generated by RetroDevKitManager

#include <nes.h>

int main() {{
    // Initialize NES
    ppu_off();
    
    // Your game code here
    
    ppu_on_all();
    
    // Main loop
    while(1) {{
        ppu_wait_nmi();
    }}
    
    return 0;
}}
"""
        else:
            return f"""// {project_name} - {devkit.console} Development
// Generated by RetroDevKitManager

int main() {{
    // Initialize system
    
    // Your game code here
    
    // Main loop
    while(1) {{
        // Game logic
    }}
    
    return 0;
}}
"""
    
    def _get_main_file_extension(self, devkit: DevKitInfo) -> str:
        """Retorna extensão apropriada para arquivo principal"""
        if "assembly" in devkit.devkit_name.lower() or "asm" in devkit.devkit_name.lower():
            return "s"
        else:
            return "c"
    
    def _generate_readme_template(self, devkit: DevKitInfo, project_name: str) -> str:
        """Gera template de README para o projeto"""
        return f"""# {project_name}

Projeto de desenvolvimento para **{devkit.console}** usando **{devkit.devkit_name}**.

## Requisitos

- {devkit.devkit_name}
- Dependências: {', '.join(devkit.dependencies)}
- Emuladores recomendados: {', '.join(devkit.emulators)}

## Compilação

```bash
make build
```

## Execução

```bash
make run
```

## Estrutura do Projeto

```
{project_name}/
├── src/           # Código fonte
├── assets/        # Recursos (gráficos, sons, etc.)
├── build/         # Arquivos compilados
├── Makefile       # Script de compilação
└── README.md      # Este arquivo
```

## Variáveis de Ambiente

As seguintes variáveis de ambiente devem estar configuradas:

{chr(10).join(f'- `{var}`: {value}' for var, value in devkit.environment_vars.items())}

---

Gerado automaticamente pelo RetroDevKitManager
"""


# Exemplo de uso
if __name__ == "__main__":
    manager = RetroDevKitManager()
    
    # Listar devkits disponíveis
    print("DevKits Disponíveis:")
    categories = manager.list_available_devkits()
    for category, devkits in categories.items():
        if devkits:  # Só mostrar categorias com devkits
            print(f"\n{category}:")
            for devkit in devkits:
                print(f"  - {devkit['id']}: {devkit['name']}")
    
    # Verificar status de instalação
    print("\nStatus de Instalação:")
    status = manager.get_installation_status()
    for devkit_id, installed in status.items():
        status_icon = "✅" if installed else "❌"
        print(f"  {status_icon} {devkit_id}")