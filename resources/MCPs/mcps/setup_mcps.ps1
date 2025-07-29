<#
.SYNOPSIS
    Instala dependências, compila e configura servidores MCP locais e remotos
    para diversas ferramentas de IA (Roo, Cline, Cursor, etc.).

.DESCRIPTION
    Este script automatiza o processo de configuração de servidores MCP:
    1. Verifica pré-requisitos (Node, npm/pnpm, Python, uv, Git).
    2. Lê chaves de API de 'mcp_api_keys.env'.
    3. Instala dependências (npm/pnpm/uv) para MCPs locais em C:\MCPs Servers.
    4. Compila projetos Node.js/TypeScript locais.
    5. Gera um arquivo mcp_settings.json combinado com configurações locais e remotas.
    6. Injeta chaves de API lidas no mcp_settings.json (preferencialmente via 'env').
    7. Detecta automaticamente os locais de configuração para Roo/Cline, Cursor, etc.
    8. Faz backup e atualiza o mcp_settings.json nesses locais.

.NOTES
    Autor: Roo
    Versão: 1.0
    Requer execução como Administrador se os locais de configuração exigirem.
    Certifique-se de que 'mcp_api_keys.env' existe e está preenchido corretamente
    antes de executar este script.
#>

# --- Configuração Inicial ---
$ErrorActionPreference = "Stop" # Para a execução em caso de erro não tratado
$ProgressPreference = 'SilentlyContinue' # Evita barras de progresso de comandos como Invoke-WebRequest

# Diretório alvo onde os MCPs serão instalados e configurados
$targetMcpBaseDir = "C:\MCPs Servers"
# Diretório onde o script está sendo executado
$scriptDir = $PSScriptRoot
# Caminho esperado para os fontes no pacote portátil
$portableSourcesDir = Join-Path $scriptDir "MCP_Sources"
# Arquivo de chaves de API (procurado no diretório alvo)
$apiKeyEnvFile = Join-Path $targetMcpBaseDir "mcp_api_keys.env"
# Arquivo de exemplo de chaves (procurado no diretório do script)
$apiKeyEnvExampleFile = Join-Path $scriptDir "mcp_api_keys.env.example"

# --- Funções Auxiliares ---

function Write-Log {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Message,
        [ValidateSet("INFO", "WARN", "ERROR")]
        [string]$Level = "INFO"
    )
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logLine = "[$timestamp] [$Level] $Message"
    Write-Host $logLine
    # Futuramente, pode adicionar escrita para um arquivo de log também
    # Add-Content -Path "setup_mcps.log" -Value $logLine
}

function Test-CommandExists {
    param([string]$Command)
    return [bool](Get-Command $Command -ErrorAction SilentlyContinue)
}

function Read-EnvFile {
    param([string]$FilePath)
    $envVars = @{}
    if (Test-Path $FilePath) {
        Get-Content $FilePath | ForEach-Object {
            $line = $_.Trim()
            # Ignora comentários e linhas vazias
            if ($line -and $line -notmatch '^\s*#') {
                $parts = $line -split '=', 2
                if ($parts.Length -eq 2) {
                    $key = $parts[0].Trim()
                    $value = $parts[1].Trim().Trim('"') # Remove aspas extras
                    $envVars[$key] = $value
                }
            }
        }
    }
    return $envVars
}

# --- 1. Cópia dos Fontes (se executando do pacote portátil) ---
if ($scriptDir -ne $targetMcpBaseDir -and (Test-Path $portableSourcesDir -PathType Container)) {
    Write-Log "Executando a partir do pacote portátil. Copiando fontes para '$targetMcpBaseDir'..."
    try {
        # Cria o diretório alvo se não existir
        if (-not (Test-Path $targetMcpBaseDir -PathType Container)) {
            Write-Log "Criando diretório alvo: $targetMcpBaseDir"
            New-Item -ItemType Directory -Path $targetMcpBaseDir -Force | Out-Null
        }
        # Copia o conteúdo da pasta MCP_Sources
        Write-Log "Copiando de '$portableSourcesDir' para '$targetMcpBaseDir'..."
        # Exclui node_modules, dist, build, .venv para evitar copiar dependências/artefatos desnecessários
        Get-ChildItem -Path $portableSourcesDir -Directory | ForEach-Object {
            $sourceSubDir = $_.FullName
            $targetSubDir = Join-Path $targetMcpBaseDir $_.Name
            Write-Log "  Copiando '$($_.Name)'..."
            Copy-Item -Path $sourceSubDir -Destination $targetSubDir -Recurse -Force -Exclude "node_modules", "dist", "build", ".venv"
        }
        Write-Log "Cópia dos fontes concluída."
    } catch {
        Write-Log "Erro ao copiar fontes do pacote para '$targetMcpBaseDir': $($_.Exception.Message)" -Level ERROR
        exit 1
    }
} elseif ($scriptDir -ne $targetMcpBaseDir) {
     Write-Log "AVISO: Script executado de '$scriptDir', mas a pasta 'MCP_Sources' não foi encontrada. Operando sobre '$targetMcpBaseDir'." -Level WARN
} else {
     Write-Log "Executando diretamente no diretório alvo: '$targetMcpBaseDir'."
}

