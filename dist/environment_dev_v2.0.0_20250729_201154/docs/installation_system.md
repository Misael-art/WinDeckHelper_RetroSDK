# Sistema de Instalação do Environment Dev

Este documento descreve o sistema de instalação do Environment Dev, incluindo suas funcionalidades, arquitetura e exemplos de uso.

## Visão Geral

O sistema de instalação do Environment Dev é responsável por gerenciar a instalação de componentes de software, fornecendo recursos como:

- Instalação de diferentes tipos de componentes (download, command, etc.)
- Gerenciamento de dependências
- Verificação de instalação
- Rollback em caso de falha
- Feedback detalhado de status
- Ações pós-instalação

## Arquitetura

O sistema de instalação é composto pelos seguintes módulos principais:

### 1. Installer (`env_dev/core/installer.py`)

Módulo principal que contém as funções de instalação de componentes:

- `install_component`: Instala um componente, gerenciando dependências e verificação
- `install_download_type`: Instala componentes do tipo download (arquivos, executáveis, etc.)
- `install_command_type`: Instala componentes do tipo command (comandos de linha de comando)
- `_verify_installation`: Verifica se um componente foi instalado corretamente
- `_handle_post_install`: Executa ações pós-instalação

### 2. RollbackManager (`env_dev/core/rollback_manager.py`)

Gerencia o rollback de ações em caso de falha na instalação:

- `start_transaction`: Inicia uma transação de rollback
- `register_action`: Registra uma ação de undo
- `trigger_rollback`: Aciona o rollback em caso de falha
- `commit_transaction`: Confirma a transação (instalação bem-sucedida)

### 3. Módulos Utilitários

- `downloader`: Gerencia o download de arquivos
- `extractor`: Gerencia a extração de arquivos
- `installer_runner`: Gerencia a execução de instaladores
- `env_manager`: Gerencia variáveis de ambiente
- `env_checker`: Verifica o ambiente (registro, comandos, etc.)
- `error_handler`: Gerencia erros e exceções

## Fluxo de Instalação

O fluxo de instalação de um componente segue os seguintes passos:

1. **Verificação Inicial**: Verifica se o componente já está instalado
2. **Instalação de Dependências**: Instala as dependências do componente
3. **Instalação do Componente**: Instala o componente de acordo com seu tipo
4. **Ações Pós-Instalação**: Executa ações pós-instalação (registro, limpeza, etc.)
5. **Verificação Final**: Verifica se o componente foi instalado corretamente

Em caso de falha em qualquer etapa, o sistema aciona o rollback para desfazer as ações realizadas.

## Sistema de Rollback

O sistema de rollback é responsável por desfazer as ações realizadas durante a instalação em caso de falha. Ele funciona da seguinte forma:

1. Antes de cada ação que modifica o sistema, registra-se uma ação de undo correspondente
2. Em caso de falha, as ações de undo são executadas em ordem reversa (LIFO)
3. O sistema fornece feedback detalhado sobre o progresso do rollback

### Tipos de Ações de Undo

- `delete_path`: Remove um arquivo ou diretório
- `run_command`: Executa um comando (ex: desinstalador)
- `run_script`: Executa um script
- `restore_env`: Restaura uma variável de ambiente
- `unset_env`: Remove uma variável de ambiente
- `remove_path`: Remove um caminho do PATH
- `modify_json`: Modifica um arquivo JSON

## Sistema de Verificação

O sistema de verificação é responsável por verificar se um componente foi instalado corretamente. Ele suporta os seguintes tipos de verificação:

- `file_exists`: Verifica se um arquivo existe
- `directory_exists`: Verifica se um diretório existe
- `env_var_exists`: Verifica se uma variável de ambiente existe
- `command_exists`: Verifica se um comando existe
- `registry_key_exists`: Verifica se uma chave de registro existe
- `command_output`: Verifica a saída de um comando

Cada tipo de verificação pode ter verificações adicionais, como:

- Tamanho mínimo de arquivo
- Número mínimo de arquivos em um diretório
- Valor esperado de uma variável de ambiente
- Versão esperada de um comando
- Valor esperado de uma chave de registro

## Sistema de Feedback

O sistema de feedback é responsável por fornecer informações detalhadas sobre o progresso da instalação. Ele suporta os seguintes tipos de mensagens:

- `stage`: Indica a etapa atual da instalação
- `progress`: Indica o progresso da instalação (porcentagem)
- `log`: Registra uma mensagem de log
- `result`: Indica o resultado da instalação
- `error`: Indica um erro durante a instalação
- `rollback`: Indica o progresso do rollback
- `verification_result`: Indica o resultado da verificação

