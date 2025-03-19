# CloverBootloaderTweak.ps1
# Script para automatizar a instalação e configuração do Clover Bootloader
# WinDeckHelper - Projeto de Automatização
# Versão: 1.0.0

#Requires -RunAsAdministrator

# Configuração inicial
$ErrorActionPreference = "Stop"
$scriptName = [System.IO.Path]::GetFileNameWithoutExtension($MyInvocation.MyCommand.Name)
$logPath = Join-Path $PSScriptRoot "logs\$scriptName.log"
$resourcesPath = Join-Path $PSScriptRoot "..\..\resources\installers"
$checksumPath = Join-Path $resourcesPath "checksums.json"

# URLs para download do Clover Bootloader
$cloverSourceUrls = @(
    "https://github.com/CloverHackyColor/CloverBootloader/releases/download/5151/CloverBootloader-5151.7z",
    "https://sourceforge.net/projects/cloverefiboot/files/Installer/Clover_v2.5k_r5151.7z/download"
)

# URLs da API do GitHub
$githubApiUrl = "https://api.github.com/repos/CloverHackyColor/CloverBootloader/releases/latest"
$githubFallbackUrl = "https://api.github.com/repos/CloverHackyColor/CloverBootloader/releases"

# Diretórios e configurações
$cloverInstallPath = "C:\EFI\Clover"
$efiBasePath = "C:\EFI"
$configFilePath = Join-Path $cloverInstallPath "config.plist"
$configBackupPath = Join-Path $cloverInstallPath "config_backup.plist"

# Função para logging
function Write-LogEntry {
    param (
        [Parameter(Mandatory = $true)]
        [string]$Message,
        
        [Parameter(Mandatory = $false)]
        [ValidateSet("INFO", "WARNING", "ERROR", "SUCCESS", "DEBUG")]
        [string]$Severity = "INFO"
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Severity] $Message"
    
    # Garante que o diretório de logs existe
    $logDir = [System.IO.Path]::GetDirectoryName($logPath)
    if (-not (Test-Path $logDir)) {
        New-Item -ItemType Directory -Path $logDir -Force | Out-Null
    }
    
    # Escreve no arquivo de log
    Add-Content -Path $logPath -Value $logEntry -Encoding UTF8
    
    # Mostra no console com cores apropriadas
    switch ($Severity) {
        "INFO"    { Write-Host $logEntry -ForegroundColor Gray }
        "WARNING" { Write-Host $logEntry -ForegroundColor Yellow }
        "ERROR"   { Write-Host $logEntry -ForegroundColor Red }
        "SUCCESS" { Write-Host $logEntry -ForegroundColor Green }
        "DEBUG"   { 
            if ($VerbosePreference -eq "Continue") {
                Write-Host $logEntry -ForegroundColor Cyan 
            }
        }
    }
}

# Função para verificar se está sendo executado como administrador
function Test-AdminPrivileges {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    $isAdmin = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    
    if (-not $isAdmin) {
        Write-LogEntry "Este script deve ser executado como Administrador!" -Severity "ERROR"
        return $false
    }
    
    Write-LogEntry "Executando com privilégios de Administrador: OK" -Severity "SUCCESS"
    return $true
}

# Função para garantir que um diretório existe
function Ensure-DirectoryExists {
    param (
        [Parameter(Mandatory = $true)]
        [string]$Path,
        
        [Parameter(Mandatory = $false)]
        [bool]$CreateIfNotExists = $true
    )
    
    if (-not (Test-Path -Path $Path -PathType Container)) {
        if ($CreateIfNotExists) {
            try {
                New-Item -Path $Path -ItemType Directory -Force | Out-Null
                Write-LogEntry "Diretório criado: $Path" -Severity "SUCCESS"
                return $true
            }
            catch {
                Write-LogEntry "Falha ao criar diretório: $Path. Erro: $_" -Severity "ERROR"
                return $false
            }
        }
        else {
            Write-LogEntry "Diretório não existe: $Path" -Severity "WARNING"
            return $false
        }
    }
    
    Write-LogEntry "Diretório existe: $Path" -Severity "DEBUG"
    return $true
}

