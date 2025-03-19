# Configuração inicial
$ErrorActionPreference = "Stop"
$Host.UI.RawUI.WindowTitle = "WinDeckHelper Launcher"

# Função para logging
function Write-Log {
    param(
        [string]$Message,
        [string]$Level = "INFO"
    )
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] [$Level] $Message"
}

# Função para exibir mensagens
function Write-Header {
    Write-Host "`n========================================"
    Write-Host "         WinDeckHelper Launcher"
    Write-Host "========================================`n"
}

function Write-Step {
    param([string]$Message)
    Write-Host "- $Message"
}

# Função para verificar ambiente
function Test-Environment {
    try {
        # Verifica se está rodando como administrador
        $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
        if (-not $isAdmin) {
            throw "Este script precisa ser executado como Administrador"
        }
        Write-Step "Executando como Administrador: OK"

        # Verifica versão do PowerShell
        $psVersion = $PSVersionTable.PSVersion
        if ($psVersion.Major -lt 5) {
            throw "PowerShell 5.0 ou superior é necessário. Versão atual: $($psVersion.ToString())"
        }
        Write-Step "PowerShell encontrado: OK"

        # Verifica e cria diretório de logs
        $logPath = Join-Path $PSScriptRoot "logs"
        if (-not (Test-Path $logPath)) {
            New-Item -ItemType Directory -Path $logPath -Force | Out-Null
        }

        return $true
    }
    catch {
        Write-Host "`n========================================"
        Write-Host "             ERRO DETECTADO"
        Write-Host "========================================`n"
        Write-Host $_.Exception.Message
        return $false
    }
}

# Exibe cabeçalho
Write-Header

Write-Host "Verificando ambiente..."
if (-not (Test-Environment)) {
    exit 1
}

# Define o arquivo de log com timestamp
$timestamp = Get-Date -Format "yyyyMMddHHmmss"
$logFile = Join-Path $PSScriptRoot "logs\windeckhelper_$timestamp.log"

# Inicia transcrição
Start-Transcript -Path $logFile -Force

Write-Host "Iniciando WinDeckHelper..."

# Carrega o script principal
$mainScript = Join-Path $PSScriptRoot "Windeckhelper.ps1"
if (Test-Path $mainScript) {
    Write-Log "Carregando script principal..." "INFO"
    try {
        . $mainScript
        Write-Log "Script principal carregado com sucesso" "INFO"
    }
    catch {
        Write-Host "`n========================================"
        Write-Host "             ERRO DETECTADO"
        Write-Host "========================================`n"
        Write-Host "O WinDeckHelper encontrou um erro durante a execução."
        Write-Host "Detalhes do erro:"
        Write-Host $_.Exception.Message
        Write-Host "`nStack Trace:"
        Write-Host $_.ScriptStackTrace
        Write-Host "`nPressione qualquer tecla para ver o log de erros..."
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
        
        # Mostra o log
        if (Test-Path $logFile) {
            Get-Content $logFile | Write-Host
        }
        else {
            Write-Host "ERRO: Arquivo de log não encontrado!"
        }
        
        Write-Host "`nPara suporte, por favor:"
        Write-Host "1. Tire um print desta tela"
        Write-Host "2. Abra uma issue no GitHub"
        Write-Host "3. Anexe o print e o arquivo de log"
    }
}

Stop-Transcript
pause