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
import platform
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


def verify_sgdk_installation(base_path: Path) -> bool:
    """Verificação específica e robusta para SGDK"""
    sgdk_path = base_path / "retro_devkits" / "sgdk"
    
    # Verificar se diretório principal existe
    if not sgdk_path.exists():
        return False
    
    # Arquivos essenciais para verificar
    essential_files = [
        sgdk_path / "inc" / "genesis.h",
        sgdk_path / "bin" / "rescomp.jar",
        sgdk_path / "makefile.gen",
        sgdk_path / "common.mk"
    ]
    
    # Verificar arquivos essenciais
    for file_path in essential_files:
        if not file_path.exists():
            return False
    
    # Verificar se há pelo menos alguns arquivos de biblioteca
    lib_path = sgdk_path / "lib"
    if lib_path.exists():
        lib_files = list(lib_path.glob("*.a"))
        if len(lib_files) == 0:
            return False
    
    # Verificar se há arquivos de include
    inc_path = sgdk_path / "inc"
    if inc_path.exists():
        inc_files = list(inc_path.glob("*.h"))
        if len(inc_files) < 5:  # Deve ter pelo menos alguns headers
            return False
    
    return True


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
                # CORREÇÃO: Dependências mais específicas e completas
                dependencies=["gcc-m68k-elf", "make", "java", "unzip", "wget", "p7zip-full"],
                environment_vars={
                    "GDK": str(self.base_path / "sgdk"),
                    "GDK_WIN": str(self.base_path / "sgdk"),
                    "JAVA_HOME": self._detect_java_home(),
                    "PATH": str(self.base_path / "sgdk" / "bin")  # Adicionar bin ao PATH
                },
                # CORREÇÃO: URL com sistema de fallback para versões
                download_url="https://github.com/Stephane-D/SGDK/releases/latest",
                # CORREÇÃO: Comandos melhorados com tratamento de erros e fallback
                install_commands=self._get_sgdk_install_commands_with_fallback(),
                # CORREÇÃO: Verificações mais robustas
                verification_commands=[
                    "java -version",
                    "make --version",
                    f"file_exists:{self.base_path / 'retro_devkits' / 'sgdk' / 'bin' / 'rescomp.jar'}",
                    f"file_exists:{self.base_path / 'retro_devkits' / 'sgdk' / 'inc' / 'genesis.h'}",
                    f"file_exists:{self.base_path / 'retro_devkits' / 'sgdk' / 'bin' / 'gcc' / 'bin' / 'm68k-elf-gcc.exe'}"
                ],
                emulators=["blastem", "gens", "fusion", "retroarch"],
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
        """Instalação nativa do devkit com robustez aprimorada"""
        self.logger.info(f"🚀 Iniciando instalação nativa do {devkit.name}")
        
        # Instalar dependências do sistema com retry
        self.logger.info("📦 Verificando e instalando dependências do sistema...")
        for attempt in range(3):
            if self._install_system_dependencies(devkit.dependencies):
                self.logger.info("✅ Dependências do sistema instaladas com sucesso!")
                break
            else:
                self.logger.warning(f"⚠️ Tentativa {attempt+1}/3 falhou. Tentando novamente...")
        else:
            self.logger.error("❌ Falha na instalação de dependências do sistema após 3 tentativas")
            return False
            
        # Executar comandos de instalação com retry e verificação
        self.logger.info(f"⚙️ Executando comandos de instalação do {devkit.name}...")
        original_cwd = os.getcwd()
        try:
            os.chdir(install_path)
            
            total_commands = len(devkit.install_commands)
            for i, command in enumerate(devkit.install_commands, 1):
                self.logger.info(f"📋 [{i}/{total_commands}] Executando: {command}")
                success = False
                for attempt in range(3):
                    try:
                        result = subprocess.run(
                            command, 
                            shell=True, 
                            capture_output=True, 
                            text=True,
                            timeout=600
                        )
                        if result.returncode == 0:
                            self.logger.info(f"✅ [{i}/{total_commands}] Comando executado com sucesso")
                            if result.stdout.strip():
                                self.logger.debug(f"Saída: {result.stdout.strip()}")
                            success = True
                            break
                        else:
                            self.logger.warning(f"⚠️ [{i}/{total_commands}] Tentativa {attempt+1}/3 falhou: Código {result.returncode}")
                            if result.stderr:
                                self.logger.warning(f"Erro: {result.stderr}")
                    except subprocess.TimeoutExpired:
                        self.logger.warning(f"⏰ [{i}/{total_commands}] Timeout na tentativa {attempt+1}/3")
                    except Exception as e:
                        self.logger.warning(f"💥 [{i}/{total_commands}] Erro na tentativa {attempt+1}/3: {str(e)}")
                if not success:
                    self.logger.error(f"❌ Falha no comando após 3 tentativas: {command}")
                    return False
                    
        finally:
            os.chdir(original_cwd)
            
        # Configurar variáveis de ambiente
        self._setup_environment_variables(devkit)
        
        # Instalar emuladores e extensões VS Code se for SGDK com verificação
        if devkit.console.lower() == "mega drive" or "sgdk" in devkit.name.lower():
            try:
                from .sgdk_improvements import SGDKInstaller
                sgdk_installer = SGDKInstaller(self.base_path, self.logger)
                
                if sgdk_installer.install_emulators():
                    self.logger.info("✅ Emuladores SGDK instalados com sucesso!")
                else:
                    self.logger.warning("⚠️ Falha na instalação de emuladores SGDK")
                
                if sgdk_installer.install_vscode_extensions():
                    self.logger.info("✅ Extensões VS Code para SGDK instaladas com sucesso!")
                else:
                    self.logger.warning("⚠️ Falha na instalação de extensões VS Code para SGDK")
                
            except Exception as e:
                self.logger.warning(f"⚠️ Erro ao instalar componentes adicionais do SGDK: {e}")
                self.logger.warning("A instalação do SGDK continuará sem os componentes adicionais")
        
        # Verificar instalação com diagnósticos aprimorados
        if self._verify_installation(devkit):
            return True
        else:
            self.logger.error("❌ Verificação da instalação falhou")
            return False
    
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
        
    def _check_dependency_robust(self, dependency: str) -> bool:
        """Verificação robusta de dependências instaladas"""
        # Mapeamento de comandos de verificação específicos
        check_commands = {
            'java': ['java', '-version'],
            'make': ['make', '--version'],
            'gcc': ['gcc', '--version'],
            'gcc-m68k-elf': ['m68k-elf-gcc', '--version'],
            '7z': ['7z'],
            'p7zip-full': ['7z'],
            'unzip': ['unzip', '-v'],
            'wget': ['wget', '--version'],
            'git': ['git', '--version'],
            'python3': ['python3', '--version'],
            'ca65': ['ca65', '--version'],
            'cc65': ['cc65', '--version']
        }
        
        # Verificar comando específico se disponível
        if dependency in check_commands:
            try:
                result = subprocess.run(
                    check_commands[dependency], 
                    capture_output=True, 
                    text=True, 
                    timeout=10
                )
                return result.returncode == 0
            except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
                return False
        
        # Verificação genérica usando which
        return shutil.which(dependency) is not None
    
    def _install_dependencies_manually(self, dependencies: List[str]) -> bool:
        """Instalação manual de dependências quando não há gerenciador de pacotes"""
        print("\n🔧 Tentando instalação manual de dependências...")
        
        manual_installers = {
            'java': self._install_java_manually,
            'make': self._install_make_manually,
            '7z': self._install_7z_manually
        }
        
        success_count = 0
        for dep in dependencies:
            if dep in manual_installers:
                print(f"🔧 Instalando {dep} manualmente...")
                if manual_installers[dep]():
                    print(f"✅ {dep} instalado manualmente")
                    success_count += 1
                else:
                    print(f"❌ Falha na instalação manual de {dep}")
            else:
                print(f"⚠️  Instalação manual de {dep} não implementada")
                
        return success_count > 0
    
    def _install_java_manually(self) -> bool:
        """Instalação manual robusta do Java"""
        try:
            if platform.system() == "Windows":
                # Tentar instalar OpenJDK via winget se disponível
                if shutil.which('winget'):
                    result = subprocess.run(
                        ['winget', 'install', 'Microsoft.OpenJDK.11'],
                        capture_output=True, text=True
                    )
                    return result.returncode == 0
                    
                # Fallback: baixar e instalar manualmente
                java_url = "https://download.java.net/java/GA/jdk11/9/GPL/openjdk-11.0.2_windows-x64_bin.zip"
                java_path = self.base_path / "java"
                return self._download_and_extract(java_url, java_path, "java")
            else:
                # Linux: tentar diferentes métodos
                commands = [
                    ['sudo', 'apt-get', 'update', '&&', 'sudo', 'apt-get', 'install', '-y', 'openjdk-11-jdk'],
                    ['sudo', 'yum', 'install', '-y', 'java-11-openjdk-devel'],
                    ['sudo', 'dnf', 'install', '-y', 'java-11-openjdk-devel']
                ]
                
                for cmd in commands:
                    try:
                        result = subprocess.run(cmd, capture_output=True, text=True)
                        if result.returncode == 0:
                            return True
                    except Exception:
                        continue
                        
        except Exception as e:
            self.logger.error(f"Erro na instalação manual do Java: {e}")
            
        return False
    
    def _install_make_manually(self) -> bool:
        """Instalação manual robusta do Make"""
        try:
            if platform.system() == "Windows":
                # Baixar make para Windows
                make_url = "http://gnuwin32.sourceforge.net/downlinks/make-bin-zip.php"
                make_path = self.base_path / "make"
                return self._download_and_extract(make_url, make_path, "make")
            else:
                # Linux: make geralmente vem com build-essential
                commands = [
                    ['sudo', 'apt-get', 'install', '-y', 'build-essential'],
                    ['sudo', 'yum', 'groupinstall', '-y', 'Development Tools'],
                    ['sudo', 'dnf', 'groupinstall', '-y', 'Development Tools']
                ]
                
                for cmd in commands:
                    try:
                        result = subprocess.run(cmd, capture_output=True, text=True)
                        if result.returncode == 0:
                            return True
                    except Exception:
                        continue
                        
        except Exception as e:
            self.logger.error(f"Erro na instalação manual do Make: {e}")
            
        return False
    
    def _install_7z_manually(self) -> bool:
        """Instalação manual robusta do 7-Zip"""
        try:
            if platform.system() == "Windows":
                # Baixar 7-Zip para Windows
                sevenzip_url = "https://www.7-zip.org/a/7z1900-x64.exe"
                sevenzip_path = self.base_path / "7zip"
                return self._download_and_install_exe(sevenzip_url, "7z1900-x64.exe")
            else:
                # Linux: instalar p7zip
                commands = [
                    ['sudo', 'apt-get', 'install', '-y', 'p7zip-full'],
                    ['sudo', 'yum', 'install', '-y', 'p7zip'],
                    ['sudo', 'dnf', 'install', '-y', 'p7zip']
                ]
                
                for cmd in commands:
                    try:
                        result = subprocess.run(cmd, capture_output=True, text=True)
                        if result.returncode == 0:
                            return True
                    except Exception:
                        continue
                        
        except Exception as e:
            self.logger.error(f"Erro na instalação manual do 7-Zip: {e}")
            
        return False
    
    def _download_and_extract(self, url: str, dest_path: Path, tool_name: str) -> bool:
        """Download e extração de ferramentas"""
        try:
            dest_path.mkdir(parents=True, exist_ok=True)
            filename = url.split('/')[-1]
            file_path = dest_path / filename
            
            print(f"📥 Baixando {tool_name}...")
            urllib.request.urlretrieve(url, file_path)
            
            print(f"📦 Extraindo {tool_name}...")
            if filename.endswith('.zip'):
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(dest_path)
            elif filename.endswith('.7z'):
                subprocess.run(['7z', 'x', str(file_path), f'-o{dest_path}'])
                
            file_path.unlink()  # Remover arquivo baixado
            return True
            
        except Exception as e:
            self.logger.error(f"Erro no download/extração de {tool_name}: {e}")
            return False
    
    def _download_and_install_exe(self, url: str, filename: str) -> bool:
        """Download e instalação de executáveis"""
        try:
            temp_path = self.base_path / "temp"
            temp_path.mkdir(parents=True, exist_ok=True)
            file_path = temp_path / filename
            
            print(f"📥 Baixando {filename}...")
            urllib.request.urlretrieve(url, file_path)
            
            print(f"🔧 Instalando {filename}...")
            result = subprocess.run([str(file_path), '/S'], capture_output=True)
            
            file_path.unlink()  # Remover arquivo baixado
            return result.returncode == 0
            
        except Exception as e:
            self.logger.error(f"Erro na instalação de {filename}: {e}")
            return False
    
    def _install_system_dependencies(self, dependencies: List[str]) -> bool:
        """Instala dependências do sistema com feedback visual e verificação robusta"""
        self.logger.info("🔍 Verificando dependências do sistema...")
        print("\n📦 Verificando e instalando dependências necessárias...")
        
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
        print("🔍 Detectando gerenciador de pacotes...")
        for pm in package_managers:
            if shutil.which(pm):
                active_pm = pm
                print(f"✅ Encontrado: {pm}")
                break
                
        if not active_pm:
            print("⚠️  Nenhum gerenciador de pacotes encontrado")
            self.logger.warning("Nenhum gerenciador de pacotes encontrado")
            return self._install_dependencies_manually(dependencies)
            
        # Mapear dependências para nomes de pacotes específicos
        package_mapping = self._get_package_mapping(active_pm)
        
        total_deps = len(dependencies)
        installed_count = 0
        failed_deps = []
        
        for i, dep in enumerate(dependencies, 1):
            print(f"\n[{i}/{total_deps}] Verificando dependência: {dep}")
            
            # Verificar se já está instalado
            if self._check_dependency_robust(dep):
                print(f"✅ {dep} já está instalado")
                installed_count += 1
                continue
                
            if dep in package_mapping:
                package_name = package_mapping[dep]
                cmd = package_managers[active_pm] + [package_name]
                
                print(f"📥 Instalando {package_name}...")
                self.logger.info(f"Instalando {package_name}")
                
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                    
                    if result.returncode == 0:
                        print(f"✅ {package_name} instalado com sucesso")
                        installed_count += 1
                    else:
                        print(f"❌ Falha ao instalar {package_name}")
                        self.logger.error(f"Falha ao instalar {package_name}: {result.stderr}")
                        failed_deps.append(dep)
                        
                except subprocess.TimeoutExpired:
                    print(f"⏰ Timeout ao instalar {package_name}")
                    self.logger.error(f"Timeout ao instalar {package_name}")
                    failed_deps.append(dep)
                except Exception as e:
                    print(f"❌ Erro ao instalar {package_name}: {e}")
                    self.logger.error(f"Erro ao instalar {package_name}: {e}")
                    failed_deps.append(dep)
            else:
                print(f"⚠️  Dependência {dep} não mapeada para {active_pm}")
                failed_deps.append(dep)
                
        # Relatório final
        print(f"\n📊 Relatório de instalação:")
        print(f"✅ Instaladas: {installed_count}/{total_deps}")
        if failed_deps:
            print(f"❌ Falharam: {len(failed_deps)} ({', '.join(failed_deps)})")
            
        return len(failed_deps) == 0
    
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
                'gcc-m68k-elf': 'gcc-m68k-elf',  # CORREÇÃO: Mapeamento mais específico
                'gcc-mips': 'gcc-mips-linux-gnu',
                'gcc-mips64': 'gcc-mips64-linux-gnuabi64',
                'gcc-sh2': 'gcc-sh4-linux-gnu',
                'devkitpro': 'devkitpro-pacman',
                'wine': 'wine',
                'unzip': 'unzip',
                'wget': 'wget',
                'p7zip-full': 'p7zip-full'  # Para extrair arquivos .7z
            },
            'choco': {
                'cc65': 'cc65',
                'make': 'make',
                'cmake': 'cmake',
                'python3': 'python3',
                'java': 'openjdk11',
                'git': 'git',
                'wget': 'wget',
                'wine': 'wine',
                'unzip': 'unzip',
                'p7zip-full': '7zip'  # 7zip no Windows
            },
            'brew': {
                'cc65': 'cc65',
                'sdcc': 'sdcc',
                'make': 'make',
                'cmake': 'cmake',
                'python3': 'python3',
                'java': 'openjdk@11',
                'unzip': 'unzip',
                'wget': 'wget',
                'p7zip-full': 'p7zip'
            }
        }
        
        return mappings.get(package_manager, {})
    
    def _setup_environment_variables(self, devkit: DevKitInfo) -> None:
        """Configura variáveis de ambiente permanentemente com verificação aprimorada"""
        self.logger.info("🔧 Configurando variáveis de ambiente do SGDK...")
        
        for var_name, var_value in devkit.environment_vars.items():
            self.logger.info(f"Configurando {var_name} = {var_value}")
            
            # Configurar para a sessão atual
            os.environ[var_name] = var_value
            
            # Configurar permanentemente baseado no SO
            if platform.system() == "Windows":
                # Windows: usar setx para persistir + registro
                try:
                    # Método 1: setx (usuário atual)
                    subprocess.run(
                        ["setx", var_name, var_value],
                        check=True,
                        capture_output=True
                    )
                    
                    # Método 2: PowerShell para PATH (se aplicável)
                    if var_name == "PATH" or "PATH" in var_name:
                        ps_command = f"[Environment]::SetEnvironmentVariable('{var_name}', '{var_value}', 'User')"
                        subprocess.run(
                            ["powershell", "-Command", ps_command],
                            check=True,
                            capture_output=True
                        )
                    
                    self.logger.info(f"✅ Variável {var_name} configurada no Windows (setx + PowerShell)")
                    
                    # Verificar se foi configurada corretamente
                    verify_cmd = f"echo %{var_name}%"
                    result = subprocess.run(verify_cmd, shell=True, capture_output=True, text=True)
                    if result.returncode == 0 and var_value in result.stdout:
                        self.logger.info(f"✅ Verificação: {var_name} configurada corretamente")
                    else:
                        self.logger.warning(f"⚠️ Verificação: {var_name} pode não estar configurada corretamente")
                        
                except subprocess.CalledProcessError as e:
                    self.logger.error(f"❌ Erro ao configurar {var_name}: {e}")
                    # Fallback: tentar apenas com PowerShell
                    try:
                        ps_command = f"[Environment]::SetEnvironmentVariable('{var_name}', '{var_value}', 'User')"
                        subprocess.run(["powershell", "-Command", ps_command], check=True)
                        self.logger.info(f"✅ Fallback: {var_name} configurada via PowerShell")
                    except Exception as fallback_error:
                        self.logger.error(f"❌ Fallback falhou para {var_name}: {fallback_error}")
            else:
                # Unix-like: adicionar aos arquivos de perfil com verificação
                profile_files = [
                    Path.home() / ".bashrc",
                    Path.home() / ".zshrc", 
                    Path.home() / ".profile",
                    Path.home() / ".bash_profile"
                ]
                
                export_line = f"export {var_name}='{var_value}'\n"
                comment_line = f"# SGDK Environment Variable - Added by RetroDevKitManager\n"
                
                for profile_file in profile_files:
                    if profile_file.exists():
                        try:
                            # Verificar se a variável já existe no arquivo
                            with open(profile_file, "r") as f:
                                content = f.read()
                            
                            if f"export {var_name}=" not in content:
                                with open(profile_file, "a") as f:
                                    f.write("\n" + comment_line + export_line)
                                self.logger.info(f"✅ Variável {var_name} adicionada a {profile_file}")
                            else:
                                self.logger.info(f"ℹ️ Variável {var_name} já existe em {profile_file}")
                                
                        except Exception as e:
                            self.logger.error(f"❌ Erro ao escrever em {profile_file}: {e}")
                
                # Verificar se foi configurada
                try:
                    result = subprocess.run(f"echo ${var_name}", shell=True, capture_output=True, text=True)
                    if result.returncode == 0:
                        self.logger.info(f"✅ Verificação: {var_name} = {result.stdout.strip()}")
                except Exception as e:
                    self.logger.warning(f"⚠️ Não foi possível verificar {var_name}: {e}")
        
        # Instruções para o usuário
        if platform.system() == "Windows":
            self.logger.info("\n📋 IMPORTANTE: Reinicie o terminal ou faça logoff/login para que as variáveis de ambiente tenham efeito completo.")
        else:
            self.logger.info("\n📋 IMPORTANTE: Execute 'source ~/.bashrc' ou reinicie o terminal para carregar as variáveis de ambiente.")
        
        # Mostrar resumo das variáveis configuradas
        self.logger.info("\n📊 Resumo das variáveis de ambiente configuradas:")
        for var_name, var_value in devkit.environment_vars.items():
            self.logger.info(f"  {var_name} = {var_value}")
    
    def _verify_installation(self, devkit: DevKitInfo) -> bool:
        """Verifica se a instalação foi bem-sucedida"""
        self.logger.info(f"Verificando instalação do {devkit.name}")
        
        for command in devkit.verification_commands:
            # CORREÇÃO: Usar verificação nativa Python para arquivos
            if command.startswith("test -f") or command.startswith("file_exists:"):
                # Extrair caminho do arquivo
                if command.startswith("test -f"):
                    file_path = command.split("test -f ")[1].strip()
                else:
                    file_path = command.split("file_exists:")[1].strip()
                
                # Normalizar caminho para Windows
                file_path = file_path.replace('/', os.sep).replace('\\', os.sep)
                
                if not Path(file_path).exists():
                    self.logger.error(f"Arquivo não encontrado: {file_path}")
                    return False
                else:
                    self.logger.info(f"✅ Arquivo encontrado: {file_path}")
                continue
            
            # Para outros comandos, executar normalmente
            try:
                result = subprocess.run(
                    command, 
                    shell=True, 
                    capture_output=True, 
                    text=True,
                    timeout=30
                )
                
                if result.returncode != 0:
                    self.logger.error(f"Verificação falhou para: {command}")
                    self.logger.error(f"Saída: {result.stderr}")
                    return False
                else:
                    self.logger.info(f"✅ Comando executado com sucesso: {command}")
            except subprocess.TimeoutExpired:
                self.logger.error(f"Timeout na verificação: {command}")
                return False
            except Exception as e:
                self.logger.error(f"Erro na verificação {command}: {e}")
                return False
                
        self.logger.info(f"✅ {devkit.name} instalado com sucesso!")
        return True
    
    def _detect_java_home(self) -> str:
        """Detecta automaticamente o JAVA_HOME"""
        # Primeiro, verifica se JAVA_HOME já está definido
        java_home = os.environ.get('JAVA_HOME')
        if java_home and Path(java_home).exists():
            return java_home
        
        # Tenta detectar Java automaticamente
        try:
            if sys.platform == "win32":
                # No Windows, verifica o registro
                try:
                    import winreg
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                                       r"SOFTWARE\JavaSoft\Java Development Kit")
                    current_version = winreg.QueryValueEx(key, "CurrentVersion")[0]
                    version_key = winreg.OpenKey(key, current_version)
                    java_home = winreg.QueryValueEx(version_key, "JavaHome")[0]
                    return java_home
                except:
                    pass
                
                # Fallback: procura em locais comuns no Windows
                common_paths = [
                    "C:\\Program Files\\Java",
                    "C:\\Program Files (x86)\\Java",
                    "C:\\Program Files\\Eclipse Adoptium",
                    "C:\\Program Files\\OpenJDK"
                ]
                for base_path in common_paths:
                    if Path(base_path).exists():
                        for java_dir in Path(base_path).iterdir():
                            if java_dir.is_dir() and "jdk" in java_dir.name.lower():
                                return str(java_dir)
            else:
                # Unix-like systems
                result = subprocess.run(["which", "java"], capture_output=True, text=True)
                if result.returncode == 0:
                    java_path = Path(result.stdout.strip())
                    # Resolve symlinks e vai para o diretório pai
                    java_home = java_path.resolve().parent.parent
                    return str(java_home)
                
                # Fallback: procura em locais comuns
                common_paths = [
                    "/usr/lib/jvm",
                    "/usr/java",
                    "/opt/java",
                    "/Library/Java/JavaVirtualMachines"  # macOS
                ]
                for base_path in common_paths:
                    if Path(base_path).exists():
                        for java_dir in Path(base_path).iterdir():
                            if java_dir.is_dir():
                                return str(java_dir)
        except Exception as e:
            self.logger.warning(f"Erro ao detectar JAVA_HOME: {e}")
        
        # Fallback final
        return str(self.base_path / "java")
    
    def _get_sgdk_install_commands_with_fallback(self) -> List[str]:
        """Retorna comandos de instalação do SGDK com sistema de fallback de versões"""
        # Atualizado para SGDK v2.11 (versão mais atual)
        if sys.platform == "win32":
            return [
                "powershell -Command \"Invoke-WebRequest -Uri 'https://github.com/Stephane-D/SGDK/releases/download/v2.11/sgdk211.7z' -OutFile 'sgdk211.7z'\"",
                "7z x sgdk211.7z -osgdk",
                "del sgdk211.7z"
            ]
        else:
            # Linux installation commands
            sgdk_path = self.base_path / "sgdk"
            download_cmd = f"wget -O sgdk211.7z https://github.com/Stephane-D/SGDK/releases/download/v2.11/sgdk211.7z"
            extract_cmd = f"7z x sgdk211.7z -o{sgdk_path}"
            cleanup_cmd = "rm sgdk211.7z"
            chmod_cmd = f"chmod +x {sgdk_path / 'bin'}/*"
            return [download_cmd, extract_cmd, cleanup_cmd, chmod_cmd]

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
            # Usar método _verify_installation melhorado
            try:
                is_installed = self._verify_installation(devkit)
                status[devkit_id] = is_installed
            except Exception as e:
                self.logger.error(f"Erro ao verificar {devkit_id}: {e}")
                status[devkit_id] = False
            
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


    def install_sgdk(self, force_reinstall: bool = False) -> bool:
        """Instala o SGDK (Sega Genesis Development Kit) com todas as melhorias robustas"""
        try:
            self.logger.info("🚀 Iniciando instalação robusta do SGDK...")
            
            # Usar o novo instalador melhorado
            from .improved_sgdk_installer import ImprovedSGDKInstaller
            
            # Criar instalador SGDK melhorado
            sgdk_installer = ImprovedSGDKInstaller(self.logger, self.base_path)
            
            # Executar instalação completa com todas as verificações
            if sgdk_installer.install_sgdk(force_reinstall=force_reinstall):
                self.logger.info("✅ SGDK instalado com sucesso usando instalador robusto!")
                
                # Executar diagnósticos adicionais do sistema antigo para compatibilidade
                try:
                    from .sgdk_improvements import SGDKDiagnostics
                    diagnostics = SGDKDiagnostics(self.logger)
                    results = diagnostics.run_full_diagnostics(self.base_path / "sgdk")
                    
                    if not all(results.values()):
                        self.logger.warning("⚠️ Alguns diagnósticos falharam, mas instalação principal foi bem-sucedida")
                        try:
                            report = diagnostics.generate_diagnostic_report(results)
                            self.logger.warning(f"Relatório de diagnóstico:\n{report}")
                        except AttributeError:
                            # Fallback se método não existir
                            self.logger.warning("Diagnósticos detalhados não disponíveis")
                except Exception as diag_error:
                    self.logger.warning(f"⚠️ Erro nos diagnósticos adicionais: {diag_error}")
                
                return True
            else:
                self.logger.error("❌ Falha na instalação robusta do SGDK")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Erro durante instalação do SGDK: {e}")
            return False
    
    def install_gbdk(self) -> bool:
        """Instala o GBDK (Game Boy Development Kit)"""
        return self.install_devkit("gbdk")
    
    def install_snes(self) -> bool:
        """Instala o SNES Development Kit"""
        return self.install_devkit("snes")
    
    def install_psx(self) -> bool:
        """Instala o PSX Development Kit"""
        return self.install_devkit("psx")
    
    def install_n64(self) -> bool:
        """Instala o N64 Development Kit"""
        return self.install_devkit("n64")
    
    def install_gba(self) -> bool:
        """Instala o GBA Development Kit"""
        return self.install_devkit("gba")
    
    def install_neogeo(self) -> bool:
        """Instala o Neo Geo Development Kit"""
        return self.install_devkit("neogeo")
    
    def install_nes(self) -> bool:
        """Instala o NES Development Kit"""
        return self.install_devkit("nes")
    
    def install_saturn(self) -> bool:
        """Instala o Saturn Development Kit"""
        return self.install_devkit("saturn")
    
    def install_sgdk_real(self) -> bool:
        """
        Instala o SGDK usando o instalador real (versão 2.11)
        Returns:
            bool: True se instalação foi bem-sucedida
        """
        try:
            # Importar o instalador real
            from .sgdk_real_installer import install_sgdk_real
            
            self.logger.info("Iniciando instalação real do SGDK 2.11")
            result = install_sgdk_real()
            
            if result.get("success", False):
                self.logger.info("✅ SGDK 2.11 instalado com sucesso!")
                return True
            else:
                error_msg = result.get("error_message", "Erro desconhecido")
                self.logger.error(f"❌ Falha na instalação do SGDK: {error_msg}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Erro na instalação real do SGDK: {e}")
            return False
    
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