# Script simplificado de instalação do Clover Boot Manager

# Verificar se estamos executando como administrador
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "Este script precisa ser executado como administrador." -ForegroundColor Red
    Write-Host "Por favor, execute o PowerShell como administrador e tente novamente." -ForegroundColor Red
    exit 1
}

Write-Host "Iniciando instalação do Clover Boot Manager..." -ForegroundColor Yellow

# Criar diretório temporário
$tempDir = "$env:TEMP\CloverInstall"
if (Test-Path $tempDir) {
    Remove-Item -Path $tempDir -Recurse -Force
}
New-Item -Path $tempDir -ItemType Directory -Force | Out-Null

# Verificar se o arquivo local do Clover existe
$localFile = "$PSScriptRoot\CloverV2-5161.zip"
if (-not (Test-Path $localFile)) {
    Write-Host "Arquivo do Clover não encontrado: $localFile" -ForegroundColor Red
    Write-Host "Por favor, baixe o arquivo do Clover e coloque-o no mesmo diretório deste script." -ForegroundColor Red
    exit 1
}

# Copiar arquivo para diretório temporário
$zipFile = Join-Path -Path $tempDir -ChildPath "CloverV2.zip"
Copy-Item -Path $localFile -Destination $zipFile -Force

# Extrair arquivo
Write-Host "Extraindo arquivo do Clover..." -ForegroundColor Yellow
Expand-Archive -Path $zipFile -DestinationPath $tempDir -Force

# Verificar se a extração foi bem-sucedida
if (-not (Test-Path "$tempDir\EFI")) {
    Write-Host "Falha ao extrair o arquivo do Clover: diretório EFI não encontrado" -ForegroundColor Red
    exit 1
}

# Encontrar a partição EFI
Write-Host "Procurando partição EFI..." -ForegroundColor Yellow

# Verificar se já existe uma partição EFI montada
$efiDriveLetter = $null
$existingEfiVolumes = Get-Volume | Where-Object { Test-Path "$($_.DriveLetter):\EFI" -ErrorAction SilentlyContinue }

if ($existingEfiVolumes) {
    $efiDriveLetter = $existingEfiVolumes[0].DriveLetter
    Write-Host "Partição EFI já montada em ${efiDriveLetter}:" -ForegroundColor Green
} else {
    # Tentar montar a partição EFI
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
                                Write-Host "Atribuída letra temporária $letter à partição EFI" -ForegroundColor Yellow
                                break
                            } catch {
                                Write-Host "Erro ao atribuir letra $letter à partição EFI: $_" -ForegroundColor Red
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
                Write-Host "Erro ao acessar partição EFI: $_" -ForegroundColor Red
            }
        }
    }
}

# Verificar se encontramos a partição EFI
if (-not $efiDriveLetter) {
    Write-Host "Não foi possível encontrar ou montar a partição EFI" -ForegroundColor Red
    exit 1
}

$efiPath = "${efiDriveLetter}:"
Write-Host "Partição EFI encontrada em $efiPath" -ForegroundColor Green

# Criar backup da partição EFI
$backupDate = Get-Date -Format "yyyyMMdd_HHmmss"
$backupDir = "$env:USERPROFILE\Documents\EFI_Backup_$backupDate"
Write-Host "Criando backup da partição EFI em $backupDir..." -ForegroundColor Yellow

if (-not (Test-Path "$env:USERPROFILE\Documents")) {
    New-Item -Path "$env:USERPROFILE\Documents" -ItemType Directory -Force | Out-Null
}

New-Item -Path $backupDir -ItemType Directory -Force | Out-Null
Copy-Item -Path "$efiPath\*" -Destination $backupDir -Recurse -Force

# Instalar o Clover
Write-Host "Instalando Clover na partição EFI..." -ForegroundColor Yellow

# Verificar se o diretório EFI existe na partição
if (-not (Test-Path "$efiPath\EFI")) {
    New-Item -Path "$efiPath\EFI" -ItemType Directory -Force | Out-Null
}

