/**
 * ROM DATABASE MCP
 *
 * Este MCP fornece ferramentas para gerenciar o banco de dados de ROMs do Mega_Emu.
 * Permite catalogar, pesquisar e gerenciar metadados de ROMs para as diferentes
 * plataformas suportadas.
 */

const fs = require('fs').promises;
const path = require('path');
const crypto = require('crypto');

// Configurações
const CONFIG = {
  databasePath: path.join(__dirname, '../../data/roms/database.json'),
  romsDir: path.join(__dirname, '../../data/roms'),
  supportedPlatforms: ['megadrive', 'nes', 'mastersystem', 'gamegear'],
  hashAlgorithm: 'sha1'
};

// Garantir que o diretório de dados existe
async function ensureDirectoriesExist() {
  try {
    await fs.mkdir(path.dirname(CONFIG.databasePath), { recursive: true });
    for (const platform of CONFIG.supportedPlatforms) {
      await fs.mkdir(path.join(CONFIG.romsDir, platform), { recursive: true });
    }
  } catch (error) {
    console.error('Erro ao criar diretórios:', error);
  }
}

// Estrutura inicial do banco de dados
const emptyDatabase = {
  version: "1.0.0",
  lastUpdated: new Date().toISOString(),
  platforms: {
    megadrive: { count: 0, roms: {} },
    nes: { count: 0, roms: {} },
    mastersystem: { count: 0, roms: {} },
    gamegear: { count: 0, roms: {} }
  },
  totalRoms: 0
};

/**
 * Inicializa ou carrega o banco de dados de ROMs
 */
async function initDatabase() {
  await ensureDirectoriesExist();

  try {
    await fs.access(CONFIG.databasePath);
    // O arquivo existe, carregar
    const data = await fs.readFile(CONFIG.databasePath, 'utf8');
    return JSON.parse(data);
  } catch (error) {
    // Arquivo não existe, criar novo
    console.log('Criando novo banco de dados de ROMs...');
    await fs.writeFile(CONFIG.databasePath, JSON.stringify(emptyDatabase, null, 2), 'utf8');
    return emptyDatabase;
  }
}

/**
 * Calcula o hash de um arquivo ROM
 */
async function calculateRomHash(romPath) {
  try {
    console.log(`Tentando ler arquivo: ${romPath}`);
    const exists = await fs.access(romPath).then(() => true).catch(() => false);
    if (!exists) {
      console.error(`Arquivo não encontrado: ${romPath}`);
      return null;
    }

    const stats = await fs.stat(romPath);
    console.log(`Tamanho do arquivo: ${stats.size} bytes`);

    const data = await fs.readFile(romPath);
    console.log(`Arquivo lido com sucesso, tamanho do buffer: ${data.length}`);

    const hash = crypto.createHash(CONFIG.hashAlgorithm).update(data).digest('hex');
    console.log(`Hash calculado: ${hash}`);
    return hash;
  } catch (error) {
    console.error(`Erro detalhado ao calcular hash para ${romPath}:`, error);
    return null;
  }
}

/**
 * Adiciona uma ROM ao banco de dados
 */
async function addRom(romPath, platform, metadata = {}) {
  if (!CONFIG.supportedPlatforms.includes(platform)) {
    throw new Error(`Plataforma não suportada: ${platform}`);
  }

  try {
    const db = await initDatabase();
    const romFilename = path.basename(romPath);
    const hash = await calculateRomHash(romPath);

    if (!hash) {
      throw new Error(`Não foi possível calcular hash para ${romPath}`);
    }

    // Verificar se ROM já existe por hash
    const platformData = db.platforms[platform];
    const existingRoms = Object.values(platformData.roms);
    const existingRom = existingRoms.find(rom => rom.hash === hash);

    if (existingRom) {
      console.log(`ROM já existe no banco de dados: ${existingRom.name}`);
      return existingRom;
    }

    // Adicionar nova ROM
    const romId = `${platform}_${hash.substring(0, 8)}`;
    const romInfo = {
      id: romId,
      name: metadata.name || romFilename,
      filename: romFilename,
      hash: hash,
      path: romPath,
      size: (await fs.stat(romPath)).size,
      platform: platform,
      added: new Date().toISOString(),
      metadata: {
        title: metadata.title || metadata.name || romFilename,
        description: metadata.description || '',
        publisher: metadata.publisher || 'Desconhecido',
        developer: metadata.developer || 'Desconhecido',
        releaseDate: metadata.releaseDate || 'Desconhecido',
        region: metadata.region || 'Desconhecido',
        genre: metadata.genre || 'Desconhecido',
        players: metadata.players || '1'
      }
    };

    // Atualizar banco de dados
    db.platforms[platform].roms[romId] = romInfo;
    db.platforms[platform].count = Object.keys(db.platforms[platform].roms).length;
    db.totalRoms = Object.values(db.platforms).reduce((total, platform) => total + platform.count, 0);
    db.lastUpdated = new Date().toISOString();

    // Salvar banco de dados
    await fs.writeFile(CONFIG.databasePath, JSON.stringify(db, null, 2), 'utf8');
    console.log(`ROM adicionada ao banco de dados: ${romInfo.name}`);

    return romInfo;
  } catch (error) {
    console.error(`Erro ao adicionar ROM ${romPath}:`, error);
    throw error;
  }
}

