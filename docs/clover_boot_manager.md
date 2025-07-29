# Clover Boot Manager

## Introdução

O Clover Boot Manager é um gerenciador de boot avançado que permite inicializar múltiplos sistemas operacionais em um único computador. Ele oferece uma interface gráfica amigável e suporte para configurações avançadas de inicialização.

Este documento descreve a implementação do Clover Boot Manager no Environment Dev Script, incluindo instalação, configuração, verificação e recuperação.

## Visão Geral

A implementação do Clover Boot Manager no Environment Dev Script inclui:

1. **Instalação Segura**: Instalação do Clover Boot Manager com backup da partição EFI.
2. **Detecção de Sistemas Operacionais**: Detecção automática de sistemas operacionais instalados.
3. **Configuração Automática**: Configuração automática do Clover Boot Manager com base nos sistemas operacionais detectados.
4. **Verificação Robusta**: Verificação detalhada da instalação do Clover Boot Manager.
5. **Recuperação Fácil**: Sistema de recuperação em caso de problemas com o Clover Boot Manager.

## Recursos

- **Multiboot**: Inicie diferentes sistemas operacionais (Windows, Linux, macOS) a partir de um único menu de inicialização.
- **Temas personalizáveis**: Interface gráfica atraente e personalizável.
- **Configuração avançada**: Opções avançadas para configurar o processo de inicialização.
- **Compatibilidade UEFI**: Projetado para funcionar com sistemas UEFI modernos.
- **Backup e Restauração**: Sistema de backup e restauração da partição EFI.
- **Detecção Automática**: Detecção automática de sistemas operacionais instalados.

## Requisitos

- Sistema com firmware UEFI (não compatível com BIOS legado)
- Partição EFI acessível
- Pelo menos 100 MB de espaço livre na partição EFI
- Privilégios de administrador para instalação

## Arquitetura

A implementação do Clover Boot Manager é baseada em vários módulos Python:

- **clover_installer.py**: Módulo principal para instalação e desinstalação do Clover Boot Manager.
- **clover_verification.py**: Módulo para verificação da instalação do Clover Boot Manager.
- **efi_backup.py**: Módulo para backup e restauração da partição EFI.
- **os_detection.py**: Módulo para detecção de sistemas operacionais instalados.

### Diagrama de Fluxo

```
┬───────────────┬     ┬───────────────┬     ┬───────────────┬
│  Verificação de │     │  Backup da      │     │  Instalação do  │
│  Pré-requisitos │────▶│  Partição EFI   │────▶│  Clover         │
┴───────────────┴     ┴───────────────┴     ┴───────────────┴
                                                         │
                                                         ▼
┬───────────────┬     ┬───────────────┬     ┬───────────────┬
│  Verificação da │     │  Configuração   │     │  Detecção de    │
│  Instalação     │◀────│  do Clover      │◀────│  Sistemas OS    │
┴───────────────┴     ┴───────────────┴     ┴───────────────┴
```

## Instalação

### Pré-requisitos

- Sistema operacional Windows 10 ou superior
- Partição EFI acessível
- Privilégios de administrador
- Espaço suficiente na partição EFI (pelo menos 100 MB livres)

### Processo de Instalação

1. **Verificação de Pré-requisitos**:
   - Verifica se o sistema está em modo UEFI
   - Verifica se a partição EFI está acessível
   - Verifica se há espaço suficiente na partição EFI
   - Verifica se o usuário tem privilégios de administrador

2. **Backup da Partição EFI**:
   - Cria um backup completo da partição EFI
   - Armazena o backup em um local seguro
   - Registra informações sobre o backup para recuperação

3. **Extração do Clover**:
   - Extrai o arquivo ZIP do Clover para um diretório temporário
   - Verifica a integridade dos arquivos extraídos

4. **Instalação na Partição EFI**:
   - Monta a partição EFI se necessário
   - Copia os arquivos do Clover para a partição EFI
   - Preserva os bootloaders existentes

5. **Detecção de Sistemas Operacionais**:
   - Detecta sistemas operacionais instalados
   - Identifica Windows, Linux e macOS

