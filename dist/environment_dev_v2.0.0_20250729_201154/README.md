# Environment Dev - Instalador Modular

Um instalador modular para configuração de ambientes de desenvolvimento para PC Engines, com suporte a rollback, verificação de instalação e feedback detalhado de status.

## 🚀 Principais Recursos

- **Sistema de Instalação Real**: Downloads e instalações reais de componentes (não simulações)
- **Interface Gráfica Moderna**: Dashboard interativo com feedback em tempo real
- **Sistema de Rollback**: Desfaz instalações em caso de falha
- **Verificação de Instalação**: Confirma se os componentes foram instalados corretamente
- **Gerenciamento de Dependências**: Instalação automática de dependências na ordem correta
- **Progresso em Tempo Real**: Barras de progresso e logs detalhados durante instalações
- **86+ Componentes**: Ampla biblioteca de ferramentas para desenvolvimento
- **Categorização de Erros**: Sistema robusto de tratamento e categorização de erros
- **Sistema de Mirrors**: Fallback automático para URLs alternativas
- **Verificação de Espaço**: Confirma espaço em disco antes dos downloads

## ✨ Novidades da Versão Atual

### 🔧 Correções Críticas Implementadas
- **Instalações Reais**: Removidas todas as simulações - agora faz downloads e instalações reais
- **GUI Corrigida**: Interface gráfica agora chama funções reais de instalação
- **Downloads Funcionais**: Sistema de download completamente funcional com progresso real
- **Diagnósticos Reais**: Verificações de sistema agora executam diagnósticos reais

### 📊 Componentes Testados e Funcionais
- **CCleaner** (instalação manual): ✅ Funcional
- **Game Fire** (download automático): ✅ Download testado
- **Anaconda, LM Studio, NVIDIA CUDA**: ✅ Configurados para instalação automática
- **86 componentes** carregados e validados

## Estrutura do Projeto

```
environment_dev_script/
├── env_dev/                 # Código principal do instalador
│   ├── config/              # Configurações e definições
│   ├── core/                # Funcionalidade principal
│   ├── gui/                 # Interface gráfica
│   ├── utils/               # Utilitários e funções auxiliares
│   └── main.py              # Ponto de entrada do módulo
├── docs/                    # Documentação
├── logs/                    # Diretório para logs
├── downloads/               # Diretório para downloads
├── resources/               # Recursos e arquivos estáticos
├── legacy/                  # Código legado (PowerShell)
├── environment_dev.py       # Script de inicialização
└── README.md                # Documentação principal
```

## Requisitos

- Python 3.8+
- Windows 10/11
- Conexão com a internet (para componentes online)

## Instalação

1. Clone o repositório:
   ```
   git clone https://github.com/seu-usuario/environment_dev_script.git
   cd environment_dev_script
   ```

2. Crie um ambiente virtual (opcional, mas recomendado):
   ```
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. Instale as dependências:
   ```
   pip install -r env_dev/requirements.txt
   ```

## 🎯 Uso Rápido

### Interface Gráfica (Recomendado)

Execute o script principal para iniciar o dashboard interativo:

```bash
python env_dev/main.py
```

**Recursos da GUI:**
- 📊 Dashboard com status em tempo real
- 📈 Barras de progresso durante downloads
- 🔍 Sistema de diagnósticos integrado
- 📝 Logs detalhados em tempo real
- ⚙️ Seleção múltipla de componentes

### Linha de Comando

Para listar todos os componentes disponíveis:

```bash
python env_dev/main.py --list
```

Para instalar componentes específicos:

```bash
python env_dev/main.py --install "Game Fire" "Process Lasso"
```

Para executar diagnósticos do sistema:

```bash
python env_dev/main.py --check-env
```

### 🧪 Testes de Validação

Execute os testes para verificar se tudo está funcionando:

```bash
# Teste básico do sistema
python test_installation_fix.py

# Teste completo de download
python test_real_download_installation.py
```

### Opções Adicionais

- `--no-gui`: Força o modo de linha de comando
- `--check-env`: Verifica o ambiente e dependências
- `--log-level`: Define o nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `--rollback`: Ativa o modo de rollback para desfazer instalações anteriores
- `--verify-only`: Apenas verifica se os componentes estão instalados corretamente

## Sistema de Instalação

O Environment Dev possui um sistema de instalação robusto com suporte a rollback, verificação de instalação e feedback detalhado de status. Para mais informações, consulte a [documentação do sistema de instalação](docs/installation_system.md).

### Exemplos de Uso

```python
from env_dev.core.installer import install_component

# Definição do componente
component_data = {
    'install_method': 'download',
    'download_url': 'https://example.com/tools/utility.zip',
    'extract_path': 'C:\\Program Files\\Utility',
    'verify_actions': [
        {
            'type': 'file_exists',
            'path': 'C:\\Program Files\\Utility\\bin\\utility.exe'
        }
    ]
}

# Instalação do componente
result = install_component('Utility', component_data)
```

Para mais exemplos, consulte a [documentação de exemplos](docs/examples/installation_examples.md).

## Logs e Testes

O Environment Dev Script inclui logs detalhados e testes abrangentes para garantir o funcionamento correto do script.

### Logs Detalhados

Os logs são armazenados no diretório `logs` e incluem informações sobre a inicialização da interface gráfica, a instalação de componentes e outras operações importantes. Para mais informações, consulte a [documentação de logs e testes](docs/logs_and_tests.md).

### Testes

Para executar todos os testes:

```
python -m unittest discover tests
```

Para executar testes específicos:

```
python -m unittest tests.test_clover_scenarios
python -m unittest tests.test_gui_initialization
```

Os testes incluem:

- Testes da interface gráfica
- Testes da instalação do Clover
- Testes de cenários com diferentes configurações
- Testes de tratamento de erros

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo LICENSE para mais detalhes.
