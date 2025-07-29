# Script de verificação completa da instalação do Clover
# Este script verifica a integridade da instalação do Clover Boot Manager

function Test-CloverInstallation {
    <#
    .SYNOPSIS
        Verifica a integridade da instalação do Clover Boot Manager.
    .DESCRIPTION
        Realiza uma verificação completa da instalação do Clover, incluindo
        arquivos essenciais, configuração e integridade do bootloader.
    .PARAMETER EfiDriveLetter
        Letra da unidade da partição EFI. Se não for fornecida, tentará encontrar automaticamente.
    .OUTPUTS
        Retorna um objeto com o resultado da verificação e detalhes.
    #>
    [CmdletBinding()]
    param (
        [Parameter(Mandatory=$false)]
        [string]$EfiDriveLetter
    )
    
    $result = @{
        Success = $false
        Details = @()
        EfiPath = $null
        MissingFiles = @()
        ConfigurationIssues = @()
        BootloaderStatus = "Unknown"
    }
    
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
                    $result.Details += "Erro ao acessar partição EFI: $_"
                }
            }
        }
    } else {
        # Verificar se a letra fornecida existe
        $efiVolume = Get-Volume -DriveLetter $EfiDriveLetter -ErrorAction SilentlyContinue
        if (-not $efiVolume) {
            Write-Host "Letra de unidade $EfiDriveLetter não encontrada" -ForegroundColor Red
            $result.Details += "Letra de unidade $EfiDriveLetter não encontrada"
            return $result
        }
    }
    
    # Verificar se encontramos a partição EFI
    if (-not $EfiDriveLetter) {
        Write-Host "Não foi possível encontrar ou montar a partição EFI" -ForegroundColor Red
        $result.Details += "Não foi possível encontrar ou montar a partição EFI"
        return $result
    }
    
    $efiPath = "${EfiDriveLetter}:"
    $result.EfiPath = $efiPath
    
    # 1. Verificar arquivos essenciais do Clover
    $essentialFiles = @(
        "$efiPath\EFI\CLOVER\CLOVERX64.efi",
        "$efiPath\EFI\CLOVER\config.plist"
    )
    
    $allFilesExist = $true
    foreach ($file in $essentialFiles) {
        if (-not (Test-Path $file)) {
            Write-Host "Arquivo essencial não encontrado: $file" -ForegroundColor Red
            $result.Details += "Arquivo essencial não encontrado: $file"
            $result.MissingFiles += $file
            $allFilesExist = $false
        } else {
            Write-Host "Arquivo essencial encontrado: $file" -ForegroundColor Green
        }
    }
    
    # 2. Verificar diretórios importantes
    $essentialDirs = @(
        "$efiPath\EFI\CLOVER\drivers\UEFI",
        "$efiPath\EFI\CLOVER\themes"
    )
    
    foreach ($dir in $essentialDirs) {
        if (-not (Test-Path $dir)) {
            Write-Host "Diretório importante não encontrado: $dir" -ForegroundColor Yellow
            $result.Details += "Diretório importante não encontrado: $dir"
            $result.MissingFiles += $dir
        } else {
            Write-Host "Diretório importante encontrado: $dir" -ForegroundColor Green
        }
    }
    
    # 3. Verificar integridade do arquivo de configuração
    if (Test-Path "$efiPath\EFI\CLOVER\config.plist") {
        try {
            # Verificar se o arquivo é um XML válido
            $configContent = Get-Content "$efiPath\EFI\CLOVER\config.plist" -Raw
            
            # Verificar elementos essenciais no config.plist
            $configValid = $true
            
            if (-not ($configContent -match "<key>Boot</key>")) {
                Write-Host "Configuração do Clover não contém seção Boot" -ForegroundColor Yellow
                $result.Details += "Configuração do Clover não contém seção Boot"
                $result.ConfigurationIssues += "Seção Boot ausente"
                $configValid = $false
            }
            
            if (-not ($configContent -match "<key>GUI</key>")) {
                Write-Host "Configuração do Clover não contém seção GUI" -ForegroundColor Yellow
                $result.Details += "Configuração do Clover não contém seção GUI"
                $result.ConfigurationIssues += "Seção GUI ausente"
                $configValid = $false
            }
            
            if ($configValid) {
                Write-Host "Arquivo de configuração do Clover parece válido" -ForegroundColor Green
            } else {
                Write-Host "Arquivo de configuração do Clover pode estar incompleto" -ForegroundColor Yellow
            }
        } catch {
            Write-Host "Erro ao verificar arquivo de configuração: $_" -ForegroundColor Red
            $result.Details += "Erro ao verificar arquivo de configuração: $_"
            $result.ConfigurationIssues += "Erro ao analisar config.plist"
        }
    }
    
    # 4. Verificar backup do bootloader original
    if (Test-Path "$efiPath\EFI\BOOT\BOOTX64.efi.original") {
        Write-Host "Backup do bootloader original encontrado" -ForegroundColor Green
        $result.Details += "Backup do bootloader original encontrado"
        $result.BootloaderStatus = "Original Preserved"
    } else {
        Write-Host "Backup do bootloader original não encontrado" -ForegroundColor Yellow
        $result.Details += "Backup do bootloader original não encontrado"
        $result.BootloaderStatus = "No Original Backup"
    }
    
    # 5. Verificar se o Clover está configurado como bootloader principal
    if (Test-Path "$efiPath\EFI\BOOT\BOOTX64.efi") {
        try {
            $bootloaderContent = Get-Content "$efiPath\EFI\BOOT\BOOTX64.efi" -Raw -Encoding Byte -TotalCount 100
            $cloverContent = Get-Content "$efiPath\EFI\CLOVER\CLOVERX64.efi" -Raw -Encoding Byte -TotalCount 100 -ErrorAction SilentlyContinue
            
            if ($null -ne $cloverContent -and (Compare-Object $bootloaderContent $cloverContent -Count 100).Length -eq 0) {
                Write-Host "Clover está configurado como bootloader principal" -ForegroundColor Green
                $result.Details += "Clover está configurado como bootloader principal"
                $result.BootloaderStatus = "Clover Primary"
            } else {
                Write-Host "Clover não está configurado como bootloader principal" -ForegroundColor Yellow
                $result.Details += "Clover não está configurado como bootloader principal"
                if ($result.BootloaderStatus -eq "Original Preserved") {
                    $result.BootloaderStatus = "Original Primary, Clover Secondary"
                }
            }
        } catch {
            Write-Host "Erro ao verificar bootloader principal: $_" -ForegroundColor Red
            $result.Details += "Erro ao verificar bootloader principal: $_"
        }
    }
    
    # 6. Verificar drivers UEFI essenciais
    $essentialDrivers = @(
        "$efiPath\EFI\CLOVER\drivers\UEFI\FSInject.efi",
        "$efiPath\EFI\CLOVER\drivers\UEFI\ApfsDriverLoader.efi",
        "$efiPath\EFI\CLOVER\drivers\UEFI\HFSPlus.efi"
    )
    
    $driversFound = 0
    foreach ($driver in $essentialDrivers) {
        if (Test-Path $driver) {
            $driversFound++
        } else {
            Write-Host "Driver UEFI recomendado não encontrado: $driver" -ForegroundColor Yellow
            $result.Details += "Driver UEFI recomendado não encontrado: $driver"
        }
    }
    
    if ($driversFound -gt 0) {
        Write-Host "$driversFound drivers UEFI essenciais encontrados" -ForegroundColor Green
    } else {
        Write-Host "Nenhum driver UEFI essencial encontrado" -ForegroundColor Yellow
        $result.Details += "Nenhum driver UEFI essencial encontrado"
    }
    
    # 7. Verificar espaço livre na partição EFI
    try {
        $freeSpace = $efiVolume.SizeRemaining
        $freeSpaceMB = [math]::Round($freeSpace / 1MB, 2)
        
        if ($freeSpaceMB -lt 10) {
            Write-Host "AVISO: Pouco espaço livre na partição EFI: $freeSpaceMB MB" -ForegroundColor Red
            $result.Details += "AVISO: Pouco espaço livre na partição EFI: $freeSpaceMB MB"
        } else {
            Write-Host "Espaço livre na partição EFI: $freeSpaceMB MB" -ForegroundColor Green
        }
    } catch {
        Write-Host "Erro ao verificar espaço livre na partição EFI: $_" -ForegroundColor Red
        $result.Details += "Erro ao verificar espaço livre na partição EFI: $_"
    }
    
    # Determinar resultado final
    $result.Success = $allFilesExist -and ($result.ConfigurationIssues.Count -eq 0)
    
    # Limpar letra de unidade temporária se foi criada
    if ($tempDriveCreated) {
        $efiPartitions[0] | Remove-PartitionAccessPath -AccessPath "$efiPath"
        Write-Host "Removida letra de unidade temporária $EfiDriveLetter" -ForegroundColor Yellow
    }
    
    return $result
}

