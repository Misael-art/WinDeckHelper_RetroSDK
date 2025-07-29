# Scripts de Melhoria do Projeto

Este diretório contém scripts automatizados para melhorar e manter a qualidade do projeto Environment Dev Script.

## 📋 Visão Geral

Os scripts foram criados para resolver os principais problemas identificados na análise do projeto:

- ✅ **Hashes pendentes**: Muitos componentes com `HASH_PENDENTE_VERIFICACAO`
- ✅ **URLs inválidas**: Links de download quebrados ou desatualizados
- ✅ **Componentes legados**: 29 componentes ainda no formato antigo
- ✅ **Validação de configurações**: Verificação de estrutura e consistência
- ✅ **Automação**: Script principal para executar todas as melhorias

## 🛠️ Scripts Disponíveis

### 1. `update_pending_hashes.py`
**Propósito**: Atualiza automaticamente hashes pendentes nos arquivos YAML.

```bash
# Execução normal (atualiza os hashes)
python tools/update_pending_hashes.py

# Modo dry-run (apenas simula)
python tools/update_pending_hashes.py --dry-run

# Atualiza apenas um componente específico
python tools/update_pending_hashes.py --component "Git"
```

**Funcionalidades**:
- Encontra todos os `HASH_PENDENTE_VERIFICACAO` nos YAMLs
- Baixa temporariamente os arquivos
- Calcula hashes SHA256
- Atualiza os arquivos YAML
- Cria backups automáticos
- Gera relatório detalhado

### 2. `validate_component_urls.py`
**Propósito**: Valida e corrige URLs de download problemáticas.

```bash
# Apenas validação
python tools/validate_component_urls.py

# Validação com correção automática
python tools/validate_component_urls.py --fix

# Com timeout personalizado
python tools/validate_component_urls.py --timeout 60
```

**Funcionalidades**:
- Testa acessibilidade de todas as URLs
- Sugere URLs alternativas para links quebrados
- Corrige URLs conhecidas como problemáticas
- Suporte para APIs do GitHub (releases)
- Relatório detalhado com estatísticas

### 3. `migrate_legacy_components.py`
**Propósito**: Migra componentes do formato legado para o novo formato modular.

```bash
# Migração completa
python tools/migrate_legacy_components.py

# Modo dry-run
python tools/migrate_legacy_components.py --dry-run

# Migra apenas um componente
python tools/migrate_legacy_components.py --component "Visual Studio Code"
```

**Funcionalidades**:
- Identifica componentes no formato legado
- Converte para o novo formato YAML modular
- Categoriza automaticamente os componentes
- Cria backups com timestamp
- Atualiza `component_status.json`
- Relatório de migração

### 4. `validate_component_configs.py`
**Propósito**: Valida estrutura e consistência das configurações YAML.

```bash
# Validação básica
python tools/validate_component_configs.py

# Com correções automáticas
python tools/validate_component_configs.py --fix-minor

# Valida componente específico
python tools/validate_component_configs.py --component "CMake"
```

**Funcionalidades**:
- Valida sintaxe YAML
- Verifica campos obrigatórios
- Valida tipos de dados
- Testa URLs e hashes
- Verifica dependências
- Corrige problemas menores automaticamente

### 5. `run_improvements.py` ⭐
**Propósito**: Script principal que executa todas as melhorias de forma coordenada.

```bash
# Execução completa
python tools/run_improvements.py

# Modo dry-run (recomendado primeiro)
python tools/run_improvements.py --dry-run

# Pula validação de URLs (mais rápido)
python tools/run_improvements.py --skip-urls

# Pula migração de componentes legados
python tools/run_improvements.py --skip-migration

# Com correções menores automáticas
python tools/run_improvements.py --fix-minor
```

**Funcionalidades**:
- Executa todos os scripts em ordem lógica
- Coordena dependências entre etapas
- Gera relatório consolidado
- Tratamento de erros robusto
- Recomendações automáticas

## 📊 Relatórios Gerados

