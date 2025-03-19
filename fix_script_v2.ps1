# Script para corrigir erros de sintaxe em Windeckhelper.ps1

# Lê o conteúdo do arquivo
$content = Get-Content -Path ".\Windeckhelper.ps1" -Raw

# 1. Corrige os caracteres especiais nas expressões regulares
$fixedContent = $content -replace ' âœ"\$", ""', ' ✓$", ""'

# 2. Corrige os blocos try-catch incompletos
$tryPatterns = @(
    @{
        Start = 1684
        Pattern = '(?s)(try\s*\{.*?Error\s*=\s*\$_\.Exception\.Message\s*\}\s*\}\s*\}\s*\}\s*\})'
        Replace = '$1 catch { $errorMsg = $_.Exception.Message; Write-Error "Erro ao processar: $errorMsg" }'
    },
    @{
        Start = 3060
        Pattern = '(?s)(try\s*\{.*?}\.Exception\.Message\s*Write-Host.*?-ForegroundColor\s+Red\s*\}\s*\})'
        Replace = '$1 catch { $errorMsg = $_.Exception.Message; Write-Error "Erro ao verificar nó: $errorMsg" }'
    },
    @{
        Start = 6123
        Pattern = '(?s)(try\s*\{.*?Error\s*=\s*\$_\.Exception\.Message\s*\}\s*\}\s*\}\s*\}\s*\})'
        Replace = '$1 catch { $errorMsg = $_.Exception.Message; Write-Error "Erro ao processar: $errorMsg" }'
    },
    @{
        Start = 7499
        Pattern = '(?s)(try\s*\{.*?}\.Exception\.Message\s*Write-Host.*?-ForegroundColor\s+Red\s*\}\s*\})'
        Replace = '$1 catch { $errorMsg = $_.Exception.Message; Write-Error "Erro ao verificar nó: $errorMsg" }'
    }
)

foreach ($pattern in $tryPatterns) {
    $fixedContent = $fixedContent -replace $pattern.Pattern, $pattern.Replace
}

# 3. Corrige o problema de parênteses ausentes
$fixedContent = $fixedContent -replace '\}\s*\}\s*\}\.Exception\.Message', '} catch { $errorMsg = $_.Exception.Message; Write-Error $errorMsg }'

# 4. Corrige as expressões regulares com caracteres especiais
$fixedContent = $fixedContent -replace '\$packageName\s*=\s*\$selectedNode\.Text\s*-replace\s*"\s*âœ"\$",\s*""', '$packageName = $selectedNode.Text -replace " ✓$", ""'

# Salva o conteúdo corrigido de volta para o arquivo
$fixedContent | Set-Content -Path ".\Windeckhelper_fixed.ps1" -Encoding UTF8

Write-Host "Correções aplicadas e salvas em Windeckhelper_fixed.ps1" -ForegroundColor Green 