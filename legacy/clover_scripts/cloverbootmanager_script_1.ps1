# Script de instalação gradual do Clover Boot Manager
# Este script instala o Clover Boot Manager de forma gradual, verificando o sucesso de cada etapa

param (
    [Parameter(Mandatory=$false)]
    [switch]$Force,

    [Parameter(Mandatory=$false)]
    [string]$TargetDrive = "C:",

    [Parameter(Mandatory=$false)]
    [string]$TempDir = "$env:TEMP\CloverBootManager"
)

# Importar scripts auxiliares
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$efiBackupUtilsPath = Join-Path -Path $scriptPath -ChildPath "efi_backup_utils.ps1"
$hardwareCompatibilityPath = Join-Path -Path $scriptPath -ChildPath "hardware_compatibility.ps1"
$osDetectionPath = Join-Path -Path $scriptPath -ChildPath "os_detection.ps1"
$cloverVerificationPath = Join-Path -Path $scriptPath -ChildPath "clover_verification.ps1"
$criticalLoggerPath = Join-Path -Path $scriptPath -ChildPath "critical_operations_logger.ps1"

# Inicializar logger
if (Test-Path $criticalLoggerPath) {
    . $criticalLoggerPath
    $logFile = Initialize-CriticalLogger
    Write-CriticalOperation -OperationName "CloverInstallation" -Details "Iniciando instalação do Clover Boot Manager" -Status "STARTED" -LogFile $logFile
} else {
    Write-Host "AVISO: Script de log não encontrado. Continuando sem log detalhado." -ForegroundColor Yellow
    $logFile = $null
}

# Função para registrar operações críticas
function Log-Operation {
    param (
        [string]$Operation,
        [string]$Details,
        [string]$Status = "STARTED"
    )

    if ($logFile) {
        try {
            Write-CriticalOperation -OperationName $Operation -Details $Details -Status $Status -LogFile $logFile
        } catch {
            $color = switch ($Status) {
                "STARTED" { "Yellow" }
                "COMPLETED" { "Green" }
                "FAILED" { "Red" }
                "WARNING" { "Magenta" }
                default { "White" }
            }

            Write-Host "[$Status] [$Operation]: $Details" -ForegroundColor $color
        }
    } else {
        $color = switch ($Status) {
            "STARTED" { "Yellow" }
            "COMPLETED" { "Green" }
            "FAILED" { "Red" }
            "WARNING" { "Magenta" }
            default { "White" }
        }

        Write-Host "[$Status] [$Operation]: $Details" -ForegroundColor $color
    }
}

# Função para verificar se uma etapa foi concluída com sucesso
function Test-StepSuccess {
    param (
        [string]$StepName,
        [scriptblock]$TestScript,
        [string]$FailureMessage
    )

    Log-Operation -Operation "CloverInstallation" -Details "Verificando etapa: $StepName" -Status "STARTED"

    try {
        $result = & $TestScript

        if ($result) {
            Log-Operation -Operation "CloverInstallation" -Details "Etapa concluída com sucesso: $StepName" -Status "COMPLETED"
            return $true
        } else {
            Log-Operation -Operation "CloverInstallation" -Details "Falha na etapa: $StepName - $FailureMessage" -Status "FAILED"
            return $false
        }
    } catch {
        Log-Operation -Operation "CloverInstallation" -Details "Erro ao verificar etapa: $StepName - $_" -Status "FAILED"
        return $false
    }
}

# Etapa 1: Verificar compatibilidade de hardware
Log-Operation -Operation "CloverInstallation" -Details "Etapa 1: Verificando compatibilidade de hardware" -Status "STARTED"

if (Test-Path $hardwareCompatibilityPath) {
    . $hardwareCompatibilityPath
    $compatibilityResult = Test-HardwareCompatibility

    if (-not $compatibilityResult.Compatible -and -not $Force) {
        Log-Operation -Operation "CloverInstallation" -Details "Hardware incompatível com o Clover Boot Manager: $($compatibilityResult.Issues -join ', ')" -Status "FAILED"
        Write-Host "Para forçar a instalação mesmo com incompatibilidades, use o parâmetro -Force" -ForegroundColor Yellow
        exit 1
    } elseif (-not $compatibilityResult.Compatible -and $Force) {
        Log-Operation -Operation "CloverInstallation" -Details "Hardware incompatível, mas instalação forçada: $($compatibilityResult.Issues -join ', ')" -Status "WARNING"
    } else {
        Log-Operation -Operation "CloverInstallation" -Details "Hardware compatível com o Clover Boot Manager" -Status "COMPLETED"
    }

    # Armazenar a letra da unidade EFI para uso posterior
    $efiDriveLetter = $compatibilityResult.EfiDriveLetter
} else {
    Log-Operation -Operation "CloverInstallation" -Details "Não foi possível verificar compatibilidade de hardware: script não encontrado" -Status "WARNING"
    $efiDriveLetter = $null
}

