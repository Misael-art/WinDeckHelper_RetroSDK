# Estrutura Modular de Componentes

Este diretório contém a nova estrutura modular de componentes para o sistema Environment Dev.

## Organização

Os componentes foram divididos em categorias para facilitar a manutenção:

- `components/dev_tools.yaml`: Ferramentas de desenvolvimento (compiladores, IDEs, etc.)
- `components/system_utils.yaml`: Utilitários de sistema (compactadores, drivers, etc.)
- `components/boot_managers.yaml`: Gerenciadores de inicialização (Clover, Grub2Win, etc.)
- `components/game_dev.yaml`: Ferramentas para desenvolvimento de jogos
- `components/ai_tools.yaml`: Ferramentas de IA e machine learning
- `components/misc.yaml`: Outros componentes não categorizados

Os scripts longos e conteúdos XML foram extraídos para a pasta `scripts/` para melhorar a legibilidade.

## Como Usar

O sistema agora carrega automaticamente todos os arquivos YAML na pasta `components/`. 
Não é necessário modificar o código para adicionar novos componentes - basta criar ou 
editar os arquivos YAML apropriados.

## Adicionando Novos Componentes

Para adicionar um novo componente:

1. Identifique a categoria apropriada e abra o arquivo YAML correspondente
2. Adicione seu componente seguindo o formato:

```yaml
MeuComponente:
  category: "Categoria Apropriada"
  description: "Descrição do componente"
  dependencies: [ComponenteA, ComponenteB]  # Opcional
  download_url: "https://exemplo.com/download"  # Opcional
  install_method: "exe|msi|zip|script"  # Método de instalação
  
  # Se for um script:
  script_actions:
    - type: powershell
      command: |
        Write-Host "Script curto aqui"
```

Para scripts longos, recomenda-se criar um arquivo separado em `scripts/` e referenciar:

```yaml
MeuComponente:
  # ... outros campos ...
  script_actions:
    - type: powershell
      command_file: "scripts/meu_componente_script.ps1"
      args: []
```

## Validação

Use o script `validate_yaml.py` para verificar seus arquivos YAML:

```
python validate_yaml.py env_dev/config/components/
```

## Manutenção

Para manter a robustez do sistema:

1. Mantenha os arquivos YAML bem organizados por categoria
2. Use o validador antes de fazer alterações significativas
3. Extraia scripts longos para arquivos separados
4. Documente claramente os componentes com descrições precisas
5. Faça backup antes de modificar componentes críticos

## Estrutura de Componentes

Cada componente deve ter pelo menos:

- `category`: Categoria do componente
- `description`: Descrição clara e concisa
- `install_method`: Método de instalação 

Outros campos opcionais incluem:

- `dependencies`: Lista de outros componentes necessários
- `download_url`: URL para download do componente
- `install_args`: Argumentos para instalação
- `verify_actions`: Ações para verificar se a instalação foi bem-sucedida
- `post_install_message`: Mensagem a ser exibida após a instalação

Para scripts, use `script_actions` com subcomponentes conforme necessário. 