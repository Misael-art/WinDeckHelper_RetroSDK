# Plano de Ação para Robustecer o Sistema Environment Dev

Este documento detalha o plano para melhorar a robustez do sistema de instalação "Environment Dev", focando na verificação de integridade de downloads e na implementação de funcionalidade de rollback.

## 1. Resumo da Análise

*   **Verificação de Integridade de Downloads:** A lógica para verificar hashes de arquivos baixados já existe (`downloader.py`, `hash_utils.py`), mas sua eficácia é limitada pela falta de `expected_hash` e `hash_algorithm` em muitas definições de componentes nos arquivos YAML.
*   **Funcionalidade de Rollback:** O sistema atual carece de um mecanismo de rollback verdadeiro. Possui apenas limpeza básica de arquivos temporários/extraídos, mas não desfaz alterações no sistema (arquivos instalados, registro, variáveis de ambiente) em caso de falha após o download.

## 2. Plano de Ação

### Frente 1: Fortalecer a Verificação de Integridade de Downloads

*   **Objetivo:** Garantir que *todos* os downloads sejam verificados quanto à integridade para prevenir instalações com arquivos corrompidos.
*   **Ação Principal:** Realizar uma auditoria em **todos** os arquivos YAML de componentes localizados em `env_dev/config/components/`. Para cada componente que possua um `download_url`:
    1.  Calcular manualmente o hash SHA256 do arquivo correspondente (usando `certutil -hashfile <arquivo> SHA256` no Windows ou `sha256sum <arquivo>` no Linux/WSL).
    2.  Adicionar ou atualizar os campos `hash` e `hash_algorithm` no arquivo YAML:
        ```yaml
        NomeComponente:
          # ... outras chaves ...
          download_url: ...
          hash: <hash_sha256_calculado_aqui>  # ADICIONAR/ATUALIZAR
          hash_algorithm: sha256              # ADICIONAR/ATUALIZAR
          # ...
        ```
*   **Benefício:** Ativa a verificação de integridade existente para todos os downloads, aumentando a confiabilidade.

### Frente 2: Implementar Funcionalidade de Rollback Transacional

*   **Objetivo:** Criar um mecanismo que reverta as alterações feitas por uma instalação de componente que falhou em qualquer etapa após o download inicial verificado.
*   **Conceito:** Tratar a instalação de cada componente como uma transação atômica.
*   **Implementação:**
    1.  **Criar `RollbackManager`:** Desenvolver a classe `env_dev.core.RollbackManager` para gerenciar o estado da transação e as operações de desfazer (undo).
    2.  **Estrutura de Dados:** Definir um formato padrão para registrar operações de undo (ex: `{'component': ..., 'step_description': ..., 'action_type': ..., 'undo_action': ..., 'parameters': {...}}`).
    3.  **Integração com `installer.py`:**
        *   `rollback_manager.start_transaction(component_name)`: No início da instalação do componente.
        *   `rollback_manager.register_action(undo_operation)`: **Antes** de cada ação modificadora (extração, execução de instalador/script, alteração de ambiente).
        *   `rollback_manager.commit_transaction()`: Ao final de uma instalação bem-sucedida.
        *   `rollback_manager.trigger_rollback()`: Em caso de falha após o início da transação.
    4.  **Lógica de Rollback:** O `trigger_rollback()` executa as `undo_action` registradas em ordem **inversa**, tratando erros de forma pragmática (logar e continuar).
    5.  **Tipos de Ações de Desfazer:** Implementar lógica no `RollbackManager` para `delete_path`, `run_command`, `run_script`, `unset_env`, `delete_registry_key`, etc.
    6.  **Descoberta de Comandos de Desinstalação (Abordagem Híbrida):**
        *   Priorizar `uninstall_command`/`uninstall_args` definidos no YAML.
        *   Se não definidos, tentar descobrir automaticamente via Registro do Windows após a instalação (`HKEY_LOCAL_MACHINE\...\Uninstall`, procurando por `QuietUninstallString` ou `UninstallString`).
        *   Se nenhum comando for encontrado, registrar um aviso e potencialmente realizar um rollback de "melhor esforço" (ex: deletar diretório de extração/instalação).
    7.  **Atualizações YAML (Opcional):** Adicionar campos como `uninstall_command`, `uninstall_args`, `undo_script` para maior controle sobre o rollback.

