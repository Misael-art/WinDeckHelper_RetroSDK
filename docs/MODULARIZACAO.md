# Plano de Modularização do WinDeckHelper

## 1. Visão Geral

Este documento apresenta um plano para modularizar o projeto WinDeckHelper, transformando-o em uma estrutura mais coesa, manutenível e com responsabilidades bem definidas. A modularização visa resolver os problemas de manutenção e risco de quebra constante do script principal.

## 2. Estrutura Proposta

### 2.1 Organização de Diretórios

```
WinDeckHelper/
├── modules/                  # Módulos funcionais
│   ├── core/                 # Módulos principais
│   │   ├── logging.psm1      # Sistema de logging
│   │   ├── config.psm1       # Configurações globais
│   │   ├── utils.psm1        # Funções utilitárias
│   │   └── ui.psm1           # Interface do usuário
│   ├── environment/          # Verificação de ambiente
│   │   ├── system.psm1       # Verificação de sistema
│   │   ├── dependencies.psm1 # Verificação de dependências
│   │   └── validation.psm1   # Validação de requisitos
│   ├── installation/         # Instalação de componentes
│   │   ├── drivers.psm1      # Instalação de drivers
│   │   ├── software.psm1     # Instalação de software
│   │   ├── sdk.psm1          # Instalação de SDKs
│   │   └── emulators.psm1    # Instalação de emuladores
│   └── tweaks/               # Ajustes do sistema
│       ├── performance.psm1  # Ajustes de performance
│       ├── bootloader.psm1   # Configuração de bootloader
│       └── display.psm1      # Ajustes de display
├── resources/                # Recursos estáticos
│   ├── installers/           # Instaladores
│   └── templates/            # Templates
├── logs/                     # Diretório de logs
├── tests/                    # Testes automatizados
│   ├── unit/                 # Testes unitários
│   └── integration/          # Testes de integração
├── docs/                     # Documentação
├── Start.bat                 # Script de inicialização
└── WinDeckHelper.ps1        # Script principal (orquestrador)
```

### 2.2 Fluxo de Execução

1. **Start.bat**: Inicia o script com privilégios de administrador
2. **WinDeckHelper.ps1**: Orquestra a execução dos módulos
   - Carrega os módulos necessários
   - Inicializa o sistema de logging
   - Apresenta a interface do usuário
   - Coordena a execução das operações selecionadas
   - Fornece feedback ao usuário

## 3. Componentes Principais

### 3.1 Sistema de Logging (modules/core/logging.psm1)

```powershell
# Exemplo de implementação
function Write-Log {
    param(
        [string]$Message,
        [ValidateSet("INFO", "WARNING", "ERROR", "SUCCESS", "DEBUG")]
        [string]$Level = "INFO",
        [string]$LogFile = "$PSScriptRoot\..\..\logs\windeckhelper.log"
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level] $Message"
    
    # Garante que o diretório de logs existe
    $logDir = Split-Path -Parent $LogFile
    if (-not (Test-Path $logDir)) {
        New-Item -ItemType Directory -Path $logDir -Force | Out-Null
    }
    
    Add-Content -Path $LogFile -Value $logMessage -Encoding UTF8
    
    switch ($Level) {
        "INFO"    { Write-Host $logMessage -ForegroundColor Gray }
        "WARNING" { Write-Host $logMessage -ForegroundColor Yellow }
        "ERROR"   { Write-Host $logMessage -ForegroundColor Red }
        "SUCCESS" { Write-Host $logMessage -ForegroundColor Green }
        "DEBUG"   { Write-Host $logMessage -ForegroundColor Cyan }
    }
}

function Start-Logging {
    param(
        [string]$SessionId = (New-Guid).ToString(),
        [string]$LogFile = "$PSScriptRoot\..\..\logs\windeckhelper.log"
    )
    
    Write-Log "Iniciando sessão de log: $SessionId" -Level "INFO" -LogFile $LogFile
    return $SessionId
}

function Stop-Logging {
    param(
        [string]$SessionId,
        [string]$LogFile = "$PSScriptRoot\..\..\logs\windeckhelper.log"
    )
    
    Write-Log "Encerrando sessão de log: $SessionId" -Level "INFO" -LogFile $LogFile
}

Export-ModuleMember -Function Write-Log, Start-Logging, Stop-Logging
```

### 3.2 Interface do Usuário (modules/core/ui.psm1)

```powershell
# Exemplo de implementação
function Show-Progress {
    param(
        [string]$Status,
        [int]$PercentComplete = 0,
        [string]$Phase = "",
        [string]$DetailStatus = ""
    )
    
    # Implementação da barra de progresso
    $progressBar = if ($PercentComplete -gt 0) {
        $barLength = [math]::Floor($PercentComplete / 2)
        $bar = "#" * $barLength
        "[$bar] $PercentComplete%"
    } else { "" }
    
    $output = @()
    if ($Phase) { $output += "# $Phase" }
    $output += $Status
    if ($progressBar) { $output += $progressBar }
    if ($DetailStatus) { $output += $DetailStatus }
    
    return $output -join "`n"
}

