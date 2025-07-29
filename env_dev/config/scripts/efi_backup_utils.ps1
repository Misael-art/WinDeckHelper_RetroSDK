# Utilitários para backup e restauração da partição EFI
# Este script contém funções para gerenciar backups permanentes da partição EFI

# Diretório base para backups permanentes
$EFI_BACKUP_BASE_DIR = "$env:USERPROFILE\Documents\Environment_Dev\EFI_Backups"

function New-EfiBackup {
    <#
    .SYNOPSIS
        Cria um backup permanente da partição EFI.
    .DESCRIPTION
        Cria um backup completo da partição EFI em um local permanente,
        registrando metadados para possível restauração futura.
    .PARAMETER EfiDriveLetter
        Letra da unidade da partição EFI. Se não for fornecida, tentará encontrar automaticamente.
    .PARAMETER BackupName
        Nome personalizado para o backup. Se não for fornecido, será usado um timestamp.
    .OUTPUTS
        Retorna um objeto com informações sobre o backup criado.
    #>
    [CmdletBinding()]
    param (
        [Parameter(Mandatory=$false)]
        [string]$EfiDriveLetter,
        
        [Parameter(Mandatory=$false)]
        [string]$BackupName
    )
    
    # Criar diretório base de backups se não existir
    if (-not (Test-Path $EFI_BACKUP_BASE_DIR)) {
        New-Item -Path $EFI_BACKUP_BASE_DIR -ItemType Directory -Force | Out-Null
        Write-Host "Diretório de backups criado: $EFI_BACKUP_BASE_DIR" -ForegroundColor Green
    }
    
    # Gerar nome do backup baseado em timestamp se não fornecido
    if (-not $BackupName) {
        $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $BackupName = "EFI_Backup_$timestamp"
    }
    
    $backupPath = Join-Path -Path $EFI_BACKUP_BASE_DIR -ChildPath $BackupName
    
    # Criar diretório para este backup específico
    New-Item -Path $backupPath -ItemType Directory -Force | Out-Null
    
    # Encontrar a partição EFI se não fornecida
    $efiVolume = $null
    $tempDriveCreated = $false
    
    if (-not $EfiDriveLetter) {
        Write-Host "Procurando partição EFI..." -ForegroundColor Yellow
        $disks = Get-Disk | Where-Object {$_.PartitionStyle -eq "GPT"}
        
        foreach ($disk in $disks) {
            $efiPartitions = $disk | Get-Partition | Where-Object {$_.GptType -eq "{c12a7328-f81f-11d2-ba4b-00a0c93ec93b}"}
            
            if ($efiPartitions) {
                try {
                    # Obter volume da partição EFI
                    $efiVolume = $efiPartitions[0] | Get-Volume
                    
                    # Se não tiver letra de unidade, atribuir uma temporária
                    if (-not $efiVolume.DriveLetter) {
                        $driveLetter = 69 # Letra 'E'
                        while ([char]$driveLetter -le 90) {
                            $letter = [char]$driveLetter
                            if (-not (Get-Volume -DriveLetter $letter -ErrorAction SilentlyContinue)) {
                                $efiPartitions[0] | Add-PartitionAccessPath -AccessPath "${letter}:"
                                $efiVolume = Get-Volume -DriveLetter $letter
                                $tempDriveCreated = $true
                                Write-Host "Atribuída letra temporária $letter à partição EFI" -ForegroundColor Yellow
                                break
                            }
                            $driveLetter++
                        }
                    }
                    
                    if ($efiVolume.DriveLetter) {
                        $EfiDriveLetter = $efiVolume.DriveLetter
                        break
                    }
                } catch {
                    Write-Host "Erro ao acessar partição EFI: $_" -ForegroundColor Red
                }
            }
        }
    } else {
        # Verificar se a letra fornecida existe
        $efiVolume = Get-Volume -DriveLetter $EfiDriveLetter -ErrorAction SilentlyContinue
        if (-not $efiVolume) {
            Write-Host "Letra de unidade $EfiDriveLetter não encontrada" -ForegroundColor Red
            return $null
        }
    }
    
    # Verificar se encontramos a partição EFI
    if (-not $EfiDriveLetter) {
        Write-Host "Não foi possível encontrar ou montar a partição EFI" -ForegroundColor Red
        return $null
    }
    
    $efiPath = "${EfiDriveLetter}:"
    
    # Verificar se o diretório EFI existe
    if (-not (Test-Path "$efiPath\EFI")) {
        Write-Host "Diretório EFI não encontrado em $efiPath" -ForegroundColor Red
        
        # Limpar letra de unidade temporária se foi criada
        if ($tempDriveCreated) {
            $efiPartitions[0] | Remove-PartitionAccessPath -AccessPath "$efiPath"
            Write-Host "Removida letra de unidade temporária $EfiDriveLetter" -ForegroundColor Yellow
        }
        
        return $null
    }
    
    # Realizar o backup
    Write-Host "Criando backup da partição EFI ($efiPath) em $backupPath..." -ForegroundColor Green
    
    try {
        # Copiar todo o conteúdo da partição EFI
        Copy-Item -Path "$efiPath\*" -Destination $backupPath -Recurse -Force
        
        # Registrar metadados do backup
        $backupInfo = @{
            Date = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
            Path = $backupPath
            EfiDriveLetter = $EfiDriveLetter
            DiskNumber = $disk.Number
            BackupName = $BackupName
            TempDriveCreated = $tempDriveCreated
            BootloaderEntries = @()
        }
        
        # Registrar entradas de bootloader encontradas
        if (Test-Path "$efiPath\EFI\BOOT") {
            $bootloaderEntries = Get-ChildItem -Path "$efiPath\EFI\BOOT" -Filter "*.efi" | Select-Object -ExpandProperty Name
            $backupInfo.BootloaderEntries += $bootloaderEntries
        }
        
        # Salvar metadados
        $backupInfo | ConvertTo-Json -Depth 4 | Out-File -FilePath "$backupPath\backup_info.json" -Encoding utf8 -Force
        
        # Criar arquivo de recuperação
        $recoveryScript = @"
# Script de recuperação para backup EFI: $BackupName
# Criado em: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

`$backupPath = "$backupPath"
`$efiDriveLetter = "$EfiDriveLetter"

Write-Host "Iniciando restauração da partição EFI a partir do backup: `$backupPath" -ForegroundColor Yellow
Write-Host "AVISO: Este processo substituirá o conteúdo atual da partição EFI!" -ForegroundColor Red
Write-Host "Pressione CTRL+C para cancelar ou qualquer outra tecla para continuar..." -ForegroundColor Yellow
`$null = `$Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# Verificar se o backup existe
if (-not (Test-Path "`$backupPath")) {
    Write-Host "Backup não encontrado em: `$backupPath" -ForegroundColor Red
    exit 1
}

# Verificar se a partição EFI está acessível
`$efiPath = "`${efiDriveLetter}:"
if (-not (Test-Path "`$efiPath\EFI")) {
    Write-Host "Partição EFI não encontrada ou não montada em `$efiPath" -ForegroundColor Red
    
    # Tentar encontrar e montar a partição EFI
    `$disks = Get-Disk | Where-Object {`$_.PartitionStyle -eq "GPT"}
    `$efiFound = `$false
    
    foreach (`$disk in `$disks) {
        `$efiPartitions = `$disk | Get-Partition | Where-Object {`$_.GptType -eq "{c12a7328-f81f-11d2-ba4b-00a0c93ec93b}"}
        if (`$efiPartitions) {
            try {
                # Tentar montar com a letra especificada
                `$efiPartitions[0] | Add-PartitionAccessPath -AccessPath "`$efiPath"
                if (Test-Path "`$efiPath\EFI") {
                    `$efiFound = `$true
                    Write-Host "Partição EFI montada em `$efiPath" -ForegroundColor Green
                    break
                }
            } catch {
                Write-Host "Erro ao montar partição EFI: `$_" -ForegroundColor Red
            }
        }
    }
    
    if (-not `$efiFound) {
        Write-Host "Não foi possível encontrar ou montar a partição EFI. Abortando." -ForegroundColor Red
        exit 1
    }
}

# Fazer backup do estado atual antes da restauração
`$tempBackupDir = "`$env:TEMP\EFI_Temp_Backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
New-Item -Path `$tempBackupDir -ItemType Directory -Force | Out-Null
Write-Host "Criando backup temporário do estado atual em `$tempBackupDir..." -ForegroundColor Yellow
Copy-Item -Path "`$efiPath\*" -Destination `$tempBackupDir -Recurse -Force

# Restaurar o backup
Write-Host "Restaurando backup para a partição EFI..." -ForegroundColor Green
try {
    # Limpar diretório EFI (preservando outros arquivos na raiz)
    if (Test-Path "`$efiPath\EFI") {
        Remove-Item -Path "`$efiPath\EFI" -Recurse -Force
    }
    
    # Copiar arquivos do backup
    Copy-Item -Path "`$backupPath\*" -Destination "`$efiPath\" -Recurse -Force
    
    Write-Host "Restauração concluída com sucesso!" -ForegroundColor Green
    Write-Host "Um backup temporário do estado anterior foi salvo em: `$tempBackupDir" -ForegroundColor Yellow
} catch {
    Write-Host "Erro durante a restauração: `$_" -ForegroundColor Red
    Write-Host "Tentando restaurar o estado anterior..." -ForegroundColor Yellow
    
    try {
        # Tentar restaurar o estado anterior
        if (Test-Path "`$efiPath\EFI") {
            Remove-Item -Path "`$efiPath\EFI" -Recurse -Force
        }
        Copy-Item -Path "`$tempBackupDir\*" -Destination "`$efiPath\" -Recurse -Force
        Write-Host "Estado anterior restaurado." -ForegroundColor Green
    } catch {
        Write-Host "Falha ao restaurar estado anterior: `$_" -ForegroundColor Red
        Write-Host "ATENÇÃO: Seu sistema pode não inicializar corretamente!" -ForegroundColor Red
    }
    
    exit 1
}

Write-Host "Pressione qualquer tecla para sair..."
`$null = `$Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
"@
        
        # Salvar script de recuperação
        $recoveryScript | Out-File -FilePath "$backupPath\restore_efi.ps1" -Encoding utf8 -Force
        
        # Criar arquivo batch para facilitar a restauração
        $batchContent = @"
@echo off
echo EFI Backup Restore Utility
echo =========================
echo.
echo Este utilitario ira restaurar o backup da particao EFI.
echo AVISO: Este processo substituira o conteudo atual da particao EFI!
echo.
echo Pressione CTRL+C para cancelar ou qualquer tecla para continuar...
pause > nul

powershell -ExecutionPolicy Bypass -File "%~dp0restore_efi.ps1"
"@
        
        $batchContent | Out-File -FilePath "$backupPath\restore_efi.bat" -Encoding ASCII -Force
        
        # Limpar letra de unidade temporária se foi criada
        if ($tempDriveCreated) {
            $efiPartitions[0] | Remove-PartitionAccessPath -AccessPath "$efiPath"
            Write-Host "Removida letra de unidade temporária $EfiDriveLetter" -ForegroundColor Yellow
        }
        
        Write-Host "Backup da partição EFI concluído com sucesso!" -ForegroundColor Green
        Write-Host "Backup salvo em: $backupPath" -ForegroundColor Green
        Write-Host "Para restaurar, execute o arquivo 'restore_efi.bat' no diretório do backup." -ForegroundColor Yellow
        
        return $backupInfo
    } catch {
        Write-Host "Erro ao criar backup da partição EFI: $_" -ForegroundColor Red
        
        # Limpar letra de unidade temporária se foi criada
        if ($tempDriveCreated) {
            $efiPartitions[0] | Remove-PartitionAccessPath -AccessPath "$efiPath"
            Write-Host "Removida letra de unidade temporária $EfiDriveLetter" -ForegroundColor Yellow
        }
        
        return $null
    }
}

