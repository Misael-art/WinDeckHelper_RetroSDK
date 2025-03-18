# Habilita logs detalhados
$ErrorActionPreference = "Stop"
$VerbosePreference = "Continue"

# Inicia o log
Start-Transcript -Path "$PSScriptRoot\windeckhelper.log" -Append

try {
    Write-Verbose "Iniciando launcher do WinDeckHelper..."
    
    # Verifica se está rodando como administrador
    $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    if (-not $isAdmin) {
        throw "Este script precisa ser executado como administrador!"
    }
    Write-Verbose "Verificação de administrador: OK"

    # Verifica se o arquivo principal existe
    $mainScript = Join-Path $PSScriptRoot "Windeckhelper.ps1"
    if (-not (Test-Path $mainScript)) {
        throw "Arquivo Windeckhelper.ps1 não encontrado!"
    }
    Write-Verbose "Arquivo principal encontrado: $mainScript"

    # Carrega e executa o script principal
    Write-Verbose "Carregando script principal..."
    . $mainScript
    Write-Verbose "Script principal carregado com sucesso"

} catch {
    Write-Error "Erro durante a execução: $_"
    Add-Type -AssemblyName PresentationFramework
    [System.Windows.Forms.MessageBox]::Show("Erro durante a execução: $_`n`nVerifique o arquivo de log para mais detalhes.", "WinDeckHelper Error")
} finally {
    Stop-Transcript
} 