function Show-Menu {
    param(
        [string]$Title,
        [string[]]$Options,
        [string]$Message = "Selecione uma opção:"
    )
    
    Write-Host "`n$Title" -ForegroundColor Cyan
    Write-Host $Message
    
    for ($i = 0; $i -lt $Options.Count; $i++) {
        Write-Host "[$($i+1)] $($Options[$i])"
    }
    
    $selection = Read-Host "Digite o número da opção"
    $index = [int]$selection - 1
    
    if ($index -ge 0 -and $index -lt $Options.Count) {
        return $Options[$index]
    } else {
        Write-Host "Opção inválida!" -ForegroundColor Red
        return Show-Menu -Title $Title -Options $Options -Message $Message
    }
}

function Show-Notification {
    param(
        [string]$Message,
        [ValidateSet("INFO", "WARNING", "ERROR", "SUCCESS")]
        [string]$Type = "INFO",
        [switch]$RequireConfirmation
    )
    
    $color = switch ($Type) {
        "INFO"    { "White" }
        "WARNING" { "Yellow" }
        "ERROR"   { "Red" }
        "SUCCESS" { "Green" }
    }
    
    Write-Host $Message -ForegroundColor $color
    
    if ($RequireConfirmation) {
        Read-Host "Pressione ENTER para continuar"
    }
}