function Restore-EfiBackup {
    <#
    .SYNOPSIS
        Restaura um backup da partição EFI.
    .DESCRIPTION
        Restaura um backup previamente criado da partição EFI.
    .PARAMETER BackupPath
        Caminho completo para o diretório de backup.
    .PARAMETER Force
        Se deve forçar a restauração sem confirmação.
    #>
    [CmdletBinding()]
    param (
        [Parameter(Mandatory=$true)]
        [string]$BackupPath,
        
        [Parameter(Mandatory=$false)]
        [switch]$Force
    )
    
    # Verificar se o backup existe
    if (-not (Test-Path $BackupPath)) {
        Write-Host "Backup não encontrado em: $BackupPath" -ForegroundColor Red
        return $false
    }
    
    # Verificar se o arquivo de metadados existe
    $metadataPath = Join-Path -Path $BackupPath -ChildPath "backup_info.json"
    if (-not (Test-Path $metadataPath)) {
        Write-Host "Arquivo de metadados do backup não encontrado: $metadataPath" -ForegroundColor Red
        return $false
    }
    
    # Carregar metadados do backup
    $backupInfo = Get-Content -Path $metadataPath -Raw | ConvertFrom-Json
    $efiDriveLetter = $backupInfo.EfiDriveLetter
    
    # Confirmar restauração
    if (-not $Force) {
        Write-Host "AVISO: Este processo substituirá o conteúdo atual da partição EFI!" -ForegroundColor Red
        Write-Host "Backup a ser restaurado: $($backupInfo.BackupName) criado em $($backupInfo.Date)" -ForegroundColor Yellow
        $confirmation = Read-Host "Tem certeza que deseja continuar? (S/N)"
        if ($confirmation -ne "S") {
            Write-Host "Operação cancelada pelo usuário." -ForegroundColor Yellow
            return $false
        }
    }
    
    # Verificar se a partição EFI está acessível
    $efiPath = "${efiDriveLetter}:"
    $tempDriveCreated = $false
    
    if (-not (Test-Path "$efiPath\EFI")) {
        Write-Host "Partição EFI não encontrada ou não montada em $efiPath" -ForegroundColor Red
        
        # Tentar encontrar e montar a partição EFI
        $disks = Get-Disk | Where-Object {$_.PartitionStyle -eq "GPT"}
        $efiFound = $false
        
        foreach ($disk in $disks) {
            $efiPartitions = $disk | Get-Partition | Where-Object {$_.GptType -eq "{c12a7328-f81f-11d2-ba4b-00a0c93ec93b}"}
            if ($efiPartitions) {
                try {
                    # Obter volume da partição EFI
                    $efiVolume = $efiPartitions[0] | Get-Volume
                    
                    # Se não tiver letra de unidade, atribuir uma temporária
                    if (-not $efiVolume.DriveLetter) {
                        $driveLetter = 69 # Letra 'E'
                        while ([char]$driveLetter -le 90) {
                            $letter = [char]$driveLetter
                            if (-not (Get-Volume -DriveLetter $letter -ErrorAction SilentlyContinue)) {
                                $efiPartitions[0] | Add-PartitionAccessPath -AccessPath "${letter}:"
                                $efiVolume = Get-Volume -DriveLetter $letter
                                $efiDriveLetter = $letter
                                $tempDriveCreated = $true
                                Write-Host "Atribuída letra temporária $letter à partição EFI" -ForegroundColor Yellow
                                break
                            }
                            $driveLetter++
                        }
                    } else {
                        $efiDriveLetter = $efiVolume.DriveLetter
                    }
                    
                    if ($efiVolume.DriveLetter) {
                        $efiPath = "${efiDriveLetter}:"
                        if (Test-Path "$efiPath") {
                            $efiFound = $true
                            Write-Host "Partição EFI encontrada em $efiPath" -ForegroundColor Green
                            break
                        }
                    }
                } catch {
                    Write-Host "Erro ao acessar partição EFI: $_" -ForegroundColor Red
                }
            }
        }
        
        if (-not $efiFound) {
            Write-Host "Não foi possível encontrar ou montar a partição EFI. Abortando." -ForegroundColor Red
            return $false
        }
    }
    
    # Fazer backup do estado atual antes da restauração
    $tempBackupDir = "$env:TEMP\EFI_Temp_Backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    New-Item -Path $tempBackupDir -ItemType Directory -Force | Out-Null
    Write-Host "Criando backup temporário do estado atual em $tempBackupDir..." -ForegroundColor Yellow
    Copy-Item -Path "$efiPath\*" -Destination $tempBackupDir -Recurse -Force
    
    # Restaurar o backup
    Write-Host "Restaurando backup para a partição EFI..." -ForegroundColor Green
    try {
        # Limpar diretório EFI (preservando outros arquivos na raiz)
        if (Test-Path "$efiPath\EFI") {
            Remove-Item -Path "$efiPath\EFI" -Recurse -Force
        }
        
        # Copiar arquivos do backup
        Copy-Item -Path "$BackupPath\*" -Destination "$efiPath\" -Recurse -Force -Exclude "backup_info.json", "restore_efi.ps1", "restore_efi.bat"
        
        Write-Host "Restauração concluída com sucesso!" -ForegroundColor Green
        Write-Host "Um backup temporário do estado anterior foi salvo em: $tempBackupDir" -ForegroundColor Yellow
        
        # Limpar letra de unidade temporária se foi criada
        if ($tempDriveCreated) {
            $efiPartitions[0] | Remove-PartitionAccessPath -AccessPath "$efiPath"
            Write-Host "Removida letra de unidade temporária $efiDriveLetter" -ForegroundColor Yellow
        }
        
        return $true
    } catch {
        Write-Host "Erro durante a restauração: $_" -ForegroundColor Red
        Write-Host "Tentando restaurar o estado anterior..." -ForegroundColor Yellow
        
        try {
            # Tentar restaurar o estado anterior
            if (Test-Path "$efiPath\EFI") {
                Remove-Item -Path "$efiPath\EFI" -Recurse -Force
            }
            Copy-Item -Path "$tempBackupDir\*" -Destination "$efiPath\" -Recurse -Force
            Write-Host "Estado anterior restaurado." -ForegroundColor Green
        } catch {
            Write-Host "Falha ao restaurar estado anterior: $_" -ForegroundColor Red
            Write-Host "ATENÇÃO: Seu sistema pode não inicializar corretamente!" -ForegroundColor Red
        }
        
        # Limpar letra de unidade temporária se foi criada
        if ($tempDriveCreated) {
            $efiPartitions[0] | Remove-PartitionAccessPath -AccessPath "$efiPath"
            Write-Host "Removida letra de unidade temporária $efiDriveLetter" -ForegroundColor Yellow
        }
        
        return $false
    }
}

