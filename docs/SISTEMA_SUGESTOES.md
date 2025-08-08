# Sistema de Sugestões Inteligentes

Este documento descreve o novo sistema de sugestões inteligentes implementado para o Environment Developer, que cria correspondências automáticas entre aplicações detectadas e componentes YAML disponíveis.

## 📋 Visão Geral

O sistema de sugestões inteligentes resolve o problema de correspondência manual entre aplicações detectadas e componentes YAML, implementando:

1. **Mapeamento automático** entre nomes detectados e componentes YAML
2. **Correspondência fuzzy** para variações de nomes
3. **Metadados enriquecidos** nos componentes YAML
4. **Sistema de sugestões** baseado em aplicações detectadas

## 🏗️ Arquitetura

### Módulos Principais

#### 1. `ComponentMatcher` (`core/component_matcher.py`)
- **Responsabilidade**: Correspondência entre aplicações detectadas e componentes
- **Funcionalidades**:
  - Normalização de nomes de aplicações
  - Matching fuzzy usando algoritmo de Levenshtein
  - Mapeamento por aliases e executáveis
  - Cálculo de confiança das correspondências

#### 2. `ComponentMetadataManager` (`core/component_metadata_manager.py`)
- **Responsabilidade**: Gerenciamento de metadados de componentes
- **Funcionalidades**:
  - Carregamento e salvamento de metadados
  - Busca por categoria e tags
  - Adição de aliases e dicas de detecção
  - Exportação de YAMLs enriquecidos

#### 3. `IntelligentSuggestionEngine` (`core/intelligent_suggestions.py`)
- **Responsabilidade**: Geração de sugestões inteligentes
- **Funcionalidades**:
  - Análise de contexto de desenvolvimento
  - Regras de sugestão baseadas em padrões
  - Ranqueamento por relevância
  - Histórico de sugestões

#### 4. `SuggestionService` (`core/suggestion_service.py`)
- **Responsabilidade**: Coordenação e integração dos módulos
- **Funcionalidades**:
  - Cache de aplicações e sugestões
  - Interface unificada para a GUI
  - Relatórios de correspondência
  - Configuração de regras customizadas

#### 5. `SuggestionsWidget` (`gui/suggestions_widget.py`)
- **Responsabilidade**: Interface gráfica para sugestões
- **Funcionalidades**:
  - Exibição de sugestões em cards
  - Filtros por categoria e confiança
  - Instalação direta de componentes sugeridos
  - Atualização automática de sugestões

## 🚀 Como Usar

### 1. Interface Gráfica

1. Execute a aplicação principal:
   ```bash
   python main.py
   ```

2. Navegue até a aba **"Sugestões"** no painel de controle

3. Clique em **"Verificar Aplicações Instaladas"** para detectar aplicações

4. Visualize as sugestões organizadas por:
   - **Confiança**: Alta (>0.8), Média (0.5-0.8), Baixa (<0.5)
   - **Categoria**: Editores, Ferramentas, Runtimes, etc.
   - **Tags**: desenvolvimento, javascript, python, etc.

5. Instale componentes sugeridos diretamente pelos botões de ação

### 2. Programaticamente

```python
from env_dev.core.suggestion_service import create_suggestion_service

# Cria o serviço
service = create_suggestion_service()

# Aplicações detectadas (exemplo)
detected_apps = [
    {'name': 'Visual Studio Code', 'version': '1.84.0'},
    {'name': 'Node.js', 'version': '20.8.0'}
]

# Obtém sugestões
suggestions = service.get_suggestions(detected_apps)

# Processa sugestões
for suggestion in suggestions:
    print(f"{suggestion.component_name} (confiança: {suggestion.confidence:.2f})")
    print(f"Razão: {suggestion.reason}")
```

### 3. Script de Demonstração

Execute o script de demonstração para ver todas as funcionalidades:

```bash
python examples/demo_suggestions.py
```

## 📝 Adicionando Metadados aos Componentes

