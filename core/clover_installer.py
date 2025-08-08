#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo para instalar o Clover Boot Manager.

Este módulo contém funções para instalar e desinstalar o Clover Boot Manager.
"""

import os
import logging
import subprocess
import platform
import tempfile
import zipfile
import shutil
import time
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Union

# Importar módulos auxiliares
from env_dev.utils.efi_backup import find_efi_partition, unmount_efi_partition, create_efi_backup
from env_dev.utils.os_detection import detect_operating_systems, generate_clover_config
from env_dev.utils.clover_verification import verify_clover_installation

# Configurar logger
logger = logging.getLogger(__name__)

# Caminho para o arquivo ZIP do Clover
CLOVER_ZIP_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "resources",
    "clover",
    "CloverV2-5161.zip"
)

# Verificar se o arquivo ZIP do Clover existe
if not os.path.exists(CLOVER_ZIP_PATH):
    logger.warning(f"Arquivo ZIP do Clover não encontrado em {CLOVER_ZIP_PATH}")

    # Tentar encontrar o arquivo ZIP do Clover em outros locais
    alt_paths = [
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "env_dev", "config", "scripts", "CloverV2-5161.zip"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "env_dev", "config", "scripts", "CloverV2-5151-X64.zip"),
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "resources", "clover", "CloverV2-5151-X64.zip")
    ]

    # Procurar o arquivo ZIP do Clover em todos os locais alternativos
    for alt_path in alt_paths:
        if os.path.exists(alt_path):
            logger.info(f"Arquivo ZIP do Clover encontrado em {alt_path}")
            CLOVER_ZIP_PATH = alt_path
            break

    # Se ainda não encontrou, procurar em qualquer arquivo .zip no diretório resources/clover
    if not os.path.exists(CLOVER_ZIP_PATH):
        resources_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "resources", "clover")
        if os.path.exists(resources_dir):
            for file in os.listdir(resources_dir):
                if file.endswith(".zip") and "clover" in file.lower():
                    CLOVER_ZIP_PATH = os.path.join(resources_dir, file)
                    logger.info(f"Usando arquivo ZIP do Clover: {CLOVER_ZIP_PATH}")
                    break

    for alt_path in alt_paths:
        if os.path.exists(alt_path):
            logger.info(f"Arquivo ZIP do Clover encontrado em {alt_path}")
            CLOVER_ZIP_PATH = alt_path
            break

def _get_clover_search_paths() -> List[str]:
    """
    Retorna lista de caminhos onde procurar o arquivo ZIP do Clover.
    
    Returns:
        Lista de caminhos para busca
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    return [
        os.path.join(base_dir, "resources", "clover"),
        os.path.join(base_dir, "env_dev", "config", "scripts"),
        os.path.join(os.path.expanduser("~"), "Downloads", "Environment_Dev", "clover"),
        os.path.join(os.path.expanduser("~"), "Downloads"),
        os.path.join(base_dir, "downloads"),
        os.path.join(base_dir, "temp_download")
    ]

def _find_clover_zip() -> Optional[str]:
    """
    Procura o arquivo ZIP do Clover em locais conhecidos.
    
    Returns:
        Caminho do arquivo ZIP encontrado ou None se não encontrado
    """
    # Primeiro verificar o caminho padrão
    if os.path.exists(CLOVER_ZIP_PATH):
        return CLOVER_ZIP_PATH
    
    # Procurar em locais alternativos
    search_paths = _get_clover_search_paths()
    
    for search_dir in search_paths:
        if not os.path.exists(search_dir):
            continue
            
        try:
            for file in os.listdir(search_dir):
                if (file.lower().startswith("clover") and 
                    file.endswith(".zip") and 
                    os.path.isfile(os.path.join(search_dir, file))):
                    
                    found_path = os.path.join(search_dir, file)
                    logger.info(f"Arquivo Clover encontrado em: {found_path}")
                    return found_path
        except (OSError, PermissionError) as e:
            logger.debug(f"Erro ao acessar diretório {search_dir}: {e}")
            continue
    
    return None

