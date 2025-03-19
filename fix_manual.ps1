# Script para corrigir manualmente as linhas problemáticas

# Lendo todo o arquivo
$lines = Get-Content .\Windeckhelper.ps1

# Linhas problemáticas identificadas
$problematicLines = @{
    182 = $true; 634 = $true; 690 = $true; 870 = $true; 909 = $true;
    935 = $true; 966 = $true; 999 = $true; 1026 = $true; 1047 = $true
}

# Função para corrigir uma linha específica
function Fix-Line {
    param (
        [string]$line
    )
    
    # Corrigir o padrão "$_ catch { $errorMsg = ..." para "$_.Exception.Message"
    if ($line -match '\$_\s+catch\s*\{') {
        $line = $line -replace '\$_\s+catch\s*\{[^}]*\}', '$_.Exception.Message'
    }
    
    return $line
}

# Corrigindo cada linha
for ($i = 0; $i -lt $lines.Count; $i++) {
    $lineNumber = $i + 1
    
    # Se esta é uma das linhas problemáticas, corrigir
    if ($problematicLines.ContainsKey($lineNumber)) {
        $lines[$i] = Fix-Line -line $lines[$i]
        Write-Host "Corrigida linha $lineNumber" -ForegroundColor Green
    }
}

# Salvar de volta para o arquivo
$lines | Set-Content -Path ".\Windeckhelper_manual_fixed.ps1" -Encoding UTF8

Write-Host "Correção manual concluída. Arquivo salvo como Windeckhelper_manual_fixed.ps1" -ForegroundColor Green 