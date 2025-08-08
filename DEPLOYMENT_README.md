# Environment Dev Deep Evaluation - Deployment Guide

## 🚀 Guia Completo de Deployment

Este guia explica como criar um pacote de deployment completo do **Environment Dev Deep Evaluation** usando PyInstaller.

## 📋 Pré-requisitos

### Sistema
- **Python 3.8+** (recomendado: Python 3.11+)
- **Windows 10/11**, **Linux** ou **macOS**
- **2GB RAM** mínimo
- **5GB espaço livre** em disco (para build)

### Dependências
- PyInstaller 5.13.2+
- Pillow (PIL)
- PyYAML
- Requests
- psutil
- py7zr

## 🎯 Processo de Deployment

### Opção 1: Deployment Automático (Recomendado)

Execute o script master que faz tudo automaticamente:

```bash
python deploy_complete.py
```

Este script irá:
1. ✅ Verificar pré-requisitos
2. 📦 Instalar dependências necessárias
3. 🔨 Criar o executável com PyInstaller
4. 📁 Organizar o pacote completo
5. 🧪 Testar o pacote criado
6. 📊 Gerar relatório final

### Opção 2: Deployment Manual (Passo a Passo)

#### Passo 1: Instalar Dependências
```bash
python install_build_dependencies.py
```

#### Passo 2: Criar Pacote
```bash
python build_deployment.py
```

#### Passo 3: Testar Pacote
```bash
python test_deployment_package.py
```

### Opção 3: PyInstaller Direto

Para usuários avançados:

```bash
# Usando arquivo spec otimizado
pyinstaller environment_dev.spec

# Ou comando direto
pyinstaller --onedir --windowed --name "EnvironmentDevDeepEvaluation" main.py
```

## 📦 Estrutura do Pacote Final

```
EnvironmentDevDeepEvaluation_Portable/
├── EnvironmentDevDeepEvaluation/          # Executável principal
│   ├── EnvironmentDevDeepEvaluation.exe   # Executável Windows
│   ├── _internal/                         # Dependências internas
│   └── ...
├── config/                                # Configurações
│   └── components/                        # Componentes YAML
├── docs/                                  # Documentação completa
├── data/                                  # Dados iniciais
├── Iniciar_Environment_Dev.bat           # Launcher Windows
├── iniciar_environment_dev.sh            # Launcher Linux/Mac
├── LEIA-ME.txt                           # Instruções de uso
└── build_info.json                       # Informações do build
```

## 🎮 Como Usar o Pacote

### Windows
1. Extrair o pacote ZIP
2. Executar `Iniciar_Environment_Dev.bat`
3. Ou executar diretamente: `EnvironmentDevDeepEvaluation/EnvironmentDevDeepEvaluation.exe`

### Linux/Mac
1. Extrair o pacote ZIP
2. Dar permissão: `chmod +x iniciar_environment_dev.sh`
3. Executar: `./iniciar_environment_dev.sh`

## 🔧 Configurações Avançadas

### Personalizar Build

Edite o arquivo `environment_dev.spec` para:
- Adicionar/remover dependências
- Modificar ícone da aplicação
- Incluir arquivos adicionais
- Configurar compressão

### Otimizações

Para reduzir o tamanho do executável:

```python
# No arquivo .spec, adicione à lista excludes:
excludes=[
    'matplotlib', 'numpy', 'scipy', 'pandas',
    'jupyter', 'pytest', 'unittest'
]
```

### Build com UPX (Compressão)

Para executáveis menores:

```bash
# Instalar UPX
# Windows: baixar de https://upx.github.io/
# Linux: sudo apt install upx
# Mac: brew install upx

# Build com compressão
pyinstaller --upx-dir=/path/to/upx environment_dev.spec
```

## 🧪 Testes e Validação

### Testes Automáticos

O script `test_deployment_package.py` verifica:
- ✅ Estrutura do pacote
- ✅ Existência do executável
- ✅ Arquivos de configuração
- ✅ Documentação
- ✅ Scripts de inicialização
- ✅ Dependências

### Testes Manuais

1. **Teste de Inicialização**
   - Execute o launcher apropriado
   - Verifique se a GUI abre corretamente

2. **Teste de Funcionalidades**
   - Teste detecção de componentes
   - Teste instalação de um componente simples
   - Verifique logs e relatórios

3. **Teste de Portabilidade**
   - Copie o pacote para outro computador
   - Execute sem instalar Python
   - Verifique funcionamento completo

## 📊 Monitoramento e Logs

### Logs de Build
- `deployment/build_report_*.json` - Relatório do build
- `deployment_master_report_*.json` - Relatório completo

### Logs de Execução
- `logs/` - Logs da aplicação em execução
- Console do launcher - Mensagens de inicialização

## 🐛 Troubleshooting

### Problemas Comuns

#### "ModuleNotFoundError" no executável
```bash
# Adicionar ao hidden_imports no .spec:
hiddenimports=['modulo_ausente']
```

#### Executável muito grande
```bash
# Excluir módulos desnecessários no .spec:
excludes=['modulo_desnecessario']
```

#### Erro de permissão no Linux/Mac
```bash
chmod +x iniciar_environment_dev.sh
chmod +x EnvironmentDevDeepEvaluation/EnvironmentDevDeepEvaluation
```

#### Antivírus bloqueia executável
- Adicionar exceção no antivírus
- Usar certificado de código (para distribuição)

### Logs de Debug

Para debug detalhado:

```bash
# Build com debug
pyinstaller --debug=all environment_dev.spec

# Executar com console (Windows)
pyinstaller --console environment_dev.spec
```

## 📈 Otimizações de Performance

### Build Otimizado
- Use `--onedir` para inicialização mais rápida
- Use `--upx` para executáveis menores
- Exclua módulos desnecessários

### Runtime Otimizado
- Configure cache adequadamente
- Use threads para operações longas
- Otimize detecção de componentes

## 🔒 Segurança

### Assinatura de Código
Para distribuição profissional:

```bash
# Windows (com certificado)
signtool sign /f certificado.p12 /p senha EnvironmentDevDeepEvaluation.exe

# Mac (com certificado Apple)
codesign -s "Developer ID" EnvironmentDevDeepEvaluation
```

### Verificação de Integridade
- Gere hashes SHA256 do pacote
- Inclua checksums na distribuição
- Use HTTPS para downloads

## 📚 Recursos Adicionais

### Documentação
- [PyInstaller Manual](https://pyinstaller.readthedocs.io/)
- [Python Packaging Guide](https://packaging.python.org/)

### Ferramentas Úteis
- **auto-py-to-exe** - GUI para PyInstaller
- **cx_Freeze** - Alternativa ao PyInstaller
- **Nuitka** - Compilador Python

## 🤝 Contribuição

Para contribuir com melhorias no processo de deployment:

1. Fork o repositório
2. Crie branch para sua feature
3. Teste o deployment completo
4. Submeta pull request

## 📞 Suporte

Para problemas com deployment:
1. Verifique logs de build
2. Execute testes automáticos
3. Consulte troubleshooting
4. Abra issue no repositório

---

**Environment Dev Team** - 2025

*Este guia é atualizado regularmente. Verifique a versão mais recente no repositório.*