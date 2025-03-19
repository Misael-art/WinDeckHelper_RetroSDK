# Diagnostico.ps1
# Script para diagnóstico do WinDeckHelper
# Versão: 1.1.0

param(
    [switch]$FullDiagnostic,
    [switch]$InterfaceOnly,
    [switch]$SystemCheck,
    [switch]$GenerateReport
)

# Configuração
$ErrorActionPreference = "Stop"
$VerbosePreference = "Continue"
$scriptPath = $PSScriptRoot
$logFile = Join-Path $scriptPath "logs\diagnostico.log"
$mainScript = Join-Path $scriptPath "Windeckhelper.ps1"
$cloverScript = Join-Path $scriptPath "CloverBootloaderTweak.ps1"
$reportPath = Join-Path $scriptPath "logs\diagnostic_report.html"

# Cria diretório de logs se não existir
if (-not (Test-Path (Split-Path $logFile -Parent))) {
    New-Item -ItemType Directory -Path (Split-Path $logFile -Parent) -Force | Out-Null
}

# Função para log
function Write-Log {
    param(
        [string]$Message,
        [ValidateSet("INFO", "WARNING", "ERROR", "SUCCESS", "DEBUG")]
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
        "DEBUG"   { Write-Host $logMessage -ForegroundColor Cyan }
    }
}

function Test-AdminPrivileges {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    $isAdmin = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    
    if ($isAdmin) {
        Write-Log "Executando com privilégios de administrador" -Level "SUCCESS"
    } else {
        Write-Log "ATENÇÃO: Não está executando como administrador - algumas verificações podem falhar" -Level "WARNING"
    }
    
    return $isAdmin
}

function Test-ScriptIntegrity {
    $scripts = @{
        "WinDeckHelper" = $mainScript
        "CloverBootloader" = $cloverScript
    }
    
    $results = @{}
    
    foreach ($script in $scripts.GetEnumerator()) {
        $scriptName = $script.Key
        $scriptPath = $script.Value
        
        if (Test-Path $scriptPath) {
            try {
                $syntaxCheck = [System.Management.Automation.PSParser]::Tokenize((Get-Content $scriptPath -Raw), [ref]$null)
                $results[$scriptName] = @{
                    "Exists" = $true
                    "SyntaxValid" = $true
                    "Size" = (Get-Item $scriptPath).Length
                    "LastModified" = (Get-Item $scriptPath).LastWriteTime
                }
                Write-Log "Script $scriptName: válido sintaticamente" -Level "SUCCESS"
            } catch {
                $results[$scriptName] = @{
                    "Exists" = $true
                    "SyntaxValid" = $false
                    "Error" = $_.Exception.Message
                }
                Write-Log "Script ${scriptName}: erro de sintaxe detectado: $($_.Exception.Message)" -Level "ERROR"
            }
        } else {
            $results[$scriptName] = @{
                "Exists" = $false
            }
            Write-Log "Script ${scriptName}: não encontrado em $scriptPath" -Level "ERROR"
        }
    }
    
    return $results
}