### Estrutura de Metadados

Adicione a seção `metadata` aos seus componentes YAML:

```yaml
component_name:
  name: "Nome do Componente"
  description: "Descrição do componente"
  category: "Categoria Principal"
  
  # Metadados para correspondência
  metadata:
    aliases:
      - "nome_alternativo"
      - "outro_alias"
    tags:
      - "tag1"
      - "tag2"
    executables:
      - "programa.exe"
      - "outro.exe"
    detection_hints:
      registry_keys:
        - "HKEY_LOCAL_MACHINE\\SOFTWARE\\Programa"
      common_paths:
        - "%PROGRAMFILES%\\Programa"
      commands:
        - "programa --version"
      environment_vars:
        - "PROGRAMA_PATH"
  
  # Configuração de instalação original
  windows:
    installer_type: "exe"
    # ... resto da configuração
```

### Exemplo Completo

Veja o arquivo `examples/component_metadata_example.yaml` para exemplos completos de componentes com metadados.

## 🔧 Configuração Avançada

### Regras de Sugestão Customizadas

```python
from env_dev.core.intelligent_suggestions import SuggestionRule

# Cria regra customizada
rule = SuggestionRule(
    name="Desenvolvedor React",
    condition=lambda apps: any('react' in app.get('name', '').lower() for app in apps),
    suggestions=['nodejs', 'vscode', 'git'],
    priority=0.9
)

# Adiciona ao serviço
service.add_suggestion_rule(rule)
```

### Configuração de Cache

```python
# Configurar tempo de cache (em segundos)
service.cache_duration = 3600  # 1 hora

# Limpar cache manualmente
service.clear_cache()
```

## 📊 Métricas e Relatórios

### Relatório de Correspondências

```python
# Gera relatório detalhado
report = service.generate_match_report(detected_apps)
print(report)
```

### Estatísticas de Sugestões

```python
# Obtém estatísticas
stats = service.get_suggestion_stats()
print(f"Total de sugestões: {stats['total']}")
print(f"Confiança média: {stats['avg_confidence']:.2f}")
```

## 🐛 Solução de Problemas

### Problemas Comuns

1. **Sugestões não aparecem**:
   - Verifique se as aplicações foram detectadas
   - Confirme que os metadados estão corretos
   - Execute `service.refresh_suggestions()`

2. **Correspondências incorretas**:
   - Ajuste os aliases nos metadados
   - Modifique o threshold de confiança
   - Adicione regras de exclusão

3. **Performance lenta**:
   - Ative o cache de sugestões
   - Reduza o número de componentes verificados
   - Otimize as regras de detecção

### Logs de Debug

```python
import logging
logging.getLogger('env_dev.core.suggestion_service').setLevel(logging.DEBUG)
```

## 🔮 Próximas Melhorias

### Planejadas

1. **Machine Learning**: Aprendizado baseado em histórico de instalações
2. **Integração com APIs**: Busca automática de novos componentes
3. **Sugestões Contextuais**: Baseadas em projetos ativos
4. **Feedback do Usuário**: Sistema de avaliação de sugestões
5. **Sincronização**: Compartilhamento de metadados entre usuários

### Contribuições

Para contribuir com melhorias:

1. Adicione metadados aos componentes existentes
2. Crie regras de sugestão específicas para seu domínio
3. Reporte bugs e sugestões de melhoria
4. Contribua com novos algoritmos de correspondência

## 📚 Referências

- [Algoritmo de Levenshtein](https://en.wikipedia.org/wiki/Levenshtein_distance)
- [Fuzzy String Matching](https://en.wikipedia.org/wiki/Approximate_string_matching)
- [YAML Specification](https://yaml.org/spec/)
- [PyQt5 Documentation](https://doc.qt.io/qtforpython/)

---

**Versão**: 1.0.0  
**Data**: Novembro 2024  
**Autor**: Sistema de Sugestões Inteligentes - Environment Developer