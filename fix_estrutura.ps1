# Script para corrigir problemas estruturais no Windeckhelper.ps1

# Lê o arquivo como um único bloco de texto para preservar a estrutura
$content = Get-Content -Path ".\Windeckhelper.ps1" -Raw

# 1. Corrige caracteres especiais nas expressões regulares
$content = $content -replace ' âœ"\$", ""', ' ✓$", ""'

# 2. Verifica e corrige blocos try sem catch
# Localiza a área específica da linha 843
$line843Pattern = '(?s)(try\s*\{[^{}]*?)(\}\s*\}\s*\}\s*function Test-ProgramInstalled)'
$content = $content -replace $line843Pattern, '$1}
    catch {
        $errorMsg = $_.Exception.Message
        Write-Error "Erro ao verificar programa: $errorMsg"
    }$2'

# 3. Corrige problemas na linha 2218-2223
$line2218Pattern = '(?s)(try\s*\{[^{}]*?)(\}\s*\}\s*\}$)'
$content = $content -replace $line2218Pattern, '$1}
    catch {
        $errorMsg = $_.Exception.Message
        Write-Error "Erro ao processar operação: $errorMsg"
    }$2'

# 4. Verifica se a função Is-Tweak-Selected está fechada corretamente na linha 758
# Isso requer uma análise mais cuidadosa do contexto
$functionPattern = '(?s)(function Is-Tweak-Selected\s*\{[^{]*?try\s*\{.*?)(\s*\}\s*\}\s*function)'
$content = $content -replace $functionPattern, '$1
    }
    catch {
        $errorMsg = $_.Exception.Message
        Write-Error "Erro em Is-Tweak-Selected: $errorMsg"
        return $false
    }$2'

# 5. Verifica se o bloco try global na linha 15 está fechado corretamente
# Este é um problema mais complexo que pode exigir uma análise manual

# Salva o conteúdo corrigido
$content | Set-Content -Path ".\Windeckhelper_estrutura_fixed.ps1" -Encoding UTF8

Write-Host "Correções estruturais aplicadas. Verifique Windeckhelper_estrutura_fixed.ps1" -ForegroundColor Green 