"""Melhorias específicas para o Nintendo 64 Development Kit (libdragon)
Implementação completa do manager para desenvolvimento N64"""

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

class N64Manager(RetroDevkitManager):
    """Manager específico para Nintendo 64 Development Kit (libdragon)"""
    
    def __init__(self, base_path: Path, logger: logging.Logger):
        super().__init__(base_path, logger)
        self.libdragon_version = "latest"
        self.libdragon_url = "https://github.com/DragonMinded/libdragon/releases/latest/download/libdragon-windows-x64.zip"
        self.mips_toolchain_url = "https://github.com/DragonMinded/libdragon/releases/latest/download/mips64-elf-toolchain-windows.zip"
        
    def get_devkit_folder_name(self) -> str:
        """Retorna o nome da pasta do N64 devkit"""
        return "N64"
        
    def get_devkit_info(self) -> DevkitInfo:
        """Retorna informações do N64 devkit"""
        return DevkitInfo(
            name="Nintendo 64 Development Kit",
            console="Nintendo 64",
            devkit_name="libdragon",
            version=self.libdragon_version,
            dependencies=[
                "make",
                "unzip",
                "wget",
                "cmake",
                "python3"
            ],
            environment_vars={
                "N64_INST": str(self.devkit_path / "libdragon"),
                "LIBDRAGON_HOME": str(self.devkit_path / "libdragon"),
                "PATH": str(self.devkit_path / "mips64-elf" / "bin")
            },
            download_url=self.libdragon_url,
            install_commands=[
                "Download and extract libdragon",
                "Download and extract MIPS toolchain",
                "Setup environment variables",
                "Install emulators",
                "Setup VS Code extensions"
            ],
            verification_files=[
                "mips64-elf/bin/mips64-elf-gcc.exe",
                "mips64-elf/bin/mips64-elf-ld.exe",
                "libdragon/include/libdragon.h",
                "libdragon/lib/libdragon.a",
                "libdragon/tools/n64tool.exe"
            ]
        )
        
    def install_dependencies(self) -> bool:
        """Instala dependências do N64 devkit"""
        try:
            self.logger.info("Instalando dependências do N64 devkit...")
            
            # Download e instalação do MIPS toolchain
            if not self._install_mips_toolchain():
                return False
                
            # Download e instalação do libdragon
            if not self._install_libdragon():
                return False
                
            # Instalar ferramentas adicionais
            if not self._install_additional_tools():
                self.logger.warning("Falha na instalação de ferramentas adicionais")
                
            self.logger.info("N64 devkit instalado com sucesso")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na instalação do N64 devkit: {e}")
            return False
            
    def _install_mips_toolchain(self) -> bool:
        """Instala o MIPS toolchain"""
        try:
            self.logger.info("Instalando MIPS toolchain...")
            
            toolchain_zip = self.devkit_path / "mips-toolchain.zip"
            if not self.download_file(self.mips_toolchain_url, toolchain_zip, "MIPS Toolchain"):
                return False
                
            # Extrair toolchain
            toolchain_path = self.devkit_path / "mips64-elf"
            if not self.extract_archive(toolchain_zip, toolchain_path):
                return False
                
            # Remover arquivo zip
            toolchain_zip.unlink()
            
            self.logger.info("MIPS toolchain instalado com sucesso")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na instalação do MIPS toolchain: {e}")
            return False
            
    def _install_libdragon(self) -> bool:
        """Instala o libdragon"""
        try:
            self.logger.info("Instalando libdragon...")
            
            libdragon_zip = self.devkit_path / "libdragon.zip"
            if not self.download_file(self.libdragon_url, libdragon_zip, "libdragon"):
                return False
                
            # Extrair libdragon
            libdragon_path = self.devkit_path / "libdragon"
            if not self.extract_archive(libdragon_zip, libdragon_path):
                return False
                
            # Remover arquivo zip
            libdragon_zip.unlink()
            
            self.logger.info("libdragon instalado com sucesso")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na instalação do libdragon: {e}")
            return False
            
    def _install_additional_tools(self) -> bool:
        """Instala ferramentas adicionais para N64"""
        try:
            self.logger.info("Instalando ferramentas adicionais...")
            
            tools_path = self.tools_path
            tools_path.mkdir(parents=True, exist_ok=True)
            
            # Criar scripts de conversão básicos
            self._create_conversion_scripts()
            
            # Instalar UNFLoader se disponível
            self._install_unfloader()
            
            self.logger.info("Ferramentas adicionais instaladas")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na instalação de ferramentas adicionais: {e}")
            return False
            
    def _install_unfloader(self) -> bool:
        """Instala UNFLoader para flashcart deployment"""
        try:
            self.logger.info("Instalando UNFLoader...")
            
            unfloader_url = "https://github.com/buu342/N64-UNFLoader/releases/latest/download/UNFLoader-Windows.zip"
            unfloader_zip = self.tools_path / "unfloader.zip"
            
            if self.download_file(unfloader_url, unfloader_zip, "UNFLoader"):
                unfloader_path = self.tools_path / "UNFLoader"
                if self.extract_archive(unfloader_zip, unfloader_path):
                    unfloader_zip.unlink()
                    self.logger.info("UNFLoader instalado com sucesso")
                    return True
                    
            self.logger.warning("Falha na instalação do UNFLoader")
            return False
            
        except Exception as e:
            self.logger.error(f"Erro na instalação do UNFLoader: {e}")
            return False
            
    def _create_conversion_scripts(self) -> bool:
        """Cria scripts de conversão de assets"""
        try:
            scripts_path = self.devkit_path / "scripts"
            scripts_path.mkdir(exist_ok=True)
            
            # Script para conversão de imagens
            img_script = scripts_path / "convert_image.bat"
            img_content = '''@echo off
REM Script para conversao de imagens para N64
echo Conversao de imagens ainda nao implementada
echo Use libdragon tools manualmente por enquanto
pause
'''
            img_script.write_text(img_content, encoding='utf-8')
            
            # Script para conversão de áudio
            audio_script = scripts_path / "convert_audio.bat"
            audio_content = '''@echo off
REM Script para conversao de audio para N64
echo Conversao de audio ainda nao implementada
echo Use libdragon tools manualmente por enquanto
pause
'''
            audio_script.write_text(audio_content, encoding='utf-8')
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na criação de scripts de conversão: {e}")
            return False
            
    def verify_installation(self) -> bool:
        """Verifica se o N64 devkit está instalado corretamente"""
        try:
            devkit_info = self.get_devkit_info()
            
            # Verificar arquivos essenciais
            for file_path in devkit_info.verification_files:
                full_path = self.devkit_path / file_path
                if not full_path.exists():
                    self.logger.error(f"Arquivo não encontrado: {full_path}")
                    return False
                    
            # Testar compilador MIPS
            gcc_path = self.devkit_path / "mips64-elf" / "bin" / "mips64-elf-gcc.exe"
            success, output = self.run_command([str(gcc_path), "--version"])
            if not success:
                self.logger.error("Falha ao executar mips64-elf-gcc")
                return False
                
            # Testar n64tool
            n64tool_path = self.devkit_path / "libdragon" / "tools" / "n64tool.exe"
            if n64tool_path.exists():
                success, output = self.run_command([str(n64tool_path), "-h"])
                if not success:
                    self.logger.warning("n64tool pode não estar funcionando corretamente")
                    
            self.logger.info("Verificação do N64 devkit concluída com sucesso")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na verificação do N64 devkit: {e}")
            return False
            
    def install_emulators(self) -> bool:
        """Instala emuladores N64"""
        try:
            self.logger.info("Instalando emuladores N64...")
            
            emulators = {
                "Ares": {
                    "url": "https://github.com/ares-emulator/ares/releases/latest/download/ares-windows.zip",
                    "folder": "Ares"
                },
                "Mupen64Plus": {
                    "url": "https://github.com/mupen64plus/mupen64plus-core/releases/latest/download/mupen64plus-bundle-win32.zip",
                    "folder": "Mupen64Plus"
                },
                "Project64": {
                    "url": "https://www.pj64-emu.com/file/project64-latest/",
                    "folder": "Project64"
                }
            }
            
            for emu_name, emu_info in emulators.items():
                if emu_name == "Project64":
                    # Project64 requer download manual
                    self.logger.info(f"Para {emu_name}, faça download manual de {emu_info['url']}")
                    continue
                    
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
            
            # Script para Ares
            ares_script = scripts_path / "run_ares.bat"
            ares_content = f'''@echo off
REM Script para executar Ares
set EMULATOR_PATH="{self.emulators_path}\\Ares\\ares.exe"
if exist %EMULATOR_PATH% (
    start "" %EMULATOR_PATH% %1
) else (
    echo Ares nao encontrado em %EMULATOR_PATH%
    pause
)
'''
            ares_script.write_text(ares_content, encoding='utf-8')
            
            # Script para Mupen64Plus
            mupen_script = scripts_path / "run_mupen64plus.bat"
            mupen_content = f'''@echo off
REM Script para executar Mupen64Plus
set EMULATOR_PATH="{self.emulators_path}\\Mupen64Plus\\mupen64plus.exe"
if exist %EMULATOR_PATH% (
    start "" %EMULATOR_PATH% %1
) else (
    echo Mupen64Plus nao encontrado em %EMULATOR_PATH%
    pause
)
'''
            mupen_script.write_text(mupen_content, encoding='utf-8')
            
            # Script genérico
            run_script = scripts_path / "run_n64_rom.bat"
            run_content = f'''@echo off
REM Script generico para executar ROM N64
setlocal

if "%1"=="" (
    echo Uso: run_n64_rom.bat arquivo.n64
    pause
    exit /b 1
)

set ROM_FILE=%1
set ARES_PATH="{self.emulators_path}\\Ares\\ares.exe"
set MUPEN_PATH="{self.emulators_path}\\Mupen64Plus\\mupen64plus.exe"

if exist %ARES_PATH% (
    echo Executando com Ares...
    start "" %ARES_PATH% %ROM_FILE%
) else if exist %MUPEN_PATH% (
    echo Executando com Mupen64Plus...
    start "" %MUPEN_PATH% %ROM_FILE%
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
        """Instala extensões VS Code para N64"""
        try:
            self.logger.info("Instalando extensões VS Code para N64...")
            
            extensions = [
                "ms-vscode.cpptools",  # C/C++ support
                "ms-vscode.makefile-tools",  # Makefile support
                "13xforever.language-x86-64-assembly",  # MIPS assembly support
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
        """Cria scripts de conveniência para desenvolvimento N64"""
        try:
            self.logger.info("Criando scripts de conveniência...")
            
            scripts_path = self.devkit_path / "scripts"
            scripts_path.mkdir(exist_ok=True)
            
            # Script de compilação
            compile_script = scripts_path / "compile_n64_rom.bat"
            compile_content = f'''@echo off
