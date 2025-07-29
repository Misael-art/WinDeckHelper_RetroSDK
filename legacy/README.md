# Arquivos Legados (PowerShell)

Este diretório contém a versão antiga do projeto escrita em PowerShell. Estes arquivos são mantidos para referência e compatibilidade, mas não são mais ativamente desenvolvidos.

## Estrutura

- `modules/core/`: Contém os módulos principais da versão PowerShell
  - `logging.psm1`: Sistema de logs
  - `utils.psm1`: Funções utilitárias (download, verificação de hash, etc.)
  - `config.psm1`: Funções de configuração
  - `ui.psm1`: Interface de usuário em console
  
- `modules/environment/`: Funções relacionadas ao ambiente de execução
- `modules/installation/`: Scripts de instalação de componentes
- `modules/tweaks/`: Ajustes e otimizações do sistema

## Migração para Python

Os arquivos neste diretório foram migrados para Python e estão agora disponíveis na pasta `env_dev/` na raiz do projeto. As principais melhorias na versão Python incluem:

1. Sistema de logs melhorado com suporte a cores e rotação de arquivos
2. Verificação de hash com suporte a múltiplos algoritmos
3. Interface gráfica moderna
4. Verificação de internet com fallback
5. Detecção de display aprimorada
6. Gerenciamento de variáveis de ambiente do sistema

## Uso (Legado)

Se for necessário utilizar a versão PowerShell por algum motivo, execute os scripts a partir do diretório raiz, importando os módulos:

```powershell
Import-Module .\legacy\modules\core\utils.psm1
```

> **Nota**: Recomendamos usar a nova versão Python do projeto sempre que possível. 