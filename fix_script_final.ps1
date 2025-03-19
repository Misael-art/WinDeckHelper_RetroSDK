# Script para corrigir erros de sintaxe finais no Windeckhelper.ps1

# Função para tratar blocos try-catch corretamente
function Add-MissingCatchBlocks {
    param (
        [string]$content
    )
    
    # Padrão para encontrar blocos try sem catch
    $tryPattern = 'try\s*\{(?:[^{}]|(?<open>\{)|(?<close-open>\}))+(?(open)(?!))\}'
    
    # Encontrar todas as correspondências
    $matches = [regex]::Matches($content, $tryPattern)
    
    # Para cada match, verificar se tem um catch e adicionar se necessário
    foreach ($match in $matches) {
        $tryBlock = $match.Value
        $pos = $match.Index + $match.Length
        
        # Verificar se já tem um catch
        $nextChar = $content.Substring($pos, [Math]::Min(20, $content.Length - $pos))
        if (-not $nextChar.TrimStart().StartsWith("catch")) {
            # Adicionar bloco catch
            $newTryBlock = $tryBlock + "`n    catch {`n        `$errorMsg = `$_.Exception.Message`n        Write-Error `"Erro: `$errorMsg`"`n    }"
            $content = $content.Substring(0, $match.Index) + $newTryBlock + $content.Substring($pos)
        }
    }
    
    return $content
}

# Restaurar do backup original
$backupFile = ".\Windeckhelper.ps1.bak"
if (Test-Path $backupFile) {
    Copy-Item $backupFile .\Windeckhelper_temp.ps1 -Force
    
    # Ler o conteúdo completo do arquivo
    $content = Get-Content -Path ".\Windeckhelper_temp.ps1" -Raw
    
    # 1. Corrigir problemas com caracteres especiais
    $content = $content -replace ' âœ"\$", ""', ' ✓$", ""'
    
    # 2. Corrigir problemas com Registry Keys
    $content = $content -replace "HKCU:\\", "HKCU:\"
    $content = $content -replace "HKLM:\\", "HKLM:\"
    
    # 3. Corrigir sintaxe incorreta
    $content = $content -replace "using Sytry", "try"
    $content = $content -replace "switch \(iRet\) = 2;", "switch (iRet) {"
    $content = $content -replace "int DMDO_270 = 3;", ""
    
    # 4. Corrigir os problemas de blocos try-catch
    $content = Add-MissingCatchBlocks -content $content
    
    # 5. Salvar o arquivo corrigido
    $content | Set-Content -Path ".\Windeckhelper_fixed.ps1" -Encoding UTF8
    
    Write-Host "Correções finais aplicadas e salvas em Windeckhelper_fixed.ps1" -ForegroundColor Green
} else {
    Write-Host "Arquivo de backup não encontrado!" -ForegroundColor Red
} 