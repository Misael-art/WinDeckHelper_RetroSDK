# MCPs - Módulos de Controle de Projeto para Mega_Emu

Este diretório contém os Módulos de Controle de Projeto (MCPs) desenvolvidos especificamente para auxiliar no desenvolvimento do projeto Mega_Emu.

## O que são MCPs?

MCPs são módulos de software que fornecem funcionalidades específicas para o gerenciamento e automação de tarefas no projeto. Eles são projetados para tornar o desenvolvimento mais eficiente, permitindo:

1. Automação de tarefas repetitivas
2. Análise e monitoramento de desempenho
3. Depuração avançada
4. Gerenciamento de dados do projeto

## MCPs Disponíveis

### 1. Code Analyzer

Fornece ferramentas para análise estática de código, identificando problemas potenciais e oportunidades de melhoria.

**Principais funcionalidades:**
- Análise de complexidade ciclomática
- Verificação de conformidade com padrões de código
- Análise de gerenciamento de recursos
- Estatísticas de código

**Exemplo de uso:**
```javascript
const { codeAnalyzer } = require('./mcps');

// Gerar um relatório completo de análise de código
codeAnalyzer.generateFullReport('./src')
  .then(report => {
    console.log(`Pontuação de saúde do código: ${report.summary.healthScore}/100`);
  });
```

### 2. ROM Database

Gerencia um banco de dados de ROMs para as diferentes plataformas suportadas pelo emulador.

**Principais funcionalidades:**
- Catalogação de ROMs com metadados
- Pesquisa e filtro de ROMs
- Cálculo de hashes para verificação de integridade
- Estatísticas do banco de dados

**Exemplo de uso:**
```javascript
const { romDatabase } = require('./mcps');

// Inicializar banco de dados
romDatabase.initDatabase()
  .then(db => {
    // Escanear diretório para adicionar ROMs
    return romDatabase.scanDirectory('./roms/megadrive', 'megadrive');
  })
  .then(results => {
    console.log(`ROMs adicionadas: ${results.added}`);
  });
```

### 3. Performance Monitor

Fornece ferramentas para monitorar e analisar o desempenho do emulador em tempo real.

**Principais funcionalidades:**
- Monitoramento contínuo de métricas de desempenho
- Estatísticas de FPS, uso de memória e CPU
- Geração de relatórios de desempenho
- Comparação entre diferentes configurações

**Exemplo de uso:**
```javascript
const { performanceMonitor } = require('./mcps');

// Iniciar monitoramento contínuo
performanceMonitor.startContinuousMonitoring('megadrive', 500);

// Após algum tempo, gerar relatório
setTimeout(async () => {
  const report = await performanceMonitor.generatePerformanceReport();
  console.log(`FPS médio: ${report.fps.average}`);
  performanceMonitor.stopContinuousMonitoring();
}, 30000);
```

### 4. Debug Tools

Fornece ferramentas de depuração avançadas para o emulador.

**Principais funcionalidades:**
- Controle de execução (pausa, retomada, passo a passo)
- Definição de breakpoints e watches
- Inspeção de registradores e memória
- Desassembly de código

**Exemplo de uso:**
```javascript
const { debugTools } = require('./mcps');

// Anexar o depurador ao emulador
debugTools.attachDebugger('megadrive');

// Adicionar um breakpoint
debugTools.addBreakpoint(0x1000, '', 'Início do programa');

// Pausar a execução
debugTools.pauseExecution();

// Examinar a memória
const memData = debugTools.readMemory(0x2000, 8);
console.log(memData);

// Executar passo a passo
debugTools.stepExecution();
```

## Requisitos

- Node.js v14.0.0 ou superior
- Acesso aos diretórios do projeto Mega_Emu

## Instalação

1. Os MCPs já estão incluídos no projeto e não requerem instalação adicional.
2. Para usar em seus scripts ou ferramentas, simplesmente importe o módulo desejado.

## Integração com Outras Ferramentas

Os MCPs podem ser integrados facilmente com outras ferramentas do ecossistema Mega_Emu, como:

- Interface de linha de comando para operações em lote
- Painel de controle para monitoramento visual
- Scripts de CI/CD para testes automatizados
- Extensões de IDE para depuração ao vivo

## Adicionando Novos MCPs

Para adicionar um novo MCP:

1. Crie um novo arquivo JavaScript neste diretório seguindo o padrão dos existentes
2. Exporte suas funções com uma interface clara e bem documentada
3. Atualize o arquivo `index.js` para incluir seu novo MCP
4. Documente seu MCP neste README