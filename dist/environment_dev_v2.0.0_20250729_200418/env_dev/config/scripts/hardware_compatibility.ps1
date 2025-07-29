# Script de verificação de compatibilidade de hardware
# Este script verifica se o hardware é compatível com o Clover Boot Manager

function Test-HardwareCompatibility {
    <#
    .SYNOPSIS
        Verifica a compatibilidade do hardware com o Clover Boot Manager.
    .DESCRIPTION
        Verifica se o hardware atual é compatível com o Clover Boot Manager,
        incluindo firmware UEFI, espaço na partição EFI, e outras verificações.
    .OUTPUTS
        Retorna um objeto com o resultado da verificação e detalhes.
    #>
    [CmdletBinding()]
    param ()
    
    $result = @{
        Compatible = $true
        Issues = @()
        Details = @()
        IsSteamDeck = $false
        IsUefi = $false
        EfiSpace = 0
        EfiDriveLetter = $null
    }
    
    Write-Host "Verificando compatibilidade de hardware para o Clover Boot Manager..." -ForegroundColor Yellow
    
    # Verificar se é um Steam Deck
    try {
        $computerSystem = Get-WmiObject -Class Win32_ComputerSystem
        $manufacturer = $computerSystem.Manufacturer
        $model = $computerSystem.Model
        
        $result.Details += "Fabricante: $manufacturer"
        $result.Details += "Modelo: $model"
        
        if ($manufacturer -like "*Valve*" -or $model -like "*Steam Deck*") {
            $result.IsSteamDeck = $true
            $result.Details += "Dispositivo identificado como Steam Deck"
            Write-Host "Dispositivo identificado como Steam Deck" -ForegroundColor Green
        }
    } catch {
        $result.Issues += "Não foi possível determinar o fabricante do hardware: $_"
        Write-Host "Não foi possível determinar o fabricante do hardware: $_" -ForegroundColor Red
    }
    
    # Verificar firmware UEFI
    try {
        $firmware = Get-ComputerInfo | Select-Object BiosFirmwareType
        $isUefi = $firmware.BiosFirmwareType -eq "Uefi"
        $result.IsUefi = $isUefi
        
        if ($isUefi) {
            $result.Details += "Sistema usando firmware UEFI: OK"
            Write-Host "Sistema usando firmware UEFI: OK" -ForegroundColor Green
        } else {
            $result.Compatible = $false
            $result.Issues += "O sistema não está usando firmware UEFI, que é necessário para o Clover"
            Write-Host "O sistema não está usando firmware UEFI, que é necessário para o Clover" -ForegroundColor Red
        }
    } catch {
        $result.Issues += "Não foi possível determinar o tipo de firmware: $_"
        Write-Host "Não foi possível determinar o tipo de firmware: $_" -ForegroundColor Red
    }
    
    # Verificar partição EFI
    try {
        $efiPartition = Get-Partition | Where-Object { $_.GptType -eq "{c12a7328-f81f-11d2-ba4b-00a0c93ec93b}" }
        
        if ($efiPartition) {
            $efiVolume = $efiPartition | Get-Volume -ErrorAction SilentlyContinue
            $tempDriveCreated = $false
            
            # Se não tiver letra de unidade, atribuir uma temporária
            if ($efiVolume -and -not $efiVolume.DriveLetter) {
                $driveLetter = 69 # Letra 'E'
                while ([char]$driveLetter -le 90) {
                    $letter = [char]$driveLetter
                    if (-not (Get-Volume -DriveLetter $letter -ErrorAction SilentlyContinue)) {
                        $efiPartition | Add-PartitionAccessPath -AccessPath "${letter}:"
                        $efiVolume = Get-Volume -DriveLetter $letter
                        $tempDriveCreated = $true
                        Write-Host "Atribuída letra temporária $letter à partição EFI" -ForegroundColor Yellow
                        break
                    }
                    $driveLetter++
                }
            }
            
            if ($efiVolume) {
                $result.EfiDriveLetter = $efiVolume.DriveLetter
                $efiSize = [math]::Round($efiVolume.Size / 1MB, 2)
                $efiSpaceRemaining = [math]::Round($efiVolume.SizeRemaining / 1MB, 2)
                $result.EfiSpace = $efiSpaceRemaining
                
                $result.Details += "Partição EFI encontrada: $($efiVolume.DriveLetter):"
                $result.Details += "Tamanho da partição EFI: $efiSize MB"
                $result.Details += "Espaço livre na partição EFI: $efiSpaceRemaining MB"
                
                Write-Host "Partição EFI encontrada: $($efiVolume.DriveLetter):" -ForegroundColor Green
                Write-Host "Tamanho da partição EFI: $efiSize MB" -ForegroundColor Green
                Write-Host "Espaço livre na partição EFI: $efiSpaceRemaining MB" -ForegroundColor Green
                
                if ($efiSpaceRemaining -lt 10) {
                    $result.Compatible = $false
                    $result.Issues += "Espaço insuficiente na partição EFI (menos de 10MB disponíveis)"
                    Write-Host "Espaço insuficiente na partição EFI (menos de 10MB disponíveis)" -ForegroundColor Red
                }
                
                # Limpar letra de unidade temporária se foi criada
                if ($tempDriveCreated) {
                    $efiPartition | Remove-PartitionAccessPath -AccessPath "$($efiVolume.DriveLetter):"
                    Write-Host "Removida letra de unidade temporária $($efiVolume.DriveLetter)" -ForegroundColor Yellow
                }
            } else {
                $result.Compatible = $false
                $result.Issues += "Partição EFI encontrada, mas não foi possível acessá-la"
                Write-Host "Partição EFI encontrada, mas não foi possível acessá-la" -ForegroundColor Red
            }
        } else {
            $result.Compatible = $false
            $result.Issues += "Partição EFI não encontrada"
            Write-Host "Partição EFI não encontrada" -ForegroundColor Red
        }
    } catch {
        $result.Issues += "Erro ao verificar partição EFI: $_"
        Write-Host "Erro ao verificar partição EFI: $_" -ForegroundColor Red
    }
    
    # Verificar permissões de administrador
    try {
        $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
        
        if ($isAdmin) {
            $result.Details += "Executando com privilégios de administrador: OK"
            Write-Host "Executando com privilégios de administrador: OK" -ForegroundColor Green
        } else {
            $result.Compatible = $false
            $result.Issues += "Não está executando com privilégios de administrador, que são necessários para instalar o Clover"
            Write-Host "Não está executando com privilégios de administrador, que são necessários para instalar o Clover" -ForegroundColor Red
        }
    } catch {
        $result.Issues += "Erro ao verificar privilégios de administrador: $_"
        Write-Host "Erro ao verificar privilégios de administrador: $_" -ForegroundColor Red
    }
    
    # Verificar se o Secure Boot está ativado
    try {
        $secureBootStatus = Confirm-SecureBootUEFI -ErrorAction SilentlyContinue
        
        if ($secureBootStatus -eq $true) {
            $result.Details += "Secure Boot está ativado. Pode ser necessário desativá-lo para usar o Clover."
            Write-Host "Secure Boot está ativado. Pode ser necessário desativá-lo para usar o Clover." -ForegroundColor Yellow
        } else {
            $result.Details += "Secure Boot está desativado: OK"
            Write-Host "Secure Boot está desativado: OK" -ForegroundColor Green
        }
    } catch {
        $result.Details += "Não foi possível determinar o status do Secure Boot: $_"
        Write-Host "Não foi possível determinar o status do Secure Boot: $_" -ForegroundColor Yellow
    }
    
    # Verificar espaço em disco para instalação
    try {
        $systemDrive = Get-PSDrive -Name C
        $freeSpaceGB = [math]::Round($systemDrive.Free / 1GB, 2)
        
        $result.Details += "Espaço livre no disco do sistema: $freeSpaceGB GB"
        Write-Host "Espaço livre no disco do sistema: $freeSpaceGB GB" -ForegroundColor Green
        
        if ($freeSpaceGB -lt 1) {
            $result.Compatible = $false
            $result.Issues += "Espaço insuficiente no disco do sistema (menos de 1GB disponível)"
            Write-Host "Espaço insuficiente no disco do sistema (menos de 1GB disponível)" -ForegroundColor Red
        }
    } catch {
        $result.Issues += "Erro ao verificar espaço em disco: $_"
        Write-Host "Erro ao verificar espaço em disco: $_" -ForegroundColor Red
    }
    
    # Resumo da compatibilidade
    if ($result.Compatible) {
        Write-Host "Hardware compatível com o Clover Boot Manager" -ForegroundColor Green
    } else {
        Write-Host "Hardware incompatível com o Clover Boot Manager" -ForegroundColor Red
        Write-Host "Problemas encontrados:" -ForegroundColor Red
        foreach ($issue in $result.Issues) {
            Write-Host "  - $issue" -ForegroundColor Red
        }
    }
    
    return $result
}

# Exportar funções
Export-ModuleMember -Function Test-HardwareCompatibility