6. **Configuração do Clover**:
   - Cria ou atualiza o arquivo config.plist
   - Configura entradas de boot para os sistemas operacionais detectados
   - Configura temas e opções avançadas

7. **Verificação da Instalação**:
   - Verifica se os arquivos do Clover foram instalados corretamente
   - Verifica se a configuração do Clover está correta
   - Verifica se o Clover está configurado como bootloader padrão

### Instalação pelo Environment Dev Script

O Clover Boot Manager pode ser instalado através do Environment Dev Script. Siga estas etapas:

1. Execute o Environment Dev Script
2. Selecione "Gerenciadores de Boot" na lista de categorias
3. Selecione "CloverBootManager" na lista de componentes
4. Clique em "Instalar"
5. Siga as instruções na tela

Durante a instalação, você será perguntado se deseja usar o Clover como bootloader principal. Se escolher "Sim", o Clover será executado automaticamente na inicialização do sistema. Se escolher "Não", o bootloader original será preservado e você precisará selecionar o Clover manualmente no menu de inicialização do UEFI.

## Uso

Após a instalação, reinicie o computador para acessar o Clover Boot Manager. Você verá uma interface gráfica com os sistemas operacionais detectados.

### Navegação Básica

- Use as teclas de seta para navegar entre as opções
- Pressione Enter para selecionar um sistema operacional
- Pressione F1 para obter ajuda
- Pressione F2 para acessar as opções de inicialização
- Pressione F3 para mostrar informações sobre o sistema
- Pressione F4 para acessar as opções de configuração

### Configuração

O Clover Boot Manager é configurado através do arquivo `config.plist` localizado na partição EFI. O Environment Dev Script gera automaticamente uma configuração básica com base nos sistemas operacionais detectados.

Para configurações mais avançadas, você pode editar o arquivo `config.plist` manualmente ou usar ferramentas como o Clover Configurator.

## Recuperação

O Environment Dev Script inclui recursos de recuperação para o Clover Boot Manager. Se você encontrar problemas com o Clover, pode usar as seguintes opções:

### Restaurar Backup da Partição EFI

Durante a instalação, o Environment Dev Script cria automaticamente um backup da partição EFI. Você pode restaurar este backup usando o menu de ferramentas do Environment Dev Script:

1. Execute o Environment Dev Script
2. Selecione "Ferramentas" no menu principal
3. Selecione "Recuperar Clover Boot Manager"
4. Selecione "Restaurar Backup da Partição EFI"
5. Escolha o backup que deseja restaurar

### Reparar Bootloader do Windows

Se você não conseguir iniciar o Windows após a instalação do Clover, pode reparar o bootloader do Windows:

1. Execute o Environment Dev Script
2. Selecione "Ferramentas" no menu principal
3. Selecione "Recuperar Clover Boot Manager"
4. Selecione "Reparar Bootloader do Windows"

### Desinstalar Clover

Para remover completamente o Clover Boot Manager:

1. Execute o Environment Dev Script
2. Selecione "Ferramentas" no menu principal
3. Selecione "Recuperar Clover Boot Manager"
4. Selecione "Desinstalar Clover Boot Manager"

## Solução de Problemas

### O sistema não inicia após a instalação do Clover

- Inicie em modo seguro (pressione F8 durante a inicialização)
- Use uma mídia de recuperação do Windows
- Restaure o backup da partição EFI usando o Environment Dev Script

### Clover inicia, mas não mostra todos os sistemas operacionais

- Verifique a configuração do Clover em `EFI/CLOVER/config.plist`
- Execute o utilitário de detecção de sistemas operacionais do Environment Dev Script

### Erros durante a inicialização do Clover

- Verifique os logs do Clover
- Restaure o bootloader original

## Recursos Adicionais

- [Site oficial do Clover](https://github.com/CloverHackyColor/CloverBootloader)
- [Documentação do Clover](https://github.com/CloverHackyColor/CloverBootloader/wiki)
- [Fórum do Clover](https://www.insanelymac.com/forum/forum/424-clover/)

## Suporte

Se você encontrar problemas com o Clover Boot Manager instalado pelo Environment Dev Script, entre em contato com o suporte do Environment Dev Script.
