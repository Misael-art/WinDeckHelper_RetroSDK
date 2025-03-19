# TesteInterface.ps1
# Testes automatizados para interface do WinDeckHelper
# Versão: 1.0.0

param(
    [switch]$Interactive,
    [switch]$NonInteractive,
    [switch]$GenerateReport
)

# Configuração
$ErrorActionPreference = "Stop"
$scriptPath = $PSScriptRoot
$logFile = Join-Path $scriptPath "logs\teste_interface.log"
$testReportPath = Join-Path $scriptPath "logs\teste_interface_report.html"
$mainScriptPath = Join-Path $scriptPath "Windeckhelper.ps1"

# Cria diretório de logs se não existir
if (-not (Test-Path (Split-Path $logFile -Parent))) {
    New-Item -ItemType Directory -Path (Split-Path $logFile -Parent) -Force | Out-Null
}

# Função para log
function Write-Log {
    param(
        [string]$Message,
        [ValidateSet("INFO", "WARNING", "ERROR", "SUCCESS", "TEST", "DEBUG")]
        [string]$Level = "INFO"
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level] $Message"
    
    Add-Content -Path $logFile -Value $logMessage -Encoding UTF8
    
    switch ($Level) {
        "INFO"    { Write-Host $logMessage -ForegroundColor Gray }
        "WARNING" { Write-Host $logMessage -ForegroundColor Yellow }
        "ERROR"   { Write-Host $logMessage -ForegroundColor Red }
        "SUCCESS" { Write-Host $logMessage -ForegroundColor Green }
        "TEST"    { Write-Host $logMessage -ForegroundColor Magenta }
        "DEBUG"   { Write-Host $logMessage -ForegroundColor Cyan }
    }
}

