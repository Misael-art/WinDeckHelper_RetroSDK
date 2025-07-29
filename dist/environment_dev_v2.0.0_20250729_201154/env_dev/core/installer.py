#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo installer do Environment Dev

Este módulo contém as funções relacionadas à instalação de componentes.
"""

import logging
import os
import shutil
import subprocess
import time
import sys
import re
import traceback
from urllib.parse import urlparse
from typing import Dict, List, Any, Optional, Set, Tuple, Callable
import json
import platform
import zipfile
import tarfile
import glob
import requests
import threading
from pathlib import Path
import queue

# Importa os módulos utilitários
from env_dev.utils import downloader, extractor, installer_runner, env_manager, hash_utils
from env_dev.utils import env_checker # Importa o novo módulo de verificação
from env_dev.utils import disk_space, permission_checker # Importa os novos módulos

# Importa o sistema de gestão de erros
from env_dev.utils.error_handler import (
    EnvDevError, ErrorCategory, ErrorSeverity,
    handle_exception, installation_error, dependency_error,
    file_error, network_error, permission_error
)

# Importa o Rollback Manager
from env_dev.core.rollback_manager import RollbackManager

# Define um diretório base para downloads
# Timeout padrão para ações de script em segundos (ex: 15 minutos)
DEFAULT_SCRIPT_TIMEOUT = 900
DOWNLOAD_DIR = os.path.join(os.path.expanduser("~"), "Downloads", "Environment_Dev")
TEMP_DIR = os.path.join(os.environ.get('TEMP', os.environ.get('TMP', '/tmp')), 'env_dev_temp')
# Certifica-se de que o diretório temporário existe
os.makedirs(TEMP_DIR, exist_ok=True)
MAX_INSTALL_RETRIES = 2  # Número máximo de tentativas de instalação em caso de falha

# Fila de status global para comunicação com a GUI
status_queue = queue.Queue()

# Importa o sistema de log
from env_dev.utils.log_manager import setup_logging, INSTALLATION, ROLLBACK, VERIFICATION, SUCCESS

# Logger principal
logger, log_manager = setup_logging()

# Configura o formato detalhado para o console
log_manager.use_detailed_console_format(True)

def send_status_update(component_name, status=None, message="", status_queue=None, **kwargs):
    """
    Envia uma atualização de status formatada para a GUI.
    
    Args:
        component_name (str ou dict): Nome do componente sendo instalado/configurado, 
                                     ou payload estruturado completo
        status (str, opcional): Status da operação ("SUCCESS", "FAILED", "PROGRESS", etc.)
        message (str, opcional): Mensagem detalhando o status
        status_queue (Queue, opcional): Fila para enviar mensagens de status. 
                                       Se não fornecida, usa a fila global
        **kwargs: Parâmetros adicionais para formatos específicos:
            - percent (float): Porcentagem de progresso (0-100) para status "PROGRESS"
            - stage (str): Nome do estágio atual para status "PROGRESS"
    
    Este método cria uma mensagem estruturada (dicionário) com a seguinte estrutura:
    
    Para atualização de estágio:
    {
        'type': 'stage',
        'component': 'nome_do_componente',
        'stage': 'nome_do_estágio'
    }
    
    Para progresso:
    {
        'type': 'progress',
        'component': 'nome_do_componente',
        'percent': 35.5
    }
    
    Para resultado:
    {
        'type': 'result',
        'component': 'nome_do_componente',
        'status': 'SUCCESS/FAILED/etc',
        'message': 'mensagem detalhada'
    }
    """
    try:
        # Suporte para payload completo (formato novo)
        if isinstance(component_name, dict) and 'type' in component_name:
            payload = component_name.copy()
            # Verifica se a timestamp já existe
            if 'timestamp' not in payload:
                payload['timestamp'] = time.time()
            
            # Usa a fila específica se fornecida, caso contrário usa a global
            target_queue = status_queue if status_queue is not None else globals().get('status_queue')
            
            if target_queue is None:
                logging.debug(f"Nenhuma fila de status disponível para enviar payload do tipo '{payload.get('type')}'")
                return
                
            _send_structured_status_update(target_queue, payload)
            return
            
        # Se chegamos aqui, é o formato antigo (compatibilidade)
        # Usa a fila específica se fornecida, caso contrário usa a global
        target_queue = status_queue if status_queue is not None else globals().get('status_queue')
            
        if target_queue is None:
            logging.debug(f"Nenhuma fila de status disponível para '{component_name}'")
            return
            
        if status and status.upper() == "PROGRESS":
            # Caso especial: se temos um estágio, enviamos atualização de estágio
            if 'stage' in kwargs:
                _send_structured_status_update(
                    target_queue, 
                    {
                        'type': 'stage',
                        'component': component_name,
                        'stage': kwargs.get('stage', 'Unknown Stage'),
                        'timestamp': time.time()
                    }
                )
            
            # Se temos uma porcentagem, enviamos atualização de progresso
            if 'percent' in kwargs:
                _send_structured_status_update(
                    target_queue,
                    {
                        'type': 'progress',
                        'component': component_name,
                        'percent': kwargs.get('percent', 0.0),
                        'timestamp': time.time()
                    }
                )
                
        else:  # SUCCESS, FAILED, WARNING, etc.
            # Envio de resultado final
            _send_structured_status_update(
                target_queue,
                {
                    'type': 'result',
                    'component': component_name,
                    'status': status.upper() if status else 'UNKNOWN',
                    'message': message,
                    'timestamp': time.time()
                }
            )
    except Exception as e:
        logging.error(f"Erro ao enviar atualização de status: {e}")


def _send_structured_status_update(queue, payload):
    """
    Envia uma atualização de status estruturada via fila.
    
    Args:
        queue (Queue): A fila para enviar o payload
        payload (dict): O payload estruturado a ser enviado
        
    Raises:
        Exception: Se houver erros ao enfileirar
    """
    try:
        queue.put_nowait(payload)
    except Exception as e:
        logging.error(f"Erro ao enfileirar status estruturado: {e}")
        raise

def calculate_progress(current, total):
    """Calcula a porcentagem de progresso."""
    if total == 0:
        return 0
    return int((current / total) * 100)

# --- Funções Auxiliares de Utilidade ---

def expand_env_vars(path):
    """Expande variáveis de ambiente no formato ${env:NOME_VAR}."""
    if not path or '${env:' not in path:
        return path
    env_vars = re.findall(r'\${env:([^}]+)}', path)
    result = path
    for var in env_vars:
        if var in os.environ:
            result = result.replace(f'${{env:{var}}}', os.environ[var])
            logging.debug(f"Variável de ambiente expandida: ${{env:{var}}} -> {os.environ[var]}")
        else:
            logging.warning(f"Variável de ambiente '{var}' não encontrada")
    return result

def clean_download_file(download_path: str, reason: str = "cleanup") -> bool:
    """Tenta remover um arquivo de download, com tratamento de erro adequado."""
    if not download_path or not os.path.exists(download_path):
        return True

    try:
        os.remove(download_path)
        logging.info(f"Arquivo '{download_path}' removido ({reason}).")
        return True
    except OSError as e:
        err = file_error(
            f"Falha ao remover arquivo '{download_path}': {e}",
            file_path=download_path,
            severity=ErrorSeverity.WARNING
        )
        err.log()
        return False

def handle_extraction_cleanup(extract_path: str, component_name: str) -> bool:
    """
    Tenta limpar um diretório de extração falho.
    (Esta função pode se tornar obsoleta ou menos necessária com o RollbackManager)
    """
    if not os.path.isdir(extract_path):
        return True

    try:
        logging.info(f"Tentando limpar diretório de extração falho: {extract_path}")
        shutil.rmtree(extract_path)
        logging.info(f"Diretório de extração '{extract_path}' removido após falha em '{component_name}'.")
        return True
    except OSError as e:
        err = file_error(
            f"Erro ao remover diretório de extração '{extract_path}' após falha: {e}",
            file_path=extract_path,
            severity=ErrorSeverity.WARNING
        )
        err.log()
        return False

# --- Funções de Instalação por Método ---

def _install_archive(component_name, component_data, download_path, rollback_mgr: RollbackManager):
    """Instala um componente a partir de um arquivo compactado."""
    extract_path = component_data.get('extract_path')
    if not extract_path:
        err = installation_error(f"Caminho de extração ('extract_path') não definido para '{component_name}'.", component=component_name, severity=ErrorSeverity.ERROR)
        err.log()
        return False

    if not download_path:
        err = installation_error(f"Download necessário para extração de '{component_name}', mas falhou ou foi pulado.", component=component_name, severity=ErrorSeverity.ERROR)
        err.log()
        return False

    extract_path = expand_env_vars(extract_path)
    logger.info(f"Extraindo {component_name} para {extract_path}...")
    send_status_update({'type': 'stage', 'component': component_name, 'stage': 'Extracting'})

    if not extractor.is_7zip_available():
        err = dependency_error("7-Zip não encontrado. Não é possível extrair o arquivo.", dependency="7zip", severity=ErrorSeverity.ERROR)
        err.log()
        return False

    # Registra ação de rollback ANTES da extração
    # Registra ação de rollback ANTES da extração
    rollback_mgr.register_action({
        'undo_action': 'delete_path',
        'parameters': {'path': extract_path},
        'step': 'Extracting Archive'
    })

    rollback_mgr.register_action({
        'undo_action': 'delete_path',
        'parameters': {'path': extract_path},
        'step': 'Extracting Archive'
    })

    success = extractor.extract_archive(
        archive_path=download_path,
        destination_path=extract_path,
        extract_subdir=component_data.get('extract_subdir')
    )
    if not success:
        err = installation_error(f"Falha ao extrair {component_name} para {extract_path}.", component=component_name, severity=ErrorSeverity.ERROR)
        err.log()
        return False # Indica falha para acionar rollback

    return success

def _install_executable(component_name, component_data, download_path, rollback_mgr: RollbackManager):
    """Instala um componente a partir de um instalador .exe ou .msi."""
    install_args = component_data.get('install_args')
    timeout = int(component_data.get('timeout', installer_runner.DEFAULT_INSTALLER_TIMEOUT))
    uninstall_command = component_data.get('uninstall_command')
    uninstall_args = component_data.get('uninstall_args', [])

    if not download_path:
        err = installation_error(f"Download necessário para instalação de '{component_name}', mas falhou ou foi pulado.", component=component_name, severity=ErrorSeverity.ERROR)
        err.log()
        return False

    # Registra ação de rollback ANTES da execução (se comando de undo for conhecido)
    if uninstall_command:
        rollback_mgr.register_action({
            'undo_action': 'run_command',
            'parameters': {'command': [uninstall_command] + uninstall_args},
            'step': 'Running Installer'
        })
    else:
        # TODO: Implementar descoberta via registro após instalação bem-sucedida
        # ou registrar uma ação de undo genérica (ex: delete_guessed_path)
        logger.warning(f"Comando de desinstalação não definido para '{component_name}'. Rollback pode ser incompleto.")

    logger.info(f"Executando instalador {component_name} com timeout de {timeout}s...")
    send_status_update({'type': 'stage', 'component': component_name, 'stage': 'Running Installer'})

    # Registra ação de rollback ANTES da execução (se comando de undo for conhecido)
    if uninstall_command:
        rollback_mgr.register_action({
            'undo_action': 'run_command',
            'parameters': {'command': [uninstall_command] + uninstall_args},
            'step': 'Running Installer'
        })
    else:
        logger.warning(f"Comando de desinstalação não definido para '{component_name}'. Rollback pode ser incompleto.")

    for attempt in range(MAX_INSTALL_RETRIES):
        if attempt > 0:
            wait_time = 3 * (attempt + 1)
            logger.info(f"Tentativa {attempt+1}/{MAX_INSTALL_RETRIES} de instalação de {component_name} após {wait_time}s...")
            time.sleep(wait_time)

        try:
            success = installer_runner.run_installer(download_path, install_args, timeout=timeout)
            if success:
                # TODO: Se uninstall_command não foi definido, tentar descobrir via registro aqui?
                return True
            logger.warning(f"Tentativa {attempt+1}/{MAX_INSTALL_RETRIES} de instalação de {component_name} falhou, mas sem erro crítico.")
        except Exception as e:
            err = installation_error(f"Erro na tentativa {attempt+1}/{MAX_INSTALL_RETRIES} de instalação de {component_name}: {e}", component=component_name, severity=ErrorSeverity.WARNING, original_error=e)
            err.log()

    err = installation_error(f"Falha na instalação de {component_name} após {MAX_INSTALL_RETRIES} tentativas.", component=component_name, severity=ErrorSeverity.ERROR)
    err.log()
    return False # Indica falha para acionar rollback

def _install_pip(component_name, component_data, rollback_mgr: RollbackManager):
    """Instala um componente usando pip."""
    package_name = component_data.get('install_args')
    if not package_name:
        err = installation_error(f"'install_args' (nome do pacote pip) não definido para '{component_name}'.", component=component_name, severity=ErrorSeverity.ERROR)
        err.log()
        return False

    logger.info(f"Instalando pacote pip: {package_name}...")
    send_status_update({'type': 'stage', 'component': component_name, 'stage': 'Installing (pip)'})
    # Usamos aspas duplas em torno do caminho do Python para lidar com espaços
    python_path = sys.executable
    command = [python_path, "-m", "pip", "install", package_name]
    uninstall_command = [python_path, "-m", "pip", "uninstall", "-y", package_name]

    # Registra ação de rollback ANTES da instalação
    rollback_mgr.register_action({
        'undo_action': 'run_command',
        'parameters': {'command': uninstall_command},
        'step': 'Installing (pip)'
    })

    for attempt in range(MAX_INSTALL_RETRIES):
        if attempt > 0:
            wait_time = 2 * (attempt + 1)
            logger.info(f"Tentativa {attempt+1}/{MAX_INSTALL_RETRIES} de instalação pip de {package_name} após {wait_time}s...")
            time.sleep(wait_time)
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True, encoding='utf-8', errors='ignore')
            logger.info(f"Pacote pip '{package_name}' instalado com sucesso.")
            logger.debug(f"Saída do pip:\n{result.stdout}")
            return True
        except subprocess.CalledProcessError as e:
            err = installation_error(f"Erro ao instalar pacote pip '{package_name}' (Código: {e.returncode}).", component=component_name, severity=ErrorSeverity.WARNING if attempt < MAX_INSTALL_RETRIES - 1 else ErrorSeverity.ERROR, original_error=e, context={"stdout": e.stdout, "stderr": e.stderr})
            err.log()
            logger.error(f"Saída do pip (stdout):\n{e.stdout}")
            logger.error(f"Saída de erro do pip (stderr):\n{e.stderr}")
        except FileNotFoundError as e:
            err = dependency_error(f"Comando '{sys.executable}' ou 'pip' não encontrado para instalar '{package_name}'.", dependency="pip", severity=ErrorSeverity.ERROR, original_error=e)
            err.log()
            return False # Falha crítica, aciona rollback
        except Exception as e:
            err = handle_exception(e, message=f"Erro inesperado durante a instalação pip de '{package_name}'", category=ErrorCategory.INSTALLATION, severity=ErrorSeverity.ERROR)
            err.log()
            return False # Falha crítica, aciona rollback

    return False # Indica falha para acionar rollback

def _install_vcpkg(component_name, component_data, all_components_data, rollback_mgr: RollbackManager):
    """Instala um componente usando vcpkg."""
    package_name = component_data.get('install_args')
    if not package_name:
        err = installation_error(f"'install_args' (nome do pacote vcpkg) não definido para '{component_name}'.", component=component_name, severity=ErrorSeverity.ERROR)
        err.log()
        return False

    vcpkg_component_name = 'vcpkg'
    vcpkg_path = None
    vcpkg_base_path = None # Inicializa

    if vcpkg_component_name in all_components_data:
        vcpkg_base_path = all_components_data[vcpkg_component_name].get('extract_path')

        if vcpkg_base_path:
            vcpkg_base_path = expand_env_vars(vcpkg_base_path) # Expande vars aqui
            if os.path.isdir(vcpkg_base_path):
                potential_exe_path = os.path.join(vcpkg_base_path, 'vcpkg.exe')
                if os.path.isfile(potential_exe_path):
                    vcpkg_path = potential_exe_path

        if not vcpkg_path:
            err = dependency_error(f"Não foi possível encontrar vcpkg.exe no caminho definido: {vcpkg_base_path}", dependency="vcpkg", severity=ErrorSeverity.ERROR)
            err.log()
            return False
    else:
        err = dependency_error(f"Componente '{vcpkg_component_name}' não definido na configuração. Necessário para instalar '{component_name}'.", dependency="vcpkg", severity=ErrorSeverity.ERROR)
        err.log()
        return False

    logger.info(f"Instalando pacote vcpkg: {package_name}...")
    send_status_update({'type': 'stage', 'component': component_name, 'stage': 'Installing (vcpkg)'})
    command = [vcpkg_path, "install", package_name]
    uninstall_command = [vcpkg_path, "remove", package_name, "--recurse"]
    vcpkg_dir = os.path.dirname(vcpkg_path)

    # Registra ação de rollback ANTES da instalação
    rollback_mgr.register_action({
        'undo_action': 'run_command',
        'parameters': {'command': uninstall_command, 'cwd': vcpkg_dir},
        'step': 'Installing (vcpkg)'
    })

    for attempt in range(MAX_INSTALL_RETRIES):
        if attempt > 0:
            wait_time = 3 * (attempt + 1)
            logger.info(f"Tentativa {attempt+1}/{MAX_INSTALL_RETRIES} de instalação vcpkg de {package_name} após {wait_time}s...")
            time.sleep(wait_time)
        try:
            result = subprocess.run(command, cwd=vcpkg_dir, capture_output=True, text=True, check=True, encoding='utf-8', errors='ignore')
            logger.info(f"Pacote vcpkg '{package_name}' instalado com sucesso.")
            logger.debug(f"Saída do vcpkg:\n{result.stdout}")
            return True
        except subprocess.CalledProcessError as e:
            err = installation_error(f"Erro ao instalar pacote vcpkg '{package_name}' (Código: {e.returncode}).", component=component_name, severity=ErrorSeverity.WARNING if attempt < MAX_INSTALL_RETRIES - 1 else ErrorSeverity.ERROR, original_error=e, context={"stdout": e.stdout, "stderr": e.stderr})
            err.log()
            logger.error(f"Saída do vcpkg (stdout):\n{e.stdout}")
            logger.error(f"Saída de erro do vcpkg (stderr):\n{e.stderr}")
        except FileNotFoundError as e:
            err = dependency_error(f"Comando '{vcpkg_path}' não encontrado.", dependency="vcpkg", severity=ErrorSeverity.ERROR, original_error=e)
            err.log()
            return False # Falha crítica, aciona rollback
        except Exception as e:
            err = handle_exception(e, message=f"Erro inesperado durante a instalação vcpkg de '{package_name}'", category=ErrorCategory.INSTALLATION, severity=ErrorSeverity.ERROR)
            err.log()
            return False # Falha crítica, aciona rollback

    return False # Indica falha para acionar rollback

def _run_script_action(component_name, action, cwd, rollback_mgr: RollbackManager, timeout=DEFAULT_SCRIPT_TIMEOUT):
    """Executa uma única ação de script com timeout, incluindo nome do componente no log."""
    action_type = action.get('type')
    action_command_or_file = action.get('command')
    action_args = action.get('args', [])
    undo_script = action.get('undo_script') # Para rollback

    if not action_type or not action_command_or_file:
        err = installation_error(f"Ação de script inválida para '{component_name}': {action}", component=component_name, severity=ErrorSeverity.ERROR)
        err.log()
        return False

    processed_args = [expand_env_vars(str(arg)) for arg in action_args]
    action_args = processed_args

    logger.info(f"Executando ação de script '{action_type}' para '{component_name}': {action_command_or_file} {' '.join(action_args)}")
    send_status_update({'type': 'stage', 'component': component_name, 'stage': f'Running Script ({action_type})'})

    # Registra ação de rollback ANTES da execução (se script de undo for definido)
    if undo_script:
        # Assume que RollbackManager terá _undo_run_script
        rollback_mgr.register_action({
            'undo_action': 'run_script',
            'parameters': {'script_path': undo_script, 'cwd': cwd},
            'step': f'Running Script ({action_type})'
        })
    else:
        # Se for uma ação simples como criar diretório, podemos registrar undo 'delete_path'
        if action_type == 'powershell' and 'New-Item' in action_command_or_file and '-ItemType Directory' in action_command_or_file:
             # Extrai o caminho do comando (simplificação, pode precisar de regex mais robusto)
             match = re.search(r"-Path\s+'?([^']+)'?", action_command_or_file)
             if match:
                 dir_path = expand_env_vars(match.group(1))
                 rollback_mgr.register_action({
                     'undo_action': 'delete_path',
                     'parameters': {'path': dir_path},
                     'step': f'Creating Directory via Script ({action_type})'
                 })
             else:
                 logger.warning(f"Não foi possível extrair o caminho do diretório da ação New-Item para rollback.")
        else:
             logger.warning(f"Script de undo não definido para ação '{action_type}' de '{component_name}'. Rollback pode ser incompleto.")


    full_command = []
    shell_needed = False
    executable_path = None

    try:
        if action_type == 'powershell':
            if action_command_or_file.lower().endswith('.ps1'):
                script_file = os.path.join(cwd, action_command_or_file) if cwd else action_command_or_file
                if not os.path.isfile(script_file):
                    raise FileNotFoundError(f"Script PowerShell '{script_file}' não encontrado.")
                full_command = ['powershell.exe', '-ExecutionPolicy', 'Bypass', '-File', script_file] + action_args
            else:
                full_command = ['powershell.exe', '-ExecutionPolicy', 'Bypass', '-Command', action_command_or_file] + action_args
        elif action_type == 'batch':
            script_file = os.path.join(cwd, action_command_or_file) if cwd else action_command_or_file
            if not os.path.isfile(script_file):
                raise FileNotFoundError(f"Script Batch '{script_file}' não encontrado.")
            full_command = [script_file] + action_args
            shell_needed = False
        elif action_type == 'executable':
            potential_exe = os.path.join(cwd, action_command_or_file) if cwd else action_command_or_file
            if os.path.isfile(potential_exe):
                executable_path = potential_exe
            else:
                executable_path = shutil.which(action_command_or_file)
            if not executable_path:
                raise FileNotFoundError(f"Executável '{action_command_or_file}' não encontrado no diretório '{cwd}' ou no PATH.")
            full_command = [executable_path] + action_args
        else:
            err = installation_error(f"Tipo de ação de script desconhecido '{action_type}' para '{component_name}'.", component=component_name, severity=ErrorSeverity.ERROR)
            err.log()
            return False

        start_time = time.time()
        logger.info(f"Executando script com timeout de {timeout} segundos...")
        result = subprocess.run(full_command, cwd=cwd, capture_output=True, text=True, check=True, encoding='utf-8', errors='ignore', shell=shell_needed, timeout=timeout)
        end_time = time.time()
        logger.info(f"Ação de script concluída em {end_time - start_time:.2f} segundos.")
        logger.debug(f"Saída da ação:\n{result.stdout}")
        return True

    except subprocess.TimeoutExpired as e:
        err = installation_error(f"Timeout ({timeout}s) excedido durante a execução da ação de script: {' '.join(full_command)}", component=component_name, severity=ErrorSeverity.ERROR, original_error=e)
        err.log()
        return False # Indica falha para acionar rollback

    except subprocess.CalledProcessError as e:
        if action_type == 'batch' and not shell_needed:
             logger.warning(f"Falha ao executar script batch '{full_command[0]}' sem shell=True. Tentando com shell=True...")
             try:
                 start_time_shell = time.time()
                 result = subprocess.run(full_command, cwd=cwd, capture_output=True, text=True, check=True, encoding='utf-8', errors='ignore', shell=True, timeout=timeout)
                 end_time_shell = time.time()
                 logger.info(f"Ação de script batch (com shell=True) concluída em {end_time_shell - start_time_shell:.2f} segundos.")
                 logger.debug(f"Saída da ação (com shell=True):\n{result.stdout}")
                 return True
             except Exception as shell_e:
                 err = installation_error(f"Erro ao executar ação de script '{action_type}' para '{component_name}' (Código: {e.returncode}, Tentativa com shell=True também falhou: {shell_e}).", component=component_name, severity=ErrorSeverity.ERROR, original_error=e, context={"stdout": e.stdout, "stderr": e.stderr, "shell_error": str(shell_e)})
                 err.log()
                 logger.error(f"Saída da ação (stdout):\n{e.stdout}")
                 logger.error(f"Saída de erro da ação (stderr):\n{e.stderr}")
                 return False # Indica falha para acionar rollback
        else:
            err = installation_error(f"Erro ao executar ação de script '{action_type}' para '{component_name}' (Código: {e.returncode}).", component=component_name, severity=ErrorSeverity.ERROR, original_error=e, context={"stdout": e.stdout, "stderr": e.stderr})
            err.log()
            logger.error(f"Saída da ação (stdout):\n{e.stdout}")
            logger.error(f"Saída de erro da ação (stderr):\n{e.stderr}")
            return False # Indica falha para acionar rollback

    except FileNotFoundError as e:
        err = dependency_error(f"Comando ou script não encontrado para ação '{action_type}' de '{component_name}': {e}", dependency=action_command_or_file, severity=ErrorSeverity.ERROR, original_error=e)
        err.log()
        return False # Indica falha para acionar rollback

    except Exception as e:
        err = handle_exception(e, message=f"Erro inesperado durante execução da ação de script '{action_type}' para '{component_name}'", category=ErrorCategory.EXECUTION, severity=ErrorSeverity.ERROR)
        err.log()
        return False # Indica falha para acionar rollback

def _install_script(component_name, component_data, rollback_mgr: RollbackManager):
    """Instala um componente executando uma série de ações de script."""
    script_actions = component_data.get('script_actions', [])
    if not script_actions:
        logger.warning(f"Componente '{component_name}' definido como 'script', mas sem 'script_actions'.")
        return True

    cwd = component_data.get('extract_path')
    if cwd:
        cwd = expand_env_vars(cwd)
        if not os.path.isdir(cwd):
             logger.info(f"Criando diretório de trabalho/extração para script: {cwd}")
             try:
                 os.makedirs(cwd, exist_ok=True)
                 # Registra criação de diretório para rollback
                 rollback_mgr.register_action({
                     'undo_action': 'delete_path',
                     'parameters': {'path': cwd},
                     'step': 'Creating Script CWD'
                 })
             except OSError as e:
                 err = file_error(f"Não foi possível criar o diretório de trabalho '{cwd}' para o script de '{component_name}': {e}", file_path=cwd)
                 err.log()
                 return False # Falha crítica, aciona rollback
    else:
        cwd = os.getcwd()

    logger.info(f"Executando ações de script para {component_name} em {cwd}...")
    send_status_update({'type': 'stage', 'component': component_name, 'stage': 'Running Scripts'})

    for i, action in enumerate(script_actions):
        logger.info(f"Executando ação {i+1}/{len(script_actions)}...")
        timeout = int(action.get('timeout', DEFAULT_SCRIPT_TIMEOUT))
        # Passa o rollback_mgr para _run_script_action
        if not _run_script_action(component_name, action, cwd, rollback_mgr, timeout=timeout):
            logger.error(f"Falha na ação de script {i+1} para '{component_name}'. Abortando instalação do script.")
            return False # Indica falha para acionar rollback

    logger.info(f"Todas as ações de script para '{component_name}' concluídas com sucesso.")
    return True

# --- Funções de Configuração e Verificação ---

def _configure_environment(component_name, component_data, rollback_mgr: RollbackManager):
    """Aplica configurações de ambiente (variáveis, PATH) para um componente."""
    env_configs = component_data.get('environment', {})
    if not env_configs:
        return True # Nada a configurar

    logger.info(f"Configurando ambiente para {component_name}...")
    send_status_update({'type': 'stage', 'component': component_name, 'stage': 'Configuring Environment'})

    success = True
    for var_name, config in env_configs.items():
        var_value = config.get('value')
        var_scope = config.get('scope', 'user') # 'user' ou 'system'
        action_type = config.get('action', 'set') # 'set', 'append_path', 'remove_path'

        if var_value is None:
            logger.warning(f"Valor não definido para variável de ambiente '{var_name}' em '{component_name}'. Pulando.")
            continue

        # Expande variáveis no valor a ser definido/adicionado
        var_value = expand_env_vars(var_value)

        # Registra ação de rollback ANTES de modificar o ambiente
        try:
            original_value = env_manager.get_env_var(var_name, var_scope) # Obter valor atual para rollback
            undo_params = {'variable_name': var_name, 'scope': var_scope}
            undo_action = None

            if action_type == 'set':
                undo_params['original_value'] = original_value # Salva valor original
                # Se o valor original era None, o undo é unset, senão é restore
                undo_action = 'restore_env' if original_value is not None else 'unset_env'
            elif action_type == 'append_path':
                undo_action = 'remove_path'
                undo_params['path_to_remove'] = var_value # O valor a ser removido do PATH
            elif action_type == 'remove_path':
                # Rollback de 'remove_path' seria 'append_path', mais complexo
                logger.warning(f"Rollback para 'remove_path' não implementado ainda para '{var_name}'.")
                undo_action = None # Não registra rollback por enquanto

            if undo_action:
                rollback_mgr.register_action({
                    'undo_action': undo_action,
                    'parameters': undo_params,
                    'step': f'Configuring Env Var {var_name}'
                })
        except Exception as e:
             logger.error(f"Erro ao obter valor original da variável '{var_name}' para registrar rollback: {e}")
             # Continua mesmo assim? Ou considera falha? Por enquanto, continua.

        # Executa a ação de configuração
        try:
            if action_type == 'set':
                env_manager.set_env_var(var_name, var_value, var_scope)
            elif action_type == 'append_path':
                env_manager.add_to_path(var_value, var_scope)
            elif action_type == 'remove_path':
                env_manager.remove_from_path(var_value, var_scope)
            else:
                logger.error(f"Ação de ambiente desconhecida '{action_type}' para '{var_name}' em '{component_name}'.")
                success = False
        except Exception as e:
             err = handle_exception(e, f"Erro ao configurar variável de ambiente '{var_name}' para '{component_name}'", ErrorCategory.CONFIGURATION, ErrorSeverity.ERROR)
             err.log()
             success = False
             # Se falhar aqui, o rollback registrado anteriormente será executado
             # Retorna False para indicar falha na configuração
             return False # Falha na configuração deve acionar rollback da instalação

    return success

def _infer_check_patterns(component_name, component_data):
    """
    Gera verificações padrão baseada no tipo e dados de instalação.
    Esta função é usada quando o componente não tem 'verify_actions' definidas.
    """
    install_method = component_data.get('install_method')
    inferred_checks = []
    
    # Tentamos inferir verificações com base no método de instalação
    if install_method == 'archive' and 'extract_path' in component_data:
        extract_path = component_data.get('extract_path')
        extract_path = expand_env_vars(extract_path)
        inferred_checks.append({'type': 'directory_exists', 'path': extract_path})
        logger.verification(f"Inferindo verificação 'directory_exists' para '{component_name}': {extract_path}")
    
    elif install_method in ['exe', 'msi']:
        # Para instaladores, tentamos adivinhar o diretório de instalação típico
        install_args = component_data.get('install_args', [])
        binary_name = component_data.get('binary', component_name.lower())
        
        common_paths = []
        
        # Checa argumentos do instalador para possíveis paths
        for arg in install_args:
            if '/install' in arg or '/dir=' in arg or '/INSTALL' in arg:
                parts = arg.split('=')
                if len(parts) > 1:
                    path = parts[-1].strip('"')
                    common_paths.append(path)
        
        # Verifica caminhos comuns
        if platform.system() == 'Windows':
            common_paths.extend([
                f'C:\\Program Files\\{component_name}',
                f'C:\\Program Files (x86)\\{component_name}',
                f'C:\\Program Files\\{component_name.replace(" ", "")}',
                f'C:\\Program Files (x86)\\{component_name.replace(" ", "")}'
            ])
        
        for p in common_paths:
            inferred_checks.append({'type': 'directory_exists', 'path': p})
            logger.verification(f"Inferindo verificação heurística 'directory_exists' para '{component_name}': {p}")

    elif install_method == 'pip' and install_args:
        package_name = install_args.split()[0]
        inferred_checks.append({'type': 'command_output', 'command': f'{sys.executable} -m pip show {package_name}', 'expected_contains': f'Name: {package_name}'})
        logger.debug(f"Inferindo verificação 'pip show' para '{component_name}': {package_name}")

    if inferred_checks:
        logger.info(f"Nenhuma 'verify_actions' definida para '{component_name}'. Usando verificações inferidas: {inferred_checks}")
        return inferred_checks
    else:
        logger.warning(f"Nenhuma 'verify_actions' definida para '{component_name}' e nenhuma verificação pôde ser inferida.")
        return []

def _verify_installation(component_name, component_data):
    """
    Verifica se um componente foi instalado corretamente com base nas 'verify_actions'.

    Args:
        component_name: Nome do componente.
        component_data: Dicionário de dados do componente.

    Returns:
        bool: True se todas as verificações passarem, False caso contrário
    """
    logger.info(f"Verificando instalação de '{component_name}'...")

    # Caso especial para o Clover Boot Manager
    if component_name == "CloverBootManager":
        try:
            from env_dev.utils.clover_verification import verify_clover_installation
            result = verify_clover_installation()
            logger.info(f"Resultado da verificação do Clover: {result['success']}")
            if result['issues']:
                for issue in result['issues']:
                    logger.warning(f"Problema na verificação do Clover: {issue}")
            return result['success']
        except Exception as e:
            logger.error(f"Erro ao verificar instalação do Clover: {e}")
            return False

    verify_actions = component_data.get('verify_actions')

    if not verify_actions:
        verify_actions = _infer_check_patterns(component_name, component_data)

    if not verify_actions:
        logger.info(f"Nenhuma ação de verificação definida ou inferida para '{component_name}'. Assumindo sucesso.")
        return True

    logger.verification(f"Verificando instalação de {component_name}...")
    send_status_update({'type': 'stage', 'component': component_name, 'stage': 'Verifying Installation'})

    all_checks_passed = True
    verification_results = []
    total_checks = len(verify_actions)

    for i, action in enumerate(verify_actions):
        action_type = action.get('type')
        check_passed = False
        error_msg = f"Falha na verificação {i+1} ({action_type})"
        check_details = {}

        # Atualiza progresso da verificação
        send_status_update({
            'type': 'progress',
            'component': component_name,
            'stage': 'Verification',
            'percent': int((i / total_checks) * 100) if total_checks > 0 else 0
        })

        try:
            if action_type == 'file_exists':
                path = expand_env_vars(action.get('path'))
                check_details['path'] = path
                if path and os.path.isfile(path):
                    check_passed = True
                    # Verificação adicional: tamanho do arquivo
                    if action.get('min_size'):
                        min_size = int(action.get('min_size'))
                        file_size = os.path.getsize(path)
                        if file_size < min_size:
                            check_passed = False
                            error_msg += f": Arquivo '{path}' existe mas tem tamanho insuficiente ({file_size} bytes < {min_size} bytes)"
                            check_details['actual_size'] = file_size
                            check_details['min_size'] = min_size
                else:
                    error_msg += f": Arquivo não encontrado em '{path}'"

            elif action_type == 'directory_exists':
                path = expand_env_vars(action.get('path'))
                check_details['path'] = path
                if path and os.path.isdir(path):
                    check_passed = True
                    # Verificação adicional: conteúdo do diretório
                    if action.get('min_files'):
                        min_files = int(action.get('min_files'))
                        files_count = len([f for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))])
                        if files_count < min_files:
                            check_passed = False
                            error_msg += f": Diretório '{path}' existe mas contém poucos arquivos ({files_count} < {min_files})"
                            check_details['files_count'] = files_count
                            check_details['min_files'] = min_files
                else:
                    error_msg += f": Diretório não encontrado em '{path}'"

            elif action_type == 'env_var_exists':
                name = action.get('name')
                check_details['name'] = name
                # Verifica variável de ambiente atual do processo E persistente
                env_value = os.environ.get(name) or env_manager.get_env_var(name, 'user') or env_manager.get_env_var(name, 'system')
                if name and env_value:
                    check_passed = True
                    check_details['value'] = env_value
                    # Verificação adicional: valor esperado
                    if action.get('expected_value') and action.get('expected_value') != env_value:
                        check_passed = False
                        error_msg += f": Variável '{name}' tem valor '{env_value}' mas esperava '{action.get('expected_value')}'"
                        check_details['expected_value'] = action.get('expected_value')
                else:
                    error_msg += f": Variável de ambiente '{name}' não definida"

            elif action_type == 'command_exists':
                name = action.get('name')
                check_details['name'] = name
                command_path = shutil.which(name)
                if name and command_path:
                    check_passed = True
                    check_details['path'] = command_path
                    # Verificação adicional: versão do comando
                    if action.get('version_command') and action.get('expected_version'):
                        version_cmd = action.get('version_command').replace('{cmd}', name)
                        try:
                            result = subprocess.run(version_cmd, shell=True, capture_output=True, text=True, timeout=30, check=False, encoding='utf-8', errors='ignore')
                            if result.returncode == 0:
                                version_output = result.stdout.strip()
                                check_details['version'] = version_output
                                if action.get('expected_version') not in version_output:
                                    check_passed = False
                                    error_msg += f": Comando '{name}' existe mas versão não corresponde. Esperava '{action.get('expected_version')}', obteve '{version_output}'"
                                    check_details['expected_version'] = action.get('expected_version')
                        except Exception as ver_e:
                            logger.verification(f"Erro ao verificar versão do comando '{name}': {ver_e}")
                else:
                    error_msg += f": Comando '{name}' não encontrado no PATH"

            elif action_type == 'registry_key_exists':
                key_path = action.get('path')
                hive = action.get('hive', 'HKLM')
                check_details['hive'] = hive
                check_details['path'] = key_path
                if env_checker.registry_key_exists(hive, key_path):
                     check_passed = True
                     # Verificação adicional: valor da chave
                     if action.get('value_name'):
                         value_name = action.get('value_name')
                         try:
                             reg_value = env_checker.get_registry_value(hive, key_path, value_name)
                             check_details['value'] = str(reg_value)
                             if action.get('expected_value') and str(reg_value) != str(action.get('expected_value')):
                                 check_passed = False
                                 error_msg += f": Valor '{value_name}' da chave de registro é '{reg_value}' mas esperava '{action.get('expected_value')}'"
                                 check_details['expected_value'] = action.get('expected_value')
                         except Exception as reg_e:
                             logger.verification(f"Erro ao ler valor '{value_name}' da chave de registro '{hive}\\{key_path}': {reg_e}")
                else:
                     error_msg += f": Chave de registro não encontrada '{hive}\\{key_path}'"

            elif action_type == 'command_output':
                # Verifica se o comando principal existe antes de tentar executar (especialmente para flatpak)
                command_parts = action.get('command')
                executable_name = None
                if isinstance(command_parts, list) and command_parts:
                    executable_name = command_parts[0]
                elif isinstance(command_parts, str):
                     # Tenta extrair o primeiro "token" como nome do executável
                     try:
                         import shlex
                         executable_name = shlex.split(command_parts)[0]
                     except: # Se shlex falhar, usa a string inteira (menos robusto)
                          executable_name = command_parts.split()[0] if command_parts else None

                if executable_name and shutil.which(executable_name) is None:
                     error_msg += f": Comando principal '{executable_name}' não encontrado no PATH."
                     check_passed = False
                     # Pula a execução do comando se o executável não existe
                else:
                    # Continua com a lógica original de execução e verificação (CORRETAMENTE INDENTADO)
                    command_str_orig = action.get('command') # Renomeia para evitar conflito
                    expected_contains = action.get('expected_contains')
                    expected_regex = action.get('expected_regex')
                    check_details['command'] = command_str_orig # Usa a variável renomeada

                    if command_str_orig and (expected_contains or expected_regex):
                        try:
                            command_to_run = action.get('command') # Pode ser string ou lista
                            use_shell = False
                            if isinstance(command_to_run, str):
                                # Tenta dividir a string em lista, se falhar, usa shell=True
                                try:
                                    command_list = shlex.split(command_to_run)
                                    command_to_run = command_list # Usa a lista dividida
                                    logger.debug(f"Comando string dividido em lista: {command_to_run}")
                                except ValueError:
                                    logger.warning(f"Não foi possível dividir o comando string '{command_to_run}' com shlex. Usando shell=True como fallback.")
                                    use_shell = True
                            elif not isinstance(command_to_run, list):
                                 raise ValueError("Comando inválido: deve ser string ou lista.")

                            logger.debug(f"Executando verificação de comando: {command_to_run} (shell={use_shell})")
                            result = subprocess.run(command_to_run, shell=use_shell, capture_output=True, text=True, timeout=60, check=False, encoding='utf-8', errors='ignore')
                            output = result.stdout + result.stderr
                            check_details['exit_code'] = result.returncode
                            check_details['output'] = output[:200] + ('...' if len(output) > 200 else '')

                            # Compara em minúsculas para robustez
                            if expected_contains and expected_contains.lower() in output.lower():
                                check_passed = True
                                check_details['match_type'] = 'contains'
                                check_details['expected'] = expected_contains
                            elif expected_regex and re.search(expected_regex, output):
                                check_passed = True
                                check_details['match_type'] = 'regex'
                                check_details['expected'] = expected_regex
                            else:
                                 # Usa command_str_orig na mensagem de erro
                                 error_msg += f": Saída do comando '{command_str_orig}' não contém '{expected_contains or expected_regex}'. Saída: {output[:100]}..."

                        except Exception as cmd_e:
                            # Usa command_str_orig na mensagem de erro
                            error_msg += f": Erro ao executar comando '{command_str_orig}': {cmd_e}"
                            check_details['error'] = str(cmd_e)
                    else: # Este else pertence ao if da linha 1454
                        error_msg += ": Ação 'command_output' requer 'command' e ('expected_contains' ou 'expected_regex')"
# <<<< REMOVER ESTAS LINHAS DUPLICADAS >>>>

            else:
                logger.verification(f"Tipo de verificação desconhecido '{action_type}' para '{component_name}'.")
                all_checks_passed = False
                continue

            # Registra o resultado da verificação
            verification_result = {
                'type': action_type,
                'passed': check_passed,
                'details': check_details
            }

            if not check_passed:
                verification_result['error'] = error_msg

            verification_results.append(verification_result)

            if check_passed:
                logger.verification(f"Verificação {i+1}/{len(verify_actions)} ({action_type}) para '{component_name}' passou.")
            else:
                logger.verification(error_msg)
                logger.rollback(f"Preparando para rollback de '{component_name}' devido a falha na verificação ({action_type}).")
                all_checks_passed = False

                # Notifica erro de verificação
                send_status_update({
                    'type': 'error',
                    'component': component_name,
                    'category': 'VERIFICATION',
                    'message': error_msg,
                    'details': check_details,
                    'severity': 'ERROR',
                    'recoverable': True
                }, status_queue=status_queue)

        except Exception as verify_e:
             error_msg = f"Erro durante a execução da verificação {i+1} ({action_type}) para '{component_name}': {verify_e}"
             logger.verification(error_msg)
             logger.rollback(f"Preparando para rollback de '{component_name}' devido a exceção durante verificação ({action_type}).")
             all_checks_passed = False

             # Registra o erro de verificação
             verification_results.append({
                'type': action_type,
                'passed': False,
                'error': error_msg,
                'details': {'exception': str(verify_e)}
             })

             # Notifica erro de verificação
             send_status_update({
                'type': 'error',
                'component': component_name,
                'category': 'VERIFICATION',
                'message': error_msg,
                'severity': 'ERROR',
                'recoverable': True
             }, status_queue=status_queue)

    # Atualiza progresso final
    send_status_update({
        'type': 'progress',
        'component': component_name,
        'stage': 'Verification',
        'percent': 100
    })

    # Envia resultado da verificação
    verification_status = 'SUCCESS' if all_checks_passed else 'FAILED'
    send_status_update({
        'type': 'verification_result',
        'component': component_name,
        'status': verification_status,
        'results': verification_results,
        'message': f"Verificação de {component_name}: {verification_status}"
    }, status_queue=status_queue)

    if all_checks_passed:
        logger.verification(f"Todas as {len(verify_actions)} verificações para '{component_name}' passaram.")
    else:
        logger.verification(f"Uma ou mais verificações falharam para '{component_name}'.")
        logger.rollback(f"Preparando para rollback de '{component_name}' devido a falhas nas verificações.")

    return all_checks_passed

def _show_post_install_message(component_name, component_data):
    """Exibe a mensagem pós-instalação, se definida."""
    message = component_data.get('post_install_message')
    if message:
        logger.installation(f"--- Mensagem Pós-Instalação para {component_name} ---")
        logger.installation(message.strip())
        logger.installation("-----------------------------------------------------")
        send_status_update({'type': 'log', 'level': 'INFO', 'message': f"Post-Install ({component_name}): {message.strip()}"})

def _handle_post_install(component_name, component_data, rollback_mgr: RollbackManager):
    """
    Executa ações pós-instalação para um componente.

    Estas ações podem incluir:
    - Configuração adicional
    - Registro de componente em banco de dados local
    - Verificação de integridade
    - Limpeza de arquivos temporários
    - Notificação de outros componentes

    Args:
        component_name: Nome do componente
        component_data: Dados do componente
        rollback_mgr: Instância do RollbackManager para registro de ações de rollback

    Returns:
        bool: True se todas as ações pós-instalação foram bem-sucedidas, False caso contrário
    """
    logger.installation(f"Executando ações pós-instalação para {component_name}...")
    send_status_update({'type': 'stage', 'component': component_name, 'stage': 'Post-Installation'})

    # Obtém ações pós-instalação do componente
    post_install_actions = component_data.get('post_install_actions', [])
    if not post_install_actions:
        logger.installation(f"Nenhuma ação pós-instalação definida para '{component_name}'")
        return True

    success = True
    for i, action in enumerate(post_install_actions):
        action_type = action.get('type')
        logger.installation(f"Executando ação pós-instalação {i+1}/{len(post_install_actions)} ({action_type}) para '{component_name}'")

        try:
            if action_type == 'cleanup':
                # Limpa arquivos temporários
                paths_to_clean = action.get('paths', [])
                for path in paths_to_clean:
                    path = expand_env_vars(path)
                    if os.path.exists(path):
                        if os.path.isdir(path):
                            logger.installation(f"Removendo diretório temporário: {path}")
                            shutil.rmtree(path, ignore_errors=True)
                        else:
                            logger.installation(f"Removendo arquivo temporário: {path}")
                            os.remove(path)

            elif action_type == 'register':
                # Registra o componente em um banco de dados local ou arquivo de configuração
                registry_file = action.get('registry_file', os.path.join(os.path.expanduser("~"), ".env_dev", "installed_components.json"))
                registry_file = expand_env_vars(registry_file)

                # Garante que o diretório existe
                os.makedirs(os.path.dirname(registry_file), exist_ok=True)

                # Carrega o registro existente ou cria um novo
                registry_data = {}
                if os.path.exists(registry_file):
                    try:
                        with open(registry_file, 'r', encoding='utf-8') as f:
                            registry_data = json.load(f)
                    except json.JSONDecodeError:
                        logger.installation(f"Arquivo de registro corrompido: {registry_file}. Criando novo.")

                # Adiciona ou atualiza o componente no registro
                registry_data[component_name] = {
                    'version': component_data.get('version', 'unknown'),
                    'install_date': time.strftime("%Y-%m-%d %H:%M:%S"),
                    'install_method': component_data.get('install_method'),
                    'extract_path': expand_env_vars(component_data.get('extract_path', '')),
                    'status': 'installed'
                }

                # Salva o registro atualizado
                with open(registry_file, 'w', encoding='utf-8') as f:
                    json.dump(registry_data, f, indent=2)

                logger.installation(f"Componente '{component_name}' registrado em {registry_file}")

                # Registra ação de rollback para remover do registro
                rollback_mgr.register_action({
                    'undo_action': 'modify_json',
                    'parameters': {
                        'file_path': registry_file,
                        'operation': 'remove_key',
                        'key': component_name
                    },
                    'step': 'Registering Component'
                })

            elif action_type == 'notify':
                # Notifica outros componentes ou sistemas sobre a instalação
                target = action.get('target', '')
                message = action.get('message', f"Componente {component_name} instalado com sucesso")

                if target == 'system_tray':
                    # Notificação na bandeja do sistema (exemplo simplificado)
                    logger.installation(f"Enviando notificação para bandeja do sistema: {message}")
                    # Implementação real dependeria de uma biblioteca como 'plyer' ou similar

                elif target == 'log_file':
                    # Registra em um arquivo de log específico
                    log_file = action.get('log_file', '')
                    if log_file:
                        log_file = expand_env_vars(log_file)
                        with open(log_file, 'a', encoding='utf-8') as f:
                            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")

                elif target == 'event':
                    # Dispara um evento para outros componentes (simulado aqui)
                    event_name = action.get('event_name', 'component_installed')
                    logger.installation(f"Disparando evento '{event_name}' para '{component_name}'")
                    # Em uma implementação real, usaria um sistema de eventos

            else:
                logger.installation(f"Tipo de ação pós-instalação desconhecido: {action_type}")

        except Exception as e:
            err = handle_exception(e,
                                  f"Erro durante ação pós-instalação {i+1} ({action_type}) para '{component_name}'",
                                  ErrorCategory.INSTALLATION,
                                  ErrorSeverity.WARNING)
            err.log()
            logger.rollback(f"Preparando para rollback de '{component_name}' devido a falha na ação pós-instalação ({action_type}).")
            # Continua com as próximas ações, mas marca como falha
            success = False

    if success:
        logger.installation(f"Todas as ações pós-instalação para '{component_name}' concluídas com sucesso")
    else:
        logger.installation(f"Uma ou mais ações pós-instalação para '{component_name}' falharam")
        logger.rollback(f"Preparando para rollback de '{component_name}' devido a falhas nas ações pós-instalação.")

    return success


class InstallationActionManager:
    """Gerenciador de ações de instalação.
    
    Esta classe coordena as diferentes etapas de instalação de um componente,
    implementando uma máquina de estados clara e mantendo o controle de falhas.
    """
    
    def __init__(self, component_name: str, component_data: Dict[str, Any], all_components_data: Dict[str, Any]):
        """Inicializa o gerenciador de ações para um componente específico."""
        self.component_name = component_name
        self.component_data = component_data
        self.all_components_data = all_components_data
        self.install_method = component_data.get('install_method', 'none')
        self.logger = logger
        
        # Estes atributos serão configurados pelo chamador
        self.rollback_mgr = None  # Será definido pelo chamador
        self.progress_callback = None  # Função de callback para atualizações de progresso
        self.status_queue = None  # Fila para enviar mensagens de status
        
        # Rastreia resultados de diferentes etapas
        self.download_result = None
        self.verification_results = {}
    
    def start_installation(self) -> bool:
        """Inicia o fluxo de instalação completo para o componente."""
        try:
            # Monitoramento de tempo de instalação
            start_time = time.time()
            
            # 1. Verifica pré-requisitos
            if not self._check_prerequisites():
                self.logger.error(f"Falha nos pré-requisitos para '{self.component_name}'")
                send_status_update({
                    'type': 'result',
                    'component': self.component_name,
                    'status': 'FAILED',
                    'message': 'Prerequisites check failed',
                    'severity': 'ERROR',
                    'recoverable': True
                }, status_queue=self.status_queue)
                
                return False
            
            # 2. Realiza a instalação conforme o método definido
            if not self._perform_installation():
                self.logger.error(f"Falha na instalação do componente '{self.component_name}'")
                send_status_update({
                    'type': 'result',
                    'component': self.component_name,
                    'status': 'FAILED',
                    'message': 'Installation failed',
                    'severity': 'ERROR',
                    'recoverable': True
                }, status_queue=self.status_queue)
                
                return False
                
            # 3. Configura o ambiente (variáveis, paths, etc)
            if not self._configure_environment():
                self.logger.error(f"Falha na configuração de ambiente para '{self.component_name}'")
                # Não retorna False aqui, pois a instalação já foi feita
                
            # 4. Verifica a instalação
            if not self._verify_installation():
                self.logger.error(f"Falha na verificação pós-instalação para '{self.component_name}'")
                
                verification_status = "FAILED"
                verification_results = {'success': False, 'errors': self.verification_results}
                
                send_status_update({
                    'type': 'verification',
                    'component': self.component_name,
                    'status': verification_status,
                    'results': verification_results,
                    'message': f"Verificação de {self.component_name}: {verification_status}"
                }, status_queue=self.status_queue)
                
                return False
                
            # 5. Executa ações pós-instalação
            self._handle_post_install()
                
            # Tempo total de instalação
            end_time = time.time()
            elapsed_time = end_time - start_time
            self.logger.info(f"Tempo total para instalar '{self.component_name}': {elapsed_time:.2f} segundos")
                
            # Retorna sucesso geral
            return True
            
        except Exception as e:
            # Loga e propaga a exceção para o chamador
            self.logger.exception(f"Erro durante instalação de '{self.component_name}': {e}")
            send_status_update({
                'type': 'result',
                'component': self.component_name,
                'status': 'FAILED',
                'message': f"Unexpected error: {str(e)}",
                'exception': traceback.format_exc()
            }, status_queue=self.status_queue)
            
            raise

    def _check_prerequisites(self) -> bool:
        """
        Verifica se todos os pré-requisitos para a instalação estão satisfeitos.

        Verifica:
        - Dependências
        - Permissões necessárias
        - Espaço em disco
        - Versão do sistema operacional
        - Outros requisitos específicos

        Returns:
            bool: True se todos os pré-requisitos estão satisfeitos, False caso contrário
        """
        self.logger.info(f"Verificando pré-requisitos para '{self.component_name}'...")
        send_status_update({'type': 'stage', 'component': self.component_name, 'stage': 'Checking Prerequisites'})

        # 1. Verifica permissões de administrador se necessário
        requires_admin = self.component_data.get('requires_admin', False)
        if requires_admin and not env_checker.is_admin():
            err = permission_error(f"Componente '{self.component_name}' requer privilégios de administrador para instalar.",
                                  component=self.component_name)
            err.log()
            send_status_update({'type': 'result', 'component': self.component_name, 'status': 'FAILURE', 'message': 'Admin privileges required'})
            return False

        # 2. Verifica espaço em disco (se especificado)
        required_space = self.component_data.get('required_disk_space_mb', 0)
        if required_space > 0:
            install_drive = os.path.splitdrive(expand_env_vars(self.component_data.get('extract_path', 'C:\\')))[0]
            if not install_drive:
                install_drive = 'C:'

            try:
                free_space = shutil.disk_usage(install_drive).free / (1024 * 1024)  # Em MB
                if free_space < required_space:
                    err = installation_error(
                        f"Espaço em disco insuficiente para '{self.component_name}'. Necessário: {required_space} MB, Disponível: {free_space:.1f} MB",
                        component=self.component_name,
                        severity=ErrorSeverity.ERROR
                    )
                    err.log()
                    return False
            except Exception as e:
                self.logger.warning(f"Não foi possível verificar espaço em disco para '{install_drive}': {e}")

        # 3. Verifica versão do sistema operacional (se especificado)
        required_os = self.component_data.get('required_os', {})
        if required_os:
            current_os = platform.system()
            if current_os == 'Windows':
                min_version = required_os.get('min_windows_version')
                if min_version:
                    win_ver = platform.version()
                    # Implementação simplificada - em produção, usar comparação semântica de versões
                    if win_ver < min_version:
                        err = installation_error(
                            f"Versão do Windows incompatível para '{self.component_name}'. Mínimo: {min_version}, Atual: {win_ver}",
                            component=self.component_name,
                            severity=ErrorSeverity.ERROR
                        )
                        err.log()
                        return False

        # 4. Verifica dependências (usando a função existente)
        dependencies = self.component_data.get('dependencies', [])
        if dependencies:
            # Cria um conjunto vazio para rastrear componentes instalados nesta sessão
            # Isso é apenas para a verificação de dependências, não afeta o estado global
            temp_installed = set()
            visiting = set()

            if not _handle_dependencies(
                self.component_name,
                self.component_data,
                self.all_components_data,
                temp_installed,
                visiting,
                self.rollback_mgr,
                status_queue=self.status_queue
            ):
                self.logger.error(f"Falha ao resolver dependências para '{self.component_name}'")
                return False

        self.logger.info(f"Todos os pré-requisitos para '{self.component_name}' estão satisfeitos")
        return True

    def _perform_installation(self) -> bool:
        """
        Executa a instalação principal com base no método definido.
        
        Returns:
            bool: True se a instalação foi bem-sucedida, False caso contrário
        """
        self.logger.info(f"Executando instalação principal para '{self.component_name}' usando método '{self.install_method}'")

        # Executa a instalação com base no método
        if self.install_method in ['download', 'archive', 'exe', 'msi']:
            success, self.download_path = install_download_type(
                self.component_name,
                self.component_data,
                self.rollback_mgr,
                progress_callback=self.progress_callback,
                status_queue=self.status_queue
            )
            return success

        elif self.install_method in ['pip', 'vcpkg']:
            return install_command_type(
                self.component_name,
                self.component_data,
                self.all_components_data,
                self.rollback_mgr,
                status_queue=self.status_queue
            )

        elif self.install_method == 'script':
            return _install_script(
                self.component_name,
                self.component_data,
                self.rollback_mgr
            )

        elif self.install_method == 'none':
            self.logger.info(f"Componente '{self.component_name}' definido como 'none'. Nenhuma ação de instalação necessária.")
            return True

        else:
            err = installation_error(
                f"Tipo de instalação desconhecido: '{self.install_method}'",
                component=self.component_name
            )
            err.log()
            send_status_update({
                'type': 'result',
                'component': self.component_name,
                'status': 'FAILED',
                'message': f"Unknown installation type: {self.install_method}"
            }, status_queue=self.status_queue)
            return False

    def _configure_environment(self) -> bool:
        """
        Configura o ambiente do sistema após a instalação principal.

        Configura:
        - Variáveis de ambiente
        - PATH do sistema
        - Registros do Windows
        - Outros aspectos do ambiente

        Returns:
            bool: True se a configuração foi bem-sucedida, False caso contrário
        """
        return _configure_environment(self.component_name, self.component_data, self.rollback_mgr)

    def _verify_installation(self) -> bool:
        """
        Verifica se a instalação foi bem-sucedida usando verificações definidas ou inferidas.

        Executa verificações como:
        - Existência de arquivos/diretórios
        - Verificação de comandos
        - Verificação de variáveis de ambiente
        - Verificação de chaves de registro
        - Saída de comandos específicos

        Returns:
            bool: True se todas as verificações passaram, False caso contrário
        """
        self.logger.info(f"Verificando instalação de '{self.component_name}'...")
        send_status_update({'type': 'stage', 'component': self.component_name, 'stage': 'Verifying Installation'})

        # Obtém as verificações definidas no componente
        verify_actions = self.component_data.get('verify_actions')

        # Se não houver verificações definidas, tenta inferir com base no método de instalação
        if not verify_actions:
            verify_actions = _infer_check_patterns(self.component_name, self.component_data)

        # Se ainda não houver verificações, assume sucesso
        if not verify_actions:
            self.logger.info(f"Nenhuma ação de verificação definida ou inferida para '{self.component_name}'. Assumindo sucesso.")
            return True

        # Executa todas as verificações
        all_checks_passed = True
        for i, action in enumerate(verify_actions):
            action_type = action.get('type')
            check_passed = False
            error_msg = f"Falha na verificação {i+1} ({action_type})"

            try:
                # Verificação de arquivo
                if action_type == 'file_exists':
                    path = expand_env_vars(action.get('path', ''))
                    if path and os.path.isfile(path):
                        check_passed = True
                    else:
                        error_msg += f": Arquivo '{path}' não encontrado"

                # Verificação de diretório
                elif action_type == 'directory_exists':
                    path = expand_env_vars(action.get('path', ''))
                    if path and os.path.isdir(path):
                        check_passed = True
                    else:
                        error_msg += f": Diretório '{path}' não encontrado"

                # Verificação de comando no PATH
                elif action_type == 'command_exists':
                    name = action.get('name')
                    if name and shutil.which(name):
                        check_passed = True
                    else:
                        error_msg += f": Comando '{name}' não encontrado no PATH"

                # Verificação de saída de comando
                elif action_type == 'command_output':
                    command = action.get('command')
                    expected_contains = action.get('expected_contains')
                    expected_regex = action.get('expected_regex')
                    expected_return_code = action.get('expected_return_code', 0)

                    if command and (expected_contains or expected_regex):
                        try:
                            # Prepara o comando
                            if isinstance(command, list):
                                command = [expand_env_vars(item) for item in command]
                                command_str = ' '.join(command)
                            else:
                                command = expand_env_vars(command)
                                command_str = command

                            # Executa o comando
                            self.logger.debug(f"Executando comando de verificação: {command_str}")
                            result = subprocess.run(command, shell=not isinstance(command, list),
                                                  capture_output=True, text=True, check=False)

                            # Verifica o código de retorno
                            if result.returncode != expected_return_code:
                                error_msg += f": Comando '{command_str}' retornou código {result.returncode} (esperado: {expected_return_code})"
                            else:
                                # Verifica a saída esperada
                                if expected_contains and expected_contains not in result.stdout:
                                    error_msg += f": Saída do comando não contém '{expected_contains}'"
                                elif expected_regex and not re.search(expected_regex, result.stdout):
                                    error_msg += f": Saída do comando não corresponde ao padrão '{expected_regex}'"
                                else:
                                    check_passed = True
                        except Exception as cmd_e:
                            error_msg += f": Erro ao executar comando '{command_str}': {cmd_e}"
                    else:
                        error_msg += ": Ação 'command_output' requer 'command' e ('expected_contains' ou 'expected_regex')"

                # Verificação de variável de ambiente
                elif action_type == 'env_var':
                    var_name = action.get('name')
                    expected_value = action.get('expected_value')

                    if var_name:
                        if var_name not in os.environ:
                            error_msg += f": Variável de ambiente '{var_name}' não definida"
                        elif expected_value and os.environ[var_name] != expected_value:
                            error_msg += f": Variável '{var_name}' tem valor '{os.environ[var_name]}' (esperado: '{expected_value}')"
                        else:
                            check_passed = True
                    else:
                        error_msg += ": Ação 'env_var' requer 'name'"

                # Verificação de chave de registro (Windows)
                elif action_type == 'registry_key_exists':
                    if platform.system() != 'Windows':
                        self.logger.warning(f"Verificação 'registry_key_exists' ignorada em sistema não-Windows")
                        check_passed = True
                    else:
                        import winreg
                        key_path = action.get('path')
                        hive_name = action.get('hive', 'HKEY_LOCAL_MACHINE')

                        if key_path:
                            # Mapeia o nome da hive para a constante do winreg
                            hive_map = {
                                'HKEY_LOCAL_MACHINE': winreg.HKEY_LOCAL_MACHINE,
                                'HKEY_CURRENT_USER': winreg.HKEY_CURRENT_USER,
                                'HKEY_CLASSES_ROOT': winreg.HKEY_CLASSES_ROOT,
                                'HKEY_USERS': winreg.HKEY_USERS,
                                'HKEY_CURRENT_CONFIG': winreg.HKEY_CURRENT_CONFIG
                            }

                            hive = hive_map.get(hive_name)
                            if hive:
                                try:
                                    with winreg.OpenKey(hive, key_path) as _:
                                        check_passed = True
                                except FileNotFoundError:
                                    error_msg += f": Chave de registro '{hive_name}\\{key_path}' não encontrada"
                            else:
                                error_msg += f": Hive de registro '{hive_name}' inválida"
                        else:
                            error_msg += ": Ação 'registry_key_exists' requer 'path'"

                # Verificação de valor de registro (Windows)
                elif action_type == 'registry_value':
                    if platform.system() != 'Windows':
                        self.logger.warning(f"Verificação 'registry_value' ignorada em sistema não-Windows")
                        check_passed = True
                    else:
                        key_path = action.get('path')
                        value_name = action.get('value_name')
                        expected_value = action.get('expected_value')
                        hive_name = action.get('hive', 'HKEY_LOCAL_MACHINE')

                        if key_path and value_name:
                            # Mapeia o nome da hive para a constante do winreg
                            hive_map = {
                                'HKEY_LOCAL_MACHINE': winreg.HKEY_LOCAL_MACHINE,
                                'HKEY_CURRENT_USER': winreg.HKEY_CURRENT_USER,
                                'HKEY_CLASSES_ROOT': winreg.HKEY_CLASSES_ROOT,
                                'HKEY_USERS': winreg.HKEY_USERS,
                                'HKEY_CURRENT_CONFIG': winreg.HKEY_CURRENT_CONFIG
                            }

                            hive = hive_map.get(hive_name)
                            if hive:
                                try:
                                    with winreg.OpenKey(hive, key_path) as key:
                                        value, _ = winreg.QueryValueEx(key, value_name)

                                        if expected_value is not None and str(value) != str(expected_value):
                                            error_msg += f": Valor de registro '{value_name}' é '{value}' (esperado: '{expected_value}')"
                                        else:
                                            check_passed = True
                                except FileNotFoundError:
                                    error_msg += f": Chave de registro '{hive_name}\\{key_path}' não encontrada"
                                except WindowsError:
                                    error_msg += f": Valor de registro '{value_name}' não encontrado"
                            else:
                                error_msg += f": Hive de registro '{hive_name}' inválida"
                        else:
                            error_msg += ": Ação 'registry_value' requer 'path' e 'value_name'"

                else:
                    self.logger.warning(f"Tipo de verificação desconhecido: '{action_type}'")
                    continue

                # Registra o resultado da verificação
                if check_passed:
                    self.logger.info(f"Verificação {i+1}/{len(verify_actions)} ({action_type}) para '{self.component_name}' passou.")
                else:
                    self.logger.error(error_msg)
                    all_checks_passed = False

            except Exception as e:
                self.logger.error(f"Erro durante a execução da verificação {i+1} ({action_type}): {e}")
                all_checks_passed = False

        # Resultado final
        if all_checks_passed:
            self.logger.info(f"Todas as {len(verify_actions)} verificações para '{self.component_name}' passaram.")
        else:
            self.logger.error(f"Uma ou mais verificações falharam para '{self.component_name}'.")
            logger.rollback(f"Preparando para rollback de '{self.component_name}' devido a falhas nas verificações.")

        return all_checks_passed

    def _handle_post_install(self) -> bool:
        """
        Executa ações pós-instalação para o componente.

        Returns:
            bool: True se todas as ações pós-instalação foram bem-sucedidas, False caso contrário
        """
        return _handle_post_install(self.component_name, self.component_data, self.rollback_mgr)

def install_component(component_name, component_data, all_components_data=None, installed_components=None, progress_callback=None, rollback_mgr=None, status_queue=None):
    """
    Instala um componente com base em seus dados.
    
    Args:
        component_name: Nome do componente
        component_data: Dados do componente
        all_components_data: Dicionário com todos os componentes (para dependências)
        installed_components: Conjunto opcional para rastrear componentes instalados
        progress_callback: Função de callback para atualizações de progresso
        rollback_mgr: Gerenciador de rollback (opcional)
        status_queue: Fila para enviar mensagens de status (opcional)
        
    Returns:
        True se a instalação foi bem-sucedida, False caso contrário
    """
    try:
        logger.info(f"Iniciando instalação de: {component_name}")
        send_status_update({'type': 'stage', 'component': component_name, 'stage': 'Preparation'}, status_queue=status_queue)
        
        # Cria um RollbackManager se não for fornecido
        if rollback_mgr is None:
            rollback_mgr = RollbackManager()
            rollback_mgr.start_transaction(component_name)
        
        # Extrai método de instalação ANTES de verificar se já está instalado
        install_method = component_data.get('install_method', 'none')
        
        # Para componentes com método 'none', apenas exibe mensagem e marca como sucesso
        if install_method == 'none':
            logger.info(f"Componente '{component_name}' definido como 'none' (instalação manual).")
            _show_post_install_message(component_name, component_data)
            
            # Marca como instalado sem verificação automática
            if installed_components is not None and hasattr(installed_components, 'add'):
                installed_components.add(component_name)
                
            send_status_update({
                'type': 'result',
                'component': component_name,
                'status': 'SUCCESS',
                'message': 'Componente de instalação manual - instruções exibidas'
            }, status_queue=status_queue)
            
            return True
        
        # Para outros métodos, verifica se já está instalado
        is_installed = _verify_installation(component_name, component_data)
        if is_installed:
            logger.info(f"Componente '{component_name}' já está instalado.")
            send_status_update({
                'type': 'result',
                'component': component_name,
                'status': 'SUCCESS',
                'message': 'Componente já instalado'
            }, status_queue=status_queue)
            
            if installed_components is not None and hasattr(installed_components, 'add'):
                installed_components.add(component_name)
            return True
            
        # Verifica e instala dependências
        if all_components_data and 'dependencies' in component_data:
            # Cria conjuntos vazios para rastrear componentes instalados nesta sessão
            temp_installed = set()
            visiting = set()
            
            if not _handle_dependencies(
                component_name,
                component_data,
                all_components_data,
                temp_installed,
                visiting,
                rollback_mgr,
                status_queue=status_queue
            ):
                logger.error(f"Falha ao resolver dependências para '{component_name}'")
                send_status_update({
                    'type': 'result',
                    'component': component_name,
                    'status': 'FAILED',
                    'message': 'Falha ao resolver dependências'
                }, status_queue=status_queue)
                return False
        
        # Instala de acordo com o método
        success = False
        
        try:
            if install_method in ['download', 'archive', 'exe', 'msi']:
                success, download_path = install_download_type(
                    component_name,
                    component_data,
                    rollback_mgr,
                    progress_callback=progress_callback,
                    status_queue=status_queue
                )
            elif install_method in ['pip', 'vcpkg']:
                success = install_command_type(
                    component_name,
                    component_data,
                    all_components_data,
                    rollback_mgr,
                    status_queue=status_queue
                )
            elif install_method == 'script':
                success = _install_script(
                    component_name,
                    component_data,
                    rollback_mgr
                )
            else:
                err = installation_error(
                    f"Tipo de instalação desconhecido: '{install_method}'",
                    component=component_name
                )
                err.log()
                send_status_update({
                    'type': 'result',
                    'component': component_name,
                    'status': 'FAILED',
                    'message': f"Tipo de instalação desconhecido: {install_method}"
                }, status_queue=status_queue)
                return False
                
            # Se a instalação falhou, aciona o rollback e retorna
            if not success:
                logger.error(f"Falha na instalação do componente '{component_name}'")
                rollback_mgr.trigger_rollback()
                send_status_update({
                    'type': 'result',
                    'component': component_name,
                    'status': 'FAILED',
                    'message': 'Falha na instalação do componente'
                }, status_queue=status_queue)
                return False
            
            # Configuração de ambiente
            if not _configure_environment(component_name, component_data, rollback_mgr):
                logger.error(f"Falha na configuração de ambiente para '{component_name}'")
                rollback_mgr.trigger_rollback()
                send_status_update({
                    'type': 'result',
                    'component': component_name,
                    'status': 'FAILED',
                    'message': 'Falha na configuração de ambiente'
                }, status_queue=status_queue)
                return False
            
            # Verificação pós-instalação
            is_verified = _verify_installation(component_name, component_data)
            if not is_verified:
                logger.error(f"Falha na verificação pós-instalação para '{component_name}'")
                rollback_mgr.trigger_rollback()
                send_status_update({
                    'type': 'result',
                    'component': component_name,
                    'status': 'FAILED',
                    'message': 'Falha na verificação pós-instalação'
                }, status_queue=status_queue)
                return False
            
            # Ações pós-instalação
            if not _handle_post_install(component_name, component_data, rollback_mgr):
                logger.error(f"Falha nas ações pós-instalação para '{component_name}'")
                rollback_mgr.trigger_rollback()
                send_status_update({
                    'type': 'result',
                    'component': component_name,
                    'status': 'FAILED',
                    'message': 'Falha nas ações pós-instalação'
                }, status_queue=status_queue)
                return False
            
            # Mensagem pós-instalação
            _show_post_install_message(component_name, component_data)
            
            # Marca como instalado 
            if installed_components is not None and hasattr(installed_components, 'add'):
                installed_components.add(component_name)
                
            logger.info(f"Componente '{component_name}' instalado com sucesso.")
            send_status_update({
                'type': 'result',
                'component': component_name,
                'status': 'SUCCESS',
                'message': 'Componente instalado com sucesso'
            }, status_queue=status_queue)
            
            return True
                
        except Exception as e:
            err = handle_exception(e, f"Erro ao instalar o componente '{component_name}'")
            err.log()
            rollback_mgr.trigger_rollback()
            send_status_update({
                'type': 'result',
                'component': component_name,
                'status': 'FAILED',
                'message': f"Erro: {str(e)}"
            }, status_queue=status_queue)
            return False
    except Exception as e:
        logger.exception(f"Erro não tratado durante instalação de '{component_name}': {e}")
        send_status_update({
            'type': 'result',
            'component': component_name,
            'status': 'FAILED',
            'message': f"Erro não tratado: {str(e)}"
        }, status_queue=status_queue)
        return False

def _handle_dependencies(component_name, component_data, all_components_data, installed_components, visiting, rollback_mgr, status_queue=None):
    """
    Manipula a instalação das dependências de um componente.
    
    Args:
        component_name: Nome do componente
        component_data: Dados do componente
        all_components_data: Dicionário com todos os componentes
        installed_components: Conjunto para rastrear componentes já instalados
        visiting: Conjunto para detectar ciclos de dependência
        rollback_mgr: Gerenciador de rollback
        status_queue: Fila para enviar mensagens de status
        
    Returns:
        True se todas as dependências foram instaladas, False caso contrário
    """
    dependencies = component_data.get('dependencies', [])
    if not dependencies:
        return True
        
    logger.info(f"Verificando dependências para '{component_name}': {dependencies}")
    send_status_update({
        'type': 'stage',
        'component': component_name,
        'stage': 'Resolvendo Dependências'
    }, status_queue=status_queue)
    
    # Verifica ciclos de dependência
    if component_name in visiting:
        logger.error(f"Ciclo de dependência detectado ao instalar '{component_name}'")
        return False
        
    visiting.add(component_name)
    
    for dep_name in dependencies:
        # Se a dependência já está instalada, pula
        if dep_name in installed_components:
            logger.info(f"Dependência '{dep_name}' já instalada. Pulando.")
            continue
            
        # Verifica se a dependência está definida nos dados de componentes
        if dep_name not in all_components_data:
            logger.error(f"Dependência '{dep_name}' de '{component_name}' não encontrada nos dados dos componentes.")
            continue
            
        logger.info(f"Instalando dependência '{dep_name}' para '{component_name}'")
        success = install_component(
            component_name=dep_name,
            component_data=all_components_data[dep_name],
            all_components_data=all_components_data,
            installed_components=installed_components,
            rollback_mgr=rollback_mgr,
            status_queue=status_queue
        )
        
        if not success:
            logger.error(f"Falha ao instalar dependência '{dep_name}' para '{component_name}'")
            visiting.remove(component_name)
            return False
    
    visiting.remove(component_name)
    return True

def install_download_type(component_name, component_data, rollback_mgr, progress_callback=None, status_queue=None):
    """
    Instala um componente do tipo download, archive, exe ou msi.
    
    Args:
        component_name: Nome do componente
        component_data: Dados do componente
        rollback_mgr: Gerenciador de rollback
        progress_callback: Função de callback para atualizações de progresso (opcional)
        status_queue: Fila para enviar mensagens de status (opcional)
        
    Returns:
        Tupla (bool, str): (True se a instalação foi bem-sucedida, caminho do download)
    """
    logger.info(f"Instalando componente '{component_name}' do tipo download/archive/exe/msi")
    send_status_update({'type': 'stage', 'component': component_name, 'stage': 'Download'}, status_queue=status_queue)
    
    try:
        # Obtém dados do download
        download_url = component_data.get('download_url')
        if not download_url:
            err = installation_error(f"URL de download não especificada para '{component_name}'", component=component_name, severity=ErrorSeverity.ERROR)
            err.log()
            return False, None
            
        logger.info(f"Baixando {component_name} de {download_url}")
        
        # Nome de arquivo baseado na URL se não especificado
        filename = component_data.get('filename')
        if not filename:
            filename = os.path.basename(download_url)
            
        # Diretório de download
        download_dir = component_data.get('download_dir', os.path.join(TEMP_DIR, component_name))
        os.makedirs(download_dir, exist_ok=True)
        
        # Caminho completo do download
        download_path = os.path.join(download_dir, filename)
        
        # Hash para verificação
        expected_hash = component_data.get('hash')
        hash_algo = component_data.get('hash_algorithm', 'sha256')
        
        # Registra ação de rollback para o download
        rollback_mgr.register_action({
            'undo_action': 'delete_path',
            'parameters': {'path': download_path},
            'step': 'Downloading'
        })
        
        # Baixa o arquivo
        from env_dev.utils import downloader
        download_success = downloader.download_file(
            url=download_url,
            destination_path=download_path,
            expected_hash=expected_hash,
            hash_algorithm=hash_algo,
            progress_callback=progress_callback
        )
        
        if not download_success:
            logger.error(f"Falha ao baixar arquivo para '{component_name}'")
            return False, None
            
        logger.info(f"Download de '{component_name}' concluído com sucesso.")
        
        # Determina o método de instalação
        install_method = component_data.get('install_method', 'archive')
        
        # Executa a instalação conforme o método
        if install_method == 'archive':
            success = _install_archive(component_name, component_data, download_path, rollback_mgr)
            return success, download_path
        elif install_method in ['exe', 'msi']:
            success = _install_executable(component_name, component_data, download_path, rollback_mgr)
            return success, download_path
        elif install_method == 'download':
            # Apenas baixa o arquivo, sem instalar
            logger.info(f"Componente '{component_name}' apenas requer download. Marcando como sucesso.")
            return True, download_path
        else:
            err = installation_error(f"Método de instalação '{install_method}' não suportado pela função install_download_type", component=component_name)
            err.log()
            return False, download_path
            
    except Exception as e:
        err = handle_exception(
            e, 
            message=f"Erro ao instalar componente '{component_name}' do tipo download",
            category=ErrorCategory.INSTALLATION,
            severity=ErrorSeverity.ERROR,
            context={"component": component_name}
        )
        err.log()
        return False, None

def install_command_type(component_name, component_data, all_components_data, rollback_mgr, status_queue=None):
    """
    Instala um componente do tipo command (pip, vcpkg, etc).
    
    Args:
        component_name: Nome do componente
        component_data: Dados do componente
        all_components_data: Dicionário com todos os componentes (para vcpkg)
        rollback_mgr: Gerenciador de rollback
        status_queue: Fila para enviar mensagens de status (opcional)
        
    Returns:
        bool: True se a instalação foi bem-sucedida, False caso contrário
    """
    install_method = component_data.get('install_method')
    
    logger.info(f"Instalando componente '{component_name}' do tipo {install_method}")
    send_status_update({'type': 'stage', 'component': component_name, 'stage': f'Installing ({install_method})'}, status_queue=status_queue)
    
    try:
        if install_method == 'pip':
            return _install_pip(component_name, component_data, rollback_mgr)
        elif install_method == 'vcpkg':
            return _install_vcpkg(component_name, component_data, all_components_data, rollback_mgr)
        else:
            err = installation_error(f"Método de instalação '{install_method}' não suportado pela função install_command_type", component=component_name)
            err.log()
            return False
    except Exception as e:
        err = handle_exception(
            e, 
            message=f"Erro ao instalar componente '{component_name}' do tipo {install_method}",
            category=ErrorCategory.INSTALLATION,
            severity=ErrorSeverity.ERROR,
            context={"component": component_name}
        )
        err.log()
        return False