Cada script gera relatórios detalhados:

- `hash_update_report.txt` - Resultado da atualização de hashes
- `url_validation_report.txt` - Status das URLs validadas
- `migration_report.txt` - Resultado da migração de componentes
- `validation_report.txt` - Problemas encontrados nas configurações
- `improvement_report.txt` - Relatório consolidado de todas as melhorias

## 🚀 Uso Recomendado

### Primeira Execução
```bash
# 1. Execute em modo dry-run para ver o que será feito
python tools/run_improvements.py --dry-run

# 2. Se estiver satisfeito, execute as melhorias
python tools/run_improvements.py --fix-minor

# 3. Verifique os relatórios gerados
```

### Execução Rápida (sem validação de URLs)
```bash
# Para execuções mais rápidas, pule a validação de URLs
python tools/run_improvements.py --skip-urls --fix-minor
```

### Execução Específica
```bash
# Apenas atualizar hashes
python tools/update_pending_hashes.py

# Apenas migrar componentes legados
python tools/migrate_legacy_components.py

# Apenas validar configurações
python tools/validate_component_configs.py --fix-minor
```

## 🔧 Dependências

Os scripts utilizam apenas bibliotecas padrão do Python e módulos já existentes no projeto:

- `yaml` - Para manipulação de arquivos YAML
- `requests` - Para validação de URLs
- `pathlib` - Para manipulação de caminhos
- `json` - Para manipulação de JSON
- Módulos do projeto: `LogManager`, `NetworkUtils`, etc.

## 📝 Logs e Debugging

Todos os scripts utilizam o sistema de logging do projeto:

- Logs detalhados são salvos automaticamente
- Níveis: INFO, WARNING, ERROR, SUCCESS
- Saída colorida no console
- Logs persistentes em arquivos

## ⚠️ Segurança e Backups

### Backups Automáticos
- Todos os scripts criam backups antes de modificar arquivos
- Backups incluem timestamp para versionamento
- Formato: `arquivo.yaml.backup_YYYYMMDD_HHMMSS`

### Modo Dry-Run
- Sempre disponível com `--dry-run`
- Simula todas as operações sem fazer alterações
- Recomendado para primeira execução

### Validações
- Verificação de integridade antes de modificações
- Validação de URLs antes de downloads
- Verificação de dependências

## 🎯 Resultados Esperados

Após executar todas as melhorias:

1. **Hashes Atualizados**: Todos os `HASH_PENDENTE_VERIFICACAO` substituídos por hashes SHA256 válidos
2. **URLs Corrigidas**: Links de download funcionais e atualizados
3. **Componentes Migrados**: Todos os componentes no novo formato modular
4. **Configurações Validadas**: Estrutura YAML consistente e válida
5. **Relatórios Detalhados**: Documentação completa de todas as alterações

## 🔄 Manutenção Contínua

### Execução Periódica
```bash
# Execute mensalmente para manter o projeto atualizado
python tools/run_improvements.py --skip-migration
```

### Novos Componentes
```bash
# Valide novos componentes adicionados
python tools/validate_component_configs.py --component "NovoComponente"
```

### Monitoramento de URLs
```bash
# Verifique URLs periodicamente
python tools/validate_component_urls.py
```

## 📞 Suporte

Em caso de problemas:

1. Verifique os logs detalhados
2. Execute em modo `--dry-run` primeiro
3. Consulte os relatórios gerados
4. Verifique se todas as dependências estão instaladas
5. Execute scripts individuais para isolar problemas

## 🎉 Contribuição

Para adicionar novos scripts de melhoria:

1. Siga o padrão dos scripts existentes
2. Use o sistema de logging do projeto
3. Implemente modo `--dry-run`
4. Crie backups automáticos
5. Gere relatórios detalhados
6. Adicione documentação neste README

---

**Nota**: Estes scripts foram criados como parte da análise de melhorias do projeto e implementam as recomendações do `PLANO_ROBUSTEZ.md` e `AVALIACAO_PROJETO.md`.