import winreg
import logging
import os
import ctypes

# Constantes para acesso ao registro
HKEY_CURRENT_USER = winreg.HKEY_CURRENT_USER
HKEY_LOCAL_MACHINE = winreg.HKEY_LOCAL_MACHINE

# Chaves de registro para variáveis de ambiente
USER_ENV_KEY = r"Environment"
SYSTEM_ENV_KEY = r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"

# Mensagem para notificar sobre a necessidade de reiniciar o terminal/sistema
ENV_CHANGE_NOTICE = "Alterações nas variáveis de ambiente podem exigir a reinicialização do terminal ou do sistema para terem efeito."

def _read_env_variable(scope, name):
    """Lê uma variável de ambiente do registro (usuário ou sistema)."""
    try:
        if scope == 'user':
            key_handle = HKEY_CURRENT_USER
            subkey = USER_ENV_KEY
        elif scope == 'system':
            key_handle = HKEY_LOCAL_MACHINE
            subkey = SYSTEM_ENV_KEY
        else:
            raise ValueError("Scope deve ser 'user' ou 'system'")

        with winreg.OpenKey(key_handle, subkey, 0, winreg.KEY_READ) as key:
            value, _ = winreg.QueryValueEx(key, name)
            return value
    except FileNotFoundError:
        logging.debug(f"Variável '{name}' não encontrada no escopo '{scope}'.")
        return None
    except Exception as e:
        logging.error(f"Erro ao ler variável '{name}' do registro ({scope}): {e}")
        return None

def _write_env_variable(scope, name, value):
    """Escreve uma variável de ambiente no registro (usuário ou sistema)."""
    try:
        if scope == 'user':
            key_handle = HKEY_CURRENT_USER
            subkey = USER_ENV_KEY
            access = winreg.KEY_WRITE
        elif scope == 'system':
            key_handle = HKEY_LOCAL_MACHINE
            subkey = SYSTEM_ENV_KEY
            # Requer privilégios de administrador
            access = winreg.KEY_WRITE | winreg.KEY_WOW64_64KEY # Garante acesso à chave 64-bit
        else:
            raise ValueError("Scope deve ser 'user' ou 'system'")

        with winreg.OpenKey(key_handle, subkey, 0, access) as key:
            winreg.SetValueEx(key, name, 0, winreg.REG_EXPAND_SZ, value) # Usa REG_EXPAND_SZ para PATH

        # Notifica outros processos sobre a mudança (broadcast)
        HWND_BROADCAST = 0xFFFF
        WM_SETTINGCHANGE = 0x1A
        SMTO_ABORTIFHUNG = 0x0002
        result = ctypes.c_long()
        ctypes.windll.user32.SendMessageTimeoutW(HWND_BROADCAST, WM_SETTINGCHANGE, 0, "Environment", SMTO_ABORTIFHUNG, 5000, ctypes.byref(result))
        logging.info(f"Variável '{name}' atualizada no escopo '{scope}'. {ENV_CHANGE_NOTICE}")
        return True

    except PermissionError:
        logging.error(f"Erro de permissão ao escrever variável '{name}' no registro ({scope}). Execute como administrador para modificar variáveis do sistema.")
        return False
    except Exception as e:
        logging.error(f"Erro ao escrever variável '{name}' no registro ({scope}): {e}")
        return False

def get_path(scope='user'):
    """Obtém a variável PATH do usuário ou do sistema."""
    path_value = _read_env_variable(scope, 'Path')
    return path_value.split(';') if path_value else []

def add_to_path(directory, scope='user', prepend=False):
    """
    Adiciona um diretório à variável PATH do usuário ou do sistema, se ainda não estiver presente.

    Args:
        directory (str): O diretório a ser adicionado.
        scope (str): 'user' para o PATH do usuário, 'system' para o PATH do sistema.
        prepend (bool): Se True, adiciona no início do PATH; caso contrário, no final.

    Returns:
        bool: True se o PATH foi modificado, False caso contrário ou se ocorrer erro.
    """
    if not os.path.isdir(directory):
        logging.warning(f"Diretório '{directory}' não encontrado. Não será adicionado ao PATH.")
        return False

    current_path_list = get_path(scope)
    normalized_directory = os.path.normpath(directory)

    # Verifica se o diretório (ou uma versão normalizada) já existe no PATH
    path_exists = any(os.path.normpath(p) == normalized_directory for p in current_path_list)

    if path_exists:
        logging.info(f"Diretório '{normalized_directory}' já existe no PATH do escopo '{scope}'.")
        return False

    logging.info(f"Adicionando '{normalized_directory}' ao PATH do escopo '{scope}'.")

    if prepend:
        new_path_list = [normalized_directory] + current_path_list
    else:
        new_path_list = current_path_list + [normalized_directory]

    # Remove entradas vazias que podem surgir
    new_path_list = [p for p in new_path_list if p]
    new_path_string = ';'.join(new_path_list)

    return _write_env_variable(scope, 'Path', new_path_string)

