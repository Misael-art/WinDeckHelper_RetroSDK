# Script para corrigir erros de sintaxe em Windeckhelper.ps1

# Função para adicionar um bloco catch se necessário
function Add-CatchBlock {
    param(
        [string]$line,
        [ref]$inTryBlock,
        [ref]$tryBlockContent
    )
    
    if ($line -match "^[\s]*try[\s]*{") {
        $inTryBlock.Value = $true
        $tryBlockContent.Value = @($line)
        return $null
    }
    
    if ($inTryBlock.Value) {
        $tryBlockContent.Value += $line
        
        if ($line -match "^[\s]*}[\s]*$" -and -not ($line -match "catch|finally")) {
            $inTryBlock.Value = $false
            $fullBlock = $tryBlockContent.Value -join "`n"
            return $fullBlock + "`n    catch {`n        `$errorMsg = `$_.Exception.Message`n        Write-Error `"Erro: `$errorMsg`"`n    }"
        }
    }
    
    return $line
}

# Lê o arquivo linha por linha
$lines = Get-Content ".\Windeckhelper.ps1"
$newLines = @()
$inTryBlock = $false
$tryBlockContent = @()

foreach ($line in $lines) {
    # 1. Corrige os caracteres especiais nas expressões regulares
    $line = $line -replace ' âœ"\$", ""', ' ✓$", ""'
    
    # 2. Corrige o problema de parênteses ausentes
    $line = $line -replace '\.Exception\.Message(?!\s*=)', ' catch { $errorMsg = $_.Exception.Message; Write-Error $errorMsg }'
    
    # 3. Processa blocos try-catch
    $processedLine = Add-CatchBlock -line $line -inTryBlock ([ref]$inTryBlock) -tryBlockContent ([ref]$tryBlockContent)
    if ($processedLine) {
        $newLines += $processedLine
    }
}

# Salva o arquivo corrigido
$newLines | Set-Content -Path ".\Windeckhelper_fixed.ps1" -Encoding UTF8

Write-Host "Correções aplicadas e salvas em Windeckhelper_fixed.ps1" -ForegroundColor Green 