# --- 2. Verificação de Pré-requisitos ---
Write-Log "Iniciando verificação de pré-requisitos..."
$prereqsMet = $true

if (-not (Test-CommandExists "node")) { Write-Log "Node.js não encontrado. Por favor, instale-o." -Level ERROR; $prereqsMet = $false }
if (-not (Test-CommandExists "npm")) { Write-Log "npm não encontrado. Por favor, instale Node.js (que inclui npm)." -Level ERROR; $prereqsMet = $false }
# pnpm é opcional para alguns projetos, mas verificamos
if (-not (Test-CommandExists "pnpm")) { Write-Log "pnpm não encontrado. Alguns MCPs podem precisar dele. Considere instalar: npm install -g pnpm" -Level WARN }
if (-not (Test-CommandExists "python")) { Write-Log "Python não encontrado. Por favor, instale Python 3.10+." -Level ERROR; $prereqsMet = $false } # Idealmente verificar versão
if (-not (Test-CommandExists "uv")) {
    Write-Log "uv (Python package manager) não encontrado. Tentando instalar via pip..." -Level WARN
    try {
        pip install uv --user # Instala no diretório do usuário
        # Tenta adicionar o diretório de scripts do usuário ao PATH da sessão atual
        $userScriptsPath = Join-Path $env:APPDATA "Python\Scripts" # Caminho comum no Windows
        if (Test-Path $userScriptsPath -PathType Container -ErrorAction SilentlyContinue) {
             Write-Log "Adicionando $userScriptsPath ao PATH da sessão..." -Level INFO
             $env:Path += ";$userScriptsPath"
             # Verifica novamente se uv agora é encontrado
             if (-not (Test-CommandExists "uv")) {
                 Write-Log "uv ainda não encontrado no PATH após adição. Pode ser necessário reiniciar o terminal/VSCode." -Level WARN
             }
        } else {
             Write-Log "Diretório de scripts do usuário Python não encontrado em $userScriptsPath. Verifique a instalação do Python." -Level WARN
        }
    } catch {
        Write-Log "Falha ao instalar uv via pip. Por favor, instale manualmente: https://docs.astral.sh/uv/getting-started/installation/" -Level ERROR
        $prereqsMet = $false
    }
}
if (-not (Test-CommandExists "git")) { Write-Log "Git não encontrado. Por favor, instale-o." -Level ERROR; $prereqsMet = $false }
if (-not (Test-CommandExists "bun")) { Write-Log "Bun não encontrado. O MCP 'mcp-youtube' pode não funcionar corretamente. Considere instalar: npm install -g bun" -Level WARN }

# Verifica o diretório alvo
if (-not (Test-Path $targetMcpBaseDir -PathType Container)) {
    Write-Log "Diretório alvo dos MCPs não encontrado ou não criado: $targetMcpBaseDir" -Level ERROR
    # Não define $prereqsMet = $false aqui, pois a cópia pode ter falhado antes
    # A falha na cópia já terá saído do script
}

if (-not $prereqsMet) {
    Write-Log "Pré-requisitos não atendidos. Abortando script." -Level ERROR
    exit 1
}
Write-Log "Pré-requisitos verificados com sucesso."

