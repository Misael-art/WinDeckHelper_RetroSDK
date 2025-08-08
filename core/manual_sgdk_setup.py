#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Instalação Manual do SGDK
Este script configura o ambiente SGDK mesmo sem o download automático
"""

import os
import sys
from pathlib import Path
import subprocess
import json

def create_sgdk_structure():
    """Cria a estrutura básica de diretórios do SGDK"""
    base_path = Path("C:/Users/misae/RetroDevKits/retro_devkits/sgdk")
    
    # Estrutura de diretórios do SGDK
    directories = [
        "bin",
        "inc", 
        "lib",
        "src",
        "tools",
        "sample",
        "doc"
    ]
    
    for dir_name in directories:
        dir_path = base_path / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"✓ Diretório criado: {dir_path}")
    
    return base_path

def create_makefile_template(sgdk_path):
    """Cria um Makefile básico para projetos SGDK"""
    makefile_content = '''# SGDK Makefile Template
# Configuração básica para desenvolvimento Mega Drive/Genesis

# Configurações do SGDK
SGDK_PATH = C:/Users/misae/RetroDevKits/retro_devkits/sgdk
GCC_PATH = $(SGDK_PATH)/bin
INC_PATH = $(SGDK_PATH)/inc
LIB_PATH = $(SGDK_PATH)/lib

# Configurações do projeto
PROJECT_NAME = game
SRC_DIR = src
OBJ_DIR = obj
BIN_DIR = bin

# Compilador e flags
CC = $(GCC_PATH)/m68k-elf-gcc
AS = $(GCC_PATH)/m68k-elf-as
LD = $(GCC_PATH)/m68k-elf-ld
OBJCOPY = $(GCC_PATH)/m68k-elf-objcopy

CFLAGS = -m68000 -Wall -Wextra -std=c99 -ffreestanding
CFLAGS += -I$(INC_PATH) -I$(SRC_DIR)
LDFLAGS = -T $(SGDK_PATH)/md.ld -nostdlib
LIBS = -L$(LIB_PATH) -lmd

# Arquivos fonte
SRCS = $(wildcard $(SRC_DIR)/*.c)
OBJS = $(SRCS:$(SRC_DIR)/%.c=$(OBJ_DIR)/%.o)

# Regra principal
all: $(BIN_DIR)/$(PROJECT_NAME).bin

# Compilação do binário final
$(BIN_DIR)/$(PROJECT_NAME).bin: $(BIN_DIR)/$(PROJECT_NAME).elf
	@mkdir -p $(BIN_DIR)
	$(OBJCOPY) -O binary $< $@
	@echo "✓ ROM criada: $@"

# Link dos objetos
$(BIN_DIR)/$(PROJECT_NAME).elf: $(OBJS)
	@mkdir -p $(BIN_DIR)
	$(LD) $(LDFLAGS) -o $@ $^ $(LIBS)

# Compilação dos objetos
$(OBJ_DIR)/%.o: $(SRC_DIR)/%.c
	@mkdir -p $(OBJ_DIR)
	$(CC) $(CFLAGS) -c $< -o $@

# Limpeza
clean:
	rm -rf $(OBJ_DIR) $(BIN_DIR)

.PHONY: all clean
'''
    
    makefile_path = sgdk_path / "Makefile.template"
    with open(makefile_path, 'w', encoding='utf-8') as f:
        f.write(makefile_content)
    
    print(f"✓ Template Makefile criado: {makefile_path}")

def create_sample_project(sgdk_path):
    """Cria um projeto de exemplo básico"""
    sample_dir = sgdk_path / "sample" / "hello_world"
    sample_dir.mkdir(parents=True, exist_ok=True)
    
    # main.c básico
    main_c = '''#include "genesis.h"

int main()
{
    // Inicializa o sistema
    SYS_init();
    
    // Configura o plano de texto
    VDP_setTextPalette(PAL0);
    VDP_setTextPriority(TRUE);
    
    // Exibe mensagem
    VDP_drawText("Hello SGDK World!", 10, 10);
    VDP_drawText("Press START to continue", 8, 12);
    
    // Loop principal
    while(1)
    {
        // Lê o controle
        u16 joy = JOY_readJoypad(JOY_1);
        
        if(joy & BUTTON_START)
        {
            VDP_clearText();
            VDP_drawText("START pressed!", 12, 14);
        }
        
        // Aguarda próximo frame
        SYS_doVBlankProcess();
    }
    
    return 0;
}
'''
    
    with open(sample_dir / "main.c", 'w', encoding='utf-8') as f:
        f.write(main_c)
    
    print(f"✓ Projeto de exemplo criado: {sample_dir}")

def setup_environment_variables(sgdk_path):
    """Configura as variáveis de ambiente necessárias"""
    env_vars = {
        'SGDK_PATH': str(sgdk_path),
        'GDK': str(sgdk_path),
        'SGDK_BIN': str(sgdk_path / 'bin'),
        'SGDK_INC': str(sgdk_path / 'inc'),
        'SGDK_LIB': str(sgdk_path / 'lib')
    }
    
    # Cria script de configuração
    setup_script = sgdk_path / "setup_env.bat"
    with open(setup_script, 'w', encoding='utf-8') as f:
        f.write("@echo off\n")
        f.write("echo Configurando ambiente SGDK...\n")
        for var, value in env_vars.items():
            f.write(f"set {var}={value}\n")
        f.write("echo ✓ Variáveis de ambiente configuradas\n")
        f.write("echo Para usar o SGDK, execute este script antes de compilar\n")
    
    print(f"✓ Script de ambiente criado: {setup_script}")
    return env_vars

def create_installation_guide(sgdk_path):
    """Cria um guia de instalação manual"""
    guide_content = '''# Guia de Instalação Manual do SGDK

## Status Atual
✓ Estrutura de diretórios criada
✓ Templates e exemplos configurados
⚠️ Binários do SGDK precisam ser baixados manualmente

## Próximos Passos

### 1. Download Manual do SGDK
Visite: https://github.com/Stephane-D/SGDK/releases/latest
Baixe: sgdk211_win.7z (ou versão mais recente)

### 2. Extração
Extraia o conteúdo para: C:/Users/misae/RetroDevKits/retro_devkits/sgdk/

### 3. Estrutura Esperada
Após a extração, você deve ter:
```
sgdk/
├── bin/          # Executáveis (gcc, as, ld, etc.)
├── inc/          # Headers (.h)
├── lib/          # Bibliotecas (.a)
├── src/          # Código fonte do SGDK
├── tools/        # Ferramentas auxiliares
└── sample/       # Projetos de exemplo
```

### 4. Configuração do Ambiente
Execute: setup_env.bat

### 5. Teste
Compile o projeto de exemplo em sample/hello_world/

## Dependências Necessárias
- Microsoft Visual C++ Redistributable
- Java Runtime Environment (para algumas ferramentas)
- Make (já disponível em tools/make/)

## Troubleshooting
- Verifique se todos os arquivos foram extraídos corretamente
- Confirme que as variáveis de ambiente estão configuradas
- Teste com um projeto simples primeiro

## Suporte
Para mais informações, consulte:
- Documentação oficial do SGDK
- Fóruns da comunidade Mega Drive/Genesis
'''
    
    guide_path = sgdk_path / "INSTALLATION_GUIDE.md"
    with open(guide_path, 'w', encoding='utf-8') as f:
        f.write(guide_content)
    
    print(f"✓ Guia de instalação criado: {guide_path}")

def main():
    """Função principal"""
    print("=== Configuração Manual do SGDK ===")
    print("Preparando ambiente de desenvolvimento...\n")
    
    try:
        # Cria estrutura básica
        sgdk_path = create_sgdk_structure()
        
        # Configura templates e exemplos
        create_makefile_template(sgdk_path)
        create_sample_project(sgdk_path)
        
        # Configura ambiente
        env_vars = setup_environment_variables(sgdk_path)
        
        # Cria guia
        create_installation_guide(sgdk_path)
        
        print("\n=== Configuração Concluída ===")
        print(f"✓ SGDK configurado em: {sgdk_path}")
        print("\n⚠️  AÇÃO NECESSÁRIA:")
        print("1. Baixe manualmente o SGDK de: https://github.com/Stephane-D/SGDK/releases")
        print("2. Extraia para o diretório criado")
        print("3. Execute setup_env.bat para configurar o ambiente")
        print("\n📖 Consulte INSTALLATION_GUIDE.md para instruções detalhadas")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro durante a configuração: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
