/**
 * Mega_Emu - MCPs - Módulos de Controle de Projeto
 * 
 * Este arquivo principal integra todos os MCPs personalizados criados para o projeto.
 */

const codeAnalyzer = require('./code_analyzer');
const romDatabase = require('./rom_database');
const performanceMonitor = require('./performance_monitor');
const debugTools = require('./debugger');

// Exportar todos os MCPs
module.exports = {
  codeAnalyzer,
  romDatabase,
  performanceMonitor,
  debugTools
};

// Informações sobre os MCPs disponíveis
const mcpInfo = {
  version: '1.0.0',
  created: '2025-03-27',
  mcps: [
    {
      name: 'Code Analyzer',
      description: 'Análise estática de código para identificar problemas e melhorias',
      mainFunctions: [
        'analyzeComplexity', 'checkCodeStyle', 'analyzeResourceManagement',
        'countCodeStats', 'generateFullReport'
      ]
    },
    {
      name: 'ROM Database',
      description: 'Gerenciamento de banco de dados de ROMs para diferentes plataformas',
      mainFunctions: [
        'initDatabase', 'addRom', 'scanDirectory', 'searchRoms', 
        'removeRom', 'updateRomMetadata', 'generateDatabaseStats'
      ]
    },
    {
      name: 'Performance Monitor',
      description: 'Monitoramento e análise de desempenho do emulador',
      mainFunctions: [
        'initPerformanceMonitor', 'collectSystemMetrics', 'startContinuousMonitoring',
        'stopContinuousMonitoring', 'generatePerformanceReport', 'comparePerformance'
      ]
    },
    {
      name: 'Debug Tools',
      description: 'Ferramentas de depuração para o emulador',
      mainFunctions: [
        'attachDebugger', 'pauseExecution', 'resumeExecution', 'stepExecution',
        'addBreakpoint', 'removeBreakpoint', 'readMemory', 'writeMemory',
        'disassemble', 'saveDebuggerState', 'loadDebuggerState'
      ]
    }
  ]
};

// Para teste direto deste script
if (require.main === module) {
  console.log('=== MCPs do Mega_Emu ===');
  console.log(`Versão: ${mcpInfo.version}`);
  console.log(`Data de Criação: ${mcpInfo.created}`);
  console.log('\nMódulos disponíveis:');
  
  mcpInfo.mcps.forEach(mcp => {
    console.log(`\n- ${mcp.name}: ${mcp.description}`);
    console.log('  Funções principais:');
    mcp.mainFunctions.forEach(fn => console.log(`    * ${fn}`));
  });
}