# Função para obter a versão mais recente do Clover Bootloader
function Get-LatestCloverVersion {
    Write-LogEntry "Obtendo informações da versão mais recente do Clover Bootloader..." -Severity "INFO"
    
    try {
        # Define cabeçalhos para evitar limitações de taxa da API
        $headers = @{
            "Accept" = "application/vnd.github.v3+json"
            "User-Agent" = "WinDeckHelper-CloverBootloader"
        }
        
        # Tenta obter a versão mais recente pela API
        $response = Invoke-RestMethod -Uri $githubApiUrl -Headers $headers -ErrorAction Stop
        
        if ($response.assets.Count -gt 0) {
            $latestVersion = $response.tag_name
            $downloadUrl = $response.assets | Where-Object { $_.name -like "*.7z" } | Select-Object -First 1 -ExpandProperty browser_download_url
            
            if (-not [string]::IsNullOrEmpty($downloadUrl)) {
                Write-LogEntry "Versão mais recente encontrada: $latestVersion" -Severity "SUCCESS"
                return @{
                    Version = $latestVersion
                    DownloadUrl = $downloadUrl
                    Success = $true
                }
            }
        }
        
        # Se falhou em encontrar o URL específico, tenta o fallback
        Write-LogEntry "Não foi possível encontrar o URL de download específico, tentando fallback..." -Severity "WARNING"
        $fallbackResponse = Invoke-RestMethod -Uri $githubFallbackUrl -Headers $headers -ErrorAction Stop
        
        if ($fallbackResponse.Count -gt 0) {
            $latestRelease = $fallbackResponse | Select-Object -First 1
            $latestVersion = $latestRelease.tag_name
            $downloadUrl = $latestRelease.assets | Where-Object { $_.name -like "*.7z" } | Select-Object -First 1 -ExpandProperty browser_download_url
            
            if (-not [string]::IsNullOrEmpty($downloadUrl)) {
                Write-LogEntry "Versão encontrada via fallback: $latestVersion" -Severity "SUCCESS"
                return @{
                    Version = $latestVersion
                    DownloadUrl = $downloadUrl
                    Success = $true
                }
            }
        }
        
        # Se ainda falhou, use as URLs predefinidas
        Write-LogEntry "Fallback para URLs predefinidas..." -Severity "WARNING"
        return @{
            Version = "5151" # Versão hardcoded como fallback
            DownloadUrl = $cloverSourceUrls[0]
            Success = $true
        }
    }
    catch {
        Write-LogEntry "Erro ao obter a versão mais recente: $_" -Severity "ERROR"
        
        # Retorna URL de fallback em caso de falha
        return @{
            Version = "5151" # Versão hardcoded como fallback
            DownloadUrl = $cloverSourceUrls[0]
            Success = $true
            Fallback = $true
        }
    }
}

# Função para calcular hash de arquivo
function Get-FileHash256 {
    param (
        [Parameter(Mandatory = $true)]
        [string]$FilePath
    )
    
    if (-not (Test-Path $FilePath)) {
        Write-LogEntry "Arquivo não encontrado para cálculo de hash: $FilePath" -Severity "ERROR"
        return $null
    }
    
    try {
        $hash = Get-FileHash -Path $FilePath -Algorithm SHA256
        return $hash.Hash.ToLower()
    }
    catch {
        Write-LogEntry "Erro ao calcular hash do arquivo: $_" -Severity "ERROR"
        return $null
    }
}

