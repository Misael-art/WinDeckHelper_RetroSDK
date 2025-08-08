# Script de monitoramento detalhado para operações críticas
# Este script implementa um sistema de log específico para operações críticas

function Initialize-CriticalLogger {
    <#
    .SYNOPSIS
        Inicializa o sistema de log para operações críticas.
    .DESCRIPTION
        Cria o diretório de logs e inicializa o arquivo de log para operações críticas.
    .PARAMETER LogDirectory
        Diretório onde os logs serão armazenados.
    .OUTPUTS
        Retorna o caminho do arquivo de log.
    #>
    [CmdletBinding()]
    param (
        [Parameter(Mandatory=$false)]
        [string]$LogDirectory = "$env:USERPROFILE\Documents\Environment_Dev\Logs"
    )
    
    # Criar diretório de logs se não existir
    if (-not (Test-Path $LogDirectory)) {
        New-Item -Path $LogDirectory -ItemType Directory -Force | Out-Null
    }
    
    # Criar arquivo de log para operações críticas
    $logFile = Join-Path -Path $LogDirectory -ChildPath "critical_operations.log"
    
    # Adicionar cabeçalho ao arquivo de log se for novo
    if (-not (Test-Path $logFile)) {
        $header = @"
# Log de Operações Críticas do Environment Dev
# Iniciado em: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
# Este arquivo contém registros detalhados de operações críticas realizadas pelo Environment Dev
# Formato: [Timestamp] [Status] [Operação]: Detalhes

"@
        $header | Out-File -FilePath $logFile -Encoding utf8
    }
    
    return $logFile
}

function Write-CriticalOperation {
    <#
    .SYNOPSIS
        Registra uma operação crítica no log.
    .DESCRIPTION
        Registra uma operação crítica no log, incluindo timestamp, status e detalhes.
    .PARAMETER OperationName
        Nome da operação crítica.
    .PARAMETER Details
        Detalhes da operação.
    .PARAMETER Status
        Status da operação (STARTED, COMPLETED, FAILED, WARNING).
    .PARAMETER LogFile
        Caminho do arquivo de log.
    .OUTPUTS
        Nenhum.
    #>
    [CmdletBinding()]
    param (
        [Parameter(Mandatory=$true)]
        [string]$OperationName,
        
        [Parameter(Mandatory=$true)]
        [string]$Details,
        
        [Parameter(Mandatory=$false)]
        [ValidateSet("STARTED", "COMPLETED", "FAILED", "WARNING")]
        [string]$Status = "STARTED",
        
        [Parameter(Mandatory=$false)]
        [string]$LogFile = $null
    )
    
    # Se o arquivo de log não for fornecido, inicializar o logger
    if (-not $LogFile -or -not (Test-Path $LogFile)) {
        $LogFile = Initialize-CriticalLogger
    }
    
    # Formatar a entrada de log
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Status] [$OperationName]: $Details"
    
    # Escrever no arquivo de log
    $logEntry | Out-File -FilePath $LogFile -Encoding utf8 -Append
    
    # Exibir na tela com cores apropriadas
    $color = switch ($Status) {
        "STARTED" { "Yellow" }
        "COMPLETED" { "Green" }
        "FAILED" { "Red" }
        "WARNING" { "Magenta" }
        default { "White" }
    }
    
    Write-Host $logEntry -ForegroundColor $color
}