# Preservar o bootloader original
if (Test-Path "$efiPath\EFI\BOOT\BOOTX64.efi") {
    Write-Host "Preservando bootloader original..." -ForegroundColor Yellow
    Copy-Item -Path "$efiPath\EFI\BOOT\BOOTX64.efi" -Destination "$efiPath\EFI\BOOT\BOOTX64.efi.original" -Force
    Write-Host "Bootloader original preservado como BOOTX64.efi.original" -ForegroundColor Green
}

# Verificar se o diretório CLOVER já existe e fazer backup se necessário
if (Test-Path "$efiPath\EFI\CLOVER") {
    $cloverBackupDir = "$efiPath\EFI\CLOVER.bak"
    if (Test-Path $cloverBackupDir) {
        Remove-Item -Path $cloverBackupDir -Recurse -Force
    }
    Rename-Item -Path "$efiPath\EFI\CLOVER" -NewName "CLOVER.bak"
    Write-Host "Backup da instalação anterior do Clover criado como CLOVER.bak" -ForegroundColor Yellow
}

# Copiar diretório CLOVER
Write-Host "Copiando arquivos do Clover para a partição EFI..." -ForegroundColor Yellow
Copy-Item -Path "$tempDir\EFI\CLOVER" -Destination "$efiPath\EFI\" -Recurse -Force

# Verificar se a cópia foi bem-sucedida
if (Test-Path "$efiPath\EFI\CLOVER\CLOVERX64.efi") {
    Write-Host "Arquivos do Clover copiados com sucesso" -ForegroundColor Green
    
    # Perguntar se deseja usar o Clover como bootloader principal
    $useCloverAsMain = $false
    $useCloverAsMainPrompt = Read-Host "Deseja configurar o Clover como bootloader principal? (S/N) [N]"
    if ($useCloverAsMainPrompt -eq "S" -or $useCloverAsMainPrompt -eq "s") {
        $useCloverAsMain = $true
        Write-Host "Configurando Clover como bootloader principal..." -ForegroundColor Yellow
    } else {
        Write-Host "Preservando bootloader original..." -ForegroundColor Yellow
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
            Write-Host "Clover configurado como bootloader principal" -ForegroundColor Green
        } else {
            Write-Host "Falha ao configurar Clover como bootloader principal" -ForegroundColor Red
        }
    }
} else {
    Write-Host "Falha ao copiar arquivos do Clover: CLOVERX64.efi não encontrado" -ForegroundColor Red
    
    # Tentar restaurar backup anterior se existir
    if (Test-Path "$efiPath\EFI\CLOVER.bak") {
        Write-Host "Restaurando backup anterior do Clover..." -ForegroundColor Yellow
        Remove-Item -Path "$efiPath\EFI\CLOVER" -Recurse -Force -ErrorAction SilentlyContinue
        Rename-Item -Path "$efiPath\EFI\CLOVER.bak" -NewName "CLOVER"
        Write-Host "Backup anterior do Clover restaurado" -ForegroundColor Green
    }
    
    exit 1
}

# Limpar arquivos temporários
Write-Host "Limpando arquivos temporários..." -ForegroundColor Yellow
Remove-Item -Path $tempDir -Recurse -Force -ErrorAction SilentlyContinue

# Concluído
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "      INSTALAÇÃO DO CLOVER BOOT MANAGER CONCLUÍDA   " -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host
Write-Host "O Clover Boot Manager foi instalado com sucesso!" -ForegroundColor Green
Write-Host
Write-Host "Um backup da partição EFI foi criado em:" -ForegroundColor Yellow
Write-Host "  $backupDir" -ForegroundColor Yellow
Write-Host
Write-Host "Para acessar o Clover na próxima inicialização, reinicie o computador." -ForegroundColor Yellow
Write-Host

exit 0
