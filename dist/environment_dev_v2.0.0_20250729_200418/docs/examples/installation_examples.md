# Exemplos de Uso do Sistema de Instalação

Este documento contém exemplos práticos de uso do sistema de instalação do Environment Dev.

## Índice

1. [Instalação de Componentes Básicos](#instalação-de-componentes-básicos)
2. [Instalação com Dependências](#instalação-com-dependências)
3. [Verificação de Instalação](#verificação-de-instalação)
4. [Ações Pós-Instalação](#ações-pós-instalação)
5. [Tratamento de Erros](#tratamento-de-erros)
6. [Rollback Manual](#rollback-manual)
7. [Instalação de Componentes Complexos](#instalação-de-componentes-complexos)

## Instalação de Componentes Básicos

### Instalação de um Arquivo ZIP

```python
from env_dev.core.installer import install_component

# Definição do componente
component_data = {
    'install_method': 'download',
    'download_url': 'https://example.com/tools/utility.zip',
    'download_path': '%TEMP%\\downloads\\utility.zip',
    'extract_path': 'C:\\Program Files\\Utility',
    'file_hash': 'abcdef1234567890abcdef1234567890',  # SHA-256 hash
    'verify_actions': [
        {
            'type': 'directory_exists',
            'path': 'C:\\Program Files\\Utility'
        },
        {
            'type': 'file_exists',
            'path': 'C:\\Program Files\\Utility\\bin\\utility.exe'
        }
    ]
}

# Instalação do componente
try:
    result = install_component('Utility', component_data)
    if result:
        print("Utility instalado com sucesso!")
    else:
        print("Falha ao instalar Utility.")
except Exception as e:
    print(f"Erro durante a instalação: {e}")
```

### Instalação via Comando

```python
from env_dev.core.installer import install_component

# Definição do componente
component_data = {
    'install_method': 'command',
    'command': ['npm', 'install', '-g', 'package-name'],
    'working_dir': 'C:\\Projects',
    'verify_actions': [
        {
            'type': 'command_exists',
            'name': 'package-name'
        }
    ]
}

# Instalação do componente
try:
    result = install_component('NPM Package', component_data)
    if result:
        print("Pacote NPM instalado com sucesso!")
    else:
        print("Falha ao instalar pacote NPM.")
except Exception as e:
    print(f"Erro durante a instalação: {e}")
```

### Instalação de um Executável

```python
from env_dev.core.installer import install_component

# Definição do componente
component_data = {
    'install_method': 'download',
    'download_url': 'https://example.com/tools/installer.exe',
    'download_path': '%TEMP%\\downloads\\installer.exe',
    'run_after_download': True,
    'installer_args': ['/S', '/D=C:\\Program Files\\Tool'],
    'verify_actions': [
        {
            'type': 'directory_exists',
            'path': 'C:\\Program Files\\Tool'
        },
        {
            'type': 'registry_key_exists',
            'hive': 'HKLM',
            'path': 'SOFTWARE\\Tool'
        }
    ]
}

# Instalação do componente
try:
    result = install_component('Tool', component_data)
    if result:
        print("Tool instalado com sucesso!")
    else:
        print("Falha ao instalar Tool.")
except Exception as e:
    print(f"Erro durante a instalação: {e}")
```

## Instalação com Dependências

```python
from env_dev.core.installer import install_component

# Definição do componente principal
component_data = {
    'install_method': 'download',
    'download_url': 'https://example.com/tools/main-app.zip',
    'download_path': '%TEMP%\\downloads\\main-app.zip',
    'extract_path': 'C:\\Program Files\\MainApp',
    'dependencies': ['DotNetRuntime', 'VisualCppRedist'],
    'verify_actions': [
        {
            'type': 'file_exists',
            'path': 'C:\\Program Files\\MainApp\\main-app.exe'
        }
    ]
}

# Definição das dependências (normalmente em um arquivo de configuração)
dependencies = {
    'DotNetRuntime': {
        'install_method': 'download',
        'download_url': 'https://example.com/dotnet/runtime.exe',
        'download_path': '%TEMP%\\downloads\\dotnet-runtime.exe',
        'run_after_download': True,
        'installer_args': ['/quiet', '/norestart'],
        'verify_actions': [
            {
                'type': 'registry_key_exists',
                'hive': 'HKLM',
                'path': 'SOFTWARE\\Microsoft\\NET Framework Setup\\NDP\\v4\\Full'
            }
        ]
    },
    'VisualCppRedist': {
        'install_method': 'download',
        'download_url': 'https://example.com/vcredist/vcredist_x64.exe',
        'download_path': '%TEMP%\\downloads\\vcredist_x64.exe',
        'run_after_download': True,
        'installer_args': ['/quiet', '/norestart'],
        'verify_actions': [
            {
                'type': 'registry_key_exists',
                'hive': 'HKLM',
                'path': 'SOFTWARE\\Microsoft\\VisualStudio\\14.0\\VC\\Runtimes\\x64'
            }
        ]
    }
}

# Função para obter dados de componentes
def get_component_data(component_name):
    return dependencies.get(component_name)

# Patch da função get_component_data no módulo installer
import env_dev.core.installer
env_dev.core.installer.get_component_data = get_component_data

# Instalação do componente principal (que instalará as dependências)
try:
    result = install_component('MainApp', component_data)
    if result:
        print("MainApp e suas dependências instalados com sucesso!")
    else:
        print("Falha ao instalar MainApp.")
except Exception as e:
    print(f"Erro durante a instalação: {e}")
```

## Verificação de Instalação

### Verificações Avançadas

```python
from env_dev.core.installer import install_component

# Definição do componente com verificações avançadas
component_data = {
    'install_method': 'download',
    'download_url': 'https://example.com/tools/database.zip',
    'download_path': '%TEMP%\\downloads\\database.zip',
    'extract_path': 'C:\\Program Files\\Database',
    'verify_actions': [
        # Verifica se o diretório existe e tem pelo menos 10 arquivos
        {
            'type': 'directory_exists',
            'path': 'C:\\Program Files\\Database',
            'min_files': 10
        },
        # Verifica se o arquivo existe e tem pelo menos 1MB
        {
            'type': 'file_exists',
            'path': 'C:\\Program Files\\Database\\bin\\database.exe',
            'min_size': 1048576  # 1MB em bytes
        },
        # Verifica se o comando existe e tem a versão correta
        {
            'type': 'command_exists',
            'name': 'database',
            'version_command': '{cmd} --version',
            'expected_version': '2.1.0'
        },
        # Verifica se a variável de ambiente existe e tem o valor correto
        {
            'type': 'env_var_exists',
            'name': 'DATABASE_HOME',
            'expected_value': 'C:\\Program Files\\Database'
        },
        # Verifica se a chave de registro existe e tem o valor correto
        {
            'type': 'registry_key_exists',
            'hive': 'HKLM',
            'path': 'SOFTWARE\\Database',
            'value_name': 'Version',
            'expected_value': '2.1.0'
        },
        # Verifica se o comando retorna a saída esperada
        {
            'type': 'command_output',
            'command': 'database --status',
            'expected_contains': 'Database is running'
        }
    ]
}

# Instalação do componente
try:
    result = install_component('Database', component_data)
    if result:
        print("Database instalado e verificado com sucesso!")
    else:
        print("Falha ao instalar ou verificar Database.")
except Exception as e:
    print(f"Erro durante a instalação: {e}")
```

### Verificação Manual

```python
from env_dev.core.installer import _verify_installation

# Definição do componente
component_data = {
    'verify_actions': [
        {
            'type': 'file_exists',
            'path': 'C:\\Program Files\\App\\app.exe'
        },
        {
            'type': 'command_exists',
            'name': 'app'
        }
    ]
}

# Verificação manual
result = _verify_installation('App', component_data)
if result:
    print("App está instalado corretamente!")
else:
    print("App não está instalado ou está com problemas.")
```

## Ações Pós-Instalação

```python
from env_dev.core.installer import install_component

# Definição do componente com ações pós-instalação
component_data = {
    'install_method': 'download',
    'download_url': 'https://example.com/tools/app.zip',
    'download_path': '%TEMP%\\downloads\\app.zip',
    'extract_path': 'C:\\Program Files\\App',
    'post_install_actions': [
        # Limpeza de arquivos temporários
        {
            'type': 'cleanup',
            'paths': [
                '%TEMP%\\downloads\\app.zip',
                '%TEMP%\\app_installer_logs'
            ]
        },
        # Registro do componente instalado
        {
            'type': 'register',
            'registry_file': 'C:\\ProgramData\\installed_components.json'
        },
        # Notificação em arquivo de log
        {
            'type': 'notify',
            'target': 'log_file',
            'log_file': 'C:\\ProgramData\\installation.log',
            'message': 'App instalado em {timestamp}'
        },
        # Configuração de variáveis de ambiente
        {
            'type': 'set_env',
            'variable_name': 'APP_HOME',
            'value': 'C:\\Program Files\\App',
            'scope': 'user'
        },
        # Adição ao PATH
        {
            'type': 'add_to_path',
            'path': 'C:\\Program Files\\App\\bin',
            'scope': 'user'
        }
    ],
    'verify_actions': [
        {
            'type': 'file_exists',
            'path': 'C:\\Program Files\\App\\app.exe'
        }
    ]
}

# Instalação do componente
try:
    result = install_component('App', component_data)
    if result:
        print("App instalado com sucesso e ações pós-instalação executadas!")
    else:
        print("Falha ao instalar App.")
except Exception as e:
    print(f"Erro durante a instalação: {e}")
```

## Tratamento de Erros

```python
from env_dev.core.installer import install_component
from env_dev.utils.error_handler import EnvDevError, ErrorCategory, ErrorSeverity

# Definição do componente
component_data = {
    'install_method': 'download',
    'download_url': 'https://example.com/tools/app.zip',
    'download_path': '%TEMP%\\downloads\\app.zip',
    'extract_path': 'C:\\Program Files\\App'
}

# Instalação com tratamento de erros detalhado
try:
    result = install_component('App', component_data)
    if result:
        print("App instalado com sucesso!")
    else:
        print("Falha ao instalar App.")
except EnvDevError as e:
    # Tratamento específico por categoria de erro
    if e.category == ErrorCategory.NETWORK:
        print(f"Erro de rede durante a instalação: {e.message}")
        print(f"Verifique sua conexão e tente novamente.")
    elif e.category == ErrorCategory.PERMISSION:
        print(f"Erro de permissão: {e.message}")
        print(f"Execute o instalador como administrador.")
    elif e.category == ErrorCategory.DEPENDENCY:
        print(f"Erro de dependência: {e.message}")
        print(f"Instale as dependências manualmente e tente novamente.")
    elif e.category == ErrorCategory.INSTALLATION:
        print(f"Erro durante a instalação: {e.message}")
        print(f"Detalhes: {e.details}")
    else:
        print(f"Erro: {e.message}")
        
    # Tratamento por severidade
    if e.severity == ErrorSeverity.WARNING:
        print("Este é um aviso, a instalação pode estar incompleta.")
    elif e.severity == ErrorSeverity.ERROR:
        print("Este é um erro grave, a instalação falhou.")
    elif e.severity == ErrorSeverity.CRITICAL:
        print("Este é um erro crítico, o sistema pode estar instável.")
        
    # Log do erro
    e.log()
except Exception as e:
    print(f"Erro não categorizado: {e}")
```

## Rollback Manual

```python
from env_dev.core.installer import install_component
from env_dev.core.rollback_manager import RollbackManager

# Criação do gerenciador de rollback
rollback_mgr = RollbackManager()

# Definição do componente
component_data = {
    'install_method': 'download',
    'download_url': 'https://example.com/tools/app.zip',
    'download_path': '%TEMP%\\downloads\\app.zip',
    'extract_path': 'C:\\Program Files\\App'
}

# Início da transação
rollback_mgr.start_transaction('App')

try:
    # Registro manual de ações de rollback
    rollback_mgr.register_action({
        'undo_action': 'delete_path',
        'parameters': {'path': 'C:\\Program Files\\App'},
        'step': 'Extraction'
    })
    
    # Instalação do componente
    # Nota: Normalmente isso seria feito pelo install_component,
    # mas aqui mostramos como fazer manualmente para fins de exemplo
    
    # Simulação de erro
    if not os.path.exists('C:\\Program Files\\App\\config.ini'):
        raise Exception("Arquivo de configuração não encontrado!")
    
    # Se chegou aqui, a instalação foi bem-sucedida
    rollback_mgr.commit_transaction()
    print("App instalado com sucesso!")
    
except Exception as e:
    print(f"Erro durante a instalação: {e}")
    print("Iniciando rollback...")
    
    # Acionamento manual do rollback
    rollback_mgr.trigger_rollback()
    
    print("Rollback concluído.")
```

## Instalação de Componentes Complexos

### Instalação de um Banco de Dados

```python
from env_dev.core.installer import install_component

# Definição do componente de banco de dados
component_data = {
    'install_method': 'download',
    'download_url': 'https://example.com/database/installer.exe',
    'download_path': '%TEMP%\\downloads\\db_installer.exe',
    'run_after_download': True,
    'installer_args': [
        '/SILENT',
        '/COMPONENTS=server,client,tools',
        '/DIR=C:\\Program Files\\Database',
        '/SERVICENAME=DatabaseService',
        '/SERVICEACCOUNT=LocalSystem'
    ],
    'post_install_actions': [
        # Configuração inicial do banco
        {
            'type': 'run_script',
            'script_path': 'C:\\Program Files\\Database\\scripts\\init_db.sql',
            'script_type': 'sql',
            'connection_string': 'Server=localhost;User=admin;Password=admin;'
        },
        # Criação de usuário
        {
            'type': 'run_command',
            'command': [
                'C:\\Program Files\\Database\\bin\\db_admin.exe',
                'create_user',
                '--username', 'app_user',
                '--password', 'secure_password',
                '--role', 'app_role'
            ]
        },
        # Configuração de firewall
        {
            'type': 'run_command',
            'command': [
                'netsh', 'advfirewall', 'firewall', 'add', 'rule',
                'name=DatabasePort',
                'dir=in',
                'action=allow',
                'protocol=TCP',
                'localport=5432'
            ]
        }
    ],
    'verify_actions': [
        # Verifica se o serviço está instalado e em execução
        {
            'type': 'command_output',
            'command': 'sc query DatabaseService',
            'expected_contains': 'RUNNING'
        },
        # Verifica se a porta está aberta
        {
            'type': 'command_output',
            'command': 'netstat -an | findstr :5432',
            'expected_contains': 'LISTENING'
        },
        # Verifica se é possível conectar ao banco
        {
            'type': 'command_output',
            'command': 'C:\\Program Files\\Database\\bin\\db_client.exe --test-connection',
            'expected_contains': 'Connection successful'
        }
    ]
}

# Instalação do componente
try:
    result = install_component('Database', component_data)
    if result:
        print("Banco de dados instalado e configurado com sucesso!")
    else:
        print("Falha ao instalar o banco de dados.")
except Exception as e:
    print(f"Erro durante a instalação: {e}")
```

### Instalação de um Ambiente de Desenvolvimento Completo

```python
from env_dev.core.installer import install_component

# Definição do componente principal (ambiente de desenvolvimento)
component_data = {
    'install_method': 'meta',  # Componente meta que apenas agrupa dependências
    'dependencies': [
        'VSCode',
        'Python',
        'NodeJS',
        'Git',
        'Docker'
    ],
    'post_install_actions': [
        # Configuração global do Git
        {
            'type': 'run_command',
            'command': [
                'git', 'config', '--global', 'user.name', 'Developer'
            ]
        },
        {
            'type': 'run_command',
            'command': [
                'git', 'config', '--global', 'user.email', 'dev@example.com'
            ]
        },
        # Instalação de extensões do VSCode
        {
            'type': 'run_command',
            'command': [
                'code', '--install-extension', 'ms-python.python'
            ]
        },
        {
            'type': 'run_command',
            'command': [
                'code', '--install-extension', 'dbaeumer.vscode-eslint'
            ]
        },
        # Criação de ambiente virtual Python
        {
            'type': 'run_command',
            'command': [
                'python', '-m', 'venv', 'C:\\Dev\\venv'
            ]
        },
        # Instalação de pacotes npm globais
        {
            'type': 'run_command',
            'command': [
                'npm', 'install', '-g', 'eslint', 'prettier'
            ]
        }
    ],
    'verify_actions': [
        # Verifica se todos os componentes estão instalados
        {
            'type': 'command_exists',
            'name': 'code'
        },
        {
            'type': 'command_exists',
            'name': 'python'
        },
        {
            'type': 'command_exists',
            'name': 'node'
        },
        {
            'type': 'command_exists',
            'name': 'git'
        },
        {
            'type': 'command_exists',
            'name': 'docker'
        }
    ]
}

# Definição das dependências (normalmente em um arquivo de configuração)
dependencies = {
    'VSCode': {
        'install_method': 'download',
        'download_url': 'https://code.visualstudio.com/sha/download?build=stable&os=win32-x64',
        'download_path': '%TEMP%\\downloads\\vscode.exe',
        'run_after_download': True,
        'installer_args': ['/SILENT', '/MERGETASKS=!runcode'],
        'verify_actions': [
            {
                'type': 'command_exists',
                'name': 'code'
            }
        ]
    },
    'Python': {
        'install_method': 'download',
        'download_url': 'https://www.python.org/ftp/python/3.10.0/python-3.10.0-amd64.exe',
        'download_path': '%TEMP%\\downloads\\python.exe',
        'run_after_download': True,
        'installer_args': ['/quiet', 'InstallAllUsers=1', 'PrependPath=1'],
        'verify_actions': [
            {
                'type': 'command_exists',
                'name': 'python',
                'version_command': '{cmd} --version',
                'expected_version': '3.10'
            }
        ]
    },
    'NodeJS': {
        'install_method': 'download',
        'download_url': 'https://nodejs.org/dist/v16.13.0/node-v16.13.0-x64.msi',
        'download_path': '%TEMP%\\downloads\\node.msi',
        'run_after_download': True,
        'installer_args': ['/quiet', '/norestart'],
        'verify_actions': [
            {
                'type': 'command_exists',
                'name': 'node',
                'version_command': '{cmd} --version',
                'expected_version': 'v16'
            }
        ]
    },
    'Git': {
        'install_method': 'download',
        'download_url': 'https://github.com/git-for-windows/git/releases/download/v2.34.0.windows.1/Git-2.34.0-64-bit.exe',
        'download_path': '%TEMP%\\downloads\\git.exe',
        'run_after_download': True,
        'installer_args': ['/SILENT', '/COMPONENTS="icons,ext\\reg\\shellhere,assoc,assoc_sh"'],
        'verify_actions': [
            {
                'type': 'command_exists',
                'name': 'git',
                'version_command': '{cmd} --version',
                'expected_version': '2.34'
            }
        ]
    },
    'Docker': {
        'install_method': 'download',
        'download_url': 'https://desktop.docker.com/win/stable/Docker%20Desktop%20Installer.exe',
        'download_path': '%TEMP%\\downloads\\docker.exe',
        'run_after_download': True,
        'installer_args': ['install', '--quiet'],
        'verify_actions': [
            {
                'type': 'command_exists',
                'name': 'docker',
                'version_command': '{cmd} --version',
                'expected_version': 'Docker version'
            }
        ]
    }
}

# Função para obter dados de componentes
def get_component_data(component_name):
    return dependencies.get(component_name)

# Patch da função get_component_data no módulo installer
import env_dev.core.installer
env_dev.core.installer.get_component_data = get_component_data

# Instalação do ambiente de desenvolvimento completo
try:
    result = install_component('DevEnvironment', component_data)
    if result:
        print("Ambiente de desenvolvimento instalado com sucesso!")
    else:
        print("Falha ao instalar o ambiente de desenvolvimento.")
except Exception as e:
    print(f"Erro durante a instalação: {e}")
```

Estes exemplos demonstram como utilizar o sistema de instalação do Environment Dev para diferentes cenários, desde instalações simples até ambientes complexos com múltiplos componentes e configurações.