# Função para download de arquivo com progresso e verificação de integridade
function Download-FileWithProgress {
    param (
        [Parameter(Mandatory = $true)]
        [string]$Url,
        
        [Parameter(Mandatory = $true)]
        [string]$OutputPath,
        
        [Parameter(Mandatory = $false)]
        [string]$ExpectedHash = "",
        
        [Parameter(Mandatory = $false)]
        [int]$MaxRetries = 3
    )
    
    # Garante que o diretório de destino existe
    $outputDir = [System.IO.Path]::GetDirectoryName($OutputPath)
    if (-not (Test-Path -Path $outputDir)) {
        New-Item -Path $outputDir -ItemType Directory -Force | Out-Null
    }
    
    $retryCount = 0
    $success = $false
    
    while (-not $success -and $retryCount -lt $MaxRetries) {
        try {
            Write-LogEntry "Baixando de: $Url" -Severity "INFO"
            Write-LogEntry "Destino: $OutputPath" -Severity "DEBUG"
            
            if ($retryCount -gt 0) {
                Write-LogEntry "Tentativa $($retryCount + 1) de $MaxRetries" -Severity "WARNING"
            }
            
            # Cria WebClient com timeout aumentado
            $webClient = New-Object System.Net.WebClient
            $webClient.Headers.Add("User-Agent", "WinDeckHelper-CloverBootloader")
            $webClient.Timeout = 60000 # 60 segundos
            
            # Adiciona eventos para acompanhar o progresso
            $totalBytes = 0
            $lastPercentage = 0
            
            $webClient.DownloadProgressChanged = {
                param($sender, $e)
                $percent = $e.ProgressPercentage
                $totalBytes = $e.TotalBytesToReceive
                
                if ($percent -ge ($lastPercentage + 10) -or $percent -eq 100) {
                    $downloadedMB = [Math]::Round($e.BytesReceived / 1MB, 2)
                    $totalMB = if ($e.TotalBytesToReceive -gt 0) { [Math]::Round($e.TotalBytesToReceive / 1MB, 2) } else { "?" }
                    Write-LogEntry "Download em progresso: $percent% ($downloadedMB MB / $totalMB MB)" -Severity "INFO"
                    $script:lastPercentage = $percent
                }
            }
            
            $webClient.DownloadFileCompleted = {
                param($sender, $e)
                if ($e.Error -ne $null) {
                    Write-LogEntry "Erro no download: $($e.Error.Message)" -Severity "ERROR"
                    $script:success = $false
                }
                else {
                    Write-LogEntry "Download concluído!" -Severity "SUCCESS"
                }
            }
            
            # Faz o download
            $webClient.DownloadFileAsync($Url, $OutputPath)
            
            # Aguarda o download terminar
            while ($webClient.IsBusy) {
                Start-Sleep -Milliseconds 100
            }
            
            # Verifica se o arquivo foi baixado corretamente
            if (-not (Test-Path $OutputPath)) {
                throw "Arquivo não foi baixado para o destino."
            }
            
            $fileSize = (Get-Item $OutputPath).Length
            if ($fileSize -eq 0) {
                throw "Arquivo baixado tem tamanho zero."
            }
            
            # Verifica o hash do arquivo, se fornecido
            if (-not [string]::IsNullOrEmpty($ExpectedHash)) {
                $actualHash = Get-FileHash256 -FilePath $OutputPath
                
                if ($actualHash -ne $null -and $actualHash -eq $ExpectedHash) {
                    Write-LogEntry "Verificação de integridade: SUCESSO" -Severity "SUCCESS"
                }
                else {
                    throw "Falha na verificação de integridade. Hash esperado: $ExpectedHash, Hash atual: $actualHash"
                }
            }
            
            $success = $true
            Write-LogEntry "Download completo e verificado: $OutputPath" -Severity "SUCCESS"
        }
        catch {
            $retryCount++
            Write-LogEntry "Erro no download: $_" -Severity "ERROR"
            
            if ($retryCount -lt $MaxRetries) {
                Write-LogEntry "Aguardando antes de tentar novamente..." -Severity "WARNING"
                Start-Sleep -Seconds (2 * $retryCount) # Backoff exponencial
                
                # Se ainda houver falha, tente URLs alternativas
                if ($retryCount -eq ($MaxRetries - 1) -and $cloverSourceUrls.Count -gt 1) {
                    $alternativeUrl = $cloverSourceUrls[1]
                    Write-LogEntry "Tentando URL alternativa: $alternativeUrl" -Severity "WARNING"
                    $Url = $alternativeUrl
                }
            }
            else {
                Write-LogEntry "Número máximo de tentativas excedido. Download falhou." -Severity "ERROR"
                return $false
            }
        }
        finally {
            if ($webClient -ne $null) {
                $webClient.Dispose()
            }
        }
    }
    
    return $success
}

