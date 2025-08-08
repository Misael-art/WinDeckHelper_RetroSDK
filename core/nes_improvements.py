"""Melhorias específicas para o NES Development Kit (CC65)
Implementação completa do manager para desenvolvimento NES"""

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

class NESManager(RetroDevkitManager):
    """Manager específico para NES Development Kit (CC65)"""
    
    def __init__(self, base_path: Path, logger: logging.Logger):
        super().__init__(base_path, logger)
        self.cc65_version = "2.19"
        self.cc65_url = f"https://github.com/cc65/cc65/releases/download/V{self.cc65_version}/cc65-{self.cc65_version}-windows.zip"
        self.neslib_url = "https://github.com/clbr/neslib/archive/refs/heads/master.zip"
        
    def get_devkit_folder_name(self) -> str:
        """Retorna o nome da pasta do NES devkit"""
        return "NES"
        
    def get_devkit_info(self) -> DevkitInfo:
        """Retorna informações do NES devkit"""
        return DevkitInfo(
            name="NES Development Kit",
            console="Nintendo Entertainment System",
            devkit_name="CC65",
            version=self.cc65_version,
            dependencies=[
                "make",
                "unzip",
                "wget",
                "python3"
            ],
            environment_vars={
                "CC65_HOME": str(self.devkit_path / "cc65"),
                "PATH": str(self.devkit_path / "cc65" / "bin")
            },
            download_url=self.cc65_url,
            install_commands=[
                "Download and extract CC65",
                "Download and extract NESLib",
                "Setup environment variables",
                "Install emulators",
                "Setup VS Code extensions"
            ],
            verification_files=[
                "cc65/bin/cc65.exe",
                "cc65/bin/ca65.exe",
                "cc65/bin/ld65.exe",
                "cc65/lib/nes.lib",
                "neslib/neslib.h",
                "neslib/neslib.lib"
            ]
        )
        
    def install_dependencies(self) -> bool:
        """Instala dependências do NES devkit"""
        try:
            self.logger.info("Instalando dependências do NES devkit...")
            
            # Download e instalação do CC65
            if not self._install_cc65():
                return False
                
            # Download e instalação do NESLib
            if not self._install_neslib():
                return False
                
            # Instalar ferramentas adicionais
            if not self._install_additional_tools():
                self.logger.warning("Falha na instalação de ferramentas adicionais")
                
            self.logger.info("NES devkit instalado com sucesso")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na instalação do NES devkit: {e}")
            return False
            
    def _install_cc65(self) -> bool:
        """Instala o CC65 compiler suite"""
        try:
            self.logger.info("Instalando CC65...")
            
            cc65_zip = self.devkit_path / "cc65.zip"
            if not self.download_file(self.cc65_url, cc65_zip, "CC65"):
                return False
                
            # Extrair CC65
            cc65_path = self.devkit_path / "cc65"
            if not self.extract_archive(cc65_zip, cc65_path):
                return False
                
            # Remover arquivo zip
            cc65_zip.unlink()
            
            self.logger.info("CC65 instalado com sucesso")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na instalação do CC65: {e}")
            return False
            
    def _install_neslib(self) -> bool:
        """Instala a NESLib"""
        try:
            self.logger.info("Instalando NESLib...")
            
            neslib_zip = self.devkit_path / "neslib.zip"
            if not self.download_file(self.neslib_url, neslib_zip, "NESLib"):
                return False
                
            # Extrair NESLib
            neslib_path = self.devkit_path / "neslib"
            if not self.extract_archive(neslib_zip, neslib_path):
                return False
                
            # Remover arquivo zip
            neslib_zip.unlink()
            
            # Compilar NESLib se necessário
            self._compile_neslib(neslib_path)
            
            self.logger.info("NESLib instalada com sucesso")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na instalação da NESLib: {e}")
            return False
            
    def _compile_neslib(self, neslib_path: Path) -> bool:
        """Compila a NESLib se necessário"""
        try:
            # Verificar se já existe neslib.lib
            lib_file = neslib_path / "neslib.lib"
            if lib_file.exists():
                return True
                
            self.logger.info("Compilando NESLib...")
            
            # Procurar por Makefile ou script de build
            makefile = neslib_path / "Makefile"
            if makefile.exists():
                success, output = self.run_command(["make"], cwd=str(neslib_path))
                if success:
                    self.logger.info("NESLib compilada com sucesso")
                    return True
                else:
                    self.logger.warning(f"Falha na compilação da NESLib: {output}")
                    
            return True  # Continuar mesmo se a compilação falhar
            
        except Exception as e:
            self.logger.error(f"Erro na compilação da NESLib: {e}")
            return True  # Não falhar por causa disso
            
    def _install_additional_tools(self) -> bool:
        """Instala ferramentas adicionais para NES"""
        try:
            self.logger.info("Instalando ferramentas adicionais...")
            
            tools_path = self.tools_path
            tools_path.mkdir(parents=True, exist_ok=True)
            
            # Instalar ferramentas de conversão
            self._install_conversion_tools()
            
            # Criar scripts de conveniência
            self._create_convenience_scripts()
            
            self.logger.info("Ferramentas adicionais instaladas")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na instalação de ferramentas adicionais: {e}")
            return False
            
    def _install_conversion_tools(self) -> bool:
        """Instala ferramentas de conversão de assets"""
        try:
            self.logger.info("Instalando ferramentas de conversão...")
            
            tools_path = self.tools_path
            
            # Criar scripts de conversão básicos
            scripts_path = self.devkit_path / "scripts"
            scripts_path.mkdir(exist_ok=True)
            
            # Script para conversão de CHR (gráficos)
            chr_script = scripts_path / "convert_chr.bat"
            chr_content = '''@echo off
REM Script para conversao de CHR (graficos NES)
echo Conversao de CHR ainda nao implementada
echo Use ferramentas como NES Screen Tool ou YY-CHR
pause
'''
            chr_script.write_text(chr_content, encoding='utf-8')
            
            # Script para conversão de música
            music_script = scripts_path / "convert_music.bat"
            music_content = '''@echo off
REM Script para conversao de musica NES
echo Conversao de musica ainda nao implementada
echo Use FamiTracker ou FamiStudio
pause
'''
            music_script.write_text(music_content, encoding='utf-8')
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na instalação de ferramentas de conversão: {e}")
            return False
            
    def verify_installation(self) -> bool:
        """Verifica se o NES devkit está instalado corretamente"""
        try:
            devkit_info = self.get_devkit_info()
            
            # Verificar arquivos essenciais
            for file_path in devkit_info.verification_files:
                full_path = self.devkit_path / file_path
                if not full_path.exists():
                    self.logger.warning(f"Arquivo não encontrado: {full_path}")
                    
            # Testar compilador CC65
            cc65_path = self.devkit_path / "cc65" / "bin" / "cc65.exe"
            if cc65_path.exists():
                success, output = self.run_command([str(cc65_path), "--version"])
                if not success:
                    self.logger.error("Falha ao executar cc65")
                    return False
            else:
                self.logger.error("Compilador CC65 não encontrado")
                return False
                
            # Testar assembler CA65
            ca65_path = self.devkit_path / "cc65" / "bin" / "ca65.exe"
            if ca65_path.exists():
                success, output = self.run_command([str(ca65_path), "--version"])
                if not success:
                    self.logger.error("Falha ao executar ca65")
                    return False
            else:
                self.logger.error("Assembler CA65 não encontrado")
                return False
                
            self.logger.info("Verificação do NES devkit concluída com sucesso")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na verificação do NES devkit: {e}")
            return False
            
    def install_emulators(self) -> bool:
        """Instala emuladores NES"""
        try:
            self.logger.info("Instalando emuladores NES...")
            
            emulators = {
                "FCEUX": {
                    "url": "https://github.com/TASEmulators/fceux/releases/latest/download/fceux-win64.zip",
                    "folder": "FCEUX"
                },
                "Nestopia": {
                    "url": "https://github.com/0ldsk00l/nestopia/releases/latest/download/Nestopia-win64.zip",
                    "folder": "Nestopia"
                },
                "Mesen": {
                    "url": "https://github.com/SourMesen/Mesen/releases/latest/download/Mesen.zip",
                    "folder": "Mesen"
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
            
            # Script para FCEUX
            fceux_script = scripts_path / "run_fceux.bat"
            fceux_content = f'''@echo off
REM Script para executar FCEUX
set EMULATOR_PATH="{self.emulators_path}\\FCEUX\\fceux.exe"
if exist %EMULATOR_PATH% (
    start "" %EMULATOR_PATH% %1
) else (
    echo FCEUX nao encontrado em %EMULATOR_PATH%
    pause
)
'''
            fceux_script.write_text(fceux_content, encoding='utf-8')
            
            # Script para Nestopia
            nestopia_script = scripts_path / "run_nestopia.bat"
            nestopia_content = f'''@echo off
REM Script para executar Nestopia
set EMULATOR_PATH="{self.emulators_path}\\Nestopia\\nestopia.exe"
if exist %EMULATOR_PATH% (
    start "" %EMULATOR_PATH% %1
) else (
    echo Nestopia nao encontrado em %EMULATOR_PATH%
    pause
)
'''
            nestopia_script.write_text(nestopia_content, encoding='utf-8')
            
            # Script para Mesen
            mesen_script = scripts_path / "run_mesen.bat"
            mesen_content = f'''@echo off
REM Script para executar Mesen
set EMULATOR_PATH="{self.emulators_path}\\Mesen\\Mesen.exe"
if exist %EMULATOR_PATH% (
    start "" %EMULATOR_PATH% %1
) else (
    echo Mesen nao encontrado em %EMULATOR_PATH%
    pause
)
'''
            mesen_script.write_text(mesen_content, encoding='utf-8')
            
            # Script genérico
            run_script = scripts_path / "run_nes_rom.bat"
            run_content = f'''@echo off
REM Script generico para executar ROM NES
setlocal

if "%1"=="" (
    echo Uso: run_nes_rom.bat arquivo.nes
    pause
    exit /b 1
)

set ROM_FILE=%1
set FCEUX_PATH="{self.emulators_path}\\FCEUX\\fceux.exe"
set NESTOPIA_PATH="{self.emulators_path}\\Nestopia\\nestopia.exe"
set MESEN_PATH="{self.emulators_path}\\Mesen\\Mesen.exe"

if exist %FCEUX_PATH% (
    echo Executando com FCEUX...
    start "" %FCEUX_PATH% %ROM_FILE%
) else if exist %NESTOPIA_PATH% (
    echo Executando com Nestopia...
    start "" %NESTOPIA_PATH% %ROM_FILE%
) else if exist %MESEN_PATH% (
    echo Executando com Mesen...
    start "" %MESEN_PATH% %ROM_FILE%
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
        """Instala extensões VS Code para NES"""
        try:
            self.logger.info("Instalando extensões VS Code para NES...")
            
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
        """Cria scripts de conveniência para desenvolvimento NES"""
        try:
            self.logger.info("Criando scripts de conveniência...")
            
            scripts_path = self.devkit_path / "scripts"
            scripts_path.mkdir(exist_ok=True)
            
            # Script de compilação
            compile_script = scripts_path / "compile_nes_rom.bat"
            compile_content = f'''@echo off
REM Script de compilacao NES
setlocal

set CC65_HOME={self.devkit_path}\\cc65
set PATH=%CC65_HOME%\\bin;%PATH%

if "%1"=="" (
    echo Uso: compile_nes_rom.bat projeto_folder
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

echo Compilando projeto NES...
make

if exist "*.nes" (
    echo ROM criada com sucesso!
) else (
    echo Erro na compilacao!
)

pause
'''
            compile_script.write_text(compile_content, encoding='utf-8')
            
            # Script de execução
            run_script = scripts_path / "run_nes_game.bat"
            run_content = f'''@echo off
REM Script para executar jogo NES
setlocal

if "%1"=="" (
    echo Uso: run_nes_game.bat arquivo.nes
    pause
    exit /b 1
)

set ROM_FILE=%1
set FCEUX_PATH="{self.emulators_path}\\FCEUX\\fceux.exe"
set MESEN_PATH="{self.emulators_path}\\Mesen\\Mesen.exe"

if exist %FCEUX_PATH% (
    echo Executando com FCEUX...
    start "" %FCEUX_PATH% %ROM_FILE%
) else if exist %MESEN_PATH% (
    echo Executando com Mesen...
    start "" %MESEN_PATH% %ROM_FILE%
) else (
    echo Nenhum emulador encontrado!
    pause
)
'''
            run_script.write_text(run_content, encoding='utf-8')
            
            # Script de criação de projeto
            create_project_script = scripts_path / "create_nes_project.bat"
            create_project_content = f'''@echo off
REM Script para criar novo projeto NES
setlocal

if "%1"=="" (
    echo Uso: create_nes_project.bat nome_do_projeto
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

echo Criando projeto NES: %PROJECT_NAME%
mkdir "%PROJECT_DIR%"

echo Copiando template...
xcopy "{self.devkit_path}\\templates\\nes_template\\*" "%PROJECT_DIR%\\" /E /I /Q

echo Projeto criado: %PROJECT_DIR%
echo.
echo Para compilar: cd "%PROJECT_DIR%" && make
echo Para executar: run_nes_game.bat "%PROJECT_DIR%\\game.nes"
pause
'''
            create_project_script.write_text(create_project_content, encoding='utf-8')
            
            # Script de debug
            debug_script = scripts_path / "debug_nes_game.bat"
            debug_content = f'''@echo off
REM Script para debug de jogo NES
setlocal

if "%1"=="" (
    echo Uso: debug_nes_game.bat arquivo.nes
    pause
    exit /b 1
)

set ROM_FILE=%1
set FCEUX_PATH="{self.emulators_path}\\FCEUX\\fceux.exe"
set MESEN_PATH="{self.emulators_path}\\Mesen\\Mesen.exe"

if exist %MESEN_PATH% (
    echo Iniciando debug com Mesen...
    start "" %MESEN_PATH% %ROM_FILE% --debug
) else if exist %FCEUX_PATH% (
    echo Iniciando debug com FCEUX...
    start "" %FCEUX_PATH% %ROM_FILE%
) else (
    echo Nenhum emulador encontrado!
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
        """Cria template de projeto NES"""
        try:
            self.logger.info(f"Criando template de projeto NES: {project_name}")
            
            # Criar estrutura de diretórios
            project_path.mkdir(parents=True, exist_ok=True)
            (project_path / "src").mkdir(exist_ok=True)
            (project_path / "res").mkdir(exist_ok=True)
            (project_path / "build").mkdir(exist_ok=True)
            (project_path / "include").mkdir(exist_ok=True)
            
            # Criar main.c
            main_c = project_path / "src" / "main.c"
            main_content = f'''// {project_name} - NES Project
// Generated by NES Manager

#include <neslib.h>
#include <string.h>

// Screen dimensions
#define SCREEN_WIDTH  256
#define SCREEN_HEIGHT 240

// Sprite definitions
#define SPRITE_PLAYER 0

// Game variables
unsigned char player_x = 128;
unsigned char player_y = 120;

void init_nes() {{
    // Initialize NES hardware
    ppu_off();
    
    // Set background color
    pal_bg(palette_bg);
    pal_spr(palette_spr);
    
    // Enable sprites and background
    ppu_on_all();
}}

void update_input() {{
    unsigned char pad = pad_poll(0);
    
    // Move player with D-pad
    if (pad & PAD_LEFT && player_x > 8) {{
        player_x--;
    }}
    if (pad & PAD_RIGHT && player_x < 248) {{
        player_x++;
    }}
    if (pad & PAD_UP && player_y > 8) {{
        player_y--;
    }}
    if (pad & PAD_DOWN && player_y < 232) {{
        player_y++;
    }}
}}

void update_sprites() {{
    // Update player sprite
    oam_spr(player_x, player_y, SPRITE_PLAYER, 0);
}}

void main() {{
    // Initialize NES
    init_nes();
    
    // Main game loop
    while(1) {{
        // Update input
        update_input();
        
        // Update sprites
        update_sprites();
        
        // Wait for next frame
        ppu_wait_nmi();
    }}
}}

// Background palette
const unsigned char palette_bg[] = {{
    0x0F, 0x00, 0x10, 0x30,  // Background 0
    0x0F, 0x06, 0x16, 0x26,  // Background 1
    0x0F, 0x09, 0x19, 0x29,  // Background 2
    0x0F, 0x01, 0x11, 0x21   // Background 3
}};

// Sprite palette
const unsigned char palette_spr[] = {{
    0x0F, 0x14, 0x24, 0x34,  // Sprite 0
    0x0F, 0x02, 0x12, 0x22,  // Sprite 1
    0x0F, 0x07, 0x17, 0x27,  // Sprite 2
    0x0F, 0x0A, 0x1A, 0x2A   // Sprite 3
}};
'''
            main_c.write_text(main_content, encoding='utf-8')
            
            # Criar Makefile
            makefile = project_path / "Makefile"
            makefile_content = f'''# Makefile for {project_name}
# Generated by NES Manager

PROJECT_NAME = {project_name}
SOURCE_DIR = src
BUILD_DIR = build
RES_DIR = res
INCLUDE_DIR = include

# CC65 settings
CC65_HOME = {self.devkit_path}/cc65
NESLIB_HOME = {self.devkit_path}/neslib

CC = $(CC65_HOME)/bin/cc65
CA = $(CC65_HOME)/bin/ca65
LD = $(CC65_HOME)/bin/ld65

# Compiler flags
CFLAGS = -I$(NESLIB_HOME) -I$(INCLUDE_DIR) -O -t nes
AFLAGS = -t nes
LDFLAGS = -C nes.cfg -L$(CC65_HOME)/lib -L$(NESLIB_HOME)

# Source files
SOURCES = $(wildcard $(SOURCE_DIR)/*.c)
ASM_SOURCES = $(wildcard $(SOURCE_DIR)/*.s)
OBJECTS = $(SOURCES:$(SOURCE_DIR)/%.c=$(BUILD_DIR)/%.o) $(ASM_SOURCES:$(SOURCE_DIR)/%.s=$(BUILD_DIR)/%.o)

# Target files
ROM = $(BUILD_DIR)/$(PROJECT_NAME).nes

.PHONY: all clean run debug

all: $(ROM)

$(ROM): $(OBJECTS)
	@echo "Linking $(PROJECT_NAME)..."
	@mkdir -p $(BUILD_DIR)
	$(LD) $(LDFLAGS) -o $@ $^ nes.lib neslib.lib

$(BUILD_DIR)/%.o: $(SOURCE_DIR)/%.c
	@mkdir -p $(BUILD_DIR)
	@echo "Compiling $<..."
	$(CC) $(CFLAGS) -o $(BUILD_DIR)/$*.s $<
	$(CA) $(AFLAGS) -o $@ $(BUILD_DIR)/$*.s

$(BUILD_DIR)/%.o: $(SOURCE_DIR)/%.s
	@mkdir -p $(BUILD_DIR)
	@echo "Assembling $<..."
	$(CA) $(AFLAGS) -o $@ $<

clean:
	@echo "Cleaning build files..."
	@rm -rf $(BUILD_DIR)/*

run: $(ROM)
	@echo "Running $(PROJECT_NAME)..."
	@"{self.emulators_path}/FCEUX/fceux.exe" $(ROM)

debug: $(ROM)
	@echo "Debugging $(PROJECT_NAME)..."
	@"{self.emulators_path}/Mesen/Mesen.exe" $(ROM) --debug
'''
            makefile.write_text(makefile_content, encoding='utf-8')
            
            # Criar README
            readme = project_path / "README.md"
            readme_content = f'''# {project_name}

NES project created with NES Manager.

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

- `src/` - C and assembly source files
- `res/` - Graphics and audio resources
- `build/` - Compiled objects and ROM
- `include/` - Header files

## Resources

- [CC65 Documentation](https://cc65.github.io/)
- [NESLib Documentation](https://github.com/clbr/neslib)
- [NES Development Guide](https://www.nesdev.org/)
- [NESdev Wiki](https://www.nesdev.org/wiki/)
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
            "label": "Build NES ROM",
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
            "label": "Run NES Game",
            "type": "shell",
            "command": "make",
            "args": ["run"],
            "group": "test",
            "dependsOn": "Build NES ROM"
        },
        {
            "label": "Debug NES Game",
            "type": "shell",
            "command": "make",
            "args": ["debug"],
            "group": "test",
            "dependsOn": "Build NES ROM"
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
        "*.nes": "binary"
    }},
    "C_Cpp.default.includePath": [
        "{self.devkit_path}/neslib",
        "./include"
    ],
    "C_Cpp.default.defines": [
        "__NES__"
    ],
    "makefile.configureOnOpen": true
}}'''
            settings_json.write_text(settings_content, encoding='utf-8')
            
            self.logger.info(f"Template de projeto criado: {project_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na criação do template: {e}")
            return False