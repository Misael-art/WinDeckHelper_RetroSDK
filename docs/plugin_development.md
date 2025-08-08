# Guia de Desenvolvimento de Plugins - Environment Dev

## Visão Geral

O sistema de plugins do Environment Dev permite estender as funcionalidades do sistema de forma segura e modular. Este guia aborda desde conceitos básicos até técnicas avançadas de desenvolvimento.

## Arquitetura de Plugins

### Conceitos Fundamentais

1. **Plugin Base**: Classe abstrata que define a interface comum
2. **Hooks**: Pontos de extensão no sistema principal
3. **Sandbox**: Ambiente isolado de execução
4. **Manifesto**: Arquivo de configuração do plugin
5. **Lifecycle**: Ciclo de vida do plugin (load → activate → deactivate → unload)

### Estrutura de um Plugin

```
my-plugin/
├── plugin.json          # Manifesto do plugin
├── __init__.py          # Ponto de entrada
├── main.py              # Lógica principal
├── requirements.txt     # Dependências Python
├── assets/              # Recursos estáticos
│   ├── icons/
│   └── templates/
├── tests/               # Testes do plugin
│   ├── test_main.py
│   └── fixtures/
└── docs/                # Documentação
    └── README.md
```

## Criando seu Primeiro Plugin

### 1. Manifesto do Plugin (plugin.json)

```json
{
  "name": "my-awesome-plugin",
  "version": "1.0.0",
  "description": "Um plugin incrível que faz coisas incríveis",
  "author": "Seu Nome",
  "email": "seu.email@exemplo.com",
  "license": "MIT",
  "homepage": "https://github.com/usuario/my-awesome-plugin",
  "repository": "https://github.com/usuario/my-awesome-plugin.git",
  "keywords": ["development", "automation", "utility"],
  
  "engine": {
    "environment_dev": ">=2.0.0"
  },
  
  "main": "main.py",
  "entry_point": "MyAwesomePlugin",
  
  "dependencies": {
    "python": ">=3.8",
    "packages": [
      "requests>=2.25.0",
      "click>=8.0.0"
    ]
  },
  
  "permissions": [
    "filesystem.read",
    "filesystem.write:/tmp",
    "network.http",
    "system.env_vars"
  ],
  
  "hooks": [
    "runtime.before_install",
    "runtime.after_install",
    "config.changed",
    "system.startup"
  ],
  
  "ui": {
    "has_settings": true,
    "has_dashboard": false,
    "menu_items": [
      {
        "label": "My Plugin Settings",
        "action": "open_settings",
        "icon": "assets/icons/settings.svg"
      }
    ]
  },
  
  "compatibility": {
    "platforms": ["windows", "linux", "macos"],
    "architectures": ["x86_64", "arm64"],
    "steamdeck": true
  }
}
```

### 2. Classe Principal do Plugin