REM Script de compilacao N64
setlocal

set N64_INST={self.devkit_path}\\libdragon
set LIBDRAGON_HOME={self.devkit_path}\\libdragon
set PATH={self.devkit_path}\\mips64-elf\\bin;%PATH%

if "%1"=="" (
    echo Uso: compile_n64_rom.bat projeto_folder
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

echo Compilando projeto N64...
make

if exist "*.n64" (
    echo ROM criada com sucesso!
) else (
    echo Erro na compilacao!
)

pause
'''
            compile_script.write_text(compile_content, encoding='utf-8')
            
            # Script de execução
            run_script = scripts_path / "run_n64_game.bat"
            run_content = f'''@echo off
REM Script para executar jogo N64
setlocal

if "%1"=="" (
    echo Uso: run_n64_game.bat arquivo.n64
    pause
    exit /b 1
)

set ROM_FILE=%1
set ARES_PATH="{self.emulators_path}\\Ares\\ares.exe"
set MUPEN_PATH="{self.emulators_path}\\Mupen64Plus\\mupen64plus.exe"

if exist %ARES_PATH% (
    echo Executando com Ares...
    start "" %ARES_PATH% %ROM_FILE%
) else if exist %MUPEN_PATH% (
    echo Executando com Mupen64Plus...
    start "" %MUPEN_PATH% %ROM_FILE%
) else (
    echo Nenhum emulador encontrado!
    pause
)
'''
            run_script.write_text(run_content, encoding='utf-8')
            
            # Script de deploy para flashcart
            flashcart_script = scripts_path / "flashcart_deploy.bat"
            flashcart_content = f'''@echo off
REM Script de deploy para flashcart N64
setlocal

if "%1"=="" (
    echo Uso: flashcart_deploy.bat arquivo.n64
    pause
    exit /b 1
)

set ROM_FILE=%1
set UNFLOADER_PATH="{self.tools_path}\\UNFLoader\\UNFLoader.exe"

if exist %UNFLOADER_PATH% (
    echo Fazendo deploy com UNFLoader...
    %UNFLOADER_PATH% -r %ROM_FILE%
) else (
    echo UNFLoader nao encontrado!
    echo Copie manualmente para o flashcart
    pause
)
'''
            flashcart_script.write_text(flashcart_content, encoding='utf-8')
            
            # Script de criação de projeto
            create_project_script = scripts_path / "create_n64_project.bat"
            create_project_content = f'''@echo off
REM Script para criar novo projeto N64
setlocal

if "%1"=="" (
    echo Uso: create_n64_project.bat nome_do_projeto
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

echo Criando projeto N64: %PROJECT_NAME%
mkdir "%PROJECT_DIR%"

echo Copiando template...
xcopy "{self.devkit_path}\\templates\\n64_template\\*" "%PROJECT_DIR%\\" /E /I /Q

echo Projeto criado: %PROJECT_DIR%
echo.
echo Para compilar: cd "%PROJECT_DIR%" && make
echo Para executar: run_n64_game.bat "%PROJECT_DIR%\\game.n64"
pause
'''
            create_project_script.write_text(create_project_content, encoding='utf-8')
            
            self.logger.info("Scripts de conveniência criados")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na criação de scripts: {e}")
            return False
            
    def create_project_template(self, project_name: str, project_path: Path) -> bool:
        """Cria template de projeto N64"""
        try:
            self.logger.info(f"Criando template de projeto N64: {project_name}")
            
            # Criar estrutura de diretórios
            project_path.mkdir(parents=True, exist_ok=True)
            (project_path / "src").mkdir(exist_ok=True)
            (project_path / "assets").mkdir(exist_ok=True)
            (project_path / "build").mkdir(exist_ok=True)
            (project_path / "include").mkdir(exist_ok=True)
            
            # Criar main.c
            main_c = project_path / "src" / "main.c"
            main_content = f'''// {project_name} - Nintendo 64 Project
// Generated by N64 Manager

#include <libdragon.h>
#include <stdio.h>

// Screen resolution
#define SCREEN_WIDTH  320
#define SCREEN_HEIGHT 240

static resolution_t res = RESOLUTION_320x240;
static bitdepth_t bit = DEPTH_16_BPP;

void init_graphics() {{
    // Initialize display
    display_init(res, bit, 2, GAMMA_NONE, ANTIALIAS_RESAMPLE);
    
    // Initialize RDP
    rdp_init();
    
    // Initialize controller
    controller_init();
}}

void draw_frame() {{
    static display_context_t disp = 0;
    
    // Wait for display
    while(!(disp = display_lock()));
    
    // Clear screen
    graphics_fill_screen(disp, 0x001F); // Blue background
    
    // Draw text
    graphics_set_color(0xFFFFFFFF, 0x00000000);
    graphics_draw_text(disp, 10, 10, "{project_name}");
    graphics_draw_text(disp, 10, 30, "Nintendo 64 Game");
    graphics_draw_text(disp, 10, 50, "Press START to exit");
    
    // Show display
    display_show(disp);
}}

int main() {{
    // Initialize systems
    init_graphics();
    
    printf("\\n{project_name} - N64 Game\\n");
    
    // Main game loop
    while(1) {{
        // Read controller
        controller_scan();
        struct controller_data keys = get_keys_down();
        
        // Check for START button
        if(keys.c[0].start) {{
            break;
        }}
        
        // Draw frame
        draw_frame();
    }}
    
    return 0;
}}
'''
            main_c.write_text(main_content, encoding='utf-8')
            
            # Criar Makefile
            makefile = project_path / "Makefile"
            makefile_content = f'''# Makefile for {project_name}
# Generated by N64 Manager

PROJECT_NAME = {project_name}
SOURCE_DIR = src
BUILD_DIR = build
ASSETS_DIR = assets
INCLUDE_DIR = include

# libdragon settings
N64_INST = {self.devkit_path}/libdragon
LIBDRAGON_HOME = {self.devkit_path}/libdragon
TOOLCHAIN = {self.devkit_path}/mips64-elf

CC = $(TOOLCHAIN)/bin/mips64-elf-gcc
LD = $(TOOLCHAIN)/bin/mips64-elf-ld
OBJCOPY = $(TOOLCHAIN)/bin/mips64-elf-objcopy
N64TOOL = $(LIBDRAGON_HOME)/tools/n64tool
CHKSUM64 = $(LIBDRAGON_HOME)/tools/chksum64

# Compiler flags
CFLAGS = -std=gnu99 -march=vr4300 -mtune=vr4300 -O2 -Wall -Werror -I$(LIBDRAGON_HOME)/include -I$(INCLUDE_DIR)
LDFLAGS = -L$(LIBDRAGON_HOME)/lib -ldragon -lc -lm -ldragonsys -Tn64.ld
ASFLAGS = -mtune=vr4300 -march=vr4300

# Source files
SOURCES = $(wildcard $(SOURCE_DIR)/*.c)
OBJECTS = $(SOURCES:$(SOURCE_DIR)/%.c=$(BUILD_DIR)/%.o)

# Target files
ELF = $(BUILD_DIR)/$(PROJECT_NAME).elf
BIN = $(BUILD_DIR)/$(PROJECT_NAME).bin
ROM = $(BUILD_DIR)/$(PROJECT_NAME).n64

.PHONY: all clean run debug

all: $(ROM)

$(ROM): $(BIN)
	@echo "Creating N64 ROM..."
	$(N64TOOL) -b -l 2M -h $(LIBDRAGON_HOME)/mips64-elf/lib/header -t "$(PROJECT_NAME)" $< $@
	$(CHKSUM64) $@

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

run: $(ROM)
	@echo "Running $(PROJECT_NAME)..."
	@"{self.emulators_path}/Ares/ares.exe" $(ROM)

debug: $(ROM)
	@echo "Debugging $(PROJECT_NAME)..."
	@"{self.emulators_path}/Mupen64Plus/mupen64plus.exe" --gdb $(ROM)
'''
            makefile.write_text(makefile_content, encoding='utf-8')
            
            # Criar README
            readme = project_path / "README.md"
            readme_content = f'''# {project_name}

Nintendo 64 project created with N64 Manager.

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
- `assets/` - Graphics and audio assets
- `build/` - Compiled objects and binaries
- `include/` - Header files

## Resources

- [libdragon Documentation](https://github.com/DragonMinded/libdragon)
- [N64 Programming Guide](https://ultra64.ca/files/documentation/online-manuals/)
- [N64 Development Community](https://discord.gg/WqFgNWf)
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
            "label": "Build N64 ROM",
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
            "label": "Run N64 Game",
            "type": "shell",
            "command": "make",
            "args": ["run"],
            "group": "test",
            "dependsOn": "Build N64 ROM"
        },
        {
            "label": "Debug N64 Game",
            "type": "shell",
            "command": "make",
            "args": ["debug"],
            "group": "test",
            "dependsOn": "Build N64 ROM"
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
        "*.c": "c"
    }},
    "C_Cpp.default.includePath": [
        "{self.devkit_path}/libdragon/include",
        "./include"
    ],
    "C_Cpp.default.defines": [
        "__N64__",
        "_LANGUAGE_C"
    ],
    "makefile.configureOnOpen": true
}}'''
            settings_json.write_text(settings_content, encoding='utf-8')
            
            self.logger.info(f"Template de projeto criado: {project_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na criação do template: {e}")
            return False