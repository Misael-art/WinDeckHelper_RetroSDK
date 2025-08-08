"""Melhorias específicas para o Neo Geo Development Kit (NGDevKit)
Implementação completa do manager para desenvolvimento Neo Geo"""

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

class NeoGeoManager(RetroDevkitManager):
    """Manager específico para Neo Geo Development Kit (NGDevKit)"""
    
    def __init__(self, base_path: Path, logger: logging.Logger):
        super().__init__(base_path, logger)
        self.ngdevkit_version = "latest"
        self.ngdevkit_url = "https://github.com/dciabrin/ngdevkit/archive/refs/heads/master.zip"
        self.gcc_m68k_url = "https://github.com/dciabrin/ngdevkit/releases/latest/download/ngdevkit-toolchain-win64.zip"
        
    def get_devkit_folder_name(self) -> str:
        """Retorna o nome da pasta do Neo Geo devkit"""
        return "NeoGeo"
        
    def get_devkit_info(self) -> DevkitInfo:
        """Retorna informações do Neo Geo devkit"""
        return DevkitInfo(
            name="Neo Geo Development Kit",
            console="SNK Neo Geo",
            devkit_name="NGDevKit",
            version=self.ngdevkit_version,
            dependencies=[
                "make",
                "unzip",
                "wget",
                "cmake",
                "python3",
                "mingw-w64"
            ],
            environment_vars={
                "NGDEVKIT": str(self.devkit_path / "ngdevkit"),
                "NGDEVKIT_TOOLCHAIN": str(self.devkit_path / "toolchain"),
                "PATH": str(self.devkit_path / "toolchain" / "bin")
            },
            download_url=self.ngdevkit_url,
            install_commands=[
                "Download and extract NGDevKit",
                "Download and extract m68k toolchain",
                "Setup environment variables",
                "Install emulators",
                "Setup VS Code extensions"
            ],
            verification_files=[
                "toolchain/bin/m68k-neogeo-elf-gcc.exe",
                "toolchain/bin/m68k-neogeo-elf-ld.exe",
                "ngdevkit/include/neogeo.h",
                "ngdevkit/include/ng/neogeo.h",
                "ngdevkit/tools/neosprconv.py"
            ]
        )
        
    def install_dependencies(self) -> bool:
        """Instala dependências do Neo Geo devkit"""
        try:
            self.logger.info("Instalando dependências do Neo Geo devkit...")
            
            # Download e instalação do m68k toolchain
            if not self._install_m68k_toolchain():
                return False
                
            # Download e instalação do NGDevKit
            if not self._install_ngdevkit():
                return False
                
            # Instalar ferramentas adicionais
            if not self._install_additional_tools():
                self.logger.warning("Falha na instalação de ferramentas adicionais")
                
            self.logger.info("Neo Geo devkit instalado com sucesso")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na instalação do Neo Geo devkit: {e}")
            return False
            
    def _install_m68k_toolchain(self) -> bool:
        """Instala o m68k toolchain"""
        try:
            self.logger.info("Instalando m68k toolchain...")
            
            toolchain_zip = self.devkit_path / "m68k-toolchain.zip"
            if not self.download_file(self.gcc_m68k_url, toolchain_zip, "m68k Toolchain"):
                return False
                
            # Extrair toolchain
            toolchain_path = self.devkit_path / "toolchain"
            if not self.extract_archive(toolchain_zip, toolchain_path):
                return False
                
            # Remover arquivo zip
            toolchain_zip.unlink()
            
            self.logger.info("m68k toolchain instalado com sucesso")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na instalação do m68k toolchain: {e}")
            return False
            
    def _install_ngdevkit(self) -> bool:
        """Instala o NGDevKit"""
        try:
            self.logger.info("Instalando NGDevKit...")
            
            ngdevkit_zip = self.devkit_path / "ngdevkit.zip"
            if not self.download_file(self.ngdevkit_url, ngdevkit_zip, "NGDevKit"):
                return False
                
            # Extrair NGDevKit
            ngdevkit_path = self.devkit_path / "ngdevkit"
            if not self.extract_archive(ngdevkit_zip, ngdevkit_path):
                return False
                
            # Remover arquivo zip
            ngdevkit_zip.unlink()
            
            self.logger.info("NGDevKit instalado com sucesso")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na instalação do NGDevKit: {e}")
            return False
            
    def _install_additional_tools(self) -> bool:
        """Instala ferramentas adicionais para Neo Geo"""
        try:
            self.logger.info("Instalando ferramentas adicionais...")
            
            tools_path = self.tools_path
            tools_path.mkdir(parents=True, exist_ok=True)
            
            # Criar scripts de conversão básicos
            self._create_conversion_scripts()
            
            # Instalar ferramentas de sprite/tile conversion
            self._install_sprite_tools()
            
            self.logger.info("Ferramentas adicionais instaladas")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na instalação de ferramentas adicionais: {e}")
            return False
            
    def _install_sprite_tools(self) -> bool:
        """Instala ferramentas de conversão de sprites"""
        try:
            self.logger.info("Instalando ferramentas de sprite...")
            
            # As ferramentas de sprite estão incluídas no NGDevKit
            # Criar scripts wrapper para facilitar o uso
            scripts_path = self.devkit_path / "scripts"
            scripts_path.mkdir(exist_ok=True)
            
            # Script para conversão de sprites
            sprite_script = scripts_path / "convert_sprite.bat"
            sprite_content = f'''@echo off
REM Script para conversao de sprites Neo Geo
setlocal

if "%1"=="" (
    echo Uso: convert_sprite.bat imagem.png
    pause
    exit /b 1
)

set IMAGE_FILE=%1
set NGDEVKIT_PATH="{self.devkit_path}\\ngdevkit"
set PYTHON_PATH=python

if exist %NGDEVKIT_PATH%\\tools\\neosprconv.py (
    echo Convertendo sprite %IMAGE_FILE%...
    %PYTHON_PATH% %NGDEVKIT_PATH%\\tools\\neosprconv.py %IMAGE_FILE%
) else (
    echo Ferramenta de conversao nao encontrada!
    pause
)
'''
            sprite_script.write_text(sprite_content, encoding='utf-8')
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na instalação de ferramentas de sprite: {e}")
            return False
            
    def _create_conversion_scripts(self) -> bool:
        """Cria scripts de conversão de assets"""
        try:
            scripts_path = self.devkit_path / "scripts"
            scripts_path.mkdir(exist_ok=True)
            
            # Script para conversão de tiles
            tile_script = scripts_path / "convert_tiles.bat"
            tile_content = '''@echo off
REM Script para conversao de tiles Neo Geo
echo Conversao de tiles ainda nao implementada
echo Use NGDevKit tools manualmente por enquanto
pause
'''
            tile_script.write_text(tile_content, encoding='utf-8')
            
            # Script para conversão de paletas
            palette_script = scripts_path / "convert_palette.bat"
            palette_content = '''@echo off
REM Script para conversao de paletas Neo Geo
echo Conversao de paletas ainda nao implementada
echo Use NGDevKit tools manualmente por enquanto
pause
'''
            palette_script.write_text(palette_content, encoding='utf-8')
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na criação de scripts de conversão: {e}")
            return False
            
    def verify_installation(self) -> bool:
        """Verifica se o Neo Geo devkit está instalado corretamente"""
        try:
            devkit_info = self.get_devkit_info()
            
            # Verificar arquivos essenciais
            for file_path in devkit_info.verification_files:
                full_path = self.devkit_path / file_path
                if not full_path.exists():
                    self.logger.error(f"Arquivo não encontrado: {full_path}")
                    return False
                    
            # Testar compilador m68k
            gcc_path = self.devkit_path / "toolchain" / "bin" / "m68k-neogeo-elf-gcc.exe"
            if gcc_path.exists():
                success, output = self.run_command([str(gcc_path), "--version"])
                if not success:
                    self.logger.error("Falha ao executar m68k-neogeo-elf-gcc")
                    return False
            else:
                self.logger.warning("Compilador m68k não encontrado")
                
            self.logger.info("Verificação do Neo Geo devkit concluída com sucesso")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na verificação do Neo Geo devkit: {e}")
            return False
            
    def install_emulators(self) -> bool:
        """Instala emuladores Neo Geo"""
        try:
            self.logger.info("Instalando emuladores Neo Geo...")
            
            emulators = {
                "MAME": {
                    "url": "https://github.com/mamedev/mame/releases/latest/download/mame0259b_64bit.exe",
                    "folder": "MAME"
                },
                "Nebula": {
                    "url": "http://nebula.emulatronia.com/descargas/nebula252.zip",
                    "folder": "Nebula"
                },
                "Kawaks": {
                    "url": "http://cps2shock.retrogames.com/kawaks.zip",
                    "folder": "Kawaks"
                }
            }
            
            for emu_name, emu_info in emulators.items():
                if emu_name == "MAME":
                    # MAME é um instalador
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
            
            # Script para MAME
            mame_script = scripts_path / "run_mame.bat"
            mame_content = f'''@echo off
REM Script para executar MAME
set MAME_PATH="C:\\mame\\mame.exe"
if exist %MAME_PATH% (
    start "" %MAME_PATH% neogeo -cart %1
) else (
    echo MAME nao encontrado!
    echo Instale o MAME em C:\\mame\\
    pause
)
'''
            mame_script.write_text(mame_content, encoding='utf-8')
            
            # Script para Nebula
            nebula_script = scripts_path / "run_nebula.bat"
            nebula_content = f'''@echo off
REM Script para executar Nebula
set EMULATOR_PATH="{self.emulators_path}\\Nebula\\nebula.exe"
if exist %EMULATOR_PATH% (
    start "" %EMULATOR_PATH% %1
) else (
    echo Nebula nao encontrado em %EMULATOR_PATH%
    pause
)
'''
            nebula_script.write_text(nebula_content, encoding='utf-8')
            
            # Script para Kawaks
            kawaks_script = scripts_path / "run_kawaks.bat"
            kawaks_content = f'''@echo off
REM Script para executar Kawaks
set EMULATOR_PATH="{self.emulators_path}\\Kawaks\\kawaks.exe"
if exist %EMULATOR_PATH% (
    start "" %EMULATOR_PATH% %1
) else (
    echo Kawaks nao encontrado em %EMULATOR_PATH%
    pause
)
'''
            kawaks_script.write_text(kawaks_content, encoding='utf-8')
            
            # Script genérico
            run_script = scripts_path / "run_neogeo_rom.bat"
            run_content = f'''@echo off
REM Script generico para executar ROM Neo Geo
setlocal

if "%1"=="" (
    echo Uso: run_neogeo_rom.bat arquivo.neo
    pause
    exit /b 1
)

set ROM_FILE=%1
set MAME_PATH="C:\\mame\\mame.exe"
set NEBULA_PATH="{self.emulators_path}\\Nebula\\nebula.exe"
set KAWAKS_PATH="{self.emulators_path}\\Kawaks\\kawaks.exe"

if exist %MAME_PATH% (
    echo Executando com MAME...
    start "" %MAME_PATH% neogeo -cart %ROM_FILE%
) else if exist %NEBULA_PATH% (
    echo Executando com Nebula...
    start "" %NEBULA_PATH% %ROM_FILE%
) else if exist %KAWAKS_PATH% (
    echo Executando com Kawaks...
    start "" %KAWAKS_PATH% %ROM_FILE%
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
        """Instala extensões VS Code para Neo Geo"""
        try:
            self.logger.info("Instalando extensões VS Code para Neo Geo...")
            
            extensions = [
                "ms-vscode.cpptools",  # C/C++ support
                "ms-vscode.makefile-tools",  # Makefile support
                "13xforever.language-x86-64-assembly",  # Assembly support
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
        """Cria scripts de conveniência para desenvolvimento Neo Geo"""
        try:
            self.logger.info("Criando scripts de conveniência...")
            
            scripts_path = self.devkit_path / "scripts"
            scripts_path.mkdir(exist_ok=True)
            
            # Script de compilação
            compile_script = scripts_path / "compile_neogeo_rom.bat"
            compile_content = f'''@echo off
