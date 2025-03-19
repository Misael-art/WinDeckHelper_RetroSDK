# Script para corrigir erros de sintaxe em Windeckhelper.ps1

# Lê o arquivo linha por linha
$lines = Get-Content ".\Windeckhelper.ps1"
$newLines = @()
$inTryBlock = $false
$tryBlockContent = @()
$tryLevel = 0

foreach ($line in $lines) {
    $processedLine = $line

    # 1. Corrige a sintaxe incorreta "using Sytry"
    if ($line -match "using Sytry") {
        $processedLine = $line -replace "using Sytry", "try"
    }

    # 2. Corrige caracteres especiais nas expressões regulares
    $processedLine = $processedLine -replace ' âœ"\$", ""', ' ✓$", ""'
    
    # 3. Corrige problemas com blocos try
    if ($processedLine -match "^[\s]*try[\s]*{") {
        $tryLevel++
        $inTryBlock = $true
    }
    
    if ($inTryBlock -and $processedLine -match "^[\s]*}[\s]*$") {
        $tryLevel--
        if ($tryLevel -eq 0) {
            $inTryBlock = $false
            if (-not ($processedLine -match "catch|finally")) {
                $processedLine = "}`n    catch {`n        `$errorMsg = `$_.Exception.Message`n        Write-Error `"Erro: `$errorMsg`"`n    }"
            }
        }
    }

    # 4. Corrige problemas com switch/case
    $processedLine = $processedLine -replace "switch \(iRet\) = 2;", "switch (iRet) {"
    
    # 5. Remove linhas problemáticas
    if ($processedLine -match "int DMDO_270 = 3;") {
        continue
    }

    # 6. Corrige problemas com Registry Keys
    $processedLine = $processedLine -replace "HKCU:\\", "HKCU:\"
    $processedLine = $processedLine -replace "HKLM:\\", "HKLM:\"

    $newLines += $processedLine
}

# Salva o arquivo corrigido
$newLines | Set-Content -Path ".\Windeckhelper_fixed.ps1" -Encoding UTF8

Write-Host "Correções aplicadas e salvas em Windeckhelper_fixed.ps1" -ForegroundColor Green 