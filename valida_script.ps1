# Script para validar a sintaxe do Windeckhelper.ps1

$scriptPath = ".\Windeckhelper.ps1"

try {
    # Tenta analisar o script sem executá-lo
    $null = [System.Management.Automation.PSParser]::Tokenize((Get-Content $scriptPath -Raw), [ref]$null)
    Write-Host "Script $scriptPath está correto sintaticamente." -ForegroundColor Green
} catch {
    Write-Host "Erro de sintaxe no script $scriptPath" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
} 