# WinDeckHelper

Um assistente automatizado para configuração e instalação de ambientes de desenvolvimento para PC Engines, otimizado para dispositivos como o Steam Deck rodando Windows.

## 🚀 Funcionalidades

### Instalação Automatizada
- **Drivers Essenciais**
  - AMD Video Drivers (otimizados para Steam Deck)
  - Bluetooth
  - Audio
  - Wi-Fi
  - Controles e Periféricos

### 🛠️ Ferramentas de Desenvolvimento
- **IDEs e Editores**
  - Visual Studio Code
  - Visual Studio Community
  - Notepad++
  - Sublime Text

- **Controle de Versão**
  - Git
  - GitHub Desktop
  - TortoiseGit

- **SDKs e Frameworks**
  - SGDK (Sega Genesis Development Kit)
  - PSn00bSDK (PlayStation Development)
  - PS2DEV (PlayStation 2 Development)
  - SNESDev (Super Nintendo Development)
  - GBDK (Game Boy Development)

### 🎮 Emuladores
- RetroArch
- PCSX2
- Dolphin
- RPCS3
- Xemu
- Cemu
- Yuzu

### 🔧 Utilitários
- 7-Zip
- CPU-Z
- GPU-Z
- HWiNFO
- MSI Afterburner
- Process Lasso
- MemReduct
- OBS Studio
- VLC Media Player
- K-Lite Codec Pack

### 🤖 Ferramentas de IA
- Ollama
- LM Studio

### 🔄 Tweaks e Otimizações
- **Sistema**
  - Desativar Game Bar
  - Desativar Login após Suspensão
  - Mostrar Teclado Virtual

- **Multi-Boot**
  - Clover Bootloader (Detecção automática de sistemas Linux)
  - Configuração de dual/multi-boot automatizada
  - Backup de configuração de boot

## 📋 Requisitos do Sistema
- Windows 10/11
- PowerShell 5.1 ou superior
- Conexão com a Internet
- Privilégios de Administrador

## 🔍 Verificações Automáticas
- Detecção de Visual C++ Runtimes
  - Verificação dupla (DLLs e Registro)
  - Suporte para versões de 2005 a 2022
  - Verificação de arquiteturas x86 e x64
  - Informações detalhadas de versão

- Verificação de SDKs
  - Detecção automática de instalação
  - Verificação de dependências
  - Validação de variáveis de ambiente
  - Checagem de arquivos críticos

## 💻 Interface
- Design moderno e intuitivo
- Tema escuro otimizado
- Seleção de componentes em árvore
- Botões de ação com tooltips
- Barra de progresso em tempo real
- Log detalhado de operações

## 📥 Instalação

1. Clone o repositório:
```powershell
git clone https://github.com/seu-usuario/windeckhelper.git
```

2. Execute o script como administrador:
```powershell
powershell -ExecutionPolicy Bypass -File Windeckhelper.ps1
```

## ⚙️ Configuração
O script detecta automaticamente:
- Sistema operacional e arquitetura
- Componentes já instalados
- Dependências necessárias
- Espaço em disco disponível
- Conexão com a internet

## 🤝 Contribuindo

1. Faça um Fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add: nova funcionalidade'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📝 Licença
Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 🙏 Agradecimentos
- Comunidade Steam Deck
- Contribuidores de SDKs e Emuladores
- Todos os desenvolvedores envolvidos no projeto

## 📞 Suporte
- Abra uma issue para reportar bugs
- Sugestões são sempre bem-vindas
- Participe das discussões no GitHub

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