REM Script de compilacao Neo Geo
setlocal

set NGDEVKIT={self.devkit_path}\\ngdevkit
set NGDEVKIT_TOOLCHAIN={self.devkit_path}\\toolchain
set PATH=%NGDEVKIT_TOOLCHAIN%\\bin;%PATH%

if "%1"=="" (
    echo Uso: compile_neogeo_rom.bat projeto_folder
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

echo Compilando projeto Neo Geo...
make

if exist "*.neo" (
    echo ROM criada com sucesso!
) else (
    echo Erro na compilacao!
)

pause
'''
            compile_script.write_text(compile_content, encoding='utf-8')
            
            # Script de execução
            run_script = scripts_path / "run_neogeo_game.bat"
            run_content = f'''@echo off
REM Script para executar jogo Neo Geo
setlocal

if "%1"=="" (
    echo Uso: run_neogeo_game.bat arquivo.neo
    pause
    exit /b 1
)

set ROM_FILE=%1
set MAME_PATH="C:\\mame\\mame.exe"
set NEBULA_PATH="{self.emulators_path}\\Nebula\\nebula.exe"

if exist %MAME_PATH% (
    echo Executando com MAME...
    start "" %MAME_PATH% neogeo -cart %ROM_FILE%
) else if exist %NEBULA_PATH% (
    echo Executando com Nebula...
    start "" %NEBULA_PATH% %ROM_FILE%
) else (
    echo Nenhum emulador encontrado!
    pause
)
'''
            run_script.write_text(run_content, encoding='utf-8')
            
            # Script de criação de projeto
            create_project_script = scripts_path / "create_neogeo_project.bat"
            create_project_content = f'''@echo off
REM Script para criar novo projeto Neo Geo
setlocal

if "%1"=="" (
    echo Uso: create_neogeo_project.bat nome_do_projeto
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

echo Criando projeto Neo Geo: %PROJECT_NAME%
mkdir "%PROJECT_DIR%"

echo Copiando template...
xcopy "{self.devkit_path}\\templates\\neogeo_template\\*" "%PROJECT_DIR%\\" /E /I /Q

echo Projeto criado: %PROJECT_DIR%
echo.
echo Para compilar: cd "%PROJECT_DIR%" && make
echo Para executar: run_neogeo_game.bat "%PROJECT_DIR%\\game.neo"
pause
'''
            create_project_script.write_text(create_project_content, encoding='utf-8')
            
            self.logger.info("Scripts de conveniência criados")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na criação de scripts: {e}")
            return False
            
    def create_project_template(self, project_name: str, project_path: Path) -> bool:
        """Cria template de projeto Neo Geo"""
        try:
            self.logger.info(f"Criando template de projeto Neo Geo: {project_name}")
            
            # Criar estrutura de diretórios
            project_path.mkdir(parents=True, exist_ok=True)
            (project_path / "src").mkdir(exist_ok=True)
            (project_path / "res").mkdir(exist_ok=True)
            (project_path / "build").mkdir(exist_ok=True)
            (project_path / "include").mkdir(exist_ok=True)
            
            # Criar main.c
            main_c = project_path / "src" / "main.c"
            main_content = f'''// {project_name} - Neo Geo Project
// Generated by Neo Geo Manager

#include <neogeo.h>
#include <ng/neogeo.h>

// Screen dimensions
#define SCREEN_WIDTH  320
#define SCREEN_HEIGHT 224

// Sprite and tile definitions
#define SPRITE_CHAR   0x0000
#define TILE_CHAR     0x1000

void init_neogeo() {{
    // Initialize Neo Geo hardware
    // Set up video modes, palettes, etc.
    
    // Clear screen
    for (int i = 0; i < 0x7000; i++) {{
        *((volatile u16*)(0x200000 + i * 2)) = 0x0020;
    }}
}}

void main() {{
    // Initialize Neo Geo
    init_neogeo();
    
    // Main game loop
    while(1) {{
        // Read input
        u8 input = *((volatile u8*)0x300000);
        
        // Simple input handling
        if (input & 0x01) {{ // Button A
            // Do something
        }}
        
        if (input & 0x02) {{ // Button B
            // Do something else
        }}
        
        // Wait for VBlank
        while (!(*((volatile u8*)0x3C0006) & 0x01));
        while (*((volatile u8*)0x3C0006) & 0x01);
    }}
}}
'''
            main_c.write_text(main_content, encoding='utf-8')
            
            # Criar Makefile
            makefile = project_path / "Makefile"
            makefile_content = f'''# Makefile for {project_name}
# Generated by Neo Geo Manager

PROJECT_NAME = {project_name}
SOURCE_DIR = src
BUILD_DIR = build
RES_DIR = res
INCLUDE_DIR = include

# NGDevKit settings
NGDEVKIT = {self.devkit_path}/ngdevkit
NGDEVKIT_TOOLCHAIN = {self.devkit_path}/toolchain

CC = $(NGDEVKIT_TOOLCHAIN)/bin/m68k-neogeo-elf-gcc
LD = $(NGDEVKIT_TOOLCHAIN)/bin/m68k-neogeo-elf-ld
OBJCOPY = $(NGDEVKIT_TOOLCHAIN)/bin/m68k-neogeo-elf-objcopy

# Compiler flags
CFLAGS = -I$(NGDEVKIT)/include -I$(INCLUDE_DIR) -O2 -fomit-frame-pointer
LDFLAGS = -L$(NGDEVKIT)/lib -lneogeo

# Source files
SOURCES = $(wildcard $(SOURCE_DIR)/*.c)
OBJECTS = $(SOURCES:$(SOURCE_DIR)/%.c=$(BUILD_DIR)/%.o)

# Target files
ELF = $(BUILD_DIR)/$(PROJECT_NAME).elf
BIN = $(BUILD_DIR)/$(PROJECT_NAME).bin
ROM = $(BUILD_DIR)/$(PROJECT_NAME).neo

.PHONY: all clean run

all: $(ROM)

$(ROM): $(BIN)
	@echo "Creating Neo Geo ROM..."
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

run: $(ROM)
	@echo "Running $(PROJECT_NAME)..."
	@"{self.emulators_path}/Nebula/nebula.exe" $(ROM)
'''
            makefile.write_text(makefile_content, encoding='utf-8')
            
            # Criar README
            readme = project_path / "README.md"
            readme_content = f'''# {project_name}

Neo Geo project created with Neo Geo Manager.

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

- `src/` - C source files
- `res/` - Graphics and audio resources
- `build/` - Compiled objects and binaries
- `include/` - Header files

## Resources

- [NGDevKit Documentation](https://github.com/dciabrin/ngdevkit)
- [Neo Geo Programming Guide](https://wiki.neogeodev.org/)
- [Neo Geo Development Community](https://neogeodev.org/)
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
            "label": "Build Neo Geo ROM",
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
            "label": "Run Neo Geo Game",
            "type": "shell",
            "command": "make",
            "args": ["run"],
            "group": "test",
            "dependsOn": "Build Neo Geo ROM"
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
        "*.s": "asm"
    }},
    "C_Cpp.default.includePath": [
        "{self.devkit_path}/ngdevkit/include",
        "./include"
    ],
    "C_Cpp.default.defines": [
        "__NEOGEO__"
    ],
    "makefile.configureOnOpen": true
}}'''
            settings_json.write_text(settings_content, encoding='utf-8')
            
            self.logger.info(f"Template de projeto criado: {project_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na criação do template: {e}")
            return False