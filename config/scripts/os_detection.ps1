# Script de detecção de sistemas operacionais
# Este script detecta os sistemas operacionais instalados para configuração do Clover

function Get-InstalledOperatingSystems {
    <#
    .SYNOPSIS
        Detecta sistemas operacionais instalados no sistema.
    .DESCRIPTION
        Detecta sistemas operacionais instalados, incluindo Windows, Linux e macOS.
        Identifica suas localizações e bootloaders para configuração do Clover.
    .OUTPUTS
        Retorna um array de objetos com informações sobre os sistemas operacionais detectados.
    #>
    [CmdletBinding()]
    param ()
    
    $operatingSystems = @()
    
    Write-Host "Detectando sistemas operacionais instalados..." -ForegroundColor Yellow
    
    # Detectar Windows
    try {
        $windowsInstalled = Test-Path "C:\Windows"
        if ($windowsInstalled) {
            $windowsVersion = Get-WmiObject -Class Win32_OperatingSystem | Select-Object -ExpandProperty Caption
            
            $operatingSystems += [PSCustomObject]@{
                Name = $windowsVersion
                Type = "Windows"
                Path = "C:\Windows"
                BootLoader = "EFI\Microsoft\Boot\bootmgfw.efi"
                DriveLabel = "Windows"
                Detected = $true
                Active = $true
            }
            
            Write-Host "Detectado: $windowsVersion" -ForegroundColor Green
        }
    } catch {
        Write-Host "Erro ao detectar Windows: $_" -ForegroundColor Red
    }
    
    # Detectar outros sistemas operacionais através de partições
    try {
        $disks = Get-Disk | Where-Object {$_.PartitionStyle -eq "GPT"}
        
        foreach ($disk in $disks) {
            $partitions = $disk | Get-Partition | Where-Object {$_.Size -gt 10GB}
            
            foreach ($partition in $partitions) {
                try {
                    # Tentar obter volume
                    $volume = $partition | Get-Volume -ErrorAction SilentlyContinue
                    
                    if ($volume -and $volume.FileSystemType -ne "NTFS" -and $volume.FileSystemType -ne $null) {
                        # Possível sistema Linux ou macOS
                        $driveLetter = $volume.DriveLetter
                        $driveLabel = $volume.FileSystemLabel
                        
                        if ($volume.FileSystemType -eq "HFS+" -or $volume.FileSystemType -eq "APFS") {
                            # Provável macOS
                            $operatingSystems += [PSCustomObject]@{
                                Name = "macOS"
                                Type = "macOS"
                                Path = "${driveLetter}:\"
                                BootLoader = "EFI\Apple\Boot\bootmgfw.efi"
                                DriveLabel = $driveLabel
                                Detected = $true
                                Active = $true
                            }
                            
                            Write-Host "Detectado: macOS em $driveLabel (${driveLetter}:)" -ForegroundColor Green
                        } elseif ($volume.FileSystemType -eq "ext4" -or $volume.FileSystemType -eq "ext3" -or $volume.FileSystemType -eq "ext2" -or $volume.FileSystemType -eq "btrfs" -or $volume.FileSystemType -eq "xfs") {
                            # Provável Linux
                            $linuxType = "Linux"
                            
                            # Tentar identificar a distribuição
                            if ($driveLetter) {
                                if (Test-Path "${driveLetter}:\etc\os-release") {
                                    $osRelease = Get-Content "${driveLetter}:\etc\os-release" -ErrorAction SilentlyContinue
                                    $distroName = ($osRelease | Where-Object { $_ -match "^NAME=" }) -replace 'NAME="(.+)"', '$1'
                                    
                                    if ($distroName) {
                                        $linuxType = $distroName
                                    }
                                } elseif (Test-Path "${driveLetter}:\etc\steamos-release") {
                                    $linuxType = "SteamOS"
                                } elseif (Test-Path "${driveLetter}:\etc\debian_version") {
                                    $linuxType = "Debian"
                                } elseif (Test-Path "${driveLetter}:\etc\fedora-release") {
                                    $linuxType = "Fedora"
                                } elseif (Test-Path "${driveLetter}:\etc\redhat-release") {
                                    $linuxType = "Red Hat"
                                } elseif (Test-Path "${driveLetter}:\etc\arch-release") {
                                    $linuxType = "Arch Linux"
                                } elseif (Test-Path "${driveLetter}:\etc\SuSE-release") {
                                    $linuxType = "SuSE"
                                } elseif (Test-Path "${driveLetter}:\etc\gentoo-release") {
                                    $linuxType = "Gentoo"
                                }
                            }
                            
                            $operatingSystems += [PSCustomObject]@{
                                Name = $linuxType
                                Type = "Linux"
                                Path = "${driveLetter}:\"
                                BootLoader = "EFI\ubuntu\grubx64.efi" # Padrão, pode variar
                                DriveLabel = $driveLabel
                                Detected = $true
                                Active = $true
                            }
                            
                            Write-Host "Detectado: $linuxType em $driveLabel (${driveLetter}:)" -ForegroundColor Green
                        }
                    }
                } catch {
                    # Ignorar erros de acesso a volumes
                }
            }
        }
    } catch {
        Write-Host "Erro ao detectar outros sistemas operacionais: $_" -ForegroundColor Red
    }
    
    # Detectar sistemas operacionais através da partição EFI
    try {
        $efiPartitions = Get-Partition | Where-Object {$_.GptType -eq "{c12a7328-f81f-11d2-ba4b-00a0c93ec93b}"}
        
        if ($efiPartitions) {
            $efiPartition = $efiPartitions[0]
            $efiVolume = $efiPartition | Get-Volume -ErrorAction SilentlyContinue
            $tempDriveCreated = $false
            $efiDriveLetter = $null
            
            # Se não tiver letra de unidade, atribuir uma temporária
            if ($efiVolume -and -not $efiVolume.DriveLetter) {
                $driveLetter = 69 # Letra 'E'
                while ([char]$driveLetter -le 90) {
                    $letter = [char]$driveLetter
                    if (-not (Get-Volume -DriveLetter $letter -ErrorAction SilentlyContinue)) {
                        $efiPartition | Add-PartitionAccessPath -AccessPath "${letter}:"
                        $efiVolume = Get-Volume -DriveLetter $letter
                        $efiDriveLetter = $letter
                        $tempDriveCreated = $true
                        Write-Host "Atribuída letra temporária $letter à partição EFI" -ForegroundColor Yellow
                        break
                    }
                    $driveLetter++
                }
            } elseif ($efiVolume) {
                $efiDriveLetter = $efiVolume.DriveLetter
            }
            
            if ($efiDriveLetter) {
                $efiPath = "${efiDriveLetter}:"
                
                # Verificar bootloaders na partição EFI
                if (Test-Path "$efiPath\EFI\Microsoft\Boot\bootmgfw.efi") {
                    # Windows bootloader encontrado
                    if (-not ($operatingSystems | Where-Object { $_.Type -eq "Windows" })) {
                        $operatingSystems += [PSCustomObject]@{
                            Name = "Windows"
                            Type = "Windows"
                            Path = "Desconhecido"
                            BootLoader = "EFI\Microsoft\Boot\bootmgfw.efi"
                            DriveLabel = "Desconhecido"
                            Detected = $true
                            Active = $true
                        }
                        
                        Write-Host "Detectado: Windows (apenas bootloader)" -ForegroundColor Yellow
                    }
                }
                
                if (Test-Path "$efiPath\EFI\ubuntu") {
                    # Ubuntu bootloader encontrado
                    if (-not ($operatingSystems | Where-Object { $_.Type -eq "Linux" -and $_.Name -eq "Ubuntu" })) {
                        $operatingSystems += [PSCustomObject]@{
                            Name = "Ubuntu"
                            Type = "Linux"
                            Path = "Desconhecido"
                            BootLoader = "EFI\ubuntu\grubx64.efi"
                            DriveLabel = "Desconhecido"
                            Detected = $true
                            Active = $true
                        }
                        
                        Write-Host "Detectado: Ubuntu (apenas bootloader)" -ForegroundColor Yellow
                    }
                }
                
                if (Test-Path "$efiPath\EFI\debian") {
                    # Debian bootloader encontrado
                    if (-not ($operatingSystems | Where-Object { $_.Type -eq "Linux" -and $_.Name -eq "Debian" })) {
                        $operatingSystems += [PSCustomObject]@{
                            Name = "Debian"
                            Type = "Linux"
                            Path = "Desconhecido"
                            BootLoader = "EFI\debian\grubx64.efi"
                            DriveLabel = "Desconhecido"
                            Detected = $true
                            Active = $true
                        }
                        
                        Write-Host "Detectado: Debian (apenas bootloader)" -ForegroundColor Yellow
                    }
                }
                
                if (Test-Path "$efiPath\EFI\fedora") {
                    # Fedora bootloader encontrado
                    if (-not ($operatingSystems | Where-Object { $_.Type -eq "Linux" -and $_.Name -eq "Fedora" })) {
                        $operatingSystems += [PSCustomObject]@{
                            Name = "Fedora"
                            Type = "Linux"
                            Path = "Desconhecido"
                            BootLoader = "EFI\fedora\grubx64.efi"
                            DriveLabel = "Desconhecido"
                            Detected = $true
                            Active = $true
                        }
                        
                        Write-Host "Detectado: Fedora (apenas bootloader)" -ForegroundColor Yellow
                    }
                }
                
                if (Test-Path "$efiPath\EFI\steamos") {
                    # SteamOS bootloader encontrado
                    if (-not ($operatingSystems | Where-Object { $_.Type -eq "Linux" -and $_.Name -eq "SteamOS" })) {
                        $operatingSystems += [PSCustomObject]@{
                            Name = "SteamOS"
                            Type = "Linux"
                            Path = "Desconhecido"
                            BootLoader = "EFI\steamos\grubx64.efi"
                            DriveLabel = "Desconhecido"
                            Detected = $true
                            Active = $true
                        }
                        
                        Write-Host "Detectado: SteamOS (apenas bootloader)" -ForegroundColor Yellow
                    }
                }
                
                if (Test-Path "$efiPath\EFI\Apple") {
                    # macOS bootloader encontrado
                    if (-not ($operatingSystems | Where-Object { $_.Type -eq "macOS" })) {
                        $operatingSystems += [PSCustomObject]@{
                            Name = "macOS"
                            Type = "macOS"
                            Path = "Desconhecido"
                            BootLoader = "EFI\Apple\Boot\bootmgfw.efi"
                            DriveLabel = "Desconhecido"
                            Detected = $true
                            Active = $true
                        }
                        
                        Write-Host "Detectado: macOS (apenas bootloader)" -ForegroundColor Yellow
                    }
                }
                
                # Limpar letra de unidade temporária se foi criada
                if ($tempDriveCreated) {
                    $efiPartition | Remove-PartitionAccessPath -AccessPath "$efiPath"
                    Write-Host "Removida letra de unidade temporária $efiDriveLetter" -ForegroundColor Yellow
                }
            }
        }
    } catch {
        Write-Host "Erro ao verificar bootloaders na partição EFI: $_" -ForegroundColor Red
    }
    
    # Se nenhum sistema operacional foi detectado, adicionar Windows como padrão
    if ($operatingSystems.Count -eq 0) {
        $operatingSystems += [PSCustomObject]@{
            Name = "Windows"
            Type = "Windows"
            Path = "C:\Windows"
            BootLoader = "EFI\Microsoft\Boot\bootmgfw.efi"
            DriveLabel = "Windows"
            Detected = $false
            Active = $true
        }
        
        Write-Host "Nenhum sistema operacional detectado. Adicionando Windows como padrão." -ForegroundColor Yellow
    }
    
    return $operatingSystems
}

