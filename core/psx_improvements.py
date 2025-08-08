"""Melhorias específicas para o PlayStation 1 Development Kit (PSn00bSDK)
Implementação completa do manager para desenvolvimento PSX"""

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

class PSXManager(RetroDevkitManager):
    """Manager específico para PlayStation 1 Development Kit (PSn00bSDK)"""
    
    def __init__(self, base_path: Path, logger: logging.Logger):
        super().__init__(base_path, logger)
        self.psn00bsdk_version = "latest"
        self.psn00bsdk_url = "https://github.com/Lameguy64/PSn00bSDK/releases/latest/download/psn00bsdk-windows.zip"
        self.mkpsxiso_url = "https://github.com/Lameguy64/mkpsxiso/releases/latest/download/mkpsxiso-windows.zip"
        
    def get_devkit_folder_name(self) -> str:
        """Retorna o nome da pasta do PSX devkit"""
        return "PSX"
        
    def get_devkit_info(self) -> DevkitInfo:
        """Retorna informações do PSX devkit"""
        return DevkitInfo(
            name="PlayStation 1 Development Kit",
            console="Sony PlayStation 1",
            devkit_name="PSn00bSDK",
            version=self.psn00bsdk_version,
            dependencies=[
                "make",
                "unzip",
                "wget",
                "cmake",
                "gcc"
            ],
            environment_vars={
                "PSN00BSDK_HOME": str(self.devkit_path / "PSn00bSDK"),
                "MKPSXISO_HOME": str(self.devkit_path / "mkpsxiso"),
                "PATH": str(self.devkit_path / "PSn00bSDK" / "bin")
            },
            download_url=self.psn00bsdk_url,
            install_commands=[
                "Download and extract PSn00bSDK",
                "Download and extract mkpsxiso",
                "Setup environment variables",
                "Install emulators",
                "Setup VS Code extensions"
            ],
            verification_files=[
                "PSn00bSDK/bin/mipsel-none-elf-gcc.exe",
                "PSn00bSDK/bin/mipsel-none-elf-ld.exe",
                "PSn00bSDK/include/psxapi.h",
                "PSn00bSDK/include/psxgpu.h",
                "mkpsxiso/mkpsxiso.exe"
            ]
        )
        
    def install_dependencies(self) -> bool:
        """Instala dependências do PSX devkit"""
        try:
            self.logger.info("Instalando dependências do PSX devkit...")
            
            # Download e instalação do PSn00bSDK
            if not self._install_psn00bsdk():
                return False
                
            # Download e instalação do mkpsxiso
            if not self._install_mkpsxiso():
                return False
                
            # Instalar ferramentas adicionais
            if not self._install_additional_tools():
                self.logger.warning("Falha na instalação de ferramentas adicionais")
                
            self.logger.info("PSX devkit instalado com sucesso")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na instalação do PSX devkit: {e}")
            return False
            
    def _install_psn00bsdk(self) -> bool:
        """Instala o PSn00bSDK"""
        try:
            self.logger.info("Instalando PSn00bSDK...")
            
            sdk_zip = self.devkit_path / "psn00bsdk.zip"
            if not self.download_file(self.psn00bsdk_url, sdk_zip, "PSn00bSDK"):
                return False
                
            # Extrair PSn00bSDK
            sdk_path = self.devkit_path / "PSn00bSDK"
            if not self.extract_archive(sdk_zip, sdk_path):
                return False
                
            # Remover arquivo zip
            sdk_zip.unlink()
            
            self.logger.info("PSn00bSDK instalado com sucesso")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na instalação do PSn00bSDK: {e}")
            return False
            
    def _install_mkpsxiso(self) -> bool:
        """Instala o mkpsxiso"""
        try:
            self.logger.info("Instalando mkpsxiso...")
            
            mkpsxiso_zip = self.devkit_path / "mkpsxiso.zip"
            if not self.download_file(self.mkpsxiso_url, mkpsxiso_zip, "mkpsxiso"):
                return False
                
            # Extrair mkpsxiso
            mkpsxiso_path = self.devkit_path / "mkpsxiso"
            if not self.extract_archive(mkpsxiso_zip, mkpsxiso_path):
                return False
                
            # Remover arquivo zip
            mkpsxiso_zip.unlink()
            
            self.logger.info("mkpsxiso instalado com sucesso")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na instalação do mkpsxiso: {e}")
            return False
            
    def _install_additional_tools(self) -> bool:
        """Instala ferramentas adicionais para PSX"""
        try:
            self.logger.info("Instalando ferramentas adicionais...")
            
            tools_path = self.tools_path
            tools_path.mkdir(parents=True, exist_ok=True)
            
            # Aqui você pode adicionar downloads de ferramentas específicas
            # Por exemplo: img2tim, wav2vag, etc.
            
            # Criar scripts de conversão básicos
            self._create_conversion_scripts()
            
            self.logger.info("Ferramentas adicionais instaladas")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na instalação de ferramentas adicionais: {e}")
            return False
            
    def _create_conversion_scripts(self) -> bool:
        """Cria scripts de conversão de assets"""
        try:
            scripts_path = self.devkit_path / "scripts"
            scripts_path.mkdir(exist_ok=True)
            
            # Script para conversão de imagens (placeholder)
            img_script = scripts_path / "convert_image.bat"
            img_content = '''@echo off
REM Script para conversao de imagens para TIM
echo Conversao de imagens ainda nao implementada
echo Use img2tim manualmente por enquanto
pause
'''
            img_script.write_text(img_content, encoding='utf-8')
            
            # Script para conversão de áudio (placeholder)
            audio_script = scripts_path / "convert_audio.bat"
            audio_content = '''@echo off
REM Script para conversao de audio para VAG
echo Conversao de audio ainda nao implementada
echo Use wav2vag manualmente por enquanto
pause
'''
            audio_script.write_text(audio_content, encoding='utf-8')
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na criação de scripts de conversão: {e}")
            return False
            
    def verify_installation(self) -> bool:
        """Verifica se o PSX devkit está instalado corretamente"""
        try:
            devkit_info = self.get_devkit_info()
            
            # Verificar arquivos essenciais
            for file_path in devkit_info.verification_files:
                full_path = self.devkit_path / file_path
                if not full_path.exists():
                    self.logger.error(f"Arquivo não encontrado: {full_path}")
                    return False
                    
            # Testar compilador
            gcc_path = self.devkit_path / "PSn00bSDK" / "bin" / "mipsel-none-elf-gcc.exe"
            success, output = self.run_command([str(gcc_path), "--version"])
            if not success:
                self.logger.error("Falha ao executar mipsel-none-elf-gcc")
                return False
                
            # Testar mkpsxiso
            mkpsxiso_path = self.devkit_path / "mkpsxiso" / "mkpsxiso.exe"
            success, output = self.run_command([str(mkpsxiso_path), "-h"])
            if not success:
                self.logger.error("Falha ao executar mkpsxiso")
                return False
                
            self.logger.info("Verificação do PSX devkit concluída com sucesso")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na verificação do PSX devkit: {e}")
            return False
            
    def install_emulators(self) -> bool:
        """Instala emuladores PSX"""
        try:
            self.logger.info("Instalando emuladores PSX...")
            
            emulators = {
                "DuckStation": {
                    "url": "https://github.com/stenzek/duckstation/releases/latest/download/duckstation-windows-x64-release.zip",
                    "folder": "DuckStation"
                },
                "ePSXe": {
                    "url": "http://www.epsxe.com/files/ePSXe205.zip",
                    "folder": "ePSXe"
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
            
            # Script para DuckStation
            duckstation_script = scripts_path / "run_duckstation.bat"
            duckstation_content = f'''@echo off
REM Script para executar DuckStation
set EMULATOR_PATH="{self.emulators_path}\\DuckStation\\duckstation-qt-x64-ReleaseLTCG.exe"
if exist %EMULATOR_PATH% (
    start "" %EMULATOR_PATH% %1
) else (
    echo DuckStation nao encontrado em %EMULATOR_PATH%
    pause
)
'''
            duckstation_script.write_text(duckstation_content, encoding='utf-8')
            
            # Script para ePSXe
            epsxe_script = scripts_path / "run_epsxe.bat"
            epsxe_content = f'''@echo off
REM Script para executar ePSXe
set EMULATOR_PATH="{self.emulators_path}\\ePSXe\\ePSXe.exe"
if exist %EMULATOR_PATH% (
    start "" %EMULATOR_PATH% %1
) else (
    echo ePSXe nao encontrado em %EMULATOR_PATH%
    pause
)
'''
            epsxe_script.write_text(epsxe_content, encoding='utf-8')
            
            self.logger.info("Scripts de emuladores criados")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na criação de scripts de emuladores: {e}")
            return False
            
    def install_vscode_extensions(self) -> bool:
        """Instala extensões VS Code para PSX"""
        try:
            self.logger.info("Instalando extensões VS Code para PSX...")
            
            extensions = [
                "ms-vscode.cpptools",  # C/C++ support
                "ms-vscode.makefile-tools",  # Makefile support
                "ms-vscode.cmake-tools",  # CMake support
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
        """Cria scripts de conveniência para desenvolvimento PSX"""
        try:
            self.logger.info("Criando scripts de conveniência...")
            
            scripts_path = self.devkit_path / "scripts"
            scripts_path.mkdir(exist_ok=True)
            
            # Script de compilação
            compile_script = scripts_path / "compile_psx_iso.bat"
            compile_content = f'''@echo off
REM Script de compilacao PSX
setlocal

set PSN00BSDK_HOME={self.devkit_path}\\PSn00bSDK
set MKPSXISO_HOME={self.devkit_path}\\mkpsxiso
set PATH=%PSN00BSDK_HOME%\\bin;%MKPSXISO_HOME%;%PATH%

if "%1"=="" (
    echo Uso: compile_psx_iso.bat projeto_folder
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

echo Compilando projeto PSX...
make

if exist "*.bin" (
    echo Criando ISO...
    mkpsxiso project.xml
    if exist "*.iso" (
        echo ISO criada com sucesso!
    ) else (
        echo Erro na criacao do ISO!
    )
) else (
    echo Erro na compilacao!
)

pause
'''
            compile_script.write_text(compile_content, encoding='utf-8')
            
            # Script de execução
            run_script = scripts_path / "run_psx_game.bat"
            run_content = f'''@echo off
REM Script para executar jogo PSX
setlocal

if "%1"=="" (
    echo Uso: run_psx_game.bat arquivo.iso
    pause
    exit /b 1
)

set ISO_FILE=%1
set DUCKSTATION_PATH="{self.emulators_path}\\DuckStation\\duckstation-qt-x64-ReleaseLTCG.exe"
set EPSXE_PATH="{self.emulators_path}\\ePSXe\\ePSXe.exe"

if exist %DUCKSTATION_PATH% (
    echo Executando com DuckStation...
    start "" %DUCKSTATION_PATH% %ISO_FILE%
) else if exist %EPSXE_PATH% (
    echo Executando com ePSXe...
    start "" %EPSXE_PATH% %ISO_FILE%
) else (
    echo Nenhum emulador encontrado!
    pause
)
'''
            run_script.write_text(run_content, encoding='utf-8')
            
            # Script de debug
            debug_script = scripts_path / "debug_psx_game.bat"
            debug_content = f'''@echo off
REM Script de debug PSX com DuckStation
setlocal

if "%1"=="" (
    echo Uso: debug_psx_game.bat arquivo.iso
    pause
    exit /b 1
)

set ISO_FILE=%1
set DUCKSTATION_PATH="{self.emulators_path}\\DuckStation\\duckstation-qt-x64-ReleaseLTCG.exe"

if exist %DUCKSTATION_PATH% (
    echo Iniciando debug com DuckStation...
    start "" %DUCKSTATION_PATH% -debug %ISO_FILE%
) else (
    echo DuckStation nao encontrado para debug!
    pause
)
'''
            debug_script.write_text(debug_content, encoding='utf-8')
            
            # Script de criação de projeto
            create_project_script = scripts_path / "create_psx_project.bat"
            create_project_content = f'''@echo off
REM Script para criar novo projeto PSX
setlocal

if "%1"=="" (
    echo Uso: create_psx_project.bat nome_do_projeto
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

echo Criando projeto PSX: %PROJECT_NAME%
mkdir "%PROJECT_DIR%"

echo Copiando template...
xcopy "{self.devkit_path}\\templates\\psx_template\\*" "%PROJECT_DIR%\\" /E /I /Q

echo Projeto criado: %PROJECT_DIR%
echo.
echo Para compilar: cd "%PROJECT_DIR%" && make
echo Para executar: run_psx_game.bat "%PROJECT_DIR%\\game.iso"
pause
'''
            create_project_script.write_text(create_project_content, encoding='utf-8')
            
            self.logger.info("Scripts de conveniência criados")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na criação de scripts: {e}")
            return False
            
    def create_project_template(self, project_name: str, project_path: Path) -> bool:
        """Cria template de projeto PSX"""
        try:
            self.logger.info(f"Criando template de projeto PSX: {project_name}")
            
            # Criar estrutura de diretórios
            project_path.mkdir(parents=True, exist_ok=True)
            (project_path / "src").mkdir(exist_ok=True)
            (project_path / "assets").mkdir(exist_ok=True)
            (project_path / "build").mkdir(exist_ok=True)
            (project_path / "include").mkdir(exist_ok=True)
            
            # Criar main.c
            main_c = project_path / "src" / "main.c"
            main_content = f'''// {project_name} - PlayStation 1 Project
// Generated by PSX Manager

#include <psxapi.h>
#include <psxgpu.h>
#include <psxpad.h>
#include <stdio.h>

// Screen resolution
#define SCREEN_WIDTH  320
#define SCREEN_HEIGHT 240

// Display and draw environments
DISPENV disp;
DRAWENV draw;

// Framebuffers
char pribuff[2][32768];
char *nextpri;

void init_graphics() {{
    // Reset GPU
    ResetGraph(0);
    
    // Set display environment
    SetDefDispEnv(&disp, 0, 0, SCREEN_WIDTH, SCREEN_HEIGHT);
    SetDefDrawEnv(&draw, 0, 240, SCREEN_WIDTH, SCREEN_HEIGHT);
    
    // Set background color
    draw.isbg = 1;
    draw.r0 = 64;
    draw.g0 = 128;
    draw.b0 = 255;
    
    // Apply environments
    PutDispEnv(&disp);
    PutDrawEnv(&draw);
    
    // Initialize primitive buffer
    nextpri = pribuff[0];
    
    // Enable display
    SetDispMask(1);
}}

void init_controllers() {{
    // Initialize controller
    InitPAD(pribuff[0], 34, pribuff[1], 34);
    StartPAD();
    ChangeClearPAD(1);
}}

int main() {{
    // Initialize systems
    init_graphics();
    init_controllers();
    
    printf("\\n{project_name} - PSX Game\\n");
    printf("Press START to exit\\n");
    
    // Main game loop
    while(1) {{
        // Read controller
        PADTYPE *pad = (PADTYPE*)pribuff[0];
        
        // Check for START button
        if(!(pad->btn & PAD_START)) {{
            break;
        }}
        
        // Wait for VSync
        VSync(0);
        
        // Swap buffers
        nextpri = pribuff[GsGetActiveBuff()];
        
        // Game logic here
    }}
    
    return 0;
}}
'''
            main_c.write_text(main_content, encoding='utf-8')
            
            # Criar Makefile
            makefile = project_path / "Makefile"
            makefile_content = f'''# Makefile for {project_name}
# Generated by PSX Manager

PROJECT_NAME = {project_name}
SOURCE_DIR = src
BUILD_DIR = build
ASSETS_DIR = assets
INCLUDE_DIR = include

# PSn00bSDK settings
PSN00BSDK_HOME = {self.devkit_path}/PSn00bSDK
MKPSXISO_HOME = {self.devkit_path}/mkpsxiso

CC = $(PSN00BSDK_HOME)/bin/mipsel-none-elf-gcc
LD = $(PSN00BSDK_HOME)/bin/mipsel-none-elf-ld
MKPSXISO = $(MKPSXISO_HOME)/mkpsxiso

# Compiler flags
CFLAGS = -I$(PSN00BSDK_HOME)/include -I$(INCLUDE_DIR) -O2 -G0 -mgp32 -mfp32
LDFLAGS = -L$(PSN00BSDK_HOME)/lib -lpsxapi -lpsxgpu -lpsxpad -lpsxspu -lpsxcd

# Source files
SOURCES = $(wildcard $(SOURCE_DIR)/*.c)
OBJECTS = $(SOURCES:$(SOURCE_DIR)/%.c=$(BUILD_DIR)/%.o)

# Target executable
ELF = $(BUILD_DIR)/$(PROJECT_NAME).elf
BIN = $(BUILD_DIR)/$(PROJECT_NAME).bin
ISO = $(BUILD_DIR)/$(PROJECT_NAME).iso

.PHONY: all clean run debug iso

all: $(BIN)

iso: $(ISO)

$(ISO): $(BIN) project.xml
	@echo "Creating ISO..."
	$(MKPSXISO) project.xml
	@mv $(PROJECT_NAME).iso $(ISO)

$(BIN): $(ELF)
	@echo "Converting to binary..."
	$(PSN00BSDK_HOME)/bin/mipsel-none-elf-objcopy -O binary $< $@

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
	@rm -f *.iso

run: $(ISO)
	@echo "Running $(PROJECT_NAME)..."
	@"{self.emulators_path}/DuckStation/duckstation-qt-x64-ReleaseLTCG.exe" $(ISO)

debug: $(ISO)
	@echo "Debugging $(PROJECT_NAME)..."
	@"{self.emulators_path}/DuckStation/duckstation-qt-x64-ReleaseLTCG.exe" -debug $(ISO)
'''
            makefile.write_text(makefile_content, encoding='utf-8')
            
            # Criar project.xml para mkpsxiso
            project_xml = project_path / "project.xml"
            project_xml_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<iso_project image_name="{project_name}.iso" cue_sheet="{project_name}.cue">
    <track type="data">
        <identifiers
            system         ="PLAYSTATION"
            application    ="{project_name.upper()}"
            volume         ="{project_name.upper()}"
            volume_set     ="{project_name.upper()}"
            publisher      ="HOMEBREW"
            data_preparer  ="PSX_MANAGER"
        />
        <license file="$(PSN00BSDK_HOME)/share/licenses/infousa.dat"/>
        <file name="PSX.EXE" type="data" source="build/{project_name}.bin"/>
        <dummy sectors="1024"/>
    </track>
</iso_project>
'''
            project_xml.write_text(project_xml_content, encoding='utf-8')
            
            # Criar README
            readme = project_path / "README.md"
            readme_content = f'''# {project_name}

PlayStation 1 project created with PSX Manager.

## Building

```bash
make
```

## Creating ISO

```bash
make iso
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
- `project.xml` - ISO creation configuration

## Resources

- [PSn00bSDK Documentation](https://github.com/Lameguy64/PSn00bSDK)
- [PlayStation 1 Programming Guide](http://psx.arthus.net/sdk/Psy-Q/DOCS/)
- [mkpsxiso Documentation](https://github.com/Lameguy64/mkpsxiso)
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
            "label": "Build PSX Binary",
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
            "label": "Build PSX ISO",
            "type": "shell",
            "command": "make",
            "args": ["iso"],
            "group": "build",
            "dependsOn": "Build PSX Binary"
        },
        {
            "label": "Run PSX Game",
            "type": "shell",
            "command": "make",
            "args": ["run"],
            "group": "test",
            "dependsOn": "Build PSX ISO"
        },
        {
            "label": "Debug PSX Game",
            "type": "shell",
            "command": "make",
            "args": ["debug"],
            "group": "test",
            "dependsOn": "Build PSX ISO"
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
        "{self.devkit_path}/PSn00bSDK/include",
        "./include"
    ],
    "C_Cpp.default.defines": [
        "__PSX__"
    ],
    "makefile.configureOnOpen": true
}}'''
            settings_json.write_text(settings_content, encoding='utf-8')
            
            self.logger.info(f"Template de projeto criado: {project_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na criação do template: {e}")
            return False