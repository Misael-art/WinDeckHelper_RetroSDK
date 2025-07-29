const { updateRomMetadata } = require('./rom_database');

async function main() {
  try {
    // Exemplo: Atualizar metadados de uma ROM específica
    await updateRomMetadata('megadrive_d468fb50', {
      title: 'Aladdin',
      publisher: 'Sega',
      developer: 'Virgin Interactive',
      releaseDate: '1993-11-01',
      region: 'USA',
      genre: 'Platform',
      players: '1'
    });

    console.log('Metadados atualizados com sucesso!');
  } catch (error) {
    console.error('Erro ao atualizar metadados:', error);
  }
}

main();
