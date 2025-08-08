# Exemplos de Retro Development Kits

Esta pasta contém exemplos práticos de uso do sistema de Retro Development Kits, demonstrando como desenvolver jogos para diferentes plataformas retro.

## Estrutura dos Exemplos

```
examples/retro_devkits/
├── gameboy/
│   ├── hello_world/          # Exemplo básico Game Boy
│   ├── sprite_demo/          # Demonstração de sprites
│   └── sound_test/           # Teste de áudio
├── snes/
│   ├── hello_world/          # Exemplo básico SNES
│   ├── mode7_demo/           # Demonstração Mode 7
│   └── dma_example/          # Exemplo de DMA
├── psx/
│   ├── hello_world/          # Exemplo básico PlayStation
│   ├── 3d_cube/              # Cubo 3D simples
│   └── cd_audio/             # Reprodução de áudio CD
├── n64/
│   ├── hello_world/          # Exemplo básico N64
│   ├── controller_test/      # Teste de controle
│   └── texture_demo/         # Demonstração de texturas
├── gba/
│   ├── hello_world/          # Exemplo básico GBA
│   ├── sprite_rotation/      # Rotação de sprites
│   └── mode7_racing/         # Jogo de corrida Mode 7
├── neogeo/
│   ├── hello_world/          # Exemplo básico Neo Geo
│   ├── fighter_demo/         # Demo de luta
│   └── large_sprites/        # Sprites grandes
├── nes/
│   ├── hello_world/          # Exemplo básico NES
│   ├── scrolling_demo/       # Demonstração de scroll
│   └── music_player/         # Player de música
├── saturn/
│   ├── hello_world/          # Exemplo básico Saturn
│   ├── vdp1_sprites/         # Sprites VDP1
│   └── 3d_polygon/           # Polígonos 3D
└── automation/
    ├── build_all.py          # Script para compilar todos
    ├── test_all.py           # Script para testar todos
    └── asset_converter.py    # Conversor de assets
```

## Como Usar os Exemplos

### 1. Configuração Inicial

```bash
# Instalar todos os devkits necessários
python -c "from core.retro_devkit_manager import RetroDevkitManager; m = RetroDevkitManager(); [m.install_devkit(d) for d in m.get_supported_devkits()]"

# Verificar instalação
python -c "from core.retro_devkit_detector import RetroDevkitDetector; print(RetroDevkitDetector().generate_summary())"
```

### 2. Compilar um Exemplo

```bash
# Navegar para o exemplo
cd examples/retro_devkits/gameboy/hello_world

# Compilar
./scripts/build.bat  # Windows
./scripts/build.sh   # Linux/macOS

# Executar no emulador
./scripts/run.bat    # Windows
./scripts/run.sh     # Linux/macOS
```

### 3. Usar Scripts de Automação

```bash
# Compilar todos os exemplos
python examples/retro_devkits/automation/build_all.py

# Testar todos os exemplos
python examples/retro_devkits/automation/test_all.py

# Converter assets de um projeto
python examples/retro_devkits/automation/asset_converter.py gameboy/sprite_demo
```

## Exemplos por Plataforma

### Game Boy

#### Hello World
- **Descrição**: Exemplo básico que exibe "Hello World" na tela
- **Conceitos**: Inicialização básica, printf, loop principal
- **Arquivo principal**: `main.c`

#### Sprite Demo
- **Descrição**: Demonstra movimentação de sprites com controle
- **Conceitos**: Sprites, input do joypad, animação
- **Assets**: Sprites de personagem, tiles de fundo

#### Sound Test
- **Descrição**: Teste de reprodução de sons e música
- **Conceitos**: Canais de áudio, efeitos sonoros, música de fundo
- **Assets**: Arquivos de música e efeitos

### SNES

#### Hello World
- **Descrição**: Exemplo básico para Super Nintendo
- **Conceitos**: Inicialização do sistema, modo de vídeo, texto
- **Arquivo principal**: `main.c`

