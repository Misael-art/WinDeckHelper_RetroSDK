# Scripts de Teste de Instalação - env_dev

Este documento descreve os scripts de teste criados para verificar o sucesso das instalações realizadas pelo projeto env_dev, com foco especial no SGDK (Sega Genesis Development Kit) e suas dependências.

## 📋 Visão Geral

O projeto env_dev possui um sistema robusto de instalação de ferramentas de desenvolvimento retro. Para garantir que as instalações foram bem-sucedidas, foram criados diversos scripts de teste que verificam:

- ✅ Dependências básicas (Java, Make, Visual C++ Redistributable, 7-Zip)
- ✅ Estrutura do projeto e arquivos de configuração
- ✅ Instalação e configuração do SGDK
- ✅ Testes de compilação
- ✅ Geração de relatórios detalhados

## 🧪 Scripts de Teste Disponíveis

### 1. `test_complete_installation.py` ⭐ **PRINCIPAL**

**Descrição**: Script completo e abrangente para testar todas as instalações.

**Funcionalidades**:
- Coleta informações detalhadas do sistema
- Verifica estrutura completa do projeto
- Testa todas as dependências do SGDK
- Verifica instalação e configuração do SGDK
- Realiza teste de compilação
- Gera relatório JSON detalhado
- Fornece recomendações específicas

**Como usar**:
```bash
python test_complete_installation.py
```

**Output esperado**:
- Status detalhado de cada componente
- Relatório de dependências
- Verificação do SGDK
- Arquivo JSON com resultados completos

---

### 2. `quick_sgdk_test.py`

**Descrição**: Teste rápido focado especificamente no SGDK e dependências críticas.

**Funcionalidades**:
- Verificação rápida de Java e Make
- Teste de variáveis de ambiente (JAVA_HOME, SGDK_HOME)
- Verificação básica da estrutura do SGDK
- Teste simples de compilação

**Como usar**:
```bash
python quick_sgdk_test.py
```

**Ideal para**: Verificações rápidas durante o desenvolvimento.

---

### 3. `test_project_integrity.py`

**Descrição**: Verifica a integridade dos arquivos de configuração e estrutura do projeto.

**Funcionalidades**:
- Verificação de arquivos YAML de configuração
- Teste de importação de módulos Python
- Validação da estrutura de diretórios
- Verificação de configurações do SGDK

**Como usar**:
```bash
python test_project_integrity.py
```

**Ideal para**: Verificar se o projeto está configurado corretamente.

---

### 4. `test_sgdk_final.py`

**Descrição**: Teste específico e detalhado do SGDK.

**Funcionalidades**:
- Leitura da configuração do SGDK do arquivo YAML
- Teste detalhado de dependências
- Verificação completa da instalação do SGDK
- Relatório em formato JSON

**Como usar**:
```bash
python test_sgdk_final.py
```

---

### 5. `test_installation_benchmark.py`

**Descrição**: Benchmark que simula diferentes cenários de instalação.

**Funcionalidades**:
- Simula 5 cenários diferentes:
  - Sistema limpo
  - Dependências parciais
  - Dependências prontas
  - Totalmente instalado
  - Instalação quebrada
- Análise comparativa
- Métricas de tempo de instalação
- Insights sobre problemas comuns

**Como usar**:
```bash
python test_installation_benchmark.py
```

**Ideal para**: Entender diferentes estados do sistema e suas implicações.

---

### 6. Scripts de Demonstração

#### `demo_test_success.py`
Simula um cenário onde todas as dependências estão instaladas e funcionando.

#### `demo_complete_success.py`
Demonstra o output completo de um sistema totalmente configurado, incluindo guias de desenvolvimento.

**Como usar**:
```bash
python demo_test_success.py
python demo_complete_success.py
```

## 🎯 Cenários de Uso

### Após Instalação Inicial
```bash
# Teste completo após instalar o SGDK
python test_complete_installation.py
```

### Verificação Rápida
```bash
# Teste rápido durante desenvolvimento
python quick_sgdk_test.py
```