```python
# main.py
from env_dev.plugin import BasePlugin, hook, setting
from env_dev.api import RuntimeAPI, ConfigAPI, UIAPI
from pathlib import Path
import logging
import requests

class MyAwesomePlugin(BasePlugin):
    """Plugin que demonstra funcionalidades básicas"""
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(f"plugin.{self.name}")
        
        # APIs disponíveis
        self.runtime_api = RuntimeAPI()
        self.config_api = ConfigAPI()
        self.ui_api = UIAPI()
        
        # Configurações do plugin
        self.settings = {
            'auto_backup': True,
            'backup_interval': 3600,
            'max_backups': 10
        }
    
    def activate(self):
        """Ativação do plugin"""
        self.logger.info("Ativando My Awesome Plugin")
        
        # Carregar configurações salvas
        self.load_settings()
        
        # Inicializar recursos
        self.init_backup_system()
        
        # Registrar comandos CLI
        self.register_cli_commands()
        
        self.logger.info("Plugin ativado com sucesso")
    
    def deactivate(self):
        """Desativação do plugin"""
        self.logger.info("Desativando My Awesome Plugin")
        
        # Salvar configurações
        self.save_settings()
        
        # Limpar recursos
        self.cleanup_resources()
        
        self.logger.info("Plugin desativado")
    
    # Hooks do sistema
    @hook('runtime.before_install')
    def before_runtime_install(self, runtime_info):
        """Executado antes da instalação de um runtime"""
        self.logger.info(f"Preparando instalação de {runtime_info.name}")
        
        if self.settings['auto_backup']:
            self.create_backup(f"before_install_{runtime_info.name}")
    
    @hook('runtime.after_install')
    def after_runtime_install(self, runtime_info, success):
        """Executado após a instalação de um runtime"""
        if success:
            self.logger.info(f"Runtime {runtime_info.name} instalado com sucesso")
            self.notify_user(f"✅ {runtime_info.name} instalado!")
        else:
            self.logger.error(f"Falha na instalação de {runtime_info.name}")
            self.notify_user(f"❌ Erro ao instalar {runtime_info.name}")
    
    @hook('config.changed')
    def on_config_changed(self, config_key, old_value, new_value):
        """Executado quando configuração muda"""
        self.logger.info(f"Configuração alterada: {config_key}")
        
        # Reagir a mudanças específicas
        if config_key.startswith('backup.'):
            self.update_backup_settings()
    
    @hook('system.startup')
    def on_system_startup(self):
        """Executado na inicialização do sistema"""
        self.logger.info("Sistema iniciado, verificando backups")
        self.check_backup_schedule()
    
    # Configurações do plugin
    @setting('auto_backup', bool, default=True)
    def auto_backup_setting(self, value):
        """Configuração para backup automático"""
        self.settings['auto_backup'] = value
        return value
    
    @setting('backup_interval', int, min_value=300, max_value=86400)
    def backup_interval_setting(self, value):
        """Intervalo entre backups em segundos"""
        self.settings['backup_interval'] = value
        self.reschedule_backups()
        return value
    
    # Métodos auxiliares
    def init_backup_system(self):
        """Inicializar sistema de backup"""
        backup_dir = self.get_data_dir() / "backups"
        backup_dir.mkdir(exist_ok=True)
        
        if self.settings['auto_backup']:
            self.schedule_backup()
    
    def create_backup(self, name):
        """Criar backup do sistema"""
        try:
            backup_path = self.get_data_dir() / "backups" / f"{name}.tar.gz"
            # Lógica de backup aqui
            self.logger.info(f"Backup criado: {backup_path}")
            return backup_path
        except Exception as e:
            self.logger.error(f"Erro ao criar backup: {e}")
            return None
    
    def notify_user(self, message):
        """Notificar usuário"""
        self.ui_api.show_notification(message, plugin=self.name)
    
    def register_cli_commands(self):
        """Registrar comandos CLI"""
        from env_dev.cli import register_command
        
        @register_command('backup', plugin=self.name)
        def backup_command(name=None):
            """Criar backup manual"""
            if not name:
                name = f"manual_{self.get_timestamp()}"
            
            backup_path = self.create_backup(name)
            if backup_path:
                print(f"Backup criado: {backup_path}")
            else:
                print("Erro ao criar backup")
        
        @register_command('list-backups', plugin=self.name)
        def list_backups_command():
            """Listar backups disponíveis"""
            backup_dir = self.get_data_dir() / "backups"
            backups = list(backup_dir.glob("*.tar.gz"))
            
            if backups:
                print("Backups disponíveis:")
                for backup in sorted(backups):
                    print(f"  - {backup.name}")
            else:
                print("Nenhum backup encontrado")
```

### 3. Interface de Configurações