function Get-CriticalOperationsLog {
    <#
    .SYNOPSIS
        Obtém o conteúdo do log de operações críticas.
    .DESCRIPTION
        Obtém o conteúdo do log de operações críticas, opcionalmente filtrando por operação ou status.
    .PARAMETER LogFile
        Caminho do arquivo de log.
    .PARAMETER OperationName
        Nome da operação para filtrar.
    .PARAMETER Status
        Status da operação para filtrar.
    .PARAMETER Last
        Número de entradas mais recentes para retornar.
    .OUTPUTS
        Retorna as entradas do log.
    #>
    [CmdletBinding()]
    param (
        [Parameter(Mandatory=$false)]
        [string]$LogFile = $null,
        
        [Parameter(Mandatory=$false)]
        [string]$OperationName = $null,
        
        [Parameter(Mandatory=$false)]
        [ValidateSet("STARTED", "COMPLETED", "FAILED", "WARNING", $null)]
        [string]$Status = $null,
        
        [Parameter(Mandatory=$false)]
        [int]$Last = 0
    )
    
    # Se o arquivo de log não for fornecido, inicializar o logger
    if (-not $LogFile -or -not (Test-Path $LogFile)) {
        $LogFile = Initialize-CriticalLogger
    }
    
    # Verificar se o arquivo de log existe
    if (-not (Test-Path $LogFile)) {
        Write-Host "Arquivo de log não encontrado: $LogFile" -ForegroundColor Red
        return @()
    }
    
    # Ler o conteúdo do arquivo de log
    $logContent = Get-Content -Path $LogFile
    
    # Filtrar por operação, se especificado
    if ($OperationName) {
        $logContent = $logContent | Where-Object { $_ -match "\[$OperationName\]" }
    }
    
    # Filtrar por status, se especificado
    if ($Status) {
        $logContent = $logContent | Where-Object { $_ -match "\[$Status\]" }
    }
    
    # Retornar apenas as últimas entradas, se especificado
    if ($Last -gt 0 -and $logContent.Count -gt $Last) {
        $logContent = $logContent | Select-Object -Last $Last
    }
    
    return $logContent
}