def check_prerequisites() -> Dict[str, Any]:
    """
    Verifica os pré-requisitos para a instalação do Clover.

    Returns:
        Dict[str, Any]: Dicionário com o resultado da verificação.
    """
    result = {
        "success": True,
        "is_windows": False,
        "is_admin": False,
        "is_uefi": False,
        "efi_partition_found": False,
        "efi_space_sufficient": False,
        "clover_zip_found": False,
        "issues": []
    }

    # Verificar se estamos no Windows
    if platform.system() != "Windows":
        result["success"] = False
        result["issues"].append("Este módulo só é compatível com Windows.")
        return result

    result["is_windows"] = True

    # Verificar se estamos executando como administrador
    try:
        ps_command = """
        ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
        """

        ps_result = subprocess.run(
            ["powershell", "-Command", ps_command],
            capture_output=True,
            text=True,
            check=False
        )

        if ps_result.returncode == 0 and ps_result.stdout.strip().lower() == "true":
            result["is_admin"] = True
        else:
            result["success"] = False
            result["issues"].append("O script deve ser executado como administrador.")
    except Exception as e:
        logger.error(f"Erro ao verificar privilégios de administrador: {e}")
        result["success"] = False
        result["issues"].append(f"Erro ao verificar privilégios de administrador: {str(e)}")

    # Verificar se o sistema está em modo UEFI
    try:
        ps_command = """
        $firmware = Get-ComputerInfo | Select-Object BiosFirmwareType
        $firmware.BiosFirmwareType -eq "Uefi"
        """

        ps_result = subprocess.run(
            ["powershell", "-Command", ps_command],
            capture_output=True,
            text=True,
            check=False
        )

        if ps_result.returncode == 0 and ps_result.stdout.strip().lower() == "true":
            result["is_uefi"] = True
        else:
            result["success"] = False
            result["issues"].append("O sistema deve estar em modo UEFI para instalar o Clover.")
    except Exception as e:
        logger.error(f"Erro ao verificar modo UEFI: {e}")
        result["success"] = False
        result["issues"].append(f"Erro ao verificar modo UEFI: {str(e)}")

    # Verificar partição EFI
    efi_drive_letter, temp_drive_created = find_efi_partition()

    if efi_drive_letter:
        result["efi_partition_found"] = True

        # Verificar espaço na partição EFI
        try:
            ps_command = f"""
            $volume = Get-Volume -DriveLetter {efi_drive_letter}
            $freeSpace = [math]::Round($volume.SizeRemaining / 1MB, 2)
            Write-Output $freeSpace
            """

            ps_result = subprocess.run(
                ["powershell", "-Command", ps_command],
                capture_output=True,
                text=True,
                check=False
            )

            if ps_result.returncode == 0 and ps_result.stdout.strip():
                free_space = float(ps_result.stdout.strip())

                if free_space >= 10:  # Mínimo de 10 MB
                    result["efi_space_sufficient"] = True
                else:
                    result["success"] = False
                    result["issues"].append(f"Espaço insuficiente na partição EFI: {free_space} MB (mínimo 10 MB).")
        except Exception as e:
            logger.error(f"Erro ao verificar espaço na partição EFI: {e}")
            result["success"] = False
            result["issues"].append(f"Erro ao verificar espaço na partição EFI: {str(e)}")

        # Desmontar a partição EFI se foi montada temporariamente
        if temp_drive_created:
            unmount_efi_partition(efi_drive_letter)
    else:
        result["success"] = False
        result["issues"].append("Partição EFI não encontrada ou não acessível.")

    # Verificar se o arquivo ZIP do Clover existe
    if os.path.exists(CLOVER_ZIP_PATH):
        result["clover_zip_found"] = True
    else:
        result["success"] = False
        result["issues"].append(f"Arquivo ZIP do Clover não encontrado: {CLOVER_ZIP_PATH}")

    return result

