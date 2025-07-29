#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo para verificar a instalação do Clover Boot Manager.

Este módulo contém funções para verificar se o Clover Boot Manager está instalado corretamente.
"""

import os
import logging
import subprocess
import platform
from typing import Dict, Any, Optional, List, Tuple

# Importar módulo de backup da EFI
from env_dev.utils.efi_backup import find_efi_partition, unmount_efi_partition

# Configurar logger
logger = logging.getLogger(__name__)

def check_efi_partition() -> Tuple[Optional[str], bool, Dict[str, Any]]:
    """
    Verifica a partição EFI e sua estrutura.

    Returns:
        Tuple[Optional[str], bool, Dict[str, Any]]: Tupla contendo a letra da unidade EFI,
                                                   um booleano indicando se uma letra temporária foi criada,
                                                   e um dicionário com informações sobre a partição EFI.
    """
    # Encontrar a partição EFI
    try:
        efi_drive_letter, temp_drive_created = find_efi_partition()

        # Verifica se efi_drive_letter é uma string válida
        if efi_drive_letter and not isinstance(efi_drive_letter, str):
            logger.warning(f"Tipo inválido para letra de unidade EFI: {type(efi_drive_letter)}")
            # Tenta converter para string se possível
            efi_drive_letter = str(efi_drive_letter).strip()
            # Pega apenas o primeiro caractere se for uma string mais longa
            if len(efi_drive_letter) > 1:
                efi_drive_letter = efi_drive_letter[0]
                logger.warning(f"Usando apenas o primeiro caractere da letra de unidade EFI: {efi_drive_letter}")
    except Exception as e:
        logger.error(f"Erro ao encontrar partição EFI: {e}")
        efi_drive_letter = None
        temp_drive_created = False

    result = {
        "exists": False,
        "accessible": False,
        "size": 0,
        "free_space": 0,
        "efi_directory_exists": False,
        "boot_directory_exists": False,
        "clover_directory_exists": False
    }

    if not efi_drive_letter:
        logger.error("Não foi possível encontrar a partição EFI.")
        return None, False, result

    try:
        # Verificar se a partição EFI é acessível
        efi_path = f"{efi_drive_letter}:\\"
        result["exists"] = True

        if os.path.exists(efi_path):
            result["accessible"] = True

            # Obter informações sobre o espaço em disco
            ps_command = f"""
            $volume = Get-Volume -DriveLetter {efi_drive_letter}
            $size = [math]::Round($volume.Size / 1MB, 2)
            $freeSpace = [math]::Round($volume.SizeRemaining / 1MB, 2)
            Write-Output "$size,$freeSpace"
            """

            ps_result = subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True,
                text=True,
                check=False
            )

            if ps_result.returncode == 0 and ps_result.stdout.strip():
                size_str, free_space_str = ps_result.stdout.strip().split(",")
                result["size"] = float(size_str)
                result["free_space"] = float(free_space_str)

            # Verificar estrutura de diretórios
            result["efi_directory_exists"] = os.path.exists(os.path.join(efi_path, "EFI"))
            result["boot_directory_exists"] = os.path.exists(os.path.join(efi_path, "EFI", "BOOT"))
            result["clover_directory_exists"] = os.path.exists(os.path.join(efi_path, "EFI", "CLOVER"))

        return efi_drive_letter, temp_drive_created, result

    except Exception as e:
        logger.error(f"Erro ao verificar partição EFI: {e}")

        # Desmontar a partição EFI se foi montada temporariamente
        if temp_drive_created:
            unmount_efi_partition(efi_drive_letter)

        return efi_drive_letter, temp_drive_created, result

def verify_clover_installation() -> Dict[str, Any]:
    """
    Verifica se o Clover Boot Manager está instalado corretamente.

    Returns:
        Dict[str, Any]: Dicionário com o resultado da verificação.
    """
    result = {
        "success": False,
        "efi_partition_found": False,
        "clover_installed": False,
        "bootloader_preserved": False,
        "config_file_exists": False,
        "details": [],
        "issues": []
    }

    # Verificar partição EFI
    efi_drive_letter, temp_drive_created, efi_info = check_efi_partition()

    if not efi_drive_letter:
        # Verificar se o diretório C:\EFI\CLOVER existe (para compatibilidade com versões anteriores)
        if os.path.exists("C:\\EFI\\CLOVER"):
            result["success"] = True
            result["clover_installed"] = True
            result["details"].append("Clover encontrado em C:\\EFI\\CLOVER (instalação legada)")
            return result

        result["issues"].append("Partição EFI não encontrada ou não acessível.")
        return result

    result["efi_partition_found"] = True
    # Verifica se efi_drive_letter é uma string válida
    if isinstance(efi_drive_letter, str) and len(efi_drive_letter) == 1:
        result["details"].append(f"Partição EFI encontrada em {efi_drive_letter}:")
    else:
        result["details"].append(f"Partição EFI encontrada, mas com letra de unidade inválida: {efi_drive_letter}")
        logger.warning(f"Letra de unidade EFI inválida: {efi_drive_letter}")

    try:
        efi_path = f"{efi_drive_letter}:\\"

        # Verificar se o diretório CLOVER existe
        clover_path = os.path.join(efi_path, "EFI", "CLOVER")
        if os.path.exists(clover_path):
            result["clover_installed"] = True
            result["details"].append("Diretório CLOVER encontrado na partição EFI.")

            # Verificar arquivos essenciais do Clover
            clover_efi = os.path.join(clover_path, "CLOVERX64.efi")
            if os.path.exists(clover_efi):
                result["details"].append("Arquivo CLOVERX64.efi encontrado.")
            else:
                result["issues"].append("Arquivo CLOVERX64.efi não encontrado.")
                result["clover_installed"] = False

            # Verificar arquivo de configuração
            config_file = os.path.join(clover_path, "config.plist")
            if os.path.exists(config_file):
                result["config_file_exists"] = True
                result["details"].append("Arquivo de configuração config.plist encontrado.")
            else:
                result["issues"].append("Arquivo de configuração config.plist não encontrado.")

            # Verificar temas
            themes_dir = os.path.join(clover_path, "themes")
            if os.path.exists(themes_dir):
                themes_count = len([name for name in os.listdir(themes_dir) if os.path.isdir(os.path.join(themes_dir, name))])
                result["details"].append(f"{themes_count} temas encontrados.")
            else:
                result["details"].append("Diretório de temas não encontrado.")
        else:
            result["issues"].append("Diretório CLOVER não encontrado na partição EFI.")

        # Verificar se o bootloader original foi preservado
        original_bootloader = os.path.join(efi_path, "EFI", "BOOT", "BOOTX64.efi.original")
        if os.path.exists(original_bootloader):
            result["bootloader_preserved"] = True
            result["details"].append("Bootloader original preservado como BOOTX64.efi.original.")
        else:
            result["details"].append("Bootloader original não encontrado (pode não ter sido preservado).")

        # Determinar o sucesso geral da verificação
        result["success"] = result["clover_installed"] and result["config_file_exists"]

        # Desmontar a partição EFI se foi montada temporariamente
        if temp_drive_created:
            unmount_efi_partition(efi_drive_letter)

        return result

    except Exception as e:
        logger.error(f"Erro ao verificar instalação do Clover: {e}")
        result["issues"].append(f"Erro durante a verificação: {str(e)}")

        # Desmontar a partição EFI se foi montada temporariamente
        if temp_drive_created:
            unmount_efi_partition(efi_drive_letter)

        return result

if __name__ == "__main__":
    # Configuração básica de logging para testes
    logging.basicConfig(level=logging.INFO)

    # Teste das funções
    print("Testando módulo de verificação do Clover...")

    # Verificar partição EFI
    print("\nVerificando partição EFI:")
    efi_drive_letter, temp_drive_created, efi_info = check_efi_partition()

    if efi_drive_letter:
        print(f"Partição EFI encontrada em {efi_drive_letter}:")
        print(f"  Tamanho: {efi_info['size']} MB")
        print(f"  Espaço livre: {efi_info['free_space']} MB")
        print(f"  Diretório EFI existe: {efi_info['efi_directory_exists']}")
        print(f"  Diretório BOOT existe: {efi_info['boot_directory_exists']}")
        print(f"  Diretório CLOVER existe: {efi_info['clover_directory_exists']}")
    else:
        print("Partição EFI não encontrada.")

    # Verificar instalação do Clover
    print("\nVerificando instalação do Clover:")
    clover_result = verify_clover_installation()

    print(f"Instalação do Clover válida: {clover_result['success']}")
    print("\nDetalhes:")
    for detail in clover_result["details"]:
        print(f"  - {detail}")

    if clover_result["issues"]:
        print("\nProblemas encontrados:")
        for issue in clover_result["issues"]:
            print(f"  - {issue}")
