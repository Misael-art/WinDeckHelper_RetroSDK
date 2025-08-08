#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo para verificação de espaço em disco.

Este módulo fornece funções para verificar o espaço disponível em disco
e garantir que haja espaço suficiente para operações como downloads e instalações.
"""

import os
import shutil
import logging
import platform
import subprocess
from pathlib import Path
from typing import Dict, Tuple, Optional, Union

# Configurar logger
logger = logging.getLogger(__name__)

def get_disk_space(path: str) -> Dict[str, float]:
    """
    Obtém informações sobre o espaço em disco para o caminho especificado.
    
    Args:
        path: Caminho para verificar o espaço em disco.
        
    Returns:
        Dict[str, float]: Dicionário com informações sobre o espaço em disco (em bytes).
            - 'total': Espaço total
            - 'used': Espaço usado
            - 'free': Espaço livre
    """
    try:
        # Normaliza o caminho
        path = os.path.abspath(path)
        
        # Obtém informações sobre o espaço em disco
        total, used, free = shutil.disk_usage(path)
        
        return {
            'total': total,
            'used': used,
            'free': free
        }
    except Exception as e:
        logger.error(f"Erro ao obter informações sobre o espaço em disco para '{path}': {e}")
        # Retorna valores padrão em caso de erro
        return {
            'total': 0,
            'used': 0,
            'free': 0
        }

def format_size(size_bytes: float) -> str:
    """
    Formata um tamanho em bytes para uma string legível.
    
    Args:
        size_bytes: Tamanho em bytes.
        
    Returns:
        str: Tamanho formatado (ex: "1.23 GB").
    """
    # Define as unidades
    units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
    
    # Inicializa o índice da unidade
    unit_index = 0
    
    # Converte para a unidade apropriada
    while size_bytes >= 1024 and unit_index < len(units) - 1:
        size_bytes /= 1024
        unit_index += 1
    
    # Formata o resultado
    return f"{size_bytes:.2f} {units[unit_index]}"

def check_disk_space(path: str, required_space: float) -> Tuple[bool, str]:
    """
    Verifica se há espaço suficiente em disco para uma operação.
    
    Args:
        path: Caminho onde a operação será realizada.
        required_space: Espaço necessário em bytes.
        
    Returns:
        Tuple[bool, str]: Tupla contendo um booleano indicando se há espaço suficiente
                         e uma mensagem descritiva.
    """
    # Obtém informações sobre o espaço em disco
    disk_info = get_disk_space(path)
    
    # Verifica se há espaço suficiente
    has_space = disk_info['free'] >= required_space
    
    # Formata a mensagem
    if has_space:
        message = f"Espaço suficiente disponível: {format_size(disk_info['free'])} livre, {format_size(required_space)} necessário."
    else:
        message = f"Espaço insuficiente: {format_size(disk_info['free'])} livre, {format_size(required_space)} necessário."
    
    return has_space, message

def get_download_directory_space() -> Dict[str, float]:
    """
    Obtém informações sobre o espaço em disco no diretório de downloads.
    
    Returns:
        Dict[str, float]: Dicionário com informações sobre o espaço em disco (em bytes).
    """
    # Obtém o caminho para o diretório de downloads
    download_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "downloads"
    )
    
    # Cria o diretório se não existir
    os.makedirs(download_dir, exist_ok=True)
    
    # Retorna informações sobre o espaço em disco
    return get_disk_space(download_dir)

def ensure_space_for_download(file_size: float, download_path: Optional[str] = None) -> Tuple[bool, str]:
    """
    Verifica se há espaço suficiente para um download.
    
    Args:
        file_size: Tamanho do arquivo a ser baixado em bytes.
        download_path: Caminho onde o arquivo será baixado. Se None, usa o diretório de downloads padrão.
        
    Returns:
        Tuple[bool, str]: Tupla contendo um booleano indicando se há espaço suficiente
                         e uma mensagem descritiva.
    """
    # Se o caminho não for especificado, usa o diretório de downloads padrão
    if download_path is None:
        download_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "downloads"
        )
    
    # Adiciona 10% de margem para operações temporárias
    required_space = file_size * 1.1
    
    # Verifica se há espaço suficiente
    return check_disk_space(download_path, required_space)

def get_temp_directory_space() -> Dict[str, float]:
    """
    Obtém informações sobre o espaço em disco no diretório temporário.
    
    Returns:
        Dict[str, float]: Dicionário com informações sobre o espaço em disco (em bytes).
    """
    # Obtém o caminho para o diretório temporário
    temp_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "temp"
    )
    
    # Cria o diretório se não existir
    os.makedirs(temp_dir, exist_ok=True)
    
    # Retorna informações sobre o espaço em disco
    return get_disk_space(temp_dir)

def ensure_space_for_extraction(archive_size: float, extraction_path: Optional[str] = None) -> Tuple[bool, str]:
    """
    Verifica se há espaço suficiente para extrair um arquivo.
    
    Args:
        archive_size: Tamanho do arquivo compactado em bytes.
        extraction_path: Caminho onde o arquivo será extraído. Se None, usa o diretório temporário padrão.
        
    Returns:
        Tuple[bool, str]: Tupla contendo um booleano indicando se há espaço suficiente
                         e uma mensagem descritiva.
    """
    # Se o caminho não for especificado, usa o diretório temporário padrão
    if extraction_path is None:
        extraction_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "temp"
        )
    
    # Estima o tamanho descompactado (geralmente 2-5x o tamanho compactado)
    # Usamos 5x como uma estimativa conservadora
    required_space = archive_size * 5
    
    # Verifica se há espaço suficiente
    return check_disk_space(extraction_path, required_space)

def clean_temp_directory() -> Tuple[bool, str]:
    """
    Limpa o diretório temporário para liberar espaço.
    
    Returns:
        Tuple[bool, str]: Tupla contendo um booleano indicando se a operação foi bem-sucedida
                         e uma mensagem descritiva.
    """
    try:
        # Obtém o caminho para o diretório temporário
        temp_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "temp"
        )
        
        # Verifica se o diretório existe
        if not os.path.exists(temp_dir):
            return True, "Diretório temporário não existe."
        
        # Obtém o espaço usado antes da limpeza
        before_space = get_disk_space(temp_dir)
        
        # Remove todos os arquivos no diretório temporário
        for item in os.listdir(temp_dir):
            item_path = os.path.join(temp_dir, item)
            try:
                if os.path.isfile(item_path):
                    os.unlink(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)
            except Exception as e:
                logger.warning(f"Erro ao remover '{item_path}': {e}")
        
        # Obtém o espaço usado após a limpeza
        after_space = get_disk_space(temp_dir)
        
        # Calcula o espaço liberado
        space_freed = before_space['used'] - after_space['used']
        
        return True, f"Diretório temporário limpo. {format_size(space_freed)} liberados."
    except Exception as e:
        logger.error(f"Erro ao limpar diretório temporário: {e}")
        return False, f"Erro ao limpar diretório temporário: {e}"

def clean_downloads_directory(keep_days: int = 7) -> Tuple[bool, str]:
    """
    Limpa o diretório de downloads, removendo arquivos mais antigos que o número de dias especificado.
    
    Args:
        keep_days: Número de dias para manter os arquivos. Arquivos mais antigos serão removidos.
        
    Returns:
        Tuple[bool, str]: Tupla contendo um booleano indicando se a operação foi bem-sucedida
                         e uma mensagem descritiva.
    """
    try:
        # Obtém o caminho para o diretório de downloads
        download_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "downloads"
        )
        
        # Verifica se o diretório existe
        if not os.path.exists(download_dir):
            return True, "Diretório de downloads não existe."
        
        # Obtém o espaço usado antes da limpeza
        before_space = get_disk_space(download_dir)
        
        # Obtém a data atual
        import time
        current_time = time.time()
        
        # Remove arquivos mais antigos que o número de dias especificado
        files_removed = 0
        for item in os.listdir(download_dir):
            item_path = os.path.join(download_dir, item)
            try:
                if os.path.isfile(item_path):
                    # Obtém a data de modificação do arquivo
                    file_time = os.path.getmtime(item_path)
                    
                    # Verifica se o arquivo é mais antigo que o número de dias especificado
                    if current_time - file_time > keep_days * 86400:  # 86400 segundos = 1 dia
                        os.unlink(item_path)
                        files_removed += 1
            except Exception as e:
                logger.warning(f"Erro ao remover '{item_path}': {e}")
        
        # Obtém o espaço usado após a limpeza
        after_space = get_disk_space(download_dir)
        
        # Calcula o espaço liberado
        space_freed = before_space['used'] - after_space['used']
        
        return True, f"Diretório de downloads limpo. {files_removed} arquivos removidos. {format_size(space_freed)} liberados."
    except Exception as e:
        logger.error(f"Erro ao limpar diretório de downloads: {e}")
        return False, f"Erro ao limpar diretório de downloads: {e}"

def get_system_drives() -> Dict[str, Dict[str, float]]:
    """
    Obtém informações sobre todas as unidades do sistema.
    
    Returns:
        Dict[str, Dict[str, float]]: Dicionário com informações sobre o espaço em disco para cada unidade.
    """
    drives = {}
    
    try:
        if platform.system() == "Windows":
            # No Windows, usa o comando wmic para listar as unidades
            result = subprocess.run(
                ["wmic", "logicaldisk", "get", "deviceid,freespace,size"],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")[1:]
                for line in lines:
                    parts = line.strip().split()
                    if len(parts) >= 3:
                        drive = parts[0].replace(":", "")
                        try:
                            free = float(parts[1])
                            total = float(parts[2])
                            used = total - free
                            
                            drives[drive] = {
                                'total': total,
                                'used': used,
                                'free': free
                            }
                        except (ValueError, IndexError) as e:
                            logger.debug(f"Erro ao analisar saída do comando para unidade {drive}: {e}")
                            continue
        else:
            # Em outros sistemas, usa o comando df
            result = subprocess.run(
                ["df", "-k"],
                capture_output=True,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")[1:]
                for line in lines:
                    parts = line.strip().split()
                    if len(parts) >= 6:
                        drive = parts[5]
                        try:
                            total = float(parts[1]) * 1024  # Converte de KB para bytes
                            used = float(parts[2]) * 1024
                            free = float(parts[3]) * 1024
                            
                            drives[drive] = {
                                'total': total,
                                'used': used,
                                'free': free
                            }
                        except (ValueError, IndexError) as e:
                            logger.debug(f"Erro ao analisar saída do comando para unidade {drive}: {e}")
                            continue
    except Exception as e:
        logger.error(f"Erro ao obter informações sobre as unidades do sistema: {e}")
    
    return drives

def suggest_cleanup_actions(required_space: float) -> str:
    """
    Sugere ações para liberar espaço em disco.
    
    Args:
        required_space: Espaço necessário em bytes.
        
    Returns:
        str: Mensagem com sugestões para liberar espaço.
    """
    suggestions = [
        f"Espaço necessário: {format_size(required_space)}",
        "Sugestões para liberar espaço em disco:",
        "1. Execute a limpeza automática de arquivos temporários (Ferramentas > Limpar Arquivos Temporários)",
        "2. Remova downloads antigos (Ferramentas > Limpar Downloads)",
        "3. Use a ferramenta de limpeza de disco do Windows (cleanmgr.exe)",
        "4. Desinstale programas não utilizados",
        "5. Mova arquivos grandes para outro disco",
        "6. Esvazie a Lixeira"
    ]
    
    return "\n".join(suggestions)

if __name__ == "__main__":
    # Configuração básica de logging para testes
    logging.basicConfig(level=logging.INFO)
    
    # Teste das funções
    print("Testando módulo de verificação de espaço em disco...")
    
    # Obtém informações sobre o espaço em disco no diretório atual
    disk_info = get_disk_space(".")
    print(f"Espaço total: {format_size(disk_info['total'])}")
    print(f"Espaço usado: {format_size(disk_info['used'])}")
    print(f"Espaço livre: {format_size(disk_info['free'])}")
    
    # Verifica se há espaço suficiente para um download de 1 GB
    has_space, message = ensure_space_for_download(1024 * 1024 * 1024)
    print(f"Espaço para download: {message}")
    
    # Verifica se há espaço suficiente para extrair um arquivo de 1 GB
    has_space, message = ensure_space_for_extraction(1024 * 1024 * 1024)
    print(f"Espaço para extração: {message}")
    
    # Obtém informações sobre todas as unidades do sistema
    drives = get_system_drives()
    print("\nInformações sobre as unidades do sistema:")
    for drive, info in drives.items():
        print(f"Unidade {drive}:")
        print(f"  Espaço total: {format_size(info['total'])}")
        print(f"  Espaço usado: {format_size(info['used'])}")
        print(f"  Espaço livre: {format_size(info['free'])}")
    
    # Sugere ações para liberar espaço
    print("\nSugestões para liberar espaço:")
    print(suggest_cleanup_actions(1024 * 1024 * 1024 * 10))  # 10 GB
