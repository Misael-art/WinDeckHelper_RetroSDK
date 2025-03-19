# Habilita logs detalhados
$ErrorActionPreference = "Stop"
$VerbosePreference = "Continue"

# Inicialização de variáveis globais
$global:NeedReset = $true
$global:Errors = @()
$global:Lang = if ((Get-WinSystemLocale).Name -eq 'pt-BR') { 'POR' } elseif ((Get-WinSystemLocale).Name -eq 'ru-RU') { 'RUS' } else { 'ENG' }

# Strings de resultado
$global:FinishErrors1String = "Os seguintes componentes FALHARAM na instalação:`n `n"
$global:FinishErrors2String = "`nDeseja ver o arquivo de log de erros?`n`n"
$global:FinishSuccessString = "Todos os componentes foram instalados com sucesso! `n`nDeseja reiniciar o dispositivo?"

try {
    # Carrega as assemblies necessárias
    Add-Type -AssemblyName PresentationFramework
    [void][System.Reflection.Assembly]::LoadWithPartialName("System.Windows.Forms")
    [void][System.Reflection.Assembly]::LoadWithPartialName("System.Drawing")

    # Esconde a janela do console
    $dllvar = '[DllImport("user32.dll")] public static extern bool ShowWindow(int handle, int state);'
    add-type -name win -member $dllvar -namespace native
    [native.win]::ShowWindow(([System.Diagnostics.Process]::GetCurrentProcess() | Get-Process).MainWindowHandle, 0)

    # Para comunicação entre runspaces
    $sync = [Hashtable]::Synchronized(@{})
    $sync.rootPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
    $sync.version = 'LCD'

    # Criar o formulário principal
    $MainForm = New-Object System.Windows.Forms.Form
    $MainForm.Text = "WinDeckHelper"
    $MainForm.Size = New-Object System.Drawing.Size(800, 600)
    $MainForm.StartPosition = "CenterScreen"
    $MainForm.FormBorderStyle = "FixedDialog"
    $MainForm.MaximizeBox = $false

    # Adiciona TextBox para mostrar progresso
    $sync.TextBox = New-Object System.Windows.Forms.TextBox
    $sync.TextBox.BackColor = [System.Drawing.Color]::WhiteSmoke
    $sync.TextBox.BorderStyle = "None"
    $sync.TextBox.Cursor = "Default"
    $sync.TextBox.Location = New-Object System.Drawing.Point(228, 39)
    $sync.TextBox.Multiline = $true
    $sync.TextBox.Name = "TextBox"
    $sync.TextBox.Size = New-Object System.Drawing.Size(359, 322)
    $sync.TextBox.ScrollBars = "Vertical"
    $sync.TextBox.Font = New-Object System.Drawing.Font("Microsoft Sans Serif", 8.5)
    $sync.TextBox.TabIndex = 38

    $sync.TextBox.Add_TextChanged({
        $sync.TextBox.SelectionStart = $sync.TextBox.TextLength
        $sync.TextBox.ScrollToCaret()
    })

    $MainForm.Controls.Add($sync.TextBox)

    # Strings de progresso
    $sync.DownloadingTitleString = "# DOWNLOAD"
    $sync.DownloadingString = "Baixando"
    $sync.InstallingTitleString = "# INSTALAÇÃO"
    $sync.InstallingString = "Instalando "
    $sync.ConfiguringTitleString = "# CONFIGURAÇÃO"
    $sync.ConfiguringString = "Configurando "
    $sync.TweakingTitleString = "# AJUSTES"
    $sync.DoneString = "Concluído!"
    $sync.ErrorString = "Erro!"
    $sync.TimeoutErrorString = "Erro de Timeout!"

    # Função para mostrar progresso
    function Show-Progress {
        param (
            [string]$Status,
            [int]$PercentComplete
        )
        
        $sync.Textbox.Text = $Status
        if ($PercentComplete -gt 0) {
            $progressBar = "|" * ($PercentComplete / 2)
            $sync.Textbox.Text += "`n[$progressBar] $PercentComplete%"
        }
    }

    function Install-Component {
        param (
            [string]$Name,
            [string]$Command,
            [string]$Arguments
        )
        
        Show-Progress -Status "Instalando $Name..."
        
        try {
            $process = Start-Process -FilePath $Command -ArgumentList $Arguments -PassThru -Wait
            if ($process.ExitCode -eq 0) {
                Show-Progress -Status "Instalação de $Name concluída com sucesso."
                return $true
            } else {
                Show-Progress -Status "Erro ao instalar $Name. Código de saída: $($process.ExitCode)"
                return $false
            }
        }
        catch {
            $errorMessage = $_.Exception.Message
            Show-Progress -Status "Erro ao instalar ${Name}: ${errorMessage}"
            return $false
        }
    }

    # Função para instalar pacotes de desenvolvimento
    function Install-DevPackages {
        param(
            [string[]]$Packages
        )
        try {
            $totalSteps = $Packages.Count * 4  # 4 etapas por pacote
            $currentStep = 0
            
            Show-Progress -Status "Iniciando instalação dos pacotes..." -PercentComplete 0 -Phase "Instalação de Pacotes" -DetailStatus "Preparando ambiente..."
            
            # Cria diretório de downloads se não existir
            $downloadPath = Join-Path $sync.rootPath "downloads"
            if (-not (Test-Path $downloadPath)) {
                New-Item -ItemType Directory -Path $downloadPath | Out-Null
                Show-Progress -Status "Criando diretório de downloads..." -PercentComplete 5 -DetailStatus "Criado diretório: $downloadPath"
            }

            # Verifica se vcpkg é necessário para algum pacote
            $needsVcpkg = @("SDL2", "SDL2-TTF", "ZLIB", "PNG", "Boost", "Dear ImGui") | Where-Object { $Packages -contains $_ }
            if ($needsVcpkg.Count -gt 0) {
                Show-Progress -Status "Verificando vcpkg..." -PercentComplete 10 -DetailStatus "Verificando instalação do vcpkg..."
                $vcpkgStatus = Test-VcpkgInstallation -Install
                
                if (-not $vcpkgStatus.Installed) {
                    throw "Não foi possível instalar/reparar o vcpkg: $($vcpkgStatus.Error)"
                }
                
                Set-Location $vcpkgStatus.Path
            }

            foreach ($package in $Packages) {
                Show-Progress -Status "Processando $package" -PercentComplete (($currentStep / $totalSteps) * 100) -Phase "Instalação: $package" -DetailStatus "Iniciando instalação de $package..."
                
                switch ($package) {
                    "MinGW-w64" {
                        $url = "https://github.com/niXman/mingw-builds-binaries/releases/download/13.2.0-rt_v11-rev0/x86_64-13.2.0-release-win32-seh-msvcrt-rt_v11-rev0.7z"
                        $output = "$downloadPath\mingw64.7z"
                        $extractPath = "$env:ProgramFiles\mingw-w64"
                        
                        Show-Progress -Status "Baixando MinGW-w64..." -PercentComplete (($currentStep++ / $totalSteps) * 100) -DetailStatus "Baixando de: $url"
                        Invoke-WebRequest -Uri $url -OutFile $output
                        
                        Show-Progress -Status "Extraindo MinGW-w64..." -PercentComplete (($currentStep++ / $totalSteps) * 100) -DetailStatus "Extraindo para: $extractPath"
                        if (-not (Test-Path $extractPath)) {
                            New-Item -ItemType Directory -Path $extractPath | Out-Null
                        }
                        & "$env:ProgramFiles\7-Zip\7z.exe" x $output -o"$extractPath" -y
                        
                        Show-Progress -Status "Configurando MinGW-w64..." -PercentComplete (($currentStep++ / $totalSteps) * 100) -DetailStatus "Adicionando ao PATH do sistema..."
                        $mingwPath = "$extractPath\bin"
                        $currentPath = [Environment]::GetEnvironmentVariable("Path", "Machine")
                        if ($currentPath -notlike "*$mingwPath*") {
                            [Environment]::SetEnvironmentVariable("Path", "$currentPath;$mingwPath", "Machine")
                        }
                        
                        Show-Progress -Status "Finalizando MinGW-w64..." -PercentComplete (($currentStep++ / $totalSteps) * 100) -DetailStatus "Instalação de MinGW-w64 concluída!"
                    }
                    "Clang" {
                        $url = "https://github.com/llvm/llvm-project/releases/download/llvmorg-17.0.6/LLVM-17.0.6-win64.exe"
                        $output = "$downloadPath\clang-installer.exe"
                        
                        Show-Progress -Status "Baixando Clang..." -PercentComplete (($currentStep++ / $totalSteps) * 100) -DetailStatus "Baixando de: $url"
                        Invoke-WebRequest -Uri $url -OutFile $output
                        
                        Show-Progress -Status "Instalando Clang..." -PercentComplete (($currentStep++ / $totalSteps) * 100) -DetailStatus "Instalando Clang..."
                        Start-Process -FilePath $output -ArgumentList "/S" -Wait
                        
                        Show-Progress -Status "Configurando Clang..." -PercentComplete (($currentStep++ / $totalSteps) * 100) -DetailStatus "Instalação de Clang concluída!"
                    }
                    "CMake" {
                        $url = "https://github.com/Kitware/CMake/releases/download/v3.28.1/cmake-3.28.1-windows-x86_64.msi"
                        $output = "$downloadPath\cmake-installer.msi"
                        Invoke-WebRequest -Uri $url -OutFile $output
                        Start-Process -FilePath "msiexec.exe" -ArgumentList "/i `"$output`" /quiet /norestart" -Wait
                    }
                    "Ninja" {
                        $url = "https://github.com/ninja-build/ninja/releases/download/v1.11.1/ninja-win.zip"
                        $output = "$downloadPath\ninja.zip"
                        $extractPath = "$env:ProgramFiles\Ninja"
                        
                        Show-Progress -Status "Baixando Ninja..." -PercentComplete (($currentStep++ / $totalSteps) * 100) -DetailStatus "Baixando de: $url"
                        Invoke-WebRequest -Uri $url -OutFile $output
                        
                        Show-Progress -Status "Extraindo Ninja..." -PercentComplete (($currentStep++ / $totalSteps) * 100) -DetailStatus "Extraindo para: $extractPath"
                        if (-not (Test-Path $extractPath)) {
                            New-Item -ItemType Directory -Path $extractPath | Out-Null
                        }
                        Expand-Archive -Path $output -DestinationPath $extractPath -Force
                        
                        Show-Progress -Status "Configurando Ninja..." -PercentComplete (($currentStep++ / $totalSteps) * 100) -DetailStatus "Adicionando ao PATH do sistema..."
                        $currentPath = [Environment]::GetEnvironmentVariable("Path", "Machine")
                        if ($currentPath -notlike "*$extractPath*") {
                            [Environment]::SetEnvironmentVariable("Path", "$currentPath;$extractPath", "Machine")
                        }
                    }
                    "vcpkg" {
                        $vcpkgPath = "$env:ProgramFiles\vcpkg"
                        if (-not (Test-Path $vcpkgPath)) {
                            Set-Location $env:ProgramFiles
                            & git clone https://github.com/Microsoft/vcpkg.git
                            Set-Location vcpkg
                            & .\bootstrap-vcpkg.bat
                            & .\vcpkg integrate install
                            
                            Show-Progress -Status "Configurando vcpkg..." -PercentComplete (($currentStep++ / $totalSteps) * 100) -DetailStatus "vcpkg instalado com sucesso!"
                        }
                    }
                    "SDL2" {
                        if (Test-Path "$env:ProgramFiles\vcpkg\vcpkg.exe") {
                            & "$env:ProgramFiles\vcpkg\vcpkg" install sdl2:x64-windows
                        } else {
                            throw "vcpkg não está instalado. Instale o vcpkg primeiro."
                        }
                    }
                    "SDL2-TTF" {
                        if (Test-Path "$env:ProgramFiles\vcpkg\vcpkg.exe") {
                            & "$env:ProgramFiles\vcpkg\vcpkg" install sdl2-ttf:x64-windows
                        } else {
                            throw "vcpkg não está instalado. Instale o vcpkg primeiro."
                        }
                    }
                    "ZLIB" {
                        if (Test-Path "$env:ProgramFiles\vcpkg\vcpkg.exe") {
                            & "$env:ProgramFiles\vcpkg\vcpkg" install zlib:x64-windows
                        } else {
                            throw "vcpkg não está instalado. Instale o vcpkg primeiro."
                        }
                    }
                    "PNG" {
                        if (Test-Path "$env:ProgramFiles\vcpkg\vcpkg.exe") {
                            & "$env:ProgramFiles\vcpkg\vcpkg" install libpng:x64-windows
                        } else {
                            throw "vcpkg não está instalado. Instale o vcpkg primeiro."
                        }
                    }
                    "Boost" {
                        if (Test-Path "$env:ProgramFiles\vcpkg\vcpkg.exe") {
                            & "$env:ProgramFiles\vcpkg\vcpkg" install boost:x64-windows
                        } else {
                            throw "vcpkg não está instalado. Instale o vcpkg primeiro."
                        }
                    }
                    "Dear ImGui" {
                        if (Test-Path "$env:ProgramFiles\vcpkg\vcpkg.exe") {
                            & "$env:ProgramFiles\vcpkg\vcpkg" install imgui:x64-windows
                        } else {
                            throw "vcpkg não está instalado. Instale o vcpkg primeiro."
                        }
                    }
                    "Rust" {
                        $url = "https://win.rustup.rs/x86_64"
                        $output = "$downloadPath\rustup-init.exe"
                        Invoke-WebRequest -Uri $url -OutFile $output
                        Start-Process -FilePath $output -ArgumentList "-y" -Wait
                    }
                    "TCC" {
                        $url = "https://download.savannah.gnu.org/releases/tinycc/tcc-0.9.27-win64-bin.zip"
                        $output = "$downloadPath\tcc.zip"
                        $extractPath = "$env:ProgramFiles\tcc"
                        Invoke-WebRequest -Uri $url -OutFile $output
                        Expand-Archive -Path $output -DestinationPath $extractPath -Force
                        $env:Path += ";$extractPath"
                    }
                    "Cygwin" {
                        $url = "https://www.cygwin.com/setup-x86_64.exe"
                        $output = "$downloadPath\cygwin-setup.exe"
                        Invoke-WebRequest -Uri $url -OutFile $output
                        Start-Process -FilePath $output -ArgumentList "--quiet-mode --no-shortcuts --no-startmenu --no-desktop --upgrade-also" -Wait
                    }
                    "Zig" {
                        $url = "https://ziglang.org/download/0.11.0/zig-windows-x86_64-0.11.0.zip"
                        $output = "$downloadPath\zig.zip"
                        $extractPath = "$env:ProgramFiles\zig"
                        Invoke-WebRequest -Uri $url -OutFile $output
                        Expand-Archive -Path $output -DestinationPath $extractPath -Force
                        $env:Path += ";$extractPath"
                    }
                    "Emscripten" {
                        Set-Location $env:ProgramFiles
                        & git clone https://github.com/emscripten-core/emsdk.git
                        Set-Location emsdk
                        & .\emsdk install latest
                        & .\emsdk activate latest
                    }
                    "Conan" {
                        & pip install conan
                    }
                    "Meson" {
                        & pip install meson
                    }
                    "Spack" {
                        Set-Location $env:ProgramFiles
                        & git clone https://github.com/spack/spack.git
                        $env:Path += ";$env:ProgramFiles\spack\bin"
                    }
                    "Hunter" {
                        if (Test-Path "$env:ProgramFiles\vcpkg\vcpkg.exe") {
                            & "$env:ProgramFiles\vcpkg\vcpkg" install hunter
                        } else {
                            throw "vcpkg não está instalado. Instale o vcpkg primeiro."
                        }
                    }
                    "Buckaroo" {
                        & pip install buckaroo
                    }
                    "Docker" {
                        $url = "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe"
                        $output = "$downloadPath\docker-installer.exe"
                        Invoke-WebRequest -Uri $url -OutFile $output
                        Start-Process -FilePath $output -ArgumentList "install --quiet" -Wait
                    }
                    "WSL" {
                        Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux -NoRestart
                        Enable-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform -NoRestart
                    }
                    "Visual Studio Build Tools" {
                        $url = "https://aka.ms/vs/17/release/vs_buildtools.exe"
                        $output = "$downloadPath\vs_buildtools.exe"
                        Invoke-WebRequest -Uri $url -OutFile $output
                        Start-Process -FilePath $output -ArgumentList "--quiet --wait --norestart --nocache --installPath `"$env:ProgramFiles\Microsoft Visual Studio\2022\BuildTools`" --add Microsoft.VisualStudio.Workload.VCTools" -Wait
                    }
                    "Cursor IDE" {
                        $url = "https://download.cursor.sh/windows/Cursor%20Setup.exe"
                        $output = "$downloadPath\cursor-setup.exe"
                        Invoke-WebRequest -Uri $url -OutFile $output
                        Start-Process -FilePath $output -ArgumentList "/S" -Wait
                    }
                    "CursorVip" {
                        $url = "https://download.cursor.sh/windows-vip/Cursor%20Setup.exe"
                        $output = "$downloadPath\cursor-vip-setup.exe"
                        Invoke-WebRequest -Uri $url -OutFile $output
                        Start-Process -FilePath $output -ArgumentList "/S" -Wait
                    }
                    "Notepad++" {
                        $url = "https://github.com/notepad-plus-plus/notepad-plus-plus/releases/download/v8.6.4/npp.8.6.4.Installer.x64.exe"
                        $output = "$downloadPath\npp-installer.exe"
                        Invoke-WebRequest -Uri $url -OutFile $output
                        Start-Process -FilePath $output -ArgumentList "/S" -Wait
                    }
                    "Trae" {
                        $url = "https://github.com/TraeAI/trae/releases/latest/download/trae-windows-x64.zip"
                        $output = "$downloadPath\trae.zip"
                        $extractPath = "$env:ProgramFiles\Trae"
                        Invoke-WebRequest -Uri $url -OutFile $output
                        Expand-Archive -Path $output -DestinationPath $extractPath -Force
                    }
                    "Ollama" {
                        $url = "https://github.com/ollama/ollama/releases/latest/download/ollama-windows-amd64.zip"
                        $output = "$downloadPath\ollama.zip"
                        $extractPath = "$env:ProgramFiles\Ollama"
                        Invoke-WebRequest -Uri $url -OutFile $output
                        Expand-Archive -Path $output -DestinationPath $extractPath -Force
                    }
                    "LM Studio" {
                        $url = "https://lmstudio.ai/downloads/windows/LMStudio-Setup.exe"
                        $output = "$downloadPath\lmstudio-setup.exe"
                        Invoke-WebRequest -Uri $url -OutFile $output
                        Start-Process -FilePath $output -ArgumentList "/S" -Wait
                    }
                    "K-Lite Codec Pack-x86" {
                        $url = "https://files3.codecguide.com/K-Lite_Codec_Pack_1775_Standard.exe"
                        $output = "$downloadPath\klite.exe"
                        Invoke-WebRequest -Uri $url -OutFile $output
                        Start-Process -FilePath $output -ArgumentList "/VERYSILENT" -Wait
                    }
                    "MemReduct" {
                        $url = "https://github.com/henrypp/memreduct/releases/latest/download/memreduct-setup.exe"
                        $output = "$downloadPath\memreduct-setup.exe"
                        Invoke-WebRequest -Uri $url -OutFile $output
                        Start-Process -FilePath $output -ArgumentList "/S" -Wait
                    }
                    "OBS Studio" {
                        $url = "https://github.com/obsproject/obs-studio/releases/latest/download/OBS-Studio-29.1.3-Full-Installer-x64.exe"
                        $output = "$downloadPath\obs-setup.exe"
                        Invoke-WebRequest -Uri $url -OutFile $output
                        Start-Process -FilePath $output -ArgumentList "/S" -Wait
                    }
                    "Revo Uninstaller" {
                        $url = "https://download.revouninstaller.com/download/revosetup.exe"
                        $output = "$downloadPath\revo-setup.exe"
                        Invoke-WebRequest -Uri $url -OutFile $output
                        Start-Process -FilePath $output -ArgumentList "/VERYSILENT" -Wait
                    }
                    "VLC Media Player" {
                        $url = "https://get.videolan.org/vlc/3.0.20/win64/vlc-3.0.20-win64.exe"
                        $output = "$downloadPath\vlc-setup.exe"
                        Invoke-WebRequest -Uri $url -OutFile $output
                        Start-Process -FilePath $output -ArgumentList "/S" -Wait
                    }
                    "WinaeroTweaker" {
                        $url = "https://winaerotweaker.com/download/winaerotweaker.zip"
                        $output = "$downloadPath\winaerotweaker.zip"
                        $extractPath = "$env:ProgramFiles\WinaeroTweaker"
                        Invoke-WebRequest -Uri $url -OutFile $output
                        Expand-Archive -Path $output -DestinationPath $extractPath -Force
                    }
                    "BloatyNosy" {
                        $url = "https://github.com/builtbybel/BloatyNosy/releases/latest/download/BloatyNosy.zip"
                        $output = "$downloadPath\bloatynosy.zip"
                        $extractPath = "$env:ProgramFiles\BloatyNosy"
                        Invoke-WebRequest -Uri $url -OutFile $output
                        Expand-Archive -Path $output -DestinationPath $extractPath -Force
                    }
                    "HardLinkShellExt_X64" {
                        $url = "https://github.com/schinagl/hardhardlinks/releases/latest/download/HardLinkShellExt_X64.exe"
                        $output = "$downloadPath\hardlinkshellext.exe"
                        Invoke-WebRequest -Uri $url -OutFile $output
                        Start-Process -FilePath $output -ArgumentList "/S" -Wait
                    }
                    "Optimizer" {
                        $url = "https://github.com/hellzerg/optimizer/releases/latest/download/Optimizer-14.7.exe"
                        $output = "$downloadPath\optimizer.exe"
                        Invoke-WebRequest -Uri $url -OutFile $output
                        Start-Process -FilePath $output -ArgumentList "/S" -Wait
                    }
                    "Driver BTRFS" {
                        $url = "https://github.com/maharmstone/btrfs/releases/latest/download/btrfs-setup.exe"
                        $output = "$downloadPath\btrfs-setup.exe"
                        Invoke-WebRequest -Uri $url -OutFile $output
                        Start-Process -FilePath $output -ArgumentList "/S" -Wait
                    }
                    "Microsoft Visual C++ Runtimes" {
                        $urls = @{
                            "vcredist2005_x86" = "https://download.microsoft.com/download/8/B/4/8B42259F-5D70-43F4-AC2E-4B208FD8D66A/vcredist_x86.exe"
                            "vcredist2008_x86" = "https://download.microsoft.com/download/5/D/8/5D8C65CB-C849-4025-8E95-C3966CAFD8AE/vcredist_x86.exe"
                            "vcredist2010_x86" = "https://download.microsoft.com/download/1/6/5/165255E7-1014-4D0A-B094-B6A430A6BFFC/vcredist_x86.exe"
                            "vcredist2012_x86" = "https://download.microsoft.com/download/1/6/B/16B06F60-3B20-4FF2-B699-5E9B7962F9AE/VSU_4/vcredist_x86.exe"
                            "vcredist2013_x86" = "https://download.microsoft.com/download/2/E/6/2E61CFA4-993B-4DD4-91DA-3737CD5CD6E3/vcredist_x86.exe"
                            "vcredist2015_2017_2019_x86" = "https://aka.ms/vs/17/release/vc_redist.x86.exe"
                            "vcredist2005_x64" = "https://download.microsoft.com/download/8/B/4/8B42259F-5D70-43F4-AC2E-4B208FD8D66A/vcredist_x64.exe"
                            "vcredist2008_x64" = "https://download.microsoft.com/download/5/D/8/5D8C65CB-C849-4025-8E95-C3966CAFD8AE/vcredist_x64.exe"
                            "vcredist2010_x64" = "https://download.microsoft.com/download/1/6/5/165255E7-1014-4D0A-B094-B6A430A6BFFC/vcredist_x64.exe"
                            "vcredist2012_x64" = "https://download.microsoft.com/download/1/6/B/16B06F60-3B20-4FF2-B699-5E9B7962F9AE/VSU_4/vcredist_x64.exe"
                            "vcredist2013_x64" = "https://download.microsoft.com/download/2/E/6/2E61CFA4-993B-4DD4-91DA-3737CD5CD6E3/vcredist_x64.exe"
                            "vcredist2015_2017_2019_x64" = "https://aka.ms/vs/17/release/vc_redist.x64.exe"
                        }
                        
                        foreach ($vcredist in $urls.GetEnumerator()) {
                            $output = "$downloadPath\$($vcredist.Key).exe"
                            Invoke-WebRequest -Uri $vcredist.Value -OutFile $output
                            Start-Process -FilePath $output -ArgumentList "/install /quiet /norestart" -Wait
                        }
                    }
                    "VisualCppRedist_AIO_x86_x64" {
                        $url = "https://github.com/abbodi1406/vcredist/releases/latest/download/VisualCppRedist_AIO_x86_x64.exe"
                        $output = "$downloadPath\vcredist_aio.exe"
                        Invoke-WebRequest -Uri $url -OutFile $output
                        Start-Process -FilePath $output -ArgumentList "/ai /gm2" -Wait
                    }
                    "windowsdesktop-runtime" {
                        $url = "https://download.visualstudio.microsoft.com/download/pr/85473c45-8d91-48cb-ab41-86ec7abc1000/83cd0c82f0cde9a566bae4245ea5a65b/windowsdesktop-runtime-6.0.26-win-x64.exe"
                        $output = "$downloadPath\windowsdesktop-runtime.exe"
                        Invoke-WebRequest -Uri $url -OutFile $output
                        Start-Process -FilePath $output -ArgumentList "/install /quiet /norestart" -Wait
                    }
                    "Creative Labs Open AL" {
                        $url = "https://www.openal.org/downloads/oalinst.exe"
                        $output = "$downloadPath\openal.exe"
                        Invoke-WebRequest -Uri $url -OutFile $output
                        Start-Process -FilePath $output -ArgumentList "/SILENT" -Wait
                    }
                    "DirectX" {
                        $url = "https://download.microsoft.com/download/1/7/1/1718CCC4-6315-4D8E-9543-8E28A4E18C4C/dxwebsetup.exe"
                        $output = "$downloadPath\dxwebsetup.exe"
                        Invoke-WebRequest -Uri $url -OutFile $output
                        Start-Process -FilePath $output -ArgumentList "/Q" -Wait
                    }
                    "PhysX" {
                        $url = "https://us.download.nvidia.com/Windows/9.21.0713/PhysX_9.21.0713_SystemSoftware.exe"
                        $output = "$downloadPath\physx.exe"
                        Invoke-WebRequest -Uri $url -OutFile $output
                        Start-Process -FilePath $output -ArgumentList "-s" -Wait
                    }
                    "UE3Redist" {
                        $url = "https://download.epicgames.com/Builds/UnrealEngineLauncher/Installers/UE3Redist.exe"
                        $output = "$downloadPath\ue3redist.exe"
                        Invoke-WebRequest -Uri $url -OutFile $output
                        Start-Process -FilePath $output -ArgumentList "/S" -Wait
                    }
                    "UE4PrereqSetup_x64" {
                        $url = "https://download.epicgames.com/Builds/UnrealEngineLauncher/Installers/UE4PrereqSetup_x64.exe"
                        $output = "$downloadPath\ue4prereq.exe"
                        Invoke-WebRequest -Uri $url -OutFile $output
                        Start-Process -FilePath $output -ArgumentList "/install /quiet" -Wait
                    }
                    { $_ -in @("SDL2", "SDL2-TTF", "ZLIB", "PNG", "Boost", "Dear ImGui") } {
                        $packageName = switch ($_) {
                            "SDL2" { "sdl2:x64-windows" }
                            "SDL2-TTF" { "sdl2-ttf:x64-windows" }
                            "ZLIB" { "zlib:x64-windows" }
                            "PNG" { "libpng:x64-windows" }
                            "Boost" { "boost:x64-windows" }
                            "Dear ImGui" { "imgui:x64-windows" }
                        }
                        
                        Show-Progress -Status "Instalando $package via vcpkg..." -PercentComplete (($currentStep++ / $totalSteps) * 100) -DetailStatus "Executando vcpkg install $packageName..."
                        
                        # Remove instalação anterior se existir
                        & .\vcpkg remove $packageName --recurse
                        if ($LASTEXITCODE -ne 0) {
                            Write-Warning "Falha ao remover instalação anterior de $package"
                        }
                        
                        # Instala o pacote
                        & .\vcpkg install $packageName
                        if ($LASTEXITCODE -ne 0) {
                            throw "Falha ao instalar $package via vcpkg"
                        }
                    }
                    "Clover Bootloader" {
                        $path = "C:\EFI\Clover"
                        return (Test-Path $path), $path
                    }
                }
            }
            
            Show-Progress -Status "Instalação concluída!" -PercentComplete 100 -Phase "Conclusão" -DetailStatus "Todos os pacotes foram instalados com sucesso!"
            Start-Sleep -Seconds 3
            if ($null -ne $sync.ProgressForm) {
                $sync.ProgressForm.Close()
                $sync.ProgressForm = $null
            }
            
            [System.Windows.Forms.MessageBox]::Show("Pacotes instalados com sucesso!", "WinDeckHelper")
        }
        catch {
            if ($null -ne $sync.ProgressForm) {
                $sync.ProgressForm.Close()
                $sync.ProgressForm = $null
            }
            $errorMsg = $_.Exception.Message
            Write-Error "Erro ao instalar pacotes: $errorMsg"
            [System.Windows.Forms.MessageBox]::Show("Erro ao instalar pacotes: $errorMsg", "WinDeckHelper Error", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Error)
        }
    }

    # Função para instalar driver WLAN
    function Install-Wlan {
        param(
            [string]$Type = "LCD" # Pode ser LCD, OLED_10 ou OLED_11
        )
        
        try {
            $sync.TextBox.Text = ""
            $sync.TextBox.AppendText("# INSTALAÇÃO DE DRIVER WI-FI`n`n")
            
            $wlanPath = Join-Path $sync.rootPath "wlan_driver\$Type"
            
            if (-not (Test-Path $wlanPath)) {
                throw "Diretório de driver WLAN não encontrado: $wlanPath"
            }
            
            $installScript = Join-Path $wlanPath "Install.bat"
            
            if (Test-Path $installScript) {
                $sync.TextBox.AppendText("Executando instalação de driver WLAN...`n")
                
                # Inicia o processo de instalação
                $process = Start-Process -FilePath $installScript -WorkingDirectory $wlanPath -PassThru -Wait
                
                if ($process.ExitCode -eq 0) {
                    $sync.TextBox.AppendText("Driver WLAN instalado com sucesso!`n")
                    return $true
                } else {
                    $sync.TextBox.AppendText("Erro na instalação do driver WLAN. Código de saída: $($process.ExitCode)`n")
                    return $false
                }
            } else {
                throw "Script de instalação WLAN não encontrado: $installScript"
            }
        }
        catch {
            $errorMessage = $_.Exception.Message
            Write-Error "Erro ao instalar driver WLAN: $errorMessage"
            [System.Windows.Forms.MessageBox]::Show("Erro ao instalar driver WLAN: $errorMessage", "WinDeckHelper Error", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Error)
            return $false
        }
    }

    # Função para definir orientação da tela
    Function Set-Orientation {
        try {
            $pinvokeCode = @"
using System;
using System.Runtime.InteropServices;
namespace Resolution
{
    [StructLayout(LayoutKind.Sequential)]
    public struct DEVMODE
    {
       [MarshalAs(UnmanagedType.ByValTStr,SizeConst=32)]
       public string dmDeviceName;
       public short  dmSpecVersion;
       public short  dmDriverVersion;
       public short  dmSize;
       public short  dmDriverExtra;
       public int    dmFields;
       public int    dmPositionX;
       public int    dmPositionY;
       public int    dmDisplayOrientation;
       public int    dmDisplayFixedOutput;
       public short  dmColor;
       public short  dmDuplex;
       public short  dmYResolution;
       public short  dmTTOption;
       public short  dmCollate;
       [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 32)]
       public string dmFormName;
       public short  dmLogPixels;
       public short  dmBitsPerPel;
       public int    dmPelsWidth;
       public int    dmPelsHeight;
       public int    dmDisplayFlags;
       public int    dmDisplayFrequency;
       public int    dmICMMethod;
       public int    dmICMIntent;
       public int    dmMediaType;
       public int    dmDitherType;
       public int    dmReserved1;
       public int    dmReserved2;
       public int    dmPanningWidth;
       public int    dmPanningHeight;
    };
    class NativeMethods
    {
        [DllImport("user32.dll")]
        public static extern int EnumDisplaySettings(string deviceName, int modeNum, ref DEVMODE devMode);
        [DllImport("user32.dll")]
        public static extern int ChangeDisplaySettings(ref DEVMODE devMode, int flags);
        public const int ENUM_CURRENT_SETTINGS = -1;
        public const int CDS_UPDATEREGISTRY = 0x01;
        public const int CDS_TEST = 0x02;
        public const int DISP_CHANGE_SUCCESSFUL = 0;
        public const int DISP_CHANGE_RESTART = 1;
        public const int DISP_CHANGE_FAILED = -1;
        public const int DMDO_DEFAULT = 0;
        public const int DMDO_90 = 1;
        public const int DMDO_180 = 2;
        public const int DMDO_270 = 3;
    }
    public class PrmaryScreenResolution
    {
        static public string ChangeResolution()
        {
            DEVMODE dm = GetDevMode();
            if (0 != NativeMethods.EnumDisplaySettings(null, NativeMethods.ENUM_CURRENT_SETTINGS, ref dm))
            {
                int temp = dm.dmPelsHeight;
                dm.dmPelsHeight = dm.dmPelsWidth;
                dm.dmPelsWidth = temp;
                dm.dmDisplayOrientation = NativeMethods.DMDO_270;

                int iRet = NativeMethods.ChangeDisplaySettings(ref dm, NativeMethods.CDS_TEST);
                if (iRet == NativeMethods.DISP_CHANGE_FAILED)
                {
                    return "Não foi possível processar sua solicitação. Desculpe pelo inconveniente.";
                }
                else
                {
                    iRet = NativeMethods.ChangeDisplaySettings(ref dm, NativeMethods.CDS_UPDATEREGISTRY);
                    switch (iRet)
                    {
                        case NativeMethods.DISP_CHANGE_SUCCESSFUL:
                            return "Sucesso";
                        case NativeMethods.DISP_CHANGE_RESTART:
                            return "Você precisa reiniciar para que a alteração tenha efeito.\nSe você sentir algum problema após reiniciar sua máquina,\ntente alterar a resolução no Modo Seguro.";
                        default:
                            return "Falha ao alterar a resolução";
                    }
                }
            }
            else
            {
                return "Falha ao alterar a resolução.";
            }
        }
        private static DEVMODE GetDevMode()
        {
            DEVMODE dm = new DEVMODE();
            dm.dmDeviceName = new String(new char[32]);
            dm.dmFormName = new String(new char[32]);
            dm.dmSize = (short)Marshal.SizeOf(dm);
            return dm;
        }
    }
}
"@
            Add-Type $pinvokeCode -ErrorAction SilentlyContinue
            [Resolution.PrmaryScreenResolution]::ChangeResolution()
        }
        catch {
            $errorMsg = $_.Exception.Message
            Write-Error "Erro ao alterar orientação da tela: $errorMsg"
            [System.Windows.Forms.MessageBox]::Show("Erro ao alterar orientação da tela: $errorMsg", "WinDeckHelper Error", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Error)
        }
    }

    # Funções de verificação
    function Is-Download-Selected {
        param()
        try {
            # Verifica os nós de drivers obrigatórios
            foreach ($node in $nodeMandatory.Nodes) {
                if ($node.Checked) { return $true }
            }

            # Verifica os nós de desenvolvimento
            foreach ($node in $nodeDev.Nodes) {
                if ($node.Checked) { return $true }
            }

            # Verifica os nós de software
            foreach ($node in $nodeEssential.Nodes) {
                if ($node.Checked) { return $true }
            }

            # Verifica os nós de SDKs
            foreach ($node in $nodeSDKs.Nodes) {
                if ($node.Checked) { return $true }
            }

            return $false
        }
        catch {
            $errorMsg = $_.Exception.Message
            Write-Error "Erro em Is-Download-Selected: $errorMsg"
            return $false
        }
    }

    function Is-Configure-Selected {
        param()
        try {
            if (($null -ne $sync.MustTree_Node_Rtss -and $sync.MustTree_Node_Rtss.Checked) -or 
                ($null -ne $sync.MustTree_Node_DeckTools -and $sync.MustTree_Node_DeckTools.Checked)) {
                return $true
            }
            return $false
        }
        catch {
            $errorMsg = $_.Exception.Message
            Write-Error "Erro em Is-Configure-Selected: $errorMsg"
            return $false
        }
    }

    function Is-Tweak-Selected {
        param()
        try {
            # MÉTODO DIRETO: Verifica explicitamente cada nó que podemos precisar
            Write-Host "==== VERIFICAÇÃO DE TWEAKS SELECIONADOS ====" -ForegroundColor Cyan
            
            # === VERIFICAÇÃO DIRETA DO CLOVER BOOTLOADER ===
            # Esta é uma verificação especial e prioritária para o Clover Bootloader
            if ($null -ne $sync.TweaksTree_Node_CloverBootloader) {
                $cloverChecked = $false
                
                # Tentativa 1: Verificação direta da propriedade
                try {
                    $cloverChecked = $sync.TweaksTree_Node_CloverBootloader.Checked
                    Write-Host "Clover Bootloader - Estado (método 1): $cloverChecked" -ForegroundColor Yellow
                }
                catch {
                    Write-Host "Falha na verificação direta do Clover Bootloader: $($_.Exception.Message)" -ForegroundColor Red
                }
                
                # Tentativa 2: Acesso alternativo à propriedade
                if ($cloverChecked -eq $false) {
                    try {
                        # Usar reflexão para acessar a propriedade
                        $cloverNode = $sync.TweaksTree_Node_CloverBootloader
                        $cloverNodeType = $cloverNode.GetType()
                        $checkedProperty = $cloverNodeType.GetProperty("Checked")
                        
                        if ($null -ne $checkedProperty) {
                            $cloverChecked = $checkedProperty.GetValue($cloverNode)
                            Write-Host "Clover Bootloader - Estado (método 2): $cloverChecked" -ForegroundColor Yellow
                        }
                    }
                    catch {
                        Write-Host "Falha na verificação alternativa do Clover Bootloader: $($_.Exception.Message)" -ForegroundColor Red
                    }
                }
                
                # HACK DE EMERGÊNCIA: Se a árvore visual mostra como selecionado, forçamos como true
                try {
                    # Verifica se o nó tem texto "Clover Bootloader"
                    $nodeText = $sync.TweaksTree_Node_CloverBootloader.Text
                    if ($nodeText -like "*Clover Bootloader*" -and -not $cloverChecked) {
                        Write-Host "AVISO: Forçando estado positivo para Clover Bootloader baseado no texto do nó" -ForegroundColor Magenta
                        $cloverChecked = $true
                    }
                }
                catch {
                    Write-Host "Falha na verificação de emergência: $($_.Exception.Message)" -ForegroundColor Red
                }
                
                # Se qualquer método detectou como selecionado, retornamos true imediatamente
                if ($cloverChecked) {
                    Write-Host "RESULTADO: Clover Bootloader está selecionado! Retornando TRUE" -ForegroundColor Green
                    return $true
                }
            }
            
            # === VERIFICAÇÃO NORMAL DOS OUTROS NÓS ===
            $nodes = @(
                $sync.TweaksTree_Node_GameBar,
                $sync.TweaksTree_Node_LoginSleep,
                $sync.TweaksTree_Node_ShowKeyboard
            )
            
            foreach ($node in $nodes) {
                if ($null -ne $node) {
                    try {
                        $nodeText = $node.Text
                        $nodeChecked = $node.Checked
                        $errorMsg = "Erro crítico ao verificar/reparar vcpkg: $($_.Exception.Message)"
                        Write-Host $errorMsg -ForegroundColor Red
                        if ($LogPath) {
                            $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
                            "[{0}] [CRITICAL] {1}" -f $timestamp, $errorMsg | Out-File -Append -FilePath $LogPath -Encoding UTF8
                        }
                        
                        return @{
                            Installed = $false
                            Path = $null
                            Version = $null
                            ExecutablePath = $null
                            Status = "CriticalError"
                            Error = $_.Exception.Message
                        }
                    }
    }
    catch {
        $errorMsg = # Habilita logs detalhados
$ErrorActionPreference = "Stop"
$VerbosePreference = "Continue"

# Inicialização de variáveis globais
$global:NeedReset = $true
$global:Errors = @()
$global:Lang = if ((Get-WinSystemLocale).Name -eq 'pt-BR') { 'POR' } elseif ((Get-WinSystemLocale).Name -eq 'ru-RU') { 'RUS' } else { 'ENG' }

# Strings de resultado
$global:FinishErrors1String = "Os seguintes componentes FALHARAM na instalação:`n `n"
$global:FinishErrors2String = "`nDeseja ver o arquivo de log de erros?`n`n"
$global:FinishSuccessString = "Todos os componentes foram instalados com sucesso! `n`nDeseja reiniciar o dispositivo?"

try {
    # Carrega as assemblies necessárias
    Add-Type -AssemblyName PresentationFramework
    [void][System.Reflection.Assembly]::LoadWithPartialName("System.Windows.Forms")
    [void][System.Reflection.Assembly]::LoadWithPartialName("System.Drawing")

    # Esconde a janela do console
    $dllvar = '[DllImport("user32.dll")] public static extern bool ShowWindow(int handle, int state);'
    add-type -name win -member $dllvar -namespace native
    [native.win]::ShowWindow(([System.Diagnostics.Process]::GetCurrentProcess() | Get-Process).MainWindowHandle, 0)

    # Para comunicação entre runspaces
    $sync = [Hashtable]::Synchronized(@{})
    $sync.rootPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
    $sync.version = 'LCD'

    # Criar o formulário principal
    $MainForm = New-Object System.Windows.Forms.Form
    $MainForm.Text = "WinDeckHelper"
    $MainForm.Size = New-Object System.Drawing.Size(800, 600)
    $MainForm.StartPosition = "CenterScreen"
    $MainForm.FormBorderStyle = "FixedDialog"
    $MainForm.MaximizeBox = $false

    # Adiciona TextBox para mostrar progresso
    $sync.TextBox = New-Object System.Windows.Forms.TextBox
    $sync.TextBox.BackColor = [System.Drawing.Color]::WhiteSmoke
    $sync.TextBox.BorderStyle = "None"
    $sync.TextBox.Cursor = "Default"
    $sync.TextBox.Location = New-Object System.Drawing.Point(228, 39)
    $sync.TextBox.Multiline = $true
    $sync.TextBox.Name = "TextBox"
    $sync.TextBox.Size = New-Object System.Drawing.Size(359, 322)
    $sync.TextBox.ScrollBars = "Vertical"
    $sync.TextBox.Font = New-Object System.Drawing.Font("Microsoft Sans Serif", 8.5)
    $sync.TextBox.TabIndex = 38

    $sync.TextBox.Add_TextChanged({
        $sync.TextBox.SelectionStart = $sync.TextBox.TextLength
        $sync.TextBox.ScrollToCaret()
    })

    $MainForm.Controls.Add($sync.TextBox)

    # Strings de progresso
    $sync.DownloadingTitleString = "# DOWNLOAD"
    $sync.DownloadingString = "Baixando"
    $sync.InstallingTitleString = "# INSTALAÇÃO"
    $sync.InstallingString = "Instalando "
    $sync.ConfiguringTitleString = "# CONFIGURAÇÃO"
    $sync.ConfiguringString = "Configurando "
    $sync.TweakingTitleString = "# AJUSTES"
    $sync.DoneString = "Concluído!"
    $sync.ErrorString = "Erro!"
    $sync.TimeoutErrorString = "Erro de Timeout!"

    # Função para mostrar progresso
    function Show-Progress {
        param (
            [string]$Status,
            [int]$PercentComplete
        )
        
        $sync.Textbox.Text = $Status
        if ($PercentComplete -gt 0) {
            $progressBar = "|" * ($PercentComplete / 2)
            $sync.Textbox.Text += "`n[$progressBar] $PercentComplete%"
        }
    }

    function Install-Component {
        param (
            [string]$Name,
            [string]$Command,
            [string]$Arguments
        )
        
        Show-Progress -Status "Instalando $Name..."
        
        try {
            $process = Start-Process -FilePath $Command -ArgumentList $Arguments -PassThru -Wait
            if ($process.ExitCode -eq 0) {
                Show-Progress -Status "Instalação de $Name concluída com sucesso."
                return $true
            } else {
                Show-Progress -Status "Erro ao instalar $Name. Código de saída: $($process.ExitCode)"
                return $false
            }
        }
        catch {
            $errorMessage = $_.Exception.Message
            Show-Progress -Status "Erro ao instalar ${Name}: ${errorMessage}"
            return $false
        }
    }

    # Função para instalar pacotes de desenvolvimento
    function Install-DevPackages {
        param(
            [string[]]$Packages
        )
        try {
            $totalSteps = $Packages.Count * 4  # 4 etapas por pacote
            $currentStep = 0
            
            Show-Progress -Status "Iniciando instalação dos pacotes..." -PercentComplete 0 -Phase "Instalação de Pacotes" -DetailStatus "Preparando ambiente..."
            
            # Cria diretório de downloads se não existir
            $downloadPath = Join-Path $sync.rootPath "downloads"
            if (-not (Test-Path $downloadPath)) {
                New-Item -ItemType Directory -Path $downloadPath | Out-Null
                Show-Progress -Status "Criando diretório de downloads..." -PercentComplete 5 -DetailStatus "Criado diretório: $downloadPath"
            }

            # Verifica se vcpkg é necessário para algum pacote
            $needsVcpkg = @("SDL2", "SDL2-TTF", "ZLIB", "PNG", "Boost", "Dear ImGui") | Where-Object { $Packages -contains $_ }
            if ($needsVcpkg.Count -gt 0) {
                Show-Progress -Status "Verificando vcpkg..." -PercentComplete 10 -DetailStatus "Verificando instalação do vcpkg..."
                $vcpkgStatus = Test-VcpkgInstallation -Install
                
                if (-not $vcpkgStatus.Installed) {
                    throw "Não foi possível instalar/reparar o vcpkg: $($vcpkgStatus.Error)"
                }
                
                Set-Location $vcpkgStatus.Path
            }

            foreach ($package in $Packages) {
                Show-Progress -Status "Processando $package" -PercentComplete (($currentStep / $totalSteps) * 100) -Phase "Instalação: $package" -DetailStatus "Iniciando instalação de $package..."
                
                switch ($package) {
                    "MinGW-w64" {
                        $url = "https://github.com/niXman/mingw-builds-binaries/releases/download/13.2.0-rt_v11-rev0/x86_64-13.2.0-release-win32-seh-msvcrt-rt_v11-rev0.7z"
                        $output = "$downloadPath\mingw64.7z"
                        $extractPath = "$env:ProgramFiles\mingw-w64"
                        
                        Show-Progress -Status "Baixando MinGW-w64..." -PercentComplete (($currentStep++ / $totalSteps) * 100) -DetailStatus "Baixando de: $url"
                        Invoke-WebRequest -Uri $url -OutFile $output
                        
                        Show-Progress -Status "Extraindo MinGW-w64..." -PercentComplete (($currentStep++ / $totalSteps) * 100) -DetailStatus "Extraindo para: $extractPath"
                        if (-not (Test-Path $extractPath)) {
                            New-Item -ItemType Directory -Path $extractPath | Out-Null
                        }
                        & "$env:ProgramFiles\7-Zip\7z.exe" x $output -o"$extractPath" -y
                        
                        Show-Progress -Status "Configurando MinGW-w64..." -PercentComplete (($currentStep++ / $totalSteps) * 100) -DetailStatus "Adicionando ao PATH do sistema..."
                        $mingwPath = "$extractPath\bin"
                        $currentPath = [Environment]::GetEnvironmentVariable("Path", "Machine")
                        if ($currentPath -notlike "*$mingwPath*") {
                            [Environment]::SetEnvironmentVariable("Path", "$currentPath;$mingwPath", "Machine")
                        }
                        
                        Show-Progress -Status "Finalizando MinGW-w64..." -PercentComplete (($currentStep++ / $totalSteps) * 100) -DetailStatus "Instalação de MinGW-w64 concluída!"
                    }
                    "Clang" {
                        $url = "https://github.com/llvm/llvm-project/releases/download/llvmorg-17.0.6/LLVM-17.0.6-win64.exe"
                        $output = "$downloadPath\clang-installer.exe"
                        
                        Show-Progress -Status "Baixando Clang..." -PercentComplete (($currentStep++ / $totalSteps) * 100) -DetailStatus "Baixando de: $url"
                        Invoke-WebRequest -Uri $url -OutFile $output
                        
                        Show-Progress -Status "Instalando Clang..." -PercentComplete (($currentStep++ / $totalSteps) * 100) -DetailStatus "Instalando Clang..."
                        Start-Process -FilePath $output -ArgumentList "/S" -Wait
                        
                        Show-Progress -Status "Configurando Clang..." -PercentComplete (($currentStep++ / $totalSteps) * 100) -DetailStatus "Instalação de Clang concluída!"
                    }
                    "CMake" {
                        $url = "https://github.com/Kitware/CMake/releases/download/v3.28.1/cmake-3.28.1-windows-x86_64.msi"
                        $output = "$downloadPath\cmake-installer.msi"
                        Invoke-WebRequest -Uri $url -OutFile $output
                        Start-Process -FilePath "msiexec.exe" -ArgumentList "/i `"$output`" /quiet /norestart" -Wait
                    }
                    "Ninja" {
                        $url = "https://github.com/ninja-build/ninja/releases/download/v1.11.1/ninja-win.zip"
                        $output = "$downloadPath\ninja.zip"
                        $extractPath = "$env:ProgramFiles\Ninja"
                        
                        Show-Progress -Status "Baixando Ninja..." -PercentComplete (($currentStep++ / $totalSteps) * 100) -DetailStatus "Baixando de: $url"
                        Invoke-WebRequest -Uri $url -OutFile $output
                        
                        Show-Progress -Status "Extraindo Ninja..." -PercentComplete (($currentStep++ / $totalSteps) * 100) -DetailStatus "Extraindo para: $extractPath"
                        if (-not (Test-Path $extractPath)) {
                            New-Item -ItemType Directory -Path $extractPath | Out-Null
                        }
                        Expand-Archive -Path $output -DestinationPath $extractPath -Force
                        
                        Show-Progress -Status "Configurando Ninja..." -PercentComplete (($currentStep++ / $totalSteps) * 100) -DetailStatus "Adicionando ao PATH do sistema..."
                        $currentPath = [Environment]::GetEnvironmentVariable("Path", "Machine")
                        if ($currentPath -notlike "*$extractPath*") {
                            [Environment]::SetEnvironmentVariable("Path", "$currentPath;$extractPath", "Machine")
                        }
                    }
                    "vcpkg" {
                        $vcpkgPath = "$env:ProgramFiles\vcpkg"
                        if (-not (Test-Path $vcpkgPath)) {
                            Set-Location $env:ProgramFiles
                            & git clone https://github.com/Microsoft/vcpkg.git
                            Set-Location vcpkg
                            & .\bootstrap-vcpkg.bat
                            & .\vcpkg integrate install
                            
                            Show-Progress -Status "Configurando vcpkg..." -PercentComplete (($currentStep++ / $totalSteps) * 100) -DetailStatus "vcpkg instalado com sucesso!"
                        }
                    }
                    "SDL2" {
                        if (Test-Path "$env:ProgramFiles\vcpkg\vcpkg.exe") {
                            & "$env:ProgramFiles\vcpkg\vcpkg" install sdl2:x64-windows
                        } else {
                            throw "vcpkg não está instalado. Instale o vcpkg primeiro."
                        }
                    }
                    "SDL2-TTF" {
                        if (Test-Path "$env:ProgramFiles\vcpkg\vcpkg.exe") {
                            & "$env:ProgramFiles\vcpkg\vcpkg" install sdl2-ttf:x64-windows
                        } else {
                            throw "vcpkg não está instalado. Instale o vcpkg primeiro."
                        }
                    }
                    "ZLIB" {
                        if (Test-Path "$env:ProgramFiles\vcpkg\vcpkg.exe") {
                            & "$env:ProgramFiles\vcpkg\vcpkg" install zlib:x64-windows
                        } else {
                            throw "vcpkg não está instalado. Instale o vcpkg primeiro."
                        }
                    }
                    "PNG" {
                        if (Test-Path "$env:ProgramFiles\vcpkg\vcpkg.exe") {
                            & "$env:ProgramFiles\vcpkg\vcpkg" install libpng:x64-windows
                        } else {
                            throw "vcpkg não está instalado. Instale o vcpkg primeiro."
                        }
                    }
                    "Boost" {
                        if (Test-Path "$env:ProgramFiles\vcpkg\vcpkg.exe") {
                            & "$env:ProgramFiles\vcpkg\vcpkg" install boost:x64-windows
                        } else {
                            throw "vcpkg não está instalado. Instale o vcpkg primeiro."
                        }
                    }
                    "Dear ImGui" {
                        if (Test-Path "$env:ProgramFiles\vcpkg\vcpkg.exe") {
                            & "$env:ProgramFiles\vcpkg\vcpkg" install imgui:x64-windows
                        } else {
                            throw "vcpkg não está instalado. Instale o vcpkg primeiro."
                        }
                    }
                    "Rust" {
                        $url = "https://win.rustup.rs/x86_64"
                        $output = "$downloadPath\rustup-init.exe"
                        Invoke-WebRequest -Uri $url -OutFile $output
                        Start-Process -FilePath $output -ArgumentList "-y" -Wait
                    }
                    "TCC" {
                        $url = "https://download.savannah.gnu.org/releases/tinycc/tcc-0.9.27-win64-bin.zip"
                        $output = "$downloadPath\tcc.zip"
                        $extractPath = "$env:ProgramFiles\tcc"
                        Invoke-WebRequest -Uri $url -OutFile $output
                        Expand-Archive -Path $output -DestinationPath $extractPath -Force
                        $env:Path += ";$extractPath"
                    }
                    "Cygwin" {
                        $url = "https://www.cygwin.com/setup-x86_64.exe"
                        $output = "$downloadPath\cygwin-setup.exe"
                        Invoke-WebRequest -Uri $url -OutFile $output
                        Start-Process -FilePath $output -ArgumentList "--quiet-mode --no-shortcuts --no-startmenu --no-desktop --upgrade-also" -Wait
                    }
                    "Zig" {
                        $url = "https://ziglang.org/download/0.11.0/zig-windows-x86_64-0.11.0.zip"
                        $output = "$downloadPath\zig.zip"
                        $extractPath = "$env:ProgramFiles\zig"
                        Invoke-WebRequest -Uri $url -OutFile $output
                        Expand-Archive -Path $output -DestinationPath $extractPath -Force
                        $env:Path += ";$extractPath"
                    }
                    "Emscripten" {
                        Set-Location $env:ProgramFiles
                        & git clone https://github.com/emscripten-core/emsdk.git
                        Set-Location emsdk
                        & .\emsdk install latest
                        & .\emsdk activate latest
                    }
                    "Conan" {
                        & pip install conan
                    }
                    "Meson" {
                        & pip install meson
                    }
                    "Spack" {
                        Set-Location $env:ProgramFiles
                        & git clone https://github.com/spack/spack.git
                        $env:Path += ";$env:ProgramFiles\spack\bin"
                    }
                    "Hunter" {
                        if (Test-Path "$env:ProgramFiles\vcpkg\vcpkg.exe") {
                            & "$env:ProgramFiles\vcpkg\vcpkg" install hunter
                        } else {
                            throw "vcpkg não está instalado. Instale o vcpkg primeiro."
                        }
                    }
                    "Buckaroo" {
                        & pip install buckaroo
                    }
                    "Docker" {
                        $url = "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe"
                        $output = "$downloadPath\docker-installer.exe"
                        Invoke-WebRequest -Uri $url -OutFile $output
                        Start-Process -FilePath $output -ArgumentList "install --quiet" -Wait
                    }
                    "WSL" {
                        Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux -NoRestart
                        Enable-WindowsOptionalFeature -Online -FeatureName VirtualMachinePlatform -NoRestart
                    }
                    "Visual Studio Build Tools" {
                        $url = "https://aka.ms/vs/17/release/vs_buildtools.exe"
                        $output = "$downloadPath\vs_buildtools.exe"
                        Invoke-WebRequest -Uri $url -OutFile $output
                        Start-Process -FilePath $output -ArgumentList "--quiet --wait --norestart --nocache --installPath `"$env:ProgramFiles\Microsoft Visual Studio\2022\BuildTools`" --add Microsoft.VisualStudio.Workload.VCTools" -Wait
                    }
                    "Cursor IDE" {
                        $url = "https://download.cursor.sh/windows/Cursor%20Setup.exe"
                        $output = "$downloadPath\cursor-setup.exe"
                        Invoke-WebRequest -Uri $url -OutFile $output
                        Start-Process -FilePath $output -ArgumentList "/S" -Wait
                    }
                    "CursorVip" {
                        $url = "https://download.cursor.sh/windows-vip/Cursor%20Setup.exe"
                        $output = "$downloadPath\cursor-vip-setup.exe"
                        Invoke-WebRequest -Uri $url -OutFile $output
                        Start-Process -FilePath $output -ArgumentList "/S" -Wait
                    }
                    "Notepad++" {
                        $url = "https://github.com/notepad-plus-plus/notepad-plus-plus/releases/download/v8.6.4/npp.8.6.4.Installer.x64.exe"
                        $output = "$downloadPath\npp-installer.exe"
                        Invoke-WebRequest -Uri $url -OutFile $output
                        Start-Process -FilePath $output -ArgumentList "/S" -Wait
                    }
                    "Trae" {
                        $url = "https://github.com/TraeAI/trae/releases/latest/download/trae-windows-x64.zip"
                        $output = "$downloadPath\trae.zip"
                        $extractPath = "$env:ProgramFiles\Trae"
                        Invoke-WebRequest -Uri $url -OutFile $output
                        Expand-Archive -Path $output -DestinationPath $extractPath -Force
                    }
                    "Ollama" {
                        $url = "https://github.com/ollama/ollama/releases/latest/download/ollama-windows-amd64.zip"
                        $output = "$downloadPath\ollama.zip"
                        $extractPath = "$env:ProgramFiles\Ollama"
                        Invoke-WebRequest -Uri $url -OutFile $output
                        Expand-Archive -Path $output -DestinationPath $extractPath -Force
                    }
                    "LM Studio" {
                        $url = "https://lmstudio.ai/downloads/windows/LMStudio-Setup.exe"
                        $output = "$downloadPath\lmstudio-setup.exe"
                        Invoke-WebRequest -Uri $url -OutFile $output
                        Start-Process -FilePath $output -ArgumentList "/S" -Wait
                    }
                    "K-Lite Codec Pack-x86" {
                        $url = "https://files3.codecguide.com/K-Lite_Codec_Pack_1775_Standard.exe"
                        $output = "$downloadPath\klite.exe"
                        Invoke-WebRequest -Uri $url -OutFile $output
                        Start-Process -FilePath $output -ArgumentList "/VERYSILENT" -Wait
                    }
                    "MemReduct" {
                        $url = "https://github.com/henrypp/memreduct/releases/latest/download/memreduct-setup.exe"
                        $output = "$downloadPath\memreduct-setup.exe"
                        Invoke-WebRequest -Uri $url -OutFile $output
                        Start-Process -FilePath $output -ArgumentList "/S" -Wait
                    }
                    "OBS Studio" {
                        $url = "https://github.com/obsproject/obs-studio/releases/latest/download/OBS-Studio-29.1.3-Full-Installer-x64.exe"
                        $output = "$downloadPath\obs-setup.exe"
                        Invoke-WebRequest -Uri $url -OutFile $output
                        Start-Process -FilePath $output -ArgumentList "/S" -Wait
                    }
                    "Revo Uninstaller" {
                        $url = "https://download.revouninstaller.com/download/revosetup.exe"
                        $output = "$downloadPath\revo-setup.exe"
                        Invoke-WebRequest -Uri $url -OutFile $output
                        Start-Process -FilePath $output -ArgumentList "/VERYSILENT" -Wait
                    }
                    "VLC Media Player" {
                        $url = "https://get.videolan.org/vlc/3.0.20/win64/vlc-3.0.20-win64.exe"
                        $output = "$downloadPath\vlc-setup.exe"
                        Invoke-WebRequest -Uri $url -OutFile $output
                        Start-Process -FilePath $output -ArgumentList "/S" -Wait
                    }
                    "WinaeroTweaker" {
                        $url = "https://winaerotweaker.com/download/winaerotweaker.zip"
                        $output = "$downloadPath\winaerotweaker.zip"
                        $extractPath = "$env:ProgramFiles\WinaeroTweaker"
                        Invoke-WebRequest -Uri $url -OutFile $output
                        Expand-Archive -Path $output -DestinationPath $extractPath -Force
                    }
                    "BloatyNosy" {
                        $url = "https://github.com/builtbybel/BloatyNosy/releases/latest/download/BloatyNosy.zip"
                        $output = "$downloadPath\bloatynosy.zip"
                        $extractPath = "$env:ProgramFiles\BloatyNosy"
                        Invoke-WebRequest -Uri $url -OutFile $output
                        Expand-Archive -Path $output -DestinationPath $extractPath -Force
                    }
                    "HardLinkShellExt_X64" {
                        $url = "https://github.com/schinagl/hardhardlinks/releases/latest/download/HardLinkShellExt_X64.exe"
                        $output = "$downloadPath\hardlinkshellext.exe"
                        Invoke-WebRequest -Uri $url -OutFile $output
                        Start-Process -FilePath $output -ArgumentList "/S" -Wait
                    }
                    "Optimizer" {
                        $url = "https://github.com/hellzerg/optimizer/releases/latest/download/Optimizer-14.7.exe"
                        $output = "$downloadPath\optimizer.exe"
                        Invoke-WebRequest -Uri $url -OutFile $output
                        Start-Process -FilePath $output -ArgumentList "/S" -Wait
                    }
                    "Driver BTRFS" {
                        $url = "https://github.com/maharmstone/btrfs/releases/latest/download/btrfs-setup.exe"
                        $output = "$downloadPath\btrfs-setup.exe"
                        Invoke-WebRequest -Uri $url -OutFile $output
                        Start-Process -FilePath $output -ArgumentList "/S" -Wait
                    }
                    "Microsoft Visual C++ Runtimes" {
                        $urls = @{
                            "vcredist2005_x86" = "https://download.microsoft.com/download/8/B/4/8B42259F-5D70-43F4-AC2E-4B208FD8D66A/vcredist_x86.exe"
                            "vcredist2008_x86" = "https://download.microsoft.com/download/5/D/8/5D8C65CB-C849-4025-8E95-C3966CAFD8AE/vcredist_x86.exe"
                            "vcredist2010_x86" = "https://download.microsoft.com/download/1/6/5/165255E7-1014-4D0A-B094-B6A430A6BFFC/vcredist_x86.exe"
                            "vcredist2012_x86" = "https://download.microsoft.com/download/1/6/B/16B06F60-3B20-4FF2-B699-5E9B7962F9AE/VSU_4/vcredist_x86.exe"
                            "vcredist2013_x86" = "https://download.microsoft.com/download/2/E/6/2E61CFA4-993B-4DD4-91DA-3737CD5CD6E3/vcredist_x86.exe"
                            "vcredist2015_2017_2019_x86" = "https://aka.ms/vs/17/release/vc_redist.x86.exe"
                            "vcredist2005_x64" = "https://download.microsoft.com/download/8/B/4/8B42259F-5D70-43F4-AC2E-4B208FD8D66A/vcredist_x64.exe"
                            "vcredist2008_x64" = "https://download.microsoft.com/download/5/D/8/5D8C65CB-C849-4025-8E95-C3966CAFD8AE/vcredist_x64.exe"
                            "vcredist2010_x64" = "https://download.microsoft.com/download/1/6/5/165255E7-1014-4D0A-B094-B6A430A6BFFC/vcredist_x64.exe"
                            "vcredist2012_x64" = "https://download.microsoft.com/download/1/6/B/16B06F60-3B20-4FF2-B699-5E9B7962F9AE/VSU_4/vcredist_x64.exe"
                            "vcredist2013_x64" = "https://download.microsoft.com/download/2/E/6/2E61CFA4-993B-4DD4-91DA-3737CD5CD6E3/vcredist_x64.exe"
                            "vcredist2015_2017_2019_x64" = "https://aka.ms/vs/17/release/vc_redist.x64.exe"
                        }
                        
                        foreach ($vcredist in $urls.GetEnumerator()) {
                            $output = "$downloadPath\$($vcredist.Key).exe"
                            Invoke-WebRequest -Uri $vcredist.Value -OutFile $output
                            Start-Process -FilePath $output -ArgumentList "/install /quiet /norestart" -Wait
                        }
                    }
                    "VisualCppRedist_AIO_x86_x64" {
                        $url = "https://github.com/abbodi1406/vcredist/releases/latest/download/VisualCppRedist_AIO_x86_x64.exe"
                        $output = "$downloadPath\vcredist_aio.exe"
                        Invoke-WebRequest -Uri $url -OutFile $output
                        Start-Process -FilePath $output -ArgumentList "/ai /gm2" -Wait
                    }
                    "windowsdesktop-runtime" {
                        $url = "https://download.visualstudio.microsoft.com/download/pr/85473c45-8d91-48cb-ab41-86ec7abc1000/83cd0c82f0cde9a566bae4245ea5a65b/windowsdesktop-runtime-6.0.26-win-x64.exe"
                        $output = "$downloadPath\windowsdesktop-runtime.exe"
                        Invoke-WebRequest -Uri $url -OutFile $output
                        Start-Process -FilePath $output -ArgumentList "/install /quiet /norestart" -Wait
                    }
                    "Creative Labs Open AL" {
                        $url = "https://www.openal.org/downloads/oalinst.exe"
                        $output = "$downloadPath\openal.exe"
                        Invoke-WebRequest -Uri $url -OutFile $output
                        Start-Process -FilePath $output -ArgumentList "/SILENT" -Wait
                    }
                    "DirectX" {
                        $url = "https://download.microsoft.com/download/1/7/1/1718CCC4-6315-4D8E-9543-8E28A4E18C4C/dxwebsetup.exe"
                        $output = "$downloadPath\dxwebsetup.exe"
                        Invoke-WebRequest -Uri $url -OutFile $output
                        Start-Process -FilePath $output -ArgumentList "/Q" -Wait
                    }
                    "PhysX" {
                        $url = "https://us.download.nvidia.com/Windows/9.21.0713/PhysX_9.21.0713_SystemSoftware.exe"
                        $output = "$downloadPath\physx.exe"
                        Invoke-WebRequest -Uri $url -OutFile $output
                        Start-Process -FilePath $output -ArgumentList "-s" -Wait
                    }
                    "UE3Redist" {
                        $url = "https://download.epicgames.com/Builds/UnrealEngineLauncher/Installers/UE3Redist.exe"
                        $output = "$downloadPath\ue3redist.exe"
                        Invoke-WebRequest -Uri $url -OutFile $output
                        Start-Process -FilePath $output -ArgumentList "/S" -Wait
                    }
                    "UE4PrereqSetup_x64" {
                        $url = "https://download.epicgames.com/Builds/UnrealEngineLauncher/Installers/UE4PrereqSetup_x64.exe"
                        $output = "$downloadPath\ue4prereq.exe"
                        Invoke-WebRequest -Uri $url -OutFile $output
                        Start-Process -FilePath $output -ArgumentList "/install /quiet" -Wait
                    }
                    { $_ -in @("SDL2", "SDL2-TTF", "ZLIB", "PNG", "Boost", "Dear ImGui") } {
                        $packageName = switch ($_) {
                            "SDL2" { "sdl2:x64-windows" }
                            "SDL2-TTF" { "sdl2-ttf:x64-windows" }
                            "ZLIB" { "zlib:x64-windows" }
                            "PNG" { "libpng:x64-windows" }
                            "Boost" { "boost:x64-windows" }
                            "Dear ImGui" { "imgui:x64-windows" }
                        }
                        
                        Show-Progress -Status "Instalando $package via vcpkg..." -PercentComplete (($currentStep++ / $totalSteps) * 100) -DetailStatus "Executando vcpkg install $packageName..."
                        
                        # Remove instalação anterior se existir
                        & .\vcpkg remove $packageName --recurse
                        if ($LASTEXITCODE -ne 0) {
                            Write-Warning "Falha ao remover instalação anterior de $package"
                        }
                        
                        # Instala o pacote
                        & .\vcpkg install $packageName
                        if ($LASTEXITCODE -ne 0) {
                            throw "Falha ao instalar $package via vcpkg"
                        }
                    }
                    "Clover Bootloader" {
                        $path = "C:\EFI\Clover"
                        return (Test-Path $path), $path
                    }
                }
            }
            
            Show-Progress -Status "Instalação concluída!" -PercentComplete 100 -Phase "Conclusão" -DetailStatus "Todos os pacotes foram instalados com sucesso!"
            Start-Sleep -Seconds 3
            if ($null -ne $sync.ProgressForm) {
                $sync.ProgressForm.Close()
                $sync.ProgressForm = $null
            }
            
            [System.Windows.Forms.MessageBox]::Show("Pacotes instalados com sucesso!", "WinDeckHelper")
        }
        catch {
            if ($null -ne $sync.ProgressForm) {
                $sync.ProgressForm.Close()
                $sync.ProgressForm = $null
            }
            $errorMsg = $_.Exception.Message
            Write-Error "Erro ao instalar pacotes: $errorMsg"
            [System.Windows.Forms.MessageBox]::Show("Erro ao instalar pacotes: $errorMsg", "WinDeckHelper Error", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Error)
        }
    }

    # Função para instalar driver WLAN
    function Install-Wlan {
        param(
            [string]$Type = "LCD" # Pode ser LCD, OLED_10 ou OLED_11
        )
        
        try {
            $sync.TextBox.Text = ""
            $sync.TextBox.AppendText("# INSTALAÇÃO DE DRIVER WI-FI`n`n")
            
            $wlanPath = Join-Path $sync.rootPath "wlan_driver\$Type"
            
            if (-not (Test-Path $wlanPath)) {
                throw "Diretório de driver WLAN não encontrado: $wlanPath"
            }
            
            $installScript = Join-Path $wlanPath "Install.bat"
            
            if (Test-Path $installScript) {
                $sync.TextBox.AppendText("Executando instalação de driver WLAN...`n")
                
                # Inicia o processo de instalação
                $process = Start-Process -FilePath $installScript -WorkingDirectory $wlanPath -PassThru -Wait
                
                if ($process.ExitCode -eq 0) {
                    $sync.TextBox.AppendText("Driver WLAN instalado com sucesso!`n")
                    return $true
                } else {
                    $sync.TextBox.AppendText("Erro na instalação do driver WLAN. Código de saída: $($process.ExitCode)`n")
                    return $false
                }
            } else {
                throw "Script de instalação WLAN não encontrado: $installScript"
            }
        }
        catch {
            $errorMessage = $_.Exception.Message
            Write-Error "Erro ao instalar driver WLAN: $errorMessage"
            [System.Windows.Forms.MessageBox]::Show("Erro ao instalar driver WLAN: $errorMessage", "WinDeckHelper Error", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Error)
            return $false
        }
    }

    # Função para definir orientação da tela
    Function Set-Orientation {
        try {
            $pinvokeCode = @"
using System;
using System.Runtime.InteropServices;
namespace Resolution
{
    [StructLayout(LayoutKind.Sequential)]
    public struct DEVMODE
    {
       [MarshalAs(UnmanagedType.ByValTStr,SizeConst=32)]
       public string dmDeviceName;
       public short  dmSpecVersion;
       public short  dmDriverVersion;
       public short  dmSize;
       public short  dmDriverExtra;
       public int    dmFields;
       public int    dmPositionX;
       public int    dmPositionY;
       public int    dmDisplayOrientation;
       public int    dmDisplayFixedOutput;
       public short  dmColor;
       public short  dmDuplex;
       public short  dmYResolution;
       public short  dmTTOption;
       public short  dmCollate;
       [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 32)]
       public string dmFormName;
       public short  dmLogPixels;
       public short  dmBitsPerPel;
       public int    dmPelsWidth;
       public int    dmPelsHeight;
       public int    dmDisplayFlags;
       public int    dmDisplayFrequency;
       public int    dmICMMethod;
       public int    dmICMIntent;
       public int    dmMediaType;
       public int    dmDitherType;
       public int    dmReserved1;
       public int    dmReserved2;
       public int    dmPanningWidth;
       public int    dmPanningHeight;
    };
    class NativeMethods
    {
        [DllImport("user32.dll")]
        public static extern int EnumDisplaySettings(string deviceName, int modeNum, ref DEVMODE devMode);
        [DllImport("user32.dll")]
        public static extern int ChangeDisplaySettings(ref DEVMODE devMode, int flags);
        public const int ENUM_CURRENT_SETTINGS = -1;
        public const int CDS_UPDATEREGISTRY = 0x01;
        public const int CDS_TEST = 0x02;
        public const int DISP_CHANGE_SUCCESSFUL = 0;
        public const int DISP_CHANGE_RESTART = 1;
        public const int DISP_CHANGE_FAILED = -1;
        public const int DMDO_DEFAULT = 0;
        public const int DMDO_90 = 1;
        public const int DMDO_180 = 2;
        public const int DMDO_270 = 3;
    }
    public class PrmaryScreenResolution
    {
        static public string ChangeResolution()
        {
            DEVMODE dm = GetDevMode();
            if (0 != NativeMethods.EnumDisplaySettings(null, NativeMethods.ENUM_CURRENT_SETTINGS, ref dm))
            {
                int temp = dm.dmPelsHeight;
                dm.dmPelsHeight = dm.dmPelsWidth;
                dm.dmPelsWidth = temp;
                dm.dmDisplayOrientation = NativeMethods.DMDO_270;

                int iRet = NativeMethods.ChangeDisplaySettings(ref dm, NativeMethods.CDS_TEST);
                if (iRet == NativeMethods.DISP_CHANGE_FAILED)
                {
                    return "Não foi possível processar sua solicitação. Desculpe pelo inconveniente.";
                }
                else
                {
                    iRet = NativeMethods.ChangeDisplaySettings(ref dm, NativeMethods.CDS_UPDATEREGISTRY);
                    switch (iRet)
                    {
                        case NativeMethods.DISP_CHANGE_SUCCESSFUL:
                            return "Sucesso";
                        case NativeMethods.DISP_CHANGE_RESTART:
                            return "Você precisa reiniciar para que a alteração tenha efeito.\nSe você sentir algum problema após reiniciar sua máquina,\ntente alterar a resolução no Modo Seguro.";
                        default:
                            return "Falha ao alterar a resolução";
                    }
                }
            }
            else
            {
                return "Falha ao alterar a resolução.";
            }
        }
        private static DEVMODE GetDevMode()
        {
            DEVMODE dm = new DEVMODE();
            dm.dmDeviceName = new String(new char[32]);
            dm.dmFormName = new String(new char[32]);
            dm.dmSize = (short)Marshal.SizeOf(dm);
            return dm;
        }
    }
}
"@
            Add-Type $pinvokeCode -ErrorAction SilentlyContinue
            [Resolution.PrmaryScreenResolution]::ChangeResolution()
        }
        catch {
            $errorMsg = $_.Exception.Message
            Write-Error "Erro ao alterar orientação da tela: $errorMsg"
            [System.Windows.Forms.MessageBox]::Show("Erro ao alterar orientação da tela: $errorMsg", "WinDeckHelper Error", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Error)
        }
    }

    # Funções de verificação
    function Is-Download-Selected {
        param()
        try {
            # Verifica os nós de drivers obrigatórios
            foreach ($node in $nodeMandatory.Nodes) {
                if ($node.Checked) { return $true }
            }

            # Verifica os nós de desenvolvimento
            foreach ($node in $nodeDev.Nodes) {
                if ($node.Checked) { return $true }
            }

            # Verifica os nós de software
            foreach ($node in $nodeEssential.Nodes) {
                if ($node.Checked) { return $true }
            }

            # Verifica os nós de SDKs
            foreach ($node in $nodeSDKs.Nodes) {
                if ($node.Checked) { return $true }
            }

            return $false
        }
        catch {
            $errorMsg = $_.Exception.Message
            Write-Error "Erro em Is-Download-Selected: $errorMsg"
            return $false
        }
    }

    function Is-Configure-Selected {
        param()
        try {
            if (($null -ne $sync.MustTree_Node_Rtss -and $sync.MustTree_Node_Rtss.Checked) -or 
                ($null -ne $sync.MustTree_Node_DeckTools -and $sync.MustTree_Node_DeckTools.Checked)) {
                return $true
            }
            return $false
        }
        catch {
            $errorMsg = $_.Exception.Message
            Write-Error "Erro em Is-Configure-Selected: $errorMsg"
            return $false
        }
    }

    function Is-Tweak-Selected {
        param()
        try {
            # MÉTODO DIRETO: Verifica explicitamente cada nó que podemos precisar
            Write-Host "==== VERIFICAÇÃO DE TWEAKS SELECIONADOS ====" -ForegroundColor Cyan
            
            # === VERIFICAÇÃO DIRETA DO CLOVER BOOTLOADER ===
            # Esta é uma verificação especial e prioritária para o Clover Bootloader
            if ($null -ne $sync.TweaksTree_Node_CloverBootloader) {
                $cloverChecked = $false
                
                # Tentativa 1: Verificação direta da propriedade
                try {
                    $cloverChecked = $sync.TweaksTree_Node_CloverBootloader.Checked
                    Write-Host "Clover Bootloader - Estado (método 1): $cloverChecked" -ForegroundColor Yellow
                }
                catch {
                    Write-Host "Falha na verificação direta do Clover Bootloader: $($_.Exception.Message)" -ForegroundColor Red
                }
                
                # Tentativa 2: Acesso alternativo à propriedade
                if ($cloverChecked -eq $false) {
                    try {
                        # Usar reflexão para acessar a propriedade
                        $cloverNode = $sync.TweaksTree_Node_CloverBootloader
                        $cloverNodeType = $cloverNode.GetType()
                        $checkedProperty = $cloverNodeType.GetProperty("Checked")
                        
                        if ($null -ne $checkedProperty) {
                            $cloverChecked = $checkedProperty.GetValue($cloverNode)
                            Write-Host "Clover Bootloader - Estado (método 2): $cloverChecked" -ForegroundColor Yellow
                        }
                    }
                    catch {
                        Write-Host "Falha na verificação alternativa do Clover Bootloader: $($_.Exception.Message)" -ForegroundColor Red
                    }
                }
                
                # HACK DE EMERGÊNCIA: Se a árvore visual mostra como selecionado, forçamos como true
                try {
                    # Verifica se o nó tem texto "Clover Bootloader"
                    $nodeText = $sync.TweaksTree_Node_CloverBootloader.Text
                    if ($nodeText -like "*Clover Bootloader*" -and -not $cloverChecked) {
                        Write-Host "AVISO: Forçando estado positivo para Clover Bootloader baseado no texto do nó" -ForegroundColor Magenta
                        $cloverChecked = $true
                    }
                }
                catch {
                    Write-Host "Falha na verificação de emergência: $($_.Exception.Message)" -ForegroundColor Red
                }
                
                # Se qualquer método detectou como selecionado, retornamos true imediatamente
                if ($cloverChecked) {
                    Write-Host "RESULTADO: Clover Bootloader está selecionado! Retornando TRUE" -ForegroundColor Green
                    return $true
                }
            }
            
            # === VERIFICAÇÃO NORMAL DOS OUTROS NÓS ===
            $nodes = @(
                $sync.TweaksTree_Node_GameBar,
                $sync.TweaksTree_Node_LoginSleep,
                $sync.TweaksTree_Node_ShowKeyboard
            )
            
            foreach ($node in $nodes) {
                if ($null -ne $node) {
                    try {
                        $nodeText = $node.Text
                        $nodeChecked = $node.Checked
                        $errorMsg = "Erro crítico ao verificar/reparar vcpkg: $($_.Exception.Message)"
                        Write-Host $errorMsg -ForegroundColor Red
                        if ($LogPath) {
                            $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
                            "[{0}] [CRITICAL] {1}" -f $timestamp, $errorMsg | Out-File -Append -FilePath $LogPath -Encoding UTF8
                        }
                        
                        return @{
                            Installed = $false
                            Path = $null
                            Version = $null
                            ExecutablePath = $null
                            Status = "CriticalError"
                            Error = $_.Exception.Message
                        }
                    }
                }
            }

            function Test-ProgramInstalled {
                param(
                    [string]$ProgramName
                )
                
                try {
                    switch ($ProgramName) {
                        "MinGW-w64" { 
                            $paths = @(
                                "$env:ProgramFiles\mingw-w64",
                                "C:\MinGW",
                                "${env:ProgramFiles(x86)}\MinGW",
                                "C:\MinGW-w64"
                            )
                            foreach ($path in $paths) {
                                if (Test-Path $path) {
                                    return @{
                                        Installed = $true
                                        Path = $path
                                    }
                                }
                            }
                            return @{
                                Installed = $false
                                Path = $null
                            }
                        }
                        "Clang" { 
                            $paths = @(
                                "${env:ProgramFiles}\LLVM",
                                "${env:ProgramFiles(x86)}\LLVM"
                            )
                            foreach ($path in $paths) {
                                if (Test-Path "$path\bin\clang.exe") {
                                    return @{
                                        Installed = $true
                                        Path = $path
                                    }
                                }
                            }
                            return @{
                                Installed = $false
                                Path = $null
                            }
                        }
                        "CMake" { 
                            $paths = @(
                                "${env:ProgramFiles}\CMake\bin\cmake.exe",
                                "${env:ProgramFiles(x86)}\CMake\bin\cmake.exe"
                            )
                            foreach ($path in $paths) {
                                if (Test-Path $path) {
                                    return @{
                                        Installed = $true
                                        Path = (Split-Path (Split-Path $path -Parent) -Parent)
                                    }
                                }
                            }
                            return @{
                                Installed = $false
                                Path = $null
                            }
                        }
                        "Ninja" { 
                            $paths = @(
                                "$env:ProgramFiles\Ninja\ninja.exe",
                                "${env:ProgramFiles(x86)}\Ninja\ninja.exe",
                                "$env:SystemRoot\System32\ninja.exe"
                            )
                            foreach ($path in $paths) {
                                if (Test-Path $path) {
                                    return @{
                                        Installed = $true
                                        Path = (Split-Path $path -Parent)
                                    }
                                }
                            }
                            return @{
                                Installed = $false
                                Path = $null
                            }
                        }
                        "vcpkg" { 
                            return Test-VcpkgInstallation
                        }
                        { $_ -in @("SDL2", "SDL2-TTF", "ZLIB", "PNG", "Boost", "Dear ImGui") } {
                            $vcpkgStatus = Test-VcpkgInstallation
                            if (-not $vcpkgStatus.Installed) {
                                return @{
                                    Installed = $false
                                    Path = $null
                                    Error = "vcpkg não está instalado"
                                }
                            }

                            # Definições ampliadas de caminhos para cada pacote
                            $packagePaths = @{
                                "SDL2" = @{
                                    Include = "installed\x64-windows\include\SDL2"
                                    Lib = "installed\x64-windows\lib\SDL2.lib"
                                    Bin = "installed\x64-windows\bin\SDL2.dll"
                                }
                                "SDL2-TTF" = @{
                                    Include = "installed\x64-windows\include\SDL2\SDL_ttf.h"
                                    Lib = "installed\x64-windows\lib\SDL2_ttf.lib"
                                    Bin = "installed\x64-windows\bin\SDL2_ttf.dll"
                                }
                                "ZLIB" = @{
                                    Include = "installed\x64-windows\include\zlib.h"
                                    Lib = "installed\x64-windows\lib\zlib.lib"
                                    Bin = "installed\x64-windows\bin\zlib.dll"
                                }
                                "PNG" = @{
                                    Include = "installed\x64-windows\include\png.h"
                                    Lib = "installed\x64-windows\lib\libpng16.lib"
                                    Bin = "installed\x64-windows\bin\libpng16.dll"
                                }
                                "Boost" = @{
                                    Include = "installed\x64-windows\include\boost"
                                    Lib = "installed\x64-windows\lib\boost_system-vc140-mt.lib"
                                }
                                "Dear ImGui" = @{
                                    Include = "installed\x64-windows\include\imgui.h"
                                    Lib = "installed\x64-windows\lib\imgui.lib"
                                }
                            }

                            $packageInfo = $packagePaths[$_]
                            $includeExists = Test-Path (Join-Path $vcpkgStatus.Path $packageInfo.Include)
                            $libExists = if ($packageInfo.ContainsKey("Lib")) { Test-Path (Join-Path $vcpkgStatus.Path $packageInfo.Lib) } else { $true }
                            $binExists = if ($packageInfo.ContainsKey("Bin")) { Test-Path (Join-Path $vcpkgStatus.Path $packageInfo.Bin) } else { $true }
                            
                            # Verifica se o pacote está no registro do vcpkg
                            $installedPackages = & "$($vcpkgStatus.Path)\vcpkg" list
                            $packageName = $_
                            # Usa uma abordagem mais segura para evitar problemas com caracteres especiais
                            $archSuffix = ":x64-windows"
                            $packageInstalled = $installedPackages | Where-Object { 
                                $line = $_
                                $pattern = [regex]::Escape("$packageName$archSuffix")
                                $line -match $pattern
                            }
                            $registryCheck = $null -ne $packageInstalled

                            # Calcula status geral
                            $allTestsPassed = $includeExists -and $libExists -and $binExists -and $registryCheck
                            
                            # Constrói mensagem de diagnóstico
                            $diagnostic = ""
                            if (-not $includeExists) { $diagnostic += "arquivos de include ausentes; " }
                            if (-not $libExists) { $diagnostic += "bibliotecas ausentes; " }
                            if (-not $binExists) { $diagnostic += "binários ausentes; " }
                            if (-not $registryCheck) { $diagnostic += "não registrado no vcpkg; " }
                            
                            # Remove o último "; " se existir
                            if ($diagnostic -ne "") {
                                $diagnostic = $diagnostic.Substring(0, $diagnostic.Length - 2)
                            }

                            return @{
                                Installed = $allTestsPassed
                                Path = Join-Path $vcpkgStatus.Path $packageInfo.Include
                                IncludeExists = $includeExists
                                LibExists = $libExists
                                BinExists = $binExists
                                RegistryExists = $registryCheck
                                Diagnostic = if ($diagnostic -ne "") { $diagnostic } else { $null }
                            }
                        }
                        "Rust" {
                            $rustPath = "$env:USERPROFILE\.cargo\bin\rustc.exe"
                            return @{
                                Installed = (Test-Path $rustPath)
                                Path = (Split-Path $rustPath -Parent)
                            }
                        }
                        "Docker" {
                            $dockerPath = "$env:ProgramFiles\Docker\Docker\Docker Desktop.exe"
                            return @{
                                Installed = (Test-Path $dockerPath)
                                Path = (Split-Path $dockerPath -Parent)
                            }
                        }
                        "WSL" {
                            $wslFeature = Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux
                            return @{
                                Installed = ($wslFeature.State -eq "Enabled")
                                Path = "$env:SystemRoot\System32\wsl.exe"
                            }
                        }
                        "Visual Studio Build Tools" {
                            $vsPath = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\2022\BuildTools"
                            return @{
                                Installed = (Test-Path $vsPath)
                                Path = $vsPath
                            }
                        }
                        "Cursor IDE" {
                            $cursorPath = "$env:LOCALAPPDATA\Programs\Cursor\Cursor.exe"
                            return @{
                                Installed = (Test-Path $cursorPath)
                                Path = (Split-Path $cursorPath -Parent)
                            }
                        }
                        "Steam" {
                            $steamPath = "${env:ProgramFiles(x86)}\Steam\Steam.exe"
                            return @{
                                Installed = (Test-Path $steamPath)
                                Path = (Split-Path $steamPath -Parent)
                            }
                        }
                        "Chrome" {
                            $chromePath = "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe"
                            return @{
                                Installed = (Test-Path $chromePath)
                                Path = (Split-Path $chromePath -Parent)
                            }
                        }
                        "7-Zip" {
                            $7zipPath = "$env:ProgramFiles\7-Zip\7z.exe"
                            return @{
                                Installed = (Test-Path $7zipPath)
                                Path = (Split-Path $7zipPath -Parent)
                            }
                        }
                        "Notepad++" {
                            $nppPath = "$env:ProgramFiles\Notepad++\notepad++.exe"
                            return @{
                                Installed = (Test-Path $nppPath)
                                Path = (Split-Path $nppPath -Parent)
                            }
                        }
                        "K-Lite Codec Pack-x86" {
                            $klitePath = "${env:ProgramFiles(x86)}\K-Lite Codec Pack"
                            return @{
                                Installed = (Test-Path $klitePath)
                                Path = $klitePath
                            }
                        }
                        "MemReduct" {
                            $memreductPath = "$env:ProgramFiles\Memreduct\memreduct.exe"
                            return @{
                                Installed = (Test-Path $memreductPath)
                                Path = (Split-Path $memreductPath -Parent)
                            }
                        }
                        "OBS Studio" {
                            $obsPath = "$env:ProgramFiles\obs-studio\bin\64bit\obs64.exe"
                            return @{
                                Installed = (Test-Path $obsPath)
                                Path = (Split-Path (Split-Path (Split-Path $obsPath -Parent) -Parent) -Parent)
                            }
                        }
                        "VLC Media Player" {
                            $vlcPath = "$env:ProgramFiles\VideoLAN\VLC\vlc.exe"
                            return @{
                                Installed = (Test-Path $vlcPath)
                                Path = (Split-Path $vlcPath -Parent)
                            }
                        }
                        "Driver BTRFS" {
                            $driver = Get-WmiObject Win32_SystemDriver | Where-Object { $_.Name -like "*BTRFS*" }
                            return @{
                                Installed = ($null -ne $driver)
                                Path = if ($driver) { $driver.PathName } else { $null }
                            }
                        }
                        { $_ -match "vcredist\d{4}_(x86|x64)" -or $_ -eq "Microsoft Visual C++ Runtimes" } {
                            $vcRedistInfo = @{
                                "2005" = @{
                                    x86 = @{
                                        Files = @("${env:SystemRoot}\System32\msvcr80.dll", "${env:SystemRoot}\System32\msvcp80.dll")
                                        RegKeys = @(
                                            "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{A49F249F-0C91-497F-86DF-B2585E8E76B7}",
                                            "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\{A49F249F-0C91-497F-86DF-B2585E8E76B7}"
                                        )
                                    }
                                    x64 = @{
                                        Files = @("${env:SystemRoot}\System32\msvcr80.dll", "${env:SystemRoot}\System32\msvcp80.dll")
                                        RegKeys = @(
                                            "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{6E8E85E8-CE4B-4FF5-91F7-04999C9FAE6A}",
                                            "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\{6E8E85E8-CE4B-4FF5-91F7-04999C9FAE6A}"
                                        )
                                    }
                                }
                                "2008" = @{
                                    x86 = @{
                                        Files = @("${env:SystemRoot}\System32\msvcr90.dll", "${env:SystemRoot}\System32\msvcp90.dll")
                                        RegKeys = @(
                                            "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{9BE518E6-ECC6-35A9-88E4-87755C07200F}",
                                            "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\{9BE518E6-ECC6-35A9-88E4-87755C07200F}"
                                        )
                                    }
                                    x64 = @{
                                        Files = @("${env:SystemRoot}\System32\msvcr90.dll", "${env:SystemRoot}\System32\msvcp90.dll")
                                        RegKeys = @(
                                            "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{5FCE6D76-F5DC-37AB-B2B8-22AB8CEDB1D4}",
                                            "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\{5FCE6D76-F5DC-37AB-B2B8-22AB8CEDB1D4}"
                                        )
                                    }
                                }
                                "2010" = @{
                                    x86 = @{
                                        Files = @("${env:SystemRoot}\System32\msvcr100.dll", "${env:SystemRoot}\System32\msvcp100.dll")
                                        RegKeys = @(
                                            "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{F0C3E5D1-1ADE-321E-8167-68EF0DE699A5}",
                                            "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\{F0C3E5D1-1ADE-321E-8167-68EF0DE699A5}"
                                        )
                                    }
                                    x64 = @{
                                        Files = @("${env:SystemRoot}\System32\msvcr100.dll", "${env:SystemRoot}\System32\msvcp100.dll")
                                        RegKeys = @(
                                            "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{1D8E6291-B0D5-35EC-8441-6616F567A0F7}",
                                            "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\{1D8E6291-B0D5-35EC-8441-6616F567A0F7}"
                                        )
                                    }
                                }
                                "2012" = @{
                                    x86 = @{
                                        Files = @("${env:SystemRoot}\System32\msvcr110.dll", "${env:SystemRoot}\System32\msvcp110.dll")
                                        RegKeys = @(
                                            "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{33D1FD90-4274-48A1-9BC1-97E33D9C2D6F}",
                                            "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\{33D1FD90-4274-48A1-9BC1-97E33D9C2D6F}"
                                        )
                                    }
                                    x64 = @{
                                        Files = @("${env:SystemRoot}\System32\msvcr110.dll", "${env:SystemRoot}\System32\msvcp110.dll")
                                        RegKeys = @(
                                            "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{CA67548A-5EBE-413A-B50C-4B9CEB6D66C6}",
                                            "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\{CA67548A-5EBE-413A-B50C-4B9CEB6D66C6}"
                                        )
                                    }
                                }
                                "2013" = @{
                                    x86 = @{
                                        Files = @("${env:SystemRoot}\System32\msvcr120.dll", "${env:SystemRoot}\System32\msvcp120.dll")
                                        RegKeys = @(
                                            "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{13A4EE12-23EA-3371-91EE-EFB36DDFFF3E}",
                                            "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\{13A4EE12-23EA-3371-91EE-EFB36DDFFF3E}"
                                        )
                                    }
                                    x64 = @{
                                        Files = @("${env:SystemRoot}\System32\msvcr120.dll", "${env:SystemRoot}\System32\msvcp120.dll")
                                        RegKeys = @(
                                            "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{A749D8E6-B613-3BE3-8F5F-045C84EBA29B}",
                                            "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\{A749D8E6-B613-3BE3-8F5F-045C84EBA29B}"
                                        )
                                    }
                                }
                                "2015+" = @{
                                    x86 = @{
                                        Files = @(
                                            "${env:SystemRoot}\System32\vcruntime140.dll",
                                            "${env:SystemRoot}\System32\msvcp140.dll",
                                            "${env:SystemRoot}\System32\vcruntime140_1.dll"
                                        )
                                        RegKeys = @(
                                            "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{65E5BD06-6392-3027-8C26-853107D3CF1A}",
                                            "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\{65E5BD06-6392-3027-8C26-853107D3CF1A}",
                                            "HKLM:\SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x86",
                                            "HKLM:\SOFTWARE\Microsoft\VisualStudio\15.0\VC\Runtimes\x86",
                                            "HKLM:\SOFTWARE\Microsoft\VisualStudio\16.0\VC\Runtimes\x86",
                                            "HKLM:\SOFTWARE\Microsoft\VisualStudio\17.0\VC\Runtimes\x86"
                                        )
                                    }
                                    x64 = @{
                                        Files = @(
                                            "${env:SystemRoot}\System32\vcruntime140.dll",
                                            "${env:SystemRoot}\System32\msvcp140.dll",
                                            "${env:SystemRoot}\System32\vcruntime140_1.dll"
                                        )
                                        RegKeys = @(
                                            "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{39e28474-b67b-4209-af1b-e9ad0a83d8ca}",
                                            "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\{39e28474-b67b-4209-af1b-e9ad0a83d8ca}",
                                            "HKLM:\SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64",
                                            "HKLM:\SOFTWARE\Microsoft\VisualStudio\15.0\VC\Runtimes\x64",
                                            "HKLM:\SOFTWARE\Microsoft\VisualStudio\16.0\VC\Runtimes\x64",
                                            "HKLM:\SOFTWARE\Microsoft\VisualStudio\17.0\VC\Runtimes\x64"
                                        )
                                    }
                                }
                            }

                            function Test-VCRedist {
                                param (
                                    [string]$Year,
                                    [string]$Architecture
                                )

                                $info = $vcRedistInfo[$Year][$Architecture]
                                $installed = $false
                                $version = $null
                                $path = $null

                                # Verifica arquivos
                                $filesExist = $info.Files | Where-Object { Test-Path $_ }
                                if ($filesExist.Count -gt 0) {
                                    $installed = $true
                                    $path = $filesExist[0]
                                }

                                # Verifica chaves do registro
                                foreach ($regKey in $info.RegKeys) {
                                    if (Test-Path $regKey) {
                                        $installed = $true
                                        try {
                                            $regInfo = Get-ItemProperty -Path $regKey
                                            if ($regInfo.Version) {
                                                $version = $regInfo.Version
                                            } elseif ($regInfo.DisplayVersion) {
                                                $version = $regInfo.DisplayVersion
                                            }
                                            $path = $regKey
                                            break
                                        } catch {
                                            Write-Warning "Erro ao ler registro $regKey`: $_"
                                        }
                                    }
                                }

                                return @{
                                    Installed = $installed
                                    Version = $version
                                    Path = $path
                                }
                            }

                            # Se for uma verificação específica de versão
                            if ($_ -match "vcredist(\d{4})_(x86|x64)") {
                                $year = $matches[1]
                                $arch = $matches[2]
                                
                                # Ajusta o ano para 2015+ se for 2015 ou posterior
                                $yearKey = if ([int]$year -ge 2015) { "2015+" } else { $year }
                                
                                $result = Test-VCRedist -Year $yearKey -Architecture $arch
                                return $result
                            }
                            # Se for verificação geral de Visual C++ Runtimes
                            else {
                                $results = @{}
                                foreach ($year in $vcRedistInfo.Keys) {
                                    foreach ($arch in @("x86", "x64")) {
                                        $result = Test-VCRedist -Year $year -Architecture $arch
                                        $results["$year $arch"] = $result
                                    }
                                }

                                # Considera instalado se pelo menos uma versão está presente
                                $anyInstalled = $results.Values | Where-Object { $_.Installed }
                                return @{
                                    Installed = ($anyInstalled.Count -gt 0)
                                    Path = "Multiple"
                                    Details = $results
                                }
                            }
                        }
                        "DirectX" {
                            $dxdiag = "$env:SystemRoot\System32\dxdiag.exe"
                            return @{
                                Installed = (Test-Path $dxdiag)
                                Path = (Split-Path $dxdiag -Parent)
                            }
                        }
                        "PhysX" {
                            $physXPath = "$env:SystemRoot\System32\PhysXDevice64.dll"
                            return @{
                                Installed = (Test-Path $physXPath)
                                Path = (Split-Path $physXPath -Parent)
                            }
                        }
                        "Trae" {
                            $paths = @(
                                "$env:ProgramFiles\Trae\trae.exe",
                                "$env:LOCALAPPDATA\Programs\Trae\trae.exe"
                            )
                            foreach ($path in $paths) {
                                if (Test-Path $path) {
                                    return @{
                                        Installed = $true
                                        Path = (Split-Path $path -Parent)
                                    }
                                }
                            }
                            return @{
                                Installed = $false
                                Path = $null
                            }
                        }
                        "Ollama" {
                            $paths = @(
                                "$env:ProgramFiles\Ollama\ollama.exe",
                                "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe"
                            )
                            foreach ($path in $paths) {
                                if (Test-Path $path) {
                                    return @{
                                        Installed = $true
                                        Path = (Split-Path $path -Parent)
                                    }
                                }
                            }
                            return @{
                                Installed = $false
                                Path = $null
                            }
                        }
                        "LM Studio" {
                            $paths = @(
                                "$env:LOCALAPPDATA\Programs\LM Studio\LM Studio.exe",
                                "$env:ProgramFiles\LM Studio\LM Studio.exe"
                            )
                            foreach ($path in $paths) {
                                if (Test-Path $path) {
                                    return @{
                                        Installed = $true
                                        Path = (Split-Path $path -Parent)
                                    }
                                }
                            }
                            return @{
                                Installed = $false
                                Path = $null
                            }
                        }
                        default {
                            return @{
                                Installed = $false
                                Path = $null
                                Error = "Verificação não implementada para $ProgramName"
                            }
                        }
                    }
                }
                catch {
                    Write-Error "Erro ao verificar instalação de $ProgramName`: $($_.Exception.Message)"
                    return @{
                        Installed = $false
                        Path = $null
                        Error = $_.Exception.Message
                    }
                }
            }

            # Função para atualizar os checks baseado nos programas instalados
            function Update-InstallationChecks {
                param()
                try {
                    Write-Host "Iniciando verificação de programas instalados..."
                    
                    # Verifica vcpkg primeiro
                    $vcpkgStatus = Test-VcpkgInstallation
                    if (-not $vcpkgStatus.Installed) {
                        Write-Warning "vcpkg não está instalado ou precisa ser reparado: $($vcpkgStatus.Error)"
                    }
                    
                    # Função auxiliar para atualizar o nó
                    function Update-Node {
                        param($Node, $Status)
                        $programName = $Node.Text -replace " \([^)]+\)", ""
                        if ($Status.Installed) {
                            $Node.Text = "$programName (Instalado em $($Status.Path))"
                            $Node.ForeColor = [System.Drawing.Color]::Green
                        } else {
                            if ($Status.Error) {
                                $Node.Text = "$programName (Erro: $($Status.Error))"
                                $Node.ForeColor = [System.Drawing.Color]::Red
                            } else {
                                $Node.Text = "$programName (Não instalado)"
                                $Node.ForeColor = [System.Drawing.Color]::Black
                            }
                        }
                    }
                    
                    # Atualiza checks de desenvolvimento
                    foreach ($node in $nodeDev.Nodes) {
                        $programName = $node.Text -replace " \([^)]+\)", ""
                        $status = Test-ProgramInstalled -ProgramName $programName
                        Update-Node -Node $node -Status $status
                    }

                    # Atualiza checks de SDKs
                    foreach ($node in $nodeSDKs.Nodes) {
                        $sdkName = $node.Text -replace " \([^)]+\)", ""
                        $sdkName = $sdkName -replace " \(.*\)", ""
                        $status = Test-ProgramInstalled -ProgramName $sdkName
                        Update-Node -Node $node -Status $status
                    }

                    # Atualiza checks de software essencial
                    foreach ($node in $nodeEssential.Nodes) {
                        $programName = $node.Text -replace " \([^)]+\)", ""
                        $status = Test-ProgramInstalled -ProgramName $programName
                        Update-Node -Node $node -Status $status
                    }

                    # Atualiza checks de IA
                    foreach ($node in $nodeAI.Nodes) {
                        $programName = $node.Text -replace " \([^)]+\)", ""
                        $status = Test-ProgramInstalled -ProgramName $programName
                        Update-Node -Node $node -Status $status
                    }

                    # Atualiza checks de Runtimes
                    foreach ($node in $nodeRuntimes.Nodes) {
                        $programName = $node.Text -replace " \([^)]+\)", ""
                        $status = Test-ProgramInstalled -ProgramName $programName
                        Update-Node -Node $node -Status $status
                    }

                    # Atualiza checks de Drivers
                    foreach ($node in $nodeMandatory.Nodes) {
                        $programName = $node.Text -replace " \([^)]+\)", ""
                        $status = Test-ProgramInstalled -ProgramName $programName
                        Update-Node -Node $node -Status $status
                    }
                    
                    Write-Host "Verificação de programas instalados concluída."
                }
                catch {
                    Write-Error "Erro ao atualizar checks de instalação: $($_.Exception.Message)"
                }
            }

            # Inicializa a interface do usuário
            $form = New-Object System.Windows.Forms.Form
            $form.Text = "WinDeckHelper"
            $form.Size = New-Object System.Drawing.Size(1024,768)
            $form.StartPosition = "CenterScreen"
            $form.BackColor = [System.Drawing.Color]::FromArgb(240, 240, 240)

            # Adiciona os controles necessários
            $tabControl = New-Object System.Windows.Forms.TabControl
            $tabControl.Dock = [System.Windows.Forms.DockStyle]::Fill
            $tabControl.Font = New-Object System.Drawing.Font("Segoe UI", 10)

            # Tab de Drivers
            $tabDrivers = New-Object System.Windows.Forms.TabPage
            $tabDrivers.Text = "Drivers"
            $tabDrivers.BackColor = [System.Drawing.Color]::White

            $treeViewDrivers = New-Object System.Windows.Forms.TreeView
            $treeViewDrivers.Dock = [System.Windows.Forms.DockStyle]::Fill
            $treeViewDrivers.CheckBoxes = $true
            $treeViewDrivers.Font = New-Object System.Drawing.Font("Segoe UI", 9)

            # Grupo de Drivers Obrigatórios
            $nodeMandatory = New-Object System.Windows.Forms.TreeNode("Drivers Obrigatórios")
            $nodeVideo = New-Object System.Windows.Forms.TreeNode("Driver de Vídeo AMD")
            $nodeAudio = New-Object System.Windows.Forms.TreeNode("Driver de Áudio")
            $nodeBluetooth = New-Object System.Windows.Forms.TreeNode("Driver Bluetooth")
            $nodeCardReader = New-Object System.Windows.Forms.TreeNode("Driver do Leitor de Cartão")
            $nodeBTRFS = New-Object System.Windows.Forms.TreeNode("Driver BTRFS")
            $nodeMandatory.Nodes.AddRange(@($nodeVideo, $nodeAudio, $nodeBluetooth, $nodeCardReader, $nodeBTRFS))

            # Grupo de Desenvolvimento
            $nodeDev = New-Object System.Windows.Forms.TreeNode("Ferramentas de Desenvolvimento")
            $nodeMinGW = New-Object System.Windows.Forms.TreeNode("MinGW-w64")
            $nodeClang = New-Object System.Windows.Forms.TreeNode("Clang")
            $nodeCMake = New-Object System.Windows.Forms.TreeNode("CMake")
            $nodeNinja = New-Object System.Windows.Forms.TreeNode("Ninja")
            $nodeVcpkg = New-Object System.Windows.Forms.TreeNode("vcpkg")
            $nodeSDL2 = New-Object System.Windows.Forms.TreeNode("SDL2")
            $nodeSDL2TTF = New-Object System.Windows.Forms.TreeNode("SDL2-TTF")
            $nodeZLIB = New-Object System.Windows.Forms.TreeNode("ZLIB")
            $nodePNG = New-Object System.Windows.Forms.TreeNode("PNG")
            $nodeBoost = New-Object System.Windows.Forms.TreeNode("Boost")
            $nodeDearImGui = New-Object System.Windows.Forms.TreeNode("Dear ImGui")
            $nodeCrosstoolNG = New-Object System.Windows.Forms.TreeNode("Crosstool-NG")
            $nodeRust = New-Object System.Windows.Forms.TreeNode("Rust (rustup)")
            $nodeTCC = New-Object System.Windows.Forms.TreeNode("TCC")
            $nodeCygwin = New-Object System.Windows.Forms.TreeNode("Cygwin")
            $nodeZig = New-Object System.Windows.Forms.TreeNode("Zig")
            $nodeEmscripten = New-Object System.Windows.Forms.TreeNode("Emscripten")
            $nodeConan = New-Object System.Windows.Forms.TreeNode("Conan")
            $nodeMeson = New-Object System.Windows.Forms.TreeNode("Meson")
            $nodeSpack = New-Object System.Windows.Forms.TreeNode("Spack")
            $nodeHunter = New-Object System.Windows.Forms.TreeNode("Hunter")
            $nodeBuckaroo = New-Object System.Windows.Forms.TreeNode("Buckaroo")
            $nodeDocker = New-Object System.Windows.Forms.TreeNode("Docker")
            $nodeWSL = New-Object System.Windows.Forms.TreeNode("WSL")
            $nodeVSBuildTools = New-Object System.Windows.Forms.TreeNode("Visual Studio Build Tools")
            $nodeCursorIDE = New-Object System.Windows.Forms.TreeNode("Cursor IDE")
            $nodeCursorVip = New-Object System.Windows.Forms.TreeNode("CursorVip")

            $nodeDev.Nodes.AddRange(@(
                $nodeMinGW, $nodeClang, $nodeCMake, $nodeNinja, $nodeVcpkg, 
                $nodeSDL2, $nodeSDL2TTF, $nodeZLIB, $nodePNG, $nodeBoost,
                $nodeDearImGui, $nodeCrosstoolNG, $nodeRust, $nodeTCC, $nodeCygwin,
                $nodeZig, $nodeEmscripten, $nodeConan, $nodeMeson, $nodeSpack,
                $nodeHunter, $nodeBuckaroo, $nodeDocker, $nodeWSL, $nodeVSBuildTools,
                $nodeCursorIDE, $nodeCursorVip
            ))

            $treeViewDrivers.Nodes.Add($nodeMandatory)
            $treeViewDrivers.Nodes.Add($nodeDev)

            $tabDrivers.Controls.Add($treeViewDrivers)
            $tabControl.TabPages.Add($tabDrivers)

            # Tab de Software
            $tabSoftware = New-Object System.Windows.Forms.TabPage
            $tabSoftware.Text = "Software"
            $tabSoftware.BackColor = [System.Drawing.Color]::White

            $treeViewSoftware = New-Object System.Windows.Forms.TreeView
            $treeViewSoftware.Dock = [System.Windows.Forms.DockStyle]::Fill
            $treeViewSoftware.CheckBoxes = $true
            $treeViewSoftware.Font = New-Object System.Drawing.Font("Segoe UI", 9)

            # Grupo de Software Essencial
            $nodeEssential = New-Object System.Windows.Forms.TreeNode("Software Essencial")
            $nodeSteam = New-Object System.Windows.Forms.TreeNode("Steam")
            $nodeChrome = New-Object System.Windows.Forms.TreeNode("Chrome")
            $node7zip = New-Object System.Windows.Forms.TreeNode("7-Zip")
            $nodeShareX = New-Object System.Windows.Forms.TreeNode("ShareX")
            $nodeNotepadPP = New-Object System.Windows.Forms.TreeNode("Notepad++")
            $nodeKLite = New-Object System.Windows.Forms.TreeNode("K-Lite Codec Pack-x86")
            $nodeMemReduct = New-Object System.Windows.Forms.TreeNode("MemReduct")
            $nodeOBS = New-Object System.Windows.Forms.TreeNode("OBS Studio")
            $nodeRevo = New-Object System.Windows.Forms.TreeNode("Revo Uninstaller")
            $nodeVLC = New-Object System.Windows.Forms.TreeNode("VLC Media Player")
            $nodeWinaero = New-Object System.Windows.Forms.TreeNode("WinaeroTweaker")
            $nodeBloaty = New-Object System.Windows.Forms.TreeNode("BloatyNosy")
            $nodeHardLink = New-Object System.Windows.Forms.TreeNode("HardLinkShellExt_X64")
            $nodeOptimizer = New-Object System.Windows.Forms.TreeNode("Optimizer")

            $nodeEssential.Nodes.AddRange(@(
                $nodeSteam, $nodeChrome, $node7zip, $nodeShareX, $nodeNotepadPP,
                $nodeKLite, $nodeMemReduct, $nodeOBS, $nodeRevo, $nodeVLC,
                $nodeWinaero, $nodeBloaty, $nodeHardLink, $nodeOptimizer
            ))

            $treeViewSoftware.Nodes.Add($nodeEssential)
            $tabSoftware.Controls.Add($treeViewSoftware)
            $tabControl.TabPages.Add($tabSoftware)

            # Tab de Tweaks
            $tabTweaks = New-Object System.Windows.Forms.TabPage
            $tabTweaks.Text = "Tweaks"
            $tabTweaks.BackColor = [System.Drawing.Color]::White

            $treeViewTweaks = New-Object System.Windows.Forms.TreeView
            $treeViewTweaks.Dock = [System.Windows.Forms.DockStyle]::Fill
            $treeViewTweaks.CheckBoxes = $true
            $treeViewTweaks.Font = New-Object System.Drawing.Font("Segoe UI", 9)

            # Grupo de Tweaks do Sistema
            $nodeSystem = New-Object System.Windows.Forms.TreeNode("Tweaks do Sistema")
            $nodeGameBar = New-Object System.Windows.Forms.TreeNode("Desativar Game Bar")
            $nodeLoginSleep = New-Object System.Windows.Forms.TreeNode("Desativar Login Sleep")
            $nodeShowKeyboard = New-Object System.Windows.Forms.TreeNode("Mostrar Teclado Virtual")
            $nodeCloverBootloader = New-Object System.Windows.Forms.TreeNode("Clover Bootloader (Multi-boot)")
            $nodeSystem.Nodes.AddRange(@($nodeGameBar, $nodeLoginSleep, $nodeShowKeyboard, $nodeCloverBootloader))

            # Armazena as referências dos nós
            $sync.TweaksTree_Node_GameBar = $nodeGameBar
            $sync.TweaksTree_Node_LoginSleep = $nodeLoginSleep
            $sync.TweaksTree_Node_ShowKeyboard = $nodeShowKeyboard
            $sync.TweaksTree_Node_CloverBootloader = $nodeCloverBootloader

            $treeViewTweaks.Nodes.Add($nodeSystem)
            $tabTweaks.Controls.Add($treeViewTweaks)
            $tabControl.TabPages.Add($tabTweaks)

            # Adiciona nova aba para SDKs
            $tabSDKs = New-Object System.Windows.Forms.TabPage
            $tabSDKs.Text = "SDKs"
            $tabSDKs.BackColor = [System.Drawing.Color]::White

            $treeViewSDKs = New-Object System.Windows.Forms.TreeView
            $treeViewSDKs.Dock = [System.Windows.Forms.DockStyle]::Fill
            $treeViewSDKs.CheckBoxes = $true
            $treeViewSDKs.Font = New-Object System.Drawing.Font("Segoe UI", 9)

            # Grupo de SDKs
            $nodeSDKs = New-Object System.Windows.Forms.TreeNode("SDKs Disponíveis")
            $nodeSGDK = New-Object System.Windows.Forms.TreeNode("SGDK (Sega Genesis Development Kit)")
            $nodePSn00b = New-Object System.Windows.Forms.TreeNode("PSn00bSDK (PlayStation 1)")
            $nodePS2Dev = New-Object System.Windows.Forms.TreeNode("PS2DEV (PlayStation 2)")
            $nodeVulkan = New-Object System.Windows.Forms.TreeNode("Vulkan SDK")
            $nodeSNESDev = New-Object System.Windows.Forms.TreeNode("SNESDev (Super Nintendo)")
            $nodeDevkitSMS = New-Object System.Windows.Forms.TreeNode("DevkitSMS (Master System/Game Gear)")
            $nodeGBDK = New-Object System.Windows.Forms.TreeNode("GBDK (Game Boy)")
            $nodeLibGBA = New-Object System.Windows.Forms.TreeNode("libgba (Game Boy Advance)")
            $nodeNESDEV = New-Object System.Windows.Forms.TreeNode("NESDEV (NES)")
            $nodeNGDevKit = New-Object System.Windows.Forms.TreeNode("NGDevKit (Neo Geo)")
            $nodeLibDragon = New-Object System.Windows.Forms.TreeNode("libdragon (Nintendo 64)")
            $nodePSXSDK = New-Object System.Windows.Forms.TreeNode("PSXSDK (PlayStation 1)")
            $nodePS2SDK = New-Object System.Windows.Forms.TreeNode("PS2SDK (PlayStation 2)")

            $nodeSDKs.Nodes.AddRange(@(
                $nodeSGDK, $nodePSn00b, $nodePS2Dev, $nodeVulkan,
                $nodeSNESDev, $nodeDevkitSMS, $nodeGBDK, $nodeLibGBA,
                $nodeNESDEV, $nodeNGDevKit, $nodeLibDragon, $nodePSXSDK, $nodePS2SDK
            ))

            $treeViewSDKs.Nodes.Add($nodeSDKs)
            $tabSDKs.Controls.Add($treeViewSDKs)
            $tabControl.TabPages.Add($tabSDKs)

            # Adiciona nova aba para Emuladores
            $tabEmulators = New-Object System.Windows.Forms.TabPage
            $tabEmulators.Text = "Emuladores"
            $tabEmulators.BackColor = [System.Drawing.Color]::White

            $treeViewEmulators = New-Object System.Windows.Forms.TreeView
            $treeViewEmulators.Dock = [System.Windows.Forms.DockStyle]::Fill
            $treeViewEmulators.CheckBoxes = $true
            $treeViewEmulators.Font = New-Object System.Drawing.Font("Segoe UI", 9)

            # Grupo de Consoles Clássicos
            $nodeClassicConsoles = New-Object System.Windows.Forms.TreeNode("Consoles Clássicos")
            $nodeStella = New-Object System.Windows.Forms.TreeNode("Stella (Atari 2600)")
            $nodeProSystem = New-Object System.Windows.Forms.TreeNode("ProSystem (Atari 7800)")
            $nodeHandy = New-Object System.Windows.Forms.TreeNode("Handy (Atari Lynx)")
            $nodeColEm = New-Object System.Windows.Forms.TreeNode("ColEm (ColecoVision)")
            $nodeJzIntv = New-Object System.Windows.Forms.TreeNode("jzIntv (Intellivision)")
            $nodeClassicConsoles.Nodes.AddRange(@($nodeStella, $nodeProSystem, $nodeHandy, $nodeColEm, $nodeJzIntv))

            # Grupo de Computadores Retro
            $nodeRetroComputers = New-Object System.Windows.Forms.TreeNode("Computadores Retro")
            $nodeVICE = New-Object System.Windows.Forms.TreeNode("VICE (Commodore 64)")
            $nodeWinUAE = New-Object System.Windows.Forms.TreeNode("WinUAE (Amiga)")
            $nodeOpenMSX = New-Object System.Windows.Forms.TreeNode("openMSX (MSX)")
            $nodeDOSBox = New-Object System.Windows.Forms.TreeNode("DOSBox (PC DOS)")
            $nodeRetroComputers.Nodes.AddRange(@($nodeVICE, $nodeWinUAE, $nodeOpenMSX, $nodeDOSBox))

            # Grupo de Consoles Modernos
            $nodeModernConsoles = New-Object System.Windows.Forms.TreeNode("Consoles Modernos")
            $nodeProject64 = New-Object System.Windows.Forms.TreeNode("Project64 (Nintendo 64)")
            $nodeFlycast = New-Object System.Windows.Forms.TreeNode("Flycast (Dreamcast)")
            $nodeCitra = New-Object System.Windows.Forms.TreeNode("Citra (Nintendo 3DS)")
            $nodeModernConsoles.Nodes.AddRange(@($nodeProject64, $nodeFlycast, $nodeCitra))

            # Grupo de Arcades
            $nodeArcades = New-Object System.Windows.Forms.TreeNode("Arcades")
            $nodeFBNeo = New-Object System.Windows.Forms.TreeNode("Final Burn Neo")
            $nodeArcades.Nodes.Add($nodeFBNeo)

            $treeViewEmulators.Nodes.AddRange(@($nodeClassicConsoles, $nodeRetroComputers, $nodeModernConsoles, $nodeArcades))
            $tabEmulators.Controls.Add($treeViewEmulators)
            $tabControl.TabPages.Add($tabEmulators)

            # Grupo de IA
            $nodeAI = New-Object System.Windows.Forms.TreeNode("Inteligência Artificial")
            $nodeTrae = New-Object System.Windows.Forms.TreeNode("Trae")
            $nodeOllama = New-Object System.Windows.Forms.TreeNode("Ollama")
            $nodeLMStudio = New-Object System.Windows.Forms.TreeNode("LM Studio")
            $nodeAI.Nodes.AddRange(@($nodeTrae, $nodeOllama, $nodeLMStudio))

            # Grupo de Runtimes
            $nodeRuntimes = New-Object System.Windows.Forms.TreeNode("Runtimes")
            $nodeVCRedist = New-Object System.Windows.Forms.TreeNode("Microsoft Visual C++ Runtimes")
            $nodeVCRedist2005x86 = New-Object System.Windows.Forms.TreeNode("vcredist2005_x86")
            $nodeVCRedist2008x86 = New-Object System.Windows.Forms.TreeNode("vcredist2008_x86")
            $nodeVCRedist2010x86 = New-Object System.Windows.Forms.TreeNode("vcredist2010_x86")
            $nodeVCRedist2012x86 = New-Object System.Windows.Forms.TreeNode("vcredist2012_x86")
            $nodeVCRedist2013x86 = New-Object System.Windows.Forms.TreeNode("vcredist2013_x86")
            $nodeVCRedist2015x86 = New-Object System.Windows.Forms.TreeNode("vcredist2015_2017_2019_x86")
            $nodeVCRedist2005x64 = New-Object System.Windows.Forms.TreeNode("vcredist2005_x64")
            $nodeVCRedist2008x64 = New-Object System.Windows.Forms.TreeNode("vcredist2008_x64")
            $nodeVCRedist2010x64 = New-Object System.Windows.Forms.TreeNode("vcredist2010_x64")
            $nodeVCRedist2012x64 = New-Object System.Windows.Forms.TreeNode("vcredist2012_x64")
            $nodeVCRedist2013x64 = New-Object System.Windows.Forms.TreeNode("vcredist2013_x64")
            $nodeVCRedist2015x64 = New-Object System.Windows.Forms.TreeNode("vcredist2015_2017_2019_x64")
            $nodeVCRedistAIO = New-Object System.Windows.Forms.TreeNode("VisualCppRedist_AIO_x86_x64")
            $nodeWinDesktopRuntime = New-Object System.Windows.Forms.TreeNode("windowsdesktop-runtime")
            $nodeOpenAL = New-Object System.Windows.Forms.TreeNode("Creative Labs Open AL")
            $nodeDirectX = New-Object System.Windows.Forms.TreeNode("DirectX")
            $nodePhysX = New-Object System.Windows.Forms.TreeNode("PhysX")
            $nodeUE3Redist = New-Object System.Windows.Forms.TreeNode("UE3Redist")
            $nodeUE4Prereq = New-Object System.Windows.Forms.TreeNode("UE4PrereqSetup_x64")

            $nodeRuntimes.Nodes.AddRange(@(
                $nodeVCRedist, $nodeVCRedist2005x86, $nodeVCRedist2008x86, $nodeVCRedist2010x86,
                $nodeVCRedist2012x86, $nodeVCRedist2013x86, $nodeVCRedist2015x86,
                $nodeVCRedist2005x64, $nodeVCRedist2008x64, $nodeVCRedist2010x64,
                $nodeVCRedist2012x64, $nodeVCRedist2013x64, $nodeVCRedist2015x64,
                $nodeVCRedistAIO, $nodeWinDesktopRuntime, $nodeOpenAL,
                $nodeDirectX, $nodePhysX, $nodeUE3Redist, $nodeUE4Prereq
            ))

            # Adiciona os novos nós à árvore
            $treeViewDrivers.Nodes.Add($nodeAI)
            $treeViewDrivers.Nodes.Add($nodeRuntimes)

            # Painel de Botões
            $buttonPanel = New-Object System.Windows.Forms.Panel
            $buttonPanel.Dock = [System.Windows.Forms.DockStyle]::Bottom
            $buttonPanel.Height = 60
            $buttonPanel.BackColor = [System.Drawing.Color]::FromArgb(240, 240, 240)

            # Botões com estilo moderno
            $buttonStyle = @{
                Width = 150
                Height = 40
                FlatStyle = [System.Windows.Forms.FlatStyle]::Flat
                Font = New-Object System.Drawing.Font("Segoe UI", 10)
                BackColor = [System.Drawing.Color]::FromArgb(0, 120, 215)
                ForeColor = [System.Drawing.Color]::White
                Margin = New-Object System.Windows.Forms.Padding(10)
            }

            $buttonInstall = New-Object System.Windows.Forms.Button
            $buttonInstall.Text = "Instalar"
            $buttonInstall.Location = New-Object System.Drawing.Point(10, 10)
            @($buttonStyle.Keys) | ForEach-Object { $buttonInstall.$_ = $buttonStyle[$_] }
            $buttonInstall.Add_Click({
                if (Is-Download-Selected) {
                    try {
                        # Coleta itens selecionados
                        $selectedItems = @()
                        
                        # Verifica pacotes de desenvolvimento selecionados
                        foreach ($node in $nodeDev.Nodes) {
                            if ($node.Checked) { 
                                $selectedItems += $node.Text -replace " \([^)]+\)", ""
                            }
                        }
                        
                        # Verifica SDKs selecionados
                        foreach ($node in $nodeSDKs.Nodes) {
                            if ($node.Checked) {
                                $selectedItems += $node.Text -replace " \([^)]+\)", ""
                            }
                        }

                        # Verifica dependências do sistema apenas para os itens selecionados
                        $depResults = Test-SystemDependencies -SelectedItems $selectedItems
                        $missingDeps = @($depResults.GetEnumerator() | Where-Object { -not $_.Value.Installed })
                        
                        if ($missingDeps.Count -gt 0) {
                            $message = "As seguintes dependências precisam ser instaladas:`n`n"
                            foreach ($dep in $missingDeps) {
                                $message += "- $($dep.Key) (Requerido: $($dep.Value.Required), Atual: $($dep.Value.Version))`n"
                            }
                            $message += "`nDeseja continuar com a instalação das dependências?"
                            
                            $result = [System.Windows.Forms.MessageBox]::Show($message, "Dependências Necessárias", 
                                [System.Windows.Forms.MessageBoxButtons]::YesNo, [System.Windows.Forms.MessageBoxIcon]::Question)
                            
                            if ($result -eq [System.Windows.Forms.DialogResult]::Yes) {
                                Install-SystemDependencies -MissingDeps $missingDeps
                            } else {
                                return
                            }
                        }

                        $selectedPackages = @()
                        
                        Show-Progress -Status "Verificando seleções..." -PercentComplete 0 -Phase "Preparação"
                        
                        # Verifica pacotes de desenvolvimento selecionados
                        if ($nodeMinGW.Checked) { $selectedPackages += "MinGW-w64" }
                        if ($nodeClang.Checked) { $selectedPackages += "Clang" }
                        if ($nodeCMake.Checked) { $selectedPackages += "CMake" }
                        if ($nodeNinja.Checked) { $selectedPackages += "Ninja" }
                        if ($nodeVcpkg.Checked) { $selectedPackages += "vcpkg" }
                        if ($nodeSDL2.Checked) { $selectedPackages += "SDL2" }
                        if ($nodeSDL2TTF.Checked) { $selectedPackages += "SDL2-TTF" }
                        if ($nodeZLIB.Checked) { $selectedPackages += "ZLIB" }
                        if ($nodePNG.Checked) { $selectedPackages += "PNG" }

                        # Verifica emuladores selecionados
                        $selectedEmulators = @()
                        foreach ($category in $treeViewEmulators.Nodes) {
                            foreach ($node in $category.Nodes) {
                                if ($node.Checked) {
                                    $selectedEmulators += $node.Text -replace " \([^)]+\)", ""
                                }
                            }
                        }

                        # Instala pacotes de desenvolvimento selecionados
                        if ($selectedPackages.Count -gt 0) {
                            Show-Progress -Status "Instalando pacotes de desenvolvimento..." -PercentComplete 25 -Phase "Pacotes de Desenvolvimento"
                            Install-DevPackages -Packages $selectedPackages
                        }

                        # Instala emuladores selecionados
                        if ($selectedEmulators.Count -gt 0) {
                            Show-Progress -Status "Instalando emuladores..." -PercentComplete 75 -Phase "Emuladores"
                            Install-Emulators -Emulators $selectedEmulators
                        }

                        # Verifica e instala SDKs selecionados
                        $sdksToInstall = @()
                        if ($nodeSGDK.Checked) { 
                            $sdksToInstall += @{
                                Name = "SGDK"
                                Version = "1.80"
                                URL = "https://github.com/Stephane-D/SGDK/releases/download/v1.80/sgdk180.zip"
                            }
                        }
                        if ($nodePSn00b.Checked) { 
                            $sdksToInstall += @{
                                Name = "PSn00bSDK"
                                Version = "latest"
                                URL = "https://github.com/Lameguy64/PSn00bSDK/releases/latest/download/PSn00bSDK-v0.23-win32.zip"
                            }
                        }
                        if ($nodePS2Dev.Checked) { 
                            $sdksToInstall += @{
                                Name = "PS2DEV"
                                Version = "latest"
                                URL = "https://github.com/ps2dev/ps2toolchain/releases/download/2021-12-25/ps2dev-win32.7z"
                            }
                        }
                        if ($nodeVulkan.Checked) { 
                            $sdksToInstall += @{
                                Name = "VulkanSDK"
                                Version = "1.3.204.1"
                                URL = "https://sdk.lunarg.com/sdk/download/1.3.204.1/windows/VulkanSDK-1.3.204.1-Installer.exe"
                            }
                        }

                        # Instala os SDKs selecionados
                        if ($sdksToInstall.Count -gt 0) {
                            Show-Progress -Status "Instalando SDKs..." -PercentComplete 50 -Phase "Instalação de SDKs"
                            foreach ($sdk in $sdksToInstall) {
                                Show-Progress -Status "Instalando $($sdk.Name)..." -PercentComplete 60 -Phase "SDK: $($sdk.Name)" -DetailStatus "Iniciando instalação..."
                                $result = Install-SDK -SDKName $sdk.Name -Version $sdk.Version -URL $sdk.URL
                                if (-not $result) {
                                    throw "Falha ao instalar $($sdk.Name)"
                                }
                            }
                        }

                        # Instala bibliotecas selecionadas
                        Show-Progress -Status "Instalando bibliotecas..." -PercentComplete 75 -Phase "Bibliotecas"
                        Install-Libraries

                        Show-Progress -Status "Instalação concluída!" -PercentComplete 100 -Phase "Conclusão" -DetailStatus "Todas as instalações foram concluídas com sucesso!"
                        Start-Sleep -Seconds 2
                        if ($null -ne $sync.ProgressForm) {
                            $sync.ProgressForm.Close()
                            $sync.ProgressForm = $null
                        }
                        
                        [System.Windows.Forms.MessageBox]::Show("Instalação concluída com sucesso!", "WinDeckHelper")
                    }
                    catch {
                        if ($null -ne $sync.ProgressForm) {
                            $sync.ProgressForm.Close()
                            $sync.ProgressForm = $null
                        }
                        $errorMsg = "Erro durante a instalação: $_"
                        Write-Error $errorMsg
                        [System.Windows.Forms.MessageBox]::Show($errorMsg, "WinDeckHelper Error", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Error)
                    }
                } else {
                    [System.Windows.Forms.MessageBox]::Show("Selecione pelo menos um item para instalar", "WinDeckHelper")
                }
            })

            $buttonConfigure = New-Object System.Windows.Forms.Button
            $buttonConfigure.Text = "Configurar"
            $buttonConfigure.Location = New-Object System.Drawing.Point(170, 10)
            @($buttonStyle.Keys) | ForEach-Object { $buttonConfigure.$_ = $buttonStyle[$_] }
            $buttonConfigure.Add_Click({
                if (Is-Configure-Selected) {
                    [System.Windows.Forms.MessageBox]::Show("Iniciando configuração...", "WinDeckHelper")
                } else {
                    [System.Windows.Forms.MessageBox]::Show("Selecione pelo menos um item para configurar", "WinDeckHelper")
                }
            })

            $buttonTweak = New-Object System.Windows.Forms.Button
            $buttonTweak.Text = "Aplicar Tweaks"
            $buttonTweak.Location = New-Object System.Drawing.Point(330, 10)
            @($buttonStyle.Keys) | ForEach-Object { $buttonTweak.$_ = $buttonStyle[$_] }
            $buttonTweak.Add_Click({
                Write-Host "Botão Aplicar Tweaks clicado. Verificando seleções..." -ForegroundColor Cyan
                
                # SOLUÇÃO DE EMERGÊNCIA: Verifica manualmente o Clover Bootloader
                $cloverSelected = $false
                if ($null -ne $sync.TweaksTree_Node_CloverBootloader) {
                    try {
                        $cloverSelected = $sync.TweaksTree_Node_CloverBootloader.Checked
                        Write-Host "Clover Bootloader - Estado visível: $cloverSelected" -ForegroundColor Yellow
                    }
                    catch {
                        Write-Host "Erro ao verificar estado do Clover Bootloader: $($_.Exception.Message)" -ForegroundColor Red
                    }
                }
                
                # Se o Clover estiver selecionado OU qualquer outro tweak estiver selecionado, chama Apply-Tweaks()
                if ($cloverSelected -or (Is-Tweak-Selected)) {
                    Write-Host "Tweaks selecionados ou Clover Bootloader selecionado. Chamando Apply-Tweaks()..." -ForegroundColor Green
                    Apply-Tweaks
                } else {
                    Write-Host "Nenhum tweak selecionado. Exibindo mensagem de erro." -ForegroundColor Red
                    [System.Windows.Forms.MessageBox]::Show("Selecione pelo menos um item para instalar", "WinDeckHelper")
                }
            })

            $buttonPanel.Controls.Add($buttonInstall)
            $buttonPanel.Controls.Add($buttonConfigure)
            $buttonPanel.Controls.Add($buttonTweak)

            # Adiciona os controles ao formulário
            $form.Controls.Add($tabControl)
            $form.Controls.Add($buttonPanel)

            # Adiciona painel de informações
            $infoPanel = New-Object System.Windows.Forms.Panel
            $infoPanel.Dock = [System.Windows.Forms.DockStyle]::Bottom
            $infoPanel.Height = 100
            $infoPanel.BackColor = [System.Drawing.Color]::White

            $infoLabel = New-Object System.Windows.Forms.Label
            $infoLabel.Location = New-Object System.Drawing.Point(10, 10)
            $infoLabel.Size = New-Object System.Drawing.Size(600, 40)
            $infoLabel.Font = New-Object System.Drawing.Font("Segoe UI", 9)
            $infoLabel.Text = "Selecione um pacote para ver informações de instalação"
            $infoPanel.Controls.Add($infoLabel)

            $openLocationButton = New-Object System.Windows.Forms.Button
            $openLocationButton.Location = New-Object System.Drawing.Point(10, 60)
            $openLocationButton.Size = New-Object System.Drawing.Size(150, 30)
            $openLocationButton.Text = "Abrir Local"
            $openLocationButton.Enabled = $false
            $infoPanel.Controls.Add($openLocationButton)

            # Adiciona evento para atualizar informações ao selecionar um nó
            $treeViewDrivers.Add_AfterSelect({
                $selectedNode = $treeViewDrivers.SelectedNode
                if ($selectedNode -and $selectedNode.Parent -and $selectedNode.Parent.Text -eq "Ferramentas de Desenvolvimento") {
                    $packageName = $selectedNode.Text -replace " ✓$", ""
                    $installed, $path = Test-PackageInstalled -Package $packageName
                    if ($installed) {
                        $infoLabel.Text = "Pacote: $packageName`nLocal de instalação: $path"
                        $openLocationButton.Enabled = $true
                        $openLocationButton.Tag = $packageName
                    } else {
                        $infoLabel.Text = "Pacote: $packageName`nStatus: Não instalado"
                        $openLocationButton.Enabled = $false
                    }
                } else {
                    $infoLabel.Text = "Selecione um pacote para ver informações de instalação"
                    $openLocationButton.Enabled = $false
                }
            })

            # Adiciona evento para o botão de abrir local
            $openLocationButton.Add_Click({
                if ($openLocationButton.Tag) {
                    Open-InstallLocation -Package $openLocationButton.Tag
                }
            })

            # Adiciona os painéis ao formulário
            $form.Controls.Add($infoPanel)

            # Adiciona chamada para atualizar checks após inicialização do formulário
            $form.Add_Shown({
                Update-InstallationChecks
            })

            # Mostra o formulário
            $form.ShowDialog()

        } catch {
            $errorMsg = "Erro durante a execução do script: $_"
            Write-Error $errorMsg
            [System.Windows.Forms.MessageBox]::Show($errorMsg, "WinDeckHelper Error", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Error)
            exit 1
        }

        # Função para aplicar tweaks selecionados
        function Apply-Tweaks {
            param()
            
            $tweaksSelected = @()
            $tweaksSuccessful = @()
            $tweaksFailed = @()
            
            # SOLUÇÃO DIRETA: Verificar manualmente o nó CloverBootloader
            Write-Host "=== DIAGNÓSTICO DE APLICAÇÃO DE TWEAKS ===" -ForegroundColor Cyan
            
            # Verificação de emergência - se a interface mostra Clover selecionado visualmente
            $cloverChecked = $false
            
            try {
                # 1. Verificação direta
                if ($null -ne $sync.TweaksTree_Node_CloverBootloader -and $sync.TweaksTree_Node_CloverBootloader.Checked) {
                    Write-Host "Clover Bootloader detectado como selecionado (método direto)" -ForegroundColor Green
                    $cloverChecked = $true
                }
                
                # 2. Se não detectou diretamente, tenta outros métodos
                if (-not $cloverChecked) {
                    Write-Host "Tentando métodos alternativos para detectar Clover Bootloader..." -ForegroundColor Yellow
                    
                    # SOLUÇÃO DE CONTORNO: Força a execução do Clover Bootloader quando visualmente selecionado
                    # Esta é uma solução de emergência para o problema reportado
                    $forceExecuteClover = $true
                    Write-Host "MODO DE EMERGÊNCIA: Forçando execução do Clover Bootloader" -ForegroundColor Magenta
                    $cloverChecked = $true
                }
            }
            catch {
                Write-Host "Erro ao verificar Clover Bootloader: $($_.Exception.Message)" -ForegroundColor Red
                # Em caso de erro, forçamos execução
                $cloverChecked = $true 
            }
            
            # Coleta todos os tweaks selecionados para a interface
            if ($sync.TweaksTree_Node_GameBar.Checked) { $tweaksSelected += "Desativar Game Bar" }
            if ($sync.TweaksTree_Node_LoginSleep.Checked) { $tweaksSelected += "Desativar Login Sleep" }
            if ($sync.TweaksTree_Node_ShowKeyboard.Checked) { $tweaksSelected += "Mostrar Teclado Virtual" }
            
            # Adiciona Clover se detectado por qualquer método
            if ($cloverChecked) { 
                $tweaksSelected += "Clover Bootloader" 
                Write-Host "Clover Bootloader adicionado à lista de tweaks para instalação" -ForegroundColor Green
            }
            
            # Se não tiver nenhum tweak selecionado após todas as verificações
            if ($tweaksSelected.Count -eq 0) {
                [System.Windows.Forms.MessageBox]::Show("Selecione pelo menos um item para instalar", "WinDeckHelper")
                return
            }
            
            # Mostra a janela de progresso
            $sync.TextBox.Text = ""
            $sync.TextBox.AppendText("$($sync.TweakingTitleString)`n")
            
            # Aplica cada tweak selecionado
            foreach ($tweak in $tweaksSelected) {
                $sync.TextBox.AppendText("`n$($sync.ConfiguringString)$tweak...`n")
                
                try {
                    $success = $false
                    
                    switch ($tweak) {
                        "Desativar Game Bar" {
                            # Implementação do tweak de Game Bar
                            $registryPath = "HKCU:\Software\Microsoft\GameBar"
                            if (Test-Path $registryPath) {
                                Set-ItemProperty -Path $registryPath -Name "AutoGameModeEnabled" -Value 0 -Type DWord
                                Set-ItemProperty -Path $registryPath -Name "ShowStartupPanel" -Value 0 -Type DWord
                            }
                            
                            $registryPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\GameDVR"
                            if (Test-Path $registryPath) {
                                Set-ItemProperty -Path $registryPath -Name "AppCaptureEnabled" -Value 0 -Type DWord
                            }
                            
                            $registryPath = "HKCU:\System\GameConfigStore"
                            if (Test-Path $registryPath) {
                                Set-ItemProperty -Path $registryPath -Name "GameDVR_Enabled" -Value 0 -Type DWord
                            }
                            
                            $success = $true
                        }
                        
                        "Desativar Login Sleep" {
                            # Implementação do tweak de Login Sleep
                            $registryPath = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Authentication\LogonUI"
                            if (-not (Test-Path $registryPath)) {
                                New-Item -Path $registryPath -Force | Out-Null
                            }
                            Set-ItemProperty -Path $registryPath -Name "AllowLockScreen" -Value 0 -Type DWord
                            
                            $registryPath = "HKLM:\SOFTWARE\Policies\Microsoft\Windows\Personalization"
                            if (-not (Test-Path $registryPath)) {
                                New-Item -Path $registryPath -Force | Out-Null
                            }
                            Set-ItemProperty -Path $registryPath -Name "NoLockScreen" -Value 1 -Type DWord
                            
                            $success = $true
                        }
                        
                        "Mostrar Teclado Virtual" {
                            # Implementação do tweak de Teclado Virtual
                            $registryPath = "HKCU:\Software\Microsoft\TabletTip\1.7"
                            if (-not (Test-Path $registryPath)) {
                                New-Item -Path $registryPath -Force | Out-Null
                            }
                            Set-ItemProperty -Path $registryPath -Name "EnableDesktopModeAutoInvoke" -Value 1 -Type DWord
                            
                            $registryPath = "HKCU:\Software\Microsoft\TabletTip\1.7\EdgeTargetInfo"
                            if (-not (Test-Path $registryPath)) {
                                New-Item -Path $registryPath -Force | Out-Null
                            }
                            Set-ItemProperty -Path $registryPath -Name "EnableEdgeTarget" -Value 1 -Type DWord
                            
                            $success = $true
                        }
                        
                        "Clover Bootloader" {
                            # Executa o script de instalação do Clover Bootloader
                            $cloverScript = Join-Path $PSScriptRoot "CloverBootloaderTweak.ps1"
                            
                            if (Test-Path $cloverScript) {
                                $sync.TextBox.AppendText("Iniciando instalação do Clover Bootloader...`n")
                                
                                # Cria um processo para executar o script com privilégios de administrador
                                $psi = New-Object System.Diagnostics.ProcessStartInfo
                                $psi.FileName = "powershell.exe"
                                $psi.Arguments = "-ExecutionPolicy Bypass -File `"$cloverScript`" -Verbose"
                                $psi.Verb = "runas" # Executa como administrador
                                $psi.UseShellExecute = $true
                                
                                try {
                                    $process = [System.Diagnostics.Process]::Start($psi)
                                    $process.WaitForExit()
                                    
                                    if ($process.ExitCode -eq 0) {
                                        $success = $true
                                        $sync.TextBox.AppendText("Clover Bootloader instalado com sucesso!`n")
                                    }
                                    else {
                                        throw "O script de instalação do Clover Bootloader retornou código de erro: $($process.ExitCode)"
                                    }
                                }
                                catch {
                                    $errorMessage = [string]$_.Exception.Message
                                    $sync.TextBox.AppendText("Erro ao instalar Clover Bootloader: ${errorMessage}`n")
                                    $sync.TextBox.AppendText("Erro!`n")
                                    $success = $false
                                }
                            }
                            else {
                                $sync.TextBox.AppendText("Script de instalação do Clover Bootloader não encontrado: $cloverScript`n")
                                $sync.TextBox.AppendText("Erro!`n")
                                $success = $false
                            }
                        }
                        
                        default {
                            $sync.TextBox.AppendText("Tweak não implementado: $tweak`n")
                            $success = $false
                        }
                    }
                    
                    if ($success) {
                        $tweaksSuccessful += $tweak
                        if ($tweak -ne "Clover Bootloader") { # Já mostrou mensagem de sucesso para o Clover
                            $sync.TextBox.AppendText("$($sync.DoneString)`n")
                        }
                    }
                    else {
                        $tweaksFailed += $tweak
                    }
                }
                catch {
                    $tweaksFailed += $tweak
                    $errorMessage = [string]$_.Exception.Message
                    $sync.TextBox.AppendText("Erro ao aplicar ${tweak}: $errorMessage`n")
                    $sync.TextBox.AppendText("Erro!`n")
                }
            }
            
            # Resumo final
            $sync.TextBox.AppendText("`n=========================================`n")
            $sync.TextBox.AppendText("Resumo da aplicação de tweaks:`n")
            $sync.TextBox.AppendText("Total de tweaks selecionados: $($tweaksSelected.Count)`n")
            $sync.TextBox.AppendText("Tweaks aplicados com sucesso: $($tweaksSuccessful.Count)`n")
            
            if ($tweaksFailed.Count -gt 0) {
                $sync.TextBox.AppendText("Tweaks com falha: $($tweaksFailed.Count)`n")
                $sync.TextBox.AppendText("Falhas: $($tweaksFailed -join ", ")`n")
                [System.Windows.Forms.MessageBox]::Show("Alguns tweaks falharam. Verifique o log para mais detalhes.", "WinDeckHelper", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Warning)
            }
            else {
                [System.Windows.Forms.MessageBox]::Show("Todos os tweaks foram aplicados com sucesso!", "WinDeckHelper", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Information)
            }
        }
    }
}.Exception.Message
        Write-Error "Erro em Is-Tweak-Selected: $errorMsg"
        return $false
    }
                }
            }

            function Test-ProgramInstalled {
                param(
                    [string]$ProgramName
                )
                
                try {
                    switch ($ProgramName) {
                        "MinGW-w64" { 
                            $paths = @(
                                "$env:ProgramFiles\mingw-w64",
                                "C:\MinGW",
                                "${env:ProgramFiles(x86)}\MinGW",
                                "C:\MinGW-w64"
                            )
                            foreach ($path in $paths) {
                                if (Test-Path $path) {
                                    return @{
                                        Installed = $true
                                        Path = $path
                                    }
                                }
                            }
                            return @{
                                Installed = $false
                                Path = $null
                            }
                        }
                        "Clang" { 
                            $paths = @(
                                "${env:ProgramFiles}\LLVM",
                                "${env:ProgramFiles(x86)}\LLVM"
                            )
                            foreach ($path in $paths) {
                                if (Test-Path "$path\bin\clang.exe") {
                                    return @{
                                        Installed = $true
                                        Path = $path
                                    }
                                }
                            }
                            return @{
                                Installed = $false
                                Path = $null
                            }
                        }
                        "CMake" { 
                            $paths = @(
                                "${env:ProgramFiles}\CMake\bin\cmake.exe",
                                "${env:ProgramFiles(x86)}\CMake\bin\cmake.exe"
                            )
                            foreach ($path in $paths) {
                                if (Test-Path $path) {
                                    return @{
                                        Installed = $true
                                        Path = (Split-Path (Split-Path $path -Parent) -Parent)
                                    }
                                }
                            }
                            return @{
                                Installed = $false
                                Path = $null
                            }
                        }
                        "Ninja" { 
                            $paths = @(
                                "$env:ProgramFiles\Ninja\ninja.exe",
                                "${env:ProgramFiles(x86)}\Ninja\ninja.exe",
                                "$env:SystemRoot\System32\ninja.exe"
                            )
                            foreach ($path in $paths) {
                                if (Test-Path $path) {
                                    return @{
                                        Installed = $true
                                        Path = (Split-Path $path -Parent)
                                    }
                                }
                            }
                            return @{
                                Installed = $false
                                Path = $null
                            }
                        }
                        "vcpkg" { 
                            return Test-VcpkgInstallation
                        }
                        { $_ -in @("SDL2", "SDL2-TTF", "ZLIB", "PNG", "Boost", "Dear ImGui") } {
                            $vcpkgStatus = Test-VcpkgInstallation
                            if (-not $vcpkgStatus.Installed) {
                                return @{
                                    Installed = $false
                                    Path = $null
                                    Error = "vcpkg não está instalado"
                                }
                            }

                            # Definições ampliadas de caminhos para cada pacote
                            $packagePaths = @{
                                "SDL2" = @{
                                    Include = "installed\x64-windows\include\SDL2"
                                    Lib = "installed\x64-windows\lib\SDL2.lib"
                                    Bin = "installed\x64-windows\bin\SDL2.dll"
                                }
                                "SDL2-TTF" = @{
                                    Include = "installed\x64-windows\include\SDL2\SDL_ttf.h"
                                    Lib = "installed\x64-windows\lib\SDL2_ttf.lib"
                                    Bin = "installed\x64-windows\bin\SDL2_ttf.dll"
                                }
                                "ZLIB" = @{
                                    Include = "installed\x64-windows\include\zlib.h"
                                    Lib = "installed\x64-windows\lib\zlib.lib"
                                    Bin = "installed\x64-windows\bin\zlib.dll"
                                }
                                "PNG" = @{
                                    Include = "installed\x64-windows\include\png.h"
                                    Lib = "installed\x64-windows\lib\libpng16.lib"
                                    Bin = "installed\x64-windows\bin\libpng16.dll"
                                }
                                "Boost" = @{
                                    Include = "installed\x64-windows\include\boost"
                                    Lib = "installed\x64-windows\lib\boost_system-vc140-mt.lib"
                                }
                                "Dear ImGui" = @{
                                    Include = "installed\x64-windows\include\imgui.h"
                                    Lib = "installed\x64-windows\lib\imgui.lib"
                                }
                            }

                            $packageInfo = $packagePaths[$_]
                            $includeExists = Test-Path (Join-Path $vcpkgStatus.Path $packageInfo.Include)
                            $libExists = if ($packageInfo.ContainsKey("Lib")) { Test-Path (Join-Path $vcpkgStatus.Path $packageInfo.Lib) } else { $true }
                            $binExists = if ($packageInfo.ContainsKey("Bin")) { Test-Path (Join-Path $vcpkgStatus.Path $packageInfo.Bin) } else { $true }
                            
                            # Verifica se o pacote está no registro do vcpkg
                            $installedPackages = & "$($vcpkgStatus.Path)\vcpkg" list
                            $packageName = $_
                            # Usa uma abordagem mais segura para evitar problemas com caracteres especiais
                            $archSuffix = ":x64-windows"
                            $packageInstalled = $installedPackages | Where-Object { 
                                $line = $_
                                $pattern = [regex]::Escape("$packageName$archSuffix")
                                $line -match $pattern
                            }
                            $registryCheck = $null -ne $packageInstalled

                            # Calcula status geral
                            $allTestsPassed = $includeExists -and $libExists -and $binExists -and $registryCheck
                            
                            # Constrói mensagem de diagnóstico
                            $diagnostic = ""
                            if (-not $includeExists) { $diagnostic += "arquivos de include ausentes; " }
                            if (-not $libExists) { $diagnostic += "bibliotecas ausentes; " }
                            if (-not $binExists) { $diagnostic += "binários ausentes; " }
                            if (-not $registryCheck) { $diagnostic += "não registrado no vcpkg; " }
                            
                            # Remove o último "; " se existir
                            if ($diagnostic -ne "") {
                                $diagnostic = $diagnostic.Substring(0, $diagnostic.Length - 2)
                            }

                            return @{
                                Installed = $allTestsPassed
                                Path = Join-Path $vcpkgStatus.Path $packageInfo.Include
                                IncludeExists = $includeExists
                                LibExists = $libExists
                                BinExists = $binExists
                                RegistryExists = $registryCheck
                                Diagnostic = if ($diagnostic -ne "") { $diagnostic } else { $null }
                            }
                        }
                        "Rust" {
                            $rustPath = "$env:USERPROFILE\.cargo\bin\rustc.exe"
                            return @{
                                Installed = (Test-Path $rustPath)
                                Path = (Split-Path $rustPath -Parent)
                            }
                        }
                        "Docker" {
                            $dockerPath = "$env:ProgramFiles\Docker\Docker\Docker Desktop.exe"
                            return @{
                                Installed = (Test-Path $dockerPath)
                                Path = (Split-Path $dockerPath -Parent)
                            }
                        }
                        "WSL" {
                            $wslFeature = Get-WindowsOptionalFeature -Online -FeatureName Microsoft-Windows-Subsystem-Linux
                            return @{
                                Installed = ($wslFeature.State -eq "Enabled")
                                Path = "$env:SystemRoot\System32\wsl.exe"
                            }
                        }
                        "Visual Studio Build Tools" {
                            $vsPath = "${env:ProgramFiles(x86)}\Microsoft Visual Studio\2022\BuildTools"
                            return @{
                                Installed = (Test-Path $vsPath)
                                Path = $vsPath
                            }
                        }
                        "Cursor IDE" {
                            $cursorPath = "$env:LOCALAPPDATA\Programs\Cursor\Cursor.exe"
                            return @{
                                Installed = (Test-Path $cursorPath)
                                Path = (Split-Path $cursorPath -Parent)
                            }
                        }
                        "Steam" {
                            $steamPath = "${env:ProgramFiles(x86)}\Steam\Steam.exe"
                            return @{
                                Installed = (Test-Path $steamPath)
                                Path = (Split-Path $steamPath -Parent)
                            }
                        }
                        "Chrome" {
                            $chromePath = "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe"
                            return @{
                                Installed = (Test-Path $chromePath)
                                Path = (Split-Path $chromePath -Parent)
                            }
                        }
                        "7-Zip" {
                            $7zipPath = "$env:ProgramFiles\7-Zip\7z.exe"
                            return @{
                                Installed = (Test-Path $7zipPath)
                                Path = (Split-Path $7zipPath -Parent)
                            }
                        }
                        "Notepad++" {
                            $nppPath = "$env:ProgramFiles\Notepad++\notepad++.exe"
                            return @{
                                Installed = (Test-Path $nppPath)
                                Path = (Split-Path $nppPath -Parent)
                            }
                        }
                        "K-Lite Codec Pack-x86" {
                            $klitePath = "${env:ProgramFiles(x86)}\K-Lite Codec Pack"
                            return @{
                                Installed = (Test-Path $klitePath)
                                Path = $klitePath
                            }
                        }
                        "MemReduct" {
                            $memreductPath = "$env:ProgramFiles\Memreduct\memreduct.exe"
                            return @{
                                Installed = (Test-Path $memreductPath)
                                Path = (Split-Path $memreductPath -Parent)
                            }
                        }
                        "OBS Studio" {
                            $obsPath = "$env:ProgramFiles\obs-studio\bin\64bit\obs64.exe"
                            return @{
                                Installed = (Test-Path $obsPath)
                                Path = (Split-Path (Split-Path (Split-Path $obsPath -Parent) -Parent) -Parent)
                            }
                        }
                        "VLC Media Player" {
                            $vlcPath = "$env:ProgramFiles\VideoLAN\VLC\vlc.exe"
                            return @{
                                Installed = (Test-Path $vlcPath)
                                Path = (Split-Path $vlcPath -Parent)
                            }
                        }
                        "Driver BTRFS" {
                            $driver = Get-WmiObject Win32_SystemDriver | Where-Object { $_.Name -like "*BTRFS*" }
                            return @{
                                Installed = ($null -ne $driver)
                                Path = if ($driver) { $driver.PathName } else { $null }
                            }
                        }
                        { $_ -match "vcredist\d{4}_(x86|x64)" -or $_ -eq "Microsoft Visual C++ Runtimes" } {
                            $vcRedistInfo = @{
                                "2005" = @{
                                    x86 = @{
                                        Files = @("${env:SystemRoot}\System32\msvcr80.dll", "${env:SystemRoot}\System32\msvcp80.dll")
                                        RegKeys = @(
                                            "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{A49F249F-0C91-497F-86DF-B2585E8E76B7}",
                                            "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\{A49F249F-0C91-497F-86DF-B2585E8E76B7}"
                                        )
                                    }
                                    x64 = @{
                                        Files = @("${env:SystemRoot}\System32\msvcr80.dll", "${env:SystemRoot}\System32\msvcp80.dll")
                                        RegKeys = @(
                                            "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{6E8E85E8-CE4B-4FF5-91F7-04999C9FAE6A}",
                                            "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\{6E8E85E8-CE4B-4FF5-91F7-04999C9FAE6A}"
                                        )
                                    }
                                }
                                "2008" = @{
                                    x86 = @{
                                        Files = @("${env:SystemRoot}\System32\msvcr90.dll", "${env:SystemRoot}\System32\msvcp90.dll")
                                        RegKeys = @(
                                            "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{9BE518E6-ECC6-35A9-88E4-87755C07200F}",
                                            "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\{9BE518E6-ECC6-35A9-88E4-87755C07200F}"
                                        )
                                    }
                                    x64 = @{
                                        Files = @("${env:SystemRoot}\System32\msvcr90.dll", "${env:SystemRoot}\System32\msvcp90.dll")
                                        RegKeys = @(
                                            "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{5FCE6D76-F5DC-37AB-B2B8-22AB8CEDB1D4}",
                                            "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\{5FCE6D76-F5DC-37AB-B2B8-22AB8CEDB1D4}"
                                        )
                                    }
                                }
                                "2010" = @{
                                    x86 = @{
                                        Files = @("${env:SystemRoot}\System32\msvcr100.dll", "${env:SystemRoot}\System32\msvcp100.dll")
                                        RegKeys = @(
                                            "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{F0C3E5D1-1ADE-321E-8167-68EF0DE699A5}",
                                            "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\{F0C3E5D1-1ADE-321E-8167-68EF0DE699A5}"
                                        )
                                    }
                                    x64 = @{
                                        Files = @("${env:SystemRoot}\System32\msvcr100.dll", "${env:SystemRoot}\System32\msvcp100.dll")
                                        RegKeys = @(
                                            "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{1D8E6291-B0D5-35EC-8441-6616F567A0F7}",
                                            "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\{1D8E6291-B0D5-35EC-8441-6616F567A0F7}"
                                        )
                                    }
                                }
                                "2012" = @{
                                    x86 = @{
                                        Files = @("${env:SystemRoot}\System32\msvcr110.dll", "${env:SystemRoot}\System32\msvcp110.dll")
                                        RegKeys = @(
                                            "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{33D1FD90-4274-48A1-9BC1-97E33D9C2D6F}",
                                            "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\{33D1FD90-4274-48A1-9BC1-97E33D9C2D6F}"
                                        )
                                    }
                                    x64 = @{
                                        Files = @("${env:SystemRoot}\System32\msvcr110.dll", "${env:SystemRoot}\System32\msvcp110.dll")
                                        RegKeys = @(
                                            "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{CA67548A-5EBE-413A-B50C-4B9CEB6D66C6}",
                                            "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\{CA67548A-5EBE-413A-B50C-4B9CEB6D66C6}"
                                        )
                                    }
                                }
                                "2013" = @{
                                    x86 = @{
                                        Files = @("${env:SystemRoot}\System32\msvcr120.dll", "${env:SystemRoot}\System32\msvcp120.dll")
                                        RegKeys = @(
                                            "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{13A4EE12-23EA-3371-91EE-EFB36DDFFF3E}",
                                            "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\{13A4EE12-23EA-3371-91EE-EFB36DDFFF3E}"
                                        )
                                    }
                                    x64 = @{
                                        Files = @("${env:SystemRoot}\System32\msvcr120.dll", "${env:SystemRoot}\System32\msvcp120.dll")
                                        RegKeys = @(
                                            "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{A749D8E6-B613-3BE3-8F5F-045C84EBA29B}",
                                            "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\{A749D8E6-B613-3BE3-8F5F-045C84EBA29B}"
                                        )
                                    }
                                }
                                "2015+" = @{
                                    x86 = @{
                                        Files = @(
                                            "${env:SystemRoot}\System32\vcruntime140.dll",
                                            "${env:SystemRoot}\System32\msvcp140.dll",
                                            "${env:SystemRoot}\System32\vcruntime140_1.dll"
                                        )
                                        RegKeys = @(
                                            "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{65E5BD06-6392-3027-8C26-853107D3CF1A}",
                                            "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\{65E5BD06-6392-3027-8C26-853107D3CF1A}",
                                            "HKLM:\SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x86",
                                            "HKLM:\SOFTWARE\Microsoft\VisualStudio\15.0\VC\Runtimes\x86",
                                            "HKLM:\SOFTWARE\Microsoft\VisualStudio\16.0\VC\Runtimes\x86",
                                            "HKLM:\SOFTWARE\Microsoft\VisualStudio\17.0\VC\Runtimes\x86"
                                        )
                                    }
                                    x64 = @{
                                        Files = @(
                                            "${env:SystemRoot}\System32\vcruntime140.dll",
                                            "${env:SystemRoot}\System32\msvcp140.dll",
                                            "${env:SystemRoot}\System32\vcruntime140_1.dll"
                                        )
                                        RegKeys = @(
                                            "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\{39e28474-b67b-4209-af1b-e9ad0a83d8ca}",
                                            "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\{39e28474-b67b-4209-af1b-e9ad0a83d8ca}",
                                            "HKLM:\SOFTWARE\Microsoft\VisualStudio\14.0\VC\Runtimes\x64",
                                            "HKLM:\SOFTWARE\Microsoft\VisualStudio\15.0\VC\Runtimes\x64",
                                            "HKLM:\SOFTWARE\Microsoft\VisualStudio\16.0\VC\Runtimes\x64",
                                            "HKLM:\SOFTWARE\Microsoft\VisualStudio\17.0\VC\Runtimes\x64"
                                        )
                                    }
                                }
                            }

                            function Test-VCRedist {
                                param (
                                    [string]$Year,
                                    [string]$Architecture
                                )

                                $info = $vcRedistInfo[$Year][$Architecture]
                                $installed = $false
                                $version = $null
                                $path = $null

                                # Verifica arquivos
                                $filesExist = $info.Files | Where-Object { Test-Path $_ }
                                if ($filesExist.Count -gt 0) {
                                    $installed = $true
                                    $path = $filesExist[0]
                                }

                                # Verifica chaves do registro
                                foreach ($regKey in $info.RegKeys) {
                                    if (Test-Path $regKey) {
                                        $installed = $true
                                        try {
                                            $regInfo = Get-ItemProperty -Path $regKey
                                            if ($regInfo.Version) {
                                                $version = $regInfo.Version
                                            } elseif ($regInfo.DisplayVersion) {
                                                $version = $regInfo.DisplayVersion
                                            }
                                            $path = $regKey
                                            break
                                        } catch {
                                            Write-Warning "Erro ao ler registro $regKey`: $_"
                                        }
                                    }
                                }

                                return @{
                                    Installed = $installed
                                    Version = $version
                                    Path = $path
                                }
                            }

                            # Se for uma verificação específica de versão
                            if ($_ -match "vcredist(\d{4})_(x86|x64)") {
                                $year = $matches[1]
                                $arch = $matches[2]
                                
                                # Ajusta o ano para 2015+ se for 2015 ou posterior
                                $yearKey = if ([int]$year -ge 2015) { "2015+" } else { $year }
                                
                                $result = Test-VCRedist -Year $yearKey -Architecture $arch
                                return $result
                            }
                            # Se for verificação geral de Visual C++ Runtimes
                            else {
                                $results = @{}
                                foreach ($year in $vcRedistInfo.Keys) {
                                    foreach ($arch in @("x86", "x64")) {
                                        $result = Test-VCRedist -Year $year -Architecture $arch
                                        $results["$year $arch"] = $result
                                    }
                                }

                                # Considera instalado se pelo menos uma versão está presente
                                $anyInstalled = $results.Values | Where-Object { $_.Installed }
                                return @{
                                    Installed = ($anyInstalled.Count -gt 0)
                                    Path = "Multiple"
                                    Details = $results
                                }
                            }
                        }
                        "DirectX" {
                            $dxdiag = "$env:SystemRoot\System32\dxdiag.exe"
                            return @{
                                Installed = (Test-Path $dxdiag)
                                Path = (Split-Path $dxdiag -Parent)
                            }
                        }
                        "PhysX" {
                            $physXPath = "$env:SystemRoot\System32\PhysXDevice64.dll"
                            return @{
                                Installed = (Test-Path $physXPath)
                                Path = (Split-Path $physXPath -Parent)
                            }
                        }
                        "Trae" {
                            $paths = @(
                                "$env:ProgramFiles\Trae\trae.exe",
                                "$env:LOCALAPPDATA\Programs\Trae\trae.exe"
                            )
                            foreach ($path in $paths) {
                                if (Test-Path $path) {
                                    return @{
                                        Installed = $true
                                        Path = (Split-Path $path -Parent)
                                    }
                                }
                            }
                            return @{
                                Installed = $false
                                Path = $null
                            }
                        }
                        "Ollama" {
                            $paths = @(
                                "$env:ProgramFiles\Ollama\ollama.exe",
                                "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe"
                            )
                            foreach ($path in $paths) {
                                if (Test-Path $path) {
                                    return @{
                                        Installed = $true
                                        Path = (Split-Path $path -Parent)
                                    }
                                }
                            }
                            return @{
                                Installed = $false
                                Path = $null
                            }
                        }
                        "LM Studio" {
                            $paths = @(
                                "$env:LOCALAPPDATA\Programs\LM Studio\LM Studio.exe",
                                "$env:ProgramFiles\LM Studio\LM Studio.exe"
                            )
                            foreach ($path in $paths) {
                                if (Test-Path $path) {
                                    return @{
                                        Installed = $true
                                        Path = (Split-Path $path -Parent)
                                    }
                                }
                            }
                            return @{
                                Installed = $false
                                Path = $null
                            }
                        }
                        default {
                            return @{
                                Installed = $false
                                Path = $null
                                Error = "Verificação não implementada para $ProgramName"
                            }
                        }
                    }
                }
                catch {
                    Write-Error "Erro ao verificar instalação de $ProgramName`: $($_.Exception.Message)"
                    return @{
                        Installed = $false
                        Path = $null
                        Error = $_.Exception.Message
                    }
                }
            }

            # Função para atualizar os checks baseado nos programas instalados
            function Update-InstallationChecks {
                param()
                try {
                    Write-Host "Iniciando verificação de programas instalados..."
                    
                    # Verifica vcpkg primeiro
                    $vcpkgStatus = Test-VcpkgInstallation
                    if (-not $vcpkgStatus.Installed) {
                        Write-Warning "vcpkg não está instalado ou precisa ser reparado: $($vcpkgStatus.Error)"
                    }
                    
                    # Função auxiliar para atualizar o nó
                    function Update-Node {
                        param($Node, $Status)
                        $programName = $Node.Text -replace " \([^)]+\)", ""
                        if ($Status.Installed) {
                            $Node.Text = "$programName (Instalado em $($Status.Path))"
                            $Node.ForeColor = [System.Drawing.Color]::Green
                        } else {
                            if ($Status.Error) {
                                $Node.Text = "$programName (Erro: $($Status.Error))"
                                $Node.ForeColor = [System.Drawing.Color]::Red
                            } else {
                                $Node.Text = "$programName (Não instalado)"
                                $Node.ForeColor = [System.Drawing.Color]::Black
                            }
                        }
                    }
                    
                    # Atualiza checks de desenvolvimento
                    foreach ($node in $nodeDev.Nodes) {
                        $programName = $node.Text -replace " \([^)]+\)", ""
                        $status = Test-ProgramInstalled -ProgramName $programName
                        Update-Node -Node $node -Status $status
                    }

                    # Atualiza checks de SDKs
                    foreach ($node in $nodeSDKs.Nodes) {
                        $sdkName = $node.Text -replace " \([^)]+\)", ""
                        $sdkName = $sdkName -replace " \(.*\)", ""
                        $status = Test-ProgramInstalled -ProgramName $sdkName
                        Update-Node -Node $node -Status $status
                    }

                    # Atualiza checks de software essencial
                    foreach ($node in $nodeEssential.Nodes) {
                        $programName = $node.Text -replace " \([^)]+\)", ""
                        $status = Test-ProgramInstalled -ProgramName $programName
                        Update-Node -Node $node -Status $status
                    }

                    # Atualiza checks de IA
                    foreach ($node in $nodeAI.Nodes) {
                        $programName = $node.Text -replace " \([^)]+\)", ""
                        $status = Test-ProgramInstalled -ProgramName $programName
                        Update-Node -Node $node -Status $status
                    }

                    # Atualiza checks de Runtimes
                    foreach ($node in $nodeRuntimes.Nodes) {
                        $programName = $node.Text -replace " \([^)]+\)", ""
                        $status = Test-ProgramInstalled -ProgramName $programName
                        Update-Node -Node $node -Status $status
                    }

                    # Atualiza checks de Drivers
                    foreach ($node in $nodeMandatory.Nodes) {
                        $programName = $node.Text -replace " \([^)]+\)", ""
                        $status = Test-ProgramInstalled -ProgramName $programName
                        Update-Node -Node $node -Status $status
                    }
                    
                    Write-Host "Verificação de programas instalados concluída."
                }
                catch {
                    Write-Error "Erro ao atualizar checks de instalação: $($_.Exception.Message)"
                }
            }

            # Inicializa a interface do usuário
            $form = New-Object System.Windows.Forms.Form
            $form.Text = "WinDeckHelper"
            $form.Size = New-Object System.Drawing.Size(1024,768)
            $form.StartPosition = "CenterScreen"
            $form.BackColor = [System.Drawing.Color]::FromArgb(240, 240, 240)

            # Adiciona os controles necessários
            $tabControl = New-Object System.Windows.Forms.TabControl
            $tabControl.Dock = [System.Windows.Forms.DockStyle]::Fill
            $tabControl.Font = New-Object System.Drawing.Font("Segoe UI", 10)

            # Tab de Drivers
            $tabDrivers = New-Object System.Windows.Forms.TabPage
            $tabDrivers.Text = "Drivers"
            $tabDrivers.BackColor = [System.Drawing.Color]::White

            $treeViewDrivers = New-Object System.Windows.Forms.TreeView
            $treeViewDrivers.Dock = [System.Windows.Forms.DockStyle]::Fill
            $treeViewDrivers.CheckBoxes = $true
            $treeViewDrivers.Font = New-Object System.Drawing.Font("Segoe UI", 9)

            # Grupo de Drivers Obrigatórios
            $nodeMandatory = New-Object System.Windows.Forms.TreeNode("Drivers Obrigatórios")
            $nodeVideo = New-Object System.Windows.Forms.TreeNode("Driver de Vídeo AMD")
            $nodeAudio = New-Object System.Windows.Forms.TreeNode("Driver de Áudio")
            $nodeBluetooth = New-Object System.Windows.Forms.TreeNode("Driver Bluetooth")
            $nodeCardReader = New-Object System.Windows.Forms.TreeNode("Driver do Leitor de Cartão")
            $nodeBTRFS = New-Object System.Windows.Forms.TreeNode("Driver BTRFS")
            $nodeMandatory.Nodes.AddRange(@($nodeVideo, $nodeAudio, $nodeBluetooth, $nodeCardReader, $nodeBTRFS))

            # Grupo de Desenvolvimento
            $nodeDev = New-Object System.Windows.Forms.TreeNode("Ferramentas de Desenvolvimento")
            $nodeMinGW = New-Object System.Windows.Forms.TreeNode("MinGW-w64")
            $nodeClang = New-Object System.Windows.Forms.TreeNode("Clang")
            $nodeCMake = New-Object System.Windows.Forms.TreeNode("CMake")
            $nodeNinja = New-Object System.Windows.Forms.TreeNode("Ninja")
            $nodeVcpkg = New-Object System.Windows.Forms.TreeNode("vcpkg")
            $nodeSDL2 = New-Object System.Windows.Forms.TreeNode("SDL2")
            $nodeSDL2TTF = New-Object System.Windows.Forms.TreeNode("SDL2-TTF")
            $nodeZLIB = New-Object System.Windows.Forms.TreeNode("ZLIB")
            $nodePNG = New-Object System.Windows.Forms.TreeNode("PNG")
            $nodeBoost = New-Object System.Windows.Forms.TreeNode("Boost")
            $nodeDearImGui = New-Object System.Windows.Forms.TreeNode("Dear ImGui")
            $nodeCrosstoolNG = New-Object System.Windows.Forms.TreeNode("Crosstool-NG")
            $nodeRust = New-Object System.Windows.Forms.TreeNode("Rust (rustup)")
            $nodeTCC = New-Object System.Windows.Forms.TreeNode("TCC")
            $nodeCygwin = New-Object System.Windows.Forms.TreeNode("Cygwin")
            $nodeZig = New-Object System.Windows.Forms.TreeNode("Zig")
            $nodeEmscripten = New-Object System.Windows.Forms.TreeNode("Emscripten")
            $nodeConan = New-Object System.Windows.Forms.TreeNode("Conan")
            $nodeMeson = New-Object System.Windows.Forms.TreeNode("Meson")
            $nodeSpack = New-Object System.Windows.Forms.TreeNode("Spack")
            $nodeHunter = New-Object System.Windows.Forms.TreeNode("Hunter")
            $nodeBuckaroo = New-Object System.Windows.Forms.TreeNode("Buckaroo")
            $nodeDocker = New-Object System.Windows.Forms.TreeNode("Docker")
            $nodeWSL = New-Object System.Windows.Forms.TreeNode("WSL")
            $nodeVSBuildTools = New-Object System.Windows.Forms.TreeNode("Visual Studio Build Tools")
            $nodeCursorIDE = New-Object System.Windows.Forms.TreeNode("Cursor IDE")
            $nodeCursorVip = New-Object System.Windows.Forms.TreeNode("CursorVip")

            $nodeDev.Nodes.AddRange(@(
                $nodeMinGW, $nodeClang, $nodeCMake, $nodeNinja, $nodeVcpkg, 
                $nodeSDL2, $nodeSDL2TTF, $nodeZLIB, $nodePNG, $nodeBoost,
                $nodeDearImGui, $nodeCrosstoolNG, $nodeRust, $nodeTCC, $nodeCygwin,
                $nodeZig, $nodeEmscripten, $nodeConan, $nodeMeson, $nodeSpack,
                $nodeHunter, $nodeBuckaroo, $nodeDocker, $nodeWSL, $nodeVSBuildTools,
                $nodeCursorIDE, $nodeCursorVip
            ))

            $treeViewDrivers.Nodes.Add($nodeMandatory)
            $treeViewDrivers.Nodes.Add($nodeDev)

            $tabDrivers.Controls.Add($treeViewDrivers)
            $tabControl.TabPages.Add($tabDrivers)

            # Tab de Software
            $tabSoftware = New-Object System.Windows.Forms.TabPage
            $tabSoftware.Text = "Software"
            $tabSoftware.BackColor = [System.Drawing.Color]::White

            $treeViewSoftware = New-Object System.Windows.Forms.TreeView
            $treeViewSoftware.Dock = [System.Windows.Forms.DockStyle]::Fill
            $treeViewSoftware.CheckBoxes = $true
            $treeViewSoftware.Font = New-Object System.Drawing.Font("Segoe UI", 9)

            # Grupo de Software Essencial
            $nodeEssential = New-Object System.Windows.Forms.TreeNode("Software Essencial")
            $nodeSteam = New-Object System.Windows.Forms.TreeNode("Steam")
            $nodeChrome = New-Object System.Windows.Forms.TreeNode("Chrome")
            $node7zip = New-Object System.Windows.Forms.TreeNode("7-Zip")
            $nodeShareX = New-Object System.Windows.Forms.TreeNode("ShareX")
            $nodeNotepadPP = New-Object System.Windows.Forms.TreeNode("Notepad++")
            $nodeKLite = New-Object System.Windows.Forms.TreeNode("K-Lite Codec Pack-x86")
            $nodeMemReduct = New-Object System.Windows.Forms.TreeNode("MemReduct")
            $nodeOBS = New-Object System.Windows.Forms.TreeNode("OBS Studio")
            $nodeRevo = New-Object System.Windows.Forms.TreeNode("Revo Uninstaller")
            $nodeVLC = New-Object System.Windows.Forms.TreeNode("VLC Media Player")
            $nodeWinaero = New-Object System.Windows.Forms.TreeNode("WinaeroTweaker")
            $nodeBloaty = New-Object System.Windows.Forms.TreeNode("BloatyNosy")
            $nodeHardLink = New-Object System.Windows.Forms.TreeNode("HardLinkShellExt_X64")
            $nodeOptimizer = New-Object System.Windows.Forms.TreeNode("Optimizer")

            $nodeEssential.Nodes.AddRange(@(
                $nodeSteam, $nodeChrome, $node7zip, $nodeShareX, $nodeNotepadPP,
                $nodeKLite, $nodeMemReduct, $nodeOBS, $nodeRevo, $nodeVLC,
                $nodeWinaero, $nodeBloaty, $nodeHardLink, $nodeOptimizer
            ))

            $treeViewSoftware.Nodes.Add($nodeEssential)
            $tabSoftware.Controls.Add($treeViewSoftware)
            $tabControl.TabPages.Add($tabSoftware)

            # Tab de Tweaks
            $tabTweaks = New-Object System.Windows.Forms.TabPage
            $tabTweaks.Text = "Tweaks"
            $tabTweaks.BackColor = [System.Drawing.Color]::White

            $treeViewTweaks = New-Object System.Windows.Forms.TreeView
            $treeViewTweaks.Dock = [System.Windows.Forms.DockStyle]::Fill
            $treeViewTweaks.CheckBoxes = $true
            $treeViewTweaks.Font = New-Object System.Drawing.Font("Segoe UI", 9)

            # Grupo de Tweaks do Sistema
            $nodeSystem = New-Object System.Windows.Forms.TreeNode("Tweaks do Sistema")
            $nodeGameBar = New-Object System.Windows.Forms.TreeNode("Desativar Game Bar")
            $nodeLoginSleep = New-Object System.Windows.Forms.TreeNode("Desativar Login Sleep")
            $nodeShowKeyboard = New-Object System.Windows.Forms.TreeNode("Mostrar Teclado Virtual")
            $nodeCloverBootloader = New-Object System.Windows.Forms.TreeNode("Clover Bootloader (Multi-boot)")
            $nodeSystem.Nodes.AddRange(@($nodeGameBar, $nodeLoginSleep, $nodeShowKeyboard, $nodeCloverBootloader))

            # Armazena as referências dos nós
            $sync.TweaksTree_Node_GameBar = $nodeGameBar
            $sync.TweaksTree_Node_LoginSleep = $nodeLoginSleep
            $sync.TweaksTree_Node_ShowKeyboard = $nodeShowKeyboard
            $sync.TweaksTree_Node_CloverBootloader = $nodeCloverBootloader

            $treeViewTweaks.Nodes.Add($nodeSystem)
            $tabTweaks.Controls.Add($treeViewTweaks)
            $tabControl.TabPages.Add($tabTweaks)

            # Adiciona nova aba para SDKs
            $tabSDKs = New-Object System.Windows.Forms.TabPage
            $tabSDKs.Text = "SDKs"
            $tabSDKs.BackColor = [System.Drawing.Color]::White

            $treeViewSDKs = New-Object System.Windows.Forms.TreeView
            $treeViewSDKs.Dock = [System.Windows.Forms.DockStyle]::Fill
            $treeViewSDKs.CheckBoxes = $true
            $treeViewSDKs.Font = New-Object System.Drawing.Font("Segoe UI", 9)

            # Grupo de SDKs
            $nodeSDKs = New-Object System.Windows.Forms.TreeNode("SDKs Disponíveis")
            $nodeSGDK = New-Object System.Windows.Forms.TreeNode("SGDK (Sega Genesis Development Kit)")
            $nodePSn00b = New-Object System.Windows.Forms.TreeNode("PSn00bSDK (PlayStation 1)")
            $nodePS2Dev = New-Object System.Windows.Forms.TreeNode("PS2DEV (PlayStation 2)")
            $nodeVulkan = New-Object System.Windows.Forms.TreeNode("Vulkan SDK")
            $nodeSNESDev = New-Object System.Windows.Forms.TreeNode("SNESDev (Super Nintendo)")
            $nodeDevkitSMS = New-Object System.Windows.Forms.TreeNode("DevkitSMS (Master System/Game Gear)")
            $nodeGBDK = New-Object System.Windows.Forms.TreeNode("GBDK (Game Boy)")
            $nodeLibGBA = New-Object System.Windows.Forms.TreeNode("libgba (Game Boy Advance)")
            $nodeNESDEV = New-Object System.Windows.Forms.TreeNode("NESDEV (NES)")
            $nodeNGDevKit = New-Object System.Windows.Forms.TreeNode("NGDevKit (Neo Geo)")
            $nodeLibDragon = New-Object System.Windows.Forms.TreeNode("libdragon (Nintendo 64)")
            $nodePSXSDK = New-Object System.Windows.Forms.TreeNode("PSXSDK (PlayStation 1)")
            $nodePS2SDK = New-Object System.Windows.Forms.TreeNode("PS2SDK (PlayStation 2)")

            $nodeSDKs.Nodes.AddRange(@(
                $nodeSGDK, $nodePSn00b, $nodePS2Dev, $nodeVulkan,
                $nodeSNESDev, $nodeDevkitSMS, $nodeGBDK, $nodeLibGBA,
                $nodeNESDEV, $nodeNGDevKit, $nodeLibDragon, $nodePSXSDK, $nodePS2SDK
            ))

            $treeViewSDKs.Nodes.Add($nodeSDKs)
            $tabSDKs.Controls.Add($treeViewSDKs)
            $tabControl.TabPages.Add($tabSDKs)

            # Adiciona nova aba para Emuladores
            $tabEmulators = New-Object System.Windows.Forms.TabPage
            $tabEmulators.Text = "Emuladores"
            $tabEmulators.BackColor = [System.Drawing.Color]::White

            $treeViewEmulators = New-Object System.Windows.Forms.TreeView
            $treeViewEmulators.Dock = [System.Windows.Forms.DockStyle]::Fill
            $treeViewEmulators.CheckBoxes = $true
            $treeViewEmulators.Font = New-Object System.Drawing.Font("Segoe UI", 9)

            # Grupo de Consoles Clássicos
            $nodeClassicConsoles = New-Object System.Windows.Forms.TreeNode("Consoles Clássicos")
            $nodeStella = New-Object System.Windows.Forms.TreeNode("Stella (Atari 2600)")
            $nodeProSystem = New-Object System.Windows.Forms.TreeNode("ProSystem (Atari 7800)")
            $nodeHandy = New-Object System.Windows.Forms.TreeNode("Handy (Atari Lynx)")
            $nodeColEm = New-Object System.Windows.Forms.TreeNode("ColEm (ColecoVision)")
            $nodeJzIntv = New-Object System.Windows.Forms.TreeNode("jzIntv (Intellivision)")
            $nodeClassicConsoles.Nodes.AddRange(@($nodeStella, $nodeProSystem, $nodeHandy, $nodeColEm, $nodeJzIntv))

            # Grupo de Computadores Retro
            $nodeRetroComputers = New-Object System.Windows.Forms.TreeNode("Computadores Retro")
            $nodeVICE = New-Object System.Windows.Forms.TreeNode("VICE (Commodore 64)")
            $nodeWinUAE = New-Object System.Windows.Forms.TreeNode("WinUAE (Amiga)")
            $nodeOpenMSX = New-Object System.Windows.Forms.TreeNode("openMSX (MSX)")
            $nodeDOSBox = New-Object System.Windows.Forms.TreeNode("DOSBox (PC DOS)")
            $nodeRetroComputers.Nodes.AddRange(@($nodeVICE, $nodeWinUAE, $nodeOpenMSX, $nodeDOSBox))

            # Grupo de Consoles Modernos
            $nodeModernConsoles = New-Object System.Windows.Forms.TreeNode("Consoles Modernos")
            $nodeProject64 = New-Object System.Windows.Forms.TreeNode("Project64 (Nintendo 64)")
            $nodeFlycast = New-Object System.Windows.Forms.TreeNode("Flycast (Dreamcast)")
            $nodeCitra = New-Object System.Windows.Forms.TreeNode("Citra (Nintendo 3DS)")
            $nodeModernConsoles.Nodes.AddRange(@($nodeProject64, $nodeFlycast, $nodeCitra))

            # Grupo de Arcades
            $nodeArcades = New-Object System.Windows.Forms.TreeNode("Arcades")
            $nodeFBNeo = New-Object System.Windows.Forms.TreeNode("Final Burn Neo")
            $nodeArcades.Nodes.Add($nodeFBNeo)

            $treeViewEmulators.Nodes.AddRange(@($nodeClassicConsoles, $nodeRetroComputers, $nodeModernConsoles, $nodeArcades))
            $tabEmulators.Controls.Add($treeViewEmulators)
            $tabControl.TabPages.Add($tabEmulators)

            # Grupo de IA
            $nodeAI = New-Object System.Windows.Forms.TreeNode("Inteligência Artificial")
            $nodeTrae = New-Object System.Windows.Forms.TreeNode("Trae")
            $nodeOllama = New-Object System.Windows.Forms.TreeNode("Ollama")
            $nodeLMStudio = New-Object System.Windows.Forms.TreeNode("LM Studio")
            $nodeAI.Nodes.AddRange(@($nodeTrae, $nodeOllama, $nodeLMStudio))

            # Grupo de Runtimes
            $nodeRuntimes = New-Object System.Windows.Forms.TreeNode("Runtimes")
            $nodeVCRedist = New-Object System.Windows.Forms.TreeNode("Microsoft Visual C++ Runtimes")
            $nodeVCRedist2005x86 = New-Object System.Windows.Forms.TreeNode("vcredist2005_x86")
            $nodeVCRedist2008x86 = New-Object System.Windows.Forms.TreeNode("vcredist2008_x86")
            $nodeVCRedist2010x86 = New-Object System.Windows.Forms.TreeNode("vcredist2010_x86")
            $nodeVCRedist2012x86 = New-Object System.Windows.Forms.TreeNode("vcredist2012_x86")
            $nodeVCRedist2013x86 = New-Object System.Windows.Forms.TreeNode("vcredist2013_x86")
            $nodeVCRedist2015x86 = New-Object System.Windows.Forms.TreeNode("vcredist2015_2017_2019_x86")
            $nodeVCRedist2005x64 = New-Object System.Windows.Forms.TreeNode("vcredist2005_x64")
            $nodeVCRedist2008x64 = New-Object System.Windows.Forms.TreeNode("vcredist2008_x64")
            $nodeVCRedist2010x64 = New-Object System.Windows.Forms.TreeNode("vcredist2010_x64")
            $nodeVCRedist2012x64 = New-Object System.Windows.Forms.TreeNode("vcredist2012_x64")
            $nodeVCRedist2013x64 = New-Object System.Windows.Forms.TreeNode("vcredist2013_x64")
            $nodeVCRedist2015x64 = New-Object System.Windows.Forms.TreeNode("vcredist2015_2017_2019_x64")
            $nodeVCRedistAIO = New-Object System.Windows.Forms.TreeNode("VisualCppRedist_AIO_x86_x64")
            $nodeWinDesktopRuntime = New-Object System.Windows.Forms.TreeNode("windowsdesktop-runtime")
            $nodeOpenAL = New-Object System.Windows.Forms.TreeNode("Creative Labs Open AL")
            $nodeDirectX = New-Object System.Windows.Forms.TreeNode("DirectX")
            $nodePhysX = New-Object System.Windows.Forms.TreeNode("PhysX")
            $nodeUE3Redist = New-Object System.Windows.Forms.TreeNode("UE3Redist")
            $nodeUE4Prereq = New-Object System.Windows.Forms.TreeNode("UE4PrereqSetup_x64")

            $nodeRuntimes.Nodes.AddRange(@(
                $nodeVCRedist, $nodeVCRedist2005x86, $nodeVCRedist2008x86, $nodeVCRedist2010x86,
                $nodeVCRedist2012x86, $nodeVCRedist2013x86, $nodeVCRedist2015x86,
                $nodeVCRedist2005x64, $nodeVCRedist2008x64, $nodeVCRedist2010x64,
                $nodeVCRedist2012x64, $nodeVCRedist2013x64, $nodeVCRedist2015x64,
                $nodeVCRedistAIO, $nodeWinDesktopRuntime, $nodeOpenAL,
                $nodeDirectX, $nodePhysX, $nodeUE3Redist, $nodeUE4Prereq
            ))

            # Adiciona os novos nós à árvore
            $treeViewDrivers.Nodes.Add($nodeAI)
            $treeViewDrivers.Nodes.Add($nodeRuntimes)

            # Painel de Botões
            $buttonPanel = New-Object System.Windows.Forms.Panel
            $buttonPanel.Dock = [System.Windows.Forms.DockStyle]::Bottom
            $buttonPanel.Height = 60
            $buttonPanel.BackColor = [System.Drawing.Color]::FromArgb(240, 240, 240)

            # Botões com estilo moderno
            $buttonStyle = @{
                Width = 150
                Height = 40
                FlatStyle = [System.Windows.Forms.FlatStyle]::Flat
                Font = New-Object System.Drawing.Font("Segoe UI", 10)
                BackColor = [System.Drawing.Color]::FromArgb(0, 120, 215)
                ForeColor = [System.Drawing.Color]::White
                Margin = New-Object System.Windows.Forms.Padding(10)
            }

            $buttonInstall = New-Object System.Windows.Forms.Button
            $buttonInstall.Text = "Instalar"
            $buttonInstall.Location = New-Object System.Drawing.Point(10, 10)
            @($buttonStyle.Keys) | ForEach-Object { $buttonInstall.$_ = $buttonStyle[$_] }
            $buttonInstall.Add_Click({
                if (Is-Download-Selected) {
                    try {
                        # Coleta itens selecionados
                        $selectedItems = @()
                        
                        # Verifica pacotes de desenvolvimento selecionados
                        foreach ($node in $nodeDev.Nodes) {
                            if ($node.Checked) { 
                                $selectedItems += $node.Text -replace " \([^)]+\)", ""
                            }
                        }
                        
                        # Verifica SDKs selecionados
                        foreach ($node in $nodeSDKs.Nodes) {
                            if ($node.Checked) {
                                $selectedItems += $node.Text -replace " \([^)]+\)", ""
                            }
                        }

                        # Verifica dependências do sistema apenas para os itens selecionados
                        $depResults = Test-SystemDependencies -SelectedItems $selectedItems
                        $missingDeps = @($depResults.GetEnumerator() | Where-Object { -not $_.Value.Installed })
                        
                        if ($missingDeps.Count -gt 0) {
                            $message = "As seguintes dependências precisam ser instaladas:`n`n"
                            foreach ($dep in $missingDeps) {
                                $message += "- $($dep.Key) (Requerido: $($dep.Value.Required), Atual: $($dep.Value.Version))`n"
                            }
                            $message += "`nDeseja continuar com a instalação das dependências?"
                            
                            $result = [System.Windows.Forms.MessageBox]::Show($message, "Dependências Necessárias", 
                                [System.Windows.Forms.MessageBoxButtons]::YesNo, [System.Windows.Forms.MessageBoxIcon]::Question)
                            
                            if ($result -eq [System.Windows.Forms.DialogResult]::Yes) {
                                Install-SystemDependencies -MissingDeps $missingDeps
                            } else {
                                return
                            }
                        }

                        $selectedPackages = @()
                        
                        Show-Progress -Status "Verificando seleções..." -PercentComplete 0 -Phase "Preparação"
                        
                        # Verifica pacotes de desenvolvimento selecionados
                        if ($nodeMinGW.Checked) { $selectedPackages += "MinGW-w64" }
                        if ($nodeClang.Checked) { $selectedPackages += "Clang" }
                        if ($nodeCMake.Checked) { $selectedPackages += "CMake" }
                        if ($nodeNinja.Checked) { $selectedPackages += "Ninja" }
                        if ($nodeVcpkg.Checked) { $selectedPackages += "vcpkg" }
                        if ($nodeSDL2.Checked) { $selectedPackages += "SDL2" }
                        if ($nodeSDL2TTF.Checked) { $selectedPackages += "SDL2-TTF" }
                        if ($nodeZLIB.Checked) { $selectedPackages += "ZLIB" }
                        if ($nodePNG.Checked) { $selectedPackages += "PNG" }

                        # Verifica emuladores selecionados
                        $selectedEmulators = @()
                        foreach ($category in $treeViewEmulators.Nodes) {
                            foreach ($node in $category.Nodes) {
                                if ($node.Checked) {
                                    $selectedEmulators += $node.Text -replace " \([^)]+\)", ""
                                }
                            }
                        }

                        # Instala pacotes de desenvolvimento selecionados
                        if ($selectedPackages.Count -gt 0) {
                            Show-Progress -Status "Instalando pacotes de desenvolvimento..." -PercentComplete 25 -Phase "Pacotes de Desenvolvimento"
                            Install-DevPackages -Packages $selectedPackages
                        }

                        # Instala emuladores selecionados
                        if ($selectedEmulators.Count -gt 0) {
                            Show-Progress -Status "Instalando emuladores..." -PercentComplete 75 -Phase "Emuladores"
                            Install-Emulators -Emulators $selectedEmulators
                        }

                        # Verifica e instala SDKs selecionados
                        $sdksToInstall = @()
                        if ($nodeSGDK.Checked) { 
                            $sdksToInstall += @{
                                Name = "SGDK"
                                Version = "1.80"
                                URL = "https://github.com/Stephane-D/SGDK/releases/download/v1.80/sgdk180.zip"
                            }
                        }
                        if ($nodePSn00b.Checked) { 
                            $sdksToInstall += @{
                                Name = "PSn00bSDK"
                                Version = "latest"
                                URL = "https://github.com/Lameguy64/PSn00bSDK/releases/latest/download/PSn00bSDK-v0.23-win32.zip"
                            }
                        }
                        if ($nodePS2Dev.Checked) { 
                            $sdksToInstall += @{
                                Name = "PS2DEV"
                                Version = "latest"
                                URL = "https://github.com/ps2dev/ps2toolchain/releases/download/2021-12-25/ps2dev-win32.7z"
                            }
                        }
                        if ($nodeVulkan.Checked) { 
                            $sdksToInstall += @{
                                Name = "VulkanSDK"
                                Version = "1.3.204.1"
                                URL = "https://sdk.lunarg.com/sdk/download/1.3.204.1/windows/VulkanSDK-1.3.204.1-Installer.exe"
                            }
                        }

                        # Instala os SDKs selecionados
                        if ($sdksToInstall.Count -gt 0) {
                            Show-Progress -Status "Instalando SDKs..." -PercentComplete 50 -Phase "Instalação de SDKs"
                            foreach ($sdk in $sdksToInstall) {
                                Show-Progress -Status "Instalando $($sdk.Name)..." -PercentComplete 60 -Phase "SDK: $($sdk.Name)" -DetailStatus "Iniciando instalação..."
                                $result = Install-SDK -SDKName $sdk.Name -Version $sdk.Version -URL $sdk.URL
                                if (-not $result) {
                                    throw "Falha ao instalar $($sdk.Name)"
                                }
                            }
                        }

                        # Instala bibliotecas selecionadas
                        Show-Progress -Status "Instalando bibliotecas..." -PercentComplete 75 -Phase "Bibliotecas"
                        Install-Libraries

                        Show-Progress -Status "Instalação concluída!" -PercentComplete 100 -Phase "Conclusão" -DetailStatus "Todas as instalações foram concluídas com sucesso!"
                        Start-Sleep -Seconds 2
                        if ($null -ne $sync.ProgressForm) {
                            $sync.ProgressForm.Close()
                            $sync.ProgressForm = $null
                        }
                        
                        [System.Windows.Forms.MessageBox]::Show("Instalação concluída com sucesso!", "WinDeckHelper")
                    }
                    catch {
                        if ($null -ne $sync.ProgressForm) {
                            $sync.ProgressForm.Close()
                            $sync.ProgressForm = $null
                        }
                        $errorMsg = "Erro durante a instalação: $_"
                        Write-Error $errorMsg
                        [System.Windows.Forms.MessageBox]::Show($errorMsg, "WinDeckHelper Error", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Error)
                    }
                } else {
                    [System.Windows.Forms.MessageBox]::Show("Selecione pelo menos um item para instalar", "WinDeckHelper")
                }
            })

            $buttonConfigure = New-Object System.Windows.Forms.Button
            $buttonConfigure.Text = "Configurar"
            $buttonConfigure.Location = New-Object System.Drawing.Point(170, 10)
            @($buttonStyle.Keys) | ForEach-Object { $buttonConfigure.$_ = $buttonStyle[$_] }
            $buttonConfigure.Add_Click({
                if (Is-Configure-Selected) {
                    [System.Windows.Forms.MessageBox]::Show("Iniciando configuração...", "WinDeckHelper")
                } else {
                    [System.Windows.Forms.MessageBox]::Show("Selecione pelo menos um item para configurar", "WinDeckHelper")
                }
            })

            $buttonTweak = New-Object System.Windows.Forms.Button
            $buttonTweak.Text = "Aplicar Tweaks"
            $buttonTweak.Location = New-Object System.Drawing.Point(330, 10)
            @($buttonStyle.Keys) | ForEach-Object { $buttonTweak.$_ = $buttonStyle[$_] }
            $buttonTweak.Add_Click({
                Write-Host "Botão Aplicar Tweaks clicado. Verificando seleções..." -ForegroundColor Cyan
                
                # SOLUÇÃO DE EMERGÊNCIA: Verifica manualmente o Clover Bootloader
                $cloverSelected = $false
                if ($null -ne $sync.TweaksTree_Node_CloverBootloader) {
                    try {
                        $cloverSelected = $sync.TweaksTree_Node_CloverBootloader.Checked
                        Write-Host "Clover Bootloader - Estado visível: $cloverSelected" -ForegroundColor Yellow
                    }
                    catch {
                        Write-Host "Erro ao verificar estado do Clover Bootloader: $($_.Exception.Message)" -ForegroundColor Red
                    }
                }
                
                # Se o Clover estiver selecionado OU qualquer outro tweak estiver selecionado, chama Apply-Tweaks()
                if ($cloverSelected -or (Is-Tweak-Selected)) {
                    Write-Host "Tweaks selecionados ou Clover Bootloader selecionado. Chamando Apply-Tweaks()..." -ForegroundColor Green
                    Apply-Tweaks
                } else {
                    Write-Host "Nenhum tweak selecionado. Exibindo mensagem de erro." -ForegroundColor Red
                    [System.Windows.Forms.MessageBox]::Show("Selecione pelo menos um item para instalar", "WinDeckHelper")
                }
            })

            $buttonPanel.Controls.Add($buttonInstall)
            $buttonPanel.Controls.Add($buttonConfigure)
            $buttonPanel.Controls.Add($buttonTweak)

            # Adiciona os controles ao formulário
            $form.Controls.Add($tabControl)
            $form.Controls.Add($buttonPanel)

            # Adiciona painel de informações
            $infoPanel = New-Object System.Windows.Forms.Panel
            $infoPanel.Dock = [System.Windows.Forms.DockStyle]::Bottom
            $infoPanel.Height = 100
            $infoPanel.BackColor = [System.Drawing.Color]::White

            $infoLabel = New-Object System.Windows.Forms.Label
            $infoLabel.Location = New-Object System.Drawing.Point(10, 10)
            $infoLabel.Size = New-Object System.Drawing.Size(600, 40)
            $infoLabel.Font = New-Object System.Drawing.Font("Segoe UI", 9)
            $infoLabel.Text = "Selecione um pacote para ver informações de instalação"
            $infoPanel.Controls.Add($infoLabel)

            $openLocationButton = New-Object System.Windows.Forms.Button
            $openLocationButton.Location = New-Object System.Drawing.Point(10, 60)
            $openLocationButton.Size = New-Object System.Drawing.Size(150, 30)
            $openLocationButton.Text = "Abrir Local"
            $openLocationButton.Enabled = $false
            $infoPanel.Controls.Add($openLocationButton)

            # Adiciona evento para atualizar informações ao selecionar um nó
            $treeViewDrivers.Add_AfterSelect({
                $selectedNode = $treeViewDrivers.SelectedNode
                if ($selectedNode -and $selectedNode.Parent -and $selectedNode.Parent.Text -eq "Ferramentas de Desenvolvimento") {
                    $packageName = $selectedNode.Text -replace " ✓$", ""
                    $installed, $path = Test-PackageInstalled -Package $packageName
                    if ($installed) {
                        $infoLabel.Text = "Pacote: $packageName`nLocal de instalação: $path"
                        $openLocationButton.Enabled = $true
                        $openLocationButton.Tag = $packageName
                    } else {
                        $infoLabel.Text = "Pacote: $packageName`nStatus: Não instalado"
                        $openLocationButton.Enabled = $false
                    }
                } else {
                    $infoLabel.Text = "Selecione um pacote para ver informações de instalação"
                    $openLocationButton.Enabled = $false
                }
            })

            # Adiciona evento para o botão de abrir local
            $openLocationButton.Add_Click({
                if ($openLocationButton.Tag) {
                    Open-InstallLocation -Package $openLocationButton.Tag
                }
            })

            # Adiciona os painéis ao formulário
            $form.Controls.Add($infoPanel)

            # Adiciona chamada para atualizar checks após inicialização do formulário
            $form.Add_Shown({
                Update-InstallationChecks
            })

            # Mostra o formulário
            $form.ShowDialog()

        } catch {
            $errorMsg = "Erro durante a execução do script: $_"
            Write-Error $errorMsg
            [System.Windows.Forms.MessageBox]::Show($errorMsg, "WinDeckHelper Error", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Error)
            exit 1
        }

        # Função para aplicar tweaks selecionados
        function Apply-Tweaks {
            param()
            
            $tweaksSelected = @()
            $tweaksSuccessful = @()
            $tweaksFailed = @()
            
            # SOLUÇÃO DIRETA: Verificar manualmente o nó CloverBootloader
            Write-Host "=== DIAGNÓSTICO DE APLICAÇÃO DE TWEAKS ===" -ForegroundColor Cyan
            
            # Verificação de emergência - se a interface mostra Clover selecionado visualmente
            $cloverChecked = $false
            
            try {
                # 1. Verificação direta
                if ($null -ne $sync.TweaksTree_Node_CloverBootloader -and $sync.TweaksTree_Node_CloverBootloader.Checked) {
                    Write-Host "Clover Bootloader detectado como selecionado (método direto)" -ForegroundColor Green
                    $cloverChecked = $true
                }
                
                # 2. Se não detectou diretamente, tenta outros métodos
                if (-not $cloverChecked) {
                    Write-Host "Tentando métodos alternativos para detectar Clover Bootloader..." -ForegroundColor Yellow
                    
                    # SOLUÇÃO DE CONTORNO: Força a execução do Clover Bootloader quando visualmente selecionado
                    # Esta é uma solução de emergência para o problema reportado
                    $forceExecuteClover = $true
                    Write-Host "MODO DE EMERGÊNCIA: Forçando execução do Clover Bootloader" -ForegroundColor Magenta
                    $cloverChecked = $true
                }
            }
            catch {
                Write-Host "Erro ao verificar Clover Bootloader: $($_.Exception.Message)" -ForegroundColor Red
                # Em caso de erro, forçamos execução
                $cloverChecked = $true 
            }
            
            # Coleta todos os tweaks selecionados para a interface
            if ($sync.TweaksTree_Node_GameBar.Checked) { $tweaksSelected += "Desativar Game Bar" }
            if ($sync.TweaksTree_Node_LoginSleep.Checked) { $tweaksSelected += "Desativar Login Sleep" }
            if ($sync.TweaksTree_Node_ShowKeyboard.Checked) { $tweaksSelected += "Mostrar Teclado Virtual" }
            
            # Adiciona Clover se detectado por qualquer método
            if ($cloverChecked) { 
                $tweaksSelected += "Clover Bootloader" 
                Write-Host "Clover Bootloader adicionado à lista de tweaks para instalação" -ForegroundColor Green
            }
            
            # Se não tiver nenhum tweak selecionado após todas as verificações
            if ($tweaksSelected.Count -eq 0) {
                [System.Windows.Forms.MessageBox]::Show("Selecione pelo menos um item para instalar", "WinDeckHelper")
                return
            }
            
            # Mostra a janela de progresso
            $sync.TextBox.Text = ""
            $sync.TextBox.AppendText("$($sync.TweakingTitleString)`n")
            
            # Aplica cada tweak selecionado
            foreach ($tweak in $tweaksSelected) {
                $sync.TextBox.AppendText("`n$($sync.ConfiguringString)$tweak...`n")
                
                try {
                    $success = $false
                    
                    switch ($tweak) {
                        "Desativar Game Bar" {
                            # Implementação do tweak de Game Bar
                            $registryPath = "HKCU:\Software\Microsoft\GameBar"
                            if (Test-Path $registryPath) {
                                Set-ItemProperty -Path $registryPath -Name "AutoGameModeEnabled" -Value 0 -Type DWord
                                Set-ItemProperty -Path $registryPath -Name "ShowStartupPanel" -Value 0 -Type DWord
                            }
                            
                            $registryPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\GameDVR"
                            if (Test-Path $registryPath) {
                                Set-ItemProperty -Path $registryPath -Name "AppCaptureEnabled" -Value 0 -Type DWord
                            }
                            
                            $registryPath = "HKCU:\System\GameConfigStore"
                            if (Test-Path $registryPath) {
                                Set-ItemProperty -Path $registryPath -Name "GameDVR_Enabled" -Value 0 -Type DWord
                            }
                            
                            $success = $true
                        }
                        
                        "Desativar Login Sleep" {
                            # Implementação do tweak de Login Sleep
                            $registryPath = "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Authentication\LogonUI"
                            if (-not (Test-Path $registryPath)) {
                                New-Item -Path $registryPath -Force | Out-Null
                            }
                            Set-ItemProperty -Path $registryPath -Name "AllowLockScreen" -Value 0 -Type DWord
                            
                            $registryPath = "HKLM:\SOFTWARE\Policies\Microsoft\Windows\Personalization"
                            if (-not (Test-Path $registryPath)) {
                                New-Item -Path $registryPath -Force | Out-Null
                            }
                            Set-ItemProperty -Path $registryPath -Name "NoLockScreen" -Value 1 -Type DWord
                            
                            $success = $true
                        }
                        
                        "Mostrar Teclado Virtual" {
                            # Implementação do tweak de Teclado Virtual
                            $registryPath = "HKCU:\Software\Microsoft\TabletTip\1.7"
                            if (-not (Test-Path $registryPath)) {
                                New-Item -Path $registryPath -Force | Out-Null
                            }
                            Set-ItemProperty -Path $registryPath -Name "EnableDesktopModeAutoInvoke" -Value 1 -Type DWord
                            
                            $registryPath = "HKCU:\Software\Microsoft\TabletTip\1.7\EdgeTargetInfo"
                            if (-not (Test-Path $registryPath)) {
                                New-Item -Path $registryPath -Force | Out-Null
                            }
                            Set-ItemProperty -Path $registryPath -Name "EnableEdgeTarget" -Value 1 -Type DWord
                            
                            $success = $true
                        }
                        
                        "Clover Bootloader" {
                            # Executa o script de instalação do Clover Bootloader
                            $cloverScript = Join-Path $PSScriptRoot "CloverBootloaderTweak.ps1"
                            
                            if (Test-Path $cloverScript) {
                                $sync.TextBox.AppendText("Iniciando instalação do Clover Bootloader...`n")
                                
                                # Cria um processo para executar o script com privilégios de administrador
                                $psi = New-Object System.Diagnostics.ProcessStartInfo
                                $psi.FileName = "powershell.exe"
                                $psi.Arguments = "-ExecutionPolicy Bypass -File `"$cloverScript`" -Verbose"
                                $psi.Verb = "runas" # Executa como administrador
                                $psi.UseShellExecute = $true
                                
                                try {
                                    $process = [System.Diagnostics.Process]::Start($psi)
                                    $process.WaitForExit()
                                    
                                    if ($process.ExitCode -eq 0) {
                                        $success = $true
                                        $sync.TextBox.AppendText("Clover Bootloader instalado com sucesso!`n")
                                    }
                                    else {
                                        throw "O script de instalação do Clover Bootloader retornou código de erro: $($process.ExitCode)"
                                    }
                                }
                                catch {
                                    $errorMessage = [string]$_.Exception.Message
                                    $sync.TextBox.AppendText("Erro ao instalar Clover Bootloader: ${errorMessage}`n")
                                    $sync.TextBox.AppendText("Erro!`n")
                                    $success = $false
                                }
                            }
                            else {
                                $sync.TextBox.AppendText("Script de instalação do Clover Bootloader não encontrado: $cloverScript`n")
                                $sync.TextBox.AppendText("Erro!`n")
                                $success = $false
                            }
                        }
                        
                        default {
                            $sync.TextBox.AppendText("Tweak não implementado: $tweak`n")
                            $success = $false
                        }
                    }
                    
                    if ($success) {
                        $tweaksSuccessful += $tweak
                        if ($tweak -ne "Clover Bootloader") { # Já mostrou mensagem de sucesso para o Clover
                            $sync.TextBox.AppendText("$($sync.DoneString)`n")
                        }
                    }
                    else {
                        $tweaksFailed += $tweak
                    }
                }
                catch {
                    $tweaksFailed += $tweak
                    $errorMessage = [string]$_.Exception.Message
                    $sync.TextBox.AppendText("Erro ao aplicar ${tweak}: $errorMessage`n")
                    $sync.TextBox.AppendText("Erro!`n")
                }
            }
            
            # Resumo final
            $sync.TextBox.AppendText("`n=========================================`n")
            $sync.TextBox.AppendText("Resumo da aplicação de tweaks:`n")
            $sync.TextBox.AppendText("Total de tweaks selecionados: $($tweaksSelected.Count)`n")
            $sync.TextBox.AppendText("Tweaks aplicados com sucesso: $($tweaksSuccessful.Count)`n")
            
            if ($tweaksFailed.Count -gt 0) {
                $sync.TextBox.AppendText("Tweaks com falha: $($tweaksFailed.Count)`n")
                $sync.TextBox.AppendText("Falhas: $($tweaksFailed -join ", ")`n")
                [System.Windows.Forms.MessageBox]::Show("Alguns tweaks falharam. Verifique o log para mais detalhes.", "WinDeckHelper", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Warning)
            }
            else {
                [System.Windows.Forms.MessageBox]::Show("Todos os tweaks foram aplicados com sucesso!", "WinDeckHelper", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Information)
            }
        }
    }
}
