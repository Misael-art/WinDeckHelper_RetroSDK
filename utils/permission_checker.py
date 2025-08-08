#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo para verificação de permissões.

Este módulo fornece funções para verificar se o usuário tem permissões
adequadas para realizar operações como instalação de software e modificação
de arquivos do sistema.
"""

import os
import sys
import logging
import platform
import subprocess
import ctypes
from pathlib import Path
from typing import Dict, Tuple, Optional, Union, List

# Configurar logger
logger = logging.getLogger(__name__)

def is_admin() -> bool:
    """
    Verifica se o script está sendo executado com privilégios de administrador.
    
    Returns:
        bool: True se o script está sendo executado como administrador, False caso contrário.
    """
    try:
        if platform.system() == "Windows":
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        else:
            # No Unix, verifica se o UID é 0 (root)
            return os.geteuid() == 0
    except Exception as e:
        logger.error(f"Erro ao verificar privilégios de administrador: {e}")
        return False

def check_write_permission(path: str) -> Tuple[bool, str]:
    """
    Verifica se o usuário tem permissão de escrita no caminho especificado.
    
    Args:
        path: Caminho para verificar a permissão de escrita.
        
    Returns:
        Tuple[bool, str]: Tupla contendo um booleano indicando se o usuário tem permissão
                         e uma mensagem descritiva.
    """
    try:
        # Normaliza o caminho
        path = os.path.abspath(path)
        
        # Se o caminho não existe, verifica o diretório pai
        if not os.path.exists(path):
            parent_dir = os.path.dirname(path)
            if not os.path.exists(parent_dir):
                os.makedirs(parent_dir, exist_ok=True)
            path = parent_dir
        
        # Verifica se é um diretório
        if os.path.isdir(path):
            # Tenta criar um arquivo temporário no diretório
            test_file = os.path.join(path, f"write_test_{os.getpid()}.tmp")
            try:
                with open(test_file, "w") as f:
                    f.write("test")
                os.remove(test_file)
                return True, f"Permissão de escrita verificada em '{path}'"
            except (IOError, PermissionError) as e:
                return False, f"Sem permissão de escrita em '{path}': {e}"
        else:
            # Tenta abrir o arquivo para escrita
            try:
                with open(path, "a") as f:
                    # Testa escrita sem modificar o arquivo
                    f.flush()
                return True, f"Permissão de escrita verificada em '{path}'"
            except (IOError, PermissionError) as e:
                return False, f"Sem permissão de escrita em '{path}': {e}"
    except Exception as e:
        logger.error(f"Erro ao verificar permissão de escrita em '{path}': {e}")
        return False, f"Erro ao verificar permissão de escrita: {e}"

def check_read_permission(path: str) -> Tuple[bool, str]:
    """
    Verifica se o usuário tem permissão de leitura no caminho especificado.
    
    Args:
        path: Caminho para verificar a permissão de leitura.
        
    Returns:
        Tuple[bool, str]: Tupla contendo um booleano indicando se o usuário tem permissão
                         e uma mensagem descritiva.
    """
    try:
        # Normaliza o caminho
        path = os.path.abspath(path)
        
        # Verifica se o caminho existe
        if not os.path.exists(path):
            return False, f"Caminho '{path}' não existe"
        
        # Verifica se é um diretório
        if os.path.isdir(path):
            # Tenta listar o conteúdo do diretório
            try:
                os.listdir(path)
                return True, f"Permissão de leitura verificada em '{path}'"
            except (IOError, PermissionError) as e:
                return False, f"Sem permissão de leitura em '{path}': {e}"
        else:
            # Tenta abrir o arquivo para leitura
            try:
                with open(path, "r") as f:
                    f.read(1)  # Lê apenas o primeiro byte
                return True, f"Permissão de leitura verificada em '{path}'"
            except (IOError, PermissionError) as e:
                return False, f"Sem permissão de leitura em '{path}': {e}"
    except Exception as e:
        logger.error(f"Erro ao verificar permissão de leitura em '{path}': {e}")
        return False, f"Erro ao verificar permissão de leitura: {e}"

def check_execute_permission(path: str) -> Tuple[bool, str]:
    """
    Verifica se o usuário tem permissão de execução no caminho especificado.
    
    Args:
        path: Caminho para verificar a permissão de execução.
        
    Returns:
        Tuple[bool, str]: Tupla contendo um booleano indicando se o usuário tem permissão
                         e uma mensagem descritiva.
    """
    try:
        # Normaliza o caminho
        path = os.path.abspath(path)
        
        # Verifica se o caminho existe
        if not os.path.exists(path):
            return False, f"Caminho '{path}' não existe"
        
        # Verifica se é um diretório
        if os.path.isdir(path):
            # No Windows, não há permissão de execução para diretórios
            if platform.system() == "Windows":
                return True, f"Permissão de execução não se aplica a diretórios no Windows"
            else:
                # No Unix, verifica se o diretório tem permissão de execução
                return os.access(path, os.X_OK), f"Permissão de execução {'verificada' if os.access(path, os.X_OK) else 'não verificada'} em '{path}'"
        else:
            # Verifica se o arquivo tem permissão de execução
            if platform.system() == "Windows":
                # No Windows, verifica a extensão do arquivo
                _, ext = os.path.splitext(path)
                if ext.lower() in [".exe", ".bat", ".cmd", ".ps1"]:
                    return True, f"Arquivo '{path}' tem extensão executável"
                else:
                    return False, f"Arquivo '{path}' não tem extensão executável"
            else:
                # No Unix, verifica se o arquivo tem permissão de execução
                return os.access(path, os.X_OK), f"Permissão de execução {'verificada' if os.access(path, os.X_OK) else 'não verificada'} em '{path}'"
    except Exception as e:
        logger.error(f"Erro ao verificar permissão de execução em '{path}': {e}")
        return False, f"Erro ao verificar permissão de execução: {e}"

def check_admin_requirement(path: str) -> Tuple[bool, str]:
    """
    Verifica se o caminho especificado requer privilégios de administrador para acesso.
    
    Args:
        path: Caminho para verificar a necessidade de privilégios de administrador.
        
    Returns:
        Tuple[bool, str]: Tupla contendo um booleano indicando se o caminho requer privilégios
                         e uma mensagem descritiva.
    """
    try:
        # Normaliza o caminho
        path = os.path.abspath(path)
        
        # Verifica se o caminho existe
        if not os.path.exists(path):
            parent_dir = os.path.dirname(path)
            if not os.path.exists(parent_dir):
                return True, f"Caminho '{path}' não existe, mas pode requerer privilégios de administrador"
            path = parent_dir
        
        # Diretórios que geralmente requerem privilégios de administrador
        admin_paths = [
            "C:\\Program Files",
            "C:\\Program Files (x86)",
            "C:\\Windows",
            "C:\\Windows\\System32",
            "/usr/bin",
            "/usr/sbin",
            "/usr/local/bin",
            "/usr/local/sbin",
            "/etc",
            "/var"
        ]
        
        # Verifica se o caminho está em um diretório que requer privilégios
        for admin_path in admin_paths:
            if path.startswith(admin_path):
                return True, f"Caminho '{path}' está em um diretório que geralmente requer privilégios de administrador"
        
        # Verifica permissões de escrita
        has_write, _ = check_write_permission(path)
        if not has_write:
            # Se não tem permissão de escrita, provavelmente precisa de privilégios
            return True, f"Caminho '{path}' requer privilégios de administrador para escrita"
        
        return False, f"Caminho '{path}' não parece requerer privilégios de administrador"
    except Exception as e:
        logger.error(f"Erro ao verificar necessidade de privilégios de administrador em '{path}': {e}")
        return True, f"Erro ao verificar necessidade de privilégios de administrador: {e}"

def check_efi_partition_access() -> Tuple[bool, str]:
    """
    Verifica se o usuário tem acesso à partição EFI.
    
    Returns:
        Tuple[bool, str]: Tupla contendo um booleano indicando se o usuário tem acesso
                         e uma mensagem descritiva.
    """
    try:
        if platform.system() != "Windows":
            return False, "Verificação de acesso à partição EFI só é suportada no Windows"
        
        # Tenta encontrar a partição EFI
        ps_command = """
        $disks = Get-Disk | Where-Object {$_.PartitionStyle -eq "GPT"}
        foreach ($disk in $disks) {
            $efiPartitions = $disk | Get-Partition | Where-Object {$_.GptType -eq "{c12a7328-f81f-11d2-ba4b-00a0c93ec93b}"}
            if ($efiPartitions) {
                try {
                    $efiVolume = $efiPartitions[0] | Get-Volume -ErrorAction SilentlyContinue
                    if ($efiVolume) {
                        Write-Output "$($efiVolume.DriveLetter),$($efiVolume.FileSystemLabel),$($efiVolume.FileSystem)"
                        exit 0
                    }
                } catch {}
            }
        }
        Write-Output "NOT_FOUND"
        """
        
        result = subprocess.run(
            ["powershell", "-Command", ps_command],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0 and result.stdout.strip() != "NOT_FOUND":
            parts = result.stdout.strip().split(",")
            if len(parts) >= 1:
                drive_letter = parts[0]
                
                # Verifica se a partição EFI está acessível
                efi_path = f"{drive_letter}:\\EFI"
                if os.path.exists(efi_path):
                    # Verifica permissões de escrita
                    has_write, write_message = check_write_permission(efi_path)
                    if has_write:
                        return True, f"Partição EFI encontrada em {drive_letter}: e está acessível para escrita"
                    else:
                        return False, f"Partição EFI encontrada em {drive_letter}: mas não está acessível para escrita: {write_message}"
                else:
                    return False, f"Partição EFI encontrada em {drive_letter}: mas o diretório EFI não existe ou não está acessível"
            else:
                return False, "Partição EFI encontrada, mas não foi possível obter a letra da unidade"
        else:
            return False, "Partição EFI não encontrada ou não acessível"
    except Exception as e:
        logger.error(f"Erro ao verificar acesso à partição EFI: {e}")
        return False, f"Erro ao verificar acesso à partição EFI: {e}"

def check_permissions_for_installation(install_path: str) -> Dict[str, Union[bool, str]]:
    """
    Verifica todas as permissões necessárias para instalação em um caminho.
    
    Args:
        install_path: Caminho onde a instalação será realizada.
        
    Returns:
        Dict[str, Union[bool, str]]: Dicionário com os resultados das verificações.
    """
    results = {
        "is_admin": is_admin(),
        "requires_admin": False,
        "write_permission": False,
        "read_permission": False,
        "execute_permission": False,
        "efi_access": False,
        "messages": [],
        "success": False
    }
    
    # Verifica se o caminho requer privilégios de administrador
    requires_admin, admin_message = check_admin_requirement(install_path)
    results["requires_admin"] = requires_admin
    results["messages"].append(admin_message)
    
    # Verifica permissões de escrita
    has_write, write_message = check_write_permission(install_path)
    results["write_permission"] = has_write
    results["messages"].append(write_message)
    
    # Verifica permissões de leitura
    has_read, read_message = check_read_permission(os.path.dirname(install_path))
    results["read_permission"] = has_read
    results["messages"].append(read_message)
    
    # Verifica permissões de execução
    has_execute, execute_message = check_execute_permission(os.path.dirname(install_path))
    results["execute_permission"] = has_execute
    results["messages"].append(execute_message)
    
    # Verifica acesso à partição EFI se necessário
    if "EFI" in install_path or "efi" in install_path.lower():
        has_efi_access, efi_message = check_efi_partition_access()
        results["efi_access"] = has_efi_access
        results["messages"].append(efi_message)
    
    # Determina o sucesso geral
    if requires_admin and not results["is_admin"]:
        results["success"] = False
        results["messages"].append("A instalação requer privilégios de administrador, mas o script não está sendo executado como administrador.")
    elif not has_write:
        results["success"] = False
        results["messages"].append("A instalação requer permissão de escrita, mas o usuário não tem essa permissão.")
    else:
        results["success"] = True
    
    return results

def suggest_permission_actions(results: Dict[str, Union[bool, str]]) -> str:
    """
    Sugere ações para resolver problemas de permissão.
    
    Args:
        results: Resultados das verificações de permissão.
        
    Returns:
        str: Mensagem com sugestões para resolver problemas de permissão.
    """
    suggestions = ["Sugestões para resolver problemas de permissão:"]
    
    if results.get("requires_admin", False) and not results.get("is_admin", False):
        suggestions.append("1. Execute o script como administrador (clique com o botão direito e selecione 'Executar como administrador')")
    
    if not results.get("write_permission", False):
        suggestions.append("2. Verifique se você tem permissão de escrita no diretório de instalação")
        suggestions.append("   - Tente instalar em um diretório diferente")
        suggestions.append("   - Verifique as permissões do diretório")
    
    if not results.get("efi_access", False) and any(m for m in results.get("messages", []) if "EFI" in m or "efi" in m):
        suggestions.append("3. Verifique se você tem acesso à partição EFI")
        suggestions.append("   - Execute o script como administrador")
        suggestions.append("   - Verifique se a partição EFI está montada")
        suggestions.append("   - Verifique se o sistema está em modo UEFI")
    
    if len(suggestions) == 1:
        suggestions.append("Nenhuma sugestão disponível. Todos os requisitos de permissão parecem estar satisfeitos.")
    
    return "\n".join(suggestions)

if __name__ == "__main__":
    # Configuração básica de logging para testes
    logging.basicConfig(level=logging.INFO)
    
    # Teste das funções
    print("Testando módulo de verificação de permissões...")
    
    # Verifica se o script está sendo executado como administrador
    print(f"Executando como administrador: {is_admin()}")
    
    # Verifica permissões em alguns diretórios
    test_paths = [
        os.path.expanduser("~"),
        "C:\\Program Files",
        "C:\\Windows",
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_dir")
    ]
    
    for path in test_paths:
        print(f"\nVerificando permissões em '{path}':")
        
        has_write, write_message = check_write_permission(path)
        print(f"  Permissão de escrita: {has_write} - {write_message}")
        
        has_read, read_message = check_read_permission(path)
        print(f"  Permissão de leitura: {has_read} - {read_message}")
        
        has_execute, execute_message = check_execute_permission(path)
        print(f"  Permissão de execução: {has_execute} - {execute_message}")
        
        requires_admin, admin_message = check_admin_requirement(path)
        print(f"  Requer administrador: {requires_admin} - {admin_message}")
    
    # Verifica acesso à partição EFI
    has_efi_access, efi_message = check_efi_partition_access()
    print(f"\nAcesso à partição EFI: {has_efi_access} - {efi_message}")
    
    # Verifica todas as permissões para instalação
    install_path = "C:\\Program Files\\TestApp"
    print(f"\nVerificando permissões para instalação em '{install_path}':")
    results = check_permissions_for_installation(install_path)
    
    print(f"  Sucesso: {results['success']}")
    print(f"  É administrador: {results['is_admin']}")
    print(f"  Requer administrador: {results['requires_admin']}")
    print(f"  Permissão de escrita: {results['write_permission']}")
    print(f"  Permissão de leitura: {results['read_permission']}")
    print(f"  Permissão de execução: {results['execute_permission']}")
    print(f"  Acesso à partição EFI: {results['efi_access']}")
    
    print("\nMensagens:")
    for message in results["messages"]:
        print(f"  - {message}")
    
    print("\nSugestões:")
    print(suggest_permission_actions(results))
