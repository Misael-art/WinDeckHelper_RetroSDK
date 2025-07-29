Write-Host "Preparando sistema para dual boot Windows/Linux..."

# Verificar se o sistema está em modo UEFI ou Legacy BIOS
$firmware = Get-ComputerInfo | Select-Object BiosFirmwareType
Write-Host "Tipo de firmware: $($firmware.BiosFirmwareType)"

# Verificar se Secure Boot está ativado (apenas para UEFI)
if ($firmware.BiosFirmwareType -eq 'Uefi') {
    Write-Host "Sistema em modo UEFI - Verificando Secure Boot"
    Write-Host "AVISO: Para dual boot com algumas distribuições Linux, pode ser necessário desativar o Secure Boot nas configurações da UEFI."
} else {
    Write-Host "Sistema em modo Legacy BIOS"
}

# Listar discos e partições existentes
Write-Host "`nDiscos disponíveis:"
Get-Disk | Format-Table -AutoSize

Write-Host "`nPartições existentes:"
Get-Partition | Format-Table -AutoSize

# Verificar espaço livre
$disks = Get-Disk | Where-Object { $_.Size -gt 0 }
foreach ($disk in $disks) {
    $usedSpace = (Get-Partition -DiskNumber $disk.Number | Measure-Object -Property Size -Sum).Sum
    $freeSpace = $disk.Size - $usedSpace
    $freeSpaceGB = [math]::Round($freeSpace / 1GB, 2)

    Write-Host "Disco $($disk.Number): $freeSpaceGB GB livres de $([math]::Round($disk.Size / 1GB, 2)) GB total"
}

Write-Host "`nRecomendações para dual boot:"
Write-Host "1. Tenha pelo menos 50GB livres para a instalação do Linux"
Write-Host "2. Faça backup de todos os dados importantes antes de prosseguir"
Write-Host "3. Desfragmente o disco Windows antes de redimensionar partições"
Write-Host "4. Utilize o Gerenciador de Disco do Windows para reduzir uma partição existente"
Write-Host "   OU use ferramentas do instalador Linux como GParted durante a instalação"

Write-Host "`nDeseja verificar a fragmentação do disco C:? (S/N)"
$response = Read-Host
if ($response -eq 'S' -or $response -eq 's') {
    Write-Host "Analisando fragmentação do disco C:"
    $defrag = Optimize-Volume -DriveLetter C -Analyze -Verbose 4>&1
    $defrag | ForEach-Object { Write-Host $_ }

    Write-Host "`nDeseja desfragmentar o disco C:? (S/N) [Pode demorar bastante]"
    $defragResponse = Read-Host
    if ($defragResponse -eq 'S' -or $defragResponse -eq 's') {
        Write-Host "Iniciando desfragmentação..."
        Optimize-Volume -DriveLetter C -Defrag -Verbose
        Write-Host "Desfragmentação concluída."
    }
}

Write-Host "`nInstrução para instalação dual boot:"
Write-Host "1. Baixe a imagem ISO da distribuição Linux desejada"
Write-Host "2. Crie uma mídia bootável (pendrive ou DVD)"
Write-Host "3. Antes de iniciar a instalação, verifique se Fast Startup está desativado no Windows:"
Write-Host "   - Painel de Controle -> Opções de Energia -> Escolher a função dos botões de energia"
Write-Host "   - Desmarque 'Ligar inicialização rápida'"
Write-Host "4. Reinicie e entre na BIOS/UEFI (geralmente pressionando F2, F12, DEL durante o boot)"
Write-Host "5. Configure a ordem de boot para iniciar pelo dispositivo instalador"
Write-Host "6. Durante a instalação do Linux, escolha a opção 'Instalar ao lado do Windows'"
Write-Host "   OU use particionamento manual, tendo cuidado para NÃO formatar partições Windows"

Write-Host "`nAPÓS INSTALAR O LINUX:"
Write-Host "1. Se o GRUB for instalado corretamente, você terá um menu para escolher entre Windows e Linux"
Write-Host "2. Se apenas o Windows iniciar, use o Grub2Win para configurar o boot"
Write-Host "3. Se apenas o Linux iniciar, use ferramentas como Boot-Repair no Linux"