function Get-EfiBackups {
    <#
    .SYNOPSIS
        Lista todos os backups EFI disponíveis.
    .DESCRIPTION
        Retorna uma lista de todos os backups EFI disponíveis no diretório de backups.
    #>
    [CmdletBinding()]
    param ()
    
    # Verificar se o diretório de backups existe
    if (-not (Test-Path $EFI_BACKUP_BASE_DIR)) {
        Write-Host "Diretório de backups não encontrado: $EFI_BACKUP_BASE_DIR" -ForegroundColor Yellow
        return @()
    }
    
    # Encontrar todos os diretórios de backup
    $backupDirs = Get-ChildItem -Path $EFI_BACKUP_BASE_DIR -Directory
    $backups = @()
    
    foreach ($dir in $backupDirs) {
        $metadataPath = Join-Path -Path $dir.FullName -ChildPath "backup_info.json"
        if (Test-Path $metadataPath) {
            try {
                $metadata = Get-Content -Path $metadataPath -Raw | ConvertFrom-Json
                $backups += [PSCustomObject]@{
                    Name = $dir.Name
                    Path = $dir.FullName
                    Date = $metadata.Date
                    EfiDriveLetter = $metadata.EfiDriveLetter
                    BootloaderEntries = $metadata.BootloaderEntries
                }
            } catch {
                Write-Host "Erro ao ler metadados do backup $($dir.Name): $_" -ForegroundColor Red
            }
        }
    }
    
    return $backups
}

# Exportar funções
Export-ModuleMember -Function New-EfiBackup, Restore-EfiBackup, Get-EfiBackups
