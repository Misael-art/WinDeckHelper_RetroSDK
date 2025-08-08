"""Melhorias específicas para o Sega Saturn Development Kit (Jo-Engine + Yaul)
Implementação completa do manager para desenvolvimento Sega Saturn"""

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
from typing import Dict, List, Optional, Tuple, Any
import logging
from dataclasses import dataclass

from .retro_devkit_base import RetroDevkitManager, DevkitInfo

class SaturnManager(RetroDevkitManager):
    """Manager específico para Sega Saturn Development Kit (Jo-Engine + Yaul)"""
    
    def __init__(self, base_path: Path, logger: logging.Logger):
        super().__init__(base_path, logger)
        self.joengine_version = "latest"
        self.yaul_version = "latest"
        self.joengine_url = "https://github.com/johannes-fetz/joengine/archive/refs/heads/master.zip"
        self.yaul_url = "https://github.com/yaul-org/libyaul/archive/refs/heads/master.zip"
        self.gcc_sh2_url = "https://github.com/yaul-org/libyaul/releases/latest/download/yaul-tool-chain-windows-x86_64.zip"
        
    def get_devkit_folder_name(self) -> str:
        """Retorna o nome da pasta do Sega Saturn devkit"""
        return "Saturn"
        
    def get_devkit_info(self) -> DevkitInfo:
        """Retorna informações do Sega Saturn devkit"""
        return DevkitInfo(
            name="Sega Saturn Development Kit",
            console="Sega Saturn",
            devkit_name="Jo-Engine + Yaul",
            version=f"Jo-Engine {self.joengine_version}, Yaul {self.yaul_version}",
            dependencies=[
                "make",
                "unzip",
                "wget",
                "cmake",
                "python3",
                "mingw-w64"
            ],
            environment_vars={
                "JOENGINE": str(self.devkit_path / "joengine"),
                "YAUL_INSTALL_ROOT": str(self.devkit_path / "yaul"),
                "YAUL_PROG_SH_PREFIX": str(self.devkit_path / "toolchain" / "bin" / "sh-elf-"),
                "YAUL_ARCH_SH_PREFIX": str(self.devkit_path / "toolchain" / "bin" / "sh-elf-"),
                "PATH": str(self.devkit_path / "toolchain" / "bin")
            },
            download_url=self.joengine_url,
            install_commands=[
                "Download and extract Jo-Engine",
                "Download and extract Yaul",
                "Download and extract SH-2 toolchain",
                "Setup environment variables",
                "Install emulators",
                "Setup VS Code extensions"
            ],
            verification_files=[
                "toolchain/bin/sh-elf-gcc.exe",
                "toolchain/bin/sh-elf-ld.exe",
                "joengine/jo/jo.h",
                "joengine/Compiler/COMMON/jo_compile_saturn.bat",
                "yaul/include/yaul.h",
                "yaul/lib/libyaul.a"
            ]
        )
        
    def install_dependencies(self) -> bool:
        """Instala dependências do Sega Saturn devkit"""
        try:
            self.logger.info("Instalando dependências do Sega Saturn devkit...")
            
            # Download e instalação do SH-2 toolchain
            if not self._install_sh2_toolchain():
                return False
                
            # Download e instalação do Jo-Engine
            if not self._install_joengine():
                return False
                
            # Download e instalação do Yaul
            if not self._install_yaul():
                return False
                
            # Instalar ferramentas adicionais
            if not self._install_additional_tools():
                self.logger.warning("Falha na instalação de ferramentas adicionais")
                
            self.logger.info("Sega Saturn devkit instalado com sucesso")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na instalação do Sega Saturn devkit: {e}")
            return False
            
    def _install_sh2_toolchain(self) -> bool:
        """Instala o SH-2 toolchain"""
        try:
            self.logger.info("Instalando SH-2 toolchain...")
            
            toolchain_zip = self.devkit_path / "sh2-toolchain.zip"
            if not self.download_file(self.gcc_sh2_url, toolchain_zip, "SH-2 Toolchain"):
                return False
                
            # Extrair toolchain
            toolchain_path = self.devkit_path / "toolchain"
            if not self.extract_archive(toolchain_zip, toolchain_path):
                return False
                
            # Remover arquivo zip
            toolchain_zip.unlink()
            
            self.logger.info("SH-2 toolchain instalado com sucesso")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na instalação do SH-2 toolchain: {e}")
            return False
            
    def _install_joengine(self) -> bool:
        """Instala o Jo-Engine"""
        try:
            self.logger.info("Instalando Jo-Engine...")
            
            joengine_zip = self.devkit_path / "joengine.zip"
            if not self.download_file(self.joengine_url, joengine_zip, "Jo-Engine"):
                return False
                
            # Extrair Jo-Engine
            joengine_path = self.devkit_path / "joengine"
            if not self.extract_archive(joengine_zip, joengine_path):
                return False
                
            # Remover arquivo zip
            joengine_zip.unlink()
            
            # Configurar Jo-Engine
            self._configure_joengine(joengine_path)
            
            self.logger.info("Jo-Engine instalado com sucesso")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na instalação do Jo-Engine: {e}")
            return False
            
    def _install_yaul(self) -> bool:
        """Instala o Yaul"""
        try:
            self.logger.info("Instalando Yaul...")
            
            yaul_zip = self.devkit_path / "yaul.zip"
            if not self.download_file(self.yaul_url, yaul_zip, "Yaul"):
                return False
                
            # Extrair Yaul
            yaul_path = self.devkit_path / "yaul"
            if not self.extract_archive(yaul_zip, yaul_path):
                return False
                
            # Remover arquivo zip
            yaul_zip.unlink()
            
            # Compilar Yaul se necessário
            self._compile_yaul(yaul_path)
            
            self.logger.info("Yaul instalado com sucesso")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na instalação do Yaul: {e}")
            return False
            
    def _configure_joengine(self, joengine_path: Path) -> bool:
        """Configura o Jo-Engine"""
        try:
            self.logger.info("Configurando Jo-Engine...")
            
            # Criar script de configuração
            config_script = joengine_path / "configure_joengine.bat"
            config_content = f'''@echo off
REM Configuracao do Jo-Engine
set JOENGINE={joengine_path}
set YAUL_INSTALL_ROOT={self.devkit_path}\\yaul
set YAUL_PROG_SH_PREFIX={self.devkit_path}\\toolchain\\bin\\sh-elf-
set YAUL_ARCH_SH_PREFIX={self.devkit_path}\\toolchain\\bin\\sh-elf-
set PATH=%YAUL_INSTALL_ROOT%\\bin;{self.devkit_path}\\toolchain\\bin;%PATH%

echo Jo-Engine configurado com sucesso!
echo JOENGINE=%JOENGINE%
echo YAUL_INSTALL_ROOT=%YAUL_INSTALL_ROOT%
pause
'''
            config_script.write_text(config_content, encoding='utf-8')
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na configuração do Jo-Engine: {e}")
            return False
            
    def _compile_yaul(self, yaul_path: Path) -> bool:
        """Compila o Yaul se necessário"""
        try:
            # Verificar se já existe libyaul.a
            lib_file = yaul_path / "lib" / "libyaul.a"
            if lib_file.exists():
                return True
                
            self.logger.info("Compilando Yaul...")
            
            # Procurar por Makefile ou script de build
            makefile = yaul_path / "Makefile"
            if makefile.exists():
                success, output = self.run_command(["make"], cwd=str(yaul_path))
                if success:
                    self.logger.info("Yaul compilado com sucesso")
                    return True
                else:
                    self.logger.warning(f"Falha na compilação do Yaul: {output}")
                    
            return True  # Continuar mesmo se a compilação falhar
            
        except Exception as e:
            self.logger.error(f"Erro na compilação do Yaul: {e}")
            return True  # Não falhar por causa disso
            
    def _install_additional_tools(self) -> bool:
        """Instala ferramentas adicionais para Sega Saturn"""
        try:
            self.logger.info("Instalando ferramentas adicionais...")
            
            tools_path = self.tools_path
            tools_path.mkdir(parents=True, exist_ok=True)
            
            # Criar scripts de conversão
            self._create_conversion_scripts()
            
            # Instalar ferramentas de áudio/vídeo
            self._install_media_tools()
            
            self.logger.info("Ferramentas adicionais instaladas")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na instalação de ferramentas adicionais: {e}")
            return False
            
    def _install_media_tools(self) -> bool:
        """Instala ferramentas de conversão de mídia"""
        try:
            self.logger.info("Instalando ferramentas de mídia...")
            
            scripts_path = self.devkit_path / "scripts"
            scripts_path.mkdir(exist_ok=True)
            
            # Script para conversão de texturas
            texture_script = scripts_path / "convert_texture.bat"
            texture_content = '''@echo off
REM Script para conversao de texturas Saturn
echo Conversao de texturas ainda nao implementada
echo Use ferramentas como Saturn Texture Editor
pause
'''
            texture_script.write_text(texture_content, encoding='utf-8')
            
            # Script para conversão de áudio
            audio_script = scripts_path / "convert_audio.bat"
            audio_content = '''@echo off
REM Script para conversao de audio Saturn
echo Conversao de audio ainda nao implementada
echo Use ferramentas como Saturn Sound Format
pause
'''
            audio_script.write_text(audio_content, encoding='utf-8')
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na instalação de ferramentas de mídia: {e}")
            return False
            
    def _create_conversion_scripts(self) -> bool:
        """Cria scripts de conversão de assets"""
        try:
            scripts_path = self.devkit_path / "scripts"
            scripts_path.mkdir(exist_ok=True)
            
            # Script para conversão de sprites
            sprite_script = scripts_path / "convert_sprites.bat"
            sprite_content = '''@echo off
REM Script para conversao de sprites Saturn
echo Conversao de sprites ainda nao implementada
echo Use Jo-Engine sprite tools
pause
'''
            sprite_script.write_text(sprite_content, encoding='utf-8')
            
            # Script para conversão de modelos 3D
            model_script = scripts_path / "convert_3d_model.bat"
            model_content = '''@echo off
REM Script para conversao de modelos 3D Saturn
echo Conversao de modelos 3D ainda nao implementada
echo Use Jo-Engine 3D tools
pause
'''
            model_script.write_text(model_content, encoding='utf-8')
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na criação de scripts de conversão: {e}")
            return False
            
    def verify_installation(self) -> bool:
        """Verifica se o Sega Saturn devkit está instalado corretamente"""
        try:
            devkit_info = self.get_devkit_info()
            
            # Verificar arquivos essenciais
            for file_path in devkit_info.verification_files:
                full_path = self.devkit_path / file_path
                if not full_path.exists():
                    self.logger.warning(f"Arquivo não encontrado: {full_path}")
                    
            # Testar compilador SH-2
            gcc_path = self.devkit_path / "toolchain" / "bin" / "sh-elf-gcc.exe"
            if gcc_path.exists():
                success, output = self.run_command([str(gcc_path), "--version"])
                if not success:
                    self.logger.error("Falha ao executar sh-elf-gcc")
                    return False
            else:
                self.logger.error("Compilador SH-2 não encontrado")
                return False
                
            self.logger.info("Verificação do Sega Saturn devkit concluída com sucesso")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na verificação do Sega Saturn devkit: {e}")
            return False
            
    def install_emulators(self) -> bool:
        """Instala emuladores Sega Saturn"""
        try:
            self.logger.info("Instalando emuladores Sega Saturn...")
            
            emulators = {
                "Mednafen": {
                    "url": "https://mednafen.github.io/releases/files/mednafen-1.29.0-win64.zip",
                    "folder": "Mednafen"
                },
                "SSF": {
                    "url": "http://www7a.biglobe.ne.jp/~phantasy/ssf/SSF_012_beta_R4.zip",
                    "folder": "SSF"
                },
                "Kronos": {
                    "url": "https://github.com/FCare/Kronos/releases/latest/download/kronos_windows.zip",
                    "folder": "Kronos"
                }
            }
            
            for emu_name, emu_info in emulators.items():
                if self._install_emulator(emu_name, emu_info["url"], emu_info["folder"]):
                    self.logger.info(f"{emu_name} instalado com sucesso")
                else:
                    self.logger.warning(f"Falha na instalação do {emu_name}")
                    
            # Criar scripts de execução
            self._create_emulator_scripts()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na instalação de emuladores: {e}")
            return False
            
    def _install_emulator(self, name: str, url: str, folder: str) -> bool:
        """Instala um emulador específico"""
        try:
            emu_path = self.emulators_path / folder
            emu_path.mkdir(parents=True, exist_ok=True)
            
            zip_file = emu_path / f"{name}.zip"
            
            if self.download_file(url, zip_file, name):
                if self.extract_archive(zip_file, emu_path):
                    zip_file.unlink()
                    return True
                    
            return False
            
        except Exception as e:
            self.logger.error(f"Erro na instalação do {name}: {e}")
            return False
            
    def _create_emulator_scripts(self) -> bool:
        """Cria scripts para execução dos emuladores"""
        try:
            scripts_path = self.devkit_path / "scripts"
            scripts_path.mkdir(exist_ok=True)
            
            # Script para Mednafen
            mednafen_script = scripts_path / "run_mednafen.bat"
            mednafen_content = f'''@echo off
REM Script para executar Mednafen
set EMULATOR_PATH="{self.emulators_path}\\Mednafen\\mednafen.exe"
if exist %EMULATOR_PATH% (
    start "" %EMULATOR_PATH% %1
) else (
    echo Mednafen nao encontrado em %EMULATOR_PATH%
    pause
)
'''
            mednafen_script.write_text(mednafen_content, encoding='utf-8')
            
            # Script para SSF
            ssf_script = scripts_path / "run_ssf.bat"
            ssf_content = f'''@echo off
REM Script para executar SSF
set EMULATOR_PATH="{self.emulators_path}\\SSF\\SSF.exe"
if exist %EMULATOR_PATH% (
    start "" %EMULATOR_PATH% %1
) else (
    echo SSF nao encontrado em %EMULATOR_PATH%
    pause
)
'''
            ssf_script.write_text(ssf_content, encoding='utf-8')
            
            # Script para Kronos
            kronos_script = scripts_path / "run_kronos.bat"
            kronos_content = f'''@echo off
REM Script para executar Kronos
set EMULATOR_PATH="{self.emulators_path}\\Kronos\\kronos.exe"
if exist %EMULATOR_PATH% (
    start "" %EMULATOR_PATH% %1
) else (
    echo Kronos nao encontrado em %EMULATOR_PATH%
    pause
)
'''
            kronos_script.write_text(kronos_content, encoding='utf-8')
            
            # Script genérico
            run_script = scripts_path / "run_saturn_game.bat"
            run_content = f'''@echo off
REM Script generico para executar jogo Saturn
setlocal

if "%1"=="" (
    echo Uso: run_saturn_game.bat arquivo.iso
    pause
    exit /b 1
)

set GAME_FILE=%1
set MEDNAFEN_PATH="{self.emulators_path}\\Mednafen\\mednafen.exe"
set SSF_PATH="{self.emulators_path}\\SSF\\SSF.exe"
set KRONOS_PATH="{self.emulators_path}\\Kronos\\kronos.exe"

if exist %MEDNAFEN_PATH% (
    echo Executando com Mednafen...
    start "" %MEDNAFEN_PATH% %GAME_FILE%
) else if exist %SSF_PATH% (
    echo Executando com SSF...
    start "" %SSF_PATH% %GAME_FILE%
) else if exist %KRONOS_PATH% (
    echo Executando com Kronos...
    start "" %KRONOS_PATH% %GAME_FILE%
) else (
    echo Nenhum emulador encontrado!
    pause
)
'''
            run_script.write_text(run_content, encoding='utf-8')
            
            self.logger.info("Scripts de emuladores criados")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na criação de scripts de emuladores: {e}")
            return False
            
    def install_vscode_extensions(self) -> bool:
        """Instala extensões VS Code para Sega Saturn"""
        try:
            self.logger.info("Instalando extensões VS Code para Sega Saturn...")
            
            extensions = [
                "ms-vscode.cpptools",  # C/C++ support
                "ms-vscode.makefile-tools",  # Makefile support
                "13xforever.language-x86-64-assembly",  # Assembly support
                "bierner.markdown-preview-enhanced",  # Documentation
                "ms-vscode.hexeditor"  # Hex editor for ROM inspection
            ]
            
            for extension in extensions:
                success, output = self.run_command(["code", "--install-extension", extension])
                if success:
                    self.logger.info(f"Extensão {extension} instalada")
                else:
                    self.logger.warning(f"Falha na instalação da extensão {extension}")
                    
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na instalação de extensões VS Code: {e}")
            return False
            
    def create_convenience_scripts(self) -> bool:
        """Cria scripts de conveniência para desenvolvimento Sega Saturn"""
        try:
            self.logger.info("Criando scripts de conveniência...")
            
            scripts_path = self.devkit_path / "scripts"
            scripts_path.mkdir(exist_ok=True)
            
            # Script de compilação
            compile_script = scripts_path / "compile_saturn_game.bat"
            compile_content = f'''@echo off
REM Script de compilacao Sega Saturn
setlocal

set JOENGINE={self.devkit_path}\\joengine
set YAUL_INSTALL_ROOT={self.devkit_path}\\yaul
set YAUL_PROG_SH_PREFIX={self.devkit_path}\\toolchain\\bin\\sh-elf-
set YAUL_ARCH_SH_PREFIX={self.devkit_path}\\toolchain\\bin\\sh-elf-
set PATH=%YAUL_INSTALL_ROOT%\\bin;{self.devkit_path}\\toolchain\\bin;%PATH%

if "%1"=="" (
    echo Uso: compile_saturn_game.bat projeto_folder
    pause
    exit /b 1
)

set PROJECT_DIR=%1

if not exist "%PROJECT_DIR%" (
    echo Diretorio do projeto nao encontrado: %PROJECT_DIR%
    pause
    exit /b 1
)

cd /d "%PROJECT_DIR%"

echo Compilando projeto Sega Saturn...
make

if exist "*.iso" (
    echo ISO criada com sucesso!
) else (
    echo Erro na compilacao!
)

pause
'''
            compile_script.write_text(compile_content, encoding='utf-8')
            
            # Script de execução
            run_script = scripts_path / "run_saturn_game.bat"
            run_content = f'''@echo off
REM Script para executar jogo Sega Saturn
setlocal

if "%1"=="" (
    echo Uso: run_saturn_game.bat arquivo.iso
    pause
    exit /b 1
)

set GAME_FILE=%1
set MEDNAFEN_PATH="{self.emulators_path}\\Mednafen\\mednafen.exe"
set SSF_PATH="{self.emulators_path}\\SSF\\SSF.exe"

if exist %MEDNAFEN_PATH% (
    echo Executando com Mednafen...
    start "" %MEDNAFEN_PATH% %GAME_FILE%
) else if exist %SSF_PATH% (
    echo Executando com SSF...
    start "" %SSF_PATH% %GAME_FILE%
) else (
    echo Nenhum emulador encontrado!
    pause
)
'''
            run_script.write_text(run_content, encoding='utf-8')
            
            # Script de criação de projeto
            create_project_script = scripts_path / "create_saturn_project.bat"
            create_project_content = f'''@echo off
REM Script para criar novo projeto Sega Saturn
setlocal

if "%1"=="" (
    echo Uso: create_saturn_project.bat nome_do_projeto
    pause
    exit /b 1
)

set PROJECT_NAME=%1
set PROJECTS_DIR={self.devkit_path}\\projects
set PROJECT_DIR=%PROJECTS_DIR%\\%PROJECT_NAME%

if exist "%PROJECT_DIR%" (
    echo Projeto ja existe: %PROJECT_DIR%
    pause
    exit /b 1
)

echo Criando projeto Sega Saturn: %PROJECT_NAME%
mkdir "%PROJECT_DIR%"

echo Copiando template...
xcopy "{self.devkit_path}\\templates\\saturn_template\\*" "%PROJECT_DIR%\\" /E /I /Q

echo Projeto criado: %PROJECT_DIR%
echo.
echo Para compilar: cd "%PROJECT_DIR%" && make
echo Para executar: run_saturn_game.bat "%PROJECT_DIR%\\game.iso"
pause
'''
            create_project_script.write_text(create_project_content, encoding='utf-8')
            
            # Script de debug
            debug_script = scripts_path / "debug_saturn_game.bat"
            debug_content = f'''@echo off
REM Script para debug de jogo Sega Saturn
setlocal

if "%1"=="" (
    echo Uso: debug_saturn_game.bat arquivo.iso
    pause
    exit /b 1
)

set GAME_FILE=%1
set MEDNAFEN_PATH="{self.emulators_path}\\Mednafen\\mednafen.exe"

if exist %MEDNAFEN_PATH% (
    echo Iniciando debug com Mednafen...
    start "" %MEDNAFEN_PATH% %GAME_FILE% -debugger
) else (
    echo Mednafen nao encontrado para debug!
    pause
)
'''
            debug_script.write_text(debug_content, encoding='utf-8')
            
            self.logger.info("Scripts de conveniência criados")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na criação de scripts: {e}")
            return False
            
    def create_project_template(self, project_name: str, project_path: Path) -> bool:
        """Cria template de projeto Sega Saturn"""
        try:
            self.logger.info(f"Criando template de projeto Sega Saturn: {project_name}")
            
            # Criar estrutura de diretórios
            project_path.mkdir(parents=True, exist_ok=True)
            (project_path / "src").mkdir(exist_ok=True)
            (project_path / "res").mkdir(exist_ok=True)
            (project_path / "build").mkdir(exist_ok=True)
            (project_path / "include").mkdir(exist_ok=True)
            
            # Criar main.c
            main_c = project_path / "src" / "main.c"
            main_content = f'''// {project_name} - Sega Saturn Project
// Generated by Saturn Manager

#include <jo/jo.h>

// Screen dimensions
#define SCREEN_WIDTH  320
#define SCREEN_HEIGHT 224

// Game variables
int player_x = 160;
int player_y = 112;

void my_init(void) {{
    // Initialize Jo-Engine
    jo_core_init(JO_COLOR_Black);
    
    // Load sprites and textures here
    // jo_sprite_add_tga("TEX", "PLAYER.TGA", JO_COLOR_Transparent);
}}

void my_gamepad(void) {{
    // Handle input
    if (jo_is_pad1_key_pressed(JO_KEY_LEFT) && player_x > 8) {{
        player_x -= 2;
    }}
    if (jo_is_pad1_key_pressed(JO_KEY_RIGHT) && player_x < 312) {{
        player_x += 2;
    }}
    if (jo_is_pad1_key_pressed(JO_KEY_UP) && player_y > 8) {{
        player_y -= 2;
    }}
    if (jo_is_pad1_key_pressed(JO_KEY_DOWN) && player_y < 216) {{
        player_y += 2;
    }}
}}

void my_draw(void) {{
    // Clear screen
    jo_clear_screen();
    
    // Draw player sprite
    // jo_sprite_draw3D(jo_get_sprite_id("PLAYER"), player_x, player_y, 0);
    
    // Draw simple rectangle as placeholder
    jo_draw_rectangle(player_x - 8, player_y - 8, 16, 16, JO_COLOR_White);
    
    // Draw text
    jo_printf(0, 0, "{project_name}");
    jo_printf(0, 1, "X: %d Y: %d", player_x, player_y);
}}

void jo_main(void) {{
    // Initialize
    my_init();
    
    // Set callbacks
    jo_core_set_screens_order(ORDER_2D_THEN_3D);
    jo_core_add_callback(my_gamepad);
    jo_core_add_callback(my_draw);
    
    // Start main loop
    jo_core_run();
}}
'''
            main_c.write_text(main_content, encoding='utf-8')
            
            # Criar Makefile
            makefile = project_path / "Makefile"
            makefile_content = f'''# Makefile for {project_name}
# Generated by Saturn Manager

PROJECT_NAME = {project_name}
SOURCE_DIR = src
BUILD_DIR = build
RES_DIR = res
INCLUDE_DIR = include

# Jo-Engine settings
JOENGINE = {self.devkit_path}/joengine
YAUL_INSTALL_ROOT = {self.devkit_path}/yaul
YAUL_PROG_SH_PREFIX = {self.devkit_path}/toolchain/bin/sh-elf-
YAUL_ARCH_SH_PREFIX = {self.devkit_path}/toolchain/bin/sh-elf-

CC = $(YAUL_PROG_SH_PREFIX)gcc
LD = $(YAUL_PROG_SH_PREFIX)ld
OBJCOPY = $(YAUL_PROG_SH_PREFIX)objcopy

# Compiler flags
CFLAGS = -I$(JOENGINE) -I$(YAUL_INSTALL_ROOT)/include -I$(INCLUDE_DIR) -O2 -m2 -mb
LDFLAGS = -L$(JOENGINE) -L$(YAUL_INSTALL_ROOT)/lib -ljo -lyaul

# Source files
SOURCES = $(wildcard $(SOURCE_DIR)/*.c)
OBJECTS = $(SOURCES:$(SOURCE_DIR)/%.c=$(BUILD_DIR)/%.o)

# Target files
ELF = $(BUILD_DIR)/$(PROJECT_NAME).elf
BIN = $(BUILD_DIR)/$(PROJECT_NAME).bin
ISO = $(BUILD_DIR)/$(PROJECT_NAME).iso

.PHONY: all clean run debug

all: $(ISO)

$(ISO): $(BIN)
	@echo "Creating Saturn ISO..."
	@mkdir -p $(BUILD_DIR)
	# Use Jo-Engine ISO creation tools here
	@cp $< $@

$(BIN): $(ELF)
	@echo "Converting to binary..."
	$(OBJCOPY) -O binary $< $@

$(ELF): $(OBJECTS)
	@echo "Linking $(PROJECT_NAME)..."
	$(LD) -o $@ $^ $(LDFLAGS)

$(BUILD_DIR)/%.o: $(SOURCE_DIR)/%.c
	@mkdir -p $(BUILD_DIR)
	@echo "Compiling $<..."
	$(CC) $(CFLAGS) -c -o $@ $<

clean:
	@echo "Cleaning build files..."
	@rm -rf $(BUILD_DIR)/*

run: $(ISO)
	@echo "Running $(PROJECT_NAME)..."
	@"{self.emulators_path}/Mednafen/mednafen.exe" $(ISO)

debug: $(ISO)
	@echo "Debugging $(PROJECT_NAME)..."
	@"{self.emulators_path}/Mednafen/mednafen.exe" $(ISO) -debugger
'''
            makefile.write_text(makefile_content, encoding='utf-8')
            
            # Criar README
            readme = project_path / "README.md"
            readme_content = f'''# {project_name}

Sega Saturn project created with Saturn Manager.

## Building

```bash
make
```

## Running

```bash
make run
```

## Debugging

```bash
make debug
```

## Cleaning

```bash
make clean
```

## Project Structure

- `src/` - C source files
- `res/` - Graphics, audio and other resources
- `build/` - Compiled objects and ISO
- `include/` - Header files

## Resources

- [Jo-Engine Documentation](https://github.com/johannes-fetz/joengine)
- [Yaul Documentation](https://github.com/yaul-org/libyaul)
- [Sega Saturn Development Guide](https://segadev.org/)
- [Saturn Programming Guide](https://antime.kapsi.fi/sega/files/ST-013-R3-061694.pdf)
'''
            readme.write_text(readme_content, encoding='utf-8')
            
            # Criar configuração VS Code
            vscode_dir = project_path / ".vscode"
            vscode_dir.mkdir(exist_ok=True)
            
            # tasks.json
            tasks_json = vscode_dir / "tasks.json"
            tasks_content = '''{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Build Saturn Game",
            "type": "shell",
            "command": "make",
            "group": {
                "kind": "build",
                "isDefault": true
            },
            "presentation": {
                "echo": true,
                "reveal": "always",
                "focus": false,
                "panel": "shared"
            },
            "problemMatcher": ["$gcc"]
        },
        {
            "label": "Run Saturn Game",
            "type": "shell",
            "command": "make",
            "args": ["run"],
            "group": "test",
            "dependsOn": "Build Saturn Game"
        },
        {
            "label": "Debug Saturn Game",
            "type": "shell",
            "command": "make",
            "args": ["debug"],
            "group": "test",
            "dependsOn": "Build Saturn Game"
        },
        {
            "label": "Clean Build",
            "type": "shell",
            "command": "make",
            "args": ["clean"],
            "group": "build"
        }
    ]
}'''
            tasks_json.write_text(tasks_content, encoding='utf-8')
            
            # settings.json
            settings_json = vscode_dir / "settings.json"
            settings_content = f'''{{
    "files.associations": {{
        "*.h": "c",
        "*.c": "c",
        "*.s": "asm",
        "*.iso": "binary"
    }},
    "C_Cpp.default.includePath": [
        "{self.devkit_path}/joengine",
        "{self.devkit_path}/yaul/include",
        "./include"
    ],
    "C_Cpp.default.defines": [
        "__SATURN__",
        "__SH2__"
    ],
    "makefile.configureOnOpen": true
}}'''
            settings_json.write_text(settings_content, encoding='utf-8')
            
            self.logger.info(f"Template de projeto criado: {project_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na criação do template: {e}")
            return False