/**
 * Escaneia um diretório e adiciona todas as ROMs encontradas
 */
async function scanDirectory(directory, platform) {
  if (!CONFIG.supportedPlatforms.includes(platform)) {
    throw new Error(`Plataforma não suportada: ${platform}`);
  }

  try {
    const files = await fs.readdir(directory);
    console.log(`Escaneando ${files.length} arquivos em ${directory}...`);

    const results = {
      added: 0,
      skipped: 0,
      errors: 0,
      details: []
    };

    for (const file of files) {
      const filePath = path.join(directory, file);
      const stats = await fs.stat(filePath);

      if (stats.isFile()) {
        try {
          await addRom(filePath, platform);
          results.added++;
          results.details.push({ file, status: 'added' });
        } catch (error) {
          console.error(`Erro ao adicionar ${file}:`, error);
          results.errors++;
          results.details.push({ file, status: 'error', error: error.message });
        }
      } else if (stats.isDirectory()) {
        // Opcionalmente, para escanear recursivamente
        // const subResults = await scanDirectory(filePath, platform);
        // results.added += subResults.added;
        // results.skipped += subResults.skipped;
        // results.errors += subResults.errors;
        results.skipped++;
        results.details.push({ file, status: 'skipped', reason: 'directory' });
      }
    }

    console.log(`Escaneamento concluído: ${results.added} adicionados, ${results.skipped} ignorados, ${results.errors} erros`);
    return results;
  } catch (error) {
    console.error(`Erro ao escanear diretório ${directory}:`, error);
    throw error;
  }
}

/**
 * Pesquisa ROMs no banco de dados
 */
async function searchRoms(query, options = {}) {
  const db = await initDatabase();
  const results = [];

  const platforms = options.platform ? [options.platform] : CONFIG.supportedPlatforms;

  for (const platform of platforms) {
    if (!db.platforms[platform]) continue;

    const roms = Object.values(db.platforms[platform].roms);

    for (const rom of roms) {
      const matchesQuery =
        !query ||
        rom.name.toLowerCase().includes(query.toLowerCase()) ||
        rom.metadata.title.toLowerCase().includes(query.toLowerCase()) ||
        rom.metadata.publisher.toLowerCase().includes(query.toLowerCase()) ||
        rom.metadata.developer.toLowerCase().includes(query.toLowerCase());

      if (matchesQuery) {
        results.push(rom);
      }
    }
  }

  // Ordenar resultados
  if (options.sortBy) {
    results.sort((a, b) => {
      if (options.sortBy === 'name') {
        return a.name.localeCompare(b.name);
      } else if (options.sortBy === 'date') {
        return new Date(b.added) - new Date(a.added);
      } else if (options.sortBy === 'size') {
        return b.size - a.size;
      }
      return 0;
    });
  }

  // Limitar resultados
  if (options.limit) {
    return results.slice(0, options.limit);
  }

  return results;
}

/**
 * Remove uma ROM do banco de dados
 */
async function removeRom(romId) {
  const db = await initDatabase();
  let removed = false;

  for (const platform of CONFIG.supportedPlatforms) {
    if (db.platforms[platform].roms[romId]) {
      console.log(`Removendo ROM ${db.platforms[platform].roms[romId].name}`);
      delete db.platforms[platform].roms[romId];
      db.platforms[platform].count = Object.keys(db.platforms[platform].roms).length;
      removed = true;
    }
  }

  if (removed) {
    db.totalRoms = Object.values(db.platforms).reduce((total, platform) => total + platform.count, 0);
    db.lastUpdated = new Date().toISOString();
    await fs.writeFile(CONFIG.databasePath, JSON.stringify(db, null, 2), 'utf8');
    return true;
  }

  console.log(`ROM ${romId} não encontrada`);
  return false;
}