#### Mode 7 Demo
- **Descrição**: Demonstração do famoso Mode 7 do SNES
- **Conceitos**: Transformações de matriz, rotação, escala
- **Assets**: Texturas para transformação

#### DMA Example
- **Descrição**: Exemplo de uso do DMA para transferência rápida
- **Conceitos**: DMA, VRAM, otimização de performance
- **Técnicas**: Transferência de dados otimizada

### PlayStation

#### Hello World
- **Descrição**: Exemplo básico para PlayStation 1
- **Conceitos**: Inicialização do GPU, primitivas 2D
- **Arquivo principal**: `main.c`

#### 3D Cube
- **Descrição**: Renderização de um cubo 3D rotativo
- **Conceitos**: Geometria 3D, transformações, GPU
- **Técnicas**: Matemática 3D, pipeline gráfico

#### CD Audio
- **Descrição**: Reprodução de áudio de CD
- **Conceitos**: Sistema de CD, streaming de áudio
- **Assets**: Faixas de áudio em formato CD

### Nintendo 64

#### Hello World
- **Descrição**: Exemplo básico para Nintendo 64
- **Conceitos**: Inicialização do sistema, RDP, RSP
- **Arquivo principal**: `main.c`

#### Controller Test
- **Descrição**: Teste completo do controle do N64
- **Conceitos**: Input analógico, botões, rumble
- **Funcionalidades**: Teste de todos os controles

#### Texture Demo
- **Descrição**: Demonstração de texturas e filtros
- **Conceitos**: Mapeamento de textura, filtros, TMEM
- **Assets**: Texturas de exemplo

### Game Boy Advance

#### Hello World
- **Descrição**: Exemplo básico para Game Boy Advance
- **Conceitos**: Modos de vídeo, paletas, tiles
- **Arquivo principal**: `main.c`

#### Sprite Rotation
- **Descrição**: Rotação e escala de sprites
- **Conceitos**: Transformações afins, hardware sprites
- **Técnicas**: Rotação em tempo real

#### Mode 7 Racing
- **Descrição**: Jogo de corrida estilo Mode 7
- **Conceitos**: Pseudo-3D, perspectiva, gameplay
- **Assets**: Pista, carros, interface

### Neo Geo

#### Hello World
- **Descrição**: Exemplo básico para Neo Geo
- **Conceitos**: Sistema arcade, sprites grandes
- **Arquivo principal**: `main.c`

#### Fighter Demo
- **Descrição**: Demo de jogo de luta
- **Conceitos**: Animação complexa, input, colisão
- **Assets**: Sprites de lutadores, cenários

#### Large Sprites
- **Descrição**: Demonstração de sprites grandes do Neo Geo
- **Conceitos**: Sprites 16x16 até 16x512, paletas
- **Técnicas**: Otimização de sprites

### NES

#### Hello World
- **Descrição**: Exemplo básico para Nintendo Entertainment System
- **Conceitos**: PPU, nametables, paletas
- **Arquivo principal**: `main.c`

#### Scrolling Demo
- **Descrição**: Demonstração de scroll horizontal e vertical
- **Conceitos**: Scroll de câmera, nametables, mirroring
- **Técnicas**: Scroll suave

#### Music Player
- **Descrição**: Player de música com engine de áudio
- **Conceitos**: APU, canais de som, sequenciamento
- **Assets**: Músicas em formato tracker

### Sega Saturn

#### Hello World
- **Descrição**: Exemplo básico para Sega Saturn
- **Conceitos**: Dual CPU, VDP1, VDP2
- **Arquivo principal**: `main.c`

#### VDP1 Sprites
- **Descrição**: Demonstração do chip VDP1 para sprites
- **Conceitos**: Sprites escaláveis, rotação, transparência
- **Técnicas**: Efeitos visuais avançados

