# Script simplificado de instalação do Clover Boot Manager
# Este script instala o Clover Boot Manager de forma robusta

param (
    [Parameter(Mandatory=$false)]
    [switch]$Force
)

# Configurações
$cloverUrl = "https://github.com/CloverHackyColor/CloverBootloader/releases/download/5161/CloverV2-5161.zip"
$tempDir = "$env:TEMP\CloverBootManager"
$logDir = "$env:USERPROFILE\Documents\Environment_Dev\Logs"
$logFile = "$logDir\clover_installation.log"

# Função para registrar logs
function Write-Log {
    param (
        [string]$Message,
        [string]$Level = "INFO"
    )

    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"

    # Criar diretório de logs se não existir
    if (-not (Test-Path $logDir)) {
        New-Item -Path $logDir -ItemType Directory -Force | Out-Null
    }

    # Escrever no arquivo de log
    $logEntry | Out-File -FilePath $logFile -Append -Encoding utf8

    # Exibir na tela com cores apropriadas
    $color = switch ($Level) {
        "INFO" { "White" }
        "SUCCESS" { "Green" }
        "WARNING" { "Yellow" }
        "ERROR" { "Red" }
        default { "White" }
    }

    Write-Host $logEntry -ForegroundColor $color
}

# Função para criar backup da partição EFI
function Backup-EfiPartition {
    Write-Log "Criando backup da partição EFI..." "INFO"

    # Encontrar a partição EFI
    $efiPartition = $null
    $tempDriveCreated = $false
    $efiDriveLetter = $null

    # Verificar se já existe uma partição EFI montada
    $existingEfiVolumes = Get-Volume | Where-Object { Test-Path "$($_.DriveLetter):\EFI" -ErrorAction SilentlyContinue }

    if ($existingEfiVolumes) {
        $efiDriveLetter = $existingEfiVolumes[0].DriveLetter
        Write-Log "Partição EFI já montada em ${efiDriveLetter}:" "INFO"
        return @{
            Path = "$env:USERPROFILE\Documents\Environment_Dev\EFI_Backups\EFI_Backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
            EfiDriveLetter = $efiDriveLetter
            TempDriveCreated = $false
        }
    }

    # Se não encontrou, tentar montar a partição EFI
    $disks = Get-Disk | Where-Object {$_.PartitionStyle -eq "GPT"}
    foreach ($disk in $disks) {
        $efiPartitions = $disk | Get-Partition | Where-Object {$_.GptType -eq "{c12a7328-f81f-11d2-ba4b-00a0c93ec93b}"}

        if ($efiPartitions) {
            try {
                # Obter volume da partição EFI
                $efiVolume = $efiPartitions[0] | Get-Volume -ErrorAction SilentlyContinue

                # Se não tiver letra de unidade, atribuir uma temporária
                if ($efiVolume -and -not $efiVolume.DriveLetter) {
                    $driveLetter = 69 # Letra 'E'
                    while ([char]$driveLetter -le 90) {
                        $letter = [char]$driveLetter
                        if (-not (Get-Volume -DriveLetter $letter -ErrorAction SilentlyContinue)) {
                            try {
                                $efiPartitions[0] | Add-PartitionAccessPath -AccessPath "${letter}:"
                                $efiVolume = Get-Volume -DriveLetter $letter
                                $efiDriveLetter = $letter
                                $tempDriveCreated = $true
                                Write-Log "Atribuída letra temporária $letter à partição EFI" "INFO"
                                break
                            } catch {
                                Write-Log "Erro ao atribuir letra $letter à partição EFI: $_" "WARNING"
                                $driveLetter++
                                continue
                            }
                        }
                        $driveLetter++
                    }
                } elseif ($efiVolume) {
                    $efiDriveLetter = $efiVolume.DriveLetter
                }

                if ($efiVolume -and $efiVolume.DriveLetter) {
                    break
                }
            } catch {
                Write-Log "Erro ao acessar partição EFI: $_" "ERROR"
            }
        }
    }

    # Verificar se encontramos a partição EFI
    if (-not $efiDriveLetter) {
        # Tentar usar uma letra fixa para a partição EFI
        Write-Log "Tentando usar letra fixa para a partição EFI..." "WARNING"

        # Usar letra S: para a partição EFI
        $fixedLetter = "S"

        # Verificar se a letra já está em uso
        if (Get-Volume -DriveLetter $fixedLetter -ErrorAction SilentlyContinue) {
            Write-Log "Letra $fixedLetter já está em uso" "WARNING"
        } else {
            try {
                # Tentar montar a partição EFI com a letra fixa
                $efiPartitions[0] | Add-PartitionAccessPath -AccessPath "${fixedLetter}:"
                $efiDriveLetter = $fixedLetter
                $tempDriveCreated = $true
                Write-Log "Atribuída letra fixa $fixedLetter à partição EFI" "INFO"
            } catch {
                Write-Log "Erro ao atribuir letra fixa $fixedLetter à partição EFI: $_" "ERROR"
            }
        }
    }

    # Se ainda não encontramos a partição EFI, usar uma letra padrão
    if (-not $efiDriveLetter -and $Force) {
        Write-Log "Forçando uso da letra S: para a partição EFI" "WARNING"
        $efiDriveLetter = "S"
    } elseif (-not $efiDriveLetter) {
        Write-Log "Não foi possível encontrar ou montar a partição EFI" "ERROR"
        return $null
    }

    $efiPath = "${efiDriveLetter}:"
    Write-Log "Partição EFI encontrada em $efiPath" "SUCCESS"

    # Criar diretório de backup
    $backupDate = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupDir = "$env:USERPROFILE\Documents\Environment_Dev\EFI_Backups\EFI_Backup_$backupDate"

    if (-not (Test-Path "$env:USERPROFILE\Documents\Environment_Dev\EFI_Backups")) {
        New-Item -Path "$env:USERPROFILE\Documents\Environment_Dev\EFI_Backups" -ItemType Directory -Force | Out-Null
    }

    New-Item -Path $backupDir -ItemType Directory -Force | Out-Null

    # Fazer backup da partição EFI
    try {
        Write-Log "Copiando conteúdo da partição EFI para $backupDir..." "INFO"
        Copy-Item -Path "$efiPath\*" -Destination $backupDir -Recurse -Force
        Write-Log "Backup da partição EFI concluído com sucesso" "SUCCESS"

        # Criar arquivo de informações do backup
        $backupInfo = @{
            Date = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
            EfiDriveLetter = $efiDriveLetter
            BackupPath = $backupDir
            TempDriveCreated = $tempDriveCreated
        }

        $backupInfo | ConvertTo-Json | Out-File -FilePath "$backupDir\backup_info.json" -Encoding utf8

        # Retornar informações do backup
        return @{
            Path = $backupDir
            EfiDriveLetter = $efiDriveLetter
            TempDriveCreated = $tempDriveCreated
        }
    } catch {
        Write-Log "Erro ao criar backup da partição EFI: $_" "ERROR"

        # Limpar letra de unidade temporária se foi criada
        if ($tempDriveCreated) {
            try {
                $efiPartitions[0] | Remove-PartitionAccessPath -AccessPath "$efiPath"
                Write-Log "Removida letra de unidade temporária $efiDriveLetter" "INFO"
            } catch {
                Write-Log "Erro ao remover letra de unidade temporária: $_" "WARNING"
            }
        }

        return $null
    }
}

