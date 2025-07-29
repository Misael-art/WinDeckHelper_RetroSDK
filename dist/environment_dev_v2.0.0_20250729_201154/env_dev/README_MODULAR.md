# Migração para Estrutura Modular de Componentes

Este documento explica a migração do arquivo `components.yaml` para uma estrutura modular mais robusta e fácil de manter.

## Motivação

A estrutura anterior apresentava diversos problemas:

1. Arquivo único muito grande (mais de 1500 linhas)
2. Conteúdo XML embutido como texto literal
3. Scripts longos misturados com configuração
4. Dificuldade de manutenção e validação
5. Maior probabilidade de problemas de sintaxe YAML

A nova estrutura resolve esses problemas ao:

1. Dividir os componentes em múltiplos arquivos por categoria
2. Extrair scripts longos para arquivos dedicados
3. Implementar validação robusta dos arquivos YAML
4. Criar um sistema de carregamento modular
5. Manter retrocompatibilidade com a estrutura anterior

## Nova Estrutura de Diretórios

```
env_dev/
  ├── config/
  │   ├── components/
  │   │   ├── boot_managers.yaml
  │   │   ├── system_utils.yaml
  │   │   ├── dev_tools.yaml
  │   │   ├── game_dev.yaml
  │   │   └── ai_tools.yaml
  │   ├── scripts/
  │   │   ├── cloverbootmanager_script_0.ps1
  │   │   └── dualbootpartitionmanager_script_1.ps1
  │   ├── loader.py
  │   └── README.md
  ├── validate_yaml.py
  ├── split_components.py
  ├── migrate_structure.ps1
  └── migrate_components.bat
```

## Como Migrar

Execute o script de migração fornecido:

**Windows (GUI):**
```
env_dev\migrate_components.bat
```

**Windows (PowerShell):**
```
cd env_dev
.\migrate_structure.ps1
```

**Linha de Comando (Python):**
```
cd env_dev
python split_components.py
```

## O Que a Migração Faz

1. Cria backup do arquivo `components.yaml` original
2. Divide os componentes por categoria em arquivos separados
3. Extrai scripts longos para arquivos dedicados
4. Cria o módulo de carregamento `loader.py`
5. Atualiza as referências no código principal
6. Valida os arquivos YAML gerados

## Como Usar a Nova Estrutura

Não é necessário alterar o código que usa os componentes. A função `load_components()` continua funcionando da mesma forma, mas agora carrega de múltiplos arquivos.

### Adicionando Novos Componentes

Para adicionar um novo componente:

1. Identifique a categoria apropriada (ex: `boot_managers.yaml`)
2. Adicione o componente seguindo o formato YAML padrão
3. Para scripts longos, crie um arquivo separado em `scripts/`

Exemplo:

```yaml
MeuComponente:
  category: Boot Managers
  description: Descrição do meu componente
  dependencies: [7-Zip]
  install_method: script
  script_actions:
    - type: powershell
      command_file: scripts/meu_componente_script.ps1
      args: []
```

### Validando Arquivos YAML

Use o script `validate_yaml.py` para verificar a sintaxe e estrutura:

```
python validate_yaml.py env_dev/config/components/
```

## Vantagens da Nova Estrutura

1. **Manutenção mais fácil:** Arquivos menores e organizados por categoria
2. **Melhor legibilidade:** Scripts separados da configuração
3. **Validação robusta:** Verifica a estrutura de cada componente
4. **Escalabilidade:** Adicionar novos componentes não aumenta a complexidade
5. **Segurança:** Backups automáticos e validação antes de carregar
6. **Modularidade:** Possibilidade de ativar/desativar categorias inteiras

## Solução de Problemas

- **Erro ao carregar componentes:** Verifique o log para identificar o arquivo problemático e use `validate_yaml.py` para validar.
- **Scripts não encontrados:** Verifique se os caminhos em `command_file` estão corretos.
- **Conflitos de nome:** Evite usar o mesmo nome de componente em arquivos diferentes.

---

Se encontrar problemas durante a migração, o arquivo original está disponível como backup em `components.yaml.backup_[timestamp]`. 