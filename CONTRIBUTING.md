# Contribuindo para o Environment Dev Deep Evaluation

Obrigado por considerar contribuir para o Environment Dev Deep Evaluation! 🎉

## 🤝 Como Contribuir

### Reportando Bugs
1. Verifique se o bug já foi reportado nas [Issues](https://github.com/Misael-art/EnvironmentDev_MISA/issues)
2. Se não, crie uma nova issue com:
   - Descrição clara do problema
   - Passos para reproduzir
   - Comportamento esperado vs atual
   - Screenshots se aplicável
   - Informações do sistema (OS, Python version, etc.)

### Sugerindo Melhorias
1. Abra uma issue com a tag "enhancement"
2. Descreva claramente a melhoria proposta
3. Explique por que seria útil
4. Considere implementações alternativas

### Contribuindo com Código

#### Configuração do Ambiente
```bash
# Fork e clone o repositório
git clone https://github.com/SEU_USUARIO/EnvironmentDev_MISA.git
cd EnvironmentDev_MISA

# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# Instalar dependências
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

#### Processo de Desenvolvimento
1. **Fork** o repositório
2. **Crie** uma branch para sua feature:
   ```bash
   git checkout -b feature/nome-da-feature
   ```
3. **Faça** suas alterações seguindo as diretrizes
4. **Teste** suas alterações:
   ```bash
   python -m pytest tests/
   python test_sgdk_fixes.py
   ```
5. **Commit** suas mudanças:
   ```bash
   git commit -m "feat: adiciona nova funcionalidade X"
   ```
6. **Push** para sua branch:
   ```bash
   git push origin feature/nome-da-feature
   ```
7. **Abra** um Pull Request

## 📝 Diretrizes de Código

### Estilo de Código
- Siga PEP 8 para Python
- Use type hints quando possível
- Docstrings para funções e classes
- Comentários em português para clareza

### Exemplo de Código
```python
def detectar_componente(nome: str, caminho: Optional[str] = None) -> bool:
    """
    Detecta se um componente está instalado no sistema.
    
    Args:
        nome: Nome do componente a ser detectado
        caminho: Caminho opcional para busca
        
    Returns:
        True se o componente foi encontrado
        
    Raises:
        ComponenteError: Se houver erro na detecção
    """
    try:
        # Implementação aqui
        return True
    except Exception as e:
        logger.error(f"Erro ao detectar {nome}: {e}")
        raise ComponenteError(f"Falha na detecção: {e}")
```

### Estrutura de Commits
Use conventional commits:
- `feat:` - Nova funcionalidade
- `fix:` - Correção de bug
- `docs:` - Mudanças na documentação
- `style:` - Formatação, sem mudança de código
- `refactor:` - Refatoração de código
- `test:` - Adição ou correção de testes
- `chore:` - Tarefas de manutenção

## 🧪 Testes

### Executando Testes
```bash
# Todos os testes
python -m pytest tests/ -v

# Testes específicos
python test_sgdk_fixes.py
python test_final_fixes.py
python test_deployment_package.py

# Com cobertura
python -m pytest tests/ --cov=core --cov-report=html
```

### Escrevendo Testes
- Teste todas as novas funcionalidades
- Mantenha cobertura > 80%
- Use nomes descritivos
- Teste casos de erro

```python
def test_detectar_componente_sucesso():
    """Testa detecção bem-sucedida de componente"""
    resultado = detectar_componente("git")
    assert resultado is True

def test_detectar_componente_nao_encontrado():
    """Testa quando componente não é encontrado"""
    resultado = detectar_componente("componente_inexistente")
    assert resultado is False
```

## 📚 Documentação

### Atualizando Documentação
- Mantenha README.md atualizado
- Documente novas funcionalidades
- Atualize guias de usuário se necessário
- Use português para documentação de usuário

### Estrutura da Documentação
```
docs/
├── installation_configuration_guide.md  # Guia de instalação
├── steamdeck_usage_guide.md            # Uso no Steam Deck
├── architecture_analysis.md            # Arquitetura técnica
└── README.md                           # Índice da documentação
```

## 🎮 Testando no Steam Deck

Se você tem acesso a um Steam Deck:
1. Teste a interface touch
2. Verifique navegação por gamepad
3. Teste performance e bateria
4. Valide otimizações específicas

## 🐛 Debugging

### Logs
- Use o sistema de logging existente
- Logs em `logs/` directory
- Níveis: DEBUG, INFO, WARNING, ERROR

### Ferramentas Úteis
```bash
# Debug mode
python main.py --debug

# Verbose logging
python main.py --verbose

# Profile performance
python -m cProfile main.py
```

## 📋 Checklist para Pull Requests

- [ ] Código segue as diretrizes de estilo
- [ ] Testes passam (`python -m pytest`)
- [ ] Documentação atualizada
- [ ] Commit messages seguem padrão
- [ ] Branch está atualizada com main
- [ ] Funcionalidade testada manualmente
- [ ] Sem arquivos desnecessários commitados

## 🏷️ Tipos de Contribuição

### 🔧 Código
- Novas funcionalidades
- Correções de bugs
- Melhorias de performance
- Refatorações

### 📖 Documentação
- Guias de usuário
- Documentação técnica
- Exemplos de código
- Traduções

### 🧪 Testes
- Novos casos de teste
- Melhoria de cobertura
- Testes de integração
- Testes de performance

### 🎨 Design/UX
- Melhorias na interface
- Otimizações para Steam Deck
- Acessibilidade
- Usabilidade

## 🎯 Áreas que Precisam de Ajuda

- [ ] Suporte a mais componentes retro
- [ ] Melhorias na interface gráfica
- [ ] Otimizações de performance
- [ ] Testes em diferentes sistemas
- [ ] Documentação em inglês
- [ ] Integração com mais gerenciadores de pacotes

## 📞 Obtendo Ajuda

- **Issues**: Para bugs e sugestões
- **Discussions**: Para perguntas gerais
- **Discord**: [Link do servidor] (se houver)
- **Email**: Através de issues no GitHub

## 🙏 Reconhecimento

Todos os contribuidores serão reconhecidos:
- Nome no README.md
- Créditos nos releases
- Badge de contribuidor

## 📄 Licença

Ao contribuir, você concorda que suas contribuições serão licenciadas sob a mesma licença MIT do projeto.

---

**Obrigado por contribuir! 🚀**

Sua ajuda torna este projeto melhor para toda a comunidade de desenvolvimento!