# Função para baixar e extrair o Clover
function Download-Clover {
    param (
        [string]$Url,
        [string]$DestinationPath
    )

    Write-Log "Usando arquivo local do Clover..." "INFO"

    # Criar diretório temporário
    if (-not (Test-Path $DestinationPath)) {
        New-Item -Path $DestinationPath -ItemType Directory -Force | Out-Null
    }

    $zipFile = Join-Path -Path $DestinationPath -ChildPath "CloverV2.zip"

    try {
        # Usar arquivo local
        $localFile = "$PSScriptRoot\CloverV2-5161.zip"

        if (Test-Path $localFile) {
            # Copiar arquivo local
            Copy-Item -Path $localFile -Destination $zipFile -Force

            # Verificar se a cópia foi bem-sucedida
            if (Test-Path $zipFile -and (Get-Item $zipFile).Length -gt 0) {
                Write-Log "Arquivo do Clover copiado com sucesso" "SUCCESS"
                return $zipFile
            } else {
                Write-Log "Falha ao copiar o arquivo do Clover: arquivo vazio ou não encontrado" "ERROR"
                return $null
            }
        } else {
            Write-Log "Arquivo local do Clover não encontrado: $localFile" "ERROR"
            return $null
        }
    } catch {
        Write-Log "Erro ao copiar o arquivo do Clover: $_" "ERROR"
        return $null
    }
}