```python
# settings_ui.py
from env_dev.ui import SettingsPanel, Field, Button, Label

class MyPluginSettings(SettingsPanel):
    """Interface de configurações do plugin"""
    
    def __init__(self, plugin):
        super().__init__()
        self.plugin = plugin
        self.build_ui()
    
    def build_ui(self):
        """Construir interface"""
        self.add_field(
            Field.checkbox(
                'auto_backup',
                label='Backup Automático',
                value=self.plugin.settings['auto_backup'],
                help_text='Criar backups automaticamente antes de operações importantes'
            )
        )
        
        self.add_field(
            Field.number(
                'backup_interval',
                label='Intervalo de Backup (segundos)',
                value=self.plugin.settings['backup_interval'],
                min_value=300,
                max_value=86400,
                help_text='Tempo entre backups automáticos'
            )
        )
        
        self.add_field(
            Field.number(
                'max_backups',
                label='Máximo de Backups',
                value=self.plugin.settings['max_backups'],
                min_value=1,
                max_value=100,
                help_text='Número máximo de backups a manter'
            )
        )
        
        self.add_button(
            Button(
                'create_backup',
                label='Criar Backup Agora',
                action=self.create_manual_backup,
                style='primary'
            )
        )
        
        self.add_button(
            Button(
                'clean_backups',
                label='Limpar Backups Antigos',
                action=self.clean_old_backups,
                style='secondary'
            )
        )
    
    def create_manual_backup(self):
        """Criar backup manual"""
        backup_path = self.plugin.create_backup(f"manual_{self.plugin.get_timestamp()}")
        if backup_path:
            self.show_success(f"Backup criado: {backup_path.name}")
        else:
            self.show_error("Erro ao criar backup")
    
    def clean_old_backups(self):
        """Limpar backups antigos"""
        cleaned = self.plugin.clean_old_backups()
        self.show_info(f"{cleaned} backups antigos removidos")
```

## APIs Disponíveis

### Runtime API

```python
from env_dev.api import RuntimeAPI

runtime_api = RuntimeAPI()

# Listar runtimes disponíveis
runtimes = runtime_api.list_available()

# Obter informações de um runtime
runtime_info = runtime_api.get_info('python-3.11')

# Instalar runtime
success = runtime_api.install('python-3.11', config='development')

# Verificar se runtime está instalado
is_installed = runtime_api.is_installed('python-3.11')

# Desinstalar runtime
runtime_api.uninstall('python-3.11')

# Buscar runtimes
results = runtime_api.search('python', category='language')
```

### Configuration API

```python
from env_dev.api import ConfigAPI

config_api = ConfigAPI()

# Obter configuração
value = config_api.get('general.auto_update')

# Definir configuração
config_api.set('general.auto_update', True)

# Obter configuração com valor padrão
value = config_api.get('my_plugin.setting', default='default_value')

# Listar todas as configurações
all_configs = config_api.list_all()

# Criar perfil de configuração
profile = config_api.create_profile('my-profile', {
    'runtime.preferred': 'python-3.11',
    'packages.auto_install': True
})

# Ativar perfil
config_api.activate_profile('my-profile')
```

### UI API

```python
from env_dev.api import UIAPI

ui_api = UIAPI()

# Mostrar notificação
ui_api.show_notification('Operação concluída!', type='success')

# Mostrar diálogo de confirmação
confirmed = ui_api.confirm('Deseja continuar?', 'Esta ação não pode ser desfeita')

# Solicitar entrada do usuário
user_input = ui_api.prompt('Digite o nome:', default='exemplo')

# Mostrar progresso
with ui_api.progress('Processando...') as progress:
    for i in range(100):
        progress.update(i, f'Processando item {i}')
        time.sleep(0.1)

# Abrir arquivo/diretório
ui_api.open_file('/path/to/file.txt')
ui_api.open_directory('/path/to/directory')
```

### File System API

```python
from env_dev.api import FileSystemAPI

fs_api = FileSystemAPI()

# Operações seguras de arquivo (respeitam sandbox)
fs_api.read_file('/allowed/path/file.txt')
fs_api.write_file('/allowed/path/output.txt', 'conteúdo')
fs_api.create_directory('/allowed/path/new_dir')

# Listar arquivos
files = fs_api.list_files('/allowed/path', pattern='*.py')

# Verificar permissões
can_read = fs_api.can_read('/some/path')
can_write = fs_api.can_write('/some/path')
```

### Network API

