"""Melhorias específicas para o Game Boy Advance Development Kit (devkitARM)
Implementação completa do manager para desenvolvimento GBA"""

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

class GBAManager(RetroDevkitManager):
    """Manager específico para Game Boy Advance Development Kit (devkitARM)"""
    
    def __init__(self, base_path: Path, logger: logging.Logger):
        super().__init__(base_path, logger)
        self.devkitarm_version = "latest"
        self.devkitpro_url = "https://github.com/devkitPro/installer/releases/latest/download/devkitProUpdater-3.0.4.exe"
        self.libgba_url = "https://github.com/devkitPro/libgba/archive/refs/heads/master.zip"
        
    def get_devkit_folder_name(self) -> str:
        """Retorna o nome da pasta do GBA devkit"""
        return "GBA"
        
    def get_devkit_info(self) -> DevkitInfo:
        """Retorna informações do GBA devkit"""
        return DevkitInfo(
            name="Game Boy Advance Development Kit",
            console="Nintendo Game Boy Advance",
            devkit_name="devkitARM",
            version=self.devkitarm_version,
            dependencies=[
                "make",
                "unzip",
                "wget",
                "cmake",
                "python3"
            ],
            environment_vars={
                "DEVKITPRO": str(self.devkit_path / "devkitPro"),
                "DEVKITARM": str(self.devkit_path / "devkitPro" / "devkitARM"),
                "LIBGBA": str(self.devkit_path / "devkitPro" / "libgba"),
                "PATH": str(self.devkit_path / "devkitPro" / "devkitARM" / "bin")
            },
            download_url=self.devkitpro_url,
            install_commands=[
                "Download and install devkitPro",
                "Install devkitARM toolchain",
                "Install libgba",
                "Setup environment variables",
                "Install emulators",
                "Setup VS Code extensions"
            ],
            verification_files=[
                "devkitPro/devkitARM/bin/arm-none-eabi-gcc.exe",
                "devkitPro/devkitARM/bin/arm-none-eabi-ld.exe",
                "devkitPro/libgba/include/gba.h",
                "devkitPro/libgba/lib/libgba.a",
                "devkitPro/tools/bin/gbafix.exe"
            ]
        )
        
    def install_dependencies(self) -> bool:
        """Instala dependências do GBA devkit"""
        try:
            self.logger.info("Instalando dependências do GBA devkit...")
            
            # Download e instalação do devkitPro
            if not self._install_devkitpro():
                return False
                
            # Instalar libgba
            if not self._install_libgba():
                return False
                
            # Instalar ferramentas adicionais
            if not self._install_additional_tools():
                self.logger.warning("Falha na instalação de ferramentas adicionais")
                
            self.logger.info("GBA devkit instalado com sucesso")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na instalação do GBA devkit: {e}")
            return False
            
    def _install_devkitpro(self) -> bool:
        """Instala o devkitPro"""
        try:
            self.logger.info("Instalando devkitPro...")
            
            # Para Windows, usar o instalador oficial
            installer_path = self.devkit_path / "devkitProUpdater.exe"
            if not self.download_file(self.devkitpro_url, installer_path, "devkitPro Installer"):
                return False
                
            # Executar instalador silenciosamente
            devkitpro_path = self.devkit_path / "devkitPro"
            devkitpro_path.mkdir(parents=True, exist_ok=True)
            
            # Nota: O instalador oficial requer interação do usuário
            # Para automação completa, seria necessário usar uma versão portável
            self.logger.info("Execute o instalador manualmente e instale devkitARM")
            self.logger.info(f"Instalador baixado em: {installer_path}")
            self.logger.info(f"Instale em: {devkitpro_path}")
            
            # Criar estrutura básica se não existir
            (devkitpro_path / "devkitARM").mkdir(parents=True, exist_ok=True)
            (devkitpro_path / "libgba").mkdir(parents=True, exist_ok=True)
            (devkitpro_path / "tools").mkdir(parents=True, exist_ok=True)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na instalação do devkitPro: {e}")
            return False
            
    def _install_libgba(self) -> bool:
        """Instala a libgba"""
        try:
            self.logger.info("Instalando libgba...")
            
            libgba_zip = self.devkit_path / "libgba.zip"
            if not self.download_file(self.libgba_url, libgba_zip, "libgba"):
                return False
                
            # Extrair libgba
            libgba_path = self.devkit_path / "devkitPro" / "libgba"
            if not self.extract_archive(libgba_zip, libgba_path):
                return False
                
            # Remover arquivo zip
            libgba_zip.unlink()
            
            self.logger.info("libgba instalada com sucesso")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na instalação da libgba: {e}")
            return False
            
    def _install_additional_tools(self) -> bool:
        """Instala ferramentas adicionais para GBA"""
        try:
            self.logger.info("Instalando ferramentas adicionais...")
            
            tools_path = self.tools_path
            tools_path.mkdir(parents=True, exist_ok=True)
            
            # Instalar GRIT (Graphics Raster Image Transcoder)
            self._install_grit()
            
            # Instalar Usenti (Sprite/Tile editor)
            self._install_usenti()
            
            # Criar scripts de conversão básicos
            self._create_conversion_scripts()
            
            self.logger.info("Ferramentas adicionais instaladas")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na instalação de ferramentas adicionais: {e}")
            return False
            
    def _install_grit(self) -> bool:
        """Instala GRIT para conversão de gráficos"""
        try:
            self.logger.info("Instalando GRIT...")
            
            grit_url = "https://www.coranac.com/files/grit-win.zip"
            grit_zip = self.tools_path / "grit.zip"
            
            if self.download_file(grit_url, grit_zip, "GRIT"):
                grit_path = self.tools_path / "GRIT"
                if self.extract_archive(grit_zip, grit_path):
                    grit_zip.unlink()
                    self.logger.info("GRIT instalado com sucesso")
                    return True
                    
            self.logger.warning("Falha na instalação do GRIT")
            return False
            
        except Exception as e:
            self.logger.error(f"Erro na instalação do GRIT: {e}")
            return False
            
    def _install_usenti(self) -> bool:
        """Instala Usenti para edição de sprites"""
        try:
            self.logger.info("Instalando Usenti...")
            
            usenti_url = "https://www.coranac.com/files/usenti-win.zip"
            usenti_zip = self.tools_path / "usenti.zip"
            
            if self.download_file(usenti_url, usenti_zip, "Usenti"):
                usenti_path = self.tools_path / "Usenti"
                if self.extract_archive(usenti_zip, usenti_path):
                    usenti_zip.unlink()
                    self.logger.info("Usenti instalado com sucesso")
                    return True
                    
            self.logger.warning("Falha na instalação do Usenti")
            return False
            
        except Exception as e:
            self.logger.error(f"Erro na instalação do Usenti: {e}")
            return False
            
    def _create_conversion_scripts(self) -> bool:
        """Cria scripts de conversão de assets"""
        try:
            scripts_path = self.devkit_path / "scripts"
            scripts_path.mkdir(exist_ok=True)
            
            # Script para conversão de imagens com GRIT
            grit_script = scripts_path / "convert_image_grit.bat"
            grit_content = f'''@echo off
REM Script para conversao de imagens com GRIT
setlocal

if "%1"=="" (
    echo Uso: convert_image_grit.bat imagem.bmp
    pause
    exit /b 1
)

set IMAGE_FILE=%1
set GRIT_PATH="{self.tools_path}\\GRIT\\grit.exe"

if exist %GRIT_PATH% (
    echo Convertendo %IMAGE_FILE% com GRIT...
    %GRIT_PATH% %IMAGE_FILE% -gb -gB8
) else (
    echo GRIT nao encontrado!
    pause
)
'''
            grit_script.write_text(grit_content, encoding='utf-8')
            
            # Script para abrir Usenti
            usenti_script = scripts_path / "open_usenti.bat"
            usenti_content = f'''@echo off
REM Script para abrir Usenti
set USENTI_PATH="{self.tools_path}\\Usenti\\usenti.exe"

if exist %USENTI_PATH% (
    start "" %USENTI_PATH% %1
) else (
    echo Usenti nao encontrado!
    pause
)
'''
            usenti_script.write_text(usenti_content, encoding='utf-8')
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na criação de scripts de conversão: {e}")
            return False
            
    def verify_installation(self) -> bool:
        """Verifica se o GBA devkit está instalado corretamente"""
        try:
            devkit_info = self.get_devkit_info()
            
            # Verificar arquivos essenciais
            for file_path in devkit_info.verification_files:
                full_path = self.devkit_path / file_path
                if not full_path.exists():
                    self.logger.error(f"Arquivo não encontrado: {full_path}")
                    return False
                    
            # Testar compilador ARM
            gcc_path = self.devkit_path / "devkitPro" / "devkitARM" / "bin" / "arm-none-eabi-gcc.exe"
            if gcc_path.exists():
                success, output = self.run_command([str(gcc_path), "--version"])
                if not success:
                    self.logger.error("Falha ao executar arm-none-eabi-gcc")
                    return False
            else:
                self.logger.warning("Compilador ARM não encontrado - execute o instalador devkitPro")
                
            # Testar gbafix
            gbafix_path = self.devkit_path / "devkitPro" / "tools" / "bin" / "gbafix.exe"
            if gbafix_path.exists():
                success, output = self.run_command([str(gbafix_path), "-h"])
                if not success:
                    self.logger.warning("gbafix pode não estar funcionando corretamente")
                    
            self.logger.info("Verificação do GBA devkit concluída")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na verificação do GBA devkit: {e}")
            return False
            
    def install_emulators(self) -> bool:
        """Instala emuladores GBA"""
        try:
            self.logger.info("Instalando emuladores GBA...")
            
            emulators = {
                "mGBA": {
                    "url": "https://github.com/mgba-emu/mgba/releases/latest/download/mGBA-0.10.3-win64.zip",
                    "folder": "mGBA"
                },
                "VBA-M": {
                    "url": "https://github.com/visualboyadvance-m/visualboyadvance-m/releases/latest/download/visualboyadvance-m-Win-x64.zip",
                    "folder": "VBA-M"
                },
                "No$GBA": {
                    "url": "https://www.nogba.com/no$gba.zip",
                    "folder": "NoGBA"
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
            
            # Script para mGBA
            mgba_script = scripts_path / "run_mgba.bat"
            mgba_content = f'''@echo off
REM Script para executar mGBA
set EMULATOR_PATH="{self.emulators_path}\\mGBA\\mGBA.exe"
if exist %EMULATOR_PATH% (
    start "" %EMULATOR_PATH% %1
) else (
    echo mGBA nao encontrado em %EMULATOR_PATH%
    pause
)
'''
            mgba_script.write_text(mgba_content, encoding='utf-8')
            
            # Script para VBA-M
            vbam_script = scripts_path / "run_vbam.bat"
            vbam_content = f'''@echo off
REM Script para executar VBA-M
set EMULATOR_PATH="{self.emulators_path}\\VBA-M\\visualboyadvance-m.exe"
if exist %EMULATOR_PATH% (
    start "" %EMULATOR_PATH% %1
) else (
    echo VBA-M nao encontrado em %EMULATOR_PATH%
    pause
)
'''
            vbam_script.write_text(vbam_content, encoding='utf-8')
            
            # Script para No$GBA
            nogba_script = scripts_path / "run_nogba.bat"
            nogba_content = f'''@echo off
REM Script para executar No$GBA
set EMULATOR_PATH="{self.emulators_path}\\NoGBA\\NO$GBA.EXE"
if exist %EMULATOR_PATH% (
    start "" %EMULATOR_PATH% %1
) else (
    echo No$GBA nao encontrado em %EMULATOR_PATH%
    pause
)
'''
            nogba_script.write_text(nogba_content, encoding='utf-8')
            
            # Script genérico
            run_script = scripts_path / "run_gba_rom.bat"
            run_content = f'''@echo off
REM Script generico para executar ROM GBA
setlocal

if "%1"=="" (
    echo Uso: run_gba_rom.bat arquivo.gba
    pause
    exit /b 1
)

set ROM_FILE=%1
set MGBA_PATH="{self.emulators_path}\\mGBA\\mGBA.exe"
set VBAM_PATH="{self.emulators_path}\\VBA-M\\visualboyadvance-m.exe"
set NOGBA_PATH="{self.emulators_path}\\NoGBA\\NO$GBA.EXE"

if exist %MGBA_PATH% (
    echo Executando com mGBA...
    start "" %MGBA_PATH% %ROM_FILE%
) else if exist %VBAM_PATH% (
    echo Executando com VBA-M...
    start "" %VBAM_PATH% %ROM_FILE%
) else if exist %NOGBA_PATH% (
    echo Executando com No$GBA...
    start "" %NOGBA_PATH% %ROM_FILE%
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
        """Instala extensões VS Code para GBA"""
        try:
            self.logger.info("Instalando extensões VS Code para GBA...")
            
            extensions = [
                "ms-vscode.cpptools",  # C/C++ support
                "ms-vscode.makefile-tools",  # Makefile support
                "13xforever.language-x86-64-assembly",  # ARM assembly support
                "bierner.markdown-preview-enhanced"  # Documentation
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
        """Cria scripts de conveniência para desenvolvimento GBA"""
        try:
            self.logger.info("Criando scripts de conveniência...")
            
            scripts_path = self.devkit_path / "scripts"
            scripts_path.mkdir(exist_ok=True)
            
            # Script de compilação
            compile_script = scripts_path / "compile_gba_rom.bat"
            compile_content = f'''@echo off
REM Script de compilacao GBA
setlocal

set DEVKITPRO={self.devkit_path}\\devkitPro
set DEVKITARM=%DEVKITPRO%\\devkitARM
set LIBGBA=%DEVKITPRO%\\libgba
set PATH=%DEVKITARM%\\bin;%PATH%

if "%1"=="" (
    echo Uso: compile_gba_rom.bat projeto_folder
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

echo Compilando projeto GBA...
make

if exist "*.gba" (
    echo ROM criada com sucesso!
) else (
    echo Erro na compilacao!
)

pause
'''
            compile_script.write_text(compile_content, encoding='utf-8')
            
            # Script de execução
            run_script = scripts_path / "run_gba_game.bat"
            run_content = f'''@echo off
REM Script para executar jogo GBA
setlocal

if "%1"=="" (
    echo Uso: run_gba_game.bat arquivo.gba
    pause
    exit /b 1
)

set ROM_FILE=%1
set MGBA_PATH="{self.emulators_path}\\mGBA\\mGBA.exe"
set VBAM_PATH="{self.emulators_path}\\VBA-M\\visualboyadvance-m.exe"

if exist %MGBA_PATH% (
    echo Executando com mGBA...
    start "" %MGBA_PATH% %ROM_FILE%
) else if exist %VBAM_PATH% (
    echo Executando com VBA-M...
    start "" %VBAM_PATH% %ROM_FILE%
) else (
    echo Nenhum emulador encontrado!
    pause
)
'''
            run_script.write_text(run_content, encoding='utf-8')
            
            # Script de deploy para flashcart
            flashcart_script = scripts_path / "flashcart_deploy.bat"
            flashcart_content = r'''@echo off
REM Script de deploy para flashcart GBA
setlocal

if "%1"=="" (
    echo Uso: flashcart_deploy.bat arquivo.gba
    pause
    exit /b 1
)

set ROM_FILE=%1

echo Copiando ROM para flashcart...
echo Insira o flashcart e pressione qualquer tecla
pause

REM Detectar drive do flashcart (assumindo que seja removivel)
for %%d in (D E F G H I J K L M N O P Q R S T U V W X Y Z) do (
    if exist %%d:\ (
        echo Tentando copiar para %%d:\
        copy "%ROM_FILE%" "%%d:\"
        if not errorlevel 1 (
            echo ROM copiada com sucesso para %%d:\
            goto :done
        )
    )
)

echo Falha ao copiar ROM - verifique se o flashcart esta conectado
:done
pause
'''
            flashcart_script.write_text(flashcart_content, encoding='utf-8')
            
            # Script de criação de projeto
            create_project_script = scripts_path / "create_gba_project.bat"
            create_project_content = f'''@echo off
REM Script para criar novo projeto GBA
setlocal

if "%1"=="" (
    echo Uso: create_gba_project.bat nome_do_projeto
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

echo Criando projeto GBA: %PROJECT_NAME%
mkdir "%PROJECT_DIR%"

echo Copiando template...
xcopy "{self.devkit_path}\\templates\\gba_template\\*" "%PROJECT_DIR%\\" /E /I /Q

echo Projeto criado: %PROJECT_DIR%
echo.
echo Para compilar: cd "%PROJECT_DIR%" && make
echo Para executar: run_gba_game.bat "%PROJECT_DIR%\\game.gba"
pause
'''
            create_project_script.write_text(create_project_content, encoding='utf-8')
            
            self.logger.info("Scripts de conveniência criados")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na criação de scripts: {e}")
            return False
            
    def create_project_template(self, project_name: str, project_path: Path) -> bool:
        """Cria template de projeto GBA"""
        try:
            self.logger.info(f"Criando template de projeto GBA: {project_name}")
            
            # Criar estrutura de diretórios
            project_path.mkdir(parents=True, exist_ok=True)
            (project_path / "source").mkdir(exist_ok=True)
            (project_path / "data").mkdir(exist_ok=True)
            (project_path / "build").mkdir(exist_ok=True)
            (project_path / "include").mkdir(exist_ok=True)
            
            # Criar main.c
            main_c = project_path / "source" / "main.c"
            main_content = f'''// {project_name} - Game Boy Advance Project
// Generated by GBA Manager

#include <gba.h>
#include <stdio.h>

// Screen dimensions
#define SCREEN_WIDTH  240
#define SCREEN_HEIGHT 160

// Colors (15-bit RGB)
#define COLOR_BLACK   0x0000
#define COLOR_WHITE   0x7FFF
#define COLOR_RED     0x001F
#define COLOR_GREEN   0x03E0
#define COLOR_BLUE    0x7C00

void init_gba() {{
    // Set video mode 3 (240x160, 16-bit color, bitmap)
    SetMode(MODE_3 | BG2_ENABLE);
}}

void draw_pixel(int x, int y, u16 color) {{
    if (x >= 0 && x < SCREEN_WIDTH && y >= 0 && y < SCREEN_HEIGHT) {{
        ((u16*)VRAM)[y * SCREEN_WIDTH + x] = color;
    }}
}}

void draw_rect(int x, int y, int width, int height, u16 color) {{
    for (int i = 0; i < height; i++) {{
        for (int j = 0; j < width; j++) {{
            draw_pixel(x + j, y + i, color);
        }}
    }}
}}

void clear_screen(u16 color) {{
    draw_rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT, color);
}}

int main() {{
    // Initialize GBA
    init_gba();
    
    // Clear screen to blue
    clear_screen(COLOR_BLUE);
    
    // Draw some rectangles
    draw_rect(50, 50, 100, 60, COLOR_WHITE);
    draw_rect(60, 60, 80, 40, COLOR_RED);
    
    // Main game loop
    while(1) {{
        // Scan for key input
        scanKeys();
        
        // Get current key state
        u16 keys = keysDown();
        
        // Exit on START + SELECT
        if ((keys & KEY_START) && (keys & KEY_SELECT)) {{
            break;
        }}
        
        // Simple input handling
        if (keys & KEY_A) {{
            draw_rect(10, 10, 20, 20, COLOR_GREEN);
        }}
        
        if (keys & KEY_B) {{
            draw_rect(10, 10, 20, 20, COLOR_BLUE);
        }}
        
        // Wait for VBlank
        VBlankIntrWait();
    }}
    
    return 0;
}}
'''
            main_c.write_text(main_content, encoding='utf-8')
            
            # Criar Makefile
            makefile = project_path / "Makefile"
            makefile_content = f'''#---------------------------------------------------------------------------------
# Makefile for {project_name}
# Generated by GBA Manager
#---------------------------------------------------------------------------------

PROJECT_NAME := {project_name}

#---------------------------------------------------------------------------------
# devkitARM settings
#---------------------------------------------------------------------------------
ifeq ($(strip $(DEVKITARM)),)
$(error "Please set DEVKITARM in your environment. export DEVKITARM=<path to>devkitARM")
endif

include $(DEVKITARM)/gba_rules

#---------------------------------------------------------------------------------
# TARGET is the name of the output
# BUILD is the directory where object files & intermediate files will be placed
# SOURCES is a list of directories containing source code
# INCLUDES is a list of directories containing extra header files
# DATA is a list of directories containing binary data
# GRAPHICS is a list of directories containing files to be processed by grit
#---------------------------------------------------------------------------------
TARGET      := $(PROJECT_NAME)
BUILD       := build
SOURCES     := source
INCLUDES    := include
DATA        := data
GRAPHICS    := gfx

#---------------------------------------------------------------------------------
# options for code generation
#---------------------------------------------------------------------------------
ARCH    := -mthumb -mthumb-interwork

CFLAGS  := -g -Wall -O2\
           -mcpu=arm7tdmi -mtune=arm7tdmi\
           $(ARCH)

CFLAGS  += $(INCLUDE)

CXXFLAGS    := $(CFLAGS) -fno-rtti -fno-exceptions

ASFLAGS := -g $(ARCH)
LDFLAGS = -g $(ARCH) -Wl,-Map,$(notdir $*.map)

#---------------------------------------------------------------------------------
# any extra libraries we wish to link with the project
#---------------------------------------------------------------------------------
LIBS    := -lgba

#---------------------------------------------------------------------------------
# list of directories containing libraries, this must be the top level containing
# include and lib
#---------------------------------------------------------------------------------
LIBDIRS := $(LIBGBA)

#---------------------------------------------------------------------------------
# no real need to edit anything past this point unless you need to add additional
# rules for different file extensions
#---------------------------------------------------------------------------------

ifneq ($(BUILD),$(notdir $(CURDIR)))

export OUTPUT   := $(CURDIR)/$(TARGET)
export TOPDIR   := $(CURDIR)

export VPATH    := $(foreach dir,$(SOURCES),$(CURDIR)/$(dir)) \
                   $(foreach dir,$(DATA),$(CURDIR)/$(dir)) \
                   $(foreach dir,$(GRAPHICS),$(CURDIR)/$(dir))

export DEPSDIR  := $(CURDIR)/$(BUILD)

CFILES      := $(foreach dir,$(SOURCES),$(notdir $(wildcard $(dir)/*.c)))
CPPFILES    := $(foreach dir,$(SOURCES),$(notdir $(wildcard $(dir)/*.cpp)))
SFILES      := $(foreach dir,$(SOURCES),$(notdir $(wildcard $(dir)/*.s)))
PCXFILES    := $(foreach dir,$(GRAPHICS),$(notdir $(wildcard $(dir)/*.pcx)))
BMPFILES    := $(foreach dir,$(GRAPHICS),$(notdir $(wildcard $(dir)/*.bmp)))
BINFILES    := $(foreach dir,$(DATA),$(notdir $(wildcard $(dir)/*.*)))

#---------------------------------------------------------------------------------
# use CXX for linking C++ projects, CC for standard C
#---------------------------------------------------------------------------------
ifeq ($(strip $(CPPFILES)),)
    export LD   := $(CC)
else
    export LD   := $(CXX)
endif

export OFILES_BIN   := $(addsuffix .o,$(BINFILES))
export OFILES_SOURCES := $(CPPFILES:.cpp=.o) $(CFILES:.c=.o) $(SFILES:.s=.o)
export OFILES := $(OFILES_BIN) $(OFILES_SOURCES)

export HFILES_BIN   := $(addsuffix .h,$(subst .,_,$(BINFILES)))

export INCLUDE  := $(foreach dir,$(INCLUDES),-iquote $(CURDIR)/$(dir)) \
                   $(foreach dir,$(LIBDIRS),-I$(dir)/include) \
                   -I$(CURDIR)/$(BUILD)

export LIBPATHS := $(foreach dir,$(LIBDIRS),-L$(dir)/lib)

.PHONY: $(BUILD) clean

#---------------------------------------------------------------------------------
$(BUILD):
	@[ -d $@ ] || mkdir -p $@
	@$(MAKE) --no-print-directory -C $(BUILD) -f $(CURDIR)/Makefile

#---------------------------------------------------------------------------------
clean:
	@echo clean ...
	@rm -fr $(BUILD) $(TARGET).elf $(TARGET).gba

#---------------------------------------------------------------------------------
run: $(BUILD)
	@echo "Running $(TARGET).gba..."
	@"{self.emulators_path}/mGBA/mGBA.exe" $(TARGET).gba

#---------------------------------------------------------------------------------
else

#---------------------------------------------------------------------------------
# main targets
#---------------------------------------------------------------------------------

$(OUTPUT).gba   :   $(OUTPUT).elf

$(OUTPUT).elf   :   $(OFILES)

$(OFILES_SOURCES) : $(HFILES_BIN)

#---------------------------------------------------------------------------------
# The bin2o rule should be copied and modified
# for each extension used in the data directories
#---------------------------------------------------------------------------------

#---------------------------------------------------------------------------------
# rule to build soundbank from music files
#---------------------------------------------------------------------------------
soundbank.bin soundbank.h : $(AUDIOFILES)
#---------------------------------------------------------------------------------
	@mmutil $^ -osoundbank.bin -hsoundbank.h

#---------------------------------------------------------------------------------
# This rule links in binary data with the .bin extension
#---------------------------------------------------------------------------------
%.bin.o %_bin.h :   %.bin
#---------------------------------------------------------------------------------
	@echo $(notdir $<)
	@$(bin2o)

#---------------------------------------------------------------------------------
# This rule creates assembly source files using grit
# grit takes an image file and a .grit describing how the file is to be processed
# add additional rules like this for each image extension
# you use in the graphics folders
#---------------------------------------------------------------------------------
%.s %.h: %.bmp %.grit
#---------------------------------------------------------------------------------
	grit $< -fts -o$*

%.s %.h: %.pcx %.grit
#---------------------------------------------------------------------------------
	grit $< -fts -o$*

-include $(DEPSDIR)/*.d

#---------------------------------------------------------------------------------------
endif
#---------------------------------------------------------------------------------------
'''
            makefile.write_text(makefile_content, encoding='utf-8')
            
            # Criar README
            readme = project_path / "README.md"
            readme_content = f'''# {project_name}

Game Boy Advance project created with GBA Manager.

## Building

```bash
make
```

## Running

```bash
make run
```

## Cleaning

```bash
make clean
```

## Project Structure

- `source/` - C/C++ source files
- `data/` - Binary data files
- `gfx/` - Graphics files (processed by GRIT)
- `build/` - Compiled objects and binaries
- `include/` - Header files

## Controls

- A Button: Draw green rectangle
- B Button: Draw blue rectangle
- START + SELECT: Exit

## Resources

- [TONC GBA Programming Tutorial](https://www.coranac.com/tonc/text/)
- [devkitPro Documentation](https://devkitpro.org/wiki/Getting_Started)
- [GBA Development Community](https://gbadev.org/)
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
            "label": "Build GBA ROM",
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
            "label": "Run GBA Game",
            "type": "shell",
            "command": "make",
            "args": ["run"],
            "group": "test",
            "dependsOn": "Build GBA ROM"
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
        "*.s": "arm"
    }},
    "C_Cpp.default.includePath": [
        "{self.devkit_path}/devkitPro/libgba/include",
        "{self.devkit_path}/devkitPro/devkitARM/arm-none-eabi/include",
        "./include"
    ],
    "C_Cpp.default.defines": [
        "__GBA__",
        "ARM7"
    ],
    "makefile.configureOnOpen": true
}}'''
            settings_json.write_text(settings_content, encoding='utf-8')
            
            self.logger.info(f"Template de projeto criado: {project_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na criação do template: {e}")
            return False