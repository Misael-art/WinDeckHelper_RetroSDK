#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo para gerenciar backups da partição EFI.

Este módulo contém funções para criar, listar e restaurar backups da partição EFI.
"""

import os
import shutil
import datetime
import logging
import subprocess
import json
import platform
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Configurar logger
logger = logging.getLogger(__name__)

# Diretório padrão para backups da EFI
DEFAULT_BACKUP_DIR = os.path.join(os.path.expanduser("~"), "Documents", "Environment_Dev", "EFI_Backups")

def find_efi_partition() -> Tuple[Optional[str], bool]:
    """
    Encontra a partição EFI e retorna sua letra de unidade.

    Returns:
        Tuple[Optional[str], bool]: Tupla contendo a letra da unidade EFI (ou None se não encontrada)
                                   e um booleano indicando se uma letra temporária foi criada.
    """
    logger.info("Procurando partição EFI...")

    # Verificar se estamos no Windows
    if platform.system() != "Windows":
        logger.error("Este módulo só é compatível com Windows.")
        return None, False

    efi_drive_letter = None
    temp_drive_created = False

    try:
        # Verificar se já existe uma partição EFI montada
        # Executar PowerShell para listar volumes
        ps_command = """
        Get-Volume | Where-Object { Test-Path "$($_.DriveLetter):\\EFI" -ErrorAction SilentlyContinue } | Select-Object -ExpandProperty DriveLetter
        """
        result = subprocess.run(
            ["powershell", "-Command", ps_command],
            capture_output=True,
            text=True,
            check=False
        )

        if result.stdout.strip():
            # Limpar e processar a saída para obter apenas a letra da unidade
            output = result.stdout.strip()
            # Extrair apenas a primeira letra válida da saída
            for char in output:
                if char.isalpha():
                    efi_drive_letter = char
                    break

            if efi_drive_letter:
                logger.info(f"Partição EFI já montada em {efi_drive_letter}:")
                return efi_drive_letter, False
            else:
                logger.warning(f"Saída inválida ao procurar partição EFI: {output}")
                # Tentar usar a letra E como padrão
                efi_drive_letter = 'E'
                logger.info(f"Usando letra padrão para partição EFI: {efi_drive_letter}")
                return efi_drive_letter, False

        # Se não encontrou, tentar montar a partição EFI
        ps_mount_command = """
        $disks = Get-Disk | Where-Object {$_.PartitionStyle -eq "GPT"}
        foreach ($disk in $disks) {
            $efiPartitions = $disk | Get-Partition | Where-Object {$_.GptType -eq "{c12a7328-f81f-11d2-ba4b-00a0c93ec93b}"}
            if ($efiPartitions) {
                try {
                    $efiVolume = $efiPartitions[0] | Get-Volume -ErrorAction SilentlyContinue
                    if ($efiVolume -and -not $efiVolume.DriveLetter) {
                        $driveLetter = 69 # Letra 'E'
                        while ([char]$driveLetter -le 90) {
                            $letter = [char]$driveLetter
                            if (-not (Get-Volume -DriveLetter $letter -ErrorAction SilentlyContinue)) {
                                $efiPartitions[0] | Add-PartitionAccessPath -AccessPath "${letter}:"
                                Write-Output $letter
                                exit 0
                            }
                            $driveLetter++
                        }
                    } elseif ($efiVolume) {
                        Write-Output $efiVolume.DriveLetter
                        exit 0
                    }
                } catch {
                    Write-Error "Erro ao acessar partição EFI: $_"
                }
            }
        }
        Write-Output "NOT_FOUND"
        """

        result = subprocess.run(
            ["powershell", "-Command", ps_mount_command],
            capture_output=True,
            text=True,
            check=False
        )

        output = result.stdout.strip()
        if output and output != "NOT_FOUND":
            # Limpar e processar a saída para obter apenas a letra da unidade
            # Extrair apenas a primeira letra válida da saída
            for char in output:
                if char.isalpha():
                    efi_drive_letter = char
                    break

            if efi_drive_letter:
                temp_drive_created = True
                logger.info(f"Partição EFI montada temporariamente em {efi_drive_letter}:")
                return efi_drive_letter, temp_drive_created
            else:
                logger.warning(f"Saída inválida ao montar partição EFI: {output}")
                # Tentar usar a letra E como padrão
                efi_drive_letter = 'E'
                temp_drive_created = True
                logger.info(f"Usando letra padrão para partição EFI montada: {efi_drive_letter}")
                return efi_drive_letter, temp_drive_created

        logger.error("Não foi possível encontrar ou montar a partição EFI.")
        return None, False

    except Exception as e:
        logger.error(f"Erro ao procurar partição EFI: {e}")
        return None, False

def unmount_efi_partition(drive_letter: str) -> bool:
    """
    Desmonta a partição EFI se foi montada temporariamente.

    Args:
        drive_letter: Letra da unidade a ser desmontada.

    Returns:
        bool: True se a operação foi bem-sucedida, False caso contrário.
    """
    if not drive_letter:
        return False

    try:
        ps_command = f"""
        $efiPartition = Get-Partition | Where-Object {{$_.GptType -eq "{{c12a7328-f81f-11d2-ba4b-00a0c93ec93b}}"}}
        $efiPartition | Remove-PartitionAccessPath -AccessPath "{drive_letter}:"
        """

        result = subprocess.run(
            ["powershell", "-Command", ps_command],
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode == 0:
            logger.info(f"Partição EFI desmontada com sucesso: {drive_letter}:")
            return True
        else:
            logger.error(f"Erro ao desmontar partição EFI: {result.stderr}")
            return False

    except Exception as e:
        logger.error(f"Erro ao desmontar partição EFI: {e}")
        return False

def create_efi_backup(backup_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Cria um backup da partição EFI.

    Args:
        backup_name: Nome opcional para o backup. Se não fornecido, um nome será gerado.

    Returns:
        Optional[Dict[str, Any]]: Dicionário com informações do backup, ou None se falhar.
    """
    # Criar diretório de backup se não existir
    os.makedirs(DEFAULT_BACKUP_DIR, exist_ok=True)

    # Gerar nome do backup se não fornecido
    if not backup_name:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"EFI_Backup_{timestamp}"

    backup_path = os.path.join(DEFAULT_BACKUP_DIR, backup_name)

    # Encontrar a partição EFI
    efi_drive_letter, temp_drive_created = find_efi_partition()

    if not efi_drive_letter:
        logger.error("Não foi possível encontrar a partição EFI para backup.")
        return None

    try:
        # Criar diretório de backup
        os.makedirs(backup_path, exist_ok=True)

        # Copiar conteúdo da partição EFI
        efi_path = f"{efi_drive_letter}:\\"
        logger.info(f"Copiando conteúdo da partição EFI de {efi_path} para {backup_path}...")

        # Usar robocopy para cópia mais confiável
        robocopy_command = f'robocopy "{efi_path}" "{backup_path}" /E /R:1 /W:1'

        result = subprocess.run(
            robocopy_command,
            shell=True,
            capture_output=True,
            text=True,
            check=False
        )

        # Robocopy retorna códigos diferentes de 0 mesmo em caso de sucesso
        # Códigos 0-7 são considerados sucesso
        if result.returncode <= 7:
            logger.info("Backup da partição EFI criado com sucesso.")

            # Criar arquivo de metadados
            metadata = {
                "date": datetime.datetime.now().isoformat(),
                "efi_drive_letter": efi_drive_letter,
                "backup_path": backup_path,
                "temp_drive_created": temp_drive_created
            }

            with open(os.path.join(backup_path, "backup_info.json"), "w") as f:
                json.dump(metadata, f, indent=2)

            # Desmontar a partição EFI se foi montada temporariamente
            if temp_drive_created:
                unmount_efi_partition(efi_drive_letter)

            return {
                "name": backup_name,
                "path": backup_path,
                "date": metadata["date"],
                "success": True
            }
        else:
            logger.error(f"Erro ao copiar arquivos da partição EFI: {result.stderr}")

            # Desmontar a partição EFI se foi montada temporariamente
            if temp_drive_created:
                unmount_efi_partition(efi_drive_letter)

            return None

    except Exception as e:
        logger.error(f"Erro ao criar backup da partição EFI: {e}")

        # Desmontar a partição EFI se foi montada temporariamente
        if temp_drive_created:
            unmount_efi_partition(efi_drive_letter)

        return None