function Monitor-CloverInstallation {
    <#
    .SYNOPSIS
        Monitora a instalação do Clover Boot Manager.
    .DESCRIPTION
        Monitora a instalação do Clover Boot Manager, registrando operações críticas e verificando o status.
    .PARAMETER InstallationScript
        Caminho do script de instalação do Clover.
    .PARAMETER LogFile
        Caminho do arquivo de log.
    .OUTPUTS
        Retorna um objeto com o resultado do monitoramento.
    #>
    [CmdletBinding()]
    param (
        [Parameter(Mandatory=$true)]
        [string]$InstallationScript,
        
        [Parameter(Mandatory=$false)]
        [string]$LogFile = $null
    )
    
    # Inicializar o logger se necessário
    if (-not $LogFile) {
        $LogFile = Initialize-CriticalLogger
    }
    
    # Verificar se o script de instalação existe
    if (-not (Test-Path $InstallationScript)) {
        Write-CriticalOperation -OperationName "CloverInstallation" -Details "Script de instalação não encontrado: $InstallationScript" -Status "FAILED" -LogFile $LogFile
        return @{
            Success = $false
            Details = "Script de instalação não encontrado: $InstallationScript"
        }
    }
    
    # Verificar compatibilidade de hardware
    Write-CriticalOperation -OperationName "CloverInstallation" -Details "Verificando compatibilidade de hardware" -Status "STARTED" -LogFile $LogFile
    
    # Importar script de verificação de compatibilidade
    $scriptPath = Split-Path -Parent $InstallationScript
    $hardwareCompatibilityPath = Join-Path -Path $scriptPath -ChildPath "hardware_compatibility.ps1"
    
    if (Test-Path $hardwareCompatibilityPath) {
        . $hardwareCompatibilityPath
        $compatibilityResult = Test-HardwareCompatibility
        
        if (-not $compatibilityResult.Compatible) {
            Write-CriticalOperation -OperationName "CloverInstallation" -Details "Hardware incompatível com o Clover Boot Manager: $($compatibilityResult.Issues -join ', ')" -Status "FAILED" -LogFile $LogFile
            return @{
                Success = $false
                Details = "Hardware incompatível com o Clover Boot Manager: $($compatibilityResult.Issues -join ', ')"
            }
        }
        
        Write-CriticalOperation -OperationName "CloverInstallation" -Details "Hardware compatível com o Clover Boot Manager" -Status "COMPLETED" -LogFile $LogFile
    } else {
        Write-CriticalOperation -OperationName "CloverInstallation" -Details "Não foi possível verificar compatibilidade de hardware: script não encontrado" -Status "WARNING" -LogFile $LogFile
    }
    
    # Criar backup da partição EFI antes da instalação
    Write-CriticalOperation -OperationName "CloverInstallation" -Details "Criando backup da partição EFI antes da instalação" -Status "STARTED" -LogFile $LogFile
    
    # Importar utilitários de backup da EFI
    $efiBackupUtilsPath = Join-Path -Path $scriptPath -ChildPath "efi_backup_utils.ps1"
    
    if (Test-Path $efiBackupUtilsPath) {
        . $efiBackupUtilsPath
        $backupName = "Pre_Clover_Install_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
        $backupResult = New-EfiBackup -BackupName $backupName
        
        if ($backupResult) {
            Write-CriticalOperation -OperationName "CloverInstallation" -Details "Backup da partição EFI criado com sucesso: $($backupResult.Path)" -Status "COMPLETED" -LogFile $LogFile
        } else {
            Write-CriticalOperation -OperationName "CloverInstallation" -Details "Falha ao criar backup da partição EFI" -Status "WARNING" -LogFile $LogFile
        }
    } else {
        Write-CriticalOperation -OperationName "CloverInstallation" -Details "Não foi possível criar backup da partição EFI: script não encontrado" -Status "WARNING" -LogFile $LogFile
    }
    
    # Iniciar instalação do Clover
    Write-CriticalOperation -OperationName "CloverInstallation" -Details "Iniciando instalação do Clover Boot Manager" -Status "STARTED" -LogFile $LogFile
    
    try {
        # Executar script de instalação
        $installOutput = & $InstallationScript 2>&1
        $installSuccess = $LASTEXITCODE -eq 0
        
        # Registrar saída da instalação
        $installOutputStr = $installOutput | Out-String
        Write-CriticalOperation -OperationName "CloverInstallation" -Details "Saída da instalação: $installOutputStr" -Status "COMPLETED" -LogFile $LogFile
        
        if ($installSuccess) {
            Write-CriticalOperation -OperationName "CloverInstallation" -Details "Instalação do Clover Boot Manager concluída com sucesso" -Status "COMPLETED" -LogFile $LogFile
        } else {
            Write-CriticalOperation -OperationName "CloverInstallation" -Details "Falha na instalação do Clover Boot Manager: código de saída $LASTEXITCODE" -Status "FAILED" -LogFile $LogFile
        }
    } catch {
        Write-CriticalOperation -OperationName "CloverInstallation" -Details "Erro ao executar script de instalação: $_" -Status "FAILED" -LogFile $LogFile
        $installSuccess = $false
    }
    
    # Verificar instalação
    if ($installSuccess) {
        Write-CriticalOperation -OperationName "CloverInstallation" -Details "Verificando instalação do Clover Boot Manager" -Status "STARTED" -LogFile $LogFile
        
        # Importar script de verificação do Clover
        $cloverVerificationPath = Join-Path -Path $scriptPath -ChildPath "clover_verification.ps1"
        
        if (Test-Path $cloverVerificationPath) {
            . $cloverVerificationPath
            $verificationResult = Test-CloverInstallation
            
            if ($verificationResult.Success) {
                Write-CriticalOperation -OperationName "CloverInstallation" -Details "Verificação da instalação do Clover Boot Manager concluída com sucesso" -Status "COMPLETED" -LogFile $LogFile
            } else {
                Write-CriticalOperation -OperationName "CloverInstallation" -Details "Falha na verificação da instalação do Clover Boot Manager: $($verificationResult.Details -join ', ')" -Status "FAILED" -LogFile $LogFile
                $installSuccess = $false
            }
        } else {
            Write-CriticalOperation -OperationName "CloverInstallation" -Details "Não foi possível verificar instalação do Clover Boot Manager: script não encontrado" -Status "WARNING" -LogFile $LogFile
        }
    }
    
    # Retornar resultado do monitoramento
    return @{
        Success = $installSuccess
        LogFile = $LogFile
    }
}

# Exportar funções
Export-ModuleMember -Function Initialize-CriticalLogger, Write-CriticalOperation, Get-CriticalOperationsLog, Monitor-CloverInstallation
