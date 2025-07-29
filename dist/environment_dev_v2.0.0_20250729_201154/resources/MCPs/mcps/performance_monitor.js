/**
 * PERFORMANCE MONITOR MCP
 * 
 * Este MCP fornece ferramentas para monitorar o desempenho do emulador Mega_Emu.
 * Permite coletar métricas de desempenho, identificar gargalos e fornecer
 * insights para otimização.
 */

const fs = require('fs').promises;
const path = require('path');
const os = require('os');
const { exec } = require('child_process');
const util = require('util');
const execAsync = util.promisify(exec);

// Configurações
const CONFIG = {
  reportsDir: path.join(__dirname, '../../docs/reports/performance'),
  samplingInterval: 100, // ms
  memoryThreshold: 500 * 1024 * 1024, // 500 MB
  cpuThreshold: 80, // 80%
  platformProfiles: {
    megadrive: {
      targetFPS: 60,
      expectedCycles: 7600000 // ~7.6MHz
    },
    nes: {
      targetFPS: 60,
      expectedCycles: 1790000 // ~1.79MHz
    },
    mastersystem: {
      targetFPS: 60,
      expectedCycles: 3580000 // ~3.58MHz
    }
  }
};

// Estatísticas de execução para monitoramento em tempo real
let runtimeStats = {
  startTime: null,
  samplesCount: 0,
  currentFPS: 0,
  averageFPS: 0,
  peakMemoryUsage: 0,
  averageMemoryUsage: 0,
  cpuUsage: 0,
  platform: '',
  cyclesPerSecond: 0,
  frameskips: 0,
  slowFrames: 0,
  status: 'idle', // idle, running, paused
  snapshots: []
};

/**
 * Inicializa o monitor de desempenho
 */
function initPerformanceMonitor(platform) {
  if (!CONFIG.platformProfiles[platform]) {
    console.warn(`Plataforma desconhecida: ${platform}, usando configurações padrão`);
    platform = 'megadrive'; // Usar como padrão
  }
  
  runtimeStats = {
    startTime: Date.now(),
    samplesCount: 0,
    currentFPS: 0,
    averageFPS: 0,
    peakMemoryUsage: 0,
    averageMemoryUsage: 0,
    cpuUsage: 0,
    platform,
    cyclesPerSecond: 0,
    frameskips: 0,
    slowFrames: 0,
    status: 'running',
    snapshots: []
  };
  
  console.log(`Monitor de desempenho inicializado para plataforma: ${platform}`);
  return runtimeStats;
}

/**
 * Coleta métricas do sistema
 */
async function collectSystemMetrics() {
  try {
    const memoryUsage = process.memoryUsage();
    
    // Em ambiente real, seria usado uma API do emulador para coletar estes dados
    // Aqui simulamos valores aproximados
    const currentStats = {
      timestamp: Date.now(),
      elapsedMs: Date.now() - runtimeStats.startTime,
      memory: {
        rss: memoryUsage.rss,
        heapTotal: memoryUsage.heapTotal,
        heapUsed: memoryUsage.heapUsed,
        external: memoryUsage.external
      },
      cpu: {
        user: 0,
        system: 0,
        total: 0
      },
      fps: Math.random() * 10 + 55, // Simulando entre 55-65 FPS
      cpuLoad: Math.random() * 30 + 20, // Simulando 20-50% de uso de CPU
      cyclesPerSecond: CONFIG.platformProfiles[runtimeStats.platform].expectedCycles * 
                      (0.9 + Math.random() * 0.2) // Variação de ±10%
    };
    
    // Atualizar estatísticas em execução
    runtimeStats.samplesCount++;
    runtimeStats.currentFPS = currentStats.fps;
    runtimeStats.averageFPS = ((runtimeStats.averageFPS * (runtimeStats.samplesCount - 1)) + 
                              currentStats.fps) / runtimeStats.samplesCount;
    
    runtimeStats.peakMemoryUsage = Math.max(runtimeStats.peakMemoryUsage, memoryUsage.rss);
    runtimeStats.averageMemoryUsage = ((runtimeStats.averageMemoryUsage * (runtimeStats.samplesCount - 1)) + 
                                      memoryUsage.rss) / runtimeStats.samplesCount;
    
    runtimeStats.cpuUsage = currentStats.cpuLoad;
    runtimeStats.cyclesPerSecond = currentStats.cyclesPerSecond;
    
    if (currentStats.fps < CONFIG.platformProfiles[runtimeStats.platform].targetFPS * 0.9) {
      runtimeStats.slowFrames++;
    }
    
    // Adicionar snapshot à lista (limitando o número de snapshots para evitar uso excessivo de memória)
    if (runtimeStats.snapshots.length >= 100) {
      runtimeStats.snapshots.shift(); // Remover o mais antigo
    }
    runtimeStats.snapshots.push(currentStats);
    
    return currentStats;
  } catch (error) {
    console.error('Erro ao coletar métricas do sistema:', error);
    return null;
  }
}

