"""Melhorias específicas para o Game Boy Development Kit (GBDK-2020)
Implementação completa do manager para desenvolvimento Game Boy/Game Boy Color"""

import os
import sys
import json
import subprocess
import shutil
import urllib.request
import zipfile
import platform
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import logging
from dataclasses import dataclass

from .retro_devkit_base import RetroDevkitManager, DevkitInfo

class GBDKManager(RetroDevkitManager):
    """Manager específico para Game Boy Development Kit (GBDK-2020)"""
    
    def __init__(self, base_path: Path, logger: logging.Logger):
        super().__init__(base_path, logger)
        self.gbdk_version = "4.2.0"
        self.gbdk_url = f"https://github.com/gbdk-2020/gbdk-2020/releases/download/{self.gbdk_version}/gbdk-windows-x64.zip"
        
    def get_devkit_folder_name(self) -> str:
        """Retorna o nome da pasta do GBDK"""
        return "GBDK"
        
    def get_devkit_info(self) -> DevkitInfo:
        """Retorna informações do GBDK"""
        return DevkitInfo(
            name="Game Boy Development Kit",
            console="Game Boy / Game Boy Color",
            devkit_name="GBDK-2020",
            version=self.gbdk_version,
            dependencies=[
                "make",
                "unzip",
                "wget"
            ],
            environment_vars={
                "GBDK_HOME": str(self.devkit_path),
                "PATH": str(self.devkit_path / "bin")
            },
            download_url=self.gbdk_url,
            install_commands=[
                "Download and extract GBDK-2020",
                "Setup environment variables",
                "Install emulators",
                "Setup VS Code extensions"
            ],
            verification_files=[
                "bin/lcc.exe",
                "bin/sdcc.exe",
                "bin/sdldgb.exe",
                "include/gb/gb.h"
            ]
        )
        
    def install_dependencies(self) -> bool:
        """Instala dependências do GBDK"""
        try:
            self.logger.info("Instalando dependências do GBDK...")
            
            # Download do GBDK-2020
            gbdk_zip = self.devkit_path / "gbdk.zip"
            if not self.download_file(self.gbdk_url, gbdk_zip, "GBDK-2020"):
                return False
                
            # Extrair GBDK
            if not self.extract_archive(gbdk_zip, self.devkit_path):
                return False
                
            # Mover arquivos para estrutura correta
            extracted_folder = self.devkit_path / "gbdk"
            if extracted_folder.exists():
                for item in extracted_folder.iterdir():
                    shutil.move(str(item), str(self.devkit_path))
                extracted_folder.rmdir()
                
            # Remover arquivo zip
            gbdk_zip.unlink()
            
            self.logger.info("GBDK-2020 instalado com sucesso")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na instalação do GBDK: {e}")
            return False
            
    def verify_installation(self) -> bool:
        """Verifica se o GBDK está instalado corretamente"""
        try:
            devkit_info = self.get_devkit_info()
            
            # Verificar arquivos essenciais
            for file_path in devkit_info.verification_files:
                full_path = self.devkit_path / file_path
                if not full_path.exists():
                    self.logger.error(f"Arquivo não encontrado: {full_path}")
                    return False
                    
            # Testar compilador
            lcc_path = self.devkit_path / "bin" / "lcc.exe"
            success, output = self.run_command([str(lcc_path), "-v"])
            if not success:
                self.logger.error("Falha ao executar lcc")
                return False
                
            self.logger.info("Verificação do GBDK concluída com sucesso")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na verificação do GBDK: {e}")
            return False
            
    def install_emulators(self) -> bool:
        """Instala emuladores Game Boy"""
        try:
            self.logger.info("Instalando emuladores Game Boy...")
            
            emulators = {
                "BGB": {
                    "url": "https://bgb.bircd.org/bgb.zip",
                    "folder": "BGB"
                },
                "SameBoy": {
                    "url": "https://github.com/LIJI32/SameBoy/releases/latest/download/sameboy_winsdl.zip",
                    "folder": "SameBoy"
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
            
            # Script para BGB
            bgb_script = scripts_path / "run_bgb.bat"
            bgb_content = f'''@echo off
REM Script para executar BGB
set EMULATOR_PATH="{self.emulators_path}\\BGB\\bgb.exe"
if exist %EMULATOR_PATH% (
    start "" %EMULATOR_PATH% %1
) else (
    echo BGB nao encontrado em %EMULATOR_PATH%
    pause
)
'''
            bgb_script.write_text(bgb_content, encoding='utf-8')
            
            # Script para SameBoy
            sameboy_script = scripts_path / "run_sameboy.bat"
            sameboy_content = f'''@echo off
REM Script para executar SameBoy
set EMULATOR_PATH="{self.emulators_path}\\SameBoy\\sameboy.exe"
if exist %EMULATOR_PATH% (
    start "" %EMULATOR_PATH% %1
) else (
    echo SameBoy nao encontrado em %EMULATOR_PATH%
    pause
)
'''
            sameboy_script.write_text(sameboy_content, encoding='utf-8')
            
            self.logger.info("Scripts de emuladores criados")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na criação de scripts de emuladores: {e}")
            return False
            
    def install_vscode_extensions(self) -> bool:
        """Instala extensões VS Code para Game Boy"""
        try:
            self.logger.info("Instalando extensões VS Code para Game Boy...")
            
            extensions = [
                "ms-vscode.cpptools",  # C/C++ support
                "ms-vscode.makefile-tools",  # Makefile support
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
        """Cria scripts de conveniência para desenvolvimento GB"""
        try:
            self.logger.info("Criando scripts de conveniência...")
            
            scripts_path = self.devkit_path / "scripts"
            scripts_path.mkdir(exist_ok=True)
            
            # Script de compilação
            compile_script = scripts_path / "compile_gb_rom.bat"
            compile_content = f'''@echo off
REM Script de compilacao Game Boy
setlocal

set GBDK_HOME={self.devkit_path}
set PATH=%GBDK_HOME%\\bin;%PATH%

if "%1"=="" (
    echo Uso: compile_gb_rom.bat arquivo.c
    pause
    exit /b 1
)

set SOURCE_FILE=%1
set ROM_FILE=%~n1.gb

echo Compilando %SOURCE_FILE%...
lcc -Wa-l -Wl-m -Wl-j -DUSE_SFR_FOR_REG=1 -c -o %~n1.o %SOURCE_FILE%
lcc -Wa-l -Wl-m -Wl-j -DUSE_SFR_FOR_REG=1 -o %ROM_FILE% %~n1.o

if exist %ROM_FILE% (
    echo ROM criada: %ROM_FILE%
) else (
    echo Erro na compilacao!
)

pause
'''
            compile_script.write_text(compile_content, encoding='utf-8')
            
            # Script de execução
            run_script = scripts_path / "run_gb_rom.bat"
            run_content = f'''@echo off
REM Script para executar ROM Game Boy
setlocal

if "%1"=="" (
    echo Uso: run_gb_rom.bat arquivo.gb
    pause
    exit /b 1
)

set ROM_FILE=%1
set BGB_PATH="{self.emulators_path}\\BGB\\bgb.exe"
set SAMEBOY_PATH="{self.emulators_path}\\SameBoy\\sameboy.exe"

if exist %BGB_PATH% (
    echo Executando com BGB...
    start "" %BGB_PATH% %ROM_FILE%
) else if exist %SAMEBOY_PATH% (
    echo Executando com SameBoy...
    start "" %SAMEBOY_PATH% %ROM_FILE%
) else (
    echo Nenhum emulador encontrado!
    pause
)
'''
            run_script.write_text(run_content, encoding='utf-8')
            
            # Script de debug
            debug_script = scripts_path / "debug_gb_rom.bat"
            debug_content = f'''@echo off
REM Script de debug Game Boy com BGB
setlocal

if "%1"=="" (
    echo Uso: debug_gb_rom.bat arquivo.gb
    pause
    exit /b 1
)

set ROM_FILE=%1
set BGB_PATH="{self.emulators_path}\\BGB\\bgb.exe"

if exist %BGB_PATH% (
    echo Iniciando debug com BGB...
    start "" %BGB_PATH% -d %ROM_FILE%
) else (
    echo BGB nao encontrado para debug!
    pause
)
'''
            debug_script.write_text(debug_content, encoding='utf-8')
            
            # Script de limpeza
            clean_script = scripts_path / "clean_gb_project.bat"
            clean_content = '''@echo off
REM Script de limpeza de projeto Game Boy
echo Limpando arquivos temporarios...
del /q *.o *.lst *.map *.sym 2>nul
echo Limpeza concluida!
pause
'''
            clean_script.write_text(clean_content, encoding='utf-8')
            
            self.logger.info("Scripts de conveniência criados")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na criação de scripts: {e}")
            return False
            
    def create_project_template(self, project_name: str, project_path: Path) -> bool:
        """Cria template de projeto Game Boy"""
        try:
            self.logger.info(f"Criando template de projeto Game Boy: {project_name}")
            
            # Criar estrutura de diretórios
            project_path.mkdir(parents=True, exist_ok=True)
            (project_path / "src").mkdir(exist_ok=True)
            (project_path / "assets").mkdir(exist_ok=True)
            (project_path / "build").mkdir(exist_ok=True)
            
            # Criar main.c
            main_c = project_path / "src" / "main.c"
            main_content = f'''// {project_name} - Game Boy Project
// Generated by GBDK Manager

#include <gb/gb.h>
#include <stdio.h>

// Sprite data (8x8 pixel sprite)
const unsigned char sprite_data[] = {{
    0x7E, 0x7E, 0x81, 0xFF, 0xA5, 0xFF, 0x81, 0xFF,
    0xBD, 0xFF, 0x81, 0xFF, 0x7E, 0x7E, 0x00, 0x00
}};

void main() {{
    // Initialize graphics
    DISPLAY_ON;
    SHOW_SPRITES;
    
    // Load sprite data
    set_sprite_data(0, 1, sprite_data);
    set_sprite_tile(0, 0);
    move_sprite(0, 88, 78);
    
    // Main game loop
    while(1) {{
        // Wait for VBlank
        wait_vbl_done();
        
        // Game logic here
    }}
}}
'''
            main_c.write_text(main_content, encoding='utf-8')
            
            # Criar Makefile
            makefile = project_path / "Makefile"
            makefile_content = f'''# Makefile for {project_name}
# Generated by GBDK Manager

PROJECT_NAME = {project_name}
SOURCE_DIR = src
BUILD_DIR = build
ASSETS_DIR = assets

# GBDK settings
GBDK_HOME = {self.devkit_path}
LCC = $(GBDK_HOME)/bin/lcc

# Compiler flags
CFLAGS = -Wa-l -Wl-m -Wl-j -DUSE_SFR_FOR_REG=1

# Source files
SOURCES = $(wildcard $(SOURCE_DIR)/*.c)
OBJECTS = $(SOURCES:$(SOURCE_DIR)/%.c=$(BUILD_DIR)/%.o)

# Target ROM
ROM = $(BUILD_DIR)/$(PROJECT_NAME).gb

.PHONY: all clean run debug

all: $(ROM)

$(ROM): $(OBJECTS)
	@echo "Linking $(PROJECT_NAME)..."
	$(LCC) $(CFLAGS) -o $@ $^
	@echo "ROM created: $@"

$(BUILD_DIR)/%.o: $(SOURCE_DIR)/%.c
	@mkdir -p $(BUILD_DIR)
	@echo "Compiling $<..."
	$(LCC) $(CFLAGS) -c -o $@ $<

clean:
	@echo "Cleaning build files..."
	@rm -rf $(BUILD_DIR)/*

run: $(ROM)
	@echo "Running $(PROJECT_NAME)..."
	@"{self.emulators_path}/BGB/bgb.exe" $(ROM)

debug: $(ROM)
	@echo "Debugging $(PROJECT_NAME)..."
	@"{self.emulators_path}/BGB/bgb.exe" -d $(ROM)
'''
            makefile.write_text(makefile_content, encoding='utf-8')
            
            # Criar README
            readme = project_path / "README.md"
            readme_content = f'''# {project_name}

Game Boy project created with GBDK Manager.

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

- `src/` - Source code files
- `assets/` - Graphics and audio assets
- `build/` - Compiled objects and ROM

## Resources

- [GBDK-2020 Documentation](https://gbdk-2020.github.io/gbdk-2020/)
- [Game Boy Programming Manual](https://ia801906.us.archive.org/19/items/GameBoyProgManVer1.1/GameBoyProgManVer1.1.pdf)
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
            "label": "Build Game Boy ROM",
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
            "problemMatcher": []
        },
        {
            "label": "Run Game Boy ROM",
            "type": "shell",
            "command": "make",
            "args": ["run"],
            "group": "test",
            "dependsOn": "Build Game Boy ROM"
        },
        {
            "label": "Debug Game Boy ROM",
            "type": "shell",
            "command": "make",
            "args": ["debug"],
            "group": "test",
            "dependsOn": "Build Game Boy ROM"
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
        "{self.devkit_path}/include"
    ],
    "C_Cpp.default.defines": [
        "USE_SFR_FOR_REG=1"
    ],
    "makefile.configureOnOpen": true
}}'''
            settings_json.write_text(settings_content, encoding='utf-8')
            
            self.logger.info(f"Template de projeto criado: {project_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na criação do template: {e}")
            return False