def extract_clover_zip(destination_path: str, clover_zip_path: str = None) -> bool:
    """
    Extrai o arquivo ZIP do Clover para o diretório de destino.

    Args:
        destination_path: Caminho para o diretório de destino.
        clover_zip_path: Caminho do arquivo ZIP (opcional, usa busca automática se None).

    Returns:
        bool: True se a extração foi bem-sucedida, False caso contrário.
    """
    try:
        # Encontrar arquivo ZIP se não fornecido
        if clover_zip_path is None:
            clover_zip_path = _find_clover_zip()
        
        if not clover_zip_path or not os.path.exists(clover_zip_path):
            logger.error(f"Arquivo ZIP do Clover não encontrado: {clover_zip_path}")
            return False

        # Criar diretório de destino se não existir
        os.makedirs(destination_path, exist_ok=True)

        # Extrair arquivo ZIP
        with zipfile.ZipFile(clover_zip_path, "r") as zip_ref:
            zip_ref.extractall(destination_path)

        # Verificar se a extração foi bem-sucedida
        if os.path.exists(os.path.join(destination_path, "EFI")):
            logger.info(f"Arquivo ZIP do Clover extraído com sucesso para {destination_path}")
            return True
        else:
            logger.error("Falha ao extrair arquivo ZIP do Clover: diretório EFI não encontrado")
            return False
    except Exception as e:
        logger.error(f"Erro ao extrair arquivo ZIP do Clover: {e}")
        return False