```python
from env_dev.api import NetworkAPI

net_api = NetworkAPI()

# Requisições HTTP (respeitam whitelist de domínios)
response = net_api.get('https://api.github.com/repos/user/repo')
data = net_api.post('https://api.example.com/data', json={'key': 'value'})

# Download de arquivos
net_api.download('https://example.com/file.zip', '/local/path/file.zip')

# Verificar conectividade
is_online = net_api.is_online()
can_reach = net_api.can_reach('github.com')
```

## Hooks Disponíveis

### Hooks de Runtime

```python
@hook('runtime.before_install')
def before_install(runtime_info):
    """Antes da instalação de runtime"""
    pass

@hook('runtime.after_install')
def after_install(runtime_info, success):
    """Após instalação de runtime"""
    pass

@hook('runtime.before_uninstall')
def before_uninstall(runtime_info):
    """Antes da desinstalação"""
    pass

@hook('runtime.after_uninstall')
def after_uninstall(runtime_info, success):
    """Após desinstalação"""
    pass

@hook('runtime.update_available')
def update_available(runtime_info, new_version):
    """Quando atualização está disponível"""
    pass
```

### Hooks de Configuração

```python
@hook('config.changed')
def config_changed(key, old_value, new_value):
    """Quando configuração muda"""
    pass

@hook('config.profile_activated')
def profile_activated(profile_name):
    """Quando perfil é ativado"""
    pass

@hook('config.profile_created')
def profile_created(profile_name, settings):
    """Quando perfil é criado"""
    pass
```

### Hooks de Sistema

```python
@hook('system.startup')
def system_startup():
    """Na inicialização do sistema"""
    pass

@hook('system.shutdown')
def system_shutdown():
    """No desligamento do sistema"""
    pass

@hook('system.error')
def system_error(error_info):
    """Quando erro ocorre no sistema"""
    pass

@hook('system.steamdeck_detected')
def steamdeck_detected(device_info):
    """Quando Steam Deck é detectado"""
    pass
```

### Hooks de Plugins

```python
@hook('plugin.loaded')
def plugin_loaded(plugin_name):
    """Quando plugin é carregado"""
    pass

@hook('plugin.activated')
def plugin_activated(plugin_name):
    """Quando plugin é ativado"""
    pass

@hook('plugin.deactivated')
def plugin_deactivated(plugin_name):
    """Quando plugin é desativado"""
    pass
```

## Sistema de Permissões

### Tipos de Permissões

```json
{
  "permissions": [
    // Sistema de arquivos
    "filesystem.read",                    // Leitura geral
    "filesystem.read:/specific/path",     // Leitura específica
    "filesystem.write",                   // Escrita geral
    "filesystem.write:/tmp",              // Escrita em diretório específico
    "filesystem.execute",                 // Execução de arquivos
    
    // Rede
    "network.http",                       // Requisições HTTP
    "network.https",                      // Requisições HTTPS
    "network.ftp",                        // Acesso FTP
    "network.domain:github.com",          // Domínio específico
    
    // Sistema
    "system.env_vars",                    // Variáveis de ambiente
    "system.processes",                   // Informações de processos
    "system.hardware",                    // Informações de hardware
    "system.registry",                    // Acesso ao registro (Windows)
    
    // Environment Dev
    "envdev.runtime.install",             // Instalar runtimes
    "envdev.runtime.uninstall",           // Desinstalar runtimes
    "envdev.config.read",                 // Ler configurações
    "envdev.config.write",                // Modificar configurações
    "envdev.plugins.manage",              // Gerenciar outros plugins
    
    // UI
    "ui.notifications",                   // Mostrar notificações
    "ui.dialogs",                         // Mostrar diálogos
    "ui.menu",                            // Adicionar itens ao menu
    "ui.dashboard"                        // Adicionar widgets ao dashboard
  ]
}
```

### Verificação de Permissões

```python
class MyPlugin(BasePlugin):
    def some_method(self):
        # Verificar permissão antes de usar
        if self.has_permission('filesystem.write:/tmp'):
            self.write_temp_file()
        else:
            self.logger.warning("Permissão negada para escrita em /tmp")
    
    def request_permission(self):
        # Solicitar permissão em tempo de execução
        granted = self.request_permission(
            'network.domain:api.example.com',
            reason='Necessário para sincronizar dados'
        )
        
        if granted:
            self.sync_data()
```