# Função para extrair arquivos 7z
function Extract-7ZipArchive {
    param (
        [Parameter(Mandatory = $true)]
        [string]$ArchivePath,
        
        [Parameter(Mandatory = $true)]
        [string]$DestinationPath
    )
    
    Write-LogEntry "Extraindo arquivo 7z: $ArchivePath" -Severity "INFO"
    
    try {
        # Verifica se 7-Zip está instalado
        $sevenZipPath = "$env:ProgramFiles\7-Zip\7z.exe"
        
        if (-not (Test-Path $sevenZipPath)) {
            # Tenta encontrar em Program Files (x86)
            $sevenZipPath = "${env:ProgramFiles(x86)}\7-Zip\7z.exe"
            
            if (-not (Test-Path $sevenZipPath)) {
                throw "7-Zip não encontrado no sistema. Por favor, instale o 7-Zip."
            }
        }
        
        # Executa a extração
        $process = Start-Process -FilePath $sevenZipPath -ArgumentList "x `"$ArchivePath`" -o`"$DestinationPath`" -y" -Wait -PassThru -NoNewWindow
        
        if ($process.ExitCode -ne 0) {
            throw "Erro durante a extração. Código de saída: $($process.ExitCode)"
        }
        
        Write-LogEntry "Extração concluída com sucesso" -Severity "SUCCESS"
        return $true
    }
    catch {
        Write-LogEntry "Erro ao extrair arquivo: $_" -Severity "ERROR"
        return $false
    }
}

