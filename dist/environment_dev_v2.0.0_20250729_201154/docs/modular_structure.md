# Estrutura Modular do Environment Dev Script

## Introdução

O Environment Dev Script foi migrado para uma estrutura modular para melhorar a manutenção, escalabilidade e organização do código. Este documento descreve a nova estrutura modular e como ela funciona.

## Visão Geral

A estrutura modular do Environment Dev Script é baseada em:

1. **Componentes Modulares**: Cada componente é definido em um arquivo YAML separado.
2. **Utilitários Especializados**: Funções utilitárias são organizadas em módulos Python específicos.
3. **Sistema de Verificação Robusto**: Verificações de pré-requisitos, permissões e espaço em disco.
4. **Gerenciamento de Erros**: Sistema centralizado de categorização e tratamento de erros.
5. **Rollback Transacional**: Sistema de rollback para garantir a integridade do sistema.

## Estrutura de Diretórios

```
Environment_dev_Script/
├── env_dev/
│   ├── config/
│   │   ├── components/
│   │   │   ├── boot_managers.yaml
│   │   │   ├── development_tools.yaml
│   │   │   ├── ...
│   │   ├── loader.py
│   │   ├── README.md
│   ├── core/
│   │   ├── installer.py
│   │   ├── rollback_manager.py
│   │   ├── ...
│   ├── gui/
│   │   ├── app_gui.py
│   │   ├── ...
│   ├── utils/
│   │   ├── disk_space.py
│   │   ├── downloader.py
│   │   ├── efi_backup.py
│   │   ├── error_handler.py
│   │   ├── permission_checker.py
│   │   ├── ...
│   ├── main.py
│   ├── components.yaml (legado)
├── resources/
│   ├── clover/
│   │   ├── CloverV2-5161.zip
│   ├── ...
├── docs/
│   ├── modular_structure.md
│   ├── ...
├── environment_dev.py
```

## Componentes Modulares

Os componentes são definidos em arquivos YAML separados na pasta `env_dev/config/components/`. Cada arquivo YAML contém um ou mais componentes relacionados a uma categoria específica.

### Exemplo de Componente

```yaml
CloverBootManager:
  category: Boot Managers
  dependencies: []
  description: Gerenciador de boot avançado para configurações de multiboot
  install_method: python_module
  module_path: env_dev.core.clover_installer
  module_function: install_clover
  verify_actions:
    - type: python_module
      module_path: env_dev.utils.clover_verification
      module_function: verify_clover_installation
  rollback_actions:
    - type: python_module
      module_path: env_dev.utils.efi_backup
      module_function: restore_latest_backup
  post_install_message: |
    Clover Boot Manager foi instalado com sucesso.
    
    Um backup da partição EFI foi criado em caso de problemas.
    Para acessar o modo de recuperação em caso de problemas, use a opção
    "Recuperar Clover Boot Manager" no menu de ferramentas do Environment Dev.
    
    Um guia detalhado de recuperação está disponível na documentação.
    
    Reinicie o computador para usar o Clover para inicialização.
```

### Tipos de Instalação

Os componentes podem usar diferentes métodos de instalação:

- **python_module**: Usa um módulo Python para instalação.
- **script**: Executa um script (PowerShell, Batch, etc.).
- **download**: Baixa um arquivo e o instala.
- **archive**: Baixa e extrai um arquivo compactado.
- **exe**: Baixa e executa um instalador executável.
- **msi**: Baixa e executa um instalador MSI.
- **none**: Não requer instalação (apenas verificação).

## Utilitários Especializados

### Verificação de Espaço em Disco

O módulo `disk_space.py` fornece funções para verificar o espaço disponível em disco e garantir que haja espaço suficiente para operações como downloads e instalações.

```python
# Verificar se há espaço suficiente para um download
has_space, message = ensure_space_for_download(file_size, download_path)
if not has_space:
    logger.error(message)
    # Sugerir ações para liberar espaço
    logger.info(suggest_cleanup_actions(file_size))
```

### Verificação de Permissões

O módulo `permission_checker.py` fornece funções para verificar se o usuário tem permissões adequadas para realizar operações como instalação de software e modificação de arquivos do sistema.

```python
# Verificar permissões para instalação
perm_results = check_permissions_for_installation(install_path)
if not perm_results['success']:
    # Sugerir ações para resolver problemas de permissão
    logger.info(suggest_permission_actions(perm_results))
```