## Testes de Plugins

### Estrutura de Testes

```python
# tests/test_main.py
import pytest
from unittest.mock import Mock, patch
from env_dev.testing import PluginTestCase
from main import MyAwesomePlugin

class TestMyAwesomePlugin(PluginTestCase):
    """Testes para MyAwesomePlugin"""
    
    def setUp(self):
        """Configuração dos testes"""
        self.plugin = MyAwesomePlugin()
        self.plugin.activate()
    
    def tearDown(self):
        """Limpeza após testes"""
        self.plugin.deactivate()
    
    def test_activation(self):
        """Testar ativação do plugin"""
        self.assertTrue(self.plugin.is_active())
        self.assertIsNotNone(self.plugin.settings)
    
    def test_backup_creation(self):
        """Testar criação de backup"""
        with self.mock_filesystem():
            backup_path = self.plugin.create_backup('test_backup')
            self.assertIsNotNone(backup_path)
            self.assertTrue(backup_path.exists())
    
    @patch('requests.get')
    def test_network_request(self, mock_get):
        """Testar requisição de rede"""
        mock_get.return_value.json.return_value = {'status': 'ok'}
        
        result = self.plugin.check_remote_status()
        self.assertEqual(result['status'], 'ok')
    
    def test_hook_execution(self):
        """Testar execução de hooks"""
        runtime_info = Mock()
        runtime_info.name = 'test-runtime'
        
        # Simular hook
        self.plugin.before_runtime_install(runtime_info)
        
        # Verificar se backup foi criado
        self.assertTrue(self.plugin.backup_created)
    
    def test_settings_validation(self):
        """Testar validação de configurações"""
        # Configuração válida
        result = self.plugin.backup_interval_setting(3600)
        self.assertEqual(result, 3600)
        
        # Configuração inválida
        with self.assertRaises(ValueError):
            self.plugin.backup_interval_setting(100)  # Muito baixo
```

### Testes de Integração

```python
# tests/test_integration.py
import pytest
from env_dev.testing import IntegrationTestCase
from main import MyAwesomePlugin

class TestPluginIntegration(IntegrationTestCase):
    """Testes de integração com o sistema"""
    
    def test_full_workflow(self):
        """Testar fluxo completo"""
        # Ativar plugin
        plugin = MyAwesomePlugin()
        plugin.activate()
        
        # Simular instalação de runtime
        runtime_info = self.create_test_runtime('python-3.11')
        
        # Verificar se hooks são executados
        with self.capture_hooks() as hooks:
            self.runtime_manager.install(runtime_info)
        
        # Verificar se plugin reagiu corretamente
        self.assertIn('runtime.before_install', hooks)
        self.assertIn('runtime.after_install', hooks)
        
        # Verificar se backup foi criado
        backups = list(plugin.get_data_dir().glob('backups/*.tar.gz'))
        self.assertGreater(len(backups), 0)
    
    def test_permission_enforcement(self):
        """Testar aplicação de permissões"""
        plugin = MyAwesomePlugin()
        
        # Tentar operação sem permissão
        with self.deny_permission('filesystem.write:/restricted'):
            result = plugin.write_restricted_file()
            self.assertFalse(result)
        
        # Tentar operação com permissão
        with self.grant_permission('filesystem.write:/tmp'):
            result = plugin.write_temp_file()
            self.assertTrue(result)
```

## Distribuição de Plugins

### Empacotamento

```bash
# Criar pacote do plugin
env_dev plugin package my-plugin/

# Gerar arquivo .envdev-plugin
env_dev plugin build my-plugin/ --output my-plugin-1.0.0.envdev-plugin

# Validar pacote
env_dev plugin validate my-plugin-1.0.0.envdev-plugin
```

### Publicação