function Get-CloverConfig {
    <#
    .SYNOPSIS
        Gera uma configuração do Clover com base nos sistemas operacionais detectados.
    .DESCRIPTION
        Gera um arquivo config.plist para o Clover com entradas para os sistemas operacionais detectados.
    .PARAMETER OperatingSystems
        Array de objetos com informações sobre os sistemas operacionais detectados.
    .PARAMETER OutputPath
        Caminho onde o arquivo config.plist será salvo.
    .OUTPUTS
        Retorna o caminho do arquivo de configuração gerado.
    #>
    [CmdletBinding()]
    param (
        [Parameter(Mandatory=$true)]
        [array]$OperatingSystems,
        
        [Parameter(Mandatory=$false)]
        [string]$OutputPath = "$env:TEMP\clover_config.plist"
    )
    
    Write-Host "Gerando configuração do Clover para os sistemas operacionais detectados..." -ForegroundColor Yellow
    
    # Criar estrutura básica do config.plist
    $configXml = @"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Boot</key>
    <dict>
        <key>Arguments</key>
        <string></string>
        <key>DefaultVolume</key>
        <string>LastBootedVolume</string>
        <key>Timeout</key>
        <integer>5</integer>
        <key>XMPDetection</key>
        <string>Yes</string>
    </dict>
    <key>GUI</key>
    <dict>
        <key>Mouse</key>
        <dict>
            <key>Enabled</key>
            <true/>
            <key>Speed</key>
            <integer>8</integer>
        </dict>
        <key>Scan</key>
        <dict>
            <key>Entries</key>
            <true/>
            <key>Legacy</key>
            <false/>
            <key>Tool</key>
            <true/>
        </dict>
        <key>Theme</key>
        <string>Clovy</string>
        <key>Custom</key>
        <dict>
            <key>Entries</key>
            <array>
"@
    
    # Adicionar entradas para cada sistema operacional detectado
    foreach ($os in $OperatingSystems) {
        if ($os.Active) {
            $entryTitle = $os.Name
            $entryType = $os.Type.ToLower()
            $entryPath = $os.BootLoader
            
            $entryXml = @"
                <dict>
                    <key>Disabled</key>
                    <false/>
                    <key>FullTitle</key>
                    <string>$entryTitle</string>
                    <key>Hidden</key>
                    <false/>
                    <key>Type</key>
                    <string>$entryType</string>
                    <key>Path</key>
                    <string>$entryPath</string>
                </dict>
"@
            
            $configXml += $entryXml
        }
    }
    
    # Fechar a estrutura XML
    $configXml += @"
            </array>
        </dict>
    </dict>
</dict>
</plist>
"@
    
    # Salvar o arquivo de configuração
    $configXml | Out-File -FilePath $OutputPath -Encoding utf8
    
    Write-Host "Configuração do Clover gerada com sucesso: $OutputPath" -ForegroundColor Green
    
    return $OutputPath
}

# Exportar funções
Export-ModuleMember -Function Get-InstalledOperatingSystems, Get-CloverConfig