# Etapa 2: Criar backup da partição EFI
Log-Operation -Operation "CloverInstallation" -Details "Etapa 2: Criando backup da partição EFI" -Status "STARTED"

if (Test-Path $efiBackupUtilsPath) {
    . $efiBackupUtilsPath
    $backupName = "Pre_Clover_Install_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    $backupResult = New-EfiBackup -BackupName $backupName -EfiDriveLetter $efiDriveLetter

    if ($backupResult) {
        Log-Operation -Operation "CloverInstallation" -Details "Backup da partição EFI criado com sucesso: $($backupResult.Path)" -Status "COMPLETED"
        $backupPath = $backupResult.Path
    } else {
        Log-Operation -Operation "CloverInstallation" -Details "Falha ao criar backup da partição EFI" -Status "WARNING"

        if (-not $Force) {
            Write-Host "Para continuar sem backup, use o parâmetro -Force" -ForegroundColor Yellow
            exit 1
        }

        $backupPath = $null
    }
} else {
    Log-Operation -Operation "CloverInstallation" -Details "Não foi possível criar backup da partição EFI: script não encontrado" -Status "WARNING"
    $backupPath = $null
}

# Etapa 3: Detectar sistemas operacionais
Log-Operation -Operation "CloverInstallation" -Details "Etapa 3: Detectando sistemas operacionais" -Status "STARTED"

if (Test-Path $osDetectionPath) {
    . $osDetectionPath
    $operatingSystems = Get-InstalledOperatingSystems

    if ($operatingSystems.Count -gt 0) {
        Log-Operation -Operation "CloverInstallation" -Details "Sistemas operacionais detectados: $($operatingSystems.Count)" -Status "COMPLETED"

        foreach ($os in $operatingSystems) {
            Log-Operation -Operation "CloverInstallation" -Details "Sistema operacional detectado: $($os.Name) ($($os.Type))" -Status "COMPLETED"
        }
    } else {
        Log-Operation -Operation "CloverInstallation" -Details "Nenhum sistema operacional detectado" -Status "WARNING"
    }
} else {
    Log-Operation -Operation "CloverInstallation" -Details "Não foi possível detectar sistemas operacionais: script não encontrado" -Status "WARNING"
    $operatingSystems = @()
}

# Etapa 4: Baixar e extrair o Clover
Log-Operation -Operation "CloverInstallation" -Details "Etapa 4: Baixando e extraindo o Clover Boot Manager" -Status "STARTED"

# Criar diretório temporário
if (-not (Test-Path $TempDir)) {
    New-Item -Path $TempDir -ItemType Directory -Force | Out-Null
}

# URL do Clover (versão estável)
$cloverUrl = "https://github.com/CloverHackyColor/CloverBootloader/releases/download/5151/CloverV2-5151.zip"
$cloverZip = Join-Path -Path $TempDir -ChildPath "CloverV2.zip"

# Baixar o Clover
try {
    Log-Operation -Operation "CloverInstallation" -Details "Baixando Clover de $cloverUrl" -Status "STARTED"

    # Usar TLS 1.2
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

    # Baixar o arquivo
    Invoke-WebRequest -Uri $cloverUrl -OutFile $cloverZip

    # Verificar se o download foi bem-sucedido
    $downloadSuccess = Test-StepSuccess -StepName "Download do Clover" -TestScript {
        Test-Path $cloverZip -and (Get-Item $cloverZip).Length -gt 0
    } -FailureMessage "Arquivo de download não encontrado ou vazio"

    if (-not $downloadSuccess) {
        Log-Operation -Operation "CloverInstallation" -Details "Falha ao baixar o Clover" -Status "FAILED"
        exit 1
    }
} catch {
    Log-Operation -Operation "CloverInstallation" -Details "Erro ao baixar o Clover: $_" -Status "FAILED"
    exit 1
}

