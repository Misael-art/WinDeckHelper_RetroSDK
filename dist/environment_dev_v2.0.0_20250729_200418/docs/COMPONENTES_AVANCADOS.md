# Componentes Avançados e Scripting

Este documento detalha como criar componentes mais complexos no `components.yaml`, utilizando `script_actions`, variáveis de ambiente e gerenciando dependências.

## 1. Exemplo de Componente com `script_actions`

O método de instalação `script` oferece flexibilidade máxima, permitindo executar comandos arbitrários (PowerShell, Batch, executáveis).

**Cenário:** Instalar uma ferramenta que requer download manual de um ZIP, extração para um local específico e execução de um script de configuração pós-extração.

```yaml
MinhaFerramentaCustom:
  category: Ferramentas Customizadas
  description: Exemplo de ferramenta instalada via script complexo.
  # Não há download_url direto, o script cuidará disso.
  install_method: script
  # Define onde a ferramenta será extraída/instalada
  extract_path: "C:\\Program Files\\MinhaFerramenta" 
  script_actions:
    # Ação 1: Criar o diretório de destino
    - type: powershell
      command: "New-Item"
      args: ["-Path", "C:\\Program Files\\MinhaFerramenta", "-ItemType", "Directory", "-Force"]
      
    # Ação 2: Baixar o arquivo ZIP usando PowerShell
    - type: powershell
      command: "Invoke-WebRequest"
      args: 
        - "-Uri"
        - "https://servidor.com/path/to/minha_ferramenta_v1.zip" 
        - "-OutFile"
        - "${env:TEMP}\\minha_ferramenta.zip" # Usa variável de ambiente TEMP

    # Ação 3: Extrair o arquivo ZIP (requer 7-Zip no PATH)
    - type: executable 
      command: "7z.exe" # Assume que 7z.exe está no PATH
      args: 
        - "x" # Comando de extração
        - "${env:TEMP}\\minha_ferramenta.zip" # Arquivo a extrair
        - "-o C:\\Program Files\\MinhaFerramenta" # Diretório de destino
        - "-y" # Assume 'Sim' para todas as perguntas

    # Ação 4: Executar um script de configuração pós-extração
    - type: batch
      command: "setup.bat" # Nome do script DENTRO do diretório extraído
      args: ["--config-option", "valor"]
      # working_dir não é necessário aqui, pois _install_script define 
      # o 'cwd' para 'extract_path' por padrão quando ele existe.

    # Ação 5: Limpar o arquivo ZIP baixado
    - type: powershell
      command: "Remove-Item"
      args: ["-Path", "${env:TEMP}\\minha_ferramenta.zip", "-Force"]

  # Ações para verificar se a instalação foi bem-sucedida
  verify_actions:
    - type: file_exists
      path: "C:\\Program Files\\MinhaFerramenta\\MinhaFerramenta.exe"
    - type: directory_exists
      path: "C:\\Program Files\\MinhaFerramenta\\data"
```

**Observações:**

*   Cada ação em `script_actions` é executada sequencialmente. Se uma falhar, as seguintes não são executadas.
*   O `extract_path` é usado como diretório de trabalho (`cwd`) padrão para as `script_actions` se ele existir.
*   É crucial garantir que os comandos (como `7z.exe`) estejam disponíveis no PATH do sistema ou fornecer o caminho completo.

## 2. Uso de Variáveis de Ambiente (`${env:VAR}`)

Você pode usar variáveis de ambiente do sistema ou do usuário nos campos `extract_path`, `args` (dentro de `script_actions`) e `path` (dentro de `verify_actions`) usando a sintaxe `${env:NOME_DA_VARIAVEL}`.

**Exemplos:**

*   `extract_path: "${env:USERPROFILE}\\MinhasFerramentas\\App"`
*   `args: ["-output", "${env:TEMP}\\output.log"]`
*   `path: "${env:ProgramFiles}\\Ferramenta\\bin\\tool.exe"`

O instalador tentará expandir essas variáveis antes de usar os caminhos/argumentos. Se uma variável não for encontrada, um aviso será logado.

## 3. Diretório de Trabalho (`cwd`) para Scripts

*   **Padrão:** Se `extract_path` estiver definido e o diretório existir (ou for criado pelo script), ele será usado como o diretório de trabalho (`cwd`) para todas as `script_actions` subsequentes. Isso é útil para executar scripts que estão dentro do pacote extraído/clonado.
*   **Sem `extract_path`:** Se `extract_path` não for definido, as `script_actions` serão executadas no diretório de trabalho onde o `environment_dev.py` foi iniciado.
*   **Sobrescrita (Futuro):** (Não implementado atualmente) Poderia haver um campo `working_dir` opcional dentro de cada `script_action` para sobrescrever o `cwd` padrão para aquela ação específica.

## 4. Gerenciamento de Dependências Customizadas

Você pode definir dependências entre seus componentes customizados da mesma forma que os componentes padrão, usando a chave `dependencies`:

```yaml
MinhaLibCustom:
  category: Bibliotecas Customizadas
  description: Uma biblioteca base.
  install_method: script
  extract_path: "${env:USERPROFILE}\\libs\\minhalib"
  script_actions:
    # ... ações para instalar a lib ...
  verify_actions:
    - type: directory_exists
      path: "${env:USERPROFILE}\\libs\\minhalib"

MinhaFerramentaQueUsaLib:
  category: Ferramentas Customizadas
  description: Ferramenta que depende da MinhaLibCustom.
  dependencies:
    - MinhaLibCustom # Garante que MinhaLibCustom seja instalada primeiro
  install_method: script
  extract_path: "C:\\Program Files\\MinhaFerramentaAvancada"
  script_actions:
    # ... ações que podem usar a MinhaLibCustom ...
  verify_actions:
    - type: file_exists
      path: "C:\\Program Files\\MinhaFerramentaAvancada\\tool.exe"
```

O instalador garantirá que `MinhaLibCustom` seja processada (e instalada, se necessário) antes de tentar instalar `MinhaFerramentaQueUsaLib`.