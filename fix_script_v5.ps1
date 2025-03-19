# Script para corrigir erros de sintaxe em Windeckhelper.ps1

# Vamos restaurar o backup original e corrigir novamente
Copy-Item .\Windeckhelper.ps1.bak .\Windeckhelper_temp.ps1 -Force

# Lê o arquivo linha por linha
$lines = Get-Content ".\Windeckhelper_temp.ps1"
$newLines = @()

# Processa o arquivo linha por linha
for ($i = 0; $i -lt $lines.Count; $i++) {
    $line = $lines[$i]
    $processedLine = $line

    # 1. Corrige a sintaxe incorreta "using Sytry"
    if ($line -match "using Sytry") {
        $processedLine = $line -replace "using Sytry", "try"
    }

    # 2. Corrige caracteres especiais nas expressões regulares
    $processedLine = $processedLine -replace ' âœ"\$", ""', ' ✓$", ""'
    
    # 3. Corrige problemas com switch/case
    $processedLine = $processedLine -replace "switch \(iRet\) = 2;", "switch (iRet) {"
    
    # 4. Remove linhas problemáticas
    if ($processedLine -match "int DMDO_270 = 3;") {
        continue
    }

    # 5. Corrige problemas com Registry Keys
    $processedLine = $processedLine -replace "HKCU:\\", "HKCU:\"
    $processedLine = $processedLine -replace "HKLM:\\", "HKLM:\"
    
    # 6. Adiciona o $newLines ao array
    $newLines += $processedLine
}

# Processamento especial para blocos try sem catch
$content = $newLines -join "`n"

# 7. Corrige erros específicos (baseado nas mensagens de erro)
$content = $content -replace '(?s)(try\s*\{.*?)(\}\s*\}\s*\}\s*function)', '$1
    catch {
        $errorMsg = $_.Exception.Message
        Write-Error "Erro: $errorMsg"
    }
$2'

# Corrige os blocos try nas áreas problemáticas
$lineNumbers = @(182, 634, 690, 870, 909, 935, 966, 999, 1026, 1047)
foreach ($lineNumber in $lineNumbers) {
    # Encontra o bloco try-catch correspondente e corrige
    $pattern = "try\s*\{(?:[^{}]|(?<open>\{)|(?<close-open>\}))+(?(open)(?!))\}"
    $regex = [regex]$pattern
    
    # Divide o conteúdo em linhas para processamento
    $contentLines = $content -split "`n"
    
    # Verifica se há linhas suficientes para acessar a linha especificada
    if ($lineNumber -le $contentLines.Length) {
        # Obtém a linha específica e algumas linhas antes e depois para contexto
        $startLine = [Math]::Max(0, $lineNumber - 10)
        $endLine = [Math]::Min($contentLines.Length - 1, $lineNumber + 10)
        $context = $contentLines[$startLine..$endLine] -join "`n"
        
        # Substitui apenas o catch incorreto nesse contexto
        $fixedContext = $context -replace '\$_\s+catch\s*\{[^{}]*\}', '$_.Exception.Message'
        
        # Substitui o contexto no conteúdo completo
        $content = $content.Replace($context, $fixedContext)
    }
}

# Salva o arquivo corrigido
$content | Set-Content -Path ".\Windeckhelper_fixed.ps1" -Encoding UTF8

Write-Host "Correções aplicadas e salvas em Windeckhelper_fixed.ps1" -ForegroundColor Green 