def install_clover(rollback_mgr=None, force: bool = False) -> bool:
    """
    Instala o Clover Boot Manager.

    Args:
        rollback_mgr: Gerenciador de rollback (opcional).
        force: Se True, força a instalação mesmo se os pré-requisitos não forem atendidos.

    Returns:
        bool: True se a instalação foi bem-sucedida, False caso contrário.
    """
    logger.info("========== INICIANDO INSTALAÇÃO DO CLOVER BOOT MANAGER ==========")
    logger.debug(f"Parâmetros: rollback_mgr={rollback_mgr}, force={force}")
    logger.debug(f"Diretório atual: {os.getcwd()}")
    logger.debug(f"Diretório do script: {os.path.dirname(os.path.abspath(__file__))}")

    # Verificar se o arquivo ZIP do Clover existe
    logger.info("Verificando arquivo ZIP do Clover...")
    clover_zip_path = _find_clover_zip()
    
    if not clover_zip_path:
        logger.error("Arquivo ZIP do Clover não encontrado em nenhum local conhecido")
        logger.info("Para instalar o Clover, baixe o arquivo ZIP do Clover e coloque em uma das seguintes pastas:")
        alternative_paths = _get_clover_search_paths()
        for path in alternative_paths:
            logger.info(f"  - {path}")
        return False
    
    logger.info(f"Arquivo ZIP do Clover encontrado: {clover_zip_path}")
    logger.debug(f"Tamanho do arquivo: {os.path.getsize(clover_zip_path) / (1024*1024):.2f} MB")
    logger.debug(f"Data de modificação: {time.ctime(os.path.getmtime(clover_zip_path))}")

    # Verificar pré-requisitos
    logger.info("Verificando pré-requisitos para instalação do Clover...")
    prereq_result = check_prerequisites()
    logger.debug(f"Resultado da verificação de pré-requisitos: {prereq_result}")

    if not prereq_result["success"] and not force:
        logger.error("Pré-requisitos não atendidos para instalação do Clover:")
        for issue in prereq_result["issues"]:
            logger.error(f"  - {issue}")
        logger.info("Use a opção 'force=True' para forçar a instalação mesmo sem atender os pré-requisitos.")
        return False

    if not prereq_result["success"] and force:
        logger.warning("Forçando instalação do Clover mesmo sem atender os pré-requisitos:")
        for issue in prereq_result["issues"]:
            logger.warning(f"  - {issue}")
        logger.debug("Modo forçado ativado - continuando instalação mesmo com pré-requisitos não atendidos")

    # Criar backup da partição EFI
    logger.info("Criando backup da partição EFI...")
    backup_result = create_efi_backup()

    if backup_result:
        # Verifica se o resultado é um dicionário ou um booleano
        if isinstance(backup_result, dict) and 'path' in backup_result:
            logger.info(f"Backup da partição EFI criado com sucesso: {backup_result['path']}")
        else:
            logger.info("Backup da partição EFI criado com sucesso.")

        # Registrar backup no gerenciador de rollback, se disponível
        if rollback_mgr:
            try:
                rollback_mgr.register_backup("efi_partition", backup_result["path"])
                logger.info("Backup registrado no gerenciador de rollback")
            except Exception as e:
                logger.warning(f"Erro ao registrar backup no gerenciador de rollback: {e}")
    else:
        logger.warning("Falha ao criar backup da partição EFI")

        if not force:
            logger.error("Abortando instalação devido a falha no backup")
            return False

    # Criar diretório temporário para extração
    with tempfile.TemporaryDirectory() as temp_dir:
        logger.info(f"Extraindo Clover para diretório temporário: {temp_dir}")

        # Extrair arquivo ZIP do Clover
        if not extract_clover_zip(temp_dir, clover_zip_path):
            logger.error("Falha ao extrair arquivo ZIP do Clover")
            return False

        # Encontrar a partição EFI
        efi_drive_letter, temp_drive_created = find_efi_partition()

        if not efi_drive_letter:
            # Se não encontrar a partição EFI, tentar instalar em C:\EFI\CLOVER (para compatibilidade com versões anteriores)
            logger.warning("Não foi possível encontrar a partição EFI. Tentando instalar em C:\\EFI\\CLOVER")

            # Criar diretório C:\EFI\CLOVER se não existir
            os.makedirs("C:\\EFI\\CLOVER", exist_ok=True)

            # Copiar arquivos do Clover para C:\EFI\CLOVER
            try:
                # Verificar se o diretório EFI existe no diretório temporário
                if not os.path.exists(os.path.join(temp_dir, "EFI", "CLOVER")):
                    logger.error("Diretório EFI\\CLOVER não encontrado no arquivo ZIP do Clover")
                    return False

                # Copiar diretório CLOVER
                logger.info("Copiando arquivos do Clover para C:\\EFI\\CLOVER...")
                shutil.copytree(os.path.join(temp_dir, "EFI", "CLOVER"), "C:\\EFI\\CLOVER", dirs_exist_ok=True)

                # Verificar se a cópia foi bem-sucedida
                if os.path.exists(os.path.join("C:\\EFI\\CLOVER", "CLOVERX64.efi")):
                    logger.info("Arquivos do Clover copiados com sucesso para C:\\EFI\\CLOVER")
                    return True
                else:
                    logger.error("Falha ao copiar arquivos do Clover para C:\\EFI\\CLOVER")
                    return False
            except Exception as e:
                logger.error(f"Erro ao instalar o Clover em C:\\EFI\\CLOVER: {e}")
                return False

        try:
            efi_path = f"{efi_drive_letter}:\\"

            # Verificar se o diretório EFI existe na partição
            if not os.path.exists(os.path.join(efi_path, "EFI")):
                os.makedirs(os.path.join(efi_path, "EFI"), exist_ok=True)

            # Preservar o bootloader original
            boot_dir = os.path.join(efi_path, "EFI", "BOOT")
            original_bootloader = os.path.join(boot_dir, "BOOTX64.efi")

            if os.path.exists(original_bootloader):
                logger.info("Preservando bootloader original...")
                shutil.copy2(original_bootloader, os.path.join(boot_dir, "BOOTX64.efi.original"))
                logger.info("Bootloader original preservado como BOOTX64.efi.original")

            # Verificar se o diretório CLOVER já existe e fazer backup se necessário
            clover_dir = os.path.join(efi_path, "EFI", "CLOVER")
            clover_backup_dir = os.path.join(efi_path, "EFI", "CLOVER.bak")

            if os.path.exists(clover_dir):
                logger.info("Fazendo backup da instalação anterior do Clover...")

                if os.path.exists(clover_backup_dir):
                    shutil.rmtree(clover_backup_dir)

                os.rename(clover_dir, clover_backup_dir)
                logger.info("Backup da instalação anterior do Clover criado como CLOVER.bak")

            # Copiar diretório CLOVER
            logger.info("Copiando arquivos do Clover para a partição EFI...")
            shutil.copytree(os.path.join(temp_dir, "EFI", "CLOVER"), clover_dir)

            # Verificar se a cópia foi bem-sucedida
            if os.path.exists(os.path.join(clover_dir, "CLOVERX64.efi")):
                logger.info("Arquivos do Clover copiados com sucesso")

                # Detectar sistemas operacionais e gerar configuração
                logger.info("Detectando sistemas operacionais...")
                operating_systems = detect_operating_systems()

                if operating_systems:
                    logger.info(f"Detectados {len(operating_systems)} sistemas operacionais")

                    # Gerar configuração do Clover
                    config_path = generate_clover_config(operating_systems)

                    # Copiar configuração para o diretório do Clover
                    shutil.copy2(config_path, os.path.join(clover_dir, "config.plist"))
                    logger.info("Configuração do Clover gerada e copiada com sucesso")

                    # Remover arquivo temporário
                    os.unlink(config_path)
                else:
                    logger.warning("Nenhum sistema operacional detectado")

                # Perguntar se deseja usar o Clover como bootloader principal
                use_clover_as_main = False

                try:
                    response = input("Deseja configurar o Clover como bootloader principal? (S/N) [N]: ")
                    use_clover_as_main = response.strip().upper() == "S"
                except:
                    # Em caso de erro ou execução não interativa, não usar como bootloader principal
                    logger.warning("Modo não interativo detectado, preservando bootloader original")

                if use_clover_as_main:
                    logger.warning("Configurando Clover como bootloader principal...")

                    # Verificar se o diretório BOOT existe
                    if not os.path.exists(boot_dir):
                        os.makedirs(boot_dir, exist_ok=True)

                    # Copiar o Clover como bootloader principal
                    shutil.copy2(os.path.join(clover_dir, "CLOVERX64.efi"), os.path.join(boot_dir, "BOOTX64.efi"))

                    # Verificar se a cópia foi bem-sucedida
                    if os.path.exists(os.path.join(boot_dir, "BOOTX64.efi")):
                        logger.info("Clover configurado como bootloader principal")
                    else:
                        logger.error("Falha ao configurar Clover como bootloader principal")
                else:
                    logger.info("Preservando bootloader original")

                # Desmontar a partição EFI se foi montada temporariamente
                if temp_drive_created:
                    unmount_efi_partition(efi_drive_letter)

                logger.info("Instalação do Clover Boot Manager concluída com sucesso")
                return True
            else:
                logger.error("Falha ao copiar arquivos do Clover: CLOVERX64.efi não encontrado")

                # Tentar restaurar backup anterior se existir
                if os.path.exists(clover_backup_dir):
                    logger.info("Restaurando backup anterior do Clover...")

                    if os.path.exists(clover_dir):
                        shutil.rmtree(clover_dir)

                    os.rename(clover_backup_dir, clover_dir)
                    logger.info("Backup anterior do Clover restaurado")

                # Desmontar a partição EFI se foi montada temporariamente
                if temp_drive_created:
                    unmount_efi_partition(efi_drive_letter)

                return False
        except Exception as e:
            logger.error(f"Erro ao instalar o Clover: {e}")

            # Desmontar a partição EFI se foi montada temporariamente
            if temp_drive_created:
                unmount_efi_partition(efi_drive_letter)

            return False

