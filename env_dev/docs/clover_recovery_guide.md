# Guia de Recuperação do Clover Boot Manager

Este guia fornece instruções detalhadas sobre como recuperar seu sistema em caso de problemas com o Clover Boot Manager.

## Introdução

O Clover Boot Manager é uma ferramenta poderosa para gerenciar múltiplos sistemas operacionais em um único computador. No entanto, como ele modifica o processo de inicialização do sistema, problemas na instalação ou configuração podem impedir que seu computador inicie corretamente.

Este guia fornece instruções para recuperar seu sistema em diferentes cenários de falha.

## Cenários de Falha Comuns

### 1. Sistema não inicia após instalação do Clover

Se o sistema não iniciar após a instalação do Clover, você pode:

- Iniciar em modo seguro (pressione F8 durante a inicialização)
- Usar uma mídia de recuperação do Windows
- Usar o utilitário de recuperação do Clover

### 2. Clover inicia, mas não mostra todos os sistemas operacionais

Se o Clover iniciar, mas não mostrar todos os sistemas operacionais instalados:

- Verifique a configuração do Clover em `EFI/CLOVER/config.plist`
- Execute o utilitário de detecção de sistemas operacionais

### 3. Erros durante a inicialização do Clover

Se o Clover apresentar erros durante a inicialização:

- Verifique os logs do Clover
- Restaure o bootloader original

## Utilitário de Recuperação do Clover

O Environment Dev Script inclui um utilitário de recuperação do Clover que pode ser usado para resolver problemas de inicialização.

### Como acessar o utilitário de recuperação

1. Inicie o Windows em modo seguro (pressione F8 durante a inicialização)
2. Abra um prompt de comando como administrador
3. Execute o seguinte comando:

```powershell
powershell -ExecutionPolicy Bypass -File "D:\Steamapps\DevProjetos\PC Engines Projects\Environment_dev_Script\env_dev\config\scripts\clover_recovery.ps1"
```

### Opções do utilitário de recuperação

O utilitário de recuperação oferece as seguintes opções:

1. **Restaurar partição EFI a partir de backup**: Restaura a partição EFI a partir de um backup criado durante a instalação do Clover.
2. **Reparar bootloader do Windows**: Repara o bootloader do Windows usando os comandos `bootrec`.
3. **Verificar instalação do Clover**: Verifica a integridade da instalação do Clover.
4. **Desinstalar Clover**: Remove o Clover e restaura o bootloader original.

## Restauração Manual do Bootloader Original

Se você não conseguir acessar o utilitário de recuperação, pode restaurar manualmente o bootloader original seguindo estas etapas:

1. Inicie o Windows em modo seguro ou use uma mídia de recuperação do Windows
2. Abra um prompt de comando como administrador
3. Execute os seguintes comandos:

```powershell
# Montar a partição EFI
$disks = Get-Disk | Where-Object {$_.PartitionStyle -eq "GPT"}
$efiPartition = $disks | Get-Partition | Where-Object {$_.GptType -eq "{c12a7328-f81f-11d2-ba4b-00a0c93ec93b}"}
$driveLetter = "S"
$efiPartition | Add-PartitionAccessPath -AccessPath "${driveLetter}:"

# Restaurar o bootloader original
if (Test-Path "${driveLetter}:\EFI\BOOT\BOOTX64.efi.original") {
    Copy-Item -Path "${driveLetter}:\EFI\BOOT\BOOTX64.efi.original" -Destination "${driveLetter}:\EFI\BOOT\BOOTX64.efi" -Force
    Write-Host "Bootloader original restaurado com sucesso!" -ForegroundColor Green
} else {
    Write-Host "Backup do bootloader original não encontrado." -ForegroundColor Red
}

# Desmontar a partição EFI
$efiPartition | Remove-PartitionAccessPath -AccessPath "${driveLetter}:"
```

## Reparação do Bootloader do Windows

Se você precisar reparar o bootloader do Windows, siga estas etapas:

1. Inicie o Windows em modo seguro ou use uma mídia de recuperação do Windows
2. Abra um prompt de comando como administrador
3. Execute os seguintes comandos:

```cmd
bootrec /fixmbr
bootrec /fixboot
bootrec /rebuildbcd
```

## Prevenção de Problemas

Para evitar problemas com o Clover Boot Manager:

1. **Sempre crie um backup da partição EFI antes de instalar ou atualizar o Clover**
2. **Preserve o bootloader original durante a instalação**
3. **Mantenha uma mídia de recuperação do Windows à mão**
4. **Documente as configurações do seu sistema**

## Suporte Adicional

Se você encontrar problemas que não consegue resolver usando este guia, entre em contato com o suporte do Environment Dev Script ou consulte a documentação oficial do Clover Boot Manager.

---

*Este guia foi criado para o Environment Dev Script. Última atualização: [DATA]*
