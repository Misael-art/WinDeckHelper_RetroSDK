# Guia Completo dos Retro Development Kits

## Índice

1. [Introdução](#introdução)
2. [Instalação e Configuração](#instalação-e-configuração)
3. [Devkits Suportados](#devkits-suportados)
4. [Emuladores Integrados](#emuladores-integrados)
5. [Fluxo de Desenvolvimento](#fluxo-de-desenvolvimento)
6. [Scripts de Automação](#scripts-de-automação)
7. [Configuração do VS Code](#configuração-do-vs-code)
8. [Solução de Problemas](#solução-de-problemas)
9. [API e Extensibilidade](#api-e-extensibilidade)
10. [Exemplos Práticos](#exemplos-práticos)

## Introdução

O sistema de Retro Development Kits do Environment Development é uma solução completa para desenvolvimento de jogos retro, oferecendo suporte integrado para 8 plataformas clássicas com mais de 20 emuladores e 40+ scripts de automação.

### Características Principais

- **8 Devkits Suportados**: Game Boy, SNES, PlayStation, Nintendo 64, Game Boy Advance, Neo Geo, NES e Sega Saturn
- **20+ Emuladores Integrados**: Configuração automática dos melhores emuladores para cada plataforma
- **40+ Scripts de Automação**: Compilação, execução, debug e conversão de assets
- **Integração com VS Code**: Extensões, snippets e configurações otimizadas
- **Detecção Automática**: Identifica devkits já instalados no sistema
- **Configuração Unificada**: Gerenciamento centralizado de todas as ferramentas
- **Logging Avançado**: Sistema de logs detalhado para debug e monitoramento

## Pré-requisitos do Sistema

Antes de instalar qualquer devkit, certifique-se de que seu sistema possui as dependências necessárias.

### Windows

#### Dependências Obrigatórias

1. **Java Development Kit (JDK 11+)**
   ```powershell
   # Via Chocolatey (recomendado)
   choco install openjdk11
   
   # Ou baixar manualmente de:
   # https://adoptium.net/temurin/releases/
   ```

2. **Make**
   ```powershell
   # Via Chocolatey
   choco install make
   
   # Ou via Visual Studio Build Tools
   choco install visualstudio2022buildtools
   ```

3. **7-Zip**
   ```powershell
   # Via Chocolatey
   choco install 7zip
   
   # Ou baixar de: https://www.7-zip.org/
   ```

4. **wget**
   ```powershell
   # Via Chocolatey
   choco install wget
   
   # Ou usar PowerShell nativo (já incluído no Windows 10+)
   ```

#### Dependências Opcionais

1. **Git**
   ```powershell
   choco install git
   ```

2. **Visual Studio Code**
   ```powershell
   choco install vscode
   ```

3. **Chocolatey** (para instalação automática de dependências)
   ```powershell
   # Executar como Administrador
   Set-ExecutionPolicy Bypass -Scope Process -Force
   [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
   iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
   ```

### Linux (Ubuntu/Debian)

#### Dependências Obrigatórias

1. **Java Development Kit (JDK 11+)**
   ```bash
   sudo apt update
   sudo apt install openjdk-11-jdk
   
   # Verificar instalação
   java -version
   javac -version
   ```

2. **Build Essential (inclui make, gcc)**
   ```bash
   sudo apt install build-essential
   ```

3. **7-Zip**
   ```bash
   sudo apt install p7zip-full
   ```

4. **wget e unzip**
   ```bash
   sudo apt install wget unzip
   ```

#### Dependências Opcionais

1. **Git**
   ```bash
   sudo apt install git
   ```

2. **Visual Studio Code**
   ```bash
   # Via snap
   sudo snap install code --classic
   
   # Ou via repositório oficial
   wget -qO- https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > packages.microsoft.gpg
   sudo install -o root -g root -m 644 packages.microsoft.gpg /etc/apt/trusted.gpg.d/
   sudo sh -c 'echo "deb [arch=amd64,arm64,armhf signed-by=/etc/apt/trusted.gpg.d/packages.microsoft.gpg] https://packages.microsoft.com/repos/code stable main" > /etc/apt/sources.list.d/vscode.list'
   sudo apt update
   sudo apt install code
   ```

### Linux (CentOS/RHEL/Fedora)

#### Dependências Obrigatórias

1. **Java Development Kit (JDK 11+)**
   ```bash
   # CentOS/RHEL
   sudo yum install java-11-openjdk-devel
   
   # Fedora
   sudo dnf install java-11-openjdk-devel
   ```

2. **Development Tools**
   ```bash
   # CentOS/RHEL
   sudo yum groupinstall "Development Tools"
   
   # Fedora
   sudo dnf groupinstall "Development Tools"
   ```

3. **7-Zip**
   ```bash
   # CentOS/RHEL (via EPEL)
   sudo yum install epel-release
   sudo yum install p7zip
   
   # Fedora
   sudo dnf install p7zip
   ```

4. **wget**
   ```bash
   # CentOS/RHEL
   sudo yum install wget
   
   # Fedora
   sudo dnf install wget
   ```

### Verificação de Pré-requisitos

Após instalar as dependências, verifique se estão funcionando:

```bash
# Verificar Java
java -version
javac -version

# Verificar Make
make --version

# Verificar 7-Zip
7z

# Verificar wget
wget --version
```

### Solução de Problemas Comuns

#### Java não encontrado
- **Windows**: Certifique-se de que `JAVA_HOME` está configurado e `%JAVA_HOME%\bin` está no PATH
- **Linux**: Execute `sudo update-alternatives --config java` para configurar a versão padrão

#### Make não encontrado no Windows
- Instale Visual Studio Build Tools ou use `mingw-w64`
- Alternativamente, use WSL (Windows Subsystem for Linux)

#### 7-Zip não encontrado
- **Windows**: Adicione `C:\Program Files\7-Zip` ao PATH
- **Linux**: Instale `p7zip-full` (Ubuntu) ou `p7zip` (CentOS/Fedora)

#### Permissões no Linux
- Execute comandos de instalação com `sudo`
- Para desenvolvimento, evite usar `sudo` - configure permissões adequadas

## Instalação e Configuração

### Instalação Automática

```python
from core.retro_devkit_manager import RetroDevkitManager

# Inicializar o gerenciador
manager = RetroDevkitManager()

# Instalar um devkit específico
manager.install_devkit('gbdk')  # Game Boy Development Kit
manager.install_devkit('snes')  # SNES Development Kit

# Instalar todos os devkits
for devkit in manager.get_supported_devkits():
    manager.install_devkit(devkit)
```

### Instalação via Component Manager

```python
from core.component_manager import ComponentManager

# Inicializar o gerenciador de componentes
component_manager = ComponentManager()

# Instalar componentes de retro devkits
component_manager.install_component('gbdk')
component_manager.install_component('snes_devkit')
component_manager.install_component('psx_devkit')
```

### Verificação da Instalação

```python
from core.retro_devkit_detector import RetroDevkitDetector

# Detectar devkits instalados
detector = RetroDevkitDetector()
results = detector.detect_all_devkits()

# Gerar relatório
print(detector.generate_summary())
```

## Devkits Suportados

### 1. Game Boy Development Kit (GBDK)

**Descrição**: Kit de desenvolvimento para Game Boy e Game Boy Color

**Ferramentas Incluídas**:
- GBDK-2020 (compilador C)
- RGBDS (assembler)
- Ferramentas de conversão de sprites e tiles

**Emuladores**:
- BGB (Windows)
- SameBoy (multiplataforma)
- Gambatte (libretro)

**Exemplo de Projeto**:
```c
#include <gb/gb.h>
#include <stdio.h>

void main() {
    printf("Hello Game Boy!");
    while(1) {
        wait_vbl_done();
    }
}
```

### 2. SNES Development Kit

**Descrição**: Kit de desenvolvimento para Super Nintendo

**Ferramentas Incluídas**:
- CC65 (compilador C)
- CA65 (assembler)
- Ferramentas de conversão de gráficos

**Emuladores**:
- BSNES (alta precisão)
- SNES9x (performance)
- Mesen-S (debug)

### 3. PlayStation Development Kit (PSn00bSDK)

**Descrição**: SDK moderno para PlayStation 1

**Ferramentas Incluídas**:
- PSn00bSDK (SDK completo)
- MIPS GCC toolchain
- Ferramentas de conversão de assets

**Emuladores**:
- DuckStation (moderno)
- PCSX-Redux (desenvolvimento)
- Mednafen (precisão)

### 4. Nintendo 64 Development Kit (libdragon)

**Descrição**: SDK open-source para Nintendo 64

**Ferramentas Incluídas**:
- libdragon (SDK)
- MIPS64 GCC toolchain
- Ferramentas de conversão de texturas

**Emuladores**:
- Project64 (compatibilidade)
- Mupen64Plus (multiplataforma)
- Simple64 (moderno)

### 5. Game Boy Advance Development Kit (devkitARM)

**Descrição**: Kit de desenvolvimento para Game Boy Advance

**Ferramentas Incluídas**:
- devkitARM (toolchain)
- libgba (biblioteca)
- Ferramentas de conversão de assets

**Emuladores**:
- mGBA (precisão)
- VBA-M (compatibilidade)
- NanoBoyAdvance (moderno)

### 6. Neo Geo Development Kit (NGDevKit)

**Descrição**: Kit de desenvolvimento para Neo Geo

**Ferramentas Incluídas**:
- NGDevKit (toolchain)
- M68K GCC
- Ferramentas de conversão de sprites

**Emuladores**:
- FinalBurn Neo (arcade)
- MAME (precisão)
- NeoRAGEx (clássico)

### 7. NES Development Kit (CC65)

**Descrição**: Kit de desenvolvimento para Nintendo Entertainment System

**Ferramentas Incluídas**:
- CC65 (compilador C)
- CA65 (assembler)
- Ferramentas de conversão CHR

**Emuladores**:
- FCEUX (desenvolvimento)
- Nestopia (precisão)
- Mesen (debug avançado)

### 8. Sega Saturn Development Kit (Jo-Engine + Yaul)

**Descrição**: Kits de desenvolvimento para Sega Saturn

**Ferramentas Incluídas**:
- Jo-Engine (engine C)
- Yaul (SDK baixo nível)
- SH-2 toolchain

**Emuladores**:
- Mednafen (precisão)
- SSF (compatibilidade)
- Kronos (moderno)

## Emuladores Integrados

### Configuração Automática

Todos os emuladores são configurados automaticamente com:
- Scripts de execução personalizados
- Configurações otimizadas para desenvolvimento
- Integração com o sistema de build
- Suporte a debugging quando disponível

### Exemplo de Uso

```python
# Executar ROM no emulador padrão
manager.run_rom('game.gb', 'gbdk')

# Executar em emulador específico
manager.run_rom('game.sfc', 'snes', emulator='bsnes')

# Debug com emulador
manager.debug_rom('game.nes', 'nes', emulator='mesen')
```

## Fluxo de Desenvolvimento

### 1. Criação de Projeto

```bash
# Criar novo projeto Game Boy
python -m core.gbdk_improvements create_project my_gb_game

# Criar novo projeto SNES
python -m core.snes_improvements create_project my_snes_game
```

### 2. Desenvolvimento

- Editar código no VS Code com extensões otimizadas
- Usar snippets específicos da plataforma
- Aproveitar syntax highlighting e IntelliSense

### 3. Compilação

```bash
# Compilar projeto
./scripts/build.bat  # Windows
./scripts/build.sh   # Linux/macOS

# Compilação com debug
./scripts/build_debug.bat
```

### 4. Teste e Debug

```bash
# Executar no emulador
./scripts/run.bat

# Debug no emulador
./scripts/debug.bat
```

### 5. Conversão de Assets

```bash
# Converter sprites (Game Boy)
./scripts/convert_sprites.bat sprites/

# Converter música (NES)
./scripts/convert_music.bat music/song.txt
```

## Scripts de Automação

### Scripts de Build

**build.bat/sh**: Compilação padrão do projeto
```batch
@echo off
echo Compilando projeto...
lcc -Wa-l -Wl-m -Wl-j -DUSE_SFR_FOR_REG -c -o main.o main.c
lcc -Wa-l -Wl-m -Wl-j -DUSE_SFR_FOR_REG -o game.gb main.o
echo Compilacao concluida!
```

**build_debug.bat/sh**: Compilação com símbolos de debug
```batch
@echo off
echo Compilando com debug...
lcc -Wa-l -Wl-m -Wl-j -DUSE_SFR_FOR_REG -debug -c -o main.o main.c
lcc -Wa-l -Wl-m -Wl-j -DUSE_SFR_FOR_REG -debug -o game.gb main.o
echo Compilacao com debug concluida!
```

### Scripts de Execução

**run.bat/sh**: Executa ROM no emulador padrão
```batch
@echo off
if exist game.gb (
    start "" "C:\Emulators\BGB\bgb.exe" game.gb
) else (
    echo ROM nao encontrada! Execute build.bat primeiro.
)
```

**debug.bat/sh**: Executa ROM em modo debug
```batch
@echo off
if exist game.gb (
    start "" "C:\Emulators\Mesen\Mesen.exe" game.gb
) else (
    echo ROM nao encontrada! Execute build_debug.bat primeiro.
)
```

### Scripts de Conversão

**convert_sprites.bat/sh**: Converte sprites para formato da plataforma
**convert_music.bat/sh**: Converte música para formato da plataforma
**convert_maps.bat/sh**: Converte mapas/tiles para formato da plataforma

## Configuração do VS Code

### Extensões Instaladas Automaticamente

- **C/C++**: IntelliSense para código C
- **Assembly**: Syntax highlighting para assembly
- **Hex Editor**: Visualização de ROMs e dados binários
- **GitLens**: Controle de versão avançado
- **Error Lens**: Visualização inline de erros
- **Bracket Pair Colorizer**: Colorização de brackets
- **Platform-specific**: Extensões específicas por plataforma

### Configurações Automáticas

**settings.json**:
```json
{
    "C_Cpp.default.includePath": [
        "${workspaceFolder}/include",
        "C:/GBDK/include"
    ],
    "C_Cpp.default.defines": [
        "__GBDK__",
        "USE_SFR_FOR_REG"
    ],
    "files.associations": {
        "*.h": "c",
        "*.c": "c",
        "*.s": "asm",
        "*.asm": "asm"
    }
}
```

**tasks.json**:
```json
{
    "version": "2.0.0",
    "tasks": [
        {
            "label": "Build",
            "type": "shell",
            "command": "./scripts/build.bat",
            "group": {
                "kind": "build",
                "isDefault": true
            }
        },
        {
            "label": "Run",
            "type": "shell",
            "command": "./scripts/run.bat",
            "dependsOn": "Build"
        }
    ]
}
```

### Snippets Personalizados

**c.json**:
```json
{
    "Game Boy Main Function": {
        "prefix": "gbmain",
        "body": [
            "#include <gb/gb.h>",
            "#include <stdio.h>",
            "",
            "void main() {",
            "    // Inicialização",
            "    $1",
            "    ",
            "    // Loop principal",
            "    while(1) {",
            "        wait_vbl_done();",
            "        $2",
            "    }",
            "}"
        ],
        "description": "Template para função main do Game Boy"
    }
}
```

## Solução de Problemas

### Problemas Comuns

#### 1. Devkit não detectado

**Sintomas**: Sistema não encontra o devkit instalado

**Soluções**:
```python
# Verificar detecção manual
from core.retro_devkit_detector import RetroDevkitDetector
detector = RetroDevkitDetector()
result = detector.detect_devkit('gbdk')
print(f"Detectado: {result.is_installed}")
print(f"Caminho: {result.installation_path}")

# Forçar redetecção
detector.clear_cache()
results = detector.detect_all_devkits()
```

#### 2. Erro de compilação

**Sintomas**: Build falha com erros de compilador

**Soluções**:
- Verificar se o devkit está corretamente instalado
- Verificar variáveis de ambiente
- Verificar sintaxe do código
- Consultar logs detalhados

```python
# Verificar logs
from core.retro_devkit_logger import RetroDevkitLogger
logger_manager = RetroDevkitLogger()
logger_manager.enable_debug_mode()

# Verificar instalação
manager = RetroDevkitManager()
status = manager.verify_installation('gbdk')
print(f"Status: {status}")
```

#### 3. Emulador não inicia

**Sintomas**: ROM não abre no emulador

**Soluções**:
- Verificar se o emulador está instalado
- Verificar se a ROM foi compilada corretamente
- Verificar configurações do emulador

```python
# Verificar emuladores
manager = RetroDevkitManager()
emulators = manager.get_installed_emulators('gbdk')
print(f"Emuladores disponíveis: {emulators}")

# Testar emulador específico
manager.test_emulator('bgb', 'test.gb')
```

### Logs e Debug

#### Habilitar Modo Debug

```python
from core.retro_devkit_logger import RetroDevkitLogger

logger_manager = RetroDevkitLogger()
logger_manager.enable_debug_mode()

# Logs serão salvos em logs/retro_devkits/
```

#### Visualizar Logs

```python
# Obter resumo dos logs
summary = logger_manager.get_log_summary()
print(summary)

# Exportar logs
logger_manager.export_logs('debug_export.json')
```

## API e Extensibilidade

### Criando um Novo Devkit

```python
from core.retro_devkit_base import RetroDevkitBase

class MyCustomDevkit(RetroDevkitBase):
    def __init__(self, base_path, logger):
        super().__init__(base_path, logger)
        self.devkit_name = "my_custom"
        
    def install(self):
        """Implementar instalação personalizada"""
        # Lógica de instalação
        return True
        
    def verify_installation(self):
        """Verificar se está instalado"""
        # Lógica de verificação
        return True
        
    def create_project(self, project_name, project_path):
        """Criar novo projeto"""
        # Lógica de criação de projeto
        return True
```

### Registrando Novo Devkit

```python
# Adicionar ao manager
manager = RetroDevkitManager()
manager.register_devkit('my_custom', MyCustomDevkit)

# Adicionar detecção
detector = RetroDevkitDetector()
detector.add_devkit_check('my_custom', {
    'files': ['path/to/executable.exe'],
    'confidence': 0.9
})
```

### Hooks e Eventos

```python
# Registrar hooks
manager.register_hook('before_install', my_before_install_hook)
manager.register_hook('after_install', my_after_install_hook)

def my_before_install_hook(devkit_name):
    print(f"Iniciando instalação de {devkit_name}")
    
def my_after_install_hook(devkit_name, success):
    if success:
        print(f"Instalação de {devkit_name} concluída com sucesso")
    else:
        print(f"Falha na instalação de {devkit_name}")
```

## Exemplos Práticos

### Exemplo 1: Projeto Game Boy Completo

```c
// main.c
#include <gb/gb.h>
#include <stdio.h>

// Dados de sprite
const unsigned char sprite_data[] = {
    0x7E,0x7E,0x81,0xFF,0xA5,0xFF,0x81,0xFF,
    0xBD,0xFF,0x81,0xFF,0x7E,0x7E,0x00,0x00
};

void main() {
    // Configurar sprites
    set_sprite_data(0, 1, sprite_data);
    set_sprite_tile(0, 0);
    move_sprite(0, 88, 78);
    
    // Mostrar sprites
    SHOW_SPRITES;
    
    // Loop principal
    while(1) {
        // Verificar input
        if(joypad() & J_A) {
            move_sprite(0, 88, 68);
        } else {
            move_sprite(0, 88, 78);
        }
        
        wait_vbl_done();
    }
}
```

### Exemplo 2: Automação de Build

```python
# build_automation.py
from core.retro_devkit_manager import RetroDevkitManager
import os

def build_all_projects():
    """Compila todos os projetos de exemplo"""
    manager = RetroDevkitManager()
    projects = [
        ('gbdk', 'examples/gameboy/hello_world'),
        ('snes', 'examples/snes/sprite_demo'),
        ('nes', 'examples/nes/sound_test')
    ]
    
    for devkit, project_path in projects:
        print(f"Compilando {project_path}...")
        
        # Mudar para diretório do projeto
        os.chdir(project_path)
        
        # Compilar
        success = manager.build_project(devkit)
        
        if success:
            print(f"✅ {project_path} compilado com sucesso")
            
            # Testar no emulador
            manager.test_project(devkit)
        else:
            print(f"❌ Falha na compilação de {project_path}")
            
if __name__ == '__main__':
    build_all_projects()
```

### Exemplo 3: Conversão de Assets

```python
# asset_converter.py
from core.retro_devkit_manager import RetroDevkitManager
from pathlib import Path

def convert_game_assets(project_path):
    """Converte todos os assets de um projeto"""
    manager = RetroDevkitManager()
    project = Path(project_path)
    
    # Converter sprites
    sprites_dir = project / 'assets' / 'sprites'
    if sprites_dir.exists():
        for png_file in sprites_dir.glob('*.png'):
            print(f"Convertendo sprite: {png_file.name}")
            manager.convert_sprite(png_file, 'gbdk')
            
    # Converter mapas
    maps_dir = project / 'assets' / 'maps'
    if maps_dir.exists():
        for tmx_file in maps_dir.glob('*.tmx'):
            print(f"Convertendo mapa: {tmx_file.name}")
            manager.convert_map(tmx_file, 'gbdk')
            
    # Converter música
    music_dir = project / 'assets' / 'music'
    if music_dir.exists():
        for mod_file in music_dir.glob('*.mod'):
            print(f"Convertendo música: {mod_file.name}")
            manager.convert_music(mod_file, 'gbdk')
            
    print("Conversão de assets concluída!")

if __name__ == '__main__':
    convert_game_assets('my_game_project')
```

## Conclusão

O sistema de Retro Development Kits oferece uma solução completa e integrada para desenvolvimento de jogos retro, combinando:

- **Facilidade de uso**: Instalação e configuração automática
- **Produtividade**: Scripts de automação e integração com VS Code
- **Flexibilidade**: Suporte a múltiplas plataformas e emuladores
- **Extensibilidade**: API para adicionar novos devkits e funcionalidades
- **Confiabilidade**: Sistema de logs e testes abrangentes

Com este sistema, desenvolvedores podem focar na criação de jogos incríveis para plataformas retro, sem se preocupar com a complexidade da configuração e gerenciamento das ferramentas de desenvolvimento.

---

**Documentação atualizada em**: Dezembro 2024  
**Versão do sistema**: 1.0.0  
**Suporte**: Consulte os logs do sistema ou abra uma issue no repositório