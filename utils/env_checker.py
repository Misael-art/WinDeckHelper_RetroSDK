import os
import shutil
import logging
import subprocess
import platform
import re

# Import winreg apenas no Windows
if platform.system() == "Windows":
    try:
        import winreg
    except ImportError:
        winreg = None # Define como None se não puder importar
else:
    winreg = None # Define como None em outras plataformas


# Lista de diretórios comuns onde softwares são instalados ou armazenam dados
COMMON_INSTALL_DIRS = [
    os.environ.get("ProgramFiles", "C:\\Program Files"),
    os.environ.get("ProgramFiles(x86)", "C:\\Program Files (x86)"),
    os.environ.get("LOCALAPPDATA", ""),
    os.environ.get("APPDATA", ""),
    os.environ.get("ProgramData", "C:\\ProgramData"),
]
# Filtra diretórios vazios (caso as variáveis de ambiente não existam)
COMMON_INSTALL_DIRS = [d for d in COMMON_INSTALL_DIRS if d and os.path.isdir(d)]

def check_path_for_executable(executable_name):
    """Verifica se um executável está no PATH."""
    if not executable_name:
        return False
    path = shutil.which(executable_name)
    if path:
        logging.debug(f"[EnvCheck] Executável '{executable_name}' encontrado no PATH: {path}")
        return True
    else:
        logging.debug(f"[EnvCheck] Executável '{executable_name}' não encontrado no PATH.")
        return False

def check_common_folders(folder_name_patterns):
    """
    Verifica a existência de pastas com nomes correspondentes aos padrões
    dentro dos diretórios de instalação comuns.

    Args:
        folder_name_patterns (list): Lista de nomes de pastas a procurar (case-insensitive).
    """
    if not folder_name_patterns:
        return False

    for base_dir in COMMON_INSTALL_DIRS:
        try:
            # Lista todos os itens no diretório base
            for item in os.listdir(base_dir):
                item_path = os.path.join(base_dir, item)
                # Verifica se é um diretório
                if os.path.isdir(item_path):
                    # Compara com cada padrão fornecido (case-insensitive)
                    for pattern in folder_name_patterns:
                        if pattern.lower() == item.lower():
                            logging.debug(f"[EnvCheck] Pasta encontrada em diretório comum: {item_path}")
                            return True # Encontrou uma correspondência
        except FileNotFoundError:
            logging.debug(f"[EnvCheck] Diretório base não encontrado: {base_dir}")
            continue
        except PermissionError:
            logging.debug(f"[EnvCheck] Sem permissão para acessar: {base_dir}")
            continue
        except Exception as e:
            logging.warning(f"[EnvCheck] Erro ao listar diretório {base_dir}: {e}")
            continue

    logging.debug(f"[EnvCheck] Nenhuma pasta correspondente a {folder_name_patterns} encontrada nos diretórios comuns.")
    return False

def check_env_var_exists(var_name):
    """Verifica se uma variável de ambiente existe."""
    if not var_name:
        return False
    value = os.environ.get(var_name)
    if value is not None:
        logging.debug(f"[EnvCheck] Variável de ambiente '{var_name}' encontrada com valor: {value}")
        return True
    else:
        logging.debug(f"[EnvCheck] Variável de ambiente '{var_name}' não encontrada.")
        return False


def check_executable_runs(executable_path, args=None):
    """Verifica se um executável pode ser iniciado com sucesso (código de saída 0)."""
    if not executable_path or not os.path.isfile(executable_path):
        # Tenta encontrar no PATH se não for um caminho completo
        if not os.path.dirname(executable_path):
            found_path = shutil.which(executable_path)
            if not found_path:
                logging.debug(f"[EnvCheck] Executável '{executable_path}' não encontrado no PATH ou como caminho absoluto.")
                return False
            executable_path = found_path
        else:
             logging.debug(f"[EnvCheck] Caminho do executável não encontrado ou não é um arquivo: {executable_path}")
             return False

    command = [executable_path]
    if args:
        command.extend(args)

    try:
        # Usa STARTUPINFO para ocultar a janela no Windows
        startupinfo = None
        if platform.system() == "Windows":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE

        # Executa o comando com timeout curto, captura saída e oculta janela
        result = subprocess.run(command, capture_output=True, text=True, check=False, timeout=15, startupinfo=startupinfo, encoding='utf-8', errors='ignore')
        
        if result.returncode == 0:
            logging.debug(f"[EnvCheck] Executável '{executable_path}' executado com sucesso (código 0).")
            return True
        else:
            logging.debug(f"[EnvCheck] Executável '{executable_path}' executado com erro (código {result.returncode}).")
            logging.debug(f"[EnvCheck] Stderr: {result.stderr.strip()}")
            return False
    except FileNotFoundError:
        logging.debug(f"[EnvCheck] Comando não encontrado ao tentar executar: {executable_path}")
        return False
    except subprocess.TimeoutExpired:
        logging.debug(f"[EnvCheck] Timeout ao tentar executar: {executable_path}")
        return False
    except PermissionError:
        logging.debug(f"[EnvCheck] Permissão negada ao tentar executar: {executable_path}")
        return False
    except Exception as e:
        logging.warning(f"[EnvCheck] Erro inesperado ao executar '{executable_path}': {e}")
        return False