function Test-InterfaceComponents {
    Write-Log "Iniciando verificação de componentes da interface..." -Level "INFO"
    
    # Esta função será executada quando o script principal for carregado
    # para verificar os componentes da interface
    $testFunction = @'
function Test-Interface {
    $results = @{}
    
    # Verifica objetos de sincronização
    if ($null -eq $sync) {
        $results["SyncObject"] = "FALHA: Objeto de sincronização não encontrado"
    } else {
        $results["SyncObject"] = "OK"
        
        # Verifica nós da árvore de tweaks
        $tweakNodes = @(
            "TweaksTree_Node_GameBar",
            "TweaksTree_Node_LoginSleep", 
            "TweaksTree_Node_ShowKeyboard",
            "TweaksTree_Node_CloverBootloader"
        )
        
        foreach ($nodeName in $tweakNodes) {
            $node = $sync.$nodeName
            if ($null -eq $node) {
                $results[$nodeName] = "FALHA: Nó não encontrado"
            } else {
                try {
                    $isChecked = $node.Checked
                    $nodeText = $node.Text
                    $results[$nodeName] = "OK: '$nodeText', Selecionado: $isChecked"
                } catch {
                    $results[$nodeName] = "ERRO: $($_.Exception.Message)"
                }
            }
        }
        
        # Verifica funções críticas
        $functions = @(
            "Is-Tweak-Selected",
            "Apply-Tweaks"
        )
        
        foreach ($funcName in $functions) {
            if (Get-Command $funcName -ErrorAction SilentlyContinue) {
                $results["Function_$funcName"] = "OK: Função encontrada"
            } else {
                $results["Function_$funcName"] = "FALHA: Função não encontrada"
            }
        }
    }
    
    return $results
}
'@
    
    # Como não podemos executar diretamente o teste da interface sem carregar toda a UI,
    # vamos apenas verificar o script principal para garantir que ele existe e é válido
    if (Test-Path $mainScript) {
        Write-Log "Script principal encontrado. A verificação da interface requer execução interativa." -Level "INFO"
        Write-Log "Para verificar a interface, execute o WinDeckHelper e use o menu de diagnóstico." -Level "INFO"
        
        # Analisando o script para encontrar nós da interface
        $content = Get-Content $mainScript -Raw
        
        $treeNodePattern = '\$sync\.TweaksTree_Node_\w+\s*='
        $treeNodes = [regex]::Matches($content, $treeNodePattern)
        
        Write-Log "Nós de árvore detectados no script: $($treeNodes.Count)" -Level "INFO"
        foreach ($node in $treeNodes) {
            Write-Log "Nó detectado: $($node.Value)" -Level "DEBUG"
        }
        
        return @{
            "ScriptValid" = $true
            "NodesDetected" = $treeNodes.Count
            "TestFunction" = $testFunction
        }
    } else {
        Write-Log "Script principal não encontrado em $mainScript" -Level "ERROR"
        return @{
            "ScriptValid" = $false
        }
    }
}