# Função para instalar o Clover Bootloader
function Install-CloverBootloader {
    param (
        [switch]$UseLocal = $false
    )
    
    Write-LogEntry "Iniciando processo de instalação do Clover Bootloader" -Severity "INFO"
    
    # Verifica privilégios de administrador
    if (-not (Test-AdminPrivileges)) {
        return $false
    }
    
    # Garante que os diretórios necessários existem
    Ensure-DirectoryExists -Path $resourcesPath
    
    $cloverInstallerPath = ""
    $cloverVersion = ""
    
    if ($UseLocal) {
        # Procura por instaladores locais
        Write-LogEntry "Procurando por instaladores locais do Clover Bootloader..." -Severity "INFO"
        $localInstallers = Get-ChildItem -Path $resourcesPath -Filter "CloverBootloader-*.7z" | Sort-Object LastWriteTime -Descending
        
        if ($localInstallers.Count -gt 0) {
            $latestInstaller = $localInstallers[0]
            $cloverInstallerPath = $latestInstaller.FullName
            $cloverVersion = $latestInstaller.Name -replace "CloverBootloader-", "" -replace ".7z", ""
            
            Write-LogEntry "Instalador local encontrado: $($latestInstaller.Name)" -Severity "SUCCESS"
        }
        else {
            Write-LogEntry "Nenhum instalador local encontrado. Baixando a versão mais recente..." -Severity "WARNING"
            $UseLocal = $false
        }
    }
    
    if (-not $UseLocal) {
        # Obtém informações da versão mais recente
        $latestInfo = Get-LatestCloverVersion
        
        if (-not $latestInfo.Success) {
            Write-LogEntry "Falha ao obter informações da versão mais recente do Clover. Abortando." -Severity "ERROR"
            return $false
        }
        
        $cloverVersion = $latestInfo.Version
        $downloadUrl = $latestInfo.DownloadUrl
        
        # Prepara o nome do arquivo
        $fileName = "CloverBootloader-$cloverVersion.7z"
        $cloverInstallerPath = Join-Path $resourcesPath $fileName
        
        # Verifica se o arquivo já existe
        if (Test-Path $cloverInstallerPath) {
            Write-LogEntry "Instalador já existe: $cloverInstallerPath" -Severity "INFO"
            
            # Verifica integridade se tivermos checksum
            if (Test-Path $checksumPath) {
                try {
                    $checksums = Get-Content $checksumPath -Raw | ConvertFrom-Json
                    $expectedHash = $checksums.clover.$cloverVersion
                    
                    if (-not [string]::IsNullOrEmpty($expectedHash)) {
                        $actualHash = Get-FileHash256 -FilePath $cloverInstallerPath
                        
                        if ($actualHash -eq $expectedHash) {
                            Write-LogEntry "Verificação de integridade do instalador local: SUCESSO" -Severity "SUCCESS"
                        }
                        else {
                            Write-LogEntry "Falha na verificação de integridade do instalador local. Baixando novamente..." -Severity "WARNING"
                            Remove-Item $cloverInstallerPath -Force
                            
                            # Baixa o instalador
                            $downloadSuccess = Download-FileWithProgress -Url $downloadUrl -OutputPath $cloverInstallerPath -ExpectedHash $expectedHash
                            
                            if (-not $downloadSuccess) {
                                Write-LogEntry "Falha no download do instalador. Abortando." -Severity "ERROR"
                                return $false
                            }
                        }
                    }
                    else {
                        Write-LogEntry "Nenhum checksum encontrado para versão $cloverVersion. Pulando verificação." -Severity "WARNING"
                    }
                }
                catch {
                    Write-LogEntry "Erro ao processar arquivo de checksums: $_" -Severity "WARNING"
                }
            }
            else {
                Write-LogEntry "Arquivo de checksums não encontrado. Pulando verificação de integridade." -Severity "WARNING"
            }
        }
        else {
            # Baixa o instalador
            $expectedHash = ""
            
            # Tenta obter checksum do arquivo de checksums
            if (Test-Path $checksumPath) {
                try {
                    $checksums = Get-Content $checksumPath -Raw | ConvertFrom-Json
                    $expectedHash = $checksums.clover.$cloverVersion
                }
                catch {
                    Write-LogEntry "Erro ao processar arquivo de checksums: $_" -Severity "WARNING"
                }
            }
            
            $downloadSuccess = Download-FileWithProgress -Url $downloadUrl -OutputPath $cloverInstallerPath -ExpectedHash $expectedHash
            
            if (-not $downloadSuccess) {
                Write-LogEntry "Falha no download do instalador. Abortando." -Severity "ERROR"
                return $false
            }
        }
    }
    
    # Prepara diretório temporário para extração
    $tempDir = Join-Path $env:TEMP "CloverBootloader_$([Guid]::NewGuid().ToString())"
    Ensure-DirectoryExists -Path $tempDir
    
    try {
        # Extrai o instalador
        Write-LogEntry "Extraindo instalador do Clover Bootloader..." -Severity "INFO"
        $extractSuccess = Extract-7ZipArchive -ArchivePath $cloverInstallerPath -DestinationPath $tempDir
        
        if (-not $extractSuccess) {
            throw "Falha ao extrair o arquivo do Clover Bootloader."
        }
        
        # Procura o instalador extraído
        $cloverExe = Get-ChildItem -Path $tempDir -Filter "Clover*.exe" -Recurse | Select-Object -First 1
        
        if ($cloverExe -eq $null) {
            throw "Instalador Clover EXE não encontrado após extração."
        }
        
        # Executa o instalador
        Write-LogEntry "Executando instalador do Clover Bootloader: $($cloverExe.FullName)" -Severity "INFO"
        $installArgs = "/S /D=$cloverInstallPath"
        $process = Start-Process -FilePath $cloverExe.FullName -ArgumentList $installArgs -Wait -PassThru -NoNewWindow
        
        if ($process.ExitCode -ne 0) {
            throw "Instalação falhou com código de saída: $($process.ExitCode)"
        }
        
        # Verifica se a instalação foi bem-sucedida
        if (-not (Test-Path $cloverInstallPath)) {
            throw "Diretório de instalação não encontrado após a instalação."
        }
        
        # Procura pelo arquivo config.plist
        $configFileExists = Test-Path $configFilePath
        
        if (-not $configFileExists) {
            Write-LogEntry "Arquivo config.plist não encontrado. Procurando em locais alternativos..." -Severity "WARNING"
            
            # Procura em locais alternativos
            $alternativePaths = @(
                "C:\EFI\CLOVER\config.plist",
                "C:\CLOVER\config.plist",
                "$cloverInstallPath\EFI\CLOVER\config.plist"
            )
            
            foreach ($path in $alternativePaths) {
                if (Test-Path $path) {
                    $configFilePath = $path
                    $configFileExists = $true
                    Write-LogEntry "Arquivo config.plist encontrado em: $path" -Severity "SUCCESS"
                    break
                }
            }
        }
        
        if (-not $configFileExists) {
            throw "Arquivo config.plist não encontrado após a instalação."
        }
        
        # Cria backup do arquivo config.plist
        Copy-Item -Path $configFilePath -Destination $configBackupPath -Force
        Write-LogEntry "Backup do arquivo config.plist criado: $configBackupPath" -Severity "SUCCESS"
        
        # Detecta sistemas Linux
        Write-LogEntry "Iniciando detecção de sistemas Linux..." -Severity "INFO"
        $linuxEfiFiles = @()
        
        # Procura por arquivos .efi relacionados ao Linux
        $efiDirs = Get-ChildItem -Path $efiBasePath -Directory -ErrorAction SilentlyContinue
        
        foreach ($dir in $efiDirs) {
            if ($dir.Name -eq "Clover") { continue } # Ignora o diretório do Clover
            
            Write-LogEntry "Verificando diretório: $($dir.FullName)" -Severity "DEBUG"
            $efiFiles = Get-ChildItem -Path $dir.FullName -Recurse -Filter "*.efi" -ErrorAction SilentlyContinue
            
            foreach ($file in $efiFiles) {
                $relativePath = $file.FullName.Replace("C:\", "\")
                $name = ""
                
                # Tenta identificar o sistema Linux
                switch -Wildcard ($dir.Name) {
                    "ubuntu*" { $name = "Ubuntu" }
                    "debian*" { $name = "Debian" }
                    "fedora*" { $name = "Fedora" }
                    "opensuse*" { $name = "openSUSE" }
                    "arch*" { $name = "Arch Linux" }
                    "manjaro*" { $name = "Manjaro" }
                    "linuxmint*" { $name = "Linux Mint" }
                    "pop_os*" { $name = "Pop!_OS" }
                    "elementary*" { $name = "elementary OS" }
                    "kali*" { $name = "Kali Linux" }
                    "zorin*" { $name = "Zorin OS" }
                    "mx*" { $name = "MX Linux" }
                    default { 
                        if ($file.Name -match "grub") {
                            $name = "GRUB Linux"
                        }
                        elseif ($file.Name -match "vmlinuz") {
                            $name = "Linux Kernel"
                        }
                        else {
                            $name = "Linux ($($dir.Name))" 
                        }
                    }
                }
                
                $linuxEfiFiles += [PSCustomObject]@{
                    Name = $name
                    Path = $relativePath
                    File = $file.Name
                }
                
                Write-LogEntry "Detectado: $name em $relativePath" -Severity "SUCCESS"
            }
        }
        
        # Atualiza o arquivo config.plist com as entradas Linux
        if ($linuxEfiFiles.Count -gt 0) {
            Write-LogEntry "Atualizando config.plist com $($linuxEfiFiles.Count) sistemas Linux detectados..." -Severity "INFO"
            
            try {
                # Carrega o arquivo config.plist
                $configContent = Get-Content -Path $configFilePath -Raw
                
                # Modifica o XML
                $xml = New-Object System.Xml.XmlDocument
                $xml.PreserveWhitespace = $true
                $xml.LoadXml($configContent)
                
                # Verifica se o nó de entradas customizadas existe
                $dictNode = $xml.SelectSingleNode("//dict/key[text()='Custom']/following-sibling::dict[1]")
                
                if ($dictNode -eq $null) {
                    # Cria os nós necessários
                    $customKey = $xml.CreateElement("key")
                    $customKey.InnerText = "Custom"
                    $customDict = $xml.CreateElement("dict")
                    
                    $rootDict = $xml.SelectSingleNode("//dict")
                    $rootDict.AppendChild($customKey)
                    $rootDict.AppendChild($customDict)
                    
                    $dictNode = $customDict
                }
                
                # Cria ou obtém o nó de entradas
                $entriesKey = $dictNode.SelectSingleNode("key[text()='Entries']")
                $entriesArray = $null
                
                if ($entriesKey -eq $null) {
                    $entriesKey = $xml.CreateElement("key")
                    $entriesKey.InnerText = "Entries"
                    $dictNode.AppendChild($entriesKey)
                    
                    $entriesArray = $xml.CreateElement("array")
                    $dictNode.AppendChild($entriesArray)
                }
                else {
                    $entriesArray = $entriesKey.NextSibling
                    
                    if ($entriesArray -eq $null -or $entriesArray.Name -ne "array") {
                        $entriesArray = $xml.CreateElement("array")
                        $dictNode.InsertAfter($entriesArray, $entriesKey)
                    }
                }
                
                # Adiciona entradas para cada sistema Linux
                foreach ($linux in $linuxEfiFiles) {
                    $entryDict = $xml.CreateElement("dict")
                    
                    # Adiciona FullTitle
                    $fullTitleKey = $xml.CreateElement("key")
                    $fullTitleKey.InnerText = "FullTitle"
                    $entryDict.AppendChild($fullTitleKey)
                    
                    $fullTitleString = $xml.CreateElement("string")
                    $fullTitleString.InnerText = $linux.Name
                    $entryDict.AppendChild($fullTitleString)
                    
                    # Adiciona Path
                    $pathKey = $xml.CreateElement("key")
                    $pathKey.InnerText = "Path"
                    $entryDict.AppendChild($pathKey)
                    
                    $pathString = $xml.CreateElement("string")
                    $pathString.InnerText = $linux.Path
                    $entryDict.AppendChild($pathString)
                    
                    # Adiciona Hidden
                    $hiddenKey = $xml.CreateElement("key")
                    $hiddenKey.InnerText = "Hidden"
                    $entryDict.AppendChild($hiddenKey)
                    
                    $hiddenFalse = $xml.CreateElement("false")
                    $entryDict.AppendChild($hiddenFalse)
                    
                    # Adiciona a entrada ao array
                    $entriesArray.AppendChild($entryDict)
                }
                
                # Salva o arquivo
                $xml.Save($configFilePath)
                Write-LogEntry "Arquivo config.plist atualizado com sucesso" -Severity "SUCCESS"
            }
            catch {
                Write-LogEntry "Erro ao atualizar config.plist: $_" -Severity "ERROR"
                Write-LogEntry "Restaurando backup do config.plist..." -Severity "WARNING"
                
                if (Test-Path $configBackupPath) {
                    Copy-Item -Path $configBackupPath -Destination $configFilePath -Force
                    Write-LogEntry "Backup restaurado" -Severity "INFO"
                }
            }
        }
        else {
            Write-LogEntry "Nenhum sistema Linux detectado" -Severity "WARNING"
        }
        
        # Instalação concluída
        Write-LogEntry "Instalação do Clover Bootloader v$cloverVersion concluída com sucesso" -Severity "SUCCESS"
        Write-LogEntry "Caminho de instalação: $cloverInstallPath" -Severity "INFO"
        
        if ($linuxEfiFiles.Count -gt 0) {
            Write-LogEntry "Sistemas Linux configurados: $($linuxEfiFiles.Count)" -Severity "SUCCESS"
        }
        
        return $true
    }
    catch {
        Write-LogEntry "Erro durante a instalação: $_" -Severity "ERROR"
        return $false
    }
    finally {
        # Limpa arquivos temporários
        if (Test-Path $tempDir) {
            Remove-Item -Path $tempDir -Recurse -Force -ErrorAction SilentlyContinue
            Write-LogEntry "Arquivos temporários removidos" -Severity "DEBUG"
        }
    }
}

# Função principal
function Start-CloverBootloaderInstallation {
    Write-LogEntry "=== Iniciando instalação do Clover Bootloader ===" -Severity "INFO"
    Write-LogEntry "Versão do script: 1.0.0" -Severity "INFO"
    
    # Executa a instalação
    $result = Install-CloverBootloader
    
    if ($result) {
        Write-LogEntry "=== Clover Bootloader instalado e configurado com sucesso ===" -Severity "SUCCESS"
    }
    else {
        Write-LogEntry "=== Falha na instalação do Clover Bootloader ===" -Severity "ERROR"
    }
    
    return $result
}

# Executa a função principal se o script for executado diretamente
if ($MyInvocation.InvocationName -eq $MyInvocation.MyCommand.Definition) {
    Start-CloverBootloaderInstallation
} 