def check_registry_key_exists(key_path):
    """Verifica a existência de uma chave de registro (Apenas Windows)."""
    if platform.system() != "Windows" or not winreg:
        logging.debug("[EnvCheck] Verificação de registro pulada (não é Windows ou winreg não disponível).")
        return False # Ou True? Depende se queremos falhar ou ignorar em não-Windows.
                     # Vamos retornar False para indicar que a verificação não foi positiva.

    try:
        # Separa a hive (HKEY_*) do sub_key
        parts = key_path.split('\\', 1)
        if len(parts) != 2:
            logging.warning(f"[EnvCheck] Formato inválido para chave de registro: {key_path}")
            return False
            
        hive_name, sub_key = parts
        
        # Mapeia nome da hive para constante winreg
        hive_map = {
            "HKEY_CLASSES_ROOT": winreg.HKEY_CLASSES_ROOT,
            "HKEY_CURRENT_USER": winreg.HKEY_CURRENT_USER,
            "HKEY_LOCAL_MACHINE": winreg.HKEY_LOCAL_MACHINE,
            "HKEY_USERS": winreg.HKEY_USERS,
            "HKEY_PERFORMANCE_DATA": winreg.HKEY_PERFORMANCE_DATA,
            "HKEY_CURRENT_CONFIG": winreg.HKEY_CURRENT_CONFIG,
            "HKEY_DYN_DATA": winreg.HKEY_DYN_DATA
        }
        
        hive = hive_map.get(hive_name.upper())
        if not hive:
            logging.warning(f"[EnvCheck] Hive de registro desconhecida: {hive_name}")
            return False

        # Tenta abrir a chave
        with winreg.OpenKey(hive, sub_key, 0, winreg.KEY_READ) as key:
            logging.debug(f"[EnvCheck] Chave de registro encontrada: {key_path}")
            return True
            
    except FileNotFoundError:
        logging.debug(f"[EnvCheck] Chave de registro não encontrada: {key_path}")
        return False
    except PermissionError:
        logging.debug(f"[EnvCheck] Permissão negada para acessar chave de registro: {key_path}")
        return False # Considera não encontrado se não tiver permissão
    except Exception as e:
        logging.warning(f"[EnvCheck] Erro ao verificar chave de registro '{key_path}': {e}")
        return False

def check_file_contains(file_path, text_pattern, use_regex=False):
    """Verifica se um arquivo contém um texto ou padrão regex."""
    if not file_path or not os.path.isfile(file_path):
        logging.debug(f"[EnvCheck] Arquivo não encontrado para verificação de conteúdo: {file_path}")
        return False
        
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
            if use_regex:
                if re.search(text_pattern, content):
                    logging.debug(f"[EnvCheck] Padrão regex '{text_pattern}' encontrado em '{file_path}'.")
                    return True
                else:
                    logging.debug(f"[EnvCheck] Padrão regex '{text_pattern}' não encontrado em '{file_path}'.")
                    return False
            else:
                if text_pattern in content:
                    logging.debug(f"[EnvCheck] Texto '{text_pattern[:50]}...' encontrado em '{file_path}'.")
                    return True
                else:
                    logging.debug(f"[EnvCheck] Texto '{text_pattern[:50]}...' não encontrado em '{file_path}'.")
                    return False
                    
    except Exception as e:
        logging.warning(f"[EnvCheck] Erro ao ler arquivo '{file_path}' para verificação de conteúdo: {e}")
        return False

# --- Funções futuras (exemplo) ---
# def check_registry_uninstall_key(display_name_pattern):
#     """Verifica chaves de desinstalação no registro."""
#     # Implementação usando winreg
#     pass

def check_file_exists(file_path):
    """Verifica se um arquivo existe."""
    if not file_path:
        return False
    exists = os.path.isfile(file_path)
    if exists:
        logging.debug(f"[EnvCheck] Arquivo encontrado: {file_path}")
    else:
        logging.debug(f"[EnvCheck] Arquivo não encontrado: {file_path}")
    return exists

