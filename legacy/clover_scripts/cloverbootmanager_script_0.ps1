# Script de instalação do Clover Boot Manager
# Este script foi extraído do componente CloverBootManager

# Criar diretórios de trabalho
$tempDir = "$env:TEMP\CloverBootManager"
New-Item -Path $tempDir -ItemType Directory -Force | Out-Null
New-Item -Path "$tempDir\Backup" -ItemType Directory -Force | Out-Null
New-Item -Path "$tempDir\Extracted" -ItemType Directory -Force | Out-Null

# Obter informações do sistema
$firmwareType = (Get-ComputerInfo).BiosFirmwareType
$isUefi = $firmwareType -eq "Uefi"
$isWindows = $true
$isSteamOS = Test-Path "C:\SteamOS" -ErrorAction SilentlyContinue

# Salvar informações para uso posterior
@{
  FirmwareType = $firmwareType
  IsUefi = $isUefi
  IsWindows = $isWindows
  IsSteamOS = $isSteamOS
} | ConvertTo-Json | Out-File -FilePath "$tempDir\system_info.json" -Encoding utf8 -Force

# Baixar Clover
Write-Host "Baixando Clover Bootloader..."
Invoke-WebRequest -Uri "https://sourceforge.net/projects/cloverefiboot/files/Bootable_ISO/CloverISO-5151.tar.lzma/download" -OutFile "$tempDir\CloverISO.tar.lzma" -UseBasicParsing

# Extrair arquivos
Write-Host "Extraindo arquivos..."
& 7z x "$tempDir\CloverISO.tar.lzma" -o"$tempDir" -y
& 7z x "$tempDir\CloverISO.tar" -o"$tempDir\Extracted" -y

# Preparar configuração
$baseConfigPath = "$tempDir\Extracted\EFI\CLOVER\config.plist"

# Instalar Clover
if ($isUefi) {
  Write-Host "Instalando Clover para sistema UEFI..."
  
  # Encontrar partição EFI
  $efiVolume = $null
  $disks = Get-Disk | Where-Object {$_.PartitionStyle -eq "GPT"}
  foreach ($disk in $disks) {
    $efiPartitions = $disk | Get-Partition | Where-Object {$_.GptType -eq "{c12a7328-f81f-11d2-ba4b-00a0c93ec93b}"}
    if ($efiPartitions) {
      try {
        # Obter letra temporária para a partição EFI se necessário
        $efiVolume = $efiPartitions[0] | Get-Volume
        if (-not $efiVolume.DriveLetter) {
          # Atribuir letra temporária
          $driveLetter = 69 # Letra 'E'
          while ([char]$driveLetter -le 90) {
            $letter = [char]$driveLetter
            if (-not (Get-Volume -DriveLetter $letter -ErrorAction SilentlyContinue)) {
              $efiPartitions[0] | Add-PartitionAccessPath -AccessPath "${letter}:"
              $efiVolume = Get-Volume -DriveLetter $letter
              break
            }
            $driveLetter++
          }
        }

        if ($efiVolume.DriveLetter) {
          $efiPath = "${efiVolume.DriveLetter}:"
          
          # Fazer backup de bootloaders existentes
          Write-Host "Fazendo backup de bootloaders existentes..."
          if (Test-Path "$efiPath\EFI\BOOT") {
            Copy-Item -Path "$efiPath\EFI\BOOT" -Destination "$tempDir\Backup\BOOT" -Recurse -Force
          }
          if (Test-Path "$efiPath\EFI\Microsoft") {
            Copy-Item -Path "$efiPath\EFI\Microsoft" -Destination "$tempDir\Backup\Microsoft" -Recurse -Force
          }
          if (Test-Path "$efiPath\EFI\CLOVER") {
            Copy-Item -Path "$efiPath\EFI\CLOVER" -Destination "$tempDir\Backup\CLOVER" -Recurse -Force
          }
          
          # Copiar arquivos do Clover
          Write-Host "Copiando arquivos Clover para partição EFI..."
          if (-not (Test-Path "$efiPath\EFI")) {
            New-Item -Path "$efiPath\EFI" -ItemType Directory -Force | Out-Null
          }
          
          # Copiar CLOVER
          Copy-Item -Path "$tempDir\Extracted\EFI\CLOVER" -Destination "$efiPath\EFI\" -Recurse -Force
          
          # Preservar bootloader Windows se existir
          if (Test-Path "$tempDir\Backup\Microsoft") {
            if (-not (Test-Path "$efiPath\EFI\Microsoft")) {
              Copy-Item -Path "$tempDir\Backup\Microsoft" -Destination "$efiPath\EFI\" -Recurse -Force
            }
          }
          
          # Preservar bootloader original
          if (Test-Path "$tempDir\Backup\BOOT") {
            # Fazer backup do bootloader Clover primeiro
            if (Test-Path "$efiPath\EFI\BOOT") {
              Copy-Item -Path "$efiPath\EFI\BOOT" -Destination "$tempDir\Extracted\EFI\CLOVER_BOOT" -Recurse -Force
            }
            
            # Restaurar bootloader original
            Copy-Item -Path "$tempDir\Backup\BOOT" -Destination "$efiPath\EFI\" -Recurse -Force
            
            # Adicionar entrada para Clover no bootloader existente
            # Nota: Esta parte requer mais implementação específica dependendo do bootloader existente
          }
          
          # Configuração básica
          Write-Host "Configurando Clover..."
          $configFile = "$efiPath\EFI\CLOVER\config.plist"
          
          # Detecção automática de sistemas operacionais
          # Nota: Clover faz isso automaticamente na maioria dos casos
          
          Write-Host "Clover instalado na partição EFI!"
        } else {
          Write-Host "Não foi possível acessar a partição EFI." -ForegroundColor Red
        }
      } catch {
        Write-Host "Erro ao configurar partição EFI: $_" -ForegroundColor Red
      }
      break
    }
  }
} else {
  Write-Host "Instalando Clover para sistema Legacy BIOS..."
  
  # Implementação para sistemas Legacy BIOS
  # Usar arquivo EFI\BOOT\BOOTX64.efi em uma partição bootável
  
  # Para sistemas Legacy, precisamos criar uma partição bootável ou usar uma existente
  # e instalar o Clover como bootloader primário
  
  # Nota: Esta parte é mais complexa e requer acesso direto ao MBR
  Write-Host "Instalação em sistemas Legacy BIOS requer configuração adicional." -ForegroundColor Yellow
  Write-Host "Por favor, consulte a documentação oficial do Clover para sistemas Legacy." -ForegroundColor Yellow
}

# Verificar instalação
if (Test-Path "C:\EFI\CLOVER\CLOVERX64.efi" -ErrorAction SilentlyContinue) {
  Write-Host "Clover Boot Manager instalado com sucesso!" -ForegroundColor Green
  return 0
} else {
  Write-Host "Clover Boot Manager não encontrado após instalação. Verifique o log." -ForegroundColor Red
  return 1
} 