```bash
# Publicar no repositório oficial
env_dev plugin publish my-plugin-1.0.0.envdev-plugin --repo official

# Publicar em repositório personalizado
env_dev plugin publish my-plugin-1.0.0.envdev-plugin --repo https://my-repo.com/plugins

# Gerar assinatura digital
env_dev plugin sign my-plugin-1.0.0.envdev-plugin --key my-key.pem
```

### Instalação

```bash
# Instalar do repositório
env_dev plugin install my-awesome-plugin

# Instalar arquivo local
env_dev plugin install my-plugin-1.0.0.envdev-plugin

# Instalar do GitHub
env_dev plugin install github:usuario/my-plugin

# Instalar versão específica
env_dev plugin install my-awesome-plugin@1.0.0
```

## Boas Práticas

### Segurança

1. **Princípio do Menor Privilégio**:
   - Solicite apenas as permissões necessárias
   - Valide todas as entradas do usuário
   - Use APIs fornecidas em vez de acesso direto

2. **Tratamento de Erros**:
   ```python
   try:
       result = self.risky_operation()
   except PermissionError:
       self.logger.warning("Permissão negada")
       return None
   except Exception as e:
       self.logger.error(f"Erro inesperado: {e}")
       self.report_error(e)
       return None
   ```

3. **Validação de Dados**:
   ```python
   def validate_input(self, data):
       if not isinstance(data, dict):
           raise ValueError("Dados devem ser um dicionário")
       
       required_fields = ['name', 'version']
       for field in required_fields:
           if field not in data:
               raise ValueError(f"Campo obrigatório: {field}")
       
       return True
   ```

### Performance

1. **Operações Assíncronas**:
   ```python
   import asyncio
   
   async def long_running_task(self):
       """Operação demorada em background"""
       await asyncio.sleep(1)  # Simular trabalho
       return "resultado"
   
   def start_background_task(self):
       """Iniciar tarefa em background"""
       task = asyncio.create_task(self.long_running_task())
       task.add_done_callback(self.on_task_complete)
   ```

2. **Cache Inteligente**:
   ```python
   from functools import lru_cache
   
   @lru_cache(maxsize=128)
   def expensive_computation(self, param):
       """Computação cara com cache"""
       # Lógica complexa aqui
       return result
   ```

3. **Lazy Loading**:
   ```python
   def __init__(self):
       self._heavy_resource = None
   
   @property
   def heavy_resource(self):
       if self._heavy_resource is None:
           self._heavy_resource = self.load_heavy_resource()
       return self._heavy_resource
   ```

### Usabilidade

1. **Mensagens Claras**:
   ```python
   def install_dependency(self, package):
       try:
           self.package_manager.install(package)
           self.notify_user(f"✅ {package} instalado com sucesso")
       except Exception as e:
           self.notify_user(
               f"❌ Erro ao instalar {package}: {str(e)}",
               type='error',
               actions=[{
                   'label': 'Tentar Novamente',
                   'action': lambda: self.install_dependency(package)
               }]
           )
   ```

2. **Configurações Intuitivas**:
   ```python
   def get_settings_schema(self):
       return {
           'auto_backup': {
               'type': 'boolean',
               'default': True,
               'title': 'Backup Automático',
               'description': 'Criar backups automaticamente antes de operações importantes'
           },
           'backup_interval': {
               'type': 'integer',
               'default': 3600,
               'minimum': 300,
               'maximum': 86400,
               'title': 'Intervalo de Backup',
               'description': 'Tempo entre backups em segundos',
               'unit': 'segundos'
           }
       }
   ```

### Compatibilidade

1. **Detecção de Plataforma**:
   ```python
   import platform
   
   def is_compatible(self):
       system = platform.system().lower()
       arch = platform.machine().lower()
       
       supported_systems = self.manifest['compatibility']['platforms']
       supported_archs = self.manifest['compatibility']['architectures']
       
       return system in supported_systems and arch in supported_archs
   ```

2. **Versionamento Semântico**:
   ```python
   def check_engine_compatibility(self):
       required_version = self.manifest['engine']['environment_dev']
       current_version = self.get_engine_version()
       
       return self.version_satisfies(current_version, required_version)
   ```

## Exemplos Avançados