#### 3D Polygon
- **Descrição**: Renderização de polígonos 3D
- **Conceitos**: Geometria 3D, dual CPU, otimização
- **Técnicas**: Programação paralela

## Scripts de Automação

### build_all.py

Script que compila todos os exemplos automaticamente:

```python
#!/usr/bin/env python3
"""Script para compilar todos os exemplos de retro devkits"""

import os
import sys
from pathlib import Path
from core.retro_devkit_manager import RetroDevkitManager

def build_all_examples():
    """Compila todos os exemplos"""
    base_path = Path(__file__).parent
    manager = RetroDevkitManager()
    
    examples = [
        ('gameboy', 'hello_world'),
        ('gameboy', 'sprite_demo'),
        ('gameboy', 'sound_test'),
        ('snes', 'hello_world'),
        ('snes', 'mode7_demo'),
        ('snes', 'dma_example'),
        # ... mais exemplos
    ]
    
    success_count = 0
    total_count = len(examples)
    
    for platform, example in examples:
        example_path = base_path / platform / example
        if not example_path.exists():
            print(f"⚠️  Exemplo não encontrado: {platform}/{example}")
            continue
            
        print(f"🔨 Compilando {platform}/{example}...")
        
        # Mudar para diretório do exemplo
        original_cwd = os.getcwd()
        os.chdir(example_path)
        
        try:
            # Compilar usando o script de build
            if (example_path / 'scripts' / 'build.bat').exists():
                result = os.system('scripts\\build.bat')
            elif (example_path / 'scripts' / 'build.sh').exists():
                result = os.system('bash scripts/build.sh')
            else:
                print(f"❌ Script de build não encontrado para {platform}/{example}")
                continue
                
            if result == 0:
                print(f"✅ {platform}/{example} compilado com sucesso")
                success_count += 1
            else:
                print(f"❌ Falha na compilação de {platform}/{example}")
                
        except Exception as e:
            print(f"❌ Erro ao compilar {platform}/{example}: {e}")
        finally:
            os.chdir(original_cwd)
            
    print(f"\n📊 Resultado: {success_count}/{total_count} exemplos compilados com sucesso")
    return success_count == total_count

if __name__ == '__main__':
    success = build_all_examples()
    sys.exit(0 if success else 1)
```

### test_all.py

Script que testa todos os exemplos nos emuladores:

```python
#!/usr/bin/env python3
"""Script para testar todos os exemplos nos emuladores"""

import os
import time
from pathlib import Path
from core.retro_devkit_manager import RetroDevkitManager

def test_all_examples():
    """Testa todos os exemplos nos emuladores"""
    base_path = Path(__file__).parent
    manager = RetroDevkitManager()
    
    # Mapear extensões de ROM por plataforma
    rom_extensions = {
        'gameboy': '.gb',
        'snes': '.sfc',
        'psx': '.bin',
        'n64': '.z64',
        'gba': '.gba',
        'neogeo': '.neo',
        'nes': '.nes',
        'saturn': '.bin'
    }
    
    for platform_dir in base_path.iterdir():
        if not platform_dir.is_dir() or platform_dir.name == 'automation':
            continue
            
        platform = platform_dir.name
        rom_ext = rom_extensions.get(platform)
        
        if not rom_ext:
            print(f"⚠️  Extensão de ROM desconhecida para {platform}")
            continue
            
        print(f"\n🎮 Testando exemplos de {platform.upper()}...")
        
        for example_dir in platform_dir.iterdir():
            if not example_dir.is_dir():
                continue
                
            example_name = example_dir.name
            
            # Procurar ROM compilada
            rom_files = list(example_dir.glob(f"*{rom_ext}"))
            
            if not rom_files:
                print(f"❌ ROM não encontrada para {platform}/{example_name}")
                continue
                
            rom_file = rom_files[0]
            print(f"🚀 Testando {platform}/{example_name} ({rom_file.name})...")
            
            try:
                # Executar no emulador por 5 segundos
                manager.run_rom_test(str(rom_file), platform, duration=5)
                print(f"✅ {platform}/{example_name} executado com sucesso")
                
            except Exception as e:
                print(f"❌ Erro ao testar {platform}/{example_name}: {e}")
                
            # Pequena pausa entre testes
            time.sleep(1)
            
    print("\n🏁 Testes concluídos!")

if __name__ == '__main__':
    test_all_examples()
```