# --- 3. Gerenciamento de Chaves de API ---
Write-Log "Verificando arquivo de chaves de API em '$targetMcpBaseDir'..."
if (-not (Test-Path $apiKeyEnvFile)) {
    Write-Log "Arquivo '$apiKeyEnvFile' não encontrado no diretório alvo." -Level WARN
    if (Test-Path $apiKeyEnvExampleFile) {
        Write-Log "Um arquivo de exemplo '$apiKeyEnvExampleFile' foi encontrado no diretório do script." -Level INFO
        Write-Log "Por favor, copie '$($apiKeyEnvExampleFile.Split('\')[-1])' para '$targetMcpBaseDir'," -Level INFO
        Write-Log "renomeie-o para '$($apiKeyEnvFile.Split('\')[-1])' e preencha as chaves necessárias." -Level INFO
    } else {
        Write-Log "Arquivo de exemplo '$apiKeyEnvExampleFile' também não encontrado no diretório do script. Não é possível continuar sem as chaves." -Level ERROR
    }
    exit 1
}

Write-Log "Lendo chaves de API de '$apiKeyEnvFile'..."
$apiKeys = Read-EnvFile -FilePath $apiKeyEnvFile
if ($apiKeys.Count -eq 0) {
    Write-Log "Nenhuma chave de API encontrada ou o arquivo está vazio/mal formatado em '$apiKeyEnvFile'." -Level WARN
    # Continuar mesmo assim, mas alguns MCPs podem não funcionar
} else {
    Write-Log "Chaves de API lidas com sucesso."
}

# --- 4. Instalação de Dependências e Build (MCPs Locais no Diretório Alvo) ---
Write-Log "Iniciando instalação de dependências e build para MCPs locais em '$targetMcpBaseDir'..."

$mcpDirs = Get-ChildItem -Path $targetMcpBaseDir -Directory | Where-Object { $_.Name -notin ("node_modules", "build", "dist", ".git", ".vscode", "scripts", "tests", "docs", "assets", "image", "mcp-client", "supabase_mcp", "temp_servers", "MCP_Sources") } # Exclui pastas comuns e a pasta de fontes se existir

foreach ($dir in $mcpDirs) {
    $mcpName = $dir.Name
    $mcpPath = $dir.FullName
    Write-Log "Processando MCP: $mcpName em $mcpPath"

    Push-Location $mcpPath

    # Bloco Try/Catch/Finally principal para cada diretório MCP
    try {
        # --- Processamento Node.js ---
        if (Test-Path "package.json") {
            Write-Log "  Projeto Node.js detectado."

            # Instalar dependências (Execução direta)
            Write-Log "    Tentando instalar dependências (npm/pnpm)..."
            try {
                if (Test-Path "pnpm-lock.yaml") {
                    if (Test-CommandExists "pnpm") {
                        Write-Log "      Executando 'pnpm install' diretamente..."
                        pnpm install
                    } else {
                         Write-Log "    'pnpm-lock.yaml' encontrado, mas pnpm não está instalado. Pulando instalação." -Level WARN
                    }
                } else {
                    Write-Log "      Executando 'npm install' diretamente..."
                    npm install
                }
            } catch {
                 Write-Log "    Falha ao executar install (npm/pnpm): $($_.Exception.Message)" -Level ERROR
            }

            # Build (se necessário)
            $packageJson = Get-Content "package.json" -Raw | ConvertFrom-Json
            $buildCommand = $null
            if ($packageJson.scripts -and $packageJson.scripts.PSObject.Properties.Name -contains 'build') {
                if (Test-Path "pnpm-lock.yaml" -and (Test-CommandExists "pnpm")) {
                    $buildCommand = "pnpm run build"
                } else {
                    $buildCommand = "npm run build"
                }
            } elseif ($mcpName -eq "mcp-youtube" -and $packageJson.scripts -and $packageJson.scripts.PSObject.Properties.Name -contains 'prepublish') {
                 if (Test-CommandExists "bun") {
                     $buildCommand = "npm run prepublish"
                 } else {
                     Write-Log "    Bun não encontrado. Pulando build para mcp-youtube." -Level WARN
                 }
            }

            if ($buildCommand) {
                 Write-Log "    Tentando executar comando de build: '$buildCommand'..."
                 try {
                     Invoke-Expression $buildCommand
                 } catch {
                      Write-Log "    Falha ao executar '$buildCommand': $($_.Exception.Message)" -Level ERROR
                 }
            }
        # --- Processamento Python ---
        } elseif (Test-Path "pyproject.toml") {
            Write-Log "  Projeto Python (uv) detectado."
            Write-Log "    Tentando executar 'python -m uv sync'..."
            try {
                python -m uv sync
            } catch {
                 Write-Log "    Falha ao executar 'python -m uv sync': $($_.Exception.Message)" -Level ERROR
            }
        # --- Tipo Não Reconhecido ---
        } else {
            Write-Log "  Tipo de projeto não reconhecido (sem package.json ou pyproject.toml). Pulando instalação/build." -Level WARN
        }
    # --- Captura de Erro Geral ---
    } catch {
        # Captura erros que podem ocorrer fora dos blocos try internos (ex: Push-Location, Get-Content)
        Write-Log "  Erro GERAL ao processar MCP '$mcpName': $($_.Exception.Message)" -Level ERROR
    } finally {
        # --- Limpeza (Sempre Executa) ---
        # Garante que sempre voltamos ao diretório anterior, mesmo se ocorrer erro
        Pop-Location
    }
}
Write-Log "Instalação/Build dos MCPs locais concluída (com possíveis erros)."

