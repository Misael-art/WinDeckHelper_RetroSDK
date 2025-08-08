# Script de recuperação para o Clover Boot Manager
# Este script pode ser executado em modo de recuperação para restaurar o sistema após falha na inicialização

param (
    [Parameter(Mandatory=$false)]
    [switch]$SafeMode,
    
    [Parameter(Mandatory=$false)]
    [string]$BackupPath
)

# Importar utilitários de backup da EFI
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$efiBackupUtilsPath = Join-Path -Path $scriptPath -ChildPath "efi_backup_utils.ps1"

if (Test-Path $efiBackupUtilsPath) {
    . $efiBackupUtilsPath
} else {
    Write-Host "ERRO: Não foi possível encontrar o arquivo de utilitários de backup da EFI: $efiBackupUtilsPath" -ForegroundColor Red
    exit 1
}

function Test-SafeMode {
    <#
    .SYNOPSIS
        Verifica se o sistema está em modo seguro.
    .DESCRIPTION
        Verifica se o Windows está sendo executado em modo seguro.
    .OUTPUTS
        Retorna $true se o sistema estiver em modo seguro, $false caso contrário.
    #>
    $safeMode = $false
    
    try {
        $systemInfo = Get-WmiObject -Class Win32_ComputerSystem
        $safeMode = $systemInfo.BootupState -like "*Safe*"
        
        # Verificação alternativa
        if (-not $safeMode) {
            $safeBootKey = Get-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\SafeBoot" -ErrorAction SilentlyContinue
            if ($safeBootKey) {
                $safeMode = $true
            }
        }
    } catch {
        Write-Host "Erro ao verificar modo seguro: $_" -ForegroundColor Red
    }
    
    return $safeMode
}

function Show-RecoveryMenu {
    <#
    .SYNOPSIS
        Exibe o menu de recuperação do Clover.
    .DESCRIPTION
        Exibe um menu interativo com opções para recuperar o sistema após falha na inicialização do Clover.
    #>
    Clear-Host
    Write-Host "====================================================" -ForegroundColor Cyan
    Write-Host "      MODO DE RECUPERAÇÃO DO CLOVER BOOT MANAGER    " -ForegroundColor Cyan
    Write-Host "====================================================" -ForegroundColor Cyan
    Write-Host
    Write-Host "Este utilitário ajuda a recuperar seu sistema após falhas na instalação" -ForegroundColor Yellow
    Write-Host "ou configuração do Clover Boot Manager." -ForegroundColor Yellow
    Write-Host
    Write-Host "Opções disponíveis:" -ForegroundColor White
    Write-Host
    Write-Host "  1. Restaurar partição EFI a partir de backup" -ForegroundColor Green
    Write-Host "  2. Reparar bootloader do Windows" -ForegroundColor Green
    Write-Host "  3. Verificar instalação do Clover" -ForegroundColor Green
    Write-Host "  4. Desinstalar Clover" -ForegroundColor Yellow
    Write-Host "  5. Sair" -ForegroundColor Red
    Write-Host
    
    $choice = Read-Host "Digite o número da opção desejada"
    
    switch ($choice) {
        "1" { Restore-EfiFromBackup }
        "2" { Repair-WindowsBootloader }
        "3" { Test-CloverInstallation }
        "4" { Uninstall-Clover }
        "5" { return }
        default { 
            Write-Host "Opção inválida. Pressione qualquer tecla para continuar..." -ForegroundColor Red
            $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            Show-RecoveryMenu
        }
    }
}