def list_efi_backups() -> List[Dict[str, Any]]:
    """
    Lista todos os backups disponíveis da partição EFI.

    Returns:
        List[Dict[str, Any]]: Lista de dicionários com informações dos backups.
    """
    backups = []

    # Verificar se o diretório de backups existe
    if not os.path.exists(DEFAULT_BACKUP_DIR):
        logger.warning(f"Diretório de backups não encontrado: {DEFAULT_BACKUP_DIR}")
        return backups

    # Listar diretórios de backup
    for item in os.listdir(DEFAULT_BACKUP_DIR):
        item_path = os.path.join(DEFAULT_BACKUP_DIR, item)

        if os.path.isdir(item_path):
            # Verificar se é um backup válido (contém arquivo de metadados)
            metadata_file = os.path.join(item_path, "backup_info.json")

            if os.path.exists(metadata_file):
                try:
                    with open(metadata_file, "r") as f:
                        metadata = json.load(f)

                    backups.append({
                        "name": item,
                        "path": item_path,
                        "date": metadata.get("date", "Desconhecido"),
                        "efi_drive_letter": metadata.get("efi_drive_letter", "Desconhecido")
                    })
                except Exception as e:
                    logger.warning(f"Erro ao ler metadados do backup {item}: {e}")
            else:
                # Verificar se contém diretório EFI (backup sem metadados)
                if os.path.exists(os.path.join(item_path, "EFI")):
                    creation_time = os.path.getctime(item_path)
                    creation_date = datetime.datetime.fromtimestamp(creation_time).isoformat()

                    backups.append({
                        "name": item,
                        "path": item_path,
                        "date": creation_date,
                        "efi_drive_letter": "Desconhecido"
                    })

    # Ordenar backups por data (mais recente primeiro)
    backups.sort(key=lambda x: x["date"], reverse=True)

    return backups