def uninstall_clover() -> bool:
    """
    Desinstala o Clover Boot Manager.

    Returns:
        bool: True se a desinstalação foi bem-sucedida, False caso contrário.
    """
    logger.info("Iniciando desinstalação do Clover Boot Manager...")

    # Criar backup da partição EFI antes da desinstalação
    logger.info("Criando backup da partição EFI antes da desinstalação...")
    backup_result = create_efi_backup("Pre_Clover_Uninstall")

    if backup_result:
        logger.info(f"Backup da partição EFI criado com sucesso: {backup_result['path']}")
    else:
        logger.warning("Falha ao criar backup da partição EFI antes da desinstalação")

    # Encontrar a partição EFI
    efi_drive_letter, temp_drive_created = find_efi_partition()

    if not efi_drive_letter:
        logger.error("Não foi possível encontrar a partição EFI para desinstalação")
        return False

    try:
        efi_path = f"{efi_drive_letter}:\\"

        # Verificar se o Clover está instalado
        clover_dir = os.path.join(efi_path, "EFI", "CLOVER")

        if not os.path.exists(clover_dir):
            logger.warning("Clover não encontrado na partição EFI")

            # Desmontar a partição EFI se foi montada temporariamente
            if temp_drive_created:
                unmount_efi_partition(efi_drive_letter)

            return False

        # Restaurar bootloader original se existir
        boot_dir = os.path.join(efi_path, "EFI", "BOOT")
        original_bootloader = os.path.join(boot_dir, "BOOTX64.efi.original")

        if os.path.exists(original_bootloader):
            logger.info("Restaurando bootloader original...")
            shutil.copy2(original_bootloader, os.path.join(boot_dir, "BOOTX64.efi"))
            logger.info("Bootloader original restaurado")

        # Remover diretório CLOVER
        logger.info("Removendo diretório CLOVER...")
        shutil.rmtree(clover_dir)

        # Verificar se a remoção foi bem-sucedida
        if not os.path.exists(clover_dir):
            logger.info("Diretório CLOVER removido com sucesso")

            # Restaurar backup anterior se existir
            clover_backup_dir = os.path.join(efi_path, "EFI", "CLOVER.bak")

            if os.path.exists(clover_backup_dir):
                logger.info("Restaurando backup anterior do Clover...")
                os.rename(clover_backup_dir, clover_dir)
                logger.info("Backup anterior do Clover restaurado")

            # Desmontar a partição EFI se foi montada temporariamente
            if temp_drive_created:
                unmount_efi_partition(efi_drive_letter)

            logger.info("Desinstalação do Clover Boot Manager concluída com sucesso")
            return True
        else:
            logger.error("Falha ao remover diretório CLOVER")

            # Desmontar a partição EFI se foi montada temporariamente
            if temp_drive_created:
                unmount_efi_partition(efi_drive_letter)

            return False
    except Exception as e:
        logger.error(f"Erro ao desinstalar o Clover: {e}")

        # Desmontar a partição EFI se foi montada temporariamente
        if temp_drive_created:
            unmount_efi_partition(efi_drive_letter)

        return False