def remove_from_path(directory, scope='user'):
    """
    Remove um diretório da variável PATH do usuário ou do sistema.

    Args:
        directory (str): O diretório a ser removido.
        scope (str): 'user' para o PATH do usuário, 'system' para o PATH do sistema.

    Returns:
        bool: True se o PATH foi modificado, False caso contrário ou se ocorrer erro.
    """
    current_path_list = get_path(scope)
    normalized_directory = os.path.normpath(directory)

    # Verifica se o diretório existe no PATH
    new_path_list = []
    found = False
    for p in current_path_list:
        if p and os.path.normpath(p) == normalized_directory:
            found = True
            logging.info(f"Removendo '{normalized_directory}' do PATH do escopo '{scope}'.")
        else:
            new_path_list.append(p)

    if not found:
        logging.info(f"Diretório '{normalized_directory}' não encontrado no PATH do escopo '{scope}'.")
        return False

    # Remove entradas vazias que podem surgir
    new_path_list = [p for p in new_path_list if p]
    new_path_string = ';'.join(new_path_list)

    return _write_env_variable(scope, 'Path', new_path_string)

def is_admin():
    """Verifica se o script está sendo executado com privilégios de administrador."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False

def get_env_var(name, scope='user'):
    """
    Obtém o valor de uma variável de ambiente do registro do Windows.

    Args:
        name (str): Nome da variável de ambiente.
        scope (str): 'user' para variáveis do usuário, 'system' para variáveis do sistema.

    Returns:
        str: Valor da variável de ambiente, ou None se não existir.
    """
    if not name:
        logging.error("Nome da variável de ambiente deve ser fornecido.")
        return None

    # Primeiro tenta obter do ambiente do processo atual
    if name in os.environ:
        return os.environ[name]

    # Se não encontrar, tenta obter do registro
    return _read_env_variable(scope, name)

def set_env_var(name, value, scope='user'):
    """
    Define ou atualiza uma variável de ambiente no registro do Windows.

    Args:
        name (str): Nome da variável de ambiente.
        value (str): Valor a ser definido.
        scope (str): 'user' para variáveis do usuário, 'system' para variáveis do sistema.

    Returns:
        bool: True se a operação for bem-sucedida, False caso contrário.
    """
    if not name or not value:
        logging.error("Nome e valor da variável de ambiente devem ser fornecidos.")
        return False

    if scope == 'system' and not is_admin():
        logging.error("Privilégios de administrador são necessários para modificar variáveis de ambiente do sistema.")
        return False

    # Verifica se a variável já existe com o mesmo valor
    current_value = _read_env_variable(scope, name)
    if current_value == value:
        logging.info(f"Variável '{name}' já possui o valor '{value}' no escopo '{scope}'.")
        return True

    # Define ou atualiza a variável
    result = _write_env_variable(scope, name, value)
    if result:
        # Também define a variável no ambiente do processo atual para uso imediato
        os.environ[name] = value

    return result

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)

    print(f"Executando como administrador: {is_admin()}")

    # --- Testes (CUIDADO: Modificam o registro) ---
    # Descomente com cautela para testar

    # test_dir_user = r"C:\TestPathUser"
    # test_dir_system = r"C:\TestPathSystem"

    # print("\n--- Teste PATH Usuário ---")
    # os.makedirs(test_dir_user, exist_ok=True)
    # print(f"PATH atual (User): {';'.join(get_path('user'))}")
    # add_to_path(test_dir_user, scope='user')
    # print(f"PATH após adição (User): {';'.join(get_path('user'))}")
    # # Para remover (requer implementação de remove_from_path ou edição manual)
    # # print(f"Lembre-se de remover '{test_dir_user}' do PATH do usuário manualmente se necessário.")
    # # os.rmdir(test_dir_user)

    # print("\n--- Teste PATH Sistema (Requer Admin) ---")
    # if is_admin():
    #     os.makedirs(test_dir_system, exist_ok=True)
    #     print(f"PATH atual (System): {';'.join(get_path('system'))}")
    #     add_to_path(test_dir_system, scope='system')
    #     print(f"PATH após adição (System): {';'.join(get_path('system'))}")
    #     # Para remover (requer implementação de remove_from_path ou edição manual)
    #     # print(f"Lembre-se de remover '{test_dir_system}' do PATH do sistema manualmente se necessário.")
    #     # os.rmdir(test_dir_system)
    # else:
    #      print("Pule o teste do PATH do sistema. Execute como administrador para testar.")

    print("\nTestes concluídos (se descomentados). Verifique o Editor de Variáveis de Ambiente do Windows.")