## Exemplos de Uso

### Instalação de um Componente Simples

```python
from env_dev.core.installer import install_component

component_data = {
    'install_method': 'download',
    'download_url': 'http://example.com/test.zip',
    'extract_path': 'C:\\Program Files\\Test',
    'verify_actions': [
        {
            'type': 'directory_exists',
            'path': 'C:\\Program Files\\Test'
        }
    ]
}

result = install_component('TestComponent', component_data)
```

### Instalação de um Componente com Dependências

```python
component_data = {
    'install_method': 'download',
    'download_url': 'http://example.com/test.zip',
    'extract_path': 'C:\\Program Files\\Test',
    'dependencies': ['Dependency1', 'Dependency2'],
    'verify_actions': [
        {
            'type': 'directory_exists',
            'path': 'C:\\Program Files\\Test'
        }
    ]
}

result = install_component('TestComponent', component_data)
```

### Instalação de um Componente com Ações Pós-Instalação

```python
component_data = {
    'install_method': 'download',
    'download_url': 'http://example.com/test.zip',
    'extract_path': 'C:\\Program Files\\Test',
    'post_install_actions': [
        {
            'type': 'cleanup',
            'paths': ['C:\\Temp\\test.zip']
        },
        {
            'type': 'register',
            'registry_file': 'C:\\ProgramData\\installed_components.json'
        }
    ],
    'verify_actions': [
        {
            'type': 'directory_exists',
            'path': 'C:\\Program Files\\Test'
        }
    ]
}

result = install_component('TestComponent', component_data)
```

## Melhores Práticas

### Definição de Componentes

- Sempre defina ações de verificação para seus componentes
- Use dependências para garantir que os componentes sejam instalados na ordem correta
- Defina ações pós-instalação para limpeza e registro

### Tratamento de Erros

- Sempre verifique o resultado da instalação
- Trate os erros de forma adequada
- Use o sistema de categorização de erros para fornecer mensagens úteis

### Verificação

- Defina verificações específicas para cada componente
- Use verificações adicionais para garantir que o componente foi instalado corretamente
- Verifique não apenas a existência, mas também a funcionalidade do componente

## Referência de API

### `install_component(component_name, component_data, force_install=False, visiting=None, rollback_mgr=None, progress_callback=None)`

Instala um componente, gerenciando dependências e verificação.

**Parâmetros:**
- `component_name`: Nome do componente
- `component_data`: Dados do componente
- `force_install`: Se True, força a instalação mesmo se o componente já estiver instalado
- `visiting`: Conjunto de componentes sendo visitados (para detecção de ciclos)
- `rollback_mgr`: Instância do RollbackManager
- `progress_callback`: Função de callback para progresso

**Retorna:**
- `bool`: True se a instalação foi bem-sucedida, False caso contrário

### `_verify_installation(component_name, component_data, log_level=logging.INFO)`

Verifica se um componente foi instalado corretamente.

**Parâmetros:**
- `component_name`: Nome do componente
- `component_data`: Dados do componente
- `log_level`: Nível de log para mensagens de sucesso

**Retorna:**
- `bool`: True se todas as verificações passarem, False caso contrário

### `_handle_post_install(component_name, component_data, rollback_mgr)`

Executa ações pós-instalação para um componente.

**Parâmetros:**
- `component_name`: Nome do componente
- `component_data`: Dados do componente
- `rollback_mgr`: Instância do RollbackManager

**Retorna:**
- `bool`: True se todas as ações pós-instalação foram bem-sucedidas, False caso contrário

### `RollbackManager`

#### `start_transaction(component_name)`

Inicia uma transação de rollback para um componente específico.

**Parâmetros:**
- `component_name`: Nome do componente

#### `register_action(undo_operation)`

Registra uma operação de undo na pilha.

**Parâmetros:**
- `undo_operation`: Dicionário descrevendo a ação de undo

#### `trigger_rollback()`

Inicia o processo de rollback, executando as ações de undo registradas em ordem reversa.

#### `commit_transaction()`

Confirma a transação atual, indicando que a instalação foi bem-sucedida.

## Conclusão

O sistema de instalação do Environment Dev fornece uma solução robusta para a instalação de componentes de software, com recursos avançados como gerenciamento de dependências, verificação de instalação, rollback em caso de falha e feedback detalhado de status.

Ao seguir as melhores práticas e utilizar os recursos disponíveis, é possível criar instalações confiáveis e resilientes para seus componentes.