function Restore-EfiFromBackup {
    <#
    .SYNOPSIS
        Restaura a partição EFI a partir de um backup.
    .DESCRIPTION
        Lista os backups disponíveis e permite ao usuário escolher um para restaurar.
    #>
    Clear-Host
    Write-Host "====================================================" -ForegroundColor Cyan
    Write-Host "      RESTAURAÇÃO DA PARTIÇÃO EFI A PARTIR DE BACKUP" -ForegroundColor Cyan
    Write-Host "====================================================" -ForegroundColor Cyan
    Write-Host
    
    # Se um caminho de backup foi fornecido como parâmetro, usar esse
    if ($BackupPath -and (Test-Path $BackupPath)) {
        $restoreResult = Restore-EfiBackup -BackupPath $BackupPath
        
        if ($restoreResult) {
            Write-Host "Restauração concluída com sucesso!" -ForegroundColor Green
        } else {
            Write-Host "Falha na restauração. Verifique os logs para mais detalhes." -ForegroundColor Red
        }
        
        Write-Host "Pressione qualquer tecla para continuar..." -ForegroundColor Yellow
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        Show-RecoveryMenu
        return
    }
    
    # Listar backups disponíveis
    $backups = Get-EfiBackups
    
    if ($backups.Count -eq 0) {
        Write-Host "Nenhum backup encontrado." -ForegroundColor Red
        Write-Host "Pressione qualquer tecla para voltar ao menu principal..." -ForegroundColor Yellow
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        Show-RecoveryMenu
        return
    }
    
    Write-Host "Backups disponíveis:" -ForegroundColor Green
    Write-Host
    
    for ($i = 0; $i -lt $backups.Count; $i++) {
        Write-Host "  $($i+1). $($backups[$i].Name) - Criado em: $($backups[$i].Date)" -ForegroundColor White
    }
    
    Write-Host "  C. Cancelar e voltar ao menu principal" -ForegroundColor Red
    Write-Host
    
    $choice = Read-Host "Digite o número do backup que deseja restaurar"
    
    if ($choice -eq "C" -or $choice -eq "c") {
        Show-RecoveryMenu
        return
    }
    
    $index = [int]$choice - 1
    
    if ($index -ge 0 -and $index -lt $backups.Count) {
        $selectedBackup = $backups[$index]
        
        Write-Host "Você selecionou: $($selectedBackup.Name)" -ForegroundColor Yellow
        $confirm = Read-Host "Tem certeza que deseja restaurar este backup? (S/N)"
        
        if ($confirm -eq "S" -or $confirm -eq "s") {
            $restoreResult = Restore-EfiBackup -BackupPath $selectedBackup.Path
            
            if ($restoreResult) {
                Write-Host "Restauração concluída com sucesso!" -ForegroundColor Green
            } else {
                Write-Host "Falha na restauração. Verifique os logs para mais detalhes." -ForegroundColor Red
            }
        } else {
            Write-Host "Operação cancelada pelo usuário." -ForegroundColor Yellow
        }
    } else {
        Write-Host "Opção inválida." -ForegroundColor Red
    }
    
    Write-Host "Pressione qualquer tecla para continuar..." -ForegroundColor Yellow
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    Show-RecoveryMenu
}

function Repair-WindowsBootloader {
    <#
    .SYNOPSIS
        Repara o bootloader do Windows.
    .DESCRIPTION
        Executa comandos para reparar o bootloader do Windows após falha na instalação do Clover.
    #>
    Clear-Host
    Write-Host "====================================================" -ForegroundColor Cyan
    Write-Host "           REPARAÇÃO DO BOOTLOADER DO WINDOWS       " -ForegroundColor Cyan
    Write-Host "====================================================" -ForegroundColor Cyan
    Write-Host
    
    Write-Host "Este processo irá reparar o bootloader do Windows usando o comando bootrec." -ForegroundColor Yellow
    Write-Host "É recomendado executar este comando apenas se o Windows não estiver iniciando corretamente." -ForegroundColor Yellow
    Write-Host
    
    $confirm = Read-Host "Deseja continuar? (S/N)"
    
    if ($confirm -eq "S" -or $confirm -eq "s") {
        Write-Host "Reparando bootloader do Windows..." -ForegroundColor Green
        
        try {
            # Verificar se estamos em modo administrador
            $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
            
            if (-not $isAdmin) {
                Write-Host "Este comando requer privilégios de administrador." -ForegroundColor Red
                Write-Host "Por favor, execute este script como administrador." -ForegroundColor Red
            } else {
                # Executar comandos de reparo
                Write-Host "Executando: bootrec /fixmbr" -ForegroundColor Yellow
                $result1 = Start-Process -FilePath "bootrec.exe" -ArgumentList "/fixmbr" -Wait -PassThru -NoNewWindow
                
                Write-Host "Executando: bootrec /fixboot" -ForegroundColor Yellow
                $result2 = Start-Process -FilePath "bootrec.exe" -ArgumentList "/fixboot" -Wait -PassThru -NoNewWindow
                
                Write-Host "Executando: bootrec /rebuildbcd" -ForegroundColor Yellow
                $result3 = Start-Process -FilePath "bootrec.exe" -ArgumentList "/rebuildbcd" -Wait -PassThru -NoNewWindow
                
                if ($result1.ExitCode -eq 0 -and $result2.ExitCode -eq 0 -and $result3.ExitCode -eq 0) {
                    Write-Host "Reparação do bootloader concluída com sucesso!" -ForegroundColor Green
                } else {
                    Write-Host "Ocorreram erros durante a reparação do bootloader." -ForegroundColor Red
                    Write-Host "Códigos de saída: $($result1.ExitCode), $($result2.ExitCode), $($result3.ExitCode)" -ForegroundColor Red
                }
            }
        } catch {
            Write-Host "Erro ao reparar bootloader: $_" -ForegroundColor Red
        }
    } else {
        Write-Host "Operação cancelada pelo usuário." -ForegroundColor Yellow
    }
    
    Write-Host "Pressione qualquer tecla para continuar..." -ForegroundColor Yellow
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    Show-RecoveryMenu
}