### Plugin de Integração com Docker

```python
# docker_integration.py
class DockerIntegrationPlugin(BasePlugin):
    """Plugin para integração com Docker"""
    
    def activate(self):
        self.docker_client = self.init_docker_client()
        self.register_runtime_provider()
    
    def init_docker_client(self):
        """Inicializar cliente Docker"""
        try:
            import docker
            return docker.from_env()
        except Exception as e:
            self.logger.error(f"Docker não disponível: {e}")
            return None
    
    def register_runtime_provider(self):
        """Registrar como provedor de runtimes"""
        self.runtime_api.register_provider(
            name='docker',
            provider=self,
            priority=50
        )
    
    def list_available_runtimes(self):
        """Listar runtimes Docker disponíveis"""
        if not self.docker_client:
            return []
        
        runtimes = []
        
        # Imagens populares
        popular_images = [
            'python:3.11', 'node:18', 'golang:1.21',
            'openjdk:17', 'ruby:3.2', 'php:8.2'
        ]
        
        for image in popular_images:
            runtime_info = self.create_docker_runtime_info(image)
            runtimes.append(runtime_info)
        
        return runtimes
    
    def install_runtime(self, runtime_info):
        """Instalar runtime Docker"""
        try:
            image_name = runtime_info.docker_image
            self.docker_client.images.pull(image_name)
            
            # Criar container de desenvolvimento
            container = self.docker_client.containers.create(
                image_name,
                name=f"envdev-{runtime_info.name}",
                detach=True,
                volumes={
                    str(Path.home()): {'bind': '/workspace', 'mode': 'rw'}
                },
                working_dir='/workspace'
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao instalar runtime Docker: {e}")
            return False
    
    @hook('runtime.execute')
    def execute_in_container(self, runtime_name, command):
        """Executar comando em container"""
        container_name = f"envdev-{runtime_name}"
        
        try:
            container = self.docker_client.containers.get(container_name)
            
            if container.status != 'running':
                container.start()
            
            result = container.exec_run(command)
            return result.output.decode()
            
        except Exception as e:
            self.logger.error(f"Erro ao executar comando: {e}")
            return None
```

### Plugin de Monitoramento de Performance

```python
# performance_monitor.py
import psutil
import time
from threading import Thread

class PerformanceMonitorPlugin(BasePlugin):
    """Plugin para monitoramento de performance"""
    
    def activate(self):
        self.monitoring = True
        self.metrics = []
        self.monitor_thread = Thread(target=self.monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        # Registrar widget no dashboard
        self.ui_api.register_dashboard_widget(
            'performance_monitor',
            self.create_performance_widget()
        )
    
    def deactivate(self):
        self.monitoring = False
        if self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
    
    def monitor_loop(self):
        """Loop de monitoramento"""
        while self.monitoring:
            metrics = self.collect_metrics()
            self.metrics.append(metrics)
            
            # Manter apenas últimas 100 medições
            if len(self.metrics) > 100:
                self.metrics.pop(0)
            
            # Verificar alertas
            self.check_alerts(metrics)
            
            time.sleep(5)  # Coletar a cada 5 segundos
    
    def collect_metrics(self):
        """Coletar métricas do sistema"""
        return {
            'timestamp': time.time(),
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent,
            'network_io': psutil.net_io_counters()._asdict(),
            'processes': len(psutil.pids())
        }
    
    def check_alerts(self, metrics):
        """Verificar condições de alerta"""
        if metrics['cpu_percent'] > 90:
            self.ui_api.show_notification(
                '⚠️ CPU usage high: {:.1f}%'.format(metrics['cpu_percent']),
                type='warning'
            )
        
        if metrics['memory_percent'] > 85:
            self.ui_api.show_notification(
                '⚠️ Memory usage high: {:.1f}%'.format(metrics['memory_percent']),
                type='warning'
            )
    
    def create_performance_widget(self):
        """Criar widget de performance"""
        return {
            'title': 'System Performance',
            'type': 'chart',
            'data_source': self.get_chart_data,
            'refresh_interval': 5000,  # 5 segundos
            'chart_type': 'line',
            'height': 200
        }
    
    def get_chart_data(self):
        """Obter dados para o gráfico"""
        if not self.metrics:
            return {'labels': [], 'datasets': []}
        
        labels = []
        cpu_data = []
        memory_data = []
        
        for metric in self.metrics[-20:]:  # Últimos 20 pontos
            timestamp = metric['timestamp']
            labels.append(time.strftime('%H:%M:%S', time.localtime(timestamp)))
            cpu_data.append(metric['cpu_percent'])
            memory_data.append(metric['memory_percent'])
        
        return {
            'labels': labels,
            'datasets': [
                {
                    'label': 'CPU %',
                    'data': cpu_data,
                    'borderColor': 'rgb(255, 99, 132)',
                    'backgroundColor': 'rgba(255, 99, 132, 0.2)'
                },
                {
                    'label': 'Memory %',
                    'data': memory_data,
                    'borderColor': 'rgb(54, 162, 235)',
                    'backgroundColor': 'rgba(54, 162, 235, 0.2)'
                }
            ]
        }
```

