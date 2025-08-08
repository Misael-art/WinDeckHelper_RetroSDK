"""Melhorias específicas para o módulo SGDK no RetroDevKitManager
Correções e aprimoramentos identificados na revisão do código"""

import os
import sys
import json
import subprocess
import shutil
import urllib.request
import zipfile
import platform
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass
import time

# Importar o novo instalador real
try:
    from .sgdk_real_installer import SGDKRealInstaller, install_sgdk_real, check_sgdk_status
    from .component_status_manager import get_status_manager, ComponentStatus
    REAL_INSTALLER_AVAILABLE = True
except ImportError:
    REAL_INSTALLER_AVAILABLE = False

class SGDKInstaller:
    """Instalador aprimorado específico para SGDK com instalação real"""
    
    def __init__(self, base_path: Path, logger: logging.Logger):
        self.base_path = base_path
        self.logger = logger
        self.sgdk_version = "2.11"  # Versão mais recente
        self.sgdk_path = base_path / "sgdk"
        self.gendk_path = base_path / "GENDK"
        self.emulators_path = self.gendk_path / "_Emuladores"
        
        # Usar instalador real se disponível
        self.real_installer = SGDKRealInstaller() if REAL_INSTALLER_AVAILABLE else None
        self.status_manager = get_status_manager() if REAL_INSTALLER_AVAILABLE else None
        
    def install_sgdk_real(self) -> Dict[str, any]:
        """
        Instala o SGDK usando o instalador real (versão 2.11)
        Returns:
            Dict com resultado da instalação
        """
        try:
            self.logger.info("Iniciando instalação real do SGDK 2.11")
            
            if not REAL_INSTALLER_AVAILABLE:
                self.logger.warning("Instalador real não disponível, usando método legado")
                return self._install_sgdk_legacy()
            
            # Verificar se já está instalado
            status = check_sgdk_status()
            if status["installed"] and status["version"] == "2.11":
                self.logger.info("SGDK 2.11 já está instalado")
                
                # Marcar como instalado no status manager
                if self.status_manager:
                    self.status_manager.mark_component_installed(
                        component_id="sgdk",
                        name="SGDK (Sega Genesis Development Kit)",
                        version="2.11",
                        install_path=status["install_path"]
                    )
                
                return {
                    "success": True,
                    "message": "SGDK 2.11 já instalado",
                    "version": "2.11",
                    "install_path": status["install_path"]
                }
            
            # Instalar usando o instalador real
            result = install_sgdk_real()
            
            # Atualizar status manager
            if self.status_manager:
                if result["success"]:
                    self.status_manager.mark_component_installed(
                        component_id="sgdk",
                        name="SGDK (Sega Genesis Development Kit)",
                        version="2.11",
                        install_path=result["install_path"]
                    )
                else:
                    self.status_manager.mark_component_failed(
                        component_id="sgdk",
                        name="SGDK (Sega Genesis Development Kit)",
                        error_message=result.get("error_message", "Instalação falhou")
                    )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Erro na instalação real do SGDK: {e}")
            
            # Marcar como falha no status manager
            if self.status_manager:
                self.status_manager.mark_component_failed(
                    component_id="sgdk",
                    name="SGDK (Sega Genesis Development Kit)",
                    error_message=str(e)
                )
            
            return {
                "success": False,
                "error_message": str(e)
            }

    def _install_sgdk_legacy(self) -> Dict[str, any]:
        """Método de instalação legado (fallback)"""
        self.logger.info("Usando método de instalação legado do SGDK")
        
        # Implementação básica de fallback
        return {
            "success": False,
            "error_message": "Instalador real não disponível e método legado não implementado"
        }

    def get_improved_sgdk_config(self) -> dict:
        """Configuração melhorada do SGDK com correções identificadas"""
        return {
            "name": "Sega Mega Drive Development Kit",
            "console": "Sega Mega Drive / Genesis",
            "devkit_name": "SGDK",
            # CORREÇÃO 1: Dependências mais específicas e corretas
            "dependencies": [
                "gcc-m68k-elf",  # Mais específico que gcc-m68k
                "make", 
                "java",
                "unzip",  # Necessário para extrair SGDK
                "wget"    # Necessário para download
            ],
            "environment_vars": {
                "GDK": str(self.base_path / "sgdk"),
                "GDK_WIN": str(self.base_path / "sgdk"),
                "JAVA_HOME": self._detect_java_home(),
                "PATH": str(self.base_path / "sgdk" / "bin")  # Adicionar bin ao PATH
            },
            # CORREÇÃO 2: URL de download mais confiável
            "download_url": f"https://github.com/Stephane-D/SGDK/releases/download/v{self.sgdk_version}/sgdk{self.sgdk_version.replace('.', '')}.7z",
            # CORREÇÃO 3: Comandos de instalação melhorados
            "install_commands": self._get_improved_install_commands(),
            # CORREÇÃO 4: Verificações mais robustas
            "verification_commands": [
                "java -version",
                "make --version",
                # Verificar se SGDK foi extraído corretamente
                f"test -f {self.base_path / 'sgdk' / 'bin' / 'rescomp.jar'}",
                f"test -f {self.base_path / 'sgdk' / 'inc' / 'genesis.h'}"
            ],
            "emulators": {
                "BizHawk": {
                    "path": str(self.emulators_path / "BizHawk"),
                    "executable": "EmuHawk.exe",
                    "config_required": True,
                    "description": "Emulador multi-sistema com ferramentas avançadas de debugging",
                    "features": ["debugging", "save_states", "input_recording", "memory_viewer"]
                },
                "Blastem": {
                    "path": str(self.emulators_path / "Blastem"),
                    "executable": "blastem.exe",
                    "config_required": False,
                    "description": "Emulador Genesis/Mega Drive de alta precisão",
                    "features": ["high_accuracy", "fast_performance", "sound_quality"]
                },
                "GensKMod": {
                    "path": str(self.emulators_path / "GensKMod"),
                    "executable": "Gens.exe",
                    "config_required": False,
                    "description": "Versão modificada do Gens com melhorias",
                    "features": ["classic_interface", "compatibility", "lightweight"]
                }
            },
            "docker_support": True
        }
    
    def _detect_java_home(self) -> str:
        """Detecta JAVA_HOME automaticamente"""
        # Tentar detectar Java instalado
        java_paths = [
            "/usr/lib/jvm/default-java",
            "/usr/lib/jvm/java-11-openjdk",
            "/usr/lib/jvm/java-8-openjdk",
            "C:\\Program Files\\Java\\jdk-11",
            "C:\\Program Files\\OpenJDK\\jdk-11"
        ]
        
        # Verificar JAVA_HOME existente
        existing_java = os.environ.get('JAVA_HOME')
        if existing_java and Path(existing_java).exists():
            return existing_java
            
        # Procurar Java instalado
        for path in java_paths:
            if Path(path).exists():
                return path
                
        # Fallback para detecção automática
        try:
            result = subprocess.run(['java', '-XshowSettings:properties', '-version'], 
                                  capture_output=True, text=True, stderr=subprocess.STDOUT)
            for line in result.stdout.split('\n'):
                if 'java.home' in line:
                    return line.split('=')[1].strip()
        except:
            pass
            
        return str(self.base_path / "java")
    
    def _get_improved_install_commands(self) -> List[str]:
        """Comandos de instalação melhorados com tratamento de erros"""
        commands = []
        
        # Detectar sistema operacional
        if os.name == 'nt':  # Windows
            commands.extend([
                # Baixar SGDK usando PowerShell (mais confiável que wget no Windows)
                f"powershell -Command \"Invoke-WebRequest -Uri 'https://github.com/Stephane-D/SGDK/releases/download/v{self.sgdk_version}/sgdk{self.sgdk_version.replace('.', '')}.7z' -OutFile 'sgdk.7z'\"",
                # Extrair usando 7zip se disponível, senão usar PowerShell
                "if (Get-Command 7z -ErrorAction SilentlyContinue) { 7z x sgdk.7z -osgdk } else { powershell -Command \"Expand-Archive sgdk.7z sgdk\" }",
                # Verificar se extração foi bem-sucedida
                "if not exist sgdk\\bin\\rescomp.jar (echo ERRO: SGDK nao foi extraido corretamente && exit 1)",
                # Tornar scripts executáveis (se necessário)
                "icacls sgdk\\bin\\* /grant Everyone:F"
            ])
        else:  # Unix-like
            commands.extend([
                # Instalar 7zip se não estiver disponível
                "which 7z || (echo 'Instalando 7zip...' && sudo apt-get update && sudo apt-get install -y p7zip-full)",
                # Baixar SGDK
                f"wget -O sgdk.7z 'https://github.com/Stephane-D/SGDK/releases/download/v{self.sgdk_version}/sgdk{self.sgdk_version.replace('.', '')}.7z'",
                # Extrair
                "7z x sgdk.7z -osgdk",
                # Verificar extração
                "test -f sgdk/bin/rescomp.jar || (echo 'ERRO: SGDK não foi extraído corretamente' && exit 1)",
                # Tornar executáveis
                "chmod +x sgdk/bin/*"
            ])
            
        return commands
    
    def install_sgdk_dependencies_windows(self) -> bool:
        """Instala dependências específicas do SGDK no Windows"""
        self.logger.info("Instalando dependências do SGDK no Windows")
        
        dependencies = {
            'java': 'openjdk11',
            'make': 'make',
            '7zip': '7zip',
            'wget': 'wget'
        }
        
        # Verificar se Chocolatey está disponível
        if shutil.which('choco'):
            for dep_name, choco_package in dependencies.items():
                if not self._check_dependency_installed(dep_name):
                    self.logger.info(f"Instalando {dep_name} via Chocolatey")
                    try:
                        result = subprocess.run(['choco', 'install', choco_package, '-y'], 
                                              capture_output=True, text=True, timeout=300)
                        if result.returncode != 0:
                            self.logger.warning(f"Falha ao instalar {dep_name}: {result.stderr}")
                            # Não falhar completamente, apenas avisar
                            self.logger.warning(f"Continuando sem {dep_name}. Instale manualmente se necessário.")
                    except subprocess.TimeoutExpired:
                        self.logger.warning(f"Timeout ao instalar {dep_name}. Continuando...")
                    except Exception as e:
                        self.logger.warning(f"Erro ao instalar {dep_name}: {e}. Continuando...")
        else:
            self.logger.warning("Chocolatey não encontrado. Instale manualmente: Java, Make, 7zip")
            # Não falhar, apenas avisar
            
        return True
    
    def install_sgdk_dependencies_linux(self) -> bool:
        """Instala dependências específicas do SGDK no Linux"""
        self.logger.info("Instalando dependências do SGDK no Linux")
        
        # Detectar distribuição
        distro_commands = {
            'apt': ['sudo', 'apt-get', 'update', '&&', 'sudo', 'apt-get', 'install', '-y'],
            'yum': ['sudo', 'yum', 'install', '-y'],
            'dnf': ['sudo', 'dnf', 'install', '-y'],
            'pacman': ['sudo', 'pacman', '-S', '--noconfirm']
        }
        
        package_manager = None
        for pm in distro_commands:
            if shutil.which(pm):
                package_manager = pm
                break
                
        if not package_manager:
            self.logger.error("Nenhum gerenciador de pacotes suportado encontrado")
            return False
            
        # Pacotes necessários por distribuição
        packages = {
            'apt': ['openjdk-11-jdk', 'build-essential', 'p7zip-full', 'wget'],
            'yum': ['java-11-openjdk-devel', 'make', 'gcc', 'p7zip', 'wget'],
            'dnf': ['java-11-openjdk-devel', 'make', 'gcc', 'p7zip', 'wget'],
            'pacman': ['jdk11-openjdk', 'base-devel', 'p7zip', 'wget']
        }
        
        cmd = distro_commands[package_manager] + packages[package_manager]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            self.logger.error(f"Falha ao instalar dependências: {result.stderr}")
            return False
            
        return True
    
    def _check_dependency_installed(self, dependency: str) -> bool:
        """Verifica se uma dependência está instalada"""
        # Primeiro verificar se está no PATH
        path_checks = {
            'java': lambda: shutil.which('java') is not None or shutil.which('javac') is not None,
            'make': lambda: shutil.which('make') is not None or shutil.which('mingw32-make') is not None,
            '7zip': lambda: shutil.which('7z') is not None,
            'wget': lambda: shutil.which('wget') is not None
        }
        
        if dependency in path_checks and path_checks[dependency]():
            return True
            
        # Se não encontrou no PATH, tentar executar comando
        check_commands = {
            'java': ['java', '-version'],
            'make': ['make', '--version'],
            '7zip': ['7z'],
            'wget': ['wget', '--version']
        }
        
        if dependency in check_commands:
            try:
                result = subprocess.run(check_commands[dependency], 
                                      capture_output=True, text=True)
                return result.returncode == 0
            except FileNotFoundError:
                return False
                
        return False
    
    def verify_sgdk_installation(self, sgdk_path: Path) -> bool:
        """Verificação robusta da instalação do SGDK"""
        self.logger.info("Verificando instalação do SGDK")
        
        # Verificar estrutura de diretórios
        required_dirs = ['bin', 'inc', 'lib', 'res', 'sample']
        for dir_name in required_dirs:
            dir_path = sgdk_path / dir_name
            if not dir_path.exists():
                self.logger.error(f"Diretório obrigatório não encontrado: {dir_path}")
                return False
                
        # Verificar arquivos essenciais
        required_files = [
            'bin/rescomp.jar',
            'bin/bintos.exe' if os.name == 'nt' else 'bin/bintos',
            'inc/genesis.h',
            'lib/libmd.a'
        ]
        
        for file_path in required_files:
            full_path = sgdk_path / file_path
            if not full_path.exists():
                self.logger.error(f"Arquivo obrigatório não encontrado: {full_path}")
                return False
                
        # Verificar se Java pode executar rescomp
        try:
            rescomp_path = sgdk_path / 'bin' / 'rescomp.jar'
            result = subprocess.run(['java', '-jar', str(rescomp_path)], 
                                  capture_output=True, text=True, timeout=10)
            # rescomp deve retornar erro de uso (código 1) quando executado sem argumentos
            if result.returncode not in [0, 1]:
                self.logger.error("rescomp.jar não pode ser executado corretamente")
                return False
        except Exception as e:
            self.logger.error(f"Erro ao testar rescomp.jar: {e}")
            return False
            
        self.logger.info("✅ SGDK instalado e verificado com sucesso!")
        return True
    
    def install_emulators(self) -> bool:
        """Instala e configura os emuladores necessários para SGDK"""
        try:
            self.logger.info("🎮 Iniciando instalação dos emuladores SGDK...")
            
            # Criar estrutura de diretórios
            self.emulators_path.mkdir(parents=True, exist_ok=True)
            
            # Instalar cada emulador
            emulators_success = {
                "BizHawk": self._install_bizhawk(),
                "Blastem": self._install_blastem(),
                "GensKMod": self._install_genskmod()
            }
            
            # Configurar BizHawk para SGDK
            if emulators_success["BizHawk"]:
                self._configure_bizhawk_for_sgdk()
            
            # Criar scripts de lançamento
            self._create_emulator_scripts()
            
            success_count = sum(emulators_success.values())
            total_count = len(emulators_success)
            
            self.logger.info(f"✅ Instalação concluída: {success_count}/{total_count} emuladores instalados")
            return success_count > 0
            
        except Exception as e:
             self.logger.error(f"❌ Erro na instalação dos emuladores: {e}")
             return False
    
    def install_vscode_extensions(self) -> bool:
        """Instala extensões do VS Code para desenvolvimento SGDK"""
        try:
            self.logger.info("🔧 Iniciando instalação das extensões VS Code para SGDK...")
            
            # Instalar Genesis Code para VS Code e VS Code Insiders
            extensions_installed = {
                'vscode': self._install_genesis_code_vscode(),
                'vscode_insiders': self._install_genesis_code_vscode_insiders()
            }
            
            # Configurar workspace para SGDK
            self._configure_vscode_workspace()
            
            success_count = sum(extensions_installed.values())
            self.logger.info(f"✅ {success_count}/2 extensões VS Code instaladas com sucesso!")
            
            return success_count > 0
            
        except Exception as e:
            self.logger.error(f"❌ Erro na instalação das extensões VS Code: {e}")
            return False
    
    def _install_bizhawk(self) -> bool:
        """Instala o emulador BizHawk"""
        try:
            bizhawk_path = self.emulators_path / "BizHawk"
            bizhawk_path.mkdir(exist_ok=True)
            
            # URL do BizHawk (versão estável)
            bizhawk_url = "https://github.com/TASEmulators/BizHawk/releases/latest/download/BizHawk-2.9.1-win-x64.zip"
            
            self.logger.info("📥 Baixando BizHawk...")
            
            # Comandos de instalação específicos por plataforma
            if platform.system() == "Windows":
                install_commands = [
                    f'powershell -Command "Invoke-WebRequest -Uri \'{bizhawk_url}\' -OutFile \'{bizhawk_path}/bizhawk.zip\'"',
                    f'powershell -Command "Expand-Archive -Path \'{bizhawk_path}/bizhawk.zip\' -DestinationPath \'{bizhawk_path}\' -Force"',
                    f'del "{bizhawk_path}/bizhawk.zip"'
                ]
            else:
                install_commands = [
                    f'wget -O "{bizhawk_path}/bizhawk.zip" "{bizhawk_url}"',
                    f'unzip "{bizhawk_path}/bizhawk.zip" -d "{bizhawk_path}"',
                    f'rm "{bizhawk_path}/bizhawk.zip"'
                ]
            
            # Executar comandos de instalação com retry
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    for cmd in install_commands:
                        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
                        if result.returncode != 0:
                            raise Exception(f"Comando falhou: {cmd}")
                    break
                except Exception as e:
                    self.logger.warning(f"Tentativa {attempt+1} falhou: {e}")
                    if attempt == max_retries - 1:
                        raise
                    time.sleep(5)
            
            # Verificar se foi instalado corretamente
            exe_path = bizhawk_path / "EmuHawk.exe"
            if exe_path.exists():
                self.logger.info("✅ BizHawk instalado com sucesso")
                return True
            else:
                self.logger.error("❌ BizHawk não foi instalado corretamente")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Erro ao instalar BizHawk: {e}")
            return False
    
    def _install_blastem(self) -> bool:
        """Instala o emulador Blastem"""
        try:
            blastem_path = self.emulators_path / "Blastem"
            blastem_path.mkdir(exist_ok=True)
            
            # URL do Blastem
            blastem_url = "https://www.retrodev.com/blastem/nightlies/blastem-win64-latest.zip"
            
            self.logger.info("📥 Baixando Blastem...")
            
            if platform.system() == "Windows":
                install_commands = [
                    f'powershell -Command "Invoke-WebRequest -Uri \'{blastem_url}\' -OutFile \'{blastem_path}/blastem.zip\'"',
                    f'powershell -Command "Expand-Archive -Path \'{blastem_path}/blastem.zip\' -DestinationPath \'{blastem_path}\' -Force"',
                    f'del "{blastem_path}/blastem.zip"'
                ]
            else:
                install_commands = [
                    f'wget -O "{blastem_path}/blastem.zip" "{blastem_url}"',
                    f'unzip "{blastem_path}/blastem.zip" -d "{blastem_path}"',
                    f'rm "{blastem_path}/blastem.zip"'
                ]
            
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    for cmd in install_commands:
                        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
                        if result.returncode != 0:
                            raise Exception(f"Comando falhou: {cmd}")
                    break
                except Exception as e:
                    self.logger.warning(f"Tentativa {attempt+1} falhou: {e}")
                    if attempt == max_retries - 1:
                        raise
                    time.sleep(5)
            
            # Verificar instalação
            exe_path = blastem_path / "blastem.exe"
            if exe_path.exists():
                self.logger.info("✅ Blastem instalado com sucesso")
                return True
            else:
                self.logger.error("❌ Blastem não foi instalado corretamente")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Erro ao instalar Blastem: {e}")
            return False
    
    def _install_genskmod(self) -> bool:
        """Instala o emulador GensKMod"""
        try:
            genskmod_path = self.emulators_path / "GensKMod"
            genskmod_path.mkdir(exist_ok=True)
            
            # URL do GensKMod
            genskmod_url = "https://segaretro.org/images/7/75/Gens_KMod_v2.15a.zip"
            
            self.logger.info("📥 Baixando GensKMod...")
            
            if platform.system() == "Windows":
                install_commands = [
                    f'powershell -Command "Invoke-WebRequest -Uri \'{genskmod_url}\' -OutFile \'{genskmod_path}/genskmod.zip\'"',
                    f'powershell -Command "Expand-Archive -Path \'{genskmod_path}/genskmod.zip\' -DestinationPath \'{genskmod_path}\' -Force"',
                    f'del "{genskmod_path}/genskmod.zip"'
                ]
            else:
                install_commands = [
                    f'wget -O "{genskmod_path}/genskmod.zip" "{genskmod_url}"',
                    f'unzip "{genskmod_path}/genskmod.zip" -d "{genskmod_path}"',
                    f'rm "{genskmod_path}/genskmod.zip"'
                ]
            
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    for cmd in install_commands:
                        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
                        if result.returncode != 0:
                            raise Exception(f"Comando falhou: {cmd}")
                    break
                except Exception as e:
                    self.logger.warning(f"Tentativa {attempt+1} falhou: {e}")
                    if attempt == max_retries - 1:
                        raise
                    time.sleep(5)
            
            # Verificar instalação
            exe_path = genskmod_path / "Gens.exe"
            if exe_path.exists():
                self.logger.info("✅ GensKMod instalado com sucesso")
                return True
            else:
                self.logger.error("❌ GensKMod não foi instalado corretamente")
                return False
                
        except Exception as e:
             self.logger.error(f"❌ Erro ao instalar GensKMod: {e}")
             return False
    
    def _configure_bizhawk_for_sgdk(self) -> bool:
        """Configura o BizHawk especificamente para desenvolvimento SGDK"""
        try:
            bizhawk_path = self.emulators_path / "BizHawk"
            config_path = bizhawk_path / "config.ini"
            
            # Configuração otimizada para desenvolvimento SGDK
            config_content = """[Genesis]
# Configuração otimizada para desenvolvimento SGDK
Region=USA
AutoDetectRegion=false
VDP_DisplayOverscan=false
VDP_DispBG=true
VDP_DispOBJ=true

[Sound]
Enabled=true
SampleRate=44100
BufferSizeMs=100

[Video]
FinalFilter=None
DispFPS=true
DispFrameCounter=true
DispLagCounter=true
DispInputDisplay=true

[Hotkeys]
# Hotkeys úteis para desenvolvimento
Frame_Advance=F
Pause=Space
Fast_Forward=Tab
Reboot_Core=Ctrl+R
Open_ROM=Ctrl+O
Save_State=F5
Load_State=F9

[Debugging]
# Habilitar ferramentas de debug
EnableDebugger=true
BreakOnStart=false
ShowMemoryDomains=true
"""
            
            config_path.write_text(config_content, encoding='utf-8')
            
            # Criar script de lançamento para ROMs SGDK
            launch_script_content = f"""@echo off
REM Script para executar ROMs SGDK no BizHawk
REM Uso: launch_sgdk_rom.bat caminho_para_rom.bin

if "%1"=="" (
    echo Uso: %0 caminho_para_rom.bin
    pause
    exit /b 1
)

if not exist "%1" (
    echo Erro: ROM não encontrada: %1
    pause
    exit /b 1
)

echo Executando ROM SGDK: %1
echo Emulador: BizHawk (Otimizado para SGDK)
echo.

"{bizhawk_path}\\\\EmuHawk.exe" "%1"
"""
            
            launch_script_path = bizhawk_path / "launch_sgdk_rom.bat"
            launch_script_path.write_text(launch_script_content, encoding='utf-8')
            
            self.logger.info("✅ BizHawk configurado para desenvolvimento SGDK")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao configurar BizHawk: {e}")
            return False
    
    def _create_emulator_scripts(self) -> bool:
        """Cria scripts de conveniência para lançar emuladores"""
        try:
            scripts_path = self.gendk_path / "scripts"
            scripts_path.mkdir(exist_ok=True)
            
            # Script principal de lançamento
            main_script_content = f"""@echo off
REM Script principal para executar ROMs SGDK
REM Gerado automaticamente pelo RetroDevKitManager

setlocal enabledelayedexpansion

echo ========================================
echo    SGDK ROM Launcher
echo ========================================
echo.

if "%1"=="" (
    echo Uso: %0 caminho_para_rom.bin [emulador]
    echo.
    echo Emuladores disponíveis:
    echo   1. BizHawk (padrão)
    echo   2. Blastem
    echo   3. GensKMod
    echo.
    echo Exemplo: %0 minha_rom.bin bizhawk
    pause
    exit /b 1
)

set ROM_PATH=%1
set EMULATOR=%2

if "%EMULATOR%"=="" set EMULATOR=bizhawk

if not exist "%ROM_PATH%" (
    echo Erro: ROM não encontrada: %ROM_PATH%
    pause
    exit /b 1
)

echo ROM: %ROM_PATH%
echo Emulador: %EMULATOR%
echo.

if /i "%EMULATOR%"=="bizhawk" (
    if exist "{self.emulators_path}\\BizHawk\\EmuHawk.exe" (
        echo Executando no BizHawk...
        "{self.emulators_path}\\BizHawk\\EmuHawk.exe" "%ROM_PATH%"
    ) else (
        echo Erro: BizHawk não encontrado
        pause
        exit /b 1
    )
) else if /i "%EMULATOR%"=="blastem" (
    if exist "{self.emulators_path}\\Blastem\\blastem.exe" (
        echo Executando no Blastem...
        "{self.emulators_path}\\Blastem\\blastem.exe" "%ROM_PATH%"
    ) else (
        echo Erro: Blastem não encontrado
        pause
        exit /b 1
    )
) else if /i "%EMULATOR%"=="genskmod" (
    if exist "{self.emulators_path}\\GensKMod\\Gens.exe" (
        echo Executando no GensKMod...
        "{self.emulators_path}\\GensKMod\\Gens.exe" "%ROM_PATH%"
    ) else (
        echo Erro: GensKMod não encontrado
        pause
        exit /b 1
    )
) else (
    echo Erro: Emulador desconhecido: %EMULATOR%
    echo Emuladores disponíveis: bizhawk, blastem, genskmod
    pause
    exit /b 1
)
"""
            
            main_script_path = scripts_path / "run_sgdk_rom.bat"
            main_script_path.write_text(main_script_content, encoding='utf-8')
            
            # Script para compilar e executar
            compile_and_run_content = f"""@echo off
REM Script para compilar projeto SGDK e executar no emulador
REM Uso: compile_and_run.bat [projeto] [emulador]

setlocal enabledelayedexpansion

set PROJECT_DIR=%1
set EMULATOR=%2

if "%PROJECT_DIR%"=="" set PROJECT_DIR=.
if "%EMULATOR%"=="" set EMULATOR=bizhawk

echo ========================================
echo    SGDK Compile & Run
echo ========================================
echo.
echo Projeto: %PROJECT_DIR%
echo Emulador: %EMULATOR%
echo.

cd /d "%PROJECT_DIR%"

if not exist "Makefile" (
    echo Erro: Makefile não encontrado no diretório: %PROJECT_DIR%
    pause
    exit /b 1
)

echo Compilando projeto...
make clean
make

if errorlevel 1 (
    echo Erro na compilação!
    pause
    exit /b 1
)

echo.
echo Compilação concluída com sucesso!
echo.

for %%f in (*.bin) do (
    echo Executando ROM: %%f
    "{scripts_path}\run_sgdk_rom.bat" "%%f" "%EMULATOR%"
    goto :found
)

echo Erro: Nenhuma ROM (.bin) encontrada!
pause
exit /b 1

:found
echo.
echo Concluído!
"""
            
            compile_script_path = scripts_path / "compile_and_run.bat"
            compile_script_path.write_text(compile_and_run_content, encoding='utf-8')
            
            self.logger.info("✅ Scripts de emuladores criados com sucesso")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao criar scripts de emuladores: {e}")
            return False
    
    def _install_genesis_code_vscode(self) -> bool:
        """Instala a extensão Genesis Code no VS Code"""
        try:
            self.logger.info("📦 Instalando Genesis Code no VS Code...")
            
            # Verificar se VS Code está instalado
            if not shutil.which('code'):
                self.logger.warning("⚠️ VS Code não encontrado no PATH")
                return False
            
            # Instalar extensão Genesis Code
            result = subprocess.run([
                'code', '--install-extension', 'zerasul.genesis-code'
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                self.logger.info("✅ Genesis Code instalado no VS Code")
                return True
            else:
                self.logger.error(f"❌ Erro ao instalar Genesis Code: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Erro ao instalar Genesis Code no VS Code: {e}")
            return False
    
    def _install_genesis_code_vscode_insiders(self) -> bool:
        """Instala a extensão Genesis Code no VS Code Insiders"""
        try:
            self.logger.info("📦 Instalando Genesis Code no VS Code Insiders...")
            
            # Verificar se VS Code Insiders está instalado
            if not shutil.which('code-insiders'):
                self.logger.warning("⚠️ VS Code Insiders não encontrado no PATH")
                return False
            
            # Instalar extensão Genesis Code
            result = subprocess.run([
                'code-insiders', '--install-extension', 'zerasul.genesis-code'
            ], capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                self.logger.info("✅ Genesis Code instalado no VS Code Insiders")
                return True
            else:
                self.logger.error(f"❌ Erro ao instalar Genesis Code: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Erro ao instalar Genesis Code no VS Code Insiders: {e}")
            return False
    
    def _configure_vscode_workspace(self) -> bool:
        """Configura workspace do VS Code para desenvolvimento SGDK"""
        try:
            self.logger.info("⚙️ Configurando workspace VS Code para SGDK...")
            
            # Criar diretório de configuração
            vscode_config_path = self.gendk_path / ".vscode"
            vscode_config_path.mkdir(exist_ok=True)
            
            # Configuração de settings.json
            settings_config = {
                "C_Cpp.default.includePath": [
                    str(self.sgdk_path / "inc"),
                    "${workspaceFolder}/inc",
                    "${workspaceFolder}/src"
                ],
                "C_Cpp.default.defines": [
                    "__GENESIS__",
                    "__SGDK__"
                ],
                "C_Cpp.default.compilerPath": str(self.sgdk_path / "bin" / "gcc"),
                "C_Cpp.default.cStandard": "c99",
                "files.associations": {
                    "*.res": "plaintext",
                    "*.h": "c",
                    "*.c": "c"
                },
                "terminal.integrated.env.windows": {
                    "GDK": str(self.sgdk_path),
                    "GDK_WIN": str(self.sgdk_path),
                    "PATH": f"{self.sgdk_path / 'bin'};${env:PATH}"
                },
                "terminal.integrated.env.linux": {
                    "GDK": str(self.sgdk_path),
                    "PATH": f"{self.sgdk_path / 'bin'}:${env:PATH}"
                }
            }
            
            settings_path = vscode_config_path / "settings.json"
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings_config, f, indent=4)
            
            # Configuração de tasks.json para compilação
            tasks_config = {
                "version": "2.0.0",
                "tasks": [
                    {
                        "label": "SGDK: Build Project",
                        "type": "shell",
                        "command": "make",
                        "group": {
                            "kind": "build",
                            "isDefault": True
                        },
                        "presentation": {
                            "echo": True,
                            "reveal": "always",
                            "focus": False,
                            "panel": "shared"
                        },
                        "problemMatcher": "$gcc"
                    },
                    {
                        "label": "SGDK: Clean Project",
                        "type": "shell",
                        "command": "make",
                        "args": ["clean"],
                        "group": "build"
                    },
                    {
                        "label": "SGDK: Build and Run",
                        "type": "shell",
                        "command": "make",
                        "args": ["run"],
                        "group": "build",
                        "dependsOn": "SGDK: Build Project"
                    }
                ]
            }
            
            tasks_path = vscode_config_path / "tasks.json"
            with open(tasks_path, 'w', encoding='utf-8') as f:
                json.dump(tasks_config, f, indent=4)
            
            # Configuração de launch.json para debugging
            launch_config = {
                "version": "0.2.0",
                "configurations": [
                    {
                        "name": "SGDK Debug",
                        "type": "cppdbg",
                        "request": "launch",
                        "program": "${workspaceFolder}/out/${workspaceFolderBasename}.bin",
                        "args": [],
                        "stopAtEntry": False,
                        "cwd": "${workspaceFolder}",
                        "environment": [],
                        "externalConsole": False,
                        "MIMode": "gdb",
                        "preLaunchTask": "SGDK: Build Project"
                    }
                ]
            }
            
            launch_path = vscode_config_path / "launch.json"
            with open(launch_path, 'w', encoding='utf-8') as f:
                json.dump(launch_config, f, indent=4)
            
            self.logger.info("✅ Workspace VS Code configurado para SGDK")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao configurar workspace VS Code: {e}")
            return False
    
    def create_sgdk_project_template(self, project_name: str, project_path: Path) -> bool:
        """Cria template de projeto SGDK melhorado"""
        self.logger.info(f"Criando projeto SGDK: {project_name}")
        
        # Criar estrutura de diretórios
        dirs = ['src', 'res', 'inc', 'out']
        for dir_name in dirs:
            (project_path / dir_name).mkdir(parents=True, exist_ok=True)
            
        # Criar Makefile melhorado
        makefile_content = self._generate_improved_makefile(project_name)
        with open(project_path / 'Makefile', 'w') as f:
            f.write(makefile_content)
            
        # Criar main.c básico
        main_content = self._generate_improved_main_c(project_name)
        with open(project_path / 'src' / 'main.c', 'w') as f:
            f.write(main_content)
            
        # Criar arquivo de recursos
        resources_content = "// Arquivo de recursos\n// Adicione aqui sprites, música, etc.\n"
        with open(project_path / 'res' / 'resources.res', 'w') as f:
            f.write(resources_content)
            
        # Criar README específico para SGDK
        readme_content = self._generate_sgdk_readme(project_name)
        with open(project_path / 'README.md', 'w') as f:
            f.write(readme_content)
            
        return True
    
    def _generate_improved_makefile(self, project_name: str) -> str:
        """Gera Makefile melhorado para projetos SGDK"""
        return f"""# Makefile para projeto SGDK: {project_name}
# Gerado automaticamente pelo RetroDevKitManager

# Configurações do projeto
PROJECT_NAME = {project_name}
GDK = $(GDK_WIN)

# Diretórios
SRC_DIR = src
RES_DIR = res
INC_DIR = inc
OUT_DIR = out

# Arquivos fonte
SRCS = $(wildcard $(SRC_DIR)/*.c)
RES = $(wildcard $(RES_DIR)/*.res)
OBJS = $(SRCS:.c=.o)
RES_OBJS = $(RES:.res=.o)

# Configurações do compilador
CC = $(GDK)/bin/gcc
LD = $(GDK)/bin/ld
RESCOMP = java -jar $(GDK)/bin/rescomp.jar
BINTOS = $(GDK)/bin/bintos

# Flags
CFLAGS = -I$(INC_DIR) -I$(GDK)/inc -O2 -Wall
LDFLAGS = -L$(GDK)/lib -lmd

# Regra principal
all: $(OUT_DIR)/$(PROJECT_NAME).bin

# Criar diretório de saída
$(OUT_DIR):
\tmkdir -p $(OUT_DIR)

# Compilar recursos
%.o: %.res
\t$(RESCOMP) $< $@

# Compilar código C
%.o: %.c
\t$(CC) $(CFLAGS) -c $< -o $@

# Linkar e gerar ROM
$(OUT_DIR)/$(PROJECT_NAME).bin: $(OUT_DIR) $(OBJS) $(RES_OBJS)
\t$(CC) $(OBJS) $(RES_OBJS) $(LDFLAGS) -o $(OUT_DIR)/$(PROJECT_NAME).elf
\t$(BINTOS) $(OUT_DIR)/$(PROJECT_NAME).elf $(OUT_DIR)/$(PROJECT_NAME).bin

# Limpeza
clean:
\trm -f $(OBJS) $(RES_OBJS)
\trm -rf $(OUT_DIR)

# Executar no emulador (BlastEm)
run: $(OUT_DIR)/$(PROJECT_NAME).bin
\tblastem $(OUT_DIR)/$(PROJECT_NAME).bin

.PHONY: all clean run
"""
    
    def _generate_improved_main_c(self, project_name: str) -> str:
        """Gera main.c melhorado para projetos SGDK"""
        return f"""/*
 * {project_name}
 * Projeto SGDK gerado automaticamente
 * 
 * Para mais informações sobre SGDK:
 * https://github.com/Stephane-D/SGDK
 */

#include <genesis.h>

// Função principal
int main()
{{
    // Inicializar sistema
    SYS_disableInts();
    
    // Configurar paleta
    PAL_setPalette(PAL0, palette_grey, DMA);
    
    // Limpar tela
    VDP_clearPlane(BG_A, TRUE);
    VDP_clearPlane(BG_B, TRUE);
    
    // Exibir texto de boas-vindas
    VDP_drawText("Bem-vindo ao {project_name}!", 10, 10);
    VDP_drawText("Projeto SGDK funcionando!", 10, 12);
    VDP_drawText("Pressione START para continuar", 8, 14);
    
    // Reabilitar interrupções
    SYS_enableInts();
    
    // Loop principal
    while(1)
    {{
        // Ler controles
        u16 joy = JOY_readJoypad(JOY_1);
        
        // Verificar se START foi pressionado
        if(joy & BUTTON_START)
        {{
            VDP_drawText("START pressionado!", 10, 16);
        }}
        
        // Aguardar próximo frame
        SYS_doVBlankProcess();
    }}
    
    return 0;
}}
"""
    
    def _generate_sgdk_readme(self, project_name: str) -> str:
        """Gera README específico para projetos SGDK"""
        return f"""# {project_name}

Projeto de desenvolvimento para Sega Mega Drive usando SGDK.

## Sobre o SGDK

O SGDK (Sega Genesis Development Kit) é um kit de desenvolvimento moderno para criar jogos para o Sega Mega Drive/Genesis.

## Estrutura do Projeto

```
{project_name}/
├── src/          # Código fonte C
├── res/          # Recursos (sprites, música, etc.)
├── inc/          # Headers personalizados
├── out/          # ROMs compiladas
├── Makefile      # Script de compilação
└── README.md     # Este arquivo
```

## Como Compilar

1. Certifique-se de que o SGDK está instalado e configurado
2. Execute: `make`
3. A ROM será gerada em `out/{project_name}.bin`

## Como Executar

### No Emulador
```bash
make run  # Executa no BlastEm (se instalado)
```

### Outros Emuladores
- **Gens**: Abra `out/{project_name}.bin`
- **Fusion**: Abra `out/{project_name}.bin`
- **RetroArch**: Use o core Genesis Plus GX

## Recursos Úteis

- [Documentação SGDK](https://github.com/Stephane-D/SGDK/wiki)
- [Tutoriais SGDK](https://www.ohsat.com/tutorial/)
- [Comunidade SGDK](https://discord.gg/xmnBWQS)

## Desenvolvimento

### Adicionando Sprites
1. Coloque imagens PNG em `res/`
2. Adicione ao arquivo `res/resources.res`
3. Recompile com `make`

### Adicionando Música
1. Converta música para formato VGM
2. Adicione ao `res/resources.res`
3. Use as funções de áudio do SGDK

## Limpeza

```bash
make clean  # Remove arquivos temporários
```

---

Gerado automaticamente pelo RetroDevKitManager
"""


class SGDKDiagnostics:
    """Diagnósticos específicos para instalação SGDK"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        
    def run_full_diagnostics(self, sgdk_path: Path) -> Dict[str, bool]:
        """Executa diagnósticos completos do SGDK"""
        results = {}
        
        # Verificar Java
        results['java_available'] = self._check_java()
        results['java_version_ok'] = self._check_java_version()
        
        # Verificar Make
        results['make_available'] = self._check_make()
        
        # Verificar estrutura SGDK
        results['sgdk_structure'] = self._check_sgdk_structure(sgdk_path)
        results['sgdk_binaries'] = self._check_sgdk_binaries(sgdk_path)
        
        # Verificar variáveis de ambiente
        results['env_vars'] = self._check_environment_variables(sgdk_path)
        
        # Teste de compilação
        results['compilation_test'] = self._test_compilation(sgdk_path)
        
        return results
    
    def _check_java(self) -> bool:
        """Verifica se Java está disponível"""
        try:
            result = subprocess.run(['java', '-version'], capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def _check_java_version(self) -> bool:
        """Verifica se a versão do Java é adequada (8+)"""
        try:
            result = subprocess.run(['java', '-version'], capture_output=True, text=True)
            output = result.stderr  # Java imprime versão no stderr
            
            # Procurar por padrão de versão
            import re
            version_match = re.search(r'version "(\d+)\.(\d+)', output)
            if version_match:
                major = int(version_match.group(1))
                minor = int(version_match.group(2))
                
                # Java 8+ (1.8+) ou Java 11+
                return (major == 1 and minor >= 8) or major >= 11
                
        except Exception:
            pass
            
        return False
    
    def _check_make(self) -> bool:
        """Verifica se Make está disponível"""
        try:
            result = subprocess.run(['make', '--version'], capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            return False
    
    def _check_sgdk_structure(self, sgdk_path: Path) -> bool:
        """Verifica estrutura de diretórios do SGDK"""
        required_dirs = ['bin', 'inc', 'lib', 'res']
        return all((sgdk_path / dir_name).exists() for dir_name in required_dirs)
    
    def _check_sgdk_binaries(self, sgdk_path: Path) -> bool:
        """Verifica binários essenciais do SGDK"""
        required_files = [
            'bin/rescomp.jar',
            'inc/genesis.h',
            'lib/libmd.a'
        ]
        return all((sgdk_path / file_path).exists() for file_path in required_files)
    
    def _check_environment_variables(self, sgdk_path: Path) -> bool:
        """Verifica variáveis de ambiente"""
        gdk = os.environ.get('GDK')
        gdk_win = os.environ.get('GDK_WIN')
        java_home = os.environ.get('JAVA_HOME')
        
        # Pelo menos uma das variáveis GDK deve estar definida
        gdk_ok = gdk or gdk_win
        
        # JAVA_HOME deve estar definido ou Java deve estar no PATH
        java_ok = java_home or shutil.which('java')
        
        return bool(gdk_ok and java_ok)
    
    def _test_compilation(self, sgdk_path: Path) -> bool:
        """Testa compilação básica"""
        try:
            # Criar projeto temporário para teste
            import tempfile
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Criar main.c simples
                main_c = temp_path / 'main.c'
                with open(main_c, 'w') as f:
                    f.write('#include <genesis.h>\nint main() { return 0; }')
                
                # Tentar compilar
                gcc_path = sgdk_path / 'bin' / 'gcc'
                if not gcc_path.exists():
                    return False
                    
                result = subprocess.run([
                    str(gcc_path),
                    '-I', str(sgdk_path / 'inc'),
                    '-c', str(main_c),
                    '-o', str(temp_path / 'main.o')
                ], capture_output=True, text=True)
                
                return result.returncode == 0
                
        except Exception:
            return False
    
    def generate_diagnostic_report(self, results: Dict[str, bool]) -> str:
        """Gera relatório de diagnóstico"""
        report = ["=== RELATÓRIO DE DIAGNÓSTICO SGDK ===", ""]
        
        status_icon = lambda x: "✅" if x else "❌"
        
        report.extend([
            f"{status_icon(results.get('java_available', False))} Java disponível",
            f"{status_icon(results.get('java_version_ok', False))} Versão do Java adequada (8+)",
            f"{status_icon(results.get('make_available', False))} Make disponível",
            f"{status_icon(results.get('sgdk_structure', False))} Estrutura SGDK correta",
            f"{status_icon(results.get('sgdk_binaries', False))} Binários SGDK presentes",
            f"{status_icon(results.get('env_vars', False))} Variáveis de ambiente configuradas",
            f"{status_icon(results.get('compilation_test', False))} Teste de compilação",
            ""
        ])
        
        # Resumo
        total_checks = len(results)
        passed_checks = sum(results.values())
        
        report.extend([
            f"Resumo: {passed_checks}/{total_checks} verificações passaram",
            ""
        ])
        
        # Recomendações
        if not results.get('java_available', False):
            report.append("⚠️  Instale Java 8 ou superior")
        if not results.get('make_available', False):
            report.append("⚠️  Instale Make/Build Tools")
        if not results.get('sgdk_structure', False):
            report.append("⚠️  Reinstale SGDK - estrutura incorreta")
        if not results.get('env_vars', False):
            report.append("⚠️  Configure variáveis de ambiente GDK e JAVA_HOME")
            
        return "\n".join(report)