/**
 * Inicia monitoramento contínuo
 */
let monitoringInterval = null;

function startContinuousMonitoring(platform, interval = CONFIG.samplingInterval) {
  if (monitoringInterval) {
    console.log('Monitoramento já está em execução. Pare o atual antes de iniciar um novo.');
    return false;
  }
  
  initPerformanceMonitor(platform);
  
  monitoringInterval = setInterval(async () => {
    if (runtimeStats.status === 'running') {
      await collectSystemMetrics();
      
      // Verificar limites
      if (runtimeStats.peakMemoryUsage > CONFIG.memoryThreshold) {
        console.warn(`Alerta: Uso de memória acima do limite (${Math.round(runtimeStats.peakMemoryUsage / 1024 / 1024)} MB)`);
      }
      
      if (runtimeStats.cpuUsage > CONFIG.cpuThreshold) {
        console.warn(`Alerta: Uso de CPU acima do limite (${Math.round(runtimeStats.cpuUsage)}%)`);
      }
    }
  }, interval);
  
  console.log(`Monitoramento contínuo iniciado para plataforma: ${platform}, intervalo: ${interval}ms`);
  return true;
}

/**
 * Para o monitoramento contínuo
 */
function stopContinuousMonitoring() {
  if (!monitoringInterval) {
    console.log('Nenhum monitoramento em execução.');
    return false;
  }
  
  clearInterval(monitoringInterval);
  monitoringInterval = null;
  runtimeStats.status = 'idle';
  
  console.log('Monitoramento contínuo interrompido.');
  return true;
}

/**
 * Pausa ou retoma o monitoramento
 */
function pauseResumeMonitoring() {
  if (!monitoringInterval) {
    console.log('Nenhum monitoramento em execução.');
    return false;
  }
  
  if (runtimeStats.status === 'running') {
    runtimeStats.status = 'paused';
    console.log('Monitoramento pausado.');
  } else if (runtimeStats.status === 'paused') {
    runtimeStats.status = 'running';
    console.log('Monitoramento retomado.');
  }
  
  return true;
}

/**
 * Gera um relatório de desempenho
 */
async function generatePerformanceReport() {
  try {
    if (runtimeStats.samplesCount === 0) {
      console.warn('Nenhum dado coletado para gerar relatório.');
      return null;
    }
    
    const report = {
      date: new Date().toISOString(),
      platform: runtimeStats.platform,
      duration: {
        ms: Date.now() - runtimeStats.startTime,
        formatted: formatDuration(Date.now() - runtimeStats.startTime)
      },
      fps: {
        current: runtimeStats.currentFPS,
        average: runtimeStats.averageFPS,
        target: CONFIG.platformProfiles[runtimeStats.platform].targetFPS,
        percentOfTarget: (runtimeStats.averageFPS / CONFIG.platformProfiles[runtimeStats.platform].targetFPS) * 100
      },
      memory: {
        peak: {
          bytes: runtimeStats.peakMemoryUsage,
          formatted: formatBytes(runtimeStats.peakMemoryUsage)
        },
        average: {
          bytes: runtimeStats.averageMemoryUsage,
          formatted: formatBytes(runtimeStats.averageMemoryUsage)
        }
      },
      cpu: {
        current: runtimeStats.cpuUsage,
        cores: os.cpus().length
      },
      emulation: {
        cyclesPerSecond: runtimeStats.cyclesPerSecond,
        expectedCycles: CONFIG.platformProfiles[runtimeStats.platform].expectedCycles,
        slowFrames: runtimeStats.slowFrames,
        frameskips: runtimeStats.frameskips
      },
      system: {
        platform: os.platform(),
        arch: os.arch(),
        cpuModel: os.cpus()[0].model,
        totalMemory: formatBytes(os.totalmem()),
        freeMemory: formatBytes(os.freemem())
      },
      samplesCount: runtimeStats.samplesCount,
      performanceScore: calculatePerformanceScore()
    };
    
    // Salvar relatório em disco
    await saveReport(report);
    
    return report;
  } catch (error) {
    console.error('Erro ao gerar relatório de desempenho:', error);
    return null;
  }
}

/**
 * Calcula uma pontuação de desempenho com base nas métricas coletadas
 */
function calculatePerformanceScore() {
  if (runtimeStats.samplesCount === 0) {
    return 0;
  }
  
  const targetFPS = CONFIG.platformProfiles[runtimeStats.platform].targetFPS;
  const fpsRatio = Math.min(runtimeStats.averageFPS / targetFPS, 1); // Limitado a 1.0 (100%)
  
  const memoryEfficiency = 1 - Math.min(runtimeStats.peakMemoryUsage / CONFIG.memoryThreshold, 1);
  const cpuEfficiency = 1 - Math.min(runtimeStats.cpuUsage / CONFIG.cpuThreshold, 1);
  
  const slowFramesRatio = runtimeStats.slowFrames / runtimeStats.samplesCount;
  
  // Fórmula ponderada para pontuação de 0-100
  const score = (
    (fpsRatio * 50) + // FPS conta 50% da pontuação
    (memoryEfficiency * 20) + // Eficiência de memória conta 20%
    (cpuEfficiency * 20) + // Eficiência de CPU conta 20%
    ((1 - slowFramesRatio) * 10) // Ausência de frames lentos conta 10%
  );
  
  return Math.round(score);
}