if __name__ == "__main__":
    # Configuração básica de logging para testes
    logging.basicConfig(level=logging.INFO)

    # Teste das funções
    print("Testando módulo de instalação do Clover...")

    # Verificar pré-requisitos
    print("\nVerificando pré-requisitos:")
    prereq_result = check_prerequisites()

    print(f"Pré-requisitos atendidos: {prereq_result['success']}")
    print(f"  Windows: {prereq_result['is_windows']}")
    print(f"  Administrador: {prereq_result['is_admin']}")
    print(f"  UEFI: {prereq_result['is_uefi']}")
    print(f"  Partição EFI: {prereq_result['efi_partition_found']}")
    print(f"  Espaço suficiente: {prereq_result['efi_space_sufficient']}")
    print(f"  Arquivo ZIP do Clover: {prereq_result['clover_zip_found']}")

    if prereq_result["issues"]:
        print("\nProblemas encontrados:")
        for issue in prereq_result["issues"]:
            print(f"  - {issue}")

    # Perguntar se deseja instalar o Clover
    if prereq_result["success"]:
        response = input("\nDeseja instalar o Clover Boot Manager? (S/N): ")

        if response.strip().upper() == "S":
            print("\nInstalando Clover Boot Manager...")
            install_result = install_clover()

            if install_result:
                print("Instalação do Clover Boot Manager concluída com sucesso!")
            else:
                print("Falha na instalação do Clover Boot Manager.")
        else:
            print("Instalação cancelada pelo usuário.")
