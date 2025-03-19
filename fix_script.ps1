# Script para corrigir erros de sintaxe em Windeckhelper.ps1

# Lê o conteúdo do arquivo
$content = Get-Content -Path ".\Windeckhelper.ps1" -Raw

# Corrige o primeiro erro (linha 843)
# Procura o padrão de Try sem Catch por volta da linha 824-843
$fixedContent = $content -replace '(?s)(try\s*\{\s*\$nodeText\s*=\s*\$node\.Text.*?)(\s*\}\s*\}\s*\}\s*function Test-ProgramInstalled)', '$1
                    catch {
                        $errorMsg = $_.Exception.Message
                        Write-Host "Erro ao verificar nó: $errorMsg" -ForegroundColor Red
                    }$2'

# Corrige o segundo erro (linha 2219)
# Procura o padrão de Try sem Catch por volta da linha 2152-2219
$fixedContent = $fixedContent -replace '(?s)(try\s*\{\s*\$success\s*=\s*\$false.*?)(\s*\}\s*\}\s*\}$)', '$1
                catch {
                    $errorMsg = $_.Exception.Message
                    Write-Host "Erro ao aplicar tweaks: $errorMsg" -ForegroundColor Red
                    [System.Windows.Forms.MessageBox]::Show("Erro ao aplicar tweaks: $errorMsg", "WinDeckHelper", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Error)
                }$2'

# Salva o conteúdo corrigido de volta para o arquivo
$fixedContent | Set-Content -Path ".\Windeckhelper_fixed.ps1" -Encoding UTF8

Write-Host "Correções aplicadas e salvas em Windeckhelper_fixed.ps1" -ForegroundColor Green 