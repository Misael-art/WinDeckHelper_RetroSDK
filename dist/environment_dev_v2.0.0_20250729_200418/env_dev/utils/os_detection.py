#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo para detectar sistemas operacionais instalados.

Este módulo contém funções para detectar sistemas operacionais instalados e gerar
configurações para o Clover Boot Manager.
"""

import os
import logging
import subprocess
import platform
import tempfile
import plistlib
from typing import Dict, Any, Optional, List, Tuple

# Importar módulo de backup da EFI
from env_dev.utils.efi_backup import find_efi_partition, unmount_efi_partition

# Configurar logger
logger = logging.getLogger(__name__)

def detect_operating_systems() -> List[Dict[str, Any]]:
    """
    Detecta sistemas operacionais instalados no sistema.
    
    Returns:
        List[Dict[str, Any]]: Lista de dicionários com informações sobre os sistemas operacionais detectados.
    """
    operating_systems = []
    
    # Verificar se estamos no Windows
    if platform.system() != "Windows":
        logger.error("Este módulo só é compatível com Windows.")
        return operating_systems
    
    logger.info("Detectando sistemas operacionais instalados...")
    
    # Detectar Windows
    try:
        windows_installed = os.path.exists("C:\\Windows")
        if windows_installed:
            # Obter versão do Windows
            ps_command = """
            Get-WmiObject -Class Win32_OperatingSystem | Select-Object -ExpandProperty Caption
            """
            
            result = subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0 and result.stdout.strip():
                windows_version = result.stdout.strip()
            else:
                windows_version = "Windows"
            
            operating_systems.append({
                "name": windows_version,
                "type": "Windows",
                "path": "C:\\Windows",
                "bootloader": "EFI\\Microsoft\\Boot\\bootmgfw.efi",
                "drive_label": "Windows",
                "detected": True,
                "active": True
            })
            
            logger.info(f"Detectado: {windows_version}")
    except Exception as e:
        logger.error(f"Erro ao detectar Windows: {e}")
    
    # Detectar outros sistemas operacionais através de partições
    try:
        # Obter lista de discos e partições
        ps_command = """
        $disks = Get-Disk | Where-Object {$_.PartitionStyle -eq "GPT"}
        foreach ($disk in $disks) {
            $partitions = $disk | Get-Partition | Where-Object {$_.Size -gt 10GB}
            foreach ($partition in $partitions) {
                try {
                    $volume = $partition | Get-Volume -ErrorAction SilentlyContinue
                    if ($volume -and $volume.FileSystemType -ne "NTFS" -and $volume.FileSystemType -ne $null) {
                        $driveLetter = $volume.DriveLetter
                        $driveLabel = $volume.FileSystemLabel
                        $fileSystem = $volume.FileSystemType
                        Write-Output "$driveLetter,$driveLabel,$fileSystem"
                    }
                } catch {}
            }
        }
        """
        
        result = subprocess.run(
            ["powershell", "-Command", ps_command],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0 and result.stdout.strip():
            for line in result.stdout.strip().split("\n"):
                if not line.strip():
                    continue
                
                parts = line.strip().split(",")
                if len(parts) >= 3:
                    drive_letter, drive_label, file_system = parts
                    
                    # Identificar sistema operacional com base no sistema de arquivos
                    if file_system in ["HFS+", "APFS"]:
                        # Provável macOS
                        operating_systems.append({
                            "name": "macOS",
                            "type": "macOS",
                            "path": f"{drive_letter}:\\",
                            "bootloader": "EFI\\Apple\\Boot\\bootmgfw.efi",
                            "drive_label": drive_label,
                            "detected": True,
                            "active": True
                        })
                        
                        logger.info(f"Detectado: macOS em {drive_label} ({drive_letter}:)")
                    elif file_system in ["ext4", "ext3", "ext2", "btrfs", "xfs"]:
                        # Provável Linux
                        linux_type = "Linux"
                        
                        # Tentar identificar a distribuição
                        if drive_letter:
                            os_release_path = f"{drive_letter}:\\etc\\os-release"
                            steamos_release_path = f"{drive_letter}:\\etc\\steamos-release"
                            debian_version_path = f"{drive_letter}:\\etc\\debian_version"
                            fedora_release_path = f"{drive_letter}:\\etc\\fedora-release"
                            redhat_release_path = f"{drive_letter}:\\etc\\redhat-release"
                            arch_release_path = f"{drive_letter}:\\etc\\arch-release"
                            
                            if os.path.exists(os_release_path):
                                try:
                                    with open(os_release_path, "r") as f:
                                        os_release_content = f.read()
                                    
                                    # Extrair nome da distribuição
                                    import re
                                    name_match = re.search(r'NAME="(.+)"', os_release_content)
                                    if name_match:
                                        linux_type = name_match.group(1)
                                except:
                                    pass
                            elif os.path.exists(steamos_release_path):
                                linux_type = "SteamOS"
                            elif os.path.exists(debian_version_path):
                                linux_type = "Debian"
                            elif os.path.exists(fedora_release_path):
                                linux_type = "Fedora"
                            elif os.path.exists(redhat_release_path):
                                linux_type = "Red Hat"
                            elif os.path.exists(arch_release_path):
                                linux_type = "Arch Linux"
                        
                        operating_systems.append({
                            "name": linux_type,
                            "type": "Linux",
                            "path": f"{drive_letter}:\\",
                            "bootloader": "EFI\\ubuntu\\grubx64.efi",  # Padrão, pode variar
                            "drive_label": drive_label,
                            "detected": True,
                            "active": True
                        })
                        
                        logger.info(f"Detectado: {linux_type} em {drive_label} ({drive_letter}:)")
    except Exception as e:
        logger.error(f"Erro ao detectar outros sistemas operacionais: {e}")
    
    # Detectar sistemas operacionais através da partição EFI
    efi_drive_letter, temp_drive_created = find_efi_partition()
    
    if efi_drive_letter:
        try:
            efi_path = f"{efi_drive_letter}:\\"
            
            # Verificar bootloaders na partição EFI
            if os.path.exists(os.path.join(efi_path, "EFI", "Microsoft", "Boot", "bootmgfw.efi")):
                # Windows bootloader encontrado
                if not any(os["type"] == "Windows" for os in operating_systems):
                    operating_systems.append({
                        "name": "Windows",
                        "type": "Windows",
                        "path": "Desconhecido",
                        "bootloader": "EFI\\Microsoft\\Boot\\bootmgfw.efi",
                        "drive_label": "Desconhecido",
                        "detected": True,
                        "active": True
                    })
                    
                    logger.info("Detectado: Windows (apenas bootloader)")
            
            if os.path.exists(os.path.join(efi_path, "EFI", "ubuntu")):
                # Ubuntu bootloader encontrado
                if not any(os["type"] == "Linux" and os["name"] == "Ubuntu" for os in operating_systems):
                    operating_systems.append({
                        "name": "Ubuntu",
                        "type": "Linux",
                        "path": "Desconhecido",
                        "bootloader": "EFI\\ubuntu\\grubx64.efi",
                        "drive_label": "Desconhecido",
                        "detected": True,
                        "active": True
                    })
                    
                    logger.info("Detectado: Ubuntu (apenas bootloader)")
            
            if os.path.exists(os.path.join(efi_path, "EFI", "debian")):
                # Debian bootloader encontrado
                if not any(os["type"] == "Linux" and os["name"] == "Debian" for os in operating_systems):
                    operating_systems.append({
                        "name": "Debian",
                        "type": "Linux",
                        "path": "Desconhecido",
                        "bootloader": "EFI\\debian\\grubx64.efi",
                        "drive_label": "Desconhecido",
                        "detected": True,
                        "active": True
                    })
                    
                    logger.info("Detectado: Debian (apenas bootloader)")
            
            if os.path.exists(os.path.join(efi_path, "EFI", "fedora")):
                # Fedora bootloader encontrado
                if not any(os["type"] == "Linux" and os["name"] == "Fedora" for os in operating_systems):
                    operating_systems.append({
                        "name": "Fedora",
                        "type": "Linux",
                        "path": "Desconhecido",
                        "bootloader": "EFI\\fedora\\grubx64.efi",
                        "drive_label": "Desconhecido",
                        "detected": True,
                        "active": True
                    })
                    
                    logger.info("Detectado: Fedora (apenas bootloader)")
            
            if os.path.exists(os.path.join(efi_path, "EFI", "steamos")):
                # SteamOS bootloader encontrado
                if not any(os["type"] == "Linux" and os["name"] == "SteamOS" for os in operating_systems):
                    operating_systems.append({
                        "name": "SteamOS",
                        "type": "Linux",
                        "path": "Desconhecido",
                        "bootloader": "EFI\\steamos\\grubx64.efi",
                        "drive_label": "Desconhecido",
                        "detected": True,
                        "active": True
                    })
                    
                    logger.info("Detectado: SteamOS (apenas bootloader)")
            
            if os.path.exists(os.path.join(efi_path, "EFI", "Apple")):
                # macOS bootloader encontrado
                if not any(os["type"] == "macOS" for os in operating_systems):
                    operating_systems.append({
                        "name": "macOS",
                        "type": "macOS",
                        "path": "Desconhecido",
                        "bootloader": "EFI\\Apple\\Boot\\bootmgfw.efi",
                        "drive_label": "Desconhecido",
                        "detected": True,
                        "active": True
                    })
                    
                    logger.info("Detectado: macOS (apenas bootloader)")
            
            # Desmontar a partição EFI se foi montada temporariamente
            if temp_drive_created:
                unmount_efi_partition(efi_drive_letter)
        except Exception as e:
            logger.error(f"Erro ao verificar bootloaders na partição EFI: {e}")
            
            # Desmontar a partição EFI se foi montada temporariamente
            if temp_drive_created:
                unmount_efi_partition(efi_drive_letter)
    
    # Se nenhum sistema operacional foi detectado, adicionar Windows como padrão
    if not operating_systems:
        operating_systems.append({
            "name": "Windows",
            "type": "Windows",
            "path": "C:\\Windows",
            "bootloader": "EFI\\Microsoft\\Boot\\bootmgfw.efi",
            "drive_label": "Windows",
            "detected": False,
            "active": True
        })
        
        logger.warning("Nenhum sistema operacional detectado. Adicionando Windows como padrão.")
    
    return operating_systems

def generate_clover_config(operating_systems: List[Dict[str, Any]]) -> str:
    """
    Gera um arquivo de configuração do Clover com base nos sistemas operacionais detectados.
    
    Args:
        operating_systems: Lista de dicionários com informações sobre os sistemas operacionais detectados.
        
    Returns:
        str: Caminho para o arquivo de configuração gerado.
    """
    logger.info("Gerando configuração do Clover para os sistemas operacionais detectados...")
    
    # Criar estrutura básica do config.plist
    config = {
        "Boot": {
            "Arguments": "",
            "DefaultVolume": "LastBootedVolume",
            "Timeout": 5,
            "XMPDetection": "Yes"
        },
        "GUI": {
            "Mouse": {
                "Enabled": True,
                "Speed": 8
            },
            "Scan": {
                "Entries": True,
                "Legacy": False,
                "Tool": True
            },
            "Theme": "Clovy",
            "Custom": {
                "Entries": []
            }
        }
    }
    
    # Adicionar entradas para cada sistema operacional detectado
    for os_info in operating_systems:
        if os_info.get("active", True):
            entry = {
                "Disabled": False,
                "FullTitle": os_info["name"],
                "Hidden": False,
                "Type": os_info["type"].lower(),
                "Path": os_info["bootloader"]
            }
            
            config["GUI"]["Custom"]["Entries"].append(entry)
    
    # Salvar o arquivo de configuração em um arquivo temporário
    with tempfile.NamedTemporaryFile(suffix=".plist", delete=False) as temp_file:
        temp_path = temp_file.name
    
    with open(temp_path, "wb") as f:
        plistlib.dump(config, f)
    
    logger.info(f"Configuração do Clover gerada com sucesso: {temp_path}")
    
    return temp_path

if __name__ == "__main__":
    # Configuração básica de logging para testes
    logging.basicConfig(level=logging.INFO)
    
    # Teste das funções
    print("Testando módulo de detecção de sistemas operacionais...")
    
    # Detectar sistemas operacionais
    print("\nDetectando sistemas operacionais:")
    operating_systems = detect_operating_systems()
    
    for os_info in operating_systems:
        print(f"  - {os_info['name']} ({os_info['type']})")
        print(f"    Caminho: {os_info['path']}")
        print(f"    Bootloader: {os_info['bootloader']}")
        print(f"    Rótulo: {os_info['drive_label']}")
        print(f"    Detectado: {os_info['detected']}")
        print(f"    Ativo: {os_info['active']}")
        print()
    
    # Gerar configuração do Clover
    print("\nGerando configuração do Clover:")
    config_path = generate_clover_config(operating_systems)
    print(f"Configuração gerada em: {config_path}")
