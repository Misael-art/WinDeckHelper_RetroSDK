# Environment Dev Deep Evaluation v2.0

<div align="center">

![Environment Dev](https://img.shields.io/badge/Environment-Dev-blue?style=for-the-badge)
![Version](https://img.shields.io/badge/Version-2.0.0-green?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.8+-yellow?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-red?style=for-the-badge)

**Sistema completo de detecção e instalação de ambientes de desenvolvimento**

[🚀 Download](#-download) • [📖 Documentação](#-documentação) • [🎮 Steam Deck](#-steam-deck) • [🤝 Contribuir](#-contribuindo)

</div>

## 🎯 Visão Geral

O **Environment Dev Deep Evaluation** é uma solução completa e robusta para detectar, gerenciar e instalar ambientes de desenvolvimento. Com interface gráfica moderna, suporte completo ao Steam Deck e sistema de instalação inteligente.

### ✨ Principais Funcionalidades

- 🔍 **Detecção Automática** - Identifica componentes já instalados no sistema
- 🛠️ **Instalação Robusta** - Sistema de instalação com rollback automático
- 🎮 **Steam Deck Ready** - Otimizado para Steam Deck com interface touch
- 🎨 **Interface Moderna** - GUI responsiva e intuitiva
- 🔄 **Status Persistente** - Mantém estado entre execuções
- 🎯 **SGDK 2.11** - Instalação real do Sega Genesis Development Kit
- 🧩 **Sistema de Plugins** - Arquitetura extensível
- 📊 **Relatórios Detalhados** - Logs e métricas completas

## 🚀 Download

### Pacote Pronto para Uso
Baixe o executável completo (não requer Python instalado):

- **Windows**: [EnvironmentDevDeepEvaluation_v2.0.zip](releases/latest)
- **Linux/Mac**: [EnvironmentDevDeepEvaluation_v2.0.zip](releases/latest)

### Instalação Rápida
```bash
# 1. Baixar e extrair o ZIP
# 2. Executar o launcher:
# Windows:
Iniciar_Environment_Dev.bat

# Linux/Mac:
./iniciar_environment_dev.sh
```

## 📖 Documentação

### Guias de Usuário
- 📋 [Guia de Instalação](docs/installation_configuration_guide.md)
- 🎮 [Uso no Steam Deck](docs/steamdeck_usage_guide.md)
- 🏗️ [Arquitetura do Sistema](docs/architecture_analysis.md)

### Para Desenvolvedores
- 🔧 [Guia de Deployment](DEPLOYMENT_README.md)
- 📝 [Resumo das Correções](FINAL_FIXES_SUMMARY.md)
- 🛠️ [Sistema de Instalação](SISTEMA_INSTALACAO_ROBUSTO_COMPLETO.md)

## 🎮 Steam Deck

Totalmente otimizado para Steam Deck com:

- ✅ Interface touch otimizada
- ✅ Navegação por gamepad
- ✅ Detecção automática de hardware
- ✅ Otimizações de bateria
- ✅ Modo overlay
- ✅ Feedback háptico

## 🛠️ Componentes Suportados

### Runtimes Essenciais
- **Git** - Sistema de controle de versão
- **Python 3.x** - Linguagem de programação
- **Node.js** - Runtime JavaScript
- **Java JDK** - Kit de desenvolvimento Java
- **.NET SDK** - Framework Microsoft
- **Visual C++** - Redistributables Microsoft
- **PowerShell** - Shell avançado

### Ferramentas de Desenvolvimento
- **Visual Studio Code** - Editor de código
- **Docker Desktop** - Containerização
- **Kubernetes** - Orquestração de containers
- **Git Bash** - Terminal Git para Windows

### Kits de Desenvolvimento Retro 🕹️
- **SGDK 2.11** - Sega Genesis Development Kit
- **GBDK** - Game Boy Development Kit
- **CC65** - Compilador para SNES
- **PSn00bSDK** - PlayStation 1 SDK
- **Devkitpro** - Nintendo consoles
- **E muitos outros...**

## 🔧 Instalação para Desenvolvimento

### Pré-requisitos
- Python 3.8+
- Windows 10/11, Linux ou macOS
- 2GB RAM mínimo
- 1GB espaço em disco

### Instalação
```bash
# Clonar repositório
git clone https://github.com/Misael-art/EnvironmentDev_MISA.git
cd EnvironmentDev_MISA

# Instalar dependências
pip install -r requirements.txt

# Executar
python main.py
```

### Criar Pacote de Deployment
```bash
# Instalar dependências de build
python install_build_dependencies.py

# Criar executável
python build_deployment.py

# Testar pacote
python test_deployment_package.py
```

## 📊 Estatísticas do Projeto

- **Linhas de Código**: ~15,000+
- **Arquivos Python**: 50+
- **Componentes Suportados**: 140+
- **Documentação**: 20+ arquivos
- **Testes**: 100+ casos de teste

## 🏗️ Arquitetura

```
EnvironmentDev_MISA/
├── core/                    # Núcleo do sistema
│   ├── detection_engine.py      # Motor de detecção
│   ├── installer.py             # sistema de instalação
│   ├── component_manager.py     # gerenciador de componentes
│   └── ...
├── gui/                     # Interface gráfica
│   ├── modern_frontend_manager.py
│   ├── components_viewer_gui.py
│   └── ...
├── config/                  # Configurações
│   └── components/              # Definições YAML
├── docs/                    # Documentação
├── deployment/              # Pacotes de distribuição
└── tests/                   # Testes automatizados
```

## 🧪 Testes

```bash
# Executar todos os testes
python -m pytest tests/

# Testes específicos
python test_sgdk_fixes.py
python test_final_fixes.py
python test_deployment_package.py
```

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor:

1. **Fork** o repositório
2. **Crie** uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. **Commit** suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. **Push** para a branch (`git push origin feature/AmazingFeature`)
5. **Abra** um Pull Request

### Diretrizes
- Siga o estilo de código existente
- Adicione testes para novas funcionalidades
- Atualize a documentação
- Teste no Steam Deck se possível

## 📝 Changelog

### v2.0.0 (2025-08-08)
- ✅ **SGDK atualizado para versão 2.11**
- ✅ **Sistema de status persistente implementado**
- ✅ **Correção de falsos positivos na detecção**
- ✅ **Sincronização automática entre detecção e interface**
- ✅ **Sistema de deployment completo com PyInstaller**
- ✅ **Documentação abrangente**
- ✅ **Testes automatizados**

### v1.0.0 (2025-08-01)
- 🎉 Lançamento inicial
- 🔍 Sistema de detecção básico
- 🛠️ Instalação de componentes essenciais
- 🎮 Suporte inicial ao Steam Deck

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 🙏 Agradecimentos

- **Stephane-D** - Criador do SGDK
- **Comunidade Steam Deck** - Feedback e testes
- **Desenvolvedores Retro** - Inspiração e sugestões
- **Contribuidores** - Todas as contribuições valiosas

## 📞 Suporte

- 🐛 **Issues**: [GitHub Issues](https://github.com/Misael-art/EnvironmentDev_MISA/issues)
- 💬 **Discussões**: [GitHub Discussions](https://github.com/Misael-art/EnvironmentDev_MISA/discussions)
- 📧 **Email**: [Criar Issue](https://github.com/Misael-art/EnvironmentDev_MISA/issues/new)

---

<div align="center">

**Feito com ❤️ para a comunidade de desenvolvimento**

[⭐ Star este projeto](https://github.com/Misael-art/EnvironmentDev_MISA) se ele foi útil para você!

</div>