# Extrair o Clover
try {
    Log-Operation -Operation "CloverInstallation" -Details "Extraindo Clover" -Status "STARTED"

    # Criar diretório de extração
    $extractDir = Join-Path -Path $TempDir -ChildPath "Extract"
    if (Test-Path $extractDir) {
        Remove-Item -Path $extractDir -Recurse -Force
    }
    New-Item -Path $extractDir -ItemType Directory -Force | Out-Null

    # Extrair o arquivo
    Expand-Archive -Path $cloverZip -DestinationPath $extractDir -Force

    # Verificar se a extração foi bem-sucedida
    $extractSuccess = Test-StepSuccess -StepName "Extração do Clover" -TestScript {
        Test-Path "$extractDir\EFI"
    } -FailureMessage "Diretório EFI não encontrado após extração"

    if (-not $extractSuccess) {
        Log-Operation -Operation "CloverInstallation" -Details "Falha ao extrair o Clover" -Status "FAILED"
        exit 1
    }
} catch {
    Log-Operation -Operation "CloverInstallation" -Details "Erro ao extrair o Clover: $_" -Status "FAILED"
    exit 1
}

# Etapa 5: Encontrar e montar a partição EFI
Log-Operation -Operation "CloverInstallation" -Details "Etapa 5: Encontrando e montando a partição EFI" -Status "STARTED"

$efiVolume = $null
$tempDriveCreated = $false

if ($efiDriveLetter) {
    # Usar a letra de unidade EFI já encontrada
    $efiVolume = Get-Volume -DriveLetter $efiDriveLetter -ErrorAction SilentlyContinue

    if ($efiVolume) {
        Log-Operation -Operation "CloverInstallation" -Details "Partição EFI já montada em $efiDriveLetter:" -Status "COMPLETED"
    } else {
        Log-Operation -Operation "CloverInstallation" -Details "Letra de unidade EFI fornecida, mas volume não encontrado" -Status "WARNING"
        $efiDriveLetter = $null
    }
}

if (-not $efiDriveLetter) {
    # Tentar encontrar a partição EFI
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
                            $efiPartitions[0] | Add-PartitionAccessPath -AccessPath "${letter}:"
                            $efiVolume = Get-Volume -DriveLetter $letter
                            $efiDriveLetter = $letter
                            $tempDriveCreated = $true
                            Log-Operation -Operation "CloverInstallation" -Details "Atribuída letra temporária $letter à partição EFI" -Status "COMPLETED"
                            break
                        }
                        $driveLetter++
                    }
                } elseif ($efiVolume) {
                    $efiDriveLetter = $efiVolume.DriveLetter
                    Log-Operation -Operation "CloverInstallation" -Details "Partição EFI encontrada em $efiDriveLetter:" -Status "COMPLETED"
                }

                if ($efiVolume -and $efiVolume.DriveLetter) {
                    break
                }
            } catch {
                Log-Operation -Operation "CloverInstallation" -Details "Erro ao acessar partição EFI: $_" -Status "WARNING"
            }
        }
    }
}

# Verificar se encontramos a partição EFI
if (-not $efiVolume -or -not $efiDriveLetter) {
    Log-Operation -Operation "CloverInstallation" -Details "Não foi possível encontrar ou montar a partição EFI" -Status "FAILED"
    exit 1
}

$efiPath = "${efiDriveLetter}:"

# Etapa 6: Gerar configuração do Clover
Log-Operation -Operation "CloverInstallation" -Details "Etapa 6: Gerando configuração do Clover" -Status "STARTED"

if (Test-Path $osDetectionPath -and $operatingSystems.Count -gt 0) {
    . $osDetectionPath
    $configPath = Get-CloverConfig -OperatingSystems $operatingSystems

    if (Test-Path $configPath) {
        Log-Operation -Operation "CloverInstallation" -Details "Configuração do Clover gerada com sucesso: $configPath" -Status "COMPLETED"
    } else {
        Log-Operation -Operation "CloverInstallation" -Details "Falha ao gerar configuração do Clover" -Status "WARNING"
        $configPath = $null
    }
} else {
    Log-Operation -Operation "CloverInstallation" -Details "Não foi possível gerar configuração do Clover: script não encontrado ou nenhum sistema operacional detectado" -Status "WARNING"
    $configPath = $null
}

# Etapa 7: Instalar o Clover na partição EFI
Log-Operation -Operation "CloverInstallation" -Details "Etapa 7: Instalando o Clover na partição EFI" -Status "STARTED"