function Test-CloverInstallation {
    <#
    .SYNOPSIS
        Verifica a instalação do Clover.
    .DESCRIPTION
        Executa uma verificação completa da instalação do Clover e exibe os resultados.
    #>
    Clear-Host
    Write-Host "====================================================" -ForegroundColor Cyan
    Write-Host "           VERIFICAÇÃO DA INSTALAÇÃO DO CLOVER      " -ForegroundColor Cyan
    Write-Host "====================================================" -ForegroundColor Cyan
    Write-Host
    
    # Importar script de verificação do Clover
    $cloverVerificationPath = Join-Path -Path $scriptPath -ChildPath "clover_verification.ps1"
    
    if (Test-Path $cloverVerificationPath) {
        . $cloverVerificationPath
    } else {
        Write-Host "ERRO: Não foi possível encontrar o arquivo de verificação do Clover: $cloverVerificationPath" -ForegroundColor Red
        Write-Host "Pressione qualquer tecla para continuar..." -ForegroundColor Yellow
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        Show-RecoveryMenu
        return
    }
    
    Write-Host "Executando verificação da instalação do Clover..." -ForegroundColor Yellow
    
    # Executar verificação
    $result = Test-CloverInstallation
    
    Write-Host
    Write-Host "Resultado da verificação:" -ForegroundColor Cyan
    Write-Host
    
    if ($result.Success) {
        Write-Host "A instalação do Clover parece estar íntegra." -ForegroundColor Green
    } else {
        Write-Host "Foram encontrados problemas na instalação do Clover:" -ForegroundColor Red
        
        if ($result.MissingFiles.Count -gt 0) {
            Write-Host "  - Arquivos ausentes:" -ForegroundColor Red
            foreach ($file in $result.MissingFiles) {
                Write-Host "    * $file" -ForegroundColor Red
            }
        }
        
        if ($result.ConfigurationIssues.Count -gt 0) {
            Write-Host "  - Problemas de configuração:" -ForegroundColor Red
            foreach ($issue in $result.ConfigurationIssues) {
                Write-Host "    * $issue" -ForegroundColor Red
            }
        }
        
        Write-Host "  - Status do bootloader: $($result.BootloaderStatus)" -ForegroundColor Yellow
    }
    
    Write-Host
    Write-Host "Detalhes adicionais:" -ForegroundColor Cyan
    foreach ($detail in $result.Details) {
        Write-Host "  - $detail" -ForegroundColor White
    }
    
    Write-Host
    Write-Host "Pressione qualquer tecla para continuar..." -ForegroundColor Yellow
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    Show-RecoveryMenu
}

