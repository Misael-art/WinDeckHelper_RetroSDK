Write-Host "=== Instalação do GloverWindows ==="
Write-Host "Este assistente ajudará a instalar o GloverWindows em seu sistema."
Write-Host "Por favor, siga as instruções cuidadosamente para garantir uma instalação bem-sucedida."

# Verificar o tipo de firmware do sistema
$firmwareType = (Get-ComputerInfo).BiosFirmwareType
Write-Host "Firmware detectado: $firmwareType"

# Verificar partições existentes
Write-Host "Verificando partições existentes..."
Get-Disk | Get-Partition | Format-Table -Property DriveLetter, Size, Type

# Verificar espaço disponível em disco
Write-Host "Verificando espaço disponível em disco..."
$disks = Get-Disk | Where-Object {$_.Size -gt 0}
foreach ($disk in $disks) {
    $freeSpace = ($disk | Get-Partition | Get-Volume | Measure-Object -Property SizeRemaining -Sum).Sum / 1GB
    Write-Host "Disco $($disk.Number): $($freeSpace.ToString('0.00')) GB disponíveis"
}

$createPartition = Read-Host "Deseja criar uma nova partição para o GloverWindows? (S/N)"
if ($createPartition -eq "S" -or $createPartition -eq "s") {
    Write-Host "Abrindo o Gerenciamento de Disco para criar uma nova partição..."
    Write-Host "Por favor, crie uma partição de pelo menos 20 GB para o GloverWindows."
    Start-Process diskmgmt.msc
    Read-Host "Pressione Enter quando terminar de criar a partição"
} else {
    Write-Host "Pulando a criação de partição. Certifique-se de ter pelo menos 20 GB livres na partição desejada."
}

# Instruções para baixar a ISO do GloverWindows
Write-Host "=== Baixando o GloverWindows ==="
Write-Host "O GloverWindows deve ser baixado do site oficial:"
Write-Host "https://gloverwindows.com/download"
Write-Host "Por favor, baixe a versão mais recente do GloverWindows e salve-a em sua máquina."

$downloadComplete = Read-Host "Completou o download da ISO do GloverWindows? (S/N)"
if ($downloadComplete -eq "S" -or $downloadComplete -eq "s") {
    Write-Host "Ótimo! Agora você precisa criar uma mídia de instalação do GloverWindows."
    Write-Host "Você pode usar o Rufus (https://rufus.ie) para criar um USB bootável com a ISO do GloverWindows."
}

# Verificar se o Grub2Win está instalado
$grub2winPaths = @(
    "${env:ProgramFiles}\Grub2Win\grub2win.exe",
    "${env:USERPROFILE}\AppData\Local\Grub2Win\grub2win.exe",
    "C:\Grub2Win\grub2win.exe"
)

$grub2winInstalled = $false
$grub2winPath = ""

foreach ($path in $grub2winPaths) {
    if (Test-Path $path) {
        $grub2winInstalled = $true
        $grub2winPath = $path
        break
    }
}

if ($grub2winInstalled) {
    Write-Host "Grub2Win encontrado em: $grub2winPath"
    $openGrub2Win = Read-Host "Deseja abrir o Grub2Win para configurar o dual boot? (S/N)"
    if ($openGrub2Win -eq "S" -or $openGrub2Win -eq "s") {
        Start-Process $grub2winPath
    }
} else {
    Write-Host "Grub2Win não encontrado. Por favor, instale o Grub2Win antes de continuar."
    Write-Host "Você pode instalá-lo com o comando: python environment_dev.py --install Grub2Win"
}

Write-Host "=== Concluindo a instalação do GloverWindows ==="
Write-Host "Após a instalação do GloverWindows, você precisará configurar o dual boot com o Grub2Win."
Write-Host "Abra o Grub2Win e adicione uma nova entrada para o GloverWindows, apontando para a partição onde ele foi instalado."
Write-Host "Isso permitirá que você escolha entre seu sistema operacional principal e o GloverWindows ao iniciar o computador."

Read-Host "Pressione Enter para finalizar" 