def check_directory_exists(dir_path):
    """Verifica se um diretório existe."""
    if not dir_path:
        return False
    exists = os.path.isdir(dir_path)
    if exists:
        logging.debug(f"[EnvCheck] Diretório encontrado: {dir_path}")
    else:
        logging.debug(f"[EnvCheck] Diretório não encontrado: {dir_path}")
    return exists

def check_command_available(command):
    """Verifica se um comando está disponível no sistema."""
    if not command:
        return False
    
    # Se é um caminho completo, verificar se existe
    if os.path.sep in command:
        return check_file_exists(command)
    
    # Caso contrário, verificar no PATH
    return check_path_for_executable(command)

def registry_key_exists(hive, key_path):
    """Verifica a existência de uma chave de registro com hive e key_path separados."""
    if platform.system() != "Windows" or not winreg:
        logging.debug("[EnvCheck] Verificação de registro pulada (não é Windows ou winreg não disponível).")
        return False
    
    try:
        # Mapeia nome da hive para constante winreg
        hive_map = {
            'HKLM': winreg.HKEY_LOCAL_MACHINE,
            'HKEY_LOCAL_MACHINE': winreg.HKEY_LOCAL_MACHINE,
            'HKCU': winreg.HKEY_CURRENT_USER,
            'HKEY_CURRENT_USER': winreg.HKEY_CURRENT_USER,
            'HKCR': winreg.HKEY_CLASSES_ROOT,
            'HKEY_CLASSES_ROOT': winreg.HKEY_CLASSES_ROOT,
            'HKEY_USERS': winreg.HKEY_USERS,
            'HKEY_CURRENT_CONFIG': winreg.HKEY_CURRENT_CONFIG
        }
        
        if hive not in hive_map:
            logging.warning(f"[EnvCheck] Hive de registro desconhecida: {hive}")
            return False
            
        hive_const = hive_map[hive]
        
        # Tenta abrir a chave
        with winreg.OpenKey(hive_const, key_path, 0, winreg.KEY_READ) as key:
            logging.debug(f"[EnvCheck] Chave de registro encontrada: {hive}\\{key_path}")
            return True
            
    except FileNotFoundError:
        logging.debug(f"[EnvCheck] Chave de registro não encontrada: {hive}\\{key_path}")
        return False
    except PermissionError:
        logging.debug(f"[EnvCheck] Permissão negada para acessar chave de registro: {hive}\\{key_path}")
        return False
    except Exception as e:
        logging.warning(f"[EnvCheck] Erro ao verificar chave de registro '{hive}\\{key_path}': {e}")
        return False

def get_registry_value(hive, key_path, value_name):
    """Obtém o valor de uma entrada específica no registro."""
    if platform.system() != "Windows" or not winreg:
        logging.debug("[EnvCheck] Verificação de registro pulada (não é Windows ou winreg não disponível).")
        return None
    
    try:
        # Mapeia nome da hive para constante winreg
        hive_map = {
            'HKLM': winreg.HKEY_LOCAL_MACHINE,
            'HKEY_LOCAL_MACHINE': winreg.HKEY_LOCAL_MACHINE,
            'HKCU': winreg.HKEY_CURRENT_USER,
            'HKEY_CURRENT_USER': winreg.HKEY_CURRENT_USER,
            'HKCR': winreg.HKEY_CLASSES_ROOT,
            'HKEY_CLASSES_ROOT': winreg.HKEY_CLASSES_ROOT,
            'HKEY_USERS': winreg.HKEY_USERS,
            'HKEY_CURRENT_CONFIG': winreg.HKEY_CURRENT_CONFIG
        }
        
        if hive not in hive_map:
            logging.warning(f"[EnvCheck] Hive de registro desconhecida: {hive}")
            return None
            
        hive_const = hive_map[hive]
        
        # Tenta abrir a chave e ler o valor
        with winreg.OpenKey(hive_const, key_path, 0, winreg.KEY_READ) as key:
            value, reg_type = winreg.QueryValueEx(key, value_name)
            logging.debug(f"[EnvCheck] Valor '{value_name}' encontrado: {value}")
            return value
            
    except FileNotFoundError:
        logging.debug(f"[EnvCheck] Chave de registro não encontrada: {hive}\\{key_path}")
        return None
    except PermissionError:
        logging.debug(f"[EnvCheck] Permissão negada para acessar chave de registro: {hive}\\{key_path}")
        return None
    except Exception as e:
        logging.warning(f"[EnvCheck] Erro ao ler valor '{value_name}' da chave '{hive}\\{key_path}': {e}")
        return None

# Alias para compatibilidade com função de um parâmetro
check_registry_key_exists_single = check_registry_key_exists