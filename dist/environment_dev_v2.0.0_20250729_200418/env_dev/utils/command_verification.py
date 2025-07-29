#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo para verificação consistente de comandos e executáveis.

Este módulo fornece funções robustas para verificar se comandos estão disponíveis
no sistema, com tratamento adequado para diferentes sistemas operacionais.
"""

import os
import sys
import shutil
import subprocess
import platform
import logging
from typing import Optional, List, Dict, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)

def command_exists(command: str, check_path: bool = True, check_builtin: bool = True, 
                  use_cache: bool = True) -> bool:
    """
    Verifica se um comando existe e está disponível no sistema.
    
    Args:
        command: Nome do comando a verificar
        check_path: Se deve verificar no PATH do sistema
        check_builtin: Se deve verificar comandos built-in do shell
        use_cache: Se deve usar cache de resultados para melhor performance
        
    Returns:
        True se o comando existe, False caso contrário
    """
    # Cache para evitar verificações repetidas
    if not hasattr(command_exists, '_cache'):
        command_exists._cache = {}
    
    cache_key = f"{command}_{check_path}_{check_builtin}"
    
    if use_cache and cache_key in command_exists._cache:
        logger.debug(f"Comando '{command}' encontrado no cache: {command_exists._cache[cache_key]}")
        return command_exists._cache[cache_key]
    
    try:
        result = False
        
        # Método 1: Usar shutil.which (mais confiável)
        if check_path:
            which_result = shutil.which(command)
            if which_result:
                logger.debug(f"Comando '{command}' encontrado via shutil.which: {which_result}")
                result = True
        
        # Método 2: Verificar comandos built-in do shell
        if not result and check_builtin:
            if _is_builtin_command(command):
                logger.debug(f"Comando '{command}' é um comando built-in")
                result = True
        
        # Método 3: Tentar executar com --version ou --help (apenas se não encontrado ainda)
        if not result:
            if _test_command_execution(command):
                logger.debug(f"Comando '{command}' respondeu a teste de execução")
                result = True
        
        # Método 4: Verificação específica para Windows
        if not result and platform.system() == 'Windows':
            result = _windows_command_check(command)
        
        if not result:
            logger.debug(f"Comando '{command}' não encontrado")
        
        # Armazenar no cache
        if use_cache:
            command_exists._cache[cache_key] = result
        
        return result
        
    except Exception as e:
        logger.debug(f"Erro ao verificar comando '{command}': {e}")
        if use_cache:
            command_exists._cache[cache_key] = False
        return False

def _is_builtin_command(command: str) -> bool:
    """
    Verifica se um comando é built-in do shell.
    
    Args:
        command: Nome do comando
        
    Returns:
        True se é um comando built-in, False caso contrário
    """
    # Comandos built-in comuns do Windows
    windows_builtins = {
        'cd', 'dir', 'copy', 'move', 'del', 'md', 'mkdir', 'rd', 'rmdir',
        'type', 'echo', 'set', 'path', 'cls', 'exit', 'help', 'vol',
        'date', 'time', 'ver', 'title', 'color', 'prompt', 'pushd', 'popd'
    }
    
    # Comandos built-in comuns do Unix/Linux
    unix_builtins = {
        'cd', 'pwd', 'echo', 'export', 'unset', 'alias', 'unalias',
        'history', 'exit', 'logout', 'source', 'eval', 'exec', 'test',
        'true', 'false', 'read', 'printf', 'kill', 'jobs', 'fg', 'bg'
    }
    
    if platform.system() == 'Windows':
        return command.lower() in windows_builtins
    else:
        return command.lower() in unix_builtins

def _test_command_execution(command: str) -> bool:
    """
    Testa se um comando pode ser executado.
    
    Args:
        command: Nome do comando
        
    Returns:
        True se o comando pode ser executado, False caso contrário
    """
    test_args = ['--version', '--help', '-h', '-V']
    
    for arg in test_args:
        try:
            result = subprocess.run(
                [command, arg],
                capture_output=True,
                timeout=5,
                check=False
            )
            
            # Se o comando executou sem erro crítico, consideramos que existe
            if result.returncode in [0, 1]:  # 0 = sucesso, 1 = erro comum mas comando existe
                return True
                
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            continue
        except Exception as e:
            logger.debug(f"Erro ao testar comando '{command} {arg}': {e}")
            continue
    
    return False

def _windows_command_check(command: str) -> bool:
    """
    Verificação específica para comandos no Windows.
    
    Args:
        command: Nome do comando
        
    Returns:
        True se o comando existe no Windows, False caso contrário
    """
    try:
        # Usar 'where' command do Windows para encontrar executáveis
        result = subprocess.run(
            ['where', command],
            capture_output=True,
            timeout=5,
            check=False
        )
        
        if result.returncode == 0 and result.stdout.strip():
            logger.debug(f"Comando '{command}' encontrado via 'where': {result.stdout.strip()}")
            return True
        
        # Tentar com extensões comuns do Windows
        windows_extensions = ['.exe', '.cmd', '.bat', '.com']
        for ext in windows_extensions:
            if shutil.which(command + ext):
                logger.debug(f"Comando '{command}' encontrado com extensão '{ext}'")
                return True
        
        return False
        
    except Exception as e:
        logger.debug(f"Erro na verificação Windows para '{command}': {e}")
        return False

def clear_command_cache():
    """
    Limpa o cache de comandos verificados.
    """
    if hasattr(command_exists, '_cache'):
        command_exists._cache.clear()
        logger.debug("Cache de comandos limpo")

def get_command_path(command: str) -> Optional[str]:
    """
    Obtém o caminho completo de um comando.
    
    Args:
        command: Nome do comando
        
    Returns:
        Caminho completo do comando ou None se não encontrado
    """
    try:
        path = shutil.which(command)
        if path:
            return os.path.abspath(path)
        return None
    except Exception as e:
        logger.debug(f"Erro ao obter caminho do comando '{command}': {e}")
        return None

def get_command_version(command: str) -> Optional[str]:
    """
    Obtém a versão de um comando.
    
    Args:
        command: Nome do comando
        
    Returns:
        String com a versão ou None se não conseguir obter
    """
    if not command_exists(command):
        return None
    
    version_args = ['--version', '-V', '-version', 'version']
    
    for arg in version_args:
        try:
            result = subprocess.run(
                [command, arg],
                capture_output=True,
                text=True,
                timeout=10,
                check=False
            )
            
            if result.returncode == 0 and result.stdout.strip():
                # Extrair primeira linha que geralmente contém a versão
                first_line = result.stdout.strip().split('\n')[0]
                return first_line
                
        except Exception as e:
            logger.debug(f"Erro ao obter versão de '{command}': {e}")
            continue
    
    return None

def verify_commands(commands: List[str]) -> Dict[str, Dict[str, any]]:
    """
    Verifica múltiplos comandos e retorna informações detalhadas.
    
    Args:
        commands: Lista de comandos para verificar
        
    Returns:
        Dicionário com informações de cada comando
    """
    results = {}
    
    for command in commands:
        results[command] = {
            'exists': command_exists(command),
            'path': get_command_path(command),
            'version': get_command_version(command),
            'is_builtin': _is_builtin_command(command)
        }
    
    return results

def find_alternative_commands(command: str) -> List[str]:
    """
    Encontra comandos alternativos para um comando específico.
    
    Args:
        command: Comando original
        
    Returns:
        Lista de comandos alternativos disponíveis
    """
    # Mapeamento de comandos alternativos comuns
    alternatives = {
        'python': ['python3', 'py', 'python.exe'],
        'pip': ['pip3', 'python -m pip', 'py -m pip'],
        'git': ['git.exe'],
        'node': ['nodejs', 'node.exe'],
        'npm': ['npm.cmd', 'npm.exe'],
        'make': ['mingw32-make', 'gmake', 'nmake'],
        'gcc': ['clang', 'cl', 'tcc'],
        'g++': ['clang++', 'cl'],
        'cmake': ['cmake.exe'],
        'ninja': ['ninja.exe', 'ninja-build'],
        'curl': ['wget', 'powershell -Command Invoke-WebRequest'],
        'wget': ['curl', 'powershell -Command Invoke-WebRequest'],
        'tar': ['7z', 'powershell -Command Expand-Archive'],
        'unzip': ['7z', 'powershell -Command Expand-Archive'],
        'ls': ['dir'],
        'cat': ['type', 'Get-Content'],
        'grep': ['findstr', 'Select-String'],
        'which': ['where', 'Get-Command']
    }
    
    available_alternatives = []
    
    # Verificar alternativas conhecidas
    for alt in alternatives.get(command, []):
        if command_exists(alt):
            available_alternatives.append(alt)
    
    return available_alternatives

def get_system_commands_info() -> Dict[str, any]:
    """
    Obtém informações sobre comandos importantes do sistema.
    
    Returns:
        Dicionário com informações do sistema
    """
    important_commands = [
        'python', 'python3', 'pip', 'pip3', 'git', 'node', 'npm',
        'cmake', 'make', 'ninja', 'gcc', 'g++', 'clang', 'curl',
        'wget', 'tar', 'unzip', '7z', 'powershell', 'cmd'
    ]
    
    system_info = {
        'platform': platform.system(),
        'architecture': platform.architecture()[0],
        'python_version': sys.version,
        'path_dirs': os.environ.get('PATH', '').split(os.pathsep),
        'commands': verify_commands(important_commands)
    }
    
    return system_info

def diagnose_command_issues(command: str) -> Dict[str, any]:
    """
    Diagnostica problemas com um comando específico.
    
    Args:
        command: Nome do comando para diagnosticar
        
    Returns:
        Dicionário com diagnóstico detalhado
    """
    diagnosis = {
        'command': command,
        'exists': command_exists(command),
        'path': get_command_path(command),
        'version': get_command_version(command),
        'alternatives': find_alternative_commands(command),
        'issues': [],
        'suggestions': []
    }
    
    if not diagnosis['exists']:
        diagnosis['issues'].append(f"Comando '{command}' não encontrado no sistema")
        
        if diagnosis['alternatives']:
            diagnosis['suggestions'].append(
                f"Comandos alternativos disponíveis: {', '.join(diagnosis['alternatives'])}"
            )
        else:
            diagnosis['suggestions'].append(
                f"Instale o software que fornece o comando '{command}'"
            )
    
    # Verificar se está no PATH
    if diagnosis['exists'] and not diagnosis['path']:
        diagnosis['issues'].append(f"Comando '{command}' existe mas não está no PATH")
        diagnosis['suggestions'].append("Adicione o diretório do comando ao PATH do sistema")
    
    return diagnosis

if __name__ == "__main__":
    # Teste das funções
    logging.basicConfig(level=logging.INFO)
    
    print("=== Teste de Verificação de Comandos ===")
    
    test_commands = ['python', 'git', 'nonexistent_command', 'echo', 'dir']
    
    for cmd in test_commands:
        exists = command_exists(cmd)
        path = get_command_path(cmd)
        version = get_command_version(cmd)
        
        print(f"\nComando: {cmd}")
        print(f"  Existe: {exists}")
        print(f"  Caminho: {path}")
        print(f"  Versão: {version}")
        
        if not exists:
            alternatives = find_alternative_commands(cmd)
            if alternatives:
                print(f"  Alternativas: {alternatives}")
    
    print("\n=== Diagnóstico de Sistema ===")
    system_info = get_system_commands_info()
    print(f"Plataforma: {system_info['platform']}")
    print(f"Arquitetura: {system_info['architecture']}")
    
    available_commands = [cmd for cmd, info in system_info['commands'].items() if info['exists']]
    print(f"Comandos disponíveis: {len(available_commands)}/{len(system_info['commands'])}")