# Testes de verificação estática de script
function Test-ScriptStaticAnalysis {
    Write-Log "Iniciando análise estática do script principal..." -Level "TEST"
    
    $results = @{
        ScriptExists = $false
        SyntaxValid = $false
        TweakFunctionsFound = $false
        InterfaceNodesFound = $false
        CloverHandlerFound = $false
        TreeViewDefined = $false
    }
    
    # Verifica se o script existe
    if (Test-Path $mainScriptPath) {
        $results.ScriptExists = $true
        Write-Log "Script principal encontrado: $mainScriptPath" -Level "SUCCESS"
        
        try {
            # Verifica sintaxe
            $null = [System.Management.Automation.PSParser]::Tokenize((Get-Content $mainScriptPath -Raw), [ref]$null)
            $results.SyntaxValid = $true
            Write-Log "Análise sintática do script principal: VÁLIDO" -Level "SUCCESS"
            
            # Carrega o conteúdo do script para análise
            $content = Get-Content $mainScriptPath -Raw
            
            # Busca pela função Is-Tweak-Selected
            if ($content -match "function\s+Is-Tweak-Selected") {
                $results.TweakFunctionsFound = $true
                Write-Log "Função Is-Tweak-Selected encontrada no script" -Level "SUCCESS"
            } else {
                Write-Log "Função Is-Tweak-Selected NÃO encontrada no script" -Level "ERROR"
            }
            
            # Busca pelas definições de nós da TreeView
            if ($content -match "\$sync\.TweaksTree_Node_CloverBootloader\s*=") {
                $results.InterfaceNodesFound = $true
                Write-Log "Definição de nós da interface encontrada" -Level "SUCCESS"
            } else {
                Write-Log "Definição de nós da interface NÃO encontrada" -Level "ERROR"
            }
            
            # Busca pelo case de Clover Bootloader na função Apply-Tweaks
            if ($content -match "\""Clover Bootloader\""\s*\{") {
                $results.CloverHandlerFound = $true
                Write-Log "Manipulador de Clover Bootloader encontrado" -Level "SUCCESS"
            } else {
                Write-Log "Manipulador de Clover Bootloader NÃO encontrado" -Level "ERROR"
            }
            
            # Busca pela definição da TreeView
            if ($content -match "\$treeViewTweaks\s*=\s*New-Object\s+System\.Windows\.Forms\.TreeView") {
                $results.TreeViewDefined = $true
                Write-Log "Definição da TreeView encontrada" -Level "SUCCESS"
            } else {
                Write-Log "Definição da TreeView NÃO encontrada" -Level "ERROR"
            }
            
        } catch {
            Write-Log "Erro na análise do script: $($_.Exception.Message)" -Level "ERROR"
        }
    } else {
        Write-Log "Script principal não encontrado em: $mainScriptPath" -Level "ERROR"
    }
    
    return $results
}

# Verifica nós específicos da interface
function Get-InterfaceTestInstructions {
    $instructions = @"
====================================================
INSTRUÇÕES PARA TESTE MANUAL DA INTERFACE
====================================================

Execute os seguintes passos para testar a interface:

1. Inicie o WinDeckHelper usando launcher.ps1 ou Start.bat
2. Vá para a aba "Tweaks"
3. Verifique se o item "Clover Bootloader (Multi-boot)" existe
4. Marque apenas o Clover Bootloader
5. Clique no botão "Aplicar Tweaks"
6. Confirme se a instalação inicia ou se recebe mensagem de erro
7. Tire uma captura de tela do resultado

Diagnóstico para problemas:
- Se receber mensagem "Selecione pelo menos um item para instalar"
  mesmo com o item selecionado, há um problema de detecção de seleção.
- Verifique o log console para mensagens de diagnóstico adicionais.

Resultado esperado:
- Ao selecionar Clover Bootloader e clicar em Aplicar, 
  o script de instalação deve iniciar sem mensagens de erro.

"@

    return $instructions
}

# Gera relatório HTML
function Generate-TestReport {
    param(
        [hashtable]$TestResults
    )
    
    $reportHtml = @"
<!DOCTYPE html>
<html>
<head>
    <title>Relatório de Testes de Interface WinDeckHelper</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1, h2 { color: #0066cc; }
        .section { margin-bottom: 20px; border: 1px solid #ddd; padding: 10px; border-radius: 5px; }
        .success { color: green; }
        .warning { color: orange; }
        .error { color: red; }
        table { border-collapse: collapse; width: 100%; }
        th, td { text-align: left; padding: 8px; border-bottom: 1px solid #ddd; }
        th { background-color: #f2f2f2; }
        pre { background-color: #f8f8f8; padding: 10px; border-radius: 5px; overflow-x: auto; }
    </style>
</head>
<body>
    <h1>Relatório de Testes de Interface WinDeckHelper</h1>
    <p>Data: $(Get-Date -Format "dd/MM/yyyy HH:mm:ss")</p>

    <div class="section">
        <h2>Análise Estática do Script</h2>
        <table>
            <tr><th>Teste</th><th>Resultado</th></tr>
            <tr>
                <td>Script Principal Existe</td>
                <td class="$(if ($TestResults.Static.ScriptExists) { 'success' } else { 'error' })">
                    $(if ($TestResults.Static.ScriptExists) { 'PASSOU' } else { 'FALHOU' })
                </td>
            </tr>
            <tr>
                <td>Sintaxe Válida</td>
                <td class="$(if ($TestResults.Static.SyntaxValid) { 'success' } else { 'error' })">
                    $(if ($TestResults.Static.SyntaxValid) { 'PASSOU' } else { 'FALHOU' })
                </td>
            </tr>
            <tr>
                <td>Funções de Tweak Encontradas</td>
                <td class="$(if ($TestResults.Static.TweakFunctionsFound) { 'success' } else { 'error' })">
                    $(if ($TestResults.Static.TweakFunctionsFound) { 'PASSOU' } else { 'FALHOU' })
                </td>
            </tr>
            <tr>
                <td>Nós de Interface Encontrados</td>
                <td class="$(if ($TestResults.Static.InterfaceNodesFound) { 'success' } else { 'error' })">
                    $(if ($TestResults.Static.InterfaceNodesFound) { 'PASSOU' } else { 'FALHOU' })
                </td>
            </tr>
            <tr>
                <td>Manipulador de Clover Encontrado</td>
                <td class="$(if ($TestResults.Static.CloverHandlerFound) { 'success' } else { 'error' })">
                    $(if ($TestResults.Static.CloverHandlerFound) { 'PASSOU' } else { 'FALHOU' })
                </td>
            </tr>
            <tr>
                <td>TreeView Definida</td>
                <td class="$(if ($TestResults.Static.TreeViewDefined) { 'success' } else { 'error' })">
                    $(if ($TestResults.Static.TreeViewDefined) { 'PASSOU' } else { 'FALHOU' })
                </td>
            </tr>
        </table>
    </div>

    <div class="section">
        <h2>Instruções para Teste Manual</h2>
        <pre>$(Get-InterfaceTestInstructions)</pre>
    </div>

    <div class="section">
        <h2>Logs de Teste</h2>
        <pre>$(Get-Content $logFile -Tail 20 -ErrorAction SilentlyContinue | Out-String)</pre>
    </div>

    <div class="section">
        <h2>Recomendações</h2>
        <ul>
            <li>Execute o diagnóstico completo com <code>.\Diagnostico.ps1 -FullDiagnostic -GenerateReport</code></li>
            <li>Verifique se o script CloverBootloaderTweak.ps1 está presente e válido</li>
            <li>Teste a interface com privilégios de administrador</li>
            <li>Se o problema persistir, verifique os logs detalhados na pasta logs</li>
        </ul>
    </div>
</body>
</html>
"@

    $reportHtml | Out-File -FilePath $testReportPath -Encoding UTF8
    Write-Log "Relatório de testes gerado em: $testReportPath" -Level "SUCCESS"
    return $testReportPath
}

# Script Principal
function Start-InterfaceTesting {
    Write-Log "==== INICIANDO TESTES DE INTERFACE DO WINDECKHELPER ====" -Level "TEST"
    Write-Log "Data e hora: $(Get-Date -Format "dd/MM/yyyy HH:mm:ss")" -Level "INFO"
    
    $testResults = @{}
    
    # Análise estática
    Write-Log "Executando análise estática do script..." -Level "TEST"
    $testResults.Static = Test-ScriptStaticAnalysis
    
    # Verifica se a análise foi bem-sucedida
    $staticSuccess = $testResults.Static.ScriptExists -and 
                    $testResults.Static.SyntaxValid -and 
                    $testResults.Static.TweakFunctionsFound -and 
                    $testResults.Static.InterfaceNodesFound -and 
                    $testResults.Static.CloverHandlerFound
    
    if ($staticSuccess) {
        Write-Log "Análise estática concluída com sucesso" -Level "SUCCESS"
    } else {
        Write-Log "Análise estática identificou problemas" -Level "WARNING"
    }
    
    # Se for interativo, mostra instruções para o usuário
    if ($Interactive) {
        Write-Log "Iniciando teste interativo da interface..." -Level "TEST"
        $instructions = Get-InterfaceTestInstructions
        Write-Host "`n$instructions`n" -ForegroundColor Yellow
        
        Write-Host "Pressione qualquer tecla quando terminar o teste..." -ForegroundColor Cyan
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    }
    
    # Gera relatório se solicitado
    if ($GenerateReport) {
        $reportPath = Generate-TestReport -TestResults $testResults
        Write-Log "Relatório de testes gerado: $reportPath" -Level "SUCCESS"
        
        # Abre o relatório no navegador
        Start-Process $reportPath
    }
    
    Write-Log "==== TESTES DE INTERFACE CONCLUÍDOS ====" -Level "SUCCESS"
    return $testResults
}

# Executa testes com base nos parâmetros
if (-not ($Interactive -or $NonInteractive)) {
    # Se nenhum parâmetro for especificado, assume modo interativo
    $Interactive = $true
}

$testResults = Start-InterfaceTesting

# Exibe instruções finais
Write-Host "`nPara diagnóstico completo do sistema, execute:" -ForegroundColor Yellow
Write-Host ".\Diagnostico.ps1 -FullDiagnostic -GenerateReport" -ForegroundColor Cyan

# Retorna os resultados
return $testResults 