### Backup da Partição EFI

O módulo `efi_backup.py` fornece funções para criar, listar e restaurar backups da partição EFI.

```python
# Criar backup da partição EFI
backup_result = create_efi_backup()
if backup_result:
    logger.info(f"Backup da partição EFI criado com sucesso: {backup_result['path']}")
```

### Verificação do Clover

O módulo `clover_verification.py` fornece funções para verificar a instalação do Clover Boot Manager.

```python
# Verificar instalação do Clover
result = verify_clover_installation()
if result['success']:
    logger.info("Clover Boot Manager está instalado corretamente.")
else:
    logger.error("Clover Boot Manager não está instalado corretamente.")
    for issue in result['issues']:
        logger.error(f"  - {issue}")
```

## Sistema de Verificação Robusto

O Environment Dev Script inclui um sistema de verificação robusto para garantir que os componentes sejam instalados corretamente e que os pré-requisitos sejam atendidos.

### Verificação de Pré-requisitos

Antes de instalar um componente, o sistema verifica se os pré-requisitos são atendidos:

1. **Verificação de Dependências**: Verifica se as dependências do componente estão instaladas.
2. **Verificação de Permissões**: Verifica se o usuário tem permissões adequadas para instalar o componente.
3. **Verificação de Espaço em Disco**: Verifica se há espaço suficiente em disco para instalar o componente.

### Verificação de Instalação

Após a instalação de um componente, o sistema verifica se a instalação foi bem-sucedida:

1. **Verificação de Arquivos**: Verifica se os arquivos necessários foram instalados.
2. **Verificação de Registro**: Verifica se as entradas de registro necessárias foram criadas.
3. **Verificação de Serviços**: Verifica se os serviços necessários foram instalados e estão em execução.

## Gerenciamento de Erros

O Environment Dev Script inclui um sistema centralizado de categorização e tratamento de erros.

### Categorias de Erros

Os erros são categorizados em:

- **INSTALLATION**: Erros durante a instalação de componentes.
- **DEPENDENCY**: Erros relacionados a dependências.
- **PERMISSION**: Erros relacionados a permissões.
- **DISK_SPACE**: Erros relacionados a espaço em disco.
- **NETWORK**: Erros relacionados a rede.
- **FILE**: Erros relacionados a arquivos.
- **VERIFICATION**: Erros durante a verificação de componentes.
- **ROLLBACK**: Erros durante o rollback de componentes.

### Tratamento de Erros

Os erros são tratados de acordo com sua categoria e severidade:

- **ERROR**: Erros críticos que impedem a continuação da operação.
- **WARNING**: Avisos que não impedem a continuação da operação, mas podem causar problemas.
- **INFO**: Informações sobre o progresso da operação.

## Rollback Transacional

O Environment Dev Script inclui um sistema de rollback para garantir a integridade do sistema em caso de falha na instalação de componentes.

### Registro de Ações

Durante a instalação de um componente, o sistema registra as ações realizadas:

1. **Arquivos Criados**: Arquivos criados durante a instalação.
2. **Arquivos Modificados**: Arquivos modificados durante a instalação.
3. **Entradas de Registro**: Entradas de registro criadas ou modificadas durante a instalação.
4. **Serviços**: Serviços instalados ou modificados durante a instalação.

### Rollback de Ações

Em caso de falha na instalação, o sistema realiza o rollback das ações registradas:

1. **Restauração de Arquivos**: Restaura os arquivos modificados ou remove os arquivos criados.
2. **Restauração de Registro**: Restaura as entradas de registro modificadas ou remove as entradas criadas.
3. **Restauração de Serviços**: Restaura os serviços modificados ou remove os serviços instalados.

## Conclusão

A estrutura modular do Environment Dev Script oferece uma base sólida para o desenvolvimento e manutenção do projeto. A organização em componentes modulares, utilitários especializados, sistema de verificação robusto, gerenciamento de erros e rollback transacional garantem a qualidade e confiabilidade do sistema.

## Referências

- [Documentação do Clover Boot Manager](docs/clover_boot_manager.md)
- [Guia de Desenvolvimento](docs/development_guide.md)
- [Guia de Contribuição](docs/contribution_guide.md)