### Diagnóstico de Problemas
```bash
# Verificar integridade do projeto
python test_project_integrity.py

# Benchmark para entender o estado atual
python test_installation_benchmark.py
```

### Demonstração
```bash
# Ver como seria um sistema funcionando
python demo_complete_success.py
```

## 📊 Interpretação dos Resultados

### Status Possíveis

- **🎉 FULLY_READY**: Sistema completamente pronto para desenvolvimento
- **⚠️ SGDK_READY_DEPS_MISSING**: SGDK instalado mas dependências faltando
- **🔧 PARTIAL_DEPENDENCIES**: Algumas dependências instaladas
- **🆕 CLEAN_SYSTEM**: Sistema limpo, nada instalado

### Dependências Verificadas

1. **Java Runtime Environment**
   - Comando `java -version`
   - Variável `JAVA_HOME`
   - Executável no PATH

2. **Make (Build Tools)**
   - Comando `make --version`
   - Executável no PATH

3. **Visual C++ Redistributable** (Windows)
   - Verificação no registro do Windows
   - Múltiplas versões suportadas

4. **7-Zip**
   - Comando `7z`
   - Localizações padrão no Windows

5. **SGDK**
   - Variável `SGDK_HOME`
   - Estrutura de diretórios (bin/, inc/, lib/)
   - Executáveis essenciais
   - Headers importantes
   - Teste de compilação

## 🔧 Arquivos Gerados

Os scripts geram arquivos de relatório com timestamp:

- `installation_test_results_YYYYMMDD_HHMMSS.json`
- `installation_benchmark_results.json`
- `sgdk_test_results_YYYYMMDD_HHMMSS.json`

### Estrutura do JSON de Resultados

```json
{
  "timestamp": "2024-01-01T12:00:00",
  "system_info": {
    "platform": "Windows",
    "architecture": "64bit",
    "python_version": "3.11.0"
  },
  "dependencies": {
    "java": {
      "installed": true,
      "version": "openjdk 11.0.16",
      "java_home": "C:\\Program Files\\Java\\jdk-11.0.16"
    }
  },
  "sgdk": {
    "installed": true,
    "sgdk_home": "C:\\SGDK",
    "compilation_test": {
      "success": true
    }
  },
  "summary": {
    "overall_status": "FULLY_READY",
    "recommendations": []
  }
}
```

## 🚀 Próximos Passos

Após executar os testes e confirmar que tudo está funcionando:

1. **Criar um projeto SGDK**:
   ```bash
   mkdir meu_jogo_genesis
   cd meu_jogo_genesis
   ```

2. **Criar um arquivo main.c básico**:
   ```c
   #include "genesis.h"
   
   int main() {
       VDP_drawText("Hello Genesis!", 10, 10);
       while(1) {
           SYS_doVBlankProcess();
       }
       return 0;
   }
   ```

3. **Compilar**:
   ```bash
   %SGDK_HOME%\bin\sgdk-gcc -o game.bin main.c
   ```

4. **Testar no emulador**:
   - Kega Fusion
   - Gens
   - BlastEm

## 🐛 Solução de Problemas

### Java não encontrado
- Verificar se Java está instalado
- Configurar variável `JAVA_HOME`
- Adicionar Java ao PATH

### Make não encontrado
- Instalar Build Tools para Visual Studio
- Ou instalar GnuWin32 Make
- Verificar PATH

### SGDK não encontrado
- Verificar se `SGDK_HOME` está configurado
- Verificar se a estrutura de diretórios está completa
- Reinstalar SGDK se necessário

### Erro de compilação
- Verificar se todas as dependências estão instaladas
- Verificar se os headers do SGDK estão presentes
- Verificar se as bibliotecas estão linkadas corretamente

## 📞 Suporte

Se os testes indicarem problemas:

1. Execute `python test_complete_installation.py` para diagnóstico completo
2. Verifique as recomendações no output
3. Execute `python retro_devkit_manager.py` para reinstalar componentes
4. Execute os testes novamente para confirmar correções

---

**Desenvolvido para o projeto env_dev**  
*Facilitando o desenvolvimento de jogos retro desde 2024*