Write-Host "`nPreparação concluída! Seu sistema está agora pronto para a instalação dual boot."
Out-File -FilePath "${env:USERPROFILE}\AppData\Local\DualBootPartitionManager\prepare_dualboot.ps1" -Encoding utf8 -Force -InputObject @'
Write-Host "Preparando sistema para dual boot Windows/Linux..."

# Verificar se o sistema está em modo UEFI ou Legacy BIOS
$firmware = Get-ComputerInfo | Select-Object BiosFirmwareType
Write-Host "Tipo de firmware: $($firmware.BiosFirmwareType)"

# Verificar se Secure Boot está ativado (apenas para UEFI)
if ($firmware.BiosFirmwareType -eq 'Uefi') {
    Write-Host "Sistema em modo UEFI - Verificando Secure Boot"
    Write-Host "AVISO: Para dual boot com algumas distribuições Linux, pode ser necessário desativar o Secure Boot nas configurações da UEFI."
} else {
    Write-Host "Sistema em modo Legacy BIOS"
}

# Listar discos e partições existentes
Write-Host "`nDiscos disponíveis:"
Get-Disk | Format-Table -AutoSize

Write-Host "`nPartições existentes:"
Get-Partition | Format-Table -AutoSize

# Verificar espaço livre
$disks = Get-Disk | Where-Object { $_.Size -gt 0 }
foreach ($disk in $disks) {
    $usedSpace = (Get-Partition -DiskNumber $disk.Number | Measure-Object -Property Size -Sum).Sum
    $freeSpace = $disk.Size - $usedSpace
    $freeSpaceGB = [math]::Round($freeSpace / 1GB, 2)

    Write-Host "Disco $($disk.Number): $freeSpaceGB GB livres de $([math]::Round($disk.Size / 1GB, 2)) GB total"
}

Write-Host "`nRecomendações para dual boot:"
Write-Host "1. Tenha pelo menos 50GB livres para a instalação do Linux"
Write-Host "2. Faça backup de todos os dados importantes antes de prosseguir"
Write-Host "3. Desfragmente o disco Windows antes de redimensionar partições"
Write-Host "4. Utilize o Gerenciador de Disco do Windows para reduzir uma partição existente"
Write-Host "   OU use ferramentas do instalador Linux como GParted durante a instalação"

Write-Host "`nDeseja verificar a fragmentação do disco C:? (S/N)"
$response = Read-Host
if ($response -eq 'S' -or $response -eq 's') {
    Write-Host "Analisando fragmentação do disco C:"
    $defrag = Optimize-Volume -DriveLetter C -Analyze -Verbose 4>&1
    $defrag | ForEach-Object { Write-Host $_ }

    Write-Host "`nDeseja desfragmentar o disco C:? (S/N) [Pode demorar bastante]"
    $defragResponse = Read-Host
    if ($defragResponse -eq 'S' -or $defragResponse -eq 's') {
        Write-Host "Iniciando desfragmentação..."
        Optimize-Volume -DriveLetter C -Defrag -Verbose
        Write-Host "Desfragmentação concluída."
    }
}

Write-Host "`nInstrução para instalação dual boot:"
Write-Host "1. Baixe a imagem ISO da distribuição Linux desejada"
Write-Host "2. Crie uma mídia bootável (pendrive ou DVD)"
Write-Host "3. Antes de iniciar a instalação, verifique se Fast Startup está desativado no Windows:"
Write-Host "   - Painel de Controle -> Opções de Energia -> Escolher a função dos botões de energia"
Write-Host "   - Desmarque 'Ligar inicialização rápida'"
Write-Host "4. Reinicie e entre na BIOS/UEFI (geralmente pressionando F2, F12, DEL durante o boot)"
Write-Host "5. Configure a ordem de boot para iniciar pelo dispositivo instalador"
Write-Host "6. Durante a instalação do Linux, escolha a opção 'Instalar ao lado do Windows'"
Write-Host "   OU use particionamento manual, tendo cuidado para NÃO formatar partições Windows"

Write-Host "`nAPÓS INSTALAR O LINUX:"
Write-Host "1. Se o GRUB for instalado corretamente, você terá um menu para escolher entre Windows e Linux"
Write-Host "2. Se apenas o Windows iniciar, use o Grub2Win para configurar o boot"
Write-Host "3. Se apenas o Linux iniciar, use ferramentas como Boot-Repair no Linux"

Write-Host "`nPreparação concluída! Seu sistema está agora pronto para a instalação dual boot."
'@ 