# WinDeckHelper

WinDeckHelper é uma ferramenta de automação para configuração e instalação de ambiente de desenvolvimento para PC Engines, especialmente otimizada para dispositivos como o Steam Deck rodando Windows.

## 🚀 Funcionalidades

- 🔧 Instalação automatizada de ferramentas de desenvolvimento
- 📦 Gerenciamento de SDKs para desenvolvimento de jogos retro
- 🎮 Instalação de emuladores
- 🛠️ Configuração de drivers e runtimes
- 🤖 Suporte para ferramentas de IA
- 🔄 Verificação automática de dependências

## 📋 Requisitos do Sistema

- Windows 10/11
- PowerShell 5.1 ou superior
- Conexão com a Internet
- Privilégios de administrador

## 🎯 Grupos de Instalação

### Drivers Obrigatórios
- Driver de Vídeo AMD
- Driver de Áudio
- Driver Bluetooth
- Driver do Leitor de Cartão
- Driver BTRFS

### Ferramentas de Desenvolvimento
- MinGW-w64
- Clang
- CMake
- Ninja
- vcpkg
- SDL2
- SDL2-TTF
- ZLIB
- PNG
- Boost
- Dear ImGui
- E muito mais...

### SDKs
- SGDK (Sega Genesis)
- PSn00bSDK (PlayStation 1)
- PS2DEV (PlayStation 2)
- SNESDev (Super Nintendo)
- DevkitSMS (Master System/Game Gear)
- GBDK (Game Boy)
- E outros...

### Emuladores
- Stella (Atari 2600)
- ProSystem (Atari 7800)
- Handy (Atari Lynx)
- ColEm (ColecoVision)
- jzIntv (Intellivision)
- E muitos outros...

### Runtimes e Bibliotecas
- Microsoft Visual C++ Runtimes
- DirectX
- OpenAL
- PhysX
- UE3/UE4 Prerequisites

## 🚀 Como Usar

1. Clone o repositório:
```powershell
git clone https://github.com/seu-usuario/WinDeckHelper.git
```

2. Execute o script Start.bat como administrador

3. Selecione os componentes desejados na interface gráfica

4. Clique em "Instalar" para iniciar o processo

## ⚙️ Configuração

O script detectará automaticamente:
- Sistema operacional e arquitetura
- Componentes já instalados
- Dependências necessárias
- Versão do LCD/OLED para drivers específicos

## 🤝 Contribuindo

1. Faça um Fork do projeto
2. Crie uma Branch para sua Feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a Branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## ✨ Agradecimentos

- Comunidade Steam Deck
- Contribuidores de SDKs e emuladores
- Todos os desenvolvedores que tornaram este projeto possível

[ENG](https://github.com/anejolov/WinDeckHelper/blob/main/README.md) | [РУС](https://github.com/anejolov/WinDeckHelper/blob/main/README_RUS.md)

WinDeckHelper - Utilities installer and tweaker for your Windows Steam Deck.

Project inspired by [CelesteHeartsong / SteamDeckAutomatedInstall](https://github.com/CelesteHeartsong/SteamDeckAutomatedInstall)

![WinDeckHelper-2 3_eng](https://github.com/user-attachments/assets/cf92a494-a93b-41a8-836b-760306b60d39)

[Download latest version here](https://github.com/anejolov/WinDeckHelper/releases/tag/v2.3.1)


## How To Install
- Open WinDeckHelper.exe as Administrator
- Select Steam Deck version LCD/OLED
- If Wi-Fi driver is not installed by default, install it by clicking on [Install WI-FI Driver]
- Connect to the internet
- Choose the stuff you need and click on START.
- Reboot the system after the process is finished.

## Stuff Categories
- [ Must-Have ] - Must-have things you need to play games on your WinDeck.
- [ Tweaks ] - Some tweaks to improve quality of your Windows life.
- [ Soft ] - Software you may need, like Browser etc.

## Potential Issues
- Windows Defender defines WinDeckHelper as a virus. Please disable Defender if possible.
- Custom Resolution Utility is disabled for OLED, because I have no cru profile for OLED version
- If "Custom Resolution Utility" window does not disappear:
  - Please click on "import" button, select "cru-steamdeck.bin" file from "Downloads" folder and click "OK"
- If "EqualizerAPO" window does not disappear:
  - Please check "Speakers" checkbox from list of devices and click "OK"