try {
    # Verificar se o diretório EFI existe na partição
    if (-not (Test-Path "$efiPath\EFI")) {
        New-Item -Path "$efiPath\EFI" -ItemType Directory -Force | Out-Null
    }

    # Preservar o bootloader original
    if (Test-Path "$efiPath\EFI\BOOT\BOOTX64.efi") {
        Log-Operation -Operation "CloverInstallation" -Details "Preservando bootloader original" -Status "STARTED"
        Copy-Item -Path "$efiPath\EFI\BOOT\BOOTX64.efi" -Destination "$efiPath\EFI\BOOT\BOOTX64.efi.original" -Force
        Log-Operation -Operation "CloverInstallation" -Details "Bootloader original preservado como BOOTX64.efi.original" -Status "COMPLETED"
    }

    # Copiar arquivos do Clover para a partição EFI
    Log-Operation -Operation "CloverInstallation" -Details "Copiando arquivos do Clover para a partição EFI" -Status "STARTED"

    # Verificar se o diretório CLOVER já existe e fazer backup se necessário
    if (Test-Path "$efiPath\EFI\CLOVER") {
        $cloverBackupDir = "$efiPath\EFI\CLOVER.bak"
        if (Test-Path $cloverBackupDir) {
            Remove-Item -Path $cloverBackupDir -Recurse -Force
        }
        Rename-Item -Path "$efiPath\EFI\CLOVER" -NewName "CLOVER.bak"
        Log-Operation -Operation "CloverInstallation" -Details "Backup da instalação anterior do Clover criado como CLOVER.bak" -Status "COMPLETED"
    }

    # Copiar diretório CLOVER
    Copy-Item -Path "$extractDir\EFI\CLOVER" -Destination "$efiPath\EFI\" -Recurse -Force

    # Verificar se a cópia foi bem-sucedida
    $copySuccess = Test-StepSuccess -StepName "Cópia dos arquivos do Clover" -TestScript {
        Test-Path "$efiPath\EFI\CLOVER\CLOVERX64.efi"
    } -FailureMessage "Arquivo CLOVERX64.efi não encontrado após cópia"

    if (-not $copySuccess) {
        Log-Operation -Operation "CloverInstallation" -Details "Falha ao copiar arquivos do Clover" -Status "FAILED"

        # Tentar restaurar backup anterior se existir
        if (Test-Path "$efiPath\EFI\CLOVER.bak") {
            Log-Operation -Operation "CloverInstallation" -Details "Restaurando backup anterior do Clover" -Status "STARTED"
            Remove-Item -Path "$efiPath\EFI\CLOVER" -Recurse -Force -ErrorAction SilentlyContinue
            Rename-Item -Path "$efiPath\EFI\CLOVER.bak" -NewName "CLOVER"
            Log-Operation -Operation "CloverInstallation" -Details "Backup anterior do Clover restaurado" -Status "COMPLETED"
        }

        exit 1
    }

    # Copiar configuração personalizada, se disponível
    if ($configPath -and (Test-Path $configPath)) {
        Log-Operation -Operation "CloverInstallation" -Details "Copiando configuração personalizada" -Status "STARTED"
        Copy-Item -Path $configPath -Destination "$efiPath\EFI\CLOVER\config.plist" -Force
        Log-Operation -Operation "CloverInstallation" -Details "Configuração personalizada copiada com sucesso" -Status "COMPLETED"
    }

    # Configurar o Clover como bootloader principal (opcional)
    $useCloverAsMain = $false # Por padrão, não substituir o bootloader original

    # Perguntar ao usuário se deseja usar o Clover como bootloader principal
    $useCloverAsMainPrompt = Read-Host "Deseja configurar o Clover como bootloader principal? (S/N) [N]"
    if ($useCloverAsMainPrompt -eq "S" -or $useCloverAsMainPrompt -eq "s") {
        $useCloverAsMain = $true
        Log-Operation -Operation "CloverInstallation" -Details "Usuário optou por configurar o Clover como bootloader principal" -Status "WARNING"
    } else {
        Log-Operation -Operation "CloverInstallation" -Details "Usuário optou por preservar o bootloader original" -Status "COMPLETED"
    }

    if ($useCloverAsMain) {
        Log-Operation -Operation "CloverInstallation" -Details "Configurando Clover como bootloader principal" -Status "STARTED"

        # Verificar se o diretório BOOT existe
        if (-not (Test-Path "$efiPath\EFI\BOOT")) {
            New-Item -Path "$efiPath\EFI\BOOT" -ItemType Directory -Force | Out-Null
        }

        # Copiar o Clover como bootloader principal
        Copy-Item -Path "$efiPath\EFI\CLOVER\CLOVERX64.efi" -Destination "$efiPath\EFI\BOOT\BOOTX64.efi" -Force

        # Verificar se a cópia foi bem-sucedida
        $bootloaderSuccess = Test-StepSuccess -StepName "Configuração do bootloader principal" -TestScript {
            Test-Path "$efiPath\EFI\BOOT\BOOTX64.efi"
        } -FailureMessage "Arquivo BOOTX64.efi não encontrado após cópia"

        if ($bootloaderSuccess) {
            Log-Operation -Operation "CloverInstallation" -Details "Clover configurado como bootloader principal" -Status "COMPLETED"
        } else {
            Log-Operation -Operation "CloverInstallation" -Details "Falha ao configurar Clover como bootloader principal" -Status "WARNING"
        }
    }

    Log-Operation -Operation "CloverInstallation" -Details "Instalação do Clover na partição EFI concluída com sucesso" -Status "COMPLETED"
} catch {
    Log-Operation -Operation "CloverInstallation" -Details "Erro ao instalar o Clover na partição EFI: $_" -Status "FAILED"
    exit 1
}