## Depuração de Plugins

### Logging Avançado

```python
import logging
from env_dev.logging import PluginLogger

class MyPlugin(BasePlugin):
    def __init__(self):
        super().__init__()
        
        # Logger específico do plugin
        self.logger = PluginLogger(self.name)
        
        # Configurar níveis diferentes para diferentes módulos
        self.logger.set_level('network', logging.DEBUG)
        self.logger.set_level('filesystem', logging.INFO)
    
    def complex_operation(self):
        """Operação complexa com logging detalhado"""
        with self.logger.context('complex_operation'):
            self.logger.info("Iniciando operação complexa")
            
            try:
                # Etapa 1
                with self.logger.timer('step1'):
                    self.logger.debug("Executando etapa 1")
                    result1 = self.step1()
                    self.logger.debug(f"Resultado etapa 1: {result1}")
                
                # Etapa 2
                with self.logger.timer('step2'):
                    self.logger.debug("Executando etapa 2")
                    result2 = self.step2(result1)
                    self.logger.debug(f"Resultado etapa 2: {result2}")
                
                self.logger.info("Operação concluída com sucesso")
                return result2
                
            except Exception as e:
                self.logger.error(f"Erro na operação: {e}", exc_info=True)
                raise
```

### Ferramentas de Debug

```python
from env_dev.debug import PluginDebugger

class MyPlugin(BasePlugin):
    def __init__(self):
        super().__init__()
        
        # Ativar debugger em modo desenvolvimento
        if self.is_development_mode():
            self.debugger = PluginDebugger(self)
            self.debugger.enable()
    
    def problematic_method(self):
        """Método com problemas"""
        # Breakpoint condicional
        if self.debugger and self.some_condition():
            self.debugger.breakpoint()
        
        # Trace de execução
        with self.debugger.trace('problematic_method'):
            result = self.do_something()
            
            # Inspecionar variáveis
            self.debugger.inspect({
                'result': result,
                'self.state': self.state
            })
            
            return result
```

## Recursos Adicionais

### Documentação

- [API Reference](api_reference.md)
- [Plugin Examples](https://github.com/environment-dev/plugin-examples)
- [Best Practices Guide](best_practices.md)
- [Security Guidelines](security_guidelines.md)

### Ferramentas

- **Plugin Generator**: `env_dev plugin create --template basic`
- **Plugin Validator**: `env_dev plugin validate`
- **Plugin Debugger**: `env_dev plugin debug`
- **Plugin Profiler**: `env_dev plugin profile`

### Comunidade

- **Discord**: https://discord.gg/environment-dev-plugins
- **Forum**: https://forum.environment-dev.org/plugins
- **GitHub Discussions**: https://github.com/environment-dev/core/discussions

### Suporte

- **Plugin Development Support**: plugins@environment-dev.org
- **Bug Reports**: https://github.com/environment-dev/core/issues
- **Feature Requests**: https://github.com/environment-dev/core/discussions/categories/ideas