def restore_efi_backup(backup_path: str) -> bool:
    """
    Restaura um backup da partição EFI.

    Args:
        backup_path: Caminho para o diretório de backup.

    Returns:
        bool: True se a restauração foi bem-sucedida, False caso contrário.
    """
    # Verificar se o backup existe
    if not os.path.exists(backup_path):
        logger.error(f"Backup não encontrado: {backup_path}")
        return False

    # Verificar se é um backup válido
    if not os.path.exists(os.path.join(backup_path, "EFI")):
        logger.error(f"Backup inválido (diretório EFI não encontrado): {backup_path}")
        return False

    # Encontrar a partição EFI
    efi_drive_letter, temp_drive_created = find_efi_partition()

    if not efi_drive_letter:
        logger.error("Não foi possível encontrar a partição EFI para restauração.")
        return False

    try:
        # Restaurar conteúdo da partição EFI
        efi_path = f"{efi_drive_letter}:\\"
        logger.info(f"Restaurando conteúdo da partição EFI de {backup_path} para {efi_path}...")

        # Usar robocopy para cópia mais confiável
        robocopy_command = f'robocopy "{backup_path}" "{efi_path}" /E /R:1 /W:1'

        result = subprocess.run(
            robocopy_command,
            shell=True,
            capture_output=True,
            text=True,
            check=False
        )

        # Robocopy retorna códigos diferentes de 0 mesmo em caso de sucesso
        # Códigos 0-7 são considerados sucesso
        if result.returncode <= 7:
            logger.info("Backup da partição EFI restaurado com sucesso.")

            # Desmontar a partição EFI se foi montada temporariamente
            if temp_drive_created:
                unmount_efi_partition(efi_drive_letter)

            return True
        else:
            logger.error(f"Erro ao restaurar arquivos para a partição EFI: {result.stderr}")

            # Desmontar a partição EFI se foi montada temporariamente
            if temp_drive_created:
                unmount_efi_partition(efi_drive_letter)

            return False

    except Exception as e:
        logger.error(f"Erro ao restaurar backup da partição EFI: {e}")

        # Desmontar a partição EFI se foi montada temporariamente
        if temp_drive_created:
            unmount_efi_partition(efi_drive_letter)

        return False

def restore_latest_backup() -> bool:
    """
    Restaura o backup mais recente da partição EFI.

    Returns:
        bool: True se a restauração foi bem-sucedida, False caso contrário.
    """
    backups = list_efi_backups()

    if not backups:
        logger.error("Nenhum backup encontrado para restauração.")
        return False

    # Pegar o backup mais recente
    latest_backup = backups[0]

    logger.info(f"Restaurando backup mais recente: {latest_backup['name']} ({latest_backup['date']})")

    return restore_efi_backup(latest_backup["path"])

if __name__ == "__main__":
    # Configuração básica de logging para testes
    logging.basicConfig(level=logging.INFO)

    # Teste das funções
    print("Testando módulo de backup da EFI...")

    # Listar backups existentes
    print("\nBackups existentes:")
    backups = list_efi_backups()
    for backup in backups:
        print(f"  - {backup['name']} ({backup['date']})")

    # Criar novo backup
    print("\nCriando novo backup...")
    backup_result = create_efi_backup()

    if backup_result:
        print(f"Backup criado com sucesso: {backup_result['name']}")
    else:
        print("Falha ao criar backup.")

    # Listar backups novamente
    print("\nBackups após criação:")
    backups = list_efi_backups()
    for backup in backups:
        print(f"  - {backup['name']} ({backup['date']})")