Export-ModuleMember -Function Show-Progress, Show-Menu, Show-Notification
```

### 3.3 Verificação de Ambiente (modules/environment/system.psm1)

```powershell
# Exemplo de implementação
function Test-AdminPrivileges {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Test-SystemRequirements {
    $results = @{
        "AdminPrivileges" = Test-AdminPrivileges
        "PowerShellVersion" = $PSVersionTable.PSVersion.Major -ge 5
        "DiskSpace" = (Get-PSDrive -Name C).Free -gt 10GB
        "Memory" = (Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory -gt 4GB
    }
    
    return $results
}

function Get-SystemInfo {
    $osInfo = Get-CimInstance Win32_OperatingSystem
    $computerSystem = Get-CimInstance Win32_ComputerSystem
    
    return @{
        "OSVersion" = $osInfo.Caption
        "OSBuild" = $osInfo.BuildNumber
        "ComputerName" = $computerSystem.Name
        "Manufacturer" = $computerSystem.Manufacturer
        "Model" = $computerSystem.Model
        "Memory" = [math]::Round($computerSystem.TotalPhysicalMemory / 1GB, 2)
        "Processor" = (Get-CimInstance Win32_Processor).Name
    }
}

Export-ModuleMember -Function Test-AdminPrivileges, Test-SystemRequirements, Get-SystemInfo
```

### 3.4 Instalação de Componentes (modules/installation/software.psm1)

```powershell
# Exemplo de implementação
function Install-Software {
    param(
        [string[]]$Packages,
        [string]$DownloadPath = "$PSScriptRoot\..\..\downloads",
        [switch]$Silent
    )
    
    # Importa módulos necessários
    Import-Module "$PSScriptRoot\..\core\logging.psm1"
    Import-Module "$PSScriptRoot\..\core\ui.psm1"
    
    # Cria diretório de downloads se não existir
    if (-not (Test-Path $DownloadPath)) {
        New-Item -ItemType Directory -Path $DownloadPath -Force | Out-Null
        Write-Log "Criado diretório de downloads: $DownloadPath"
    }
    
    $results = @{}
    $totalPackages = $Packages.Count
    $currentPackage = 0
    
    foreach ($package in $Packages) {
        $currentPackage++
        $percentComplete = [math]::Floor(($currentPackage / $totalPackages) * 100)
        
        if (-not $Silent) {
            $progressText = Show-Progress -Status "Instalando $package" -PercentComplete $percentComplete -Phase "Instalação" -DetailStatus "Pacote $currentPackage de $totalPackages"
            Write-Host $progressText
        }
        
        Write-Log "Iniciando instalação de $package" -Level "INFO"
        
        try {
            # Lógica de instalação específica para cada pacote
            switch ($package) {
                "MinGW-w64" {
                    # Implementação específica para MinGW-w64
                    $results[$package] = $true
                }
                "Clang" {
                    # Implementação específica para Clang
                    $results[$package] = $true
                }
                # Adicionar mais casos conforme necessário
                default {
                    Write-Log "Pacote desconhecido: $package" -Level "WARNING"
                    $results[$package] = $false
                }
            }
            
            if ($results[$package]) {
                Write-Log "Instalação de $package concluída com sucesso" -Level "SUCCESS"
            } else {
                Write-Log "Falha na instalação de $package" -Level "ERROR"
            }
        } catch {
            $errorMsg = $_.Exception.Message
            Write-Log "Erro ao instalar $package: $errorMsg" -Level "ERROR"
            $results[$package] = $false
        }
    }
    
    return $results
}

function Test-SoftwareInstalled {
    param(
        [string]$Name,
        [string]$Path = "",
        [string]$Command = ""
    )
    
    if ($Path -and (Test-Path $Path)) {
        return $true
    }
    
    if ($Command) {
        try {
            $null = Get-Command $Command -ErrorAction Stop
            return $true
        } catch {
            return $false
        }
    }
    
    # Verifica no registro do Windows
    $installed = Get-ItemProperty HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\* | 
                Where-Object { $_.DisplayName -like "*$Name*" }
    
    if (-not $installed) {
        $installed = Get-ItemProperty HKLM:\Software\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\* | 
                    Where-Object { $_.DisplayName -like "*$Name*" }
    }
    
    return $null -ne $installed
}

Export-ModuleMember -Function Install-Software, Test-SoftwareInstalled
```

## 4. Script Principal (WinDeckHelper.ps1)

O script principal será responsável por orquestrar a execução dos módulos:

```powershell
# WinDeckHelper.ps1 - Script principal (orquestrador)

# Configuração inicial
$ErrorActionPreference = "Stop"
$VerbosePreference = "Continue"
$scriptPath = $PSScriptRoot

# Importa módulos principais
Import-Module "$scriptPath\modules\core\logging.psm1"
Import-Module "$scriptPath\modules\core\config.psm1"
Import-Module "$scriptPath\modules\core\ui.psm1"
Import-Module "$scriptPath\modules\core\utils.psm1"

# Inicia sessão de log
$sessionId = Start-Logging

# Verifica privilégios de administrador
Import-Module "$scriptPath\modules\environment\system.psm1"

$adminCheck = Test-AdminPrivileges
if (-not $adminCheck) {
    Write-Log "O script precisa ser executado como administrador" -Level "ERROR"
    Show-Notification "Este aplicativo requer privilégios de administrador." -Type "ERROR" -RequireConfirmation
    Stop-Logging $sessionId
    exit 1
}

# Verifica requisitos do sistema
$sysRequirements = Test-SystemRequirements
foreach ($req in $sysRequirements.GetEnumerator()) {
    if (-not $req.Value) {
        Write-Log "Requisito não atendido: $($req.Key)" -Level "ERROR"
        Show-Notification "Requisito do sistema não atendido: $($req.Key)" -Type "ERROR" -RequireConfirmation
    }
}

# Inicializa a interface do usuário
$mainForm = New-Object System.Windows.Forms.Form
$mainForm.Text = "WinDeckHelper"
$mainForm.Size = New-Object System.Drawing.Size(800, 600)
$mainForm.StartPosition = "CenterScreen"

# Adiciona controles à interface
# ... (implementação da interface)

# Função principal para executar operações selecionadas
function Start-Operations {
    param(
        [string[]]$SelectedOperations
    )
    
    $results = @{}
    
    foreach ($operation in $SelectedOperations) {
        Write-Log "Iniciando operação: $operation" -Level "INFO"
        
        switch ($operation) {
            "InstallDrivers" {
                Import-Module "$scriptPath\modules\installation\drivers.psm1"
                $results[$operation] = Install-Drivers
            }
            "InstallSoftware" {
                Import-Module "$scriptPath\modules\installation\software.psm1"
                $results[$operation] = Install-Software -Packages $config.Software
            }
            "InstallSDKs" {
                Import-Module "$scriptPath\modules\installation\sdk.psm1"
                $results[$operation] = Install-SDK -SDKs $config.SDKs
            }
            "InstallEmulators" {
                Import-Module "$scriptPath\modules\installation\emulators.psm1"
                $results[$operation] = Install-Emulators -Emulators $config.Emulators
            }
            "ApplyTweaks" {
                Import-Module "$scriptPath\modules\tweaks\performance.psm1"
                Import-Module "$scriptPath\modules\tweaks\bootloader.psm1"
                Import-Module "$scriptPath\modules\tweaks\display.psm1"
                
                $results[$operation] = @{
                    "Performance" = Apply-PerformanceTweaks -Tweaks $config.Tweaks.Performance
                    "Bootloader" = Apply-BootloaderTweaks -Tweaks $config.Tweaks.Bootloader
                    "Display" = Apply-DisplayTweaks -Tweaks $config.Tweaks.Display
                }
            }
        }
        
        Write-Log "Operação concluída: $operation" -Level "INFO"
    }
    
    return $results
}

# Exibe a interface e aguarda interação do usuário
$mainForm.ShowDialog()

# Encerra a sessão de log
Stop-Logging $sessionId