# Função para instalar o Clover
function Install-Clover {
    param (
        [string]$ZipFile,
        [string]$EfiDriveLetter
    )

    Write-Log "Instalando Clover na partição EFI..." "INFO"

    $efiPath = "${EfiDriveLetter}:"

    try {
        # Extrair o arquivo ZIP
        $extractDir = Join-Path -Path $tempDir -ChildPath "Extract"
        if (Test-Path $extractDir) {
            Remove-Item -Path $extractDir -Recurse -Force
        }
        New-Item -Path $extractDir -ItemType Directory -Force | Out-Null

        Write-Log "Extraindo arquivo ZIP..." "INFO"
        Expand-Archive -Path $ZipFile -DestinationPath $extractDir -Force

        # Verificar se a extração foi bem-sucedida
        if (-not (Test-Path "$extractDir\EFI")) {
            Write-Log "Falha ao extrair o Clover: diretório EFI não encontrado" "ERROR"
            return $false
        }

        # Verificar se o diretório EFI existe na partição
        if (-not (Test-Path "$efiPath\EFI")) {
            New-Item -Path "$efiPath\EFI" -ItemType Directory -Force | Out-Null
        }

        # Preservar o bootloader original
        if (Test-Path "$efiPath\EFI\BOOT\BOOTX64.efi") {
            Write-Log "Preservando bootloader original..." "INFO"
            Copy-Item -Path "$efiPath\EFI\BOOT\BOOTX64.efi" -Destination "$efiPath\EFI\BOOT\BOOTX64.efi.original" -Force
            Write-Log "Bootloader original preservado como BOOTX64.efi.original" "SUCCESS"
        }

        # Verificar se o diretório CLOVER já existe e fazer backup se necessário
        if (Test-Path "$efiPath\EFI\CLOVER") {
            $cloverBackupDir = "$efiPath\EFI\CLOVER.bak"
            if (Test-Path $cloverBackupDir) {
                Remove-Item -Path $cloverBackupDir -Recurse -Force
            }
            Rename-Item -Path "$efiPath\EFI\CLOVER" -NewName "CLOVER.bak"
            Write-Log "Backup da instalação anterior do Clover criado como CLOVER.bak" "INFO"
        }

        # Copiar diretório CLOVER
        Write-Log "Copiando arquivos do Clover para a partição EFI..." "INFO"
        Copy-Item -Path "$extractDir\EFI\CLOVER" -Destination "$efiPath\EFI\" -Recurse -Force

        # Verificar se a cópia foi bem-sucedida
        if (Test-Path "$efiPath\EFI\CLOVER\CLOVERX64.efi") {
            Write-Log "Arquivos do Clover copiados com sucesso" "SUCCESS"

            # Perguntar se deseja usar o Clover como bootloader principal
            $useCloverAsMain = $false
            $useCloverAsMainPrompt = Read-Host "Deseja configurar o Clover como bootloader principal? (S/N) [N]"
            if ($useCloverAsMainPrompt -eq "S" -or $useCloverAsMainPrompt -eq "s") {
                $useCloverAsMain = $true
                Write-Log "Usuário optou por configurar o Clover como bootloader principal" "WARNING"
            } else {
                Write-Log "Usuário optou por preservar o bootloader original" "INFO"
            }

            if ($useCloverAsMain) {
                # Verificar se o diretório BOOT existe
                if (-not (Test-Path "$efiPath\EFI\BOOT")) {
                    New-Item -Path "$efiPath\EFI\BOOT" -ItemType Directory -Force | Out-Null
                }

                # Copiar o Clover como bootloader principal
                Copy-Item -Path "$efiPath\EFI\CLOVER\CLOVERX64.efi" -Destination "$efiPath\EFI\BOOT\BOOTX64.efi" -Force

                # Verificar se a cópia foi bem-sucedida
                if (Test-Path "$efiPath\EFI\BOOT\BOOTX64.efi") {
                    Write-Log "Clover configurado como bootloader principal" "SUCCESS"
                } else {
                    Write-Log "Falha ao configurar Clover como bootloader principal" "ERROR"
                }
            }

            return $true
        } else {
            Write-Log "Falha ao copiar arquivos do Clover: CLOVERX64.efi não encontrado" "ERROR"

            # Tentar restaurar backup anterior se existir
            if (Test-Path "$efiPath\EFI\CLOVER.bak") {
                Write-Log "Restaurando backup anterior do Clover..." "INFO"
                Remove-Item -Path "$efiPath\EFI\CLOVER" -Recurse -Force -ErrorAction SilentlyContinue
                Rename-Item -Path "$efiPath\EFI\CLOVER.bak" -NewName "CLOVER"
                Write-Log "Backup anterior do Clover restaurado" "SUCCESS"
            }

            return $false
        }
    } catch {
        Write-Log "Erro ao instalar o Clover: $_" "ERROR"
        return $false
    }
}