# Etapa 8: Verificar a instalação
Log-Operation -Operation "CloverInstallation" -Details "Etapa 8: Verificando a instalação do Clover" -Status "STARTED"

if (Test-Path $cloverVerificationPath) {
    . $cloverVerificationPath
    $verificationResult = Test-CloverInstallation -EfiDriveLetter $efiDriveLetter

    if ($verificationResult.Success) {
        Log-Operation -Operation "CloverInstallation" -Details "Verificação da instalação do Clover concluída com sucesso" -Status "COMPLETED"
    } else {
        Log-Operation -Operation "CloverInstallation" -Details "Falha na verificação da instalação do Clover: $($verificationResult.Details -join ', ')" -Status "WARNING"
    }
} else {
    Log-Operation -Operation "CloverInstallation" -Details "Não foi possível verificar instalação do Clover: script não encontrado" -Status "WARNING"
}

# Etapa 9: Limpar recursos temporários
Log-Operation -Operation "CloverInstallation" -Details "Etapa 9: Limpando recursos temporários" -Status "STARTED"

# Limpar letra de unidade temporária se foi criada
if ($tempDriveCreated) {
    try {
        $efiPartition = Get-Partition | Where-Object {$_.GptType -eq "{c12a7328-f81f-11d2-ba4b-00a0c93ec93b}"}
        $efiPartition | Remove-PartitionAccessPath -AccessPath "$efiPath"
        Log-Operation -Operation "CloverInstallation" -Details "Removida letra de unidade temporária $efiDriveLetter" -Status "COMPLETED"
    } catch {
        Log-Operation -Operation "CloverInstallation" -Details "Erro ao remover letra de unidade temporária: $_" -Status "WARNING"
    }
}

# Limpar arquivos temporários
if (Test-Path $TempDir) {
    try {
        Remove-Item -Path $TempDir -Recurse -Force -ErrorAction SilentlyContinue
        Log-Operation -Operation "CloverInstallation" -Details "Arquivos temporários removidos" -Status "COMPLETED"
    } catch {
        Log-Operation -Operation "CloverInstallation" -Details "Erro ao remover arquivos temporários: $_" -Status "WARNING"
    }
}

# Etapa 10: Finalizar instalação
Log-Operation -Operation "CloverInstallation" -Details "Instalação do Clover Boot Manager concluída com sucesso" -Status "COMPLETED"

# Exibir informações de recuperação
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "      INSTALAÇÃO DO CLOVER BOOT MANAGER CONCLUÍDA   " -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host
Write-Host "O Clover Boot Manager foi instalado com sucesso!" -ForegroundColor Green
Write-Host

if ($backupPath) {
    Write-Host "Um backup da partição EFI foi criado em:" -ForegroundColor Yellow
    Write-Host "  $backupPath" -ForegroundColor Yellow
    Write-Host
    Write-Host "Para restaurar este backup em caso de problemas, execute:" -ForegroundColor Yellow
    Write-Host "  powershell -ExecutionPolicy Bypass -File `"$scriptPath\clover_recovery.ps1`" -BackupPath `"$backupPath`"" -ForegroundColor Yellow
}

Write-Host
Write-Host "Para acessar o modo de recuperação em caso de problemas, execute:" -ForegroundColor Yellow
Write-Host "  powershell -ExecutionPolicy Bypass -File `"$scriptPath\clover_recovery.ps1`"" -ForegroundColor Yellow
Write-Host

# Retornar código de sucesso
exit 0