/**
 * Atualiza metadados de uma ROM
 */
async function updateRomMetadata(romId, metadata) {
  const db = await initDatabase();
  let updated = false;

  for (const platform of CONFIG.supportedPlatforms) {
    if (db.platforms[platform].roms[romId]) {
      const rom = db.platforms[platform].roms[romId];

      // Atualizar campos
      if (metadata.name) rom.name = metadata.name;
      if (metadata.title) rom.metadata.title = metadata.title;
      if (metadata.description) rom.metadata.description = metadata.description;
      if (metadata.publisher) rom.metadata.publisher = metadata.publisher;
      if (metadata.developer) rom.metadata.developer = metadata.developer;
      if (metadata.releaseDate) rom.metadata.releaseDate = metadata.releaseDate;
      if (metadata.region) rom.metadata.region = metadata.region;
      if (metadata.genre) rom.metadata.genre = metadata.genre;
      if (metadata.players) rom.metadata.players = metadata.players;

      rom.lastUpdated = new Date().toISOString();
      updated = true;
      console.log(`Metadados atualizados para ROM ${rom.name}`);
    }
  }

  if (updated) {
    db.lastUpdated = new Date().toISOString();
    await fs.writeFile(CONFIG.databasePath, JSON.stringify(db, null, 2), 'utf8');
    return true;
  }

  console.log(`ROM ${romId} não encontrada`);
  return false;
}

/**
 * Gera estatísticas do banco de dados de ROMs
 */
async function generateDatabaseStats() {
  const db = await initDatabase();

  const stats = {
    totalRoms: db.totalRoms,
    byPlatform: {},
    byPublisher: {},
    byReleaseYear: {},
    byRegion: {},
    byGenre: {},
    sizeStats: {
      total: 0,
      average: 0,
      min: Number.MAX_SAFE_INTEGER,
      max: 0
    }
  };

  let totalSize = 0;
  let romCount = 0;

  // Processar cada plataforma
  for (const platform of CONFIG.supportedPlatforms) {
    const platformData = db.platforms[platform];
    stats.byPlatform[platform] = platformData.count;

    // Processar ROMs desta plataforma
    for (const romId in platformData.roms) {
      const rom = platformData.roms[romId];
      romCount++;

      // Estatísticas por publisher
      const publisher = rom.metadata.publisher;
      stats.byPublisher[publisher] = (stats.byPublisher[publisher] || 0) + 1;

      // Estatísticas por ano de lançamento
      const releaseYear = typeof rom.metadata.releaseDate === 'string' ?
        rom.metadata.releaseDate.substring(0, 4) : 'Desconhecido';
      stats.byReleaseYear[releaseYear] = (stats.byReleaseYear[releaseYear] || 0) + 1;

      // Estatísticas por região
      const region = rom.metadata.region;
      stats.byRegion[region] = (stats.byRegion[region] || 0) + 1;

      // Estatísticas por gênero
      const genre = rom.metadata.genre;
      stats.byGenre[genre] = (stats.byGenre[genre] || 0) + 1;

      // Estatísticas de tamanho
      const size = rom.size;
      totalSize += size;
      stats.sizeStats.min = Math.min(stats.sizeStats.min, size);
      stats.sizeStats.max = Math.max(stats.sizeStats.max, size);
    }
  }

  // Finalizar estatísticas de tamanho
  stats.sizeStats.total = totalSize;
  stats.sizeStats.average = romCount > 0 ? Math.round(totalSize / romCount) : 0;
  if (stats.sizeStats.min === Number.MAX_SAFE_INTEGER) {
    stats.sizeStats.min = 0;
  }

  return stats;
}

// Exportar funções
module.exports = {
  initDatabase,
  addRom,
  scanDirectory,
  searchRoms,
  removeRom,
  updateRomMetadata,
  generateDatabaseStats,
  calculateRomHash,
  CONFIG
};

// Para teste direto deste script
if (require.main === module) {
  generateDatabaseStats().then(console.log);
}