*   **Diagrama de Fluxo (Instalação com Rollback):**
    ```mermaid
    graph TD
        A[Iniciar Instalação Componente] --> B{Download Necessário?};
        B -- Sim --> C[Executar Download];
        B -- Não --> G[Verificar Instalação Existente];
        C --> D{Download OK? (Hash Verificado)};
        D -- Não --> E[Erro: Falha Download/Hash];
        D -- Sim --> F[Registrar Ação: Download (se necessário p/ rollback)];
        F --> G;
        G -- Já Instalado --> H[Sucesso (Componente Já Instalado)];
        G -- Não Instalado --> I[RollbackMgr: start_transaction];
        I --> J{Instalar Dependências};
        J -- Falha --> K[RollbackMgr: trigger_rollback];
        J -- Sucesso --> L[RollbackMgr: register_action(undo_deps)];
        L --> M{Executar Extração/Instalador};
        M -- Falha --> K;
        M -- Sucesso --> N[RollbackMgr: register_action(undo_extract_install)];
        N --> O{Executar Scripts/Configuração};
        O -- Falha --> K;
        O -- Sucesso --> P[RollbackMgr: register_action(undo_script_config)];
        P --> Q{Verificar Instalação Final};
        Q -- Falha --> K;
        Q -- Sucesso --> R[RollbackMgr: commit_transaction];
        R --> S[Sucesso (Componente Instalado)];
        K --> T[Erro: Instalação Falhou (Rollback Executado)];
        E --> Z[Fim];
        H --> Z;
        S --> Z;
        T --> Z;
    ```

*   **Diagrama de Sequência (RollbackManager - Simplificado):**
    ```mermaid
    sequenceDiagram
        participant Installer as installer.py
        participant RollbackMgr as RollbackManager
        participant OS as Sistema Operacional/Arquivos

        Installer->>RollbackMgr: start_transaction("ComponenteX")
        Installer->>OS: Extrair Arquivos (para /path/to/extract)
        alt Sucesso na Extração
            Installer->>RollbackMgr: register_action(undo='delete_path', path='/path/to/extract')
            Installer->>OS: Executar Instalador (.exe)
            alt Sucesso no Instalador
                Installer->>RollbackMgr: register_action(undo='run_command', cmd='uninstaller.exe /S') # Comando obtido via YAML ou Registro
                Installer->>OS: Executar Script Config
                alt Sucesso no Script
                     Installer->>RollbackMgr: register_action(undo='run_script', script='undo_config.ps1') # Se definido
                     Installer->>Installer: Verificar Instalação Final
                     alt Verificação OK
                         Installer->>RollbackMgr: commit_transaction()
                         Installer-->>User: Sucesso
                     else Verificação Falhou
                         Installer->>RollbackMgr: trigger_rollback()
                         RollbackMgr->>OS: Executar 'undo_config.ps1'
                         RollbackMgr->>OS: Executar 'uninstaller.exe /S'
                         RollbackMgr->>OS: Deletar '/path/to/extract'
                         Installer-->>User: Erro (Rollback Executado)
                     end
                else Falha no Script
                     Installer->>RollbackMgr: trigger_rollback()
                     RollbackMgr->>OS: Executar 'uninstaller.exe /S'
                     RollbackMgr->>OS: Deletar '/path/to/extract'
                     Installer-->>User: Erro (Rollback Executado)
                end
            else Falha no Instalador
                Installer->>RollbackMgr: trigger_rollback()
                RollbackMgr->>OS: Deletar '/path/to/extract'
                Installer-->>User: Erro (Rollback Executado)
            end
        else Falha na Extração
            Installer->>RollbackMgr: trigger_rollback() # Rollback vazio neste caso
            Installer-->>User: Erro (Rollback Executado)
        end
    ```

## 3. Estratégia de Testes

*   **Integridade:**
    *   Testar a instalação de componentes que *antes* não tinham hash, após adicioná-los.
    *   Introduzir artificialmente um hash incorreto em um componente e verificar se o download falha como esperado.
    *   Verificar se componentes com hash correto e arquivo já existente no destino pulam o download.
*   **Rollback:**
    *   Criar cenários de teste onde a instalação falha intencionalmente em diferentes etapas (extração, execução do .exe/msi, script pós-instalação, falha de verificação).
    *   Verificar se o sistema é revertido ao estado anterior à tentativa de instalação (arquivos/diretórios removidos, comandos de desinstalação executados, etc.).
    *   Testar cenários com dependências para garantir que o rollback funcione corretamente em cadeia, se aplicável.
    *   Testar a descoberta de comandos de desinstalação via Registro.
    *   Testar o fallback quando nenhum comando de desinstalação é encontrado.