function Uninstall-Clover {
    <#
    .SYNOPSIS
        Desinstala o Clover Boot Manager.
    .DESCRIPTION
        Remove o Clover Boot Manager e restaura o bootloader original.
    #>
    Clear-Host
    Write-Host "====================================================" -ForegroundColor Cyan
    Write-Host "           DESINSTALAÇÃO DO CLOVER BOOT MANAGER     " -ForegroundColor Cyan
    Write-Host "====================================================" -ForegroundColor Cyan
    Write-Host
    
    Write-Host "Este processo irá remover o Clover Boot Manager e restaurar o bootloader original." -ForegroundColor Yellow
    Write-Host "AVISO: Esta operação pode deixar seu sistema não inicializável se não for executada corretamente." -ForegroundColor Red
    Write-Host
    
    $confirm = Read-Host "Tem certeza que deseja desinstalar o Clover? (S/N)"
    
    if ($confirm -eq "S" -or $confirm -eq "s") {
        Write-Host "Desinstalando Clover Boot Manager..." -ForegroundColor Yellow
        
        # Encontrar a partição EFI
        $efiVolume = $null
        $tempDriveCreated = $false
        
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
                        break
                    }
                } catch {
                    Write-Host "Erro ao acessar partição EFI: $_" -ForegroundColor Red
                }
            }
        }
        
        if (-not $efiVolume) {
            Write-Host "Não foi possível encontrar ou montar a partição EFI" -ForegroundColor Red
            Write-Host "Pressione qualquer tecla para continuar..." -ForegroundColor Yellow
            $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            Show-RecoveryMenu
            return
        }
        
        $efiPath = "${efiVolume.DriveLetter}:"
        
        # Verificar se o Clover está instalado
        if (-not (Test-Path "$efiPath\EFI\CLOVER")) {
            Write-Host "Clover não encontrado na partição EFI." -ForegroundColor Red
            
            # Limpar letra de unidade temporária se foi criada
            if ($tempDriveCreated) {
                $efiPartitions[0] | Remove-PartitionAccessPath -AccessPath "$efiPath"
                Write-Host "Removida letra de unidade temporária $($efiVolume.DriveLetter)" -ForegroundColor Yellow
            }
            
            Write-Host "Pressione qualquer tecla para continuar..." -ForegroundColor Yellow
            $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            Show-RecoveryMenu
            return
        }
        
        # Criar backup antes da desinstalação
        $backupName = "Pre_Clover_Uninstall_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
        $backupPath = "$env:USERPROFILE\Documents\Environment_Dev\EFI_Backups\$backupName"
        
        Write-Host "Criando backup da partição EFI antes da desinstalação..." -ForegroundColor Yellow
        New-Item -Path $backupPath -ItemType Directory -Force | Out-Null
        Copy-Item -Path "$efiPath\*" -Destination $backupPath -Recurse -Force
        
        # Restaurar bootloader original se existir
        $bootloaderRestored = $false
        if (Test-Path "$efiPath\EFI\BOOT\BOOTX64.efi.original") {
            Write-Host "Restaurando bootloader original..." -ForegroundColor Green
            Copy-Item -Path "$efiPath\EFI\BOOT\BOOTX64.efi.original" -Destination "$efiPath\EFI\BOOT\BOOTX64.efi" -Force
            $bootloaderRestored = $true
        }
        
        # Remover diretório do Clover
        Write-Host "Removendo diretório do Clover..." -ForegroundColor Yellow
        Remove-Item -Path "$efiPath\EFI\CLOVER" -Recurse -Force
        
        # Verificar se a desinstalação foi bem-sucedida
        if (-not (Test-Path "$efiPath\EFI\CLOVER")) {
            Write-Host "Clover Boot Manager desinstalado com sucesso!" -ForegroundColor Green
            
            if ($bootloaderRestored) {
                Write-Host "Bootloader original restaurado." -ForegroundColor Green
            } else {
                Write-Host "AVISO: Não foi possível restaurar o bootloader original." -ForegroundColor Red
                Write-Host "Você pode precisar reparar o bootloader do Windows." -ForegroundColor Red
            }
        } else {
            Write-Host "Falha ao remover o diretório do Clover." -ForegroundColor Red
        }
        
        # Limpar letra de unidade temporária se foi criada
        if ($tempDriveCreated) {
            $efiPartitions[0] | Remove-PartitionAccessPath -AccessPath "$efiPath"
            Write-Host "Removida letra de unidade temporária $($efiVolume.DriveLetter)" -ForegroundColor Yellow
        }
    } else {
        Write-Host "Operação cancelada pelo usuário." -ForegroundColor Yellow
    }
    
    Write-Host "Pressione qualquer tecla para continuar..." -ForegroundColor Yellow
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    Show-RecoveryMenu
}

# Ponto de entrada principal
if ($SafeMode -or (Test-SafeMode)) {
    Write-Host "Sistema detectado em modo seguro." -ForegroundColor Yellow
    Write-Host "Iniciando modo de recuperação do Clover Boot Manager..." -ForegroundColor Green
} else {
    Write-Host "Iniciando utilitário de recuperação do Clover Boot Manager..." -ForegroundColor Green
}

# Exibir menu de recuperação
Show-RecoveryMenu
