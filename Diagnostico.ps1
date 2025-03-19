# Script de Diagnóstico do WinDeckHelper
$ErrorActionPreference = "Continue"
$diagnosticoLog = Join-Path $PSScriptRoot "diagnostico.log"

function Write-Diagnostico {
    param(
        [string]$Mensagem,
        [string]$Status = "INFO"
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "$timestamp [$Status] $Mensagem"
    Add-Content -Path $diagnosticoLog -Value $logMessage
    
    switch ($Status) {
        "ERRO" { Write-Host $logMessage -ForegroundColor Red }
        "AVISO" { Write-Host $logMessage -ForegroundColor Yellow }
        "OK" { Write-Host $logMessage -ForegroundColor Green }
        default { Write-Host $logMessage }
    }
}

# Limpa log anterior
if (Test-Path $diagnosticoLog) {
    Remove-Item $diagnosticoLog -Force
}

Write-Diagnostico "Iniciando Diagnóstico do WinDeckHelper..."
Write-Diagnostico "----------------------------------------"

# Informações do Sistema
Write-Diagnostico "Sistema Operacional: $([System.Environment]::OSVersion.VersionString)"
Write-Diagnostico "Arquitetura: $([System.Environment]::Is64BitOperatingSystem)"
Write-Diagnostico "PowerShell Versão: $($PSVersionTable.PSVersion)"
Write-Diagnostico "Diretório de Trabalho: $PSScriptRoot"

# Verifica Privilégios
try {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    $isAdmin = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    Write-Diagnostico "Executando como Administrador: $isAdmin" -Status $(if ($isAdmin) { "OK" } else { "ERRO" })
} catch {
    Write-Diagnostico "Erro ao verificar privilégios: $_" -Status "ERRO"
}

# Verifica Arquivos
$arquivosNecessarios = @(
    "Windeckhelper.ps1",
    "launcher.ps1",
    "Start.bat"
)

foreach ($arquivo in $arquivosNecessarios) {
    $caminho = Join-Path $PSScriptRoot $arquivo
    $existe = Test-Path $caminho
    Write-Diagnostico "Arquivo $arquivo: $(if ($existe) { 'Encontrado' } else { 'Não encontrado' })" -Status $(if ($existe) { "OK" } else { "ERRO" })
}

# Verifica Assemblies
$assembliesNecessarios = @(
    "System.Windows.Forms",
    "System.Drawing",
    "PresentationFramework"
)

foreach ($assembly in $assembliesNecessarios) {
    try {
        Add-Type -AssemblyName $assembly
        Write-Diagnostico "Assembly $assembly: Carregado" -Status "OK"
    } catch {
        Write-Diagnostico "Assembly $assembly: Erro ao carregar - $_" -Status "ERRO"
    }
}

# Verifica Conexão
try {
    $testConnection = Test-NetConnection -ComputerName "8.8.8.8" -Port 443 -WarningAction SilentlyContinue
    Write-Diagnostico "Conexão com Internet: $($testConnection.TcpTestSucceeded)" -Status $(if ($testConnection.TcpTestSucceeded) { "OK" } else { "AVISO" })
} catch {
    Write-Diagnostico "Erro ao testar conexão: $_" -Status "AVISO"
}

# Verifica Política de Execução
$politica = Get-ExecutionPolicy
Write-Diagnostico "Política de Execução: $politica" -Status $(if ($politica -eq "Restricted") { "AVISO" } else { "OK" })

# Verifica Espaço em Disco
$drive = Split-Path $PSScriptRoot -Qualifier
$espaco = Get-PSDrive $drive.TrimEnd(':')
$espacoLivre = [math]::Round($espaco.Free / 1GB, 2)
Write-Diagnostico "Espaço Livre em Disco ($drive): ${espacoLivre}GB" -Status $(if ($espacoLivre -gt 10) { "OK" } else { "AVISO" })

Write-Diagnostico "----------------------------------------"
Write-Diagnostico "Diagnóstico Concluído!"
Write-Diagnostico "Se encontrou problemas, por favor:"
Write-Diagnostico "1. Tire um print desta tela"
Write-Diagnostico "2. Abra uma issue no GitHub"
Write-Diagnostico "3. Anexe o print e os arquivos de log"

Write-Host "`nPressione qualquer tecla para sair..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") 