function Test-SystemRequirements {
    Write-Log "Verificando requisitos do sistema..." -Level "INFO"
    
    $results = @{}
    
    # Verifica versão do PowerShell
    $psVersion = $PSVersionTable.PSVersion
    $results["PowerShell"] = "Versão: $psVersion"
    Write-Log "PowerShell versão: $psVersion" -Level "INFO"
    
    # Verifica espaço em disco
    $systemDrive = (Get-Item $env:SystemDrive)
    $freeSpace = [math]::Round(($systemDrive.Root.FreeSpace / 1GB), 2)
    $results["FreeSpace"] = "$freeSpace GB"
    
    if ($freeSpace -lt 5) {
        Write-Log "ALERTA: Espaço livre em disco baixo: $freeSpace GB" -Level "WARNING"
    } else {
        Write-Log "Espaço livre em disco: $freeSpace GB" -Level "SUCCESS"
    }
    
    # Verifica política de execução
    $executionPolicy = Get-ExecutionPolicy
    $results["ExecutionPolicy"] = $executionPolicy.ToString()
    
    if ($executionPolicy -eq "Restricted") {
        Write-Log "ALERTA: Política de execução restritiva pode impedir scripts" -Level "WARNING"
    } else {
        Write-Log "Política de execução: $executionPolicy" -Level "INFO"
    }
    
    # Verifica .NET Framework
    $dotNetVersion = (Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\NET Framework Setup\NDP\v4\Full").Release
    if ($dotNetVersion -ge 461808) {
        $dotNetVersionStr = "4.7.2 ou superior"
        Write-Log ".NET Framework: $dotNetVersionStr" -Level "SUCCESS"
    } else {
        $dotNetVersionStr = "Inferior a 4.7.2"
        Write-Log "ALERTA: .NET Framework desatualizado: $dotNetVersionStr" -Level "WARNING"
    }
    $results["DotNET"] = $dotNetVersionStr
    
    return $results
}

function Generate-DiagnosticReport {
    param(
        [hashtable]$Data
    )
    
    $reportHtml = @"
<!DOCTYPE html>
<html>
<head>
    <title>Relatório de Diagnóstico WinDeckHelper</title>
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
    </style>
</head>
<body>
    <h1>Relatório de Diagnóstico WinDeckHelper</h1>
    <p>Data: $(Get-Date -Format "dd/MM/yyyy HH:mm:ss")</p>

    <div class="section">
        <h2>Informações do Sistema</h2>
        <table>
            <tr><th>Item</th><th>Valor</th></tr>
"@

    foreach ($item in $Data.System.GetEnumerator()) {
        $reportHtml += "<tr><td>$($item.Key)</td><td>$($item.Value)</td></tr>`n"
    }

    $reportHtml += @"
        </table>
    </div>

    <div class="section">
        <h2>Integridade dos Scripts</h2>
        <table>
            <tr><th>Script</th><th>Status</th><th>Detalhes</th></tr>
"@

    foreach ($script in $Data.ScriptIntegrity.GetEnumerator()) {
        $scriptName = $script.Key
        $details = $script.Value
        
        if ($details.Exists -and $details.SyntaxValid) {
            $status = "<span class='success'>OK</span>"
            $detailText = "Tamanho: $([math]::Round($details.Size / 1KB, 2)) KB, Modificado: $($details.LastModified)"
        } elseif ($details.Exists -and -not $details.SyntaxValid) {
            $status = "<span class='error'>Erro de Sintaxe</span>"
            $detailText = $details.Error
        } else {
            $status = "<span class='error'>Não Encontrado</span>"
            $detailText = ""
        }
        
        $reportHtml += "<tr><td>$scriptName</td><td>$status</td><td>$detailText</td></tr>`n"
    }

    $reportHtml += @"
        </table>
    </div>

    <div class="section">
        <h2>Interface (Detecção Estática)</h2>
        <p>Nós detectados: $($Data.Interface.NodesDetected)</p>
        <p>Validade do script: $($Data.Interface.ScriptValid)</p>
        <p><i>Nota: Para diagnóstico completo da interface, execute o WinDeckHelper com o modo de diagnóstico interativo.</i></p>
    </div>

    <div class="section">
        <h2>Registros de Log</h2>
        <pre>$(Get-Content $logFile -Tail 20 -ErrorAction SilentlyContinue | Out-String)</pre>
    </div>
</body>
</html>
"@

    $reportHtml | Out-File -FilePath $reportPath -Encoding UTF8
    Write-Log "Relatório de diagnóstico gerado em: $reportPath" -Level "SUCCESS"
    return $reportPath
}

# Função principal
function Start-Diagnostic {
    Write-Log "==== INICIANDO DIAGNÓSTICO DO WINDECKHELPER ====" -Level "INFO"
    Write-Log "Data e hora: $(Get-Date -Format "dd/MM/yyyy HH:mm:ss")" -Level "INFO"
    Write-Log "Diretório do script: $scriptPath" -Level "INFO"
    
    # Verifica privilégios
    $isAdmin = Test-AdminPrivileges
    
    $diagnosticData = @{}
    
    # Verifica integridade dos scripts
    Write-Log "Verificando integridade dos scripts..." -Level "INFO"
    $diagnosticData.ScriptIntegrity = Test-ScriptIntegrity
    
    # Verifica componentes da interface (se solicitado)
    if ($FullDiagnostic -or $InterfaceOnly) {
        Write-Log "Verificando componentes da interface..." -Level "INFO"
        $diagnosticData.Interface = Test-InterfaceComponents
    }
    
    # Verifica requisitos do sistema (se solicitado)
    if ($FullDiagnostic -or $SystemCheck) {
        Write-Log "Verificando requisitos do sistema..." -Level "INFO"
        $diagnosticData.System = Test-SystemRequirements
    }
    
    # Gera relatório se solicitado
    if ($GenerateReport) {
        $reportFile = Generate-DiagnosticReport -Data $diagnosticData
        Write-Log "Para visualizar o relatório completo, abra: $reportFile" -Level "SUCCESS"
    }
    
    Write-Log "==== DIAGNÓSTICO CONCLUÍDO ====" -Level "SUCCESS"
    
    return $diagnosticData
}

# Inicia o diagnóstico com base nos parâmetros
if (-not ($FullDiagnostic -or $InterfaceOnly -or $SystemCheck)) {
    # Se nenhum parâmetro for especificado, faz diagnóstico completo
    $FullDiagnostic = $true
}

$results = Start-Diagnostic

# Exibe instruções finais
Write-Host ""
Write-Host "Para testar os componentes da interface interativamente, abra o WinDeckHelper e use as ferramentas de diagnóstico incluídas." -ForegroundColor Yellow
Write-Host "Log de diagnóstico salvo em: $logFile" -ForegroundColor Yellow

if ($GenerateReport) {
    # Abre o relatório no navegador padrão
    Start-Process $reportPath
}

return $results 