/**
 * Salva o relatório de desempenho em disco
 */
async function saveReport(report) {
  const reportDir = CONFIG.reportsDir;
  const filename = `perf_report_${report.platform}_${new Date().toISOString().replace(/[:.]/g, '-')}.json`;
  const reportPath = path.join(reportDir, filename);
  
  try {
    // Garantir que o diretório existe
    await fs.mkdir(reportDir, { recursive: true });
    
    // Salvar relatório
    await fs.writeFile(reportPath, JSON.stringify(report, null, 2), 'utf8');
    console.log(`Relatório salvo em: ${reportPath}`);
    
    return reportPath;
  } catch (error) {
    console.error('Erro ao salvar relatório:', error);
    return null;
  }
}

/**
 * Compara desempenho entre diferentes configurações
 */
async function comparePerformance(reports) {
  if (!Array.isArray(reports) || reports.length < 2) {
    console.warn('São necessários pelo menos dois relatórios para comparação.');
    return null;
  }
  
  // Assume-se que todos os relatórios são da mesma plataforma para uma comparação válida
  const platform = reports[0].platform;
  
  const comparison = {
    date: new Date().toISOString(),
    platform,
    reports: reports.length,
    metrics: {
      fps: reports.map(r => r.fps.average),
      memory: reports.map(r => r.memory.peak.bytes),
      cpu: reports.map(r => r.cpu.current),
      performanceScore: reports.map(r => r.performanceScore)
    },
    best: {
      fps: Math.max(...reports.map(r => r.fps.average)),
      memory: Math.min(...reports.map(r => r.memory.peak.bytes)),
      cpu: Math.min(...reports.map(r => r.cpu.current)),
      performanceScore: Math.max(...reports.map(r => r.performanceScore))
    },
    improvement: {
      fps: calculateImprovement(reports.map(r => r.fps.average)),
      memory: calculateImprovement(reports.map(r => r.memory.peak.bytes), true),
      cpu: calculateImprovement(reports.map(r => r.cpu.current), true),
      performanceScore: calculateImprovement(reports.map(r => r.performanceScore))
    }
  };
  
  // Determinar melhor configuração geral
  const scoreIndex = reports.findIndex(r => r.performanceScore === comparison.best.performanceScore);
  comparison.bestOverallConfig = scoreIndex >= 0 ? `Configuração #${scoreIndex + 1}` : 'Indeterminado';
  
  return comparison;
}

// Funções auxiliares

/**
 * Calcula a porcentagem de melhoria entre o primeiro e último valor
 */
function calculateImprovement(values, lowerIsBetter = false) {
  if (!values.length || values.length < 2) {
    return 0;
  }
  
  const first = values[0];
  const last = values[values.length - 1];
  
  if (lowerIsBetter) {
    // Para métricas onde menor é melhor (memória, CPU)
    return first > 0 ? ((first - last) / first) * 100 : 0;
  } else {
    // Para métricas onde maior é melhor (FPS, pontuação)
    return first > 0 ? ((last - first) / first) * 100 : 0;
  }
}

/**
 * Formata bytes para string legível (KB, MB, GB)
 */
function formatBytes(bytes) {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Formata duração em ms para string legível
 */
function formatDuration(ms) {
  if (ms < 1000) {
    return `${ms}ms`;
  }
  
  const seconds = Math.floor(ms / 1000) % 60;
  const minutes = Math.floor(ms / (1000 * 60)) % 60;
  const hours = Math.floor(ms / (1000 * 60 * 60));
  
  return `${hours > 0 ? hours + 'h ' : ''}${minutes > 0 ? minutes + 'm ' : ''}${seconds}s`;
}

// Exportar funções
module.exports = {
  initPerformanceMonitor,
  collectSystemMetrics,
  startContinuousMonitoring,
  stopContinuousMonitoring,
  pauseResumeMonitoring,
  generatePerformanceReport,
  comparePerformance,
  getRuntimeStats: () => runtimeStats,
  CONFIG
};

// Para teste direto deste script
if (require.main === module) {
  startContinuousMonitoring('megadrive', 500);
  
  // Simula algumas coletas e gera um relatório após 5 segundos
  setTimeout(async () => {
    const report = await generatePerformanceReport();
    console.log(report);
    stopContinuousMonitoring();
    
    process.exit(0);
  }, 5000);
}