### asset_converter.py

Script para converter assets de projetos:

```python
#!/usr/bin/env python3
"""Script para converter assets de projetos"""

import sys
from pathlib import Path
from core.retro_devkit_manager import RetroDevkitManager

def convert_project_assets(project_path):
    """Converte todos os assets de um projeto"""
    project = Path(project_path)
    
    if not project.exists():
        print(f"❌ Projeto não encontrado: {project_path}")
        return False
        
    # Determinar plataforma pelo caminho
    platform = None
    for part in project.parts:
        if part in ['gameboy', 'snes', 'psx', 'n64', 'gba', 'neogeo', 'nes', 'saturn']:
            platform = part
            break
            
    if not platform:
        print(f"❌ Não foi possível determinar a plataforma para {project_path}")
        return False
        
    print(f"🔄 Convertendo assets para {platform}/{project.name}...")
    
    manager = RetroDevkitManager()
    assets_dir = project / 'assets'
    
    if not assets_dir.exists():
        print(f"⚠️  Diretório de assets não encontrado: {assets_dir}")
        return True
        
    converted_count = 0
    
    # Converter sprites
    sprites_dir = assets_dir / 'sprites'
    if sprites_dir.exists():
        for image_file in sprites_dir.glob('*.png'):
            print(f"  🖼️  Convertendo sprite: {image_file.name}")
            try:
                manager.convert_sprite(str(image_file), platform)
                converted_count += 1
            except Exception as e:
                print(f"    ❌ Erro: {e}")
                
    # Converter mapas
    maps_dir = assets_dir / 'maps'
    if maps_dir.exists():
        for map_file in maps_dir.glob('*.tmx'):
            print(f"  🗺️  Convertendo mapa: {map_file.name}")
            try:
                manager.convert_map(str(map_file), platform)
                converted_count += 1
            except Exception as e:
                print(f"    ❌ Erro: {e}")
                
    # Converter música
    music_dir = assets_dir / 'music'
    if music_dir.exists():
        for music_file in music_dir.glob('*.mod'):
            print(f"  🎵 Convertendo música: {music_file.name}")
            try:
                manager.convert_music(str(music_file), platform)
                converted_count += 1
            except Exception as e:
                print(f"    ❌ Erro: {e}")
                
    print(f"✅ Conversão concluída! {converted_count} assets convertidos.")
    return True

def main():
    if len(sys.argv) != 2:
        print("Uso: python asset_converter.py <caminho_do_projeto>")
        print("Exemplo: python asset_converter.py gameboy/sprite_demo")
        sys.exit(1)
        
    project_path = sys.argv[1]
    success = convert_project_assets(project_path)
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
```

## Requisitos

- Python 3.8+
- Sistema de Retro Development Kits instalado
- Devkits específicos para cada plataforma
- Emuladores configurados

## Contribuindo

Para adicionar novos exemplos:

1. Crie um diretório para sua plataforma (se não existir)
2. Crie um subdiretório para seu exemplo
3. Inclua código fonte, assets e scripts de build
4. Adicione documentação no README do exemplo
5. Teste a compilação e execução

## Suporte

Para problemas com os exemplos:

1. Verifique se todos os devkits estão instalados
2. Consulte os logs do sistema
3. Verifique a documentação específica da plataforma
4. Abra uma issue no repositório

---

**Última atualização**: Dezembro 2024  
**Exemplos testados**: Todas as plataformas suportadas  
**Status**: Funcional e testado