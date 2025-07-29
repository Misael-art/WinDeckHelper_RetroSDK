# 🚀 Guia de Instalação - Environment Dev v2.0.0

## 📋 Pré-requisitos

### Sistema Operacional
- ✅ **Windows 10** (versão 1903 ou superior)
- ✅ **Windows 11** (todas as versões)

### Software Necessário
- ✅ **Python 3.8+** ([Download aqui](https://www.python.org/downloads/))
- ✅ **Conexão com internet** (para downloads de componentes)
- ✅ **Espaço em disco**: Mínimo 2GB livres

### Permissões
- ⚠️ **Permissões de administrador** podem ser necessárias para algumas instalações
- ✅ **Acesso à internet** sem proxy restritivo

## 🎯 Instalação Rápida (Recomendada)

### Opção 1: Distribuição Pré-compilada

1. **Baixe a distribuição**:
   ```
   environment_dev_v2.0.0_YYYYMMDD_HHMMSS.zip
   ```

2. **Extraia o arquivo**:
   - Clique com botão direito → "Extrair tudo..."
   - Escolha um local (ex: `C:\Tools\EnvironmentDev\`)

3. **Execute a instalação**:
   ```cmd
   cd C:\Tools\EnvironmentDev\
   install.bat
   ```

4. **Inicie o programa**:
   ```cmd
   run.bat
   ```

### Opção 2: Instalação Manual

1. **Clone o repositório**:
   ```bash
   git clone https://github.com/seu-usuario/environment_dev_script.git
   cd environment_dev_script
   ```

2. **Crie ambiente virtual** (opcional, mas recomendado):
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. **Instale dependências**:
   ```bash
   pip install -r requirements-dev.txt
   ```

4. **Execute**:
   ```bash
   python env_dev/main.py
   ```

## 🧪 Validação da Instalação

### Teste Automático
Execute os scripts de teste para verificar se tudo está funcionando:

```bash
# Teste básico do sistema
python test_installation_fix.py

# Teste completo de download
python test_real_download_installation.py
```

### Resultado Esperado
```
🎉 Todos os testes passaram! O sistema de instalação foi corrigido.

✓ 86 componentes carregados
✓ Sistema de download funcionando
✓ GUI corrigida para usar instalação real
✓ Integração com GUI verificada
```

### Teste Manual
1. Execute `python env_dev/main.py`
2. Verifique se a interface gráfica abre
3. Clique em "Diagnostics" - deve executar verificações reais
4. Selecione um componente e teste a instalação

## 🔧 Configuração Avançada

### Variáveis de Ambiente (Opcional)

```cmd
# Diretório de downloads personalizado
set ENVDEV_DOWNLOAD_DIR=C:\MyDownloads

# Nível de log detalhado
set ENVDEV_LOG_LEVEL=DEBUG

# Timeout personalizado para downloads
set ENVDEV_DOWNLOAD_TIMEOUT=300
```

### Configuração de Proxy (Se Necessário)

Edite `env_dev/config/settings.json`:
```json
{
  "proxy": {
    "http": "http://proxy.empresa.com:8080",
    "https": "https://proxy.empresa.com:8080"
  }
}
```

## 🚨 Solução de Problemas

### Problema: "Python não encontrado"
**Solução**:
1. Instale Python 3.8+ do site oficial
2. Marque "Add Python to PATH" durante a instalação
3. Reinicie o terminal

### Problema: "Módulo não encontrado"
**Solução**:
```bash
pip install -r requirements-dev.txt --upgrade
```

### Problema: "Permissão negada"
**Solução**:
1. Execute como administrador
2. Ou instale em diretório do usuário:
   ```bash
   pip install --user -r requirements-dev.txt
   ```

### Problema: "Falha no download"
**Solução**:
1. Verifique conexão com internet
2. Desative temporariamente antivírus/firewall
3. Configure proxy se necessário

### Problema: Interface não abre
**Solução**:
1. Verifique se tkinter está instalado:
   ```bash
   python -c "import tkinter; print('OK')"
   ```
2. Se falhar, reinstale Python com "tcl/tk and IDLE"

## 📊 Verificação de Sistema

### Comando de Diagnóstico
```bash
python env_dev/main.py --check-env
```

### Informações Coletadas
- ✅ Versão do Python
- ✅ Módulos instalados
- ✅ Espaço em disco
- ✅ Conexão com internet
- ✅ Permissões de escrita
- ✅ Configuração de proxy

## 🔄 Atualização

### Atualização Automática (Futura)
```bash
python env_dev/main.py --update
```

### Atualização Manual
1. Baixe a nova versão
2. Faça backup das configurações personalizadas
3. Substitua os arquivos
4. Execute os testes de validação

## 📞 Suporte

### Antes de Reportar Problemas
1. ✅ Execute `test_installation_fix.py`
2. ✅ Verifique logs em `logs/`
3. ✅ Consulte esta documentação
4. ✅ Verifique issues conhecidos no GitHub

### Como Reportar
1. **Descreva o problema** claramente
2. **Inclua logs** relevantes
3. **Especifique o ambiente**:
   - Versão do Windows
   - Versão do Python
   - Mensagem de erro completa

### Canais de Suporte
- 🐛 **GitHub Issues**: Para bugs e problemas técnicos
- 📖 **Documentação**: `docs/` para guias detalhados
- 💬 **Discussões**: Para dúvidas gerais

## 🎯 Próximos Passos

Após a instalação bem-sucedida:

1. **Explore a interface**: Familiarize-se com o dashboard
2. **Execute diagnósticos**: Verifique o status do seu sistema
3. **Teste instalações**: Comece com componentes simples
4. **Configure preferências**: Personalize conforme necessário
5. **Leia a documentação**: Explore recursos avançados

---

**🎉 Parabéns! Você agora tem o Environment Dev v2.0.0 funcionando com sistema de instalação real!**