# Função para verificar a instalação do Clover
function Test-CloverInstallation {
    param (
        [string]$EfiDriveLetter
    )

    Write-Log "Verificando instalação do Clover..." "INFO"

    $efiPath = "${EfiDriveLetter}:"

    # Verificar arquivos essenciais
    $essentialFiles = @(
        "$efiPath\EFI\CLOVER\CLOVERX64.efi",
        "$efiPath\EFI\CLOVER\config.plist"
    )

    $allFilesExist = $true
    foreach ($file in $essentialFiles) {
        if (-not (Test-Path $file)) {
            Write-Log "Arquivo essencial não encontrado: $file" "ERROR"
            $allFilesExist = $false
        } else {
            Write-Log "Arquivo essencial encontrado: $file" "SUCCESS"
        }
    }

    # Verificar backup do bootloader original
    if (Test-Path "$efiPath\EFI\BOOT\BOOTX64.efi.original") {
        Write-Log "Backup do bootloader original encontrado" "SUCCESS"
    } else {
        Write-Log "Backup do bootloader original não encontrado" "WARNING"
    }

    return $allFilesExist
}

# Função principal
function Main {
    Write-Log "Iniciando instalação do Clover Boot Manager..." "INFO"

    # Criar backup da partição EFI
    $backupResult = Backup-EfiPartition
    if (-not $backupResult -and -not $Force) {
        Write-Log "Falha ao criar backup da partição EFI. Use -Force para continuar sem backup." "ERROR"
        return 1
    }

    $efiDriveLetter = $backupResult.EfiDriveLetter
    $tempDriveCreated = $backupResult.TempDriveCreated

    # Baixar o Clover
    $zipFile = Download-Clover -Url $cloverUrl -DestinationPath $tempDir
    if (-not $zipFile) {
        Write-Log "Falha ao baixar o Clover" "ERROR"
        return 1
    }

    # Instalar o Clover
    $installResult = Install-Clover -ZipFile $zipFile -EfiDriveLetter $efiDriveLetter
    if (-not $installResult) {
        Write-Log "Falha ao instalar o Clover" "ERROR"
        return 1
    }

    # Verificar a instalação
    $verifyResult = Test-CloverInstallation -EfiDriveLetter $efiDriveLetter
    if (-not $verifyResult) {
        Write-Log "Verificação da instalação do Clover falhou" "WARNING"
    } else {
        Write-Log "Verificação da instalação do Clover concluída com sucesso" "SUCCESS"
    }

    # Limpar letra de unidade temporária se foi criada
    if ($tempDriveCreated) {
        try {
            $efiPartition = Get-Partition | Where-Object {$_.GptType -eq "{c12a7328-f81f-11d2-ba4b-00a0c93ec93b}"}
            $efiPartition | Remove-PartitionAccessPath -AccessPath "${efiDriveLetter}:"
            Write-Log "Removida letra de unidade temporária $efiDriveLetter" "INFO"
        } catch {
            Write-Log "Erro ao remover letra de unidade temporária: $_" "WARNING"
        }
    }

    # Limpar arquivos temporários
    if (Test-Path $tempDir) {
        try {
            Remove-Item -Path $tempDir -Recurse -Force -ErrorAction SilentlyContinue
            Write-Log "Arquivos temporários removidos" "INFO"
        } catch {
            Write-Log "Erro ao remover arquivos temporários: $_" "WARNING"
        }
    }

    Write-Log "Instalação do Clover Boot Manager concluída com sucesso" "SUCCESS"

    # Exibir informações de recuperação
    Write-Host "====================================================" -ForegroundColor Cyan
    Write-Host "      INSTALAÇÃO DO CLOVER BOOT MANAGER CONCLUÍDA   " -ForegroundColor Cyan
    Write-Host "====================================================" -ForegroundColor Cyan
    Write-Host
    Write-Host "O Clover Boot Manager foi instalado com sucesso!" -ForegroundColor Green
    Write-Host

    if ($backupResult) {
        Write-Host "Um backup da partição EFI foi criado em:" -ForegroundColor Yellow
        Write-Host "  $($backupResult.Path)" -ForegroundColor Yellow
        Write-Host
    }

    Write-Host "Para acessar o Clover na próxima inicialização, reinicie o computador." -ForegroundColor Yellow
    Write-Host

    return 0
}

# Executar função principal
$exitCode = Main
exit $exitCode