# Adiciona um aviso sobre a autenticação manual do Google Drive
Write-Log "IMPORTANTE: Para o MCP do Google Drive, lembre-se de executar 'npx @modelcontextprotocol/server-gdrive auth' manualmente após este script, se ainda não o fez, para autorizar o acesso." -Level WARN

# --- 5. Geração Dinâmica do mcp_settings.json ---
Write-Log "Gerando configuração JSON combinada..."

# Estrutura base do JSON (pode ser lida de um template se preferir)
$mcpConfig = @{
  mcpServers = @{
    # --- MCPs Remotos/NPM ---
    "github" = @{ # Simplificado para usar apenas 'env'
      command = "cmd"; args = @("/c", "npx", "-y", "@smithery/cli@latest", "run", "@smithery-ai/github"); disabled = $false; alwaysAllow = @(); env = @{}
    }
    "Sequential Thinking" = @{ command = "cmd"; args = @("/c", "npx", "-y", "@smithery/cli@latest", "run", "@smithery-ai/server-sequential-thinking", "--config", '"{}"'); disabled = $false; alwaysAllow = @() }
    "Claude Code MCP Server" = @{ command = "cmd"; args = @("/c", "npx", "-y", "@smithery/cli@latest", "run", "@auchenberg/claude-code-mcp", "--config", '"{}"'); disabled = $false; alwaysAllow = @() }
    "Gemini Thinking Serve" = @{ # Simplificado para usar apenas 'env'
      command = "cmd"; args = @("/c", "npx", "-y", "@smithery/cli@latest", "run", "@bartekke8it56w2/new-mcp"); disabled = $false; alwaysAllow = @(); env = @{}
    }
     "Qwen Autonomous Coder Agent" = @{ # Simplificado para usar apenas 'env'
      command = "cmd"; args = @("/c", "npx", "-y", "@smithery/cli@latest", "run", "@sfatkhutdinov/autonomous-coder-agent"); disabled = $false; alwaysAllow = @(); env = @{}
    }
    "Puppeteer" = @{ command = "cmd"; args = @("/c", "npx", "-y", "@smithery/cli@latest", "run", "@smithery-ai/puppeteer", "--config", '"{}"'); disabled = $false; alwaysAllow = @() }
    "Desktop Commander" = @{ command = "cmd"; args = @("/c", "npx", "-y", "@smithery/cli@latest", "run", "@wonderwhy-er/desktop-commander", "--config", '"{}"'); disabled = $false; alwaysAllow = @() }
    "Cursor-mcp-tool" = @{ command = "cmd"; args = @("/c", "npx", "-y", "@smithery/cli@latest", "run", "cursor-mcp-tool", "--config", '"{}"'); disabled = $false; alwaysAllow = @() }
    "github.com/AgentDeskAI/browser-tools-mcp" = @{ command = "cmd"; args = @("/c", "npx", "@agentdeskai/browser-tools-mcp@1.2.0"); disabled = $false; alwaysAllow = @() }
    "google-drive" = @{ # Novo
      command = "cmd"; args = @("/c", "npx", "@modelcontextprotocol/server-gdrive"); disabled = $false; alwaysAllow = @()
      # Nota: Requer execução manual prévia de 'npx @modelcontextprotocol/server-gdrive auth'
    }
    "spotify" = @{ # Novo - Removido --config, usando apenas env
      command = "cmd"; args = @("/c", "npx", "@superseoworld/mcp-spotify"); disabled = $false; alwaysAllow = @(); env = @{} # Adicionado env vazio para injeção
    }
    "notion" = @{ # Novo
      command = "cmd"; args = @("/c", "npx", "@modelcontextprotocol/server-notion"); disabled = $false; alwaysAllow = @(); env = @{} # Adicionado env vazio para injeção
    }

    # --- MCPs Locais ---
    "codegen-mcp-server" = @{ command = "uvx"; args = @("--from", "git+https://github.com/codegen-sh/codegen-sdk.git#egg=codegen-mcp-server&subdirectory=codegen-examples/examples/codegen-mcp-server", "codegen-mcp-server"); disabled = $false; alwaysAllow = @() }
    "Figma-Context-MCP" = @{ command = "cmd"; args = @("/c", "cd /d `"$targetMcpBaseDir\Figma-Context-MCP`" && node dist/index.js"); disabled = $false; alwaysAllow = @(); env = @{} }
    "magic-mcp" = @{ command = "cmd"; args = @("/c", "cd /d `"$targetMcpBaseDir\magic-mcp`" && node dist/index.js"); disabled = $false; alwaysAllow = @(); env = @{} } # Atualizado com env vazio
    "mcp-playwright" = @{ command = "cmd"; args = @("/c", "cd /d `"$targetMcpBaseDir\mcp-playwright`" && node dist/index.js"); disabled = $false; alwaysAllow = @() }
    "mcp-server-neon" = @{ command = "cmd"; args = @("/c", "cd /d `"$targetMcpBaseDir\mcp-server-neon`" && node dist/index.js"); disabled = $false; alwaysAllow = @() }
    "markdownify-mcp" = @{ command = "cmd"; args = @("/c", "cd /d `"$targetMcpBaseDir\markdownify-mcp`" && node simple-markdownify.js"); disabled = $false; alwaysAllow = @() }
    "mcp-youtube" = @{ command = "cmd"; args = @("/c", "cd /d `"$targetMcpBaseDir\mcp-youtube`" && node final-youtube-info.js"); disabled = $false; alwaysAllow = @() }
    "memory-mcp" = @{ command = "cmd"; args = @("/c", "cd /d `"$targetMcpBaseDir\memory-mcp`" && node dist/index.js"); disabled = $false; alwaysAllow = @() }
    "slack-mcp" = @{ command = "cmd"; args = @("/c", "cd /d `"$targetMcpBaseDir\slack-mcp`" && node dist/index.js"); disabled = $false; alwaysAllow = @(); env = @{} }
    "Software-planning-mcp" = @{ command = "cmd"; args = @("/c", "cd /d `"$targetMcpBaseDir\Software-planning-mcp`" && node simple-planning.js"); disabled = $false; alwaysAllow = @() }
    "sqlite-mcp" = @{ command = "cmd"; args = @("/c", "cd /d `"$targetMcpBaseDir\sqlite-mcp`" && node simple-sqlite.js"); disabled = $false; alwaysAllow = @() }
    "supabase-mcp-server" = @{ command = "cmd"; args = @("/c", "cd /d `"$targetMcpBaseDir\supabase-mcp-server`" && python -m uv run supabase-mcp-server"); disabled = $false; alwaysAllow = @(); env = @{} } # Usando python -m uv
  }
}

# Injetar chaves de API na seção 'env' (se a chave existir no .env)
# Injetar chaves de API na seção 'env' (se a chave existir no .env)
if ($apiKeys.ContainsKey("GITHUB_PERSONAL_ACCESS_TOKEN")) { $mcpConfig.mcpServers.'github'.env.GITHUB_PERSONAL_ACCESS_TOKEN = $apiKeys.GITHUB_PERSONAL_ACCESS_TOKEN }
if ($apiKeys.ContainsKey("GEMINI_API_KEY")) { $mcpConfig.mcpServers.'Gemini Thinking Serve'.env.GEMINI_API_KEY = $apiKeys.GEMINI_API_KEY }
if ($apiKeys.ContainsKey("QWEN_BASE_URL")) { $mcpConfig.mcpServers.'Qwen Autonomous Coder Agent'.env.QWEN_BASE_URL = $apiKeys.QWEN_BASE_URL }
if ($apiKeys.ContainsKey("QWEN_MODEL_NAME")) { $mcpConfig.mcpServers.'Qwen Autonomous Coder Agent'.env.QWEN_MODEL_NAME = $apiKeys.QWEN_MODEL_NAME }
if ($apiKeys.ContainsKey("FIGMA_PERSONAL_ACCESS_TOKEN")) { $mcpConfig.mcpServers.'Figma-Context-MCP'.env.FIGMA_PERSONAL_ACCESS_TOKEN = $apiKeys.FIGMA_PERSONAL_ACCESS_TOKEN }
if ($apiKeys.ContainsKey("FIGMA_FILE_KEY")) { $mcpConfig.mcpServers.'Figma-Context-MCP'.env.FIGMA_FILE_KEY = $apiKeys.FIGMA_FILE_KEY }
if ($apiKeys.ContainsKey("SLACK_BOT_TOKEN")) { $mcpConfig.mcpServers.'slack-mcp'.env.SLACK_BOT_TOKEN = $apiKeys.SLACK_BOT_TOKEN }
if ($apiKeys.ContainsKey("SUPABASE_PROJECT_REF")) { $mcpConfig.mcpServers.'supabase-mcp-server'.env.SUPABASE_PROJECT_REF = $apiKeys.SUPABASE_PROJECT_REF }
if ($apiKeys.ContainsKey("SUPABASE_DB_PASSWORD")) { $mcpConfig.mcpServers.'supabase-mcp-server'.env.SUPABASE_DB_PASSWORD = $apiKeys.SUPABASE_DB_PASSWORD }
if ($apiKeys.ContainsKey("SUPABASE_REGION")) { $mcpConfig.mcpServers.'supabase-mcp-server'.env.SUPABASE_REGION = $apiKeys.SUPABASE_REGION }
if ($apiKeys.ContainsKey("SUPABASE_ACCESS_TOKEN")) { $mcpConfig.mcpServers.'supabase-mcp-server'.env.SUPABASE_ACCESS_TOKEN = $apiKeys.SUPABASE_ACCESS_TOKEN }
if ($apiKeys.ContainsKey("SUPABASE_SERVICE_ROLE_KEY")) { $mcpConfig.mcpServers.'supabase-mcp-server'.env.SUPABASE_SERVICE_ROLE_KEY = $apiKeys.SUPABASE_SERVICE_ROLE_KEY }
if ($apiKeys.ContainsKey("TWENTY_FIRST_API_KEY")) { $mcpConfig.mcpServers.'magic-mcp'.env.TWENTY_FIRST_API_KEY = $apiKeys.TWENTY_FIRST_API_KEY } # Novo Magic UI
if ($apiKeys.ContainsKey("SPOTIFY_CLIENT_ID")) { $mcpConfig.mcpServers.'spotify'.env.SPOTIFY_CLIENT_ID = $apiKeys.SPOTIFY_CLIENT_ID } # Novo Spotify
if ($apiKeys.ContainsKey("SPOTIFY_CLIENT_SECRET")) { $mcpConfig.mcpServers.'spotify'.env.SPOTIFY_CLIENT_SECRET = $apiKeys.SPOTIFY_CLIENT_SECRET } # Novo Spotify
if ($apiKeys.ContainsKey("NOTION_API_KEY")) { $mcpConfig.mcpServers.'notion'.env.NOTION_API_KEY = $apiKeys.NOTION_API_KEY } # Novo Notion

# Remover blocos 'env' vazios
$mcpConfig.mcpServers.PSObject.Properties | Where-Object { $_.Value -is [hashtable] -and $_.Value.ContainsKey('env') -and $_.Value.env.Count -eq 0 } | ForEach-Object {
    $_.Value.Remove('env')
}


# Converter para JSON final
$finalJson = $mcpConfig | ConvertTo-Json -Depth 10
Write-Log "Configuração JSON final gerada."

# --- 6. Identificação Robusta dos Locais de Configuração ---
Write-Log "Identificando locais de configuração das ferramentas de IA..."
$configPathsToUpdate = [System.Collections.Generic.List[string]]::new()

$potentialPaths = @{
    "Roo/Cline (VSCode Ext)" = @(
        Join-Path $env:APPDATA "Code\User\globalStorage\rooveterinaryinc.roo-cline\settings\mcp_settings.json"
        Join-Path $env:LOCALAPPDATA "Code\User\globalStorage\rooveterinaryinc.roo-cline\settings\mcp_settings.json" # Alternativa
    )
    "Cursor IDE" = @(
        Join-Path $env:APPDATA "Cursor\User\globalStorage\cursor.cursor-mcp\mcp_settings.json" # Suposição 1
        Join-Path $env:APPDATA "Cursor\User\config\mcp_servers.json" # Suposição 2
        Join-Path $env:LOCALAPPDATA "Programs\Cursor\resources\app\User\globalStorage\cursor.cursor-mcp\mcp_settings.json" # Suposição 3
        # Adicionar mais caminhos se conhecidos
    )
    "Windsurf" = @(
         Join-Path $env:APPDATA "Windsurf\config\mcp_servers.json" # Suposição
         # Adicionar mais caminhos se conhecidos
    )
     "Trae" = @(
         Join-Path $env:APPDATA "Trae\config\mcp_servers.json" # Suposição
         # Adicionar mais caminhos se conhecidos
    )
     "Augment" = @(
         Join-Path $env:APPDATA "Augment\config\mcp_servers.json" # Suposição
         # Adicionar mais caminhos se conhecidos
    )
    "VSCode Stable" = @(
        # Geralmente extensões gerenciam isso, mas verificamos locais comuns de extensões MCP se conhecidos
        # Exemplo: Join-Path $env:USERPROFILE ".vscode\extensions\alguma.extensao-mcp-0.1.0\config\mcp_settings.json"
    )
     "VSCode Insiders" = @(
        Join-Path $env:APPDATA "Code - Insiders\User\globalStorage\rooveterinaryinc.roo-cline\settings\mcp_settings.json" # Se usar a mesma extensão
        # Adicionar mais caminhos se conhecidos
    )
}

foreach ($tool in $potentialPaths.Keys) {
    $foundPath = $false
    foreach ($path in $potentialPaths[$tool]) {
        if (Test-Path $path -PathType Leaf) {
            Write-Log "  Local de configuração encontrado para '$tool': $path"
            $configPathsToUpdate.Add($path)
            $foundPath = $true
            break # Usa o primeiro encontrado
        } elseif (Test-Path (Split-Path $path -Parent) -PathType Container) {
             # Se o arquivo não existe, mas o diretório sim, consideramos como um local válido para criar o arquivo
             Write-Log "  Diretório de configuração encontrado para '$tool', arquivo será criado em: $path"
             $configPathsToUpdate.Add($path)
             $foundPath = $true
             break
        }
    }
    if (-not $foundPath) {
        Write-Log "  Nenhum local de configuração encontrado para '$tool'. Verifique os caminhos potenciais no script." -Level WARN
    }
}

if ($configPathsToUpdate.Count -eq 0) {
    Write-Log "Nenhum local de configuração válido foi encontrado para atualizar. Verifique os caminhos no script." -Level ERROR
    exit 1
}

# --- 7. Cópia/Atualização do mcp_settings.json ---
Write-Log "Atualizando arquivos de configuração MCP..."

foreach ($targetPath in $configPathsToUpdate) {
    try {
        Write-Log "  Processando: $targetPath"
        $targetDir = Split-Path $targetPath -Parent
        # Cria o diretório se não existir
        if (-not (Test-Path $targetDir -PathType Container)) {
            Write-Log "    Criando diretório: $targetDir"
            New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
        }

        # Faz backup do arquivo existente
        if (Test-Path $targetPath -PathType Leaf) {
            $backupPath = "$targetPath.bak"
            Write-Log "    Fazendo backup do arquivo existente para: $backupPath"
            Copy-Item -Path $targetPath -Destination $backupPath -Force
        }

        # Escreve o novo arquivo de configuração
        Write-Log "    Escrevendo nova configuração..."
        Set-Content -Path $targetPath -Value $finalJson -Encoding UTF8 -Force

        Write-Log "    Arquivo de configuração atualizado com sucesso."

    } catch {
        Write-Log "  Erro ao atualizar '$targetPath': $($_.Exception.Message)" -Level ERROR
    }
}

Write-Log "Script concluído!"
Write-Log "Verifique os logs para quaisquer erros durante a instalação/build dos MCPs."
Write-Log "Lembrete Google Drive: Execute 'npx @modelcontextprotocol/server-gdrive auth' manualmente se ainda não o fez." -Level WARN
Write-Log "Certifique-se de reiniciar as ferramentas de IA (Roo, Cline, Cursor, etc.) para que elas carreguem a nova configuração MCP."