function Test-CloverBootability {
    <#
    .SYNOPSIS
        Verifica se o Clover está configurado corretamente para inicialização.
    .DESCRIPTION
        Verifica se o Clover está configurado corretamente para inicialização,
        incluindo entradas de boot e configuração do firmware.
    .OUTPUTS
        Retorna um objeto com o resultado da verificação e detalhes.
    #>
    [CmdletBinding()]
    param ()
    
    $result = @{
        Success = $false
        Details = @()
        BootEntries = @()
    }
    
    # Verificar se estamos em um sistema UEFI
    try {
        $firmwareType = (Get-ComputerInfo).BiosFirmwareType
        $isUefi = $firmwareType -eq "Uefi"
        
        if (-not $isUefi) {
            Write-Host "Sistema não está usando firmware UEFI" -ForegroundColor Yellow
            $result.Details += "Sistema não está usando firmware UEFI"
            return $result
        }
        
        Write-Host "Sistema usando firmware UEFI: OK" -ForegroundColor Green
    } catch {
        Write-Host "Erro ao verificar tipo de firmware: $_" -ForegroundColor Red
        $result.Details += "Erro ao verificar tipo de firmware: $_"
        return $result
    }
    
    # Verificar entradas de boot usando bcdedit
    try {
        $bcdOutput = & bcdedit /enum firmware
        
        # Verificar se há entradas relacionadas ao Clover
        $cloverEntries = $bcdOutput | Where-Object { $_ -match "clover|CLOVER" }
        
        if ($cloverEntries.Count -gt 0) {
            Write-Host "Entradas de boot relacionadas ao Clover encontradas:" -ForegroundColor Green
            foreach ($entry in $cloverEntries) {
                Write-Host "  $entry" -ForegroundColor Green
                $result.BootEntries += $entry
            }
            $result.Details += "Entradas de boot relacionadas ao Clover encontradas"
        } else {
            Write-Host "Nenhuma entrada de boot relacionada ao Clover encontrada" -ForegroundColor Yellow
            $result.Details += "Nenhuma entrada de boot relacionada ao Clover encontrada"
        }
        
        # Verificar ordem de boot
        $bootOrder = $bcdOutput | Where-Object { $_ -match "displayorder" }
        if ($bootOrder) {
            Write-Host "Ordem de boot: $bootOrder" -ForegroundColor Green
            $result.Details += "Ordem de boot: $bootOrder"
        }
    } catch {
        Write-Host "Erro ao verificar entradas de boot: $_" -ForegroundColor Red
        $result.Details += "Erro ao verificar entradas de boot: $_"
    }
    
    # Verificar se o Clover está na partição EFI
    $cloverInstallation = Test-CloverInstallation
    if ($cloverInstallation.Success) {
        Write-Host "Instalação do Clover verificada com sucesso" -ForegroundColor Green
        $result.Details += "Instalação do Clover verificada com sucesso"
        $result.Success = $true
    } else {
        Write-Host "Problemas encontrados na instalação do Clover" -ForegroundColor Yellow
        $result.Details += "Problemas encontrados na instalação do Clover"
        $result.Details += $cloverInstallation.Details
    }
    
    return $result
}

# Exportar funções
Export-ModuleMember -Function Test-CloverInstallation, Test-CloverBootability
