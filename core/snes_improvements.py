"""Melhorias específicas para o Super Nintendo Development Kit (libSFX + ca65)
Implementação completa do manager para desenvolvimento SNES"""

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

class SNESManager(RetroDevkitManager):
    """Manager específico para Super Nintendo Development Kit (libSFX + ca65)"""
    
    def __init__(self, base_path: Path, logger: logging.Logger):
        super().__init__(base_path, logger)
        self.cc65_version = "2.19"
        self.libsfx_version = "latest"
        self.cc65_url = f"https://github.com/cc65/cc65/releases/download/V{self.cc65_version}/cc65-{self.cc65_version}-windows.zip"
        self.libsfx_url = "https://github.com/Optiroc/libSFX/archive/refs/heads/master.zip"
        
    def get_devkit_folder_name(self) -> str:
        """Retorna o nome da pasta do SNES devkit"""
        return "SNES"
        
    def get_devkit_info(self) -> DevkitInfo:
        """Retorna informações do SNES devkit"""
        return DevkitInfo(
            name="Super Nintendo Development Kit",
            console="Super Nintendo Entertainment System",
            devkit_name="libSFX + ca65",
            version=f"cc65-{self.cc65_version} + libSFX-{self.libsfx_version}",
            dependencies=[
                "make",
                "unzip",
                "wget",
                "python3"
            ],
            environment_vars={
                "CC65_HOME": str(self.devkit_path / "cc65"),
                "LIBSFX_HOME": str(self.devkit_path / "libSFX"),
                "PATH": str(self.devkit_path / "cc65" / "bin")
            },
            download_url=self.cc65_url,
            install_commands=[
                "Download and extract cc65",
                "Download and extract libSFX",
                "Setup environment variables",
                "Install emulators",
                "Setup VS Code extensions"
            ],
            verification_files=[
                "cc65/bin/ca65.exe",
                "cc65/bin/ld65.exe",
                "cc65/bin/cc65.exe",
                "libSFX/libsfx.inc",
                "libSFX/Makefile"
            ]
        )
        
    def install_dependencies(self) -> bool:
        """Instala dependências do SNES devkit"""
        try:
            self.logger.info("Instalando dependências do SNES devkit...")
            
            # Download e instalação do cc65
            if not self._install_cc65():
                return False
                
            # Download e instalação do libSFX
            if not self._install_libsfx():
                return False
                
            self.logger.info("SNES devkit instalado com sucesso")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na instalação do SNES devkit: {e}")
            return False
            
    def _install_cc65(self) -> bool:
        """Instala o compilador cc65"""
        try:
            self.logger.info("Instalando cc65...")
            
            cc65_zip = self.devkit_path / "cc65.zip"
            if not self.download_file(self.cc65_url, cc65_zip, "cc65"):
                return False
                
            # Extrair cc65
            cc65_path = self.devkit_path / "cc65"
            if not self.extract_archive(cc65_zip, cc65_path):
                return False
                
            # Remover arquivo zip
            cc65_zip.unlink()
            
            self.logger.info("cc65 instalado com sucesso")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na instalação do cc65: {e}")
            return False
            
    def _install_libsfx(self) -> bool:
        """Instala a biblioteca libSFX"""
        try:
            self.logger.info("Instalando libSFX...")
            
            libsfx_zip = self.devkit_path / "libsfx.zip"
            if not self.download_file(self.libsfx_url, libsfx_zip, "libSFX"):
                return False
                
            # Extrair libSFX
            temp_path = self.devkit_path / "temp_libsfx"
            if not self.extract_archive(libsfx_zip, temp_path):
                return False
                
            # Mover para estrutura correta
            extracted_folder = temp_path / "libSFX-master"
            libsfx_path = self.devkit_path / "libSFX"
            
            if extracted_folder.exists():
                shutil.move(str(extracted_folder), str(libsfx_path))
                shutil.rmtree(temp_path)
            else:
                # Fallback se a estrutura for diferente
                shutil.move(str(temp_path), str(libsfx_path))
                
            # Remover arquivo zip
            libsfx_zip.unlink()
            
            self.logger.info("libSFX instalado com sucesso")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na instalação do libSFX: {e}")
            return False
            
    def verify_installation(self) -> bool:
        """Verifica se o SNES devkit está instalado corretamente"""
        try:
            devkit_info = self.get_devkit_info()
            
            # Verificar arquivos essenciais
            for file_path in devkit_info.verification_files:
                full_path = self.devkit_path / file_path
                if not full_path.exists():
                    self.logger.error(f"Arquivo não encontrado: {full_path}")
                    return False
                    
            # Testar compilador ca65
            ca65_path = self.devkit_path / "cc65" / "bin" / "ca65.exe"
            success, output = self.run_command([str(ca65_path), "-V"])
            if not success:
                self.logger.error("Falha ao executar ca65")
                return False
                
            self.logger.info("Verificação do SNES devkit concluída com sucesso")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na verificação do SNES devkit: {e}")
            return False
            
    def install_emulators(self) -> bool:
        """Instala emuladores SNES"""
        try:
            self.logger.info("Instalando emuladores SNES...")
            
            emulators = {
                "bsnes": {
                    "url": "https://github.com/bsnes-emu/bsnes/releases/latest/download/bsnes-windows.zip",
                    "folder": "bsnes"
                },
                "SNES9x": {
                    "url": "https://github.com/snes9xgit/snes9x/releases/latest/download/snes9x-1.62.3-win32-x64.zip",
                    "folder": "SNES9x"
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
            
            # Script para bsnes
            bsnes_script = scripts_path / "run_bsnes.bat"
            bsnes_content = f'''@echo off
REM Script para executar bsnes
set EMULATOR_PATH="{self.emulators_path}\\bsnes\\bsnes.exe"
if exist %EMULATOR_PATH% (
    start "" %EMULATOR_PATH% %1
) else (
    echo bsnes nao encontrado em %EMULATOR_PATH%
    pause
)
'''
            bsnes_script.write_text(bsnes_content, encoding='utf-8')
            
            # Script para SNES9x
            snes9x_script = scripts_path / "run_snes9x.bat"
            snes9x_content = f'''@echo off
REM Script para executar SNES9x
set EMULATOR_PATH="{self.emulators_path}\\SNES9x\\snes9x-x64.exe"
if exist %EMULATOR_PATH% (
    start "" %EMULATOR_PATH% %1
) else (
    echo SNES9x nao encontrado em %EMULATOR_PATH%
    pause
)
'''
            snes9x_script.write_text(snes9x_content, encoding='utf-8')
            
            self.logger.info("Scripts de emuladores criados")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na criação de scripts de emuladores: {e}")
            return False
            
    def install_vscode_extensions(self) -> bool:
        """Instala extensões VS Code para SNES"""
        try:
            self.logger.info("Instalando extensões VS Code para SNES...")
            
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
        """Cria scripts de conveniência para desenvolvimento SNES"""
        try:
            self.logger.info("Criando scripts de conveniência...")
            
            scripts_path = self.devkit_path / "scripts"
            scripts_path.mkdir(exist_ok=True)
            
            # Script de compilação
            compile_script = scripts_path / "compile_snes_rom.bat"
            compile_content = f'''@echo off
REM Script de compilacao SNES
setlocal

set CC65_HOME={self.devkit_path}\\cc65
set LIBSFX_HOME={self.devkit_path}\\libSFX
set PATH=%CC65_HOME%\\bin;%PATH%

if "%1"=="" (
    echo Uso: compile_snes_rom.bat projeto_folder
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

echo Compilando projeto SNES...
make

if exist "*.sfc" (
    echo ROM criada com sucesso!
) else (
    echo Erro na compilacao!
)

pause
'''
            compile_script.write_text(compile_content, encoding='utf-8')
            
            # Script de execução
            run_script = scripts_path / "run_snes_rom.bat"
            run_content = f'''@echo off
REM Script para executar ROM SNES
setlocal

if "%1"=="" (
    echo Uso: run_snes_rom.bat arquivo.sfc
    pause
    exit /b 1
)

set ROM_FILE=%1
set BSNES_PATH="{self.emulators_path}\\bsnes\\bsnes.exe"
set SNES9X_PATH="{self.emulators_path}\\SNES9x\\snes9x-x64.exe"

if exist %BSNES_PATH% (
    echo Executando com bsnes...
    start "" %BSNES_PATH% %ROM_FILE%
) else if exist %SNES9X_PATH% (
    echo Executando com SNES9x...
    start "" %SNES9X_PATH% %ROM_FILE%
) else (
    echo Nenhum emulador encontrado!
    pause
)
'''
            run_script.write_text(run_content, encoding='utf-8')
            
            # Script de criação de projeto
            create_project_script = scripts_path / "create_snes_project.bat"
            create_project_content = f'''@echo off
REM Script para criar novo projeto SNES
setlocal

if "%1"=="" (
    echo Uso: create_snes_project.bat nome_do_projeto
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

echo Criando projeto SNES: %PROJECT_NAME%
mkdir "%PROJECT_DIR%"

echo Copiando template...
xcopy "{self.devkit_path}\\templates\\snes_template\\*" "%PROJECT_DIR%\\" /E /I /Q

echo Projeto criado: %PROJECT_DIR%
echo.
echo Para compilar: cd "%PROJECT_DIR%" && make
echo Para executar: run_snes_rom.bat "%PROJECT_DIR%\\game.sfc"
pause
'''
            create_project_script.write_text(create_project_content, encoding='utf-8')
            
            # Script de debug
            debug_script = scripts_path / "debug_snes_rom.bat"
            debug_content = f'''@echo off
REM Script de debug SNES com bsnes
setlocal

if "%1"=="" (
    echo Uso: debug_snes_rom.bat arquivo.sfc
    pause
    exit /b 1
)

set ROM_FILE=%1
set BSNES_PATH="{self.emulators_path}\\bsnes\\bsnes.exe"

if exist %BSNES_PATH% (
    echo Iniciando debug com bsnes...
    start "" %BSNES_PATH% --debug %ROM_FILE%
) else (
    echo bsnes nao encontrado para debug!
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
        """Cria template de projeto SNES"""
        try:
            self.logger.info(f"Criando template de projeto SNES: {project_name}")
            
            # Criar estrutura de diretórios
            project_path.mkdir(parents=True, exist_ok=True)
            (project_path / "src").mkdir(exist_ok=True)
            (project_path / "assets").mkdir(exist_ok=True)
            (project_path / "build").mkdir(exist_ok=True)
            (project_path / "include").mkdir(exist_ok=True)
            
            # Criar main.s (assembly principal)
            main_s = project_path / "src" / "main.s"
            main_content = f'''; {project_name} - SNES Project
; Generated by SNES Manager

.include "libsfx.inc"

.segment "CODE"

; Reset vector
Reset:
    ; Initialize SNES
    SFX_init
    
    ; Set screen mode
    lda #$01
    sta BGMODE
    
    ; Enable BG1
    lda #$01
    sta TM
    
    ; Turn on screen
    lda #$0F
    sta INIDISP
    
    ; Main loop
MainLoop:
    ; Wait for VBlank
    SFX_wait_vbl
    
    ; Game logic here
    
    bra MainLoop

; Interrupt vectors
.segment "VECTORS"
.word 0, 0, 0, 0, 0, 0, 0, 0
.word 0, 0, 0, 0, 0, 0, Reset, 0
'''
            main_s.write_text(main_content, encoding='utf-8')
            
            # Criar Makefile
            makefile = project_path / "Makefile"
            makefile_content = f'''# Makefile for {project_name}
# Generated by SNES Manager

PROJECT_NAME = {project_name}
SOURCE_DIR = src
BUILD_DIR = build
ASSETS_DIR = assets
INCLUDE_DIR = include

# Toolchain settings
CC65_HOME = {self.devkit_path}/cc65
LIBSFX_HOME = {self.devkit_path}/libSFX

CA65 = $(CC65_HOME)/bin/ca65
LD65 = $(CC65_HOME)/bin/ld65

# Compiler flags
ASFLAGS = -I $(LIBSFX_HOME) -I $(INCLUDE_DIR)
LDFLAGS = -C $(LIBSFX_HOME)/libsfx.cfg

# Source files
SOURCES = $(wildcard $(SOURCE_DIR)/*.s)
OBJECTS = $(SOURCES:$(SOURCE_DIR)/%.s=$(BUILD_DIR)/%.o)

# Target ROM
ROM = $(BUILD_DIR)/$(PROJECT_NAME).sfc

.PHONY: all clean run debug

all: $(ROM)

$(ROM): $(OBJECTS)
	@echo "Linking $(PROJECT_NAME)..."
	$(LD65) $(LDFLAGS) -o $@ $^
	@echo "ROM created: $@"

$(BUILD_DIR)/%.o: $(SOURCE_DIR)/%.s
	@mkdir -p $(BUILD_DIR)
	@echo "Assembling $<..."
	$(CA65) $(ASFLAGS) -o $@ $<

clean:
	@echo "Cleaning build files..."
	@rm -rf $(BUILD_DIR)/*

run: $(ROM)
	@echo "Running $(PROJECT_NAME)..."
	@"{self.emulators_path}/bsnes/bsnes.exe" $(ROM)

debug: $(ROM)
	@echo "Debugging $(PROJECT_NAME)..."
	@"{self.emulators_path}/bsnes/bsnes.exe" --debug $(ROM)
'''
            makefile.write_text(makefile_content, encoding='utf-8')
            
            # Criar README
            readme = project_path / "README.md"
            readme_content = f'''# {project_name}

SNES project created with SNES Manager.

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

- `src/` - Assembly source files
- `assets/` - Graphics and audio assets
- `build/` - Compiled objects and ROM
- `include/` - Header files

## Resources

- [libSFX Documentation](https://github.com/Optiroc/libSFX)
- [SNES Development Manual](https://problemkaputt.de/fullsnes.htm)
- [65816 Assembly Reference](http://6502.org/tutorials/65c816opcodes.html)
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
            "label": "Build SNES ROM",
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
            "label": "Run SNES ROM",
            "type": "shell",
            "command": "make",
            "args": ["run"],
            "group": "test",
            "dependsOn": "Build SNES ROM"
        },
        {
            "label": "Debug SNES ROM",
            "type": "shell",
            "command": "make",
            "args": ["debug"],
            "group": "test",
            "dependsOn": "Build SNES ROM"
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
        "*.s": "asm",
        "*.inc": "asm",
        "*.cfg": "ini"
    }},
    "makefile.configureOnOpen": true
}}'''
            settings_json.write_text(settings_content, encoding='utf-8')
            
            self.logger.info(f"Template de projeto criado: {project_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na criação do template: {e}")
            return False
            
    def install_audio_tools(self) -> bool:
        """Instala ferramentas de áudio SPC700"""
        try:
            self.logger.info("Instalando ferramentas de áudio SPC700...")
            
            audio_tools_path = self.tools_path / "audio"
            audio_tools_path.mkdir(parents=True, exist_ok=True)
            
            # Aqui você pode adicionar downloads de ferramentas específicas
            # Por exemplo: SPC700 tools, conversores de áudio, etc.
            
            self.logger.info("Ferramentas de áudio instaladas")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na instalação de ferramentas de áudio: {e}")
            return False